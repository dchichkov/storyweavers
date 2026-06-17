#!/usr/bin/env python3
"""
storyworlds/worlds/snow_day_help.py
===================================

Snow-day helpfulness world.

The child wants to walk out in winter weather. The scene only works when the
chosen weather, helper action, gear item, and path are compatible. A parent
predicts risk first, asks for one helpful action, and then the trio goes out
along the safe path.

Usage:
    python storyworlds/worlds/snow_day_help.py
    python storyworlds/worlds/snow_day_help.py --all --trace --qa
    python storyworlds/worlds/snow_day_help.py --weather ice_storm --item boots
    python storyworlds/worlds/snow_day_help.py --verify
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

# Standalone-script bootstrap for storyworlds/results.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SAFE_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    region: str = ""
    worn_by: Optional[str] = None
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def phrase_for(self) -> str:
        return self.phrase or self.label


@dataclass
class Setting:
    place: str
    phrase: str
    available_paths: set[str]


@dataclass
class Weather:
    id: str
    phrase: str
    hazard: int


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    safety: int
    traits: set[str] = field(default_factory=set)


@dataclass
class HelperAction:
    id: str
    label: str
    phrase: str
    safety: int
    needs_item: set[str] = field(default_factory=set)


@dataclass
class SnowPath:
    id: str
    label: str
    phrase: str
    hazard: int
    allowed_actions: set[str]
    notes: str = ""


@dataclass
class World:
    setting: Setting
    weather: Weather
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return copy.deepcopy(self)


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def route_hazard(weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> int:
    return weather.hazard + path.hazard - item.safety - action.safety


def is_route_safe(weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> bool:
    if path.id == "frozen_bridge" and weather.id == "ice_storm" and action.id != "wear_boots":
        return False
    if item.id not in (action.needs_item or {item.id}):
        return False
    if action.id not in path.allowed_actions:
        return False
    return route_hazard(weather, item, action, path) <= SAFE_LIMIT


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for weather_id, weather in WEATHERS.items():
            for item_id, item in ITEMS.items():
                for action_id, action in HELPERS.items():
                    for path_id in setting.available_paths:
                        path = PATHS[path_id]
                        if is_route_safe(weather, item, action, path):
                            combos.append((place_id, weather_id, item_id, action_id, path_id))
    return sorted(combos)


def _warn_message(weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> str:
    return (
        f"{weather.phrase} makes the path risky. "
        f"{action.label} with {item.label} keeps the walk safer than running out "
        f"without thinking."
    )


def _r_confidence(world: World) -> list[str]:
    hero = world.facts.get("hero")
    if not isinstance(hero, Entity):
        return []
    if hero.memes["safe_route"] >= 1 and hero.memes["prepared"] >= 1:
        sig = ("confidence", hero.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["joy"] += 1
        return [f"{hero.label} felt ready and proud."]
    return []


def _r_cleanup(world: World) -> list[str]:
    hero = world.facts.get("hero")
    parent = world.facts.get("parent")
    if not isinstance(hero, Entity) or not isinstance(parent, Entity):
        return []
    if not world.facts.get("safe_arrival"):
        return []
    sig = ("cleanup", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if parent:
        parent.memes["trust"] += 1
        return [f"{parent.label.capitalize()} smiled and said, \"Great teamwork.\""]
    return []


CAUSAL_RULES = [
    Rule("confidence", _r_confidence),
    Rule("trust", _r_cleanup),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def maybe_predict(weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> dict:
    # Lightweight forward simulation: route_hazard is the only causal mechanism.
    return {
        "safe": is_route_safe(weather, item, action, path),
        "hazard": route_hazard(weather, item, action, path),
        "action_ok": item.id in (action.needs_item or {item.id}),
        "path_ok": action.id in path.allowed_actions,
    }


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    article = "a little boy" if hero.type == "boy" else "a little girl"
    world.say(f"Once upon a time, there was {article} named {hero.id} with {hero.pronoun('possessive')} helper {parent.label}.")
    world.say(f"{hero.pronoun().capitalize()} loved winter mornings and wanted to walk through {world.setting.phrase}.")


def describe_weather(world: World, weather: Weather) -> None:
    world.say(f"The whole town watched as {weather.phrase} moved through.")


def equip_item(world: World, hero: Entity, item: Item) -> None:
    world.say(f"{hero.id} prepared {item.label}.")


def warning(world: World, parent: Entity, hero: Entity, weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> None:
    pred = maybe_predict(weather, item, action, path)
    if pred["safe"]:
        world.say(
            f'{parent.label.capitalize()} said, '
            f'"This might be slippery, but if we {action.phrase}, this path can be safe."'
        )
    else:
        world.say(
            f'"This looks too dangerous," {parent.label} said. '
            f'"Even with you trying, {path.label} in this weather is not safe."'
        )
    if not pred["action_ok"] or not pred["path_ok"]:
        world.say(_warn_message(weather, item, action, path))


def helper_scene(world: World, hero: Entity, parent: Entity, item: Item, action: HelperAction) -> bool:
    hero.memes["prepared"] += 1
    if item.safety > 0:
        world.say(f"{hero.id} and {parent.label} chose to {action.phrase}.")
        return True
    world.say(f"{hero.id} tried to {action.phrase}, but it was not much help.")
    return False


def take_path(world: World, hero: Entity, weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> None:
    pred = maybe_predict(weather, item, action, path)
    if pred["safe"]:
        hero.memes["safe_route"] += 1
        hero.memes["safe_arrival"] += 1
        world.facts["safe_arrival"] = True
        world.say(
            f"Then they took the {path.label}. The walk stayed steady, "
            f"and they reached their place safely."
        )
    else:
        hero.memes["safe_arrival"] += 0
        world.facts["safe_arrival"] = False
        parent = world.get("parent")
        world.say(
            f"They reached {path.label} too late for comfort. The path was too rough, "
            f"so {parent.label} brought them back inside."
        )


def moral(world: World, hero: Entity, parent: Entity, safe_arrival: bool) -> None:
    if safe_arrival:
        world.say(
            f"{parent.label.capitalize()} hugged {hero.pronoun('object')} and said, "
            f'"Thanks for being helpful first, then we can enjoy the day."'
        )
        world.facts["resolution"] = "safe"
    else:
        world.say(
            f"{parent.label.capitalize()} said, \"Tomorrow will be kinder; let's try a different plan.\""
        )
        world.facts["resolution"] = "deferred"
    propagate(world, narrate=True)


def build_story(setting: Setting, weather: Weather, item: Item, action: HelperAction, path: SnowPath,
                hero_name: str, hero_gender: str, parent_name: str) -> World:
    world = World(setting=setting, weather=weather)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
    ))
    parent = world.add(Entity(
        id=parent_name,
        kind="character",
        type="mother" if hero_gender == "girl" else "father",
        label=parent_name,
    ))
    item_ent = world.add(Entity(
        id=item.id,
        type=item.id,
        kind="thing",
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region="body",
    ))
    item_ent.memes["helpfulness"] += 1

    # Act 1: setup
    introduce(world, hero, parent)
    describe_weather(world, weather)
    world.para()

    # Act 2: warning and helpful compromise
    equip_item(world, hero, item)
    warning(world, parent, hero, weather, item, action, path)
    helper_scene(world, hero, parent, item, action)
    world.para()

    # Act 3: travel and resolution
    safe_arrival = maybe_predict(weather, item, action, path)["safe"]
    take_path(world, hero, weather, item, action, path)

    world.facts.update(
        hero=hero,
        parent=parent,
        setting=setting,
        weather=weather,
        item=item,
        action=action,
        path=path,
        safe_arrival=safe_arrival,
    )

    moral(world, hero, parent, safe_arrival)
    return world


def label(word: str) -> str:
    return word.replace("_", " ")


SETTINGS: dict[str, Setting] = {
    "neighborhood": Setting("neighborhood", "their snowy neighborhood", {"front_walk", "short_cut"}),
    "park": Setting("park", "the local park", {"front_walk", "short_cut", "frozen_bridge"}),
    "town_center": Setting("town_center", "the town center", {"front_walk", "short_cut"}),
}

WEATHERS: dict[str, Weather] = {
    "light_snow": Weather("light_snow", "a gentle, light snowfall", 0),
    "snowstorm": Weather("snowstorm", "a heavy snowstorm", 2),
    "ice_storm": Weather("ice_storm", "a fierce ice storm", 3),
}

ITEMS: dict[str, Item] = {
    "boots": Item("boots", "snow boots", "snow boots", 2, {"footwear", "traction"}),
    "shovel": Item("shovel", "a shovel", "shovel", 1, {"path_work"}),
    "scarf": Item("scarf", "a warm scarf", "scarf", 1, {"warm", "wind"}),
    "coat": Item("coat", "a thick coat", "thick coat", 2, {"warm", "wind"}),
    "mittens": Item("mittens", "mittens", "mittens", 1, {"warm", "grip"}),
}

HELPERS: dict[str, HelperAction] = {
    "clear_path": HelperAction(
        "clear_path",
        "clear the path",
        "clear the drifted path before stepping out",
        2,
        needs_item={"shovel"},
    ),
    "wear_boots": HelperAction(
        "wear_boots",
        "put on protective boots",
        "put on warm boots",
        2,
        needs_item={"boots"},
    ),
    "layer_up": HelperAction(
        "layer_up",
        "layer up",
        "layer up with warm clothes",
        1,
        needs_item={"scarf", "coat", "mittens"},
    ),
    "call_help": HelperAction(
        "call_help",
        "walk with an adult helper",
        "call for a helping hand",
        1,
    ),
}

PATHS: dict[str, SnowPath] = {
    "front_walk": SnowPath(
        "front_walk",
        "front walk",
        "front walk",
        1,
        {"clear_path", "wear_boots", "layer_up", "call_help"},
        "The normal route stays clear enough if prepared well.",
    ),
    "short_cut": SnowPath(
        "short_cut",
        "short cut",
        "short cut",
        2,
        {"clear_path", "wear_boots", "layer_up", "call_help"},
        "A shorter route with a higher slip risk.",
    ),
    "frozen_bridge": SnowPath(
        "frozen_bridge",
        "frozen bridge",
        "frozen bridge",
        3,
        {"wear_boots", "call_help"},
        "A narrow bridge needs both traction and cooperation.",
    ),
}


@dataclass
class StoryParams:
    place: str
    weather: str
    item: str
    action: str
    path: str
    hero: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short winter story about a parent helping a child stay safe.",
        f"Tell a cautionary tale set in {f['setting'].phrase} with {label(f['weather'].id)} weather.",
        f"Use a helpful action that makes a risky {f['path'].phrase} safe on a snow day.",
    ]


KNOWLEDGE = {
    "boots": [("What do boots help with?", "Boots give extra traction and keep feet warm in cold weather.")],
    "shovel": [("What is a shovel for on a snowy day?", "A shovel clears packed snow and can make a narrow path safer.")],
    "scarf": [("Why do children wear scarves?", "A scarf helps keep the face warm and can reduce chilling.")],
    "coat": [("Why is a coat useful in snow?", "A coat adds insulation and blocks cold wind.")],
    "mittens": [("Why wear mittens instead of thin gloves?", "Mittens protect more of the hand and keep fingers warmer.")],
    "front_walk": [("What is the front walk in this story?", "It is the usual route, usually the safest path.")],
    "short_cut": [("What is risky about a short cut?", "A short cut can be steeper or slicker and needs extra preparation.")],
    "frozen_bridge": [("Why is a frozen bridge risky?", "A frozen bridge can be slick, so slips are more likely.")],
    "snowstorm": [("What makes a snowstorm risky?", "Strong snow and wind reduce visibility and traction.")],
    "ice_storm": [("Why is an ice storm dangerous for walking?", "Freezing ice makes surfaces very slick.")],
}
KNOWLEDGE_ORDER = [
    "boots", "shovel", "coat", "scarf", "mittens",
    "front_walk", "short_cut", "frozen_bridge", "snowstorm", "ice_storm",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    path = f["path"]
    weather = f["weather"]
    action = f["action"]
    item = f["item"]
    pred = maybe_predict(weather, item, action, path)
    safe = f.get("safe_arrival", False)
    qa: list[tuple[str, str]] = [
        (f"Who is the story about?",
         f"It is about {hero.label}, helper {parent.label}, and a snow-day walk."),
        (f"What weather are they in?",
         f"They walked during {weather.phrase}."),
        ("What helpful action did the parent ask for?",
         f"The parent asked {hero.label} to {action.phrase}. {item.label.capitalize()} was part of the safe winter preparation."),
        (f"How did they make the {path.label} safe?",
         f"They prepared before stepping outside. The plan brought the route risk down to {pred['hazard']}, so the {path.label} was safe enough to use."),
    ]
    if safe:
        qa.append((f"What was the outcome of the story?",
                  f"They took the {path.label} and stayed safe because they acted before leaving."))
    else:
        qa.append(("What was the outcome?", "They stayed inside because the path was still too risky."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {
        f["item"].id,
        f["weather"].id,
        f["path"].id,
    }
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.caretaker:
            bits.append(f"caretaker={ent.caretaker}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if ent.region:
            bits.append(f"region={ent.region}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  safe path predicted: {world.facts.get('safe_arrival')}")
    return "\n".join(lines)


CURATED = [
    StoryParams("park", "snowstorm", "boots", "wear_boots", "short_cut", "Lena", "girl", "Mama"),
    StoryParams("neighborhood", "light_snow", "scarf", "layer_up", "front_walk", "Milo", "boy", "Dad"),
    StoryParams("park", "ice_storm", "boots", "wear_boots", "frozen_bridge", "Nora", "girl", "Dad"),
    StoryParams("town_center", "snowstorm", "coat", "call_help", "front_walk", "Tia", "girl", "Mom"),
]


def explain_rejection(place: str, weather: Weather, item: Item, action: HelperAction, path: SnowPath) -> str:
    if not is_route_safe(weather, item, action, path):
        return (
            f"(No story: in {place} with {weather.phrase}, {action.label} with "
            f"{item.label} does not make {path.label} safe.)"
        )
    return ""


ASP_RULES = r"""
setting(neighborhood).
setting(park).
setting(town_center).

path(front_walk).
path(short_cut).
path(frozen_bridge).

weather(light_snow, 0).
weather(snowstorm, 2).
weather(ice_storm, 3).

item(boots, 2).
item(shovel, 1).
item(scarf, 1).
item(coat, 2).
item(mittens, 1).

action(clear_path, 2).
action(wear_boots, 2).
action(layer_up, 1).
action(call_help, 1).

action_item_ok(clear_path, shovel).
action_item_ok(wear_boots, boots).
action_item_ok(layer_up, scarf).
action_item_ok(layer_up, coat).
action_item_ok(layer_up, mittens).
action_item_ok(call_help, boots).
action_item_ok(call_help, shovel).
action_item_ok(call_help, scarf).
action_item_ok(call_help, coat).
action_item_ok(call_help, mittens).

path_allows(front_walk, clear_path).
path_allows(front_walk, wear_boots).
path_allows(front_walk, layer_up).
path_allows(front_walk, call_help).
path_allows(short_cut, clear_path).
path_allows(short_cut, wear_boots).
path_allows(short_cut, layer_up).
path_allows(short_cut, call_help).
path_allows(frozen_bridge, wear_boots).
path_allows(frozen_bridge, call_help).

setting_path(neighborhood, front_walk).
setting_path(neighborhood, short_cut).
setting_path(park, front_walk).
setting_path(park, short_cut).
setting_path(park, frozen_bridge).
setting_path(town_center, front_walk).
setting_path(town_center, short_cut).

path_hazard(front_walk, 1).
path_hazard(short_cut, 2).
path_hazard(frozen_bridge, 3).

safe(P,W,I,A,Pt) :-
    setting(P),
    setting_path(P, Pt),
    weather(W, WH),
    item(I, IS),
    action(A, AS),
    action_item_ok(A, I),
    path_allows(Pt, A),
    path_hazard(Pt, PH),
    WH + PH - IS - AS <= 2,
    not blocked_bridge(W, Pt, A).

blocked_bridge(W, Pt, A) :-
    action(A, _),
    W = ice_storm,
    Pt = frozen_bridge,
    A != wear_boots.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in sorted(SETTINGS):
        lines.append(asp.fact("setting", place))
        for path_id in sorted(SETTINGS[place].available_paths):
            lines.append(asp.fact("setting_path", place, path_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id, weather.hazard))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id, item.safety))
    for action_id, action in HELPERS.items():
        lines.append(asp.fact("action", action_id, action.safety))
        if action.needs_item:
            for item_id in sorted(action.needs_item):
                lines.append(asp.fact("action_item_ok", action_id, item_id))
        else:
            for item_id in sorted(ITEMS):
                lines.append(asp.fact("action_item_ok", action_id, item_id))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path_hazard", path_id, path.hazard))
        for action_id in sorted(path.allowed_actions):
            lines.append(asp.fact("path_allows", path_id, action_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show safe/5."))
    return sorted(set(asp.atoms(model, "safe")))


def asp_verify() -> int:
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: inline ASP gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between Python gate and inline ASP gate:")
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Snow-day helpfulness with weather, item, helper action, and path constraints."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=HELPERS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--hero")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None, help="base seed for random choices")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, weather, item, action, path) combos")
    ap.add_argument("--verify", action="store_true", help="check Python vs inline ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [c for c in valid_combos()
                  if (args.place is None or c[0] == args.place)
                  and (args.weather is None or c[1] == args.weather)
                  and (args.item is None or c[2] == args.item)
                  and (args.action is None or c[3] == args.action)
                  and (args.path is None or c[4] == args.path)]

    if not candidates:
        if args.place and args.weather and args.item and args.action and args.path:
            place = SETTINGS[args.place]
            w = WEATHERS[args.weather]
            item = ITEMS[args.item]
            action = HELPERS[args.action]
            path = PATHS[args.path]
            raise StoryError(explain_rejection(place.place, w, item, action, path))
        raise StoryError("(No valid combinations match the requested options.)")

    place_id, weather_id, item_id, action_id, path_id = rng.choice(candidates)
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(names)
    parent = args.parent or ("Maya" if gender == "girl" else "Milo")
    return StoryParams(place_id, weather_id, item_id, action_id, path_id, hero, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = build_story(
        SETTINGS[params.place],
        WEATHERS[params.weather],
        ITEMS[params.item],
        HELPERS[params.action],
        PATHS[params.path],
        params.hero,
        params.gender,
        params.parent,
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
        print("")
        print(dump_trace(sample.world))
    if qa and sample.world is not None:
        print("")
        print(format_qa(sample))


GIRL_NAMES = ["Lena", "Maya", "Nora", "Tia", "Zia", "Ella", "Mira"]
BOY_NAMES = ["Milo", "Sam", "Noah", "Kai", "Owen", "Eli", "Raf"]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, weather, item, action, path) combinations:")
        for p, w, i, a, path in combos:
            print(f"  {p:12} {w:10} {i:8} {a:11} {path}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.hero} in {p.place}: {p.weather}/{p.path}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
