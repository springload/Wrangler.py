import SimpleHTTPServer
import SocketServer
import os
import time

class BasicServer(object):
    def __init__(self, path, reporter, port=None):
        PORT = 8000

        if port != None:
            PORT = port

        os.chdir(path) 

        try:
            reporter.log("Starting a server" , "blue")
            # Wait for the port to free up, dirty :)
            time.sleep(1)
            Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
            httpd = SocketServer.TCPServer(("", PORT), Handler)
        except KeyboardInterrupt:
            reporter.log("Closing server" , "red")
            return
        
        try:
            reporter.log("Started server at 127.0.0.1:%d" % (PORT), "green")
            httpd.serve_forever()
        
        except KeyboardInterrupt: 
            httpd.server_close()
            reporter.log("Closed server at at 127.0.0.1:%d" % (PORT), "red")

