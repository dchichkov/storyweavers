#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py
=============================================================

A small storyworld about a child called Twist who turns pizza night into a
superhero mission. The family cannot find the pepperoni. A suspicious clue makes
the hiding place feel like a villain's lair, but the child uses the *right safe
tool* to investigate. The twist is that the scary "villain" is only an ordinary
household thing, and the real superpower is calm, sensible problem-solving.

Run it
------
    python storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py
    python storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py --place pantry_shelf --tool step_stool
    python storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py --place cooler --tool flashlight
    python storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/pepperoni_twist_superhero_story.py --qa --json
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
class Place:
    id: str
    label: str
    phrase: str
    need: str
    clue: str
    danger: str
    reveal: str
    find_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    action: str = ""
    finish: str = ""
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


def _r_mystery(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    if place.meters["suspicious"] < THRESHOLD:
        return []
    sig = ("mystery", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    return ["__mystery__"]


def _r_found_relief(world: World) -> list[str]:
    hero = world.get("hero")
    pepperoni = world.get("pepperoni")
    if pepperoni.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="mystery", tag="emotion", apply=_r_mystery),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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


PLACES = {
    "pantry_shelf": Place(
        id="pantry_shelf",
        label="pantry shelf",
        phrase="the highest pantry shelf",
        need="high",
        clue="something on the highest shelf gave a quick papery flutter",
        danger="climbing on a wobbly chair to reach up high",
        reveal="a loose grocery list was flapping against a cereal box",
        find_text="the pepperoni packet had slipped behind a tower of soup cans",
        tags={"pantry", "high", "paper"},
    ),
    "under_couch": Place(
        id="under_couch",
        label="under the couch",
        phrase="the dark space under the couch",
        need="dark",
        clue="two tiny red glints blinked from the shadows",
        danger="sticking a hand into a dark place without looking",
        reveal="the red glints were only shiny toy car reflectors",
        find_text="the pepperoni packet was tucked beside a crayon and a puzzle piece",
        tags={"dark", "living_room", "reflector"},
    ),
    "cooler": Place(
        id="cooler",
        label="cooler",
        phrase="the big picnic cooler by the back door",
        need="heavy",
        clue="a low thump came from inside, then the lid gave a little wobble",
        danger="trying to yank open a heavy lid alone",
        reveal="a rolling ice pack had bumped the cooler wall",
        find_text="the pepperoni packet was resting on top of the juice boxes",
        tags={"cooler", "heavy", "ice"},
    ),
}

TOOLS = {
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a sturdy step stool",
        covers={"high"},
        action="set the step stool firmly on the floor and climbed up one careful step at a time",
        finish="From there, Twist could see safely over the shelf.",
        tags={"stool", "safe_tool"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        covers={"dark"},
        action="clicked on the flashlight and aimed its round beam into the shadows before reaching",
        finish="The light turned the scary dark into an ordinary hiding place.",
        tags={"flashlight", "safe_tool"},
    ),
    "grownup_help": Tool(
        id="grownup_help",
        label="grown-up help",
        phrase="both hands and a grown-up helper",
        covers={"heavy"},
        action="waited for the grown-up to hold the cooler steady while Twist lifted with both hands",
        finish="Doing it together made the heavy lid feel manageable instead of scary.",
        tags={"grownup_help", "safe_tool"},
    ),
}

GIRL_NAMES = ["Twist", "Mia", "Luna", "Zoe", "Ava", "Nora", "Piper", "Ruby"]
BOY_NAMES = ["Twist", "Max", "Leo", "Finn", "Eli", "Noah", "Sam", "Theo"]
TRAITS = ["quick", "brave", "curious", "kind", "lively", "careful"]


def tool_fits(place: Place, tool: Tool) -> bool:
    return place.need in tool.covers


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for tool_id, tool in TOOLS.items():
            if tool_fits(place, tool):
                out.append((place_id, tool_id))
    return sorted(out)


@dataclass
class StoryParams:
    place: str
    tool: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On pizza night, {hero.id} tied a dish towel around {hero.pronoun('possessive')} shoulders "
        f"and called {hero.pronoun('self') if False else ''}"
    )


def scene_setup(world: World, hero: Entity, parent: Entity) -> None:
    trait = hero.attrs.get("trait", "brave")
    world.say(
        f"On pizza night, {hero.id} tied a dish towel around {hero.pronoun('possessive')} shoulders "
        f"like a cape. In {hero.pronoun('possessive')} mind, {hero.id} was Super Twist, the {trait} hero "
        f"of the kitchen."
    )
    world.say(
        f"{parent.label_word.capitalize()} rolled the dough, set out the cheese, and reached for the pepperoni."
    )
    world.say(
        f"Then {parent.pronoun()} blinked. 'Oh no,' {parent.pronoun()} said. 'The pepperoni is missing.'"
    )
    world.get("pepperoni").meters["lost"] += 1


def alarm(world: World, hero: Entity, parent: Entity, place_cfg: Place) -> None:
    place = world.get("place")
    place.meters["suspicious"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That was all {hero.id} needed to hear. '{hero.id} to the rescue!' {hero.pronoun().capitalize()} cried."
    )
    world.say(
        f"But when they listened carefully, {place_cfg.clue}. Suddenly {place_cfg.phrase} felt less like a corner "
        f"of the house and more like a villain's lair."
    )


def unsafe_idea(world: World, hero: Entity, place_cfg: Place) -> None:
    hero.memes["impulse"] += 1
    world.say(
        f"{hero.id} started to hurry forward, already thinking about {place_cfg.danger}."
    )


def safe_coaching(world: World, hero: Entity, parent: Entity, place_cfg: Place, tool_cfg: Tool) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"'{hero.id}, real heroes do not rush into trouble,' said {parent.label_word}. "
        f"'We use the right safe tool first.'"
    )
    if tool_cfg.id == "grownup_help":
        world.say(
            f"{parent.label_word.capitalize()} knelt beside {hero.pronoun('object')} so they could work as a team."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} handed {hero.pronoun('object')} {tool_cfg.phrase}."
        )


def investigate(world: World, hero: Entity, place_cfg: Place, tool_cfg: Tool) -> None:
    world.say(
        f"Super Twist took a breath, then {tool_cfg.action}."
    )
    world.say(tool_cfg.finish)
    world.get("place").meters["checked"] += 1
    world.facts["method"] = tool_cfg.label


def reveal(world: World, hero: Entity, place_cfg: Place) -> None:
    world.say(
        f"And then came the twist: the terrible kitchen villain was not terrible at all. "
        f"It was only {place_cfg.reveal}."
    )
    world.get("place").meters["revealed"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] += 1


def recover(world: World, hero: Entity, parent: Entity, place_cfg: Place) -> None:
    pepperoni = world.get("pepperoni")
    pepperoni.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Right beside it, {place_cfg.find_text}."
    )
    world.say(
        f"{hero.id} lifted the packet high above {hero.pronoun('possessive')} cape and grinned. "
        f"'Pepperoni saved!'"
    )
    world.say(
        f"{parent.label_word.capitalize()} laughed and called {hero.pronoun('object')} the hero of supper."
    )


def ending(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"Soon little red circles of pepperoni were tucked all over the pizza like bright superhero badges."
    )
    world.say(
        f"When the pie came out hot and bubbling, {hero.id} took the first proud sniff. "
        f"{hero.pronoun().capitalize()} had expected a battle, but the real victory had been slowing down, "
        f"looking carefully, and asking for the right help."
    )
    world.say(
        f"That night Super Twist ate a warm slice at the table and knew the best heroes make kitchens feel safe."
    )


def tell(
    place_cfg: Place,
    tool_cfg: Tool,
    hero_name: str = "Twist",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "brave",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        attrs={"name": hero_name, "trait": trait},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    pepperoni = world.add(Entity(
        id="pepperoni",
        type="food",
        label="pepperoni",
        phrase="the pepperoni packet",
        tags={"pepperoni", "pizza"},
    ))
    place = world.add(Entity(
        id="place",
        type="place",
        label=place_cfg.label,
        phrase=place_cfg.phrase,
        attrs={"need": place_cfg.need},
        tags=set(place_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        tags=set(tool_cfg.tags),
    ))

    scene_setup(world, hero, parent)
    world.para()
    alarm(world, hero, parent, place_cfg)
    unsafe_idea(world, hero, place_cfg)
    safe_coaching(world, hero, parent, place_cfg, tool_cfg)
    world.para()
    investigate(world, hero, place_cfg, tool_cfg)
    reveal(world, hero, place_cfg)
    recover(world, hero, parent, place_cfg)
    world.para()
    ending(world, hero, parent)

    world.facts.update(
        hero=hero,
        parent=parent,
        pepperoni=pepperoni,
        place_cfg=place_cfg,
        tool_cfg=tool_cfg,
        place=place,
        tool=tool,
        recovered=pepperoni.meters["found"] >= THRESHOLD,
        safe=tool_fits(place_cfg, tool_cfg),
        twist_reveal=place_cfg.reveal,
    )
    return world


KNOWLEDGE = {
    "pepperoni": [
        (
            "What is pepperoni?",
            "Pepperoni is a spicy kind of sausage that people often slice into little circles for pizza."
        )
    ],
    "pizza": [
        (
            "What goes on a pizza?",
            "A pizza often has dough, sauce, cheese, and toppings. Different families choose different toppings they like."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight helpful in a dark place?",
            "A flashlight helps you see before you reach into the dark. It turns a hidden place into a place you can check safely."
        )
    ],
    "stool": [
        (
            "Why should you use a step stool instead of climbing on a wobbly chair?",
            "A step stool is made to help you reach safely. A wobbly chair can tip or slide."
        )
    ],
    "grownup_help": [
        (
            "Why is it smart to ask a grown-up for help with something heavy?",
            "A grown-up can help steady, lift, and watch for danger. Working together is safer than tugging alone."
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise that changes what you thought was happening. It can make a scary moment turn out to be ordinary after all."
        )
    ],
}
KNOWLEDGE_ORDER = ["pepperoni", "pizza", "flashlight", "stool", "grownup_help", "twist"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place_cfg = world.facts["place_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    hero_name = hero.attrs.get("name", "Twist")
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "pepperoni" and ends with a gentle twist.',
        f"Tell a child-friendly story about a young hero named {hero_name} who thinks {place_cfg.phrase} hides a villain, but uses {tool_cfg.label} and discovers a harmless surprise.",
        "Write a simple kitchen adventure where the missing pizza topping causes a superhero mission, and the ending shows that being careful is a real superpower.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    place_cfg = world.facts["place_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    hero_name = hero.attrs.get("name", "Twist")
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, who pretended to be Super Twist, and {hero.pronoun('possessive')} {pw} during pizza night."
        ),
        (
            "What problem started the superhero mission?",
            "The family could not find the pepperoni for the pizza. That missing topping turned an ordinary kitchen moment into a rescue mission."
        ),
        (
            f"Why did {place_cfg.phrase} seem scary at first?",
            f"It seemed scary because {place_cfg.clue}. That clue made the place feel like a villain's lair in Twist's imagination."
        ),
        (
            f"How did {hero_name} investigate safely?",
            f"{hero_name} used {tool_cfg.label} instead of rushing in unsafely. That helped {hero.pronoun('object')} check {place_cfg.label} carefully before grabbing anything."
        ),
        (
            "What was the twist?",
            f"The scary villain was not real at all. It was only {place_cfg.reveal}, so the mystery turned out to be an ordinary household thing."
        ),
        (
            "How did the story end?",
            "Twist found the pepperoni, the pizza was finished, and supper felt cheerful again. The ending shows that careful thinking helped more than pretending to be fearless."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tool_cfg = world.facts["tool_cfg"]
    tags = {"pepperoni", "pizza", "twist"}
    if tool_cfg.id == "flashlight":
        tags.add("flashlight")
    if tool_cfg.id == "step_stool":
        tags.add("stool")
    if tool_cfg.id == "grownup_help":
        tags.add("grownup_help")
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pantry_shelf",
        tool="step_stool",
        hero_name="Twist",
        hero_gender="girl",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        place="under_couch",
        tool="flashlight",
        hero_name="Max",
        hero_gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        place="cooler",
        tool="grownup_help",
        hero_name="Luna",
        hero_gender="girl",
        parent="mother",
        trait="kind",
    ),
]


def explain_rejection(place_cfg: Place, tool_cfg: Tool) -> str:
    return (
        f"(No story: {tool_cfg.label} does not solve the problem at {place_cfg.label}. "
        f"That place needs help with '{place_cfg.need}', so choose a tool that really fits.)"
    )


ASP_RULES = r"""
needs_tool(P, T) :- place(P), tool(T), need(P, N), covers(T, N).
valid(P, T) :- needs_tool(P, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("need", place_id, place.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for need in sorted(tool.covers):
            lines.append(asp.fact("covers", tool_id, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "pepperoni" not in sample.story.lower():
            raise StoryError("smoke test story did not render the expected pepperoni story")
        print("OK: smoke test story generation passed.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story:
            raise StoryError("random sample rendered empty story")
        print("OK: random generation passed.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM GENERATION FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Super Twist rescues the missing pepperoni with the right safe tool."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, tool) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.tool:
        place_cfg = PLACES[args.place]
        tool_cfg = TOOLS[args.tool]
        if not tool_fits(place_cfg, tool_cfg):
            raise StoryError(explain_rejection(place_cfg, tool_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, tool_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    place_cfg = PLACES[params.place]
    tool_cfg = TOOLS[params.tool]
    if not tool_fits(place_cfg, tool_cfg):
        raise StoryError(explain_rejection(place_cfg, tool_cfg))

    world = tell(
        place_cfg=place_cfg,
        tool_cfg=tool_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    hero = world.facts["hero"]
    world_story = world.render().replace("hero", hero.attrs.get("name", "Twist"))
    world_story = world_story.replace("parent", world.facts["parent"].label_word)
    world_story = world_story.replace("Twist to the rescue", f"{hero.attrs.get('name', 'Twist')} to the rescue")

    story = world_story.replace("hero", hero.attrs.get("name", "Twist"))
    story = story.replace("Twist", hero.attrs.get("name", "Twist")) if hero.attrs.get("name", "Twist") != "Twist" else world.render()

    if hero.attrs.get("name", "Twist") != "Twist":
        story = world.render().replace("Twist", hero.attrs.get("name", "Twist"))
    else:
        story = world.render()

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, tool) pairs:\n")
        for place_id, tool_id in combos:
            print(f"  {place_id:13} {tool_id}")
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
            header = f"### {p.hero_name}: {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
