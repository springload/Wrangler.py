import os
import subprocess
import shelve 
import sys 
import Core
import Parsers
from blinker import signal
import messages as messages

# Takes a directory and transforms the matching elements into Page instances.
class Reader():
    default_class = "Page"
    parsers = {}
    classes = {
        default_class: Core.Page
    }

    def __init__(self, config, reporter):
        conf = config["wrangler"]
        self.input_dir = conf['input_dir']
        self.ignore_files = conf['ignore']
        self.nocache = conf['nocache']
        self.lib_path = conf["lib_path"]
        self.config = config
        self.reporter = reporter
        formats_allowed_by_config = conf['data_formats'] if 'data_formats' in conf else None

        self.check_custom_default_class()
        self.data_formats = self.register_parsers(formats_allowed_by_config)


    def register_parsers(self, formats_allowed_by_config=None):
        formats = []

        if formats_allowed_by_config == []:
            exit("You need at least one file format configured. Check your wrangler.yaml file.")

        for cls in Core.Parser.__subclasses__():
            
            if hasattr(cls, "accepts"):
                acceptable_types = []
                parser = cls(self.input_dir, "")
                for file_format in cls.accepts:
                    if formats_allowed_by_config:
                        if file_format in formats_allowed_by_config:
                            acceptable_types.append(file_format)
                            self.parsers[file_format] =  parser
                    else:
                        acceptable_types.append(file_format)
                        self.parsers[file_format] =  parser

                self.reporter.verbose("Created a %s to handle %s" % (cls.__name__, acceptable_types), "blue")
                formats += acceptable_types

        return formats


    def check_custom_default_class(self):
        for cls in Core.Page.__subclasses__():
            if cls.__name__ == self.default_class:
                self.classes[self.default_class] = cls
                self.reporter.verbose("Set default class to new default subclass '%s'" % (cls.__name__), "blue")

           

    def load_class(self, file_class):
        if not file_class in self.classes:
            for cls in Core.Page.__subclasses__():
                if cls.__name__ == file_class:
                    self.classes[file_class] = cls
                    self.reporter.verbose("Loaded class %s" % (file_class), "blue")

        return self.classes[file_class]


    def init_cache(self):
        if (self.nocache):
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


    def dir_as_tree(self, path, parent=None):
        """Recursive function that walks a directory and returns a tree
        of nested nodes.
        """

        basename = os.path.basename(path)
        node = Core.Node(basename, path, parent)
        self.graph.add(node)

        # Gather some more information on this path here
        # and write it to attributes
        if os.path.isdir(path):
            # Recurse
            node.tag = 'dir'
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)

                # Ignore all the crufty things that get scraped, as well as hidden fies
                if not os.path.basename(item_path).startswith(".") and not ":" in item_path and not "%" in item_path and not "?" in item_path:
                    child_node = self.dir_as_tree(item_path, node)
                    node.add_child(child_node)
            return node
        else:
            node.tag = 'file'

            if basename.startswith("index") and basename.endswith(tuple(self.data_formats)):
                node.is_index = True 
            return node


    def comparitor(self, a, b):
        a_cargo = a.get_cargo()
        b_cargo = b.get_cargo()

        if not a_cargo:
            if a.tag == "dir":
                for _child in a.children:
                    filename = os.path.basename(_child.path)

                    if filename.startswith("index") and filename.endswith(tuple(self.data_formats)):
                        a_cargo = _child.get_cargo()
               
        if not b_cargo:
            if b.tag == "dir":
                for _child in b.children:
                    filename = os.path.basename(_child.path)
                    if filename.startswith("index") and filename.endswith(tuple(self.data_formats)):
                        b_cargo = _child.get_cargo()
                       
        try:
            a_weight = a_cargo.get_weight()
        except:
            a_weight = 0

        try:
            b_weight = b_cargo.get_weight()
        except:
            b_weight = 0

        if a_weight < b_weight: return -1
        if a_weight > b_weight: return 1

        return 0


    def recursive_sort(self, node):
        if node.tag == 'dir':
            node.children = sorted(node.children, cmp=self.comparitor)
            for n in node.children:
                self.recursive_sort(n)
        return node


    def fetch(self):
        shelf = self.init_cache()

        self.graph = Core.NodeGraph()
        root_node = self.dir_as_tree(self.input_dir)
        self.graph.root(root_node)
        
        for key, node in self.graph.all().items():
            if node.tag == "file":
                node.add_cargo(self.new_item(shelf, node.path))
        
        self.recursive_sort(root_node)
        self.save_cache(shelf)

        return self.graph


    def load_parser_by_format(self, data_format):
        try: 
            return self.parsers[data_format]
        except:
            self.reporter.verbose("No parser found for %s" % (data_format), "red")


    def new_item(self, shelf, filename):

        file_format = os.path.splitext(filename)[1].replace(os.extsep, "")
        parser = self.load_parser_by_format(file_format)

        try:
            mtime = os.path.getmtime(filename)
        except:
            print "Oops! Couldn't load \"%s\". Check the path exists." % (filename)
            return False

        if (not shelf.has_key(filename)) or (shelf[filename].get_mtime() < mtime) or (self.nocache):
            
            # Check if custom class is set, otherwise make it a page... 
            if parser:
                page_data = parser.load(filename);

                if page_data:
                    page_classname = self.default_class

                    if "class" in page_data["meta"]:
                        page_classname = page_data["meta"]["class"]

                    PageClass = self.load_class(page_classname)
                    new_page = PageClass(page_data, self.config)
                    shelf[filename] = new_page
                    print "\033[1;35mCaching \033[0m\033[2m%s\033[0m" % (filename)
                    return new_page
        else:
            if filename in shelf:
                return shelf[filename]
