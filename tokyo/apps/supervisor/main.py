import asyncio
import logging

from tokyo.packages.common.logging import configure_logging


async def run() -> None:
    configure_logging("info")
    logging.getLogger(__name__).info("Supervisor skeleton started.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

