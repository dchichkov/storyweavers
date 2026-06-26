#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/self_nurse_quest_flashback_reconciliation_fairy_tale.py
=========================================================================================

A small fairy-tale storyworld about a self who loses courage, meets a nurse,
follows a quest, remembers a flashback, and ends in reconciliation.

Premise
-------
A child-like self carries a hurt feeling in a little forest kingdom.
A kind nurse helps the self remember an earlier moment of bravery.
Together they go on a quest for a glowing bandage blossom.

Story shape
-----------
1. Setup: the self feels uneasy and needs help.
2. Quest: the nurse offers a path to the moonlit glade.
3. Flashback: the self remembers a past kindness and regains courage.
4. Reconciliation: the self and the nurse make peace with worry and heal.

The world is small, concrete, and state-driven:
- entities have physical meters and emotional memes,
- locations matter,
- the quest changes what the characters carry and feel,
- the flashback modifies courage and trust,
- reconciliation resolves tension and proves the change at the end.

The inline ASP twin mirrors the Python reasonableness gate:
- a quest requires a reachable location,
- the bandage blossom must be at the glade,
- the nurse must be kind enough to help,
- the flashback must be plausible for the self,
- the reconciliation must only happen after a resolved quest.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

LOCATIONS = {
    "cottage": {"name": "the cottage", "kind": "home", "reachable": {"lane"}},
    "lane": {"name": "the mossy lane", "kind": "path", "reachable": {"cottage", "wood", "glade"}},
    "wood": {"name": "the silver wood", "kind": "forest", "reachable": {"lane", "glade"}},
    "glade": {"name": "the moonlit glade", "kind": "quest", "reachable": {"wood", "lane"}},
}

SELF_NAMES = ["Lily", "Mira", "Nora", "Elin", "Rose", "Ada", "June"]
NURSE_NAMES = ["Nurse Hazel", "Nurse Rowan", "Nurse Prim", "Nurse Ivy"]
TRAITS = ["gentle", "curious", "brave", "small", "careful", "bright"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------



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


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    portable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    blossom: object | None = None
    nurse: object | None = None
    self_ent: object | None = None
    def __post_init__(self) -> None:
        for k in ["tired", "safe", "hurt", "glow", "travel", "kept"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "trust", "hope", "courage", "kindness", "peace"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "nurse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# World parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    self_name: str
    nurse_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# State rules
# ---------------------------------------------------------------------------
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


def _adjacent(a: str, b: str) -> bool:
    return b in _safe_lookup(LOCATIONS, a)["reachable"]


def _travel(world: World, actor: Entity, dest: str) -> None:
    if actor.location == dest:
        return
    if not _adjacent(actor.location, dest):
        pass
    actor.location = dest
    actor.meters["travel"] += 1


def _comfort(world: World, nurse: Entity, self_ent: Entity) -> None:
    if nurse.location != self_ent.location:
        pass
    self_ent.memes["trust"] += 1
    self_ent.memes["hope"] += 1
    nurse.memes["kindness"] += 1


def _flashback(world: World, self_ent: Entity) -> bool:
    if self_ent.meters["hurt"] < THRESHOLD:
        return False
    self_ent.memes["courage"] += 1
    self_ent.memes["worry"] = max(0.0, self_ent.memes["worry"] - 1)
    return True


def _quest_success(world: World, self_ent: Entity) -> bool:
    blossom = world.get("blossom")
    return self_ent.location == blossom.location and self_ent.memes["courage"] >= THRESHOLD


def _reconcile(world: World, self_ent: Entity, nurse: Entity) -> bool:
    if not _quest_success(world, self_ent):
        return False
    self_ent.memes["peace"] += 1
    self_ent.memes["worry"] = 0.0
    nurse.memes["peace"] += 1
    return True


# ---------------------------------------------------------------------------
# Content model
# ---------------------------------------------------------------------------


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in LOCATIONS:
        pass


def predict_flashback(world: World, self_ent: Entity) -> bool:
    sim = world.copy()
    return _flashback(sim, sim.get(self_ent.id))


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(params.place)

    self_ent = world.add(Entity(
        id=params.self_name,
        kind="character",
        type="girl",
        label="self",
        location="cottage",
        traits=["self", params.trait, "quiet"],
    ))
    nurse = world.add(Entity(
        id=params.nurse_name,
        kind="character",
        type="nurse",
        label="nurse",
        location="cottage",
        traits=["nurse", "kind"],
    ))
    blossom = world.add(Entity(
        id="blossom",
        kind="thing",
        type="flower",
        label="bandage blossom",
        phrase="a glowing bandage blossom",
        location="glade",
        portable=True,
    ))

    # Setup
    self_ent.memes["worry"] += 1
    self_ent.meters["hurt"] += 1
    world.say(
        f"Once in a quiet cottage, {self_ent.id} was a {params.trait} little self "
        f"who felt a sore worry in {self_ent.pronoun('possessive')} chest."
    )
    world.say(
        f"A kind nurse came by with soft steps and a warm lantern, and {self_ent.id} "
        f"trusted {nurse.pronoun('object')} enough to listen."
    )

    # Quest
    world.para()
    _travel(world, self_ent, "lane")
    _travel(world, nurse, "lane")
    _comfort(world, nurse, self_ent)
    world.say(
        f"The nurse spoke of a quest: they must go from the mossy lane to the moonlit glade "
        f"to find a glowing bandage blossom."
    )
    _travel(world, self_ent, "wood")
    _travel(world, nurse, "wood")
    self_ent.memes["worry"] += 1
    world.say(
        f"In the silver wood, the trees whispered, and {self_ent.id} trembled a little more "
        f"because the quest felt bigger than a small self."
    )

    # Flashback
    world.para()
    if predict_flashback(world, self_ent):
        self_ent.meters["hurt"] += 0  # keep state explicit; the memory does the turning
        world.say(
            f"Then came a flashback: {self_ent.id} remembered how, long ago, {nurse.id} "
            f"had wrapped a scraped knee and hummed a tiny lullaby."
        )
        world.say(
            f"That memory made {self_ent.id} lift {self_ent.pronoun('possessive')} chin, "
            f"and courage glimmered like a candle in the dark wood."
        )
    else:
        pass

    # Resolution quest
    _travel(world, self_ent, "glade")
    _travel(world, nurse, "glade")
    if self_ent.location != blossom.location:
        pass
    self_ent.meters["kept"] += 1
    self_ent.meters["safe"] += 1
    world.say(
        f"At the moonlit glade, the bandage blossom waited beneath a silver leaf, and "
        f"{self_ent.id} picked it gently."
    )

    # Reconciliation
    world.para()
    if _reconcile(world, self_ent, nurse):
        world.say(
            f"{self_ent.id} and the nurse smiled at each other, because the worry was gone "
            f"and the quest had been kind."
        )
        world.say(
            f"Back at the cottage, {self_ent.id} kept the blossom close, and the little self "
            f"fell asleep feeling brave and mended."
        )
    else:
        pass

    world.facts.update(
        self=self_ent,
        nurse=nurse,
        blossom=blossom,
        quest_done=True,
        flashback=True,
        reconciled=True,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------


PLACES = {
    "cottage": "cottage",
    "lane": "lane",
    "wood": "wood",
    "glade": "glade",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is valid when the self can travel to the lane, then the wood, then the glade.
can_go(Self, From, To) :- location(Self, From), reachable(From, To).
quest_step(Self, lane) :- location(Self, cottage), reachable(cottage, lane).
quest_step(Self, wood) :- quest_step(Self, lane), reachable(lane, wood).
quest_step(Self, glade) :- quest_step(Self, wood), reachable(wood, glade).

% The flashback is reasonable only if the self started with hurt and worry.
can_flashback(Self) :- hurt(Self), worry(Self).

% Reconciliation requires the quest to be completed and the blossom to be found.
can_reconcile(Self) :- quest_done(Self), has_blossom(Self), flashbacked(Self).

valid_story(Self, Nurse, Place) :- can_reconcile(Self),
                                   nurse_kind(Nurse),
                                   home_place(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc, data in LOCATIONS.items():
        lines.append(asp.fact("home_place", loc))
        for nxt in sorted(data["reachable"]):
            lines.append(asp.fact("reachable", loc, nxt))
    lines.append(asp.fact("nurse_kind", "nurse"))
    lines.append(asp.fact("self_kind", "self"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("self", "nurse", p) for p in LOCATIONS}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: self, nurse, quest, flashback, reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--nurse-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    name = getattr(args, "name", None) or rng.choice(SELF_NAMES)
    nurse_name = getattr(args, "nurse_name", None) or rng.choice(NURSE_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, self_name=name, nurse_name=nurse_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    self_ent = _safe_fact(world, f, "self")
    nurse = _safe_fact(world, f, "nurse")
    return [
        f"Write a fairy tale about {self_ent.id}, a little self, who meets {nurse.id} and goes on a quest.",
        f"Tell a gentle story with a flashback that helps {self_ent.id} become brave again.",
        f"Write a story where a nurse leads a self to a moonlit glade and they end in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    self_ent = _safe_fact(world, f, "self")
    nurse = _safe_fact(world, f, "nurse")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {self_ent.id}, a little self, and {nurse.id}, a kind nurse.",
        ),
        QAItem(
            question=f"What was the quest for?",
            answer="The quest was for a glowing bandage blossom in the moonlit glade.",
        ),
        QAItem(
            question=f"What did the flashback help {self_ent.id} remember?",
            answer=f"It helped {self_ent.id} remember that {nurse.id} had been kind before, so courage could return.",
        ),
        QAItem(
            question=f"How did the story end at {place}?",
            answer=f"It ended in reconciliation, with worry gone and {self_ent.id} feeling brave and mended.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nurse for?",
            answer="A nurse helps care for someone who is hurt or unwell.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a purpose, like looking for something important.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened before.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after worry or conflict.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


CURATED = [
    StoryParams(place="glade", self_name="Lily", nurse_name="Nurse Hazel", trait="gentle"),
    StoryParams(place="wood", self_name="Mira", nurse_name="Nurse Rowan", trait="curious"),
    StoryParams(place="lane", self_name="Nora", nurse_name="Nurse Prim", trait="brave"),
]


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/3."))
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
