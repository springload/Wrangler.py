import os
import time
import re
import traceback
import utilities as util

class Parser(object):

    defaults = {
        "meta":{
            "title": None,
            "template": None,
            "description": None,
            "view": None
        }
    }

    def __init__(self, input_dir, root):
       self.input_dir = input_dir
       self.project_root = root

    def get_data(self):
        return self.data

    def interpret(self, file_contents):
        return file_contents

    def attempt(self, file_contents, filepath):
        try:
            return self.interpret(file_contents)
        except:
            print "\033[31mCouldn't decode %s as %s\033[0m" % (filepath, self.accepts)
            traceback.print_exc()

    def read_file(self, file_path):
        source_file = open(file_path, 'r')
        file_contents = ""
        try:
            file_contents = source_file.read().decode('utf8')
        except:
            print "\033[31mTrouble reading %s\033[0m" % (source_file)
            traceback.print_exc()
        return file_contents
    
    def parse(self, filepath, file_name, relative_path,  file_contents, mtime):
        page_data = {"data":[]}
        contents = self.attempt(file_contents, filepath)
        page_data.update(self.defaults)
        
        if contents != None: 
            if "meta" in contents:
                page_data["meta"].update(contents["meta"])
            # print contents["data"]
            if "data" in contents:
                page_data["data"] = contents["data"]

        page_data["meta"].update({
            "filename": file_name,
            "filepath": filepath,
            "relative_path": relative_path,
            "mtime": mtime
        })
        return page_data

    def load(self, filepath):
        file_name, file_extension = os.path.splitext(filepath)
        file_path = os.path.join(self.project_root, filepath)
        relative_path = file_name.replace(self.input_dir+"/", "")     
        mtime = os.path.getmtime(filepath)
        file_contents = self.read_file(file_path)

        if file_extension == ".%s" % (self.accepts):
            return self.parse(file_path, file_name, relative_path, file_contents, mtime)
        else:
            raise Exception("%s does not parse %s, expected .%s" % (self.__class__.__name__, file_extension, self.accepts))


# Every file matching the pattern gets thrown into a Page object
class Page(object):
    def __init__(self, data, config):
        self.data = data
        self.config = config
        self.set_name(self.data["meta"]["filepath"])

    def get_content(self):
        return self.data["data"]

    def get_metadata(self):
        return self.data["meta"]
    
    def set_name(self, filepath):
        self.name = os.path.splitext(filepath)[0]
        return self.name
    
    def get_name(self):
        return self.name

    def get_output_path(self):
        return self.output_path

    def set_output_path(self, path):
        self.output_path = path

    def get_modified_time(self):
        return self.data["meta"]["mtime"]

    def get_file_path(self):
        return self.data["meta"]["filepath"]

    def get_mtime(self):
        if "mtime" in self.data["meta"]:
            return self.data["meta"]["mtime"]
        return 0

    def relpath(self):
        return self.data["meta"]["relative_path"]

    def get_template(self):
        if "template" in self.data["meta"]:
            return self.data["meta"]['template']

        return self.config["default_template"]

    def before_render(self):
        return False;

    def on_save(self):
        return False;


class Renderer(object):
    def __init__(self, config, reporter, writer):
        self.config = config
        self.reporter = reporter
        self.writer = writer
        self.init()
        return None

    def render(self, item):
        return str(item)


class Writer(object):
    def __init__(self, output_path, output_file_ext, reporter):
        self.output_path = output_path
        self.output_file_ext = output_file_ext
        self.reporter = reporter
        self.reporter.verbose("Ensure directory exists: \033[34m%s\033[0m" % (self.output_path))
        util.ensure_dir(self.output_path)
        return None

    def generate_output_path(self, filename):
        path = os.path.join(self.output_path, filename + os.extsep +  self.output_file_ext)
        return path

    def save(self, data):

        item=data[1]
        html=data[0]

        filename = item.get_output_path()
        new_directory = os.path.dirname(filename)

        if html == False:
            return False

        try: 
            util.ensure_dir(new_directory)
            file_object = open(filename, "w")
            file_object.write(html.encode('utf8'))
            self.reporter.print_stdout(item.get_file_path(), filename, item.get_template())
            item.on_save()
        except:
            print "\033[31mCouldn't write %s\033[0m" % (filename)
            traceback.print_exc()
            self.reporter.log_item_saved(item.get_file_path(), item.get_template(), 0)
            return False
        finally:
            self.reporter.log_item_saved(item.get_file_path(), item.get_template(), 1)
            return True


class Reporter(object):
    def __init__(self, config):
        self.config = config
        self.log_data = []
        return None

    def print_stdout(self, original_path, new_path, template):
        print "\033[1;32mBuilding \033[0m\033[2m%s\033[0m > \033[34m%s \033[2m[%s]\033[0m" % (original_path, new_path, template)


    def update_log(self, items, last_modified_time):
        file = open(self.config['compiled_templates_log'], 'w')
        print>>file, "this_render=%s, prev_render=%s" % (time.time(), last_modified_time)

        for item in items:
            print>>file, "%s, %s, %s" % (item[0], item[2], item[1])

        self.verbose("Wrote log to: \033[32m%s\033[0m" % (self.config['compiled_templates_log']))
    
    def log_item_saved(self, path, template, result):
        self.log_data.append([path, template, result])

    def get_last_build_time(self):
        """
        Get the last run time. Useful for checking what stuff's changed since we
        last ran the script.
        """
        last_time = 0
        if os.path.exists(self.config['build_cache_file']):
            with open(self.config['build_cache_file'], "r") as buildFile: 
                lines = map(float, buildFile.readline().split())
                if len(lines) > 0:
                    last_time = lines[0]
        return last_time

    def get_config_modified_time(self):
        """
        Force a re-render if the config file has changed (global paths may be invalid, etc..)
        """
        mtime = 0
        if os.path.exists(self.config['config_path']):
            mtime = os.path.getmtime(self.config['config_path'])
        return mtime

    def set_last_build_time(self, update_time=None):
        """
        Save the last successful run time in a var
        """
        if (update_time == None):
            update_time = time.time()

        self.update_log(self.log_data, self.get_last_build_time())

        with open(self.config['build_cache_file'], "w") as buildFile:
            buildFile.write("%s" % (update_time))

    def verbose(self, message):
        if self.config["verbose"] == True:
            print message

