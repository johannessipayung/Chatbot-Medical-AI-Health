from app.domain.state import ChatbotState

from langgraph.graph import (
    StateGraph,
    END
)

from app.agents.nodes import (
    node_guardrail_pii,
    node_retrieve_hybrid,
    node_crewai_generator
)


def router_guardrail(
    state: ChatbotState
):

    if state.get(
        "blocked_by_guardrail"
    ):

        return "end"

    return "continue"


def build_medical_graph():

    workflow = StateGraph(
        ChatbotState
    )

    workflow.add_node(
        "guardrail",
        node_guardrail_pii
    )

    workflow.add_node(
        "retrieve",
        node_retrieve_hybrid
    )

    workflow.add_node(
        "crewai",
        node_crewai_generator
    )

    workflow.set_entry_point(
        "guardrail"
    )

    workflow.add_conditional_edges(
        "guardrail",
        router_guardrail,
        {
            "end": END,
            "continue": "retrieve"
        }
    )

    workflow.add_edge(
        "retrieve",
        "crewai"
    )

    workflow.add_edge(
        "crewai",
        END
    )

    return workflow.compile()