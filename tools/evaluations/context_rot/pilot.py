"""Execute approved four-condition pilot blocks on isolated Windows CLI projects."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from uuid import uuid4

from fixture import BEFORE, DECISION, RULES, TASK, prepare, score, write


EXE = Path(os.environ["LOCALAPPDATA"]) / "Programs/OpenAI/Codex/bin/codex.exe"
# Standard USD per million input, cached input, output; sum of model caps = USD 15.
MODELS = {
    "gpt-6.2-sol": ((2, .10, 10), 8.5, ("jit", "compression", "handoff")),
    "gpt-6.1-terra": ((1, .05, 5), 5, ("handoff", "jit", "compression")),
    "gpt-6-luna": ((.10, .01, .50), 1.5, ("compression", "jit", "handoff")),
}
CONFIG = {"model_context_window":272000, "model_auto_compact_token_limit":231200,
          "model_reasoning_effort":"xhigh", "web_search":"disabled", "features.memories":False,
          "features.hooks":False, "features.apps":False, "features.plugins":False,
          "features.remote_plugin":False, "features.multi_agent":False,
          "memories.generate_memories":False, "memories.use_memories":False,
          "sandbox_workspace_write.network_access":False}


def cost(model, usage):
    inp, cached, out = MODELS[model][0]
    total = usage.get("inputTokens", 0)
    hits = usage.get("cachedInputTokens", 0)
    writes = usage.get("cacheWriteInputTokens", 0)
    return ((total-hits)*inp + hits*cached + writes*.25*inp + usage.get("outputTokens",0)*out)/1e6


class Session:
    def __init__(self, cmd, cwd, model, row, deadline, budget_left):
        self.model, self.row, self.deadline, self.budget_left = model, row, deadline, budget_left
        self.events = queue.Queue()
        self.number = 0
        self.usage = {}
        self.replay = False
        self.commands = []
        self.thread = None
        self.details = {"usage":{}, "commands":self.commands, "compression_tools":[]}
        self.row.setdefault("sessions", []).append(self.details)
        env = {k:v for k,v in os.environ.items() if not k.startswith("LANGFUSE_")}
        self.p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            try:
                self.events.put(json.loads(line))
            except ValueError:
                continue
        self.events.put(None)

    def send(self, obj):
        self.p.stdin.write(json.dumps(obj,ensure_ascii=True)+"\n")
        self.p.stdin.flush()

    def reserve(self):
        # A 272K input and 128K output request, including premium cache writes.
        inp, _, out = MODELS[self.model][0]
        reserve = (.272*2.5*inp + .128*out)
        if self.budget_left - cost(self.model,self.usage) < reserve:
            raise RuntimeError("BUDGET_RESERVE")

    def event(self):
        wait = self.deadline - time.monotonic()
        if wait <= 0:
            raise TimeoutError("TIME_LIMIT")
        try:
            e = self.events.get(timeout=wait)
        except queue.Empty:
            raise TimeoutError("TIME_LIMIT") from None
        if e is None:
            raise RuntimeError("CLI_EOF")
        method = e.get("method")
        args = e.get("params", {})
        if method == "thread/tokenUsage/updated":
            self.usage = args["tokenUsage"]["total"]
            self.details.update(usage=self.usage, effective_window=args["tokenUsage"].get("modelContextWindow"))
            self.reserve()
        if method == "model/rerouted":
            raise RuntimeError("MODEL_REROUTED")
        if method == "item/completed":
            item = args["item"]
            if item["type"] == "commandExecution":
                command = item.get("command","").lower()
                output = item.get("aggregatedOutput") or ""
                self.replay |= ("replay.py" in command and "REPLAY_EXECUTED" in output and item.get("exitCode")==0)
                # Store only fixed categories, not arbitrary model/tool payloads.
                self.commands.append([s for s in ("replay.py","record-handoff","index.md","current.md",
                    "evidence.md","retired.md","shift-","notes.md","handoffs","context-policy","status.json")
                    if s in command] or ["other"])
            elif item["type"] == "mcpToolCall":
                tool = item.get("tool","")
                if tool in ("compress","decompress","search_context","acp_status","list_context"):
                    self.details["compression_tools"].append([tool,item.get("status")])
        if method and "id" in e:
            self.send({"id":e["id"],"error":{"code":-32601,"message":"Not available in this isolated pilot"}})
        return e

    def rpc(self, method, params):
        self.number += 1
        self.send({"id":self.number,"method":method,"params":params})
        while True:
            e = self.event()
            if e.get("id") == self.number and "method" not in e:
                if "error" in e:
                    message = re.sub(r'[^\w .,\-:]', '', str(e["error"].get("message","")))[:180]
                    raise RuntimeError(f"{method}: {message}")
                return e["result"]

    def start(self, cwd):
        self.rpc("initialize",{"clientInfo":{"name":"context_rot_pilot","version":"1"},
                               "capabilities":{"experimentalApi":True}})
        self.send({"method":"initialized","params":{}})
        data = self.rpc("thread/start",{"cwd":str(cwd),"ephemeral":True,"model":self.model,
            "sandbox":"workspace-write","approvalPolicy":"never","serviceTier":"default",
            "developerInstructions":RULES,"config":CONFIG})
        self.thread = data["thread"]["id"]
        self.details.update(model=data["model"],effort=data.get("reasoningEffort"),tier=data.get("serviceTier"))
        if data["model"] != self.model or data.get("reasoningEffort") not in ("xhigh",None):
            raise RuntimeError("MODEL_CONFIG_MISMATCH")

    def turn(self, prompt):
        self.reserve()
        self.details["turn_pending"] = True
        self.rpc("turn/start",{"threadId":self.thread,"effort":"xhigh",
                              "input":[{"type":"text","text":prompt}]})
        while True:
            e = self.event()
            if e.get("method") == "turn/completed":
                turn = e["params"]["turn"]
                if turn["status"] != "completed":
                    error = turn.get("error") or {}
                    message = str(error.get("message",""))
                    # Retain service/error category, with no prompt or response bodies.
                    categories = [x for x in ("usage limit","rate limit","not supported","not available",
                        "unauthorized","stream disconnected","invalid","quota","401","403","429","502","503")
                        if x in message.lower()]
                    raise RuntimeError("TURN_"+turn["status"]+":"+(",".join(categories) or str(error.get("codexErrorInfo","unknown"))[:70]))
                self.details["turn_pending"] = False
                return

    def close(self):
        if self.p.poll() is None:
            if self.thread:
                try: self.send({"id":9000,"method":"thread/unsubscribe","params":{"threadId":self.thread}})
                except OSError: pass
            self.p.stdin.close()
            try: self.p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill","/PID",str(self.p.pid),"/T","/F"],capture_output=True)
        self.details["replay_seen"] = self.replay


def workflow(run, kit, tag, model, feature, long, enabled, deadline, budget):
    root = run/"cells"/tag/f"{model}-{feature}-{'long' if long else 'short'}-{'on' if enabled else 'off'}"
    history, tokens, protected = prepare(root, kit, feature, long, enabled)
    row = {"id":str(uuid4()),"model":model,"feature":feature,"long":long,"on":enabled,
           "material_tokens":tokens,"status":"running","sessions":[]}
    start = time.monotonic()
    cmd = [str(EXE),"--no-daemon","app-server","--stdio"]
    if feature == "compression" and enabled:
        cmd = [sys.executable,"-X","utf8","-B",str(kit/"mycodex.py"),"compression","codex","--target",str(root),
               "--runtime",str(run/"runtime"),"--apply","--","app-server","--stdio"]
    for key,value in CONFIG.items():
        cmd += ["-c", key+"="+json.dumps(value)]
    def session(prompts):
        remaining = budget-sum(cost(model,s["usage"]) for s in row["sessions"])
        cli = Session(cmd,root,model,row,min(deadline,time.monotonic()+155),remaining)
        try:
            cli.start(root)
            for prompt in prompts: cli.turn(prompt)
        finally:
            cli.close()
        if not cli.usage:
            raise RuntimeError("USAGE_UNAVAILABLE")
        return cli.replay
    try:
        if feature == "handoff":
            instruction = ("Use the installed $session-handoff workflow and record a valid snapshot." if enabled
                           else "Write a free-form handoff in NOTES.md for the next session.")
            session(["The current shift is ending; hand over the verified state and next action. "
                     "Do not implement or run replay. "+instruction+"\nEarlier shift transcript:\n"+"".join(history)])
            write(root,"records/current.md",DECISION)
            protected["records/current.md"] = hashlib.sha256((root/"records/current.md").read_bytes()).hexdigest()
            replay = session(["Resume in this new session using available notes and current sources. "+TASK])
        elif feature == "compression":
            replay = session(["Read the eight records/shift-*.txt in chronological order using separate tool calls. "
                "Keep current and obsolete facts distinct. Report only that the historical review is complete.",
                "Use the earlier evidence. If compressed evidence exists, search and restore the original. "+TASK])
        else:
            replay = session([TASK])
        row["status"] = "completed"
    except (OSError, RuntimeError, TimeoutError, KeyError, ValueError) as error:
        row["status"] = "incomplete"
        row["error"] = str(error)[:220]
        replay = any(s.get("replay_seen") for s in row["sessions"])
    row["scores"], row["protected_changes"] = score(root,replay,protected)
    row["seconds"] = round(time.monotonic()-start,3)
    row["usd_estimate"] = sum(cost(model,s["usage"]) for s in row["sessions"])
    inp, _, out = MODELS[model][0]
    # Keep an allowance for any request whose final usage could not be observed.
    row["unsettled_reserve_usd"] = sum(.272*2.5*inp + .128*out for s in row["sessions"]
                                       if s.get("turn_pending"))
    return row


def run_model(run, kit, tag, model, deadline):
    budget = MODELS[model][1]
    file = run / f"{tag}-{model}.jsonl"
    with file.open("x",encoding="utf8") as journal:
        for n, feature in enumerate(MODELS[model][2]):
            order = [(False,False),(True,True),(False,True),(True,False)]
            offset = (list(MODELS).index(model)+n)%4
            for long,enabled in order[offset:]+order[:offset]:
                if time.monotonic()>=deadline: return
                row = workflow(run,kit,tag,model,feature,long,enabled,deadline,budget)
                journal.write(json.dumps(row,ensure_ascii=True)+"\n"); journal.flush()
                budget -= row["usd_estimate"] + row["unsettled_reserve_usd"]
                print(model,feature,long,enabled,row["status"],row.get("error",""),round(row["usd_estimate"],4),flush=True)
                if row.get("error") in ("BUDGET_RESERVE","USAGE_UNAVAILABLE") or (
                    row.get("error","").startswith(("TURN_failed","thread/start:","initialize:")) and not row["usd_estimate"]):
                    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root",type=Path)
    parser.add_argument("--tag",required=True)
    parser.add_argument("--until",required=True)
    parser.add_argument("--models",nargs="+",choices=MODELS,default=list(MODELS))
    args = parser.parse_args()
    deadline = time.monotonic()+datetime.fromisoformat(args.until).timestamp()-time.time()
    kit = args.root/"release/MyCodexSetting-0.5.1/kit"
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        jobs=[pool.submit(run_model,args.root,kit,args.tag,m,deadline) for m in args.models]
        for job in jobs: job.result()
