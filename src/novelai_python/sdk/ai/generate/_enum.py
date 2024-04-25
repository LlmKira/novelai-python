# Description: Enum class for TextLLMModel
from enum import Enum
from typing import List


class TextLLMModel(Enum):
    """
    Enum class for TextLLMModel
    """
    Sigurd = "6B-v4"
    Euterpe = "euterpe-v2"
    Krake = "krake-v2"

    Clio = "clio-v1"
    Kayra = "kayra-v1"
    """Default model for TextLLMModel"""

    Genji = "genji-jp-6b-v2"
    Snek = "genji-python-6b"
    HypeBot = "hypebot"
    """Default comment model for TextLLMModel"""
    Inline = "infillmodel"

    neo2b = "2.7B"
    j6b = "6B"
    j6bv3 = "6B-v3"
    genjijp6b = "genji-jp-6b"
    euterpev0 = "euterpe-v0"
    blue = "blue"
    red = "red"
    green = "green"
    purple = "purple"
    cassandra = "cassandra"


TOKENIZER = {
    TextLLMModel.Sigurd: "gpt2",
    TextLLMModel.Euterpe: "gpt2",
    TextLLMModel.Krake: "pile",
    TextLLMModel.Snek: "gpt2",
    TextLLMModel.Genji: "gpt2-genji",
    TextLLMModel.HypeBot: "gpt2",
    TextLLMModel.Inline: "gpt2",
    TextLLMModel.Clio: "nerdstash_v1",
    TextLLMModel.Kayra: "nerdstash_v2",
}


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


def generate_order(request_body: dict) -> List[int]:
    order_list = []
    for member in Order:
        key, order = member.value
        if key in request_body and request_body[key] is None:
            order_list.append(order)
    order_list.sort()  # ensures the order list is properly sorted according to the true order
    return order_list
