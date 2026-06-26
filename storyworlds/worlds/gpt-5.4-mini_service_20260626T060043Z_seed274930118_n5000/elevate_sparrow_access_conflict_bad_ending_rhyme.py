#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/elevate_sparrow_access_conflict_bad_ending_rhyme.py
=================================================================================================

A small superhero-story world about a tiny caped sparrow, a high place to reach,
and a locked access point that turns the day into a conflict. The world is
narrow on purpose: it generates only plausible stories where the sparrow wants
to elevate, but access is blocked, and the ending lands in a bad but coherent
place.

Seed tale sketch:
---
A tiny hero-sparrow in a bright cape wanted to get up to the roof garden to
save a fallen flag. The only way up was a humming platform called the elevate.
But a stern gatekeeper kept the access door locked. The sparrow argued, tried,
and failed to get through. In the end, the flag stayed below, and the sparrow
had to fly away in the rain, still brave, still small.

Design goals:
- Superhero-story tone with a tiny heroic lead.
- Three required instruments: elevate, sparrow, access.
- Conflict, bad ending, and rhyme all shape the narrative.
- The world state drives prose, Q&A, and ASP parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sparrow", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    height: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hero:
    name: str = "Pip"
    kind: str = "sparrow"
    cape_color: str = "red"
    trait: str = "brave"


@dataclass
class Blocker:
    id: str
    label: str
    lock_kind: str
    mood: str
    keeps_out: set[str]


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    effect: str
    helps_with: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def rhyme(a: str, b: str) -> str:
    """
    A tiny rhyme helper. We keep it simple and deterministic: a light word-tail
    match is enough for child-facing rhyme flavor.
    """
    def tail(s: str) -> str:
        s = re.sub(r"[^a-z]+", "", s.lower())
        for n in range(3, 1, -1):
            if len(s) >= n:
                return s[-n:]
        return s

    return tail(a) == tail(b)


def rhyme_line(left: str, right: str) -> str:
    if rhyme(left, right):
        return f"{left} and {right} went high and sly."
    return f"{left} and {right} would not quite chime."


@dataclass
class StoryParams:
    place: str
    blocker: str
    tool: str
    hero_name: str
    seed: Optional[int] = None


PLACES = {
    "rooftop": Place(name="the rooftop garden", height="high above the street", weather="windy", affords={"elevate"}),
    "tower": Place(name="the watch tower", height="high above the square", weather="stormy", affords={"elevate"}),
    "atrium": Place(name="the glass atrium", height="up under the ceiling", weather="echoing", affords={"elevate"}),
}

BARRIERS = {
    "gate": Blocker(
        id="gate",
        label="the iron gate",
        lock_kind="key lock",
        mood="stern",
        keeps_out={"access"},
    ),
    "door": Blocker(
        id="door",
        label="the tall door",
        lock_kind="bolt",
        mood="cold",
        keeps_out={"access"},
    ),
    "screen": Blocker(
        id="screen",
        label="the blue access screen",
        lock_kind="code",
        mood="glowing",
        keeps_out={"access"},
    ),
}

TOOLS = {
    "ladder": Tool(id="ladder", label="a bright ladder", verb="lean", effect="reach", helps_with={"elevate"}),
    "rope": Tool(id="rope", label="a red rope", verb="tie", effect="pull", helps_with={"elevate"}),
    "badge": Tool(id="badge", label="a silver badge", verb="show", effect="open", helps_with={"access"}),
}

HEROES = ["Pip", "Skye", "Milo", "Ruby", "Jett"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: a tiny sparrow, a high place, and blocked access.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--blocker", choices=BARRIERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=HEROES)
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


def valid_combo(place: str, blocker: str, tool: str) -> bool:
    p = PLACES[place]
    b = BARRIERS[blocker]
    t = TOOLS[tool]
    return "elevate" in p.affords and ("access" in b.keeps_out) and (t.helps_with & {"elevate", "access"})


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for blocker in BARRIERS:
            for tool in TOOLS:
                if valid_combo(place, blocker, tool):
                    out.append((place, blocker, tool))
    return out


def explain_rejection(place: str, blocker: str, tool: str) -> str:
    p = PLACES[place]
    b = BARRIERS[blocker]
    t = TOOLS[tool]
    if "access" not in b.keeps_out:
        return "(No story: the blocker does not block access, so there is no real conflict.)"
    if not (t.helps_with & {"elevate", "access"}):
        return f"(No story: {t.label} does not help a sparrow elevate or gain access.)"
    return f"(No story: the setup at {p.name} does not support the superhero conflict.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.blocker and args.tool and not valid_combo(args.place, args.blocker, args.tool):
        raise StoryError(explain_rejection(args.place, args.blocker, args.tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.blocker is None or c[1] == args.blocker)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, blocker, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        blocker=blocker,
        tool=tool,
        hero_name=args.name or rng.choice(HEROES),
    )


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="sparrow", label=params.hero_name))
    blocker = world.add(Entity(id="blocker", kind="character", type="guard", label=BARRIERS[params.blocker].label))
    tool = world.add(Entity(id="tool", kind="thing", type=params.tool, label=TOOLS[params.tool].label))
    world.facts.update(hero=hero, blocker=blocker, tool=tool, blocker_cfg=BARRIERS[params.blocker], tool_cfg=TOOLS[params.tool])
    return world


def predict_blocked(world: World) -> bool:
    return True


def story_opening(world: World) -> None:
    hero: Entity = world.facts["hero"]
    tool: Entity = world.facts["tool"]
    world.say(
        f"{hero.name_or_label()} was a tiny sparrow superhero in a bright cape."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked to lift up, zoom along, and keep the sky neat and fair."
    )
    world.say(
        f"Near {world.place.name}, {hero.name_or_label()} spotted {tool.name_or_label()} and dreamed of a tall ride."
    )


def story_conflict(world: World) -> None:
    hero: Entity = world.facts["hero"]
    blocker_cfg: Blocker = world.facts["blocker_cfg"]
    tool_cfg: Tool = world.facts["tool_cfg"]

    world.para()
    world.say(
        f"But the way up was blocked: {blocker_cfg.label} stood at the access point with a {blocker_cfg.lock_kind}."
    )
    world.say(
        f'{hero.name_or_label()} tapped the side of {tool_cfg.label} and said, "I need to elevate!"'
    )
    world.say(
        f'{blocker_cfg.label} stayed shut and said, "No access, little hero."'
    )
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1.0
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0


def story_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    blocker_cfg: Blocker = world.facts["blocker_cfg"]
    tool_cfg: Tool = world.facts["tool_cfg"]

    world.say(
        f"{hero.name_or_label()} tried to use {tool_cfg.label}, but {tool_cfg.verb}ing did not unlock the access."
    )
    world.say(
        f"Wind tugged at the cape, and the sparrow felt small beneath the big hard door."
    )
    world.say(
        rhyme_line("high", "sky")
    )
    world.say(
        f"Still, {hero.name_or_label()} peeped a brave rhyme: 'Fly, try, reach the sky.'"
    )


def story_bad_ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    blocker_cfg: Blocker = world.facts["blocker_cfg"]

    world.para()
    world.say(
        f"At last, the stormclouds rolled over {world.place.name}, and the access point stayed locked."
    )
    world.say(
        f"{hero.name_or_label()} had to leave the roof below, with {blocker_cfg.label} still in place."
    )
    world.say(
        f"The little superhero flew home in the drizzle, cape damp, dream unlifted, but heart still brave."
    )


def tell(world: World) -> World:
    story_opening(world)
    story_conflict(world)
    story_turn(world)
    story_bad_ending(world)
    world.facts["resolved"] = False
    world.facts["conflict"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.place.name
    return [
        f"Write a superhero story for a young child about a sparrow who wants to elevate at {p}, but access is blocked.",
        f"Tell a short rhyming story about a tiny sparrow hero, a locked access point, and a bad ending.",
        f"Make a gentle superhero tale with the words elevate, sparrow, and access, ending in a setback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    blocker_cfg: Blocker = world.facts["blocker_cfg"]
    tool_cfg: Tool = world.facts["tool_cfg"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who wanted to elevate at {place}?",
            answer=f"The tiny sparrow superhero {hero.name_or_label()} wanted to elevate at {place}.",
        ),
        QAItem(
            question="Why was the sparrow upset?",
            answer=f"The sparrow was upset because {blocker_cfg.label} kept the access point locked.",
        ),
        QAItem(
            question=f"What tool did {hero.name_or_label()} try to use?",
            answer=f"{hero.name_or_label()} tried to use {tool_cfg.label}, but it did not open the access.",
        ),
        QAItem(
            question="Did the hero get through in the end?",
            answer="No. The story ends badly, with the access still blocked and the sparrow flying away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sparrow?",
            answer="A sparrow is a small bird that can hop, flutter, and fly short distances.",
        ),
        QAItem(
            question="What does access mean?",
            answer="Access means the ability to get into a place or use something.",
        ),
        QAItem(
            question="What does elevate mean?",
            answer="Elevate means to lift up or move higher.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who tries to save the day, often with a special costume or power.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== prompts ==")
    for p in sample.prompts:
        out.append(f"- {p}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind} meters={e.meters} memes={e.memes}")
    lines.append(f"place={world.place.name}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rooftop", blocker="gate", tool="badge", hero_name="Pip"),
    StoryParams(place="tower", blocker="door", tool="ladder", hero_name="Skye"),
    StoryParams(place="atrium", blocker="screen", tool="rope", hero_name="Ruby"),
]


ASP_RULES = r"""
place(P) :- setting(P).
blocker(B) :- lock(B).
tool(T) :- tooldef(T).

can_story(P,B,T) :- setting(P), lock(B), tooldef(T), elevates(T), blocks_access(B), supports(P,elevate).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("supports", p, "elevate"))
        lines.append(asp.fact("topic", p, "superhero"))
    for b_id, b in BARRIERS.items():
        lines.append(asp.fact("lock", b_id))
        lines.append(asp.fact("blocks_access", b_id))
    for t_id, t in TOOLS.items():
        lines.append(asp.fact("tooldef", t_id))
        if "elevate" in t.helps_with:
            lines.append(asp.fact("elevates", t_id))
        if "access" in t.helps_with:
            lines.append(asp.fact("opens_access", t_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(setup_world(params))
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
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_story_params(place: str, blocker: str, tool: str) -> bool:
    return valid_combo(place, blocker, tool)


if __name__ == "__main__":
    main()
