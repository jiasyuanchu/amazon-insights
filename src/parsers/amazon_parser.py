import re
import logging
from bs4 import BeautifulSoup
from typing import Dict, Optional, Union
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonProductParser:
    def __init__(self):
        self.price_patterns = [
            r'\$([0-9,]+\.?[0-9]*)',
            r'Price:\s*\$([0-9,]+\.?[0-9]*)',
            r'([0-9,]+\.?[0-9]*)\s*dollars?'
        ]
        
        self.bsr_patterns = [
            r'#([0-9,]+)\s*in\s*([^(]+)',
            r'Best Sellers Rank:\s*#([0-9,]+)',
            r'Amazon Best Sellers Rank:\s*#([0-9,]+)'
        ]
    
    def parse_product_data(self, raw_data: Dict) -> Optional[Dict]:
        try:
            if not raw_data or 'data' not in raw_data:
                logger.error("Invalid raw data structure")
                return None
            
            content = raw_data['data']
            html_content = content.get('html', '')
            markdown_content = content.get('markdown', '')
            
            soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
            
            product_info = {
                'scraped_at': datetime.now().isoformat(),
                'title': self._extract_title(soup, markdown_content),
                'price': self._extract_price(soup, markdown_content),
                'buybox_price': self._extract_buybox_price(soup, markdown_content),
                'rating': self._extract_rating(soup, markdown_content),
                'review_count': self._extract_review_count(soup, markdown_content),
                'bsr': self._extract_bsr(soup, markdown_content),
                'availability': self._extract_availability(soup, markdown_content)
            }
            
            logger.info(f"Successfully parsed product: {product_info['title'][:50]}...")
            return product_info
            
        except Exception as e:
            logger.error(f"Error parsing product data: {str(e)}")
            return None
    
    def _extract_title(self, soup: Optional[BeautifulSoup], markdown: str) -> str:
        # Try HTML selectors first if available
        if soup:
            title_selectors = [
                '#productTitle',
                'h1[data-automation-id="product-title"]',
                'h1.a-size-large',
                'h1#title',
                '.product-title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    if title and len(title) > 10:  # Ensure it's a meaningful title
                        return title
        
        # Extract from markdown - look for Amazon product title pattern
        if markdown:
            # Look for the pattern "Amazon.com : [PRODUCT TITLE] : Category"
            amazon_pattern = r'Amazon\.com\s*:\s*(.+?)\s*:\s*[^:]+(?:\s*:.*)?$'
            title_match = re.search(amazon_pattern, markdown, re.MULTILINE | re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                if title and len(title) > 10:
                    return title
            
            # Look for first heading
            title_match = re.search(r'^#\s*(.+?)(?:\n|$)', markdown, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
                if title and len(title) > 10:
                    return title
            
            # Look for product title in the first few lines
            lines = markdown.split('\n')[:10]
            for line in lines:
                line = line.strip()
                # Skip common navigation/header text
                if (line and len(line) > 20 and len(line) < 200 and 
                    not line.startswith(('Amazon.com', 'Search', 'Hello,', 'Cart', 'Account', 'Returns')) and
                    not re.match(r'^[\s\W]*$', line) and  # Not just whitespace/punctuation
                    ':' not in line[:20]):  # Avoid navigation items like "Sports : Outdoors"
                    return line
            
        return "Title not found"
    
    def _extract_price(self, soup: Optional[BeautifulSoup], markdown: str) -> Optional[float]:
        if soup:
            price_selectors = [
                '.a-price-whole',
                '.a-offscreen',
                '[data-automation-id="product-price"]'
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    price = self._parse_price_string(price_text)
                    if price:
                        return price
        
        for pattern in self.price_patterns:
            matches = re.findall(pattern, markdown)
            for match in matches:
                price = self._parse_price_string(match)
                if price:
                    return price
        
        return None
    
    def _extract_buybox_price(self, soup: Optional[BeautifulSoup], markdown: str) -> Optional[float]:
        if soup:
            buybox_selectors = [
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price.a-text-price.a-size-medium.apexPriceToPay'
            ]
            
            for selector in buybox_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True)
                    price = self._parse_price_string(price_text)
                    if price:
                        return price
        
        return self._extract_price(soup, markdown)
    
    def _extract_rating(self, soup: Optional[BeautifulSoup], markdown: str) -> Optional[float]:
        if soup:
            rating_selectors = [
                '[data-automation-id="product-rating"]',
                '.a-icon-alt'
            ]
            
            for selector in rating_selectors:
                element = soup.select_one(selector)
                if element:
                    rating_text = element.get_text(strip=True)
                    rating_match = re.search(r'([0-9.]+)\s*out of\s*5', rating_text)
                    if rating_match:
                        return float(rating_match.group(1))
        
        rating_patterns = [
            r'([0-9.]+)\s*out of\s*5\s*stars',
            r'Rating:\s*([0-9.]+)',
            r'([0-9.]+)\s*stars?'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, markdown)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_review_count(self, soup: Optional[BeautifulSoup], markdown: str) -> Optional[int]:
        if soup:
            review_selectors = [
                '[data-automation-id="reviews-count"]',
                '#acrCustomerReviewText'
            ]
            
            for selector in review_selectors:
                element = soup.select_one(selector)
                if element:
                    review_text = element.get_text(strip=True)
                    count = self._parse_number_string(review_text)
                    if count:
                        return count
        
        review_patterns = [
            r'([0-9,]+)\s*customer reviews?',
            r'([0-9,]+)\s*ratings?',
            r'([0-9,]+)\s*reviews?'
        ]
        
        for pattern in review_patterns:
            match = re.search(pattern, markdown)
            if match:
                return self._parse_number_string(match.group(1))
        
        return None
    
    def _extract_bsr(self, soup: Optional[BeautifulSoup], markdown: str) -> Optional[Dict]:
        bsr_data = {}
        
        for pattern in self.bsr_patterns:
            matches = re.findall(pattern, markdown, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    rank, category = match
                    rank_num = self._parse_number_string(rank)
                    if rank_num:
                        bsr_data[category.strip()] = rank_num
                elif len(match) == 1:
                    rank_num = self._parse_number_string(match[0])
                    if rank_num:
                        bsr_data['overall'] = rank_num
        
        return bsr_data if bsr_data else None
    
    def _extract_availability(self, soup: Optional[BeautifulSoup], markdown: str) -> str:
        if soup:
            availability_selectors = [
                '#availability span',
                '[data-automation-id="availability"]'
            ]
            
            for selector in availability_selectors:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        availability_patterns = [
            r'In Stock',
            r'Out of Stock',
            r'Currently unavailable',
            r'Available'
        ]
        
        for pattern in availability_patterns:
            if re.search(pattern, markdown, re.IGNORECASE):
                return pattern
        
        return "Unknown"
    
    def _parse_price_string(self, price_str: str) -> Optional[float]:
        if not price_str:
            return None
        
        price_str = re.sub(r'[^\d.,]', '', price_str)
        price_str = price_str.replace(',', '')
        
        try:
            return float(price_str)
        except ValueError:
            return None
    
    def _parse_number_string(self, num_str: str) -> Optional[int]:
        if not num_str:
            return None
        
        num_str = re.sub(r'[^\d,]', '', num_str)
        num_str = num_str.replace(',', '')
        
        try:
            return int(num_str)
        except ValueError:
            return None