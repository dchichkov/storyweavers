#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dissimilar_assumption_nervous_misunderstanding_tall_tale.py
======================================================================================

A standalone storyworld for a child-facing tall tale about a giant misunderstanding.

Premise
-------
In a roomy frontier place, a child notices an enormous sign -- thunder, giant tracks,
or a wobbling shadow -- and makes a wild assumption about what kind of creature is
coming. The assumption is wrong. The real creature is enormous but gentle and merely
nervous because something ordinary has scared it. A calm helper reads the world more
carefully, so the child switches from fear to help, and the ending image proves the
misunderstanding has been mended.

The world keeps two small axes in play:

* physical meters: noise, fear source, calmness, damage-risk, mess
* emotional memes: alarm, courage, relief, kindness, embarrassment

The "tall tale" quality comes from scale and imagery, not nonsense: hats can jump
from heads, barns can rattle, and tracks can look skillet-sized, but the world still
checks that a clue can plausibly trigger the chosen mistaken assumption, and that the
chosen comfort method suits the real creature.

Run it
------
python storyworlds/worlds/gpt-5.4/dissimilar_assumption_nervous_misunderstanding_tall_tale.py
python storyworlds/worlds/gpt-5.4/dissimilar_assumption_nervous_misunderstanding_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/dissimilar_assumption_nervous_misunderstanding_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/dissimilar_assumption_nervous_misunderstanding_tall_tale.py --asp
python storyworlds/worlds/gpt-5.4/dissimilar_assumption_nervous_misunderstanding_tall_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    sight: str
    sound: str
    hint_trait: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MistakenThing:
    id: str
    label: str
    phrase: str
    requires: set[str] = field(default_factory=set)
    boast: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    kind_word: str
    size_line: str
    sound_line: str
    likes: str
    afraid_of: set[str] = field(default_factory=set)
    comforts: set[str] = field(default_factory=set)
    helper_fix: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Scare:
    id: str
    label: str
    phrase: str
    tag: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    skill: str
    action: str
    result: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm_spreads(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    creature = world.get("creature")
    if creature.meters["racket"] >= THRESHOLD and hero.memes["alarm"] < THRESHOLD:
        sig = ("alarm", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["alarm"] += 1
            helper.memes["concern"] += 1
            world.get("place").meters["risk"] += 1
            out.append("__alarm__")
    return out


def _r_kindness_calms(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.memes["comforted"] >= THRESHOLD:
        sig = ("calmed", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.memes["calm"] += 1
            creature.meters["racket"] = 0.0
            world.get("place").meters["risk"] = 0.0
            out.append("__calmed__")
    return out


CAUSAL_RULES = [
    Rule(name="alarm_spreads", tag="social", apply=_r_alarm_spreads),
    Rule(name="kindness_calms", tag="social", apply=_r_kindness_calms),
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


def clue_matches_assumption(clue: Clue, mistaken: MistakenThing) -> bool:
    return clue.hint_trait in mistaken.requires


def comfort_works(creature: Creature, scare: Scare, comfort: Comfort) -> bool:
    return scare.tag in creature.afraid_of and comfort.skill in creature.comforts


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for clue_id, clue in CLUES.items():
            for mistaken_id, mistaken in MISTAKEN.items():
                if not clue_matches_assumption(clue, mistaken):
                    continue
                for creature_id, creature in CREATURES.items():
                    for scare_id, scare in SCARES.items():
                        for comfort_id, comfort in COMFORTS.items():
                            if comfort_works(creature, scare, comfort):
                                combos.append((place_id, clue_id, mistaken_id, creature_id, scare_id, comfort_id))
    return combos


def predict_misread(world: World, clue: Clue, mistaken: MistakenThing) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["alarm"] += 1 if clue_matches_assumption(clue, mistaken) else 0
    return {
        "alarmed": hero.memes["alarm"] >= THRESHOLD,
        "risk": sim.get("place").meters["risk"],
    }


def introduce(world: World, place: Place, hero: Entity, helper: Entity) -> None:
    world.say(
        f"On the broadest morning {place.label} had seen that week, {hero.id} stood with "
        f"{helper.id} where {place.opening}."
    )
    world.say(
        f"The place was so roomy that a shout could take a nap halfway across it before "
        f"reaching the fence."
    )


def first_clue(world: World, hero: Entity, clue: Clue) -> None:
    world.say(clue.sight)
    world.say(clue.sound)
    world.facts["clue_seen"] = True


def jump_to_assumption(world: World, hero: Entity, helper: Entity, clue: Clue, mistaken: MistakenThing) -> None:
    pred = predict_misread(world, clue, mistaken)
    if pred["alarmed"]:
        hero.memes["alarm"] += 1
        hero.memes["imagination"] += 1
    world.say(
        f'"That can only mean {mistaken.phrase}!" {hero.id} gasped. '
        f'It was a mighty assumption, built faster than a pancake flips on a hot griddle.'
    )
    world.say(
        f'{hero.id} felt nervous clear down to {hero.pronoun("possessive")} bootlaces, '
        f'and because the clue and the truth were so dissimilar, the misunderstanding grew legs at once.'
    )


def helper_doubts(world: World, helper: Entity, clue: Clue, mistaken: MistakenThing) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} narrowed {helper.pronoun("possessive")} eyes at the sign in the dust. '
        f'"Maybe," {helper.pronoun()} said, "but {clue.label} can fool a person when {helper.pronoun()} looks too quick."'
    )
    if mistaken.boast:
        world.say(mistaken.boast)


def reveal_real_creature(world: World, creature: Creature, scare: Scare) -> None:
    ent = world.get("creature")
    ent.meters["racket"] += 1
    ent.memes["fear"] += 1
    ent.meters["mess"] += 1
    world.facts["scare_seen"] = scare.label
    propagate(world, narrate=False)
    world.say(
        f"Then the truth lumbered into view: {creature.phrase}. {creature.size_line}"
    )
    world.say(
        f"{creature.sound_line} It was not fierce at all. It was only nervous because {scare.effect}."
    )


def near_trouble(world: World, place: Place, creature: Creature, clue: Clue) -> None:
    world.say(
        f"With every startled hop, the ground shivered and the air shook, and for a minute it looked as if "
        f"{clue.risk}."
    )


def helper_reads_world(world: World, helper: Entity, creature: Creature, scare: Scare) -> None:
    helper.memes["wisdom"] += 1
    world.say(
        f'{helper.id} tipped {helper.pronoun("possessive")} hat back and listened harder. '
        f'"Hear that?" {helper.pronoun()} said. "That is not anger. That is worry. '
        f'{creature.helper_fix}"'
    )
    world.say(
        f'Then {helper.pronoun()} pointed at the real trouble: {scare.phrase}.'
    )


def comfort_creature(world: World, hero: Entity, helper: Entity, creature: Creature, comfort: Comfort) -> None:
    ent = world.get("creature")
    hero.memes["courage"] += 1
    hero.memes["kindness"] += 1
    ent.memes["comforted"] += 1
    ent.attrs["comfort"] = comfort.label
    propagate(world, narrate=False)
    world.say(
        f'{helper.id} showed {hero.id} the safe way to help, and together they {comfort.action}.'
    )
    world.say(
        f"{comfort.result} The great {creature.kind_word} stopped trembling long enough to blink its huge kind eyes."
    )


def resolve(world: World, hero: Entity, creature: Creature, comfort: Comfort) -> None:
    hero.memes["relief"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f'{hero.id} let out a breath so long it could have dried a creek bed. '
        f'"It was not {world.facts["mistaken"].phrase} after all," {hero.pronoun()} said.'
    )
    world.say(
        f'"No," said {world.get("helper").id}, smiling. "Just a big heart having a big scare."'
    )
    world.say(
        f"From then on, whenever a strange sign appeared, {hero.id} remembered that a quick assumption can grow "
        f"taller than a windmill, while the truth may be plain and gentle."
    )


def closing_image(world: World, place: Place, creature: Creature) -> None:
    world.say(
        f"By sundown, {creature.ending_image}, and {place.ending}."
    )


def tell(
    place: Place,
    clue: Clue,
    mistaken: MistakenThing,
    creature: Creature,
    scare: Scare,
    comfort: Comfort,
    hero_name: str = "Tess",
    hero_type: str = "girl",
    helper_name: str = "Old Juniper",
    helper_type: str = "woman",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, phrase=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, phrase=helper_name, role="helper"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label, phrase=place.label, role="place"))
    creature_ent = world.add(
        Entity(
            id="creature",
            kind="thing",
            type="creature",
            label=creature.label,
            phrase=creature.phrase,
            role="creature",
            tags=set(creature.tags),
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        place_cfg=place,
        clue=clue,
        mistaken=mistaken,
        creature_cfg=creature,
        scare=scare,
        comfort=comfort,
    )

    introduce(world, place, hero, helper)
    first_clue(world, hero, clue)

    world.para()
    jump_to_assumption(world, hero, helper, clue, mistaken)
    helper_doubts(world, helper, clue, mistaken)

    world.para()
    reveal_real_creature(world, creature, scare)
    near_trouble(world, place, creature, clue)

    world.para()
    helper_reads_world(world, helper, creature, scare)
    comfort_creature(world, hero, helper, creature, comfort)
    resolve(world, hero, creature, comfort)

    world.para()
    closing_image(world, place, creature)

    world.facts.update(
        misunderstood=True,
        calmed=creature_ent.memes["calm"] >= THRESHOLD,
        risk_gone=place_ent.meters["risk"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    clue: str
    mistaken: str
    creature: str
    scare: str
    comfort: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "prairie": Place(
        id="prairie",
        label="on the prairie edge",
        opening="the grass rolled in waves right up to the red barn",
        ending="the red barn stood quiet again, with only crickets keeping watch",
        tags={"prairie"},
    ),
    "canyon": Place(
        id="canyon",
        label="by the canyon pasture",
        opening="the canyon wall threw back every hoofbeat twice",
        ending="the canyon kept the evening cool and the fences humming softly",
        tags={"canyon"},
    ),
    "riverside": Place(
        id="riverside",
        label="beside the riverside meadow",
        opening="the river shone like a silver rope beside the long grass",
        ending="the river slid past in a calm silver ribbon",
        tags={"river"},
    ),
}

CLUES = {
    "tracks": Clue(
        id="tracks",
        label="giant tracks",
        sight="In the dust lay tracks as wide as washbasins and as deep as soup bowls.",
        sound="From somewhere beyond the fence came a heavy huff and a clump that made the milk pails tinkle.",
        hint_trait="footprints",
        risk="the fence might pop like a row of crackers",
        tags={"tracks"},
    ),
    "shadow": Clue(
        id="shadow",
        label="a wobbling shadow",
        sight="Across the side of the barn slid a wobbling shadow so long it seemed to borrow extra evening from the sun.",
        sound="The boards gave a low boom-boom, like a giant knocking politely with two soft fists.",
        hint_trait="shape",
        risk="the hay wagon might roll itself backward from fright",
        tags={"shadow"},
    ),
    "snort": Clue(
        id="snort",
        label="a sky-shaking snort",
        sight="Dust jumped from the road in tiny puffs, though nobody could yet be seen.",
        sound="Then came a snort so big it startled three sparrows right out of one tree at the same time.",
        hint_trait="noise",
        risk="the lantern hooks might ring all afternoon",
        tags={"snort"},
    ),
}

MISTAKEN = {
    "giant": MistakenThing(
        id="giant",
        label="a hill giant",
        phrase="a hill giant coming to borrow the barn roof for a hat",
        requires={"footprints", "shape"},
        boast="Folks said a hill giant once stepped over the moonlight without wrinkling it.",
        tags={"giant"},
    ),
    "dragon": MistakenThing(
        id="dragon",
        label="a prairie dragon",
        phrase="a prairie dragon looking for a place to sneeze sparks",
        requires={"noise", "shape"},
        boast="In tall-tale country, a prairie dragon is blamed whenever the kettle whistles too hard.",
        tags={"dragon"},
    ),
    "thunderbird": MistakenThing(
        id="thunderbird",
        label="the thunderbird",
        phrase="the thunderbird dipping low enough to flap the weather crooked",
        requires={"noise", "footprints"},
        boast="Some cousins swore the thunderbird could flap rain out of a clear blue noon.",
        tags={"thunderbird"},
    ),
}

CREATURES = {
    "ox": Creature(
        id="ox",
        label="blue ox",
        phrase="a blue ox taller than a wagon stack",
        kind_word="ox",
        size_line="Its shoulders rose so high that swallows might have mistaken them for a small hill.",
        sound_line="Every breath from its nose moved the grass in two shiny lanes.",
        likes="salt apples",
        afraid_of={"tin_rattle", "echo", "kite"},
        comforts={"hum", "snack"},
        helper_fix="Big creatures make big noises when they are scared, same as small ones.",
        ending_image="the blue ox was crunching quietly beside the trough, its tail swishing like a lazy rope",
        tags={"ox"},
    ),
    "hen": Creature(
        id="hen",
        label="prairie hen",
        phrase="a prairie hen bigger than a porch swing",
        kind_word="hen",
        size_line="Its feathers puffed so wide it looked like a haystack had decided to grow legs.",
        sound_line="Its worried clucks bounced off the boards in a hundred little echoes.",
        likes="corn cakes",
        afraid_of={"kite", "echo", "tin_rattle"},
        comforts={"grain", "hum"},
        helper_fix="Listen close and you can hear the flutter in it.",
        ending_image="the giant hen was pecking corn as neatly as a needle sewing buttons",
        tags={"hen"},
    ),
    "calf": Creature(
        id="calf",
        label="spotted calf",
        phrase="a spotted calf as high as a porch roof",
        kind_word="calf",
        size_line="Its ears were so broad that each one looked ready to catch a whole gust of wind.",
        sound_line="Its moo quivered at the edges, like a door trying not to creak.",
        likes="sweet clover",
        afraid_of={"tin_rattle", "kite", "echo"},
        comforts={"rope", "snack"},
        helper_fix="That sound says 'please help me,' not 'run for the hills.'",
        ending_image="the giant calf was nosing sweet clover in slow happy circles",
        tags={"calf"},
    ),
}

SCARES = {
    "tin_rattle": Scare(
        id="tin_rattle",
        label="loose tin pans banging on a line",
        phrase="a string of loose tin pans knocking together in the wind",
        tag="tin_rattle",
        effect="a string of loose tin pans was banging and flashing in the wind",
        tags={"tin"},
    ),
    "kite": Scare(
        id="kite",
        label="a torn red kite snapping overhead",
        phrase="a torn red kite whipping and snapping over the pasture",
        tag="kite",
        effect="a torn red kite kept diving and snapping above its head",
        tags={"kite"},
    ),
    "echo": Scare(
        id="echo",
        label="a bouncing canyon echo",
        phrase="a bouncing echo that threw every small sound back twice as large",
        tag="echo",
        effect="the canyon echo was tossing its own scared noises right back at it",
        tags={"echo"},
    ),
}

COMFORTS = {
    "hum": Comfort(
        id="hum",
        label="a low humming song",
        phrase="a low humming song",
        skill="hum",
        action="sang a low humming song and moved slow as drifting shade",
        result="The long notes settled over the field the way a blanket settles over sleepy knees",
        tags={"song"},
    ),
    "snack": Comfort(
        id="snack",
        label="a bucket of treats",
        phrase="a bucket of treats",
        skill="snack",
        action="held out a bucket of treats and spoke in soft steady voices",
        result="One careful sniff became two, and soon the creature was thinking more about eating than fearing",
        tags={"treats"},
    ),
    "grain": Comfort(
        id="grain",
        label="a scoop of grain",
        phrase="a scoop of grain",
        skill="grain",
        action="scattered a shining trail of grain and whispered kindly",
        result="The tiny patter of grain on the ground gave the big frightened creature something simple to follow",
        tags={"grain"},
    ),
    "rope": Comfort(
        id="rope",
        label="a soft lead rope",
        phrase="a soft lead rope",
        skill="rope",
        action="looped a soft lead rope gently and walked toward the gate one patient step at a time",
        result="The steady pull gave the trembling creature a clear safe path to trust",
        tags={"rope"},
    ),
}

GIRL_NAMES = ["Tess", "Maisie", "Ruby", "Clara", "Nell", "Willa"]
BOY_NAMES = ["Beau", "Eli", "Hank", "Jesse", "Milo", "Otis"]
HELPER_WOMEN = ["Old Juniper", "Aunt Maybelle", "Miss Lark"]
HELPER_MEN = ["Old Cedar", "Uncle Bo", "Mister Pike"]


CURATED = [
    StoryParams(
        place="prairie",
        clue="tracks",
        mistaken="giant",
        creature="ox",
        scare="tin_rattle",
        comfort="hum",
        hero_name="Tess",
        hero_gender="girl",
        helper_name="Old Juniper",
        helper_gender="woman",
    ),
    StoryParams(
        place="canyon",
        clue="shadow",
        mistaken="dragon",
        creature="hen",
        scare="kite",
        comfort="grain",
        hero_name="Beau",
        hero_gender="boy",
        helper_name="Old Cedar",
        helper_gender="man",
    ),
    StoryParams(
        place="riverside",
        clue="snort",
        mistaken="thunderbird",
        creature="calf",
        scare="echo",
        comfort="rope",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Aunt Maybelle",
        helper_gender="woman",
    ),
    StoryParams(
        place="prairie",
        clue="shadow",
        mistaken="dragon",
        creature="ox",
        scare="kite",
        comfort="snack",
        hero_name="Hank",
        hero_gender="boy",
        helper_name="Mister Pike",
        helper_gender="man",
    ),
]


KNOWLEDGE = {
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show that something passed by, how big it was, and sometimes how fast it was moving. But tracks do not tell the whole story all by themselves."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off a wall, canyon, or big hard surface and comes back to your ears. It can make a small sound seem bigger or stranger."
        )
    ],
    "kite": [
        (
            "Why might a snapping kite scare an animal?",
            "A snapping kite moves fast and makes sudden flapping sounds overhead. Many animals get nervous when something strange dives and crackles above them."
        )
    ],
    "tin": [
        (
            "Why do banging pans make loud noise?",
            "Metal pans are hard and ring when they hit each other. In the wind they can clatter again and again, which sounds sharp and startling."
        )
    ],
    "song": [
        (
            "Why can a soft song calm someone down?",
            "A soft steady song is predictable, so it can make a frightened body slow down and feel safer. Calm sounds help replace sudden scary ones."
        )
    ],
    "treats": [
        (
            "Why can food help calm an animal?",
            "A familiar snack can help a frightened animal focus on something safe and pleasant. It also shows that the person nearby is not trying to hurt it."
        )
    ],
    "grain": [
        (
            "Why would grain help a bird feel safe?",
            "Grain is familiar food for many birds. Seeing it scattered on the ground gives them a simple safe thing to peck at instead of watching the scary thing."
        )
    ],
    "rope": [
        (
            "What does a lead rope do?",
            "A lead rope helps guide an animal in a steady gentle way. Used kindly, it can show the animal where safety is."
        )
    ],
    "giant": [
        (
            "What is an assumption?",
            "An assumption is when you decide what is true before you really know. Sometimes assumptions are wrong, so it helps to look again."
        )
    ],
    "dragon": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what they saw or heard. It can shrink when people slow down and check the facts."
        )
    ],
    "thunderbird": [
        (
            "Why can big stories sound true at first?",
            "Big stories use exciting details that grab your attention fast. When people are nervous, they may believe the most dramatic idea before the simplest one."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    clue = f["clue"]
    mistaken = f["mistaken"]
    creature = f["creature_cfg"]
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the words "dissimilar", "assumption", and "nervous".',
        f"Tell a gentle misunderstanding story where {hero.label} sees {clue.label} at {place.label} and makes a wild assumption about {mistaken.label}, but the truth is a scared {creature.label}.",
        f"Write a child-facing tall tale where a huge sign looks frightening at first, then turns into a lesson about looking carefully and helping kindly.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    mistaken = f["mistaken"]
    creature = f["creature_cfg"]
    scare = f["scare"]
    comfort = f["comfort"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who notices a giant clue and gets scared, and {helper.label}, who helps read the situation more carefully. It is also about the huge {creature.label} that only needs help."
        ),
        (
            f"What made {hero.label} think something scary was coming?",
            f"{hero.label} saw {clue.label} and heard the big noise that came with it. Because those signs seemed so enormous, {hero.pronoun('subject')} made the assumption that {mistaken.phrase}."
        ),
        (
            f"Why was that a misunderstanding?",
            f"It was a misunderstanding because the real creature was not dangerous at all. The clue and the truth were dissimilar, and the sound came from a frightened {creature.kind_word}, not from {mistaken.label}."
        ),
        (
            f"Why was the {creature.label} acting so wildly?",
            f"It was nervous because {scare.effect}. The strange trouble kept startling it, so each frightened jump made the place feel more dangerous."
        ),
        (
            f"How did {helper.label} and {hero.label} solve the problem?",
            f"They stopped guessing and looked closely at what was really wrong. Then they {comfort.action}, which worked because it matched what could calm that creature."
        ),
        (
            "How did the story end?",
            f"It ended with the danger gone and the giant creature calm again. The last picture shows that what looked frightening was really a big scared heart needing gentle help."
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set()
    tags |= set(f["clue"].tags)
    tags |= set(f["mistaken"].tags)
    tags |= set(f["scare"].tags)
    tags |= set(f["comfort"].tags)
    order = ["tracks", "echo", "kite", "tin", "song", "treats", "grain", "rope", "giant", "dragon", "thunderbird"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% clue / mistaken reasonableness
clue_matches(C, M) :- clue_trait(C, T), assumption_need(M, T).

% creature / scare / comfort reasonableness
comfort_works(Cr, Sc, Co) :- fears(Cr, Tag), scare_tag(Sc, Tag), can_comfort(Cr, Skill), comfort_skill(Co, Skill).

valid(P, C, M, Cr, Sc, Co) :- place(P), clue(C), mistaken(M), creature(Cr), scare(Sc), comfort(Co),
                              clue_matches(C, M), comfort_works(Cr, Sc, Co).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_trait", clue_id, clue.hint_trait))
    for mistaken_id, mistaken in MISTAKEN.items():
        lines.append(asp.fact("mistaken", mistaken_id))
        for req in sorted(mistaken.requires):
            lines.append(asp.fact("assumption_need", mistaken_id, req))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        for tag in sorted(creature.afraid_of):
            lines.append(asp.fact("fears", creature_id, tag))
        for skill in sorted(creature.comforts):
            lines.append(asp.fact("can_comfort", creature_id, skill))
    for scare_id, scare in SCARES.items():
        lines.append(asp.fact("scare", scare_id))
        lines.append(asp.fact("scare_tag", scare_id, scare.tag))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("comfort_skill", comfort_id, comfort.skill))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
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
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale misunderstanding storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mistaken", choices=MISTAKEN)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--scare", choices=SCARES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def explain_rejection(clue: Clue, mistaken: MistakenThing, creature: Creature, scare: Scare, comfort: Comfort) -> str:
    if not clue_matches_assumption(clue, mistaken):
        return (
            f"(No story: {clue.label} does not honestly point toward {mistaken.label}. "
            f"The misunderstanding must come from a clue that could really invite that assumption.)"
        )
    if scare.tag not in creature.afraid_of:
        return (
            f"(No story: {creature.label} would not be frightened by {scare.label} in this world, "
            f"so the panic has no grounded cause.)"
        )
    if comfort.skill not in creature.comforts:
        return (
            f"(No story: {comfort.label} is not a believable way to calm {creature.label}. "
            f"Pick a comfort that matches the creature's needs.)"
        )
    return "(No story: that combination is not supported by the world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.mistaken:
        if not clue_matches_assumption(CLUES[args.clue], MISTAKEN[args.mistaken]):
            raise StoryError(
                explain_rejection(
                    CLUES[args.clue],
                    MISTAKEN[args.mistaken],
                    CREATURES[args.creature] if args.creature else next(iter(CREATURES.values())),
                    SCARES[args.scare] if args.scare else next(iter(SCARES.values())),
                    COMFORTS[args.comfort] if args.comfort else next(iter(COMFORTS.values())),
                )
            )
    if args.creature and args.scare and args.comfort:
        if not comfort_works(CREATURES[args.creature], SCARES[args.scare], COMFORTS[args.comfort]):
            raise StoryError(
                explain_rejection(
                    CLUES[args.clue] if args.clue else next(iter(CLUES.values())),
                    MISTAKEN[args.mistaken] if args.mistaken else next(iter(MISTAKEN.values())),
                    CREATURES[args.creature],
                    SCARES[args.scare],
                    COMFORTS[args.comfort],
                )
            )

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.mistaken is None or c[2] == args.mistaken)
        and (args.creature is None or c[3] == args.creature)
        and (args.scare is None or c[4] == args.scare)
        and (args.comfort is None or c[5] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue, mistaken, creature, scare, comfort = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_name = args.helper_name or rng.choice(HELPER_WOMEN if helper_gender == "woman" else HELPER_MEN)

    return StoryParams(
        place=place,
        clue=clue,
        mistaken=mistaken,
        creature=creature,
        scare=scare,
        comfort=comfort,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.mistaken not in MISTAKEN:
        raise StoryError(f"(Unknown mistaken thing: {params.mistaken})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.scare not in SCARES:
        raise StoryError(f"(Unknown scare: {params.scare})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")

    clue = CLUES[params.clue]
    mistaken = MISTAKEN[params.mistaken]
    creature = CREATURES[params.creature]
    scare = SCARES[params.scare]
    comfort = COMFORTS[params.comfort]

    if not clue_matches_assumption(clue, mistaken) or not comfort_works(creature, scare, comfort):
        raise StoryError(explain_rejection(clue, mistaken, creature, scare, comfort))

    world = tell(
        place=PLACES[params.place],
        clue=clue,
        mistaken=mistaken,
        creature=creature,
        scare=scare,
        comfort=comfort,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_gender,
    )
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return StorySample(
        params=params,
        story=world.render().replace("hero", hero.label).replace("helper", helper.label),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for place, clue, mistaken, creature, scare, comfort in combos:
            print(f"  {place:10} {clue:8} {mistaken:12} {creature:8} {scare:10} {comfort}")
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
            header = (
                f"### {p.hero_name}: {p.clue} -> {p.mistaken} / really {p.creature} "
                f"({p.scare}, {p.comfort})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
