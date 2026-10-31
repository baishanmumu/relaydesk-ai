# relaydesk/app/services/tools/woocommerce.py

import httpx
from langchain_core.tools import tool
from relaydesk.app.core.settings import get_settings
from relaydesk.app.core.logger import logger
from typing import List, Dict, Optional

settings = get_settings()

@tool
def search_products(query: str, limit: int = 10) -> List[Dict]:
    """Search for products in WooCommerce based on a query.
    
    Args:
        query: The search query (e.g., product name, category).
        limit: Maximum number of products to return (default: 10).
        
    Returns:
        A list of product dictionaries with key details.
    """
    logger.info("WooCommerce product search started (limit=%d).", limit)
    
    if not settings.WOOCOMMERCE_API_URL or not settings.WOOCOMMERCE_CONSUMER_KEY or not settings.WOOCOMMERCE_CONSUMER_SECRET:
        error_msg = "WooCommerce API credentials are not configured."
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Ensure the URL follows the correct WooCommerce REST API format
    base_url = settings.WOOCOMMERCE_API_URL.rstrip('/')
    
    if not base_url.endswith('/wp-json/wc/v3'):
        # If the URL doesn't include the API path, add it
        if '/wp-json/wc/v3' not in base_url:
            url = f"{base_url}/wp-json/wc/v3/products"
        else:
            url = f"{base_url}/products"
    else:
        url = f"{base_url}/products"
    
    params = {
        "search": query,
        "per_page": max(1, min(limit, 100))
    }
    
    with httpx.Client(timeout=30.0) as client:
        try:
            response = client.get(
                url,
                params=params,
                auth=httpx.BasicAuth(settings.WOOCOMMERCE_CONSUMER_KEY, settings.WOOCOMMERCE_CONSUMER_SECRET)
            )
            
            logger.info(f"📊 Response status: {response.status_code}")
            response.raise_for_status()
            products = response.json()
            
            logger.info(f"✅ Successfully retrieved {len(products)} products")
            
            # Extract key information
            simplified_products = []
            for product in products:
                simplified_products.append({
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "description": product.get("short_description") or product.get("description", "")[:100] + "...",
                    "permalink": product.get("permalink"),
                    "sku": product.get("sku"),
                })
            
            return simplified_products
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Product search failed with status {e.response.status_code}.") from None
        except httpx.TimeoutException:
            raise RuntimeError("Product search timed out.") from None
        except httpx.ConnectError:
            raise RuntimeError("Product search service is unavailable.") from None
        except Exception:
            raise RuntimeError("Product search failed.") from None

@tool
def search_orders(search_type: str, search_value: str, limit: int = 10) -> List[Dict]:
    """Search for orders in WooCommerce based on specific criteria.
    
    Args:
        search_type: The type of search to perform. Must be one of: 'email', 'name', or 'id'.
        search_value: The value to search for based on the search_type.
        limit: Maximum number of orders to return (default: 10).
        
    Returns:
        A list of order dictionaries with key details.
    """
    logger.info("WooCommerce order search started (type=%s, limit=%d).", search_type, limit)
    
    if not settings.WOOCOMMERCE_API_URL or not settings.WOOCOMMERCE_CONSUMER_KEY or not settings.WOOCOMMERCE_CONSUMER_SECRET:
        error_msg = "WooCommerce API credentials are not configured."
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Validate search_type
    valid_search_types = ['email', 'name', 'id']
    if search_type not in valid_search_types:
        error_msg = f"Invalid search_type: {search_type}. Must be one of: {valid_search_types}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Ensure the URL follows the correct WooCommerce REST API format
    base_url = settings.WOOCOMMERCE_API_URL.rstrip('/')
    
    if not base_url.endswith('/wp-json/wc/v3'):
        # If the URL doesn't include the API path, add it
        if '/wp-json/wc/v3' not in base_url:
            url = f"{base_url}/wp-json/wc/v3/orders"
        else:
            url = f"{base_url}/orders"
    else:
        url = f"{base_url}/orders"
    
    
    # Build parameters based on search type
    params = {
        "per_page": max(1, min(limit, 100))
    }
    
    if search_type == 'email':
        # Search by customer email
        params["customer_email"] = search_value
    elif search_type == 'name':
        # For name search, we'll search in billing first and last name
        params["search"] = search_value
    elif search_type == 'id':
        # For ID search, we can directly get the order
        try:
            order_id = int(search_value)
            url = f"{url}/{order_id}"
            params = {}  # No params needed for specific order
        except ValueError:
            # If not a valid integer, treat as a general search
            params["search"] = search_value
    
    
    # Use synchronous httpx client with longer timeout for orders
    with httpx.Client(timeout=60.0) as client:
        try:
            response = client.get(
                url,
                params=params,
                auth=httpx.BasicAuth(settings.WOOCOMMERCE_CONSUMER_KEY, settings.WOOCOMMERCE_CONSUMER_SECRET)
            )
            
            logger.info(f"📊 Order search response status: {response.status_code}")
            response.raise_for_status()
            
            # Handle single order response (when searching by ID)
            if search_type == 'id' and params == {}:
                order = response.json()
                orders = [order] if order else []
            else:
                orders = response.json()
            
            logger.info(f"✅ Successfully retrieved {len(orders)} orders")
            
            # Log search results for debugging
            if len(orders) == 0:
                logger.warning("No orders found for the requested search type (%s).", search_type)
            
            # Extract key information
            simplified_orders = []
            for order in orders:
                simplified_orders.append({
                    "id": order.get("id"),
                    "status": order.get("status"),
                    "total": order.get("total"),
                    "currency": order.get("currency"),
                    "date_created": order.get("date_created"),
                })
            
            return simplified_orders
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Order search failed with status {e.response.status_code}.") from None
        except httpx.TimeoutException:
            raise RuntimeError("Order search timed out.") from None
        except httpx.ConnectError:
            raise RuntimeError("Order search service is unavailable.") from None
        except Exception:
            raise RuntimeError("Order search failed.") from None

# Additional tools for WooCommerce operations can be added here if needed
