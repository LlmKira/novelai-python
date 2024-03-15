import inspect
from abc import abstractmethod


class BaseCell(object):

    @abstractmethod
    def source(self):
        raise NotImplementedError

    @classmethod
    def attributes(cls):
        return [attr for attr in dir(cls) if attr.isupper()]

    @classmethod
    def get_values(cls):
        # 获取类中所有的大写属性的值
        return [value for name, value in inspect.getmembers(cls) if name.isupper()]
