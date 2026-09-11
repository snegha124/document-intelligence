from typing import Any, Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class InvoiceExtraction(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None

    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None

    customer_name: Optional[str] = None
    customer_address: Optional[str] = None

    currency: Optional[str] = None

    line_items: list[LineItem] = Field(default_factory=list)

    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    total: Optional[float] = None

    payment_method: Optional[str] = None
    reference_number: Optional[str] = None

    raw_fields: dict[str, Any] = Field(default_factory=dict)


class FinancialLineItem(BaseModel):
    name: Optional[str] = None
    current_period: Optional[float] = None
    previous_period: Optional[float] = None


class BalanceSheetExtraction(BaseModel):
    company_name: Optional[str] = None
    statement_date: Optional[str] = None

    currency: Optional[str] = None
    unit: Optional[str] = None

    assets: list[FinancialLineItem] = Field(default_factory=list)
    liabilities: list[FinancialLineItem] = Field(default_factory=list)
    equity: list[FinancialLineItem] = Field(default_factory=list)

    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None

    raw_fields: dict[str, Any] = Field(default_factory=dict)


class ProfitLossExtraction(BaseModel):
    company_name: Optional[str] = None
    statement_date: Optional[str] = None

    currency: Optional[str] = None
    unit: Optional[str] = None

    income: list[FinancialLineItem] = Field(default_factory=list)
    expenses: list[FinancialLineItem] = Field(default_factory=list)

    total_income: Optional[float] = None
    total_expenses: Optional[float] = None

    profit_before_tax: Optional[float] = None
    tax_expense: Optional[float] = None
    net_profit: Optional[float] = None

    raw_fields: dict[str, Any] = Field(default_factory=dict)


class CashFlowExtraction(BaseModel):
    company_name: Optional[str] = None
    statement_date: Optional[str] = None

    currency: Optional[str] = None
    unit: Optional[str] = None

    operating_activities: list[FinancialLineItem] = Field(
        default_factory=list
    )

    investing_activities: list[FinancialLineItem] = Field(
        default_factory=list
    )

    financing_activities: list[FinancialLineItem] = Field(
        default_factory=list
    )

    foreign_exchange_effect: Optional[float] = None

    net_cash_change: Optional[float] = None
    opening_cash_balance: Optional[float] = None
    closing_cash_balance: Optional[float] = None


class ExtractionResult(BaseModel):
    document_type: str

    invoice: Optional[InvoiceExtraction] = None

    balance_sheet: Optional[BalanceSheetExtraction] = None

    profit_loss: Optional[ProfitLossExtraction] = None

    cash_flow: Optional[CashFlowExtraction] = None