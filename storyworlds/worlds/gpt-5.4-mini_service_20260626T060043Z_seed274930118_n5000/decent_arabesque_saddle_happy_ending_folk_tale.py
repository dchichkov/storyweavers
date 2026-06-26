#!/usr/bin/env python3
"""
storyworlds/worlds/decent_arabesque_saddle_happy_ending_folk_tale.py
====================================================================

A small folk-tale storyworld about a child, a proud pony, and a fancy saddle
with arabesque stitching. The tale stays gentle and practical: someone wants to
ride, someone worries about safety, and a decent fix leads to a happy ending.

Seed words:
- decent
- arabesque
- saddle

Style:
- Folk tale
- Happy ending
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    mounted_on: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["slip", "dust", "speed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "trust", "calm", "delight"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "maiden"}
        male = {"boy", "father", "grandfather", "man", "groom"}
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
    tone: str = "folk"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    gives: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def mounted_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.mounted_on == actor.id]


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for rider in world.characters():
        if rider.meters["speed"] < THRESHOLD:
            continue
        for item in world.mounted_items(rider):
            if item.protective:
                continue
            if "back" not in world.zone:
                continue
            sig = ("slip", rider.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["slip"] += 1
            out.append(f"{rider.id}'s {item.label} began to slip.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["slip"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That gave {carer.label} a worried look.")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    for rider in world.characters():
        if rider.memes["calm"] < THRESHOLD:
            continue
        sig = ("trust", rider.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        rider.memes["trust"] += 1
        out.append(f"{rider.id} felt steadier after hearing the kind plan.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in [_r_slip, _r_worry, _r_trust]:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and "slip" in gear.gives:
            return gear
    return None


def predict(world: World, rider: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(rider.id).meters["speed"] += 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return {"slip": bool(prize.meters["slip"] >= THRESHOLD)}


SETTINGS = {
    "meadow": Setting(place="the green meadow", affords={"ride", "gallop"}),
    "barnyard": Setting(place="the quiet barnyard", affords={"ride"}),
    "hillroad": Setting(place="the hill road", affords={"ride", "parade"}),
}

ACTIVITIES = {
    "ride": Activity(
        id="ride",
        verb="ride along the lane",
        gerund="riding along the lane",
        rush="set off at a trot",
        risk="the saddle might slide on the back",
        weather="clear",
        zone={"back"},
        keyword="saddle",
        tags={"saddle", "pony"},
    ),
    "parade": Activity(
        id="parade",
        verb="join the village parade",
        gerund="joining the village parade",
        rush="hurry into the procession",
        risk="the saddle might shift when the pony stepped lively",
        weather="clear",
        zone={"back"},
        keyword="parade",
        tags={"saddle", "village"},
    ),
    "gallop": Activity(
        id="gallop",
        verb="gallop by the willow trees",
        gerund="galloping by the willow trees",
        rush="spur the pony into a swift gallop",
        risk="the saddle might wobble in the rush",
        weather="clear",
        zone={"back"},
        keyword="willow",
        tags={"saddle"},
    ),
}

PRIZES = {
    "saddle": Prize(
        label="saddle",
        phrase="a decent saddle with arabesque carvings",
        type="saddle",
        region="back",
    )
}

GEAR = [
    Gear(
        id="girth",
        label="a sturdy girth strap",
        covers={"back"},
        gives={"slip"},
        prep="tighten the girth strap first",
        tail="tightened the girth strap and checked the saddle once more",
    ),
    Gear(
        id="blanket",
        label="a soft saddle blanket",
        covers={"back"},
        gives={"slip"},
        prep="lay a saddle blanket under it",
        tail="laid the saddle blanket and settled the saddle gently",
    ),
]

NAMES = ["Mira", "Tobin", "Anya", "Perrin", "Mabel", "Rowan"]
TRAITS = ["decent", "brave", "kind", "careful", "cheerful", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type="child", traits=[trait, "little"]))
    elder = world.add(Entity(id="elder", kind="character", type="grandmother", label="Grandmother"))
    pony = world.add(Entity(id="pony", kind="character", type="pony", label="the pony"))
    saddle = world.add(Entity(
        id="saddle", type="saddle", label="saddle",
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
        mounted_on=pony.id, region=prize_cfg.region, meters={"slip": 0.0}, memes={}
    ))

    world.say(f"Once, in {setting.place}, there lived a {trait} child named {hero.id}.")
    world.say(f"{hero.id} loved {activity.gerund}, and {hero.id} also treasured the {prize_cfg.label} with arabesque carvings.")
    world.say(f"Grandmother said the {prize_cfg.label} was decent enough for a special day, but it must stay fixed on the pony.")

    world.para()
    world.say(f"One clear morning, {hero.id} and {hero.pronoun('possessive')} Grandmother went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, and the pony stamped as if it wanted to come too.")
    world.say(f"But Grandmother looked at the {prize_cfg.label} and said, \"Mind the back; {activity.risk}.\"")
    hero.meters["speed"] += 1
    world.zone = set(activity.zone)
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.id} paused, then chose a decent way forward instead of a hasty one.")
    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError("No fitting gear exists for this tale.")
    world.add(Entity(
        id=gear.id, type="gear", label=gear.label, protective=True,
        owner=hero.id, caretaker=elder.id, covers=set(gear.covers)
    )).worn_by = hero.id

    world.say(f"Grandmother helped: she said to {gear.prep}.")
    world.say(f"Then she {gear.tail}.")
    hero.memes["calm"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"At last, {hero.id} rode out with a happy heart, and the {prize_cfg.label} stayed true on the pony's back.")
    world.say(f"They {activity.gerund}, and the lane seemed to smile with them.")
    world.say(f"By evening, the village remembered a tiny, decent, arabesque thing that led to a happy ending.")

    world.facts.update(hero=hero, elder=elder, pony=pony, saddle=saddle, gear=gear, activity=activity, prize_cfg=prize_cfg)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short folk tale for a child about "{hero.id}", a {act.keyword}, and an arabesque {prize.label}.',
        f"Tell a happy-ending story where {hero.id} wants to {act.verb} but must keep the {prize.label} decent and safe.",
        f'Write a gentle village tale that includes the words "decent", "arabesque", and "{prize.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    act = f["activity"]
    prize = f["prize_cfg"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the tale?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.pronoun('subject')} loved the feeling of a pony ride and the open road.",
        ),
        QAItem(
            question=f"What special thing did {hero.id} care about?",
            answer=f"{hero.id} cared about the {prize.label} with arabesque carvings, because it was a decent-looking saddle for a special day.",
        ),
        QAItem(
            question=f"Why did Grandmother warn {hero.id}?",
            answer=f"Grandmother warned {hero.id} because if the pony moved too fast, the {prize.label} could slip on the back.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {gear.label} so the {prize.label} stayed fixed, and {hero.id} could ride safely.",
        ),
        QAItem(
            question=f"How did the tale end?",
            answer=f"It ended happily, with {hero.id} riding out, Grandmother pleased, and the {prize.label} resting steady on the pony.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "saddle": [
        QAItem(
            question="What is a saddle for?",
            answer="A saddle is a seat that helps a rider sit on a horse or pony more safely and comfortably.",
        ),
    ],
    "pony": [
        QAItem(
            question="What is a pony?",
            answer="A pony is a small horse.",
        ),
    ],
    "girth": [
        QAItem(
            question="What does a girth strap do?",
            answer="A girth strap helps hold a saddle in place under a horse's belly.",
        ),
    ],
    "blanket": [
        QAItem(
            question="Why put a blanket under a saddle?",
            answer="A saddle blanket can help the saddle sit more softly and keep the horse more comfortable.",
        ),
    ],
    "arabesque": [
        QAItem(
            question="What is an arabesque pattern?",
            answer="An arabesque pattern is a curving, swirly design often made of leaves, vines, or graceful lines.",
        ),
    ],
    "decent": [
        QAItem(
            question="What does decent mean?",
            answer="Decent can mean polite, proper, or good enough to be trusted.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("saddle")
    tags.add("pony")
    out: list[QAItem] = []
    for tag in ["decent", "arabesque", "saddle", "pony", "girth", "blanket"]:
        if tag in tags or tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.mounted_on:
            bits.append(f"mounted_on={e.mounted_on}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), fixes(G,A).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for a in sorted(ACTIVITIES):
            if "slip" in g.gives:
                lines.append(asp.fact("fixes", g.id, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} would affect the {prize.label}, but no decent fix fits this folk-tale setup.)"
    )


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="meadow", activity="ride", prize="saddle", name="Mira", trait="decent"),
    StoryParams(place="barnyard", activity="ride", prize="saddle", name="Tobin", trait="careful"),
    StoryParams(place="hillroad", activity="parade", prize="saddle", name="Anya", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a saddle, a child, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
