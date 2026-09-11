from backend.app.schemas.extraction import (
    InvoiceExtraction,
    LineItem,
    BalanceSheetExtraction,
    FinancialLineItem,
    ProfitLossExtraction,
    CashFlowExtraction,
)


def test_invoice_schema():
    invoice = InvoiceExtraction(
        invoice_number="INV-001",
        vendor_name="Test Vendor",
        currency="USD",
        line_items=[
            LineItem(
                description="Laptop",
                quantity=2,
                unit_price=500,
                amount=1000,
            )
        ],
        total=1000,
    )

    assert invoice.invoice_number == "INV-001"
    assert invoice.line_items[0].quantity == 2
    assert invoice.total == 1000


def test_balance_sheet_schema():
    balance_sheet = BalanceSheetExtraction(
        company_name="Test Company",
        statement_date="2026-03-31",
        assets=[
            FinancialLineItem(
                name="Cash",
                current_period=500
            )
        ],
        total_assets=500,
    )

    assert balance_sheet.company_name == "Test Company"
    assert balance_sheet.assets[0].name == "Cash"
    assert balance_sheet.total_assets == 500


def test_profit_loss_schema():
    profit_loss = ProfitLossExtraction(
        company_name="Test Company",
        total_income=1000,
        total_expenses=600,
        profit_before_tax=400,
        net_profit=300,
    )

    assert profit_loss.total_income == 1000
    assert profit_loss.total_expenses == 600
    assert profit_loss.net_profit == 300


def test_cash_flow_schema():
    cash_flow = CashFlowExtraction(
        company_name="Test Company",
        operating_activities=[
            FinancialLineItem(
                name="Operating activities",
                current_period=500
            )
        ],
        investing_activities=[
            FinancialLineItem(
                name="Investing activities",
                current_period=-200
            )
        ],
        financing_activities=[
            FinancialLineItem(
                name="Financing activities",
                current_period=100
            )
        ],
        foreign_exchange_effect=0,
        net_cash_change=400,
        opening_cash_balance=1000,
        closing_cash_balance=1400,
    )

    assert cash_flow.company_name == "Test Company"
    assert cash_flow.net_cash_change == 400
    assert cash_flow.closing_cash_balance == 1400