import sys
import os
import random

# Добавляем src в путь, чтобы Python увидел твою библиотеку без установки через pip
# Если скрипт лежит в корне novelai-python/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from novelai_python.tool.random_prompt import RandomPromptGenerator, RandomPromptGeneratorV2
    # Для прямой проверки данных (опционально, если экспорт открыт)
    from novelai_python.tool.random_prompt.data.nsfw_data import NSFW_NW
    print("✅ Импорт прошел успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что запускаете скрипт из корня проекта и структура папок верна.")
    sys.exit(1)

def test_legacy():
    print("\n--- 1. TEST LEGACY (V1) ---")
    try:
        gen = RandomPromptGenerator()
        prompt = gen.generate_common_tags(nsfw=False)
        print(f"Legacy Prompt: {prompt[:100]}...") 
        if prompt:
            print("✅ Legacy generator works")
        else:
            print("⚠️ Legacy returned empty string")
    except Exception as e:
        print(f"❌ Legacy Failed: {e}")

def test_v2_anime_v3():
    print("\n--- 2. TEST ANIME V3 (Magic Dice) ---")
    try:
        # Прогоним 5 раз, чтобы убедиться, что веса не крашат скрипт
        for i in range(3):
            prompt = RandomPromptGeneratorV2.generate(model="anime_v3", holiday=True)
            print(f"V3 [{i}]: {prompt[:100]}...")
            
            # Проверка Holiday (работает только в Декабре)
            if "christmas" in prompt or "snow" in prompt or "winter" in prompt:
                print("   🎄 Holiday spirit detected!")
                
        print("✅ Anime V3 works")
    except Exception as e:
        print(f"❌ Anime V3 Failed: {e}")
        import traceback
        traceback.print_exc()

def test_v2_anime_v4():
    print("\n--- 3. TEST ANIME V4 (Curated) ---")
    try:
        for i in range(3):
            prompt = RandomPromptGeneratorV2.generate(model="anime_v4", holiday=False)
            print(f"V4 [{i}]: {prompt[:100]}...")
        print("✅ Anime V4 works")
    except Exception as e:
        print(f"❌ Anime V4 Failed: {e}")
        import traceback
        traceback.print_exc()

def test_v2_furry():
    print("\n--- 4. TEST FURRY (SFW & NSFW) ---")
    try:
        # SFW
        sfw_prompt = RandomPromptGeneratorV2.generate(model="furry", nsfw=False)
        print(f"🦊 Furry SFW: {sfw_prompt[:100]}...")

        # NSFW
        # Проверяем, расшифровался ли NSFW_NW (тег "nsfw")
        if NSFW_NW == "BAD_WORD" or not NSFW_NW:
             print("⚠️ Внимание: NSFW данные не расшифрованы (используются заглушки).")
        
        nsfw_prompt = RandomPromptGeneratorV2.generate(model="furry", nsfw=True)
        print(f"🔞 Furry NSFW: {nsfw_prompt[:100]}...")
        
        # Проверка на наличие NSFW маркера
        if "nsfw" in nsfw_prompt or NSFW_NW in nsfw_prompt:
            print("✅ NSFW tag injection works")
        else:
            print("⚠️ NSFW tag missing (might be random chance or decoding issue)")

    except Exception as e:
        print(f"❌ Furry Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Testing Random Prompt Generator...")
    test_legacy()
    test_v2_anime_v3()
    test_v2_anime_v4()
    test_v2_furry()
    print("\n🎉 Все тесты завершены.")