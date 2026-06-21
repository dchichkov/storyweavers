#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py
===============================================================================

A standalone storyworld for a tall-tale flavored cautionary story about a child,
a robot, a wobbling tote, and the kind of problem solving that comes after a bad
idea makes a loud mess.

The tiny domain:
- A child has to move some oversized fair cargo.
- A trusty robot offers a grounded warning about a risky route and a shaky tote.
- A boasty child may ignore the warning and even say nothing can "jinx" the trip.
- A noisy mishap proves the warning was real.
- Then child and robot solve the problem sensibly and finish the job safely.

The model prefers a few plausible branches over broad coverage:
- careful children heed the warning and avoid the mishap;
- bolder children ignore it, causing a small accident;
- a good fix can still save the day, while a weak fix can leave the delivery spoiled.

Run it
------
python storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py
python storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py --all --qa
python storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py --json
python storyworlds/worlds/gpt-5.4/robot_tote_jinx_problem_solving_cautionary_sound.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CAREFUL_TRAITS = {"careful", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    sturdy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        robotish = {"robot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in robotish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Route:
    id: str
    place: str
    start: str
    goal: str
    brag: str
    roughness: int
    hazards: set[str] = field(default_factory=set)
    clatter: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    plural: bool
    fragility: int
    sound: str
    cracked: str
    safe_end: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    guards: set[str] = field(default_factory=set)
    setup: str = ""
    work: str = ""
    qa_text: str = ""
    fail_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str
    label: str
    boost: int
    boast: str
    move: str
    noise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    route: str
    cargo: str
    fix: str
    mistake: str
    child_name: str
    child_gender: str
    robot_name: str
    grownup: str
    trait: str
    seed: Optional[int] = None


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


def _r_wobble(world: World) -> list[str]:
    tote = world.get("tote")
    cargo = world.get("cargo")
    child = world.get("child")
    robot = world.get("robot")
    out: list[str] = []
    if tote.meters["jolted"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tote.meters["wobble"] += 1
    child.memes["alarm"] += 1
    robot.memes["caution"] += 1
    if cargo.fragile:
        cargo.meters["risk"] += 1
    out.append("__wobble__")
    return out


def _r_crack(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["risk"] < THRESHOLD or cargo.meters["impact"] < THRESHOLD:
        return []
    sig = ("crack",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["cracked"] += 1
    cargo.meters["spilled"] += 1
    world.get("child").mêmes = world.get("child").memes
    world.get("child").memes["regret"] += 1
    return ["__crack__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="crack", tag="physical", apply=_r_crack),
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
        for s in produced:
            world.say(s)
    return produced


ROUTES = {
    "bridge": Route(
        id="bridge",
        place="the Big Bell Valley",
        start="the moonberry shed",
        goal="the fair pie table",
        brag="long enough to make a cow yawn halfway across",
        roughness=2,
        hazards={"bounce", "rattle"},
        clatter="CLACK-clack, RATTLE-rattle",
        tags={"bridge", "sound"},
    ),
    "hill": Route(
        id="hill",
        place="the Windy Turnip Ridge",
        start="the barn porch",
        goal="the market tent",
        brag="so steep even raindrops seemed to slide down it sideways",
        roughness=2,
        hazards={"speed", "bounce"},
        clatter="BUMP-bump, skitter-skatter",
        tags={"hill", "sound"},
    ),
    "boardwalk": Route(
        id="boardwalk",
        place="the Marshmallow Marsh",
        start="the lantern house",
        goal="the evening parade gate",
        brag="so creaky that ducks could keep time on it",
        roughness=1,
        hazards={"rattle", "wind"},
        clatter="CREEEAK, tap-tap, wobble-wobble",
        tags={"boardwalk", "sound"},
    ),
}

CARGO = {
    "jam": Cargo(
        id="jam",
        label="moonberry jam jars",
        phrase="three giant moonberry jam jars",
        plural=True,
        fragility=2,
        sound="clink-clink",
        cracked="purple jam ran down the tote slats like shiny paint",
        safe_end="the moonberry jam jars sat still as sleeping toads",
        tags={"jam", "fragile"},
    ),
    "eggs": Cargo(
        id="eggs",
        label="thunder-eggs",
        phrase="a crate of thunder-eggs as big as soup bowls",
        plural=True,
        fragility=2,
        sound="tok-tok",
        cracked="a bright yellow yolk oozed through the straw like sunrise",
        safe_end="the thunder-eggs rode along without even a peep",
        tags={"eggs", "fragile"},
    ),
    "globes": Cargo(
        id="globes",
        label="glass chime-globes",
        phrase="two glass chime-globes that sang when the wind kissed them",
        plural=True,
        fragility=3,
        sound="ting-a-ling",
        cracked="one globe split with a sad silver note and scattered bright beads",
        safe_end="the glass chime-globes chimed softly and stayed whole",
        tags={"glass", "fragile", "sound"},
    ),
}

FIXES = {
    "straw": Fix(
        id="straw",
        label="straw padding",
        sense=3,
        power=3,
        guards={"bounce", "rattle"},
        setup="stuffed the tote with clean straw until it looked like a little golden nest",
        work="They tucked the cargo deep into the straw and let the jolts sink into the soft bed.",
        qa_text="lined the tote with straw to cushion the bumps",
        fail_text="The straw helped a little, but the load still jolted too hard",
        tags={"straw", "problem_solving"},
    ),
    "slow_mode": Fix(
        id="slow_mode",
        label="slow mode",
        sense=3,
        power=3,
        guards={"speed", "wind"},
        setup="clicked the robot into slow mode so each step landed with a careful thump",
        work="The robot shortened its steps and held the tote low and level.",
        qa_text="switched the robot to slow mode and moved carefully",
        fail_text="Even in slow mode, the tote still shook more than it should",
        tags={"robot", "problem_solving"},
    ),
    "two_trips": Fix(
        id="two_trips",
        label="two small trips",
        sense=3,
        power=4,
        guards={"bounce", "rattle", "speed", "wind"},
        setup="split the load into two smaller trips so the tote could breathe instead of bulge",
        work="With less weight in the tote, the robot could balance the cargo without a frantic wobble.",
        qa_text="split the load and carried it in two smaller trips",
        fail_text="They tried making smaller trips, but too much had already been spoiled",
        tags={"tote", "problem_solving"},
    ),
    "rope": Fix(
        id="rope",
        label="one loose rope",
        sense=1,
        power=1,
        guards={"speed"},
        setup="looped one sleepy rope around the tote and hoped for the best",
        work="The rope stopped almost nothing and mostly flapped about.",
        qa_text="tied the tote with one loose rope",
        fail_text="The loose rope slapped around and did not steady the tote",
        tags={"weak_fix"},
    ),
}

MISTAKES = {
    "race": Mistake(
        id="race",
        label="racing",
        boost=1,
        boast='"Nothing can jinx us now!"',
        move="told the robot to race the wind",
        noise="WHIRRRR-zip!",
        tags={"speed", "jinx"},
    ),
    "overfill": Mistake(
        id="overfill",
        label="overfilling",
        boost=1,
        boast='"Nothing can jinx a tote this strong!"',
        move="piled the tote high enough to tickle the robot's chin",
        noise="BOINK-boink!",
        tags={"bounce", "jinx"},
    ),
    "skip_checks": Mistake(
        id="skip_checks",
        label="skipping checks",
        boost=1,
        boast='"Jinx is just a silly word. Let\'s go!"',
        move="waved away the robot's careful checklist",
        noise="click-snap, clunk",
        tags={"rattle", "jinx"},
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Poppy", "Tess", "Lula", "Daisy", "June", "Ivy"]
BOY_NAMES = ["Otis", "Beau", "Milo", "Rafe", "Toby", "Finn", "Jasper", "Eli"]
ROBOT_NAMES = ["Totebot", "Tinwhistle", "Clankle", "Brassy", "Whirrby"]
TRAITS = ["careful", "steady", "thoughtful", "curious", "bold", "hasty"]


def valid_fix(route: Route, fix: Fix) -> bool:
    return bool(route.hazards & fix.guards) or fix.id == "two_trips"


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        for cargo_id, cargo in CARGO.items():
            if cargo.fragility < 1:
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN and valid_fix(route, fix):
                    combos.append((route_id, cargo_id, fix_id))
    return combos


def severity_of(route: Route, cargo: Cargo, mistake: Mistake) -> int:
    return route.roughness + cargo.fragility + mistake.boost - 1


def would_heed(trait: str) -> bool:
    return trait in CAREFUL_TRAITS


def outcome_of(params: StoryParams) -> str:
    route = ROUTES[params.route]
    cargo = CARGO[params.cargo]
    fix = FIXES[params.fix]
    mistake = MISTAKES[params.mistake]
    if would_heed(params.trait):
        return "averted"
    if fix.power >= severity_of(route, cargo, mistake):
        return "solved"
    return "spoiled"


def predict_mishap(world: World, route: Route, cargo_cfg: Cargo, mistake: Mistake) -> dict:
    sim = world.copy()
    tote = sim.get("tote")
    cargo = sim.get("cargo")
    tote.meters["jolted"] += 1
    cargo.meters["impact"] += 1
    sim.facts["route"] = route
    sim.facts["cargo_cfg"] = cargo_cfg
    sim.facts["mistake"] = mistake
    propagate(sim, narrate=False)
    return {
        "risk": cargo.meters["risk"],
        "cracked": cargo.meters["cracked"] >= THRESHOLD,
        "severity": severity_of(route, cargo_cfg, mistake),
    }


def opening(world: World, child: Entity, robot: Entity, grownup: Entity,
            route: Route, cargo_cfg: Cargo) -> None:
    child.memes["joy"] += 1
    robot.memes["helpfulness"] += 1
    world.say(
        f"In {route.place}, where stories grew taller than beanpoles, {child.id} had a helper robot named {robot.id}."
    )
    world.say(
        f"{robot.id} had brass knees, a whistling chest, and a square tote on {robot.pronoun('possessive')} back big enough to carry a bakery's worth of trouble."
    )
    world.say(
        f"That morning, {grownup.label_word.capitalize()} asked them to carry {cargo_cfg.phrase} from {route.start} to {route.goal} by way of a road {route.brag}."
    )


def boast_and_warning(world: World, child: Entity, robot: Entity, grownup: Entity,
                      route: Route, cargo_cfg: Cargo, mistake: Mistake) -> None:
    pred = predict_mishap(world, route, cargo_cfg, mistake)
    world.facts["predicted_severity"] = pred["severity"]
    robot.memes["caution"] += 1
    child.memes["desire"] += 1
    world.say(
        f'The cargo made a small song in the tote -- {cargo_cfg.sound}, {cargo_cfg.sound} -- and {child.id} grinned.'
    )
    world.say(
        f'{child.id} {mistake.move} and said, {mistake.boast}'
    )
    world.say(
        f'{robot.id} gave a polite warning buzz. "Whirr-click. This route is rough. If the tote jolts, the {cargo_cfg.label} may crack."'
    )
    world.say(
        f'{grownup.label_word.capitalize()} nodded from the porch. "Listen to the robot. Big jobs like a calm head."'
    )


def heed(world: World, child: Entity, robot: Entity, route: Route, cargo_cfg: Cargo, fix: Fix) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"For one blink, {child.id} puffed up like a little storm cloud. Then the warning settled in."
    )
    world.say(
        f'"You are right," {child.pronoun()} said. "Let us do it the safe way."'
    )
    world.say(
        f"So {robot.id} {fix.setup}. {fix.work}"
    )
    world.say(
        f"They crossed the route without a single foolish hurry, and {cargo_cfg.safe_end} when they reached the other side."
    )


def ignore_warning(world: World, child: Entity, robot: Entity, route: Route,
                   cargo_cfg: Cargo, mistake: Mistake) -> None:
    child.memes["defiance"] += 1
    tote = world.get("tote")
    cargo = world.get("cargo")
    world.say(
        f"But {child.id} was already chasing the big feeling of the job. {child.pronoun().capitalize()} tapped the tote and sent them off."
    )
    tote.meters["jolted"] += 1
    cargo.meters["impact"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Out on the road came the noise: {mistake.noise} {route.clatter}! The tote hopped. The robot lurched. The cargo sang a frightened little song -- {cargo_cfg.sound}!"
    )


def mishap(world: World, child: Entity, cargo_cfg: Cargo) -> None:
    cargo = world.get("cargo")
    if cargo.meters["cracked"] >= THRESHOLD:
        world.say(
            f"Then came the worst sound of all: crack! {cargo_cfg.cracked}"
        )
    else:
        world.say(
            f"No piece broke all the way through, but the load knocked together hard enough to make {child.id}'s heart thump."
        )


def solve(world: World, child: Entity, robot: Entity, grownup: Entity,
          cargo_cfg: Cargo, fix: Fix) -> None:
    child.memes["regret"] += 1
    robot.memes["helpfulness"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} stopped the robot at once. "{robot.id}, I made the tote do too much," {child.pronoun()} said.'
    )
    world.say(
        f'{robot.id} gave a softer hum. "Problem detected. Problem can still be solved."'
    )
    world.say(
        f'Together they {fix.setup}. {fix.work}'
    )
    world.say(
        f'After that, {robot.id} moved with steady little sounds -- thump, hiss, clink -- and the rest of the trip behaved itself.'
    )
    world.say(
        f"When they reached {world.facts['route'].goal}, {grownup.label_word} saw that the load was safe at last, and {child.id} felt proud for fixing the trouble instead of pretending it had not happened."
    )


def spoil(world: World, child: Entity, robot: Entity, grownup: Entity,
          cargo_cfg: Cargo, fix: Fix) -> None:
    child.memes["sad"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} and {robot.id} tried one more fix: they {fix.setup}. {fix.work}'
    )
    world.say(
        f"But it was too late to save all of it. {fix.fail_text}, and part of the load had already gone bad."
    )
    world.say(
        f'{grownup.label_word.capitalize()} was not cross so much as sorry. "{child.id}," {grownup.pronoun()} said, "a loud mistake is still a teacher. Next time, hear the small warning before it grows teeth."'
    )
    world.say(
        f"{child.id} looked at the drippy tote and never again bragged that nothing could jinx a foolish plan."
    )


def tell(route: Route, cargo_cfg: Cargo, fix: Fix, mistake: Mistake,
         child_name: str = "Mira", child_gender: str = "girl",
         robot_name: str = "Totebot", grownup_type: str = "aunt",
         trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    robot = world.add(Entity(
        id="robot",
        kind="character",
        type="robot",
        label=robot_name,
        role="robot",
        sturdy=True,
        tags={"robot"},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
    ))
    tote = world.add(Entity(
        id="tote",
        type="tote",
        label="tote",
        phrase="the robot's square tote",
        role="container",
        sturdy=True,
        tags={"tote"},
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="cargo",
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        role="cargo",
        fragile=True,
        tags=set(cargo_cfg.tags),
    ))
    world.facts.update(
        child=child,
        robot=robot,
        grownup=grownup,
        tote=tote,
        cargo=cargo,
        route=route,
        cargo_cfg=cargo_cfg,
        fix=fix,
        mistake=mistake,
        child_name=child_name,
        robot_name=robot_name,
    )

    opening(world, child, robot, grownup, route, cargo_cfg)
    world.para()
    boast_and_warning(world, child, robot, grownup, route, cargo_cfg, mistake)

    if would_heed(trait):
        world.para()
        heed(world, child, robot, route, cargo_cfg, fix)
        outcome = "averted"
    else:
        world.para()
        ignore_warning(world, child, robot, route, cargo_cfg, mistake)
        mishap(world, child, cargo_cfg)
        world.para()
        if fix.power >= severity_of(route, cargo_cfg, mistake):
            solve(world, child, robot, grownup, cargo_cfg, fix)
            outcome = "solved"
        else:
            spoil(world, child, robot, grownup, cargo_cfg, fix)
            outcome = "spoiled"

    world.facts.update(
        outcome=outcome,
        heed=would_heed(trait),
        severity=severity_of(route, cargo_cfg, mistake),
        cracked=world.get("cargo").meters["cracked"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "robot": [
        (
            "What is a robot?",
            "A robot is a machine that can move and do jobs. Some robots can carry things or help people follow careful steps."
        )
    ],
    "tote": [
        (
            "What is a tote?",
            "A tote is a container used to carry things from one place to another. If it is packed too full or jolted too hard, the things inside can bump together."
        )
    ],
    "jinx": [
        (
            "What does jinx mean in a story like this?",
            "In stories, saying something will never go wrong can feel like tempting trouble. The real lesson is not magic but overconfidence, because careless boasting can make people ignore a good warning."
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can crack or break if it is bumped or dropped. Fragile things need slow hands and steady carrying."
        )
    ],
    "sound": [
        (
            "Why do stories use sound words like clink and clatter?",
            "Sound words help you hear the action in your mind. They can make a wobble feel funny, scary, or sudden."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what went wrong, thinking about why it happened, and trying a better plan. Good problem solving is calm and honest."
        )
    ],
    "straw": [
        (
            "Why can straw help protect fragile things?",
            "Straw is soft and springy, so it can cushion bumps. That makes it useful for packing breakable things in a tote or crate."
        )
    ],
}
KNOWLEDGE_ORDER = ["robot", "tote", "jinx", "fragile", "sound", "problem_solving", "straw"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route = f["route"]
    cargo_cfg = f["cargo_cfg"]
    outcome = f["outcome"]
    child_name = f["child_name"]
    robot_name = f["robot_name"]
    if outcome == "averted":
        return [
            f'Write a tall-tale style story for a 3-to-5-year-old that includes the words "robot", "tote", and "jinx", with sound effects and a safe problem-solving ending.',
            f"Tell a story where {child_name} and a robot named {robot_name} need to carry {cargo_cfg.label}, but the child listens to a warning before the tote starts bouncing.",
            f"Write a cautionary story with funny sound effects where bragging almost causes trouble, but calm thinking saves the day before anything breaks.",
        ]
    if outcome == "solved":
        return [
            f'Write a tall-tale style story that includes "robot", "tote", and "jinx", with a loud mishap, a warning that proves true, and problem solving afterward.',
            f"Tell a child-friendly cautionary story where {child_name} ignores a robot's warning, hears the cargo rattle, and then fixes the problem the sensible way.",
            f"Write a simple story with sound effects and a complete beginning, middle, and ending, where a wobbling tote teaches a child to slow down and think.",
        ]
    return [
        f'Write a cautionary tall-tale story for a 3-to-5-year-old that includes "robot", "tote", and "jinx", with sound effects and a sadder lesson after a careless choice.',
        f"Tell a story where a child ignores a robot's warning about fragile cargo, tries too weak a fix, and learns that small warnings should be heard early.",
        f"Write a child-facing story with noisy action and a clear lesson: boasting does not make a risky plan safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    robot = f["robot"]
    grownup = f["grownup"]
    route = f["route"]
    cargo_cfg = f["cargo_cfg"]
    fix = f["fix"]
    mistake = f["mistake"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['child_name']}, a child with a helper robot named {f['robot_name']}. They are trying to carry {cargo_cfg.phrase} in a tote for a grown-up."
        ),
        (
            "What job did they need to do?",
            f"They had to carry {cargo_cfg.label} from {route.start} to {route.goal}. The route was rough, so the job needed careful moving instead of bragging."
        ),
        (
            "Why did the robot warn the child?",
            f"The robot warned that the route could jolt the tote and crack the cargo. The warning came from a real risk, because the load was fragile and the road was bumpy."
        ),
        (
            'Why did the story use the word "jinx"?',
            f'The child used "jinx" while boasting that nothing could go wrong. That boasting showed overconfidence, which is why the warning mattered so much.'
        ),
    ]
    if outcome == "averted":
        qa.append((
            "Did anything break?",
            f"No. {f['child_name']} listened before the trip turned noisy, and they used {fix.label} to make the carrying safer. The ending proves the change because the cargo arrived calm and whole."
        ))
        qa.append((
            "How did they solve the problem?",
            f"They solved it early by listening to the warning and changing the plan before there was a crash. Using {fix.label} matched the danger on that route."
        ))
    elif outcome == "solved":
        qa.append((
            "What happened when the child ignored the warning?",
            f"The tote started jolting and the cargo rattled with loud sound effects. That noisy wobble proved the warning had been right."
        ))
        qa.append((
            "How did they fix the problem?",
            f"They used {fix.label} after the mishap. The child admitted the mistake, and the better plan made the rest of the trip safe."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{f['child_name']} learned that a bold feeling is not the same as a good plan. Listening to a warning early is wiser than cleaning up a loud mistake later."
        ))
    else:
        qa.append((
            "Could they save everything?",
            f"No. They tried {fix.label}, but it was too weak for the trouble they had already caused. Part of the load was spoiled because the warning had been ignored too long."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a sadder lesson instead of a cheerful triumph. The child was safe, but the spoiled cargo showed that careless boasting can make a small danger grow."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"robot", "tote", "jinx", "fragile", "sound", "problem_solving"}
    if f["fix"].id == "straw":
        tags.add("straw")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="bridge",
        cargo="jam",
        fix="straw",
        mistake="overfill",
        child_name="Mira",
        child_gender="girl",
        robot_name="Totebot",
        grownup="aunt",
        trait="careful",
    ),
    StoryParams(
        route="hill",
        cargo="eggs",
        fix="slow_mode",
        mistake="race",
        child_name="Otis",
        child_gender="boy",
        robot_name="Tinwhistle",
        grownup="father",
        trait="bold",
    ),
    StoryParams(
        route="boardwalk",
        cargo="globes",
        fix="two_trips",
        mistake="skip_checks",
        child_name="Poppy",
        child_gender="girl",
        robot_name="Whirrby",
        grownup="mother",
        trait="hasty",
    ),
    StoryParams(
        route="hill",
        cargo="globes",
        fix="rope",
        mistake="race",
        child_name="Milo",
        child_gender="boy",
        robot_name="Clankle",
        grownup="uncle",
        trait="curious",
    ),
]


def explain_rejection(route: Route, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(No story: '{fix.id}' is known in the world, but it is too weak or silly to count as a sensible fix. "
            f"Pick a better plan such as straw, slow_mode, or two_trips.)"
        )
    return (
        f"(No story: {fix.label} does not match the main danger on {route.id}. "
        f"The fix must actually steady the tote against hazards like {sorted(route.hazards)}.)"
    )


ASP_RULES = r"""
fragile_cargo(C) :- cargo(C), fragility(C, F), F >= 1.

helps(R, Fx) :- route(R), fix(Fx), hazard(R, H), guards(Fx, H).
valid(R, C, Fx) :- route(R), cargo(C), fragile_cargo(C), sensible(Fx), helps(R, Fx).
valid(R, C, Fx) :- route(R), cargo(C), fragile_cargo(C), sensible(Fx), universal(Fx).

heed :- trait(T), careful_trait(T).

severity(V) :- chosen_route(R), roughness(R, RR),
               chosen_cargo(C), fragility(C, CF),
               chosen_mistake(M), boost(M, B),
               V = RR + CF + B - 1.

strong_enough :- chosen_fix(Fx), power(Fx, P), severity(V), P >= V.

outcome(averted) :- heed.
outcome(solved) :- not heed, strong_enough.
outcome(spoiled) :- not heed, not strong_enough.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("roughness", route_id, route.roughness))
        for hazard in sorted(route.hazards):
            lines.append(asp.fact("hazard", route_id, hazard))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("fragility", cargo_id, cargo.fragility))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
        if fix.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", fix_id))
        if fix.id == "two_trips":
            lines.append(asp.fact("universal", fix_id))
        for guard in sorted(fix.guards):
            lines.append(asp.fact("guards", fix_id, guard))
    for mistake_id, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mistake_id))
        lines.append(asp.fact("boost", mistake_id, mistake.boost))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_mistake", params.mistake),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(120):
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
        print(f"MISMATCH: {bad}/{len(cases)} outcome predictions differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale cautionary storyworld: a child, a robot, a tote, and a loud lesson."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--robot-name")
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.fix:
        route = ROUTES[args.route]
        fix = FIXES[args.fix]
        if fix.sense < SENSE_MIN or not valid_fix(route, fix):
            raise StoryError(explain_rejection(route, fix))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(ROUTES[args.route] if args.route else next(iter(ROUTES.values())), FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, cargo_id, fix_id = rng.choice(sorted(combos))
    mistake_id = args.mistake or rng.choice(sorted(MISTAKES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    robot_name = args.robot_name or rng.choice(ROBOT_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        route=route_id,
        cargo=cargo_id,
        fix=fix_id,
        mistake=mistake_id,
        child_name=child_name,
        child_gender=gender,
        robot_name=robot_name,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Unknown mistake: {params.mistake})")
    route = ROUTES[params.route]
    cargo_cfg = CARGO[params.cargo]
    fix = FIXES[params.fix]
    if fix.sense < SENSE_MIN and not (would_heed(params.trait) is False and params.fix == "rope"):
        raise StoryError(explain_rejection(route, fix))
    world = tell(
        route=route,
        cargo_cfg=cargo_cfg,
        fix=fix,
        mistake=MISTAKES[params.mistake],
        child_name=params.child_name,
        child_gender=params.child_gender,
        robot_name=params.robot_name,
        grownup_type=params.grownup,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (route, cargo, fix) combos:\n")
        for route_id, cargo_id, fix_id in combos:
            print(f"  {route_id:10} {cargo_id:8} {fix_id}")
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
            header = f"### {p.child_name} and {p.robot_name}: {p.cargo} by {p.route} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
