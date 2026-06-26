#!/usr/bin/env python3
"""
pretzel_pokey_reinforce_inner_monologue_surprise_mystery.py
============================================================

A small rhyming storyworld about a pokey pretzel mystery that gets reinforced
with a clever fix, using an inner monologue, a surprise clue, and a solved
mystery.

The simulated domain is a tiny bake-shop scene:
- A child finds a pokey pretzel that snaps too easily.
- A surprise clue appears: a loose ribbon tag and a crumb trail.
- The child thinks aloud in an inner monologue, then reinforces the pretzel
  with a warm wrap so it can carry a badge for the bake fair.

The story stays grounded in the world model: the pretzel has physical meters
for crispness, bendiness, and strength; the child has meme state for worry,
curiosity, and delight.
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

RHYME_ENDINGS = {
    "start": ["glow", "show", "flow", "toe"],
    "mystery": ["glow", "know", "show"],
    "resolve": ["bright", "light", "kite"],
}

NAMES = ["Mina", "Toby", "Luna", "Eli", "Pia", "Noah", "Nia", "Owen"]
GUARDIANS = ["mom", "dad", "aunt", "uncle", "grandma"]
PLACES = ["the little bake shop", "the sunny kitchen", "the cozy bakery corner"]
BAKE_GOODS = ["pretzel", "twisty pretzel", "salty pretzel", "brown pretzel"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["crispness", "bendiness", "strength", "warmth", "cleanliness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "curiosity", "delight", "surprise", "relief", "resolve"]:
            self.memes.setdefault(k, 0.0)


@dataclass
class Setting:
    place: str = "the little bake shop"
    smell: str = "sweet cinnamon"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            setting=copy.deepcopy(self.setting),
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    guardian: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def _is_pokey(pretzel: Entity) -> bool:
    return pretzel.meters["crispness"] >= 1.0 and pretzel.meters["bendiness"] <= 0.5


def _needs_reinforce(pretzel: Entity) -> bool:
    return pretzel.meters["strength"] < 1.0


def _predict_break(world: World, pretzel_id: str) -> bool:
    sim = world.copy()
    pretzel = sim.get(pretzel_id)
    pretzel.meters["strength"] -= 0.5
    pretzel.meters["crispness"] += 0.2
    return pretzel.meters["strength"] < 1.0


def _make_pokey_clue(world: World) -> str:
    ribbon = world.entities.get("ribbon")
    if ribbon and ribbon.carried_by == "wind":
        return "a ribbon tag fluttering near the shelf"
    return "a crumb trail by the counter"


def build_world(params: StoryParams) -> World:
    setting = Setting(place=params.place)
    world = World(setting=setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="child", label=params.hero_name))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.guardian, label=params.guardian))
    pretzel = world.add(Entity(
        id="pretzel",
        type="pretzel",
        label="pretzel",
        phrase="a warm twisty pretzel",
        owner=hero.id,
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        type="ribbon",
        label="ribbon",
        phrase="a little ribbon tag",
        carried_by="wind",
    ))
    wrap = world.add(Entity(
        id="wrap",
        type="wrap",
        label="butter wrap",
        phrase="a soft butter wrap",
    ))

    # Initial state.
    pretzel.meters["crispness"] = 1.0
    pretzel.meters["bendiness"] = 0.2
    pretzel.meters["strength"] = 0.4
    pretzel.meters["warmth"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["surprise"] = 1.0

    world.facts.update(
        hero=hero,
        guardian=guardian,
        pretzel=pretzel,
        ribbon=ribbon,
        wrap=wrap,
        clue=_make_pokey_clue(world),
    )
    return world


def tell_story(world: World) -> World:
    f = world.facts
    hero: Entity = f["hero"]
    guardian: Entity = f["guardian"]
    pretzel: Entity = f["pretzel"]
    clue: str = f["clue"]

    world.say(
        f"In {world.setting.place}, where the air smelled like {world.setting.smell}, "
        f"{hero.id} found a pretzel so pokey and neat, it looked like a crunchy treat."
    )
    world.say(
        f"It twinkled in a basket with a little tilt, yet one tiny tap made it bend and wilt."
    )
    world.say(
        f"{hero.id} frowned and thought, 'Why so sharp, so fast? Will this pretzel stay whole, or will it not last?'"
    )
    hero.memes["worry"] += 1.0

    world.para()
    world.say(
        f"Then came a surprise: {clue}, just there in sight."
    )
    hero.memes["surprise"] += 1.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{hero.id} whispered, 'Hmm, that clue feels funny. It may be the key to the pretzel's bumpy journey.'"
    )
    world.say(
        f"'If the twist is too pokey and breaks with a click, maybe I can reinforce it quick.'"
    )
    hero.memes["resolve"] += 1.0

    world.para()
    if _predict_break(world, pretzel.id):
        world.say(
            f"{guardian.id} nodded, 'You're right to pause; a weak little twist needs a kinder cause.'"
        )
        world.say(
            f"So {hero.id} wrapped the pretzel with warm butter wrap, a gentle soft hug, not a hard little trap."
        )
        pretzel.meters["strength"] += 1.2
        pretzel.meters["bendiness"] += 0.4
        pretzel.meters["warmth"] += 0.5
        pretzel.meters["cleanliness"] += 0.2
        hero.memes["relief"] += 1.0
        hero.memes["delight"] += 1.0
        world.say(
            f"The pokey pretzel stood tall, no longer so shy; it got extra strength and a brighter-sure sky."
        )
        world.say(
            f"At the bake fair, it kept its proud twist, and {hero.id} grinned wide, with a satisfied mist."
        )
    else:
        world.say(
            f"{hero.id} tried a small fix, and the pretzel stayed bright; the mystery melted in warm golden light."
        )
        pretzel.meters["strength"] += 0.6
        hero.memes["relief"] += 1.0
        hero.memes["delight"] += 1.0

    world.facts["solved"] = True
    world.facts["reinforced"] = pretzel.meters["strength"] >= 1.0
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bake_shop": Setting(place="the little bake shop", smell="sweet cinnamon"),
    "kitchen": Setting(place="the sunny kitchen", smell="buttery toast"),
    "bakery_corner": Setting(place="the cozy bakery corner", smell="vanilla sugar"),
}

# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        f'Write a rhyming story for a child named {hero.id} about a pokey pretzel mystery.',
        f'Tell a gentle story with an inner monologue, a surprise clue, and a way to reinforce a pretzel.',
        "Create a short child-facing rhyme where a small problem gets solved with a soft, clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guardian: Entity = f["guardian"]
    pretzel: Entity = f["pretzel"]
    clue: str = f["clue"]

    return [
        QAItem(
            question=f"What did {hero.id} notice at {world.setting.place}?",
            answer=(
                f"{hero.id} noticed a pokey pretzel that looked crunchy and a little fragile. "
                f"The pretzel seemed strong at first, but it did not have enough strength to stay safe."
            ),
        ),
        QAItem(
            question="What surprise clue helped the child think?",
            answer=(
                f"The surprise clue was {clue}. It gave {hero.id} a new idea and made the mystery feel solvable."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} think in the inner monologue?",
            answer=(
                f"{hero.id} thought that the pretzel might break if it stayed too pokey, and wondered how to reinforce it kindly."
            ),
        ),
        QAItem(
            question=f"How was the pretzel reinforced?",
            answer=(
                f"{hero.id} wrapped the pretzel with a warm butter wrap, which gave it more strength and helped it stay whole."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel when the mystery was solved?",
            answer=(
                f"{hero.id} felt relief and delight when the pretzel stood tall and the problem was solved."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does reinforce mean?",
        answer=(
            "To reinforce something means to make it stronger so it can hold together better."
        ),
    ),
    QAItem(
        question="What is a surprise?",
        answer="A surprise is something unexpected that makes you pause and pay attention.",
    ),
    QAItem(
        question="What is a mystery?",
        answer="A mystery is a puzzle or unknown thing that needs thinking to solve.",
    ),
    QAItem(
        question="What is an inner monologue?",
        answer="An inner monologue is the quiet thinking voice inside your head.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

valid(Place, Hero, Guardian) :- place(Place), hero(Hero), guardian(Guardian).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for h in NAMES:
        lines.append(asp.fact("hero", h))
    for g in GUARDIANS:
        lines.append(asp.fact("guardian", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(place, hero, guardian) for place in SETTINGS for hero in NAMES for guardian in GUARDIANS}
    asp_set = set(asp_valid_triples())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(asp_set)} combos).")
        return 0
    print("MISMATCH:")
    if python_set - asp_set:
        print(" only in python:", sorted(python_set - asp_set)[:10])
    if asp_set - python_set:
        print(" only in asp:", sorted(asp_set - python_set)[:10])
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: pretzel, pokey, reinforce; inner monologue, surprise, mystery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    hero_name = args.name or rng.choice(NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(place=place, hero_name=hero_name, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_triples()
        print(f"{len(triples)} compatible triples:")
        for t in triples[:50]:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(SETTINGS):
            params = StoryParams(place=place, hero_name=NAMES[i % len(NAMES)], guardian=GUARDIANS[i % len(GUARDIANS)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
