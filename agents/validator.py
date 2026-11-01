"""Validation Agent: Audits the scraped structured data against Pydantic schemas to ensure clean normalization."""

import logging
from typing import List, Optional
from .scraper import ProductMetadata, SearchResult

logger = logging.getLogger(__name__)


def validate_product_list(products: List[Dict[str, Any]]) -> tuple:
    """
    Validate a list of product dictionaries against the ProductMetadata schema.
    Returns (valid_products, errors).
    """
    valid: List[ProductMetadata] = []
    errors: List[str] = []
    for i, data in enumerate(products):
        try:
            product = ProductMetadata(**data)
            valid.append(product)
            logger.info(f"Product {i} validated: {product.asin}")
        except Exception as e:
            err_msg = f"Product {i} validation error: {e}"
            errors.append(err_msg)
            logger.error(err_msg)
    return valid, errors


def validate_search_result(result: Dict[str, Any]) -> tuple:
    """Validate a single SearchResult dict."""
    try:
        sr = SearchResult(**result)
        return sr, []
    except Exception as e:
        return [], [f"SearchResult validation error: {e}"]


if __name__ == "__main__":
    import sys, json
    # Simple test
    raw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"products": [], "total_found": 0}
    valid, errs = validate_product_list(raw.get("products", []))
    print(f"Valid: {len(valid)}, Errors: {len(errs)}")
    for v in valid:
        print(v.asin, v.title, v.price)