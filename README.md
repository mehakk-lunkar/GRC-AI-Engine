# GRC-AI-Engine
AI Engine to provide a list of tools and their steps based on Compliance Task and Compliance Name.
<img width="850" alt="Screenshot 2025-05-31 at 11 52 36 AM" src="https://github.com/user-attachments/assets/f95dce39-0f97-4682-9457-0d2f4470f271" />

### Lookup Endpoint Example
*Replace the `<token>` placeholder with your JWT token.*
You can test the GRC AI Engine lookup endpoint using the following `curl` request: 

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/ai-engine/v1/lookup' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "Maintain separate admin and user accounts",
  "compliance": "NIST 800-171"
}'

