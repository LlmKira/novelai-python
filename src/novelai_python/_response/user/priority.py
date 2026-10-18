# @File    : priority.py

from pydantic import BaseModel, Field


class PriorityResp(BaseModel):
    """GET /user/priority: the account's task priority balance."""

    maxPriorityActions: int | None = Field(default=None, description="Priority actions the balance refills to")
    nextRefillAt: int | None = Field(default=None, description="Next priority refill (UNIX timestamp)")
    taskPriority: float | None = Field(default=None, description="Current task priority")
