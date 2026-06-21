#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py
=============================================================

A standalone storyworld about pirate pretend-play on a farmyard: one child
boasts about bravery, takes or nearly takes a foolish shortcut near manure, and
learns that real bravery means telling the truth and choosing the safe way.

Run it
------
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --crossing plank --response rinse
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --crossing stone_path
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --response laugh
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/manure_liar_bravery_pirate_tale.py --verify
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
BRAVERY_INIT = 6.0
STEADY_TRAITS = {"careful", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    slippery: bool = False
    filthy: bool = False
    helpful: bool = False
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
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    hideout: str
    role_solo: str
    role_plural: str
    ending: str
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


@dataclass
class Crossing:
    id: str
    label: str
    phrase: str
    step_text: str
    manure_near: str
    risky: bool
    slip: int
    filthy: bool = True
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
class SafeWay:
    id: str
    label: str
    phrase: str
    help_text: str
    ending_text: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"boaster", "mate"}]

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
    child = world.get("boaster")
    crossing = world.get("crossing")
    if child.meters["on_crossing"] < THRESHOLD:
        return out
    if not crossing.slippery:
        return out
    if child.memes["bravery"] > child.memes["balance"]:
        sig = ("slip", child.id, crossing.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["slipped"] += 1
            child.meters["messy"] += 1
            child.memes["fear"] += 1
            if crossing.filthy:
                child.meters["manure"] += 1
            out.append("__slip__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("boaster")
    if child.meters["slipped"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("yard").meters["danger"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="worry", tag="emotional", apply=_r_worry),
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
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(crossing: Crossing) -> bool:
    return crossing.risky and crossing.filthy


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def mess_severity(crossing: Crossing, delay: int) -> int:
    return crossing.slip + delay


def is_contained(response: Response, crossing: Crossing, delay: int) -> bool:
    return response.power >= mess_severity(crossing, delay)


def initial_steadiness(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_avert(relation: str, boaster_age: int, mate_age: int, trait: str) -> bool:
    mate_older = relation == "siblings" and mate_age > boaster_age
    authority = initial_steadiness(trait) + 1.0 + (4.0 if mate_older else 0.0)
    return mate_older and authority > BRAVERY_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("boaster")
    child.meters["on_crossing"] += 1
    propagate(sim, narrate=False)
    return {
        "slips": child.meters["slipped"] >= THRESHOLD,
        "manure": child.meters["manure"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright farm afternoon, {a.id} and {b.id} turned the barnyard into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} shouted. '
        f'"Let\'s find {theme.goal} in {theme.hideout}!"'
    )


def need_crossing(world: World, b: Entity, crossing: Crossing) -> None:
    world.say(
        f"But between them and the hideout lay {crossing.phrase}, with a sour smell "
        f"of manure curling up beside it."
    )
    world.say(
        f'{b.id} leaned forward and squinted. "That way looks tricky," '
        f'{b.pronoun()} said.'
    )


def boast(world: World, a: Entity, crossing: Crossing) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} puffed up with pirate bravery. "A real pirate would use '
        f'{crossing.label}," {a.pronoun()} said. "Watch me."'
    )
    world.say("For one proud moment, sounding fearless felt more important than thinking.")


def warn(world: World, b: Entity, a: Entity, crossing: Crossing, helper: Entity) -> None:
    pred = predict_trouble(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["manure"]:
        extra = " If you slip there, you will land right by the manure."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "Do not call me a liar just because I say '
        f'it is unsafe," {b.pronoun()} said. "{crossing.step_text}{extra} '
        f'Let\'s ask {helper.label_word} for the safe way."'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I am not scared, and you are not the captain," {a.id} said. '
        f'"You are calling me foolish, but I am brave." Then {a.id} marched ahead anyway.'
    )


def back_down(world: World, a: Entity, b: Entity, helper: Entity, safe_way: SafeWay, theme: Theme) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} took one more look at the slick boards and the dark manure below them. '
        f'"Maybe brave does not mean barging ahead," {a.pronoun()} murmured.'
    )
    world.say(
        f'{b.id} squeezed {a.pronoun("possessive")} hand, and together they went to '
        f'{helper.label_word} for help instead of pretending harder.'
    )
    world.para()
    world.say(
        f'{helper.label_word.capitalize()} smiled and showed them {safe_way.phrase}. '
        f'{safe_way.help_text}'
    )
    world.say(
        f'Soon the {theme.role_plural} crossed safely and {theme.ending}.'
    )


def attempt(world: World, a: Entity, crossing: Crossing) -> None:
    a.meters["on_crossing"] += 1
    propagate(world, narrate=False)
    if a.meters["slipped"] >= THRESHOLD:
        world.say(
            f'{a.id} stepped onto {crossing.label}. {crossing.step_text} '
            f'At once {a.pronoun()} slipped, windmilled both arms, and landed with one boot in the manure.'
        )
    else:
        world.say(
            f'{a.id} stepped onto {crossing.label}. {crossing.step_text} '
            f'{a.pronoun().capitalize()} teetered, but did not fall.'
        )


def alarm(world: World, b: Entity, a: Entity, helper: Entity) -> None:
    if a.meters["slipped"] >= THRESHOLD:
        world.say(f'"{a.id}!" {b.id} cried. "Stop moving!"')
    else:
        world.say(f'"{a.id}, come back!" {b.id} cried.')
    world.say(f'"{helper.label_word.upper()}!"')


def rescue(world: World, helper: Entity, response: Response, a: Entity, safe_way: SafeWay, theme: Theme) -> None:
    a.meters["manure"] = 0.0
    a.meters["messy"] = 0.0
    a.meters["on_crossing"] = 0.0
    a.meters["slipped"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} came quickly and {response.text}."
    )
    world.say(
        f'The sour smell faded, the fright settled, and the game stopped feeling like a test of pride.'
    )
    world.say(
        f'Then {helper.pronoun()} pointed to {safe_way.phrase}. {safe_way.help_text}'
    )
    world.say(
        f'After that, the {theme.role_plural} crossed the safe way and {theme.ending}.'
    )


def rescue_fail(world: World, helper: Entity, response: Response, a: Entity) -> None:
    world.get("yard").meters["danger"] += 1
    a.meters["manure"] += 1
    a.memes["shame"] += 1
    world.say(f"{helper.label_word.capitalize()} hurried over and {response.fail}.")
    world.say(
        f"But the mess spread from boot to sock to trousers, and the whole game came to a stop."
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f'Then {helper.label_word.capitalize()} knelt beside them. '
        f'"Bravery is not showing off," {helper.pronoun()} said softly. '
        f'"Bravery is telling the truth, listening when something is dangerous, and asking for help before the mess grows."'
    )
    world.say(
        f'{a.id} looked down. "I should not have called anyone a liar," {a.pronoun()} whispered.'
    )
    world.say(f'"And I should have listened," {a.pronoun()} added.')


def wash_and_end(world: World, helper: Entity, a: Entity, b: Entity, safe_way: SafeWay, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f'After clean water, dry socks, and one deep breath, {helper.label_word} brought them back to {safe_way.phrase}.'
    )
    world.say(
        f'{b.id} went first this time, and {a.id} followed carefully, one honest step after another.'
    )
    world.say(
        f'Together the {theme.role_plural} {theme.ending} -- not louder, but wiser and truly brave.'
    )


def sad_end(world: World, helper: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{helper.label_word.capitalize()} led them inside for washing, and the pirate game was over for the day.'
    )
    world.say(
        f'{a.id} sat very still while the manure was scrubbed away. {a.pronoun().capitalize()} felt more small than bold.'
    )
    world.say(
        f'Neither child forgot the lesson: calling someone a liar does not make a risky thing safe, and pretend bravery can turn into a real mess very fast.'
    )


def tell(
    theme: Theme,
    crossing: Crossing,
    safe_way: SafeWay,
    response: Response,
    *,
    boaster_name: str = "Tom",
    boaster_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "steady",
    delay: int = 0,
    boaster_age: int = 6,
    mate_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="boaster",
        kind="character",
        type=boaster_gender,
        label=boaster_name,
        role="boaster",
        age=boaster_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id="mate",
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        age=mate_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the grown-up",
        role="helper",
        helpful=True,
    ))
    yard = world.add(Entity(id="yard", type="yard", label="the yard"))
    route = world.add(Entity(
        id="crossing",
        type="crossing",
        label=crossing.label,
        slippery=crossing.risky,
        filthy=crossing.filthy,
    ))
    bridge = world.add(Entity(
        id="safe_way",
        type="safe_way",
        label=safe_way.label,
        helpful=True,
    ))

    a.memes["bravery"] = BRAVERY_INIT
    a.memes["balance"] = float(max(1, 7 - crossing.slip - delay))
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_steadiness(trait)
    world.facts["predicted_danger"] = 0.0
    world.facts["theme"] = theme
    world.facts["crossing_cfg"] = crossing
    world.facts["safe_way_cfg"] = safe_way
    world.facts["response"] = response
    world.facts["relation"] = relation

    play_setup(world, a, b, theme)
    need_crossing(world, b, crossing)

    world.para()
    boast(world, a, crossing)
    warn(world, b, a, crossing, helper)

    averted = would_avert(relation, boaster_age, mate_age, trait)

    if averted:
        back_down(world, a, b, helper, safe_way, theme)
        severity, contained = 0, True
    else:
        defy(world, a, b)
        world.para()
        attempt(world, a, crossing)
        alarm(world, b, a, helper)

        severity = mess_severity(crossing, delay)
        contained = is_contained(response, crossing, delay)

        world.para()
        if contained:
            rescue(world, helper, response, a, safe_way, theme)
            lesson(world, helper, a, b)
            world.para()
            wash_and_end(world, helper, a, b, safe_way, theme)
        else:
            rescue_fail(world, helper, response, a)
            lesson(world, helper, a, b)
            sad_end(world, helper, a, b)

    outcome = "averted" if averted else ("contained" if contained else "spoiled")
    world.facts.update(
        boaster=a,
        mate=b,
        helper=helper,
        crossing=route,
        safe_way=bridge,
        outcome=outcome,
        slipped=a.meters["slipped"] >= THRESHOLD,
        manure=a.meters["manure"] >= THRESHOLD,
        severity=severity,
        delay=delay,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a muddy island kingdom behind the barn",
        rig="The wheelbarrow was their pirate ship, a hay rake became a mast, a feed bucket held their treasure, and a chalk map pointed toward the hidden cove behind the chicken coop.",
        title_a="Captain",
        title_b="Scout",
        goal="the hidden chest",
        hideout="the old shed",
        role_solo="a pirate",
        role_plural="pirates",
        ending="hurried off to claim the hidden chest",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a windy sea fort beside the fields",
        rig="An upturned crate was their deck, a broom was their flagpole, a rope ring was their anchor, and a torn paper map marked the secret fort by the shed.",
        title_a="Captain",
        title_b="Lookout",
        goal="the secret fort",
        hideout="the tin-roof shed",
        role_solo="a corsair",
        role_plural="corsairs",
        ending="raced off to the secret fort",
    ),
}

CROSSINGS = {
    "plank": Crossing(
        id="plank",
        label="the wobbly plank",
        phrase="a wobbly plank laid over the muck",
        step_text="The board was wet and bowed in the middle.",
        manure_near="under the plank",
        risky=True,
        slip=2,
        filthy=True,
        tags={"plank", "manure", "danger"},
    ),
    "barrel": Crossing(
        id="barrel",
        label="the rolling barrel",
        phrase="an old barrel tipped beside the manure cart",
        step_text="The barrel shifted as soon as a foot touched it.",
        manure_near="by the manure cart",
        risky=True,
        slip=3,
        filthy=True,
        tags={"barrel", "manure", "danger"},
    ),
    "stone_path": Crossing(
        id="stone_path",
        label="the stone path",
        phrase="a neat stone path with a clean edge",
        step_text="The stones were flat and dry.",
        manure_near="far from the path",
        risky=False,
        slip=0,
        filthy=False,
        tags={"stones"},
    ),
}

SAFE_WAYS = {
    "bridge": SafeWay(
        id="bridge",
        label="the little footbridge",
        phrase="the little footbridge by the fence",
        help_text="It was sturdy, dry, and far from the manure pile.",
        ending_text="They crossed on the bridge.",
        tags={"bridge", "safe_way"},
    ),
    "gate": SafeWay(
        id="gate",
        label="the side gate",
        phrase="the side gate and the clean lane beyond it",
        help_text="The long way took a few extra steps, but every board was steady and clean.",
        ending_text="They went through the gate.",
        tags={"gate", "safe_way"},
    ),
}

RESPONSES = {
    "rinse": Response(
        id="rinse",
        sense=3,
        power=4,
        text="lifted the child out, set both boots on the grass, and rinsed away the manure with the hose before anyone else stepped in it",
        fail="tried to rinse the mess with one small watering can, but there was too much muck and too much wobbling to fix quickly",
        qa_text="lifted the child out and rinsed away the manure with the hose",
        tags={"hose", "washing", "help"},
    ),
    "pull_back": Response(
        id="pull_back",
        sense=3,
        power=3,
        text="caught the child under the arms and pulled the little pirate straight back onto the clean grass",
        fail="grabbed for the child, but the rolling footing and sticky muck made the whole rescue slow and clumsy",
        qa_text="pulled the child back onto the clean grass",
        tags={"help", "pull"},
    ),
    "laugh": Response(
        id="laugh",
        sense=1,
        power=0,
        text="laughed and told everyone to shake it off",
        fail="laughed first instead of helping, so the mess only spread",
        qa_text="laughed instead of helping",
        tags={"bad_help"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "steady", "sensible", "thoughtful", "kind", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for crossing_id, crossing in CROSSINGS.items():
            if not hazard_at_risk(crossing):
                continue
            for safe_id in SAFE_WAYS:
                combos.append((theme, crossing_id, safe_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    crossing: str
    safe_way: str
    response: str
    boaster_name: str
    boaster_gender: str
    mate_name: str
    mate_gender: str
    helper: str
    trait: str
    delay: int = 0
    boaster_age: int = 6
    mate_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "manure": [
        (
            "What is manure?",
            "Manure is animal waste that farmers sometimes use to help plants grow. It is dirty and smelly, so children should not step in it or play near it.",
        )
    ],
    "danger": [
        (
            "Why can a wobbly board be dangerous?",
            "A wobbly board can tip or slide when you step on it. That can make you fall before you are ready.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge safer than a slippery shortcut?",
            "A good bridge gives your feet a steady place to go. A safe path matters more than showing off.",
        )
    ],
    "help": [
        (
            "What should you do if a friend slips into a messy or dangerous place?",
            "Call a grown-up right away and stay where you are. Quick help is safer than jumping in after them.",
        )
    ],
    "washing": [
        (
            "Why should manure be washed off quickly?",
            "Manure is dirty and can carry germs. Washing it off quickly helps keep skin and clothes cleaner.",
        )
    ],
    "honesty": [
        (
            "What does it mean to be honest?",
            "Being honest means telling what is true, even when it is hard. Honest words help people make safe choices.",
        )
    ],
    "bravery": [
        (
            "What is real bravery?",
            "Real bravery is doing the right thing when you feel pressure to show off. Sometimes the brave choice is to slow down, tell the truth, and ask for help.",
        )
    ],
}


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["boaster"]
    b = f["mate"]
    crossing = f["crossing_cfg"]
    theme = f["theme"]
    safe = f["safe_way_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the words "manure" and "liar", where one child boasts about bravery but listens in time and chooses {safe.label} instead of {crossing.label}.',
            f"Tell a gentle farmyard pirate tale where {a.label} almost takes a foolish shortcut near manure, but {b.label} helps {a.pronoun('object')} understand that real bravery is honest and careful.",
            f'Write a story where a child says "liar" in the middle of an argument, then learns that brave children ask for the safe way instead of showing off.',
        ]
    if outcome == "spoiled":
        return [
            f'Write a pirate-style cautionary story for a 3-to-5-year-old that includes the words "manure" and "liar", where a boastful child takes {crossing.label}, gets into a messy problem, and learns a lesson about real bravery.',
            f"Tell a farm pirate tale where {a.label} ignores {b.label}'s warning near manure, and the game ends sadly after a grown-up has to clean up the mess.",
            f'Write a story where calling someone a liar does not make danger disappear, and the ending shows that pretend bravery can ruin the day.',
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "manure" and "liar", where one child boasts about bravery, slips near manure, and a grown-up helps them recover and choose {safe.label}.',
        f"Tell a farmyard pirate tale where {a.label} ignores {b.label}'s warning, but the ending is gentle and teaches that brave children tell the truth and ask for help.",
        f'Write a simple story with pirates, a risky shortcut, the word "liar", and an ending where the children keep playing in a safer way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["boaster"]
    b = f["mate"]
    helper = f["helper"]
    crossing = f["crossing_cfg"]
    safe = f["safe_way_cfg"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    pw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, who were pretending to be pirates near the barn. It is also about their {pw}, who helped when the game turned risky.",
        ),
        (
            "What problem stood between the children and the hideout?",
            f"They wanted to reach the hideout, but {crossing.phrase} stood in the way with manure close by. That made the shortcut feel daring, but also dirty and unsafe.",
        ),
        (
            f"Why did {b.label} warn {a.label}?",
            f"{b.label} could see that {crossing.label} was not steady and that a slip would end near the manure. {b.pronoun().capitalize()} warned {a.pronoun('object')} because the danger was real, not because {b.pronoun()} wanted to spoil the game.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.label} learn before anyone got hurt?",
                f"{a.label} learned that real bravery was not barging ahead just to win an argument. {a.pronoun().capitalize()} stopped, asked for help, and chose the safe way instead.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children crossing by {safe.label} and going on with their pirate game. The ending shows that the adventure stayed fun because they chose honesty and safety together.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.label} tried the shortcut?",
                f"{a.label} slipped and got manure on one boot, which scared both children. The proud moment turned into a rescue because the risky shortcut could not hold steady.",
            )
        )
        qa.append(
            (
                f"How did their {pw} help?",
                f"Their {pw} {response.qa_text}. After that, the grown-up showed them {safe.phrase} so the game could continue in a safer way.",
            )
        )
        qa.append(
            (
                f"What was the lesson about bravery?",
                f"The lesson was that bravery is not showing off or calling someone a liar when they warn you. Brave children tell the truth, listen to danger, and ask for help before the mess gets bigger.",
            )
        )
    else:
        qa.append(
            (
                f"Did the grown-up fix the problem quickly?",
                f"No. Their {pw} tried to help, but the mess spread and the pirate game had to end for the day. The slow cleanup showed that one foolish choice can spoil something happy.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with washing, quiet feelings, and no more pirate game that afternoon. The ending proves that pretend bravery and hurtful words can turn play into a sad mess.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"manure", "honesty", "bravery", "help"}
    crossing_cfg = world.facts["crossing_cfg"]
    safe_way_cfg = world.facts["safe_way_cfg"]
    response = world.facts["response"]
    if "danger" in crossing_cfg.tags:
        tags.add("danger")
    if "bridge" in safe_way_cfg.tags or "gate" in safe_way_cfg.tags:
        tags.add("bridge")
    if "washing" in response.tags:
        tags.add("washing")
    ordered = ["manure", "danger", "bridge", "help", "washing", "honesty", "bravery"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
        flags = [n for n, on in (("slippery", e.slippery), ("filthy", e.filthy), ("helpful", e.helpful)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({e.type:8}) {label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        crossing="plank",
        safe_way="bridge",
        response="rinse",
        boaster_name="Tom",
        boaster_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        helper="mother",
        trait="steady",
        delay=0,
        boaster_age=6,
        mate_age=4,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        theme="corsairs",
        crossing="barrel",
        safe_way="gate",
        response="pull_back",
        boaster_name="Max",
        boaster_gender="boy",
        mate_name="Mia",
        mate_gender="girl",
        helper="father",
        trait="careful",
        delay=0,
        boaster_age=5,
        mate_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        theme="pirates",
        crossing="barrel",
        safe_way="bridge",
        response="pull_back",
        boaster_name="Sam",
        boaster_gender="boy",
        mate_name="Zoe",
        mate_gender="girl",
        helper="mother",
        trait="clever",
        delay=1,
        boaster_age=6,
        mate_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        theme="corsairs",
        crossing="barrel",
        safe_way="gate",
        response="pull_back",
        boaster_name="Eli",
        boaster_gender="boy",
        mate_name="Nora",
        mate_gender="girl",
        helper="father",
        trait="kind",
        delay=2,
        boaster_age=7,
        mate_age=5,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(crossing: Crossing) -> str:
    if not crossing.risky:
        return (
            f"(No story: {crossing.label} is not actually risky, so there is no honest danger near the manure and no real turn in the tale. Pick a risky crossing like plank or barrel.)"
        )
    if not crossing.filthy:
        return (
            f"(No story: {crossing.label} is not near manure, so this world's central dirty danger is missing.)"
        )
    return "(No story: this crossing does not create a plausible farmyard hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.boaster_age, params.mate_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], CROSSINGS[params.crossing], params.delay)
    return "contained" if contained else "spoiled"


ASP_RULES = r"""
hazard(C) :- crossing(C), risky(C), filthy(C).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,C,SW) :- theme(T), hazard(C), safe_way(SW).

steady_now(T) :- trait(T), is_steady(T).
init_steadiness(5) :- trait(T), steady_now(T).
init_steadiness(3) :- trait(T), not steady_now(T).
mate_older :- relation(siblings), boaster_age(BA), mate_age(MA), MA > BA.
bonus(4) :- mate_older.
bonus(0) :- not mate_older.
authority(C + 1 + B) :- init_steadiness(C), bonus(B).
averted :- mate_older, authority(A), bravery_init(BR), A > BR.

severity(S + D) :- chosen_crossing(C), slip(C,S), delay(D).
resp_power(P) :- chosen_response(R), power(R,P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spoiled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid, crossing in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        if crossing.risky:
            lines.append(asp.fact("risky", cid))
        if crossing.filthy:
            lines.append(asp.fact("filthy", cid))
        lines.append(asp.fact("slip", cid, crossing.slip))
    for sid in SAFE_WAYS:
        lines.append(asp.fact("safe_way", sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_crossing", params.crossing),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("boaster_age", params.boaster_age),
            asp.fact("mate_age", params.mate_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play, bragging, manure, and real bravery. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--safe-way", dest="safe_way", choices=SAFE_WAYS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the mess grows before help fully takes hold")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crossing:
        crossing = CROSSINGS[args.crossing]
        if not hazard_at_risk(crossing):
            raise StoryError(explain_rejection(crossing))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.crossing is None or c[1] == args.crossing)
        and (args.safe_way is None or c[2] == args.safe_way)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, crossing, safe_way = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    boaster_name, boaster_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=boaster_name)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    boaster_age, mate_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme,
        crossing=crossing,
        safe_way=safe_way,
        response=response,
        boaster_name=boaster_name,
        boaster_gender=boaster_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        helper=helper,
        trait=trait,
        delay=delay,
        boaster_age=boaster_age,
        mate_age=mate_age,
        relation=relation,
        trust=trust,
    )


def _require(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(Invalid {field_name}: {key})")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    theme = _require(THEMES, params.theme, "theme")
    crossing = _require(CROSSINGS, params.crossing, "crossing")
    safe_way = _require(SAFE_WAYS, params.safe_way, "safe_way")
    response = _require(RESPONSES, params.response, "response")
    if not hazard_at_risk(crossing):
        raise StoryError(explain_rejection(crossing))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        theme=theme,
        crossing=crossing,
        safe_way=safe_way,
        response=response,
        boaster_name=params.boaster_name,
        boaster_gender=params.boaster_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
        boaster_age=params.boaster_age,
        mate_age=params.mate_age,
        relation=params.relation,
        trust=params.trust,
    )
    boaster = world.facts["boaster"]
    mate = world.facts["mate"]
    helper = world.facts["helper"]
    world.story_names = {"boaster": boaster.label, "mate": mate.label, "helper": helper.label_word}
    story_text = (
        world.render()
        .replace("boaster", boaster.label)
        .replace("mate", mate.label)
        .replace("helper", helper.label_word)
    )
    return StorySample(
        params=params,
        story=story_text,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, crossing, safe_way) combos:\n")
        for theme, crossing, safe_way in combos:
            print(f"  {theme:9} {crossing:10} {safe_way}")
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
            header = f"### {p.boaster_name} & {p.mate_name}: {p.crossing} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
