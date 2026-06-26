#!/usr/bin/env python3
"""
A standalone story world: a cautionary nursery rhyme at the dock.

Seed premise:
A small child goes to a dock with a prized epee and a muff. A spark of
carelessness can inflame a danger, but a wiser choice keeps the child safe.
The story should feel like a nursery rhyme: light, concrete, repetitive, and
cautionary.
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
    protective: bool = False
    plural: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"heat": 0.0, "soot": 0.0, "wet": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "boldness": 0.0, "care": 0.0, "alarm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class DockSetting:
    place: str = "the dock"
    affords: set[str] = field(default_factory=lambda: {"play", "spark"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    protective: bool = False


class World:
    def __init__(self, setting: DockSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTING = DockSetting()

ACTIVITIES = {
    "spark": Activity(
        id="spark",
        verb="strike a spark",
        gerund="striking sparks",
        rush="rush to the bright little spark",
        danger="inflame the straw",
        soil="blacken the air",
        keyword="inflame",
        tags={"fire", "spark", "cautionary"},
    ),
    "play": Activity(
        id="play",
        verb="play by the water",
        gerund="dancing by the dock",
        rush="skip near the edge",
        danger="muff the warning",
        soil="get the hem damp",
        keyword="muff",
        tags={"dock", "water", "cautionary"},
    ),
}

PRIZES = {
    "epee": Prize(
        id="epee",
        label="epee",
        phrase="a silver toy epee",
        region="hand",
        plural=False,
    ),
    "muff": Prize(
        id="muff",
        label="muff",
        phrase="a soft red muff",
        region="hands",
        plural=False,
    ),
}

GEAR = {
    "bucket": Gear(
        id="bucket",
        label="a tin bucket of water",
        prep="set a tin bucket of water beside the sparks",
        tail="kept the spark from growing",
        guards={"inflame"},
        covers={"dock"},
        protective=True,
    ),
    "rope": Gear(
        id="rope",
        label="a snug rope line",
        prep="tie a snug rope line near the dock edge",
        tail="kept the child back from the water",
        guards={"muff"},
        covers={"edge"},
        protective=True,
    ),
}

NAMES = ["Pip", "Mia", "Nell", "Jo", "Tom", "Ava", "Ben", "Rose"]
TRAITS = ["small", "bright-eyed", "cheery", "curious", "careful", "bold"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    for actor in world.characters():
        if actor.meters["heat"] >= THRESHOLD and actor.meters["wet"] < THRESHOLD:
            sig = ("alarm", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["alarm"] += 1
                out.append(f"The little air went hot, and everyone felt alarm.")

        if actor.meters["heat"] >= THRESHOLD:
            for item in world.worn_items(actor):
                if item.protective:
                    continue
                sig = ("soot", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["soot"] += 1
                out.append(f"{actor.id}'s {item.label} went dusty and dark.")

        if actor.meters["wet"] >= THRESHOLD:
            actor.memes["worry"] += 1

    if narrate:
        for s in out:
            world.say(s)
    return out


def can_fix(activity: Activity, prize: Prize) -> bool:
    if activity.id == "spark" and prize.id == "epee":
        return True
    if activity.id == "play" and prize.id == "muff":
        return True
    return False


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if activity.id == "spark" and prize.id == "epee":
        return GEAR["bucket"]
    if activity.id == "play" and prize.id == "muff":
        return GEAR["rope"]
    return None


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.get(prize.id)
    return {
        "soot": item.meters["soot"] >= THRESHOLD,
        "worry": sim.get(actor.id).memes["worry"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {next(t for t in [hero.type] if t)} {hero.id} with a bright little grin.")
    world.say(f"{hero.pronoun().capitalize()} loved the dock where the boards made a soft tap-tap song.")

def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {prize.label} close.")
    world.say(f"It was {prize.phrase}, and {hero.id} liked the way it shone.")

def arrive(world: World, hero: Entity) -> None:
    world.say(f"One day at {world.setting.place}, the gulls went 'caw-caw' above the water.")

def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = {"dock", "edge"}
    if activity.id == "spark":
        actor.meters["heat"] += 1
        actor.memes["boldness"] += 1
        world.say(f"{actor.id} tried to {activity.verb}, and the tiny bright spark leapt fast.")
        propagate(world, narrate=narrate)
    elif activity.id == "play":
        actor.meters["wet"] += 1
        actor.memes["care"] += 1
        world.say(f"{actor.id} wanted to {activity.verb}, where the water lapped and laughed.")
        propagate(world, narrate=narrate)
    else:
        raise StoryError("unknown activity")

def warning(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize)
    if activity.id == "spark":
        world.say(f'"A spark can {activity.danger}," said {parent.id}. "Please mind the dock."')
        return pred["soot"]
    world.say(f'"Easy, little one," said {parent.id}. "The edge is not a toy."')
    return pred["worry"] >= THRESHOLD

def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["boldness"] += 1
    world.say(f"But {hero.id} was keen to go on, and {hero.pronoun()} rushed toward the shine.")

def offer_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = choose_gear(activity, prize)
    if not gear:
        return None
    if not can_fix(activity, prize):
        return None
    world.say(f"Then {parent.id} looked wise and small, and said, '{gear.prep}.'")
    return gear

def accept(world: World, hero: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    world.say(f"{hero.id} nodded, and the little worry fell down like a leaf.")
    world.say(f"They took {gear.label}, and at once the caution was kept in place.")
    if activity.id == "spark":
        world.say(f"So the dock stayed safe, the spark did not inflame the straw, and {hero.id}'s {prize.label} stayed bright.")
    else:
        world.say(f"So {hero.id} played by the water, the {prize.label} stayed dry, and the dock kept its gentle song.")


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    parent = world.add(Entity(id="Parent", kind="character", type="parent"))
    activity = ACTIVITIES[params.activity]
    prize = world.add(Entity(id=params.prize, type="thing", label=params.prize, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    intro(world, hero)
    prize_line(world, hero, prize)
    world.para()
    arrive(world, hero)
    warning(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    do_activity(world, hero, activity)
    world.para()
    gear = offer_fix(world, parent, hero, activity, prize)
    if gear:
        world.say(f"{hero.id} agreed, and the soft little caution stayed wise.")
        accept(world, hero, prize, activity, gear)
    world.facts = {
        "hero": hero,
        "parent": parent,
        "activity": activity,
        "prize": prize,
        "gear": gear,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary nursery-rhyme story set at the dock using the word "{f["activity"].keyword}".',
        f"Tell a child-friendly rhyme about {f['hero'].id}, a {f['prize'].label}, and a warning at the dock.",
        f"Write a short nursery-style tale where a small child learns a safer way to handle {f['activity'].keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f["gear"]
    qs = [
        QAItem(
            question=f"Who was the story about at the dock?",
            answer=f"It was about {hero.id}, a little child who loved the dock and carried {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {activity.verb}, which made the moment feel risky and bright.",
        ),
        QAItem(
            question=f"Why did the parent warn {hero.id}?",
            answer=f"The parent warned {hero.id} because a spark could {activity.danger} and a careless step could lead to trouble.",
        ),
    ]
    if gear:
        qs.append(
            QAItem(
                question="What helped make the ending safe?",
                answer=f"{gear.label} helped, because it gave the story a safer way to continue at the dock.",
            )
        )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dock?",
            answer="A dock is a wooden place by the water where boats can stop and people can stand near the edge.",
        ),
        QAItem(
            question="What is a warning?",
            answer="A warning is a careful message that tells someone to stop, slow down, or be safe.",
        ),
        QAItem(
            question="What is a spark?",
            answer="A spark is a tiny flash of fire that can grow bigger if it is not watched.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk if the activity affects the region it is associated with.
at_risk(A, P) :- activity(A), prize(P), risky(A, R), region(P, R).

% A gear choice is compatible if it guards the dangerous quality and protects the region.
fix(A, P, G) :- at_risk(A, P), gear(G), guards(G, A), covers(G, R), region(P, R).

valid(Place, A, P) :- place(Place), affords(Place, A), at_risk(A, P), fix(A, P, _).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "dock"))
    lines.append(asp.fact("affords", "dock", "spark"))
    lines.append(asp.fact("affords", "dock", "play"))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risky", aid, act.danger))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for a in g.guards:
            lines.append(asp.fact("guards", gid, a))
        for r in g.covers:
            lines.append(asp.fact("covers", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in ["dock"]:
        for act_id, act in ACTIVITIES.items():
            for prize_id, pr in PRIZES.items():
                if can_fix(act, pr):
                    out.append((place, act_id, prize_id))
    return out


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    if a - b:
        print("only in ASP:", sorted(a - b))
    if b - a:
        print("only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary nursery rhyme at the dock.")
    ap.add_argument("--place", choices=["dock"], default="dock")
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams(place="dock", activity="spark", prize="epee", name="Pip", trait="curious"),
    StoryParams(place="dock", activity="play", prize="muff", name="Mia", trait="careful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "dock":
        raise StoryError("This story world only uses the dock.")
    combo_pool = valid_combos()
    if args.activity:
        combo_pool = [c for c in combo_pool if c[1] == args.activity]
    if args.prize:
        combo_pool = [c for c in combo_pool if c[2] == args.prize]
    if not combo_pool:
        raise StoryError("No valid dock story matches the requested options.")
    _, act, prize = rng.choice(combo_pool)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="dock", activity=act, prize=prize, name=name, trait=trait)


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

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1 and not args.all:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
