#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alibi_mystery_to_solve_transformation_tall_tale.py
==============================================================================

A standalone story world for a child-facing tall tale with a mystery to solve
and a transformation at its heart.

Premise
-------
At a booming county fair, a prize object vanishes. A nearby grown-up looks
suspicious, but has an alibi. The real culprit is a small fair animal that has
been transformed by moon-thistle pollen into a giant version of itself. The
hero solves the mystery by following outsized clues, calming the transformed
animal in a sensible way, and bringing the prize back.

The storyworld prefers a small set of strong, common-sense variants:
- the animal must actually like the missing prize and be strong enough to drag it
- the chosen calming method must be a reasonable way to end the giant-animal panic
- a named suspect must have a true alibi, so the mystery turns from blame to clues

Run it
------
python storyworlds/worlds/gpt-5.4/alibi_mystery_to_solve_transformation_tall_tale.py
python storyworlds/worlds/gpt-5.4/alibi_mystery_to_solve_transformation_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/alibi_mystery_to_solve_transformation_tall_tale.py --qa
python storyworlds/worlds/gpt-5.4/alibi_mystery_to_solve_transformation_tall_tale.py --trace
python storyworlds/worlds/gpt-5.4/alibi_mystery_to_solve_transformation_tall_tale.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    weight: int
    scent: str
    trail: str
    destination: str
    nibble: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    giant_label: str
    likes: set[str] = field(default_factory=set)
    strength: int = 1
    clue: str = ""
    sound: str = ""
    burrow: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    sense: int
    power: int
    use_text: str
    calm_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    job: str
    alibi_place: str
    alibi_witness: str
    busy_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_missing_means_worry(world: World) -> list[str]:
    prize = world.entities.get("prize")
    hero = world.entities.get("hero")
    if not prize or not hero:
        return []
    if prize.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return []


def _r_giant_leaves_clues(world: World) -> list[str]:
    creature = world.entities.get("creature")
    prize = world.entities.get("prize")
    if not creature or not prize:
        return []
    if creature.meters["giant"] < THRESHOLD or prize.meters["dragged"] < THRESHOLD:
        return []
    sig = ("clues", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("fair").meters["mystery"] += 1
    prize.meters["clues_visible"] += 1
    return []


def _r_shrink_calm(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if not creature:
        return []
    if creature.meters["shrunk"] < THRESHOLD:
        return []
    sig = ("calm", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["calm"] += 1
    creature.meters["giant"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_means_worry", tag="emotion", apply=_r_missing_means_worry),
    Rule(name="giant_leaves_clues", tag="physical", apply=_r_giant_leaves_clues),
    Rule(name="shrink_calm", tag="transformation", apply=_r_shrink_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def can_steal(prize: Prize, creature: Creature) -> bool:
    return prize.id in creature.likes and creature.strength >= prize.weight


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def is_recovered(remedy: Remedy, creature: Creature) -> bool:
    return remedy.power >= creature.strength


def predict_case(prize: Prize, creature: Creature, remedy: Remedy) -> dict:
    return {
        "can_steal": can_steal(prize, creature),
        "recovered": can_steal(prize, creature) and is_recovered(remedy, creature),
    }


def opening(world: World, hero: Entity, helper: Entity, parent: Entity, prize: Prize) -> None:
    hero.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"On fair day, {hero.id} and {helper.id} went with {hero.pronoun('possessive')} "
        f"{parent.label_word} to the county grounds, where the windmill spun so fast it "
        f"looked as if it were stirring the clouds with a spoon."
    )
    world.say(
        f"At the center of it all sat {prize.phrase}, so big and grand that folks said "
        f"you could smell {prize.scent} from two cornfields away."
    )


def introduce_mystery(world: World, hero: Entity, prize: Prize) -> None:
    world.say(
        f"{hero.id} blinked once, twice, and then three times for luck. "
        f"{prize.phrase.capitalize()} was gone."
    )
    prize_ent = world.get("prize")
    prize_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Only a long scrape in the dust and a few crumbs of {prize.trail} showed "
        f"where it had stood."
    )


def point_to_suspect(world: World, hero: Entity, suspect: Entity) -> None:
    hero.memes["suspicion"] += 1
    world.say(
        f"Standing nearest was {suspect.id}, the {suspect.attrs['job']}, with flour on "
        f"{suspect.pronoun('possessive')} sleeves and a startled look on "
        f"{suspect.pronoun('possessive')} face."
    )
    world.say(
        f'"Maybe {suspect.id} took it," {hero.id} whispered. "It looks mighty suspicious."'
    )


def hear_alibi(world: World, suspect: Entity, suspect_cfg: Suspect) -> None:
    suspect.memes["earnest"] += 1
    world.say(
        f'But {suspect.id} lifted both hands and said, "I have an alibi. I was at '
        f'{suspect_cfg.alibi_place} with {suspect_cfg.alibi_witness}, and half the fair '
        f'saw me there."'
    )
    world.say(
        f"{suspect_cfg.busy_text.capitalize()}, and the words rang true as a dinner bell."
    )


def inspect_clues(world: World, hero: Entity, helper: Entity, prize: Prize, creature: Creature) -> None:
    hero.memes["clever"] += 1
    helper.memes["helpful"] += 1
    world.say(
        f"{hero.id} knelt by the scrape marks. They were not boot marks at all. "
        f"They were {creature.clue}, with a streak of {prize.trail} between them."
    )
    world.say(
        f'"That is no grown-up trail," said {helper.id}. "Something small made itself '
        f'awful big."'
    )


def reveal_pollen(world: World, parent: Entity, creature: Creature) -> None:
    parent.memes["wisdom"] += 1
    world.say(
        f"{parent.label_word.capitalize()} looked toward the moon-thistle patch by the fence "
        f"and nodded slowly. Yellow sparkles still floated there like sleepy fireflies."
    )
    world.say(
        f'"Moon-thistle pollen again," {parent.pronoun()} said. "One sniff of that can turn '
        f'a plain little {creature.label} into {creature.giant_label} by suppertime."'
    )


def chase(world: World, hero: Entity, helper: Entity, prize: Prize, creature: Creature) -> None:
    prize_ent = world.get("prize")
    creature_ent = world.get("creature")
    creature_ent.meters["giant"] += 1
    prize_ent.meters["dragged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The trail ran past the pie tent, over the pumpkin scales, and straight toward "
        f"{creature.burrow}, where the ground rose in a hump big enough to trip a wagon."
    )
    world.say(
        f"There they found the culprit: {creature.giant_label}, {creature.sound}, with "
        f"{prize.phrase} tucked beside it like a bedtime snack."
    )


def use_remedy(world: World, hero: Entity, helper: Entity, remedy: Remedy, creature: Creature) -> None:
    world.say(
        f"{hero.id} and {helper.id} did not shout. They remembered the sensible way. "
        f"They {remedy.use_text}."
    )
    creature_ent = world.get("creature")
    if is_recovered(remedy, creature):
        creature_ent.meters["shrunk"] += 1
        propagate(world, narrate=False)
        world.say(remedy.calm_text.format(creature=creature.label, giant=creature.giant_label))
    else:
        creature_ent.memes["panic"] += 1
        world.say(
            f"But {creature.giant_label.lower()} only shuffled harder and held the prize tighter, "
            f"still too riled up to listen."
        )


def resolution_happy(world: World, hero: Entity, helper: Entity, prize: Prize, creature: Creature) -> None:
    world.get("prize").meters["missing"] = 0.0
    world.get("prize").meters["recovered"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"In three blinks and a breath, the giant shape folded smaller and smaller until "
        f"only a regular {creature.label} sat there, whiskers twitching with embarrassment."
    )
    world.say(
        f"{hero.id} rolled {prize.phrase} back to the fair. It had one {prize.nibble}, but "
        f"it was safe, and the mystery was solved fair and square."
    )
    world.say(
        f"{suspect_line(world)} Nobody blamed the wrong person after that."
    )


def resolution_mended(world: World, hero: Entity, prize: Prize, creature: Creature) -> None:
    world.get("prize").meters["missing"] = 0.0
    world.get("prize").meters["recovered"] += 1
    world.get("prize").meters["nibbled"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"At last the fair band struck up a low, steady tune, and even {creature.giant_label.lower()} "
        f"stopped to listen. That gave everyone time to tug {prize.phrase} home."
    )
    world.say(
        f"The prize came back with more than one {prize.nibble}, so the bakers patched and polished "
        f"it into a laughing sort of victory."
    )
    world.say(
        f"{suspect_line(world)} The fair learned that a good clue is better than a wild guess."
    )


def suspect_line(world: World) -> str:
    suspect = world.facts["suspect"]
    return (
        f"{suspect.id} was cleared at once, because an alibi as solid as a fence post "
        f"beats a suspicious look every time."
    )


def tell(
    prize: Prize,
    creature: Creature,
    remedy: Remedy,
    suspect_cfg: Suspect,
    hero_name: str = "Mae",
    hero_gender: str = "girl",
    helper_name: str = "Jeb",
    helper_gender: str = "boy",
    parent_type: str = "father",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    suspect = world.add(
        Entity(
            id=suspect_cfg.label,
            kind="character",
            type="woman" if suspect_cfg.id == "baker" else "man",
            role="suspect",
            label=suspect_cfg.label,
            attrs={"job": suspect_cfg.job},
            tags=set(suspect_cfg.tags),
        )
    )
    world.add(Entity(id="fair", type="place", label="the fair"))
    world.add(
        Entity(
            id="prize",
            type="prize",
            label=prize.label,
            phrase=prize.phrase,
            tags=set(prize.tags),
        )
    )
    world.add(
        Entity(
            id="creature",
            type="animal",
            label=creature.label,
            phrase=creature.giant_label,
            tags=set(creature.tags),
        )
    )

    opening(world, hero, helper, parent, prize)
    world.para()
    introduce_mystery(world, hero, prize)
    point_to_suspect(world, hero, suspect)
    hear_alibi(world, suspect, suspect_cfg)
    inspect_clues(world, hero, helper, prize, creature)
    reveal_pollen(world, parent, creature)
    world.para()
    chase(world, hero, helper, prize, creature)
    use_remedy(world, hero, helper, remedy, creature)

    if is_recovered(remedy, creature):
        world.para()
        resolution_happy(world, hero, helper, prize, creature)
        outcome = "recovered"
    else:
        world.para()
        resolution_mended(world, hero, prize, creature)
        outcome = "mended"

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        suspect=suspect,
        suspect_cfg=suspect_cfg,
        prize_cfg=prize,
        creature_cfg=creature,
        remedy=remedy,
        outcome=outcome,
        had_alibi=True,
        transformed=True,
        clue=creature.clue,
        solved=True,
    )
    return world


KNOWLEDGE = {
    "alibi": [
        (
            "What is an alibi?",
            "An alibi is a good reason showing where someone was at the time something happened. It can help prove that person did not do it."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery?",
            "You look for clues, ask careful questions, and check which ideas fit the facts. A good mystery is solved by noticing what is true, not by guessing wildly."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a different form. In this story world, a small animal can change into a giant one."
        )
    ],
    "rabbit": [
        (
            "Why do rabbits nibble things?",
            "Rabbits like to gnaw and nibble with their front teeth. They often go after foods that smell sweet or fresh."
        )
    ],
    "goat": [
        (
            "Why are goats hard to stop once they want a snack?",
            "Goats are curious and stubborn animals. If they smell something tasty, they may pull and tug to get it."
        )
    ],
    "hog": [
        (
            "Why can a hog make a big mess around food?",
            "A hog is strong and loves eating. If it gets into food, it can push, root, and gobble in a hurry."
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft song sung to calm someone down. Quiet music can help a frightened creature settle."
        )
    ],
    "mint": [
        (
            "Why can a cool cloth or minty water help an upset animal?",
            "A cool, gentle touch can calm a hot, startled animal. When a creature feels less stirred up, it is easier for it to settle."
        )
    ],
    "oats": [
        (
            "Why should you use food carefully when calming an animal?",
            "Food can lure an animal to a safe spot, but it should be used carefully and kindly. You do not want to make the animal grabby or more excited."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "alibi",
    "mystery",
    "transformation",
    "rabbit",
    "goat",
    "hog",
    "lullaby",
    "mint",
    "oats",
]


PRIZES = {
    "pie": Prize(
        id="pie",
        label="pie",
        phrase="the blue-ribbon huckleberry pie",
        weight=1,
        scent="warm berries and sugar",
        trail="purple filling",
        destination="the hay shed",
        nibble="missing bite",
        tags={"mystery"},
    ),
    "cheese": Prize(
        id="cheese",
        label="cheese wheel",
        phrase="the champion cheese wheel",
        weight=2,
        scent="sharp cheese and butter",
        trail="yellow crumbs",
        destination="the cider press",
        nibble="gnawed edge",
        tags={"mystery"},
    ),
    "melon": Prize(
        id="melon",
        label="melon",
        phrase="the striped moonmelon",
        weight=3,
        scent="sweet rind and sunshine",
        trail="green rind scrapings",
        destination="the wagon shed",
        nibble="toothy scoop",
        tags={"mystery"},
    ),
}

CREATURES = {
    "rabbit": Creature(
        id="rabbit",
        label="rabbit",
        giant_label="a rabbit as big as a wheelbarrow",
        likes={"pie", "melon"},
        strength=1,
        clue="enormous hopping prints",
        sound="snuffling like a tiny engine",
        burrow="the clover hill",
        tags={"rabbit", "transformation"},
    ),
    "goat": Creature(
        id="goat",
        label="goat",
        giant_label="a goat as big as a porch swing",
        likes={"pie", "cheese", "melon"},
        strength=2,
        clue="split hoofprints big as soup bowls",
        sound="bleating loud enough to rattle the bunting",
        burrow="the clover hill",
        tags={"goat", "transformation"},
    ),
    "hog": Creature(
        id="hog",
        label="hog",
        giant_label="a hog as big as a hay wagon",
        likes={"cheese", "melon"},
        strength=3,
        clue="round hoof holes and a plowed-up groove",
        sound="snorting like thunder in a barrel",
        burrow="the clover hill",
        tags={"hog", "transformation"},
    ),
}

REMEDIES = {
    "lullaby": Remedy(
        id="lullaby",
        label="a soft lullaby",
        sense=3,
        power=3,
        use_text="sang a low lullaby the grandmothers used for fussy calves",
        calm_text="The tune floated over {giant}, and its ears drooped. The moon-thistle shine slipped off it like dust off a coat.",
        qa_text="They sang a soft lullaby to calm the giant animal down and let the magic wear off",
        tags={"lullaby"},
    ),
    "cool_cloth": Remedy(
        id="cool_cloth",
        label="a cool mint cloth",
        sense=2,
        power=2,
        use_text="soaked a cloth in cool mint water and laid it gently over the creature's head",
        calm_text="The coolness made the wild shine leave {giant}. Soon only an ordinary {creature} remained, blinking in surprise.",
        qa_text="They used a cool mint cloth to settle the giant animal until it shrank",
        tags={"mint"},
    ),
    "oats_trail": Remedy(
        id="oats_trail",
        label="an oat trail",
        sense=2,
        power=1,
        use_text="shook out a careful trail of oats and backed away step by step",
        calm_text="The smell of oats slowed {giant} for a moment, and some of the magic faded",
        qa_text="They used a trail of oats to lure the creature away from the prize",
        tags={"oats"},
    ),
}

SUSPECTS = {
    "baker": Suspect(
        id="baker",
        label="Mrs. Crumb",
        job="baker",
        alibi_place="the judging tent",
        alibi_witness="the three pie judges",
        busy_text="she had been cutting sample slices for the judges",
        tags={"alibi"},
    ),
    "fiddler": Suspect(
        id="fiddler",
        label="Mr. Reed",
        job="fiddler",
        alibi_place="the bandstand",
        alibi_witness="the whole brass band",
        busy_text="he had been sawing away on his fiddle on the bandstand",
        tags={"alibi"},
    ),
    "gardener": Suspect(
        id="gardener",
        label="Aunt Posy",
        job="gardener",
        alibi_place="the ribbon table",
        alibi_witness="the mayor's daughter",
        busy_text="she had been pinning ribbons at the table by the gate",
        tags={"alibi"},
    ),
}

GIRL_NAMES = ["Mae", "Tilda", "June", "Pearl", "Nell", "Ruby"]
BOY_NAMES = ["Jeb", "Bo", "Cal", "Hank", "Otis", "Finn"]
TRAITS = ["observant", "brave", "steady", "curious", "quick-thinking"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for prize_id, prize in PRIZES.items():
        for creature_id, creature in CREATURES.items():
            if not can_steal(prize, creature):
                continue
            for remedy_id, remedy in REMEDIES.items():
                if remedy.sense >= SENSE_MIN:
                    for suspect_id in SUSPECTS:
                        out.append((prize_id, creature_id, remedy_id, suspect_id))
    return out


@dataclass
class StoryParams:
    prize: str
    creature: str
    remedy: str
    suspect: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    creature = f["creature_cfg"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "alibi", a missing {prize.label}, and a giant transformed {creature.label}.',
        f"Tell a mystery where {hero.id} first suspects a grown-up, then follows clues to discover that magic changed a small {creature.label} into something enormous.",
        "Write a playful county-fair story with huge images, a solved mystery, and an ending where the truth matters more than blame.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    suspect = f["suspect"]
    prize = f["prize_cfg"]
    creature = f["creature_cfg"]
    remedy = f["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id} at the county fair, with {hero.id}'s {parent.label_word} helping them think carefully. They are trying to find {prize.phrase} after it disappears."
        ),
        (
            f"What was the mystery?",
            f"The mystery was that {prize.phrase} vanished from the fair. The children had to figure out who took it and where it went."
        ),
        (
            f"Why did {hero.id} stop blaming {suspect.id}?",
            f"{suspect.id} had an alibi and explained exactly where {suspect.pronoun('subject')} had been. The children also found clue marks that did not belong to a person at all."
        ),
        (
            "What clues helped solve the mystery?",
            f"They found {creature.clue} and a streak of {prize.trail} in the dust. Those clues showed that something animal-sized had become much bigger than normal."
        ),
        (
            "What transformation happened in the story?",
            f"Moon-thistle pollen changed a small {creature.label} into {creature.giant_label}. That transformation is what made the mystery possible, because the animal suddenly became strong enough to drag the prize away."
        ),
    ]
    if f["outcome"] == "recovered":
        qa.append(
            (
                f"How did {hero.id} and {helper.id} get the prize back?",
                f"They {remedy.qa_text.lower()}. Once the creature calmed and shrank, they could roll the prize back safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the missing prize returned and the wrong suspect cleared. The ending proves the children solved the mystery by following clues and respecting the alibi."
            )
        )
    else:
        qa.append(
            (
                f"Did the prize come back exactly the same?",
                f"No. The children got it back, but it had extra bites and scrapes on it. Even so, they still solved the mystery and cleared the innocent suspect."
            )
        )
        qa.append(
            (
                "What lesson did everyone learn?",
                f"They learned that a suspicious look is not proof. The fair did better once people listened to the alibi, checked the clues, and acted calmly around the transformed animal."
            )
        )
    return qa


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"alibi", "mystery", "transformation"} | set(f["creature_cfg"].tags) | set(f["remedy"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        prize="pie",
        creature="rabbit",
        remedy="cool_cloth",
        suspect="baker",
        hero_name="Mae",
        hero_gender="girl",
        helper_name="Jeb",
        helper_gender="boy",
        parent="father",
        trait="observant",
    ),
    StoryParams(
        prize="cheese",
        creature="goat",
        remedy="lullaby",
        suspect="fiddler",
        hero_name="June",
        hero_gender="girl",
        helper_name="Cal",
        helper_gender="boy",
        parent="mother",
        trait="steady",
    ),
    StoryParams(
        prize="melon",
        creature="hog",
        remedy="lullaby",
        suspect="gardener",
        hero_name="Bo",
        hero_gender="boy",
        helper_name="Pearl",
        helper_gender="girl",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        prize="cheese",
        creature="goat",
        remedy="oats_trail",
        suspect="baker",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Otis",
        helper_gender="boy",
        parent="mother",
        trait="curious",
    ),
]


def explain_rejection(prize: Prize, creature: Creature, remedy: Remedy) -> str:
    if not can_steal(prize, creature):
        if prize.id not in creature.likes:
            return (
                f"(No story: a {creature.label} would not plausibly sneak off with {prize.phrase}. "
                f"The culprit must actually want the missing thing.)"
            )
        return (
            f"(No story: {prize.phrase.capitalize()} is too heavy for a {creature.label}, even with moon-thistle magic. "
            f"Pick a stronger transformed animal or a lighter prize.)"
        )
    if remedy.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_remedies()))
        return (
            f"(No story: '{remedy.id}' is too weak or fussy for this world's common-sense gate. "
            f"Try one of these calmer choices: {better}.)"
        )
    return "(No story: that combination does not fit this mystery world.)"


def outcome_of(params: StoryParams) -> str:
    prize = PRIZES[params.prize]
    creature = CREATURES[params.creature]
    remedy = REMEDIES[params.remedy]
    if not can_steal(prize, creature):
        raise StoryError(explain_rejection(prize, creature, remedy))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_rejection(prize, creature, remedy))
    return "recovered" if is_recovered(remedy, creature) else "mended"


ASP_RULES = r"""
likes_prize(C, P) :- likes(C, P).
can_steal(P, C) :- prize(P), creature(C), likes_prize(C, P), weight(P, W), strength(C, S), S >= W.
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(P, C, R, S) :- prize(P), creature(C), remedy(R), suspect(S), can_steal(P, C), sensible(R).

recovered :- chosen_prize(P), chosen_creature(C), chosen_remedy(R),
             can_steal(P, C), power(R, Pow), strength(C, Str), Pow >= Str.
mended :- chosen_prize(P), chosen_creature(C), chosen_remedy(R),
          can_steal(P, C), power(R, Pow), strength(C, Str), Pow < Str.

outcome(recovered) :- recovered.
outcome(mended) :- not recovered, mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("weight", prize_id, prize.weight))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("strength", creature_id, creature.strength))
        for like in sorted(creature.likes):
            lines.append(asp.fact("likes", creature_id, like))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    for suspect_id in SUSPECTS:
        lines.append(asp.fact("suspect", suspect_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_prize", params.prize),
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_remedy", params.remedy),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "alibi" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story missing expected content.")
    if not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: QA generation returned empty results.")


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

    bad = []
    for params in cases:
        try:
            py = outcome_of(params)
            asp_out = asp_outcome(params)
        except StoryError as err:
            rc = 1
            print(f"Unexpected StoryError during verification: {err}")
            continue
        if py != asp_out:
            bad.append((params, py, asp_out))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for params, py, asp_out in bad[:5]:
            print(f"  {params} -> python={py} asp={asp_out}")

    try:
        smoke_test()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery storyworld with an alibi and a transformation."
    )
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.prize and args.creature and args.remedy:
        prize = PRIZES[args.prize]
        creature = CREATURES[args.creature]
        remedy = REMEDIES[args.remedy]
        if not can_steal(prize, creature) or remedy.sense < SENSE_MIN:
            raise StoryError(explain_rejection(prize, creature, remedy))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_rejection(PRIZES[args.prize or "pie"], CREATURES[args.creature or "rabbit"], REMEDIES[args.remedy]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.prize is None or combo[0] == args.prize)
        and (args.creature is None or combo[1] == args.creature)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.suspect is None or combo[3] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    prize, creature, remedy, suspect = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = pick_name(rng, hero_gender)
    helper_name = pick_name(rng, helper_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        prize=prize,
        creature=creature,
        remedy=remedy,
        suspect=suspect,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")

    prize = PRIZES[params.prize]
    creature = CREATURES[params.creature]
    remedy = REMEDIES[params.remedy]
    suspect = SUSPECTS[params.suspect]

    if not can_steal(prize, creature) or remedy.sense < SENSE_MIN:
        raise StoryError(explain_rejection(prize, creature, remedy))

    world = tell(
        prize=prize,
        creature=creature,
        remedy=remedy,
        suspect_cfg=suspect,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (prize, creature, remedy, suspect) combos:\n")
        for prize, creature, remedy, suspect in combos:
            print(f"  {prize:7} {creature:8} {remedy:10} {suspect}")
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
            header = f"### {p.hero_name}: {p.prize} / {p.creature} / {p.remedy} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
