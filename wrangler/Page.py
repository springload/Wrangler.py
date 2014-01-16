import os
import re
import yaml
import json
import traceback

# Every file matching the pattern gets thrown into a Page object
class Page(object):
    def __init__(self, data, config):
        self.data = data
        self.config = config
        self.output_path = False
        self.fileExtension = self.config["data_format"]

    def get_page_content(self):
        return self.data["data"]

    def get_metadata(self):
        return self.data["meta"]

    def set_output_path(self, output_dir, output_file_extension):
        name = self.data["meta"]["relative_path"].replace(".%s" % (self.fileExtension), ".%s" % (output_file_extension), 1)
        path = "%s/%s" % (output_dir, name)
        self.output_path = re.sub("/{2,}", "/", path)
        self.data["meta"]["slug"] = self.output_path

    def get_output_path(self):
        return self.output_path

    def get_modified_time(self):
        return self.data["meta"]["mtime"]

    def get_file_path(self):
        return self.data["meta"]["file_path"]

    def get_mtime(self):
        if "mtime" in self.data["meta"]:
            return self.data["meta"]["mtime"]
        return 0

    def get_template(self):
        if "template" in self.data["meta"]:
            return self.data["meta"]['template']

        return self.config["default_template"]

    def before_render(self):
        return False;

    def on_save(self):
        return False;