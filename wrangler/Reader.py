import os
import subprocess
import shelve 
import sys 
import Core
import Parsers

# Takes a directory and transforms the matching elements into Page instances.
class Reader():
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

    def get_files(self):
        return self.files
    
    def init_cache(self):
        if (self.config["nocache"]):
            try:
                os.remove("wrangler_cache.db")
            except OSError:
                pass

        return shelve.open("wrangler_cache") 
    
    def save_cache(self, shelf):
        try:
            shelf.sync()
        finally:
            shelf.close()

    def fetch(self):
        items = []

        p = subprocess.Popen(["find", self.input_dir, "-name", "*.%s" % (self.data_format)], stdout=subprocess.PIPE)

        out, err = p.communicate()
        files = out.split("\n")

        if (self.config["verbose"]):
            print "Searching input directory '%s' " % (self.input_dir)

        self.files = files

        return self.process(files, self.data_format)

    
    def load_parser_by_format(self, data_format, input_dir, root):

        for parser in dir(Parsers):
            p =  getattr(Parsers, parser)
            if hasattr(p, "__bases__") and hasattr(p, "accepts"):
                if data_format == p.accepts:
                    return p(input_dir, root)

        raise Exception("No parser found for %s" % (data_format))


    def new_item(self, parser, filename):
        # Check if custom class is set, otherwise make it a page... 
        page_data = parser.load(filename);
        page_view = page_data["meta"]["view"]

        if (page_view != None and "views" in self.config):
            PageClass = self.load_class(page_view)
        else:
            PageClass = Core.Page

        return PageClass(page_data, self.config)

    def process(self, files, data_format):

        shelf = self.init_cache()
        parser = self.load_parser_by_format(self.data_format, self.input_dir, "")
        items = []

        if (self.config["verbose"]):
            print "Target directory contains %s items" % (len(files)) 

        for f in files:
            try: 
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
                        shelf[f] = self.new_item(parser, f)
                        print "\033[1;35mCaching \033[0m\033[2m%s\033[0m" % (f)

                    items.append(shelf[f])
            except (KeyboardInterrupt, SystemExit):
                break
                raise
            except:
                raise
            
        self.save_cache(shelf)
        
        return items
