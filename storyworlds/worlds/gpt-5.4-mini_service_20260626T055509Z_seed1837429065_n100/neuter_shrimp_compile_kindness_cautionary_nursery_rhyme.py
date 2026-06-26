#!/usr/bin/env python3
"""
storyworlds/worlds/neuter_shrimp_compile_kindness_cautionary_nursery_rhyme.py
===============================================================================

A small nursery-rhyme-style story world about a neuter little shrimp who wants
to compile a shiny shell song, with Kindness and Cautionary beats shaping the
turn and resolution.

Seed tale, imagined:
---
A tiny shrimp lived in a coral nook and loved to compile little songs by
stacking bright shells into patterns. One tide, the shrimp found a loose
needle-shell that could prick a fin. A wise crab offered a kinder way: slow
down, sort the shells, and build the song safely. The shrimp listened, used a
soft basket, and the finished song came out neat, bright, and unhurt.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "shrimp":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Reef:
    place: str = "the coral nook"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


class World:
    def __init__(self, reef: Reef) -> None:
        self.reef = reef
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.reef)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c


ACTIVITY = Activity(
    id="compile",
    verb="compile a shell tune",
    gerund="compiling shell tunes",
    rush="rush to stack the shells",
    mess="scratched",
    soil="scratched and dim",
    zone={"hands", "head"},
    keyword="compile",
    tags={"compile", "kindness", "cautionary"},
)

PRIZE = Prize(
    label="fin card",
    phrase="a bright fin card",
    type="card",
    region="hands",
)

GEAR = [
    Tool(
        id="basket",
        label="a soft basket",
        covers={"hands"},
        guards={"scratched"},
        prep="use a soft basket for the sharp shells",
        tail="tucked the sharp shells into a soft basket",
    ),
    Tool(
        id="mittens",
        label="little shell mittens",
        covers={"hands"},
        guards={"scratched"},
        prep="put on little shell mittens first",
        tail="slipped on little shell mittens",
    ),
]

SETTINGS = {
    "reef": Reef(place="the coral nook", affords={"compile"}),
}

NAMES = ["Pip", "Miri", "Tio", "Nia", "Lumi"]
COMPANIONS = ["crab", "starfish", "turtle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    companion: str
    seed: Optional[int] = None


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scratched", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("scrape", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scratched"] = item.meters.get("scratched", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got scratched.")
    return out


CAUSAL_RULES = [_r_scrape]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)


def predict_scrape(world: World, actor: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters[activity.mess] = 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    return any(e.meters.get("scratched", 0.0) >= THRESHOLD for e in sim.entities.values())


def place_intro(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"In {world.reef.place}, there lived a little shrimp named {hero.id}.")
    world.say(f"It loved {activity.gerund}, and the reef hummed like a lullaby.")


def caution(world: World, companion: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"One tide, {companion.type} said, \"Careful, {hero.id}; {prize.label} may turn {activity.soil}.\""
    )


def desire(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"But {hero.id} still wanted to {activity.verb}, quick as a wink.")


def worry(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"The sharp shells looked tricky, and the little {prize.label} could be scratched.")


def offer_kindness(world: World, companion: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Tool]:
    for tool in GEAR:
        if prize.region in tool.covers and activity.mess in tool.guards:
            t = world.add(Entity(
                id=tool.id,
                type="tool",
                label=tool.label,
                owner=hero.id,
                caretaker=companion.id,
                protective=True,
                covers=set(tool.covers),
                plural=tool.plural,
            ))
            t.worn_by = hero.id
            if predict_scrape(world, hero, activity):
                t.worn_by = None
                del world.entities[t.id]
                return None
            world.say(f"Then {companion.type} smiled kindly and said, \"How about we {tool.prep}?\"")
            return tool
    return None


def accept(world: World, hero: Entity, companion: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(f"{hero.id} nodded, and the little shrimp took the kind help.")
    world.say(
        f"So it {tool.tail}, {activity.gerund} safely, and the {prize.label} stayed bright and neat."
    )


def tell(reef: Reef, hero_name: str, companion_type: str) -> World:
    world = World(reef)
    hero = world.add(Entity(id=hero_name, kind="character", type="shrimp"))
    companion = world.add(Entity(id="Kind Guide", kind="character", type=companion_type, label=companion_type))
    prize = world.add(Entity(
        id="card",
        type=PRIZE.type,
        label=PRIZE.label,
        phrase=PRIZE.phrase,
        owner=hero.id,
        caretaker=companion.id,
        region=PRIZE.region,
        plural=PRIZE.plural,
    ))

    place_intro(world, hero, ACTIVITY)
    world.para()
    caution(world, companion, hero, prize, ACTIVITY)
    desire(world, hero, ACTIVITY)
    worry(world, hero, prize, ACTIVITY)

    tool = offer_kindness(world, companion, hero, ACTIVITY, prize)
    world.para()
    if tool:
        accept(world, hero, companion, ACTIVITY, prize, tool)
    else:
        world.say("So the tiny shrimp paused and chose a safer way instead.")

    world.facts.update(hero=hero, companion=companion, prize=prize, tool=tool, activity=ACTIVITY, reef=reef)
    return world


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("activity", ACTIVITY.id),
        asp.fact("mess_of", ACTIVITY.id, ACTIVITY.mess),
    ]
    for z in sorted(ACTIVITY.zone):
        lines.append(asp.fact("splashes", ACTIVITY.id, z))
    lines.append(asp.fact("prize", PRIZE.label))
    lines.append(asp.fact("worn_on", PRIZE.label, PRIZE.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    lines.append(asp.fact("places", SETTINGS["reef"].place))
    lines.append(asp.fact("affords", "reef", ACTIVITY.id))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), gear(G), covers(G, R), worn_on(P, R), splashes(A, R0), R = R0, guards(G, M), mess_of(A, M).
has_fix(A, P) :- protects(_, A, P).
valid_story(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("reef", ACTIVITY.id, PRIZE.label)]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(set(asp_valid_combos())))
    print("Python:", sorted(set(valid_combos())))
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery rhyme about a neuter shrimp who wants to compile a shell tune.',
        f"Tell a gentle story where {world.facts['hero'].id} wants to compile at {world.reef.place}, but a kind helper worries about the {PRIZE.label}.",
        "Write a cautionary nursery rhyme that ends with kindness making the safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    prize: Entity = f["prize"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little shrimp named {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {ACTIVITY.verb} in the coral nook.",
        ),
        QAItem(
            question=f"Why did the helper speak in a cautionary way?",
            answer=f"{companion.type} worried the {prize.label} could get {ACTIVITY.soil} if the shrimp rushed ahead.",
        ),
    ] + (
        [
            QAItem(
                question=f"How did kindness help {hero.id} finish the task?",
                answer=f"They used {tool.label} first, so {hero.id} could {ACTIVITY.verb} safely and the {prize.label} stayed bright.",
            ),
            QAItem(
                question=f"What changed by the end?",
                answer=f"By the end, the shrimp felt happy, the worry was gone, and the finished tune stayed neat and safe.",
            ),
        ] if tool else []
    )


KNOWLEDGE = {
    "shrimp": [
        QAItem(
            question="What is a shrimp?",
            answer="A shrimp is a tiny sea creature with a soft body and small legs.",
        )
    ],
    "compile": [
        QAItem(
            question="What does it mean to compile something?",
            answer="To compile means to gather and put pieces together into one finished thing.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping gently, using care, and trying to make things safer or happier for someone else.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning so someone can avoid danger or trouble.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("shrimp", "compile", "kindness", "cautionary"):
        out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a shrimp, a compile, a kindness, and a caution.")
    ap.add_argument("--place", choices=["reef"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "reef"
    if place != "reef":
        raise StoryError("Only the reef setting is available in this tiny world.")
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, activity="compile", prize="card", name=name, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.companion)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place="reef", activity="compile", prize="card", name=n, companion=c))
                   for n in NAMES[:3] for c in COMPANIONS[:1]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
