#!/usr/bin/python
# serve toplev csv file as http using dygraph
# toplev.py -I100 -o x.csv -v -x, ...
# tl-serve.py x.csv [host [port]]

import string
import argparse
import BaseHTTPServer
import csv
import gen_level
import re
from collections import defaultdict

ap = argparse.ArgumentParser(usage="Serve toplev csv file as http")
ap.add_argument('csvfile', help='toplev csv file to serve', type=argparse.FileType('r'))
ap.add_argument('host', nargs='?', default="localhost", help='Hostname to bind to (default localhost)')
ap.add_argument('port', nargs='?', default="9001", type=int, help='Port to bind to (default 9001)')
args = ap.parse_args()

T = string.Template

class Data:
    def __init__(self, f):
        self.times = []
        self.vals = []
        self.csv = csv.reader(f)
        self.headers = dict()
        self.levels = defaultdict(set)

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
            if name not in self.headers:
                n = gen_level.get_subplot(name)
                if not n:
                    n = str(gen_level.get_level(name))
                self.headers[name] = n
                self.levels[n].add(name)
            prevts = ts

data = Data(args.csvfile)
data.update()

class TLHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def header(self, type):
        self.send_response(200)
        self.send_header('Content-Type', type)
        self.end_headers()

    def bad(self):
        self.send_response(401)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write("%s not found" % (self.path))

    def do_GET(self):
        if self.path == "/":
            self.header("text/html")
            self.wfile.write("""
<html><head><title>Toplev</title>
<script type="text/javascript" src="dygraph-combined.js"></script>
</head>
<body>""")
            graph = ""
            for j in sorted(data.levels.keys()):
                graph += T("""
<h1>$name</h1>
<p>
<div id="lev$name"></div>
<script type="text/javascript">
    g = new Dygraph(document.getElementById("lev$name"),
                    "/$file.csv",
                    {stackedGraph: 1})
</script>
</p>
                """).substitute({"name": j, "file": j})
            self.wfile.write(graph + """
</body>
</html>""")
        elif self.path == "/dygraph-combined.js":
            with open("dygraph-combined.js", "r") as f:
                self.header("text/javascript")
                self.wfile.write(f.read())
        elif self.path.endswith(".csv"):
            l = re.sub(r"\.csv$", "", self.path[1:])
            if l not in data.levels:
                self.bad()
                return
            self.header("text/csv")
            hdr = sorted(data.levels[l])
            wr = csv.writer(self.wfile)
            wr.writerow(["Timestamp"] + hdr)
            for v, t in zip(data.vals, data.times):
                wr.writerow([t] + [v[x] if x in v else "" for x in hdr])
        else:
            self.bad()

httpd = BaseHTTPServer.HTTPServer((args.host, args.port), TLHandler)

print "serving at",args.host,"port",args.port,"until Ctrl-C"
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    httpd.socket.close()
