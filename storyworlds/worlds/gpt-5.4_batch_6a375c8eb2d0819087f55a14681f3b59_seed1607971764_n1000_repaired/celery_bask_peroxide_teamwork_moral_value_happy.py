#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py
==============================================================================

A standalone story world in a fable-like garden domain: small creatures want to
carry a shiny picnic ribbon home to decorate their shared nest, but a sticky
spill on the stepping stones makes the path unsafe. One friend proposes hurrying
alone; another notices the danger; a wise helper brings diluted peroxide to lift
the sticky berry stain from the ribbon without harming it; and the friends learn
that patient teamwork brings a happier ending than grabbing glory alone.

The seed required the words "celery", "bask", and "peroxide", plus teamwork,
moral value, and a happy ending in a fable style. This world turns those into a
simulated little domain with typed entities, physical meters, emotional memes,
constraint-checked combinations, grounded Q&A, and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py
    python storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py --team ants --mess berry_jam --treasure ribbon
    python storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py --treasure salt_crystal
    python storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py --all
    python storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/celery_bask_peroxide_teamwork_moral_value_happy.py --verify
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
TEAMWORK_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    carry_capacity: int = 0
    delicate: bool = False
    stainable: bool = False
    cleaned_by: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "duck", "mother"}
        male = {"boy", "fox", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Team:
    id: str
    species: str
    plural: str
    home: str
    goal_place: str
    bask_place: str
    stash_phrase: str
    member_a: str
    member_b: str
    helper: str
    helper_title: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Mess:
    id: str
    label: str
    patch: str
    shine: str
    slippery: bool
    sticky: bool
    removable_by: set[str]
    risk_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    use_text: str
    delicate: bool
    stainable: bool
    weight: int
    ruined_by_mess: bool
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cleaner:
    id: str
    label: str
    phrase: str
    method_text: str
    gentle: bool
    strength: int
    cleans: set[str]
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    treasure = world.get("treasure")
    for actor in world.characters():
        if actor.role not in {"leader", "partner"}:
            continue
        if actor.meters["crossing"] < THRESHOLD:
            continue
        if path.meters["slippery"] < THRESHOLD:
            continue
        if actor.meters["helpers"] >= THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["slipped"] += 1
        actor.memes["alarm"] += 1
        treasure.meters["dropped"] += 1
        out.append("__slip__")
    return out


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.get("treasure")
    path = world.get("path")
    if treasure.meters["dropped"] < THRESHOLD:
        return out
    if path.meters["sticky"] < THRESHOLD:
        return out
    if not treasure.stainable:
        return out
    sig = ("stain", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["stained"] += 1
    treasure.meters["dimmed"] += 1
    out.append("__stain__")
    return out


def _r_burden(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.get("treasure")
    need = treasure.meters["weight_need"]
    if need < THRESHOLD:
        return out
    helpers = sum(1 for actor in world.characters() if actor.role in {"leader", "partner"} and actor.meters["helpers"] >= THRESHOLD)
    if helpers >= int(need):
        return out
    for actor in world.characters():
        if actor.role not in {"leader", "partner"}:
            continue
        if actor.meters["crossing"] < THRESHOLD:
            continue
        sig = ("burden", actor.id, int(need))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["strain"] += 1
        out.append("__burden__")
    return out


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="stain", tag="physical", apply=_r_stain),
    Rule(name="burden", tag="physical", apply=_r_burden),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def teamwork_needed(team: Team, treasure: Treasure) -> bool:
    return treasure.weight > 1


def cleaning_possible(mess: Mess, cleaner: Cleaner, treasure: Treasure) -> bool:
    return treasure.stainable and mess.id in cleaner.cleans and cleaner.gentle and cleaner.strength >= 1


def valid_combo(team: Team, mess: Mess, treasure: Treasure, cleaner: Cleaner) -> bool:
    if not teamwork_needed(team, treasure):
        return False
    if treasure.ruined_by_mess and not cleaning_possible(mess, cleaner, treasure):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for team_id, team in TEAMS.items():
        for mess_id, mess in MESSES.items():
            for treasure_id, treasure in TREASURES.items():
                for cleaner_id, cleaner in CLEANERS.items():
                    if valid_combo(team, mess, treasure, cleaner):
                        combos.append((team_id, mess_id, treasure_id, cleaner_id))
    return combos


def predict_mishap(world: World, attempt_alone: bool) -> dict:
    sim = world.copy()
    leader = sim.get("leader")
    partner = sim.get("partner")
    if attempt_alone:
        leader.meters["crossing"] += 1
        leader.meters["helpers"] = 0
    else:
        leader.meters["crossing"] += 1
        partner.meters["crossing"] += 1
        leader.meters["helpers"] = 1
        partner.meters["helpers"] = 1
    propagate(sim, narrate=False)
    treasure = sim.get("treasure")
    return {
        "slipped": leader.meters["slipped"] >= THRESHOLD or partner.meters["slipped"] >= THRESHOLD,
        "stained": treasure.meters["stained"] >= THRESHOLD,
        "burden": any(actor.memes["strain"] >= THRESHOLD for actor in sim.characters() if actor.role in {"leader", "partner"}),
    }


def opening(world: World, leader: Entity, partner: Entity, team: Team, treasure: Treasure) -> None:
    for actor in (leader, partner):
        actor.memes["joy"] += 1
    world.say(
        f"In the old garden by {team.home}, two {team.species}, {leader.id} and {partner.id}, "
        f"liked to work side by side. At sunrise they would bask at {team.bask_place}, and by noon "
        f"they would scamper through clover looking for anything bright enough to cheer {team.stash_phrase}."
    )
    world.say(
        f"That morning they found {treasure.phrase}. It gleamed among the stepping stones, and both friends "
        f"imagined how pretty it would look {treasure.use_text}."
    )


def temptation(world: World, leader: Entity, partner: Entity, team: Team, mess: Mess, treasure: Treasure) -> None:
    world.say(
        f"But a patch of {mess.patch} lay across the stones, {mess.shine} in the sun. "
        f"{leader.id} flicked {leader.pronoun('possessive')} feelers and said, "
        f'"If I hurry, I can carry the {treasure.label} across by myself and be first back to {team.goal_place}."'
    )
    leader.memes["pride"] += 1
    partner.memes["care"] += 1


def warning(world: World, leader: Entity, partner: Entity, team: Team, mess: Mess, treasure: Treasure) -> None:
    pred = predict_mishap(world, attempt_alone=True)
    world.facts["predicted_slip"] = pred["slipped"]
    world.facts["predicted_stain"] = pred["stained"]
    world.facts["predicted_burden"] = pred["burden"]
    extra = ""
    if pred["predicted_stain"] if "predicted_stain" in pred else False:
        extra = ""
    if pred["slipped"] and pred["stained"]:
        extra = f" {partner.id} had seen enough berry stains to know the {treasure.label} would lose its shine."
    elif pred["slipped"]:
        extra = f" {partner.id} could almost see the {treasure.label} skidding away."
    world.say(
        f'{partner.id} shook {partner.pronoun("possessive")} head. "The stones are {mess.risk_text}. '
        f'One pair of legs is not enough for a treasure this size."{extra}'
    )


def defy(world: World, leader: Entity, treasure: Treasure) -> None:
    leader.meters["crossing"] += 1
    leader.meters["helpers"] = 0
    treasure.meters["being_carried"] += 1
    world.say(
        f'But wanting all the credit made {leader.id} hasty. {leader.pronoun().capitalize()} tucked one edge of the '
        f'{treasure.label} under {leader.pronoun("possessive")} arms and stepped onto the stones alone.'
    )
    propagate(world, narrate=False)


def mishap(world: World, leader: Entity, mess: Mess, treasure: Treasure) -> None:
    slipped = leader.meters["slipped"] >= THRESHOLD
    stained = treasure.meters["stained"] >= THRESHOLD
    if slipped and stained:
        world.say(
            f"The first stone wobbled under {leader.id}. {leader.pronoun().capitalize()} slid, the {treasure.label} "
            f"fell into the {mess.label}, and a dark smear dimmed its bright edge."
        )
    elif slipped:
        world.say(
            f"The first stone wobbled under {leader.id}, and the {treasure.label} nearly skittered away."
        )
    else:
        world.say(
            f"{leader.id} soon discovered that the treasure pulled harder than expected."
        )
    leader.memes["shame"] += 1
    leader.memes["need"] += 1


def helper_arrives(world: World, leader: Entity, partner: Entity, helper: Entity, team: Team, cleaner: Cleaner) -> None:
    partner.memes["helpfulness"] += 1
    helper.memes["wisdom"] += 1
    world.say(
        f'{partner.id} did not scold. {partner.pronoun().capitalize()} called to {team.helper_title} {helper.id}, '
        f'who kept a tiny satchel of careful remedies. Soon the old helper came along carrying {cleaner.phrase}.'
    )


def clean_treasure(world: World, helper: Entity, treasure: Entity, cleaner: Cleaner, mess: Mess) -> None:
    treasure.meters["stained"] = 0.0
    treasure.meters["dimmed"] = 0.0
    treasure.meters["cleaned"] += 1
    world.say(
        f"{helper.id} dabbed the stain with {cleaner.method_text}. The bit of peroxide loosened the sticky mark, "
        f"and the treasure's bright color peeped out again."
    )


def choose_teamwork(world: World, leader: Entity, partner: Entity, treasure: Entity) -> None:
    leader.memes["pride"] = 0.0
    leader.memes["gratitude"] += 1
    leader.memes["cooperation"] += 1
    partner.memes["cooperation"] += 1
    leader.meters["crossing"] = 0.0
    partner.meters["crossing"] = 0.0
    leader.meters["helpers"] = 1
    partner.meters["helpers"] = 1
    treasure.meters["being_carried"] += 1
    world.say(
        f'"I was foolish to chase the praise alone," said {leader.id}. "{partner.id}, will you carry it with me?" '
        f'{partner.id} smiled and took the other end.'
    )


def safe_crossing(world: World, leader: Entity, partner: Entity, team: Team, treasure: Treasure) -> None:
    leader.meters["crossing"] += 1
    partner.meters["crossing"] += 1
    propagate(world, narrate=False)
    treasure.meters["home"] += 1
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    leader.memes["trust"] += 1
    partner.memes["trust"] += 1
    world.say(
        f"Slowly they crossed together, step by step, holding the {treasure.label} level between them. "
        f"When they reached {team.goal_place}, the afternoon seemed warmer than before."
    )


def ending(world: World, leader: Entity, partner: Entity, team: Team, treasure: Treasure) -> None:
    world.say(
        f"They hung the {treasure.label} {treasure.use_text}, and then the two friends sat in a stripe of sunlight to bask. "
        f"Even the breeze through the celery by the path sounded as if it approved."
    )
    world.say(
        f"From that day on, {leader.id} remembered that bright things are safest in many hands, "
        f"and {partner.id} remembered that kindness can rescue a friend without any boasting at all."
    )


def tell(team: Team, mess: Mess, treasure_cfg: Treasure, cleaner: Cleaner) -> World:
    world = World()
    leader = world.add(Entity(
        id=team.member_a,
        kind="character",
        type=team.species,
        label=team.member_a,
        role="leader",
        attrs={"team": team.id},
        carry_capacity=1,
    ))
    partner = world.add(Entity(
        id=team.member_b,
        kind="character",
        type=team.species,
        label=team.member_b,
        role="partner",
        attrs={"team": team.id},
        carry_capacity=1,
    ))
    helper = world.add(Entity(
        id=team.helper,
        kind="character",
        type=team.species,
        label=team.helper,
        role="helper",
        attrs={"team": team.id},
        carry_capacity=0,
    ))
    path = world.add(Entity(
        id="path",
        kind="thing",
        type="path",
        label="stepping stones",
        attrs={"mess": mess.id},
    ))
    path.meters["slippery"] = 1.0 if mess.slippery else 0.0
    path.meters["sticky"] = 1.0 if mess.sticky else 0.0
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_cfg.id,
        label=treasure_cfg.label,
        delicate=treasure_cfg.delicate,
        stainable=treasure_cfg.stainable,
        attrs={"treasure_cfg": treasure_cfg.id},
        carry_capacity=0,
    ))
    treasure.meters["weight_need"] = float(treasure_cfg.weight)

    opening(world, leader, partner, team, treasure_cfg)
    world.para()
    temptation(world, leader, partner, team, mess, treasure_cfg)
    warning(world, leader, partner, team, mess, treasure_cfg)
    defy(world, leader, treasure)
    mishap(world, leader, mess, treasure)

    world.para()
    helper_arrives(world, leader, partner, helper, team, cleaner)
    clean_treasure(world, helper, treasure, cleaner, mess)
    choose_teamwork(world, leader, partner, treasure)
    safe_crossing(world, leader, partner, team, treasure_cfg)

    world.para()
    ending(world, leader, partner, team, treasure_cfg)

    world.facts.update(
        team=team,
        mess=mess,
        treasure_cfg=treasure_cfg,
        cleaner=cleaner,
        leader=leader,
        partner=partner,
        helper=helper,
        path=path,
        treasure=treasure,
        teamwork=leader.memes["cooperation"] + partner.memes["cooperation"] >= TEAMWORK_MIN,
        slipped=leader.meters["slipped"] >= THRESHOLD,
        stained_before_clean=world.get("treasure").meters["cleaned"] >= THRESHOLD,
        cleaned=world.get("treasure").meters["cleaned"] >= THRESHOLD,
        happy=world.get("treasure").meters["home"] >= THRESHOLD,
        moral="teamwork_and_humility",
    )
    return world


TEAMS = {
    "ants": Team(
        id="ants",
        species="ant",
        plural="ants",
        home="the root of a pear tree",
        goal_place="their neat little hill",
        bask_place="a flat stone near the marigolds",
        stash_phrase="their little hall",
        member_a="Pip",
        member_b="Moss",
        helper="Aunt Brindle",
        helper_title="Aunt",
        tags={"teamwork", "garden"},
    ),
    "mice": Team(
        id="mice",
        species="mouse",
        plural="mice",
        home="the hollow under the shed",
        goal_place="their warm nook",
        bask_place="the fence rail",
        stash_phrase="their cupboard of bright odds and ends",
        member_a="Nib",
        member_b="Tansy",
        helper="Old Hazel",
        helper_title="Old",
        tags={"teamwork", "garden"},
    ),
    "wrens": Team(
        id="wrens",
        species="wren",
        plural="wrens",
        home="the crook of the apple tree",
        goal_place="their woven nest",
        bask_place="the sunny branch above the beans",
        stash_phrase="their woven room",
        member_a="Flit",
        member_b="Reed",
        helper="Grandam Fern",
        helper_title="Grandam",
        tags={"teamwork", "garden"},
    ),
}

MESSES = {
    "berry_jam": Mess(
        id="berry_jam",
        label="berry jam",
        patch="berry jam",
        shine="purple and tempting",
        slippery=True,
        sticky=True,
        removable_by={"peroxide_rinse", "dew_wash"},
        risk_text="slick with berry jam",
        tags={"stain", "berries"},
    ),
    "honey_drip": Mess(
        id="honey_drip",
        label="honey",
        patch="a honey drip",
        shine="golden and slow",
        slippery=True,
        sticky=True,
        removable_by={"peroxide_rinse", "dew_wash"},
        risk_text="sticky and slick",
        tags={"stain", "sticky"},
    ),
    "pollen_paste": Mess(
        id="pollen_paste",
        label="pollen paste",
        patch="pollen paste",
        shine="yellow in the light",
        slippery=True,
        sticky=True,
        removable_by={"peroxide_rinse", "dew_wash"},
        risk_text="soft and slippery",
        tags={"stain", "garden"},
    ),
}

TREASURES = {
    "ribbon": Treasure(
        id="ribbon",
        label="ribbon",
        phrase="a long blue ribbon",
        use_text="over the door of their home",
        delicate=True,
        stainable=True,
        weight=2,
        ruined_by_mess=True,
        tags={"ribbon", "delicate"},
    ),
    "petal_lantern": Treasure(
        id="petal_lantern",
        label="petal lantern",
        phrase="a petal lantern made from a tiny seed shell",
        use_text="beside their supper shelf",
        delicate=True,
        stainable=True,
        weight=2,
        ruined_by_mess=True,
        tags={"lantern", "delicate"},
    ),
    "bead_chain": Treasure(
        id="bead_chain",
        label="bead chain",
        phrase="a bead chain of fallen dew-bright seeds",
        use_text="along the wall of their home",
        delicate=True,
        stainable=True,
        weight=2,
        ruined_by_mess=True,
        tags={"beads", "delicate"},
    ),
    "salt_crystal": Treasure(
        id="salt_crystal",
        label="salt crystal",
        phrase="a salt crystal shaped like a tiny star",
        use_text="on a shelf in their home",
        delicate=True,
        stainable=False,
        weight=1,
        ruined_by_mess=False,
        tags={"crystal"},
    ),
}

CLEANERS = {
    "peroxide_rinse": Cleaner(
        id="peroxide_rinse",
        label="peroxide rinse",
        phrase="a walnut-cap of water with a drop of peroxide",
        method_text="a soft leaf dipped in clear water and a breath of peroxide",
        gentle=True,
        strength=1,
        cleans={"berry_jam", "honey_drip", "pollen_paste"},
        qa_text="used a tiny rinse with peroxide to lift the stain gently",
        tags={"peroxide", "cleaning"},
    ),
    "dew_wash": Cleaner(
        id="dew_wash",
        label="dew wash",
        phrase="a folded clover leaf full of clean dew",
        method_text="cool dawn dew and a patient cloth of moss",
        gentle=True,
        strength=1,
        cleans={"honey_drip", "pollen_paste"},
        qa_text="washed the treasure carefully with dew and moss",
        tags={"dew", "cleaning"},
    ),
    "brisk_scrub": Cleaner(
        id="brisk_scrub",
        label="brisk scrub",
        phrase="a stiff thistle brush",
        method_text="a rough thistle brush",
        gentle=False,
        strength=1,
        cleans={"berry_jam", "honey_drip", "pollen_paste"},
        qa_text="scrubbed hard with a stiff brush",
        tags={"scrub"},
    ),
}

NAMES = {
    "ants": [("Pip", "Moss"), ("Tic", "Clover"), ("Dot", "Rill")],
    "mice": [("Nib", "Tansy"), ("Pipkin", "Mallow"), ("Bram", "Sorrel")],
    "wrens": [("Flit", "Reed"), ("Fern", "Pipit"), ("Wisp", "Lark")],
}


@dataclass
class StoryParams:
    team: str
    mess: str
    treasure: str
    cleaner: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "peroxide": [(
        "What is peroxide?",
        "Peroxide is a liquid people sometimes use for careful cleaning. In tiny, gentle amounts, it can help lift some stains."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means two or more people helping one another on the same job. A hard task often becomes safer and easier when everyone shares it."
    )],
    "celery": [(
        "What is celery?",
        "Celery is a crunchy green plant with long stalks. It often grows in gardens or is eaten as a snack."
    )],
    "bask": [(
        "What does bask mean?",
        "To bask means to rest in warm sunshine or comfort. Animals often bask when they feel safe and calm."
    )],
    "stain": [(
        "What is a stain?",
        "A stain is a mark left on something by dirt, juice, or another material. Some stains can be cleaned if you treat them gently."
    )],
    "humility": [(
        "Why is it good to admit a mistake?",
        "Admitting a mistake helps people fix a problem together. It also shows honesty and helps trust grow again."
    )],
}
KNOWLEDGE_ORDER = ["teamwork", "humility", "peroxide", "stain", "celery", "bask"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    team = f["team"]
    mess = f["mess"]
    treasure = f["treasure_cfg"]
    cleaner = f["cleaner"]
    leader = f["leader"]
    partner = f["partner"]
    return [
        f'Write a short fable for a child about teamwork in a garden. Include the words "celery", "bask", and "peroxide".',
        f"Tell a fable where {leader.id} tries to carry a {treasure.label} alone across {mess.label}, but {partner.id} helps rescue the day and both friends learn to share the work.",
        f"Write a moral story where a wise helper uses {cleaner.label} carefully, the friends work together, and the ending proves that kindness is brighter than pride.",
        f"Tell a small creature tale set near celery where two friends bask happily at the end because they chose teamwork.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    helper = f["helper"]
    team = f["team"]
    mess = f["mess"]
    treasure_cfg = f["treasure_cfg"]
    cleaner = f["cleaner"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two {team.plural}, {leader.id} and {partner.id}, and their wise helper {helper.id}. They live near {team.home} and care about the same little home."
        ),
        (
            f"Why did {leader.id} want the {treasure_cfg.label}?",
            f"{leader.id} wanted to carry the {treasure_cfg.label} back so it could shine {treasure_cfg.use_text}. {leader.pronoun().capitalize()} also liked the idea of being first and winning the praise alone."
        ),
        (
            f"Why was the path dangerous?",
            f"The stepping stones were dangerous because they were {mess.risk_text}. That made it easy to slip and easy for the treasure to fall into the mess."
        ),
        (
            f"What happened when {leader.id} tried to do the job alone?",
            f"{leader.id} slipped while carrying the {treasure_cfg.label} alone, and it fell into the {mess.label}. The mishap happened because one small creature hurried over a slick path without enough help."
        ),
        (
            f"How did {helper.id} help fix the problem?",
            f"{helper.id} {cleaner.qa_text}. That careful cleaning brought back the treasure's brightness so the friends could still carry it home."
        ),
        (
            "How did the friends solve the problem after that?",
            f"They shared the work and carried the {treasure_cfg.label} together, one on each side. Moving slowly as a team made the crossing safer than trying to grab all the credit alone."
        ),
        (
            "What is the moral of the story?",
            "The story teaches that teamwork and humility bring happier endings than pride. When someone admits a mistake and accepts help, a problem can turn into a shared success."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork", "humility", "celery", "bask"}
    if "peroxide" in f["cleaner"].id:
        tags.add("peroxide")
    if f["slipped"] or f["cleaned"]:
        tags.add("stain")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(team: Team, mess: Mess, treasure: Treasure, cleaner: Cleaner) -> str:
    if not teamwork_needed(team, treasure):
        return (
            f"(No story: the {treasure.label} is light enough for one creature to carry, "
            f"so the world would not honestly teach teamwork. Pick a treasure that truly needs two friends.)"
        )
    if treasure.ruined_by_mess and not cleaning_possible(mess, cleaner, treasure):
        return (
            f"(No story: {cleaner.label} is not a gentle way to rescue a {treasure.label} from {mess.label}. "
            f"Pick a cleaner that can lift the stain without harming the treasure.)"
        )
    return "(No story: this combination does not make a sensible teamwork fable.)"


CURATED = [
    StoryParams(team="ants", mess="berry_jam", treasure="ribbon", cleaner="peroxide_rinse"),
    StoryParams(team="mice", mess="honey_drip", treasure="petal_lantern", cleaner="dew_wash"),
    StoryParams(team="wrens", mess="pollen_paste", treasure="bead_chain", cleaner="peroxide_rinse"),
]


ASP_RULES = r"""
needs_teamwork(Treasure) :- treasure(Treasure), weight(Treasure, W), W > 1.
cleaning_possible(M, T, C) :- mess(M), treasure(T), cleaner(C),
                              stainable(T), ruined_by_mess(T),
                              gentle(C), cleans(C, M).
valid(Team, M, T, C) :- team(Team), mess(M), treasure(T), cleaner(C),
                        needs_teamwork(T),
                        (not ruined_by_mess(T); cleaning_possible(M, T, C)).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for team_id in TEAMS:
        lines.append(asp.fact("team", team_id))
    for mess_id in MESSES:
        lines.append(asp.fact("mess", mess_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        lines.append(asp.fact("weight", treasure_id, treasure.weight))
        if treasure.stainable:
            lines.append(asp.fact("stainable", treasure_id))
        if treasure.ruined_by_mess:
            lines.append(asp.fact("ruined_by_mess", treasure_id))
    for cleaner_id, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cleaner_id))
        if cleaner.gentle:
            lines.append(asp.fact("gentle", cleaner_id))
        for mess_id in sorted(cleaner.cleans):
            lines.append(asp.fact("cleans", cleaner_id, mess_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
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
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story or "peroxide" not in sample.story or "celery" not in sample.story or "bask" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missed required seed words or was empty.)")
        print("OK: smoke test generated a normal story successfully.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-like story world: a shared treasure, a sticky path, a gentle cleaning fix, and a teamwork moral."
    )
    ap.add_argument("--team", choices=TEAMS)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.team and args.mess and args.treasure and args.cleaner:
        team = TEAMS[args.team]
        mess = MESSES[args.mess]
        treasure = TREASURES[args.treasure]
        cleaner = CLEANERS[args.cleaner]
        if not valid_combo(team, mess, treasure, cleaner):
            raise StoryError(explain_rejection(team, mess, treasure, cleaner))

    combos = [
        combo for combo in valid_combos()
        if (args.team is None or combo[0] == args.team)
        and (args.mess is None or combo[1] == args.mess)
        and (args.treasure is None or combo[2] == args.treasure)
        and (args.cleaner is None or combo[3] == args.cleaner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    team_id, mess_id, treasure_id, cleaner_id = rng.choice(sorted(combos))
    return StoryParams(team=team_id, mess=mess_id, treasure=treasure_id, cleaner=cleaner_id)


def generate(params: StoryParams) -> StorySample:
    if params.team not in TEAMS:
        raise StoryError(f"(Unknown team: {params.team})")
    if params.mess not in MESSES:
        raise StoryError(f"(Unknown mess: {params.mess})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.cleaner not in CLEANERS:
        raise StoryError(f"(Unknown cleaner: {params.cleaner})")
    team = TEAMS[params.team]
    mess = MESSES[params.mess]
    treasure = TREASURES[params.treasure]
    cleaner = CLEANERS[params.cleaner]
    if not valid_combo(team, mess, treasure, cleaner):
        raise StoryError(explain_rejection(team, mess, treasure, cleaner))
    world = tell(team, mess, treasure, cleaner)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (team, mess, treasure, cleaner) combos:\n")
        for team, mess, treasure, cleaner in combos:
            print(f"  {team:8} {mess:12} {treasure:14} {cleaner}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.team}: {p.treasure} through {p.mess} ({p.cleaner})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
