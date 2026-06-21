#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/japanese_card_dim_humor_magic_space_adventure.py
================================================================================

A small standalone story world for a humorous, magical space adventure about a
child-friendly crew, a tiny problem with a dim card, and a bright fix.

Seed words / style cues:
- japanese
- card-dim
- Humor
- Magic
- Space Adventure

This world keeps the plot tiny and state-driven: a crew finds a card that dims
their ship's map, tries a silly fix, gets a surprise from a magical helper, and
ends with a bright image that proves the change.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIGHT_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_darken(world: World) -> list[str]:
    out = []
    card = world.entities.get("card")
    if not card or card.meters["dimmed"] < THRESHOLD:
        return out
    sig = ("darken",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ship = world.entities.get("ship")
    if ship:
        ship.meters["vision"] -= 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["worry"] += 1
    out.append("__gloom__")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    if world.entities.get("helper") and world.entities["helper"].memes["joke"] >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("darken", _r_darken), Rule("laugh", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Setting:
    id: str
    place: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Card:
    id: str
    label: str
    phrase: str
    color: str
    magic: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    label: str
    text: str
    power: int
    funny: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    card: str
    fix: str
    hero: str
    friend: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "orbital_hall": Setting("orbital_hall", "the moonlit hallway of the station", "bright and bouncy"),
    "star_barn": Setting("star_barn", "the cargo bay that looked like a little space barn", "silly and cozy"),
    "planet_garden": Setting("planet_garden", "the glass garden dome", "quiet and shiny"),
}

CARDS = {
    "dim_card": Card("dim_card", "card-dim", "a card that made the map go dim", "silver", magic=True),
    "moon_card": Card("moon_card", "a moon card", "a moon card with sleepy sparkles", "pale blue", magic=True),
    "japanese_card": Card("japanese_card", "japanese card", "a japanese card with a smiling star", "red", magic=True),
}

FIXES = {
    "chant": Fix("chant", "chant", "singing a tiny rhyme", 2, "and the whole crew giggled"),
    "polish": Fix("polish", "polish", "polishing the card with a soft cloth", 3, "and it shone like a teaspoon"),
    "moonbeam": Fix("moonbeam", "moonbeam", "asking the moonbeam to help", 4, "and the light came back with a wink"),
}

GIRL_NAMES = ["Mina", "Aiko", "Luna", "Sora", "Nori", "Mira"]
BOY_NAMES = ["Kiko", "Ren", "Taro", "Noa", "Haru", "Piko"]
TRAITS = ["curious", "cheerful", "silly", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, f) for s in SETTINGS for c in CARDS for f in FIXES if CARDS[c].magic]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magical space-adventure story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--card", choices=CARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--n", type=int, default=1)
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
    combos = valid_combos()
    if args.setting and args.card and args.fix and (args.setting, args.card, args.fix) not in combos:
        raise StoryError("That combination does not make a reasonable story.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    card = args.card or rng.choice(sorted(CARDS))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(setting, card, fix, hero, friend)


def _dim_card(world: World, card: Entity) -> None:
    card.meters["dimmed"] += 1
    card.meters["shine"] -= 1
    propagate(world, narrate=False)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    card = CARDS[params.card]
    fix = FIXES[params.fix]
    hero = world.add(Entity(params.hero, "character", "child", traits=["curious"]))
    friend = world.add(Entity(params.friend, "character", "child", traits=["silly"]))
    helper = world.add(Entity("helper", "character", "astronaut", label="Captain Kira"))
    ship = world.add(Entity("ship", "thing", "ship", label="the little ship"))
    card_ent = world.add(Entity("card", "thing", "card", label=card.label))
    helper.memes["joke"] = 1.0
    ship.meters["vision"] = 2.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1

    world.say(
        f"{hero.id} and {friend.id} floated through {setting.place} on a bright, bouncy day. "
        f"Everything looked like a game."
    )
    world.say(
        f"They found {card.phrase}, and when {hero.id} held it up, the star map went card-dim."
    )
    world.para()
    hero.memes["curiosity"] += 1
    friend.memes["worry"] += 1
    world.say(
        f'"That is a very grumpy card," {friend.id} said. '
        f'"It made the route look sleepy."'
    )
    world.say(f'"I can fix it," {hero.id} said, with a laugh that bounced like a marble.')
    if fix.id == "chant":
        world.say(f"{hero.id} tried {fix.text}, which was absurdly tiny.")
    elif fix.id == "polish":
        world.say(f"{hero.id} tried {fix.text}, using a cloth from the snack kit.")
    else:
        world.say(f"{hero.id} tried {fix.text}, even though the moon was being very dramatic.")
    _dim_card(world, card_ent)
    world.para()
    if fix.power >= 3:
        card_ent.meters["dimmed"] = 0.0
        card_ent.meters["shine"] = 2.0
        hero.memes["relief"] += 1
        friend.memes["relief"] += 1
        world.say(
            f"Then Captain Kira winked from the window and waved a moonbeam over the card. "
            f"The little {card.label} lit up again, shiny and proud."
        )
        world.say(
            f"{friend.id} giggled so hard that {hero.id} nearly dropped the map. "
            f"The route sprang back, bright as a ribbon."
        )
        world.say(
            f"In the end, the crew sailed on under the glowing stars, and the "
            f"{card.label} stayed bright in {hero.id}'s hand."
        )
        outcome = "fixed"
    else:
        world.say(
            f"The silly fix only made everyone laugh, and the map stayed dim for one more turn."
        )
        world.say(
            f"So {helper.label_word} shone a gentle moonbeam anyway, and the crew finally saw the way."
        )
        outcome = "rescued"
    world.facts.update(
        hero=hero, friend=friend, helper=helper, ship=ship, card=card, fix=fix,
        setting=setting, outcome=outcome
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous space-adventure story that includes the words "japanese" and "card-dim".',
        f"Tell a magical story where {f['hero'].id} and {f['friend'].id} find a card-dim map and then make it bright again.",
        f"Write a child-friendly spaceship story with a silly problem, a magic helper, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, card, fix = f["hero"], f["friend"], f["card"], f["fix"]
    answers = [
        QAItem(
            question="What problem did the children find?",
            answer=f"They found {card.phrase}, and it made the star map go card-dim. That made the route hard to read."
        ),
        QAItem(
            question="How did they try to solve it?",
            answer=f"{hero.id} tried {fix.text}. It was a small, silly attempt, but it showed they wanted to help."
        ),
    ]
    if f["outcome"] == "fixed":
        answers.append(
            QAItem(
                question="What made the card bright again?",
                answer="Captain Kira waved a moonbeam over it, and the card shone again. The magic brought the map back to life."
            )
        )
    else:
        answers.append(
            QAItem(
                question="What made the ending work?",
                answer="The crew laughed at the silly fix, then the helper used a moonbeam. That turned the dim map bright enough to follow."
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a map help you do in space?",
            answer="A map helps you know where to go. In a space adventure, it can guide a ship to the next place."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something that can do surprising things in a story. It can make a problem easier or make something glow."
        ),
        QAItem(
            question="What is funny about a card-dim map?",
            answer="It is funny because the map becomes hard to see, even though everyone wants to go exploring. A silly problem can still be fixed in a playful way."
        ),
        QAItem(
            question="What does japanese mean in this story world?",
            answer="It is one of the words the story must include. The world treats it like a special label on a magical card."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_hall", "dim_card", "polish", "Mina", "Ren"),
    StoryParams("star_barn", "japanese_card", "chant", "Sora", "Kiko"),
    StoryParams("planet_garden", "moon_card", "moonbeam", "Luna", "Haru"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CARDS.items():
        lines.append(asp.fact("card", cid))
        if c.magic:
            lines.append(asp.fact("magic", cid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,F) :- setting(S), card(C), fix(F), magic(C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate:")
        print("  only in asp:", sorted(a - p))
        print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, card=None, fix=None, hero=None, friend=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, c, f in combos:
            print(f"  {s:14} {c:12} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
