from typing import Literal

from novelai_python.tool.random_prompt.generate_scene_composition import (
    Conditions,
    generate_appearance,
    generate_scene_composition,
)
from novelai_python.tool.random_prompt.generate_scene_tags import generate_character_traits, generate_scene_tags
from novelai_python.tool.random_prompt.generate_tags import generate_tags, get_holiday_themed_tags


class RandomPromptGenerator:
    def __init__(self, **kwargs) -> None:
        pass

    @staticmethod
    def generate_scene_composition() -> list[str]:
        return generate_scene_composition()

    @staticmethod
    def generate_scene_tags() -> list:
        return generate_scene_tags()

    @staticmethod
    def generate_common_tags(nsfw: bool = False) -> str:
        return generate_tags(nsfw)

    @staticmethod
    def get_holiday_themed_tags() -> str:
        return get_holiday_themed_tags()

    @staticmethod
    def generate_character(
        tags: list[str], gender: Literal["m", "f", "o"], additional_tags: str | None = None, character_limit: int = 1
    ) -> str:
        """
        Generate a character based on the given tags
        :param tags: given tags
        :param gender: the gender of the character
        :param additional_tags: nothing
        :param character_limit: num of characters
        :return: random character prompt
        """
        return generate_appearance(
            tags=Conditions(tags=tags), gender=gender, additional_tags=additional_tags, character_limit=character_limit
        )

    @staticmethod
    def generate_character_traits(
        gender: Literal["m", "f", "o"],
        portrait_type: Literal[
            "half-length portrait",
            "three-quarter length portrait",
            "full-length portrait",
        ],
        level: int,
    ) -> tuple:
        """
        Generate character traits
        :param gender: one of 'm', 'f', 'o'
        :param portrait_type: one of "half-length portrait", "three-quarter length portrait", "full-length portrait"
        :param level: level of generate depth
        :return: tags(generated tags), flags(removed categories)
        """
        return generate_character_traits(gender=gender, portrait_type=portrait_type, level=level)


if __name__ == "__main__":
    gen = RandomPromptGenerator()
    for _i in range(1):
        s = RandomPromptGenerator()
        print(s.generate_common_tags(nsfw=False))
        print(s.generate_scene_tags())
        print(s.generate_scene_composition())
        print(s.get_holiday_themed_tags())
        print(
            s.generate_character(
                tags=["vampire", "werewolf"],
                gender="f",
                additional_tags="",
                character_limit=1,
            )
        )
        print(s.generate_character_traits(gender="f", portrait_type="half-length portrait", level=1))
