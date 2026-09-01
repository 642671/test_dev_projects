import glob, json, io, os

f = sorted(glob.glob(r"C:\Users\twm\AppData\Local\Temp\login_run_*.json"))[-1]
print("REPORT", f)
d = json.load(open(f, encoding="utf-8"))
run = d.get("run", {})
def walk(items):
    for it in items or []:
        nm = it.get("name", "")
        if "request" in it:
            ex = it.get("executions", [])
            for e in ex:
                resp = e.get("response")
                if resp and "login" in nm.lower():
                    print("REQ", nm)
                    print("CODE", resp.get("code"), resp.get("status"))
                    print("HEADERS", json.dumps(resp.get("headers"), ensure_ascii=False))
                    body = resp.get("stream") or resp.get("responseTime")
                    st = resp.get("stream")
                    print("BODY_LEN", len(st or ""), "empty?", not bool(st))
                    print("BODY", (st or "")[:400])
        elif "item" in it:
            walk(it["item"])
walk(run.get("executions", []))
