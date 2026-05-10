from pydantic import BaseModel
from pydantic.generics import GenericModel
from typing import Generic, TypeVar

T = TypeVar('T')

class ApiSuccessResponse(GenericModel, Generic[T]):
    success: bool = True
    data: T

class ApiErrorDetail(BaseModel):
    code: str
    message: str

class ApiErrorResponse(BaseModel):
    success: bool = False
    error: ApiErrorDetail