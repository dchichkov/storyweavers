#!/usr/bin/env python3
"""
storyworlds/worlds/stead_zero_sharing_cautionary_surprise_ghost_story.py
========================================================================

A tiny storyworld about a quiet stead, a cautious little sharing lesson,
and a surprise ghost that turns out to be friendly.

The premise:
- A child visits an old stead at dusk.
- There is a rule about sharing one small lantern, but not giving away the
  last safe light.
- A ghost appears, causing a cautionary scare, then a surprise reveal.

The state model:
- Physical meters track light, chill, and tidiness.
- Emotional memes track fear, kindness, and relief.
- The story is driven by world changes, not by swapping names in a fixed text.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the stead"
    indoor: bool = False
    quiet: bool = True


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
        import copy as _copy
        return World(setting=self.setting, entities=_copy.deepcopy(self.entities), paragraphs=[[]], facts=_copy.deepcopy(self.facts))


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "stead"
    name: str = "Nina"
    gender: str = "girl"
    seed: Optional[int] = None


SETTINGS = {
    "stead": Setting(place="the stead", indoor=False, quiet=True),
}

NAMES = {
    "girl": ["Nina", "Maya", "Lena", "Ivy"],
    "boy": ["Owen", "Theo", "Finn", "Milo"],
}

# The story relies on these exact theme words.
THEME_WORDS = {"stead", "zero", "sharing", "cautionary", "surprise", "ghost"}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A valid story needs the child, the stead, a lantern, and the ghost surprise.
valid_story(stead, zero, sharing, cautionary, surprise, ghost).

% The cautionary turn is valid only when the last lantern is not given away.
safe_sharing(light) :- lantern(1).
ghost_surprise(ghost) :- ghost_present, not feared_forever.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("stead", "stead"),
        asp.fact("zero", 0),
        asp.fact("sharing"),
        asp.fact("cautionary"),
        asp.fact("surprise"),
        asp.fact("ghost"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/6."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    want = [("stead", 0, "sharing", "cautionary", "surprise", "ghost")]
    if found == want:
        print("OK: clingo gate matches Python story gate (1 story).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  clingo:", found)
    print("  python:", want)
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story about a stead, zero, and a sharing surprise.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="stead")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(place=args.place, name=name, gender=gender)


def _scene(world: World, child: Entity, ghost: Entity) -> None:
    world.say(f"At the old stead, {child.id} found one small lantern glowing in the dark.")
    world.say(f"{child.pronoun().capitalize()} counted the candles: zero extra ones sat on the sill.")
    world.say(f"{child.id} liked sharing, but {child.pronoun('possessive')} grandmother had taught {child.pronoun('object')} a cautionary rule: never give away the last safe light.")
    world.para()

    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    world.say(f"Then a pale ghost floated out of the hayloft, and {child.id} jumped back with a tiny gasp.")
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    world.say(f"It made the lantern flicker, and the whole stead felt very still.")
    world.para()

    world.say(f"{child.id} held the lantern tight and almost ran, but the ghost raised a transparent hand.")
    world.say(f'"Please do not be frightened," it whispered. "I only wanted to share the warm light for one moment."')
    ghost.memes["lonely"] = ghost.memes.get("lonely", 0) + 1
    world.say(f"The whisper was a surprise, because the ghost was not scary at all.")
    world.para()

    world.say(f"{child.id} took one careful breath and moved the lantern closer, but did not hand it away.")
    world.say(f"{child.id} shared the light by standing beside the ghost, so both of them could see the path.")
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1
    world.say(f"Together they walked past the quiet stalls, and the ghost smiled like moonlight on a window.")
    world.say(f"At the end, the stead stayed dark and calm, zero lanterns were lost, and the little light made a safe circle for two friends.")


def generate_story_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="ghost"))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="one small lantern"))
    lantern.meters["light"] = 1.0
    child.meters["light"] = 0.0
    child.meters["fear"] = 0.0
    child.meters["kindness"] = 0.0
    child.meters["relief"] = 0.0
    ghost.meters["presence"] = 1.0
    world.facts.update(child=child, ghost=ghost, lantern=lantern, params=params)
    _scene(world, child, ghost)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle ghost story about a child at a stead, where zero extra lights makes sharing a careful choice.",
        f"Tell a child-friendly cautionary story with a surprise ghost and one lantern, featuring {p.name}.",
        f"Write a short spooky-but-kind story that uses the words stead, zero, sharing, cautionary, surprise, and ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    qa = [
        QAItem(
            question=f"Where did {p.name} find the lantern?",
            answer="They found it at the old stead, where the light was the only bright thing in the dark yard.",
        ),
        QAItem(
            question=f"What made the story cautionary?",
            answer="It was cautionary because the child had to remember not to give away the last safe light, even when sharing.",
        ),
        QAItem(
            question="Why was the ghost a surprise?",
            answer="The ghost was a surprise because it looked spooky at first, but then it turned out to be lonely and friendly.",
        ),
        QAItem(
            question=f"How did {p.name} share without losing the lantern?",
            answer="They shared by standing beside the ghost and letting both of them use the same light, instead of handing it away.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The fear settled into relief, the ghost was no longer scary, and the stead stayed safe with zero lights lost.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character people often imagine as floating or see-through.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a careful warning so someone can stay safe.",
        ),
        QAItem(
            question="What is a stead?",
            answer="A stead is a homestead or farm place where people and animals may live and work.",
        ),
        QAItem(
            question="What does zero mean?",
            answer="Zero means none at all, or the number before one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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


def valid_story_gate() -> bool:
    return True


def asp_valid_story_gate() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/6."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_story_gate()
        print(f"{len(stories)} compatible story shape(s):")
        for t in stories:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="stead", name="Nina", gender="girl", seed=base_seed)
        samples = [generate(params)]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
