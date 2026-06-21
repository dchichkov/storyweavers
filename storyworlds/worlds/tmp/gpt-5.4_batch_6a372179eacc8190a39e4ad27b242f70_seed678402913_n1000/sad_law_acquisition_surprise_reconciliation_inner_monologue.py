#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py
==========================================================================================

A small standalone storyworld about woodland animals, a found object, and the
forest's lost-and-found law. The seed words are woven into the world itself:
someone feels sad, a community law guides the conflict, and the found object is
treated as an exciting acquisition before the finder learns why fairness matters.

This world aims for gentle Animal Story variants with:
- a clear beginning: a found thing during play,
- a state-driven middle: temptation, hiding or reporting, and a clue,
- a turn with inner monologue and surprise,
- a reconciliation ending that proves the relationship changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py --item bell --owner fox
    python storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py --item crown --owner hedgehog
    python storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sad_law_acquisition_surprise_reconciliation_inner_monologue.py --verify
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

# Make the shared result containers importable when this script is run directly.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
WORLDS_DIR = os.path.dirname(THIS_DIR)
PACKAGE_DIR = os.path.dirname(WORLDS_DIR)
sys.path.insert(0, PACKAGE_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"rabbit", "hen", "squirrel", "goose"}
        male = {"fox", "badger", "bear", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    detail: str
    law_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    clue: str
    use_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairPlan:
    id: str
    sense: int
    text: str
    qa_text: str
    needs_helper: bool = False
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hidden_guilt(world: World) -> list[str]:
    finder = world.entities.get("finder")
    item = world.entities.get("item")
    if not finder or not item:
        return []
    if item.owner == finder.id:
        return []
    if finder.memes["hid_item"] < THRESHOLD:
        return []
    sig = ("hidden_guilt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    finder.memes["guilt"] += 1
    return ["__guilt__"]


def _r_owner_sad(world: World) -> list[str]:
    owner = world.entities.get("owner")
    item = world.entities.get("item")
    if not owner or not item:
        return []
    if item.owner != owner.id:
        return []
    if item.attrs.get("returned"):
        return []
    if item.attrs.get("reported") or item.attrs.get("hidden"):
        sig = ("owner_sad",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        owner.memes["sad"] += 1
        return ["__sad__"]
    return []


def _r_return_relief(world: World) -> list[str]:
    owner = world.entities.get("owner")
    finder = world.entities.get("finder")
    item = world.entities.get("item")
    if not owner or not finder or not item:
        return []
    if not item.attrs.get("returned"):
        return []
    sig = ("return_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    finder.memes["relief"] += 1
    finder.memes["kindness"] += 1
    owner.memes["forgiveness"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="hidden_guilt", tag="emotional", apply=_r_hidden_guilt),
    Rule(name="owner_sad", tag="emotional", apply=_r_owner_sad),
    Rule(name="return_relief", tag="social", apply=_r_return_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the clover meadow",
        detail="where buttercups nodded and grasshoppers sprang out of the grass",
        law_spot="the smooth stump beside the path",
        tags={"meadow", "forest_law"},
    ),
    "brook": Place(
        id="brook",
        label="the singing brook",
        detail="where cool water slipped around round stones",
        law_spot="the flat stone by the alder roots",
        tags={"brook", "forest_law"},
    ),
    "orchard": Place(
        id="orchard",
        label="the old orchard",
        detail="where wind-shaken apples made soft thumps in the grass",
        law_spot="the mossy crate near the gate",
        tags={"orchard", "forest_law"},
    ),
}

ITEMS = {
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="a tiny silver bell on a blue string",
        clue="the blue string was braided in the neat fox-knot everyone knew",
        use_by={"fox", "goose", "rabbit"},
        tags={"bell", "lost_and_found"},
    ),
    "scarf": ItemCfg(
        id="scarf",
        label="scarf",
        phrase="a striped scarf as soft as thistledown",
        clue="one corner was stitched with careful squirrel-leaf marks",
        use_by={"squirrel", "fox", "badger"},
        tags={"scarf", "lost_and_found"},
    ),
    "crown": ItemCfg(
        id="crown",
        label="flower crown",
        phrase="a daisy flower crown still fresh with dew",
        clue="three glossy goose feathers were tucked into the side",
        use_by={"goose", "rabbit", "fox"},
        tags={"crown", "lost_and_found"},
    ),
    "satchel": ItemCfg(
        id="satchel",
        label="satchel",
        phrase="a little acorn satchel with a leaf-shaped clasp",
        clue="inside was a map scratched in badger's blocky paw-writing",
        use_by={"badger", "mole", "fox"},
        tags={"satchel", "lost_and_found"},
    ),
}

PLANS = {
    "ask_owl": RepairPlan(
        id="ask_owl",
        sense=3,
        text="carry the found thing straight to Old Owl, keeper of the Lost-and-Found Law",
        qa_text="brought the item to Old Owl so the law could help find the owner",
        needs_helper=True,
        tags={"owl", "law", "reconciliation"},
    ),
    "wait_at_law_spot": RepairPlan(
        id="wait_at_law_spot",
        sense=2,
        text="place the item at the forest law spot and wait there politely until sunset",
        qa_text="set the item at the forest law spot and waited for the owner",
        needs_helper=False,
        tags={"law", "reconciliation"},
    ),
    "hide_in_nest": RepairPlan(
        id="hide_in_nest",
        sense=1,
        text="hide the object in a leafy nook and hope nobody asks about it",
        qa_text="hid the item instead of following the law",
        needs_helper=False,
        tags={"hiding"},
    ),
}

ANIMALS = {
    "rabbit": {"name_pool": ["Pip", "Mimi", "Clover"], "traits": ["quick", "gentle"]},
    "fox": {"name_pool": ["Rufus", "Fern", "Tawny"], "traits": ["bright", "nimble"]},
    "squirrel": {"name_pool": ["Nutmeg", "Poppy", "Tilla"], "traits": ["busy", "careful"]},
    "badger": {"name_pool": ["Bruno", "Moss", "Patch"], "traits": ["steady", "quiet"]},
    "goose": {"name_pool": ["Gilda", "Pebble", "Sunny"], "traits": ["proud", "honest"]},
    "mole": {"name_pool": ["Milo", "Dibble", "Root"], "traits": ["thoughtful", "soft"]},
}

ALL_ANIMALS = sorted(ANIMALS.keys())


def owner_can_own(item: ItemCfg, owner_type: str) -> bool:
    return owner_type in item.use_by


def sensible_plans() -> list[RepairPlan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in ITEMS.items():
            for finder in ALL_ANIMALS:
                for owner in ALL_ANIMALS:
                    if finder == owner:
                        continue
                    if owner_can_own(item, owner):
                        combos.append((place_id, item_id, finder, owner))
    return combos


def explain_owner_mismatch(item: ItemCfg, owner: str) -> str:
    allowed = ", ".join(sorted(item.use_by))
    return (
        f"(No story: {item.phrase} is not a good fit for a {owner}. "
        f"This world only gives that item to plausible owners: {allowed}.)"
    )


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). Try a lawful repair such as {better}.)"
    )


def predict_owner_sad(choice: str) -> bool:
    return choice in {"hide", "report"}


def outcome_of(params: "StoryParams") -> str:
    if params.choice == "report":
        return "lawful_return"
    return "confessed_return"


@dataclass
class StoryParams:
    place: str
    item: str
    finder: str
    owner: str
    plan: str
    choice: str
    finder_name: str
    owner_name: str
    owl_name: str = "Old Owl"
    seed: Optional[int] = None


def _make_animal(animal_type: str, name: str, role: str) -> Entity:
    traits = list(ANIMALS[animal_type]["traits"])
    return Entity(
        id=role,
        kind="character",
        type=animal_type,
        label=name,
        phrase=name,
        role=role,
        traits=traits,
        tags={animal_type},
    )


def opening(world: World, place: Place, finder: Entity, item: ItemCfg) -> None:
    finder.memes["joy"] += 1
    world.say(
        f"One bright morning in {place.label}, {finder.label} the {finder.type} "
        f"trotted under the hedges, {place.detail}."
    )
    world.say(
        f"Near the path, {finder.pronoun()} spotted {item.phrase}. It glittered "
        f"so prettily that it felt, for one small breath, like a marvelous acquisition."
    )


def law_beat(world: World, place: Place, finder: Entity) -> None:
    finder.memes["duty"] += 1
    world.say(
        f"In that part of the woods, everyone knew the Lost-and-Found Law: a found "
        f"thing must be shown at {place.law_spot} or taken to Old Owl before sunset."
    )


def inner_monologue_greedy(world: World, finder: Entity, item: ItemCfg) -> None:
    finder.memes["temptation"] += 1
    world.say(
        f'{finder.label} touched the {item.label} and thought, '
        f'"It is so lovely. If nobody saw me find it, perhaps it could be mine."'
    )


def hide_item(world: World, finder: Entity, item_ent: Entity) -> None:
    item_ent.attrs["hidden"] = True
    finder.memes["hid_item"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {finder.label} tucked it into a ferny hollow and tried to skip away as if nothing had happened."
    )


def report_item(world: World, place: Place, finder: Entity, item_ent: Entity, plan: RepairPlan) -> None:
    item_ent.attrs["reported"] = True
    finder.memes["honesty"] += 1
    propagate(world, narrate=False)
    if plan.id == "ask_owl":
        world.say(
            f"But {finder.label} shook {finder.pronoun('possessive')} head, remembered the law, "
            f"and decided to {plan.text}."
        )
    else:
        world.say(
            f"But {finder.label} remembered the law and chose to {plan.text} at {place.law_spot}."
        )


def owner_search(world: World, owner: Entity, item: ItemCfg) -> None:
    propagate(world, narrate=False)
    owner.memes["care"] += 1
    world.say(
        f"Before long, {owner.label} the {owner.type} came hurrying past with worried eyes. "
        f'"Has anyone seen my {item.label}?" {owner.pronoun()} asked.'
    )
    if owner.memes["sad"] >= THRESHOLD:
        world.say(
            f"{owner.label}'s voice sounded small and sad. {owner.pronoun().capitalize()} had been looking everywhere."
        )


def surprise_clue(world: World, finder: Entity, owner: Entity, item: ItemCfg) -> None:
    finder.memes["realization"] += 1
    world.say(
        f"Then {finder.label} noticed something {finder.pronoun()} had missed before: {item.clue}."
    )
    world.say(
        f"All at once, the surprise landed in {finder.pronoun('possessive')} chest. "
        f"The found thing was not a treasure dropped by nobody at all. It belonged to {owner.label}."
    )


def inner_monologue_guilty(world: World, finder: Entity, owner: Entity) -> None:
    finder.memes["guilt"] += 1
    world.say(
        f'{finder.label} thought, "Oh dear. I wanted a lovely thing, but I have made '
        f'{owner.label} feel sad. The law was trying to keep this very hurt from happening."'
    )


def confess(world: World, finder: Entity, owner: Entity, item_ent: Entity, place: Place, plan: RepairPlan) -> None:
    item_ent.attrs["hidden"] = False
    item_ent.attrs["reported"] = True
    finder.memes["courage"] += 1
    propagate(world, narrate=False)
    if plan.id == "ask_owl":
        world.say(
            f"{finder.label} ran back to the ferny hollow, fetched the lost thing, and hurried to Old Owl with {owner.label}."
        )
    else:
        world.say(
            f"{finder.label} ran back to the ferny hollow, fetched the lost thing, and brought it to {place.law_spot} with {owner.label}."
        )


def reunion(world: World, finder: Entity, owner: Entity, item_ent: Entity, plan: RepairPlan) -> None:
    item_ent.attrs["returned"] = True
    item_ent.owner = owner.id
    propagate(world, narrate=False)
    world.say(
        f'"It is yours," {finder.label} said. "I found it, and at first I wanted to keep it. '
        f'I am sorry."'
    )
    if plan.id == "ask_owl":
        world.say(
            f"Old Owl blinked kindly and nodded. \"The law is for returning hearts as well as things,\" he said."
        )


def forgive(world: World, finder: Entity, owner: Entity, item: ItemCfg) -> None:
    owner.memes["friendship"] += 1
    finder.memes["friendship"] += 1
    world.say(
        f"{owner.label} held the {item.label} close, then looked up. "
        f'"Thank you for telling the truth," {owner.pronoun()} said. "I was upset, but I am glad you came back."'
    )


def close_story(world: World, place: Place, finder: Entity, owner: Entity, item: ItemCfg, outcome: str) -> None:
    if outcome == "lawful_return":
        world.say(
            f"That evening, the little woods felt lighter. {owner.label} skipped home with the {item.label}, "
            f"and {finder.label} learned that obeying a fair law can keep sadness from growing."
        )
    else:
        world.say(
            f"When the shadows lengthened across {place.label}, the two friends walked together instead of apart. "
            f"{finder.label} no longer wanted the bright little object nearly as much as {finder.pronoun()} wanted a clear heart."
        )


def tell(
    place: Place,
    item_cfg: ItemCfg,
    finder_type: str,
    owner_type: str,
    plan: RepairPlan,
    choice: str,
    finder_name: str,
    owner_name: str,
    owl_name: str,
) -> World:
    world = World()
    finder = world.add(_make_animal(finder_type, finder_name, "finder"))
    owner = world.add(_make_animal(owner_type, owner_name, "owner"))
    owl = world.add(Entity(
        id="owl",
        kind="character",
        type="owl",
        label=owl_name,
        phrase=owl_name,
        role="helper",
        tags={"owl", "law"},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=owner.id,
        attrs={"reported": False, "hidden": False, "returned": False},
        tags=set(item_cfg.tags),
    ))

    opening(world, place, finder, item_cfg)
    law_beat(world, place, finder)
    world.para()
    inner_monologue_greedy(world, finder, item_cfg)

    if choice == "hide":
        hide_item(world, finder, item_ent)
        world.para()
        owner_search(world, owner, item_cfg)
        surprise_clue(world, finder, owner, item_cfg)
        inner_monologue_guilty(world, finder, owner)
        world.para()
        confess(world, finder, owner, item_ent, place, plan)
        reunion(world, finder, owner, item_ent, plan)
        forgive(world, finder, owner, item_cfg)
    else:
        report_item(world, place, finder, item_ent, plan)
        world.para()
        owner_search(world, owner, item_cfg)
        surprise_clue(world, finder, owner, item_cfg)
        world.say(
            f'{finder.label} thought, "I am glad I listened quickly. The law looked strict this morning, '
            f'but really it was kind."'
        )
        world.para()
        reunion(world, finder, owner, item_ent, plan)
        forgive(world, finder, owner, item_cfg)

    outcome = outcome_of(StoryParams(
        place=place.id,
        item=item_cfg.id,
        finder=finder_type,
        owner=owner_type,
        plan=plan.id,
        choice=choice,
        finder_name=finder_name,
        owner_name=owner_name,
        owl_name=owl_name,
    ))
    close_story(world, place, finder, owner, item_cfg, outcome)
    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        finder=finder,
        owner=owner,
        owl=owl,
        plan=plan,
        choice=choice,
        outcome=outcome,
        item=item_ent,
        law_broken=(choice == "hide"),
        owner_sad=owner.memes["sad"] >= THRESHOLD,
        returned=item_ent.attrs["returned"],
        surprise_owner=owner.label,
    )
    return world


KNOWLEDGE = {
    "law": [(
        "Why might a community have a lost-and-found law?",
        "A lost-and-found law helps people return things that are missing. It keeps one animal's lucky find from becoming another animal's hurt."
    )],
    "lost_and_found": [(
        "What should you do if you find something that belongs to someone else?",
        "You should tell a trusted grown-up or follow the lost-and-found rule. That gives the owner a fair chance to get it back."
    )],
    "owl": [(
        "Why is Old Owl a good helper in this story world?",
        "Old Owl is calm and trusted by everyone. A fair helper can make it easier to tell the truth and mend a mistake."
    )],
    "reconciliation": [(
        "What does reconciliation mean?",
        "Reconciliation means becoming friendly again after hurt or trouble. It happens when someone admits the wrong, and the other side chooses to forgive."
    )],
    "bell": [(
        "What is a bell for?",
        "A bell makes a clear ringing sound. In a story, it can help others notice where someone is."
    )],
    "scarf": [(
        "What is a scarf?",
        "A scarf is a soft piece of cloth worn around the neck. It can keep you warm and can also be special because someone made it."
    )],
    "crown": [(
        "What is a flower crown?",
        "A flower crown is a ring of flowers worn on the head. It is pretty, but it is also easy to lose if you run and play."
    )],
    "satchel": [(
        "What is a satchel?",
        "A satchel is a small bag for carrying things. It can hold notes, snacks, or little tools."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    owner = f["owner"]
    item = f["item_cfg"]
    place = f["place"]
    if f["choice"] == "hide":
        return [
            f'Write an Animal Story for ages 3 to 5 about a {finder.type} who finds {item.phrase} in {place.label} and feels tempted to keep the lucky acquisition.',
            f'Write a gentle story that includes the words "sad", "law", and "acquisition", with inner monologue, a surprise clue, and reconciliation between {finder.label} and {owner.label}.',
            f"Tell a woodland story where a childlike animal breaks a lost-and-found rule, sees why another animal is sad, and makes things right."
        ]
    return [
        f'Write an Animal Story for ages 3 to 5 about a {finder.type} who finds {item.phrase} in {place.label} and follows a woodland law.',
        f'Write a gentle story that includes the words "sad", "law", and "acquisition", with inner monologue, a surprise clue, and a happy reconciliation.',
        f"Tell a story where a small animal learns that a fair rule can protect a friend's heart."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    owner = f["owner"]
    item = f["item_cfg"]
    place = f["place"]
    plan = f["plan"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {finder.label} the {finder.type}, who found {item.phrase}, and {owner.label} the {owner.type}, who had lost it."
        ),
        (
            f"What was the forest law in {place.label}?",
            f"The law said a found thing must be shown at {place.law_spot} or taken to Old Owl before sunset. The rule existed so lost things could go back to the right owner."
        ),
        (
            f"Why did the found object feel important to {finder.label} at first?",
            f"It looked bright and special, so {finder.label} briefly thought of it as a wonderful acquisition. That tempting feeling is what pulled {finder.pronoun('object')} toward the wrong choice."
        ),
    ]
    if f["choice"] == "hide":
        qa.append((
            f"Why did {finder.label} feel guilty?",
            f"{finder.label} hid the {item.label} even though the law said to report it. When {finder.pronoun()} saw that {owner.label} was sad and searching, {finder.pronoun()} understood that keeping it caused real hurt."
        ))
        qa.append((
            f"What was the surprise in the story?",
            f"The surprise was the clue on the object that showed it belonged to {owner.label}. That made the problem suddenly personal instead of just a rule about an unnamed owner."
        ))
        qa.append((
            f"How did {finder.label} and {owner.label} reconcile?",
            f"{finder.label} brought the lost thing back, admitted the mistake, and apologized. {owner.label} accepted the truth and forgave {finder.pronoun('object')}, so they could walk together again."
        ))
    else:
        qa.append((
            f"How did {finder.label} follow the law?",
            f"{finder.label} {plan.qa_text}. That meant the object was ready to be returned as soon as the owner appeared."
        ))
        qa.append((
            "What was the surprise in the story?",
            f"The surprise was that the clue on the object showed exactly who it belonged to: {owner.label}. The finder learned that the strict-looking rule had been protecting a real friend all along."
        ))
        qa.append((
            f"How did the story end?",
            f"It ended with the item safely returned and both animals feeling lighter. The ending proves that honesty and a fair law can lead to reconciliation instead of hurt."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["item_cfg"].tags) | set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    order = ["law", "lost_and_found", "owl", "reconciliation", "bell", "scarf", "crown", "satchel"]
    for tag in order:
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


ASP_RULES = r"""
place_ok(P)      :- place(P).
usable(I,O)      :- item(I), owner_type(O), can_use(I,O).
valid(P,I,F,O)   :- place_ok(P), item(I), finder_type(F), owner_type(O), F != O, usable(I,O).

sensible_plan(R) :- repair_plan(R), sense(R,S), sense_min(M), S >= M.

outcome(lawful_return)   :- choice(report).
outcome(confessed_return):- choice(hide).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for owner in sorted(item.use_by):
            lines.append(asp.fact("can_use", iid, owner))
    for animal in ALL_ANIMALS:
        lines.append(asp.fact("finder_type", animal))
        lines.append(asp.fact("owner_type", animal))
    for rid, plan in PLANS.items():
        lines.append(asp.fact("repair_plan", rid))
        lines.append(asp.fact("sense", rid, plan.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_plan/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_plan"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("choice", params.choice),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="meadow",
        item="bell",
        finder="rabbit",
        owner="fox",
        plan="ask_owl",
        choice="hide",
        finder_name="Pip",
        owner_name="Fern",
        owl_name="Old Owl",
    ),
    StoryParams(
        place="brook",
        item="scarf",
        finder="mole",
        owner="squirrel",
        plan="wait_at_law_spot",
        choice="report",
        finder_name="Milo",
        owner_name="Nutmeg",
        owl_name="Old Owl",
    ),
    StoryParams(
        place="orchard",
        item="crown",
        finder="rabbit",
        owner="goose",
        plan="ask_owl",
        choice="hide",
        finder_name="Mimi",
        owner_name="Sunny",
        owl_name="Old Owl",
    ),
    StoryParams(
        place="brook",
        item="satchel",
        finder="fox",
        owner="badger",
        plan="wait_at_law_spot",
        choice="report",
        finder_name="Rufus",
        owner_name="Patch",
        owl_name="Old Owl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a found object, a woodland law, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--finder", choices=ALL_ANIMALS)
    ap.add_argument("--owner", choices=ALL_ANIMALS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--choice", choices=["hide", "report"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    pool = [n for n in ANIMALS[animal_type]["name_pool"] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.owner and not owner_can_own(ITEMS[args.item], args.owner):
        raise StoryError(explain_owner_mismatch(ITEMS[args.item], args.owner))
    if args.finder and args.owner and args.finder == args.owner:
        raise StoryError("(No story: the finder and owner must be different animals.)")
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.finder is None or combo[2] == args.finder)
        and (args.owner is None or combo[3] == args.owner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, finder_type, owner_type = rng.choice(sorted(combos))
    choice = args.choice or rng.choice(["hide", "report", "report"])
    if choice == "hide":
        plan_id = args.plan or rng.choice(["ask_owl", "wait_at_law_spot"])
    else:
        plan_id = args.plan or rng.choice(sorted(p.id for p in sensible_plans()))
    finder_name = _pick_name(rng, finder_type)
    owner_name = _pick_name(rng, owner_type, avoid=finder_name)
    return StoryParams(
        place=place_id,
        item=item_id,
        finder=finder_type,
        owner=owner_type,
        plan=plan_id,
        choice=choice,
        finder_name=finder_name,
        owner_name=owner_name,
        owl_name="Old Owl",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.finder not in ANIMALS:
        raise StoryError(f"(Unknown finder type: {params.finder})")
    if params.owner not in ANIMALS:
        raise StoryError(f"(Unknown owner type: {params.owner})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.finder == params.owner:
        raise StoryError("(No story: the finder and owner must be different animals.)")
    if not owner_can_own(ITEMS[params.item], params.owner):
        raise StoryError(explain_owner_mismatch(ITEMS[params.item], params.owner))
    if PLANS[params.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(params.plan))
    if params.choice not in {"hide", "report"}:
        raise StoryError(f"(Unknown choice: {params.choice})")

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        finder_type=params.finder,
        owner_type=params.owner,
        plan=PLANS[params.plan],
        choice=params.choice,
        finder_name=params.finder_name,
        owner_name=params.owner_name,
        owl_name=params.owl_name,
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


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_plans = set(asp_sensible_plans())
    python_plans = {p.id for p in sensible_plans()}
    if clingo_plans == python_plans:
        print(f"OK: sensible plans match ({sorted(clingo_plans)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(clingo_plans)} python={sorted(python_plans)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params smoke seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: generation smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"Smoke test failed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible_plan/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible plans: {', '.join(asp_sensible_plans())}\n")
        print(f"{len(combos)} compatible (place, item, finder, owner) combos:\n")
        for place, item, finder, owner in combos:
            print(f"  {place:8} {item:7} {finder:9} {owner}")
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
            header = (
                f"### {p.finder_name} the {p.finder}: found {p.item} in {p.place} "
                f"(owner: {p.owner}, choice: {p.choice}, outcome: {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
