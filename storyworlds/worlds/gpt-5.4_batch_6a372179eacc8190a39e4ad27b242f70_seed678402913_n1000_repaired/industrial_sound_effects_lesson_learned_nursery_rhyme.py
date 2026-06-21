#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/industrial_sound_effects_lesson_learned_nursery_rhyme.py
===================================================================================

A small storyworld about a child visiting a busy workroom with a big industrial
machine. The machine sounds wonderful and looks tempting up close, but the child
must learn the gentle rule: loud, strong machines are for grown-up hands, and
small helpers stay back until the machine stops.

The prose aims for a nursery-rhyme feel: short beats, repeated sound effects,
and a clear little lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/industrial_sound_effects_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/industrial_sound_effects_lesson_learned_nursery_rhyme.py --place bakery --machine mixer
    python storyworlds/worlds/gpt-5.4/industrial_sound_effects_lesson_learned_nursery_rhyme.py --response round_window
    python storyworlds/worlds/gpt-5.4/industrial_sound_effects_lesson_learned_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/industrial_sound_effects_lesson_learned_nursery_rhyme.py --verify
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
SENSE_MIN = 2
CAUTIOUS_TRAITS = {"careful", "patient", "gentle"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    details: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    place_word: str
    sound: str
    hum: str
    hazards: set[str] = field(default_factory=set)
    features: set[str] = field(default_factory=set)
    lesson: str = ""
    safe_job: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)
    loudness: int = 1
    sprinkle_word: str = ""


@dataclass
class Response:
    id: str
    label: str
    sense: int
    guards: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    setup: str = ""
    safe_view: str = ""
    helper_line: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    child = world.get("child")
    if machine.meters["running"] < THRESHOLD or child.meters["near_machine"] < THRESHOLD:
        return out
    sig = ("noise", machine.id, child.id, child.meters["wearing_earmuffs"] >= THRESHOLD)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["noise"] += float(machine.attrs.get("loudness", 1))
    if child.meters["wearing_earmuffs"] < THRESHOLD:
        child.memes["startled"] += 1
        out.append("__startled__")
    return out


def _r_specks(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    child = world.get("child")
    if machine.meters["running"] < THRESHOLD or child.meters["near_machine"] < THRESHOLD:
        return out
    if "splash" not in machine.attrs.get("hazards", set()):
        return out
    sig = ("specks", machine.id, child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["speckled"] += 1
    out.append("__specks__")
    return out


CAUSAL_RULES = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="specks", tag="physical", apply=_r_specks),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if item.startswith("__"):
                continue
            world.say(item)
    return produced


def response_covers(machine: Machine, response: Response) -> bool:
    return response.guards >= machine.hazards and response.needs <= machine.features


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for machine_id in sorted(place.affords):
            machine = MACHINES[machine_id]
            for response_id, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and response_covers(machine, response):
                    combos.append((place_id, machine_id, response_id))
    return sorted(combos)


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_rejection(machine: Machine, response: Response) -> str:
    lacks = sorted(machine.hazards - response.guards)
    need = sorted(response.needs - machine.features)
    if lacks:
        return (
            f"(No story: {response.label} does not solve all the hazards of the "
            f"{machine.label}. It still leaves {', '.join(lacks)} unguarded.)"
        )
    if need:
        return (
            f"(No story: {response.label} needs {', '.join(need)}, but the "
            f"{machine.label} does not have that feature.)"
        )
    return "(No story: this machine and response do not make a sensible pair.)"


def child_listens(trait: str) -> bool:
    return trait in CAUTIOUS_TRAITS


def predict_oops(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    machine = sim.get("machine")
    child.meters["near_machine"] = 1
    machine.meters["running"] = 1
    produced = propagate(sim, narrate=False)
    return {
        "startled": sim.get("child").memes["startled"] >= THRESHOLD,
        "speckled": sim.get("child").meters["speckled"] >= THRESHOLD,
        "noise": sim.get("room").meters["noise"],
        "markers": list(produced),
    }


def introduce(world: World, child: Entity, adult: Entity, place: Place) -> None:
    trait = child.traits[0] if child.traits else "bright"
    world.say(
        f"{child.id}, a {trait} little {child.type}, skipped beside {child.pronoun('possessive')} "
        f"{adult.label_word} to {place.phrase}. {place.details}"
    )


def notice_machine(world: World, child: Entity, machine: Machine) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"There stood {machine.phrase}, big and shiny in the {machine.place_word}. "
        f'"{machine.sound}! {machine.sound}!" sang the room.'
    )


def tempt(world: World, child: Entity, machine: Machine) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'{child.id} clapped small hands. "What a grand industrial thing! May I go close?" '
        f'{child.pronoun().capitalize()} asked.'
    )


def warn(world: World, child: Entity, adult: Entity, machine: Machine) -> None:
    pred = predict_oops(world)
    world.facts["predicted_noise"] = int(pred["noise"])
    world.facts["predicted_startled"] = pred["startled"]
    world.facts["predicted_speckled"] = pred["speckled"]
    extra = ""
    if pred["speckled"]:
        sprinkle = machine.sprinkle_word or "specks"
        extra = f" and toss {sprinkle} into the air"
    world.say(
        f'{adult.label_word.capitalize()} shook {adult.pronoun("possessive")} head. '
        f'"Not close, little one. When this machine begins, it can roar{extra}. '
        f'We stay back until the strong work is done."'
    )


def edge_close(world: World, child: Entity) -> None:
    child.meters["near_machine"] = 1
    child.memes["defiance"] += 1
    world.say(
        f"But curiosity had quick feet. Tip-tap, tip-tap, {child.id} edged nearer to the yellow line."
    )


def start_machine(world: World, machine_ent: Entity, machine: Machine) -> None:
    machine_ent.meters["running"] = 1
    markers = propagate(world, narrate=False)
    world.facts["markers"] = markers
    world.say(
        f"Then the grown-up switch went down, and {machine.sound} went the {machine.label}; "
        f"{machine.hum} it rolled and rumbled."
    )


def startled_beat(world: World, child: Entity, machine: Machine) -> None:
    if child.memes["startled"] >= THRESHOLD and child.meters["speckled"] >= THRESHOLD:
        sprinkle = machine.sprinkle_word or "tiny specks"
        world.say(
            f"{child.id} jumped back. \"Oh!\" {child.pronoun()} cried, as {sprinkle} kissed "
            f"{child.pronoun('possessive')} sleeves."
        )
    elif child.memes["startled"] >= THRESHOLD:
        world.say(
            f"{child.id} jumped back with wide eyes. The sudden song was louder than {child.pronoun()} expected."
        )


def calm_and_stop(world: World, child: Entity, adult: Entity, machine_ent: Entity, response: Response) -> None:
    machine_ent.meters["running"] = 0
    child.meters["near_machine"] = 0
    child.memes["relief"] += 1
    adult.memes["calm"] += 1
    world.say(
        f'{adult.label_word.capitalize()} touched {child.pronoun("possessive")} shoulder and spoke soft and slow. '
        f'"Back we go. Strong machines need space."'
    )
    world.say(
        f"Click went the stop button, and the busy room grew kinder."
    )


def set_safeguard(world: World, child: Entity, adult: Entity, response: Response) -> None:
    if "noise" in response.guards:
        child.meters["wearing_earmuffs"] = 1
    child.meters["near_machine"] = 0
    child.meters["behind_line"] = 1
    child.memes["trust"] += 1
    world.say(
        f"{adult.label_word.capitalize()} {response.setup}"
    )


def safe_run(world: World, machine_ent: Entity, machine: Machine, response: Response) -> None:
    machine_ent.meters["running"] = 1
    markers = propagate(world, narrate=False)
    world.facts["safe_markers"] = markers
    world.say(
        f"Now the machine could sing again: {machine.sound}! {machine.sound}! "
        f"{response.safe_view}"
    )
    machine_ent.meters["running"] = 0


def lesson(world: World, child: Entity, adult: Entity, machine: Machine) -> None:
    child.memes["lesson"] += 1
    child.memes["pride"] += 1
    world.say(
        f'{adult.label_word.capitalize()} bent down and smiled. "{machine.lesson}"'
    )
    world.say(
        f'{child.id} nodded. "First we wait, then we help," {child.pronoun()} said.'
    )


def helper_job(world: World, child: Entity, adult: Entity, machine: Machine, response: Response) -> None:
    child.memes["joy"] += 1
    world.say(
        f"When the humming stopped, {child.id} got a safe job at last. "
        f"{response.helper_line} {machine.safe_job}"
    )
    world.say(
        f"So it was {machine.ending_image}, and the lesson stayed bright in {child.pronoun('possessive')} mind."
    )


def tell(
    place: Place,
    machine: Machine,
    response: Response,
    child_name: str = "Molly",
    child_gender: str = "girl",
    adult_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            label="the grown-up",
            role="adult",
        )
    )
    room = world.add(Entity(id="room", type="room", label=place.label))
    machine_ent = world.add(
        Entity(
            id="machine",
            type="machine",
            label=machine.label,
            phrase=machine.phrase,
            role="machine",
            attrs={"hazards": set(machine.hazards), "loudness": machine.loudness},
            tags=set(machine.tags),
        )
    )

    introduce(world, child, adult, place)
    notice_machine(world, child, machine)

    world.para()
    tempt(world, child, machine)
    warn(world, child, adult, machine)

    listened = child_listens(trait)
    if not listened:
        world.para()
        edge_close(world, child)
        start_machine(world, machine_ent, machine)
        startled_beat(world, child, machine)
        calm_and_stop(world, child, adult, machine_ent, response)

    world.para()
    set_safeguard(world, child, adult, response)
    safe_run(world, machine_ent, machine, response)
    lesson(world, child, adult, machine)
    helper_job(world, child, adult, machine, response)

    outcome = "listened" if listened else "startled"
    world.facts.update(
        child=child,
        adult=adult,
        place=place,
        machine_cfg=machine,
        machine=machine_ent,
        response=response,
        outcome=outcome,
        listened=listened,
        speckled=child.meters["speckled"] >= THRESHOLD,
    )
    return world


PLACES = {
    "bakery": Place(
        id="bakery",
        label="bakery",
        phrase="the warm town bakery",
        affords={"mixer"},
        details="Pans winked on shelves, and floury light lay on the floor.",
        tags={"bakery"},
    ),
    "laundry": Place(
        id="laundry",
        label="laundry",
        phrase="the clean town laundry",
        affords={"washer"},
        details="Fresh soap floated in the air, and baskets sat in tidy rows.",
        tags={"laundry"},
    ),
    "jam_room": Place(
        id="jam_room",
        label="jam room",
        phrase="the berry jam room",
        affords={"stirrer"},
        details="Copper pots glowed softly, and the room smelled sweet as summer.",
        tags={"jam"},
    ),
}

MACHINES = {
    "mixer": Machine(
        id="mixer",
        label="industrial mixer",
        phrase="an industrial mixer with a silver bowl big as a moon",
        place_word="bakery corner",
        sound="WHIRR-whump",
        hum="round and round",
        hazards={"noise", "motion", "splash"},
        features={"line"},
        lesson="Big mixers are not for little fingers. We listen, we stay back, and we help when the bowl is still.",
        safe_job="Then she sprinkled cinnamon on the buns with a careful pinch-pinch-pinch.",
        ending_image="Molly stood by the line in her earmuffs, smiling like a tiny baker star",
        tags={"industrial", "mixer", "noise", "earmuffs"},
        loudness=3,
        sprinkle_word="floury dots",
    ),
    "washer": Machine(
        id="washer",
        label="industrial washer",
        phrase="an industrial washer with a round glass window",
        place_word="laundry room",
        sound="WHOOSH-clunk",
        hum="swish and tumble",
        hazards={"noise", "motion", "splash"},
        features={"line", "window"},
        lesson="Big washers wash best when small helpers watch with patient feet. We never crowd the drum while it spins.",
        safe_job="Then he matched tiny socks into pairs, one-two, one-two.",
        ending_image="Theo watched the round window from a safe spot, counting bubbles with a grin",
        tags={"industrial", "washer", "noise", "laundry", "window"},
        loudness=2,
        sprinkle_word="misty drops",
    ),
    "stirrer": Machine(
        id="stirrer",
        label="industrial jam stirrer",
        phrase="an industrial jam stirrer turning in a shining copper pot",
        place_word="jam room",
        sound="GLUG-hum",
        hum="slow and steady",
        hazards={"noise", "motion", "splash"},
        features={"line"},
        lesson="Big stirrers keep the jam safe, and little helpers keep themselves safe by waiting for the spoon to stop.",
        safe_job="Then she set bright berry labels in a row, tap-tap, straight and neat.",
        ending_image="Ava stood behind the yellow stripe, rosy-cheeked and proud",
        tags={"industrial", "jam", "noise", "berries"},
        loudness=2,
        sprinkle_word="sticky dots",
    ),
}

RESPONSES = {
    "earmuffs_line": Response(
        id="earmuffs_line",
        label="earmuffs and the yellow line",
        sense=3,
        guards={"noise", "motion", "splash"},
        needs={"line"},
        setup="lifted out soft blue earmuffs, settled them over the small ears, and pointed to the yellow line on the floor.",
        safe_view="From behind the line, the child watched with calm eyes and safe feet.",
        helper_line="When it was still, the grown-up nodded and made room beside the table.",
        qa_text="used earmuffs and the yellow line so the child could stay back",
        tags={"earmuffs", "line"},
    ),
    "round_window": Response(
        id="round_window",
        label="the round window and earmuffs",
        sense=3,
        guards={"noise", "motion", "splash"},
        needs={"window"},
        setup="set snug earmuffs on the child's head and tapped the round window where watching was safe.",
        safe_view="The child peeped through the round glass while the machine did the strong work alone.",
        helper_line="After the drum was still, the grown-up opened the door and invited a tiny helping hand.",
        qa_text="had the child watch through the round window in earmuffs",
        tags={"earmuffs", "window"},
    ),
    "hands_on_ears": Response(
        id="hands_on_ears",
        label="just cover ears with hands",
        sense=1,
        guards={"noise"},
        needs=set(),
        setup="told the child to cover both ears with small hands.",
        safe_view="The child squinted and tried to stand still.",
        helper_line="The grown-up said that was enough watching for now.",
        qa_text="only covered the child's ears with small hands",
        tags={"noise"},
    ),
}


GIRL_NAMES = ["Molly", "Ava", "Nora", "Lila", "Poppy", "Ruby", "Mina", "Tessa"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Finn", "Sam", "Owen", "Leo"]
TRAITS = ["careful", "patient", "gentle", "bouncy", "curious", "brisk"]


@dataclass
class StoryParams:
    place: str
    machine: str
    response: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "industrial": [
        (
            "What does industrial mean?",
            "Industrial means made for big, strong work, often in a workroom or factory. Industrial machines are not toys, so children need a grown-up's help around them.",
        )
    ],
    "earmuffs": [
        (
            "Why do people wear earmuffs around loud machines?",
            "Earmuffs help make loud sounds softer for your ears. They are part of staying safe in a noisy place.",
        )
    ],
    "mixer": [
        (
            "What does a big mixer do?",
            "A big mixer turns and stirs ingredients together. It can work fast and strong, so little hands should stay out of the bowl.",
        )
    ],
    "washer": [
        (
            "Why should you not crowd a big washer while it spins?",
            "A big washer moves fast and can splash and thump while it works. It is safer to watch from a little distance until it stops.",
        )
    ],
    "window": [
        (
            "Why is a window a good place to watch a machine?",
            "A window lets you look closely while your body stays safely back. You can see the work without getting near the moving parts.",
        )
    ],
    "line": [
        (
            "What is a safety line for?",
            "A safety line shows where it is safe to stand. Staying behind it gives strong machines the space they need.",
        )
    ],
    "noise": [
        (
            "Why can loud sounds surprise you?",
            "Loud sounds reach your ears all at once and can make your body jump. That is why calm listening and ear protection help.",
        )
    ],
    "jam": [
        (
            "Why do people stir jam in big pots?",
            "Big pots help people cook many berries together. The stirring keeps the jam moving so it cooks evenly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["industrial", "noise", "earmuffs", "line", "window", "mixer", "washer", "jam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    machine = f["machine_cfg"]
    response = f["response"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the word "industrial" and the sound effect "{machine.sound}".',
        f"Tell a gentle lesson-learned story where a child named {child.id} wants to go close to an {machine.label}, but a grown-up teaches {response.label}.",
        f"Write a child-facing story with bouncing sounds, a near mistake, and a safe ending where the child learns to wait until the machine stops.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    machine = f["machine_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {child.pronoun('possessive')} {adult.label_word} in a room with an {machine.label}. The big machine made the day feel exciting and a little risky.",
        ),
        (
            f"What made {child.id} want to go close?",
            f"{child.id} thought the machine looked grand and sounded wonderful. The noisy rhythm made it seem like a song, so curiosity pulled {child.pronoun('object')} forward.",
        ),
        (
            f"Why did the grown-up say to stay back?",
            f"The grown-up knew the machine was loud, strong, and full of moving work. If {child.id} went too near, the sudden noise could startle {child.pronoun('object')} and the machine could toss tiny specks nearby.",
        ),
    ]
    if f["outcome"] == "startled":
        qa.append(
            (
                f"What happened when {child.id} edged too close?",
                f"When the machine began, the sound made {child.id} jump, and a few tiny specks reached {child.pronoun('possessive')} sleeves. That quick scare is what helped the lesson feel real.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} listen right away?",
                f"Yes. {child.id} listened to the warning before the noisy work began. That helped the whole visit stay calm from the start.",
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They used {response.label} and gave the child a safe place to watch. After the machine stopped, the child got a small helper job, so the child could join in without danger.",
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that strong industrial machines are for grown-up hands while they are moving. A little helper waits, watches from a safe spot, and helps only after the humming stops.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"industrial", "noise"}
    tags |= set(world.facts["response"].tags)
    tags |= set(world.facts["machine_cfg"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bakery",
        machine="mixer",
        response="earmuffs_line",
        child_name="Molly",
        child_gender="girl",
        adult_type="mother",
        trait="bouncy",
    ),
    StoryParams(
        place="laundry",
        machine="washer",
        response="round_window",
        child_name="Theo",
        child_gender="boy",
        adult_type="father",
        trait="patient",
    ),
    StoryParams(
        place="jam_room",
        machine="stirrer",
        response="earmuffs_line",
        child_name="Ava",
        child_gender="girl",
        adult_type="mother",
        trait="curious",
    ),
]


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
covers_all(M, R) :- machine(M), response(R), not missing_guard(M, R).
missing_guard(M, R) :- hazard(M, H), not guards(R, H).
needs_ok(M, R) :- machine(M), response(R), not missing_need(M, R).
missing_need(M, R) :- needs(R, F), not feature(M, F).

valid(P, M, R) :- place(P), affords(P, M), sensible(R), covers_all(M, R), needs_ok(M, R).

listened :- trait(T), cautious(T).
outcome(listened) :- listened.
outcome(startled) :- not listened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for machine_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, machine_id))
    for machine_id, machine in MACHINES.items():
        lines.append(asp.fact("machine", machine_id))
        for hazard in sorted(machine.hazards):
            lines.append(asp.fact("hazard", machine_id, hazard))
        for feature in sorted(machine.features):
            lines.append(asp.fact("feature", machine_id, feature))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for guard in sorted(response.guards):
            lines.append(asp.fact("guards", response_id, guard))
        for need in sorted(response.needs):
            lines.append(asp.fact("needs", response_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "listened" if child_listens(params.trait) else "startled"


def asp_verify() -> int:
    rc = 0

    a_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if a_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(a_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in clingo:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in python:", sorted(p_valid - a_valid))

    a_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if a_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(a_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(a_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(20):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "industrial" not in sample.story.lower():
            raise StoryError("Smoke test story missing text or required seed word.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme storyworld: a child, an industrial machine, and a gentle lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    if args.place and args.machine and args.machine not in PLACES[args.place].affords:
        raise StoryError(
            f"(No story: {PLACES[args.place].label} does not have the {MACHINES[args.machine].label}.)"
        )

    if args.machine and args.response:
        machine = MACHINES[args.machine]
        response = RESPONSES[args.response]
        if not response_covers(machine, response):
            raise StoryError(explain_rejection(machine, response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.machine is None or combo[1] == args.machine)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, machine_id, response_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        name = rng.choice(pool)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        machine=machine_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.machine not in MACHINES:
        raise StoryError(f"(Unknown machine '{params.machine}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if params.machine not in PLACES[params.place].affords:
        raise StoryError(
            f"(No story: {PLACES[params.place].label} does not have the {MACHINES[params.machine].label}.)"
        )
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_covers(MACHINES[params.machine], RESPONSES[params.response]):
        raise StoryError(explain_rejection(MACHINES[params.machine], RESPONSES[params.response]))

    world = tell(
        place=PLACES[params.place],
        machine=MACHINES[params.machine],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, machine, response) combos:\n")
        for place_id, machine_id, response_id in combos:
            print(f"  {place_id:9} {machine_id:8} {response_id}")
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
            header = f"### {p.child_name}: {p.machine} at {p.place} ({outcome_of(p)})"
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
