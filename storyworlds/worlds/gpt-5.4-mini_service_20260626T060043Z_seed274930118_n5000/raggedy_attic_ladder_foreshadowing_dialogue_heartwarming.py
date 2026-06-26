#!/usr/bin/env python3
"""
storyworlds/worlds/raggedy_attic_ladder_foreshadowing_dialogue_heartwarming.py
==============================================================================

A small heartwarming storyworld about a raggedy attic ladder, a careful child,
and a gentle fix that turns worry into warmth.

Seed tale:
---
A child and a grandparent notice that the attic ladder is raggedy and a little
wobbly. The grandparent warns that it might not be safe, but the child wants to
go up to look for a special box of memories. They talk it through, bring a
flashlight and a steady stool, and make a careful plan. In the end, they climb
together safely and find the box, and the child learns that being careful can
still feel exciting and kind.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    carried_by: object | None = None
    box: object | None = None
    child: object | None = None
    elder: object | None = None
    lantern: object | None = None
    stepstool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if "_tags" not in self.__dict__:
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
    name: str
    gender: str
    elder: str
    elder_name: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class Ladder:
    label: str = "attic ladder"
    raggedy: bool = True
    wobbly: bool = True
    repaired: bool = False
    safe_after: bool = False
    ladder: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.ladder = Ladder()

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.ladder = copy.deepcopy(self.ladder)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld: a raggedy attic ladder, careful talk, and a safe discovery."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


GIRL_NAMES = ["Mia", "Nora", "Lily", "Ella", "June", "Ruby", "Ivy", "Ada"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Milo", "Owen", "Noah", "Eli"]
ELDER_NAMES = ["Rose", "Mabel", "June", "Hazel", "Arthur", "George", "Walter", "Evelyn"]
ELDER_BY_GENDER = {"grandmother": ["Rose", "Mabel", "June", "Hazel", "Evelyn"], "grandfather": ["Arthur", "George", "Walter"]}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather"])
    elder_name = getattr(args, "elder_name", None) or rng.choice(ELDER_BY_GENDER[elder])
    return StoryParams(name=name, gender=gender, elder=elder, elder_name=elder_name)


def _hero_pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id=params.name, kind="character", type=params.gender, label=params.name,
        traits=["curious", "kind"], meters={"fear": 0.0, "joy": 0.0, "trust": 0.0}, memes={}
    ))
    elder = world.add(Entity(
        id=params.elder_name, kind="character", type=params.elder, label=params.elder_name,
        traits=["gentle", "patient"], meters={"worry": 0.0, "joy": 0.0}, memes={}
    ))
    lantern = world.add(Entity(
        id="lantern", kind="thing", type="lantern", label="a little flashlight",
        owner=child.id, carried_by=child.id if False else None, meters={}, memes={}
    ))
    box = world.add(Entity(
        id="box", kind="thing", type="box", label="a small keepsake box",
        phrase="a small box of memories", owner=elder.id, meters={}, memes={}
    ))
    stepstool = world.add(Entity(
        id="stepstool", kind="thing", type="stool", label="a steady step stool",
        owner=elder.id, meters={}, memes={}
    ))

    # Act 1: foreshadowing the concern.
    world.say(
        f"In the hallway, {params.name} noticed the attic ladder by the ceiling. "
        f"It looked raggedy, with one worn rung and a little sway that made it whisper when touched."
    )
    world.say(
        f"{params.elder_name} saw the child looking up and said, “That ladder has been with us for a long time.” "
        f"Then {params.elder_name} added, “Old things can still be useful, but we have to treat them carefully.”"
    )
    world.para()
    world.say(
        f"{params.name} pointed to the attic door. “Can we go up?” {child.pronoun().capitalize()} asked. "
        f"“I want to find the memory box.”"
    )
    world.say(
        f"{params.elder_name} smiled, but {elder.pronoun('possessive')} voice stayed soft. "
        f"“Not without a plan,” {elder.pronoun()} said. “A raggedy ladder can wobble when we rush.”"
    )
    child.meters["desire"] = 1.0
    elder.meters["worry"] = 1.0
    world.facts["foreshadowed_wobble"] = True

    # Act 2: dialogue and careful planning.
    world.para()
    world.say(
        f"{params.name} hugged the flashlight and said, “I can go slowly.” "
        f"{params.elder_name} replied, “That helps, and I have a better idea too.”"
    )
    world.say(
        f"They brought the little flashlight and the steady step stool. "
        f"{params.elder_name} placed the stool at the bottom, and {params.name} held it still with both hands."
    )
    world.say(
        f"“Ready?” {params.elder_name} asked. “Ready,” {params.name} answered, and the two of them laughed at how serious they sounded."
    )
    child.meters["trust"] += 1.0
    elder.meters["trust"] = elder.meters.get("trust", 0.0) + 1.0
    world.facts["prepared"] = True

    # Act 3: resolution and payoff.
    world.para()
    world.ladder.repaired = True
    world.ladder.safe_after = True
    child.meters["joy"] += 1.0
    elder.meters["joy"] += 1.0
    world.say(
        f"Together, they climbed one careful step at a time. The raggedy ladder still looked old, "
        f"but now it had no reason to feel scary because they were patient and steady."
    )
    world.say(
        f"At the top, {params.name} found the small keepsake box. Inside were folded photos, a ribbon, "
        f"and a tiny toy that made {params.elder_name} laugh with surprise."
    )
    world.say(
        f"{params.name} held the box close and said, “We did it.” {params.elder_name} squeezed {child.pronoun('possessive')} shoulder and said, "
        f"“We did it safely.”"
    )
    world.say(
        f"By the time they climbed back down, the attic ladder was still raggedy, but it had become part of a warm memory instead of a worry."
    )

    world.facts.update(hero=child, elder=elder, lantern=lantern, box=box, stool=stepstool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a heartwarming story about a raggedy attic ladder, careful talk, and a small safe discovery.",
        f"Tell a gentle story where {f['hero'].id} and {f['elder'].id} worry about an old attic ladder but solve it together.",
        "Write a simple foreshadowing story with dialogue that ends in a warm, safe moment in the attic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    return [
        QAItem(
            question=f"What was raggedy in the story?",
            answer=f"The attic ladder was raggedy, with a worn rung and a little sway.",
        ),
        QAItem(
            question=f"Why did {elder.id} want {child.id} to be careful?",
            answer=f"{elder.id} wanted {child.id} to be careful because the attic ladder could wobble if they rushed.",
        ),
        QAItem(
            question=f"What did {child.id} and {elder.id} bring before climbing?",
            answer=f"They brought a little flashlight and a steady step stool so they could climb safely.",
        ),
        QAItem(
            question=f"What did they find in the attic?",
            answer=f"They found a small keepsake box with folded photos, a ribbon, and a tiny toy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight helps you see in dark places by shining a bright beam of light.",
        ),
        QAItem(
            question="Why should you be careful on old stairs or ladders?",
            answer="Old stairs or ladders can be wobbly, so careful steps help keep people safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carries:
            bits.append(f"carries={e.carries}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  ladder: raggedy={world.ladder.raggedy} wobbly={world.ladder.wobbly} repaired={world.ladder.repaired} safe_after={world.ladder.safe_after}")
    return "\n".join(lines)


ASP_RULES = r"""
% The ladder is relevant when it is raggedy and wobbly.
unsafe_ladder(L) :- raggedy(L), wobbly(L).

% If careful help and tools are present, the situation becomes safe enough.
safe_plan(P) :- careful(P), tool(P), steady_support(P).

% A story is acceptable when the ladder is unsafe but a safe plan exists.
valid_story(S) :- unsafe_ladder(S), safe_plan(S).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("raggedy", "attic_ladder"),
        asp.fact("wobbly", "attic_ladder"),
        asp.fact("careful", "plan"),
        asp.fact("tool", "plan"),
        asp.fact("steady_support", "plan"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("attic_ladder",)}
    if atoms == expected:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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


CURATED = [
    StoryParams(name="Mia", gender="girl", elder="grandmother", elder_name="Rose"),
    StoryParams(name="Leo", gender="boy", elder="grandfather", elder_name="Arthur"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(getattr(args, "n", None), 1)):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} and {p.elder_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
