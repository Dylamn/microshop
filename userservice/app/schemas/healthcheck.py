from enum import Enum
from typing import Literal

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class LivenessProbeResponse(BaseModel):
    status: Literal["alive"] = "alive"


class ReadinessProbeResponse(BaseModel):
    database: ServiceStatus = ServiceStatus.UNKNOWN

    @property
    def is_ready(self) -> bool:
        return all(val == ServiceStatus.OK for _, val in self)


class HealthContextResponse(BaseModel):
        service: str = "userservice"
        version: str
        environment: Literal["development", "staging", "production"]
        uptime_seconds: int = 0
