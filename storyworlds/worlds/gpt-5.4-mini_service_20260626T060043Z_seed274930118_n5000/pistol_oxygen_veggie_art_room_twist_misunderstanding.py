#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pistol_oxygen_veggie_art_room_twist_misunderstanding.py
==============================================================================================================================

A small whodunit-style story world in an art room.

Seed inspiration:
- pistol
- oxygen
- veggie
- Twist
- Misunderstanding
- Kindness

Premise:
A child's art room mystery begins with a strange-looking paint pistol, an oxygen tank for bubble art,
and a veggie print tray. A misunderstanding makes the wrong person look suspicious. A twist reveals
the real cause, and kindness repairs the room and the feelings in it.

The world is intentionally small and constraint-checked:
- The art room must support the mystery tools.
- The story must feature a believable clue trail.
- The resolution must come from a true twist, not from arbitrary narration.
- Invalid explicit combinations raise StoryError.

The prose engine simulates a live world with physical meters and emotional memes.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the art room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    clue: str
    mess: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    culprit: str
    object: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


SETTING = Setting(place="the art room", affords={"paint_pistol", "oxygen_bubbles", "veggie_prints"})

TOOLS = {
    "paint_pistol": Tool(
        id="paint_pistol",
        label="paint pistol",
        phrase="a bright little paint pistol",
        clue="the paint mist",
        mess="splatter",
        effect="sprayed dots across the paper",
        tags={"pistol", "twist"},
    ),
    "oxygen_bubbles": Tool(
        id="oxygen_bubbles",
        label="oxygen bubble tube",
        phrase="a careful oxygen tube for bubble art",
        clue="the fizzing bubbles",
        mess="foam",
        effect="made silver bubbles in the paint cup",
        tags={"oxygen", "twist"},
    ),
    "veggie_prints": Tool(
        id="veggie_prints",
        label="veggie stamp tray",
        phrase="a veggie stamp tray with carved carrots and peas",
        clue="the green prints",
        mess="smear",
        effect="left leafy marks on the paper",
        tags={"veggie", "misunderstanding"},
    ),
}

GENDER_NAMES = {
    "girl": ["Mia", "Nora", "Ava", "Zoe", "Luna", "Ivy"],
    "boy": ["Leo", "Ben", "Max", "Finn", "Noah", "Owen"],
}

TRAITS = ["curious", "gentle", "clever", "careful", "brave"]

CURATED = [
    StoryParams(setting="art_room", culprit="paint_pistol", object="veggie_prints", helper="oxygen_bubbles",
                name="Mia", gender="girl", parent="mother", trait="curious"),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting == "art_room" and params.culprit in TOOLS and params.object in TOOLS and params.helper in TOOLS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this world only works in the art room with the pistol, oxygen, and veggie clues linked together.)"


def build_world(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError(explain_rejection(params))

    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    helper = world.add(Entity(id="Helper", kind="character", type="teacher", label="Ms. Plum"))
    culprit = world.add(Entity(id=params.culprit, type="thing", label=TOOLS[params.culprit].label, phrase=TOOLS[params.culprit].phrase))
    obj = world.add(Entity(id=params.object, type="thing", label=TOOLS[params.object].label, phrase=TOOLS[params.object].phrase))
    air = world.add(Entity(id=params.helper, type="thing", label=TOOLS[params.helper].label, phrase=TOOLS[params.helper].phrase))

    world.facts.update(child=child, parent=parent, helper=helper, culprit=culprit, object=obj, air=air, params=params)
    return world


def _do_setup(world: World) -> None:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]

    world.say(
        f"{child.id} was a little {p.trait} {p.gender} who loved the art room because it was full of color, paper, and secrets."
    )
    world.say(
        f"One morning, {child.pronoun('possessive')} {parent.type} brought {child.id} to {world.setting.place}, where Ms. Plum had set out a paint pistol, an oxygen bubble tube, and a veggie stamp tray."
    )
    world.say(
        f"{child.id} wanted to use every tool, but {child.pronoun('possessive')} favorite was the paint pistol because it made tiny dots that looked like stars."
    )
    world.para()
    world.say(
        f"Then something odd happened: the veggie tray tipped, the green paper got smeared, and the oxygen bubbles popped all over the table."
    )
    world.say(
        f"Because the paint pistol was still nearby, everyone had to wonder who had done it."
    )


def _investigate(world: World) -> None:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    obj = world.facts["object"]
    air = world.facts["air"]

    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1

    world.say(
        f"{child.id} looked at the clues: the paint mist, the fizzing bubbles, and the green prints from the veggie tray."
    )
    world.say(
        f"{child.id} first thought the paint pistol must be guilty, but {child.pronoun('possessive')} {parent.type} noticed the pistol's cap was still on."
    )
    world.say(
        f"That was the twist: the pistol had not fired at all."
    )
    world.say(
        f"Instead, the oxygen tube had blown a burst of bubbles, and that puff had bumped the veggie tray just enough to make it slip."
    )
    world.say(
        f"The misunderstanding grew when green paint landed on the table, because everyone assumed the shiny tool was to blame."
    )
    parent.memes["concern"] = parent.memes.get("concern", 0) + 1
    world.say(
        f"But Ms. Plum knelt down and said the room could still be gentle: 'Let's look again, together.'"
    )


def _resolution(world: World) -> None:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    obj = world.facts["object"]
    air = world.facts["air"]

    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    parent.memes["kindness"] = parent.memes.get("kindness", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    child.memes["worry"] = 0
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"{child.id} took a soft breath and said, 'I thought the paint pistol did it. I was wrong.'"
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.type} smiled, and Ms. Plum handed over a clean cloth."
    )
    world.say(
        f"Together they wiped the table, straightened the veggie tray, and set the oxygen tube safely on its hook."
    )
    world.say(
        f"Then {child.id} tested the paint pistol again, and this time it only made happy starry dots."
    )
    world.say(
        f"The art room felt warm again: no blame, just kindness, and a mystery solved."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _do_setup(world)
    _investigate(world)
    _resolution(world)
    return world


def prompt_lines(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short whodunit for a young child set in an art room using the words "pistol", "oxygen", and "veggie".',
        f"Tell a gentle mystery where {p.name} notices clues in {world.setting.place} and the answer depends on a misunderstanding and a twist.",
        f"Write a kindness-focused detective story in the art room where the wrong tool looks guilty at first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    return [
        QAItem(
            question=f"Where does {child.id}'s mystery happen?",
            answer="It happens in the art room, where the paint tools and paper are laid out for a small messy project.",
        ),
        QAItem(
            question=f"What made the story a whodunit instead of just an art scene?",
            answer="There was a mystery about which tool caused the mess, so everyone had to look at clues and solve it.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer="The twist was that the paint pistol was not guilty after all; the oxygen bubbles and the bumped veggie tray caused the confusion.",
        ),
        QAItem(
            question=f"How did the misunderstanding get fixed?",
            answer="The child admitted the wrong guess, and everyone cleaned up together with kindness instead of blame.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pistol in this story?",
            answer="It is a paint pistol, a toy-like art tool that makes little paint dots instead of being a weapon.",
        ),
        QAItem(
            question="Why would oxygen be in an art room?",
            answer="In this story, oxygen is part of a bubble-art tool that helps make fizzing bubbles in paint.",
        ),
        QAItem(
            question="What does veggie mean here?",
            answer="Veggie means vegetable, and the story uses a veggie stamp tray with carved shapes like carrots and peas.",
        ),
        QAItem(
            question="Why is kindness important in a mystery?",
            answer="Kindness helps people tell the truth, listen carefully, and fix a mistake without hurting anyone's feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "art_room"),
        asp.fact("affords", "art_room", "paint_pistol"),
        asp.fact("affords", "art_room", "oxygen_bubbles"),
        asp.fact("affords", "art_room", "veggie_prints"),
    ]
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("tagged", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(art_room) :- setting(art_room),
                         affords(art_room, paint_pistol),
                         affords(art_room, oxygen_bubbles),
                         affords(art_room, veggie_prints).

twist(paint_pistol) :- tagged(paint_pistol, twist).
misunderstanding(veggie_prints) :- tagged(veggie_prints, misunderstanding).
kindness(art_room) :- valid_story(art_room).
#show valid_story/1.
#show twist/1.
#show misunderstanding/1.
#show kindness/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1.\n#show twist/1.\n#show misunderstanding/1.\n#show kindness/1."))
    atoms = set((s.name, tuple(a.string if a.type == s.type.String else a.number if a.type == s.type.Number else a.name for a in s.arguments)) for s in model)
    expected = {
        ("valid_story", ("art_room",)),
        ("twist", ("paint_pistol",)),
        ("misunderstanding", ("veggie_prints",)),
        ("kindness", ("art_room",)),
    }
    if atoms == expected:
        print("OK: ASP rules match Python story gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def generation_prompts(world: World) -> list[str]:
    return prompt_lines(world)


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:14} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit set in an art room.")
    ap.add_argument("--setting", choices=["art_room"], default=None)
    ap.add_argument("--culprit", choices=list(TOOLS))
    ap.add_argument("--object", choices=list(TOOLS))
    ap.add_argument("--helper", choices=list(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or "art_room"
    culprit = args.culprit or rng.choice(list(TOOLS))
    obj = args.object or rng.choice([k for k in TOOLS if k != culprit])
    helper = args.helper or rng.choice([k for k in TOOLS if k not in {culprit, obj}])
    if len({culprit, obj, helper}) < 3:
        raise StoryError("The pistol, oxygen, and veggie clues must be three different tools.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(setting=setting, culprit=culprit, object=obj, helper=helper,
                         name=name, gender=gender, parent=parent, trait=trait)
    if not valid_story(params):
        raise StoryError(explain_rejection(params))
    return params


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
        print(asp_program("#show valid_story/1.\n#show twist/1.\n#show misunderstanding/1.\n#show kindness/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1.\n#show twist/1.\n#show misunderstanding/1.\n#show kindness/1."))
        print("\n".join(str(s) for s in model))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
