from pydantic import BaseModel


class BalanceEntry(BaseModel):
    user_id: str
    name: str
    balance: float
