import os
import time
import re
import traceback
import utilities as util
import itertools
from copy import deepcopy
from unicodedata import normalize
from blinker import signal

"""
---------------------------------------------------------------------------------------------------
Generally useful things
---------------------------------------------------------------------------------------------------

"""

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')

def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

# Takes a path, slugifies the filename, returns it.

def clean_path(filename, ext):
    path = os.path.dirname(filename)
    basename = os.path.basename(filename)
    clean_filename = slugify(u"%s" % (basename))
    return os.path.join(path,clean_filename + os.extsep + ext)

"""
---------------------------------------------------------------------------------------------------
Parser
---------------------------------------------------------------------------------------------------

Normalises data in a file and returns dicts ready to construct
page objects with

"""
class Parser(object):

    defaults = {
        "meta":{
            "title": None,
            "template": None,
            "description": None,
            "view": None,
            "output_file_extension": None
        }
    }

    def __init__(self, input_dir, root):
       self.input_dir = input_dir
       self.project_root = root

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
        _defaults = deepcopy(self.defaults)
        page_data.update(_defaults)
        
        if contents != None: 
            if "meta" in contents:
                page_data["meta"].update(contents["meta"])
            if "data" in contents:
                page_data["data"] = contents["data"]

        page_data["meta"].update({
            "filename": file_name,
            "filepath": filepath,
            "relative_path": relative_path,
            "mtime": mtime
        })

        sig = signal("wranglerLoadItem")
        sig.send('item', item=file_name, file_contents=file_contents, mtime=mtime)

        return page_data

    def load(self, filepath):
        file_name, file_extension = os.path.splitext(filepath)
        file_path = os.path.join(self.project_root, filepath)
        relative_path = file_name.replace(self.input_dir+"/", "")     
        mtime = os.path.getmtime(filepath)
        file_contents = self.read_file(file_path)

        if file_extension:

            if file_extension == ".%s" % (self.accepts):
                return self.parse(file_path, file_name, relative_path, file_contents, mtime)
            else:
                print "%s does not parse %s, expected .%s. Check the 'data_format' in wrangler.json" % (self.__class__.__name__, file_extension, self.accepts)




"""
---------------------------------------------------------------------------------------------------
NodeGraph
---------------------------------------------------------------------------------------------------

Allow for flat and tree navigation within a directory

"""

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



"""
---------------------------------------------------------------------------------------------------
Node
---------------------------------------------------------------------------------------------------

Tree object that makes it easier to keep track of all the pages and how they relate to each other.

"""

class Node(object):
    def __init__(self, name, path, parent=None, cargo=None):
        self.name = name
        self.path = path
        self.cargo = cargo
        self.parent = parent
        self.children = list()
        self.is_index = False
        return None

    def add_child(self, node):
        self.children.append(node)

    def add_cargo(self, cargo=None):
        self.cargo = cargo

    def get_cargo(self):
        return self.cargo

    def get_children(self):
        return self.children

    def get_parent(self):
        return self.parent

    def get_siblings(self):
        siblings = []
        if self.parent != None:
            siblings = self.get_parent().get_children()
        return siblings

    def get_unique_siblings(self):
        siblings = []
        if self.parent != None:
            siblings = [sibling for sibling in  self.get_parent().get_children() if sibling.path != self.path]
        return siblings 

    def get_child(self, name):
        child = None

        for item in self.children:
            if name == "index" and item.is_index:
                child = item
            elif item.name == name:
                child = item  

        return child

    def get_child_pages(self):
        children = []

        directories = [d for d in self.get_parent().get_children() if d.tag == 'dir']
        
        # print "child pages for %s" % (self.path)

        for node in directories:
            index = node.get_child("index")

            # print "\t", node.path


            if index:
                children.append(index)

        return children

    def get_parents(self):
        parents = []

        def _get(n):
            if n != None:
                parents.append(n.get_child("index"))
                _get(n.parent)

        _get(self.parent)

        return parents

    def get_parent_dirs(self):
        parents = []

        def _get(n):
            if n != None:
                parents.append(n)
                _get(n.parent)

        _get(self.parent)

        return parents
    

    def get_parents_siblings(self):
        _parent_siblings = []

        is_deep_enough = hasattr(self.get_parent(), "get_parent")

        if is_deep_enough:
            parent = self.get_parent().get_parent()

        if parent:
            directories = [d for d in parent.get_children() if d.tag == 'dir'] 

            for node in directories:
                index = node.get_child("index")

                if index:
                    _parent_siblings.append(index)

        return _parent_siblings


"""
---------------------------------------------------------------------------------------------------
Page
---------------------------------------------------------------------------------------------------

Provides methods for dealing with data loaded from a filesystem

"""
class Page(object):
    new_id = itertools.count().next
    def __init__(self, data, config):
        self.id = Page.new_id()
        self.data = data
        self.config = config
        self.set_name(self.data["meta"]["filepath"])
        self.data["meta"]["id"] = self.id

    def get_content(self):
        return self.data["data"]

    def get_metadata(self):
        return self.data["meta"]

    def get_file_ext(self):
        return self.data["meta"]["output_file_extension"] if "output_file_extension" in self.data["meta"] else None
    
    def set_name(self, filepath):
        self.name = os.path.splitext(filepath)[0]
        return self.name
    
    def get_name(self):
        return self.name

    def get_title(self):
        return self.data["meta"]["title"] if "title" in self.data["meta"] else None

    def get_short_title(self):
        return self.data["meta"]["alias"] if "alias" in self.data["meta"] else None

    def get_meta_description(self):
        return self.data["meta"]["description"] if "description" in self.data["meta"] else None

    def get_meta_keywords(self):
        return self.data["meta"]["keywords"] if "keywords" in self.data["meta"] else None

    def get_output_path(self):
        file_ext = self.get_file_ext()
        
        if file_ext == None:
            return self.output_path
        else:
            return self.output_path_no_ext + file_ext

    def get_relative_output_path(self):
        return self.relative_output_path

    def set_output_path(self, path):
        self.output_path = path[0]
        self.relative_output_path = path[1]
        self.output_path_no_ext = path[2]
        
        self._ext = self.output_path.split(".")[1]
        tidy_url = self.relative_output_path.replace("index.%s" % (self._ext), "")

        self.data["meta"]["segments"] = [segment for segment in self.relative_output_path.split("/")]
        self.data["meta"]["url"] = "/%s" % (tidy_url)
        self.data["meta"]["path"] = "/%s/" % (os.path.dirname(self.relative_output_path))


    def get_tidy_url(self):
        return self.data["meta"]["url"]

    def get_modified_time(self):
        return self.data["meta"]["mtime"]

    def get_file_path(self):
        return self.data["meta"]["filepath"]

    def get_tags(self):
        return self.data["meta"]["tags"] if "tags" in self.data["meta"] else None

    def get_related(self):
        return self.data["meta"]["related"] if "related" in self.data["meta"] else None

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

    def show_in_navigation(self):
        return False if "hide_from_nav" in self.data["meta"] and self.data["meta"]["hide_from_nav"] else True

    def get_weight(self):
        return self.data["meta"]["weight"] if "weight" in self.data["meta"] else 0

    def get_thumbnail(self):
        return self.data["meta"]["thumbnail"] if "thumbnail" in self.data["meta"] else None

    def get_properties(self):
        return {
                "title": self.get_title(),
                "alias": self.get_short_title(),
                "description": self.get_meta_description(),
                "url": self.get_tidy_url(),
                "show_in_navigation": self.show_in_navigation(),
                "weight": self.get_weight(),
                "thumbnail": self.get_thumbnail()
        }

    def map_related_nodes(self, nodes, keyname):
        _data = []
        
        for node in nodes:
            if node:
                page = node.get_cargo()
                if page != None:
                    _data.append(page.get_properties())
        
        self.data["meta"][keyname] = _data

    def set_siblings(self, nodes):
        self.map_related_nodes(nodes, "siblings")

    def set_parents(self, nodes):
        self.map_related_nodes(nodes, "parents")

    def set_children(self, nodes):
        self.map_related_nodes(nodes, "children")

    def set_parents_siblings(self, nodes):
        self.map_related_nodes(nodes, "parents_siblings")

    def set_related_nodes(self, nodes):
        self.map_related_nodes(nodes, "related_nodes")

    def cleanup(self):
        self.data["meta"]["siblings"] = None
        self.data["meta"]["parents"] = None
        self.data["meta"]["parents_siblings"] = None
        self.data["meta"]["children"] = None
        self.data["meta"]["related_nodes"] = None


"""
---------------------------------------------------------------------------------------------------
Renderer
---------------------------------------------------------------------------------------------------

Generates templated content to pass to the writer

"""
class Renderer(object):
    def __init__(self, config, reporter, writer):
        self.config = config
        self.reporter = reporter
        self.writer = writer
        self.init()
        return None

    def render(self, item):
        return str(item)

"""
---------------------------------------------------------------------------------------------------
Writer
---------------------------------------------------------------------------------------------------

Saves rendered items to the filesystem

"""
class Writer(object):
    def __init__(self, output_path, output_file_ext, reporter):
        self.output_path = output_path
        self.output_file_ext = output_file_ext
        self.reporter = reporter
        self.reporter.verbose("Ensure directory exists: \033[34m%s\033[0m" % (self.output_path))
        util.ensure_dir(self.output_path)
        return None

    def generate_output_path(self, filename):
        relative_output_path = clean_path(filename, self.output_file_ext)
        path = os.path.join(self.output_path, relative_output_path)
        path_no_ext = os.path.join(self.output_path, filename + os.extsep)
        return path, relative_output_path, path_no_ext

    def save(self, data):

        item=data[1]
        html=data[0]

        filename = item.get_output_path()
        new_directory = os.path.dirname(filename)

        if html == False:
            return False

        try: 
            sig = signal('wranglerBeforeSaveItem')
            sig.send('item', item=item, path=filename)
            util.ensure_dir(new_directory)
            file_object = open(filename, "w")
            file_object.write(html.encode('utf8'))
            self.reporter.print_stdout(item.get_file_path(), filename, item.get_template())
            item.on_save()
            siggy = signal('wranglerOnSaveItem')
            siggy.send('item', item=item, path=filename)

        except:
            print "\033[31mCouldn't write %s\033[0m" % (filename)
            traceback.print_exc()
            self.reporter.log_item_saved(item.get_file_path(), item.get_template(), 0)
            return False
        finally:
            self.reporter.log_item_saved(item.get_file_path(), item.get_template(), 1)
            return True




"""
---------------------------------------------------------------------------------------------------
Reporter
---------------------------------------------------------------------------------------------------
Shares our findings with the rest of the class

"""
class Reporter(object):
    def __init__(self, config):
        self.config = config
        self.log_data = []
        return None

    def print_stdout(self, original_path, new_path, template):
        self.verbose("\033[1;32mBuilding \033[0m\033[2m%s\033[0m > \033[34m%s \033[2m[%s]\033[0m" % (original_path, new_path, template))


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

    def pretty(self, colour, message):
        colours = {
            "green": "\033[32m",
            "red": "\033[31m",
            "blue": "\033[34m",
            "basic": "\033[0m"
        }
        
        return "%s%s%s" % (colours[colour], message, colours["basic"]) 

    def log(self, message, status=None):
        msg = message
        if status:
            msg = self.pretty(status, message)
        print msg

    def verbose(self, message):
        if self.config["verbose"] == True:
            print message



# """
# ---------------------------------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------------------------------
# """

# class Extension(object):
#     """
#     Simple implementation of extensions.
#     """
#     default = {
#         "options":{}
#     }
#     def __init__(self, config=None, node_graph=None, reporter=None):
#         self.config = config if config != None else self.default
#         self.node_graph = node_graph
#         self.reporter=reporter


