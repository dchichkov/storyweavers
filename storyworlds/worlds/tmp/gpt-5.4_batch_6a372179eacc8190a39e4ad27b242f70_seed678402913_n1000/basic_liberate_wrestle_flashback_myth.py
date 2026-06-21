#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py
===================================================================

A small myth-flavored storyworld about a child, a trapped stream spirit, and a
plain tool used bravely. The tale uses a flashback: an elder remembers the old
promise that the hill spring once made to the village, and that memory guides
the rescue.

The world model is deliberately compact and state-driven:

- A blocked spring makes the grove thirsty and the village worried.
- A child can try to free the spring by hand, but some tangles require help or
  a simple tool.
- The elder's flashback reveals why the spring matters and raises resolve.
- If the child wrestles the bramble loose with a basic hook or with a friend's
  help, the water runs again and the valley changes.
- Unreasonable combinations are rejected with StoryError.

Run it
------
python storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py
python storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py --hero Mira --obstacle roots
python storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py --tool bare_hands
python storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py --all
python storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py --qa --json
python storyworlds/worlds/gpt-5.4/basic_liberate_wrestle_flashback_myth.py --verify
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
        female = {"girl", "woman", "daughter", "priestess"}
        male = {"boy", "man", "son", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    strength: int
    snap: str
    remnant: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    basic: bool
    motion: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    power: int
    kind: str
    arrival: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ElderMemory:
    id: str
    opener: str
    body: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    helper: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    memory: str
    seed: Optional[int] = None


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


def _r_thirst(world: World) -> list[str]:
    spring = world.get("spring")
    grove = world.get("grove")
    village = world.get("village")
    out: list[str] = []
    if spring.meters["blocked"] >= THRESHOLD:
        sig = ("thirst",)
        if sig not in world.fired:
            world.fired.add(sig)
            grove.meters["thirst"] += 1
            village.memes["worry"] += 1
    if spring.meters["flow"] >= THRESHOLD:
        sig = ("blessing",)
        if sig not in world.fired:
            world.fired.add(sig)
            grove.meters["thirst"] = 0.0
            grove.meters["bloom"] += 1
            village.memes["relief"] += 1
            out.append("__water_returns__")
    return out


CAUSAL_RULES = [
    Rule(name="thirst", tag="physical", apply=_r_thirst),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


PLACES = {
    "cedar_hill": Place(
        id="cedar_hill",
        label="Cedar Hill",
        phrase="the cedar hill above the valley",
        image="where the wind combed the dark trees and the stones kept old songs",
        tags={"hill", "grove"},
    ),
    "sun_gorge": Place(
        id="sun_gorge",
        label="Sun Gorge",
        phrase="the bright gorge beyond the fields",
        image="where swallows wheeled over warm cliffs and gold moss clung to the rocks",
        tags={"gorge", "spring"},
    ),
    "moon_olive": Place(
        id="moon_olive",
        label="Moon-Olive Grove",
        phrase="the moon-olive grove near the village",
        image="where silver leaves whispered over shallow pools of light",
        tags={"grove", "spring"},
    ),
}

OBSTACLES = {
    "brambles": Obstacle(
        id="brambles",
        label="brambles",
        phrase="a black knot of brambles",
        strength=3,
        snap="The thorny knot tore loose all at once.",
        remnant="A few broken thorns lay by the stones like sleepy claws.",
        tags={"brambles", "thorn"},
    ),
    "roots": Obstacle(
        id="roots",
        label="roots",
        phrase="a braid of old roots",
        strength=2,
        snap="The roots gave with a wet crack and rolled aside.",
        remnant="The loosened roots lay like dark ropes beside the spring.",
        tags={"roots", "tree"},
    ),
    "stone_net": Obstacle(
        id="stone_net",
        label="stone net",
        phrase="a lattice of fallen stones and vines",
        strength=4,
        snap="The last stone tipped, and the whole net slumped down the bank.",
        remnant="Pebbles glittered in the mud where the snare had been.",
        tags={"stone", "vines"},
    ),
}

TOOLS = {
    "bare_hands": Tool(
        id="bare_hands",
        label="bare hands",
        phrase="only bare hands",
        power=1,
        sense=2,
        basic=True,
        motion="dug fingers into the tangle and tried to wrench it free",
        qa_text="used only bare hands",
        tags={"hands", "basic"},
    ),
    "reed_hook": Tool(
        id="reed_hook",
        label="reed hook",
        phrase="a basic reed hook",
        power=2,
        sense=3,
        basic=True,
        motion="slid a basic reed hook under the tangle and levered hard",
        qa_text="used a basic reed hook as a lever",
        tags={"hook", "basic", "reed"},
    ),
    "ash_staff": Tool(
        id="ash_staff",
        label="ash staff",
        phrase="a forked ash staff",
        power=2,
        sense=3,
        basic=False,
        motion="jammed a forked ash staff beneath the tangle and pushed with all her weight",
        qa_text="used a forked ash staff to pry the blockage loose",
        tags={"staff", "wood"},
    ),
}

HELPERS = {
    "alone": Helper(
        id="alone",
        label="alone",
        phrase="alone",
        power=0,
        kind="none",
        arrival="No one stood beside the child except the listening leaves.",
        qa_text="no one helped",
        tags=set(),
    ),
    "friend": Helper(
        id="friend",
        label="friend",
        phrase="a sure-footed friend",
        power=1,
        kind="friend",
        arrival="A friend came running over the stones and knelt beside the child without a word.",
        qa_text="a friend pulled beside the hero",
        tags={"friend"},
    ),
    "goat": Helper(
        id="goat",
        label="mountain goat",
        phrase="a stubborn mountain goat",
        power=1,
        kind="goat",
        arrival="The old mountain goat that wandered the slope lowered its horns and shoved at the vines.",
        qa_text="a mountain goat shoved at the tangle",
        tags={"goat", "animal"},
    ),
}

MEMORIES = {
    "promise": ElderMemory(
        id="promise",
        opener="The elder touched the dry stones and spoke as if opening a door in time.",
        body='“When I was small,” the elder said, “this spring sang every dawn. It promised that as long as the village shared water kindly, the grove would never thirst.”',
        lesson="So the child understood that freeing the water was not only about today. It was about keeping an old promise alive.",
        tags={"promise", "flashback"},
    ),
    "lantern": ElderMemory(
        id="lantern",
        opener="The elder closed his eyes, and the afternoon seemed to step backward.",
        body='“I remember a summer of dust,” he said. “One night your grandmother carried a lantern here, and the spring shone like a star in a cup. We drank, and the fields lived.”',
        lesson="The memory made the hidden water feel near again, as if the past itself were asking for help.",
        tags={"lantern", "flashback"},
    ),
    "song": ElderMemory(
        id="song",
        opener="The elder leaned on his cane, and his voice grew soft with remembering.",
        body='“Long ago,” he said, “children used to leave olive leaves here and sing. The stream answered them with clear laughter.”',
        lesson="That flashback turned the quiet stones into something holy and familiar at once.",
        tags={"song", "flashback"},
    ),
}

GIRL_NAMES = ["Mira", "Ione", "Thalia", "Rhea", "Dora", "Selene"]
BOY_NAMES = ["Pavo", "Lykos", "Timon", "Nikos", "Aren", "Damon"]
ELDER_NAMES = ["Nestor", "Iris", "Old Maro", "Teya", "Soros", "Helia"]


def valid_combo(place_id: str, obstacle_id: str, tool_id: str, helper_id: str) -> bool:
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    helper = HELPERS[helper_id]
    if tool.sense < SENSE_MIN:
        return False
    total = tool.power + helper.power
    return total >= obstacle.strength


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id in PLACES:
        for obstacle_id in OBSTACLES:
            for tool_id in TOOLS:
                for helper_id in HELPERS:
                    if valid_combo(place_id, obstacle_id, tool_id, helper_id):
                        combos.append((place_id, obstacle_id, tool_id, helper_id))
    return combos


def explain_rejection(obstacle: Obstacle, tool: Tool, helper: Helper) -> str:
    total = tool.power + helper.power
    return (
        f"(No story: {tool.phrase} with {helper.phrase} is too weak to free "
        f"{obstacle.phrase}. The child may wrestle bravely, but the world model "
        f"requires enough strength to liberate the blocked spring.)"
    )


def _do_block(world: World, obstacle: Obstacle) -> None:
    spring = world.get("spring")
    spring.meters["blocked"] += 1
    spring.attrs["obstacle"] = obstacle.id
    propagate(world, narrate=False)


def _do_liberate(world: World, obstacle: Obstacle, tool: Tool, helper: Helper, narrate: bool = True) -> None:
    spring = world.get("spring")
    hero = world.get("hero")
    grove = world.get("grove")
    spring.meters["blocked"] = 0.0
    spring.meters["flow"] += 1
    spring.meters["freed"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    grove.meters["bloom"] += 1
    produced = propagate(world, narrate=False)
    if narrate:
        world.say(obstacle.snap)
        world.say(
            "Cold water burst out from under the stones, first in threads, then in a silver rush."
        )
        if "__water_returns__" in produced:
            world.say(
                "The thirsty grove drank at once, and the valley seemed to breathe again."
            )


def predict_success(world: World, obstacle: Obstacle, tool: Tool, helper: Helper) -> bool:
    sim = world.copy()
    sim.facts["attempt_power"] = tool.power + helper.power
    return tool.power + helper.power >= obstacle.strength


def opening(world: World, hero: Entity, elder: Entity, place: Place, obstacle: Obstacle) -> None:
    spring = world.get("spring")
    village = world.get("village")
    world.say(
        f"In the days when hills were said to remember footsteps, {hero.id} climbed to {place.phrase}, {place.image}."
    )
    world.say(
        f"There, beside the old spring, {hero.pronoun()} found {obstacle.phrase} choking the water-mouth. "
        f"Only a weak dripping sound came from below, and even the grass nearby looked tired."
    )
    if spring.meters["blocked"] >= THRESHOLD:
        world.say(
            f"Below the slope, the village jars were growing light, and {elder.id} had come to see why the grove had gone thirsty."
        )
        village.memes["worry"] += 1


def flashback(world: World, elder: Entity, memory: ElderMemory) -> None:
    hero = world.get("hero")
    hero.memes["resolve"] += 1
    world.say(memory.opener)
    world.say(memory.body)
    world.say(memory.lesson)


def choose_tool(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["resolve"] += 1
    article = "an" if tool.phrase[:1].lower() in "aeiou" else "a"
    if tool.basic:
        world.say(
            f"{hero.id} looked around and found {tool.phrase} near the reeds. It was nothing grand, only a basic thing made for pulling baskets from water, but {hero.pronoun()} held it as if plain tools also had their hour."
        )
    else:
        world.say(
            f"{hero.id} picked up {article} {tool.label} lying by the shrine stones and tested its weight."
        )


def helper_arrives(world: World, helper: Helper) -> None:
    if helper.id != "alone":
        world.say(helper.arrival)


def wrestle_scene(world: World, hero: Entity, obstacle: Obstacle, tool: Tool, helper: Helper) -> None:
    total = tool.power + helper.power
    hero.memes["strain"] += 1
    world.say(
        f"Then {hero.id} began to wrestle with {obstacle.label}. {hero.pronoun().capitalize()} {tool.motion}."
    )
    if helper.id == "friend":
        world.say(
            f"Together they counted their pulls like temple drummers, and the tangle shivered against the stones."
        )
    elif helper.id == "goat":
        world.say(
            "The goat stamped, shoved, and made the vines jump as if the hillside itself had joined the struggle."
        )
    else:
        world.say(
            f"For a moment it seemed the snare would hold forever, and {hero.id}'s arms trembled with the effort."
        )
    world.facts["attempt_power"] = total


def ending(world: World, hero: Entity, elder: Entity, place: Place, obstacle: Obstacle, tool: Tool, helper: Helper) -> None:
    spring = world.get("spring")
    if spring.meters["flow"] >= THRESHOLD:
        hero.memes["joy"] += 1
        elder.memes["gratitude"] += 1
        world.say(
            f"{elder.id} cupped the water in both hands and laughed like someone much younger."
        )
        world.say(
            f"Soon the channels below filled, the leaves in {place.label} lifted, and children ran with empty jars that would not stay empty for long."
        )
        if tool.basic:
            world.say(
                f"{hero.id} set down the basic hook, shining with mud and water, and learned that even a simple thing can help liberate a blessing."
            )
        else:
            world.say(
                f"{hero.id} leaned on the {tool.label} and watched the clear stream braid sunlight across the stones."
            )
        world.say(
            f"And from that day on, people remembered how {hero.id} had dared to wrestle the mountain's knot and set the spring free."
        )


def tell(place: Place, obstacle: Obstacle, tool: Tool, helper: Helper, hero_name: str,
         hero_gender: str, elder_name: str, elder_gender: str, memory: ElderMemory) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_gender, label=elder_name, role="elder"))
    spring = world.add(Entity(id="spring", kind="thing", type="spring", label="spring", phrase="the old spring"))
    grove = world.add(Entity(id="grove", kind="thing", type="grove", label=place.label))
    village = world.add(Entity(id="village", kind="thing", type="village", label="the village"))
    if helper.id == "friend":
        helper_ent = world.add(Entity(id="helper", kind="character", type=hero_gender, label="friend", role="helper"))
    elif helper.id == "goat":
        helper_ent = world.add(Entity(id="helper", kind="thing", type="goat", label="goat", role="helper"))
    else:
        helper_ent = world.add(Entity(id="helper", kind="thing", type="silence", label="silence", role="helper"))

    _do_block(world, obstacle)
    opening(world, hero, elder, place, obstacle)

    world.para()
    flashback(world, elder, memory)

    world.para()
    choose_tool(world, hero, tool)
    helper_arrives(world, helper)
    wrestle_scene(world, hero, obstacle, tool, helper)
    _do_liberate(world, obstacle, tool, helper, narrate=True)

    world.para()
    ending(world, hero, elder, place, obstacle, tool, helper)

    world.facts.update(
        place=place,
        obstacle=obstacle,
        tool=tool,
        helper=helper,
        memory=memory,
        hero=hero,
        elder=elder,
        helper_entity=helper_ent,
        spring=spring,
        grove=grove,
        village=village,
        liberated=spring.meters["freed"] >= THRESHOLD,
        attempt_power=tool.power + helper.power,
        required_power=obstacle.strength,
        used_basic=tool.basic,
    )
    return world


KNOWLEDGE = {
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a part of a story that briefly looks back to something that happened earlier. It helps readers understand the present moment better."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up naturally from the ground. People, plants, and animals may depend on it."
        )
    ],
    "grove": [
        (
            "What is a grove?",
            "A grove is a small group of trees growing close together. Groves can give shade, fruit, and shelter."
        )
    ],
    "basic": [
        (
            "What does basic mean?",
            "Basic means simple and plain, not fancy. A basic tool can still be useful if it fits the job."
        )
    ],
    "wrestle": [
        (
            "What does wrestle mean?",
            "To wrestle means to struggle hard with something using your body and strength. People can wrestle an opponent or even a heavy tangled object."
        )
    ],
    "liberate": [
        (
            "What does liberate mean?",
            "To liberate means to set something free. In a story, a hero might liberate a trapped creature or blocked stream."
        )
    ],
    "reed": [
        (
            "What is a reed?",
            "A reed is a tall water plant with a thin stem. People can weave or shape reeds into simple tools."
        )
    ],
    "goat": [
        (
            "Why are mountain goats good on rocky hills?",
            "Mountain goats have strong legs and sure feet, so they can move on steep, stony ground more easily than people."
        )
    ],
}

KNOWLEDGE_ORDER = ["flashback", "spring", "grove", "basic", "wrestle", "liberate", "reed", "goat"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    return [
        'Write a short myth for a young child that includes the words "basic", "liberate", and "wrestle", and uses a flashback.',
        f"Tell a mythic story where {hero.label} climbs to {place.phrase}, hears an elder's flashback about a sacred spring, and then tries to liberate it from {obstacle.label}.",
        f"Write a simple myth in which a child uses {tool.phrase} and {helper.phrase} to free water for a village, with a remembered scene from long ago guiding the choice.",
        f"Tell a gentle myth where the past returns for a moment, and that memory gives a child courage to wrestle a blockage away from a spring.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    memory = world.facts["memory"]
    place = world.facts["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who climbed to {place.phrase}, and {elder.label}, who remembered the spring's old story. Together they helped bring hope back to the thirsty place."
        ),
        (
            "What problem did the hero find at the spring?",
            f"{hero.label} found {obstacle.phrase} choking the spring so the water could barely come out. Because the flow was blocked, the grove and village were beginning to thirst."
        ),
        (
            "Where is the flashback in the story?",
            f"The flashback comes when {elder.label} remembers how the spring helped the village long ago. That remembered scene explains why freeing the water matters so much now."
        ),
        (
            f"Why did {hero.label} decide to help liberate the spring?",
            f"{elder.label}'s memory showed that the spring had cared for the village before. That made {hero.label} feel responsible for protecting the old gift instead of walking away."
        ),
        (
            f"What did {hero.label} use while trying to wrestle the blockage free?",
            f"{hero.label} {tool.qa_text}. "
            + (
                f"{helper.qa_text.capitalize()} too, so the pulling strength was enough."
                if helper.id != "alone"
                else "No helper added extra strength, so the effort had to come from the hero alone."
            ),
        ),
    ]
    if world.facts["liberated"]:
        qa.append(
            (
                "How did the story end?",
                f"The spring ran free again, and the grove stopped thirsting. The ending image of water filling jars and brightening leaves shows that the rescue truly changed the valley."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"flashback", "spring", "grove", "wrestle", "liberate"}
    if world.facts["used_basic"]:
        tags.add("basic")
    if "reed" in world.facts["tool"].tags:
        tags.add("reed")
    if world.facts["helper"].id == "goat":
        tags.add("goat")
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cedar_hill",
        obstacle="roots",
        tool="reed_hook",
        helper="alone",
        hero="Mira",
        hero_gender="girl",
        elder="Iris",
        elder_gender="woman",
        memory="promise",
    ),
    StoryParams(
        place="sun_gorge",
        obstacle="brambles",
        tool="bare_hands",
        helper="friend",
        hero="Timon",
        hero_gender="boy",
        elder="Helia",
        elder_gender="woman",
        memory="song",
    ),
    StoryParams(
        place="moon_olive",
        obstacle="stone_net",
        tool="ash_staff",
        helper="goat",
        hero="Rhea",
        hero_gender="girl",
        elder="Nestor",
        elder_gender="elder",
        memory="lantern",
    ),
    StoryParams(
        place="moon_olive",
        obstacle="roots",
        tool="bare_hands",
        helper="friend",
        hero="Aren",
        hero_gender="boy",
        elder="Teya",
        elder_gender="woman",
        memory="promise",
    ),
]


ASP_RULES = r"""
valid_combo(P, O, T, H) :- place(P), obstacle(O), tool(T), helper(H),
                           tool_power(T, TP), helper_power(H, HP),
                           obstacle_strength(O, Need), TP + HP >= Need,
                           tool_sense(T, S), sense_min(M), S >= M.

chosen_ok :- chosen_obstacle(O), chosen_tool(T), chosen_helper(H),
             tool_power(T, TP), helper_power(H, HP),
             obstacle_strength(O, Need), TP + HP >= Need,
             tool_sense(T, S), sense_min(M), S >= M.

liberated :- chosen_ok.
#show valid_combo/4.
#show liberated/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_strength", oid, obstacle.strength))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_power", tid, tool.power))
        lines.append(asp.fact("tool_sense", tid, tool.sense))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_power", hid, helper.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_liberated(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show liberated/0."))
    return bool(asp.atoms(model, "liberated"))


def _check_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.memory not in MEMORIES:
        raise StoryError(f"(No story: unknown memory '{params.memory}'.)")
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if tool.sense < SENSE_MIN or not valid_combo(params.place, params.obstacle, params.tool, params.helper):
        raise StoryError(explain_rejection(obstacle, tool, helper))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    cases = list(CURATED)
    for idx in range(50):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(1000 + idx))
            cases.append(params)
        except StoryError:
            continue
    mismatch = 0
    for params in cases:
        try:
            py_ok = valid_combo(params.place, params.obstacle, params.tool, params.helper)
            asp_ok = asp_liberated(params)
            if py_ok != asp_ok:
                mismatch += 1
        except Exception:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP liberation parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} liberation outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child frees a blocked spring with help from a flashback and a simple tool."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "elder", "man"])
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.helper and args.obstacle:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        helper = HELPERS[args.helper]
        if not valid_combo(args.place or next(iter(PLACES)), args.obstacle, args.tool, args.helper):
            raise StoryError(explain_rejection(obstacle, tool, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, tool, helper = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "elder", "man"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    memory = args.memory or rng.choice(sorted(MEMORIES))
    return StoryParams(
        place=place,
        obstacle=obstacle,
        tool=tool,
        helper=helper,
        hero=hero,
        hero_gender=hero_gender,
        elder=elder,
        elder_gender=elder_gender,
        memory=memory,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        place=PLACES[params.place],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        helper=HELPERS[params.helper],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        elder_name=params.elder,
        elder_gender=params.elder_gender,
        memory=MEMORIES[params.memory],
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
        print(asp_program(show="#show valid_combo/4.\n#show liberated/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, tool, helper) combos:\n")
        for place, obstacle, tool, helper in combos:
            print(f"  {place:11} {obstacle:10} {tool:10} {helper}")
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
            header = f"### {p.hero}: {p.obstacle} at {p.place} with {p.tool} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
