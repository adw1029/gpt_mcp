"""Data access. Modules depend on the repository protocols here, never on a concrete backend."""
from rate_gpt.config import Settings
from rate_gpt.data.repository import ApplicationRepository


def build_application_repository(settings: Settings) -> ApplicationRepository:
    match settings.data_backend:
        case "memory":
            from rate_gpt.data.memory import InMemoryApplicationRepository

            return InMemoryApplicationRepository.create(seed=settings.seed_demo_data)
        case "dynamodb":
            from rate_gpt.data.dynamo import DynamoApplicationRepository

            return DynamoApplicationRepository.create(settings.applications_table)
        case other:
            raise ValueError(f"Unknown data backend: {other!r}")
