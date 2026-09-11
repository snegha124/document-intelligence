from math import isclose

from backend.app.schemas.extraction import (
    InvoiceExtraction,
    BalanceSheetExtraction,
    ProfitLossExtraction,
    CashFlowExtraction,
)


TOLERANCE = 0.05


def build_validation_result(
    checks: list[dict],
) -> dict:

    failed = any(
        check["status"] == "failed"
        for check in checks
    )

    return {
        "overall_status": "failed" if failed else "passed",
        "checks": checks,
    }


# =============================================================
# INVOICE VALIDATION
# =============================================================

def validate_invoice(
    invoice: InvoiceExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Check quantity × unit price ≈ line amount
    # ---------------------------------------------------------
    for item in invoice.line_items:

        if (
            item.quantity is not None
            and item.unit_price is not None
            and item.amount is not None
        ):

            expected = item.quantity * item.unit_price
            actual = item.amount

            passed = isclose(
                expected,
                actual,
                abs_tol=TOLERANCE
            )

            checks.append({
                "check": "quantity_times_unit_price",
                "description": item.description,
                "expected": expected,
                "actual": actual,
                "status": "passed" if passed else "failed",
            })

        else:

            checks.append({
                "check": "quantity_times_unit_price",
                "description": item.description,
                "status": "not_checkable",
            })

    # ---------------------------------------------------------
    # Check subtotal + tax - discount ≈ total
    # ---------------------------------------------------------
    if (
        invoice.subtotal is not None
        and invoice.total is not None
    ):

        tax = invoice.tax or 0
        discount = invoice.discount or 0

        expected_total = (
            invoice.subtotal
            + tax
            - discount
        )

        passed = isclose(
            expected_total,
            invoice.total,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "subtotal_tax_discount_total",
            "expected": expected_total,
            "actual": invoice.total,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "subtotal_tax_discount_total",
            "status": "not_checkable",
        })

    return build_validation_result(checks)


# =============================================================
# BALANCE SHEET VALIDATION
# =============================================================

def validate_balance_sheet(
    balance_sheet: BalanceSheetExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Check assets ≈ liabilities + equity
    # ---------------------------------------------------------
    if (
        balance_sheet.total_assets is not None
        and balance_sheet.total_liabilities is not None
        and balance_sheet.total_equity is not None
    ):

        expected = (
            balance_sheet.total_liabilities
            + balance_sheet.total_equity
        )

        actual = balance_sheet.total_assets

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "assets_equals_liabilities_plus_equity",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "assets_equals_liabilities_plus_equity",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Check asset line items against total assets
    # ---------------------------------------------------------
    asset_values = [
        item.current_period
        for item in balance_sheet.assets
        if item.current_period is not None
    ]

    if (
        asset_values
        and balance_sheet.total_assets is not None
    ):

        expected = sum(asset_values)
        actual = balance_sheet.total_assets

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "asset_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "asset_line_items_sum",
            "status": "not_checkable",
        })

    return build_validation_result(checks)


# =============================================================
# PROFIT & LOSS VALIDATION
# =============================================================

def validate_profit_loss(
    profit_loss: ProfitLossExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Check income line items against total income
    # ---------------------------------------------------------
    income_values = [
        item.current_period
        for item in profit_loss.income
        if item.current_period is not None
    ]

    if (
        income_values
        and profit_loss.total_income is not None
    ):

        expected = sum(income_values)
        actual = profit_loss.total_income

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "income_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "income_line_items_sum",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Check expense line items against total expenses
    # ---------------------------------------------------------
    expense_values = [
        item.current_period
        for item in profit_loss.expenses
        if item.current_period is not None
    ]

    if (
        expense_values
        and profit_loss.total_expenses is not None
    ):

        expected = sum(expense_values)
        actual = profit_loss.total_expenses

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "expense_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "expense_line_items_sum",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Check total income - total expenses ≈ profit before tax
    # ---------------------------------------------------------
    if (
        profit_loss.total_income is not None
        and profit_loss.total_expenses is not None
        and profit_loss.profit_before_tax is not None
    ):

        expected = (
            profit_loss.total_income
            - profit_loss.total_expenses
        )

        actual = profit_loss.profit_before_tax

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "income_minus_expenses_equals_profit_before_tax",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "income_minus_expenses_equals_profit_before_tax",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Check consolidated profit using raw fields
    # ---------------------------------------------------------
    raw_fields = profit_loss.raw_fields

    minority_interest = raw_fields.get(
        "minority_interest"
    )

    share_in_profits = raw_fields.get(
        "share_in_profits_of_associates"
    )

    consolidated_profit = raw_fields.get(
        "consolidated_profit_for_the_year_attributable_to_the_group"
    )

    if (
        profit_loss.net_profit is not None
        and isinstance(minority_interest, dict)
        and isinstance(share_in_profits, dict)
        and isinstance(consolidated_profit, dict)
        and minority_interest.get("current") is not None
        and share_in_profits.get("current") is not None
        and consolidated_profit.get("current") is not None
    ):

        expected = (
            profit_loss.net_profit
            - minority_interest["current"]
            + share_in_profits["current"]
        )

        actual = consolidated_profit["current"]

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "net_profit_minority_interest_associates",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "net_profit_minority_interest_associates",
            "status": "not_checkable",
        })

    return build_validation_result(checks)


# =============================================================
# CASH FLOW VALIDATION
# =============================================================

def validate_cash_flow(
    cash_flow: CashFlowExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Sum operating activities
    # ---------------------------------------------------------
    operating_values = [
        item.current_period
        for item in cash_flow.operating_activities
        if item.current_period is not None
    ]

    operating_total = (
        sum(operating_values)
        if operating_values
        else None
    )

    # ---------------------------------------------------------
    # Sum investing activities
    # ---------------------------------------------------------
    investing_values = [
        item.current_period
        for item in cash_flow.investing_activities
        if item.current_period is not None
    ]

    investing_total = (
        sum(investing_values)
        if investing_values
        else None
    )

    # ---------------------------------------------------------
    # Sum financing activities
    # ---------------------------------------------------------
    financing_values = [
        item.current_period
        for item in cash_flow.financing_activities
        if item.current_period is not None
    ]

    financing_total = (
        sum(financing_values)
        if financing_values
        else None
    )

    # ---------------------------------------------------------
    # Check:
    #
    # Operating
    # + Investing
    # + Financing
    # + FX
    # ≈ Net Cash Change
    # ---------------------------------------------------------
    if (
        operating_total is not None
        and investing_total is not None
        and financing_total is not None
        and cash_flow.net_cash_change is not None
    ):

        fx = cash_flow.foreign_exchange_effect or 0

        expected = (
            operating_total
            + investing_total
            + financing_total
            + fx
        )

        actual = cash_flow.net_cash_change

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "operating_investing_financing_fx_equals_net_cash_change",
            "operating": operating_total,
            "investing": investing_total,
            "financing": financing_total,
            "foreign_exchange": fx,
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "operating_investing_financing_fx_equals_net_cash_change",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Check opening cash + net change ≈ closing cash
    # ---------------------------------------------------------
    if (
        cash_flow.opening_cash_balance is not None
        and cash_flow.net_cash_change is not None
        and cash_flow.closing_cash_balance is not None
    ):

        expected = (
            cash_flow.opening_cash_balance
            + cash_flow.net_cash_change
        )

        actual = cash_flow.closing_cash_balance

        passed = isclose(
            expected,
            actual,
            abs_tol=TOLERANCE
        )

        checks.append({
            "check": "opening_cash_plus_net_change_equals_closing_cash",
            "expected": expected,
            "actual": actual,
            "status": "passed" if passed else "failed",
        })

    else:

        checks.append({
            "check": "opening_cash_plus_net_change_equals_closing_cash",
            "status": "not_checkable",
        })

    return build_validation_result(checks)