from typing import Optional

from sqlmodel import Field, SQLModel


class ImportDefinitionBase(SQLModel):
    input_transaction_type: str
    input_payee: str
    account_id: int = Field(foreign_key="quantum_account.account_id")
    transaction_type_id: int = Field(foreign_key="quantum_transaction_type.transaction_type_id")
    payee_id: int = Field(foreign_key="quantum_payee.payee_id")
    category_id: int = Field(foreign_key="quantum_category.category_id")


class ImportDefinition(ImportDefinitionBase, table=True):
    __tablename__: str = "quantum_import_definition"  # type: ignore

    import_definition_id: Optional[int] = Field(default=None, primary_key=True)

    # account: Account = Relationship(back_populates="import_definitions")
    # transaction_type: TransactionType = Relationship(back_populates="import_definitions")
    # payee: Payee = Relationship(back_populates="import_definitions")
    # category: Category = Relationship(back_populates="import_definitions")


class ImportDefinitionCreate(ImportDefinitionBase):
    ...


class ImportDefinitionRead(ImportDefinitionBase):
    import_definition_id: int


class ImportDefinitionUpdate(SQLModel):
    ...
