#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-style surprise at a bus stop lobby.

Premise:
- A child waits at a bus stop.
- The lobby/shelter feels a little eerie because of an old novelty toy.
- A harmless ghost appears, causing surprise.
- A kind action resolves the scare into a friendly, cozy ending.

The world is intentionally tiny and classical: one setting, a handful of entities,
physical meters for visible state, emotional memes for feelings, and a short
state-driven arc that can be rendered as a complete children's story.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bus stop"
    affords: set[str] = field(default_factory=lambda: {"novelty"})


@dataclass
class Surprise:
    id: str
    label: str
    trigger: str
    reveal: str
    safe: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mia"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    setting: str = "bus_stop_surprise"
    surprise: str = "ghost"


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes.get("surprise", 0.0) < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["visible"] = 1
    out.append(f"A little ghost drifted out from behind the lobby bench.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["comfort"] = 1.0
    ghost.memes["kindness"] = 1.0
    out.append("The ghost only waved and pointed to the bus schedule, as if it wanted to help.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_surprise, _r_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def world_intro(world: World, child: Entity, parent: Entity, novelty: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved quiet waits at the bus stop."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.type} stood nearby, "
        f"and a shiny novelty coin in the lobby made the place feel extra odd."
    )


def build_world(params: StoryParams) -> World:
    setting = Setting(place="the bus stop lobby", affords={"novelty"})
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"still": 1.0},
        memes={"curiosity": 1.0, "surprise": 0.0, "fear": 0.0, "comfort": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={"watchful": 1.0},
        memes={"care": 1.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="a ghost",
        meters={"visible": 0.0, "drift": 1.0},
        memes={"kindness": 0.0},
    ))
    novelty = world.add(Entity(
        id="novelty",
        kind="thing",
        type="novelty",
        label="novelty coin",
        phrase="a shiny novelty coin",
        owner="lobby",
        meters={"gleam": 1.0},
    ))

    world_intro(world, child, parent, novelty)

    world.para()
    world.say(
        f"At the bus stop lobby, {child.id} noticed {novelty.phrase} on the bench."
    )
    world.say(
        f"It was a tiny surprise, the kind that makes a place feel a little spooky."
    )
    child.memes["surprise"] += 1.0
    child.memes["fear"] += 1.0
    world.facts["first_surprise"] = True
    world.facts["novelty"] = novelty
    world.facts["ghost"] = ghost
    world.facts["child"] = child
    world.facts["parent"] = parent

    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.id} took a careful breath and held up the novelty coin like a lantern."
    )
    world.say(
        f"The ghost drifted closer, pointed at the timetable, and smiled as if saying hello."
    )
    child.memes["fear"] = 0.0
    child.memes["comfort"] = 1.0
    child.memes["joy"] = 1.0
    ghost.memes["kindness"] = 1.0
    ghost.meters["visible"] = 1.0

    world.para()
    world.say(
        f"When the bus finally came, {child.id} was not scared anymore."
    )
    world.say(
        f"{child.id} waved at the ghost, and the ghost waved back from the lobby window."
    )
    world.say(
        f"The bus stop felt cozy again, with the novelty coin shining softly beside {child.id}."
    )

    world.facts["resolved"] = True
    world.facts["setting"] = setting
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short ghost story for a young child set at a bus stop, where a novelty coin causes a surprise.',
        'Tell a gentle story about a child in a lobby at the bus stop who gets a spooky surprise and then feels safe again.',
        'Write a simple story that includes the words "novelty" and "lobby" and ends with a friendly ghost.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.label}, a curious little {child.type}, and {parent.label}, who stays with {child.label} at the bus stop lobby.",
        ),
        QAItem(
            question="What caused the first surprise?",
            answer="A shiny novelty coin on the bench made the lobby feel spooky and gave the child a small surprise.",
        ),
        QAItem(
            question="What did the ghost do when it appeared?",
            answer="The ghost drifted out from behind the bench, then waved and pointed at the bus schedule so it felt friendly instead of scary.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The child felt safe again, waved at the ghost, and waited for the bus while the novelty coin shone softly in the lobby.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus stop for?",
            answer="A bus stop is a place where people wait for a bus to come and pick them up.",
        ),
        QAItem(
            question="What is a lobby?",
            answer="A lobby is an entry area or waiting space inside a building where people can pause before going farther in.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is usually the spirit of someone who has died, but in children's stories it can be friendly and harmless.",
        ),
        QAItem(
            question="What does novelty mean?",
            answer="Novelty means something new, unusual, or made mostly to surprise and delight people.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "bus_stop": Setting(place="the bus stop lobby", affords={"novelty"}),
}

SURPRISES = {
    "ghost": Surprise(
        id="ghost",
        label="ghost",
        trigger="novelty coin",
        reveal="a friendly ghost",
        safe=True,
    ),
}

TRAITS = ["curious", "quiet", "brave", "gentle", "wondering"]
NAMES = {
    "girl": ["Mia", "Ava", "Nora", "Lina", "Zoe"],
    "boy": ["Noah", "Eli", "Milo", "Theo", "Finn"],
}


@dataclass
class StoryContext:
    params: StoryParams
    world: World


def valid_combos() -> list[tuple[str, str]]:
    return [("bus_stop", "ghost")]


ASP_RULES = r"""
setting(bus_stop).
affords(bus_stop, novelty).

surprise(ghost).
trigger(ghost, novelty).
safe(ghost).

valid_story(S, Su) :- setting(S), affords(S, novelty), surprise(Su), trigger(Su, novelty), safe(Su).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "bus_stop"), asp.fact("affords", "bus_stop", "novelty")]
    lines.append(asp.fact("surprise", "ghost"))
    lines.append(asp.fact("trigger", "ghost", "novelty"))
    lines.append(asp.fact("safe", "ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story bus stop world with a novelty surprise.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES[args.gender]),
        gender=args.gender,
        parent=args.parent,
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(vals)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i in range(5):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
