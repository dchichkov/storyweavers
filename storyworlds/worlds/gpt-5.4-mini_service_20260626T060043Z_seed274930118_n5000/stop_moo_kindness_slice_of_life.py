#!/usr/bin/env python3
"""
storyworlds/worlds/stop_moo_kindness_slice_of_life.py
======================================================

A small slice-of-life storyworld about a child, a noisy moo, and a kinder way
to solve the problem.

Seed tale:
---
On a quiet afternoon, a child hears a cow mooing from the yard. The sound is so
loud that the child wants it to stop. A parent notices that the cow is not being
naughty; it is calling for help. Together they walk over, find the little calf
near the fence, and open the gate so the two can be together again. The mooing
softens, the child feels proud of being kind, and the day becomes calm again.

This script turns that premise into a tiny simulated world with meters and
memes, grounded narration, QA, JSON output, and a clingo-backed reasonableness
gate.
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
MOO_KEYS = {"moo", "noise", "worry", "kindness", "calm"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    paired_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool = False
    has_gate: bool = False
    has_barn: bool = False


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def finish_moo(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cow = world.get("cow")
    calf = world.get("calf")
    if child.meters.get("helped", 0) < THRESHOLD:
        return out
    if cow.meters.get("calm", 0) < THRESHOLD:
        return out
    sig = ("quieted",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The noisy moo faded into a soft, happy sound.")
    out.append(f"{cow.noun().capitalize()} leaned toward {calf.noun()} and the yard grew peaceful again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (finish_moo,):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "farmyard": Setting(place="the farmyard", outdoors := False if False else False, has_gate=True, has_barn=True),
    "porch": Setting(place="the porch", indoors=False, has_gate=True, has_barn=False),
    "lane": Setting(place="the lane beside the fence", indoors=False, has_gate=True, has_barn=True),
}


def setting_detail(setting: Setting) -> str:
    if setting.place == "the porch":
        return "The porch was warm, and the afternoon air moved slowly through the yard."
    if setting.place == "the lane beside the fence":
        return "The fence line was quiet except for one worried moo drifting over the grass."
    return "The farmyard looked ordinary, with little patches of grass and a gate that could be opened by hand."


def reasonableness(place: str) -> bool:
    return place in SETTINGS


def explain_rejection(place: str) -> str:
    return f"(No story: the setting {place!r} does not fit this small cow-and-kindness scene.)"


def seed_child_name(rng: random.Random, child_type: str) -> str:
    girls = ["Maya", "Nina", "Lila", "June", "Ruby", "Iris"]
    boys = ["Owen", "Milo", "Eli", "Theo", "Noah", "Finn"]
    return rng.choice(girls if child_type == "girl" else boys)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(
        id="child", kind="character", type=params.child_type, label=params.child_name,
        traits=["little", params.trait],
        memes={"worry": 0.0, "kindness": 0.0, "pride": 0.0, "calm": 0.0},
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=params.parent_type, label=params.parent_type,
        memes={"patience": 1.0, "kindness": 1.0, "calm": 1.0},
    ))
    cow = world.add(Entity(
        id="cow", kind="character", type="cow", label="the cow",
        memes={"worry": 0.0, "noise": 0.0, "calm": 0.0},
    ))
    calf = world.add(Entity(
        id="calf", kind="character", type="calf", label="the calf",
        memes={"worry": 0.0, "calm": 0.0},
    ))
    gate = world.add(Entity(
        id="gate", kind="thing", type="gate", label="the gate",
        phrase="a little gate",
        meters={"open": 0.0},
    ))

    # Act 1: setup.
    world.say(f"{child.label} was a little {params.trait} {params.child_type} who liked quiet afternoons.")
    world.say(f"{child.label} also liked when the day felt calm enough to hear birds and footsteps.")
    world.say(f"That day, a long moo came from {world.setting.place}.")
    world.say(setting_detail(world.setting))

    # Act 2: the noise is noticed, and kindness changes the plan.
    world.para()
    child.meters["attention"] = 1.0
    child.memes["worry"] += 1.0
    cow.meters["moo"] = 1.0
    cow.memes["noise"] += 1.0
    world.say(f"{child.label} covered {child.pronoun('possessive')} ears and said, \"Please stop the moo!\"")
    world.say(f"{parent.label} looked toward the sound and shook {parent.pronoun('possessive')} head a little. "
              f"\"Maybe the cow is not trying to be loud,\" {parent.pronoun()} said. \"Maybe it needs help.\"")
    world.say(f"{child.label} listened again, this time more carefully, and the moo sounded worried instead of naughty.")
    world.say(f"They walked over together, hand in hand, following the sound to the fence.")

    # Act 3: the cause is found and solved kindly.
    world.para()
    calf.memes["worry"] += 1.0
    world.say(f"Near the fence, they found {calf.noun()} waiting by itself, looking small and lost.")
    world.say(f"{child.label} saw that the cow was calling the calf.")
    world.say(f"{child.label} helped {parent.pronoun('object')} open the gate, and {parent.pronoun()} guided {calf.noun()} through it.")
    gate.meters["open"] = 1.0
    cow.paired_with = calf.id
    calf.paired_with = cow.id
    child.meters["helped"] = 1.0
    child.memes["kindness"] += 1.0
    child.memes["pride"] += 1.0
    cow.memes["calm"] += 1.0
    calf.memes["calm"] += 1.0
    world.say(f"The cow nuzzled the calf, and the calf answered with a tiny, happy nudge.")
    propagate(world, narrate=True)
    world.say(f"{child.label} smiled, because kindness had done what shouting could not.")
    world.say(f"The yard was still again, except for one soft moo that now sounded like thanks.")

    world.facts.update(
        child=child,
        parent=parent,
        cow=cow,
        calf=calf,
        gate=gate,
        place=params.place,
        trait=params.trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a gentle slice-of-life story about a child named {child.label} who hears a moo and learns kindness.',
        f'Tell a short story where someone wants to stop a moo, but the real answer is to help the cow.',
        f'Write a calm, child-friendly story set at {f["place"]} that ends with the moo becoming soft and happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cow = f["cow"]
    calf = f["calf"]
    place = f["place"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Why did {child.label} want the moo to stop?",
            answer=f"{child.label} wanted the moo to stop because it was loud and made the quiet afternoon feel interrupted.",
        ),
        QAItem(
            question=f"What did {parent.label} think the cow might need?",
            answer=f"{parent.label} thought the cow might need help instead of scolding, because the sound felt worried.",
        ),
        QAItem(
            question=f"What did {child.label} and {parent.label} find near the fence?",
            answer=f"They found {calf.noun()} waiting by the fence, and that showed why {cow.noun()} had been mooing.",
        ),
        QAItem(
            question=f"How did {child.label} help at {place}?",
            answer=f"{child.label} helped open the gate and let the calf go through, which was a kind thing to do.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} felt proud and calm, because being {trait} meant helping instead of only complaining.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moo?",
            answer="A moo is the sound a cow makes.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, caring, and being gentle with someone else.",
        ),
        QAItem(
            question="Why might a cow moo loudly?",
            answer="A cow might moo loudly if it is calling for another animal or wants help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    parts.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
% If the cow is mooing and the calf is separate, there is a problem worth solving.
worry(cow) :- mooing(cow), separated(cow, calf).

% A kind solution is to reunite the cow and calf through an open gate.
kind_fix(cow) :- worry(cow), gate_open, reunited(cow, calf).

% A valid story needs the moo, the worry, and the kindness turn.
valid_story(P) :- setting(P), mooing(cow), kind_fix(cow).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        if setting.has_gate:
            lines.append(asp.fact("gate_setting", sid))
        if setting.has_barn:
            lines.append(asp.fact("barn_setting", sid))
    lines.append(asp.fact("mooing", "cow"))
    lines.append(asp.fact("separated", "cow", "calf"))
    lines.append(asp.fact("reunited", "cow", "calf"))
    lines.append(asp.fact("gate_open"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def validate_python() -> list[str]:
    return [sid for sid in SETTINGS if reasonableness(sid)]


def asp_verify() -> int:
    py = set(validate_python())
    cl = {p[0] for p in asp_valid_places()}
    if py == cl:
        print(f"OK: ASP gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: stop the moo with kindness.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["calm", "curious", "gentle", "shy", "brave"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    if not reasonableness(place):
        raise StoryError(explain_rejection(place))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or seed_child_name(rng, gender)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["calm", "curious", "gentle", "shy", "brave"])
    return StoryParams(place=place, child_name=child_name, child_type=gender, parent_type=parent_type, trait=trait)


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


CURATED = [
    StoryParams(place="farmyard", child_name="Maya", child_type="girl", parent_type="mother", trait="curious"),
    StoryParams(place="porch", child_name="Owen", child_type="boy", parent_type="father", trait="gentle"),
    StoryParams(place="lane", child_name="Lila", child_type="girl", parent_type="mother", trait="calm"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_places())} valid places:\n")
        for item in asp_valid_places():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
