"""
Shared slowapi rate-limiter instance.

Import `limiter` wherever @limiter.limit(...) decorators are needed.
The limiter is registered on the FastAPI app in main.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
