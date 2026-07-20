"""Food domain entity. Macros are per 100 g."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Food:
    id: int
    name: str
    category: str  # key: protein | carb | vegetable | fruit | dairy | fat | other
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    tags: tuple[str, ...] = field(default_factory=tuple)  # DietTag values
