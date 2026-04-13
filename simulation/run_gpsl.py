"""CLI for the Phase 2 GPSL experiment."""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from simulation.config import load_config


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2 — GPSL Cipher Encoding & Operator-Level Distance"
    )
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--seed", type=int, help="Override experiment seed")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and exit")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.seed is not None:
        config.seed = args.seed

    output_base = args.output_dir or config.output_dir
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = Path(output_base) / f"run-{timestamp}"

    if args.dry_run:
        print(f"Config loaded: {len(config.agent_configs)} agents")
        print(f"Rounds: {config.num_rounds}, Payloads/round: {config.payloads_per_round}")
        print(f"Output would go to: {run_dir}")

        from simulation.payloads.gpsl_spatial_templates import GPSL_SPATIAL_TEMPLATES
        print(f"GPSL payloads: {len(GPSL_SPATIAL_TEMPLATES)}")
        for p in GPSL_SPATIAL_TEMPLATES[:5]:
            print(f"  {p.payload_id}: ops={p.operators_required}")
        print(f"  ... and {len(GPSL_SPATIAL_TEMPLATES)-5} more")
        return

    run_dir.mkdir(parents=True, exist_ok=True)

    import yaml
    with open(run_dir / "config.yaml", "w") as f:
        yaml.dump({"run_timestamp": timestamp, "experiment": "phase2_gpsl"}, f)

    from simulation.experiment_gpsl import GpslExperimentRunner
    runner = GpslExperimentRunner(config, run_dir)
    asyncio.run(runner.execute())

    print(f"\nResults written to {run_dir}")
    print(f"GPSL results: {run_dir / 'gpsl_results.json'}")


if __name__ == "__main__":
    main()
