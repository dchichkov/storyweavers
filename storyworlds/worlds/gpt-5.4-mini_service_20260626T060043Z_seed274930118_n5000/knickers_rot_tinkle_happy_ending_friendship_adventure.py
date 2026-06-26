#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/knickers_rot_tinkle_happy_ending_friendship_adventure.py
===============================================================================================================================

A small story world about a friendship adventure with a little danger,
a rotten obstacle, a tinkle sound, and a happy ending.

Seed-inspired premise:
- Two friends set off on a tiny adventure.
- A beloved pair of knickers is at risk near something rotten.
- A bright tinkle helps guide them to safety.
- The friends solve the problem together and end with a warm, happy image.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- shared results imported eagerly
- ASP helper imported lazily
- StoryParams, registries, parser, resolve_params, generate, emit, main
- supports --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
        for k in ["rot", "dust", "joy", "fear", "friendship", "curiosity", "relief", "tension"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
    covers: set[str]
    guards: set[str]
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


SETTINGS = {
    "lane": Setting(place="the old lane", affords={"trail"}),
    "garden": Setting(place="the garden path", affords={"trail", "creek"}),
    "woods": Setting(place="the little woods", affords={"trail"}),
    "creek": Setting(place="the creek bank", affords={"creek"}),
}

ACTIVITIES = {
    "trail": Activity(
        id="trail",
        verb="explore the trail",
        gerund="exploring the trail",
        rush="dash down the trail",
        mess="dust",
        soil="dusty and dull",
        zone={"feet", "legs"},
        keyword="trail",
        tags={"adventure", "path"},
    ),
    "creek": Activity(
        id="creek",
        verb="follow the creek",
        gerund="following the creek",
        rush="hurry to the water",
        mess="rot",
        soil="stained by rot",
        zone={"feet", "legs"},
        keyword="creek",
        tags={"water", "tinkle", "rot"},
    ),
}

PRIZES = {
    "knickers": Prize(
        label="knickers",
        phrase="a favorite pair of knickers",
        type="knickers",
        region="legs",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="dryboots",
        label="dry boots",
        covers={"feet"},
        guards={"rot", "dust"},
        prep="put on dry boots first",
        tail="came back with the dry boots",
        plural=True,
    ),
    Gear(
        id="shorts",
        label="old shorts",
        covers={"legs"},
        guards={"dust"},
        prep="change into old shorts first",
        tail="came back with the old shorts",
        plural=True,
    ),
    Gear(
        id="rainboots",
        label="rain boots",
        covers={"feet"},
        guards={"rot"},
        prep="wear rain boots first",
        tail="came back with the rain boots",
        plural=True,
    ),
]

NAMES = ["Milo", "Nina", "Poppy", "Jasper", "Tia", "Robin", "Leo", "Mira"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "lively", "bold"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    if activity.mess == "rot":
        actor.meters["rot"] += 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, friend: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if name in {"Nina", "Poppy", "Tia", "Mira"} else "boy",
                            traits=["little", trait, "friendly"]))
    buddy = world.add(Entity(id=friend, kind="character", type="girl" if friend in {"Nina", "Poppy", "Tia", "Mira"} else "boy",
                             traits=["little", "kind"]))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=buddy.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["friendship"] += 1
    buddy.memes["friendship"] += 1
    world.say(
        f"{hero.id} and {buddy.id} were two little friends who loved a brave adventure together."
    )
    world.say(
        f"{hero.id} packed {hero.pronoun('possessive')} {prize.label} and smiled at the bright morning."
    )
    world.say(
        f"They set off for {world.setting.place}, where the air felt lively and full of surprises."
    )

    world.para()
    world.say(
        f"Near the path, they heard a tiny tinkle from a bell on a fence, and both friends paused to listen."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {buddy.id} pointed to a rotten old plank near the way."
    )

    _do_activity(world, hero, activity)
    if prize_at_risk(activity, prize):
        prize.meters[activity.mess] += 1
        prize.meters["rot"] += 1
        hero.memes["tension"] += 1
        buddy.memes["tension"] += 1
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {prize.label} could get {activity.soil} if they rushed ahead."
        )
        world.say(
            f"{buddy.id} held up a hand and said they should choose a safer way so the adventure could stay happy."
        )

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No friendly gear could protect the prize in this story world.")

    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=buddy.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id

    hero.memes["curiosity"] += 1
    buddy.memes["friendship"] += 1
    world.say(
        f"{buddy.id} smiled and said, \"{gear.prep}, and then we can go on together.\""
    )
    world.say(
        f"{hero.id} nodded, and the two friends came back with the {gear.label}, ready for the safe part of the trail."
    )
    world.say(
        f"At last, {hero.id} went {activity.gerund} while {prize.label} stayed clean and the rotten spot was left behind."
    )
    world.say(
        f"The little tinkle sounded again from the fence, and the friends laughed all the way home."
    )

    hero.memes["joy"] += 1
    buddy.memes["relief"] += 1
    buddy.memes["friendship"] += 1

    world.facts.update(
        hero=hero,
        buddy=buddy,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
        conflict=True,
        tinkle=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, buddy, act, prize = f["hero"], f["buddy"], f["activity"], f["prize"]
    return [
        f'Write a short adventure story for a young child that includes the words "knickers", "rot", and "tinkle".',
        f"Tell a friendship adventure where {hero.id} and {buddy.id} want to {act.verb} but must protect {hero.pronoun('possessive')} {prize.label}.",
        f"Write a happy ending story about two friends, a rotten obstacle, and a tiny tinkle that helps them choose a safe path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, buddy, act, prize, gear = f["hero"], f["buddy"], f["activity"], f["prize"], f["gear"]
    return [
        QAItem(
            question=f"Who went on the adventure together?",
            answer=f"{hero.id} and {buddy.id} went on the adventure together as close friends.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the trail?",
            answer=f"{hero.id} wanted to {act.verb}, but {buddy.id} noticed a rotten danger first.",
        ),
        QAItem(
            question=f"What did they protect during the story?",
            answer=f"They protected {hero.pronoun('possessive')} {prize.label} so it would not get ruined by rot.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the two friends coming back together after choosing the safe path.",
        ),
        QAItem(
            question=f"What helped them decide to slow down?",
            answer=f"A tiny tinkle from a bell helped them pause and listen before rushing ahead.",
        ),
        QAItem(
            question=f"What gear helped the hero keep going safely?",
            answer=f"{gear.label} helped {hero.id} keep going safely while the {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rot?",
            answer="Rot is what happens when something old or damp starts to decay and become soft or broken.",
        ),
        QAItem(
            question="What can a tinkle sound like?",
            answer="A tinkle can sound like a small bell or a tiny piece of metal making a light, bright sound.",
        ),
        QAItem(
            question="What are knickers?",
            answer="Knickers are a kind of clothing worn on the lower body.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="creek", prize="knickers", name="Milo", friend="Nina", trait="curious"),
    StoryParams(place="woods", activity="trail", prize="knickers", name="Poppy", friend="Leo", trait="brave"),
    StoryParams(place="lane", activity="trail", prize="knickers", name="Tia", friend="Jasper", trait="cheerful"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
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
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship adventure with knickers, rot, and a tinkle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.friend, params.trait)
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
        print(f"{len(combos)} compatible combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:8} {prize:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
