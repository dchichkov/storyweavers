#!/usr/bin/env python3
"""
Storyworld: responsive absorb serve-gerund conflict comedy.

A tiny, child-facing comedy world about a helpful child host, a messy serving
problem, and a responsive absorb-what-spills fix that turns the conflict into a
laughing ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    absorbs: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type in {"scissors", "glasses"} else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    absorbs: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting("the kitchen", {"serve"}),
    "playroom": Setting("the playroom", {"serve"}),
    "garden": Setting("the garden", {"serve"}),
}

ACTIVITIES = {
    "serve": Activity(
        id="serve",
        verb="serve juice",
        gerund="serving juice",
        rush="rush to the table",
        mess="spill",
        soil="spilled",
        zone={"table", "floor", "shirt"},
        keyword="serve-gerund",
        tags={"serve", "spill"},
    ),
    "pour": Activity(
        id="pour",
        verb="pour tea",
        gerund="pouring tea",
        rush="dash to the pitcher",
        mess="spill",
        soil="dribbled",
        zone={"table", "shirt"},
        keyword="responsive",
        tags={"pour", "spill"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean red shirt", "shirt", "shirt"),
    "apron": Prize("apron", "a bright apron", "apron", "shirt"),
    "tray": Prize("tray", "a shiny tray", "tray", "hands"),
}

GEAR = [
    Gear(
        id="towel",
        label="a thick towel",
        absorbs={"spill"},
        covers={"shirt"},
        prep="put a thick towel under the cup",
        tail="spared the shirt and soaked up the spill",
    ),
    Gear(
        id="traygear",
        label="a tray",
        absorbs={"spill"},
        covers={"table"},
        prep="set the cups on a tray",
        tail="kept the wobble from becoming a wobble-and-splash show",
    ),
]

NAMES = ["Mina", "Toby", "Lila", "Nico", "Pia", "Bram"]
TRAITS = ["cheerful", "curious", "silly", "bright", "witty"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def predict_spill(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    return prize_id == "shirt" and activity.id in {"serve", "pour"}


def apply_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters.setdefault(activity.mess, 0.0)
    actor.meters[activity.mess] += 1.0
    actor.memes.setdefault("joy", 0.0)
    actor.memes["joy"] += 1.0
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if activity.mess in item.meters:
            item.meters[activity.mess] += 0.4


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender, meters={}, memes={}, 
        ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id
    ))
    towel = world.add(Entity(
        id="towel", type="thing", label="towel", protective=True, absorbs={"spill"},
        owner=hero.id, caretaker=parent.id
    ))
    prize.worn_by = hero.id

    hero.memes["love"] = 1.0
    world.say(
        f"{hero.id} was a {trait} little {hero.type} who loved helping in the {setting.place[4:] if setting.place.startswith('the ') else setting.place}."
    )
    world.say(
        f"{hero.id} liked {activity.gerund}, especially when the cups clinked like tiny bells."
    )
    world.say(
        f"One day, {hero.id}'s {parent.label_word if hasattr(parent, 'label_word') else 'parent'} bought {hero.pronoun('object')} {prize.phrase} for the job."
    )
    world.say(f"{hero.id} wore {prize.label} and grinned like the room was already applauding.")

    world.para()
    world.say(
        f"When it was time to {activity.verb}, {hero.id} tried to be very {trait}, but the cup wobbled."
    )
    if predict_spill(world, hero, activity, prize.id):
        world.say(
            f"\"Careful,\" said {parent.id}, because the juice was getting ideas and heading for a splash."
        )
    world.say(f"{hero.id} {activity.rush}, and the juice went everywhere with a comic little plop.")

    world.para()
    apply_activity(world, hero, activity)
    prize.meters.setdefault("spill", 0.0)
    prize.meters["spill"] += 1.0
    hero.memes["embarrassment"] = 1.0
    world.say(
        f"The {prize.label} got {activity.soil}, and {hero.id} made a face that said, \"Oh no, my masterpiece!\""
    )
    world.say(
        f"That would mean extra cleaning for the grown-up, and the kitchen looked as if it had joined the joke."
    )
    world.say(
        f"Then {hero.id} noticed the towel and the tray. \"Aha,\" {hero.pronoun('subject')} said, \"the room needs a smarter plan.\""
    )

    if activity.id == "serve":
        world.say(
            f"The towel was responsive and eager to absorb the spill, so {hero.id} tucked it under the cup."
        )
    else:
        world.say(
            f"The tray was responsive too; it helped absorb the wobble before the wobble could become a splat."
        )

    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1.0
    world.say(
        f"{hero.id} tried again, and this time the {prize.label} stayed fine while the towel did the heroic soaking."
    )
    world.say(
        f"At the end, everybody laughed, because the biggest mess had turned into the smallest joke."
    )

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": activity,
        "setting": setting,
        "gear": towel,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f"Write a short comedy about {hero.id} {act.gerund} without ruining {prize.phrase}.",
        f"Tell a child-friendly story about a responsive helper that can absorb a spill during {act.keyword}.",
        f"Create a funny story where a little {hero.type} learns a safer way to {act.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the start?",
            answer=f"{hero.id} wanted to {act.verb}, and {hero.id} was excited about it.",
        ),
        QAItem(
            question=f"What problem happened when {hero.id} tried to {act.verb}?",
            answer=f"The juice spilled and got {prize.label} {act.soil}.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer="A responsive towel helped absorb the spill, and then the child tried again more carefully.",
        ),
        QAItem(
            question=f"Why was the ending funny?",
            answer=f"Because the messy spill turned into a joke, and everyone ended up laughing instead of worrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does absorb mean?",
            answer="Absorb means to soak up liquid so it does not spread everywhere.",
        ),
        QAItem(
            question="What is a responsive helper?",
            answer="A responsive helper notices what is happening and quickly helps in a useful way.",
        ),
        QAItem(
            question="What is a gerund?",
            answer="A gerund is a verb form that acts like a noun, such as serving or laughing.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity touches the same region.
prize_at_risk(A,P) :- activity(A), worn_on(P,R), splashes(A,R).

% Gear is a compatible fix if it absorbs the mess and covers the at-risk region.
protects(G,A,P) :- gear(G), prize_at_risk(A,P),
                   mess_of(A,M), absorbs(G,M),
                   worn_on(P,R), covers(G,R).

has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.absorbs):
            lines.append(asp.fact("absorbs", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and prize_id == "shirt":
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: responsive absorb serve-gerund conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize and args.prize != "shirt":
        raise StoryError("This world keeps the joke focused: the messy serving problem needs a shirt to be worth fixing.")
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(SETTINGS[place].affords))
    prize = args.prize or "shirt"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"absorbs={sorted(e.absorbs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("(1) Generation prompts", sample.prompts),
            ("(2) Story questions", sample.story_qa),
            ("(3) World knowledge", sample.world_qa),
        ]:
            print(title)
            if isinstance(items, list) and items and isinstance(items[0], str):
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("kitchen", "serve", "shirt", "Mina", "girl", "mother", "cheerful"),
            StoryParams("playroom", "pour", "shirt", "Toby", "boy", "father", "silly"),
            StoryParams("garden", "serve", "shirt", "Lila", "girl", "mother", "witty"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
