#!/usr/bin/env python3
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    party: str
    affords: set[str] = field(default_factory=set)
    opening: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    need: str
    hiding_place: str
    action: str
    clue_object: str
    clue_mark: str
    kind_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectProfile:
    id: str
    name: str
    gender: str
    trait: str
    role: str
    can_do: set[str] = field(default_factory=set)
    line: str = ""
    innocent_busy: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    motive: str
    culprit: str
    detective_name: str
    detective_gender: str
    caregiver: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the warm kitchen",
        party="a family brunch",
        affords={"welcome_drink", "test_punch"},
        opening="Sunlight lay across the floor tiles, and the long table waited for plates and cups.",
        tags={"kitchen", "party"},
    ),
    "garden": Setting(
        id="garden",
        place="the back garden",
        party="a little garden party",
        affords={"welcome_drink", "test_punch", "cheer_up"},
        opening="Paper flowers bobbed on the fence, and the grass smelled sweet after watering.",
        tags={"garden", "party"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        party="a rainy-day tea party",
        affords={"cheer_up"},
        opening="A blanket fort leaned against the sofa, and tiny cups waited on a toy table.",
        tags={"playroom", "party"},
    ),
}

MOTIVES = {
    "welcome_drink": Motive(
        id="welcome_drink",
        need="make a sparkling welcome drink before the guest of honor arrived",
        hiding_place="under the side bench beside three clean cups",
        action="slipped one fizz tablet into water to start a sparkling welcome drink",
        clue_object="a lemon-yellow napkin",
        clue_mark="a lemon smell and a damp yellow napkin",
        kind_reason="wanted the first sip to feel extra special for Auntie May",
        tags={"fizz", "drink", "welcome"},
    ),
    "test_punch": Motive(
        id="test_punch",
        need="quietly test the punch before everyone tasted it",
        hiding_place="under the table beside the big glass bowl",
        action="dropped a fizz tablet into a spoonful of punch to see if it was too sour",
        clue_object="a tiny measuring spoon",
        clue_mark="a shiny measuring spoon dotted with bubbles",
        kind_reason="wanted to make sure the punch was good before the guests drank it",
        tags={"fizz", "punch", "taste"},
    ),
    "cheer_up": Motive(
        id="cheer_up",
        need="cheer up shy little Milo before the party games began",
        hiding_place="inside the blanket fort beside a blue paper cup",
        action="made a bubbling cup with a fizz tablet to coax a smile out of Milo",
        clue_object="a blue paper cup",
        clue_mark="a blue cup ring, still wet with bubbles",
        kind_reason="wanted nervous Milo to giggle before the noisy party started",
        tags={"fizz", "comfort", "cup"},
    ),
}

SUSPECTS = {
    "nora": SuspectProfile(
        id="nora",
        name="Nora",
        gender="girl",
        trait="tidy",
        role="decorator",
        can_do={"welcome_drink"},
        line="I was making things look nice for Auntie May.",
        innocent_busy="looping paper flowers onto string",
        tags={"decorations"},
    ),
    "ben": SuspectProfile(
        id="ben",
        name="Ben",
        gender="boy",
        trait="curious",
        role="taster",
        can_do={"test_punch"},
        line="I only wanted the punch to be just right.",
        innocent_busy="counting cups beside the bowl",
        tags={"taste"},
    ),
    "tia": SuspectProfile(
        id="tia",
        name="Tia",
        gender="girl",
        trait="kind",
        role="helper",
        can_do={"cheer_up"},
        line="Milo likes bubbles when he feels shy.",
        innocent_busy="reading softly in the blanket fort",
        tags={"comfort"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_missing_worry(world: World) -> list[str]:
    detective = world.entities.get("detective")
    tin = world.entities.get("tin")
    if detective is None or tin is None:
        return []
    if tin.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["worry"] += 1
    detective.memes["curiosity"] += 1
    world.get("case").meters["mystery"] += 1
    return []


def _r_fizz(world: World) -> list[str]:
    tin = world.entities.get("tin")
    hide = world.entities.get("hide")
    if tin is None or hide is None:
        return []
    if tin.meters["in_water"] < THRESHOLD:
        return []
    sig = ("fizz", hide.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tin.meters["fizzing"] += 1
    hide.meters["bubbly"] += 1
    world.facts["heard_fizz"] = True
    return []


def _r_relief(world: World) -> list[str]:
    case = world.entities.get("case")
    if case is None or case.meters["solved"] < THRESHOLD:
        return []
    sig = ("relief", "all")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="meme", apply=_r_missing_worry),
    Rule(name="fizz", tag="physical", apply=_r_fizz),
    Rule(name="relief", tag="meme", apply=_r_relief),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(setting_id: str, motive_id: str, culprit_id: str) -> bool:
    if setting_id not in SETTINGS or motive_id not in MOTIVES or culprit_id not in SUSPECTS:
        return False
    return motive_id in SETTINGS[setting_id].affords and motive_id in SUSPECTS[culprit_id].can_do


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for motive_id in MOTIVES:
            for culprit_id in SUSPECTS:
                if valid_combo(setting_id, motive_id, culprit_id):
                    out.append((setting_id, motive_id, culprit_id))
    return out


def explain_rejection(setting_id: str, motive_id: str, culprit_id: str) -> str:
    if setting_id in SETTINGS and motive_id in MOTIVES and motive_id not in SETTINGS[setting_id].affords:
        setting = SETTINGS[setting_id]
        motive = MOTIVES[motive_id]
        return (
            f"(No story: {setting.place} does not fit this plan. A child cannot {motive.need} there "
            f"without the needed cups, bowl, or quiet corner.)"
        )
    if culprit_id in SUSPECTS and motive_id in MOTIVES and motive_id not in SUSPECTS[culprit_id].can_do:
        suspect = SUSPECTS[culprit_id]
        motive = MOTIVES[motive_id]
        return (
            f"(No story: {suspect.name} is not the sensible culprit for this case. "
            f"{suspect.name} would not plausibly {motive.need}.)"
        )
    return "(No story: the chosen mystery pieces do not make a reasonable case.)"


def setup_party(world: World, detective: Entity, caregiver: Entity, setting: Setting) -> None:
    detective.memes["joy"] += 1
    world.say(
        f"On the morning of {setting.party}, {detective.id} padded into {setting.place} and stopped at once."
    )
    world.say(setting.opening)
    world.say(
        f"{caregiver.label_word.capitalize()} was setting out a tin of lemon fizz tablets for the drinks, "
        f"and {detective.id} loved the tiny hiss they made in water."
    )
    world.say(
        f'"Do not use these yet," {caregiver.label_word} said. "They are for later, when everyone is ready."'
    )


def secret_take(world: World, culprit: Entity, motive: Motive) -> None:
    tin = world.get("tin")
    hide = world.get("hide")
    culprit.memes["secret"] += 1
    culprit.memes["kindness"] += 1
    tin.meters["missing"] += 1
    tin.meters["in_water"] += 1
    hide.attrs["clue_mark"] = motive.clue_mark
    hide.attrs["used_for"] = motive.need
    world.facts["clue_mark"] = motive.clue_mark
    propagate(world, narrate=False)


def discover_missing(world: World, detective: Entity, caregiver: Entity, motive: Motive) -> None:
    tin = world.get("tin")
    world.para()
    world.say(
        f"A little later, the tin was gone. Only a round dry spot on the table showed where it had been."
    )
    propagate(world, narrate=False)
    if world.facts.get("heard_fizz"):
        world.say(
            f"{detective.id} held very still. From somewhere nearby came the softest sound in the world: "
            f'"fizz... fizz..." It was only a whisper, but it made the room feel like a mystery book.'
        )
        world.say(
            "That tiny hiss was a bit of foreshadowing, though nobody knew it yet."
        )
    world.say(
        f'{caregiver.label_word.capitalize()} looked around in surprise. "Who took the fizz tablets?"'
    )
    world.say(
        f"{detective.id} drew a careful breath. This would be the first real case {detective.pronoun()} had ever solved."
    )
    world.facts["mystery_open"] = tin.meters["missing"] >= THRESHOLD
    world.facts["need"] = motive.need


def suspect_sentence(profile: SuspectProfile, culprit_id: str) -> str:
    if profile.id == culprit_id:
        return (
            f"{profile.name} stood very straight and tried to look busy, but there was something tucked "
            f"close by: {profile.line}"
        )
    return (
        f"{profile.name} was {profile.innocent_busy}. When asked, {profile.pronoun('subject')} only said, "
        f'"{profile.line}"'
    )


def interview_suspects(world: World, detective: Entity, culprit_id: str) -> None:
    world.para()
    world.say(
        f"{detective.id} went from one helper to the next, watching with detective eyes instead of party eyes."
    )
    for sid in ["nora", "ben", "tia"]:
        profile = SUSPECTS[sid]
        suspect = world.get(sid)
        if sid == culprit_id:
            if sid == "nora":
                extra = "A corner of a yellow napkin peeked from her pocket."
            elif sid == "ben":
                extra = "A tiny measuring spoon flashed in his sleeve."
            else:
                extra = "There was a pale blue ring on her wrist, as if a paper cup had rested there."
            world.say(
                f"{suspect.id} looked up. {profile.line} {extra}"
            )
        else:
            world.say(
                f"{suspect.id} was {profile.innocent_busy}. {profile.line}"
            )
    detective.memes["focus"] += 1


def inspect_clue(world: World, detective: Entity, motive: Motive) -> None:
    hide = world.get("hide")
    detective.meters["clue_found"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"Then {detective.id} followed the hiss to {motive.hiding_place}. There, waiting like a clue in plain sight, "
        f"was {hide.attrs['clue_mark']}."
    )


def flashback_reveal(world: World, detective: Entity, culprit: Entity, motive: Motive) -> None:
    case = world.get("case")
    detective.memes["insight"] += 1
    case.meters["solved"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"Then a flashback flickered through {detective.id}'s mind. {detective.pronoun().capitalize()} remembered "
        f"hearing {culprit.id} say, \"{culprit.attrs['memory_line']}\" before the tin disappeared."
    )
    world.say(
        f'Now the little pieces fit together. "{culprit.id} took the tablets," {detective.id} said. '
        f'"Not to be naughty. {culprit.pronoun().capitalize()} wanted to {motive.need}."'
    )
    world.facts["solved"] = True


def surprise_resolution(world: World, detective: Entity, caregiver: Entity, culprit: Entity, motive: Motive) -> None:
    world.say(
        f"Everyone turned to {culprit.id}. To everyone's surprise, {culprit.pronoun()} did not look mean at all. "
        f"{culprit.pronoun().capitalize()} only looked caught and hopeful."
    )
    world.say(
        f'"I only {motive.action}," {culprit.id} admitted. "{motive.kind_reason}."'
    )
    world.say(
        f"{caregiver.label_word.capitalize()} knelt beside {culprit.id} and smiled a little. "
        f'"That was a kind idea," {caregiver.pronoun()} said, "but next time, ask before you borrow the fizz tablets."'
    )
    world.say(
        f"{culprit.id} nodded, and the tight feeling in the room melted away."
    )
    world.para()
    world.say(
        f"Soon the cups were filled properly, the secret clue was no longer a secret, and {detective.id} got the happy ending every small detective hopes for."
    )
    world.say(
        f"The drinks lifted bright bubbles to the top, Auntie May laughed, and the whole party sparkled with a gentle fizz."
    )


def tell(
    setting: Setting,
    motive: Motive,
    culprit_profile: SuspectProfile,
    detective_name: str,
    detective_gender: str,
    caregiver_type: str,
) -> World:
    world = World(setting)
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            traits=["observant"],
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            role="caregiver",
            label="the grown-up",
        )
    )
    world.add(
        Entity(
            id="case",
            kind="thing",
            type="case",
            label="the case",
        )
    )
    tin = world.add(
        Entity(
            id="tin",
            kind="thing",
            type="tin",
            label="the tin of fizz tablets",
            phrase="a bright tin of lemon fizz tablets",
            tags={"fizz"},
        )
    )
    hide = world.add(
        Entity(
            id="hide",
            kind="thing",
            type="spot",
            label="the hiding spot",
            phrase=motive.hiding_place,
        )
    )
    world.facts["item_label"] = tin.label
    world.facts["setting"] = setting
    world.facts["motive"] = motive
    world.facts["culprit_profile"] = culprit_profile

    for sid in ["nora", "ben", "tia"]:
        profile = SUSPECTS[sid]
        suspect = world.add(
            Entity(
                id=profile.name,
                kind="character",
                type=profile.gender,
                role="suspect",
                traits=[profile.trait],
                attrs={
                    "profile_id": profile.id,
                    "memory_line": profile.line,
                    "busy": profile.innocent_busy,
                },
            )
        )
        if profile.id == culprit_profile.id:
            suspect.role = "culprit"

    culprit = world.get(culprit_profile.name)

    setup_party(world, detective, caregiver, setting)
    secret_take(world, culprit, motive)
    discover_missing(world, detective, caregiver, motive)
    interview_suspects(world, detective, culprit_profile.id)
    inspect_clue(world, detective, motive)
    flashback_reveal(world, detective, culprit, motive)
    surprise_resolution(world, detective, caregiver, culprit, motive)

    world.facts.update(
        detective=detective,
        caregiver=caregiver,
        culprit=culprit,
        suspects=[world.get(SUSPECTS[s].name) for s in ["nora", "ben", "tia"]],
        clue=motive.clue_mark,
        heard_fizz=bool(world.facts.get("heard_fizz")),
        solved=world.get("case").meters["solved"] >= THRESHOLD,
        secret_kindness=culprit.memes["kindness"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "fizz": [
        (
            "What does fizz mean?",
            "Fizz is the tiny hissing sound and little bubbles you get when a fizzy drink or tablet meets water. The bubbles race upward and make a soft, lively noise.",
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure something out. It might be a sound, a smell, or an object left in the wrong place.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is an early hint that something important will matter later. It helps the ending feel surprising but fair.",
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is when a story remembers something from earlier. That memory can help a character understand what is happening now.",
        )
    ],
    "surprise": [
        (
            "Why can a mystery ending feel surprising?",
            "A mystery can feel surprising when the answer is not what everyone first guessed. The best surprise still matches the clues you saw before.",
        )
    ],
    "party": [
        (
            "Why should you ask before borrowing something for a party?",
            "You should ask first because other people may already have a plan for it. Asking helps everyone share and keeps the party running smoothly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fizz", "clue", "foreshadowing", "flashback", "surprise", "party"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    setting = f["setting"]
    motive = f["motive"]
    culprit = f["culprit"]
    return [
        'Write a gentle whodunit for a 3-to-5-year-old that includes the word "fizz" and ends with a kind surprise.',
        f"Tell a child-friendly mystery set in {setting.place} where {detective.id} hears a faint fizz, follows clues, and learns that {culprit.id} was trying to {motive.need}.",
        "Write a story that uses foreshadowing, a flashback, and a surprise reveal, but keeps the ending warm instead of scary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    caregiver = f["caregiver"]
    culprit = f["culprit"]
    motive = f["motive"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a small detective at {setting.party}, and the helpers around {detective.pronoun('object')}. The mystery began when the tin of fizz tablets disappeared.",
        ),
        (
            "What was the mystery?",
            f"The mystery was who had taken the fizz tablets from the table. The missing tin mattered because the bubbles were meant for the party drinks later.",
        ),
        (
            "What was the foreshadowing clue?",
            f"The foreshadowing clue was the tiny sound of \"fizz... fizz...\" that {detective.id} heard before the answer was known. That early hiss pointed toward water, bubbles, and the hiding place.",
        ),
        (
            "How did the flashback help solve the case?",
            f"{detective.id} remembered something {culprit.id} had said earlier, and that memory made the clue make sense. The flashback connected the culprit's kind plan to the bubbling hiding spot.",
        ),
        (
            f"Why did {culprit.id} take the fizz tablets?",
            f"{culprit.id} took them to {motive.need}. It was not a mean choice; it was a secret kind plan that should have been asked about first.",
        ),
        (
            "What was the surprise ending?",
            f"The surprise was that the culprit was not trying to ruin the party at all. {culprit.id} only wanted to help, so the ending turned from suspicion into relief.",
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                f"What did the grown-up say after the mystery was solved?",
                f"{caregiver.label_word.capitalize()} said the idea was kind but that borrowing the fizz tablets should have been asked about first. That answer solved the problem and also taught a gentle rule about sharing.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fizz", "clue", "foreshadowing", "flashback", "surprise", "party"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        motive="welcome_drink",
        culprit="nora",
        detective_name="Lily",
        detective_gender="girl",
        caregiver="aunt",
    ),
    StoryParams(
        setting="kitchen",
        motive="test_punch",
        culprit="ben",
        detective_name="Max",
        detective_gender="boy",
        caregiver="mother",
    ),
    StoryParams(
        setting="playroom",
        motive="cheer_up",
        culprit="tia",
        detective_name="Ava",
        detective_gender="girl",
        caregiver="father",
    ),
    StoryParams(
        setting="garden",
        motive="cheer_up",
        culprit="tia",
        detective_name="Noah",
        detective_gender="boy",
        caregiver="aunt",
    ),
]


ASP_RULES = r"""
valid(S, M, C) :- setting(S), motive(M), suspect(C), affords(S, M), can_do(C, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for motive_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, motive_id))
    for mid in MOTIVES:
        lines.append(asp.fact("motive", mid))
    for cid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", cid))
        for motive_id in sorted(suspect.can_do):
            lines.append(asp.fact("can_do", cid, motive_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle whodunit storyworld: the case of the missing fizz tablets."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name not in {p.name for p in SUSPECTS.values()}]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.motive and args.culprit and not valid_combo(args.setting, args.motive, args.culprit):
        raise StoryError(explain_rejection(args.setting, args.motive, args.culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.motive is None or combo[1] == args.motive)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        setting_id = args.setting or next(iter(SETTINGS))
        motive_id = args.motive or next(iter(MOTIVES))
        culprit_id = args.culprit or next(iter(SUSPECTS))
        raise StoryError(explain_rejection(setting_id, motive_id, culprit_id))

    setting_id, motive_id, culprit_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    caregiver = args.caregiver or rng.choice(["mother", "father", "aunt"])
    return StoryParams(
        setting=setting_id,
        motive=motive_id,
        culprit=culprit_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        caregiver=caregiver,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Invalid motive: {params.motive})")
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if not valid_combo(params.setting, params.motive, params.culprit):
        raise StoryError(explain_rejection(params.setting, params.motive, params.culprit))

    world = tell(
        setting=SETTINGS[params.setting],
        motive=MOTIVES[params.motive],
        culprit_profile=SUSPECTS[params.culprit],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        caregiver_type=params.caregiver,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    for seed in range(6):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print("SMOKE resolve_params failed:", err)

    try:
        for params in smoke_cases:
            sample = generate(params)
            _ = sample.to_json()
            _ = format_qa(sample)
            if sample.world is not None:
                _ = dump_trace(sample.world)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    except Exception as err:
        rc = 1
        print("SMOKE generation failed:", err)
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, motive, culprit) combos:\n")
        for setting_id, motive_id, culprit_id in combos:
            print(f"  {setting_id:8} {motive_id:14} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.detective_name}: {p.setting}, {p.motive}, culprit {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
