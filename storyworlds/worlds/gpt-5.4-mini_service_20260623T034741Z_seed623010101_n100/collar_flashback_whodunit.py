#!/usr/bin/env python3
"""
storyworlds/worlds/collar_flashback_whodunit.py
==============================================

A small storyworld for a child-friendly whodunit with a flashback beat.

Premise:
- A family pet's collar goes missing.
- The children and a grown-up search a few likely places.
- A flashback reveals who moved the collar and why.
- The mystery resolves with a concrete ending image that proves the change.

The world model uses physical meters and emotional memes:
- meters: location, hiddenness, dust, dampness, foundness
- memes: worry, curiosity, relief, suspicion, memory

The story is deliberately compact, but state-driven:
- clues alter suspicion
- searching changes location/hiddenness
- the flashback changes the meaning of the clues
- the ending proves the collar is back where it belongs
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


@dataclass
class Place:
    id: str
    label: str
    kind: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Clue:
    id: str
    label: str
    place: str
    weight: float = 1.0
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str = "kitchen"
    mystery: str = "collar"
    culprit: str = "dog"
    name: str = "Mina"
    sibling: str = "Owen"
    parent: str = "mother"
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "kitchen": Place("kitchen", "the kitchen", "indoors", {"inside", "table", "drawer"}),
    "hall": Place("hall", "the hall", "indoors", {"inside", "hook", "bench"}),
    "garden": Place("garden", "the garden", "outdoors", {"outside", "bush", "bench"}),
    "laundry": Place("laundry", "the laundry room", "indoors", {"inside", "basket", "basket_hole"}),
}

COLLARS = {
    "red": Clue("red", "a red collar", "hook", 1.0, {"collar", "red"}),
    "blue": Clue("blue", "a blue collar", "bench", 1.0, {"collar", "blue"}),
    "green": Clue("green", "a green collar", "drawer", 1.0, {"collar", "green"}),
}

CULES = ["dog", "cat", "rabbit"]

CURATED = [
    StoryParams(setting="kitchen", mystery="collar", culprit="dog", name="Mina", sibling="Owen", parent="mother"),
    StoryParams(setting="hall", mystery="collar", culprit="cat", name="Leah", sibling="Noah", parent="father"),
    StoryParams(setting="garden", mystery="collar", culprit="dog", name="Ivy", sibling="Eli", parent="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CULES:
            for coll in COLLARS:
                out.append((s, coll, c))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a flashback and a missing collar.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=["collar"])
    ap.add_argument("--culprit", choices=CULES)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.culprit is None or c[2] == args.culprit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, _, culprit = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        mystery="collar",
        culprit=culprit,
        name=args.name or rng.choice(["Mina", "Ivy", "Leah", "Tia", "Nora"]),
        sibling=args.sibling or rng.choice(["Owen", "Eli", "Noah", "Ben", "Milo"]),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity]:
    place = SETTINGS[params.setting]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Ivy", "Leah", "Tia", "Nora"} else "boy", role="sleuth", meters={}, memes={}))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="boy", role="helper", meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", role="adult", meters={}, memes={}))
    pet = world.add(Entity(id="Pet", kind="character", type=params.culprit, label=f"the {params.culprit}", role="pet", meters={"hidden": 0.0, "found": 0.0}, memes={"restless": 0.0}, attrs={"collar_spot": COLLARS["red"].place}))
    collar = world.add(Entity(id="collar", type="thing", label="collar", phrase="a collar", owner="Pet", meters={"hidden": 0.0, "dust": 0.0, "found": 0.0}, memes={"worry": 0.0}, attrs={"color": "red"}))
    world.facts.update(child=child, sibling=sibling, parent=parent, pet=pet, collar=collar, setting=place)
    return world, child, sibling, parent, pet


def _search(world: World, place: str) -> None:
    world.get("collar").meters["hidden"] += 1.0
    if place == world.place.id:
        world.get("collar").meters["found"] += 1.0
        world.get("collar").meters["dust"] += 0.2
    else:
        world.get("collar").meters["hidden"] += 0.2


def tell(params: StoryParams) -> World:
    world, child, sibling, parent, pet = _setup_world(params)
    collar = world.get("collar")
    child.memes["curiosity"] = 1.0
    sibling.memes["curiosity"] = 0.8
    parent.memes["worry"] = 0.5
    pet.memes["worry"] = 1.0

    world.say(f"{child.id} noticed that {pet.label_word if hasattr(pet, 'label_word') else 'the pet'} was bare-necked, and the collar was gone.")
    world.say(f"{child.id} and {sibling.id} looked under the bench and by the drawer, while {parent.label_word} listened closely.")
    world.para()

    _search(world, "bench")
    _search(world, "drawer")
    parent.memes["worry"] += 0.5
    child.memes["suspicion"] = 0.7
    world.say(f"They found only a little dust and a bent ribbon, which made the mystery feel even stranger.")
    world.say(f'"Who moved the collar?" {child.id} whispered.')

    world.para()
    world.say(f"Then came a flashback: earlier, {sibling.id} had seen the collar near a muddy paw print.")
    world.say(f'{sibling.id} remembered {pet.label if hasattr(pet, "label") else "the pet"} shaking water onto the floor, so {sibling.id} had tucked the collar away on the high hook to keep it clean.')
    collar.meters["hidden"] = 0.0
    collar.meters["found"] = 1.0
    collar.memes["worry"] = 0.0
    sibling.memes["memory"] = 1.0
    child.memes["suspicion"] = 0.0
    child.memes["relief"] = 1.0

    world.para()
    world.say(f"{child.id} climbed to the hook, found {collar.label} at last, and held it up like a tiny prize.")
    world.say(f'{parent.label_word.capitalize()} smiled, because the flashback had solved the puzzle: it was never stolen, only hidden for safekeeping.')
    world.say(f"At the end, {pet.label if hasattr(pet, 'label') else 'the pet'} wore the collar again, and its bell gave one bright little jingle by the door.")

    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        pet=pet,
        collar=collar,
        found=bool(collar.meters["found"] >= THRESHOLD),
        hidden=bool(collar.meters["hidden"] == 0.0),
        setting=params.setting,
        culprit=params.culprit,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    return [
        f"Write a short whodunit for a young child about {child.id} and {sibling.id} solving a missing collar mystery.",
        f"Tell a gentle mystery story where the word 'collar' appears, and a flashback explains why it was hidden.",
        f"Write a child-friendly detective story set in {world.place.label} that ends with the collar back on the pet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    parent = f["parent"]
    collar = f["collar"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"The pet's collar was missing. {child.id} noticed it right away, so the search began as soon as the story opened.",
        ),
        QAItem(
            question=f"What clue made the mystery feel strange before the flashback?",
            answer=f"They found only dust and a bent ribbon. That clue made it seem as if something had been hidden, not stolen.",
        ),
        QAItem(
            question=f"What did the flashback show {sibling.id} had done with the collar?",
            answer=f"The flashback showed {sibling.id} had tucked the collar on a high hook to keep it clean. {sibling.id} moved it because the pet had shaken muddy water everywhere.",
        ),
        QAItem(
            question=f"How did the mystery end for {collar.label}?",
            answer=f"{child.id} found the collar on the hook and held it up at the end. Then the pet wore it again, so the missing thing was back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a collar?",
            answer="A collar is a band that goes around an animal's neck. It can hold a tag or a bell so people know which pet it is.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part that tells about something from earlier. It helps explain a clue or show why something happened.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them figure out what really happened. Small things like dust, a mark, or a moved object can solve the mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id:8} {e.type:8} meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(out)


ASP_RULES = r"""
setting(kitchen). setting(hall). setting(garden). setting(laundry).
mystery(collar).
culprit(dog). culprit(cat). culprit(rabbit).

valid(S, M, C) :- setting(S), mystery(M), culprit(C).
found(M) :- mystery(M).
flashback_explains(collar).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    lines.append(asp.fact("mystery", "collar"))
    for c in CULES:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, culprit=None, name=None, sibling=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: ASP parity and story generation smoke test passed.")
        return 0
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
