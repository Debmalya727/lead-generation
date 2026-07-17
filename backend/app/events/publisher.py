class EventPublisher:
    """
    Interface for dispatching platform events to registers and queues.
    """
    async def publish(self, event_name: str, payload: dict) -> None:
        pass
