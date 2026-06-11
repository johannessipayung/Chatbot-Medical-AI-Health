from crewai import (
    Agent,
    Task,
    Crew
)

from app.config.llm_config import (
    get_crewai_llm
)


class MedicalCrewFactory:

    @staticmethod
    def create_generation_crew(
        context: str,
        question: str
    ):

        crewai_llm = get_crewai_llm()

        analyst = Agent(
            role="Medical Clinical Analyst",

            goal="""
Extract accurate clinical evidence
from medical documents.
""",

            backstory="""
Senior clinical specialist that only
uses evidence-based medical guidelines.
""",

            llm=crewai_llm,

            verbose=True
        )

        evidence_reviewer = Agent(
            role="Medical Evidence Reviewer",

            goal="""
Validate that medical evidence is
reliable and recent.
""",

            backstory="""
Expert reviewer of WHO and clinical guidelines.
""",

            llm=crewai_llm,

            verbose=True
        )

        safety_validator = Agent(
            role="Medical Safety Validator",

            goal="""
Prevent hallucinations, dangerous
medical advice, overdose instruction,
and unsupported claims.
""",

            backstory="""
Expert AI medical safety specialist.
""",

            llm=crewai_llm,

            verbose=True
        )

        communicator = Agent(
            role="Medical Communicator",

            goal="""
Create transparent medical responses.
Must include:
- source citation
- page citation
- confidence score
- disclaimer
""",

            backstory="""
Professional healthcare communicator.
""",

            llm=crewai_llm,

            verbose=True
        )

        analysis_task = Task(

            description=f"""
Analyze this question carefully:

QUESTION:
{question}

MEDICAL CONTEXT:
{context}

Extract the most relevant
clinical evidence only.
""",

            expected_output="""
Structured medical findings.
""",

            agent=analyst
        )

        review_task = Task(

            description="""
Review whether the evidence
is medically reliable.
""",

            expected_output="""
Validated medical evidence.
""",

            agent=evidence_reviewer
        )

        safety_task = Task(

            description="""
Check for harmful advice,
unsafe dosage,
hallucinations,
or unsupported claims.
""",

            expected_output="""
Safe medical validation.
""",

            agent=safety_validator
        )

        communication_task = Task(

            description=f"""
Generate final answer for:

{question}

Requirements:
- Use ONLY provided medical evidence
- Include citations
- Include page number
- Include confidence score
- Include disclaimer
- Do NOT hallucinate
""",

            expected_output="""
Professional medical answer with citations.
""",

            agent=communicator
        )

        crew = Crew(
            agents=[
                analyst,
                evidence_reviewer,
                safety_validator,
                communicator
            ],

            tasks=[
                analysis_task,
                review_task,
                safety_task,
                communication_task
            ],

            verbose=True
        )

        return crew