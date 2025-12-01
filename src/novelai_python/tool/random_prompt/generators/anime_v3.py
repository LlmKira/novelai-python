import random
from ..logic import TagSelector, apply_curly_brackets, js_random_int
from .holiday import inject_holiday_spirit
from ..data.anime_v3_data import * 
from ..data.nsfw_data import NSFW_NW

def t_generate_character(gender_char, framing, is_no_humans, char_count, selector: TagSelector):
    # ... (код этой функции такой же, как был, он верный) ...
    tags = []
    if random.random() < 0.1: tags.append(selector.weighted_choice(SPECIES, simple=True))
    is_monster = any(t in ["mermaid", "centaur", "lamia"] for t in tags)
    if random.random() < 0.4: tags.append(selector.weighted_choice(SKIN, simple=True))
    if random.random() < 0.8: tags.append(selector.weighted_choice(EYE_COLORS, simple=True))
    if random.random() < 0.1: tags.append(selector.weighted_choice(EYES_SPECIAL, simple=True))
    if random.random() < 0.2: tags.append(selector.weighted_choice(EYES_EXPRESSION, simple=True))
    if random.random() < 0.8: tags.append(selector.weighted_choice(HAIR_LENGTH, simple=True))
    if random.random() < 0.5: tags.append(selector.weighted_choice(HAIR_STYLE, simple=True))
    if random.random() < 0.7: tags.append(selector.weighted_choice(HAIR_COLORS, simple=True))
    if random.random() < 0.1: 
        tags.append(selector.weighted_choice(HAIR_COLORS_SPECIAL, simple=True))
        tags.append(selector.weighted_choice(HAIR_COLORS, simple=True))
    if random.random() < 0.1: tags.append(selector.weighted_choice(HAIR_TYPE, simple=True))
    if random.random() < 0.2: tags.append(selector.weighted_choice(HAIR_BANGS, simple=True))
    if gender_char.startswith("f") and random.random() < 0.5: tags.append(selector.weighted_choice(CHEST, simple=True))
    n_body = 0
    if char_count == 1: n_body = selector.pick_count([[0, 10], [1, 30], [2, 15], [3, 5]])
    elif char_count == 2: n_body = selector.pick_count([[0, 20], [1, 40], [2, 10]])
    else: n_body = selector.pick_count([[0, 30], [1, 30]])
    for _ in range(n_body): tags.append(selector.weighted_choice(BODY_FEATURES, simple=True))
    if random.random() < 0.2:
        tags.append(selector.weighted_choice(HATS, simple=True))
        if random.random() < 0.2: tags.append(selector.weighted_choice(HAT_EXTRAS, simple=True))
    elif random.random() < 0.3: tags.append(selector.weighted_choice(HEAD_ACCESSORIES, simple=True))
    outfit_type = selector.weighted_choice([["uniform", 10], ["swimsuit", 5], ["bodysuit", 5], ["normal clothes", 40]], simple=True)
    if outfit_type == "uniform": tags.append(selector.weighted_choice(UNIFORMS, simple=True))
    elif outfit_type == "swimsuit": tags.append(selector.weighted_choice(SWIMSUITS, simple=True))
    elif outfit_type == "bodysuit": tags.append(selector.weighted_choice(BODYSUITS, simple=True))
    elif outfit_type == "normal clothes":
        if gender_char.startswith("f") and random.random() < 0.5:
            tags.append(selector.weighted_choice(SOCKS, simple=True))
            if random.random() < 0.2: tags.append(selector.weighted_choice(SOCKS_EXTRAS, simple=True))
        if gender_char.startswith("f") and random.random() < 0.2:
            is_colored = random.random() < 0.5
            color = selector.weighted_choice(COLORS, simple=True)
            dress = selector.weighted_choice(DRESSES, simple=True)
            tags.append(f"{color} {dress}" if is_colored else dress)
        else:
            if random.random() < 0.85: 
                is_colored = random.random() < 0.5
                color = selector.weighted_choice(COLORS, simple=True)
                top = selector.weighted_choice(TOPS, simple=True)
                tags.append(f"{color} {top}" if is_colored else top)
            if not is_monster:
                if random.random() < 0.85 and framing != "portrait": 
                    is_colored = random.random() < 0.5
                    color = selector.weighted_choice(COLORS, simple=True)
                    bottom = selector.weighted_choice(BOTTOMS, simple=True)
                    tags.append(f"{color} {bottom}" if is_colored else bottom)
                if random.random() < 0.6 and (framing == "full body" or framing is None): 
                    is_colored = random.random() < 0.5
                    color = selector.weighted_choice(COLORS, simple=True)
                    shoes = selector.weighted_choice(SHOES, simple=True)
                    tags.append(f"{color} {shoes}" if is_colored else shoes)
    if random.random() < 0.6: tags.append(selector.weighted_choice(EXPRESSIONS, simple=True))
    chance = 1.0 if (is_no_humans and char_count == 1) else 0.4
    if random.random() < chance: tags.append(selector.weighted_choice(POSES, simple=True))
    o_acc = 0
    if char_count == 1: o_acc = selector.pick_count([[0, 10], [1, 30], [2, 15], [3, 5]])
    elif char_count == 2: o_acc = selector.pick_count([[0, 20], [1, 40], [2, 10]])
    else: o_acc = selector.pick_count([[0, 30], [1, 30]])
    for _ in range(o_acc): tags.append(selector.weighted_choice(ACCESSORIES, simple=True))
    if is_monster: tags = [t for t in tags if "legwear" not in t]
    return tags

def generate_anime_v3_prompt(use_holiday=True, is_nsfw=False):
    selector = TagSelector()
    tags = []
    if is_nsfw: tags.append(NSFW_NW)
    
    char_count = selector.pick_count([[1, 70], [2, 20], [3, 7], [0, 5]])
    
    # No humans branch
    if char_count == 0:
        tags.append("no humans")
        if random.random() < 0.3: tags.append(selector.weighted_choice(STYLES, simple=True))
        tags.append(selector.weighted_choice(SCENERY_TYPES, simple=True))
        count_scenery = selector.pick_count([[2, 15], [3, 50], [4, 15], [5, 5]])
        for _ in range(count_scenery): tags.append(selector.weighted_choice(SCENERY_DETAILS, simple=True))
        count_obj = selector.pick_count([[0, 15], [1, 10], [2, 20], [3, 20], [4, 20], [5, 15]])
        for _ in range(count_obj): tags.append(selector.weighted_choice(OBJECTS, simple=True))
        
        prompt = ", ".join([t for t in tags if t])
        if use_holiday: prompt = inject_holiday_spirit(prompt)
        return prompt

    # Humans branch
    if random.random() < 0.3: tags.append(selector.weighted_choice(STYLES, simple=True))
    m_cnt, f_cnt, o_cnt = 0, 0, 0
    # Ghost call fix
    for _ in range(char_count):
        _ = selector.weighted_choice([["m", 30], ["f", 50], ["o", 10]], simple=True)
        g = selector.weighted_choice([["m", 30], ["f", 50]], simple=True)
        if g == "m": m_cnt += 1
        elif g == "f": f_cnt += 1
    if f_cnt == 1: tags.insert(0, "1girl")
    elif f_cnt == 2: tags.insert(0, "2girls")
    elif f_cnt == 3: tags.insert(0, "3girls")
    if m_cnt == 1: tags.insert(0, "1boy")
    elif m_cnt == 2: tags.insert(0, "2boys")
    elif m_cnt == 3: tags.insert(0, "3boys")
    if o_cnt == 1: tags.insert(0, "1other")
    elif o_cnt == 2: tags.insert(0, "2others")
    elif o_cnt == 3: tags.insert(0, "3others")
    
    if random.random() < 0.8:
        bg = selector.weighted_choice(BACKGROUNDS, simple=True)
        tags.append(bg)
        if bg == "scenery" and random.random() < 0.5:
            c = js_random_int(1, 3)
            for _ in range(c): tags.append(selector.weighted_choice(SCENERY_DETAILS, simple=True))
    if random.random() < 0.3: tags.append(selector.weighted_choice(ANGLES, simple=True))
    framing = None
    if random.random() < 0.7:
        framing = selector.weighted_choice(FRAMING, simple=True)
        if framing: tags.append(framing)
    for _ in range(f_cnt): tags.extend(t_generate_character("f", framing, False, char_count, selector))
    for _ in range(m_cnt): tags.extend(t_generate_character("m", framing, False, char_count, selector))
    for _ in range(o_cnt): tags.extend(t_generate_character("o", framing, False, char_count, selector))
    if random.random() < 0.2:
        c_obj = js_random_int(0, 3) if char_count == 2 else js_random_int(0, 4)
        for _ in range(c_obj): tags.append(selector.weighted_choice(OBJECTS, simple=True))
    if random.random() < 0.25:
        c_eff = js_random_int(1, 3)
        for _ in range(c_eff): tags.append(selector.weighted_choice(EFFECTS, simple=True))
    if random.random() < 0.2: tags.append(selector.weighted_choice(YEARS, simple=True))
    if random.random() < 0.1: tags.append(selector.weighted_choice(FOCUS, simple=True))

    unique_tags = list(dict.fromkeys([t for t in tags if t]))
    final_tags = [apply_curly_brackets(t) for t in unique_tags]
    
    prompt = ", ".join(final_tags)
    if use_holiday:
        prompt = inject_holiday_spirit(prompt)
        
    return prompt