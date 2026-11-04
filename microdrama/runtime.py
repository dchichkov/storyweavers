"""Public API for deterministic generation and portable evidence bundles."""
from dataclasses import asdict, dataclass
from pathlib import Path

from .engine import compose, digest
from .palace import Parameters, build_world, library
from .prose import narrate


@dataclass
class Story:
    params: Parameters
    seed: int
    world: object
    episodes: list
    choices: list
    paragraphs: list

    @property
    def text(self):
        return "The Palace That Learned to Read\n\n" + "\n\n".join(p.text for p in self.paragraphs) + "\n"

    def bundle(self):
        from .qa import questions
        source = {p.name: p.read_text() for p in sorted(Path(__file__).parent.glob("*.py"))}
        return {"format": "microdrama-1", "source_hash": digest(source),
                "parameters": asdict(self.params), "seed": self.seed,
                "outcome": self.world.state["palace.outcome"],
                "initial": self.world.initial, "final": self.world.state,
                "entities": self.world.entities,
                "events": [asdict(e) for e in self.world.history],
                "choices": self.choices,
                "paragraphs": [asdict(p) for p in self.paragraphs],
                "qa": [asdict(a) for a in questions(self)]}


def generate(params=None, seed=0):
    params = params or Parameters()
    world = build_world(params)
    episodes, choices = compose(world, library(params), params, seed)
    return Story(params, seed, world, episodes, choices, narrate(episodes, params))
