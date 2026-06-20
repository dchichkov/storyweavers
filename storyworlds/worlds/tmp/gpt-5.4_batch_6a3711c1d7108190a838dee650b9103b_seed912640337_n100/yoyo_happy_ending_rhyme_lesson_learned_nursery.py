#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py
==============================================================================

A standalone story world about a child, a yoyo, and a small lesson about where
play belongs. The prose aims for a nursery-rhyme feel: light rhythm, simple
images, and a gentle repeated lesson.

The world model is not just noun swapping. A child tries to play with a yoyo in
a cramped place near something fragile. The string snags or the yoyo bumps,
danger rises, and a calm grown-up redirects the play to a clear practice spot.
The story ends happily once the child learns the safer pattern:

    low and slow before high and show

The reasonableness gate is physical:
- a risky story needs a cramped place AND a fragile nearby object
- the offered fix must provide enough open space for the yoyo to swing safely

Run it
------
    python storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py
    python storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py --spot kitchen --hazard teacup
    python storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py --spot meadow --hazard teacup
    python storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py --all
    python storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/yoyo_happy_ending_rhyme_lesson_learned_nursery.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MIN_SAFE_SPACE = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    fragile: bool = False
    open_space: int = 0
    stringy: bool = False
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
    rhyme: str
    space: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    sound: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    place_line: str
    lesson_line: str
    space: int
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_risk(world: World) -> list[str]:
    child = world.get("child")
    yoyo = world.get("yoyo")
    place = world.get("place")
    hazard = world.get("hazard")
    if yoyo.meters["swinging"] < THRESHOLD:
        return []
    sig = ("risk", place.id, hazard.id)
    if sig in world.fired:
        return []
    if place.open_space >= MIN_SAFE_SPACE:
        return []
    if not hazard.fragile:
        return []
    world.fired.add(sig)
    hazard.meters["wobble"] += 1
    child.memes["worry"] += 1
    place.meters["danger"] += 1
    return ["__risk__"]


def _r_tangle(world: World) -> list[str]:
    child = world.get("child")
    yoyo = world.get("yoyo")
    place = world.get("place")
    if yoyo.meters["swinging"] < THRESHOLD:
        return []
    sig = ("tangle", place.id)
    if sig in world.fired:
        return []
    if place.open_space >= MIN_SAFE_SPACE:
        return []
    world.fired.add(sig)
    yoyo.meters["tangled"] += 1
    child.memes["frustration"] += 1
    return ["__tangle__"]


CAUSAL_RULES = [
    Rule("risk", "physical", _r_risk),
    Rule("tangle", "physical", _r_tangle),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def hazard_at_risk(spot: Spot, hazard: Hazard) -> bool:
    return spot.space < MIN_SAFE_SPACE and hazard.fragile


def remedy_fits(remedy: Remedy) -> bool:
    return remedy.space >= MIN_SAFE_SPACE


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    good_remedies = [r for r in REMEDIES.values() if remedy_fits(r)]
    if not good_remedies:
        return combos
    for spot_id, spot in SPOTS.items():
        for hazard_id, hazard in HAZARDS.items():
            for remedy_id in REMEDIES:
                if hazard_at_risk(spot, hazard) and remedy_fits(REMEDIES[remedy_id]):
                    combos.append((spot_id, hazard_id, remedy_id))
    return combos


def explain_rejection(spot: Spot, hazard: Hazard) -> str:
    if spot.space >= MIN_SAFE_SPACE:
        return (
            f"(No story: {spot.phrase} already gives the yoyo plenty of room, so "
            f"{hazard.phrase} is not in real danger. Pick a snugger spot like the "
            f"kitchen or the stair landing.)"
        )
    if not hazard.fragile:
        return (
            f"(No story: {hazard.phrase} is not fragile enough for a wobble-and-warning "
            f"story. Choose something easy to tip or knock.)"
        )
    return "(No story: this combination does not make a believable little hazard.)"


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    return (
        f"(No story: remedy '{rid}' does not provide enough open space for a yoyo. "
        f"Choose one that gives room to swing low and slow.)"
    )


# ---------------------------------------------------------------------------
# Prediction and verbs
# ---------------------------------------------------------------------------
def predict_trouble(world: World) -> dict:
    sim = world.copy()
    do_swing(sim, narrate=False)
    return {
        "wobble": sim.get("hazard").meters["wobble"] >= THRESHOLD,
        "tangled": sim.get("yoyo").meters["tangled"] >= THRESHOLD,
        "danger": sim.get("place").meters["danger"],
    }


def do_swing(world: World, narrate: bool = True) -> None:
    world.get("yoyo").meters["swinging"] += 1
    world.get("child").memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, spot: Spot) -> None:
    world.say(
        f"{child.id} had a bright red yoyo, yo-high and yo-low. "
        f"In {spot.phrase}, {child.pronoun()} loved to make it go."
    )
    world.say(
        f"It hummed on the string with a soft little show, "
        f"and {spot.rhyme} made the whole corner glow."
    )


def near_fragile(world: World, hazard: Hazard) -> None:
    world.say(
        f"Nearby sat {hazard.phrase}, quiet and still. "
        f"It looked very pretty, but breakable still."
    )


def tempt(world: World, child: Entity) -> None:
    child.memes["eager"] += 1
    world.say(
        f'"Watch my yoyo dip! Watch my yoyo fly!" said {child.id}. '
        f'"I can toss it fast. I can toss it high!"'
    )


def warn(world: World, mentor: Entity, child: Entity, hazard: Hazard) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_tangled"] = pred["tangled"]
    mentor.memes["care"] += 1
    wobble = "make the " + hazard.label + " wobble" if pred["wobble"] else "make a fuss"
    tangle = "and snarl the string" if pred["tangled"] else ""
    world.say(
        f'"Not so high in here, my dear," said {mentor.label_word}. '
        f'"A quick yoyo swing could {wobble} {tangle}. '
        f'Play needs room, and room needs care."'
    )


def mishap(world: World, child: Entity, hazard: Hazard) -> None:
    do_swing(world, narrate=False)
    child.memes["surprise"] += 1
    bits = []
    if world.get("yoyo").meters["tangled"] >= THRESHOLD:
        bits.append("the string gave a tiny twist")
    if world.get("hazard").meters["wobble"] >= THRESHOLD:
        bits.append(f"{hazard.phrase} gave a little {hazard.sound}")
    if not bits:
        bits.append("the yoyo hopped too close for comfort")
    joined = ", and ".join(bits)
    world.say(
        f"Down went the yoyo with a hop and a whip; "
        f"then {joined}. {child.id} stopped in the middle of the trip."
    )


def pause(world: World, child: Entity) -> None:
    child.memes["listening"] += 1
    world.say(
        f"{child.id} held the yoyo still by the side of one shoe. "
        f'"Oh dear," {child.pronoun()} whispered, "what should I do?"'
    )


def redirect(world: World, mentor: Entity, child: Entity, remedy: Remedy) -> None:
    world.get("place").open_space = remedy.space
    world.get("place").meters["danger"] = 0.0
    world.get("yoyo").meters["tangled"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f'{mentor.label_word.capitalize()} smiled kindly and knew what to say: '
        f'"{remedy.place_line} Come, let us play."'
    )
    world.say(
        f'"First low and slow, then high with a show; '
        f'{remedy.lesson_line}"'
    )


def practice(world: World, child: Entity, remedy: Remedy) -> None:
    child.memes["skill"] += 1
    child.memes["joy"] += 1
    world.get("yoyo").meters["smooth"] += 1
    world.say(
        f"So off they went to {remedy.phrase}. "
        f"The yoyo went down, then up in neat rays."
    )
    world.say(
        "Low and slow, then high with a show: "
        "that was the tune that helped it go."
    )


def ending(world: World, child: Entity, mentor: Entity, hazard: Hazard) -> None:
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    world.say(
        f"{hazard.phrase.capitalize()} stayed safe where it had been, "
        f"and the room grew calm and bright again."
    )
    world.say(
        f'"Now I know where yoyo games should go," said {child.id}. '
        f'"I leave tight spots and choose room below."'
    )
    world.say(
        f"So {child.id} and {mentor.label_word} laughed in the golden glow, "
        f"with a happy little yoyo going low, then high, then low."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    spot: Spot,
    hazard_cfg: Hazard,
    remedy_cfg: Remedy,
    child_name: str = "Molly",
    child_type: str = "girl",
    mentor_type: str = "grandmother",
    child_trait: str = "merry",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child",
                             traits=[child_trait]))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, role="mentor",
                              label="the grown-up"))
    place = world.add(Entity(id="place", type="place", label=spot.label, open_space=spot.space))
    yoyo = world.add(Entity(id="yoyo", type="toy", label="yoyo", stringy=True))
    hazard = world.add(Entity(id="hazard", type="hazard", label=hazard_cfg.label,
                              fragile=hazard_cfg.fragile))

    introduce(world, child, spot)
    near_fragile(world, hazard_cfg)

    world.para()
    tempt(world, child)
    warn(world, mentor, child, hazard_cfg)

    world.para()
    mishap(world, child, hazard_cfg)
    pause(world, child)

    world.para()
    redirect(world, mentor, child, remedy_cfg)
    practice(world, child, remedy_cfg)
    ending(world, child, mentor, hazard_cfg)

    world.facts.update(
        child=child,
        mentor=mentor,
        spot=spot,
        hazard_cfg=hazard_cfg,
        remedy=remedy_cfg,
        hazard=hazard,
        yoyo=yoyo,
        learned=child.memes["lesson"] >= THRESHOLD,
        safe_space=place.open_space >= MIN_SAFE_SPACE,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SPOTS = {
    "kitchen": Spot(
        "kitchen", "kitchen", "the little kitchen nook",
        "the spoons gave a silver glow", 0,
        tags={"kitchen", "indoors"},
    ),
    "stair": Spot(
        "stair", "stair landing", "the narrow stair landing",
        "the banister shone with a sleepy glow", 0,
        tags={"stairs", "indoors"},
    ),
    "hall": Spot(
        "hall", "hall", "the short front hall",
        "the small rug sat in a row", 1,
        tags={"hall", "indoors"},
    ),
    "meadow": Spot(
        "meadow", "meadow", "the open green meadow",
        "the daisies swayed to and fro", 3,
        tags={"outside", "meadow"},
    ),
}

HAZARDS = {
    "teacup": Hazard(
        "teacup", "teacup", "a blue teacup on the table", "clink",
        tags={"teacup", "fragile"},
    ),
    "vase": Hazard(
        "vase", "vase", "a tall flower vase by the wall", "wobble",
        tags={"vase", "fragile", "flowers"},
    ),
    "lamp": Hazard(
        "lamp", "lamp", "a glass bedside lamp", "tink",
        tags={"lamp", "fragile"},
    ),
}

REMEDIES = {
    "chalk_ring": Remedy(
        "chalk_ring", "chalk ring", "the chalk ring in the yard",
        "Let us step to the chalk ring in the yard.",
        "low and slow before high and show",
        3,
        tags={"yard", "chalk", "practice"},
    ),
    "porch_mat": Remedy(
        "porch_mat", "porch mat", "the wide porch mat",
        "Let us step to the wide porch mat.",
        "low and slow before high and show",
        2,
        tags={"porch", "practice"},
    ),
    "table_side": Remedy(
        "table_side", "table side", "the same table side",
        "Let us stay right here by the table side.",
        "low and slow before high and show",
        1,
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Molly", "Lila", "Daisy", "Poppy", "Nell", "Rosie"]
BOY_NAMES = ["Toby", "Milo", "Benji", "Robin", "Ollie", "Jem"]
TRAITS = ["merry", "bouncy", "bright", "gentle", "cheery"]
MENTORS = ["mother", "father", "grandmother", "grandfather"]

CURATED = [
    StoryParams("kitchen", "teacup", "chalk_ring", "Molly", "girl", "grandmother", "merry"),
    StoryParams("stair", "vase", "porch_mat", "Toby", "boy", "father", "bouncy"),
    StoryParams("hall", "lamp", "chalk_ring", "Rosie", "girl", "mother", "bright"),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    spot: str
    hazard: str
    remedy: str
    child_name: str
    child_type: str
    mentor_type: str
    child_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "yoyo": [(
        "What is a yoyo?",
        "A yoyo is a toy on a string that goes down and comes back up when you throw it gently and pull at the right time."
    )],
    "fragile": [(
        "What does fragile mean?",
        "Fragile means something can break easily if it is bumped, dropped, or knocked over."
    )],
    "practice": [(
        "Why is open space good for yoyo play?",
        "Open space gives the string room to swing without hitting people or things. That makes practice safer and smoother."
    )],
    "lesson": [(
        "What is a good rule for trying a new trick?",
        "Start slow in a safe place before you try to go fast. That way you can learn without making a mess or causing a bump."
    )],
    "chalk": [(
        "Why draw a chalk ring for practice?",
        "A chalk ring shows a clear place to stand and play. It helps a child remember where there is enough room."
    )],
    "porch": [(
        "Why can a porch be a good place to play carefully?",
        "A wide porch can give you a flat open spot with fewer breakable things nearby. That makes careful play easier."
    )],
    "teacup": [(
        "Why should you be careful near a teacup?",
        "A teacup can tip or crack if something bumps it. Gentle hands and enough space help keep it safe."
    )],
    "vase": [(
        "Why can a vase be easy to knock over?",
        "A vase is often tall and can wobble if it is bumped. If it falls, it may break and spill water."
    )],
    "lamp": [(
        "Why should toys stay away from a glass lamp?",
        "A glass lamp can crack if it is hit. It is safer to move play away from breakable lamps."
    )],
}
KNOWLEDGE_ORDER = ["yoyo", "fragile", "practice", "lesson", "chalk", "porch", "teacup", "vase", "lamp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, spot, hazard, remedy = f["child"], f["spot"], f["hazard_cfg"], f["remedy"]
    return [
        'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the word "yoyo" and ends happily with a lesson learned.',
        f"Tell a gentle rhyming story where {child.id} tries to play with a yoyo in {spot.phrase} near {hazard.phrase}, then learns to move to {remedy.phrase}.",
        'Write a simple story with a repeated rhyme lesson like "low and slow before high and show," and make the ending calm and cheerful.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mentor = f["mentor"]
    spot = f["spot"]
    hazard = f["hazard_cfg"]
    remedy = f["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child with a yoyo, and {mentor.label_word} who helps {child.pronoun('object')} choose a safer place to play."
        ),
        (
            f"Where did {child.id} begin to play?",
            f"{child.id} began in {spot.phrase}. It was a snug place, which is why the yoyo did not have enough room."
        ),
        (
            f"Why did {mentor.label_word} warn {child.id}?",
            f"{mentor.label_word.capitalize()} warned {child.id} because a quick yoyo swing near {hazard.phrase} could make it wobble. The warning came from noticing the place was tight and the nearby object was fragile."
        ),
        (
            "What little problem happened?",
            f"When the yoyo went down, the string twisted and {hazard.phrase} gave a little {hazard.sound}. That small scare showed {child.id} the warning was true."
        ),
        (
            "How was the problem solved?",
            f"{mentor.label_word.capitalize()} moved the play to {remedy.phrase}, where there was more room. In the open spot, {child.id} could practice the yoyo safely and smoothly."
        ),
        (
            "What lesson did the child learn?",
            f"{child.id} learned to play low and slow before trying high and show. {child.pronoun().capitalize()} also learned to choose a roomy place instead of a tight one."
        ),
        (
            "How did the story end?",
            f"It ended happily with the fragile thing still safe and the yoyo bouncing neatly in a better place. {child.id} and {mentor.label_word} finished by laughing together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"yoyo", "fragile", "practice", "lesson"} | set(f["hazard_cfg"].tags) | set(f["remedy"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.fragile:
            bits.append("fragile=True")
        if e.open_space:
            bits.append(f"open_space={e.open_space}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risky_spot(S) :- spot(S), space(S, N), min_safe(M), N < M.
usable_remedy(R) :- remedy(R), remedy_space(R, N), min_safe(M), N >= M.
hazardous(H) :- hazard(H), fragile(H).

valid(S, H, R) :- risky_spot(S), hazardous(H), usable_remedy(R).

outcome(learned) :- valid(S, H, R), chosen(S, H, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("min_safe", MIN_SAFE_SPACE))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("space", sid, spot.space))
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if hz.fragile:
            lines.append(asp.fact("fragile", hid))
    for rid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_space", rid, rem.space))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen", params.spot, params.hazard, params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "learned" if (
        hazard_at_risk(SPOTS[params.spot], HAZARDS[params.hazard])
        and remedy_fits(REMEDIES[params.remedy])
    ) else "?"


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

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("SMOKE FAIL: resolve_params crashed on default args:", err)

    for params in smoke_cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for", params)
        try:
            sample = generate(params)
            if not sample.story.strip():
                rc = 1
                print("SMOKE FAIL: generated empty story for", params)
        except Exception as err:  # pragma: no cover - defensive verify path
            rc = 1
            print("SMOKE FAIL: generate crashed for", params, "->", err)
    if rc == 0:
        print(f"OK: outcome model matches on {len(smoke_cases)} smoke scenarios.")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child learns where a yoyo should be played."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--mentor-type", choices=MENTORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.hazard:
        if not hazard_at_risk(SPOTS[args.spot], HAZARDS[args.hazard]):
            raise StoryError(explain_rejection(SPOTS[args.spot], HAZARDS[args.hazard]))
    if args.remedy and not remedy_fits(REMEDIES[args.remedy]):
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        c for c in valid_combos()
        if (args.spot is None or c[0] == args.spot)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot, hazard, remedy = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    mentor_type = args.mentor_type or rng.choice(MENTORS)
    child_trait = rng.choice(TRAITS)
    return StoryParams(spot, hazard, remedy, child_name, child_type, mentor_type, child_trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SPOTS[params.spot],
        HAZARDS[params.hazard],
        REMEDIES[params.remedy],
        params.child_name,
        params.child_type,
        params.mentor_type,
        params.child_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, hazard, remedy) combos:\n")
        for spot, hazard, remedy in combos:
            print(f"  {spot:8} {hazard:8} {remedy}")
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
            header = f"### {p.child_name}: {p.spot}, {p.hazard}, {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
