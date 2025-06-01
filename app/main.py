from fastapi import FastAPI, HTTPException
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
        "api_key_configured": bool(OPENROUTER_API_KEY),
        "environment": os.getenv("ENV", "production")
    }

@app.get("/favicon.ico")
def favicon():
    return PlainTextResponse("")

@app.get("/apple-touch-icon.png")
@app.get("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return PlainTextResponse("")

# Load OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not found in environment variables")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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
    {
        "name": "Exfoliating Face Wash",
        "type": "face wash",
        "skin_type": "acne-prone",
        "price": 21.64,
        "image_url": "https://media.istockphoto.com/id/1218450334/photo/flat-lay-flatlay-top-above-overhead-view-photo-of-blank-empty-white-tube-for-cream-isolated.jpg?s=612x612&w=0&k=20&c=Fp38-GfhHTe-tweUOpalawrY1ydgyehbNtAmOcctZJQ=",
        "description": "An exfoliating face wash that helps remove dead skin cells and unclog pores, ideal for acne-prone skin."
    },
    {
        "name": "Foaming Face Wash",
        "type": "face wash",
        "skin_type": "acne-prone",
        "price": 19.06,
        "image_url": "https://media.istockphoto.com/id/1218450334/photo/flat-lay-flatlay-top-above-overhead-view-photo-of-blank-empty-white-tube-for-cream-isolated.jpg?s=612x612&w=0&k=20&c=Fp38-GfhHTe-tweUOpalawrY1ydgyehbNtAmOcctZJQ=",
        "description": "A foaming face wash that deeply cleanses while being gentle on sensitive, acne-prone skin."
    }
]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chatHistory: Optional[List[ChatMessage]] = []

async def get_ai_response(message: str, chat_history: List[ChatMessage], product_context: str) -> str:
    """Get AI response with product context"""
    try:
        print(f"API Key present: {'Yes' if OPENROUTER_API_KEY else 'No'}")
        
        # Create system message with product context
        system_message = f"""You are a helpful beauty advisor. When recommending products, use this product information:
{product_context}
Keep responses concise and focused on the user's question. If recommending products, explain why they would be good for the user's needs."""

        # Prepare messages for the AI
        messages = [
            {"role": "system", "content": system_message}
        ]
        messages.extend([{"role": msg.role, "content": msg.content} for msg in chat_history])
        messages.append({"role": "user", "content": message})

        print(f"Sending request to OpenRouter with messages: {json.dumps(messages, indent=2)}")

        # Make request to OpenRouter with smaller model and token limit
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": "mistralai/mistral-7b-instruct",  # Using smaller model
            "messages": messages,
            "max_tokens": 250  # Increasing token limit for longer responses
        }
        
        print(f"Request data: {json.dumps(request_data, indent=2)}")
        
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=request_data
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        
        response_data = response.json()
        
        if response.status_code != 200 or "error" in response_data:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"OpenRouter API error: {error_msg}")
            return f"I apologize, but I encountered an error: {error_msg}"
            
        return response_data["choices"][0]["message"]["content"]
        
    except Exception as e:
        print(f"Error in AI response: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"I apologize, but I encountered an error: {str(e)}"

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print(f"Received message: {request.message}")
        
        # Filter products based on message content
        relevant_products = []
        message_lower = request.message.lower()
        
        # Simple keyword matching for demonstration
        if any(word in message_lower for word in ["acne", "pimple", "breakout"]):
            relevant_products = [p for p in products if p["skin_type"] == "acne-prone"]
        elif "face wash" in message_lower or "cleanser" in message_lower:
            relevant_products = [p for p in products if p["type"] == "face wash"]
        
        print(f"Found {len(relevant_products)} matching products")

        # Create product context for AI
        product_context = ""
        if relevant_products:
            product_context = "Available products:\n" + "\n".join([
                f"- {p['name']}: {p['description']} (${p['price']})"
                for p in relevant_products
            ])
        
        # Get AI response with product context
        ai_response = await get_ai_response(request.message, request.chatHistory, product_context)
        
        return {
            "reply": ai_response,
            "recommendations": relevant_products
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e)) 