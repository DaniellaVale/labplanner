from fastapi import APIRouter
from ..models import DoeRequest, DoeResponse
from ..services.doe_client import call_doe_service

router = APIRouter()


@router.post("/generate", response_model=DoeResponse)
async def create_design(req: DoeRequest):
    payload = req.model_dump()
    result = call_doe_service(payload)
    return result
