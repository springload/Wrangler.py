import yaml
import json
import Core

class YamlParser(Core.Parser):
    accepts = "yaml"

    def interpret(self, file_contents):
        return yaml.load(file_contents)


class JsonParser(Core.Parser):
    accepts = "json"

    def interpret(self, file_contents):
        return json.load(file_contents)