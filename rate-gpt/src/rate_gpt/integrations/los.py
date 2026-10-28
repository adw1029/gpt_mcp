"""Loan origination system (LOS): where submitted applications become real loans.

Services depend on the LoanOriginationSystem protocol. The demo backend fakes
loan IDs for local runs; the gateway backend creates loans through the DMS
partner gateway (create_loan -> update_loan -> finalize_loan).
"""
import re
import uuid
from typing import Any, Protocol

from rate_gpt.domain.applications import ApplicationDetails
from rate_gpt.integrations.dms_gateway import DmsGatewayClient

# Our field values -> Encompass values the gateway expects.
# TODO: confirm with the gateway team. The DMS doc only shows one example of each.
LOAN_PURPOSE = {
    "purchase": "Purchase",
    "refinance": "NoCash-Out Refinance",
    "cash_out_refinance": "Cash-Out Refinance",
}
REFINANCE_PURPOSE = {"refinance": "NoCashOut", "cash_out_refinance": "CashOut"}
PROPERTY_TYPE = {"single_family": "Detached", "condo": "Condominium", "townhouse": "Attached"}
OCCUPANCY = {"primary_residence": "PrimaryResidence", "second_home": "SecondHome", "investment": "Investor"}


class LoanOriginationSystem(Protocol):
    def create_loan(self, details: ApplicationDetails) -> str:
        """Create the loan and return its ID."""
        ...

    def update_loan(self, loan_id: str, details: ApplicationDetails) -> None: ...

    def finalize_loan(self, loan_id: str) -> None: ...


class DemoLoanOriginationSystem:
    """Stand-in for local runs and tests: hands out fake IDs, sends nothing anywhere."""

    def create_loan(self, details: ApplicationDetails) -> str:
        return str(uuid.uuid4())

    def update_loan(self, loan_id: str, details: ApplicationDetails) -> None:
        pass

    def finalize_loan(self, loan_id: str) -> None:
        pass


class GatewayLoanOriginationSystem:
    def __init__(self, gateway: DmsGatewayClient, company: str, company_eid: int) -> None:
        self._gateway = gateway
        self._company = company
        self._company_eid = company_eid

    def create_loan(self, details: ApplicationDetails) -> str:
        result = self._gateway.call("create_loan", create_loan_payload(details, self._company, self._company_eid))
        return result["data"]["loanId"]

    def update_loan(self, loan_id: str, details: ApplicationDetails) -> None:
        self._gateway.call("update_loan", update_loan_payload(loan_id, details, self._company))

    def finalize_loan(self, loan_id: str) -> None:
        self._gateway.call("finalize_loan", {"gr-loan-guid": loan_id})


def create_loan_payload(d: ApplicationDetails, company: str, company_eid: int) -> dict[str, Any]:
    return {
        "firstName": d.first_name,
        "lastName": d.last_name,
        "loanPurposeType": LOAN_PURPOSE[d.loan_purpose],
        "emailAddress": d.email,
        "mobilePhone": format_phone(d.phone),
        "company-name": company,
        "companyEID": company_eid,
    }


def update_loan_payload(loan_id: str, d: ApplicationDetails, company: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"grLoanGuid": loan_id, "company-name": company, "loanAmount": d.loan_amount}
    subject: dict[str, Any] = {
        "propertyType": PROPERTY_TYPE[d.property_type],
        "occupancyType": OCCUPANCY[d.occupancy],
        "city": d.property_city,
        "state": d.property_state,
        "zipCode": d.property_zip,
    }
    if d.loan_purpose == "purchase":
        down = d.property_value - d.loan_amount
        payload["purchasePriceAmount"] = d.property_value
        payload["downPaymentAmount"] = down
        payload["downPaymentPercent"] = round(down / d.property_value * 100, 2)
    else:
        subject["refinancePurposeType"] = REFINANCE_PURPOSE[d.loan_purpose]
        subject["appraisedValue"] = d.property_value
    payload["subjectProperty"] = subject
    if d.employer_name:
        payload["employment"] = [
            {
                "id": "Employment/0",
                "employerName": d.employer_name,
                "currentEmploymentIndicator": True,
                "basePayAmount": d.monthly_base_income,
                "owner": "Borrower",
            }
        ]
    return payload


def format_phone(phone: str | None) -> str | None:
    """Normalize to the gateway's (949)-532-4567 format."""
    if phone is None:
        return None
    digits = re.sub(r"\D", "", phone)[-10:]
    return f"({digits[:3]})-{digits[3:6]}-{digits[6:]}"
