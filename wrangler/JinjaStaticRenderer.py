import os
import time
import markdown as md
import sys
import traceback
import glob

from docutils.core import publish_parts
from jinja2 import Environment, FileSystemLoader, meta, BaseLoader, TemplateNotFound, ChoiceLoader, Template, Markup
from SilentUndefined import SilentUndefined
from MarkdownExtension import MarkdownExtension


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

def filter_template_dir(filename):
    if filename.startswith("."):
        return False;
    return True;


class JinjaStaticRenderer():

    def __init__(self, config):
        self.config = config
        # Setup the env
        self.env = Environment(
            undefined=SilentUndefined,
            loader=FileSystemLoader(config['templates_dir']),
            extensions=[
                MarkdownExtension
            ],
            trim_blocks = True,
            lstrip_blocks = True
            )
        
        self.env.filters["markdown"] = markdown_filter
        self.env.filters['rst'] = rst_filter        
        self.template_trees = {}
        self.template_modified_times = {}
        
        var_path=os.path.dirname(self.config['compiled_templates_file'])

        if self.config["verbose"] == True:
            print "Ensure directory exists: \033[34m%s\033[0m" % (var_path)
            print "Ensure directory exists: \033[34m%s\033[0m" % (config['output_dir'])

        self.ensure_dir(var_path)
        self.ensure_dir(config['output_dir'])

        self.env.compile_templates(
            self.config['compiled_templates_file'],
            ignore_errors=False,
            filter_func=filter_template_dir 
            )

        if self.config["verbose"] == True:
            print "Loading templates from: \033[34m%s\033[0m" % (config['templates_dir'])
            print "Compile templates to .zip: \033[32m%s\033[0m" % (self.config['compiled_templates_file'])


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

            if self.config["verbose"] == True:
                print "\033[34m%s\033[0m references templates \033[32m%s\033[0m" % (template, self.template_trees[template])

        return self.template_trees[template]

    def ensure_dir(self, dir):
        try:
            os.stat(dir)
        except:
            os.makedirs(dir)


    def render(self, data_source):
        self.log_data = []

        for item in data_source:
            template = self.load_template(item.get_template())

            if (self.should_render_item(item, template)):
                item.before_render()

                if self.config["verbose"] == True:
                    print "\033[34m%s\033[37m last built at: %s\033[0m" % (item.get_file_path(), item.get_modified_time())
                self.save(self.render_template(template, item));

        self.set_last_build_time(time.time())
        self.update_log(self.log_data, self.get_last_build_time())


    def render_template(self, template, item):
        return (template.render(data=item.get_page_content(), meta=item.get_metadata()), item)


    def save(self, data):
        item=data[1]
        html=data[0]

        filename = item.get_output_path()
        file_object = open(filename, "w")
        new_directory = os.path.split(filename)[0]

        try: 
            self.ensure_dir(new_directory)
            file_object.write(html.encode('utf8'))
            self.print_stdout(item.get_file_path(), filename, item.get_template())
            item.on_save()
        except:
            print "\033[31mCouldn't write %s\033[0m" % (filename)
            traceback.print_exc()
            self.log_item_saved(item.get_file_path(), item.get_template(), 0)
            return False
        finally:
            self.log_item_saved(item.get_file_path(), item.get_template(), 1)
            return True


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


    def should_render_item(self, item, template):
        force_render = 0
        last_build_time = self.get_last_build_time()
        output_path = item.get_output_path();

        if last_build_time == 0:
            return True

        config_modified_time = self.get_config_modified_time()
        
        if last_build_time == 0 or config_modified_time >= last_build_time:
            return True

        if self.config["force"] == True:
            return True

        if output_path and not os.path.exists(output_path):
            return True
        
        if item.get_modified_time() >= last_build_time:
            return True

        template_modified_time = 0


        if template:

            referenced_templates = self.get_referenced_templates(template)
            template_modified_time = self.get_template_mtime(item.get_template())

            if template_modified_time >= last_build_time:
                return True

            ref_template_mtime = 0
            for t in referenced_templates:
                time = self.get_template_mtime(t)
                if time >= last_build_time:
                    ref_template_mtime = time
                    return True

        return False


    def print_stdout(self, original_path, new_path, template):
        print "\033[1;32mBuilding \033[0m\033[2m%s\033[0m > \033[34m%s \033[2m[%s]\033[0m" % (original_path, new_path, template)


    def update_log(self, items, last_modified_time):
        file = open(self.config['compiled_templates_log'], 'w')
        print>>file, "this_render=%s, prev_render=%s" % (time.time(), last_modified_time)

        for item in items:
            print>>file, "%s, %s, %s" % (item[0], item[2], item[1])

        if self.config["verbose"] == True:
            print "Wrote log to: \033[32m%s\033[0m" % (self.config['compiled_templates_log'])
    
    def log_item_saved(self, path, template, result):
        if not self.log_data:
            self.log_data = []
        self.log_data.append([path, template, result])

    def get_last_build_time(self):
        """
        Get the last run time. Useful for checking what stuff's changed since we
        last ran the script.
        """
        last_time = 0
        if os.path.exists(self.config['build_cache_file']):
            with open(self.config['build_cache_file'], "r") as buildFile: 
                lines = map(float, buildFile.readline().split())
                if len(lines) > 0:
                    last_time = lines[0]
        return last_time

    def get_config_modified_time(self):
        """
        Force a re-render if the config file has changed (global paths may be invalid, etc..)
        """
        mtime = 0
        if os.path.exists(self.config['config_path']):
            mtime = os.path.getmtime(self.config['config_path'])
        return mtime

    def set_last_build_time(self, update_time):
        """
        Save the last successful run time in a var
        """
        with open(self.config['build_cache_file'], "w") as buildFile:
            buildFile.write("%s" % (update_time))

    def get_global_vars(self):
        return self.config["site_vars"]

    def go(self, data):
        """
        Request some data from an endpoint/directory
        """
        self.render(data)