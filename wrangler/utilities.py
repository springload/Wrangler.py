import os

def ensure_dir(dir):
    try:
        os.stat(dir)
    except:
        os.makedirs(dir)
