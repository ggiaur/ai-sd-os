import pytest
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from kernel.ledger.ledger_chain import LedgerChain
from kernel.ledger.replay_engine import SemanticReplayEngine


def test_ledger_chain_hash_integrity(tmp_path):
    ledger = LedgerChain(tmp_path / "chain.json")
    ledger.append_event(Event(event_type=EventType.SPEC_CREATED, payload={"a": 1}))
    ledger.append_event(Event(event_type=EventType.WORKPACKAGE_CREATED, payload={"b": 2}))

    assert len(ledger) == 2
    assert ledger.verify_integrity() is True

    # Reload from disk and verify the chain survives a round trip
    reloaded = LedgerChain(tmp_path / "chain.json")
    assert len(reloaded) == 2
    assert reloaded.verify_integrity() is True


def test_ledger_chain_tamper_detection(tmp_path):
    ledger = LedgerChain(tmp_path / "chain.json")
    ledger.append_event(Event(event_type=EventType.SPEC_CREATED, payload={"a": 1}))
    ledger.append_event(Event(event_type=EventType.WORKPACKAGE_CREATED, payload={"b": 2}))

    ledger.chain[0].current_hash = "tampered"
    assert ledger.verify_integrity() is False


@pytest.mark.asyncio
async def test_event_bus_appends_every_published_event_to_ledger(tmp_path):
    ledger = LedgerChain(tmp_path / "chain.json")
    bus = EventBus(ledger=ledger)

    await bus.publish(Event(event_type=EventType.SPEC_CREATED, payload={"spec": {}, "project_root": "."}))
    await bus.publish(Event(event_type=EventType.LESSONS_LEARNED_UPDATED, payload={"sprint_id": "SPRINT-001"}))

    assert len(ledger) == 2
    assert ledger.verify_integrity() is True


def test_semantic_replay_ast_equivalence():
    original = "def add(a, b):\n    return a + b\n"
    identical = "def add(a, b):\n    return a + b\n"
    different = "def add(a, b):\n    return a - b\n"

    assert SemanticReplayEngine.verify_ast_equivalence(original, identical) is True
    assert SemanticReplayEngine.verify_ast_equivalence(original, different) is False
    assert SemanticReplayEngine.verify_ast_equivalence(original, "def add(a, b:\n") is False
