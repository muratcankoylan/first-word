#!/usr/bin/env python3
"""FIRST WORD: picture generation on Runway (Seedance 2.5 video, image models), with a spend guard.

    python3 tools/runway.py run <job>      a job from timing/generations.json: submit, wait, download, log
    python3 tools/runway.py balance        credits left in the Runway project

Every job is logged in ledger.csv with what Runway charged. A job is refused if it could take Runway spend past
the limit in budget.json. Output links are temporary, so files are downloaded as soon as a task succeeds.
"""
import base64
import csv
import datetime
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keys import env  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.dev.runwayml.com"
RATE = {"480": 20, "720": 30, "1080": 68}     # Seedance 2.5 credits per second of output


def J(*p):
    return os.path.join(ROOT, *p)


def call(method, path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Authorization": "Bearer " + env()["RUNWAYML_API_SECRET"], "X-Runway-Version": "2024-11-06", "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
        except urllib.error.HTTPError as ex:
            msg = ex.read().decode(errors="replace")[:600]
            if ex.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError("%s %s -> %d %s" % (method, path, ex.code, msg))
        except urllib.error.URLError as ex:
            if attempt < 4:
                time.sleep(5)
                continue
            raise RuntimeError("%s %s -> %r" % (method, path, ex))


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob = open(J(path), "rb").read()
    assert len(blob) < 5_000_000, "%s is over the 5 MB limit for inline inputs" % path
    return "data:%s;base64,%s" % (mime, base64.b64encode(blob).decode())


def spent_usd():
    total = 0.0
    for row in csv.DictReader(open(J("ledger.csv"))):
        if row["service"] == "runway":
            total += float(row["cost_usd"] or 0)
    return total


def log(model, what, seconds, credits, output, ok):
    with open(J("ledger.csv"), "a", newline="") as f:
        csv.writer(f).writerow([datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "runway", model, what, seconds, credits, 0.01, round(credits * 0.01, 2), output, "yes" if ok else "no"])


def estimate(job):
    b = job["body"]
    if "credits" in job:
        return job["credits"]
    if job["endpoint"].endswith("text_to_image") or "draftTaskId" in b:
        return job.get("credits", 10)      # an enhance is 68 credits a second of the draft it enhances
    secs = b.get("duration", 5)
    secs = 30 if secs == "auto" else secs
    tier = "480" if b.get("draft") else b.get("ratio", "1280:720").split(":")[1][:4].replace("720", "720")
    tier = "480" if b.get("draft") else ("1080" if "1080" in b.get("ratio", "") or "1920" in b.get("ratio", "") else "720")
    ref_secs = job.get("reference_video_seconds", 0)
    return max(80, secs * RATE[tier] + ref_secs * RATE[tier] // 2)


def run(name):
    jobs = json.load(open(J("timing", "generations.json")))["jobs"]
    job = jobs[name]
    body = dict(job["body"])
    for key in ("references",):
        if key in job.get("files", {}):
            body[key] = [dict(uri=data_uri(p)) for p in job["files"][key]]
    if "referenceAudio" in job.get("files", {}):
        body["referenceAudio"] = [dict(type="audio", uri=data_uri(p)) for p in job["files"]["referenceAudio"]]
    if "referenceVideos" in job.get("files", {}):
        body["referenceVideos"] = [dict(type="video", uri=data_uri(p)) for p in job["files"]["referenceVideos"]]
    if "promptVideo" in job.get("files", {}):
        body["promptVideo"] = data_uri(job["files"]["promptVideo"])
    if "promptImage" in job.get("files", {}):
        body["promptImage"] = [dict(uri=data_uri(p["file"]), position=p["position"]) for p in job["files"]["promptImage"]]
    budget = json.load(open(J("budget.json")))
    est = estimate(job)
    if spent_usd() + est * 0.01 > budget["split_usd"]["runway"]:
        sys.exit("refused: %s would take Runway spend past %d USD" % (name, budget["split_usd"]["runway"]))
    before = call("GET", "/v1/organization")["creditBalance"]
    if before < est:
        sys.exit("refused: %d credits needed, %d in the Runway project" % (est, before))
    task = call("POST", job["endpoint"], body)
    tid = task["id"]
    print("%s submitted, task %s, estimate %d credits" % (name, tid[:8], est), flush=True)
    t0 = time.time()
    while True:
        time.sleep(8)
        t = call("GET", "/v1/tasks/" + tid)
        if t["status"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        if time.time() - t0 > 1500:
            print("still running after 25 minutes; task id saved")
            break
    after = call("GET", "/v1/organization")["creditBalance"]
    cost = (t.get("cost") or {}).get("credits")
    charged = int(round(cost)) if cost is not None else before - after   # the task's own figure when it gives one: balance readings mix jobs that overlap
    out_files = []
    if t["status"] == "SUCCEEDED":
        for i, url in enumerate(t.get("output", [])):
            ext = os.path.splitext(url.split("?")[0])[1] or (".png" if "image" in job["endpoint"] else ".mp4")
            dest = job["out"] if i == 0 else job["out"].replace(".", "_%d." % (i + 1))
            dest = os.path.splitext(dest)[0] + ext
            os.makedirs(os.path.dirname(J(dest)), exist_ok=True)
            urllib.request.urlretrieve(url, J(dest))
            out_files.append(dest)
    res = dict(job=name, task=tid, status=t["status"], seconds_waited=round(time.time() - t0), credits_charged=charged, files=out_files,
               failure=t.get("failure"), failure_code=t.get("failureCode"), made=datetime.datetime.utcnow().isoformat() + "Z")
    json.dump(res, open(J("clips", "drafts", name + ".json"), "w"), indent=1)
    log(body.get("model", "?"), name + ": " + job.get("what", ""), body.get("duration", ""), charged, ";".join(out_files), t["status"] == "SUCCEEDED")
    print(json.dumps({k: res[k] for k in ("job", "status", "seconds_waited", "credits_charged", "files", "failure", "failure_code")}))


if __name__ == "__main__":
    if sys.argv[1] == "balance":
        o = call("GET", "/v1/organization")
        print("credits", o["creditBalance"], "| spent so far (ledger): %.2f USD" % spent_usd())
    else:
        run(sys.argv[2])
