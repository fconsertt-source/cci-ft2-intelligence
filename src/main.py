from __future__ import annotations

import argparse
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def create_evaluate_cold_chain_uc(reader=None, repository=None):
    """Placeholder factory to be monkeypatched in tests."""
    raise NotImplementedError("create_evaluate_cold_chain_uc must be monkeypatched in tests")


def evaluate_command(input_dir: Optional[str] = None, repository: Optional[object] = None):
    """Run the evaluate use case via the factory. The factory is expected to be monkeypatched in tests."""
    uc = create_evaluate_cold_chain_uc(reader=input_dir, repository=repository)
    logger.info("Running EvaluateColdChainSafetyUC...")
    results = uc.execute()
    for r in results:
        logger.info("Vaccine=%s status=%s alert=%s HER=%.3f CCM=%.2f",
                    r.vaccine_id, r.status.value, r.alert_level, r.her, r.ccm)
        for rec in r.recommendations:
            logger.info("  - %s", rec)


def main(argv: Optional[list] = None):
    parser = argparse.ArgumentParser(prog="cci-ft2-intelligence")
    parser.add_argument('--verbose', action='store_true', help='enable verbose logging')

    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("evaluate", help="Run safety evaluation use case")
    sub.add_parser("simple-pipeline", help="Run the demo simple pipeline script")

    args = parser.parse_args(argv)

    # simple logging setup suitable for tests
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if args.cmd == "evaluate":
        evaluate_command()
    elif args.cmd == "simple-pipeline":
        try:
            from scripts.simple_pipeline import run_simple_pipeline
            run_simple_pipeline()
        except Exception as e:
            logger.error("Failed to run simple-pipeline: %s", e)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
