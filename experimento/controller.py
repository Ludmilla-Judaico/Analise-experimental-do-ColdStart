#!/usr/bin/env python3
import csv, os, subprocess, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import urlparse, parse_qs

PORTS  = {"go": 9001, "node": 9002, "python": 9003, "java": 9004}
CPUSET = "0,1"                      # núcleos dos containers (ajuste ao seu hardware)
OUT    = "results/controller.csv"
LOCK   = Lock()
os.makedirs("results", exist_ok=True)

def sh(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()

def remove(name):
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)

def drop_caches():
    subprocess.run(["sync"], check=True)                 # grava páginas sujas no disco
    with open("/proc/sys/vm/drop_caches", "w") as f:     # descarta o cache
        f.write("3")

def wait_ready(port, timeout=60):
    end = time.perf_counter() + timeout
    while time.perf_counter() < end:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.002)
    return False

def start_container(rt, wl):
    name = f"fn-{rt}"
    t0 = time.perf_counter()
    sh("docker", "run", "-d", "--name", name, f"--cpuset-cpus={CPUSET}",
       "-p", f"127.0.0.1:{PORTS[rt]}:8080", f"exp-{rt}-{wl}")
    t1 = time.perf_counter()
    ok = wait_ready(PORTS[rt])
    t2 = time.perf_counter()
    return name, t0, t1, t2, ok

def proc_metrics(name):
    pid = sh("docker", "inspect", "-f", "{{.State.Pid}}", name)
    with open(f"/proc/{pid}/stat") as f:
        fields = f.read().rsplit(")", 1)[1].split()
    minflt, majflt = int(fields[7]), int(fields[9])
    rss_kb = 0
    with open(f"/proc/{pid}/status") as f:
        for line in f:
            if line.startswith("VmHWM:"):
                rss_kb = int(line.split()[1])
    return rss_kb, minflt, majflt

def invoke(rt, wl, cache, seq):
    name = f"fn-{rt}"
    remove(name)
    if cache == "warm":
        start_container(rt, wl)      # rodada descartada: garante arquivos no cache
        remove(name)
    else:
        drop_caches()
    name, t0, t1, t2, ok = start_container(rt, wl)       # a medição real
    rss, minf, majf = proc_metrics(name) if ok else (0, 0, 0)
    remove(name)
    row = [seq, rt, wl, cache, round((t1-t0)*1000, 2), round((t2-t1)*1000, 2),
           round((t2-t0)*1000, 2), rss, minf, majf, int(ok)]
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["seq","runtime","workload","cache","t_create_ms","t_ready_ms",
                        "t_total_ms","rss_peak_kb","minor_pf","major_pf","ok"])
        w.writerow(row)
    return row

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        with LOCK:                                       # uma invocação por vez
            row = invoke(q["runtime"], q["workload"], q["cache"], q["seq"])
        self.send_response(200 if row[-1] else 500)
        self.send_header("X-T-Total", str(row[6]))
        self.end_headers()
        self.wfile.write(b"OK" if row[-1] else b"FAIL")
    def log_message(self, *a): pass

ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()