from pydantic import BaseModel
from typing import List, Dict, Any

class GraphNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class GraphRelationship(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphRelationship]
