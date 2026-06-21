#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py
==================================================================

A standalone story world for a heartwarming transformation tale built around
gazpacho. A child starts with a doubtful feeling about a bowl of chopped garden
vegetables, then helps a caring grown-up transform the same vegetables into a
cool, smooth soup. The food changes shape, and so does the child's feeling:
wary -> curious -> proud.

The world model stays small and concrete:

* typed entities with physical meters and emotional memes
* a forward-chaining causal step where blending + chilling turns vegetables
  into gazpacho and cools the kitchen mood
* a reasonableness gate: only combinations with enough juicy vegetables and a
  proper transforming tool make a believable gazpacho story
* an inline ASP twin for valid-combo and outcome parity

Run it
------
    python storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py
    python storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py --produce tomato_cucumber --tool whisk
    python storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/gazpacho_transformation_heartwarming.py --verify
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
TRANSFORM_MIN = 2


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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    warmth: str
    source: str
    seat: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Produce:
    id: str
    basket: str
    colors: str
    pieces: str
    pour: str
    needs: int
    smoothness: int
    bright_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    transform_power: int
    action: str
    texture: str
    sensible: bool
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Topping:
    id: str
    phrase: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    concern: str
    dislike: str
    opening: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transform(world: World) -> list[str]:
    bowl = world.get("bowl")
    if bowl.meters["mixed"] < THRESHOLD or bowl.meters["cold"] < THRESHOLD:
        return []
    if bowl.meters["smooth"] < TRANSFORM_MIN:
        return []
    sig = ("transform", "bowl")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.meters["gazpacho"] += 1
    bowl.meters["refreshing"] += 1
    for eid in ("child", "helper"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
    if "kitchen" in world.entities:
        world.get("kitchen").memes["calm"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="transform", tag="physical", apply=_r_transform),
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


def can_transform(produce: Produce, tool: Tool) -> bool:
    return tool.sensible and tool.transform_power >= produce.needs


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for produce_id, produce in PRODUCE.items():
            for tool_id, tool in TOOLS.items():
                for topping_id in TOPPINGS:
                    if can_transform(produce, tool):
                        combos.append((setting_id, produce_id, tool_id, topping_id))
    return combos


def explain_rejection(produce: Produce, tool: Tool) -> str:
    if not tool.sensible:
        return (
            f"(No story: {tool.phrase} does not really turn chopped vegetables into smooth gazpacho. "
            f"Pick a transforming tool like a blender or food mill.)"
        )
    return (
        f"(No story: {produce.basket} need more smoothing than {tool.phrase} can give. "
        f"Pick a stronger tool for a believable transformation.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if not can_transform(PRODUCE[params.produce], TOOLS[params.tool]):
        return "unchanged"
    if params.child_mood == "brave":
        return "glad"
    return "proud"


def introduce(world: World, child: Entity, helper: Entity, mood: Mood) -> None:
    world.say(
        f"{child.id} stood with {helper.label_word} in {world.setting.place} on a {world.setting.warmth} afternoon. "
        f"{mood.opening}"
    )


def gather(world: World, child: Entity, produce: Produce) -> None:
    child.memes["interest"] += 1
    bowl = world.get("bowl")
    bowl.meters["pieces"] += 1
    world.say(
        f"On the table waited {produce.basket}: {produce.colors}. "
        f"{child.id} looked at the cut pieces and thought they were {produce.pieces}."
    )


def hesitate(world: World, child: Entity, mood: Mood) -> None:
    child.memes["wary"] += 1
    child.memes["doubt"] += 1
    world.say(
        f'"I like the colors," {child.id} said, "but I am not sure about a bowl of chopped vegetables. '
        f'{mood.concern}"'
    )


def offer_transformation(world: World, helper: Entity, tool: Tool) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled and tapped {tool.phrase}. '
        f'"Then let us transform them together," {helper.pronoun()} said.'
    )


def mix(world: World, child: Entity, helper: Entity, tool: Tool, produce: Produce) -> None:
    bowl = world.get("bowl")
    bowl.meters["mixed"] += 1
    bowl.meters["smooth"] += tool.transform_power
    child.memes["curiosity"] += 1
    world.say(
        f"They added bread, a little olive oil, and a pinch of salt. "
        f"Then {helper.label_word} {tool.action}, and the vegetables changed from neat little pieces into {tool.texture}."
    )
    if bowl.meters["smooth"] >= produce.needs:
        world.say(
            f"The red and green colors swirled together until the bowl looked bright and {produce.bright_word}."
        )


def chill(world: World, child: Entity) -> None:
    bowl = world.get("bowl")
    bowl.meters["cold"] += 1
    child.memes["patience"] += 1
    world.say(
        f"While the bowl rested in the cool box for a little while, {child.id} pressed both hands to the chilly door and waited."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, helper: Entity, topping: Topping) -> None:
    bowl = world.get("bowl")
    if bowl.meters["gazpacho"] < THRESHOLD:
        raise StoryError("(Story logic error: the bowl never became gazpacho.)")
    bowl.attrs["topping"] = topping.id
    world.say(
        f"When {helper.label_word} set the bowl down again, it was no longer a pile of chopped vegetables. "
        f"It was gazpacho, cool and silky, with {topping.phrase} on top like {topping.sparkle}."
    )
    child.memes["surprise"] += 1


def taste(world: World, child: Entity, mood: Mood) -> None:
    bowl = world.get("bowl")
    if bowl.meters["gazpacho"] < THRESHOLD:
        raise StoryError("(No tasting scene: there is no gazpacho to taste.)")
    child.meters["tasted"] += 1
    child.memes["doubt"] = 0.0
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    if mood.id == "brave":
        child.memes["relief"] += 1
    world.say(
        f"{child.id} took one careful sip. The soup tasted garden-fresh and cool instead of rough the way {child.pronoun()} had feared."
    )


def ending(world: World, child: Entity, helper: Entity, outcome: str) -> None:
    chair = world.setting.seat
    if outcome == "glad":
        line = (
            f'{child.id} laughed softly and asked for another little cup. '
            f'Soon {child.pronoun()} was sitting with {helper.label_word} on {chair}, sharing the gazpacho as the whole room felt cooler.'
        )
    else:
        line = (
            f'{child.id} grinned and said, "We made that." '
            f'Soon {child.pronoun()} was carrying a small bowl to {chair}, proud that something doubtful had turned into something lovely.'
        )
    world.say(line)


def tell(
    setting: Setting,
    produce: Produce,
    tool: Tool,
    topping: Topping,
    mood: Mood,
    child_name: str = "Lina",
    child_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    kitchen = world.add(Entity(id="kitchen", type="room", label="kitchen"))
    bowl = world.add(Entity(id="bowl", type="bowl", label="mixing bowl", phrase="the bowl of vegetables"))

    world.facts["child_name"] = child_name
    world.facts["helper_name"] = helper.label_word
    world.facts["starting_mood"] = mood.id

    introduce(world, child, helper, mood)
    gather(world, child, produce)

    world.para()
    hesitate(world, child, mood)
    offer_transformation(world, helper, tool)
    mix(world, child, helper, tool, produce)
    chill(world, child)

    world.para()
    reveal(world, child, helper, topping)
    taste(world, child, mood)
    end = outcome_of(
        StoryParams(
            setting=setting.id,
            produce=produce.id,
            tool=tool.id,
            topping=topping.id,
            child_name=child_name,
            child_gender=child_type,
            helper=helper_type,
            child_mood=mood.id,
            seed=None,
        )
    )
    ending(world, child, helper, end)

    world.facts.update(
        setting=setting,
        produce=produce,
        tool=tool,
        topping=topping,
        mood=mood,
        child=child,
        helper=helper,
        bowl=bowl,
        transformed=bowl.meters["gazpacho"] >= THRESHOLD,
        outcome=end,
    )
    return world


KNOWLEDGE = {
    "gazpacho": [
        (
            "What is gazpacho?",
            "Gazpacho is a cold soup made mostly from vegetables like tomatoes and cucumbers. It is served cool, so it feels fresh on a warm day.",
        )
    ],
    "tomato": [
        (
            "Why are tomatoes good for gazpacho?",
            "Tomatoes are juicy and soft, so they blend into a smooth soup very well. They also give gazpacho its bright red color.",
        )
    ],
    "cucumber": [
        (
            "Why does cucumber taste cool?",
            "Cucumber has a lot of water in it, so it feels crisp and refreshing when you eat it. That is why it fits nicely in a cold soup.",
        )
    ],
    "pepper": [
        (
            "What does sweet pepper add to soup?",
            "A sweet pepper adds fresh flavor and a gentle crunch before blending. When it is blended well, it helps make the soup taste bright.",
        )
    ],
    "blender": [
        (
            "What does a blender do?",
            "A blender spins food very fast and breaks it into tiny pieces. That helps turn chopped vegetables into a smooth soup.",
        )
    ],
    "food_mill": [
        (
            "What is a food mill?",
            "A food mill presses soft food through little holes. It can help make vegetables smoother for soup or sauce.",
        )
    ],
    "olive_oil": [
        (
            "Why do people add olive oil to soup?",
            "A little olive oil can make soup feel smoother and richer. It helps the flavors come together gently.",
        )
    ],
    "chill": [
        (
            "Why do some soups need to be chilled?",
            "Chilling makes a cold soup taste fresh and refreshing. It also changes how the soup feels in your mouth.",
        )
    ],
    "basil": [
        (
            "What does basil smell like?",
            "Basil smells sweet and green, a little like sunshine on leaves. A few basil leaves can make food smell extra fresh.",
        )
    ],
    "croutons": [
        (
            "What are croutons?",
            "Croutons are little toasted bread cubes. They can make a soup crunchy on top.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "gazpacho",
    "tomato",
    "cucumber",
    "pepper",
    "blender",
    "food_mill",
    "olive_oil",
    "chill",
    "basil",
    "croutons",
]


SETTINGS = {
    "sunny_kitchen": Setting(
        id="sunny_kitchen",
        place="a sunny kitchen with the window open",
        warmth="golden",
        source="garden",
        seat="the window bench",
        tags={"home"},
    ),
    "courtyard_table": Setting(
        id="courtyard_table",
        place="a shady courtyard kitchen",
        warmth="soft",
        source="courtyard pots",
        seat="the cool stone step",
        tags={"home"},
    ),
    "porch_kitchen": Setting(
        id="porch_kitchen",
        place="a small porch kitchen where the curtains breathed in the breeze",
        warmth="warm",
        source="porch planters",
        seat="the painted porch swing",
        tags={"home"},
    ),
}

PRODUCE = {
    "tomato_cucumber": Produce(
        id="tomato_cucumber",
        basket="a bowl of ripe tomatoes and cucumbers",
        colors="red tomatoes, pale green cucumbers, and a clove of garlic",
        pieces="too chunky to be soup",
        pour="a smooth pink-red ribbon",
        needs=2,
        smoothness=2,
        bright_word="shiny",
        tags={"gazpacho", "tomato", "cucumber"},
    ),
    "tomato_pepper": Produce(
        id="tomato_pepper",
        basket="a bowl of tomatoes and sweet peppers",
        colors="red tomatoes, glossy peppers, and a little onion",
        pieces="too crunchy for one spoon",
        pour="a bright scarlet pour",
        needs=2,
        smoothness=2,
        bright_word="silky",
        tags={"gazpacho", "tomato", "pepper"},
    ),
    "garden_mix": Produce(
        id="garden_mix",
        basket="a bowl of tomatoes, cucumbers, and sweet peppers",
        colors="red tomatoes, cool cucumbers, sweet peppers, and torn basil leaves",
        pieces="busy and uneven",
        pour="a velvet-red stream",
        needs=3,
        smoothness=3,
        bright_word="velvety",
        tags={"gazpacho", "tomato", "cucumber", "pepper", "basil"},
    ),
}

TOOLS = {
    "blender": Tool(
        id="blender",
        label="blender",
        phrase="the humming blender",
        transform_power=3,
        action="poured everything into the blender and let it whirl",
        texture="a smooth, rosy soup",
        sensible=True,
        qa_text="used the blender to turn the vegetables into smooth soup",
        tags={"blender", "olive_oil"},
    ),
    "food_mill": Tool(
        id="food_mill",
        label="food mill",
        phrase="the old food mill",
        transform_power=2,
        action="pressed the vegetables through the food mill with steady hands",
        texture="a softer, gentler soup",
        sensible=True,
        qa_text="pressed the vegetables through the food mill until they were smooth",
        tags={"food_mill", "olive_oil"},
    ),
    "whisk": Tool(
        id="whisk",
        label="whisk",
        phrase="a little whisk",
        transform_power=1,
        action="stirred the bowl quickly with the whisk",
        texture="a puddle with many floating pieces",
        sensible=False,
        qa_text="stirred the bowl with a whisk",
        tags=set(),
    ),
}

TOPPINGS = {
    "basil": Topping(
        id="basil",
        phrase="tiny basil ribbons",
        sparkle="green confetti",
        tags={"basil"},
    ),
    "croutons": Topping(
        id="croutons",
        phrase="golden croutons",
        sparkle="little toasted boats",
        tags={"croutons"},
    ),
    "cucumber_stars": Topping(
        id="cucumber_stars",
        phrase="small cucumber stars",
        sparkle="cool green stars",
        tags={"cucumber"},
    ),
}

MOODS = {
    "hesitant": Mood(
        id="hesitant",
        concern="What if it still feels lumpy?",
        dislike="lumps",
        opening="The day was hot enough to make even the fruit bowl look sleepy.",
        tags={"change"},
    ),
    "shy": Mood(
        id="shy",
        concern="What if I do not like it after all?",
        dislike="new foods",
        opening="The air smelled of cut herbs and warm boards from the floor.",
        tags={"change"},
    ),
    "brave": Mood(
        id="brave",
        concern="I want to try, but I need it to feel gentle.",
        dislike="sharp bits",
        opening="The whole kitchen seemed to be waiting for one small brave choice.",
        tags={"change"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Eva", "Nora", "Lola", "Sara", "June", "Ayla"]
BOY_NAMES = ["Tomas", "Leo", "Milo", "Evan", "Nico", "Owen", "Rafi", "Ben"]
HELPERS = ["grandmother", "grandfather", "mother", "father"]


@dataclass
class StoryParams:
    setting: str
    produce: str
    tool: str
    topping: str
    child_name: str
    child_gender: str
    helper: str
    child_mood: str
    seed: Optional[int] = None


def pair_phrase(world: World) -> str:
    child_name = world.facts["child_name"]
    helper_name = world.facts["helper_name"]
    return f"{child_name} and {helper_name}"


def generation_prompts(world: World) -> list[str]:
    child_name = world.facts["child_name"]
    produce = world.facts["produce"]
    mood = world.facts["mood"]
    helper = world.facts["helper"]
    return [
        f'Write a heartwarming transformation story for a 3-to-5-year-old that includes the word "gazpacho".',
        f"Tell a gentle story where {child_name} is unsure about chopped vegetables, but {helper.label_word} helps turn them into gazpacho.",
        f'Write a warm kitchen story about how something {mood.dislike} can be transformed into something cool, smooth, and loved.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    produce = world.facts["produce"]
    tool = world.facts["tool"]
    topping = world.facts["topping"]
    setting = world.facts["setting"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {world.facts['child_name']} and {helper.label_word}. They spend a warm afternoon making something together.",
        ),
        (
            "Why was the child unsure at first?",
            f"{world.facts['child_name']} saw a bowl of chopped vegetables and worried it would feel {world.facts['mood'].dislike}. The problem was not the colors but the texture {child.pronoun()} imagined.",
        ),
        (
            "How did the vegetables change?",
            f"They were mixed, smoothed, and chilled until they became gazpacho. The change happened because {helper.label_word} and the child used {tool.label} and then let the bowl get cold.",
        ),
        (
            "What was on top of the gazpacho?",
            f"The gazpacho was finished with {topping.phrase}. That topping made the bowl look welcoming before the first sip.",
        ),
    ]
    if outcome == "glad":
        qa.append(
            (
                "How did the child feel at the end?",
                f"{world.facts['child_name']} felt glad and relieved after tasting the gazpacho. The soup was gentler than {child.pronoun()} feared, so trying it felt safe and happy.",
            )
        )
    else:
        qa.append(
            (
                "How did the child change by the end?",
                f"{world.facts['child_name']} changed from doubtful to proud. Helping make the gazpacho showed {child.pronoun('object')} that the same vegetables could become something lovely.",
            )
        )
    qa.append(
        (
            "Where did the story end?",
            f"It ended in {setting.place}, where they sat together and shared the cool soup. The ending image shows that the kitchen feels calmer and the child feels closer to {helper.label_word}.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["produce"].tags) | set(world.facts["tool"].tags) | set(world.facts["topping"].tags) | {"chill"}
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="sunny_kitchen",
        produce="tomato_cucumber",
        tool="blender",
        topping="basil",
        child_name="Lina",
        child_gender="girl",
        helper="grandmother",
        child_mood="hesitant",
        seed=None,
    ),
    StoryParams(
        setting="courtyard_table",
        produce="tomato_pepper",
        tool="food_mill",
        topping="croutons",
        child_name="Leo",
        child_gender="boy",
        helper="grandfather",
        child_mood="shy",
        seed=None,
    ),
    StoryParams(
        setting="porch_kitchen",
        produce="garden_mix",
        tool="blender",
        topping="cucumber_stars",
        child_name="Mia",
        child_gender="girl",
        helper="mother",
        child_mood="brave",
        seed=None,
    ),
]


ASP_RULES = r"""
can_transform(P, T) :- produce(P), tool(T), sensible(T), need(P, N), power(T, M), M >= N.
valid(S, P, T, Top) :- setting(S), produce(P), tool(T), topping(Top), can_transform(P, T).

outcome(glad)  :- chosen_mood(brave), can_transform(chosen_produce, chosen_tool).
outcome(proud) :- chosen_mood(M), mood(M), M != brave, can_transform(chosen_produce, chosen_tool).
outcome(unchanged) :- not can_transform(chosen_produce, chosen_tool).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, produce in PRODUCE.items():
        lines.append(asp.fact("produce", pid))
        lines.append(asp.fact("need", pid, produce.needs))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, tool.transform_power))
        if tool.sensible:
            lines.append(asp.fact("sensible", tid))
    for top in TOPPINGS:
        lines.append(asp.fact("topping", top))
    for mood in MOODS:
        lines.append(asp.fact("mood", mood))
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
            asp.fact("chosen_produce", params.produce),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_mood", params.child_mood),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "gazpacho" not in smoke.story.lower():
            raise StoryError("(Smoke test failed: story missing gazpacho.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a doubtful bowl of vegetables transforms into gazpacho, and a child's feeling transforms too."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--produce", choices=PRODUCE)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--topping", choices=TOPPINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-mood", choices=MOODS, dest="child_mood")
    ap.add_argument("--child-gender", choices=["girl", "boy"], dest="child_gender")
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.produce and args.tool:
        produce = PRODUCE[args.produce]
        tool = TOOLS[args.tool]
        if not can_transform(produce, tool):
            raise StoryError(explain_rejection(produce, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.produce is None or combo[1] == args.produce)
        and (args.tool is None or combo[2] == args.tool)
        and (args.topping is None or combo[3] == args.topping)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, produce_id, tool_id, topping_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    child_mood = args.child_mood or rng.choice(sorted(MOODS))
    return StoryParams(
        setting=setting_id,
        produce=produce_id,
        tool=tool_id,
        topping=topping_id,
        child_name=child_name,
        child_gender=child_gender,
        helper=helper,
        child_mood=child_mood,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.produce not in PRODUCE:
        raise StoryError(f"(Unknown produce: {params.produce})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(Unknown topping: {params.topping})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.child_mood not in MOODS:
        raise StoryError(f"(Unknown child mood: {params.child_mood})")

    produce = PRODUCE[params.produce]
    tool = TOOLS[params.tool]
    if not can_transform(produce, tool):
        raise StoryError(explain_rejection(produce, tool))

    world = tell(
        setting=SETTINGS[params.setting],
        produce=produce,
        tool=tool,
        topping=TOPPINGS[params.topping],
        mood=MOODS[params.child_mood],
        child_name=params.child_name,
        child_type=params.child_gender,
        helper_type=params.helper,
    )
    story_text = world.render().replace("child", params.child_name)
    helper_ent = world.get("helper")
    child_ent = world.get("child")
    story_text = story_text.replace("helper", helper_ent.label_word).replace("child", child_ent.label)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, produce, tool, topping) combos:\n")
        for setting_id, produce_id, tool_id, topping_id in combos:
            print(f"  {setting_id:14} {produce_id:16} {tool_id:10} {topping_id}")
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
            header = f"### {p.child_name}: {p.produce} -> gazpacho with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
