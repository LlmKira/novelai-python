import base64
import math
import warnings
from enum import Enum
from io import BytesIO
from pathlib import Path

import numpy as np
import pydantic
from PIL import Image
from pydantic import BaseModel, Field, field_validator

from novelai_python.sdk.ai._enum import (
    Model,
    ModelTypeAlias,
    as_model,
    character_reference_error,
    get_character_reference_support,
    model_name,
)

# frames skipped when a warning picks the line to point at: this library, and pydantic, which runs its validators
_SKIPPED_IN_WARNINGS = (str(Path(__file__).parents[3]), str(Path(pydantic.__file__).parent))


def warn_left_out(message: str) -> None:
    """A UserWarning about something the library left out of a request, pointed at the caller's line
    outside the library, as PyTorch and huggingface_hub warn. ``-W error::UserWarning`` makes it an error."""
    warnings.warn(message, UserWarning, skip_file_prefixes=_SKIPPED_IN_WARNINGS)


class CharacterPosition(BaseModel):
    x: float | int = Field(default=0, le=0.9, ge=0, description="X")
    """
    0 Auto 
    0.1 0.3 0.5 0.7 0.9
    """
    y: float | int = Field(default=0, le=0.9, ge=0, description="Y")
    """
    0 Auto
    0.1 0.3 0.5 0.7 0.9
    """


class PositionMap(Enum):
    AUTO = CharacterPosition(x=0, y=0)
    A1 = CharacterPosition(x=0.1, y=0.1)
    A2 = CharacterPosition(x=0.1, y=0.3)
    A3 = CharacterPosition(x=0.1, y=0.5)
    A4 = CharacterPosition(x=0.1, y=0.7)
    A5 = CharacterPosition(x=0.1, y=0.9)
    B1 = CharacterPosition(x=0.3, y=0.1)
    B2 = CharacterPosition(x=0.3, y=0.3)
    B3 = CharacterPosition(x=0.3, y=0.5)
    B4 = CharacterPosition(x=0.3, y=0.7)
    B5 = CharacterPosition(x=0.3, y=0.9)
    C1 = CharacterPosition(x=0.5, y=0.1)
    C2 = CharacterPosition(x=0.5, y=0.3)
    C3 = CharacterPosition(x=0.5, y=0.5)
    C4 = CharacterPosition(x=0.5, y=0.7)
    C5 = CharacterPosition(x=0.5, y=0.9)
    D1 = CharacterPosition(x=0.7, y=0.1)
    D2 = CharacterPosition(x=0.7, y=0.3)
    D3 = CharacterPosition(x=0.7, y=0.5)
    D4 = CharacterPosition(x=0.7, y=0.7)
    D5 = CharacterPosition(x=0.7, y=0.9)
    E1 = CharacterPosition(x=0.9, y=0.1)
    E2 = CharacterPosition(x=0.9, y=0.3)
    E3 = CharacterPosition(x=0.9, y=0.5)
    E4 = CharacterPosition(x=0.9, y=0.7)
    E5 = CharacterPosition(x=0.9, y=0.9)


class Character(BaseModel):
    prompt: str = Field(default="", description="Prompt")
    uc: str = Field(default="", description="Negative Prompt")
    center: PositionMap | CharacterPosition = Field(default=PositionMap.AUTO, description="Center")

    @field_validator("center", mode="after")
    @classmethod
    def _normalize_center(cls, value: "PositionMap | CharacterPosition") -> "PositionMap | CharacterPosition":
        # from JSON the AUTO position comes back as a plain (0, 0); keep it AUTO so use_coords stays off
        if isinstance(value, CharacterPosition) and (value.x, value.y) == (0, 0):
            return PositionMap.AUTO
        return value

    """Center"""
    enabled: bool = Field(default=True, description="Enabled")

    @classmethod
    def build(
        cls, prompt: str, uc: str = "", center: PositionMap | CharacterPosition = PositionMap.AUTO
    ) -> "Character":
        """
        Build CharacterPrompt from prompt
        :param prompt: The main prompt
        :param uc: The negative prompt
        :param center: The center
        :return:
        """
        return cls(prompt=prompt, uc=uc, center=center)


class CharCaption(BaseModel):
    char_caption: str = Field(default="", description="Character Caption")
    centers: list[PositionMap | CharacterPosition] = Field(default=[PositionMap.AUTO], description="Center")
    """Center"""


class Caption(BaseModel):
    base_caption: str = Field(default="", description="Main Prompt")
    """Main Prompt"""
    char_captions: list[CharCaption] = Field(default_factory=list, description="Character Captions")
    """Character Captions"""


class V4Prompt(BaseModel):
    caption: Caption = Field(default_factory=Caption, description="Caption")
    use_coords: bool = Field(default=False, description="Use Coordinates")
    use_order: bool = Field(default=True, description="Use Order")

    @classmethod
    def build_from_character_prompts(
        cls, base_caption: str, character_prompts: list[Character], use_coords: bool = False, use_order: bool = True
    ) -> "V4Prompt":
        """
        Build V4Prompt from character prompts
        :param prompt: The main prompt
        :param character_prompts: List of character prompts
        :param use_coords: Whether to use coordinates
        :param use_order: Whether to use order
        :return:
        """
        caption = Caption(base_caption=base_caption)
        for character_prompt in (c for c in character_prompts if c.enabled):
            char_caption = CharCaption(char_caption=character_prompt.prompt, centers=[character_prompt.center])
            caption.char_captions.append(char_caption)
        return cls(caption=caption, use_coords=use_coords, use_order=use_order)


class V4NegativePrompt(BaseModel):
    caption: Caption = Field(default_factory=Caption, description="Caption")
    legacy_uc: bool = False

    @classmethod
    def build_from_character_prompts(
        cls, negative_prompt: str, character_prompts: list[Character], legacy_uc: bool
    ) -> "V4NegativePrompt":
        """
        Build V4NegativePrompt from character prompts
        :param negative_prompt: The main prompt
        :param character_prompts: List of character prompts
        :param legacy_uc: Legacy Uc
        :return:
        """
        caption = Caption(base_caption=negative_prompt)
        for character_prompt in (c for c in character_prompts if c.enabled):
            char_caption = CharCaption(char_caption=character_prompt.uc, centers=[character_prompt.center])
            caption.char_captions.append(char_caption)
        return cls(caption=caption, legacy_uc=legacy_uc)


# V4.5 fits a reference onto one of these canvases (validDirectorSizes in the web client)
DIRECTOR_SIZES: tuple[tuple[int, int], ...] = ((1024, 1536), (1536, 1024), (1472, 1472))


def _director_buckets() -> tuple[tuple[int, int], ...]:
    # For every height from 4096 down to 1024 in steps of 64, the widest multiple of 64 within one
    # megapixel, then the same buckets turned on their side: the 97 buckets of the web client.
    portrait = [(1048576 // (height * 64) * 64, height) for height in range(4096, 1023, -64)]
    return (*portrait, *((h, w) for w, h in reversed(portrait[:-1])))


DIRECTOR_BUCKETS: tuple[tuple[int, int], ...] = _director_buckets()
"""V5 crops a reference to the bucket closest to its aspect ratio."""

MAX_CHARACTER_REFERENCES = 16
"""The web client refuses to generate with more references than this (after filtering)."""

_STEALTH_MAGIC = b"stealth_pngcomp"

# Without outfits (V4.5) the web client folds the "Prefer same outfit" variants back
_FOLD_OUTFIT = {"character_mainoutfit": "character", "character&style_anyoutfit": "character&style"}
OUTFIT_DESCRIPTIONS = frozenset({"costume", *_FOLD_OUTFIT})


def _js_round(value: float) -> int:
    return math.floor(value + 0.5)


def _png_b64(image: Image.Image) -> str:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _strip_stealth_metadata(raw: bytes) -> bytes:
    """
    The image as the web client uploads it: a picture that carries NovelAI's metadata in the low bit of
    its alpha channel (``stealth_pngcomp``, read column by column) gets that bit cleared (alpha 254 -> 255,
    1 -> 0) and is re-encoded as PNG. JPEG, pictures above 16 megapixels and everything else stay as they are.
    """
    if raw[:3] == b"\xff\xd8\xff":
        return raw
    with Image.open(BytesIO(raw)) as src:
        if src.width * src.height > 0x1000000:
            return raw
        image = src.convert("RGBA")
    pixels = np.array(image)
    alpha = pixels[..., 3]
    bits = alpha.T.reshape(-1)[: len(_STEALTH_MAGIC) * 8] & 1
    if np.packbits(bits).tobytes() != _STEALTH_MAGIC:
        return raw
    alpha[alpha == 254] = 255
    alpha[alpha == 1] = 0
    buf = BytesIO()
    Image.fromarray(pixels, "RGBA").save(buf, format="PNG")
    return buf.getvalue()


class CharacterReference(BaseModel):
    """
    One Precise Reference entry (V4.5, and V5 Full / Curated).

    ``description`` is what the model takes from the image:

    - ``"character&style"``: the character and the art style (default of the web client);
    - ``"character"``: the character;
    - ``"style"``: the art style;
    - ``"costume"``: the outfit, V5 only ("Outfit" in the web client);
    - ``"character_mainoutfit"``: Character with "Prefer same outfit" on, V5 only;
    - ``"character&style_anyoutfit"``: Character & Style with "Prefer same outfit" off, V5 only.

    On V4.5 an outfit reference is dropped and the two outfit variants become ``"character"`` and
    ``"character&style"``, as the web client does. V5 has no Fidelity: it is sent as 1.

    ``strength`` and ``fidelity`` are not bounded: the web client's sliders end at 1 (strength 5 on V5),
    but a typed value may go past that or below zero.

    Where the web client sends no reference at all, building the request raises ``ValueError`` that says what to
    use instead:

    - V5 Full Medium: Precise Reference needs High effort, use ``nai-diffusion-5-full`` (the web client switches
      to it while a reference is set and disables Medium);
    - V4 and older models;
    - inpainting on V5 Full / V5 Full Medium (V4.5 and V5 Curated inpaint with references);
    - more than 16 references.
    - ``director_reference_*`` fields with outfit descriptions on a model without outfits (build them for the
      model with ``to_params(..., model=...)``, or pass ``character_references``).

    What the web client leaves out of the request, the library leaves out too, with a ``UserWarning`` pointed at
    the caller's line: outfit references on V4.5, vibes next to a reference. ``python -W error::UserWarning`` or
    ``warnings.simplefilter("error", UserWarning)`` turns those into errors.
    """

    image: str | bytes = Field(..., description="Reference image, raw bytes or base64")
    description: str = Field(
        default="character&style",
        description='"character&style", "character", "style", "costume", "character_mainoutfit", '
        '"character&style_anyoutfit" or "delta"',
    )
    strength: float = Field(default=1.0, allow_inf_nan=False)
    fidelity: float = Field(default=1.0, allow_inf_nan=False)
    information_extracted: float = Field(default=1.0, ge=0, le=1)

    def _raw(self) -> bytes:
        return base64.b64decode(self.image) if isinstance(self.image, str) else self.image

    def padded_image_b64(self) -> str:
        """
        V4.5: the image fitted onto the canvas closest to its aspect ratio (DIRECTOR_SIZES), Lanczos,
        centred over opaque black, PNG base64.
        """
        with Image.open(BytesIO(_strip_stealth_metadata(self._raw()))) as src:
            image = src.convert("RGBA")
        aspect = image.width / image.height
        width, height = min(DIRECTOR_SIZES, key=lambda s: abs(s[0] / s[1] - aspect))
        if aspect > width / height:
            size = (width, max(1, _js_round(width / aspect)))
        else:
            size = (max(1, _js_round(height * aspect)), height)
        if size != image.size:
            image = image.resize(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        canvas.alpha_composite(image, (_js_round((width - size[0]) / 2), _js_round((height - size[1]) / 2)))
        return _png_b64(canvas.convert("RGB"))

    def bucketed_image_b64(self) -> str:
        """
        V5: the image scaled to cover the closest bucket (DIRECTOR_BUCKETS, by log aspect ratio), Lanczos,
        and cropped to it around the centre, PNG base64. An image already of a bucket's size is sent as it is.
        """
        raw = _strip_stealth_metadata(self._raw())
        with Image.open(BytesIO(raw)) as src:
            image = src.convert("RGBA")
        log_aspect = math.log(max(image.width, 1) / max(image.height, 1))
        width, height = min(DIRECTOR_BUCKETS, key=lambda b: abs(log_aspect - math.log(b[0] / b[1])))
        if image.size == (width, height):
            return base64.b64encode(raw).decode("utf-8")
        scale = max(width / image.width, height / image.height)
        resized = (
            max(_js_round(image.width * scale), width),
            max(_js_round(image.height * scale), height),
        )
        left, top = (resized[0] - width) // 2, (resized[1] - height) // 2
        image = image.resize(resized, Image.Resampling.LANCZOS).crop((left, top, left + width, top + height))
        return _png_b64(image)

    def image_b64_for(self, model: ModelTypeAlias) -> str:
        """The image prepared the way the web client prepares it for ``model``."""
        support = get_character_reference_support(model)
        if support is None:
            raise ValueError(character_reference_error(model))
        return self.bucketed_image_b64() if support.bucket else self.padded_image_b64()

    @staticmethod
    def to_params(
        references: "list[CharacterReference]", *, model: ModelTypeAlias = Model.NAI_DIFFUSION_4_5_FULL
    ) -> dict:
        """
        Request fields the web client builds from the references for ``model``: outfit references dropped
        and the outfit variants folded where the model has no outfits, fidelity 1 where it has no Fidelity,
        each image prepared for the model.

        :raises ValueError: the model takes no references, or more than MAX_CHARACTER_REFERENCES are left.
        """
        model = as_model(model)
        support = get_character_reference_support(model)
        if support is None:
            raise ValueError(character_reference_error(model))
        if not support.outfits:
            kept = [r for r in references if r.description != "costume"]
            if len(kept) < len(references):
                warn_left_out(
                    f"{model_name(model)} takes no outfit reference: "
                    f"{len(references) - len(kept)} left out of the request, as the web client does. "
                    "Outfit references need NovelAI Diffusion V5 Full or Curated."
                )
            references = [
                r.model_copy(update={"description": _FOLD_OUTFIT.get(r.description, r.description)}) for r in kept
            ]
        # before any image is decoded: the server builds these from request bodies
        if len(references) > MAX_CHARACTER_REFERENCES:
            raise ValueError(f"At most {MAX_CHARACTER_REFERENCES} Precise Reference images, got {len(references)}")
        return {
            "director_reference_images": [r.image_b64_for(model) for r in references],
            "director_reference_descriptions": [
                {"caption": {"base_caption": r.description, "char_captions": []}, "legacy_uc": False}
                for r in references
            ],
            "director_reference_information_extracted": [r.information_extracted for r in references],
            "director_reference_strength_values": [r.strength for r in references],
            "director_reference_secondary_strength_values": [
                round(1 - r.fidelity, 4) if support.fidelity else 0 for r in references
            ],
        }
