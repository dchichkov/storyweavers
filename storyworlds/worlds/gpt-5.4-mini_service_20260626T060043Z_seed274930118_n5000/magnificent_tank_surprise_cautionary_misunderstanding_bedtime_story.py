#!/usr/bin/env python3
"""
storyworlds/worlds/magnificent_tank_surprise_cautionary_misunderstanding_bedtime_story.py
==========================================================================================

A bedtime-style story world about a magnificent tank, a gentle cautionary
warning, and a small misunderstanding that turns into a soft surprise.

The seed idea is simple:
- A child loves a magnificent tank.
- A grown-up gives a careful warning before bedtime.
- The warning is misunderstood for a moment.
- A kind surprise helps the child and grown-up settle the worry.

The world is intentionally small: one bedroom, one prized object, one risky
action, and one cozy compromise.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    caution: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    surprise: str


@dataclass
class Comfort:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    comfort: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"whisper", "stow"}),
    "nursery": Setting(place="the nursery", affords={"whisper", "stow"}),
    "hallway": Setting(place="the hallway", affords={"whisper"}),
}

ACTIVITIES = {
    "whisper": Activity(
        id="whisper",
        verb="whisper goodnight to the tank",
        gerund="whispering goodnight to the tank",
        rush="tiptoe close to the shelf",
        risk="the tank might wobble off the shelf",
        caution="the grown-up warned that the shelf was crowded and the tank could tumble",
        zone={"shelf"},
        keyword="goodnight",
    ),
    "stow": Activity(
        id="stow",
        verb="stow the tank by the pillow",
        gerund="nestling the tank near the pillow",
        rush="slide the tank onto the bed",
        risk="the tank could get bumped in the blanket",
        caution="the grown-up warned that the bed was too sleepy for a heavy tank",
        zone={"bed"},
        keyword="pillow",
    ),
}

PRIZES = {
    "toy_tank": Prize(
        label="tank",
        phrase="a magnificent tank with shiny sides",
        type="tank",
        region="shelf",
        surprise="a little moon sticker on the turret",
    )
}

COMFORTS = {
    "nightstand": Comfort(
        id="nightstand",
        label="a nightstand",
        prep="move the tank to the nightstand instead",
        tail="parked the tank on the nightstand",
        helps={"wobble", "bed"},
    ),
    "toy_box": Comfort(
        id="toy_box",
        label="a soft toy box",
        prep="put the tank in a soft toy box until morning",
        tail="rested the tank in the toy box",
        helps={"wobble", "bed"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Finn", "Theo", "Max"]
TRAITS = ["curious", "gentle", "sleepy", "careful", "cheerful"]


def risky(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or activity.id == "stow"


def select_comfort(activity: Activity, prize: Prize) -> Optional[Comfort]:
    for c in COMFORTS.values():
        if "bed" in c.helps and activity.id == "stow":
            return c
        if "wobble" in c.helps and activity.id == "whisper":
            return c
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not create a believable bedtime worry "
        f"for the {prize.label}, so there is no honest cautionary misunderstanding.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: this world only uses a {PRIZES[prize_id].label}, and the chosen character should be a {gender}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a magnificent tank, a cautionary warning, and a gentle surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not risky(act, pr):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.prize, args.gender))

    settings = [args.setting] if args.setting else list(SETTINGS)
    activities = [args.activity] if args.activity else list(ACTIVITIES)
    prizes = [args.prize] if args.prize else list(PRIZES)
    comforts = [args.comfort] if args.comfort else list(COMFORTS)

    combos = []
    for s in settings:
        for a in activities:
            for p in prizes:
                if risky(ACTIVITIES[a], PRIZES[p]):
                    combos.append((s, a, p))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, activity, prize = rng.choice(sorted(combos))
    comfort = rng.choice(sorted(comforts))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        comfort=comfort,
        name=name,
        gender=gender,
        parent=parent,
    )


def _act(world: World, child: Entity, activity: Activity, prize: Entity) -> None:
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    if activity.id == "stow":
        child.meters["bed"] = child.meters.get("bed", 0.0) + 1
    else:
        child.meters["wobble"] = child.meters.get("wobble", 0.0) + 1
    if child.meters.get("wobble", 0.0) >= THRESHOLD or child.meters.get("bed", 0.0) >= THRESHOLD:
        prize.meters["risk"] = 1.0


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="grown-up",
    ))
    prize = world.add(Entity(
        id="tank",
        type="tank",
        label="tank",
        phrase=PRIZES[params.prize].phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    comfort = COMFORTS[params.comfort]
    activity = ACTIVITIES[params.activity]

    world.say(
        f"{child.id} was a {rng_trait = random.choice(TRAITS) if False else 'careful'} little {params.gender} who loved {prize.phrase}."
    )
    world.say(
        f"At bedtime, {child.id} sat by {world.setting.place} and looked at {prize.phrase} as if it were a tiny treasure."
    )
    world.para()
    world.say(
        f"{child.id} wanted to {activity.verb}, but {parent.pronoun('subject').capitalize()} gave a gentle warning: "
        f"\"{activity.caution}.\""
    )
    world.say(
        f"{child.id} thought the warning meant something different at first, so {child.pronoun('subject')} tried to {activity.rush}."
    )
    _act(world, child, activity, prize)
    world.say(
        f"That was the misunderstanding: {child.id} had thought the worry was about {activity.keyword}, "
        f"but the real problem was {activity.risk}."
    )
    world.para()
    world.say(
        f"Then {parent.pronoun('subject')} smiled and offered a surprise: {comfort.prep}."
    )
    world.say(
        f"{child.id} nodded, and together they {comfort.tail}. The tank stayed safe, and the room grew quiet again."
    )
    world.say(
        f"Before sleep, {child.id} noticed the small moon sticker on the tank and felt very proud of the peaceful plan."
    )

    world.facts.update(child=child, parent=parent, prize=prize, comfort=comfort, activity=activity)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, activity, prize = f["child"], f["parent"], f["activity"], f["prize"]
    return [
        "Write a cozy bedtime story about a magnificent tank, a careful warning, and a kind surprise.",
        f"Tell a gentle story where {child.id} wants to {activity.verb} but {parent.pronoun('subject')} worries about the {prize.label}.",
        f"Write a bedtime story with a misunderstanding that ends with {child.id} and {parent.pronoun('subject')} choosing a safer place for the tank.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, activity, prize, comfort = f["child"], f["parent"], f["activity"], f["prize"], f["comfort"]
    return [
        QAItem(
            question=f"Who loved the magnificent tank?",
            answer=f"{child.id} loved the magnificent tank and treated it like a tiny treasure at bedtime.",
        ),
        QAItem(
            question=f"What did the grown-up warn about?",
            answer=f"{parent.pronoun('subject').capitalize()} warned that {activity.caution.lower()}.",
        ),
        QAItem(
            question=f"What was the misunderstanding?",
            answer=f"{child.id} first thought the warning was about {activity.keyword}, but it was really about the tank being in a risky place.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {comfort.label} and moved the tank to a safer spot, which kept bedtime calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tank in this story?",
            answer="In this story, a tank is a shiny toy that can be loved, carried carefully, and placed somewhere safe.",
        ),
        QAItem(
            question="Why can bedtime feel calmer after a surprise?",
            answer="A gentle surprise can help change worry into comfort, especially when grown-ups offer a safe plan.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- risky(A,P).
has_fix(A,P) :- prize_at_risk(A,P), comfort(C), helps(C,Need), needs(A,Need).
valid_story(S,A,P,C) :- setting(S), activity(A), prize(P), comfort(C), valid_combo(S,A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for a, act in ACTIVITIES.items():
            for p, prize in PRIZES.items():
                if risky(act, prize):
                    combos.append((s, a, p))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


CURATED = [
    StoryParams(setting="bedroom", activity="whisper", prize="toy_tank", comfort="nightstand", name="Mia", gender="girl", parent="mother"),
    StoryParams(setting="nursery", activity="stow", prize="toy_tank", comfort="toy_box", name="Leo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.activity} in {p.setting} with {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
