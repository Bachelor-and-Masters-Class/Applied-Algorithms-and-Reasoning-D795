import heapq
from typing import Dict, List, Tuple, Optional


class DijkstraRouter:
    name = "Dijkstra"

    def shortest_path(
        self,
        graph: Dict[str, List[Tuple[str, float]]],
        start: str,
        goal: str
    ) -> Tuple[List[str], float]:
        if start not in graph or goal not in graph:
            return [], float("inf")

        dist: Dict[str, float] = {start: 0.0}
        prev: Dict[str, Optional[str]] = {start: None}
        pq: List[Tuple[float, str]] = [(0.0, start)]

        visited = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            if u == goal:
                break

            for v, w in graph.get(u, []):
                nd = d + w
                if v not in dist or nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        if goal not in dist:
            return [], float("inf")

        # rebuild path
        path: List[str] = []
        cur: Optional[str] = goal
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()
        return path, dist[goal]
