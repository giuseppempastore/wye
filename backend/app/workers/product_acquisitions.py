import argparse
import logging
import time

from app.services.product_acquisitions import ProductAcquisitionService


logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Process persisted product acquisitions")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    service = ProductAcquisitionService()
    while True:
        processed = service.process_one()
        if args.once:
            return 0
        if not processed:
            time.sleep(max(0.2, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
