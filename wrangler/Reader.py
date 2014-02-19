import os
import subprocess
import shelve 
import sys 
import Core
import Parsers
from blinker import signal

# Takes a directory and transforms the matching elements into Page instances.
class Reader():
    default_class = "Page"
    parsers = {}
    classes = {
        default_class: Core.Page
    }

    def __init__(self, config):
        self.input_dir = config['input_dir']
        self.ignore_files = config['ignore']
        self.data_format = config['data_format']
        self.nocache = config['nocache']
        self.config = config
        self.check_custom_default_class()


    def check_custom_default_class(self):
        if "lib_path" in self.config:
            filename = "%s/%s.py" % (self.config["lib_path"], self.default_class)
            if os.path.exists(filename):
                self.load_class(self.default_class)


    def load_class(self, file_class):

        if file_class == None:
            file_class = self.default_class
        else:

            if not file_class in self.classes or file_class == self.default_class:

                filename = "%s/%s.py" % (self.config["lib_path"], file_class)

                if not os.path.exists(filename):
                    raise Exception("path %s doesn't exist in %s" % (file_class, self.config["lib_path"]))

                directory, module_name = os.path.split(filename)
                module_name = os.path.splitext(module_name)[0]

                path = list(sys.path)
                sys.path.insert(0, self.config["lib_path"])

                try:
                    module = __import__(module_name)
                finally:
                    sys.path[:] = path # restore

                for name in dir(module):
                    if module_name.split(".")[0] == name:
                        self.classes[name] = getattr(module, name)
            

        return self.classes[file_class]
    

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

            if basename == "index.%s" % (self.data_format):
                node.is_index = True 
            return node


    def comparitor(self, a, b):
        a_cargo = a.get_cargo()
        b_cargo = b.get_cargo()

        if not a_cargo:
            if a.tag == "dir":
                for _child in a.children:
                    if _child.path.endswith("index.%s" % (self.config["data_format"])):
                        a_cargo = _child.get_cargo()
               
        if not b_cargo:
            if b.tag == "dir":
                for _child in b.children:
                    if _child.path.endswith("index.%s" % (self.config["data_format"])):
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
        """
        Load parsers based on the file contents and cache 'em up so we can
        re-use them.
        """
        if not data_format in self.parsers:
            for parser in dir(Parsers):
                p =  getattr(Parsers, parser)
                if hasattr(p, "__bases__") and hasattr(p, "accepts"):
                    if data_format == p.accepts:
                        self.parsers[data_format] =  p(self.input_dir, "")
        try: 
            return self.parsers[data_format]
        except:
            raise Exception("No parser found for %s" % (data_format))


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
            page_data = parser.load(filename);

            if page_data:
                page_view = None

                if "view" in page_data["meta"]:
                    page_view = page_data["meta"]["view"]

                PageClass = self.load_class(page_view)
                new_page = PageClass(page_data, self.config)
                shelf[filename] = new_page
                print "\033[1;35mCaching \033[0m\033[2m%s\033[0m" % (filename)
                return new_page
        else:
            return shelf[filename]
