#!/usr/bin/env python3
"""
sesame_repetition_curiosity_rhyming_story.py
============================================

A small StoryWorld for the seed:

    words: sesame
    features: Repetition, Curiosity
    style: Rhyming Story

Internal source tale:
    A child notices sesame seeds making the same tiny clue again and again near
    a cozy snack spot. Instead of sweeping the mess away, the child grows
    curious, matches a gentle rhyme to the clue, and discovers the small hidden
    reason for the repeated sesame pattern. The ending image proves the place
    changed from puzzling and scattered to calm and cared-for.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class SnackSpot:
    key: str
    phrase: str
    landmark: str
    support_keys: tuple[str, ...]
    surface_height_cm: float
    ending_view: str


@dataclass(frozen=True)
class HiddenThing:
    key: str
    phrase: str
    support_key: str
    allowed_spots: tuple[str, ...]
    hiding_spot: str
    cause: str
    recovery: str
    proof_image: str
    lesson: str


@dataclass(frozen=True)
class SearchStyle:
    key: str
    phrase: str
    chant: str
    action: str
    tool: str
    solves: tuple[str, ...]


@dataclass
class StoryParams:
    spot: str
    hidden: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    spot: SnackSpot
    hidden: HiddenThing
    method: SearchStyle
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    opening_text: str = ""
    clue_text: str = ""
    turn_text: str = ""
    ending_text: str = ""
    story: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"spot={self.spot.key} hidden={self.hidden.key} method={self.method.key} "
            f"hero={self.params.hero} helper={self.params.helper}"
        )
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {name:<10} ({ent.kind:<12}) {detail}".rstrip())
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


SPOTS: dict[str, SnackSpot] = {
    "blue_step": SnackSpot(
        key="blue_step",
        phrase="the blue bakery step by the warm door",
        landmark="a striped mat and a low bread basket",
        support_keys=("trail",),
        surface_height_cm=14.0,
        ending_view="the blue step looked tidy, and the striped mat lay flat in the afternoon light",
    ),
    "window_box": SnackSpot(
        key="window_box",
        phrase="the window box under the red awning",
        landmark="mint leaves beside a little tin scoop",
        support_keys=("tap",),
        surface_height_cm=92.0,
        ending_view="the window box sat still, and the mint leaves swayed with no tiny clicking sound",
    ),
    "tea_table": SnackSpot(
        key="tea_table",
        phrase="the round tea table under the plum tree",
        landmark="a folded napkin beside a jam jar",
        support_keys=("ring",),
        surface_height_cm=58.0,
        ending_view="the tea table shone clean, with the napkin smooth beside the jam jar",
    ),
    "clay_pot": SnackSpot(
        key="clay_pot",
        phrase="the clay pot by the garden gate",
        landmark="soft soil and a small wooden spoon",
        support_keys=("glint",),
        surface_height_cm=36.0,
        ending_view="the clay pot rested neatly by the gate, with the spoon set straight beside the soil",
    ),
}

HIDDEN_THINGS: dict[str, HiddenThing] = {
    "seed_packet": HiddenThing(
        key="seed_packet",
        phrase="a paper packet of sesame seeds",
        support_key="trail",
        allowed_spots=("blue_step",),
        hiding_spot="behind the edge of the mat",
        cause="a torn seed packet had slipped behind the mat and kept letting a tiny sesame trail escape",
        recovery="followed the sesame line, lifted the mat edge, and tucked the little packet into safe hands",
        proof_image="The paper packet sat in a blue bowl, and every sesame seed stayed still and trim.",
        lesson="A repeated little trail can become a true answer when curiosity follows it gently.",
    ),
    "tin_chime": HiddenThing(
        key="tin_chime",
        phrase="a tiny tin chime",
        support_key="tap",
        allowed_spots=("window_box",),
        hiding_spot="under the mint leaves",
        cause="loose sesame seeds kept tapping a tucked-away tin chime whenever the breeze tipped them down",
        recovery="listened between the taps, parted the mint leaves, and lifted out the tiny chime",
        proof_image="The tin chime hung by the awning, quiet and bright in the late-day light.",
        lesson="When a sound repeats in the same small place, patient listening can turn it into a map.",
    ),
    "sesame_cookie": HiddenThing(
        key="sesame_cookie",
        phrase="a round sesame cookie",
        support_key="ring",
        allowed_spots=("tea_table",),
        hiding_spot="inside a folded napkin",
        cause="a wrapped cookie kept leaving a neat ring of sesame seeds each time the cloth fluttered in the breeze",
        recovery="held the cloth still, opened the fold, and found the warm round cookie inside",
        proof_image="The sesame cookie rested on a plate by the plum tree, whole and warm for all to see.",
        lesson="Calm curiosity sees patterns that hurried hands would only scatter.",
    ),
    "gold_button": HiddenThing(
        key="gold_button",
        phrase="a gold coat button",
        support_key="glint",
        allowed_spots=("clay_pot",),
        hiding_spot="under a light dusting of sesame seeds by the clay pot",
        cause="a lost gold button blinked beside the clay pot whenever the sun slid across the sesame dust",
        recovery="brushed the seeds in soft strokes until the bright button winked free",
        proof_image="The gold button shone in a little saucer by the gate, and the clay pot stood tidy and straight.",
        lesson="Looking twice at a steady gleam can reveal what fast sweeping would hide.",
    ),
}

METHODS: dict[str, SearchStyle] = {
    "trace_trace_tread": SearchStyle(
        key="trace_trace_tread",
        phrase="a trace-and-tread search",
        chant="Trace, trace, tread; follow where the sesame led.",
        action="followed the sesame marks one tiny step at a time",
        tool="careful eyes",
        solves=("trail",),
    ),
    "hush_hush_tap": SearchStyle(
        key="hush_hush_tap",
        phrase="a hush-and-tap search",
        chant="Hush, hush, tap; tiny sounds can draw a map.",
        action="grew quiet, counted the taps, and reached in only when the place felt clear",
        tool="quiet ears",
        solves=("tap",),
    ),
    "circle_circle_still": SearchStyle(
        key="circle_circle_still",
        phrase="a circle-and-still search",
        chant="Circle, circle, still; wait and watch until you will.",
        action="cupped the cloth or soil so the sesame ring would stop fluttering away",
        tool="steady hands",
        solves=("ring",),
    ),
    "brush_brush_blink": SearchStyle(
        key="brush_brush_blink",
        phrase="a brush-and-blink search",
        chant="Brush, brush, blink; look twice, then stop and think.",
        action="brushed the sesame dust aside in gentle lines until the hidden gleam could wink",
        tool="a soft napkin",
        solves=("glint",),
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Poppy", "Tess"),
    "boy": ("Eli", "Noah", "Jude"),
}

HELPERS: dict[str, str] = {
    "baker_nia": "Baker Nia",
    "grandpa_joel": "Grandpa Joel",
    "aunt_lark": "Aunt Lark",
}


def helper_name(key: str) -> str:
    return HELPERS[key]


def valid_combo(spot: str, hidden: str, method: str) -> bool:
    if spot not in SPOTS or hidden not in HIDDEN_THINGS or method not in METHODS:
        return False
    hidden_item = HIDDEN_THINGS[hidden]
    need = hidden_item.support_key
    return (
        spot in hidden_item.allowed_spots
        and need in SPOTS[spot].support_keys
        and need in METHODS[method].solves
    )


def explain_rejection(spot: str, hidden: str, method: str) -> str:
    if spot not in SPOTS:
        return f"No story: unknown sesame spot {spot!r}."
    if hidden not in HIDDEN_THINGS:
        return f"No story: unknown hidden sesame object {hidden!r}."
    if method not in METHODS:
        return f"No story: unknown sesame search method {method!r}."
    need = HIDDEN_THINGS[hidden].support_key
    if need not in SPOTS[spot].support_keys:
        return (
            f"No story: {SPOTS[spot].phrase} cannot ground {HIDDEN_THINGS[hidden].phrase}; "
            f"that mystery needs a {need} clue."
        )
    if spot not in HIDDEN_THINGS[hidden].allowed_spots:
        return (
            f"No story: {HIDDEN_THINGS[hidden].phrase} does not belong at {SPOTS[spot].phrase}; "
            f"that hidden object only fits {', '.join(SPOTS[key].phrase for key in HIDDEN_THINGS[hidden].allowed_spots)}."
        )
    if need not in METHODS[method].solves:
        return (
            f"No story: {METHODS[method].phrase} does not fit {HIDDEN_THINGS[hidden].phrase}; "
            f"try a method that can read a {need} clue."
        )
    return "No story: the sesame choices do not make a reasonable tale."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spot in sorted(SPOTS):
        for hidden in sorted(HIDDEN_THINGS):
            for method in sorted(METHODS):
                if valid_combo(spot, hidden, method):
                    combos.append((spot, hidden, method))
    return combos


def _pick_hero(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES[gender])


def build_world(params: StoryParams) -> World:
    spot = SPOTS[params.spot]
    hidden = HIDDEN_THINGS[params.hidden]
    method = METHODS[params.method]
    hero = Entity(name=params.hero, kind="child")
    sesame = Entity(name="Sesame", kind="seed_cluster")
    place = Entity(name="Spot", kind="place")
    secret = Entity(name=hidden.phrase, kind="hidden_object")
    helper = Entity(name=helper_name(params.helper), kind="helper")
    world = World(
        params=params,
        spot=spot,
        hidden=hidden,
        method=method,
        entities={
            "Hero": hero,
            "Sesame": sesame,
            "Spot": place,
            "Hidden": secret,
            "Helper": helper,
        },
    )
    place.set_meter("surface_height_cm", spot.surface_height_cm)
    place.set_tag("landmark", spot.landmark)
    sesame.set_meter("repeat_count", 0.0)
    sesame.set_meter("scatter_level", 1.0)
    sesame.set_tag("pattern", hidden.support_key)
    secret.set_meter("found", 0.0)
    secret.set_tag("spot", hidden.hiding_spot)
    return world


def _r_open_with_curiosity(world: World) -> bool:
    hero = world.entities["Hero"]
    sesame = world.entities["Sesame"]
    place = world.entities["Spot"]

    hero.add_meme("curiosity", 1.0)
    hero.add_meme("care", 0.4)
    hero.add_meter("steps_m", 1.4)
    sesame.add_meme("mystery", 0.9)
    place.add_meme("warmth", 0.8)
    place.add_meme("puzzle", 0.7)

    world.opening_text = (
        f"At {world.spot.phrase}, {world.params.hero} saw sesame seeds skitter, glitter, and spread. "
        f"Yet the little seeds did not tumble everywhere; they kept gathering near {world.spot.landmark} instead."
    )
    world.note(
        f"{world.params.hero} noticed that the sesame seeds kept returning to the same small place at {world.spot.phrase}."
    )
    return True


def _r_repeat_the_clue(world: World) -> bool:
    hero = world.entities["Hero"]
    sesame = world.entities["Sesame"]
    secret = world.entities["Hidden"]

    hero.add_meme("curiosity", 0.8)
    hero.add_meme("patience", 0.5)
    sesame.set_meter("repeat_count", 3.0)
    sesame.add_meter("scatter_level", 0.7)
    secret.set_tag("cause", world.hidden.cause)

    if world.hidden.support_key == "trail":
        clue = "Three times the sesame seeds made the same tiny trail, as neat as a stitched-up tale."
        action = "trail, trail, trail"
    elif world.hidden.support_key == "tap":
        clue = "Three times the sesame seeds gave a soft tin tick, quick and slick, then quick."
        action = "tap, tap, tap"
    elif world.hidden.support_key == "ring":
        clue = "Three times the sesame seeds settled in a round little ring, as if the air had learned to sing."
        action = "ring, ring, ring"
    else:
        clue = "Three times the sesame seeds flashed one bright blink, then waited for a child to stop and think."
        action = "blink, blink, blink"

    sesame.set_tag("repeat_action", action)
    world.clue_text = (
        f"{clue} {world.params.hero} did not brush them away at once. "
        f"Instead, {world.params.hero} whispered, \"If the sesame repeats, maybe it means to teach.\""
    )
    world.note(world.clue_text)
    return True


def _r_match_gentle_method(world: World) -> bool:
    hero = world.entities["Hero"]
    sesame = world.entities["Sesame"]
    place = world.entities["Spot"]
    secret = world.entities["Hidden"]
    helper = world.entities["Helper"]

    hero.add_meme("curiosity", 0.5)
    hero.add_meme("confidence", 0.8)
    hero.add_meme("patience", 0.9)
    hero.add_meter("search_loops", 3.0)
    sesame.add_meme("order", 1.0)
    sesame.set_meter("scatter_level", 0.2)
    place.add_meme("puzzle", -0.5)
    place.add_meme("calm", 1.1)
    secret.set_meter("found", 1.0)
    secret.set_tag("recovery", world.hidden.recovery)
    secret.set_tag("proof_image", world.hidden.proof_image)
    helper.add_meme("approval", 0.8)

    world.turn_text = (
        f"So {world.params.hero} tried {world.method.phrase}. "
        f"\"{world.method.chant}\" came once, then twice, then thrice, while {world.params.hero} {world.method.action}. "
        f"That gentle turn mattered because {world.hidden.cause}, and soon {world.params.hero} {world.hidden.recovery}."
    )
    world.note(world.turn_text)
    return True


def _r_close_with_proof(world: World) -> bool:
    hero = world.entities["Hero"]
    sesame = world.entities["Sesame"]
    place = world.entities["Spot"]
    secret = world.entities["Hidden"]
    helper = world.entities["Helper"]

    hero.add_meme("joy", 1.0)
    hero.add_meme("wonder", 0.7)
    sesame.set_meter("scatter_level", 0.0)
    sesame.add_meme("rest", 1.0)
    place.add_meme("warmth", 0.4)
    secret.set_tag("resolved", "yes")
    helper.set_tag("saw_result", "yes")

    world.ending_text = (
        f"{helper.name} smiled and said that curious hearts do better than hurried hands. "
        f"{world.hidden.proof_image} By the end, {world.spot.ending_view}, and even the sesame seeds seemed happy to stay."
    )
    world.note(world.ending_text)
    return True


RULES: tuple[tuple[str, Callable[[World], bool]], ...] = (
    ("open_with_curiosity", _r_open_with_curiosity),
    ("repeat_the_clue", _r_repeat_the_clue),
    ("match_gentle_method", _r_match_gentle_method),
    ("close_with_proof", _r_close_with_proof),
)


def run_world(world: World) -> World:
    for name, rule in RULES:
        if rule(world):
            world.fired_rules.append(name)
    return world


def render_story(world: World) -> str:
    middle = (
        f"{world.clue_text} Then {world.params.hero} chose care instead of a sweep and shove, "
        f"because curiosity wanted truth more than a quick clean-up."
    )
    ending = f"{world.turn_text} {world.ending_text} {world.hidden.lesson}"
    return "\n\n".join((world.opening_text, middle, ending))


def prompts_for(world: World) -> list[str]:
    return [
        f"Tell a rhyming story about {world.params.hero} noticing sesame seeds at {world.spot.phrase}.",
        f"Use repetition by showing the sesame clue repeat three times as {world.entities['Sesame'].tags['repeat_action']}.",
        f"Let curiosity guide {world.params.hero} into {world.method.phrase}, and end with this image: {world.hidden.proof_image}",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What first made the child stop and study the sesame seeds?",
            answer=(
                f"{world.params.hero} noticed that the sesame seeds were not scattering in a random way. "
                f"They kept making the same clue at {world.spot.phrase}, so the repeated pattern felt like a message instead of a mess."
            ),
        ),
        QAItem(
            question="Why did the child become curious instead of sweeping the seeds away?",
            answer=(
                f"The repeated sesame pattern suggested that something small was causing it on purpose or by accident. "
                f"Because {world.params.hero} paused to wonder why it kept happening, the real hidden reason had time to show itself."
            ),
        ),
        QAItem(
            question="How did the child search once the clue became clear?",
            answer=(
                f"{world.params.hero} used {world.method.phrase} and repeated the rhyme, \"{world.method.chant}\" three times. "
                f"That method matched the clue type, so the search stayed gentle enough to protect the pattern instead of ruining it."
            ),
        ),
        QAItem(
            question="What was hidden, and why was it there?",
            answer=(
                f"The hidden object was {world.hidden.phrase}, tucked {world.hidden.hiding_spot}. "
                f"It was there because {world.hidden.cause}."
            ),
        ),
        QAItem(
            question="What final image proves that the problem is over?",
            answer=(
                f"The story ends with this proof image: {world.hidden.proof_image} "
                f"That ending shows the place is calm now, because the hidden cause has been found and the sesame is no longer scattering in a puzzling way."
            ),
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can repetition help a child solve a small everyday mystery?",
            answer=(
                "Repetition points to the detail that keeps returning, which makes it easier to separate a meaningful clue from ordinary background noise. "
                "When the same tiny thing happens three times, a careful child can test whether the pattern connects to a hidden cause."
            ),
        ),
        QAItem(
            question="Why is curiosity better than rushing when a clue is made of tiny physical details?",
            answer=(
                "Curiosity slows the body down enough for the eyes and ears to notice what the clue is really doing. "
                "Rushing often destroys delicate evidence such as seed trails, soft taps, little rings, or brief glints."
            ),
        ),
        QAItem(
            question="Why do gentle search methods fit stories about seeds, cloth, and small hidden objects?",
            answer=(
                "Small objects can be pushed deeper or scattered farther if the search is rough. "
                "A gentle method keeps the surface readable, so the child's actions stay connected to the world instead of fighting it."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.spot, params.hidden, params.method):
        raise StoryError(explain_rejection(params.spot, params.hidden, params.method))
    world = run_world(build_world(params))
    story = render_story(world)
    world.story = story
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Prompts ==", *[f"{i}. {item}" for i, item in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sesame repetition curiosity rhyming story world.")
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--hidden", choices=sorted(HIDDEN_THINGS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--helper", choices=sorted(HELPERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.hidden is None or combo[1] == args.hidden)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.spot or "blue_step",
                args.hidden or "seed_packet",
                args.method or "trace_trace_tread",
            )
        )
    spot, hidden, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(rng, gender)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        spot=spot,
        hidden=hidden,
        method=method,
        hero=hero,
        gender=gender,
        helper=helper,
    )


ASP_RULES = r"""
combo(S,H,M) :-
  spot(S), hidden(H), method(M),
  spot_support(S,N), hidden_need(H,N), method_solves(M,N),
  hidden_spot(H,S).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for spot in SPOTS.values():
        rows.append(asp.fact("spot", spot.key))
        for support in spot.support_keys:
            rows.append(asp.fact("spot_support", spot.key, support))
    for hidden in HIDDEN_THINGS.values():
        rows.append(asp.fact("hidden", hidden.key))
        rows.append(asp.fact("hidden_need", hidden.key, hidden.support_key))
        for spot in hidden.allowed_spots:
            rows.append(asp.fact("hidden_spot", hidden.key, spot))
    for method in METHODS.values():
        rows.append(asp.fact("method", method.key))
        for support in method.solves:
            rows.append(asp.fact("method_solves", method.key, support))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            spot=combo[0],
            hidden=combo[1],
            method=combo[2],
            hero="Mina",
            gender="girl",
            helper="baker_nia",
            seed=2100 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        world = sample.world
        if "sesame" not in story:
            problems.append(f"{combo}: story is missing the seed word 'sesame'")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if sample.story.lower().count(METHODS[combo[2]].chant.lower()) < 1:
            problems.append(f"{combo}: story does not render the search chant")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story-grounded QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world-knowledge QA set is too small")
        if any(item.answer.count(".") < 2 for item in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if world is None:
            problems.append(f"{combo}: sample is missing its world model")
            continue
        if world.entities["Sesame"].meters.get("repeat_count") != 3.0:
            problems.append(f"{combo}: sesame repetition state was not recorded")
        if world.entities["Hidden"].meters.get("found") != 1.0:
            problems.append(f"{combo}: hidden object was never marked as found")
        if world.entities["Hidden"].tags.get("resolved") != "yes":
            problems.append(f"{combo}: hidden object never reached a resolved state")
        if world.entities["Hero"].memes.get("curiosity", 0.0) < 2.0:
            problems.append(f"{combo}: curiosity did not accumulate in the hero state")
    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, QA, repetition, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique sesame stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 41
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            spot=combo[0],
            hidden=combo[1],
            method=combo[2],
            hero="Mina",
            gender="girl",
            helper="baker_nia",
            seed=base_seed + i,
        )
        rows.append(generate(params))
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    if args.all:
        samples = _sample_all(args)
    else:
        samples = _sample_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
