from pydantic import BaseModel


class JobEvaluation(BaseModel):
    id: int
    reason: str
    decision: str