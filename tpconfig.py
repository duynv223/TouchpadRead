from ruamel.yaml import YAML


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TpConfig(metaclass=Singleton):
    config = None

    def __init__(self):
        self.load()

    def load(self):
        yaml = YAML()
        self.config = yaml.load(open('config.yaml'))

    def save(self):
        pass
