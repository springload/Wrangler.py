import os
import sys
import defaults
import yaml
import errno
import shutil
import messages as messages


class NewProject(object):
    
    config_path = "wrangler.yaml"
    directories = ["content", "templates", "var", "www", "lib"]
    default_files = [
            {
                "path": "content/index.md",
                "content": defaults.content_template()
            },
            {
                "path": "templates/template.j2",
                "content": defaults.template_template()
            },
            {
                "path": "wrangler.yaml",
                "content": defaults.config_template()
            },
            {
                "path": "lib/examples.py",
                "content": defaults.lib_template()
            }
        ]

    def __init__(self, path, reporter):
        self.path = path
        self.abspath = os.path.abspath(self.path)
        self.reporter = reporter
        self.reporter.log(messages.create_project % (self.abspath), "green")
        self.create_directory_structure()
        self.create_default_files()
        return None

    def ensure_path_exists(self, path):
        try:
            os.makedirs(path)
            self.reporter.log("Creating '%s'" % (path), "green")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
            else:
                self.reporter.log(messages.already_exists % (path), "red")

    def create_default_files(self):
        for f in self.default_files:
            safe = self.safe_path(f["path"])
            if not os.path.exists(safe):
                shutil.copy2(f["content"], f["path"])
                self.reporter.log(messages.file_created % (safe), "green")
            else:
                self.reporter.log(messages.already_exists % (safe), "red")


    def create_directory_structure(self):
        for path in self.directories:
            safe = self.safe_path(path)
            self.ensure_path_exists(safe)

    def write_file(self, path, content):
        with open(path, 'w') as outfile:
            outfile.write(content)

    def safe_path(self, path):
        return os.path.join(self.abspath, path)

