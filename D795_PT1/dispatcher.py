import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Protocol, Optional


class Router(Protocol):
    name: str

    def shortest_path(self, graph: Dict[str, List[Tuple[str, float]]], start: str, goal: str) -> Tuple[List[str], float]:
        ...


@dataclass(frozen=True)
class Call:
    call_id: int
    location: str
    call_type: str
    priority: int
    received_index: int  # preserves file order


@dataclass(frozen=True)
class Ambulance:
    ambulance_number: str
    staging_location: str


class DispatchSimulator:
    def __init__(
        self,
        calls_csv: str,
        priority_csv: str,
        ambulance_csv: str,
        network_csv: str,
        log_path: str,
        router: Router,
    ) -> None:
        self.calls_csv = calls_csv
        self.priority_csv = priority_csv
        self.ambulance_csv = ambulance_csv
        self.network_csv = network_csv
        self.log_path = log_path
        self.router = router

        self.priority_by_type = self._load_priorities()
        self.ambulances = self._load_ambulances()
        self.graph = self._load_graph()

    def _load_priorities(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        with open(self.priority_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                out[row["Call Type"].strip()] = int(row["Priority"])
        return out

    def _load_ambulances(self) -> List[Ambulance]:
        out: List[Ambulance] = []
        with open(self.ambulance_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                out.append(
                    Ambulance(
                        ambulance_number=row["Ambulance Number"].strip(),
                        staging_location=row["Staging Location"].strip(),
                    )
                )
        return out

    def _load_graph(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        Builds an undirected weighted graph using:
        edge_weight = Travel Time + Traffic Delay
        """
        graph: Dict[str, List[Tuple[str, float]]] = {}
        with open(self.network_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                start = row["Start"].strip()
                end = row["End"].strip()

                travel_time = float(row["Travel Time"])
                traffic_delay = float(row["Traffic Delay"])
                weight = travel_time + traffic_delay

                graph.setdefault(start, []).append((end, weight))
                graph.setdefault(end, []).append((start, weight))  # treat as bidirectional for routing simulation
        return graph

    def _load_calls(self) -> List[Call]:
        calls: List[Call] = []
        with open(self.calls_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                call_type = row["Call Type"].strip()
                priority = self.priority_by_type.get(call_type, 999)  # unknown types drop to end
                calls.append(
                    Call(
                        call_id=int(row["Call ID"]),
                        location=row["Location"].strip(),
                        call_type=call_type,
                        priority=priority,
                        received_index=idx,
                    )
                )
        # Highest priority first (lowest number), then received order within that priority
        calls.sort(key=lambda c: (c.priority, c.received_index))
        return calls

    def _ensure_log_dir(self) -> None:
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def _append_log_line(self, record: Dict[str, str]) -> None:
        self._ensure_log_dir()
        # name=value pairs separated by commas
        line = ",".join([f"{k}={v}" for k, v in record.items()])
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def run_once(self) -> float:
        """
        Runs the dispatch simulation once.
        Returns: total route-algorithm time in seconds for this run.
        """
        calls = self._load_calls()
        total_route_seconds = 0.0

        for call in calls:
            best: Optional[Tuple[Ambulance, List[str], float]] = None

            for amb in self.ambulances:
                start_t = time.perf_counter()
                route, travel_time = self.router.shortest_path(self.graph, amb.staging_location, call.location)
                end_t = time.perf_counter()

                total_route_seconds += (end_t - start_t)

                if best is None or travel_time < best[2]:
                    best = (amb, route, travel_time)

            assert best is not None
            selected_amb, route, travel_time = best

            dispatch_record = {
                "Call ID": str(call.call_id),
                "Call Type": call.call_type,
                "Call Location": call.location,
                "Selected Ambulance": selected_amb.ambulance_number,
                "Route to Call Location": " -> ".join(route) if route else "NO_ROUTE",
                "Time to the Call Location": f"{travel_time:.2f}",
                "Route Algorithm": self.router.name,
            }

            self._append_log_line(dispatch_record)

            # Requirement: after appending, ambulance location resets to staging and is available.
            # In this simulation, we always compute from staging, so no persistent location update is required.

        print(f"[{self.router.name}] Total time spent finding fastest routes: {total_route_seconds:.6f} seconds")
        return total_route_seconds

    def run_multiple(self, runs: int) -> None:
        times: List[float] = []
        for i in range(1, runs + 1):
            t = self.run_once()
            times.append(t)
            print(f"Run {i}/{runs}: {t:.6f} seconds")

        avg = sum(times) / len(times)
        print(f"\n[{self.router.name}] Average route-algorithm time over {runs} runs: {avg:.6f} seconds")
