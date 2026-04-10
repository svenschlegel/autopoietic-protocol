"""Simulation configuration — loads from YAML + environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass
class AgentConfig:
    name: str
    model: str
    primary_domain: str  # "SEMANTIC", "DETERMINISTIC", "SPATIAL", "TEMPORAL"
    secondary_domains: list[str] = field(default_factory=list)


@dataclass
class SimulationConfig:
    # Experiment shape
    num_agents: int = 10
    num_rounds: int = 50
    payloads_per_round: int = 4
    seed: int = 42
    routing_algorithms: list[str] = field(
        default_factory=lambda: ["gravitational", "random", "round_robin", "elo", "equal_mass"]
    )

    # Agents
    agent_configs: list[AgentConfig] = field(default_factory=list)
    default_model: str = "anthropic/claude-3.5-haiku"
    judge_model: str = "anthropic/claude-sonnet-4"
    initial_mass: float = 1.0
    max_load: int = 3

    # Payloads
    domain_weights: dict[str, float] = field(
        default_factory=lambda: {
            "SEMANTIC": 0.35,
            "DETERMINISTIC": 0.30,
            "SPATIAL": 0.20,
            "TEMPORAL": 0.15,
        }
    )
    bounty_range: tuple[float, float] = (1.0, 50.0)
    difficulty_range: tuple[float, float] = (0.3, 0.9)
    execution_window: int = 60  # seconds

    # Protocol constants
    alpha: float = 0.8
    beta: float = 1.5
    slash_rate: float = 0.05
    quarantine_threshold: int = 5
    sigma_min: float = 0.1
    sigma_max: float = 3.0
    quality_threshold: float = 0.5

    # V3.5 Mass Accrual Reform — see docs/MASS_ACCRUAL_REFORM_v0.1.md
    # Defaults preserve V3.4 behavior (no rebase, no decay) so existing
    # configs/runs are unchanged unless they explicitly opt in.
    sublinear_accrual: bool = True  # §3.2 log-saturation; False = V3.4 linear control
    season_length: int = 0          # rounds; 0 disables seasonal rebase
    season_rebase_c: float = 100.0  # log-compression scaling factor (§3.3)
    decay_rate: float = 0.0         # per-round routing-mass decay δ (§3.4)

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Output
    output_dir: str = "./results"
    plots: bool = True


def load_config(config_path: str) -> SimulationConfig:
    """Load config from YAML file, overlay env vars."""
    load_dotenv()

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    exp = raw.get("experiment", {})
    agents_raw = raw.get("agents", {})
    payloads_raw = raw.get("payloads", {})
    protocol = raw.get("protocol", {})
    openrouter = raw.get("openrouter", {})
    output = raw.get("output", {})

    # Build agent configs
    agent_configs = []
    for a in agents_raw.get("models", []):
        agent_configs.append(AgentConfig(
            name=a["name"],
            model=a["model"],
            primary_domain=a["primary_domain"],
            secondary_domains=a.get("secondary_domains", []),
        ))

    config = SimulationConfig(
        num_agents=exp.get("num_agents", 10),
        num_rounds=exp.get("num_rounds", 50),
        payloads_per_round=exp.get("payloads_per_round", 4),
        seed=exp.get("seed", 42),
        routing_algorithms=exp.get("routing_algorithms", ["gravitational", "random", "round_robin", "elo", "equal_mass"]),
        agent_configs=agent_configs,
        default_model=agents_raw.get("default_model", "anthropic/claude-3.5-haiku"),
        judge_model=agents_raw.get("judge_model", "anthropic/claude-sonnet-4"),
        initial_mass=agents_raw.get("initial_mass", 1.0),
        max_load=agents_raw.get("max_load", 3),
        domain_weights=payloads_raw.get("domain_weights", {"SEMANTIC": 0.35, "DETERMINISTIC": 0.30, "SPATIAL": 0.20, "TEMPORAL": 0.15}),
        bounty_range=tuple(payloads_raw.get("bounty_range", [1.0, 50.0])),
        difficulty_range=tuple(payloads_raw.get("difficulty_range", [0.3, 0.9])),
        execution_window=payloads_raw.get("execution_window", 60),
        alpha=protocol.get("alpha", 0.8),
        beta=protocol.get("beta", 1.5),
        slash_rate=protocol.get("slash_rate", 0.05),
        quarantine_threshold=protocol.get("quarantine_threshold", 5),
        sigma_min=protocol.get("sigma_min", 0.1),
        sigma_max=protocol.get("sigma_max", 3.0),
        quality_threshold=protocol.get("quality_threshold", 0.5),
        sublinear_accrual=protocol.get("sublinear_accrual", True),
        season_length=protocol.get("season_length", 0),
        season_rebase_c=protocol.get("season_rebase_c", 100.0),
        decay_rate=protocol.get("decay_rate", 0.0),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openrouter_base_url=openrouter.get("base_url", "https://openrouter.ai/api/v1"),
        output_dir=output.get("dir", "./results"),
        plots=output.get("plots", True),
    )

    if not config.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY not set in environment")

    return config
