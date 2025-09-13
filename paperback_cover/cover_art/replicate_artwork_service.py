from typing import Any, Literal, Optional

from fastapi import Depends

from paperback_cover.cover_art.img_models import BaseModelData
from paperback_cover.cover_art.schema import OcrResult
from paperback_cover.replicate.replicateclient import (
    ReplicateClient,
    get_replicate_client,
)


class ReplicateArtworkService:
    replicate_client: ReplicateClient

    def __init__(self, replicate_client: ReplicateClient):
        self.replicate_client = replicate_client

    async def generate_using_model(
        self,
        base_model_data: BaseModelData,
        prompt: str,
        width: int,
        height: int,
        optimise_prompt: bool,
        image_prompt_url: Optional[str] = None,
        image_prompt_strength: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> str:
        resp = await self.replicate_client.get_client().async_run(
            base_model_data.name,
            input=base_model_data.generate_replicate_request(
                prompt=prompt,
                width=width,
                height=height,
                optimise_prompt=optimise_prompt,
                image_prompt_url=image_prompt_url,
                image_prompt_strength=image_prompt_strength,
                seed=seed,
            ),
        )
        return base_model_data.fetch_output(resp)

    async def generate_using_flux(
        self,
        prompt: str,
        width: int,
        height: int,
        steps: int = 25,
        guidance: float = 3,
        interval: float = 2,
        safety_tolerance: int = 2,
        seed: int = 0,
        output_format: str = "png",
        prompt_upsampling: bool = False,
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            "black-forest-labs/flux-1.1-pro",
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "guidance": guidance,
                "interval": interval,
                "safety_tolerance": safety_tolerance,
                "seed": seed,
                "output_format": output_format,
                "prompt_upsampling": prompt_upsampling,
                "aspect_ratio": "custom",
            },
        )
        return image_link

    async def inpaint_image_using_flux(
        self,
        image_url: str,
        mask_url: str,
        steps: int = 50,
        guidance: float = 80,
        safety_tolerance: int = 6,
        prompt: str = "extend background",
        prompt_upsampling: bool = False,
        seed: int = 0,
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            "black-forest-labs/flux-fill-pro",
            input={
                "prompt": prompt,
                "image": image_url,
                "mask": mask_url,
                "steps": steps,
                "guidance": guidance,
                "safety_tolerance": safety_tolerance,
                "output_format": "png",
                "prompt_upsampling": prompt_upsampling,
                "seed": seed,
            },
        )
        return image_link

    async def inpaint_image_using_ideogram(
        self,
        image_url: str,
        mask_url: str,
        model: str = "ideogram-v3-turbo",
        prompt: str = "extend background",
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            f"ideogram-ai/{model}",
            input={
                "prompt": prompt,
                "image": image_url,
                "mask": mask_url,
            },
        )
        return image_link

    # https://replicate.com/ideogram-ai/ideogram-v2
    async def generate_image_using_ideogram(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        magic_prompt_option: str = "Auto",
        style_type: str = "None",
        inpainting_image_url: Optional[str] = None,
        mask_image_url: Optional[str] = None,
        seed: int = 0,
    ) -> str:
        request = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "magic_prompt_option": magic_prompt_option,
            "style_type": style_type,
            "seed": seed,
        }

        if inpainting_image_url:
            if mask_image_url:
                request["image"] = inpainting_image_url
                request["mask"] = mask_image_url
            else:
                raise ValueError(
                    "Mask URL is required when providing an inpainting image"
                )

        image_link: Any = await self.replicate_client.get_client().async_run(
            "ideogram-ai/ideogram-v2", input=request
        )
        return image_link

    async def remove_bg(
        self,
        image_url: str,
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            "men1scus/birefnet:f74986db0355b58403ed20963af156525e2891ea3c2d499bfbfb2a28cd87c5d7",
            input={"image": image_url},
        )
        return image_link

    async def variate_image_using_flux(
        self,
        prompt: str,
        control_image_url: str,
        seed: int = 0,
        steps: int = 50,
        guidance: int = 30,
        output_format: str = "png",
        prompt_upsampling: bool = False,
        safety_tolerance: int = 6,
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            "black-forest-labs/flux-canny-pro",
            input={
                "prompt": prompt,
                "control_image": control_image_url,
                "steps": steps,
                "guidance": guidance,
                "safety_tolerance": safety_tolerance,
                "seed": seed,
                "output_format": output_format,
                "prompt_upsampling": prompt_upsampling,
            },
        )
        return image_link

    async def faceswap_single_face(
        self,
        target_image_url: str,
        source_face_image_url: str,
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            "codeplugtech/face-swap:278a81e7ebb22db98bcba54de985d22cc1abeead2754eb1f2af717247be69b34",
            input={
                "swap_image": source_face_image_url,
                "input_image": target_image_url,
            },
        )
        return image_link

    async def image_edit_using_flux(
        self,
        prompt: str,
        input_image_url: str,
        seed: int = 0,
        model: Literal["pro", "max"] = "pro",
        aspect_ratio: str = "match_input_image",
    ) -> str:
        model_name = (
            "black-forest-labs/flux-kontext-pro"
            if model == "pro"
            else "black-forest-labs/flux-kontext-max"
        )
        image_link: Any = await self.replicate_client.get_client().async_run(
            model_name,
            input={
                "prompt": prompt,
                "input_image": input_image_url,
                "seed": seed,
                "aspect_ratio": aspect_ratio,
            },
        )
        return image_link

    async def remove_object_using_mask(
        self,
        input_image_url: str,
        mask_image_url: str,
    ) -> str:
        image_link: Any = await self.replicate_client.get_client().async_run(
            "zylim0702/remove-object:0e3a841c913f597c1e4c321560aa69e2bc1f15c65f8c366caafc379240efd8ba",
            input={
                "image": input_image_url,
                "mask": mask_image_url,
            },
        )
        return image_link

    async def upscale_image_with_creativity_control(
        self,
        input_image_url: str,
        seed: int = 0,
        resemblance: float = 80,
    ) -> str:
        assert 0 <= resemblance <= 100, "resemblance must be between 0 and 100"
        creativity = 100 - resemblance

        act_resemblance = (1.6 - 0.3) * (resemblance / 100) + 0.3
        act_creativity = (0.4 - 0.1) * (creativity / 100) + 0.1

        image_link: Any = await self.replicate_client.get_client().async_run(
            "philz1337x/clarity-upscaler:dfad41707589d68ecdccd1dfa600d55a208f9310748e44bfe35b4a6291453d5e",
            input={
                "seed": seed,
                "image": input_image_url,
                "prompt": "masterpiece, best quality, highres, <lora:more_details:0.5> <lora:SDXLrender_v2.0:1>",
                "dynamic": 6,
                "handfix": "disabled",
                "pattern": False,
                "sharpen": 0,
                "sd_model": "juggernaut_reborn.safetensors [338b85bc4f]",
                "scheduler": "DPM++ 3M SDE Karras",
                "creativity": act_creativity,
                "lora_links": "",
                "downscaling": False,
                "resemblance": act_resemblance,
                "scale_factor": 2,
                "tiling_width": 112,
                "output_format": "png",
                "tiling_height": 144,
                "custom_sd_model": "",
                "negative_prompt": "(worst quality, low quality, normal quality:2) JuggernautNegative-neg",
                "num_inference_steps": 18,
                "downscaling_resolution": 768,
            },
        )
        return image_link[0]

    async def detect_text_with_region(self, image_url: str) -> OcrResult:
        ocr_with_region: Any = await self.replicate_client.get_client().async_run(
            "lucataco/florence-2-large:da53547e17d45b9cfb48174b2f18af8b83ca020fa76db62136bf9c6616762595",
            input={
                "image": image_url,
                "task_input": "OCR with Region",
            },
        )
        return OcrResult.from_replicate_json(ocr_with_region)


def get_replicate_artwork_service(
    replicate_client: ReplicateClient = Depends(get_replicate_client),
) -> ReplicateArtworkService:
    return ReplicateArtworkService(
        replicate_client=replicate_client,
    )
