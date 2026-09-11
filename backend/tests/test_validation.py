from backend.app.schemas.extraction import (
    InvoiceExtraction,
    LineItem,
    BalanceSheetExtraction,
    FinancialLineItem,
    ProfitLossExtraction,
    CashFlowExtraction,
)

from backend.app.services.financial_validation_service import (
    validate_invoice,
    validate_balance_sheet,
    validate_profit_loss,
    validate_cash_flow,
)


def test_invoice_validation_passes():
    invoice = InvoiceExtraction(
        line_items=[
            LineItem(
                description="Test Item",
                quantity=2,
                unit_price=50,
                amount=100,
            )
        ],
        subtotal=100,
        tax=10,
        discount=0,
        total=110,
    )

    result = validate_invoice(invoice)

    assert result["overall_status"] == "passed"


def test_invoice_validation_fails():
    invoice = InvoiceExtraction(
        line_items=[
            LineItem(
                description="Test Item",
                quantity=2,
                unit_price=50,
                amount=120,
            )
        ],
        subtotal=120,
        tax=10,
        discount=0,
        total=130,
    )

    result = validate_invoice(invoice)

    assert result["overall_status"] == "failed"


def test_balance_sheet_validation_passes():
    balance_sheet = BalanceSheetExtraction(
        total_assets=1000,
        total_liabilities=600,
        total_equity=400,
    )

    result = validate_balance_sheet(balance_sheet)

    assert result["overall_status"] == "passed"


def test_profit_loss_validation_passes():
    profit_loss = ProfitLossExtraction(
        income=[
            FinancialLineItem(
                name="Revenue",
                current_period=1000,
            )
        ],
        expenses=[
            FinancialLineItem(
                name="Expenses",
                current_period=600,
            )
        ],
        total_income=1000,
        total_expenses=600,
        profit_before_tax=400,
    )

    result = validate_profit_loss(profit_loss)

    assert result["overall_status"] == "passed"


def test_cash_flow_validation_passes():
    cash_flow = CashFlowExtraction(
        operating_activities=[
            FinancialLineItem(
                name="Operating Cash",
                current_period=500,
            )
        ],
        investing_activities=[
            FinancialLineItem(
                name="Investing Cash",
                current_period=-200,
            )
        ],
        financing_activities=[
            FinancialLineItem(
                name="Financing Cash",
                current_period=100,
            )
        ],
        foreign_exchange_effect=0,
        net_cash_change=400,
    )

    result = validate_cash_flow(cash_flow)

    assert result["overall_status"] == "passed"


def test_cash_flow_validation_fails():
    cash_flow = CashFlowExtraction(
        operating_activities=[
            FinancialLineItem(
                name="Operating Cash",
                current_period=500,
            )
        ],
        investing_activities=[
            FinancialLineItem(
                name="Investing Cash",
                current_period=-200,
            )
        ],
        financing_activities=[
            FinancialLineItem(
                name="Financing Cash",
                current_period=100,
            )
        ],
        foreign_exchange_effect=0,
        net_cash_change=500,
    )

    result = validate_cash_flow(cash_flow)

    assert result["overall_status"] == "failed"