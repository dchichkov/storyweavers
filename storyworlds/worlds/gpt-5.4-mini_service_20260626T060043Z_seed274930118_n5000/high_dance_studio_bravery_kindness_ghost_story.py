#!/usr/bin/env python3
"""
A standalone storyworld for a small ghost story set in a dance studio.

Premise:
A child dancer meets a shy ghost in a dance studio. The ghost cannot reach
a high ribbon looped on the barre. The child uses bravery to climb a small
step and kindness to help, turning fright into a friendly dance.

The world is deliberately tiny and state-driven:
- physical meters: height, reach, lift, wobble, warmth, sparkle
- emotional memes: bravery, kindness, fear, trust, joy

The story is generated from simulated state rather than from a frozen template.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    helper_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dance studio"
    affords: set[str] = field(default_factory=lambda: {"practice", "reach_high_ribbon"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    trigger: str
    effect: str
    tag: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    location: str
    region: str
    high: bool = False


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    effect: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def clone(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "studio": Setting(place="the dance studio"),
}

ACTIONS = {
    "reach_high_ribbon": Action(
        id="reach_high_ribbon",
        verb="reach the high ribbon",
        gerund="reaching for the high ribbon",
        risk="could not reach the ribbon",
        trigger="the ribbon was hung high above the barre",
        effect="the ribbon came down",
        tag="high",
        keywords={"high", "ribbon", "barre"},
    ),
    "practice": Action(
        id="practice",
        verb="practice the spin",
        gerund="practicing spins",
        risk="could wobble near the mirror",
        trigger="the mirror made the room feel bigger",
        effect="the room felt steady again",
        tag="dance",
        keywords={"dance", "spin", "mirror"},
    ),
}

PROPS = {
    "ribbon": Prop(
        id="ribbon",
        label="ribbon",
        phrase="a silver ribbon",
        location="high on the barre",
        region="high",
        high=True,
    ),
    "step": Prop(
        id="step",
        label="step stool",
        phrase="a small step stool",
        location="near the barre",
        region="floor",
        high=False,
    ),
    "mirror": Prop(
        id="mirror",
        label="mirror",
        phrase="a tall mirror",
        location="along the wall",
        region="wall",
        high=False,
    ),
}

AIDS = {
    "step_stool": Aid(
        id="step_stool",
        label="step stool",
        phrase="a little step stool",
        effect="made the high ribbon easy to reach",
        helps={"reach_high_ribbon"},
    ),
    "warm_hand": Aid(
        id="warm_hand",
        label="warm hand",
        phrase="a warm hand to hold",
        effect="helped a frightened child stay calm",
        helps={"practice", "reach_high_ribbon"},
    ),
}

NAMES = ["Mina", "Noah", "Lina", "Eli", "Rose", "Theo"]
TYPES = {"girl", "boy"}
TRAITS = ["brave", "kind", "careful", "gentle", "quiet", "curious"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "studio"
    action: str = "reach_high_ribbon"
    name: str = "Mina"
    gender: str = "girl"
    trait: str = "brave"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def ensure_reasonable(action: Action) -> None:
    if action.id not in ACTIONS:
        raise StoryError("Unknown action.")
    if "high" not in action.keywords:
        raise StoryError("This world needs the word high in the core problem.")
    if action.id != "reach_high_ribbon":
        return


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    dancer = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"balance": 0.0, "reach": 0.0, "lift": 0.0, "wobble": 0.0, "warmth": 0.0},
        memes={"bravery": 0.0, "kindness": 0.0, "fear": 0.0, "trust": 0.0, "joy": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the little ghost",
        meters={"height": 0.0, "reach": 0.0, "sparkle": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "joy": 0.0},
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        type="thing",
        label="ribbon",
        phrase="a silver ribbon",
        props={"location": PROPS["ribbon"].location},
    ))
    stool = world.add(Entity(
        id="step_stool",
        type="thing",
        label="step stool",
        phrase="a little step stool",
    ))
    warm_hand = world.add(Entity(
        id="warm_hand",
        type="thing",
        label="warm hand",
        phrase="a warm hand to hold",
    ))

    world.facts.update(dancer=dancer, ghost=ghost, ribbon=ribbon, stool=stool,
                       warm_hand=warm_hand, action=ACTIONS[params.action], params=params)
    return world


def simulate(world: World) -> None:
    dancer: Entity = world.facts["dancer"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    action: Action = world.facts["action"]  # type: ignore[assignment]
    stool: Entity = world.facts["stool"]  # type: ignore[assignment]

    world.say(f"{dancer.id} was a little {dancer.type} who loved the dance studio.")
    world.say(f"Inside the studio, the air felt bright, and the tall mirror made every step look higher.")
    world.say(f"{ghost.label} floated near the barre where {action.trigger}.")
    world.say(f"{ghost.label} wanted the ribbon, but {ghost.pronoun()} could not reach it.")

    dancer.memes["fear"] += 1.0
    dancer.memes["bravery"] += 1.0
    world.para()
    world.say(f"{dancer.id} felt a tiny shiver, but {dancer.pronoun()} took a brave breath and walked closer.")

    if action.id == "reach_high_ribbon":
        dancer.memes["kindness"] += 1.0
        ghost.memes["fear"] += 1.0
        world.say(f'"I can help," {dancer.id} said, because {dancer.pronoun("subject")} was kind as well as brave.')
        world.say(f"{dancer.id} placed the step stool under the barre and climbed carefully.")
        dancer.meters["lift"] += 1.0
        dancer.meters["reach"] += 1.0
        ghost.memes["trust"] += 1.0
        world.say(f"{ghost.label} watched with wide, hopeful eyes.")
        world.say(f"Then {dancer.id} reached the high ribbon, and the ribbon came free in a soft silver flicker.")
        ghost.meters["sparkle"] += 1.0
        ghost.memes["joy"] += 1.0
        dancer.memes["joy"] += 1.0
        dancer.meters["warmth"] += 1.0
        world.para()
        world.say(f"{ghost.label} swirled around {dancer.id} like a breeze that had learned to smile.")
        world.say(f"Together they bowed to the mirror, and the dance studio felt less spooky and more like home.")
        world.facts["resolved"] = True
    else:
        raise StoryError("Unsupported action for this storyworld.")


def generation_prompts(world: World) -> list[str]:
    dancer: Entity = world.facts["dancer"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    action: Action = world.facts["action"]  # type: ignore[assignment]
    return [
        f"Write a short ghost story set in a dance studio where {dancer.id} shows bravery and kindness.",
        f"Tell a gentle story about a child and {ghost.label} who need help with a high ribbon.",
        f"Write a child-friendly story that includes the word high and ends with a peaceful dance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    dancer: Entity = world.facts["dancer"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    action: Action = world.facts["action"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where does {dancer.id} meet {ghost.label}?",
            answer="They meet in the dance studio, where the mirror, barre, and ribbon are part of the room.",
        ),
        QAItem(
            question=f"What was the high thing {ghost.label} wanted?",
            answer=f"{ghost.label} wanted the high ribbon on the barre.",
        ),
        QAItem(
            question=f"How did {dancer.id} help?",
            answer=f"{dancer.id} used bravery to come close and kindness to bring a step stool, so the high ribbon could be reached safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the ghost smiling, the ribbon free, and the dance studio feeling warm and friendly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dance studio?",
            answer="A dance studio is a room where people practice dancing, stretch, and move to music.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard because it is the right thing to do.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping someone, using gentle words, and caring about how they feel.",
        ),
        QAItem(
            question="What does high mean?",
            answer="High means up above the floor or far from the ground.",
        ),
        QAItem(
            question="Why can a step stool help?",
            answer="A step stool gives a little extra height so someone can reach something that is high up.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A high ribbon is at risk if the action is about reaching something high.
at_risk(A) :- action(A), high_action(A).

% A useful aid is one that helps the action and preserves the gentle ending.
useful_aid(X, A) :- aid(X), helps(X, A), action(A).

valid_story(Place, Action, Aid) :- setting(Place), action(Action), useful_aid(Aid, Action), high_action(Action).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if "high" in action.keywords:
            lines.append(asp.fact("high_action", aid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    for aid, item in AIDS.items():
        for a in item.helps:
            lines.append(asp.fact("helps", aid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("studio", "reach_high_ribbon", "step_stool")}
    asp_set = set(asp_valid_stories())
    if asp_set == py:
        print(f"OK: ASP matches Python ({len(py)} valid story).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story in a dance studio.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--action", choices=ACTIONS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "studio"
    action = args.action or "reach_high_ribbon"
    if action not in ACTIONS:
        raise StoryError("Unknown action.")
    ensure_reasonable(ACTIONS[action])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
    StoryParams(place="studio", action="reach_high_ribbon", name="Mina", gender="girl", trait="brave"),
    StoryParams(place="studio", action="reach_high_ribbon", name="Noah", gender="boy", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} ({p.gender}), {p.trait} in the dance studio"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
