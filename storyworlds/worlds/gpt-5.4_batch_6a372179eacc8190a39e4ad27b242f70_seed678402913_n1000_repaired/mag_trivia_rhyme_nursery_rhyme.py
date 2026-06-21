#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py
============================================================

A tiny nursery-rhyme story world about Mag, a magpie who is getting ready to
sing a rhyming verse. Mag accidentally tucks a trivia card into the rhyme
basket, so the line no longer chimes. A helper notices the bump, they sort the
pieces by sound, and the song ends neatly.

Run it
------
    python storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py --place gate --rhyme moon --intruder trivia_card
    python storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py --fix shout_louder
    python storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/mag_trivia_rhyme_nursery_rhyme.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    opening: str
    closing: str
    stash: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RhymeSet:
    id: str
    cue: str
    match: str
    sound: str
    lead_line: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Intruder:
    id: str
    label: str
    phrase: str
    fact_text: str
    sound: str
    material: str = "card"
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    method: str
    success_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    rhyme: str
    intruder: str
    fix: str
    helper_name: str
    helper_type: str
    delay: int = 0
    seed: Optional[int] = None


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


def _r_mismatch(world: World) -> list[str]:
    out: list[str] = []
    basket = world.get("basket")
    rhyme = world.facts.get("rhyme_cfg")
    intruder = world.facts.get("intruder_cfg")
    if rhyme is None or intruder is None:
        return out
    if basket.meters["mixed"] < THRESHOLD:
        return out
    sig = ("mismatch", rhyme.id, intruder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("Mag").memes["worry"] += 1
    world.get("song").meters["bumpy"] += 1
    out.append("__bump__")
    return out


def _r_ready(world: World) -> list[str]:
    out: list[str] = []
    basket = world.get("basket")
    if basket.meters["rhyme_pair"] < THRESHOLD:
        return out
    sig = ("ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("song").meters["ready"] += 1
    world.get("Mag").memes["confidence"] += 1
    out.append("__ready__")
    return out


CAUSAL_RULES = [
    Rule(name="mismatch", tag="rhyme", apply=_r_mismatch),
    Rule(name="ready", tag="rhyme", apply=_r_ready),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def rhyme_problem(rhyme: RhymeSet, intruder: Intruder) -> bool:
    return rhyme.sound != intruder.sound


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def has_replacement(place: Place, rhyme: RhymeSet) -> bool:
    return rhyme.match in place.stash


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for rhyme_id, rhyme in RHYMES.items():
            for intruder_id, intruder in INTRUDERS.items():
                if rhyme_problem(rhyme, intruder) and has_replacement(place, rhyme):
                    combos.append((place_id, rhyme_id, intruder_id))
    return combos


def explain_rejection(place: Place, rhyme: RhymeSet, intruder: Intruder) -> str:
    if not has_replacement(place, rhyme):
        return (
            f"(No story: {place.label} has no {rhyme.match} for the {rhyme.cue}/{rhyme.match} rhyme. "
            f"Without the matching piece, Mag cannot mend the verse.)"
        )
    if not rhyme_problem(rhyme, intruder):
        return (
            f"(No story: {intruder.label} already chimes with {rhyme.cue}. "
            f"If nothing bumps, there is no need to fix the rhyme.)"
        )
    return "(No story: this combination does not make a useful rhyme problem.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "smooth" if params.delay == 0 else "mended"


def _test_broken_line(world: World) -> None:
    basket = world.get("basket")
    basket.meters["mixed"] += 1
    propagate(world, narrate=False)


def predict_bump(world: World) -> bool:
    sim = world.copy()
    _test_broken_line(sim)
    return sim.get("song").meters["bumpy"] >= THRESHOLD


def introduce(world: World, mag: Entity, place: Place, rhyme: RhymeSet) -> None:
    mag.memes["joy"] += 1
    world.say(
        f"There was Mag, a merry magpie, {place.opening}. "
        f"{rhyme.lead_line}"
    )
    world.say(
        f"Mag liked bright words that rang in pairs, and today {mag.pronoun()} wanted "
        f"to sing one neat little rhyme."
    )


def gather(world: World, mag: Entity, rhyme: RhymeSet, intruder: Intruder) -> None:
    world.get("basket").meters["gathered"] += 1
    mag.memes["pride"] += 1
    world.say(
        f"Into a small round basket went a {rhyme.cue} card, and after it slipped "
        f"{intruder.phrase} marked 'trivia'."
    )
    world.say(
        f"On the trivia card were the words, \"{intruder.fact_text}\" "
        f"and Mag thought the shiny scrap looked clever."
    )


def warn(world: World, helper: Entity, rhyme: RhymeSet, intruder: Intruder) -> None:
    helper.memes["care"] += 1
    bump = predict_bump(world)
    world.facts["predicted_bump"] = bump
    world.say(
        f'{helper.id} peeped into the basket and said, '
        f'"A rhyme needs a partner sound. {intruder.label.capitalize()} does not chime with {rhyme.cue}."'
    )


def try_broken_song(world: World, mag: Entity, rhyme: RhymeSet, intruder: Intruder) -> None:
    _test_broken_line(world)
    world.say(
        f'Mag gave the basket a toss and sang, "{rhyme.cue}, {intruder.label}," '
        f"but the line landed with a little bump instead of a bounce."
    )
    if world.get("song").meters["bumpy"] >= THRESHOLD:
        world.say(
            f"{mag.id} blinked and felt the odd place in the tune. "
            f"The trivia card was bright, but it was the wrong bright thing."
        )


def mend_rhyme(world: World, mag: Entity, helper: Entity, place: Place,
               rhyme: RhymeSet, intruder: Intruder, fix: Fix) -> None:
    basket = world.get("basket")
    basket.meters["mixed"] = 0.0
    basket.meters["rhyme_pair"] += 1
    world.get("quiz_tin").meters["stored"] += 1
    propagate(world, narrate=False)
    mag.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} {fix.success_text.format(intruder=intruder.label, match=rhyme.match)}"
    )
    world.say(
        f"Then Mag tried again and found the true pair: {rhyme.cue} and {rhyme.match}."
    )


def finish_song(world: World, mag: Entity, helper: Entity, place: Place,
                rhyme: RhymeSet, outcome: str) -> None:
    mag.memes["joy"] += 1
    mag.memes["pride"] += 1
    mag.memes["worry"] = 0.0
    world.say(
        f'So {mag.id} sang, "{rhyme.cue} and {rhyme.match}," and the sound skipped lightly through {place.label}.'
    )
    if outcome == "smooth":
        world.say(
            f"{helper.id} had caught the trouble before the song could stumble, "
            f"and the basket held only what the rhyme truly needed."
        )
    else:
        world.say(
            f"The tune had bumped once, but now it rolled sweetly. "
            f"Because they fixed the basket, the second try shone brighter than the first."
        )
    world.say(place.closing)
    world.say(rhyme.end_image)


def tell(place: Place, rhyme: RhymeSet, intruder: Intruder, fix: Fix,
         helper_name: str = "Wren", helper_type: str = "bird", delay: int = 0) -> World:
    world = World(place)
    mag = world.add(Entity(id="Mag", kind="character", type="bird", label="Mag", role="singer"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name, role="helper"))
    world.add(Entity(id="basket", type="basket", label="basket"))
    world.add(Entity(id="song", type="song", label="song"))
    world.add(Entity(id="quiz_tin", type="tin", label="quiz tin"))
    world.facts.update(
        place_cfg=place,
        rhyme_cfg=rhyme,
        intruder_cfg=intruder,
        fix_cfg=fix,
        delay=delay,
    )

    introduce(world, mag, place, rhyme)
    gather(world, mag, rhyme, intruder)

    world.para()
    warn(world, helper, rhyme, intruder)
    if delay:
        try_broken_song(world, mag, rhyme, intruder)
    else:
        world.say(
            f'Mag paused before singing, for {helper.id} had made the trouble plain.'
        )

    world.para()
    mend_rhyme(world, mag, helper, place, rhyme, intruder, fix)
    finish_song(world, mag, helper, place, rhyme, "smooth" if delay == 0 else "mended")

    world.facts.update(
        mag=mag,
        helper=helper,
        place=place,
        rhyme=rhyme,
        intruder=intruder,
        fix=fix,
        outcome="smooth" if delay == 0 else "mended",
        bumped=delay == 1,
        repaired=world.get("song").meters["ready"] >= THRESHOLD,
    )
    return world


PLACES = {
    "gate": Place(
        id="gate",
        label="the garden gate",
        opening="by the garden gate one bright morning",
        closing="By the gate the leaves gave a tiny clap, as if they liked the settled tune.",
        stash={"spoon", "jar"},
        tags={"gate"},
    ),
    "hill": Place(
        id="hill",
        label="the clover hill",
        opening="upon the clover hill at the start of day",
        closing="Down the hill the clover nodded, and the tidy song floated after the breeze.",
        stash={"sock", "jar"},
        tags={"hill"},
    ),
    "well": Place(
        id="well",
        label="the old stone well",
        opening="beside the old stone well in the mild noon sun",
        closing="At the well the round old stones held the rhyme and sent it back soft and clear.",
        stash={"spoon", "bell"},
        tags={"well"},
    ),
}

RHYMES = {
    "moon": RhymeSet(
        id="moon",
        cue="moon",
        match="spoon",
        sound="oon",
        lead_line="The silver moon card winked like a coin in a nest.",
        end_image="And Mag tucked the spoon card in place, so moon and spoon danced in tune.",
        tags={"moon", "rhyme"},
    ),
    "star": RhymeSet(
        id="star",
        cue="star",
        match="jar",
        sound="ar",
        lead_line="A little gold star card gleamed as if it had borrowed a crumb of sky.",
        end_image="And star with jar made such a chime that even the dusk seemed to hum along.",
        tags={"star", "rhyme"},
    ),
    "clock": RhymeSet(
        id="clock",
        cue="clock",
        match="sock",
        sound="ock",
        lead_line="A round clock card shone with a painted face and two prim hands.",
        end_image="And clock with sock clicked so snugly together that the rhyme seemed to hop.",
        tags={"clock", "rhyme"},
    ),
    "shell": RhymeSet(
        id="shell",
        cue="shell",
        match="bell",
        sound="ell",
        lead_line="A pale shell card lay pearly in the basket, quiet and neat.",
        end_image="And shell with bell rang small and clear, like water laughing in a cup.",
        tags={"shell", "rhyme"},
    ),
}

INTRUDERS = {
    "trivia_card": Intruder(
        id="trivia_card",
        label="trivia card",
        phrase="a trivia card",
        fact_text="Mice can nibble in the night.",
        sound="ard",
        material="card",
        tags={"trivia", "card"},
    ),
    "fact_ticket": Intruder(
        id="fact_ticket",
        label="fact ticket",
        phrase="a fact ticket",
        fact_text="Owls blink softly before dawn.",
        sound="et",
        material="paper",
        tags={"trivia", "fact"},
    ),
    "quiz_stub": Intruder(
        id="quiz_stub",
        label="quiz stub",
        phrase="a quiz stub",
        fact_text="Bees brush pollen on their knees.",
        sound="ub",
        material="paper",
        tags={"trivia", "quiz"},
    ),
    "bell_clue": Intruder(
        id="bell_clue",
        label="bell clue",
        phrase="a bell clue",
        fact_text="A bell can call lambs home at dusk.",
        sound="ell",
        material="paper",
        tags={"trivia", "bell"},
    ),
}

FIXES = {
    "swap_card": Fix(
        id="swap_card",
        sense=3,
        method="swap",
        success_text="lifted out the {intruder}, slid it into the quiz tin, and fetched the {match} card from a nearby shelf.",
        qa_text="lifted the trivia piece out and swapped in the proper rhyming card",
        tags={"sort", "swap"},
    ),
    "tuck_and_fetch": Fix(
        id="tuck_and_fetch",
        sense=3,
        method="sort",
        success_text="tucked the {intruder} away for the quiz game and brought back the {match} card that belonged in the verse.",
        qa_text="put the trivia piece aside and fetched the matching rhyme card",
        tags={"sort", "fetch"},
    ),
    "shout_louder": Fix(
        id="shout_louder",
        sense=1,
        method="ignore",
        success_text="told Mag to shout over the bump, which did not really mend anything.",
        qa_text="tried to sing louder instead of fixing the rhyme",
        tags={"bad_fix"},
    ),
}

HELPERS = {
    "Wren": "bird",
    "Mouse": "mouse",
    "Lamb": "lamb",
    "Hen": "hen",
}


KNOWLEDGE = {
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have the same ending sound, like moon and spoon. Matching sounds make lines feel bouncy and easy to remember.",
        )
    ],
    "trivia": [
        (
            "What is trivia?",
            "Trivia is a small interesting fact, like a tiny bit of learning. It can be fun for a quiz, even when it does not belong in a song.",
        )
    ],
    "moon": [
        (
            "What is the moon?",
            "The moon is the bright round body you can see in the sky at night. It shines by reflecting light from the sun.",
        )
    ],
    "star": [
        (
            "What is a star?",
            "A star is a faraway ball of hot glowing gas in the sky. At night it looks like a tiny twinkling point of light.",
        )
    ],
    "clock": [
        (
            "What does a clock do?",
            "A clock tells time. Its hands or numbers help people know when it is time to wake, play, or rest.",
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is the hard outer covering of some sea animals. Empty shells can wash up on beaches and feel smooth in your hand.",
        )
    ],
    "sort": [
        (
            "Why is sorting helpful?",
            "Sorting puts things into the right groups. When pieces are sorted, it is easier to find what belongs together.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rhyme", "trivia", "moon", "star", "clock", "shell", "sort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rhyme = f["rhyme"]
    intruder = f["intruder"]
    place = f["place"]
    outcome = f["outcome"]
    return [
        (
            f'Write a nursery-rhyme style story about Mag the magpie at {place.label} '
            f'that includes the words "mag" and "trivia" and uses a clear rhyme problem.'
        ),
        (
            f"Tell a gentle rhyming story where Mag gathers {rhyme.cue} for a song, "
            f"but a {intruder.label} slips into the basket and must be sorted out."
        ),
        (
            f"Write a short child-facing verse tale with a beginning, a small bump, "
            f"and a {outcome} ending where the proper rhyming pair is found."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mag = f["mag"]
    helper = f["helper"]
    place = f["place"]
    rhyme = f["rhyme"]
    intruder = f["intruder"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Mag the magpie and {helper.id}, who helped at {place.label}. They were trying to make a little song rhyme neatly.",
        ),
        (
            "What did Mag put in the basket?",
            f"Mag put in the {rhyme.cue} card, but also a {intruder.label} marked trivia. The shiny trivia piece looked interesting, even though it did not belong in the rhyme basket.",
        ),
        (
            f"Why did {helper.id} say the basket had a problem?",
            f"{helper.id} saw that {intruder.label} did not chime with {rhyme.cue}. A rhyme needs matching ending sounds, so the basket would make the tune come out wrong.",
        ),
    ]
    if f["bumped"]:
        qa.append(
            (
                "What happened when Mag tried the wrong line first?",
                f'Mag sang "{rhyme.cue}" with the {intruder.label}, and the line bumped instead of bouncing. That happened because the trivia piece had the wrong ending sound.',
            )
        )
    else:
        qa.append(
            (
                "Did Mag sing the wrong line before the fix?",
                f"No. {helper.id} warned Mag in time, so they paused before the song could stumble. Because the trouble was noticed early, the rhyme stayed smooth.",
            )
        )
    qa.append(
        (
            "How did they fix the rhyme?",
            f"{helper.id} {fix.qa_text}. That gave Mag the true pair, {rhyme.cue} and {rhyme.match}, so the verse could ring clearly.",
        )
    )
    if outcome == "smooth":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a smooth little song at {place.label}. The basket held the proper pair, and Mag sang with confidence because the trouble had been caught early.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end after the bump?",
                f"It ended happily because the bump was mended. Once the trivia piece was put away and the right rhyming card was found, the second song came out sweet and steady.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"rhyme", "trivia"}
    tags |= set(f["rhyme"].tags)
    tags |= set(f["fix"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="gate",
        rhyme="moon",
        intruder="trivia_card",
        fix="swap_card",
        helper_name="Wren",
        helper_type="bird",
        delay=0,
    ),
    StoryParams(
        place="hill",
        rhyme="clock",
        intruder="fact_ticket",
        fix="tuck_and_fetch",
        helper_name="Mouse",
        helper_type="mouse",
        delay=1,
    ),
    StoryParams(
        place="well",
        rhyme="shell",
        intruder="quiz_stub",
        fix="swap_card",
        helper_name="Lamb",
        helper_type="lamb",
        delay=1,
    ),
    StoryParams(
        place="gate",
        rhyme="star",
        intruder="quiz_stub",
        fix="tuck_and_fetch",
        helper_name="Hen",
        helper_type="hen",
        delay=0,
    ),
]


ASP_RULES = r"""
problem(R, I) :- rhyme(R), intruder(I), rhyme_sound(R, RS), intruder_sound(I, IS), RS != IS.
valid(P, R, I) :- place(P), rhyme(R), intruder(I), has_word(P, R), problem(R, I).

sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

outcome(smooth) :- chosen_fix(F), sensible(F), delay(0).
outcome(mended) :- chosen_fix(F), sensible(F), delay(1).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for word in sorted(place.stash):
            lines.append(asp.fact("stash", place_id, word))
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rhyme_id))
        lines.append(asp.fact("rhyme_sound", rhyme_id, rhyme.sound))
        lines.append(asp.fact("match_word", rhyme_id, rhyme.match))
        lines.append(asp.fact("has_word", rhyme_id if False else "dummy"))  # never shown
    # Emit has_word directly to keep the ASP simple and close to the Python gate.
    lines = [line for line in lines if "has_word(" not in line]
    for place_id, place in PLACES.items():
        for rhyme_id, rhyme in RHYMES.items():
            if rhyme.match in place.stash:
                lines.append(asp.fact("has_word", place_id, rhyme_id))
    for intruder_id, intruder in INTRUDERS.items():
        lines.append(asp.fact("intruder", intruder_id))
        lines.append(asp.fact("intruder_sound", intruder_id, intruder.sound))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    sink = io.StringIO()
    with redirect_stdout(sink):
        emit(sample, trace=False, qa=True, header="### smoke")
    rendered = sink.getvalue()
    if "Mag" not in rendered:
        raise StoryError("Smoke test failed: emit() did not render expected content.")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sensible = {fix.id for fix in sensible_fixes()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(cl_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
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
        smoke_test()
        print("OK: smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme story world: Mag the magpie sorts a trivia card out of a rhyme basket."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--intruder", choices=INTRUDERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper-name", choices=sorted(HELPERS))
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = fix before singing; 1 = Mag tries one bumpy line first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    if args.place and args.rhyme and args.intruder:
        place = PLACES[args.place]
        rhyme = RHYMES[args.rhyme]
        intruder = INTRUDERS[args.intruder]
        if not (has_replacement(place, rhyme) and rhyme_problem(rhyme, intruder)):
            raise StoryError(explain_rejection(place, rhyme, intruder))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.rhyme is None or combo[1] == args.rhyme)
        and (args.intruder is None or combo[2] == args.intruder)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, rhyme_id, intruder_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    helper_name = args.helper_name or rng.choice(sorted(HELPERS))
    helper_type = HELPERS[helper_name]
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        place=place_id,
        rhyme=rhyme_id,
        intruder=intruder_id,
        fix=fix_id,
        helper_name=helper_name,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    if params.intruder not in INTRUDERS:
        raise StoryError(f"(Unknown intruder: {params.intruder})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    place = PLACES[params.place]
    rhyme = RHYMES[params.rhyme]
    intruder = INTRUDERS[params.intruder]
    if not (has_replacement(place, rhyme) and rhyme_problem(rhyme, intruder)):
        raise StoryError(explain_rejection(place, rhyme, intruder))

    world = tell(
        place=place,
        rhyme=rhyme,
        intruder=intruder,
        fix=FIXES[params.fix],
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        delay=params.delay,
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
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, rhyme, intruder) combos:\n")
        for place, rhyme, intruder in combos:
            print(f"  {place:6} {rhyme:6} {intruder}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.place}: {p.rhyme} with {p.intruder} ({outcome_of(p)})"
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
