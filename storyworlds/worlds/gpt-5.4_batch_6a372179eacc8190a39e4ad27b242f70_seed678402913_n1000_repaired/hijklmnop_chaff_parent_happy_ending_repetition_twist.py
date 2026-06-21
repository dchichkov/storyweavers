#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hijklmnop_chaff_parent_happy_ending_repetition_twist.py
===================================================================================

A standalone storyworld for a small folk-tale domain built from the seed words
"hijklmnop", "chaff", and "parent".

Premise
-------
A child helps a parent after harvest and keeps asking why anyone would save the
light, dusty chaff instead of the shining grain. The parent gives the same calm
answer each time. When cold night comes, a young animal needs warm bedding, and
the twist is that the "useless" chaff becomes exactly the thing that helps.

Narrative features
------------------
* Happy Ending: the animal is safe and warm, and the child understands.
* Repetition: the child asks the same kind of question three times, and the
  parent answers with the same proverb-like line.
* Twist: the bright grain is not the hero of the tale; the humble chaff is.

Run it
------
python storyworlds/worlds/gpt-5.4/hijklmnop_chaff_parent_happy_ending_repetition_twist.py
python storyworlds/worlds/gpt-5.4/hijklmnop_chaff_parent_happy_ending_repetition_twist.py --all
python storyworlds/worlds/gpt-5.4/hijklmnop_chaff_parent_happy_ending_repetition_twist.py --qa
python storyworlds/worlds/gpt-5.4/hijklmnop_chaff_parent_happy_ending_repetition_twist.py --verify
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)


@dataclass
class Crop:
    id: str
    label: str
    grain: str
    straw_color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalKind:
    id: str
    label: str
    child_word: str
    cry: str
    shelter_types: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ShelterKind:
    id: str
    label: str
    phrase: str
    floor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    crop: str
    animal: str
    shelter: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


CROPS = {
    "wheat": Crop(
        id="wheat",
        label="wheat",
        grain="wheat grain",
        straw_color="golden",
        tags={"harvest", "grain"},
    ),
    "barley": Crop(
        id="barley",
        label="barley",
        grain="barley grain",
        straw_color="pale gold",
        tags={"harvest", "grain"},
    ),
    "oats": Crop(
        id="oats",
        label="oats",
        grain="oat grain",
        straw_color="soft tan",
        tags={"harvest", "grain"},
    ),
}

ANIMALS = {
    "chick": AnimalKind(
        id="chick",
        label="chick",
        child_word="little chick",
        cry="peep-peep",
        shelter_types={"coop", "basket"},
        tags={"chick", "bedding"},
    ),
    "lamb": AnimalKind(
        id="lamb",
        label="lamb",
        child_word="little lamb",
        cry="maa",
        shelter_types={"pen", "stall"},
        tags={"lamb", "bedding"},
    ),
    "kid": AnimalKind(
        id="kid",
        label="kid goat",
        child_word="little kid goat",
        cry="maa-maa",
        shelter_types={"pen", "stall"},
        tags={"goat", "bedding"},
    ),
}

SHELTERS = {
    "coop": ShelterKind(
        id="coop",
        label="coop",
        phrase="the little coop by the fence",
        floor="the bare boards",
        tags={"coop", "farm"},
    ),
    "basket": ShelterKind(
        id="basket",
        label="basket",
        phrase="the wicker basket by the warm wall",
        floor="the hard basket bottom",
        tags={"basket", "farm"},
    ),
    "pen": ShelterKind(
        id="pen",
        label="pen",
        phrase="the small pen under the shed roof",
        floor="the cold packed earth",
        tags={"pen", "farm"},
    ),
    "stall": ShelterKind(
        id="stall",
        label="stall",
        phrase="the corner stall beside the old cart",
        floor="the chilly floorboards",
        tags={"stall", "farm"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Anya", "Ella", "Rina", "May"]
BOY_NAMES = ["Tobin", "Milo", "Finn", "Evan", "Ned", "Rowan", "Ivo", "Ben"]

KNOWLEDGE = {
    "chaff": [
        (
            "What is chaff?",
            "Chaff is the light, papery part around grain that blows away when people clean a harvest. It is not good for bread, but it can still be useful.",
        )
    ],
    "harvest": [
        (
            "What happens after a harvest?",
            "After a harvest, people often dry and clean the grain so it can be stored and used for food. The grain is kept, and the loose chaff is separated from it.",
        )
    ],
    "grain": [
        (
            "Why do people save grain?",
            "Grain can be ground or cooked for food, so families save it carefully. It helps feed people through the year.",
        )
    ],
    "bedding": [
        (
            "Why do young animals need bedding?",
            "Young animals lose warmth quickly when they lie on a cold floor. Soft, dry bedding helps keep their bodies warm and comfortable.",
        )
    ],
    "chick": [
        (
            "What sound does a chick make?",
            "A chick often makes small peeping sounds. Its tiny voice can mean it is calling, hungry, or cold.",
        )
    ],
    "lamb": [
        (
            "Why does a lamb need shelter at night?",
            "A lamb is young and small, so cold wind can trouble it quickly. Shelter and dry bedding help it rest safely.",
        )
    ],
    "goat": [
        (
            "What is a kid goat?",
            "A kid goat is a young goat. Like other baby animals, it needs warmth, food, and a safe place to rest.",
        )
    ],
}
KNOWLEDGE_ORDER = ["chaff", "harvest", "grain", "bedding", "chick", "lamb", "goat"]


def valid_combo(crop_id: str, animal_id: str, shelter_id: str) -> bool:
    if crop_id not in CROPS or animal_id not in ANIMALS or shelter_id not in SHELTERS:
        return False
    return shelter_id in ANIMALS[animal_id].shelter_types


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for crop_id in CROPS:
        for animal_id, animal in ANIMALS.items():
            for shelter_id in SHELTERS:
                if shelter_id in animal.shelter_types:
                    out.append((crop_id, animal_id, shelter_id))
    return sorted(out)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def note(self, item: str) -> None:
        self.history.append(item)


def introduce(world: World, child: Entity, parent: Entity, crop: Crop) -> None:
    world.say(
        f"In the season when the fields had gone quiet, {child.id} worked beside {child.pronoun('possessive')} {parent.label_word} in a yard full of {crop.straw_color} {crop.label}."
    )
    world.say(
        f"As {child.pronoun()} tossed the harvest in a flat tray, the bright kernels fell back with a soft patter and the light chaff rose in the breeze."
    )
    child.memes["joy"] += 1
    world.note("harvest_work")


def alphabet_song(world: World, child: Entity) -> None:
    child.memes["playfulness"] += 1
    world.say(
        f'To keep the rhythm, {child.id} sang, "hijklmnop, hijklmnop," as if those letters were a tiny field-song of {child.pronoun("possessive")} own.'
    )
    world.note("sang_hijklmnop")


def save_chaff(world: World, parent: Entity) -> None:
    basket = world.get("chaff")
    basket.meters["saved"] += 1
    world.say(
        f"But {parent.label_word.capitalize()} did not let the chaff fly away. {parent.pronoun().capitalize()} caught it in a willow basket and set the basket by the door."
    )
    world.note("saved_chaff")


def repeated_question(world: World, child: Entity, parent: Entity, idx: int) -> None:
    basket = world.get("chaff")
    child.memes["wonder"] += 1
    basket.memes["doubted"] += 1
    lines = {
        1: f'"Why keep the chaff?" asked {child.id}. "The grain is the treasure."',
        2: f'When the tray was filled again, {child.id} laughed and asked once more, "Why keep the chaff? It is only the wind\'s old feather."',
        3: f'At the doorway, seeing the basket still there, {child.id} asked for the third time, "Why keep the chaff? Surely nobody needs such light little scraps."',
    }
    world.say(lines[idx])
    world.say(
        f'"Keep even the light thing," said {parent.label_word}. "Its hour may come."'
    )
    world.facts.setdefault("repeat_count", 0)
    world.facts["repeat_count"] += 1
    world.note(f"repetition_{idx}")


def night_turn(world: World, child: Entity, parent: Entity, animal: Entity, shelter: ShelterKind) -> None:
    world.para()
    world.say(
        "By evening the wind changed. It came thin and sharp around the corners of the house, and the yard lost its warm afternoon smell."
    )
    animal.meters["cold"] += 1
    child.memes["worry"] += 1
    parent.memes["concern"] += 1
    world.say(
        f"From {shelter.phrase} came a small cry -- {animal.attrs['cry']}, {animal.attrs['cry']} -- and {child.id} ran to listen."
    )
    world.say(
        f'There lay the {animal.label} on {shelter.floor}, tucked small against the cold. "The poor dear is shivering," said {child.id}.'
    )
    world.note("animal_cold")


def twist_and_fix(world: World, child: Entity, parent: Entity, animal: Entity, shelter: ShelterKind) -> None:
    basket = world.get("chaff")
    basket.meters["used"] += 1
    basket.meters["saved"] = max(0.0, basket.meters["saved"] - 1)
    animal.meters["bedded"] += 1
    if animal.meters["cold"] >= THRESHOLD and animal.meters["bedded"] >= THRESHOLD:
        animal.meters["warm"] += 1
        animal.meters["cold"] = 0.0
    child.memes["understanding"] += 1
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    animal.memes["comfort"] += 1
    world.say(
        f"Then {parent.label_word} lifted the willow basket. {parent.pronoun().capitalize()} spread the soft chaff thick over {shelter.floor}, and the little pieces lay together like a dry, rustling quilt."
    )
    world.say(
        f"Only then did {child.id} understand the twist of the day: the shining grain would fill a sack, but the humble chaff would warm a living creature."
    )
    world.say(
        f"{child.id} knelt to help, tucked the {animal.label} into the fresh bed, and sang, very softly this time, \"hijklmnop, hijklmnop.\""
    )
    world.note("chaff_became_bedding")


def happy_ending(world: World, child: Entity, parent: Entity, animal: Entity, shelter: ShelterKind, crop: Crop) -> None:
    world.para()
    world.say(
        f"Before long, the {animal.label}'s crying faded. It curled itself into the chaff, and warmth gathered under it instead of running away through {shelter.floor}."
    )
    world.say(
        f'"Now I know," said {child.id}. "Even the light thing can have a strong heart." {parent.label_word.capitalize()} smiled, for the old saying had found its proof.'
    )
    world.say(
        f"And in the morning, when pale sun touched the yard, the {animal.label} slept safe and easy on its {crop.straw_color} bed, while the grain waited in sacks and the child no longer called the chaff useless."
    )
    world.note("happy_ending")


def tell(
    crop: Crop,
    animal_kind: AnimalKind,
    shelter_kind: ShelterKind,
    child_name: str,
    child_gender: str,
    parent_type: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            tags={"child"},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label=parent_type,
            tags={"parent"},
        )
    )
    animal = world.add(
        Entity(
            id="animal",
            kind="thing",
            type=animal_kind.id,
            label=animal_kind.child_word,
            phrase=animal_kind.label,
            attrs={"cry": animal_kind.cry},
            tags=set(animal_kind.tags),
        )
    )
    world.add(
        Entity(
            id="chaff",
            kind="thing",
            type="chaff",
            label="chaff",
            phrase="a willow basket of chaff",
            tags={"chaff", "bedding"},
        )
    )
    world.add(
        Entity(
            id="grain",
            kind="thing",
            type="grain",
            label=crop.grain,
            phrase=f"sacks of {crop.grain}",
            tags=set(crop.tags),
        )
    )

    introduce(world, child, parent, crop)
    alphabet_song(world, child)
    save_chaff(world, parent)

    world.para()
    repeated_question(world, child, parent, 1)
    repeated_question(world, child, parent, 2)
    repeated_question(world, child, parent, 3)

    night_turn(world, child, parent, animal, shelter_kind)
    twist_and_fix(world, child, parent, animal, shelter_kind)
    happy_ending(world, child, parent, animal, shelter_kind, crop)

    world.facts.update(
        child=child,
        parent=parent,
        animal=animal,
        crop=crop,
        shelter=shelter_kind,
        repeat_count=world.facts.get("repeat_count", 0),
        twist_realized=child.memes["understanding"] >= THRESHOLD,
        animal_warm=animal.meters["warm"] >= THRESHOLD,
        happy=animal.meters["warm"] >= THRESHOLD and child.memes["relief"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal = f["animal"]
    crop = f["crop"]
    return [
        'Write a folk-tale style story for a 3-to-5-year-old that includes the words "hijklmnop", "chaff", and "parent", and ends happily.',
        f"Tell a gentle harvest tale where a child named {child.id} helps a {parent.label_word}, keeps questioning a basket of chaff, and learns at night why it mattered.",
        f"Write a story with repetition and a twist: after cleaning {crop.label}, a child thinks the grain is the treasure, but the humble chaff turns out to save a cold {animal.label}.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal = f["animal"]
    crop = f["crop"]
    shelter = f["shelter"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a {animal.label} in need of care. The story begins with harvest work and ends with kindness.",
        ),
        (
            "What was the child doing at the start?",
            f"{child.id} was helping clean the {crop.label} after harvest. While the grain fell back into the tray, the chaff lifted into the air, and {child.pronoun()} sang \"hijklmnop\" to keep the work cheerful.",
        ),
        (
            "What question was repeated in the story?",
            f"The child kept asking why anyone would keep the chaff. That repeated question matters because it prepares the twist: the thing that seemed least important became the very thing that was needed.",
        ),
        (
            "Why did the parent save the chaff?",
            f"{parent.label_word.capitalize()} saved the chaff because {parent.pronoun()} believed even light things may have their hour. Later, that choice proved wise when the cold {animal.label} needed a soft, dry bed.",
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the grain was not the part that solved the night's problem. The chaff, which the child had called useless, became warm bedding for the shivering {animal.label}.",
        ),
    ]
    if f["animal_warm"]:
        qa.append(
            (
                f"How did they help the {animal.label}?",
                f"They spread the saved chaff over {shelter.floor} in {shelter.phrase}. That made a dry, soft bed, so the little animal stopped shivering and could rest warmly.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily. By morning the {animal.label} was sleeping safely on the chaff, and {child.id} had learned not to laugh at small humble things.",
            )
        )
    return qa


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    tags = {"chaff", "harvest", "grain", "bedding"} | set(world.facts["animal"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  history={world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crop="wheat",
        animal="chick",
        shelter="coop",
        child_name="Mira",
        child_gender="girl",
        parent_type="mother",
    ),
    StoryParams(
        crop="barley",
        animal="lamb",
        shelter="pen",
        child_name="Tobin",
        child_gender="boy",
        parent_type="father",
    ),
    StoryParams(
        crop="oats",
        animal="kid",
        shelter="stall",
        child_name="Lina",
        child_gender="girl",
        parent_type="mother",
    ),
    StoryParams(
        crop="wheat",
        animal="chick",
        shelter="basket",
        child_name="Finn",
        child_gender="boy",
        parent_type="father",
    ),
]


def explain_rejection(animal_id: str, shelter_id: str) -> str:
    if animal_id not in ANIMALS:
        return f"(No story: unknown animal '{animal_id}'.)"
    if shelter_id not in SHELTERS:
        return f"(No story: unknown shelter '{shelter_id}'.)"
    animal = ANIMALS[animal_id]
    shelter = SHELTERS[shelter_id]
    allowed = ", ".join(sorted(animal.shelter_types))
    return (
        f"(No story: a {animal.label} does not sensibly sleep in {shelter.phrase}. "
        f"Choose one of these shelters instead: {allowed}.)"
    )


ASP_RULES = r"""
valid(C, A, S) :- crop(C), animal(A), shelter(S), allows(A, S).
helpful_chaff(A) :- animal(A).
happy_story(C, A, S) :- valid(C, A, S), helpful_chaff(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id in CROPS:
        lines.append(asp.fact("crop", crop_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for shelter_id in sorted(animal.shelter_types):
            lines.append(asp.fact("allows", animal_id, shelter_id))
    for shelter_id in SHELTERS:
        lines.append(asp.fact("shelter", shelter_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
        except Exception as exc:
            rc = 1
            print(f"RANDOM SMOKE TEST FAILED at seed {seed}: {exc}")
            break
    if rc == 0:
        print("OK: random smoke generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a folk tale where humble chaff becomes the needed thing."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--shelter", choices=sorted(SHELTERS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.shelter and not valid_combo(
        args.crop or next(iter(CROPS)),
        args.animal,
        args.shelter,
    ):
        raise StoryError(explain_rejection(args.animal, args.shelter))

    combos = [
        combo
        for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.animal is None or combo[1] == args.animal)
        and (args.shelter is None or combo[2] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, animal_id, shelter_id = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        crop=crop_id,
        animal=animal_id,
        shelter=shelter_id,
        child_name=child_name,
        child_gender=child_gender,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crop not in CROPS:
        raise StoryError(f"(No story: unknown crop '{params.crop}'.)")
    if params.animal not in ANIMALS:
        raise StoryError(f"(No story: unknown animal '{params.animal}'.)")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(No story: unknown shelter '{params.shelter}'.)")
    if not valid_combo(params.crop, params.animal, params.shelter):
        raise StoryError(explain_rejection(params.animal, params.shelter))
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown child gender '{params.child_gender}'.)")
    if params.parent_type not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown parent type '{params.parent_type}'.)")

    world = tell(
        crop=CROPS[params.crop],
        animal_kind=ANIMALS[params.animal],
        shelter_kind=SHELTERS[params.shelter],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(asp_program("#show valid/3.\n#show happy_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (crop, animal, shelter) combos:\n")
        for crop_id, animal_id, shelter_id in combos:
            print(f"  {crop_id:8} {animal_id:6} {shelter_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.child_name}: {p.crop}, {p.animal}, {p.shelter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
