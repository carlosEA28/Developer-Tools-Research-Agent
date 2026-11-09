from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState,CompanyAnalysis,CompanyInfo
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts
from firecrawl.v2.types import Document, SearchResultWeb
from typing import Any


class Workflow:
    def __init__(self) -> None:
        self.firecrawl = FirecrawlService()
        self.llm = ChatOpenAI(model="gpt-5-nano", temperature=0.1)
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research",self._research_step)
        graph.add_node("analyze",self._analyze_step)

        graph.set_entry_point("extract_tools")

        graph.add_edge("extract_tools", "research")
        graph.add_edge("research","analyze")
        graph.add_edge("analyze", END)

        return graph.compile()


    def _extract_tools_step(self, state: ResearchState) -> dict[str, Any]:
        print(f"Finding Articles about: {state.query}")

        article_query = f"{state.query} tools comparison best alternatives"

        search_results = self.firecrawl.search_companies(article_query, num_results=3)

        all_content = ""

        for result in search_results.web or []:
            content = (
                result.markdown if isinstance(result, Document)
                else result.description
            )
            if content:
                all_content += content[:1500] + "\n\n"

        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]

        try:
            response = self.llm.invoke(messages)
            tool_names = [
                name.strip()
                for name in response.text.strip().split("\n")
                if name.strip()
            ]
            print(f"Extracted tools: {', '.join(tool_names[:5])}")

            return {"extracted_tools": tool_names}

        except Exception as e:
            print(e)
            return {}

    def _analyze_company_content(self, company_name:str, content:str)-> CompanyAnalysis:
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)

        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name,content))
        ]

        try:
            analysis = structured_llm.invoke(messages)

            return CompanyAnalysis.model_validate(analysis)

        except Exception as e:
            print(e)
            return CompanyAnalysis(
                pricing_model= "Unknown",
                is_open_source= None,
                tech_stack=[],
                description= "Failed",
                api_available= None,
                language_support=[],
                integration_capabilities= []
            )

    @staticmethod
    def _result_url(result: SearchResultWeb | Document) -> str | None:
        if isinstance(result, SearchResultWeb):
            return result.url
        return result.metadata.source_url or result.metadata.url if result.metadata else None

    def _research_step(self, state: ResearchState) -> dict[str, Any]:
        extracted_tools = state.extracted_tools

        if not extracted_tools:
            print("No extracted tools found, falling back to direct search")
            search_results = self.firecrawl.search_companies(state.query, num_results= 4)
            tool_names = []
            for result in search_results.web or []:
                title = (
                    result.title if isinstance(result, SearchResultWeb)
                    else result.metadata.title if result.metadata else None
                )
                if title:
                    tool_names.append(title)
        else:
            tool_names = extracted_tools[:4]

        print(f"Researching specific tools: {', '.join(tool_names)}")

        companies = []
        for tool_name in tool_names:
            tool_search_results = self.firecrawl.search_companies(tool_name + "official site", num_results=1)

            if tool_search_results.web:
                result = tool_search_results.web[0]
                url = self._result_url(result)
                if not url:
                    continue

                description = (
                    result.description if isinstance(result, SearchResultWeb)
                    else result.markdown
                ) or ""

                company = CompanyInfo(
                    name = tool_name,
                    description=description,
                    website=url,
                    tech_stack=[],
                    competitors=[]
                )

                content = result.markdown if isinstance(result, Document) else None
                if not content:
                    scraped = self.firecrawl.scrape_company_pages(url)
                    content = scraped.markdown if scraped else None
                if content:
                    analysis = self._analyze_company_content(company.name, content)

                    company.pricing_model = analysis.pricing_model
                    company.is_open_source = analysis.is_open_source
                    company.tech_stack = analysis.tech_stack
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.language_support = analysis.language_support
                    company.integration_capabilities = analysis.integration_capabilities

                companies.append(company)

        return {"companies": companies}

    def _analyze_step(self, state: ResearchState) -> dict[str, Any]:
            print("Generating recommendations")

            company_data = ", ".join(
                company.model_dump_json() for company in state.companies
            )

            messages = [
                SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
                HumanMessage(content=self.prompts.recommendations_user(state.query, company_data))
            ]

            response = self.llm.invoke(messages)
            return {"analysis": response.text}

    def run(self, query: str) -> ResearchState:
            initial_state = ResearchState(query=query)
            final_state = self.workflow.invoke(initial_state)
            return ResearchState.model_validate(final_state)
