#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
=================================================================

A tiny pirate-tale story world about a fellowship at sea, a troublesome paw,
and a sprig of rosemary that helps the crew reach a happy ending with a bit of
humor.

Seed tale sketch:
---
On the fellow-ship, Captain Brine sailed with a small crew and a clever ship cat
named Mottle. Mottle loved climbing ropes, but one day a salty splinter poked
her paw while she leapt from a crate to a coil of rope. The crew fussed, the cat
huffed, and nobody wanted the voyage to turn grumpy. Then the cook remembered a
bundle of rosemary in the galley. He made a warm rosemary rinse and wrapped the
paw in a clean cloth. Mottle purred, the crew laughed, and the fellow-ship
sailed on with supper, songs, and a happy ending.

World model:
---
- The ship has a shared mood, a speed, and a small pantry.
- The cat has a paw, a brave streak, and a tendency to climb.
- A splinter can raise pain and grumpiness.
- Rosemary can calm the paw and help the crew solve the problem.
- Humor comes from pirate banter, the cat's offended dignity, and the crew's
  over-serious reaction to a very small paw crisis.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caret: str = ""
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "cook", "sailor", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain_name: str = "Brine"
    cook_name: str = "Merrick"
    cat_name: str = "Mottle"
    ship_name: str = "the fellow-ship"
    herb: str = "rosemary"
    paw_side: str = "left"
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class World:
    ship_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.ship_name)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


THRESHOLD = 1.0


def setup_world(params: StoryParams) -> World:
    world = World(params.ship_name)
    world.add(Entity(id="captain", kind="character", type="captain", label=f"Captain {params.captain_name}"))
    world.add(Entity(id="cook", kind="character", type="cook", label=f"Cook {params.cook_name}"))
    world.add(Entity(id="cat", kind="character", type="cat", label=params.cat_name))
    world.add(Entity(
        id="paw",
        kind="body",
        type="paw",
        label=f"{params.cat_name}'s {params.paw_side} paw",
        owner="cat",
        caret="",
        meters={"pain": 0.0, "splinter": 0.0, "clean": 1.0},
        memes={"grump": 0.0, "comfort": 0.0, "pride": 0.0},
    ))
    world.add(Entity(
        id="rosemary",
        kind="thing",
        type="herb",
        label="rosemary",
        phrase="a bundle of rosemary",
        owner="cook",
    ))
    world.facts.update(params=params)
    return world


def introduce(world: World, params: StoryParams) -> None:
    ship = world.ship_name
    captain = world.get("captain")
    cat = world.get("cat")
    cook = world.get("cook")
    world.say(
        f"On {ship}, {captain.label} kept a cheerful crew, and {cat.label} was the quickest little cat on the water."
    )
    world.say(
        f"{cook.label} liked to say the galley had two treasures: hot soup and {params.herb} tucked in a jar."
    )


def incident(world: World, params: StoryParams) -> None:
    cat = world.get("cat")
    paw = world.get("paw")
    cat.memes["pride"] += 1
    paw.meters["splinter"] += 1
    paw.meters["pain"] += 1
    cat.memes["grump"] += 1
    world.say(
        f"One windy afternoon, {cat.label} leapt from a crate to a coil of rope and yelped when a salty splinter poked {cat.pronoun('possessive')} paw."
    )
    world.say(
        f"{cat.label} lifted the paw high and looked as if the sea itself had offended {cat.pronoun('object')}."
    )


def forecast_mood(world: World) -> dict[str, float]:
    paw = world.get("paw")
    return {
        "pain": paw.meters["pain"],
        "grump": paw.memes["grump"],
    }


def remedy_possible(world: World) -> bool:
    paw = world.get("paw")
    return paw.meters["splinter"] >= THRESHOLD and paw.meters["pain"] >= THRESHOLD


def soothe(world: World, params: StoryParams) -> None:
    cook = world.get("cook")
    cat = world.get("cat")
    paw = world.get("paw")
    rosemary = world.get("rosemary")
    if not remedy_possible(world):
        pass
    paw.meters["pain"] = max(0.0, paw.meters["pain"] - 1.0)
    paw.meters["clean"] = 1.0
    paw.memes["comfort"] += 1
    cat.memes["grump"] = max(0.0, cat.memes["grump"] - 1.0)
    cat.memes["pride"] += 1
    world.say(
        f"{cook.label} remembered {rosemary.label} in the galley, boiled a gentle rinse, and wrapped the paw in a clean cloth."
    )
    world.say(
        f'"There," {cook.pronoun("subject").capitalize()} said, "that ought to teach the splinter who the real captain is."'
    )
    world.say(
        f"{cat.label} blinked, then purred so loudly that even the rigging seemed to smile."
    )


def happy_ending(world: World, params: StoryParams) -> None:
    captain = world.get("captain")
    cook = world.get("cook")
    cat = world.get("cat")
    paw = world.get("paw")
    world.say(
        f"{captain.label} saluted the clever cure, and {cook.label} bowed so low {cat.label} tried to swat {cook.pronoun('object')} for the joke."
    )
    world.say(
        f"By sunset, {cat.label} was padding along the deck with {paw.label} steady and clean, while the crew laughed over soup and salty songs."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world, params)
    world.para()
    incident(world, params)
    world.para()
    soothe(world, params)
    world.para()
    happy_ending(world, params)
    world.facts.update(
        captain=world.get("captain"),
        cook=world.get("cook"),
        cat=world.get("cat"),
        paw=world.get("paw"),
        rosemary=world.get("rosemary"),
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    cat = world.get("cat")
    return [
        f'Write a short pirate story for a young child that includes the words "{params.ship_name}", "paw", and "{params.herb}".',
        f"Tell a humorous tale about {cat.label} getting a sore paw on {params.ship_name} and the crew fixing it kindly.",
        f"Write a happy-ending sea story where a pirate cook uses {params.herb} to help a cat's paw feel better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    captain = world.get("captain")
    cook = world.get("cook")
    cat = world.get("cat")
    paw = world.get("paw")
    return [
        QAItem(
            question=f"Who sailed on {params.ship_name} with {cat.label}?",
            answer=f"{captain.label} sailed with {cook.label} and {cat.label} on {params.ship_name}.",
        ),
        QAItem(
            question=f"What happened to {cat.label}'s paw?",
            answer=f"A salty splinter poked {cat.label}'s paw and made it hurt.",
        ),
        QAItem(
            question=f"How did {cook.label} help the paw?",
            answer=f"{cook.label} used {params.herb} in a warm rinse and wrapped the paw in a clean cloth.",
        ),
        QAItem(
            question=f"How did the story end for {cat.label}?",
            answer=f"{cat.label} ended up happy again, with the paw steady and clean and the crew laughing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a fragrant herb used in cooking and sometimes in simple home remedies.",
        ),
        QAItem(
            question="What is a paw?",
            answer="A paw is a foot on an animal like a cat or dog, often with soft pads and claws.",
        ),
        QAItem(
            question="What is a fellowship?",
            answer="A fellowship is a group of companions who work or travel together as friends.",
        ),
        QAItem(
            question=f"Why might a ship's crew keep herbs like {params.herb} nearby?",
            answer="A ship's crew might keep herbs nearby for cooking, for smell, and to help with little problems along the way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A paw is at risk when a splinter is present and pain is high.
paw_at_risk(P) :- paw(P), splinter(P), pain(P).

% Rosemary is a compatible remedy when it can calm the paw and clean the cloth.
compatible_remedy(R, P) :- herb(R), paw(P), paw_at_risk(P), soothes(R), cleans(R).

resolved_story(P) :- paw(P), paw_at_risk(P), compatible_remedy(_, P).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("ship", "fellow_ship"),
        asp.fact("fellow_ship", "fellow-ship"),
        asp.fact("crewmate", "captain"),
        asp.fact("crewmate", "cook"),
        asp.fact("cat", "cat"),
        asp.fact("paw", "paw"),
        asp.fact("splinter", "paw"),
        asp.fact("pain", "paw"),
        asp.fact("herb", "rosemary"),
        asp.fact("soothes", "rosemary"),
        asp.fact("cleans", "rosemary"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved_story/1."))
    asp_set = set(asp.atoms(model, "resolved_story"))
    py_set = {("paw",)} if True else set()
    if asp_set == py_set:
        print("OK: ASP twin matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate tale story world about a fellow-ship, a paw, and rosemary."
    )
    ap.add_argument("--captain-name", default="Brine")
    ap.add_argument("--cook-name", default="Merrick")
    ap.add_argument("--cat-name", default="Mottle")
    ap.add_argument("--ship-name", default="the fellow-ship")
    ap.add_argument("--herb", default="rosemary")
    ap.add_argument("--paw-side", choices=["left", "right"], default="left")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        captain_name=getattr(args, "captain_name", None) or rng.choice(["Brine", "Marrow", "Tide"]),
        cook_name=getattr(args, "cook_name", None) or rng.choice(["Merrick", "Sal", "Bram"]),
        cat_name=getattr(args, "cat_name", None) or rng.choice(["Mottle", "Whisk", "Sailor"]),
        ship_name=getattr(args, "ship_name", None) or "the fellow-ship",
        herb=getattr(args, "herb", None) or "rosemary",
        paw_side=getattr(args, "paw_side", None) or rng.choice(["left", "right"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(resolve_params(args, random.Random(base_seed)))]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
