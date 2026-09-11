import json
import os

import pymupdf
from google import genai
from google.genai import types

from backend.app.schemas.extraction import (
    InvoiceExtraction,
    BalanceSheetExtraction,
    ProfitLossExtraction,
    CashFlowExtraction,
)


# =============================================================
# GEMINI CONFIGURATION
# =============================================================

MODEL_NAME = "gemini-3.6-flash"


def get_gemini_client():
    """
    Create and return the Gemini client.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set"
        )

    return genai.Client(
        api_key=api_key
    )


# =============================================================
# NUMBER CLEANING
# =============================================================

def clean_number(value):
    """
    Convert a value into a numeric type.

    Handles:
    - integers
    - floats
    - numeric strings
    - comma-separated numbers
    - accounting-style negative numbers
    """

    if isinstance(value, str):

        value = (
            value
            .replace(",", "")
            .replace(" ", "")
            .strip()
        )

        # Handle accounting-style negatives:
        # (12345) -> -12345
        if (
            value.startswith("(")
            and value.endswith(")")
        ):
            value = "-" + value[1:-1]

        try:
            return float(value)

        except ValueError:
            return None

    if isinstance(value, (int, float)):
        return value

    return None


# =============================================================
# FINANCIAL DATA CLEANING
# =============================================================

def clean_financial_data(data):
    """
    Clean numeric values in financial extraction data.

    This function expects a dictionary.
    """

    if not isinstance(data, dict):
        return data

    for section in [
        "assets",
        "liabilities",
        "equity",
        "income",
        "expenses",
        "operating_activities",
        "investing_activities",
        "financing_activities",
    ]:

        for item in data.get(section, []):

            if not isinstance(item, dict):
                continue

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
        "foreign_exchange_effect",
        "net_cash_change",
        "opening_cash_balance",
        "closing_cash_balance",
    ]:

        value = data.get(field)

        if isinstance(value, dict):

            if value.get("current_period") is not None:
                value = value.get(
                    "current_period"
                )

            elif value.get("current") is not None:
                value = value.get(
                    "current"
                )

            else:
                value = None

        data[field] = clean_number(value)

    return data


# =============================================================
# JSON RESPONSE PARSER
# =============================================================

def parse_json_response(
    response_text: str,
) -> dict:
    """
    Convert Gemini JSON response into a Python dictionary.
    """

    if not response_text:
        raise ValueError(
            "Gemini returned an empty response"
        )

    response_text = response_text.strip()

    if response_text.startswith("```"):

        response_text = response_text.replace(
            "```json",
            "",
            1,
        )

        response_text = response_text.replace(
            "```",
            "",
        )

        response_text = response_text.strip()

    return json.loads(response_text)


# =============================================================
# INVOICE EXTRACTION
# =============================================================

def extract_invoice(
    ocr_text: str,
) -> InvoiceExtraction:

    client = get_gemini_client()

    prompt = f"""
You are an expert document extraction system.

Extract information from the invoice OCR text below.

IMPORTANT RULES:

1. Extract ONLY information supported by the OCR text.

2. Do not invent or guess missing values.

3. If a field cannot be determined reliably, use null.

4. Extract ALL meaningful visible invoice information.

5. Preserve invoice numbers, dates and financial values
   carefully.

6. Extract vendor and customer information when available.

7. Extract vendor tax ID when available.

8. Extract currency when explicitly shown.

9. Extract every visible line item.

10. For every line item, extract:
    - description
    - quantity
    - unit price
    - amount

11. Do not calculate missing values.

12. Preserve the values as they appear in the OCR.

13. Extract subtotal, tax, discount and total when available.

14. Extract payment method when available.

15. Extract reference number when available.

16. Numbers must be JSON numbers, not strings.

17. Do not include commas inside JSON numbers.

18. Return ONLY valid JSON.

Return exactly:

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
        contents=prompt,
    )

    data = parse_json_response(
        response.text
    )

    return InvoiceExtraction.model_validate(
        data
    )


# =============================================================
# BALANCE SHEET EXTRACTION
# =============================================================

def extract_balance_sheet(
    ocr_text: str,
    file_bytes: bytes | None = None,
    filename: str | None = None,
) -> BalanceSheetExtraction:

    client = get_gemini_client()

    prompt = f"""
You are an expert financial-document extraction system.

You are extracting a Balance Sheet from a financial document.

You have TWO sources of information:

1. OCR text
2. The original document page image

The ORIGINAL DOCUMENT IMAGE is the PRIMARY source for:

- table layout
- row labels
- column alignment
- current-period values
- previous-period values
- section boundaries
- printed totals

The OCR text is a SUPPORTING source.

============================================================
CRITICAL EXTRACTION RULES
============================================================

1. Extract ONLY information actually visible in the document.

2. DO NOT invent values.

3. DO NOT guess values.

4. DO NOT calculate missing values.

5. DO NOT replace an explicitly printed value with a
   calculated value.

6. Extract ALL meaningful visible Balance Sheet line items.

7. Preserve the meaning of every line item.

8. Preserve CURRENT and PREVIOUS period values separately.

9. Identify the company name when visible.

10. Identify the statement date when visible.

11. Identify the currency when visible.

12. Identify the unit when visible.

13. Carefully read the column headings from the ORIGINAL
    DOCUMENT IMAGE.

14. Do NOT assume the first numeric column is current period
    unless the document's headings confirm it.

15. Do NOT assume the second numeric column is previous period
    unless the document's headings confirm it.

============================================================
TOTAL EXTRACTION RULES
============================================================

16. Carefully identify the explicitly printed TOTAL ASSETS.

17. Carefully identify the explicitly printed TOTAL for
    CAPITAL AND LIABILITIES, if present.

18. Carefully identify the explicitly printed TOTAL LIABILITIES
    if the document provides a separate liabilities total.

19. Carefully identify the explicitly printed TOTAL EQUITY
    if the document provides a separate equity total.

20. NEVER calculate total_assets if a printed total is available.

21. NEVER calculate total_liabilities if a printed total is
    available.

22. NEVER calculate total_equity if a printed total is available.

23. NEVER use the previous-period total as the current-period
    total.

24. NEVER swap current-period and previous-period values.

25. If the same total is printed in multiple sections,
    verify which period each number belongs to.

26. If OCR conflicts with the original image, trust the
    ORIGINAL IMAGE when the number is clearly readable.

27. If a total cannot be read reliably from either source,
    return null.

28. Do not silently correct a number using arithmetic.

============================================================
CAPITAL AND LIABILITIES
============================================================

Some financial statements use a section such as:

CAPITAL AND LIABILITIES

Capital
Reserves and surplus
Minority interest
Deposits
Borrowings
Other liabilities and provisions
Total

In this structure:

- Capital is a line item.
- Reserves and surplus is a line item.
- Minority interest is a line item.
- Deposits is a line item.
- Borrowings is a line item.
- Other liabilities and provisions is a line item.
- The "Total" below those rows is the total for the
  Capital and Liabilities section.

Read the current-period and previous-period values from
the correct columns in the ORIGINAL IMAGE.

============================================================
ASSETS
============================================================

For an Assets section such as:

ASSETS

Cash and balances with Reserve Bank of India
Balances with banks and money at call and short notice
Investments
Advances
Fixed assets
Other assets
Total

Extract every line item.

The "Total" below the Assets rows is the printed
TOTAL ASSETS.

Read its current-period and previous-period values from
the correct columns in the ORIGINAL IMAGE.

============================================================
IMPORTANT EXAMPLE
============================================================

If the image shows:

                    31-Mar-18       31-Mar-17

Capital             5,190,181       5,125,091
Reserves            1,090,801,062   912,814,397
...
Total               11,031,861,695  8,923,441,607

then:

total_assets/current_period must be:

11031861695

NOT:

8923441607

because 8,923,441,607 belongs to the previous-period column.

============================================================
NUMBER RULES
============================================================

29. Return numeric values as JSON numbers.

30. Do not include commas inside JSON numbers.

31. Example:

    11,031,861,695

    must become:

    11031861695

32. Preserve negative values as negative numbers.

33. Do not convert units.

34. If the document says:

    ₹ in '000

    or

    Rs. in '000

    preserve the unit in the "unit" field.

35. Keep extracted financial numbers in the same unit
    represented by the document.

============================================================
OUTPUT STRUCTURE
============================================================

Return exactly:

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

Each item inside assets, liabilities and equity must use:

{{
    "name": null,
    "current_period": null,
    "previous_period": null
}}

For total_assets:

- Return the explicitly printed CURRENT-period total.
- Return a single numeric value.
- Do not return an object.
- Do not calculate it.
- Do not use the previous-period number.

For total_liabilities:

- Return the explicitly printed CURRENT-period liabilities
  total if separately available.
- Otherwise return null.

For total_equity:

- Return the explicitly printed CURRENT-period equity
  total if separately available.
- Otherwise return null.

Additional meaningful information such as contingent
liabilities and bills for collection may be stored in
raw_fields.

============================================================
OCR TEXT
============================================================

----------------
{ocr_text}
----------------

Use the ORIGINAL DOCUMENT IMAGE to resolve any disagreement
between the OCR text and the visual table.
"""

    # =========================================================
    # PREPARE ORIGINAL DOCUMENT IMAGE
    # =========================================================

    image_parts = []

    if file_bytes and filename:

        extension = (
            "."
            + filename.lower().split(".")[-1]
        )

        try:

            # -------------------------------------------------
            # PDF
            # -------------------------------------------------

            if extension == ".pdf":

                pdf = pymupdf.open(
                    stream=file_bytes,
                    filetype="pdf",
                )

                for page in pdf:

                    pixmap = page.get_pixmap(
                        matrix=pymupdf.Matrix(
                            2.5,
                            2.5,
                        ),
                        alpha=False,
                    )

                    image_bytes = pixmap.tobytes(
                        "png"
                    )

                    image_parts.append(
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/png",
                        )
                    )

                pdf.close()

            # -------------------------------------------------
            # IMAGE
            # -------------------------------------------------

            elif extension in {
                ".jpg",
                ".jpeg",
                ".png",
            }:

                mime_type = (
                    "image/png"
                    if extension == ".png"
                    else "image/jpeg"
                )

                image_parts.append(
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type,
                    )
                )

        except Exception:
            # OCR remains available as fallback.
            image_parts = []

    # =========================================================
    # SEND OCR + ORIGINAL IMAGE TO GEMINI
    # =========================================================

    contents = [
        prompt
    ]

    contents.extend(
        image_parts
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
    )

    data = parse_json_response(
        response.text
    )

    data = clean_financial_data(
        data
    )

    return BalanceSheetExtraction.model_validate(
        data
    )


# =============================================================
# PROFIT & LOSS EXTRACTION
# =============================================================

def extract_profit_loss(
    ocr_text: str,
) -> ProfitLossExtraction:

    client = get_gemini_client()

    prompt = f"""
You are an expert financial-document extraction system.

Extract information from the Profit and Loss statement OCR
text below.

IMPORTANT RULES:

1. Extract ONLY information supported by the OCR text.

2. Do not invent or guess values.

3. If a field cannot be determined reliably, use null.

4. Extract ALL meaningful visible income line items.

5. Extract ALL meaningful visible expense/expenditure
   line items.

6. Preserve current-period and previous-period values separately.

7. Extract company name when available.

8. Extract statement date when available.

9. Extract currency when available.

10. Extract unit when available.

11. Extract explicitly printed total income.

12. Extract explicitly printed total expenses.

13. Do not calculate missing totals.

14. For profit_before_tax, extract the explicitly printed
    profit figure that represents profit after income and
    expenditure but BEFORE minority interest.

    For example, if the document contains:

    "Consolidated Net Profit for the year before minorities' interest"

    use that value for profit_before_tax.

15. Do NOT calculate profit_before_tax when it is not explicitly
    available in the document.

16. Extract tax expense only when explicitly shown.

17. For net_profit, prefer the explicitly printed profit
    attributable to the group.

    For example, if the document contains:

    "Consolidated Net Profit for the year attributable to the group"

    use that value for net_profit.

18. If the document contains "Net profit for the year" without
    minority-interest information, that value may be used for
    net_profit.

19. Do not confuse:
    - profit before minority interest
    - minority interest
    - profit attributable to the group
    - consolidated profit
    - brought-forward profit
    - appropriations
    with each other.

20. Preserve additional meaningful information such as:
    - minority interest
    - share in profits of associates
    - EPS
    - appropriations
    - brought-forward profit
    - additions on amalgamation

    in raw_fields.

21. Preserve negative values.

22. Numbers must be JSON numbers.

23. Do not include commas inside numbers.

24. Return ONLY valid JSON.

Return exactly:

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

IMPORTANT P&L MAPPING EXAMPLE:

If the document contains:

Consolidated Net Profit for the year before minorities' interest
65446.50    46148.70

Less: Minority Interest
1384.46    151.59

Consolidated Net Profit for the year attributable to the group
64062.04    45997.11

then return:

"profit_before_tax": 65446.50

"net_profit": 64062.04

and preserve the minority interest in raw_fields.

Do not calculate these values yourself. Extract them because
they are explicitly printed in the document.

OCR TEXT:
----------------
{ocr_text}
----------------
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    data = parse_json_response(
        response.text
    )

    data = clean_financial_data(
        data
    )

    return ProfitLossExtraction.model_validate(
        data
    )
# =============================================================
# CASH FLOW EXTRACTION
# =============================================================

def extract_cash_flow(
    ocr_text: str,
) -> CashFlowExtraction:

    client = get_gemini_client()

    prompt = f"""
You are an expert financial-document extraction system.

Extract information from the Cash Flow Statement OCR text.

IMPORTANT RULES:

1. Extract ONLY information explicitly supported by the OCR.

2. Do not hallucinate.

3. Do not invent values.

4. Do not calculate missing values.

5. If a value cannot be determined reliably, return null.

6. Extract ALL meaningful operating activity line items.

7. Extract ALL meaningful investing activity line items.

8. Extract ALL meaningful financing activity line items.

9. Preserve current-period and previous-period values.

10. Extract company name when available.

11. Extract statement date when available.

12. Extract currency when available.

13. Extract unit when available.

14. Extract foreign exchange effects when explicitly shown.

15. Extract explicitly printed net cash change.

16. Extract explicitly printed opening cash balance.

17. Extract explicitly printed closing cash balance.

18. Preserve negative values.

19. Do not calculate missing totals.

20. Numbers must be JSON numbers.

21. Do not include commas inside numbers.

22. Return ONLY valid JSON.

Return exactly:

{{
    "company_name": null,
    "statement_date": null,
    "currency": null,
    "unit": null,
    "operating_activities": [],
    "investing_activities": [],
    "financing_activities": [],
    "foreign_exchange_effect": null,
    "net_cash_change": null,
    "opening_cash_balance": null,
    "closing_cash_balance": null
}}

Each activity line item must use:

{{
    "name": null,
    "current_period": null,
    "previous_period": null
}}

OCR TEXT:
----------------
{ocr_text}
----------------
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
        raise ValueError(
            "Gemini returned no structured Cash Flow data"
        )

    # response.parsed is already a Pydantic object.
    # Do not pass it through clean_financial_data(),
    # because that function expects a dictionary.

    return data