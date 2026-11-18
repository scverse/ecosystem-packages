import sys

import httpx2

# httpx-retries imports `httpx`; point it to httpx2 (https://github.com/will-ockmore/httpx-retries/issues/73)
sys.modules["httpx"] = httpx2
