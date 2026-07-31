import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel
from kernel.event_bus.events import Event

GENESIS_HASH = "0" * 64


class LedgerBlock(BaseModel):
    sequence_number: int
    previous_hash: str
    current_hash: str
    event_data: Dict[str, Any]


class LedgerChain:
    """Kriptográfiai SHA-256 hash-lánc az EventBus-on áthaladó eseményekről.

    Minden EventBus.publish() hívás egy blokkot ír a láncba, így a
    .ai-sd-os/ledger/chain.json a rendszer teljes, manipuláció-ellenőrizhető
    audit-naplója lesz (SYSTEM_CONSTITUTION L2.1 garancia).
    """

    def __init__(self, storage_path: Path = Path("./.ai-sd-os/ledger/chain.json")):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.chain: List[LedgerBlock] = self._load_chain()

    def _load_chain(self) -> List[LedgerBlock]:
        if not self.storage_path.exists():
            return []
        raw = self.storage_path.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        return [LedgerBlock(**block) for block in data]

    def _save_chain(self) -> None:
        data = [block.model_dump(mode="json") for block in self.chain]
        self.storage_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def append_event(self, event: Event) -> LedgerBlock:
        previous_hash = self.chain[-1].current_hash if self.chain else GENESIS_HASH
        seq = len(self.chain) + 1

        event_data = event.model_dump(mode="json")
        payload_bytes = json.dumps(event_data["payload"], sort_keys=True, default=str).encode("utf-8")
        current_hash = hashlib.sha256(
            f"{previous_hash}{event.timestamp}{event.sender}{event.event_type.value}".encode("utf-8")
            + payload_bytes
        ).hexdigest()

        block = LedgerBlock(
            sequence_number=seq,
            previous_hash=previous_hash,
            current_hash=current_hash,
            event_data=event_data,
        )
        self.chain.append(block)
        self._save_chain()
        return block

    def verify_integrity(self) -> bool:
        for i in range(1, len(self.chain)):
            if self.chain[i].previous_hash != self.chain[i - 1].current_hash:
                return False
        return True

    def __len__(self) -> int:
        return len(self.chain)
