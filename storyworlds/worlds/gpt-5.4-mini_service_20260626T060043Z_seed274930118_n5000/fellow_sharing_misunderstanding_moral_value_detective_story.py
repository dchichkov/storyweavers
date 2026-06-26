#!/usr/bin/env python3
"""
Standalone storyworld: a detective-style tale about a fellow, sharing, a
misunderstanding, and a moral value turn.

The premise is small and classical:
- A fellow notices something shared has gone wrong.
- The world model tracks possession, trust, and a simple clue trail.
- The "mystery" is a misunderstanding, not a real theft.
- Resolution proves a moral value: fair sharing and honest asking.

This file follows the Storyweavers storyworld contract.
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
# Domain registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    place: str
    indoors: bool = True


@dataclass(frozen=True)
class ObjectItem:
    id: str
    label: str
    phrase: str
    plural: bool = False


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    phrase: str


@dataclass(frozen=True)
class MoralValue:
    id: str
    label: str
    explanation: str


SETTINGS = {
    "library": Setting(place="the small library", indoors=True),
    "playroom": Setting(place="the playroom", indoors=True),
    "garden_shed": Setting(place="the garden shed", indoors=True),
}

OBJECTS = {
    "markers": ObjectItem(
        id="markers",
        label="markers",
        phrase="a bright box of markers",
        plural=True,
    ),
    "cookies": ObjectItem(
        id="cookies",
        label="cookies",
        phrase="a plate of jam cookies",
        plural=True,
    ),
    "book": ObjectItem(
        id="book",
        label="book",
        phrase="a picture book with a blue cover",
    ),
}

CLUES = {
    "crumbs": Clue(id="crumbs", label="crumbs", phrase="a few crumbs"),
    "cap": Clue(id="cap", label="cap", phrase="a blue cap"),
    "smudge": Clue(id="smudge", label="smudge", phrase="a smudge of red ink"),
}

VALUES = {
    "fairness": MoralValue(
        id="fairness",
        label="fairness",
        explanation="Fairness means giving everyone a proper turn and not taking more than your share.",
    ),
    "honesty": MoralValue(
        id="honesty",
        label="honesty",
        explanation="Honesty means telling the truth when something looks strange.",
    ),
    "sharing": MoralValue(
        id="sharing",
        label="sharing",
        explanation="Sharing means letting others use something kindly and taking care of it together.",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Iris", "Eli", "Sana", "Noah", "Lina"]
FELLOW_NAMES = ["fellow", "young fellow", "little fellow", "helpful fellow"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"clean": 1.0, "visible": 1.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.events = []
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    object_id: str
    clue_id: str
    value_id: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def valid_combo(place: str, object_id: str, clue_id: str, value_id: str) -> bool:
    if place not in SETTINGS or object_id not in OBJECTS or clue_id not in CLUES or value_id not in VALUES:
        return False
    # Detective-style reasonable pairings:
    # - cookies -> crumbs clue
    # - markers -> smudge clue
    # - book -> cap clue is a misunderstanding at the shed/library involving a dropped cap
    if object_id == "cookies" and clue_id != "crumbs":
        return False
    if object_id == "markers" and clue_id != "smudge":
        return False
    if object_id == "book" and clue_id != "cap":
        return False
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = []
    for place in SETTINGS:
        if args.place and args.place != place:
            continue
        for obj_id in OBJECTS:
            if args.object and args.object != obj_id:
                continue
            for clue_id in CLUES:
                if args.clue and args.clue != clue_id:
                    continue
                for value_id in VALUES:
                    if args.value and args.value != value_id:
                        continue
                    if valid_combo(place, obj_id, clue_id, value_id):
                        candidates.append((place, obj_id, clue_id, value_id))
    if not candidates:
        raise StoryError("No valid story matches the requested options.")
    place, object_id, clue_id, value_id = rng.choice(candidates)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, object_id=object_id, clue_id=clue_id, value_id=value_id, name=name)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    fellow = world.add(Entity(
        id=params.name,
        kind="character",
        type="fellow",
        label=f"{params.name} the fellow",
        phrase=f"a helpful fellow named {params.name}",
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="child",
        label="a friend",
        phrase="a nearby friend",
    ))
    shared_object = OBJECTS[params.object_id]
    clue = CLUES[params.clue_id]
    value = VALUES[params.value_id]

    item = world.add(Entity(
        id="item",
        kind="thing",
        type=shared_object.id,
        label=shared_object.label,
        phrase=shared_object.phrase,
        owner=fellow.id,
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        phrase=clue.phrase,
    ))

    # Act 1: setup.
    world.say(f"{params.name} was a helpful fellow who liked calm puzzles and kind answers.")
    world.say(f"One day, {params.name} brought {shared_object.phrase} to {setting.place} to share with a friend.")
    world.say(f"{params.name} liked {VALUES[params.value_id].label} because {value.explanation}")

    # Act 2: misunderstanding.
    world.say(f"Then the item was not where it should have been.")
    world.say(f"{params.name} saw {clue.phrase} nearby and began to worry.")
    fellow.memes["worry"] += 1.0
    fellow.memes["curiosity"] += 1.0
    world.facts["suspected"] = "friend"
    world.facts["clue"] = clue.id
    world.facts["value"] = value.id
    world.facts["item"] = item.id

    if params.object_id == "cookies":
        world.say(f"{params.name} thought someone had taken too many cookies without asking.")
    elif params.object_id == "markers":
        world.say(f"{params.name} thought the markers had been borrowed without sharing them back.")
    else:
        world.say(f"{params.name} thought the book had been lost, and the clue made the case look worse.")

    # Act 3: detective turn.
    if clue.id == "crumbs":
        world.say(f"But the crumbs led to the table, not to a thief.")
        friend.shared_with.add(fellow.id)
        item.shared_with.add(friend.id)
        world.say(f"The friend had only moved the plate to keep it safe while the two of them took turns.")
    elif clue.id == "smudge":
        world.say(f"But the smudge of red ink pointed to the art corner.")
        friend.shared_with.add(fellow.id)
        item.shared_with.add(friend.id)
        world.say(f"The friend had borrowed the markers for a drawing and put them back in the cup.")
    else:
        world.say(f"But the blue cap showed the trail was about a dropped hat, not a stolen book.")
        friend.shared_with.add(fellow.id)
        item.shared_with.add(friend.id)
        world.say(f"The friend had only moved the book to make room and then left the cap behind.")

    fellow.memes["worry"] = 0.0
    fellow.memes["trust"] += 1.0
    fellow.memes["relief"] += 1.0

    # Moral conclusion.
    world.say(f"{params.name} smiled, apologized for jumping to conclusions, and thanked the friend for helping.")
    world.say(f"In the end, they shared the {shared_object.label} properly, and {value.label} made the room feel peaceful again.")

    world.facts.update(
        fellow=fellow.id,
        friend=friend.id,
        setting=setting.place,
        object=shared_object.id,
        clue=clue.id,
        value=value.id,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective-style story for a child about a fellow in {f["setting"]} who notices a clue and learns about {VALUES[f["value"]].label}.',
        f"Tell a short mystery about {f['fellow']} and a shared {OBJECTS[f['object']].label} that turns out to be a misunderstanding.",
        f'Create a gentle story with a fellow, a clue, and a moral lesson about {VALUES[f["value"]].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj = OBJECTS[f["object"]]
    clue = CLUES[f["clue"]]
    value = VALUES[f["value"]]
    return [
        QAItem(
            question=f"What did {f['fellow']} bring to {f['setting']} at the start of the story?",
            answer=f"{f['fellow']} brought {obj.phrase} so the item could be shared with a friend.",
        ),
        QAItem(
            question=f"What clue made the fellow worry?",
            answer=f"The clue was {clue.phrase}, which made the scene look like a mystery at first.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer="The fellow thought something had been taken, but it had only been moved or borrowed kindly.",
        ),
        QAItem(
            question=f"What moral value did the fellow learn?",
            answer=f"The story taught {value.label}: {value.explanation}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to understand what really happened.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use something kindly and fairly instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first and then learns the truth.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
kind(fellow).
kind(object).
kind(clue).
kind(value).

valid(P,O,C,V) :- place(P), object(O), clue(C), value(V), combo_ok(P,O,C,V).
resolves(O,C) :- valid(_,O,C,_).
moral(V) :- valid(_,_,_,V).
#show valid/4.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for v in VALUES:
        lines.append(asp.fact("value", v))
    for p in SETTINGS:
        for o in OBJECTS:
            for c in CLUES:
                for v in VALUES:
                    if valid_combo(p, o, c, v):
                        lines.append(asp.fact("combo_ok", p, o, c, v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set()
    for p in SETTINGS:
        for o in OBJECTS:
            for c in CLUES:
                for v in VALUES:
                    if valid_combo(p, o, c, v):
                        py.add((p, o, c, v))
    asp_set = asp_valid_combos()
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} label={e.label!r} "
            f"owner={e.owner!r} meters={e.meters} memes={e.memes} shared_with={sorted(e.shared_with)}"
        )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld about sharing and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--object", choices=OBJECTS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--value", choices=VALUES.keys())
    ap.add_argument("--name", choices=NAMES)
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


def resolve_all() -> list[StoryParams]:
    out = []
    for p in SETTINGS:
        for o in OBJECTS:
            for c in CLUES:
                for v in VALUES:
                    if valid_combo(p, o, c, v):
                        out.append(StoryParams(place=p, object_id=o, clue_id=c, value_id=v, name="Milo"))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for combo in combos:
            print(combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        params_list = resolve_all()
        for p in params_list:
            samples.append(generate(p))
    else:
        seen = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if len(samples) >= args.n:
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.object_id} / {p.clue_id} / {p.value_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
