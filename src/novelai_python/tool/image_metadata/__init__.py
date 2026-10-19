import base64
import json
import logging
from io import BytesIO

import numpy as np
from nacl.encoding import Base64Encoder
from nacl.signing import VerifyKey
from PIL import Image
from PIL.ExifTags import IFD as ExifIFD
from PIL.ExifTags import Base as ExifBase
from PIL.PngImagePlugin import PngInfo
from pydantic import BaseModel, ConfigDict

from novelai_python.sdk.ai._enum import PROMOTION as PROMOTION
from novelai_python.sdk.ai._enum import Model, find_model_by_hashcode

from .bch_utils import fec_decode
from .lsb_extractor import ImageLsbDataExtractor
from .lsb_injector import inject_data

logger = logging.getLogger(__name__)


class BrokenMetaDataError(Exception):
    pass


class BrokenCommentError(Exception):
    pass


class CommentModel(BaseModel):
    prompt: str | None = None
    steps: int | None = None
    height: int | None = None
    width: int | None = None
    scale: float | None = None
    uncond_scale: float | None = None
    cfg_rescale: float | None = None
    seed: int | None = None
    n_samples: int | None = None
    hide_debug_overlay: bool | None = None
    noise_schedule: str | None = None
    legacy_v3_extend: bool | None = None
    reference_information_extracted: float | None = None
    reference_strength: float | None = None
    reference_strength_multiple: list[float] | None = None
    reference_information_extracted_multiple: list[float] | None = None
    sampler: str | None = None
    controlnet_strength: float | None = None
    controlnet_model: None | str | None = None
    dynamic_thresholding: bool | None = None
    dynamic_thresholding_percentile: float | None = None
    dynamic_thresholding_mimic_scale: float | None = None
    sm: bool | None = None
    sm_dyn: bool | None = None
    skip_cfg_below_sigma: float | None = None
    lora_unet_weights: None | str | None = None
    lora_clip_weights: None | str | None = None
    uc: str | None = None
    request_type: str | None = None
    signed_hash: str | None = None
    skip_cfg_above_sigma: float | None = None
    deliberate_euler_ancestral_bug: bool | None = None
    prefer_brownian: bool | None = None
    cfg_sched_eligibility: str | None = None
    explike_fine_detail: bool | None = None
    minimize_sigma_inf: bool | None = None
    uncond_per_vibe: bool | None = None
    wonky_vibe_correlation: bool | None = None
    version: int | None = None

    extra_passthrough_testing: dict | None = None
    """More test infomation"""
    v4_prompt: dict | None = None
    v4_negative_prompt: dict | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def generate_method(self):
        return self.request_type or "Unknown"

    @property
    def negative_prompt(self):
        return self.uc

    @property
    def vibe_transfer_strength(self) -> list[float]:
        """
        Get the vibe transfer strength totally
        """
        if self.reference_strength_multiple:
            return self.reference_strength_multiple
        reference_strength = [] if self.reference_strength is None else [self.reference_strength]
        return reference_strength

    @property
    def vibe_transfer_information(self) -> list[float]:
        """
        Get the vibe transfer information totally
        """
        if self.reference_information_extracted_multiple:
            return self.reference_information_extracted_multiple
        reference_information = (
            [] if self.reference_information_extracted is None else [self.reference_information_extracted]
        )
        return reference_information


class ImageMetadata(BaseModel):
    """
    ImageMetadata is a class that represents the metadata of a NovelAI generated image.
    """

    Generation_time: float | None = None
    Comment: CommentModel | None = None
    Title: str | None = None
    Description: str | None = None
    Software: str | None = None
    Source: str | None = None
    dpi: tuple[float, float] | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def used_model(self) -> Model | None:
        """
        Get the model used to generate the image from the Model code
        :return:  Model or None
        """
        model = find_model_by_hashcode(self.Source) if self.Source else None
        return model if isinstance(model, Model) else None

    @staticmethod
    def reset_alpha(image: Image.Image) -> BytesIO:
        """
        Remove LSB from the image, set the alpha channel to 254
        :param image: Type: Union[str, bytes, Path, BytesIO]
        :return: BytesIO
        """
        image = image.convert("RGBA")
        data = np.array(image)
        data[..., 3] = 254
        new_image = Image.fromarray(data, "RGBA")
        new_img_io = BytesIO()
        new_image.save(new_img_io, format="PNG")
        return new_img_io

    def apply_to_image(self, image: Image.Image, *, inject_lsb: bool = True) -> BytesIO:
        """
        Write metadata to origin_image
        If you set inject_lsb to True, the image will be injected with metadata using LSB.

        **But if you set inject_lsb to False, the image will be reset to the 254 alpha channel**
        :param image:  Union[str, bytes, Path, BytesIO]
        :param inject_lsb:  Inject metadata using LSB
        :return:  BytesIO
        """
        origin_image = image
        metadata = PngInfo()
        for k, v in self.model_dump(mode="json", exclude_none=True).items():
            if isinstance(v, dict):
                v = json.dumps(v)
            metadata.add_text(k, v)
        if inject_lsb:
            # Inject metadata using LSB
            origin_image = inject_data(origin_image, metadata)

        # Prepare image to be saved
        be_copy_image = BytesIO()
        origin_image.save(be_copy_image, format="PNG", pnginfo=metadata, optimize=False, compress_level=0)
        return be_copy_image

    @classmethod
    def _extract_metadata_from_lsb(cls, image: Image.Image):
        """
        Extract metadata using LSB extraction method.
        :param image: IMAGE_INPUT_TYPE
        """
        try:
            image_meta_data, _fec_data = ImageLsbDataExtractor().extract_data(image)
            return cls.model_validate(image_meta_data)
        except Exception as e:
            logger.debug(f"Error extracting data in LSB: {e}")
            return None

    @staticmethod
    def _file_metadata(image: Image.Image) -> dict:
        """File-level metadata: PNG tEXt chunks, or the EXIF block NovelAI writes into WebP.

        EXIF mapping as in NovelAI's nai_sig.py: DocumentName -> Title, ImageDescription ->
        Description, Software -> Source, Artist, Copyright, UserComment (ASCII-prefixed) -> Comment.
        """
        if image.format != "WEBP":
            return dict(image.info)
        exif = image.getexif()
        out = {}
        for tag, key in (
            (ExifBase.DocumentName, "Title"),
            (ExifBase.ImageDescription, "Description"),
            (ExifBase.Software, "Source"),
            (ExifBase.Artist, "Artist"),
            (ExifBase.Copyright, "Copyright"),
        ):
            if tag in exif:
                out[key] = exif[tag]
        comment = exif.get_ifd(ExifIFD.Exif).get(ExifBase.UserComment)
        if isinstance(comment, bytes):
            # 8-byte charset prefix; NovelAI writes ASCII and anything else is not trusted
            comment = comment[8:].rstrip(b"\x00").decode("ascii") if comment[:8] == b"ASCII\x00\x00\x00" else None
        if comment:
            # V5 WebP: UserComment is the whole metadata object
            # {"Comment": "<json>", "Generation_time": ..., "Source": ..., ...}
            try:
                payload = json.loads(comment)
            except ValueError:
                payload = None
            if isinstance(payload, dict) and "Comment" in payload:
                out.update(payload)
            else:
                out["Comment"] = comment
        return out

    @classmethod
    def _extract_metadata_from_comments(cls, image: Image.Image):
        """
        Extract metadata from image comments and other info (PNG text or WebP EXIF).
        :param image: Union[str, bytes, Path, BytesIO]
        :return: ImageMetadata, or None when the file carries no Comment
        """
        generate_map = cls._file_metadata(image)
        if "Comment" not in generate_map:
            return None
        comment = generate_map["Comment"]
        try:
            comment_dict = json.loads(comment)
        except Exception as e:
            raise BrokenMetaDataError(
                "ImageMetadata: non-standard comment json cant be loaded, given image maybe be modified!"
            ) from e
        comment_dict["prompt"] = comment_dict.get("prompt", "")
        try:
            comment_model = CommentModel.model_validate(comment_dict)
        except Exception as e:
            raise BrokenCommentError(
                "ImageMetadata: comment model validate failed, given image maybe be modified."
                "If you are sure that the image is from novelai.net, please issue this problem to "
                "https://github.com/LlmKira/novelai-python/issues."
            ) from e
        try:
            return cls.model_validate(
                {
                    **generate_map,
                    "Comment": comment_model.model_dump(mode="python"),
                }
            )
        except Exception as e:
            raise BrokenMetaDataError(
                "ImageMetadata: some error occurred when validate the model, are the image from novelai.net?"
            ) from e

    @classmethod
    def load_image(cls, image: Image.Image):
        """
        Load image and extract metadata using LSB/Metadata
        :param image: str, bytes, Path, BytesIO
        :return: ImageMetadata
        :raises ValueError: Data extraction failed
        """

        metadata = cls._extract_metadata_from_lsb(image)
        if metadata:
            return metadata
        metadata = cls._extract_metadata_from_comments(image)
        if metadata:
            return metadata
        raise ValueError("No metadata found")

    @classmethod
    def load_from_watermark(cls, image: Image.Image):
        """
        Load image and extract metadata using LSB/Metadata
        :param image: str, bytes, Path, BytesIO
        :return: ImageMetadata
        :raises ValueError: Data extraction failed
        """
        metadata = cls._extract_metadata_from_lsb(image)
        if metadata:
            return metadata
        raise ValueError("No metadata found")

    @classmethod
    def load_from_pnginfo(cls, image: Image.Image):
        """
        Load image and extract metadata using LSB/Metadata
        :param image: str, bytes, Path, BytesIO
        :return: ImageMetadata
        :raises ValueError: Data extraction failed
        """
        metadata = cls._extract_metadata_from_comments(image)
        if metadata:
            return metadata
        raise ValueError("No metadata found")


class ImageVerifier:
    @staticmethod
    def verify_latents(image: Image.Image, signed_hash: bytes, verify_key: VerifyKey):
        sig = None
        latents = None
        try:
            # PngImageFile only: other formats carry no latent chunks
            for cid, data, after_idat in getattr(image, "private_chunks", []):
                if after_idat:
                    if cid == b"ltns":
                        sig = data
                    elif cid == b"ltnt":
                        latents = data
        except Exception as e:
            logger.debug(f"Error extracting latents: {e}")
            return True, False, None
        if sig is None or latents is None:
            return True, False, None
        if not sig.startswith(b"NovelAI_ltntsig"):
            return False, False, None
        sig = sig[len(b"NovelAI_ltntsig") :]
        if not latents.startswith(b"NovelAI_latents"):
            return False, False, None
        latents = latents[len(b"NovelAI_latents") :]
        if len(sig) != 64:
            return False, False, None
        w, h = image.size
        base_size = (w // 8) * (h // 8) * 4
        if len(latents) != base_size * 4 and len(latents) != base_size * 2:
            return False, False, None
        float_dim = 4 if len(latents) == base_size * 4 else 2
        try:
            verify_key.verify(signed_hash + latents, sig)
            return True, True, (float_dim, latents)
        except Exception as e:
            logger.debug(f"Error verifying latents: {e}")
            return False, False, None

    def verify(
        self, image: Image.Image, verify_key_hex: str = "Y2JcQAOhLwzwSDUJPNgL04nS0Tbqm7cSRc4xk0vRMic="
    ) -> tuple[bool, bool]:
        """
        Verify if the image is a NovelAI generated image

        :param image: PIL.Image.Image - The image to verify.
        :param verify_key_hex: str - The verification key in base64 format.
        :return: Tuple[bool, bool] - The first bool indicates if the image is verified, the second bool indicates if the image has latents.
        :raises ValueError: If the required metadata or signed hash is missing.
        """
        w, h = image.size
        image_array = np.array(image)
        try:
            metadata, fec_data = ImageLsbDataExtractor().extract_data(image, get_fec=True)
        except Exception as e:
            logger.debug(f"Error extracting data in LSB: {e}")
            metadata = None
            fec_data = None
        if not metadata or not metadata.get("Comment") or not metadata["Comment"].get("signed_hash"):
            raise ValueError(
                "Bad image lsb or metadata. Comment or Comment.signed_hash is missing, the image is be tampered or not generated by NovelAI."
            )
        parameter = metadata["Comment"]
        signed_hash = base64.b64decode(parameter.pop("signed_hash").encode("utf-8"))
        # Build verify key
        verify_key = VerifyKey(verify_key_hex.encode("utf-8"), encoder=Base64Encoder)
        # Verify latents
        good_latents, have_latents, _latents = self.verify_latents(image, signed_hash, verify_key)
        if not good_latents:
            return False, False
        rgb = image_array[:, :, :3].tobytes()
        parameter = json.dumps(parameter).encode("utf-8")
        # Older images sign the RGB bytes; V5 signs RGBA with the alpha LSB cleared,
        # because that bit carries the stealth metadata (as NovelAI's nai_sig.py does).
        candidates = [rgb]
        if image_array.ndim == 3 and image_array.shape[-1] == 4:
            masked = image_array.copy()
            masked[..., -1] &= 0xFE
            candidates.append(masked.tobytes())
        for image_bytes in candidates:
            try:
                verify_key.verify(image_bytes + parameter, signed_hash)
                return True, have_latents
            except Exception as e:
                logger.debug(f"Error verifying image [1]: {e}")
        if fec_data is None:
            return False, False
        try:
            rgb, _errs = fec_decode(bytearray(rgb), bytearray(fec_data), w, h)
            verify_key.verify(bytes(rgb) + parameter, signed_hash)
        except Exception as e:
            logger.debug(f"Error verifying image [2]: {e}")
            return False, False
        return True, have_latents
