from pathlib import Path

import pytest

from kernel.event_bus.bus import EventBus
from kernel.ledger.ledger_chain import LedgerChain, GENESIS_HASH
from kernel.ledger.replay_engine import SemanticReplayEngine
from kernel.event_bus.events import Event, EventType


def _make_event(sender="TestAgent"):
    return Event(event_type=EventType.SYSTEM_INITIALIZED, payload={"x": 1}, sender=sender)


# --- LedgerChain ----------------------------------------------------------

def test_ledger_chain_first_block_links_to_genesis(tmp_path):
    ledger = LedgerChain(tmp_path / "chain.json")
    block = ledger.append_event(_make_event())

    assert block.sequence_number == 1
    assert block.previous_hash == GENESIS_HASH


def test_ledger_chain_links_consecutive_blocks(tmp_path):
    ledger = LedgerChain(tmp_path / "chain.json")
    b1 = ledger.append_event(_make_event())
    b2 = ledger.append_event(_make_event())

    assert b2.previous_hash == b1.current_hash
    assert ledger.verify_integrity() is True


def test_ledger_chain_detects_tampering(tmp_path):
    ledger = LedgerChain(tmp_path / "chain.json")
    ledger.append_event(_make_event())
    ledger.append_event(_make_event())

    # Simulate tampering with a stored block.
    ledger.chain[0].current_hash = "deadbeef" * 8

    assert ledger.verify_integrity() is False


@pytest.mark.asyncio
async def test_event_bus_appends_every_published_event_to_ledger(tmp_path):
    """Integration point: the bus, not just the ledger in isolation, must
    actually wire every publish() into the hash chain."""
    ledger = LedgerChain(tmp_path / "chain.json")
    bus = EventBus(ledger=ledger)

    await bus.publish(Event(event_type=EventType.SPEC_CREATED, payload={"spec": {}, "project_root": "."}))
    await bus.publish(Event(event_type=EventType.LESSONS_LEARNED_UPDATED, payload={"sprint_id": "SPRINT-001"}))

    assert len(ledger) == 2
    assert ledger.verify_integrity() is True


def test_ledger_chain_persists_and_reloads(tmp_path):
    storage = tmp_path / "chain.json"
    ledger = LedgerChain(storage)
    ledger.append_event(_make_event())
    ledger.append_event(_make_event())

    reloaded = LedgerChain(storage)

    assert len(reloaded) == 2
    assert reloaded.verify_integrity() is True


# --- SemanticReplayEngine ---------------------------------------------------

def test_ast_equivalence_true_for_formatting_only_differences():
    original = "def f(x):\n    return x + 1\n"
    reformatted = "def f(x):\n\n    return x+1\n"

    assert SemanticReplayEngine.verify_ast_equivalence(original, reformatted) is True


def test_ast_equivalence_false_for_actual_logic_difference():
    original = "def f(x):\n    return x + 1\n"
    different = "def f(x):\n    return x - 1\n"

    assert SemanticReplayEngine.verify_ast_equivalence(original, different) is False


def test_ast_equivalence_false_for_syntax_error():
    original = "def f(x):\n    return x + 1\n"
    broken = "def f(x):\n    return x +\n"

    assert SemanticReplayEngine.verify_ast_equivalence(original, broken) is False


def test_is_semantically_equivalent_falls_back_to_test_pass(tmp_path):
    (tmp_path / "test_dummy.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    # AST differs (different logic), but the fallback test suite passes.
    result = SemanticReplayEngine.is_semantically_equivalent(
        original_code="def f():\n    return 1\n",
        replayed_code="def f():\n    return 2\n",
        workspace_path=tmp_path,
        test_command="python3 -m pytest -q",
    )
    assert result is True
