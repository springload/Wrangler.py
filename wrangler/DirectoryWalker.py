import os
import subprocess
import shelve 
import sys 
import Page
from YamlParser import YamlParser

# Takes a directory and transforms the matching elements into the matching class.
class DirectoryWalker():
    def __init__(self, config):
        self.input_dir = config['input_dir']
        self.ignore_files = config['ignore']
        self.data_format = config['data_format']
        self.nocache = config['nocache']
        self.config = config


    def load_class(self, file_class):
        filename = "%s/%s.py" % (self.config["views"], file_class)

        if not os.path.exists(filename):
            raise Exception("path %s doesn't exist in %s" % (file_class, self.config["views"]))

        directory, module_name = os.path.split(filename)
        module_name = os.path.splitext(module_name)[0]

        path = list(sys.path)
        sys.path.insert(0, directory)

        try:
            module = __import__(module_name)
        finally:
            sys.path[:] = path # restore

        for name in dir(module):
            if module_name.split(".")[0] == name:
                return getattr(module, name)

        return Page

    def fetch(self):
        items = []

        # Not supported in python 2.6 hmmm
        # if sys.version_info > (2,7,0):
            # files = subprocess.check_output(["find", self.input_dir, "-name", "*.%s" % (self.data_format)], stderr=subprocess.STDOUT)
        # else:
        p = subprocess.Popen(["find", self.input_dir, "-name", "*.%s" % (self.data_format)], stdout=subprocess.PIPE)

        out, err = p.communicate()
        files = out.split("\n")

        if (self.config["nocache"]):
            try:
                os.remove("wrangler_cache.db")
            except OSError:
                pass

        shelf = shelve.open("wrangler_cache") 

        for f in files: 
            if f != '':

                file_mtime = os.path.getmtime(f);
                lib_needs_refresh = False

                if "views" in self.config and f in shelf and hasattr(shelf[f], "item_class"):
                    lib_path = self.config["views"];
                    lib_mtime = os.path.getmtime("%s/%s" % (lib_path, shelf[f].item_class))
                    
                    if lib_mtime < file_mtime:
                        lib_needs_refresh = True

                # If the key doesn't exist on the shelf, or the mtime is different, re-cache the object
                if (not shelf.has_key(f)) or (shelf[f].get_mtime() < file_mtime) or (self.nocache) or (lib_needs_refresh):

                    # Check if custom class is set, otherwise make it a page... 
                    page = YamlParser(f, self.input_dir, "");

                    if (page.item_class and "views" in self.config):
                        pageClass = self.load_class(page.item_class)
                    else:
                        pageClass = Page.Page

                    item = pageClass(page.data, self.config)

                    # Register the output path
                    item.set_output_path(self.config['output_dir'], self.config['output_file_extension'])
                    shelf[f] = item

                    print "\033[1;35mCaching \033[0m\033[2m%s\033[0m" % (f)

                items.append(shelf[f])
        try:
            shelf.sync()
        finally:
            shelf.close()

        return items