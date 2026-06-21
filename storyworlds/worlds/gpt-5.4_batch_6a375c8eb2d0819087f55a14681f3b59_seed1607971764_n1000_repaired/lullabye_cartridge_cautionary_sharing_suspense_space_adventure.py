#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py
================================================================================================

A standalone story world for a small Space Adventure domain with caution, sharing,
and suspense. Two children on a pretend overnight mission discover that one
glow cartridge is more useful in a shared guide lamp than clipped into one
person's flashy badge. In the darker branches, the story turns suspenseful
until the cartridge is shared and a calm comfort method -- often a soft
lullabye -- helps the frightened partner feel brave again.

Run it
------
    python storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py
    python storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py --zone crater_tunnel
    python storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py --cartridge sticker_cartridge
    python storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lullabye_cartridge_cautionary_sharing_suspense_space_adventure.py --verify
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Setting:
    id: str
    place: str
    scene: str
    launch: str
    ending: str
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
class Cartridge:
    id: str
    label: str
    phrase: str
    glow: str
    powers_light: bool
    has_song: bool = False
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
class Zone:
    id: str
    label: str
    description: str
    hazard_line: str
    ending_image: str
    dark: bool
    risk: int
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
class Comfort:
    id: str
    sense: int
    power: int
    action: str
    calming: str
    qa_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.flags: dict[str, bool] = {
            "entered_zone": False,
            "comfort_used": False,
        }
        self.facts: dict = {
            "predicted_dark": False,
            "predicted_risk": 0,
        }

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
        clone.flags = dict(self.flags)
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


def _r_lamp_bright(world: World) -> list[str]:
    lamp = world.get("lamp")
    if lamp.meters["cartridge"] < THRESHOLD:
        return []
    sig = ("lamp_bright",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lamp.meters["light"] += 1
    return []


def _r_dark_fear(world: World) -> list[str]:
    if not world.flags["entered_zone"]:
        return []
    lamp = world.get("lamp")
    zone = world.get("zone")
    partner = world.get("partner")
    if lamp.meters["light"] >= THRESHOLD:
        return []
    sig = ("dark_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    zone.meters["danger"] += 1
    partner.memes["fear"] += 1
    partner.memes["stuck"] += 1
    return ["__dark__"]


def _r_comfort(world: World) -> list[str]:
    if not world.flags["comfort_used"]:
        return []
    partner = world.get("partner")
    if partner.memes["fear"] < THRESHOLD:
        return []
    sig = ("comfort",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    partner.memes["fear"] = 0.0
    partner.memes["calm"] += 1
    partner.memes["trust"] += 1
    world.get("instigator").memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="lamp_bright", tag="physical", apply=_r_lamp_bright),
    Rule(name="dark_fear", tag="emotional", apply=_r_dark_fear),
    Rule(name="comfort", tag="emotional", apply=_r_comfort),
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


def hazard_at_risk(cartridge: Cartridge, zone: Zone) -> bool:
    return cartridge.powers_light and zone.dark


def sensible_comforts() -> list[Comfort]:
    return [c for c in COMFORTS.values() if c.sense >= SENSE_MIN]


def mission_risk(zone: Zone, delay: int) -> int:
    return zone.risk + delay


def can_continue(comfort: Comfort, zone: Zone, delay: int) -> bool:
    return comfort.power >= mission_risk(zone, delay)


def predict_dark(world: World) -> dict:
    sim = world.copy()
    sim.flags["entered_zone"] = True
    propagate(sim, narrate=False)
    partner = sim.get("partner")
    return {
        "dark": partner.memes["fear"] >= THRESHOLD,
        "risk": int(sim.get("zone").meters["danger"] + partner.memes["fear"]),
    }


def play_setup(world: World, setting: Setting, a: Entity, b: Entity, guide: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At {setting.place}, {a.id} and {b.id} stepped into {setting.scene}. "
        f"{setting.launch}"
    )
    world.say(
        f'"Captain {a.id} and Navigator {b.id}!" {guide.label_word.capitalize()} '
        f"whispered. \"Mission control is listening.\""
    )


def need_light(world: World, zone: Zone, b: Entity) -> None:
    world.say(
        f"Ahead of them waited {zone.description}. Even the silver stars painted on the walls "
        f"looked swallowed by the dark."
    )
    world.say(f'"That place is dark enough to lose a boot in," {b.id} said. "We need the guide lamp."')


def tempt(world: World, a: Entity, cartridge: Cartridge) -> None:
    a.memes["greed"] += 1
    world.say(
        f"But there was only one fresh cartridge, {cartridge.phrase}. "
        f"{a.id} slid it into the shiny badge on {a.pronoun('possessive')} chest just to watch it "
        f"{cartridge.glow}."
    )
    world.say(f"For one proud moment, {a.id} liked being the brightest explorer in the room.")


def warn(world: World, a: Entity, b: Entity, guide: Entity, zone: Zone) -> None:
    pred = predict_dark(world)
    world.facts["predicted_dark"] = pred["dark"]
    world.facts["predicted_risk"] = pred["risk"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} looked from the dark passage to {a.id}\'s glowing badge. '
        f'"If the cartridge stays with you, the lamp stays dim," {b.pronoun()} said. '
        f'"Then {zone.hazard_line}"'
    )
    world.say(
        f'{guide.label_word.capitalize()} nodded. "Space teams share the light," '
        f'{guide.pronoun()} said.'
    )


def share_before(world: World, a: Entity, b: Entity, lamp: Entity, cartridge: Cartridge, zone: Zone) -> None:
    a.memes["greed"] = 0.0
    a.memes["care"] += 1
    b.memes["trust"] += 1
    lamp.meters["cartridge"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} looked down at the bright badge, then unclipped the cartridge. "
        f"\"The lamp needs it more than I do,\" {a.pronoun()} said."
    )
    world.say(
        f"When the cartridge clicked into the guide lamp, it {cartridge.glow}, and "
        f"{zone.label} stopped looking like a hungry mouth."
    )


def enter_zone(world: World, a: Entity, b: Entity, zone: Zone) -> None:
    world.flags["entered_zone"] = True
    propagate(world, narrate=False)
    world.say(
        f"Together they stepped into {zone.label}. Their boots made tiny thup-thup sounds, "
        f"and for a breath everything felt very far from home."
    )


def fright(world: World, b: Entity, zone: Zone) -> None:
    world.say(
        f"Then the dark pressed close. {b.id} heard the echo of {b.pronoun('possessive')} own breath "
        f"and froze beside the wall."
    )
    world.say(f'"{zone.hazard_line}" {b.id} whispered this time, and {b.pronoun()} did not sound brave at all.')


def share_after(world: World, a: Entity, lamp: Entity, cartridge: Cartridge) -> None:
    a.memes["greed"] = 0.0
    a.memes["care"] += 1
    lamp.meters["cartridge"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Right away, {a.id} understood. {a.pronoun().capitalize()} pulled the cartridge from the badge "
        f"with shaky fingers and snapped it into the lamp."
    )
    world.say(
        f"The beam opened like a small silver road, and the worst of the dark slid backward."
    )


def soothe(world: World, a: Entity, b: Entity, comfort: Comfort, cartridge: Cartridge) -> None:
    world.flags["comfort_used"] = True
    propagate(world, narrate=False)
    extra = ""
    if comfort.id == "helmet_lullabye" and cartridge.has_song:
        extra = " The cartridge even held a tiny lullabye tune, and the helmets played it softly between the stars."
    world.say(
        f"{a.id} stayed beside {b.id} and {comfort.action}. {comfort.calming}.{extra}"
    )


def mission_success(world: World, setting: Setting, a: Entity, b: Entity, zone: Zone) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    b.memes["stuck"] = 0.0
    world.say(
        f"Soon they reached the end of {zone.label}, where a tin meteor flag waited on a crate. "
        f"{b.id} took one side, {a.id} took the other, and they carried it together."
    )
    world.say(
        f"On the walk back, they passed the lamp from hand to hand. {setting.ending} {zone.ending_image}"
    )


def turn_back(world: World, guide: Entity, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["sad"] += 1
    b.memes["relief"] += 1
    b.memes["stuck"] = 0.0
    world.say(
        f'{guide.label_word.capitalize()} touched their shoulders and led them back to the bright hatch. '
        f'"A mission can wait," {guide.pronoun()} said. "Friends come first."'
    )
    world.say(
        f"Back in the warm part of the station, {a.id} handed the lamp to {b.id} without being asked. "
        f"{setting.ending}"
    )


def lesson(world: World, guide: Entity, a: Entity, b: Entity) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'{guide.label_word.capitalize()} smiled at them both. "A space team shares tools before the dark gets a say," '
        f'{guide.pronoun()} said.'
    )
    world.say(
        f"{a.id} nodded. {b.id} nodded too, and after that the lamp never belonged to only one pair of hands."
    )


def bedtime_note(world: World, b: Entity, comfort: Comfort, cartridge: Cartridge) -> None:
    if comfort.id != "helmet_lullabye" and not cartridge.has_song:
        world.say(
            f"Much later, when the stars outside the window dimmed, {b.id} still remembered the soft lullabye "
            f"that had made the tunnel feel smaller."
        )


def tell(
    setting: Setting,
    cartridge: Cartridge,
    zone: Zone,
    comfort: Comfort,
    choice: str = "hide_first",
    delay: int = 0,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    partner: str = "Milo",
    partner_gender: str = "boy",
    guide_type: str = "mother",
    robot_name: str = "Pip",
) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator"))
    b = world.add(Entity(id=partner, kind="character", type=partner_gender, role="partner"))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, role="guide", label="the guide"))
    robot = world.add(Entity(id=robot_name, kind="thing", type="robot", role="helper", label=robot_name))
    lamp = world.add(Entity(id="lamp", kind="thing", type="lamp", label="guide lamp"))
    zone_ent = world.add(Entity(id="zone", kind="thing", type="zone", label=zone.label))
    lamp.meters["cartridge"] = 0.0
    lamp.meters["light"] = 0.0
    zone_ent.meters["danger"] = 0.0
    a.memes["greed"] = 0.0
    a.memes["care"] = 0.0
    b.memes["fear"] = 0.0
    b.memes["trust"] = 1.0
    b.memes["stuck"] = 0.0

    play_setup(world, setting, a, b, guide)
    need_light(world, zone, b)

    world.para()
    tempt(world, a, cartridge)
    warn(world, a, b, guide, zone)

    if choice == "share_first":
        world.para()
        share_before(world, a, b, lamp, cartridge, zone)
        enter_zone(world, a, b, zone)
        soothe(world, a, b, comfort, cartridge)
        mission_success(world, setting, a, b, zone)
        outcome = "averted"
    else:
        world.para()
        world.say(
            f'"Just for a minute," {a.id} said, still wearing the glowing badge. '
            f'Even {robot.id} gave a worried little beep.'
        )
        enter_zone(world, a, b, zone)
        fright(world, b, zone)
        severity = mission_risk(zone, delay)
        share_after(world, a, lamp, cartridge)
        soothe(world, a, b, comfort, cartridge)
        if can_continue(comfort, zone, delay):
            mission_success(world, setting, a, b, zone)
            outcome = "shared_soon"
        else:
            turn_back(world, guide, a, b, setting)
            outcome = "turned_back"

    world.para()
    lesson(world, guide, a, b)
    bedtime_note(world, b, comfort, cartridge)

    world.facts.update(
        setting=setting,
        cartridge=cartridge,
        zone_cfg=zone,
        comfort=comfort,
        instigator=a,
        partner=b,
        guide=guide,
        robot=robot,
        lamp=lamp,
        choice=choice,
        delay=delay,
        outcome=outcome,
        continued=outcome in {"averted", "shared_soon"},
        scared=world.get("partner").memes["calm"] >= THRESHOLD or outcome == "turned_back",
    )
    return world


SETTINGS = {
    "moon_base": Setting(
        id="moon_base",
        place="the museum's moon-base hall",
        scene="a silver training station with portholes, blinking maps, and foam meteors",
        launch="A cardboard rover waited by the airlock, and every button seemed ready for adventure.",
        ending="By then the whole hall felt less like a contest and more like a crew.",
        tags={"museum", "space"},
    ),
    "ring_station": Setting(
        id="ring_station",
        place="their living-room ring station",
        scene="a blanket spaceship circling the sofa planet",
        launch="Blue fairy lights blinked like distant stars around the couch.",
        ending="The blanket walls no longer felt tiny once they were laughing together inside them.",
        tags={"home", "space"},
    ),
    "comet_ship": Setting(
        id="comet_ship",
        place="the library's comet ship exhibit",
        scene="a narrow starship with paper planets hanging above the hatch",
        launch="The mission book said a comet flag was hidden somewhere ahead.",
        ending="The quiet library ship seemed to hum kindly around them.",
        tags={"library", "space"},
    ),
}

CARTRIDGES = {
    "glow_cartridge": Cartridge(
        id="glow_cartridge",
        label="glow cartridge",
        phrase="a bright glow cartridge",
        glow="shone lemon-yellow",
        powers_light=True,
        has_song=False,
        tags={"cartridge", "light"},
    ),
    "star_cartridge": Cartridge(
        id="star_cartridge",
        label="star cartridge",
        phrase="a blue star cartridge",
        glow="glowed icy blue",
        powers_light=True,
        has_song=False,
        tags={"cartridge", "light"},
    ),
    "lullabye_cartridge": Cartridge(
        id="lullabye_cartridge",
        label="lullabye cartridge",
        phrase="a silver lullabye cartridge",
        glow="glowed soft as moonmilk",
        powers_light=True,
        has_song=True,
        tags={"cartridge", "light", "lullabye"},
    ),
    "sticker_cartridge": Cartridge(
        id="sticker_cartridge",
        label="sticker cartridge",
        phrase="a sticker cartridge full of shiny decals",
        glow="sparkled with stars but made no light at all",
        powers_light=False,
        has_song=False,
        tags={"cartridge"},
    ),
}

ZONES = {
    "crater_tunnel": Zone(
        id="crater_tunnel",
        label="the crater tunnel",
        description="the crater tunnel, a curving hallway painted black and blue",
        hazard_line="I can't see the floor anymore",
        ending_image="At the hatch, the stars on the wall seemed friendly again.",
        dark=True,
        risk=2,
        tags={"dark", "tunnel"},
    ),
    "shadow_airlock": Zone(
        id="shadow_airlock",
        label="the shadow airlock",
        description="the shadow airlock, where two round doors made the dark feel deeper",
        hazard_line="The dark is squeezing my chest",
        ending_image="Even the heavy airlock doors looked playful once the lamp was shared.",
        dark=True,
        risk=3,
        tags={"dark", "airlock"},
    ),
    "meteor_bay": Zone(
        id="meteor_bay",
        label="the meteor bay",
        description="the meteor bay, a room of hanging rocks and sleepy red lights",
        hazard_line="Everything sounds bigger in here",
        ending_image="The red lights blinked like sleepy planets instead of warnings.",
        dark=True,
        risk=1,
        tags={"dark", "bay"},
    ),
    "sun_window": Zone(
        id="sun_window",
        label="the sun window",
        description="the sun window, a bright room washed with gold paper sunlight",
        hazard_line="I can see just fine",
        ending_image="Nothing there had ever been scary in the first place.",
        dark=False,
        risk=0,
        tags={"bright"},
    ),
}

COMFORTS = {
    "helmet_lullabye": Comfort(
        id="helmet_lullabye",
        sense=3,
        power=3,
        action="began to sing a small helmet-radio lullabye",
        calming="The tune gave the air something gentle to hold onto",
        qa_text="sang a soft lullabye over the helmet radio",
        tags={"lullabye", "calm"},
    ),
    "robot_hum": Comfort(
        id="robot_hum",
        sense=3,
        power=2,
        action="asked the little robot to hum and held the lamp low beside their boots",
        calming="The steady humming made the tunnel feel measured instead of endless",
        qa_text="used the robot's steady humming to calm the fear",
        tags={"robot", "calm"},
    ),
    "countdown_game": Comfort(
        id="countdown_game",
        sense=2,
        power=1,
        action="started a slow ten-to-one countdown and breathed with the numbers",
        calming="Counting gave both children something steady to do",
        qa_text="used a slow countdown to make the moment calmer",
        tags={"calm", "counting"},
    ),
    "boast_louder": Comfort(
        id="boast_louder",
        sense=1,
        power=0,
        action="talked louder and tried to pretend nothing was wrong",
        calming="It did not help much at all",
        qa_text="just talked louder instead of truly helping",
        tags={"bad_idea"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_comforts():
        return combos
    for setting_id in SETTINGS:
        for cartridge_id, cartridge in CARTRIDGES.items():
            for zone_id, zone in ZONES.items():
                if hazard_at_risk(cartridge, zone):
                    combos.append((setting_id, cartridge_id, zone_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    cartridge: str
    zone: str
    comfort: str
    choice: str
    delay: int
    instigator: str
    instigator_gender: str
    partner: str
    partner_gender: str
    guide: str
    robot_name: str
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
    "cartridge": [
        (
            "What is a cartridge?",
            "A cartridge is a little piece that fits into a machine and helps it do a job. In this world, the cartridge gives power to the lamp.",
        )
    ],
    "lullabye": [
        (
            "What is a lullabye?",
            "A lullabye is a soft, gentle song people use to help someone feel calm or sleepy. Quiet songs can make a scary moment feel smaller.",
        )
    ],
    "dark": [
        (
            "Why can the dark feel scary?",
            "The dark hides what is around you, so your brain has less information and can start to worry. A steady light and a calm voice help because they make the place feel known again.",
        )
    ],
    "sharing": [
        (
            "Why is sharing important on a team?",
            "Sharing lets everyone use the tool that helps most at the right time. On a team, keeping everything to yourself can make the job harder and can leave a friend without what they need.",
        )
    ],
    "robot": [
        (
            "Why can a steady sound be calming?",
            "A steady hum or beat gives your body something regular to follow. That can slow your breathing and help you feel safer.",
        )
    ],
    "counting": [
        (
            "Why does counting sometimes help when you are scared?",
            "Counting gives your mind one simple thing to do. It can slow a panicky feeling and help you notice your breathing again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cartridge", "lullabye", "dark", "sharing", "robot", "counting"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    setting = f["setting"]
    cartridge = f["cartridge"]
    zone = f["zone_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short Space Adventure story for a 3-to-5-year-old that includes the words '
        f'"lullabye" and "{cartridge.label}".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a space-station sharing story where {a.id} wants the {cartridge.label} on a badge, "
            f"but gives it to the guide lamp before entering {zone.label}.",
            f"Write a gentle cautionary story set in {setting.place} where two children learn that the team light matters more than looking brightest.",
        ]
    if outcome == "turned_back":
        return [
            base,
            f"Tell a suspenseful space adventure where {a.id} keeps the {cartridge.label} too long, "
            f"{b.id} gets frightened in {zone.label}, and the mission must turn back.",
            f"Write a cautionary sharing story where the children are safe in the end but learn to share tools before the dark becomes a problem.",
        ]
    return [
        base,
        f"Tell a suspenseful but comforting space story where {a.id} keeps the {cartridge.label} for a minute, "
        f"then shares it in time to help {b.id} feel brave again.",
        f"Write a cautionary sharing story with a dark tunnel, a soft lullabye, and an ending that proves the children learned to work as a crew.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    guide = f["guide"]
    setting = f["setting"]
    cartridge = f["cartridge"]
    zone = f["zone_cfg"]
    comfort = f["comfort"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children on a pretend space mission, and their {guide.label_word} guiding the adventure. The story follows what happens when one tool matters to both children at once.",
        ),
        (
            "What did the children need before they could explore the dark place?",
            f"They needed the guide lamp to have the cartridge, because {zone.label} was too dark to cross safely without good light. That need is what made sharing important.",
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} could tell the lamp would stay dim if {a.id} kept the cartridge on the badge. {b.pronoun().capitalize()} was worried the dark would feel bigger and scarier once they stepped into {zone.label}.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed when {a.id} shared the cartridge before entering?",
                f"When {a.id} gave the cartridge to the lamp, the path became bright before the scary part could begin. Sharing early kept the mission calm and let both children explore together.",
            )
        )
    elif outcome == "shared_soon":
        qa.append(
            (
                f"What happened when {a.id} kept the cartridge too long?",
                f"The dark pressed in and {b.id} froze, because the lamp was still dim when they entered {zone.label}. Then {a.id} shared the cartridge and {comfort.qa_text}, which helped the fear settle down.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the mission continuing and the children carrying the meteor flag together. The final image shows they had stopped treating the light like one person's prize and started using it like a team's tool.",
            )
        )
    else:
        qa.append(
            (
                "Why did they turn back instead of finishing the mission?",
                f"They turned back because the dark scare had already grown too big for that moment. Even after the cartridge was shared, the safest choice was to leave the tunnel and try again another time.",
            )
        )
        qa.append(
            (
                f"What lesson did {a.id} learn?",
                f"{a.id} learned that looking brightest is not the same as helping most. The story warns that waiting too long to share can spoil the adventure for everyone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cartridge", "dark", "sharing"}
    tags |= set(f["cartridge"].tags)
    tags |= set(f["comfort"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flags: {world.flags}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_base",
        cartridge="lullabye_cartridge",
        zone="crater_tunnel",
        comfort="helmet_lullabye",
        choice="share_first",
        delay=0,
        instigator="Nova",
        instigator_gender="girl",
        partner="Milo",
        partner_gender="boy",
        guide="mother",
        robot_name="Pip",
    ),
    StoryParams(
        setting="comet_ship",
        cartridge="glow_cartridge",
        zone="meteor_bay",
        comfort="robot_hum",
        choice="hide_first",
        delay=0,
        instigator="Leo",
        instigator_gender="boy",
        partner="Zia",
        partner_gender="girl",
        guide="father",
        robot_name="Tink",
    ),
    StoryParams(
        setting="ring_station",
        cartridge="star_cartridge",
        zone="shadow_airlock",
        comfort="countdown_game",
        choice="hide_first",
        delay=2,
        instigator="Ava",
        instigator_gender="girl",
        partner="Finn",
        partner_gender="boy",
        guide="mother",
        robot_name="Dot",
    ),
    StoryParams(
        setting="moon_base",
        cartridge="lullabye_cartridge",
        zone="shadow_airlock",
        comfort="helmet_lullabye",
        choice="hide_first",
        delay=0,
        instigator="Theo",
        instigator_gender="boy",
        partner="Nora",
        partner_gender="girl",
        guide="father",
        robot_name="Pip",
    ),
]


def explain_rejection(cartridge: Cartridge, zone: Zone) -> str:
    if not cartridge.powers_light:
        return (
            f"(No story: {cartridge.label} does not power the guide lamp, so it cannot honestly cause or solve the dark-place problem. "
            f"Pick a real light cartridge.)"
        )
    if not zone.dark:
        return (
            f"(No story: {zone.label} is not truly dark, so the children do not need to share the lamp there. "
            f"Pick a darker zone like crater_tunnel or shadow_airlock.)"
        )
    return "(No story: this combination has no believable light-sharing hazard.)"


def explain_comfort(cid: str) -> str:
    comfort = COMFORTS[cid]
    better = ", ".join(sorted(c.id for c in sensible_comforts()))
    return (
        f"(Refusing comfort '{cid}': it scores too low on common sense "
        f"(sense={comfort.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.choice == "share_first":
        return "averted"
    comfort = COMFORTS[params.comfort]
    zone = ZONES[params.zone]
    return "shared_soon" if can_continue(comfort, zone, params.delay) else "turned_back"


ASP_RULES = r"""
hazard(C, Z) :- powers_light(C), dark_zone(Z).
valid(S, C, Z) :- setting(S), cartridge(C), zone(Z), hazard(C, Z).

sensible(K) :- comfort(K), sense(K, S), sense_min(M), S >= M.

risk(R + D) :- chosen_zone(Z), zone_risk(Z, R), delay(D).
power(P) :- chosen_comfort(K), comfort_power(K, P).

outcome(averted) :- choice(share_first).
outcome(shared_soon) :- choice(hide_first), power(P), risk(R), P >= R.
outcome(turned_back) :- choice(hide_first), power(P), risk(R), P < R.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for cartridge_id, cartridge in CARTRIDGES.items():
        lines.append(asp.fact("cartridge", cartridge_id))
        if cartridge.powers_light:
            lines.append(asp.fact("powers_light", cartridge_id))
    for zone_id, zone in ZONES.items():
        lines.append(asp.fact("zone", zone_id))
        lines.append(asp.fact("zone_risk", zone_id, zone.risk))
        if zone.dark:
            lines.append(asp.fact("dark_zone", zone_id))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("sense", comfort_id, comfort.sense))
        lines.append(asp.fact("comfort_power", comfort_id, comfort.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(k for (k,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_zone", params.zone),
            asp.fact("chosen_comfort", params.comfort),
            asp.fact("delay", params.delay),
            asp.fact("choice", params.choice),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_gate = set(valid_combos())
    clingo_gate = set(asp_valid_combos())
    if python_gate == clingo_gate:
        print(f"OK: gate matches valid_combos() ({len(python_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_gate - python_gate:
            print("  only in clingo:", sorted(clingo_gate - python_gate))
        if python_gate - clingo_gate:
            print("  only in python:", sorted(python_gate - clingo_gate))

    python_sensible = {c.id for c in sensible_comforts()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible comforts match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible comforts: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space adventure about sharing the lamp before the dark gets bigger."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cartridge", choices=CARTRIDGES)
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--choice", choices=["share_first", "hide_first"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the instigator hesitates before sharing")
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nova", "Luna", "Ava", "Mira", "Nora", "Zia", "Ivy", "Skye"]
BOY_NAMES = ["Milo", "Leo", "Finn", "Theo", "Max", "Eli", "Owen", "Kai"]
ROBOTS = ["Pip", "Dot", "Tink", "Pebble"]


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.zone and args.cartridge:
        zone = ZONES[args.zone]
        cartridge = CARTRIDGES[args.cartridge]
        if not hazard_at_risk(cartridge, zone):
            raise StoryError(explain_rejection(cartridge, zone))
    if args.zone and not ZONES[args.zone].dark:
        cartridge = CARTRIDGES[args.cartridge] if args.cartridge else next(iter(CARTRIDGES.values()))
        raise StoryError(explain_rejection(cartridge, ZONES[args.zone]))
    if args.cartridge and not CARTRIDGES[args.cartridge].powers_light:
        zone = ZONES[args.zone] if args.zone else next(iter(ZONES.values()))
        raise StoryError(explain_rejection(CARTRIDGES[args.cartridge], zone))
    if args.comfort and COMFORTS[args.comfort].sense < SENSE_MIN:
        raise StoryError(explain_comfort(args.comfort))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cartridge is None or combo[1] == args.cartridge)
        and (args.zone is None or combo[2] == args.zone)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cartridge_id, zone_id = rng.choice(sorted(combos))
    comfort_id = args.comfort or rng.choice(sorted(c.id for c in sensible_comforts()))
    choice = args.choice or rng.choice(["share_first", "hide_first", "hide_first"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    instigator, ig = _pick_kid(rng)
    partner, pg = _pick_kid(rng, avoid=instigator)
    guide = args.guide or rng.choice(["mother", "father"])
    robot_name = rng.choice(ROBOTS)
    return StoryParams(
        setting=setting_id,
        cartridge=cartridge_id,
        zone=zone_id,
        comfort=comfort_id,
        choice=choice,
        delay=delay,
        instigator=instigator,
        instigator_gender=ig,
        partner=partner,
        partner_gender=pg,
        guide=guide,
        robot_name=robot_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cartridge = CARTRIDGES[params.cartridge]
        zone = ZONES[params.zone]
        comfort = COMFORTS[params.comfort]
    except KeyError as exc:
        raise StoryError(f"(Unknown story parameter: {exc})") from exc

    if not hazard_at_risk(cartridge, zone):
        raise StoryError(explain_rejection(cartridge, zone))
    if comfort.sense < SENSE_MIN:
        raise StoryError(explain_comfort(params.comfort))
    if params.choice not in {"share_first", "hide_first"}:
        raise StoryError("(Choice must be 'share_first' or 'hide_first'.)")
    if params.delay not in {0, 1, 2}:
        raise StoryError("(Delay must be 0, 1, or 2.)")

    world = tell(
        setting=setting,
        cartridge=cartridge,
        zone=zone,
        comfort=comfort,
        choice=params.choice,
        delay=params.delay,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        guide_type=params.guide,
        robot_name=params.robot_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible comforts: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cartridge, zone) combos:\n")
        for setting_id, cartridge_id, zone_id in combos:
            print(f"  {setting_id:12} {cartridge_id:18} {zone_id}")
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
                f"### {p.instigator} & {p.partner}: {p.cartridge} in {p.zone} "
                f"({p.setting}, {p.choice}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
