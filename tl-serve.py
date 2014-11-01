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
ap.add_argument('csvfile', help='toplev csv file to serve')
ap.add_argument('host', nargs='?', default="localhost", help='Hostname to bind to (default localhost)')
ap.add_argument('port', nargs='?', default="9001", type=int, help='Port to bind to (default 9001)')
ap.add_argument('--verbose', '-v', action='store_true', help='Display all metrics, even if below threshold')
ap.add_argument('--gen', help='Generate HTML files in specified directory')
ap.add_argument('--title', help='Title for output')
args = ap.parse_args()

T = string.Template

class Data:
    def __init__(self, fn):
        self.times = []
        self.vals = []
        self.fn = fn
        self.levels = defaultdict(set)
        self.metrics = set()
        self.mtime = None
        self.helptxt = dict()

    def update(self):
        mtime = os.path.getmtime(self.fn)
        if self.mtime == mtime:
            return
        self.mtime = mtime
        csvf = csv.reader(open(self.fn, 'r'))
        prevts = None
        val = dict()
        for r in csvf:
            ts, name, pct, state, helptxt = r[0], r[1], r[2], r[3], r[4]
            if name not in self.helptxt or self.helptxt[name] == "":
                self.helptxt[name] = helptxt
            if state == "below" and not args.verbose:
                continue
            if prevts and ts != prevts:
                self.times.append(prevts)
                self.vals.append(val)
                val = dict()
            val[name] = pct
            n = gen_level.level_name(name)
            if gen_level.is_metric(name):
                self.metrics.add(n)
            self.levels[n].add(name)
            prevts = ts


data = Data(args.csvfile)
data.update()

early_plots = ["TopLevel", "CPU_Utilization", "Power", "Frequency", "CPU-METRIC"]

def sort_pos(i):
    if i in early_plots:
        return early_plots.index(i)
    if i in data.metrics:
        return 30
    return 20

def cmp_level(a, b):
    ap, bp = sort_pos(a), sort_pos(b)
    if ap != bp:
        return ap - bp
    return cmp(a, b)

def jsname(n):
    return n.replace(".", "_").replace("-", "_")

def gen_html():
    lev = sorted(data.levels.keys(), cmp=cmp_level)
    graph = """
<html><head><title>Toplev</title>
<link rel="shortcut icon" href="toplev.ico" />
<script type="text/javascript" src="dygraph-combined.js"></script>
</head>
<body>
<script type="text/javascript">

var graphs = []
var goptions = []
var num_graphs = 0
var block_redraw = false

function enable(el) {
    p = document.getElementById(el.name)
    p.style.display = el.checked ? 'block' : 'none';
}

function change_all(flag) {
    all_displays = document.getElementsByClassName("disp")
    for (i = 0; i < all_displays.length; i++) {
        p = all_displays[i];
        p.style.display = flag ? 'block' : 'none';
    }
    togs = document.getElementsByClassName("toggles")
    for (i = 0; i < togs.length; i++) {
        p = togs[i];
        p.checked = flag;
    }
}

var timer

function toggle_refresh(el) {
    p = document.getElementById("refresh_rate")
    if (timer) {
        clearInterval(timer)
        timer = null
    }
    if (el.checked) {
        timer = setInterval(function () {
                    for (i = 0; i < num_graphs; i++) {
                        graphs[i].updateOptions(goptions[i])
                    }
                }, Number(p.value))
    }
}
</script>
"""
    if args.title:
        graph += T("<h1>$title</h1>\n").substitute({"title": args.title})
    graph += """
<div><p>
<b>Display:</b>
"""
    for j, id in zip(lev, range(len(lev))):
        graph += T("""
<input id="$id" class="toggles" type=checkbox name="d_$name" onClick="enable(this)" checked />
<label for="$id">$name</label>
        """).substitute({"id": id, "name": j})
    graph += """
<input id="all" type=checkbox name="dall" onClick="change_all(this.checked)" checked />
<label for="all">Toggle all</label>
<input id="enable_refresh" type=checkbox onClick="toggle_refresh(this)" />
<label for"enable_refresh">Auto-refresh</a>
<input id="refresh_rate" type="text" size=4 value="1000" name="refresh"  />
<label for="refresh_rate">Refresh rate (ms)</label>
</p></div>

Drag to zoom. Double click to zoom out again<br />

<div id="help" style="position:fixed; right:0; width:300px; font-size: 11"> </div>
"""
    for j in lev:
        opts = {
            "title": j,
            "width": 1000,
            "height": 180,
            #"xlabel": "time",
        }

        
        graph += T("""
<script type="text/javascript">
help_$name = {
""").substitute({"name": jsname(j)})
        for i in data.levels[j]:
            if i not in data.helptxt:
                #print i,"not found in",data.helptxt.keys()
                continue
            graph += T("""
        "$name": "$help",
        """).substitute({"name": i, "help": data.helptxt[i] })
        graph += """
}
</script>
"""
        if j in data.metrics:
            unit = gen_level.get_unit(list(data.levels[j])[0])
            if unit:
                opts["ylabel"] = unit
        else:
            opts["stackedGraph"] = 1
            opts["stackedGraphNaNFill"] = "none"
            opts["ylabel"] = "% CPU time"
            unit = '%'
        if unit == '%':
            opts["valueRange"] = [-5, 110]
        graph += T("""

<div id="d_$name" class="disp"></div>

<script type="text/javascript">
    i = num_graphs++
    goptions[i] = $opts
    goptions[i].highlightCallback = function(e, x, pts, row) {
        p = document.getElementById("help")
        h = ""
        for (i = 0; i < pts.length; i++) {
            n = pts[i].name
            if (n in help_$jname && help_$jname[n] != "") {
                h += "<b>" + n + "</b>: " + help_$jname[n] + " <br /> "
            } else {
                // location.reload(); // XXX
            }
        }
        p.innerHTML = h
    }
    goptions[i].drawCallback = function(me, initial) {
        if (block_redraw || initial)
            return;
        block_redraw = true
        xrange = me.xAxisRange()
        for (i = 0; i < num_graphs; i++) {
            if (graphs[i] != me) {
                graphs[i].updateOptions({
                    dateWindow: xrange,
                })
            }
        }
        block_redraw = false
    }
    goptions[i].unhighlightCallback = function(e, x, pts, row) {
        p = document.getElementById("help")
        p.innerHTML = ""
    }
    graphs[i] = new Dygraph(document.getElementById("d_$name"), "$file.csv", goptions[i])
    goptions[i]["file"] = "$file.csv"
</script>
                """).substitute({"name": j, "jname": jsname(j), "file": j, "opts": opts})
    graph += """
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
        elif self.path == "/toplev.ico":
            self.serve_file("toplev.ico", "image/x-icon")
        elif self.path.endswith(".csv"):
            data.update()
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
