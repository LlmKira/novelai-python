# -*- coding: utf-8 -*-
import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from loguru import logger
from nacl.encoding import Base64Encoder
from nacl.signing import VerifyKey
from pydantic import BaseModel, ConfigDict

from .lsb_extractor import ImageLsbDataExtractor
from .lsb_injector import inject_data
from ...sdk.ai.generate_image._enum import PROMOTION, Model


class ImageMetadata(BaseModel):
    """
    ImageMetadata is a class that represents the metadata of a NovelAI generated image.
    """

    class CommentModel(BaseModel):
        prompt: str
        steps: int = None
        height: int = None
        width: int = None
        scale: float = None
        uncond_scale: float = None
        cfg_rescale: float = None
        seed: int = None
        n_samples: int = None
        hide_debug_overlay: bool = None
        noise_schedule: str = None
        legacy_v3_extend: bool = None
        reference_information_extracted: float = None
        reference_strength: float = None
        sampler: str = None
        controlnet_strength: float = None
        controlnet_model: Union[None, str] = None
        dynamic_thresholding: bool = None
        dynamic_thresholding_percentile: float = None
        dynamic_thresholding_mimic_scale: float = None
        sm: bool = None
        sm_dyn: bool = None
        skip_cfg_below_sigma: float = None
        lora_unet_weights: Union[None, str] = None
        lora_clip_weights: Union[None, str] = None
        uc: str = None
        request_type: str = None
        signed_hash: str = None
        model_config = ConfigDict(extra="allow")

        @property
        def negative_prompt(self):
            return self.uc

    Title: str = "AI generated image"
    Software: str = "NovelAI"
    Source: str = None
    Description: str
    Comment: CommentModel
    """
    AI generated image
    silvery white, best quality, amazing quality, very aesthetic, absurdres
    {'prompt': 'silvery white, best quality, amazing quality, very aesthetic, absurdres', 'steps': 28, 'height': 128, 'width': 128, 'scale': 10.0, 'uncond_scale': 1.0, 'cfg_rescale': 0.38, 'seed': 1148692016, 'n_samples': 1, 'hide_debug_overlay': False, 'noise_schedule': 'native', 'legacy_v3_extend': False, 'reference_information_extracted': 0.87, 'reference_strength': 1.0, 'sampler': 'k_euler', 'controlnet_strength': 1.0, 'controlnet_model': None, 'dynamic_thresholding': False, 'dynamic_thresholding_percentile': 0.999, 'dynamic_thresholding_mimic_scale': 10.0, 'sm': True, 'sm_dyn': True, 'skip_cfg_below_sigma': 0.0, 'lora_unet_weights': None, 'lora_clip_weights': None, 'uc': 'nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], small', 'request_type': 'PromptGenerateRequest', 'signed_hash': 'GmLfTgQTOI4WRcTloiSmenArH/Y8szJdVJ1DW18yeqYPkqw3o1zellB4xCQFYle+0tuF9KVP8RkHiDNbQXr0DA=='}
    """
    model_config = ConfigDict(extra="allow")

    @property
    def used_model(self) -> Union[Model, None]:
        """
        Get the model used to generate the image from the Model code
        :return:  Model or None
        """
        return PROMOTION.get(self.Source, None)

    @staticmethod
    def reset_alpha(input_img: BytesIO) -> BytesIO:
        """
        Remove LSB from the image, set the alpha channel to 254
        :param input_img:
        :return:
        """
        if isinstance(input_img, BytesIO):
            input_img.seek(0)
        image = Image.open(input_img).convert('RGBA')
        data = np.array(image)
        data[..., 3] = 254
        new_image = Image.fromarray(data, 'RGBA')
        _new_img_io = BytesIO()
        new_image.save(_new_img_io, format="PNG")
        return _new_img_io

    def apply_to_image(self,
                       origin_image: Image.Image,
                       *,
                       inject_lsb: bool = True
                       ) -> BytesIO:
        """
        Write metadata to origin_image
        If you set inject_lsb to True, the image will be injected with metadata using LSB.

        **But if you set inject_lsb to False, the image will be reset to the 254 alpha channel**
        :param origin_image:  BytesIO
        :param inject_lsb:  Inject metadata using LSB
        :return:  BytesIO
        """
        metadata = PngInfo()
        for k, v in self.model_dump(mode="json").items():
            if isinstance(v, dict):
                v = json.dumps(v)
            metadata.add_text(k, v)
        if inject_lsb:
            # Inject metadata using LSB
            origin_image = inject_data(origin_image, metadata)
        # Save original image with metadata (and LSB if inject_lsb is True)
        new_img = BytesIO()
        origin_image.save(new_img, format="PNG", pnginfo=metadata, optimize=False, compress_level=0)
        return new_img

    @classmethod
    def load_image(cls,
                   image_io: Union[str, bytes, Path, BytesIO]
                   ):
        """
        Load image and extract metadata using LSB/Metadata
        :param image_io: str, bytes, Path, BytesIO
        :return: ImageMetadata
        :raises ValidationError:  Data extraction failed
        """
        if isinstance(image_io, BytesIO):
            image_io.seek(0)
        try:
            image_data = ImageLsbDataExtractor().extract_data(image_io)
            model = cls(**image_data)
        except Exception as e:
            logger.debug(f"Error trying extracting data in LSB: {e}")
        else:
            return model
        with Image.open(image_io) as img:
            title = img.info.get("Title", None)
            prompt = img.info.get("Description", None)
            comment = img.info.get("Comment", None)
            assert isinstance(comment, str), ValueError("Comment Empty")
            try:
                comment = json.loads(comment)
            except Exception as e:
                logger.debug(f"Error loading comment: {e}")
                comment = {}
        return cls(Title=title, Description=prompt, Comment=cls.CommentModel(**comment))

    @staticmethod
    def verify_image_is_novelai(
            image: Union[Image.Image, np.ndarray],
            verify_key_hex: str = "Y2JcQAOhLwzwSDUJPNgL04nS0Tbqm7cSRc4xk0vRMic="
    ) -> bool:
        """
        Verify if the image is a NovelAI generated image
        :param image:  Image.Image or np.ndarray
        :param verify_key_hex:
        :return:  bool
        :raises RuntimeError:  No metadata found in image
        :raises RuntimeError:  Comment not in metadata
        :raises RuntimeError:  signed_hash not in comment
        """
        # MIT:https://github.com/NovelAI/novelai-image-metadata/blob/main/nai_sig.py
        if isinstance(image, Image.Image):
            image = np.array(image)
        metadata = ImageLsbDataExtractor().extract_data(image)

        if metadata is None:
            raise RuntimeError("No metadata found in image")
        if "Comment" not in metadata:
            raise RuntimeError("Comment not in metadata")
        comment = metadata["Comment"]
        if "signed_hash" not in comment:
            raise RuntimeError("signed_hash not in comment")
        signed_hash = comment["signed_hash"].encode("utf-8")
        signed_hash = base64.b64decode(signed_hash)
        del comment["signed_hash"]
        verify_key_hex = verify_key_hex.encode("utf-8")
        verify_key = VerifyKey(verify_key_hex, encoder=Base64Encoder)
        image_and_comment = image[:, :, :3].tobytes() + json.dumps(comment).encode("utf-8")
        try:
            verify_key.verify(image_and_comment, signed_hash)
        except Exception as e:
            logger.trace(e)
            return False
        return True
