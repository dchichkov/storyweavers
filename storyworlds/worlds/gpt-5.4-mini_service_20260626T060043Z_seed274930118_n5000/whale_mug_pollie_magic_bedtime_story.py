#!/usr/bin/env python3
"""
storyworlds/worlds/whale_mug_pollie_magic_bedtime_story.py
===========================================================

A small bedtime-story world about a sleepy whale, a treasured mug, and a little
helper named Pollie.

Premise:
A childlike whale loves a warm bedtime sip from a favorite mug. Pollie helps
with the bedtime routine, but a bit of magic makes the mug disappear and drift
into an unexpected place.

Turn:
The whale and Pollie look for the mug by moonlight and discover that the magic
did not steal it; it transformed the worry into a gentle clue.

Resolution:
With Pollie's help, the mug is found, the magic is used kindly, and the whale
falls asleep feeling safe, cozy, and loved.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "whale": {"subject": "it", "object": "it", "possessive": "its"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, mapping["whale"])[case]


@dataclass
class Setting:
    place: str = "the moonlit harbor"
    indoors: bool = False
    calm: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_magic_shift(world: World) -> list[str]:
    out = []
    whale = world.get("whale")
    mug = world.get("mug")
    if whale.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("shift",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mug.location = "under the pillow"
    mug.meters["lost"] = 1.0
    out.append("The magic made the little mug drift softly under the pillow.")
    return out


def _r_find_mug(world: World) -> list[str]:
    out = []
    mug = world.get("mug")
    pollie = world.get("pollie")
    whale = world.get("whale")
    if mug.location != "under the pillow":
        return out
    sig = ("found",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mug.location = "in the whale's fins"
    whale.memes["relief"] = whale.memes.get("relief", 0.0) + 1
    pollie.memes["pride"] = pollie.memes.get("pride", 0.0) + 1
    out.append("Pollie peeked under the pillow and found the mug waiting there, warm and safe.")
    return out


def _r_sleep(world: World) -> list[str]:
    out = []
    whale = world.get("whale")
    mug = world.get("mug")
    sig = ("sleep",)
    if sig in world.fired:
        return out
    if whale.memes.get("relief", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    whale.memes["sleepy"] = 1.0
    out.append("With the mug back in place, the whale yawned and drifted into a cozy sleep.")
    return out


CAUSAL_RULES = [
    Rule("magic_shift", _r_magic_shift),
    Rule("find_mug", _r_find_mug),
    Rule("sleep", _r_sleep),
]


def propagate(world: World) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


SETTINGS = {
    "harbor": Setting(place="the moonlit harbor", indoors=False, calm=True),
    "bedroom": Setting(place="the little bedroom", indoors=True, calm=True),
    "seashell_cove": Setting(place="the seashell cove", indoors=False, calm=True),
}

TRAITS = ["gentle", "curious", "sleepy", "brave", "soft-spoken"]

GIRL_NAMES = ["Mira", "Luna", "Nina", "Ivy", "Poppy", "Elsa"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Eli", "Noah", "Toby"]


ASP_RULES = r"""
worry(whale) :- needs_bedtime(whale).
magic_shift(mug) :- worry(whale).
found(mug) :- magic_shift(mug).
sleep(whale) :- found(mug).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("needs_bedtime", "whale"),
        asp.fact("has_helper", "pollie"),
        asp.fact("treasured", "mug"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sleep/1."))
    clingo_set = set(asp.atoms(model, "sleep"))
    python_set = {("whale",)} if True else set()
    if clingo_set == python_set:
        print("OK: clingo gate matches Python gate (sleep/1).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a whale, a mug, Pollie, and a little magic."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, trait=trait)


def generate_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    whale = world.add(Entity(
        id="whale", kind="character", type="whale", label="whale",
        traits=["little", params.trait], location=world.setting.place,
        memes={"love_mug": 1.0},
    ))
    pollie = world.add(Entity(
        id="pollie", kind="character", type=params.gender, label="Pollie",
        traits=["gentle", "helpful"], location=world.setting.place,
    ))
    mug = world.add(Entity(
        id="mug", kind="thing", type="mug", label="mug",
        phrase="a tiny blue mug with a star on it", owner="whale",
        caretaker="pollie", location="on the bedside table",
        meters={"warm": 1.0},
    ))
    world.facts.update(whale=whale, pollie=pollie, mug=mug, params=params)
    return world


def tell(world: World) -> World:
    whale = world.get("whale")
    pollie = world.get("pollie")
    mug = world.get("mug")
    p = world.facts["params"]

    world.say(
        f"Under the quiet moon, a little whale named {p.name} lived by {world.setting.place}."
    )
    world.say(
        f"{whale.pronoun().capitalize()} loved the bedtime mug most of all, because it held a warm sip that made the night feel safe."
    )
    world.say(
        f"Pollie, who was {p.trait}, always helped with the blankets, the lullaby, and the last tiny drink."
    )

    world.para()
    whale.memes["worry"] = 1.0
    world.say(
        f"But tonight, the mug was missing from the bedside table, and {p.name} felt a little wobble in {whale.pronoun('possessive')} heart."
    )
    world.say(
        f"Pollie whispered, 'Let's look gently. Magic sometimes hides things so we can find them in a kinder way.'"
    )
    propagate(world)

    world.para()
    world.say(
        f"Pollie lifted the pillow, and there was the mug, tucked away as neat as a shell in sand."
    )
    world.say(
        f"{p.name} held {whale.pronoun('possessive')} mug with care, and the warm cup shone like a small, friendly moon."
    )
    world.say(
        f"Then the whale smiled, the worry melted away, and the room became quiet enough for dreams."
    )
    propagate(world)
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    whale = world.get("whale")
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about a little whale named {p.name} and the helpful Pollie by {world.setting.place}.",
        ),
        QAItem(
            question="What did the whale love most at bedtime?",
            answer="The whale loved the warm little mug, because it made the night feel safe and cozy.",
        ),
        QAItem(
            question="Where did Pollie find the mug?",
            answer="Pollie found the mug tucked under the pillow, where the magic had gently hidden it.",
        ),
        QAItem(
            question="How did the whale feel at the end?",
            answer=f"At the end, {p.name} felt relieved and sleepy, and {whale.pronoun('subject')} drifted off happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in a bedtime story?",
            answer="Magic is a special make-believe kind of power that can change or hide things in gentle, surprising ways.",
        ),
        QAItem(
            question="Why do children like a warm mug at bedtime?",
            answer="A warm mug can feel cozy and calming, which helps the body and mind get ready for sleep.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle bedtime story about a whale named {p.name}, a mug, and Pollie, with a touch of magic.",
        f"Tell a soothing story where {p.name} the whale loses a mug at bedtime and Pollie helps find it.",
        "Write a short, moonlit bedtime story where magic hides a mug and a kind helper brings calm.",
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
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="harbor", name="Mira", gender="girl", trait="gentle"),
    StoryParams(place="bedroom", name="Theo", gender="boy", trait="sleepy"),
    StoryParams(place="seashell_cove", name="Luna", gender="girl", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show sleep/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show sleep/1."))
        print("sleep facts:", sorted(set(asp.atoms(model, "sleep"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
