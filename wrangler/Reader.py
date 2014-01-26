import os
import subprocess
import shelve 
import sys 
import Core
import Parsers


class NodeGraph():
    def __init__(self):
        self._nodes = {}
        self._root = None

    def add(self, item):
        self._nodes[item.path] = item

    def root(self, item):
        self._root = item

    def tree(self):
        return self._root

    def all(self):
        return self._nodes


# Takes a directory and transforms the matching elements into Page instances.
class Reader():
    default_class = "Page"

    def __init__(self, config):
        self.input_dir = config['input_dir']
        self.ignore_files = config['ignore']
        self.data_format = config['data_format']
        self.nocache = config['nocache']
        self.config = config
        self.custom_default_module = self.check_custom_default()


    def check_custom_default(self):
        filename = "%s/%s.py" % (self.config["lib_path"], self.default_class)
        return os.path.exists(filename)


    def load_class(self, file_class):
        filename = "%s/%s.py" % (self.config["lib_path"], file_class)

        if not os.path.exists(filename):
            raise Exception("path %s doesn't exist in %s" % (file_class, self.config["lib_path"]))

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


    def fetch(self):
        shelf = self.init_cache()
        parser = self.load_parser_by_format(self.data_format, self.input_dir, "")

        self.graph = NodeGraph()

        root_node = self.dir_as_tree(self.input_dir)        

        
        self.graph.root(root_node)
        
        for key, node in self.graph.all().items():
            if node.tag == "file":

                node.add_cargo(self.new_item(parser, shelf, node.path))
        
        self.save_cache(shelf)
        return self.graph


    def load_parser_by_format(self, data_format, input_dir, root):

        for parser in dir(Parsers):
            p =  getattr(Parsers, parser)
            if hasattr(p, "__bases__") and hasattr(p, "accepts"):
                if data_format == p.accepts:
                    return p(input_dir, root)

        raise Exception("No parser found for %s" % (data_format))


    def new_item(self, parser, shelf, filename):
        mtime = os.path.getmtime(filename)
        if (not shelf.has_key(filename)) or (shelf[filename].get_mtime() < mtime) or (self.nocache):
            
            # Check if custom class is set, otherwise make it a page... 
            page_data = parser.load(filename);

            if page_data:

                page_view = page_data["meta"]["view"]

                if (page_view != None and "lib_path" in self.config):
                    PageClass = self.load_class(page_view)
                elif self.custom_default_module:
                    PageClass = self.load_class(self.default_class)
                else:
                    PageClass = getattr(Core, self.default_class)

                new_page = PageClass(page_data, self.config)
                shelf[filename] = new_page
                print "\033[1;35mCaching \033[0m\033[2m%s\033[0m" % (filename)
                return new_page
        else:
            return shelf[filename]
