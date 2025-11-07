import os
import sys
from mangum import Mangum

# Add the parent directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Create ASGI handler for Vercel
handler = Mangum(app)

# This is the entry point for Vercel serverless functions
# The FastAPI app is imported from main.py
