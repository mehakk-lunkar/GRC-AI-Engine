from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

payload = {"sub": "test_user"}  

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print("Bearer", token)

#Bearer = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIifQ.-hbe4pbm5KX_rVNVdg7Fua2ukJeRedKRV5S5Bc5wgck