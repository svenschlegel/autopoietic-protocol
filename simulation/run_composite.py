"""CLI for the Phase 2.5 multi-agent collaboration experiment."""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from simulation.config import load_config


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2.5 — Multi-Agent Collaboration Experiment"
    )
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and exit")
    args = parser.parse_args()

    config = load_config(args.config)

    output_base = args.output_dir or config.output_dir
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = Path(output_base) / f"run-{timestamp}"

    if args.dry_run:
        print(f"Config loaded: {len(config.agent_configs)} agents")
        print(f"Output would go to: {run_dir}")
        print(f"Agent models: {[a.model for a in config.agent_configs]}")

        from simulation.payloads.composite_templates import COMPOSITE_TEMPLATES
        print(f"Composite payloads: {len(COMPOSITE_TEMPLATES)}")
        for t in COMPOSITE_TEMPLATES:
            domains = [d.name for d in t.sub_domains]
            print(f"  {t.payload_id}: {' + '.join(domains)}")
        return

    run_dir.mkdir(parents=True, exist_ok=True)

    # Save config copy
    import yaml
    with open(run_dir / "config.yaml", "w") as f:
        yaml.dump({"run_timestamp": timestamp, "experiment": "composite_collaboration"}, f)

    from simulation.experiment_composite import CompositeExperimentRunner

    runner = CompositeExperimentRunner(config, run_dir)
    asyncio.run(runner.execute())

    print(f"\nResults written to {run_dir}")
    print(f"Composite results: {run_dir / 'composite_results.json'}")
    print(f"\nTo analyze: PYTHONPATH=. python3 simulation/analysis/composite_compare.py --results {run_dir / 'composite_results.json'}")


if __name__ == "__main__":
    main()
