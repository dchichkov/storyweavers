#!/usr/bin/env python3
"""
A standalone Storyweavers world about a curious child, an orthodontist, and a
magical mattress tethered by a wooden stake.

The mattress responds to unanswered questions. A loose anchor could send it
sailing over the hill, so curiosity, careful observation, and a gentle plan
shape the story's ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "the hilltop orthodontic garden"
SEED_WORDS = ("mattress", "orthodontist", "stake")
FEATURE_REGISTRY = ("bad_ending", "magic", "curiosity")
NAME_REGISTRY = ("Rowan", "Milo", "Lena", "Sasha", "Ari", "Tess")
ORTHODONTIST_REGISTRY = ("Noor", "Vale", "Kim", "Ibarra", "Singh")
ENDING_REGISTRY = ("safe", "bad")
VOICE_REGISTRY = (
    "Where does the moon rest in daylight?",
    "Can a mattress hear a question before it is finished?",
    "Why do the stars look so close from this hill?",
    "Could a bed float gently enough to carry a dream?",
)


@dataclass
class Entity:
    """A typed person or object with physical meters and emotional memes."""

    id: str
    kind: str
    type: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("height", "stability", "strain", "distance", "soundness"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "trust", "care", "relief", "sadness"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    name: str = "Rowan"
    orthodontist: str = "Noor"
    case: int = 0
    voice: int = 0
    ending_mode: str = "safe"
    seed: Optional[int] = None


@dataclass(frozen=True)
class GardenCase:
    clue: str
    false_lead: str
    cause: str
    repair: str
    proof: str
    closing_image: str


CASES = (
    GardenCase(
        clue="a wet circle of soil spreading around the stake",
        false_lead="A paper star fluttered beside the gate, but it had never touched the mattress.",
        cause="spring rain had softened the ground beneath the stake",
        repair="they moved the tether to a broad stone planter, packed it with gravel, and set in a fresh stake",
        proof="a careful pull from the paving left the new stake firm",
        closing_image="a bead of rain shone on the blue cord beneath the garden lantern",
    ),
    GardenCase(
        clue="blue fibers worn thin where the cord rubbed against the iron gate",
        false_lead="The wind chime rang brightly, though it hung well away from the mattress.",
        cause="the old cord had rubbed thin against the gate",
        repair="they moved the mattress clear of the gate and replaced the frayed cord with a new one",
        proof="the new cord held when a breeze lifted the mattress's corners",
        closing_image="the fresh blue cord curled neatly beside the quiet gate",
    ),
    GardenCase(
        clue="a pale split running down the wooden stake",
        false_lead="A bright patch of moonlight slid across the path, but it was only a reflection.",
        cause="damp weather had split the old stake along its grain",
        repair="they set a sturdy cedar stake deep in packed earth and tied the cord well above the split",
        proof="the cedar stake stayed straight through a gentle test",
        closing_image="the cedar stake cast a small, steady star-shaped shadow",
    ),
    GardenCase(
        clue="cracked earth on the side of the stake nearest the apple tree",
        false_lead="A cricket hopped under the bench, making the grass rustle in a tempting direction.",
        cause="the apple tree's roots had slowly pushed the stake loose",
        repair="they moved the anchor clear of the roots and fixed a fresh stake in a gravel-weighted planter",
        proof="the anchor stayed still when a passing breeze tugged the cord",
        closing_image="a fallen apple rested beside the firm planter",
    ),
)


@dataclass
class World:
    hero: Entity
    doctor: Entity
    mattress: Entity
    stake: Entity
    cord: Entity
    mirror: Entity
    lantern: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    events: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def record(self, event: str) -> None:
        self.events.append(event)


def reasonableness_gate(params: StoryParams) -> bool:
    """Reject choices that cannot describe a coherent, safe story."""

    if not isinstance(params, StoryParams):
        raise StoryError("Story parameters must be a StoryParams object.")
    name_pattern = re.compile(r"^[A-Za-z][A-Za-z '-]{0,29}$")
    for label, value in (
        ("The child's name", params.name),
        ("The orthodontist's name", params.orthodontist),
    ):
        if not isinstance(value, str) or not name_pattern.fullmatch(value.strip()):
            raise StoryError(f"{label} must be a short, non-empty name using letters, spaces, apostrophes, or hyphens.")
    if params.name.strip().casefold() == params.orthodontist.strip().casefold():
        raise StoryError("The child and orthodontist must have different names.")
    if type(params.case) is not int or not 0 <= params.case < len(CASES):
        raise StoryError(f"The case must be an integer from 0 to {len(CASES) - 1}.")
    if type(params.voice) is not int or not 0 <= params.voice < len(VOICE_REGISTRY):
        raise StoryError(f"The voice must be an integer from 0 to {len(VOICE_REGISTRY) - 1}.")
    if params.ending_mode not in ENDING_REGISTRY:
        raise StoryError(f"The ending must be one of: {', '.join(ENDING_REGISTRY)}.")
    if params.seed is not None and type(params.seed) is not int:
        raise StoryError("The seed must be an integer.")
    return True


def build_world(params: StoryParams) -> World:
    hero = Entity(
        id=params.name,
        kind="person",
        type="child",
        label="the patient",
        location="the garden paving",
        memes={"curiosity": 1.0, "worry": 2.0, "trust": 0.0, "care": 0.0, "relief": 0.0, "sadness": 0.0},
    )
    doctor = Entity(
        id=params.orthodontist,
        kind="person",
        type="orthodontist",
        label="the orthodontist",
        location="the garden path",
        memes={"curiosity": 0.0, "worry": 0.0, "trust": 0.0, "care": 2.0, "relief": 0.0, "sadness": 0.0},
    )
    mattress = Entity(
        id="blue_mattress",
        kind="object",
        type="mattress",
        label="the blue mattress",
        location="the garden nook",
        meters={"height": 0.0, "stability": 0.7, "strain": 0.0, "distance": 0.0, "soundness": 1.0},
    )
    stake = Entity(
        id="wooden_stake",
        kind="object",
        type="stake",
        label="the star-painted stake",
        location="the garden soil",
        meters={"height": 0.0, "stability": 0.5, "strain": 0.0, "distance": 0.0, "soundness": 0.5},
    )
    cord = Entity(
        id="blue_cord",
        kind="object",
        type="cord",
        label="the blue cord",
        location="between the mattress and stake",
        meters={"height": 0.0, "stability": 0.5, "strain": 0.0, "distance": 0.0, "soundness": 0.5},
    )
    mirror = Entity(
        id="dental_mirror",
        kind="tool",
        type="mirror",
        label="the orthodontist's small dental mirror",
        location="the clinic bag",
    )
    lantern = Entity(
        id="garden_lantern",
        kind="object",
        type="lantern",
        label="the garden lantern",
        location="beside the path",
    )
    return World(hero, doctor, mattress, stake, cord, mirror, lantern)


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = build_world(params)
    hero, doctor = world.hero, world.doctor
    mattress, stake, cord = world.mattress, world.stake, world.cord
    case = CASES[params.case]
    question = VOICE_REGISTRY[params.voice]

    openings = (
        f"{hero.id} arrived at the hilltop clinic for a braces check with Dr. {doctor.id}, an orthodontist.",
        f"On a breezy afternoon, {hero.id} visited Dr. {doctor.id}, an orthodontist, to have their braces checked.",
        f"{hero.id} had come up the hill for an appointment with Dr. {doctor.id}, the orthodontist, and was glad to wait outside.",
        f"Before the afternoon's braces check, {hero.id} met Dr. {doctor.id}, an orthodontist, in the little garden beside the clinic.",
    )
    world.say(openings[params.voice])
    world.say(
        f"In the garden nook lay a soft blue mattress where nervous children could rest. "
        f"A blue cord tied it to a star-painted wooden stake."
    )
    world.say(
        "The mattress had a gentle bit of magic: when it heard an unanswered question, "
        "its corners lifted as if it wanted to listen more closely."
    )
    world.record("The child arrived for a braces check and noticed the enchanted mattress.")

    world.para()
    hero.memes["curiosity"] += 1.0
    world.say(f"{hero.id} looked up at the first evening star and asked, “{question}”")
    mattress.meters["height"] = 0.25
    mattress.meters["strain"] = 0.3
    stake.meters["stability"] = 0.45
    world.say(
        "The mattress gave a soft hum and rose a handspan. The cord held, but the stake tipped a little."
    )
    world.say(
        f"Nearby, {case.clue} made the problem easier to see. {case.false_lead}"
    )
    world.record("A question lifted the mattress and put a small strain on its anchor.")

    world.para()
    world.say(
        f"“The stake is leaning,” {hero.id} said. “Could we look before asking it anything else?”"
    )
    world.say(
        f"“Good noticing,” said Dr. {doctor.id}. “Keep your feet on the paving while I check it.”"
    )
    world.say(
        f"Dr. {doctor.id} took the small dental mirror from the clinic bag and checked the anchor from the path. "
        f"The view confirmed that {case.cause}."
    )
    world.say(
        f"{hero.id} glanced toward the rooftops. “The bad ending would be the mattress flying away.”"
    )
    world.say(
        f"“Then we won't climb after it or tug while it floats,” Dr. {doctor.id} replied. "
        "“We can make a careful plan from the ground.”"
    )
    world.record("The child and doctor chose to inspect the anchor from a safe place.")

    if params.ending_mode == "safe":
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
        hero.memes["trust"] += 1.0
        doctor.memes["care"] += 1.0
        stake.meters["soundness"] = 0.95
        stake.meters["stability"] = 0.95
        cord.meters["soundness"] = 0.95
        cord.meters["strain"] = 0.2
        mattress.meters["height"] = 0.0
        mattress.meters["stability"] = 0.95
        mattress.meters["strain"] = 0.15
        stake.location = "a secure place in the garden"
        cord.location = "a smooth, secure loop"
        mattress.location = "the garden nook, safely tethered"

        world.para()
        world.say(
            f"“Braces guide teeth with gentle, steady pressure,” Dr. {doctor.id} explained. "
            "“An anchor needs patient care, too.”"
        )
        world.say(f"“Then let's make it steady before we ask another question,” said {hero.id}.")
        world.say(f"Together, {case.repair}.")
        world.say(
            f"They tested the tether with a careful pull from the paving. {case.proof}."
        )
        mattress.meters["height"] = 0.12
        mattress.meters["strain"] = 0.25
        world.say(
            f"{hero.id} tried one more question. The mattress rose just a little, stayed close to the ground, "
            "and settled softly back into its nook."
        )
        world.record("The anchor was repaired and the mattress passed a gentle test.")

        world.para()
        doctor.memes["care"] += 1.0
        hero.memes["relief"] += 1.0
        hero.memes["trust"] += 1.0
        world.say(
            f"Dr. {doctor.id} finished the braces check while {hero.id} rested nearby. "
            f"The garden grew quiet, and {case.closing_image}."
        )
        world.say(
            "The mattress stayed where it belonged, ready for the next child who needed a calm place to breathe."
        )
        world.record("The appointment ended with the mattress safely anchored.")
    else:
        world.para()
        world.say(
            "Before they could finish their plan, a gust swept across the hill. "
            f"Because {case.cause}, the weakest part of the old anchor gave way."
        )
        stake.meters["soundness"] = 0.0
        stake.meters["stability"] = 0.0
        cord.meters["soundness"] = 0.0
        cord.meters["strain"] = 1.0
        mattress.meters["height"] = 18.0
        mattress.meters["stability"] = 0.0
        mattress.meters["strain"] = 1.0
        mattress.meters["distance"] = 60.0
        mattress.location = "beyond the hill, out of sight"
        hero.memes["worry"] = 0.0
        hero.memes["sadness"] = 1.0
        doctor.memes["care"] += 2.0
        world.say(
            "The mattress floated over the apple tree and disappeared beyond the hill. "
            "No one was on it, and neither of them tried to chase it."
        )
        world.say(
            f"“I wanted it to come back,” {hero.id} said. "
            f"“I know,” said Dr. {doctor.id}. “We can miss it and still make this corner feel safe.”"
        )
        world.record("The anchor failed in the gust; the unoccupied mattress drifted out of sight.")

        world.para()
        world.say(
            f"Dr. {doctor.id} gathered the loose cord and marked the patch of ground for the gardener to repair. "
            "Inside, they made a low resting place with a folded quilt and a pillow, well away from the broken stake."
        )
        world.say(
            "It was a bad ending for the blue mattress, and they did not pretend it was a rescue. "
            "But Dr. Noor finished the braces check gently, and the quilted nest gave "
            f"{hero.id} a place to rest while the lantern glowed in the window."
        )
        hero.memes["trust"] += 1.0
        hero.memes["relief"] += 0.5
        doctor.memes["care"] += 1.0
        world.record("The lost mattress was not recovered; the clinic made a safer resting place indoors.")

    world.facts.update(
        hero=hero,
        doctor=doctor,
        mattress=mattress,
        stake=stake,
        cord=cord,
        case=case,
        question=question,
        ending_mode=params.ending_mode,
        resolved=True,
        clue=case.clue,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        seed_words=SEED_WORDS,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    doctor = world.facts["doctor"]
    case: GardenCase = world.facts["case"]
    mode = world.facts["ending_mode"]

    if mode == "safe":
        ending_answer = (
            f"{hero.id} and Dr. {doctor.id} secured the mattress before testing it again. "
            f"They saw that {case.proof}, so it could rise a little without drifting away."
        )
    else:
        ending_answer = (
            f"A gust pulled the mattress beyond the hill after {case.cause}. "
            f"{hero.id} and Dr. {doctor.id} stayed safely on the ground and made an indoor resting place with a quilt and pillow."
        )

    return [
        QAItem(
            question=f"Why had {hero.id} come to the hilltop clinic?",
            answer=(
                f"{hero.id} had come to Dr. {doctor.id}, an orthodontist, for a braces check. "
                "The garden mattress gave the child a quiet place to settle before the appointment."
            ),
        ),
        QAItem(
            question="What made the blue mattress lift into the air?",
            answer=(
                f"The mattress had a little magic that made its corners rise when it heard an unanswered question. "
                f"When {hero.id} asked, “{world.facts['question']}” it lifted and tugged on its tether."
            ),
        ),
        QAItem(
            question=f"What clue helped {hero.id} and Dr. {doctor.id} understand the danger?",
            answer=(
                f"They noticed {case.clue}. A closer look showed that {case.cause}, "
                "so they knew the mattress needed a safer anchor."
            ),
        ),
        QAItem(
            question="How did the story end for the mattress and the child?",
            answer=ending_answer,
        ),
        QAItem(
            question="What did the orthodontist's explanation about braces teach the child?",
            answer=(
                f"Dr. {doctor.id} explained that braces guide teeth with gentle, steady pressure. "
                "The child used that idea to see why a careful, steady anchor was better than a sudden tug."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an orthodontist do?",
            answer=(
                "An orthodontist is a dentist who helps guide teeth and jaws into healthier positions. "
                "Braces can move teeth gradually with careful pressure."
            ),
        ),
        QAItem(
            question="What is a stake?",
            answer=(
                "A stake is a sturdy post pushed into the ground or another firm base. "
                "People can tie a cord to it to help hold something in place."
            ),
        ),
        QAItem(
            question="What is curiosity?",
            answer=(
                "Curiosity is the wish to learn more about something. "
                "A curious person can ask a question, look closely, and then decide what to do."
            ),
        ),
        QAItem(
            question="How does magic work in this story?",
            answer=(
                "In this make-believe tale, the mattress lifts its corners when it hears an unanswered question. "
                "The magic is gentle, but the mattress still needs a sound anchor."
            ),
        ),
        QAItem(
            question="Why was the mattress tied down?",
            answer=(
                "The mattress could rise when it heard a question, so the cord and stake kept it near the garden. "
                "A strong anchor helped everyone stay safe."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case: GardenCase = world.facts["case"]
    return [
        (
            "Write a warm, child-friendly story about a curious child visiting an orthodontist "
            "and discovering a magical mattress tied to a wooden stake."
        ),
        (
            f"Use this clue to turn curiosity into a careful plan: {case.clue}. "
            "Include spoken dialogue and show what changes by the ending."
        ),
        (
            "Tell a heartwarming story with a possible bad ending. Keep the child safe, "
            "make the mattress's magic matter, and end with a concrete image."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    entities = (
        world.hero,
        world.doctor,
        world.mattress,
        world.stake,
        world.cord,
        world.mirror,
        world.lantern,
    )
    for entity in entities:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:16} ({entity.kind}/{entity.type}) "
            f"location={entity.location!r} meters={meters} memes={memes}"
        )
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.events)
    return "\n".join(lines)


ASP_RULES = r"""
% Registry-backed twin for the small orthodontic garden world.
word_present(W) :- required_word(W), registered_word(W).
required_words_present :-
    word_present(mattress),
    word_present(orthodontist),
    word_present(stake).

named_roles :-
    character(hero, H),
    H != "",
    character(doctor, D),
    D != "",
    H != D.

case_valid :- selected_case(C), available_case(C).
voice_valid :- selected_voice(V), available_voice(V).
ending_valid :- selected_ending(E), available_ending(E).

valid_story :-
    setting(orthodontic_garden),
    required_words_present,
    feature(bad_ending),
    feature(magic),
    feature(curiosity),
    named_roles,
    case_valid,
    voice_valid,
    ending_valid,
    resolved.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    """Emit registry and selected-parameter facts for the inline ASP twin."""
    import storyworlds.asp as asp  # lazy import

    params = params or StoryParams()
    lines = [
        asp.fact("setting", "orthodontic_garden"),
        *(asp.fact("registered_word", word) for word in SEED_WORDS),
        *(asp.fact("required_word", word) for word in SEED_WORDS),
        *(asp.fact("feature", feature) for feature in FEATURE_REGISTRY),
        *(asp.fact("available_case", index) for index in range(len(CASES))),
        *(asp.fact("available_voice", index) for index in range(len(VOICE_REGISTRY))),
        *(asp.fact("available_ending", ending) for ending in ENDING_REGISTRY),
        asp.fact("character", "hero", params.name),
        asp.fact("character", "doctor", params.orthodontist),
        asp.fact("selected_case", params.case),
        asp.fact("selected_voice", params.voice),
        asp.fact("selected_ending", params.ending_mode),
        asp.fact("resolved"),
    ]
    return "\n".join(lines)


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def _asp_valid(params: StoryParams) -> bool:
    import storyworlds.asp as asp  # lazy import

    model = asp.one_model(asp_program("#show valid_story/0.", params))
    return any(atom.name == "valid_story" and not atom.arguments for atom in model)


def asp_verify() -> int:
    """Compare the Python gate with ASP and exercise both story endings."""
    tests = (
        StoryParams(name="Rowan", orthodontist="Noor", case=0, voice=0, ending_mode="safe", seed=11),
        StoryParams(name="Lena", orthodontist="Ibarra", case=1, voice=2, ending_mode="bad", seed=12),
        StoryParams(name="Ari", orthodontist="Singh", case=3, voice=3, ending_mode="safe", seed=13),
    )

    try:
        for params in tests:
            python_valid = reasonableness_gate(params)
            asp_valid = _asp_valid(params)
            if asp_valid != python_valid:
                print(
                    f"MISMATCH: ASP/Python parity failed for case {params.case} "
                    f"with the {params.ending_mode} ending."
                )
                return 1

            sample = generate(params)
            lowered = sample.story.casefold()
            if not all(word in lowered for word in SEED_WORDS):
                print("MISMATCH: A generated story is missing a required seed word.")
                return 1
            if "“" not in sample.story or "said" not in lowered:
                print("MISMATCH: A generated story is missing spoken dialogue.")
                return 1
            if not sample.story_qa or not sample.world_qa:
                print("MISMATCH: A generated story is missing a question-and-answer set.")
                return 1
            if not sample.world.facts.get("resolved"):
                print("MISMATCH: A generated story did not reach a resolution.")
                return 1

        try:
            reasonableness_gate(StoryParams(name="Noor", orthodontist="Noor"))
        except StoryError:
            pass
        else:
            print("MISMATCH: The Python gate accepted identical character names.")
            return 1

    except StoryError as exc:
        print(f"MISMATCH: Generated-story verification failed: {exc}")
        return 1

    print("OK: ASP/Python parity holds, and safe and bad-ending stories resolve.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming magical-mattress story world in an orthodontic garden."
    )
    parser.add_argument("--name", default=None, help="the child's name")
    parser.add_argument("--orthodontist", default=None, help="the orthodontist's name")
    parser.add_argument("--case", type=int, choices=range(len(CASES)), default=None)
    parser.add_argument("--voice", type=int, choices=range(len(VOICE_REGISTRY)), default=None)
    parser.add_argument("--ending", choices=ENDING_REGISTRY, default=None)
    parser.add_argument("-n", type=int, default=1, help="number of distinct stories")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="show the curated stories")
    parser.add_argument("--trace", action="store_true", help="show simulated world state")
    parser.add_argument("--qa", action="store_true", help="show prompts and question-and-answer sets")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--asp", action="store_true", help="solve and show the ASP model")
    parser.add_argument("--verify", action="store_true", help="check ASP/Python parity and generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print facts and inline ASP rules")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    name = args.name or rng.choice(NAME_REGISTRY)
    orthodontist = args.orthodontist or rng.choice(ORTHODONTIST_REGISTRY)
    offset = sample_seed - base_seed
    case = args.case if args.case is not None else offset % len(CASES)
    voice = args.voice if args.voice is not None else (offset // len(CASES)) % len(VOICE_REGISTRY)
    ending_mode = args.ending or ("bad" if offset % 4 == 3 else "safe")
    params = StoryParams(
        name=name,
        orthodontist=orthodontist,
        case=case,
        voice=voice,
        ending_mode=ending_mode,
        seed=sample_seed,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = (
    StoryParams(name="Rowan", orthodontist="Noor", case=0, voice=0, ending_mode="safe", seed=101),
    StoryParams(name="Milo", orthodontist="Vale", case=2, voice=1, ending_mode="safe", seed=102),
    StoryParams(name="Lena", orthodontist="Ibarra", case=1, voice=3, ending_mode="bad", seed=103),
)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1 and not args.all:
        parser.error("-n must be at least 1.")

    if args.asp:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        params = resolve_params(args, random.Random(base_seed), base_seed, base_seed)
        import storyworlds.asp as asp  # lazy import

        model = asp.one_model(asp_program("#show valid_story/0.", params))
        print("ASP model:", [str(atom) for atom in model])
        return

    try:
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            base_seed = args.seed if args.seed is not None else random.randrange(2**31)
            samples: list[StorySample] = []
            seen: set[str] = set()
            index = 0
            limit = max(50, args.n * 50)
            while len(samples) < args.n and index < limit:
                sample_seed = base_seed + index
                params = resolve_params(
                    args,
                    random.Random(sample_seed),
                    sample_seed,
                    base_seed,
                )
                sample = generate(params)
                if sample.story not in seen:
                    seen.add(sample.story)
                    samples.append(sample)
                index += 1
            if len(samples) < args.n:
                raise StoryError("Could not produce the requested number of distinct stories.")

    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
