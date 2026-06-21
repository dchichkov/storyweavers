#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pepperoni_epiphany_porcelain_conflict_mystery_to_solve.py
=====================================================================================

A standalone story world for a small folk-tale mystery:

A child in a village kitchen is meant to watch a blue porcelain plate of
pepperoni for the evening bread. Some of the pepperoni vanishes. In the first
sting of surprise, one child blames another. Then they search for clues, a true
epiphany arrives, and the real thief is found. The ending proves that the
conflict changed into trust.

This world prefers a *solvable* mystery: the chosen clue and the chosen storage
spot must narrow the thief down to exactly one plausible culprit. If the clue is
too vague for the place, the world refuses the story.

Run it
------
    python storyworlds/worlds/gpt-5.4/pepperoni_epiphany_porcelain_conflict_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/pepperoni_epiphany_porcelain_conflict_mystery_to_solve.py --storage shelf --clue pawprints
    python storyworlds/worlds/gpt-5.4/pepperoni_epiphany_porcelain_conflict_mystery_to_solve.py --storage table --clue pawprints
    python storyworlds/worlds/gpt-5.4/pepperoni_epiphany_porcelain_conflict_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/pepperoni_epiphany_porcelain_conflict_mystery_to_solve.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    village: str
    kitchen_detail: str
    outside_detail: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Storage:
    id: str
    label: str
    phrase: str
    height: str
    open_air: bool
    lookup_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    line: str
    indicates: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    kind: str
    can_reach: set[str] = field(default_factory=set)
    needs_open_air: bool = False
    hiding_place: str = ""
    carry_line: str = ""
    trail_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ElderStyle:
    id: str
    type: str
    gentle_line: str
    wisdom_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_conflict(world: World) -> list[str]:
    seeker = world.get("seeker")
    accused = world.get("accused")
    if seeker.memes["blame"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["conflict"] += 1
    accused.memes["conflict"] += 1
    accused.memes["hurt"] += 1
    return ["__conflict__"]


def _r_epiphany(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.memes["noticed_clue"] < THRESHOLD or seeker.memes["reasoned"] < THRESHOLD:
        return []
    sig = ("epiphany",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["epiphany"] += 1
    return ["__epiphany__"]


def _r_repair(world: World) -> list[str]:
    seeker = world.get("seeker")
    accused = world.get("accused")
    if seeker.memes["apology"] < THRESHOLD:
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["trust"] += 1
    accused.memes["trust"] += 1
    seeker.memes["conflict"] = 0.0
    accused.memes["conflict"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="epiphany", tag="mind", apply=_r_epiphany),
    Rule(name="repair", tag="social", apply=_r_repair),
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


def culprit_can_access(storage: Storage, culprit: Culprit) -> bool:
    if storage.height not in culprit.can_reach:
        return False
    if culprit.needs_open_air and not storage.open_air:
        return False
    return True


def clue_matches(clue: Clue, culprit: Culprit) -> bool:
    return culprit.id in clue.indicates


def candidate_culprits(storage: Storage, clue: Clue) -> list[str]:
    out = []
    for cid, culprit in CULPRITS.items():
        if culprit_can_access(storage, culprit) and clue_matches(clue, culprit):
            out.append(cid)
    return sorted(out)


def solved_culprit(storage: Storage, clue: Clue) -> Optional[str]:
    cands = candidate_culprits(storage, clue)
    if len(cands) == 1:
        return cands[0]
    return None


def explain_rejection(storage: Storage, clue: Clue) -> str:
    cands = candidate_culprits(storage, clue)
    if not cands:
        return (
            f"(No story: {clue.phrase} does not fit any thief who could reach "
            f"{storage.phrase}. The mystery would have no believable answer.)"
        )
    return (
        f"(No story: {clue.phrase} near {storage.phrase} points to too many possible "
        f"thieves ({', '.join(cands)}). This world only tells mysteries with one clear answer.)"
    )


def predict_solution(storage: Storage, clue: Clue) -> dict:
    cands = candidate_culprits(storage, clue)
    return {
        "candidates": cands,
        "solved": len(cands) == 1,
        "culprit": cands[0] if len(cands) == 1 else "",
    }


def introduce(world: World, seeker: Entity, accused: Entity, elder: Entity, storage: Storage) -> None:
    world.say(
        f"In {world.setting.village}, where evening bread smelled warm before the sun went down, "
        f"{seeker.id} and {accused.id} helped {elder.label_word} in the kitchen. "
        f"{world.setting.kitchen_detail}"
    )
    world.say(
        f"On {storage.phrase} stood a blue porcelain plate, and on the plate lay neat red rounds of pepperoni "
        f"for the village loaf."
    )


def charge_guard(world: World, elder: Entity, seeker: Entity, accused: Entity) -> None:
    seeker.memes["duty"] += 1
    accused.memes["duty"] += 1
    world.say(
        f'"Watch the plate while I knead the dough," said {elder.label_word}. '
        f'"A good loaf is built by patient hands."'
    )
    world.say(
        f"{seeker.id} stood a little straighter, and {accused.id} nodded, though the pepperoni smelled so savory "
        f"that both children swallowed once."
    )


def theft(world: World, culprit: Culprit, storage: Storage, clue: Clue) -> None:
    plate = world.get("plate")
    plate.meters["missing_food"] += 1
    world.facts["pepperoni_missing"] = True
    world.say(
        f"But while the dough was turned and folded, something quick and hungry came by. "
        f"{culprit.carry_line} From the blue porcelain plate, several pepperoni rounds vanished."
    )
    world.say(clue.line)


def accuse(world: World, seeker: Entity, accused: Entity) -> None:
    seeker.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {seeker.id} saw the thinned plate, surprise leapt into the wrong shape. "
        f'"You took it!" {seeker.pronoun()} cried to {accused.id}.'
    )
    if accused.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{accused.id} drew back with hot cheeks. "I did not," {accused.pronoun()} said. '
            f'The room felt smaller all at once.'
        )


def elder_stays_calm(world: World, elder: Entity, clue: Clue) -> None:
    world.say(
        f"{elder.label_word.capitalize()} did not scold either child. "
        f'{elder.pronoun("subject").capitalize()} only said, "{ELDER_STYLES[world.facts["elder_style"]].gentle_line}"'
    )
    world.say(
        f'"A true answer leaves traces," {elder.pronoun()} added. '
        f'"Look with your eyes before you speak with your anger."'
    )
    world.facts["featured_clue"] = clue.label


def search(world: World, seeker: Entity, accused: Entity, storage: Storage, clue: Clue) -> None:
    seeker.memes["curiosity"] += 1
    accused.memes["curiosity"] += 1
    seeker.memes["noticed_clue"] += 1
    world.say(
        f"So the two children bent close to {storage.lookup_line}. There they found {clue.phrase}."
    )
    world.say(
        f"{accused.id} pointed first, and {seeker.id} stared hard. The mystery turned from a quarrel into a puzzle."
    )


def realize(world: World, seeker: Entity, storage: Storage, clue: Clue, culprit: Culprit) -> None:
    pred = predict_solution(storage, clue)
    seeker.memes["reasoned"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_candidates"] = pred["candidates"]
    world.facts["predicted_culprit"] = pred["culprit"]
    if storage.height == "high":
        place_line = f"Only something that could reach so high could have stolen from {storage.phrase}"
    else:
        place_line = f"Only something that could nose or pad up to {storage.phrase} could have stolen from it"
    world.say(
        f"Then a bright little epiphany came to {seeker.id}. {place_line}, and {clue.phrase} belonged to no child at all."
    )
    if seeker.memes["epiphany"] >= THRESHOLD:
        world.say(
            f'"It was {culprit.phrase}!" {seeker.id} said. "I blamed {accused.id}, but the clue was telling the true story."'
        )


def follow_trail(world: World, seeker: Entity, accused: Entity, culprit: Culprit) -> None:
    seeker.meters["steps_taken"] += 1
    accused.meters["steps_taken"] += 1
    world.say(
        f"Out they went past the oven door and into the lane. {world.setting.outside_detail}"
    )
    world.say(culprit.trail_line)


def recover(world: World, seeker: Entity, accused: Entity, culprit: Culprit) -> None:
    plate = world.get("plate")
    plate.meters["found_again"] += 1
    world.say(
        f"There, by {culprit.hiding_place}, they found {culprit.phrase} worrying the stolen pepperoni."
    )
    world.say(
        f"{accused.id} clapped once, and {seeker.id} shooed the thief away with a kitchen towel. "
        f"Not every slice could be saved, but enough good pieces remained for the loaf."
    )


def apology(world: World, seeker: Entity, accused: Entity, elder: Entity) -> None:
    seeker.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{seeker.id} turned to {accused.id} and bowed {seeker.pronoun('possessive')} head. "
        f'"I was wrong to blame you," {seeker.pronoun()} said. "My mouth ran faster than my thoughts."'
    )
    world.say(
        f'{accused.id} let out the breath {accused.pronoun()} had been holding. '
        f'"Next time we will solve it together," {accused.pronoun()} answered.'
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled and said, "{ELDER_STYLES[world.facts["elder_style"]].wisdom_line}"'
    )


def ending(world: World, seeker: Entity, accused: Entity, elder: Entity) -> None:
    seeker.memes["joy"] += 1
    accused.memes["joy"] += 1
    world.say(
        f"By dusk the loaf came from the oven brown and shining. The rescued pepperoni rested on top, and the blue porcelain "
        f"plate sat empty beside it like a witness that had told the truth."
    )
    world.say(
        f"{seeker.id} and {accused.id} carried the bread out together, no longer sharp with blame, and {world.setting.closing_image}"
    )


def tell(
    setting: Setting,
    storage: Storage,
    clue: Clue,
    culprit: Culprit,
    elder_style: ElderStyle,
    seeker_name: str = "Mira",
    seeker_gender: str = "girl",
    accused_name: str = "Tobin",
    accused_gender: str = "boy",
) -> World:
    world = World(setting)
    seeker = world.add(Entity(id="seeker", kind="character", type=seeker_gender, label=seeker_name, role="seeker"))
    accused = world.add(Entity(id="accused", kind="character", type=accused_gender, label=accused_name, role="accused"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_style.type, label=elder_style.type, role="elder"))
    plate = world.add(Entity(id="plate", kind="thing", type="plate", label="plate", phrase="a blue porcelain plate"))
    thief = world.add(Entity(id="thief", kind="animal", type=culprit.kind, label=culprit.label, phrase=culprit.phrase))

    seeker.memes["trust"] = 1.0
    accused.memes["trust"] = 1.0

    world.facts["storage"] = storage
    world.facts["clue"] = clue
    world.facts["culprit_cfg"] = culprit
    world.facts["elder_style"] = elder_style.id
    world.facts["setting"] = setting
    world.facts["seeker_name"] = seeker_name
    world.facts["accused_name"] = accused_name
    world.facts["elder"] = elder
    world.facts["seeker"] = seeker
    world.facts["accused"] = accused
    world.facts["plate"] = plate
    world.facts["thief"] = thief

    introduce(world, seeker, accused, elder, storage)
    charge_guard(world, elder, seeker, accused)

    world.para()
    theft(world, culprit, storage, clue)
    accuse(world, seeker, accused)
    elder_stays_calm(world, elder, clue)

    world.para()
    search(world, seeker, accused, storage, clue)
    realize(world, seeker, storage, clue, culprit)
    follow_trail(world, seeker, accused, culprit)
    recover(world, seeker, accused, culprit)

    world.para()
    apology(world, seeker, accused, elder)
    ending(world, seeker, accused, elder)

    world.facts["solved"] = True
    world.facts["conflict_happened"] = True
    world.facts["repaired"] = seeker.memes["trust"] > 1 and accused.memes["trust"] > 1
    return world


SETTINGS = {
    "willow_hollow": Setting(
        id="willow_hollow",
        village="Willow Hollow",
        kitchen_detail="Copper pans glimmered on the wall, and flour dust floated like pale mist in the last light.",
        outside_detail="Swallows dipped over the well, and the lane still held the day's warmth.",
        closing_image="the first star looked down on Willow Hollow as if even the sky approved of peace.",
        tags={"village", "bread"},
    ),
    "stonebridge": Setting(
        id="stonebridge",
        village="Stonebridge",
        kitchen_detail="Bundles of herbs hung from the beams, and the table smelled of rosemary and warm yeast.",
        outside_detail="The old bridge cast a long shadow, and the river muttered over its stones.",
        closing_image="the bread steam curled into the cool evening while the bridge bells gave one soft ring.",
        tags={"village", "river"},
    ),
    "sunmeadow": Setting(
        id="sunmeadow",
        village="Sunmeadow",
        kitchen_detail="The open window carried in clover scent, and the hearth made the room glow honey-gold.",
        outside_detail="Chickens scratched in the dust, and the meadows beyond the fence were turning silver with dusk.",
        closing_image="the meadow crickets began their song while the children tore the loaf and laughed again.",
        tags={"village", "meadow"},
    ),
}

STORAGES = {
    "table": Storage(
        id="table",
        label="table",
        phrase="the low kneading table",
        height="low",
        open_air=False,
        lookup_line="the flour-dusted edge of the low kneading table",
        tags={"table"},
    ),
    "shelf": Storage(
        id="shelf",
        label="shelf",
        phrase="the high pantry shelf",
        height="high",
        open_air=False,
        lookup_line="the narrow board of the high pantry shelf",
        tags={"shelf"},
    ),
    "window": Storage(
        id="window",
        label="window",
        phrase="the open windowsill",
        height="high",
        open_air=True,
        lookup_line="the bright open windowsill",
        tags={"window"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="pawprints",
        phrase="little greasy pawprints",
        line="A few little greasy pawprints marked the place where the slices had been.",
        indicates={"dog", "cat"},
        tags={"tracks"},
    ),
    "feather": Clue(
        id="feather",
        label="feather",
        phrase="a black feather with a red grease stain",
        line="Beside the plate lay a black feather with a red grease stain at its tip.",
        indicates={"crow"},
        tags={"feather"},
    ),
    "flowerpot": Clue(
        id="flowerpot",
        label="tilted flowerpot",
        phrase="a tipped flowerpot and a gray whisker",
        line="The basil pot nearby had been tipped askew, and one gray whisker clung to the rim.",
        indicates={"cat"},
        tags={"whisker"},
    ),
    "nosemark": Clue(
        id="nosemark",
        label="nose mark",
        phrase="a round damp nose mark in the flour",
        line="Across the flour ran a round damp nose mark, as if someone had sniffed the plate before stealing.",
        indicates={"dog"},
        tags={"nose"},
    ),
}

CULPRITS = {
    "dog": Culprit(
        id="dog",
        label="dog",
        phrase="the baker's little dog",
        kind="dog",
        can_reach={"low"},
        needs_open_air=False,
        hiding_place="the woodpile",
        carry_line="The baker's little dog padded in with a wagging tail and snatched what it could carry",
        trail_line="A faint red trail led toward the woodpile, where a tail gave one guilty thump against a log.",
        tags={"dog"},
    ),
    "cat": Culprit(
        id="cat",
        label="cat",
        phrase="the miller's gray cat",
        kind="cat",
        can_reach={"low", "high"},
        needs_open_air=False,
        hiding_place="the warm stone by the herb pots",
        carry_line="The miller's gray cat leapt lightly where it pleased and hooked away a prize between quick paws",
        trail_line="Near the herb pots a gray tail slipped around a warm stone, and the smell of pepperoni hung in the air.",
        tags={"cat"},
    ),
    "crow": Culprit(
        id="crow",
        label="crow",
        phrase="a glossy crow",
        kind="bird",
        can_reach={"high"},
        needs_open_air=True,
        hiding_place="the rain barrel",
        carry_line="A glossy crow darted through the open air, snatched a slice, and came back bold enough for more",
        trail_line="Up by the rain barrel a sharp caw broke the quiet, and something black hopped with great satisfaction.",
        tags={"crow"},
    ),
}

ELDER_STYLES = {
    "grandmother": ElderStyle(
        id="grandmother",
        type="grandmother",
        gentle_line="No one mends a mystery by tearing a friend.",
        wisdom_line="The tongue should wait for the eyes, and the heart should wait for the truth.",
    ),
    "grandfather": ElderStyle(
        id="grandfather",
        type="grandfather",
        gentle_line="A hot guess is a poor lantern for a dark question.",
        wisdom_line="When you follow signs instead of temper, even a quarrel can find its way home.",
    ),
}


@dataclass
class StoryParams:
    setting: str
    storage: str
    clue: str
    culprit: str
    elder: str
    seeker_name: str
    seeker_gender: str
    accused_name: str
    accused_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="willow_hollow",
        storage="shelf",
        clue="pawprints",
        culprit="cat",
        elder="grandmother",
        seeker_name="Mira",
        seeker_gender="girl",
        accused_name="Tobin",
        accused_gender="boy",
    ),
    StoryParams(
        setting="stonebridge",
        storage="window",
        clue="feather",
        culprit="crow",
        elder="grandfather",
        seeker_name="Anya",
        seeker_gender="girl",
        accused_name="Bram",
        accused_gender="boy",
    ),
    StoryParams(
        setting="sunmeadow",
        storage="table",
        clue="nosemark",
        culprit="dog",
        elder="grandmother",
        seeker_name="Luka",
        seeker_gender="boy",
        accused_name="Mira",
        accused_gender="girl",
    ),
    StoryParams(
        setting="sunmeadow",
        storage="window",
        clue="flowerpot",
        culprit="cat",
        elder="grandfather",
        seeker_name="Nella",
        seeker_gender="girl",
        accused_name="Pavel",
        accused_gender="boy",
    ),
]

GIRL_NAMES = ["Mira", "Anya", "Nella", "Rosa", "Elka", "Talia", "Lina", "Veda"]
BOY_NAMES = ["Tobin", "Bram", "Luka", "Pavel", "Ivo", "Soren", "Milo", "Jori"]


KNOWLEDGE = {
    "pepperoni": [
        (
            "What is pepperoni?",
            "Pepperoni is a spicy sausage usually cut into little round slices. People often put it on bread or pizza for flavor."
        )
    ],
    "porcelain": [
        (
            "What is porcelain?",
            "Porcelain is a smooth, hard kind of clay that is baked until it becomes strong. Many cups and plates are made from it."
        )
    ],
    "tracks": [
        (
            "What can pawprints tell you?",
            "Pawprints can show that an animal walked through a place. If you look closely, they can help you guess what sort of animal was there."
        )
    ],
    "feather": [
        (
            "Why is a feather a useful clue?",
            "A feather can show that a bird has been nearby. If it is found beside missing food, it may point to a bird thief."
        )
    ],
    "whisker": [
        (
            "What does a whisker tell you?",
            "A whisker can be a clue that a cat or another furry animal brushed past something. Small things left behind can solve a big mystery."
        )
    ],
    "nose": [
        (
            "What can a nose mark in flour mean?",
            "A nose mark in flour can mean an animal sniffed there. Dogs often lead with their noses when they hunt for food."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery fairly?",
            "You look for clues first and make your guess after that. Fair thinking is slower than blaming, but it leads you closer to the truth."
        )
    ],
    "conflict": [
        (
            "What should you do after blaming someone unfairly?",
            "You should say you were sorry and tell the truth about your mistake. An honest apology helps mend hurt feelings."
        )
    ],
    "epiphany": [
        (
            "What is an epiphany?",
            "An epiphany is a sudden clear understanding. It is the moment when a confusing thing suddenly makes sense."
        )
    ],
    "crow": [
        (
            "Why might a crow steal food?",
            "Crows are clever birds and often grab easy food when they see it. They are quick and bold, especially near open windows."
        )
    ],
    "cat": [
        (
            "Why are cats good at reaching high places?",
            "Cats are nimble and can jump onto shelves and walls. That makes them good climbers and sneaky snack thieves."
        )
    ],
    "dog": [
        (
            "Why do dogs follow food smells?",
            "Dogs have very strong noses and notice food quickly. A good smell can lead them right to a tasty treat."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "pepperoni",
    "porcelain",
    "mystery",
    "conflict",
    "epiphany",
    "tracks",
    "feather",
    "whisker",
    "nose",
    "crow",
    "cat",
    "dog",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    accused = f["accused"]
    setting = f["setting"]
    storage = f["storage"]
    clue = f["clue"]
    return [
        (
            'Write a folk-tale style story for a 3-to-5-year-old that includes the words '
            '"pepperoni", "epiphany", and "porcelain", and centers on a child-sized mystery.'
        ),
        (
            f"Tell a gentle conflict story set in {setting.village} where {seeker.label} wrongly blames "
            f"{accused.label} after pepperoni vanishes from a porcelain plate on {storage.phrase}, and a clue "
            f"helps them solve the mystery."
        ),
        (
            f"Write a simple village tale where {clue.phrase} turns a quarrel into understanding, and end with "
            f"bread shared in peace."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    accused = f["accused"]
    elder = f["elder"]
    storage = f["storage"]
    clue = f["clue"]
    culprit = f["culprit_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.label} and {accused.label}, two children helping {elder.label_word} in the village kitchen. "
            f"The trouble begins when pepperoni goes missing from a blue porcelain plate."
        ),
        (
            "What was the mystery to solve?",
            f"The mystery was who stole the pepperoni from the porcelain plate on {storage.phrase}. "
            f"The children had to look for signs instead of trusting the first angry guess."
        ),
        (
            f"Why did {seeker.label} and {accused.label} begin to argue?",
            f"{seeker.label} saw that several pepperoni slices were gone and blamed {accused.label} too quickly. "
            f"That unfair guess hurt {accused.label}'s feelings and turned surprise into conflict."
        ),
        (
            "What clue helped solve the mystery?",
            f"They found {clue.phrase}. That clue mattered because it pointed toward the real thief instead of either child."
        ),
        (
            "What was the epiphany in the story?",
            f"The epiphany came when {seeker.label} understood that the clue and the place of the plate fit only {culprit.phrase}. "
            f"That sudden understanding changed the story from blaming into solving."
        ),
        (
            "Who really took the pepperoni, and how did the children know?",
            f"{culprit.phrase.capitalize()} took it. The clue matched that thief, and {storage.phrase} was a place that thief could reach while the wrong person could not."
        ),
        (
            "How was the conflict fixed?",
            f"{seeker.label} apologized for blaming {accused.label}. After the truth was known, the children worked together and their sharp feelings softened into trust."
        ),
        (
            "How did the story end?",
            f"It ended with the bread baked and shared in peace. The empty blue porcelain plate beside the loaf showed that the mystery had been solved and the quarrel had changed."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pepperoni", "porcelain", "mystery", "conflict", "epiphany"}
    tags |= set(f["clue"].tags)
    tags |= set(f["culprit_cfg"].tags)
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for storage_id, storage in STORAGES.items():
        for clue_id, clue in CLUES.items():
            solved = solved_culprit(storage, clue)
            if solved:
                combos.append((storage_id, clue_id, solved))
    return sorted(combos)


ASP_RULES = r"""
candidate(S, Cl, Cu) :- storage(S), clue(Cl), culprit(Cu),
                        reaches(Cu, H), height(S, H),
                        clue_points(Cl, Cu),
                        not requires_open(Cu).
candidate(S, Cl, Cu) :- storage(S), clue(Cl), culprit(Cu),
                        reaches(Cu, H), height(S, H),
                        clue_points(Cl, Cu),
                        requires_open(Cu), open_air(S).

other_candidate(S, Cl, Cu) :- candidate(S, Cl, Other), candidate(S, Cl, Cu), Other != Cu.
unique_solution(S, Cl, Cu) :- candidate(S, Cl, Cu), not other_candidate(S, Cl, Cu).
valid(S, Cl, Cu) :- unique_solution(S, Cl, Cu).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, storage in STORAGES.items():
        lines.append(asp.fact("storage", sid))
        lines.append(asp.fact("height", sid, storage.height))
        if storage.open_air:
            lines.append(asp.fact("open_air", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for culprit_id in sorted(clue.indicates):
            lines.append(asp.fact("clue_points", cid, culprit_id))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for reach in sorted(culprit.can_reach):
            lines.append(asp.fact("reaches", cid, reach))
        if culprit.needs_open_air:
            lines.append(asp.fact("requires_open", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if a - p:
            print("  only in ASP:", sorted(a - p))
        if p - a:
            print("  only in Python:", sorted(p - a))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale mystery story world: a vanished snack, a wrong accusation, and a clue-led epiphany."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--elder", choices=ELDER_STYLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.storage and args.clue:
        storage = STORAGES[args.storage]
        clue = CLUES[args.clue]
        solved = solved_culprit(storage, clue)
        if not solved:
            raise StoryError(explain_rejection(storage, clue))
        if args.culprit and args.culprit != solved:
            raise StoryError(
                f"(No story: with {storage.phrase} and {clue.phrase}, the only believable culprit is {solved}, not {args.culprit}.)"
            )
    if args.culprit and not args.storage and not args.clue:
        possible = [triple for triple in valid_combos() if triple[2] == args.culprit]
        if not possible:
            raise StoryError(f"(No story: no valid clue/storage pair leads to culprit '{args.culprit}'.)")

    combos = [
        combo for combo in valid_combos()
        if (args.storage is None or combo[0] == args.storage)
        and (args.clue is None or combo[1] == args.clue)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    storage_id, clue_id, culprit_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    elder_id = args.elder or rng.choice(sorted(ELDER_STYLES))
    seeker_gender = rng.choice(["girl", "boy"])
    accused_gender = rng.choice(["girl", "boy"])
    seeker_name = _pick_name(rng, seeker_gender)
    accused_name = _pick_name(rng, accused_gender, avoid=seeker_name)

    return StoryParams(
        setting=setting_id,
        storage=storage_id,
        clue=clue_id,
        culprit=culprit_id,
        elder=elder_id,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        accused_name=accused_name,
        accused_gender=accused_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.storage not in STORAGES:
        raise StoryError(f"(Unknown storage: {params.storage})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.elder not in ELDER_STYLES:
        raise StoryError(f"(Unknown elder style: {params.elder})")

    solved = solved_culprit(STORAGES[params.storage], CLUES[params.clue])
    if solved != params.culprit:
        raise StoryError(
            f"(Invalid story: {params.clue} at {params.storage} solves to {solved!r}, not {params.culprit!r}.)"
        )

    world = tell(
        setting=SETTINGS[params.setting],
        storage=STORAGES[params.storage],
        clue=CLUES[params.clue],
        culprit=CULPRITS[params.culprit],
        elder_style=ELDER_STYLES[params.elder],
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        accused_name=params.accused_name,
        accused_gender=params.accused_gender,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (storage, clue, culprit) combos:\n")
        for storage, clue, culprit in combos:
            print(f"  {storage:8} {clue:11} {culprit}")
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
            header = f"### {p.setting}: {p.clue} at {p.storage} -> {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
