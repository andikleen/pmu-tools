#!/usr/bin/env python
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
import itertools
import tldata

ap = argparse.ArgumentParser(usage="Serve toplev csv file as http or generate in directory")
ap.add_argument('csvfile', help='toplev csv file to serve')
ap.add_argument('host', nargs='?', default="localhost", help='Hostname to bind to (default localhost)')
ap.add_argument('port', nargs='?', default="9001", type=int, help='Port to bind to (default 9001)')
ap.add_argument('--verbose', '-v', action='store_true', help='Display all metrics, even if below threshold')
ap.add_argument('--gen', help='Generate HTML files in specified directory')
ap.add_argument('--title', help='Title for output')
args = ap.parse_args()

T = string.Template

data = tldata.TLData(args.csvfile, args.verbose)
data.update()

def jsname(n):
    return n.replace(".", "_").replace("-", "_")

def comma_strings(l):
    return ",".join(['"%s"' % (x) for x in l])

def gen_html_header():
    graph = """<html><head><title>Toplev</title>
<link rel="shortcut icon" href="toplev.ico" />
<script type="text/javascript" src="dygraph-combined.js"></script>
</head>
<body>
<script type="text/javascript">

var cpus = ["""

    graph += comma_strings(sorted(data.cpus)) + "]\n"
    graph += "var nodes = [" + comma_strings(tldata.level_order(data)) + "]"

    graph += """
var graphs = []
var goptions = []
var num_graphs = 0
var block_redraw = false

function enable(el) {
    for (i = 0; i < cpus.length; i++) {
        p = document.getElementById("d_" + cpus[i] + "_" + el.name)
        p.style.display = el.checked ? 'block' : 'none';
    }
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

function add_node(cpu, nd) {
    p = document.getElementById("d_" + cpus[cpu] + "_" + nodes[nd])
    p.parentNode.appendChild(p)
}

function toggle_interleave(el) {
    if (!el.checked) {
        for (cpu = 0; cpu < cpus.length; cpu++) {
            for (nd = 0; nd < nodes.length; nd++) {
                add_node(cpu, nd)
            }
        }
    } else {
        for (nd = 0; nd < nodes.length; nd++) {
            for (cpu = 0; cpu < cpus.length; cpu++) {
                add_node(cpu, nd)
            }
        }
    }
}

function draw_graph(me, initial) {
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

function hilight_help(e, x, pts, row, help) {
    p = document.getElementById("help")
    h = ""
    for (i = 0; i < pts.length; i++) {
        n = pts[i].name
        if (n in help && help[n] != "") {
            h += "<b>" + n + "</b>: " + help[n] + " <br /> "
        } else {
            // location.reload(); // XXX
        }
    }
    p.innerHTML = h
}

function unhilight_help(e, x, pts, row) {
    p = document.getElementById("help")
    p.innerHTML = ""
}

</script>
"""
    if args.title:
        graph += T("<h1>$title</h1>\n").substitute({"title": args.title})
    graph += """
<div><p>
<b>Display:</b>
"""
    lev = tldata.level_order(data)
    for num, name in enumerate(lev):
        graph += T("""\
<input id="$id" class="toggles" type=checkbox name="$name" onClick="enable(this)" checked />
<label for="$id">$name</label>
        """).substitute({"id": num, "name": name})
    graph += """
<input id="all" type=checkbox name="dall" onClick="change_all(this.checked)" checked />
<label for="all">Toggle all</label>
<input id="enable_refresh" type=checkbox onClick="toggle_refresh(this)" />
<label for="enable_refresh">Auto-refresh</label>
<input id="refresh_rate" type="text" size=4 value="1000" name="refresh"  />
<label for="refresh_rate">Refresh rate (ms)</label>
<input id="interleave" type=checkbox onClick="toggle_interleave(this)" />
<label for="interleave">Interleave CPUs</label>
</p></div>

Drag to zoom. Double click to zoom out again<br />

<div id="help" style="position:fixed; right:0; width:300px; font-size: 11"> </div>
"""

    for j in lev:
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
        """).substitute({"name": get_postfix(i), "help": data.helptxt[i] })
        graph += """
}
</script>
"""
    return graph

def gen_html_cpu(cpu):
    lev = tldata.level_order(data)
    graph = ""
    for name in lev:
        opts = {
            "title": name + " " + cpu,
            "width": 1000,
            "height": 180,
            #"xlabel": "time",
        }

        if name in data.metrics:
            unit = gen_level.get_unit(list(data.levels[name])[0])
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

<div id="d_${cpu}_$name" class="disp"></div>

<script type="text/javascript">
    i = num_graphs++
    goptions[i] = $opts
    goptions[i].highlightCallback = function(e, x, pts, row) {
        hilight_help(e, x, pts, row, help_$jname)
    }
    goptions[i].unhighlightCallback = unhilight_help
    goptions[i].drawCallback = draw_graph
    graphs[i] = new Dygraph(document.getElementById("d_${cpu}_$name"), "$cpu.$file.csv", goptions[i])
    goptions[i]["file"] = "$cpu.$file.csv"
</script>
                """).substitute({"name": name, "jname": jsname(name), "file": name, "cpu": cpu, "opts": opts})
    return graph

def gen_html():
    graph = gen_html_header()
    for cpu in sorted(data.cpus):
        graph += gen_html_cpu(cpu)
    graph += """
</body>
</html>"""
    return graph

def get_postfix(s):
    m = re.match(r'.*\.(.*)', s)
    if m:
        return m.group(1)
    return s

def gencsv(wfile, l, cpu):
    hdr = sorted(data.levels[l])
    wr = csv.writer(wfile)
    wr.writerow(["Timestamp"] + map(get_postfix, hdr))
    for val, ts in zip(data.vals, data.times):
        wr.writerow([ts] + [val[(x, cpu)] if (x, cpu) in val else "" for x in hdr])

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
            m = re.match(r"/(cpu|C\d+|S\d+-C\d+|C\d+-T\d+)\.(.*?)\.csv", self.path)
            if not m:
                self.bad()
                return
            cpu = m.group(1)
            l = m.group(2)
            if l not in data.levels:
                self.bad()
                return
            self.header("text/csv")
            gencsv(self.wfile, l, cpu)
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
    for cpu in data.cpus:
        for l in data.levels:
            with open(genfn(args.gen, cpu + "." + l + ".csv"), 'w') as f:
                gencsv(f, l, cpu)
    print "Please browse", args.gen, "through a web server, not through file:"
else:
    httpd = BaseHTTPServer.HTTPServer((args.host, args.port), TLHandler)

    print "serving at",args.host,"port",args.port,"until Ctrl-C"
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()
