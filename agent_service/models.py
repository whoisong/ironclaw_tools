from typing import Any, Literal

from pydantic import BaseModel, Field


class SkillResult(BaseModel):
    ok: bool = True
    skill: str
    result: dict[str, Any] = Field(default_factory=dict)


class ComputerUseRequest(BaseModel):
    goal: str = Field(min_length=1)
    execute: bool = False


class BrowserUseRequest(BaseModel):
    action: Literal["open", "click", "type", "extract"]
    url: str | None = None
    selector: str | None = None
    text: str | None = None
    timeout_ms: int = 15_000


class ReadScreenRequest(BaseModel):
    question: str = Field(min_length=1)


class RunCodeRequest(BaseModel):
    language: Literal["python", "bash"]
    code: str = Field(min_length=1)
    timeout_seconds: int = Field(default=15, ge=1, le=120)


class SearchWebRequest(BaseModel):
    query: str = Field(min_length=1)
    max_results: int = Field(default=5, ge=1, le=25)

