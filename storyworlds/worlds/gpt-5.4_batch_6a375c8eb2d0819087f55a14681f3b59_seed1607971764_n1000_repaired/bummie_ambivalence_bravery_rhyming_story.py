#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py
======================================================================

A small storyworld about a child who must be brave enough to fetch Bummie, a
beloved soft comfort-cloth, from a slightly spooky place. The child feels
ambivalence first -- wanting to help, yet feeling a flutter of fear -- and then
uses the right aid to do the kind thing.

The prose is rendered in a gentle rhyming-story style, but the story is still
driven by simulated state: physical meters track distance, dampness, height,
and retrieval; emotional memes track worry, ambivalence, bravery, and relief.

Run it
------
    python storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py --place hedge_tunnel --aid lantern
    python storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py --place loft_shelf --aid boots
    python storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bummie_ambivalence_bravery_rhyming_story.py --verify
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
    approach: str
    hazard: str
    scare: int
    image: str
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
class Aid:
    id: str
    label: str
    phrase: str
    solves: str
    comfort: int
    use_line: str
    ending_line: str
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
class Trait:
    id: str
    label: str
    nerve: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
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


def _r_ambivalence(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["worry"] < THRESHOLD or hero.memes["care"] < THRESHOLD:
        return []
    sig = ("ambivalence",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["ambivalence"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    hero = world.get("hero")
    sibling = world.get("sibling")
    bummie = world.get("bummie")
    if bummie.meters["found"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    sibling.memes["relief"] += 1
    sibling.memes["sad"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="ambivalence", tag="emotion", apply=_r_ambivalence),
    Rule(name="relief", tag="emotion", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "hedge_tunnel": Place(
        id="hedge_tunnel",
        label="the hedge tunnel",
        approach="a little tunnel where the leaves made green shade",
        hazard="dark",
        scare=3,
        image="leafy walls held a pocket of night in the middle of day",
        tags={"dark", "garden"},
    ),
    "puddle_ditch": Place(
        id="puddle_ditch",
        label="the puddle ditch",
        approach="a low dip by the gate where rainwater liked to stay",
        hazard="mud",
        scare=2,
        image="the mud looked slippy and squishy and gray",
        tags={"mud", "rain"},
    ),
    "loft_shelf": Place(
        id="loft_shelf",
        label="the loft shelf",
        approach="a high shelf by the attic stairs",
        hazard="high",
        scare=3,
        image="the dusty shelf sat above little hands and little chairs",
        tags={"high", "attic"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a buttery glow",
        solves="dark",
        comfort=2,
        use_line="The lantern made a gold little pool, and the shadows grew thin.",
        ending_line="its warm little circle still shining on Bummie and chin",
        tags={"lantern", "light"},
    ),
    "boots": Aid(
        id="boots",
        label="boots",
        phrase="bright rain boots with a stomp-stomp sound",
        solves="mud",
        comfort=1,
        use_line="The boots kept the squelch from nibbling at toes on the way.",
        ending_line="with neat little boot prints that faded away",
        tags={"boots", "mud"},
    ),
    "stool": Aid(
        id="stool",
        label="stool",
        phrase="a sturdy kitchen stool that stood square on the floor",
        solves="high",
        comfort=2,
        use_line="The stool held still and strong, so the high place felt small.",
        ending_line="with Bummie tucked safe after one careful climb up the wall",
        tags={"stool", "climb"},
    ),
}

TRAITS = {
    "timid": Trait(id="timid", label="timid", nerve=1),
    "steady": Trait(id="steady", label="steady", nerve=2),
    "bold": Trait(id="bold", label="bold", nerve=3),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Poppy", "Zoe", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Finn", "Eli", "Noah", "Sam"]
SIBLING_NAMES = ["Pip", "Kit", "June", "Bea", "Toby", "Mae"]

KNOWLEDGE = {
    "dark": [
        (
            "Why can a dark place feel scary?",
            "A dark place can feel scary because your eyes cannot see every corner clearly. When you cannot tell what is there, your body may feel jumpy even if the place is safe."
        )
    ],
    "mud": [
        (
            "Why is mud slippery?",
            "Mud is wet dirt, so your feet can slide on it more easily than on dry ground. That is why careful steps and proper boots help."
        )
    ],
    "high": [
        (
            "Why do children use a sturdy stool with a grown-up nearby?",
            "A sturdy stool can help someone reach a high place more safely than stretching on tiptoe. A grown-up nearby helps keep the climb calm and steady."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so you can see where you are going. Seeing clearly often helps people feel calmer and braver."
        )
    ],
    "boots": [
        (
            "Why do boots help in puddles and mud?",
            "Boots keep wet mud away from your feet and give you a steadier step. That makes a muddy walk feel safer."
        )
    ],
    "stool": [
        (
            "What makes a stool safer than reaching from the floor?",
            "A good stool brings you closer to a high thing, so you do not have to wobble and stretch so much. Safer reaching means fewer slips."
        )
    ],
    "comfort": [
        (
            "Why can a comfort cloth or toy help a child feel better?",
            "A comfort thing feels familiar, soft, and loved. That familiar feeling can help a child calm down after a fright or a cry."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing a kind or necessary thing even when you feel scared inside. It does not mean having no fear at all."
        )
    ],
}


def valid_combo(place: Place, aid: Aid) -> bool:
    return place.hazard == aid.solves


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for aid_id, aid in AIDS.items():
            if valid_combo(place, aid):
                out.append((place_id, aid_id))
    return out


def bravery_score(place: Place, aid: Aid, trait: Trait) -> int:
    return trait.nerve + aid.comfort + 1


def mood_of(place: Place, aid: Aid, trait: Trait) -> str:
    margin = bravery_score(place, aid, trait) - place.scare
    if margin >= 2:
        return "springy"
    if margin == 1:
        return "steady"
    return "quivery"


def predict_retrieval(world: World, place: Place, aid: Aid, trait: Trait) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["care"] += 1
    hero.memes["worry"] += 1
    propagate(sim, narrate=False)
    can_reach = valid_combo(place, aid) and bravery_score(place, aid, trait) >= place.scare
    return {
        "ambivalence": hero.memes["ambivalence"] >= THRESHOLD,
        "can_reach": can_reach,
        "mood": mood_of(place, aid, trait),
    }


def introduce(world: World, hero: Entity, sibling: Entity) -> None:
    world.say(
        f"{hero.id} and little {sibling.id} played by the window one soft afternoon, snug and light. "
        f"They bounced a cloth friend named Bummie till the room felt warm and bright."
    )


def lose_bummie(world: World, sibling: Entity, place: Place) -> None:
    bummie = world.get("bummie")
    sibling.memes["sad"] += 1
    bummie.meters["lost"] += 1
    bummie.attrs["place"] = place.id
    world.say(
        f"Then Bummie gave a fluttery flop and slipped away from their game, "
        f"landing in {place.label}, where the world did not look quite the same."
    )
    world.say(
        f"{place.label.capitalize()} was {place.approach}; {place.image}. "
        f'"Bummie!" cried {sibling.id}, and tears came round and round.'
    )


def feel_ambivalence(world: World, hero: Entity) -> None:
    hero.memes["care"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} felt ambivalence in {hero.pronoun('possessive')} little chest that day: "
        f"helping felt right, but fear still whispered, stay away."
    )


def parent_guides(world: World, parent: Entity, hero: Entity, place: Place, aid: Aid, trait: Trait) -> None:
    pred = predict_retrieval(world, place, aid, trait)
    world.facts["predicted_mood"] = pred["mood"]
    world.facts["predicted_ambivalence"] = pred["ambivalence"]
    world.say(
        f"{parent.label_word.capitalize()} knelt down low and said, "
        f'"You do not have to roar to show you care. Brave hearts can tremble and still go there."'
    )
    world.say(
        f'"Take {aid.phrase}," {parent.pronoun()} said. "It fits this place just right, '
        f'and I will stay right here beside your sight."'
    )


def take_aid(world: World, hero: Entity, aid: Aid) -> None:
    tool = world.get("aid")
    tool.attrs["in_hand"] = True
    hero.meters["ready"] += 1
    hero.memes["supported"] += 1
    world.say(aid.use_line)


def retrieve(world: World, hero: Entity, sibling: Entity, place: Place, aid: Aid, trait: Trait) -> None:
    bummie = world.get("bummie")
    hero.meters["steps"] += 1
    hero.memes["bravery"] = float(bravery_score(place, aid, trait))
    hero.meters["distance"] = float(place.scare)
    if place.hazard == "mud":
        hero.meters["mud"] += 1
    if place.hazard == "high":
        hero.meters["height"] += 1
    bummie.meters["found"] += 1
    bummie.meters["lost"] = 0.0
    propagate(world, narrate=False)

    mood = mood_of(place, aid, trait)
    if mood == "quivery":
        line = f"{hero.id} took one small breath, then another, then stepped on through."
    elif mood == "steady":
        line = f"{hero.id} walked with a careful beat, brave and true."
    else:
        line = f"{hero.id} moved with a bright brave skip, as if kindness already knew what to do."
    world.say(line)
    world.say(
        f"Soon {hero.pronoun()} reached out, scooped up Bummie, and turned back with a smile set free. "
        f"{sibling.id} clapped little hands to see."
    )


def resolve(world: World, hero: Entity, sibling: Entity, aid: Aid) -> None:
    hero.memes["pride"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"{sibling.id} hugged Bummie close and the crying grew small; "
        f"the room felt softer, gentler, kinder to all."
    )
    world.say(
        f'{hero.id} whispered, "I was scared at the start, and that is true, '
        f'but bravery can walk with a shaky shoe."'
    )
    world.say(
        f"And there they stood, {aid.ending_line}, "
        f"with brave little hearts in a tender line."
    )


def tell(
    *,
    place: Place,
    aid: Aid,
    trait: Trait,
    hero_name: str,
    hero_gender: str,
    sibling_name: str,
    sibling_gender: str,
    parent_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait.id]))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_gender, role="sibling"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="bummie", type="comfort", label="Bummie", attrs={"soft": True, "place": place.id}))
    world.add(Entity(id="aid", type="aid", label=aid.label, attrs={"in_hand": False}))
    world.add(Entity(id="place", type="place", label=place.label, attrs={"hazard": place.hazard}))

    hero.memes["care"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["ambivalence"] = 0.0
    hero.memes["supported"] = 0.0
    hero.memes["bravery"] = 0.0
    sibling.memes["sad"] = 0.0
    sibling.memes["relief"] = 0.0
    world.get("bummie").meters["lost"] = 0.0
    world.get("bummie").meters["found"] = 0.0

    introduce(world, hero, sibling)
    world.para()
    lose_bummie(world, sibling, place)
    feel_ambivalence(world, hero)
    world.para()
    parent_guides(world, parent, hero, place, aid, trait)
    take_aid(world, hero, aid)
    retrieve(world, hero, sibling, place, aid, trait)
    world.para()
    resolve(world, hero, sibling, aid)

    world.facts.update(
        hero=hero,
        sibling=sibling,
        parent=parent,
        place=place,
        aid=aid,
        trait=trait,
        bummie=world.get("bummie"),
        mood=mood_of(place, aid, trait),
        bravery=bravery_score(place, aid, trait),
        retrieved=world.get("bummie").meters["found"] >= THRESHOLD,
        ambivalence=hero.memes["ambivalence"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    aid: str
    trait: str
    hero_name: str
    hero_gender: str
    sibling_name: str
    sibling_gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    place = f["place"]
    aid = f["aid"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "bummie" and "ambivalence" and shows bravery.',
        f"Tell a gentle rhyming story where {hero.id} feels torn but chooses to fetch Bummie from {place.label} with {aid.phrase}.",
        f"Write a child-facing poem-story in which {sibling.id} loses Bummie, a grown-up offers the right help, and bravery means going on even while a heart feels shaky.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    parent = f["parent"]
    place = f["place"]
    aid = f["aid"]
    mood = f["mood"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, little {sibling.id}, and {hero.pronoun('possessive')} {parent.label_word}. Bummie is the soft comfort-cloth they care about."
        ),
        (
            "What happened to Bummie?",
            f"Bummie slipped away from the game and landed in {place.label}. That is why {sibling.id} began to cry and needed help."
        ),
        (
            f"Why did {hero.id} feel ambivalence?",
            f"{hero.id} wanted to help because {sibling.id} was sad, but {place.label} also felt scary. The mixed feeling of caring and worrying at the same time is the ambivalence named in the story."
        ),
        (
            f"How did the grown-up help {hero.id} be brave?",
            f"{parent.label_word.capitalize()} gave {hero.id} {aid.phrase} because it matched the problem in {place.label}. The right help made the place feel more manageable, so bravery had a safe path to follow."
        ),
        (
            f"How did {hero.id} get Bummie back?",
            f"{hero.id} went carefully into {place.label} and used the {aid.label} to handle the tricky part. {hero.pronoun().capitalize()} brought Bummie back instead of turning away, which is what made the brave choice matter."
        ),
        (
            "How did the story end?",
            f"It ended with {sibling.id} hugging Bummie again and the whole room feeling calm. {hero.id} still admitted to being scared, but by the end that fear was standing beside bravery instead of blocking it."
        ),
    ]
    if mood == "quivery":
        qa.append(
            (
                f"Was {hero.id} fearless?",
                f"No. {hero.id} was still shaky inside, and the story says so plainly. The brave part is that {hero.pronoun()} kept going kindly even with that fluttery feeling."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"comfort", "bravery"}
    tags |= set(world.facts["place"].tags)
    tags |= set(world.facts["aid"].tags)
    ordered = ["dark", "mud", "high", "lantern", "boots", "stool", "comfort", "bravery"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} helps with {aid.solves}, but {place.label} is a {place.hazard} problem. "
        f"Pick the aid that matches the place's real trouble.)"
    )


def outcome_of(params: StoryParams) -> str:
    return mood_of(PLACES[params.place], AIDS[params.aid], TRAITS[params.trait])


ASP_RULES = r"""
compatible(P,A) :- place(P), aid(A), hazard(P,H), solves(A,H).

score(P,A,T,N + C + 1) :- compatible(P,A), trait(T), scare(P,N), comfort(A,C).
margin(P,A,T,S - N) :- score(P,A,T,S), scare(P,N).

mood(P,A,T,springy) :- compatible(P,A), margin(P,A,T,M), M >= 2.
mood(P,A,T,steady)  :- compatible(P,A), margin(P,A,T,1).
mood(P,A,T,quivery) :- compatible(P,A), margin(P,A,T,0).

#show compatible/2.
#show mood/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("hazard", place_id, place.hazard))
        lines.append(asp.fact("scare", place_id, place.scare))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("solves", aid_id, aid.solves))
        lines.append(asp.fact("comfort", aid_id, aid.comfort))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("nerve", trait_id, trait.nerve))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_mood(place_id: str, aid_id: str, trait_id: str) -> str:
    import asp

    show = (
        f"#show mood/4.\n"
        f"chosen_place({place_id}).\n"
        f"chosen_aid({aid_id}).\n"
        f"chosen_trait({trait_id}).\n"
    )
    program = (
        f"{asp_facts()}\n"
        r"""
compatible(P,A) :- place(P), aid(A), hazard(P,H), solves(A,H).
score(P,A,T,Nr + C + 1) :- compatible(P,A), trait(T), nerve(T,Nr), comfort(A,C).
margin(P,A,T,S - N) :- score(P,A,T,S), scare(P,N).
mood(P,A,T,springy) :- compatible(P,A), margin(P,A,T,M), M >= 2.
mood(P,A,T,steady)  :- compatible(P,A), margin(P,A,T,1).
mood(P,A,T,quivery) :- compatible(P,A), margin(P,A,T,0).
#show mood/4.
"""
    )
    model = asp.one_model(program)
    for p, a, t, m in asp.atoms(model, "mood"):
        if (p, a, t) == (place_id, aid_id, trait_id):
            return m
    return "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combo gate matches ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = []
    for place_id, aid_id in sorted(valid_combos()):
        for trait_id in sorted(TRAITS):
            params = StoryParams(
                place=place_id,
                aid=aid_id,
                trait=trait_id,
                hero_name="Lila",
                hero_gender="girl",
                sibling_name="Pip",
                sibling_gender="boy",
                parent="mother",
            )
            cases.append(params)

    bad = 0
    for params in cases:
        if outcome_of(params) != asp_mood(params.place, params.aid, params.trait):
            bad += 1
    if bad == 0:
        print(f"OK: mood model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} mood results differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        place="hedge_tunnel",
        aid="lantern",
        trait="timid",
        hero_name="Lila",
        hero_gender="girl",
        sibling_name="Pip",
        sibling_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="puddle_ditch",
        aid="boots",
        trait="steady",
        hero_name="Milo",
        hero_gender="boy",
        sibling_name="Mae",
        sibling_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="loft_shelf",
        aid="stool",
        trait="bold",
        hero_name="Ruby",
        hero_gender="girl",
        sibling_name="Toby",
        sibling_gender="boy",
        parent="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming bravery storyworld: a child fetches Bummie with the right help."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--aid", choices=sorted(AIDS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.aid:
        place = PLACES[args.place]
        aid = AIDS[args.aid]
        if not valid_combo(place, aid):
            raise StoryError(explain_rejection(place, aid))

    combos = [
        (place_id, aid_id)
        for place_id, aid_id in valid_combos()
        if (args.place is None or args.place == place_id)
        and (args.aid is None or args.aid == aid_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, aid_id = rng.choice(sorted(combos))
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    sibling_name = args.sibling_name or rng.choice([n for n in SIBLING_NAMES if n != hero_name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        aid=aid_id,
        trait=trait_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    place = PLACES[params.place]
    aid = AIDS[params.aid]
    trait = TRAITS[params.trait]

    if not valid_combo(place, aid):
        raise StoryError(explain_rejection(place, aid))

    world = tell(
        place=place,
        aid=aid,
        trait=trait,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sibling_name=params.sibling_name,
        sibling_gender=params.sibling_gender,
        parent_type=params.parent,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, aid) combos:\n")
        for place_id, aid_id in combos:
            print(f"  {place_id:13} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.place} with {p.aid} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
