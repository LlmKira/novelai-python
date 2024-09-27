# -*- coding: utf-8 -*-
import base64
import json
from io import BytesIO
from typing import Union, Optional, List

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from loguru import logger
from nacl.encoding import Base64Encoder
from nacl.signing import VerifyKey
from pydantic import BaseModel, ConfigDict

from novelai_python.sdk.ai._enum import PROMOTION, Model
from ._type import IMAGE_INPUT_TYPE, get_image_bytes
from .lsb_extractor import ImageLsbDataExtractor
from .lsb_injector import inject_data


class ImageMetadata(BaseModel):
    """
    ImageMetadata is a class that represents the metadata of a NovelAI generated image.
    """

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

    Title: str = "AI generated image"
    Software: str = "NovelAI"
    Source: str = None
    Description: str
    Comment: CommentModel

    model_config = ConfigDict(extra="allow")

    @property
    def used_model(self) -> Union[Model, None]:
        """
        Get the model used to generate the image from the Model code
        :return:  Model or None
        """
        return PROMOTION.get(self.Source, None)

    @staticmethod
    def reset_alpha(image: IMAGE_INPUT_TYPE) -> BytesIO:
        """
        Remove LSB from the image, set the alpha channel to 254
        :param image: Type: Union[str, bytes, Path, BytesIO]
        :return: BytesIO
        """
        image_data = get_image_bytes(image)
        image = Image.open(image_data).convert('RGBA')
        data = np.array(image)
        data[..., 3] = 254
        new_image = Image.fromarray(data, 'RGBA')
        _new_img_io = BytesIO()
        new_image.save(_new_img_io, format="PNG")
        return _new_img_io

    def apply_to_image(self, image: IMAGE_INPUT_TYPE, *, inject_lsb: bool = True) -> BytesIO:
        """
        Write metadata to origin_image
        If you set inject_lsb to True, the image will be injected with metadata using LSB.

        **But if you set inject_lsb to False, the image will be reset to the 254 alpha channel**
        :param image:  Union[str, bytes, Path, BytesIO]
        :param inject_lsb:  Inject metadata using LSB
        :return:  BytesIO
        """
        image_data = get_image_bytes(image)
        origin_image = Image.open(image_data)
        metadata = PngInfo()
        for k, v in self.model_dump(mode="json").items():
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
    def _extract_metadata_from_lsb(cls, image: IMAGE_INPUT_TYPE):
        """
        Extract metadata using LSB extraction method.
        :param image: IMAGE_INPUT_TYPE
        """
        try:
            image_meta_data = ImageLsbDataExtractor().extract_data(image)
            return cls.model_validate(image_meta_data)
        except Exception as e:
            logger.trace(f"Error extracting data in LSB: {e}")
            return None

    @classmethod
    def _extract_metadata_from_comments(cls, image: IMAGE_INPUT_TYPE):
        """
        Extract metadata from image comments and other info.
        :param image: IMAGE_INPUT_TYPE
        """
        with Image.open(image) as img:
            title = img.info.get("Title", None)
            description = img.info.get("Description", None)
            comment = img.info.get("Comment", "{}")
            try:
                comment_dict = json.loads(comment)
            except Exception as e:
                logger.trace(f"Error loading comment: {e}")
                comment_dict = {}
        try:
            comment_dict.setdefault("prompt", description)
            comment_model = cls.CommentModel.model_validate(comment_dict)
            return cls(Title=title, Description=description, Comment=comment_model)
        except Exception as e:
            logger.debug(f"Error loading comment: {e}")
            return None

    @classmethod
    def load_image(cls, image: IMAGE_INPUT_TYPE):
        """
        Load image and extract metadata using LSB/Metadata
        :param image: str, bytes, Path, BytesIO
        :return: ImageMetadata
        :raises ValueError: Data extraction failed
        """
        image_data = get_image_bytes(image)
        metadata = cls._extract_metadata_from_lsb(image_data)
        if metadata:
            return metadata
        metadata = cls._extract_metadata_from_comments(image)
        if metadata:
            return metadata
        raise ValueError("No metadata found")

    @staticmethod
    def verify_image_is_novelai(
            image,
            verify_key_hex: str = "Y2JcQAOhLwzwSDUJPNgL04nS0Tbqm7cSRc4xk0vRMic="
    ) -> bool:
        """
        Verify if the image is a NovelAI generated image

        :param image: Union[str, bytes, Path, BytesIO] - The input image to verify.
        :param verify_key_hex: str - The verification key in base64 format.
        :return: bool - True if the image is verified as NovelAI generated, otherwise False.
        :raises ValueError: If the required metadata or signed hash is missing.
        """
        image_data = get_image_bytes(image)
        image_array = np.array(Image.open(image_data))
        metadata = ImageMetadata.load_image(image_data)

        if not metadata or not metadata.Comment or not metadata.Comment.signed_hash:
            raise ValueError("Required metadata or signed hash is missing, maybe not a NovelAI image")

        comment_json = metadata.Comment.model_dump(mode="json")
        signed_hash = base64.b64decode(comment_json.pop("signed_hash").encode("utf-8"))
        try:
            verify_key = VerifyKey(verify_key_hex.encode("utf-8"), encoder=Base64Encoder)
            image_and_comment = image_array[:, :, :3].tobytes() + json.dumps(comment_json).encode("utf-8")
            verify_key.verify(image_and_comment, signed_hash)
            return True
        except Exception as e:
            logger.trace(f"Verification failed: {e}")
            return False
