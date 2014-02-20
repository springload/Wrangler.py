import os
import sys
import argparse
import json
import yaml
import importlib
import inspect
from blinker import signal

import Reader as Reader
import JinjaStaticRenderer as renderer
import Core as Core
import Extensions as Extensions
import defaults as defaults
import NewProject as generate
import BasicServer as serve
import Watcher as watch
import messages as messages

class Wrangler(object):

    defaults = defaults.load_defaults()

    # Default config just loads the YAML config file
    config = {
        "wrangler": {
            "verbose": False,
            "force": False,
            "nocache": False,
            "input_dir": False,
            "output_dir": False
        },
        "site": {},
        "extensions": {}
    }

    # User config path 
    config_path = 'wrangler.yaml'
    extension_results = {}

    # Hmm it turns out there's not going to be any global options at all, the whole app
    # works best as a series of subcommands with very independent options.
    def parse_args(self, args=None):
        d = '\033[32mProcess recursive directories of JSON files through Jinja2 templates. \033[0m'
        parser = argparse.ArgumentParser(description=d)
        
        subparsers = parser.add_subparsers(dest="subparser", help='sub-command help')
        
        # ---------------------------------------------------------------------
        # wrangler create .
        # ---------------------------------------------------------------------
        # Creating a new project/scaffolding
         
        parser_generate = subparsers.add_parser('create', help='create help')
        parser_generate.add_argument('path', type=str, help='wrangler create path')
       

        # ---------------------------------------------------------------------
        # wrangler serve www
        # ---------------------------------------------------------------------
        # Serving up content on a specified URL
        
        parser_serve = subparsers.add_parser('serve', help='server help')
        parser_serve.add_argument('path', type=str, help='wrangler server path')
        parser_serve.add_argument("-p", "--port",
                            help='\033[34mThe port number, eg `8000`\033[0m', type=int)

        # ---------------------------------------------------------------------
        # wrangler build [i] [o]
        # ---------------------------------------------------------------------
        # Running the build command
        
        parser_build = subparsers.add_parser('build', help='build help')
        parser_build.add_argument('input_dir',
                            help='\033[34mInput directory such as `content`\033[0m')
        parser_build.add_argument('output_dir',
                            help='\033[34mOutput directory such as `www`\033[0m')
        parser_build.add_argument("-t", "--templates_dir",
                            help='\033[34mTemplate directory such as `templates`\033[0m')
        parser_build.add_argument("-c", "--config",
                            help='\033[34mPath to `wrangler.json`\033[0m')
        parser_build.add_argument("-o", "--output_file_extension",
                            help='\033[34mType of files to output such as `html`\033[0m')
        parser_build.add_argument("-d", "--data_format",
                            help='\033[34mType of files to match in input_dir, such as `json`\033[0m')
        parser_build.add_argument("-v", "--verbose", action="store_true",
                            help='\033[34mPrint all the plumbing\033[0m')
        parser_build.add_argument("-f", "--force", action="store_true",
                            help='\033[34mSmash out all the templates regardless of mtime\033[0m')
        parser_build.add_argument("-n", "--nocache", action="store_true",
                            help='\033[34mTurn off data persistence\033[0m')


        # ---------------------------------------------------------------------
        # wrangler watch [i] [o]
        # ---------------------------------------------------------------------
        # Same config as build..
        
        parser_watch = subparsers.add_parser('watch', help='build help')
        parser_watch.add_argument('input_dir',
                            help='\033[34mInput directory such as `content`\033[0m')
        parser_watch.add_argument('output_dir',
                            help='\033[34mOutput directory such as `www`\033[0m')
        parser_watch.add_argument("-f", "--force", action="store_true",
                            help='\033[34mSmash out all the templates regardless of mtime\033[0m')
        parser_watch.add_argument("-n", "--nocache", action="store_true",
                            help='\033[34mTurn off data persistence\033[0m')
        parser_watch.add_argument("-v", "--verbose", action="store_true",
                            help='\033[34mPrint all the plumbing\033[0m')
        
        parser_clean = subparsers.add_parser('clean', help='clean help')
        return parser.parse_args(args)


    def update_config(self, args):
        userConfig = None

        # Load the defaults
        self.config.update( self.defaults )

        # Check for custom config in the arguments
        if (hasattr(args, "config")):
            if args.config != None:
                self.config_path = args.config

        # Load custom config if it exists
        _path = u"%s" % (self.config_path)

        if os.path.exists( _path ):
            userConfig = yaml.load( file(_path) )
            self.config.update( userConfig )

        # # Apply command line flags if set, ignore Nones.
        self.config["wrangler"].update((k, v) for k, v in args.__dict__.iteritems() if v is not None)
        
        # If there's a library path, load all the modules
        if "lib_path" in self.config["wrangler"]:
            self.load_classes(self.config["wrangler"]["lib_path"])


    def main(self, args=None):
        args = self.parse_args(args)

        self.update_config(args)

        # Reporter only really needs to check the verbosity level
        self._reporter = Core.Reporter(self.config, self.config_path)

        if "subparser" in args:
            
            if args.subparser == "create":
                generate.NewProject(args.path, self._reporter)
                exit()
            
            if args.subparser == "serve":
                port = None
                if args.port:
                    port = args.port 
                serve.BasicServer(args.path, self._reporter, port)
            
            if args.subparser == "build":
                self.render()

            if args.subparser == "watch":

                watch_init = signal('watch_init')
                watch_change = signal('watch_change')
                
                watch_init.connect(self.on_watch_ready)
                watch_change.connect(self.on_watch_change)
                watcher = watch.Watcher(self.config["wrangler"]["input_dir"], self.config["wrangler"]["templates_dir"])

            if args.subparser == "clean":
                # self.update_config(args)
                files = [self.config["wrangler"]["compiled_templates_file"], self.config["wrangler"]["build_cache_file"]]
                
                for f in files:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                            self._reporter.log("Cleaning up: %s" % (f), "blue")
                        except:
                            self._reporter.log("Couldn't access: %s" % (f), "red")
                self._reporter.log("Done", "green")
                exit()

        else:
            return None

    def on_watch_ready(self, sender):
        conf = self.config["wrangler"]
        self._reporter.log(messages.watch_start % (conf['input_dir'], conf['templates_dir']), "blue")

    def on_watch_change(self, sender):
        self._reporter.log(messages.watch_change % (sender.src_path), "green")
        self.render()

    def render(self):
        conf = self.config["wrangler"]
        self._reader = Reader.Reader(self.config)
        self._writer = Core.Writer(conf["output_dir"], conf["output_file_extension"], self._reporter)
        self._renderer = renderer.JinjaStaticRenderer(self.config, self._reporter, self._writer)
        self._reporter.log(messages.start_render % (conf["data_formats"], conf["input_dir"]), "blue")
        self.graph = self._reader.fetch()

        total_nodes = 0

        for key, node in self.graph.all().items():
            if node.tag == 'file':
                cargo = node.get_cargo()     
                if cargo:
                    cargo.set_output_path(self._writer.generate_output_path(cargo.relpath()))
                total_nodes += 1

        

        before = signal('wranglerBeforeRender')
        result = before.send('wrangler',
                    config=self.config,
                    renderer=self._renderer,
                    reporter=self._reporter,
                    nodes=self.graph)

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

                    # The important bit that does the saving and the rendering
                    if self._writer.save(
                        self._renderer.render(
                            cargo,
                            meta = cargo.get_metadata(),
                            data = cargo.get_content(),
                            site = self.config["site"],
                            extensions = self.extension_results
                            )
                        ):
                        rendered += 1
                    cargo.cleanup()
                    del cargo
    

        after = signal('wranglerAfterRender')
        final_result = after.send('wrangler',
                    config=self.config,
                    renderer=self._renderer,
                    reporter=self._reporter,
                    nodes=self.graph)
        
        if rendered > 0:
            self._reporter.log(messages.built_n_of_n % (rendered, total_nodes, conf["output_dir"]), "green")
            self._reporter.set_last_build_time()
        else:
             self._reporter.log(messages.nochange % (conf["input_dir"], conf["templates_dir"]), "red")


    def load_classes(self, views):
        """
        Pull in files from the lib directory
        """
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
        sig = signal("wranglerExtension")
        results = sig.send('wrangler')

        # Results returns a list of tuples.
        # First one will be the decorator, second will be the fn
        for result in results:
            responder = result[1]
            self.extension_results[responder.__name__] = responder(config=self.config, reporter=self._reporter, nodes=self.graph)

        # print self.extension_results

def start():
    sys.exit(Wrangler().main())

if __name__ == '__main__':
    start()
