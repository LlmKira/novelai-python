# -*- coding: utf-8 -*-
from typing import List, Literal

# --- OLD IMPORTS (LEGACY) ---
from novelai_python.tool.random_prompt.generate_scene_composition import generate_scene_composition, \
    generate_appearance, Conditions
from novelai_python.tool.random_prompt.generate_scene_tags import generate_scene_tags, generate_character_traits
from novelai_python.tool.random_prompt.generate_tags import generate_tags, get_holiday_themed_tags

# --- NEW IMPORTS (V2 / MAGIC DICE) ---
from .generators.anime_v3 import generate_anime_v3_prompt
from .generators.anime_v4 import generate_anime_v4_prompt
from .generators.furry import generate_furry_prompt
from .generators.holiday import inject_holiday_spirit


class RandomPromptGenerator(object):
    """
    Legacy generator (V1). Based on older logic.
    Kept for backward compatibility.
    """

    def __init__(self, **kwargs):
        pass

    @staticmethod
    def generate_scene_composition() -> List[str]:
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
            tags: List[str],
            gender: Literal['m', 'f', 'o'],
            additional_tags: str = None,
            character_limit: int = 1
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
            tags=Conditions(tags=tags),
            gender=gender,
            additional_tags=additional_tags,
            character_limit=character_limit
        )

    @staticmethod
    def generate_character_traits(
            gender: Literal['m', 'f', 'o'],
            portrait_type: Literal[
                "half-length portrait",
                "three-quarter length portrait",
                "full-length portrait",
            ],
            level: int
    ) -> tuple:
        """
        Generate character traits
        :param gender: one of 'm', 'f', 'o'
        :param portrait_type: one of "half-length portrait", "three-quarter length portrait", "full-length portrait"
        :param level: level of generate depth
        :return: tags(generated tags), flags(removed categories)
        """
        return generate_character_traits(
            gender=gender,
            portrait_type=portrait_type,
            level=level
        )


class RandomPromptGeneratorV2(object):
    """
    New generator (V2). Based on NovelAI 'Magic Dice' logic (2024).
    Supports Anime V3, V4 and Furry modes with advanced tag compatibility logic.
    """

    @staticmethod
    def generate(
        model: Literal["anime_v3", "anime_v4", "furry"] = "anime_v4", 
        holiday: bool = False,
        nsfw: bool = False
    ) -> str:
        """
        Generates a random prompt using the exact logic from the web UI.
        
        :param model: Model type. 
                      'anime_v3' (Curated/Full V3) - The most varied generator (Magic Dice style).
                      'anime_v4' (Curated/Full V4) - Newer tags, stricter compatibility logic.
                      'furry' (Furry V3) - Specialized for furry species and attributes.
        :param holiday: Adds Christmas/Winter tags if current date is in December.
        :param nsfw: Enables NSFW logic (mostly affects 'furry' mode and some V4 logic).
        :return: A string of comma-separated tags.
        """
        if model == "anime_v3":
            # V3 logic in JS doesn't have explicit NSFW toggle, tags are mixed in lists
            return generate_anime_v3_prompt(use_holiday=holiday, is_nsfw=nsfw)
        elif model == "anime_v4":
            return generate_anime_v4_prompt(use_holiday=holiday, is_nsfw=nsfw)
        elif model == "furry":
            return generate_furry_prompt(use_holiday=holiday, is_nsfw=nsfw)
        else:
            raise ValueError(f"Unknown random prompt model: {model}. Available: anime_v3, anime_v4, furry")

    @staticmethod
    def apply_holiday(prompt: str) -> str:
        """Applies holiday tags injection to an existing prompt."""
        return inject_holiday_spirit(prompt)

generate_random_prompt = RandomPromptGeneratorV2.generate

apply_holiday_spirit = RandomPromptGeneratorV2.apply_holiday

if __name__ == '__main__':
    print("--- Legacy Generator ---")
    gen = RandomPromptGenerator()
    print(gen.generate_common_tags(nsfw=False))

    print("\n--- V2 Generator (Magic Dice) ---")
    gen_v2 = RandomPromptGeneratorV2()
    print("Anime V3:", gen_v2.generate(model="anime_v3"))
    print("Anime V4:", gen_v2.generate(model="anime_v4"))
    print("Furry (NSFW):", gen_v2.generate(model="furry", nsfw=True))