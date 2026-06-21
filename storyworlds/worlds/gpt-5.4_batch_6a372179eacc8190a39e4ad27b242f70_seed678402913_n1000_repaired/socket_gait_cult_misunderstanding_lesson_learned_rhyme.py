#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py
====================================================================================

A small adventure storyworld about two children following a rhyming clue in an
old building. A misunderstanding grows from an antique sign with the word
"cult" on it, and a second misunderstanding makes one child think a metal item
might help with a dark room and a socket. Someone stops the mistake in time, a
grown-up explains the old sign and the safety rule, and the adventure ends with
the children moving forward with a steadier gait and a better idea.

The world model is deliberately narrow:

* A site provides an old sign, a dark room, a rhyming clue, and a small prize.
* An attempt object must be both plausible as a mistaken "light-fixing" idea and
  electrically risky; otherwise the story is rejected.
* A helper notices first -- either the other child or the guide -- and this
  changes the turn of the prose while keeping the lesson intact.

Run it
------
    python storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py
    python storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py --site lighthouse --attempt brass_key
    python storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py --attempt leaf
    python storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/socket_gait_cult_misunderstanding_lesson_learned_rhyme.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Site:
    id: str
    label: str = ""
    opening: str = ""
    sign_name: str = ""
    clue_place: str = ""
    dark_place: str = ""
    prize: str = ""
    prize_phrase: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Attempt:
    id: str
    label: str = ""
    phrase: str = ""
    conductive: bool = False
    plausible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeLight:
    id: str
    label: str = ""
    phrase: str = ""
    shine: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_socket_risk(world: World) -> list[str]:
    child = world.get("hero")
    socket = world.get("socket")
    tool = world.get("attempt")
    if socket.meters["powered"] < THRESHOLD:
        return []
    if tool.meters["near_socket"] < THRESHOLD:
        return []
    sig = ("socket_risk", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    child.memes["alarm"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["alarm"] += 1
    return ["__risk__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="socket_risk", tag="physical", apply=_r_socket_risk),
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


SITES = {
    "lighthouse": Site(
        id="lighthouse",
        label="the old lighthouse",
        opening="windy stairs and windows full of sea light",
        sign_name="Tidewatch Cult",
        clue_place="the keeper's map box",
        dark_place="the round lamp room at the top",
        prize="shell compass",
        prize_phrase="a tiny shell compass tied with blue string",
        ending_image="the sea flashed silver below them",
        tags={"adventure", "tower"},
    ),
    "clocktower": Site(
        id="clocktower",
        label="the old clock tower",
        opening="creaky stairs and giant clock faces that glowed like moons",
        sign_name="Bellkeepers Cult",
        clue_place="the cabinet below the chime ropes",
        dark_place="the small gear room behind the clock face",
        prize="brass star badge",
        prize_phrase="a brass star badge wrapped in soft felt",
        ending_image="the town roofs looked like toy blocks below",
        tags={"adventure", "tower"},
    ),
    "greenhouse": Site(
        id="greenhouse",
        label="the glasshouse at the edge of the garden",
        opening="misty panes and leafy paths that felt like a jungle",
        sign_name="Rose Cult",
        clue_place="the potting bench drawer",
        dark_place="the fern room behind the warm pipes",
        prize="seed packet",
        prize_phrase="a little paper packet of moonflower seeds",
        ending_image="the glass walls shone with evening gold",
        tags={"adventure", "garden"},
    ),
}

ATTEMPTS = {
    "brass_key": Attempt(
        id="brass_key",
        label="brass key",
        phrase="a small brass key",
        conductive=True,
        plausible=True,
        tags={"metal", "socket"},
    ),
    "silver_coin": Attempt(
        id="silver_coin",
        label="silver coin",
        phrase="a smooth silver coin",
        conductive=True,
        plausible=True,
        tags={"metal", "socket"},
    ),
    "leaf": Attempt(
        id="leaf",
        label="leaf",
        phrase="a dry curled leaf",
        conductive=False,
        plausible=False,
        tags={"leaf"},
    ),
    "feather": Attempt(
        id="feather",
        label="feather",
        phrase="a soft white feather",
        conductive=False,
        plausible=False,
        tags={"feather"},
    ),
}

SAFE_LIGHTS = {
    "flashlight": SafeLight(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        shine="clicked on bright as a little moon",
        tags={"flashlight"},
    ),
    "lantern": SafeLight(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        shine="glowed warm and steady",
        tags={"lantern"},
    ),
    "headlamp": SafeLight(
        id="headlamp",
        label="head-lamp",
        phrase="a head-lamp",
        shine="spilled a clean circle of light ahead",
        tags={"headlamp"},
    ),
}

HELPERS = {"friend", "guide"}

GIRL_NAMES = ["Lina", "Mira", "Tess", "Nora", "Poppy", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Jules", "Ben", "Theo", "Milo", "Finn", "Sam", "Leo", "Arlo"]
GUIDE_NAMES = ["Aunt May", "Mr. Hale", "Grandpa Reed", "Ms. Wren"]


@dataclass
class StoryParams:
    site: str
    attempt: str
    safe_light: str
    helper: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


def attempt_is_reasonable(attempt: Attempt) -> bool:
    return attempt.conductive and attempt.plausible


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for site in sorted(SITES):
        for attempt_id, attempt in ATTEMPTS.items():
            if not attempt_is_reasonable(attempt):
                continue
            for light in sorted(SAFE_LIGHTS):
                for helper in sorted(HELPERS):
                    combos.append((site, attempt_id, light, helper))
    return combos


def explain_attempt(attempt: Attempt) -> str:
    if not attempt.plausible:
        return (
            f"(No story: {attempt.phrase} is not a believable way for a child to try "
            f"to 'fix' a light, so the misunderstanding falls flat.)"
        )
    if not attempt.conductive:
        return (
            f"(No story: {attempt.phrase} is not the kind of object that makes the "
            f"socket mistake feel dangerous enough to need the lesson.)"
        )
    return "(No story: that attempt does not fit this world.)"


def predict_risk(world: World, attempt_id: str) -> dict:
    sim = world.copy()
    sim.get(attempt_id).meters["near_socket"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "alarm": sim.get("hero").memes["alarm"],
    }


def introduce(world: World, hero: Entity, friend: Entity, guide: Entity, site: Site) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On an adventure afternoon, {hero.id} and {friend.id} climbed into {site.label} "
        f"with {guide.id}. Inside were {site.opening}."
    )
    world.say(
        f'{guide.id} smiled and said, "There is one hidden prize here, and the clue is tucked in {site.clue_place}."'
    )


def find_clue(world: World, hero: Entity, friend: Entity, site: Site) -> None:
    world.say(
        f"They found a folded card and read the rhyme together: "
        f'"Mind your gait, do not rush late; ask for light to set things right."'
    )
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.facts["rhyme"] = "Mind your gait, do not rush late; ask for light to set things right."


def see_sign(world: World, hero: Entity, friend: Entity, site: Site) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"At the next landing they passed an old painted sign that said {site.sign_name}. "
        f"{hero.id} stared at the word cult and slowed to a tiny tiptoe gait."
    )
    world.say(
        f'"A cult sounds secret and scary," {hero.id} whispered. "{friend.id}, do you think someone is hiding in there?"'
    )


def friend_reacts(world: World, friend: Entity) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} swallowed and listened to the creaks around them, but only dust and wind answered.'
    )


def enter_dark_room(world: World, hero: Entity, site: Site) -> None:
    world.say(
        f"They reached {site.dark_place}, and the room looked dim enough to swallow the corners. "
        f"On one wall was an empty socket beside a dead lamp."
    )
    hero.memes["need_light"] += 1
    world.get("room").meters["dark"] += 1
    world.get("socket").meters["powered"] += 1


def reach_toward_socket(world: World, hero: Entity, attempt: Attempt) -> None:
    world.get("attempt").meters["near_socket"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} looked at the rhyme again and held up {attempt.phrase}. '
        f'"Maybe ask for light means I should use this in the socket," {hero.pronoun()} said.'
    )


def stop_by_friend(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["brave"] += 1
    hero.memes["startled"] += 1
    world.say(
        f'"Stop!" cried {friend.id}, catching {hero.id}\'s wrist before {hero.pronoun()} got close. '
        f'"A socket is not for keys or coins. It can hurt you."'
    )


def stop_by_guide(world: World, hero: Entity, guide: Entity) -> None:
    guide.memes["care"] += 1
    hero.memes["startled"] += 1
    world.say(
        f'"Easy there," said {guide.id}, stepping in fast and gently lowering {hero.id}\'s hand. '
        f'"A socket is only for the right plug or bulb. Metal does not belong there."'
    )


def explain(world: World, hero: Entity, friend: Entity, guide: Entity, site: Site) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["understanding"] += 1
    friend.memes["relief"] += 1
    guide.memes["care"] += 1
    world.say(
        f'{guide.id} knelt beside the old sign and tapped the painted letters. '
        f'"Long ago, {site.sign_name} was just the name of a club of people who loved this place," {guide.pronoun()} explained.'
    )
    world.say(
        f'"So the cult word was not a monster clue at all," said {friend.id}. '
        f'"And the rhyme did not mean poke the socket. It meant ask a grown-up for safe light."'
    )


def use_safe_light(world: World, hero: Entity, friend: Entity, guide: Entity, light: SafeLight) -> None:
    world.get("room").meters["dark"] = 0.0
    world.get("room").meters["danger"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'{guide.id} took out {light.phrase} that {light.shine}. Warm light spread through the room at once.'
    )


def find_prize(world: World, hero: Entity, friend: Entity, site: Site) -> None:
    world.get("prize").meters["found"] += 1
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"Behind the dead lamp they found {site.prize_phrase}. "
        f"{hero.id} laughed, and {friend.id} held it up as if the whole adventure had been waiting for that moment."
    )


def lesson(world: World, hero: Entity, friend: Entity, guide: Entity) -> None:
    world.say(
        f'"Now I know two things," said {hero.id}. "Old words can fool me, and a socket is never a place for random metal things."'
    )
    world.say(
        f'{guide.id} nodded. "That is the brave lesson -- when you are unsure, ask first."'
    )
    world.say(
        f'{friend.id} grinned and sang the rhyme back with a happier swing: '
        f'"Mind your gait, do not rush late; ask for light to set things right."'
    )


def ending(world: World, hero: Entity, friend: Entity, site: Site) -> None:
    world.say(
        f"They walked back out with a bolder gait than before, and {site.ending_image}. "
        f"The adventure felt brighter because they understood it now."
    )


def tell(
    site: Site,
    attempt: Attempt,
    light: SafeLight,
    helper: str,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    guide_name: str,
    guide_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    hero.attrs["name"] = hero_name
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    friend.attrs["name"] = friend_name
    guide = world.add(Entity(id="guide", kind="character", type=guide_type, label=guide_name, role="guide"))
    world.add(Entity(id="room", type="room", label=site.dark_place))
    world.add(Entity(id="socket", type="socket", label="socket"))
    world.add(
        Entity(
            id="attempt",
            type="thing",
            label=attempt.label,
            phrase=attempt.phrase,
            tags=set(attempt.tags),
        )
    )
    world.add(Entity(id="prize", type="prize", label=site.prize, phrase=site.prize_phrase))
    world.facts["site"] = site
    world.facts["attempt_cfg"] = attempt
    world.facts["light_cfg"] = light
    world.facts["helper"] = helper

    introduce(world, hero, friend, guide, site)
    find_clue(world, hero, friend, site)

    world.para()
    see_sign(world, hero, friend, site)
    friend_reacts(world, friend)

    world.para()
    enter_dark_room(world, hero, site)
    risk = predict_risk(world, "attempt")
    world.facts["predicted_danger"] = risk["danger"]
    reach_toward_socket(world, hero, attempt)

    if helper == "friend":
        stop_by_friend(world, hero, friend)
    else:
        stop_by_guide(world, hero, guide)

    world.para()
    explain(world, hero, friend, guide, site)
    use_safe_light(world, hero, friend, guide, light)
    find_prize(world, hero, friend, site)

    world.para()
    lesson(world, hero, friend, guide)
    ending(world, hero, friend, site)

    world.facts.update(
        hero=hero,
        friend=friend,
        guide=guide,
        danger_seen=world.get("attempt").meters["near_socket"] >= THRESHOLD,
        prize_found=world.get("prize").meters["found"] >= THRESHOLD,
        site_id=site.id,
        attempt_id=attempt.id,
        light_id=light.id,
    )
    return world


KNOWLEDGE = {
    "socket": [
        (
            "What is a socket?",
            "A socket is the place where the right plug or bulb goes so electricity can be used safely. It is never for fingers, coins, or keys.",
        )
    ],
    "electricity": [
        (
            "Why should children not put metal in a socket?",
            "Metal can carry electricity, so putting it in a socket can give a dangerous shock. If a room is dark, the safe choice is to ask a grown-up for help.",
        )
    ],
    "cult_word": [
        (
            "Can old words sometimes mean something different than you expect?",
            "Yes. A word on an old sign can belong to another time, so it is smart to ask what it means before you get scared.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words with matching sounds, like late and gate. Rhymes can help people remember a rule or clue.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight safer than trying to fix a dark room yourself?",
            "A flashlight gives light without asking a child to touch wires or sockets. It solves the dark problem in a safe way.",
        )
    ],
    "lantern": [
        (
            "What does a camping lantern do?",
            "A camping lantern shines light around a whole space, so people can see clearly without poking at anything dangerous.",
        )
    ],
    "headlamp": [
        (
            "What is a head-lamp?",
            "A head-lamp is a small light you wear on your head. It helps you see while keeping your hands free.",
        )
    ],
}
KNOWLEDGE_ORDER = ["socket", "electricity", "cult_word", "rhyme", "flashlight", "lantern", "headlamp"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    site = world.facts["site"]
    attempt = world.facts["attempt_cfg"]
    light = world.facts["light_cfg"]
    return [
        (
            f'Write a short adventure story for a 3-to-5-year-old that includes the words '
            f'"socket", "gait", and "cult", and uses a rhyme to teach a safety lesson.'
        ),
        (
            f"Tell a gentle misunderstanding story where {hero.attrs['name']} and {friend.attrs['name']} explore "
            f"{site.label}, worry about an old sign with the word cult, and learn that {attempt.label} does not belong near a socket."
        ),
        (
            f"Write a child-facing adventure with a dark room, a mistaken idea, a calm explanation, and a happy ending with {light.phrase}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    guide = world.facts["guide"]
    site = world.facts["site"]
    attempt = world.facts["attempt_cfg"]
    light = world.facts["light_cfg"]
    helper = world.facts["helper"]
    hero_name = hero.attrs["name"]
    friend_name = friend.attrs["name"]
    guide_name = guide.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {friend_name}, two children on an adventure, and {guide_name}, who leads them through {site.label}.",
        ),
        (
            "What clue did they follow?",
            "They followed a rhyme that told them to mind their gait and ask for light. The rhyme mattered because it was supposed to slow them down and help them choose a safe idea.",
        ),
        (
            f"Why did {hero_name} start walking with a tiny tiptoe gait?",
            f"{hero_name} saw the old sign with the word cult and misunderstood it as something scary. That made {hero.pronoun('object')} move quietly and nervously instead of feeling excited.",
        ),
        (
            f"Why was reaching toward the socket a mistake?",
            f"{hero_name} thought the rhyme meant {hero.pronoun()} should use {attempt.phrase} to make light, but that was the wrong idea. A socket is dangerous for random metal things, so asking for help was the safe choice.",
        ),
    ]
    if helper == "friend":
        qa.append(
            (
                f"Who stopped {hero_name} first?",
                f"{friend_name} stopped {hero_name} first by catching {hero.pronoun('possessive')} wrist and warning {hero.pronoun('object')} about the socket. That quick warning interrupted the mistake before anyone got hurt.",
            )
        )
    else:
        qa.append(
            (
                f"Who stopped {hero_name} first?",
                f"{guide_name} stopped {hero_name} first and gently lowered {hero.pronoun('possessive')} hand. The guide knew the socket rule and turned the moment into a calm lesson.",
            )
        )
    qa.append(
        (
            "What did the word cult really mean in the story?",
            f"It was just part of the old club name {site.sign_name}, not a scary secret group. The children learned that old words can sound strange if you do not know the history around them.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"{guide_name} used {light.phrase}, the children found {site.prize_phrase}, and they walked out with a bolder gait. The ending shows that understanding and safe help made the adventure bright again.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"socket", "electricity", "cult_word", "rhyme", world.facts["light_id"]}
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        site="lighthouse",
        attempt="brass_key",
        safe_light="lantern",
        helper="friend",
        hero="Lina",
        hero_gender="girl",
        friend="Theo",
        friend_gender="boy",
        guide_name="Aunt May",
        guide_type="mother",
        seed=101,
    ),
    StoryParams(
        site="clocktower",
        attempt="silver_coin",
        safe_light="headlamp",
        helper="guide",
        hero="Milo",
        hero_gender="boy",
        friend="Zoe",
        friend_gender="girl",
        guide_name="Mr. Hale",
        guide_type="father",
        seed=102,
    ),
    StoryParams(
        site="greenhouse",
        attempt="brass_key",
        safe_light="flashlight",
        helper="friend",
        hero="Nora",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        guide_name="Ms. Wren",
        guide_type="mother",
        seed=103,
    ),
]


ASP_RULES = r"""
% Reasonableness gate: the mistaken object must be both plausible and risky.
risky_attempt(A) :- attempt(A), conductive(A), plausible(A).

valid(S, A, L, H) :- site(S), risky_attempt(A), light(L), helper(H).

% The immediate helper determines the stop outcome.
outcome(friend_stop) :- chosen_helper(friend).
outcome(guide_stop)  :- chosen_helper(guide).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site in sorted(SITES):
        lines.append(asp.fact("site", site))
    for aid, attempt in ATTEMPTS.items():
        lines.append(asp.fact("attempt", aid))
        if attempt.conductive:
            lines.append(asp.fact("conductive", aid))
        if attempt.plausible:
            lines.append(asp.fact("plausible", aid))
    for light in sorted(SAFE_LIGHTS):
        lines.append(asp.fact("light", light))
    for helper in sorted(HELPERS):
        lines.append(asp.fact("helper", helper))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_helper", params.helper)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "friend_stop" if params.helper == "friend" else "guide_stop"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print(f"MISMATCH in outcome for helper={case.helper}")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: rhyme, misunderstanding, socket safety, and a lesson learned."
    )
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--attempt", choices=sorted(ATTEMPTS))
    ap.add_argument("--safe-light", dest="safe_light", choices=sorted(SAFE_LIGHTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--guide-name", dest="guide_name")
    ap.add_argument("--guide-type", dest="guide_type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.attempt:
        attempt = ATTEMPTS[args.attempt]
        if not attempt_is_reasonable(attempt):
            raise StoryError(explain_attempt(attempt))

    combos = [
        combo
        for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.attempt is None or combo[1] == args.attempt)
        and (args.safe_light is None or combo[2] == args.safe_light)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site, attempt, safe_light, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or pick_name(rng, hero_gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend = args.friend or pick_name(rng, friend_gender, avoid=hero)
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    guide_type = args.guide_type or rng.choice(["mother", "father"])
    return StoryParams(
        site=site,
        attempt=attempt,
        safe_light=safe_light,
        helper=helper,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        guide_name=guide_name,
        guide_type=guide_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.attempt not in ATTEMPTS:
        raise StoryError(f"(Unknown attempt: {params.attempt})")
    if params.safe_light not in SAFE_LIGHTS:
        raise StoryError(f"(Unknown safe light: {params.safe_light})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    attempt = ATTEMPTS[params.attempt]
    if not attempt_is_reasonable(attempt):
        raise StoryError(explain_attempt(attempt))

    world = tell(
        site=SITES[params.site],
        attempt=attempt,
        light=SAFE_LIGHTS[params.safe_light],
        helper=params.helper,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (site, attempt, safe_light, helper) combos:\n")
        for site, attempt, light, helper in combos:
            print(f"  {site:11} {attempt:12} {light:10} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.site}: {p.attempt} / {p.safe_light} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
