from typing_extensions import Protocol


class EmailService(Protocol):
    async def send_payment_failure_email(self, tenant: str) -> None: ...
