#!/usr/bin/env python3
"""Planning-only stage search, successful-prefix memory and expansion cap.
Same ordered requests, candidate order, current-world predicate and start state.
A node expansion means ONE candidate-prefix predicate evaluation; revalidation
is charged identically and included in total. Counts only, NOT wall-clock time.
Cache stores only an actually accepted first-three-stage prefix from the PAST,
with its root context; never future worlds, task outcomes or a solution oracle.
A stale prefix FAILS validation after a world change, is discarded and replanned.
No robot execution/reset trick: these are planning requests from the same root.
This cache policy is our sketch, not a claim of automatic MTC cache support.
Real Panda/SO-101/MoveIt planning 本页未运行.
"""
from dataclasses import dataclass

STAGES = ("connect", "grasp", "ik", "place", "retreat")
PREFIX_LEN, CAP = 3, 8
ARMS = ("full_replan", "cached_prefix", "bounded_8")


@dataclass(frozen=True)
class Request:
    name: str
    routes: tuple
    slot: object  # None: both place alternatives blocked.
    context: str = "same_start_object"


STREAM = (
    Request("warmup", (0,1), 0),
    Request("repeat", (0,1), 0),
    Request("place_blocked", (0,1), None),
    Request("recover_new_slot", (0,1), 1),
    Request("world_change", (1,), 1),
    Request("repeat_B", (1,), 0),
    Request("both_routes_blocked", (), 0),
    Request("restored_B", (1,), 0),
)


def feasible(prefix, request):
    """Current-world query, same access for all arms; no stream look-ahead."""
    stage, choice = len(prefix)-1, prefix[-1]
    if stage == 0:
        return choice in request.routes
    if stage == 1:
        return True  # IK feasibility is not known until the next stage is expanded.
    if stage == 2:
        return prefix[1] == 1 and choice == 0
    if stage == 3:
        return request.slot is not None and choice == request.slot
    return choice == 0


class Search:
    def __init__(self, request, cap=None):
        self.request, self.cap = request, cap
        self.search_nodes = self.revalidation_nodes = 0
        self.best_prefix, self.last_failure = (), "none"

    def check(self, path, revalidate=False):
        if self.cap is not None and self.search_nodes+self.revalidation_nodes >= self.cap:
            raise OverflowError("expansion_budget")
        if revalidate:
            self.revalidation_nodes += 1
        else:
            self.search_nodes += 1
        valid = feasible(path,self.request)
        if valid and min(PREFIX_LEN,len(path)) > len(self.best_prefix):
            self.best_prefix = path[:PREFIX_LEN]
        if not valid:
            self.last_failure = STAGES[len(path)-1]
        return valid

    def dfs(self, prefix):
        if len(prefix) == len(STAGES):
            return prefix
        for candidate in (0,1):
            path = prefix+(candidate,)
            if self.check(path):
                result = self.dfs(path)
                if result is not None:
                    return result
        return None


def run(arm, stream=STREAM):
    cache, cache_context = (), None
    rows = []
    for req in stream:  # Only the current request is passed to Search.
        search = Search(req,CAP if arm=="bounded_8" else None)
        prefix, stale = (), False
        if arm=="cached_prefix" and cache and cache_context==req.context:
            for end in range(1,len(cache)+1):
                if not search.check(cache[:end],revalidate=True):
                    stale = True  # Cached candidate really failed the current predicate.
                    search.best_prefix = ()  # Drop all dependent cached results.
                    break
            else:
                prefix = cache
        try:
            solution = search.dfs(prefix)
            if solution is None and prefix:
                solution = search.dfs(())  # Charge exhaustive root fallback, not a free global no-solution oracle.
            status = "success" if solution is not None else "no_solution"
        except OverflowError:
            solution, status = None, "budget_exhausted"
        if arm=="cached_prefix":
            cache = solution[:PREFIX_LEN] if solution else search.best_prefix
            cache_context = req.context
        total = search.search_nodes+search.revalidation_nodes
        if arm=="bounded_8":
            assert total <= CAP
        rows.append((req.name,status,search.search_nodes,search.revalidation_nodes,total,
                     int(stale),search.last_failure,solution))
    return rows


def main():
    print("shared stream=8 planning requests; stages=connect/grasp/ik/place/retreat candidates=0,1; prefix=3 budget=8")
    print("one expansion=one current-world prefix predicate check; total=search+revalidation; counts only, NOT wall-clock")
    print("request arm result search_nodes revalidation_nodes total_nodes stale_prefix_failed last_rejected_stage solution")
    summaries = []
    for arm in ARMS:
        rows = run(arm)
        for name,status,n,v,total,stale,reason,solution in rows:
            path = "-" if solution is None else "".join(map(str,solution))
            print(f"{name} {arm} {status} {n} {v} {total} {stale} {reason} {path}")
        summaries.append((arm,rows))
    print("arm successes/8 search_nodes revalidation_nodes total_nodes stale_prefix_failures budget_exhaustions")
    for arm,rows in summaries:
        print(f"{arm} {sum(r[1]=='success' for r in rows)}/8 {sum(r[2] for r in rows)} "
              f"{sum(r[3] for r in rows)} {sum(r[4] for r in rows)} {sum(r[5] for r in rows)} "
              f"{sum(r[1]=='budget_exhausted' for r in rows)}")
    changed = next(r for r in run("cached_prefix") if r[0]=="world_change")
    assert changed[5] == 1 and changed[3] > 0
    print("world_change: cached route0 FAILS revalidation; discard dependents, then repair via route1 (not an unsafe execution)")
    print("cache contains past accepted prefixes only; bounded exhaustion is not proof of infeasibility; no universal winner")
    print("new toy counts are not old stage_graph_toy mock seconds; real MoveIt/Panda/SO-101 本页未运行")


if __name__ == "__main__":
    main()
