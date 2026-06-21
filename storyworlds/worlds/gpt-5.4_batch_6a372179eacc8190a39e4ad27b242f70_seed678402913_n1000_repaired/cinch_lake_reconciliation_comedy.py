#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cinch_lake_reconciliation_comedy.py
==============================================================

A standalone story world about a silly lakeside lunch disaster: one child boasts
that fastening the snacks is "a cinch", refuses help, and a comic bump spills
everything anyway. The children squabble, then reconcile by apologizing and
fixing the container together.

The core constraint is simple and child-sized:
- a place must actually allow the chosen bump,
- the chosen repair must fit the chosen container's closure,
- and only sensible repairs are allowed by default.

The resulting stories are small reconciliation comedies: the turn comes from a
physical mess at the lake, and the ending image shows the friendship repaired,
not just the lunch.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    closure: str
    cargo: str
    spill_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bump:
    id: str
    label: str
    force: int
    text: str
    aftermath: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    power: int
    closures: set[str] = field(default_factory=set)
    act_text: str = ""
    gather_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    container: str
    bump: str
    repair: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    parent: str
    trait1: str
    trait2: str
    relation: str = "friends"
    seed: Optional[int] = None


PLACES = {
    "dock": Place(
        id="dock",
        label="the dock",
        scene="At the little lake dock, the boards smelled warm and the water blinked with silver ripples.",
        affords={"dock_wobble", "goose_nudge", "breeze_flip"},
        tags={"lake", "dock"},
    ),
    "reed_bank": Place(
        id="reed_bank",
        label="the reedy bank",
        scene="By the edge of the lake, reeds whispered and tiny waves kept kissing the stones.",
        affords={"goose_nudge", "breeze_flip"},
        tags={"lake", "reeds"},
    ),
    "boathouse_path": Place(
        id="boathouse_path",
        label="the boathouse path",
        scene="Near the lake boathouse, the gravel path curved past bright rowboats and a rack of orange life jackets.",
        affords={"wagon_bounce", "breeze_flip"},
        tags={"lake", "boathouse"},
    ),
}

CONTAINERS = {
    "snack_sack": ContainerCfg(
        id="snack_sack",
        label="snack sack",
        phrase="a striped snack sack with a red cinch cord",
        closure="cinch",
        cargo="jam buns",
        spill_word="buns",
        tags={"cinch", "bag", "snack"},
    ),
    "pie_tin": ContainerCfg(
        id="pie_tin",
        label="pie tin",
        phrase="a round pie tin with a shiny lid",
        closure="lid",
        cargo="mini berry pies",
        spill_word="pies",
        tags={"tin", "pie", "snack"},
    ),
    "picnic_basket": ContainerCfg(
        id="picnic_basket",
        label="picnic basket",
        phrase="a wicker picnic basket with a clicky clasp",
        closure="clasp",
        cargo="cheese crackers",
        spill_word="crackers",
        tags={"basket", "clasp", "snack"},
    ),
}

BUMPS = {
    "dock_wobble": Bump(
        id="dock_wobble",
        label="a wobbly board",
        force=1,
        text="One loose board on the dock gave a silly boing under their shoes.",
        aftermath="The container bobbled in the air like it had suddenly remembered a dance step.",
        tags={"dock", "wobble"},
    ),
    "breeze_flip": Bump(
        id="breeze_flip",
        label="a cheeky breeze",
        force=1,
        text="A lake breeze whisked around them and puffed at the container like an invisible prankster.",
        aftermath="For a second it tilted sideways and everything inside seemed to lean with it.",
        tags={"wind", "lake"},
    ),
    "goose_nudge": Bump(
        id="goose_nudge",
        label="a nosy goose",
        force=2,
        text='A goose waddled up, stretched its long neck, and gave the container one bold little nudge.',
        aftermath="That was all it took to jolt the snacks toward the edge.",
        tags={"goose", "lake"},
    ),
    "wagon_bounce": Bump(
        id="wagon_bounce",
        label="a wagon bump",
        force=2,
        text="Their red wagon hit a fat bump in the gravel and bounced as if it had hiccupped.",
        aftermath="The container leapt up and came down crooked.",
        tags={"wagon", "gravel"},
    ),
}

REPAIRS = {
    "pull_cinch": Repair(
        id="pull_cinch",
        label="pull the cinch cord tight",
        sense=3,
        power=2,
        closures={"cinch"},
        act_text="pulled the red cord snug and made the sack pucker shut",
        gather_text="They tucked the clean buns back in with careful fingers.",
        qa_text="They tightened the cinch cord so the sack finally stayed shut.",
        tags={"cinch", "fix"},
    ),
    "press_lid": Repair(
        id="press_lid",
        label="snap the lid back on",
        sense=3,
        power=2,
        closures={"lid"},
        act_text="pressed the lid down all the way until it gave a neat little snap",
        gather_text="They rescued the pies that had landed on the clean picnic cloth.",
        qa_text="They pressed the lid back on until it snapped shut.",
        tags={"lid", "fix"},
    ),
    "clip_clasp": Repair(
        id="clip_clasp",
        label="close the clasp properly",
        sense=3,
        power=2,
        closures={"clasp"},
        act_text="folded the basket shut and clicked the clasp until both children heard it catch",
        gather_text="They brushed off the safe crackers and stacked them back inside.",
        qa_text="They shut the basket and clicked the clasp properly.",
        tags={"clasp", "fix"},
    ),
    "double_bow": Repair(
        id="double_bow",
        label="tie a double bow",
        sense=2,
        power=1,
        closures={"cinch", "clasp"},
        act_text="used both sets of hands to tie a careful double bow around it",
        gather_text="They saved what they could while laughing at the ridiculous knot.",
        qa_text="They worked together to tie a careful double bow around it.",
        tags={"knot", "fix"},
    ),
    "sit_on_it": Repair(
        id="sit_on_it",
        label="sit on it",
        sense=1,
        power=1,
        closures={"cinch", "lid", "clasp"},
        act_text="sat on the poor container, which only made everything look more squashed",
        gather_text="Nothing about the lunch looked happier afterward.",
        qa_text="They sat on it, which was not a sensible fix.",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["bouncy", "chatty", "careful", "goofy", "helpful", "dramatic"]


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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("bump_happened"):
        return out
    container = world.get("container")
    bump = world.facts["bump_cfg"]
    if container.meters["secure"] >= THRESHOLD:
        return out
    sig = ("spill", bump.id, container.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    container.meters["spilled"] += 1
    world.get("snacks").meters["scattered"] += 1
    world.get("lake").meters["commotion"] += 1
    out.append("__spill__")
    return out


def _r_ducks(world: World) -> list[str]:
    out: list[str] = []
    snacks = world.get("snacks")
    if snacks.meters["scattered"] < THRESHOLD:
        return out
    sig = ("ducks", "snacks")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ducks").meters["interested"] += 1
    out.append("At once, a line of hopeful ducks started marching over as if someone had rung a lunch bell.")
    return out


def _r_feelings(world: World) -> list[str]:
    out: list[str] = []
    container = world.get("container")
    if container.meters["spilled"] < THRESHOLD:
        return out
    sig = ("feelings", "spill")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead = world.get("lead")
    pal = world.get("pal")
    lead.memes["embarrassment"] += 1
    pal.memes["annoyance"] += 1
    lead.memes["annoyance"] += 1
    out.append("__feelings__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("apology_done") or not world.facts.get("repair_done"):
        return out
    sig = ("reconcile", "friends")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead = world.get("lead")
    pal = world.get("pal")
    for kid in (lead, pal):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
        kid.memes["anger"] = 0.0
    lead.memes["remorse"] += 1
    pal.memes["forgiveness"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="ducks", tag="physical", apply=_r_ducks),
    Rule(name="feelings", tag="emotional", apply=_r_feelings),
    Rule(name="reconcile", tag="emotional", apply=_r_reconcile),
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
        for sent in produced:
            world.say(sent)
    return produced


def repair_fits(container: ContainerCfg, repair: Repair) -> bool:
    return container.closure in repair.closures


def valid_combo(place_id: str, container_id: str, bump_id: str, repair_id: str) -> bool:
    place = PLACES[place_id]
    container = CONTAINERS[container_id]
    repair = REPAIRS[repair_id]
    return bump_id in place.affords and repair.sense >= SENSE_MIN and repair_fits(container, repair)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for bump_id in sorted(place.affords):
            for container_id in CONTAINERS:
                for repair_id, repair in REPAIRS.items():
                    if repair.sense < SENSE_MIN:
                        continue
                    if repair_fits(CONTAINERS[container_id], repair):
                        combos.append((place_id, container_id, bump_id, repair_id))
    return combos


def explain_combo(place_id: str, container_id: str, bump_id: str, repair_id: str) -> str:
    place = PLACES[place_id]
    container = CONTAINERS[container_id]
    repair = REPAIRS[repair_id]
    if bump_id not in place.affords:
        return (
            f"(No story: {place.label} does not naturally create {BUMPS[bump_id].label}. "
            f"Pick a bump the place actually affords.)"
        )
    if repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair_id}': {repair.label} is too silly to count as a sensible fix "
            f"(sense={repair.sense} < {SENSE_MIN}).)"
        )
    if not repair_fits(container, repair):
        return (
            f"(No story: {repair.label} does not fit {container.phrase}. "
            f"The repair has to match a {container.closure} closure.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    repair = REPAIRS[params.repair]
    bump = BUMPS[params.bump]
    return "neat" if repair.power >= bump.force else "messy"


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def _do_bump(world: World) -> None:
    world.facts["bump_happened"] = True
    propagate(world, narrate=False)


def predict_spill(world: World, bump: Bump) -> dict:
    sim = world.copy()
    sim.facts["bump_cfg"] = bump
    _do_bump(sim)
    return {
        "spilled": sim.get("container").meters["spilled"] >= THRESHOLD,
        "ducks": sim.get("ducks").meters["interested"] >= THRESHOLD,
    }


def introduce(world: World, place: Place, lead: Entity, pal: Entity, parent: Entity, container: ContainerCfg) -> None:
    world.say(
        f"{place.scene} {lead.id} and {pal.id} had come with {lead.id}'s {parent.label_word} for a tiny picnic beside the lake."
    )
    world.say(
        f"They were carrying {container.phrase}, and inside were {container.cargo} meant for a grand lakeside snack."
    )
    for kid in (lead, pal):
        kid.memes["joy"] += 1


def mission(world: World, lead: Entity, pal: Entity, container: ContainerCfg) -> None:
    world.say(
        f'"Let\'s march in like fancy captains and open the {container.label} at the best spot," {pal.id} said.'
    )
    world.say(
        f'That sounded perfect to {lead.id}, who liked any plan that made an ordinary lunch feel important.'
    )


def boast(world: World, lead: Entity, pal: Entity, container: ContainerCfg) -> None:
    lead.memes["pride"] += 1
    world.say(
        f'When {pal.id} reached to help, {lead.id} grinned and pulled the container a little closer. '
        f'"No need. Fastening this is a cinch," {lead.pronoun()} said.'
    )
    world.say(
        f'But in all the showing off, {lead.id} only gave the {container.closure} a quick half-done tug.'
    )
    world.get("container").meters["loose"] += 1


def warn(world: World, pal: Entity, lead: Entity, bump: Bump, container: ContainerCfg) -> None:
    pred = predict_spill(world, bump)
    pal.memes["care"] += 1
    world.facts["predicted_spill"] = pred["spilled"]
    ducks_line = " and the ducks will come running" if pred["ducks"] else ""
    world.say(
        f'{pal.id} narrowed {pal.pronoun("possessive")} eyes. "That does not look shut to me. '
        f'If {bump.label} happens, the {container.spill_word} could spill{ducks_line}."'
    )


def defy(world: World, lead: Entity) -> None:
    lead.memes["defiance"] += 1
    world.say(
        f'"It will be fine," {lead.id} said, walking on with the proud carefulness of someone trying very hard to look extra casual.'
    )


def bump_and_spill(world: World, lead: Entity, pal: Entity, bump: Bump, container: ContainerCfg) -> None:
    world.say(bump.text)
    world.say(bump.aftermath)
    world.facts["bump_cfg"] = bump
    _do_bump(world)
    if world.get("container").meters["spilled"] >= THRESHOLD:
        world.say(
            f'Out popped the {container.spill_word}. They bounced, rolled, and skittered in three different directions at once.'
        )
        if world.get("ducks").meters["interested"] >= THRESHOLD:
            world.say("The whole scene was so sudden that even the ducks looked delighted.")
    else:
        world.say("Somehow the lunch stayed put after all.")


def squabble(world: World, lead: Entity, pal: Entity) -> None:
    if world.get("container").meters["spilled"] < THRESHOLD:
        return
    lead.memes["anger"] += 1
    pal.memes["anger"] += 1
    world.say(
        f'"I told you it wasn\'t shut," {pal.id} said.'
    )
    world.say(
        f'{lead.id} opened {lead.pronoun("possessive")} mouth to argue, saw the runaway snack parade, and then made a face instead.'
    )


def apology(world: World, lead: Entity, pal: Entity) -> None:
    world.say(
        f'"You were right," {lead.id} said at last. "I wanted to look clever, and I made a mess. I\'m sorry."'
    )
    world.say(
        f'{pal.id} let out one huffy little breath, then nodded. "I still want lunch more than I want a fight."'
    )
    world.facts["apology_done"] = True
    propagate(world, narrate=False)


def repair_and_gather(world: World, lead: Entity, pal: Entity, repair: Repair) -> None:
    container = world.get("container")
    container.meters["secure"] = float(repair.power)
    container.meters["loose"] = 0.0
    world.say(
        f'Together they {repair.act_text}.'
    )
    world.say(repair.gather_text)
    world.facts["repair_done"] = True
    propagate(world, narrate=False)


def ending_neat(world: World, lead: Entity, pal: Entity, parent: Entity, place: Place, container: ContainerCfg) -> None:
    world.say(
        f"{parent.label_word.capitalize()} spread the picnic cloth while the two children set the now-secure {container.label} in the middle like a trophy."
    )
    world.say(
        f'Soon they were eating beside the lake and laughing about the "fancy captain disaster" as if it had happened to someone much sillier.'
    )
    world.say(
        f'By the time the sun made a gold stripe across {place.label}, {lead.id} and {pal.id} were shoulder to shoulder again, and sharing the last of the snack was the easiest part of the day.'
    )


def ending_messy(world: World, lead: Entity, pal: Entity, parent: Entity, place: Place, bump: Bump) -> None:
    world.say(
        f'They did not save every bite, especially after {bump.label} and the ducks had both taken their turn at the joke.'
    )
    world.say(
        f'But {parent.label_word} bought them a warm bag of popcorn from the little lake stand, and the two children shared it from the same striped cup.'
    )
    world.say(
        f'Before long, {lead.id} and {pal.id} were laughing so hard at the bold goose and the ridiculous knot that nobody could remember how the argument had sounded in the first place.'
    )


def tell(
    place: Place,
    container_cfg: ContainerCfg,
    bump: Bump,
    repair: Repair,
    kid1: str,
    kid1_gender: str,
    kid2: str,
    kid2_gender: str,
    parent_type: str,
    trait1: str,
    trait2: str,
    relation: str,
) -> World:
    world = World()
    lead = world.add(Entity(id="lead", kind="character", type=kid1_gender, label=kid1, attrs={"name": kid1, "trait": trait1, "relation": relation}))
    pal = world.add(Entity(id="pal", kind="character", type=kid2_gender, label=kid2, attrs={"name": kid2, "trait": trait2, "relation": relation}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    lake = world.add(Entity(id="lake", type="lake", label="lake"))
    ducks = world.add(Entity(id="ducks", type="ducks", label="ducks"))
    snacks = world.add(Entity(id="snacks", type="food", label=container_cfg.cargo))
    container = world.add(Entity(id="container", type="container", label=container_cfg.label, phrase=container_cfg.phrase, attrs={"closure": container_cfg.closure}))

    world.facts.update(
        place=place,
        container_cfg=container_cfg,
        bump_cfg=bump,
        repair_cfg=repair,
        lead=lead,
        pal=pal,
        parent=parent,
        relation=relation,
        bump_happened=False,
        apology_done=False,
        repair_done=False,
    )

    introduce(world, place, lead, pal, parent, container_cfg)
    mission(world, lead, pal, container_cfg)

    world.para()
    boast(world, lead, pal, container_cfg)
    warn(world, pal, lead, bump, container_cfg)
    defy(world, lead)

    world.para()
    bump_and_spill(world, lead, pal, bump, container_cfg)
    squabble(world, lead, pal)

    world.para()
    apology(world, lead, pal)
    repair_and_gather(world, lead, pal, repair)

    world.para()
    if repair.power >= bump.force:
        ending_neat(world, lead, pal, parent, place, container_cfg)
        outcome = "neat"
    else:
        ending_messy(world, lead, pal, parent, place, bump)
        outcome = "messy"

    world.facts.update(
        outcome=outcome,
        spilled=world.get("container").meters["spilled"] >= THRESHOLD,
        ducks_arrived=world.get("ducks").meters["interested"] >= THRESHOLD,
        secure=world.get("container").meters["secure"] >= THRESHOLD,
    )
    return world


def pair_noun(lead: Entity, pal: Entity, relation: str) -> str:
    if relation == "siblings":
        if lead.type == "boy" and pal.type == "boy":
            return "two brothers"
        if lead.type == "girl" and pal.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    container = f["container_cfg"]
    bump = f["bump_cfg"]
    repair = f["repair_cfg"]
    lead = f["lead"]
    pal = f["pal"]
    return [
        f'Write a short comedy for a 3-to-5-year-old set by a lake. Include the word "cinch" and end with a reconciliation.',
        f"Tell a funny story where {lead.label} boasts that fastening {container.phrase} is a cinch, then {bump.label} proves otherwise, and {pal.label} helps make peace.",
        f"Write a gentle lakeside mishap story in which spilled snacks lead to an apology, a teamwork fix ({repair.label}), and two children laughing together at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    pal = f["pal"]
    parent = f["parent"]
    place = f["place"]
    container = f["container_cfg"]
    bump = f["bump_cfg"]
    repair = f["repair_cfg"]
    pair = pair_noun(lead, pal, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {lead.label} and {pal.label}, having a picnic by the lake with {lead.label}'s {parent.label_word}. The story follows their silly argument and the way they make up.",
        ),
        (
            "Why did the snacks spill?",
            f"The snacks spilled because {lead.label} bragged that fastening the container was a cinch and left it only half shut. Then {bump.label} knocked it crooked before the lunch was secure.",
        ),
        (
            f"What warning did {pal.label} give?",
            f"{pal.label} said the container did not look properly shut and warned that the food could spill. {pal.pronoun('subject').capitalize()} could see the risk before the bump happened.",
        ),
    ]
    if f["spilled"]:
        qa.append(
            (
                "Why did the children argue?",
                f"They argued because the food scattered and both children felt upset in the middle of the mess. {lead.label} felt embarrassed after showing off, and {pal.label} felt annoyed because the warning had been ignored.",
            )
        )
    qa.append(
        (
            "How did they reconcile?",
            f"{lead.label} stopped arguing and apologized for trying to look clever. Then both children worked together on the fix, which turned the problem from a blame moment into a teamwork moment.",
        )
    )
    if f["outcome"] == "neat":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the lunch saved and the friendship mended. After they used the fix -- {repair.qa_text} -- they ate beside the lake and laughed about the whole disaster.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily even though not every snack was saved. The children had already made up, and they shared popcorn by the lake while laughing at the mess together.",
            )
        )
    return qa


KNOWLEDGE = {
    "lake": [
        (
            "What is a lake?",
            "A lake is a big body of water with land all around it. People can picnic, watch ducks, or ride boats there.",
        )
    ],
    "cinch": [
        (
            "What does cinch mean in this story?",
            'Here "cinch" means something easy to do. The funny part is that the child says it is easy, but then makes a mistake anyway.',
        )
    ],
    "goose": [
        (
            "Why can a goose make a picnic silly?",
            "A goose is curious and bold, so it may waddle over to see what food people have. That can make a picnic feel funny and a little wild.",
        )
    ],
    "wind": [
        (
            "What can wind do to loose things?",
            "Wind can push and tip things that are not fastened well. That is why bags, lids, and hats need to be secured.",
        )
    ],
    "dock": [
        (
            "Why do people need careful feet on a dock?",
            "A dock can wobble or feel slippery above the water. Walking carefully helps you keep your balance and hold onto your things.",
        )
    ],
    "fix": [
        (
            "Why does helping together fix a problem faster?",
            "Two people can share jobs, notice mistakes, and calm each other down. Working together often repairs both the mess and the mood.",
        )
    ],
    "sorry": [
        (
            "Why can saying sorry help friends make up?",
            "A real apology shows that someone understands the hurt they caused. That makes it easier for the other person to forgive and start again.",
        )
    ],
    "basket": [
        (
            "What does a clasp on a basket do?",
            "A clasp keeps the basket shut so the things inside do not tumble out. If it is not clicked closed, the basket can pop open.",
        )
    ],
    "lid": [
        (
            "What does a lid do?",
            "A lid covers the top of a container and keeps what is inside from spilling. It works best when it is pressed on all the way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lake", "cinch", "goose", "wind", "dock", "basket", "lid", "fix", "sorry"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"lake", "fix", "sorry"}
    tags |= set(f["place"].tags)
    tags |= set(f["container_cfg"].tags)
    tags |= set(f["bump_cfg"].tags)
    tags |= set(f["repair_cfg"].tags)
    mapped: set[str] = set()
    if "goose" in tags:
        mapped.add("goose")
    if "wind" in tags:
        mapped.add("wind")
    if "dock" in tags:
        mapped.add("dock")
    if "cinch" in tags:
        mapped.add("cinch")
    if "clasp" in tags or "basket" in tags:
        mapped.add("basket")
    if "lid" in tags or "tin" in tags:
        mapped.add("lid")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags or key in mapped:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="dock",
        container="snack_sack",
        bump="goose_nudge",
        repair="pull_cinch",
        kid1="Max",
        kid1_gender="boy",
        kid2="Lily",
        kid2_gender="girl",
        parent="mother",
        trait1="goofy",
        trait2="careful",
        relation="friends",
    ),
    StoryParams(
        place="boathouse_path",
        container="picnic_basket",
        bump="wagon_bounce",
        repair="double_bow",
        kid1="Ava",
        kid1_gender="girl",
        kid2="Ben",
        kid2_gender="boy",
        parent="father",
        trait1="dramatic",
        trait2="helpful",
        relation="siblings",
    ),
    StoryParams(
        place="reed_bank",
        container="pie_tin",
        bump="breeze_flip",
        repair="press_lid",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Owen",
        kid2_gender="boy",
        parent="mother",
        trait1="chatty",
        trait2="careful",
        relation="friends",
    ),
]


ASP_RULES = r"""
valid(P, C, B, R) :- place(P), container(C), bump(B), repair(R),
                     affords(P, B),
                     sensible(R),
                     closure(C, K),
                     fits(R, K).

sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.

outcome(neat)  :- chosen_bump(B), chosen_repair(R), power(R, P), force(B, F), P >= F.
outcome(messy) :- chosen_bump(B), chosen_repair(R), power(R, P), force(B, F), P < F.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for bump_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, bump_id))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("closure", container_id, container.closure))
    for bump_id, bump in BUMPS.items():
        lines.append(asp.fact("bump", bump_id))
        lines.append(asp.fact("force", bump_id, bump.force))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
        for closure in sorted(repair.closures):
            lines.append(asp.fact("fits", repair_id, closure))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_bump", params.bump),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a silly lake picnic, a boast, a spill, and a reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--bump", choices=BUMPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.container and args.bump and args.repair:
        if not valid_combo(args.place, args.container, args.bump, args.repair):
            raise StoryError(explain_combo(args.place, args.container, args.bump, args.repair))
    elif args.place and args.bump and args.bump not in PLACES[args.place].affords:
        fallback_container = args.container or next(iter(CONTAINERS))
        fallback_repair = args.repair or next(iter(REPAIRS))
        raise StoryError(explain_combo(args.place, fallback_container, args.bump, fallback_repair))
    elif args.container and args.repair and not repair_fits(CONTAINERS[args.container], REPAIRS[args.repair]):
        place = args.place or next(iter(PLACES))
        bump = args.bump or next(iter(PLACES[place].affords))
        raise StoryError(explain_combo(place, args.container, bump, args.repair))
    elif args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        place = args.place or next(iter(PLACES))
        bump = args.bump or next(iter(PLACES[place].affords))
        container = args.container or next(iter(CONTAINERS))
        raise StoryError(explain_combo(place, container, bump, args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.container is None or combo[1] == args.container)
        and (args.bump is None or combo[2] == args.bump)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, container_id, bump_id, repair_id = rng.choice(sorted(combos))
    kid1, kid1_gender = _pick_child(rng)
    kid2, kid2_gender = _pick_child(rng, avoid=kid1)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["friends", "siblings"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    return StoryParams(
        place=place_id,
        container=container_id,
        bump=bump_id,
        repair=repair_id,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        parent=parent,
        trait1=trait1,
        trait2=trait2,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        container = CONTAINERS[params.container]
        bump = BUMPS[params.bump]
        repair = REPAIRS[params.repair]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if not valid_combo(params.place, params.container, params.bump, params.repair):
        raise StoryError(explain_combo(params.place, params.container, params.bump, params.repair))

    world = tell(
        place=place,
        container_cfg=container,
        bump=bump,
        repair=repair,
        kid1=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2=params.kid2,
        kid2_gender=params.kid2_gender,
        parent_type=params.parent,
        trait1=params.trait1,
        trait2=params.trait2,
        relation=params.relation,
    )

    story = world.render()
    if "{" in story or "}" in story:
        raise StoryError("(Rendered story contains unresolved template braces.)")

    return StorySample(
        params=params,
        story=story,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(25):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed unexpectedly for seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover - defensive
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, container, bump, repair) combos:\n")
        for place, container, bump, repair in combos:
            print(f"  {place:14} {container:14} {bump:12} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.kid1} & {p.kid2}: {p.container} at {p.place} "
                f"({p.bump}, {p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
