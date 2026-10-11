from __future__ import annotations

import pytest

from zerosys.core.errors import CircularDependencyError, PlannerError
from zerosys.core.planner.dag import DependencyGraph
from zerosys.core.planner.task import Task, TaskKind

pytestmark = pytest.mark.unit


def _task(name: str) -> Task:
    return Task(kind=TaskKind.COMMAND, name=name)


def test_empty_graph_has_no_tasks() -> None:
    graph = DependencyGraph()

    assert len(graph) == 0
    assert graph.tasks() == []
    assert graph.topological_order() == []


def test_single_task_topological_order() -> None:
    graph = DependencyGraph()
    task = _task("solo")
    graph.add_task(task)

    assert graph.topological_order() == [task]


def test_duplicate_task_id_raises() -> None:
    graph = DependencyGraph()
    task = _task("a")
    graph.add_task(task)

    with pytest.raises(PlannerError, match="already exists"):
        graph.add_task(task)


def test_add_dependency_unknown_id_raises() -> None:
    graph = DependencyGraph()
    task = _task("a")
    graph.add_task(task)

    with pytest.raises(PlannerError, match="unknown dependency"):
        graph.add_dependency(task.id, "missing")


def test_add_dependency_unknown_task_id_raises() -> None:
    graph = DependencyGraph()
    other = _task("b")
    graph.add_task(other)

    with pytest.raises(PlannerError, match="unknown task"):
        graph.add_dependency("missing", other.id)


def test_self_dependency_raises() -> None:
    graph = DependencyGraph()
    task = _task("a")
    graph.add_task(task)

    with pytest.raises(PlannerError, match="cannot depend on itself"):
        graph.add_dependency(task.id, task.id)


def test_declared_dependencies_are_linked() -> None:
    graph = DependencyGraph()
    a = _task("a")
    b = Task(kind=TaskKind.COMMAND, name="b", depends_on=[a.id])
    graph.add_task(a)
    graph.add_task(b)

    graph.link_declared_dependencies()

    assert graph.dependencies_of(b.id) == {a.id}
    assert graph.dependents_of(a.id) == {b.id}


def test_link_declared_unknown_dependency_raises() -> None:
    graph = DependencyGraph()
    b = Task(kind=TaskKind.COMMAND, name="b", depends_on=["missing"])
    graph.add_task(b)

    with pytest.raises(PlannerError, match="unknown task"):
        graph.link_declared_dependencies()


def test_topological_order_chain() -> None:
    graph = DependencyGraph()
    a = _task("a")
    b = _task("b")
    c = _task("c")
    graph.add_task(a)
    graph.add_task(b)
    graph.add_task(c)
    graph.add_dependency(b.id, a.id)
    graph.add_dependency(c.id, b.id)

    ordered = graph.topological_order()

    assert ordered == [a, b, c]


def test_topological_order_is_deterministic_across_runs() -> None:
    graph = DependencyGraph()
    a = _task("a")
    b = _task("b")
    c = _task("c")
    d = _task("d")
    for task in (a, b, c, d):
        graph.add_task(task)
    graph.add_dependency(c.id, a.id)
    graph.add_dependency(d.id, b.id)

    first = [task.name for task in graph.topological_order()]
    second = [task.name for task in graph.topological_order()]

    assert first == second
    assert first == ["a", "b", "c", "d"]


def test_topological_order_cycle_raises() -> None:
    graph = DependencyGraph()
    a = _task("a")
    b = _task("b")
    graph.add_task(a)
    graph.add_task(b)
    graph.add_dependency(b.id, a.id)
    graph.add_dependency(a.id, b.id)

    with pytest.raises(CircularDependencyError):
        graph.topological_order()


def test_levels_group_independent_tasks() -> None:
    graph = DependencyGraph()
    a = _task("a")
    b = _task("b")
    c = _task("c")
    graph.add_task(a)
    graph.add_task(b)
    graph.add_task(c)
    graph.add_dependency(c.id, a.id)
    graph.add_dependency(c.id, b.id)

    levels = graph.levels()

    assert [[task.name for task in level] for level in levels] == [
        ["a", "b"],
        ["c"],
    ]


def test_roots_and_leaves() -> None:
    graph = DependencyGraph()
    a = _task("a")
    b = _task("b")
    c = _task("c")
    graph.add_task(a)
    graph.add_task(b)
    graph.add_task(c)
    graph.add_dependency(b.id, a.id)
    graph.add_dependency(c.id, b.id)

    assert [t.name for t in graph.roots()] == ["a"]
    assert [t.name for t in graph.leaves()] == ["c"]


def test_find_by_name() -> None:
    graph = DependencyGraph()
    a = _task("alpha")
    graph.add_task(a)

    assert graph.find_by_name("alpha") is a
    assert graph.find_by_name("missing") is None


def test_contains_by_id() -> None:
    graph = DependencyGraph()
    a = _task("a")
    graph.add_task(a)

    assert a.id in graph
    assert "nonexistent" not in graph


def test_task_by_id_returns_task() -> None:
    graph = DependencyGraph()
    a = _task("a")
    graph.add_task(a)

    assert graph.task_by_id(a.id) is a


def test_task_by_id_unknown_raises() -> None:
    graph = DependencyGraph()

    with pytest.raises(PlannerError):
        graph.task_by_id("missing")
