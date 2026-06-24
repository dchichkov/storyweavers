#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child who loves a collection, notices a
strange thunk, and uses a little magic to diagnose what is going on.

The world is intentionally small and constraint-checked:
- one child has a cherished collection
- a tiny magical helper or charm can diagnose a problem
- a thunk reveals something has fallen, jammed, or knocked loose
- the ending shows a concrete change in state

The prose should feel like a gentle everyday story rather than an event log.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Thing:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    covers: set[str] = field(default_factory=set)
    magical: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the living room"
    cozy_detail: str = "sunlight pooled on the rug"


@dataclass
class CollectionItem:
    id: str
    label: str
    phrase: str
    kind: str
    place: str
    can_thunk: bool = False
    can_jam: bool = False


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    method: str
    clue: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Thing] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Thing) -> Thing:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Thing:
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
        clone = World(self.setting)
        clone.entities = {k: Thing(**{
            **vars(v),
            "covers": set(v.covers),
            "meters": dict(v.meters),
            "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "living_room": Setting(place="the living room", cozy_detail="sunlight pooled on the rug"),
    "kitchen_table": Setting(place="the kitchen table", cozy_detail="a small lamp made a warm circle of light"),
    "bedroom_floor": Setting(place="the bedroom floor", cozy_detail="a striped blanket was folded by the bed"),
}

COLLECTIONS = {
    "buttons": [
        CollectionItem("red_button", "red button", "a red button with two holes", "button", "jar", True, False),
        CollectionItem("blue_button", "blue button", "a blue button with a tiny star", "button", "jar", True, False),
        CollectionItem("gold_button", "gold button", "a gold button that sparkled like a coin", "button", "jar", True, False),
    ],
    "shells": [
        CollectionItem("round_shell", "round shell", "a round shell from the shore", "shell", "box", True, False),
        CollectionItem("white_shell", "white shell", "a white shell with a soft curl", "shell", "box", True, False),
        CollectionItem("pink_shell", "pink shell", "a pink shell that looked like a tiny fan", "shell", "box", True, False),
    ],
    "marbles": [
        CollectionItem("green_marble", "green marble", "a green marble with a clear swish inside", "marble", "bag", True, True),
        CollectionItem("amber_marble", "amber marble", "an amber marble that glowed in the light", "marble", "bag", True, True),
        CollectionItem("blue_marble", "blue marble", "a blue marble as smooth as water", "marble", "bag", True, False),
    ],
}

MAGIC_TOOLS = {
    "glow_stone": MagicTool(
        id="glow_stone",
        label="glow stone",
        phrase="a palm-sized glow stone",
        method="hold it up to the collection and ask it to glow at the trouble spot",
        clue="the dim place would brighten where the jam was hiding",
    ),
    "listening_spoon": MagicTool(
        id="listening_spoon",
        label="listening spoon",
        phrase="a silver listening spoon",
        method="tap the jars and listen for the odd little thunk",
        clue="the wrong jar would sound hollow and soft",
    ),
}

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    collection: str
    magic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Lena", "Nora", "Ivy", "Zoe", "Ava", "Ruby", "Maya"]
NAMES_BOY = ["Eli", "Noah", "Finn", "Leo", "Sam", "Theo", "Ben", "Max"]
TRAITS = ["curious", "gentle", "patient", "quiet", "cheerful", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life storyworld about a collection, a thunk, and a bit of magic."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--collection", choices=COLLECTIONS)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in COLLECTIONS:
            for m in MAGIC_TOOLS:
                combos.append((s, c, m))
    return combos


def select_item_collection(collection_id: str) -> list[CollectionItem]:
    if collection_id not in COLLECTIONS:
        raise StoryError(f"Unknown collection '{collection_id}'.")
    return COLLECTIONS[collection_id]


def explain_rejection() -> str:
    return "(No story: the chosen options don't make a plausible everyday collection problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.collection:
        combos = [c for c in combos if c[1] == args.collection]
    if args.magic:
        combos = [c for c in combos if c[2] == args.magic]
    if not combos:
        raise StoryError(explain_rejection())

    setting, collection, magic = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, collection=collection, magic=magic, name=name, gender=gender, parent=parent, trait=trait)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    child = world.add(Thing(id=params.name, kind="character", type=params.gender))
    parent = world.add(Thing(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    collection_items = select_item_collection(params.collection)
    tool = MAGIC_TOOLS[params.magic]

    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["tool"] = tool
    world.facts["collection_items"] = collection_items

    for item in collection_items:
        world.add(Thing(
            id=item.id,
            kind="thing",
            type=item.kind,
            label=item.label,
            phrase=item.phrase,
            owner=child.id,
            caretaker=parent.id,
            plural=False,
            meters={"tidy": 1.0},
            memes={"precious": 1.0},
        ))

    # The collection container itself.
    container_label = {"buttons": "glass jar", "shells": "small box", "marbles": "drawstring bag"}[params.collection]
    world.add(Thing(
        id="container",
        kind="thing",
        type="container",
        label=container_label,
        phrase=f"a little {container_label}",
        owner=child.id,
        caretaker=parent.id,
        meters={"tidy": 1.0},
    ))

    # The hidden problem object.
    problem = world.add(Thing(
        id="jammed_lid",
        kind="thing",
        type="lid",
        label="lid",
        phrase="the jar lid",
        owner="container",
        caretaking_note := "",
        meters={"loose": 0.0, "stuck": 1.0},
    ))
    problem.memes["annoying"] = 1.0

    # Choose a meaningful collection item to be affected.
    chosen = collection_items[0]
    if params.collection == "marbles":
        chosen = collection_items[1]
    elif params.collection == "buttons":
        chosen = collection_items[2]
    world.facts["chosen_item"] = chosen
    world.facts["problem"] = problem
    world.facts["container_label"] = container_label
    return world


def diagnose_problem(world: World) -> str:
    tool: MagicTool = world.facts["tool"]
    item: CollectionItem = world.facts["chosen_item"]
    if tool.id == "glow_stone":
        return f"The glow stone showed a tiny bright spot near the {item.label}."
    return f"The listening spoon made the {world.facts['container_label']} go thunk, and the soft sound came from the {item.label}."


def resolve_problem(world: World) -> None:
    item: CollectionItem = world.facts["chosen_item"]
    problem: Thing = world.facts["problem"]
    child: Thing = world.facts["child"]
    parent: Thing = world.facts["parent"]
    tool: MagicTool = world.facts["tool"]

    # Fix the jam.
    problem.meters["stuck"] = 0.0
    problem.meters["open"] = 1.0
    item.meters["tidy"] = 1.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1.0
    world.facts["resolved"] = True
    world.say(
        f"They used {tool.label} the careful way, and after one more gentle try the {world.facts['container_label']} opened."
    )
    world.say(
        f"The {item.label} stayed safe inside, and {child.id} smiled because the collection was neat again."
    )


def tell_story(world: World) -> None:
    child: Thing = world.facts["child"]
    parent: Thing = world.facts["parent"]
    tool: MagicTool = world.facts["tool"]
    item: CollectionItem = world.facts["chosen_item"]
    setting = world.setting

    world.say(
        f"{child.id} was a little {child.type} who loved a collection of {world.facts['collection_items'][0].kind}s."
    )
    world.say(
        f"At {setting.place}, {setting.cozy_detail}, and {child.id} sorted the collection with a careful little smile."
    )

    world.para()
    world.say(
        f"Then, while {child.id} reached for the {item.label}, there came a soft thunk from the {world.facts['container_label']}."
    )
    world.say(
        f"{child.id} frowned and called for {parent.label}."
    )
    world.say(
        f"The {parent.type} leaned closer, because the sound meant something in the collection was not quite right."
    )
    world.say(
        f"{parent.label.capitalize()} brought out {tool.phrase} and said it could {tool.method}."
    )

    world.para()
    world.say(diagnose_problem(world))
    world.say(
        f"That was enough to diagnose the trouble: the lid had caught on a tiny edge, and the collection could not be put away neatly."
    )
    world.say(
        f"{child.id} held still while the {parent.type} fixed it with a patient twist."
    )
    resolve_problem(world)

    world.para()
    world.say(
        f"In the end, the jar was open, the collection was lined up again, and the room felt calm and ordinary in the best way."
    )
    world.facts["story_done"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child: Thing = world.facts["child"]
    parent: Thing = world.facts["parent"]
    tool: MagicTool = world.facts["tool"]
    item: CollectionItem = world.facts["chosen_item"]
    return [
        f'Write a gentle slice-of-life story for a young child about {child.id}, a collection, and a small magical tool called "{tool.label}".',
        f"Tell a simple story where {child.id} hears a thunk near a {item.kind} collection and asks {parent.label} for help.",
        f'Write a child-friendly story that uses the word "diagnose" in a natural way and ends with the collection being safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Thing = world.facts["child"]
    parent: Thing = world.facts["parent"]
    tool: MagicTool = world.facts["tool"]
    item: CollectionItem = world.facts["chosen_item"]
    setting = world.setting

    return [
        QAItem(
            question=f"What was {child.id} doing in {setting.place} when the thunk happened?",
            answer=f"{child.id} was sorting a collection and reaching for the {item.label}. {setting.cozy_detail.capitalize()}, and the room felt calm until the thunk sounded.",
        ),
        QAItem(
            question=f"Why did {child.id} call for {parent.label} after the thunk?",
            answer=f"{child.id} called for {parent.label} because the thunk meant something in the collection was not quite right. The parent came to help diagnose the trouble.",
        ),
        QAItem(
            question=f"How did the magical tool help diagnose the problem?",
            answer=f"{tool.label.capitalize()} helped by {tool.method}. That made the hidden problem easier to find.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the collection was neat again, the stuck lid was fixed, and {child.id} felt proud and relieved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a collection?",
            answer="A collection is a group of things someone likes to keep together, like shells, buttons, or marbles.",
        ),
        QAItem(
            question="What does diagnose mean?",
            answer="To diagnose something means to figure out what is causing a problem.",
        ),
        QAItem(
            question="What is a thunk?",
            answer="A thunk is a short, dull sound, like something bumping or landing softly.",
        ),
        QAItem(
            question="What does magic do in this world?",
            answer="Magic helps look closely at a small problem so it can be understood and fixed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Trace / emit
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.label:
            parts.append(f"label={e.label}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        if e.meters:
            parts.append(f"meters={dict(e.meters)}")
        if e.memes:
            parts.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting(S).
collection(C) :- collection(C).
magic(M) :- magic(M).

valid_story(S, C, M) :- setting(S), collection(C), magic(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in COLLECTIONS:
        lines.append(asp.fact("collection", c))
    for m in MAGIC_TOOLS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.collection:
        combos = [c for c in combos if c[1] == args.collection]
    if args.magic:
        combos = [c for c in combos if c[2] == args.magic]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, collection, magic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, collection=collection, magic=magic, name=name, gender=gender, parent=parent, trait=trait)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, m) for s in SETTINGS for c in COLLECTIONS for m in MAGIC_TOOLS]


CURATED = [
    StoryParams(setting="living_room", collection="buttons", magic="glow_stone", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="kitchen_table", collection="shells", magic="listening_spoon", name="Eli", gender="boy", parent="father", trait="careful"),
    StoryParams(setting="bedroom_floor", collection="marbles", magic="glow_stone", name="Nora", gender="girl", parent="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.collection} + {p.magic} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
