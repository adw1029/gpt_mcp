Auth for MCP DEV  

Endpoint: https://gr.oktapreview.com/oauth2/aus2aagfx9cSr6Aag0h8/v1/token 

Client ID: 0oa2n709uihEeYNNz0h8 

Client Secret: yLw55z2miFqmNIM6yseaHvSgVpBMacHUPZNATHu8sVXwUCcDkw11AJui_E9b2iai 

Scope: api.all.digital-mortgage-systems-mcp 

 

Tool to create loan 

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/create_loan 

With a payload structure of: 

{ 

"firstName": "Andy", 

"lastName": "America", 

"loanPurposeType": "NoCash-Out Refinance", 

"emailAddress": "andyamerica@gmail.com", 

"mobilePhone": "(949)-532-4567", 

"company-name": "owning", 

"companyEID": 5, 

} 

 

On success, this will return you with the GR loan guid, sample response:  

{ 

"tool": "create_loan", 

"result": "{\n \"success\": true,\n \"data\": {\n \"loanId\": \"146efa44-b389-49c9-9749-4640ec8675af\"\n }\n}", 

"success": true, 

"request_id": "ecf1f66c-94ab-4026-9078-d52801a77967" 

} 

 

 

Tool to create borrower MYA account  

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/create_borrower_entity 

With a payload structure of:  

{ 

"email-address": { 

"primary": "andy-america-TEST1026@gmail.com" 

}, 

"identifier": { 

"okta-id": null 

}, 

"name": { 

"first": "Andy", 

"last": "America" 

}, 

"phone": { 

"home": "(949)-704-5667" 

}, 

"language-preference": "en", 

"company-name": "owning" 

} 

 

On success, this will return you the MYA borrower guid which you will use in the payload when creating the Okta account to link them together: 

{ 

"tool": "create_borrower_entity", 

"result": "{\n \"success\": true,\n \"data\": {\n \"id\": \"3d29693f-fa35-498b-9a29-4fc592afaa9a\",\n \"already-exists\": true\n }\n}", 

"success": true, 

"request_id": "f25d8a7c-10c3-4046-877a-0acf49426f65" 

} 

 

 

Tool to create borrower Okta account 

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/create_okta_user 

With a payload structure of: 

{ 

"profile": { 

"firstName": "Andy", 

"lastName": "America", 

"email": "andy-america-TEST1026@gmail.com", 

"login": "andy-america-TEST1026@gmail.com", 

"mobilePhone": "(949)-704-5667", 

"borrowerID": “3d29693f-fa35-498b-9a29-4fc592afaa9a" 

}, 

"credentials": { 

"password": { 

"value": "Password123!3434" 

}  

} 

} 

 

On success, this will return you a big chunk, none of which is needed further down the line: 

{ 

"tool": "create_okta_user", 

"result": "{\n \"success\": true,\n \"data\": {\n \"id\": \"00u15b09yqgfj0vTu1d8\",\n \"status\": \"ACTIVE\",\n...", 

"success": true, 

"request_id": "e844f204-049f-49b1-9c11-4e54c8d2e412" 

} 

 

 

Tool to patch application fields on a loan 

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/update_loan 

This below payload shows all of the possible fields/properties that can be patched for a loan involving questions asked throughout the application process. This is a full list of patchable fields and their formats, you can pass as little or as many fields as you would like in a single patch request (grLoanGuid and company-name are always required): 

{ 

"grLoanGuid": "146efa44-b389-49c9-9749-4640ec8675af", 

"company-name": "gri", 

"loanAmount": 640000, 

"purchasePriceAmount": 800000, 

"downPaymentAmount": 160000, 

"downPaymentPercent": 20, 

"borrowerRequestedLoanAmount": 420000, 

"borrowerESignConsentReceivedDate": "10/26/2026", 

"coBorrowerESignConsentReceivedDate": "10/26/2026", 

 

"borrower": { 

"middleName": "A", 

"suffixToName": "Jr", 

"nickname": "Alex", 

"languagePreference": "English", 

"languageCodeOtherDescription": "Portuguese", 

"maritalStatusType": "Married", 

"dependentCount": 2, 

"dependentsAgesDescription": "8,12", 

"selfDeclaredMilitaryServiceIndicator": true, 

"activeDuty": true, 

"reserveNationalGuardReserveActivated": false, 

"veteran": false, 

"spousalVaBenefitsEligibilityIndicator": true, 

"militaryBranchOfService": "Army", 

"authorizedCreditReportIndicator": true, 

"creditReportAuthorizationMethod": "Internet", 

"dateAuthorizedCreditReport": "2026-10-26T19:00:00.000Z" 

}, 

 

"coborrower": { 

"middleName": "B", 

"suffixToName": "Sr", 

"nickname": "Sam", 

"languagePreference": "Spanish", 

"languageCodeOtherDescription": "Portuguese", 

"mobilePhone": "3105550199", 

"emailAddressText": "sam@example.com", 

"maritalStatusType": "Married", 

"dependentCount": 1, 

"dependentsAgesDescription": "5", 

"selfDeclaredMilitaryServiceIndicator": true, 

"activeDuty": false, 

"reserveNationalGuardReserveActivated": false, 

"veteran": true, 

"spousalVaBenefitsEligibilityIndicator": true, 

"militaryBranchOfService": "Navy", 

"authorizedCreditReportIndicator": true, 

"creditReportAuthorizationMethod": "Internet", 

"dateAuthorizedCreditReport": "2026-10-26T19:00:00.000Z" 

}, 

 

"borrowerMonthlyExpenses": { 

"rentAmount": 2500, 

"realEstateTaxAmount": 450, 

"mortgageInsuranceAmount": 120, 

"homeownersAssociationDuesAndCondoFeesAmount": 75 

}, 

 

"coborrowerMonthlyExpenses": { 

"rentAmount": 1800, 

"realEstateTaxAmount": 300, 

"mortgageInsuranceAmount": 90, 

"homeownersAssociationDuesAndCondoFeesAmount": 50 

}, 

 

"residences": [ 

{ 

"id": "Residence/0", 

"uRLA2020StreetAddress": "123 Main St", 

"addressCity": "Los Angeles", 

"addressState": "CA", 

"addressCounty": "Los Angeles", 

"addressPostalCode": "90001", 

"addressUnitDesignatorType": "Apt", 

"addressUnitIdentifier": "4B", 

"durationTermYears": 3, 

"durationTermMonths": 2, 

"residencyBasisType": "Own", 

"residencyType": "Current", 

"applicantType": "Borrower" 

}, 

{ 

"id": "Residence/2", 

"uRLA2020StreetAddress": "456 Oak Ave", 

"addressCity": "Pasadena", 

"addressState": "CA", 

"addressCounty": "Los Angeles", 

"addressPostalCode": "91101", 

"addressUnitDesignatorType": "Unit", 

"addressUnitIdentifier": "12", 

"durationTermYears": 1, 

"durationTermMonths": 6, 

"residencyBasisType": "Rent", 

"residencyType": "Current", 

"applicantType": "CoBorrower" 

} 

], 

 

"subjectProperty": { 

"propertyType": "Detached", 

"occupancyType": "PrimaryResidence", 

"city": "Irvine", 

"state": "CA", 

"zipCode": "92618", 

 

"refinancePurposeType": "NoCashOut", 

"streetAddress": "789 Harbor Blvd", 

"unitType": "Apt", 

"addressUnitIdentifier": "2A", 

"county": "Orange", 

"refinancePropertyOriginalCostAmount": 500000, 

"appraisedValue": 650000 

}, 

 

"employment": [ 

{ 

"id": "Employment/0", 

"employerName": "Acme Corp", 

"positionDescription": "Engineer", 

"addressCity": "Los Angeles", 

"addressState": "CA", 

"phoneNumber": "3105550100", 

"employmentStartDate": "2020-03-15", 

"endDate": "2024-01-31", 

"currentEmploymentIndicator": true, 

"selfEmployedIndicator": false, 

"basePayAmount": 10000, 

"bonusAmount": 500, 

"commissionsAmount": 1000, 

"overtimeAmount": 400, 

"owner": "Borrower" 

}, 

{ 

"id": "Employment/1", 

"employerName": "Northwind LLC", 

"positionDescription": "Designer", 

"addressCity": "Pasadena", 

"addressState": "CA", 

"phoneNumber": "6265550144", 

"employmentStartDate": "2019-06-01", 

"endDate": "2023-12-15", 

"currentEmploymentIndicator": false, 

"selfEmployedIndicator": true, 

"basePayAmount": 8000, 

"bonusAmount": 250, 

"commissionsAmount": 750, 

"overtimeAmount": 200, 

"owner": "CoBorrower" 

} 

], 

 

"otherIncomeSources": [ 

{ "id": "OtherIncomeSource/0", "description": "Pension", "monthlyAmount": 500, "owner": "Borrower" }, 

{ "id": "OtherIncomeSource/1", "description": "SocialSecurity", "monthlyAmount": 400, "owner": "CoBorrower" }, 

{ "id": "OtherIncomeSource/2", "description": "Other", "otherDescription": "Royalty income", "monthlyAmount": 250, "owner": "Borrower" }, 

], 

 

"assets": [ 

{ 

"id": "Asset/18", 

"assetType": "CheckingAccount", 

"holderName": "Chase", 

"owner": "Borrower", 

"total": 15000 

}, 

{ 

"id": "Asset/22", 

"assetType": "SavingsAccount", 

"holderName": "Wells Fargo", 

"owner": "CoBorrower", 

"total": 22000 

}, 

{ 

"id": "Asset/26", 

"assetType": "CheckingAccount", 

"holderName": "Bank of America", 

"owner": "Both", 

"total": 8000 

} 

] 

} 

 

Some notes on the other income and asset ID fields since they are a bit unintuitive since these are lists and not just a single field. For other income, the id will simply be “OtherIncomeSource/n”. N will start at 0, and increase by 1 for each additional other income source, regardless of if it is the borrower or coborrower’s. If the income source is denoted as “Other”, the “otherDescription” field allows the borrower to explain further. Assets are a little trickier, the ID follows the formula: 

Asset/{18 + 4 × (position − 1)} 

Asset 

Id 

1st 

Asset/18 

2nd 

Asset/22 

3rd 

Asset/26 

nth 

Asset/{18 + 4(n−1)} 

 

Regardless of whether it is the borrower/coborrower/both who own the asset. Although this is a patching tool, this also allows you to add new income sources and assets since they are list objects. 

 

 

Tool to finalize a loan 

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/finalize_loan 

With a payload structure of: 

{ 

"gr-loan-guid": "d464735c-9700-4f70-a95e-14e0a4e4de6d" 

} 

 

The field in the payload is the GR loan guid you got when you created the loan. On success, you will be a response like: 
{ 

"tool": "finalize_loan", 

"result": "{\n \"success\": true,\n \"message\": \"Lead with GUID d464735c-9700-4f70-a95e-14e0a4e4de6d finalized successfully.\"\n}", 

"success": true, 

"request_id": "56d3e9e8-9ebd-4016-9274-f883e3c93fe0" 

} 

 

Tool to get borrower tasks on a loan 

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/get_tasks 

With a payload structure of: 

{ 

"loan-id": "7cfd9cd7-1b86-4406-8d8f-98e224bac28e", 

"company": "gri" 

} 

 

Note: the loan-id passed cannot be the GR loan id returned by the create loan tool, it must be either the loan number or the encompass loan number. Reference the tool below this to get those properties for your use. 

 

The response will contain a list of task objects, and will return every single borrower task that was on the loan, including hidden or completed tasks. To filter the response to just be incomplete tasks on your end, you will have to omit tasks with property “task-completed”: true or “task-removed”: true 

 

 

Tool to fetch loan properties 

POST https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools/get_oneloan_properties 

With a payload structure of:  

{ 

"loan_identifier": "424cd357-353a-4268-8298-c166d7a068fc", 

"company": "gri", 

"requestedProperties": ["364", "GUID"] 

} 

 

The above example requests fields 364 (loan number) and GUID (encompass loan guid). You can pass any other encompass field ids as well. If you omit requestedProperties, the entire oneloan object response will be passed back. The response will look like this: 

{ 

"tool": "get_oneloan_properties", 

"result": "{\n \"success\": true,\n \"data\": {\n \"364\": \"265195401DEV\",\n \"GUID\": \"7cfd9cd7-1b86-4406-8d8f-98e224bac28e\"\n }\n}", 

"success": true, 

"request_id": "e5ab91fb-e7e3-4d7f-b85e-c0723aa9175c" 

} 

 

Check Application Status 

TBD 

 

 

 

 

 

 

 

 