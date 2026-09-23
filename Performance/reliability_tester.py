"""
Universal Concurrent-Load & Reliability Simulation Engine.

Framework-agnostic mathematical model calculating throughput (req/s),
outbound egress, saturation thresholds, and hardware degradation curves
when N users act concurrently against web applications and APIs.

Supports standard traffic profiles:
  - balanced_api : Standard RESTful CRUD workflow (50% GET / 30% POST / 20% PUT)
  - read_heavy   : Content catalog & read-intensive browsing (85% GET / 15% POST)
  - write_heavy  : High-volume data ingestion & transactional submissions (65% POST / 35% GET)
  - burst_ping   : High-frequency polling, health checks & telemetry pings

Run:
  python Performance/reliability_tester.py --scenario balanced_api --concurrent 500
  python Performance/reliability_tester.py --concurrent 50,100,500,1000,2000
"""
from __future__ import annotations

import os
import sys
import math
import argparse
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

# Ensure stdout uses UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Logical CPU thread detection for host capacity scaling
DETECTED_CPU_CORES = os.cpu_count() or 4
_worker_factor = DETECTED_CPU_CORES / 4.0

# --- Standardized Web/API Payload Sizes (Bytes) ---
PAYLOAD_BYTES: Dict[str, int] = {
    'health_ping': 250,           # Lightweight heartbeat / status check
    'auth_token': 1_200,          # OAuth / JWT token generation & headers
    'resource_get': 12_000,       # Standard JSON entity / collection read
    'resource_post': 3_500,       # JSON payload write / form submission
    'resource_put': 2_500,        # Update entity payload
    'dashboard_summary': 45_000,  # Aggregated analytics / metrics view
    'bulk_export': 120_000,       # Large dataset / report serialization
}

# --- Requests Per Generic User Flow ---
REQUESTS_PER_FLOW: Dict[str, List[Tuple[str, int]]] = {
    'auth_only': [('auth_token', 1)],
    'health_check': [('health_ping', 2)],
    'browse_catalog': [('resource_get', 3), ('health_ping', 1)],
    'dashboard_view': [('auth_token', 1), ('dashboard_summary', 1), ('resource_get', 2)],
    'transactional_write': [('auth_token', 1), ('resource_post', 2), ('resource_get', 1)],
    'update_batch': [('resource_get', 2), ('resource_put', 2)],
    'export_data': [('auth_token', 1), ('bulk_export', 1)],
}

# Categorization of endpoint computational weights
ENDPOINT_WEIGHT: Dict[str, str] = {
    'health_ping': 'light',
    'auth_token': 'medium',
    'resource_get': 'medium',
    'resource_post': 'write',
    'resource_put': 'write',
    'dashboard_summary': 'heavy',
    'bulk_export': 'heavy',
}

# Server throughput profiles (requests/second sustained)
SERVER_PROFILES: Dict[str, Dict[str, Any]] = {
    'dev_single_worker': {
        'label': 'Development Server (Single Worker / Thread)',
        'light_rps': 25,
        'medium_rps': 12,
        'heavy_rps': 4,
        'write_rps': 8,
    },
    'host_hardware': {
        'label': f'Host Hardware ({DETECTED_CPU_CORES} Workers on {DETECTED_CPU_CORES} CPU Cores)',
        'light_rps': round(120 * _worker_factor),
        'medium_rps': round(60 * _worker_factor),
        'heavy_rps': round(25 * _worker_factor),
        'write_rps': round(40 * _worker_factor),
    },
    'cloud_small': {
        'label': 'Cloud Standard (2-4 Workers, 2GB RAM Container)',
        'light_rps': 100,
        'medium_rps': 50,
        'heavy_rps': 20,
        'write_rps': 35,
    },
    'cloud_scaled': {
        'label': 'Cloud Production Cluster (8-16 Workers + Redis Cache)',
        'light_rps': 350,
        'medium_rps': 180,
        'heavy_rps': 75,
        'write_rps': 120,
    },
}


@dataclass
class ScenarioMix:
    name: str
    description: str
    flows: Dict[str, float]  # fraction of users per flow (must sum to 1.0)


SCENARIOS: Dict[str, ScenarioMix] = {
    'balanced_api': ScenarioMix(
        name='balanced_api',
        description='Standard RESTful API workload with balanced read/write distribution',
        flows={
            'browse_catalog': 0.40,
            'dashboard_view': 0.25,
            'transactional_write': 0.25,
            'export_data': 0.10,
        },
    ),
    'read_heavy': ScenarioMix(
        name='read_heavy',
        description='Read-dominated traffic (catalogs, dashboards, content feeds)',
        flows={
            'browse_catalog': 0.60,
            'dashboard_view': 0.30,
            'export_data': 0.05,
            'transactional_write': 0.05,
        },
    ),
    'write_heavy': ScenarioMix(
        name='write_heavy',
        description='Transactional rush (batch data ingestion, checkout/submit spikes)',
        flows={
            'transactional_write': 0.55,
            'update_batch': 0.25,
            'dashboard_view': 0.15,
            'browse_catalog': 0.05,
        },
    ),
    'burst_ping': ScenarioMix(
        name='burst_ping',
        description='High-frequency heartbeat, webhook pings and auth token validation',
        flows={
            'health_check': 0.65,
            'auth_only': 0.25,
            'browse_catalog': 0.10,
        },
    ),
}


def calculate_flow_stats(flow_key: str) -> Tuple[int, int]:
    """Return total (request_count, response_bytes) for one user executing a flow."""
    total_requests = 0
    total_bytes = 0
    for payload_key, count in REQUESTS_PER_FLOW.get(flow_key, []):
        total_requests += count
        total_bytes += PAYLOAD_BYTES.get(payload_key, 1000) * count
    return total_requests, total_bytes


def simulate_scenario(
    concurrent_users: int,
    scenario: ScenarioMix,
    burst_seconds: int = 120,
) -> Dict[str, Any]:
    """Calculate aggregated traffic and resource demand for a scenario mix."""
    users_by_flow = {
        flow: int(round(concurrent_users * fraction))
        for flow, fraction in scenario.flows.items()
    }
    
    # Correct rounding drift
    drift = concurrent_users - sum(users_by_flow.values())
    if drift != 0:
        largest_flow = max(scenario.flows, key=scenario.flows.get)
        users_by_flow[largest_flow] += drift

    total_requests = 0
    total_egress_bytes = 0

    for flow, user_count in users_by_flow.items():
        if user_count <= 0:
            continue
        req_per_user, bytes_per_user = calculate_flow_stats(flow)
        total_requests += user_count * req_per_user
        total_egress_bytes += user_count * bytes_per_user

    burst_seconds = max(burst_seconds, 1)
    arrival_rps = total_requests / burst_seconds

    return {
        'users_by_flow': users_by_flow,
        'total_requests': total_requests,
        'total_egress_mb': total_egress_bytes / (1024 * 1024),
        'total_ingress_mb': (total_egress_bytes * 0.15) / (1024 * 1024),
        'arrival_rps': arrival_rps,
        'burst_seconds': burst_seconds,
    }


def calculate_effective_capacity(scenario: ScenarioMix, server_key: str) -> float:
    """Calculate weighted sustained RPS capacity for the scenario request mix."""
    profile = SERVER_PROFILES[server_key]
    weighted_rps = 0.0
    total_weights = 0.0

    for flow, fraction in scenario.flows.items():
        for payload_key, count in REQUESTS_PER_FLOW.get(flow, []):
            weight_class = ENDPOINT_WEIGHT.get(payload_key, 'medium')
            rps = profile.get(f'{weight_class}_rps', profile['medium_rps'])
            weighted_rps += fraction * count * rps
            total_weights += fraction * count

    return (weighted_rps / total_weights) if total_weights > 0 else float(profile['medium_rps'])


def assess_reliability_state(util_pct: float) -> Tuple[str, str]:
    """
    Assess system reliability and degradation tier based on capacity utilization.
    Returns (status_badge, description).
    """
    if util_pct < 60.0:
        return 'OPTIMAL', 'Optimal performance — zero queueing, latency < 50ms'
    elif util_pct < 85.0:
        return 'HEALTHY', 'Stable throughput — minor queue buffers, latency < 150ms'
    elif util_pct < 100.0:
        return 'SATURATED', 'Capacity limit reached — elevated queuing, latency 200-500ms'
    elif util_pct < 150.0:
        return 'OVERLOADED', 'Bottleneck — request queue buildup, potential 504 timeouts'
    else:
        return 'CRITICAL', 'System overload — connection rejection, widespread timeouts & drops'


def run_simulation(
    scenarios: List[ScenarioMix],
    servers: List[str],
    concurrent_list: List[int],
    burst_seconds: int = 120,
    total_sample_users: int = 2000,
):
    """Execute and render the analytical concurrent load simulation."""
    print("=" * 78)
    print(" ⚡ UniversalTester: Concurrent Load & Reliability Simulation Engine")
    print("=" * 78)
    print(f" Sample Population : {total_sample_users:,} total simulated users")
    print(f" Burst Window      : {burst_seconds}s (concurrent execution window)")
    print(f" Concurrency Tiers : {', '.join(str(c) for c in concurrent_list)}")
    print(f" Host Environment  : {DETECTED_CPU_CORES} CPU Cores / Logical Processors")
    print("=" * 78)

    for scenario in scenarios:
        print(f"\n▶ Scenario: {scenario.name.upper()}")
        print(f"  Description: {scenario.description}")
        print()

        header = f" {'Concurrent':>10} | {'% of Sample':>11} | {'Requests':>9} | {'Egress MB':>10} | {'Req/s':>8}"
        print(header)
        print(" " + "─" * (len(header) - 1))

        for concurrent in concurrent_list:
            agg = simulate_scenario(concurrent, scenario, burst_seconds)
            pct = (concurrent / total_sample_users * 100.0) if total_sample_users > 0 else 0.0
            print(
                f" {concurrent:>10,} | {pct:>10.1f}% | {agg['total_requests']:>9,} | "
                f"{agg['total_egress_mb']:>9.2f}MB | {agg['arrival_rps']:>8.1f}"
            )

        print("\n  Hardware Sizing & Reliability Thresholds:")
        for server_key in servers:
            profile = SERVER_PROFILES[server_key]
            cap_rps = calculate_effective_capacity(scenario, server_key)
            print(f"   • {profile['label']} (Capacity: ~{cap_rps:.0f} req/s)")

            for concurrent in concurrent_list:
                agg = simulate_scenario(concurrent, scenario, burst_seconds)
                util = (agg['arrival_rps'] / cap_rps) * 100.0 if cap_rps > 0 else 999.0
                status, desc = assess_reliability_state(util)
                print(f"     └─ {concurrent:>5,} users ──► Util: {util:>5.0f}% [{status:<10}] {desc}")

    print("\n" + "=" * 78)
    print(" 💡 Sizing & Reliability Guidance:")
    print("  • Small / Single-Worker Server : Ideal for dev & testing up to ~100 concurrent.")
    print("  • Multi-Worker Host Server    : Sustains 500-1,000 concurrent with moderate queuing.")
    print("  • Scaled Cloud Cluster        : Recommended for peak events exceeding 1,000+ users.")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='UniversalTester Concurrency & Reliability Simulator'
    )
    parser.add_argument(
        '--scenario',
        choices=['all', 'balanced_api', 'read_heavy', 'write_heavy', 'burst_ping'],
        default='balanced_api',
        help='Traffic pattern (default: balanced_api)',
    )
    parser.add_argument(
        '--server',
        choices=['all', 'dev_single_worker', 'host_hardware', 'cloud_small', 'cloud_scaled'],
        default='all',
        help='Server capacity profile (default: all)',
    )
    parser.add_argument(
        '--concurrent',
        type=str,
        default='50,100,500,1000',
        help='Comma-separated concurrent user volumes to simulate',
    )
    parser.add_argument(
        '--burst-seconds',
        type=int,
        default=120,
        help='Duration in seconds of the peak burst window (default: 120)',
    )
    parser.add_argument(
        '--total-users',
        type=int,
        default=2000,
        help='Total user population sample (default: 2000)',
    )

    args = parser.parse_args()

    # Parse concurrency list
    raw_concurrent = [int(x.strip()) for x in args.concurrent.split(',') if x.strip()]
    if len(raw_concurrent) == 1:
        target = raw_concurrent[0]
        milestones = [10, 25, 50, 100, 200, 500, 1000, 2000, 3000, 5000]
        curve = [m for m in milestones if m < target]
        if not curve or curve[-1] != target:
            curve.append(target)
        concurrent_list = sorted(list(set(curve)))
    else:
        concurrent_list = sorted(raw_concurrent)

    total_users = max(args.total_users, max(concurrent_list) if concurrent_list else 2000)

    scenarios = (
        [SCENARIOS[args.scenario]]
        if args.scenario != 'all'
        else list(SCENARIOS.values())
    )
    servers = (
        [args.server]
        if args.server != 'all'
        else list(SERVER_PROFILES.keys())
    )

    run_simulation(
        scenarios=scenarios,
        servers=servers,
        concurrent_list=concurrent_list,
        burst_seconds=args.burst_seconds,
        total_sample_users=total_users,
    )


if __name__ == '__main__':
    main()
