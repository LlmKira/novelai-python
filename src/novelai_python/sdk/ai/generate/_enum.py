from enum import Enum
from typing import List


class PenStyle(Enum):
    Off = "off"
    VeryLight = "very_light"
    Light = "light"
    Default = "medium"
    Aggressive = "aggressive"
    VeryAggressive = "very_aggressive"


class Order(Enum):
    Temperature = ("temperature", 0)
    TopK = ("top_k", 1)
    TopP = ("top_p", 2)
    TFS = ("tfs", 3)
    TopA = ("top_a", 4)
    TypicalP = ("typical_p", 5)
    Cfg = ("cfg", 6)
    TopG = ("top_g", 7)
    Mirostat = ("mirostat", 8)
    Math1 = ("math1", 9)
    MinP = ("min_p", 10)


def generate_order(request_body: dict) -> List[int]:
    order_list = []
    for member in Order:
        key, order = member.value
        if key in request_body and request_body[key] is None:
            order_list.append(order)
    order_list.sort()  # ensures the order list is properly sorted according to the true order
    return order_list
