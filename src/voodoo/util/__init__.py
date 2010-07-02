def M_add_class_attribs(attribs):
    def foo(name, bases, dict_):
        for v, k in attribs:
            dict_[k] = v
        return type(name, bases, dict_)
    return foo

def enum(names):
    class Foo(object):
        __metaclass__ = M_add_class_attribs(enumerate(names))
        def __setattr__(self, name, value):  # this makes it read-only
            raise NotImplementedError
    return Foo()

__all__ = ["enum"]
