class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, obj=None):
        obj = obj or {}
        for key, value in obj.items():
            self[key] = self.wrap_object(value)

    @staticmethod
    def wrap_object(obj):
        if isinstance(obj, dict):
            return DotDict(obj)
        elif isinstance(obj, list):
            return LengthList([DotDict.wrap_object(v) for v in obj])
        return obj
    
class LengthList(list):
    @property
    def length(self): return len(self)