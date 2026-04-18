from typing import Annotated, Dict, List, TypedDict, Union
from langgraph.graph import StateGraph, END
import operator

class ReporterState(TypedDict):
    repo_url: str
    memory_context: str
    specialist_outputs: Annotated[Dict[str, str], operator.ior]
    models_used: Annotated[Dict[str, str], operator.ior]
    final_report: str
    config: Dict[str, Union[int, float, bool, str]]
    available_models: List[str]

def create_reporter_graph():
    workflow = StateGraph(ReporterState)
    
    # Adding a dummy node so the graph compilation does not fail in LangGraph
    def dummy_node(state: ReporterState):
        return state
        
    workflow.add_node("entry", dummy_node)
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", END)
    
    return workflow.compile()
