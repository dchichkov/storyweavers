#!/usr/bin/env python3
"""
Storyworld: rug rhyme dialogue conflict.

A small, child-facing story domain inspired by a rhyming picture-book feel:
a child wants to play on a rug, something messy or risky threatens it, and a
gentle dialogue resolves the conflict in a safe, satisfying way.
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
# Core data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
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
    keyword: str = "rug"
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
        return any(g.id in self.entities and region in g.meters.get("covers", set()) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# World registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"crayons", "tea"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"crayons", "tea"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"crayons", "tea"}),
}

ACTIVITIES = {
    "crayons": Activity(
        id="crayons",
        verb="draw with crayons",
        gerund="drawing with crayons",
        rush="dash for the crayons",
        mess="scribbled",
        soil="all scribbled",
        zone={"rug"},
        keyword="rug",
        tags={"rug", "color", "messy"},
    ),
    "tea": Activity(
        id="tea",
        verb="have a pretend tea party",
        gerund="playing tea party",
        rush="rush to the tea set",
        mess="spilled",
        soil="spilled all over",
        zone={"rug"},
        keyword="rug",
        tags={"rug", "spill", "cups"},
    ),
}

PRIZES = {
    "rug": Prize(
        label="rug",
        phrase="a soft striped rug",
        type="rug",
        region="rug",
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a little snack tray",
        covers={"rug"},
        guards={"spilled"},
        prep="set the cups on a little tray",
        tail="set the cups on a tray and kept the rug dry",
    ),
    Gear(
        id="paper",
        label="a big sheet of paper",
        covers={"rug"},
        guards={"scribbled"},
        prep="spread out a big sheet of paper first",
        tail="spread out paper and kept the rug neat",
    ),
]

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
NAMES_BOY = ["Ben", "Leo", "Sam", "Theo", "Max"]
TRAITS = ["curious", "cheerful", "bouncy", "gentle", "silly"]


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


# ---------------------------------------------------------------------------
# Rhyme-friendly story engine
# ---------------------------------------------------------------------------

def rhyme_line(*parts: str) -> str:
    return " ".join(parts)


def build_rhyme_bank() -> dict[str, list[tuple[str, str]]]:
    return {
        "setup": [
            ("On the rug, snug as a bug,", "the little one smiled in a cozy hug."),
            ("By the soft little mat, under hat and chat,", "a child sat still, then wanted that."),
        ],
        "conflict": [
            ("But the rug was a favorite thing,", "and spills could make it sad in spring."),
            ("Crayons can slide and tea can pour,", "and that means trouble on the floor."),
        ],
        "resolution": [
            ("So they chose a plan that fit just right,", "and kept the rug both clean and bright."),
            ("A helper, a tray, and a careful way,", "turned the frown into a happy play."),
        ],
    }


RHYME_BANK = build_rhyme_bank()


class WorldRules:
    @staticmethod
    def activity_at_risk(activity: Activity, prize: Prize) -> bool:
        return prize.region in activity.zone

    @staticmethod
    def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
        for gear in GEAR:
            if activity.mess in gear.guards and prize.region in gear.covers:
                return gear
        return None


# ---------------------------------------------------------------------------
# State transitions and narration
# ---------------------------------------------------------------------------

def narrate_setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(rhyme_line(*RHYME_BANK["setup"][0]))
    world.say(
        f"{hero.id} was a little {next(t for t in ['curious','cheerful','bouncy','gentle','silly'] if True)} {hero.type} "
        f"who loved {activity.gerund} on {prize.label}."
    )
    world.say(
        f"{hero.id}'s {parent.label} had bought {hero.pronoun('object')} {prize.phrase}, "
        f"and {hero.id} loved how it felt soft and snug."
    )


def narrate_conflict(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.para()
    world.say(rhyme_line(*RHYME_BANK["conflict"][0]))
    world.say(
        f"One day, {hero.id} wanted to {activity.verb} right away."
    )
    world.say(
        f'But {hero.pronoun("possessive")} {parent.label} said, "Not yet, dear one. '
        f"If you {activity.rush}, {prize.label} may get {activity.soil}."'
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    parent.memes["concern"] = parent.memes.get("concern", 0.0) + 1


def narrate_dialogue(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f'"But I want to {activity.verb}!" said {hero.id}.'
    )
    world.say(
        f'"We can," said {parent.id}, "but we need a way to keep the {prize.label} safe."'
    )
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1


def narrate_resolution(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    world.para()
    world.say(rhyme_line(*RHYME_BANK["resolution"][0]))
    world.say(
        f'{parent.id} smiled and said, "How about we {gear.prep}?"'
    )
    world.say(
        f'{hero.id} nodded, then grinned and said, "Yes, that sounds grand!"'
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2
    hero.memes["frustration"] = 0.0
    parent.memes["concern"] = 0.0
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed clean and bright."
    )


# ---------------------------------------------------------------------------
# Selection and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if WorldRules.activity_at_risk(act, prize) and WorldRules.select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not really threaten the {prize.label}, "
        f"so the rug conflict would feel fake. Choose an activity that can truly mess up the rug.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rug rhyme dialogue conflict storyworld.")
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
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (WorldRules.activity_at_risk(act, prize) and WorldRules.select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    prize = world.add(Entity(id=params.prize, type="rug", label="rug", phrase="a soft striped rug", owner=hero.id, caretaker=parent.id))
    act = ACTIVITIES[params.activity]

    hero.memes["trait"] = 1
    narrate_setup(world, hero, parent, prize, act)
    narrate_conflict(world, hero, parent, prize, act)
    narrate_dialogue(world, hero, parent, prize, act)
    gear = WorldRules.select_gear(act, prize)
    if gear is None:
        raise StoryError("(No story: no safe, plausible way to protect the rug was found.)")
    narrate_resolution(world, hero, parent, prize, act, gear)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": act,
        "gear": gear,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a short rhyming story for a preschooler about {hero.id}, {parent.label}, and a rug.',
        f'Tell a gentle dialogue story where {hero.id} wants to {act.verb} but {parent.label} worries about the rug.',
        f'Write a simple story with a conflict and a happy fix using the word "rug".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the rug?",
            answer=f"{hero.id} wanted to {act.verb} on the rug.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry during the story?",
            answer=f"{parent.id} worried because {act.gerund} could make the rug {act.soil}.",
        ),
        QAItem(
            question=f"How did they keep the rug safe in the end?",
            answer=f"They used {gear.label} and chose a careful way, so the rug stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rug?",
            answer="A rug is a soft mat or carpet that lies on the floor.",
        ),
        QAItem(
            question="Why do people try to keep a rug clean?",
            answer="People keep a rug clean so it stays nice to sit on and does not get stained.",
        ),
        QAItem(
            question="What does it mean to have a conflict?",
            answer="A conflict is when people want different things and need to work out a problem.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which makes a story fun to hear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(nursery).
place(playroom).
place(living_room).

activity(crayons).
activity(tea).

prize(rug).
worn_on(rug, rug).

gear(tray).
gear(paper).

affords(nursery, crayons).
affords(nursery, tea).
affords(playroom, crayons).
affords(playroom, tea).
affords(living_room, crayons).
affords(living_room, tea).

mess_of(crayons, scribbled).
mess_of(tea, spilled).

splashes(crayons, rug).
splashes(tea, rug).

guards(tray, spilled).
covers(tray, rug).

guards(paper, scribbled).
covers(paper, rug).

prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, "rug"))
    for gid in [g.id for g in GEAR]:
        lines.append(asp.fact("gear", gid))
    for place, setting in SETTINGS.items():
        for a in setting.affords:
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("mess_of", aid, act.mess))
        lines.append(asp.fact("splashes", aid, "rug"))
    for gear in GEAR:
        for m in gear.guards:
            lines.append(asp.fact("guards", gear.id, m))
        for c in gear.covers:
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
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

CURATED = [
    StoryParams(place="nursery", activity="crayons", prize="rug", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="playroom", activity="tea", prize="rug", name="Ben", gender="boy", parent="father", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
