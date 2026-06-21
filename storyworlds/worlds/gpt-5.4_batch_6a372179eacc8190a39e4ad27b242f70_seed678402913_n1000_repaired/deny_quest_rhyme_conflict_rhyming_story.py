#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py
=====================================================================

A standalone storyworld for a child-sized quest told in a gentle rhyming style.

Premise
-------
A child sets out on a small quest to fetch a special thing from a distant place.
A cautious keeper blocks the way and says "deny" because the path is unsafe.
A little guide answers the conflict with a rhyme that points to the proper tool.
When the child accepts the safer method, the quest can continue and the ending
image proves what changed.

This world is deliberately narrow and reasoned:
- each quest belongs to one place,
- each place has one fitting obstacle,
- each obstacle requires a kind of safety tool,
- an explicit incompatible tool is refused with StoryError.

Run it
------
python storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py
python storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py --place echo_cave --quest bell_berry --tool lantern
python storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py --tool ribbon
python storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/deny_quest_rhyme_conflict_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
class Place:
    id: str
    label: str
    start_image: str
    destination: str
    keeper_name: str
    keeper_type: str
    keeper_phrase: str
    guide_name: str
    guide_type: str
    guide_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    place: str
    item_label: str
    item_phrase: str
    reason: str
    return_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    place: str
    label: str
    danger: str
    need: str
    deny_line: str
    cross_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    provides: set[str] = field(default_factory=set)
    sense: int = 3
    rhyme_hint: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    obstacle: str
    tool: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "moon_meadow": Place(
        id="moon_meadow",
        label="Moon Meadow",
        start_image="The grass still wore silver dew.",
        destination="the far hill where moonblossoms grew",
        keeper_name="Nell",
        keeper_type="woman",
        keeper_phrase="Nell the bridge keeper",
        guide_name="Wren",
        guide_type="bird",
        guide_phrase="a tiny wren on the rail",
        tags={"meadow", "bridge"},
    ),
    "pebble_brook": Place(
        id="pebble_brook",
        label="Pebble Brook",
        start_image="Round stones shone like wet little moons.",
        destination="the bend where the silver shell lay",
        keeper_name="Otis",
        keeper_type="man",
        keeper_phrase="Otis the stepping-stone watcher",
        guide_name="Frog",
        guide_type="animal",
        guide_phrase="a green frog on a cattail",
        tags={"brook", "stones"},
    ),
    "echo_cave": Place(
        id="echo_cave",
        label="Echo Cave",
        start_image="The hill mouth yawned cool and gray.",
        destination="the deep nook where bell-berries hung",
        keeper_name="Mara",
        keeper_type="woman",
        keeper_phrase="Mara the cave keeper",
        guide_name="Bat",
        guide_type="animal",
        guide_phrase="a soft-winged bat near the arch",
        tags={"cave", "dark"},
    ),
}

QUESTS = {
    "moonblossom": Quest(
        id="moonblossom",
        place="moon_meadow",
        item_label="moonblossom",
        item_phrase="a pale moonblossom",
        reason="to brighten a droopy garden pot at home",
        return_image="The bloom glowed in a jar by the window.",
        tags={"flower", "garden"},
    ),
    "silver_shell": Quest(
        id="silver_shell",
        place="pebble_brook",
        item_label="silver shell",
        item_phrase="a small silver shell",
        reason="to sing in Grandma's wind chime",
        return_image="The shell chimed with the porch bells at dusk.",
        tags={"shell", "music"},
    ),
    "bell_berry": Quest(
        id="bell_berry",
        place="echo_cave",
        item_label="bell-berry",
        item_phrase="a round bell-berry",
        reason="to tuck into a sleepy tea for a sniffly neighbor",
        return_image="The berry steamed sweetly in the teacup's curl.",
        tags={"berry", "tea"},
    ),
}

OBSTACLES = {
    "windy_bridge": Obstacle(
        id="windy_bridge",
        place="moon_meadow",
        label="windy bridge",
        danger="gusts shook the bridge from side to side",
        need="holdfast",
        deny_line='Nell lifted a hand and said, "I must deny this way today."',
        cross_line="With a steady line in hand, the child crossed the swaying bridge.",
        tags={"bridge", "wind"},
    ),
    "slick_stones": Obstacle(
        id="slick_stones",
        place="pebble_brook",
        label="slick stones",
        danger="the stepping stones wore a skin of cold, slippery moss",
        need="boots",
        deny_line='Otis stamped his staff and said, "I must deny those stones today."',
        cross_line="With dry boots hugging each foot, the child stepped from stone to stone.",
        tags={"stones", "water"},
    ),
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        place="echo_cave",
        label="dark tunnel",
        danger="the tunnel curled so dark that even brave eyes guessed wrong",
        need="light",
        deny_line='Mara shook her head and said, "I must deny that dark today."',
        cross_line="With a safe light leading the way, the child walked the cave without a stumble.",
        tags={"cave", "dark"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="guide rope",
        phrase="a guide rope",
        provides={"holdfast"},
        sense=3,
        rhyme_hint="Hold the rope and do not sway; step by step will make your way.",
        tags={"rope", "bridge"},
    ),
    "handrail": Tool(
        id="handrail",
        label="wooden handrail",
        phrase="the wooden handrail",
        provides={"holdfast"},
        sense=3,
        rhyme_hint="Palm the rail and breathe out slow; feet can learn the path to go.",
        tags={"rail", "bridge"},
    ),
    "boots": Tool(
        id="boots",
        label="yellow rain boots",
        phrase="yellow rain boots",
        provides={"boots"},
        sense=3,
        rhyme_hint="Boots on toes and worry off; wet stones stop being quite so rough.",
        tags={"boots", "water"},
    ),
    "reed_boots": Tool(
        id="reed_boots",
        label="reed boots",
        phrase="reed-wrapped boots",
        provides={"boots"},
        sense=2,
        rhyme_hint="Wrap your feet before you leap; then the brook will play, not sweep.",
        tags={"boots", "water"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        provides={"light"},
        sense=3,
        rhyme_hint="Carry light and do not race; bright steps fit a shadowed place.",
        tags={"lantern", "light"},
    ),
    "glow_jar": Tool(
        id="glow_jar",
        label="glow jar",
        phrase="a glow jar of firefly light",
        provides={"light"},
        sense=3,
        rhyme_hint="Take a glow instead of guess; soft light turns the cave to less.",
        tags={"light", "jar"},
    ),
    "ribbon": Tool(
        id="ribbon",
        label="ribbon",
        phrase="a satin ribbon",
        provides={"pretty"},
        sense=1,
        rhyme_hint="",
        tags={"pretty"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Ava", "Tessa", "Ruby", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Milo", "Theo", "Owen", "Finn", "Leo", "Sam", "Eli"]
TRAITS = ["brave", "gentle", "curious", "hopeful", "cheerful", "eager"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.stanzas: list[list[str]] = [[]]
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
            self.stanzas[-1].append(text)

    def para(self) -> None:
        if self.stanzas[-1]:
            self.stanzas.append([])

    def render(self) -> str:
        return "\n\n".join("\n".join(block) for block in self.stanzas if block)


def compatible(place: Place, quest: Quest, obstacle: Obstacle, tool: Tool) -> bool:
    return (
        quest.place == place.id
        and obstacle.place == place.id
        and tool.sense >= SENSE_MIN
        and obstacle.need in tool.provides
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                for tool_id, tool in TOOLS.items():
                    if compatible(place, quest, obstacle, tool):
                        combos.append((place_id, quest_id, obstacle_id, tool_id))
    return sorted(combos)


def explain_tool(tool: Tool, obstacle: Obstacle) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.phrase} is too flimsy to be a sensible answer here. "
            f"The {obstacle.label} needs real safety help, not something merely pretty.)"
        )
    return (
        f"(No story: {tool.phrase} does not solve the problem at the {obstacle.label}. "
        f"This path needs something that provides {obstacle.need}.)"
    )


def explain_combo(place: Place, quest: Quest, obstacle: Obstacle) -> str:
    if quest.place != place.id:
        return (
            f"(No story: the quest for {quest.item_phrase} belongs to {PLACES[quest.place].label}, "
            f"not {place.label}.)"
        )
    if obstacle.place != place.id:
        return (
            f"(No story: the {obstacle.label} is part of {PLACES[obstacle.place].label}, "
            f"not {place.label}.)"
        )
    return "(No story: this combination does not form one coherent quest.)"


def opening(world: World, child: Entity, place: Place, quest: Quest) -> None:
    child.memes["hope"] += 1
    child.meters["quest"] += 1
    world.say(f"{child.id} woke early while the sky was pearl-gray.")
    world.say(f"{place.start_image} {child.pronoun('subject').capitalize()} had a quest for the day.")
    world.say(
        f'"I will find {quest.item_phrase}," said {child.id}, "for {quest.reason}."'
    )
    world.say(
        f"So off went the {child.attrs['trait']} child toward {place.destination}, "
        f"with a hum and a hopeful stride."
    )


def denial(world: World, child: Entity, keeper: Entity, obstacle: Obstacle) -> None:
    keeper.memes["caution"] += 1
    child.memes["frustration"] += 1
    world.say(
        f"At the {obstacle.label} stood {keeper.label}, watching how {obstacle.danger}."
    )
    world.say(obstacle.deny_line)
    world.say(
        f'"No small feet pass while danger is high. I do not mock you, '
        f'but I cannot let courage deny the sky."'
    )


def protest(world: World, child: Entity, quest: Quest) -> None:
    child.memes["determination"] += 1
    world.say(
        f'{child.id} frowned and said, "But I need {quest.item_phrase} before the day says good-bye."'
    )
    if child.memes["frustration"] >= THRESHOLD:
        world.say(
            f"The quest felt close enough to touch, and being stopped stung very much."
        )


def guide_rhyme(world: World, guide: Entity, tool: Tool, obstacle: Obstacle) -> None:
    guide.memes["help"] += 1
    world.say(
        f"Then {guide.phrase} piped up with a small clear cry."
    )
    world.say(f'"{tool.rhyme_hint}"')
    world.say(
        f"The rhyme fit the trouble exactly, because the {obstacle.label} needed {obstacle.need}, not hurry."
    )


def accept_tool(world: World, child: Entity, keeper: Entity, tool: Tool) -> None:
    child.meters["safety"] += 1
    child.memes["trust"] += 1
    child.memes["frustration"] = 0.0
    world.say(
        f"{child.id} looked at {tool.phrase}, then up at {keeper.label}, and gave a thoughtful nod."
    )
    world.say(
        f'"You did not deny me to be unkind," said {child.id}. '
        f'"You were guarding the path until I used a wiser way."'
    )


def cross(world: World, child: Entity, keeper: Entity, obstacle: Obstacle) -> None:
    child.meters["travel"] += 1
    child.meters["quest"] += 1
    keeper.memes["approval"] += 1
    world.say(
        f'{keeper.label} smiled at last and said, "Now the path and child agree."'
    )
    world.say(obstacle.cross_line)


def find_item(world: World, child: Entity, place: Place, quest: Quest) -> None:
    child.meters["quest"] += 1
    child.meters["item_found"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Beyond the path, {place.destination} waited soft and shy."
    )
    world.say(
        f"There {child.id} found {quest.item_phrase}, tucked just where the guide had said."
    )


def return_home(world: World, child: Entity, quest: Quest) -> None:
    child.meters["home"] += 1
    child.memes["relief"] += 1
    world.say(
        f"Home came the child by evening light, still humming the helpful rhyme."
    )
    world.say(quest.return_image)
    world.say(
        f"From then on, {child.id} remembered this: a careful pause can help a brave heart fly."
    )


def tell(place: Place, quest: Quest, obstacle: Obstacle, tool: Tool,
         child_name: str, child_gender: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": trait},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=place.keeper_type,
        label=place.keeper_name,
        phrase=place.keeper_phrase,
        role="keeper",
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=place.guide_type,
        label=place.guide_name,
        phrase=place.guide_phrase,
        role="guide",
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        role="tool",
        tags=set(tool.tags),
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="quest_item",
        label=quest.item_label,
        phrase=quest.item_phrase,
        role="item",
        tags=set(quest.tags),
    ))

    opening(world, child, place, quest)
    world.para()
    denial(world, child, keeper, obstacle)
    protest(world, child, quest)
    guide_rhyme(world, guide, tool, obstacle)
    world.para()
    accept_tool(world, child, keeper, tool)
    cross(world, child, keeper, obstacle)
    find_item(world, child, place, quest)
    world.para()
    return_home(world, child, quest)

    world.facts.update(
        child=child,
        keeper=keeper,
        guide=guide,
        tool=tool_ent,
        tool_cfg=tool,
        place=place,
        quest=quest,
        obstacle=obstacle,
        item=item,
        resolved=child.meters["item_found"] >= THRESHOLD,
        denied=True,
    )
    return world


KNOWLEDGE = {
    "bridge": [
        (
            "Why might a bridge be unsafe on a windy day?",
            "Strong wind can shake a bridge and make balance harder. Holding a steady support helps people cross more safely.",
        )
    ],
    "stones": [
        (
            "Why are wet stones slippery?",
            "Water and moss make the tops of stones slick. Feet can slide more easily when the surface is smooth and wet.",
        )
    ],
    "cave": [
        (
            "Why is it hard to walk in a dark cave?",
            "In a dark cave, it is hard to see where the ground bends or dips. A safe light helps you place your steps carefully.",
        )
    ],
    "rope": [
        (
            "What can a guide rope do?",
            "A guide rope gives your hand something steady to hold. That makes balance easier when a path wobbles.",
        )
    ],
    "boots": [
        (
            "Why do boots help near water?",
            "Boots protect your feet and can give better grip than bare shoes. They help you step more safely on wet ground.",
        )
    ],
    "light": [
        (
            "Why is a lantern safer than guessing in the dark?",
            "A lantern lets you see where to put your feet. Guessing in the dark can lead to bumps and stumbles.",
        )
    ],
    "keeper": [
        (
            "Why would a keeper stop someone from crossing?",
            "A careful keeper stops people when a path looks unsafe. That is a way of protecting them, not being mean.",
        )
    ],
    "rhyme": [
        (
            "How can a rhyme help someone remember something important?",
            "A rhyme is easy to say again in your mind. That makes it easier to remember good advice at the right moment.",
        )
    ],
}
KNOWLEDGE_ORDER = ["keeper", "bridge", "stones", "cave", "rope", "boots", "light", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    quest = f["quest"]
    obstacle = f["obstacle"]
    tool = f["tool_cfg"]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old about a child on a quest in '
            f'{place.label} who hears the word "deny" and learns a safer way forward.'
        ),
        (
            f"Tell a gentle quest story where {child.id} wants to fetch {quest.item_phrase}, "
            f"but a keeper blocks the {obstacle.label} until {child.pronoun('subject')} uses {tool.phrase}."
        ),
        (
            f'Write a rhyming conflict-and-resolution story in which a small guide gives advice in rhyme, '
            f'and the ending shows that caution helped the quest succeed.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    guide = f["guide"]
    quest = f["quest"]
    obstacle = f["obstacle"]
    tool = f["tool_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a {child.attrs['trait']} child on a quest, plus {keeper.label} the keeper and {guide.label} the little guide."
        ),
        (
            f"What was {child.id} trying to find?",
            f"{child.id} was trying to find {quest.item_phrase}. {child.pronoun('subject').capitalize()} wanted it {quest.reason}."
        ),
        (
            f"Why did {keeper.label} say \"deny\"?",
            f"{keeper.label} said \"deny\" because {obstacle.danger}. The keeper was stopping {child.id} from taking an unsafe path, not ending the quest forever."
        ),
        (
            f"How was the conflict solved?",
            f"{guide.label} gave a rhyme that pointed to {tool.phrase}, which matched the problem at the {obstacle.label}. Once {child.id} accepted the safer tool, the keeper allowed the crossing and the quest could continue."
        ),
    ]
    if f.get("resolved"):
        qa.append(
            (
                f"How did the story end?",
                f"{child.id} crossed safely, found {quest.item_phrase} in {place.label}, and came home with it by evening. The ending proves that listening to careful advice helped the quest succeed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"keeper", "rhyme"}
    obstacle = f["obstacle"]
    tool = f["tool_cfg"]
    if "bridge" in obstacle.tags or "wind" in obstacle.tags:
        tags.add("bridge")
    if "stones" in obstacle.tags or "water" in obstacle.tags:
        tags.add("stones")
    if "cave" in obstacle.tags or "dark" in obstacle.tags:
        tags.add("cave")
    if "rope" in tool.tags or "rail" in tool.tags:
        tags.add("rope")
    if "boots" in tool.tags:
        tags.add("boots")
    if "lantern" in tool.tags or "light" in tool.tags or "jar" in tool.tags:
        tags.add("light")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_meadow",
        quest="moonblossom",
        obstacle="windy_bridge",
        tool="rope",
        child_name="Mina",
        child_gender="girl",
        trait="brave",
    ),
    StoryParams(
        place="moon_meadow",
        quest="moonblossom",
        obstacle="windy_bridge",
        tool="handrail",
        child_name="Ben",
        child_gender="boy",
        trait="hopeful",
    ),
    StoryParams(
        place="pebble_brook",
        quest="silver_shell",
        obstacle="slick_stones",
        tool="boots",
        child_name="Ruby",
        child_gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="pebble_brook",
        quest="silver_shell",
        obstacle="slick_stones",
        tool="reed_boots",
        child_name="Theo",
        child_gender="boy",
        trait="gentle",
    ),
    StoryParams(
        place="echo_cave",
        quest="bell_berry",
        obstacle="dark_tunnel",
        tool="lantern",
        child_name="Ella",
        child_gender="girl",
        trait="eager",
    ),
    StoryParams(
        place="echo_cave",
        quest="bell_berry",
        obstacle="dark_tunnel",
        tool="glow_jar",
        child_name="Milo",
        child_gender="boy",
        trait="cheerful",
    ),
]


ASP_RULES = r"""
valid(P, Q, O, T) :- place(P), quest(Q), obstacle(O), tool(T),
                     quest_place(Q, P), obstacle_place(O, P),
                     need(O, N), provides(T, N),
                     sense(T, S), sense_min(M), S >= M.

approval(granted) :- chosen_place(P), chosen_quest(Q), chosen_obstacle(O), chosen_tool(T),
                     valid(P, Q, O, T).
approval(denied)  :- chosen_place(P), chosen_quest(Q), chosen_obstacle(O), chosen_tool(T),
                     not valid(P, Q, O, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        lines.append(asp.fact("quest_place", quest_id, quest.place))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_place", obstacle_id, obstacle.place))
        lines.append(asp.fact("need", obstacle_id, obstacle.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for need in sorted(tool.provides):
            lines.append(asp.fact("provides", tool_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_approval(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_quest", params.quest),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show approval/1."))
    atoms = asp.atoms(model, "approval")
    return atoms[0][0] if atoms else "?"


def approval_of(params: StoryParams) -> str:
    try:
        place = PLACES[params.place]
        quest = QUESTS[params.quest]
        obstacle = OBSTACLES[params.obstacle]
        tool = TOOLS[params.tool]
    except KeyError:
        return "denied"
    return "granted" if compatible(place, quest, obstacle, tool) else "denied"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming quest storyworld: a keeper says deny until a child uses the right safe tool."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible quest combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest:
        if QUESTS[args.quest].place != args.place:
            raise StoryError(explain_combo(PLACES[args.place], QUESTS[args.quest], OBSTACLES[next(iter(OBSTACLES))]))
    if args.place and args.obstacle:
        if OBSTACLES[args.obstacle].place != args.place:
            quest = next(q for q in QUESTS.values() if q.place == args.place)
            raise StoryError(explain_combo(PLACES[args.place], quest, OBSTACLES[args.obstacle]))
    if args.tool and args.obstacle:
        tool = TOOLS[args.tool]
        obstacle = OBSTACLES[args.obstacle]
        if not (tool.sense >= SENSE_MIN and obstacle.need in tool.provides):
            raise StoryError(explain_tool(tool, obstacle))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.quest is None or combo[1] == args.quest)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        if args.place and args.quest and QUESTS[args.quest].place != args.place:
            raise StoryError(explain_combo(PLACES[args.place], QUESTS[args.quest], OBSTACLES[next(iter(OBSTACLES))]))
        if args.place and args.obstacle and OBSTACLES[args.obstacle].place != args.place:
            quest = next(q for q in QUESTS.values() if q.place == args.place)
            raise StoryError(explain_combo(PLACES[args.place], quest, OBSTACLES[args.obstacle]))
        if args.tool and args.obstacle:
            raise StoryError(explain_tool(TOOLS[args.tool], OBSTACLES[args.obstacle]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, quest_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        quest=quest_id,
        obstacle=obstacle_id,
        tool=tool_id,
        child_name=name,
        child_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not compatible(place, quest, obstacle, tool):
        if quest.place != place.id or obstacle.place != place.id:
            raise StoryError(explain_combo(place, quest, obstacle))
        raise StoryError(explain_tool(tool, obstacle))

    world = tell(
        place=place,
        quest=quest,
        obstacle=obstacle,
        tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP valid combos match Python ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for place_id in PLACES:
        for quest_id in QUESTS:
            for obstacle_id in OBSTACLES:
                for tool_id in TOOLS:
                    cases.append(
                        StoryParams(
                            place=place_id,
                            quest=quest_id,
                            obstacle=obstacle_id,
                            tool=tool_id,
                            child_name="Mina",
                            child_gender="girl",
                            trait="brave",
                        )
                    )
    mismatches = [
        p for p in cases
        if asp_approval(p) != approval_of(p)
    ]
    if not mismatches:
        print(f"OK: ASP approval matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} approval results differ.")

    try:
        smoke = generate(CURATED[0])
        if "deny" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: story did not include the seed word 'deny'.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show approval/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, obstacle, tool) combos:\n")
        for place_id, quest_id, obstacle_id, tool_id in combos:
            print(f"  {place_id:12} {quest_id:12} {obstacle_id:13} {tool_id}")
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
            header = f"### {p.child_name}: {p.quest} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
