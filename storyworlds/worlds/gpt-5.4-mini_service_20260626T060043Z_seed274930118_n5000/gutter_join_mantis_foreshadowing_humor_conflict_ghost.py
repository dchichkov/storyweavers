#!/usr/bin/env python3
"""
A small ghost-story world with foreshadowing, humor, and conflict.

Premise:
A child hears odd tapping in the gutter after sunset. The taps seem spooky at
first, but a tiny mantis and a shy ghost are involved. The child must decide
whether to join the strange pair, face a little fear, and help fix the noisy
mess.

The world is intentionally tiny: a few setting choices, a few cast choices, and
one causal turn. The story is driven by the simulated state, not by a frozen
template.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"      # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    dusk: bool = True
    has_gutter: bool = True
    shadowy: bool = True


@dataclass
class Cast:
    hero_name: str
    hero_type: str
    parent_type: str
    ghost_name: str
    mantis_name: str


@dataclass
class StoryParams:
    setting: str
    seed: Optional[int] = None
    hero_name: str = "Milo"
    hero_gender: str = "boy"
    parent_type: str = "mother"
    ghost_name: str = "Whisp"
    mantis_name: str = "Midge"


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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "old_house": Setting(name="the old house", dusk=True, has_gutter=True, shadowy=True),
    "porch": Setting(name="the porch", dusk=True, has_gutter=True, shadowy=True),
    "backyard": Setting(name="the backyard", dusk=True, has_gutter=True, shadowy=False),
}

GHOST_TOKENS = {
    "cold": "a cold draft",
    "tap": "a tiny tapping sound",
    "rattle": "a soft rattle in the gutter",
    "glow": "a little pale glow",
}

MANTIS_FACTS = {
    "gutter": "A gutter is the long channel that catches rainwater along a roof.",
    "mantis": "A mantis is a small insect with folded front legs, like it is always praying.",
    "join": "To join means to come along with someone and be part of the group.",
}

GHOST_FACTS = {
    "ghost": "A ghost in a story is a spooky, see-through person who may be scary or friendly.",
    "foreshadowing": "Foreshadowing is a clue that hints something important may happen later.",
    "humor": "Humor is something funny that makes a story feel lighter.",
    "conflict": "Conflict is a problem or tension that a character has to face.",
}


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def hero_name_for_gender(gender: str) -> str:
    if gender == "girl":
        return random.choice(["Mina", "Ivy", "Luna", "Nora", "Pia"])
    return random.choice(["Milo", "Theo", "Otis", "Finn", "Ezra"])


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero_type = "girl" if params.hero_gender == "girl" else "boy"
    parent_type = params.parent_type
    ghost_name = params.ghost_name
    mantis_name = params.mantis_name

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=hero_type,
        label=params.hero_name,
        meters={"bravery": 0.0, "curiosity": 0.0, "mess": 0.0},
        memes={"worry": 0.0, "joy": 0.0, "conflict": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
        meters={},
        memes={"worry": 0.0},
    ))
    ghost = world.add(Entity(
        id=ghost_name,
        kind="character",
        type="ghost",
        label=ghost_name,
        meters={"glow": 1.0, "cold": 1.0},
        memes={"shyness": 1.0, "humor": 0.0, "conflict": 0.0},
    ))
    mantis = world.add(Entity(
        id=mantis_name,
        kind="character",
        type="mantis",
        label=mantis_name,
        meters={"tap": 1.0},
        memes={"patience": 1.0, "humor": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, ghost=ghost, mantis=mantis)
    return world


def foreshadow(world: World) -> None:
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    mantis = world.facts["mantis"]

    world.say(f"At dusk, {hero.id} heard {GHOST_TOKENS['tap']} near {world.setting.name}.")
    world.say(f"Something in the dark looked like {GHOST_TOKENS['glow']}, and that made {hero.id} look twice.")
    hero.meters["curiosity"] += 1
    hero.memes["worry"] += 1
    ghost.memes["shyness"] += 0.5
    mantis.memes["patience"] += 0.5
    world.facts["foreshadowed"] = True


def introduce_cast(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    ghost = world.facts["ghost"]
    mantis = world.facts["mantis"]

    world.say(
        f"{hero.id} was a little {hero.type} who loved midnight stories, "
        f"but {hero.pronoun('possessive')} {parent.label} said the old house was no place for dawdling."
    )
    world.say(
        f"Behind a loose board, {ghost.id} floated quietly, and a tiny mantis named {mantis.id} clung to a leaf by the gutter."
    )
    world.facts["introduced"] = True


def tension(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    ghost = world.facts["ghost"]
    mantis = world.facts["mantis"]

    hero.memes["worry"] += 1
    parent.memes["worry"] += 1
    ghost.memes["shyness"] += 1
    world.say(
        f"{hero.id} wanted to join them, but {hero.pronoun('possessive')} {parent.label} frowned at the spooky gutter and said, "
        f'"No climbing, and no ghost business."'
    )
    world.say(
        f"{ghost.id} made a tiny sorry face, and {mantis.id} tapped the leaf like it was trying to keep the peace."
    )
    hero.memes["conflict"] += 1
    world.facts["conflict"] = True


def resolve(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    ghost = world.facts["ghost"]
    mantis = world.facts["mantis"]

    hero.meters["bravery"] += 1
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0
    ghost.memes["humor"] += 1

    world.say(
        f"Then {mantis.id} climbed onto {hero.id}'s sleeve and pointed to the gutter, where a stuck leaf was making the tapping sound."
    )
    world.say(
        f"{ghost.id} laughed in a whisper, because the scary sound was only {GHOST_TOKENS['rattle']}."
    )
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label} joined the ghost and the mantis, and together they cleared the leaf from the gutter."
    )
    world.say(
        f"After that, {ghost.id} glowed warmly instead of eerily, and {hero.id} smiled at the quiet house, which felt friendly now."
    )
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    foreshadow(world)
    world.para()
    introduce_cast(world)
    world.para()
    tension(world)
    world.para()
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The world is reasonable when a child hears a clue in a gutter, a ghost is shy,
% and a mantis can help make the strange sound understandable.
foreshadowing(S) :- setting(S), gutter(S), dusk(S).
has_conflict(H) :- child(H), wants_to_join(H), blocked_by_parent(H).
humor(M) :- mantis(M), taps(M).
resolution(H) :- has_conflict(H), humor(_), ghost(_).

valid_story(S) :- foreshadowing(S), has_conflict(_), resolution(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dusk:
            lines.append(asp.fact("dusk", sid))
        if s.has_gutter:
            lines.append(asp.fact("gutter", sid))
        if s.shadowy:
            lines.append(asp.fact("shadowy", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_settings() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(a[0] for a in asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {sid for sid, s in SETTINGS.items() if s.has_gutter and s.dusk}
    asp_set = set(asp_reasonable_settings())
    if python_set == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} settings).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(asp_set - python_set))
    print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f'Write a short ghost story for a child that includes the words "gutter", "join", and "mantis".',
        f"Tell a spooky-but-funny story where {hero.id} hears a sound by the gutter and learns what is really making it.",
        f"Write a gentle story with foreshadowing, humor, and conflict about a child, a ghost, and a mantis.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    ghost = world.facts["ghost"]
    mantis = world.facts["mantis"]

    return [
        QAItem(
            question=f"What did {hero.id} hear near the house at dusk?",
            answer="They heard a tiny tapping sound near the gutter, which seemed spooky at first.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel torn about joining {ghost.id} and {mantis.id}?",
            answer=f"{hero.id} wanted to join them, but {hero.pronoun('possessive')} {parent.label} worried about the spooky gutter and said to stay back.",
        ),
        QAItem(
            question=f"What turned out to be the real cause of the strange noise?",
            answer="A stuck leaf in the gutter was making the tapping sound, so the noise was not a scary monster at all.",
        ),
        QAItem(
            question=f"How did the story end after {hero.id} helped?",
            answer=f"{hero.id}, {ghost.id}, {mantis.id}, and the parent worked together, and the house felt friendly and calm at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(*("What is a gutter?", MANTIS_FACTS["gutter"])),
        QAItem(*("What is a mantis?", MANTIS_FACTS["mantis"])),
        QAItem(*("What does it mean to join someone?", MANTIS_FACTS["join"])),
        QAItem(*("What is foreshadowing?", GHOST_FACTS["foreshadowing"])),
        QAItem(*("What is humor in a story?", GHOST_FACTS["humor"])),
        QAItem(*("What is conflict in a story?", GHOST_FACTS["conflict"])),
        QAItem(*("What is a ghost?", GHOST_FACTS["ghost"])),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with gutter, join, and mantis.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--ghost-name")
    ap.add_argument("--mantis-name")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or random.choice(["Milo", "Mina", "Pip", "Ivy", "Nico", "Luna"])
    parent = args.parent or rng.choice(["mother", "father"])
    ghost_name = args.ghost_name or rng.choice(["Whisp", "Murmur", "Pale", "Shy", "Boo"])
    mantis_name = args.mantis_name or rng.choice(["Midge", "Twig", "Nib", "Prong", "Nettle"])
    return StoryParams(
        setting=setting,
        seed=args.seed,
        hero_name=hero_name,
        hero_gender=gender,
        parent_type=parent,
        ghost_name=ghost_name,
        mantis_name=mantis_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="old_house", hero_name="Milo", hero_gender="boy", parent_type="mother", ghost_name="Whisp", mantis_name="Midge"),
    StoryParams(setting="porch", hero_name="Mina", hero_gender="girl", parent_type="father", ghost_name="Murmur", mantis_name="Twig"),
    StoryParams(setting="backyard", hero_name="Nico", hero_gender="boy", parent_type="mother", ghost_name="Pale", mantis_name="Nib"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(vals)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.hero_name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
