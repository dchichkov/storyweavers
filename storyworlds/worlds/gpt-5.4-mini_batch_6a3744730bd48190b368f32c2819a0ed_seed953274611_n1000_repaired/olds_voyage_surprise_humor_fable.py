#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/olds_voyage_surprise_humor_fable.py
====================================================================

A tiny fable-style storyworld about two old friends, a voyage, a surprise, and
a harmless joke that becomes a wise lesson.

The world is built around a small simulated domain:
- a pair of old travelers ("the olds") set out on a voyage,
- they expect one thing and discover another,
- humor softens the mistake,
- a surprise changes the plan,
- the ending proves what changed by showing a new route, a new tool, or a new
  attitude.

The required seed words are kept in the world and the prose:
- "olds"
- "voyage"

The style aims for a simple fable: concrete, child-facing, and ending with a
clear lesson image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "father", "dad"}
        female = {"woman", "girl", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Route:
    id: str
    place: str
    surprise: str
    danger: str
    ending_image: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
class Vessel:
    id: str
    label: str
    size: str
    can_turn: bool
    can_float: bool
    can_carry: bool
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
class Weather:
    id: str
    label: str
    mood: str
    surprise_kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
class Fix:
    id: str
    label: str
    smart: int
    strength: int
    text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
    route: str
    vessel: str
    weather: str
    fix: str
    elder: str
    companion: str
    elder_type: str
    companion_type: str
    seed: Optional[int] = None
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_laugh(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["surprise"] >= THRESHOLD and ("laugh", e.id) not in world.fired:
            world.fired.add(("laugh", e.id))
            e.memes["humor"] += 1
            out.append("__laugh__")
    return out


def _r_lessons(world: World) -> list[str]:
    out = []
    if world.facts.get("resolved") and ("lesson",) not in world.fired:
        world.fired.add(("lesson",))
        world.get("elders").memes["wisdom"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES: list[tuple[str, Callable[[World], list[str]]]] = [
    ("laugh", _r_laugh),
    ("lesson", _r_lessons),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_fixs() -> list[Fix]:
    return [f for f in FIXES.values() if f.smart >= 2]


def valid_combo(route: Route, vessel: Vessel, fix: Fix) -> bool:
    return route.danger != "none" and vessel.can_float and fix.smart >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for rid, r in ROUTES.items():
        for vid, v in VESSELS.items():
            for fid, f in FIXES.items():
                if valid_combo(r, v, f):
                    out.append((rid, vid, fid))
    return out


def predict_surprise(world: World, route: Route, weather: Weather) -> bool:
    sim = world.copy()
    sim.get("elders").memes["surprise"] += 1
    sim.get("companion").memes["surprise"] += 1
    return route.surprise == weather.surprise_kind


def tell(route: Route, vessel: Vessel, weather: Weather, fix: Fix, elder_name: str,
         companion_name: str, elder_type: str, companion_type: str) -> World:
    w = World()
    elders = w.add(Entity(id="elders", kind="character", type=elder_type, label=elder_name, role="traveler"))
    companion = w.add(Entity(id="companion", kind="character", type=companion_type, label=companion_name, role="traveler"))

    elders.memes["curiosity"] = 1
    companion.memes["trust"] = 1

    w.facts["route"] = route
    w.facts["vessel"] = vessel
    w.facts["weather"] = weather
    w.facts["fix"] = fix

    w.say(
        f"The olds were two travelers with kind eyes and slow steps, and they began a voyage "
        f"across {route.place}. They rode in {vessel.label}, and the day felt {weather.mood}."
    )
    w.say(
        f"{elder_name} said, \"A voyage is wiser when the wind is friendly.\" "
        f"{companion_name} nodded and pointed ahead."
    )

    w.para()
    elders.memes["hope"] += 1
    companion.memes["hope"] += 1
    if predict_surprise(w, route, weather):
        elders.memes["surprise"] += 1
        companion.memes["surprise"] += 1
        w.say(
            f"Then came a surprise: {route.surprise}. It was so sudden that even the gulls seemed to blink."
        )
    else:
        w.say(
            f"The road stayed plain, and the olds kept humming as the voyage went on."
        )

    w.para()
    if route.surprise == weather.surprise_kind:
        w.say(
            f"{companion_name} laughed first. \"Well, that is a fine trick of the sea,\" {companion.pronoun()} said, "
            f"and {elder_name} laughed too."
        )
        w.say(
            f"Instead of grumbling, they used {fix.label}. {fix.text}."
        )
        w.say(
            f"That choice turned a mishap into a joke, and the voyage became easier."
        )
        w.facts["resolved"] = True
    else:
        w.say(
            f"They had no need for a fix, so they simply kept going until the shore grew near."
        )
        w.facts["resolved"] = False

    w.para()
    w.say(
        f"At the end, {route.ending_image}. {route.lesson}"
    )
    w.say("The olds smiled, because a little humor had helped the whole voyage go wiser.")

    w.facts.update(
        elders=elders,
        companion=companion,
        outcome="surprised" if route.surprise == weather.surprise_kind else "calm",
        used_fix=route.surprise == weather.surprise_kind,
        route_id=route.id,
    )
    propagate(w, narrate=False)
    return w


ROUTES = {
    "river": Route(
        id="river",
        place="a sleepy river",
        surprise="a fish jumped into the boat",
        danger="slip",
        ending_image="the boat bobbed beside a bright reed bed",
        lesson="They learned that some surprises are silly, not scary, and a calm laugh can steady the heart.",
        tags={"river", "surprise", "humor"},
    ),
    "islands": Route(
        id="islands",
        place="a chain of little islands",
        surprise="a turtle had stolen their map",
        danger="lost",
        ending_image="the turtle floated past with the map on its shell",
        lesson="They learned that looking closely can turn a missing thing into a kind discovery.",
        tags={"islands", "surprise", "humor"},
    ),
    "harbor": Route(
        id="harbor",
        place="a windy harbor",
        surprise="their hat blew onto a mast",
        danger="silly",
        ending_image="the mast wore the hat like a tiny crown",
        lesson="They learned that a good laugh can make a windy day feel smaller.",
        tags={"harbor", "surprise", "humor"},
    ),
}

VESSELS = {
    "skiff": Vessel(id="skiff", label="a small skiff", size="small", can_turn=True, can_float=True, can_carry=True, tags={"boat"}),
    "barge": Vessel(id="barge", label="a wide barge", size="wide", can_turn=False, can_float=True, can_carry=True, tags={"boat"}),
    "raft": Vessel(id="raft", label="a brave little raft", size="small", can_turn=True, can_float=True, can_carry=False, tags={"boat"}),
}

WEATHERS = {
    "gentle": Weather(id="gentle", label="gentle weather", mood="bright", surprise_kind="fish", tags={"weather"}),
    "breezy": Weather(id="breezy", label="breezy weather", mood="windy", surprise_kind="hat", tags={"weather"}),
    "still": Weather(id="still", label="still weather", mood="quiet", surprise_kind="map", tags={"weather"}),
}

FIXES = {
    "net": Fix(id="net", label="a net", smart=3, strength=2, text="they scooped the fish up gently and set it back in the water", fail_text="the net came up empty", tags={"fix"}),
    "pole": Fix(id="pole", label="a long pole", smart=3, strength=1, text="they hooked the hat free with the pole and bowed to the mast", fail_text="the pole could not reach", tags={"fix"}),
    "ask": Fix(id="ask", label="a cheerful question", smart=2, strength=1, text="they asked the turtle politely, and it pushed the map back with its nose", fail_text="the question answered nothing", tags={"fix"}),
}

ELDER_NAMES = ["Old Ben", "Old Mira", "Old Toma", "Old Lila"]
COMPANION_NAMES = ["Pip", "Nina", "Soot", "Moss"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about the olds and a voyage with surprise and humor.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--elder")
    ap.add_argument("--companion")
    ap.add_argument("--elder-type", default="woman", choices=["woman", "man"])
    ap.add_argument("--companion-type", default="boy", choices=["girl", "boy", "woman", "man"])
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
    if args.fix and FIXES[args.fix].smart < 2:
        raise StoryError("The chosen fix is too silly for this fable.")
    combos = [c for c in valid_combos()
              if (args.route is None or c[0] == args.route)
              and (args.vessel is None or c[1] == args.vessel)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, vessel, fix = rng.choice(sorted(combos))
    elder = args.elder or rng.choice(ELDER_NAMES)
    companion = args.companion or rng.choice(COMPANION_NAMES)
    return StoryParams(route=route, vessel=vessel, weather=rng.choice(list(WEATHERS)),
                       fix=fix, elder=elder, companion=companion,
                       elder_type=args.elder_type, companion_type=args.companion_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about the olds on a voyage where a surprise becomes a joke and a wise fix helps.",
        f"Tell a short story using the words 'olds' and 'voyage' with a surprise on the route {f['route'].place}.",
        f"Write a child-friendly fable where humor helps two travelers keep going after an odd surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    route: Route = f["route"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question="Who are the story about?",
            answer="It is about the olds, two kind travelers, and their voyage together."
        ),
        QAItem(
            question="What surprising thing happened?",
            answer=f"They met this surprise: {route.surprise}. It changed the voyage from ordinary to funny."
        ),
        QAItem(
            question="How did the olds respond?",
            answer=f"They laughed, used {fix.label}, and kept going in a wiser way. The joke helped them stay calm."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a voyage?",
            answer="A voyage is a long trip, often over water, taken to reach another place."
        ),
        QAItem(
            question="What is surprise?",
            answer="A surprise is something you do not expect, so it can make people gasp or laugh."
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the kind of funny feeling or joke that makes people smile or laugh."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines += ["", "== (3) World-knowledge questions =="]
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(route="river", vessel="skiff", weather="gentle", fix="net", elder="Old Mira", companion="Pip", elder_type="woman", companion_type="boy"),
    StoryParams(route="islands", vessel="raft", weather="still", fix="ask", elder="Old Ben", companion="Nina", elder_type="man", companion_type="girl"),
    StoryParams(route="harbor", vessel="barge", weather="breezy", fix="pole", elder="Old Toma", companion="Soot", elder_type="man", companion_type="boy"),
]


def valid_combo_for_asp(route: Route, vessel: Vessel, fix: Fix) -> bool:
    return valid_combo(route, vessel, fix)


ASP_RULES = r"""
valid(R,V,F) :- route(R), vessel(V), fix(F), can_float(V), smart(F,S), S >= 2, dangerous(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("dangerous", rid))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if v.can_float:
            lines.append(asp.fact("can_float", vid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("smart", fid, f.smart))
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
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    sample = CURATED[0]
    try:
        sample_world = generate(sample)
        _ = sample_world.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print(f"OK: ASP matches Python and generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    route = ROUTES.get(params.route)
    vessel = VESSELS.get(params.vessel)
    weather = WEATHERS.get(params.weather)
    fix = FIXES.get(params.fix)
    if not all([route, vessel, weather, fix]):
        raise StoryError("Invalid params.")
    world = tell(route, vessel, weather, fix, params.elder, params.companion, params.elder_type, params.companion_type)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid route/vessel/fix combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
