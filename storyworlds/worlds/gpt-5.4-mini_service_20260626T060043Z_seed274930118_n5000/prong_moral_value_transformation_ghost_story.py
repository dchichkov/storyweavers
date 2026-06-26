#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prong_moral_value_transformation_ghost_story.py
==============================================================================================================

A standalone story world in a ghost-story style: a child meets a lonely ghost,
a prong-shaped keepsake becomes the source of tension, and a moral choice leads
to a transformation.

The world models:
- typed entities with physical meters and emotional memes
- a small causal story about fear, greed, kindness, and change
- child-facing prose with a spooky-but-gentle tone
- an inline ASP twin for the reasonableness gate

Theme words: prong, moral value, transformation
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


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
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
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    alive: bool = True
    spectral: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "cold": 0.0, "bright": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "kindness": 0.0, "greed": 0.0, "hope": 0.0, "change": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label or self.type


@dataclass
class Place:
    name: str
    eerie: bool = True
    affords: set[str] = field(default_factory=set)
    cover: str = ""


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    protected_by: str = ""


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mood: str = "eerie"

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.mood = self.mood
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(name="the attic", eerie=True, affords={"search", "hide"}, cover="dusty rafters"),
    "graveyard": Place(name="the graveyard", eerie=True, affords={"search", "hide"}, cover="old stones"),
    "cellar": Place(name="the cellar", eerie=True, affords={"search", "hide"}, cover="brick walls"),
}

ACTIONS = {
    "search": {
        "verb": "search the shadows",
        "gerund": "searching the shadows",
        "rush": "rush into the shadows",
        "risk": "cold",
        "value": "curiosity",
    },
    "hide": {
        "verb": "hide from the ghostly wind",
        "gerund": "hiding from the ghostly wind",
        "rush": "dash behind the boxes",
        "risk": "dust",
        "value": "courage",
    },
    "listen": {
        "verb": "listen for the old whisper",
        "gerund": "listening for the old whisper",
        "rush": "lean closer to the whisper",
        "risk": "cold",
        "value": "patience",
    },
}

ARTIFACTS = {
    "prong": Artifact(
        id="prong",
        label="prong",
        phrase="a small silver prong from an old lantern hook",
        kind="prong",
        risk="lost",
        protected_by="sharing",
    ),
    "latch": Artifact(
        id="latch",
        label="latch",
        phrase="a brass latch with a bent edge",
        kind="latch",
        risk="stuck",
        protected_by="care",
    ),
    "bell": Artifact(
        id="bell",
        label="bell",
        phrase="a tiny bell tied with blue string",
        kind="bell",
        risk="silent",
        protected_by="kindness",
    ),
}

CHILD_NAMES = ["Mina", "Owen", "Tia", "Leo", "Nora", "Eli"]
GHOST_NAMES = ["Murk", "Pale Tom", "Wisp", "Misty", "Old Vale"]
TRAITS = ["curious", "brave", "gentle", "stubborn", "quiet"]


@dataclass
class StoryParams:
    place: str
    action: str
    artifact: str
    child_name: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def artifact_at_risk(action: str, artifact: Artifact) -> bool:
    return action in {"search", "hide", "listen"} and artifact.risk in {"lost", "stuck", "silent"}


def selects_reasonable_fix(action: str, artifact: Artifact) -> bool:
    # The moral turn is only reasonable if the child can answer with a helpful act.
    if artifact.id == "prong":
        return action in {"search", "listen"}
    if artifact.id == "latch":
        return action in {"search", "hide"}
    if artifact.id == "bell":
        return action in {"listen", "hide"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for action in ACTIONS:
            for artifact in ARTIFACTS:
                if artifact_at_risk(action, ARTIFACTS[artifact]) and selects_reasonable_fix(action, ARTIFACTS[artifact]):
                    combos.append((place, action, artifact))
    return combos


def explain_rejection(action: str, artifact: Artifact) -> str:
    return (
        f"(No story: {artifact.label} does not create a strong enough ghost-story problem "
        f"for {ACTIONS[action]['verb']}. The moral turn needs a real risk and a real fix.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def predict_outcome(world: World, child: Entity, action: str, artifact: Entity) -> dict:
    sim = world.copy()
    do_action(sim, child.id, action, narrate=False)
    ghost = sim.facts["ghost"]
    return {
        "fear": ghost.memes["fear"],
        "hope": child.memes["hope"],
        "changed": ghost.memes["change"] >= THRESHOLD,
    }


def do_action(world: World, child_id: str, action: str, narrate: bool = True) -> None:
    child = world.get(child_id)
    child.memes[ACTIONS[action]["value"]] += 1
    if action == "search":
        child.meters["cold"] += 1
    elif action == "hide":
        child.meters["dust"] += 1
    elif action == "listen":
        child.meters["cold"] += 0.5

    ghost = world.facts["ghost"]
    if action == "search":
        ghost.memes["fear"] += 1
    elif action == "hide":
        ghost.memes["greed"] += 0.5
    elif action == "listen":
        ghost.memes["hope"] += 1

    if narrate:
        propagate(world)


def propagate(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.facts["ghost"]
    child = world.facts["child"]
    artifact = world.facts["artifact"]

    sig = ("ghost_warn", ghost.id)
    if ghost.memes["fear"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        out.append(f"The air went cold, and {ghost.name_or_label()} whispered from the dark.")

    sig = ("artifact_loss", artifact.id)
    if child.meters["dust"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        out.append(f"Little dust clouds clung to {child.id}'s sleeves as the old thing slipped from sight.")

    sig = ("moral_turn", child.id)
    if child.memes["kindness"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        ghost.memes["change"] += 1
        ghost.memes["greed"] = 0.0
        ghost.memes["fear"] = 0.0
        out.append(f"That kind choice made the ghost soften, as if a knot inside the dark had untied itself.")
    if out:
        for line in out:
            world.say(line)
    return out


def build_story(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type="child"))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", spectral=True))
    artifact = world.add(Entity(
        id=params.artifact,
        kind="thing",
        type=params.artifact,
        label=ARTIFACTS[params.artifact].label,
        phrase=ARTIFACTS[params.artifact].phrase,
        owner=ghost.id,
    ))
    world.facts.update(child=child, ghost=ghost, artifact=artifact, params=params)

    # Act 1: setup
    world.say(f"{child.id} was a {params.trait} child who liked old places where the air felt full of secrets.")
    world.say(f"One dim evening, {child.id} wandered into {world.place.name}, where {ghost.name_or_label()} kept watch over {artifact.phrase}.")
    world.say(f"The ghost said the little {artifact.label} was important, because it helped keep the old memory from drifting away.")

    # Act 2: tension
    world.para()
    world.say(f"{child.id} wanted to {ACTIONS[params.action]['verb']}, but the whisper in the dark made the room feel smaller.")
    do_action(world, child.id, params.action)
    world.say(f"{child.id} noticed the {artifact.label} trembling in the shadows, and the ghost grew frightened that it might be lost.")

    # Act 3: turn and resolution
    world.para()
    child.memes["kindness"] += 1
    world.say(
        f"Then {child.id} did not grab the thing away. {child.id} held out both hands and promised to help look after it."
    )
    if params.artifact == "prong":
        world.say(
            f"Together they found the prong tucked near the broken lantern hook, and {child.id} carried it carefully, like a tiny silver tooth from the night."
        )
    elif params.artifact == "latch":
        world.say(
            f"Together they loosened the latch with gentle fingers, and the old door finally sighed open without a squeak."
        )
    else:
        world.say(
            f"Together they tied the bell back in place, and its soft ring sounded like a moonbeam touching the floorboards."
        )
    propagate(world)
    world.say(
        f"After that, {ghost.name_or_label()} was not so frightening anymore. The ghost felt lighter, and {child.id} walked home with a brave little smile."
    )

    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
action(A) :- activity(A).
artifact(X) :- relic(X).

at_risk(A, X) :- action(A), artifact(X), risk(X, lost), affects(A, search).
at_risk(A, X) :- action(A), artifact(X), risk(X, stuck), affects(A, hide).
at_risk(A, X) :- action(A), artifact(X), risk(X, silent), affects(A, listen).

reasonable_fix(A, X) :- at_risk(A, X), helpful(A, X).

valid(Place, Action, Artifact) :- place(Place), action(Action), artifact(Artifact),
                                  at_risk(Action, Artifact), reasonable_fix(Action, Artifact).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid in ACTIONS:
        lines.append(asp.fact("activity", aid))
    for rid, art in ARTIFACTS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("risk", rid, art.risk))
        for act in ACTIONS:
            if selects_reasonable_fix(act, art):
                lines.append(asp.fact("helpful", act, rid))
    for act in ACTIONS:
        lines.append(asp.fact("affects", act, act))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
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


# ---------------------------------------------------------------------------
# Q&A and prose
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a gentle ghost story for a young child that includes the word "prong".',
        f"Tell a spooky-but-kind story where {p.child_name} meets {p.ghost_name} in {world.place.name} and learns a moral lesson.",
        f"Write a short story about a child, a ghost, and a prong that ends with a transformation from fear to kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    artifact = world.facts["artifact"]

    return [
        QAItem(
            question=f"Who was the story about in {world.place.name}?",
            answer=(
                f"It was about {child.id}, a {p.trait} child, and {ghost.name_or_label()}, a lonely ghost who guarded {artifact.phrase}."
            ),
        ),
        QAItem(
            question=f"What did {child.id} want to do at the beginning of the story?",
            answer=(
                f"{child.id} wanted to {ACTIONS[p.action]['verb']}, but the ghostly room felt full of secrets and shadows."
            ),
        ),
        QAItem(
            question=f"Why did the ghost care so much about the {artifact.label}?",
            answer=(
                f"The ghost cared because the {artifact.label} held an old memory, and the ghost was afraid it would be lost."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, the ghost was less frightened and more hopeful, because {child.id} chose kindness instead of taking the thing away."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prong?",
            answer="A prong is a pointed part of something like a fork, hook, or tool.",
        ),
        QAItem(
            question="What does it mean when a ghost story has a moral value?",
            answer="It means the story shows a lesson about how to act kindly, bravely, or fairly.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes in an important way, like a scared ghost becoming gentle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.spectral:
            bits.append("spectral=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a prong, moral value, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.action is None or c[1] == args.action)
        and (args.artifact is None or c[2] == args.artifact)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, action, artifact = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, artifact=artifact, child_name=child_name, ghost_name=ghost_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
    StoryParams(place="attic", action="search", artifact="prong", child_name="Mina", ghost_name="Wisp", trait="curious"),
    StoryParams(place="cellar", action="listen", artifact="bell", child_name="Owen", ghost_name="Murk", trait="quiet"),
    StoryParams(place="graveyard", action="hide", artifact="latch", child_name="Tia", ghost_name="Pale Tom", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
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
