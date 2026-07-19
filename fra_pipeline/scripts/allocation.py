"""Explicit, configurable seat-allocation and tie policies.

Consolidates three previously-implicit decisions so they are documented, tested,
and reproducible:

* Gap 17 -- the super-district allocator is a SIMPLIFIED TWO-PARTY PROPORTIONAL
  approximation, NOT full Single Transferable Vote. It has no candidate rankings,
  quotas, surplus transfers, eliminations, transfer values, or exhausted ballots.
  It simply rounds ``dem_share * seats``. Name it accordingly everywhere.
* Gap 18 -- the rounding rule at half-seat boundaries is explicit and selectable.
  The historical default is Python's built-in banker's rounding (round-half-to-even),
  preserved as ``"round_half_even"`` so existing outputs are reproducible.
* Gap 19 -- the single-member baseline tie rule (exactly equal DEM/REP votes) is
  explicit and selectable. The historical behavior awarded ties to Republicans via
  an undocumented ``else`` branch; that is preserved as the default ``"republican"``.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP

# ---------------------------------------------------------------------------
# Gap 19: single-member district tie policy
# ---------------------------------------------------------------------------

DISTRICT_TIE_POLICIES = ("republican", "democratic", "no_seat", "error")


def decide_district_winner(dem_votes: float, rep_votes: float,
                           tie_policy: str = "republican") -> str | None:
    """Return the winner of a single-member district: ``"DEM"``, ``"REP"``, or ``None``.

    ``tie_policy`` only applies when ``dem_votes == rep_votes``:

    * ``"republican"`` (historical default) -> ``"REP"``
    * ``"democratic"``                       -> ``"DEM"``
    * ``"no_seat"``                          -> ``None`` (seat awarded to neither)
    * ``"error"``                            -> raises ``ValueError``
    """
    if dem_votes > rep_votes:
        return "DEM"
    if rep_votes > dem_votes:
        return "REP"
    # exact tie
    if tie_policy == "republican":
        return "REP"
    if tie_policy == "democratic":
        return "DEM"
    if tie_policy == "no_seat":
        return None
    if tie_policy == "error":
        raise ValueError(f"district tie ({dem_votes} == {rep_votes}) with tie_policy='error'")
    raise ValueError(f"unknown tie_policy {tie_policy!r}; expected one of {DISTRICT_TIE_POLICIES}")


# ---------------------------------------------------------------------------
# Gap 17 + 18: super-district two-party proportional allocation
# ---------------------------------------------------------------------------

ALLOCATION_METHODS = ("round_half_even", "round_half_up", "largest_remainder")


def allocate_two_party_seats(dem_share: float, total_seats: int,
                             method: str = "round_half_even") -> tuple[int, int]:
    """Allocate ``total_seats`` between DEM and REP from a two-party ``dem_share``.

    Returns ``(dem_seats, rep_seats)`` with ``dem_seats + rep_seats == total_seats``.

    This is a simplified two-party proportional approximation, NOT STV (Gap 17).

    Methods (Gap 18):

    * ``"round_half_even"`` (historical default) -- banker's rounding of
      ``dem_share * total_seats``; matches the original ``round(...)`` behavior.
    * ``"round_half_up"`` -- arithmetic rounding; ``x.5`` always rounds up.
    * ``"largest_remainder"`` -- Hamilton/Hare largest-remainder method. For a
      two-party split this awards the fractional seat to whichever party has the
      larger remainder, with an explicit deterministic DEM-wins tie at exactly 0.5.
    """
    if not 0 <= total_seats:
        raise ValueError("total_seats must be non-negative")
    ds = Decimal(str(dem_share)) * total_seats

    if method == "round_half_even":
        dem_seats = int(ds.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    elif method == "round_half_up":
        dem_seats = int(ds.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    elif method == "largest_remainder":
        floor = int(ds // 1)
        remainder = ds - floor
        # one seat left to assign for two parties; DEM takes it if its remainder >= 0.5
        dem_seats = floor + (1 if remainder >= Decimal("0.5") else 0)
    else:
        raise ValueError(f"unknown method {method!r}; expected one of {ALLOCATION_METHODS}")

    dem_seats = max(0, min(total_seats, dem_seats))
    return dem_seats, total_seats - dem_seats
