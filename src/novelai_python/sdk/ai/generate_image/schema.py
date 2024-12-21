from enum import Enum
from typing import List, Union

from pydantic import BaseModel, Field


class CharacterPosition(BaseModel):
    x: Union[float, int] = Field(0, le=0.9, ge=0, description="X")
    """
    0 Auto 
    0.1 0.3 0.5 0.7 0.9
    """
    y: Union[float, int] = Field(0, le=0.9, ge=0, description="Y")
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
    prompt: str = Field(None, description="Prompt")
    uc: str = Field("", description="Negative Prompt")
    center: Union[PositionMap, CharacterPosition] = Field(PositionMap.AUTO, description="Center")
    """Center"""

    @classmethod
    def build(cls,
              prompt: str,
              uc: str = '',
              center: Union[PositionMap, CharacterPosition] = PositionMap.AUTO
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
    char_caption: str = Field('', description="Character Caption")
    centers: List[Union[PositionMap, CharacterPosition]] = Field([PositionMap.AUTO], description="Center")
    """Center"""


class Caption(BaseModel):
    base_caption: str = Field("", description="Main Prompt")
    """Main Prompt"""
    char_captions: List[CharCaption] = Field(default_factory=list, description="Character Captions")
    """Character Captions"""


class V4Prompt(BaseModel):
    caption: Caption = Field(default_factory=Caption, description="Caption")
    use_coords: bool = Field(True, description="Use Coordinates")
    use_order: bool = Field(True, description="Use Order")

    @classmethod
    def build_from_character_prompts(cls,
                                     prompt: str,
                                     character_prompts: List[Character],
                                     use_coords: bool = True,
                                     use_order: bool = True
                                     ) -> "V4Prompt":
        """
        Build V4Prompt from character prompts
        :param prompt: The main prompt
        :param character_prompts: List of character prompts
        :param use_coords: Whether to use coordinates
        :param use_order: Whether to use order
        :return:
        """
        caption = Caption(base_caption=prompt)
        for character_prompt in character_prompts:
            char_caption = CharCaption(char_caption=character_prompt.prompt, centers=[character_prompt.center])
            caption.char_captions.append(char_caption)
        return cls(caption=caption, use_coords=use_coords, use_order=use_order)


class V4NegativePrompt(BaseModel):
    caption: Caption = Field(default_factory=Caption, description="Caption")

    @classmethod
    def build_from_character_prompts(cls,
                                     negative_prompt: str,
                                     character_prompts: List[Character]
                                     ) -> "V4NegativePrompt":
        """
        Build V4NegativePrompt from character prompts
        :param negative_prompt: The main prompt
        :param character_prompts: List of character prompts
        :return:
        """
        caption = Caption(base_caption=negative_prompt)
        for character_prompt in character_prompts:
            char_caption = CharCaption(char_caption=character_prompt.uc, centers=[character_prompt.center])
            caption.char_captions.append(char_caption)
        return cls(caption=caption)
