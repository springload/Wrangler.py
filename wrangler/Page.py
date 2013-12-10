import os
import re
import yaml
import json

# Every file matching the pattern gets thrown into a Page object
class Page():
    def __init__(self, fileName, input_dir, root):
        self.file_name, self.fileExtension = os.path.splitext(fileName)
        self.file_path = os.path.join(root, fileName)
        self.relative_path = os.path.join(root.replace(input_dir, "", 1), fileName)
        self.output_filename = ""
        self.output_path = ""
        # self.file_contents = ""
        # self.mtime = 0
        # self.meta = {}
        self.file_contents = self.get_contents(self.file_path)
        self.mtime = self.get_modified_time()
        self.meta = self.get_metadata(self.file_contents)

    def get_contents(self, file_path):
        source_file = open(file_path, 'r')
        file_contents = source_file.read()
        return file_contents

    def get_metadata(self, file_contents):
        page_vars = {}
        if self.fileExtension == ".json":
            page_vars = self.get_as_json(file_contents)

        if self.fileExtension == ".md":
            page_vars = self.get_as_yaml(file_contents)

        return page_vars

    def get_as_json(self, file_contents):

        page_vars = {"yk_data":{"title": None, "template": None, "description": None}}
        default_content = {"data":""}

        json_data = json.loads(file_contents)

        if "yk_data" in json_data:
            page_vars.update(json_data["yk_data"])

        # For backwards compatibility with old stuff
        page_vars["extends"] = page_vars["template"]
        
        if "data" in json_data:
            self.file_contents = json_data["data"]
        else:
            self.file_contents = default_content

        return page_vars

    def get_as_yaml(self, file_contents):
        delimiter = "@@@"
        md_hash = re.split("(%s)" % (delimiter), file_contents)
        page_vars = 0

        if len(md_hash) > 1:
            page_vars = yaml.load(md_hash[2])
            file_contents = "%s%s" % (md_hash[0], md_hash[4])
            self.file_contents = file_contents.replace("{##}", "")

        return page_vars

    def get_page_content(self):
        return self.file_contents

    def get_page_content_from_list(self):
        content = self.file_contents
        values = ','.join(str(v) for v in content)
        return values

    def set_page_content(self, str):
        self.file_contents = str

    def get_page_vars(self):
        return self.meta

    def get_modified_time(self):
        return os.path.getmtime(self.file_path)

    def get_template(self):
        template = 0
        if self.meta != 0:
            if self.meta['extends']:
                template = self.meta['extends']
        return template

    # def before_render(self):
        # self.file_contents = self.get_contents(self.file_path)
        # self.mtime = self.get_modified_time()
        # self.meta = self.get_metadata(self.file_contents)

    def set_output_path(self, output_dir, output_file_extension):
        name = self.relative_path.replace(self.fileExtension, ".%s" % (output_file_extension), 1)
        path = "%s/%s" % (output_dir, name)
        self.output_path = re.sub("/{2,}", "/", path)
        self.output_filename = name

    def get_output_path(self):
        return self.output_path

    def get_file_path(self):
        return self.file_path

    def get_relative_path(self):
        return self.relative_path
