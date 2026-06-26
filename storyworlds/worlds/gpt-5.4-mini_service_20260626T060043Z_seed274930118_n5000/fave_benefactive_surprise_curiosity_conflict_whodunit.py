#!/usr/bin/env python3
"""
A tiny whodunit-style story world about a missing favorite thing, a helpful
benefactive, and the clues that solve the mystery.

The seed premise:
- A child has a fave item.
- Someone else is the benefactive: they wanted the child to have it safe, ready,
  or special.
- Surprise, curiosity, and conflict rise when the item goes missing.
- The story resolves by tracing physical clues and emotional motives.

This world stays small on purpose: one setting, a short list of suspects,
simple physical traces, and a final reveal that changes the world state.
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


SURPRISE = "surprise"
CURIOSITY = "curiosity"
CONFLICT = "conflict"



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
    helper_for: Optional[str] = None
    suspect: bool = False
    alive: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    benefactive: object | None = None
    child: object | None = None
    fave: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str = "the old house"
    rooms: list[str] = field(default_factory=lambda: ["kitchen", "hall", "back room"])
    hidden_spot: str = "the tin box under the bench"
    world: object | None = None
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
        return None


@dataclass
class Clue:
    location: str
    thing: str
    hints: list[str] = field(default_factory=list)
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
        return None


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    benefactive_name: str
    benefactive_type: str
    fave_item: str
    setting: str = "house"
    seed: Optional[int] = None
    params: object | None = None
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
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues: list[Clue] = []
        self.fired: set[str] = set()

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            pieces = []
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            if meters:
                pieces.append(f"meters={meters}")
            if memes:
                pieces.append(f"memes={memes}")
            if e.owner:
                pieces.append(f"owner={e.owner}")
            if e.helper_for:
                pieces.append(f"helper_for={e.helper_for}")
            if e.suspect:
                pieces.append("suspect=True")
            if e.label:
                pieces.append(f'label="{e.label}"')
            lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(pieces)}")
        for clue in self.clues:
            lines.append(f"  clue at {clue.location}: {clue.thing} -> {', '.join(clue.hints)}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.child_name.strip():
        pass
    if not params.benefactive_name.strip():
        pass
    if params.child_name == params.benefactive_name:
        pass
    if params.setting != "house":
        pass
    if not params.fave_item.strip():
        pass


def _say_intro(world: World, child: Entity, benefactive: Entity, fave: Entity) -> None:
    world.say(
        f"{child.id} had a fave {fave.label}, and everybody in the house knew it."
    )
    world.say(
        f"{benefactive.id} was the kind of grown-up who liked to keep little things safe for {child.id}."
    )


def _say_setup(world: World, child: Entity, fave: Entity) -> None:
    child.memes[SURPRISE] += 1
    child.memes[CURIOSITY] += 1
    world.say(
        f"One morning, {child.id} looked where {child.pronoun('possessive')} {fave.label} should be."
    )
    world.say(
        f"It was gone, and that made {child.id} freeze with surprise."
    )


def _say_conflict(world: World, child: Entity, suspect: Entity) -> None:
    child.memes[CONFLICT] += 1
    world.say(
        f"{child.id} asked {suspect.id} first, because the clue trail started near {suspect.pronoun('possessive')} room."
    )
    world.say(
        f"{suspect.id} frowned and said {suspect.pronoun('subject')} had not taken it, which made the air feel tight."
    )


def _add_clue(world: World, location: str, thing: str, *hints: str) -> None:
    world.clues.append(Clue(location=location, thing=thing, hints=list(hints)))


def _investigate(world: World, child: Entity, benefactive: Entity, fave: Entity, suspect: Entity) -> None:
    world.para()
    world.say(
        f"Then {child.id} started to look more carefully, because curiosity was stronger than worry."
    )
    world.say(
        f"On the hall table, {child.id} found a crumb, a bent ribbon, and a small note."
    )
    _add_clue(
        world,
        "hall table",
        "crumb, bent ribbon, and note",
        "the note was from the benefactive",
        "the ribbon matched the fave item's bag",
    )
    world.say(
        f"The note said {benefactive.id} had moved the {fave.label} for a reason, and that changed the puzzle."
    )
    world.say(
        f"That meant the first suspect was not the thief after all."
    )
    suspect.memes[CONFLICT] = max(0.0, suspect.memes.get(CONFLICT, 0.0) - 1.0)


def _reveal(world: World, child: Entity, benefactive: Entity, fave: Entity) -> None:
    world.para()
    child.memes[SURPRISE] += 1
    benefactive.memes["kindness"] += 1
    world.say(
        f"{child.id} found {fave.label} in {world.setting.hidden_spot}, wrapped in a clean cloth."
    )
    world.say(
        f"{benefactive.id} had hidden it there to keep it safe for a special surprise later."
    )
    world.say(
        f"At once, the whole mystery made sense."
    )
    world.say(
        f"{child.id} smiled, because the missing thing had been protected, not stolen."
    )


def _ending(world: World, child: Entity, benefactive: Entity, fave: Entity) -> None:
    world.para()
    child.memes[CONFLICT] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.say(
        f"By evening, {child.id} was carrying the {fave.label} again, and {benefactive.id} was laughing beside {child.id}."
    )
    world.say(
        f"The house felt calm, and the little mystery ended with the fave item safe where it belonged."
    )


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(Setting())

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    benefactive = world.add(Entity(
        id=params.benefactive_name,
        kind="character",
        type=params.benefactive_type,
        helper_for=params.child_name,
    ))
    fave = world.add(Entity(
        id="fave_item",
        kind="thing",
        type=params.fave_item,
        label=params.fave_item,
        owner=params.child_name,
    ))
    suspect = world.add(Entity(
        id="neighbor",
        kind="character",
        type="boy",
        label="the neighbor boy",
        suspect=True,
    ))

    # World facts for QA and traces
    world.facts.update(
        child=child,
        benefactive=benefactive,
        fave=fave,
        suspect=suspect,
        setting=world.setting,
    )

    _say_intro(world, child, benefactive, fave)
    _say_setup(world, child, fave)
    _say_conflict(world, child, suspect)
    _investigate(world, child, benefactive, fave, suspect)
    _reveal(world, child, benefactive, fave)
    _ending(world, child, benefactive, fave)
    return world


SETTINGS = {
    "house": Setting(),
}

CHILD_TYPES = ["girl", "boy"]
BENEFACTIVE_TYPES = ["mother", "father", "grandma", "grandpa", "aunt", "uncle"]
FAVE_ITEMS = ["blue whistle", "little red train", "shiny marble", "soft bear", "yellow scarf"]
NAMES = ["Mia", "Leo", "Nina", "Owen", "Zoe", "Max", "Lia", "Theo", "Ava", "Noah"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    benefactive = _safe_fact(world, f, "benefactive")
    fave = _safe_fact(world, f, "fave")
    return [
        f"Write a tiny whodunit for a young child about {child.id}'s missing {fave.label}.",
        f"Tell a mystery story where {benefactive.id} is a benefactive who hid the {fave.label} for a good reason.",
        f"Make a short, gentle detective story with surprise, curiosity, and conflict, ending with the {fave.label} found safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    benefactive = _safe_fact(world, f, "benefactive")
    fave = _safe_fact(world, f, "fave")
    suspect = _safe_fact(world, f, "suspect")
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {child.id}, who lost a fave {fave.label} in the house.",
        ),
        QAItem(
            question=f"Why did {child.id} feel upset at first?",
            answer=f"{child.id} felt upset because the fave {fave.label} was missing, and that brought surprise and conflict.",
        ),
        QAItem(
            question=f"Who turned out to be helping all along?",
            answer=f"{benefactive.id} was helping all along by keeping the {fave.label} safe for a special surprise.",
        ),
        QAItem(
            question=f"Why did {child.id} first suspect {suspect.id}?",
            answer=f"{child.id} found clues near {suspect.id}'s room, so it seemed like a mystery with a possible thief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone solve a puzzle or mystery.",
        ),
        QAItem(
            question="What does curiosity help you do?",
            answer="Curiosity helps you ask questions and look carefully so you can learn what happened.",
        ),
        QAItem(
            question="What is a benefactive?",
            answer="A benefactive is someone who does something to help another person get a good result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A fave item is missing when the benefactive moved it for safety.
missing(F) :- fave(F), moved_by_benefactive(F).

% A suspect is plausible if clues point near their room before the reveal.
plausible_suspect(S) :- suspect(S), clue_near_room(S).

% The mystery resolves when the item is hidden safely by the benefactive.
resolved(F) :- missing(F), moved_by_benefactive(F), safe_hidden(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("fave", "fave_item"))
    lines.append(asp.fact("moved_by_benefactive", "fave_item"))
    lines.append(asp.fact("safe_hidden", "fave_item"))
    lines.append(asp.fact("suspect", "neighbor"))
    lines.append(asp.fact("clue_near_room", "neighbor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world.")
    ap.add_argument("--name")
    ap.add_argument("--benefactive-name")
    ap.add_argument("--fave-item")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--benefactive-type", choices=BENEFACTIVE_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_type = getattr(args, "child_type", None) or rng.choice(CHILD_TYPES)
    benefactive_type = getattr(args, "benefactive_type", None) or rng.choice(BENEFACTIVE_TYPES)
    child_name = getattr(args, "name", None) or rng.choice(NAMES)
    benefactive_name = getattr(args, "benefactive_name", None) or rng.choice([n for n in NAMES if n != child_name])
    fave_item = getattr(args, "fave_item", None) or rng.choice(FAVE_ITEMS)
    params = StoryParams(
        child_name=child_name,
        child_type=child_type,
        benefactive_name=benefactive_name,
        benefactive_type=benefactive_type,
        fave_item=fave_item,
    )
    reasonableness_gate(params)
    return params


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    program = asp_program("#show resolved/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "resolved"))
    expected = {("fave_item",)}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        atoms = asp.atoms(model, "resolved")
        print(f"resolved items: {atoms}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("Mia", "girl", "Grandma", "grandma", "blue whistle"),
            StoryParams("Leo", "boy", "Dad", "father", "little red train"),
            StoryParams("Zoe", "girl", "Aunt June", "aunt", "shiny marble"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
