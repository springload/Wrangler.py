import os
import sys
import argparse
import json
import importlib
import JinjaStaticRenderer as renderer
import Reader as Reader
import Core as Core
import Extensions as Extensions
import inspect

class Wrangler():

    defaults = {
        "generator_config": {
            "build_cache_file": "var/build.cache",
            "default_template": "base.j2",
            "templates_dir": "templates",
            "compiled_templates_file": "var/jinja",
            "compiled_templates_log": "var/jinja.log",
            "output_file_extension": "html",
            "output_dir": "www",
            "input_dir": "site",
            "data_format": "json",
            "ignore": [".", "_"],
            "site_vars":"site_vars",
            "verbose": "false",
            "force": "false",
            "nocache": "false",
            "item_class": "Page",
            "lib_path": "site/lib",
            "extensions": {
                "SiteMap": {
                    "options": {
                        "webroot":"/"
                    }
                },
                "CacheBuster": {
                    "options": {}
                },
                "FileInfo": {
                    "options": {
                        "directory": "www/assets",
                        "filetypes": ["css", "pdf"],
                        "webroot": "www"
                    }
                },
                "MooExtension": {
                    "options": {}
                }
            }
        },
        "site_vars": {
            "paths": {
                "css": "assets/css",
                "js": "assets/js",
                "assets": "assets",
                "images": "assets/images",
                "webroot": "www",
                "app": "app",
                "content": "content"
            }
        }
    }

    # Default config just loads the YAML config file
    config = {
        'config_path':'wrangler.json',
    }

    def __init__(self):
        return None

    def parse_args(self, args=None):
        d = '\033[32mProcess recursive directories of JSON files through Jinja2 templates. \033[0m'
        parser = argparse.ArgumentParser(description=d)
        parser.add_argument('input_dir',
                            help='\033[34mInput directory such as `site/content`\033[0m')
        parser.add_argument('output_dir',
                            help='\033[34mOutput directory such as `www`\033[0m')
        parser.add_argument("-t", "--templates_dir",
                            help='\033[34mTemplate directory such as `templates`\033[0m')
        parser.add_argument("-c", "--config",
                            help='\033[34mPath to `config.json`\033[0m')
        parser.add_argument("-o", "--output_file_extension",
                            help='\033[34mType of files to output such as `html`\033[0m')
        parser.add_argument("-d", "--data_format",
                            help='\033[34mType of files to match in input_dir, such as `json`\033[0m')
        parser.add_argument("-v", "--verbose", action="store_true",
                            help='\033[34mPrint all the plumbing\033[0m')
        parser.add_argument("-f", "--force", action="store_true",
                            help='\033[34mSmash out all the templates regardless of mtime\033[0m')
        parser.add_argument("-n", "--nocache", action="store_true",
                            help='\033[34mTurn off data persistence\033[0m')
        return parser.parse_args(args)


    def update_config(self, args):
        # If a config file is specified, load all config from there instead
        if (args.__dict__["config"] != None):
            self.config['config_path'] = args.__dict__["config"]


        self.config.update( self.defaults["generator_config"] )

        if os.path.exists( self.config['config_path'] ):
            userConfig = json.load( file(self.config['config_path']) )
            self.config.update( userConfig["generator_config"] )
        # else: 
            # userConfig = self.defaults

        # Apply settings from the config file (if present)
        # self.config.update( userConfig["generator_config"] )

        # Apply command line flags if set, ignore Nones.
        self.config.update((k, v) for k, v in args.__dict__.iteritems() if v is not None)
        
        # The site vars object is mapped to an item in the json object
        self.config["site_vars"] = userConfig[userConfig["generator_config"]["site_vars"]]



    def main(self, args=None):
        args = self.parse_args(args)

        self.update_config(args)

        if "lib_path" in self.config:
            self.load_classes(self.config["lib_path"])

        self._reporter = Core.Reporter(self.config)
        self._reader = Reader.Reader(self.config)
        self._writer = Core.Writer(self.config["output_dir"], self.config["output_file_extension"], self._reporter)
        self._renderer = renderer.JinjaStaticRenderer(self.config, self._reporter, self._writer)

        self._reporter.log("Digesting \"%s\" files from \"%s\"" % (self.config["data_format"], self.config["input_dir"]), "blue")
        self.graph = self._reader.fetch()


        # Set output paths before trying to render anything.
        # Two loops not so efficient... hmmm
        def set_output(node):
            if node.tag == 'file':
                cargo = node.get_cargo()
                if cargo:
                    cargo.set_output_path(self._writer.generate_output_path(cargo.relpath()))
            else:
                for child in node.children:
                    set_output(child)

        set_output(self.graph.tree())


        if "WranglerHooks" in sys.modules and hasattr(sys.modules["WranglerHooks"], "BeforeRender"):
            hook = sys.modules["WranglerHooks"].BeforeRender(self.config, self._renderer)
            hook.process(self.graph)

        self.process_extensions()
    

        rendered = 0

        for key, node in self.graph.all().items():
            if node.tag == 'file':
                # Leaky boat.
                cargo = node.get_cargo()
                if cargo:
                    cargo.set_parents(node.get_parents())
                    cargo.set_children(node.get_child_pages())
                    cargo.set_siblings(node.get_siblings())
                    cargo.set_parents_siblings(node.get_parents_siblings())
                    
                    _rel = cargo.get_related()

                    if _rel != None:
                        arr = self.graph.all()
                        related = []
                        for item in _rel:
                            _item = arr.get(item)
                            if _item:
                                related.append(_item)
                        
                        cargo.set_related_nodes(related)

                    if self._writer.save(self._renderer.render(cargo)):
                        rendered += 1

                    cargo.cleanup()
                    del cargo
    

        if "WranglerHooks" in sys.modules and hasattr(sys.modules["WranglerHooks"], "AfterRender"):
            hook = sys.modules["WranglerHooks"].AfterRender(self.config, self._renderer)
            hook.process(self.graph)
        
        if rendered > 0:
            self._reporter.log("Built %s of %s pages in \"%s\" directory " % (rendered, len(self.graph.all()) ,self.config["output_dir"]), "green")
            self._reporter.set_last_build_time()
        else:
             self._reporter.log("Hmm... nothing's changed in \"%s\" or \"%s\" since last time.\nIf you've removed pages, or included a template dynamically, try --force" % (self.config["input_dir"], self.config["templates_dir"]), "red")

    def load_classes(self, views): 
        classfiles = [os.path.join(dirpath, f)
            for dirpath, dirnames, files in os.walk(views)
            for f in files if f.endswith('.py')]

        path = list(sys.path)
        sys.path.insert(0, views)

        moduleNames = []


        for f in classfiles:
            moduleNames.append(os.path.basename(f.replace(".py", "")))

        if len(moduleNames) > 0:
            try:
                map(__import__, moduleNames);
            finally:
                # restore the syspath
                sys.path[:] = path 


    def process_extensions(self):
        """
        Load extensions from the core and import any from the site/lib directory too
        """
        extension_classes = inspect.getmembers(sys.modules["wrangler.Extensions"], inspect.isclass)

        if "lib_path" in self.config:
            extension_classes = extension_classes + inspect.getmembers(sys.modules["Extensions"], inspect.isclass)

        if extension_classes:
            for extension_name, extension_config in self.config["extensions"].items():
                # try:
                    ext = [(name, obj) for (name, obj) in extension_classes if name == extension_name]
                    if ext[0]:
                        extension = ext[0][1](extension_config, self.graph)
                        self._reporter.verbose("Running extension %s > site.%s" % (ext[0][0], ext[0][0].lower()))
                        self.config["site_vars"][extension_name.lower()] = extension.run()
                # except:
                    # self._reporter.log("Couldn't load extension %s" % (extension_name), "red")


def start():
    sys.exit(Wrangler().main())

if __name__ == '__main__':
    start()
