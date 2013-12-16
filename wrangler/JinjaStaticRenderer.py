import os
import time
import markdown as md
import sys
import traceback

from docutils.core import publish_parts
from Page import Page
from DirectoryWalker import DirectoryWalker
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

class JinjaStaticRenderer():
    """
    In theory this should probably sub-class a generic renderer
    """ 
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
        self.template_modified_times = {}
        self.template_trees = {}

        # self.template_modified_times = self.get_template_mtimes(config)
        # self.template_trees = self.load_abstract_syntax_trees()

        var_path=os.path.dirname(self.config['compiled_templates_file'])


        if self.config["verbose"] == True:
            print "Ensure directory exists: \033[34m%s\033[0m" % (var_path)
            print "Ensure directory exists: \033[34m%s\033[0m" % (config['output_dir'])

        self.ensure_dir(var_path)
        self.ensure_dir(config['output_dir'])

        self.env.compile_templates(
            self.config['compiled_templates_file'],
            ignore_errors=False
            )

        if self.config["verbose"] == True:
            print "Loading templates from: \033[34m%s\033[0m" % (config['templates_dir'])
            print "Compile templates to .zip: \033[32m%s\033[0m" % (self.config['compiled_templates_file'])

        # This lets us have bespoke template pages in the input dir too. 
        # self.env.loader = FileSystemLoader(self.config['templates_dir'])

    # def get_template_mtimes(self, config):
    #     """
    #     Get the template modified times to save disk lookups for each item.
    #     """
    #     template_files = self.env.list_templates()

    #     mod_times = {}

    #     for path in template_files:
    #         file_name = path
    #         file_mtime = os.path.getmtime("%s/%s" % (self.config['templates_dir'], file_name)  )
    #         mod_times[file_name] = file_mtime

    #     return mod_times

    # def load_abstract_syntax_trees(self):
    #     """
    #     Cache up the ASTs so we don't have to hit the disk for each page.
    #     So far, this is probably the single biggest speed boost.
    #     """
    #     template_files = self.env.list_templates()
    #     asts = {}
    #     for template in template_files:
    #         asts[template] = self.env.parse(self.env.loader.get_source(self.env, template))

    #     return asts

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

    def get_global_vars(self):
        return self.config['site_vars']

    def ensure_dir(self, dir):
        try:
            os.stat(dir)
        except:
            os.mkdir(dir)

    def render(self, data_source):
        """
        Kick off the rendering loop. If no cache found, or config has been modified, 
        force everything to be re-rendered.
        """
        force_render = 0
        last_build_time = self.get_last_build_time()
        config_modified_time = self.get_config_modified_time()
        output_dir = self.config['output_dir']
        output_file_extension = self.config['output_file_extension']
        templates_dir = self.config['templates_dir']
        default_template = self.config['default_template']
        
        if last_build_time == 0 or config_modified_time >= last_build_time:
            force_render = 1

        if self.config["force"] == True:
            force_render = 1

        rendered_files = []
        
        for item in data_source:
            item.set_output_path(output_dir, output_file_extension)
            rendered_file = self.render_item(last_build_time, self.env, force_render, templates_dir, default_template, item)
            rendered_files.append(rendered_file)



        self.set_last_build_time(time.time())
        self.update_log(rendered_files, last_build_time)


    def render_item(self, last_build_time, env, force_render, templates_dir, default_template, page):
        new_file_path = page.get_output_path()
        new_directory = os.path.split(new_file_path)[0]
        
        # Force a render if the output file doesn't exist
        if not os.path.exists(new_file_path) or page.get_modified_time() >= last_build_time:
            force_render = 1

        template_modified_time = 0
        template = page.get_template()
        
        if template == 0:
            template = default_template

        try:
            template_object = env.get_template(template)
        except:
            print "\033[1;91mCouldn't parse `%s`. Check the template for errors \033[0;37m" % (template)
            
            if self.config["verbose"] == True:
                traceback.print_exc()
            print "\033[0m"
            return [new_file_path, 0, template]

        referenced_templates = self.get_referenced_templates(template)
        template_modified_time = self.get_template_mtime(template)

        if template_modified_time >= last_build_time:
            force_render = 1

        ref_template_mtime = 0
        for t in referenced_templates:
            time = self.get_template_mtime(t)
            if time >= last_build_time:
                force_render = 1
                ref_template_mtime = time

        if self.config["verbose"] == True:
            print "\033[34m%s\033[37m last built at: %s, page mtime: %s, templ mtime: %s, ref-templates mtime: %s\033[0m" % (page.file_path, last_build_time, page.get_modified_time(), template_modified_time, ref_template_mtime)


        file_did_render = 0

        if template_object and last_build_time == 0 or force_render == 1:
            self.ensure_dir(new_directory)
            html = template_object.render(
                content=page.get_page_content(),
                site=self.get_global_vars(),
                template=page.get_page_vars()
                )
            new_file = open(new_file_path, "w")
            try: 
                new_file.write(html.encode('utf8'))
            except:
                print "\033[31mTrouble writing %s\033[0m" % (new_file_path)
                traceback.print_exc()

            self.print_stdout(page.get_file_path(), new_file_path, template)
            file_did_render = 1

        return [new_file_path, file_did_render, template]
            
    def print_stdout(self, original_path, new_path, template):
        print "\033[32mBuilding \033[0m\033[2m%s\033[0m > \033[34m%s \033[2m[%s]\033[0m" % (original_path, new_path, template)

    def update_log(self, items, last_modified_time):
        file = open(self.config['compiled_templates_log'], 'w')
        print>>file, "this_render=%s, prev_render=%s" % (time.time(), last_modified_time)

        for item in items:
            print>>file, "%s, %s, %s" % (item[0], item[2], item[1])

        if self.config["verbose"] == True:
            print "Wrote log to: \033[32m%s\033[0m" % (self.config['compiled_templates_log'])

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

    def get_data(self, source_type, params):
        """
        Future-friendly method. For when this interfaces with a swanky API.
        """
        if source_type == "directory":
            source = DirectoryWalker(params)
            return source.fetch()

    def go(self):
        """
        Request some data from an endpoint/directory
        """
        data = self.get_data(
            "directory",
            {
                'input_dir': self.config['input_dir'],
                'ignore_files': self.config['ignore'],
                'item_class': Page,
                'data_format': self.config['data_format']
            }
        )

        self.render(data)