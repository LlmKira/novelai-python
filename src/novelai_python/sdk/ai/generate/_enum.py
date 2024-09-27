import json
import pathlib
from functools import lru_cache
from typing import List, Dict, Optional

from novelai_python._enum import TextLLMModelTypeAlias, TextTokenizerGroup, TextLLMModel, \
    COLORS_LLM
from novelai_python.sdk.ai.generate._const import BanWords, DefaultBanWords, RepetitionPenaltyWhitelist
from novelai_python.sdk.ai.generate._schema import Theme, Preset, StoryDefault, ContextConfig, LoreDefaults, \
    EphemeralDefaults, ContextDefaults, ContextPresets, KeyOrderEntry, Key, PenStyle, LLMGenerationParams, \
    LogitBiasGroup

themes_json = pathlib.Path(__file__).parent / "themes.json"


@lru_cache
def get_themes() -> List[Theme]:
    theme_data = json.loads(themes_json.read_text())
    assert isinstance(theme_data, list)
    return [Theme.model_validate(data) for data in theme_data]


def get_bad_words_ids(group: TextTokenizerGroup, use_banBrackets: bool):
    if use_banBrackets:
        ban_words = BanWords()
    else:
        ban_words = DefaultBanWords()
    if group == TextTokenizerGroup.GENJI:
        return ban_words.GENJI
    elif group == TextTokenizerGroup.PILE:
        return ban_words.PILE
    elif group == TextTokenizerGroup.PILE_NAI:
        if use_banBrackets:
            return ban_words.PILE_NAI
        else:
            return ban_words.PILE
    elif group == TextTokenizerGroup.GPT2:
        return ban_words.GPT2
    elif group in [TextTokenizerGroup.NERDSTASH, TextTokenizerGroup.NERDSTASH_V2]:
        return ban_words.NERDSTASH
    elif group == TextTokenizerGroup.LLAMA3 and use_banBrackets:
        return ban_words.LLAMA3
    return []


def get_eos_token_id(group: TextTokenizerGroup):
    if group in [TextTokenizerGroup.PILE, TextTokenizerGroup.PILE_NAI]:
        return 31
    elif group == TextTokenizerGroup.GPT2:
        return 29
    elif group in [TextTokenizerGroup.NERDSTASH, TextTokenizerGroup.NERDSTASH_V2]:
        return 49405
    elif group == TextTokenizerGroup.LLAMA3:
        return 29
    raise NotImplementedError(f"Invalid tokenizer for adventure EOS token")


def get_end_exclude_sequences(group: TextTokenizerGroup):
    if group in [TextTokenizerGroup.PILE, TextTokenizerGroup.PILE_NAI]:
        return [[187, 31]]
    elif group == TextTokenizerGroup.GPT2:
        return [[198, 29]]
    elif group in [TextTokenizerGroup.NERDSTASH, TextTokenizerGroup.NERDSTASH_V2]:
        return [[85, 49405]]
    elif group == TextTokenizerGroup.LLAMA3:
        return [[29]]
    raise NotImplementedError(f"Invalid tokenizer for adventure end sequences")


def get_logit_bias_group(group: TextTokenizerGroup):
    """
    Get logit bias group
    :param group:
    :return:
    """
    if group == TextTokenizerGroup.GENJI:
        return [
            LogitBiasGroup(sequence=[7398], bias=-0.25, ensure_sequence_finish=False, generate_once=False),
            LogitBiasGroup(sequence=[15864], bias=-0.25, ensure_sequence_finish=False, generate_once=False),
            LogitBiasGroup(sequence=[29146], bias=-0.25, ensure_sequence_finish=False, generate_once=False),
            LogitBiasGroup(sequence=[4707], bias=-0.25, ensure_sequence_finish=False, generate_once=False)
        ]
    return []


def pickup_reverse_bias_model(model: TextLLMModelTypeAlias):
    """
    :param model: model
    :return:
    """
    if model in [TextLLMModel.J_6B, TextLLMModel.J_6B_V3, TextLLMModel.J_6B_V4]:
        return TextLLMModel.J_6B_V4
    elif model == TextLLMModel.NEO_2B:
        return TextLLMModel.NEO_2B
    elif model in [TextLLMModel.GENJI_JP_6B, TextLLMModel.GENJI_JP_6B_V2]:
        return TextLLMModel.GENJI_JP_6B_V2
    elif model == TextLLMModel.GENJI_PYTHON_6B:
        return TextLLMModel.GENJI_PYTHON_6B
    elif model in [TextLLMModel.EUTERPE_V0, TextLLMModel.EUTERPE_V2]:
        return TextLLMModel.EUTERPE_V2
    elif model in [TextLLMModel.KRAKE_V1, TextLLMModel.KRAKE_V2]:
        return TextLLMModel.KRAKE_V2
    return model


def get_default_prefix(model: TextLLMModel) -> List[str]:
    """
    Get prefix for model
    :param model:
    :return:
    """
    if model in [TextLLMModel.J_6B_V4, TextLLMModel.EUTERPE_V2]:
        return [
            theme.label for theme in get_themes()
            if theme.label not in ["special_instruct", "special_openings"]
        ]
    elif model == TextLLMModel.KRAKE_V2:
        return [
            "vanilla", "general_crossgenre", "theme_textadventure", "style_algernonblackwood",
            "style_arthurconandoyle", "style_edgarallanpoe", "style_hplovecraft", "style_shridanlefanu",
            "style_julesverne", "theme_19thcenturyromance", "theme_actionarcheology", "theme_ai",
            "theme_animalfiction", "theme_childrens", "theme_christmas", "theme_comedicfantasy", "theme_cyberpunk",
            "theme_darkfantasy", "theme_dragons", "theme_egypt", "theme_feudaljapan", "theme_generalfantasy",
            "theme_history", "theme_horror", "theme_huntergatherer", "theme_litrpg", "theme_magicacademy",
            "theme_libraries", "theme_mars", "theme_medieval", "theme_militaryscifi", "theme_mystery",
            "theme_naval", "theme_philosophy", "theme_pirates", "theme_poeticfantasy", "theme_postapocalyptic",
            "theme_rats", "theme_romanempire", "theme_sciencefantasy", "theme_spaceopera", "theme_superheroes",
            "theme_airships", "theme_travel", "theme_urbanfantasy", "theme_valentines", "theme_vikings",
            "theme_westernromance", "inspiration_crabsnailandmonkey", "inspiration_mercantilewolfgirlromance",
            "inspiration_nervegear", "theme_romanceofthreekingdoms", "inspiration_thronewars",
            "inspiration_witchatlevelcap"
        ]
    elif model in [TextLLMModel.CASSANDRA] + COLORS_LLM:
        return ["vanilla", "special_instruct", "special_proseaugmenter", "theme_textadventure"]
    elif model == TextLLMModel.KAYRA:
        return ["vanilla", "special_instruct", "special_proseaugmenter", "theme_textadventure", "theme_christmas"]
    return []


def get_repetition_penalty_whitelist(group: TextTokenizerGroup) -> List[str]:
    whitelist = RepetitionPenaltyWhitelist()
    if group == TextTokenizerGroup.NERDSTASH:
        return whitelist.NERDSTASH
    elif group == TextTokenizerGroup.NERDSTASH_V2:
        return whitelist.NERDSTASH_V2
    elif group == TextTokenizerGroup.LLAMA3:
        return whitelist.LLAMA3
    return []


def get_model_preset(model: TextLLMModel) -> "ModelPresetManager":
    return PresetMapping.get(model, Default)


def get_default_preset(model: TextLLMModel) -> Preset:
    return get_model_preset(model).get_all_presets()[0]


class ModelPresetManager:
    def __init__(self):
        self.presets: Dict[TextLLMModel, List[Preset]] = {}

    def register_preset(self, model: TextLLMModel, preset: Preset) -> None:
        if model not in self.presets:
            self.presets[model] = []
        self.presets[model].append(preset)

    def get_presets(self, model: TextLLMModel) -> list[Preset]:
        return self.presets.get(model, [])

    def get_all_presets(self) -> List[Preset]:
        return [preset for presets in self.presets.values() for preset in presets]

    def get_preset_by_id(self, model: TextLLMModel, preset_id: str) -> Optional[Preset]:
        for preset in self.get_presets(model):
            if preset.id == preset_id:
                return preset
        return None


Default = ModelPresetManager()
Default.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Sigurd Lore Generation",
        id="default-sigurdloregen",
        parameters=LLMGenerationParams(
            temperature=0.34,
            top_k=1,
            top_p=1,
            top_a=1,
            typical_p=0.8,
            tail_free_sampling=1,
            repetition_penalty=2.725,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="The default Lore Generation preset for Sigurd."
    )
)
Default.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Euterpe Lore Generation",
        id="default-euterpeloregen",
        parameters=LLMGenerationParams(
            temperature=0.34,
            top_k=1,
            top_p=1,
            top_a=1,
            typical_p=0.8,
            tail_free_sampling=1,
            repetition_penalty=2.725,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="The default Lore Generation preset for Euterpe."
    )
)

Default.register_preset(
    TextLLMModel.CLIO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Fresh Coffee",
        id="default-freshcoffee",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=25,
            top_p=1,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.925,
            repetition_penalty=1.9,
            repetition_penalty_range=768,
            repetition_penalty_slope=3.33,
            repetition_penalty_frequency=0.0025,
            repetition_penalty_presence=0.001,
            repetition_penalty_default_whitelist=True,
            phrase_rep_pen=PenStyle.VeryLight,  # Assuming PenStyle is an Enum or similar
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description=""
    )
)

J6bv4 = ModelPresetManager()
J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Storywriter",
        id="default-trueoptimalnucleus",
        parameters=LLMGenerationParams(
            temperature=0.72,
            max_length=40,
            min_length=1,
            top_k=0,
            top_p=0.725,
            tail_free_sampling=1,
            repetition_penalty=2.75,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.18,
            bad_words_ids=[]
        ),
        description="Optimized settings for relevant output."
    )
)

J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Coherent Creativity",
        id="default-coherentcreativity",
        parameters=LLMGenerationParams(
            temperature=0.51,
            max_length=40,
            min_length=1,
            top_k=0,
            top_p=1,
            tail_free_sampling=0.992,
            repetition_penalty=3.875,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            bad_words_ids=[]
        ),
        description="A good balance between coherence, creativity, and quality of prose."
    )
)

J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Luna Moth",
        id="default-moth-luna",
        parameters=LLMGenerationParams(
            temperature=2,
            max_length=40,
            min_length=1,
            top_k=85,
            top_p=0.235,
            tail_free_sampling=1,
            repetition_penalty=2.975,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            bad_words_ids=[]
        ),
        description="A great degree of creativity without losing coherency."
    )
)

J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Sphinx Moth",
        id="default-moth-sphinx",
        parameters=LLMGenerationParams(
            temperature=2.5,
            max_length=40,
            min_length=1,
            top_k=30,
            top_p=0.175,
            tail_free_sampling=1,
            repetition_penalty=3,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            bad_words_ids=[]
        ),
        description="Maximum randomness while still being plot relevant. Like Sphinx riddles!"
    )
)

J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Emperor Moth",
        id="default-moth-emperor",
        parameters=LLMGenerationParams(
            temperature=1.25,
            max_length=40,
            min_length=1,
            top_k=0,
            top_p=0.235,
            tail_free_sampling=1,
            repetition_penalty=2.75,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            bad_words_ids=[]
        ),
        description="Medium randomness with a decent bit of creative writing.",
        contextPresets=None
    )
)

J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Best Guess",
        id="default-bestguess",
        parameters=LLMGenerationParams(
            temperature=0.8,
            max_length=40,
            min_length=1,
            top_k=110,
            top_p=0.9,
            tail_free_sampling=1,
            repetition_penalty=3.1,
            repetition_penalty_range=512,
            repetition_penalty_slope=3.33,
            bad_words_ids=[]
        ),
        description="A subtle change with alternative context settings.",
        contextPresets=ContextPresets(
            contextDefaults=[
                ContextDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="[",
                        suffix="]\n",
                        tokenBudget=1,
                        reservedTokens=1,
                        budgetPriority=-100,
                        trimDirection="doNotTrim",
                        insertionType="newline",
                        maximumTrimType="sentence",
                        insertionPosition=-12
                    )
                ),
                ContextDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="[",
                        suffix="]\n",
                        tokenBudget=1,
                        reservedTokens=1,
                        budgetPriority=-800,
                        trimDirection="doNotTrim",
                        insertionType="newline",
                        maximumTrimType="sentence",
                        insertionPosition=-4
                    )
                )
            ],
            ephemeralDefaults=[
                EphemeralDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="",
                        suffix="\n",
                        tokenBudget=1,
                        reservedTokens=1,
                        budgetPriority=-100,
                        trimDirection="doNotTrim",
                        insertionType="newline",
                        maximumTrimType="newline",
                        insertionPosition=-2
                    ),
                    startingStep=1,
                    delay=0,
                    duration=1,
                    repeat=False,
                    reverse=False
                )
            ],
            loreDefaults=[
                LoreDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="[",
                        suffix="]\n",
                        tokenBudget=1,
                        reservedTokens=1,
                        budgetPriority=-200,
                        trimDirection="trimBottom",
                        insertionType="newline",
                        maximumTrimType="sentence",
                        insertionPosition=-10
                    ),
                    lastUpdatedAt="2021-07-19T01:16:17.425Z",
                    displayName="New Lorebook Entry",
                    keys=[],
                    searchRange=1000,
                    enabled=True,
                    forceActivation=False,
                    keyRelative=False,
                    nonStoryActivatable=False
                )
            ],
            storyDefault=StoryDefault(
                prefix="",
                suffix="",
                tokenBudget=1,
                reservedTokens=512,
                budgetPriority=0,
                trimDirection="trimTop",
                insertionType="newline",
                maximumTrimType="sentence",
                insertionPosition=-1
            )
        )
    )
)
J6bv4.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Pleasing Results",
        id="default-pleasingresults",
        parameters=LLMGenerationParams(
            temperature=0.44,
            max_length=40,
            min_length=1,
            top_k=0,
            top_p=1,
            tail_free_sampling=0.9,
            repetition_penalty=3.35,
            repetition_penalty_range=1024,
            repetition_penalty_slope=6.75,
            bad_words_ids=[]
        ),
        description="Expectable output with alternative context settings.",
        contextPresets=ContextPresets(
            contextDefaults=[
                ContextDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="",
                        suffix="\n",
                        tokenBudget=1,
                        reservedTokens=206,
                        budgetPriority=-200,
                        trimDirection="trimBottom",
                        insertionType="newline",
                        maximumTrimType="sentence",
                        insertionPosition=-11
                    )
                ),
                ContextDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="",
                        suffix="\n",
                        tokenBudget=1,
                        reservedTokens=1,
                        budgetPriority=-400,
                        trimDirection="trimBottom",
                        insertionType="newline",
                        maximumTrimType="sentence",
                        insertionPosition=-4
                    )
                )
            ],
            ephemeralDefaults=[
                EphemeralDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="",
                        suffix="\n",
                        tokenBudget=1,
                        reservedTokens=1,
                        budgetPriority=-10000,
                        trimDirection="doNotTrim",
                        insertionType="newline",
                        maximumTrimType="newline",
                        insertionPosition=-2,
                    ),
                    startingStep=1,
                    delay=0,
                    duration=1,
                    repeat=False,
                    reverse=False
                )
            ],
            loreDefaults=[
                LoreDefaults(
                    text="",
                    contextConfig=ContextConfig(
                        prefix="",
                        suffix="\n",
                        tokenBudget=1,
                        reservedTokens=0,
                        budgetPriority=400,
                        trimDirection="trimBottom",
                        insertionType="newline",
                        maximumTrimType="sentence",
                        insertionPosition=-1
                    ),
                    lastUpdatedAt="2021-07-19T00:36:55.977Z",
                    displayName="New Lorebook Entry",
                    keys=[],
                    searchRange=1000,
                    enabled=True,
                    forceActivation=False,
                    keyRelative=False,
                    nonStoryActivatable=False
                )
            ],
            storyDefault=StoryDefault(
                prefix="",
                suffix="",
                tokenBudget=1,
                reservedTokens=512,
                budgetPriority=0,
                trimDirection="trimTop",
                insertionType="newline",
                maximumTrimType="sentence",
                insertionPosition=-1
            )
        )
    )
)
Neo2b = ModelPresetManager()

Neo2b.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Storywriter (Calliope)",
        id="defaultcalliope-trueoptimalnucleus",
        parameters=LLMGenerationParams(
            temperature=0.72,
            top_k=0,
            top_p=0.725,
            tail_free_sampling=1,
            repetition_penalty=2.75,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.18,
            bad_words_ids=[]
        ),
        description="Optimized settings for relevant output."
    )
)

Genjipython6b = ModelPresetManager()
Genjipython6b.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Storywriter (Snek)",
        id="defaultsnek-trueoptimalnucleus",
        parameters=LLMGenerationParams(
            temperature=0.72,
            top_k=0,
            top_p=0.725,
            tail_free_sampling=1,
            repetition_penalty=2.75,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.18,
            bad_words_ids=[]
        ),
        description="Optimized settings for relevant output."
    )
)

Genjijp6bv2 = ModelPresetManager()

Genjijp6bv2.register_preset(
    TextLLMModel.J_6B_V4,
    Preset(
        presetVersion=2,
        remoteId="",
        name="Genji Default",
        id="defaultgenji-genji",
        parameters=LLMGenerationParams(
            temperature=0.86,
            top_k=0,
            top_p=1,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.927,
            repetition_penalty=2.9,
            repetition_penalty_range=2048,
            repetition_penalty_slope=3.33,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0
        ),
        description="Default Settings",
    )
)

Euterpev2 = ModelPresetManager()
Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Genesis",
        id="default-genesis",
        parameters=LLMGenerationParams(
            temperature=0.63,
            top_k=0,
            top_p=0.975,
            tail_free_sampling=0.975,
            repetition_penalty=2.975,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Stable and logical, but with scattered creativity."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Basic Coherence",
        id="default-basic-coherence",
        parameters=LLMGenerationParams(
            temperature=0.585,
            top_k=0,
            top_p=1,
            tail_free_sampling=0.87,
            repetition_penalty=3.05,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.33,
        ),
        description="Keeps things on track."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Ouroboros",
        id="default-ouroboros",
        parameters=LLMGenerationParams(
            temperature=1.07,
            top_k=264,
            top_p=1,
            tail_free_sampling=0.925,
            repetition_penalty=2.165,
            repetition_penalty_range=404,
            repetition_penalty_slope=0.84,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Versatile, conforms well to poems, lists, chat, etc."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Ace of Spades",
        id="default-ace-of-spades",
        parameters=LLMGenerationParams(
            temperature=1.15,
            max_length=30,
            top_k=0,
            top_p=0.95,
            tail_free_sampling=0.8,
            repetition_penalty=2.75,
            repetition_penalty_range=2048,
            repetition_penalty_slope=7.02,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Expressive, while still staying focused."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Moonlit Chronicler",
        id="default-moonlit-chronicler",
        parameters=LLMGenerationParams(
            temperature=1.25,
            top_k=300,
            top_p=1,
            top_a=0.782,
            typical_p=0.95,
            tail_free_sampling=0.802,
            repetition_penalty=2.075,
            repetition_penalty_range=512,
            repetition_penalty_slope=0.36,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Tells a tale with confidence, but variety where it matters."
    )
)
Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Fandango",
        id="default-fandango",
        parameters=LLMGenerationParams(
            temperature=0.86,
            top_k=20,
            top_p=0.95,
            tail_free_sampling=1,
            repetition_penalty=2.25,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            # Assuming Key is a correct mapping for the order items
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
            ]
        ),
        description="A rhythmic dance of prose, whoever takes the lead."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="All-Nighter",
        id="default-all-nighter",
        parameters=LLMGenerationParams(
            temperature=1.33,
            top_k=13,
            top_p=1,
            tail_free_sampling=0.836,
            repetition_penalty=2.366,
            repetition_penalty_range=400,
            repetition_penalty_slope=0.33,
            repetition_penalty_frequency=0.01,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Creative diction with room for embellishments."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Low Rider",
        id="default-low-rider-2",
        parameters=LLMGenerationParams(
            temperature=0.94,
            top_k=12,
            top_p=1,
            tail_free_sampling=0.94,
            repetition_penalty=2.66,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.18,
            repetition_penalty_frequency=0.013,
            repetition_penalty_presence=0,
            # Assuming a mapping for the order as per your schema
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Reliable, aimed at story development."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Morpho",
        id="default-morpho",
        parameters=LLMGenerationParams(
            temperature=0.6889,
            max_length=25,
            top_k=0,
            top_p=1,
            tail_free_sampling=1,
            repetition_penalty=1,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0.1,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Let the AI generate without constraints."
    )
)

Euterpev2.register_preset(
    TextLLMModel.EUTERPE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Pro Writer",
        id="default-prowriter20",
        parameters=LLMGenerationParams(
            temperature=1.348,
            top_k=64,
            top_p=0.909,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.688,
            repetition_penalty=4.967,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Optimal settings for readability, based on AI-powered mass statistical analysis of Euterpe output."
    )
)

Krakev1 = ModelPresetManager()
Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Astraea",
        id="default-astreacreative",
        parameters=LLMGenerationParams(
            temperature=0.9,
            top_k=22,
            top_p=0.85,
            top_a=1,
            typical_p=0.9,
            tail_free_sampling=0.92,
            repetition_penalty=1.024,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Follows your style with precision."
    )
)

Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Blackjack",
        id="default-blackjack",
        parameters=LLMGenerationParams(
            temperature=1.3,
            top_k=0,
            top_p=0.98,
            top_a=0.98,
            typical_p=1,
            tail_free_sampling=0.95,
            repetition_penalty=1.005,
            repetition_penalty_range=2048,
            repetition_penalty_slope=4,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Balanced probability with the chance for less obvious outcomes."
    )
)

Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Adder",
        id="default-adder04",
        parameters=LLMGenerationParams(
            temperature=1.06,
            max_length=17,
            top_k=0,
            top_p=0.85,
            top_a=0.086,
            typical_p=0.986,
            tail_free_sampling=0.961,
            repetition_penalty=1.016,
            repetition_penalty_range=720,
            repetition_penalty_slope=0.77,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="For logic and narrative progression with the right amount of spice."
    )
)
Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="20BC",
        id="default-20bc",
        parameters=LLMGenerationParams(
            temperature=0.55,
            top_k=0,
            top_p=1,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.872,
            repetition_penalty=1.03,
            repetition_penalty_range=2048,
            repetition_penalty_slope=3.33,
            bad_words_ids=[],
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Keeps things on track."
    )
)
Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Ptah",
        id="default-ptah",
        parameters=LLMGenerationParams(
            temperature=0.98,
            top_k=150,
            top_p=0.825,
            top_a=1,
            typical_p=0.95,
            tail_free_sampling=0.84,
            repetition_penalty=1.032,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Gives you the tools to build your worlds."
    )
)
Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Iris",
        id="default-iris",
        parameters=LLMGenerationParams(
            temperature=2.5,
            top_k=0,
            top_p=1,
            top_a=1,
            typical_p=0.799,
            tail_free_sampling=0.9,
            repetition_penalty=1,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="A wide array of ideas from beyond to shake up your writing."
    )
)
Krakev1.register_preset(
    TextLLMModel.KRAKE_V1,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Calypso",
        id="default-calypso",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=20,
            top_p=1,
            top_a=0.2,
            typical_p=1,
            tail_free_sampling=1,
            repetition_penalty=1.04,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Creatively elaborates upon an existing scene."
    )
)
Krakev2 = ModelPresetManager()

Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Blue Lighter",
        id="default-blue-lighter",
        parameters=LLMGenerationParams(
            temperature=1.33,
            top_k=81,
            top_p=0.88,
            top_a=0.085,
            typical_p=0.965,
            tail_free_sampling=0.937,
            repetition_penalty=1.05,
            repetition_penalty_range=560,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Easy to steer, imaginative, and fast-paced."
    )
)
Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Redjack",
        id="default-redjack",
        parameters=LLMGenerationParams(
            temperature=1.1,
            top_k=0,
            top_p=0.96,
            top_a=0.98,
            typical_p=1,
            tail_free_sampling=0.92,
            repetition_penalty=1.0075,
            repetition_penalty_range=2048,
            repetition_penalty_slope=4,
            repetition_penalty_frequency=0.025,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Focuses on staying on track, only rarely deviating from what's already written."
    )
)
Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Reverie",
        id="default-reverie",
        parameters=LLMGenerationParams(
            temperature=0.925,
            top_k=85,
            top_p=0.985,
            top_a=0.12,
            typical_p=0.85,
            tail_free_sampling=0.925,
            repetition_penalty=1.0225,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Narrative consistency with a focus on paying attention to memory and module content."
    )
)

Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Top Gun Beta",
        id="default-topgun-beta",
        parameters=LLMGenerationParams(
            temperature=0.58,
            top_k=10,
            top_p=0.675,
            top_a=0.1,
            typical_p=0.985,
            tail_free_sampling=0.919,
            repetition_penalty=1.05,
            repetition_penalty_range=880,
            repetition_penalty_slope=0.2,
            repetition_penalty_frequency=0.02,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Creative and fast-paced. Go into less expected directions while staying coherent and avoiding repetitive loops."
    )
)
Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Calypso",
        id="default-calypso",
        parameters=LLMGenerationParams(
            temperature=1.1,
            top_k=10,
            top_p=0.95,
            top_a=0.15,
            typical_p=0.95,
            tail_free_sampling=0.95,
            repetition_penalty=1.075,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Weave an enrapturing endless tale, custom fit for 2nd person perspective but highly flexible for other uses."
    )
)
Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Blue Adder",
        id="default-blue-adder",
        parameters=LLMGenerationParams(
            temperature=1.01,
            top_k=0,
            top_p=0.7,
            top_a=0.06,
            typical_p=0.996,
            tail_free_sampling=0.991,
            repetition_penalty=1.02325,
            repetition_penalty_range=496,
            repetition_penalty_slope=0.72,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Jumps from one idea to the next, logical but unpredictable."
    )
)

Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="20BC+",
        id="default-20bcplus",
        parameters=LLMGenerationParams(
            temperature=0.58,
            max_length=75,
            min_length=1,
            top_k=20,
            top_p=1,
            top_a=0.05,
            typical_p=0.985,
            tail_free_sampling=0.879,
            repetition_penalty=1.055,
            repetition_penalty_range=2048,
            repetition_penalty_slope=3.33,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Keeps things on track."
    )
)
Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Calibrated",
        id="default-calibrated",
        parameters=LLMGenerationParams(
            temperature=0.34,
            top_k=0,
            top_p=1,
            top_a=1,
            typical_p=0.975,
            tail_free_sampling=1,
            repetition_penalty=1.036,
            repetition_penalty_range=2048,
            repetition_penalty_slope=3.33,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Adjusted for highly consistent output."
    )
)
Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Iris",
        id="default-iris",
        parameters=LLMGenerationParams(
            temperature=2.5,
            top_k=0,
            top_p=1,
            top_a=1,
            typical_p=0.9566,
            tail_free_sampling=0.97,
            repetition_penalty=1,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Imaginative and original, a kaleidoscope of unpredictability."
    )
)

Krakev2.register_preset(
    TextLLMModel.KRAKE_V2,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Krait",
        id="default-krait",
        parameters=LLMGenerationParams(
            temperature=0.9,
            top_k=1000,
            top_p=0.992,
            top_a=0.072,
            typical_p=0.98,
            tail_free_sampling=0.997,
            repetition_penalty=1.0236,
            repetition_penalty_range=610,
            repetition_penalty_slope=0.85,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Controlled chaos, for random generation and chat style."
    )
)
Colorful = ModelPresetManager()
Colorful.register_preset(
    TextLLMModel.BLUE,
    Preset(
        presetVersion=3,
        remoteId="",
        name="⬜️",
        id="default-na",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=0,
            top_p=1,
            tail_free_sampling=0.87,
            repetition_penalty=1,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0
        ),
        description=""
    )
)
Clio = ModelPresetManager()
Clio.register_preset(
    TextLLMModel.CLIO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Vingt-Un",
        id="default-vigntun",
        parameters=LLMGenerationParams(
            temperature=1.21,
            top_k=0,
            top_p=0.912,
            top_a=1,
            typical_p=0.912,
            tail_free_sampling=0.921,
            repetition_penalty=1.21,
            repetition_penalty_range=321,
            repetition_penalty_slope=2.1,
            repetition_penalty_frequency=0.00621,
            repetition_penalty_presence=0,
            phrase_rep_pen=PenStyle.VeryLight,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="A good all-around default with a bent towards prose."
    )
)

Clio.register_preset(
    TextLLMModel.CLIO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Long Press",
        id="default-longpress",
        parameters=LLMGenerationParams(
            temperature=1.155,
            top_k=25,
            top_p=1,
            top_a=0.265,
            typical_p=0.985,
            tail_free_sampling=0.88,
            repetition_penalty=1.65,
            repetition_penalty_range=8192,
            repetition_penalty_slope=1.5,
            repetition_penalty_frequency=0.0085,
            repetition_penalty_presence=0.0125,
            repetition_penalty_default_whitelist=True,
            phrase_rep_pen=PenStyle.VeryLight,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Intended for creative prose."
    )
)
Clio.register_preset(
    TextLLMModel.CLIO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Edgewise",
        id="default-edgewise",
        parameters=LLMGenerationParams(
            temperature=1.09,
            top_k=0,
            top_p=0.969,
            top_a=0.09,
            typical_p=0.99,
            tail_free_sampling=0.969,
            repetition_penalty=1.09,
            repetition_penalty_range=8192,
            repetition_penalty_slope=0.069,
            repetition_penalty_frequency=0.006,
            repetition_penalty_presence=0.009,
            repetition_penalty_default_whitelist=True,
            phrase_rep_pen=PenStyle.VeryLight,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Handles a variety of generation styles well."
    )
)
Clio.register_preset(
    TextLLMModel.CLIO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Fresh Coffee",
        id="default-freshcoffee",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=25,
            top_p=1,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.925,
            repetition_penalty=1.9,
            repetition_penalty_range=768,
            repetition_penalty_slope=3.33,
            repetition_penalty_frequency=0.0025,
            repetition_penalty_presence=0.001,
            repetition_penalty_default_whitelist=True,
            phrase_rep_pen=PenStyle.VeryLight,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Keeps things on track."
    )
)
Clio.register_preset(
    TextLLMModel.CLIO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Talker C",
        id="default-talkerc",
        parameters=LLMGenerationParams(
            temperature=1.5,
            top_k=10,
            top_p=0.75,
            top_a=0.08,
            typical_p=0.975,
            tail_free_sampling=0.967,
            repetition_penalty=2.25,
            repetition_penalty_range=8192,
            repetition_penalty_slope=0.09,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0.005,
            repetition_penalty_default_whitelist=True,
            phrase_rep_pen=PenStyle.VeryLight,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Designed for chat style generation."
    )
)
Kayra = ModelPresetManager()
Kayra.register_preset(
    TextLLMModel.KAYRA,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Carefree",
        id="default-carefree",
        parameters=LLMGenerationParams(
            temperature=1.35,
            top_k=15,
            top_p=0.85,
            top_a=0.1,
            typical_p=1,
            tail_free_sampling=0.915,
            repetition_penalty=2.8,
            repetition_penalty_range=2048,
            repetition_penalty_slope=0.02,
            repetition_penalty_frequency=0.02,
            repetition_penalty_presence=0,
            repetition_penalty_default_whitelist=True,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Aggressive,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False)
            ]
        ),
        description="A good all-rounder."
    )
)
Kayra.register_preset(
    TextLLMModel.KAYRA,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Stelenes",
        id="default-stelenes",
        parameters=LLMGenerationParams(
            temperature=2.5,
            top_k=0,
            top_p=1,
            top_a=1,
            typical_p=0.969,
            tail_free_sampling=0.941,
            repetition_penalty=1,
            repetition_penalty_range=1024,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            repetition_penalty_default_whitelist=True,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Default,
            top_g=0,
            mirostat_tau=0,
            mirostat_lr=1,
            order=[
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False)
            ]
        ),
        description="More likely to choose reasonable alternatives. Variety on retries."
    )
)
Kayra.register_preset(
    TextLLMModel.KAYRA,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Fresh Coffee",
        id="default-freshcoffeek",
        parameters=LLMGenerationParams(
            temperature=1,
            max_length=60,
            top_k=25,
            top_p=1,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.925,
            repetition_penalty=1.9,
            repetition_penalty_range=768,
            repetition_penalty_slope=1,
            repetition_penalty_frequency=0.0025,
            repetition_penalty_presence=0.001,
            repetition_penalty_default_whitelist=False,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Off,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False)
            ]
        ),
        description="Keeps things on track. Handles instruct well."
    )
)
Kayra.register_preset(
    TextLLMModel.KAYRA,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Asper",
        id="default-asper",
        parameters=LLMGenerationParams(
            temperature=1.16,
            top_k=175,
            top_p=0.998,
            top_a=0.004,
            typical_p=0.96,
            tail_free_sampling=0.994,
            repetition_penalty=1.68,
            repetition_penalty_range=2240,
            repetition_penalty_slope=1.5,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0.005,
            repetition_penalty_default_whitelist=True,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Default,
            top_g=8,
            mirostat_tau=0,
            mirostat_lr=1,
            order=[
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False)
            ]
        ),
        description="For creative writing. Expect unexpected twists."
    )
)

Kayra.register_preset(
    TextLLMModel.KAYRA,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Writer's Daemon",
        id="default-writersdaemon",
        parameters=LLMGenerationParams(
            temperature=1.5,
            top_k=70,
            top_p=0.95,
            top_a=0.02,
            typical_p=0.95,
            tail_free_sampling=0.95,
            repetition_penalty=1.625,
            repetition_penalty_range=2016,
            repetition_penalty_slope=0,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.VeryAggressive,
            top_g=0,
            mirostat_tau=5,
            mirostat_lr=0.25,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.TFS, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False)
            ]
        ),
        description="Extremely imaginative, sometimes too much."
    )
)

Erato = ModelPresetManager()
Erato.register_preset(
    TextLLMModel.ERATO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Golden Arrow",
        id="default-erato-goldenarrow",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=0,
            top_p=0.995,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.87,
            repetition_penalty=1.5,
            repetition_penalty_range=2240,
            repetition_penalty_slope=1,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            repetition_penalty_default_whitelist=True,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Light,  # Mapping "light" to PenStyle.Light
            top_g=0,
            mirostat_tau=0,
            mirostat_lr=1,
            math1_temp=0.3,
            math1_quad=0.19,
            math1_quad_entropy_scale=0,
            min_p=0,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False)
            ]
        ),
        description="A good all-rounder."
    )
)
Erato.register_preset(
    TextLLMModel.ERATO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Wilder",
        id="default-erato-wilder",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=300,
            top_p=0.98,
            top_a=0.004,
            typical_p=0.96,
            tail_free_sampling=0.96,
            repetition_penalty=1.48,
            repetition_penalty_range=2240,
            repetition_penalty_slope=0.64,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            repetition_penalty_default_whitelist=True,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Default,
            top_g=0,
            mirostat_tau=0,
            mirostat_lr=1,
            math1_temp=-0.0485,
            math1_quad=0.145,
            math1_quad_entropy_scale=0,
            min_p=0.02,
            order=[
                KeyOrderEntry(id=Key.Math1, enabled=True),
                KeyOrderEntry(id=Key.MinP, enabled=True),
                KeyOrderEntry(id=Key.Temperature, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Cfg, enabled=False)
            ]
        ),
        description=(
            "Higher variety of word choice, more differences between rerolls, "
            "more prone to mistakes."
        )
    )
)
Erato.register_preset(
    TextLLMModel.ERATO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Zany Scribe",
        id="default-erato-zanyscribe",
        parameters=LLMGenerationParams(
            temperature=1,
            top_k=0,
            top_p=0.98,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.99,
            repetition_penalty=1,
            repetition_penalty_range=3024,
            repetition_penalty_slope=1.1,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0.25,
            repetition_penalty_default_whitelist=True,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Default,
            top_g=0,
            mirostat_tau=1,
            mirostat_lr=1,
            math1_temp=-0.275,
            math1_quad=0.35,
            math1_quad_entropy_scale=-0.2,
            min_p=0.08,
            order=[
                KeyOrderEntry(id=Key.Temperature, enabled=False),
                KeyOrderEntry(id=Key.MinP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=True),
                KeyOrderEntry(id=Key.Mirostat, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False)
            ]
        ),
        description="Avoids mistakes and repetition. Prioritizes more complex words."
    )
)
Erato.register_preset(
    TextLLMModel.ERATO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="Dragonfruit",
        id="default-erato-dragonfruit",
        parameters=LLMGenerationParams(
            temperature=1.37,
            top_k=0,
            top_p=1,
            top_a=0.1,
            typical_p=0.875,
            tail_free_sampling=0.87,
            repetition_penalty=3.25,
            repetition_penalty_range=6000,
            repetition_penalty_slope=3.25,
            repetition_penalty_frequency=0,
            repetition_penalty_presence=0,
            repetition_penalty_default_whitelist=False,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Off,
            top_g=0,
            mirostat_tau=4,
            mirostat_lr=0.2,
            math1_temp=0.9,
            math1_quad=0.07,
            math1_quad_entropy_scale=-0.05,
            min_p=0.035,
            order=[
                KeyOrderEntry(id=Key.Temperature, enabled=True),
                KeyOrderEntry(id=Key.TypicalP, enabled=True),
                KeyOrderEntry(id=Key.Math1, enabled=True),
                KeyOrderEntry(id=Key.MinP, enabled=True),
                KeyOrderEntry(id=Key.Mirostat, enabled=True),
                KeyOrderEntry(id=Key.TopA, enabled=True),
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False)
            ]
        ),
        description="Varied and complex language with little repetition. More frequent mistakes and contradictions."
    )
)
Erato.register_preset(
    TextLLMModel.ERATO,
    Preset(
        presetVersion=3,
        remoteId="",
        name="小説家",
        id="default-erato-shousetsuka",
        parameters=LLMGenerationParams(
            temperature=1,
            max_length=60,
            min_length=1,
            top_k=50,
            top_p=0.85,
            top_a=1,
            typical_p=1,
            tail_free_sampling=0.895,
            repetition_penalty=1.63,
            repetition_penalty_range=1024,
            repetition_penalty_slope=3.33,
            repetition_penalty_frequency=0.0035,
            repetition_penalty_presence=0,
            repetition_penalty_default_whitelist=False,
            cfg_scale=1,
            cfg_uc="",
            phrase_rep_pen=PenStyle.Default,
            top_g=0,
            mirostat_tau=0,
            mirostat_lr=1,
            math1_temp=0.3,
            math1_quad=0.0645,
            math1_quad_entropy_scale=0.05,
            min_p=0.05,
            order=[
                KeyOrderEntry(id=Key.Cfg, enabled=False),
                KeyOrderEntry(id=Key.Temperature, enabled=False),
                KeyOrderEntry(id=Key.Math1, enabled=True),
                KeyOrderEntry(id=Key.MinP, enabled=True),
                KeyOrderEntry(id=Key.TopP, enabled=False),
                KeyOrderEntry(id=Key.TopA, enabled=False),
                KeyOrderEntry(id=Key.TopK, enabled=False),
                KeyOrderEntry(id=Key.TFS, enabled=False),
                KeyOrderEntry(id=Key.TypicalP, enabled=False),
                KeyOrderEntry(id=Key.TopG, enabled=False),
                KeyOrderEntry(id=Key.Mirostat, enabled=False)
            ]
        ),
        description="Designed for writing in Japanese. Works fine for English too."
    )
)

PresetMapping = {
    TextLLMModel.J_6B_V4: J6bv4,
    TextLLMModel.NEO_2B: Neo2b,
    TextLLMModel.GENJI_PYTHON_6B: Genjipython6b,
    TextLLMModel.GENJI_JP_6B_V2: Genjijp6bv2,
    TextLLMModel.EUTERPE_V2: Euterpev2,
    TextLLMModel.KRAKE_V1: Krakev1,
    TextLLMModel.KRAKE_V2: Krakev2,
    TextLLMModel.BLUE: Colorful,
    TextLLMModel.RED: Colorful,
    TextLLMModel.GREEN: Colorful,
    TextLLMModel.PURPLE: Colorful,
    TextLLMModel.PINK: Colorful,
    TextLLMModel.YELLOW: Colorful,
    TextLLMModel.WHITE: Colorful,
    TextLLMModel.BLACK: Colorful,
    TextLLMModel.CLIO: Clio,
    TextLLMModel.KAYRA: Kayra,
    TextLLMModel.ERATO: Erato,
}
