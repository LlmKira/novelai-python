# src/novelai_python/tool/random_prompt/logic.py
import random
from typing import List, Any

class TagSelector:
    def __init__(self):
        self.selected_tags = set()

    def weighted_choice(self, choices: List[Any], simple: bool = False) -> str:
        valid_choices = []
        for item in choices:
            if not simple:
                blockers = item[4] if len(item) > 4 else []
                if blockers and any(b in self.selected_tags for b in blockers): continue
                requirements = item[3] if len(item) > 3 else []
                if requirements and not all(r in self.selected_tags for r in requirements): continue
            valid_choices.append(item)

        if not valid_choices: return ""

        total_weight = sum(item[1] for item in valid_choices)
        # JS: let r = tf(i, 1) -> floor(random * (i-1)) + 1
        r = int(random.random() * (total_weight - 1)) + 1
        
        upto = 0
        for item in valid_choices:
            upto += item[1] # JS: s += e[1]
            if r <= upto:   # JS: if (r <= s)
                tag = item[0]
                if not simple and len(item) > 2:
                    adds = item[2]
                    if isinstance(adds, list):
                        for t in adds: self.selected_tags.add(t)
                    elif isinstance(adds, str): self.selected_tags.add(adds)
                return tag
        return valid_choices[0][0]

    def pick_count(self, ranges: List[List[int]]) -> int:
        # То же самое для чисел
        total = sum(item[1] for item in ranges)
        r = int(random.random() * (total - 1)) + 1
        upto = 0
        for item in ranges:
            upto += item[1]
            if r <= upto:
                return item[0]
        return ranges[0][0]

def apply_curly_brackets(tag: str) -> str:
    if not tag: return ""
    if random.random() < 0.02:
        return f"{{{tag}}}"
    return tag
    
def js_random_int(min_val, max_val):
    """
    Эмуляция JS tf(max, min): floor(random * (max - min)) + min
    Верхняя граница НЕ включается в множитель, но результат сдвигается.
    Пример tf(3, 1) -> 1, 2.
    """
    return int(random.random() * (max_val - min_val)) + min_val