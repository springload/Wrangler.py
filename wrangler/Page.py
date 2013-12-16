import os
import re
import yaml
import json
import traceback



# Every file matching the pattern gets thrown into a Page object
class Page():
    def __init__(self, fileName, input_dir, root, data_format):
        self.file_name, self.fileExtension = os.path.splitext(fileName)
        self.file_path = os.path.join(root, fileName)
        self.relative_path = os.path.join(root.replace(input_dir, "", 1), fileName)
        self.output_filename = ""
        self.output_path = ""
        self.file_contents = self.read_file(self.file_path)
        self.mtime = self.get_modified_time()
        self.data_format = data_format
        self.data = self.get_data(self.file_contents)
        self.meta = self.get_metadata(self.data)
        self.content = self.get_content(self.data)
        

    def read_file(self, file_path):
        source_file = open(file_path, 'r')
        file_contents = ""
        try:
            file_contents = source_file.read().decode('utf8')
        except:
            print "\033[31mTrouble reading %s\033[0m" % (source_file)
            traceback.print_exc() 
        
        return file_contents

    def get_data(self, file_contents):
        data = {
            "meta":{
                "title": None,
                "template": None,
                "description": None
            }
        }

        if self.data_format == "json":
            data.update(self.get_as_json(file_contents))

        if self.data_format == "yaml":
            data.update(self.get_as_yaml(file_contents))

        return data

    def get_as_json(self, file_contents):
        json_data = {}
        try:
            json_data = json.loads(file_contents)
        except:
            print "\033[31mCouldn't decode %s as JSON\033[0m" % (self.file_path)
            traceback.print_exc() 

        return json_data

    def get_as_yaml(self, file_contents):
        yaml_data = {}
        try:
            yaml_data = yaml.load(file_contents)
        except:
            print "\033[31mCouldn't decode %s as YAML\033[0m" % (self.file_path)
            traceback.print_exc() 
            
        return yaml_data

    def get_metadata(self, data):
        return data["meta"]

    def get_content(self, data):
        content = data.copy()
        content.pop("meta", None)
        return content

    def get_page_content(self):
        return self.content["data"]

    def get_page_content_from_list(self):
        content = self.file_contents
        values = ','.join(str(v) for v in content)
        return values

    def set_page_content(self, str):
        self.file_contents = str

    def get_page_vars(self):
        return self.meta

    def get_modified_time(self):
        mtime = os.path.getmtime(self.file_path)
        return mtime

    def get_template(self):
        template = 0
        if self.meta != 0:
            if self.meta['template']:
                template = self.meta['template']
        return template


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
