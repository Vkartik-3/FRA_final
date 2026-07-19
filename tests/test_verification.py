#!/usr/bin/env python3
"""
Quick test script to verify the BFS contiguity checking works correctly.
Run this before the professor meeting to make sure everything is working.
"""

from collections import deque

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


def test_bfs():
    """Test the BFS algorithm with simple cases."""

    print("Testing BFS Contiguity Algorithm")
    print("=" * 50)

    # Test 1: Simple connected graph
    print("\nTest 1: Simple connected graph (3 nodes in a line)")
    adjacency = {
        0: {1},
        1: {0, 2},
        2: {1}
    }
    nodes = {0, 1, 2}
    result = is_super_district_contiguous(adjacency, nodes)
    print(f"  Expected: True, Got: {result} - {'PASS' if result else 'FAIL'}")

    # Test 2: Disconnected graph
    print("\nTest 2: Disconnected graph (2 separate components)")
    adjacency = {
        0: {1},
        1: {0},
        2: {3},
        3: {2}
    }
    nodes = {0, 1, 2, 3}  # All 4 nodes, but 0-1 disconnected from 2-3
    result = is_super_district_contiguous(adjacency, nodes)
    print(f"  Expected: False, Got: {result} - {'PASS' if not result else 'FAIL'}")

    # Test 3: Complex connected graph
    print("\nTest 3: Complex connected graph (6 nodes, multiple paths)")
    adjacency = {
        0: {1, 2},
        1: {0, 3},
        2: {0, 4},
        3: {1, 5},
        4: {2, 5},
        5: {3, 4}
    }
    nodes = {0, 1, 2, 3, 4, 5}
    result = is_super_district_contiguous(adjacency, nodes)
    print(f"  Expected: True, Got: {result} - {'PASS' if result else 'FAIL'}")

    # Test 4: Partial selection (only some nodes)
    print("\nTest 4: Partial selection (only nodes 0, 1, 3 from complex graph)")
    nodes = {0, 1, 3}  # Connected: 0-1-3
    result = is_super_district_contiguous(adjacency, nodes)
    print(f"  Expected: True, Got: {result} - {'PASS' if result else 'FAIL'}")

    # Test 5: Partial selection that's disconnected
    print("\nTest 5: Partial selection disconnected (nodes 0, 3 from complex graph)")
    nodes = {0, 3}  # Not connected without node 1
    result = is_super_district_contiguous(adjacency, nodes)
    print(f"  Expected: False, Got: {result} - {'PASS' if not result else 'FAIL'}")

    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    test_bfs()
