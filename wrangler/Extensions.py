import pprint 
import time 
import os
from wrangler.Core import extension


class SiteMap(object):
    def __init__(self, config, reporter, nodes):
        self.config = config
        self.reporter = reporter
        self.nodes = nodes
        self.webroot = "/"

    def get_index(self, node):
        index = node.get_child("index")
        index_data = None
        if index:
            cargo = index.get_cargo()
            if cargo:   
                index_data = cargo.get_properties()
        return index_data

    def process_node(self, node):
        data = []

        if node.tag == "dir":

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
                        try:
                            data.append({"data": key.get_cargo().get_properties(), "children": []})
                        except:
                            self.reporter.verbose("Couldn't include %s in sitemap" % (key.path), "red")
                    else:
                        if not node.parent:
                            try:
                                data.append({"data": key.get_cargo().get_properties(), "children": []})
                            except:
                                self.reporter.verbose("Couldn't include %s in sitemap" % (key.path), "red")
        return data
        
    def run(self):
        if "webroot" in self.config:
            self.webroot = self.config["webroot"]
        res = self.process_node(self.nodes.tree())
        # p = pprint.PrettyPrinter(depth=12)
        # p.pprint(res)
        return res

@extension
def sitemap(**kwargs):
    return SiteMap(kwargs["config"]["extensions"]["sitemap"], kwargs["reporter"], kwargs["nodes"]).run()


@extension
def cachebuster(**kwargs):
    return int(time.time())


@extension
def fileinfo(**kwargs):
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

