import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from core.utils.fields import datetime_factory


async def _noop_sender(metric: "Metric", *args: Any, **kwargs: Any):
    logging.getLogger(__name__).debug("Noop sender for metric %s: %s", metric.name, metric.gauge or metric.counter)


class Metric(BaseModel):
    name: str
    timestamp: datetime = Field(default_factory=datetime_factory)
    tags: dict[str, int | str | float | bool] = Field(default_factory=dict)

    gauge: float | None = None
    counter: int | None = None

    sender: ClassVar[Callable[["Metric"], Awaitable[None]]] = _noop_sender

    async def send(self):
        await self.__class__.sender(self)

    @classmethod
    def reset_sender(cls):
        cls.sender = _noop_sender
