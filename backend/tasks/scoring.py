from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Optional, Set
import math

def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None

def days_until(d: Optional[date]) -> Optional[int]:
    if d is None:
        return None
    today = date.today()
    return (d - today).days

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def detect_cycle(tasks: List[Dict[str, Any]]) -> List[List[str]]:
    id_map = {}
    for t in tasks:
        tid = t.get("id") or t.get("title")
        id_map[tid] = t

    visited = {}
    cycles = []

    def dfs(node, stack):
        visited[node] = 1
        stack.append(node)
        for dep in id_map.get(node, {}).get("dependencies", []):
            dep_node = dep
            if dep_node not in id_map:
                continue
            if visited.get(dep_node) == 1:
                idx = stack.index(dep_node)
                cycles.append(stack[idx:] + [dep_node])
            elif visited.get(dep_node) is None:
                dfs(dep_node, stack)
        stack.pop()
        visited[node] = 2

    for node in list(id_map.keys()):
        if visited.get(node) is None:
            dfs(node, [])

    return cycles

def simple_score(task: Dict[str, Any]) -> float:
    importance = clamp(int(task.get("importance", 5)), 1, 10)
    est = float(task.get("estimated_hours", 1.0)) if task.get("estimated_hours") is not None else 1.0
    due_date = parse_date(task.get("due_date"))
    deps = task.get("dependencies") or []

    imp = importance * 8
    du = days_until(due_date)
    if du is None:
        due_weight = 5
    else:
        if du < 0:
            due_weight = 60 + (max(-30, du))
        else:
            due_weight = max(0, 30 - du)

    effort_penalty = est * 2
    dep_bonus = len(deps) * 6
    raw = imp + due_weight - effort_penalty + dep_bonus
    score = clamp(raw, 0, 100)
    return round(score, 2)

def smart_balance_score(task: Dict[str, Any], tasks_index: Dict[str, Dict[str,Any]], weights: Dict[str,float]=None) -> Tuple[float, Dict[str,float]]:
    if weights is None:
        weights = {
            "urgency": 0.30,
            "importance": 0.30,
            "effort": 0.20,
            "dependency": 0.15,
            "blocking": 0.05
        }

    importance = clamp(int(task.get("importance", 5)), 1, 10)
    est = float(task.get("estimated_hours", 1.0)) if task.get("estimated_hours") is not None else 1.0
    due_date = parse_date(task.get("due_date"))
    deps = task.get("dependencies") or []
    tid = task.get("id") or task.get("title")

    du = days_until(due_date)
    if du is None:
        urgency_raw = 30
    else:
        if du < 0:
            urgency_raw = 100
        else:
            urgency_raw = clamp(100 * math.exp(-du / 7.0), 0, 100)

    urgency_score = (urgency_raw / 100) * 30
    importance_score = ((importance - 1) / 9.0) * 30
    effort_raw = 1.0 / (est + 0.1)
    effort_score = clamp((effort_raw / 1.0) * 20, 0, 20)

    blocking_count = 0
    for other in tasks_index.values():
        if (task.get("id") or task.get("title")) in (other.get("dependencies") or []):
            blocking_count += 1
    dependency_score = clamp(min(len(deps) * 5, 15), 0, 15)
    blocking_score = clamp(min(blocking_count * 5, 5), 0, 5)

    components = {
        "urgency": urgency_score,
        "importance": importance_score,
        "effort": effort_score,
        "dependency": dependency_score,
        "blocking": blocking_score
    }

    comp_norm = {
        "urgency": components["urgency"] / 30.0,
        "importance": components["importance"] / 30.0,
        "effort": components["effort"] / 20.0,
        "dependency": components["dependency"] / 15.0,
        "blocking": components["blocking"] / 5.0
    }

    final_score = (
        comp_norm["urgency"] * weights["urgency"] +
        comp_norm["importance"] * weights["importance"] +
        comp_norm["effort"] * weights["effort"] +
        comp_norm["dependency"] * weights["dependency"] +
        comp_norm["blocking"] * weights["blocking"]
    ) * 100.0

    breakdown = {k: round(v, 3) for k,v in comp_norm.items()}
    return round(final_score, 2), breakdown
