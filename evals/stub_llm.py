"""
A fake OpenAI-compatible LLM server used only in CI.
It looks at the text the app sends and replies with the recorded answer from golden_set.json. No real model, so it is instant and free.
"""

import json 
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))

# Load only the cases that have a recorded answer.
with open(os.path.join(HERE, "golden_set.json"), encoding="utf-8") as f:
    CASES = [case for case in json.load(f) if "recorded_output" in case]

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read the JSON body the app sent.
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")

        prompt_text = " ".join(str(m.get("content", "")) for m in body.get("messages", []))

        answer = None 
        for case in CASES:
            if case["text"] in prompt_text:
                answer = case["recorded_output"]
                break

        if answer is None:
            self.send_response(404)
            self.end_headers()
            return 

        reply = {
            "id": "stub",
            "object": "chat.completion",
            "model": body.get("model", "stub-model"),
            "choices": [
                {
                    "index": 0, 
                    "finish_reason" : "stop",
                    "message": {
                        "role": "assistant",
                        "content": answer
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }

        data = json.dumps(reply).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any):
        # Keep CI logs quiet: do not print one line per request.
        pass

if __name__ == "__main__":
    # Listen only on this machine, port 9999.
    HTTPServer(("127.0.0.1", 9999), Handler).serve_forever()