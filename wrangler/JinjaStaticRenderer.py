import os
import markdown as md
import sys
import traceback
import glob
import Core
import utilities as util
import types

from docutils.core import publish_parts
from jinja2 import Environment, FileSystemLoader, meta, BaseLoader, TemplateNotFound, ChoiceLoader, Template, Markup
from SilentUndefined import SilentUndefined
from MarkdownExtension import MarkdownExtension
from blinker import signal

def rst_filter(s):
    return Markup(publish_parts(source=s, writer_name='html')['body'])

def markdown_filter(value):
    """
    Jinja2 markdown filter with support for extensions.
    """
    output = value
    marked = md.Markdown(
        extensions=['extra','meta','sane_lists'],
        output_format='html5',
        safe_mode=False 
        )
    out = marked.convert(output)
    return out



def load_custom_filters(path):
    classfiles = [os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(path)
        for f in files if f.endswith('Filters.py')]

    path = list(sys.path)
    sys.path.insert(0, path)

    moduleNames = []

    for f in classfiles:
        moduleNames.append(os.path.basename(f.replace(".py", "")))

    if len(moduleNames) > 0:
        try:
            map(__import__, moduleNames);
        finally:
            # restore the syspath
            sys.path[:] = path 



class JinjaStaticRenderer(Core.Renderer):

    def init(self):

        # Setup the env
        self.env = Environment(
            undefined=SilentUndefined,
            loader=FileSystemLoader(self.config['templates_dir']),
            extensions=[
                MarkdownExtension
            ],
            trim_blocks = True,
            lstrip_blocks = True
            )
        
        self.env.filters["markdown"] = markdown_filter
        self.env.filters['rst'] = rst_filter

        # Load up some custom, project specific filters
        if "lib_path" in self.config and os.path.exists(self.config["lib_path"]):
            load_custom_filters(self.config["lib_path"])
            customFilters = sys.modules["Filters"] if "Filters" in sys.modules else None


            if customFilters:
                items = [customFilters.__dict__.get(a) for a in dir(customFilters) if isinstance(customFilters.__dict__.get(a), types.FunctionType)]

                for fn in items:
                    _name = fn.__name__.lower()
                    if _name.startswith("filter_"):
                        _name = _name.replace("filter_", "")
                        self.env.filters[_name] = fn

        self.template_trees = {}
        self.template_modified_times = {}
        
        var_path = os.path.dirname(self.config['compiled_templates_file'])

        self.reporter.verbose("Ensure directory exists: \033[34m%s\033[0m" % (var_path))
        util.ensure_dir(var_path)

        self.reporter.verbose("Loading templates from: \033[34m%s\033[0m" % (self.config['templates_dir']))
        self.env.compile_templates(
            self.config['compiled_templates_file'],
            ignore_errors=False,
            filter_func=self.filter_hidden_files 
            )

        self.reporter.verbose("Compile templates to .zip: \033[32m%s\033[0m" % (self.config['compiled_templates_file']))
    
    def filter_hidden_files(self, filename):
        _name = os.path.basename(filename)
        _path = os.path.dirname(filename)

        for _segment in _path.split(os.sep):
            if _segment.startswith("."):
                return False
        if _name.startswith("."):
            return False;
        
        self.reporter.verbose("Loading template: %s" % (_name))

        return True;


    def get_template_mtime(self, template):
        """
        Request the template's mtime. If we don't have it yet, cache it.
        """
        if not template in self.template_modified_times:
            self.template_modified_times[template] = os.path.getmtime("%s/%s" % (self.config['templates_dir'], template) )
        return self.template_modified_times[template]


    def get_referenced_templates(self, template):
        """
        Request the template's Abstract Syntax Tree so we can find other template references.
        Store the reference list in a dictionary
        """

        if not template in self.template_trees:
            try: 
                ast = self.env.parse(self.env.loader.get_source(self.env, template))
                self.template_trees[template] = list(meta.find_referenced_templates(ast))
            except:
                self.template_trees[template] = list()

            self.reporter.verbose("\033[34m%s\033[0m references templates \033[32m%s\033[0m" % (template, self.template_trees[template]))

        return self.template_trees[template]


    def render(self, item):
        template_name = item.get_template()
        template = self.load_template(template_name)

        if template and (self.should_render_item(item, template_name)):
            sig = signal("wranglerRenderItem")
            sig.send('item', item=item, template_name=template_name)
            return (template.render(data=item.get_content(), meta=item.get_metadata(), site=self.config["site_vars"]), item)

        return (False, item)


    def load_template(self, template_name):
        template_object = False
        try:
            template_object = self.env.get_template(template_name)
        except:
            print "\033[1;91mCouldn't parse `%s`. Check the template for errors \033[0;37m" % (template)
            
            if self.config["verbose"] == True:
                traceback.print_exc()
            print "\033[0m"
            return False
        finally:
            return template_object


    def should_render_item(self, item, template_name):
        force_render = 0
        last_build_time = self.reporter.get_last_build_time()
        output_path = item.get_output_path()

        if last_build_time == 0:
            return True

        config_modified_time = self.reporter.get_config_modified_time()
        
        if last_build_time == 0 or config_modified_time >= last_build_time:
            return True

        if self.config["force"] == True:
            return True

        if output_path and not os.path.exists(output_path):
            return True
        
        if item.get_modified_time() >= last_build_time:
            return True

        template_modified_time = 0

        if template_name:

            referenced_templates = self.get_referenced_templates(template_name)
            template_modified_time = self.get_template_mtime(template_name)
            
            if template_modified_time >= last_build_time:
                return True

            ref_template_mtime = 0

            for t in referenced_templates:
                time = self.get_template_mtime(t)
                if time >= last_build_time:
                    ref_template_mtime = time
                    return True

        return False
