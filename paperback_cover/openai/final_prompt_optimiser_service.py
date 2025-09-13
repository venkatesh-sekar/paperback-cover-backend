import logging
from typing import Optional

from pydantic import BaseModel

from paperback_cover.openai.openai_client import OpenAiClient

logger = logging.getLogger(__name__)

INSTRUCTION = """Objective:
Analyze the given prompt and optimize it to generate a high-quality, genre-specific book cover artwork. Assume the role of a professional book cover designer, ensuring the final output aligns with industry standards.

Key Guidelines:

Generate Only Artwork
- Ignore all text elements (titles, author names, taglines, etc.).

Enhance Genre Accuracy
Adjust details to align with the conventions of the specified genre/sub-genre if provided.
- Modify lighting, color scheme, and composition to enhance thematic consistency only if necessary.
- Improve Thumbnail Readability

The output should be a single paragraph (under 250 words). No fluff or details that are not directly related to the visual aspects of the artwork.
- It should describe the scene, style, lighting, and key elements.
- Exclude Redundant Instructions
- Keep the language simple 
- Title, author name, and other text elements should not be included in the description unless it's a part of the artwork.
    
Sometimes the prompt might contain elements that might not be in the vocabulary of the model. In such cases, you can try to explain the element or mood.
- Eg: If the prompt contains "martian landscape", you can add a sentence like "desert landscape, barren, red terrain with craters and rocks"    
    
Expected Output:
- A single cohesive paragraph describing the artwork.
- Strong genre-appropriate style, texture, mood, and lighting (Change only if necessary).
- Optimized for clarity and impact at all sizes.

The user will also pass instructions for each prompt, which is very important and must be followed for the final output to be correct. The instructions will be in the following format:
::: MODEL INSTRUCTIONS START :::
<INSTRUCTIONS>
::: MODEL INSTRUCTIONS END :::

Use the instructions to only change the syntax and format. Only if the model requires detailed information and the instructions are not detailed, you can add more details to the prompt.
"""


class OpenAiPromptOptimiserOutput(BaseModel):
    optimised_prompt: str


class FinalPromptOptimiserService:
    client: OpenAiClient
    name = "Final prompt optimiser assistant"

    def __init__(self, openai_client: OpenAiClient):
        self.client = openai_client
        # Previously, an assistant was created or updated.
        # When using chat completions we no longer need to manage a separate assistant.

    async def optimise_prompt(
        self, prompt: str, instructions: str
    ) -> Optional[OpenAiPromptOptimiserOutput]:
        # Use chat completions API with a system and a user message
        logger.info(f"Optimising prompt: {prompt}")
        completion = await self.client.get_client().beta.chat.completions.parse(
            extra_body={"provider": {"require_parameters": True}},
            model="google/gemini-2.5-pro-preview-03-25",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{INSTRUCTION}"
                        "::: MODEL INSTRUCTIONS START :::"
                        f"{instructions}"
                        "::: MODEL INSTRUCTIONS END :::"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format=OpenAiPromptOptimiserOutput,
        )
        message = completion.choices[0].message

        if message.parsed:
            logger.info(
                f"Successfully optimised prompt: {message.parsed.optimised_prompt}"
            )
            return message.parsed
        else:
            logger.error("Failed to optimise prompt via chat completions")
            return None

    async def basic_optimisation(
        self, prompt: str
    ) -> Optional[OpenAiPromptOptimiserOutput]:
        # Use chat completions API with a system and a user message
        logger.info(f"Optimising prompt: {prompt}")
        completion = await self.client.get_client().beta.chat.completions.parse(
            extra_body={"provider": {"require_parameters": True}},
            model="meta-llama/llama-3.2-3b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        """
                        Fix grammatical mistakes, punctuation.
                        Do not change the meaning of the prompt. Do not add/remove any text to the prompt.
                        Do not change any text inside of quotes/brackets/curly braces.
                        Do not add any other text to the prompt. Just respond back with the optimised prompt. Do not add any prefix or suffix to the prompt.
                        """
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        message = completion.choices[0].message

        if message.content:
            logger.info(f"Successfully optimised prompt: {message.content}")
            return OpenAiPromptOptimiserOutput(optimised_prompt=message.content)
        else:
            logger.error("Failed to optimise prompt via chat completions")
            return None
