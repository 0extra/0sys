from __future__ import annotations

from collections import defaultdict, deque

from zerosys.core.errors import CircularDependencyError, PlannerError
from zerosys.core.planner.task import Task


class DependencyGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, Task] = {}
        self._order: dict[str, int] = {}
        self._forward: dict[str, set[str]] = defaultdict(set)
        self._backward: dict[str, set[str]] = defaultdict(set)
        self._next_order = 0

    def add_task(self, task: Task) -> None:
        if task.id in self._nodes:
            raise PlannerError(f"task with id '{task.id}' already exists")
        self._nodes[task.id] = task
        self._order[task.id] = self._next_order
        self._next_order += 1
        self._forward.setdefault(task.id, set())
        self._backward.setdefault(task.id, set())

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        if task_id not in self._nodes:
            raise PlannerError(f"unknown task id '{task_id}'")
        if depends_on_id not in self._nodes:
            raise PlannerError(f"unknown dependency id '{depends_on_id}'")
        if task_id == depends_on_id:
            raise PlannerError(f"task '{task_id}' cannot depend on itself")
        self._forward[depends_on_id].add(task_id)
        self._backward[task_id].add(depends_on_id)

    def link_declared_dependencies(self) -> None:
        for task in self._nodes.values():
            for dep_id in task.depends_on:
                if dep_id not in self._nodes:
                    raise PlannerError(f"task '{task.id}' depends on unknown task '{dep_id}'")
                self._forward[dep_id].add(task.id)
                self._backward[task.id].add(dep_id)

    def tasks(self) -> list[Task]:
        return list(self._nodes.values())

    def task_by_id(self, task_id: str) -> Task:
        try:
            return self._nodes[task_id]
        except KeyError as exc:
            raise PlannerError(f"unknown task id '{task_id}'") from exc

    def find_by_name(self, name: str) -> Task | None:
        for task in self._nodes.values():
            if task.name == name:
                return task
        return None

    def dependencies_of(self, task_id: str) -> set[str]:
        return set(self._backward.get(task_id, set()))

    def dependents_of(self, task_id: str) -> set[str]:
        return set(self._forward.get(task_id, set()))

    def _ordered(self, ids: set[str] | list[str]) -> list[str]:
        return sorted(ids, key=lambda nid: self._order[nid])

    def roots(self) -> list[Task]:
        ids = [nid for nid, deps in self._backward.items() if not deps]
        return [self._nodes[nid] for nid in self._ordered(ids)]

    def leaves(self) -> list[Task]:
        ids = [nid for nid, deps in self._forward.items() if not deps]
        return [self._nodes[nid] for nid in self._ordered(ids)]

    def topological_order(self) -> list[Task]:
        in_degree = {nid: len(self._backward[nid]) for nid in self._nodes}
        ready = [nid for nid in self._nodes if in_degree[nid] == 0]
        queue: deque[str] = deque(self._ordered(ready))
        ordered: list[Task] = []

        while queue:
            nid = queue.popleft()
            ordered.append(self._nodes[nid])
            newly_ready: list[str] = []
            for dependent in self._forward[nid]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    newly_ready.append(dependent)
            for nid2 in self._ordered(newly_ready):
                queue.append(nid2)

        if len(ordered) != len(self._nodes):
            cycle = self._find_cycle()
            raise CircularDependencyError("circular dependency detected: " + " -> ".join(cycle))

        return ordered

    def levels(self) -> list[list[Task]]:
        in_degree = {nid: len(self._backward[nid]) for nid in self._nodes}
        current = self._ordered([nid for nid in self._nodes if in_degree[nid] == 0])
        result: list[list[Task]] = []

        while current:
            result.append([self._nodes[nid] for nid in current])
            next_level: list[str] = []
            for nid in current:
                for dependent in self._forward[nid]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_level.append(dependent)
            current = self._ordered(next_level)

        if sum(len(level) for level in result) != len(self._nodes):
            cycle = self._find_cycle()
            raise CircularDependencyError("circular dependency detected: " + " -> ".join(cycle))

        return result

    def _find_cycle(self) -> list[str]:
        visited: set[str] = set()
        stack: list[str] = []
        on_stack: set[str] = set()

        def dfs(node: str) -> list[str] | None:
            visited.add(node)
            stack.append(node)
            on_stack.add(node)
            for neighbor in self._ordered(list(self._forward[node])):
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in on_stack:
                    idx = stack.index(neighbor)
                    return [*stack[idx:], neighbor]
            stack.pop()
            on_stack.discard(node)
            return None

        for nid in self._ordered(list(self._nodes)):
            if nid not in visited:
                cycle = dfs(nid)
                if cycle:
                    return cycle
        return []

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, task_id: object) -> bool:
        return task_id in self._nodes
