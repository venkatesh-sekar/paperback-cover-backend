import logging
import random
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from paperback_cover.cover_art.instructions.flux_1_1_pro import (
    flux_1_1_pro_instructions,
)
from paperback_cover.cover_art.instructions.flux_1_1_pro_ultra import (
    flux_1_1_pro_ultra_instructions,
)
from paperback_cover.cover_art.instructions.ideogram_v2 import ideogram_v2_instructions

logger = logging.getLogger(__name__)


class Handler(BaseModel):
    def handle(self, data: dict, **kwargs) -> dict:
        raise NotImplementedError


class SeedDetails(Handler):
    seed_name: str = "seed"
    seed_lower_bound: int
    seed_upper_bound: int

    def handle(self, data: dict, **kwargs) -> dict:
        data[self.seed_name] = random.randint(
            self.seed_lower_bound, self.seed_upper_bound
        )
        return data


class HeightAndWidthRestrictor(Handler):
    height_name: str = "height"
    width_name: str = "width"
    height_upper_bound: int | None = None
    width_upper_bound: int | None = None

    def handle(self, data: dict, **kwargs) -> dict:
        h_key = self.height_name
        w_key = self.width_name

        # only run if both dimensions are present
        if h_key in data and w_key in data:
            height = data[h_key]
            width = data[w_key]

            # guard against zero or negative values
            if height <= 0 or width <= 0:
                return data

            # compute how much to scale down each dimension
            scale = 1.0
            if self.height_upper_bound is not None and height > self.height_upper_bound:
                scale = min(scale, self.height_upper_bound / height)
            if self.width_upper_bound is not None and width > self.width_upper_bound:
                scale = min(scale, self.width_upper_bound / width)

            # apply the shrink (only if it actually needs reducing)
            if scale < 1.0:
                new_h = height * scale
                new_w = width * scale
                # if you want integer pixels:
                data[h_key] = int(new_h)
                data[w_key] = int(new_w)

        return data


class DivisibleByNumberRestrictor(Handler):
    height_name: str = "height"
    width_name: str = "width"
    multiple: int = 8

    def handle(self, data: dict, **kwargs) -> dict:
        h_key, w_key = self.height_name, self.width_name

        if h_key in data and w_key in data:
            height = data[h_key]
            width = data[w_key]

            # guard against invalid inputs
            if height <= 0 or width <= 0:
                return data

            aspect_ratio = width / height

            # snap height to nearest multiple of 8
            m = self.multiple
            snapped_h = max(m, int(round(height / m) * m))

            # compute width by ratio and then snap to nearest multiple
            snapped_w = max(m, int(round((snapped_h * aspect_ratio) / m) * m))

            data[h_key] = snapped_h
            data[w_key] = snapped_w

        return data


class StyleReferenceImageListDetails(Handler):
    key: str = "style_reference_image_list"

    def handle(self, data: dict, **kwargs) -> dict:
        style_reference_image_list = kwargs.get("style_reference_image_list")
        if style_reference_image_list:
            data[self.key] = style_reference_image_list
        return data


class AspectRatioDetails(Handler):
    aspect_ratio_name: str = "aspect_ratio"
    aspect_ratio_options: List[str]  # Example ["1:1", "4:5", "16:9"]

    def find_closest_aspect_ratio(self, width: int, height: int) -> str:
        all_ratios = [ratio.split(":") for ratio in self.aspect_ratio_options]
        all_ratios = [(int(ratio[0]), int(ratio[1])) for ratio in all_ratios]
        all_ratios.sort(key=lambda x: abs(x[0] / x[1] - width / height))
        return f"{all_ratios[0][0]}:{all_ratios[0][1]}"

    def handle(self, data: dict, **kwargs) -> dict:
        width = kwargs["width"]
        height = kwargs["height"]
        aspect_ratio = self.find_closest_aspect_ratio(width, height)
        data[self.aspect_ratio_name] = aspect_ratio
        return data


class WidhtAndHeightOptions(Handler):
    name: str = "size"
    options: List[str]  # Example ["1024x1024"]

    def find_closest_width_height(self, width: int, height: int) -> str:
        all_sizes = [size.split("x") for size in self.options]
        all_sizes = [(int(size[0]), int(size[1])) for size in all_sizes]

        target_aspect_ratio = width / height

        # Sort by aspect ratio similarity first, then by size proximity
        all_sizes.sort(
            key=lambda x: (
                abs((x[0] / x[1]) - target_aspect_ratio),
                abs(x[0] - width) + abs(x[1] - height),
            )
        )
        return f"{all_sizes[0][0]}x{all_sizes[0][1]}"

    def handle(self, data: dict, **kwargs) -> dict:
        width = kwargs["width"]
        height = kwargs["height"]
        size = self.find_closest_width_height(width, height)
        data[self.name] = size
        return data


class WidhtAndHeightSeperatedOptions(Handler):
    width_name: str = "width"
    height_name: str = "height"
    options: List[str]  # Example ["1024x1024"]

    def find_closest_width_height(self, width: int, height: int) -> tuple[int, int]:
        all_sizes = [size.split("x") for size in self.options]
        all_sizes = [(int(size[0]), int(size[1])) for size in all_sizes]

        target_aspect_ratio = width / height

        # Sort by aspect ratio similarity first, then by size proximity
        all_sizes.sort(
            key=lambda x: (
                abs((x[0] / x[1]) - target_aspect_ratio),
                abs(x[0] - width) + abs(x[1] - height),
            )
        )
        return all_sizes[0][0], all_sizes[0][1]

    def handle(self, data: dict, **kwargs) -> dict:
        width = kwargs["width"]
        height = kwargs["height"]
        closest_width, closest_height = self.find_closest_width_height(width, height)
        data[self.width_name] = closest_width
        data[self.height_name] = closest_height
        return data


class DirectWidthHeight(Handler):
    width_name: str = "width"
    height_name: str = "height"

    def handle(self, data: dict, **kwargs) -> dict:
        data[self.width_name] = kwargs["width"]
        data[self.height_name] = kwargs["height"]
        return data


class ImagePromptDetails(Handler):
    image_prompt_name: str = "image_prompt"
    image_url: Optional[str] = None

    def handle(self, data: dict, **kwargs) -> dict:
        if not kwargs["image_prompt_url"]:
            return data
        image_url = kwargs["image_prompt_url"]
        data[self.image_prompt_name] = image_url
        return data


class ImagePromptStrength(Handler):
    image_prompt_strength_name: str = "image_prompt_strength"
    lower_bound: int
    upper_bound: int

    def handle(self, data: dict, **kwargs) -> dict:
        if not kwargs["image_prompt_strength"]:
            return data
        strength = kwargs["image_prompt_strength"]
        modified_strength = (self.upper_bound - self.lower_bound) * (
            strength / 100
        ) + self.lower_bound
        data[self.image_prompt_strength_name] = modified_strength
        return data


class OptimisePrompt(Handler):
    optimise_prompt_name: str = "optimise_prompt"
    true_value: Any = True
    false_value: Any = False

    def handle(self, data: dict, **kwargs) -> dict:
        if kwargs["optimise_prompt"]:
            data[self.optimise_prompt_name] = self.true_value
        else:
            data[self.optimise_prompt_name] = self.false_value
        return data


class OutputHandler(BaseModel):
    def fetch(self, response: Any) -> str:
        return response


class ListOutputHandler(OutputHandler):
    index: int = 0

    def fetch(self, response: Any) -> str:
        return response[self.index]


ideogram_v3_aspect_ratios = [
    "1:3",
    "3:1",
    "1:2",
    "2:1",
    "9:16",
    "16:9",
    "10:16",
    "16:10",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "1:1",
]


class BaseModelData(BaseModel):
    name: str
    prompt_name: str = "prompt"
    data: dict
    handlers: List[Handler]
    output_handler: OutputHandler = OutputHandler()
    instructions: str

    def generate_replicate_request(
        self,
        prompt: str,
        width: int,
        height: int,
        optimise_prompt: bool,
        image_prompt_url: Optional[str] = None,
        image_prompt_strength: Optional[int] = None,
        seed: Optional[int] = None,
    ):
        """
        Allowed kwargs:
        - width: int
        - height: int

        - image_prompt_url: str
        - image_prompt_strength: int [0, 100] Larger values mean more influence from the image prompt

        - optimise_prompt: bool
        """
        kwargs = {
            "width": width,
            "height": height,
            "image_prompt_url": image_prompt_url,
            "optimise_prompt": optimise_prompt,
            "image_prompt_strength": image_prompt_strength,
        }
        data = self.data.copy()
        for handler in self.handlers:
            data = handler.handle(data, **kwargs)
        data[self.prompt_name] = prompt
        if seed:
            data["seed"] = seed

        logger.info(f"Generated replicate request for {self.name} | {data}")

        return data

    def fetch_output(self, response: Any) -> str:
        return self.output_handler.fetch(response)


available_img_gen_models: Dict[str, BaseModelData] = {
    "flux-1.1-pro-ultra": BaseModelData(
        name="black-forest-labs/flux-1.1-pro-ultra",
        data={
            "raw": True,  # Generate less processed, more natural-looking images
            "output_format": "png",
            "safety_tolerance": 6,
        },
        handlers=[
            SeedDetails(
                seed_lower_bound=0,
                seed_upper_bound=1000000,
            ),
            AspectRatioDetails(
                aspect_ratio_options=[
                    "21:9",
                    "16:9",
                    "3:2",
                    "4:3",
                    "5:4",
                    "1:1",
                    "4:5",
                    "3:4",
                    "2:3",
                    "9:16",
                    "9:21",
                ],
            ),
            ImagePromptDetails(),
            ImagePromptStrength(lower_bound=0, upper_bound=1),
        ],
        instructions=flux_1_1_pro_ultra_instructions,
    ),
    "flux-1.1-pro": BaseModelData(
        name="black-forest-labs/flux-1.1-pro",
        data={
            "aspect_ratio": "custom",
            "output_format": "png",
            "output_quality": 100,
        },
        handlers=[
            SeedDetails(
                seed_lower_bound=0,
                seed_upper_bound=1000000,
            ),
            DirectWidthHeight(),
            ImagePromptDetails(),
            OptimisePrompt(optimise_prompt_name="prompt_upsampling"),
            HeightAndWidthRestrictor(
                height_upper_bound=1440,
                width_upper_bound=1440,
            ),
        ],
        instructions=flux_1_1_pro_instructions,
    ),
    "ideogram-v3-turbo": BaseModelData(
        name="ideogram-ai/ideogram-v3-turbo",
        data={"magic_prompt_option": "Auto", "style_type": "None"},
        instructions=ideogram_v2_instructions,
        handlers=[
            StyleReferenceImageListDetails(key="style_reference_images"),
            OptimisePrompt(
                optimise_prompt_name="magic_prompt_option",
                true_value="On",
                false_value="Off",
            ),
            SeedDetails(
                seed_lower_bound=0,
                seed_upper_bound=2147483647,
            ),
            AspectRatioDetails(
                aspect_ratio_options=ideogram_v3_aspect_ratios,
            ),
        ],
    ),
    "ideogram-v3-balanced": BaseModelData(
        name="ideogram-ai/ideogram-v3-balanced",
        data={"magic_prompt_option": "Auto", "style_type": "None"},
        instructions=ideogram_v2_instructions,
        handlers=[
            StyleReferenceImageListDetails(key="style_reference_images"),
            OptimisePrompt(
                optimise_prompt_name="magic_prompt_option",
                true_value="On",
                false_value="Off",
            ),
            SeedDetails(
                seed_lower_bound=0,
                seed_upper_bound=2147483647,
            ),
            AspectRatioDetails(
                aspect_ratio_options=ideogram_v3_aspect_ratios,
            ),
        ],
    ),
    "ideogram-v3-quality": BaseModelData(
        name="ideogram-ai/ideogram-v3-quality",
        data={"magic_prompt_option": "Auto", "style_type": "None"},
        instructions=ideogram_v2_instructions,
        handlers=[
            StyleReferenceImageListDetails(key="style_reference_images"),
            OptimisePrompt(
                optimise_prompt_name="magic_prompt_option",
                true_value="On",
                false_value="Off",
            ),
            SeedDetails(
                seed_lower_bound=0,
                seed_upper_bound=2147483647,
            ),
            AspectRatioDetails(
                aspect_ratio_options=ideogram_v3_aspect_ratios,
            ),
        ],
    ),
}


def fetch_model_data(model_name: str) -> BaseModelData:
    return available_img_gen_models[model_name]
