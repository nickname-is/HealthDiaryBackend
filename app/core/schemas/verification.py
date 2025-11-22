from pydantic import BaseModel


class EmailVerificationRequest(BaseModel):
    email: str


class Verification(BaseModel):
    otp_code: str


class EmailVerification(Verification):
    email: str


class ResetPasswordVerification(Verification):
    email: str
    new_password: str
