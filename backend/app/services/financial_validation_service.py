from math import isclose

from backend.app.schemas.extraction import (
    InvoiceExtraction,
    BalanceSheetExtraction,
    ProfitLossExtraction,
    CashFlowExtraction,
)


# =============================================================
# VALIDATION SETTINGS
# =============================================================

ABSOLUTE_TOLERANCE = 0.05

# 0.5% relative tolerance for large financial values.
RELATIVE_TOLERANCE = 0.005


def numbers_match(expected, actual) -> bool:
    """
    Compare two financial values using both absolute
    and relative tolerance.
    """

    if expected is None or actual is None:
        return False

    return isclose(
        float(expected),
        float(actual),
        abs_tol=ABSOLUTE_TOLERANCE,
        rel_tol=RELATIVE_TOLERANCE,
    )


def build_validation_result(
    checks: list[dict],
) -> dict:

    failed = any(
        check.get("status") == "failed"
        for check in checks
    )

    passed = any(
        check.get("status") == "passed"
        for check in checks
    )

    if failed:
        overall_status = "failed"

    elif passed:
        overall_status = "passed"

    else:
        overall_status = "not_checkable"

    return {
        "overall_status": overall_status,
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
    # Quantity × Unit Price ≈ Line Amount
    # ---------------------------------------------------------

    if not invoice.line_items:

        checks.append({
            "check": "quantity_times_unit_price",
            "status": "not_checkable",
            "reason": "No invoice line items were extracted.",
        })

    else:

        for index, item in enumerate(
            invoice.line_items,
            start=1,
        ):

            if (
                item.quantity is not None
                and item.unit_price is not None
                and item.amount is not None
            ):

                expected = (
                    item.quantity
                    * item.unit_price
                )

                actual = item.amount

                passed = numbers_match(
                    expected,
                    actual,
                )

                checks.append({
                    "check": "quantity_times_unit_price",
                    "line_item": index,
                    "description": item.description,
                    "expected": expected,
                    "actual": actual,
                    "status": (
                        "passed"
                        if passed
                        else "failed"
                    ),
                })

            else:

                checks.append({
                    "check": "quantity_times_unit_price",
                    "line_item": index,
                    "description": item.description,
                    "status": "not_checkable",
                })

    # ---------------------------------------------------------
    # Subtotal + Tax - Discount ≈ Total
    # ---------------------------------------------------------

    if (
        invoice.subtotal is not None
        and invoice.total is not None
    ):

        tax = (
            invoice.tax
            if invoice.tax is not None
            else 0
        )

        discount = (
            invoice.discount
            if invoice.discount is not None
            else 0
        )

        expected_total = (
            invoice.subtotal
            + tax
            - discount
        )

        actual_total = invoice.total

        passed = numbers_match(
            expected_total,
            actual_total,
        )

        checks.append({
            "check": "subtotal_tax_discount_total",
            "expected": expected_total,
            "actual": actual_total,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": "subtotal_tax_discount_total",
            "status": "not_checkable",
        })

    return build_validation_result(
        checks
    )


# =============================================================
# BALANCE SHEET VALIDATION
# =============================================================

def validate_balance_sheet(
    balance_sheet: BalanceSheetExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Get explicit totals first
    # ---------------------------------------------------------

    total_assets = (
        balance_sheet.total_assets
    )

    total_liabilities = (
        balance_sheet.total_liabilities
    )

    total_equity = (
        balance_sheet.total_equity
    )

    # ---------------------------------------------------------
    # Derive liabilities if explicit total is unavailable
    # ---------------------------------------------------------

    if (
        total_liabilities is None
        and balance_sheet.liabilities
    ):

        liability_values = [
            item.current_period
            for item in balance_sheet.liabilities
            if item.current_period is not None
        ]

        if liability_values:
            total_liabilities = sum(
                liability_values
            )

    # ---------------------------------------------------------
    # Derive equity if explicit total is unavailable
    # ---------------------------------------------------------

    if (
        total_equity is None
        and balance_sheet.equity
    ):

        equity_values = [
            item.current_period
            for item in balance_sheet.equity
            if item.current_period is not None
        ]

        if equity_values:
            total_equity = sum(
                equity_values
            )

    # ---------------------------------------------------------
    # Assets ≈ Liabilities + Equity
    # ---------------------------------------------------------

    if (
        total_assets is not None
        and total_liabilities is not None
        and total_equity is not None
    ):

        expected = (
            total_liabilities
            + total_equity
        )

        actual = total_assets

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": (
                "assets_equals_liabilities_plus_equity"
            ),
            "expected": expected,
            "actual": actual,
            "derived_liabilities": total_liabilities,
            "derived_equity": total_equity,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": (
                "assets_equals_liabilities_plus_equity"
            ),
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Asset line items ≈ Total Assets
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

        actual = (
            balance_sheet.total_assets
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": "asset_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": "asset_line_items_sum",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Liability line items ≈ Total Liabilities
    # ---------------------------------------------------------

    liability_values = [
        item.current_period
        for item in balance_sheet.liabilities
        if item.current_period is not None
    ]

    if (
        liability_values
        and total_liabilities is not None
    ):

        expected = sum(
            liability_values
        )

        actual = total_liabilities

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": "liability_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": "liability_line_items_sum",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Equity line items ≈ Total Equity
    # ---------------------------------------------------------

    equity_values = [
        item.current_period
        for item in balance_sheet.equity
        if item.current_period is not None
    ]

    if (
        equity_values
        and total_equity is not None
    ):

        expected = sum(
            equity_values
        )

        actual = total_equity

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": "equity_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": "equity_line_items_sum",
            "status": "not_checkable",
        })

    return build_validation_result(
        checks
    )


# =============================================================
# PROFIT & LOSS VALIDATION
# =============================================================

def validate_profit_loss(
    profit_loss: ProfitLossExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Income line items ≈ Total Income
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

        expected = sum(
            income_values
        )

        actual = (
            profit_loss.total_income
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": "income_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": "income_line_items_sum",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Expense line items ≈ Total Expenses
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

        expected = sum(
            expense_values
        )

        actual = (
            profit_loss.total_expenses
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": "expense_line_items_sum",
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": "expense_line_items_sum",
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Total Income - Total Expenses ≈ Profit Before Tax
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

        actual = (
            profit_loss.profit_before_tax
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": (
                "income_minus_expenses_equals_profit_before_tax"
            ),
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": (
                "income_minus_expenses_equals_profit_before_tax"
            ),
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Consolidated Profit Check
    # ---------------------------------------------------------

    raw_fields = (
        profit_loss.raw_fields
        or {}
    )

    minority_interest = raw_fields.get(
        "minority_interest"
    )

    share_in_profits = raw_fields.get(
        "share_in_profits_of_associates"
    )

    consolidated_profit = raw_fields.get(
        "consolidated_profit_for_the_year"
    )

    if consolidated_profit is None:

        consolidated_profit = raw_fields.get(
            "consolidated_profit_for_the_year_attributable_to_the_group"
        )

    def get_current_value(value):

        if not isinstance(value, dict):
            return None

        if value.get("current_period") is not None:
            return value.get(
                "current_period"
            )

        if value.get("current") is not None:
            return value.get(
                "current"
            )

        return None

    minority_current = get_current_value(
        minority_interest
    )

    share_current = get_current_value(
        share_in_profits
    )

    consolidated_current = get_current_value(
        consolidated_profit
    )

    if (
        profit_loss.net_profit is not None
        and minority_current is not None
        and share_current is not None
        and consolidated_current is not None
    ):

        expected = (
            profit_loss.net_profit
            - minority_current
            + share_current
        )

        actual = (
            consolidated_current
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": (
                "net_profit_minority_interest_associates"
            ),
            "expected": expected,
            "actual": actual,
            "minority_interest": minority_current,
            "share_in_profits_of_associates": share_current,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": (
                "net_profit_minority_interest_associates"
            ),
            "status": "not_checkable",
        })

    return build_validation_result(
        checks
    )


# =============================================================
# CASH FLOW VALIDATION
# =============================================================

def validate_cash_flow(
    cash_flow: CashFlowExtraction,
) -> dict:

    checks = []

    # ---------------------------------------------------------
    # Operating activities
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
    # Investing activities
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
    # Financing activities
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
    # Operating + Investing + Financing + FX
    # ≈ Net Cash Change
    # ---------------------------------------------------------

    if (
        operating_total is not None
        and investing_total is not None
        and financing_total is not None
        and cash_flow.net_cash_change is not None
    ):

        fx = (
            cash_flow.foreign_exchange_effect
            if cash_flow.foreign_exchange_effect is not None
            else 0
        )

        expected = (
            operating_total
            + investing_total
            + financing_total
            + fx
        )

        actual = (
            cash_flow.net_cash_change
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": (
                "operating_investing_financing_fx_equals_net_cash_change"
            ),
            "operating": operating_total,
            "investing": investing_total,
            "financing": financing_total,
            "foreign_exchange": fx,
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": (
                "operating_investing_financing_fx_equals_net_cash_change"
            ),
            "status": "not_checkable",
        })

    # ---------------------------------------------------------
    # Opening Cash + Net Change ≈ Closing Cash
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

        actual = (
            cash_flow.closing_cash_balance
        )

        passed = numbers_match(
            expected,
            actual,
        )

        checks.append({
            "check": (
                "opening_cash_plus_net_change_equals_closing_cash"
            ),
            "expected": expected,
            "actual": actual,
            "status": (
                "passed"
                if passed
                else "failed"
            ),
        })

    else:

        checks.append({
            "check": (
                "opening_cash_plus_net_change_equals_closing_cash"
            ),
            "status": "not_checkable",
        })

    return build_validation_result(
        checks
    )