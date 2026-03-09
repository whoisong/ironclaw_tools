from fastapi import FastAPI, HTTPException

from agent_service.mcp import handle_mcp_request
from agent_service.models import (
    BrowserUseRequest,
    ComputerUseRequest,
    ReadScreenRequest,
    RunCodeRequest,
    SearchWebRequest,
    SkillResult,
)
from agent_service.skills.browser_use import browser_use
from agent_service.skills.computer_use import computer_use
from agent_service.skills.read_screen import read_screen
from agent_service.skills.run_code import run_code
from agent_service.skills.search_web import search_web

app = FastAPI(title="IronClaw Local Agent Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/mcp")
def mcp_endpoint(payload: dict) -> dict:
    return handle_mcp_request(payload)


@app.post("/skills/computer_use", response_model=SkillResult)
def skill_computer_use(payload: ComputerUseRequest) -> SkillResult:
    try:
        return SkillResult(skill="computer_use", result=computer_use(payload.goal, payload.execute))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/skills/browser_use", response_model=SkillResult)
def skill_browser_use(payload: BrowserUseRequest) -> SkillResult:
    try:
        return SkillResult(
            skill="browser_use",
            result=browser_use(payload.action, payload.url, payload.selector, payload.text, payload.timeout_ms),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/skills/read_screen", response_model=SkillResult)
def skill_read_screen(payload: ReadScreenRequest) -> SkillResult:
    try:
        return SkillResult(skill="read_screen", result=read_screen(payload.question))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/skills/run_code", response_model=SkillResult)
def skill_run_code(payload: RunCodeRequest) -> SkillResult:
    try:
        return SkillResult(
            skill="run_code",
            result=run_code(payload.language, payload.code, payload.timeout_seconds),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/skills/search_web", response_model=SkillResult)
def skill_search_web(payload: SearchWebRequest) -> SkillResult:
    try:
        return SkillResult(skill="search_web", result=search_web(payload.query, payload.max_results))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
