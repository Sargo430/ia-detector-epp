"""
Entrypoint del edge agent.
Maneja: setup, graceful shutdown con SIGINT/SIGTERM, reinicio ante crashes.
"""
import asyncio
import signal
import sys

from agent.pipeline import EdgePipeline
from utils.logger import setup_logging, get_logger

log = get_logger("main")


async def run_with_restart(max_crashes: int = 10) -> None:
    """Reinicia el pipeline automáticamente ante fallos inesperados."""
    crashes = 0

    while crashes < max_crashes:
        pipeline = EdgePipeline()
        try:
            pipeline.setup()
            await pipeline.run()
            break  # salida limpia (stop() fue llamado)
        except KeyboardInterrupt:
            log.info("main.shutdown.signal")
            pipeline.stop()
            break
        except FileNotFoundError as e:
            log.error("main.fatal", error=str(e))
            sys.exit(1)
        except Exception as e:
            crashes += 1
            log.error(
                "main.crash",
                error=str(e),
                crash_count=crashes,
                max=max_crashes,
            )
            if crashes < max_crashes:
                wait = min(crashes * 5, 60)
                log.info("main.restart", wait=wait)
                await asyncio.sleep(wait)
            else:
                log.error("main.max_crashes_reached")
                sys.exit(1)


def main() -> None:
    setup_logging()
    log.info("edge_agent.start")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    pipeline_ref: list[EdgePipeline] = []

    def handle_signal(sig, frame):
        log.info("main.signal", signal=sig)
        for p in pipeline_ref:
            p.stop()
        loop.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(run_with_restart())
    finally:
        loop.close()
        log.info("edge_agent.stopped")


if __name__ == "__main__":
    main()
