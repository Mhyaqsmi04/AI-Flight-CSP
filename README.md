# AI-Flight-CSP

This project models flight tour planning as a **Constraint Satisfaction Problem (CSP)** and solves it using **Backtracking Search** with **Forward Checking**.

## Problem Definition
Given:
- A sequence of cities to visit (including return to origin)
- Stay-time windows between consecutive flights
- A budget window (MinPrice, MaxPrice)
- A database of flights in the form: `Origin Dest Day Price`

We must select one flight for each consecutive route so that:
- Time window constraints are satisfied
- Travel order is chronological
- Total cost is within the budget window

## CSP Formulation
- **Variables:** \(X_0 ... X_{N-1}\) where \(X_i\) is the selected flight from City[i] to City[i+1]
- **Domain:** all available flights for each required route (may include multiple days and prices)
- **Constraints:**
  - **Time Window:** `min_stay_i <= day(i+1) - day(i) <= max_stay_i`
  - **Chronological Order:** enforced by the time window constraint
  - **Budget Window:** `MinPrice <= TotalCost <= MaxPrice`
    - (Budget is **not applied** in Forward Checking as required)

## Algorithm
- **Backtracking Search** assigns flights sequentially.
- After each assignment, **Forward Checking** filters the domain of the next variable by removing flights that violate the time window constraint.
- Two modes are supported:
  - **cheapest (default):** returns the minimum-cost valid solution
  - **first:** returns the first valid solution in chronological order (matches sample outputs)

## How to Run (Windows PowerShell)

### Cheapest mode (default)
```powershell
Get-Content .\samples\sample1.txt | python .\src\main.py
Get-Content .\samples\sample2.txt | python .\src\main.py
