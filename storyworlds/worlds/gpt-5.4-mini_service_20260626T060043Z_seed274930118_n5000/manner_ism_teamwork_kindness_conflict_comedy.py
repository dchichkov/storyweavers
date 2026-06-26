#!/usr/bin/env python3
"""
A tiny comedic storyworld about manners, teamwork, kindness, and a very silly
problem that gets solved together.

The seed idea: a child-centered scene where a small team is trying to bring a
snack to a gathering, but the manners of the moment matter almost as much as
the snack itself. Conflict comes from a grumpy interruption; teamwork and
kindness fix the mess.

The word "manner-ism" is treated as a playful in-world label for the habit of
using extra-polite phrases and tiny etiquette rituals when people work together.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    crowd: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    spill: str
    keyword: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    helps: set[str]
    needed_for: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prop: str
    name: str
    gender: str
    helper: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def _entity_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _entity_mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def build_story(world: World, hero: Entity, helper: Entity, host: Entity, prop: Entity, act: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved being helpful."
    )
    world.say(
        f"At {world.setting.place}, {hero.id}, {helper.id}, and {host.id} were getting ready for the snack."
    )
    world.say(
        f"They were trying to {act.verb}, and everyone kept practicing the same tiny "
        f"manner-ism: say please, say thank you, and pass the thing before it tips."
    )

    world.lines.append("")
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{hero.id} wanted to {act.verb} right away, because {act.gerund} looked funny and exciting."
    )
    world.say(
        f"But the {prop.label} was wobbly, and {world.setting.crowd} were watching with wide eyes."
    )
    world.say(
        f"When {hero.id} tried to {act.rush}, the {prop.label} nearly got {act.spill}."
    )
    world.say(
        f"That was the comic trouble: one small slip, one big mess, and one very dramatic gasp."
    )

    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0) + 1
    world.lines.append("")
    world.say(
        f"{host.id} held up a hand and said, 'Easy now. We can fix this with teamwork and kindness.'"
    )
    world.say(
        f"{helper.id} steadied one side, {hero.id} held the other, and {host.id} passed a napkin like a tiny hero."
    )

    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    host.memes["kindness"] = host.memes.get("kindness", 0) + 1
    prop.carried_by = hero.id
    prop.meters["stable"] = 1.0
    prop.meters["mess"] = 0.0

    world.say(
        f"Then {hero.id} remembered the best manner-ism of all: ask for help, and give help back."
    )
    world.say(
        f"Together they carried the {prop.label} carefully to the table, and this time it stayed neat."
    )
    world.say(
        f"Everyone laughed, because the snack was safe, the manners were fine, and the big problem had turned into a small joke."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        host=host,
        prop=prop,
        act=act,
        world=world,
    )


SETTINGS = {
    "picnic": Setting(place="the picnic blanket", crowd="the neighbors", afford={"carry", "serve"}),
    "classroom": Setting(place="the classroom table", crowd="the classmates", afford={"carry", "serve"}),
    "kitchen": Setting(place="the kitchen counter", crowd="the family", afford={"carry", "serve"}),
}

ACTIVITIES = {
    "carry": Activity(
        id="carry",
        verb="carry the snack",
        gerund="carrying the snack",
        rush="dash across the blanket",
        mess="sticky",
        spill="sticky all over the cloth",
        keyword="manner-ism",
        risk="spill the snack",
        tags={"teamwork", "kindness", "conflict", "comedy"},
    ),
    "serve": Activity(
        id="serve",
        verb="serve the treats",
        gerund="serving the treats",
        rush="scoop too fast",
        mess="crumbly",
        spill="crumbly crumbs everywhere",
        keyword="manner-ism",
        risk="spill the treats",
        tags={"teamwork", "kindness", "conflict", "comedy"},
    ),
}

PROPS = {
    "cake": Prop(
        id="cake",
        label="cake",
        phrase="a big frosted cake",
        helps={"carry", "serve"},
        needed_for={"carry", "serve"},
    ),
    "punch": Prop(
        id="punch",
        label="juice punch",
        phrase="a huge bowl of juice punch",
        helps={"carry", "serve"},
        needed_for={"carry", "serve"},
    ),
    "cookies": Prop(
        id="cookies",
        label="cookie tray",
        phrase="a tray of smiling cookies",
        helps={"carry", "serve"},
        needed_for={"carry", "serve"},
        plural=False,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Pia"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Theo", "Sam"]
TRAITS = ["cheerful", "curious", "silly", "brave", "gentle", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, act_id, prop_id)
        for place, setting in SETTINGS.items()
        for act_id in setting.afford
        for prop_id, prop in PROPS.items()
        if act_id in prop.helps
    ]


def explain_rejection(activity: Activity, prop: Prop) -> str:
    return (
        f"(No story: {activity.verb} and {prop.label} do not make a reasonable comedy "
        f"problem together in this world.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic manners-and-teamwork storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--mood")
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
    if args.activity and args.prop:
        act = ACTIVITIES[args.activity]
        prop = PROPS[args.prop]
        if args.activity not in prop.helps:
            raise StoryError(explain_rejection(act, prop))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    mood = args.mood or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prop=prop, name=name, gender=gender, helper=helper, mood=mood)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.mood, "kind"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="friend", traits=["helpful", "kind"]))
    host = world.add(Entity(id="Host", kind="character", type="adult", label="host", traits=["calm", "kind"]))
    prop_cfg = PROPS[params.prop]
    prop = world.add(Entity(id=prop_cfg.id, type="thing", label=prop_cfg.label, phrase=prop_cfg.phrase, plural=prop_cfg.plural))
    build_story(world, hero, helper, host, prop, ACTIVITIES[params.activity])
    story_qa = [
        QAItem(
            question=f"What was the manner-ism the children kept practicing at {world.setting.place}?",
            answer="They kept practicing the tiny rule to say please, say thank you, and pass the thing carefully.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} tried to {ACTIVITIES[params.activity].rush}?",
            answer=f"The {prop.label} nearly got {ACTIVITIES[params.activity].spill}, which turned the moment into a funny little mess.",
        ),
        QAItem(
            question="How did the group fix the problem?",
            answer="They used teamwork and kindness: one child steadied the snack, another helped from the other side, and the host passed a napkin.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a manner-ism in this storyworld?",
            answer="A manner-ism is a playful habit of using extra-polite little routines when people work together.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about other people’s feelings.",
        ),
        QAItem(
            question="What does conflict mean?",
            answer="Conflict means people want different things or a problem gets in the way for a moment.",
        ),
    ]
    prompts = [
        f"Write a short comedy story about {params.name} learning a manner-ism while trying to {ACTIVITIES[params.activity].verb}.",
        f"Tell a child-friendly story where kindness and teamwork solve a funny problem with {prop.label}.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.traits:
                bits.append(f"traits={e.traits}")
            print(f"  {e.id}: {', '.join(bits)}")
    if qa:
        print("\n== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="picnic", activity="carry", prop="cake", name="Mia", gender="girl", helper="Ben", mood="silly"),
    StoryParams(place="classroom", activity="serve", prop="cookies", name="Leo", gender="boy", helper="Nora", mood="curious"),
    StoryParams(place="kitchen", activity="carry", prop="punch", name="Ava", gender="girl", helper="Sam", mood="cheerful"),
]


ASP_RULES = r"""
place(picnic). place(classroom). place(kitchen).
activity(carry). activity(serve).
prop(cake). prop(punch). prop(cookies).

affords(picnic,carry). affords(picnic,serve).
affords(classroom,carry). affords(classroom,serve).
affords(kitchen,carry). affords(kitchen,serve).

helps(cake,carry). helps(cake,serve).
helps(punch,carry). helps(punch,serve).
helps(cookies,carry). helps(cookies,serve).

valid(Place,Act,Prop) :- affords(Place,Act), helps(Prop,Act).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in SETTINGS[p].afford:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p, cfg in PROPS.items():
        lines.append(asp.fact("prop", p))
        for a in cfg.helps:
            lines.append(asp.fact("helps", p, a))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def valid_combos_asp() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def format_qa(sample: StorySample) -> str:
    out = []
    for title, items in [("prompts", sample.prompts), ("story qa", sample.story_qa), ("world qa", sample.world_qa)]:
        out.append(f"== {title} ==")
        if title == "prompts":
            for i, p in enumerate(items, 1):
                out.append(f"{i}. {p}")
        else:
            for item in items:
                out.append(f"Q: {item.question}")
                out.append(f"A: {item.answer}")
        out.append("")
    return "\n".join(out).rstrip()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in valid_combos_asp()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
