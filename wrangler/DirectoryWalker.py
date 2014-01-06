import os
import subprocess
import shelve 
import sys 

# Takes a directory and transforms the matching elements into the matching class.
class DirectoryWalker():
    def __init__(self, params):
        self.item_class = params['item_class']
        self.input_dir = params['input_dir']
        self.ignore_files = params['ignore_files']
        self.data_format = params['data_format']
        self.nocache = params['nocache']

    def fetch(self):
        items = []

        # Not supported in python 2.6 hmmm
        # if sys.version_info > (2,7,0):
            # files = subprocess.check_output(["find", self.input_dir, "-name", "*.%s" % (self.data_format)], stderr=subprocess.STDOUT)
        # else:
        p = subprocess.Popen(["find", self.input_dir, "-name", "*.%s" % (self.data_format)], stdout=subprocess.PIPE)

        out, err = p.communicate()
        files = out.split("\n")

        shelf = shelve.open("test_shelf.db") 

        for f in files: 
            if f != '':

                # If the key doesn't exist on the shelf, or the mtime is different, re-cache the object
                if (not shelf.has_key(f)) or (shelf[f].mtime < os.path.getmtime(f)) or (self.nocache):
                    item = self.item_class(f, self.input_dir,  "", self.data_format)
                    shelf[f] = item

                    print "\033[1;35mCaching \033[0m\033[2m%s\033[0m" % (f)

                items.append(shelf[f])

        try:
            shelf.sync()
        finally:
            shelf.close()

        return items