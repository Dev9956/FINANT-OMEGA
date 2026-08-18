"""FININT OMEGA — Knowledge graph for financial entities and relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    COMPANY = "company"
    PERSON = "person"
    SECTOR = "sector"
    INDUSTRY = "industry"
    EVENT = "event"
    CONCEPT = "concept"


class EdgeType(str, Enum):
    WORKS_AT = "works_at"
    BELONGS_TO = "belongs_to"
    SUPPLIES = "supplies"
    COMPETES_WITH = "competes_with"
    ACQUIRED = "acquired"
    INVESTED_IN = "invested_in"
    MENTIONS = "mentions"


@dataclass
class Node:
    node_id: str
    label: str
    node_type: NodeType = NodeType.CONCEPT
    properties: dict = field(default_factory=dict)


@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.MENTIONS
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


class KnowledgeGraph:
    """In-memory knowledge graph for financial entities and relationships."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    def add_node(self, node_id: str, label: str, node_type: NodeType = NodeType.CONCEPT, **properties) -> Node:
        node = Node(node_id=node_id, label=label, node_type=node_type, properties=properties)
        self._nodes[node_id] = node
        return node

    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False
        del self._nodes[node_id]
        self._edges = [e for e in self._edges if e.source_id != node_id and e.target_id != node_id]
        return True

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType = EdgeType.MENTIONS, weight: float = 1.0, **properties) -> Edge:
        edge = Edge(source_id=source_id, target_id=target_id, edge_type=edge_type, weight=weight, properties=properties)
        self._edges.append(edge)
        return edge

    def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[Node]:
        neighbor_ids: set[str] = set()
        for e in self._edges:
            if e.source_id == node_id:
                if edge_type is None or e.edge_type == edge_type:
                    neighbor_ids.add(e.target_id)
            elif e.target_id == node_id:
                if edge_type is None or e.edge_type == edge_type:
                    neighbor_ids.add(e.source_id)
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def search(self, query: str, node_type: NodeType | None = None) -> list[Node]:
        q = query.lower()
        results = []
        for node in self._nodes.values():
            if q in node.label.lower():
                if node_type is None or node.node_type == node_type:
                    results.append(node)
        return results

    def get_edges_for_node(self, node_id: str) -> list[Edge]:
        return [e for e in self._edges if e.source_id == node_id or e.target_id == node_id]

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def shortest_path(self, start_id: str, end_id: str, max_depth: int = 5) -> list[str] | None:
        if start_id == end_id:
            return [start_id]
        from collections import deque
        visited: set[str] = {start_id}
        queue: deque[tuple[str, list[str]]] = deque([(start_id, [start_id])])
        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for edge in self.get_edges_for_node(current):
                next_id = edge.target_id if edge.source_id == current else edge.source_id
                if next_id == end_id:
                    return path + [next_id]
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))
        return None
