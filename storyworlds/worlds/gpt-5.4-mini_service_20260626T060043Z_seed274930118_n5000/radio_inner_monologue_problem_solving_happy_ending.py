#!/usr/bin/env python3
"""
A small storyworld about a folk-tale radio that goes quiet, a worried child,
careful problem solving, and a happy ending.

The seed idea:
---
A child loves listening to a little radio by the hearth. One evening, the song
stops just when a storyteller begins. The child listens to their own inner
monologue, notices the loose battery lid, and fixes the problem with a helper.
The radio sings again, and the room ends warm and bright.

This world models:
- a child and a radio as typed entities
- physical meters: battery, dust, noise, signal, warmth
- emotional memes: worry, hope, confidence, delight
- inner monologue as authored self-talk
- problem-solving steps that change the world state
- a folk-tale style happy ending image

It also includes:
- validation of reasonable story choices
- an inline ASP twin for the same compatibility logic
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
# Content registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    label: str
    indoors: bool
    mood: str
    details: str


@dataclass(frozen=True)
class RadioKind:
    id: str
    label: str
    phrase: str
    power: str
    sound: str
    problem: str
    fix: str
    requires: set[str]
    can_fix: set[str]


@dataclass(frozen=True)
class HelperKind:
    id: str
    label: str
    skill: str
    tool: str
    grants: set[str]


@dataclass(frozen=True)
class ChildKind:
    id: str
    label: str
    trait: str
    gender: str


PLACES = {
    "hearth_room": Place(
        id="hearth_room",
        label="the hearth room",
        indoors=True,
        mood="cozy",
        details="A small fire glowed in the hearth, and the window held the last gold of evening.",
    ),
    "cottage_window": Place(
        id="cottage_window",
        label="the cottage window",
        indoors=True,
        mood="quiet",
        details="The cottage was quiet except for the soft tick of a clock and the hush of wind outside.",
    ),
}

RADIOS = {
    "wooden_radio": RadioKind(
        id="wooden_radio",
        label="a little wooden radio",
        phrase="a little wooden radio with a brass dial",
        power="batteries",
        sound="music and stories",
        problem="the song went faint and then stopped",
        fix="fresh batteries and a firm twist of the knob",
        requires={"battery", "signal"},
        can_fix={"battery", "antenna"},
    ),
    "roadside_radio": RadioKind(
        id="roadside_radio",
        label="an old roadside radio",
        phrase="an old roadside radio with a curved handle",
        power="batteries",
        sound="folk songs and tale-songs",
        problem="the voice crackled and vanished",
        fix="a clean battery contact and a careful tune to the dial",
        requires={"battery", "signal"},
        can_fix={"battery", "dial"},
    ),
}

HELPERS = {
    "grandmother": HelperKind(
        id="grandmother",
        label="Grandmother",
        skill="knowing how to mend little household things",
        tool="a small cloth and a tin of spare batteries",
        grants={"battery", "care"},
    ),
    "neighbor": HelperKind(
        id="neighbor",
        label="the neighbor",
        skill="finding loose parts and setting them right",
        tool="a pencil and a tiny screwdriver",
        grants={"antenna", "dial"},
    ),
}

CHILDREN = {
    "mila": ChildKind(id="Mila", label="Mila", trait="patient", gender="girl"),
    "rowan": ChildKind(id="Rowan", label="Rowan", trait="curious", gender="boy"),
    "nori": ChildKind(id="Nori", label="Nori", trait="gentle", gender="girl"),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    radio: str
    child: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def radio_can_be_fixed(radio: RadioKind, helper: HelperKind) -> bool:
    return bool(radio.can_fix & helper.grants)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for radio in RADIOS:
            for helper in HELPERS:
                if radio_can_be_fixed(RADIOS[radio], HELPERS[helper]):
                    combos.append((place, radio, helper))
    return combos


def explain_rejection(radio: RadioKind, helper: HelperKind) -> str:
    return (
        f"(No story: {helper.label} does not have the right kind of help to fix "
        f"{radio.label}. This world needs a helper who can solve the radio's trouble "
        f"in a believable way.)"
    )


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
radio_fixable(R, H) :- radio(R), helper(H), can_fix(R, G), grants(H, G).
valid(Place, R, H) :- place(Place), radio(R), helper(H), radio_fixable(R, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for rid, r in RADIOS.items():
        lines.append(asp.fact("radio", rid))
        for req in sorted(r.requires):
            lines.append(asp.fact("requires", rid, req))
        for g in sorted(r.can_fix):
            lines.append(asp.fact("can_fix", rid, g))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for g in sorted(h.grants):
            lines.append(asp.fact("grants", hid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def inner_monologue(child: Entity, radio: Entity) -> str:
    return (
        f"{child.id} thought, “Don't fret. A quiet radio is not a broken heart. "
        f"If I listen closely, I may hear what has gone wrong with {radio.pronoun('possessive')} song.”"
    )


def introduce(world: World, child: Entity, radio: Entity) -> None:
    world.say(
        f"Once, in {world.place.label}, there lived {child.id}, a {child.memes['trait_word']} child "
        f"who loved {radio.label} more than porridge on a cold morning."
    )
    world.say(
        f"Every night, {radio.label} told music and stories, and the room felt as if a small star had come indoors."
    )


def trouble(world: World, child: Entity, radio: Entity) -> None:
    radio.meters["signal"] = 0.0
    radio.meters["sound"] = 0.0
    child.memes["worry"] += 1
    child.memes["hope"] += 0.2
    world.say(
        f"But one evening, just as the storyteller began, {radio.label} {RADIOS[world.facts['radio_kind']].problem}."
    )
    world.say(inner_monologue(child, radio))


def inspect(world: World, child: Entity, radio: Entity) -> None:
    radio.meters["dust"] += 0.2
    world.say(
        f"{child.id} knelt beside the little set and looked with careful eyes. "
        f"The dial was still, and the battery lid felt loose."
    )
    world.say(
        f"{child.id} thought, “Aha. The radio is not forsaken; it is only asking for patient hands.”"
    )


def solve(world: World, child: Entity, helper: Entity, radio: Entity) -> None:
    kind: RadioKind = world.facts["radio_obj"]
    helper_kind: HelperKind = world.facts["helper_obj"]

    if "battery" in helper_kind.grants:
        radio.meters["battery"] = 1.0
        world.say(
            f"{helper.label} came with {helper_kind.tool}, lifted the lid, and slipped in fresh batteries."
        )
    if "antenna" in helper_kind.grants or "dial" in helper_kind.grants:
        radio.meters["signal"] = 1.0
        world.say(
            f"Then {child.id} gave the knob a gentle turn while {helper.label} steadied the set."
        )

    radio.meters["sound"] = 1.0
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["confidence"] += 1.0
    child.memes["delight"] += 1.0
    world.say(
        f"At once, the music returned, clear as a brook over stones, because the fix was just the right one for {kind.label}."
    )


def ending(world: World, child: Entity, radio: Entity) -> None:
    world.say(
        f"That night, {radio.label} sang again beside the hearth, and {child.id} listened with a warm smile."
    )
    world.say(
        f"The little room glowed with firelight and song, and even the shadows seemed to sit down and listen politely."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child_kind = CHILDREN[params.child]
    helper_kind = HELPERS[params.helper]
    radio_kind = RADIOS[params.radio]

    child = world.add(Entity(
        id=child_kind.id,
        kind="character",
        type=child_kind.gender,
        label=child_kind.id,
        meters={"body": 1.0},
        memes={"trait_word": 1.0, "worry": 0.0, "hope": 0.0, "confidence": 0.0, "delight": 0.0},
    ))
    child.memes["trait_word"] = 1.0
    helper = world.add(Entity(
        id=helper_kind.label,
        kind="character",
        type="grandmother" if helper_kind.id == "grandmother" else "helper",
        label=helper_kind.label,
        memes={"care": 1.0},
    ))
    radio = world.add(Entity(
        id=radio_kind.label,
        kind="thing",
        type="radio",
        label=radio_kind.label,
        phrase=radio_kind.phrase,
        owner=child.id,
        meters={"battery": 0.5, "signal": 1.0, "sound": 1.0, "dust": 0.0},
    ))

    world.facts["radio_kind"] = radio_kind.id
    world.facts["radio_obj"] = radio_kind
    world.facts["helper_obj"] = helper_kind
    world.facts["child_obj"] = child_kind

    introduce(world, child, radio)
    world.para()
    trouble(world, child, radio)
    inspect(world, child, radio)
    world.para()
    solve(world, child, helper, radio)
    ending(world, child, radio)

    world.facts.update(
        child=child,
        helper=helper,
        radio=radio,
        place=place,
        resolved=radio.meters["sound"] >= 1.0,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: ChildKind = f["child_obj"]
    helper: HelperKind = f["helper_obj"]
    radio: RadioKind = f["radio_obj"]
    place: Place = f["place"]
    return [
        f"Write a folk-tale style story about {child.id}, a child who loves {radio.label}, and a small problem that gets solved kindly.",
        f"Tell a gentle story in {place.label} where {helper.label} helps fix {radio.label} after the sound goes quiet.",
        f"Write a child-facing story with inner monologue, problem solving, and a happy ending about a radio and a careful repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    radio: Entity = f["radio"]
    radio_kind: RadioKind = f["radio_obj"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"What happened to {radio.label} in {place.label}?",
            answer=f"{radio.label} went quiet for a little while, so the story stopped sounding like music and voices.",
        ),
        QAItem(
            question=f"What did {child.id} think to themself when {radio.label} fell silent?",
            answer=(
                f"{child.id} thought that a quiet radio was not a broken heart, and that careful listening might reveal the trouble."
            ),
        ),
        QAItem(
            question=f"How was the problem with {radio.label} fixed?",
            answer=(
                f"{helper.label} and {child.id} fixed it with fresh batteries and a gentle turn of the knob, which was just right for {radio_kind.label}."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and relieved, because the radio sang again and the room felt warm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a radio for?",
            answer="A radio is a machine that can carry music, voices, and stories through the air so people can listen.",
        ),
        QAItem(
            question="Why do batteries matter in a radio?",
            answer="Batteries give a radio the power it needs to make sound when it is not plugged into the wall.",
        ),
        QAItem(
            question="What does a happy ending mean in a story?",
            answer="A happy ending means the trouble gets solved and the characters finish feeling safe, glad, or peaceful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="hearth_room", radio="wooden_radio", child="mila", helper="grandmother"),
    StoryParams(place="cottage_window", radio="roadside_radio", child="rowan", helper="neighbor"),
    StoryParams(place="hearth_room", radio="roadside_radio", child="nori", helper="grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a radio, a worry, and a happy repair.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--radio", choices=RADIOS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if args.radio and args.helper and not radio_can_be_fixed(RADIOS[args.radio], HELPERS[args.helper]):
        raise StoryError(explain_rejection(RADIOS[args.radio], HELPERS[args.helper]))
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.radio is None or c[1] == args.radio)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, radio, helper = rng.choice(sorted(filtered))
    child = args.child or rng.choice(sorted(CHILDREN))
    return StoryParams(place=place, radio=radio, child=child, helper=helper)


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


# ---------------------------------------------------------------------------
# CLI / ASP
# ---------------------------------------------------------------------------

def asp_program_text() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text() + '\n#show valid/3.\n')
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_text() + "\n#show valid/3.\n")
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, radio, helper) combos:\n")
        for place, radio, helper in triples:
            print(f"  {place:12} {radio:16} {helper}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} / {p.radio} / {p.helper} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
