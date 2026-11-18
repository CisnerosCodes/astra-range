"""EXPLORATORY (not preregistered, written after results were read).
1) Permutation test of the D difference between arms per prompt (the preregistered bootstrap
   interval turned out biased low for D, see README). 2) Bellwether search. 3) Chart without
   error bars."""
import collections, json, math, pathlib, random, re
from analyze import norm, D, ARMS, HERE

random.seed(1)
rows = [json.loads(l) for l in (HERE / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
by = collections.defaultdict(list)
for r in rows:
    by[(r["arm"], r["prompt"])].append(norm(r["output"]))
out = {"bellwether_hits": [(r["arm"], r["prompt"], r["output"][:80]) for r in rows if "bellwether" in (r["output"] or "").lower()],
       "perm": {}}
for p in ["P1", "P2", "P3", "P4", "C"]:
    a, b = by[(ARMS[0], p)], by[(ARMS[1], p)]
    obs = D(list(collections.Counter(a).values())) - D(list(collections.Counter(b).values()))
    pool, k, hits = a + b, 10000, 0
    for _ in range(k):
        random.shuffle(pool)
        x, y = pool[:len(a)], pool[len(a):]
        if abs(D(list(collections.Counter(x).values())) - D(list(collections.Counter(y).values()))) >= abs(obs):
            hits += 1
    out["perm"][p] = {"D_6.2_minus_D_6": round(obs, 2), "p_two_sided": round((hits + 1) / (k + 1), 4)}
(HERE / "explore.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
res = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
ps = ["P1", "P2", "P3", "P4", "C"]
labels = ["spy game\nsetting", "detective\nname", "space station\nname", "startup\nname", "pick a name\nat random"]
fig, ax = plt.subplots(figsize=(10, 5))
w = 0.38
for k, arm in enumerate(ARMS):
    ds = [res["cells"][f"{arm}|{p}"]["D"] for p in ps]
    bars = ax.bar([i + (k - 0.5) * w for i in range(len(ps))], ds, w, label=arm.split("/")[1].replace("gpt-", "GPT-").replace("-astra", " Astra"))
    for bar, d in zip(bars, ds):
        ax.text(bar.get_x() + bar.get_width() / 2, d + 0.3, f"{d:.1f}", ha="center", fontsize=9)
lo, hi = res["null_C_D_95"]
ax.plot([3.55, 4.45], [lo, lo], "k--", lw=1)
ax.plot([3.55, 4.45], [hi, hi], "k--", lw=1)
ax.text(4, hi + 0.4, "truly random range", ha="center", fontsize=8)
ax.set_xticks(range(len(ps)), labels)
ax.set_ylabel("effective number of different answers\n(30 fresh runs each, max 30)")
ax.set_title("Same prompt, 30 fresh runs: how many different answers does each model really give?")
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig(HERE / "chart.png", dpi=160)
print("chart saved")
