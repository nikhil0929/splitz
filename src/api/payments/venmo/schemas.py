from pydantic import BaseModel

class VenmoBase(BaseModel):
    payment_amount:int
    note:str
    username: List[str]
    payment_type: str

class VenmoLink(BaseModel):
    payment_url: str