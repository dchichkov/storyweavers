#!/usr/bin/env python3
"""
A small story world for an intense bedtime comedy: a child, a stubborn zipper,
a lullaby, and a kind fix.

The seed premise is simple:
- something bedtime-related becomes unusually intense,
- a zipper gets stuck at the wrong moment,
- a lullaby helps soften the mood,
- kindness turns the mishap into a funny, happy ending.

The simulated world tracks:
- physical meters: stuckness, snugness, noise, tiredness, looseness
- emotional memes: worry, giggles, kindness, relief, patience, comfort

The story is not a frozen template. It is built from a live state machine:
1) setup and desire,
2) tension from the stuck zipper,
3) lullaby + kindness as a compatible fix,
4) resolution image proving the change.
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

# Story contract: model typed entities with meters and memes.
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
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    result: str
    mess: str
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
class Fix:
    id: str
    label: str
    action: str
    effect: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _set_mem(ent: Entity, key: str, val: float) -> None:
    ent.memes[key] = val


def is_stuck(prize: Prize, activity: Activity) -> bool:
    return prize.region in activity.zone


def compatible_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if activity.keyword in fx.guards and prize.region in fx.covers:
            return fx
    return None


def setup_world(setting: Setting, activity: Activity, prize: Prize,
                hero_name: str, hero_type: str, parent_type: str,
                trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
        meters={"tired": 0.0, "snug": 0.0},
        memes={"worry": 0.0, "giggles": 0.0, "kindness": 0.0, "comfort": 0.0, "patience": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={"tired": 0.0},
        memes={"kindness": 0.0, "patience": 0.0, "relief": 0.0},
    ))
    item = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize.region,
        plural=prize.plural,
        meters={"stuck": 0.0, "snug": 1.0},
    ))
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label="the blanket",
        phrase="a soft bedtime blanket",
        owner=hero.id,
        caretaker=parent.id,
        meters={"warm": 1.0},
        memes={"comfort": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, prize=item, activity=activity, setting=setting, blanket=blanket)
    return world


def _scene_intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    prize: Entity = world.facts["prize"]
    activity: Activity = world.facts["activity"]
    setting: Setting = world.facts["setting"]
    world.say(
        f"{hero.id} was a little {hero.traits[-1]} {hero.type} who loved bedtime because "
        f"the room felt safe and soft."
    )
    world.say(
        f"{hero.id} also loved {activity.gerund}, especially when {prize.label} had to be "
        f"pulled just right."
    )
    world.say(
        f"That night, {hero.id}'s {parent.type if parent.type in {'mother', 'father'} else 'parent'} had helped "
        f"with pajamas in {setting.place} and smiled at the sleepy, cozy mess of blankets."
    )


def _start_activity(world: World) -> None:
    hero: Entity = world.facts["hero"]
    activity: Activity = world.facts["activity"]
    prize: Entity = world.facts["prize"]
    world.para()
    world.say(
        f"Then {hero.id} wanted to {activity.verb}, but the {prize.label} was already "
        f"caught in an awkward little twist."
    )
    _add_mem(hero, "worry", 1.0)
    _add_meter(prize, "stuck", 1.0)
    _add_meter(hero, "tired", 1.0)
    _add_meter(hero, "snug", 1.0)


def _intensify(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    prize: Entity = world.facts["prize"]
    activity: Activity = world.facts["activity"]
    if _meter(prize, "stuck") >= THRESHOLD:
        world.say(
            f"{hero.id} gave the zipper a brave tug, and it answered with a very dramatic zzzzt."
        )
        _add_mem(hero, "worry", 1.0)
        _add_mem(hero, "giggles", 1.0)
        _add_meter(hero, "noise", 1.0)
        _add_meter(prize, "stuck", 0.5)
        world.say(
            f"{parent.id} looked over, tried not to laugh, and said, "
            f"\"That zipper sounds intense for something so tiny.\""
        )
        _add_mem(parent, "kindness", 1.0)
        _add_mem(parent, "patience", 1.0)
        world.say(
            f"{hero.id} tried again, but the snag only made the moment feel even more intense."
        )
        _add_meter(hero, "tired", 1.0)
        _add_mem(hero, "worry", 1.0)
        world.facts["tension"] = True
        world.facts["activity_line"] = activity.verb


def _lullaby_and_kindness(world: World) -> Optional[Fix]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    prize: Entity = world.facts["prize"]
    activity: Activity = world.facts["activity"]
    fix = compatible_fix(activity, prize)
    if fix is None:
        raise StoryError("No compatible lullaby-kindness fix exists for this scene.")

    world.para()
    world.say(
        f"Then {parent.id} started a soft lullaby, the kind that makes a wrinkly frown forget its job."
    )
    _add_mem(hero, "comfort", 1.0)
    _add_mem(hero, "patience", 1.0)
    _add_meter(hero, "noise", -0.5)
    world.say(
        f"The tune was calm, but the situation stayed funny: {hero.id} hummed along while keeping "
        f"a careful finger on the stubborn {prize.label}."
    )
    world.say(
        f"With a kind little smile, {parent.id} followed the zipper's seam, took a breath, and tried again."
    )
    _add_mem(parent, "kindness", 1.0)
    _add_mem(parent, "patience", 1.0)
    _add_meter(prize, "stuck", -1.0)
    _add_meter(prize, "snug", 1.0)
    _add_mem(hero, "giggles", 1.0)
    world.say(
        f"This time the {prize.label} slid open with a cheerful zip, as if it had finally remembered how to be helpful."
    )
    world.facts["fix"] = fix
    return fix


def _resolution(world: World, fix: Fix) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    prize: Entity = world.facts["prize"]
    activity: Activity = world.facts["activity"]
    _set_mem(hero, "worry", 0.0)
    _add_mem(hero, "relief", 1.0)
    _add_mem(parent, "relief", 1.0)
    _add_meter(hero, "snug", 1.0)
    world.para()
    world.say(
        f"{hero.id} laughed so hard that the blanket bobbed like a tiny boat."
    )
    world.say(
        f"Then {hero.id} got back to {activity.gerund}, with the {prize.label} finally behaving and "
        f"{parent.id} still humming the last note of the lullaby."
    )
    world.say(
        f"At the end, the zipper was fixed, the room was cozy, and the whole bedtime adventure felt "
        f"more silly than scary."
    )


def tell(setting: Setting, activity: Activity, prize: Prize,
         hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = setup_world(setting, activity, prize, hero_name, hero_type, parent_type, trait)
    _scene_intro(world)
    _start_activity(world)
    _intensify(world)
    fix = _lullaby_and_kindness(world)
    _resolution(world, fix)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", cozy=True, affords={"lullaby", "zipper"}),
    "nursery": Setting(place="the nursery", cozy=True, affords={"lullaby", "zipper"}),
    "sleepover": Setting(place="the sleepover corner", cozy=True, affords={"lullaby", "zipper"}),
}

ACTIVITIES = {
    "zipper": Activity(
        id="zipper",
        verb="zip up the bedtime blanket",
        gerund="zipping the blanket",
        rush="yank the zipper fast",
        result="the zipper finally slides",
        mess="stuck",
        zone={"torso"},
        keyword="zipper",
        tags={"zipper", "bedtime", "comedy"},
    ),
    "lullaby": Activity(
        id="lullaby",
        verb="sing the lullaby louder",
        gerund="singing a lullaby",
        rush="rush the last verse",
        result="the room turns calm",
        mess="noise",
        zone={"torso"},
        keyword="lullaby",
        tags={"lullaby", "bedtime", "kindness", "comedy"},
    ),
}

PRIZES = {
    "blanket": Prize(
        label="blanket",
        phrase="a soft bedtime blanket with one zippy zipper",
        type="blanket",
        region="torso",
    ),
    "pajamas": Prize(
        label="pajamas",
        phrase="striped pajamas with a sticky zipper",
        type="pajamas",
        region="torso",
        plural=True,
    ),
}

FIXES = [
    Fix(
        id="kind_song",
        label="a kind lullaby",
        action="sing softly and help with the zipper",
        effect="calm the room and loosen the snag",
        guards={"zipper"},
        covers={"torso"},
    ),
    Fix(
        id="gentle_help",
        label="gentle kindness",
        action="pause, sing, and tug carefully together",
        effect="make the zipper behave",
        guards={"zipper"},
        covers={"torso"},
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Finn", "Leo", "Owen"]
TRAITS = ["curious", "cheerful", "sleepy", "brave", "bouncy", "silly"]

CURATED = [
    ("bedroom", "zipper", "blanket", "Milo", "boy", "mother", "curious"),
    ("nursery", "zipper", "pajamas", "Nora", "girl", "father", "cheerful"),
    ("sleepover", "zipper", "blanket", "Theo", "boy", "mother", "silly"),
]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for activity in ACTIVITIES:
            for prize in PRIZES:
                if activity == "zipper" and prize in {"blanket", "pajamas"}:
                    combos.append((place, activity, prize))
                if activity == "lullaby" and prize in {"blanket", "pajamas"}:
                    combos.append((place, activity, prize))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    activity: Activity = f["activity"]
    prize: Entity = f["prize"]
    return [
        f'Write a short funny bedtime story for a child named {hero.id} that includes the word "{activity.keyword}".',
        f"Tell a comedy where a little {hero.type} tries to {activity.verb} but a {prize.label} zipper gets stuck, and kindness helps.",
        f'Write a gentle, intense-but-silly story using the word "{activity.keyword}" and ending with a lullaby.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {activity.verb}. The zipper got stuck, so the job turned into a funny little struggle.",
        ),
        QAItem(
            question=f"Why did the bedtime moment feel intense?",
            answer=f"It felt intense because the {prize.label} zipper would not move at first, so {hero.id} had to tug, pause, and try again.",
        ),
        QAItem(
            question=f"What helped the zipper loosen?",
            answer=f"A kind lullaby and gentle help from {parent.id} loosened the snag. The calm song and careful tug made the zipper slide open.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} laughing, the {prize.label} working again, and bedtime feeling cozy instead of stressful.",
        ),
        QAItem(
            question=f"What kind of fix did the parent use?",
            answer=f"{parent.id} used {fix.label}: {fix.effect}. That was the compatible answer to the stuck zipper problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lullaby?",
            answer="A lullaby is a soft song people sing to help someone feel calm and sleepy.",
        ),
        QAItem(
            question="What does a zipper do?",
            answer="A zipper joins two sides of cloth together and can open or close with a little pull.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: v for k, v in e.memes.items() if abs(v) > 0}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def explain_rejection(activity: str, prize: str) -> str:
    return f"(No story: {activity} and {prize} are not a compatible bedtime comedy pair.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy story world about a stuck zipper, a lullaby, and kindness.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if True else True]
    filtered = []
    for c in valid_combos():
        if args.place is not None and c[0] != args.place:
            continue
        if args.activity is not None and c[1] != args.activity:
            continue
        if args.prize is not None and c[2] != args.prize:
            continue
        filtered.append(c)
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(filtered)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.prize and args.gender not in PRIZES[prize].genders:
        raise StoryError("Chosen prize does not fit the requested gender.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
% A prize is at risk when the activity touches its region.
risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).

% A fix is compatible when it handles the activity's keyword and covers the region.
fixable(A,P,F) :- risk(A,P), fix(F), handles(F,A), covers(F,R), worn_on(P,R).

compatible(Place,A,P) :- setting(Place), affords(Place,A), risk(A,P), fixable(A,P,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in SETTINGS[sid].affords:
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("handles", "kind_song", a.keyword))
        lines.append(asp.fact("handles", "gentle_help", a.keyword))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for r in fx.covers:
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, activity, prize, name, gender, parent, trait in CURATED:
            samples.append(generate(StoryParams(place, activity, prize, name, gender, parent, trait)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
