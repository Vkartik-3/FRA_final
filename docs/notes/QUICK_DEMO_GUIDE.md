# Quick Demo Guide - For Professor Meeting

**What to do:** Follow these steps to demonstrate the verification system

---

## Step 1: Run the Dashboard

```bash
cd fra_pipeline
streamlit run scripts/dashboard_fra.py
```

Wait for it to load. You'll see the dashboard open in your browser.

---

## Step 2: Show Initial Verification

Point to the **green checkmark** at the top:

✅ **Data Verification Passed - Plan 347 loaded successfully**

**What to say:**
> "When the dashboard loads, it automatically runs 5 verification checks - all precincts assigned, exactly 3 super-districts, total seats = 14, Dem + Rep seats = 14, and vote totals preserved. If any check fails, the dashboard stops with an error."

---

## Step 3: Show the "Re-Verify Now" Button

Scroll down slightly - you'll see a section titled:

**🔄 Real-Time Verification**

With a blue button: **🔄 Re-Run All Verification Checks Now**

**What to say:**
> "This button runs the ACTUAL verification algorithms in real-time - the same BFS contiguity checks, geometry validation, and vote conservation checks that run during plan generation."

---

## Step 4: Click the Button (THE DEMO)

**Click the button** - Professor will see:

1. **Loading message appears:**
   ```
   ⏳ Running real-time verification (this may take 10-30 seconds)...
   ```

2. **Spinner shows it's actually working** - Watch for 10-30 seconds

3. **Results appear with timestamp:**
   ```
   ✅ Real-Time Verification Results - 2025-12-17 14:32:15

   🎉 ALL CHECKS PASSED - Data integrity verified in real-time!
   ```

4. **Expandable sections show each check:**
   - ✅ Precinct Assignment Completeness
   - ✅ Super-District Count
   - ✅ Total Seat Allocation
   - ✅ Seat Allocation Math
   - ✅ Vote Conservation (Critical)
   - ✅ Geographic Contiguity (BFS Algorithm) ← **THIS IS THE KEY ONE**
   - ✅ Geometry Validation

**What to say while waiting:**
> "Right now it's building a spatial adjacency graph from the geometries, then running Breadth-First Search on all 3 super-districts to verify they're contiguous. It's also validating all 2,658 geometries and checking vote conservation."

---

## Step 5: Expand the Contiguity Check

**Click on:** ✅ Geographic Contiguity (BFS Algorithm)

Professor will see:
```
Super-district 0: 891 precincts → ✓ Contiguous
Super-district 1: 885 precincts → ✓ Contiguous
Super-district 2: 882 precincts → ✓ Contiguous
```

**What to say:**
> "This shows that the BFS algorithm successfully traversed all precincts in each super-district. If any super-district had disconnected pieces, this check would fail."

---

## Step 6: Show the Code (If Asked)

If professor asks "How does BFS actually work?", open `dashboard_fra.py` and show him **lines 211-243**:

```python
def is_super_district_contiguous(precinct_adjacency, super_district_precincts):
    """
    Check if a super-district is geographically contiguous using BFS.
    """
    if not super_district_precincts:
        return False

    # Start BFS from arbitrary precinct
    start = next(iter(super_district_precincts))
    visited = {start}
    queue = deque([start])

    while queue:
        current = queue.popleft()

        # Check all neighbors of current precinct
        for neighbor in precinct_adjacency.get(current, set()):
            if neighbor in super_district_precincts and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # If we visited all precincts, the super-district is contiguous
    return len(visited) == len(super_district_precincts)
```

**What to say:**
> "This is the actual BFS implementation. It starts from one precinct, uses a queue to visit all connected neighbors, and if it can reach all precincts in the super-district, they're contiguous."

---

## Step 7: Scroll Down to See Technical Summary

Scroll past the map to the section:

**📋 Technical Summary: FRA Gluing Process**

Shows INPUT → PROCESS → OUTPUT with real data

**What to say:**
> "This shows what this specific plan did - started with 14 districts, merged them into 3 super-districts with 5-5-4 seats, and allocated seats proportionally."

---

## Step 8: Scroll to System Log

Keep scrolling to:

**🔍 System Verification Log - Detailed Execution Trace**

Shows terminal-style log with 7 stages

**What to say:**
> "This reconstructs the processing pipeline showing every stage - data loading, baseline plan, FRA gluing, vote aggregation, vote conservation verification, seat allocation, and final checks. The 'Re-Verify Now' button above actually runs these checks in real-time."

---

## If Professor Asks: "How do I know this is really running?"

**Demo the failure case:**

1. Say: "Good question! Let me show you what happens if the data is wrong."

2. Open `fra_pipeline/outputs/plan_347/fra_results.csv` in a text editor

3. Change one of the seat numbers (e.g., change `dem_seats` from 7 to 8)

4. Save the file

5. Refresh the dashboard

6. Click "Re-Verify Now" again

7. **It will FAIL** and show:
   ```
   ❌ Seat Allocation Math - FAILED
   Dem 8 + Rep 7 = 15 (expected 14)
   ```

8. Say: "See? It actually checks the data. If something is wrong, it catches it."

9. **IMPORTANT:** Change the file back to the correct value after demo!

---

## Key Talking Points

### "What did you add?"
- ~400 lines of verification code
- Real-time BFS contiguity checking
- 7 automated verification checks
- Detailed system logging
- Timestamped verification results

### "How does it check contiguity?"
- Builds spatial adjacency graph from geometries
- Runs BFS starting from one precinct
- Visits all connected neighbors
- If all precincts reachable → contiguous ✓
- Show the code (lines 211-243 in dashboard_fra.py)

### "How does it check vote conservation?"
- Sums votes from shapefile (original)
- Sums votes from FRA results (aggregated)
- Compares: if they don't match → FAIL
- Assertions in generation scripts crash if votes change
- Show the code (lines 678-685 in fra_gluing_algorithm.py)

### "How does seat allocation work?"
- Calculate vote share: `dem_votes / total_votes`
- Calculate proportional seats: `vote_share × total_seats`
- Round to nearest integer
- Example: 51.2% × 5 = 2.56 → rounds to 3 seats
- Show the code (lines 467-508 in fra_gluing_algorithm.py)

---

## Emergency Backup (If Something Breaks)

If the dashboard crashes or button doesn't work:

1. **Show the code** - Open `dashboard_fra.py` and show the functions (lines 184-378)
2. **Show verification in generation** - Open `fra_gluing_algorithm.py` and show assertions (lines 658-701)
3. **Show terminal output** - Run `python scripts/fra_gluing_algorithm.py` and show verification summary

---

## Files to Have Open (Just in Case)

1. `dashboard_fra.py` - The main file you modified
2. `fra_gluing_algorithm.py` - Shows actual verification during generation
3. `PROFESSOR_EXPLANATION.md` - Your detailed reference guide

---

**Time needed for demo:** 5-10 minutes

**Confidence level:** 🔥 **100%**

**You got this!** 💪
