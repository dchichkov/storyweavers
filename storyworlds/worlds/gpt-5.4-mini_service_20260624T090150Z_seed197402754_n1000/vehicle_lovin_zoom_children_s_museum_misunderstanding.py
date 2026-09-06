#!/usr/bin/env python3
"""
A small storyworld about a children's museum visit with a pirate-tale feel:
a lovable vehicle, a zoomy mishap, a misunderstanding, some humor, and a
problem-solving turn that fixes the day.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StorySample  # noqa: E402

MUSEUM_ROOMS = ["the ship room", "the wheel room", "the build room", "the map nook"]
VEHICLE_TYPES = ["car", "truck", "bus", "boat", "train"]
HERO_NAMES = ["Milo", "Nina", "Pip", "Tia", "Jules", "Rory", "Luna", "Benny"]
GROWNUP_NAMES = ["Captain Ada", "Mr. Finch", "Mara", "Captain Bea"]


@dataclass
class StoryParams:
    vehicle: str
    hero: str
    grownup: str
    room: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class StoryArc:
    premise: str
    trouble: str
    mistaken_belief: str
    actual_cause: str
    clue: str
    test: str
    child_action: str
    grownup_action: str
    solution: str
    result: str
    ending_image: str
    worried_line: str
    explanation_line: str


ARCS = [
    StoryArc(
        premise="carry paper treasure tickets to a pretend harbor",
        trouble="a fanfare of tickets whirled beneath the climbing nets",
        mistaken_belief="the vehicle had been shoved much too hard",
        actual_cause="an air vent had blown across the track",
        clue="the ribbon flags fluttered even after the vehicle stopped",
        test="held one ticket beside the quiet vehicle and watched it lift in the breeze",
        child_action="gathered the scattered tickets into a cargo basket",
        grownup_action="turned the track away from the vent",
        solution="they built a low cardboard tunnel that sheltered the ticket route",
        result="the next cargo arrived without losing a single ticket",
        ending_image="a neat row of ticket flags waved above the pretend harbor",
        worried_line="Avast! That push sent the treasure flying!",
        explanation_line="The vehicle stopped, but the wind kept zooming. Let's test the breeze.",
    ),
    StoryArc(
        premise="deliver foam bricks to a half-built pirate fort",
        trouble="the brass exhibit bell clanged whenever the wheels crossed one floorboard",
        mistaken_belief="the vehicle kept bumping the museum bell",
        actual_cause="a loose bell stand was trembling with the floor",
        clue="the bell rang once more while the parked vehicle sat far away",
        test="tapped the springy floorboard with one sneaker and heard the same clang",
        child_action="laid a felt square beneath the wobbly stand",
        grownup_action="held the bell steady while the felt was tucked in",
        solution="they marked a gentle cargo lane beside the firm floorboards",
        result="the bricks reached the fort and the bell stayed peacefully still",
        ending_image="the finished foam fort stood under a silent golden bell",
        worried_line="Hold fast! Are those wheels striking the bell?",
        explanation_line="It clangs when the vehicle is parked. The floor may be telling the bell to move.",
    ),
    StoryArc(
        premise="search for a missing foam ship's wheel",
        trouble="the treasured wheel vanished just as the vehicle zoomed past its display",
        mistaken_belief="the child had tucked the wheel into the vehicle for a joke",
        actual_cause="the wheel's magnet had snapped onto the metal axle",
        clue="one side of the vehicle wobbled and made a soft scraping sound",
        test="rolled the vehicle backward slowly and saw a blue edge turn underneath",
        child_action="lifted the vehicle only after asking for help",
        grownup_action="slid the foam wheel safely off the axle",
        solution="they returned the wheel and placed a wooden tray beside its magnetic display",
        result="the vehicle rolled evenly and the ship's wheel stayed in its tray",
        ending_image="the blue wheel gleamed beside four straight wheel tracks",
        worried_line="Oh, barnacles! Did that missing wheel sail away in your cargo?",
        explanation_line="I didn't hide it. Listen to this scrape beneath the vehicle.",
    ),
    StoryArc(
        premise="race a moon-message toward the museum lighthouse",
        trouble="an enormous vehicle-shaped shadow leaped across the painted sea wall",
        mistaken_belief="the vehicle had somehow climbed onto the mural",
        actual_cause="a lighthouse projector was shining through its spinning wheels",
        clue="the giant shadow copied every tiny turn without leaving the wall",
        test="covered one wheel with the treasure map and watched half the shadow disappear",
        child_action="angled the track so the wheels missed the beam",
        grownup_action="lowered the projector toward the lighthouse lens",
        solution="they made a shadow cove where visitors could safely test shapes",
        result="the moon-message reached the lighthouse while the shadow stayed in its cove",
        ending_image="a round moon and a tiny wheel-shadow rested side by side on the wall",
        worried_line="Shiver me timbers! Is the vehicle climbing the painted ocean?",
        explanation_line="Only its shadow is zooming up there. Watch what happens when I block the light.",
    ),
    StoryArc(
        premise="bring a pretend lunch to a sleepy museum dinosaur",
        trouble="a mighty dinosaur roar burst out at every fast pass",
        mistaken_belief="the child was secretly pressing the roar button",
        actual_cause="the vehicle's wheel was crossing a hidden floor sensor",
        clue="a little footprint symbol blinked exactly when the dinosaur roared",
        test="pressed the marked tile with one hand while the vehicle waited",
        child_action="drew a curving route around the sensor with rope",
        grownup_action="made a sign showing where visitors could trigger the roar on purpose",
        solution="they separated the quiet delivery lane from the roaring discovery tile",
        result="the lunch arrived softly, then everyone chose when to hear one grand roar",
        ending_image="the vehicle rested by the dinosaur's toes beneath a bright ROAR HERE sign",
        worried_line="That roar may frighten someone. Did you press the sound button?",
        explanation_line="My hands were steering. I think the wheel found a button in the floor.",
    ),
    StoryArc(
        premise="tow a key to the locked treasure chest",
        trouble="the large wooden key disappeared halfway across the room",
        mistaken_belief="the child had dropped the key behind an exhibit",
        actual_cause="the key's loop had hooked around the rear axle",
        clue="the vehicle made a tiny clack each time its back wheels turned",
        test="pulled it one handspan at a time and followed the clacking sound",
        child_action="stopped the vehicle before the loop could tighten",
        grownup_action="unhooked the key while keeping the wheels still",
        solution="they tied the key upright in a bright red cargo cup",
        result="the key reached the chest and opened it with a cheerful click",
        ending_image="gold paper stars spilled around the parked vehicle and its red cup",
        worried_line="The key is gone! Did it tumble behind the map case?",
        explanation_line="Wait and hear that clack. The vehicle may be carrying the key where we can't see it.",
    ),
    StoryArc(
        premise="unroll a blue-cloth sea for a pirate puppet show",
        trouble="a blue wave streamed behind the vehicle and covered the path",
        mistaken_belief="a cup of water had spilled across the museum floor",
        actual_cause="the folded sea cloth had caught on the cargo hook",
        clue="the blue trail was dry and had silver fish sewn along its edge",
        test="pinched one silver fish and lifted the cloth from the floor",
        child_action="reeled the cloth onto a cardboard tube",
        grownup_action="fastened the tube across the vehicle like a safe sail",
        solution="they rolled out the sea together from the puppet-stage dock",
        result="the path stayed clear and the whole blue ocean opened without a wrinkle",
        ending_image="silver fish shimmered in the cloth sea beside the docked vehicle",
        worried_line="Stop the zoom! I think water is spreading across the floor!",
        explanation_line="It isn't wet. These fish belong to the puppet sea.",
    ),
    StoryArc(
        premise="carry a rescue rope across a foam-block bridge",
        trouble="the bridge folded down before the vehicle reached the middle",
        mistaken_belief="the zooming vehicle had knocked the bridge apart",
        actual_cause="one support peg had already rolled beneath a bench",
        clue="an empty round hole showed where the missing support belonged",
        test="compared the two bridge sides and counted one fewer peg",
        child_action="spotted the runaway peg by following its dusty track",
        grownup_action="kept the bridge level as the peg went back in",
        solution="they rebuilt the crossing and tested it first with one foam block",
        result="the rescue rope crossed a bridge that stayed firm",
        ending_image="three foam flags stood proudly along the repaired bridge",
        worried_line="Easy there! Did the vehicle knock our bridge down?",
        explanation_line="It never touched the bridge. This empty peg-hole is our clue.",
    ),
    StoryArc(
        premise="lead a make-believe pirate parade to the map nook",
        trouble="the vehicle seemed to zoom the wrong way around every arrow",
        mistaken_belief="the child was ignoring the parade route",
        actual_cause="a nearby fan had flipped the loose arrow cards face down",
        clue="anchor stickers on the backs pointed opposite the arrows on the fronts",
        test="switched off the fan for a moment and watched the cards lie flat",
        child_action="matched every anchor sticker to the next parade station",
        grownup_action="clipped the arrow cards securely to the route rope",
        solution="they walked the corrected route together before restarting the parade",
        result="the vehicle led every pirate straight to the map nook",
        ending_image="a line of paper hats followed the clipped arrows to a red X",
        worried_line="Our captain is steering against every arrow!",
        explanation_line="The anchors disagree with the arrows. Maybe the wind turned our signs over.",
    ),
    StoryArc(
        premise="deliver a blanket to a sleeping baby-doll cabin",
        trouble="a recorded squawk sounded whenever the vehicle passed the doorway",
        mistaken_belief="the child was waking the doll by touching the sound controls",
        actual_cause="one wheel was pressing a floor button hidden under the rug",
        clue="a small bump under the rug matched the round sound button",
        test="lifted the rug corner and pressed the button while the vehicle waited",
        child_action="made a quiet detour from flat puzzle pieces",
        grownup_action="moved the rug so the discovery button remained visible",
        solution="they used the detour for the blanket delivery and left the button free for play",
        result="the blanket reached the cabin without another surprise squawk",
        ending_image="the doll lay tucked in while the vehicle waited beside a moon-shaped path",
        worried_line="Hush! Are you pressing the controls beside the sleeping cabin?",
        explanation_line="Both my hands are here. I felt a bump under that rug when the wheel passed.",
    ),
    StoryArc(
        premise="signal a cardboard island with a shiny message disk",
        trouble="the lighthouse flashed wildly whenever the vehicle turned",
        mistaken_belief="the child had switched the exhibit to storm mode",
        actual_cause="a polished hubcap was bouncing light into the lighthouse sensor",
        clue="each flash matched the moment the shiny wheel faced the lamp",
        test="held a pirate scarf over the hubcap and saw the flashing stop",
        child_action="wrapped the message disk in cloth until delivery time",
        grownup_action="shifted the lamp so it no longer faced the track",
        solution="they made one marked signal station where reflections could be tried safely",
        result="the island received three calm flashes instead of a wild storm",
        ending_image="three dots of light glowed above the vehicle on the cardboard shore",
        worried_line="Who turned the lighthouse into a storm signal?",
        explanation_line="Nobody touched the switch. The shiny wheel flashes back at the lamp.",
    ),
    StoryArc(
        premise="answer a puppet captain's call for a rescue vehicle",
        trouble="a siren chirped and the curtain opened before the show was ready",
        mistaken_belief="the child had taken an emergency prop without permission",
        actual_cause="the vehicle had rolled onto the storyteller's start mark",
        clue="a taped star beneath its front wheel said PARK RESCUE HERE",
        test="rolled off the star and heard the siren stop at once",
        child_action="asked the puppet captain when the rescue should begin",
        grownup_action="reset the curtain and invited the waiting children to count down",
        solution="they parked beside the star until the audience gave the call, 'Rescue away'",
        result="the vehicle entered on cue and saved the puppet ship",
        ending_image="the rescued puppet crew waved from a curtain full of paper stars",
        worried_line="That siren means the show has started. Did we borrow its rescue prop?",
        explanation_line="I think the floor invited the vehicle. Look at the star under its wheel.",
    ),
]


OPENINGS = [
    "At the children's museum, {hero} tied on a paper pirate hat and chose a lovable {vehicle} for the day's quest.",
    "The doors of the children's museum opened, and {hero} hurried with {grownup} toward a lovable {vehicle} waiting in {room}.",
    "In {room} at the children's museum, {hero} discovered a lovable {vehicle} with wheels ready for a pretend voyage.",
    "{hero} and {grownup} entered the children's museum as a two-person pirate crew, then found a lovable {vehicle} in {room}.",
    "A bell welcomed {hero} to the children's museum, where a lovable {vehicle} waited in {room} like a tiny ship in port.",
    "Today's treasure hunt began inside the children's museum, in {room}: {hero}, {grownup}, and one lovable {vehicle} made a cheerful crew.",
]


HUMOR_LINES = [
    "{grownup} called the flying tickets the fastest paper crew on the seven seas.",
    "The bell gave one last tiny ding, as if it were apologizing for all the fuss.",
    "{hero} laughed that the vehicle had been wearing the missing wheel like a bracelet.",
    "The giant shadow looked as though it wanted a pirate hat of its own.",
    "{hero} bowed to the dinosaur and said, 'A loud review for such a quiet lunch!'",
    "{grownup} called the hidden key a very clanky hitchhiker.",
    "'Good,' said {hero}, 'because this ocean is much too big for a mop.'",
    "They named the runaway support Captain Peg, the pirate who hid under benches.",
    "{grownup} told the arrows they needed a better captain than the fan.",
    "The baby doll slept through the whole investigation, which made {hero} giggle.",
    "The lighthouse gave one polite wink when the shiny wheel was finally covered.",
    "The puppet captain saluted so hard that its paper hat slipped over one eye.",
]


ACTION_FORMS = [
    (
        "{grownup} raised a hand. '{worried_line}'",
        "{hero} took a breath. '{explanation_line}'",
    ),
    (
        "'{worried_line}' asked {grownup}, kneeling beside the track.",
        "{hero} pointed to the clue. '{explanation_line}'",
    ),
    (
        "{grownup} called, '{worried_line}' and the little crew paused.",
        "'Let's look before we blame the zoom,' said {hero}. '{explanation_line}'",
    ),
    (
        "The worried {grownup} asked, '{worried_line}'",
        "'We can solve the misunderstanding,' {hero} replied. '{explanation_line}'",
    ),
    (
        "'{worried_line}' cried {grownup}. The adventure stopped for one careful moment.",
        "{hero} answered softly, '{explanation_line}'",
    ),
    (
        "{grownup} frowned at the surprise. '{worried_line}'",
        "{hero} did not argue; instead, the young captain said, '{explanation_line}'",
    ),
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character":
            return "they"
        return "it"


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Children's museum pirate-tale storyworld.")
    ap.add_argument("--vehicle", choices=VEHICLE_TYPES)
    ap.add_argument("--hero")
    ap.add_argument("--grownup")
    ap.add_argument("--room", choices=MUSEUM_ROOMS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    vehicle = args.vehicle or rng.choice(VEHICLE_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    room = args.room or rng.choice(MUSEUM_ROOMS)
    return StoryParams(vehicle=vehicle, hero=hero, grownup=grownup, room=room)


def asp_facts() -> str:
    import asp
    lines = []
    for v in VEHICLE_TYPES:
        lines.append(asp.fact("vehicle", v))
    for r in MUSEUM_ROOMS:
        lines.append(asp.fact("room", r))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("feature", "humor"))
    lines.append(asp.fact("feature", "problem_solving"))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(V,R) :- vehicle(V), room(R).
humor(V) :- vehicle(V).
problem_solving(V,R) :- vehicle(V), room(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show humor/1.\n#show problem_solving/2."))
    got_m = set(asp.atoms(model, "misunderstanding"))
    got_h = set(asp.atoms(model, "humor"))
    got_p = set(asp.atoms(model, "problem_solving"))
    want_m = {(v, r) for v in VEHICLE_TYPES for r in MUSEUM_ROOMS}
    want_h = {(v,) for v in VEHICLE_TYPES}
    want_p = {(v, r) for v in VEHICLE_TYPES for r in MUSEUM_ROOMS}
    ok = got_m == want_m and got_h == want_h and got_p == want_p
    if ok:
        print("OK: ASP parity matches Python registries.")
        return 0
    print("Mismatch between ASP and Python registries.")
    return 1


def story_variation(params: StoryParams) -> int:
    if params.seed is not None:
        seed = params.seed
    else:
        stable_text = "|".join((params.vehicle, params.hero, params.grownup, params.room))
        seed = sum((index + 1) * ord(char) for index, char in enumerate(stable_text))
    return (seed * 137 + 59) % (len(ARCS) * len(OPENINGS) * len(ACTION_FORMS))


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(id="hero", kind="character", label=params.hero, type="child", memes={"joy": 1.0}))
    grownup = world.add(Entity(id="grownup", kind="character", label=params.grownup, type="adult"))
    vehicle = world.add(Entity(id="vehicle", kind="thing", label=params.vehicle, type=params.vehicle, meters={"speed": 0.0}, memes={"lovin": 1.0}))
    return world


def generate_story(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    grownup = world.entities["grownup"]
    vehicle = world.entities["vehicle"]
    variation = story_variation(p)
    arc_index = variation % len(ARCS)
    arc = ARCS[arc_index]
    variation //= len(ARCS)
    opening = OPENINGS[variation % len(OPENINGS)].format(
        hero=p.hero, grownup=p.grownup, vehicle=p.vehicle, room=p.room
    )
    variation //= len(OPENINGS)
    grownup_line, hero_line = ACTION_FORMS[variation % len(ACTION_FORMS)]

    world.say(opening)
    world.say(
        f"{p.hero} was a vehicle-lovin' young captain and patted the {p.vehicle}'s side. "
        f"'Ready to zoom,' {p.hero} said. The crew's mission was to {arc.premise}."
    )

    world.para()
    world.say(
        f"The {p.vehicle} began to zoom through {p.room}. Then {arc.trouble}."
    )
    vehicle.meters["speed"] = 1.0
    hero.memes["excited"] = 1.0
    world.say(
        grownup_line.format(
            hero=p.hero,
            grownup=p.grownup,
            worried_line=arc.worried_line,
            explanation_line=arc.explanation_line,
        )
    )
    world.say(
        f"For one uneasy moment, the misunderstanding was that {arc.mistaken_belief}."
    )
    hero.memes["worry"] = 1.0
    grownup.memes["mistaken"] = 1.0
    world.facts["misunderstanding"] = True

    world.para()
    world.say(
        hero_line.format(
            hero=p.hero,
            grownup=p.grownup,
            worried_line=arc.worried_line,
            explanation_line=arc.explanation_line,
        )
    )
    world.say(f"The useful clue was that {arc.clue}.")
    world.say(f"To check instead of guessing, {p.hero} {arc.test}.")
    world.say(f"Now they understood: {arc.actual_cause}.")
    humor_line = HUMOR_LINES[arc_index].format(hero=p.hero, grownup=p.grownup)
    world.say(humor_line)
    grownup.memes["mistaken"] = 0.0
    hero.memes["curious"] = 1.0

    world.para()
    world.say(f"{p.hero} {arc.child_action}, and {p.grownup} {arc.grownup_action}.")
    world.say(f"Their plan worked: {arc.solution}.")
    world.say(f"Soon {arc.result}.")
    world.say(
        f"With the misunderstanding settled, {p.hero} gave the lovable vehicle one last careful zoom. "
        f"At closing time, {arc.ending_image}."
    )
    vehicle.meters["speed"] = 0.25
    hero.memes["proud"] = 1.0
    hero.memes["joy"] = 2.0
    grownup.memes["joy"] = 1.0
    world.facts.update(
        {
            "premise": arc.premise,
            "trouble": arc.trouble,
            "mistaken_belief": arc.mistaken_belief,
            "actual_cause": arc.actual_cause,
            "clue": arc.clue,
            "test": arc.test,
            "child_action": arc.child_action,
            "grownup_action": arc.grownup_action,
            "solution": arc.solution,
            "result": arc.result,
            "ending_image": arc.ending_image,
            "humor_line": humor_line,
            "problem_solving": True,
            "humor": True,
            "settled": True,
        }
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a pirate-style story for children about {p.hero}, a lovable {p.vehicle}, and a misunderstanding at {p.room}. Their mission is to {world.facts['premise']}.",
        f"Tell a funny museum tale where a vehicle-lovin' child makes a {p.vehicle} zoom, {p.grownup} worries, and careful clues solve the misunderstanding.",
        f"Create a short story with the words vehicle, lovin, and zoom, set in a children's museum and ending in a happy fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    facts = world.facts
    return [
        QAItem(
            question=f"What mission did {p.hero} choose for the {p.vehicle} in {p.room}?",
            answer=f"{p.hero} chose to {facts['premise']}. The lovable {p.vehicle} was the crew's special vehicle for that mission.",
        ),
        QAItem(
            question=f"What really caused the trouble while {p.hero}'s {p.vehicle} zoomed through {p.room}?",
            answer=f"{p.grownup} learned that the real cause was that {facts['actual_cause']}. {p.hero} investigated after noticing that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.grownup} make the {p.vehicle}'s museum mission work?",
            answer=f"In {p.room}, {p.hero} {facts['child_action']}, while {p.grownup} {facts['grownup_action']}. Together, {facts['solution']}.",
        ),
        QAItem(
            question=f"What did {p.hero} and {p.grownup} see at the end of the {p.vehicle}'s adventure in {p.room}?",
            answer=f"By closing time, {facts['ending_image']}. {p.hero} and {p.grownup} could see that the misunderstanding was settled and the museum mission had worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vehicle?",
            answer="A vehicle is something that helps people or things move from one place to another, like a car, truck, train, or boat.",
        ),
        QAItem(
            question="What does it mean to zoom?",
            answer="To zoom means to move very fast, like when a toy car races across the floor.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is happening, but they do not have the right idea at first.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.label} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(vehicle="boat", hero="Pip", grownup="Captain Ada", room="the ship room"),
    StoryParams(vehicle="car", hero="Milo", grownup="Mara", room="the wheel room"),
    StoryParams(vehicle="train", hero="Nina", grownup="Mr. Finch", room="the build room"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/2.\n#show humor/1.\n#show problem_solving/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2.\n#show humor/1.\n#show problem_solving/2."))
        print(f"misunderstanding={len(asp.atoms(model, 'misunderstanding'))}")
        print(f"humor={len(asp.atoms(model, 'humor'))}")
        print(f"problem_solving={len(asp.atoms(model, 'problem_solving'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero} and the {p.vehicle} at {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
