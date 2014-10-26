#!/usr/bin/python
# serve toplev csv file as http using dygraph
# toplev.py -I100 -o x.csv -v -x, ...
# interval-normalize.py x.csv > y.csv
# tl-serve.py y.csv [host [port]]

import argparse
import BaseHTTPServer

ap = argparse.ArgumentParser(usage="Serve toplev csv file as http")
ap.add_argument('csvfile', help='toplev csv file to serve', type=argparse.FileType('r'))
ap.add_argument('host', nargs='?', default="localhost", help='Hostname to bind to (default localhost)')
ap.add_argument('port', nargs='?', default="9001", type=int, help='Port to bind to (default 9001)')
args = ap.parse_args()

class TLHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def header(self, type):
        self.send_response(200)
        self.send_header('Content-Type', type)
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.header("text/html")
            self.wfile.write("""
<html><head><title>Toplev</title>
<script type="text/javascript" src="dygraph-combined.js"></script>
</head>
<body>
<div id="graph1"></div>
<script type="text/javascript">
    g = new Dygraph(document.getElementById("graph1"),
                    "data.csv",
                    {stackedGraph: 1})
</script>
</body>
</html>""")
        elif self.path == "/dygraph-combined.js":
            with open("dygraph-combined.js", "r") as f:
                self.header("text/javascript")
                self.wfile.write(f.read())
        elif self.path == "/data.csv":
            args.csvfile.seek(0)
            self.header("text/csv")
            self.wfile.write(args.csvfile.read())
        else:
            self.send_response(401)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write("%s not found" % (self.path))

httpd = BaseHTTPServer.HTTPServer((args.host, args.port), TLHandler)

print "serving at",args.host,"port",args.port,"until Ctrl-C"
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    httpd.socket.close()
