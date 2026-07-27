"""Port for multimodal (image) analysis of meal photos.

Concrete adapters live in `app.infrastructure.ai.vision`. Keeping this separate
from `LLMPort` matters: text generation is used by several use cases, while
vision is a distinct capability with its own provider, model and failure modes.
"""

from abc import ABC, abstractmethod

from app.domain.entities.estimated_food import EstimatedFood


class VisionUnavailableError(RuntimeError):
    """The vision provider could not be reached (outage, quota, bad key).

    Same contract as `EmbeddingUnavailableError`: adapters raise this instead of
    leaking transport errors, so a provider hiccup becomes a handled response
    rather than a 500.
    """


class VisionPort(ABC):
    """Extracts the foods visible in a meal photo, with estimated portions."""

    @abstractmethod
    async def analyze_meal(self, image: bytes, mime_type: str) -> list[EstimatedFood]:
        """Return the foods recognised in the image (empty if there is no food).

        The image is untrusted input: adapters must treat any text inside it as
        data, never as instructions.
        """
