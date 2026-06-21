#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/poop_pl_spire_conflict_misunderstanding_bad_ending.py
================================================================================

A standalone story world in a small mythic domain: two young beacon-keepers must
light the fire atop a spire before bad weather closes in, but a misunderstanding
over a strange fuel called "poop-pl" turns into conflict. The quarrel damages
their chance to help, and the story ends badly.

This world favors a narrow, plausible shape over broad coverage:

- A beacon on a spire matters because travelers below truly need it.
- The fuel must actually be suitable for the weather, or the story is refused.
- The misunderstanding must fit the fuel's appearance or role.
- The conflict changes world state: trust drops, anger rises, oil spills,
  the beacon stays dark or comes too late, and real loss follows.

Run it
------
    python storyworlds/worlds/gpt-5.4/poop_pl_spire_conflict_misunderstanding_bad_ending.py
    python storyworlds/worlds/gpt-5.4/poop_pl_spire_conflict_misunderstanding_bad_ending.py --fuel poop_pl --weather fog
    python storyworlds/worlds/gpt-5.4/poop_pl_spire_conflict_misunderstanding_bad_ending.py --fuel driftwood
    python storyworlds/worlds/gpt-5.4/poop_pl_spire_conflict_misunderstanding_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/poop_pl_spire_conflict_misunderstanding_bad_ending.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "daughter"}
        male = {"boy", "man", "priest", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    spire_name: str
    below: str
    travelers: str
    loss: str
    closing_image: str
    weather_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky: str
    rise: str
    need: int
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fuel:
    id: str
    label: str
    phrase: str
    carry: str
    signal: str
    power: int
    looks_dirty: bool = False
    sacred: bool = False
    suspicious_reasons: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Misread:
    id: str
    claim: str
    shout: str
    fit_tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    weather: str
    fuel: str
    misread: str
    keeper_one: str
    keeper_one_gender: str
    keeper_two: str
    keeper_two_gender: str
    elder_title: str
    spark: bool
    trait_one: str
    trait_two: str
    delay: int = 1
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


def _r_quarrel(world: World) -> list[str]:
    a = world.get("keeper_one")
    b = world.get("keeper_two")
    if a.memes["accused"] < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    a.memes["trust"] -= 2
    b.memes["trust"] -= 2
    return ["__quarrel__"]


def _r_spill(world: World) -> list[str]:
    if world.get("keeper_one").memes["anger"] < THRESHOLD:
        return []
    jar = world.get("oil")
    if jar.meters["spilled"] >= THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jar.meters["spilled"] += 1
    world.get("beacon").meters["ready"] = 0.0
    return ["__spill__"]


def _r_dark_danger(world: World) -> list[str]:
    beacon = world.get("beacon")
    if beacon.meters["lit"] >= THRESHOLD:
        return []
    sig = ("dark_danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("below").meters["danger"] += 1
    return []


RULES = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="dark_danger", tag="physical", apply=_r_dark_danger),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(s for s in produced if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the cliff harbor of Namar",
        spire_name="the Shell Spire",
        below="the black water below the cliffs",
        travelers="fishing boats",
        loss="one boat struck the teeth of the rocks, and the others drifted all night in fear",
        closing_image="At dawn the spire still smoked weakly, and splintered oars washed against the harbor steps.",
        weather_ids={"fog", "storm"},
        tags={"harbor", "spire"},
    ),
    "valley": Setting(
        id="valley",
        place="the frost valley of Ilen",
        spire_name="the Pine Spire",
        below="the white road curling through the valley",
        travelers="pack mules and traders",
        loss="two mule carts slid from the road, and the traders spent the night crying for one another in the snow",
        closing_image="At dawn the spire stood pale above the valley, and dropped bundles lay half-buried beside the road.",
        weather_ids={"snow", "fog"},
        tags={"valley", "spire"},
    ),
    "delta": Setting(
        id="delta",
        place="the reed delta of Sur",
        spire_name="the Crane Spire",
        below="the twisting water-roads among the reeds",
        travelers="river boats",
        loss="three river boats missed the safe channel and grounded in the mud till morning",
        closing_image="At dawn the spire looked over the silent reeds, and stuck boats leaned like tired animals in the gray mud.",
        tags={"delta", "spire"},
        weather_ids={"fog", "storm"},
    ),
}

WEATHERS = {
    "fog": Weather(
        id="fog",
        sky="A gray fog was already lifting from the low places.",
        rise="By dusk the fog would climb high enough to swallow the paths below.",
        need=2,
        danger="Without a strong beacon, the world below would lose its edges.",
        tags={"fog"},
    ),
    "storm": Weather(
        id="storm",
        sky="The sea-wind had begun to beat like a drum against the stone.",
        rise="By dusk the storm would turn the world below into rain, noise, and blind spray.",
        need=3,
        danger="Without a fierce beacon, even the brave would not know where home was.",
        tags={"storm"},
    ),
    "snow": Weather(
        id="snow",
        sky="Fine snow was falling in slow white threads.",
        rise="By dusk the snow would hide the road and fill every footprint.",
        need=2,
        danger="Without a clear beacon, the road below would seem to vanish.",
        tags={"snow"},
    ),
}

FUELS = {
    "poop_pl": Fuel(
        id="poop_pl",
        label="poop-pl",
        phrase="a pouch of poop-pl pellets",
        carry="small brown pellets that the temple dried from bitter marsh sap",
        signal="They burned with a dark blue heart and sent up a thick guiding smoke.",
        power=3,
        looks_dirty=True,
        sacred=True,
        suspicious_reasons={"filth", "curse"},
        tags={"poop-pl", "smoke", "beacon"},
    ),
    "cedar_pitch": Fuel(
        id="cedar_pitch",
        label="cedar pitch",
        phrase="a crock of cedar pitch",
        carry="sticky black pitch wrapped in cedar bark",
        signal="It made a steady orange fire that could be seen far away.",
        power=2,
        looks_dirty=True,
        suspicious_reasons={"curse"},
        tags={"pitch", "beacon"},
    ),
    "sun_oil": Fuel(
        id="sun_oil",
        label="sun-oil",
        phrase="a brass flask of sun-oil",
        carry="clear oil that smelled of herbs and warm stone",
        signal="It burned bright but did not hold long against the wildest weather.",
        power=2,
        looks_dirty=False,
        sacred=False,
        suspicious_reasons={"theft"},
        tags={"oil", "beacon"},
    ),
    "driftwood": Fuel(
        id="driftwood",
        label="driftwood",
        phrase="an armful of driftwood",
        carry="salt-stiff wood gathered from the shore",
        signal="It flared fast and fell fast.",
        power=1,
        looks_dirty=False,
        sacred=False,
        suspicious_reasons=set(),
        tags={"wood"},
    ),
}

MISREADS = {
    "filth": Misread(
        id="filth",
        claim="thought the dark pellets were dirt that would shame the holy fire",
        shout='"You brought filth to the beacon!"',
        fit_tag="filth",
        tags={"misunderstanding"},
    ),
    "curse": Misread(
        id="curse",
        claim="thought the fuel was a curse-bundle meant to darken the flame",
        shout='"You mean to curse the spire!"',
        fit_tag="curse",
        tags={"misunderstanding", "curse"},
    ),
    "theft": Misread(
        id="theft",
        claim="thought the flask had been stolen from the shrine stores",
        shout='"That belongs below. You stole it!"',
        fit_tag="theft",
        tags={"misunderstanding", "theft"},
    ),
}

GIRL_NAMES = ["Asha", "Mira", "Nila", "Tara", "Suri", "Luma", "Iri", "Vesa"]
BOY_NAMES = ["Kian", "Daren", "Ivo", "Soren", "Pavel", "Niko", "Rian", "Tomas"]
TRAITS = ["proud", "quick", "dutiful", "restless", "solemn", "eager"]


def valid_combo(setting_id: str, weather_id: str, fuel_id: str, misread_id: str) -> bool:
    setting = SETTINGS[setting_id]
    weather = WEATHERS[weather_id]
    fuel = FUELS[fuel_id]
    misread = MISREADS[misread_id]
    if weather_id not in setting.weather_ids:
        return False
    if fuel.power < weather.need:
        return False
    if misread.fit_tag not in fuel.suspicious_reasons:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for wid in WEATHERS:
            for fid in FUELS:
                for mid in MISREADS:
                    if valid_combo(sid, wid, fid, mid):
                        combos.append((sid, wid, fid, mid))
    return combos


def explain_rejection(setting_id: str, weather_id: str, fuel_id: str, misread_id: str) -> str:
    setting = SETTINGS[setting_id]
    weather = WEATHERS[weather_id]
    fuel = FUELS[fuel_id]
    misread = MISREADS[misread_id]
    if weather_id not in setting.weather_ids:
        return (
            f"(No story: {weather.id} does not fit {setting.place}. "
            f"This mythic beacon belongs to a different kind of danger.)"
        )
    if fuel.power < weather.need:
        return (
            f"(No story: {fuel.label} is too weak for {weather.id}. "
            f"If the fuel cannot honestly guide the {setting.travelers}, the beacon conflict has no good shape.)"
        )
    if misread.fit_tag not in fuel.suspicious_reasons:
        return (
            f"(No story: the misunderstanding '{misread.id}' does not fit {fuel.label}. "
            f"The accusation must arise from what the fuel looks like or where it belongs.)"
        )
    return "(No story: this combination does not form a reasonable mythic conflict.)"


def outcome_of(params: StoryParams) -> str:
    if params.spark and params.delay <= 1:
        return "late"
    return "dark"


def predict_beacon(world: World, fuel: Fuel, weather: Weather, spark: bool, delay: int) -> dict:
    sim = world.copy()
    sim.get("keeper_one").memes["accused"] += 1
    propagate(sim, narrate=False)
    lit = spark and delay <= 1 and fuel.power >= weather.need
    if lit:
        sim.get("beacon").meters["lit"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("oil").meters["spilled"] >= THRESHOLD,
        "danger": sim.get("below").meters["danger"],
        "lit": lit,
    }


def introduce(world: World, a: Entity, b: Entity, elder: Entity, setting: Setting, weather: Weather) -> None:
    world.say(
        f"In the old days, when every road listened to signs from above, "
        f"{a.id} and {b.id} kept watch for {elder.label} on {setting.spire_name} in {setting.place}."
    )
    world.say(
        f"Below them lay {setting.below}, where {setting.travelers} waited each evening for the beacon's answer."
    )
    world.say(weather.sky)
    world.say(weather.rise)
    world.say(weather.danger)


def climb_with_fuel(world: World, a: Entity, fuel: Fuel) -> None:
    a.memes["duty"] += 1
    world.say(
        f"That evening {a.id} climbed the last stair carrying {fuel.phrase}. "
        f"It was {fuel.carry}, and {a.pronoun()} had been told it would feed the sacred fire."
    )
    world.say(fuel.signal)


def see_and_misread(world: World, b: Entity, a: Entity, fuel: Fuel, misread: Misread) -> None:
    pred = predict_beacon(world, fuel, WEATHERS[world.facts["weather_id"]], world.facts["spark"], world.facts["delay"])
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["fear"] += 1
    world.say(
        f"But when {b.id} saw the fuel in {a.id}'s hands, {b.pronoun()} {misread.claim}."
    )
    if fuel.looks_dirty:
        world.say(
            f"The little lumps looked humble and ugly in the dusk, and fear made them seem worse than they were."
        )
    world.say(f'{misread.shout} {b.id} cried.')


def accuse(world: World, a: Entity, b: Entity) -> None:
    a.memes["accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} stared in hurt surprise. {a.pronoun().capitalize()} answered that {a.pronoun('possessive')} hands were clean and {a.pronoun('possessive')} errand honest,"
    )
    world.say(
        f"but the words came too fast, and soon both keepers were speaking like flint striking flint."
    )


def struggle(world: World, a: Entity, b: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{b.id} reached for the pouch, {a.id} pulled back, and between them the oil jar rang against the stones and broke."
    )
    world.say(
        f"The sharp smell ran over the steps, and the waiting brazier gave only a weak cough of smoke."
    )


def bad_turn(world: World, setting: Setting, fuel: Fuel, weather: Weather, spark: bool, delay: int) -> None:
    beacon = world.get("beacon")
    below = world.get("below")
    if spark and delay <= 1 and fuel.power >= weather.need:
        beacon.meters["lit"] += 1
        beacon.meters["late"] += 1
        below.meters["danger"] += 1
        world.say(
            f"At last {a_or_b(world)} found one ember sleeping in the ash pan below the brazier."
        )
        world.say(
            f"They coaxed up a thin flame, but it rose too late. The light touched the weather only after the world below had already gone astray."
        )
    else:
        beacon.meters["dark"] += 1
        below.meters["danger"] += 2
        world.say(
            f"When the sun slid away, the brazier atop the spire stayed dark."
        )
        world.say(
            f"No fire answered the deepening weather. The heights were silent when help was needed most."
        )


def loss(world: World, setting: Setting) -> None:
    outcome = world.facts["outcome"]
    if outcome == "late":
        world.say(
            f"Because the sign came late, {setting.loss}."
        )
        world.say(
            f"No one below forgot that the beacon had spoken after the danger, not before it."
        )
    else:
        world.say(
            f"Because the sign never came, {setting.loss}."
        )
        world.say(
            f"The grief below climbed the spire in shouts and bells before morning."
        )


def ending(world: World, a: Entity, b: Entity, elder: Entity, setting: Setting) -> None:
    for keeper in (a, b):
        keeper.memes["sorrow"] += 1
        keeper.memes["trust"] = 0.0
    elder.memes["grief"] += 1
    world.say(
        f"When {elder.label} climbed the steps at dawn, neither child tried to speak first."
    )
    world.say(
        f"They knew the quarrel had been built on a lie born from fear, yet knowing it then could not mend the night."
    )
    world.say(
        f"{a.id} kept the torn pouch in {a.pronoun('possessive')} hands. {b.id} could not bear to look at it."
    )
    world.say(setting.closing_image)


def a_or_b(world: World) -> str:
    if world.get("keeper_one").memes["duty"] >= world.get("keeper_two").memes["duty"]:
        return world.get("keeper_one").id
    return world.get("keeper_two").id


def tell(
    setting: Setting,
    weather: Weather,
    fuel: Fuel,
    misread: Misread,
    keeper_one: str = "Asha",
    keeper_one_gender: str = "girl",
    keeper_two: str = "Kian",
    keeper_two_gender: str = "boy",
    elder_title: str = "the old warden",
    spark: bool = True,
    trait_one: str = "dutiful",
    trait_two: str = "proud",
    delay: int = 1,
) -> World:
    world = World()
    a = world.add(Entity(id="keeper_one", kind="character", type=keeper_one_gender, label=keeper_one, role="carrier", traits=[trait_one]))
    b = world.add(Entity(id="keeper_two", kind="character", type=keeper_two_gender, label=keeper_two, role="watcher", traits=[trait_two]))
    elder = world.add(Entity(id="elder", kind="character", type="woman" if elder_title == "the old priestess" else "man", label=elder_title, role="elder"))
    world.add(Entity(id="beacon", type="beacon", label="the beacon"))
    world.add(Entity(id="oil", type="oil jar", label="the oil jar"))
    world.add(Entity(id="below", type="below", label=setting.below))
    a.memes["trust"] = 4.0
    b.memes["trust"] = 4.0

    world.facts["weather_id"] = weather.id
    world.facts["spark"] = spark
    world.facts["delay"] = delay

    introduce(world, a, b, elder, setting, weather)
    world.para()
    climb_with_fuel(world, a, fuel)
    see_and_misread(world, b, a, fuel, misread)
    accuse(world, a, b)
    struggle(world, a, b)

    world.para()
    bad_turn(world, setting, fuel, weather, spark, delay)
    loss(world, setting)

    world.para()
    ending(world, a, b, elder, setting)

    world.facts.update(
        setting=setting,
        weather=weather,
        fuel=fuel,
        misread=misread,
        keeper_one_ent=a,
        keeper_two_ent=b,
        elder=elder,
        spark=spark,
        spilled=world.get("oil").meters["spilled"] >= THRESHOLD,
        outcome="late" if world.get("beacon").meters["late"] >= THRESHOLD else "dark",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["keeper_one_ent"]
    b = f["keeper_two_ent"]
    setting = f["setting"]
    fuel = f["fuel"]
    weather = f["weather"]
    misread = f["misread"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the words "poop-pl" and "spire", with a misunderstanding that turns into conflict and ends badly.',
        f"Tell a mythic story where two young keepers on {setting.spire_name} must light a beacon before {weather.id}, but {b.label} wrongly accuses {a.label} over {fuel.label}.",
        f"Write a sad myth about fear making children misunderstand one another, so a holy fire on a spire is lit too late or not at all.",
    ]


KNOWLEDGE = {
    "spire": [
        (
            "What is a spire?",
            "A spire is a very tall, narrow tower or top of a tower. People can use a high spire to see far away or to show a light."
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a fire or lamp used as a signal. It helps people find the right way when it is dark or dangerous."
        )
    ],
    "fog": [
        (
            "Why is fog hard to travel in?",
            "Fog fills the air with tiny drops of water, so faraway things look blurry and fade away. That makes it hard to tell where the safe path is."
        )
    ],
    "storm": [
        (
            "Why can storms make travel dangerous?",
            "Storms bring wind, rain, and loud noise that hide the way. In a storm, people can miss rocks, roads, or safe channels."
        )
    ],
    "snow": [
        (
            "Why can snow hide the road?",
            "Snow can cover footprints, stones, and edges, so the ground all starts to look the same. That makes it easier to get lost."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what another person means or is doing. It can cause hurt feelings and trouble if nobody stops to ask calmly."
        )
    ],
    "conflict": [
        (
            "What is a conflict?",
            "A conflict is a fight or sharp disagreement between people. It often grows when both sides are angry and stop listening."
        )
    ],
    "poop-pl": [
        (
            "What was poop-pl in this story world?",
            "Poop-pl was a strange temple fuel made into little brown pellets. Even though it looked humble, it was meant to help the beacon burn strongly."
        )
    ],
}

KNOWLEDGE_ORDER = ["spire", "beacon", "fog", "storm", "snow", "misunderstanding", "conflict", "poop-pl"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["keeper_one_ent"]
    b = f["keeper_two_ent"]
    elder = f["elder"]
    setting = f["setting"]
    weather = f["weather"]
    fuel = f["fuel"]
    misread = f["misread"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two young keepers on {setting.spire_name}, and {elder.label} who trusted them with the beacon."
        ),
        (
            "What were the keepers supposed to do?",
            f"They were supposed to light the beacon on the spire before {weather.id} grew worse. The light was meant to guide {setting.travelers} below."
        ),
        (
            f"Why did {b.label} get angry?",
            f"{b.label} misunderstood the {fuel.label} and {misread.claim}. Because fear came first, {b.pronoun()} judged before listening."
        ),
        (
            "What changed the story from worry into real trouble?",
            f"The misunderstanding turned into a quarrel, and during the struggle the oil jar broke. That left the beacon weak or dark when the weather closed in."
        ),
    ]
    if outcome == "late":
        qa.append(
            (
                "Did the beacon help in time?",
                "No. A small flame finally rose, but it came too late to protect everyone below. The signal answered after the danger had already begun its harm."
            )
        )
    else:
        qa.append(
            (
                "Did the beacon light at all?",
                "No. The beacon stayed dark when help was needed most. Because no clear signal shone from the spire, the travelers below lost their way."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended sadly: {setting.loss}. By dawn the children understood the truth, but the damage from the quarrel could not be undone."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"spire", "beacon", "misunderstanding", "conflict"}
    tags |= set(world.facts["weather"].tags)
    tags |= set(world.facts["fuel"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="harbor",
        weather="fog",
        fuel="poop_pl",
        misread="filth",
        keeper_one="Asha",
        keeper_one_gender="girl",
        keeper_two="Kian",
        keeper_two_gender="boy",
        elder_title="the old warden",
        spark=True,
        trait_one="dutiful",
        trait_two="proud",
        delay=1,
    ),
    StoryParams(
        setting="valley",
        weather="snow",
        fuel="cedar_pitch",
        misread="curse",
        keeper_one="Mira",
        keeper_one_gender="girl",
        keeper_two="Soren",
        keeper_two_gender="boy",
        elder_title="the old priestess",
        spark=False,
        trait_one="solemn",
        trait_two="quick",
        delay=2,
    ),
    StoryParams(
        setting="delta",
        weather="storm",
        fuel="poop_pl",
        misread="curse",
        keeper_one="Nila",
        keeper_one_gender="girl",
        keeper_two="Tomas",
        keeper_two_gender="boy",
        elder_title="the old warden",
        spark=False,
        trait_one="eager",
        trait_two="restless",
        delay=2,
    ),
    StoryParams(
        setting="harbor",
        weather="storm",
        fuel="poop_pl",
        misread="filth",
        keeper_one="Iri",
        keeper_one_gender="girl",
        keeper_two="Rian",
        keeper_two_gender="boy",
        elder_title="the old priestess",
        spark=True,
        trait_one="dutiful",
        trait_two="quick",
        delay=2,
    ),
    StoryParams(
        setting="valley",
        weather="fog",
        fuel="sun_oil",
        misread="theft",
        keeper_one="Vesa",
        keeper_one_gender="girl",
        keeper_two="Niko",
        keeper_two_gender="boy",
        elder_title="the old warden",
        spark=True,
        trait_one="eager",
        trait_two="proud",
        delay=1,
    ),
]


ASP_RULES = r"""
weather_fits(S, W) :- setting(S), weather(W), allowed_weather(S, W).
strong_enough(F, W) :- fuel(F), weather(W), fuel_power(F, P), weather_need(W, N), P >= N.
misread_fits(F, M) :- fuel(F), misread(M), suspicious(F, T), misread_tag(M, T).

valid(S, W, F, M) :- weather_fits(S, W), strong_enough(F, W), misread_fits(F, M).

late :- chosen_spark(1), chosen_delay(D), D <= 1,
        chosen_weather(W), chosen_fuel(F), strong_enough(F, W).
dark :- not late.
outcome(late) :- late.
outcome(dark) :- dark.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for wid in sorted(setting.weather_ids):
            lines.append(asp.fact("allowed_weather", sid, wid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("weather_need", wid, weather.need))
    for fid, fuel in FUELS.items():
        lines.append(asp.fact("fuel", fid))
        lines.append(asp.fact("fuel_power", fid, fuel.power))
        for tag in sorted(fuel.suspicious_reasons):
            lines.append(asp.fact("suspicious", fid, tag))
    for mid, misread in MISREADS.items():
        lines.append(asp.fact("misread", mid))
        lines.append(asp.fact("misread_tag", mid, misread.fit_tag))
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
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_fuel", params.fuel),
            asp.fact("chosen_spark", 1 if params.spark else 0),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a mythic beacon, a misunderstanding, and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--fuel", choices=FUELS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--elder-title", choices=["the old warden", "the old priestess"])
    ap.add_argument("--spark", choices=["yes", "no"], help="whether a backup ember can still be found")
    ap.add_argument("--delay", type=int, choices=[1, 2], help="how long the quarrel delays the beacon")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    spark = None
    if args.spark is not None:
        spark = args.spark == "yes"

    if args.setting and args.weather and args.fuel and args.misread:
        if not valid_combo(args.setting, args.weather, args.fuel, args.misread):
            raise StoryError(explain_rejection(args.setting, args.weather, args.fuel, args.misread))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.weather is None or combo[1] == args.weather)
        and (args.fuel is None or combo[2] == args.fuel)
        and (args.misread is None or combo[3] == args.misread)
    ]
    if not combos:
        if args.setting and args.weather and args.fuel and args.misread:
            raise StoryError(explain_rejection(args.setting, args.weather, args.fuel, args.misread))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, weather_id, fuel_id, misread_id = rng.choice(sorted(combos))
    gender_one = rng.choice(["girl", "boy"])
    gender_two = rng.choice(["girl", "boy"])
    name_one = _pick_name(rng, gender_one)
    name_two = _pick_name(rng, gender_two, avoid=name_one)
    elder_title = args.elder_title or rng.choice(["the old warden", "the old priestess"])
    spark_value = spark if spark is not None else rng.choice([True, False, True])
    delay = args.delay if args.delay is not None else rng.choice([1, 2])
    return StoryParams(
        setting=setting_id,
        weather=weather_id,
        fuel=fuel_id,
        misread=misread_id,
        keeper_one=name_one,
        keeper_one_gender=gender_one,
        keeper_two=name_two,
        keeper_two_gender=gender_two,
        elder_title=elder_title,
        spark=spark_value,
        trait_one=rng.choice(TRAITS),
        trait_two=rng.choice(TRAITS),
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        weather = WEATHERS[params.weather]
        fuel = FUELS[params.fuel]
        misread = MISREADS[params.misread]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not valid_combo(params.setting, params.weather, params.fuel, params.misread):
        raise StoryError(explain_rejection(params.setting, params.weather, params.fuel, params.misread))

    world = tell(
        setting=setting,
        weather=weather,
        fuel=fuel,
        misread=misread,
        keeper_one=params.keeper_one,
        keeper_one_gender=params.keeper_one_gender,
        keeper_two=params.keeper_two,
        keeper_two_gender=params.keeper_two_gender,
        elder_title=params.elder_title,
        spark=params.spark,
        trait_one=params.trait_one,
        trait_two=params.trait_two,
        delay=params.delay,
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
    for i in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(i))
        except StoryError:
            continue
        cases.append(p)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible (setting, weather, fuel, misread) combos:\n")
        for setting, weather, fuel, misread in combos:
            print(f"  {setting:8} {weather:6} {fuel:12} {misread}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.keeper_one} and {p.keeper_two}: {p.fuel} on the {p.setting} spire ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
