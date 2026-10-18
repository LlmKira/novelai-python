import base64
from enum import Enum
from io import BytesIO

from PIL import Image
from pydantic import BaseModel, Field, field_validator


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
        for character_prompt in character_prompts:
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
        for character_prompt in character_prompts:
            char_caption = CharCaption(char_caption=character_prompt.uc, centers=[character_prompt.center])
            caption.char_captions.append(char_caption)
        return cls(caption=caption, legacy_uc=legacy_uc)


# Sizes the API accepts for character reference images (validDirectorSizes in the web client)
DIRECTOR_SIZES: tuple[tuple[int, int], ...] = ((1024, 1536), (1536, 1024), (1472, 1472))


class CharacterReference(BaseModel):
    """One Precise Reference (character reference) entry, V4.5 only.

    Defaults are the web client's for a newly added image.
    """

    image: str | bytes = Field(..., description="Reference image, raw bytes or base64")
    description: str = Field(
        default="character&style", description='"character", "style", "costume", "character&style" or "delta"'
    )
    strength: float = Field(default=1.0, ge=0, le=1)
    fidelity: float = Field(default=1.0, ge=0, le=1)
    information_extracted: float = Field(default=1.0, ge=0, le=1)

    def padded_image_b64(self) -> str:
        """The image fitted onto opaque black at the director size closest to its aspect ratio, PNG base64."""
        raw = base64.b64decode(self.image) if isinstance(self.image, str) else self.image
        with Image.open(BytesIO(raw)) as src:
            img = src.convert("RGB")
        aspect = img.width / img.height
        width, height = min(DIRECTOR_SIZES, key=lambda s: abs(s[0] / s[1] - aspect))
        ratio = min(width / img.width, height / img.height)
        img = img.resize(
            (max(1, round(img.width * ratio)), max(1, round(img.height * ratio))), Image.Resampling.BICUBIC
        )
        canvas = Image.new("RGB", (width, height), (0, 0, 0))
        canvas.paste(img, ((width - img.width) // 2, (height - img.height) // 2))
        buf = BytesIO()
        canvas.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def to_params(references: "list[CharacterReference]") -> dict:
        """Request fields the web client builds from the references (applyCharacterReferenceFields)."""
        return {
            "director_reference_images": [r.padded_image_b64() for r in references],
            "director_reference_descriptions": [
                {"caption": {"base_caption": r.description, "char_captions": []}, "legacy_uc": False}
                for r in references
            ],
            "director_reference_information_extracted": [r.information_extracted for r in references],
            "director_reference_strength_values": [r.strength for r in references],
            "director_reference_secondary_strength_values": [round(1 - r.fidelity, 4) for r in references],
        }
