#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spectacle_pop_curiosity_friendship_moral_value_detective.py
======================================================================================

A standalone storyworld for a tiny detective-story domain built from the seed
words "spectacle" and "pop".

Premise
-------
Two child friends are eager for a little neighborhood spectacle: a lantern,
shadow, or puppet show. Just before it begins, they hear a sharp "pop" and the
show cannot start. One child is tempted to blame the nearest person, but the
friends choose to investigate properly. They follow a clue, discover the true
cause, and fix the problem. The moral turn is simple and child-facing: curiosity
should be careful, friendship means listening, and it is wrong to accuse someone
without checking the facts.

World model
-----------
The model tracks:
- physical meters: blocked, dim, delayed, found, fixed
- emotional memes: curiosity, trust, worry, relief, fairness, pride

The state drives whether the children accuse too quickly, how they investigate,
what clue they find, and how the ending proves the change.

Run it
------
python storyworlds/worlds/gpt-5.4/spectacle_pop_curiosity_friendship_moral_value_detective.py
python storyworlds/worlds/gpt-5.4/spectacle_pop_curiosity_friendship_moral_value_detective.py --show lanterns --cause balloon
python storyworlds/worlds/gpt-5.4/spectacle_pop_curiosity_friendship_moral_value_detective.py --show shadow_wall --cause loose_plug --fix tie_ribbon
python storyworlds/worlds/gpt-5.4/spectacle_pop_curiosity_friendship_moral_value_detective.py --all
python storyworlds/worlds/gpt-5.4/spectacle_pop_curiosity_friendship_moral_value_detective.py --verify
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
class Show:
    id: str
    spectacle: str
    place: str
    image: str
    need: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    sound: str
    culprit_object: str
    breaks_need: str
    clue: str
    hiding_spot: str
    explanation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    repairs_need: str
    action: str
    proof: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    show: str
    cause: str
    fix: str
    sleuth_name: str
    sleuth_gender: str
    friend_name: str
    friend_gender: str
    helper_role: str
    fairness_trait: str
    trust: int
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


def _r_delay(world: World) -> list[str]:
    out: list[str] = []
    stage = world.get("stage")
    if stage.meters["blocked"] < THRESHOLD:
        return out
    sig = ("delay", "stage")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stage.meters["delayed"] += 1
    for eid in ("sleuth", "friend", "helper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__delay__")
    return out


def _r_find_truth(world: World) -> list[str]:
    out: list[str] = []
    stage = world.get("stage")
    culprit = world.get("culprit")
    if culprit.meters["found"] < THRESHOLD:
        return out
    sig = ("truth", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stage.meters["mystery_solved"] += 1
    world.get("sleuth").memes["fairness"] += 1
    world.get("friend").memes["fairness"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES = [
    Rule(name="delay", tag="physical", apply=_r_delay),
    Rule(name="truth", tag="social", apply=_r_find_truth),
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


SHOWS = {
    "lanterns": Show(
        id="lanterns",
        spectacle="a lantern spectacle",
        place="the little park",
        image="paper lanterns hanging from a string over the path",
        need="power",
        opening="glow like a row of tiny moons",
        ending="the lanterns shone over the path again",
        tags={"lantern", "light", "spectacle"},
    ),
    "shadow_wall": Show(
        id="shadow_wall",
        spectacle="a shadow spectacle",
        place="the library yard",
        image="a white sheet stretched between two poles for shadow animals",
        need="light",
        opening="make black rabbit and fox shapes dance on the sheet",
        ending="the bright lamp threw sharp animal shadows across the sheet",
        tags={"shadow", "light", "spectacle"},
    ),
    "puppets": Show(
        id="puppets",
        spectacle="a puppet spectacle",
        place="the school garden",
        image="a small puppet stage with a bright striped curtain",
        need="curtain",
        opening="open with a grand swish",
        ending="the little curtain opened, and the puppet parade could begin",
        tags={"puppet", "stage", "spectacle"},
    ),
}

CAUSES = {
    "balloon": Cause(
        id="balloon",
        label="a balloon",
        sound="a red balloon gave a loud pop",
        culprit_object="balloon ribbon",
        breaks_need="power",
        clue="a scrap of red rubber and a ribbon caught near the battery box",
        hiding_spot="beside the battery box",
        explanation="The balloon popped, and its ribbon snagged the battery cord loose.",
        tags={"balloon", "pop", "cord"},
    ),
    "loose_plug": Cause(
        id="loose_plug",
        label="a loose plug",
        sound="the old plug snapped out with a small pop",
        culprit_object="plug",
        breaks_need="light",
        clue="a plug half out of the socket and a little scrape mark on the wall",
        hiding_spot="behind the lamp table",
        explanation="The plug had slipped almost all the way out, so the lamp could not stay on.",
        tags={"plug", "pop", "lamp"},
    ),
    "button_burst": Cause(
        id="button_burst",
        label="a burst button",
        sound="a curtain button went pop",
        culprit_object="button",
        breaks_need="curtain",
        clue="a shiny blue button on the grass and one loose loop on the curtain tie",
        hiding_spot="under the front step of the stage",
        explanation="A button on the curtain tie burst off, so the curtain sagged and would not open neatly.",
        tags={"button", "pop", "curtain"},
    ),
}

FIXES = {
    "plug_back": Fix(
        id="plug_back",
        label="push the plug back in",
        repairs_need="light",
        action="pressed the plug in until it sat snug and safe",
        proof="the lamp blinked on at once",
        tags={"plug", "repair"},
    ),
    "retie_ribbon": Fix(
        id="retie_ribbon",
        label="untangle the ribbon and tie the cord high",
        repairs_need="power",
        action="freed the ribbon, then tied the cord up where it could not be snagged again",
        proof="the battery hummed softly and the lanterns began to glow",
        tags={"ribbon", "repair"},
    ),
    "pin_curtain": Fix(
        id="pin_curtain",
        label="pin the curtain tie together",
        repairs_need="curtain",
        action="fastened the loose tie with a sturdy safety pin",
        proof="the curtain gathered back in a neat stripe",
        tags={"curtain", "repair"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Nora", "Sana", "Ruby", "Tess", "Eva", "June"]
BOY_NAMES = ["Owen", "Max", "Theo", "Ben", "Luca", "Sam", "Eli", "Noah"]
TRAITS = ["fair", "patient", "careful", "kind"]


def cause_matches_show(cause: Cause, show: Show) -> bool:
    return cause.breaks_need == show.need


def fix_matches_show(fix: Fix, show: Show) -> bool:
    return fix.repairs_need == show.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for show_id, show in SHOWS.items():
        for cause_id, cause in CAUSES.items():
            if not cause_matches_show(cause, show):
                continue
            for fix_id, fix in FIXES.items():
                if fix_matches_show(fix, show):
                    combos.append((show_id, cause_id, fix_id))
    return combos


def explain_rejection(show: Show, cause: Cause, fix: Optional[Fix] = None) -> str:
    if not cause_matches_show(cause, show):
        return (
            f"(No story: {cause.label} would disrupt {cause.breaks_need}, but "
            f"{show.spectacle} depends on {show.need}. The mystery and the fix "
            f"would not fit the show.)"
        )
    if fix is not None and not fix_matches_show(fix, show):
        return (
            f"(No story: '{fix.label}' repairs {fix.repairs_need}, but "
            f"{show.spectacle} needs {show.need}. Pick a fix that actually solves the problem.)"
        )
    return "(No story: this combination does not form a sensible mystery.)"


def initial_trust(trust: int) -> float:
    return float(trust)


def jumps_to_blame(trait: str, trust: int) -> bool:
    caution = 2 if trait in {"fair", "patient", "careful", "kind"} else 0
    return (trust + caution) < 5


def predict_block(world: World, show: Show, cause: Cause) -> dict:
    sim = world.copy()
    stage = sim.get("stage")
    culprit = sim.get("culprit")
    stage.meters["blocked"] += 1
    culprit.meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "delayed": stage.meters["delayed"] >= THRESHOLD,
        "need": show.need,
    }


def introduce(world: World, sleuth: Entity, friend: Entity, helper: Entity, show: Show) -> None:
    sleuth.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    sleuth.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"By dusk, {show.place} was ready for {show.spectacle}. "
        f"{show.image} waited to {show.opening}."
    )
    world.say(
        f"{sleuth.id} and {friend.id} stood close together, feeling like two small detectives. "
        f"They loved mysteries almost as much as they loved doing things side by side."
    )
    world.say(
        f"{helper.id}, the {helper.role}, was checking everything one last time with calm hands."
    )


def pop_event(world: World, sleuth: Entity, friend: Entity, show: Show, cause: Cause) -> None:
    stage = world.get("stage")
    culprit = world.get("culprit")
    pred = predict_block(world, show, cause)
    stage.meters["blocked"] += 1
    culprit.meters["active"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_delay"] = pred["delayed"]
    world.say(
        f"Then {cause.sound}. After that sharp pop, something important stopped working."
    )
    if show.need in {"power", "light"}:
        world.say(
            f"The bright part of the show went dim, and a worried murmur moved through the crowd."
        )
    else:
        world.say(
            f"The front of the stage drooped crookedly, and the show could not begin."
        )
    sleuth.memes["worry"] += 1
    friend.memes["worry"] += 1


def suspect_beat(world: World, sleuth: Entity, friend: Entity, helper: Entity) -> None:
    if jumps_to_blame(friend.attrs.get("fairness_trait", ""), int(friend.memes["trust"])):
        friend.memes["haste"] += 1
        world.say(
            f'"Was it {helper.id}?" {friend.id} whispered. "Maybe {helper.pronoun()} bumped something."'
        )
        world.say(
            f"{sleuth.id} lowered {sleuth.pronoun('possessive')} voice at once. "
            f'"A detective should not blame a person before finding clues," {sleuth.pronoun()} said.'
        )
        sleuth.memes["fairness"] += 1
    else:
        friend.memes["fairness"] += 1
        world.say(
            f'"Let\'s not guess," {friend.id} whispered. "Real detectives look first and blame last."'
        )


def search(world: World, sleuth: Entity, friend: Entity, show: Show, cause: Cause) -> None:
    sleuth.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"So the two friends began a careful search around the part of the show that needed {show.need}."
    )
    world.say(
        f"They looked low, then high, and noticed {cause.clue}."
    )


def discover(world: World, sleuth: Entity, friend: Entity, cause: Cause) -> None:
    culprit = world.get("culprit")
    culprit.meters["found"] += 1
    propagate(world, narrate=False)
    sleuth.memes["pride"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'"There!" said {sleuth.id}. Near {cause.hiding_spot}, they found the true problem.'
    )
    world.say(cause.explanation)


def apology_or_praise(world: World, sleuth: Entity, friend: Entity, helper: Entity) -> None:
    if friend.memes["haste"] >= THRESHOLD:
        friend.memes["fairness"] += 1
        world.say(
            f'{friend.id} felt {friend.pronoun("possessive")} cheeks grow warm. '
            f'"I\'m glad we checked first," {friend.pronoun()} said. '
            f'"It would have been unfair to blame {helper.id}."'
        )
    else:
        world.say(
            f'{friend.id} grinned at {sleuth.id}. "Good thing we kept our heads," {friend.pronoun()} said.'
        )


def repair(world: World, helper: Entity, show: Show, fix: Fix) -> None:
    stage = world.get("stage")
    stage.meters["blocked"] = 0.0
    stage.meters["fixed"] += 1
    stage.meters["bright"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} listened, nodded, and {fix.action}. {fix.proof}."
    )
    if stage.meters["mystery_solved"] >= THRESHOLD:
        world.say(
            f"The case was solved, and the friends had helped save the show."
        )


def ending(world: World, sleuth: Entity, friend: Entity, show: Show) -> None:
    sleuth.memes["relief"] += 1
    friend.memes["relief"] += 1
    sleuth.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"Soon {show.ending}. {sleuth.id} and {friend.id} stood shoulder to shoulder, watching the spectacle they had protected."
    )
    world.say(
        f"They felt proud not only because they were curious, but because they had been fair and loyal friends while solving the mystery."
    )


def tell(
    show: Show,
    cause: Cause,
    fix: Fix,
    sleuth_name: str,
    sleuth_gender: str,
    friend_name: str,
    friend_gender: str,
    helper_role: str,
    fairness_trait: str,
    trust: int,
) -> World:
    world = World()
    sleuth = world.add(
        Entity(
            id=sleuth_name,
            kind="character",
            type=sleuth_gender,
            role="sleuth",
            traits=["curious", fairness_trait],
            attrs={"fairness_trait": fairness_trait},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["curious"],
            attrs={"fairness_trait": fairness_trait},
        )
    )
    friend.memes["trust"] = initial_trust(trust)
    helper_type = "father" if helper_role == "caretaker" else "woman"
    helper = world.add(
        Entity(
            id="Mara" if helper_role == "librarian" else "Mr. Reed",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    helper.role = helper_role
    stage = world.add(
        Entity(
            id="stage",
            kind="thing",
            type="show",
            label=show.spectacle,
            phrase=show.spectacle,
            attrs={"need": show.need},
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="thing",
            type="cause",
            label=cause.culprit_object,
            phrase=cause.label,
            attrs={"cause": cause.id},
        )
    )

    introduce(world, sleuth, friend, helper, show)
    world.para()
    pop_event(world, sleuth, friend, show, cause)
    suspect_beat(world, sleuth, friend, helper)
    world.para()
    search(world, sleuth, friend, show, cause)
    discover(world, sleuth, friend, cause)
    apology_or_praise(world, sleuth, friend, helper)
    world.para()
    repair(world, helper, show, fix)
    ending(world, sleuth, friend, show)

    world.facts.update(
        show=show,
        cause=cause,
        fix=fix,
        sleuth=sleuth,
        friend=friend,
        helper=helper,
        stage=stage,
        culprit=culprit,
        hasty=friend.memes["haste"] >= THRESHOLD,
        solved=stage.meters["mystery_solved"] >= THRESHOLD,
        fixed=stage.meters["fixed"] >= THRESHOLD,
        delayed=stage.meters["delayed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "spectacle": [
        (
            "What is a spectacle?",
            "A spectacle is something people gather to watch because it looks exciting or wonderful. It might be a show with lights, puppets, or shadows.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and checks facts carefully. A good detective does not blame people without evidence.",
        )
    ],
    "balloon": [
        (
            "Why does a balloon make a pop sound?",
            "A balloon pops when its stretchy skin breaks and the air rushes out fast. That sudden burst makes the pop sound.",
        )
    ],
    "plug": [
        (
            "What does a plug do?",
            "A plug connects a lamp or machine to electricity. If it slips out, the thing may stop working.",
        )
    ],
    "curtain": [
        (
            "Why is a curtain important in a puppet show?",
            "A curtain helps hide the stage until the show begins. When it opens neatly, the start feels special.",
        )
    ],
    "fairness": [
        (
            "Why is it important not to accuse someone too quickly?",
            "It is important because guessing can hurt someone's feelings and spread a false idea. Fair people look for the truth first.",
        )
    ],
    "friendship": [
        (
            "How can friends solve a problem well together?",
            "Friends solve problems well when they listen to each other and stay calm. Working together helps them notice more clues and make kinder choices.",
        )
    ],
}
KNOWLEDGE_ORDER = ["spectacle", "detective", "balloon", "plug", "curtain", "fairness", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    show = f["show"]
    cause = f["cause"]
    sleuth = f["sleuth"]
    friend = f["friend"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "spectacle" and "pop".',
        f"Tell a mystery where {sleuth.id} and {friend.id} hear a pop just before {show.spectacle}, follow a clue, and solve the problem together.",
        f"Write a story about curiosity, friendship, and fairness where children refuse to blame someone too quickly and discover that {cause.label} caused the trouble.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    show = f["show"]
    cause = f["cause"]
    fix = f["fix"]
    sleuth = f["sleuth"]
    friend = f["friend"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the detectives in the story?",
            f"The little detectives are {sleuth.id} and {friend.id}. They solve the mystery together because they stay close, curious, and calm.",
        ),
        (
            "What problem happened before the show?",
            f"Just before {show.spectacle}, they heard a pop and the show could not start properly. The pop meant something important for {show.need} had gone wrong.",
        ),
        (
            "What clue helped them solve the mystery?",
            f"They noticed {cause.clue}. That clue pointed them toward the true problem instead of a wild guess.",
        ),
        (
            "How did they fix the problem?",
            f"{helper.id} {fix.action}. {fix.proof}, which showed the problem was really solved.",
        ),
        (
            "What moral did the friends learn?",
            f"They learned that curiosity should go with fairness. Instead of blaming someone too fast, they checked the facts and treated people kindly.",
        ),
    ]
    if f["hasty"]:
        qa.append(
            (
                f"Why was it good that {sleuth.id} stopped the quick guess?",
                f"It was good because a quick guess might have unfairly blamed {helper.id}. Looking for clues first protected both the truth and someone's feelings.",
            )
        )
    else:
        qa.append(
            (
                f"How did friendship help {sleuth.id} and {friend.id}?",
                f"Their friendship helped them listen to each other and stay patient. Because they worked as a team, they found the clue and saved the spectacle.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"spectacle", "detective", "fairness", "friendship"}
    tags |= set(f["show"].tags)
    tags |= set(f["cause"].tags)
    if f["show"].need == "curtain":
        tags.add("curtain")
    if f["cause"].id == "balloon":
        tags.add("balloon")
    if f["cause"].id == "loose_plug":
        tags.add("plug")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        show="lanterns",
        cause="balloon",
        fix="retie_ribbon",
        sleuth_name="Lina",
        sleuth_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        helper_role="caretaker",
        fairness_trait="fair",
        trust=2,
    ),
    StoryParams(
        show="shadow_wall",
        cause="loose_plug",
        fix="plug_back",
        sleuth_name="Max",
        sleuth_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        helper_role="librarian",
        fairness_trait="patient",
        trust=7,
    ),
    StoryParams(
        show="puppets",
        cause="button_burst",
        fix="pin_curtain",
        sleuth_name="June",
        sleuth_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        helper_role="caretaker",
        fairness_trait="kind",
        trust=6,
    ),
]


ASP_RULES = r"""
cause_matches_show(S, C) :- show_need(S, N), cause_breaks(C, N).
fix_matches_show(S, F)   :- show_need(S, N), fix_repairs(F, N).
valid(S, C, F) :- show(S), cause(C), fix(F), cause_matches_show(S, C), fix_matches_show(S, F).

careful(T) :- trait(T), fairness_trait(T).
careful(fair).
careful(patient).
careful(careful).
careful(kind).

hasty :- trust(V), V < 3.
hasty :- trust(V), V < 5, chosen_trait(T), not careful(T).

show_problem(power)   :- chosen_show(S), show_need(S, power).
show_problem(light)   :- chosen_show(S), show_need(S, light).
show_problem(curtain) :- chosen_show(S), show_need(S, curtain).

solved :- chosen_show(S), chosen_cause(C), chosen_fix(F),
          cause_matches_show(S, C), fix_matches_show(S, F).

#show valid/3.
#show hasty/0.
#show solved/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for show_id, show in SHOWS.items():
        lines.append(asp.fact("show", show_id))
        lines.append(asp.fact("show_need", show_id, show.need))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_breaks", cause_id, cause.breaks_need))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_repairs", fix_id, fix.repairs_need))
    for trait in sorted(set(TRAITS)):
        lines.append(asp.fact("trait", trait))
    for trait in ["fair", "patient", "careful", "kind"]:
        lines.append(asp.fact("fairness_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_hasty(trait: str, trust: int) -> bool:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_trait", trait),
            asp.fact("trust", trust),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "hasty"))


def asp_solved(show: str, cause: str, fix: str) -> bool:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_show", show),
            asp.fact("chosen_cause", cause),
            asp.fact("chosen_fix", fix),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "solved"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: two child detectives save a little spectacle after a mysterious pop."
    )
    ap.add_argument("--show", choices=SHOWS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper-role", choices=["caretaker", "librarian"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.show and args.cause:
        show = SHOWS[args.show]
        cause = CAUSES[args.cause]
        if not cause_matches_show(cause, show):
            raise StoryError(explain_rejection(show, cause))
    if args.show and args.fix:
        show = SHOWS[args.show]
        fix = FIXES[args.fix]
        example_cause = next(iter(CAUSES.values()))
        if not fix_matches_show(fix, show):
            raise StoryError(explain_rejection(show, example_cause, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.show is None or combo[0] == args.show)
        and (args.cause is None or combo[1] == args.cause)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    show_id, cause_id, fix_id = rng.choice(sorted(combos))
    sleuth_name, sleuth_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=sleuth_name)
    helper_role = args.helper_role or rng.choice(["caretaker", "librarian"])
    fairness_trait = rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    return StoryParams(
        show=show_id,
        cause=cause_id,
        fix=fix_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_role=helper_role,
        fairness_trait=fairness_trait,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.show not in SHOWS:
        raise StoryError(f"(Invalid show: {params.show})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")
    show = SHOWS[params.show]
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]
    if not cause_matches_show(cause, show):
        raise StoryError(explain_rejection(show, cause))
    if not fix_matches_show(fix, show):
        raise StoryError(explain_rejection(show, cause, fix))

    world = tell(
        show=show,
        cause=cause,
        fix=fix,
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_role=params.helper_role,
        fairness_trait=params.fairness_trait,
        trust=params.trust,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combinations match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = [
        ("fair", 2),
        ("fair", 8),
        ("kind", 1),
        ("patient", 6),
    ]
    bad_hasty = []
    for trait, trust in cases:
        if asp_hasty(trait, trust) != jumps_to_blame(trait, trust):
            bad_hasty.append((trait, trust))
    if not bad_hasty:
        print(f"OK: hasty-guess logic matches on {len(cases)} cases.")
    else:
        rc = 1
        print("MISMATCH in hasty-guess logic:", bad_hasty)

    bad_solved = []
    for show_id, cause_id, fix_id in CURATED_PARAMS_FOR_VERIFY():
        if asp_solved(show_id, cause_id, fix_id) != (
            cause_matches_show(CAUSES[cause_id], SHOWS[show_id])
            and fix_matches_show(FIXES[fix_id], SHOWS[show_id])
        ):
            bad_solved.append((show_id, cause_id, fix_id))
    if not bad_solved:
        print("OK: solved-state logic matches curated scenarios.")
    else:
        rc = 1
        print("MISMATCH in solved-state logic:", bad_solved)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def CURATED_PARAMS_FOR_VERIFY() -> list[tuple[str, str, str]]:
    return [(p.show, p.cause, p.fix) for p in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (show, cause, fix) combos:\n")
        for show_id, cause_id, fix_id in combos:
            print(f"  {show_id:12} {cause_id:12} {fix_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.sleuth_name} & {p.friend_name}: {p.show} / {p.cause} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
