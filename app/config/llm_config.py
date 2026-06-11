from langchain_openai import ChatOpenAI

from crewai import LLM

from app.config.settings import settings


def get_langchain_llm():

    return ChatOpenAI(
        model=settings.MODEL_NAME,
        openai_api_key=settings.MAIA_API_KEY,
        openai_api_base=settings.MAIA_BASE_URL,
        temperature=0.1
    )


def get_crewai_llm():

    return LLM(
        model=f"openai/{settings.MODEL_NAME}",
        api_key=settings.MAIA_API_KEY,
        base_url=settings.MAIA_BASE_URL,
        temperature=0.1
    )