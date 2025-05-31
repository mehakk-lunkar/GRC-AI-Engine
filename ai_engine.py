from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, validator
from typing import List, Dict
from dotenv import load_dotenv
import os
import re
from groq import Groq

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ALGORITHM = "HS256"

app = FastAPI(title="GRC AI Engine")
security = HTTPBearer()
client = Groq(api_key=GROQ_API_KEY)

router = APIRouter(prefix="/api/ai-engine/v1")

# Compliance Knowledge Base for validation
compliance_knowledge_base = {
    "iso 27001": {
        "full_name": "ISO/IEC 27001",
        "aliases": ["iso 27001", "iso27001", "iso/iec 27001"]
    },
    "nist 800-53": {
        "full_name": "NIST Special Publication 800-53",
        "aliases": ["nist 800-53", "nist sp 800-53", "nist 80053"]
    },
    "soc 2": {
        "full_name": "Service Organization Control 2",
        "aliases": ["soc 2", "soc2"]
    },
    "gdpr": {
        "full_name": "General Data Protection Regulation",
        "aliases": ["gdpr"]
    },
    "hipaa": {
        "full_name": "Health Insurance Portability and Accountability Act",
        "aliases": ["hipaa"]
    },
    "pci dss": {
        "full_name": "Payment Card Industry Data Security Standard",
        "aliases": ["pci dss", "pci-dss", "pci"]
    },
    "ccpa": {
        "full_name": "California Consumer Privacy Act",
        "aliases": ["ccpa"]
    },
    "nist 800-171": {
        "full_name": "NIST Special Publication 800-171",
        "aliases": ["nist 800-171", "nist sp 800-171", "nist 800171"]
    }
}

def normalize_input(input_str):
    return input_str.lower().strip()

def find_compliance_in_kb(normalized_input):
    for key, details in compliance_knowledge_base.items():
        if normalized_input == key.lower():
            return details["full_name"]
        if normalized_input in [alias.lower() for alias in details.get("aliases", [])]:
            return details["full_name"]
    return None

def validate_compliance_input(user_input: str):
    normalized_input = normalize_input(user_input)
    full_name = find_compliance_in_kb(normalized_input)
    if not full_name:
        raise HTTPException(status_code=400, detail=f"Compliance '{user_input}' not recognized or supported.")
    return full_name

class LookupRequest(BaseModel):
    task: str
    compliance: str
    @validator("task")
    def validate_task(cls, v):
        if not re.match(r'^[A-Za-z\s]+$', v):
            raise ValueError("Compliance Task must contain only letters and spaces (no numbers or special characters).")
        if len(v.strip()) <= 20:
            raise ValueError("Compliance Task must be longer than 20 characters.")
        return v

class ToolResponse(BaseModel):
    tool: str
    Steps: str

# KnowledgeBase
knowledge_base = {
    "All servers should have an AntiMalware tool installed|ISO/IEC 27001": [
        {"tool": "Microsoft Defender", "Steps": "1. Open Settings > Update & Security > Windows Security.\n2. Click 'Virus & Threat Protection' and configure settings.\n3. Enable real-time protection.\n4. Set regular scan schedules.\n5. Monitor threat history and logs."},
        {"tool": "Sophos Intercept X", "Steps": "1. Sign up at Sophos Central.\n2. Download and install Intercept X agent.\n3. Assign the device to a policy.\n4. Configure malware and exploit protection.\n5. Monitor alerts via Sophos Central dashboard."},
        {"tool": "McAfee Endpoint Security", "Steps": "1. Download McAfee installer from the ePO.\n2. Install it on the server.\n3. Configure policies through ePO console.\n4. Enable On-Access and On-Demand scans.\n5. Review logs and update signatures regularly."},
        {"tool": "Bitdefender GravityZone", "Steps": "1. Log into GravityZone portal.\n2. Create and assign endpoint policies.\n3. Deploy the agent on target servers.\n4. Configure antimalware and firewall settings.\n5. Schedule reports and monitor security status."},
        {"tool": "Kaspersky Endpoint Security", "Steps": "1. Install Kaspersky Security Center.\n2. Deploy Kaspersky Endpoint Security agent.\n3. Apply relevant security policies.\n4. Set up scanning schedules.\n5. Monitor results and threat reports from the console."}
    ],
    "All user accounts should have MFA enabled|ISO/IEC 27001": [
        {"tool": "Microsoft Azure AD MFA", "Steps": "1. Go to Azure portal > Users > MFA.\n2. Enable MFA for target users.\n3. Configure verification methods.\n4. Instruct users to register via https://aka.ms/mfasetup.\n5. Monitor MFA status from Azure AD logs."},
        {"tool": "Google Authenticator", "Steps": "1. Install app on device.\n2. Enable 2FA in user account settings.\n3. Scan QR code or enter secret key.\n4. Verify setup with OTP.\n5. Use the app to approve future logins."},
        {"tool": "Okta MFA", "Steps": "1. Login to Okta admin portal > Security > Multifactor.\n2. Enable desired factor (e.g., SMS, Okta Verify).\n3. Assign policies to user groups.\n4. Users enroll at next login.\n5. Review MFA logs and dashboard for activity."},
        {"tool": "Authy", "Steps": "1. Install Authy app on mobile device.\n2. Register using phone number and email.\n3. Link to user accounts supporting TOTP.\n4. Use Authy for login verifications.\n5. Enable backups and multi-device sync if needed."},
        {"tool": "Duo Security", "Steps": "1. Create Duo account > Configure integrations.\n2. Install Duo Authentication Proxy if needed.\n3. Link Duo with your identity provider.\n4. Users install Duo Mobile and enroll.\n5. Monitor access logs and enforce device policies."}
    ]
}

# JWT Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Groq API
def query_groq_for_tools(task: str, compliance: str) -> List[Dict[str, str]]:
    prompt = f"""
You are a cybersecurity AI assistant. A company follows {compliance} standards.
The task is: "{task}"

Provide a list of exactly top 5 tools that help perform this task. For each tool, respond in this format:

### Tool: <tool name>
Steps:
1. Step one
2. Step two
3. Step three
4. Step four
5. Step five
---
End of response.
"""

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800,
        )
        response_text = completion.choices[0].message.content.strip()

        tools = []
        pattern = r"### Tool: (.+?)\nSteps:\n((?:\d+\..+\n?)+)"
        matches = re.findall(pattern, response_text, re.MULTILINE)
        for tool_name, steps_text in matches:
            steps_lines = [line.strip() for line in steps_text.strip().splitlines()]
            steps_clean = "\n".join(steps_lines)
            tools.append({"tool": tool_name.strip(), "Steps": steps_clean})
        if not tools:
            tools.append({"tool": "No tools found", "Steps": "No steps available"})
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Groq API: {str(e)}")

@router.post("/lookup", response_model=List[ToolResponse])
def lookup(request: LookupRequest, user=Depends(verify_token)):
    compliance_full_name = validate_compliance_input(request.compliance)  # just one value
    lookup_key = f"{request.task.strip()}|{compliance_full_name}"
    if lookup_key in knowledge_base:
        return knowledge_base[lookup_key]
    return query_groq_for_tools(request.task, compliance_full_name)

@router.get("/health")
def health():
    return {"status": "AI Engine is running"}

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai_engine:app", host="0.0.0.0", port=8000, reload=True)
