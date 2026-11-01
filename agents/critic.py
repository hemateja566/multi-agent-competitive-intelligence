"""Critic/Audit Agent: Evaluates the proposed price change against business safety constraints before finalizing."""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- Constraint definitions (could be loaded from MySQL or config) ---

MIN_MARGIN_PERCENT = 18.0  # "Margin cannot drop below 18%"
MAX_PRICE_DEVIATION_PERCENT = 25.0  # max % price change from current in one go
ALLOWED_RETAILERS = {"ExampleMart", "CompetitorCo"}  # example whitelist


def check_constraints(proposal: Dict[str, Any]) -> List[str]:
    """
    Evaluate the pricing proposal against all business constraints.
    Returns a list of violation messages; empty list means all pass.
    """
    violations: List[str] = []

    # 1. Margin constraint
    current_price = proposal.get("current_price", 0)
    suggested_price = proposal.get("suggested_price", 0)
    # We need cost to compute margin; if not provided, estimate or skip.
    cost = proposal.get("cost_estimate")
    if cost is None:
        # Simple estimate: assume current price reflects some margin.
        # For demonstration, we'll compute margin as if cost is fixed.
        # In production, fetch cost from DB.
        violations.append("Cost estimate missing; cannot verify margin constraint.")
        return violations

    margin = ((suggested_price - cost) / suggested_price) * 100
    if margin < MIN_MARGIN_PERCENT:
        violations.append(
            f"Margin would drop to {margin:.1f}%, below minimum allowed {MIN_MARGIN_PERCENT}%."
        )

    # 2. Price deviation constraint
    if current_price and current_price > 0:
        deviation_pct = abs(suggested_price - current_price) / current_price * 100
        if deviation_pct > MAX_PRICE_DEVIATION_PERCENT:
            violations.append(
                f"Price deviation {deviation_pct:.1f}% exceeds maximum allowed {MAX_PRICE_DEVIATION_PERCENT}%."
            )

    # 3. Retailer eligibility (if proposal includes retailer change)
    retailer = proposal.get("retailer")
    if retailer and retailer not in ALLOWED_RETAILERS:
        violations.append(f"Retailer '{retailer}' is not in the allowed list.")

    return violations


def evaluate_proposal(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return an evaluation result with verdict and details.
    verdict: "APPROVE", "REJECT", "REVISE"
    """
    violations = check_constraints(proposal)
    if not violations:
        return {"verdict": "APPROVE", "violations": [], "message": "All constraints passed."}
    elif any("Margin" in v for v in violations):
        # Could revise to meet margin
        return {
            "verdict": "REVISE",
            "violations": violations,
            "message": "Proposal violates margin constraints. Revise to meet minimum margin.",
        }
    else:
        return {
            "verdict": "REJECT",
            "violations": violations,
            "message": "Proposal rejected due to constraint violations.",
        }


if __name__ == "__main__":
    import sys, json
    proposal = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {
        "current_price": 29.99,
        "suggested_price": 24.00,
        "cost_estimate": 19.60,
    }
    result = evaluate_proposal(proposal)
    print(json.dumps(result, indent=2))