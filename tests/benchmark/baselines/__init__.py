"""Retrieval baselines for benchmark evaluation."""

from abc import ABC, abstractmethod

from hcr_core.types.corpus import Chunk


class RetrievalBaseline(ABC):
    """Abstract base class for retrieval baselines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this baseline for reporting."""

    @abstractmethod
    def retrieve(self, query: str, token_budget: int) -> list[Chunk]:
        """Retrieve chunks for a query within the given token budget."""
