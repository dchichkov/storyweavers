#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py
================================================================================

A standalone storyworld about a child in a school gymnasium that has been turned
into a temporary place for something else. In the half-dark, a spooky "ghost"
seems to move between the temporary things. The world model tracks fear,
kindness, trust, and safety, and the ending depends on whether the child answers
fear with gentle help.

The style leans toward a soft ghost story: whispery, shadowy, and eerie, but
still child-facing and concrete. The intended moral value is that kindness and
calm courage are better than teasing or running from someone who might need help.

Run it
------
    python storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py
    python storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py --setup shelter --source kitten
    python storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py --setup stage --source lost_child
    python storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py --response laugh_and_run
    python storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py --all
    python storyworlds/worlds/gpt-5.4/gymnasium_temporary_happy_ending_moral_value_ghost.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher": "teacher",
            "caretaker": "caretaker",
        }.get(self.type, self.type or self.label or "someone")


@dataclass
class Setup:
    id: str = ""
    title: str = ""
    opening: str = ""
    structures: str = ""
    spooky_place: str = ""
    adult_role: str = "teacher"
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str = ""
    title: str = ""
    allowed_setups: set[str] = field(default_factory=set)
    appearance: str = ""
    sound: str = ""
    reveal: str = ""
    need_help: int = 0
    need_kindness: int = 0
    comfort: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str = ""
    label: str = ""
    sense: int = 0
    help: int = 0
    kindness: int = 0
    opening_text: str = ""
    reveal_text: str = ""
    lingering_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_hidden_spooky(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    room = world.get("room")
    if source.meters["hidden"] >= THRESHOLD:
        sig = ("spooky", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["spooky"] += 1
            child.memes["fear"] += 1
    return out


def _r_gentle_trust(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    if child.memes["gentle_call"] >= THRESHOLD and source.meters["hidden"] >= THRESHOLD:
        sig = ("trust", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            source.memes["trust"] += 1
            if source.memes["trust"] >= THRESHOLD:
                out.append("__trust__")
    return out


def _r_help_safety(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    if source.meters["helped"] >= THRESHOLD:
        sig = ("safe", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            source.meters["safe"] += 1
            child.memes["bravery"] += 1
            child.memes["kindness"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_spooky", tag="social", apply=_r_hidden_spooky),
    Rule(name="gentle_trust", tag="social", apply=_r_gentle_trust),
    Rule(name="help_safety", tag="physical", apply=_r_help_safety),
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
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


def valid_setup_source(setup: Setup, source: Source) -> bool:
    return setup.id in source.allowed_setups


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def warm_responses_for(source: Source) -> list[Response]:
    return [
        r for r in sensible_responses()
        if r.help >= source.need_help and r.kindness >= source.need_kindness
    ]


def outcome_of(params: "StoryParams") -> str:
    source = SOURCES[params.source]
    response = RESPONSES[params.response]
    if response.help >= source.need_help and response.kindness >= source.need_kindness:
        return "warm"
    return "lingering"


def predict_outcome(source: Source, response: Response) -> dict:
    return {
        "warm": response.help >= source.need_help and response.kindness >= source.need_kindness,
        "needs_help": source.need_help,
        "needs_kindness": source.need_kindness,
    }


def describe_friend_push(friend: Entity) -> str:
    if friend.attrs.get("temperament") == "bold":
        return f'"It has to be a ghost," {friend.id} whispered, trying to sound brave.'
    return f'"Do you hear that?" {friend.id} whispered, edging closer to {friend.pronoun("possessive")} friend.'


def introduce(world: World, child: Entity, friend: Entity, setup: Setup) -> None:
    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"One windy evening, {setup.opening} The big gymnasium looked different from daytime. "
        f"{setup.structures}"
    )
    world.say(
        f"{child.id} and {friend.id} had stayed a little late to carry paper stars and fold chairs, "
        f"so they were the last children still peeking around the echoing room."
    )


def first_haunt(world: World, child: Entity, friend: Entity, setup: Setup, source: Source) -> None:
    source_ent = world.get("source")
    source_ent.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then something pale slipped near {setup.spooky_place}. It made {source.sound}, and the sound "
        f"floated through the gymnasium so softly that it felt like a secret."
    )
    world.say(describe_friend_push(friend))
    if child.attrs.get("trait") == "careful":
        world.say(f"{child.id} felt a cool shiver race right down to {child.pronoun('possessive')} shoes.")
    else:
        world.say(f"{child.id}'s heart gave one hard thump, but {child.pronoun()} kept looking.")


def choose_response(world: World, child: Entity, friend: Entity, adult: Entity, source: Source, response: Response) -> None:
    child.attrs["chosen_response"] = response.id
    if response.id == "call_gently":
        child.memes["gentle_call"] += 1
        propagate(world, narrate=False)
        world.say(response.opening_text.format(child=child.id, friend=friend.id))
    elif response.id == "ask_adult":
        child.memes["gentle_call"] += 1
        child.meters["adult_near"] += 1
        propagate(world, narrate=False)
        world.say(
            response.opening_text.format(
                child=child.id,
                friend=friend.id,
                adult=adult.label_word,
            )
        )
    elif response.id == "peek_alone":
        world.say(response.opening_text.format(child=child.id, friend=friend.id))
    else:
        world.say(response.opening_text.format(child=child.id, friend=friend.id))


def reveal_and_help(world: World, child: Entity, friend: Entity, adult: Entity, setup: Setup, source: Source, response: Response) -> None:
    source_ent = world.get("source")
    source_ent.meters["revealed"] += 1
    source_ent.meters["hidden"] = 0.0
    source_ent.meters["helped"] += 1
    propagate(world, narrate=False)
    trust_line = ""
    if source_ent.memes["trust"] >= THRESHOLD:
        trust_line = " The soft voice helped the scared little sound answer back instead of hiding."
    world.say(
        response.reveal_text.format(
            child=child.id,
            friend=friend.id,
            adult=adult.label_word,
            reveal=source.reveal,
            comfort=source.comfort,
            place=setup.spooky_place,
        ) + trust_line
    )
    world.say(
        f"In one moment, the ghost story changed into a helping story. {child.id} saw that the pale shape "
        f"had never wanted to frighten anyone at all."
    )
    if source.id == "kitten":
        world.say(
            f"Soon the little kitten was tucked into a box with a towel, and the whole gymnasium seemed less hollow "
            f"and more warm."
        )
    elif source.id == "lost_child":
        world.say(
            f"Soon the little child was wrapped in a steadier hug, and the shadows between the temporary things did "
            f"not look lonely anymore."
        )
    else:
        world.say(
            f"Soon the loose silver banner was tied down high above the floor, and the dark fluttering corner became "
            f"ordinary cloth again."
        )


def lingering_end(world: World, child: Entity, friend: Entity, adult: Entity, setup: Setup, source: Source, response: Response) -> None:
    source_ent = world.get("source")
    source_ent.meters["revealed"] += 1
    source_ent.meters["hidden"] = 0.0
    world.say(
        response.lingering_text.format(
            child=child.id,
            friend=friend.id,
            adult=adult.label_word,
            reveal=source.reveal,
            comfort=source.comfort,
            place=setup.spooky_place,
        )
    )
    world.say(
        f"At last {adult.label_word} came and made everything safe, but {child.id} wished {child.pronoun()} had spoken "
        f"with more kindness the first time."
    )
    world.say(
        f"As the gymnasium lights went bright, the room no longer felt haunted. It felt temporary in a different way, "
        f"as if fear itself could pass when someone chose to help."
    )


def moral_close(world: World, child: Entity, friend: Entity, setup: Setup, source: Source) -> None:
    world.say(
        f"While they carried the last folded chair away, {friend.id} gave a sheepish smile. "
        f'"Next time," {friend.pronoun()} said, "let\'s remember that spooky noises can belong to someone who needs help."'
    )
    world.say(
        f"{child.id} nodded. After that night, the gymnasium still echoed, and the temporary things still rustled, "
        f"but {child.pronoun()} was quicker to bring a gentle voice than a frightened guess."
    )


def tell(
    setup: Setup,
    source: Source,
    response: Response,
    child_name: str = "Mina",
    child_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    adult_type: str = "teacher",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"trait": trait},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        label=friend_name,
        attrs={"temperament": "bold" if trait != "bold" else "soft"},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="gymnasium",
    ))
    source_ent = world.add(Entity(
        id="source",
        kind="thing",
        type=source.id,
        label=source.title,
        phrase=source.reveal,
        tags=set(source.tags),
    ))
    world.facts["room"] = room

    introduce(world, child, friend, setup)
    world.para()
    first_haunt(world, child, friend, setup, source)
    world.para()
    choose_response(world, child, friend, adult, source, response)
    prediction = predict_outcome(source, response)
    world.facts["predicted_warm"] = prediction["warm"]
    world.para()
    if prediction["warm"]:
        reveal_and_help(world, child, friend, adult, setup, source, response)
        world.para()
        moral_close(world, child, friend, setup, source)
        outcome = "warm"
    else:
        lingering_end(world, child, friend, adult, setup, source, response)
        outcome = "lingering"

    world.facts.update(
        child=child,
        friend=friend,
        adult=adult,
        setup=setup,
        source_cfg=source,
        source=source_ent,
        response=response,
        outcome=outcome,
        spooky=room.meters["spooky"] >= THRESHOLD,
        helped=source_ent.meters["safe"] >= THRESHOLD,
    )
    return world


SETUPS = {
    "shelter": Setup(
        id="shelter",
        title="storm shelter",
        opening="the school gymnasium had become a temporary shelter while a storm rumbled outside.",
        structures="Rows of folding cots stood under the basketball hoops, and white blankets hung from rope lines to make small sleeping corners.",
        spooky_place="the line of hanging blankets",
        adult_role="teacher",
        tags={"storm", "shelter", "temporary"},
    ),
    "stage": Setup(
        id="stage",
        title="school play hall",
        opening="the school gymnasium had become a temporary theater for the winter play.",
        structures="A painted moon leaned against the wall, black curtains crossed the floor, and a cardboard castle waited beside a stack of wooden stools.",
        spooky_place="the black curtain beside the cardboard castle",
        adult_role="teacher",
        tags={"play", "stage", "temporary"},
    ),
    "fair": Setup(
        id="fair",
        title="book fair hall",
        opening="the school gymnasium had become a temporary book fair for family night.",
        structures="Cloth booths made little aisles between the hoops, and silver streamers drooped from signs that pointed to stories and picture books.",
        spooky_place="the cloth booth at the end of the aisle",
        adult_role="caretaker",
        tags={"books", "fair", "temporary"},
    ),
}

SOURCES = {
    "kitten": Source(
        id="kitten",
        title="kitten",
        allowed_setups={"shelter", "stage", "fair"},
        appearance="a pale shape with bright eyes",
        sound="the tiniest mew and a scratch-scratch",
        reveal="a white kitten tangled in cloth and blinking in the dim light",
        need_help=2,
        need_kindness=2,
        comfort="a towel and a warm box",
        tags={"kitten", "animal", "kindness"},
    ),
    "lost_child": Source(
        id="lost_child",
        title="lost child",
        allowed_setups={"shelter", "fair"},
        appearance="a small white blur crouched low",
        sound="a sniffling whisper and a shaky little hiccup",
        reveal="a small child wrapped in a blanket, lost and trying not to cry loudly",
        need_help=2,
        need_kindness=2,
        comfort="a steady hand and a familiar grown-up",
        tags={"child", "kindness", "help"},
    ),
    "banner": Source(
        id="banner",
        title="loose banner",
        allowed_setups={"stage", "fair"},
        appearance="a silver shape that rose and dipped",
        sound="a flap-flap and a papery hiss",
        reveal="a loose silver banner blowing in the fan",
        need_help=1,
        need_kindness=1,
        comfort="a knot tied tight",
        tags={"wind", "banner", "temporary"},
    ),
}

RESPONSES = {
    "ask_adult": Response(
        id="ask_adult",
        label="ask a grown-up",
        sense=3,
        help=3,
        kindness=2,
        opening_text="{child} took one careful breath, slipped back to the {adult}, and said, \"Something is in the dark, and I think it may need help.\"",
        reveal_text="The {adult} came with a flashlight, and {child} stayed close instead of running. Behind {place} they found {reveal}.",
        lingering_text="The {adult} came later and found {reveal}, but {child} had lost precious minutes to fear.",
        qa_text="asked a grown-up and stayed nearby while help came",
        tags={"adult", "help"},
    ),
    "call_gently": Response(
        id="call_gently",
        label="call gently",
        sense=3,
        help=2,
        kindness=3,
        opening_text="{child} swallowed hard and whispered, \"Hello? We are not here to tease you. Are you all right?\"",
        reveal_text="{child} spoke softly again, and {friend} stopped whispering about ghosts. From behind {place} came {reveal}.",
        lingering_text="{child} called out, but then backed away too quickly, and the frightened thing stayed hidden until a grown-up finally came.",
        qa_text="spoke softly first and turned the scary moment into a kind one",
        tags={"gentle", "kindness"},
    ),
    "peek_alone": Response(
        id="peek_alone",
        label="peek alone",
        sense=2,
        help=1,
        kindness=1,
        opening_text="{child} took three tiny steps forward and peeped around the edge while {friend} clutched {friend}'s sleeve.",
        reveal_text="{child} peeped around {place} and discovered {reveal}.",
        lingering_text="{child} peeped around {place} and discovered {reveal}, but froze instead of helping right away.",
        qa_text="peeked alone to see what the shape was",
        tags={"peek"},
    ),
    "laugh_and_run": Response(
        id="laugh_and_run",
        label="laugh and run",
        sense=1,
        help=0,
        kindness=0,
        opening_text="{friend} laughed too loudly, and both children ran for the door.",
        reveal_text="",
        lingering_text="",
        qa_text="laughed and ran away",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "June", "Ivy", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Owen", "Finn", "Theo", "Eli", "Sam"]
TRAITS = ["careful", "kind", "curious", "steady", "bold"]


@dataclass
class StoryParams:
    setup: str
    source: str
    response: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setup="shelter",
        source="lost_child",
        response="call_gently",
        child_name="Mina",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        adult_type="teacher",
        trait="careful",
    ),
    StoryParams(
        setup="stage",
        source="kitten",
        response="ask_adult",
        child_name="Leo",
        child_gender="boy",
        friend_name="June",
        friend_gender="girl",
        adult_type="teacher",
        trait="steady",
    ),
    StoryParams(
        setup="fair",
        source="banner",
        response="peek_alone",
        child_name="Nora",
        child_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        adult_type="caretaker",
        trait="curious",
    ),
    StoryParams(
        setup="fair",
        source="kitten",
        response="peek_alone",
        child_name="Eli",
        child_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        adult_type="caretaker",
        trait="bold",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for setup_id, setup in SETUPS.items():
        for source_id, source in SOURCES.items():
            if valid_setup_source(setup, source):
                combos.append((setup_id, source_id))
    return combos


KNOWLEDGE = {
    "gymnasium": [
        ("What is a gymnasium?",
         "A gymnasium is a big room at a school where people play games, exercise, and sometimes hold large events.")
    ],
    "temporary": [
        ("What does temporary mean?",
         "Temporary means something is only there for a short time. It is not meant to stay forever.")
    ],
    "ghost": [
        ("Why can a place seem spooky even when there is no ghost?",
         "Dim light, echoes, and flapping cloth can make ordinary things seem mysterious. Our brains sometimes guess \"ghost\" before we know the real cause.")
    ],
    "kindness": [
        ("Why is kindness important when something seems scary?",
         "Because the scary thing might really be a person or animal that needs help. A gentle voice can make frightened others feel safe enough to answer.")
    ],
    "help": [
        ("Why is it smart to ask a grown-up for help?",
         "A grown-up can bring light, calm, and help when a problem is confusing. Asking for help is brave, not babyish.")
    ],
    "kitten": [
        ("Why might a kitten cry in a big room?",
         "A kitten can feel scared and lost in a big echoing place. It may mew softly because it wants warmth and help.")
    ],
    "storm": [
        ("Why would people use a school as a shelter during a storm?",
         "A school building is large and sturdy, so it can give people a safe place to wait while bad weather passes.")
    ],
    "banner": [
        ("Why does cloth flap when air blows on it?",
         "Moving air pushes light cloth and makes it lift, wave, and slap. In dim light, that movement can look strange.")
    ],
}
KNOWLEDGE_ORDER = ["gymnasium", "temporary", "ghost", "kindness", "help", "kitten", "storm", "banner"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setup = f["setup"]
    source = f["source_cfg"]
    response = f["response"]
    return [
        f'Write a soft ghost story for a 3-to-5-year-old set in a gymnasium that has been turned into a temporary {setup.title}.',
        f"Tell a spooky-but-gentle story where {child.id} hears a ghostly sound, chooses to {response.label}, and learns that fear should not come before kindness.",
        f'Write a happy-ending moral story that includes the words "gymnasium" and "temporary" and reveals that the ghostly thing was really {source.title}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    adult = f["adult"]
    setup = f["setup"]
    source = f["source_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            f"It happens in a school gymnasium that has been turned into a temporary {setup.title}. "
            f"The changed room is what makes the familiar place feel strange and spooky."
        ),
        (
            "Why did the gymnasium seem haunted at first?",
            f"It was dim and echoing, and something pale moved near {setup.spooky_place}. "
            f"The sound {source.sound} made the children think of a ghost before they knew the truth."
        ),
        (
            f"What did {child.id} do when the children got scared?",
            f"{child.id} chose to {response.qa_text}. "
            f"That choice matters because it turned a frightened moment into a careful one."
        ),
    ]
    if outcome == "warm":
        qa.append((
            "What was the 'ghost' really?",
            f"It was really {source.reveal}. "
            f"The pale shape seemed spooky only because the children saw it before they understood it."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily because the hidden trouble was helped and the fear passed. "
            f"By the end, the gymnasium felt warm again, and the children had learned to answer spooky things with kindness."
        ))
        qa.append((
            "What is the moral of the story?",
            f"The moral is that brave kindness is better than wild guessing. "
            f"When something seems scary, it may really be someone who needs help."
        ))
    else:
        qa.append((
            "Did the children learn anything even though they hesitated?",
            f"Yes. They learned that seeing the truth is not the same as helping right away. "
            f"{child.id} wished for more kindness and quicker courage once a grown-up made things safe."
        ))
        qa.append((
            "How did the story end?",
            f"It still ended safely, but with a softer lesson. "
            f"The gymnasium was no longer spooky once help arrived, and {child.id} understood that fear should not make us slow to help."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gymnasium", "temporary", "ghost", "kindness", "help"}
    if "storm" in f["setup"].tags:
        tags.add("storm")
    if "kitten" in f["source_cfg"].tags:
        tags.add("kitten")
    if "banner" in f["source_cfg"].tags:
        tags.add("banner")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo_rejection(setup: Setup, source: Source) -> str:
    return (
        f"(No story: {source.title} is not a plausible hidden cause in the temporary {setup.title}. "
        f"Pick one of: {', '.join(sorted(source.allowed_setups))} for that source.)"
    )


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    options = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {options}.)"
    )


ASP_RULES = r"""
valid(Su, So) :- setup(Su), source(So), compatible(So, Su).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

warm_choice :- chosen_source(So), chosen_response(R),
               source_need_help(So, HN), help(R, H), H >= HN,
               source_need_kind(So, KN), kind(R, K), K >= KN.

outcome(warm) :- warm_choice.
outcome(lingering) :- not warm_choice.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setup_id in SETUPS:
        lines.append(asp.fact("setup", setup_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_need_help", source_id, source.need_help))
        lines.append(asp.fact("source_need_kind", source_id, source.need_kindness))
        for setup_id in sorted(source.allowed_setups):
            lines.append(asp.fact("compatible", source_id, setup_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("help", response_id, response.help))
        lines.append(asp.fact("kind", response_id, response.kindness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_gate = set(valid_combos())
    clingo_gate = set(asp_valid_combos())
    if python_gate == clingo_gate:
        print(f"OK: gate matches valid_combos() ({len(python_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_gate - python_gate:
            print("  only in clingo:", sorted(clingo_gate - python_gate))
        if python_gate - clingo_gate:
            print("  only in python:", sorted(python_gate - clingo_gate))

    python_sense = {r.id for r in sensible_responses()}
    clingo_sense = set(asp_sensible())
    if python_sense == clingo_sense:
        print(f"OK: sensible responses match ({sorted(python_sense)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  python:", sorted(python_sense))
        print("  clingo:", sorted(clingo_sense))

    cases = list(CURATED)
    for setup_id, source_id in valid_combos():
        for response_id in sorted(RESPONSES):
            if RESPONSES[response_id].sense < SENSE_MIN:
                continue
            cases.append(StoryParams(
                setup=setup_id,
                source=source_id,
                response=response_id,
                child_name="Mina",
                child_gender="girl",
                friend_name="Ben",
                friend_gender="boy",
                adult_type=SETUPS[setup_id].adult_role,
                trait="careful",
            ))
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        _ = sample.to_json()
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Soft ghost-story world: a child in a gymnasium turned into a temporary place, a spooky mistake, and a lesson in kindness."
    )
    ap.add_argument("--setup", choices=SETUPS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["teacher", "caretaker"])
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible setup/source set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setup and args.source:
        setup = SETUPS[args.setup]
        source = SOURCES[args.source]
        if not valid_setup_source(setup, source):
            raise StoryError(explain_combo_rejection(setup, source))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setup is None or combo[0] == args.setup)
        and (args.source is None or combo[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setup_id, source_id = rng.choice(sorted(combos))
    setup = SETUPS[setup_id]
    source = SOURCES[source_id]

    if args.response is not None:
        response_id = args.response
    else:
        good = [r.id for r in warm_responses_for(source)]
        if not good:
            good = [r.id for r in sensible_responses()]
        response_id = rng.choice(sorted(good))

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    adult_type = args.adult or setup.adult_role
    trait = rng.choice(TRAITS)

    return StoryParams(
        setup=setup_id,
        source=source_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setup not in SETUPS:
        raise StoryError(f"(Unknown setup: {params.setup})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    setup = SETUPS[params.setup]
    source = SOURCES[params.source]
    response = RESPONSES[params.response]
    if not valid_setup_source(setup, source):
        raise StoryError(explain_combo_rejection(setup, source))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))

    world = tell(
        setup=setup,
        source=source,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setup, source) combos:\n")
        for setup_id, source_id in combos:
            print(f"  {setup_id:8} {source_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.setup} / {p.source} / {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
