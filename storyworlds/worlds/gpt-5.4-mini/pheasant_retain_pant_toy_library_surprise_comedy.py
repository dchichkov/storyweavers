#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pheasant_retain_pant_toy_library_surprise_comedy.py
===================================================================================

A standalone storyworld for a tiny comedy set in a toy library.

Premise:
- A child visits a toy library.
- A surprise happens involving a pheasant.
- The child tries to retain a toy and keep a straight face, but ends up panting.
- A calm librarian turns the surprise into a funny, safe ending.

This world keeps the simulation small: typed entities with physical meters and
emotional memes, a few causal rules, a reasonableness gate, and an inline ASP
twin for parity checking.

Seed words: pheasant, retain, pant
Setting: toy library
Style: comedy
Feature: surprise
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"librarian": "librarian"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    label: str
    quiet_rule: str
    shelves: str
    surprise_place: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Toy:
    id: str
    label: str
    phrase: str
    surprise: str
    retainable: bool = True
    noisy: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Surprise:
    id: str
    label: str
    entrance: str
    effect: str
    comedy: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
@dataclass
class StoryParams:
    setting: str
    toy: str
    surprise: str
    hero: str
    hero_gender: str
    librarian: str
    librarian_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    "toy_library": Setting("toy_library", "the toy library",
                           "whispering voices only", "rows of toy shelves",
                           "the checkout desk"),
}

TOYS = {
    "bear": Toy("bear", "plush bear", "a plush bear", "retained the bear",
                retainable=True, noisy=False, tags={"toy", "retain"}),
    "robot": Toy("robot", "wind-up robot", "a wind-up robot", "retained the robot",
                 retainable=True, noisy=True, tags={"toy", "retain"}),
    "kite": Toy("kite", "tiny kite", "a tiny kite", "retained the kite",
                retainable=True, noisy=True, tags={"toy", "retain"}),
    "train": Toy("train", "wooden train", "a wooden train", "retained the train",
                 retainable=True, noisy=False, tags={"toy", "retain"}),
}

SURPRISES = {
    "pheasant": Surprise(
        "pheasant", "pheasant",
        "a feathered pheasant strutted in through the open door",
        "the bird bobbed its head at every shelf",
        "the pheasant looked as proud as a parade marshal",
        harmless=True, tags={"pheasant", "surprise"},
    ),
    "popper": Surprise(
        "popper", "party popper",
        "a party popper went pop by mistake",
        "confetti drifted over the checkout desk",
        "even the pencils seemed to clap",
        harmless=True, tags={"surprise", "pop"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Sam"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_pant(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["dazzled"] < THRESHOLD or e.meters["running"] < THRESHOLD:
            continue
        sig = ("pant", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["flutter"] += 1
        e.meters["panting"] += 1
        out.append("__pant__")
    return out


CAUSAL_RULES = [Rule("pant", _r_pant)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def toy_is_retained(toy: Toy) -> bool:
    return toy.retainable


def surprise_is_reasonable(s: Surprise) -> bool:
    return s.harmless


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for toy in TOYS.values():
            if not toy_is_retained(toy):
                continue
            for surprise in SURPRISES.values():
                if surprise_is_reasonable(surprise):
                    combos.append((setting, toy.id, surprise.id))
    return combos


def intro(world: World, hero: Entity, librarian: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} came to {world.setting.label}, where the rule was "
        f"{world.setting.quiet_rule}. {world.setting.shelves.capitalize()} made the room look like a tiny museum."
    )
    world.say(
        f"{librarian.label_word.capitalize()} smiled behind the desk and said the toys had to be kept neat and kindly."
    )


def choose_toy(world: World, hero: Entity, toy: Toy) -> None:
    hero.memes["want"] += 1
    world.say(
        f"{hero.id} found {toy.phrase} and decided to {toy.surprise}. "
        f'{hero.id} whispered, "I want to retain this one."'
    )


def surprise_entry(world: World, surprise: Surprise) -> None:
    world.say(
        f"Then, with no warning at all, {surprise.entrance}. "
        f"{surprise.comedy.capitalize()}."
    )


def react(world: World, hero: Entity, surprise: Surprise, toy: Toy) -> None:
    hero.meters["running"] += 1
    hero.meters["dazzled"] += 1
    hero.memes["startled"] += 1
    world.say(
        f"{hero.id} blinked twice, then started to pant like a tiny puppy in a raincoat."
    )
    world.say(
        f'"Pheasant!" {hero.id} gasped, because the surprise had a beak and excellent timing.'
    )
    if toy.noisy:
        world.say(
            f"The {toy.label} nearly rolled off the table, but {hero.id} grabbed it and managed to retain it anyway."
        )
    else:
        world.say(
            f"{hero.id} hugged the {toy.label} so tightly that it did not budge an inch."
        )


def calm_fix(world: World, librarian: Entity, hero: Entity, toy: Toy, surprise: Surprise) -> None:
    librarian.memes["amused"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{librarian.label_word.capitalize()} laughed softly. "
        f'"That is the most serious-looking pheasant I have ever seen," {librarian.pronoun()} said.'
    )
    world.say(
        f"With a gentle scoop and a polite shoo, {librarian.id} guided the pheasant to the door."
    )
    world.say(
        f'Then {librarian.id} tucked the {toy.label} back in its place and said, '
        f'"There. Retained, returned, and still respectable."'
    )
    world.say(
        f"{hero.id} stopped panting, grinned, and looked proud of {hero.pronoun('possessive')} bravery."
    )
    world.say(
        f"The toy library went quiet again, except for one feather that drifted down like applause."
    )


def tell(setting: Setting, toy: Toy, surprise: Surprise,
         hero_name: str = "Mina", hero_gender: str = "girl",
         librarian_name: str = "Rue", librarian_gender: str = "woman") -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="child"))
    librarian = world.add(Entity(librarian_name, kind="character", type=librarian_gender,
                                 role="librarian", label="the librarian"))
    toy_ent = world.add(Entity("toy", type="toy", label=toy.label))
    surprise_ent = world.add(Entity("surprise", type="surprise", label=surprise.label))

    intro(world, hero, librarian)
    world.para()
    choose_toy(world, hero, toy)
    surprise_entry(world, surprise)
    react(world, hero, surprise, toy)
    propagate(world, narrate=True)
    world.para()
    calm_fix(world, librarian, hero, toy, surprise)

    world.facts.update(
        hero=hero, librarian=librarian, toy=toy, toy_ent=toy_ent,
        surprise=surprise, surprise_ent=surprise_ent, setting=setting,
        retained=True, panting=hero.meters["panting"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child set in a toy library that includes the words "{f["surprise"].label}", "retain", and "pant".',
        f"Tell a comedy story where {f['hero'].id} tries to retain a toy in the toy library, then gets surprised by a {f['surprise'].label}.",
        f"Write a light, silly story with a surprise in a toy library and an ending where the child keeps the toy and calms down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    librarian = f["librarian"]
    toy = f["toy"]
    surprise = f["surprise"]
    return [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens in the toy library, where the shelves are full of toys and everyone tries to keep their voices quiet. That setting makes the surprise feel extra funny."
        ),
        QAItem(
            question=f"What was {hero.id} trying to do?",
            answer=f"{hero.id} was trying to retain the {toy.label} and keep it close. Then the surprise made {hero.id} pant and hold on even tighter."
        ),
        QAItem(
            question="What happened when the surprise arrived?",
            answer=f"A pheasant came in with a proud strut and startled everyone. The bird did not hurt anyone, but it made the moment very silly."
        ),
        QAItem(
            question=f"How did {librarian.id} help?",
            answer=f"{librarian.id} laughed, guided the pheasant out, and put the {toy.label} back where it belonged. That calm help turned the surprise into a neat ending."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pheasant?",
            answer="A pheasant is a bird with feathers and a pointed beak. It can walk in a very proud, funny way."
        ),
        QAItem(
            question="What does retain mean?",
            answer="To retain something means to keep it or hold onto it. If you retain a toy, you do not let it slip away."
        ),
        QAItem(
            question="What does pant mean?",
            answer="To pant means to breathe fast, usually after running or getting startled. It can sound a little like a tiny dog after a game."
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise_combo(S, T, U) :- setting(S), toy(T), surprise(U).
retained(T) :- toy(T), retainable(T).
funny(U) :- surprise(U), harmless(U).
outcome(comedy) :- surprise_combo(S, T, U), retained(T), funny(U).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if toy.retainable:
            lines.append(asp.fact("retainable", tid))
    for uid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", uid))
        if s.harmless:
            lines.append(asp.fact("harmless", uid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show surprise_combo/3."))
    return sorted(set(asp.atoms(model, "surprise_combo")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print(" only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy library comedy storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--librarian")
    ap.add_argument("--librarian-gender", choices=["woman", "man"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.toy is None or c[1] == args.toy)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, surprise = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    librarian_gender = args.librarian_gender or rng.choice(["woman", "man"])
    librarian = args.librarian or rng.choice(["Rue", "Tess", "Mara", "June"])
    return StoryParams(setting, toy, surprise, hero, hero_gender, librarian, librarian_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOYS[params.toy], SURPRISES[params.surprise],
                 params.hero, params.hero_gender, params.librarian, params.librarian_gender)
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
    StoryParams("toy_library", "bear", "pheasant", "Mina", "girl", "Rue", "woman"),
    StoryParams("toy_library", "robot", "pheasant", "Theo", "boy", "Tess", "woman"),
    StoryParams("toy_library", "train", "popper", "Lily", "girl", "Mara", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show surprise_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, t, u in combos:
            print(f"  {s:12} {t:8} {u}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
