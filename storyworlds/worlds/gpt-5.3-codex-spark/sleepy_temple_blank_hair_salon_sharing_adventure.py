#!/usr/bin/env python3
"""
sleepy_temple_blank_hair_salon_sharing_adventure.py
====================================================

Source tale
----------
A sleepy child visits the temple-themed hair salon in search of a calm adventure.
The child gets a blank style sheet, then must help a friend complete a wobbly
"adventure braiding" route through the salon. The object needed for the route is
in one person’s hands, so the sleepy child and friend share it and switch roles.
By passing it back and forth, they cross the final mirror bridge and leave with
hair that proves the team solved the route together.

This world keeps the state explicit:
- physical meters track energy, focus, and steadiness,
- emotional memes track trust, courage, fatigue, and joy,
- story flow follows premise -> tension -> shared turn -> resolution,
- and the ending image is derived from those final traces.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
STORYWORLDS = Path(__file__).resolve().parents[2]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

SALON_NAME = "Temple Tide Hair Salon"


@dataclass(frozen=True)
class Route:
    key: str
    display: str
    open_line: str
    start_zone: str
    obstacle: str
    clue_zone: str
    finish_zone: str
    ending_image: str
    allowed_tools: tuple[str, ...]
    pace_boost: float
    tension_spike: float


@dataclass(frozen=True)
class ShareTool:
    key: str
    display: str
    phrase: str
    helpful_for: str
    trust_gain: float
    focus_gain: float
    sleep_calming: float
    share_phrase: str


@dataclass(frozen=True)
class HeroTemplate:
    key: str
    first_names: tuple[str, ...]


@dataclass(frozen=True)
class StoryParams:
    route: str
    tool: str
    hero: str
    gender: str
    friend: str
    seed: int | None = None


@dataclass
class Entity:
    key: str
    label: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    stage: str
    location: str
    summary: str
    cause: str
    consequence: str


@dataclass
class World:
    params: StoryParams
    route: Route
    tool: ShareTool
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    blank_board_visible: bool = False
    shared: bool = False
    resolved: bool = False
    final_image: str = ""
    setup_reason: str = ""
    share_explanation: str = ""
    story: str = ""

    def hero(self) -> Entity:
        return self.entities["hero"]

    def friend(self) -> Entity:
        return self.entities["friend"]

    def stylist(self) -> Entity:
        return self.entities["stylist"]

    def object(self) -> Entity:
        return self.entities["share_object"]

    def add_event(self, stage: str, location: str, summary: str, cause: str, consequence: str) -> None:
        self.events.append(Event(stage, location, summary, cause, consequence))

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  salon: {SALON_NAME}")
        lines.append(f"  route={self.route.key}, tool={self.tool.key}")
        lines.append(f"  blank_board_visible={self.blank_board_visible}, shared={self.shared}, resolved={self.resolved}")
        for entity in self.entities.values():
            lines.append(f"  {entity.key}: {entity.label} ({entity.kind}) @ {entity.location}")
            meters = ", ".join(f"{k}={v:.2f}" for k, v in sorted(entity.meters.items())) or "none"
            memes = ", ".join(f"{k}={v:.2f}" for k, v in sorted(entity.memes.items())) or "none"
            inv = ", ".join(entity.inventory) or "none"
            notes = ", ".join(f"{k}={v}" for k, v in sorted(entity.notes.items())) or "none"
            lines.append(f"    meters=[{meters}]")
            lines.append(f"    memes=[{memes}]")
            lines.append(f"    inventory=[{inv}]")
            lines.append(f"    notes=[{notes}]")
        lines.append("  events:")
        for event in self.events:
            lines.append(f"    - {event.stage} @ {event.location}: {event.summary} (cause={event.cause}; consequence={event.consequence})")
        return "\n".join(lines)


ROUTES: dict[str, Route] = {
    "ribbon_river": Route(
        key="ribbon_river",
        display="Ribbon River",
        open_line=(
            "A narrow ribbon bridge crossed the central salon hall, lit by tiny temple bells and misty lamps. "
            "The floor felt soft beneath small, careful feet."
        ),
        start_zone="the temple check-in circle",
        obstacle="hanging row of warm curls that moved whenever someone shifted too fast",
        clue_zone="the mirror cave by the river bridge",
        finish_zone="the bright bell window",
        ending_image="{hero} and {friend} stepped out of Temple Tide Hair Salon with matching star braids and steady, proud smiles.",
        allowed_tools=("blank_style_board", "mirror_glide_stand"),
        pace_boost=0.14,
        tension_spike=0.20,
    ),
    "echo_stair": Route(
        key="echo_stair",
        display="Echo Stair",
        open_line=(
            "A spiraling stair of low stools climbed past reflective glass and soft chimes. "
            "Every step answered with an echo that made sleepy hands want to stop."
        ),
        start_zone="the sleepy stair entry",
        obstacle="section where the stool turns dipped and felt too smooth for tired balance",
        clue_zone="the chalk station under a glowing temple arch",
        finish_zone="the dawn mirror ledge",
        ending_image="{hero} and {friend} reached the dawn mirror ledge together, and {hero}'s sleepy eyes looked bright again.",
        allowed_tools=("blank_style_board", "ribbon_lock_combs"),
        pace_boost=0.12,
        tension_spike=0.23,
    ),
    "lantern_path": Route(
        key="lantern_path",
        display="Lantern Path",
        open_line=(
            "A lantern lane threaded from shampoo caves to a tall temple frame. "
            "The route glimmered, but the final bend required steady timing."
        ),
        start_zone="the steam entrance",
        obstacle="sleepy spin of cape cloth near the finish ring",
        clue_zone="the warm cape rack under the top lanterns",
        finish_zone="the silver rinse mirror",
        ending_image="{hero} and {friend} stood at the silver rinse mirror, hair shining like dawn, and the salon looked like an answered quest.",
        allowed_tools=("mirror_glide_stand", "ribbon_lock_combs"),
        pace_boost=0.16,
        tension_spike=0.21,
    ),
}

TOOLS: dict[str, ShareTool] = {
    "blank_style_board": ShareTool(
        key="blank_style_board",
        display="Blank Style Board",
        phrase="blank style board",
        helpful_for="drawing the next braid step while one hand steadied the other",
        trust_gain=0.20,
        focus_gain=0.22,
        sleep_calming=0.15,
        share_phrase="both of them held the board together, one tracing while the other followed in rhythm",
    ),
    "mirror_glide_stand": ShareTool(
        key="mirror_glide_stand",
        display="Mirror-Glide Stand",
        phrase="mirror-glide stand",
        helpful_for="sharing both the rear view and the front view at the same moment",
        trust_gain=0.18,
        focus_gain=0.18,
        sleep_calming=0.10,
        share_phrase="a stand swapped from one friend to the other at the hardest bend",
    ),
    "ribbon_lock_combs": ShareTool(
        key="ribbon_lock_combs",
        display="Pair of Twin Ribbon Combs",
        phrase="pair of twin ribbon combs",
        helpful_for="locking one side of the braid while the other side rested",
        trust_gain=0.15,
        focus_gain=0.16,
        sleep_calming=0.12,
        share_phrase="the twin combs passed through small hands, then back again after each turn",
    ),
}

HERO_TEMPLATES: dict[str, HeroTemplate] = {
    "boy": HeroTemplate(key="boy", first_names=("Kai", "Eli", "Nico", "Toma", "Rin")),
    "girl": HeroTemplate(key="girl", first_names=("Mina", "Lena", "Nora", "Pia", "Aya")),
}

FRIENDS: tuple[str, ...] = ("Jules", "Amir", "Miko", "Rae", "Sana")


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combos() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for route in ROUTES.values():
        for tool in route.allowed_tools:
            rows.append((route.key, tool))
    return sorted(rows)


def describe_rejection(route_key: str, tool_key: str) -> str:
    if route_key not in ROUTES:
        raise StoryError(f"Unknown route '{route_key}'. Choose from: {', '.join(sorted(ROUTES))}.")
    if tool_key not in TOOLS:
        raise StoryError(f"Unknown share tool '{tool_key}'. Choose from: {', '.join(sorted(TOOLS))}.")
    route = ROUTES[route_key]
    if tool_key not in route.allowed_tools:
        return (
            f"Route '{route.display}' cannot use {TOOLS[tool_key].display}. "
            f"Allowed tools are {', '.join(route.allowed_tools)}."
        )
    return f"Unknown route-tool combination: {route_key}, {tool_key}."


def build_world(params: StoryParams) -> World:
    if (params.route, params.tool) not in valid_combos():
        raise StoryError(describe_rejection(params.route, params.tool))

    route = ROUTES[params.route]
    tool = TOOLS[params.tool]
    world = World(params=params, route=route, tool=tool)

    hero = Entity(
        key="hero",
        label=params.hero,
        kind="sleepy child adventurer",
        location=route.start_zone,
        meters={"focus": 0.44, "energy": 0.55, "steadiness": 0.38, "sleepiness": 0.76},
        memes={"trust": 0.48, "courage": 0.52, "worry": 0.41, "joy": 0.31, "fatigue": 0.33},
        inventory=[],
        notes={"goal": route.finish_zone, "hero_mood": "sleepy"},
    )
    friend = Entity(
        key="friend",
        label=params.friend,
        kind="helper friend",
        location=route.start_zone,
        meters={"focus": 0.58, "energy": 0.66, "steadiness": 0.55},
        memes={"trust": 0.61, "care": 0.74, "joy": 0.40},
        inventory=[],
        notes={"help_role": "steadying partner"},
    )
    stylist = Entity(
        key="stylist",
        label="Mara",
        kind="hair-salon stylist",
        location="the styling desk",
        meters={"focus": 0.80, "energy": 0.78, "precision": 0.85},
        memes={"patience": 0.88, "kindness": 0.93, "joy": 0.52},
        inventory=["temple comb brush", "needle thread clip"],
        notes={"tone": "calm"},
    )
    share_object = Entity(
        key="share_object",
        label=tool.display,
        kind="shared tool",
        location=route.start_zone,
        meters={"wear": 0.10},
        memes={"helpfulness": 0.70},
        inventory=[],
        notes={"used_for": tool.helpful_for},
    )

    world.entities = {ent.key: ent for ent in (hero, friend, stylist, share_object)}
    return world


def _simulate(world: World) -> None:
    hero = world.hero()
    friend = world.friend()
    stylist = world.stylist()
    obj = world.object()
    subject = _pronouns(world.params.gender)[1]

    hero.location = world.route.start_zone
    world.blank_board_visible = True
    world.setup_reason = (
        f"A blank style board sat on the counter, and {hero.label} promised to finish a salon quest before nap-time."
    )
    hero.inventory.append("blank style board")
    stylist.location = world.route.start_zone
    friend.location = world.route.start_zone
    world.add_event(
        "beginning",
        world.route.start_zone,
        f"{hero.label} entered {SALON_NAME} with a sleepy face and a mission from the temple map card.",
        "The open route was designed as a small adventure through the hair temple.",
        "A blank style board appeared at the counter as the starting clue.",
    )

    hero.memes["worry"] += 0.16
    hero.memes["fatigue"] += 0.12
    hero.meters["steadiness"] -= 0.09
    hero.meters["focus"] -= 0.10
    world.add_event(
        "tension",
        world.route.clue_zone,
        f"At {world.route.clue_zone}, {hero.label} first felt {subject} hands shake on the obstacle: {world.route.obstacle}.",
        f"A sleepy rush raised stress and the route narrowed at the turning point.",
        f"The pair had to slow down and turn sharing into a plan instead of a race.",
    )

    # Shared action turn.
    hero.location = world.route.clue_zone
    friend.location = world.route.clue_zone
    obj.location = world.route.clue_zone
    hero.inventory = [item for item in hero.inventory if item != "blank style board"]
    hero.inventory.append(world.tool.phrase)
    friend.inventory.append(world.tool.phrase)
    hero.memes["worry"] -= 0.21
    hero.memes["trust"] += world.tool.trust_gain
    hero.memes["courage"] += 0.17
    hero.memes["joy"] += 0.13
    hero.memes["fatigue"] = max(0.0, hero.memes["fatigue"] - 0.10)
    hero.meters["sleepiness"] = max(0.0, hero.meters["sleepiness"] - world.tool.sleep_calming)
    hero.meters["focus"] += world.route.pace_boost + world.tool.focus_gain
    hero.meters["steadiness"] += 0.12
    hero.meters["energy"] -= 0.04

    friend.memes["care"] = friend.memes.get("care", 0.0) + 0.12
    friend.memes["trust"] += 0.12
    friend.meters["focus"] += 0.09
    friend.meters["steadiness"] += 0.08
    world.shared = True
    world.share_explanation = world.tool.share_phrase
    world.add_event(
        "shared_turn",
        world.route.clue_zone,
        f"{hero.label} and {friend.label} shared {obj.label} and used it together: {world.share_explanation}.",
        f"The route demanded two points of view at once on {world.route.obstacle}.",
        "The shared action lowered the fear of getting stuck and restored rhythm.",
    )

    # Resolution.
    hero.location = world.route.finish_zone
    friend.location = world.route.finish_zone
    stylist.location = world.route.finish_zone
    obj.location = "stylist desk"
    hero.memes["trust"] += 0.14
    hero.memes["joy"] += 0.27
    hero.memes["courage"] += 0.11
    hero.meters["steadiness"] += 0.16
    hero.meters["focus"] += 0.06
    hero.meters["sleepiness"] = max(0.0, hero.meters["sleepiness"] - 0.10)
    hero.meters["energy"] += 0.04
    stylings = (
        f"{hero.label} and {friend.label} finished the braid path through {world.route.display}, "
        f"used the shared {world.tool.phrase}, and kept checking the final mirror together."
    )
    world.final_image = world.route.ending_image.format(hero=hero.label, friend=friend.label)
    world.resolved = True
    world.add_event(
        "ending",
        world.route.finish_zone,
        stylings,
        f"They solved the obstacle by making the route into a two-person check-in challenge.",
        f"{world.final_image}",
    )


def _sleepy_phrase(world: World) -> str:
    level = world.hero().meters["sleepiness"]
    if level > 0.60:
        return "very sleepy"
    if level > 0.30:
        return "somewhat sleepy"
    return "brightly awake"


def _courage_phrase(world: World) -> str:
    courage = world.hero().memes["courage"]
    if courage > 0.90:
        return "steady and fearless"
    if courage > 0.75:
        return "steady and brave"
    return "trying but careful"


def render_story(world: World) -> str:
    hero = world.hero()
    friend = world.friend()
    _, poss, obj = _pronouns(world.params.gender)
    opening = (
        f"At {SALON_NAME}, a temple-like hair salon with bright arches and soft steam, "
        f"{hero.label} came in while feeling { _sleepy_phrase(world) }. "
        f"The station on the counter showed a blank style board, and {hero.label} wanted a bold but gentle adventure. "
        f"{world.route.open_line}"
    )

    middle = (
        f"{hero.label} was directed to {world.route.start_zone}, where the adventure for the {world.route.display} route began. "
        f"At the first turning, {hero.label} nearly paused in the middle of the {world.route.obstacle} because {poss} hands were sleepy. "
        f"Then {friend.label} pointed to the {world.tool.phrase} and offered a sharing plan. "
        f"They moved slowly, one side checking the front reflection, the other holding the shared {world.tool.display}, and each step became safer than the last."
    )

    ending = (
        f"Once they reached {world.route.finish_zone}, {hero.label} crossed the final stretch using the same shared rhythm. "
        f"Now {hero.label} felt { _courage_phrase(world) }, and the sleepy wave had turned into alert excitement. "
        f"{world.final_image} "
        f"The final image is the proof that sharing changed the route from a risky wobble into a win together."
    )

    return "\n\n".join([opening, middle, ending])


def build_prompts(world: World) -> list[str]:
    hero = world.hero().label
    return [
        "Write a child-facing Adventure story with a clear beginning, a tense middle, and an ending image.",
        f"Set the action in a hair salon and include the word 'sleepy' in the opening situation.",
        f"Show how {hero} shares a tool with a friend and turns a temple-style route into success.",
    ]


def build_story_qa(world: World) -> list[QAItem]:
    hero = world.hero().label
    friend = world.friend().label
    return [
        QAItem(
            question=f"Why did {hero} feel shaky at the start of the adventure?",
            answer=(
                f"{hero} had a high sleepiness meter and low steadiness when arriving at the salon, so the first turn with moving curls felt uncertain. "
                f"The route created one risky moment, so the body had to choose slow steps instead of hasty ones first."
            ),
        ),
        QAItem(
            question="What was the blank style board used for?",
            answer=(
                f"The blank style board worked as a shared planning target, showing where the next braid step belonged while everyone moved through the temple route. "
                f"It did not hold all the style by itself, but it gave {hero} and {friend} a concrete checkpoint after each move."
            ),
        ),
        QAItem(
            question=f"How did {hero} and {friend} use sharing to solve the obstacle?",
            answer=(
                f"They kept the same {world.tool.phrase} at the tricky bend and passed it between them in a rhythm, so one person checked the reflection while the other guided the braid. "
                f"That shared method reduced the risk of a miss and kept the route moving instead of stopping."
            ),
        ),
        QAItem(
            question=f"How did the shared action change {hero}'s emotional state?",
            answer=(
                f"The shared sequence increased {hero}'s trust and courage and lowered worry and sleepiness enough for steadier hands. "
                f"With each passed step, the adventure turned from 'I might fail' into 'we can finish this together.'"
            ),
        ),
        QAItem(
            question="What is proven by the ending image?",
            answer=(
                f"The final image shows both {hero} and {friend} at the same finishing mirror zone with matching, confident braids, not a tense or messy end. "
                f"That visual change is the trace result of the shared tool strategy succeeding after the obstacle."
            ),
        ),
    ]


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is a blank style board useful in a children story adventure?",
            answer=(
                f"A blank style board gives a low-pressure plan target at the start and keeps choices focused while the route changes. "
                f"Because it begins as blank, each step can be filled by real actions instead of guessing what is expected."
            ),
        ),
        QAItem(
            question="How can sharing a tool help with a risky point in a cooperative setting?",
            answer=(
                f"Sharing turns a single-resource bottleneck into a cooperative pattern with a clear handoff rhythm. "
                f"That lets one participant carry the current task while the other watches for balance, improving safety and success."
            ),
        ),
        QAItem(
            question="What makes the temple framing important in this world?",
            answer=(
                f"The salon is described as temple-like to make the route feel ceremonial and navigable, like a mini quest with defined stations. "
                f"Each station changes location and action state, which is why the world model tracks both place and meters as the story advances."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _simulate(world)
    world.story = render_story(world)
    return StorySample(
        params=params,
        story=world.story,
        prompts=build_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["--- prompts ---"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("--- story qa ---")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    lines.append("--- world qa ---")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n" + sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sleepy temple hair salon sharing adventure world.")
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--tool", dest="tool", choices=sorted(TOOLS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_TEMPLATES))
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError(describe_rejection(args.route or "ribbon_river", args.tool or "blank_style_board"))

    route_key, tool_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_TEMPLATES))
    hero = args.hero or rng.choice(HERO_TEMPLATES[gender].first_names)
    friend_candidates = [name for name in FRIENDS if name != hero]
    if not friend_candidates:
        raise StoryError("No helper friend options remain after removing the hero name.")
    friend = args.friend or rng.choice(friend_candidates)
    if args.friend and args.friend not in FRIENDS:
        raise StoryError(f"Unknown friend '{args.friend}'. Choose from: {', '.join(FRIENDS)}.")
    if friend == hero:
        raise StoryError("Friend and hero must be different people.")

    return StoryParams(
        route=route_key,
        tool=tool_key,
        hero=hero,
        gender=gender,
        friend=friend,
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
route(ribbon_river). route(echo_stair). route(lantern_path).
share_tool(blank_style_board). share_tool(mirror_glide_stand). share_tool(ribbon_lock_combs).

route_allows_tool(ribbon_river, blank_style_board).
route_allows_tool(ribbon_river, mirror_glide_stand).
route_allows_tool(echo_stair, blank_style_board).
route_allows_tool(echo_stair, ribbon_lock_combs).
route_allows_tool(lantern_path, mirror_glide_stand).
route_allows_tool(lantern_path, ribbon_lock_combs).

valid_combo(R, T) :-
  route(R),
  share_tool(T),
  route_allows_tool(R, T).

#show valid_combo/2.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for route in ROUTES.values():
        rows.append(asp.fact("route", route.key))
        for tool in route.allowed_tools:
            rows.append(asp.fact("route_allows_tool", route.key, tool))
    for tool in TOOLS:
        rows.append(asp.fact("share_tool", tool))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            route=combo[0],
            tool=combo[1],
            hero="Mina",
            gender="girl",
            friend="Jules",
            seed=1200 + i,
        )
        sample = generate(params)
        if sample.world is None:
            problems.append(f"{combo}: no world in generated sample")
            continue
        story = sample.story.lower()
        world = sample.world

        for required in ("sleepy", "temple", "blank"):
            if required not in story:
                problems.append(f"{combo}: generated story is missing required word '{required}'")

        if story.count("\n\n") < 2:
            problems.append(f"{combo}: story does not have clear beginning-middle-ending structure")

        if world.final_image.lower() not in story:
            problems.append(f"{combo}: ending image from state is not present in story output")

        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA too small")

        if not world.resolved:
            problems.append(f"{combo}: world did not resolve")

        if world.share_explanation == "":
            problems.append(f"{combo}: share explanation is missing")

        if any(a.answer.count(".") < 2 for a in sample.story_qa):
            problems.append(f"{combo}: a story QA answer is too short")

    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("Mismatch between Python and ASP valid_combo gates.")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    issues = exercise_generated_stories()
    if issues:
        print("Story exercise failures:")
        for item in issues:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass structure, word, and QA checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    attempts = 0
    seen: set[str] = set()
    target = max(1, args.n)

    while len(samples) < target and attempts < target * 30:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed), index=attempts)
        params = StoryParams(
            route=params.route,
            tool=params.tool,
            hero=params.hero,
            gender=params.gender,
            friend=params.friend,
            seed=seed,
        )
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)

    if len(samples) < target:
        raise StoryError("Not enough unique stories with the selected constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 777
    for i, (route_key, tool_key) in enumerate(valid_combos()):
        gender = args.gender or "girl"
        hero = args.hero or HERO_TEMPLATES[gender].first_names[0]
        friend = args.friend or FRIENDS[0]
        if friend == hero:
            friend = FRIENDS[1]
        params = StoryParams(
            route=route_key,
            tool=tool_key,
            hero=hero,
            gender=gender,
            friend=friend,
            seed=base_seed + i,
        )
        samples.append(generate(params))
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return 0

    if args.verify:
        return asp_verify()

    if args.asp:
        for row in asp_valid_combos():
            print("\t".join(row))
        return 0

    try:
        samples = _sample_all(args) if args.all else _sample_n(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                params = sample.params
                header = f"### route={params.route} tool={params.tool}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
