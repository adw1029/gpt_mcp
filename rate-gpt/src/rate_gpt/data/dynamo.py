"""DynamoDB storage for deployed environments. One item per application, keyed by `id`."""
from typing import Any

from rate_gpt.domain.applications import LoanApplication


class DynamoApplicationRepository:
    def __init__(self, table: Any) -> None:
        self._table = table

    @classmethod
    def create(cls, table_name: str) -> "DynamoApplicationRepository":
        import boto3

        return cls(boto3.resource("dynamodb").Table(table_name))

    def get(self, application_id: str) -> LoanApplication | None:
        item = self._table.get_item(Key={"id": application_id.strip().upper()}).get("Item")
        return LoanApplication.model_validate_json(item["data"]) if item else None

    def save(self, application: LoanApplication) -> None:
        # The full record is stored as JSON; stage and timestamps are copied out for querying.
        self._table.put_item(
            Item={
                "id": application.id,
                "stage": application.stage.value,
                "created_at": application.created_at.isoformat(),
                "updated_at": application.updated_at.isoformat(),
                "data": application.model_dump_json(),
            }
        )
