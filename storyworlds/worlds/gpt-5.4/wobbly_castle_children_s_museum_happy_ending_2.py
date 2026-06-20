#!/usr/bin/env python3
"""
wobbly_castle_children_s_museum_happy_ending_2.py
=================================================

Seed prompt used:
    Write a story that includes the following words and narrative instruments.
    Words: wobbly castle
    Setting: children's museum
    Features: Happy Ending, Rhyme, Bravery
    Style: Nursery Rhyme

Internal source tale written from the seed:
    At Clover Clock Children's Museum, a child is chosen to carry one bright
    castle keepsake to the top of the wobbly castle exhibit. The route wiggles
    in a specific physical way, so the child pauses. A nearby helper gives a
    matching brave rhyme and safe method. The child uses that exact support,
    reaches the top, places the keepsake, and the final image shows the castle
    glowing happily because the world really changed.

This world keeps the domain small on purpose. The hero always has a concrete
object, a concrete route, and a concrete wobble to solve in a children's
museum. Bravery is not abstract here: it is embodied in the fitting move that
changes meters in the world and leads to the happy ending image.
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


MUSEUM_NAME = "Clover Clock Children's Museum"


@dataclass(frozen=True)
class Route:
    key: str
    phrase: str
    footing: str
    lookout: str
    allows_wobbles: tuple[str, ...]
    finale: str
    height_meters: float


@dataclass(frozen=True)
class Wobble:
    key: str
    phrase: str
    cause: str
    need: str
    risk: str
    tremble_meters: float


@dataclass(frozen=True)
class BraveMove:
    key: str
    phrase: str
    helper_name: str
    helper_role: str
    helper_phrase: str
    tool_phrase: str
    action: str
    chant: str
    solves: tuple[str, ...]


@dataclass(frozen=True)
class Finale:
    key: str
    carried_item: str
    goal_phrase: str
    ending_image: str
    lesson: str


@dataclass
class StoryParams:
    route: str
    wobble: str
    move: str
    finale: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    key: str
    label: str
    kind: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    summary: str


@dataclass
class World:
    params: StoryParams
    route_cfg: Route
    wobble_cfg: Wobble
    move_cfg: BraveMove
    finale_cfg: Finale
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    story: str = ""

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def add_event(self, event_id: str, summary: str) -> None:
        self.history.append(Event(event_id, summary))

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            f"  params: route={self.params.route}, wobble={self.params.wobble}, "
            f"move={self.params.move}, finale={self.params.finale}, hero={self.params.hero}"
        )
        for key, ent in self.entities.items():
            meters = ", ".join(
                f"{name}={value:g}" for name, value in sorted(ent.meters.items())
            ) or "none"
            memes = ", ".join(
                f"{name}={value:g}" for name, value in sorted(ent.memes.items())
            ) or "none"
            notes = ", ".join(
                f"{name}={value}" for name, value in sorted(ent.notes.items())
            ) or "none"
            lines.append(f"  {key}: {ent.label} ({ent.kind}) @ {ent.location or 'n/a'}")
            lines.append(f"    meters: {meters}")
            lines.append(f"    memes: {memes}")
            lines.append(f"    notes: {notes}")
        lines.append(f"  facts: {self.facts}")
        lines.append("  history:")
        for event in self.history:
            lines.append(f"    - {event.id}: {event.summary}")
        return "\n".join(lines)


ROUTES: dict[str, Route] = {
    "pillow_drawbridge": Route(
        key="pillow_drawbridge",
        phrase="the pillow drawbridge over the pretend moat",
        footing="quilted planks and a felt rope rail",
        lookout="cushion crocodiles and painted shields below",
        allows_wobbles=("shimmy",),
        finale="crown_hook",
        height_meters=0.9,
    ),
    "button_steps": Route(
        key="button_steps",
        phrase="the giant button steps beside the story tower",
        footing="round stitched pads that rise and dip",
        lookout="clockwork mice peeping from little windows",
        allows_wobbles=("bobble",),
        finale="star_slot",
        height_meters=1.0,
    ),
    "cloud_ramp": Route(
        key="cloud_ramp",
        phrase="the cloud ramp curling to the high keep window",
        footing="a silver mat and a moon-soft side rail",
        lookout="paper swallows gliding near the skylight",
        allows_wobbles=("lean",),
        finale="banner_pole",
        height_meters=1.3,
    ),
}

WOBBLES: dict[str, Wobble] = {
    "shimmy": Wobble(
        key="shimmy",
        phrase="a shimmy-shake",
        cause="the hanging planks twitched whenever a small foot landed",
        need="rope",
        risk="sitting down in the middle and feeling stuck",
        tremble_meters=0.8,
    ),
    "bobble": Wobble(
        key="bobble",
        phrase="a bobble-bounce",
        cause="the round button pads puffed upward again after every careful step",
        need="count",
        risk="trying two pads at once in a worried hurry",
        tremble_meters=0.9,
    ),
    "lean": Wobble(
        key="lean",
        phrase="a lean-and-tilt",
        cause="the ramp rose higher near the bright keep window and felt steeper there",
        need="hand",
        risk="freezing halfway under the skylight",
        tremble_meters=0.7,
    ),
}

BRAVE_MOVES: dict[str, BraveMove] = {
    "rope_rhyme": BraveMove(
        key="rope_rhyme",
        phrase="the rope-and-rhyme plan",
        helper_name="Maker May",
        helper_role="museum maker",
        helper_phrase="Maker May tapped the felt rope and smiled a quiet yes",
        tool_phrase="the felt rope rail",
        action="kept one hand on the felt rope and sang each foot to the next plank",
        chant="Hold the rope, step and hope; slow feet float, slow feet cope.",
        solves=("rope",),
    ),
    "button_count": BraveMove(
        key="button_count",
        phrase="the button-count plan",
        helper_name="Guide Lou",
        helper_role="museum guide",
        helper_phrase="Guide Lou beat a tiny drum so each landing had its turn",
        tool_phrase="a tiny drum beat and counted steps",
        action="touched each round pad once and counted every landing out loud",
        chant="One for the toe, two soft and slow, three small brave feet in a row.",
        solves=("count",),
    ),
    "window_hand": BraveMove(
        key="window_hand",
        phrase="the window-hand plan",
        helper_name="Auntie Fern",
        helper_role="careful grown-up",
        helper_phrase="Auntie Fern offered a warm hand and pointed to the bright star in the window",
        tool_phrase="a steady hand and a bright fixed star to watch",
        action="held the warm hand at the steep part and looked at the window star instead of the floor",
        chant="Hand in hand, eyes on light; little steps can climb just right.",
        solves=("hand",),
    ),
}

FINALES: dict[str, Finale] = {
    "crown_hook": Finale(
        key="crown_hook",
        carried_item="the ribbon crown",
        goal_phrase="the high hook above the drawbridge arch",
        ending_image="the ribbon crown swung from the hook while the felt moat shone blue and the whole hall clapped in time",
        lesson="Bravery stayed gentle because the child used the support that truly belonged to that path.",
    ),
    "star_slot": Finale(
        key="star_slot",
        carried_item="the silver star card",
        goal_phrase="the brass slot at the top tower table",
        ending_image="the silver star card slipped into the slot, and a ring of golden bulbs blinked around the tower mice",
        lesson="Bravery grew one count at a time, because steady rhythm was stronger than a frightened rush.",
    ),
    "banner_pole": Finale(
        key="banner_pole",
        carried_item="the moon banner",
        goal_phrase="the slim pole by the keep window",
        ending_image="the moon banner fluttered by the skylight and turned the wobbly castle pale gold from rail to roof",
        lesson="Bravery became bright because safe help and a clear place to look carried the child through the steep part.",
    ),
}

HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Nell", "Poppy", "Tess", "Mira"),
    "boy": ("Rory", "Owen", "Jude", "Milo"),
}

NEED_TEXT: dict[str, str] = {
    "rope": "a rope to steady one hand",
    "count": "counting each landing",
    "hand": "a steady hand and a calm point to watch",
}


def _pronouns(gender: str) -> tuple[str, str]:
    if gender == "boy":
        return ("he", "his")
    return ("she", "her")


def valid_combo(route_key: str, wobble_key: str, move_key: str, finale_key: str) -> bool:
    if (
        route_key not in ROUTES
        or wobble_key not in WOBBLES
        or move_key not in BRAVE_MOVES
        or finale_key not in FINALES
    ):
        return False
    route = ROUTES[route_key]
    wobble = WOBBLES[wobble_key]
    move = BRAVE_MOVES[move_key]
    finale = FINALES[finale_key]
    if wobble.key not in route.allows_wobbles:
        return False
    if wobble.need not in move.solves:
        return False
    if route.finale != finale.key:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_key in sorted(ROUTES):
        for wobble_key in sorted(WOBBLES):
            for move_key in sorted(BRAVE_MOVES):
                for finale_key in sorted(FINALES):
                    if valid_combo(route_key, wobble_key, move_key, finale_key):
                        combos.append((route_key, wobble_key, move_key, finale_key))
    return combos


def explain_rejection(
    route_key: str, wobble_key: str, move_key: str, finale_key: str
) -> str:
    if route_key not in ROUTES:
        return f"No story: unknown route {route_key!r}."
    if wobble_key not in WOBBLES:
        return f"No story: unknown wobble {wobble_key!r}."
    if move_key not in BRAVE_MOVES:
        return f"No story: unknown brave move {move_key!r}."
    if finale_key not in FINALES:
        return f"No story: unknown finale {finale_key!r}."
    route = ROUTES[route_key]
    wobble = WOBBLES[wobble_key]
    move = BRAVE_MOVES[move_key]
    finale = FINALES[finale_key]
    if wobble.key not in route.allows_wobbles:
        return f"No story: {route.phrase} does not wobble with {wobble.phrase}."
    if wobble.need not in move.solves:
        return (
            f"No story: {move.phrase} does not solve {wobble.phrase}. "
            f"This path needs help for {wobble.need!r}."
        )
    if route.finale != finale.key:
        expected = FINALES[route.finale].goal_phrase
        return f"No story: {route.phrase} leads to {expected}, not {finale.goal_phrase}."
    return "No story: that museum setup is outside this world's reasonable choices."


def params_from_combo(
    combo: tuple[str, str, str, str],
    seed: int,
    hero: str | None = None,
    gender: str | None = None,
) -> StoryParams:
    chosen_gender = gender or ("girl" if seed % 2 == 0 else "boy")
    chosen_hero = hero or HEROES[chosen_gender][seed % len(HEROES[chosen_gender])]
    return StoryParams(
        route=combo[0],
        wobble=combo[1],
        move=combo[2],
        finale=combo[3],
        hero=chosen_hero,
        gender=chosen_gender,
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    return [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.wobble is None or combo[1] == args.wobble)
        and (args.move is None or combo[2] == args.move)
        and (args.finale is None or combo[3] == args.finale)
    ]


def build_world(params: StoryParams) -> World:
    if params.gender not in HEROES:
        raise StoryError(f"No story: unknown gender group {params.gender!r}.")
    if not valid_combo(params.route, params.wobble, params.move, params.finale):
        raise StoryError(
            explain_rejection(params.route, params.wobble, params.move, params.finale)
        )

    route_cfg = ROUTES[params.route]
    wobble_cfg = WOBBLES[params.wobble]
    move_cfg = BRAVE_MOVES[params.move]
    finale_cfg = FINALES[params.finale]

    world = World(
        params=params,
        route_cfg=route_cfg,
        wobble_cfg=wobble_cfg,
        move_cfg=move_cfg,
        finale_cfg=finale_cfg,
    )
    world.entities["museum"] = Entity(
        key="museum",
        label=MUSEUM_NAME,
        kind="place",
        location="main hall",
        meters={"light": 1.0, "open": 1.0},
        memes={"wonder": 1.2, "welcome": 1.0},
        notes={"room": "castle play gallery"},
    )
    world.entities["castle"] = Entity(
        key="castle",
        label="the wobbly castle",
        kind="exhibit",
        location="castle play gallery",
        meters={
            "height": route_cfg.height_meters,
            "wobble": wobble_cfg.tremble_meters,
            "steady_path": 0.0,
            "glow": 0.0,
        },
        memes={"wonder": 1.0},
        notes={"footing": route_cfg.footing, "lookout": route_cfg.lookout},
    )
    world.entities["hero"] = Entity(
        key="hero",
        label=params.hero,
        kind=params.gender,
        location=route_cfg.phrase,
        meters={"pause": 0.0, "steps_forward": 0.0, "goal_reached": 0.0},
        memes={"fear": 1.1, "bravery": 0.6, "joy": 0.7, "wonder": 1.4},
        notes={"goal": finale_cfg.goal_phrase},
    )
    world.entities["helper"] = Entity(
        key="helper",
        label=move_cfg.helper_name,
        kind=move_cfg.helper_role,
        location=route_cfg.phrase,
        meters={"nearby": 1.0, "support": 1.0},
        memes={"calm": 1.2, "care": 1.3},
        notes={"tool": move_cfg.tool_phrase},
    )
    world.entities["item"] = Entity(
        key="item",
        label=finale_cfg.carried_item,
        kind="keepsake",
        location="hero hands",
        meters={"carried": 1.0, "placed": 0.0},
        memes={"importance": 1.0},
        notes={"destination": finale_cfg.goal_phrase},
    )
    world.entities["goal"] = Entity(
        key="goal",
        label=finale_cfg.goal_phrase,
        kind="destination",
        location=route_cfg.phrase,
        meters={"ready": 1.0, "complete": 0.0},
        memes={"gleam": 1.0},
        notes={"ending": "happy"},
    )

    world.facts["setting"] = "children's museum"
    world.facts["feature"] = "bravery"
    world.facts["style"] = "nursery rhyme"
    world.facts["need"] = wobble_cfg.need
    world.add_event(
        "arrival",
        f"{params.hero} entered {MUSEUM_NAME} and saw the wobbly castle.",
    )
    world.add_event(
        "mission",
        f"{params.hero} carried {finale_cfg.carried_item} toward {finale_cfg.goal_phrase}.",
    )
    return world


def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    castle = world.get("castle")
    item = world.get("item")
    goal = world.get("goal")

    hero.meters["pause"] = 1.0
    hero.memes["fear"] += 0.5
    world.add_event(
        "wobble",
        f"The path had {world.wobble_cfg.phrase} because {world.wobble_cfg.cause}.",
    )

    hero.memes["bravery"] += 1.1
    hero.memes["fear"] = max(0.4, hero.memes["fear"] - 0.7)
    helper.meters["support"] = 1.3
    castle.meters["steady_path"] = 1.0
    world.add_event(
        "turn",
        f"{world.move_cfg.helper_phrase}, and {world.params.hero} chose {world.move_cfg.phrase}.",
    )

    hero.meters["steps_forward"] = 3.0
    castle.meters["wobble"] = max(0.2, castle.meters["wobble"] - 0.5)
    world.add_event("crossing", f"{world.params.hero} {world.move_cfg.action}.")

    hero.meters["goal_reached"] = 1.0
    item.location = world.finale_cfg.goal_phrase
    item.meters["carried"] = 0.0
    item.meters["placed"] = 1.0
    goal.meters["complete"] = 1.0
    castle.meters["glow"] = 1.0
    hero.memes["joy"] += 1.5
    hero.memes["wonder"] += 0.4
    world.facts["ending"] = "happy"
    world.facts["change"] = "fear_to_bravery"
    world.add_event(
        "placement",
        f"{world.params.hero} placed {world.finale_cfg.carried_item} at {world.finale_cfg.goal_phrase}.",
    )
    world.add_event("ending", world.finale_cfg.ending_image)


def render_story(world: World) -> str:
    hero = world.get("hero")
    subject, possessive = _pronouns(world.params.gender)
    if hero.memes["bravery"] <= hero.memes["fear"]:
        raise StoryError("No story: the brave turn did not complete successfully.")

    opening = (
        f"At {MUSEUM_NAME}, {world.params.hero} came to the castle play gallery and found the wobbly castle. "
        f"There waited {world.route_cfg.phrase}, with {world.route_cfg.footing} and {world.route_cfg.lookout}. "
        f"In one hand {subject} carried {world.finale_cfg.carried_item} for {world.finale_cfg.goal_phrase}."
    )
    tension = (
        f"But the way ahead had {world.wobble_cfg.phrase}. "
        f"{world.wobble_cfg.cause.capitalize()}, so {world.params.hero} made a still little stop, afraid of {world.wobble_cfg.risk}. "
        f"Wobble, wobble, do not win; brave small feet may yet begin."
    )
    turn = (
        f"Then came {world.move_cfg.phrase}. {world.move_cfg.helper_phrase}. "
        f"{world.params.hero} whispered, \"{world.move_cfg.chant}\" "
        f"Then {world.params.hero} {world.move_cfg.action}. "
        f"The shaking place felt less like trouble and more like a true path through."
    )
    ending = (
        f"Step by step, {world.params.hero} reached {world.finale_cfg.goal_phrase} and set {world.finale_cfg.carried_item} in place, and {world.finale_cfg.ending_image}. "
        f"{world.finale_cfg.lesson} {world.params.hero} came back down with {possessive} smile alight, and the children's museum felt snug and bright that night."
    )
    return "\n\n".join([opening, tension, turn, ending])


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Tell a nursery-rhyme story in a children's museum where {world.params.hero} "
            f"must carry {world.finale_cfg.carried_item} through a wobbly castle."
        ),
        (
            f"The route is {world.route_cfg.phrase}, the wobble is {world.wobble_cfg.phrase}, "
            f"and the fitting brave move is {world.move_cfg.phrase}."
        ),
        (
            f"End with {world.finale_cfg.goal_phrase} and a happy final image proving that "
            f"fear changed into bravery."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    helper = world.get("helper")
    return [
        QAItem(
            question="Where does this story happen?",
            answer=(
                f"This story happens at {MUSEUM_NAME}, inside the castle play gallery. "
                f"The wobbly castle is a real museum exhibit there, so the brave problem belongs to that physical place."
            ),
        ),
        QAItem(
            question=f"What was {world.params.hero} carrying, and where did it need to go?",
            answer=(
                f"{world.params.hero} was carrying {world.finale_cfg.carried_item}. "
                f"It needed to reach {world.finale_cfg.goal_phrase}, because placing it there completes the castle's happy ending image."
            ),
        ),
        QAItem(
            question=f"Why did {world.params.hero} stop in the middle of the story?",
            answer=(
                f"{world.params.hero} stopped because the route had {world.wobble_cfg.phrase}. "
                f"{world.wobble_cfg.cause.capitalize()}, so the pause came from a real museum wobble and not from laziness."
            ),
        ),
        QAItem(
            question=f"What brave move matched the problem on the path?",
            answer=(
                f"The fitting brave move was {world.move_cfg.phrase}. "
                f"It matched the problem because the wobble needed {NEED_TEXT[world.wobble_cfg.need]}, and that is exactly what the move supplied."
            ),
        ),
        QAItem(
            question="Who helped during the hard middle, and how?",
            answer=(
                f"{helper.label} helped during the hard middle. "
                f"{world.move_cfg.helper_phrase}, and that calm support gave the child the right safe cue instead of a random cheer."
            ),
        ),
        QAItem(
            question="How can we tell the ending is both brave and happy?",
            answer=(
                f"We can tell because {world.params.hero} reaches {world.finale_cfg.goal_phrase} and places {world.finale_cfg.carried_item} there. "
                f"The final image shows that {world.finale_cfg.ending_image}, which proves the world changed after the brave choice."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is a rope rail helpful on a shaky play bridge?",
            answer=(
                "A rope rail gives one hand a steady job while the feet learn the bridge's movement. "
                "That extra contact can turn a fluttery crossing into a slower and safer one."
            ),
        ),
        QAItem(
            question="Why can counting help on bouncy steps?",
            answer=(
                "Counting gives each step a rhythm, and rhythm slows the body down. "
                "When a child stops rushing, the feet can land one at a time instead of tumbling ahead together."
            ),
        ),
        QAItem(
            question="Why might looking at one bright fixed point help on a high ramp?",
            answer=(
                "A fixed point gives the eyes something calm to follow while the body keeps moving. "
                "That can shrink the feeling of tilt, especially when a steady hand is nearby too."
            ),
        ),
        QAItem(
            question="What makes a happy ending feel earned in a bravery story?",
            answer=(
                "A happy ending feels earned when the child meets a real obstacle, chooses a fitting safe method, and then changes the world in a visible way. "
                "The joy matters more when the final image grows out of the solved physical problem."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    world.story = render_story(world)
    return StorySample(
        params=params,
        story=world.story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(R,W,M,F) :-
    route(R),
    wobble(W),
    move(M),
    finale(F),
    route_allows(R,W),
    wobble_need(W,N),
    move_solves(M,N),
    route_finale(R,F).

ok :- chosen(R,W,M,F), valid(R,W,M,F).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds import asp

    lines: list[str] = []
    for route in ROUTES.values():
        lines.append(asp.fact("route", route.key))
        for wobble in route.allows_wobbles:
            lines.append(asp.fact("route_allows", route.key, wobble))
        lines.append(asp.fact("route_finale", route.key, route.finale))
    for wobble in WOBBLES.values():
        lines.append(asp.fact("wobble", wobble.key))
        lines.append(asp.fact("wobble_need", wobble.key, wobble.need))
    for move in BRAVE_MOVES.values():
        lines.append(asp.fact("move", move.key))
        for solve in move.solves:
            lines.append(asp.fact("move_solves", move.key, solve))
    for finale in FINALES.values():
        lines.append(asp.fact("finale", finale.key))
    if params is not None:
        lines.append(
            asp.fact("chosen", params.route, params.wobble, params.move, params.finale)
        )
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None, show: str = "") -> str:
    return asp_facts(params) + ASP_RULES + ("\n" + show if show else "")


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise StoryError("Verification failed: sample is missing its live world.")
    hero = world.get("hero")
    castle = world.get("castle")
    item = world.get("item")
    goal = world.get("goal")
    story_lower = sample.story.lower()

    if "wobbly castle" not in story_lower:
        raise StoryError("Verification failed: story is missing 'wobbly castle'.")
    if "children's museum" not in story_lower:
        raise StoryError("Verification failed: story is missing 'children's museum'.")
    if sample.story.count("\n\n") < 3:
        raise StoryError("Verification failed: story should have four paragraphs.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Verification failed: unresolved template braces leaked into prose.")
    if "meters" in sample.story or "memes" in sample.story:
        raise StoryError("Verification failed: debug labels leaked into prose.")
    if "  " in sample.story:
        raise StoryError("Verification failed: doubled spaces leaked into prose.")
    if hero.meters["goal_reached"] < 1.0:
        raise StoryError("Verification failed: the child never reached the goal.")
    if item.meters["placed"] < 1.0 or goal.meters["complete"] < 1.0:
        raise StoryError("Verification failed: the keepsake was not placed at the goal.")
    if castle.meters["glow"] < 1.0:
        raise StoryError("Verification failed: the final image did not change the castle.")
    if castle.meters["steady_path"] < 1.0:
        raise StoryError("Verification failed: the safe path was never established.")
    if hero.memes["bravery"] <= hero.memes["fear"]:
        raise StoryError("Verification failed: bravery did not overtake fear.")
    if hero.memes["joy"] <= 1.0:
        raise StoryError("Verification failed: joy did not rise into a happy ending.")
    required_events = {
        "arrival",
        "mission",
        "wobble",
        "turn",
        "crossing",
        "placement",
        "ending",
    }
    present_events = {event.id for event in world.history}
    if required_events - present_events:
        raise StoryError(
            f"Verification failed: missing events {sorted(required_events - present_events)}."
        )
    if len(sample.prompts) != 3:
        raise StoryError("Verification failed: expected exactly three generation prompts.")
    if len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
        raise StoryError("Verification failed: QA sets are too thin.")
    for qa in list(sample.story_qa) + list(sample.world_qa):
        if len(qa.answer.split()) < 12:
            raise StoryError(
                f"Verification failed: answer is too short for question {qa.question!r}."
            )


def verify() -> str:
    py = sorted(valid_combos())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        raise StoryError(f"Python/ASP mismatch. only_py={only_py} only_asp={only_lp}")

    for index, combo in enumerate(py):
        sample = generate(params_from_combo(combo, 2000 + index))
        verify_sample(sample)

    return (
        f"OK: Python and ASP agree on {len(py)} valid wobbly-castle museum combinations.\n"
        f"OK: Exercised all {len(py)} generated stories with grounded QA and happy endings."
    )


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate brave nursery-rhyme stories about a wobbly castle in a children's museum."
        )
    )
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--wobble", choices=sorted(WOBBLES))
    parser.add_argument("--move", choices=sorted(BRAVE_MOVES))
    parser.add_argument("--finale", choices=sorted(FINALES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = matching_combos(args)
    if not combos:
        route_key = args.route or next(iter(ROUTES))
        wobble_key = args.wobble or next(iter(WOBBLES))
        move_key = args.move or next(iter(BRAVE_MOVES))
        finale_key = args.finale or next(iter(FINALES))
        raise StoryError(explain_rejection(route_key, wobble_key, move_key, finale_key))

    explicit = all(
        getattr(args, field) is not None for field in ("route", "wobble", "move", "finale")
    )
    seed = (args.seed if args.seed is not None else 1) + index
    chosen_gender = args.gender or rng.choice(sorted(HEROES))

    if explicit:
        params = StoryParams(
            route=args.route,
            wobble=args.wobble,
            move=args.move,
            finale=args.finale,
            hero=args.hero or HEROES[chosen_gender][seed % len(HEROES[chosen_gender])],
            gender=chosen_gender,
            seed=seed,
        )
        if not valid_combo(params.route, params.wobble, params.move, params.finale):
            raise StoryError(
                explain_rejection(params.route, params.wobble, params.move, params.finale)
            )
        return params

    combo = rng.choice(combos)
    return params_from_combo(combo, seed, hero=args.hero, gender=chosen_gender)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            route_key = args.route or next(iter(ROUTES))
            wobble_key = args.wobble or next(iter(WOBBLES))
            move_key = args.move or next(iter(BRAVE_MOVES))
            finale_key = args.finale or next(iter(FINALES))
            raise StoryError(explain_rejection(route_key, wobble_key, move_key, finale_key))
        samples: list[StorySample] = []
        for index, combo in enumerate(combos):
            params = params_from_combo(
                combo,
                (args.seed if args.seed is not None else 1) + index,
                hero=args.hero,
                gender=args.gender,
            )
            samples.append(generate(params))
        return samples

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = (args.seed if args.seed is not None else 1) + index
        params = resolve_params(args, random.Random(seed), index)
        samples.append(generate(params))
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    try:
        if args.show_asp:
            print(asp_program(show="#show valid/4.\n#show ok/0."))
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in asp_valid_combos():
                print("\t".join(combo))
            return 0

        samples = samples_from_args(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(
                    json.dumps(
                        [sample.to_dict() for sample in samples],
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = (
                    f"### route={p.route} wobble={p.wobble} move={p.move} finale={p.finale}"
                )
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
