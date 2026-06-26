#!/usr/bin/env python3
"""
Storyworld: bedtime rhyme and the lesson learned.

A small, self-contained story domain where a child has a knack for making
rhymes, wants to stay up a little longer, and learns to resign from play in
favor of bedtime. The story is gentle, concrete, and intended to read like a
classical bedtime tale with a clear turn and a closing lesson learned.

This module follows the Storyweavers contract:
- defines StoryParams and the standard CLI helpers
- uses typed entities with meters and memes
- includes a Python reasonableness gate and an inline ASP_RULES twin
- emits StorySample with grounded QA sets
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "mess": 0.0, "sleepy": 0.0}
        if not self.memes:
            self.memes = {"desire": 0.0, "resist": 0.0, "comfort": 0.0, "joy": 0.0}

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
    place: str = "the little bedroom"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"rhyme", "bedtime"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Comfort:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        if hero.meters["tired"] < THRESHOLD:
            continue
        sig = ("sleep", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["sleepy"] += 1
        out.append(f"{hero.id} felt sleepier and sleepier.")
    return out


CAUSAL_RULES = [_r_sleep]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(world_setting: Setting, activity: Activity, prize: Prize, comfort: Comfort,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(world_setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little", trait, "dreamy"]
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    story_prop = world.add(Entity(
        id="book", type="book", label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=parent.id
    ))
    hero.meters["tired"] = 1.0

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who had a knack for making rhymes."
    )
    world.say(
        f"{hero.id} loved to whisper tiny bedtime lines and watch the words land like soft feathers."
    )
    world.say(
        f"One night, {hero.id}'s {parent.label or 'parent'} gave {hero.id} {story_prop.phrase} to hold during the story."
    )

    world.para()
    world.say(
        f"When the lamp glowed low, {hero.id} still wanted one more {activity.verb} instead of going to bed."
    )
    world.say(
        f"{hero.id} tried to {activity.rush}, but the room was getting quiet and the pillow looked very inviting."
    )
    hero.memes["desire"] += 1
    hero.meters["tired"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{parent.id} smiled and said, \"It is okay to resign from play for tonight; sleep has its own kind of magic.\""
    )
    world.say(
        f"Then {parent.id} offered a gentle {comfort.label} and sat beside the bed."
    )
    hero.memes["resist"] += 1
    hero.memes["comfort"] += 1

    world.say(
        f"{hero.id} listened, took a slow breath, and began a last little rhyme: \"Night is bright, dreams take flight.\""
    )
    world.say(
        f"That made the room feel soft and kind, and {hero.id}'s shoulders loosened."
    )

    world.para()
    hero.memes["joy"] += 1
    world.say(
        f"So {hero.id} tucked the {story_prop.label} close, let the rhyme finish, and resigned from staying up any longer."
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, the {comfort.label} was warm, and the lesson learned was simple: "
        f"when bedtime calls, a small heart can rest and still keep its knack for rhyme."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=story_prop,
        activity=activity,
        comfort=comfort,
        setting=world_setting,
        trait=trait,
    )
    return world


SETTINGS = {
    "bedroom": Setting(place="the little bedroom", indoor=True, affords={"rhyme", "bedtime"}),
    "nursery": Setting(place="the cozy nursery", indoor=True, affords={"rhyme", "bedtime"}),
    "attic_room": Setting(place="the attic room", indoor=True, affords={"rhyme", "bedtime"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="make one more rhyme",
        gerund="making soft rhymes",
        rush="dash after one more rhyme",
        mess="noise",
        soil="too wakeful",
        weather="",
        keyword="rhyme",
        tags={"rhyme"},
    ),
    "bedtime": Activity(
        id="bedtime",
        verb="stay up a little longer",
        gerund="drifting toward sleep",
        rush="fight sleep",
        mess="tired",
        soil="sleepy",
        weather="",
        keyword="bedtime",
        tags={"bedtime"},
    ),
}

PRIZES = {
    "book": Prize(
        label="storybook",
        phrase="a tiny storybook with moon pictures",
        type="book",
        plural=False,
    ),
    "lamp": Prize(
        label="night lamp",
        phrase="a little night lamp",
        type="lamp",
        plural=False,
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a soft blue blanket",
        type="blanket",
        plural=False,
    ),
}

COMFORTS = [
    Comfort(id="blanket", label="soft blanket", prep="pull a soft blanket up", tail="snuggled under the blanket"),
    Comfort(id="teddy", label="teddy bear", prep="place a teddy bear nearby", tail="held the teddy bear close"),
    Comfort(id="song", label="quiet song", prep="sing one quiet song", tail="rested after the song"),
]

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Ela", "Mia"]
BOY_NAMES = ["Theo", "Pip", "Ben", "Milo", "Ari", "Noah"]
TRAITS = ["curious", "gentle", "brave", "dreamy", "cheerful", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    comfort: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                for comfort in COMFORTS:
                    combos.append((place, act, prize, comfort.id))
    return combos


def explain_rejection(_: Activity, __: Prize) -> str:
    return "(No story: this bedtime world only uses gentle, sleep-friendly choices.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with rhyme and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--comfort", choices=[c.id for c in COMFORTS])
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.comfort is None or c[3] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid bedtime story combination matches the given options.)")
    place, activity, prize, comfort = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place, activity, prize, comfort, name, gender, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child with a knack for rhyme, using the word "resign".',
        f"Tell a gentle story where {f['hero'].id} wants one more rhyme, but bedtime teaches {f['hero'].id} to resign from play.",
        f"Write a soft story with a lesson learned and a final rhyme before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    comfort: Comfort = f["comfort"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What knack did {hero.id} have in the story?",
            answer=f"{hero.id} had a knack for making rhymes.",
        ),
        QAItem(
            question=f"Why did {hero.id} need to resign from play?",
            answer=f"{hero.id} needed to resign from play because bedtime was here and the room was getting quiet.",
        ),
        QAItem(
            question=f"What did the parent offer to help {hero.id} settle down?",
            answer=f"The parent offered a {comfort.label} and a calm moment beside the bed.",
        ),
        QAItem(
            question=f"What was the lesson learned at the end?",
            answer=f"The lesson learned was that bedtime can be gentle, and a child can rest while still keeping a knack for rhyme.",
        ),
        QAItem(
            question=f"What did {hero.id} hold close while getting ready for sleep?",
            answer=f"{hero.id} held the {prize.label} close while listening to one last rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like night and light.",
        ),
        QAItem(
            question="What does bedtime mean?",
            answer="Bedtime is the time when a child gets ready to sleep.",
        ),
        QAItem(
            question="Why do people use a soft blanket at night?",
            answer="A soft blanket helps a child feel warm and safe while resting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Act,Prize,Comfort) :- setting(Place), activity(Act), prize(Prize), comfort(Comfort).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        next(c for c in COMFORTS if c.id == params.comfort),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, combo in enumerate(valid_combos()):
            params = StoryParams(
                place=combo[0], activity=combo[1], prize=combo[2], comfort=combo[3],
                name=GIRL_NAMES[i % len(GIRL_NAMES)],
                gender="girl" if i % 2 == 0 else "boy",
                parent="mother" if i % 2 == 0 else "father",
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
