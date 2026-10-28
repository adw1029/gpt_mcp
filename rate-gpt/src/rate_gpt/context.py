"""Shared dependencies handed to every module at registration time."""
from dataclasses import dataclass

from rate_gpt.config import Settings
from rate_gpt.data import ApplicationRepository, build_application_repository
from rate_gpt.integrations import BorrowerAccounts, LoanOriginationSystem, build_integrations


@dataclass
class AppContext:
    settings: Settings
    applications: ApplicationRepository
    los: LoanOriginationSystem
    accounts: BorrowerAccounts

    @classmethod
    def from_settings(cls, settings: Settings) -> "AppContext":
        integrations = build_integrations(settings)
        return cls(
            settings=settings,
            applications=build_application_repository(settings),
            los=integrations.los,
            accounts=integrations.accounts,
        )
