import hashlib
import json
import os
from typing import Dict, Any, List
from pathlib import Path

class LedgerChain:
    """
    Kriptográfiai SHA-256 Hash Chain az események (Events) naplózására.
    """
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.chain_file = storage_path / "chain.json"
        self.chain: List[Dict[str, Any]] = []
        self._load_chain()

    def _load_chain(self):
        if self.chain_file.exists():
            with open(self.chain_file, "r", encoding="utf-8") as f:
                self.chain = json.load(f)
        else:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._append_genesis_block()

    def _append_genesis_block(self):
        genesis = {
            "index": 0,
            "previous_hash": "0" * 64,
            "event_id": "genesis",
            "event_type": "genesis",
            "timestamp": 0.0,
            "hash": ""
        }
        genesis["hash"] = self._compute_hash(genesis)
        self.chain.append(genesis)
        self._save_chain()

    def _compute_hash(self, block: Dict[str, Any]) -> str:
        block_string = json.dumps({
            "index": block.get("index"),
            "previous_hash": block.get("previous_hash"),
            "event_id": block.get("event_id"),
            "event_type": block.get("event_type"),
            "timestamp": block.get("timestamp")
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def append_event(self, event: Any) -> str:
        last_block = self.chain[-1]

        new_block = {
            "index": last_block["index"] + 1,
            "previous_hash": last_block["hash"],
            "event_id": event.event_id,
            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
            "timestamp": event.timestamp,
            "hash": ""
        }

        new_block["hash"] = self._compute_hash(new_block)
        self.chain.append(new_block)
        self._save_chain()
        return new_block["hash"]

    def _save_chain(self):
        with open(self.chain_file, "w", encoding="utf-8") as f:
            json.dump(self.chain, f, indent=2)

    def verify_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            if current["previous_hash"] != previous["hash"]:
                return False

            if current["hash"] != self._compute_hash(current):
                return False
        return True
