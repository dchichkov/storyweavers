#!/usr/bin/env python3
"""
storyworlds/worlds/honey_dusty_moss_misty_path_shopping_mall_3.py
=================================================================

A standalone storyworld for a seed prompt:

    Words: honey, dusty moss, misty path
    Setting: shopping mall
    Features: Inner Monologue, Bad Ending, Dialogue
    Style: Pirate Tale

Internal source tale
--------------------
At a shopping mall pirate event, a child follows a misty path toward a prize
chest while a grown-up keeps watch. The path winds past a display dressed with
dusty moss and a tempting honey reward. The child hears clear warnings, but an
inner boast says a quick pirate shortcut will win the prize first. The child
breaks the rules, makes a sticky mess, and the mall game closes before the
prize chest can be opened. The ending is not cruel, but it is plainly bad: the
child loses the game and must watch the misty path go dark.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass(frozen=True)
class MallRoute:
    key: str
    phrase: str
    path_phrase: str
    crowd_phrase: str
    warning_line: str
    closure_line: str
    final_image: str
    allowed_displays: tuple[str, ...]
    allowed_choices: tuple[str, ...]
    fog_level: float
    crowd_level: float


@dataclass(frozen=True)
class DisplayTrap:
    key: str
    phrase: str
    fragile_part: str
    warning_line: str
    compatible_choices: tuple[str, ...]
    compatible_temptations: tuple[str, ...]


@dataclass(frozen=True)
class Temptation:
    key: str
    phrase: str
    smell_line: str
    promise: str
    mess_phrase: str
    compatible_choices: tuple[str, ...]


@dataclass(frozen=True)
class BadChoice:
    key: str
    thought_line: str
    whisper_line: str
    action_line: str
    stumble_line: str
    off_path: float
    display_damage: float
    honey_spill: float
    slip_gain: float
    balance_cost: float


@dataclass
class StoryParams:
    route: str
    display: str
    temptation: str
    choice: str
    hero: str
    gender: str
    companion: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    route: MallRoute
    display: DisplayTrap
    temptation: Temptation
    choice: BadChoice
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, line: str) -> None:
        if line:
            self.paragraphs[-1].append(line)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(bits) for bits in self.paragraphs if bits)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"route={self.route.key}")
        rows.append(f"display={self.display.key}")
        rows.append(f"temptation={self.temptation.key}")
        rows.append(f"choice={self.choice.key}")
        for ent in self.entities.values():
            rows.append(
                f"{ent.id}<{ent.type}> label={ent.label!r} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"facts={self.facts}")
        rows.append(f"fired={self.fired}")
        return "\n".join(rows)


ROUTES: dict[str, MallRoute] = {
    "atrium_cove": MallRoute(
        key="atrium_cove",
        phrase="the Pearl Plaza shopping mall atrium",
        path_phrase="a misty path of blue lantern lights that curled around the fountain",
        crowd_phrase="shoppers leaned over the railings as if they were watching a tiny harbor parade",
        warning_line="Stay on the lantern marks, matey, and keep your hands to yourself.",
        closure_line="The game clerk pulled the rope across the atrium trail and shut the pirate game for cleaning.",
        final_image="The fountain glittered beside a closed prize chest while the mall music kept playing without the hero.",
        allowed_displays=("moss_island", "captain_window"),
        allowed_choices=("duck_under_rope", "grab_honey_jar"),
        fog_level=1.0,
        crowd_level=0.7,
    ),
    "food_court_quay": MallRoute(
        key="food_court_quay",
        phrase="the shopping mall food court",
        path_phrase="a misty path that ran between trays and chairs like a little harbor lane",
        crowd_phrase="families paused with drinks and watched the treasure game from the tables",
        warning_line="Slow feet only, matey. The food court floor is no deck for running wild.",
        closure_line="A worker rolled over with towels, and the rope went up across the food-court trail.",
        final_image="By the tray return, the little bell stayed silent and the prize chest sat dark under the food-court lights.",
        allowed_displays=("moss_island", "fog_bridge"),
        allowed_choices=("duck_under_rope", "run_for_chest"),
        fog_level=0.8,
        crowd_level=0.9,
    ),
    "arcade_docks": MallRoute(
        key="arcade_docks",
        phrase="the second-floor arcade wing of the shopping mall",
        path_phrase="a misty path that slipped beneath blinking signs toward a toy ship bow",
        crowd_phrase="arcade noises chimed like gulls while children queued along the wall",
        warning_line="Wait for the lantern cue, matey. Treasure comes to patient sailors.",
        closure_line="The helper dropped the rope and turned the arcade trail into a no-entry lane.",
        final_image="The toy ship blinked behind the rope, and the ticket chest stayed locked while other children stared.",
        allowed_displays=("captain_window", "fog_bridge"),
        allowed_choices=("grab_honey_jar", "run_for_chest"),
        fog_level=1.2,
        crowd_level=0.8,
    ),
}

DISPLAYS: dict[str, DisplayTrap] = {
    "moss_island": DisplayTrap(
        key="moss_island",
        phrase="a fake island ringed with dusty moss and cardboard rocks",
        fragile_part="a cardboard palm tree",
        warning_line='"Keep outside the rope," called the game clerk. "That island is for eyes, not feet."',
        compatible_choices=("duck_under_rope", "grab_honey_jar"),
        compatible_temptations=("honey_bun", "honey_token"),
    ),
    "captain_window": DisplayTrap(
        key="captain_window",
        phrase="a captain window display with dusty moss tucked around a gold compass tray",
        fragile_part="the compass tray",
        warning_line='"Hands off the captain display," said the cookie seller. "The prize comes at the end of the path."',
        compatible_choices=("grab_honey_jar", "run_for_chest"),
        compatible_temptations=("honey_jar", "honey_token"),
    ),
    "fog_bridge": DisplayTrap(
        key="fog_bridge",
        phrase="a short bridge of crate planks with dusty moss packed around the rails",
        fragile_part="a crate rail",
        warning_line='"One slow sailor at a time," warned the parade helper. "The bridge is part of the show."',
        compatible_choices=("duck_under_rope", "run_for_chest"),
        compatible_temptations=("honey_bun", "honey_jar"),
    ),
}

TEMPTATIONS: dict[str, Temptation] = {
    "honey_bun": Temptation(
        key="honey_bun",
        phrase="a paper flag promising a free honey bun to the first child at the chest",
        smell_line="Warm honey drifted from a nearby bakery counter and wrapped the whole pirate game in a sweet smell.",
        promise="the free honey bun flag",
        mess_phrase="a stripe of honey glaze",
        compatible_choices=("duck_under_rope", "run_for_chest"),
    ),
    "honey_jar": Temptation(
        key="honey_jar",
        phrase="a clear honey jar with a plastic doubloon floating inside",
        smell_line="A sweet ribbon of honey drifted from the sample counter beside the pirate game.",
        promise="the shiny honey jar and its doubloon",
        mess_phrase="a spoonful of sticky honey",
        compatible_choices=("grab_honey_jar", "run_for_chest"),
    ),
    "honey_token": Temptation(
        key="honey_token",
        phrase="a honey-glazed compass cookie pinned beside the prize map",
        smell_line="The compass cookie smelled of honey and butter, almost like treasure you could eat.",
        promise="the honey compass cookie",
        mess_phrase="crumbs and honey streaks",
        compatible_choices=("duck_under_rope", "grab_honey_jar"),
    ),
}

CHOICES: dict[str, BadChoice] = {
    "duck_under_rope": BadChoice(
        key="duck_under_rope",
        thought_line="If I slip under the rope right now, I can beat the whole deck to the prize.",
        whisper_line='"Only one quick shortcut," {hero} whispered.',
        action_line="{hero} ducked under the rope and cut across the display edge instead of staying on the marked path.",
        stumble_line="A shoe caught the display border, and the pirate set shivered.",
        off_path=1.2,
        display_damage=0.8,
        honey_spill=0.6,
        slip_gain=0.4,
        balance_cost=0.4,
    ),
    "grab_honey_jar": BadChoice(
        key="grab_honey_jar",
        thought_line="If I grab the sweet treasure first, everyone will see I am the boldest sailor here.",
        whisper_line='"No one will mind one tiny touch," {hero} murmured.',
        action_line="{hero} reached past the warning sign for the tempting display instead of waiting for the game to offer the prize.",
        stumble_line="The display tipped just enough for the sweet bait to slide loose.",
        off_path=1.0,
        display_damage=0.7,
        honey_spill=1.2,
        slip_gain=0.5,
        balance_cost=0.5,
    ),
    "run_for_chest": BadChoice(
        key="run_for_chest",
        thought_line="If I dash before the next lantern cue, the chest will be mine before anyone can blink.",
        whisper_line='"Fast feet win treasure," {hero} said under {hero_possessive} breath.',
        action_line="{hero} bolted along the misty path without waiting for the next signal from the helper.",
        stumble_line="The fog hid a slick patch beside the display, and the rush turned into a skid.",
        off_path=1.1,
        display_damage=0.5,
        honey_spill=0.8,
        slip_gain=0.8,
        balance_cost=0.7,
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Lina", "Nessa", "Tali"),
    "boy": ("Rafi", "Milo", "Tobin", "Eren"),
}

COMPANIONS: tuple[str, ...] = ("Aunt Bea", "Uncle Joss", "Big Sister Nia", "Dad Rowan")


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[gender])


def _pick_companion(rng: random.Random) -> str:
    return rng.choice(COMPANIONS)


def valid_combo(route_key: str, display_key: str, temptation_key: str, choice_key: str) -> bool:
    if route_key not in ROUTES or display_key not in DISPLAYS:
        return False
    if temptation_key not in TEMPTATIONS or choice_key not in CHOICES:
        return False
    route = ROUTES[route_key]
    display = DISPLAYS[display_key]
    temptation = TEMPTATIONS[temptation_key]
    return (
        display_key in route.allowed_displays
        and choice_key in route.allowed_choices
        and choice_key in display.compatible_choices
        and temptation_key in display.compatible_temptations
        and choice_key in temptation.compatible_choices
    )


def invalid_reason(route_key: str, display_key: str, temptation_key: str, choice_key: str) -> str:
    if route_key not in ROUTES:
        return f"No story: unknown mall route {route_key!r}."
    if display_key not in DISPLAYS:
        return f"No story: unknown display {display_key!r}."
    if temptation_key not in TEMPTATIONS:
        return f"No story: unknown temptation {temptation_key!r}."
    if choice_key not in CHOICES:
        return f"No story: unknown bad choice {choice_key!r}."

    route = ROUTES[route_key]
    display = DISPLAYS[display_key]
    temptation = TEMPTATIONS[temptation_key]
    if display_key not in route.allowed_displays:
        return (
            f"No story: {route.phrase} does not stage display {display_key!r}. "
            f"Try one of: {', '.join(route.allowed_displays)}."
        )
    if choice_key not in route.allowed_choices:
        return (
            f"No story: {route.phrase} does not support bad choice {choice_key!r}. "
            f"Try one of: {', '.join(route.allowed_choices)}."
        )
    if choice_key not in display.compatible_choices:
        return (
            f"No story: {display.phrase} does not fail in the way {choice_key!r}. "
            f"It fits: {', '.join(display.compatible_choices)}."
        )
    if temptation_key not in display.compatible_temptations:
        return (
            f"No story: {display.phrase} is not stocked with temptation {temptation_key!r}. "
            f"It fits: {', '.join(display.compatible_temptations)}."
        )
    if choice_key not in temptation.compatible_choices:
        return (
            f"No story: temptation {temptation_key!r} does not lure choice {choice_key!r}. "
            f"It fits: {', '.join(temptation.compatible_choices)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_key in sorted(ROUTES):
        for display_key in sorted(DISPLAYS):
            for temptation_key in sorted(TEMPTATIONS):
                for choice_key in sorted(CHOICES):
                    if valid_combo(route_key, display_key, temptation_key, choice_key):
                        combos.append((route_key, display_key, temptation_key, choice_key))
    return combos


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random(args.seed + index)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(gender, rng)
    companion = args.companion or _pick_companion(rng)
    route_key, display_key, temptation_key, choice_key = combo
    return StoryParams(
        route=route_key,
        display=display_key,
        temptation=temptation_key,
        choice=choice_key,
        hero=hero,
        gender=gender,
        companion=companion,
        seed=args.seed + index,
    )


def build_world(params: StoryParams) -> World:
    route = ROUTES[params.route]
    display = DISPLAYS[params.display]
    temptation = TEMPTATIONS[params.temptation]
    choice = CHOICES[params.choice]
    world = World(params=params, route=route, display=display, temptation=temptation, choice=choice)

    hero = world.add(Entity("hero", params.hero, params.gender))
    hero.meters["balance"] = 1.0
    hero.meters["sticky_shoes"] = 0.0
    hero.meters["off_path"] = 0.0
    hero.memes["caution"] = 1.0
    hero.memes["pride"] = 0.8
    hero.memes["regret"] = 0.0

    companion = world.add(Entity("companion", params.companion, "adult"))
    companion.memes["calm"] = 1.0
    companion.memes["concern"] = 0.0

    path = world.add(Entity("path", route.path_phrase, "path"))
    path.meters["fog"] = route.fog_level
    path.meters["crowd"] = route.crowd_level
    path.meters["slippery"] = 0.0
    path.meters["open"] = 1.0

    display_ent = world.add(Entity("display", display.phrase, "display"))
    display_ent.meters["dust"] = 1.0
    display_ent.meters["damage"] = 0.0
    display_ent.meters["stable"] = 1.0

    honey = world.add(Entity("honey", temptation.phrase, "treat"))
    honey.meters["spill"] = 0.0
    honey.meters["temptation"] = 1.0

    chest = world.add(Entity("chest", "the prize chest", "chest"))
    chest.meters["open"] = 1.0
    chest.meters["won"] = 0.0

    world.facts["setting"] = "shopping_mall"
    world.facts["style"] = "pirate_tale"
    world.facts["features"] = "inner_monologue,bad_ending,dialogue"
    world.facts["seed"] = str(params.seed)
    world.facts["outcome"] = "pending"
    world.facts["hero"] = hero.label
    world.facts["companion"] = companion.label
    world.facts["misty_path"] = route.path_phrase
    world.facts["temptation"] = temptation.promise
    return world


def _r_honey_turns_floor_slick(world: World) -> list[str]:
    honey = world.get("honey")
    hero = world.get("hero")
    path = world.get("path")
    companion = world.get("companion")
    if honey.meters["spill"] < THRESHOLD:
        return []
    if "honey_turns_floor_slick" in world.fired:
        return []
    world.fired.append("honey_turns_floor_slick")
    hero.meters["sticky_shoes"] += 1.0
    hero.meters["balance"] = max(0.0, hero.meters["balance"] - 0.2)
    path.meters["slippery"] += 0.5
    companion.memes["concern"] += 0.6
    return [
        f"{world.temptation.mess_phrase.capitalize()} smeared over {hero.label}'s shoes, and the mall floor turned slick under the pirate lights."
    ]


def _r_game_shuts_down(world: World) -> list[str]:
    hero = world.get("hero")
    display = world.get("display")
    path = world.get("path")
    chest = world.get("chest")
    companion = world.get("companion")
    if hero.meters["off_path"] < THRESHOLD:
        return []
    if display.meters["damage"] + path.meters["slippery"] < 1.2:
        return []
    if "game_shuts_down" in world.fired:
        return []
    world.fired.append("game_shuts_down")
    path.meters["open"] = 0.0
    chest.meters["open"] = 0.0
    companion.memes["concern"] += 1.0
    world.facts["outcome"] = "path_closed"
    return [
        world.route.closure_line,
        f'"Back behind the rope, matey," said the worker, guiding {hero.label} away from the mess.'
    ]


def _r_bad_ending_lands(world: World) -> list[str]:
    hero = world.get("hero")
    chest = world.get("chest")
    if chest.meters["open"] > 0.0:
        return []
    if "bad_ending_lands" in world.fired:
        return []
    world.fired.append("bad_ending_lands")
    hero.memes["regret"] += 1.3
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 0.5)
    world.facts["outcome"] = "bad_ending"
    return [
        f"{hero.label} did not win the prize chest. The quick pirate boast had turned into a sticky, public mistake."
    ]


RULES = (_r_honey_turns_floor_slick, _r_game_shuts_down, _r_bad_ending_lands)


def propagate(world: World) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    return lines


def _apply_bad_choice(world: World) -> None:
    hero = world.get("hero")
    display = world.get("display")
    honey = world.get("honey")
    path = world.get("path")
    choice = world.choice

    hero.meters["off_path"] += choice.off_path
    hero.meters["balance"] = max(0.0, hero.meters["balance"] - choice.balance_cost)
    hero.memes["caution"] = max(0.0, hero.memes["caution"] - 0.7)
    hero.memes["pride"] += 0.4
    display.meters["damage"] += choice.display_damage
    display.meters["stable"] = max(0.0, display.meters["stable"] - choice.display_damage)
    honey.meters["spill"] += choice.honey_spill
    path.meters["slippery"] += choice.slip_gain


def _opening(world: World) -> str:
    hero = world.get("hero")
    companion = world.get("companion")
    route = world.route
    display = world.display
    temptation = world.temptation
    return (
        f"{hero.label} came with {companion.label} to {route.phrase} for the mall's pirate treasure game. "
        f"{route.path_phrase.capitalize()} led toward a toy chest, and {route.crowd_phrase}. "
        f"{temptation.smell_line} Beside the trail stood {display.phrase}."
    )


def _warning_paragraph(world: World) -> str:
    hero = world.get("hero")
    companion = world.get("companion")
    route = world.route
    display = world.display
    choice = world.choice
    return (
        f'"{route.warning_line}" said {companion.label}. '
        f'Inside, {hero.label} thought, "{choice.thought_line}" '
        f"{display.warning_line} "
        f"{choice.whisper_line.format(hero=hero.label, hero_possessive=hero.pronoun('possessive'))}"
    )


def _action_paragraph(world: World) -> str:
    hero = world.get("hero")
    temptation = world.temptation
    display = world.display
    choice = world.choice
    return (
        f"{choice.action_line.format(hero=hero.label)} "
        f"{choice.stumble_line} "
        f"{temptation.phrase.capitalize()} lurched near {display.fragile_part}, and {temptation.mess_phrase} splashed loose."
    )


def _ending_paragraph(world: World) -> str:
    hero = world.get("hero")
    path = world.get("path")
    display = world.get("display")
    if world.facts["outcome"] != "bad_ending":
        raise StoryError("No story: the requested world failed to reach a bad ending.")
    floor_line = (
        f"Dusty moss clung to {hero.pronoun('possessive')} shoes and "
        f"{world.temptation.mess_phrase} shone on the floor"
    )
    if path.meters["open"] <= 0.0:
        return (
            f"{world.route.final_image} {hero.label} stood still at last, watching the misty path stay closed. "
            f"{floor_line}. The broken display, {display.label}, proved exactly what the boast had cost."
        )
    return (
        f"{hero.label} never reached the prize, and the pirate game felt ruined instead of thrilling. "
        f"{floor_line}, so everyone could see the mistake."
    )


def _prompts(world: World) -> list[str]:
    return [
        "Write a pirate-tale story set in a shopping mall with honey, dusty moss, and a misty path.",
        "Include spoken warnings, a private inner boast, and a bad ending caused by the child's own choice.",
        "Keep the world concrete: a mall pirate game, a visible mess, and a final image that proves the loss.",
    ]


def _display_options(keys: tuple[str, ...]) -> str:
    return ", ".join(DISPLAYS[key].phrase for key in keys)


def _choice_summary(choice_key: str) -> str:
    labels = {
        "duck_under_rope": "ducking under the rope for a shortcut",
        "grab_honey_jar": "reaching for the sweet display instead of waiting",
        "run_for_chest": "running for the chest before the signal",
    }
    return labels[choice_key]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero").label
    companion = world.get("companion").label
    return [
        QAItem(
            "Where does the story happen?",
            f"The story happens in {world.route.phrase}, where a pirate treasure game runs through the shopping mall. The misty path, the display, and the prize chest all belong to that one mall event.",
        ),
        QAItem(
            "What tempted the child to make a bad choice?",
            f"{hero} was drawn by {world.temptation.promise}. That tempting reward sounded faster and sweeter than following the rules, so it fed the risky boast inside the child's head.",
        ),
        QAItem(
            "What warning did the child ignore?",
            f"{companion} warned the child to stay on the marked pirate trail, and the worker also gave a clear spoken warning about the display. The bad ending starts because {hero} hears those rules and breaks them anyway.",
        ),
        QAItem(
            "Why did the pirate game shut down?",
            f"The game shut down because {hero} left the proper path, damaged the display, and made the floor sticky with honey. Once the trail became messy and unsafe, the worker had to close the route instead of letting the game continue.",
        ),
        QAItem(
            "What proves the ending is bad?",
            f"{hero} does not win the prize chest, and the misty path is closed before the turn is finished. The final image leaves the child standing with dusty moss on the shoes and honey on the floor, so the loss is easy to see.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    route = world.route
    display = world.display
    temptation = world.temptation
    choice = world.choice
    return [
        QAItem(
            "Why are only some displays valid for a route?",
            f"Each mall route stages only certain pirate props, so the route has to physically support the chosen display. For {route.phrase}, the fitting displays are {_display_options(route.allowed_displays)} because the local layout and pirate scene were written together.",
        ),
        QAItem(
            "Why is the temptation tied to the display?",
            f"The temptation has to be something that could actually sit in or near the chosen display. In this world, {temptation.phrase} fits {display.phrase}, so the lure feels like part of the set instead of a random object.",
        ),
        QAItem(
            "Why is the bad choice constrained?",
            f"The bad choice must match both the route and the display so the failure reads as a believable chain of events. Here, {_choice_summary(choice.key)} works because the path, crowding, and display structure all make that mistake possible.",
        ),
        QAItem(
            "What physical state changes matter most in this world?",
            "The story cares most about whether the child leaves the marked trail, spills honey, makes the floor slick, damages the display, and forces the path to close. Those visible changes decide when the pirate game stops and why the ending feels like a real loss.",
        ),
    ]


def _exercise_story(sample: StorySample) -> None:
    story = sample.story.lower()
    for needle in ("honey", "dusty moss", "misty path"):
        if needle not in story:
            raise StoryError(f"Generated story is missing required seed phrase {needle!r}.")
    if '"' not in sample.story:
        raise StoryError("Generated story is missing dialogue quotes.")
    if "thought," not in sample.story.lower():
        raise StoryError("Generated story is missing explicit inner monologue.")
    if sample.world is None or sample.world.facts.get("outcome") != "bad_ending":
        raise StoryError("Generated story did not resolve to the required bad ending state.")
    if not sample.story_qa or not sample.world_qa or not sample.prompts:
        raise StoryError("Generated story is missing required QA or prompt sets.")


def _play(world: World) -> str:
    world.say(_opening(world))
    world.para()
    world.say(_warning_paragraph(world))
    world.para()
    world.say(_action_paragraph(world))
    _apply_bad_choice(world)
    for line in propagate(world):
        world.say(line)
    world.para()
    world.say(_ending_paragraph(world))
    return world.render()


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.route, params.display, params.temptation, params.choice):
        raise StoryError(invalid_reason(params.route, params.display, params.temptation, params.choice))
    world = build_world(params)
    sample = StorySample(
        params=params,
        story=_play(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )
    _exercise_story(sample)
    return sample


ASP_RULES = r"""
combo(R,D,T,C) :-
    route(R),
    display(D),
    temptation(T),
    bad_choice(C),
    route_has_display(R, D),
    route_allows_choice(R, C),
    display_allows_choice(D, C),
    display_has_temptation(D, T),
    temptation_lures_choice(T, C).

ok :- chosen(R, D, T, C), combo(R, D, T, C).

#show combo/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for route_key, route in sorted(ROUTES.items()):
        rows.append(fact("route", route_key))
        for display_key in route.allowed_displays:
            rows.append(fact("route_has_display", route_key, display_key))
        for choice_key in route.allowed_choices:
            rows.append(fact("route_allows_choice", route_key, choice_key))
    for display_key, display in sorted(DISPLAYS.items()):
        rows.append(fact("display", display_key))
        for choice_key in display.compatible_choices:
            rows.append(fact("display_allows_choice", display_key, choice_key))
        for temptation_key in display.compatible_temptations:
            rows.append(fact("display_has_temptation", display_key, temptation_key))
    for temptation_key, temptation in sorted(TEMPTATIONS.items()):
        rows.append(fact("temptation", temptation_key))
        for choice_key in temptation.compatible_choices:
            rows.append(fact("temptation_lures_choice", temptation_key, choice_key))
    for choice_key in sorted(CHOICES):
        rows.append(fact("bad_choice", choice_key))
    if params is not None:
        rows.append(fact("chosen", params.route, params.display, params.temptation, params.choice))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program())
    return set(atoms(model, "combo"))


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")
    for index, combo in enumerate(sorted(python_set), 1):
        sample = generate(
            StoryParams(
                route=combo[0],
                display=combo[1],
                temptation=combo[2],
                choice=combo[3],
                hero="Verifier",
                gender="girl",
                companion="Aunt Bea",
                seed=index,
            )
        )
        _exercise_story(sample)
    return f"OK: verified {len(python_set)} constrained mall pirate combos with ASP parity."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate shopping-mall pirate bad-ending storyworld samples.")
    parser.add_argument("--route", choices=sorted(ROUTES), default=None)
    parser.add_argument("--display", choices=sorted(DISPLAYS), default=None)
    parser.add_argument("--temptation", choices=sorted(TEMPTATIONS), default=None)
    parser.add_argument("--choice", choices=sorted(CHOICES), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--companion", choices=COMPANIONS, default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    combos = valid_combos()
    filtered = [
        combo for combo in combos
        if (args.route is None or combo[0] == args.route)
        and (args.display is None or combo[1] == args.display)
        and (args.temptation is None or combo[2] == args.temptation)
        and (args.choice is None or combo[3] == args.choice)
    ]
    if (args.route or args.display or args.temptation or args.choice) and not filtered:
        raise StoryError(
            invalid_reason(
                args.route or "<route>",
                args.display or "<display>",
                args.temptation or "<temptation>",
                args.choice or "<choice>",
            )
        )
    if not filtered:
        filtered = combos
    rng = random.Random(args.seed + index)
    combo = rng.choice(filtered)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print("\t".join(combo))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, header=f"### {' / '.join(combo)}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0

        count = max(1, args.n)
        for index in range(count):
            sample = generate(resolve_params(args, index))
            header = f"### variant {index + 1}" if count > 1 and not args.json else None
            emit(sample, args, header)
            if index != count - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
