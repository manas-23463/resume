import os
import sys
from mangum import Mangum

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

# Create ASGI handler for Vercel
handler = Mangum(app, lifespan="off")

# Export the handler for Vercel
__all__ = ["handler"]

