#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crank_south_teamwork_folk_tale.py
==================================================================

A small standalone story world for a folk-tale-like teamwork tale:
a child and a helper must turn a stubborn crank on the south side of a village
well, gate, or mill. The crank is jammed, the pair work together, and the world
changes in a concrete ending image.

The domain is intentionally tiny and state-driven:
- a place has a south-side mechanism
- a crank can be stuck or freed
- two helpers each contribute a different kind of strength
- the ending depends on whether teamwork clears the jam

Run it:
    python storyworlds/worlds/gpt-5.4-mini/crank_south_teamwork_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/crank_south_teamwork_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/crank_south_teamwork_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/crank_south_teamwork_folk_tale.py --verify
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
from typing import Optional

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
    side: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    south_side: str
    folk_image: str
    holds: str


@dataclass
class Crank:
    id: str
    label: str
    is_stuck: bool
    turns: int
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpKind:
    id: str
    label: str
    gift: str
    action: str
    boost: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.entities.values() if e.role in {"hero", "helper"}]
    if len(crew) < 2:
        return out
    if not any(e.memes["sharing"] >= THRESHOLD for e in crew):
        return out
    if not any(e.memes["patience"] >= THRESHOLD for e in crew):
        return out
    crank = world.get("crank")
    sig = ("free", crank.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crank.is_stuck = False
    crank.turns += 1
    out.append("__free__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _r_teamwork(world)
        if sents:
            changed = True
            produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def folk_opening(world: World, hero: Entity, helper: Entity, place: Place, crank: Crank) -> None:
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"In a little village, {hero.id} and {helper.id} went south to {place.name}. "
        f"At {place.south_side}, {place.holds} waited beside a stubborn {crank.label}."
    )
    world.say(
        f"The old folk in the lane whispered that {place.folk_image}, but the {crank.label} would not move."
    )


def try_crank(world: World, hero: Entity, helper: Entity, crank: Crank) -> None:
    hero.memes["frustration"] += 1
    world.say(
        f'{hero.id} put both hands on the {crank.label}. "{crank.sound}," it went, but it would not turn.'
    )
    world.say(
        f'{helper.id} came close and said, "{hero.id}, let us do this together."'
    )


def share_work(world: World, hero: Entity, helper: Entity, crank: Crank, kind: HelpKind) -> None:
    hero.memes["sharing"] += 1
    helper.memes["patience"] += 1
    world.say(
        f"{hero.id} held the handle, and {helper.id} {kind.action}. Together they made a steady, small rhythm."
    )
    propagate(world, narrate=False)
    if not crank.is_stuck:
        world.say(
            f"The {crank.label} gave way at last. With a soft {crank.sound}, it turned, and the south-side {place_by_id(world.facts['place']).holds} began to work."
        )


def ending(world: World, hero: Entity, helper: Entity, place: Place, crank: Crank) -> None:
    if crank.is_stuck:
        world.say(
            f"At last, they called the village smith, and the smith oiled the gear so the {crank.label} could turn again."
        )
    else:
        world.say(
            f"By sunset, the south side was humming, and {place.holds} moved as it should."
        )
    world.say(
        f"{hero.id} grinned at {helper.id}. Side by side, they had done the hard thing the kind way."
    )
    world.say(
        f"That night, the folk tale in the village was simple: a stubborn crank could be won by patient hands and a helping friend."
    )


def place_by_id(pid: str) -> Place:
    return PLACES[pid]


def tell(params: "StoryParams") -> World:
    world = World()
    place = PLACES[params.place]
    crank = CRANKS[params.crank]
    help1 = HELPS[params.help1]
    help2 = HELPS[params.help2]

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    world.add(Entity(id="crank", type="thing", label=crank.label))
    world.facts["place"] = place.id

    hero.memes["sharing"] = 0.0
    helper.memes["patience"] = 0.0

    folk_opening(world, hero, helper, place, crank)
    world.para()
    try_crank(world, hero, helper, crank)
    world.say(f"They remembered the {help1.label} and the {help2.label} they had brought.")
    share_work(world, hero, helper, crank, help1)
    share_work(world, hero, helper, crank, help2)
    world.para()
    ending(world, hero, helper, place, crank)

    world.facts.update(
        hero=hero, helper=helper, place_cfg=place, crank_cfg=crank,
        help1=help1, help2=help2, freed=not crank.is_stuck,
    )
    return world


PLACES = {
    "mill": Place("mill", "the old mill", "the south wall", "the wheel turned like a moon in water", "the grain chute"),
    "well": Place("well", "the village well", "the south nook", "the bucket sang like a little bell", "the rope drum"),
    "gate": Place("gate", "the south gate", "the south gate", "the gate guarded the road like an oak giant", "the iron latch"),
}

CRANKS = {
    "wheel": Crank("wheel", "wheel crank", True, 0, "creak", {"wood"}),
    "winch": Crank("winch", "winch crank", True, 0, "grrnk", {"rope"}),
    "latch": Crank("latch", "latch crank", True, 0, "clack", {"iron"}),
}

HELPS = {
    "lift": HelpKind("lift", "lifting hands", "strength", "lifted on the heavy side", 1, {"strength"}),
    "guide": HelpKind("guide", "guiding hands", "care", "guided the handle true", 1, {"care"}),
    "steady": HelpKind("steady", "steady hands", "patience", "kept the motion slow and even", 1, {"patience"}),
}

HERO_NAMES = ["Mina", "Jo", "Tavi", "Lark", "Nell", "Pip"]
HELPER_NAMES = ["Bram", "Ivy", "Soren", "Wren", "Hale", "Faye"]
HERO_TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    crank: str
    help1: str
    help2: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid in PLACES:
        for cid in CRANKS:
            for h1 in HELPS:
                for h2 in HELPS:
                    if h1 != h2:
                        combos.append((pid, cid, h1, h2))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale teamwork storyworld with a stubborn crank.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crank", choices=CRANKS)
    ap.add_argument("--help1", choices=HELPS)
    ap.add_argument("--help2", choices=HELPS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HERO_TYPES)
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
    place = args.place or rng.choice(list(PLACES))
    crank = args.crank or rng.choice(list(CRANKS))
    help1 = args.help1 or rng.choice(list(HELPS))
    help2 = args.help2 or rng.choice([k for k in HELPS if k != help1])
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HERO_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(place, crank, help1, help2, hero, hero_type, helper, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that includes the words "{f["crank_cfg"].label}" and "south".',
        f"Tell a small teamwork story where {f['hero'].id} and {f['helper'].id} go south to fix a stubborn crank together.",
        f"Write a gentle village story about two helpers using patience and sharing to make an old crank turn again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, place, crank = f["hero"], f["helper"], f["place_cfg"], f["crank_cfg"]
    return [
        QAItem(
            question="What problem did the children face?",
            answer=f"They found a stubborn {crank.label} at {place.south_side}, and it would not turn at first. The whole place was waiting for someone patient enough to fix it."
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"{hero.id} and {helper.id} worked together, each using a different kind of help, until the {crank.label} moved. Teamwork made the hard job easier and gave the crank a steady turn."
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The south-side {place.holds} began to work, so the village could use it again. The ending shows that the crank was freed and the job was done kindly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crank?",
            answer="A crank is a handle or lever you turn by hand to make a machine move. It can be stiff or stuck if it needs fixing."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together. When each person adds a little, the whole task can become much easier."
        ),
        QAItem(
            question="What does south mean?",
            answer="South is one direction, like left or right is a direction. People use directions to say where something is."
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
free(C) :- hero_share(H), helper_patience(P), H >= 1, P >= 1, crank(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CRANKS:
        lines.append(asp.fact("crank", cid))
    for hid in HELPS:
        lines.append(asp.fact("help", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    return 0 if set(valid_combos()) == set(asp.atoms(asp.one_model(asp_program("", "#show free/1.")), "free")) else 1


CURATED = [
    StoryParams("mill", "wheel", "lift", "steady", "Mina", "girl", "Bram", "boy"),
    StoryParams("well", "winch", "guide", "steady", "Pip", "boy", "Ivy", "girl"),
    StoryParams("gate", "latch", "steady", "lift", "Nell", "girl", "Hale", "boy"),
]


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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show free/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
