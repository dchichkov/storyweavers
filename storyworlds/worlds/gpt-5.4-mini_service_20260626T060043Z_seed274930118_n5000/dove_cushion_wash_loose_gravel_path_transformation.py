#!/usr/bin/env python3
"""
A nursery-rhyme story world about a dove, a cushion, and a wash on a loose gravel path.

Seed tale:
---
A dove found a cushion on a loose gravel path. The cushion was dusty and flat, and every
time the dove pecked at it, little stones went "crunch-crunch" underfoot. The dove wanted
to wash the cushion, but the path kept scratching it with grit. Then the dove remembered
a soft little basket by the gate from an earlier day. The dove carried the cushion there,
washed it in a basin, and watched it turn fluffy and bright. Now the dove sang a happy
"coo-coo," and the cushion rested clean and full and soft.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    transformed: bool = False
    sound: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "dove":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the loose gravel path"
    ground: str = "loose gravel"
    affords: set[str] = field(default_factory=lambda: {"wash", "flashback"})


@dataclass
class StoryParams:
    setting: str = "loose_gravel_path"
    action: str = "wash"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
# World state and causal rules
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _r_grit(world: World) -> list[str]:
    out: list[str] = []
    dove = world.get("dove")
    cushion = world.get("cushion")
    if dove.meters.get("wash", 0) >= THRESHOLD and not cushion.transformed:
        sig = ("grit",)
        if sig not in world.fired:
            world.fired.add(sig)
            cushion.meters["dusty"] = cushion.meters.get("dusty", 0) + 1
            cushion.memes["sad"] = cushion.memes.get("sad", 0) + 1
            out.append("The loose gravel went crunch-crunch, and the cushion stayed dusty.")
    return out


def _r_wash_transform(world: World) -> list[str]:
    out: list[str] = []
    dove = world.get("dove")
    cushion = world.get("cushion")
    basin = world.get("basin")
    if dove.meters.get("wash", 0) >= THRESHOLD and basin.meters.get("water", 0) >= THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            if not cushion.transformed:
                cushion.transformed = True
                cushion.meters["dusty"] = 0
                cushion.meters["clean"] = 1
                cushion.meters["fluffy"] = 1
                cushion.memes["joy"] = cushion.memes.get("joy", 0) + 1
                out.append("Wash, wash, wash—then the cushion turned clean and fluffy.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_grit, _r_wash_transform):
            got = rule(world)
            if got:
                changed = True
                lines.extend(got)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def setup_world() -> World:
    world = World(Setting())
    world.add(Entity(id="dove", kind="character", type="dove", label="dove", traits=["gentle", "small"]))
    world.add(Entity(id="cushion", type="cushion", label="cushion", phrase="a small soft cushion"))
    world.add(Entity(id="basket", type="basket", label="basket", phrase="a little basket by the gate"))
    world.add(Entity(id="basin", type="basin", label="basin", phrase="a shallow washing basin"))
    world.get("basin").meters["water"] = 1
    return world


def flashback(world: World) -> None:
    world.say(
        "And the dove remembered, like a twinkly little bell, "
        "how the basket by the gate had waited there on a brighter day."
    )
    world.facts["flashback"] = True


def sound_effects(world: World) -> None:
    world.get("dove").sound = "coo-coo"
    world.say("Coo-coo! The dove peeped at the cushion. Crunch-crunch went the gravel.")
    world.facts["sounds"] = ["coo-coo", "crunch-crunch"]


def begin_story(world: World) -> None:
    dove = world.get("dove")
    cushion = world.get("cushion")
    world.say(
        "On a loose gravel path, a little dove found a cushion. "
        "The cushion was dusty, flat, and tired-looking, and the dove wished to wash it."
    )
    world.say(
        "The dove nudged the cushion with a careful beak, and the stones answered back: crunch-crunch."
    )
    dove.memes["desire"] = 1
    cushion.meters["dusty"] = 1
    cushion.meters["flat"] = 1
    world.facts["dove"] = dove
    world.facts["cushion"] = cushion


def tension(world: World) -> None:
    dove = world.get("dove")
    cushion = world.get("cushion")
    world.say(
        "But the path was all loose gravel, and every tiny step carried more grit onto the cushion."
    )
    world.say(
        "The dove frowned a little. Washing it there would only make the soft thing sadder."
    )
    dove.memes["worry"] = 1
    cushion.memes["sad"] = cushion.memes.get("sad", 0) + 1
    world.facts["tension"] = True


def turn(world: World) -> None:
    world.say(
        "Then the dove had a bright little flash of memory."
    )
    flashback(world)
    world.say(
        "There, by the gate, stood the basin with clean water waiting quietly like a moon in a pond."
    )


def resolution(world: World) -> None:
    dove = world.get("dove")
    cushion = world.get("cushion")
    basin = world.get("basin")
    world.say(
        "The dove carried the cushion from the gravel path and set it near the basin."
    )
    world.say("Splash-swish went the water, and wash-wash went the dove's careful wings.")
    dove.meters["wash"] = 1
    propagate(world, narrate=True)
    if cushion.transformed:
        world.say(
            "Soon the cushion looked bright and fluffy, and it sat like a little cloud at rest."
        )
        world.say(
            "The dove smiled a tiny smile and sang, 'Coo-coo, coo-coo,' because the wash had done its magic."
        )
    world.facts["resolved"] = True


def build_story() -> World:
    world = setup_world()
    begin_story(world)
    world.para()
    sound_effects(world)
    tension(world)
    world.para()
    turn(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about a dove, a cushion, and a wash on a loose gravel path.',
        'Tell a gentle story where a dove wants to wash a cushion, but the gravel path makes the first try messy, so a memory helps solve it.',
        'Write a simple rhyming story with "coo-coo" and "crunch-crunch" that ends with a cushion becoming clean and fluffy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    cushion = world.get("cushion")
    dove = world.get("dove")
    return [
        QAItem(
            question="What did the dove find on the path?",
            answer="The dove found a cushion on the loose gravel path.",
        ),
        QAItem(
            question="Why did the dove not want to wash the cushion on the path?",
            answer="The path was loose gravel, so the tiny stones kept adding grit and made the cushion stay dusty.",
        ),
        QAItem(
            question="What helped the dove remember a better way?",
            answer="The dove remembered the little basket by the gate and the basin with clean water nearby.",
        ),
        QAItem(
            question="What changed after the wash?",
            answer="The cushion turned clean and fluffy instead of dusty and flat.",
        ),
        QAItem(
            question="How did the dove feel at the end?",
            answer="The dove felt happy and sang softly, because the cushion was clean and bright again.",
        ),
        QAItem(
            question="What sound was heard on the loose gravel path?",
            answer=f"The gravel went crunch-crunch, and the dove made a soft {dove.sound} sound.",
        ),
        QAItem(
            question="What did the cushion become after the transformation?",
            answer="It became a clean, fluffy cushion that looked like a little cloud at rest.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dove": [
        QAItem(
            question="What is a dove?",
            answer="A dove is a small bird with soft feathers and a gentle cooing voice.",
        )
    ],
    "cushion": [
        QAItem(
            question="What is a cushion for?",
            answer="A cushion is soft and squishy, and people or animals can rest on it for comfort.",
        )
    ],
    "wash": [
        QAItem(
            question="What does wash mean?",
            answer="To wash something means to clean it with water, and sometimes with gentle soap too.",
        )
    ],
    "gravel": [
        QAItem(
            question="What is loose gravel?",
            answer="Loose gravel is made of small stones that roll and crunch underfoot.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another, like dusty becoming clean and fluffy.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        )
    ],
    "sound": [
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help you hear the action in your head and make the story feel lively.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["dove", "cushion", "wash", "gravel", "transformation", "flashback", "sound"]:
        out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A wash is reasonable in this tiny world.
valid_story(loose_gravel_path,wash,dove_cushion) :- setting(loose_gravel_path), action(wash), object(dove_cushion).

% The story includes a flashback and a transformation whenever the wash happens.
includes_flashback(loose_gravel_path,wash,dove_cushion) :- valid_story(loose_gravel_path,wash,dove_cushion).
includes_transformation(loose_gravel_path,wash,dove_cushion) :- valid_story(loose_gravel_path,wash,dove_cushion).

#show valid_story/3.
#show includes_flashback/3.
#show includes_transformation/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "loose_gravel_path"),
            asp.fact("action", "wash"),
            asp.fact("object", "dove_cushion"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("loose_gravel_path", "wash", "dove_cushion")}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP and Python agree on the valid story.")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a dove, a cushion, and a wash.")
    ap.add_argument("--setting", choices=["loose_gravel_path"], default="loose_gravel_path")
    ap.add_argument("--action", choices=["wash"], default="wash")
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
    if args.setting != "loose_gravel_path" or args.action != "wash":
        raise StoryError("This tiny world only supports a wash on the loose gravel path.")
    return StoryParams(setting=args.setting, action=args.action, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = build_story()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.transformed:
            bits.append("transformed=True")
        if ent.sound:
            bits.append(f"sound={ent.sound}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(setting="loose_gravel_path", action="wash", seed=base_seed)
        samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
