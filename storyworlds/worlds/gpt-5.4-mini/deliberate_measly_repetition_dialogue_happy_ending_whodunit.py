#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deliberate_measly_repetition_dialogue_happy_ending_whodunit.py
==============================================================================================

A small whodunit-style storyworld about a child detective, a tiny missing thing,
repeated clues, and a happy ending. The story uses dialogue, deliberate
repetition, and a careful reveal.

The domain:
- A child notices something measly but important has gone missing.
- The child and a helpful adult ask questions, repeat a clue, and follow the
  trail with a simple world model.
- A harmless misunderstanding creates tension.
- The truth is found, the missing thing is returned, and the story ends happily.

This script is standalone and stdlib-only.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    text: str
    location: str
    significance: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    tiny: bool = True
    shiny: bool = False
    edible: bool = False
    location: str = ""
    owner: str = ""
    missing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def get_entity(self, eid: str) -> Entity:
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
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("missing_seen") and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child = world.get_entity("child")
        child.memes["worry"] += 1
        out.append("The missing bowl made the child worry.")
    return out


def _r_detective(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_spotted") and ("detective", "child") not in world.fired:
        world.fired.add(("detective", "child"))
        child = world.get_entity("child")
        child.memes["resolve"] += 1
        out.append("The child felt sure the clue meant something.")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("missing_found") and ("happy", "all") not in world.fired:
        world.fired.add(("happy", "all"))
        child = world.get_entity("child")
        adult = world.get_entity("adult")
        child.memes["joy"] += 1
        adult.memes["joy"] += 1
        out.append("The whole room felt lighter at once.")
    return out


CAUSAL_RULES = [
    Rule("worry", _r_worry),
    Rule("detective", _r_detective),
    Rule("happy", _r_happy),
]


def reasonableness_gate(setting: Setting, item: Item, clue: Clue) -> bool:
    return item.tiny and item.missing and clue.location == item.location


def deliberate_search_steps() -> list[str]:
    return [
        "Look low.",
        "Look slow.",
        "Look again.",
    ]


def search_copy(world: World) -> World:
    return world.copy()


def predict_find(world: World, item_id: str) -> bool:
    sim = search_copy(world)
    item = sim.items[item_id]
    item.missing = False
    return True


def make_story_search(world: World, child: Entity, adult: Entity, item: Item, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet morning in {world.setting.place}, {child.id} noticed that {item.label} was gone. "
        f"It was only a measly little thing, but it mattered to {child.pronoun('object')} all the same."
    )
    world.say(
        f'"{item.label}?" {child.id} said. "{item.label}?" {adult.label_word} asked. "Yes," {child.id} said, '
        f'"{item.label}."'
    )
    world.para()
    for step in deliberate_search_steps():
        world.say(step)
    world.say(
        f'"I found a clue," {child.id} whispered. "{clue.text}"'
    )
    world.say(
        f'"A clue?" {adult.label_word} said. "A clue." {child.id} nodded, and both of them repeated it like a secret.'
    )
    world.facts["clue_spotted"] = True
    propagate(world)


def mistake_beats(world: World, child: Entity, adult: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f"For a moment, {child.id} thought the clue meant trouble."
    )
    world.say(
        f'"Was someone being sneaky?" {child.id} asked. "{adult.label_word} looked calm. "Maybe. Or maybe someone was helpful."'
    )


def reveal(world: World, child: Entity, adult: Entity, item: Item) -> None:
    world.facts["missing_found"] = True
    item.missing = False
    item.location = "table"
    world.say(
        f'Then they looked where the clue pointed, and there was {item.label}, tucked in a safe little place.'
    )
    world.say(
        f'"I knew it," {child.id} said. "{item.label}!" "{item.label}!" {adult.label_word} laughed.'
    )
    world.say(
        f'The supposed mystery was only a small mix-up: {adult.label_word} had moved {item.label} out of the way so it would not get lost.'
    )
    propagate(world)
    world.say(
        f'{child.id} hugged {adult.pronoun("object")} and smiled. The measly missing thing was back, and the day felt bright again.'
    )


def tell(setting: Setting, item: Item, clue: Clue, child_name: str = "Mina",
         child_gender: str = "girl", adult_type: str = "mother") -> World:
    world = World(setting)
    child = world.add_entity(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    adult = world.add_entity(Entity(id="Adult", kind="character", type=adult_type, label="the adult"))
    world.add_item(item)
    world.facts.update(child=child, adult=adult, item=item, clue=clue, setting=setting)

    make_story_search(world, child, adult, item, clue)
    world.para()
    mistake_beats(world, child, adult)
    world.para()
    reveal(world, child, adult, item)
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "A sunny window sat over a round table."),
    "classroom": Setting("classroom", "the classroom", "Tiny chairs waited by neat little desks."),
    "playroom": Setting("playroom", "the playroom", "Blocks, books, and a rug made the room cozy."),
}

ITEMS = {
    "spoon": Item("spoon", "a silver spoon", tiny=True, shiny=True, location="drawer", missing=True),
    "button": Item("button", "a red button", tiny=True, shiny=False, location="floor", missing=True),
    "marble": Item("marble", "a blue marble", tiny=True, shiny=True, location="shelf", missing=True),
}

CLUES = {
    "glimmer": Clue("glimmer", "I saw a glimmer near the table.", "drawer", "It pointed to a hiding place.", {"shine"}),
    "scratch": Clue("scratch", "There was a scratch on the shelf.", "shelf", "It hinted something had slid there.", {"move"}),
    "napkin": Clue("napkin", "A napkin was folded beside the tray.", "floor", "It showed someone had been careful.", {"careful"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Maya", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Noah", "Ben", "Toby", "Max"]
ADULTS = ["mother", "father"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    child_name: str
    child_gender: str
    adult_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for cid, clue in CLUES.items():
                if reasonableness_gate(setting, item, clue):
                    combos.append((sid, iid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style story world with repetition and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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


def explain_rejection(item: Item, clue: Clue) -> str:
    return f"(No story: the clue does not point to the missing item {item.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.clue:
        if not reasonableness_gate(SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values())),
                                   ITEMS[args.item], CLUES[args.clue]):
            raise StoryError(explain_rejection(ITEMS[args.item], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, iid, cid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(sid, iid, cid, name, gender, adult)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a young child that includes the words "deliberate" and "measly".',
        f"Tell a story where {f['child'].id} asks questions, repeats a clue, and finds the missing {f['item'].label}.",
        f"Write a happy mystery with dialogue and repetition, where a tiny missing thing is found after a careful search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    item = f["item"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What was missing?",
            answer=f"{item.label} was missing. It was a measly little thing, but it still mattered in the story."
        ),
        QAItem(
            question=f"What did {child.id} do?",
            answer=f"{child.id} made a deliberate search, asked questions, and repeated the clue until the answer became clear."
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"It ended happily when they found {item.label} where the clue pointed. The mix-up was small, and everyone felt glad."
        ),
        QAItem(
            question=f"What did {adult.label_word} say about the clue?",
            answer=f"{adult.label_word.capitalize()} said the clue might mean someone was helpful, not sneaky. That calm answer helped the child keep looking."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item: Item = f["item"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question="What does deliberate mean?",
            answer="Deliberate means careful and on purpose. Someone who is deliberate does not rush around."
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a hint that helps someone solve a mystery. It points the detective toward the answer."
        ),
        QAItem(
            question=f"Why might a tiny item still matter?",
            answer=f"Even a tiny item can matter if someone uses it every day or loves it. {item.label} was small, but it was important."
        ),
        QAItem(
            question="Why is repetition useful when searching?",
            answer="Repetition helps people remember a detail and check it again. In a mystery, repeating a clue can keep the answer in mind."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: {e.type} role={e.role} memes={dict(e.memes)}")
    for item in world.items.values():
        lines.append(f"  item {item.id}: label={item.label} missing={item.missing} location={item.location}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "spoon", "glimmer", "Mina", "girl", "mother"),
    StoryParams("classroom", "button", "napkin", "Finn", "boy", "father"),
    StoryParams("playroom", "marble", "scratch", "Lily", "girl", "mother"),
]


ASP_RULES = r"""
valid(S, I, C) :- setting(S), item(I), clue(C), clue_points_to(C, I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.tiny:
            lines.append(asp.fact("tiny", iid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_points_to", cid, clue.location))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        CLUES[params.clue],
        params.child_name,
        params.child_gender,
        params.adult_type,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos.")
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
            header = f"### {p.child_name}: {p.setting}, {p.item}, {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
