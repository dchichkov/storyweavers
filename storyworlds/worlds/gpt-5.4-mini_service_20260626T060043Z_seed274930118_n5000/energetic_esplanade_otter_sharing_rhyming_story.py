#!/usr/bin/env python3
"""
A standalone storyworld for an energetic otter on an esplanade, built around
sharing, gentle tension, and a rhyming-story cadence.

This world models a small causal scene:
- an energetic otter gathers a bright snack or toy on the esplanade
- another child or otter wants to join in
- the hero hesitates, then shares
- the shared play lifts joy and softens possessiveness

The prose aims for a Rhyming Story feel: light repetition, cheerful rhythm,
and concrete images that prove what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    partner: object | None = None
    def __post_init__(self) -> None:
        for k in ("energy", "shine", "mess", "shared", "care", "hunger", "joy", "want", "worry", "pride"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"otter", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str = "the esplanade"
    bright: bool = True
    breezy: bool = True
    SETTING: object | None = None
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
class ShareThing:
    id: str
    label: str
    phrase: str
    kind: str
    can_share: bool = True
    yum: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    item: str
    partner_kind: str
    partner_name: str
    hero_name: str
    seed: Optional[int] = None
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="the esplanade", bright=True, breezy=True)

ITEMS = {
    "pebbles": ShareThing(
        id="pebbles",
        label="smooth pebbles",
        phrase="a little pouch of smooth pebbles",
        kind="snack",
        yum="They could be sorted, stacked, and shared one by one.",
    ),
    "snack": ShareThing(
        id="snack",
        label="fish crackers",
        phrase="a bright red bag of fish crackers",
        kind="snack",
        yum="They crunched in a happy little crackle.",
    ),
    "ribbon": ShareThing(
        id="ribbon",
        label="a shiny ribbon",
        phrase="a shiny ribbon for games",
        kind="toy",
        yum="It fluttered in the breeze like a song.",
    ),
}

PARTNERS = {
    "otter": "otter",
    "child": "child",
}

HERO_TYPES = ["otter"]
PARTNER_TYPES = ["otter", "child"]
NAMES = ["Ollie", "Mina", "Pip", "Tavi", "Nori", "Milo"]
PARTNER_NAMES = ["Ari", "Bea", "Cora", "Dino", "Eli", "Fia"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the hero has a shareable thing and a partner to share with.
valid_story(item, partner_kind) :- shareable(item), partner(partner_kind).

% The emotional turn is reasonable only if sharing can lower want and raise joy.
good_turn(item) :- shareable(item), lowers_want(item), raises_joy(item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("shareable", iid))
        lines.append(asp.fact("item_kind", iid, item.kind))
        if item.can_share:
            lines.append(asp.fact("can_share", iid))
    for pk in PARTNERS:
        lines.append(asp.fact("partner", pk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2.\n#show good_turn/1."))
    return sorted(set(asp.atoms(model, "valid_story"))), sorted(set(asp.atoms(model, "good_turn")))


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def validate_params(args: argparse.Namespace) -> None:
    if getattr(args, "item", None) and getattr(args, "item", None) not in ITEMS:
        pass
    if getattr(args, "partner_kind", None) and getattr(args, "partner_kind", None) not in PARTNERS:
        pass
    if getattr(args, "hero_kind", None) and getattr(args, "hero_kind", None) != "otter":
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    validate_params(args)
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    partner_kind = getattr(args, "partner_kind", None) or rng.choice(list(PARTNERS))
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAMES)
    partner_name = getattr(args, "partner_name", None) or rng.choice(PARTNER_NAMES)
    return StoryParams(item=item, partner_kind=partner_kind, partner_name=partner_name, hero_name=hero_name)


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="otter", label="otter"))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_kind, label=params.partner_kind))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=_safe_lookup(ITEMS, params.item).kind,
        label=_safe_lookup(ITEMS, params.item).label,
        phrase=_safe_lookup(ITEMS, params.item).phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, partner=partner, item=item, item_def=_safe_lookup(ITEMS, params.item))
    return world


def predict_shared(world: World) -> bool:
    sim = world.copy()
    hero: Entity = sim.facts["hero"]  # type: ignore[assignment]
    item: Entity = sim.facts["item"]  # type: ignore[assignment]
    hero.memes["want"] += 1
    if item.owner == hero.id and item.held_by is None:
        return True
    return False


def intro(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    world.say(f"On the esplanade, an energetic otter named {hero.id} skipped and swayed.")
    world.say("The breeze blew bright and light, and the water nearby made a silver sound.")


def desire(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    item.meters["shine"] += 1
    hero.memes["want"] += 1
    world.say(f"{hero.id} found {item.phrase} and hugged it close with a gleam in their eyes.")


def partner_arrives(world: World) -> None:
    partner: Entity = _safe_fact(world, world.facts, "partner")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    world.para()
    world.say(f"Then {partner.id} came along, with a hop and a grin, and pointed at the {item.label}.")
    world.say("The partner wanted a turn, and the moment felt tight, like a knot in a string.")


def hesitation(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    if item.meters["shine"] >= THRESHOLD:
        hero.memes["worry"] += 1
        hero.memes["pride"] += 1
        world.say(f"{hero.id} clutched the {item.label} and frowned. It was theirs, and they liked it that way.")
        world.say(f"But the little thought of sharing kept tapping at their heart like a tiny drum.")


def share_turn(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    partner: Entity = _safe_fact(world, world.facts, "partner")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, world.facts, "item")  # type: ignore[assignment]
    item.meters["shared"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    world.say(f"At last, {hero.id} smiled and said, “You can have a turn.”")
    world.say(f"So {hero.id} passed the {item.label} to {partner.id}, and the two of them began a simple game.")
    world.say(f"They rolled and they shared, and they laughed while they sang in a cheerful pair.")
    world.say(f"{item.yum}")
    world.say(f"By the end, the {item.label} was not smaller at all, but the fun had grown tall.")


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    intro(world)
    desire(world)
    partner_arrives(world)
    hesitation(world)
    share_turn(world)

    world.facts["shared"] = True
    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    partner: Entity = _safe_fact(world, f, "partner")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, f, "item")  # type: ignore[assignment]
    return [
        "Write a short rhyming story about an energetic otter on an esplanade who learns to share.",
        f"Tell a gentle story where {hero.id} meets {partner.id} and shares {item.label}.",
        f"Create a child-friendly story with the words energetic, esplanade, and otter, ending in sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    partner: Entity = _safe_fact(world, f, "partner")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, f, "item")  # type: ignore[assignment]
    item_def: ShareThing = _safe_fact(world, f, "item_def")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the energetic otter in the story?",
            answer=f"The energetic otter was {hero.id}, who skipped and swayed on the esplanade.",
        ),
        QAItem(
            question=f"What did {hero.id} want to keep before sharing?",
            answer=f"{hero.id} wanted to keep {item.phrase} close, because they liked how bright and fun it was.",
        ),
        QAItem(
            question=f"What happened when {partner.id} asked for a turn?",
            answer=f"{hero.id} chose to share the {item.label}, and then they played together instead of arguing.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {partner.id} laughing together, while the shared {item.label} made the fun grow bigger.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an esplanade?",
            answer="An esplanade is a broad path or open walkway near water or a nice view, where people can stroll and play.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something with you instead of keeping it all to yourself.",
        ),
        QAItem(
            question="Why can sharing feel kind?",
            answer="Sharing feels kind because it gives another person a turn and helps everyone enjoy the moment together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if e.phrase:
            parts.append(f"phrase={e.phrase}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        lines.append(f"{e.id}: " + ", ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification helpers
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.\n#show good_turn/1.")
    model = asp.one_model(program)
    got_valid = set(asp.atoms(model, "valid_story"))
    got_good = set(asp.atoms(model, "good_turn"))
    want_valid = {(iid, pk) for iid in ITEMS for pk in PARTNERS}
    want_good = {(iid,) for iid in ITEMS}
    if got_valid != want_valid or got_good != want_good:
        print("ASP mismatch.")
        print("valid_story only in asp:", sorted(got_valid - want_valid))
        print("valid_story only in py:", sorted(want_valid - got_valid))
        print("good_turn only in asp:", sorted(got_good - want_good))
        print("good_turn only in py:", sorted(want_good - got_good))
        return 1
    print(f"OK: ASP matches Python reasonableness for {len(want_valid)} combinations.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Energetic otter on an esplanade, learning to share.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--partner-kind", choices=PARTNERS)
    ap.add_argument("--hero-kind", choices=HERO_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
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


CURATED = [
    StoryParams(item="pebbles", partner_kind="child", partner_name="Ari", hero_name="Ollie"),
    StoryParams(item="snack", partner_kind="otter", partner_name="Mina", hero_name="Pip"),
    StoryParams(item="ribbon", partner_kind="child", partner_name="Bea", hero_name="Nori"),
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
        print(asp_program("#show valid_story/2.\n#show good_turn/1."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2.\n#show good_turn/1."))
        print("valid_story:", sorted(set(asp.atoms(model, "valid_story"))))
        print("good_turn:", sorted(set(asp.atoms(model, "good_turn"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} shares {p.item} on the esplanade"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
