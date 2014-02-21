import os
import yaml

cwd = os.path.dirname(os.path.abspath(__file__))
content = "defaults/index.md"
template = "defaults/template.j2"
config = "defaults/wrangler.yaml"
lib = "defaults/examples.py"

def load_defaults():
    return yaml.load(file(config_template(), 'r'))

def content_template():
    return "%s/%s" % (cwd, content)

def template_template():
    return "%s/%s" % (cwd, template)

def config_template():
    return "%s/%s" % (cwd, config)

def lib_template():
    return "%s/%s" % (cwd, lib)