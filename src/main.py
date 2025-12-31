import sys
import time
from dataclasses import dataclass

@dataclass(frozen=True)
class Flight:
    origin: str
    dest: str
    day: int
    price: int

class Stats:
    def __init__(self):
        self.backtracks = 0
        self.nodes_visited = 0

def parse_input(lines):
    clean = [ln.strip() for ln in lines if ln.strip()]
    it = iter(clean)

    M = int(next(it))
    min_price, max_price = map(int, next(it).split())
    cities = next(it).split()
    K = len(cities)

    stay_pairs = K - 2
    min_stays, max_stays = [], []
    if stay_pairs > 0:
        stay_tokens = next(it).split()
        for i in range(stay_pairs):
            min_stays.append(int(stay_tokens[2*i]))
            max_stays.append(int(stay_tokens[2*i+1]))

    flights_by_route = {}
    for _ in range(M):
        o, d, day_s, price_s = next(it).split()
        f = Flight(o, d, int(day_s), int(price_s))
        flights_by_route.setdefault((o, d), []).append(f)

    # keep your ordering (day, price)
    for key in flights_by_route:
        flights_by_route[key].sort(key=lambda x: (x.day, x.price))

    return min_price, max_price, cities, min_stays, max_stays, flights_by_route

def build_domains(cities, flights_by_route):
    domains = []
    for i in range(len(cities) - 1):
        domains.append(list(flights_by_route.get((cities[i], cities[i+1]), [])))
    return domains

def time_ok(prev_f, next_f, mn, mx):
    return mn <= (next_f.day - prev_f.day) <= mx

def forward_check(domains, i, assignment, min_stays, max_stays):
    new_domains = [d.copy() for d in domains]
    if i >= len(domains) - 1:
        return new_domains

    cur = assignment[i]
    if cur is None:
        return new_domains

    mn = min_stays[i]
    mx = max_stays[i]

    new_domains[i+1] = [cand for cand in new_domains[i+1] if time_ok(cur, cand, mn, mx)]
    if not new_domains[i+1]:
        return None
    return new_domains

def backtrack(i, domains, assignment, min_stays, max_stays, min_price, max_price, stats, mode, best):
    n = len(domains)
    stats.nodes_visited += 1

    if i == n:
        total = sum(f.price for f in assignment)
        if min_price <= total <= max_price:
            if mode == "first":
                best["assignment"] = assignment.copy()
                best["cost"] = total
                return True
            else:
                if total < best["cost"]:
                    best["assignment"] = assignment.copy()
                    best["cost"] = total
        return False

    for val in domains[i]:
        # local consistency with previous
        if i > 0:
            mn = min_stays[i-1]
            mx = max_stays[i-1]
            if not time_ok(assignment[i-1], val, mn, mx):
                stats.backtracks += 1
                continue

        assignment[i] = val

        # prune by max_price
        partial = sum(f.price for f in assignment[:i+1])
        if partial > max_price:
            assignment[i] = None
            stats.backtracks += 1
            continue

        # branch & bound
        if mode == "cheapest" and best["cost"] < 10**18 and partial >= best["cost"]:
            assignment[i] = None
            stats.backtracks += 1
            continue

        new_domains = forward_check(domains, i, assignment, min_stays, max_stays)
        if new_domains is None:
            assignment[i] = None
            stats.backtracks += 1
            continue

        found = backtrack(i+1, new_domains, assignment, min_stays, max_stays, min_price, max_price, stats, mode, best)
        if mode == "first" and found:
            return True

        assignment[i] = None

    return False

def solve(lines, mode):
    min_price, max_price, cities, min_stays, max_stays, flights_by_route = parse_input(lines)
    domains = build_domains(cities, flights_by_route)

    if any(len(d) == 0 for d in domains):
        return None, Stats(), 0.0

    assignment = [None] * len(domains)
    stats = Stats()
    best = {"assignment": None, "cost": 10**18}

    t0 = time.perf_counter()
    backtrack(0, domains, assignment, min_stays, max_stays, min_price, max_price, stats, mode, best)
    t1 = time.perf_counter()

    return best["assignment"], stats, (t1 - t0)

def main():
    mode = "cheapest"
    if len(sys.argv) >= 2 and sys.argv[1].strip().lower() in ("first", "--first"):
        mode = "first"

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
