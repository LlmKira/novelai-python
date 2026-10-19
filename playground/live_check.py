"""Live smoke test against NovelAI on a DEDICATED account and proxy.

Never run this with production accounts. Reads:
  NOVELAI_TOKEN  — persistent API token (pst-...) of the test account
  NOVELAI_PROXY  — http://user:pass@host:port (dedicated proxy)
Optional: NOVELAI_LIVE_GENERATE=1 to also generate one 832x1216 V5 image
(costs Opus usage / Anlas on the test account).

python playground/live_check.py
"""
import asyncio
import logging
import os
import sys
import time

from novelai_python import ApiCredential, Subscription, UserData
from novelai_python.sdk.ai._enum import Model
from novelai_python.sdk.ai.generate_image import GenerateImageInfer

logger = logging.getLogger(__name__)


async def main() -> int:
    token = os.environ.get("NOVELAI_TOKEN")
    proxy = os.environ.get("NOVELAI_PROXY")
    if not token or not proxy:
        print("set NOVELAI_TOKEN and NOVELAI_PROXY (dedicated test account + proxy)")
        return 2
    cred = ApiCredential(api_token=token, proxy=proxy)

    sub = await Subscription().request(session=cred)
    print("subscription: tier", sub.tier, "active", sub.active, "anlas", sub.anlas_left,
          "usage", sub.usage.model_dump() if sub.usage else None)

    data = await UserData().request(session=cred)
    print("user/data keys:", sorted(list(data.model_dump().keys()))[:12])

    if os.environ.get("NOVELAI_LIVE_GENERATE") != "1":
        print("generation skipped (NOVELAI_LIVE_GENERATE=1 to run)")
        return 0
    gen = GenerateImageInfer.build_generate(
        prompt="1girl, solo, library, reading, very aesthetic, masterpiece, no text",
        model=Model.NAI_DIFFUSION_5_FULL, width=832, height=1216, steps=23, scale=7.0,
    )
    t0 = time.monotonic()
    resp = await gen.request(session=cred)
    dt = time.monotonic() - t0
    out = resp.save("playground/_live_out") if hasattr(resp, "save") else None
    print(f"generated in {dt:.1f}s -> {out}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(asyncio.run(main()))
