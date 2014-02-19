import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler
from blinker import signal


class WatchEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if not event.is_directory:
            sig = signal('watch_change')
            sig.send(event)

class Watcher(object):
    def __init__(self, wrangler):

        config = wrangler.config

        input_dir = config["input_dir"]
        templates_dir = config["templates_dir"]

        paths = [input_dir, templates_dir]
        threads = []

        try:
            observer = Observer()
            event_handler = WatchEventHandler()
            event_handler.wrangler = wrangler

            for i in paths:
                targetPath = str(i)
                observer.schedule(event_handler, targetPath, recursive=True)
                threads.append(observer)

            observer.start()

            signal_watch_init = signal('watch_init')
            signal_watch_init.send(self)

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                wrangler._reporter.log("Stopping with grace and poise", "green")
                observer.stop()
            
            observer.join()
        except:
            return None