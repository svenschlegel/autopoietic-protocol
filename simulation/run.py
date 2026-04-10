"""CLI orchestrator for the Gravitational Dictatorship Simulation."""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from simulation.config import load_config


def main():
    parser = argparse.ArgumentParser(description="Gravitational Dictatorship Simulation — Phase A")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--seed", type=int, help="Override experiment.seed (for multi-seed variance runs)")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and exit")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.output_dir:
        config.output_dir = args.output_dir
    if args.seed is not None:
        config.seed = args.seed

    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = Path(config.output_dir) / f"run-{timestamp}"

    if args.dry_run:
        print(f"Config loaded: {config.num_agents} agents, {config.num_rounds} rounds")
        print(f"Algorithms: {', '.join(config.routing_algorithms)}")
        print(f"Output would go to: {run_dir}")
        print(f"Agent models: {[a.model for a in config.agent_configs]}")
        return

    run_dir.mkdir(parents=True, exist_ok=True)

    # Save config copy
    import yaml
    with open(run_dir / "config.yaml", "w") as f:
        yaml.dump({"run_timestamp": timestamp}, f)

    # Run experiment
    from simulation.experiment import ExperimentRunner

    runner = ExperimentRunner(config, run_dir)
    results = asyncio.run(runner.execute())

    # Write summary
    with open(run_dir / "summary.json", "w") as f:
        json.dump(results["summary"], f, indent=2)

    with open(run_dir / "results.json", "w") as f:
        json.dump(results["detailed"], f, indent=2)

    print(f"\nResults written to {run_dir}")
    print(f"Summary: {run_dir / 'summary.json'}")

    # Generate plots if enabled
    if config.plots:
        try:
            from simulation.metrics.plots import generate_all_plots
            generate_all_plots(results["detailed"], run_dir / "plots")
            print(f"Plots: {run_dir / 'plots'}")
        except ImportError:
            print("matplotlib not available — skipping plots")


if __name__ == "__main__":
    main()
