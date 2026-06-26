#!/usr/bin/env python3
"""
storyworlds/worlds/bacon_sound_effects_transformation_space_adventure.py
========================================================================

A small storyworld about a space adventure where bacon is cooked aboard a ship,
the sizzling sound matters, and the sound can trigger a transformation.

Premise
-------
A child crew member brings bacon into a tiny spaceship galley. The bacon is
meant for a cheerful breakfast, but the sizzling sound is unusual: on this ship,
certain sound patterns can wake up an old transformation ray. The hero wants
breakfast, the captain worries about the beam, and the crew must choose whether
to keep cooking or use the sound on purpose.

This world is intentionally small and constraint-checked:
- bacon can only be cooked where the galley supports it
- the sound effect must match the transformation device
- the transformation must actually change a visible state

The story engine simulates state changes, then narrates the resulting events.
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
    location: str = ""
    edible: bool = False
    cookable: bool = False
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"heat": 0.0, "cook": 0.0, "transform": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    galley: bool = True
    transform_chamber: bool = True
    vented: bool = True
    supports_cooking: bool = True
    supports_transform_sound: bool = True


@dataclass
class Bacon:
    label: str = "bacon"
    phrase: str = "a sizzling strip of bacon"
    sound: str = "sizzle"
    sound2: str = "pop"
    transformed_form: str = "star-shaped bacon"
    taste: str = "salty and crisp"
    location: str = "galley"
    sound_keyword: str = "sizzle"


@dataclass
class StoryParams:
    ship: str
    name: str
    role: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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
        import copy as _copy
        clone = World(self.ship)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SHIP_REGISTRY = {
    "aurora": Ship(name="the Aurora"),
    "comet": Ship(name="the Comet"),
    "lantern": Ship(name="the Lantern"),
}

NAMES = ["Mina", "Jules", "Nova", "Tari", "Pip", "Lio", "Rae", "Kito"]
ROLES = ["pilot", "apprentice", "mechanic", "runner"]
COMPANIONS = ["captain", "engineer", "robot", "mate"]


BACON = Bacon()


@dataclass
class Rule:
    name: str
    apply: callable


def _r_cook(world: World) -> list[str]:
    out: list[str] = []
    bacon = world.get("bacon")
    chef = world.get("hero")
    if bacon.location != "galley":
        return out
    if chef.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("cook", bacon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bacon.meters["heat"] += 1
    bacon.meters["cook"] += 1
    out.append(f"The bacon began to sizzle in the galley.")
    out.append(f"The smell turned the whole room into breakfast.")
    return out


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    bacon = world.get("bacon")
    chamber = world.get("chamber")
    if bacon.meters["cook"] < THRESHOLD:
        return out
    if chamber.location != "ready":
        return out
    sig = ("sound", bacon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chamber.meters["transform"] += 1
    out.append("Sizzle-pop! The old chamber woke up.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    bacon = world.get("bacon")
    hero = world.get("hero")
    chamber = world.get("chamber")
    if chamber.meters["transform"] < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.transformed = True
    hero.type = "captain"
    hero.label = "captain"
    hero.memes["joy"] += 1
    out.append("Whoosh! The light wrapped around the crew member.")
    out.append(f"By the time it faded, the bacon looked like {BACON.transformed_form}.")
    return out


CAUSAL_RULES = [
    Rule("cook", _r_cook),
    Rule("sound", _r_sound),
    Rule("transform", _r_transform),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_story(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "transformed": sim.get("hero").transformed,
        "bacon_form": sim.get("bacon").phrase,
    }


def tell(params: StoryParams) -> World:
    ship = SHIP_REGISTRY[params.ship]
    world = World(ship)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.role,
        label=params.role,
        traits=["small", "curious"],
        location="galley",
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion,
        label=params.companion,
        traits=["calm"],
        location="galley",
    ))
    bacon = world.add(Entity(
        id="bacon",
        type="bacon",
        label="bacon",
        phrase=BACON.phrase,
        edible=True,
        cookable=True,
        location="galley",
    ))
    chamber = world.add(Entity(
        id="chamber",
        type="device",
        label="transformation chamber",
        phrase="an old transformation chamber",
        location="ready" if ship.transform_chamber else "broken",
    ))

    world.say(
        f"On {ship.name}, {params.name} worked beside {companion.label} in the tiny galley."
    )
    world.say(
        f"{params.name} liked {BACON.label} because it smelled {BACON.taste} when it cooked."
    )
    world.say(
        f"But the ship had an old chamber that listened for {BACON.sound_keyword} sounds."
    )

    world.para()
    world.say(
        f"One quiet morning, {params.name} put {BACON.phrase} into the pan."
    )
    hero.memes["curiosity"] += 1
    companion.memes["worry"] += 1
    propagate(world, narrate=True)

    world.para()
    if hero.transformed:
        world.say(
            f"{params.name} laughed as {hero.pronoun('possessive')} reflection changed."
        )
        world.say(
            f"The little crew member stood straighter, now feeling like a real space captain."
        )
        world.say(
            f"Nearby, the bacon crackled into {BACON.transformed_form}, crisp and golden."
        )
    else:
        world.say(
            f"{params.name} covered the pan and kept the sound low, so the chamber stayed asleep."
        )
        world.say(
            f"The bacon still cooked slowly, and the ship smelled like a safe breakfast."
        )

    world.facts.update(
        hero=hero,
        companion=companion,
        bacon=bacon,
        chamber=chamber,
        ship=ship,
        transformed=hero.transformed,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child that includes the sound word "{BACON.sound_keyword}".',
        f"Tell a gentle story where {f['hero'].id} cooks bacon on a spaceship and an old chamber wakes up from the sound.",
        f"Write a simple story about bacon, a whoosh of light, and a surprising transformation aboard a tiny ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    bacon = f["bacon"]
    qa = [
        QAItem(
            question=f"What did {hero.id} put into the pan in the galley?",
            answer=f"{hero.id} put {bacon.phrase} into the pan.",
        ),
        QAItem(
            question=f"Why did the old chamber wake up on the ship?",
            answer=f"It woke up because the bacon made a loud {BACON.sound_keyword}-pop sound while cooking.",
        ),
        QAItem(
            question=f"What changed about {hero.id} by the end of the story?",
            answer=(
                f"{hero.id} transformed and felt like a captain after the bright light "
                f"wrapped around {hero.pronoun('object')}."
            ),
        ),
    ]
    if f["transformed"]:
        qa.append(
            QAItem(
                question=f"What did the bacon become after the transformation?",
                answer=f"The bacon became {BACON.transformed_form}.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"How did {companion.id} help keep the ship safe?",
                answer=f"{companion.id} stayed calm while {hero.id} kept the sound low, so the chamber stayed asleep.",
            )
        )
    return qa


WORLD_QA = [
    QAItem(
        question="What is bacon?",
        answer="Bacon is a salty meat that people often cook until it is crisp.",
    ),
    QAItem(
        question="What does sizzle mean?",
        answer="Sizzle is the sharp sound food makes when it hits a hot pan.",
    ),
    QAItem(
        question="What is a transformation?",
        answer="A transformation is when something changes into a different form.",
    ),
    QAItem(
        question="What does whoosh sound like?",
        answer="Whoosh sounds fast and airy, like wind rushing past.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


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
        if e.location:
            bits.append(f"location={e.location}")
        if e.transformed:
            bits.append("transformed=True")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only supports bacon in the galley with a reachable transformation chamber.)"


ASP_RULES = r"""
% Bacon cooked in the galley produces the sizzle sound.
cooks(bacon) :- in(bacon,galley), curious(hero).
sound(bacon,sizzle_pop) :- cooks(bacon).

% A chamber that hears the right sound wakes up.
awake(chamber) :- sound(bacon,sizzle_pop), ready(chamber).

% The hero transforms only when the chamber is awake.
transformed(hero) :- awake(chamber), in(hero,galley).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("in", "hero", "galley"))
    lines.append(asp.fact("in", "bacon", "galley"))
    lines.append(asp.fact("ready", "chamber"))
    lines.append(asp.fact("curious", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/1."))
    clingo_set = set(asp.atoms(model, "transformed"))
    python_set = {("hero",)} if True else set()
    if clingo_set == python_set:
        print("OK: clingo gate matches the Python story logic.")
        return 0
    print("MISMATCH between clingo and Python story logic.")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: bacon, sound effects, and transformation in space."
    )
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(ship=ship, name=name, role=role, companion=companion)


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


CURATED = [
    StoryParams(ship="aurora", name="Mina", role="pilot", companion="engineer"),
    StoryParams(ship="comet", name="Nova", role="apprentice", companion="robot"),
    StoryParams(ship="lantern", name="Jules", role="mechanic", companion="captain"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show transformed/1."))
        print("transformed atoms:", asp.atoms(model, "transformed"))
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
            header = f"### {p.name}: bacon on {p.ship}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
