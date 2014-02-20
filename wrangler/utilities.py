import os
import re
from unicodedata import normalize

"""
---------------------------------------------------------------------------------------------------
Ensure directory exists
---------------------------------------------------------------------------------------------------
"""

def ensure_dir(dir):
    try:
        os.stat(dir)
    except:
        os.makedirs(dir)


"""
---------------------------------------------------------------------------------------------------
Slugify a filename/path
---------------------------------------------------------------------------------------------------
"""
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')

def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

# Takes a path, slugifies the filename, returns it.

def clean_path(filename, ext):
    path = os.path.dirname(filename)
    basename = os.path.basename(filename)
    clean_filename = slugify(u"%s" % (basename))
    return os.path.join(path,clean_filename + os.extsep + ext)