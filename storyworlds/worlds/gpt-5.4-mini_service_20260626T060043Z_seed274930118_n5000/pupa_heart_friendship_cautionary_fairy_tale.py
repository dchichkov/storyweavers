#!/usr/bin/env python3
"""
storyworlds/worlds/pupa_heart_friendship_cautionary_fairy_tale.py
=================================================================

A small fairy-tale story world about a pupa, a heart, friendship, and a
careful choice.

Seed tale:
---
In a little mossy hollow, a tiny pupa loved a bright red heart charm that
her friend had given her. One windy evening, the charm rolled toward a dark
bramble path. The pupa wanted to chase it at once, but her friend warned her
that the thorns were sharp and the night was deep. Together they thought of a
safer way, and the heart was saved without anyone getting hurt.

World model:
---
    pupa's curiosity           -> meters["curious"] += 1
    pupa following the heart   -> meters["distance"] += 1; memes["risk"] += 1
    friend warning             -> memes["care"] += 1; memes["fear"] += 1 on pupa
    safe choice                -> memes["trust"] += 1; memes["joy"] += 1
    thorny path + no caution   -> meters["scratch"] += 1; meters["hurt"] += 1
    heart kept close           -> meters["safe"] += 1; memes["peace"] += 1

Style and tone:
---
Fairy-tale, child-facing, gentle, and cautionary: a tempting choice appears,
a friend gives a warning, and the story ends with safety, friendship, and a
clear change in state.
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pupa", "maiden", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"prince", "boy", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    place: str
    indoors: bool
    path: str
    dangers: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    type: str
    kind: str = "character"


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    danger: str
    desired: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


SETTINGS = {
    "mossy_hollow": Setting(
        place="the mossy hollow",
        indoors=False,
        path="the bramble path",
        dangers={"thorns", "dark"},
    ),
    "rose_arch": Setting(
        place="the rose arch",
        indoors=False,
        path="the thorn gate",
        dangers={"thorns"},
    ),
    "lantern_glade": Setting(
        place="the lantern glade",
        indoors=False,
        path="the shadow trail",
        dangers={"dark", "water"},
    ),
}

COMPANIONS = {
    "beetle": Companion(id="beetle", label="a beetle friend", type="beetle"),
    "moth": Companion(id="moth", label="a moth friend", type="moth"),
    "mouse": Companion(id="mouse", label="a mouse friend", type="mouse"),
}

OBJECTS = {
    "heart_charm": ObjectItem(
        id="heart_charm",
        label="heart charm",
        phrase="a bright red heart charm",
        danger="lost",
    ),
    "heart_lantern": ObjectItem(
        id="heart_lantern",
        label="heart lantern",
        phrase="a little heart-shaped lantern",
        danger="dark",
    ),
    "heart_berry": ObjectItem(
        id="heart_berry",
        label="heart berry",
        phrase="a ruby heart berry",
        danger="snatched",
    ),
}

ACTIONS = {
    "follow": {
        "verb": "follow the heart",
        "rush": "dart after the heart",
        "risk": "the thorns could scratch her shell",
        "turn": "the night could swallow the path",
        "safe": "stay by the moss and wait for dawn",
        "finish": "kept the heart close and safe",
    },
    "cross": {
        "verb": "cross the path alone",
        "rush": "run down the path alone",
        "risk": "the dark could make her stumble",
        "turn": "the brambles could snag her",
        "safe": "walk with her friend and carry a lantern together",
        "finish": "crossed safely with a friend beside her",
    },
    "keep": {
        "verb": "keep the heart near",
        "rush": "hide the heart in the dark",
        "risk": "the charm could be lost in the grass",
        "turn": "the wind could roll it away",
        "safe": "tie the heart charm to a ribbon",
        "finish": "tied the heart charm to a ribbon and smiled",
    },
}


@dataclass
class StoryParams:
    setting: str
    action: str
    object: str
    name: str
    companion: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="mossy_hollow", action="follow", object="heart_lantern", name="Pippa", companion="beetle"),
    StoryParams(setting="rose_arch", action="cross", object="heart_charm", name="Mira", companion="moth"),
    StoryParams(setting="lantern_glade", action="keep", object="heart_berry", name="Lulu", companion="mouse"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about a pupa and a heart.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    if args.action and args.object:
        if args.action == "follow" and args.object == "heart_charm":
            raise StoryError("A charm is meant to be kept close, not chased down a dark path.")
    choices = [
        (s, a, o)
        for s in SETTINGS
        for a in ACTIONS
        for o in OBJECTS
        if not (a == "follow" and o == "heart_charm")
    ]
    if args.setting:
        choices = [c for c in choices if c[0] == args.setting]
    if args.action:
        choices = [c for c in choices if c[1] == args.action]
    if args.object:
        choices = [c for c in choices if c[2] == args.object]
    if not choices:
        raise StoryError("No reasonable story matches those options.")
    setting, action, obj = rng.choice(sorted(choices))
    name = args.name or rng.choice(["Pippa", "Mira", "Lulu", "Nina", "Tessa"])
    companion = args.companion or rng.choice(list(COMPANIONS))
    return StoryParams(setting=setting, action=action, object=obj, name=name, companion=companion)


def _story_state(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="pupa", label="the pupa"))
    friend = world.add(Entity(id="friend", kind="character", type=COMPANIONS[params.companion].type, label=COMPANIONS[params.companion].label))
    obj = world.add(Entity(id="heart", kind="thing", type="heart", label=OBJECTS[params.object].label, phrase=OBJECTS[params.object].phrase, owner=hero.id))

    hero.memes["curiosity"] = 1
    hero.memes["love"] = 1
    hero.meters["safe"] = 1

    # Setup
    world.say(f"Once upon a time, in {setting.place}, there lived a tiny pupa named {hero.id}.")
    world.say(f"{hero.id} loved {obj.phrase}, because her friend had given it with a warm smile.")
    world.say(f"That small heart made her feel brave, and it glittered like a promise in the grass.")
    world.para()

    # Tension
    action = ACTIONS[params.action]
    world.say(f"One evening, {obj.phrase} slipped toward {setting.path}.")
    hero.memes["desire"] = 1
    world.say(f"{hero.id} wanted to {action['verb']}, but {friend.label} looked at the path and worried.")
    world.say(f"{friend.label.capitalize()} whispered that {action['risk']} and that {action['turn']}.")
    hero.memes["fear"] = 1
    friend.memes["care"] = 1
    world.para()

    # Turn
    if params.action == "follow":
        hero.meters["distance"] = 1
        hero.memes["risk"] = 1
        world.say(f"{hero.id} paused, then listened to the warning instead of rushing ahead.")
        world.say(f"Together they chose to {action['safe']}, and the heart stayed within sight.")
        hero.memes["trust"] = 1
        hero.memes["joy"] = 1
        hero.meters["safe"] = 2
    elif params.action == "cross":
        hero.meters["distance"] = 1
        world.say(f"{hero.id} took one step, then held still and looked at her friend.")
        world.say(f"She decided not to cross alone. Instead, they chose to {action['safe']}.")
        hero.memes["trust"] = 1
        friend.memes["joy"] = 1
        hero.meters["safe"] = 2
    else:
        world.say(f"{hero.id} tucked the heart close to her shell and thought carefully.")
        world.say(f"She decided to {action['safe']}, so the wind could not carry it away.")
        hero.memes["peace"] = 1
        hero.memes["trust"] = 1
        hero.meters["safe"] = 2

    # Resolution image
    world.say(f"In the end, {hero.id} {action['finish']}, and {friend.label} stayed beside her.")
    world.say(f"The night grew calm, the path stayed dark, and the little heart shone safely in the moss.")
    world.facts.update(hero=hero, friend=friend, obj=obj, action=params.action, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, obj = f["hero"], f["obj"]
    return [
        'Write a short fairy tale about a pupa, a heart, and a careful friend.',
        f"Tell a cautionary story where {hero.id} wants to be reckless with {obj.label}, but friendship leads to a safer choice.",
        "Write a gentle bedtime tale in which a tiny creature listens to a warning before the dark path can cause harm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, obj = f["hero"], f["friend"], f["obj"]
    action = ACTIONS[f["action"]]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about {hero.id}, a tiny pupa who loved {obj.phrase} and listened to a careful friend.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do when the heart moved toward the path?",
            answer=f"{hero.id} wanted to {action['verb']}, but her friend warned her that the path could be dangerous.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.label} keep the heart safe?",
            answer=f"They did not rush into the danger. Instead, they chose a safer way, stayed together, and kept the {obj.label} close.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pupa?",
            answer="A pupa is a young insect that is changing and growing before it becomes an adult insect.",
        ),
        QAItem(
            question="What is a heart in a story like this?",
            answer="A heart can be a lovely symbol or charm that stands for care, love, and friendship.",
        ),
        QAItem(
            question="Why is it wise to listen to a warning near thorns or the dark?",
            answer="Warnings help keep you safe, because thorns can scratch and dark places can hide danger.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
pupa(P) :- hero(P).
friend(F) :- companion(F).
heart(O) :- object(O).
risky(A) :- action(A), A = follow.
risky(A) :- action(A), A = cross.
safe_choice(A) :- action(A), A = keep.
cautionary_story(P, A, O) :- hero(P), action(A), object(O), risky(A).
cautionary_story(P, A, O) :- hero(P), action(A), object(O), safe_choice(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    lines.append(asp.fact("hero", "pupa"))
    lines.append(asp.fact("role", "friendship"))
    lines.append(asp.fact("style", "fairy_tale"))
    lines.append(asp.fact("tone", "cautionary"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import to keep normal execution clingo-free.
    import asp

    program = asp_program("#show cautionary_story/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "cautionary_story"))
    py_set = {
        ("pupa", action, obj)
        for action in ACTIONS
        for obj in OBJECTS
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH between clingo and Python registries:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIONS:
            for o in OBJECTS:
                combos.append((s, a, o))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show cautionary_story/3."))
    return sorted(set(asp.atoms(model, "cautionary_story")))


def build_sample(params: StoryParams) -> StorySample:
    world = _story_state(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} cautionary story combinations:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = resolve_all(args)
        samples = [generate(p) for p in params_list]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} in {p.setting} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
