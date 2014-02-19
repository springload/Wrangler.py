import pprint 
import time 
import os
from blinker import signal

extension = signal("wranglerExtension")

class SiteMap(object):
    def __init__(self, config, reporter, nodes):
        self.config = config
        self.reporter = reporter
        self.nodes = nodes

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
        self.webroot = self.config["webroot"]
        res = self.process_node(self.nodes.tree())
        if "debug" in self.config and self.config["debug"] == True:
            p = pprint.PrettyPrinter(depth=12)
            p.pprint(res)
        return res


@extension.connect
def sitemap(sender, **kwargs):
    return SiteMap(kwargs["config"]["extensions"]["sitemap"], kwargs["reporter"], kwargs["nodes"]).run()


@extension.connect
def cachebuster(sender, **kwargs):
    return int(time.time())


@extension.connect
def fileinfo(sender, **kwargs):
    assets = {}
    config = kwargs["config"]["extensions"]["fileinfo"]

    for root, dirs, files in os.walk(config["directory"]):
        files = [f for f in files if not f[0] == '.' and any(f.endswith(x) for x in config["filetypes"])]
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for fn in files:
            path = os.path.join(root, fn)
            file_type = os.path.splitext(path)[1].replace(os.path.extsep, "")
            mtime = os.path.getmtime(path)
            size = os.stat(path).st_size # in bytes
            assets[path] = {
                "path": path.replace(config["webroot"], ""),
                "name": fn,
                "size": size,
                "type": file_type,
                "mtime": mtime
            }
    return assets 

