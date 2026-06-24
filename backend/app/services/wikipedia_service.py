import logging
import httpx
from typing import Optional, List, Dict, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)


class WikipediaService:
    """
    Dịch vụ lấy thông tin y tế từ Wikipedia.
    Hỗ trợ cả Wikipedia tiếng Anh và tiếng Việt.
    Không yêu cầu API key - hoàn toàn miễn phí!
    """

    # Các endpoint của Wikipedia
    EN_WIKI_API = "https://en.wikipedia.org/w/api.php"
    VI_WIKI_API = "https://vi.wikipedia.org/w/api.php"
    
    # Thời gian chờ (timeout) cho các yêu cầu
    TIMEOUT = 10

    @staticmethod
    def _get_wiki_api_url(language: str = "en") -> str:
        """Lấy Wikipedia API endpoint dựa trên ngôn ngữ."""
        if language.lower() in ["vi", "vietnamese"]:
            return WikipediaService.VI_WIKI_API
        return WikipediaService.EN_WIKI_API

    async def search(self, query: str, language: str = "en", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Tìm kiếm các bài viết trên Wikipedia khớp với truy vấn.
        
        Tham số:
            query: Thuật ngữ tìm kiếm (ví dụ: "aspirin", "drug interaction")
            language: "en" hoặc "vi" cho tiếng Anh hoặc tiếng Việt
            limit: Số lượng kết quả tối đa trả về
            
        Trả về:
            Danh sách kết quả tìm kiếm với tiêu đề và đoạn trích dẫn (snippet)
        """
        try:
            wiki_url = self._get_wiki_api_url(language)
            
            params = {
                "action": "query",
                "format": "json",
                "srsearch": query,
                "srwhat": "text",
                "srprop": "snippet|size|timestamp",
                "srlimit": limit,
                "list": "search"
            }
            
            headers = {
                "User-Agent": "MediAI/1.0 (https://localhost)"
            }
            
            logger.info(f"[Wikipedia] Searching '{query}' in {language} Wikipedia")
            
            async with httpx.AsyncClient(trust_env=False, headers=headers, follow_redirects=True) as client:
                response = await client.get(wiki_url, params=params, timeout=self.TIMEOUT)
                
                if response.status_code != 200:
                    logger.warning(f"[Wikipedia] Search failed: {response.status_code} {response.text}")
                    return []
                
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                
                logger.info(f"[Wikipedia] Found {len(search_results)} results")
                return search_results
                
        except Exception as e:
            logger.error(f"[Wikipedia] Search error: {e}")
            return []

    async def get_article_summary(
        self, 
        article_title: str, 
        language: str = "en", 
        chars: int = 500
    ) -> Optional[str]:
        """
        Lấy phần giới thiệu/tóm tắt của một bài viết trên Wikipedia.
        
        Tham số:
            article_title: Tiêu đề bài viết Wikipedia
            language: "en" hoặc "vi"
            chars: Số lượng ký tự tối đa trả về (mặc định 500)
            
        Trả về:
            Tóm tắt bài viết hoặc None nếu không tìm thấy
        """
        try:
            wiki_url = self._get_wiki_api_url(language)
            
            params = {
                "action": "query",
                "format": "json",
                "titles": article_title,
                "prop": "extracts",
                "explaintext": "true",
                "exintro": "true",  # Chỉ lấy phần giới thiệu (intro)
                "exchars": chars
            }
            
            logger.info(f"[Wikipedia] Fetching article: '{article_title}' ({language})")
            
            headers = {
                "User-Agent": "MediAI/1.0 (https://localhost)"
            }
            async with httpx.AsyncClient(trust_env=False, headers=headers, follow_redirects=True) as client:
                response = await client.get(wiki_url, params=params, timeout=self.TIMEOUT)
                
                if response.status_code != 200:
                    logger.warning(f"[Wikipedia] Fetch failed: {response.status_code} {response.text}")
                    return None
                
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                
                # Lấy trang đầu tiên (và thường là duy nhất)
                for page_id, page_data in pages.items():
                    if page_id != "-1":  # -1 nghĩa là không tìm thấy trang
                        extract = page_data.get("extract", "").strip()
                        if extract:
                            logger.info(f"[Wikipedia] Got extract for '{article_title}' ({len(extract)} chars)")
                            return extract
                
                logger.warning(f"[Wikipedia] Article not found: '{article_title}'")
                return None
                
        except Exception as e:
            logger.error(f"[Wikipedia] Get article error: {e}")
            return None

    async def get_full_article(
        self, 
        article_title: str, 
        language: str = "en"
    ) -> Optional[str]:
        """
        Lấy nội dung đầy đủ của một bài viết trên Wikipedia.
        
        Tham số:
            article_title: Tiêu đề bài viết Wikipedia
            language: "en" hoặc "vi"
            
        Trả về:
            Nội dung đầy đủ bài viết hoặc None nếu không tìm thấy
        """
        try:
            wiki_url = self._get_wiki_api_url(language)
            
            params = {
                "action": "query",
                "format": "json",
                "titles": article_title,
                "prop": "extracts",
                "explaintext": "true"
            }
            
            logger.info(f"[Wikipedia] Fetching full article: '{article_title}' ({language})")
            
            headers = {
                "User-Agent": "MediAI/1.0 (https://localhost)"
            }
            async with httpx.AsyncClient(trust_env=False, headers=headers, follow_redirects=True) as client:
                response = await client.get(wiki_url, params=params, timeout=self.TIMEOUT)
                
                if response.status_code != 200:
                    logger.warning(f"[Wikipedia] Full article fetch failed: {response.status_code} {response.text}")
                    return None
                
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                
                for page_id, page_data in pages.items():
                    if page_id != "-1":
                        extract = page_data.get("extract", "").strip()
                        if extract:
                            # Giới hạn ở 3000 ký tự đầu tiên để tránh quá tải ngữ cảnh (context)
                            return extract[:3000]
                
                return None
                
        except Exception as e:
            logger.error(f"[Wikipedia] Get full article error: {e}")
            return None

    async def search_and_summarize(
        self,
        query: str,
        language: str = "en"
    ) -> Optional[str]:
        """
        Tìm kiếm một thuật ngữ và trả về tóm tắt của bài viết khớp nhất.
        
        Tham số:
            query: Thuật ngữ tìm kiếm
            language: "en" hoặc "vi"
            
        Trả về:
            Tóm tắt bài viết hoặc None
        """
        try:
            # Tìm kiếm trước
            results = await self.search(query, language, limit=1)
            
            article_title = None
            if results:
                article_title = results[0].get("title")
            else:
                logger.warning(f"[Wikipedia] No search results for '{query}', trying direct article fetch")
                article_title = query
            
            if not article_title:
                return None
            
            # Lấy tóm tắt bài viết
            summary = await self.get_article_summary(article_title, language)
            
            if summary:
                # Thêm liên kết bài viết để tham khảo
                wiki_lang = "vi" if language.lower() in ["vi", "vietnamese"] else "en"
                article_url = f"https://{wiki_lang}.wikipedia.org/wiki/{quote(article_title)}"
                return f"{summary}\n\n[Source: Wikipedia - {article_title}]({article_url})"
            
            return None
            
        except Exception as e:
            logger.error(f"[Wikipedia] Search and summarize error: {e}")
            return None

    async def extract_medical_context(
        self,
        terms: List[str],
        language: str = "en",
        max_results: int = 3
    ) -> Dict[str, Optional[str]]:
        """
        Trích xuất thông tin y tế cho nhiều thuật ngữ (thuốc, bệnh lý, triệu chứng).
        
        Tham số:
            terms: Danh sách các thuật ngữ y tế cần tra cứu
            language: "en" hoặc "vi"
            max_results: Số lượng bài viết tối đa để lấy cho mỗi thuật ngữ
            
        Trả về:
            Từ điển ánh xạ thuật ngữ -> tóm tắt
        """
        results = {}
        
        for term in terms:
            try:
                summary = await self.search_and_summarize(term, language)
                results[term] = summary
            except Exception as e:
                logger.error(f"[Wikipedia] Error extracting context for '{term}': {e}")
                results[term] = None
        
        return results


# Thực thể toàn cục (global instance)
wikipedia_service = WikipediaService()
