import json
import os

from google import genai

from backend.app.schemas.extraction import (
    InvoiceExtraction,
    BalanceSheetExtraction,
    ProfitLossExtraction,
    CashFlowExtraction,
)


MODEL_NAME = "gemini-3.6-flash"


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    return genai.Client(api_key=api_key)


def clean_number(value):
    if isinstance(value, str):
        value = value.replace(",", "").strip()

        try:
            return float(value)
        except ValueError:
            return None

    if isinstance(value, (int, float)):
        return value

    return None


def clean_financial_data(data):
    for section in [
        "assets",
        "liabilities",
        "equity",
        "income",
        "expenses",
    ]:
        for item in data.get(section, []):
            item["current_period"] = clean_number(
                item.get("current_period")
            )
            item["previous_period"] = clean_number(
                item.get("previous_period")
            )

    for field in [
        "total_assets",
        "total_liabilities",
        "total_equity",
        "total_income",
        "total_expenses",
        "profit_before_tax",
        "tax_expense",
        "net_profit",
    ]:
        value = data.get(field)

        if isinstance(value, dict):
            value = value.get("current_period")

        data[field] = clean_number(value)

    return data


def extract_invoice(ocr_text: str) -> InvoiceExtraction:
    client = get_gemini_client()

    prompt = f"""
You are a document extraction system.

Extract information from the invoice OCR text below.

IMPORTANT RULES:
1. Extract only information supported by the OCR text.
2. Do not invent or guess missing values.
3. If a field cannot be determined reliably, use null.
4. Preserve numbers carefully.
5. Return ONLY valid JSON.
6. For line items, extract description, quantity, unit price and amount when available.
7. The currency should be the currency code or symbol shown on the document.

Return JSON using exactly this structure:

{{
    "invoice_number": null,
    "invoice_date": null,
    "vendor_name": null,
    "vendor_address": null,
    "vendor_tax_id": null,
    "customer_name": null,
    "customer_address": null,
    "currency": null,
    "line_items": [],
    "subtotal": null,
    "tax": null,
    "discount": null,
    "total": null,
    "payment_method": null,
    "reference_number": null,
    "raw_fields": {{}}
}}

OCR TEXT:
----------------
{ocr_text}
----------------
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    response_text = response.text.strip()

    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    data = json.loads(response_text)

    return InvoiceExtraction.model_validate(data)


def extract_balance_sheet(
    ocr_text: str
) -> BalanceSheetExtraction:

    client = get_gemini_client()

    prompt = f"""
You are a financial document extraction system.

Extract information from the Balance Sheet OCR text below.

IMPORTANT RULES:
1. Extract only information supported by the OCR text.
2. Do not invent, guess, or calculate missing values.
3. If a value cannot be determined reliably, use null.
4. Extract ALL meaningful visible balance-sheet line items.
5. Preserve current-period and previous-period values separately when shown.
6. Extract company name, statement date, currency, and units when available.
7. Extract total assets, total liabilities, and total equity when available.
8. Preserve financial line-item names as closely as possible.
9. Numbers must be returned as JSON numbers, NOT strings.
10. Do not include commas inside numbers.
11. If the document shows "8,923,441,607", return 8923441607.
12. Return ONLY valid JSON.

Return JSON using exactly this structure:

{{
    "company_name": null,
    "statement_date": null,
    "currency": null,
    "unit": null,
    "assets": [],
    "liabilities": [],
    "equity": [],
    "total_assets": null,
    "total_liabilities": null,
    "total_equity": null,
    "raw_fields": {{}}
}}

Each item inside assets, liabilities, and equity must use:

{{
    "name": null,
    "current_period": null,
    "previous_period": null
}}

For total_assets, total_liabilities and total_equity:
- Use a single numeric value for the current period.
- Do not return an object.
- If the value is not separately available, use null.

OCR TEXT:
----------------
{ocr_text}
----------------
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    response_text = response.text.strip()

    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    data = json.loads(response_text)

    data = clean_financial_data(data)

    return BalanceSheetExtraction.model_validate(data)


def extract_profit_loss(
    ocr_text: str
) -> ProfitLossExtraction:

    client = get_gemini_client()

    prompt = f"""
You are a financial document extraction system.

Extract information from the Profit and Loss statement OCR text below.

IMPORTANT RULES:
1. Extract only information supported by the OCR text.
2. Do not invent or guess missing values.
3. If a field cannot be determined reliably, use null.
4. Extract ALL meaningful visible income line items.
5. Extract ALL meaningful visible expense/expenditure line items.
6. Preserve current-period and previous-period values separately when shown.
7. Extract company name, statement date, currency, and units when available.
8. The statement may use labels such as "INCOME", "EXPENDITURE",
   "PROFIT", "Total", "Net profit for the year", etc.
9. Extract the explicitly printed total immediately following the
   INCOME section as total_income, even if only the current-period
   total is visible in OCR.
10. Extract the explicitly printed total immediately following the
    EXPENDITURE section as total_expenses, even if only the
    current-period total is visible in OCR.
11. If a total has no previous-period value visible in the OCR,
    return the current-period value and do not invent the previous value.
12. If the statement explicitly provides profit before tax, extract it.
13. If the statement does not explicitly provide profit before tax,
    use null. Do NOT calculate it.
14. If tax expense is explicitly shown, extract it.
15. Extract "Net profit for the year" as net_profit when present.
16. Do not confuse "Consolidated profit for the year attributable
    to the Group" with "Net profit for the year".
17. Preserve additional meaningful values such as minority interest,
    share in profits of associates, EPS, and appropriations in raw_fields.
18. Do not include commas inside numbers.
19. Do not calculate missing values.
20. Return ONLY valid JSON.

Return JSON using exactly this structure:

{{
    "company_name": null,
    "statement_date": null,
    "currency": null,
    "unit": null,
    "income": [],
    "expenses": [],
    "total_income": null,
    "total_expenses": null,
    "profit_before_tax": null,
    "tax_expense": null,
    "net_profit": null,
    "raw_fields": {{}}
}}

Each item inside income and expenses must use:

{{
    "name": null,
    "current_period": null,
    "previous_period": null
}}

For total_income, total_expenses, profit_before_tax,
tax_expense and net_profit:
- Use a single numeric value for the current period.
- Do not return an object.
- If the value is not explicitly available, use null.

OCR TEXT:
----------------
{ocr_text}
----------------
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    response_text = response.text.strip()

    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    data = json.loads(response_text)

    data = clean_financial_data(data)

    return ProfitLossExtraction.model_validate(data)
def extract_cash_flow(ocr_text: str) -> CashFlowExtraction:
    client = get_gemini_client()

    prompt = f"""
You are extracting data from a Cash Flow Statement.

Extract ALL meaningful visible information from the document.

Rules:
- Do not hallucinate or calculate values that are not explicitly present.
- If a value is missing, return null.
- Preserve current and previous comparative-period values when available.
- Extract operating activities.
- Extract investing activities.
- Extract financing activities.
- Extract foreign exchange effects when explicitly shown.
- Extract net change in cash when explicitly shown.
- Extract opening and closing cash balances when explicitly shown.
- Preserve additional meaningful fields in raw_fields.
- Numeric values must be numbers without commas.
- Keep negative values negative.
- Preserve the original meaning of each line item.

Return only data matching the CashFlowExtraction schema.

Document text:
{ocr_text}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": CashFlowExtraction,
        },
    )

    data = response.parsed

    if data is None:
        raise ValueError("Gemini returned no structured Cash Flow data")

    return clean_financial_data(data)