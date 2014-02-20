# One place to edit all the system messages seems like a good idea!

create_project = "Setting up a new project in '%s'"

nochange = """\
Hmm... nothing's changed in \"%s\" or \"%s\" since last time.
If you've removed pages, or included a template dynamically, try --force\
"""

built_n_of_n = "Built %s of %s pages in \"%s\" directory"
	
start_render = "Digesting \"%s\" files"
render_success = "\033[1;32mBuilding \033[0m\033[2m%s\033[0m > \033[34m%s \033[2m[%s]\033[0m"

watch_start = "Listening for changes in '%s', '%s'"
watch_change = "Change detected in %s"


parser_error = """\
%s does not parse %s, expected .%s. Check the 'data_format' in wrangler.yaml\
"""

parser_decode_error = "\033[31mCouldn't load %s as %s\033[0m"

file_created = "Created '%s'"
file_decode_error = "\033[31mTrouble reading %s\033[0m"
file_write_error = "\033[31mCouldn't write %s\033[0m"
already_exists = "Couldn't create '%s', it already exists"

write_log = "Wrote log to: \033[32m%s\033[0m"

unpickle_error = """\
Couldn't load %s from the cache. Try running `wrangler clean`\
then `wrangler build`, or build again with the `--nocache` option.
"""