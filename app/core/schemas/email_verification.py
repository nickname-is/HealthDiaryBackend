from pydantic import BaseModel


class EmailVerification(BaseModel):
    otp_code: str
