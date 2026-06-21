#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/demographic_rhyme_misunderstanding_humor_bedtime_story.py
=====================================================================================

A standalone story world about a child at bedtime who overhears the word
"demographic," misunderstands it as a nighttime creature, and is gently guided
toward the real meaning with rhyme, humor, and a calm ending.

The world model keeps a few concrete state variables:

- physical meters: room darkness, bedtime readiness, sleepiness, night-light glow
- emotional memes: curiosity, confusion, fear, calm, amusement, trust

The story shape is always:

1. warm bedtime setup
2. overheard grown-up word
3. misunderstanding in the dark
4. playful explanation with a chart or flyer
5. a rhyming bedtime line that proves the fear changed into calm

Run it
------
python storyworlds/worlds/gpt-5.4/demographic_rhyme_misunderstanding_humor_bedtime_story.py
python storyworlds/worlds/gpt-5.4/demographic_rhyme_misunderstanding_humor_bedtime_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/demographic_rhyme_misunderstanding_humor_bedtime_story.py --all --qa
python storyworlds/worlds/gpt-5.4/demographic_rhyme_misunderstanding_humor_bedtime_story.py --json
python storyworlds/worlds/gpt-5.4/demographic_rhyme_misunderstanding_humor_bedtime_story.py --verify
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
        female = {"girl", "mother", "mom", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "dad", "grandfather", "man", "uncle"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class FamilySetting:
    id: str
    place: str
    room_detail: str
    neighborhood: str
    household: str
    bedtime_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BigWord:
    id: str
    word: str
    source_text: str
    real_meaning: str
    child_guess: str
    rhyme_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ExplanationProp:
    id: str
    label: str
    phrase: str
    visual: str
    shows: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    cuddle_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LightSource:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_dark_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    room = world.entities.get("room")
    if child is None or room is None:
        return out
    if child.memes["confusion"] < THRESHOLD or room.meters["dark"] < THRESHOLD:
        return out
    sig = ("dark_confusion", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_explanation_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    paper = world.entities.get("prop")
    if child is None or paper is None:
        return out
    if child.meters["understands"] < THRESHOLD or paper.meters["seen"] < THRESHOLD:
        return out
    sig = ("explanation_calm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["confusion"] = 0.0
    child.memes["calm"] += 1
    child.memes["amusement"] += 1
    out.append("__calm__")
    return out


def _r_rhyme_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["rhyme_said"] < THRESHOLD or child.memes["calm"] < THRESHOLD:
        return out
    sig = ("rhyme_sleep", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["sleepy"] += 1
    child.meters["ready_for_sleep"] += 1
    out.append("__sleepy__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="dark_confusion", tag="emotional", apply=_r_dark_confusion),
    Rule(name="explanation_calm", tag="emotional", apply=_r_explanation_calm),
    Rule(name="rhyme_sleep", tag="emotional", apply=_r_rhyme_sleep),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "apartment": FamilySetting(
        id="apartment",
        place="a small apartment bedroom",
        room_detail="A soft blanket made a little hill over the child's knees, and the hall light drew a gold line under the door.",
        neighborhood="their busy apartment building",
        household="an apartment home with neighbors close by",
        bedtime_sound="a faraway elevator hummed and then went quiet",
        tags={"bedroom", "family"},
    ),
    "duplex": FamilySetting(
        id="duplex",
        place="a cozy upstairs bedroom",
        room_detail="A patchwork quilt lay smooth on the bed, and moonlight sat on the window ledge like a pale cat.",
        neighborhood="their duplex on a tree-lined street",
        household="a duplex where cousins and grandparents visited often",
        bedtime_sound="the heater clicked once and settled down",
        tags={"bedroom", "family"},
    ),
    "rowhouse": FamilySetting(
        id="rowhouse",
        place="a warm rowhouse bedroom",
        room_detail="Stuffed animals leaned against the pillows, and a curtain puffed gently whenever the night breeze slipped past.",
        neighborhood="their rowhouse block",
        household="a rowhouse full of cousins, stories, and shoes by the door",
        bedtime_sound="someone downstairs rinsed one last teacup",
        tags={"bedroom", "family"},
    ),
}

BIG_WORDS = {
    "demographic": BigWord(
        id="demographic",
        word="demographic",
        source_text="a demographic chart for the neighborhood meeting",
        real_meaning="a demographic is a group of people described in some shared way, like age or where they live",
        child_guess="a polite but sneaky night creature wearing a map like a cape",
        rhyme_line="Demographic, not magic-giraffic",
        tags={"demographic", "misunderstanding"},
    ),
}

PROPS = {
    "flyer": ExplanationProp(
        id="flyer",
        label="flyer",
        phrase="a folded meeting flyer",
        visual="big circles in blue and orange",
        shows="it showed groups of neighbors on a simple chart",
        tags={"chart", "paper"},
    ),
    "poster": ExplanationProp(
        id="poster",
        label="poster",
        phrase="a rolled-up community poster",
        visual="tiny bars in happy colors",
        shows="it showed groups of people in the neighborhood",
        tags={"chart", "paper"},
    ),
    "tablet": ExplanationProp(
        id="tablet",
        label="tablet",
        phrase="a glowing tablet screen",
        visual="bright little blocks and dots",
        shows="it showed a chart about who lived nearby",
        tags={"chart", "screen"},
    ),
}

COMFORTS = {
    "rabbit": ComfortItem(
        id="rabbit",
        label="rabbit",
        phrase="a floppy rabbit",
        cuddle_line="The rabbit's long ears folded over the blanket as if even the toy were getting sleepy.",
        tags={"toy"},
    ),
    "whale": ComfortItem(
        id="whale",
        label="whale",
        phrase="a squishy blue whale",
        cuddle_line="The whale toy looked so round and calm that it made the whole pillow seem softer.",
        tags={"toy"},
    ),
    "dinosaur": ComfortItem(
        id="dinosaur",
        label="dinosaur",
        phrase="a tiny green dinosaur",
        cuddle_line="The dinosaur's stitched grin was so cheerful that it was hard to stay worried beside it.",
        tags={"toy"},
    ),
}

LIGHTS = {
    "nightlight": LightSource(
        id="nightlight",
        label="night-light",
        phrase="a pear-shaped night-light",
        glow="glowed the color of warm honey",
        tags={"light"},
    ),
    "starlamp": LightSource(
        id="starlamp",
        label="star lamp",
        phrase="a little star lamp",
        glow="spilled soft dots across the ceiling",
        tags={"light"},
    ),
    "halllight": LightSource(
        id="halllight",
        label="hall light",
        phrase="the hall light",
        glow="made a bright stripe under the door",
        tags={"light"},
    ),
}

CHILDREN = [
    {"name": "Mina", "gender": "girl", "heritage": "Pakistani American"},
    {"name": "Jayden", "gender": "boy", "heritage": "Black American"},
    {"name": "Sofía", "gender": "girl", "heritage": "Mexican American"},
    {"name": "Noah", "gender": "boy", "heritage": "Jewish American"},
    {"name": "Asha", "gender": "girl", "heritage": "Indian American"},
    {"name": "Mateo", "gender": "boy", "heritage": "Puerto Rican American"},
]

CAREGIVERS = [
    {"name": "Mom", "type": "mother"},
    {"name": "Dad", "type": "father"},
    {"name": "Grandma", "type": "grandmother"},
    {"name": "Grandpa", "type": "grandfather"},
]


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    child_heritage: str
    caregiver_name: str
    caregiver_type: str
    prop: str
    comfort: str
    light: str
    word: str = "demographic"
    seed: Optional[int] = None


def valid_combo(setting_id: str, prop_id: str, light_id: str, word_id: str) -> bool:
    return (
        setting_id in SETTINGS
        and prop_id in PROPS
        and light_id in LIGHTS
        and word_id in BIG_WORDS
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for prop_id in PROPS:
            for light_id in LIGHTS:
                for word_id in BIG_WORDS:
                    if valid_combo(setting_id, prop_id, light_id, word_id):
                        combos.append((setting_id, prop_id, light_id, word_id))
    return combos


def explain_rejection(setting_id: str, prop_id: str, light_id: str, word_id: str) -> str:
    bits: list[str] = []
    if setting_id not in SETTINGS:
        bits.append(f"unknown setting '{setting_id}'")
    if prop_id not in PROPS:
        bits.append(f"unknown prop '{prop_id}'")
    if light_id not in LIGHTS:
        bits.append(f"unknown light '{light_id}'")
    if word_id not in BIG_WORDS:
        bits.append(f"unknown word '{word_id}'")
    if bits:
        return "(No story: " + "; ".join(bits) + ".)"
    return "(No story: this bedtime misunderstanding needs a valid setting, a readable chart-like prop, a gentle light source, and a supported big word.)"


def predict_worry(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    room = sim.get("room")
    child.memes["confusion"] += 1
    room.meters["dark"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": child.memes["fear"],
        "confusion": child.memes["confusion"],
    }


def setup_bedtime(world: World, setting: FamilySetting, child: Entity, caregiver: Entity,
                  comfort: ComfortItem, light: LightSource) -> None:
    world.say(
        f"In {setting.place}, {child.id}, a {child.attrs['heritage']} child, tucked {child.pronoun('possessive')} feet under the blanket while {caregiver.label_word} straightened the room for bed."
    )
    world.say(setting.room_detail)
    world.say(
        f"Nearby sat {comfort.phrase}, and {light.phrase} {light.glow}. {setting.bedtime_sound}."
    )
    child.meters["sleepy"] += 0.5
    child.memes["trust"] += 1


def overhear_word(world: World, caregiver: Entity, child: Entity, word: BigWord, prop: ExplanationProp) -> None:
    child.memes["curiosity"] += 1
    child.memes["confusion"] += 1
    world.say(
        f"From the doorway, {child.id} heard {caregiver.label_word} murmur about {word.source_text} and pat {prop.phrase} against {caregiver.pronoun('possessive')} palm."
    )
    world.say(
        f'The word "{word.word}" sounded much too large for a sleepy room.'
    )


def imagine_wrong_thing(world: World, child: Entity, word: BigWord, comfort: ComfortItem) -> None:
    room = world.get("room")
    room.meters["dark"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"A demographic?" {child.id} whispered. "{child.pronoun("subject").capitalize()}s it a creature that tiptoes through the hall and counts pillows?"'
    )
    world.say(
        f"To {child.id}, the word began to sound like {word.child_guess}. {comfort.cuddle_line}"
    )


def caregiver_returns(world: World, caregiver: Entity, child: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{caregiver.label_word.capitalize()} came back, noticed the round worried eyes, and sat on the edge of the bed until the mattress gave a little sigh."
    )


def explain_word(world: World, caregiver: Entity, child: Entity, word: BigWord,
                 prop: ExplanationProp, light: LightSource) -> None:
    prop_ent = world.get("prop")
    prop_ent.meters["seen"] += 1
    child.meters["understands"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"No, sleepy bean," {caregiver.label_word} said with a smile. "A {word.word} is not a monster at all. {word.real_meaning.capitalize()}."'
    )
    world.say(
        f"{caregiver.label_word.capitalize()} opened {prop.phrase} under {light.phrase}. {prop.visual.capitalize()} shone on the page, and {prop.shows}."
    )
    world.say(
        f'"So it is about people, not peeping?" {child.id} asked.'
    )


def laugh_and_rhyme(world: World, caregiver: Entity, child: Entity, word: BigWord) -> None:
    child.memes["amusement"] += 1
    child.memes["calm"] += 1
    child.meters["rhyme_said"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{caregiver.label_word.capitalize()} laughed softly. "Right. No pillow-sniffing demographic in here."'
    )
    world.say(
        f'Together they made a silly rhyme: "{word.rhyme_line}."'
    )


def settle_to_sleep(world: World, child: Entity, caregiver: Entity, comfort: ComfortItem) -> None:
    world.say(
        f"{child.id} hugged {comfort.phrase} and gave one last sleepy giggle."
    )
    if child.meters["ready_for_sleep"] >= THRESHOLD:
        world.say(
            f"Soon the strange word was only a word again, and not a shadowy thing at all. {child.id}'s breathing grew slow while {caregiver.label_word} pulled the blanket snug."
        )
    else:
        world.say(
            f"The room felt kinder now, and {child.id} settled down while {caregiver.label_word} pulled the blanket snug."
        )


def tell(setting: FamilySetting, word: BigWord, prop: ExplanationProp, comfort: ComfortItem,
         light: LightSource, child_name: str, child_gender: str, child_heritage: str,
         caregiver_name: str, caregiver_type: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={"heritage": child_heritage},
        tags={"child"},
    ))
    caregiver = world.add(Entity(
        id=caregiver_name,
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label=caregiver_name,
        tags={"adult"},
    ))
    world.add(Entity(
        id="room",
        type="room",
        label=setting.place,
        tags={"room"},
    ))
    world.add(Entity(
        id="prop",
        type="paper" if prop.id != "tablet" else "screen",
        label=prop.label,
        phrase=prop.phrase,
        tags=set(prop.tags),
    ))

    setup_bedtime(world, setting, child, caregiver, comfort, light)
    world.para()
    overhear_word(world, caregiver, child, word, prop)
    imagine_wrong_thing(world, child, word, comfort)
    caregiver_returns(world, caregiver, child)
    world.para()
    explain_word(world, caregiver, child, word, prop, light)
    laugh_and_rhyme(world, caregiver, child, word)
    world.para()
    settle_to_sleep(world, child, caregiver, comfort)

    world.facts.update(
        setting=setting,
        child=child,
        caregiver=caregiver,
        word=word,
        prop=prop,
        comfort=comfort,
        light=light,
        feared=child.memes["fear"] >= THRESHOLD,
        understood=child.meters["understands"] >= THRESHOLD,
        sleepy=child.meters["ready_for_sleep"] >= THRESHOLD,
        rhyme_used=child.meters["rhyme_said"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "demographic": [
        (
            "What does demographic mean?",
            "A demographic is a group of people described in some shared way, like their age, where they live, or another simple trait. It is a word people use when they talk about communities and patterns."
        )
    ],
    "chart": [
        (
            "What is a chart?",
            "A chart is a simple picture that helps people understand information. It can use bars, circles, or dots to show ideas clearly."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime routines help children sleep?",
            "Bedtime routines help because the same calm steps happen in the same order, and the body learns that sleep is coming next. That makes it easier to feel safe and drowsy."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like cat and hat. Rhymes can make language feel playful and easy to remember."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or thinks something the wrong way. Asking a question can clear it up."
        )
    ],
    "nightlight": [
        (
            "What does a night-light do?",
            "A night-light gives a small soft glow in the dark. It can help a room feel less scary at bedtime."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    setting = f["setting"]
    word = f["word"]
    return [
        f'Write a gentle bedtime story for a young child that includes the word "{word.word}" and turns a misunderstanding into a laugh.',
        f"Tell a cozy story set in {setting.place} where {child.id}, a {child.attrs['heritage']} child, overhears a grown-up word and imagines the wrong thing until {caregiver.label_word} explains it.",
        f'Write a child-facing story that uses rhyme, humor, and a soft bedtime ending after someone misunderstands the word "{word.word}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    word = f["word"]
    prop = f["prop"]
    light = f["light"]
    comfort = f["comfort"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a {child.attrs['heritage']} child getting ready for bed, and {caregiver.label_word}, who helps explain a confusing word."
        ),
        (
            f"Where does the story happen?",
            f"It happens in {setting.place}. The quiet room and bedtime sounds make the misunderstanding feel bigger at first."
        ),
        (
            f"What word did {child.id} hear?",
            f'{child.id} heard the word "{word.word}." It sounded strange and enormous in the sleepy room, so {child.pronoun("subject")} began to imagine the wrong thing.'
        ),
        (
            f"What did {child.id} think a demographic was?",
            f"{child.id} imagined it was {word.child_guess}. That funny mistake happened because the word was unfamiliar and the room was already dark and dreamy."
        ),
        (
            f"How did {caregiver.label_word} explain the word?",
            f"{caregiver.label_word.capitalize()} showed {prop.phrase} under {light.phrase} and explained that {word.real_meaning}. Seeing the page helped turn a spooky guess into a clear idea."
        ),
    ]
    if f["rhyme_used"]:
        qa.append(
            (
                "What made the story funny instead of scary?",
                f"The grown-up and child made a silly rhyme together and laughed at the mistake. That joke changed the mood because the word stopped sounding like a creature and started sounding like something they understood."
            )
        )
    if f["sleepy"]:
        qa.append(
            (
                f"How did the story end?",
                f"It ended with {child.id} hugging {comfort.phrase} and settling down to sleep. The room felt calm again because the misunderstanding had been explained."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"demographic", "chart", "bedtime", "rhyme", "misunderstanding"}
    if world.facts["light"].id == "nightlight":
        tags.add("nightlight")
    out: list[tuple[str, str]] = []
    for key in ["demographic", "chart", "bedtime", "rhyme", "misunderstanding", "nightlight"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="apartment",
        child_name="Mina",
        child_gender="girl",
        child_heritage="Pakistani American",
        caregiver_name="Mom",
        caregiver_type="mother",
        prop="flyer",
        comfort="rabbit",
        light="nightlight",
        word="demographic",
    ),
    StoryParams(
        setting="duplex",
        child_name="Jayden",
        child_gender="boy",
        child_heritage="Black American",
        caregiver_name="Grandma",
        caregiver_type="grandmother",
        prop="poster",
        comfort="whale",
        light="starlamp",
        word="demographic",
    ),
    StoryParams(
        setting="rowhouse",
        child_name="Sofía",
        child_gender="girl",
        child_heritage="Mexican American",
        caregiver_name="Dad",
        caregiver_type="father",
        prop="tablet",
        comfort="dinosaur",
        light="halllight",
        word="demographic",
    ),
]


ASP_RULES = r"""
valid(S, P, L, W) :- setting(S), prop(P), light(L), word(W).

% Predictive mood shift:
fear_after_overhear(yes) :- dark_room, child_confused.
fear_after_overhear(no)  :- not dark_room.
fear_after_overhear(no)  :- not child_confused.

calm_after_explanation(yes) :- saw_prop, understood_word.
sleepy_end(yes) :- calm_after_explanation(yes), used_rhyme.

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for prop_id in PROPS:
        lines.append(asp.fact("prop", prop_id))
    for light_id in LIGHTS:
        lines.append(asp.fact("light", light_id))
    for word_id in BIG_WORDS:
        lines.append(asp.fact("word", word_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_flags() -> tuple[str, str, str]:
    import asp

    extra = "\n".join([
        "dark_room.",
        "child_confused.",
        "saw_prop.",
        "understood_word.",
        "used_rhyme.",
    ])
    model = asp.one_model(
        asp_program(
            extra,
            "#show fear_after_overhear/1.\n#show calm_after_explanation/1.\n#show sleepy_end/1.",
        )
    )
    fear = asp.atoms(model, "fear_after_overhear")[0][0]
    calm = asp.atoms(model, "calm_after_explanation")[0][0]
    sleepy = asp.atoms(model, "sleepy_end")[0][0]
    return fear, calm, sleepy


def verify_smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story is empty.")
    if "demographic" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not include the seed word.")
    if not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: QA generation failed.")


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    fear, calm, sleepy = asp_story_flags()
    if (fear, calm, sleepy) == ("yes", "yes", "yes"):
        print("OK: ASP mood flags match the intended story arc.")
    else:
        rc = 1
        print("MISMATCH in ASP mood flags:", (fear, calm, sleepy))

    try:
        verify_smoke_generation()
        print("OK: smoke generation passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime misunderstanding story world with rhyme and humor."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--word", choices=BIG_WORDS, default=None)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-heritage")
    ap.add_argument("--caregiver-name")
    ap.add_argument("--caregiver-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    word_id = args.word or "demographic"
    if any(v is not None for v in [args.setting, args.prop, args.light, word_id]):
        setting_id = args.setting or rng.choice(sorted(SETTINGS))
        prop_id = args.prop or rng.choice(sorted(PROPS))
        light_id = args.light or rng.choice(sorted(LIGHTS))
        if not valid_combo(setting_id, prop_id, light_id, word_id):
            raise StoryError(explain_rejection(setting_id, prop_id, light_id, word_id))
    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.prop is None or combo[1] == args.prop)
        and (args.light is None or combo[2] == args.light)
        and (word_id is None or combo[3] == word_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, prop_id, light_id, word_id = rng.choice(sorted(combos))

    child_choice = rng.choice(CHILDREN)
    caregiver_choice = rng.choice(CAREGIVERS)

    child_name = args.child_name or child_choice["name"]
    child_gender = args.child_gender or child_choice["gender"]
    child_heritage = args.child_heritage or child_choice["heritage"]
    caregiver_name = args.caregiver_name or caregiver_choice["name"]
    caregiver_type = args.caregiver_type or caregiver_choice["type"]
    comfort_id = args.comfort or rng.choice(sorted(COMFORTS))

    return StoryParams(
        setting=setting_id,
        child_name=child_name,
        child_gender=child_gender,
        child_heritage=child_heritage,
        caregiver_name=caregiver_name,
        caregiver_type=caregiver_type,
        prop=prop_id,
        comfort=comfort_id,
        light=light_id,
        word=word_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(explain_rejection(params.setting, params.prop, params.light, params.word))
    if params.prop not in PROPS:
        raise StoryError(explain_rejection(params.setting, params.prop, params.light, params.word))
    if params.light not in LIGHTS:
        raise StoryError(explain_rejection(params.setting, params.prop, params.light, params.word))
    if params.word not in BIG_WORDS:
        raise StoryError(explain_rejection(params.setting, params.prop, params.light, params.word))
    if params.comfort not in COMFORTS:
        raise StoryError(f"(No story: unknown comfort item '{params.comfort}'.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unsupported child gender '{params.child_gender}'.)")
    if params.caregiver_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(No story: unsupported caregiver type '{params.caregiver_type}'.)")

    world = tell(
        setting=SETTINGS[params.setting],
        word=BIG_WORDS[params.word],
        prop=PROPS[params.prop],
        comfort=COMFORTS[params.comfort],
        light=LIGHTS[params.light],
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_heritage=params.child_heritage,
        caregiver_name=params.caregiver_name,
        caregiver_type=params.caregiver_type,
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
        print(asp_program("", "#show valid/4.\n#show fear_after_overhear/1.\n#show calm_after_explanation/1.\n#show sleepy_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, prop, light, word) combos:\n")
        for setting_id, prop_id, light_id, word_id in combos:
            print(f"  {setting_id:10} {prop_id:8} {light_id:10} {word_id}")
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
            header = f"### {p.child_name}: {p.word} at bedtime in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
