import csv
import os
import heapq
from pprint import pprint
from time import perf_counter


# -------- Load Ambulances --------
def load_ambulances(path):
    ambulances = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ambulances.append({
                "ambulance_number": row["Ambulance Number"],
                "staging_location": row["Staging Location"]
            })
    return ambulances


# -------- Load Call Priorities --------
def load_call_priorities(path):
    priorities = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            priorities[row["Call Type"]] = int(row["Priority"])
    return priorities


# -------- Load Calls --------
def load_calls(path, priority_map):
    calls = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            calls.append({
                "call_id": int(row["Call ID"]),
                "location": row["Location"],
                "call_type": row["Call Type"],
                "priority": priority_map[row["Call Type"]],
                "order": idx
            })
    return calls


# -------- Load Location Network --------
def load_location_network(path):
    graph = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start = row["Start"]
            end = row["End"]
            weight = float(row["Travel Time"]) + float(row["Traffic Delay"])

            if start not in graph:
                graph[start] = []
            graph[start].append((end, weight))

            # ensure the end node exists in graph even if it has no outgoing edges
            if end not in graph:
                graph[end] = []

    return graph


def sort_calls(calls):
    # Priority: lower number = higher priority (1 first)
    # Then preserve received order within the same priority
    return sorted(calls, key=lambda c: (c["priority"], c["order"]))


class RouteTimer:
    def __init__(self):
        self.total_seconds = 0.0

    def time_call(self, fn, *args, **kwargs):
        start = perf_counter()
        result = fn(*args, **kwargs)
        end = perf_counter()
        self.total_seconds += (end - start)
        return result


def dijkstra_shortest_path(graph, start, goal):
    """
    Returns (best_time, route_list). best_time is float('inf') if unreachable.
    graph format: {node: [(neighbor, weight), ...]}
    """
    if start not in graph or goal not in graph:
        return float("inf"), []

    dist = {start: 0.0}
    prev = {start: None}
    heap = [(0.0, start)]
    visited = set()

    while heap:
        cur_dist, node = heapq.heappop(heap)

        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            break

        for nbr, w in graph.get(node, []):
            if nbr in visited:
                continue
            nd = cur_dist + w
            if nd < dist.get(nbr, float("inf")):
                dist[nbr] = nd
                prev[nbr] = node
                heapq.heappush(heap, (nd, nbr))

    if goal not in dist:
        return float("inf"), []

    # Reconstruct path
    route = []
    cur = goal
    while cur is not None:
        route.append(cur)
        cur = prev.get(cur)
    route.reverse()

    return dist[goal], route


def select_best_ambulance_for_call(graph, ambulances, call_location, timer):
    best_time = float("inf")
    best_route = []
    best_ambulance_number = None
    best_ambulance_start = None

    for amb in ambulances:
        start = amb["staging_location"]
        t, route = timer.time_call(dijkstra_shortest_path, graph, start, call_location)

        if t < best_time:
            best_time = t
            best_route = route
            best_ambulance_number = amb["ambulance_number"]
            best_ambulance_start = start

    return {
        "selected_ambulance": best_ambulance_number,
        "ambulance_start": best_ambulance_start,
        "time_to_call": best_time,
        "route": best_route
    }


def build_dispatch_record(call, selection_result):
    return {
        "Call ID": call["call_id"],
        "Call Type": call["call_type"],
        "Call Location": call["location"],
        "Selected Ambulance": selection_result["selected_ambulance"],
        "Route to Call Location": selection_result["route"],
        "Time to the Call Location": selection_result["time_to_call"]
    }


def append_dispatch_log(record, log_path="/var/log/ambulance_call_log.csv"):
    # Windows/local dev fallback: if /var/log path doesn't exist, write to project folder instead
    if log_path.startswith("/var/") and not os.path.exists("/var"):
        log_path = "ambulance_call_log.csv"  # local fallback (same format, same content)

    line = ",".join([
        f"Call ID={record['Call ID']}",
        f"Call Type={record['Call Type']}",
        f"Call Location={record['Call Location']}",
        f"Selected Ambulance={record['Selected Ambulance']}",
        f"Route to Call Location={' > '.join(record['Route to Call Location'])}",
        f"Time to the Call Location={record['Time to the Call Location']:.2f}",
    ])

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    ambulances = load_ambulances("ambulance.csv")
    priorities = load_call_priorities("call_priority.csv")
    calls = load_calls("calls.csv", priorities)
    sorted_calls = sort_calls(calls)
    graph = load_location_network("location_network.csv")
    timer = RouteTimer()
    print("\nRouteTimer ready. total_seconds =", timer.total_seconds)

    # Quick Dijkstra sanity test using first ambulance and first sorted call
    first_amb = ambulances[0]["staging_location"]
    first_call_loc = sorted_calls[0]["location"]

    best_time, route = timer.time_call(dijkstra_shortest_path, graph, first_amb, first_call_loc)

    print("\nDijkstra sanity test:")
    print("Start:", first_amb)
    print("Goal :", first_call_loc)
    print("Time :", best_time)
    print("Route:", route[:10], "..." if len(route) > 10 else "")
    print("Timer total_seconds:", timer.total_seconds)

    print("\nDispatch record + log append (all calls):")
    count = 0
    for call in sorted_calls:
        selection = select_best_ambulance_for_call(graph, ambulances, call["location"], timer)
        record = build_dispatch_record(call, selection)

        append_dispatch_log(record)
        count += 1

    print(f"\nDone. Logged {count} calls.")
    print("Timer total_seconds (route algorithm only):", timer.total_seconds)
    print("ROUTE_SECONDS_TOTAL:", timer.total_seconds)

    print("Ambulances (first 2):")
    pprint(ambulances[:2])

    print("\nCalls (first 2):")
    pprint(calls[:2])

    print("\nGraph sample (first 1 start node):")
    first_node = next(iter(graph))
    print(first_node, "->", graph[first_node][:3])

    print("\nFirst 5 sorted calls (call_id, priority, order):")
    for c in sorted_calls[:5]:
        print(c["call_id"], c["priority"], c["order"])
