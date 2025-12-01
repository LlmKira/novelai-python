import random
from ..data.holiday import HOLIDAY_TAGS
from ..logic import TagSelector, js_random_int

def inject_holiday_spirit(prompt_text: str) -> str:
    selector = TagSelector()
    
    # В JS: tf(3, 5) -> floor(rnd * -2) + 5 -> 3, 4
    # В Python js_random_int(3, 5): int(rnd * (5-3)) + 3 -> int(rnd*2) + 3 -> 3, 4.
    count = js_random_int(3, 6)

    selected = set()
    holiday_parts = []
    
    for _ in range(count):
        tag = selector.weighted_choice(HOLIDAY_TAGS, simple=True)
        attempts = 0
        while tag in selected and attempts < 10:
            tag = selector.weighted_choice(HOLIDAY_TAGS, simple=True)
            attempts += 1
        
        if tag and tag not in selected:
            selected.add(tag)
            holiday_parts.append(tag)

    if not prompt_text:
        parts = []
    else:
        parts = prompt_text.split(",")

    part1 = ",".join(parts[:6])
    holiday_str = ", ".join(holiday_parts)
    part2 = ",".join(parts[6:])

    result = ""
    if part1:
        result += part1
        
    result += ", " + holiday_str + "," + part2
    
    return result