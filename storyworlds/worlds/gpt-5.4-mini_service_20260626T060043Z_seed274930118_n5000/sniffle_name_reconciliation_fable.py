#!/usr/bin/env python3
"""
A small fable world about a hurt feeling, a misplaced name, and reconciliation.

Seed tale:
---
In a little forest school, a tiny mouse kept sniffing because other animals
had started calling him by the wrong name. He felt small and lonely, so he
stopped joining the games. An old turtle asked why he was quiet. The mouse
sniffled, told the truth, and showed the turtle the name tag sewn inside his
coat.

The turtle listened carefully, then helped him tell the others the correct name.
The forest children apologized, repeated his name with kindness, and asked him
to join their circle again. The mouse stopped sniffing, lifted his head, and
smiled. From then on, the little forest remembered that a true friend listens
before naming, and reconciliation begins with a gentle apology.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "mouse": {"subject": "he", "object": "him", "possessive": "his"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "turtle": {"subject": "she", "object": "her", "possessive": "her"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Setting:
    place: str
    season: str
    afford: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    name: str
    mistaken_name: str
    helper: str
    season: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes.get("hurt", 0.0) < THRESHOLD or hero.memes.get("heard_apology", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hurt"] = 0.0
    hero.memes["warmth"] = hero.memes.get("warmth", 0.0) + 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    out.append("The small hurt softened when kind words were spoken.")
    return out


CAUSAL_RULES = [Rule("reconcile", _r_reconcile)]


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


def predict_healing(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.entities["hero"]
    return hero.memes.get("hurt", 0.0) < THRESHOLD


SETTINGS = {
    "schoolyard": Setting(place="the forest schoolyard", season="autumn", afford={"play", "listen"}),
    "grove": Setting(place="the quiet grove", season="spring", afford={"play", "listen"}),
    "clearing": Setting(place="the moonlit clearing", season="summer", afford={"play", "listen"}),
}

HEROES = {
    "mouse": {"type": "mouse", "label": "mouse", "traits": ["little", "gentle"]},
    "rabbit": {"type": "rabbit", "label": "rabbit", "traits": ["small", "quick"]},
    "boy": {"type": "boy", "label": "boy", "traits": ["little", "thoughtful"]},
}

HELPERS = {
    "turtle": {"type": "turtle", "label": "turtle", "traits": ["old", "patient"]},
    "fox": {"type": "fox", "label": "fox", "traits": ["calm", "wise"]},
}

NAMES = {
    "mouse": ["Milo", "Pip", "Nico", "Toby", "Finn"],
    "rabbit": ["Luna", "Mina", "Tessa", "Nell", "Ruby"],
    "boy": ["Ari", "Ben", "Owen", "Theo", "Eli"],
}

MISTAKEN_NAMES = ["Milo", "Mina", "Pip", "Ruby", "Toby", "Nell"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for hero in HEROES:
            for helper in HELPERS:
                combos.append((place, hero, helper))
    return combos


def setting_detail(setting: Setting) -> str:
    if setting.place == "the forest schoolyard":
        return "The children had gathered beneath the oak trees, where leaves made a soft brown carpet."
    if setting.place == "the quiet grove":
        return "The grove was still, and the ferns leaned in as if they were listening."
    return "The clearing held silver light, and the fireflies blinked like tiny lanterns."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.label)
    world.say(f"{hero.id} was a little {trait} {hero.label} who loved the sound of leaves underfoot.")


def sniffle(world: World, hero: Entity, mistaken_name: str) -> None:
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    hero.memes["lonely"] = hero.memes.get("lonely", 0.0) + 1
    world.say(
        f"But the others kept calling {hero.pronoun('object')} {mistaken_name} instead of {hero.id}, "
        f"and soon {hero.id} began to sniffle."
    )
    world.say(f"{hero.pronoun().capitalize()} stood still and stopped joining the games.")


def ask_why(world: World, helper: Entity, hero: Entity) -> None:
    world.say(
        f"The wise {helper.label} noticed the quiet and asked why {hero.id} had gone so still."
    )


def truth_told(world: World, hero: Entity, helper: Entity, mistaken_name: str) -> None:
    hero.memes["heard_apology"] = hero.memes.get("heard_apology", 0.0) + 1
    world.say(
        f"{hero.id} sniffled and said, \"That is not my name. My name is {hero.id}.\" "
        f"Then {hero.pronoun().capitalize()} showed {helper.pronoun('object')} the name tag sewn inside {hero.pronoun('possessive')} coat."
    )


def apology(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    world.say(
        f"The {helper.label} listened carefully and helped the others say {hero.id}'s name the right way."
    )
    world.say(
        f"The forest children apologized, and their voices became soft and proper, like careful footsteps."
    )


def ending(world: World, hero: Entity, helper: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} stopped sniffing, lifted {hero.pronoun('possessive')} head, and smiled."
    )
    world.say(
        f"Before long, {hero.id} was back in the circle, and the {helper.label} sat nearby, pleased that the small hurt had been reconciled."
    )


def tell(setting: Setting, hero_kind: str, helper_kind: str, name: str, mistaken_name: str) -> World:
    world = World(setting)
    hero_cfg = HEROES[hero_kind]
    helper_cfg = HELPERS[helper_kind]
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        traits=hero_cfg["traits"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg["type"],
        label=helper_cfg["label"],
        traits=helper_cfg["traits"],
    ))
    world.facts["hero_name"] = name
    world.facts["mistaken_name"] = mistaken_name
    world.facts["helper_kind"] = helper_kind
    world.facts["setting"] = setting

    introduce(world, hero)
    world.say(setting_detail(setting))
    world.para()
    sniffle(world, hero, mistaken_name)
    ask_why(world, helper, hero)
    truth_told(world, hero, helper, mistaken_name)
    apology(world, helper, hero)
    world.para()
    ending(world, hero, helper)
    world.facts["reconciled"] = predict_healing(world)
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    return world


KNOWLEDGE = {
    "sniffle": [
        (
            "What does it mean when someone sniffles?",
            "Sniffling usually means a person has a cold, is crying, or is trying to hold back tears, so their nose makes little breathing sounds.",
        )
    ],
    "name": [
        (
            "Why is calling someone by the right name important?",
            "A name helps people feel seen and respected. Using the right name shows that you are listening and being kind.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation means people who felt hurt or upset work things out, make peace, and become friendly again.",
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology says sorry for a mistake and helps begin fixing the hurt it caused.",
        )
    ],
    "listen": [
        (
            "Why do good listeners ask questions?",
            "Good listeners ask questions so they can understand what someone באמת means and not jump to the wrong idea.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mistaken_name = f["mistaken_name"]
    return [
        f'Write a short fable for children that includes the word "sniffle" and teaches why a name matters.',
        f"Tell a gentle forest story about {hero.id}, a small {hero.label}, who gets upset when others call {hero.pronoun('object')} {mistaken_name}.",
        f"Write a reconciliation fable where a {helper.label} listens, helps correct a name, and the hurt feelings soften by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mistaken_name = f["mistaken_name"]
    return [
        QAItem(
            question=f"Why did {hero.id} start to sniffle in the story?",
            answer=(
                f"{hero.id} started to sniffle because the other animals kept calling {hero.pronoun('object')} {mistaken_name} instead of {hero.id}. "
                f"The wrong name made {hero.id} feel small and lonely."
            ),
        ),
        QAItem(
            question=f"What did the {helper.label} do when {hero.id} got quiet?",
            answer=(
                f"The {helper.label} asked why {hero.id} was so quiet, listened to the answer, and helped the others say {hero.id}'s name correctly."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the others?",
            answer=(
                f"The story ended with reconciliation. The others apologized, {hero.id} stopped sniffing, and {hero.id} returned to the circle smiling."
            ),
        ),
        QAItem(
            question=f"What clue showed that {hero.id} was telling the truth about {hero.id}'s name?",
            answer=(
                f"{hero.id} showed the name tag sewn inside {hero.pronoun('possessive')} coat, which proved that {hero.id} was telling the truth."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["sniffle", "name", "reconciliation", "apology", "listen"]:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="schoolyard", hero="mouse", name="Milo", mistaken_name="Pip", helper="turtle", season="autumn"),
    StoryParams(place="grove", hero="rabbit", name="Luna", mistaken_name="Mina", helper="fox", season="spring"),
    StoryParams(place="clearing", hero="boy", name="Ari", mistaken_name="Toby", helper="turtle", season="summer"),
]


ASP_RULES = r"""
hero(H) :- hero_kind(H).
helper(K) :- helper_kind(K).
hurt(H) :- sniffles(H).
misnamed(H) :- called_as(H, N), true_name(H, T), N != T.
needs_reconciliation(H) :- hurt(H), misnamed(H).
heard_apology(H) :- apology_given(H).
reconciled(H) :- needs_reconciliation(H), heard_apology(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero_kind", hid))
    for kid in HELPERS:
        lines.append(asp.fact("helper_kind", kid))
    for tag in KNOWLEDGE:
        lines.append(asp.fact("topic", tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small reconciliation fable world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--mistaken-name")
    ap.add_argument("--season", choices=["spring", "summer", "autumn"])
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
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(NAMES[hero])
    mistaken_name = args.mistaken_name or rng.choice([n for n in MISTAKEN_NAMES if n != name])
    season = args.season or SETTINGS[place].season
    if name == mistaken_name:
        raise StoryError("The true name and mistaken name must be different.")
    return StoryParams(place=place, hero=hero, name=name, mistaken_name=mistaken_name, helper=helper, season=season)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero, params.helper, params.name, params.mistaken_name)
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


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.hero} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
