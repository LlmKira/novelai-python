from novelai_python.utils.prompt_factory import Loader, DataSelector

data = Loader(source=DataSelector.ACTION)
tag = data.random_tag(sub_type=DataSelector.ACTION.FOOD, n=1000)
print(tag)
print(data.attributes)
