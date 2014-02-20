import os
import yaml

cwd = os.path.dirname(os.path.abspath(__file__))
content = "defaults/index.yaml"
template = "defaults/template.j2"
config = "defaults/wrangler.yaml"

def load_defaults():
    return yaml.load(file(config_template(), 'r'))

def content_template():
    return "%s/%s" % (cwd, content)

def template_template():
    return "%s/%s" % (cwd, template)

def config_template():
    return "%s/%s" % (cwd, config)
