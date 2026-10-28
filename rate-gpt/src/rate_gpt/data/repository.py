from typing import Protocol

from rate_gpt.domain.applications import LoanApplication


class ApplicationRepository(Protocol):
    def get(self, application_id: str) -> LoanApplication | None: ...

    def save(self, application: LoanApplication) -> None: ...
