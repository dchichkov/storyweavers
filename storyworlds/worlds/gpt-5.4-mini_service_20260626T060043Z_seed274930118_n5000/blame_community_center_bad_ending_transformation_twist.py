#!/usr/bin/env python3
"""
storyworlds/worlds/blame_community_center_bad_ending_transformation_twist.py
============================================================================

A standalone story world for a tall-tale community-center story with blame,
a bad ending turn, a transformation, and a twist.

Seed premise:
---
At the community center, a small hero gets blamed for a big mess during a public
project. The day seems headed for a bad ending, until the real cause is revealed
and the mess transforms into something useful and surprising.
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

COMMUNITY_CENTER = "the community center"
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dusty", "painted", "dirty", "broken", "fixed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "blame", "pride", "relief", "confusion", "wonder"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = COMMUNITY_CENTER
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def story_sentence(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p).strip()


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["painted"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["painted"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.id}'s {item.label} got painted and dirty.")
    return out


def _r_blame(world: World) -> list[str]:
    out: list[str] = []
    blamed = world.facts.get("blamed")
    if not blamed:
        return out
    hero = world.get(blamed)
    if hero.memes["blame"] >= THRESHOLD and hero.memes["fear"] >= THRESHOLD:
        sig = ("blame", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__blame__")
    return out


CAUSAL_RULES = [_r_spill, _r_blame]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__blame__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.facts = dict(world.facts)
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters[activity.mess] += 1
    simulate_spill(sim, actor, activity)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["dirty"] >= THRESHOLD}


def simulate_spill(world: World, actor: Entity, activity: Activity) -> None:
    for item in world.worn_items(actor):
        if item.protective or item.region not in activity.zone:
            continue
        if world.covered(actor, item.region):
            continue
        item.meters["dirty"] += 1
        item.meters[activity.mess] += 1


def introduction(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a tall-tale heart, and {helper.id} was the kind of helper who could lift a smile as easy as a bucket."
    )


def setup(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"At {COMMUNITY_CENTER}, {hero.id} loved to {activity.verb}, especially when the room smelled like paint and hope."
    )
    world.say(
        f"{helper.id} had brought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} like a treasure from a parade wagon."
    )


def warning(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"Then the big mural ladder creaked, the paint bucket tipped, and a blue splash raced across the floor like a river with boots on."
    )
    world.say(
        f"{helper.id} looked at {hero.id}'s {prize.label} and said, 'If you keep painting now, that {prize.label} will end up {activity.soil}.'"
    )


def blame_scene(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["blame"] += 1
    hero.memes["fear"] += 1
    world.facts["blamed"] = hero.id
    world.say(
        f"Some of the grown-ups pointed at {hero.id} and blamed {hero.pronoun('object')} for the splash."
    )
    world.say(
        f"The day looked headed for a bad ending, the kind that hangs over a room like a wet coat."
    )


def twist_scene(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Then came the twist: the paint had not started with {hero.id} at all."
    )
    world.say(
        f"A loose ceiling fan had spun the old tarp, flung the brush, and sent the blue paint flying like a startled jay."
    )
    hero.memes["confusion"] += 1
    hero.memes["wonder"] += 1
    hero.memes["blame"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1


def transformation_scene(world: World, hero: Entity, helper: Entity, prize: Entity, gear: Gear) -> None:
    hero.meters["painted"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{helper.id} laughed a thunder-laugh and brought out {gear.label}."
    )
    world.say(
        f"{hero.id} pulled it on, and the messy splash transformed into the start of a brand-new mural: a blue river, a gold sun, and three dancing ducks big enough to make a lion grin."
    )


def ending(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"By sunset, {hero.id} was {activity.gerund}, {prize.phrase} stayed clean, and the room looked brighter than a kite on a windy hill."
    )
    world.say(
        f"The bad ending had turned inside out, and the whole community center stood smiling under the new wall of paint."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mabel",
         hero_type: str = "girl", helper_name: str = "Mr. Otis", helper_type: str = "man") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    gear = world.add(Entity(
        id="smock",
        type="gear",
        label="an old paint smock",
        protective=True,
        covers={"torso"},
        plural=False,
        owner=hero.id,
    ))
    gear.worn_by = hero.id

    introduction(world, hero, helper)
    world.para()
    setup(world, hero, helper, prize, activity)
    warning(world, hero, helper, prize, activity)
    blame_scene(world, hero, helper)
    world.para()
    twist_scene(world, hero, helper)
    transformation_scene(world, hero, helper, prize, GEAR[0])
    ending(world, hero, helper, prize, activity)

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, gear=GEAR[0], setting=setting)
    return world


SETTINGS = {
    "community_center": Setting(place=COMMUNITY_CENTER, affords={"mural"}),
}

ACTIVITIES = {
    "mural": Activity(
        id="mural",
        verb="paint the mural",
        gerund="painting murals",
        rush="dash for the paint",
        mess="painted",
        soil="covered in paint",
        zone={"torso"},
        keyword="blame",
        tags={"paint", "twist", "transformation", "blame"},
    )
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a neat apron", type="apron", region="torso"),
    "sneakers": Prize(label="sneakers", phrase="bright white sneakers", type="sneakers", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="smock",
        label="an old paint smock",
        covers={"torso"},
        guards={"painted"},
        prep="put on the old paint smock",
        tail="pulled the smock on",
    ),
]

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Ada", "June", "Ivy"]
BOY_NAMES = ["Otis", "Eli", "Benn", "Tom", "Cal", "Noel"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale community-center story world with blame, twist, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or "community_center"
    activity = args.activity or "mural"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    if args.gender and args.gender not in PRIZES[prize].genders:
        raise StoryError("That prize does not fit the chosen hero gender in this world.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "Mr. Otis"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        hero_name=params.name,
        hero_type=params.gender,
        helper_name=params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story set at {COMMUNITY_CENTER} that begins with blame and ends with a twist.',
        f"Tell a child-friendly story where {f['hero'].id} gets blamed for a paint mess, but the real cause is surprising and the ending changes the room.",
        f'Write a short story that uses the word "blame" and ends with a transformation of a bad ending into something bright.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    return [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {COMMUNITY_CENTER}, where a small mess could feel as big as a wagon wheel.",
        ),
        QAItem(
            question=f"Why did people blame {hero.id}?",
            answer=f"People blamed {hero.id} because paint splashed everywhere, and the room looked ready for a bad ending before the truth came out.",
        ),
        QAItem(
            question=f"What was the twist?",
            answer=f"The twist was that {hero.id} did not cause the splash; a loose ceiling fan and a flying tarp did.",
        ),
        QAItem(
            question=f"How did the day transform?",
            answer=f"The bad ending transformed into a bright mural, and {hero.id} ended up {activity.gerund} while {prize.label} stayed clean.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.id} helped by bringing out a paint smock and turning the mess into part of the mural.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community center?",
            answer="A community center is a place where people gather for activities, classes, and events.",
        ),
        QAItem(
            question="What does a smock do?",
            answer="A smock helps keep paint off your clothes when you are making art.",
        ),
        QAItem(
            question="What is a mural?",
            answer="A mural is a large picture painted on a wall.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(community_center).
activity(mural).
prize(shirt). prize(apron). prize(sneakers).

affords(community_center,mural).

zone(mural,torso).
mess_of(mural,painted).

worn_on(shirt,torso).
worn_on(apron,torso).
worn_on(sneakers,feet).

gender_ok(shirt,girl). gender_ok(shirt,boy).
gender_ok(apron,girl). gender_ok(apron,boy).
gender_ok(sneakers,girl). gender_ok(sneakers,boy).

gear(smock).
guards(smock,painted).
covers(smock,torso).

prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).

valid(Place,A,P) :- place(Place), activity(A), prize(P), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), gender_ok(P,G).

#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "community_center"),
            asp.fact("activity", "mural"),
            asp.fact("prize", "shirt"),
            asp.fact("prize", "apron"),
            asp.fact("prize", "sneakers"),
            asp.fact("affords", "community_center", "mural"),
            asp.fact("zone", "mural", "torso"),
            asp.fact("mess_of", "mural", "painted"),
            asp.fact("worn_on", "shirt", "torso"),
            asp.fact("worn_on", "apron", "torso"),
            asp.fact("worn_on", "sneakers", "feet"),
            asp.fact("gear", "smock"),
            asp.fact("guards", "smock", "painted"),
            asp.fact("covers", "smock", "torso"),
            asp.fact("gender_ok", "shirt", "girl"),
            asp.fact("gender_ok", "shirt", "boy"),
            asp.fact("gender_ok", "apron", "girl"),
            asp.fact("gender_ok", "apron", "boy"),
            asp.fact("gender_ok", "sneakers", "girl"),
            asp.fact("gender_ok", "sneakers", "boy"),
        ]
    )


def asp_program(show: str = "#show valid/3.\n#show valid_story/4.") -> str:
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:18} {act:8} {prize:10} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for gender in ["girl", "boy"]:
            params = StoryParams(
                place="community_center",
                activity="mural",
                prize="shirt" if gender == "girl" else "apron",
                name="Mabel" if gender == "girl" else "Otis",
                gender=gender,
                helper="Mr. Otis",
                seed=base_seed,
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
