from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


TransactionType = Literal["expense", "reimbursement"]
SplitType = Literal["equal", "amounts", "parts"]


class TransactionCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    transaction_type: TransactionType = "expense"
    split_between: List[str] = Field(default_factory=list)
    split_type: SplitType = "equal"
    split_amounts: Dict[str, float] = Field(default_factory=dict)
    split_parts: Dict[str, float] = Field(default_factory=dict)
    to_user_id: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    split_between: Optional[List[str]] = None
    split_type: Optional[SplitType] = None
    split_amounts: Optional[Dict[str, float]] = None
    split_parts: Optional[Dict[str, float]] = None
    to_user_id: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class TransactionRead(BaseModel):
    id: str
    group_id: str
    title: str
    amount: float
    transaction_type: TransactionType
    paid_by: str
    split_between: List[str]
    split_type: SplitType = "equal"
    split_amounts: Dict[str, float] = Field(default_factory=dict)
    split_parts: Dict[str, float] = Field(default_factory=dict)
    to_user_id: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)