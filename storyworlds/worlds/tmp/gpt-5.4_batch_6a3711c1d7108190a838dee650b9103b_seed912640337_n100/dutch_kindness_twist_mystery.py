#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py
==========================================================

A small story world for a gentle mystery with a kindness twist.

Premise
-------
A child notices that a useful object has gone missing. There are tiny clues, a
shadowy errand, and a growing sense of mystery. In the end, the object was not
taken for meanness at all: it was borrowed for a kind surprise, and the hero
chooses generosity instead of blame.

The seed word "dutch" appears in every story as part of the little world detail:
a tiny dutch windmill magnet on the shared shelf where the missing item used to
sit.

Run it
------
    python storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py
    python storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py --setting canal_house --item tin --need bulbs
    python storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py --item umbrella --need bulbs
    python storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py --all
    python storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dutch_kindness_twist_mystery.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    shelf: str
    path: str
    reveal_place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    utility: str
    clue_mark: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    recipient_role: str
    recipient_label: str
    problem: str
    utility: str
    first_clue: str
    second_clue: str
    reveal_action: str
    help_result: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def item_fits_need(item: MissingItem, need: Need) -> bool:
    return item.utility == need.utility


def valid_in_setting(setting: Setting, need: Need) -> bool:
    return need.id in setting.affords


def valid_combo(setting: Setting, item: MissingItem, need: Need) -> bool:
    return item_fits_need(item, need) and valid_in_setting(setting, need)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for nid, need in NEEDS.items():
                if valid_combo(setting, item, need):
                    out.append((sid, iid, nid))
    return out


def predict_kindness(item: MissingItem, need: Need) -> dict:
    useful = item_fits_need(item, need)
    return {
        "useful": useful,
        "comfort": 1 if useful else 0,
    }


def propagate(world: World) -> None:
    hero = world.get("hero")
    borrower = world.get("borrower")
    recipient = world.get("recipient")
    item = world.get("item")
    if borrower.meters["holding"] >= THRESHOLD and recipient.meters["need"] >= THRESHOLD:
        sig = ("prepare", item.id, recipient.id)
        if sig not in world.fired:
            world.fired.add(sig)
            borrower.memes["kindness"] += 1
            world.facts["project_ready"] = True
    if world.facts.get("clues_found", 0) >= 2:
        sig = ("mystery", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["curiosity"] += 1
            hero.memes["suspicion"] += 1
    if world.facts.get("revealed"):
        sig = ("reveal", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["suspicion"] = 0.0
            hero.memes["relief"] += 1
            hero.memes["kindness"] += 1
            recipient.meters["need"] = 0.0
            recipient.meters["comfort"] += 1


def opening(world: World, setting: Setting, hero: Entity, helper: Entity, item: MissingItem) -> None:
    hero.memes["calm"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"After school, {hero.id} and {helper.id} padded into {setting.place}. "
        f"On {setting.shelf} sat a tiny dutch windmill magnet, a bowl of keys, "
        f"and usually {item.phrase}."
    )
    world.say(
        f"But that afternoon the space beside the magnet was empty, and the empty space "
        f"looked almost louder than the hallway itself."
    )


def notice_missing(world: World, hero: Entity, item: MissingItem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"{item.label.capitalize()} is gone," {hero.id} whispered. '
        f"{hero.pronoun().capitalize()} looked around as if the walls might answer."
    )


def first_clue(world: World, helper: Entity, need: Need) -> None:
    world.facts["clues_found"] = world.facts.get("clues_found", 0) + 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.id} pointed to {need.first_clue}. It was such a small clue that it made the mystery feel bigger."
    )
    propagate(world)


def guess(world: World, hero: Entity, helper: Entity, item: MissingItem, need: Need) -> None:
    pred = predict_kindness(item, need)
    world.facts["predicted_useful"] = pred["useful"]
    hero.memes["suspicion"] += 1
    if pred["useful"]:
        world.say(
            f'"Maybe someone borrowed it for a reason," {helper.id} said softly. '
            f'"{item.label.capitalize()} could really help with that sort of problem."'
        )
    else:
        world.say(
            f'"I cannot think why anyone would take it," {helper.id} said softly, and the mystery felt colder.'
        )


def second_clue(world: World, setting: Setting, need: Need) -> None:
    world.facts["clues_found"] = world.facts.get("clues_found", 0) + 1
    world.say(
        f"They followed {setting.path} and found {need.second_clue}. Now the clue trail was too neat to be an accident."
    )
    propagate(world)


def approach_reveal(world: World, setting: Setting, hero: Entity) -> None:
    world.say(
        f"At the door of {setting.reveal_place}, {hero.id} held still for one breath. "
        f"The room on the other side was quiet enough to feel secret."
    )


def reveal(world: World, setting: Setting, hero: Entity, helper: Entity,
           borrower: Entity, recipient: Entity, item: MissingItem, need: Need) -> None:
    world.facts["revealed"] = True
    propagate(world)
    world.say(
        f"Then the door opened, and there was the twist: not a thief at all, but {borrower.id}, "
        f"carefully using {item.phrase}. {need.reveal_action}"
    )
    world.say(
        f"{recipient.label.capitalize()} looked up in surprise. The missing thing had become part of a kindness."
    )
    hero.memes["wonder"] += 1
    helper.memes["relief"] += 1


def kind_choice(world: World, hero: Entity, borrower: Entity, item: MissingItem, need: Need) -> None:
    borrower.memes["worry"] += 1
    world.say(
        f'"I meant to put it back before anyone worried," {borrower.id} said. '
        f'"I only needed {item.label} because {need.problem}."'
    )
    world.say(
        f"For a moment, {hero.id} remembered the empty shelf and the spooky feeling in the hall. "
        f"Then {hero.pronoun()} saw the careful hands and the shy face in front of {hero.pronoun('object')}."
    )
    hero.memes["kindness"] += 1
    borrower.memes["relief"] += 1
    world.say(
        f'"Next time, you can ask me," {hero.id} said. "But we can finish helping now."'
    )


def resolution(world: World, hero: Entity, helper: Entity, borrower: Entity,
               recipient: Entity, item: MissingItem, need: Need) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    borrower.memes["joy"] += 1
    recipient.memes["gratitude"] += 1
    recipient.meters["comfort"] += 1
    world.say(
        f"Together they finished the small job. {need.help_result}"
    )
    world.say(
        f"When {item.phrase} finally went back to its place, it no longer looked lost. "
        f"It looked important."
    )
    world.say(
        f"That evening, {need.ending_image}"
    )


def tell(setting: Setting, item: MissingItem, need: Need,
         hero_name: str = "Mila", hero_type: str = "girl",
         helper_name: str = "Daan", helper_type: str = "boy",
         borrower_name: str = "Saar", borrower_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    borrower = world.add(Entity(id=borrower_name, kind="character", type=borrower_type, role="borrower", label=borrower_name))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=need.recipient_role,
        role="recipient",
        label=need.recipient_label,
    ))
    item_ent = world.add(Entity(id="item", type="item", label=item.label, role="item"))
    item_ent.meters["missing"] += 1
    borrower.meters["holding"] += 1
    recipient.meters["need"] += 1

    world.facts.update(
        setting=setting,
        item_cfg=item,
        need_cfg=need,
        hero=hero,
        helper=helper,
        borrower=borrower,
        recipient=recipient,
        clues_found=0,
        revealed=False,
        project_ready=False,
    )

    opening(world, setting, hero, helper, item)
    notice_missing(world, hero, item)

    world.para()
    first_clue(world, helper, need)
    guess(world, hero, helper, item, need)
    second_clue(world, setting, need)

    world.para()
    approach_reveal(world, setting, hero)
    reveal(world, setting, hero, helper, borrower, recipient, item, need)
    kind_choice(world, hero, borrower, item, need)

    world.para()
    resolution(world, hero, helper, borrower, recipient, item, need)
    return world


SETTINGS = {
    "canal_house": Setting(
        "canal_house",
        "the hallway of their tall canal house",
        "the painted hall shelf under the stairs",
        "the narrow stairs past the coats and the old clock",
        "the glass back room",
        affords={"bulbs", "rain"},
    ),
    "school": Setting(
        "school",
        "the quiet corridor beside the school library",
        "the class sharing shelf by the reading rug",
        "the soft corridor past the art table and the music room",
        "the little garden shed",
        affords={"bulbs", "stairs"},
    ),
    "courtyard": Setting(
        "courtyard",
        "the echoey entry hall by the courtyard door",
        "the wooden bench shelf near the mailboxes",
        "the brick passage beside the bicycles and potted herbs",
        "the covered courtyard nook",
        affords={"rain", "stairs"},
    ),
}

ITEMS = {
    "tin": MissingItem(
        "tin",
        "round tin",
        "a round blue tin painted with windmills",
        "container",
        "a pinch of dry soil and one papery tulip skin",
        "it could hold small things without losing them",
        tags={"tin", "bulbs"},
    ),
    "umbrella": MissingItem(
        "umbrella",
        "yellow umbrella",
        "a bright yellow umbrella with a curved handle",
        "cover",
        "three silver drops on the floor and a folded strap hanging loose",
        "it could keep someone dry on the walk home",
        tags={"umbrella", "rain"},
    ),
    "lantern": MissingItem(
        "lantern",
        "little lantern",
        "a little battery lantern with a pearly handle",
        "light",
        "a tiny warm glow peeking under a door and one fresh battery box",
        "it could make a dark place feel safe",
        tags={"lantern", "stairs"},
    ),
}

NEEDS = {
    "bulbs": Need(
        "bulbs",
        "grandfather",
        "Mr. Vos",
        "Mr. Vos needed a safe place to sort his tulip bulbs for the school bed",
        "container",
        "a pinch of dry soil and one papery tulip skin on the shelf",
        "a trail of soil dots leading toward the quiet room at the back",
        "Beside him lay neat rows of tulip bulbs, and the tin held them in little careful piles",
        "The bulbs were sorted, labeled, and ready for planting, and Mr. Vos smiled as if spring had already arrived",
        "the windmill tin rested back on the shelf, while outside the first dark earth waited for bright tulips",
        tags={"bulbs", "garden"},
    ),
    "rain": Need(
        "rain",
        "woman",
        "Mrs. Noor",
        "Mrs. Noor had to walk medicine across the courtyard in the rain",
        "cover",
        "three silver drops and the mark of a wet handle on the bench",
        "soft wet footprints leading toward the covered nook",
        "Mrs. Noor was tucking a small paper medicine packet under the yellow umbrella",
        "The packet stayed dry, and Mrs. Noor could carry it safely to her neighbor without it turning limp",
        "the umbrella hung back by the door, still bright, while rain tapped the windows like a secret that had turned friendly",
        tags={"rain", "umbrella"},
    ),
    "stairs": Need(
        "stairs",
        "grandmother",
        "Oma Lena",
        "Oma Lena was afraid of the dim cellar steps where the jam jars were kept",
        "light",
        "a soft bead of light under the storeroom door and one fresh battery wrapper nearby",
        "a ribbon of warm light trembling along the floor toward the little nook",
        "Oma Lena was smiling at the steps while the lantern glowed beside the jars",
        "The dark steps no longer felt scary, and Oma Lena could carry the jars up safely without guessing where to put her feet",
        "the little lantern glimmered on the shelf again, and even the shadows seemed gentler than before",
        tags={"stairs", "lantern"},
    ),
}

GIRL_NAMES = ["Mila", "Lotte", "Nina", "Ava", "Sara", "Evi", "Roos", "Emma"]
BOY_NAMES = ["Daan", "Mats", "Finn", "Noah", "Lars", "Bram", "Timo", "Sem"]


@dataclass
class StoryParams:
    setting: str
    item: str
    need: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    borrower: str
    borrower_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mystery": [(
        "What is a mystery?",
        "A mystery is something you do not understand yet, so you look for clues and ask careful questions."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help someone or make life easier for them. It often means noticing what another person needs."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. It can point your thinking in the right direction."
    )],
    "bulbs": [(
        "What is a tulip bulb?",
        "A tulip bulb is the round part planted in the soil that grows into a tulip flower later."
    )],
    "umbrella": [(
        "What does an umbrella do?",
        "An umbrella opens over your head to keep rain off you and the things you are carrying."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light you can carry from place to place. A battery lantern gives light without a flame."
    )],
    "stairs": [(
        "Why can dark stairs be hard to use?",
        "Dark stairs are hard because you cannot see where each step begins and ends. Good light helps your feet move safely."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "clue", "kindness", "bulbs", "umbrella", "lantern", "stairs"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    need = f["need_cfg"]
    setting = f["setting"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "dutch" and begins when {item.phrase} goes missing in {setting.place}.',
        f"Tell a child-friendly twist story where {hero.id} follows small clues, fears something sneaky happened, and then learns the missing object was borrowed for kindness.",
        f"Write a simple mystery with a warm ending: a child searches for {item.label}, discovers {need.problem}, and chooses help over blame.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    borrower = f["borrower"]
    recipient = f["recipient"]
    item = f["item_cfg"]
    need = f["need_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {helper.id}, and {borrower.id}, plus {recipient.label}. "
            f"They are all part of one small mystery in {setting.place}."
        ),
        (
            f"What was missing at the start?",
            f"{item.phrase.capitalize()} was missing from {setting.shelf}. That empty place is what started the mystery."
        ),
        (
            "What clues did the children find?",
            f"They found {need.first_clue}, and later they found {need.second_clue}. "
            f"Those clues showed that the object had been moved on purpose, not simply forgotten."
        ),
        (
            f"Why did {hero.id} think something strange had happened?",
            f"{hero.id} saw the empty shelf and the clue trail, so the hall felt secret and suspicious. "
            f"The clues made the missing object seem like part of a hidden plan."
        ),
        (
            "What was the twist?",
            f"The twist was that nobody had stolen the missing thing. {borrower.id} had borrowed it to help because {need.problem}."
        ),
        (
            f"How did the mystery end?",
            f"It ended kindly. {hero.id} chose to help finish the job, and {need.help_result.lower()}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "clue", "kindness"} | set(world.facts["item_cfg"].tags) | set(world.facts["need_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("canal_house", "tin", "bulbs", "Mila", "girl", "Daan", "boy", "Saar", "girl"),
    StoryParams("courtyard", "umbrella", "rain", "Lotte", "girl", "Finn", "boy", "Bram", "boy"),
    StoryParams("school", "lantern", "stairs", "Noah", "boy", "Evi", "girl", "Roos", "girl"),
]


def explain_rejection(item: MissingItem, need: Need, setting: Setting) -> str:
    if not item_fits_need(item, need):
        return (
            f"(No story: {item.label} helps with {item.utility}, but this problem needs "
            f"{need.utility}. The missing object must plausibly solve the hidden kindness.)"
        )
    return (
        f"(No story: {setting.place} does not support this kind surprise. "
        f"Pick a setting where {need.problem.lower()} could happen.)"
    )


ASP_RULES = r"""
fits(I, N) :- item_utility(I, U), need_utility(N, U).
valid(S, I, N) :- setting(S), item(I), need(N), fits(I, N), affords(S, N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_utility", iid, item.utility))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_utility", nid, need.utility))
    for sid, setting in SETTINGS.items():
        for nid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, nid))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if "dutch" not in sample.story.lower():
            raise StoryError('Story did not include required seed word "dutch".')
        print("OK: smoke-tested random resolve_params() generation.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle mystery story world with a kindness twist. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--borrower")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.need:
        if not valid_combo(SETTINGS[args.setting], ITEMS[args.item], NEEDS[args.need]):
            raise StoryError(explain_rejection(ITEMS[args.item], NEEDS[args.need], SETTINGS[args.setting]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.item is None or c[1] == args.item)
        and (args.need is None or c[2] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, item, need = rng.choice(sorted(combos))

    used: set[str] = set()
    if args.hero:
        hero = args.hero
        hero_gender = "girl" if hero in GIRL_NAMES else "boy"
    else:
        hero, hero_gender = _pick_name(rng, used)
    used.add(hero)

    if args.helper:
        helper = args.helper
        helper_gender = "girl" if helper in GIRL_NAMES else "boy"
    else:
        helper, helper_gender = _pick_name(rng, used)
    used.add(helper)

    if args.borrower:
        borrower = args.borrower
        borrower_gender = "girl" if borrower in GIRL_NAMES else "boy"
    else:
        borrower, borrower_gender = _pick_name(rng, used)

    return StoryParams(
        setting=setting,
        item=item,
        need=need,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        borrower=borrower,
        borrower_gender=borrower_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        NEEDS[params.need],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.borrower,
        params.borrower_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, need) combos:\n")
        for setting, item, need in combos:
            print(f"  {setting:12} {item:9} {need}")
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
            header = f"### {p.hero}: {p.item} / {p.need} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
