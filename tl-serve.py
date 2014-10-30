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
import os
from collections import defaultdict

ap = argparse.ArgumentParser(usage="Serve toplev csv file as http or generate in directory")
ap.add_argument('csvfile', help='toplev csv file to serve', type=argparse.FileType('r'))
ap.add_argument('host', nargs='?', default="localhost", help='Hostname to bind to (default localhost)')
ap.add_argument('port', nargs='?', default="9001", type=int, help='Port to bind to (default 9001)')
ap.add_argument('--verbose', '-v', action='store_true', help='Display all metrics, even if below threshold')
ap.add_argument('--gen', help='Generate HTML files in specified directory')
args = ap.parse_args()

T = string.Template

# XXX
metric_levels = {
    "L1dMissLatency": "Latencies",
    "InstPerTakenBranch": "Basic Block Length",
}

metric_unit = {
    "Latencies": "Cycles",
    "Basic_Block_Length": "Insns",
    "CPU_Utilization": "CPUs"
}

class Data:
    def __init__(self, f):
        self.times = []
        self.vals = []
        self.csv = csv.reader(f)
        self.headers = dict()
        self.levels = defaultdict(set)
        self.metrics = set()

    def update(self):
        prevts = None
        val = dict()
        for r in self.csv:
            ts, name, pct, state, helptxt = r[0], r[1], r[2], r[3], r[4]
            if state == "below" and not args.verbose:
                continue
            if prevts and ts != prevts:
                self.times.append(prevts)
                self.vals.append(val)
                val = dict()
            val[name] = pct
            if name not in self.headers:
                if name.count(".") > 0:
                    f = name.split(".")[:-1]
                    n = ".".join(f)
                    n = n.replace(" ", "_")
                elif gen_level.is_metric(name):
                    n = gen_level.get_subplot(name)
                    if not n:
                        n = metric_levels[name] if name in metric_levels else "CPU-METRIC"
                    n = n.replace(" ", "_")
                    self.metrics.add(n)
                else:
                    n = "TopLevel"
                self.headers[name] = n
                self.levels[n].add(name)
            prevts = ts


data = Data(args.csvfile)
data.update()

def cmp_level(a, b):
    if a == "TopLevel":
        return -1
    if b == "TopLevel":
        return +1
    if a in data.metrics:
        return +1
    if b in data.metrics:
        return -1
    return cmp(a, b)

def gen_html():
    graph = """
<html><head><title>Toplev</title>
<script type="text/javascript" src="dygraph-combined.js"></script>
</head>
<body>
"""
    for j in sorted(data.levels.keys(), cmp=cmp_level):
        opts = dict()
        if j not in data.metrics:
            opts["stackedGraph"] = 1
            opts["stackedGraphNaNFill"] = "none"
            opts["ylabel"] = "% CPU time"
            opts["valueRange"] = [-5, 110]
        elif j in metric_unit:
            opts["ylabel"] = metric_unit[j]
        opts["title"] = j
        opts["width"] = 1000
        opts["height"] = 180
        #opts["xlabel"] = "time"
        graph += T("""
<div id="d$name"></div>
<script type="text/javascript">
    g = new Dygraph(document.getElementById("d$name"),
                    "/$file.csv", $opts)
</script>
                """).substitute({"name": j, "file": j, "opts": opts})
    graph + """
</body>
</html>"""
    return graph

def gencsv(wfile, l):
    hdr = sorted(data.levels[l])
    wr = csv.writer(wfile)
    wr.writerow(["Timestamp"] + hdr)
    for v, t in zip(data.vals, data.times):
        wr.writerow([t] + [v[x] if x in v else "" for x in hdr])

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

    def serve_file(self, fn, mime):
        with open(fn, "r") as f:
            self.header(mime)
            self.wfile.write(f.read())

    def do_GET(self):
        if self.path == "/":
            self.header("text/html")
            self.wfile.write(gen_html())
        elif self.path == "/dygraph-combined.js":
            self.serve_file("dygraph-combined.js", "text/javascript")
        elif self.path == "/favicon.ico":
            self.serve_file("toplev.ico", "image/x-icon")
        elif self.path.endswith(".csv"):
            l = re.sub(r"\.csv$", "", self.path[1:])
            if l not in data.levels:
                self.bad()
                return
            self.header("text/csv")
            gencsv(self.wfile, l)
        else:
            self.bad()

def copyfile(a, b):
    with open(a, "r") as af:
        with open(b, "w") as bf:
            bf.write(af.read())

if args.gen:
    if not os.path.isdir(args.gen):
        os.makedirs(args.gen)
    genfn = os.path.join
    with open(genfn(args.gen, "index.html"), 'w') as f:
        f.write(gen_html())
    copyfile('dygraph-combined.js', genfn(args.gen, 'dygraph-combined.js'))
    copyfile('toplev.ico', genfn(args.gen, 'favicon.ico'))
    for l in data.levels:
        with open(genfn(args.gen, l + ".csv"), 'w') as f:
            gencsv(f, l)
    print "Please browse", args.gen, "through a web server, not through file:"
else:
    httpd = BaseHTTPServer.HTTPServer((args.host, args.port), TLHandler)

    print "serving at",args.host,"port",args.port,"until Ctrl-C"
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()
