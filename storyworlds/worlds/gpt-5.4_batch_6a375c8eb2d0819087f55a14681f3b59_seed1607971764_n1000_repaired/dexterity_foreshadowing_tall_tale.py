#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dexterity_foreshadowing_tall_tale.py
===============================================================

A standalone story world in a tall-tale style: a child famous for impossible
dexterity must carry an absurdly oversized fair-day prize along a risky route.
The world always plants a foreshadowing sign before the trouble arrives: a hum
in the bridge ropes, a twitch in a tower of pies, a wind that already knows the
way to mischief.

The simulation models:
- physical meters: wobble, spill, danger, carried, delivered
- emotional memes: pride, worry, relief, trust, awe
- a reasonableness gate over cargo/aid compatibility
- an inline ASP twin of the gate and the outcome model

Typical runs:
    python storyworlds/worlds/gpt-5.4/dexterity_foreshadowing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/dexterity_foreshadowing_tall_tale.py --place river_fair --cargo pies --aid balancing_pole
    python storyworlds/worlds/gpt-5.4/dexterity_foreshadowing_tall_tale.py --cargo soup --aid mitten
    python storyworlds/worlds/gpt-5.4/dexterity_foreshadowing_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/dexterity_foreshadowing_tall_tale.py --verify
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

DEXTERITY_LEVELS = {
    "legendary": 4,
    "nimble": 3,
    "steady": 2,
    "learning": 1,
}

SENSE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Place:
    id: str
    label: str
    opening: str
    route: str
    omen: str
    hazard_text: str
    difficulty: int
    ending_image: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    kind: str
    container: str
    top_heavy: int
    mess: str
    boast: str
    ending: str
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
class Aid:
    id: str
    label: str
    phrase: str
    handles: set[str]
    sense: int
    stability: int
    carry_text: str
    save_text: str
    fail_text: str
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


def _r_wobble_to_danger(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["wobble"] < THRESHOLD:
        return []
    sig = ("danger", "cargo")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("route").meters["danger"] += 1
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return ["__danger__"]


def _r_spill_to_loss(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["spill"] < THRESHOLD:
        return []
    sig = ("loss", "cargo")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["delivered"] = 0.0
    world.get("route").meters["mess"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble_to_danger", tag="physical", apply=_r_wobble_to_danger),
    Rule(name="spill_to_loss", tag="physical", apply=_r_spill_to_loss),
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


def aid_works_for(aid: Aid, cargo: Cargo) -> bool:
    return cargo.kind in aid.handles


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def best_possible_control(place: Place, cargo: Cargo, aid: Aid) -> int:
    return DEXTERITY_LEVELS["legendary"] + aid.stability


def valid_combo(place: Place, cargo: Cargo, aid: Aid) -> bool:
    if not aid_works_for(aid, cargo):
        return False
    if aid.sense < SENSE_MIN:
        return False
    return best_possible_control(place, cargo, aid) >= place.difficulty + cargo.top_heavy


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for cid, cargo in CARGOS.items():
            for aid_id, aid in AIDS.items():
                if valid_combo(place, cargo, aid):
                    combos.append((pid, cid, aid_id))
    return combos


def severity(place: Place, cargo: Cargo, hurry: int) -> int:
    return place.difficulty + cargo.top_heavy + hurry


def control_score(aid: Aid, dexterity: str) -> int:
    return aid.stability + DEXTERITY_LEVELS[dexterity]


def outcome_of(params: "StoryParams") -> str:
    if params.place not in PLACES or params.cargo not in CARGOS or params.aid not in AIDS:
        raise StoryError("(Unknown place, cargo, or aid.)")
    place = PLACES[params.place]
    cargo = CARGOS[params.cargo]
    aid = AIDS[params.aid]
    if not valid_combo(place, cargo, aid):
        raise StoryError(explain_rejection(place, cargo, aid))
    score = control_score(aid, params.dexterity)
    need = severity(place, cargo, params.hurry)
    if score > need:
        return "smooth"
    if score == need:
        return "saved"
    return "spilled"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    place: Place = sim.facts["place"]
    cargo_cfg: Cargo = sim.facts["cargo_cfg"]
    aid_cfg: Aid = sim.facts["aid_cfg"]
    dexterity_name: str = sim.facts["dexterity"]
    hurry: int = sim.facts["hurry"]
    need = severity(place, cargo_cfg, hurry)
    score = control_score(aid_cfg, dexterity_name)
    wobble = max(0, need - aid_cfg.stability)
    sim.get("cargo").meters["wobble"] += wobble
    if score < need:
        sim.get("cargo").meters["spill"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("cargo").meters["wobble"],
        "spill": sim.get("cargo").meters["spill"] >= THRESHOLD,
        "danger": sim.get("route").meters["danger"],
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place, cargo: Cargo) -> None:
    hero.memes["pride"] += 1
    hero.memes["awe"] += 1
    world.say(
        f"In {place.label}, folks said {hero.id}'s dexterity was so fine "
        f"{hero.pronoun()} could button a shirt in a dust storm and never miss a hole."
    )
    world.say(
        f"On the morning of the fair, {place.opening} and {helper.id} pointed at "
        f"{cargo.phrase}. {cargo.boast}"
    )


def assign_task(world: World, hero: Entity, helper: Entity, cargo: Cargo, aid: Aid) -> None:
    world.say(
        f'"If anyone can carry {cargo.label} to the judging tent, it is {hero.id}," '
        f"{helper.id} said. {hero.id} took {aid.phrase} and {aid.carry_text}."
    )
    hero.meters["carried"] += 1
    world.get("cargo").meters["carried"] += 1


def foreshadow(world: World, helper: Entity, place: Place, cargo: Cargo) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_spill"] = pred["spill"]
    helper.memes["worry"] += 1
    line = (
        f"Before they even reached {place.route}, {place.omen} "
        f"{helper.id} narrowed {helper.pronoun('possessive')} eyes at {cargo.container}."
    )
    if pred["spill"]:
        line += (
            f' "That load is already whispering trouble," {helper.pronoun()} said.'
        )
    else:
        line += (
            f' "That road likes to test steady hands," {helper.pronoun()} said.'
        )
    world.say(line)


def set_off(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"Off {hero.pronoun()} went toward {place.route}, walking so carefully that "
        f"even the pebbles seemed to hold their breath."
    )


def trouble(world: World, hero: Entity, helper: Entity, place: Place, cargo: Cargo, aid: Aid, dexterity_name: str, hurry: int) -> None:
    need = severity(place, cargo, hurry)
    score = control_score(aid, dexterity_name)
    wobble = max(1, need - aid.stability)
    world.get("cargo").meters["wobble"] += wobble
    propagate(world, narrate=False)
    hero.memes["focus"] += 1
    world.say(
        f"Halfway along {place.route}, {place.hazard_text} {cargo.container} tipped, "
        f"wavered, and gave one long shiver that could have frightened the freckles "
        f"off a turnip."
    )
    if score >= need:
        world.say(
            f"But {hero.id} bent knees, tightened fingers, and showed the sort of "
            f"dexterity people talk about for years. {aid.save_text}"
        )
    else:
        world.say(
            f"{hero.id} tried to answer with quick hands, but the wobble was bigger "
            f"than one child and one tool. {aid.fail_text}"
        )


def finish_smooth(world: World, hero: Entity, helper: Entity, place: Place, cargo: Cargo) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.get("cargo").meters["delivered"] += 1
    world.say(
        f"They reached the judging tent with every bit of {cargo.label} still where it belonged. "
        f"The crowd let out one cheer, then another, and then a third because one cheer did not seem big enough."
    )
    world.say(
        f"By supper, people were saying {place.ending_image}, and that was how "
        f"{hero.id} became the child who could carry {cargo.ending} without losing so much as a crumb."
    )


def finish_saved(world: World, hero: Entity, helper: Entity, place: Place, cargo: Cargo) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.get("cargo").meters["delivered"] += 1
    world.say(
        f"For one heartbeat it looked as if the day would end in a grand splat, "
        f"but {hero.id} coaxed the load back into line and marched on."
    )
    world.say(
        f"They arrived a little rumpled but still triumphant. By sunset, people were saying "
        f"{place.ending_image}, and even the judges tipped their hats to that rescue."
    )


def finish_spilled(world: World, hero: Entity, helper: Entity, place: Place, cargo: Cargo) -> None:
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.get("cargo").meters["spill"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The whole load came apart in a mighty, ridiculous tumble, and {cargo.mess} spread "
        f"across {place.route} so wide a goose could have skated over it."
    )
    world.say(
        f"{hero.id} looked near tears, but {helper.id} squeezed {hero.pronoun('possessive')} shoulder. "
        f'"Big tales are not made only of winning," {helper.pronoun()} said. '
        f'"Next time we listen when the road starts hinting."'
    )
    world.say(
        f"That evening, the town still laughed kindly about the day {cargo.ending} met the ground, "
        f"and {hero.id} promised to bring both patience and dexterity to the next fair."
    )
def tell(
    cargo_cfg: Cargo,
    aid_cfg: Aid,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    dexterity_name: str,
    hurry: Hurry,
    place=None,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    route = world.add(Entity(id="route", kind="thing", type="route", label=place.route))
    cargo = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo_cfg.label))
    aid = world.add(Entity(id="aid", kind="thing", type="aid", label=aid_cfg.label))
    hero.meters["dexterity"] = float(DEXTERITY_LEVELS[dexterity_name])
    hero.attrs["dexterity_name"] = dexterity_name
    helper.attrs["relationship"] = "helper"
    world.facts.update(
        place=place,
        cargo_cfg=cargo_cfg,
        aid_cfg=aid_cfg,
        dexterity=dexterity_name,
        hurry=hurry,
        hero=hero,
        helper=helper,
        route=route,
        cargo=cargo,
        aid=aid,
    )

    introduce(world, hero, helper, place, cargo_cfg)
    assign_task(world, hero, helper, cargo_cfg, aid_cfg)

    world.para()
    foreshadow(world, helper, place, cargo_cfg)
    set_off(world, hero, place)

    world.para()
    trouble(world, hero, helper, place, cargo_cfg, aid_cfg, dexterity_name, hurry)

    outcome = outcome_of(
        StoryParams(
            place=place.id,
            cargo=cargo_cfg.id,
            aid=aid_cfg.id,
            hero=hero_name,
            gender=hero_gender,
            helper=helper_name,
            helper_gender=helper_gender,
            dexterity=dexterity_name,
            hurry=hurry,
            seed=None,
        )
    )
    world.facts["outcome"] = outcome
    if outcome == "smooth":
        world.para()
        finish_smooth(world, hero, helper, place, cargo_cfg)
    elif outcome == "saved":
        world.para()
        finish_saved(world, hero, helper, place, cargo_cfg)
    else:
        world.para()
        finish_spilled(world, hero, helper, place, cargo_cfg)

    return world
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


PLACES = {
    "river_fair": Place(
        id="river_fair",
        label="River Fair",
        opening="the tents flapped like bright sails beside the brown water",
        route="the rope bridge",
        omen="the bridge ropes hummed like a fiddle string before a snap.",
        hazard_text="a river gust came curling up from below, and the bridge planks gave a hop",
        difficulty=3,
        ending_image="the rope bridge had learned better than to argue with a steady child",
        tags={"bridge", "wind", "fair"},
    ),
    "prairie_fair": Place(
        id="prairie_fair",
        label="Prairie Fair",
        opening="the fairground shone yellow under a sun as broad as a brass plate",
        route="the wagon-rutted lane",
        omen="the lane twitched in the heat, and every rut looked hungry for a wheel.",
        hazard_text="one deep rut grabbed at a boot and jolted the whole burden sideways",
        difficulty=2,
        ending_image="even the ruts laid down flat when that child walked by",
        tags={"lane", "rut", "fair"},
    ),
    "mesa_market": Place(
        id="mesa_market",
        label="Mesa Market",
        opening="the market bells rang under red cliffs high enough to scrape the moon",
        route="the windy cliff path",
        omen="the cliff wind kept taking practice nips at aprons and hat brims.",
        hazard_text="a sidewind slapped across the path and tried to peel the load away",
        difficulty=4,
        ending_image="the cliff wind had to tip its hat to finer hands than its own",
        tags={"cliff", "wind", "market"},
    ),
}

CARGOS = {
    "pies": Cargo(
        id="pies",
        label="the stack of pies",
        phrase="a pie stack tall enough to shade a calf",
        kind="stack",
        container="the wobbling pie board",
        top_heavy=2,
        mess="blueberry filling and crust",
        boast="It was said that stack had one more pie than sensible arithmetic allowed.",
        ending="a tower of pies through a bridge wind",
        tags={"pie", "stack"},
    ),
    "soup": Cargo(
        id="soup",
        label="the kettle of soup",
        phrase="a kettle of bean soup broad enough to reflect the sky",
        kind="sloshing",
        container="the soup kettle",
        top_heavy=1,
        mess="bean soup",
        boast="Old timers swore the spoon in that kettle was big enough to row across a pond.",
        ending="a sky-sized kettle of soup over bad ground",
        tags={"soup", "kettle"},
    ),
    "pumpkins": Cargo(
        id="pumpkins",
        label="the crate of pumpkins",
        phrase="a crate of pumpkins piled like orange cannonballs",
        kind="rolling",
        container="the pumpkin crate",
        top_heavy=2,
        mess="pumpkins and straw",
        boast="The crate was so full the top pumpkin looked ready to ask for a seat belt.",
        ending="a crate of pumpkins along a path that wanted to roll them home",
        tags={"pumpkin", "crate"},
    ),
}

AIDS = {
    "balancing_pole": Aid(
        id="balancing_pole",
        label="balancing pole",
        phrase="a long balancing pole",
        handles={"stack", "sloshing"},
        sense=3,
        stability=3,
        carry_text="spread both hands wide on it as if it were part of her own shoulders",
        save_text="The pole dipped one way, then the other, and the load obeyed her instead of the wind.",
        fail_text="The pole bowed like a fishing rod, and the burden kept right on arguing.",
        tags={"pole", "balance"},
    ),
    "sling_harness": Aid(
        id="sling_harness",
        label="sling harness",
        phrase="a broad sling harness",
        handles={"sloshing", "rolling"},
        sense=3,
        stability=3,
        carry_text="settled it across shoulders and hips so the weight sat close and mean",
        save_text="The harness caught the sway and spread it through her whole body until the shaking quieted.",
        fail_text="The harness strained and creaked, but the swing of the load got away from her.",
        tags={"harness", "carry"},
    ),
    "crate_braces": Aid(
        id="crate_braces",
        label="crate braces",
        phrase="a set of crate braces",
        handles={"rolling", "stack"},
        sense=2,
        stability=2,
        carry_text="lashed them tight with quick knots that made the crate stand straighter",
        save_text="The braces held just long enough for her to catch the lean and bully it back into place.",
        fail_text="The braces knocked once, twice, and then the whole cargo lurched past saving.",
        tags={"braces", "crate"},
    ),
    "mitten": Aid(
        id="mitten",
        label="one wool mitten",
        phrase="one wool mitten",
        handles={"stack"},
        sense=1,
        stability=0,
        carry_text="waved it as if softness could solve engineering",
        save_text="Against all common sense, it somehow helped.",
        fail_text="A mitten was no match for a fair-day disaster.",
        tags={"mitten"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Ada", "Tess", "Nell", "Molly", "Pearl", "Elsie"]
BOY_NAMES = ["Eli", "Bo", "Cal", "Jasper", "Otis", "Levi", "Sam", "Wade"]
HELPERS = [
    ("Uncle Cal", "man"),
    ("Aunt May", "woman"),
    ("Old Gus", "man"),
    ("Miss Wren", "woman"),
]
DEXTERITY_CHOICES = ["legendary", "nimble", "steady", "learning"]


KNOWLEDGE = {
    "bridge": [(
        "Why can a rope bridge be hard to cross with something heavy?",
        "A rope bridge moves under your feet, so a heavy load can start swinging. When the bridge and the load move together, it is harder to keep your balance."
    )],
    "wind": [(
        "Why can wind make carrying things difficult?",
        "Wind pushes sideways on whatever you are holding. That extra shove can turn a small wobble into a big one."
    )],
    "pie": [(
        "Why is a tall stack of pies hard to carry?",
        "A tall stack is top-heavy, so the weight is high up instead of low and steady. That makes the whole stack tip more easily."
    )],
    "soup": [(
        "Why does soup slosh in a kettle?",
        "Soup is a liquid, so it keeps moving after the pot moves. That sloshing can shove the kettle from side to side."
    )],
    "pumpkin": [(
        "Why do round pumpkins try to roll?",
        "Pumpkins are round and heavy, so they move when a crate tips. Once one starts rolling, it can push the others too."
    )],
    "balance": [(
        "What does dexterity mean?",
        "Dexterity means being skillful and careful with your hands and body. A person with good dexterity can control small movements very well."
    )],
    "pole": [(
        "How can a balancing pole help?",
        "A balancing pole spreads your weight from side to side. That can make a shaky load easier to steady."
    )],
    "harness": [(
        "What does a carrying harness do?",
        "A harness helps hold weight close to your body. That makes the load less wild and easier to control."
    )],
    "crate": [(
        "What do braces do on a crate?",
        "Braces help keep a crate stiff so it does not twist as much. A stiffer crate can keep things from rolling all at once."
    )],
    "foreshadowing": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is an early clue that hints at something important later. It helps the later trouble feel prepared instead of sudden."
    )],
}
KNOWLEDGE_ORDER = [
    "foreshadowing", "balance", "bridge", "wind", "pie", "soup",
    "pumpkin", "pole", "harness", "crate",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    cargo: Cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    if outcome == "spilled":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the word "dexterity" and uses foreshadowing. A child carries {cargo.phrase} across {place.route}, and the warning signs turn out to matter.',
            f"Tell a funny tall tale where {hero.id} is famous for dexterity, but {place.route} proves too wild and {cargo.label} spills everywhere.",
            f"Write a story with an early clue about danger, a huge wobble in the middle, and a warm ending where the child learns to heed the hint next time.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "dexterity" and uses foreshadowing. A child carries {cargo.phrase} across {place.route}.',
        f"Tell a tall tale where {hero.id}'s dexterity is tested by {place.route}, and {helper.id} notices the danger before it happens.",
        f"Write a playful story with a giant fair-day load, an early hint of trouble, and an ending that proves what the child managed to save.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    cargo_cfg: Cargo = f["cargo_cfg"]
    aid_cfg: Aid = f["aid_cfg"]
    outcome = f["outcome"]
    predicted_spill = f.get("predicted_spill", False)
    qas: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child known for unusual dexterity, and {helper.id}, who helps watch the load. Together they try to carry {cargo_cfg.label} through the fair."
        ),
        (
            f"What clue warned them that trouble might come on {place.route}?",
            f"The warning clue was that {place.omen} That early sign mattered because it hinted the road or bridge would try to shake the cargo later."
        ),
        (
            f"What was {hero.id} carrying, and why was it hard?",
            f"{hero.id} was carrying {cargo_cfg.phrase}. It was hard because the load was awkward and easy to wobble on {place.route}."
        ),
        (
            f"How did {aid_cfg.label} help?",
            f"{hero.id} used {aid_cfg.phrase} to control the load. It helped by matching the kind of burden they had and giving {hero.pronoun('object')} a steadier way to carry it."
        ),
    ]
    if outcome == "smooth":
        qas.append((
            f"Why did everything go well in the end?",
            f"It went well because {hero.id}'s dexterity and the right tool were stronger than the trouble on {place.route}. The early warning let everyone take the danger seriously before the big wobble came."
        ))
        qas.append((
            "How did the story end?",
            f"They reached the judging tent with the load still safe. The ending image shows that the town now tells stories about {hero.id}'s steady hands."
        ))
    elif outcome == "saved":
        qas.append((
            f"What almost happened in the middle of the story?",
            f"The load almost spilled when the path or bridge jolted it hard. The story had foreshadowed that moment with an early clue, so the wobble felt like the danger they had been warned about."
        ))
        qas.append((
            f"How was the load saved?",
            f"{hero.id} answered the wobble with quick hands and careful feet. The save worked because {hero.pronoun('possessive')} dexterity and {aid_cfg.label} were just enough together."
        ))
    else:
        qas.append((
            f"Why did {cargo_cfg.label} spill?",
            f"It spilled because the hazard on {place.route} made the cargo wobble harder than {hero.id} and the tool could manage. The story warned about that risk early, and then the clue came true."
        ))
        qas.append((
            "Was the ending mean or kind?",
            f"The ending was kind even though the cargo was lost. {helper.id} comforts {hero.id}, and the story turns the mistake into a lesson about listening to warning signs."
        ))
    if predicted_spill:
        qas.append((
            "What did the foreshadowing do in this story?",
            f"It gave a hint before the trouble arrived. That made the later spill or near-spill feel connected to the world instead of coming from nowhere."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place: Place = f["place"]
    cargo_cfg: Cargo = f["cargo_cfg"]
    aid_cfg: Aid = f["aid_cfg"]
    tags = {"foreshadowing", "balance"} | set(place.tags) | set(cargo_cfg.tags) | set(aid_cfg.tags)
    out: list[tuple[str, str]] = []
    tag_map = {
        "bridge": "bridge",
        "wind": "wind",
        "pie": "pie",
        "soup": "soup",
        "pumpkin": "pumpkin",
        "pole": "pole",
        "harness": "harness",
        "crate": "crate",
        "balance": "balance",
        "foreshadowing": "foreshadowing",
    }
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    cargo: str
    aid: str
    hero: str
    gender: str
    helper: str
    helper_gender: str
    dexterity: str
    hurry: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="river_fair",
        cargo="pies",
        aid="balancing_pole",
        hero="June",
        gender="girl",
        helper="Uncle Cal",
        helper_gender="man",
        dexterity="legendary",
        hurry=0,
    ),
    StoryParams(
        place="prairie_fair",
        cargo="pumpkins",
        aid="crate_braces",
        hero="Eli",
        gender="boy",
        helper="Aunt May",
        helper_gender="woman",
        dexterity="steady",
        hurry=0,
    ),
    StoryParams(
        place="mesa_market",
        cargo="soup",
        aid="sling_harness",
        hero="Mabel",
        gender="girl",
        helper="Old Gus",
        helper_gender="man",
        dexterity="nimble",
        hurry=1,
    ),
    StoryParams(
        place="river_fair",
        cargo="pies",
        aid="crate_braces",
        hero="Bo",
        gender="boy",
        helper="Miss Wren",
        helper_gender="woman",
        dexterity="learning",
        hurry=1,
    ),
]


def explain_rejection(place: Place, cargo: Cargo, aid: Aid) -> str:
    if not aid_works_for(aid, cargo):
        return (
            f"(No story: {aid.label} is not a sensible way to carry {cargo.label}. "
            f"It does not suit a {cargo.kind} load.)"
        )
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: {aid.label} scores too low on common sense for this world. "
            f"Choose a sturdier, more believable aid.)"
        )
    return (
        f"(No story: even with expert hands, {aid.label} is not enough for "
        f"{cargo.label} on {place.route}.)"
    )


ASP_RULES = r"""
compatible_aid(A, C) :- aid_handles(A, K), cargo_kind(C, K).
sensible(A) :- aid(A), sense(A, S), sense_min(M), S >= M.
possible(P, C, A) :- place(P), cargo(C), aid(A), compatible_aid(A, C), sensible(A),
                     dexterity(legendary, D), stability(A, ST), difficulty(P, DF),
                     top_heavy(C, TH), D + ST >= DF + TH.

need(P, C, H, N) :- difficulty(P, DF), top_heavy(C, TH), N = DF + TH + H.
control(A, X, V) :- stability(A, ST), dexterity(X, DX), V = ST + DX.

outcome(P, C, A, X, H, smooth) :- possible(P, C, A), need(P, C, H, N), control(A, X, V), V > N.
outcome(P, C, A, X, H, saved) :- possible(P, C, A), need(P, C, H, N), control(A, X, V), V = N.
outcome(P, C, A, X, H, spilled) :- possible(P, C, A), need(P, C, H, N), control(A, X, V), V < N.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("difficulty", pid, place.difficulty))
    for cid, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_kind", cid, cargo.kind))
        lines.append(asp.fact("top_heavy", cid, cargo.top_heavy))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("stability", aid_id, aid.stability))
        for kind in sorted(aid.handles):
            lines.append(asp.fact("aid_handles", aid_id, kind))
    for dex_name, level in DEXTERITY_LEVELS.items():
        lines.append(asp.fact("dexterity", dex_name, level))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show possible/3."))
    return sorted(set(asp.atoms(model, "possible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_dexterity", params.dexterity),
        asp.fact("chosen_hurry", params.hurry),
        "selected(O) :- chosen_place(P), chosen_cargo(C), chosen_aid(A), chosen_dexterity(X), chosen_hurry(H), outcome(P,C,A,X,H,O).",
    ])
    model = asp.one_model(asp_program(extra, "#show selected/1."))
    atoms = asp.atoms(model, "selected")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
        except StoryError as err:
            rc = 1
            print(f"Generation setup failed during verify: {err}")
            continue
        if py != cl:
            mismatches += 1
            print(f"Outcome mismatch for {params}: python={py} asp={cl}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        _ = smoke.to_json()
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"Smoke test failed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a child with famous dexterity carries an absurd load through a foreshadowed risk."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--dexterity", choices=DEXTERITY_CHOICES)
    ap.add_argument("--hurry", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cargo and args.aid:
        place = PLACES[args.place]
        cargo = CARGOS[args.cargo]
        aid = AIDS[args.aid]
        if not valid_combo(place, cargo, aid):
            raise StoryError(explain_rejection(place, cargo, aid))
    if args.aid and args.aid in AIDS and AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(
            f"(No story: {AIDS[args.aid].label} is intentionally kept as a bad idea and refused by this world.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cargo_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    default_names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(default_names)
    helper_name, helper_gender = rng.choice(HELPERS)
    if args.helper is not None:
        helper_name = args.helper
    if args.helper_gender is not None:
        helper_gender = args.helper_gender
    dexterity_name = args.dexterity or rng.choice(DEXTERITY_CHOICES)
    hurry = args.hurry if args.hurry is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        cargo=cargo_id,
        aid=aid_id,
        hero=hero,
        gender=gender,
        helper=helper_name,
        helper_gender=helper_gender,
        dexterity=dexterity_name,
        hurry=hurry,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.dexterity not in DEXTERITY_LEVELS:
        raise StoryError(f"(Unknown dexterity level: {params.dexterity})")
    place = PLACES[params.place]
    cargo = CARGOS[params.cargo]
    aid = AIDS[params.aid]
    if not valid_combo(place, cargo, aid):
        raise StoryError(explain_rejection(place, cargo, aid))

    world = tell(
        place=place,
        cargo_cfg=cargo,
        aid_cfg=aid,
        hero_name=params.hero,
        hero_gender=params.gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        dexterity_name=params.dexterity,
        hurry=params.hurry,
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
        print(asp_program("", "#show possible/3.\n#show outcome/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cargo, aid) combos:\n")
        for place, cargo, aid in combos:
            print(f"  {place:12} {cargo:10} {aid}")
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
            header = f"### {p.hero}: {p.cargo} at {p.place} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
