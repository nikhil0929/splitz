# from typing import List
from typing import Optional
# from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from ..base_model import Base
# from sqlalchemy.orm import relationship



class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(50))
    phone_number: Mapped[str] = mapped_column(String(30))
    email: Mapped[Optional[str]]
    # addresses: Mapped[List["Address"]] = relationship(
    #     back_populates="users", cascade="all, delete-orphan"
    # )
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, phone-number={self.phone_number!r})"