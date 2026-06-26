#!/usr/bin/env python3
"""
A small detective-style storyworld set in a dining room.

Premise:
A child detective notices a surprise at the dining table: fifty paper stars
have been scattered, and a prize plant on the sideboard is starting to shrivel.
The detective and a helper form a tiny alliance to find who moved the water
glass, protect the plant, and restore order before dinner.

The story is state-driven:
- surprise raises alert and curiosity
- a missing or tipped glass lowers plant moisture
- shriveling progresses when moisture is too low
- an alliance with a helper increases confidence and cooperation
- the ending proves the room changed: the clue is solved, the plant is saved,
  and the dinner room is calm again.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dining room"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str = "thing"


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    clue: str


@dataclass
class World:
    setting: Setting
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _narrate_state(world: World, text: str) -> None:
    world.say(text)


def detect_surprise(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["alert"] = detective.memes.get("alert", 0.0) + 1
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    _narrate_state(
        world,
        f"In the dining room, {detective.id} noticed a surprise: {clue.phrase}."
    )


def count_fifty(world: World, clue: Clue) -> None:
    world.facts["fifty"] = 50
    _narrate_state(
        world,
        "There were fifty paper stars on the floor, and that was one clue too many to ignore."
    )


def plant_starts_shrivel(world: World, plant: Entity) -> None:
    plant.meters["moisture"] = plant.meters.get("moisture", 0.0) - 1
    plant.meters["shrivel"] = plant.meters.get("shrivel", 0.0) + 1
    _narrate_state(
        world,
        f"The little plant on the sideboard began to shrivel at the edges."
    )


def form_alliance(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["trust"] = detective.memes.get("trust", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    detective.memes["alliance"] = detective.memes.get("alliance", 0.0) + 1
    helper.memes["alliance"] = helper.memes.get("alliance", 0.0) + 1
    _narrate_state(
        world,
        f"{detective.id} made an alliance with {helper.id}; together they had more eyes than one."
    )


def inspect_glass(world: World, detective: Entity, helper: Entity, glass: Entity) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    helper.memes["focus"] = helper.memes.get("focus", 0.0) + 1
    if glass.meters.get("spilled", 0.0) >= THRESHOLD:
        _narrate_state(
            world,
            "They found the tipped glass under the table, and the wet ring on the cloth matched the clue."
        )
    else:
        _narrate_state(
            world,
            "They checked the table carefully, but the glass still stood steady."
        )


def fix_the_room(world: World, detective: Entity, helper: Entity, plant: Entity, glass: Entity) -> None:
    if glass.meters.get("spilled", 0.0) >= THRESHOLD:
        glass.meters["spilled"] = 0.0
        plant.meters["moisture"] = plant.meters.get("moisture", 0.0) + 2
        plant.meters["shrivel"] = max(0.0, plant.meters.get("shrivel", 0.0) - 1)
        detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
        helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
        _narrate_state(
            world,
            f"With careful hands, they righted the glass, watered the plant, and the shriveled leaves perked up again."
        )


@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    suspect_name: str
    seed: Optional[int] = None


DETECTIVE_NAMES = ["Maya", "Leo", "Nina", "Owen", "Iris", "Eli"]
HELPER_NAMES = ["Aunt June", "Dad", "Milo", "Grandma", "Nora"]
SUSPECT_NAMES = ["the cat", "the wind", "the clumsy spoon", "the puppy", "the draft"]


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    detective = world.add(Entity(id=params.detective_name, kind="character", type="girl" if params.detective_name in {"Maya", "Nina", "Iris"} else "boy"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="woman" if "Aunt" in params.helper_name or "Grandma" in params.helper_name or params.helper_name == "Nora" else "man"))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label="potted plant", phrase="a potted plant on the sideboard", caretaker=helper.id))
    glass = world.add(Entity(id="glass", kind="thing", type="glass", label="water glass", phrase="a tipped water glass", caretaker=helper.id))
    stars = world.add(Entity(id="stars", kind="thing", type="stars", label="paper stars", phrase="fifty paper stars", plural=True))
    suspect = world.add(Entity(id="suspect", kind="thing", type="suspect", label=params.suspect_name, phrase=params.suspect_name))

    glass.meters["spilled"] = 1.0
    plant.meters["moisture"] = 0.0
    plant.meters["shrivel"] = 1.0

    detect_surprise(world, detective, stars)
    count_fifty(world, stars)
    plant_starts_shrivel(world, plant)

    world.para()
    form_alliance(world, detective, helper)
    _narrate_state(
        world,
        f"{detective.id} studied the room like a real detective and guessed that {suspect.label} might have bumped the glass."
    )
    inspect_glass(world, detective, helper, glass)
    fix_the_room(world, detective, helper, plant, glass)

    world.para()
    detective.memes["solve"] = 1.0
    world.say(
        f"By dinner, the table was dry, the plant stood straighter, and {detective.id} and {helper.id} shared a pleased nod."
    )
    world.say(
        f"The surprise had become a solved case, and the dining room felt calm again."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        plant=plant,
        glass=glass,
        stars=stars,
        suspect=suspect,
        place="the dining room",
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly detective story set in a dining room with a surprise, fifty clues, and a tiny alliance.',
        f"Tell a short mystery where {f['detective'].id} and {f['helper'].id} form an alliance to solve why {f['plant'].phrase} is shrinking.",
        "Write a gentle detective tale in which fifty paper stars help reveal who tipped the water glass in the dining room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    h = world.facts["helper"]
    p = world.facts["plant"]
    g = world.facts["glass"]
    s = world.facts["suspect"]
    return [
        QAItem(
            question=f"What surprise did {d.id} find in the dining room?",
            answer="They found fifty paper stars scattered on the floor, which made the room feel like a mystery right away.",
        ),
        QAItem(
            question=f"Why did {d.id} and {h.id} make an alliance?",
            answer=f"They made an alliance so they could solve the case together, find the tipped glass, and help the shriveling plant.",
        ),
        QAItem(
            question=f"What was making {p.label} shrivel?",
            answer="The plant was shriveling because its water glass had been tipped and it needed care again.",
        ),
        QAItem(
            question=f"Who did {d.id} think bumped the glass?",
            answer=f"{d.id} guessed that {s.label} might have bumped the glass, though the important part was checking the clue and fixing the room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alliance?",
            answer="An alliance is a group agreement to help each other reach a goal, like solving a problem together.",
        ),
        QAItem(
            question="What does shrivel mean?",
            answer="To shrivel means to get smaller, wrinkly, or dry-looking because something needs water or care.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What does fifty mean?",
            answer="Fifty means 50, which is a lot of things to count.",
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
    out = ["--- world model ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "dining_room"),
        asp.fact("contains", "dining_room", "table"),
        asp.fact("contains", "dining_room", "sideboard"),
        asp.fact("contains", "dining_room", "floor"),
        asp.fact("clue_kind", "surprise"),
        asp.fact("count_word", "fifty"),
        asp.fact("action", "detect"),
        asp.fact("action", "form_alliance"),
        asp.fact("action", "inspect"),
        asp.fact("action", "repair"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% The detective storyworld is valid when a surprise is detected, an alliance is
% formed, shrivel is reduced, and the case is solved.
surprise_detected :- clue_kind(surprise), setting(dining_room).
alliance_formed :- action(form_alliance).
case_solved :- surprise_detected, alliance_formed, count_word(fifty).
valid_story :- case_solved.
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin confirms the storyworld is valid.")
        return 0
    print("MISMATCH: ASP twin did not confirm validity.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld set in a dining room.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
    return StoryParams(
        detective_name=args.name or rng.choice(DETECTIVE_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        suspect_name=args.suspect or rng.choice(SUSPECT_NAMES),
    )


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
    StoryParams(detective_name="Maya", helper_name="Aunt June", suspect_name="the cat"),
    StoryParams(detective_name="Leo", helper_name="Dad", suspect_name="the clumsy spoon"),
    StoryParams(detective_name="Iris", helper_name="Grandma", suspect_name="the draft"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
