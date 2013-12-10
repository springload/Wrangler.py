from jinja2 import Undefined


# Jinja 2 replace undefined with a blank string, kind of like twig :)
class SilentUndefined(Undefined):
    """
    A redefinition of undefined that eats errors.
    """
    def __getattr__(self, name):
        return self

    __getitem__ = __getattr__

    def __call__(self, *args, **kwargs):
        return self