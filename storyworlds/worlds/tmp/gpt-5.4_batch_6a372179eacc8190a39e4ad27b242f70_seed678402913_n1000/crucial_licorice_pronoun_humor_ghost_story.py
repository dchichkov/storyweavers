#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crucial_licorice_pronoun_humor_ghost_story.py
========================================================================

A small ghost-story-flavored simulation with a comic reveal.

Seed words and instruments
--------------------------
Words: crucial, licorice, pronoun
Features: Humor
Style: Ghost Story

Premise
-------
On a windy evening, a child sees a white, wobbly shape in a spooky part of the
house and thinks it might be a ghost. The crucial choice is how to respond:
panic is refused, while a polite, brave approach lets the child discover who is
really under the sheet. A strand of licorice helps draw the "ghost" close, and
a gentle joke about not guessing somebody's pronoun turns the scare into a
laugh.

Run it
------
    python storyworlds/worlds/gpt-5.4/crucial_licorice_pronoun_humor_ghost_story.py
    python storyworlds/worlds/gpt-5.4/crucial_licorice_pronoun_humor_ghost_story.py --place pantry --figure grandpa
    python storyworlds/worlds/gpt-5.4/crucial_licorice_pronoun_humor_ghost_story.py --method scream
    python storyworlds/worlds/gpt-5.4/crucial_licorice_pronoun_humor_ghost_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/crucial_licorice_pronoun_humor_ghost_story.py --verify
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
        explicit = self.attrs.get("pronouns")
        if explicit:
            return explicit[case]
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "grandpa", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    spooky_line: str
    ending_line: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Figure:
    id: str
    label: str
    type: str
    phrase: str
    reason: str
    allowed_places: set[str] = field(default_factory=set)
    hungry: bool = False
    laugh_line: str = ""
    pronouns: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    sense: int
    uses_licorice: bool
    text: str
    qa_text: str
    brave_gain: int
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


def _r_spooky(world: World) -> list[str]:
    out: list[str] = []
    hidden = world.entities.get("ghost")
    room = world.entities.get("room")
    if not hidden or not room:
        return out
    if hidden.meters["sheeted"] < THRESHOLD or room.meters["dark"] < THRESHOLD:
        return out
    sig = ("spooky", hidden.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hidden.meters["spooky"] += 1
    for ent in world.entities.values():
        if ent.role in {"hero", "helper"}:
            ent.memes["fear"] += 1
            ent.memes["curiosity"] += 1
    out.append("__spooky__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    hero = world.entities.get("hero")
    if not ghost or not hero:
        return out
    if hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("trust", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["trust"] += 1
    out.append("__trust__")
    return out


CAUSAL_RULES = [
    Rule(name="spooky", tag="tone", apply=_r_spooky),
    Rule(name="kindness", tag="social", apply=_r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def plausible_visit(place_id: str, figure_id: str) -> bool:
    return place_id in FIGURES[figure_id].allowed_places


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def best_method() -> Method:
    return max(METHODS.values(), key=lambda m: m.sense)


def outcome_of(params: "StoryParams") -> str:
    figure = FIGURES[params.figure]
    method = METHODS[params.method]
    return "snack_reveal" if method.uses_licorice and figure.hungry else "voice_reveal"


def explain_rejection(place_id: str, figure_id: str) -> str:
    place = PLACES[place_id]
    figure = FIGURES[figure_id]
    return (
        f"(No story: {figure.label} has no good reason to be haunting {place.label}. "
        f"In this world, {figure.pronouns['subject']} would not plausibly be there for "
        f"{figure.reason.lower()}.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    options = " / ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A funny ghost story can be spooky, "
        f"but the child should solve the mystery with a calmer move. Try: {options}.)"
    )


def reveal_prediction(place: Place, figure: Figure, method: Method) -> str:
    if method.uses_licorice and figure.hungry:
        return f"The licorice would probably draw the shape out in {place.label}."
    return f"A polite question would probably make the shape answer in {place.label}."


def setup_evening(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    room = world.add(Entity(id="room", type="room", label=place.label, role="room"))
    room.meters["dark"] += 1
    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"On a windy evening, {hero.id} and {helper.id} padded down the hall when "
        f"they saw {place.label} ahead. {place.spooky_line}"
    )
    world.say(
        f"A white shape wobbled in the dimness and gave a soft rustly sigh. "
        f"For one chilly second, it looked exactly like a ghost."
    )


def spot_ghost(world: World, ghost: Entity) -> None:
    ghost.meters["sheeted"] += 1
    ghost.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The shape drifted one step sideways, bumping the wall with a tiny thump. "
        f"That made it even spookier."
    )


def crucial_warning(world: World, hero: Entity, helper: Entity, method: Method, figure: Figure, place: Place) -> None:
    helper.memes["kindness"] += 1
    hero.memes["thoughtful"] += 1
    prediction = reveal_prediction(place, figure, method)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," whispered {helper.id}. "The crucial thing is not to point and shout '
        f'\'it\' before we know who is under that sheet. A ghost might want the right '
        f'pronoun too."'
    )
    world.say(
        f"{hero.id} blinked, because that was both polite and a little funny. {prediction}"
    )


def do_method(world: World, hero: Entity, helper: Entity, ghost: Entity, method: Method) -> None:
    hero.memes["bravery"] += method.brave_gain
    hero.memes["kindness"] += 1
    helper.memes["bravery"] += 1
    propagate(world, narrate=False)
    if method.uses_licorice:
        world.say(
            f"{hero.id} unwound a black rope of licorice from {hero.pronoun('possessive')} pocket "
            f"and laid it on the floor like a peace offering."
        )
        ghost.meters["tempted"] += 1
    world.say(method.text)


def reveal_by_voice(world: World, hero: Entity, helper: Entity, ghost: Entity, figure: Figure) -> None:
    ghost.meters["revealed"] += 1
    ghost.meters["hidden"] = 0.0
    for kid in (hero, helper):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["amusement"] += 1
    world.say(
        f'From under the sheet came a muffled answer: "Not a ghost. '
        f'Use {figure.pronouns["subject"]}/{figure.pronouns["object"]}, please."'
    )
    world.say(
        f"The white shape lifted the sheet, and there was {figure.phrase}. "
        f"{figure.reason}."
    )


def reveal_by_snack(world: World, hero: Entity, helper: Entity, ghost: Entity, figure: Figure) -> None:
    ghost.meters["revealed"] += 1
    ghost.meters["hidden"] = 0.0
    ghost.meters["tempted"] += 1
    for kid in (hero, helper):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["amusement"] += 1
    world.say(
        f"The shape froze. Then a hand sneaked out from under the sheet, picked up the licorice, "
        f"and gave a very un-ghostly chew."
    )
    world.say(
        f'"Well," said a familiar voice, "a real ghost would never stop for candy first." '
        f"The sheet slid down, and there was {figure.phrase}. {figure.reason}."
    )


def laugh_and_end(world: World, hero: Entity, helper: Entity, figure_ent: Entity, place: Place, figure: Figure) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    figure_ent.memes["joy"] += 1
    world.say(
        figure.laugh_line or f"{figure_ent.id} laughed so hard the sheet slipped off one shoulder."
    )
    world.say(
        f"Soon the scary corner of {place.label} did not feel haunted at all. {place.ending_line}"
    )


def tell(place: Place, figure_cfg: Figure, method: Method, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    figure_ent = world.add(
        Entity(
            id="ghost",
            kind="character",
            type=figure_cfg.type,
            role="ghost",
            label=figure_cfg.label,
            phrase=figure_cfg.phrase,
            attrs={"pronouns": dict(figure_cfg.pronouns)},
            tags=set(figure_cfg.tags),
        )
    )

    setup_evening(world, hero, helper, place)
    spot_ghost(world, figure_ent)

    world.para()
    crucial_warning(world, hero, helper, method, figure_cfg, place)
    do_method(world, hero, helper, figure_ent, method)

    world.para()
    if method.uses_licorice and figure_cfg.hungry:
        reveal_by_snack(world, hero, helper, figure_ent, figure_cfg)
    else:
        reveal_by_voice(world, hero, helper, figure_ent, figure_cfg)
    laugh_and_end(world, hero, helper, figure_ent, place, figure_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        figure=figure_ent,
        figure_cfg=figure_cfg,
        place=place,
        method=method,
        outcome="snack_reveal" if method.uses_licorice and figure_cfg.hungry else "voice_reveal",
        prediction=world.facts.get("prediction", ""),
        spooky=figure_ent.meters["spooky"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic stairs",
        spooky_line="The rafters creaked above them, and moonlight striped the steps like pale fingers.",
        ending_line="A minute later the attic stairs were only stairs again, and the moonlight looked more silvery than spooky.",
        allows={"cousin", "neighbor"},
        tags={"attic", "ghost"},
    ),
    "pantry": Place(
        id="pantry",
        label="the pantry door",
        spooky_line="Jars clicked softly inside, and the little glass pane shone like one watchful eye.",
        ending_line="Soon the pantry door stood wide open, smelling of crackers and laughter instead of mystery.",
        allows={"grandpa", "neighbor"},
        tags={"pantry", "ghost", "licorice"},
    ),
    "laundry": Place(
        id="laundry",
        label="the laundry room doorway",
        spooky_line="Fresh sheets swayed on the rack, and the dryer hummed like a sleepy monster.",
        ending_line="Soon the dryer hummed on, the sheets looked ordinary again, and nobody minded the shadows.",
        allows={"cousin", "aunt"},
        tags={"laundry", "ghost"},
    ),
}

FIGURES = {
    "cousin": Figure(
        id="cousin",
        label="cousin",
        type="girl",
        phrase="cousin Bea, wearing a bedsheet like a cape",
        reason="She had been practicing a surprise ghost dance and had tripped over the hem.",
        allowed_places={"attic", "laundry"},
        hungry=False,
        laugh_line='"Bea is a fine pronoun for me," she said, bowing under the sheet.',
        pronouns={"subject": "she", "object": "her", "possessive": "her"},
        tags={"costume", "family", "pronoun"},
    ),
    "grandpa": Figure(
        id="grandpa",
        label="grandpa",
        type="grandfather",
        phrase="Grandpa Ollie, wrapped in a white tablecloth",
        reason="He had come sneaking for a midnight snack and grabbed the wrong cloth in the dark.",
        allowed_places={"pantry"},
        hungry=True,
        laugh_line='"I was haunting the licorice jar," Grandpa admitted, still chewing.',
        pronouns={"subject": "he", "object": "him", "possessive": "his"},
        tags={"family", "licorice", "pronoun"},
    ),
    "aunt": Figure(
        id="aunt",
        label="aunt",
        type="aunt",
        phrase="Aunt Mira, tangled in a fresh white sheet",
        reason="She had been carrying laundry and had walked straight into her own washing.",
        allowed_places={"laundry"},
        hungry=False,
        laugh_line='"Next time I will haunt in stripes," Aunt Mira said, peeling the sheet from her hair.',
        pronouns={"subject": "she", "object": "her", "possessive": "her"},
        tags={"family", "laundry", "pronoun"},
    ),
    "neighbor": Figure(
        id="neighbor",
        label="neighbor",
        type="person",
        phrase="their neighbor Ash, hidden under a sheet with a flashlight under the chin",
        reason="They had come to invite the children to a backyard shadow show and had chosen a very silly entrance.",
        allowed_places={"attic", "pantry"},
        hungry=True,
        laugh_line='"They works just fine," Ash said. "Ghost manners appreciated."',
        pronouns={"subject": "they", "object": "them", "possessive": "their"},
        tags={"neighbor", "pronoun", "flashlight"},
    ),
}

METHODS = {
    "ask": Method(
        id="ask",
        sense=3,
        uses_licorice=False,
        text='In a steady voice, the children asked, "Hello? We do not want to guess. Who are you, and what pronoun should we use?"',
        qa_text="They asked politely who was under the sheet and which pronoun was right.",
        brave_gain=2,
        tags={"ask", "pronoun"},
    ),
    "offer": Method(
        id="offer",
        sense=3,
        uses_licorice=True,
        text='Then they said, "If you are friendly, you may come out for this licorice first."',
        qa_text="They offered licorice and spoke kindly to the figure.",
        brave_gain=2,
        tags={"licorice", "kindness"},
    ),
    "scream": Method(
        id="scream",
        sense=1,
        uses_licorice=False,
        text='They screamed and bolted for the nearest blanket fort.',
        qa_text="They screamed and ran.",
        brave_gain=0,
        tags={"panic"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "June", "Ivy", "Poppy", "Ada"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Max", "Finn", "Owen", "Leo", "Eli"]


@dataclass
class StoryParams:
    place: str
    figure: str
    method: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="pantry",
        figure="grandpa",
        method="offer",
        hero_name="June",
        hero_type="girl",
        helper_name="Milo",
        helper_type="boy",
    ),
    StoryParams(
        place="attic",
        figure="neighbor",
        method="ask",
        hero_name="Theo",
        hero_type="boy",
        helper_name="Ivy",
        helper_type="girl",
    ),
    StoryParams(
        place="laundry",
        figure="aunt",
        method="ask",
        hero_name="Lila",
        hero_type="girl",
        helper_name="Ben",
        helper_type="boy",
    ),
    StoryParams(
        place="laundry",
        figure="cousin",
        method="offer",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Finn",
        helper_type="boy",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id in PLACES:
        for figure_id in FIGURES:
            if plausible_visit(place_id, figure_id):
                combos.append((place_id, figure_id))
    return combos


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story that tries to feel spooky and mysterious. In funny ghost stories, the scary part often turns out to be less dangerous than it first seemed."
        )
    ],
    "licorice": [
        (
            "What is licorice?",
            "Licorice is a chewy candy that comes in ropes or twists. Some people love its strong taste, and some people think it is funny-looking too."
        )
    ],
    "pronoun": [
        (
            "What is a pronoun?",
            "A pronoun is a word you use instead of a name, like he, she, or they. Asking for the right pronoun is a polite way to talk about someone."
        )
    ],
    "costume": [
        (
            "Why can a sheet look spooky in the dark?",
            "A white sheet hides a person's shape and catches the light, so in the dark it can look floaty and strange. That is why costumes like that can make people jump."
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight under a face look spooky?",
            "Light shining up from below makes shadows fall in unusual places. That can make an ordinary face look mysterious for a moment."
        )
    ],
    "kindness": [
        (
            "Why is it smart to speak kindly when you are unsure who someone is?",
            "Kind words keep a scary moment from turning mean. They also make it easier for the other person to answer and clear up the misunderstanding."
        )
    ],
}

KNOWLEDGE_ORDER = ["ghost", "licorice", "pronoun", "costume", "flashlight", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    figure_cfg = f["figure_cfg"]
    method = f["method"]
    return [
        f'Write a funny ghost story for a 3-to-5-year-old that includes the words "crucial", "licorice", and "pronoun".',
        f"Tell a gentle spooky story where {hero.id} and {helper.id} see a ghostly shape near {place.label}, stay polite, and discover it is really {figure_cfg.label}.",
        f"Write a short humorous ghost story where children solve a scare by being brave and kind, using {method.id} instead of panicking.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    figure = f["figure"]
    figure_cfg = f["figure_cfg"]
    place = f["place"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, who thought they saw a ghost near {place.label}. The ghostly shape turned out to be {figure_cfg.phrase}."
        ),
        (
            f"Why did the shape look spooky at first?",
            f"It was dark, and a white sheet hid the person's real shape, so the figure looked floaty and strange. That is why the children first thought it might be a ghost."
        ),
        (
            "What was the crucial thing the children remembered?",
            f"They remembered not to point and call the figure 'it' before knowing who was there. The children decided to be polite and ask for the right pronoun instead."
        ),
        (
            f"How did {hero.id} and {helper.id} solve the mystery?",
            f"{method.qa_text} That brave, calm choice helped the hidden person answer instead of making the scare bigger."
        ),
    ]
    if outcome == "snack_reveal":
        qa.append(
            (
                "Why did the licorice help?",
                f"The figure was hungry, so the licorice tempted {figure.pronoun('object')} into reaching out from under the sheet. That silly little snack clue made the mystery fall apart at once."
            )
        )
    else:
        qa.append(
            (
                "How was the ghost finally revealed?",
                f"The person answered from under the sheet, telling the children who {figure.pronoun('subject')} was and which pronoun fit. Once the voice answered politely, the fear melted into laughter."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with everyone laughing in the once-spooky corner. {place.ending_line}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost", "kindness"}
    figure_cfg = world.facts["figure_cfg"]
    method = world.facts["method"]
    tags |= set(figure_cfg.tags)
    tags |= set(method.tags)
    place = world.facts["place"]
    tags |= set(place.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
plausible(P, F) :- place(P), figure(F), allowed(F, P).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

hungry(F) :- figure(F), figure_hungry(F).

outcome(snack_reveal) :- chosen_method(M), uses_licorice(M), chosen_figure(F), hungry(F).
outcome(voice_reveal) :- chosen_method(M), chosen_figure(F), not (uses_licorice(M), hungry(F)).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for figure_id, figure in FIGURES.items():
        lines.append(asp.fact("figure", figure_id))
        if figure.hungry:
            lines.append(asp.fact("figure_hungry", figure_id))
        for place_id in sorted(figure.allowed_places):
            lines.append(asp.fact("allowed", figure_id, place_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.uses_licorice:
            lines.append(asp.fact("uses_licorice", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show plausible/2."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_figure", params.figure),
            asp.fact("chosen_method", params.method),
        ]
    )
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
        print("MISMATCH in plausible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_methods = set(asp_sensible())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_methods)} python={sorted(python_methods)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke story came out empty")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny ghost-story world: a sheeted shape, a polite question, and a comic reveal."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--figure", choices=FIGURES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list plausible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.figure and not plausible_visit(args.place, args.figure):
        raise StoryError(explain_rejection(args.place, args.figure))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.figure is None or combo[1] == args.figure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, figure_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    hero_type = rng.choice(["girl", "boy"])
    helper_type = "boy" if hero_type == "girl" else "girl"
    hero_name = _pick_name(rng, hero_type)
    helper_name = _pick_name(rng, helper_type, avoid=hero_name)
    return StoryParams(
        place=place_id,
        figure=figure_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.figure not in FIGURES:
        raise StoryError(f"(Unknown figure '{params.figure}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    if not plausible_visit(params.place, params.figure):
        raise StoryError(explain_rejection(params.place, params.figure))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        place=PLACES[params.place],
        figure_cfg=FIGURES[params.figure],
        method=METHODS[params.method],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show plausible/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} plausible (place, figure) combos:\n")
        for place_id, figure_id in combos:
            print(f"  {place_id:8} {figure_id}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.figure} at {p.place} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
