"""Orchestrate the multi-agent price intelligence pipeline."""

import logging
import os
import json
from typing import Dict, Any

from agents.scraper import scrape_and_validate
from agents.validator import validate_product_list, ProductMetadata
from agents.pricing import compute_recommended_price
from agents.critic import evaluate_proposal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_full_pipeline(query: str, asin: str, current_price: float) -> Dict[str, Any]:
    """
    Run the full 4-agent pipeline:
    1. Scraper/Search Agent gathers data
    2. Validation Agent normalizes schemas
    3. Economics/Pricing Agent proposes price
    4. Critic/Audit Agent validates constraints
    """
    logger.info("=== Starting Price Intelligence Pipeline ===")

    # Step 1: Scrape and validate
    logger.info(f"Step 1: Scraper searching for query: {query}")
    products = scrape_and_validate(query)
    logger.info(f"Step 1 completed: {len(products)} products validated.")

    # Step 2: Validation (already done via Pydantic, but we re-ensure)
    valid_products, errors = validate_product_list([p.dict() for p in products])
    if errors:
        logger.warning(f"Validation errors: {errors}")

    # Step 3: Pricing agent proposes revised price
    logger.info(f"Step 3: Pricing agent computing proposal for {asin}")
    proposal = compute_recommended_price(asin, current_price)
    if not proposal:
        return {"status": "error", "message": "Pricing agent could not compute a proposal."}
    logger.info(f"Step 3 proposal: {proposal}")

    # Step 4: Critic evaluates against constraints
    # Add cost estimate to proposal for critic (we'll estimate roughly)
    cost_estimate = current_price * 0.6  # placeholder cost ratio
    evaluation_proposal = {
        "current_price": current_price,
        "suggested_price": proposal["suggested_price"],
        "cost_estimate": cost_estimate,
    }
    evaluation = evaluate_proposal(evaluation_proposal)
    proposal["critic_verdict"] = evaluation["verdict"]
    proposal["critic_violations"] = evaluation["violations"]
    proposal["critic_message"] = evaluation["message"]

    logger.info(f"Step 4 critic evaluation: {evaluation['verdict']} - {evaluation['message']}")

    logger.info("=== Pipeline finished ===")

    return {
        "products": [p.dict() for p in valid_products],
        "pricing_proposal": proposal,
        "pipeline_status": "completed",
    }


if __name__ == "__main__":
    import sys, json
    query = sys.argv[1] if len(sys.argv) > 1 else "wireless headphones"
    asin = sys.argv[2] if len(sys.argv) > 2 else "B0XYZ123"
    current_price = float(sys.argv[3]) if len(sys.argv) > 3 else 29.99
    result = run_full_pipeline(query, asin, current_price)
    print(json.dumps(result, indent=2))