#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py
======================================================================

A standalone story world about a larger-than-life child who goes on a magical
quest to solve one town-sized problem, meets one oversized obstacle, and learns
that even in a tall tale, the right help must have real relevance.

The world model prefers a narrow set of common-sense fantasy pairings:
a problem creates a goal, a goal chooses a route, a route brings an obstacle,
and only a relevant magic aid can solve that obstacle. The child-facing prose
still sounds playful and exaggerated, but the simulation underneath keeps the
conflict and resolution grounded.

Run it
------
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py --need orchard
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py --aid sun_jar
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py --obstacle shadow_river --aid anchor_boots
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/relevance_conflict_magic_quest_tall_tale.py --verify
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
# This file lives one level deeper than most worlds:
#   storyworlds/worlds/gpt-5.4/<this_file>.py
# so we add storyworlds/ to sys.path.
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Need:
    id: str
    town_line: str
    quest: str
    reward_label: str
    reward_phrase: str
    ending_line: str
    route: str
    obstacle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    path_line: str
    horizon_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    boast: str
    threat: str
    solved_by: str
    aftermath: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    use_line: str
    solves: str
    style: str
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


def _r_blocked(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if hero is None or obstacle is None:
        return []
    if obstacle.meters["active"] < THRESHOLD:
        return []
    sig = ("blocked", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["frustration"] += 1
    hero.memes["determination"] += 1
    return ["__blocked__"]


def _r_relevant_aid(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    aid = world.entities.get("aid")
    reward = world.entities.get("reward")
    if hero is None or obstacle is None or aid is None or reward is None:
        return []
    if obstacle.meters["active"] < THRESHOLD:
        return []
    if aid.attrs.get("solves") != obstacle.attrs.get("id"):
        return []
    sig = ("solved", obstacle.id, aid.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["active"] = 0.0
    obstacle.meters["cleared"] += 1
    reward.meters["reached"] += 1
    hero.memes["hope"] += 1
    hero.memes["awe"] += 1
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked", tag="conflict", apply=_r_blocked),
    Rule(name="relevant_aid", tag="magic", apply=_r_relevant_aid),
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


NEEDS = {
    "orchard": Need(
        id="orchard",
        town_line="the orchard leaves were hanging limp, and even the apples looked too tired to shine",
        quest="to fetch the Rain Pearl from the Cloud Corral",
        reward_label="Rain Pearl",
        reward_phrase="the Rain Pearl",
        ending_line="Soon the orchard drank deep, and apples swelled so round that two children had to hug each one at once.",
        route="high_trail",
        obstacle="wind_troll",
        tags={"orchard", "rain"},
    ),
    "mill": Need(
        id="mill",
        town_line="the old flour mill had gone still, and the baker's sacks of grain sat waiting like sleepy cattle",
        quest="to fetch the Whistle Wheel from Echo Mesa",
        reward_label="Whistle Wheel",
        reward_phrase="the Whistle Wheel",
        ending_line="Soon the mill sang and spun, and flour puffed from the door like friendly little clouds.",
        route="shadow_ford",
        obstacle="shadow_river",
        tags={"mill", "wind"},
    ),
    "schoolhouse": Need(
        id="schoolhouse",
        town_line="the schoolhouse was so dim that the letters on the slate looked shy",
        quest="to fetch the Sunrise Chalk from Dawn Cave",
        reward_label="Sunrise Chalk",
        reward_phrase="the Sunrise Chalk",
        ending_line="Soon the schoolhouse glowed warm and gold, and every chalk letter stood bright as a rooster's crow.",
        route="moon_meadow",
        obstacle="sleeping_hill",
        tags={"schoolhouse", "light"},
    ),
}

ROUTES = {
    "high_trail": Route(
        id="high_trail",
        path_line="The trail climbed so high that the fence posts had to wave at passing clouds.",
        horizon_line="Far ahead, the Cloud Corral rattled on the rim of the sky.",
        tags={"heights"},
    ),
    "shadow_ford": Route(
        id="shadow_ford",
        path_line="The road dipped to a ford where noon looked like late evening.",
        horizon_line="Beyond it, Echo Mesa rang back every footstep twice for good measure.",
        tags={"river"},
    ),
    "moon_meadow": Route(
        id="moon_meadow",
        path_line="The meadow rolled silver and wide, as if moonlight had decided not to go home at dawn.",
        horizon_line="At the far edge, Dawn Cave blinked open like a sleepy eye.",
        tags={"meadow"},
    ),
}

OBSTACLES = {
    "wind_troll": Obstacle(
        id="wind_troll",
        label="wind troll",
        phrase="a wind troll with whiskers made of weather vanes",
        boast='"No feet can stand where I blow," roared the troll.',
        threat="Each puff from him shoved pebbles uphill and nearly tipped the hero's hat into next Thursday.",
        solved_by="anchor_boots",
        aftermath="The wind troll snorted once, saw he had met steadier feet than his own gusts, and shuffled aside.",
        tags={"wind_troll", "wind"},
    ),
    "shadow_river": Obstacle(
        id="shadow_river",
        label="shadow river",
        phrase="a shadow river black as spilled ink",
        boast='"Cross me if you can," whispered the river, hiding its stepping stones under dark water.',
        threat="It swallowed the shape of the banks and made left and right seem to trade places.",
        solved_by="sun_jar",
        aftermath="The shadow river shrank back from the bright shine and showed every stepping stone like coins in a fountain.",
        tags={"shadow_river", "shadow"},
    ),
    "sleeping_hill": Obstacle(
        id="sleeping_hill",
        label="sleeping hill",
        phrase="a sleeping hill that snored boulders",
        boast='"Nobody passes while I nap," grumbled the hill without even opening its grassy eyes.',
        threat="Every snore rolled a rock across the path and bounced the hero's shadow clear off the ground.",
        solved_by="lullaby_fiddle",
        aftermath="The sleeping hill sighed into a gentler dream and flattened a smooth path with one polite yawn.",
        tags={"sleeping_hill", "sleep"},
    ),
}

AIDS = {
    "anchor_boots": Aid(
        id="anchor_boots",
        label="anchor boots",
        phrase="a pair of anchor boots with soles heavy as barn doors",
        use_line="the hero stamped into the earth until the ground remembered how to hold still",
        solves="wind_troll",
        style="weight",
        tags={"anchor_boots", "boots"},
    ),
    "sun_jar": Aid(
        id="sun_jar",
        label="sun jar",
        phrase="a sun jar with a morning beam corked inside",
        use_line="the hero uncorked the jar, and the bright beam ran over the water like a gold ribbon",
        solves="shadow_river",
        style="light",
        tags={"sun_jar", "light"},
    ),
    "lullaby_fiddle": Aid(
        id="lullaby_fiddle",
        label="lullaby fiddle",
        phrase="a lullaby fiddle carved from moonwood",
        use_line="the hero drew the bow once, and the note floated soft as warm milk through the grass",
        solves="sleeping_hill",
        style="song",
        tags={"lullaby_fiddle", "music"},
    ),
}

GIRL_NAMES = ["Polly", "Mabel", "June", "Dora", "Sadie", "Nell"]
BOY_NAMES = ["Hank", "Eli", "Beau", "Jasper", "Clem", "Rory"]
TRAITS = ["brave", "kind", "stout-hearted", "quick-thinking", "cheerful", "steady"]


def relevant_aid(obstacle_id: str, aid_id: str) -> bool:
    if obstacle_id not in OBSTACLES or aid_id not in AIDS:
        return False
    return OBSTACLES[obstacle_id].solved_by == aid_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for need_id, need in NEEDS.items():
        route_id = need.route
        obstacle_id = need.obstacle
        for aid_id in AIDS:
            if relevant_aid(obstacle_id, aid_id):
                combos.append((need_id, route_id, aid_id))
    return combos


@dataclass
class StoryParams:
    need: str
    route: str
    obstacle: str
    aid: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, need: Need) -> None:
    world.say(
        f"In the town of Big Willow, {hero.id} was such a {hero.attrs.get('trait')} {hero.type} "
        f"that {hero.pronoun('possessive')} footsteps made the porch planks hum little welcome songs."
    )
    world.say(
        f"One morning, {need.town_line}. Folks said the trouble had grown so large "
        f"it had to be measured with a wagon pole."
    )


def call_to_quest(world: World, hero: Entity, parent: Entity, need: Need) -> None:
    hero.memes["care"] += 1
    hero.memes["duty"] += 1
    world.say(
        f'{hero.id} tipped {hero.pronoun("possessive")} hat back and said, '
        f'"Then I\'ll go {need.quest}."'
    )
    world.say(
        f"{hero.id}'s {parent.label_word} did not laugh. "
        f'"A big journey needs the right kind of magic," {parent.pronoun()} said. '
        f'"Strength is fine, but relevance matters."'
    )


def receive_aid(world: World, hero: Entity, parent: Entity, aid: Aid) -> None:
    hero.meters["prepared"] += 1
    world.say(
        f"From a cedar chest, {parent.label_word} brought out {aid.phrase}. "
        f'"Take this," {parent.pronoun()} said. '
        f'"It may look small beside your boots, but it is exactly the sort of magic '
        f'that knows what job it belongs to."'
    )


def set_out(world: World, hero: Entity, route: Route, need: Need) -> None:
    hero.meters["travel"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"So {hero.id} set out {need.quest}, crossing country so broad that a rabbit "
        f"could start at breakfast and still be hopping at supper."
    )
    world.say(route.path_line)
    world.say(route.horizon_line)


def meet_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    obj = world.get("obstacle")
    obj.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before long, the way was blocked by {obstacle.phrase}. {obstacle.boast}"
    )
    world.say(obstacle.threat)


def wrong_for_obstacle(aid: Aid, obstacle: Obstacle) -> str:
    if aid.style == "weight":
        return (
            f"{aid.label.capitalize()} were mighty useful for standing still, "
            f"but they could not brighten a dark crossing or soothe a bad temper."
        )
    if aid.style == "light":
        return (
            f"The {aid.label} shone fine and brave, but light alone could not pin a storm in place "
            f"or sing a hill into a kinder dream."
        )
    return (
        f"The {aid.label} played sweetly, but a tune was no good for showing hidden stones "
        f"or planting feet against a gale."
    )


def struggle(world: World, hero: Entity, aid: Aid, obstacle: Obstacle) -> None:
    hero.memes["doubt"] += 1
    hero.meters["delayed"] += 1
    world.say(
        f"{hero.id} tried {aid.use_line}, but the trouble only grew fussier."
    )
    world.say(wrong_for_obstacle(aid, obstacle))
    world.say(
        f"That was the hard part of the quest: a traveler can carry real magic and still be wrong "
        f"if the magic has no relevance to the trouble at hand."
    )


def solve(world: World, hero: Entity, aid: Aid, obstacle: Obstacle) -> None:
    world.say(
        f"Then {hero.id} remembered what {hero.pronoun('possessive')} {world.get('parent').label_word} had said."
    )
    world.say(
        f"{hero.pronoun().capitalize()} used {aid.phrase} properly: {aid.use_line}."
    )
    propagate(world, narrate=False)
    world.say(obstacle.aftermath)


def claim_reward(world: World, hero: Entity, need: Need) -> None:
    reward = world.get("reward")
    reward.meters["carried_home"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Beyond the obstacle waited {need.reward_phrase}, shining as if a piece of weather "
        f"had learned manners and decided to fit in a traveler's hands."
    )
    world.say(
        f"{hero.id} lifted it gently and headed home in strides so long that fence rails "
        f"looked like comb teeth below."
    )


def homecoming(world: World, hero: Entity, need: Need) -> None:
    world.say(
        f"When {hero.id} came back to Big Willow, the whole town gathered before the first dust cloud "
        f"from {hero.pronoun('possessive')} boots had even settled."
    )
    world.say(need.ending_line)
    world.say(
        f"After that, whenever somebody bragged that any old magic would do, the people of Big Willow "
        f"would grin and say, \"Only if it has relevance.\""
    )


def tell(
    need: Need,
    route: Route,
    obstacle: Obstacle,
    aid: Aid,
    hero_name: str = "Polly",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "brave",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"trait": trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            role="obstacle",
            attrs={"id": obstacle.id},
        )
    )
    aid_ent = world.add(
        Entity(
            id="aid",
            kind="thing",
            type="aid",
            label=aid.label,
            phrase=aid.phrase,
            role="aid",
            attrs={"solves": aid.solves, "style": aid.style},
        )
    )
    reward = world.add(
        Entity(
            id="reward",
            kind="thing",
            type="reward",
            label=need.reward_label,
            phrase=need.reward_phrase,
            role="reward",
        )
    )

    introduce(world, hero, need)
    world.para()
    call_to_quest(world, hero, parent, need)
    receive_aid(world, hero, parent, aid)
    world.para()
    set_out(world, hero, route, need)
    meet_obstacle(world, hero, obstacle)

    success = relevant_aid(obstacle.id, aid.id)
    world.para()
    if success:
        solve(world, hero, aid, obstacle)
        claim_reward(world, hero, need)
        world.para()
        homecoming(world, hero, need)
    else:
        struggle(world, hero, aid, obstacle)
        world.say(
            f"So {hero.id} trudged home before sunset, wiser than when {hero.pronoun()} had left, "
            f"and asked for help instead of another guess."
        )
        world.para()
        world.say(
            f"That night the town still had its trouble, but {hero.id} had learned something grand: "
            f"a quest is not won by the biggest boast. It is won by finding the magic that truly fits."
        )
        world.say(
            f"The next morning, Big Willow planned again, this time matching the problem to the proper wonder."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        need=need,
        route=route,
        obstacle_cfg=obstacle,
        obstacle=obstacle_ent,
        aid=aid,
        aid_ent=aid_ent,
        reward=reward,
        success=success,
    )
    return world


KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with an important goal. The traveler goes somewhere hard so they can bring back help, treasure, or an answer.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is a special power that can do things ordinary tools cannot. In a good story, magic still works best when it matches the problem it is trying to solve.",
        )
    ],
    "relevance": [
        (
            "What does relevance mean?",
            "Relevance means something really fits the matter being talked about or solved. If an idea has relevance, it belongs to the problem instead of wandering off somewhere else.",
        )
    ],
    "wind": [
        (
            "Why would heavy boots help in strong wind?",
            "Heavy boots can help you stay planted so a gust cannot push you away. In a fantasy story, extra-heavy magic boots make that idea bigger and sillier.",
        )
    ],
    "light": [
        (
            "Why does light help you cross a dark place?",
            "Light helps you see where the safe steps are. When the path stops hiding, it becomes much easier to cross carefully.",
        )
    ],
    "music": [
        (
            "Why can a lullaby calm something down?",
            "A lullaby is soft and gentle, so it can help a person or creature rest. Story magic often turns that calm feeling into a real power.",
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees grow in rows. People care for the trees so they can make lots of fruit.",
        )
    ],
    "mill": [
        (
            "What does a mill do?",
            "A mill uses turning power, often from wind or water, to grind grain into flour. Flour can then be used to bake bread and other foods.",
        )
    ],
    "schoolhouse": [
        (
            "What is a schoolhouse?",
            "A schoolhouse is a building where children go to learn. In old stories, one little schoolhouse might serve a whole town.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "magic", "relevance", "orchard", "mill", "schoolhouse", "wind", "light", "music"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    need = f["need"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid"]
    success = f["success"]
    if success:
        return [
            f'Write a tall-tale quest for young children that includes the word "relevance."',
            f"Tell a magical frontier story where {hero.id} journeys to help a town with its {need.id} problem, meets {obstacle.phrase}, and uses {aid.phrase} because it is the right kind of magic.",
            f"Write a story with conflict, magic, and a quest, where the ending proves that the most useful wonder is the one that fits the trouble.",
        ]
    return [
        f'Write a tall-tale story for young children that includes the word "relevance."',
        f"Tell a magical quest where {hero.id} sets out to help the town but learns that {aid.label} is not the right answer to {obstacle.label}.",
        f"Write a conflict story in which a brave child carries real magic on a quest, yet still has to admit that the magic does not fit the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    need = f["need"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid"]
    success = f["success"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a larger-than-life {hero.type} from Big Willow. {hero.id} goes on a quest to help the whole town.",
        ),
        (
            "Why did the hero leave home?",
            f"{hero.id} left home because Big Willow had a problem with its {need.id}. The quest mattered to everyone in town, so {hero.pronoun()} went to fetch {need.reward_phrase}.",
        ),
        (
            "What blocked the hero on the journey?",
            f"The path was blocked by {obstacle.phrase}. That obstacle turned the trip into a real conflict instead of an easy walk.",
        ),
        (
            f"What did {hero.id}'s {pw} say before the journey?",
            f"{hero.pronoun('possessive').capitalize()} {pw} said that a big journey needs the right kind of magic, and that relevance matters. The warning was important because the quest could only be solved by fitting the tool to the trouble.",
        ),
    ]
    if success:
        qa.append(
            (
                f"How did {hero.id} get past the {obstacle.label}?",
                f"{hero.id} used {aid.phrase} to face the {obstacle.label}. It worked because that magic matched the obstacle instead of merely looking impressive.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} brought home {need.reward_phrase}, and Big Willow's problem changed for the better. {need.ending_line}",
            )
        )
        qa.append(
            (
                "What does relevance mean in this story?",
                f"In this story, relevance means choosing help that truly fits the trouble. The hero wins because the magic is the right kind, not just the biggest kind.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {aid.label} fail?",
                f"{aid.label.capitalize()} was real magic, but it did not fit the {obstacle.label}. The quest failed that day because the tool had no relevance to the problem at hand.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} came home without {need.reward_phrase}, but with a wiser heart. The town still needed help, and the hero had learned to stop guessing and start matching the answer to the problem.",
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.id} learned that bravery and magic are not enough by themselves. A quest is solved when the answer truly fits the trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"quest", "magic", "relevance"}
    need = f["need"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid"]
    tags |= need.tags
    if obstacle.id == "wind_troll" or aid.id == "anchor_boots":
        tags.add("wind")
    if obstacle.id == "shadow_river" or aid.id == "sun_jar":
        tags.add("light")
    if obstacle.id == "sleeping_hill" or aid.id == "lullaby_fiddle":
        tags.add("music")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        need="orchard",
        route="high_trail",
        obstacle="wind_troll",
        aid="anchor_boots",
        hero_name="Polly",
        hero_gender="girl",
        parent="mother",
        trait="steady",
    ),
    StoryParams(
        need="mill",
        route="shadow_ford",
        obstacle="shadow_river",
        aid="sun_jar",
        hero_name="Hank",
        hero_gender="boy",
        parent="father",
        trait="quick-thinking",
    ),
    StoryParams(
        need="schoolhouse",
        route="moon_meadow",
        obstacle="sleeping_hill",
        aid="lullaby_fiddle",
        hero_name="June",
        hero_gender="girl",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        need="mill",
        route="shadow_ford",
        obstacle="shadow_river",
        aid="anchor_boots",
        hero_name="Beau",
        hero_gender="boy",
        parent="father",
        trait="brave",
    ),
]


def explain_rejection(need_id: str, route_id: str, obstacle_id: str, aid_id: str) -> str:
    need = NEEDS[need_id]
    if need.route != route_id:
        return (
            f"(No story: the {need.id} quest travels by {need.route}, not {route_id}. "
            f"The route comes from the goal, so those choices must stay together.)"
        )
    if need.obstacle != obstacle_id:
        return (
            f"(No story: the {need.id} quest meets {need.obstacle}, not {obstacle_id}. "
            f"Each quest has one signature conflict on its path.)"
        )
    right = OBSTACLES[obstacle_id].solved_by
    return (
        f"(No story: {aid_id} is not relevant to {obstacle_id}. "
        f"Try --aid {right}, which is the magic that actually fits this conflict.)"
    )


ASP_RULES = r"""
quest_route(N, R)    :- need(N), route(R), canonical_route(N, R).
quest_obstacle(N, O) :- need(N), obstacle(O), canonical_obstacle(N, O).

valid(N, R, A) :- need(N), route(R), aid(A),
                  quest_route(N, R),
                  quest_obstacle(N, O),
                  solves(A, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("canonical_route", need_id, need.route))
        lines.append(asp.fact("canonical_obstacle", need_id, need.obstacle))
    for route_id in ROUTES:
        lines.append(asp.fact("route", route_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("solves", aid_id, aid.solves))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
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
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random generated empty story during verify.")
        print("OK: random resolve_params() + generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tall-tale child uses relevant magic on a quest."
    )
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_need = args.need
    explicit_route = args.route
    explicit_obstacle = args.obstacle
    explicit_aid = args.aid

    if explicit_need and explicit_route and NEEDS[explicit_need].route != explicit_route:
        raise StoryError(explain_rejection(explicit_need, explicit_route, NEEDS[explicit_need].obstacle, explicit_aid or AIDS[next(iter(AIDS))].id))
    if explicit_need and explicit_obstacle and NEEDS[explicit_need].obstacle != explicit_obstacle:
        route_id = explicit_route or NEEDS[explicit_need].route
        raise StoryError(explain_rejection(explicit_need, route_id, explicit_obstacle, explicit_aid or AIDS[next(iter(AIDS))].id))
    if explicit_obstacle and explicit_aid and not relevant_aid(explicit_obstacle, explicit_aid):
        need_id = explicit_need
        if need_id is None:
            matches = [nid for nid, need in NEEDS.items() if need.obstacle == explicit_obstacle]
            need_id = matches[0] if matches else next(iter(NEEDS))
        route_id = explicit_route or NEEDS[need_id].route
        raise StoryError(explain_rejection(need_id, route_id, explicit_obstacle, explicit_aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.need is None or combo[0] == args.need)
        and (args.route is None or combo[1] == args.route)
        and (args.aid is None or combo[2] == args.aid)
        and (args.obstacle is None or NEEDS[combo[0]].obstacle == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    need_id, route_id, aid_id = rng.choice(sorted(combos))
    obstacle_id = NEEDS[need_id].obstacle
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        need=need_id,
        route=route_id,
        obstacle=obstacle_id,
        aid=aid_id,
        hero_name=name,
        hero_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    need = NEEDS[params.need]
    if need.route != params.route or need.obstacle != params.obstacle or not relevant_aid(params.obstacle, params.aid):
        raise StoryError(explain_rejection(params.need, params.route, params.obstacle, params.aid))

    world = tell(
        need=need,
        route=ROUTES[params.route],
        obstacle=OBSTACLES[params.obstacle],
        aid=AIDS[params.aid],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (need, route, aid) combos:\n")
        for need_id, route_id, aid_id in combos:
            obstacle_id = NEEDS[need_id].obstacle
            print(f"  {need_id:11} {route_id:13} {obstacle_id:14} {aid_id}")
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
            header = f"### {p.hero_name}: {p.need} quest by {p.route} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
