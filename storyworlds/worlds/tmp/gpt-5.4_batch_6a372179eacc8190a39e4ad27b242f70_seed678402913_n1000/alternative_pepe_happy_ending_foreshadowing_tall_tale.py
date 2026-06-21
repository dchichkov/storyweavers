#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alternative_pepe_happy_ending_foreshadowing_tall_tale.py
====================================================================================

A standalone storyworld for a tall-tale-flavored story about Pepe, a windy
shortcut, and a safer alternative.

This little world rebuilds one simple shape:

- Pepe has a giant festival errand.
- The story foreshadows trouble with outsized signs of wind and a groaning bridge.
- A helper offers an alternative route.
- Either Pepe listens in time, or he learns after one scary wobble.
- The ending is always happy, concrete, and changed by the safer choice.

Run it
------
    python storyworlds/worlds/gpt-5.4/alternative_pepe_happy_ending_foreshadowing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/alternative_pepe_happy_ending_foreshadowing_tall_tale.py --cargo banner --alternative ferry
    python storyworlds/worlds/gpt-5.4/alternative_pepe_happy_ending_foreshadowing_tall_tale.py --setting mesa --alternative ferry
    python storyworlds/worlds/gpt-5.4/alternative_pepe_happy_ending_foreshadowing_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/alternative_pepe_happy_ending_foreshadowing_tall_tale.py --verify
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
PRIDE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "sensible", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    id: str
    place: str
    festival: str
    hill: str
    opening: str
    bridge_name: str
    affords: set[str] = field(default_factory=set)
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    goal: str
    carry_verb: str
    windage: int
    sturdy: int
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Alternative:
    id: str
    label: str
    phrase: str
    compatible_tags: set[str] = field(default_factory=set)
    path_text: str = ""
    rescue_text: str = ""
    ride_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Wind:
    id: str
    force: int
    sign: str
    omen: str
    bridge_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    helper_type: str
    label: str
    intro: str
    authority: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    cargo: str
    alternative: str
    wind: str
    helper: str
    trait: str
    seed: Optional[int] = None


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


def _r_bridge_risk(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.get("bridge")
    cargo = world.get("cargo")
    if bridge.meters["sway"] < THRESHOLD:
        return out
    sig = ("risk", "bridge")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["risk"] += 1
    world.get("Pepe").memes["fear"] += 1
    helper = world.get("helper")
    helper.memes["urgency"] += 1
    out.append("__bridge_risk__")
    return out


CAUSAL_RULES = [
    Rule(name="bridge_risk", tag="physical", apply=_r_bridge_risk),
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


SETTINGS = {
    "fairground": Setting(
        id="fairground",
        place="Dusty Bend Fairground",
        festival="the Cloud-Kite Supper",
        hill="Supper Bell Hill",
        opening="In Dusty Bend, even the chicken coops cast shadows as long as steamboats.",
        bridge_name="Whistle-Plank Bridge",
        affords={"orchard_road", "ferry"},
        ending_image="Below them, lanterns winked on one by one until the whole fairground looked like a necklace laid on the earth.",
        tags={"fair"},
    ),
    "river": Setting(
        id="river",
        place="Blue Barrel Landing",
        festival="the River Lantern Picnic",
        hill="Lantern Bluff",
        opening="At Blue Barrel Landing, folks said the river was so broad it needed two sunsets every evening.",
        bridge_name="Sing-Slat Bridge",
        affords={"ferry", "wagon_road"},
        ending_image="From the bluff, the river shone with floating lanterns, bright as a sky that had decided to practice being water.",
        tags={"river"},
    ),
    "mesa": Setting(
        id="mesa",
        place="Juniper Mesa",
        festival="the Big Sky Pie Parade",
        hill="Echo Top",
        opening="On Juniper Mesa, the wind had such long legs it could run around a barn before the door had time to slam.",
        bridge_name="Holler-Board Bridge",
        affords={"mule_path", "wagon_road"},
        ending_image="Across the mesa, banners snapped, fiddles skipped, and the whole parade curled below them like a bright ribbon.",
        tags={"mesa"},
    ),
}

CARGOES = {
    "banner": Cargo(
        id="banner",
        label="banner",
        phrase="a parade banner as wide as a bedsheet and twice as boastful",
        goal="hang it on the hilltop pole before the music started",
        carry_verb="carried the banner pole on his shoulder",
        windage=3,
        sturdy=1,
        plural=False,
        tags={"cloth", "festival"},
    ),
    "pie": Cargo(
        id="pie",
        label="pie",
        phrase="a blackberry pie so tall it needed its own weather report",
        goal="set it on the judges' table before the blue-ribbon bell rang",
        carry_verb="balanced the pie high in both hands",
        windage=1,
        sturdy=1,
        plural=False,
        tags={"food", "festival"},
    ),
    "pinwheels": Cargo(
        id="pinwheels",
        label="pinwheels",
        phrase="a bouquet of pinwheels that flashed like a pocketful of rainbows",
        goal="plant them by the bandstand at the top of the hill",
        carry_verb="hugged the pinwheels to his chest",
        windage=3,
        sturdy=2,
        plural=True,
        tags={"light", "festival"},
    ),
}

ALTERNATIVES = {
    "orchard_road": Alternative(
        id="orchard_road",
        label="orchard road",
        phrase="the orchard road",
        compatible_tags={"cloth", "food", "light", "festival"},
        path_text="the long orchard road, where the apple trees stood shoulder to shoulder and broke the worst of the wind",
        rescue_text="down off the first planks and pointed toward the orchard road",
        ride_text="They took the orchard road under bending apple branches, one careful step after another.",
        qa_text="They used the orchard road, where the trees blocked the hardest gusts.",
        tags={"road", "alternative"},
    ),
    "ferry": Alternative(
        id="ferry",
        label="ferry",
        phrase="the old ferry",
        compatible_tags={"cloth", "food", "light", "festival"},
        path_text="the old ferry, a flat boat that crossed low on the water while the bridge sang overhead",
        rescue_text="back to shore and waved for the old ferry",
        ride_text="They boarded the old ferry, which rocked gently and kept the cargo low and steady.",
        qa_text="They crossed by the old ferry instead of trusting the windy bridge.",
        tags={"boat", "alternative"},
    ),
    "wagon_road": Alternative(
        id="wagon_road",
        label="wagon road",
        phrase="the wagon road",
        compatible_tags={"food", "light", "festival"},
        path_text="the wagon road, broad and patient, with ruts deep enough to hold a shadow until noon",
        rescue_text="away from the bridge and led him to the wagon road",
        ride_text="They followed the wagon road, slow and steady, until the hill began to rise under their feet.",
        qa_text="They chose the wagon road, which was slower but steadier than the bridge.",
        tags={"road", "alternative"},
    ),
    "mule_path": Alternative(
        id="mule_path",
        label="mule path",
        phrase="the mule path",
        compatible_tags={"food", "festival"},
        path_text="the mule path, a tucked-away trail that curled behind the rocks where the wind could not get a good grip",
        rescue_text="toward the mule path behind the rocks",
        ride_text="They slipped onto the mule path, where even the bold wind had to duck and squeeze.",
        qa_text="They went by the sheltered mule path behind the rocks.",
        tags={"path", "alternative"},
    ),
}

WINDS = {
    "gusty": Wind(
        id="gusty",
        force=2,
        sign="the laundry on three porches all pointed west at once",
        omen="Even before he reached the bridge, Pepe noticed that the town windmills were turning so fast they looked like silver coins.",
        bridge_text="The boards gave a long fiddle-string hum under every puff of air.",
        tags={"wind"},
    ),
    "blustery": Wind(
        id="blustery",
        force=3,
        sign="a straw hat sailed off a scarecrow and landed two fences away",
        omen="Even before he reached the bridge, Pepe saw tumbleweeds racing each other and winning by a mile.",
        bridge_text="The rails complained and the planks hopped like fish on a dock.",
        tags={"wind"},
    ),
}

HELPERS = {
    "aunt": HelperCfg(
        id="aunt",
        helper_type="aunt",
        label="Aunt Lula",
        intro="Aunt Lula had hands strong enough to twist pie dough and stubborn weather into behaving.",
        authority=3,
        tags={"adult"},
    ),
    "grandpa": HelperCfg(
        id="grandpa",
        helper_type="grandfather",
        label="Grandpa Tico",
        intro="Grandpa Tico had crossed more creeks than there were buttons on his Sunday vest.",
        authority=4,
        tags={"adult"},
    ),
    "baker": HelperCfg(
        id="baker",
        helper_type="man",
        label="Mr. Bobo the baker",
        intro="Mr. Bobo the baker knew a wobbly thing the way a cat knows a leaking cream jug.",
        authority=2,
        tags={"adult"},
    ),
}

TRAITS = ["careful", "sensible", "thoughtful", "bold", "hasty", "curious"]
GIRL_NAMES: list[str] = []
BOY_NAMES: list[str] = []


def alternative_supports(cargo: Cargo, alternative: Alternative) -> bool:
    return bool(cargo.tags & alternative.compatible_tags)


def bridge_danger(cargo: Cargo, wind: Wind) -> int:
    return cargo.windage + wind.force


def risky_bridge(cargo: Cargo, wind: Wind) -> bool:
    return bridge_danger(cargo, wind) >= 4


def initial_caution(trait: str) -> float:
    return 4.0 if trait in CAUTIOUS_TRAITS else 2.0


def would_listen(helper: HelperCfg, trait: str) -> bool:
    return helper.authority + initial_caution(trait) > PRIDE_INIT


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for cargo_id, cargo in CARGOES.items():
            for alt_id in sorted(setting.affords):
                alt = ALTERNATIVES[alt_id]
                if risky_bridge(cargo, WINDS["gusty"]) and alternative_supports(cargo, alt):
                    combos.append((setting_id, cargo_id, alt_id))
    return combos


def explain_rejection(setting: Setting, cargo: Cargo, alternative: Alternative) -> str:
    if alternative.id not in setting.affords:
        return (
            f"(No story: {alternative.phrase} does not belong to {setting.place}. "
            f"Pick an alternative route that exists in that setting.)"
        )
    if not alternative_supports(cargo, alternative):
        return (
            f"(No story: {alternative.phrase} is not a sensible way to move the "
            f"{cargo.label}. This world only accepts alternatives that actually "
            f"fit the cargo and the wind problem.)"
        )
    return "(No story: this combination does not produce a sensible windy-bridge tale.)"


def predict_bridge(world: World) -> dict:
    sim = world.copy()
    cargo = sim.get("cargo")
    wind = sim.facts["wind_cfg"]
    bridge = sim.get("bridge")
    bridge.meters["sway"] = float(max(0, bridge_danger(sim.facts["cargo_cfg"], wind) - sim.facts["cargo_cfg"].sturdy))
    propagate(sim, narrate=False)
    return {
        "risky": cargo.meters["risk"] >= THRESHOLD,
        "sway": bridge.meters["sway"],
    }


def introduce(world: World, setting: Setting, pepe: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    pepe.memes["joy"] += 1
    pepe.memes["pride"] = PRIDE_INIT
    world.say(setting.opening)
    world.say(
        f"That was the very morning Pepe set out for {setting.festival}, and he was grinning like a boy who expected the day to fit in his pocket."
    )
    world.say(helper_cfg.intro)
    world.say(f"{helper.label} walked beside him, keeping one eye on the sky and one on Pepe's plans.")


def mission(world: World, setting: Setting, pepe: Entity, cargo_ent: Entity, cargo_cfg: Cargo) -> None:
    world.say(
        f"Pepe {cargo_cfg.carry_verb}. He was taking {cargo_ent.phrase} to {setting.hill} to {cargo_cfg.goal}."
    )


def foreshadow(world: World, setting: Setting, wind: Wind) -> None:
    bridge = setting.bridge_name
    world.say(wind.omen)
    world.say(
        f"Along the creek, {wind.sign}, and {bridge} kept muttering over the water. {wind.bridge_text}"
    )


def warning(world: World, pepe: Entity, helper: Entity, cargo_cfg: Cargo, alternative: Alternative, setting: Setting) -> None:
    pred = predict_bridge(world)
    helper.memes["care"] += 1
    world.facts["predicted_risky"] = pred["risky"]
    world.say(
        f'"Pepe," said {helper.label}, "that bridge is talking too much for my liking. We have an alternative: {alternative.path_text}."'
    )
    if pred["risky"]:
        world.say(
            f'"If the wind gets one good tug at that {cargo_cfg.label}, it may dance right out of your hands."'
        )
    else:
        world.say(
            f'"The bridge may hold, but there is no prize for hurrying into foolishness."'
        )


def choose_alternative(world: World, helper: Entity, alternative: Alternative) -> None:
    pepe = world.get("Pepe")
    pepe.memes["relief"] += 1
    pepe.memes["wisdom"] += 1
    world.say(
        f"Pepe looked at the bridge, then at {helper.label}, and for once he let the wiser voice win."
    )
    world.say(
        f"Instead of the shortcut, he chose the alternative: {alternative.path_text}."
    )
    world.say(alternative.ride_text)


def step_onto_bridge(world: World, setting: Setting, cargo_cfg: Cargo) -> None:
    bridge = world.get("bridge")
    sway = max(0, bridge_danger(cargo_cfg, world.facts["wind_cfg"]) - cargo_cfg.sturdy)
    bridge.meters["sway"] = float(sway)
    propagate(world, narrate=False)
    world.say(
        f"But Pepe was feeling taller than a flagpole and twice as sure. He stepped onto {setting.bridge_name} anyway."
    )
    if cargo_cfg.label == "pie":
        world.say(
            "At once the pie tilted, and the berry filling made one shiny, dangerous slide toward the crust."
        )
    elif cargo_cfg.plural:
        world.say(
            "At once the pinwheels spun so wildly they tried to become a flock and fly away."
        )
    else:
        world.say(
            "At once the banner swelled full of wind and pulled sideways like a mule that had suddenly remembered an appointment."
        )


def rescue_to_alternative(world: World, helper: Entity, alternative: Alternative) -> None:
    pepe = world.get("Pepe")
    cargo = world.get("cargo")
    pepe.memes["fear"] += 1
    helper.memes["urgency"] += 1
    cargo.meters["saved"] += 1
    world.say(
        f"{helper.label} caught Pepe by the elbow, {alternative.rescue_text}, and steadied the {cargo.label} before it could tumble into the creek."
    )
    world.say(
        f'"There now," said {helper.pronoun("subject")}. "A long road is better than a short mistake."'
    )
    world.say(alternative.ride_text)
    pepe.memes["relief"] += 1
    pepe.memes["wisdom"] += 1


def arrival(world: World, setting: Setting, pepe: Entity, cargo_cfg: Cargo) -> None:
    pepe.memes["joy"] += 1
    world.say(
        f"By the time they reached {setting.hill}, the fiddles were already sawing and the kettles were already steaming."
    )
    if cargo_cfg.label == "pie":
        world.say(
            "Pepe set the pie down so neatly that not one blackberry dared escape."
        )
    elif cargo_cfg.plural:
        world.say(
            "Pepe planted the pinwheels by the bandstand, and they spun with such happy color that even the grumpiest boots began to tap."
        )
    else:
        world.say(
            "Pepe raised the banner on the hilltop pole, and it opened over the crowd like a bright second sunrise."
        )


def ending(world: World, setting: Setting, helper: Entity, cargo_cfg: Cargo, alternative: Alternative, listened: bool) -> None:
    pepe = world.get("Pepe")
    helper.memes["love"] += 1
    pepe.memes["love"] += 1
    if listened:
        world.say(
            f'Pepe tipped his head toward {helper.label}. "Good thing we took the alternative," he said, and he meant it.'
        )
    else:
        world.say(
            f'Pepe gave {helper.label} a sheepish smile. "Next time," he said, "I will listen before the bridge sings its whole song."'
        )
    world.say(
        f"Then they stood together above the town while the wind went fussing somewhere else, and {setting.ending_image}"
    )
    world.facts["lesson_text"] = (
        f"Pepe learned that a safer alternative can carry a big day to a happy ending. "
        f"He finished the errand because he stopped treating the warning like a joke."
    )
    world.facts["arrival_text"] = alternative.qa_text


def tell(
    setting: Setting,
    cargo_cfg: Cargo,
    alternative: Alternative,
    wind: Wind,
    helper_cfg: HelperCfg,
    trait: str,
) -> World:
    world = World()
    pepe = world.add(
        Entity(
            id="Pepe",
            kind="character",
            type="boy",
            label="Pepe",
            phrase="Pepe",
            role="hero",
            traits=[trait],
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.helper_type,
            label=helper_cfg.label,
            phrase=helper_cfg.label,
            role="helper",
            traits=["steady"],
            tags=set(helper_cfg.tags),
        )
    )
    cargo_ent = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo_cfg.label,
            phrase=cargo_cfg.phrase,
            plural=cargo_cfg.plural,
            tags=set(cargo_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="bridge",
            type="bridge",
            label=setting.bridge_name,
            phrase=setting.bridge_name,
            tags={"bridge"},
        )
    )

    world.facts.update(
        setting=setting,
        cargo_cfg=cargo_cfg,
        alternative=alternative,
        wind_cfg=wind,
        helper_cfg=helper_cfg,
        trait=trait,
    )

    introduce(world, setting, pepe, helper, helper_cfg)
    mission(world, setting, pepe, cargo_ent, cargo_cfg)
    world.para()
    foreshadow(world, setting, wind)
    warning(world, pepe, helper, cargo_cfg, alternative, setting)
    world.para()

    listened = would_listen(helper_cfg, trait)
    if listened:
        choose_alternative(world, helper, alternative)
        outcome = "listened"
    else:
        step_onto_bridge(world, setting, cargo_cfg)
        rescue_to_alternative(world, helper, alternative)
        outcome = "rescued"

    world.para()
    arrival(world, setting, pepe, cargo_cfg)
    ending(world, setting, helper, cargo_cfg, alternative, listened)

    world.facts.update(
        pepe=pepe,
        helper=helper,
        cargo=cargo_ent,
        outcome=outcome,
        listened=listened,
        rescued=(outcome == "rescued"),
        risky=risky_bridge(cargo_cfg, wind),
    )
    return world


KNOWLEDGE = {
    "wind": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows a clue early on about what may happen later. A groaning bridge or wild wind can warn readers before the trouble starts."
        ),
        (
            "Why can strong wind make carrying things hard?",
            "Strong wind pushes and tugs on whatever you are carrying. Light or wide things can twist in your hands and become hard to control."
        ),
    ],
    "bridge": [
        (
            "Why can a wobbly bridge be dangerous?",
            "A wobbly bridge can shift under your feet and make you lose your balance. If you are carrying something, that extra motion can make a fall or spill more likely."
        ),
    ],
    "alternative": [
        (
            "What is an alternative?",
            "An alternative is another choice you can use instead of your first idea. Sometimes the alternative is slower, but it is also safer or smarter."
        ),
    ],
    "boat": [
        (
            "What does a ferry do?",
            "A ferry is a boat that carries people and things across water. It can be a safer way to cross when a bridge is crowded or windy."
        ),
    ],
    "path": [
        (
            "Why is a sheltered path calmer in the wind?",
            "Rocks, trees, or hills can block part of the wind. That makes the air on a sheltered path push less hard."
        ),
    ],
    "road": [
        (
            "Why is a long road sometimes better than a shortcut?",
            "A long road can be wiser when it is smooth and steady. Getting there safely matters more than hurrying."
        ),
    ],
    "food": [
        (
            "Why can a pie tip when someone hurries with it?",
            "A pie can tip if the person carrying it sways or jolts. Soft filling moves, and that movement can make the pie slide or spill."
        ),
    ],
    "cloth": [
        (
            "Why does cloth pull in the wind?",
            "Cloth catches moving air like a sail. The wider it is, the more the wind can tug on it."
        ),
    ],
    "light": [
        (
            "Why do pinwheels spin?",
            "Pinwheels spin because moving air pushes their blades. A strong gust can make them turn very fast."
        ),
    ],
}
KNOWLEDGE_ORDER = ["wind", "bridge", "alternative", "boat", "path", "road", "food", "cloth", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    cargo = f["cargo_cfg"]
    alternative = f["alternative"]
    return [
        'Write a tall tale for a 3-to-5-year-old that includes the words "Pepe" and "alternative" and uses clear foreshadowing before a happy ending.',
        f"Tell a windy tall tale where Pepe must carry a {cargo.label} to {setting.hill}, notices big warning signs, and reaches the festival by choosing {alternative.phrase}.",
        f"Write a child-facing story in which a grown-up offers an alternative to a risky shortcut, and the ending image proves the day turned out well.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pepe = f["pepe"]
    helper = f["helper"]
    setting = f["setting"]
    cargo = f["cargo_cfg"]
    alternative = f["alternative"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Pepe, who was carrying a {cargo.label} to {setting.hill}, and {helper.label}, who watched out for him."
        ),
        (
            "What clues warned that trouble was coming?",
            f"The wind was already acting wild, and {setting.bridge_name} was groaning over the creek. Those signs foreshadowed that the shortcut bridge was not safe."
        ),
        (
            f"Why did {helper.label} suggest an alternative?",
            f"{helper.label} could tell the bridge and wind together might knock the {cargo.label} out of Pepe's hands. The alternative route was safer because it avoided the worst swaying and gusting."
        ),
    ]
    if outcome == "listened":
        qa.append(
            (
                "Did Pepe listen right away?",
                f"Yes. Pepe looked at the windy bridge and chose the alternative before anything went wrong. That choice turned the warning into a happy ending instead of a disaster."
            )
        )
    else:
        qa.append(
            (
                "What happened when Pepe tried the bridge?",
                f"The bridge wobbled and the {cargo.label} almost got away from him. Then {helper.label} steadied Pepe and led him to the alternative route, so the scare became a lesson instead of a loss."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"Pepe reached {setting.hill} in time and finished his festival errand. {f['lesson_text']}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"wind", "bridge", "alternative"}
    tags |= set(f["alternative"].tags)
    tags |= set(f["cargo_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="fairground",
        cargo="banner",
        alternative="orchard_road",
        wind="blustery",
        helper="grandpa",
        trait="careful",
    ),
    StoryParams(
        setting="river",
        cargo="pie",
        alternative="ferry",
        wind="gusty",
        helper="aunt",
        trait="bold",
    ),
    StoryParams(
        setting="mesa",
        cargo="pie",
        alternative="mule_path",
        wind="blustery",
        helper="baker",
        trait="hasty",
    ),
    StoryParams(
        setting="mesa",
        cargo="pinwheels",
        alternative="wagon_road",
        wind="gusty",
        helper="grandpa",
        trait="thoughtful",
    ),
]


ASP_RULES = r"""
% Compatible-route gate.
valid(S, C, A) :- setting(S), cargo(C), alternative(A), afforded(S, A), cargo_tag(C, T), alt_ok(A, T), risky(C, gusty).

% Outcome model.
careful_trait(T) :- trait(T), cautious(T).
init_caution(4) :- trait(T), careful_trait(T).
init_caution(2) :- trait(T), not careful_trait(T).
listens :- helper_authority(H), init_caution(C), pride_init(P), H + C > P.
outcome(listened) :- listens.
outcome(rescued) :- not listens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for alt_id in sorted(setting.affords):
            lines.append(asp.fact("afforded", setting_id, alt_id))
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        for tag in sorted(cargo.tags):
            lines.append(asp.fact("cargo_tag", cargo_id, tag))
        for wind_id, wind in WINDS.items():
            if risky_bridge(cargo, wind):
                lines.append(asp.fact("risky", cargo_id, wind_id))
    for alt_id, alt in ALTERNATIVES.items():
        lines.append(asp.fact("alternative", alt_id))
        for tag in sorted(alt.compatible_tags):
            lines.append(asp.fact("alt_ok", alt_id, tag))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    helper_cfg = HELPERS[params.helper]
    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("helper_authority", helper_cfg.authority),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "listened" if would_listen(HELPERS[params.helper], params.trait) else "rescued"


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

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
        sample = generate(CURATED[0])
        if not sample.story or "Pepe" not in sample.story:
            raise StoryError("Smoke test story was empty or missing Pepe.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation ran.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: Pepe, a windy bridge, and a wiser alternative."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.alternative:
        setting = SETTINGS[args.setting]
        if args.alternative not in setting.affords:
            alt = ALTERNATIVES[args.alternative]
            cargo = CARGOES[args.cargo] if args.cargo else next(iter(CARGOES.values()))
            raise StoryError(explain_rejection(setting, cargo, alt))

    if args.cargo and args.alternative:
        cargo = CARGOES[args.cargo]
        alt = ALTERNATIVES[args.alternative]
        setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        if not alternative_supports(cargo, alt):
            raise StoryError(explain_rejection(setting, cargo, alt))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.alternative is None or combo[2] == args.alternative)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cargo_id, alt_id = rng.choice(sorted(combos))
    wind_id = args.wind or rng.choice(sorted(WINDS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        alternative=alt_id,
        wind=wind_id,
        helper=helper_id,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cargo = CARGOES[params.cargo]
        alternative = ALTERNATIVES[params.alternative]
        wind = WINDS[params.wind]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if params.alternative not in setting.affords or not alternative_supports(cargo, alternative):
        raise StoryError(explain_rejection(setting, cargo, alternative))

    world = tell(
        setting=setting,
        cargo_cfg=cargo,
        alternative=alternative,
        wind=wind,
        helper_cfg=helper,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cargo, alternative) combos:\n")
        for setting, cargo, alt in combos:
            print(f"  {setting:10} {cargo:10} {alt}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Pepe: {p.cargo} at {p.setting} via {p.alternative} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
