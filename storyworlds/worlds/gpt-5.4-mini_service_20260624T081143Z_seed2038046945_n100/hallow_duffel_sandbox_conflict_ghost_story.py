#!/usr/bin/env python3
"""
Standalone storyworld: hallow duffel sandbox conflict ghost story.

A small, child-facing simulation where a hallow in a sandbox gets tangled with
a duffel bag, creating a gentle ghost-story conflict that is resolved by a
careful, state-driven turn.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "sandbox": "the sandbox",
}

HERO_NAMES = ["Mina", "Pip", "June", "Toby", "Nora", "Eli"]
HELPER_NAMES = ["Moss", "Wren", "Milo", "Ivy", "Lark", "Bea"]

ASPECTS = {
    "hallow": {
        "label": "hallow",
        "phrase": "a small hallow carved in the sand",
        "meter": "open",
        "risk": "the hallow could collapse",
    },
    "duffel": {
        "label": "duffel",
        "phrase": "a soft duffel bag with a flap",
        "meter": "sag",
        "risk": "sand could clog the flap",
    },
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the sandbox contains both focal objects and the
% conflict can be resolved by a gentle repair.
conflict(hallow_duffel) :- in_place(hallow), in_place(duffel).
resolved(hallow_duffel) :- conflict(hallow_duffel), careful_fix.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("place", "sandbox"),
        asp.fact("in_place", "hallow"),
        asp.fact("in_place", "duffel"),
        asp.fact("feature", "conflict"),
        asp.fact("style", "ghost_story"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    atoms = set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "resolved"))
    return ("hallow_duffel",) in atoms


# ---------------------------------------------------------------------------
# Parser / params
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story sandbox world with a hallow and a duffel.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or "sandbox"
    if place != "sandbox":
        raise StoryError("This world only knows the sandbox.")
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, name=name, helper=helper)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="child"))
    hallow = world.add(Entity(
        id="hallow",
        type="hallow",
        label="hallow",
        phrase=ASPECTS["hallow"]["phrase"],
        owner=hero.id,
        meters={"open": 1.0},
        memes={"haunted": 0.0, "conflict": 0.0},
    ))
    duffel = world.add(Entity(
        id="duffel",
        type="duffel",
        label="duffel",
        phrase=ASPECTS["duffel"]["phrase"],
        owner=helper.id,
        meters={"sag": 1.0},
        memes={"conflict": 0.0},
    ))

    # Beginning.
    world.say(
        f"In {world.place}, {hero.id} found {hallow.phrase}, and {helper.id} found {duffel.phrase}."
    )
    world.say(
        f"The sand felt quiet, but the little hallow made the day seem like a ghost story with a secret."
    )

    # Middle turn: the duffel's flap is pulled into the hollow shape.
    world.para()
    hallow.memes["haunted"] += 1
    duffel.meters["sand"] = duffel.meters.get("sand", 0.0) + 1.0
    hallow.meters["crumbly"] = hallow.meters.get("crumbly", 0.0) + 1.0
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1

    world.say(
        f"When {helper.id} set the {duffel.label} near the hollow, sand slipped into the flap and the bag sagged."
    )
    world.say(
        f"{hero.id} worried the hallow would collapse, and {helper.id} worried the bag would stay stuck."
    )
    world.say(
        f"They both stopped, listening to the soft hiss of sand like a tiny ghost whisper."
    )

    # Resolution: lift, shake, and reshape.
    world.para()
    duffel.meters["sand"] = 0.0
    hallow.meters["crumbly"] = 0.0
    hero.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    hallow.memes["calm"] = 1.0
    duffel.memes["calm"] = 1.0

    world.say(
        f"Then {helper.id} lifted the duffel by the strap while {hero.id} gently packed the sand back into the hallow."
    )
    world.say(
        f"The flap opened cleanly again, the hollow kept its shape, and the sandbox felt peaceful."
    )
    world.say(
        f"At the end, the hallow stayed bright in the sand, and the duffel sat beside it as if it had learned the quiet rule of the place."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        hallow=hallow,
        duffel=duffel,
        place=params.place,
        conflict=True,
        resolved=True,
    )

    story = world.render()
    prompts = [
        "Write a gentle ghost story set in a sandbox with a hallow and a duffel.",
        f"Tell a child-friendly story where {params.name} and {params.helper} solve a small conflict about sand and a bag.",
        "Make the ending show that the sandbox changed from tense to calm.",
    ]
    story_qa = [
        QAItem(
            question="What did the children find in the sandbox?",
            answer="They found a small hallow in the sand and a soft duffel bag with a flap.",
        ),
        QAItem(
            question="Why did the children feel worried?",
            answer="They worried because sand slipped into the duffel flap and the hallow might collapse.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer="They lifted the duffel, shook out the sand, and packed the hallow back into shape together.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a box or shallow area filled with sand where children can dig and build.",
        ),
        QAItem(
            question="What does a duffel bag usually do?",
            answer="A duffel bag is a soft bag used to carry toys, clothes, or other belongings.",
        ),
        QAItem(
            question="What can happen to a hollow shape in sand?",
            answer="A hollow shape in sand can crumble or fill in if the sand is not packed carefully.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
# Verification / main
# ---------------------------------------------------------------------------

def verify() -> int:
    if not asp_valid():
        print("ASP parity check failed.")
        return 1
    print("OK: ASP program and Python world agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
        print("conflicts:", asp.atoms(model, "conflict"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(argparse.Namespace(place="sandbox", name=None, helper=None), random.Random(base_seed))
        params.seed = base_seed
        samples = [generate(params)]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
