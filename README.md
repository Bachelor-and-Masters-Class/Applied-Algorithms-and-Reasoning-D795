# Ambulance Dispatch

**WGU D795 · Applied Algorithms and Reasoning**

Decides which ambulance answers each 911 call and the fastest way to get there. The most urgent calls go first.

## How it works

- **The city is a map of roads.** Each road's cost is travel time plus traffic delay, not just distance.
- **Fastest route:** Dijkstra's algorithm finds the quickest path from an ambulance to a call. It always finds the true best route, which matters when lives are on the line. If a place can't be reached, it says so instead of crashing.
- **Who goes first:** calls are sorted by priority. Calls with the same priority keep their arrival order, so no one gets skipped.
- **Which ambulance:** for each call, it checks every ambulance's travel time and sends the fastest one.
- **Timing:** a timer measures only the routing algorithm, not file loading, so the speed number is honest.
- **Log:** every decision is saved with the call, the ambulance, the route and the arrival time.

## Speed

| Step | Cost |
|---|---|
| One route lookup | O((V + E) log V) |
| Picking an ambulance | O(A × (V + E) log V) per call |
| Sorting calls | O(n log n) |
| Memory | O(V + E) |

V = locations, E = roads, A = ambulances, n = calls

## Run it

```
python main.py
```

Needs `ambulance.csv`, `calls.csv`, `call_priority.csv` and `location_network.csv` in the same folder.

## Files

- `main.py`: loads data, runs dispatch, reports timing
- `dispatcher.py`: picks the ambulance
- `router.py`: Dijkstra's algorithm
- `*.csv`: ambulances, calls, priorities and road network
- `D795_PT1/`, `D795_PT2/`: the two graded task submissions

**Built with:** Python
