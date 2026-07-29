import asyncio
import logging
from typing import Callable, Awaitable, Dict, List
from kernel.event_bus.events import Event, EventType

logger = logging.getLogger("EventBus")

Handler = Callable[[Event], Awaitable[None]]

class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[Handler]] = {}
        self._global_subscribers: List[Handler] = []
        self._history: List[Event] = []

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Handler) -> None:
        self._global_subscribers.append(handler)

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        logger.debug(f"[EventBus] Publishing {event.event_type} (id={event.event_id})")

        handlers = list(self._subscribers.get(event.event_type, [])) + list(self._global_subscribers)
        for h in handlers:
            try:
                if asyncio.iscoroutinefunction(h):
                    await h(event)
                else:
                    h(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type} in {h}: {e}", exc_info=True)
                raise

    @property
    def history(self) -> List[Event]:
        return list(self._history)
