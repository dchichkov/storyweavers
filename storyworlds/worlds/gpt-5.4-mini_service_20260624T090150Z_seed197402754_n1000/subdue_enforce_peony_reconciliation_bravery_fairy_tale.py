#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a brave child, a stubborn peony, and a
gentle reconciliation.

Seed tale:
---
Once, in a castle garden, a little child found a proud peony glowing beside a
stone path. The child wanted to take the flower home, but the garden keeper
said the peony must stay rooted and the rule must be enforced. A hummingbird
guided the child to be brave, subdue the urge to grab, and ask the peony what
it needed. The peony was lonely because the other flowers would not share the
sunlight. The child helped trim the vines, made room for the peony, and the
garden became peaceful again.

World idea:
---
- Physical meters: brightness, crowding, tidiness, stem_strength, path_blocked
- Emotional memes: desire, worry, bravery, anger, reconciliation, relief
- The story turns when bravery changes the method from taking to helping.

This file is self-contained except for the shared result containers.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryKnob:
    id: str
    verb: str
    danger: str
    urge: str
    mess: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    challenge: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


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
        return clone


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mm(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_m(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = _m(ent, key) + amt


def _inc_mm(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = _mm(ent, key) + amt


def _set_m(ent: Entity, key: str, val: float) -> None:
    ent.meters[key] = val


SETTINGS = {
    "castle_garden": Setting("the castle garden", indoors=False, tags={"garden", "flower", "fairy"}),
    "rose_arch": Setting("the rose arch", indoors=False, tags={"garden", "flower", "fairy"}),
    "sunny_courtyard": Setting("the sunny courtyard", indoors=False, tags={"garden", "flower", "fairy"}),
}

CHALLENGES = {
    "peony": StoryKnob(
        id="peony",
        verb="take the peony home",
        danger="pluck it from the root",
        urge="reach for the flower",
        mess="crowded and tangled",
        zone="path",
        tags={"peony", "flower", "fairy"},
    ),
    "vines": StoryKnob(
        id="vines",
        verb="clear the vines",
        danger="let the path stay blocked",
        urge="push through the vines",
        mess="tangled",
        zone="path",
        tags={"garden", "bravery"},
    ),
    "thornbush": StoryKnob(
        id="thornbush",
        verb="cross the thornbush",
        danger="get scratched",
        urge="rush through",
        mess="scratched",
        zone="hands",
        tags={"garden", "bravery"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Ruby", "Nora", "Elia", "Wren"]
BOY_NAMES = ["Rowan", "Eli", "Tobin", "Finn", "Perry", "Bram"]
TRAITS = ["gentle", "curious", "brave", "kind", "patient", "cheerful"]
GUARDIANS = ["queen", "king", "gardener", "grandmother"]

KNOWLEDGE = {
    "peony": [
        ("What is a peony?", "A peony is a big, soft flower with many petals that can bloom in a garden."),
    ],
    "flower": [
        ("Why do flowers need sunlight?", "Flowers need sunlight to help them grow strong and open their petals."),
    ],
    "fairy": [
        ("What is a fairy tale?", "A fairy tale is a make-believe story that often has castles, magic, and a happy ending."),
    ],
    "bravery": [
        ("What is bravery?", "Bravery means doing the right thing even when you feel scared or unsure."),
    ],
    "reconciliation": [
        ("What is reconciliation?", "Reconciliation means making peace again after a disagreement."),
    ],
    "garden": [
        ("What is a garden?", "A garden is a place where people grow flowers, plants, and sometimes vegetables."),
    ],
    "root": [
        ("Why do flowers need roots?", "Roots hold a plant in the soil and help it drink water."),
    ],
}

KNOWLEDGE_ORDER = ["peony", "flower", "garden", "fairy", "bravery", "reconciliation", "root"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for c_name, challenge in CHALLENGES.items():
            if "fairy" in setting.tags and "flower" in challenge.tags:
                combos.append((s_name, c_name))
    return combos


def explain_rejection(setting: str, challenge: str) -> str:
    return f"(No story: the setting {setting} and challenge {challenge} do not make a fairytale fit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about peonies, bravery, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("(No valid fairy-tale combination matches the given options.)")
    setting, challenge = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, name=name, gender=gender, guardian=guardian, trait=trait)


def _subdue_phrase(challenge: StoryKnob) -> str:
    if challenge.id == "peony":
        return "subdue the urge to pull the peony"
    if challenge.id == "vines":
        return "subdue the vines by tying them back gently"
    return "subdue the fear and step carefully"


def _enforce_phrase(challenge: StoryKnob) -> str:
    if challenge.id == "peony":
        return "enforce the garden rule by leaving the peony where it grew"
    if challenge.id == "vines":
        return "enforce the rule that the path must stay open"
    return "enforce the rule by moving slowly and safely"


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian, label=params.guardian))
    challenge = CHALLENGES[params.challenge]
    setting = world.setting

    hero.memes = {"desire": 1.0, "worry": 0.0, "bravery": 0.0, "reconciliation": 0.0, "relief": 0.0, "anger": 0.0}
    guardian.memes = {"care": 1.0}

    if challenge.id == "peony":
        flower = world.add(Entity(
            id="Peony",
            kind="thing",
            type="flower",
            label="peony",
            phrase="a bright peony",
            owner=None,
            caretaker=guardian.id,
            meters={"brightness": 2.0, "stem_strength": 1.0, "crowding": 2.0},
            memes={"quiet": 1.0},
        ))
    else:
        flower = world.add(Entity(
            id="Peony",
            kind="thing",
            type="flower",
            label="peony",
            phrase="a bright peony",
            caretaker=guardian.id,
            meters={"brightness": 2.0, "stem_strength": 1.0, "crowding": 1.0},
            memes={"quiet": 1.0},
        ))

    world.say(f"Once upon a time, in {setting.place}, there lived a {params.trait} {params.gender} named {params.name}.")
    world.say(f"{params.name} loved the peony because its petals looked like pink silk in the sun.")
    world.para()

    world.say(f"One morning, {params.name} found {flower.phrase} near the stone path.")
    world.say(f"The peony seemed to ask for help, because the place felt {challenge.mess}.")
    _inc_mm(hero, "desire", 1.0)
    _inc_mm(hero, "worry", 1.0)
    _inc_m(flower, "crowding", 1.0)
    world.say(f"{params.name} wanted to {challenge.verb}, but {params.guardian} raised a hand and spoke softly.")
    world.say(f'"We must {_enforce_phrase(challenge)}," said the {params.guardian}, "and not {_subdue_phrase(challenge)} the wrong way."')
    world.para()

    _inc_mm(hero, "bravery", 1.0)
    world.say(f"{params.name} took a brave breath and chose to listen.")
    world.say(f"With bravery, {params.name} tried to {_subdue_phrase(challenge)} instead of forcing anything.")
    _inc_m(flower, "crowding", -1.0)
    _inc_m(flower, "brightness", 1.0)
    _inc_mm(hero, "anger", -0.5)
    _inc_mm(hero, "reconciliation", 1.0)
    world.say(f"{params.name} spoke kindly to the peony and gently moved the tangled stems away from the light.")
    world.say(f"The peony stood taller, and the path grew open again.")
    world.say(f"Then {params.name} and the {params.guardian} smiled together, because that was how the rule could be kept and the flower could still be safe.")
    world.para()

    _inc_mm(hero, "relief", 1.0)
    _set_m(flower, "crowding", 0.0)
    _set_m(flower, "stem_strength", 2.0)
    world.say(f"In the end, {params.name} did not take the peony home.")
    world.say(f"Instead, {params.name} left it in the garden, where it could keep blooming in the sunlight, and the garden felt peaceful again.")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        flower=flower,
        setting=params.setting,
        challenge=challenge,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short fairy tale for a young child about {p.name}, a peony, and a lesson in bravery.',
        f"Tell a gentle story where {p.name} wants to {f['challenge'].verb} but learns reconciliation instead.",
        f'Write a castle-garden story that uses the words "subdue" and "enforce" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    guardian = f["guardian"]
    challenge = f["challenge"]
    flower = f["flower"]
    return [
        QAItem(
            question=f"What did {p.name} want to do with the peony at first?",
            answer=f"At first, {p.name} wanted to {challenge.verb}.",
        ),
        QAItem(
            question=f"Who reminded {p.name} about the rule in {world.setting.place}?",
            answer=f"The {p.guardian} reminded {p.name} that they must enforce the garden rule and keep the peony safe.",
        ),
        QAItem(
            question=f"How did {p.name} show bravery?",
            answer=f"{p.name} showed bravery by listening, calming down, and choosing to subdue the urge to grab the flower.",
        ),
        QAItem(
            question=f"What changed after reconciliation?",
            answer=f"After reconciliation, the peony had more room and sunlight, and {p.name} and the {p.guardian} felt peaceful again.",
        ),
        QAItem(
            question=f"Did {p.name} take the peony home?",
            answer=f"No, {p.name} did not take the peony home. The peony stayed in the garden and kept blooming there.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    tags.add("bravery")
    tags.add("reconciliation")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_name(S).
challenge(C) :- challenge_name(C).

fairy_fit(S,C) :- setting(S), challenge(C), fairy_place(S), flower_challenge(C).
valid_story(S,C) :- fairy_fit(S,C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
        lines.append(asp.fact("fairy_place", s))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge_name", c))
        lines.append(asp.fact("flower_challenge", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(World(SETTINGS[params.setting]), params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, challenge) combos:\n")
        for s, c in combos:
            print(f"  {s:16} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s, c in valid_combos():
            p = StoryParams(setting=s, challenge=c, name="Lina", gender="girl", guardian="queen", trait="brave")
            p.seed = base_seed
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
