import os
import sys
import defaults
import json
import errno


class NewProject(object):
    config_path = "wrangler.json"
    directories = ["content", "templates", "var", "www"]
    default_files = [
            {
                "path": "content/index.yaml",
                "content": defaults.yaml
            },
            {
                "path": "templates/template.j2",
                "content": defaults.template
            }
        ]

    def __init__(self, path, reporter):
        self.path = path
        self.abspath = os.path.abspath(self.path)
        self.reporter = reporter

        self.reporter.log("Setting up a new project in '%s'" % (self.abspath), "green")
        
        self.create_directory_structure()
        self.create_default_files()
        self.safe_default_config()

        return None

    def ensure_path_exists(self, path):
        try:
            os.makedirs(path)
            self.reporter.log("Creating '%s'" % (path), "green")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
            else:
                self.reporter.log("Couldn't create '%s', it already exists " % (path), "red")

    def create_default_files(self):
        for f in self.default_files:
            safe = self.safe_path(f["path"])
            if not os.path.exists(safe):
                self.write_file(safe, f["content"])
                self.reporter.log("Created '%s'" % (safe), "green")
            else:
                self.reporter.log("Couldn't create '%s', it already exists " % (safe), "red")


    def create_directory_structure(self):
        for path in self.directories:
            safe = self.safe_path(path)
            self.ensure_path_exists(safe)

    def write_file(self, path, content):
        with open(path, 'w') as outfile:
            outfile.write(content)

    def safe_path(self, path):
        return os.path.join(self.abspath, path)

    def safe_default_config(self):
        config = self.safe_path(self.config_path)
        if not os.path.exists(config):
            with open(config, 'w') as outfile:
                outfile.write(json.dumps(defaults.defaults, sort_keys=True, indent=4))
                self.reporter.log("Created '%s'" % (config), "green")
        else:
            self.reporter.log("Couldn't create '%s', it already exists " % (config), "red")

