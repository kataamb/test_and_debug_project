from pydantic import BaseModel, ConfigDict
from uuid import UUID

class User(BaseModel):
    id: UUID = UUID("00000000-0000-0000-0000-000000000000")
    nickname: str
    fio: str
    email: str
    phone_number: str
    password: str

    model_config = ConfigDict(
        from_attributes=True
    )
