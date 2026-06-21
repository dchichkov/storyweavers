#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py
==============================================================

A standalone story world for a small animal tale built from the seed words
"swear" and "Sound Effects".

Premise
-------
A little animal wants to carry a treat across a tricky forest path to share at a
snack spot. The hero proudly insists, "I swear I can do it myself," but the
route jolts, splashes, or blows at the treat. A helper then offers the right
carrier, and together they finish the job the safe way.

This world prefers a narrow band of plausible stories:
- the route must truly threaten the chosen treat;
- the rescue carrier must actually protect that treat from that route;
- the story always includes concrete sound effects from the world state.

Run it
------
    python storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py
    python storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py --cargo honey --route stones
    python storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py --cargo honey --tool basket
    python storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4/swear_sound_effects_animal_story.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


def sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class HeroSpec:
    id: str
    animal: str
    opening: str
    feet: str
    tail_line: str
    cheer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperSpec:
    id: str
    animal: str
    move: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    plural: bool
    risks: set[str]
    loss_text: str
    rescue_text: str
    shared_text: str
    sound: str
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    hazard: str
    sound: str
    mishap_text: str
    safe_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fits: set[str]
    guards: set[str]
    carry_verb: str
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


def route_threatens(route: Route, cargo: Cargo) -> bool:
    return route.hazard in cargo.risks


def tool_fits(tool: Tool, cargo: Cargo) -> bool:
    return cargo.id in tool.fits


def tool_solves(tool: Tool, route: Route, cargo: Cargo) -> bool:
    return tool_fits(tool, cargo) and route.hazard in tool.guards


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hero_id in HEROES:
        for cargo_id, cargo in CARGO.items():
            for route_id, route in ROUTES.items():
                if not route_threatens(route, cargo):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_solves(tool, route, cargo):
                        combos.append((hero_id, cargo_id, route_id, tool_id))
    return combos


def _r_spill_sadness(world: World) -> list[str]:
    cargo = world.get("cargo")
    hero = world.get("hero")
    helper = world.get("helper")
    if cargo.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill_sadness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["sad"] += 1
    hero.memes["worry"] += 1
    helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule("spill_sadness", "emotion", _r_spill_sadness),
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
        for s in produced:
            world.say(s)
    return produced


def predict_mishap(route: Route, cargo: Cargo) -> dict:
    return {
        "threatened": route_threatens(route, cargo),
        "hazard": route.hazard,
    }


def introduce(world: World, hero: Entity, hero_spec: HeroSpec, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In the green woods, {hero.id} the {hero_spec.animal} {hero_spec.opening}. "
        f"That morning, {hero.pronoun('subject')} had found {cargo.phrase} to share at the mossy snack stone."
    )
    world.say(hero_spec.tail_line)


def goal(world: World, hero: Entity, cargo: Cargo, route: Route) -> None:
    world.say(
        f"The only way there was {route.phrase}. On the other side, the other small animals were waiting for a treat."
    )
    world.say(
        f'{hero.id} hugged {cargo.it()} close and said, "I can bring {cargo.it()} across all by myself. '
        f'I swear I can do it without dropping a single bit."'
    )


def warning(world: World, helper: Entity, helper_spec: HelperSpec, route: Route, cargo: Cargo) -> None:
    pred = predict_mishap(route, cargo)
    helper.memes["care"] += 1
    world.facts["predicted_hazard"] = pred["hazard"]
    world.say(
        f"{helper.id} the {helper_spec.animal} {helper_spec.move} and looked from {route.label} to {cargo.it()}. "
        f'"Careful," {helper.pronoun("subject")} said. "{route.label.capitalize()} goes {route.sound}, and {cargo.label} do not like that."'
    )


def attempt(world: World, hero: Entity, route: Route, cargo: Entity, cargo_cfg: Cargo) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"But {hero.id} took a brave little breath and stepped forward. {route.label.capitalize()} went {route.sound}."
    )
    cargo.meters["spilled"] += 1
    cargo.meters["lost"] += 1
    hero.meters["stumble"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{sentence_case(cargo_cfg.sound)}! {route.mishap_text} {cargo_cfg.loss_text}'
    )


def comfort(world: World, helper: Entity, helper_spec: HelperSpec, hero: Entity) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"{hero.id}'s ears drooped. But {helper.id} {helper_spec.comfort}. "
        f'"It is all right," {helper.pronoun("subject")} said. "A hard path needs a smart plan."'
    )


def rescue_plan(world: World, helper: Entity, tool: Tool, cargo: Cargo, route: Route) -> None:
    world.say(
        f"From under a fern, {helper.id} pulled out {tool.phrase}. "
        f'"This will help," {helper.pronoun("subject")} said. "It can keep {cargo.it()} safe when {route.label} goes {route.sound}."'
    )
    world.get("cargo").attrs["tool"] = tool.id
    world.get("cargo").meters["protected"] += 1
    world.get("hero").memes["trust"] += 1


def retry(world: World, hero: Entity, helper: Entity, tool: Tool, cargo: Cargo, route: Route) -> None:
    hero.memes["care"] += 1
    hero.memes["gratitude"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'This time, {hero.id} let {helper.id} help {tool.carry_verb}. Together they started again.'
    )
    world.say(
        f"{route.safe_text} and went {route.sound}, but the {tool.label} held steady. {cargo.rescue_text}"
    )
    cargo_ent = world.get("cargo")
    cargo_ent.meters["delivered"] += 1
    cargo_ent.meters["shared"] += 1
    cargo_ent.meters["spilled"] = 0.0
    world.get("hero").meters["stumble"] = 0.0


def ending(world: World, hero: Entity, hero_spec: HeroSpec, helper: Entity, cargo: Cargo, tool: Tool) -> None:
    world.say(
        f"At the snack stone, everyone shared the treat. {cargo.shared_text}"
    )
    world.say(
        f'{hero.id} smiled at {helper.id} and said, "Next time I will still be brave, but I will listen first. I swear that too."'
    )
    world.say(
        f"{hero_spec.cheer} {sentence_case(tool.ending_image)}"
    )


def tell(hero_spec: HeroSpec, helper_spec: HelperSpec, cargo: Cargo, route: Route, tool: Tool,
         hero_name: str, helper_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_spec.animal, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_spec.animal, role="helper"))
    cargo_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label))
    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name

    introduce(world, hero, hero_spec, cargo)
    goal(world, hero, cargo, route)

    world.para()
    warning(world, helper, helper_spec, route, cargo)
    attempt(world, hero, route, cargo_ent, cargo)

    world.para()
    comfort(world, helper, helper_spec, hero)
    rescue_plan(world, helper, tool, cargo, route)
    retry(world, hero, helper, tool, cargo, route)

    world.para()
    ending(world, hero, hero_spec, helper, cargo, tool)

    world.facts.update(
        hero=hero,
        helper=helper,
        hero_spec=hero_spec,
        helper_spec=helper_spec,
        cargo_cfg=cargo,
        route=route,
        tool=tool,
        spilled_before_help=True,
        delivered=cargo_ent.meters["delivered"] >= THRESHOLD,
        shared=cargo_ent.meters["shared"] >= THRESHOLD,
    )
    return world


HEROES = {
    "squirrel": HeroSpec(
        "squirrel", "squirrel",
        "liked to hurry before thinking",
        "paws",
        "Its striped tail flicked swish-swish above the clover.",
        "Soon the clearing rang with tiny happy chitters.",
        tags={"squirrel"},
    ),
    "rabbit": HeroSpec(
        "rabbit", "rabbit",
        "loved any errand that felt like a race",
        "paws",
        "Long ears tipped forward, listening to every rustle in the grass.",
        "Soon the clearing rang with tiny happy munch-munch sounds.",
        tags={"rabbit"},
    ),
    "otter": HeroSpec(
        "otter", "otter",
        "thought every path looked like a fun game",
        "paws",
        "Its whiskers twitched twitch-twitch in the cool air.",
        "Soon the clearing rang with tiny happy slurps and giggles.",
        tags={"otter"},
    ),
}

HELPERS = {
    "hedgehog": HelperSpec(
        "hedgehog", "hedgehog",
        "came pattering over",
        "gave a soft, kind nod",
        tags={"hedgehog"},
    ),
    "turtle": HelperSpec(
        "turtle", "turtle",
        "came plodding over",
        "rested a gentle shell-side shoulder nearby",
        tags={"turtle"},
    ),
    "robin": HelperSpec(
        "robin", "robin",
        "fluttered down beside the path",
        "tilted a bright head and chirped softly",
        tags={"robin"},
    ),
}

CARGO = {
    "berries": Cargo(
        "berries", "berries", "a heap of plump blue berries on a leaf plate", True,
        {"jolt", "gust"},
        "Little blue berries bounced away into the grass.",
        "Not one berry rolled free now.",
        "Blue juice shone like tiny stars on happy mouths.",
        "plip-plip-plip",
        tags={"berries", "sharing"},
    ),
    "honey": Cargo(
        "honey", "a honey pot", "a small honey pot with a shiny yellow drip at the rim", False,
        {"tilt"},
        "A sticky golden ribbon dribbled down the side.",
        "The honey stayed tucked safely inside.",
        "The sweet smell of honey floated warm and sunny in the air.",
        "glup-glup",
        tags={"honey", "sharing"},
    ),
    "seedcakes": Cargo(
        "seedcakes", "seed cakes", "two round seed cakes stacked on a birch-bark square", True,
        {"jolt", "gust"},
        "Crumbs skipped off like tiny pebbles.",
        "The seed cakes stayed neat and round.",
        "Crumbs dusted a flat stone where everyone nibbled together.",
        "crick-crack",
        tags={"seedcake", "sharing"},
    ),
}

ROUTES = {
    "log": Route(
        "log", "the log bridge", "a wobbly log bridge over a silver stream",
        "jolt",
        "tok-tok wobble-wobble",
        "The bark gave a bounce under each step.",
        "The bridge still bounced a little",
        tags={"bridge", "stream"},
    ),
    "stones": Route(
        "stones", "the stepping stones", "a line of slippery stepping stones through the creek",
        "tilt",
        "splish-splash slip",
        "Water winked between the stones, and one paw slid sideways.",
        "The stones were still splashy",
        tags={"stones", "creek"},
    ),
    "branch": Route(
        "branch", "the windy branch path", "a high branch path where the breeze could push at anything light",
        "gust",
        "whooo-fff",
        "A teasing breeze puffed right into the path.",
        "The wind still whispered around them",
        tags={"wind", "branch"},
    ),
}

TOOLS = {
    "basket": Tool(
        "basket", "berry basket", "a small berry basket with a bendy willow handle",
        {"berries", "seedcakes"},
        {"jolt", "gust"},
        "set the treat inside the berry basket",
        "the basket swung lightly from one paw, and the evening sun turned its handle gold.",
        tags={"basket"},
    ),
    "jar": Tool(
        "jar", "corked jar", "a corked jar with a snug lid",
        {"honey"},
        {"tilt"},
        "pour the honey into the corked jar",
        "the jar gleamed like amber while the creek made silver sparkles below.",
        tags={"jar"},
    ),
    "tray": Tool(
        "tray", "flat moss tray", "a flat moss tray with little raised edges",
        {"seedcakes"},
        {"jolt"},
        "slide the seed cakes onto the moss tray",
        "the tray rested steady between careful paws, green and soft as a tiny meadow.",
        tags={"tray"},
    ),
    "pouch": Tool(
        "pouch", "chest pouch", "a soft chest pouch tied with grass string",
        {"berries"},
        {"gust", "jolt"},
        "tip the berries into the chest pouch",
        "the pouch sat snug and safe, and not a single berry peeked out.",
        tags={"pouch"},
    ),
}


GIRLISH_NAMES = ["Pip", "Mimi", "Nell", "Tansy", "Poppy", "Lulu"]
BOYISH_NAMES = ["Pip", "Moss", "Tobin", "Nico", "Fern", "Ollie"]


@dataclass
class StoryParams:
    hero: str
    helper: str
    cargo: str
    route: str
    tool: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "berries": [(
        "Why do loose berries roll away so easily?",
        "Berries are small and round, so when something bumps them they can roll quickly. That is why a little wall or basket helps keep them together."
    )],
    "honey": [(
        "Why does honey need a lid?",
        "Honey is sticky and slow, but it still slides if a pot tilts. A lid helps keep it inside the jar instead of dripping out."
    )],
    "seedcake": [(
        "Why can seed cakes crumble?",
        "Seed cakes hold together, but a hard bump can shake crumbs loose. Carrying them on something steady helps them stay neat."
    )],
    "bridge": [(
        "Why can a log bridge make things bounce?",
        "A round log can wobble under little feet. That wobble can jolt whatever you are carrying."
    )],
    "stones": [(
        "Why are stepping stones slippery?",
        "Water makes smooth stones slick. Wet paws can slide, which makes a carried thing tip."
    )],
    "wind": [(
        "What can wind do to light things?",
        "Wind can push at light things and make them sway or blow sideways. That is why it helps to tuck them into something secure."
    )],
    "basket": [(
        "What does a basket do?",
        "A basket keeps small things together so they do not roll away. Its sides help hold the food in place while you carry it."
    )],
    "jar": [(
        "Why is a jar good for honey?",
        "A jar has firm sides and a lid or cork. That helps liquid stay inside even if the path is splashy."
    )],
    "tray": [(
        "When is a tray helpful?",
        "A tray is helpful when you want to carry flat food without squashing it. A steady tray can stop hard bumps from knocking it apart."
    )],
    "pouch": [(
        "What is good about a pouch?",
        "A pouch holds things close to your body, so they do not wobble as much. That can make carrying safer on a bouncy path."
    )],
}
KNOWLEDGE_ORDER = ["berries", "honey", "seedcake", "bridge", "stones", "wind", "basket", "jar", "tray", "pouch"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    route = f["route"]
    tool = f["tool"]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the word "swear" and uses clear sound effects like "{route.sound}" or "{cargo.sound}".',
        f"Tell a gentle forest story where {hero.id} tries to carry {cargo.label} across {route.label}, says \"I swear,\" makes a small mistake, and then accepts help from {helper.id}.",
        f"Write a child-facing animal tale with a wobble, a kind helper, and a happy sharing ending using {tool.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    route = f["route"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {f['hero_spec'].animal}, and {helper.id}, a kind {f['helper_spec'].animal}. They are trying to bring food to share at the snack stone."
        ),
        (
            f"What did {hero.id} say with the word 'swear'?",
            f"{hero.id} said, \"I swear I can do it,\" because {hero.pronoun('subject')} felt proud and wanted to carry the treat alone. That line shows {hero.pronoun('subject')} were brave, but not careful yet."
        ),
        (
            f"Why did the first trip go wrong?",
            f"The first trip went wrong because {route.label} goes {route.sound}, and that kind of path was bad for {cargo.label}. The route made the treat bounce or tip, so some of it spilled before help came."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} brought {tool.phrase} and showed a safer way to carry the {cargo.label}. The tool matched both the treat and the path, so the second trip stayed steady."
        ),
        (
            "How did the story end?",
            f"It ended with the animals sharing the treat together at the snack stone. The ending image proves the problem changed, because after the spill and worry, the food arrived safely."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cargo_cfg"].tags) | set(world.facts["route"].tags) | set(world.facts["tool"].tags)
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("squirrel", "hedgehog", "berries", "log", "basket", "Pip", "Bram"),
    StoryParams("rabbit", "robin", "honey", "stones", "jar", "Mimi", "Red"),
    StoryParams("otter", "turtle", "seedcakes", "branch", "basket", "Nico", "Shell"),
    StoryParams("rabbit", "hedgehog", "seedcakes", "log", "tray", "Tansy", "Prickle"),
    StoryParams("squirrel", "turtle", "berries", "branch", "pouch", "Fern", "Mossback"),
]


def explain_rejection(cargo: Cargo, route: Route, tool: Tool) -> str:
    if not route_threatens(route, cargo):
        return (
            f"(No story: {route.label} does not create the kind of trouble that would spill {cargo.label}. "
            f"The problem needs a real risk before a rescue plan makes sense.)"
        )
    if not tool_fits(tool, cargo):
        return (
            f"(No story: {tool.label} is not a sensible carrier for {cargo.label}. "
            f"Pick a tool that actually fits the food.)"
        )
    return (
        f"(No story: {tool.label} fits {cargo.label}, but it does not protect against the {route.hazard} hazard on {route.label}. "
        f"The fix must actually solve the trouble on this path.)"
    )


ASP_RULES = r"""
threatens(C, R) :- cargo(C), route(R), risk(C, H), hazard(R, H).
fits(C, T) :- cargo(C), tool(T), fit(T, C).
solves(C, R, T) :- threatens(C, R), fits(C, T), route(R), tool(T), hazard(R, H), guard(T, H).
valid(Hero, C, R, T) :- hero(Hero), cargo(C), route(R), tool(T), solves(C, R, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for cid, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cid))
        for risk in sorted(cargo.risks):
            lines.append(asp.fact("risk", cid, risk))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("hazard", rid, route.hazard))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fit in sorted(tool.fits):
            lines.append(asp.fact("fit", tid, fit))
        for guard in sorted(tool.guards):
            lines.append(asp.fact("guard", tid, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "swear" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story was empty or missing 'swear'.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify mode guard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a proud little helper learns that a smart plan beats a risky path."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.route and args.tool:
        cargo = CARGO[args.cargo]
        route = ROUTES[args.route]
        tool = TOOLS[args.tool]
        if not tool_solves(tool, route, cargo):
            raise StoryError(explain_rejection(cargo, route, tool))

    combos = [
        c for c in valid_combos()
        if (args.hero is None or c[0] == args.hero)
        and (args.cargo is None or c[1] == args.cargo)
        and (args.route is None or c[2] == args.route)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, cargo_id, route_id, tool_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_name = args.hero_name or rng.choice(GIRLISH_NAMES + BOYISH_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRLISH_NAMES + BOYISH_NAMES + ["Bram", "Red", "Shell", "Prickle", "Mossback"]) if n != hero_name])
    return StoryParams(hero_id, helper_id, cargo_id, route_id, tool_id, hero_name, helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        HEROES[params.hero],
        HELPERS[params.helper],
        CARGO[params.cargo],
        ROUTES[params.route],
        TOOLS[params.tool],
        params.hero_name,
        params.helper_name,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, cargo, route, tool) combos:\n")
        for hero, cargo, route, tool in combos:
            print(f"  {hero:8} {cargo:10} {route:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.cargo} on {p.route} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
