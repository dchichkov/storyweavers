#!/usr/bin/env python3
"""
A standalone storyworld: a fable about chair trouble, sound effects, and a
flashback-guided solution.

The seed premise:
A small creature in a simple home has a favorite chair that starts to wobble.
The creature remembers an older lesson, listens to the chair's noises, and
solves the problem with care instead of force.

The story world is intentionally small and classical, but its state can select
many different chair problems, clues, remembered lessons, repairs, and endings.

This file follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Room:
    name: str = "the kitchen"
    light: str = "warm"


@dataclass
class Character:
    name: str
    kind: str
    trait: str
    meme: dict[str, float] = field(default_factory=dict)


@dataclass
class Chair:
    name: str = "the chair"
    material: str = "wood"
    wobble: float = 0.0
    creak: float = 0.0
    fixed: bool = False
    leg_tightness: float = 0.35
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    room: str
    chair_material: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "kitchen": Room(name="the kitchen", light="warm"),
    "porch": Room(name="the porch", light="golden"),
    "workshop": Room(name="the workshop", light="dusty"),
}

ROOM_PHRASES = {
    "kitchen": "in the kitchen",
    "porch": "on the porch",
    "workshop": "in the workshop",
}

KINDS = ["fox", "mouse", "rabbit", "crow", "hedgehog"]
TRAITS = ["wise", "patient", "careful", "gentle", "brave"]

MATERIALS = {
    "wood": ("wooden", "wood"),
    "pine": ("pine", "pine"),
    "oak": ("oak", "oak"),
}

NAMES = {
    "fox": ["Fenn", "Mira", "Tavi"],
    "mouse": ["Nim", "Pip", "Moss"],
    "rabbit": ["Luna", "Bram", "Tilly"],
    "crow": ["Corin", "Sable", "Jett"],
    "hedgehog": ["Pebb", "Tansy", "Brio"],
}


@dataclass(frozen=True)
class RepairArc:
    use: str
    trigger: str
    sound: str
    comparison: str
    symptom: str
    inspection: str
    cause: str
    obstacle: str
    action: str
    result: str
    ending: str
    tool: str


REPAIR_ARCS = [
    RepairArc(
        use="drawing maps at the table",
        trigger="a gust rattled the open window",
        sound="creak-creak",
        comparison="a frog clearing its throat",
        symptom="the left back leg rocked whenever weight shifted",
        inspection="pressed each corner and watched the left back joint open a hair",
        cause="a screw in the left back leg had worked loose",
        obstacle="The screw turned once, then stuck beneath a cap of dust",
        action="brushed the dust away and tightened the screw with a small wrench",
        result="the four legs stood square and the wobble vanished",
        ending="a cup of crayons stood still while a new map curled beside it",
        tool="small wrench",
    ),
    RepairArc(
        use="shelling peas beside the window",
        trigger="a pea rolled beneath one foot",
        sound="tick-tock-tick",
        comparison="a tiny clock in a hurry",
        symptom="the front foot clicked against the floor",
        inspection="slid a ribbon under each foot and found a shallow dip in the floorboard",
        cause="the floor was uneven beneath the front chair leg",
        obstacle="A thick wooden shim made the chair lean the other way",
        action="trimmed a thin square of cork and tucked it beneath the front foot",
        result="the cork filled the dip without lifting the chair too high",
        ending="three round peas rested on the seat without rolling away",
        tool="cork square",
    ),
    RepairArc(
        use="reading fables after supper",
        trigger="the chair was dragged too close to the wall",
        sound="scritch-scrape",
        comparison="a cricket bowing a rough little fiddle",
        symptom="a pale mark appeared whenever the chair leaned back",
        inspection="held a candle low and saw the top rail brushing the plaster",
        cause="the chair back was scraping the wall, not breaking inside",
        obstacle="Moving it forward left one leg perched on the edge of the rug",
        action="shifted the rug and set a felt pad behind the top rail",
        result="the chair had room to rest without touching wall or rug edge",
        ending="the candle flame and the chair's shadow both held perfectly still",
        tool="felt pad",
    ),
    RepairArc(
        use="mending a little red scarf",
        trigger="a dropped spool bounced against the lower rung",
        sound="tok-clack",
        comparison="two acorns knocking hats",
        symptom="the lower rung slipped sideways when nudged",
        inspection="followed the sound with one paw and found the rung half out of its socket",
        cause="the crossbar peg had crept out of its wooden socket",
        obstacle="Pushing the rung directly only made it spring out again",
        action="wrapped the peg with a drop of glue and tied it snug while it dried",
        result="the rung settled deep in its socket and held firm",
        ending="the finished red scarf hung from a rung that did not clack once",
        tool="glue and soft cord",
    ),
    RepairArc(
        use="sorting buttons into bright rows",
        trigger="a blue button vanished near the rocker",
        sound="grr-rip, grr-rip",
        comparison="a sleepy bear scratching a door",
        symptom="one rocker rasped only halfway through its swing",
        inspection="tilted the chair safely and traced a fresh line beneath the curved runner",
        cause="a flat pebble was trapped beneath the rocking runner",
        obstacle="The pebble was wedged too tightly to pinch out with a paw",
        action="lifted the runner with a wooden spoon and swept the pebble free",
        result="the rocker traveled in a smooth, quiet arc",
        ending="the rescued blue button rode on the seat through three silent rocks",
        tool="wooden spoon",
    ),
    RepairArc(
        use="watching rain bead on the door",
        trigger="yesterday's damp breeze had blown through the room",
        sound="eee-awk",
        comparison="a gull complaining over an empty shore",
        symptom="the seat squealed at one joint but did not wobble",
        inspection="placed one finger on each joint and felt the dry right joint shiver",
        cause="the clean wooden joint had dried and begun rubbing",
        obstacle="Pouring oil everywhere would have made the seat slippery and messy",
        action="rubbed one tiny dab of beeswax into the noisy joint",
        result="the protected joint moved freely without staining the seat",
        ending="rain tapped the window, now the only sound beside the chair",
        tool="beeswax",
    ),
    RepairArc(
        use="weaving a basket for apples",
        trigger="the basket handle caught the edge of the woven seat",
        sound="fip-fip-pop",
        comparison="raindrops hopping from a leaf",
        symptom="one cane strip lifted whenever the seat was pressed",
        inspection="ran a blunt needle along the weave and found one loose crossing",
        cause="a cane strip had slipped over instead of under its neighbor",
        obstacle="Pulling the strip straight made the gap wider",
        action="soaked the strip, wove it back under-over, and pinned it until dry",
        result="the crossing tightened into the same pattern as the rest",
        ending="one red apple sat above the repaired weave like a quiet lantern",
        tool="blunt needle and pin",
    ),
    RepairArc(
        use="practicing a song for the harvest supper",
        trigger="the highest note made something under the seat buzz",
        sound="bzzz-brum",
        comparison="a bee trapped inside a drum",
        symptom="the buzz stopped whenever the apron beneath the seat was touched",
        inspection="hummed each note slowly and located a loose wooden brace",
        cause="a small brace beneath the seat was vibrating against its peg",
        obstacle="A wad of cloth silenced the buzz but hid the loose brace",
        action="removed the cloth and pressed the brace onto a fresh cork peg",
        result="the brace held fast even when the highest note rang out",
        ending="the last clear note floated over a chair as quiet as moonlight",
        tool="fresh cork peg",
    ),
    RepairArc(
        use="painting a sign for the garden gate",
        trigger="the paint jar bumped the chair during cleanup",
        sound="tap...tap-tap",
        comparison="a woodpecker practicing very slowly",
        symptom="a decorative knob nodded atop the right post",
        inspection="covered the knob with a cloth and discovered it could turn by hand",
        cause="the top knob had loosened from its threaded post",
        obstacle="Bare paws slipped on the smooth round knob",
        action="gripped it through the cloth and turned it until the threads seated",
        result="the knob faced forward and no longer tapped",
        ending="the dry garden sign leaned against a chair crowned by one steady knob",
        tool="folded cloth",
    ),
    RepairArc(
        use="building a paper town on the seat",
        trigger="a paper tower toppled when the chair tilted",
        sound="thump-hush-thump",
        comparison="a giant tiptoeing in wool socks",
        symptom="one leg sank slightly whenever the chair stood on the soft mat",
        inspection="marked the four footprints and saw one deep hollow in the mat",
        cause="the thick mat compressed unevenly beneath the narrow chair feet",
        obstacle="Adding a block under one foot made the paper town slope",
        action="set a broad wooden board beneath all four chair feet",
        result="the board spread the weight evenly across the soft mat",
        ending="four paper houses remained upright beneath the evening lamp",
        tool="broad wooden board",
    ),
    RepairArc(
        use="polishing seed jars for spring",
        trigger="a full jar was set down harder than usual",
        sound="ping-ding",
        comparison="a spoon tapping a teacup",
        symptom="a tiny metal corner bracket chimed when the seat moved",
        inspection="held each bracket in turn and found one missing its wooden pin",
        cause="the bracket's small retaining pin had fallen out",
        obstacle="A metal nail was too sharp and too narrow for the old hole",
        action="shaped a smooth wooden peg and pressed it through the bracket",
        result="the broad peg held the bracket without scratching the chair",
        ending="the seed jars shone in a row above a bracket that made no reply",
        tool="smooth wooden peg",
    ),
    RepairArc(
        use="sharing berry cakes with a neighbor",
        trigger="the neighbor noticed one cake sliding toward the seat's edge",
        sound="whuff-click",
        comparison="a boot stepping out of soft mud",
        symptom="the removable cushion shifted whenever someone stood up",
        inspection="lifted the cushion and found one cloth tie pulled through its loop",
        cause="the cushion tie had come undone beneath the seat",
        obstacle="A tight knot held the cushion crooked and pinched its corner",
        action="loosened the knot, centered the cushion, and tied a gentle bow",
        result="the cushion stayed centered yet could still be removed for cleaning",
        ending="two berry-cake plates balanced beside a neat bow under the seat",
        tool="cushion tie",
    ),
]

FLASHBACKS = [
    ("Grandmother Reed", "listen twice before changing anything", "patient listening"),
    ("the village carpenter", "test one part at a time", "careful testing"),
    ("an old bridge keeper", "a sound points toward the place that moves", "following a sound"),
    ("their first basket lesson", "undo a poor fix before making a sound one", "correcting a mistaken fix"),
    ("a rainy-day repair", "the smallest clue can reveal the whole cause", "respecting small clues"),
    ("Father Rowan", "steady work beats one mighty shove", "using steady work"),
    ("the mill mouse", "name the cause before choosing the tool", "matching a tool to the cause"),
    ("a lesson beside the creek", "try gently, observe, and then try again", "gentle observation"),
]

OPENINGS = [
    "The chair had carried many quiet afternoons without complaint.",
    "It was not a grand chair, but it belonged in every happy memory of the room.",
    "Each scratch on the chair marked an old meal, game, or story.",
    "The chair was small enough for the room and sturdy enough to feel like a friend.",
    "Sunlight often found the chair before it found anything else.",
]

DIALOGUES = [
    '"A noise is a clue, not an enemy," {name} said.',
    '"I will ask what moved before I ask how to stop it," {name} whispered.',
    '"No thumping and no guessing," {name} decided. "First I will look."',
    '"Tell me where it hurts, little chair," {name} said, listening again.',
    '"Slow paws can solve what hurried paws miss," {name} reminded {self_ref}.',
]

ENDING_LESSONS = [
    "From then on, every odd sound received a question before it received a tool.",
    "The room seemed to agree that understanding is the first part of mending.",
    "That evening proved that careful minds can be stronger than forceful paws.",
    "Afterward, the smallest creak was treated as useful news, never a nuisance.",
    "And so patience left the chair stronger and its owner wiser.",
    "The lesson stayed: a good solution fits the cause as neatly as a key fits a lock.",
]

# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.hero: Optional[Character] = None
        self.chair = Chair()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        # meters and memes live on the chair as physical/emotional state
        self.chair.meters = {"wobble": 0.0, "fixedness": 0.0}
        self.chair.memes = {"trust": 0.0, "relief": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.room)
        other.hero = Character(
            name=self.hero.name if self.hero else "",
            kind=self.hero.kind if self.hero else "",
            trait=self.hero.trait if self.hero else "",
            meme=dict(self.hero.meme) if self.hero else {},
        )
        other.chair = Chair(
            name=self.chair.name,
            material=self.chair.material,
            wobble=self.chair.wobble,
            creak=self.chair.creak,
            fixed=self.chair.fixed,
            leg_tightness=self.chair.leg_tightness,
            meters=dict(self.chair.meters),
            memes=dict(self.chair.memes),
        )
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Causal logic
# ---------------------------------------------------------------------------
def chair_is_problematic(world: World) -> bool:
    return world.chair.wobble >= 1.0 or world.chair.creak >= 1.0


def listen_to_chair(world: World) -> None:
    if "listen" in world.fired:
        return
    world.fired.add("listen")
    world.chair.creak += 1.0
    world.chair.meters["wobble"] += 0.5
    arc = world.facts["arc"]
    world.say(f"The chair answered, {arc.sound}, like {arc.comparison}.")


def flashback(world: World) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")
    world.hero.meme["remembered"] = world.hero.meme.get("remembered", 0.0) + 1.0
    teacher, lesson, _ = world.facts["flashback"]
    world.say(
        f"The sound opened a flashback in {world.hero.name}'s mind. Long ago, "
        f"{teacher} had taught: {lesson}."
    )


def inspect(world: World) -> None:
    if "inspect" in world.fired:
        return
    world.fired.add("inspect")
    arc = world.facts["arc"]
    world.say(
        f"Instead of shaking the chair harder, {world.hero.name} {arc.inspection}. "
        f"The clue revealed the cause: {arc.cause}."
    )
    world.facts["cause_found"] = True


def solve(world: World) -> None:
    if "solve" in world.fired:
        return
    world.fired.add("solve")
    arc = world.facts["arc"]
    if world.facts.get("cause_found"):
        world.say(f"{arc.obstacle}. {world.facts['dialogue']}")
        world.say(f"So {world.hero.name} {arc.action}. {arc.result.capitalize()}.")
        world.chair.fixed = True
        world.chair.wobble = 0.0
        world.chair.creak = 0.0
        world.chair.meters["fixedness"] = 1.0
        world.chair.memes["trust"] = 1.0
        world.chair.memes["relief"] = 1.0
    else:
        raise StoryError("A repair cannot be chosen before the cause is found.")


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    if world.chair.fixed:
        arc = world.facts["arc"]
        world.say(
            f"To test the work, {world.hero.name} sat down gently. The chair stayed "
            f"steady and quiet; {arc.ending}. Later, {world.hero.name} told the adventure "
            f"as a fable about patient problem-solving. {world.facts['ending_lesson']}"
        )
    else:
        world.say(
            f"In the end, {world.hero.name} still stood by the chair, but the problem "
            f"had not yet been solved."
        )


def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    hero = Character(name=params.name, kind=params.kind, trait=params.trait)
    world.hero = hero
    world.chair.material = params.chair_material
    world.chair.name = "the chair"
    if params.seed is not None:
        choice = params.seed
    else:
        key = f"{params.name}|{params.kind}|{params.trait}|{params.room}|{params.chair_material}"
        choice = sum((i + 1) * ord(char) for i, char in enumerate(key))
    arc = REPAIR_ARCS[choice % len(REPAIR_ARCS)]
    remembered = FLASHBACKS[(choice // len(REPAIR_ARCS)) % len(FLASHBACKS)]
    opening = OPENINGS[(choice // (len(REPAIR_ARCS) * len(FLASHBACKS))) % len(OPENINGS)]
    dialogue_template = DIALOGUES[(choice * 7 + choice // 11) % len(DIALOGUES)]
    self_ref = "themself"
    world.facts.update(
        arc=arc,
        flashback=remembered,
        opening=opening,
        location_phrase=ROOM_PHRASES[params.room],
        dialogue=dialogue_template.format(name=hero.name, self_ref=self_ref),
        ending_lesson=ENDING_LESSONS[(choice * 5 + choice // 13) % len(ENDING_LESSONS)],
    )
    return world


def tell_story(world: World) -> None:
    hero = world.hero
    chair_word = f"{world.chair.material} chair"
    arc = world.facts["arc"]

    world.say(
        f"Once {world.facts['location_phrase']}, there lived a {hero.trait} little {hero.kind} "
        f"named {hero.name}."
    )
    world.say(
        f"{hero.name} loved the {chair_word} by the table, especially for "
        f"{arc.use}. {world.facts['opening']}"
    )

    world.para()
    world.say(
        f"One afternoon, {arc.trigger}, and the chair made a strange sound."
    )
    listen_to_chair(world)
    world.chair.wobble += 1.0
    if chair_is_problematic(world):
        world.say(
            f"{hero.name} listened from the front, the back, and underneath. "
            f"Soon {hero.name} noticed that {arc.symptom}. That was the real problem."
        )

    world.para()
    flashback(world)
    inspect(world)
    solve(world)

    world.para()
    conclude(world)
    world.facts.update(
        hero=hero,
        room=world.room,
        chair=world.chair,
        resolved=world.chair.fixed,
        problem=arc.symptom,
        cause=arc.cause,
        action=arc.action,
        result=arc.result,
        ending=arc.ending,
        tool=arc.tool,
        remembered_lesson=world.facts["flashback"][1],
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short fable about {hero.name}, the {f['chair'].material} chair, and the sound {f['arc'].sound}.",
        f"Tell a child-friendly problem-solving story {f['location_phrase']} where the clue is that {f['problem']}.",
        f"Write a flashback fable in which {hero.name} remembers to {f['remembered_lesson']} and uses {f['tool']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    chair = f["chair"]
    return [
        QAItem(
            question=f"What problem did {hero.name} notice with the {chair.material} chair {f['location_phrase']}?",
            answer=f"{hero.name} noticed that {f['problem']}. The sound {f['arc'].sound} helped locate the trouble.",
        ),
        QAItem(
            question=f"What did {hero.name} remember when the sound {f['arc'].sound} caused a flashback?",
            answer=(
                f"{hero.name} remembered how {f['flashback'][0]} taught the lesson to {f['remembered_lesson']}. "
                f"That memory kept {hero.name} from using force or guessing."
            ),
        ),
        QAItem(
            question=f"What caused the sound {f['arc'].sound} from the {chair.material} chair?",
            answer=(
                f"The sound came from this problem: {f['cause']}. "
                f"{hero.name} confirmed the cause by inspecting the chair carefully."
            ),
        ),
        QAItem(
            question=f"How did {hero.name} use {f['tool']} to solve the problem, and what proved it worked?",
            answer=(
                f"{hero.name.capitalize()} {f['action']}. Afterward, {f['result']}, and "
                f"the final image showed that {f['ending']}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a chair do?",
            answer="A chair is a piece of furniture that people or animals can sit on.",
        ),
        QAItem(
            question="What is a creak?",
            answer="A creak is a small squeaky sound that old or loose things can make when they move.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why is listening helpful when something seems broken?",
            answer="Listening can give clues about what is wrong, so you can choose the right fix instead of guessing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    chair = world.chair
    hero = world.hero
    return "\n".join(
        [
            "--- world model state ---",
            f"room={world.room.name}",
            f"hero={hero.name} ({hero.kind}, {hero.trait})",
            f"chair.material={chair.material}",
            f"problem={world.facts.get('problem')}",
            f"cause={world.facts.get('cause')}",
            f"tool={world.facts.get('tool')}",
            f"chair.wobble={chair.wobble}",
            f"chair.creak={chair.creak}",
            f"chair.fixed={chair.fixed}",
            f"chair.meters={chair.meters}",
            f"chair.memes={chair.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for kind in KINDS:
            for material in MATERIALS:
                combos.append((room, kind, material))
    return combos


ASP_RULES = r"""
room(Room) :- room_name(Room).
kind(Kind) :- kind_name(Kind).
material(Mat) :- material_name(Mat).

valid(Room, Kind, Mat) :- room(Room), kind(Kind), material(Mat).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room in ROOMS:
        lines.append(asp.fact("room_name", room))
    for kind in KINDS:
        lines.append(asp.fact("kind_name", kind))
    for material in MATERIALS:
        lines.append(asp.fact("material_name", material))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class _Args:
    room: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    material: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams(name="Mira", kind="fox", trait="wise", room="kitchen", chair_material="wood"),
    StoryParams(name="Nim", kind="mouse", trait="patient", room="porch", chair_material="oak"),
    StoryParams(name="Tilly", kind="rabbit", trait="gentle", room="workshop", chair_material="pine"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a chair, a problem, and a careful fix.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--material", choices=list(MATERIALS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    kind = args.kind or rng.choice(KINDS)
    trait = args.trait or rng.choice(TRAITS)
    material = args.material or rng.choice(list(MATERIALS))
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[kind])
    return StoryParams(name=name, kind=kind, trait=trait, room=room, chair_material=material)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:\n")
        for room, kind, material in triples:
            print(f"  {room:10} {kind:10} {material}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.kind} in {p.room} with {p.material} chair"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
