from enum import Enum


class ReqType(Enum):
    """
    typing.Literal["bg-removal", "colorize", "lineart", "sketch", "emotion", "declutter"]
    """
    BG_REMOVAL = "bg-removal"
    COLORIZE = "colorize"
    LINEART = "lineart"
    SKETCH = "sketch"
    EMOTION = "emotion"
    DECLUTTER = "declutter"


class Moods(Enum):
    """
    The mood of the character in the image
    """
    Neutral = "neutral"
    Happy = "happy"
    Saf = "sad"
    Angry = "angry"
    Scared = "scared"
    Surprised = "surprised"
    Tired = "tired"
    Excited = "excited"
    Nervous = "nervous"
    Thinking = "thinking"
    Confused = "confused"
    Shy = "shy"
    Disgusted = "disgusted"
    Smug = "smug"
    Bored = "bored"
    Laughing = "laughing"
    Irritated = "irritated"
    Aroused = "aroused"
    Embarrassed = "embarrassed"
    Worried = "worried"
    Love = "love"
    Determined = "determined"
    Hurt = "hurt"
    Playful = "playful"
