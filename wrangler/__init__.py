import os
import sys
import argparse
import json
from JinjaStaticRenderer import JinjaStaticRenderer

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
        "site_vars":"env",
        "verbose": "false",
        "force": "false"
    },
    "env": {
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
    'config_path':'config.json'
}


# Generic little app bootstrapper thingy
class App():
    def __init__(self, config):
        self.config = config

    def parse_args(self, args=None):
        d = '\033[32mProcess recursive directories of JSON files through Jinja2 templates. \033[0m'
        parser = argparse.ArgumentParser(description=d)
        parser.add_argument('input_dir',
                            help='\033[34mInput directory such as `site/content`\033[0m')
        parser.add_argument('output_dir',
                            help='\033[34mOutput directory such as `www`\033[0m')
        parser.add_argument("-t", "--templates",
                            help='\033[34mTemplate directory such as `templates`\033[0m')
        parser.add_argument("-c", "--config",
                            help='\033[34mPath to `config.json`\033[0m')
        parser.add_argument("-o", "--output_file_extension",
                            help='\033[34mType of files to output such as `html`\033[0m')
        parser.add_argument("-i", "--input_file_extension",
                            help='\033[34mType of files to match in input_dir, such as `json`\033[0m')
        parser.add_argument("-v", "--verbose", action="store_true",
                            help='\033[34mPrint all the plumbing\033[0m')
        parser.add_argument("-f", "--force", action="store_true",
                            help='\033[34mSmash out all the templates regardless of mtime\033[0m')

        return parser.parse_args(args)

    def main(self, args=None):
        args = self.parse_args(args)

        # If a config file is specified, load all config from there instead
        if (args.__dict__["config"] != None):
            config['config_path'] = args["config"]

        if os.path.exists( config['config_path'] ):
            userConfig = json.load( file(config['config_path']) )
            config.update( userConfig["generator_config"] )
        else: 
            userConfig = defaults

        # Apply settings from the config file (if present)
        config.update( userConfig["generator_config"] )

        # Apply command line flags if set, ignore Nones.
        config.update((k, v) for k, v in args.__dict__.iteritems() if v is not None)
    
        # The site vars object is mapped to an item in the json object
        config["site_vars"] = userConfig[userConfig["generator_config"]["site_vars"]]

        renderer = JinjaStaticRenderer(self.config)
        renderer.go()


# Do the thing! 
def start():
    sys.exit(App(config).main())

if __name__ == '__main__':    
    start()

