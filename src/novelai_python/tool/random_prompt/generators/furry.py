import random
from ..logic import TagSelector, apply_curly_brackets, js_random_int
from .holiday import inject_holiday_spirit

# Импорт NSFW данных
from ..data.nsfw_data import (
    NSFW_N, NSFW_U, NSFW_NK, NSFW_P, NSFW_MP, NSFW_FU, NSFW_YU, NSFW_YA,
    NSFW_FWM, NSFW_FWF, NSFW_NW, NSFW_NPM, NSFW_NPP, NSFW_NPA, NSFW_NSM,
    NSFW_NSA, NSFW_NSP, NSFW_NEX, NSFW_SMOD, NSFW_SACTMOD, NSFW_BD, NSFW_ST
)

# Импорт ВСЕХ Furry данных (a...)
from ..data.furry_data import *

# Особые виды и одежда
SPECIAL_SPECIES = {"taur", "serpentine", "naga", "centaur", "feral", "merfolk", "lamia"}
CLOTHES_REQUIRE_LEGS = {
    "over-kneehighs", "thighhighs", "leggings", "leg warmers", 
    "fishnet legwear", "bow legwear", "ribbed legwear", "seamed legwear", 
    "see-through legwear", "shiny legwear", "fur-trimmed legwear", 
    "lace-trimmed legwear", "uneven legwear", "mismatched legwear",
    "bare legs", "bandaged leg", "ass visible through thighs",
    "jacket around waist", "fanny pack", "garter straps", "knee pads",
    "mechanical legs", "prosthetic leg"
}

def aZ_generate_character_furry(gender_char, framing, char_count, selector: TagSelector, is_nsfw=False):
    """Портирование функции aZ() из JS"""
    tags = []
    flags = set()
    
    # Вид
    species_cat = selector.weighted_choice([["core", 50], ["humanoid", 20], ["other", 5]])
    
    if species_cat == "core":
        tags.append(selector.weighted_choice(SPECIES_FURRY))
        if random.random() < 0.8:
            tags.append(selector.weighted_choice(SPECIES_TYPE_FURRY))
    elif species_cat == "humanoid":
        tags.append("humanoid")
        tags.append(selector.weighted_choice(SPECIES_HUMANOID_FURRY))
        flags.add("not_furry")
    elif species_cat == "other":
        tags.append(selector.weighted_choice(SPECIES_OTHER_FURRY))
        
    # Кожа
    if random.random() < 0.7:
        tags.append(selector.weighted_choice(SKIN_FURRY))
    
    if random.random() < 0.7:
        mtype = selector.weighted_choice([["multicolored body", 50], ["two tone body", 30], ["rainbow body", 2]])
        if mtype == "multicolored body" or (mtype == "two tone body" and random.random() < 0.5):
             tags.append(selector.weighted_choice(SKIN_FURRY))
        tags.append(mtype)
        
    # Глаза
    if random.random() < 0.7:
        tags.append(selector.weighted_choice(EYE_COLOR_FURRY))
    if random.random() < 0.05:
        tags.append(selector.weighted_choice(EYE_SCLERA_FURRY))
    if random.random() < 0.1:
        tags.append(selector.weighted_choice(EYE_TYPE_FURRY))
        
    # Волосы
    has_hair = random.random() < (0.7 if "not_furry" in flags else 0.2)
    if has_hair:
        tags.append(selector.weighted_choice(HAIR_LENGTH_FURRY))
    
    if random.random() < (0.5 if "not_furry" in flags else 0.1):
        tags.append(selector.weighted_choice(HAIR_STYLE_FURRY))
        
    if random.random() < (0.7 if "not_furry" in flags else 0.1):
        tags.append(selector.weighted_choice(HAIR_COLOR_FURRY))
        if random.random() < 0.1:
             if random.random() < 0.5:
                 tags.append(selector.weighted_choice(HAIR_COLOR_FURRY))
             tags.append(selector.weighted_choice(HAIR_COLOR_SPECIAL_FURRY))
             
    if random.random() < (0.1 if "not_furry" in flags else 0.05):
        tags.append(selector.weighted_choice(HAIR_TYPE_FURRY))
        
    if random.random() < (0.1 if "not_furry" in flags else 0.05):
        tags.append(selector.weighted_choice(HAIR_BANGS_FURRY))
        
    # Грудь
    if gender_char.startswith("f") and random.random() < (0.5 if "feral" not in tags else 0.0):
         tags.append(selector.weighted_choice(CHEST_FURRY))
         
    # Тело
    n_body = 0
    if char_count == 1: n_body = selector.pick_count([[0, 10], [1, 30], [2, 15], [3, 5]])
    elif char_count == 2: n_body = selector.pick_count([[0, 20], [1, 40], [2, 10]])
    else: n_body = selector.pick_count([[0, 30], [1, 30]])
    
    for _ in range(n_body):
        tags.append(selector.weighted_choice(BODY_FEATURES_FURRY))
        
    # Голова
    if random.random() < 0.15:
        tags.append(selector.weighted_choice(HATS_FURRY))
    elif random.random() < 0.2:
        tags.append(selector.weighted_choice(HEAD_ACCESSORIES_FURRY))
        
    # Одежда
    outfit_pool = [["uniform", 10], ["swimsuit", 5], ["bodysuit", 5], ["normal clothes", 40]]
    outfit = selector.weighted_choice(outfit_pool)
    
    # Feral stripping logic
    if "feral" in tags:
        if not (random.random() < 0.6): outfit = None
    elif random.random() < 0.2: # Anthro naked chance
        outfit = None
        
    # Furgonomics (from JS)
    if outfit and random.random() < 0.3:
        tags.append("furgonomics")

    # NSFW Stripping logic
    if is_nsfw and random.random() < 0.9:
        nsfw_choice = selector.weighted_choice([["n", 15], ["u", 10], ["nk", 5]])
        if nsfw_choice == "n":
            tags.append(selector.weighted_choice(NSFW_N))
        elif nsfw_choice == "u":
             tags.append(selector.weighted_choice(NSFW_U))
             if random.random() < 0.5: outfit = None
        elif nsfw_choice == "nk":
             tags.append(selector.weighted_choice(NSFW_NK))
             outfit = None

    # NSFW Genitals / Body parts
    if is_nsfw and framing not in ("portrait", "upper body"):
        if gender_char == "f" and random.random() < 0.8:
            tags.append(selector.weighted_choice(NSFW_P))
        elif gender_char == "m" and random.random() < 0.8:
            tags.append(selector.weighted_choice(NSFW_MP))
        elif gender_char == "fu":
            tags.append(selector.weighted_choice(NSFW_MP))
            if random.random() < 0.5:
                tags.append(selector.weighted_choice(NSFW_P))
             
    if outfit == "uniform":
        tags.append(selector.weighted_choice(UNIFORMS_FURRY))
    elif outfit == "swimsuit":
        tags.append(selector.weighted_choice(SWIMSUITS_FURRY))
    elif outfit == "bodysuit":
        tags.append(selector.weighted_choice(BODYSUITS_FURRY))
    elif outfit == "normal clothes":
        if gender_char.startswith("f") and random.random() < 0.2:
             col = selector.weighted_choice(COLORS_FURRY)
             dress = selector.weighted_choice(DRESSES_FURRY)
             if dress: tags.append(f"{col} {dress}" if random.random() < 0.5 else dress)
        else:
            if random.random() < 0.9:
                col = selector.weighted_choice(COLORS_FURRY)
                top = selector.weighted_choice(TOPS_FURRY)
                if top: tags.append(f"{col} {top}" if random.random() < 0.5 else top)
            
            # Requires legs check
            # В JS это делается через фильтр CLOTHES_REQUIRE_LEGS в конце, 
            # но тут мы не добавляем, если спец. вид, упрощая.
            is_special = any(x in SPECIAL_SPECIES for x in tags)
            
            if not is_special:
                if random.random() < 0.7:
                    col = selector.weighted_choice(COLORS_FURRY)
                    btm = selector.weighted_choice(BOTTOMS_FURRY)
                    if btm: tags.append(f"{col} {btm}" if random.random() < 0.5 else btm)
                
                if random.random() < 0.5:
                    col = selector.weighted_choice(COLORS_FURRY)
                    sock = selector.weighted_choice(SOCKS_FURRY)
                    if sock: tags.append(f"{col} {sock}" if random.random() < 0.5 else sock)
                    
                # Shoes only if full body/none
                # В JS: if (s.has("feet") && .6 > Math.random())
                # Упрощаем: если не портрет и не upper body
                if framing not in ["portrait", "upper body"] and random.random() < 0.6:
                     col = selector.weighted_choice(COLORS_FURRY)
                     shoe = selector.weighted_choice(SHOES_FURRY)
                     if shoe: tags.append(f"{col} {shoe}" if random.random() < 0.5 else shoe)

    # Выражения
    if random.random() < 0.6:
        tags.append(selector.weighted_choice(EXPRESSIONS_FURRY))
        
    # Позы
    chance = 1.0 if (is_nsfw and char_count == 1) else 0.4
    if random.random() < chance:
        poses = POSES_FURRY[:]
        if is_nsfw:
            poses.extend(NSFW_NSM + NSFW_NSA + NSFW_NSP)
        tags.append(selector.weighted_choice(poses))
        
    # Аксессуары
    n_acc = 0
    if char_count == 1: n_acc = selector.pick_count([[0, 20], [1, 20], [2, 10], [3, 2]])
    elif char_count == 2: n_acc = selector.pick_count([[0, 30], [1, 30], [2, 5]])
    else: n_acc = selector.pick_count([[0, 30], [1, 15]])
    
    for _ in range(n_acc):
        acc_list = ACCESSORIES_FURRY[:]
        if is_nsfw: acc_list.extend(NSFW_NEX)
        tags.append(selector.weighted_choice(acc_list))

    # Очистка несовместимой одежды для монстров
    if any(x in SPECIAL_SPECIES for x in tags):
        tags = [t for t in tags if t not in CLOTHES_REQUIRE_LEGS]
        
    return [t for t in tags if t], list(flags)


def generate_furry_prompt(use_holiday=True, is_nsfw=False):
    """Реализация a$()"""
    selector = TagSelector()
    tags = []
    
    # 1. Count
    cnt_opts = [[1, 80], [2, 15], [3, 5], [0, 5]]
    if is_nsfw: cnt_opts = [[1, 35], [2, 20], [3, 7]]
    char_count = selector.pick_count(cnt_opts)
    
    # --- No Humans ---
    if char_count == 0:
        tags.append("zero pictured")
        if random.random() < 0.3:
             tags.append(selector.weighted_choice(STYLES_FURRY))
        tags.append(selector.weighted_choice(SCENERY_TYPES_FURRY))
        
        n_scen = selector.pick_count([[2, 15], [3, 50], [4, 15], [5, 5]])
        for _ in range(n_scen):
             tags.append(selector.weighted_choice([["inside", 50], ["outside", 50]]))
             tags.append(selector.weighted_choice(SCENERY_DETAILS_FURRY))
             
        n_obj = selector.pick_count([[0, 15], [1, 20], [2, 15], [3, 15], [4, 10], [5, 5]])
        # clamp
        n_obj = max(0, n_obj - char_count)
        for _ in range(n_obj):
             tags.append(selector.weighted_choice(OBJECTS_FURRY))
             
        return ", ".join([t for t in tags if t])
        
    # --- Humans / Anthros Loop ---
    # ВАЖНО: В Furry (a$) сначала выбирается пол, потом теги кол-ва, потом СТИЛЬ.
    
    m_cnt, f_cnt, o_cnt = 0, 0, 0
    for _ in range(char_count):
        g = selector.weighted_choice([["m", 45], ["f", 45], ["o", 10]])
        if g == "m": m_cnt += 1
        elif g == "f": f_cnt += 1
        else: o_cnt += 1
    
    # Prefixes
    if char_count == 1: tags.append("solo")
    elif char_count == 2: tags.append("duo")
    elif char_count == 3: tags.append("trio")
    
    # Style Check (Moved AFTER gender loop to match JS execution order)
    if random.random() < 0.3:
        tags.append(selector.weighted_choice(STYLES_FURRY))

    if f_cnt > 0: tags.append("female")
    if m_cnt > 0: tags.append("male")
    if o_cnt > 0: tags.append("ambiguous gender")
    
    # NSFW Logic
    if is_nsfw:
        tags.insert(0, NSFW_NW)
        has_futa = False
        if m_cnt >= 2 and f_cnt == 0:
            if random.random() < 0.7: tags.append(NSFW_YU)
            else: tags.append(NSFW_FU); has_futa = True
        if f_cnt >= 2 and m_cnt == 0: tags.append(NSFW_YA)
        if m_cnt > 0 and f_cnt > 0 and random.random() < 0.2: tags.append(NSFW_FU)
            
        if char_count >= 2:
            potential_nsfw = NSFW_NPM[:]
            if (m_cnt > 0 and f_cnt > 0) or has_futa: potential_nsfw.extend(NSFW_NPP)
            if f_cnt > 0 or has_futa: potential_nsfw.extend(NSFW_NPA)
            if has_futa: tags.append(NSFW_FWF)
            if (m_cnt > 0 and f_cnt > 0 and random.random() < 0.2): tags.append(NSFW_FWM)
            if potential_nsfw: tags.append(selector.weighted_choice(potential_nsfw))
            if random.random() < 0.6: tags.append(selector.weighted_choice(NSFW_SMOD))
            
        if random.random() < 0.4: tags.append(selector.weighted_choice(NSFW_SACTMOD))
        if random.random() < 0.05: tags.append(selector.weighted_choice(NSFW_BD))
        if random.random() < 0.05: tags.append(selector.weighted_choice(NSFW_ST))

    # Background
    if random.random() < 0.9:
        bg = selector.weighted_choice(BACKGROUNDS_FURRY)
        tags.append(bg)
        if bg in ["detailed background", "amazing background"]:
            n_scen = selector.pick_count([[1, 50], [2, 20]])
            tags.append(selector.weighted_choice([["inside", 50], ["outside", 50]]))
            for _ in range(n_scen): tags.append(selector.weighted_choice(SCENERY_DETAILS_FURRY))
                
    # Angles
    if random.random() < 0.3:
        tags.append(selector.weighted_choice(ANGLES_FURRY))
        
    # Framing
    framing = None
    if random.random() < 0.7:
        framing = selector.weighted_choice(FRAMING_FURRY)
        if framing: tags.append(framing)
        
    # Characters Details
    is_all_furry = True
    sub_tags = []
    
    for _ in range(f_cnt):
        t_list, flags = aZ_generate_character_furry("f", framing, char_count, selector, is_nsfw)
        if "not_furry" in flags: is_all_furry = False
        sub_tags.extend(t_list)
    for _ in range(m_cnt):
        # Futa chance for solo male in NSFW
        include_futa = is_nsfw and m_cnt == 1 and char_count == 1 and random.random() < 0.2
        if include_futa: tags.append(NSFW_FU)
        gender_key = "fu" if include_futa else "m"
        t_list, flags = aZ_generate_character_furry(gender_key, framing, char_count, selector, is_nsfw)
        if "not_furry" in flags: is_all_furry = False
        sub_tags.extend(t_list)
    for _ in range(o_cnt):
        t_list, flags = aZ_generate_character_furry("o", framing, char_count, selector, is_nsfw)
        if "not_furry" in flags: is_all_furry = False
        sub_tags.extend(t_list)

    if not is_all_furry: tags.insert(0, "not furry")
    tags.extend(sub_tags)

    # Objects
    if random.random() < 0.2:
        c = 0
        if char_count == 1: c = selector.pick_count([[0, 40], [1, 20], [2, 10], [3, 2]])
        elif char_count == 2: c = selector.pick_count([[0, 30], [1, 20], [2, 5]])
        else: c = selector.pick_count([[0, 20], [1, 10]])
        
        for _ in range(c):
            tags.append(selector.weighted_choice(OBJECTS_FURRY))
            
    # Effects
    if random.random() < 0.25:
        c = selector.pick_count([[1, 80], [2, 20]])
        for _ in range(c):
            tags.append(selector.weighted_choice(EFFECTS_FURRY))
            
    if random.random() < 0.2:
        tags.append(selector.weighted_choice(YEARS_FURRY))
    
    if random.random() < 0.05:
        tags.append(selector.weighted_choice(FOCUS_FURRY))
        
    if use_holiday:
        tags.extend(add_holiday_spirit())
        
    # Clean up and Curly Brackets
    unique = list(dict.fromkeys([t for t in tags if t]))
    final = [apply_curly_brackets(t) for t in unique]
    
    return ", ".join(final)