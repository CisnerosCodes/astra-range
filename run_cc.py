"""Claude arms of PREREGISTRATION-2.md through the Claude Code CLI (subscription). Appends to
raw_cc.jsonl; resumable. Stops on the first rate-limit or auth error. Usage: python run_cc.py"""
import concurrent.futures as cf
import json, pathlib, subprocess, tempfile, threading, time

HERE = pathlib.Path(__file__).parent
from run_prompts import PROMPTS  # same text as run.py

CLAUDE = str(pathlib.Path.home() / "AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe")
MODELS = {"opus-5.5": "opus", "fable-5.2": "claude-fable-5-2"}
BASE = ["--output-format", "json", "--no-session-persistence", "--exclude-dynamic-system-prompt-sections"]
ARMS = {"harness": [], "stripped": ["--system-prompt", "You are a helpful assistant.", "--tools", "",
                                     "--setting-sources", "", "--strict-mcp-config"]}
N = 30
RAW = HERE / "raw_cc.jsonl"
WORK = pathlib.Path(tempfile.mkdtemp(prefix="cc_empty_"))
lock = threading.Lock()
stop = threading.Event()
done = set()
if RAW.exists():
    for l in RAW.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        if not r.get("error"):
            done.add((r["model"], r["arm"], r["prompt"], r["i"]))


def call(model, arm, pid, i):
    if stop.is_set():
        return None
    cmd = [CLAUDE, "-p", PROMPTS[pid], "--model", MODELS[model]] + BASE + ARMS[arm]
    try:
        p = subprocess.run(cmd, cwd=WORK, capture_output=True, text=True, encoding="utf-8", timeout=600, shell=False)
        line = [l for l in p.stdout.splitlines() if l.strip().startswith("{")][-1]
        d = json.loads(line)
    except Exception as e:
        rec = {"model": model, "arm": arm, "prompt": pid, "i": i, "error": str(e)[:200]}
    else:
        u = d.get("usage") or {}
        rec = {"model": model, "arm": arm, "prompt": pid, "i": i, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "model_used": list((d.get("modelUsage") or {}).keys()), "output": d.get("result"),
               "is_error": d.get("is_error"), "num_turns": d.get("num_turns"),
               "notional_cost_usd": d.get("total_cost_usd"),
               "cache_read": u.get("cache_read_input_tokens"), "cache_create": u.get("cache_creation_input_tokens")}
        txt = (rec["output"] or "").lower()
        if d.get("is_error") or "rate limit" in txt or "usage limit" in txt or "login" in txt[:80]:
            rec["error"] = "api error or limit: " + txt[:150]
    with lock:
        with RAW.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if rec.get("error"):
            stop.set()
    return rec


jobs = [(m, a, p, i) for i in range(N) for p in PROMPTS for m in MODELS for a in ARMS
        if (m, a, p, i) not in done]
print(len(jobs), "to run in", WORK, flush=True)
with cf.ThreadPoolExecutor(max_workers=3) as ex:
    results = list(ex.map(lambda j: call(*j), jobs))
rows = [r for r in results if r]
print("done", len(rows), "errors", sum(1 for r in rows if r.get("error")),
      "notional usage $%.2f" % sum(r.get("notional_cost_usd") or 0 for r in rows), flush=True)
for r in [r for r in rows if r.get("error")][:3]:
    print(r)
