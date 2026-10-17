import random

from ..data.anime_v4_data import (
    ACCESSORIES_V4,
    ANGLES_V4,
    BACKGROUNDS_V4,
    BODY_FEATURES_V4,
    BODYSUITS_V4,
    BOTTOMS_V4,
    CHEST_V4,
    COLORS_V4,
    DRESSES_V4,
    EFFECTS_V4,
    EXPRESSIONS_V4,
    EYE_COLORS_V4,
    EYES_EXPR_V4,
    EYES_V4,
    FOCUS_V4,
    FRAMING_V4,
    HAIR_BANGS_V4,
    HAIR_COLORS_SPECIAL_V4,
    HAIR_COLORS_V4,
    HAIR_LENGTH_V4,
    HAIR_STYLE_V4,
    HAIR_TYPE_V4,
    HAT_EXTRAS_V4,
    HATS_V4,
    HEAD_ACCESSORIES_V4,
    OBJECTS_V4,
    POSES_V4,
    SCENERY_DETAILS_V4,
    SCENERY_TYPES_V4,
    SHOES_V4,
    SKIN_V4,
    SOCKS_EXTRAS_V4,
    SOCKS_V4,
    SPECIES_V4,
    STYLES_V4,
    SWIMSUITS_V4,
    TOPS_V4,
    UNIFORMS_V4,
    YEARS_V4,
)
from ..data.nsfw_data import NSFW_NW
from ..logic import TagSelector, js_random_int
from .holiday import inject_holiday_spirit


def ae_generate_character_details(gender_char, framing, char_count, selector: TagSelector):
    tags = []
    if random.random() < 0.1:
        tags.append(selector.weighted_choice(SPECIES_V4))
    if random.random() < 0.4:
        tags.append(selector.weighted_choice(SKIN_V4))
    if random.random() < 0.05:
        tags.append(selector.weighted_choice(EYES_V4))
    if "no eyes" not in selector.selected_tags:
        if random.random() < 0.2:
            tags.append(selector.weighted_choice(EYES_EXPR_V4))
        if random.random() < 0.8 and "nocoloreyes" not in selector.selected_tags:
            tags.append(selector.weighted_choice(EYE_COLORS_V4))
    if random.random() < 0.8:
        tags.append(selector.weighted_choice(HAIR_LENGTH_V4))
    if random.random() < 0.7:
        tags.append(selector.weighted_choice(HAIR_STYLE_V4))
    if random.random() < 0.7:
        tags.append(selector.weighted_choice(HAIR_COLORS_V4))
    if random.random() < 0.1:
        tags.append(selector.weighted_choice(HAIR_COLORS_SPECIAL_V4))
        tags.append(selector.weighted_choice(HAIR_COLORS_V4))
    if random.random() < 0.3:
        tags.append(selector.weighted_choice(HAIR_TYPE_V4))
    if random.random() < 0.4:
        tags.append(selector.weighted_choice(HAIR_BANGS_V4))
    if gender_char.startswith("f") and random.random() < 0.8:
        tags.append(selector.weighted_choice(CHEST_V4))
    n_body = 0
    if char_count == 1:
        n_body = selector.pick_count([[0, 10], [1, 30], [2, 15], [3, 5]])
    elif char_count == 2:
        n_body = selector.pick_count([[0, 20], [1, 40], [2, 10]])
    else:
        n_body = selector.pick_count([[0, 30], [1, 30]])
    for _ in range(n_body):
        tags.append(selector.weighted_choice(BODY_FEATURES_V4))
    if random.random() < 0.2:
        tags.append(selector.weighted_choice(HATS_V4))
        if random.random() < 0.2:
            tags.append(selector.weighted_choice(HAT_EXTRAS_V4))
    elif random.random() < 0.3:
        tags.append(selector.weighted_choice(HEAD_ACCESSORIES_V4))
    outfit_type = selector.weighted_choice([["uniform", 25], ["swimsuit", 5], ["bodysuit", 5], ["normal clothes", 40]])
    if outfit_type == "uniform":
        tags.append(selector.weighted_choice(UNIFORMS_V4))
    elif outfit_type == "swimsuit":
        tags.append(selector.weighted_choice(SWIMSUITS_V4))
    elif outfit_type == "bodysuit":
        tags.append(selector.weighted_choice(BODYSUITS_V4))
    elif outfit_type == "normal clothes":
        if gender_char.startswith("f") and random.random() < 0.5:
            tags.append(selector.weighted_choice(SOCKS_V4))
            if random.random() < 0.2:
                tags.append(selector.weighted_choice(SOCKS_EXTRAS_V4))
        if gender_char.startswith("f") and random.random() < 0.2:
            is_col = random.random() < 0.5
            col = selector.weighted_choice(COLORS_V4)
            dress = selector.weighted_choice(DRESSES_V4)
            if dress:
                tags.append(f"{col} {dress}" if is_col else dress)
        else:
            if random.random() < 0.85:
                is_col = random.random() < 0.5
                col = selector.weighted_choice(COLORS_V4)
                top = selector.weighted_choice(TOPS_V4)
                if top:
                    tags.append(f"{col} {top}" if is_col else top)
            if "legs" in selector.selected_tags:
                if random.random() < 0.85:
                    is_col = random.random() < 0.5
                    col = selector.weighted_choice(COLORS_V4)
                    btm = selector.weighted_choice(BOTTOMS_V4)
                    if btm:
                        tags.append(f"{col} {btm}" if is_col else btm)
                if "feet" in selector.selected_tags and random.random() < 0.6:
                    is_col = random.random() < 0.5
                    col = selector.weighted_choice(COLORS_V4)
                    shoe = selector.weighted_choice(SHOES_V4)
                    if shoe:
                        tags.append(f"{col} {shoe}" if is_col else shoe)
    if random.random() < 0.6:
        tags.append(selector.weighted_choice(EXPRESSIONS_V4))
    if random.random() < 0.4:
        tags.append(selector.weighted_choice(POSES_V4))
    acc_c = 0
    if char_count == 1:
        acc_c = selector.pick_count([[0, 10], [1, 30], [2, 15], [3, 5]])
    elif char_count == 2:
        acc_c = selector.pick_count([[0, 20], [1, 40], [2, 10]])
    else:
        acc_c = selector.pick_count([[0, 30], [1, 30]])
    for _ in range(acc_c):
        tags.append(selector.weighted_choice(ACCESSORIES_V4))
    return [t for t in tags if t]


def generate_anime_v4_prompt(use_holiday=True, is_nsfw=False):
    selector = TagSelector()
    tags = []
    if is_nsfw:
        tags.append(NSFW_NW)
    char_count = selector.pick_count([[1, 70], [2, 20], [3, 7], [0, 5]])

    if char_count == 0:
        tags.append("no humans")
        if random.random() < 0.5:
            tags.append(selector.weighted_choice(STYLES_V4))
        tags.append(selector.weighted_choice(SCENERY_TYPES_V4))
        scen_c = selector.pick_count([[2, 15], [3, 50], [4, 15], [5, 5]])
        for _ in range(scen_c):
            tags.append(selector.weighted_choice(SCENERY_DETAILS_V4))
        obj_c = selector.pick_count([[0, 15], [1, 10], [2, 20], [3, 20], [4, 20], [5, 15]])
        obj_c = max(0, obj_c - char_count)
        for _ in range(obj_c):
            tags.append(selector.weighted_choice(OBJECTS_V4))

        prompt = ", ".join([t for t in tags if t])
        if use_holiday:
            prompt = inject_holiday_spirit(prompt)
        return prompt

    if random.random() < 0.5:
        tags.append(selector.weighted_choice(STYLES_V4))
    m_cnt, f_cnt, o_cnt = 0, 0, 0
    for _ in range(char_count):
        g = selector.weighted_choice([["m", 30], ["f", 60], ["o", 0]])
        if g == "m":
            m_cnt += 1
        elif g == "f":
            f_cnt += 1
        else:
            o_cnt += 1
    if f_cnt == 1:
        tags.insert(0, "1girl")
    elif f_cnt == 2:
        tags.insert(0, "2girls")
    elif f_cnt == 3:
        tags.insert(0, "3girls")
    if m_cnt == 1:
        tags.insert(0, "1boy")
    elif m_cnt == 2:
        tags.insert(0, "2boys")
    elif m_cnt == 3:
        tags.insert(0, "3boys")
    if o_cnt == 1:
        tags.insert(0, "1other")
    elif o_cnt == 2:
        tags.insert(0, "2others")
    elif o_cnt == 3:
        tags.insert(0, "3others")

    if random.random() < 0.8:
        bg = selector.weighted_choice(BACKGROUNDS_V4)
        tags.append(bg)
        if bg == "scenery" and random.random() < 0.5:
            # Fixed: 1 to 3
            c = js_random_int(1, 3)
            for _ in range(c):
                tags.append(selector.weighted_choice(SCENERY_DETAILS_V4))
    if random.random() < 0.3:
        tags.append(selector.weighted_choice(ANGLES_V4))
    framing = None
    if random.random() < 0.7:
        framing = selector.weighted_choice(FRAMING_V4)
        if framing:
            tags.append(framing)
    sub_tags = []
    for _ in range(f_cnt):
        sub_tags.append("girl")
        sub_tags.extend(ae_generate_character_details("f", framing, char_count, selector))
    for _ in range(m_cnt):
        sub_tags.append("boy")
        sub_tags.extend(ae_generate_character_details("m", framing, char_count, selector))
    for _ in range(o_cnt):
        sub_tags.append("other")
        sub_tags.extend(ae_generate_character_details("o", framing, char_count, selector))
    tags.extend(sub_tags)
    if random.random() < 0.2:
        # Fixed 0 to 3/4
        c = js_random_int(0, 3) if char_count == 2 else js_random_int(0, 4)
        for _ in range(c):
            tags.append(selector.weighted_choice(OBJECTS_V4))
    if random.random() < 0.25:
        # Fixed 1 to 3
        c = js_random_int(1, 3)
        for _ in range(c):
            tags.append(selector.weighted_choice(EFFECTS_V4))
    if random.random() < 0.2:
        tags.append(selector.weighted_choice(YEARS_V4))
    if random.random() < 0.1:
        tags.append(selector.weighted_choice(FOCUS_V4))

    unique = list(dict.fromkeys([t for t in tags if t]))
    prompt = ", ".join(unique)
    if use_holiday:
        prompt = inject_holiday_spirit(prompt)
    return prompt
