#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/solicit_profile_happy_ending_lesson_learned_bad.py
==============================================================================

A standalone storyworld about a child with an online profile, a stranger who
tries to solicit private information, and the different ways a sensible helper
can turn that moment toward safety.

The domain is small and slice-of-life: a child posts something ordinary on a
kid-facing app, notices a flattering message from a stranger, and must decide
what to do when the message asks for personal details. The world model prefers
stories where a grown-up or older sibling helps the child make the profile
safer, block the stranger, and keep enjoying life in a wiser way. It can also
tell a sadder "bad ending" where too much information is shared and the account
has to be closed, though the child still learns the lesson safely.

Run it
------
    python storyworlds/worlds/gpt-5.4/solicit_profile_happy_ending_lesson_learned_bad.py
    python storyworlds/worlds/gpt-5.4/solicit_profile_happy_ending_lesson_learned_bad.py --all
    python storyworlds/worlds/gpt-5.4/solicit_profile_happy_ending_lesson_learned_bad.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/solicit_profile_happy_ending_lesson_learned_bad.py --qa
    python storyworlds/worlds/gpt-5.4/solicit_profile_happy_ending_lesson_learned_bad.py --verify
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
CAUTIOUS_TRAITS = {"careful", "thoughtful", "shy", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "sister": "sister", "brother": "brother"}.get(
            self.type, self.type
        )


@dataclass
class Platform:
    id: str
    label: str
    noun: str
    post: str
    audience: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ask:
    id: str
    text: str
    detail: str
    danger: str
    sensitivity: int
    shared_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    do_share: bool
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PrivacyFix:
    id: str
    text: str
    ending: str
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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    stranger = world.get("stranger")
    if child.meters["public_profile"] >= THRESHOLD and stranger.meters["soliciting"] >= THRESHOLD:
        sig = ("risk", "profile")
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["risk"] += 1
            child.memes["unease"] += 1
            out.append("__risk__")
    return out


def _r_exposure(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["shared_private"] >= THRESHOLD:
        sig = ("exposure", "child")
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["exposed"] += 1
            child.memes["worry"] += 1
            out.append("__exposure__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if helper.meters["helped"] >= THRESHOLD:
        sig = ("relief", "child")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["trust"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="risk", tag="social", apply=_r_risk),
    Rule(name="exposure", tag="social", apply=_r_exposure),
    Rule(name="relief", tag="social", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(platform: Platform, ask: Ask) -> bool:
    return "profile" in platform.tags and ask.sensitivity >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_ask_first(relation: str, child_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > child_age
    authority = initial_caution(trait) + (4.0 if helper_older else 0.0)
    return helper_older and authority > 6.0


def exposure_severity(ask: Ask, delay: int) -> int:
    return ask.sensitivity + delay


def is_contained(response: Response, ask: Ask, delay: int) -> bool:
    return response.power >= exposure_severity(ask, delay)


def predict_trouble(world: World, ask: Ask) -> dict:
    sim = world.copy()
    sim.get("stranger").meters["soliciting"] += 1
    sim.facts["ask"] = ask
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("child").meters["risk"],
        "ask_id": ask.id,
    }


def scene_setup(world: World, child: Entity, helper: Entity, platform: Platform) -> None:
    child.memes["joy"] += 1
    world.get("device").meters["on"] += 1
    world.get("child").meters["public_profile"] += 1
    world.say(
        f"After homework, {child.id} curled up on the couch with a tablet while "
        f"{helper.id} sat nearby. On {platform.label}, {child.id} had made a small profile "
        f"with {platform.audience}."
    )
    world.say(
        f"{child.pronoun().capitalize()} posted {platform.post}, and the room felt soft and ordinary, "
        f"full of lamp light and the little sounds of home. {platform.scene}"
    )


def stranger_appears(world: World, child: Entity, platform: Platform) -> None:
    stranger = world.get("stranger")
    stranger.meters["soliciting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A new message popped up from a shiny profile called {stranger.label}. "
        f'"Your work is amazing," it said. "I want to know more about you."'
    )
    world.say(
        f"The note looked friendly, but it did more than chat. It began to solicit "
        f"private facts from a child who had only meant to share {platform.noun}."
    )


def warning(world: World, helper: Entity, child: Entity, ask: Ask) -> None:
    pred = predict_trouble(world, ask)
    world.facts["predicted_risk"] = pred["risk"]
    child.memes["pause"] += 1
    world.say(
        f"Then another line arrived: \"{ask.text}\" {child.id} read it twice, feeling a small pinch in "
        f"{child.pronoun('possessive')} chest."
    )
    world.say(
        f'{helper.id} leaned closer. "{ask.detail} is not for strangers," {helper.pronoun()} said. '
        f'"A fake profile can ask sweetly and still be unsafe."'
    )


def ask_first(world: World, child: Entity, helper: Entity) -> None:
    helper.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Instead of typing back, {child.id} set the tablet in {helper.id}'s lap and asked what to do. "
        f"That one small pause changed the whole evening."
    )


def reply_anyway(world: World, child: Entity, ask: Ask) -> None:
    child.meters["shared_private"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For one quick moment, the praise felt warm. {child.id} typed back {ask.shared_line}, "
        f"not knowing how much a stranger could do with a tiny scrap of private information."
    )


def rescue(world: World, helper: Entity, response: Response, fix: PrivacyFix, child: Entity) -> None:
    helper.meters["helped"] += 1
    world.get("child").meters["public_profile"] = 0.0
    world.get("stranger").meters["soliciting"] = 0.0
    world.get("child").meters["risk"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} stayed calm and {response.text}. Then {helper.pronoun()} {fix.text}."
    )
    world.say(
        f'"Real friends do not need secrets from a child," {helper.pronoun()} explained. '
        f'"If a message tries to solicit private details, we stop and tell a grown-up."'
    )
    child.memes["lesson"] += 1
    child.memes["worry"] = 0.0


def consequence(world: World, helper: Entity, child: Entity, fix: PrivacyFix, ask: Ask) -> None:
    helper.meters["helped"] += 1
    world.get("child").meters["public_profile"] = 0.0
    world.get("stranger").meters["soliciting"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"When {helper.id} saw what had been sent, {helper.pronoun('possessive')} face went serious. "
        f"{helper.pronoun().capitalize()} explained that {ask.danger}, so the account had to be closed for now."
    )
    world.say(
        f"Together they {fix.text}, but the cheerful little profile was put away for the night. "
        f"The tablet stayed dark on the coffee table, and the room felt much quieter than before."
    )
    child.memes["lesson"] += 1
    child.memes["sad"] += 1


def ending_happy(world: World, child: Entity, helper: Entity, platform: Platform, fix: PrivacyFix) -> None:
    child.memes["joy"] += 1
    child.memes["safe"] += 1
    world.say(
        f"The next day, {child.id} made a fresh profile with only safe bits to share. "
        f"{fix.ending}"
    )
    world.say(
        f"Soon {child.pronoun()} was back to sharing {platform.noun} with people {helper.id} trusted, "
        f"and the evening ended with cocoa, a safer screen, and a lighter heart."
    )


def ending_bad(world: World, child: Entity, helper: Entity) -> None:
    child.memes["safe"] += 1
    world.say(
        f"{child.id} was safe at home, but {child.pronoun()} had to lose the account for a while. "
        f"{child.pronoun().capitalize()} leaned against {helper.id} and promised never to answer a stranger's questions alone again."
    )
    world.say(
        f"Later, they played a board game at the kitchen table instead. It was still a quiet family night, "
        f"only now the lesson sat beside them like an extra chair."
    )


def tell(
    platform: Platform,
    ask: Ask,
    response: Response,
    fix: PrivacyFix,
    *,
    child_name: str = "Lina",
    child_type: str = "girl",
    helper_name: str = "Maya",
    helper_type: str = "sister",
    helper_role: str = "helper",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    child_age: int = 8,
    helper_age: int = 11,
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=[trait],
            age=child_age,
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role=helper_role,
            age=helper_age,
            attrs={"relation": relation, "parent_type": parent_type},
        )
    )
    world.add(Entity(id="device", type="tablet", label="tablet"))
    world.add(Entity(id="stranger", type="stranger", label="SunnyStar88", role="stranger"))

    scene_setup(world, child, helper, platform)

    world.para()
    stranger_appears(world, child, platform)
    warning(world, helper, child, ask)

    averted = would_ask_first(relation, child_age, helper_age, trait)
    if averted:
        ask_first(world, child, helper)
        world.para()
        rescue(world, helper, RESPONSES["tell_helper"], fix, child)
        world.para()
        ending_happy(world, child, helper, platform, fix)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        reply_anyway(world, child, ask)
        severity = exposure_severity(ask, delay)
        contained = is_contained(response, ask, delay)
        world.para()
        if contained:
            rescue(world, helper, response, fix, child)
            world.para()
            ending_happy(world, child, helper, platform, fix)
            outcome = "contained"
        else:
            consequence(world, helper, child, fix, ask)
            world.para()
            ending_bad(world, child, helper)
            outcome = "bad"

    world.facts.update(
        child=child,
        helper=helper,
        platform=platform,
        ask=ask,
        response=response,
        fix=fix,
        relation=relation,
        averted=averted,
        outcome=outcome,
        severity=severity,
        delay=delay,
        contained=contained,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


PLATFORMS = {
    "drawing_club": Platform(
        id="drawing_club",
        label="Little Drawing Club",
        noun="drawings",
        post="a picture of a red kite over the park",
        audience="a nickname and a favorite color",
        scene="The heater hummed, and dinner smells drifted in from the kitchen.",
        tags={"profile", "art"},
    ),
    "pet_board": Platform(
        id="pet_board",
        label="Pet Snap Board",
        noun="pet photos",
        post="a photo of the family's sleepy cat under a blanket",
        audience="a nickname and a pet's silly habit",
        scene="A spoon clinked in a mug, and rain tapped softly on the window.",
        tags={"profile", "pets"},
    ),
    "book_corner": Platform(
        id="book_corner",
        label="Story Corner",
        noun="book reviews",
        post="a short note about a dragon book from the library",
        audience="a nickname and a favorite story",
        scene="Socks warmed on the rug while pages from a library book lay open nearby.",
        tags={"profile", "books"},
    ),
}

ASKS = {
    "school": Ask(
        id="school",
        text="What school do you go to?",
        detail="Your school is private information",
        danger="a stranger who learns your school can learn too much about your day",
        sensitivity=2,
        shared_line='which school bus stopped near the playground',
        tags={"school", "private_info"},
    ),
    "address": Ask(
        id="address",
        text="What street do you live on?",
        detail="Your address is private information",
        danger="an address tells strangers exactly where a child can be found",
        sensitivity=3,
        shared_line='the name of the street by the bakery',
        tags={"address", "private_info"},
    ),
    "real_name": Ask(
        id="real_name",
        text="What is your full real name?",
        detail="Your full real name is private information",
        danger="a full name can help strangers connect many pieces of a child's life",
        sensitivity=1,
        shared_line='the first and last name written on a library card',
        tags={"name", "private_info"},
    ),
}

RESPONSES = {
    "tell_helper": Response(
        id="tell_helper",
        sense=3,
        power=4,
        do_share=False,
        text="took a screenshot, blocked the stranger, and called a grown-up over",
        qa_text="blocked the stranger and showed the message to a grown-up",
        tags={"block", "tell_adult"},
    ),
    "report_then_tell": Response(
        id="report_then_tell",
        sense=3,
        power=3,
        do_share=False,
        text="reported the message inside the app, blocked the stranger, and sat beside the child until a grown-up came",
        qa_text="reported the message, blocked the stranger, and told a grown-up",
        tags={"report", "block", "tell_adult"},
    ),
    "delete_and_hide": Response(
        id="delete_and_hide",
        sense=2,
        power=2,
        do_share=False,
        text="deleted the chat, blocked the stranger, and brought the tablet straight to a grown-up",
        qa_text="deleted the chat, blocked the stranger, and told a grown-up",
        tags={"block", "tell_adult"},
    ),
    "answer_politely": Response(
        id="answer_politely",
        sense=1,
        power=1,
        do_share=True,
        text="typed a polite answer before asking anyone else",
        qa_text="answered the stranger first",
        tags={"unsafe_reply"},
    ),
}

PRIVACY_FIXES = {
    "private_nickname": PrivacyFix(
        id="private_nickname",
        text="changed the account so only approved people could see the profile and trimmed it down to a nickname",
        ending="They chose a flower nickname and left out every clue about school or street names.",
        tags={"privacy", "nickname"},
    ),
    "family_check": PrivacyFix(
        id="family_check",
        text="set the profile to private and made a new family rule to check messages together",
        ending="From then on, new messages were read with a grown-up nearby before any reply was sent.",
        tags={"privacy", "family_rule"},
    ),
    "friends_only": PrivacyFix(
        id="friends_only",
        text="changed the settings to friends-only and removed extra details from the profile",
        ending="Now the profile held only cheerful safe things, like favorite colors and drawings, and nothing a stranger could use.",
        tags={"privacy", "friends_only"},
    ),
}

GIRL_NAMES = ["Lina", "Ruby", "Mia", "Nora", "Ella", "Sana", "Lucy", "Ivy"]
BOY_NAMES = ["Owen", "Max", "Leo", "Finn", "Eli", "Noah", "Sam", "Theo"]
HELPER_NAMES = ["Maya", "Auntie Jo", "Dad", "Nina", "Ben", "Mom"]
TRAITS = ["careful", "curious", "shy", "thoughtful", "chatty", "proud", "sensible"]


@dataclass
class StoryParams:
    platform: str
    ask: str
    response: str
    fix: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    parent_type: str
    trait: str
    relation: str = "siblings"
    child_age: int = 8
    helper_age: int = 11
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "profile": [
        (
            "What is an online profile?",
            "An online profile is a small page with information about a person. It should only share safe details, not private ones."
        )
    ],
    "solicit": [
        (
            "What does solicit mean in a safety story?",
            "It means trying to ask for something. When a stranger solicits private facts from a child, that is not safe."
        )
    ],
    "privacy": [
        (
            "Why should children keep private information off the internet?",
            "Private information can help strangers learn too much about a child. Safe sharing means leaving out names, schools, streets, and other clues."
        )
    ],
    "block": [
        (
            "What does it mean to block someone online?",
            "Blocking someone stops them from sending more messages to you. It is a good safety step when a stranger is bothering you."
        )
    ],
    "report": [
        (
            "What does it mean to report a message?",
            "Reporting tells the app that a message may be unsafe or against the rules. It helps adults who run the app notice problems."
        )
    ],
    "tell_adult": [
        (
            "What should a child do if a stranger asks for private information online?",
            "The child should stop, not answer, and tell a trusted grown-up right away. A grown-up can help block the person and make the account safer."
        )
    ],
    "address": [
        (
            "Why is your address private?",
            "Your address tells people where you live. That is something strangers should not know."
        )
    ],
    "school": [
        (
            "Why is your school private information?",
            "Your school tells strangers where you spend part of your day. That is why it is safer not to share it online."
        )
    ],
    "name": [
        (
            "Why should you be careful with your full real name online?",
            "A full real name can connect many pieces of information about you. Children should use only safe nicknames when grown-ups say it is okay."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "profile",
    "solicit",
    "privacy",
    "tell_adult",
    "block",
    "report",
    "address",
    "school",
    "name",
]


CURATED = [
    StoryParams(
        platform="drawing_club",
        ask="real_name",
        response="tell_helper",
        fix="private_nickname",
        child_name="Lina",
        child_type="girl",
        helper_name="Maya",
        helper_type="sister",
        parent_type="mother",
        trait="careful",
        relation="siblings",
        child_age=8,
        helper_age=11,
        delay=0,
    ),
    StoryParams(
        platform="pet_board",
        ask="school",
        response="report_then_tell",
        fix="family_check",
        child_name="Owen",
        child_type="boy",
        helper_name="Dad",
        helper_type="father",
        parent_type="father",
        trait="curious",
        relation="family",
        child_age=8,
        helper_age=38,
        delay=0,
    ),
    StoryParams(
        platform="book_corner",
        ask="address",
        response="delete_and_hide",
        fix="friends_only",
        child_name="Mia",
        child_type="girl",
        helper_name="Nina",
        helper_type="sister",
        parent_type="mother",
        trait="chatty",
        relation="siblings",
        child_age=9,
        helper_age=10,
        delay=1,
    ),
    StoryParams(
        platform="drawing_club",
        ask="address",
        response="report_then_tell",
        fix="family_check",
        child_name="Leo",
        child_type="boy",
        helper_name="Mom",
        helper_type="mother",
        parent_type="mother",
        trait="thoughtful",
        relation="family",
        child_age=7,
        helper_age=34,
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for platform_id, platform in PLATFORMS.items():
        for ask_id, ask in ASKS.items():
            if hazard_at_risk(platform, ask):
                combos.append((platform_id, ask_id))
    return combos


def explain_rejection(platform: Platform, ask: Ask) -> str:
    if "profile" not in platform.tags:
        return "(No story: this platform has no public profile, so the stranger has no opening.)"
    if ask.sensitivity < 1:
        return "(No story: the message asks for nothing private, so there is no safety lesson.)"
    return "(No story: this combination has no clear privacy hazard.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_ask_first(params.relation, params.child_age, params.helper_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], ASKS[params.ask], params.delay) else "bad"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    platform = f["platform"]
    ask = f["ask"]
    outcome = f["outcome"]
    if outcome == "bad":
        return [
            f'Write a slice-of-life story for a young child that includes the words "solicit" and "profile".',
            f"Tell a gentle cautionary story where {child.id} gets a flattering message on {platform.label}, answers too quickly, and has to learn why {ask.detail.lower()}.",
            "Write a homey story with a bad ending for the account, but a safe lesson for the child and family.",
        ]
    return [
        f'Write a slice-of-life story for a young child that includes the words "solicit" and "profile".',
        f"Tell a story where {child.id} is using {platform.label}, a stranger tries to solicit private information, and a helper turns the moment into a lesson.",
        "Write a gentle internet-safety story with a happy ending and a clear lesson learned.",
    ]


def pair_noun(relation: str, child: Entity, helper: Entity) -> str:
    if relation == "siblings":
        if child.type == "girl" and helper.type in {"sister", "girl"}:
            return "two sisters"
        if child.type == "boy" and helper.type in {"brother", "boy"}:
            return "two brothers"
        return "a brother and a sister"
    return "a child and a trusted family helper"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    platform = f["platform"]
    ask = f["ask"]
    response = f["response"]
    fix = f["fix"]
    pair = pair_noun(f["relation"], child, helper)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}: {child.id}, who was using a tablet at home, and {helper.id}, who helped when an unsafe message appeared."
        ),
        (
            f"What was {child.id} doing at the start?",
            f"{child.id} was sharing {platform.noun} on {platform.label} and had a small online profile. The evening felt ordinary and calm before the strange message arrived."
        ),
        (
            "Why was the message a problem?",
            f"The stranger did not just say hello. The message tried to solicit private information by asking about {ask.id.replace('_', ' ')}, and that could give away too much about a child."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How did {child.id} stay safe?",
                f"{child.id} paused and asked {helper.id} before answering anything. That gave the helper time to block the stranger and make the profile safer before any private detail was shared."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily. {child.id} kept using the app in a safer way, and the new profile rules helped turn the scary moment into a lesson learned."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What did {helper.id} do after {child.id} replied?",
                f"{helper.id} {response.qa_text}. Then {helper.pronoun()} fixed the profile settings so the mistake would not keep growing into a bigger problem."
            )
        )
        qa.append(
            (
                f"What lesson did {child.id} learn?",
                f"{child.id} learned that praise from a stranger is not the same as trust. If a message asks for private facts, the safe choice is to stop and tell a grown-up."
            )
        )
    else:
        qa.append(
            (
                "Why was the ending sad?",
                f"The child was safe, but the account had to be closed for a while. That happened because {ask.danger}, so the family could not simply keep the old profile as it was."
            )
        )
        qa.append(
            (
                f"What lesson did {child.id} learn by the end?",
                f"{child.id} learned that small private details can become big clues in the wrong hands. The loss of the account made the lesson feel real, even though home was still safe."
            )
        )
    qa.append(
        (
            "What changed by the end of the story?",
            f"By the end, the family understood the profile needed stronger privacy. {fix.ending}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"profile", "solicit", "privacy"} | set(f["ask"].tags) | set(f["response"].tags) | set(f["fix"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, A) :- profile_platform(P), sensitive(A).
valid(P, A) :- platform(P), ask(A), hazard(P, A).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

helper_older :- relation(siblings), helper_age(HA), child_age(CA), HA > CA.
authority(C + B) :- init_caution(C), helper_older, older_bonus(B).
averted :- helper_older, authority(A), ask_first_threshold(T), A > T.

severity(S + D) :- chosen_ask(A), sensitivity(A, S), delay(D).
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(bad) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for platform_id, platform in PLATFORMS.items():
        lines.append(asp.fact("platform", platform_id))
        if "profile" in platform.tags:
            lines.append(asp.fact("profile_platform", platform_id))
    for ask_id, ask in ASKS.items():
        lines.append(asp.fact("ask", ask_id))
        lines.append(asp.fact("sensitivity", ask_id, ask.sensitivity))
        if ask.sensitivity >= 1:
            lines.append(asp.fact("sensitive", ask_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("older_bonus", 4))
    lines.append(asp.fact("ask_first_threshold", 6))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_ask", params.ask),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("child_age", params.child_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child profile, a stranger's message, and an internet-safety lesson."
    )
    ap.add_argument("--platform", choices=PLATFORMS)
    ap.add_argument("--ask", choices=ASKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--fix", choices=PRIVACY_FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the risky chat goes on before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible platform/ask pairs and sensible responses")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    child_type = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    return name, child_type


def _pick_helper(rng: random.Random, relation: str, parent_type: str) -> tuple[str, str, int]:
    if relation == "siblings":
        helper_type = rng.choice(["sister", "brother"])
        names = [n for n in HELPER_NAMES if n not in {"Mom", "Dad"}]
        return rng.choice(names), helper_type, rng.randint(9, 13)
    helper_type = parent_type
    helper_name = "Mom" if parent_type == "mother" else "Dad"
    return helper_name, helper_type, rng.randint(30, 42)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.platform and args.ask:
        if not hazard_at_risk(PLATFORMS[args.platform], ASKS[args.ask]):
            raise StoryError(explain_rejection(PLATFORMS[args.platform], ASKS[args.ask]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.platform is None or combo[0] == args.platform)
        and (args.ask is None or combo[1] == args.ask)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    platform_id, ask_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    fix_id = args.fix or rng.choice(sorted(PRIVACY_FIXES))
    child_name, child_type = _pick_child(rng)
    relation = rng.choice(["siblings", "family"])
    parent_type = args.parent or rng.choice(["mother", "father"])
    helper_name, helper_type, helper_age = _pick_helper(rng, relation, parent_type)
    child_age = rng.randint(7, 9)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)

    return StoryParams(
        platform=platform_id,
        ask=ask_id,
        response=response_id,
        fix=fix_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent_type=parent_type,
        trait=trait,
        relation=relation,
        child_age=child_age,
        helper_age=max(helper_age, child_age + 1) if relation == "siblings" and helper_age <= child_age else helper_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        platform = PLATFORMS[params.platform]
        ask = ASKS[params.ask]
        response = RESPONSES[params.response]
        fix = PRIVACY_FIXES[params.fix]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter choice: {exc.args[0]})") from exc
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(platform, ask):
        raise StoryError(explain_rejection(platform, ask))

    world = tell(
        platform,
        ask,
        response,
        fix,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        parent_type=params.parent_type,
        trait=params.trait,
        relation=params.relation,
        child_age=params.child_age,
        helper_age=params.helper_age,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py_valid - asp_valid))
        print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [(p, asp_outcome(p), outcome_of(p)) for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for p, ao, po in mismatches[:5]:
            print(f"  {p} -> asp={ao} python={po}")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(f"{len(combos)} compatible (platform, ask) combos:\n")
        for platform_id, ask_id in combos:
            print(f"  {platform_id:14} {ask_id}")
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
            header = f"### {p.child_name}: {p.platform} / {p.ask} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
