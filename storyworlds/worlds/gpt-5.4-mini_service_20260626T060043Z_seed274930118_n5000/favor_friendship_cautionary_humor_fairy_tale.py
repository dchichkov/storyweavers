#!/usr/bin/env python3
"""
storyworlds/worlds/favor_friendship_cautionary_humor_fairy_tale.py
===================================================================

A tiny fairy-tale story world about friendship, favors, and the comic danger of
asking for too much at once.

Seed tale:
---
A small child in a fairy-tale village needed a favor from a friend. The child
kept asking, the friend kept helping, and the requests grew too tall and too
silly. At last the child learned to pause, make a careful plan, and give a favor
back so the friendship would stay warm and fair.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "fairy", "woman", "sister"}
        male = {"boy", "prince", "king", "wizard", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    feature: str
    mood: str


@dataclass
class Favor:
    id: str
    label: str
    phrase: str
    verb: str
    burden: str
    comedy: str
    remedy: str
    risk: str
    kind: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    place: str
    favor: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "brook": Setting(place="the mossy brook", feature="a wobbly stone bridge", mood="bright"),
    "tower": Setting(place="the little tower garden", feature="a spiral stair", mood="windy"),
    "orchard": Setting(place="the apple orchard", feature="a tall ladder", mood="golden"),
    "cottage": Setting(place="the cottage lane", feature="a lantern hook", mood="soft"),
}

FAVORS = {
    "bridge": Favor(
        id="bridge",
        label="a bridge favor",
        phrase="to hold the rope bridge steady",
        verb="cross the brook",
        burden="the bridge wiggled like a noodle",
        comedy="the bridge gave a tiny wiggle-waggle as if it were ticklish",
        remedy="they should use the stepping stones and let the rope dry",
        risk="the bridge could flop and splash",
        kind="rope",
        tags={"brook", "bridge", "wet"},
    ),
    "lantern": Favor(
        id="lantern",
        label="a lantern favor",
        phrase="to lend the lantern for the dark path",
        verb="walk home safely",
        burden="the path went dim as a bedtime whisper",
        comedy="the lantern blinked like a sleepy eye",
        remedy="they should wait for moonlight and carry a candle together",
        risk="the dark path could twist their toes and their temper",
        kind="light",
        tags={"lantern", "dark", "light"},
    ),
    "ladder": Favor(
        id="ladder",
        label="a ladder favor",
        phrase="to steady the apple ladder",
        verb="pick apples",
        burden="the ladder wobbled like jelly in a teaspoon",
        comedy="the ladder shivered so much the apples seemed to giggle",
        remedy="they should tie the ladder and gather apples from the lower boughs",
        risk="the ladder could squeak and sway",
        kind="wood",
        tags={"orchard", "ladder", "apple"},
    ),
    "basket": Favor(
        id="basket",
        label="a basket favor",
        phrase="to carry the heavy basket of turnips",
        verb="bring the harvest home",
        burden="the basket grew heavy as a king's hat",
        comedy="the basket seemed to puff itself up like a proud goose",
        remedy="they should split the load and take two smaller trips",
        risk="the basket could tip and tumble",
        kind="weight",
        tags={"cottage", "basket", "harvest"},
    ),
}

HERO_NAMES = ["Mira", "Pip", "Lina", "Ned", "Tilda", "Rowan", "Ollie", "Faye"]
FRIEND_NAMES = ["Bran", "Wren", "Elsa", "Basil", "Nora", "Finn", "Sage", "Perry"]
TRAITS = ["cheerful", "curious", "shy", "spirited", "thoughtful", "bouncy"]
HERO_TYPES = ["girl", "boy"]
FRIEND_TYPES = ["fairy", "fox", "rabbit", "bird", "mouse"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_overask(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("ask", 0) < THRESHOLD:
        return out
    if hero.memes.get("impulse", 0) < THRESHOLD:
        return out
    if hero.meters.get("favor_load", 0) < THRESHOLD:
        return out
    if hero.memes.get("comic_trouble", 0) >= THRESHOLD:
        return out
    hero.memes["comic_trouble"] = 1
    out.append("The favor pile grew so high that the situation turned funny and a little wobbly.")
    return out


def _r_friendship_soften(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes.get("apology", 0) < THRESHOLD:
        return out
    if hero.memes.get("gratitude", 0) < THRESHOLD:
        return out
    if hero.memes.get("shared_help", 0) < THRESHOLD:
        return out
    if hero.memes.get("warmth", 0) >= THRESHOLD:
        return out
    hero.memes["warmth"] = 1
    friend.memes["warmth"] = 1
    out.append("The friendship grew warm again.")
    return out


CAUSAL_RULES = [Rule("overask", _r_overask), Rule("friendship_soften", _r_friendship_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, fid) for place in SETTINGS for fid in FAVORS if place in FAVORS[fid].tags)


def select_favor(place: str, favor_id: str) -> Favor:
    fav = FAVORS[favor_id]
    if place not in fav.tags:
        raise StoryError(f"(No story: {fav.label} does not fit {place}.)")
    return fav


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    favor = FAVORS[params.favor]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, meters={}, memes={}))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend, meters={}, memes={}))
    favor_obj = world.add(Entity(id="favor", type=favor.kind, label=favor.label, phrase=favor.phrase, owner="friend"))

    hero.memes["love_friend"] = 1
    friend.memes["love_friend"] = 1

    world.say(f"Long ago, in {setting.place}, there lived {hero.label}, a {params.trait} little {params.hero_type}.")
    world.say(f"{hero.label} and {friend.label} were friends, and each liked to do a small favor for the other now and then.")
    world.say(f"One day, {hero.label} needed {favor.phrase}, because {favor.verb} was not easy on that day.")
    world.para()
    world.say(f"The trouble was that {favor.burden}.")
    hero.memes["ask"] = 1
    hero.memes["impulse"] = 1
    hero.meters["favor_load"] = 1

    if favor.id == "bridge":
        world.say(f"{friend.label} laughed, because {favor.comedy}.")
    elif favor.id == "lantern":
        world.say(f"{friend.label} smiled, because {favor.comedy}.")
    elif favor.id == "ladder":
        world.say(f"{friend.label} blinked, because {favor.comedy}.")
    else:
        world.say(f"{friend.label} snorted, because {favor.comedy}.")

    world.say(f"But {friend.label} also warned, \"A favor is a gift, not a pile of pebbles. Too many at once can tumble over.\"")
    world.say(f"{hero.label} wanted the favor very badly and reached again and again, as if one more ask might make the task easier.")
    hero.memes["defiance"] = 1
    hero.meters["favor_load"] = 2
    propagate(world, narrate=True)
    world.para()

    world.say(f"Then {hero.label} paused and looked at {friend.label}. \"I see the joke now,\" {hero.label} said. \"I was being greedy with kindness.\"")
    hero.memes["apology"] = 1
    hero.memes["gratitude"] = 1
    friend.memes["forgiveness"] = 1
    world.say(f"So {hero.label} offered a favor back: {favor.remedy}.")
    hero.memes["shared_help"] = 1
    friend.memes["shared_help"] = 1
    hero.memes["comic_trouble"] = 0
    friend.memes["comic_trouble"] = 0
    propagate(world, narrate=True)

    world.say(f"At last, the two friends did it the careful way. {hero.label} and {friend.label} finished their work together, and the day felt light again.")
    world.say(f"In the end, the favor was given, the warning was remembered, and the friendship stayed warm as fresh bread.")

    world.facts = {
        "hero": hero,
        "friend": friend,
        "favor": favor_obj,
        "favor_def": favor,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    fav = f["favor_def"]
    return [
        f'Write a fairy tale about a child named {hero.label} and a friend who exchange a favor without losing patience.',
        f"Tell a humorous cautionary story where {hero.label} wants {fav.phrase} from {friend.label}, but learns to ask carefully.",
        "Write a short fairy tale about friendship, a tricky favor, and a happy, sensible ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    fav = f["favor_def"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who did {hero.label} ask for help in {setting.place}?",
            answer=f"{hero.label} asked {friend.label} for a favor in {setting.place}.",
        ),
        QAItem(
            question=f"What was the tricky favor about?",
            answer=f"It was {fav.phrase}, and that mattered because {fav.burden}.",
        ),
        QAItem(
            question=f"Why was the story funny and cautionary at the same time?",
            answer=f"It was funny because {fav.comedy}, but cautionary because too many asks can make friendship feel wobbly.",
        ),
        QAItem(
            question=f"What did {hero.label} do at the end?",
            answer=f"{hero.label} stopped pushing, said sorry, and offered a favor back so the work could be done safely together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a favor?",
            answer="A favor is a kind helpful act you do for someone else, usually without expecting a big reward.",
        ),
        QAItem(
            question="Why should friends take turns helping?",
            answer="Friends take turns helping so one friend does not do all the work and the friendship stays fair.",
        ),
        QAItem(
            question="Why is it silly to ask for too many things at once?",
            answer="If you ask for too many things at once, the work can get tangled and the helper may feel overloaded.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for tag in FAVORS:
            if place in FAVORS[tag].tags:
                lines.append(asp.fact("offers", place, tag))
    for fid, fav in FAVORS.items():
        lines.append(asp.fact("favor", fid))
        for tag in sorted(fav.tags):
            lines.append(asp.fact("fits", fid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Favor) :- place(Place), favor(Favor), offers(Place, Favor).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world about friendship, favors, and careful humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--favor", choices=FAVORS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    combos = valid_combos()
    if args.place or args.favor:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.favor is None or c[1] == args.favor)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, favor = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, favor=favor, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/favor pairs:\n")
        for place, fav in combos:
            print(f"  {place:12} {fav}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="brook", favor="bridge", hero="Mira", hero_type="girl", friend="Bran", friend_type="fairy", trait="curious"),
            StoryParams(place="orchard", favor="ladder", hero="Pip", hero_type="boy", friend="Wren", friend_type="bird", trait="cheerful"),
            StoryParams(place="cottage", favor="basket", hero="Lina", hero_type="girl", friend="Nora", friend_type="mouse", trait="thoughtful"),
            StoryParams(place="tower", favor="lantern", hero="Ned", hero_type="boy", friend="Sage", friend_type="fox", trait="spirited"),
        ]
        samples = [generate(p) for p in curated]
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
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend} | {p.place} | {p.favor}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
