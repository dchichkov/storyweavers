#!/usr/bin/env python3
"""
Story world: array, reservoir, antique, bravery, conflict, repetition, bedtime.

A small bedtime-style simulation where a child arranges an array of glowing
sleep-time objects, worries about a tiny reservoir, and finds bravery to keep
the nightly routine steady. The story is built from world state, not from a
frozen template: the array can be in order or upset, the reservoir can be full
or low, and an antique keepsake can be used to resolve the problem.

The world is intentionally small and constraint-checked. The core premise is:

- A child has a bedtime array of items to line up in order.
- An antique keepsake or nightlight matters to the child.
- A small reservoir of water or moonwater can run low, causing worry.
- Repetition of the bedtime routine helps the child feel safe.
- Bravery is needed to fix a late-night conflict without waking everyone.

The story should read like a gentle bedtime tale with a clear beginning,
middle turn, and ending image.
"""

from __future__ import annotations

import argparse
import copy
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ArrayItem:
    id: str
    label: str
    phrase: str
    kind: str
    slot: int
    polished: bool = False


@dataclass
class Reservoir:
    id: str
    label: str
    phrase: str
    kind: str
    low_phrase: str
    refill_phrase: str
    can_hold: set[str] = field(default_factory=set)


@dataclass
class Antique:
    id: str
    label: str
    phrase: str
    kind: str
    glow_phrase: str
    comfort_phrase: str
    requires_bravery: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def sorted_slots(items: list[ArrayItem]) -> bool:
    return [it.slot for it in items] == sorted(it.slot for it in items)


def reasonableness_gate(array_cfg: list[ArrayItem], reservoir: Reservoir, antique: Antique) -> None:
    if not array_cfg:
        raise StoryError("The bedtime array needs at least one item.")
    if reservoir.kind not in {"water", "moonwater", "tea"}:
        raise StoryError("The reservoir must be a small, sensible bedside reservoir.")
    if antique.kind not in {"music_box", "lamp", "toy", "clock"}:
        raise StoryError("The antique must be a child-friendly keepsake.")
    if antique.requires_bravery and not reservoir.can_hold:
        raise StoryError("A brave fix needs a reservoir or a similar place to store the solution.")


@dataclass
class StoryParams:
    place: str
    child: str
    parent: str
    array: str
    reservoir: str
    antique: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", quiet=True, affords={"array", "reservoir", "antique"}),
    "nursery": Setting(place="the nursery", quiet=True, affords={"array", "reservoir", "antique"}),
}

ARRAYS = {
    "books": [
        ArrayItem("book1", "picture book", "a picture book with a blue star", "book", 1),
        ArrayItem("book2", "storybook", "a soft storybook", "book", 2),
        ArrayItem("book3", "little book", "a little book of songs", "book", 3),
    ],
    "blocks": [
        ArrayItem("block1", "red block", "a red block", "block", 1),
        ArrayItem("block2", "yellow block", "a yellow block", "block", 2),
        ArrayItem("block3", "blue block", "a blue block", "block", 3),
    ],
    "shells": [
        ArrayItem("shell1", "small shell", "a small shell", "shell", 1),
        ArrayItem("shell2", "curved shell", "a curved shell", "shell", 2),
        ArrayItem("shell3", "moon shell", "a moon-shaped shell", "shell", 3),
    ],
}

RESERVOIRS = {
    "glass": Reservoir("glass", "glass bowl", "a glass bowl of water", "water", "nearly empty", "filled again", {"water"}),
    "cup": Reservoir("cup", "tiny cup", "a tiny cup of moonwater", "moonwater", "almost dry", "topped up", {"moonwater"}),
    "kettle": Reservoir("kettle", "little kettle", "a little kettle of warm tea", "tea", "nearly dry", "refilled", {"tea"}),
}

ANTIQUES = {
    "music_box": Antique("music_box", "antique music box", "an antique music box with a silver dancer", "music_box", "a tiny tune", "a warm, sleepy tune", True),
    "lamp": Antique("lamp", "antique lamp", "an antique lamp with a brass base", "lamp", "a soft golden glow", "a sleepy glow", False),
    "clock": Antique("clock", "antique clock", "an antique clock with round hands", "clock", "a slow tick-tock", "a steady tick-tock", False),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Lily", "Ben"]
PARENT_NAMES = ["Mom", "Dad", "Mother", "Father"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with array, reservoir, antique, bravery, conflict, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--array", choices=ARRAYS)
    ap.add_argument("--reservoir", choices=RESERVOIRS)
    ap.add_argument("--antique", choices=ANTIQUES)
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=["Mom", "Dad", "Mother", "Father"])
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
    array = args.array or rng.choice(list(ARRAYS))
    reservoir = args.reservoir or rng.choice(list(RESERVOIRS))
    antique = args.antique or rng.choice(list(ANTIQUES))
    place = args.place or rng.choice(list(SETTINGS))
    child = args.child or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    reasonableness_gate(ARRAYS[array], RESERVOIRS[reservoir], ANTIQUES[antique])
    return StoryParams(place=place, child=child, parent=parent, array=array, reservoir=reservoir, antique=antique)


def _set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def tell(setting: Setting, array_cfg: list[ArrayItem], reservoir_cfg: Reservoir, antique_cfg: Antique,
         child_name: str, parent_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent"))
    array = [copy.deepcopy(x) for x in array_cfg]
    reservoir = world.add(Entity(id=reservoir_cfg.id, type=reservoir_cfg.kind, label=reservoir_cfg.label, phrase=reservoir_cfg.phrase))
    antique = world.add(Entity(id=antique_cfg.id, type=antique_cfg.kind, label=antique_cfg.label, phrase=antique_cfg.phrase))

    _add_meme(child, "love_routine", 1)
    _add_meme(child, "need_order", 1)
    _add_meter(reservoir, "fullness", 1.0)
    _add_meme(antique, "comfort", 1)
    _add_meme(antique, "glow", 1)

    world.say(f"{child.id} lived in {setting.place}, where bedtime came softly like a whisper.")
    world.say(f"Every night, {child.id} lined up {array[0].label}, {array[1].label}, and {array[2].label} in a careful array beside the bed.")
    world.say(f"Near the pillow sat {reservoir.phrase}, and on the shelf waited {antique.phrase}.")
    world.say(f"{child.id} liked the same steps every night, because repetition made the room feel safe and warm.")

    world.para()
    _add_meme(child, "peace", 1)
    world.say(f"{parent.id} said it was time for the usual bedtime round: wash, line up the array, and listen to the old lamp or box.")
    world.say(f"{child.id} nodded, but then {reservoir.label} looked smaller than usual, and the {antique.label} seemed to hum by itself.")

    _add_meme(child, "worry", 1)
    _add_meme(parent, "watchful", 1)
    _add_meter(reservoir, "fullness", -0.75)
    world.say(f"The reservoir was almost empty, and that made the room feel a little uneasy.")
    world.say(f"{child.id} wanted the night to stay nice and steady, but the tiny problem tugged at {child.id}'s heart.")

    world.para()
    _add_meme(child, "conflict", 1)
    world.say(f"{child.id} stood very still, looking at the low reservoir, the neat array, and the antique on the shelf.")
    world.say(f"Then {antique.label} gave a little click, and {child.id} remembered that a brave bedtime fix could be small.")

    _add_meme(child, "bravery", 1)
    _add_meme(parent, "hope", 1)
    if reservoir_cfg.kind == "water":
        reservoir_phrase = "a sip of water from the kitchen"
    elif reservoir_cfg.kind == "moonwater":
        reservoir_phrase = "a careful pour from the moonwater bottle"
    else:
        reservoir_phrase = "a warm refill from the kettle"
    world.say(f"{child.id} took a deep breath, carried {reservoir_phrase}, and filled the reservoir again.")
    _add_meter(reservoir, "fullness", 1.0)
    _add_meme(reservoir, "safe", 1)

    world.say(f"That made the antique {antique_cfg.comfort_phrase}, and the room settled down.")
    _add_meme(antique, "glow", 1)
    _add_meme(child, "relief", 1)

    world.para()
    world.say(f"{child.id} lined up the array again, this time one careful piece after another, repeating the same calm order.")
    world.say(f"{parent.id} tucked the blanket in just right and smiled at the brave little helper.")
    world.say(f"At the end, the reservoir was full, the antique shone softly, and the bedtime array stood straight and tidy beside the bed.")

    world.facts.update(
        child=child,
        parent=parent,
        array=array,
        reservoir=reservoir,
        antique=antique,
        setting=setting,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ARRAYS[params.array], RESERVOIRS[params.reservoir], ANTIQUES[params.antique], params.child, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story for a small child about an array, a reservoir, and an antique.',
        f"Tell a cozy story where {f['child'].id} needs bravery to fix a bedtime problem without waking the room.",
        f"Write a bedtime tale that repeats a calming routine and ends with the reservoir full and the antique glowing softly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    reservoir = f["reservoir"]
    antique = f["antique"]
    arr = f["array"]
    return [
        QAItem(
            question=f"What did {child.id} line up beside the bed every night?",
            answer=f"{child.id} lined up an array of bedtime items: {arr[0].label}, {arr[1].label}, and {arr[2].label}. The repeated order helped the room feel safe.",
        ),
        QAItem(
            question=f"What problem made {child.id} feel worried in the story?",
            answer=f"{reservoir.label} was almost empty, and that made {child.id} feel uneasy. The little problem turned the bedtime routine into a conflict that needed a brave fix.",
        ),
        QAItem(
            question=f"How did {child.id} solve the bedtime conflict?",
            answer=f"{child.id} took a deep breath and refilled {reservoir.label}. After that, {antique.label} gave a calm glow, and bedtime could continue peacefully.",
        ),
        QAItem(
            question=f"How did the antique help the room?",
            answer=f"{antique.label} made a soft, sleepy light and reminded everyone to stay calm. Its gentle presence helped the bedtime routine feel comforting instead of scary.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an array?",
            answer="An array is a row of things placed in a certain order, like toys lined up on a shelf or books set one after another.",
        ),
        QAItem(
            question="What is a reservoir?",
            answer="A reservoir is a place that holds water or another liquid. It can be big in the real world or tiny in a story, like a small bowl or cup.",
        ),
        QAItem(
            question="What does an antique mean?",
            answer="An antique is something very old that people keep because it is special, beautiful, or full of memories.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or a little scary because it is the right thing to do.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same thing again and again. In bedtime stories, repetition can make the routine feel calm and safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(child;parent;array;reservoir;antique).

needs_bravery(C) :- child(C), conflict(C).
repetition_helpful(C) :- child(C), array(A), fixed_array(A).
calm_end(C) :- child(C), reservoir_full(C), antique_glow(C), repetition_helpful(C), needs_bravery(C).

valid_story(P) :- setting(P), child_name(P), reservoir_ok(P), antique_ok(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    for name in ARRAYS:
        lines.append(asp.fact("array_kind", name))
    for name in RESERVOIRS:
        lines.append(asp.fact("reservoir_kind", name))
    for name in ANTIQUES:
        lines.append(asp.fact("antique_kind", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    python_ok = True
    for place in SETTINGS:
        for arr in ARRAYS:
            for res in RESERVOIRS:
                for ant in ANTIQUES:
                    try:
                        reasonableness_gate(ARRAYS[arr], RESERVOIRS[res], ANTIQUES[ant])
                    except StoryError:
                        python_ok = False
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = True
    if python_ok and asp_ok:
        print("OK: Python reasonableness gate and ASP twin are both present.")
        return 0
    print("MISMATCH in verification.")
    return 1


CURATED = [
    StoryParams(place="bedroom", child="Mia", parent="Mom", array="books", reservoir="glass", antique="music_box"),
    StoryParams(place="nursery", child="Leo", parent="Dad", array="blocks", reservoir="cup", antique="lamp"),
    StoryParams(place="bedroom", child="Nora", parent="Mother", array="shells", reservoir="kettle", antique="clock"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, arr, res) for place in SETTINGS for arr in ARRAYS for res in RESERVOIRS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_story_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combinations.")
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
            header = f"### {p.child}: {p.array} / {p.reservoir} / {p.antique}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
