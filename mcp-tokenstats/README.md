# TokenStats MCP Server

Remote MCP (Model Control Protocol) server for pulling token usage statistics from Gemini Flash 2.5.

## Features

- **Token Counting**: Accurate token counting using Gemini API
- **Cost Estimation**: Calculate estimated costs based on token usage
- **Statistics**: Provides comprehensive token statistics including:
  - Input tokens
  - Estimated output tokens
  - Estimated cost (USD)
  - Maximum tokens remaining
  - Compression ratio

## Setup

### 1. Install Dependencies

```powershell
cd "C:\AI Agents\CapstoneProject\mcp-tokenstats"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and set your API key:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add your Google API key:

```env
GOOGLE_API_KEY=your-actual-api-key-here
PORT=8000
```

Or set it in PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your-api-key-here"
```

### 3. Run the Server

**Recommended: Use the run script (avoids Windows popup issues):**

```powershell
.\run-server.ps1
```

Or use the batch file:

```powershell
.\run-server.bat
```

**Alternative: Direct Python execution:**

```powershell
python server.py
```

Or using uvicorn directly:

```powershell
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## API Endpoints

### POST /tokenize

Get token usage statistics for a given prompt.

**Request:**
```json
{
  "model": "gemini-2.5-flash",
  "prompt": "Summarize: Your text here"
}
```

**Response:**
```json
{
  "input_tokens": 254,
  "estimated_output_tokens": 120,
  "estimated_cost_usd": 0.00198,
  "max_tokens_remaining": 3300,
  "compression_ratio": 0.47
}
```

### GET /

Health check and service information.

### GET /health

Health check endpoint.

## Usage Examples

### PowerShell

```powershell
$body = @{
    model = "gemini-2.5-flash"
    prompt = "Summarize: The quick brown fox jumps over the lazy dog."
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/tokenize" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$response | ConvertTo-Json -Depth 10
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/tokenize",
    json={
        "model": "gemini-2.5-flash",
        "prompt": "Summarize: Your text here"
    }
)

print(response.json())
```

### cURL

```bash
curl -X POST http://localhost:8000/tokenize \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "prompt": "Summarize: Your text here"
  }'
```

## Model Support

Currently optimized for:
- **Gemini 2.5 Flash** - Primary model with full token counting support

Other models can be specified but will use Gemini's tokenizer for estimation.

## Token Limits

- **Max Input Tokens**: 1,048,576 (1M tokens)
- **Max Output Tokens**: 65,536 (64K tokens)

## Cost Calculation

Cost estimation is based on:
- Input tokens × Input cost per million tokens
- Estimated output tokens × Output cost per million tokens

**Note**: Update pricing constants in `server.py` based on current Gemini Flash 2.5 pricing.

## Error Handling

The server returns appropriate HTTP status codes:
- `200`: Success
- `500`: Server error (e.g., API key invalid, network issues)

## Security

- Store API keys in `.env` file (not committed to version control)
- Use environment variables in production
- Consider adding authentication middleware for production deployments

## Development

To run in development mode with auto-reload:

```powershell
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## License

MIT

