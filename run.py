"""Draw the samples defined in PREREGISTRATION.md. Appends to raw.jsonl; resumable.
Usage: python -I run.py [budget_usd]"""
import concurrent.futures as cf
import json, os, pathlib, sys, threading, time, urllib.request

HERE = pathlib.Path(__file__).parent
ARMS = ["openai/gpt-6.2-astra", "openai/gpt-6-astra"]
N = 30
EFFORT = "medium"
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
NAMES = [l.strip() for l in (HERE / "names.txt").read_text().splitlines() if l.strip()]
PROMPTS = {
    "P1": "Create a puzzle spy game. Choose any setting you want. Reply with only the setting's name on line 1, then one sentence.",
    "P2": "Write the premise of a classic murder mystery. Reply with only the detective's full name on line 1, then one sentence.",
    "P3": "Invent a space station for a sci-fi story. Reply with only its name on line 1, then one sentence.",
    "P4": "Name a new AI note-taking startup. Reply with only the name on line 1, then one sentence.",
    "C": "Pick one name at random from this list and reply with only that name: " + ", ".join(NAMES),
}
KEY = os.environ["OPENROUTER_API_KEY"]  # set this in your shell before running
RAW = HERE / "raw.jsonl"
lock = threading.Lock()
done = set()
spent = 0.0
if RAW.exists():
    for l in RAW.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        done.add((r["arm"], r["prompt"], r["i"]))
        spent += r.get("cost") or 0


def call(arm, pid, i):
    global spent
    body = {"model": arm, "messages": [{"role": "user", "content": PROMPTS[pid]}],
            "reasoning": {"effort": EFFORT}, "max_tokens": 4000, "usage": {"include": True}}
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                         data=json.dumps(body).encode(),
                                         headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            j = json.loads(urllib.request.urlopen(req, timeout=300).read())
            break
        except Exception as e:
            err = str(e)[:120]
            time.sleep(5 * (attempt + 1))
    else:
        return {"arm": arm, "prompt": pid, "i": i, "error": err}
    u = j.get("usage", {})
    rec = {"arm": arm, "prompt": pid, "i": i, "effort": EFFORT, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "provider": j.get("provider"), "model_returned": j.get("model"),
           "output": j["choices"][0]["message"].get("content"),
           "completion_tokens": u.get("completion_tokens"),
           "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
           "cost": u.get("cost")}
    with lock:
        spent += rec["cost"] or 0
        with RAW.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# Interleave: sample index outermost, then prompt, then arm.
jobs = [(a, p, i) for i in range(N) for p in PROMPTS for a in ARMS if (a, p, i) not in done]
print(len(jobs), "to run; spent so far $%.4f" % spent)
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    futs = []
    for job in jobs:
        if spent >= BUDGET:
            print("budget reached, stopping submission")
            break
        futs.append(ex.submit(call, *job))
        if len(futs) % 6 == 0:
            cf.wait(futs[-6:])
    errs = [f.result() for f in futs if "error" in f.result()]
print("done. spent $%.4f, errors %d" % (spent, len(errs)))
for e in errs[:5]:
    print(e)
