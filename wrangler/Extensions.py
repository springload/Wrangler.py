import pprint 

class SiteMap(object):
    def __init__(self, webroot="/"):
        self.webroot = webroot
        return None

    def process_node(self, node):
        data = []
        for key in node.children:
            if key.tag == "dir":
                index = key.get_child("index")
                index_data = None
                if index:
                    index_data = index.get_cargo().get_properties()

                data.append({"data": index_data, "children": self.process_node(key)})
                # data[key.name]["children"] = )
            else:
                if not key.is_index:
                    data.append({"data": key.get_cargo().get_properties(), "children": {}})
        return data

        
    def build(self, root_node, print_debug=False):
        res = self.process_node(root_node)
        # pp = pprint.PrettyPrinter(depth=8)
        # pp.pprint(res)
        return res


class Hook(object):
    def __init__(self, config, renderer):
        self.config = config
        self.renderer = renderer
        return None

    def process(self, items):
        return None
