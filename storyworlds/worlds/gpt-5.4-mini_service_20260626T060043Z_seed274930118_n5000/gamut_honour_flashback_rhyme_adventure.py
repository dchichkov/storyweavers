#!/usr/bin/env python3
"""
storyworlds/worlds/gamut_honour_flashback_rhyme_adventure.py
=============================================================

A small adventure storyworld about a young explorer, a risky route, a remembered
rhyme, and a finish that earns honour.

Seed tale:
---
A child explorer wanted to cross a bright trail called the Gamut Path to bring
home an honour badge from the ridge shrine. The path was blocked by a shaky rope
bridge over a windy gap. The child almost turned back, but remembered a rhyme
taught by a grandparent in a flashback: slow steps, quiet breath, look ahead.
With that rhythm, the child crossed safely, helped a friend at the middle plank,
and reached the shrine with the badge still shining.

World model:
---
* physical meters: balance, stamina, windwear, trail progress, item wear
* emotional memes: courage, worry, honour, memory, delight

Story beats:
---
1. Setup: an adventurer, a prized honour token, and a vivid route full of gamut.
2. Tension: the route is unsafe; a flashback brings back a guiding rhyme.
3. Turn: the hero uses the rhyme, steadies balance, and helps someone else.
4. Resolution: the badge is earned, honour rises, and the ending image proves it.

The script supports:
- default story generation
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp
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
# Domain model
# ---------------------------------------------------------------------------
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        return any(region in g.meters.get("covers", set()) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ridge": Setting(place="the ridge trail", outdoors=True, affords={"bridge", "steps"}),
    "woods": Setting(place="the bright woods", outdoors=True, affords={"bridge", "steps", "stream"}),
    "harbor": Setting(place="the harbor path", outdoors=True, affords={"bridge", "stream"}),
}

ACTIVITIES = {
    "bridge": Activity(
        id="bridge",
        verb="cross the rope bridge",
        gerund="crossing the rope bridge",
        rush="run onto the bridge",
        hazard="windy and shaky",
        zone={"feet", "hands", "torso"},
        keyword="bridge",
        tags={"wind", "rope"},
    ),
    "steps": Activity(
        id="steps",
        verb="climb the stone steps",
        gerund="climbing the stone steps",
        rush="hurry up the steps",
        hazard="steep and slippery",
        zone={"feet", "hands"},
        keyword="steps",
        tags={"stone", "step"},
    ),
    "stream": Activity(
        id="stream",
        verb="cross the stream",
        gerund="crossing the stream",
        rush="dash into the water",
        hazard="cold and splashy",
        zone={"feet", "legs"},
        keyword="stream",
        tags={"water", "stream"},
    ),
}

PRIZES = {
    "badge": Prize(
        id="badge",
        label="honour badge",
        phrase="a bright honour badge",
        region="torso",
    ),
    "scarf": Prize(
        id="scarf",
        label="honour scarf",
        phrase="a blue honour scarf",
        region="torso",
    ),
    "boots": Prize(
        id="boots",
        label="trail boots",
        phrase="sturdy trail boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="rope_gloves",
        label="rope gloves",
        covers={"hands"},
        guards={"rope"},
        prep="put on rope gloves first",
        tail="slipped on the rope gloves and tried again",
    ),
    Gear(
        id="trail_boots",
        label="trail boots",
        covers={"feet"},
        guards={"water", "stone"},
        prep="lace up the trail boots",
        tail="laced up the trail boots and went on",
        plural=True,
    ),
    Gear(
        id="sash",
        label="a bright sash",
        covers={"torso"},
        guards={"wind"},
        prep="tie on a bright sash",
        tail="tied on the bright sash and stepped out",
    ),
]

GIRL_NAMES = ["Mina", "Tia", "Nora", "Lia", "Ava", "Zia"]
BOY_NAMES = ["Eli", "Tom", "Nico", "Ben", "Arlo", "Finn"]
TRAITS = ["brave", "careful", "curious", "bold", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
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


CURATED = [
    StoryParams(place="ridge", activity="bridge", prize="badge", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="woods", activity="steps", prize="scarf", name="Eli", gender="boy", parent="father", trait="steady"),
    StoryParams(place="harbor", activity="stream", prize="boots", name="Nora", gender="girl", parent="mother", trait="curious"),
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or (activity.id == "bridge" and prize.region == "torso")


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id == "bridge" and "wind" in gear.guards and prize.region in gear.covers:
            return gear
        if activity.id == "steps" and "stone" in gear.guards and prize.region in gear.covers:
            return gear
        if activity.id == "stream" and "water" in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# World simulation helpers
# ---------------------------------------------------------------------------
def story_intro(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} young adventurer who loved the gamut of colors on the trail."
    )
    world.say(
        f"{hero.id}'s {parent.type} had given {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} like a little promise of honour."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} set out for {world.setting.place}, where {act.verb} was part of the adventure."
    )


def flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"At the bridge, the boards swayed, and a flashback drifted into {hero.id}'s mind."
    )
    world.say(
        f"{hero.id} remembered a grandparent beside a little kitchen table, tapping a spoon and singing a rhyme: 'Slow feet, soft breath, look ahead, not beneath.'"
    )


def warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> None:
    world.say(
        f'"That bridge is {act.hazard}," {hero.pronoun("possessive")} {parent.type} said. "If you rush, your {prize.label} could be ruined."'
    )


def resolve_with_rhyme(world: World, hero: Entity, parent: Entity, act: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["courage"] += 2
    hero.memes["worry"] = 0
    hero.meters["balance"] += 2
    hero.meters["progress"] += 1
    hero.meters["wear"] += 0.2
    world.say(
        f"{hero.id} whispered the rhyme under {hero.pronoun('possessive')} breath and {gear.prep}."
    )
    world.say(
        f"With each careful step, {hero.pronoun('subject')} crossed the {act.id} and kept {prize.it()} dry and bright."
    )
    hero.memes["honour"] += 1
    world.say(
        f"At the middle plank, {hero.id} noticed a smaller child wobbling, so {hero.pronoun('subject')} held out a hand and helped {hero.pronoun('object')} over."
    )
    world.say(
        f"By the time they reached the shrine, {hero.id}'s {prize.label} still shone, and the whole path felt full of honour."
    )


# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + hero_traits, meters={"balance": 0.0, "progress": 0.0, "wear": 0.0}, memes={"courage": 1.0, "worry": 0.0, "honour": 0.0, "memory": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    gear = None

    story_intro(world, hero, parent, prize, activity)
    world.para()
    warn(world, parent, hero, activity, prize)
    flashback(world, hero)
    world.para()

    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No compatible gear exists for this adventure.")
    world.say(
        f"{hero.id} found {gear.label if gear.label.startswith('a ') else 'the ' + gear.label} in the pack."
    )
    resolve_with_rhyme(world, hero, parent, activity, prize, gear)
    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": activity,
        "gear": gear,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short adventure story for a child named {hero.id} who faces a {act.hazard} {act.id} route and remembers a rhyme.',
        f"Tell a gentle adventure where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} {parent.type} worries about {prize.phrase} and honour.",
        f'Write a child-friendly story with a flashback and a rhyme, ending with {hero.id} earning an honour prize on the trail.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize, gear = f["hero"], f["parent"], f["activity"], f["prize"], f["gear"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} on the adventure path.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.type} worry about the trip?",
            answer=f"{parent.type.capitalize()} worried because the route was {act.hazard}, and the {prize.label} could have been ruined.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going after the flashback?",
            answer=f"The remembered rhyme helped {hero.id} stay calm, use {gear.label}, and keep the {prize.label} safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} crossed the route safely, helped another child, and earned honour while the {prize.label} stayed bright.",
        ),
    ]


KNOWLEDGE = {
    "wind": [
        ("What does wind do?", "Wind is moving air. It can push leaves, ripple water, and make a bridge sway."),
    ],
    "rope": [
        ("What is rope used for?", "Rope can help people tie things, climb, or make a bridge safer to hold onto."),
    ],
    "stone": [
        ("Why can stone steps be slippery?", "Stone steps can be slippery when they are wet or dusty, so careful feet are important."),
    ],
    "water": [
        ("Why should you be careful near water?", "Water can be cold, deep, or fast, so children should move carefully and stay with a grown-up."),
    ],
    "stream": [
        ("What is a stream?", "A stream is a small, moving flow of water that runs over rocks and through land."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ("wind", "rope", "stone", "water", "stream"):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), zone(A,R), region(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), hazard_of(A,M), covers(G,R), zone(A,R), region(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
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
        lines.append(asp.fact("hazard_of", aid, a.keyword if aid != "stream" else "water"))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for h in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with flashback and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} and {prize.label} do not form a reasonable adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    prize_cfg = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_cfg.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
