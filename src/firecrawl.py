import os
from firecrawl import FirecrawlApp, ScrapeOptions
from firecrawl.v2.types import Document, SearchData
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService():
    def __init__(self) -> None:
        api_key= os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Missing FIRECRAWL_API_KEY env variable")

        self.app = FirecrawlApp(api_key=api_key)

    def search_companies(self, query: str, num_results: int = 5) -> SearchData:
        try:
            result = self.app.search(
                query=query,
                limit=num_results,
                scrape_options= ScrapeOptions(
                    formats=["markdown"]
                )
            )

            return result

        except Exception as e:
            print(e)
            return SearchData()

    def scrape_company_pages(self, url: str) -> Document | None:
        try:
            result = self.app.scrape(
                url, formats=["markdown"]
            )
            return result if isinstance(result, Document) else None

        except Exception as e:
                print(e)
                return None
