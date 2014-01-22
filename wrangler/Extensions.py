import pprint 

class Map(object):
    def __init__(self, webroot="/"):
        self.webroot = webroot
        return None

    def process_item(self, item):
        path = "%s%s" % (self.webroot, item.get_relative_output_path())
        title = item.data["meta"]["title"]
        description = item.data["meta"]["description"]

        return {
            "url": path,
            "title": title,
            "description": description
        }

    def filter_result(self, big_dict):
        return big_dict

    def build(self, items, print_debug=False):

        paths = []

        for key, item in items.iteritems():
            paths.append(self.process_item(item))
        
        dict_add = lambda x, y={}, index=None: dict_add(x[:-1], y).setdefault(x[-1], {"meta":paths[index]} if index != None else {} ) if(x) else y
        base_dict = {}

        ls = [(index, item["url"].split("/")) for index, item in enumerate(paths)]
        map(lambda x: dict_add(x[1], base_dict, x[0]), ls)

        res = self.filter_result(base_dict[""])

        if print_debug:
            pp = pprint.PrettyPrinter(depth=8)
            pp.pprint(res)

        return res

class Hook(object):
    def __init__(self, config, files, renderer):
        self.config = config
        self.files = files
        self.renderer = renderer
        return None

    def process(self, items):
        return None


""" 
EXAMPLE HOOKS

import wrangler.Extensions as extensions

class SiteMap(extensions.Map):
    def process_item(self, item):
        path = "%s%s" % (self.webroot, item.get_relative_output_path())
        title = item.data["meta"]["title"]
        description = item.data["meta"]["description"]

        return {
            "show_in_nav": item.show_in_navigation(),
            "show_in_quicklinks": item.show_in_quicklinks(),
            "weight": item.get_weight(),
            "id": item.id,
            "url": path,
            "title": title,
            "description": description
        }


class BeforeRender(extensions.Hook):
    def process(self, items):
        print "Generating sitemap..."
        self.config["site_vars"]["sitemap"] = SiteMap().build(items, True)
        return None


class AfterRender(extensions.Hook):
    def process(self, items):
        print "Done"
"""