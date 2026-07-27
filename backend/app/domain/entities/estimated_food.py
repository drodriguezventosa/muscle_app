"""A food estimated from a meal photo (not a catalog entry)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EstimatedFood:
    """One food recognised in a photo, with macros for the estimated portion.

    Unlike `Food` (catalog, values per 100 g), the macros here are the TOTAL for
    `grams`, because that is what a vision model can estimate about a plate. The
    caller converts to per-100 g if it needs to rescale.
    """

    name: str
    grams: float
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
