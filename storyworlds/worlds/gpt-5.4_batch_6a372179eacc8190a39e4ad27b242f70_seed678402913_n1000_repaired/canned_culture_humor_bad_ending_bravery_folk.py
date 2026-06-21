#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py
==============================================================================

A small folk-tale-flavored story world about a brave, foolish child who tries to
fetch canned food for a village culture feast from a high shelf using an unsafe
perch. The attempt is bold, funny, and doomed: the can bursts, the village
animal joins the trouble, and the ending stays bad enough to matter.

The world model prefers narrow, plausible variants over broad coverage:
a story only exists when the chosen canned food is heavy enough, or the perch is
rickety enough, that a spill is genuinely likely. Safe combinations are refused,
because then the tale would lose its brave-fool turn and bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py
    python storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py --canned peaches --perch stool
    python storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py --canned peas --perch steps
    python storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py --all
    python storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/canned_culture_humor_bad_ending_bravery_folk.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
RISK_LIMIT = 2
CHASE_LIMIT = 2


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
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Festival:
    id: str
    name: str
    square: str
    dish: str
    music: str
    closing: str
    tags: set[str] = field(default_factory=lambda: {"culture"})


@dataclass
class CannedFood:
    id: str
    label: str
    phrase: str
    weight: int
    burst: str
    dish_use: str
    smell: str
    tags: set[str] = field(default_factory=lambda: {"canned"})


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    rickety: int
    wobble_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    label: str
    phrase: str
    greed: int
    chase_text: str
    nibble_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    clang: int
    brag_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    perch = world.get("perch")
    hero = world.get("hero")
    if hero.meters["climbing"] < THRESHOLD:
        return []
    if perch.meters["risk"] <= RISK_LIMIT:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    perch.meters["wobble"] += 1
    hero.memes["alarm"] += 1
    return ["__wobble__"]


def _r_burst(world: World) -> list[str]:
    perch = world.get("perch")
    can = world.get("can")
    hero = world.get("hero")
    if perch.meters["wobble"] < THRESHOLD:
        return []
    sig = ("burst",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    can.meters["burst"] += 1
    can.meters["lost"] += 1
    hero.meters["sticky"] += 1
    hero.memes["shame"] += 1
    hero.memes["regret"] += 1
    return ["__burst__"]


def _r_animal(world: World) -> list[str]:
    can = world.get("can")
    animal = world.get("animal")
    hero = world.get("hero")
    if can.meters["burst"] < THRESHOLD:
        return []
    sig = ("animal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts["animal_event"] == "chased":
        animal.meters["chasing"] += 1
        hero.memes["panic"] += 1
    else:
        animal.meters["eating"] += 1
        hero.memes["shame"] += 1
    return ["__animal__"]


CAUSAL_RULES = [
    Rule(name="wobble", apply=_r_wobble),
    Rule(name="burst", apply=_r_burst),
    Rule(name="animal", apply=_r_animal),
]


def propagate(world: World) -> list[str]:
    markers: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                markers.extend(out)
    return markers


def spill_risk(canned: CannedFood, perch: Perch) -> int:
    return canned.weight + perch.rickety


def unsafe_combo(canned: CannedFood, perch: Perch) -> bool:
    return spill_risk(canned, perch) > RISK_LIMIT


def animal_event_of(animal: Animal, tool: Tool) -> str:
    return "chased" if animal.greed + tool.clang > CHASE_LIMIT else "nibbled"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for festival_id in FESTIVALS:
        for canned_id, canned in CANNED.items():
            for perch_id, perch in PERCHES.items():
                if unsafe_combo(canned, perch):
                    combos.append((festival_id, canned_id, perch_id))
    return combos


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    perch = sim.get("perch")
    hero.meters["climbing"] += 1
    perch.meters["risk"] = float(world.facts["risk"])
    propagate(sim)
    return {
        "wobble": perch.meters["wobble"] >= THRESHOLD,
        "burst": sim.get("can").meters["burst"] >= THRESHOLD,
    }


def tale_opening(world: World, festival: Festival, hero: Entity, friend: Entity, elder: Entity, canned: CannedFood) -> None:
    hero.memes["pride"] += 1
    friend.memes["care"] += 1
    world.say(
        f"In the days when every hill kept its own songs, the people of the village gathered for {festival.name} in {festival.square}. "
        f"There were fiddles, clapping hands, and the old {festival.music} that everybody called part of the village culture."
    )
    world.say(
        f"{elder.label_word.capitalize()} had promised to finish {festival.dish} with {canned.phrase}. "
        f"The shining can waited on the highest pantry shelf, too high for easy hands."
    )
    world.say(
        f'{hero.id}, who liked brave ideas better than slow ones, tapped {tool_phrase(world)} and said, '
        f'"Leave it to me. I will fetch the canned treasure before the next drumbeat."'
    )


def tool_phrase(world: World) -> str:
    return world.facts["tool"].phrase


def warning(world: World, hero: Entity, friend: Entity, perch: Perch, animal: Animal) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_burst"] = pred["burst"]
    extra = ""
    if pred["burst"]:
        extra = " If the can slips, supper will splash instead of simmer."
    world.say(
        f'{friend.id} looked at {perch.phrase} and then at {animal.phrase}. '
        f'"That {perch.label} was born crooked," {friend.pronoun()} warned. '
        f'"And {animal.label} has a nose for trouble.{extra}"'
    )


def boasting(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["bravery"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} only grinned wider. {tool.brag_text} "
        f"{hero.pronoun().capitalize()} climbed toward the shelf as if foolishness were a kind of crown."
    )


def climb(world: World, hero: Entity, perch_ent: Entity, canned: CannedFood, perch: Perch) -> None:
    hero.meters["climbing"] += 1
    perch_ent.meters["risk"] = float(spill_risk(canned, perch))
    markers = propagate(world)
    if "__wobble__" in markers:
        world.say(
            f"The {perch.label} answered first. {perch.wobble_text}"
        )
    if "__burst__" in markers:
        world.say(
            f"Then came the louder answer: {canned.burst} "
            f"{hero.id} landed with sticky sleeves, a shining face, and no dignity at all."
        )


def animal_mischief(world: World, hero: Entity, animal: Animal, canned: CannedFood) -> None:
    if world.facts["animal_event"] == "chased":
        world.say(
            f"{animal.chase_text} "
            f"{hero.id} ran three circles through the square while children laughed and the fiddler never missed a note."
        )
    else:
        world.say(
            f"{animal.nibble_text} "
            f"{hero.id} could only stare while the lost {canned.label} was pecked and licked right off the floorboards."
        )


def elder_judgment(world: World, elder: Entity, hero: Entity, festival: Festival, canned: CannedFood) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'{elder.label_word.capitalize()} wiped a drop of {canned.smell} from {hero.id}\'s nose and said, '
        f'"A brave heart is good, child, but it needs wise feet under it. Now our {festival.dish} must go to the tables without {canned.dish_use}."'
    )


def bad_ending(world: World, hero: Entity, festival: Festival, canned: CannedFood) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"When evening settled, the dancers stamped to {festival.closing}, but {hero.id} stood by the pump, washing {canned.smell} from {hero.pronoun('possessive')} cuffs."
    )
    world.say(
        f"The feast was served plain, and though nobody was cruel, everybody remembered who had tried to help too boldly. "
        f"That is why old people in the village still say that bravery without sense can leave a table hungry."
    )


FESTIVALS = {
    "lantern": Festival(
        id="lantern",
        name="the Lantern Culture Night",
        square="the stone square",
        dish="sweet rice with honey",
        music="lantern tune",
        closing="the lantern-song",
    ),
    "river": Festival(
        id="river",
        name="the River Culture Supper",
        square="the willow yard by the ford",
        dish="thick river porridge",
        music="reed-pipe tune",
        closing="the splash-step dance",
    ),
    "harvest": Festival(
        id="harvest",
        name="the Harvest Culture Feast",
        square="the threshing yard",
        dish="warm oat cakes",
        music="drum and fiddle tune",
        closing="the threshing reel",
    ),
}

CANNED = {
    "peaches": CannedFood(
        id="peaches",
        label="canned peaches",
        phrase="a heavy can of peaches",
        weight=2,
        burst="the can popped open and golden syrup flew in a shining arc across the room.",
        dish_use="sweet peaches on top",
        smell="peach syrup",
    ),
    "beets": CannedFood(
        id="beets",
        label="canned beets",
        phrase="a stout can of beets",
        weight=2,
        burst="the can split, and purple beet juice painted the boards and boots like a prank from a vineyard sprite.",
        dish_use="its red slices",
        smell="beet brine",
    ),
    "peas": CannedFood(
        id="peas",
        label="canned peas",
        phrase="a light can of peas",
        weight=1,
        burst="the peas scattered with a soft drumming sound, rolling into every crack as if they had grown tiny legs.",
        dish_use="its green spoonfuls",
        smell="pea water",
    ),
}

PERCHES = {
    "stool": Perch(
        id="stool",
        label="stool",
        phrase="the three-legged stool by the pantry door",
        rickety=1,
        wobble_text="It danced once to the left, once to the right, and then shook like a goat trying to remember a song.",
        tags={"stool"},
    ),
    "ladder": Perch(
        id="ladder",
        label="ladder",
        phrase="the old ladder with a loose rung",
        rickety=1,
        wobble_text="The ladder hummed, coughed, and wagged its top like a scolding finger.",
        tags={"ladder"},
    ),
    "barrel": Perch(
        id="barrel",
        label="barrel stack",
        phrase="two flour barrels with a board across them",
        rickety=2,
        wobble_text="The barrel stack rolled under {hero}, first like a slow cart and then like a joke told too far.".replace("{hero}", "the child"),
        tags={"barrel"},
    ),
    "steps": Perch(
        id="steps",
        label="granary steps",
        phrase="the broad granary steps",
        rickety=0,
        wobble_text="Nothing much happened at all.",
        tags={"steps"},
    ),
}

ANIMALS = {
    "goose": Animal(
        id="goose",
        label="the market goose",
        phrase="the market goose with bright, suspicious eyes",
        greed=2,
        chase_text="The goose cried victory, stretched its neck, and charged after the shining mess.",
        nibble_text="The goose waddled in with priestly calm and began to sample the spill.",
        tags={"goose"},
    ),
    "goat": Animal(
        id="goat",
        label="the bell-goat",
        phrase="the bell-goat from the mill yard",
        greed=1,
        chase_text="The goat clattered in, beard first, and gave chase as if the whole square belonged to him.",
        nibble_text="The goat arrived with solemn chewing and adopted the spill as its private supper.",
        tags={"goat"},
    ),
    "pig": Animal(
        id="pig",
        label="the pink pig",
        phrase="the pink pig from the back pen",
        greed=1,
        chase_text="The pig squealed and hustled after the smell with comic seriousness.",
        nibble_text="The pig snuffled happily and hoovered up what the can had surrendered.",
        tags={"pig"},
    ),
}

TOOLS = {
    "pot_helmet": Tool(
        id="pot_helmet",
        label="pot helmet",
        phrase="a dented pot on his head",
        clang=1,
        brag_text="With a dented pot on his head like a hero's helmet,",
        tags={"pot"},
    ),
    "ladle_sword": Tool(
        id="ladle_sword",
        label="ladle sword",
        phrase="a long soup ladle like a sword",
        clang=1,
        brag_text="Swinging a soup ladle as if it were a silver sword,",
        tags={"ladle"},
    ),
    "blanket_cape": Tool(
        id="blanket_cape",
        label="blanket cape",
        phrase="a blanket tied around his shoulders",
        clang=0,
        brag_text="Wrapped in a blanket cape that dragged behind him like a proud cloud,",
        tags={"blanket"},
    ),
}

ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["bold", "boastful", "fearless", "reckless"]
GIRL_NAMES = ["Mira", "Tala", "Nina", "Pia", "Rosa", "Lena"]
BOY_NAMES = ["Niko", "Pavel", "Toma", "Ivo", "Milan", "Jori"]


@dataclass
class StoryParams:
    festival: str
    canned: str
    perch: str
    animal: str
    tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def tell(
    festival: Festival,
    canned: CannedFood,
    perch: Perch,
    animal: Animal,
    tool: Tool,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, traits=[trait], role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, traits=["careful"], role="friend"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    can = world.add(Entity(id="can", type="can", label=canned.label, phrase=canned.phrase, tags=set(canned.tags)))
    perch_ent = world.add(Entity(id="perch", type="perch", label=perch.label, phrase=perch.phrase, tags=set(perch.tags)))
    animal_ent = world.add(Entity(id="animal", type="animal", label=animal.label, phrase=animal.phrase, tags=set(animal.tags)))
    hero.attrs["display"] = hero_name
    friend.attrs["display"] = friend_name

    world.facts.update(
        festival=festival,
        canned=canned,
        perch_cfg=perch,
        animal=animal,
        tool=tool,
        hero=hero,
        friend=friend,
        elder=elder,
        can=can,
        perch=perch_ent,
        animal_ent=animal_ent,
        risk=spill_risk(canned, perch),
        animal_event=animal_event_of(animal, tool),
        outcome="bad",
    )

    tale_opening(world, festival, hero, friend, elder, canned)
    warning(world, hero, friend, perch, animal)

    world.para()
    boasting(world, hero, tool)
    climb(world, hero, perch_ent, canned, perch)
    animal_mischief(world, hero, animal, canned)

    world.para()
    elder_judgment(world, elder, hero, festival, canned)
    bad_ending(world, hero, festival, canned)
    return world


KNOWLEDGE = {
    "canned": [
        (
            "What does canned food mean?",
            "Canned food is food sealed inside a metal can so it can keep for a long time. The can must be opened before the food can be eaten."
        )
    ],
    "culture": [
        (
            "What can culture mean in a village story?",
            "Culture can mean the songs, dances, food, and customs people share together. In a folk tale, a culture feast shows what a village remembers and loves."
        )
    ],
    "ladder": [
        (
            "Why can an old ladder be dangerous?",
            "An old ladder can wobble or have a loose rung. If it shifts while someone climbs, they can fall or drop what they are carrying."
        )
    ],
    "stool": [
        (
            "Why is a wobbly stool not a good climbing tool?",
            "A wobbly stool does not stand steady under your feet. If it tips, you can spill things or get hurt."
        )
    ],
    "goose": [
        (
            "Why are geese funny and troublesome in stories?",
            "Geese can hiss, honk, and chase people in a very noisy way. That makes them useful for comic trouble in folk tales."
        )
    ],
    "bravery": [
        (
            "Is bravery always wise?",
            "No. Bravery is good when it is joined to good judgment, but brave foolishness can still cause a mess."
        )
    ],
}

KNOWLEDGE_ORDER = ["canned", "culture", "ladder", "stool", "goose", "bravery"]


def generation_prompts(world: World) -> list[str]:
    festival = world.facts["festival"]
    canned = world.facts["canned"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    tool = world.facts["tool"]
    perch = world.facts["perch_cfg"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that uses the words "canned" and "culture" and ends badly but safely.',
        f"Tell a humorous village story where {hero.attrs['display']} tries to fetch {canned.label} for {festival.name} by climbing {perch.phrase}, even after {friend.attrs['display']} warns against it.",
        f"Write a folk-style cautionary story in which a brave child wearing {tool.phrase} makes a funny mistake and learns that boldness without sense can spoil supper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    festival = world.facts["festival"]
    canned = world.facts["canned"]
    perch = world.facts["perch_cfg"]
    animal = world.facts["animal"]
    tool = world.facts["tool"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    hero_name = hero.attrs["display"]
    friend_name = friend.attrs["display"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a brave but foolish child, and {friend_name}, who tried to warn {hero.pronoun('object')}. It also includes {elder.label_word} and {animal.label} at the village feast."
        ),
        (
            f"Why did {hero_name} want the canned food?",
            f"{hero_name} wanted to fetch {canned.label} so {elder.label_word} could finish {festival.dish} for {festival.name}. That made the risky idea feel grand and important."
        ),
        (
            f"What warning did {friend_name} give?",
            f"{friend_name} warned that {perch.phrase} was not safe and that {animal.label} loved trouble. The warning mattered because the perch really was too rickety for the job."
        ),
        (
            f"Why was the climb a bad idea?",
            f"It was a bad idea because {canned.label} was too much for {perch.label}. In the world of the story, the risk was already high before {hero_name} even lifted a hand toward the shelf."
        ),
        (
            f"What happened when {hero_name} climbed up with {tool.phrase}?",
            f"The {perch.label} wobbled, the can burst, and {hero_name} ended up sticky and embarrassed. The brave act turned funny because the bold costume could not make the perch any steadier."
        ),
    ]
    if world.facts["animal_event"] == "chased":
        qa.append(
            (
                f"What did {animal.label} do after the can burst?",
                f"{animal.label.capitalize()} chased after the spill and sent {hero_name} running around the square. That made the mistake even more public and silly."
            )
        )
    else:
        qa.append(
            (
                f"What did {animal.label} do after the can burst?",
                f"{animal.label.capitalize()} calmly ate the spilled food from the floor. That made the ending worse, because the feast truly lost what it needed."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended badly: the feast had to be served without {canned.dish_use}, and {hero_name} spent the evening washing {canned.smell} from {hero.pronoun('possessive')} clothes. The final image shows that a foolish brave act can leave real trouble behind."
        )
    )
    qa.append(
        (
            f"What lesson did {elder.label_word} teach?",
            f"{elder.label_word.capitalize()} taught that bravery needs wisdom under it. A bold heart alone is not enough when a task asks for steady feet and common sense."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"canned", "culture", "bravery"}
    perch_tags = world.facts["perch_cfg"].tags
    animal_tags = world.facts["animal"].tags
    tags |= set(perch_tags) | set(animal_tags)
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  risk={world.facts.get('risk')}")
    lines.append(f"  animal_event={world.facts.get('animal_event')}")
    lines.append(f"  fired rules={sorted(name for (name, *_) in world.fired)}")
    return "\n".join(lines)


def explain_rejection(canned: CannedFood, perch: Perch) -> str:
    return (
        f"(No story: {canned.label} on {perch.phrase} is not risky enough for this world. "
        f"The brave-fool tale needs a real spill hazard, but risk={spill_risk(canned, perch)} "
        f"and it must be greater than {RISK_LIMIT}. Pick a heavier can or a shakier perch.)"
    )


def outcome_of(params: StoryParams) -> str:
    return animal_event_of(ANIMALS[params.animal], TOOLS[params.tool])


ASP_RULES = r"""
valid(Fest, Can, Perch) :-
    festival(Fest), canned(Can), perch(Perch),
    weight(Can, W), rickety(Perch, R), risk_limit(M),
    W + R > M.

chased :-
    chosen_animal(A), greed(A, G),
    chosen_tool(T), clang(T, C),
    chase_limit(M), G + C > M.

outcome(chased) :- chased.
outcome(nibbled) :- not chased.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fest_id in FESTIVALS:
        lines.append(asp.fact("festival", fest_id))
    for canned_id, canned in CANNED.items():
        lines.append(asp.fact("canned", canned_id))
        lines.append(asp.fact("weight", canned_id, canned.weight))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("rickety", perch_id, perch.rickety))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("greed", animal_id, animal.greed))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("clang", tool_id, tool.clang))
    lines.append(asp.fact("risk_limit", RISK_LIMIT))
    lines.append(asp.fact("chase_limit", CHASE_LIMIT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Folk-tale story world: a brave child, canned food, village culture, and a funny bad ending."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--canned", choices=CANNED)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.canned and args.perch:
        canned = CANNED[args.canned]
        perch = PERCHES[args.perch]
        if not unsafe_combo(canned, perch):
            raise StoryError(explain_rejection(canned, perch))

    combos = [
        combo
        for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.canned is None or combo[1] == args.canned)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, canned_id, perch_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    animal = args.animal or rng.choice(sorted(ANIMALS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        festival=festival_id,
        canned=canned_id,
        perch=perch_id,
        animal=animal,
        tool=tool,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        festival = FESTIVALS[params.festival]
        canned = CANNED[params.canned]
        perch = PERCHES[params.perch]
        animal = ANIMALS[params.animal]
        tool = TOOLS[params.tool]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]})") from exc

    if not unsafe_combo(canned, perch):
        raise StoryError(explain_rejection(canned, perch))

    world = tell(
        festival=festival,
        canned=canned,
        perch=perch,
        animal=animal,
        tool=tool,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        elder_type=params.elder,
        trait=params.trait,
    )

    story = world.render()
    if not story or "{" in story or "}" in story:
        raise StoryError("(Story rendering failed closed.)")

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


CURATED = [
    StoryParams(
        festival="lantern",
        canned="peaches",
        perch="stool",
        animal="goose",
        tool="pot_helmet",
        hero="Niko",
        hero_gender="boy",
        friend="Mira",
        friend_gender="girl",
        elder="grandmother",
        trait="boastful",
    ),
    StoryParams(
        festival="river",
        canned="beets",
        perch="ladder",
        animal="goat",
        tool="ladle_sword",
        hero="Tala",
        hero_gender="girl",
        friend="Ivo",
        friend_gender="boy",
        elder="uncle",
        trait="bold",
    ),
    StoryParams(
        festival="harvest",
        canned="peas",
        perch="barrel",
        animal="pig",
        tool="blanket_cape",
        hero="Pavel",
        hero_gender="boy",
        friend="Rosa",
        friend_gender="girl",
        elder="grandfather",
        trait="fearless",
    ),
    StoryParams(
        festival="lantern",
        canned="peas",
        perch="barrel",
        animal="goose",
        tool="ladle_sword",
        hero="Lena",
        hero_gender="girl",
        friend="Jori",
        friend_gender="boy",
        elder="aunt",
        trait="reckless",
    ),
]


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append((params, asp_outcome(params), outcome_of(params)))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model on {len(mismatches)} scenarios.")
        for params, a_out, p_out in mismatches[:5]:
            print(" ", params, a_out, p_out)

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Smoke test produced incomplete sample.)")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        _ = sample.to_json()
        print("OK: smoke test story generation and emit passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, canned, perch) combos:\n")
        for festival_id, canned_id, perch_id in combos:
            print(f"  {festival_id:8} {canned_id:8} {perch_id}")
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
            header = f"### {p.hero}: {p.canned} on {p.perch} at {p.festival}"
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
