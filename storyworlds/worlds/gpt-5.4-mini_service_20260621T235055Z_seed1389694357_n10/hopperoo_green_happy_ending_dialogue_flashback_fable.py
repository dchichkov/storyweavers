#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T235055Z_seed1389694357_n10/hopperoo_green_happy_ending_dialogue_flashback_fable.py
=================================================================================================

A standalone storyworld in a small fable mode: a hopperoo, something green,
a warning remembered from a flashback, a short piece of dialogue, and a happy
ending that proves the turn in the world.

The tale is built from a tiny simulation:
- a hopperoo wants a green prize,
- a mentor or friend remembers a lesson,
- a risky choice can be avoided or repaired,
- the ending shows the changed physical state.

This world is intentionally small, child-facing, and classical in shape.
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
from pathlib import Path
from typing import Callable, Optional


def _bootstrap_results_import() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "results.py").exists():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("Could not locate storyworlds/results.py")


_bootstrap_results_import()
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIGHT_MIN = 2


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    scene: str
    detail: str
    vibe: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GreenThing:
    id: str
    label: str
    phrase: str
    kind: str
    place_use: str
    can_fall: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hopperoo")
    prize = world.get("prize")
    if hero.memes["rush"] >= THRESHOLD and not prize.meters["held"]:
        sig = ("drop",)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["fallen"] = 1
            hero.memes["worry"] += 1
            out.append("")
    return out


def _r_sooth(world: World) -> list[str]:
    out: list[str] = []
    mentor = world.get("mentor")
    hero = world.get("hopperoo")
    if mentor.memes["warning"] >= THRESHOLD and hero.memes["worry"] >= THRESHOLD:
        sig = ("sooth",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["calm"] += 1
            mentor.memes["warmth"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("drop", _r_drop), Rule("sooth", _r_sooth)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= BRIGHT_MIN]


def valid_combo(place: Place, thing: GreenThing) -> bool:
    return place.id in PLACES and thing.id in GREEN_THINGS and thing.place_use == place.id


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for gid, thing in GREEN_THINGS.items():
            if thing.place_use == pid:
                combos.append((pid, gid))
    return combos


def _flashback_line(hero: Entity, mentor: Entity, thing: GreenThing) -> str:
    return (
        f"Long ago, {mentor.id} had said, \"A wise hopperoo looks before a hop.\" "
        f"{hero.id} remembered that lesson when the {thing.label} looked inviting."
    )


def _setup(world: World, place: Place, hero: Entity, mentor: Entity, thing: GreenThing) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"At {place.scene}, {hero.id} found a little surprise: {thing.phrase}. "
        f"{place.detail}"
    )
    world.say(
        f"{hero.id} smiled and said, \"If I can reach the {thing.label}, the day will be bright.\""
    )


def _warn(world: World, hero: Entity, mentor: Entity, thing: GreenThing) -> None:
    mentor.memes["warning"] += 1
    hero.memes["rush"] += 1
    world.say(
        f"{mentor.id} watched the {thing.label} and said, \"Wait, {hero.id}. "
        f"{thing.label.capitalize()} can be tricky.\""
    )
    world.say(_flashback_line(hero, mentor, thing))


def _risk(world: World, hero: Entity, thing: GreenThing) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} took one hopping step, then another, but the {thing.label} wobbled."
    )


def _turn(world: World, hero: Entity, mentor: Entity, thing: GreenThing, response: Response) -> None:
    hero.memes["calm"] += 1
    mentor.memes["warmth"] += 1
    thing.meters["held"] = 1
    world.say(
        f'{mentor.id} said, "{response.text}"'
    )
    world.say(
        f"{hero.id} nodded and chose the safe way. Soon the {thing.label} was steady again."
    )


def _ending(world: World, hero: Entity, mentor: Entity, place: Place, thing: GreenThing) -> None:
    hero.memes["joy"] += 2
    world.say(
        f"In the end, {hero.id} and {mentor.id} stood together in {place.scene}, "
        f"and the green thing shone where it belonged."
    )
    world.say(
        f"{hero.id} laughed, because the lesson had made the day safe, and the happy ending stayed."
    )


def tell(place: Place, thing: GreenThing, response: Response,
         hero_name: str = "hopperoo", hero_type: str = "hopperoo",
         mentor_name: str = "Mina", mentor_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type, role="mentor"))
    prize = world.add(Entity(id="prize", kind="thing", type=thing.kind, label=thing.label))
    world.facts["place"] = place
    world.facts["thing"] = thing
    world.facts["response"] = response
    world.facts["hero"] = hero
    world.facts["mentor"] = mentor
    world.facts["prize"] = prize

    _setup(world, place, hero, mentor, thing)
    world.para()
    _warn(world, hero, mentor, thing)
    _risk(world, hero, thing)
    propagate(world)
    world.para()
    _turn(world, hero, mentor, thing, response)
    world.para()
    _ending(world, hero, mentor, place, thing)
    world.facts["outcome"] = "happy"
    return world


PLACES = {
    "meadow": Place(
        id="meadow",
        scene="a sunny meadow",
        detail="The grass was soft, and the breeze moved like a quiet song.",
        vibe="bright",
        tags={"field", "grass"},
    ),
    "orchard": Place(
        id="orchard",
        scene="an old orchard",
        detail="The apple trees stood in a row, with moss on the roots and light in the leaves.",
        vibe="gentle",
        tags={"trees", "fruit"},
    ),
    "pond": Place(
        id="pond",
        scene="the pond edge",
        detail="The water shivered in little rings, and reeds leaned toward the bank.",
        vibe="still",
        tags={"water", "bank"},
    ),
}

GREEN_THINGS = {
    "clover": GreenThing(
        id="clover",
        label="green clover",
        phrase="a patch of green clover",
        kind="plant",
        place_use="meadow",
        can_fall=False,
        tags={"green", "plant"},
    ),
    "apple": GreenThing(
        id="apple",
        label="green apple",
        phrase="a green apple on a low branch",
        kind="fruit",
        place_use="orchard",
        can_fall=True,
        tags={"green", "fruit"},
    ),
    "reed": GreenThing(
        id="reed",
        label="green reed",
        phrase="a green reed swaying by the pond",
        kind="plant",
        place_use="pond",
        can_fall=True,
        tags={"green", "water"},
    ),
}

RESPONSES = {
    "bridge": Response(
        id="bridge",
        sense=3,
        power=3,
        text="let's use the little bridge stone and reach it carefully",
        qa_text="used the little bridge stone and reached it carefully",
        tags={"safe", "bridge"},
    ),
    "ask": Response(
        id="ask",
        sense=3,
        power=3,
        text="let's ask for help and take one safe step at a time",
        qa_text="asked for help and took one safe step at a time",
        tags={"safe", "help"},
    ),
    "wait": Response(
        id="wait",
        sense=2,
        power=2,
        text="let's wait for the wind to settle, then try again",
        qa_text="waited for the wind to settle, then tried again",
        tags={"safe", "wait"},
    ),
}

HOPPEROO_NAMES = ["hopperoo", "Hopperoo", "Pip", "Milo", "Junie"]
MENTOR_NAMES = ["Mina", "Lara", "Nico", "Bram", "Tessa"]


@dataclass
class StoryParams:
    place: str
    thing: str
    response: str
    hero_name: str
    mentor_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="meadow", thing="clover", response="bridge", hero_name="hopperoo", mentor_name="Mina"),
    StoryParams(place="orchard", thing="apple", response="ask", hero_name="Pip", mentor_name="Bram"),
    StoryParams(place="pond", thing="reed", response="wait", hero_name="Junie", mentor_name="Tessa"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    thing = f["thing"]
    return [
        f'Write a fable-style story for a child featuring a hopperoo and the word "{thing.label}".',
        f"Tell a happy story set at {place.scene} where {f['hero'].id} remembers an old lesson before reaching {thing.phrase}.",
        f'Write a short dialogue-and-flashback tale where the green {thing.label.split()[-1]} helps teach a kind lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    place = f["place"]
    thing = f["thing"]
    response = f["response"]
    return [
        QAItem(
            question=f"What did {hero.id} want at {place.scene}?",
            answer=f"{hero.id} wanted to reach {thing.phrase}. It looked bright and nice, so the hopperoo hoped to get it without trouble.",
        ),
        QAItem(
            question=f"Why did {mentor.id} warn {hero.id}?",
            answer=f"{mentor.id} warned {hero.id} because {thing.label} could be tricky to reach safely. The warning matched the old lesson in the flashback.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id}?",
            answer=f"It reminded {hero.id} that a wise hopperoo looks before a hop. That old memory helped the hero choose the safer path.",
        ),
        QAItem(
            question=f"How did {hero.id} and {mentor.id} solve the problem?",
            answer=f"They used {response.qa_text}, so the green prize stayed safe and the two of them could smile at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    thing = f["thing"]
    out = [
        QAItem(
            question="What does green mean?",
            answer="Green is the color of grass, leaves, and many plants. It often makes a story feel fresh and alive.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before. It helps explain why a character acts wisely later.",
        ),
        QAItem(
            question="Why can a lesson help in a fable?",
            answer="A lesson can help a character choose the kinder or safer path. In a fable, that choice usually leads to a happy ending.",
        ),
    ]
    if "green" in thing.tags:
        out.append(QAItem(
            question="Why might a green plant look cheerful?",
            answer="Green plants can look cheerful because they suggest new growth and soft, living things. That makes them feel bright in a child's story.",
        ))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return sorted((pid, gid) for pid in PLACES for gid, thing in GREEN_THINGS.items() if thing.place_use == pid)


def explain_rejection(place: Place, thing: GreenThing) -> str:
    return f"(No story: {thing.phrase} does not fit {place.scene}. Pick the matching place for that green thing.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is not reasonable enough for this little fable, because sense={r.sense} < {BRIGHT_MIN}.)"


ASP_RULES = r"""
valid(P, T) :- place(P), thing(T), place_use(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, thing in GREEN_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("place_use", tid, thing.place_use))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) == set(asp_valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, thing=None, response=None, hero_name=None, mentor_name=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a hopperoo and something green.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=GREEN_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--mentor-name")
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
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, thing = rng.choice(combos)
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_name = args.hero_name or rng.choice(HOPPEROO_NAMES)
    mentor_name = args.mentor_name or rng.choice(MENTOR_NAMES)
    return StoryParams(place=place, thing=thing, response=response, hero_name=hero_name, mentor_name=mentor_name)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.thing not in GREEN_THINGS:
        raise StoryError("Unknown green thing.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    place = PLACES[params.place]
    thing = GREEN_THINGS[params.thing]
    response = RESPONSES[params.response]
    world = tell(place, thing, response, hero_name=params.hero_name, mentor_name=params.mentor_name)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, thing=t, response="bridge", hero_name="hopperoo", mentor_name="Mina")) for p, t in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params = StoryParams(place=params.place, thing=params.thing, response=params.response, hero_name=params.hero_name, mentor_name=params.mentor_name, seed=base_seed + i)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
