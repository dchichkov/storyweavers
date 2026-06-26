#!/usr/bin/env python3
"""
storyworlds/worlds/bead_waist_foreshadowing_bad_ending_teamwork_tall.py
=======================================================================

A tiny tall-tale storyworld about a bright bead at the waist, a worried
foreshadowing moment, teamwork, and a bad ending that still feels like a
complete story.

Premise:
- A child wears a bead belt around the waist.
- The child wants to take a noisy, showy ride or climb.
- A loose bead, a low trail, or a wobbling saddle foreshadows trouble.
- A warning is ignored or only partly heeded.
- The helper team tries hard to fix things together.
- The ending is a little bad in the physical sense: the prize is lost, bent,
  or scattered. But the story still closes with a clear image of what changed.

The world is small on purpose: fewer, stronger variations instead of a wide,
weak grab bag.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TALL_PHRASES = [
    "as broad as a barn door",
    "as lively as a fiddler at noon",
    "as tall as a cottonwood in a thunderstorm",
    "as quick as a jackrabbit on a fence rail",
]

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
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "man", "cowboy"}
        female = {"girl", "mother", "woman", "cowgirl"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    foreshadow: str
    consequence: str
    keyword: str


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
    guard: str
    prep: str
    tail: str


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
    "riverbend": Setting(
        place="the Riverbend fairground",
        outdoors=True,
        affords={"ride", "race"},
        detail="The wagons creaked, and the banners snapped like sailcloth.",
    ),
    "mesa": Setting(
        place="the High Mesa trail",
        outdoors=True,
        affords={"climb", "race"},
        detail="The wind went whistling by the rocks as if it had news to share.",
    ),
}

ACTIVITIES = {
    "ride": Activity(
        id="ride",
        verb="take the buckboard ride",
        gerund="riding the buckboard",
        rush="climb aboard the buckboard and jounce down the lane",
        mess="jolt",
        zone={"waist"},
        foreshadow="the wagon gave a little wobble before anybody even climbed in",
        consequence="the bead belt skipped loose and spilled like bright corn",
        keyword="bead",
    ),
    "climb": Activity(
        id="climb",
        verb="climb the winding bluff",
        gerund="climbing the bluff",
        rush="scramble up the bluff fast",
        mess="scrape",
        zone={"waist"},
        foreshadow="the trail narrowed at the waist-high rocks, and one bead kept clicking warnfully",
        consequence="the bead belt snagged on a thorn and snapped",
        keyword="waist",
    ),
    "race": Activity(
        id="race",
        verb="race the dusty track",
        gerund="racing the dusty track",
        rush="run like the wind",
        mess="dust",
        zone={"waist"},
        foreshadow="the loose bead on the belt tapped the buckle like a tiny drum warning of trouble",
        consequence="the bead belt burst open mid-stride",
        keyword="bead",
    ),
}

PRIZES = {
    "belt": Prize(
        label="bead belt",
        phrase="a shiny bead belt for the waist",
        type="belt",
        region="waist",
    ),
    "sash": Prize(
        label="beaded sash",
        phrase="a long beaded sash that wrapped around the waist",
        type="sash",
        region="waist",
    ),
}

GEAR = {
    "twine": Gear(
        id="twine",
        label="a loop of twine",
        covers={"waist"},
        guard="snag",
        prep="tie the beads down with a loop of twine",
        tail="worked together to tie the beads down with twine",
    ),
    "gloves": Gear(
        id="gloves",
        label="soft work gloves",
        covers={"hands"},
        guard="dust",
        prep="put on soft work gloves and steady the wagon side by side",
        tail="held the rails and steadied the wagon together",
    ),
}

GIRL_NAMES = ["Mabel", "June", "Ruby", "Ivy", "Annie", "Pearl"]
BOY_NAMES = ["Hank", "Bobby", "Clint", "Wade", "Ezra", "Otis"]
TRAITS = ["brave", "merry", "stubborn", "bright-eyed", "lively", "bold"]


# ---------------------------------------------------------------------------
# Parameters
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if prize.region in gear.covers and activity.id in {"ride", "climb"}:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not honestly endanger a {prize.label} "
        f"unless it sits at the {prize.region}.)"
    )


def pronounce_name(name: str) -> str:
    return name


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'merry')} {hero.type} "
        f"with a grin {random.choice(TALL_PHRASES)}."
    )


def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {prize.label} was new and bright, "
        f"and it sat snug at the {prize.region} like a promise."
    )


def foreshadow(world: World, activity: Activity, prize: Entity) -> None:
    world.say(
        f"Even so, there was a sign of trouble: {activity.foreshadow}."
    )


def warning(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f'"If that buckle slips," said {parent.id}, "your {prize.label} may not stay together '
        f"for {activity.verb}."'
    )


def teamwork(world: World, parent: Entity, hero: Entity, gear: Gear, activity: Activity) -> None:
    world.say(
        f"So {hero.id} and {parent.id} {gear.prep}, and they did it shoulder to shoulder."
    )


def bad_ending(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"But the big idea went wrong all the same: {activity.consequence}."
    )
    world.say(
        f"The {prize.label} ended in bright pieces in the dust, and {hero.id} had to gather "
        f"what {hero.pronoun('subject')} could with both hands."
    )


def closing_image(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"By sunset, the wind had quieted, {parent.id} was helping sort the beads, and "
        f"{hero.id} stood there with a small, crooked smile at the {prize.region} that was now bare."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, gender: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        memes={"trait": (hero_traits or ["merry"])[0]},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError(explain_rejection(activity, prize))

    introduce(world, hero)
    setup_prize(world, hero, prize)
    world.say(setting.detail)
    world.para()
    foreshadow(world, activity, prize)
    warning(world, parent, hero, activity, prize)
    world.say(
        f"{hero.id} heard the words, but the tall-tale excitement was already galloping."
    )
    teamwork(world, parent, hero, gear, activity)
    world.para()
    bad_ending(world, hero, prize, activity)
    closing_image(world, hero, parent, prize)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a tall-tale story for a young child that uses the words "bead" and "waist".',
        f"Tell a story where {hero.id} tries to {act.verb}, but a parent spots a problem with {prize.label}.",
        f"Write a short, lively story about teamwork, a warning, and a bad ending that still feels complete.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb} with {prize.label} at the {prize.region}.",
        ),
        QAItem(
            question=f"What warning helped foreshadow trouble?",
            answer=f"The warning was that the loose bead and the wobbly start meant the {prize.label} might not stay together.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.id} try to solve the problem?",
            answer=f"They worked together and tried to keep the {prize.label} steady with careful teamwork.",
        ),
        QAItem(
            question=f"What made the ending bad?",
            answer=f"The beads still came apart, so the prize ended in pieces instead of staying whole.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bead": [
        QAItem(
            question="What is a bead?",
            answer="A bead is a small round piece, often used on necklaces, belts, and decorations.",
        )
    ],
    "waist": [
        QAItem(
            question="Where is the waist?",
            answer="The waist is the middle part of the body, between the chest and the hips.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same job.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little clue early in a story that hints something important may happen later.",
        )
    ],
    "bad_ending": [
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when the problem is not fully fixed and something important is lost or broken.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["bead"],
        *WORLD_KNOWLEDGE["waist"],
        *WORLD_KNOWLEDGE["teamwork"],
        *WORLD_KNOWLEDGE["foreshadowing"],
        *WORLD_KNOWLEDGE["bad_ending"],
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
reasonably_valid(Place, Act, Prize) :- setting(Place), affords(Place, Act), activity(Act), prize(Prize),
                                      prize_region(Prize, Region), splashes(Act, Region).

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
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


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
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: bead, waist, foreshadowing, teamwork, bad ending."
    )
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not is_reasonable(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
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
        parts = []
        if e.region:
            parts.append(f"region={e.region}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
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


CURATED = [
    StoryParams(place="riverbend", activity="ride", prize="belt", name="Mabel", gender="girl", parent="mother", trait="bright-eyed"),
    StoryParams(place="mesa", activity="climb", prize="sash", name="Hank", gender="boy", parent="father", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonably_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
