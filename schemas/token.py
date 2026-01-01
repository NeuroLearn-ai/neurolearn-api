from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class GoogleLogin(BaseModel):
    token: str # The ID Token get from the Google Button on the Frontend