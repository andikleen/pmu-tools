#!/usr/bin/python
# serve toplev csv file as http using dygraph
# toplev.py -I100 -o x.csv -v -x, ...
# tl-serve.py x.csv [host [port]]

import string
import argparse
import BaseHTTPServer
import csv

ap = argparse.ArgumentParser(usage="Serve toplev csv file as http")
ap.add_argument('csvfile', help='toplev csv file to serve', type=argparse.FileType('r'))
ap.add_argument('host', nargs='?', default="localhost", help='Hostname to bind to (default localhost)')
ap.add_argument('port', nargs='?', default="9001", type=int, help='Port to bind to (default 9001)')
args = ap.parse_args()

T = string.template

class Data:
    def __init__(self, f):
        self.times = []
        self.vals = []
        self.csv = csv.reader(f)
        self.headers = set()

    def update(self):
        prevts = None
        val = dict()
        for r in self.csv:
            ts, name, pct, state, helptxt = r[0], r[1], r[2], r[3], r[4]
            if prevts and ts != prevts:
                self.times.append(prevts)
                self.vals.append(val)
                val = dict()
            val[name] = pct
            self.headers.add(name)
            prevts = ts

data = Data(args.csvfile)
data.update()

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
<body>""")
            graph = ""
            graph += T("""
<div id="$name"></div>
<script type="text/javascript">
    g = new Dygraph(document.getElementById("$name"),
                    "/$file.csv",
                    {stackedGraph: 1})
</script>
            """).substitute({"name": "graph1", "file": "data"})
            self.wfile.write(graph + """
</body>
</html>""")
        elif self.path == "/dygraph-combined.js":
            with open("dygraph-combined.js", "r") as f:
                self.header("text/javascript")
                self.wfile.write(f.read())
        elif self.path == "/data.csv":
            self.header("text/csv")
            hdr = sorted(data.headers)
            wr = csv.writer(self.wfile)
            wr.writerow(["Timestamp"] + hdr)
            for v, t in zip(data.vals, data.times):
                wr.writerow([t] + [v[x] if x in v else "" for x in hdr])
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
