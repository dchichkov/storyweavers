#!/usr/bin/env python3
"""
storyworlds/worlds/retard_happy_ending_ghost_story.py
======================================================

A small haunted-house storyworld with a gentle ghost-story mood and a happy ending.

Premise:
- A child visits an old house where a lonely ghost has been making a soft fuss.
- The ghost is not scary; it only rattles because it cannot finish one last simple wish.
- The child notices a dusty brass knob marked "RETARD" on an old clock.
- In this world, "retard" is the old mechanical word for "slow down."

Turn:
- The ghost is sad because the clock runs too fast and its tiny chimes never settle.
- The child first thinks the house is spooky, then learns the ghost is only asking for help.
- Turning the knob slows the clock and calms the room.

Resolution:
- The ghost can finally hear the tune clearly, the room grows warm, and the child leaves with a friend.
- The story ends with the ghost laughing softly instead of rattling alone.

World model:
- Physical meters track dust, glow, noise, warmth, and clock-speed.
- Emotional memes track fear, curiosity, loneliness, relief, and friendship.
- The simulated state drives the prose: what changes in the room is what gets narrated.
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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clock: object | None = None
    ghost: object | None = None
    knob: object | None = None
    note: object | None = None
    def __post_init__(self) -> None:
        for key in ["dust", "glow", "noise", "warmth", "clock_speed"]:
            self.meters.setdefault(key, 0.0)
        for key in ["fear", "curiosity", "loneliness", "relief", "friendship"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    name: str = "the old house"
    rooms: list[str] = field(default_factory=lambda: ["front hall", "attic"])
    spooky: bool = True
    world: object | None = None
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


def _tweak(world: World, key: str, amount: float) -> None:
    world.facts[key] = world.facts.get(key, 0.0) + amount


def _rule_spook(world: World) -> list[str]:
    out = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes["fear"] >= THRESHOLD and ghost.meters["noise"] >= THRESHOLD:
        sig = ("spook",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["curiosity"] += 1
        ghost.memes["loneliness"] += 1
        out.append("The dark room felt big enough for whispers.")
    return out


def _rule_retard(world: World) -> list[str]:
    out = []
    clock = world.get("clock")
    knob = world.get("knob")
    ghost = world.get("ghost")
    if knob.meters["turned"] >= THRESHOLD and clock.meters["clock_speed"] > 0:
        sig = ("retard",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        clock.meters["clock_speed"] = max(0.0, clock.meters["clock_speed"] - 1.0)
        ghost.meters["noise"] = max(0.0, ghost.meters["noise"] - 1.0)
        ghost.memes["relief"] += 1
        out.append("The old brass knob did what the label meant: it slowed the clock.")
    return out


def _rule_friendship(world: World) -> list[str]:
    out = []
    child = world.get("child")
    ghost = world.get("ghost")
    if ghost.memes["relief"] >= THRESHOLD and child.memes["curiosity"] >= THRESHOLD:
        sig = ("friendship",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["fear"] = 0.0
        child.memes["friendship"] += 1
        ghost.memes["friendship"] += 1
        child.memes["relief"] += 1
        out.append("The scary feeling melted into a new sort of company.")
    return out


RULES = [_rule_spook, _rule_retard, _rule_friendship]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(Place(name=params.place))
    child = world.add(Entity(id="child", kind="character", type=params.hero_type, label=params.hero_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    clock = world.add(Entity(id="clock", type="thing", label="old clock"))
    knob = world.add(Entity(id="knob", type="thing", label="brass knob"))
    note = world.add(Entity(id="note", type="thing", label="dusty note"))

    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 1.0
    ghost.meters["noise"] = 1.0
    ghost.memes["loneliness"] = 1.0
    clock.meters["clock_speed"] = 2.0
    note.meters["dust"] = 1.0
    note.memes["curiosity"] = 0.0

    world.say(f"{child.label} went into {world.place.name} where the windows sighed.")
    world.say(f"In the front hall, {ghost.label} made a soft, rattly sound from the attic.")
    world.say(f"On the clock was a dusty word: RETARD. It meant slow down, not be rude.")
    world.para()

    world.say(f"{child.label} first felt a shiver, but then {child.pronoun().capitalize()} listened.")
    world.say(f"{ghost.label} was not mean at all; {ghost.pronoun('subject')} was only lonely.")
    world.say(f"{ghost.label} pointed at the old clock, which kept hurrying and hurrying.")
    ghost.meters["noise"] += 1.0
    child.memes["fear"] += 0.0
    propagate(world)

    world.para()
    world.say(f"{child.label} climbed to the attic and found the brass knob by the clock.")
    world.say(f'{child.label} turned the knob marked "RETARD" as gently as holding a bird.')
    knob.meters["turned"] += 1.0
    propagate(world)

    world.para()
    if clock.meters["clock_speed"] <= 1.0:
        world.say(f"The ticking grew slow and kind, like footsteps on a carpet.")
    if ghost.memes["friendship"] >= THRESHOLD:
        world.say(f"{ghost.label} laughed instead of rattling, and the whole house felt warmer.")
        world.say(f"{child.label} smiled back, no longer scared, because the ghost had become a friend.")
    else:
        world.say(f"The room grew quieter, and the lonely sound went away.")

    world.facts.update(
        child=child,
        ghost=ghost,
        clock=clock,
        knob=knob,
        note=note,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost in a story?",
            "In a story, a ghost is often a spirit that can seem spooky, but it can also be lonely, sad, or kind.",
        )
    ],
    "clock": [
        (
            "What does a clock do?",
            "A clock tells time by moving its hands or making ticks so people know when minutes and hours pass.",
        )
    ],
    "slow": [
        (
            "What does it mean to slow something down?",
            "To slow something down means to make it move less quickly or happen with more time in between.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people care about each other, help each other, and feel happy together.",
        )
    ],
}


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("entity", "child"),
        asp.fact("entity", "ghost"),
        asp.fact("entity", "clock"),
        asp.fact("entity", "knob"),
        asp.fact("spooky_place", "old_house"),
        asp.fact("slowable", "clock"),
        asp.fact("marked", "knob", "retard"),
        asp.fact("meaning", "retard", "slow_down"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
marked(X, retard) :- entity(X).
retard_meaning(slow_down) :- meaning(retard, slow_down).
can_help(ghost, clock) :- slowable(clock), marked(knob, retard), retard_meaning(slow_down).
happy_ending :- can_help(ghost, clock).
#show can_help/2.
#show happy_ending/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    child = p["child"]
    ghost = p["ghost"]
    return [
        f'Write a short ghost story for children about {child.label} meeting {ghost.label} in an old house.',
        'Tell a spooky-but-gentle story where a dusty word on a clock helps a lonely ghost feel better.',
        'Write a happy-ending ghost story about a child who discovers that a scary sound was really a request for help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    clock = _safe_fact(world, world.facts, "clock")
    return [
        QAItem(
            question=f"Why did {child.label} feel scared at first?",
            answer=f"{child.label} felt scared because the old house was dark and {ghost.label} was making a spooky rattling sound.",
        ),
        QAItem(
            question="What did the word on the clock mean in this story?",
            answer='The word "RETARD" on the clock meant "slow down," because it was an old mechanical word.',
        ),
        QAItem(
            question=f"How did {child.label} help {ghost.label}?",
            answer=f"{child.label} turned the brass knob by the clock, which slowed the clock down and made {ghost.label} feel calmer.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {ghost.label} laughing softly and {child.label} no longer afraid.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["ghost", "clock", "slow", "friendship"]:
        for q, a in KNOWLEDGE[key]:
            out.append(QAItem(question=q, answer=a))
    return out


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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: str) -> str:
    return f"(No story: the world needs an old house-like place, not {place!r}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost story world with a happy ending."
    )
    ap.add_argument("--place", default="the old house")
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--ghost-name", default="Milo")
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
    if getattr(args, "place", None) and "house" not in getattr(args, "place", None).lower():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=getattr(args, "place", None) or "the old house",
        hero_name=getattr(args, "hero_name", None) or rng.choice(["Nora", "Mina", "Ivy", "June", "Eli"]),
        hero_type=getattr(args, "hero_type", None),
        ghost_name=getattr(args, "ghost_name", None) or rng.choice(["Milo", "Pip", "Wren", "Odo"]),
        seed=None,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show happy_ending/0."))
    atoms = asp.atoms(model, "happy_ending")
    if atoms:
        print("OK: ASP model reaches a happy ending.")
        return 0
    print("MISMATCH: ASP model did not reach happy_ending.")
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show can_help/2.\n#show happy_ending/0."))
    return [(sym.name, tuple(arg.string if arg.type == arg.type.String else getattr(arg, "number", getattr(arg, "name", None)) for arg in sym.arguments)) for sym in model]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show can_help/2.\n#show happy_ending/0."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams(place="the old house", hero_name="Nora", hero_type="girl", ghost_name="Milo"),
            StoryParams(place="the old house", hero_name="Eli", hero_type="boy", ghost_name="Pip"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
