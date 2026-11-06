from typing import Dict, List, Tuple, Optional


class BellmanFordRouter:
    name = "Bellman-Ford"

    def shortest_path(
        self,
        graph: Dict[str, List[Tuple[str, float]]],
        start: str,
        goal: str
    ) -> Tuple[List[str], float]:
        if start not in graph or goal not in graph:
            return [], float("inf")

        # Convert adjacency list to edge list
        vertices = list(graph.keys())
        edges: List[Tuple[str, str, float]] = []
        for u, neighbors in graph.items():
            for v, w in neighbors:
                edges.append((u, v, w))

        dist: Dict[str, float] = {v: float("inf") for v in vertices}
        prev: Dict[str, Optional[str]] = {v: None for v in vertices}
        dist[start] = 0.0

        # Relax edges |V|-1 times
        for _ in range(len(vertices) - 1):
            updated = False
            for u, v, w in edges:
                if dist[u] != float("inf") and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    prev[v] = u
                    updated = True
            if not updated:
                break  # early stop improvement

        if dist[goal] == float("inf"):
            return [], float("inf")

        # Rebuild path
        path: List[str] = []
        cur: Optional[str] = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path, dist[goal]
