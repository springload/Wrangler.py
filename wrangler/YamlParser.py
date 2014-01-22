import os
import re
import yaml
import json
import traceback

class YamlParser():
    def __init__(self, fileName, input_dir, root):
        self.file_name, self.fileExtension = os.path.splitext(fileName)
        self.file_path = os.path.join(root, fileName)
        self.relative_path = self.file_path.replace(input_dir+"/", "")        
        self.output_filename = ""
        self.output_path = ""
        self.mtime = self.get_modified_time()
        self.file_contents = self.read_file(self.file_path)
        self.data = self.get_data(self.file_contents)
        self.item_class = self.get_itemclass()
        
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
        data.update(self.get_as_yaml(file_contents))

        data["meta"]["file_name"] = self.file_name
        data["meta"]["file_path"] = self.file_path
        data["meta"]["relative_path"] = self.file_path
        data["meta"]["mtime"] = self.mtime

        return data

    def get_itemclass(self):
        if self.data["meta"]:
            if "view" in self.data["meta"]:
                return self.data["meta"]["view"]

        return False

    def get_as_yaml(self, file_contents):
        yaml_data = {}
        try:
            yaml_data = yaml.load(file_contents)
        except:
            print "\033[31mCouldn't decode %s as YAML\033[0m" % (self.file_path)
            traceback.print_exc() 
    
        return yaml_data


    def get_modified_time(self):
        mtime = os.path.getmtime(self.file_path)
        return mtime

    def set_output_path(self, output_dir, output_file_extension):
        name = self.relative_path.replace(self.fileExtension, ".%s" % (output_file_extension), 1)
        path = "%s/%s" % (output_dir, name)
        self.output_path = re.sub("/{2,}", "/", path)
        self.output_filename = name
        self.meta["slug"] = self.output_filename

    def get_output_path(self):
        return self.output_path

    def get_file_path(self):
        return self.file_path

    def get_relative_path(self):
        return self.relative_path
