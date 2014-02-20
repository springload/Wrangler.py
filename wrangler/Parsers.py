import yaml
import json
import Core
import markdown
import re

__yaml_frontmatter__ = r'(---)(.*?)\1'


class YamlParser(Core.Parser):
    accepts = ["yaml", "yml"]

    def interpret(self, file_contents):
        return yaml.load(file_contents)


class JsonParser(Core.Parser):
    accepts = ["json", "js"]

    def interpret(self, file_contents):
        return json.loads(file_contents)


class MarkdownParser(Core.Parser):
    accepts = ["md", "markdown"]
    delimiter = "---"

    def interpret(self, file_contents):
        data = {
            "meta": {},
            "data": {}
        }

        matter = re.search(__yaml_frontmatter__, file_contents, re.MULTILINE+re.DOTALL)
        if matter.group():
            data["meta"] = yaml.load(matter.group().replace(self.delimiter, ''))
            data["data"]["content"] = file_contents.replace(matter.group(), "")
        else:
            print "Couldn't load markdown."

        return data