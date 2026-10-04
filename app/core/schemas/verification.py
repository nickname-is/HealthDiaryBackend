from enum import Enum as PythonEnum

from pydantic import BaseModel


class VerificationTypes(PythonEnum):
    EMAIL_VERIFICATION = "email_verification"
    RESET_PASSWORD = "reset_password"


class EmailVerificationRequest(BaseModel):
    email: str


class Verification(BaseModel):
    otp_code: str


class EmailVerification(Verification):
    email: str


class ResetPasswordVerification(Verification):
    email: str
    new_password: str
