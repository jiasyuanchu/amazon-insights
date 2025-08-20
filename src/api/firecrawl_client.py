import logging
from typing import Dict, Optional
from config.config import FIRECRAWL_API_KEY

try:
    from firecrawl import FirecrawlApp
except ImportError:
    # Fallback for older versions
    try:
        from firecrawl_py import FirecrawlApp
    except ImportError:
        FirecrawlApp = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirecrawlClient:
    def __init__(self):
        if not FirecrawlApp:
            raise ImportError(
                "FirecrawlApp not available. Please install firecrawl-py."
            )

        self.api_key = FIRECRAWL_API_KEY
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment variables")

        self.app = FirecrawlApp(api_key=self.api_key)

    def scrape_amazon_product(self, asin: str) -> Optional[Dict]:
        amazon_url = f"https://www.amazon.com/dp/{asin}"

        try:
            logger.info(f"Scraping ASIN: {asin}")
            result = self.app.scrape(
                url=amazon_url,
                formats=["markdown"],
                include_tags=["title", "span", "div", "p"],
                exclude_tags=["script", "style", "nav", "footer", "img"],
                wait_for=2000,
                timeout=20000,
            )

            if result:
                logger.info(f"Successfully scraped ASIN: {asin}")
                # Convert the result to dict format
                if hasattr(result, "__dict__"):
                    result_dict = result.__dict__
                elif hasattr(result, "model_dump"):
                    result_dict = result.model_dump()
                else:
                    result_dict = result

                return {"data": result_dict}
            else:
                logger.error(f"Empty result for ASIN {asin}")
                return None

        except Exception as e:
            logger.error(f"Error scraping ASIN {asin}: {str(e)}")
            return None

    def batch_scrape_products(self, asins: list) -> Dict[str, Dict]:
        results = {}
        for asin in asins:
            result = self.scrape_amazon_product(asin)
            if result:
                results[asin] = result
        return results
