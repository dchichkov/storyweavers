#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/woolen_beret_dour_rhyme_nursery_rhyme.py
===================================================================

A small standalone storyworld for a nursery-rhyme-shaped tale about a child, a
woolen beret, a dour morning, and a gust of wind.

The world model is simple and concrete:

- a child starts out warm and proud in a woolen beret
- a gust blows the beret into one of a few snag spots
- the child worries and is tempted to grab too quickly
- a calm grown-up uses a sensible retrieval method
- if the beret gets wet, it must also be dried before the ending rhyme

The prose is rendered in short rhyming lines, but the lines come from simulated
state rather than from one fixed paragraph with nouns swapped in.

Run it
------
    python storyworlds/worlds/gpt-5.4/woolen_beret_dour_rhyme_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/woolen_beret_dour_rhyme_nursery_rhyme.py --spot branch --method reach
    python storyworlds/worlds/gpt-5.4/woolen_beret_dour_rhyme_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/woolen_beret_dour_rhyme_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/woolen_beret_dour_rhyme_nursery_rhyme.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "gran",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    height: str = "low"
    wet: bool = False
    snag_word: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    works_heights: set[str] = field(default_factory=set)
    works_wet: bool = False
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky_line: str
    gust_word: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n".join(self.lines)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    beret = world.get("beret")
    child = world.get("child")
    out: list[str] = []
    if beret.meters["stuck"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        child.memes["worry"] += 1
        out.append("__worry__")
    if beret.meters["wet"] >= THRESHOLD and ("chill",) not in world.fired:
        world.fired.add(("chill",))
        child.meters["chill"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
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
                produced.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def method_fits(method: Method, spot: Spot) -> bool:
    return spot.height in method.works_heights and (method.works_wet or not spot.wet)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for weather_id in WEATHERS:
        for spot_id, spot in SPOTS.items():
            for method_id, method in METHODS.items():
                if method_fits(method, spot):
                    combos.append((weather_id, spot_id, method_id))
    return combos


def explain_rejection(spot: Spot, method: Method) -> str:
    wet_need = "wet" if spot.wet else "dry"
    return (
        f"(No story: {method.label} is not a sensible way to fetch a beret from "
        f"{spot.label}. That spot is {spot.height} and {wet_need}, so choose a method "
        f"that can really reach it safely.)"
    )


def outcome_of(params: "StoryParams") -> str:
    spot = SPOTS[params.spot]
    return "dried" if spot.wet else "returned"


def predict_need(world: World, spot: Spot) -> dict:
    sim = world.copy()
    do_blowaway(sim, spot, narrate=False)
    beret = sim.get("beret")
    return {
        "wet": beret.meters["wet"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"] >= THRESHOLD,
    }


def do_blowaway(world: World, spot: Spot, narrate: bool = True) -> None:
    beret = world.get("beret")
    child = world.get("child")
    beret.meters["on_head"] = 0.0
    beret.meters["stuck"] += 1
    if spot.wet:
        beret.meters["wet"] += 1
    child.meters["warmth"] = 0.0
    propagate(world, narrate=narrate)


def setup(world: World, weather: Weather) -> None:
    child = world.get("child")
    beret = world.get("beret")
    helper = world.get("helper")
    child.memes["joy"] += 1
    child.meters["warmth"] += 1
    beret.meters["on_head"] += 1
    world.say(f"{weather.sky_line}")
    world.say(
        f"{child.id} skipped along in a woolen beret,"
    )
    world.say(
        f"snug on {child.pronoun('possessive')} curls for the start of the day."
    )
    world.say(
        f'"I have a rhyme for the lane," laughed {child.id} to {helper.label_word},'
    )
    world.say(
        '"A rhyme for the robin, the bucket, the bird!"'
    )


def gust(world: World, weather: Weather, spot: Spot) -> None:
    child = world.get("child")
    do_blowaway(world, spot, narrate=False)
    world.say(
        f"But {weather.gust_word} came puffing — not merry, but dour;"
    )
    world.say(
        f"it lifted the beret away in one hourless hour."
    )
    world.say(
        f"Over it tumbled and off it was blown,"
    )
    world.say(
        f"till into {spot.phrase} the small cap was thrown."
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} stood still with a blink and a fret;"
        )
        world.say(
            '"Oh dear," said the child, "there goes my beret!"'
        )


def warn(world: World, spot: Spot) -> None:
    child = world.get("child")
    helper = world.get("helper")
    pred = predict_need(world, spot)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_wet"] = pred["wet"]
    if spot.height == "high":
        world.say(
            f'{helper.label_word.capitalize()} said, "Do not jump and do not sway;'
        )
        world.say(
            'high things ask for help, not a hop-and-hope way."'
        )
    elif spot.wet:
        world.say(
            f'{helper.label_word.capitalize()} said, "Do not splash and do not skate;'
        )
        world.say(
            'a soggy little rescue only makes us late."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} said, "Pause your toes a bit today;'
        )
        world.say(
            'quick hands can tug hard and tear soft wool away."'
        )


def rescue(world: World, method: Method, spot: Spot) -> None:
    helper = world.get("helper")
    beret = world.get("beret")
    child = world.get("child")
    beret.meters["stuck"] = 0.0
    world.say(
        f"So {helper.label_word} {method.text}"
    )
    if spot.wet:
        world.say(
            "up came the beret with a drip and a sway,"
        )
        world.say(
            "its woolen rim darker than dawn's little gray."
        )
    else:
        world.say(
            "up came the beret with a bob and a sway,"
        )
        world.say(
            "with only a leaf where the wind wished to play."
        )
    child.memes["hope"] += 1


def dry_beret(world: World) -> None:
    beret = world.get("beret")
    child = world.get("child")
    helper = world.get("helper")
    if beret.meters["wet"] < THRESHOLD:
        return
    beret.meters["wet"] = 0.0
    beret.meters["dry_again"] += 1
    child.meters["warmth"] += 1
    world.say(
        f"Then {helper.label_word} patted it dry by the stove,"
    )
    world.say(
        "turning damp little drops to a warm woolen cove."
    )


def return_beret(world: World) -> None:
    beret = world.get("beret")
    child = world.get("child")
    beret.meters["on_head"] += 1
    child.meters["warmth"] = 1.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"Back onto {child.id}'s head went the beret so neat,"
    )
    world.say(
        "and the cold little morning grew gentle and sweet."
    )


def ending(world: World, spot: Spot) -> None:
    child = world.get("child")
    world.say(
        f'So {child.id} sang out in a bright, bouncing way,'
    )
    world.say(
        '"When gusts play tricks, we pause for the day!"'
    )
    world.say(
        f"{spot.ending_image}"
    )


def tell(
    *,
    child_name: str,
    child_type: str,
    helper_type: str,
    weather: Weather,
    spot: Spot,
    method: Method,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper"))
    beret = world.add(Entity(
        id="beret",
        kind="thing",
        type="beret",
        label="beret",
        phrase="a woolen beret",
        tags={"beret", "woolen"},
    ))

    setup(world, weather)
    gust(world, weather, spot)
    warn(world, spot)
    rescue(world, method, spot)
    dry_beret(world)
    return_beret(world)
    ending(world, spot)

    world.facts.update(
        child=child,
        helper=helper,
        beret=beret,
        weather=weather,
        spot=spot,
        method=method,
        helper_word=helper.label_word,
        child_name=child_name,
        child_type=child_type,
        outcome="dried" if spot.wet else "returned",
        wet=spot.wet,
        predicted_worry=world.facts.get("predicted_worry", False),
        predicted_wet=world.facts.get("predicted_wet", False),
    )
    return world


WEATHERS = {
    "gray": Weather(
        id="gray",
        sky_line="A dour gray morning hung over the lane,",
        gust_word="a gray gust",
        tags={"wind", "weather", "dour"},
    ),
    "misty": Weather(
        id="misty",
        sky_line="A dour misty morning sat soft on the square,",
        gust_word="a misty gust",
        tags={"wind", "weather", "dour"},
    ),
    "brisk": Weather(
        id="brisk",
        sky_line="A dour brisk morning came whistling with air,",
        gust_word="a brisk gust",
        tags={"wind", "weather", "dour"},
    ),
}

SPOTS = {
    "bush": Spot(
        id="bush",
        label="the rose bush",
        phrase="the rose bush by the gate",
        height="low",
        wet=False,
        snag_word="thorns",
        ending_image="There under the roses, with laughter alight, / the child wore the cap and the world felt right.",
        tags={"bush", "wind"},
    ),
    "branch": Spot(
        id="branch",
        label="the apple branch",
        phrase="the high apple branch by the wall",
        height="high",
        wet=False,
        snag_word="twig",
        ending_image="There under the apples, in sun after gray, / the child tipped the cap and sang down the way.",
        tags={"tree", "wind"},
    ),
    "puddle": Spot(
        id="puddle",
        label="the puddle edge",
        phrase="the puddle edge under the bench",
        height="low",
        wet=True,
        snag_word="water",
        ending_image="There by the bench, with the cap warm and dry, / the child sent a rhyme like a lark to the sky.",
        tags={"puddle", "water"},
    ),
}

METHODS = {
    "reach": Method(
        id="reach",
        label="a careful reach",
        works_heights={"low"},
        works_wet=False,
        text="bent low with one steady hand and a slow, patient reach,",
        qa_text="bent low and lifted the beret out by hand",
        tags={"reach"},
    ),
    "hook": Method(
        id="hook",
        label="a stool and a crochet hook",
        works_heights={"high"},
        works_wet=False,
        text="brought a stool and a crochet hook, then tugged it down from the branch with a careful pull,",
        qa_text="used a stool and a crochet hook to bring the beret down",
        tags={"hook"},
    ),
    "tongs": Method(
        id="tongs",
        label="the laundry tongs",
        works_heights={"low"},
        works_wet=True,
        text="used the laundry tongs with a click-clack grip, lifting the beret out without a slip,",
        qa_text="used laundry tongs to lift the beret out neatly",
        tags={"tongs"},
    ),
}


@dataclass
class StoryParams:
    weather: str
    spot: str
    method: str
    child_name: str
    child_type: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        weather="gray",
        spot="bush",
        method="reach",
        child_name="Mina",
        child_type="girl",
        helper_type="grandmother",
    ),
    StoryParams(
        weather="misty",
        spot="branch",
        method="hook",
        child_name="Toby",
        child_type="boy",
        helper_type="grandfather",
    ),
    StoryParams(
        weather="brisk",
        spot="puddle",
        method="tongs",
        child_name="Elsie",
        child_type="girl",
        helper_type="mother",
    ),
]


KNOWLEDGE = {
    "beret": [
        (
            "What is a beret?",
            "A beret is a soft round cap that sits close on your head. It can be made of wool to help keep you warm."
        )
    ],
    "woolen": [
        (
            "What does woolen mean?",
            "Woolen means something is made from wool. Wool feels soft and helps keep warm air close to your body."
        )
    ],
    "dour": [
        (
            "What does dour mean?",
            "Dour means gloomy or not cheerful. A dour sky looks gray and serious instead of bright and sunny."
        )
    ],
    "wind": [
        (
            "What can wind do to light things?",
            "Wind can push and lift light things like hats, leaves, and paper. That is why you hold on to them on blustery days."
        )
    ],
    "puddle": [
        (
            "Why can a woolen hat get soggy in a puddle?",
            "Wool can soak up water when it falls into a puddle. Then the hat feels heavy and damp until it dries."
        )
    ],
    "hook": [
        (
            "Why use a hook for something high up?",
            "A hook can reach farther than your hand. It helps pull a light thing down without climbing somewhere unsafe."
        )
    ],
    "tongs": [
        (
            "Why use tongs for something wet?",
            "Tongs help you pick up a wet thing without putting your whole hand in the water. They can grip gently from a little distance."
        )
    ],
    "reach": [
        (
            "Why move slowly when something is caught in a bush?",
            "Moving slowly helps you avoid tearing soft cloth on thorns. Careful hands are often better than quick, grabby hands."
        )
    ],
}
KNOWLEDGE_ORDER = ["beret", "woolen", "dour", "wind", "puddle", "hook", "tongs", "reach"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    spot = f["spot"]
    return [
        'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "woolen", "beret", and "dour".',
        f"Tell a rhyming story where a child named {f['child_name']} loses a woolen beret to the wind and a grown-up helps fetch it from {spot.label}.",
        f"Write a gentle rhyme in which a dour morning turns cheerful again after a lost beret is safely returned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child_name = f["child_name"]
    helper_word = f["helper_word"]
    spot = f["spot"]
    method = f["method"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child in a woolen beret, and {helper_word} who helps when the wind blows the cap away."
        ),
        (
            "What made the morning feel dour at first?",
            "The sky was gray and the wind was unfriendly, so the morning felt gloomy instead of bright. Then the gust stole the beret, which made the child worry."
        ),
        (
            f"Where did the beret land?",
            f"The beret landed in {spot.phrase}. That is why the child could not simply keep walking and singing."
        ),
        (
            f"How did {helper_word} help?",
            f"{helper_word.capitalize()} {method.qa_text}. The grown-up used a method that fit the place where the beret had landed."
        ),
    ]
    if f["wet"]:
        out.append(
            (
                "Why did they dry the beret before the end?",
                "The beret had fallen by the puddle and gotten wet, so it felt soggy and chilly. Drying it made it warm and comfortable to wear again."
            )
        )
    else:
        out.append(
            (
                "How did the story end?",
                "The beret went back onto the child's head, and the child sang a rhyme again. The ending image shows that worry changed back into warmth and play."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"beret", "woolen", "dour", "wind"}
    tags |= set(world.facts["method"].tags)
    if world.facts["wet"]:
        tags.add("puddle")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(W, S, M) :- weather(W), spot(S), method(M), allows(S, M).

allows(S, M) :- height(S, H), works_height(M, H), not wet(S).
allows(S, M) :- height(S, H), works_height(M, H), wet(S), works_wet(M).

outcome(dried)   :- chosen_spot(S), wet(S).
outcome(returned) :- chosen_spot(S), not wet(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for wid in WEATHERS:
        lines.append(asp.fact("weather", wid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("height", sid, spot.height))
        if spot.wet:
            lines.append(asp.fact("wet", sid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for height in sorted(method.works_heights):
            lines.append(asp.fact("works_height", mid, height))
        if method.works_wet:
            lines.append(asp.fact("works_wet", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_spot", params.spot)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print(f"MISMATCH in outcome for {case}")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        if "beret" not in sample.story.lower():
            raise StoryError("Smoke test story did not mention the beret.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a woolen beret, a dour gust, and a calm rescue."
    )
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mina", "Elsie", "Nora", "Poppy", "Ada", "Lucy", "June", "Mabel"]
BOY_NAMES = ["Toby", "Finn", "Ollie", "Hugo", "Milo", "Benji", "Ned", "Theo"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.method:
        spot = SPOTS[args.spot]
        method = METHODS[args.method]
        if not method_fits(method, spot):
            raise StoryError(explain_rejection(spot, method))

    combos = [
        combo for combo in valid_combos()
        if (args.weather is None or combo[0] == args.weather)
        and (args.spot is None or combo[1] == args.spot)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather, spot, method = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(
        weather=weather,
        spot=spot,
        method=method,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.weather not in WEATHERS:
        raise StoryError(f"(Invalid weather: {params.weather})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    spot = SPOTS[params.spot]
    method = METHODS[params.method]
    if not method_fits(method, spot):
        raise StoryError(explain_rejection(spot, method))

    world = tell(
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        weather=WEATHERS[params.weather],
        spot=spot,
        method=method,
    )
    world.lines = [line.replace("child", params.child_name) if line.startswith(params.child_name) else line for line in world.lines]
    rendered = world.render().replace("child sang out", f"{params.child_name} sang out")
    rendered = rendered.replace("the child wore the cap", f"{params.child_name} wore the cap")
    rendered = rendered.replace("the child tipped the cap", f"{params.child_name} tipped the cap")
    rendered = rendered.replace("the child sent a rhyme", f"{params.child_name} sent a rhyme")

    return StorySample(
        params=params,
        story=rendered,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (weather, spot, method) combos:\n")
        for weather, spot, method in combos:
            print(f"  {weather:6} {spot:7} {method}")
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
            header = f"### {p.child_name}: {p.spot} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
