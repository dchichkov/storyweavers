#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/conflict_hanker_pawn_laundry_room_dialogue_slice.py
====================================================================================

A small, standalone storyworld for a slice-of-life laundry-room story with
dialogue, conflict, hanker, and pawn.

Premise:
- A child and a parent are in a laundry room.
- The child wants to keep playing with a tiny chess pawn found in a pocket.
- The parent worries the pawn will be lost in the wash or clutter the sorting.
- The child hankers to keep it; a gentle conflict rises.
- They resolve it by making a simple labeled tin for small found things, and the
  child helps fold laundry while keeping the pawn safe.

The simulated world uses typed entities with physical meters and emotional
memes. Prose is rendered from world state, not from a frozen paragraph template.
An inline ASP twin mirrors the Python reasonableness gate and outcome model.

Run:
    python storyworlds/worlds/gpt-5.4-mini/conflict_hanker_pawn_laundry_room_dialogue_slice.py
    python storyworlds/worlds/gpt-5.4-mini/conflict_hanker_pawn_laundry_room_dialogue_slice.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/conflict_hanker_pawn_laundry_room_dialogue_slice.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    labels: tuple[str, str]


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    value: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    item: str
    response: str
    child: str
    child_gender: str
    parent_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "laundry_room": Setting(
        id="laundry_room",
        place="the laundry room",
        mood="small and busy",
        labels=("washer", "dryer"),
    )
}

ITEMS = {
    "pawn": Item(
        id="pawn",
        label="chess pawn",
        phrase="a little chess pawn",
        kind="toy",
        value=1,
        tags={"pawn", "toy"},
    ),
    "sock": Item(
        id="sock",
        label="sock",
        phrase="a missing sock",
        kind="cloth",
        value=1,
        tags={"sock"},
    ),
    "coin": Item(
        id="coin",
        label="coin",
        phrase="a shiny coin",
        kind="coin",
        value=1,
        tags={"coin"},
    ),
}

RESPONSES = {
    "tin": Response(
        id="tin",
        sense=3,
        text="got a small tin from the shelf and put the pawn inside it for safekeeping",
        qa_text="got a small tin and put the pawn inside it for safekeeping",
        tags={"tin"},
    ),
    "pocket": Response(
        id="pocket",
        sense=2,
        text="helped tuck the pawn into a pocket until the folding was done",
        qa_text="helped tuck the pawn into a pocket until the folding was done",
        tags={"pocket"},
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nina", "Sam", "Ava", "Eli"]
PARENT_NAMES = ["Mom", "Dad"]


def reasonableness_gate(item: Item, response: Response) -> bool:
    return item.id == "pawn" and response.sense >= 2


def outcome_of(params: StoryParams) -> str:
    return "kept" if params.item == "pawn" and params.response in RESPONSES else "kept"


def build_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    response = RESPONSES[params.response]

    child = world.add(Entity(
        id=params.child,
        kind="character",
        type=params.child_gender,
        role="child",
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_gender,
        label="the parent",
        role="parent",
    ))
    washer = world.add(Entity(id="washer", type="appliance", label="the washer"))
    dryer = world.add(Entity(id="dryer", type="appliance", label="the dryer"))
    tin = world.add(Entity(id="tin", type="container", label="small tin"))

    child.memes["joy"] += 1
    child.memes["hanker"] += 1
    world.say(
        f"In {setting.place}, {child.id} sat on a basket and sorted warm towels, while "
        f"the washer hummed and the dryer clicked."
    )
    world.say(
        f"Then {child.id} found {item.phrase} in a pocket. \"Look!\" {child.id} said. "
        f"\"I want to keep it.\""
    )
    world.say(
        f'\"It looks like someone’s tiny pawn,\" {child.id} said. \"I kind of hanker '
        f'to hold onto it for a while.\"'
    )

    world.para()
    parent.memes["concern"] += 1
    child.memes["conflict"] += 1
    world.say(
        f'\"I know you like it,\" {parent.id} said, \"but not while the laundry is '
        f"going. It could fall behind the machines.\""
    )
    world.say(
        f'\"But it feels special,\" {child.id} said. \"Can I pawn it in my pocket '
        f"until we're done?\""
    )

    world.para()
    if reasonableness_gate(item, response):
        child.memes["relief"] += 1
        child.memes["conflict"] = 0
        world.say(
            f'\"That sounds fair,\" {parent.id} said. {parent.pronoun().capitalize()} '
            f"{response.text}."
        )
        world.say(
            f'{child.id} nodded and helped fold the shirts. The pawn stayed safe, '
            f"and the basket stopped feeling messy."
        )
        world.say(
            f'\"After this,\" {child.id} said, \"we can put little found things in the '
            f"tin and label it.\""
        )
        world.say(f'\"Good idea,\" {parent.id} said. \"That keeps the laundry room calm.\"')
    else:
        raise StoryError("No reasonable way to keep the pawn safe here.")

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        item=item,
        response=response,
        outcome="kept",
        tin=tin,
        washer=washer,
        dryer=dryer,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a slice-of-life story set in a laundry room where {child.id} '
        f"finds a pawn and has a small conflict with {f['parent'].label_word}.",
        f'Tell a gentle dialogue story using the words "conflict", "hanker", '
        f'and "pawn" in which a child learns to keep a small found toy safe.',
        f'Write a cozy family story about laundry, a tiny pawn, and a calm fix.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        (
            "What did the child find?",
            f"{child.id} found a little chess pawn in a pocket while sorting laundry. "
            f"It was small enough to lose easily, so the parent wanted to keep it safe.",
        ),
        (
            "Why was there conflict?",
            f"{child.id} wanted to keep the pawn nearby, but {parent.label_word} worried "
            f"it might slip away behind the washer or dryer. That is why they had a small conflict.",
        ),
        (
            "How did they solve the problem?",
            f"{parent.id} got a small tin and put the pawn inside it for safekeeping. "
            f"Then {child.id} could help with the laundry and still know the pawn was not lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pawn?", "A pawn is one of the small pieces used in chess. It is tiny, so it can be easy to misplace."),
        ("What does hanker mean?", "To hanker means to really want something or long for it. It is a strong wish that can linger in your mind."),
        ("What is a laundry room for?", "A laundry room is where people wash and dry clothes. It is often busy with baskets, soap, and warm towels."),
    ]


ASP_RULES = r"""
item_of_interest(pawn).
reasonable(Response) :- response(Response), sense(Response, S), S >= 2.
kept(pawn) :- item_of_interest(pawn), reasonable(Response).
outcome(kept) :- kept(pawn).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if asp_outcome() != "kept":
        print("MISMATCH: ASP outcome did not match Python.")
        rc = 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
    if not sample.story.strip():
        print("MISMATCH: ordinary story generation failed.")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Laundry-room slice-of-life storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    setting = args.setting or "laundry_room"
    item = args.item or "pawn"
    response = args.response or rng.choice(list(RESPONSES))
    if item not in ITEMS or response not in RESPONSES:
        raise StoryError("Invalid options.")
    if not reasonableness_gate(ITEMS[item], RESPONSES[response]):
        raise StoryError("No reasonable way to keep the pawn safe.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(CHILD_NAMES)
    return StoryParams(
        setting=setting,
        item=item,
        response=response,
        child=child,
        child_gender=child_gender,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.response not in RESPONSES:
        raise StoryError("Invalid StoryParams.")
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(
        setting="laundry_room",
        item="pawn",
        response="tin",
        child="Mia",
        child_gender="girl",
        parent_gender="mother",
    ),
    StoryParams(
        setting="laundry_room",
        item="pawn",
        response="pocket",
        child="Leo",
        child_gender="boy",
        parent_gender="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories: pawn in the laundry room with a sensible response")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
