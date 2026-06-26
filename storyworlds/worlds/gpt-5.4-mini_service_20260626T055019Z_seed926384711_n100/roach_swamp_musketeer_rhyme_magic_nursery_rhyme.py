#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/roach_swamp_musketeer_rhyme_magic_nursery_rhyme.py
==============================================================================================================================

A tiny storyworld in a nursery-rhyme mood:
- a roach musketeer
- a swamp setting
- rhyme and magic as core instruments

The world is intentionally small and constraint-checked: a brave little roach
wants to sing and cross the swamp, but the swamp would spoil a cherished item.
A magical rhyme-based fix must actually cover the at-risk item.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "roach":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the swamp"
    known_for: str = "misty reeds"
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", pid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gid, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gid, g))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and any(
                    prize.region in g.covers and act.mess in g.guards for g in GEAR.values()
                ):
                    combos.append((place, act_id, prize_id))
    return combos


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
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def rhyme_line(word: str) -> str:
    return {
        "swamp": "In the swamp so dim and damp,",
        "roach": "A roach with a musketeer stamp,",
        "magic": "With magic bright as candle-flame,",
        "rhyme": "He sang a rhyme to guide his aim,",
        "moon": "Under the moon and cattail lace,",
        "safe": "He found a safe and shining place,",
    }.get(word, f"{word.capitalize()} came along with a nursery beat,")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a roach musketeer in a swamp.")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if prize.region not in act.zone:
            raise StoryError("That prize is not at risk in this swamp tale.")
        if not any(prize.region in g.covers and act.mess in g.guards for g in GEAR.values()):
            raise StoryError("No magical fix in this world can safely cover that prize.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid story combination matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    roach = world.add(Entity(id=name, kind="character", type="roach", meters={}, memes={}))
    helper = world.add(Entity(id="Mentor", kind="character", type="mouse", label="a moon-mouse"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=roach.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts.update(roach=roach, helper=helper, prize=prize, activity=activity, setting=setting)

    roach.memes["love_rhyme"] = 1
    roach.memes["magic_hope"] = 1
    world.say(f"In {setting.place}, there lived a little roach musketeer named {roach.id}.")
    world.say(f"{roach.id} was {trait} and bright, and {roach.pronoun('subject')} loved to rhyme by moonlight.")
    world.say(f"{roach.pronoun('possessive').capitalize()} {prize.label} was neat and proud, fit for a brave parade.")

    world.para()
    world.say(f"One misty day in {setting.place}, {roach.id} wished to {activity.verb}.")
    world.say(f"{rhyme_line('swamp')} {rhyme_line('roach')}")
    world.say(f"But the swamp was muddy, and the muck would spoil {roach.pronoun('possessive')} {prize.label}.")
    roach.memes["desire"] = 1
    roach.memes["worry"] = 1
    world.zone = set(activity.zone)

    if prize_cfg.region in activity.zone:
        prize.meters["muddy"] = 1
        roach.memes["trouble"] = 1
        world.say(f'{helper.label} peeped, "Not yet, my dear. The swamp will make it all a smear."')

    world.para()
    world.say(f"Then {helper.label} tapped a wand of reed and said, " f'"Try a magic rhyme instead."')
    world.say(f"{rhyme_line('magic')} {rhyme_line('rhyme')}")
    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError("No reasonable magical fix exists for this story.")
    if prize_cfg.region in activity.zone and activity.mess in gear.guards:
        world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
            worn_by=roach.id,
        ))
        roach.memes["hope"] = 1
        roach.memes["joy"] = 1
        world.say(f"They put on {gear.label}, and the rhyme made it gleam.")
        world.say(f"{roach.id} went to {activity.gerund}, and the swamp could not touch {roach.pronoun('possessive')} {prize.label}.")
        world.say(f"{rhyme_line('moon')} {rhyme_line('safe')}")
    else:
        raise StoryError("The magic in this world must truly protect the prize.")

    world.facts["gear"] = gear
    return world


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    roach = f["roach"]
    prize = f["prize"]
    act = f["activity"]
    return [
        f"Write a short nursery rhyme story about a roach musketeer named {roach.id} in the swamp.",
        f"Tell a gentle tale where {roach.id} wants to {act.verb} but a magical rhyme must keep {roach.pronoun('possessive')} {prize.label} clean.",
        f"Write a child-friendly story that includes a swamp, a musketeer, rhyme, and magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    roach = f["roach"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the little musketeer in the swamp story?",
            answer=f"The little musketeer is a roach named {roach.id}.",
        ),
        QAItem(
            question=f"What did {roach.id} want to do in the swamp?",
            answer=f"{roach.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the moon-mouse offer magic?",
            answer=f"The moon-mouse offered magic because the swamp mud would spoil {roach.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"How did the story keep the {prize.label} safe?",
            answer=f"They used {gear.label}, which covered the right part of {roach.id} and kept the {prize.label} clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swamp like?",
            answer="A swamp is a wet place with mud, reeds, and shallow water.",
        ),
        QAItem(
            question="What is rhyme in a nursery tale?",
            answer="Rhyme is when words sound alike at the ends, like sing and swing.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is a special power in a story that can do wonderful things that real life cannot.",
        ),
        QAItem(
            question="What is a musketeer?",
            answer="A musketeer is a brave fighter from old stories, often shown with a hat, a sword, and a proud pose.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


SETTINGS = {
    "swamp": Setting(place="the swamp", known_for="misty reeds", affords={"sing", "cross", "dance"}),
}

ACTIVITIES = {
    "sing": Activity(
        id="sing",
        verb="sing a rhyme",
        gerund="singing a rhyme",
        rush="skip to the lily stones",
        mess="muddy",
        soil="splashed and muddy",
        zone={"feet", "legs", "torso"},
        keyword="rhyme",
        tags={"swamp", "rhyme", "magic"},
    ),
    "cross": Activity(
        id="cross",
        verb="cross the swamp",
        gerund="crossing the swamp",
        rush="dash across the reeds",
        mess="muddy",
        soil="spattered with mud",
        zone={"feet", "legs"},
        keyword="swamp",
        tags={"swamp", "magic"},
    ),
    "dance": Activity(
        id="dance",
        verb="dance in the moon reeds",
        gerund="dancing in the moon reeds",
        rush="twirl through the reeds",
        mess="muddy",
        soil="mud-speckled",
        zone={"feet", "legs", "torso"},
        keyword="magic",
        tags={"swamp", "rhyme", "magic"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright blue cape", type="cape", region="torso"),
    "boots": Prize(label="boots", phrase="little white boots", type="boots", region="feet", plural=True),
    "sash": Prize(label="sash", phrase="a silver sash", type="sash", region="torso"),
}

GEAR = {
    "spellboots": Gear(id="spellboots", label="spell boots", covers={"feet"}, guards={"muddy"}, prep="put on spell boots", tail="wore the spell boots"),
    "mooncape": Gear(id="mooncape", label="a moon cape", covers={"torso"}, guards={"muddy"}, prep="wrap on a moon cape", tail="wrapped on the moon cape"),
    "lilycloak": Gear(id="lilycloak", label="a lily cloak", covers={"torso"}, guards={"muddy"}, prep="tie on a lily cloak", tail="tied on the lily cloak"),
}

NAMES = ["Rolo", "Ricky", "Milo", "Timo", "Rami", "Bibi"]
TRAITS = ["brave", "spry", "cheery", "tiny", "merry"]

CURATED = [
    StoryParams(place="swamp", activity="sing", prize="cape", name="Rolo", trait="brave"),
    StoryParams(place="swamp", activity="cross", prize="boots", name="Milo", trait="cheery"),
    StoryParams(place="swamp", activity="dance", prize="sash", name="Rami", trait="merry"),
]


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if prize.region not in act.zone:
            raise StoryError("That prize would not be at risk in this activity.")
        if select_gear(act, prize) is None:
            raise StoryError("No magical gear can safely fix that combination.")
    combos = [
        c for c in valid_story_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid combination matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
