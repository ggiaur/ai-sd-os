import asyncio
import logging
from typing import Callable, Awaitable, Dict, List, Optional, TYPE_CHECKING
from kernel.event_bus.events import Event, EventType
from contracts.events.registry import validate_event_payload
from kernel.contracts.validator import ContractValidationError

if TYPE_CHECKING:
    from kernel.ledger.ledger_chain import LedgerChain

logger = logging.getLogger("EventBus")

Handler = Callable[[Event], Awaitable[None]]

class EventBus:
    def __init__(self, ledger: Optional["LedgerChain"] = None) -> None:
        self._subscribers: Dict[EventType, List[Handler]] = {}
        self._global_subscribers: List[Handler] = []
        self._history: List[Event] = []
        self.ledger = ledger

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Handler) -> None:
        self._global_subscribers.append(handler)

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        logger.debug(f"[EventBus] Publishing {event.event_type} (id={event.event_id})")

        try:
            validate_event_payload(event)
        except ContractValidationError as e:
            logger.warning(f"[EventBus] Contract mismatch for {event.event_type}: {e}")

        if self.ledger is not None:
            self.ledger.append_event(event)

        handlers = list(self._subscribers.get(event.event_type, [])) + list(self._global_subscribers)
        for h in handlers:
            try:
                if asyncio.iscoroutinefunction(h):
                    await h(event)
                else:
                    h(event)
            except Exception as e:
                # Hibaizoláció: egy elbukott handler nem állíthatja meg a többi
                # feliratkozó feldolgozását, sem az esemény-lánc integritását.
                logger.error(f"Error handling event {event.event_type} in {h}: {e}", exc_info=True)

    @property
    def history(self) -> List[Event]:
        return list(self._history)
