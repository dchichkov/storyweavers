#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py
==============================================================================

A small bedtime-story world about a child and a loyal hound who go on a gentle
quest to quiet a frightening noise on a moonlit hill. The village thinks the
noise sounds barbaric, but the quest reveals a lonely giant who is missing the
one bedtime thing that helps him settle down.

The world model keeps track of:
- physical meters: progress, found, crossed, quiet, etc.
- emotional memes: fear, courage, hope, relief, love, sleepiness

The story shape is always:
1. A soft bedtime setup with a disturbing night sound.
2. A quest with a real obstacle that must be matched by a sensible tool.
3. The hound helps find the missing item.
4. The child returns it to the giant.
5. The hill grows quiet and the village goes to sleep.

Run it
------
    python storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py --qa
    python storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/hound_barbaric_quest_happy_ending_bedtime_story.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        dog = {"hound", "dog", "puppy"}
        giant = {"giant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in giant:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Hill:
    id: str
    label: str
    path_text: str
    sky_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    danger: str
    crossing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    hide_spot: str
    soothe_text: str
    ending_image: str
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


def _r_progress_grows_hope(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    giant = world.entities.get("giant")
    if child is None or giant is None:
        return out
    if child.meters["crossed"] >= THRESHOLD and ("hope",) not in world.fired:
        world.fired.add(("hope",))
        child.memes["courage"] += 1
        child.memes["hope"] += 1
        giant.memes["hope"] += 1
    return out


def _r_found_item_lifts_hearts(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    hound = world.entities.get("hound")
    giant = world.entities.get("giant")
    item = world.entities.get("item")
    if child is None or hound is None or giant is None or item is None:
        return out
    if item.meters["found"] >= THRESHOLD and ("found",) not in world.fired:
        world.fired.add(("found",))
        child.memes["relief"] += 1
        hound.memes["pride"] += 1
        giant.memes["hope"] += 1
    return out


def _r_return_quiets_hill(world: World) -> list[str]:
    out: list[str] = []
    giant = world.entities.get("giant")
    hill = world.entities.get("place")
    village = world.entities.get("village")
    item = world.entities.get("item")
    if giant is None or hill is None or village is None or item is None:
        return out
    if item.meters["returned"] >= THRESHOLD and ("quiet",) not in world.fired:
        world.fired.add(("quiet",))
        giant.meters["quiet"] += 1
        hill.meters["quiet"] += 1
        village.meters["quiet"] += 1
        giant.memes["gratitude"] += 1
        giant.memes["sleepiness"] += 1
        village.memes["sleepiness"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="progress_hope", tag="quest", apply=_r_progress_grows_hope),
    Rule(name="found_relief", tag="quest", apply=_r_found_item_lifts_hearts),
    Rule(name="return_quiet", tag="resolution", apply=_r_return_quiets_hill),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


HILLS = {
    "moon_hill": Hill(
        id="moon_hill",
        label="Moon Hill",
        path_text="a pale path that curled between sleepy stones",
        sky_text="The moon hung over Moon Hill like a silver button on a blue blanket.",
        tags={"hill", "moon"},
    ),
    "cedar_knoll": Hill(
        id="cedar_knoll",
        label="Cedar Knoll",
        path_text="a needle-soft trail under the cedar trees",
        sky_text="The moonlight slipped between the cedar branches and silvered the knoll.",
        tags={"hill", "trees"},
    ),
    "moss_rise": Hill(
        id="moss_rise",
        label="Moss Rise",
        path_text="a soft green track that glimmered with dew",
        sky_text="The sky above Moss Rise was deep and velvety, full of slow stars.",
        tags={"hill", "moss"},
    ),
}

OBSTACLES = {
    "brambles": Obstacle(
        id="brambles",
        label="brambles",
        scene="a tangle of moonlit brambles lay across the path",
        danger="the thorns could catch on sleeves and scratch small hands",
        crossing="past the thorny patch",
        tags={"brambles", "thorns"},
    ),
    "brook": Obstacle(
        id="brook",
        label="brook",
        scene="a cold brook ribboned across the path",
        danger="the stones looked slick, and the water whispered around them",
        crossing="over the shining brook",
        tags={"brook", "water"},
    ),
    "dark_wood": Obstacle(
        id="dark_wood",
        label="dark wood",
        scene="a pocket of dark wood swallowed the path ahead",
        danger="the shadows made every stump look bigger than it was",
        crossing="through the dim wood",
        tags={"dark", "wood"},
    ),
}

TOOLS = {
    "mittens": Tool(
        id="mittens",
        label="mittens",
        phrase="thick wool mittens",
        helps_with="brambles",
        use_text="The mittens let the child bend the thorny stems aside without getting scratched.",
        tags={"mittens", "warm"},
    ),
    "stepping_stones": Tool(
        id="stepping_stones",
        label="stepping stones",
        phrase="three flat stepping stones in a little sack",
        helps_with="brook",
        use_text="One by one, the child set down the stepping stones and made a tidy path across the water.",
        tags={"stones", "brook"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        helps_with="dark_wood",
        use_text="The lantern poured a warm circle of light over the path, and the shadows stopped looking so grand.",
        tags={"lantern", "light"},
    ),
}

ITEMS = {
    "bell": LostItem(
        id="bell",
        label="moon bell",
        phrase="a small moon bell on a blue ribbon",
        hide_spot="under a fern where the silver ribbon had caught",
        soothe_text="When the giant rang the moon bell, it gave one soft, sleepy note instead of a crashing clang.",
        ending_image="The bell's quiet chime floated over the hill like a tiny star learning to sing softly.",
        tags={"bell", "bedtime"},
    ),
    "blanket": LostItem(
        id="blanket",
        label="cloud blanket",
        phrase="a cloud-patterned blanket",
        hide_spot="behind a stump where the wind had folded it into the grass",
        soothe_text="When the giant wrapped the cloud blanket around his shoulders, his stompy shivers melted away.",
        ending_image="The blanket puffed around the giant like a piece of night sky tucked gently into place.",
        tags={"blanket", "bedtime"},
    ),
    "flute": LostItem(
        id="flute",
        label="reed flute",
        phrase="a little reed flute",
        hide_spot="in a patch of moss where it had rolled and hidden",
        soothe_text="When the giant blew the reed flute, the note came out low and warm, more like a yawn than a shout.",
        ending_image="The flute's soft note drifted over the roofs like a long, kind sigh.",
        tags={"music", "bedtime"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Lucy", "Ivy", "June"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Finn", "Theo", "Sam", "Eli", "Noah"]
HOUND_NAMES = ["Bramble", "Moss", "Tumble", "Pip", "Rufus", "Clover"]
TRAITS = ["gentle", "brave", "quiet", "patient", "kind", "steady"]


def matching_tool(obstacle_id: str) -> Optional[str]:
    for tool_id, tool in TOOLS.items():
        if tool.helps_with == obstacle_id:
            return tool_id
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hill_id in HILLS:
        for obstacle_id in OBSTACLES:
            for item_id in ITEMS:
                if matching_tool(obstacle_id):
                    combos.append((hill_id, obstacle_id, item_id))
    return combos


@dataclass
class StoryParams:
    hill: str
    obstacle: str
    tool: str
    item: str
    child_name: str
    child_gender: str
    hound_name: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hill="moon_hill",
        obstacle="brambles",
        tool="mittens",
        item="bell",
        child_name="Lila",
        child_gender="girl",
        hound_name="Bramble",
        parent="mother",
        trait="gentle",
    ),
    StoryParams(
        hill="cedar_knoll",
        obstacle="brook",
        tool="stepping_stones",
        item="blanket",
        child_name="Owen",
        child_gender="boy",
        hound_name="Moss",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        hill="moss_rise",
        obstacle="dark_wood",
        tool="lantern",
        item="flute",
        child_name="Nora",
        child_gender="girl",
        hound_name="Pip",
        parent="mother",
        trait="brave",
    ),
]


def explain_rejection(obstacle_id: str, tool_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    want = matching_tool(obstacle_id)
    wanted = TOOLS[want].label if want in TOOLS else "a matching tool"
    return (
        f"(No story: {tool.label} is not a sensible way past the {obstacle.label}. "
        f"This quest needs {wanted} for that obstacle.)"
    )


def predict_crossing(world: World, obstacle_id: str, tool_id: str) -> dict:
    sim = world.copy()
    if tool_id == matching_tool(obstacle_id):
        sim.get("child").meters["crossed"] += 1
        sim.get("hound").meters["crossed"] += 1
        propagate(sim, narrate=False)
    return {
        "crossed": sim.get("child").meters["crossed"] >= THRESHOLD,
        "hope": sim.get("child").memes["hope"],
    }


def introduce(world: World, hill: Hill, child: Entity, hound: Entity, parent: Entity) -> None:
    world.say(hill.sky_text)
    world.say(
        f"In a cottage below the hill lived {child.id}, a {child.attrs['trait']} little {child.type}, "
        f"and {hound.id}, {child.pronoun('possessive')} loyal hound with velvet ears."
    )
    world.say(
        f"That evening, just as {parent.label_word} was smoothing the blankets, "
        f"a great CLANG-CLANG rolled down from {hill.label}."
    )


def frighten(world: World, hill: Hill, child: Entity, hound: Entity) -> None:
    child.memes["fear"] += 1
    hound.memes["alert"] += 1
    world.say(
        f"The sound was so rough and wild that the grown-ups called it barbaric, "
        f"and even the windowpanes gave a tiny shiver."
    )
    world.say(
        f"{child.id} sat up in bed while {hound.id} lifted his nose. "
        f'"That does not sound sleepy at all," {child.id} whispered.'
    )
    world.facts["noise_place"] = hill.label


def choose_quest(world: World, child: Entity, hound: Entity, parent: Entity, hill: Hill) -> None:
    child.memes["courage"] += 1
    child.memes["care"] += 1
    hound.memes["bond"] += 1
    world.say(
        f'{parent.label_word.capitalize()} tucked a shawl around {child.id} and said, '
        f'"Somebody on {hill.label} must need help."'
    )
    world.say(
        f"{child.id} nodded. {hound.id} thumped his tail once, as if he had been waiting for a quest all evening."
    )


def set_out(world: World, hill: Hill, obstacle: Obstacle, tool: Tool, child: Entity, hound: Entity) -> None:
    world.say(
        f"So the child pulled on slippers, took {tool.phrase}, and stepped onto {hill.path_text} with {hound.id} at {child.pronoun('possessive')} side."
    )
    world.say(
        f"Before long, {obstacle.scene}. {obstacle.danger}."
    )


def cross_obstacle(world: World, obstacle: Obstacle, tool: Tool, child: Entity, hound: Entity) -> None:
    pred = predict_crossing(world, obstacle.id, tool.id)
    world.facts["predicted_crossed"] = pred["crossed"]
    child.meters["crossed"] += 1
    hound.meters["crossed"] += 1
    propagate(world, narrate=False)
    world.say(tool.use_text)
    world.say(
        f"Together, child and hound went {obstacle.crossing}, and the quest no longer felt quite so big."
    )


def giant_reveal(world: World, hill: Hill, child: Entity, hound: Entity, giant: Entity, item: LostItem) -> None:
    giant.memes["lonely"] += 1
    world.say(
        f"At the top of {hill.label}, they found no monster army at all. They found a giant sitting on a stone, blinking sadly into the moonlight."
    )
    world.say(
        f'"I am sorry for the dreadful racket," the giant rumbled. "I lost my {item.label}, and without it I do not know how to settle for sleep."'
    )
    world.say(
        f"{hound.id} walked right up and rested his chin on the giant's knee. That was when {child.id} knew the giant was more lonely than frightening."
    )


def search(world: World, item: LostItem, child: Entity, hound: Entity) -> None:
    hound.meters["sniffing"] += 1
    child.memes["focus"] += 1
    world.say(
        f'"Can your good nose help us?" {child.id} asked. {hound.id} answered with a quick sniff, then another, then a determined trot through the grass.'
    )
    world.say(
        f"He led the child to {item.hide_spot}. There lay {item.phrase}, cool with dew and moonlight."
    )
    world.get("item").meters["found"] += 1
    propagate(world, narrate=False)


def return_item(world: World, item: LostItem, child: Entity, giant: Entity) -> None:
    world.get("item").meters["returned"] += 1
    propagate(world, narrate=False)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    giant.memes["lonely"] = 0.0
    world.say(
        f"{child.id} carried the {item.label} back in both hands and gave it to the giant."
    )
    world.say(item.soothe_text)


def resolution(world: World, hill: Hill, child: Entity, hound: Entity, giant: Entity, item: LostItem, parent: Entity) -> None:
    child.memes["love"] += 1
    hound.memes["joy"] += 1
    giant.memes["gratitude"] += 1
    world.say(
        f'The giant let out a deep, happy breath. "You and your hound have saved bedtime on this hill," he said.'
    )
    world.say(
        f"{item.ending_image} The night changed at once. The rough, barbaric noise was gone, and in its place came a hush so soft that even the leaves seemed to settle down."
    )
    world.say(
        f"When {child.id} and {hound.id} walked home, the cottage windows were dark and peaceful. {parent.label_word.capitalize()} opened the door with a sleepy smile."
    )
    world.say(
        f"Soon the child was back in bed, the hound curled warm at the foot of the quilt, and somewhere above them the giant on {hill.label} finally drifted into a kind, quiet sleep."
    )


def tell(
    hill: Hill,
    obstacle: Obstacle,
    tool: Tool,
    item_cfg: LostItem,
    child_name: str,
    child_gender: str,
    hound_name: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"trait": trait},
    ))
    hound = world.add(Entity(
        id="hound",
        kind="character",
        type="hound",
        label=hound_name,
        phrase=hound_name,
        role="hound",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    giant = world.add(Entity(
        id="giant",
        kind="character",
        type="giant",
        label="the giant",
        role="giant",
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="hill",
        label=hill.label,
        role="place",
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the village",
        role="village",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="item",
    ))

    world.facts["child_name"] = child_name
    world.facts["hound_name"] = hound_name
    world.facts["hill"] = hill
    world.facts["obstacle"] = obstacle
    world.facts["tool"] = tool
    world.facts["item_cfg"] = item_cfg

    introduce(world, hill, child, hound, parent)
    frighten(world, hill, child, hound)

    world.para()
    choose_quest(world, child, hound, parent, hill)
    set_out(world, hill, obstacle, tool, child, hound)
    cross_obstacle(world, obstacle, tool, child, hound)

    world.para()
    giant_reveal(world, hill, child, hound, giant, item_cfg)
    search(world, item_cfg, child, hound)
    return_item(world, item_cfg, child, giant)

    world.para()
    resolution(world, hill, child, hound, giant, item_cfg, parent)

    world.facts.update(
        child=child,
        hound=hound,
        parent=parent,
        giant=giant,
        place=place,
        village=village,
        item=item,
        crossed=child.meters["crossed"] >= THRESHOLD,
        found=item.meters["found"] >= THRESHOLD,
        returned=item.meters["returned"] >= THRESHOLD,
        quiet=place.meters["quiet"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "hound": [
        (
            "What is a hound?",
            "A hound is a kind of dog known for using its nose very well. Many hounds can follow a smell trail better than people can.",
        )
    ],
    "barbaric": [
        (
            "What does barbaric mean?",
            "Barbaric means very rough, wild, or harsh. In this story it describes the noisy clanging that sounded scary at first.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. Someone goes out to find, fix, or help something important.",
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in the dark?",
            "A lantern makes a steady light, so you can see the path and stop guessing at shadows. That can make a dark place feel safer.",
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of moving water. It can be shallow, but slippery stones can still make crossing tricky.",
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny plants with long stems. They can catch on clothes and scratch bare skin.",
        )
    ],
    "bedtime": [
        (
            "Why do quiet sounds help at bedtime?",
            "Quiet, gentle sounds can help bodies slow down and feel calm. Loud crashing sounds make it harder to rest.",
        )
    ],
    "kindness": [
        (
            "Why is kindness useful on a quest?",
            "Kindness helps you notice what someone really needs. It can turn a frightening problem into something you can gently solve.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    hound = world.facts["hound"]
    hill = world.facts["hill"]
    item_cfg = world.facts["item_cfg"]
    obstacle = world.facts["obstacle"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "hound" and "barbaric" and has a happy quest ending.',
        f"Tell a gentle quest story where a little {child.type} and a loyal hound climb {hill.label} to find out why a barbaric noise is keeping everyone awake.",
        f"Write a cozy night story where a child crosses {obstacle.label}, helps a lonely giant find a missing {item_cfg.label}, and brings bedtime back to the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    hound = world.facts["hound"]
    parent = world.facts["parent"]
    giant = world.facts["giant"]
    hill = world.facts["hill"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    item_cfg = world.facts["item_cfg"]

    name = world.facts["child_name"]
    dog = world.facts["hound_name"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a little {child.type}, and {dog}, the loyal hound. They go together on a nighttime quest up {hill.label}.",
        ),
        (
            "Why did the child leave bed?",
            f"{name} heard a loud, rough noise rolling down from {hill.label}. The sound seemed barbaric and was keeping everyone from settling to sleep.",
        ),
        (
            f"What problem was waiting on {hill.label}?",
            f"A lonely giant had lost his {item_cfg.label}. Without it, he did not know how to calm himself at bedtime, so he made a harsh clanging noise instead.",
        ),
        (
            f"How did {name} get past the {obstacle.label}?",
            f"{name} used {tool.phrase} to get safely past the {obstacle.label}. That sensible tool matched the danger, which let the quest keep going.",
        ),
        (
            f"How did the hound help on the quest?",
            f"{dog} used his nose to search the grass and led {name} to the missing {item_cfg.label}. The hound mattered because he could find what the child could not see alone.",
        ),
        (
            "How did the story end?",
            f"{name} returned the {item_cfg.label} to the giant, and the harsh noise stopped. Then the hill, the village, and the little cottage all grew quiet enough for sleep.",
        ),
    ]
    if world.facts.get("quiet"):
        qa.append(
            (
                f"Was {name}'s {pw} angry about the quest?",
                f"No. {pw.capitalize()} understood that someone on the hill needed help and welcomed {name} home with a sleepy smile. The ending shows the quest brought peace instead of trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hound", "barbaric", "quest", "bedtime", "kindness"}
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    if obstacle.id == "brook":
        tags.add("brook")
    if obstacle.id == "brambles":
        tags.add("brambles")
    if tool.id == "lantern":
        tags.add("lantern")
    out: list[tuple[str, str]] = []
    order = ["hound", "barbaric", "quest", "brook", "brambles", "lantern", "bedtime", "kindness"]
    for tag in order:
        if tag in tags:
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, O, I) :- hill(H), obstacle(O), item(I), needed_tool(O, _).

matched(O, T) :- chosen_obstacle(O), chosen_tool(T), needed_tool(O, T).
crossed       :- matched(_, _).

found         :- crossed.
returned      :- found.
quiet         :- returned.

ending(happy) :- quiet.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hill_id in HILLS:
        lines.append(asp.fact("hill", hill_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
        want = matching_tool(obstacle_id)
        if want is not None:
            lines.append(asp.fact("needed_tool", obstacle_id, want))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_happy(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show ending/1."))
    endings = asp.atoms(model, "ending")
    return ("happy",) in endings


def outcome_of(params: StoryParams) -> str:
    return "happy" if params.tool == matching_tool(params.obstacle) else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime quest storyworld about a child, a hound, and a lonely giant."
    )
    ap.add_argument("--hill", choices=sorted(HILLS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--hound-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        want = matching_tool(args.obstacle)
        if args.tool != want:
            raise StoryError(explain_rejection(args.obstacle, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hill is None or combo[0] == args.hill)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.item is None or combo[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hill_id, obstacle_id, item_id = rng.choice(sorted(combos))
    tool_id = args.tool or matching_tool(obstacle_id)
    if tool_id is None:
        raise StoryError("(No sensible tool exists for that obstacle.)")
    if obstacle_id not in OBSTACLES or hill_id not in HILLS or item_id not in ITEMS or tool_id not in TOOLS:
        raise StoryError("(Invalid story parameters.)")

    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    hound_name = args.hound_name or rng.choice(HOUND_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        hill=hill_id,
        obstacle=obstacle_id,
        tool=tool_id,
        item=item_id,
        child_name=child_name,
        child_gender=gender,
        hound_name=hound_name,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hill not in HILLS:
        raise StoryError(f"(Unknown hill: {params.hill})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool != matching_tool(params.obstacle):
        raise StoryError(explain_rejection(params.obstacle, params.tool))

    world = tell(
        hill=HILLS[params.hill],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        item_cfg=ITEMS[params.item],
        child_name=params.child_name,
        child_gender=params.child_gender,
        hound_name=params.hound_name,
        parent_type=params.parent,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name).replace("hound", params.hound_name),
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

    for params in CURATED:
        if outcome_of(params) != "happy" or not asp_happy(params):
            rc = 1
            print(f"MISMATCH in happy-ending parity for curated params: {params}")
            break
    else:
        print(f"OK: happy-ending parity matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hill, obstacle, item) combos:\n")
        for hill_id, obstacle_id, item_id in combos:
            print(f"  {hill_id:12} {obstacle_id:10} {item_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name} and {p.hound_name}: {p.obstacle} on {p.hill} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
