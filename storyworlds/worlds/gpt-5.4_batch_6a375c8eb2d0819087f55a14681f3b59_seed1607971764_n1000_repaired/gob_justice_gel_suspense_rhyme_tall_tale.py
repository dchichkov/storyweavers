#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gob_justice_gel_suspense_rhyme_tall_tale.py
======================================================================

A standalone story world for a tall-tale mystery about a missing jar of fair
gel, a sticky gob of clues, and a child who brings justice to a moonlit town.

The world rebuilds a small source-tale shape:

- In a boastful frontier town, the fair's famous gel goes missing before judging.
- A child investigator finds a gob of gel and follows a clue trail.
- Suspense rises while the town waits to see who took it and whether the prize
  can be saved.
- The culprit has a reason grounded in world state: hunger, heat, or both.
- The ending proves justice changed the world: the truth is told, the mess is
  mended, and the fair glows on.

The model prefers plausible clue methods:
- dusting flour is good for sticky trails on dry ground
- cooling works for runny gel in hot places
- a lantern works almost anywhere, though it solves less elegantly

Run it
------
    python storyworlds/worlds/gpt-5.4/gob_justice_gel_suspense_rhyme_tall_tale.py
    python storyworlds/worlds/gpt-5.4/gob_justice_gel_suspense_rhyme_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gob_justice_gel_suspense_rhyme_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/gob_justice_gel_suspense_rhyme_tall_tale.py --asp
    python storyworlds/worlds/gpt-5.4/gob_justice_gel_suspense_rhyme_tall_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Gel:
    id: str
    label: str
    phrase: str
    color: str
    scent: str
    sticky: bool
    runny: bool
    heat_risk: bool
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    terrain: str
    hot: bool
    dry_ground: bool
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    needs_sticky: bool = False
    needs_runny: bool = False
    needs_dry_ground: bool = False
    cools: bool = False
    works_anywhere: bool = False
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
class Culprit:
    id: str
    label: str
    phrase: str
    hunger: int
    nimble: bool
    kind: str = "animal"
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


def _r_spill_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("gel_spilled", 0.0) < THRESHOLD:
        return out
    if ("spill_alarm",) in world.fired:
        return out
    world.fired.add(("spill_alarm",))
    world.get("hero").memes["worry"] += 1
    world.get("judge").memes["worry"] += 1
    world.get("town").meters["delay"] += 1
    out.append("__spill__")
    return out


def _r_reveal_trail(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("trail_found", 0.0) < THRESHOLD:
        return out
    if ("reveal",) in world.fired:
        return out
    world.fired.add(("reveal",))
    world.get("hero").memes["hope"] += 1
    world.get("helper").memes["pride"] += 1
    out.append("__trail__")
    return out


def _r_truth_calms(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("truth_told", 0.0) < THRESHOLD:
        return out
    if ("truth_calms",) in world.fired:
        return out
    world.fired.add(("truth_calms",))
    world.get("judge").memes["relief"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("town").meters["delay"] = 0.0
    out.append("__truth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill_alarm", tag="social", apply=_r_spill_alarm),
    Rule(name="reveal_trail", tag="social", apply=_r_reveal_trail),
    Rule(name="truth_calms", tag="social", apply=_r_truth_calms),
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


def tool_fits(tool: Tool, gel: Gel, hiding: HidingPlace) -> bool:
    if tool.sense < SENSE_MIN:
        return False
    if tool.works_anywhere:
        return True
    if tool.needs_sticky and not gel.sticky:
        return False
    if tool.needs_runny and not gel.runny:
        return False
    if tool.needs_dry_ground and not hiding.dry_ground:
        return False
    if tool.cools and not hiding.hot:
        return False
    return (tool.needs_sticky or tool.needs_runny or tool.cools or tool.works_anywhere)


def culprit_can_take(culprit: Culprit, hiding: HidingPlace) -> bool:
    if hiding.id in {"windmill_loft", "hayloft"}:
        return culprit.nimble
    return True


def likely_spill(gel: Gel, hiding: HidingPlace) -> bool:
    return gel.runny or hiding.hot


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for gel_id, gel in GELS.items():
        for hiding_id, hiding in HIDING_PLACES.items():
            for tool_id, tool in TOOLS.items():
                if tool_fits(tool, gel, hiding):
                    combos.append((gel_id, hiding_id, tool_id))
    return combos


def predict_case(gel: Gel, hiding: HidingPlace, tool: Tool) -> dict:
    return {
        "spill": likely_spill(gel, hiding),
        "tool_works": tool_fits(tool, gel, hiding),
    }


def open_fair(world: World, hero: Entity, helper: Entity, judge: Entity, gel: Gel) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In Braggle Butte, folks boasted that the moon rose slower just to stare at the fair. "
        f"That year the grand prize sat beside {gel.phrase}, a jar so huge it looked fit to glaze a hill."
    )
    world.say(
        f"{hero.id} and {helper.id} were helping Judge Juniper when the brass band stopped mid-toot. "
        f'"Where is the {gel.label}?" the judge cried. "Without it, the ribbon table will feel mighty bare!"'
    )


def notice_gob(world: World, hero: Entity, gel: Gel) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then {hero.id} spotted a gob of {gel.color} gel on the table leg. "
        f"It trembled in the lantern glow as if it knew a secret and meant to keep it."
    )
    world.say(
        f'"A gob, a blob, a moonlit slop," {hero.id} whispered. "That little drop may make the truth hop."'
    )


def fear_waiting(world: World, judge: Entity) -> None:
    judge.memes["worry"] += 1
    world.say(
        f"The judge gripped the ribbon book so tight the pages fluttered. "
        f"If dawn came before the mystery broke, the whole town would mutter that justice had overslept."
    )


def choose_tool(world: World, hero: Entity, tool: Tool, hiding: HidingPlace, gel: Gel) -> None:
    pred = predict_case(gel, hiding, tool)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_tool_works"] = pred["tool_works"]
    if tool.id == "flour_dust":
        world.say(
            f"{hero.id} took {tool.phrase} from the pie tent. "
            f'"Dust for the crust, truth from the dust," {hero.pronoun()} said.'
        )
    elif tool.id == "cool_pan":
        world.say(
            f"{hero.id} grabbed {tool.phrase} from the ice cart. "
            f'"Cool the ooze and the trail won\'t lose," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f"{hero.id} lifted {tool.phrase}. "
            f'"Light for the night, and maybe for right," {hero.pronoun()} said.'
        )


def follow_trail(world: World, hero: Entity, helper: Entity, tool: Tool, hiding: HidingPlace, gel: Gel) -> None:
    world.facts["gel_spilled"] = 1.0 if likely_spill(gel, hiding) else 0.0
    propagate(world, narrate=False)
    hero.memes["bravery"] += 1
    helper.memes["bravery"] += 1

    if tool.id == "flour_dust":
        world.say(
            f"Out by {hiding.phrase}, {hero.id} shook flour over the ground. "
            f"At once the sticky specks lit up in white freckles, and a secret trail curled forward."
        )
    elif tool.id == "cool_pan":
        world.say(
            f"Near {hiding.phrase}, the night was so warm that the gel kept trying to slither away. "
            f"{hero.id} pressed the cold pan close, and the shining drips stiffened long enough to follow."
        )
    else:
        world.say(
            f"At {hiding.phrase}, {hero.id} raised the lantern high. "
            f"The gel gleamed in thin streaks, and the path winked ahead like a nervous little comet."
        )

    world.facts["trail_found"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"The trail led on and on, and every board creak sounded like a drum. "
        f"For a breath the dark seemed bigger than the town itself."
    )


def discover_culprit(world: World, hero: Entity, helper: Entity, culprit_ent: Entity,
                     culprit_cfg: Culprit, hiding: HidingPlace, gel: Gel) -> None:
    culprit_ent.meters["found"] += 1
    culprit_ent.memes["guilt"] += 1
    hungry = culprit_cfg.hunger >= 3
    world.say(
        f"Behind {hiding.phrase}, they found {culprit_cfg.phrase} hugging the great jar. "
        f"{culprit_ent.pronoun().capitalize()} had not eaten the whole thing, but {culprit_ent.pronoun('possessive')} whiskers were slick with {gel.color} shine."
    )
    if hungry:
        world.say(
            f'"I only meant to taste one brave lick," {culprit_cfg.label} said. '
            f'"But the jar was heavy, my paws were quick, and then the whole sticky business got thick."'
        )
    else:
        world.say(
            f'"I hid it so nobody would laugh at the wobble," {culprit_cfg.label} said. '
            f'"When the warm boards made it jiggle, I feared I had made a terrible trouble."'
        )


def bring_jar_back(world: World, hero: Entity, helper: Entity, gel_ent: Entity, gel: Gel) -> None:
    gel_ent.attrs["returned"] = True
    gel_ent.meters["saved"] += 1
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Together they heaved the jar back on a wagon. "
        f"It wobbled once, twice, and then rode steady, proud as a sunrise in a glass coat."
    )


def judge_case(world: World, judge: Entity, hero: Entity, culprit_ent: Entity,
               culprit_cfg: Culprit, gel: Gel) -> None:
    world.facts["truth_told"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Back at the fair, Judge Juniper heard the whole tale and did not thunder first. "
        f"She looked at the gob of spilled gel, the trembling culprit, and the jar that had been saved."
    )
    world.say(
        f'"Justice is not just a shout," the judge said. "It is the truth brought out. '
        f'What was taken must be carried back, and what was spilled must be mended."'
    )
    culprit_ent.meters["repair_work"] += 1
    if culprit_cfg.hunger >= 3:
        world.say(
            f"So {culprit_cfg.label} helped scrub the sticky boards and, after the contest, got a fair spoonful in a clean bowl. "
            f"That was justice with sense in it: firm, plain, and kind."
        )
    else:
        world.say(
            f"So {culprit_cfg.label} helped scrub the sticky boards and stood beside the table to tell the truth to every listener. "
            f"That was justice with daylight in it: firm, plain, and kind."
        )


def ending_image(world: World, hero: Entity, helper: Entity, judge: Entity, gel: Gel) -> None:
    world.say(
        f"When the ribbon was finally tied, the whole square cheered so loud the weather vane nearly saluted. "
        f"The {gel.label} shone under the lanterns, the sticky mess was gone, and nobody had to guess anymore."
    )
    world.say(
        f'{hero.id} grinned at {helper.id}. "Gob to blob, clue to proof, rhyme to right," {hero.pronoun()} said. '
        f'"That is how Braggle Butte sleeps easy tonight."'
    )


def tell(gel: Gel, hiding: HidingPlace, tool: Tool, culprit_cfg: Culprit,
         hero_name: str = "Mabel", hero_type: str = "girl",
         helper_name: str = "Jed", helper_type: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    judge = world.add(Entity(id="judge", kind="character", type="woman", label="Judge Juniper", role="judge"))
    culprit_ent = world.add(Entity(id="culprit", kind="character", type="animal", label=culprit_cfg.label, role="culprit"))
    gel_ent = world.add(Entity(id="gel_jar", type="jar", label=gel.label))
    town = world.add(Entity(id="town", type="town", label="Braggle Butte"))

    hero.attrs["name"] = hero_name
    helper.attrs["name"] = helper_name
    culprit_ent.attrs["nimble"] = culprit_cfg.nimble
    culprit_ent.attrs["hungry"] = culprit_cfg.hunger
    gel_ent.attrs["returned"] = False

    world.facts["gel_spilled"] = 0.0
    world.facts["trail_found"] = 0.0
    world.facts["truth_told"] = 0.0
    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name

    open_fair(world, hero, helper, judge, gel)
    world.para()
    notice_gob(world, hero, gel)
    fear_waiting(world, judge)
    choose_tool(world, hero, tool, hiding, gel)

    world.para()
    follow_trail(world, hero, helper, tool, hiding, gel)
    discover_culprit(world, hero, helper, culprit_ent, culprit_cfg, hiding, gel)

    world.para()
    bring_jar_back(world, hero, helper, gel_ent, gel)
    judge_case(world, judge, hero, culprit_ent, culprit_cfg, gel)
    ending_image(world, hero, helper, judge, gel)

    world.facts.update(
        gel=gel,
        hiding=hiding,
        tool=tool,
        culprit_cfg=culprit_cfg,
        hero=hero,
        helper=helper,
        judge=judge,
        culprit=culprit_ent,
        gel_entity=gel_ent,
        suspense=True,
        justice_done=True,
        spill=likely_spill(gel, hiding),
    )
    return world


GELS = {
    "plum": Gel(
        id="plum",
        label="plum-proud gel",
        phrase="a barrel-big jar of plum-proud gel",
        color="purple",
        scent="sweet plum",
        sticky=True,
        runny=False,
        heat_risk=False,
        tags={"gel", "plum"},
    ),
    "mint": Gel(
        id="mint",
        label="mint-mountain gel",
        phrase="a hill-high jar of mint-mountain gel",
        color="green",
        scent="cool mint",
        sticky=False,
        runny=True,
        heat_risk=True,
        tags={"gel", "mint"},
    ),
    "peach": Gel(
        id="peach",
        label="peach-lightning gel",
        phrase="a thunder-sized jar of peach-lightning gel",
        color="gold",
        scent="sunny peach",
        sticky=True,
        runny=True,
        heat_risk=True,
        tags={"gel", "peach"},
    ),
}

HIDING_PLACES = {
    "hayloft": HidingPlace(
        id="hayloft",
        label="hayloft",
        phrase="the hayloft above the mule stalls",
        terrain="boards",
        hot=False,
        dry_ground=True,
        tags={"barn", "loft"},
    ),
    "windmill_loft": HidingPlace(
        id="windmill_loft",
        label="windmill loft",
        phrase="the windmill loft over the cistern",
        terrain="boards",
        hot=True,
        dry_ground=True,
        tags={"windmill", "loft", "hot"},
    ),
    "shade_crate": HidingPlace(
        id="shade_crate",
        label="shade crate",
        phrase="the peach crates behind the lemonade shade",
        terrain="packed dirt",
        hot=False,
        dry_ground=True,
        tags={"market", "shade"},
    ),
    "pump_bank": HidingPlace(
        id="pump_bank",
        label="pump bank",
        phrase="the damp pump bank by the stock trough",
        terrain="mud",
        hot=False,
        dry_ground=False,
        tags={"pump", "mud"},
    ),
}

TOOLS = {
    "flour_dust": Tool(
        id="flour_dust",
        label="flour dust",
        phrase="a scoop of pie flour",
        sense=3,
        needs_sticky=True,
        needs_dry_ground=True,
        tags={"flour", "clue"},
    ),
    "cool_pan": Tool(
        id="cool_pan",
        label="cool pan",
        phrase="a cold tin pan packed with ice chips",
        sense=3,
        needs_runny=True,
        cools=True,
        tags={"cold", "clue"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="the brass lantern from the judge's rail",
        sense=2,
        works_anywhere=True,
        tags={"light", "clue"},
    ),
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="a dance-hall broom",
        sense=1,
        needs_sticky=False,
        needs_runny=False,
        needs_dry_ground=False,
        cools=False,
        works_anywhere=False,
        tags={"bad_idea"},
    ),
}

CULPRITS = {
    "raccoon": Culprit(
        id="raccoon",
        label="Rascal Raccoon",
        phrase="Rascal Raccoon",
        hunger=3,
        nimble=True,
        tags={"animal", "hunger"},
    ),
    "goat": Culprit(
        id="goat",
        label="Gretta Goat",
        phrase="Gretta Goat",
        hunger=2,
        nimble=False,
        tags={"animal"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="Midnight Magpie",
        phrase="Midnight Magpie",
        hunger=1,
        nimble=True,
        tags={"animal", "bird"},
    ),
}

GIRL_NAMES = ["Mabel", "Pearl", "Dottie", "Ruby", "Cora", "Nell"]
BOY_NAMES = ["Jed", "Hank", "Otis", "Cal", "Beau", "Finn"]
TRAITS = ["steady", "curious", "brave", "sharp-eyed", "patient"]


@dataclass
class StoryParams:
    gel: str
    hiding_place: str
    tool: str
    culprit: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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
    "gel": [
        (
            "What is gel?",
            "Gel is a thick, wobbly kind of food or goo. It can hold its shape a little, but it can also jiggle or smear."
        )
    ],
    "justice": [
        (
            "What does justice mean?",
            "Justice means finding out what really happened and making things as right as possible. It is not just punishment; it is also truth and repair."
        )
    ],
    "raccoon": [
        (
            "Why do raccoons get into food?",
            "Raccoons are clever animals and often look for easy snacks. If food is left out, they may try to grab some."
        )
    ],
    "goat": [
        (
            "Why do goats nibble strange things?",
            "Goats are curious and like to mouth or nibble objects while they explore. That can get them into trouble around food and tools."
        )
    ],
    "magpie": [
        (
            "Why do magpies notice shiny things?",
            "Magpies are alert birds and often investigate bright or unusual objects. A gleaming jar or lantern can catch their attention."
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in the dark?",
            "A lantern spreads light so you can see where to step and what is nearby. In a mystery, good light can turn a guess into a clue."
        )
    ],
    "flour": [
        (
            "How can flour help show a trail?",
            "If something sticky is on the ground, flour can cling to it and make it easier to see. That can help a person follow where the mess went."
        )
    ],
    "cold": [
        (
            "Why can cold help with runny gel?",
            "Cold can make some soft things firmer and less drippy for a little while. That gives people time to carry or study them more carefully."
        )
    ],
}
KNOWLEDGE_ORDER = ["gel", "justice", "raccoon", "goat", "magpie", "lantern", "flour", "cold"]


def culprit_question_name(culprit_cfg: Culprit) -> str:
    return culprit_cfg.label


def generation_prompts(world: World) -> list[str]:
    gel = world.facts["gel"]
    culprit_cfg = world.facts["culprit_cfg"]
    hiding = world.facts["hiding"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "gob," "justice," and "gel." Make it suspenseful but gentle.',
        f"Tell a rhyming frontier-fair mystery where a giant jar of {gel.label} goes missing, a child follows a clue to {hiding.label}, and the truth brings justice.",
        f"Write a playful suspense story in a tall-tale voice where {culprit_cfg.label} causes trouble, but the ending is kind, clear, and fair.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    judge = world.facts["judge"]
    gel = world.facts["gel"]
    hiding = world.facts["hiding"]
    tool = world.facts["tool"]
    culprit_cfg = world.facts["culprit_cfg"]
    spill = world.facts["spill"]

    qa: list[tuple[str, str]] = [
        (
            "What was missing at the fair?",
            f"The huge jar of {gel.label} was missing. Without it, the judge worried the prize table would be left empty and the fair would stall."
        ),
        (
            f"What clue did {hero.label} find first?",
            f"{hero.label} found a gob of {gel.color} gel on the table leg. That tiny sticky clue showed that the jar had been moved, not simply misplaced."
        ),
        (
            f"Why did the story feel suspenseful?",
            f"It was night, the fair was waiting, and nobody knew who had taken the jar. Every step along the dark trail mattered because the town needed the truth before dawn."
        ),
        (
            f"How did {hero.label} follow the trail?",
            f"{hero.label} used {tool.phrase} to make the clue easier to see. That worked because the gel and the place matched the method, so the hidden trail could finally show itself."
        ),
        (
            f"Who had the jar, and why?",
            f"{culprit_question_name(culprit_cfg)} had hidden the jar near {hiding.phrase}. {culprit_cfg.label} did it because {'hunger tugged too hard' if culprit_cfg.hunger >= 3 else 'the wobbling jar caused panic and hiding seemed easier than telling the truth'}."
        ),
        (
            "What did the judge mean by justice?",
            f"{judge.label} meant that the truth had to be told and the mess had to be repaired. The ending was fair because the jar was returned, the sticky boards were cleaned, and the culprit faced the problem honestly."
        ),
    ]
    if spill:
        qa.append(
            (
                "Did the gel make a mess on the way?",
                f"Yes. The gel spilled as it was carried off, which is why there was a visible trail to follow. That messy trail became the very clue that helped solve the mystery."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gel", "justice"}
    culprit = world.facts["culprit_cfg"]
    tool = world.facts["tool"]
    if culprit.id == "raccoon":
        tags.add("raccoon")
    elif culprit.id == "goat":
        tags.add("goat")
    else:
        tags.add("magpie")
    if tool.id == "lantern":
        tags.add("lantern")
    elif tool.id == "flour_dust":
        tags.add("flour")
    elif tool.id == "cool_pan":
        tags.add("cold")

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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        gel="plum",
        hiding_place="hayloft",
        tool="flour_dust",
        culprit="raccoon",
        hero_name="Mabel",
        hero_gender="girl",
        helper_name="Jed",
        helper_gender="boy",
    ),
    StoryParams(
        gel="mint",
        hiding_place="windmill_loft",
        tool="cool_pan",
        culprit="magpie",
        hero_name="Pearl",
        hero_gender="girl",
        helper_name="Cal",
        helper_gender="boy",
    ),
    StoryParams(
        gel="peach",
        hiding_place="shade_crate",
        tool="lantern",
        culprit="goat",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
    ),
    StoryParams(
        gel="peach",
        hiding_place="pump_bank",
        tool="lantern",
        culprit="raccoon",
        hero_name="Nell",
        hero_gender="girl",
        helper_name="Beau",
        helper_gender="boy",
    ),
]


def explain_combo_rejection(gel: Gel, hiding: HidingPlace, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.label} is a weak clue method here. The world knows better tools and refuses a sillier one.)"
        )
    if tool.needs_sticky and not gel.sticky:
        return (
            f"(No story: {tool.label} only helps with sticky gel, but {gel.label} is too runny or slick for that method.)"
        )
    if tool.needs_runny and not gel.runny:
        return (
            f"(No story: {tool.label} helps firm up runny gel, but {gel.label} is already thick enough that cooling solves nothing.)"
        )
    if tool.needs_dry_ground and not hiding.dry_ground:
        return (
            f"(No story: {tool.label} needs dry ground or boards to show a trail, but {hiding.phrase} is too damp and muddy.)"
        )
    if tool.cools and not hiding.hot:
        return (
            f"(No story: {tool.label} matters when heat makes the gel slip away, but {hiding.phrase} is not hot enough for cooling to be the key clue.)"
        )
    return "(No story: that clue method does not honestly fit this gel and hiding place.)"


def explain_culprit_rejection(culprit_cfg: Culprit, hiding: HidingPlace) -> str:
    return (
        f"(No story: {culprit_cfg.label} is not nimble enough to hide a giant jar in {hiding.phrase}. Pick a ground-level place or a nimbler culprit.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "justice"


ASP_RULES = r"""
valid_combo(G,H,T) :- gel(G), hiding_place(H), tool(T), sensible(T), tool_fits(T,G,H).

sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.

tool_fits(T,G,H) :- works_anywhere(T).
tool_fits(T,G,H) :- needs_sticky(T), sticky(G), needs_dry_ground(T), dry_ground(H).
tool_fits(T,G,H) :- needs_runny(T), runny(G), cools(T), hot(H).
tool_fits(T,G,H) :- needs_runny(T), runny(G), not cools(T), not needs_dry_ground(T).
tool_fits(T,G,H) :- needs_sticky(T), sticky(G), not needs_dry_ground(T).

culprit_ok(C,H) :- culprit(C), hiding_place(H), not loft(H).
culprit_ok(C,H) :- culprit(C), hiding_place(H), loft(H), nimble(C).

spill(G,H) :- runny(G).
spill(G,H) :- hot(H), heat_risk(G).

outcome(justice) :- valid_combo(G,H,T), chosen_gel(G), chosen_hiding(H), chosen_tool(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, gel in GELS.items():
        lines.append(asp.fact("gel", gid))
        if gel.sticky:
            lines.append(asp.fact("sticky", gid))
        if gel.runny:
            lines.append(asp.fact("runny", gid))
        if gel.heat_risk:
            lines.append(asp.fact("heat_risk", gid))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", hid))
        if hiding.dry_ground:
            lines.append(asp.fact("dry_ground", hid))
        if hiding.hot:
            lines.append(asp.fact("hot", hid))
        if "loft" in hid:
            lines.append(asp.fact("loft", hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        if tool.needs_sticky:
            lines.append(asp.fact("needs_sticky", tid))
        if tool.needs_runny:
            lines.append(asp.fact("needs_runny", tid))
        if tool.needs_dry_ground:
            lines.append(asp.fact("needs_dry_ground", tid))
        if tool.cools:
            lines.append(asp.fact("cools", tid))
        if tool.works_anywhere:
            lines.append(asp.fact("works_anywhere", tid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if culprit.nimble:
            lines.append(asp.fact("nimble", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_culprit_ok() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show culprit_ok/2."))
    return sorted(set(asp.atoms(model, "culprit_ok")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_gel", params.gel),
            asp.fact("chosen_hiding", params.hiding_place),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    python_culprits = {
        (cid, hid)
        for cid, culprit in CULPRITS.items()
        for hid, hiding in HIDING_PLACES.items()
        if culprit_can_take(culprit, hiding)
    }
    clingo_culprits = set(asp_culprit_ok())
    if python_culprits == clingo_culprits:
        print(f"OK: culprit mobility matches ({len(clingo_culprits)} pairs).")
    else:
        rc = 1
        print("MISMATCH in culprit mobility:")
        if clingo_culprits - python_culprits:
            print("  only in clingo:", sorted(clingo_culprits - python_culprits))
        if python_culprits - clingo_culprits:
            print("  only in python:", sorted(python_culprits - clingo_culprits))

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {s}.")
            break

    mismatch = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated smoke-test story was empty.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery world: a gob of gel, a missing jar, and justice before dawn."
    )
    ap.add_argument("--gel", choices=GELS)
    ap.add_argument("--hiding-place", choices=HIDING_PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gel and args.hiding_place and args.tool:
        gel = GELS[args.gel]
        hiding = HIDING_PLACES[args.hiding_place]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, gel, hiding):
            raise StoryError(explain_combo_rejection(gel, hiding, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        gel = GELS[args.gel] if args.gel else next(iter(GELS.values()))
        hiding = HIDING_PLACES[args.hiding_place] if args.hiding_place else next(iter(HIDING_PLACES.values()))
        raise StoryError(explain_combo_rejection(gel, hiding, TOOLS[args.tool]))
    if args.culprit and args.hiding_place:
        culprit = CULPRITS[args.culprit]
        hiding = HIDING_PLACES[args.hiding_place]
        if not culprit_can_take(culprit, hiding):
            raise StoryError(explain_culprit_rejection(culprit, hiding))

    combos = [
        combo for combo in valid_combos()
        if (args.gel is None or combo[0] == args.gel)
        and (args.hiding_place is None or combo[1] == args.hiding_place)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid gel / hiding place / tool combination matches the given options.)")

    gel_id, hiding_id, tool_id = rng.choice(sorted(combos))
    culprit_choices = [
        cid for cid, culprit in CULPRITS.items()
        if (args.culprit is None or cid == args.culprit)
        and culprit_can_take(culprit, HIDING_PLACES[hiding_id])
    ]
    if not culprit_choices:
        if args.culprit:
            raise StoryError(explain_culprit_rejection(CULPRITS[args.culprit], HIDING_PLACES[hiding_id]))
        raise StoryError("(No valid culprit matches the chosen hiding place.)")

    culprit_id = rng.choice(sorted(culprit_choices))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    helper_name = args.helper_name or pick_name(rng, helper_gender, avoid=hero_name)

    return StoryParams(
        gel=gel_id,
        hiding_place=hiding_id,
        tool=tool_id,
        culprit=culprit_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        gel = GELS[params.gel]
        hiding = HIDING_PLACES[params.hiding_place]
        tool = TOOLS[params.tool]
        culprit_cfg = CULPRITS[params.culprit]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not tool_fits(tool, gel, hiding):
        raise StoryError(explain_combo_rejection(gel, hiding, tool))
    if not culprit_can_take(culprit_cfg, hiding):
        raise StoryError(explain_culprit_rejection(culprit_cfg, hiding))

    world = tell(
        gel=gel,
        hiding=hiding,
        tool=tool,
        culprit_cfg=culprit_cfg,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_gender,
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
        print(asp_program("", "#show valid_combo/3.\n#show culprit_ok/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        culprits = set(asp_culprit_ok())
        print(f"{len(combos)} compatible (gel, hiding_place, tool) combos:\n")
        for gel_id, hiding_id, tool_id in combos:
            valid_culprits = sorted(cid for (cid, hid) in culprits if hid == hiding_id)
            print(f"  {gel_id:6} {hiding_id:13} {tool_id:10}  culprits=[{', '.join(valid_culprits)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.gel} at {p.hiding_place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
