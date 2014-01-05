import os
import subprocess
import shelve 

# Takes a directory and transforms the matching elements into the matching class.
class DirectoryWalker():
    def __init__(self, params):
        self.item_class = params['item_class']
        self.input_dir = params['input_dir']
        self.ignore_files = params['ignore_files']
        self.data_format = params['data_format']

    def fetch(self):
        items = []

        files = subprocess.check_output(["find", self.input_dir, "-name", "*.yaml"], stderr=subprocess.STDOUT)
        files = files.split("\n")

        shelf = shelve.open("test_shelf.db") 

        for f in files: 
            if f != '':
                # If the key doesn't exist on the shelf, or the mtime is different, re-cache the object
                if not shelf.has_key(f) or (shelf.has_key(f) and shelf[f].mtime < os.path.getmtime(f)):
                    item = self.item_class(f, self.input_dir, "", self.data_format)
                    shelf[f] = item

                items.append(shelf[f])

        try:
            shelf.sync()
        finally:
            shelf.close()

        return items