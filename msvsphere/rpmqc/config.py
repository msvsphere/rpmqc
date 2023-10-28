import re

import yaml

from .config_schema import ConfigSchema

__all__ = ['Config']


def regex_constructor(loader: yaml.Loader,
                      node: yaml.nodes.ScalarNode) -> re.Pattern:
    value = loader.construct_scalar(node)
    return re.compile(value)


class YamlConfigLoader(yaml.SafeLoader):

    @classmethod
    def make_loader(cls):
        cls.add_constructor(u'!regex', regex_constructor)
        return cls


class Config:

    def __init__(self, cfg_path: str):
        self.data = self._parse_config_file(cfg_path)

    @staticmethod
    def _parse_config_file(cfg_path: str) -> dict:
        with open(cfg_path, 'r') as fd:
            raw_cfg = yaml.load(fd.read(), YamlConfigLoader.make_loader())
        return ConfigSchema.validate(raw_cfg)
