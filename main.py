from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Beauty Chatbot AI",
    description="AI-powered beauty product recommendation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Beauty Chatbot AI Backend is running",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "environment": os.getenv("ENV", "production")
    }

@app.get("/favicon.ico")
def favicon():
    return PlainTextResponse("")

@app.get("/apple-touch-icon.png")
@app.get("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return PlainTextResponse("")

@app.head("/")
def head_root():
    return Response(status_code=200)

# --- AI chat and product recommendation logic ---

# Sample product data
products = [
    {
        "name": "Gentle Cleanser",
        "type": "face wash",
        "skin_type": "acne-prone",
        "price": 27.89,
        "image_url": "https://media.istockphoto.com/id/1218450334/photo/flat-lay-flatlay-top-above-overhead-view-photo-of-blank-empty-white-tube-for-cream-isolated.jpg?s=612x612&w=0&k=20&c=Fp38-GfhHTe-tweUOpalawrY1ydgyehbNtAmOcctZJQ=",
        "description": "A gentle cleanser perfect for acne-prone skin, helps control breakouts while maintaining skin's natural balance."
    },
    # ... add more products as needed ...
]

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[float] = None  # Add timestamp for message ordering

class ChatRequest(BaseModel):
    message: str
    chatHistory: Optional[List[ChatMessage]] = []

async def get_ai_response(message: str, chat_history: List[ChatMessage], product_context: str) -> str:
    """Get AI response with product context"""
    try:
        OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
        OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
        
        if not OPENROUTER_API_KEY:
            return "API key not configured."

        # Create system message with formatting rules
        system_message = f"""You are a helpful beauty advisor. Follow these strict formatting rules:

1. Keep responses to 2-3 lines maximum for the main recommendation
2. When recommending products, use this format:

[Product Recommendation]
[Leave a blank line]
**REASON:**
[1-2 lines explaining why, focusing on user's needs]

3. Use this product information: {product_context}
4. Reference previous conversations when relevant
5. Keep responses focused and concise
6. In end ask for any other questions"""

        # Prepare messages with limited history
        messages = [{"role": "system", "content": system_message}]
        
        # Use last 5 messages for context
        recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
        messages.extend([{"role": msg.role, "content": msg.content} for msg in recent_history])
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": messages,
            "max_tokens": 250
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=request_data)
        response_data = response.json()

        if response.status_code != 200 or "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            return f"I apologize, but I encountered an error: {error_msg}"

        return response_data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"Error in AI response: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}"

@app.post("/chat")
async def chat(request: ChatRequest):
    # Filter products based on message content
    relevant_products = []
    message_lower = request.message.lower()
    if any(word in message_lower for word in ["acne", "pimple", "breakout"]):
        relevant_products = [p for p in products if p["skin_type"] == "acne-prone"]
    elif "face wash" in message_lower or "cleanser" in message_lower:
        relevant_products = [p for p in products if p["type"] == "face wash"]
    product_context = ""
    if relevant_products:
        product_context = "Available products:\n" + "\n".join([
            f"- {p['name']}: {p['description']} (${p['price']})"
            for p in relevant_products
        ])
    ai_response = await get_ai_response(request.message, request.chatHistory, product_context)
    return {
        "reply": ai_response,
        "recommendations": relevant_products
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 
