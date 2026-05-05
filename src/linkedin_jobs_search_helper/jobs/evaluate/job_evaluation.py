from pydantic import BaseModel


class JobEvaluation(BaseModel):
    id: int
    reason: str
    decision: str


class JobEvaluations(BaseModel):
    jobs: list[JobEvaluation]
