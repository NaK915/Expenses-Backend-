from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TransactionType = Literal["expense", "reimbursement"]


class TransactionCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    transaction_type: TransactionType = "expense"
    split_between: List[str] = Field(default_factory=list)
    to_user_id: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    split_between: Optional[List[str]] = None
    to_user_id: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class TransactionRead(BaseModel):
    id: str
    group_id: str
    title: str
    amount: float
    transaction_type: TransactionType
    paid_by: str
    split_between: List[str]
    to_user_id: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)