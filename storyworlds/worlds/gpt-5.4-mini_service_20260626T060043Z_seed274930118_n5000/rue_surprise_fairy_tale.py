#!/usr/bin/env python3
"""
storyworlds/worlds/rue_surprise_fairy_tale.py
=============================================

A small fairy-tale story world about rue, a gentle surprise, and a kind turn.

Seed tale:
---
In a little cottage garden, a child gathered rue for a sore grandmother. Under
the leaves, the child found a tiny fairy asleep in a silver cup. The fairy woke
with a start, but instead of being angry, she smiled and offered a surprise:
one bright wish, if the child used the rue to help, not to boast. The child
shared the tea, the grandmother laughed, and the garden seemed to glitter.
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


# ---------------------------------------------------------------------------
# Core entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "fairy"}
        male = {"boy", "man", "father", "grandfather", "king"}
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
    light: str
    scent: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Herb:
    id: str
    label: str
    phrase: str
    taste: str
    use: str
    magic: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    trigger: str
    reveal: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage_garden": Setting(
        place="the cottage garden",
        light="golden",
        scent="sweet earth and warm mint",
        affords={"gather"},
    ),
    "moon_wood": Setting(
        place="the moonlit wood",
        light="silver",
        scent="moss and rain",
        affords={"gather"},
    ),
    "rose_gate": Setting(
        place="the rose gate",
        light="rosy",
        scent="roses and beeswax",
        affords={"gather"},
    ),
}

HERBS = {
    "rue": Herb(
        id="rue",
        label="rue",
        phrase="a small green bundle of rue",
        taste="bitter",
        use="calm aches and chase off sour spells",
        magic="it can make a hard heart softer",
        tags={"rue", "bitter", "herb"},
    ),
}

SURPRISES = {
    "fairy": Surprise(
        id="fairy",
        label="a tiny fairy",
        phrase="a tiny fairy asleep in a silver cup",
        trigger="the child lifted the leaves",
        reveal="the fairy blinked awake and shook glitter from her wings",
        effect="she offered one bright wish and a grateful smile",
        tags={"surprise", "fairy", "magic"},
    ),
}

NAMES = {
    "girl": ["Mira", "Lina", "Nora", "Tessa", "Elena"],
    "boy": ["Eli", "Theo", "Finn", "Pip", "Milo"],
}
TRAITS = ["gentle", "brave", "curious", "kind", "hopeful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str]]:
    return [(place,) for place in SETTINGS]


def explain_rejection(place: str) -> str:
    return f"(No story: the setting {place!r} is not one of the fairytale places in this world.)"


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def _spend_worry(actor: Entity, amount: float = 1.0) -> None:
    actor.memes["worry"] = max(0.0, actor.memes.get("worry", 0.0) - amount)


def _gain(actor: Entity, key: str, amount: float = 1.0) -> None:
    actor.memes[key] = actor.memes.get(key, 0.0) + amount


def foresee(world: World, hero: Entity, herb: Herb, surprise: Surprise) -> dict[str, bool]:
    sim = world.copy()
    gather(sim, sim.get(hero.id), herb, surprise, narrate=False)
    fairy = sim.entities.get("fairy")
    return {
        "found_surprise": bool(fairy and fairy.meters.get("seen", 0.0) >= THRESHOLD),
        "kind_turn": bool(fairy and fairy.memes.get("gratitude", 0.0) >= THRESHOLD),
    }


def gather(world: World, hero: Entity, herb: Herb, surprise: Surprise, narrate: bool = True) -> None:
    if "gather" not in world.setting.affords:
        raise StoryError("This setting cannot host the gathering scene.")

    hero.meters["steps"] = hero.meters.get("steps", 0.0) + 1
    _gain(hero, "resolve", 1.0)
    if narrate:
        world.say(
            f"{hero.id} went into {world.setting.place} while the air smelled of {world.setting.scent}."
        )
        world.say(
            f"{hero.pronoun().capitalize()} wanted to gather {herb.label} because {herb.use}."
        )

    hero.meters["picked"] = hero.meters.get("picked", 0.0) + 1
    _gain(hero, "hope", 1.0)
    if narrate:
        world.say(
            f"{hero.pronoun().capitalize()} found {herb.phrase}, and its leaves tasted {herb.taste} as the fingers brushed them."
        )

    # Surprise reveal
    if surprise.id not in world.fired:
        world.fired.add(surprise.id)
        fairy = world.get("fairy")
        fairy.meters["seen"] = fairy.meters.get("seen", 0.0) + 1
        if narrate:
            world.say(f"When {surprise.trigger}, {surprise.reveal}.")
            world.say(
                f"It was {surprise.phrase}, and {surprise.effect}."
            )
        _gain(fairy, "startle", 1.0)
        _gain(fairy, "gratitude", 1.0)
        _gain(hero, "wonder", 1.0)
        _gain(hero, "kindness", 1.0)
        _spend_worry(hero, 1.0)

    # Resolution: the herb is used for help, not boast
    world.get("grandmother").meters["comfort"] = world.get("grandmother").meters.get("comfort", 0.0) + 1
    if narrate:
        world.say(
            f"{hero.id} carried the rue home and made a warm tea for {world.get('grandmother').label}."
        )
        world.say(
            f"By supper, the grandmother smiled, the fairy glittered in the window, and the garden seemed to shine a little brighter."
        )


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def tell(setting: Setting, hero_name: str, hero_gender: str, hero_trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        meters={"steps": 0.0, "picked": 0.0},
        memes={"hope": 0.0, "worry": 1.0, "wonder": 0.0, "kindness": 0.0, "resolve": 0.0},
    ))
    grandmother = world.add(Entity(
        id="grandmother",
        kind="character",
        type="grandmother",
        label="grandmother",
        meters={"comfort": 0.0},
        memes={"ache": 1.0},
    ))
    fairy = world.add(Entity(
        id="fairy",
        kind="character",
        type="fairy",
        label="fairy",
        magical=True,
        meters={"seen": 0.0},
        memes={"startle": 0.0, "gratitude": 0.0},
    ))
    herb = world.add(Entity(
        id="rue",
        type="herb",
        label="rue",
        phrase=HERBS["rue"].phrase,
        owner=hero.id,
        caretaker=grandmother.id,
    ))

    world.facts.update(hero=hero, grandmother=grandmother, fairy=fairy, herb=herb, trait=hero_trait)

    world.say(
        f"In {world.setting.place}, there lived a {hero_trait} {hero_gender} named {hero_name}."
    )
    world.say(
        f"{hero_name} loved the little herb patch, especially the rue that could {HERBS['rue'].magic}."
    )
    world.para()
    world.say(
        f"One morning, {hero_name} saw that {grandmother.label} was feeling poorly, so {hero_name} set out to gather some rue."
    )
    world.say(
        f"{hero_name} hoped the tea would bring comfort, and {world.setting.place} glimmered softly as the child walked."
    )
    world.para()
    gather(world, hero, HERBS["rue"], SURPRISES["fairy"], narrate=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short fairy tale about rue, a secret surprise, and a kind child who helps a grandmother.",
        f"Tell a gentle story where {hero.id} gathers rue and finds a magical surprise in the garden.",
        "Write a child-friendly fairy tale that ends with a happy herbal tea and a sparkling garden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    grandmother = f["grandmother"]
    qa = [
        QAItem(
            question=f"Who went to gather rue in the story?",
            answer=f"{hero.id} went to gather rue for {grandmother.label}, who needed comfort.",
        ),
        QAItem(
            question="What surprise was hiding in the rue leaves?",
            answer="A tiny fairy was hiding there, asleep in a silver cup until the leaves were lifted.",
        ),
        QAItem(
            question="What happened after the fairy woke up?",
            answer="The fairy smiled, offered a bright wish, and the child used the rue to help at home.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The grandmother felt better, and the garden seemed to glitter with a happy, fairy-tale shine.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rue in this world?",
            answer="Rue is a small herb with bitter leaves, often used in old stories for comfort and gentle magic.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when someone looks a little closer.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a story with magic, kind choices, and a wonder-filled ending.",
        ),
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- setting(P).
valid_story(P) :- place_ok(P).
surprise_story(P) :- valid_story(P), setting(P).
#show valid_story/1.
#show surprise_story/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale story world about rue and a surprising little discovery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.place not in SETTINGS:
        raise StoryError(explain_rejection(args.place))
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.trait)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1.\n#show surprise_story/1."))
        print(sorted(asp.atoms(model, "valid_story")))
        print(sorted(asp.atoms(model, "surprise_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, name="Mira", gender="girl", trait="kind", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.place} ({p.gender}, {p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
