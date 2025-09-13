import logging
import warnings

import uvicorn

logger = logging.getLogger(__name__)
warnings.simplefilter(action="ignore", category=FutureWarning)
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.basicConfig(
    format="%(asctime)s %(levelname)s # %(name)s # %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    uvicorn.run("paperback_cover.main:app", host="0.0.0.0", port=9000, log_level="info")
