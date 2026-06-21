#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py
=============================================================================================

A standalone storyworld for a tiny space-adventure domain shaped by the seed
words "astrology" and "tuv" plus the narrative features Transformation, Inner
Monologue, and Friendship.

Premise
-------
Two friends play at being space explorers in a small cardboard ship. They want
to fly to Tuv, a little moon with a silver bell-flower, but a space obstacle
blocks the way. One child worries, thinks quietly to themself, and almost gives
up. The other child uses friendship and a fitting bit of gear to help. The
worried child transforms from doubtful to brave, the pair use an astrology tool
that actually matches the obstacle, and the ending image proves that the
friendship changed the mission.

Reasonableness constraint
-------------------------
Not every navigation tool fits every obstacle. A moon lens can cut through a
dark mist, but it cannot steady a spinning asteroid ring. A star compass can
pick a path through moving rocks, but it is weak against a sleepy comet fog.
This world refuses mismatched combinations, and its inline ASP twin checks the
same compatibility rule.

Run it
------
python storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py
python storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py --destination tuv --obstacle mist --tool moon_lens
python storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py --obstacle ring --tool moon_lens
python storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py --all
python storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/astrology_tuv_transformation_inner_monologue_friendship_space.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # "character" | "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    treasure: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    problem: str
    warning: str
    route_word: str
    difficulty: int
    clears_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    use_text: str
    insight: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Form:
    id: str
    label: str
    phrase: str
    boast: str
    image: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


def _r_stuck(world: World) -> list[str]:
    ship = world.get("ship")
    obstacle = world.get("obstacle")
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    sig = ("stuck", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ship.meters["stalled"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__stuck__"]


def _r_transform(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["encouraged"] < THRESHOLD or hero.meters["wearing_form"] < THRESHOLD:
        return []
    sig = ("transform", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["brave"] += 2
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    return ["__transform__"]


def _r_clear(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    ship = world.get("ship")
    if obstacle.meters["solution"] < THRESHOLD:
        return []
    sig = ("clear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocking"] = 0.0
    ship.meters["stalled"] = 0.0
    ship.meters["moving"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
    return ["__clear__"]


CAUSAL_RULES = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="transform", tag="emotional", apply=_r_transform),
    Rule(name="clear", tag="physical", apply=_r_clear),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


DESTINATIONS = {
    "tuv": Destination(
        id="tuv",
        label="Tuv",
        phrase="the little moon Tuv",
        treasure="a silver bell-flower",
        sky="a blue moon-ring",
        tags={"tuv", "moon"},
    ),
    "aurora": Destination(
        id="aurora",
        label="Aurora Harbor",
        phrase="Aurora Harbor",
        treasure="a jar of singing stardust",
        sky="green ribbons of light",
        tags={"harbor", "stars"},
    ),
    "comet": Destination(
        id="comet",
        label="Comet Garden",
        phrase="Comet Garden",
        treasure="a comet seed that glowed warm orange",
        sky="slow silver tails",
        tags={"comet", "stars"},
    ),
}

OBSTACLES = {
    "mist": Obstacle(
        id="mist",
        label="sleepy star mist",
        phrase="a band of sleepy star mist",
        problem="The window filled with silver fog, and the cardboard ship could not see where to go.",
        warning="The mist hid the path and made every star look the same.",
        route_word="bright lane",
        difficulty=2,
        clears_with={"moon_lens", "astrology_chart"},
        tags={"mist", "stars"},
    ),
    "ring": Obstacle(
        id="ring",
        label="spinning pebble ring",
        phrase="a spinning pebble ring",
        problem="A ring of tiny space pebbles whirled around the ship like marbles in a bowl.",
        warning="The pebbles kept changing places, so a wrong turn would bump the ship.",
        route_word="safe gap",
        difficulty=2,
        clears_with={"star_compass", "astrology_chart"},
        tags={"asteroids", "space_rocks"},
    ),
    "glare": Obstacle(
        id="glare",
        label="sun-glare curtain",
        phrase="a curtain of golden glare",
        problem="A bright wall of sunlight flashed against the window and washed the star lines away.",
        warning="The glare was too strong for tired eyes and made the buttons hard to read.",
        route_word="cool shadow path",
        difficulty=1,
        clears_with={"moon_lens"},
        tags={"sunlight", "space"},
    ),
}

TOOLS = {
    "astrology_chart": Tool(
        id="astrology_chart",
        label="astrology chart",
        phrase="an astrology chart covered in moons and stars",
        kind="map",
        use_text="spread the astrology chart across the control panel and matched the signs to the real sky",
        insight="The chart showed which stars belonged together and which shining dots were only drifting fog.",
        power=2,
        tags={"astrology", "chart", "stars"},
    ),
    "moon_lens": Tool(
        id="moon_lens",
        label="moon lens",
        phrase="a moon lens with a round blue glass",
        kind="lens",
        use_text="held the moon lens to the window until the bright blur turned into one clear path",
        insight="The cool blue glass softened the glare and thinned the mist.",
        power=2,
        tags={"lens", "moon"},
    ),
    "star_compass": Tool(
        id="star_compass",
        label="star compass",
        phrase="a star compass with a humming needle",
        kind="compass",
        use_text="set the star compass humming and waited for its needle to point to the calmest opening",
        insight="The needle wiggled away from the moving pebbles and toward the quiet gap between them.",
        power=2,
        tags={"compass", "stars"},
    ),
}

FORMS = {
    "comet_cape": Form(
        id="comet_cape",
        label="Comet Captain",
        phrase="a red comet cape",
        boast="I can be small and still shine.",
        image="The cape snapped behind the seat like a tiny comet tail.",
        tags={"cape", "transformation"},
    ),
    "moon_helmet": Form(
        id="moon_helmet",
        label="Moon Pilot",
        phrase="a round silver moon helmet",
        boast="A steady head can guide a brave ship.",
        image="The helmet made the hero look as calm as the moon itself.",
        tags={"helmet", "transformation"},
    ),
    "star_boots": Form(
        id="star_boots",
        label="Star Walker",
        phrase="sparkly star boots",
        boast="My steps can find the safe path.",
        image="The boots flashed as if little constellations had landed on them.",
        tags={"boots", "transformation"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Leo", "Max", "Sam", "Finn", "Noah", "Theo", "Ben", "Eli"]
TRAITS = ["gentle", "curious", "careful", "thoughtful", "hopeful", "steady"]


@dataclass
class StoryParams:
    destination: str
    obstacle: str
    tool: str
    form: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        destination="tuv",
        obstacle="mist",
        tool="astrology_chart",
        form="comet_cape",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
        hero_trait="careful",
        friend_trait="hopeful",
    ),
    StoryParams(
        destination="aurora",
        obstacle="ring",
        tool="star_compass",
        form="moon_helmet",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        hero_trait="thoughtful",
        friend_trait="gentle",
    ),
    StoryParams(
        destination="comet",
        obstacle="glare",
        tool="moon_lens",
        form="star_boots",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        hero_trait="gentle",
        friend_trait="curious",
    ),
    StoryParams(
        destination="tuv",
        obstacle="ring",
        tool="astrology_chart",
        form="moon_helmet",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        parent="father",
        hero_trait="steady",
        friend_trait="hopeful",
    ),
]


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return tool.id in obstacle.clears_with and tool.power >= obstacle.difficulty


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dest_id in DESTINATIONS:
        for obs_id, obs in OBSTACLES.items():
            for tool_id, tool in TOOLS.items():
                if tool_fits(tool, obs):
                    combos.append((dest_id, obs_id, tool_id))
    return combos


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    good = ", ".join(sorted(obstacle.clears_with))
    return (
        f"(No story: {tool.label} is not a sensible way through {obstacle.phrase}. "
        f"This obstacle needs one of: {good}.)"
    )


def predict_block(world: World, tool_id: str) -> dict:
    sim = world.copy()
    tool = TOOLS[tool_id]
    obstacle_cfg = sim.facts["obstacle_cfg"]
    sim.get("tool").attrs["active_tool"] = tool.id
    if tool_fits(tool, obstacle_cfg):
        sim.get("obstacle").meters["solution"] += 1
        propagate(sim, narrate=False)
    return {
        "clears": sim.get("obstacle").meters["blocking"] < THRESHOLD,
        "ship_moving": sim.get("ship").meters["moving"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity, friend: Entity, dest: Destination, parent: Entity) -> None:
    ship = world.get("ship")
    ship.meters["moving"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After supper, {hero.id} and {friend.id} climbed into a cardboard rocket by the sofa."
    )
    world.say(
        f"They were space friends on a mission to {dest.phrase}, where {dest.treasure} grew under {dest.sky}."
    )
    world.say(
        f"{parent.label_word.capitalize()} tucked in a blanket star-map, smiled, and said, "
        f'"Space crews do best when they listen to each other."'
    )


def launch(world: World, hero: Entity, friend: Entity, tool: Tool, dest: Destination) -> None:
    world.say(
        f'"Next stop, {dest.label}!" {friend.id} said, tapping the dashboard made from a cereal box.'
    )
    world.say(
        f"{hero.id} kept {tool.phrase} beside the buttons, just in case the sky grew tricky."
    )


def meet_obstacle(world: World, obstacle: Obstacle) -> None:
    ship = world.get("ship")
    obs = world.get("obstacle")
    ship.meters["moving"] = 0.0
    obs.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.problem)
    world.say(obstacle.warning)


def inner_monologue(world: World, hero: Entity, dest: Destination) -> None:
    hero.memes["doubt"] += 1
    thought = (
        f"{hero.id} pressed a hand to {hero.pronoun('possessive')} chest. "
        f'Inside, {hero.pronoun()} thought, "What if I am too small to guide a ship all the way to {dest.label}?"'
    )
    world.say(thought)
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f'"My tummy feels all wiggly," {hero.id} whispered. "I do not want to lose our way."'
        )


def encourage(world: World, friend: Entity, hero: Entity, form: Form) -> None:
    hero.memes["encouraged"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} scooted closer and bumped {hero.pronoun('possessive')} shoulder with a gentle grin."
    )
    world.say(
        f'"You do not have to be big," {friend.id} said. "You only have to be you. '
        f'Put on {form.phrase}, and I will be your co-pilot."'
    )


def transform(world: World, hero: Entity, form: Form) -> None:
    hero.meters["wearing_form"] += 1
    propagate(world, narrate=False)
    hero.attrs["form_name"] = form.label
    world.say(
        f"{hero.id} pulled on {form.phrase}. In that moment, {hero.pronoun()} was not only a worried child anymore."
    )
    world.say(
        f"{hero.pronoun().capitalize()} became {form.label} in {hero.pronoun('possessive')} own mind. {form.image}"
    )
    world.say(
        f'{hero.pronoun().capitalize()} took a long breath and thought, "{form.boast}"'
    )


def choose_tool(world: World, hero: Entity, tool: Tool, obstacle: Obstacle) -> None:
    pred = predict_block(world, tool.id)
    world.facts["predicted_clear"] = pred["clears"]
    world.say(
        f"{hero.id} looked from the obstacle to the stars and remembered the rules of pretend astrology."
    )
    world.say(tool.insight)
    if not pred["clears"]:
        raise StoryError(explain_rejection(obstacle, tool))
    world.say(
        f"That meant {tool.label} could open a {obstacle.route_word} through {obstacle.label}."
    )


def solve(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    obstacle_ent = world.get("obstacle")
    world.get("tool").attrs["active_tool"] = tool.id
    obstacle_ent.meters["solution"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} {tool.use_text}."
    )
    world.say(
        f"{friend.id} counted softly, and together they steered left, then right, then straight ahead."
    )


def arrive(world: World, hero: Entity, friend: Entity, dest: Destination) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"The ship slipped through at last, and soon {dest.phrase} floated ahead like a bright marble in the dark."
    )
    world.say(
        f"There they found {dest.treasure}. {hero.id} and {friend.id} held it together, laughing because the mission had needed both brave thinking and friendship."
    )


def closing_image(world: World, hero: Entity, friend: Entity, form: Form, parent: Entity) -> None:
    world.say(
        f"When they climbed out of the cardboard rocket, {parent.label_word} asked whether the crew had made it."
    )
    world.say(
        f'"Yes," {hero.id} said, still wearing {form.phrase}. "And a co-pilot can help a captain grow brave."'
    )
    world.say(
        f"{friend.id} nodded. The room was only a room again, but the two friends still glowed as if a little piece of space had come home with them."
    )


def tell(
    dest: Destination,
    obstacle: Obstacle,
    tool: Tool,
    form: Form,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    friend_name: str = "Max",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    hero_trait: str = "careful",
    friend_trait: str = "hopeful",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[hero_trait],
            label=hero_name,
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[friend_trait],
            label=friend_name,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(Entity(id="ship", type="ship", label="cardboard rocket"))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    world.add(Entity(id="tool", type="tool", label=tool.label))

    intro(world, hero, friend, dest, parent)
    launch(world, hero, friend, tool, dest)

    world.para()
    meet_obstacle(world, obstacle)
    inner_monologue(world, hero, dest)
    encourage(world, friend, hero, form)

    world.para()
    transform(world, hero, form)
    choose_tool(world, hero, tool, obstacle)
    solve(world, hero, friend, tool)

    world.para()
    arrive(world, hero, friend, dest)
    closing_image(world, hero, friend, form, parent)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        destination=dest,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        form_cfg=form,
        transformed=hero.meters["wearing_form"] >= THRESHOLD and hero.memes["brave"] >= THRESHOLD,
        cleared=world.get("obstacle").meters["blocking"] < THRESHOLD,
        friendship_help=hero.memes["encouraged"] >= THRESHOLD,
        monologue=hero.memes["doubt"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "astrology": [
        (
            "What is astrology in a pretend space game?",
            "In a pretend game, astrology can mean looking at stars and moon signs to make a story about where to go. It is a pattern game with the sky."
        )
    ],
    "tuv": [
        (
            "What is Tuv in this storyworld?",
            "Tuv is a little moon the children pretend to visit in their cardboard rocket. It gives the adventure a clear place to reach."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps you choose a direction. In a space game, a star compass points toward the safest way to travel."
        )
    ],
    "lens": [
        (
            "What does a lens do?",
            "A lens helps your eyes see things more clearly. It can make a blurry path look sharp enough to follow."
        )
    ],
    "friendship": [
        (
            "How can a friend help when you feel worried?",
            "A friend can stay close, speak kindly, and remind you that you do not have to solve everything alone. That kind of help can make your brave feelings grow."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story like this?",
            "Transformation means someone changes in an important way. Here the child changes from doubtful to brave after support and imagination."
        )
    ],
    "space_rocks": [
        (
            "Why are space rocks hard to fly through?",
            "Moving rocks are hard to fly through because they keep changing where the open gaps are. A pilot has to watch carefully to avoid bumping into them."
        )
    ],
    "mist": [
        (
            "Why is mist hard to travel through?",
            "Mist makes it hard to see where the path is. When everything looks blurry, a traveler can lose the right way."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "astrology",
    "tuv",
    "mist",
    "space_rocks",
    "lens",
    "compass",
    "friendship",
    "transformation",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    dest = f["destination"]
    tool = f["tool_cfg"]
    return [
        f'Write a gentle space adventure for a 3-to-5-year-old that includes the words "astrology" and "{dest.id}".',
        f"Tell a story about two friends in a cardboard rocket where {hero.id} worries silently, transforms into a braver self, and reaches {dest.label} with {friend.id}'s help.",
        f"Write a child-facing friendship story where a fitting tool like {tool.label} solves a real obstacle in space instead of magic solving everything at once.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    dest = f["destination"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    form = f["form_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two friends playing space explorers together. {parent.label_word.capitalize()} helps the adventure begin, but the children do the brave work themselves."
        ),
        (
            f"Where were they trying to go?",
            f"They were trying to reach {dest.phrase}. That place mattered because they wanted to find {dest.treasure} there."
        ),
        (
            "What problem stopped the ship?",
            f"The ship was stopped by {obstacle.phrase}. It was a real problem in the game because {obstacle.warning.lower()}"
        ),
    ]
    if f.get("monologue"):
        qa.append(
            (
                f"What did {hero.id} think quietly to {hero.pronoun('object')}self?",
                f"{hero.id} worried that {hero.pronoun()} might be too small to guide the ship all the way to {dest.label}. That inner thought shows the fear before the brave change happens."
            )
        )
    if f.get("friendship_help"):
        qa.append(
            (
                f"How did {friend.id} help {hero.id}?",
                f"{friend.id} moved close, spoke kindly, and offered to be a co-pilot instead of leaving {hero.id} alone with the problem. That friendship gave {hero.id} enough courage to try again."
            )
        )
    if f.get("transformed"):
        qa.append(
            (
                f"How did {hero.id} transform?",
                f"{hero.id} put on {form.phrase} and began to think of {hero.pronoun('object')}self as {form.label}. The outside costume mattered because it helped the inside feelings turn from worry into bravery."
            )
        )
    if f.get("cleared"):
        qa.append(
            (
                f"How did they get past {obstacle.label}?",
                f"{hero.id} used {tool.label} because it matched the kind of trouble in front of the ship. Then {friend.id} counted and steered along, so the answer came from both the right tool and teamwork."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They reached {dest.phrase} and found {dest.treasure}. At the end, the mission proves that friendship helped the hero become brave enough to finish the journey."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["destination"].tags) | set(f["obstacle_cfg"].tags) | set(f["tool_cfg"].tags)
    tags |= {"friendship", "transformation", "astrology"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(Tool, Obs) :- clears_with(Obs, Tool), power(Tool, P), difficulty(Obs, D), P >= D.
valid(Dest, Obs, Tool) :- destination(Dest), obstacle(Obs), tool(Tool), fits(Tool, Obs).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for oid, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("difficulty", oid, obs.difficulty))
        for tid in sorted(obs.clears_with):
            lines.append(asp.fact("clears_with", oid, tid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, tool.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: space friends, inner monologue, transformation, and a fitting star tool."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, obstacle):
            raise StoryError(explain_rejection(obstacle, tool))

    combos = [
        c
        for c in valid_combos()
        if (args.destination is None or c[0] == args.destination)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, obstacle, tool = rng.choice(sorted(combos))
    form = args.form or rng.choice(sorted(FORMS))
    hero_name, hero_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)
    return StoryParams(
        destination=destination,
        obstacle=obstacle,
        tool=tool,
        form=form,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        dest = DESTINATIONS[params.destination]
        obstacle = OBSTACLES[params.obstacle]
        tool = TOOLS[params.tool]
        form = FORMS[params.form]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if not tool_fits(tool, obstacle):
        raise StoryError(explain_rejection(obstacle, tool))

    world = tell(
        dest=dest,
        obstacle=obstacle,
        tool=tool,
        form=form,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (destination, obstacle, tool) combos:\n")
        for dest, obstacle, tool in combos:
            print(f"  {dest:10} {obstacle:8} {tool}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.destination} via {p.obstacle} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
