from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional
from kernel.event_bus.bus import EventBus
from kernel.event_bus.events import Event, EventType
from sdk.provider_adapter import AIProvider, MockProviderAdapter

class BaseAgentSDK(ABC):
    def __init__(self, name: str, bus: EventBus, provider: Optional[AIProvider] = None):
        self.name = name
        self.bus = bus
        self.provider = provider or MockProviderAdapter()
        self.logger = logging.getLogger(f"Agent.{name}")
        self.register_subscriptions()

    @abstractmethod
    def register_subscriptions(self) -> None:
        pass

    @abstractmethod
    async def process_event(self, event: Event) -> None:
        pass

    async def emit_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        correlation_id: str,
        sender: Optional[str] = None
    ) -> Event:
        evt = Event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            sender=sender or self.name
        )
        self.logger.debug(f"Emitting {event_type} (correlation={correlation_id})")
        await self.bus.publish(evt)
        return evt
