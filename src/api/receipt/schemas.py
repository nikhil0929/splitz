from typing import Dict, Tuple, List
from pydantic import BaseModel
from src.api.user import MiniUser

class ItemBase(BaseModel):
    name: str
    quantity: int
    price: float

class GetItems(BaseModel):
    item_id_list: List[int]
    user_total_price: float

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True

class ItemWithUsers(Item):
    users: List[MiniUser]

class UserItem(Item):
    split_price: float

class ReceiptBase(BaseModel):
    receipt_name: str



## Create ReceiptCreate schema with the following dict in mind:
# sample_receipt_dict = {
#             "merchant_name": "DIN TAI FUNG",
#             "total_amount": 181.06,
#             "tax_amount": 14.26,
#             "date": "2023-07-18",
#             "items": [
#                 { "name": "Seaweed & Beancurd Salad", "price": 7.5, "quantity": 1 },
#                 { "name": "Sweet & Sour Pork Baby Back Ribs", "price": 14.5, "quantity": 1 },
#                 { "name": "Hot & Sour Soup", "price": 12.5, "quantity": 1 },
#                 { "name": "Pork Xiao Long Bao", "price": 15.5, "quantity": 1 },
#                 { "name": "Sticky Rice & Pork Shao Mai", "price": 10.5, "quantity": 1 },
#                 { "name": "Taiwanese Cabbage w / Garlic", "price": 14.0, "quantity": 1 },
#                 { "name": "Vegan Dumplings", "price": 15.5, "quantity": 1 },
#                 { "name": "Shrimp & Pork Spicy Wontons", "price": 15.0, "quantity": 1 },
#                 { "name": "Pork Chop Fried Rice", "price": 18.0, "quantity": 1 },
#                 { "name": "Chicken Shanghai Rice Cakes", "price": 16.0, "quantity": 1 },
#             ],
#         }
class ReceiptCreate(BaseModel):
    merchant_name: str
    total_amount: float
    tax_amount: float
    tip_amount: float
    date: str
    items: List[ItemBase]


class ReceiptNoItems(ReceiptBase):
    id: int
    room_code: str
    owner_id: int
    

class Receipt(ReceiptNoItems):
    items: List[ItemWithUsers]

    class Config:
        from_attributes = True

class ReceiptUpload(BaseModel):
    room_code: str
    receipt_img_url: str
