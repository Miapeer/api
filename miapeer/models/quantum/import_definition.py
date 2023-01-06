from typing import Optional

from sqlmodel import Field, SQLModel
from decimal import Decimal
from datetime import date


class ImportDefinitionBase(SQLModel):
    input_transaction_type: str
    input_payee: str
    account_id: int = Field(foreign_key="account.account_id")
    transaction_type_id: int = Field(foreign_key="transaction_type.transaction_type_id")
    payee_id: int = Field(foreign_key="payee.payee_id")
    category_id: int = Field(foreign_key="category.category_id")

class ImportDefinition(ImportDefinitionBase, table=True):
    __tablename__: str = "import_definition"  # type: ignore

    import_definition_id: Optional[int] = Field(default=None, primary_key=True)


class ImportDefinitionCreate(ImportDefinitionBase):
    ...


class ImportDefinitionRead(ImportDefinitionBase):
    import_definition_id: int


class ImportDefinitionUpdate(SQLModel):
    ...
