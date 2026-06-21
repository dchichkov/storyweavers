#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py
=================================================================================

A small storyworld about a child in a superhero costume who sees a flashy
commercial for a Yumsy snack, mistakes the ad for real hero science, and then
learns that ordinary tools and careful help matter more than braggy promises.

The seed asked for:
- the words "yumsy", "blase", and "commercial"
- the instruments Twist, Inner Monologue, and Lesson Learned
- a style close to a Superhero Story

This world makes those requests state-driven:

* A child wants to be a superhero helper.
* A local commercial for a Yumsy snack makes a false promise that feels tempting.
* A real neighborhood problem appears.
* The child's inner monologue leans toward the ad and grows a little blase about
  the plain tool that would actually help.
* The twist: the caped "hero" from the commercial is just the nearby shopkeeper
  in costume, and they say the ad was only pretend.
* The child solves the problem with the right tool and learns what real heroism is.

Run it
------
    python storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py
    python storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py --challenge kite
    python storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py --product yumsy_glow
    python storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py --all
    python storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py --qa
    python storyworlds/worlds/gpt-5.4/yumsy_blase_commercial_twist_inner_monologue_lesson.py --verify
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Product:
    id: str
    name: str
    word: str
    claim: str
    slogan: str
    lure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    place: str
    problem: str
    need: str
    sight: str
    cry: str
    solve_text: str
    solved_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    capability: str
    sense: int
    use_text: str
    qa_text: str
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


def _r_problem_pressure(world: World) -> list[str]:
    out: list[str] = []
    issue = world.get("issue")
    if issue.meters["active"] < THRESHOLD:
        return out
    sig = ("pressure", issue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    out.append("__pressure__")
    return out


def _r_false_attempt(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    issue = world.get("issue")
    if hero.meters["snack_belief"] < THRESHOLD or issue.meters["active"] < THRESHOLD:
        return out
    sig = ("false_attempt", issue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["embarrassment"] += 1
    hero.memes["doubt"] += 1
    issue.meters["active"] += 1
    out.append("__false_attempt__")
    return out


def _r_tool_success(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    issue = world.get("issue")
    tool = world.get("tool")
    if hero.meters["uses_tool"] < THRESHOLD or issue.meters["active"] < THRESHOLD:
        return out
    if tool.attrs.get("capability") != world.facts["challenge"].need:
        return out
    sig = ("tool_success", issue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    issue.meters["active"] = 0.0
    issue.meters["solved"] += 1
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    friend.memes["relief"] += 1
    out.append("__tool_success__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_pressure", tag="social", apply=_r_problem_pressure),
    Rule(name="false_attempt", tag="social", apply=_r_false_attempt),
    Rule(name="tool_success", tag="physical", apply=_r_tool_success),
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


def product_matches_challenge(product: Product, challenge: Challenge) -> bool:
    return product.claim in CHALLENGE_LURES[challenge.id]


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def tool_solves_challenge(tool: Tool, challenge: Challenge) -> bool:
    return tool.capability == challenge.need and tool.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for product_id, product in PRODUCTS.items():
        for challenge_id, challenge in CHALLENGES.items():
            if not product_matches_challenge(product, challenge):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_solves_challenge(tool, challenge):
                    combos.append((product_id, challenge_id, tool_id))
    return combos


def predict_attempt_fails(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").meters["snack_belief"] += 1
    propagate(sim, narrate=False)
    return sim.get("issue").meters["solved"] < THRESHOLD


def introduce(world: World, hero: Entity, friend: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} zipped around the sidewalk in a homemade cape, while {friend.id} trotted beside "
        f"{hero.pronoun('object')} with a paper star taped to {friend.pronoun('possessive')} shirt."
    )
    world.say(
        f'Today they were not pretending to be ordinary kids at all. They were "Sky Flash" and '
        f'"Patch Pal," two neighborhood superheroes looking for someone to help.'
    )
    world.say(
        f"{hero.id}'s {parent.label_word} had told them that real heroes watched carefully before they leaped."
    )


def commercial_scene(world: World, hero: Entity, product: Product, vendor: Entity) -> None:
    hero.memes["belief"] += 1
    world.say(
        f"Outside {vendor.attrs['shop']}, a little screen in the window played a bright commercial. "
        f"In it, a caped hero bit into {product.name} and boomed, "
        f'"{product.slogan}"'
    )
    world.say(
        f"The word {product.word} flashed in bubble letters across the screen, and the hero on the ad "
        f"struck such a proud pose that {hero.id} stared without blinking."
    )


def inner_monologue(world: World, hero: Entity, product: Product, challenge: Challenge, tool: Tool) -> None:
    world.say(
        f"Inside {hero.pronoun('possessive')} head, {hero.id} thought, "
        f'"If that commercial is telling the truth, maybe {product.name} can help me {product.lure}. '
        f'Then I would look like a real superhero."'
    )
    world.say(
        f"For one foolish moment, {hero.pronoun()} felt blase about {tool.phrase}. "
        f"It looked plain and ordinary next to a shiny superhero promise."
    )
    world.facts["predicted_fail"] = predict_attempt_fails(world)
    if world.facts["predicted_fail"]:
        world.say(
            f"But another tiny thought tapped back: plain things often work better than pretend ones."
        )


def problem_appears(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    issue = world.get("issue")
    issue.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {challenge.sight}")
    world.say(f'{challenge.cry}')
    world.say(
        f"{hero.id} stopped so fast that {hero.pronoun('possessive')} cape fluttered around {hero.pronoun('object')} like a flag."
    )


def friend_warns(world: World, friend: Entity, hero: Entity, product: Product, tool: Tool) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'"A commercial is for selling snacks," {friend.id} said. "It is not a box of real powers. '
        f'We should use {tool.phrase}."'
    )


def snack_attempt(world: World, hero: Entity, product: Product, challenge: Challenge) -> None:
    hero.meters["snack_belief"] += 1
    hero.meters["snack_bites"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} popped a piece of {product.name} into {hero.pronoun('possessive')} mouth, squared "
        f"{hero.pronoun('possessive')} shoulders, and tried to solve the problem with pure snack-powered confidence."
    )
    if challenge.id == "kite":
        world.say(
            f"{hero.pronoun().capitalize()} jumped and tugged, but the kite only danced higher in the leaves."
        )
    elif challenge.id == "wagon":
        world.say(
            f"{hero.pronoun().capitalize()} sprinted after the wagon, but fast feet did not tell the wheels how to stop."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} squinted into the dark shed, but the shadows stayed thick and black."
        )


def twist_reveal(world: World, vendor: Entity, product: Product) -> None:
    hero = world.get("hero")
    vendor.memes["kindness"] += 1
    world.say(
        f"Just then the shop door jingled, and out stepped {vendor.id}. {vendor.pronoun().capitalize()} was the very same smiling face "
        f"from the commercial, only now the cape was hanging from one hand and the shiny mask was tucked in a pocket."
    )
    world.say(
        f'"Twist of the day," {vendor.id} said with a warm grin. "I played Captain Yumsy for the ad, '
        f'but {product.name} is only a snack. Commercials can be fun, yet they are still pretend."'
    )
    hero.memes["belief"] = 0.0
    hero.memes["doubt"] += 1


def offer_tool(world: World, vendor: Entity, tool: Tool, challenge: Challenge) -> None:
    tool_ent = world.get("tool")
    tool_ent.attrs["capability"] = tool.capability
    world.say(
        f"{vendor.id} reached beside the door and held up {tool.phrase}. "
        f'"For this job, a hero wants the right tool," {vendor.pronoun()} said.'
    )
    world.say(
        f"{world.get('friend').id} nodded so hard that {world.get('friend').pronoun('possessive')} paper star bent sideways."
    )
    world.say(
        f"Now {tool.phrase} did not seem boring at all. It looked exactly like what the moment needed."
    )


def use_tool(world: World, hero: Entity, tool: Tool, challenge: Challenge) -> None:
    hero.meters["uses_tool"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took {tool.phrase}, breathed once, and {tool.use_text}."
    )
    world.say(challenge.solve_text)
    world.say(challenge.solved_image)


def lesson(world: World, hero: Entity, friend: Entity, parent: Entity, product: Product) -> None:
    hero.memes["lesson"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'{hero.id} looked at the bright Yumsy wrapper in {hero.pronoun("possessive")} hand, then folded it small and slipped it into '
        f"{hero.pronoun('possessive')} pocket."
    )
    world.say(
        f'"I get it now," {hero.pronoun()} said. "A snack can be yumsy, but it cannot do a tool\'s job for me."'
    )
    world.say(
        f"{friend.id} smiled. {parent.label_word.capitalize()} ruffled {hero.id}'s hair and said, "
        f'"That is the real superhero lesson. Listen, think, and help with what is true."'
    )


def closing(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"When the two children hurried down the sidewalk again, {hero.id}'s cape still fluttered behind {hero.pronoun('object')}, "
        f"but now it matched something real inside {hero.pronoun('object')}: good sense."
    )
    world.say(
        f"And that made {hero.id} feel more heroic than any commercial ever could."
    )


def tell(
    product: Product,
    challenge: Challenge,
    tool: Tool,
    *,
    hero_name: str = "Milo",
    hero_type: str = "boy",
    friend_name: str = "Tess",
    friend_type: str = "girl",
    parent_type: str = "mother",
    vendor_name: str = "Ms. Vega",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", label=friend_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    vendor = world.add(
        Entity(
            id=vendor_name,
            kind="character",
            type="woman",
            role="vendor",
            label=vendor_name,
            attrs={"shop": "the Corner Market"},
        )
    )
    issue = world.add(Entity(id="issue", kind="thing", type="problem", label=challenge.id))
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            attrs={"capability": tool.capability},
        )
    )

    introduce(world, hero, friend, parent)
    commercial_scene(world, hero, product, vendor)

    world.para()
    problem_appears(world, hero, friend, challenge)
    inner_monologue(world, hero, product, challenge, tool)
    friend_warns(world, friend, hero, product, tool)
    snack_attempt(world, hero, product, challenge)

    world.para()
    twist_reveal(world, vendor, product)
    offer_tool(world, vendor, tool, challenge)
    use_tool(world, hero, tool, challenge)
    lesson(world, hero, friend, parent, product)

    world.para()
    closing(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        vendor=vendor,
        product=product,
        challenge=challenge,
        tool_cfg=tool,
        issue=issue,
        attempt_failed=hero.memes["embarrassment"] >= THRESHOLD,
        solved=issue.meters["solved"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
        twist_revealed=hero.memes["belief"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    product: str
    challenge: str
    tool: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    parent_type: str
    vendor_name: str
    seed: Optional[int] = None


PRODUCTS = {
    "yumsy_mighty": Product(
        id="yumsy_mighty",
        name="Yumsy Mighty Puffs",
        word="yumsy",
        claim="muscle",
        slogan="One puff and mighty enough!",
        lure="pull something down with huge strength",
        tags={"yumsy", "commercial", "advertising", "strength"},
    ),
    "yumsy_zoom": Product(
        id="yumsy_zoom",
        name="Yumsy Zoom Bites",
        word="yumsy",
        claim="speed",
        slogan="Zip, zoom, save the room!",
        lure="run faster than a rolling wagon",
        tags={"yumsy", "commercial", "advertising", "speed"},
    ),
    "yumsy_glow": Product(
        id="yumsy_glow",
        name="Yumsy Glow Gummies",
        word="yumsy",
        claim="light",
        slogan="Glow bright and own the night!",
        lure="see through darkness all by yourself",
        tags={"yumsy", "commercial", "advertising", "light"},
    ),
}

CHALLENGES = {
    "kite": Challenge(
        id="kite",
        place="by the oak tree",
        problem="a kite was stuck high in the oak tree",
        need="reach",
        sight="a red kite snapped on a branch high above the sidewalk, its tail flicking like a worried ribbon.",
        cry='"Oh no!" cried a little boy below. "My kite is trapped!"',
        solve_text="With a careful stretch, hero and helper nudged the branch and lifted the string free.",
        solved_image="The kite floated down into waiting hands, and the boy hugged it to his chest as if it were a rescued bird.",
        tags={"kite", "tree", "reach"},
    ),
    "wagon": Challenge(
        id="wagon",
        place="near the curb",
        problem="a wagon was rolling toward the curb",
        need="brake",
        sight="a little wagon full of canned food began rolling by itself toward the curb at the end of the block.",
        cry='"The donation wagon!" called an old man. "Please stop it!"',
        solve_text="Hero reached the handle in time and pressed the brake lever down until the wheels gave one last squeak and stopped.",
        solved_image="The cans settled with a soft clink, safe and still, while everyone on the sidewalk let out the same relieved breath.",
        tags={"wagon", "brake", "helping"},
    ),
    "kitten": Challenge(
        id="kitten",
        place="at the garden shed",
        problem="a kitten was mewing in a dark shed",
        need="light",
        sight="from the garden shed came a tiny, worried mew, and the open doorway was dark as a pocket.",
        cry='"Pip is in there somewhere," whispered a girl, clutching the empty kitten basket.',
        solve_text="A steady beam slid across the floorboards until two bright kitten eyes blinked back from behind a rake.",
        solved_image="Soon the kitten was tucked into the basket, purring so hard that the handle trembled.",
        tags={"kitten", "dark", "light"},
    ),
}

TOOLS = {
    "reacher": Tool(
        id="reacher",
        label="grabber pole",
        phrase="a long grabber pole",
        capability="reach",
        sense=3,
        use_text="raised it toward the branch instead of trying to leap like a movie hero",
        qa_text="used a long grabber pole to reach the kite safely",
        tags={"tool", "reach", "helper"},
    ),
    "brake": Tool(
        id="brake",
        label="brake lever",
        phrase="the wagon's plain gray brake lever",
        capability="brake",
        sense=3,
        use_text="caught the handle and pressed the brake lever instead of just running harder",
        qa_text="pressed the wagon's brake lever to stop the wheels",
        tags={"tool", "brake", "helper"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        capability="light",
        sense=3,
        use_text="shone it low and slow instead of trusting gummy glow-power",
        qa_text="used a bright flashlight to search the dark shed",
        tags={"tool", "flashlight", "helper"},
    ),
    "cape_spin": Tool(
        id="cape_spin",
        label="cape spin",
        phrase="a wild cape spin",
        capability="showoff",
        sense=1,
        use_text="spun the cape",
        qa_text="spun a cape",
        tags={"showoff"},
    ),
}

CHALLENGE_LURES = {
    "kite": {"muscle"},
    "wagon": {"speed"},
    "kitten": {"light"},
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Milo", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
VENDOR_NAMES = ["Ms. Vega", "Mr. Reed", "Aunt June", "Ms. Sol"]
PARENT_TYPES = ["mother", "father"]


KNOWLEDGE = {
    "advertising": [
        (
            "What is a commercial?",
            "A commercial is a short advertisement that tries to make people want a product. It can be exciting and silly, but it is not the same as real life."
        )
    ],
    "yumsy": [
        (
            "Can a snack give you real superhero powers?",
            "No. A snack can give your body food and energy, but it cannot give you magical flying, glowing, or giant strength powers."
        )
    ],
    "strength": [
        (
            "What helps more than pretending to be strong?",
            "Using the right tool and asking for help helps more than pretending. Real problem-solving is usually careful, not flashy."
        )
    ],
    "speed": [
        (
            "Why does running fast not always solve a problem?",
            "Some problems need a special action, like pressing a brake, not just moving quickly. Fast feet cannot do every job."
        )
    ],
    "light": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight makes real light that helps you see where things are. It works better than guessing in the dark."
        )
    ],
    "reach": [
        (
            "Why can a long tool be safer than jumping?",
            "A long tool lets you reach something high while keeping your feet on the ground. That makes it steadier and safer."
        )
    ],
    "brake": [
        (
            "What does a brake do?",
            "A brake helps wheels slow down and stop. It is made for control, which is why it works better than panic."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a small lamp you can carry in your hand. It gives real light without any magic."
        )
    ],
    "helper": [
        (
            "What makes someone a real hero helper?",
            "A real hero helper notices what is needed and uses true help, even if it looks plain. Being wise and kind is more important than looking grand."
        )
    ],
}
KNOWLEDGE_ORDER = ["advertising", "yumsy", "strength", "speed", "light", "reach", "brake", "flashlight", "helper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    product = f["product"]
    tool = f["tool_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "{product.word}" and the word "commercial."',
        f"Tell a story where {hero.id} sees a flashy ad for {product.name}, thinks about using pretend powers, then learns to solve a real problem with {tool.phrase}.",
        f"Write a child-facing story with an inner monologue, a twist reveal, and a lesson learned after a neighborhood problem involving {challenge.problem}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    vendor = f["vendor"]
    product = f["product"]
    challenge = f["challenge"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in a superhero cape, {friend.id}, a careful friend, and {vendor.id}, the shopkeeper from the commercial."
        ),
        (
            "What problem appeared in the story?",
            f"The children noticed that {challenge.problem}. That turned their pretend superhero walk into a real moment to help someone."
        ),
        (
            f"What did {hero.id} think after seeing the commercial?",
            f"{hero.id} thought {product.name} might give real hero help because the ad looked bright and convincing. Inside {hero.pronoun('possessive')} head, {hero.pronoun()} started to believe the snack might do the job for {hero.pronoun('object')}."
        ),
        (
            f"Why does the story say {hero.id} felt blase about the tool?",
            f"{hero.id} briefly felt blase about {tool.phrase} because it looked ordinary next to the shiny commercial promise. That feeling mattered because it almost made {hero.pronoun('object')} ignore the thing that truly worked."
        ),
    ]
    if f["attempt_failed"]:
        qa.append(
            (
                f"What happened when {hero.id} tried the snack idea first?",
                f"The first idea failed, and the problem stayed active. That showed {hero.id} that confidence from an advertisement is not the same as a real way to help."
            )
        )
    if f["twist_revealed"]:
        qa.append(
            (
                "What was the twist?",
                f"The caped superhero from the commercial turned out to be {vendor.id} from the shop. The ad was only pretend, and {vendor.pronoun()} said so out loud."
            )
        )
    qa.append(
        (
            f"How was the problem solved in the end?",
            f"{hero.id} {tool.qa_text}. The plain tool matched what the problem actually needed, which is why the ending changed from shaky hope to real help."
        )
    )
    qa.append(
        (
            "What lesson did the hero learn?",
            f"{hero.id} learned that a snack may taste yumsy, but it cannot replace truth, tools, or careful thinking. Real heroes watch, listen, and use what the moment really needs."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["product"].tags) | set(f["challenge"].tags) | set(f["tool_cfg"].tags) | {"helper"}
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(product: Product, challenge: Challenge, tool: Optional[Tool] = None) -> str:
    if not product_matches_challenge(product, challenge):
        return (
            f"(No story: {product.name} promises {product.claim}, but the challenge needs {challenge.need}. "
            f"The temptation should match the problem closely enough to feel believable.)"
        )
    if tool is not None and tool.sense < SENSE_MIN:
        return (
            f"(No story: '{tool.id}' is known to the world, but it is too showy or weak to count as a sensible fix. "
            f"Pick a real tool instead.)"
        )
    if tool is not None and tool.capability != challenge.need:
        return (
            f"(No story: {tool.phrase} does not solve this problem. The challenge needs something that can {challenge.need}.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
match(P, C) :- product_claim(P, Need), challenge_lure(C, Need).
sensible(T) :- tool(T), tool_sense(T, S), sense_min(M), S >= M.
solves(T, C) :- tool_capability(T, Need), challenge_need(C, Need), sensible(T).
valid(P, C, T) :- product(P), challenge(C), tool(T), match(P, C), solves(T, C).

outcome(learned) :- valid(P, C, T), chosen_product(P), chosen_challenge(C), chosen_tool(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for product_id, product in PRODUCTS.items():
        lines.append(asp.fact("product", product_id))
        lines.append(asp.fact("product_claim", product_id, product.claim))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("challenge_need", challenge_id, challenge.need))
        for lure in sorted(CHALLENGE_LURES[challenge_id]):
            lines.append(asp.fact("challenge_lure", challenge_id, lure))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_capability", tool_id, tool.capability))
        lines.append(asp.fact("tool_sense", tool_id, tool.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_product", params.product),
            asp.fact("chosen_challenge", params.challenge),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if (
        params.product in PRODUCTS
        and params.challenge in CHALLENGES
        and params.tool in TOOLS
        and (params.product, params.challenge, params.tool) in set(valid_combos())
    ):
        return "learned"
    return "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH outcome for {params}: asp={asp_outcome(params)} python={outcome_of(params)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "commercial" not in sample.story.lower() or "yumsy" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missed required seed words.)")
        if sample.world is None:
            raise StoryError("(Smoke test failed: missing world object.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero-loving child, a flashy commercial, and a real lesson."
    )
    ap.add_argument("--product", choices=PRODUCTS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
    ap.add_argument("--vendor-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.product and args.challenge:
        product = PRODUCTS[args.product]
        challenge = CHALLENGES[args.challenge]
        if not product_matches_challenge(product, challenge):
            raise StoryError(explain_rejection(product, challenge))
    if args.tool:
        tool = TOOLS[args.tool]
        if tool.sense < SENSE_MIN:
            product = PRODUCTS[args.product] if args.product else next(iter(PRODUCTS.values()))
            challenge = CHALLENGES[args.challenge] if args.challenge else next(iter(CHALLENGES.values()))
            raise StoryError(explain_rejection(product, challenge, tool))
        if args.challenge and tool.capability != CHALLENGES[args.challenge].need:
            product = PRODUCTS[args.product] if args.product else next(iter(PRODUCTS.values()))
            raise StoryError(explain_rejection(product, CHALLENGES[args.challenge], tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.product is None or combo[0] == args.product)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    product_id, challenge_id, tool_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)
    return StoryParams(
        product=product_id,
        challenge=challenge_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent_type=args.parent_type or rng.choice(PARENT_TYPES),
        vendor_name=args.vendor_name or rng.choice(VENDOR_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.product not in PRODUCTS:
        raise StoryError(f"(Unknown product: {params.product})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    product = PRODUCTS[params.product]
    challenge = CHALLENGES[params.challenge]
    tool = TOOLS[params.tool]

    if not product_matches_challenge(product, challenge):
        raise StoryError(explain_rejection(product, challenge))
    if not tool_solves_challenge(tool, challenge):
        raise StoryError(explain_rejection(product, challenge, tool))

    world = tell(
        product=product,
        challenge=challenge,
        tool=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.parent_type,
        vendor_name=params.vendor_name,
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


CURATED = [
    StoryParams(
        product="yumsy_mighty",
        challenge="kite",
        tool="reacher",
        hero_name="Milo",
        hero_type="boy",
        friend_name="Tess",
        friend_type="girl",
        parent_type="mother",
        vendor_name="Ms. Vega",
    ),
    StoryParams(
        product="yumsy_zoom",
        challenge="wagon",
        tool="brake",
        hero_name="Ava",
        hero_type="girl",
        friend_name="Ben",
        friend_type="boy",
        parent_type="father",
        vendor_name="Mr. Reed",
    ),
    StoryParams(
        product="yumsy_glow",
        challenge="kitten",
        tool="flashlight",
        hero_name="Leo",
        hero_type="boy",
        friend_name="Maya",
        friend_type="girl",
        parent_type="mother",
        vendor_name="Aunt June",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (product, challenge, tool) combos:\n")
        for product, challenge, tool in combos:
            print(f"  {product:13} {challenge:8} {tool}")
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
            header = f"### {p.hero_name}: {p.product} / {p.challenge} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
