# -*- coding: utf-8 -*-
import base64
import json
from io import BytesIO
from typing import Union, Optional, List, Tuple

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from loguru import logger
from nacl.encoding import Base64Encoder
from nacl.signing import VerifyKey
from pydantic import BaseModel, ConfigDict

from novelai_python.sdk.ai._enum import PROMOTION, Model
from .bch_utils import fec_decode
from .lsb_extractor import ImageLsbDataExtractor
from .lsb_injector import inject_data


class BrokenMetaDataError(Exception):
    pass


class BrokenCommentError(Exception):
    pass


class CommentModel(BaseModel):
    prompt: Optional[str] = None
    steps: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    scale: Optional[float] = None
    uncond_scale: Optional[float] = None
    cfg_rescale: Optional[float] = None
    seed: Optional[int] = None
    n_samples: Optional[int] = None
    hide_debug_overlay: Optional[bool] = None
    noise_schedule: Optional[str] = None
    legacy_v3_extend: Optional[bool] = None
    reference_information_extracted: Optional[float] = None
    reference_strength: Optional[float] = None
    reference_strength_multiple: Optional[List[float]] = None
    reference_information_extracted_multiple: Optional[List[float]] = None
    sampler: Optional[str] = None
    controlnet_strength: Optional[float] = None
    controlnet_model: Optional[Union[None, str]] = None
    dynamic_thresholding: Optional[bool] = None
    dynamic_thresholding_percentile: Optional[float] = None
    dynamic_thresholding_mimic_scale: Optional[float] = None
    sm: Optional[bool] = None
    sm_dyn: Optional[bool] = None
    skip_cfg_below_sigma: Optional[float] = None
    lora_unet_weights: Optional[Union[None, str]] = None
    lora_clip_weights: Optional[Union[None, str]] = None
    uc: Optional[str] = None
    request_type: Optional[str] = None
    signed_hash: Optional[str] = None
    skip_cfg_above_sigma: Optional[float] = None
    deliberate_euler_ancestral_bug: Optional[bool] = None
    prefer_brownian: Optional[bool] = None
    cfg_sched_eligibility: Optional[str] = None
    explike_fine_detail: Optional[bool] = None
    minimize_sigma_inf: Optional[bool] = None
    uncond_per_vibe: Optional[bool] = None
    wonky_vibe_correlation: Optional[bool] = None
    version: Optional[int] = None

    extra_passthrough_testing: Optional[dict] = None
    """More test infomation"""
    v4_prompt: Optional[dict] = None
    v4_negative_prompt: Optional[dict] = None

    model_config = ConfigDict(extra="allow")

    @property
    def generate_method(self):
        return self.request_type or "Unknown"

    @property
    def negative_prompt(self):
        return self.uc

    @property
    def vibe_transfer_strength(self) -> List[float]:
        """
        Get the vibe transfer strength totally
        """
        if self.reference_strength_multiple:
            return self.reference_strength_multiple
        reference_strength = [] if self.reference_strength is None else [self.reference_strength]
        return reference_strength

    @property
    def vibe_transfer_information(self) -> List[float]:
        """
        Get the vibe transfer information totally
        """
        if self.reference_information_extracted_multiple:
            return self.reference_information_extracted_multiple
        reference_information = [] if self.reference_information_extracted is None else [
            self.reference_information_extracted]
        return reference_information


class ImageMetadata(BaseModel):
    """
    ImageMetadata is a class that represents the metadata of a NovelAI generated image.
    """

    Generation_time: Optional[float] = None
    Comment: Optional[CommentModel] = None
    Title: Optional[str] = None
    Description: Optional[str] = None
    Software: Optional[str] = None
    Source: Optional[str] = None
    dpi: Optional[Tuple[float, float]] = None

    model_config = ConfigDict(extra="allow")

    @property
    def used_model(self) -> Union[Model, None]:
        """
        Get the model used to generate the image from the Model code
        :return:  Model or None
        """
        return PROMOTION.get(self.Source, None)

    @staticmethod
    def reset_alpha(image: Image.Image) -> BytesIO:
        """
        Remove LSB from the image, set the alpha channel to 254
        :param image: Type: Union[str, bytes, Path, BytesIO]
        :return: BytesIO
        """
        image = image.convert('RGBA')
        data = np.array(image)
        data[..., 3] = 254
        new_image = Image.fromarray(data, 'RGBA')
        _new_img_io = BytesIO()
        new_image.save(_new_img_io, format="PNG")
        return _new_img_io

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
            image_meta_data, fec_data = ImageLsbDataExtractor().extract_data(image)
            return cls.model_validate(image_meta_data)
        except Exception as e:
            logger.trace(f"Error extracting data in LSB: {e}")
            return None

    @classmethod
    def _extract_metadata_from_comments(cls, image: Image.Image):
        """
        Extract metadata from image comments and other info.
        :param image: Union[str, bytes, Path, BytesIO]
        """
        generate_map = image.info
        comment = generate_map.get("Comment", "{}")
        try:
            comment_dict = json.loads(comment)
        except Exception as e:
            raise BrokenMetaDataError(
                f"ImageMetadata: non-standard comment json cant be loaded, given image maybe be modified!"
            ) from e
        comment_dict["prompt"] = comment_dict.get("prompt", "")
        try:
            comment_model = CommentModel.model_validate(comment_dict)
        except Exception as e:
            raise BrokenCommentError(
                f"ImageMetadata: comment model validate failed, given image maybe be modified."
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
                f"ImageMetadata: some error occurred when validate the model, are the image from novelai.net?"
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
            for cid, data, after_idat in image.private_chunks:
                if after_idat:
                    if cid == b'ltns':
                        sig = data
                    elif cid == b'ltnt':
                        latents = data
        except Exception as e:
            logger.trace(f"Error extracting latents: {e}")
            return True, False, None
        if sig is None or latents is None:
            return True, False, None
        if not sig.startswith(b'NovelAI_ltntsig'):
            return False, False, None
        sig = sig[len(b'NovelAI_ltntsig'):]
        if not latents.startswith(b'NovelAI_latents'):
            return False, False, None
        latents = latents[len(b'NovelAI_latents'):]
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
            logger.trace(f"Error verifying latents: {e}")
            return False, False, None

    def verify(self,
               image: Image.Image,
               verify_key_hex: str = "Y2JcQAOhLwzwSDUJPNgL04nS0Tbqm7cSRc4xk0vRMic="
               ) -> Tuple[bool, bool]:
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
            logger.trace(f"Error extracting data in LSB: {e}")
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
        good_latents, have_latents, latents = self.verify_latents(image, signed_hash, verify_key)
        if not good_latents:
            return False, False
        rgb = image_array[:, :, :3].tobytes()
        parameter = json.dumps(parameter).encode("utf-8")
        image_and_comment = rgb + parameter
        try:
            verify_key.verify(image_and_comment, signed_hash)
        except Exception as e:
            logger.trace(f"Error verifying image [1]: {e}")
            try:
                rgb, errs = fec_decode(bytearray(rgb), bytearray(fec_data), w, h)
                image_and_comment = rgb + parameter
                verify_key.verify(image_and_comment, signed_hash)
            except Exception as e:
                logger.trace(f"Error verifying image [2]: {e}")
                return False, False
        return True, have_latents
