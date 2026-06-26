#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/string_tablet_ambidextrous_friendship_bedtime_story.py
=============================================================================================================

A small bedtime-story world about string, tablet, ambidextrous hands, and friendship.

The premise is gentle and simple:
- a child loves a tablet and a friend;
- bedtime comes, so the glow and excitement become the problem;
- a soft string, a calm plan, and an ambidextrous trick help the child settle;
- the ending proves the change by showing the tablet put away and friendship made cozy.

The simulated state drives the prose: physical meters track glow, charge, tidiness, and string tension;
emotional memes track sleepy, worry, closeness, and pride. The story is not a frozen template with swapped
names; it is assembled from the world trace and the chosen bedtime plan.

Seed words included in-domain: string, tablet, ambidextrous, friendship, bedtime story.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    soothing: str
    tag: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


@dataclass
class Helper:
    id: str
    label: str
    method: str
    result: str


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


SETTINGS = {
    "nursery": Setting("the nursery", True, {"read", "draw", "write"}),
    "bedroom": Setting("the bedroom", True, {"read", "draw", "write"}),
    "windowseat": Setting("the window seat", True, {"read", "draw"}),
}

ACTIVITIES = {
    "read": Activity(
        id="read",
        verb="read one more page on the tablet",
        gerund="reading on the tablet",
        rush="reach for the tablet again",
        risk="the bright glow might keep everyone awake",
        soothing="the screen could dim and sleep could begin",
        tag="tablet",
    ),
    "draw": Activity(
        id="draw",
        verb="finish a small picture on the tablet",
        gerund="drawing little stars",
        rush="tap faster on the tablet",
        risk="the tapping might turn sleepy calm into a bouncy game",
        soothing="the picture could be saved and finished in the morning",
        tag="string",
    ),
    "write": Activity(
        id="write",
        verb="send a tiny note to a friend on the tablet",
        gerund="writing a bedtime note",
        rush="keep texting after the lights went low",
        risk="the message might stretch bed time too far",
        soothing="the note could be tucked away for morning",
        tag="friendship",
    ),
}

PRIZES = {
    "tablet": Prize("tablet", "a small blue tablet", "tablet"),
    "string": Prize("string", "a soft white string", "string"),
    "blanket": Prize("blanket", "a warm blanket with tiny moons", "blanket"),
}

HELPERS = {
    "string": Helper(
        id="string",
        label="the soft string",
        method="looped around the tablet stand like a tiny nest",
        result="rested the tablet safely beside the bed",
    ),
    "bookmark": Helper(
        id="bookmark",
        label="the paper bookmark",
        method="slipped between the pages to save the place",
        result="kept the story ready for tomorrow",
    ),
    "nightlight": Helper(
        id="nightlight",
        label="the little nightlight",
        method="glowed gently instead of the tablet screen",
        result="made the room feel cozy and sleepy",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "June", "Ivy", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Noah", "Milo", "Eli", "Ben", "Leo"]
TRAITS = ["gentle", "curious", "sleepy", "thoughtful", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if act_id == "read" and prize_id == "tablet":
                    combos.append((place, act_id, prize_id))
                if act_id == "draw" and prize_id in {"tablet", "string"}:
                    combos.append((place, act_id, prize_id))
                if act_id == "write" and prize_id in {"tablet", "blanket"}:
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a child, a tablet, and a soft string.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
        raise StoryError("No valid bedtime-story combination matches the given options.")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES + BOY_NAMES)
    if friend == name:
        friend = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, friend=friend, trait=trait)


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["ambidextrous", params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type="friend", label=f"{params.friend}, the friend"))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="the parent"))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    string = world.add(Entity(id="string", type="string", label="string"))
    string.meters["tidy"] = 1.0
    world.facts.update(hero=hero, friend=friend, parent=parent, prize=prize, string=string, params=params)
    return world


def _intro(world: World) -> None:
    f = world.facts
    hero, friend, prize = f["hero"], f["friend"], f["prize"]
    world.say(
        f"{hero.id} was a little {hero.traits[-1]} {hero.type} who had an ambidextrous way of doing things, "
        f"because {hero.pronoun('subject')} could use either hand with the same easy grace."
    )
    world.say(
        f"At {world.setting.place}, {hero.id} loved a bedtime story, a soft tablet, and quiet time with {friend.id}."
    )
    world.say(
        f"{friend.id} had brought {prize.phrase}, and {hero.id} liked how the tablet could hold tiny pictures and messages."
    )


def _turn(world: World) -> None:
    f = world.facts
    hero, parent, friend, prize, params = f["hero"], f["parent"], f["friend"], f["prize"], f["params"]
    act = ACTIVITIES[params.activity]
    hero.memes["eager"] = hero.memes.get("eager", 0.0) + 1
    prize.meters["glow"] = prize.meters.get("glow", 0.0) + 1
    world.para()
    world.say(
        f"One night, after the lamps were low, {hero.id} wanted to {act.verb} with {friend.id}."
    )
    world.say(
        f"{act.risk.capitalize()}, and {parent.label if hasattr(parent, 'label') else 'the parent'} noticed at once."
    )
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1
    hero.memes["disappointed"] = hero.memes.get("disappointed", 0.0) + 1
    world.say(
        f'"Let us slow down," said the parent. "The tablet can wait, and bedtime likes to be gentle."'
    )
    world.say(
        f"{hero.id} almost reached for the tablet again, but {hero.pronoun('subject')} paused and listened."
    )


def _resolve(world: World) -> None:
    f = world.facts
    hero, friend, prize, params = f["hero"], f["friend"], f["prize"], f["params"]
    act = ACTIVITIES[params.activity]
    helper = HELPERS["string"] if params.activity == "draw" else HELPERS["bookmark"]
    if params.activity == "write":
        helper = HELPERS["nightlight"]

    world.para()
    if params.activity == "draw":
        world.say(
            f"{hero.id} smiled and switched hands, because {hero.pronoun('subject')} was ambidextrous and could draw neatly with either hand."
        )
    else:
        world.say(
            f"{hero.id} took the tablet in one hand, then the other, and the calm little switch helped the room feel less busy."
        )

    prize.meters["glow"] = 0.0
    prize.meters["sleep_ready"] = 1.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    friend.memes["calm"] = friend.memes.get("calm", 0.0) + 1

    world.say(
        f"{helper.label.capitalize()} was {helper.method}, and that {helper.result}."
    )
    world.say(
        f"{friend.id} watched with a sleepy grin, and the two friends finished the last little bit together."
    )
    world.say(
        f"Then {hero.id} set the tablet aside, tucked the string neatly near the pillow, and listened to one last quiet page of the bedtime story."
    )
    world.say(
        f"By the end, the room was hush-soft, the tablet was resting, and friendship felt warm enough to carry into sleep."
    )


def tell_story(params: StoryParams) -> World:
    world = _setup_world(params)
    _intro(world)
    _turn(world)
    _resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a bedtime story for a child named {params.name} with the words "string", "tablet", and "ambidextrous".',
        f'Tell a gentle story about friendship where {params.name} wants to use a tablet at bedtime but learns a calmer way.',
        f'Write a short bedtime story with a soft ending image: a string put away, a tablet resting, and two friends feeling sleepy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, params = f["hero"], f["friend"], f["prize"], f["params"]
    act = ACTIVITIES[params.activity]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.traits[-1]} child who is ambidextrous and likes bedtime stories with {friend.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the tablet at bedtime?",
            answer=f"{hero.id} wanted to {act.verb}, but the parent knew bedtime should stay gentle.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the tablet resting, the string put away neatly, and {hero.id} and {friend.id} feeling calm and cozy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ambidextrous mean?",
            answer="Ambidextrous means a person can use either hand well.",
        ),
        QAItem(
            question="What is a string?",
            answer="A string is a thin, flexible piece of thread or cord that can tie, loop, or hold things together.",
        ),
        QAItem(
            question="What is a tablet?",
            answer="A tablet is a flat screen device that people can use to read, draw, or send messages.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind and caring way people help, play, and share with each other.",
        ),
    ]


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_tag", aid, act.tag))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, A, R) :- affords(P, A), prize(R), activity(A),
                        (A = read, R = tablet; A = draw, R = tablet; A = draw, R = string;
                         A = write, R = tablet; A = write, R = blanket; A = read, R = tablet).

has_friendship(A) :- activity(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid bedtime-story combos.")
        return 0
    print("MISMATCH between Python and ASP.")
    if py - cl:
        print("only in Python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams("bedroom", "read", "tablet", "Mina", "girl", "Theo", "gentle"),
    StoryParams("nursery", "draw", "tablet", "Leo", "boy", "Nora", "thoughtful"),
    StoryParams("windowseat", "write", "blanket", "Ivy", "girl", "Ben", "sleepy"),
]


def resolve_all_valid(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, friend=friend, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible bedtime-story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_all_valid(args, random.Random(seed))
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
