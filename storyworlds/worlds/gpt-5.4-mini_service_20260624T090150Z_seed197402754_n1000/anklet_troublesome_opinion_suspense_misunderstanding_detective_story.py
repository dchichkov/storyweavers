#!/usr/bin/env python3
"""
A small detective-story world about a troublesome anklet, a mistaken opinion, and
a suspenseful misunderstanding that gets solved by careful noticing.

The model is intentionally tiny and classical:
- a child detective notices a missing or misplaced anklet
- one character forms a hasty opinion from an incomplete clue
- suspense rises while the detective checks evidence
- the misunderstanding is resolved by a concrete reveal
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    indoors: bool = True
    rooms: list[str] = field(default_factory=lambda: ["hall", "kitchen", "study", "porch"])


@dataclass
class Clue:
    id: str
    where: str
    what: str
    suggests: str


@dataclass
class Mystery:
    id: str
    missing_item: str
    item_phrase: str
    item_type: str
    clue_room: str
    culprit: str
    mistaken_opinion: str
    true_location: str
    suspense_line: str
    resolution_line: str


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_type: str
    companion_name: str
    companion_type: str
    item: str
    seed: Optional[int] = None


SETTINGS = {
    "house": Setting(place="the old house", indoors=True, rooms=["hall", "kitchen", "study", "porch"]),
    "apartment": Setting(place="the small apartment", indoors=True, rooms=["entry", "bedroom", "living room", "closet"]),
    "museum": Setting(place="the quiet museum", indoors=True, rooms=["lobby", "gallery", "office", "cloakroom"]),
}

DETECTIVE_NAMES = ["Maya", "Leo", "Nina", "Jasper", "Ivy", "Theo", "Mila", "Finn"]
COMPANION_NAMES = ["Aunt June", "Ben", "Rosa", "Mr. Clay", "Tia", "Noah", "Eden", "Pip"]

ITEMS = {
    "anklet": {
        "label": "anklet",
        "phrase": "a tiny silver anklet with a blue bead",
        "owner": "companion",
        "hidden_in": "study drawer",
        "troubles": "tangled",
    }
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world about a troublesome anklet and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["girl", "boy", "mother", "father", "aunt", "uncle"])
    ap.add_argument("--item", choices=ITEMS)
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


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("label", item_id, item["label"]))
        lines.append(asp.fact("phrase", item_id, item["phrase"]))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is suspicious if the item is hidden somewhere and someone makes a
% quick opinion before checking the clue room.
suspense(item) :- item(item).
misunderstanding(item) :- item(item).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity check: ensure the inline program solves and returns the expected item facts.
    import asp

    model = asp.one_model(asp_program("#show item/1."))
    items = set(asp.atoms(model, "item"))
    python_items = {(k,) for k in ITEMS.keys()}
    if items == python_items:
        print(f"OK: ASP facts match Python registries ({len(items)} items).")
        return 0
    print("MISMATCH between ASP and Python item registries.")
    print("  only in ASP:", sorted(items - python_items))
    print("  only in Python:", sorted(python_items - items))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    companion_type = args.companion_type or rng.choice(["aunt", "uncle", "mother", "father", "girl", "boy"])
    companion_name = args.companion_name or rng.choice(COMPANION_NAMES)
    item = args.item or "anklet"
    return StoryParams(
        setting=setting,
        detective_name=detective_name,
        detective_type=detective_type,
        companion_name=companion_name,
        companion_type=companion_type,
        item=item,
    )


def _make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        traits=["careful", "curious"],
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion_type,
        label=params.companion_name,
        traits=["worried", "patient"],
    ))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=params.item,
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=companion.id,
        hidden_in=item_cfg["hidden_in"],
    ))
    world.facts.update(detective=detective, companion=companion, item=item, mystery=Mystery(
        id="m1",
        missing_item=params.item,
        item_phrase=item_cfg["phrase"],
        item_type=params.item,
        clue_room="study",
        culprit="no culprit",
        mistaken_opinion="",
        true_location=item_cfg["hidden_in"],
        suspense_line="",
        resolution_line="",
    ))
    return world


def _story_text(world: World) -> str:
    d: Entity = world.facts["detective"]
    c: Entity = world.facts["companion"]
    item: Entity = world.facts["item"]
    setting = world.setting.place

    world.say(f"{d.label} was a careful little detective who loved looking for small clues.")
    world.say(f"One afternoon at {setting}, {c.label} showed {d.pronoun('object')} a troublesome {item.label} and frowned.")
    world.say(f'"I thought I left {item.it()} on the table," {c.label} said, "but now it is gone."')
    world.para()
    world.say(f"{d.label} looked around the hall, the kitchen, and the study with a serious face.")
    world.say(f"A thin ribbon lay near the study door, and that made the first opinion feel suspicious.")
    world.say(f"{c.label} guessed that someone must have taken the {item.label}, and the house felt very quiet all at once.")
    world.para()
    world.say(f"{d.label} listened to the silence, then followed the clue to the study drawer.")
    world.say(f"Inside, the tiny silver {item.label} sat in a nest of papers, caught on a pencil and a string.")
    world.say(f"It was not stolen at all; the real trouble was a misunderstanding, and the forgotten drawer had been hiding the truth.")
    world.para()
    world.say(f"{c.label} gave a relieved laugh, and {d.label} gently untangled the {item.label}.")
    world.say(f"In the end, the anklet was safe, the troublesome mix-up was solved, and the room felt bright again.")
    world.facts["mystery"].mistaken_opinion = f"{c.label} thought someone had taken the anklet."
    world.facts["mystery"].suspense_line = "The house felt very quiet all at once."
    world.facts["mystery"].resolution_line = "The anklet was hidden in the study drawer."
    return world.render()


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    story = _story_text(world)
    detective: Entity = world.facts["detective"]
    companion: Entity = world.facts["companion"]
    item: Entity = world.facts["item"]

    prompts = [
        f"Write a short detective story for a young child about a troublesome {item.label} and a misunderstanding.",
        f"Tell a suspenseful story where {detective.label} finds out why {companion.label} made the wrong opinion about the missing {item.label}.",
        f"Write a gentle mystery set at {world.setting.place} that ends with the {item.label} being found.",
    ]

    story_qa = [
        QAItem(
            question=f"Who solved the mystery about the missing {item.label}?",
            answer=f"{detective.label} solved it by checking the rooms carefully and following the clue to the study drawer.",
        ),
        QAItem(
            question=f"Why did {companion.label} think the {item.label} was gone for good?",
            answer=f"{companion.label} saw it was missing from the table and made a quick opinion before looking in the drawer.",
        ),
        QAItem(
            question=f"Where was the troublesome {item.label} found at the end?",
            answer=f"It was found in the study drawer, caught in papers with a pencil and a string.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The rooms were checked one by one, the house went quiet, and nobody knew where the {item.label} had gone until the clue was followed.",
        ),
        QAItem(
            question=f"What misunderstanding got fixed?",
            answer=f"The misunderstanding was the belief that someone had taken the {item.label}, when it had really slipped into the study drawer.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is an anklet?",
            answer="An anklet is a small piece of jewelry worn around the ankle.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding is when someone gets the wrong idea because they do not have all the facts yet.",
        ),
    ]

    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.label:
                bits.append(f"label={e.label}")
            if e.phrase:
                bits.append(f"phrase={e.phrase}")
            if e.hidden_in:
                bits.append(f"hidden_in={e.hidden_in}")
            if e.owner:
                bits.append(f"owner={e.owner}")
            print(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show item/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show item/1."))
        print("Compatible items:")
        for atom in sorted(set(asp.atoms(model, "item"))):
            print(atom[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="house", detective_name="Maya", detective_type="girl", companion_name="Aunt June", companion_type="aunt", item="anklet"),
            StoryParams(setting="apartment", detective_name="Leo", detective_type="boy", companion_name="Rosa", companion_type="girl", item="anklet"),
            StoryParams(setting="museum", detective_name="Ivy", detective_type="girl", companion_name="Mr. Clay", companion_type="uncle", item="anklet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.detective_name}: {p.item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
