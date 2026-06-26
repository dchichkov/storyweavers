#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/snake_dim_misunderstanding_curiosity_kindness_ghost_story.py
==============================================================================================================

A small, child-facing ghost-story world built from a seed image of a
snake-dim place: a little dark, twisty hallway where a child, a ghost,
curiosity, misunderstanding, and kindness can all change the ending.

The domain is intentionally tiny and classical:
- one setting with a dim, snake-like passage
- one curious child
- one ghost who seems scary at first
- one misunderstanding about the ghost's intentions
- one act of kindness that resolves the scare

The world is simulated, not just narrated. Physical state uses meters
(light, dimness, openness, spookiness, etc.) and emotional state uses
memes (curiosity, fear, misunderstanding, kindness, relief).
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
# Tiny world model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["light", "dimness", "spookiness", "open", "cold", "dust"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "fear", "misunderstanding", "kindness", "relief", "bravery"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    feature: str = "snake-dim hallway"


@dataclass
class StoryParams:
    place: str
    feature: str
    name: str
    gender: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "house": Setting(place="the old house", feature="snake-dim hallway"),
    "attic": Setting(place="the attic", feature="snake-dim stairway"),
    "cellar": Setting(place="the cellar", feature="snake-dim tunnel"),
    "museum": Setting(place="the quiet museum", feature="snake-dim side hall"),
}

NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Zoe", "Maya", "Iris"],
    "boy": ["Eli", "Theo", "Ben", "Noah", "Finn", "Sam"],
}

GHOST_NAMES = ["Moss", "Pale Pip", "Willow", "Boo", "Mister Hush", "Pearl"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def _setup_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.place])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["little", "curious", "kind"],
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        traits=["quiet", "lonely", "gentle"],
    ))
    hallway = world.add(Entity(
        id="hallway",
        kind="thing",
        type="place",
        label=params.feature,
        phrase=params.feature,
    ))

    # Initial physical mood.
    hallway.meters["dimness"] = 3.0
    hallway.meters["cold"] = 1.5
    hallway.meters["open"] = 0.5
    ghost.meters["dimness"] = 1.0
    ghost.meters["spookiness"] = 2.0

    # Initial emotional state.
    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.2
    ghost.memes["kindness"] = 0.4
    ghost.memes["misunderstanding"] = 1.0

    world.facts.update(child=child, ghost=ghost, hallway=hallway)
    return world


def _narrate_intro(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    s = world.setting
    world.say(
        f"On a quiet night in {s.place}, {c.id} found a {s.feature} that felt extra snake-dim."
    )
    world.say(
        f"{c.id} listened to the hush and wondered who was hiding there, while {g.label} drifted nearby."
    )


def _advance_misunderstanding(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    hallway: Entity = world.facts["hallway"]

    if ("peek",) not in world.fired:
        world.fired.add(("peek",))
        c.memes["curiosity"] += 1.0
        hallway.meters["open"] += 0.5
        world.say(
            f"{c.id} tiptoed closer with wide eyes. {c.pronoun().capitalize()} wanted to know what made the shadows wiggle."
        )

    if ("spook",) not in world.fired:
        world.fired.add(("spook",))
        c.memes["fear"] += 1.2
        c.memes["misunderstanding"] += 1.0
        g.memes["misunderstanding"] += 0.5
        world.say(
            f"Then a soft float of white cloth fluttered in the dark, and {c.id} thought {g.label} might be a scary ghost."
        )
        world.say(
            f"{c.id} took a step back, because in the snake-dim hallway even a little rustle can sound like a warning."
        )


def _advance_kindness(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    hallway: Entity = world.facts["hallway"]

    if ("kindness",) not in world.fired:
        world.fired.add(("kindness",))
        g.memes["kindness"] += 1.0
        g.meters["spookiness"] -= 1.0
        hallway.meters["dimness"] -= 0.5
        world.say(
            f"Instead of chasing {c.id}, {g.label} slowly lifted a lantern and made the dark less heavy."
        )
        world.say(
            f"{g.label} pointed to a lost paper star stuck in a crack, as if asking for help."
        )
        c.memes["understanding"] = c.memes.get("understanding", 0.0) + 1.0
        c.memes["kindness"] += 1.0
        c.memes["fear"] = max(0.0, c.memes["fear"] - 0.7)
        c.memes["misunderstanding"] = max(0.0, c.memes["misunderstanding"] - 0.8)
        world.say(
            f"{c.id} understood at once that the ghost was not trying to scare anyone; {c.id} was asking for kindness."
        )
        world.say(
            f"{c.id} gently reached into the crack and freed the paper star."
        )


def _advance_resolution(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    hallway: Entity = world.facts["hallway"]

    if ("resolve",) not in world.fired:
        world.fired.add(("resolve",))
        c.memes["relief"] += 1.0
        c.memes["bravery"] += 1.0
        g.memes["relief"] += 1.0
        hallway.meters["dimness"] = max(0.0, hallway.meters["dimness"] - 1.0)
        hallway.meters["open"] += 1.0
        world.say(
            f"{g.label} gave {c.id} a shy bow, and the hallway seemed less snake-dim right away."
        )
        world.say(
            f"Together they hung the paper star where it could glow, and the little spooky place became a friendly one."
        )


def run_story(world: World) -> None:
    _narrate_intro(world)
    world.para()
    _advance_misunderstanding(world)
    world.para()
    _advance_kindness(world)
    _advance_resolution(world)


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    run_story(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Entity = f["child"]
    g: Entity = f["ghost"]
    hallway: Entity = f["hallway"]
    return [
        f'Write a short ghost story for a young child that includes the phrase "snake-dim" and ends kindly.',
        f"Tell a gentle story about {c.id} who is curious in {world.setting.place}, misunderstands {g.label}, and learns the truth.",
        f"Write a spooky-but-soft story set in {hallway.label} where curiosity turns a scare into kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]
    g: Entity = f["ghost"]
    hallway: Entity = f["hallway"]
    return [
        QAItem(
            question=f"Why did {c.id} feel nervous in {world.setting.place}?",
            answer=(
                f"{c.id} felt nervous because the {hallway.label} was snake-dim, and a flutter in the dark made the place seem spooky."
            ),
        ),
        QAItem(
            question=f"What did {c.id} first think about {g.label}?",
            answer=(
                f"At first, {c.id} thought {g.label} might be a scary ghost, because of a misunderstanding in the dark hallway."
            ),
        ),
        QAItem(
            question=f"How did the story change when {g.label} showed kindness?",
            answer=(
                f"When {g.label} showed kindness with a lantern and a gentle request for help, {c.id} understood the ghost was not mean at all."
            ),
        ),
        QAItem(
            question=f"What helped the ending become happy?",
            answer=(
                f"{c.id}'s curiosity, {g.label}'s kindness, and the shared task of freeing the paper star helped the ending become happy."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="In a story, a ghost is usually a spooky-looking spirit. In gentle stories, a ghost can also be shy, lonely, or kind.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to learn more about something and asking questions or looking closer.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what another person means or wants.",
        )
    ],
    "snake-dim": [
        QAItem(
            question="What does snake-dim mean in this story?",
            answer="Snake-dim means the place is very dark and twisty, like a snake-shaped hallway with shadows curling along it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ["ghost", "curiosity", "kindness", "misunderstanding", "snake-dim"] for qa in WORLD_KNOWLEDGE[key]]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts describe entities and their traits.
child(C) :- kind(C, character), type(C, girl).
child(C) :- kind(C, character), type(C, boy).
ghost(G) :- kind(G, character), type(G, ghost).

% A misunderstanding happens when the child has fear and the ghost seems spooky.
misunderstood(C, G) :- child(C), ghost(G), fear(C), spooky(G).

% Curiosity makes the child approach the spooky place.
approaches(C, P) :- child(C), curious(C), setting(P), dim_place(P).

% Kindness resolves the misunderstanding.
resolved(C, G) :- child(C), ghost(G), kind(G), helped(C, G).

#show compatible/2.
compatible(curiosity, kindness).
compatible(misunderstanding, kindness).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("feature", sid, s.feature))
        if "snake-dim" in s.feature:
            lines.append(asp.fact("dim_place", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show compatible/2."))
    got = sorted(set(asp.atoms(model, "compatible")))
    expected = [("curiosity", "kindness"), ("misunderstanding", "kindness")]
    if got == expected:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH between ASP twin and expected compatibility facts.")
    print("got:", got)
    print("expected:", expected)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world about curiosity, misunderstanding, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
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
    name = args.name or rng.choice(NAMES[gender])
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    feature = SETTINGS[place].feature
    if not feature:
        raise StoryError("This world needs a spooky setting feature.")
    return StoryParams(place=place, feature=feature, name=name, gender=gender, ghost_name=ghost_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="house", feature=SETTINGS["house"].feature, name="Mina", gender="girl", ghost_name="Moss"),
    StoryParams(place="cellar", feature=SETTINGS["cellar"].feature, name="Eli", gender="boy", ghost_name="Willow"),
    StoryParams(place="museum", feature=SETTINGS["museum"].feature, name="Nora", gender="girl", ghost_name="Pale Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(set(asp.atoms(model, "compatible"))))
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
            header = f"### {p.name}: {p.place} / {p.feature}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
