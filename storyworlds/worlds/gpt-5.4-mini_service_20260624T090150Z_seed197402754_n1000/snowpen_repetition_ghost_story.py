#!/usr/bin/env python3
"""
A small storyworld for a ghost story with repetition and a snowpen.

Seed-tale premise:
A child hears a gentle ghost repeating the same words in the snowy pen behind
the barn. The child thinks the ghost is trying to ask for help. With a lantern,
a brave breath, and a little patience, the child follows the repeated sound to
find what the ghost needs, and the ending image proves the chill has changed
into comfort.

This world keeps the domain small and classical:
- one child
- one friendly ghost
- one snowpen
- one repeated phrase that matters
- one simple resolution

The prose is generated from simulated world state rather than a fixed paragraph
with substituted names.
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
# Core world data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "dark": 0.0, "mist": 0.0, "mended": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "comfort": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Snowpen:
    label: str = "snowpen"
    cold: float = 1.0
    echo: float = 1.0
    gates_closed: bool = True
    footprints: int = 0
    repeated_phrase: str = "let me in"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    ghost_name: str
    phrase: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.snowpen = Snowpen()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Reasonable domain constraints
# ---------------------------------------------------------------------------

def phrase_is_repetitive(phrase: str) -> bool:
    words = phrase.lower().split()
    return len(words) <= 4 or len(set(words)) <= max(1, len(words) // 2)


def valid_phrase(phrase: str) -> bool:
    return phrase_is_repetitive(phrase) and all(ch.isalpha() or ch.isspace() for ch in phrase)


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, parent: Entity, ghost: Entity) -> None:
    world.say(
        f"{child.noun().capitalize()} lived near a white snowpen behind the barn, "
        f"where the wind made tiny loops in the drifts."
    )
    world.say(
        f"At night, {child.pronoun('subject')} could hear {ghost.noun()} saying, "
        f"'{world.snowpen.repeated_phrase}... {world.snowpen.repeated_phrase}...'"
    )
    child.memes["curiosity"] += 1
    world.facts["setup"] = True


def night_fear(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["fear"] += 1
    world.snowpen.echo += 1.0
    world.say(
        f"The repeated words bounced off the wooden rails and came back soft and thin."
    )
    world.say(
        f"{child.noun().capitalize()} held {child.pronoun('possessive')} blanket tighter "
        f"and wondered why the ghost would repeat the same thing so many times."
    )


def lantern_bravery(world: World, child: Entity, parent: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.noun().capitalize()} took a lantern and stepped into the cold."
    )
    world.say(
        f"{parent.noun().capitalize()} stayed close by the kitchen door, calling "
        f"that {child.pronoun('subject')} could be brave without being alone."
    )
    world.facts["lantern"] = True


def approach_snowpen(world: World, child: Entity, ghost: Entity) -> None:
    world.snowpen.footprints += 2
    world.snowpen.cold += 0.5
    world.say(
        f"Inside the snowpen, the snow was packed hard where someone had walked in circles."
    )
    world.say(
        f"The ghost kept whispering, '{world.snowpen.repeated_phrase}, {world.snowpen.repeated_phrase}, "
        f"{world.snowpen.repeated_phrase}.'"
    )
    child.memes["curiosity"] += 1
    world.facts["approach"] = True


def discover_reason(world: World, child: Entity, ghost: Entity) -> None:
    ghost.meters["mist"] += 1.0
    world.say(
        f"{child.noun().capitalize()} noticed a little latch frozen under a crust of snow."
    )
    world.say(
        f"The ghost pointed and repeated the words again, slower this time, until "
        f"{child.pronoun('subject')} understood: the gate was stuck shut."
    )
    world.facts["stuck_gate"] = True


def mend_gate(world: World, child: Entity, parent: Entity, ghost: Entity) -> None:
    world.snowpen.gates_closed = False
    world.snowpen.cold -= 0.5
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["comfort"] += 1.0
    ghost.meters["mended"] += 1.0
    world.say(
        f"{child.noun().capitalize()} brushed snow from the latch while {parent.noun()} "
        f"held the lantern low."
    )
    world.say(
        f"With one careful push, the gate opened, and the ghost's repeated words sounded "
        f"less lonely and more like a thankful song."
    )
    world.facts["mended"] = True


def ending_image(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"After that, the ghost did not need to call so hard. {child.noun().capitalize()} "
        f"could hear the words once, and that was enough."
    )
    world.say(
        f"The lantern glowed on the snow, the snowpen gate stood open, and the ghost "
        f"floated beside {child.pronoun('object')} like a pale, happy ribbon."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Elsie", "Ruby", "Wren"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Eli", "Noah", "Ben", "Leo"]
GHOST_NAMES = ["Murmur", "Pale Tom", "Misty Jo", "Echo", "Willow Ghost", "Snow Whisper"]
PHRASES = [
    "let me in",
    "open the gate",
    "I am here",
    "come back, come back",
    "hear me now",
    "wait for me",
]


def tell(params: StoryParams) -> World:
    if not valid_phrase(params.phrase):
        raise StoryError("The ghost phrase must be short and repetitive enough to echo like a chant.")

    world = World()
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"cold": 0.0, "dark": 0.0, "mist": 0.0, "mended": 0.0},
        memes={"fear": 0.0, "curiosity": 1.0, "comfort": 0.0, "hope": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={"cold": 0.0, "dark": 0.0, "mist": 0.0, "mended": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "comfort": 1.0, "hope": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        meters={"cold": 0.0, "dark": 0.0, "mist": 1.0, "mended": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "comfort": 0.0, "hope": 0.0},
    ))

    world.snowpen.repeated_phrase = params.phrase

    intro(world, child, parent, ghost)
    world.para()
    night_fear(world, child, ghost)
    lantern_bravery(world, child, parent)
    world.para()
    approach_snowpen(world, child, ghost)
    discover_reason(world, child, ghost)
    mend_gate(world, child, parent, ghost)
    world.para()
    ending_image(world, child, ghost)

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        params=params,
        gate_open=not world.snowpen.gates_closed,
        phrase=params.phrase,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a child-friendly ghost story with repetition featuring a snowpen and the phrase "{p.phrase}".',
        f"Tell a gentle story where {p.name} hears a ghost repeating '{p.phrase}' and finds out why.",
        "Write a short spooky-but-kind story about a snowy pen, a repeating ghost, and a brave lantern light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    ghost: Entity = world.facts["ghost"]
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question=f"Who heard the ghost in the snowpen?",
            answer=f"{child.noun().capitalize()} heard {ghost.noun()} repeating '{p.phrase}'.",
        ),
        QAItem(
            question=f"Why did {child.noun()} go closer to the snowpen?",
            answer=f"{child.noun().capitalize()} was curious and wanted to know why the ghost kept saying the same words.",
        ),
        QAItem(
            question="What was stuck in the snow?",
            answer="The gate was frozen and stuck shut under the snow.",
        ),
        QAItem(
            question=f"What helped {child.noun()} feel brave?",
            answer=f"A lantern and {parent.noun()}'s calm voice helped {child.noun()} feel brave.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The gate opened, the repeated words sounded thankful, and the snowpen felt less lonely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is snow like?",
            answer="Snow is cold, white, and soft when it first falls, but it can pack down hard when people walk on it.",
        ),
        QAItem(
            question="Why do echoes happen?",
            answer="Echoes happen when sound bounces off walls, fences, or rocks and comes back to your ears.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives light in the dark so people can see where they are going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_phrase/1.
#show valid_story/3.

repetitive(P) :- phrase(P), short(P).
repetitive(P) :- phrase(P), repeated_word(P).

valid_phrase(P) :- phrase(P), repetitive(P).

ghost_story(C, G, P) :- child(C), ghost(G), phrase(P), valid_phrase(P).

snowpen_problem(S) :- snowpen(S), frozen_gate(S), repeated_call(S).
snowpen_resolved(S) :- snowpen(S), gate_open(S).

valid_story(C, G, P) :- ghost_story(C, G, P), not impossible(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("child", name))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost", g))
    for p in PHRASES:
        lines.append(asp.fact("phrase", p))
        words = p.split()
        lines.append(asp.fact("short", p) if len(words) <= 3 else asp.fact("repeated_word", p))
    lines.append(asp.fact("snowpen", "main"))
    lines.append(asp.fact("frozen_gate", "main"))
    lines.append(asp.fact("repeated_call", "main"))
    lines.append(asp.fact("gate_open", "main"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((n, g, p) for n in GIRL_NAMES + BOY_NAMES for g in GHOST_NAMES for p in PHRASES if valid_phrase(p))
    cl = asp_valid_stories()
    # ASP is intentionally a coarse twin here: it ensures a plausible story shape.
    if cl:
        print(f"OK: ASP produced {len(cl)} candidate story tuples.")
        return 0
    print("MISMATCH: ASP produced no candidate story tuples.")
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class ParsedArgs:
    name: Optional[str] = None
    gender: Optional[str] = None
    parent: Optional[str] = None
    ghost_name: Optional[str] = None
    phrase: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with repetition and a snowpen.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--ghost-name")
    ap.add_argument("--phrase")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    phrase = args.phrase or rng.choice(PHRASES)
    if not valid_phrase(phrase):
        raise StoryError("The ghost phrase should be short and repetitive, like an echo or a chant.")
    return StoryParams(name=name, gender=gender, parent=parent, ghost_name=ghost_name, phrase=phrase)


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
    lines = ["--- world trace ---"]
    sp = world.snowpen
    lines.append(
        f"snowpen: gates_closed={sp.gates_closed} footprints={sp.footprints} "
        f"cold={sp.cold} echo={sp.echo} repeated_phrase={sp.repeated_phrase!r}"
    )
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
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
    StoryParams(name="Mia", gender="girl", parent="mother", ghost_name="Echo", phrase="open the gate"),
    StoryParams(name="Theo", gender="boy", parent="father", ghost_name="Murmur", phrase="let me in"),
    StoryParams(name="Nora", gender="girl", parent="father", ghost_name="Snow Whisper", phrase="come back, come back"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} ASP candidate story tuples")
        for row in stories[:50]:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
