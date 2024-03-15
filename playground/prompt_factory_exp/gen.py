from novelai_python.utils.prompt_factory import Generator, DataSelector

gens = Generator(pool=[

]
    , class_sample=5, tag_sample=1, tag_piece=0,
)
print(gens.generate_pool())
ori, cle = gens.generate(enable_nsfw=False, enable_illustrator=True)
print(ori, cle)
print(", ".join(cle))
