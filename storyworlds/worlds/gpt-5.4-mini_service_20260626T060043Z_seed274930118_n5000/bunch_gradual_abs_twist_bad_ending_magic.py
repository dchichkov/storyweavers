#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bunch_gradual_abs_twist_bad_ending_magic.py
===============================================================================================================

A small animal-story world about a bunch of animals, a gradual twist, and a
magic object that promises a fix but leads to a bad ending.

The seed words are woven into the premise:
- bunch: the hero is part of a bunch of animal friends
- gradual: the trouble changes slowly, not all at once
- abs: treated as "absolutely" in the child-facing story voice and as a named
  registry word for the source prompt
- Twist / Bad Ending / Magic: narrative instruments and story events

The world model uses typed entities with physical meters and emotional memes.
A short source tale is imagined first, then the story is built from state
changes: gathering, teasing out a gradual problem, a magical turn, and a final
ending image that shows what changed.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "mouse", "cat", "dog", "bear", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    clue: str
    mess: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    twist: str
    bad_ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    magic: str
    hero: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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


def _inc(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


@dataclass
class Rule:
    name: str
    apply: callable


def _r_grass(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("wait", 0) < THRESHOLD:
            continue
        if ("grass", hero.id) in world.fired:
            continue
        world.fired.add(("grass", hero.id))
        _inc(hero.meters, "bother", 1)
        out.append(f"The grass seemed to scratch at {hero.label} a little more each minute.")
    return out


def _r_magic_blowback(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("magic", 0) < THRESHOLD:
            continue
        if hero.meters.get("bother", 0) < THRESHOLD:
            continue
        if ("blowback", hero.id) in world.fired:
            continue
        world.fired.add(("blowback", hero.id))
        _inc(hero.memes, "fear", 1)
        _inc(hero.meters, "wind", 1)
        out.append(f"The magic answered with a twist, and the air began to tug at {hero.label}'s ears.")
    return [s for s in out if s]


def _r_bad_ending(world: World) -> list[str]:
    for hero in world.characters():
        if hero.meters.get("wind", 0) < THRESHOLD:
            continue
        if ("bad_ending", hero.id) in world.fired:
            continue
        world.fired.add(("bad_ending", hero.id))
        hero.memes["sad"] = hero.memes.get("sad", 0) + 1
        hero.memes["hope"] = 0.0
        return ["__bad_ending__"]
    return []


CAUSAL_RULES = [
    Rule("grass", _r_grass),
    Rule("magic_blowback", _r_magic_blowback),
    Rule("bad_ending", _r_bad_ending),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__bad_ending__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, activity: Activity, magic_item: MagicItem, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="rabbit", label=hero_name))
    bunch = world.add(Entity(id="bunch", kind="character", type="fox", label="a bunch of friends", plural=True))
    charm = world.add(Entity(
        id=magic_item.id,
        type="magic",
        label=magic_item.label,
        phrase=magic_item.phrase,
        owner=hero.id,
    ))

    # Act 1: setup
    world.say(f"{hero.label} was part of a bunch of little animal friends who loved the {setting.place}.")
    world.say(f"They had found {magic_item.phrase}, and it looked absolutely ready for a game.")
    world.say(f"{hero.label} wanted to {activity.verb}, because {activity.clue}.")

    # Act 2: gradual tension
    world.para()
    world.say(f"At first, nothing seemed wrong. Then, little by little, {activity.omen} started to show.")
    hero.meters["wait"] = 1
    hero.meters["bother"] = 1
    propagate(world, narrate=True)
    world.say(f"The bunch of friends kept watching, because the trouble was only growing gradually.")

    # Act 3: magic twist and bad ending
    world.para()
    hero.meters["magic"] = 1
    world.say(f"{hero.label} tried the magic anyway and gave the {magic_item.label} a careful tap.")
    world.say(f"The spell promised {magic_item.effect}, and for one bright second it felt like a perfect fix.")
    world.say(f"Then came the twist: {magic_item.twist}.")
    propagate(world, narrate=True)
    if hero.meters.get("wind", 0) >= THRESHOLD:
        world.say(f"After that, the bad ending arrived: {magic_item.bad_ending}.")
    world.say(f"In the last image, the bunch was still together, but the magic had blown the game apart.")

    world.facts.update(
        hero=hero,
        bunch=bunch,
        charm=charm,
        activity=activity,
        magic_item=magic_item,
        setting=setting,
    )
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", weather="breezy", affords={"listen"}),
    "hill": Setting(place="the hill", weather="windy", affords={"listen"}),
    "pond": Setting(place="the pond", weather="still", affords={"listen"}),
}

ACTIVITIES = {
    "listen": Activity(
        id="listen",
        verb="listen for the tiny bird song",
        gerund="listening for bird song",
        clue="the birds liked to hide their songs in the grass",
        mess="restless",
        omen="a little shiver in the reeds",
        tags={"bunch", "gradual"},
    ),
}

MAGIC_ITEMS = {
    "shell": MagicItem(
        id="shell",
        label="a shiny shell",
        phrase="a shiny shell with a swirl on it",
        effect="a song as sweet as honey",
        twist="the swirl began to spin faster and faster",
        bad_ending="the shell whistled so loudly that every bird flew away",
        tags={"magic", "twist", "bad ending"},
    ),
    "stick": MagicItem(
        id="stick",
        label="a magic stick",
        phrase="a magic stick wrapped in blue moss",
        effect="a dance of sparkles",
        twist="the blue moss loosened and fluttered like tiny flags",
        bad_ending="the sparkles startled the whole bunch into hiding",
        tags={"magic", "twist", "bad ending"},
    ),
}

NAMES = ["Milo", "Ruby", "Pip", "Nora", "Toby", "Daisy", "Luna", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for magic in MAGIC_ITEMS:
                out.append((place, act, magic))
    return out


def explain_rejection(activity: str, magic: str) -> str:
    return f"(No story: the activity {activity} and magic item {magic} do not form a reasonable animal tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a bunch, gradual trouble, and magic twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--hero")
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
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, magic = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, magic=magic, hero=hero)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story about a bunch of friends in {f["setting"].place} with a gradual twist and magic.',
        f"Tell a short tale where {f['hero'].label} and a bunch of friends try {f['magic_item'].phrase} and the ending goes badly.",
        f'Write a child-friendly story that includes the words "bunch", "gradual", and "magic".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    magic_item = f["magic_item"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little rabbit who was with a bunch of animal friends.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.label} wanted to {activity.verb}, but the trouble grew gradually before the magic started.",
        ),
        QAItem(
            question=f"What happened when the magic twist came?",
            answer=f"The {magic_item.label} turned the story toward a bad ending, and the birds flew away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gradual mean?",
            answer="Gradual means something changes slowly, step by step, instead of all at once.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you expected to happen next.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is pretend power that can make strange and surprising things happen.",
        ),
    ]


ASP_RULES = r"""
combo(Place,A,M) :- affords(Place,A), magic_item(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for mid in MAGIC_ITEMS:
        lines.append(asp.fact("magic_item", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - p:
        print("only in clingo:", sorted(a - p))
    if p - a:
        print("only in python:", sorted(p - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], MAGIC_ITEMS[params.magic], params.hero)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, activity, magic in valid_combos():
            params = StoryParams(place=place, activity=activity, magic=magic, hero="Milo")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
