import argparse
from dispatcher import DispatchSimulator
from router import DijkstraRouter


def main() -> None:
    parser = argparse.ArgumentParser(description="Ambulance Dispatch Prototype One (Dijkstra).")
    parser.add_argument("--calls", default="calls.csv")
    parser.add_argument("--priorities", default="call_priority.csv")
    parser.add_argument("--ambulances", default="ambulance.csv")
    parser.add_argument("--network", default="location_network.csv")
    parser.add_argument("--log", default="/var/log/ambulance_call_log.csv")
    parser.add_argument("--runs", type=int, default=1, help="Run the full dispatch simulation N times (for testing).")
    args = parser.parse_args()

    router = DijkstraRouter()
    sim = DispatchSimulator(
        calls_csv=args.calls,
        priority_csv=args.priorities,
        ambulance_csv=args.ambulances,
        network_csv=args.network,
        log_path=args.log,
        router=router,
    )

    sim.run_multiple(runs=args.runs)


if __name__ == "__main__":
    main()
