#!/usr/bin/env python3
"""
A small standalone storyworld for a friendship-flavored pirate tale.

Premise:
- Alec is a young pirate who loves stories.
- Bell is Alec's shipmate and best friend.
- A shared storybook goes missing aboard the ship.
- The crew must search the deck, follow clues, and work together.
- The ending proves their friendship made the rescue possible.

The world is intentionally small: one ship, one lost storybook, one storm,
and a friendly turn where teamwork restores both the story and the bond.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    alec: object | None = None
    bell: object | None = None
    book: object | None = None
    captain: object | None = None
    lantern: object | None = None
    map_piece: object | None = None
    def __post_init__(self):
        for k in ("salt", "wet", "fear", "joy", "trust", "care"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    seed: Optional[int] = None
    hero_name: str = "Alec"
    friend_name: str = "Bell"
    ship_name: str = "The Gull"
    lost_item: str = "storybook"
    setting: str = "the pirate ship deck"
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
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
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
            self.log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.log = list(self.log)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w
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


THRESHOLD = 1.0


def _raise_salt(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["wet"] >= THRESHOLD and not e.protective:
            sig = ("salt", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["salt"] += 1
            out.append(f"Sea spray clung to {e.label or e.id}.")
    return out


def _raise_fear(world: World) -> list[str]:
    out = []
    captain = world.entities.get("captain")
    if captain and captain.memes["storm_worry"] >= THRESHOLD:
        sig = ("fear", "crew")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["fear"] += 1
        out.append("The storm made everybody a little nervous.")
    return out


def _raise_trust(world: World) -> list[str]:
    out = []
    if world.facts.get("shared_search") and world.facts.get("storybook_found"):
        sig = ("trust", "alec_bell")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("alec").memes["trust"] += 1
        world.get("bell").memes["trust"] += 1
        out.append("Working together made their friendship feel even stronger.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_raise_salt, _raise_fear, _raise_trust):
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(params)
    alec = world.add(Entity(id="alec", kind="character", type="boy", label="Alec"))
    bell = world.add(Entity(id="bell", kind="character", type="girl", label="Bell"))
    captain = world.add(Entity(id="captain", kind="character", type="man", label="the captain"))
    book = world.add(Entity(
        id="storybook",
        type="book",
        label="storybook",
        phrase="a beloved storybook about brave pirates",
        owner="alec",
        caretaker="bell",
    ))
    map_piece = world.add(Entity(id="map", type="map", label="map scrap", phrase="a torn map scrap"))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a small lantern", protective=True, covers={"hands"}))

    world.facts["alec"] = alec
    world.facts["bell"] = bell
    world.facts["captain"] = captain
    world.facts["storybook"] = book
    world.facts["map"] = map_piece
    world.facts["lantern"] = lantern
    return world


def tell(world: World) -> World:
    alec = world.get("alec")
    bell = world.get("bell")
    captain = world.get("captain")
    book = world.get("storybook")
    map_piece = world.get("map")

    world.say(f"Alec lived aboard {world.params.ship_name}, and he loved any good story about the sea.")
    world.say(f"His best friend Bell loved stories too, and the two of them read together whenever the waves were calm.")
    world.say(f"One evening, Alec held up {book.phrase}, but then he noticed it was gone from the cabin shelf.")

    world.para()
    world.say(f"Outside, the wind hissed over {world.params.setting}, and the ship rocked in a choppy dark bay.")
    captain.memes["storm_worry"] += 1
    world.say("The captain said they should keep quiet and look carefully, because a storm was rolling in.")
    world.say("Alec felt his stomach drop, because the storybook had been a gift from his grandfather.")
    world.say("Bell squeezed his hand and promised they would find it together.")

    world.para()
    world.say("They searched the deck, peered under coils of rope, and checked by the mast.")
    world.say("Alec noticed a little torn scrap of paper caught near a wet bucket.")
    world.say(f"Bell held the lantern close, and the scrap showed part of a treasure mark.")
    world.say("That clue pointed them to the captain's chart table, where the storybook had slid during the storm.")
    world.facts["shared_search"] = True
    world.facts["storybook_found"] = True
    propagate(world, narrate=True)

    world.para()
    world.say("Alec laughed with relief and hugged Bell tight.")
    world.say("The captain smiled and said the best crew was one that could search with brave hearts and kind hands.")
    world.say("Soon the storm passed, the book was dry again, and Alec and Bell read the pirate story side by side under the lantern light.")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short pirate tale for children about two friends who lose a beloved storybook and find it together.",
        "Tell a gentle story about Alec and Bell on a ship, where friendship helps solve a stormy problem.",
        "Write a sea adventure story with a missing book, a clue, and a happy friendship ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who were the two friends in the story?",
            answer="The two friends were Alec and Bell. They lived and worked together on the pirate ship and cared about each other.",
        ),
        QAItem(
            question="What important thing went missing?",
            answer="Alec's beloved storybook went missing from the cabin shelf, which worried him because it was a special gift.",
        ),
        QAItem(
            question="How did Alec and Bell solve the problem?",
            answer="They searched the deck together, followed a torn paper clue, and found the storybook at the captain's chart table.",
        ),
        QAItem(
            question="Why did the storm make the search harder?",
            answer="The storm rocked the ship and made everyone more nervous, so Alec and Bell had to look carefully in the wind and spray.",
        ),
        QAItem(
            question="What showed that their friendship mattered at the end?",
            answer="Alec hugged Bell, and they read the storybook together again under the lantern light, which showed they were happy and close friends.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used for sailing on the sea. In stories, pirates often live and travel on one together.",
        ),
        QAItem(
            question="What is a lantern used for?",
            answer="A lantern gives light in the dark, which helps people see things at night or in a stormy place.",
        ),
        QAItem(
            question="Why can storms be hard for sailors?",
            answer="Storms can make waves big and windy, so sailors must hold on, stay careful, and work together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.protective:
            bits.append(f"protective={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A very small ASP twin for the pirate-friendship world.
friendship(a,b) :- named(a), named(b), a != b.
problem(lost_storybook) :- storm, storybook.
solve_together :- friendship(alec,bell), problem(lost_storybook).
happy_end :- solve_together.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("named", "alec"),
            asp.fact("named", "bell"),
            asp.fact("storm"),
            asp.fact("storybook"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/0."))
    ok = any(sym.name == "happy_end" for sym in model)
    if ok:
        print("OK: ASP twin produces the expected happy ending.")
        return 0
    print("MISMATCH: ASP twin did not produce happy_end.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate friendship story world.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name", default=None)
    ap.add_argument("--friend-name", default=None)
    ap.add_argument("--ship-name", default=None)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero_name=getattr(args, "hero_name", None) or "Alec",
        friend_name=getattr(args, "friend_name", None) or "Bell",
        ship_name=getattr(args, "ship_name", None) or "The Gull",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show happy_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show happy_end/0."))
        print("happy_end:", bool(model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = resolve_params(args, random.Random(base_seed))
        samples = [generate(params)]
    else:
        for i in range(getattr(args, "n", None)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
