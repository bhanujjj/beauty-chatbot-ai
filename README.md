# Beauty Chatbot AI Backend

FastAPI-based backend service for the Beauty Chatbot application. This service handles AI-powered chat interactions and product recommendations.

## Environment Variables

Create a `.env` file with:
```
OPENROUTER_API_KEY=your_api_key_here
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /chat`: Main chat endpoint
- Health check: `GET /health`

## Deployment (Render.com)

1. Push code to GitHub
2. Connect repository to Render.com
3. Create a new Web Service
4. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard 