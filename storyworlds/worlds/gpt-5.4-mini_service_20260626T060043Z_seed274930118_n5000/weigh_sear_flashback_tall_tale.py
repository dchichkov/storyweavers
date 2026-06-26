#!/usr/bin/env python3
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

TALL_TALE_OPENERS = [
    "bigger than a barn cat's grin",
    "wide as a wagon wheel",
    "as lively as a kicked-up prairie dog",
    "as grand as a thundercloud rolling home",
]

FLASHBACK_MARKERS = [
    "He remembered",
    "She remembered",
    "They remembered",
    "Long ago,",
]

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
        for k in ["weight", "heat", "dirty", "joy", "worry", "memory", "pride"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cowgirl"}
        male = {"boy", "father", "dad", "man", "cowboy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    heat: str
    danger: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_used: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn(actor))

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
    "camp": Place(id="camp", label="the trail camp", affords={"sear", "weigh"}),
    "ranch": Place(id="ranch", label="the ranch kitchen", indoors=True, affords={"sear", "weigh"}),
    "riverbank": Place(id="riverbank", label="the riverbank cookfire", affords={"sear"}),
}

ACTIVITIES = {
    "sear": Activity(
        id="sear",
        verb="sear the supper",
        gerund="searing supper",
        rush="rush to the hot skillet",
        heat="hot and bright",
        danger="seared",
        zone={"hands", "torso"},
        keyword="sear",
        tags={"fire", "cook", "heat"},
    ),
    "weigh": Activity(
        id="weigh",
        verb="weigh the meal bags",
        gerund="weighing meal bags",
        rush="dash to the scale",
        heat="careful",
        danger="stretched thin",
        zone={"hands"},
        keyword="weigh",
        tags={"balance", "measure"},
    ),
}

PRIZES = {
    "shirt": Prize(id="shirt", label="shirt", phrase="a bright new shirt", region="torso"),
    "apron": Prize(id="apron", label="apron", phrase="a sturdy apron", region="torso"),
    "hat": Prize(id="hat", label="hat", phrase="a handsome hat", region="head"),
}

GEAR = [
    Gear(
        id="apron_gear",
        label="a leather apron",
        covers={"torso"},
        guards={"seared"},
        prep="put on a leather apron first",
        tail="slipped on the leather apron",
    ),
    Gear(
        id="mitts",
        label="heavy oven mitts",
        covers={"hands"},
        guards={"seared"},
        prep="pull on heavy oven mitts first",
        tail="pulled on the heavy oven mitts",
        plural=True,
    ),
]

NAMES = {
    "girl": ["Mabel", "Lula", "Daisy", "June"],
    "boy": ["Bo", "Ned", "Tom", "Cliff"],
}
TYPES = {"girl": "girl", "boy": "boy", "cowboy": "cowboy", "cowgirl": "cowgirl"}
TRAITS = ["bold", "cheerful", "stubborn", "lively"]

CURATED = [
    ("camp", "sear", "shirt", "boy", "cowboy", "father"),
    ("ranch", "sear", "apron", "girl", "cowgirl", "mother"),
    ("camp", "weigh", "hat", "boy", "cowboy", "father"),
]


# ---------------------------------------------------------------------------
# Contract dataclass
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    hero_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.danger in gear.guards:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not reasonably threaten {prize.label}, "
        f"so there is no honest worry or compromise to tell.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_type,
        meters={"weight": 1.0, "heat": 0.0, "dirty": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "memory": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={"weight": 1.0},
        memes={"joy": 0.0, "worry": 1.0, "memory": 0.0},
    ))
    prize_ent = world.add(Entity(
        id="Prize",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize.region,
        plural=prize.plural,
        meters={"dirty": 0.0, "weight": 0.0},
        memes={"pride": 1.0},
    ))

    # Act 1: setup
    opener = random.choice(TALL_TALE_OPENERS)
    world.say(
        f"{hero.id} was a {params.trait} {params.hero_type}, {opener}, and {hero.pronoun()} loved work that made a day feel big."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked {activity.gerund} at {place.label}, and {hero.pronoun('possessive')} {prize.label} shone like a sunrise."
    )
    world.say(
        f"{params.parent_type.capitalize()} had bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize_ent.it()} proudly."
    )

    # Act 2: tension and flashback
    world.para()
    if activity.id == "sear":
        world.say(
            f"One day at {place.label}, {hero.id} wanted to {activity.verb}, but the skillet was {activity.heat}."
        )
    else:
        world.say(
            f"One day at {place.label}, {hero.id} wanted to {activity.verb}, and the little scale waited by the sack pile."
        )

    if prize_at_risk(activity, prize):
        world.say(
            f"{params.parent_type.capitalize()} said, \"You'll get your {prize.label} {activity.danger}, and then I'll have more to mend.\""
        )

    world.say(
        f"{hero.id} paused, and a flashback slipped in like a prairie breeze."
    )
    world.flashback_used = True
    world.say(
        f"{random.choice(FLASHBACK_MARKERS)} {hero.id} remembered an old time when a stubborn skillet had singed a sleeve, and {hero.pronoun('possessive')} heart had leaped right into {hero.pronoun('possessive')} boots."
    )

    # Act 3: compromise and resolution
    world.para()
    gear = select_gear(activity, prize) if prize_at_risk(activity, prize) else None
    if gear:
        g = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
        ))
        g.worn_by = hero.id
        world.say(
            f"Then {params.parent_type} smiled and said, \"How about we {gear.prep}?\""
        )
        hero.memes["joy"] += 1.0
        hero.memes["pride"] += 1.0
        world.say(
            f"{hero.id} grinned, and soon {hero.id} and {params.parent_type} {gear.tail}. After that, {hero.id} could {activity.verb} without ruining {hero.pronoun('possessive')} {prize.label}."
        )
        world.say(
            f"By supper's end, the meal was well {activity.danger}, the {prize.label} stayed clean, and the whole camp felt tall as a cottonwood."
        )
    else:
        world.say(
            f"So {params.parent_type} helped {hero.id} choose a safer job, and the two of them kept the day tidy and bright."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize_ent,
        activity=activity,
        place=place,
        gear=gear,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale for a young child about a {f['hero'].type} named {f['hero'].id} who wants to {f['activity'].verb} at {f['place'].label}.",
        f"Tell a child-friendly story that uses the words 'weigh' and 'sear' and includes a flashback.",
        f"Write a short western story where a parent worries a {f['prize'].label} will get {f['activity'].danger} unless the family finds a simple fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {f['place'].label}?",
            answer=f"{hero.id} wanted to {activity.verb} at {f['place'].label}.",
        ),
        QAItem(
            question=f"Why did the {parent.type} worry about the {prize.label}?",
            answer=f"The {parent.type} worried because the {prize.label} could get {activity.danger} if {hero.id} kept going.",
        ),
        QAItem(
            question="What happened in the flashback?",
            answer=f"{hero.id} remembered an older time when a skillet had singed a sleeve, so {hero.id} knew to be careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to weigh something?",
            answer="To weigh something means to find out how heavy it is by using a scale or balance.",
        ),
        QAItem(
            question="What does it mean to sear food?",
            answer="To sear food means to cook the outside very quickly with strong heat so it gets brown and tasty.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} worn_by={e.worn_by} meters={e.meters} memes={e.memes}")
    lines.append(f"flashback_used={world.flashback_used}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
fix(A,P) :- at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), guards(G,M), danger_of(A,M).
valid_story(Place,A,P) :- affords(Place,A), at_risk(A,P), fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("danger_of", aid, a.danger))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in SETTINGS.items():
        for aid in p.affords:
            act = ACTIVITIES[aid]
            for prid, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    combos.append((pid, aid, prid))
    return combos

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with flashbacks, weighing, and searing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "cowboy", "cowgirl"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not (prize_at_risk(ACTIVITIES[args.activity], PRIZES[args.prize]) and select_gear(ACTIVITIES[args.activity], PRIZES[args.prize])):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the requested options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_type = args.hero_type or ("cowgirl" if gender == "girl" else "cowboy")
    name = args.name or rng.choice(NAMES[gender])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, hero_type=hero_type, parent_type=parent_type, trait=trait)

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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, act, prize) in enumerate(CURATED):
            p = StoryParams(
                place=place,
                activity=act,
                prize=prize,
                name=(NAMES["boy"][i % len(NAMES["boy"]) ] if i % 2 == 0 else NAMES["girl"][i % len(NAMES["girl"]) ]),
                gender="boy" if i % 2 == 0 else "girl",
                hero_type="cowboy" if i % 2 == 0 else "cowgirl",
                parent_type="father" if i % 2 == 0 else "mother",
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
