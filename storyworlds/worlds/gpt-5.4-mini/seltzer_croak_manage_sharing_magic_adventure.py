#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/seltzer_croak_manage_sharing_magic_adventure.py
===============================================================================

A small adventure storyworld about sharing a fizzy seltzer in a magic pond quest.

Premise:
- Two children go on a little adventure.
- One has a magic bottle of seltzer that makes a croaking frog statue wake up.
- They must manage the fizz, share the drink, and follow the croak to find a prize.
- The story turns on sharing and magic, with a child-facing, concrete ending image.

The world is deliberately tiny: one shared drink, one croaking guide, a path,
and a treasure that can only be reached when the children cooperate.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

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
class Drink:
    id: str
    label: str
    phrase: str
    fizz: int
    shares: int = 2
    tags: set[str] = field(default_factory=set)

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
class Guide:
    id: str
    label: str
    croak_line: str
    hint_line: str
    tags: set[str] = field(default_factory=set)

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
class Treasure:
    id: str
    label: str
    phrase: str
    locked: bool = True
    tags: set[str] = field(default_factory=set)

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
class World:
    setting: Setting
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
        clone = World(self.setting)
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
    tag: str
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


def _r_fizz(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["fizz"] < THRESHOLD:
            continue
        sig = ("fizz", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("drink").meters["shared_fizz"] += 1
        out.append("__fizz__")
    return out


def _r_bridge(world: World) -> list[str]:
    out: list[str] = []
    if world.get("drink").meters["shared_fizz"] < THRESHOLD:
        return out
    sig = ("bridge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("path").meters["open"] += 1
    out.append("The croak turned into a clear trail.")
    return out


def _r_together(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("A")
    b = world.get("B")
    if a.memes["share"] < THRESHOLD or b.memes["share"] < THRESHOLD:
        return out
    sig = ("together",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    out.append("They felt braver together.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("fizz", "physical", _r_fizz),
    Rule("bridge", "physical", _r_bridge),
    Rule("together", "social", _r_together),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def manage_ok(drink: Drink, amount: int) -> bool:
    return amount <= drink.fizz


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for did in DRINKS:
            for gid in GUIDES:
                if manage_ok(DRINKS[did], 1):
                    combos.append((sid, did, gid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    drink: str
    guide: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
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
    "pond": Setting(
        "pond",
        scene="a moonlit pond garden",
        place_line="The stone path curved around a tiny pond, and lily pads shone like green coins.",
        ending_image="the pond glimmering under a path of little footprints",
        tags={"adventure"},
    ),
    "garden": Setting(
        "garden",
        scene="a secret garden",
        place_line="Tall flowers leaned over the path, and a narrow gate waited at the end.",
        ending_image="the gate standing open beside bright flowers",
        tags={"adventure"},
    ),
}

DRINKS = {
    "seltzer": Drink("seltzer", "seltzer", "a bottle of seltzer", fizz=2, tags={"seltzer", "sharing"}),
}

GUIDES = {
    "frog": Guide(
        "frog",
        "frog",
        "Croak! croak!",
        "The frog pointed its nose toward the hidden path.",
        tags={"croak", "magic", "adventure"},
    ),
    "statue": Guide(
        "statue",
        "frog statue",
        "Croaaak!",
        "The statue woke and blinked once, as if it knew a secret.",
        tags={"croak", "magic", "adventure"},
    ),
}

TREASURE = Treasure("shell", "silver shell", "a silver shell", locked=True, tags={"magic", "adventure"})

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Finn", "Sam"]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    a = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="hero"))
    b = world.add(Entity(params.friend, kind="character", type=params.friend_gender, role="friend"))
    parent = world.add(Entity(params.parent, kind="character", type="mother" if params.parent == "Mom" else "father", role="parent", label="the parent"))
    drink = world.add(Entity("drink", label=DRINKS[params.drink].label))
    guide = world.add(Entity("guide", label=GUIDES[params.guide].label))
    path = world.add(Entity("path", label="the path"))
    treasure = world.add(Entity("treasure", label=TREASURE.label))
    world.facts.update(a=a, b=b, parent=parent, drink=drink, guide=guide, path=path, treasure=treasure)
    return world


def story(world: World, params: StoryParams) -> None:
    a = world.facts["a"]
    b = world.facts["b"]
    parent = world.facts["parent"]
    drink = world.facts["drink"]
    guide = world.facts["guide"]
    treasure = world.facts["treasure"]

    a.memes["curious"] += 1
    b.memes["curious"] += 1
    world.say(f"On a quiet afternoon, {a.id} and {b.id} explored {world.setting.scene}.")
    world.say(world.setting.place_line)
    world.say(f"{a.id} carried {drink.phrase}, because the bottle had a magic sparkle and the water inside looked like seltzer stars.")

    world.para()
    world.say(f"Then {guide.label} jumped onto a flat stone.")
    world.say(f'{guide.croak_line} {guide.hint_line}')
    world.say(f'{b.id} grinned. "Did you hear that? Maybe the croak is trying to help us!"')

    world.para()
    a.memes["share"] += 1
    b.memes["share"] += 1
    drink.meters["fizz"] += 1
    world.say(f'{a.id} nodded and shared the seltzer with {b.id}. Each child took a careful sip and managed the fizz so it would not splash over the rim.')
    propagate(world)

    world.para()
    if world.get("path").meters["open"] >= THRESHOLD:
        world.say(f"The croak pointed them past ferns and stones until they found {treasure.phrase} tucked beside the roots.")
        treasure.locked = False
        a.memes["joy"] += 1
        b.memes["joy"] += 1
        world.say(f"{parent.id} smiled when they returned, and the two children held up the silver shell like a bright moon in their hands.")
    else:
        world.say(f"The magic stayed quiet, so {a.id} and {b.id} sat together and listened harder until the next croak showed them the way.")
        world.say(f"In the end, they still found {treasure.phrase}, because they kept calm and managed the moment together.")

    world.say(f"The adventure ended with {world.setting.ending_image}.")


def generation_prompts(world: World) -> list[str]:
    return [
        'Write an adventure story for a young child that includes the words "seltzer", "croak", and "manage".',
        f"Tell a story where {world.facts['a'].id} and {world.facts['b'].id} share something fizzy, hear a croak, and manage a magical path together.",
        "Write a gentle magic adventure about sharing a drink, following a croaking guide, and finding a treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["a"]
    b = world.facts["b"]
    parent = world.facts["parent"]
    guide = world.facts["guide"]
    drink = world.facts["drink"]
    return [
        ("Who went on the adventure?", f"{a.id} and {b.id} went on the adventure together, and {parent.id} watched them come back happy."),
        ("What did they share?", f"They shared seltzer. They managed the fizz carefully so the bottle would not spill while they explored."),
        ("Why did the croak matter?", f"The croak was magic. It helped point them toward the hidden path and the treasure at the end."),
        ("How did they manage the tricky part?", f"They stayed calm, shared the seltzer, and listened to the croak. That made the path open and kept the adventure friendly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is seltzer?", "Seltzer is fizzy water with tiny bubbles in it. It can pop and fizz like a playful drink."),
        ("What does croak mean?", "Croak is the sound a frog makes. It is a low little hop of a sound."),
        ("What does manage mean?", "Manage means to handle something well or keep it under control. If you manage a problem, you make it easier."),
        ("What is sharing?", "Sharing means letting someone else have some of what you have. It is a kind way to play together."),
        ("What is magic in a story?", "Magic is something wonderful that can happen in an impossible way. In stories, magic often helps characters on an adventure."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared_fizz(D) :- drink(D), fizz(D, F), F >= 1.
path_open(P) :- shared_fizz(D), path(P).
together(A, B) :- share(A), share(B).
outcome(ok) :- path_open(_), together(_, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("scene", sid))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("fizz", did, d.fizz))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    lines.append(asp.fact("share", "a"))
    lines.append(asp.fact("share", "b"))
    lines.append(asp.fact("path", "path"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    got = set(asp.atoms(model, "outcome"))
    want = {("ok",)}
    if got != want:
        print("MISMATCH in ASP outcome:", got, want)
        return 1
    print("OK: ASP twin matches the Python gate.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: seltzer, croak, manage, sharing, magic, adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad"])
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
    if args.hero and args.friend and args.hero == args.friend:
        raise StoryError("The two children need different names.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    drink = args.drink or "seltzer"
    guide = args.guide or rng.choice(sorted(GUIDES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice([n for n in hero_pool])
    friend_choices = [n for n in friend_pool if n != hero]
    friend = args.friend or rng.choice(friend_choices)
    parent = args.parent or rng.choice(["Mom", "Dad"])
    if setting not in SETTINGS or drink not in DRINKS or guide not in GUIDES:
        raise StoryError("No valid combination matches the given options.")
    return StoryParams(setting, drink, guide, hero, hero_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible combo: setting + seltzer + croak + sharing + magic\n")
        for sid in valid_combos():
            print("  ", sid)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("pond", "seltzer", "frog", "Lily", "girl", "Tom", "boy", "Mom"),
            StoryParams("garden", "seltzer", "statue", "Max", "boy", "Maya", "girl", "Dad"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero} and {p.friend}: {p.setting} / {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
