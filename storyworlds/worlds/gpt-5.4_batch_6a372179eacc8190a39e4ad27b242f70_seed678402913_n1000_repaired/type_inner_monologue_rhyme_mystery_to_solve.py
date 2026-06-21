#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py
===========================================================================

A small storyworld about a woodland animal solving a gentle mystery. The story
always includes the word "type", uses inner monologue, leans on rhyme, and ends
with a solved puzzle and a changed social scene.

Domain sketch
-------------
A little forest animal is about to start a rhyme circle when one needed item is
missing from the stump stage. A clue is left behind. The hero follows that clue,
reasons about what type of clue it is, finds the borrower, learns the kind
reason behind the borrowing, and then the friends solve the problem together.

The world model keeps the mystery honest:

* each culprit leaves exactly one kind of clue
* each culprit is found in exactly one matching place
* each culprit only borrows certain items for plausible reasons

So a valid story is a consistent quadruple:
    (item, culprit, clue, location)

The Python gate and the inline ASP twin both enforce that consistency.

Run it
------
python storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py
python storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py --all
python storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py --item bell --culprit duck
python storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py --culprit fox --clue feather
python storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py --qa --json
python storyworlds/worlds/gpt-5.4/type_inner_monologue_rhyme_mystery_to_solve.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "duck", "goose", "ewe"}
        male = {"boy", "father", "fox", "badger", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class HeroSpec:
    id: str
    name: str
    species: str
    title: str
    trait: str
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    song_use: str
    return_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueSpec:
    id: str
    label: str
    phrase: str
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LocationSpec:
    id: str
    label: str
    phrase: str
    sensory: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CulpritSpec:
    id: str
    name: str
    species: str
    clue: str
    location: str
    reasons: dict[str, str]
    apology: str
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


def _r_missing_makes_mystery(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.get("glade").meters["mystery"] += 1
    return []


def _r_clue_supports_guess(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("guess", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["focus"] += 1
    world.get("glade").meters["trail"] += 1
    return []


def _r_kindness_clears_worry(world: World) -> list[str]:
    hero = world.get("hero")
    culprit = world.get("culprit")
    item = world.get("item")
    if culprit.memes["understood"] < THRESHOLD or item.meters["returned"] < THRESHOLD:
        return []
    sig = ("relief", culprit.id, item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["friendship"] += 1
    culprit.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_makes_mystery", tag="mystery", apply=_r_missing_makes_mystery),
    Rule(name="clue_supports_guess", tag="mystery", apply=_r_clue_supports_guess),
    Rule(name="kindness_clears_worry", tag="social", apply=_r_kindness_clears_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


HEROES = {
    "mouse": HeroSpec(
        id="mouse",
        name="Mimi",
        species="mouse",
        title="little mouse poet",
        trait="bright-eyed",
        opening="liked neat sounds and tiny surprises",
        tags={"mouse", "animal"},
    ),
    "rabbit": HeroSpec(
        id="rabbit",
        name="Pip",
        species="rabbit",
        title="young rabbit singer",
        trait="quick-eared",
        opening="loved songs that bounced like feet on grass",
        tags={"rabbit", "animal"},
    ),
    "squirrel": HeroSpec(
        id="squirrel",
        name="Nell",
        species="squirrel",
        title="small squirrel host",
        trait="bushy-tailed",
        opening="collected cheerful words the way others collected nuts",
        tags={"squirrel", "animal"},
    ),
}

ITEMS = {
    "bell": ItemSpec(
        id="bell",
        label="bell",
        phrase="the silver singing bell",
        song_use="tap a bright note before each rhyme",
        return_use="rang the bell once, bright and clear",
        tags={"bell", "rhyme"},
    ),
    "drum": ItemSpec(
        id="drum",
        label="drum",
        phrase="the round thump-thump drum",
        song_use="beat a warm rhythm under each rhyme",
        return_use="patted the drum in a happy little boom",
        tags={"drum", "rhyme"},
    ),
    "lantern": ItemSpec(
        id="lantern",
        label="lantern",
        phrase="the firefly lantern",
        song_use="cast a soft glow over the rhyme circle",
        return_use="hung the lantern high so every face looked gold",
        tags={"lantern", "light"},
    ),
}

CLUES = {
    "feather": ClueSpec(
        id="feather",
        label="feather",
        phrase="a soft blue feather",
        line="A feather, light as weather.",
        tags={"feather", "clue"},
    ),
    "reed": ClueSpec(
        id="reed",
        label="reed",
        phrase="a green pond reed",
        line="A reed, slim as need.",
        tags={"reed", "clue"},
    ),
    "pinecone_scale": ClueSpec(
        id="pinecone_scale",
        label="pinecone scale",
        phrase="a shiny pinecone scale",
        line="A scale from a cone, not dropped by stone.",
        tags={"pinecone", "clue"},
    ),
}

LOCATIONS = {
    "nest": LocationSpec(
        id="nest",
        label="nest",
        phrase="the willow nest",
        sensory="The branches swayed and whispered over a warm little nest.",
        tags={"nest", "tree"},
    ),
    "pond": LocationSpec(
        id="pond",
        label="pond",
        phrase="the reedy pond",
        sensory="The pond made round ripples, and reeds brushed the water with a hush-hush sound.",
        tags={"pond", "water"},
    ),
    "tree_hollow": LocationSpec(
        id="tree_hollow",
        label="tree hollow",
        phrase="the old oak hollow",
        sensory="The old oak smelled like bark and sunshine, with a round dark doorway in its side.",
        tags={"tree", "hollow"},
    ),
}

CULPRITS = {
    "duck": CulpritSpec(
        id="duck",
        name="Della",
        species="duck",
        clue="feather",
        location="nest",
        reasons={
            "bell": "her ducklings would not settle down, and she hoped one gentle ding would gather them close",
            "drum": "her ducklings kept wandering in different directions, and she used the steady beat to lead them back together",
            "lantern": "clouds had covered the nest, and she borrowed the glow so her ducklings would stop peeping in the dark",
        },
        apology="I should have asked before I borrowed it.",
        tags={"duck", "animal"},
    ),
    "frog": CulpritSpec(
        id="frog",
        name="Fenn",
        species="frog",
        clue="reed",
        location="pond",
        reasons={
            "bell": "the little tadpoles were drifting apart, and he thought a tiny ring might call them to the safe side of the pond",
            "drum": "the pond was noisy with wind, and he used the beat to guide the smallest swimmers back toward the lily pads",
            "lantern": "mist had fallen over the water, and he borrowed the glow so the youngest tadpoles could find the bank",
        },
        apology="I was in such a hurry to help that I forgot my manners.",
        tags={"frog", "animal"},
    ),
    "squirrel": CulpritSpec(
        id="squirrel",
        name="Tansy",
        species="squirrel",
        clue="pinecone_scale",
        location="tree_hollow",
        reasons={
            "bell": "her twins were playing too close to a branch edge, and she rang the bell to bring them back",
            "drum": "the baby squirrels were scared of the wind, and the soft thump made them brave enough to stay together",
            "lantern": "a cloud had dimmed the hollow, and she borrowed the lantern so the babies could find their blankets",
        },
        apology="I meant to bring it right back, but the little ones needed me all at once.",
        tags={"squirrel", "animal"},
    ),
}


def compatible(item_id: str, culprit_id: str, clue_id: str, location_id: str) -> bool:
    if item_id not in ITEMS or culprit_id not in CULPRITS or clue_id not in CLUES or location_id not in LOCATIONS:
        return False
    culprit = CULPRITS[culprit_id]
    return clue_id == culprit.clue and location_id == culprit.location and item_id in culprit.reasons


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id in sorted(ITEMS):
        for culprit_id, culprit in sorted(CULPRITS.items()):
            if item_id in culprit.reasons:
                combos.append((item_id, culprit_id, culprit.clue, culprit.location))
    return combos


def infer_culprit_from_clue(clue_id: str) -> Optional[str]:
    matches = [cid for cid, culprit in CULPRITS.items() if culprit.clue == clue_id]
    if len(matches) == 1:
        return matches[0]
    return None


def infer_location_from_culprit(culprit_id: str) -> Optional[str]:
    culprit = CULPRITS.get(culprit_id)
    if culprit is None:
        return None
    return culprit.location


@dataclass
class StoryParams:
    hero: str
    item: str
    culprit: str
    clue: str
    location: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hero="mouse",
        item="bell",
        culprit="duck",
        clue="feather",
        location="nest",
    ),
    StoryParams(
        hero="rabbit",
        item="drum",
        culprit="frog",
        clue="reed",
        location="pond",
    ),
    StoryParams(
        hero="squirrel",
        item="lantern",
        culprit="squirrel",
        clue="pinecone_scale",
        location="tree_hollow",
    ),
]


def introduce(world: World, hero: Entity, item: Entity) -> None:
    world.say(
        f"In the ferny glade, {hero.id} the {hero.type} was the {hero.attrs['title']}. "
        f"{hero.pronoun().capitalize()} {hero.attrs['opening']}."
    )
    world.say(
        f"On that morning, the animals had gathered by a mossy stump, and {item.phrase} was meant to "
        f"{item.attrs['song_use']}."
    )
    world.say('"Sing and ring, sing and ring, let the forest softly sing," the little crowd had practiced.')


def notice_missing(world: World, hero: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached the stump, {item.phrase} was gone."
    )
    world.say(
        f'{hero.id} blinked and thought, "Oh dear. The rhyme circle is here, but the {item.label} is not. '
        f'What type of clue should I look for?"'
    )


def spot_clue(world: World, hero: Entity, clue: Entity) -> None:
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} saw {clue.phrase} near the stump."
    )
    world.say(
        f'{hero.id} whispered, "{clue.attrs["line"]} That is not just a scrap. It is a clue, and clues can tell what is true."'
    )


def reason(world: World, hero: Entity, culprit: Entity, location: Entity) -> None:
    hero.memes["thinking"] += 1
    culprit_id = infer_culprit_from_clue(world.facts["clue_cfg"].id)
    guessed = CULPRITS[culprit_id]
    world.facts["guessed_culprit"] = culprit_id
    world.facts["guessed_location"] = guessed.location
    world.say(
        f'{hero.id} held still and thought, "A {world.facts["clue_cfg"].label} points to {guessed.name}. '
        f'If I follow the clue, I should look by {location.label}."'
    )
    world.say('"Clue by clue, I will go through. I will not stomp, and I will not stew."')


def search(world: World, hero: Entity, location: Entity) -> None:
    hero.meters["steps"] += 1
    world.say(
        f"So {hero.id} padded toward {location.phrase}. {location.attrs['sensory']}"
    )


def find_borrower(world: World, hero: Entity, culprit: Entity, item: Entity) -> None:
    culprit.meters["found"] += 1
    culprit.meters["using"] += 1
    hero.memes["worry"] += 0
    world.say(
        f"There was {culprit.id} the {culprit.type}, holding {item.phrase}."
    )
    world.say(
        f'{hero.id} saw at once that {culprit.pronoun()} was not being mean. {culprit.pronoun().capitalize()} was using it because '
        f'{culprit.attrs["reason"]}.'
    )


def speak_and_understand(world: World, hero: Entity, culprit: Entity, item: Entity) -> None:
    culprit.memes["guilt"] += 1
    world.say(
        f'"{item.label.capitalize()} for a minute, children to finish in itty-bitty time," {culprit.id} said softly. '
        f'"{culprit.attrs["apology"]}"'
    )
    hero.memes["kindness"] += 1
    culprit.memes["understood"] += 1
    world.say(
        f'{hero.id} thought, "So that was the mystery. Not a thief, just a hurry-full heart." '
        f'Then {hero.pronoun()} said, "Next time, please ask. I can help faster than you think."'
    )


def resolve(world: World, hero: Entity, culprit: Entity, item: Entity) -> None:
    item.meters["missing"] = 0.0
    item.meters["returned"] += 1
    culprit.meters["using"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Together they finished the small job, and then {culprit.id} carried {item.phrase} back to the glade."
    )


def ending(world: World, hero: Entity, culprit: Entity, item: Entity) -> None:
    world.say(
        f"At the stump, {hero.id} {item.attrs['return_use']}, and the circle began at last."
    )
    world.say(
        f'"Near or far, here we are. Kind hearts mend what worries mar," sang the animals.'
    )
    world.say(
        f'{hero.id} smiled at {culprit.id}. The mystery was solved, the rhyme was right, and the glade felt warmer than before.'
    )


def tell(params: StoryParams) -> World:
    if not compatible(params.item, params.culprit, params.clue, params.location):
        raise StoryError(explain_rejection(params))

    hero_cfg = HEROES[params.hero]
    item_cfg = ITEMS[params.item]
    clue_cfg = CLUES[params.clue]
    location_cfg = LOCATIONS[params.location]
    culprit_cfg = CULPRITS[params.culprit]

    world = World()
    hero = world.add(Entity(
        id=hero_cfg.name,
        kind="character",
        type=hero_cfg.species,
        label=hero_cfg.species,
        phrase=f"{hero_cfg.name} the {hero_cfg.species}",
        role="hero",
        attrs={
            "title": hero_cfg.title,
            "opening": hero_cfg.opening,
            "trait": hero_cfg.trait,
        },
        tags=set(hero_cfg.tags),
    ))
    culprit = world.add(Entity(
        id=culprit_cfg.name,
        kind="character",
        type=culprit_cfg.species,
        label=culprit_cfg.species,
        phrase=f"{culprit_cfg.name} the {culprit_cfg.species}",
        role="culprit",
        attrs={
            "reason": culprit_cfg.reasons[item_cfg.id],
            "apology": culprit_cfg.apology,
        },
        tags=set(culprit_cfg.tags),
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="item",
        attrs={
            "song_use": item_cfg.song_use,
            "return_use": item_cfg.return_use,
        },
        tags=set(item_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        role="clue",
        attrs={"line": clue_cfg.line},
        tags=set(clue_cfg.tags),
    ))
    location = world.add(Entity(
        id="location",
        kind="thing",
        type="place",
        label=location_cfg.label,
        phrase=location_cfg.phrase,
        role="location",
        attrs={"sensory": location_cfg.sensory},
        tags=set(location_cfg.tags),
    ))
    world.add(Entity(
        id="glade",
        kind="thing",
        type="place",
        label="glade",
        phrase="the ferny glade",
        role="setting",
    ))

    introduce(world, hero, item)
    world.para()
    notice_missing(world, hero, item)
    spot_clue(world, hero, clue)
    reason(world, hero, culprit, location)
    world.para()
    search(world, hero, location)
    find_borrower(world, hero, culprit, item)
    speak_and_understand(world, hero, culprit, item)
    world.para()
    resolve(world, hero, culprit, item)
    ending(world, hero, culprit, item)

    world.facts.update(
        hero=hero,
        culprit=culprit,
        item=item,
        clue=clue,
        location=location,
        hero_cfg=hero_cfg,
        culprit_cfg=culprit_cfg,
        item_cfg=item_cfg,
        clue_cfg=clue_cfg,
        location_cfg=location_cfg,
        solved=item.meters["returned"] >= THRESHOLD,
        borrowed_reason=culprit_cfg.reasons[item_cfg.id],
        kind_resolution=culprit.memes["understood"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    clue_cfg = f["clue_cfg"]
    culprit_cfg = f["culprit_cfg"]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the word "type", uses inner monologue, and has a gentle mystery about a missing {item_cfg.label}.',
        f"Tell a rhyming woodland mystery where {hero.id} the {hero.type} finds {clue_cfg.phrase}, thinks about what type of clue it is, and discovers that {culprit_cfg.name} borrowed the missing item for a kind reason.",
        f"Write a soft mystery-to-solve story with small rhymes, a worried but thoughtful animal hero, and an ending where the missing {item_cfg.label} comes back and the friends sing together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    culprit = f["culprit"]
    item_cfg = f["item_cfg"]
    clue_cfg = f["clue_cfg"]
    location_cfg = f["location_cfg"]
    reason_text = f["borrowed_reason"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who was getting ready for a rhyme circle in the glade. "
            f"It is also about {culprit.id} the {culprit.type}, whose hurried borrowing caused the mystery."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item_cfg.phrase}. The animals needed it to {item_cfg.song_use}."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {clue_cfg.phrase} by the stump. That clue mattered because it pointed toward {culprit.id}."
        ),
        (
            f"How did {hero.id} solve the mystery?",
            f"{hero.id} stopped and thought about what type of clue {clue_cfg.phrase} was. "
            f"Then {hero.pronoun()} followed that clue to {location_cfg.phrase}, where {culprit.id} was holding the missing {item_cfg.label}."
        ),
        (
            f"Why had {culprit.id} borrowed the {item_cfg.label}?",
            f"{culprit.id} had borrowed it because {reason_text}. "
            f"The answer to the mystery was kindness in a hurry, not meanness."
        ),
        (
            "How did the story end?",
            f"They finished the small job together, brought the {item_cfg.label} back, and started the rhyme circle at last. "
            f"The ending shows that the mystery was solved and the friends understood each other better."
        ),
    ]
    return qa


KNOWLEDGE = {
    "bell": [
        (
            "What is a bell?",
            "A bell is something that rings when you tap or shake it. Its bright sound can help call friends or start a song."
        )
    ],
    "drum": [
        (
            "What is a drum?",
            "A drum is something you tap to make a beat. The beat can help people clap, march, or sing together."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you carry or hang up. It helps you see when a place is dim."
        )
    ],
    "feather": [
        (
            "What is a feather?",
            "A feather is a soft part of a bird's body. If you find one on the ground, it can be a clue that a bird was nearby."
        )
    ],
    "reed": [
        (
            "What is a reed?",
            "A reed is a tall water plant that grows near ponds and streams. Seeing one can tell you to look near the water."
        )
    ],
    "pinecone": [
        (
            "What is a pinecone?",
            "A pinecone is the cone from certain trees, and it has little scales on it. Animals that climb trees often carry or nibble them."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle with missing facts. You solve it by noticing clues and thinking carefully about what they mean."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme happens when words sound alike at the end, like sing and ring. Rhymes can make stories and songs feel playful."
        )
    ],
    "asking": [
        (
            "Why is it good to ask before borrowing something?",
            "Asking first is polite and helps everyone know where things are. It also stops small mix-ups from turning into worries."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "rhyme", "bell", "drum", "lantern", "feather", "reed", "pinecone", "asking"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mystery", "rhyme", "asking"}
    item_cfg = world.facts["item_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    tags |= set(item_cfg.tags)
    if clue_cfg.id == "pinecone_scale":
        tags.add("pinecone")
    else:
        tags |= set(clue_cfg.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    parts = []
    if params.culprit in CULPRITS:
        culprit = CULPRITS[params.culprit]
        if params.clue != culprit.clue:
            parts.append(
                f"{culprit.name} the {culprit.species} leaves the clue '{culprit.clue}', not '{params.clue}'"
            )
        if params.location != culprit.location:
            parts.append(
                f"{culprit.name} belongs at '{culprit.location}', not '{params.location}'"
            )
        if params.item not in culprit.reasons:
            parts.append(
                f"{culprit.name} has no borrowing reason for '{params.item}'"
            )
    if not parts:
        return "(No story: the chosen item, culprit, clue, and location do not make one consistent mystery.)"
    return "(No story: " + "; ".join(parts) + ".)"


ASP_RULES = r"""
valid(Item, Culprit, Clue, Location) :-
    item(Item), culprit(Culprit), clue(Clue), location(Location),
    reason(Culprit, Item),
    leaves(Culprit, Clue),
    lives(Culprit, Location).

inferred_culprit(Clue, Culprit) :-
    culprit(Culprit),
    leaves(Culprit, Clue).

inferred_location(Culprit, Location) :-
    culprit(Culprit),
    lives(Culprit, Location).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id in sorted(ITEMS):
        lines.append(asp.fact("item", item_id))
    for clue_id in sorted(CLUES):
        lines.append(asp.fact("clue", clue_id))
    for location_id in sorted(LOCATIONS):
        lines.append(asp.fact("location", location_id))
    for culprit_id, culprit in sorted(CULPRITS.items()):
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("leaves", culprit_id, culprit.clue))
        lines.append(asp.fact("lives", culprit_id, culprit.location))
        for item_id in sorted(culprit.reasons):
            lines.append(asp.fact("reason", culprit_id, item_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_inferred_culprit(clue_id: str) -> Optional[str]:
    import asp

    model = asp.one_model(asp_program(asp.fact("given_clue", clue_id), "#show inferred_culprit/2."))
    atoms = [atom for atom in asp.atoms(model, "inferred_culprit") if atom[0] == clue_id]
    if len(atoms) == 1:
        return atoms[0][1]
    return None


def asp_inferred_location(culprit_id: str) -> Optional[str]:
    import asp

    model = asp.one_model(asp_program("", "#show inferred_location/2."))
    atoms = [atom for atom in asp.atoms(model, "inferred_location") if atom[0] == culprit_id]
    if len(atoms) == 1:
        return atoms[0][1]
    return None


def asp_verify() -> int:
    rc = 0

    p_valid = set(valid_combos())
    a_valid = set(asp_valid_combos())
    if p_valid == a_valid:
        print(f"OK: ASP valid combos match Python ({len(p_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in ASP:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in Python:", sorted(p_valid - a_valid))

    bad_clues = []
    for clue_id in sorted(CLUES):
        if asp_inferred_culprit(clue_id) != infer_culprit_from_clue(clue_id):
            bad_clues.append(clue_id)
    if not bad_clues:
        print("OK: inferred culprit from clue matches for all clues.")
    else:
        rc = 1
        print("MISMATCH in clue inference:", bad_clues)

    bad_locations = []
    for culprit_id in sorted(CULPRITS):
        if asp_inferred_location(culprit_id) != infer_location_from_culprit(culprit_id):
            bad_locations.append(culprit_id)
    if not bad_locations:
        print("OK: inferred location from culprit matches for all culprits.")
    else:
        rc = 1
        print("MISMATCH in location inference:", bad_locations)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Woodland mystery storyworld with rhyme, inner monologue, and a gentle puzzle."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue:
        culprit = CULPRITS[args.culprit]
        if culprit.clue != args.clue:
            raise StoryError(explain_rejection(StoryParams(
                hero=args.hero or next(iter(HEROES)),
                item=args.item or next(iter(ITEMS)),
                culprit=args.culprit,
                clue=args.clue,
                location=args.location or culprit.location,
            )))
    if args.culprit and args.location:
        culprit = CULPRITS[args.culprit]
        if culprit.location != args.location:
            raise StoryError(explain_rejection(StoryParams(
                hero=args.hero or next(iter(HEROES)),
                item=args.item or next(iter(ITEMS)),
                culprit=args.culprit,
                clue=args.clue or culprit.clue,
                location=args.location,
            )))
    if args.item and args.culprit:
        culprit = CULPRITS[args.culprit]
        if args.item not in culprit.reasons:
            raise StoryError(explain_rejection(StoryParams(
                hero=args.hero or next(iter(HEROES)),
                item=args.item,
                culprit=args.culprit,
                clue=args.clue or culprit.clue,
                location=args.location or culprit.location,
            )))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.location is None or combo[3] == args.location)
    ]
    if not combos:
        candidate = StoryParams(
            hero=args.hero or next(iter(HEROES)),
            item=args.item or next(iter(ITEMS)),
            culprit=args.culprit or next(iter(CULPRITS)),
            clue=args.clue or next(iter(CLUES)),
            location=args.location or next(iter(LOCATIONS)),
        )
        raise StoryError(explain_rejection(candidate))

    item_id, culprit_id, clue_id, location_id = rng.choice(sorted(combos))
    hero_id = args.hero or rng.choice(sorted(HEROES))
    return StoryParams(
        hero=hero_id,
        item=item_id,
        culprit=culprit_id,
        clue=clue_id,
        location=location_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero '{params.hero}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit '{params.culprit}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location '{params.location}'.)")
    if not compatible(params.item, params.culprit, params.clue, params.location):
        raise StoryError(explain_rejection(params))

    world = tell(params)
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
        print(asp_program("", "#show valid/4.\n#show inferred_culprit/2.\n#show inferred_location/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, culprit, clue, location) combos:\n")
        for item_id, culprit_id, clue_id, location_id in combos:
            print(f"  {item_id:8} {culprit_id:10} {clue_id:14} {location_id}")
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
            header = f"### {p.hero}: {p.item} mystery with {p.culprit} at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
