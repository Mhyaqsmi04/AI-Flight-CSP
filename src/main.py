import sys
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

@dataclass(frozen=True)
class Flight:
    origin: str
    dest: str
    day: int
    price: int

@dataclass
class Stats:
    backtracks: int = 0
    nodes_visited: int = 0

def parse_input(lines: List[str]):
    """
    Input:
    1) M
    2) MinPrice MaxPrice
    3) city sequence: C0 C1 ... C(K-1)
    4) stay windows: (min max) pairs for each intermediate stop => count = K-2
    5) M lines: Origin Dest Day Price
    """
    clean = [ln.strip() for ln in lines if ln.strip() != ""]
    it = iter(clean)

    M = int(next(it))
    min_price, max_price = map(int, next(it).split())
    cities = next(it).split()
    K = len(cities)

    stay_pairs = max(0, K - 2)
    min_stays: List[int] = []
    max_stays: List[int] = []

    if stay_pairs > 0:
        stay_tokens = next(it).split()
        if len(stay_tokens) != 2 * stay_pairs:
            raise ValueError("Stay windows line has wrong number of integers.")
        for i in range(stay_pairs):
            mn = int(stay_tokens[2 * i])
            mx = int(stay_tokens[2 * i + 1])
            min_stays.append(mn)
            max_stays.append(mx)

    flights_by_route: Dict[Tuple[str, str], List[Flight]] = {}
    for _ in range(M):
        o, d, day_s, price_s = next(it).split()
        f = Flight(o, d, int(day_s), int(price_s))
        flights_by_route.setdefault((o, d), []).append(f)

    # Sort domains to try cheaper flights first (helps "cheapest" mode)
    for key in flights_by_route:
        flights_by_route[key].sort(key=lambda x: (x.day, x.price))

    return min_price, max_price, cities, min_stays, max_stays, flights_by_route

def build_domains(cities: List[str],
                  flights_by_route: Dict[Tuple[str, str], List[Flight]]) -> List[List[Flight]]:
    domains: List[List[Flight]] = []
    for i in range(len(cities) - 1):
        route = (cities[i], cities[i + 1])
        domains.append(list(flights_by_route.get(route, [])))
    return domains

def time_window_ok(prev_f: Flight, next_f: Flight, mn: int, mx: int) -> bool:
    diff = next_f.day - prev_f.day
    return mn <= diff <= mx

def forward_check(domains: List[List[Flight]],
                  assigned_index: int,
                  assignment: List[Optional[Flight]],
                  min_stays: List[int],
                  max_stays: List[int]) -> Optional[List[List[Flight]]]:
    """
    Forward Checking (1-step):
    After assigning X[i], filter domain of X[i+1] based on time window constraint.
    Budget constraint is NOT applied here (as required).
    """
    new_domains = [d.copy() for d in domains]
    i = assigned_index

    if i >= len(new_domains) - 1:
        return new_domains

    cur = assignment[i]
    if cur is None:
        return new_domains

    # Between flight i and i+1 uses stay index i
    mn = min_stays[i]
    mx = max_stays[i]

    filtered = [cand for cand in new_domains[i + 1] if time_window_ok(cur, cand, mn, mx)]
    new_domains[i + 1] = filtered

    if not filtered:
        return None
    return new_domains

def backtrack(i: int,
              domains: List[List[Flight]],
              assignment: List[Optional[Flight]],
              min_stays: List[int],
              max_stays: List[int],
              min_price: int,
              max_price: int,
              stats: Stats,
              mode: str,
              best: Dict[str, object]) -> bool:
    """
    mode:
      - "cheapest": find minimum-cost valid solution (branch & bound)
      - "first": return the first valid solution encountered
    Returns True only in "first" mode when a solution is found (to stop recursion).
    """
    N = len(domains)
    stats.nodes_visited += 1

    if i == N:
        total = sum(f.price for f in assignment if f is not None)
        if min_price <= total <= max_price:
            if mode == "first":
                best["cost"] = total
                best["assignment"] = assignment.copy()
                return True
            else:
                if total < best["cost"]:
                    best["cost"] = total
                    best["assignment"] = assignment.copy()
        return False

    if not domains[i]:
        stats.backtracks += 1
        return False

    for val in domains[i]:
        assignment[i] = val

        # Safe pruning using MaxPrice (not Forward Checking)
        partial_cost = sum(f.price for f in assignment[:i+1] if f is not None)
        if partial_cost > max_price:
            assignment[i] = None
            stats.backtracks += 1
            continue

        # Branch & bound (only meaningful in cheapest mode once we have a solution)
        if mode == "cheapest" and best["cost"] < 10**18 and partial_cost >= best["cost"]:
            assignment[i] = None
            stats.backtracks += 1
            continue

        # Consistency with previous flight (time window)
        if i > 0:
            prev = assignment[i - 1]
            mn = min_stays[i - 1]
            mx = max_stays[i - 1]
            if prev is None or not time_window_ok(prev, val, mn, mx):
                assignment[i] = None
                stats.backtracks += 1
                continue

        # Forward checking (do NOT apply budget here)
        new_domains = forward_check(domains, i, assignment, min_stays, max_stays)
        if new_domains is None:
            assignment[i] = None
            stats.backtracks += 1
            continue

        found = backtrack(i + 1, new_domains, assignment, min_stays, max_stays,
                          min_price, max_price, stats, mode, best)

        if mode == "first" and found:
            return True

        assignment[i] = None

    return False

def solve(lines: List[str], mode: str):
    min_price, max_price, cities, min_stays, max_stays, flights_by_route = parse_input(lines)
    domains = build_domains(cities, flights_by_route)

    # quick fail if any domain empty
    if any(len(d) == 0 for d in domains):
        return None, Stats(), 0.0

    assignment: List[Optional[Flight]] = [None] * len(domains)
    stats = Stats()
    best = {"cost": 10**18, "assignment": None}

    t0 = time.perf_counter()
    backtrack(0, domains, assignment, min_stays, max_stays,
              min_price, max_price, stats, mode, best)
    t1 = time.perf_counter()

    return best["assignment"], stats, (t1 - t0)

def main():
    # Mode selection:
    # default: cheapest
    # optional: first
    mode = "cheapest"
    if len(sys.argv) >= 2:
        arg = sys.argv[1].strip().lower()
        if arg in ("first", "--first"):
            mode = "first"
        elif arg in ("cheapest", "--cheapest"):
            mode = "cheapest"

    lines = sys.stdin.read().splitlines()
    solution, stats, runtime = solve(lines, mode)

    if solution is None:
        print("No Solution")
    else:
        total = 0
        for f in solution:
            print(f"{f.origin} {f.dest} {f.day} {f.price}")
            total += f.price
        print(f"Total Cost: {total}")

    print(f"Backtracks: {stats.backtracks}")
    print(f"Runtime: {runtime:.6f} seconds")

if __name__ == "__main__":
    main()
# CSP Flight Planning Project
