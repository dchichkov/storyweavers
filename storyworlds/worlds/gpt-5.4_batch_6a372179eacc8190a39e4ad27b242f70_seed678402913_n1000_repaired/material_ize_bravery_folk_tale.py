#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py
=============================================================

A standalone storyworld for a tiny folk-tale domain built around bravery and a
marvel that can "material-ize" when a frightened child still steps forward.

The world models a simple old-tale pattern:

    a village needs help
    a child must go somewhere fearful
    the path is blocked by a natural obstacle
    a brave act awakens a fitting wonder that material-izes
    the child returns with help, and the ending image proves the change

The core constraint is deliberately narrow: not every wonder fits every
obstacle, and not every keepsake can awaken every wonder. The Python
reasonableness gate and the ASP twin both enforce that only plausible pairings
become stories.

Run it
------
    python storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py --obstacle ravine --wonder moon_bridge
    python storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py --token seed --obstacle river
    python storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/material_ize_bravery_folk_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives one level deeper than most worlds: storyworlds/worlds/gpt-5.4/.
# So we add the package dir (storyworlds/) to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 2


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
        female = {"girl", "mother", "woman", "grandmother", "queen"}
        male = {"boy", "father", "man", "grandfather", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Quest:
    id: str
    place: str
    need_line: str
    gift: str
    gift_phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    danger_line: str
    crossing_verb: str
    fear_image: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    hint_line: str
    awakens: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    phrase: str
    manifests_line: str
    crossing_line: str
    image_line: str
    kind: str = ""
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear_stirs_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.memes["fear"] < THRESHOLD:
        return out
    sig = ("fear_stirs_bravery", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    out.append("__bravery__")
    return out


def _r_materialize(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    wonder = world.entities.get("wonder")
    token = world.entities.get("token")
    if hero is None or obstacle is None or wonder is None or token is None:
        return out
    if hero.memes["bravery"] < BRAVERY_MIN:
        return out
    if hero.meters["step_taken"] < THRESHOLD:
        return out
    if hero.meters["spoken"] < THRESHOLD:
        return out
    if wonder.attrs.get("kind") != obstacle.attrs.get("requires"):
        return out
    if wonder.id not in token.attrs.get("awakens", set()):
        return out
    sig = ("materialize", wonder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wonder.meters["real"] += 1
    obstacle.meters["passable"] += 1
    out.append("__materialized__")
    return out


CAUSAL_RULES = [
    Rule(name="fear_stirs_bravery", tag="emotional", apply=_r_fear_stirs_bravery),
    Rule(name="materialize", tag="physical", apply=_r_materialize),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_pair(obstacle: Obstacle, token: Token, wonder: Wonder) -> bool:
    return wonder.kind == obstacle.requires and wonder.id in token.awakens


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for obstacle_id, obstacle in OBSTACLES.items():
        for token_id, token in TOKENS.items():
            for wonder_id, wonder in WONDERS.items():
                if valid_pair(obstacle, token, wonder):
                    combos.append((obstacle_id, token_id, wonder_id))
    return combos


def explain_rejection(obstacle: Obstacle, token: Token, wonder: Wonder) -> str:
    if wonder.kind != obstacle.requires:
        return (
            f"(No story: {wonder.phrase} does not solve {obstacle.phrase}. "
            f"That obstacle needs a wonder of kind '{obstacle.requires}', not '{wonder.kind}'.)"
        )
    if wonder.id not in token.awakens:
        allowed = ", ".join(sorted(token.awakens))
        return (
            f"(No story: {token.phrase} cannot awaken {wonder.phrase}. "
            f"It can only awaken: {allowed}.)"
        )
    return "(No story: this obstacle, token, and wonder do not form a sensible folk-tale path.)"


def predict_crossing(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["spoken"] += 1
    hero.meters["step_taken"] += 1
    propagate(sim, narrate=False)
    return sim.get("obstacle").meters["passable"] >= THRESHOLD


def village_need(world: World, elder: Entity, quest: Quest) -> None:
    world.say(
        f"In the old days, in {quest.place}, there lived a child named {world.get('hero').id}. "
        f"The child was small, but the village had already learned that a small heart may hold great courage."
    )
    world.say(
        f"One evening, {quest.need_line} So the elders spoke in low voices of {quest.gift_phrase}, "
        f"which could be found only beyond the dangerous way."
    )
    world.say(
        f'{elder.id}, the oldest keeper of tales, said, "{quest.gift_phrase.capitalize()} lies past {world.get("obstacle").label}, '
        f'and that road yields only to the brave."'
    )


def receive_token(world: World, elder: Entity, token: Token) -> None:
    hero = world.get("hero")
    hero.attrs["token"] = token.id
    world.say(
        f"Then {elder.id} placed {token.phrase} in {hero.pronoun('possessive')} palm and whispered, "
        f'"When fear presses close, speak kindly to your own heart and let the road material-ize the right way."'
    )
    world.say(token.hint_line)


def walk_to_obstacle(world: World, obstacle: Obstacle) -> None:
    hero = world.get("hero")
    hero.meters["journey"] += 1
    world.say(
        f"Before dawn, {hero.id} walked alone until {obstacle.phrase} rose ahead. "
        f"{obstacle.danger_line}"
    )
    hero.memes["fear"] += 1
    world.say(obstacle.fear_image)
    propagate(world, narrate=False)


def hesitate(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"For a little while, {hero.id} stood still. {hero.pronoun().capitalize()} could hear {hero.pronoun('possessive')} own breathing, "
        f"and the task seemed bigger than the child who had come to meet it."
    )


def choose_bravery(world: World, token: Token) -> None:
    hero = world.get("hero")
    hero.meters["spoken"] += 1
    hero.meters["step_taken"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"Yet {hero.id} curled {hero.pronoun('possessive')} fingers around {token.label} and said, "
        f'"I am afraid, but I will still go on." Then {hero.pronoun()} took one true step forward.'
    )
    propagate(world, narrate=False)


def materialize_wonder(world: World, wonder: Wonder) -> None:
    if world.get("wonder").meters["real"] < THRESHOLD:
        return
    world.say(wonder.manifests_line)
    world.say(wonder.image_line)


def cross(world: World, obstacle: Obstacle, wonder: Wonder, quest: Quest) -> None:
    hero = world.get("hero")
    hero.meters["crossed"] += 1
    world.say(wonder.crossing_line)
    world.say(
        f"On the far side, {hero.id} found {quest.gift_phrase} and carried {quest.gift} home before the sun was high."
    )


def heal_and_end(world: World, quest: Quest) -> None:
    hero = world.get("hero")
    elder = world.get("elder")
    elder.memes["gratitude"] += 1
    hero.memes["joy"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"The gift did its work. {quest.need_line.replace('One evening, ', '').replace('That winter, ', '') if False else ''}"
    )
    world.say(
        f"When {hero.id} returned, the village lamps were still pale with morning, and soon {quest.gift_phrase} had set things right."
    )
    world.say(
        f"{elder.id} bowed {elder.pronoun('possessive')} head and said, "
        f'"Bravery is not a heart with no fear in it. Bravery is a heart that walks anyway."'
    )
    world.say(quest.ending_image)


def tell(
    quest: Quest,
    obstacle: Obstacle,
    token: Token,
    wonder: Wonder,
    hero_name: str = "Anya",
    hero_type: str = "girl",
    elder_name: str = "Old Mira",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="elder"))
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            role="obstacle",
            attrs={"requires": obstacle.requires},
            tags=set(obstacle.tags),
        )
    )
    world.add(
        Entity(
            id="token",
            kind="thing",
            type="token",
            label=token.label,
            phrase=token.phrase,
            role="token",
            attrs={"awakens": set(token.awakens)},
            tags=set(token.tags),
        )
    )
    world.add(
        Entity(
            id="wonder",
            kind="thing",
            type="wonder",
            label=wonder.label,
            phrase=wonder.phrase,
            role="wonder",
            attrs={"kind": wonder.kind},
            tags=set(wonder.tags),
        )
    )

    hero.id = hero_name
    elder.id = elder_name
    world.entities[hero_name] = world.entities.pop("hero")
    world.entities[elder_name] = world.entities.pop("elder")
    world.entities["hero"] = world.entities[hero_name]
    world.entities["elder"] = world.entities[elder_name]

    world.facts.update(
        quest=quest,
        obstacle_cfg=obstacle,
        token_cfg=token,
        wonder_cfg=wonder,
        hero=world.get("hero"),
        elder=world.get("elder"),
    )

    village_need(world, world.get("elder"), quest)
    world.para()
    receive_token(world, world.get("elder"), token)
    walk_to_obstacle(world, obstacle)
    hesitate(world)
    world.para()
    choose_bravery(world, token)
    materialize_wonder(world, wonder)
    if world.get("obstacle").meters["passable"] >= THRESHOLD:
        cross(world, obstacle, wonder, quest)
    else:
        raise StoryError("The chosen folk-tale path did not become passable after the brave act.")
    world.para()
    heal_and_end(world, quest)

    world.facts.update(
        materialized=world.get("wonder").meters["real"] >= THRESHOLD,
        crossed=world.get("hero").meters["crossed"] >= THRESHOLD,
        brave_enough=world.get("hero").memes["bravery"] >= BRAVERY_MIN,
    )
    return world


QUESTS = {
    "healing": Quest(
        id="healing",
        place="a pine-ringed village",
        need_line="One evening, the baker's youngest child grew sick, and no warm herb in the village could ease the fever.",
        gift="the silverleaf herb",
        gift_phrase="the silverleaf herb",
        ending_image="That night, the oven smoke rose straight and calm, and every house window glowed as if the village itself had let out a long breath.",
        tags={"healing", "village"},
    ),
    "rain": Quest(
        id="rain",
        place="a thirsty hill village",
        need_line="That summer, the wells went shallow, and the fields bent gray under the sun.",
        gift="the cloud-seed pearl",
        gift_phrase="the cloud-seed pearl",
        ending_image="By dusk, rain drummed softly on the roofs, and the children set out bowls just to hear the water sing inside them.",
        tags={"rain", "village"},
    ),
    "light": Quest(
        id="light",
        place="a valley of orchards",
        need_line="One evening, a strange dimness fell over the valley, and even noon looked like late twilight beneath the trees.",
        gift="the dawn ember",
        gift_phrase="the dawn ember",
        ending_image="Before bed, every apple leaf shone with a small gold edge, and even the narrow paths looked friendly again.",
        tags={"light", "village"},
    ),
}

OBSTACLES = {
    "river": Obstacle(
        id="river",
        label="the black river",
        phrase="the black river",
        danger_line="Its water ran quick as torn silk, and no ford could be seen.",
        crossing_verb="crossed",
        fear_image="Mist brushed the child's ankles, and the sound of the current made the dark seem even deeper.",
        requires="bridge",
        tags={"river", "water"},
    ),
    "ravine": Obstacle(
        id="ravine",
        label="the starless ravine",
        phrase="the starless ravine",
        danger_line="It split the earth like a mouth, and pebbles clicked for a long time before they found the bottom.",
        crossing_verb="crossed",
        fear_image="The wind came up from below in cold breaths, as if the hollow were whispering, Turn back.",
        requires="bridge",
        tags={"ravine", "heights"},
    ),
    "thorns": Obstacle(
        id="thorns",
        label="the thorn gate",
        phrase="the thorn gate",
        danger_line="Bramble canes were woven so thickly that even sunlight had trouble passing through.",
        crossing_verb="passed through",
        fear_image="The thorns scraped together like tiny teeth, and the narrow gap beyond them looked far away.",
        requires="opening",
        tags={"thorns", "path"},
    ),
}

TOKENS = {
    "bell": Token(
        id="bell",
        label="a tin courage-bell",
        phrase="a tin courage-bell",
        hint_line="The bell was light and plain, but old people said it only sang for those who walked before the shaking in their knees had stopped.",
        awakens={"stone_bridge", "moon_bridge"},
        tags={"bell", "courage"},
    ),
    "lantern": Token(
        id="lantern",
        label="a blue glass lantern",
        phrase="a blue glass lantern",
        hint_line="Its little flame did not fight the dark. It simply stayed gentle and true, which is another kind of courage.",
        awakens={"moon_bridge", "rose_door"},
        tags={"lantern", "light"},
    ),
    "seed": Token(
        id="seed",
        label="a warm sleeping seed",
        phrase="a warm sleeping seed",
        hint_line="It seemed no larger than a raindrop, yet it held a patient kind of strength, waiting for a brave hand to trust it.",
        awakens={"rose_door"},
        tags={"seed", "growth"},
    ),
}

WONDERS = {
    "stone_bridge": Wonder(
        id="stone_bridge",
        label="a bridge of stepping stones",
        phrase="a bridge of stepping stones",
        manifests_line="At once, round stones rose from the dark below, one after another, until a narrow bridge stood where there had been nothing.",
        crossing_line="The child crossed from stone to stone, not because fear had vanished, but because each step taught the next one how to be taken.",
        image_line="The wet stones shone like old coins in moonlight.",
        kind="bridge",
        tags={"bridge", "stone"},
    ),
    "moon_bridge": Wonder(
        id="moon_bridge",
        label="a moonlit bridge",
        phrase="a moonlit bridge",
        manifests_line="Then a pale bridge of light unfolded through the air, bright as milk and steady as oak.",
        crossing_line="The child walked over the shining span with careful feet, and the darkness beneath could do no more than grumble.",
        image_line="Its rails were woven of silver mist, and they hummed like a quiet song.",
        kind="bridge",
        tags={"bridge", "light"},
    ),
    "rose_door": Wonder(
        id="rose_door",
        label="a living rose-door",
        phrase="a living rose-door",
        manifests_line="The tangled canes loosened, curved, and bloomed, making an arched door of red roses where the wall of thorns had stood.",
        crossing_line="The child passed through the flowered opening, and even the thorns bent away as if they had remembered better manners.",
        image_line="Petals drifted down around the path like soft red snow.",
        kind="opening",
        tags={"flowers", "opening"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Tala", "Iva", "Lina", "Sana", "Yara", "Neta"]
BOY_NAMES = ["Milo", "Tarin", "Ivo", "Niko", "Pavel", "Soren", "Darin", "Luka"]
ELDER_NAMES = ["Old Mira", "Grandmother Vesna", "Old Rowan", "Auntie Bryn", "Elder Lark"]


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    token: str
    wonder: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        quest="healing",
        obstacle="river",
        token="bell",
        wonder="stone_bridge",
        hero_name="Anya",
        hero_gender="girl",
        elder_name="Old Mira",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="rain",
        obstacle="ravine",
        token="lantern",
        wonder="moon_bridge",
        hero_name="Milo",
        hero_gender="boy",
        elder_name="Old Rowan",
        elder_type="grandfather",
    ),
    StoryParams(
        quest="light",
        obstacle="thorns",
        token="seed",
        wonder="rose_door",
        hero_name="Tala",
        hero_gender="girl",
        elder_name="Auntie Bryn",
        elder_type="woman",
    ),
    StoryParams(
        quest="healing",
        obstacle="thorns",
        token="lantern",
        wonder="rose_door",
        hero_name="Luka",
        hero_gender="boy",
        elder_name="Grandmother Vesna",
        elder_type="grandmother",
    ),
]


KNOWLEDGE = {
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge helps you go safely from one side to the other over something hard to cross, like water or a deep gap.",
        )
    ],
    "river": [
        (
            "Why can a river be dangerous to cross?",
            "A river can be dangerous because moving water pushes hard and can carry you away if it is too deep or too fast.",
        )
    ],
    "ravine": [
        (
            "What is a ravine?",
            "A ravine is a deep crack or valley in the ground with steep sides. It can be hard and scary to cross.",
        )
    ],
    "thorns": [
        (
            "What are thorns?",
            "Thorns are sharp points that grow on some plants. They help protect the plant, but they can scratch your skin.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp with a cover around the light. People carry it so they can see in the dark.",
        )
    ],
    "seed": [
        (
            "What grows from a seed?",
            "A seed can grow into a plant when it has the right help, like soil, water, warmth, and time.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel afraid. It does not mean never feeling fear.",
        )
    ],
    "healing": [
        (
            "What does healing mean?",
            "Healing means getting better after being hurt or sick. Sometimes bodies heal with rest, and stories imagine healing with magic too.",
        )
    ],
    "rain": [
        (
            "Why is rain good for plants?",
            "Rain gives plants water so they can keep growing. Dry fields and gardens need water to stay alive.",
        )
    ],
    "light": [
        (
            "Why do people need light?",
            "Light helps people see where they are going and what is around them. It can also make a place feel safer and warmer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bravery", "bridge", "river", "ravine", "thorns", "lantern", "seed", "healing", "rain", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    obstacle = f["obstacle_cfg"]
    token = f["token_cfg"]
    wonder = f["wonder_cfg"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the word "material-ize" and teaches bravery.',
        f"Tell a folk tale about a brave child named {hero.id} who must go past {obstacle.label} to bring back {quest.gift_phrase}.",
        f"Write a fairy-tale story where {token.phrase} helps {wonder.phrase} material-ize after a child chooses courage over turning back.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    obstacle = f["obstacle_cfg"]
    token = f["token_cfg"]
    wonder = f["wonder_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child from {quest.place}, and {elder.id}, who trusted {hero.pronoun('object')} with an important journey.",
        ),
        (
            f"Why did {hero.id} have to go on the journey?",
            f"{hero.id} had to go because the village needed {quest.gift_phrase}. The need was serious, so someone had to face the dangerous road.",
        ),
        (
            f"What was scary about {obstacle.label}?",
            f"{obstacle.label.capitalize()} was scary because {obstacle.danger_line.lower()} {obstacle.fear_image} Those details show why bravery mattered instead of simple luck.",
        ),
        (
            f"What did {elder.id} give {hero.id}?",
            f"{elder.id} gave {hero.id} {token.phrase}. It was not just a keepsake, because it helped the right wonder answer a brave step.",
        ),
        (
            f"How did the wonder material-ize?",
            f"It material-ized when {hero.id} admitted being afraid and still stepped forward. The brave choice, together with {token.phrase}, awakened {wonder.phrase}.",
        ),
        (
            f"What does the story teach about bravery?",
            f"The story teaches that bravery is not the same as having no fear. {hero.id} was afraid first, and then chose to keep going anyway.",
        ),
    ]
    if f.get("crossed"):
        qa.append(
            (
                f"What happened after the wonder appeared?",
                f"After {wonder.phrase} appeared, {hero.id} got safely past {obstacle.label} and brought back {quest.gift_phrase}. The village changed because the journey succeeded.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"bravery"}
    tags |= set(f["quest"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["token_cfg"].tags)
    tags |= set(f["wonder_cfg"].tags)
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
    for key, ent in world.entities.items():
        if key in {"hero", "elder"}:
            continue
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: sorted(v) if isinstance(v, set) else v for k, v in ent.attrs.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {key:10} ({ent.type:9}) {' '.join(bits)}")
    for key in ("hero", "elder"):
        ent = world.entities.get(key)
        if ent is None:
            continue
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {key:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(O, T, W) :- obstacle(O), token(T), wonder(W), requires(O, K), kind(W, K), awakens(T, W).

brave_enough :- fear_stirs, bravery_min(M), bravery(1), M <= 1.
brave_enough :- fear_stirs, bravery_min(2).
fear_stirs.
spoken.
step_taken.

materialized :- brave_enough, spoken, step_taken, chosen_obstacle(O), chosen_token(T), chosen_wonder(W),
                requires(O, K), kind(W, K), awakens(T, W).

outcome(crossed) :- materialized.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("requires", oid, obstacle.requires))
    for tid, token in TOKENS.items():
        lines.append(asp.fact("token", tid))
        for wid in sorted(token.awakens):
            lines.append(asp.fact("awakens", tid, wid))
    for wid, wonder in WONDERS.items():
        lines.append(asp.fact("wonder", wid))
        lines.append(asp.fact("kind", wid, wonder.kind))
    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    lines.append(asp.fact("bravery", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_crossable(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_token", params.token),
            asp.fact("chosen_wonder", params.wonder),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return ("crossed",) in atoms


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    token = TOKENS[params.token]
    wonder = WONDERS[params.wonder]
    return "crossed" if valid_pair(obstacle, token, wonder) else "blocked"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(smoke_cases[0])
        if not sample.story or "material-ize" not in sample.story:
            raise StoryError("Smoke test story did not render correctly.")
        print("OK: smoke generation rendered a normal story.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    mismatch = 0
    for params in smoke_cases:
        py = outcome_of(params)
        asp_ok = asp_crossable(params)
        asp_out = "crossed" if asp_ok else "blocked"
        if py != asp_out:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(smoke_cases)} curated scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(smoke_cases)} curated outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld sketch: a brave child in a folk tale makes the right wonder material-ize."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid obstacle/token/wonder combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.token and args.wonder:
        obstacle = OBSTACLES[args.obstacle]
        token = TOKENS[args.token]
        wonder = WONDERS[args.wonder]
        if not valid_pair(obstacle, token, wonder):
            raise StoryError(explain_rejection(obstacle, token, wonder))

    combos = [
        combo
        for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.token is None or combo[1] == args.token)
        and (args.wonder is None or combo[2] == args.wonder)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, token_id, wonder_id = rng.choice(sorted(combos))
    quest_id = args.quest or rng.choice(sorted(QUESTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(hero_pool)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "woman", "man"])

    return StoryParams(
        quest=quest_id,
        obstacle=obstacle_id,
        token=token_id,
        wonder=wonder_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.token not in TOKENS:
        raise StoryError(f"(Unknown token: {params.token})")
    if params.wonder not in WONDERS:
        raise StoryError(f"(Unknown wonder: {params.wonder})")

    obstacle = OBSTACLES[params.obstacle]
    token = TOKENS[params.token]
    wonder = WONDERS[params.wonder]
    if not valid_pair(obstacle, token, wonder):
        raise StoryError(explain_rejection(obstacle, token, wonder))

    world = tell(
        quest=QUESTS[params.quest],
        obstacle=obstacle,
        token=token,
        wonder=wonder,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} valid (obstacle, token, wonder) combos:\n")
        for obstacle_id, token_id, wonder_id in combos:
            print(f"  {obstacle_id:8} {token_id:8} {wonder_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.obstacle} / {p.token} / {p.wonder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
