import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    # bot_service/bot_service.py contains: app = FastAPI(...)
    # From this directory, the import path is: bot_service:app
    uvicorn.run(
        "bot_service.bot_service:app",
        host="127.0.0.1",
        port=9000,
        reload=False,
    )

