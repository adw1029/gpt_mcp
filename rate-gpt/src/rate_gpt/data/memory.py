"""In-process storage for local development and tests. State resets on restart."""
import json
from importlib import resources

from rate_gpt.domain.applications import LoanApplication


class InMemoryApplicationRepository:
    def __init__(self) -> None:
        self._items: dict[str, LoanApplication] = {}

    @classmethod
    def create(cls, seed: bool) -> "InMemoryApplicationRepository":
        repo = cls()
        if seed:
            raw = resources.files("rate_gpt.data").joinpath("seed/applications.json").read_text()
            for item in json.loads(raw):
                repo.save(LoanApplication.model_validate(item))
        return repo

    def get(self, application_id: str) -> LoanApplication | None:
        item = self._items.get(application_id.strip().upper())
        # Hand out copies so callers can't mutate stored state without save().
        return item.model_copy(deep=True) if item else None

    def save(self, application: LoanApplication) -> None:
        self._items[application.id] = application.model_copy(deep=True)
