#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reptile_booboo_palm_twist_whodunit.py
======================================================================

A standalone story world in a tiny whodunit mode: a child notices a strange
track near a palm, worries about a reptile, follows clues, and learns a gentle
twist at the end.

This world keeps the contract:
- stdlib only
- imports shared results eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- has a Python reasonableness gate and an inline ASP twin
- uses simulated meters and memes to drive the prose and Q&A
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Clue:
    id: str
    label: str
    kind: str
    gives: str
    hidden: bool = False
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
class Twist:
    id: str
    reveal: str
    method: str
    cause: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

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


def _r_boo(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    clue = world.entities.get("clue")
    if not kid or not clue:
        return out
    if kid.memes["worry"] >= THRESHOLD and clue.meters["noticed"] >= THRESHOLD:
        sig = ("boo",)
        if sig not in world.fired:
            world.fired.add(sig)
            kid.memes["fear"] += 1
            out.append("__boo__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    reptile = world.entities.get("reptile")
    if not reptile:
        return out
    if reptile.meters["revealed"] >= THRESHOLD:
        sig = ("twist",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("boo", "social", _r_boo), Rule("twist", "plot", _r_twist)]


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


def reasonableness_ok(params: "StoryParams") -> bool:
    return params.place in PLACES and params.clue in CLUES and params.twist in TWISTS


def _mystery_opening(world: World, kid: Entity, adult: Entity, place: str) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"On a warm afternoon, {kid.id} and {adult.id} went to the {place}. "
        f"{kid.id} had a bright eye for tiny odd things."
    )


def _find_sign(world: World, kid: Entity, clue: Clue, reptile: Entity) -> None:
    clue_ent = world.add(Entity(id="clue", kind="thing", type=clue.kind, label=clue.label))
    clue_ent.meters["noticed"] += 1
    kid.memes["worry"] += 1
    world.say(
        f"Near the palm, {kid.id} found a strange sign: {clue.gives}. "
        f"It looked like trouble, and the word {clue.label} felt important."
    )
    world.say(
        f"{kid.id} peered closer and whispered, \"Is that a reptile track?\""
    )
    world.facts["clue_ent"] = clue_ent
    world.facts["reptile"] = reptile


def _ask_about_boboo(world: World, kid: Entity, adult: Entity, clue: Clue) -> None:
    world.say(
        f"{adult.id} knelt beside {kid.id}. \"Show me your booboo,\" {adult.pronoun()} said."
    )
    world.say(
        f"{kid.id} held up a little palm-shaped bandage with a grin. "
        f"It was only a booboo from a branch, not a bite."
    )


def _spot_reptile(world: World, reptile: Entity) -> None:
    reptile.meters["revealed"] += 1
    reptile.memes["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the mystery turned. A small reptile slid from behind the palm, "
        f"not sneaky at all, but carrying a curled leaf in its mouth."
    )


def _twist_reveal(world: World, reptile: Entity, twist: Twist, kid: Entity) -> None:
    world.say(
        f"The reptile was not the problem. {twist.reveal} {twist.method}, "
        f"and the whole puzzle clicked into place."
    )
    kid.memes["fear"] = 0.0
    kid.memes["relief"] += 1


def _solve(world: World, kid: Entity, adult: Entity, reptile: Entity, twist: Twist) -> None:
    world.say(
        f"{adult.id} laughed softly. \"It was a helper reptile,\" {adult.pronoun()} said. "
        f"\"It used {twist.cause} to show us where the lost shell had rolled.\""
    )
    world.say(
        f"{kid.id} looked at the palm, then at the smiling reptile, and waved. "
        f"The tiny detective story ended with everyone safe and the clue solved."
    )


def tell(place: str, clue: Clue, twist: Twist, kid_name: str = "Mina",
         kid_gender: str = "girl", adult_name: str = "Dad",
         adult_gender: str = "man") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="detective"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="helper"))
    reptile = world.add(Entity(id="reptile", kind="character", type="reptile", label="reptile"))
    palm = world.add(Entity(id="palm", kind="thing", type="palm", label="palm tree"))

    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["twist"] = twist
    world.facts["kid"] = kid
    world.facts["adult"] = adult
    world.facts["palm"] = palm

    _mystery_opening(world, kid, adult, place)
    world.para()
    _find_sign(world, kid, clue, reptile)
    _ask_about_boboo(world, kid, adult, clue)
    world.para()
    _spot_reptile(world, reptile)
    _twist_reveal(world, reptile, twist, kid)
    _solve(world, kid, adult, reptile, twist)

    world.facts["outcome"] = "solved"
    return world


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    twist: str
    kid: str
    kid_gender: str
    adult: str
    adult_gender: str
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


PLACES = {
    "garden": "garden",
    "yard": "backyard",
    "beach": "beach",
    "park": "park",
}

CLUES = {
    "track": Clue("track", "tiny tracks", "track", "a trail of little prints", tags={"track", "reptile"}),
    "scale": Clue("scale", "shiny scale", "scale", "one green scale on the path", tags={"scale", "reptile"}),
    "leaf": Clue("leaf", "curled leaf", "leaf", "a curled leaf stuck to the sand", tags={"leaf", "palm"}),
}

TWISTS = {
    "helper": Twist("helper", "The reptile was helping", "it had nudged the clue along", "a breeze from the palm", tags={"twist"}),
    "shell": Twist("shell", "The missing shell had been hiding there all along", "it had fallen beside the roots", "the shade under the palm", tags={"twist", "palm"}),
    "toy": Twist("toy", "It was only a toy reptile after all", "someone had dropped a wind-up toy", "a pocket in the sandbag", tags={"twist"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Owen", "Max"]
ADULT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, t) for p in PLACES for c in CLUES for t in TWISTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit story world with a reptile twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["man", "woman", "mother", "father"])
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
              and (args.clue is None or c[1] == args.clue)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, twist = rng.choice(sorted(combos))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    kid = args.kid or rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(place, clue, twist, kid, kid_gender, adult, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the words "reptile", "booboo", and "palm".',
        f"Tell a mystery story where {f['kid'].id} follows a clue near a palm and thinks a reptile is involved, but the ending has a twist.",
        f'Write a short detective story for a young child with a clue, a palm, and a gentle twist reveal.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    adult = f["adult"]
    clue = f["clue"]
    twist = f["twist"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id}, who went looking for clues with {adult.id}. The story is a small mystery with a gentle ending."),
        ("What did {kid} think the clue meant?".replace("{kid}", kid.id),
         f"{kid.id} thought the clue might belong to a reptile. That guess made the mystery feel bigger until the twist was revealed."),
        ("What was the booboo?",
         f"The booboo was only a little scratch from a branch, not a reptile bite. That matters because the clue looked scarier than it really was."),
        ("What was the twist?",
         f"{twist.reveal}. {twist.method.capitalize()}, so the final answer was kinder than the first guess."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a reptile?",
         "A reptile is a cold-blooded animal such as a lizard, snake, or turtle. Many reptiles have scales."),
        ("What is a palm?",
         "A palm can mean a palm tree with big fronds, or the inside of your hand. In this story it is a palm tree."),
        ("What is a booboo?",
         "A booboo is a small hurt, like a little scrape or bump. Grown-ups often clean it and put on a bandage."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, T) :- place(P), clue(C), twist(T).
mystery(C) :- clue(C).
revealed(T) :- twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid_combos()")
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story:
        print("MISMATCH: generation failed")
        return 1
    print(f"OK: ASP parity and generation smoke test passed ({len(py)} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], TWISTS[params.twist],
                 params.kid, params.kid_gender, params.adult, params.adult_gender)
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


CURATED = [
    StoryParams("garden", "track", "helper", "Mina", "girl", "Dad", "man"),
    StoryParams("beach", "leaf", "shell", "Theo", "boy", "Mom", "woman"),
    StoryParams("yard", "scale", "toy", "Lily", "girl", "Aunt June", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
