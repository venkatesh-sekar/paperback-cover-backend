import ast
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

CUSTOM_COVER_STYLE = "custom"


class CoverArtInput(BaseModel):
    book_id: str
    cover_style: str
    template_data: dict
    selected_entities: Dict[str, str]
    model_name: Optional[str] = None
    optimise_prompt: bool = False


class CoverArtSchema(BaseModel):
    id: str
    image_url: str
    created_at: datetime


class CoverArtOutput(BaseModel):
    image_url: str
    image_width: int
    image_height: int


class InferenceRequest(BaseModel):
    base_model: str
    image_width: int
    image_height: int
    positive_prompt: str
    negative_prompt: str
    steps: int
    sampler_name: str
    guidance_scale: float
    seed: int


class TextRegion(BaseModel):
    text: str
    bounding_box: List[float]  # [x1, y1, x2, y2, x3, y3, x4, y4]


class OcrResult(BaseModel):
    regions: List[TextRegion]

    @classmethod
    def from_replicate_json(cls, response: dict) -> "OcrResult":
        """
        Parses the JSON string from Replicate into an OcrResult object.
        """

        class _OcrInternalData(BaseModel):
            quad_boxes: List[List[float]]
            labels: List[str]

        class _OcrRawResponse(BaseModel):
            data: _OcrInternalData = Field(..., alias="<OCR_WITH_REGION>")

        text_data: str = response["text"]
        data: dict = ast.literal_eval(text_data)

        raw_response = _OcrRawResponse.model_validate(data)

        regions = []
        internal_data = raw_response.data
        for label, box in zip(internal_data.labels, internal_data.quad_boxes):
            regions.append(TextRegion(text=label, bounding_box=box))

        return cls(regions=regions)
