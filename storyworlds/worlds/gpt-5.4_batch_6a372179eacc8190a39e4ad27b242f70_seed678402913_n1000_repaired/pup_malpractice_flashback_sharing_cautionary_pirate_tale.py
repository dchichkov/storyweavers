#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py
======================================================================================

A standalone story world about two children playing pirates with a family pup.
One child is tempted to play "vet" the wrong way and use grown-up medicine on the
pup. The other child remembers a flashback from a real vet visit and warns that
guessing with pet medicine is malpractice. The story then branches into either an
averted near-miss or a cautionary rescue, and ends with the children sharing the
work of caring for the pup the safe way.

Run it
------
    python storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py --ailment sore_paw --remedy pain_pill
    python storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py --response wait_and_see
    python storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pup_malpractice_flashback_sharing_cautionary_pirate_tale.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "gentle", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        dog = {"pup", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    role_plural: str
    send_off: str


@dataclass
class Ailment:
    id: str
    sign: str
    worry: str
    safe_care: str
    place: str
    risk: int = 1
    bad_ideas: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    source: str
    act: str
    danger_line: str
    effect: str
    danger: int = 1
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    ailment: str
    remedy: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    pup_name: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
    share_item: str = "blue blanket"
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    pup = world.entities.get("pup")
    if pup is None:
        return out
    if pup.meters["drugged"] < THRESHOLD and pup.meters["irritated"] < THRESHOLD:
        return out
    sig = ("distress", "pup")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pup.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    if "parent" in world.entities:
        world.get("parent").memes["urgency"] += 1
    out.append("__distress__")
    return out


def _r_share_soothes(world: World) -> list[str]:
    out: list[str] = []
    pup = world.entities.get("pup")
    if pup is None:
        return out
    if pup.meters["shared_care"] < THRESHOLD:
        return out
    sig = ("soothe", "pup")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pup.memes["calm"] += 1
    if pup.memes["fear"] >= THRESHOLD:
        pup.memes["fear"] = 0.0
    for kid in world.kids():
        kid.memes["care"] += 1
    out.append("__soothed__")
    return out


CAUSAL_RULES = [
    Rule(name="distress", tag="health", apply=_r_distress),
    Rule(name="share_soothes", tag="care", apply=_r_share_soothes),
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
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a bright pirate cove",
        rig="The sofa was their ship, a laundry basket was the crow's nest, and a rolled towel was the treasure map.",
        titles=("Captain", "Lookout"),
        goal="the cookie-tin treasure",
        role_plural="pirates",
        send_off="sailed back into their game",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a windy harbor",
        rig="The rug was their dock, two chairs made a little boat, and a spoon tapped a bell for arriving ships.",
        titles=("Captain", "Mate"),
        goal="the brass-button treasure",
        role_plural="harbor pirates",
        send_off="set off to guard the harbor",
    ),
    "island": Theme(
        id="island",
        scene="a stormy island",
        rig="The bedspread became a striped sail, a shoebox held the treasure, and a pillow fort marked the hidden cave.",
        titles=("Captain", "Scout"),
        goal="the hidden cave chest",
        role_plural="island pirates",
        send_off="hurried off to explore the cave again",
    ),
}

AILMENTS = {
    "sore_paw": Ailment(
        id="sore_paw",
        sign="the pup lifted one paw and gave a soft little whine",
        worry="a sore paw",
        safe_care="resting the paw and letting a grown-up check it",
        place="after skidding on the rug",
        risk=1,
        bad_ideas={"pain_pill", "rash_cream"},
        tags={"paw", "pets"},
    ),
    "tummy_ache": Ailment(
        id="tummy_ache",
        sign="the pup's tummy gave a funny gurgle and he curled into a tight little ball",
        worry="a tummy ache",
        safe_care="plain water, quiet rest, and a grown-up calling the vet if needed",
        place="after gobbling a crust too fast",
        risk=2,
        bad_ideas={"pain_pill", "cough_syrup"},
        tags={"tummy", "pets"},
    ),
    "sneeze": Ailment(
        id="sneeze",
        sign="the pup sneezed three times and blinked at the dusty curtain tassel",
        worry="a sneezy nose",
        safe_care="moving away from the dust and letting a grown-up decide what to do",
        place="after poking his nose where the dust was hiding",
        risk=1,
        bad_ideas={"cough_syrup"},
        tags={"sneeze", "pets"},
    ),
}

REMEDIES = {
    "pain_pill": Remedy(
        id="pain_pill",
        label="a pain pill",
        phrase="one of the grown-up pain pills",
        source="in the bathroom cabinet",
        act="held up a pain pill and reached toward the pup's mouth",
        danger_line="people medicine can hurt a dog badly",
        effect="The little pill was far too strong for a tiny pup.",
        danger=2,
        tags={"medicine", "pills", "call_vet"},
    ),
    "cough_syrup": Remedy(
        id="cough_syrup",
        label="cough syrup",
        phrase="a spoon of cough syrup",
        source="on the high shelf above the sink",
        act="tipped the sticky spoon toward the pup's tongue",
        danger_line="sweet cough syrup is not safe for pets",
        effect="The syrup made the pup droop and lick his lips in confusion.",
        danger=2,
        tags={"medicine", "syrup", "call_vet"},
    ),
    "rash_cream": Remedy(
        id="rash_cream",
        label="rash cream",
        phrase="a dab of rash cream",
        source="beside the grown-up toothbrushes",
        act="smeared a dab of cream onto the pup's sore paw",
        danger_line="skin cream can sting and should never be guessed at for pets",
        effect="The cream made the paw feel worse, and the pup kept licking at it.",
        danger=1,
        tags={"medicine", "cream", "rinse"},
    ),
}

RESPONSES = {
    "call_vet": Response(
        id="call_vet",
        sense=3,
        power=4,
        text="scooped the pup up, called the vet right away, and followed every calm instruction over the phone",
        fail="called the vet, but the medicine had already had too much time to work through the pup's small body",
        qa_text="called the vet right away and followed the vet's instructions",
        tags={"vet", "call_vet"},
    ),
    "rinse_and_call": Response(
        id="rinse_and_call",
        sense=3,
        power=3,
        text="washed the wrong medicine off, kept the pup from licking more, and called the vet for help",
        fail="washed what she could and called the vet, but the mistake had already made the pup much sicker",
        qa_text="washed the wrong medicine off and called the vet",
        tags={"vet", "rinse"},
    ),
    "wait_and_see": Response(
        id="wait_and_see",
        sense=1,
        power=1,
        text="sat down to wait and see whether the pup would fix himself",
        fail="waited too long, and the pup only grew dizzier and more frightened",
        qa_text="waited instead of getting help",
        tags={"delay"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
PUP_NAMES = ["Pip", "Ruff", "Moss", "Bean", "Patch", "Skipper"]
TRAITS = ["careful", "gentle", "curious", "sensible", "thoughtful", "brave"]
SHARE_ITEMS = ["blue blanket", "striped towel", "small water bowl", "captain's pillow"]


def hazard_at_risk(ailment: Ailment, remedy: Remedy) -> bool:
    return remedy.id in ailment.bad_ideas


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def health_severity(ailment: Ailment, remedy: Remedy, delay: int) -> int:
    return ailment.risk + remedy.danger + delay


def is_contained(response: Response, ailment: Ailment, remedy: Remedy, delay: int) -> bool:
    return response.power >= health_severity(ailment, remedy, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_medicine(world: World, remedy_id: str) -> dict:
    sim = world.copy()
    remedy = REMEDIES[remedy_id]
    _do_bad_remedy(sim, remedy, narrate=False)
    pup = sim.get("pup")
    return {
        "distress": pup.meters["drugged"] + pup.meters["irritated"],
        "fear": pup.memes["fear"],
    }


def _do_bad_remedy(world: World, remedy: Remedy, narrate: bool = True) -> None:
    pup = world.get("pup")
    if remedy.id == "rash_cream":
        pup.meters["irritated"] += 1
    else:
        pup.meters["drugged"] += 1
    pup.meters["treated_wrong"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, pup: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    pup.memes["joy"] += 1
    world.say(
        f"One afternoon, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'{pup.id}, their little pup, bounced after them with a rope in his mouth as if he were the ship\'s own dog.'
    )
    world.say(
        f'"{theme.titles[0]} {a.id} and {theme.titles[1]} {b.id}!" {a.id} cried. '
        f'"Today we find {theme.goal}!"'
    )


def symptom(world: World, pup: Entity, ailment: Ailment) -> None:
    pup.meters["symptom"] += 1
    world.say(
        f"But {ailment.place}, the game hit a bump: {ailment.sign}."
    )


def worry(world: World, a: Entity, ailment: Ailment) -> None:
    a.memes["concern"] += 1
    world.say(
        f'{a.id} stopped short. "Oh no," {a.pronoun()} whispered. "Maybe {world.get("pup").id} has {ailment.worry}."'
    )


def tempt(world: World, a: Entity, remedy: Remedy) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id}\'s eyes snapped toward the hall. "I know what to do! I saw {remedy.phrase} {remedy.source}."'
    )
    world.say("For one quick moment, the idea sounded fast and clever.")


def flashback_warn(world: World, b: Entity, a: Entity, remedy: Remedy, ailment: Ailment, parent: Entity) -> None:
    pred = predict_medicine(world, remedy.id)
    b.memes["caution"] += 1
    world.facts["predicted_distress"] = pred["distress"]
    world.say(
        f"Then a flashback popped into {b.id}'s mind: the bright vet office from last spring, "
        f"with the pup on a silver table and the vet speaking gently."
    )
    world.say(
        f'"When people guess with medicine for an animal instead of asking for proper help, that is malpractice," '
        f'the vet had said. "It means taking bad care by pretending to know more than you do."'
    )
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} remembered every word."
    world.say(
        f'{b.id} grabbed {a.id}\'s sleeve. "{a.id}, no. {remedy.danger_line}. '
        f'{parent.label_word.capitalize()} said we must never give our pup grown-up medicine."{extra}'
    )
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "The safe thing is {ailment.safe_care}, not guessing."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, share_item: str, ailment: Ailment, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id}, then at the pup, and the brave-fast idea melted away. '
        f'"You\'re right," {a.pronoun()} said. "That would be bad care."'
    )
    world.say(
        f'Together they called for {parent.label_word}. Then they shared the {share_item} over the pup like a tiny captain\'s cloak and set a little bowl of water beside him.'
    )
    pup = world.get("pup")
    pup.meters["shared_care"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} checked the pup, smiled at their careful waiting, and helped with {ailment.safe_care}.'
    )
    world.para()
    world.say(
        f"The next day the pup was thumping his tail again, and the two {theme.role_plural} took turns being captain."
    )
    world.say(
        f"They shared the map, shared the treasure coins, and {theme.send_off} with the pup trotting safely beside them."
    )


def defy(world: World, a: Entity, b: Entity, remedy: Remedy) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It will only be a tiny bit," {a.id} said, and before {b.id} could stop {a.pronoun("object")}, {a.pronoun()} ran for the medicine.'
    )
    world.say(
        f'Back at the ship, {a.id} {remedy.act}.'
    )


def mistake(world: World, pup: Entity, remedy: Remedy) -> None:
    _do_bad_remedy(world, remedy, narrate=False)
    world.say(
        f"{remedy.effect} {pup.id} drew back, confused and unhappy."
    )


def alarm(world: World, b: Entity, pup: Entity, parent: Entity) -> None:
    world.say(f'"{pup.id} doesn\'t like it!" {b.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, pup: Entity, ailment: Ailment, share_item: str) -> None:
    pup.meters["drugged"] = 0.0
    pup.meters["irritated"] = 0.0
    pup.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running and {response.text}."
    )
    world.say(
        f"Soon the room grew quieter. The pup was still shaky, but he was in careful hands now."
    )
    pup.meters["shared_care"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} had the children share the work too: one held the {share_item}, and the other slid over the water bowl.'
    )
    world.say(
        f"That kind of sharing helped the pup settle while the grown-up watched him."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "I am glad you called me," {parent.pronoun()} said softly. '
        f'"But giving pets the wrong medicine is never a game. Guessing like that is malpractice, which means careless treatment. We ask a vet or a grown-up instead."'
    )
    world.say(
        f'"We understand," whispered {b.id} and {a.id} together.'
    )


def safe_ending(world: World, a: Entity, b: Entity, pup: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    pup.memes["joy"] += 1
    world.para()
    world.say(
        f"By the next afternoon, {pup.id} was wagging again. This time the {theme.role_plural} played a gentler game."
    )
    world.say(
        f"{a.id} shared the captain's hat with {b.id}, and {b.id} shared the rope toy with {pup.id}."
    )
    world.say(
        f"So they {theme.send_off} -- kinder, slower, and much wiser than before."
    )


def rescue_fail(world: World, parent: Entity, response: Response, pup: Entity, share_item: str) -> None:
    pup.meters["drugged"] += 1
    pup.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail}."
    )
    world.say(
        f"{pup.id}'s legs wobbled, and the game fell away completely."
    )
    world.say(
        f"Even then, {parent.label_word} made the children help in the only safe way they could: one carried the {share_item}, and the other held the car door open."
    )


def vet_trip(world: World, parent: Entity, a: Entity, b: Entity, pup: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} wrapped {pup.id} in a towel and hurried the children to the car for an emergency vet visit."
    )
    world.say(
        "The waiting room was bright and still, and the children sat shoulder to shoulder, listening for every small sound."
    )
    world.say(
        f"At last the vet said the pup would recover, but only because help had finally come."
    )


def sober_lesson(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'Outside the clinic, {parent.label_word.capitalize()} hugged them close. "{a.id}, {b.id}, loving an animal means asking for real help," {parent.pronoun()} said.'
    )
    world.say(
        'After that, when the game wanted to turn a pretend captain into a pretend doctor, both children remembered the vet\'s word: malpractice.'
    )
    world.say(
        f"And whenever their pup needed comfort, they shared the job instead -- one with water, one with a blanket, both with gentle hands."
    )
    world.say(
        f"Later, when they played {theme.role_plural} again, the ship sailed only with make-believe cures and real care."
    )


def tell(
    theme: Theme,
    ailment: Ailment,
    remedy: Remedy,
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    pup_name: str = "Pip",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
    share_item: str = "blue blanket",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    pup = world.add(Entity(
        id="pup",
        kind="character",
        type="pup",
        role="pup",
        label=pup_name,
        attrs={"name": pup_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    world.facts["pup_name"] = pup_name

    introduce(world, a, b, pup, theme)
    symptom(world, pup, ailment)
    worry(world, a, ailment)

    world.para()
    tempt(world, a, remedy)
    flashback_warn(world, b, a, remedy, ailment, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent, share_item, ailment, theme)
        severity = 0
        contained = True
        outcome = "averted"
    else:
        defy(world, a, b, remedy)
        world.para()
        mistake(world, pup, remedy)
        alarm(world, b, pup, parent)

        severity = health_severity(ailment, remedy, delay)
        pup.meters["severity"] = float(severity)
        contained = is_contained(response, ailment, remedy, delay)

        world.para()
        if contained:
            rescue(world, parent, response, pup, ailment, share_item)
            lesson(world, parent, a, b)
            safe_ending(world, a, b, pup, theme)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, pup, share_item)
            vet_trip(world, parent, a, b, pup)
            sober_lesson(world, parent, a, b, theme)
            outcome = "vet_trip"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        pup=pup,
        theme=theme,
        ailment=ailment,
        remedy=remedy,
        response=response,
        share_item=share_item,
        relation=relation,
        ignited=pup.meters["treated_wrong"] >= THRESHOLD,
        severity=severity,
        delay=delay,
        outcome=outcome,
        promised=a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for ailment_id, ailment in AILMENTS.items():
            for remedy_id, remedy in REMEDIES.items():
                if hazard_at_risk(ailment, remedy):
                    combos.append((theme_id, ailment_id, remedy_id))
    return combos


def explain_rejection(ailment: Ailment, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} is not the bad guess this world tells for {ailment.worry}. "
        f"This story only allows a danger that a child might wrongly believe would help, "
        f"so the mistake stays clear and cautionary.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], AILMENTS[params.ailment], REMEDIES[params.remedy], params.delay)
    return "contained" if contained else "vet_trip"


KNOWLEDGE = {
    "pets": [(
        "Why should children ask a grown-up before giving medicine to a pet?",
        "Pets have small bodies and need the right medicine in the right amount. A grown-up or a vet knows what is safe."
    )],
    "medicine": [(
        "Why can people medicine be dangerous for a dog?",
        "Medicine made for people can be too strong or wrong for a dog. It can make the dog very sick."
    )],
    "call_vet": [(
        "What should you do if an animal gets the wrong medicine?",
        "Tell a grown-up right away and call a vet as fast as you can. Getting real help quickly gives the animal the best chance to feel better."
    )],
    "vet": [(
        "What does a vet do?",
        "A vet is an animal doctor. Vets know how to help pets when they are hurt or sick."
    )],
    "sharing": [(
        "How can sharing help when a pet needs comfort?",
        "One person can bring water while another brings a blanket or stays nearby. Sharing the job means the pet gets calm, gentle care."
    )],
    "malpractice": [(
        "What does malpractice mean in this story?",
        "Here it means pretending to know how to treat an animal when you really do not. It is careless treatment instead of safe, expert help."
    )],
    "pirates": [(
        "What makes a pirate game pretend instead of real?",
        "Pretend pirate things are play objects like pillows, maps, and hats. Real danger should never be part of the game."
    )],
}
KNOWLEDGE_ORDER = ["pets", "medicine", "call_vet", "vet", "sharing", "malpractice", "pirates"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    remedy = f["remedy"]
    ailment = f["ailment"]
    theme = f["theme"]
    pup = f["pup"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the words "pup" and "malpractice".',
            f"Tell a gentle near-miss story where {a.id} wants to use {remedy.label} on a pup with {ailment.worry}, but {b.id} remembers a flashback from the vet and stops it.",
            f"Write a story about pretend pirates who learn that sharing comfort and asking a grown-up is wiser than guessing with medicine.",
        ]
    if outcome == "vet_trip":
        return [
            f'Write a cautionary pirate-style story for a 3-to-5-year-old that includes the words "pup" and "malpractice".',
            f"Tell a story where {a.id} ignores a flashback warning, gives the pup the wrong medicine, and the family must rush to the vet.",
            f"Write a story that teaches children not to play doctor with pets, and let sharing help comfort the pup at the end.",
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "pup" and "malpractice".',
        f"Tell a gentle cautionary story where two children playing {theme.role_plural} are tempted to use {remedy.label} on a pup, but a grown-up fixes the mistake safely.",
        f"Write a story with a flashback warning, a wrong choice, and an ending where the children share the work of caring for the pup.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    pup = f["pup"]
    theme = f["theme"]
    ailment = f["ailment"]
    remedy = f["remedy"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    share_item = f["share_item"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their little pup named {pup.attrs.get('name', pup.id)}. They were pretending to be {theme.role_plural} when the trouble started.",
        ),
        (
            "What problem did the pup seem to have?",
            f"The pup seemed to have {ailment.worry}. The children noticed it when {ailment.sign}.",
        ),
        (
            f"What unsafe idea did {a.id} have?",
            f"{a.id} wanted to use {remedy.label} on the pup. That was unsafe because {remedy.danger_line}.",
        ),
        (
            f"What was the flashback about?",
            f"{b.id} remembered a real visit to the vet. In that flashback, the vet said that guessing with animal medicine is malpractice, which means careless treatment instead of proper help.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How did the children help the pup safely?",
            f"They called {parent.label_word} and waited instead of guessing with medicine. They also shared the {share_item} and a bowl of water, which let them comfort the pup together while the grown-up checked him."
        ))
        qa.append((
            "How did the story end?",
            f"It ended peacefully. The pup felt better, and the children shared their pirate game and their caring jobs in a kinder way."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"How did {a.id}'s {parent.label_word} fix the mistake?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That quick help kept the wrong medicine from turning into a bigger emergency."
        ))
        qa.append((
            "Why did sharing matter after the mistake?",
            f"The children shared the work of helping the pup. One held the {share_item} while the other brought water, so the pup could settle down in a calm way."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that pets need real help, not pretend doctor games. They also learned that sharing careful jobs is a much better way to show love."
        ))
    else:
        qa.append((
            "Did the pup get better right away?",
            f"No. The pup grew shakier, and the family had to hurry to the vet. The story becomes scary to show how quickly a wrong medicine choice can turn serious."
        ))
        qa.append((
            "What did the children do at the clinic?",
            f"They stayed close together and shared the work they could safely do. One carried the comfort item and the other helped with the door, because helping calmly was all that was left to do."
        ))
        qa.append((
            "What lesson stayed with them afterward?",
            f"They remembered the vet's warning about malpractice. After that, they never treated pretend caring like real animal medicine again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pets", "sharing", "malpractice", "pirates"}
    remedy = world.facts["remedy"]
    response = world.facts["response"]
    tags |= set(remedy.tags)
    tags |= set(response.tags)
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        ailment="sore_paw",
        remedy="pain_pill",
        response="call_vet",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        pup_name="Pip",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
        share_item="blue blanket",
    ),
    StoryParams(
        theme="harbor",
        ailment="tummy_ache",
        remedy="cough_syrup",
        response="call_vet",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        pup_name="Patch",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
        share_item="striped towel",
    ),
    StoryParams(
        theme="island",
        ailment="sore_paw",
        remedy="rash_cream",
        response="rinse_and_call",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        pup_name="Bean",
        parent="mother",
        trait="gentle",
        delay=0,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=6,
        share_item="captain's pillow",
    ),
    StoryParams(
        theme="pirates",
        ailment="tummy_ache",
        remedy="pain_pill",
        response="rinse_and_call",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Rose",
        cautioner_gender="girl",
        pup_name="Skipper",
        parent="father",
        trait="sensible",
        delay=2,
        instigator_age=7,
        cautioner_age=4,
        relation="siblings",
        trust=3,
        share_item="small water bowl",
    ),
]


ASP_RULES = r"""
hazard(A, R) :- ailment(A), remedy(R), bad_idea(A, R).
sensible(P)  :- response(P), sense(P, S), sense_min(M), S >= M.
valid(T, A, R) :- theme(T), hazard(A, R).

cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
cautioner_older  :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)         :- cautioner_older.
bonus(0)         :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Ar + Rd + D) :- chosen_ailment(A), ailment_risk(A, Ar),
                         chosen_remedy(R), remedy_danger(R, Rd), delay(D).
resp_power(P)    :- chosen_response(Rp), power(Rp, P).
contained        :- resp_power(P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(vet_trip)  :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for aid, ailment in AILMENTS.items():
        lines.append(asp.fact("ailment", aid))
        lines.append(asp.fact("ailment_risk", aid, ailment.risk))
        for rid in sorted(ailment.bad_ideas):
            lines.append(asp.fact("bad_idea", aid, rid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_danger", rid, remedy.danger))
    for pid, response in RESPONSES.items():
        lines.append(asp.fact("response", pid))
        lines.append(asp.fact("sense", pid, response.sense))
        lines.append(asp.fact("power", pid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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

    scenario = "\n".join([
        asp.fact("chosen_ailment", params.ailment),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate game, a pup, a bad medicine guess, and a safer way to care."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--ailment", choices=AILMENTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help is delayed")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.ailment and args.remedy:
        ailment = AILMENTS[args.ailment]
        remedy = REMEDIES[args.remedy]
        if not hazard_at_risk(ailment, remedy):
            raise StoryError(explain_rejection(ailment, remedy))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.ailment is None or c[1] == args.ailment)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, ailment, remedy = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    pup_name = rng.choice(PUP_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    share_item = rng.choice(SHARE_ITEMS)
    return StoryParams(
        theme=theme,
        ailment=ailment,
        remedy=remedy,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        pup_name=pup_name,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        share_item=share_item,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        ailment = AILMENTS[params.ailment]
        remedy = REMEDIES[params.remedy]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not hazard_at_risk(ailment, remedy):
        raise StoryError(explain_rejection(ailment, remedy))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=theme,
        ailment=ailment,
        remedy=remedy,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        pup_name=params.pup_name,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        share_item=params.share_item,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, ailment, remedy) combos:\n")
        for theme, ailment, remedy in combos:
            print(f"  {theme:8} {ailment:11} {remedy}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.ailment} / {p.remedy} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
