import pprint 
import time 
import os

class SiteMap(object):
    def __init__(self, config={"options":{"webroot":"/"}}, node_graph=None):
        self.webroot = config["options"]["webroot"]
        self.node_graph = node_graph
        return None

    def process_node(self, node):
        data = []
        for key in node.children:
            if key.tag == "dir":
                index = key.get_child("index")
                index_data = None
                if index:
                    cargo = index.get_cargo()
                    if cargo:   
                        index_data = cargo.get_properties()

                data.append({"data": index_data, "children": self.process_node(key)})
            else:
                if not key.is_index:
                    cargo = key.get_cargo()
                    if cargo:
                        data.append({"data": key.get_cargo().get_properties(), "children": {}})
        return data
        
    def run(self):
        res = self.process_node(self.node_graph.tree())
        return res


class CacheBuster(object):
    def __init__(self, config={"options":{}}, node_graph=None):
        self.config = config
        
    def run(self):
        return int(time.time())


class FileInfo(object):
    def __init__(self, config={"options":{"directory":"assets", "filetypes": ["css", "pdf"]}}, node_graph=None):
        self.config = config

    def run(self):
        assets = {}
        for root, dirs, files in os.walk(self.config["options"]["directory"]):
            files = [f for f in files if not f[0] == '.' and any(f.endswith(x) for x in self.config["options"]["filetypes"])]
            dirs[:] = [d for d in dirs if not d[0] == '.']
            for fn in files:
                path = os.path.join(root, fn)
                file_type = os.path.splitext(path)[1].replace(os.path.extsep, "")
                mtime = os.path.getmtime(path)
                size = os.stat(path).st_size # in bytes
                assets[path] = {
                    "path": path.replace(self.config["options"]["webroot"], ""),
                    "name": fn,
                    "size": size,
                    "type": file_type,
                    "mtime": mtime
                }
        return assets


class Hook(object):
    def __init__(self, config, renderer):
        self.config = config
        self.renderer = renderer
        return None

    def process(self, items):
        return None
