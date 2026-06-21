#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py
==============================================================

A small story world about two children at a retreat, a friendship rhyme that
goes wobbly, and a helper who turns the day around. The prose aims for a gentle,
rhyming-story feel: concrete images, paired sounds, and a clear beginning,
middle turn, and ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py --place pine_lodge --challenge shy_voice --help duet
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py --help hush_alone
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py --trace
    python storyworlds/worlds/gpt-5.4/retreat_friendship_rhyming_story.py --verify
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
class Place:
    id: str
    retreat_name: str
    spot: str
    open_a: str
    open_b: str
    nook: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    need: str
    severity: int
    wobble_line: str
    why_line: str
    comfort_line: str
    meter_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpMove:
    id: str
    label: str
    sense: int
    power: int
    supports: set[str] = field(default_factory=set)
    offer_line: str = ""
    action_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    challenge: str
    help: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    friend_trait: str
    patience: int = 2
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_step_back(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["worry"] < THRESHOLD:
        return []
    sig = ("step_back", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["steps_back"] += 1
    hero.memes["joy"] -= 0.5
    return ["__step_back__"]


def _r_comfort(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if friend.memes["kindness"] < THRESHOLD or hero.memes["courage"] < THRESHOLD:
        return []
    sig = ("comfort", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return ["__comfort__"]


CAUSAL_RULES = [
    Rule(name="step_back", tag="emotional", apply=_r_step_back),
    Rule(name="comfort", tag="emotional", apply=_r_comfort),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(s for s in made if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


PLACES = {
    "pine_lodge": Place(
        id="pine_lodge",
        retreat_name="Pinecone Retreat",
        spot="the pine lodge porch",
        open_a="At Pinecone Retreat, the morning smelled sweet.",
        open_b="The porch boards shone warm beneath small dancing feet.",
        nook="a bench by the fern wall",
        tags={"retreat", "porch"},
    ),
    "lakeside_lawn": Place(
        id="lakeside_lawn",
        retreat_name="Lakeside Retreat",
        spot="the lakeside lawn",
        open_a="At Lakeside Retreat, the blue water flashed bright.",
        open_b="The grass bowed and glittered in clean silver light.",
        nook="a quiet blanket near the reeds",
        tags={"retreat", "lake"},
    ),
    "apple_yard": Place(
        id="apple_yard",
        retreat_name="Apple Blossom Retreat",
        spot="the apple yard",
        open_a="At Apple Blossom Retreat, red petals curled light.",
        open_b="They twirled in the breeze like kites taking flight.",
        nook="a little stool under the apple tree",
        tags={"retreat", "orchard"},
    ),
}

CHALLENGES = {
    "shy_voice": Challenge(
        id="shy_voice",
        label="a shy voice",
        need="steady courage",
        severity=2,
        wobble_line="When it was time to say the rhyme, the first small words came out thin and shy.",
        why_line="The big circle felt larger than the hero had expected, and the sound seemed to float away.",
        comfort_line="A warm voice beside the hero would make the rhyme feel smaller, safer, and easier to say.",
        meter_key="voice_steady",
        tags={"shy", "voice"},
    ),
    "lost_beat": Challenge(
        id="lost_beat",
        label="a lost beat",
        need="steady counting",
        severity=1,
        wobble_line="When the clapping began, the hero rushed ahead and the rhyme lost its neat little beat.",
        why_line="Fast hands and eager feet tangled the pattern, so the words no longer landed together.",
        comfort_line="A patient friend could slow the pattern down and help the rhyme find its feet again.",
        meter_key="beat_steady",
        tags={"rhythm", "clap"},
    ),
    "wind_cards": Challenge(
        id="wind_cards",
        label="flying rhyme cards",
        need="held pages",
        severity=2,
        wobble_line="Just then a cheeky breeze skipped by, and the rhyme cards fluttered up like white birds.",
        why_line="Without the word cards, the hero could not remember the last line that made the rhyme complete.",
        comfort_line="If someone held the cards still, the brave little poem could stay in place.",
        meter_key="cards_secure",
        tags={"wind", "cards"},
    ),
}

HELPS = {
    "duet": HelpMove(
        id="duet",
        label="a shoulder-to-shoulder duet",
        sense=3,
        power=3,
        supports={"shy_voice"},
        offer_line='"Then say it with me," the friend whispered. "Two soft voices can still sound bright."',
        action_line="They stood shoulder to shoulder and let each line travel out together, light as a kite.",
        qa_line="stood beside the hero and turned the rhyme into a duet",
        tags={"duet", "friendship"},
    ),
    "clap_count": HelpMove(
        id="clap_count",
        label="a slow clap count",
        sense=3,
        power=2,
        supports={"lost_beat"},
        offer_line='"Let us count it slow," the friend said. "One clap, two clap, then the line can go."',
        action_line="The friend tapped the pattern gently, and the rhyme found its feet one careful beat at a time.",
        qa_line="counted the claps slowly so the rhyme could find its beat again",
        tags={"clap", "counting"},
    ),
    "ribbon_clip": HelpMove(
        id="ribbon_clip",
        label="a ribbon clip",
        sense=3,
        power=3,
        supports={"wind_cards"},
        offer_line='"I have a ribbon clip," the friend said. "We can pin the cards and keep the words from sailing away."',
        action_line="The friend clipped the fluttering cards to the stand, and the last brave line stayed where it belonged.",
        qa_line="used a ribbon clip to hold the rhyme cards still",
        tags={"clip", "wind"},
    ),
    "hush_alone": HelpMove(
        id="hush_alone",
        label="telling the hero to hide alone",
        sense=1,
        power=1,
        supports=set(),
        offer_line='"Maybe just hide behind the chair," the friend muttered.',
        action_line="The idea only made the worry feel bigger.",
        qa_line="told the hero to hide alone",
        tags={"unhelpful"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Lucy", "Ella", "Maya", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Max", "Sam", "Theo", "Noah", "Eli"]
TRAITS = ["patient", "gentle", "sunny", "thoughtful", "steady", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for challenge_id in CHALLENGES:
            for help_id, move in HELPS.items():
                if move.sense >= SENSE_MIN and challenge_id in move.supports:
                    combos.append((place_id, challenge_id, help_id))
    return combos


def support_strength(challenge: Challenge, move: HelpMove, patience: int) -> int:
    bonus = 1 if patience >= 2 else 0
    return move.power + bonus


def outcome_of(params: StoryParams) -> str:
    challenge = CHALLENGES[params.challenge]
    move = HELPS[params.help]
    if params.challenge not in move.supports:
        return "stuck"
    return "shared" if support_strength(challenge, move, params.patience) >= challenge.severity + 1 else "private"


def explain_rejection(challenge: Challenge, move: HelpMove) -> str:
    if move.sense < SENSE_MIN:
        return (
            f"(Refusing help '{move.id}': it scores too low on common sense "
            f"(sense={move.sense} < {SENSE_MIN}). A friendship story should offer "
            f"real help, not send a child away alone.)"
        )
    return (
        f"(No story: {move.label} does not solve {challenge.label}. "
        f"The help must match the exact wobble in the rhyme.)"
    )


def introduce(world: World, place: Place, hero: Entity, friend: Entity, parent: Entity) -> None:
    world.say(place.open_a)
    world.say(place.open_b)
    world.say(
        f"{hero.id} and {friend.id} wore paper leaf badges at {place.retreat_name}, "
        f"and {hero.id}'s {parent.label_word} smiled nearby."
    )
    world.say(
        f'The two friends had made a friendship rhyme for the welcome circle. '
        f'"We will say it together when the bell rings," said {friend.id}.'
    )


def build_hope(world: World, place: Place, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"They practiced at {place.spot}, tapping shoes, trading grins, and making small bright lines that nearly chimed."
    )
    world.say(
        f'{hero.id} held the little rhyme close and said, "I want the whole retreat to hear our friendship song."'
    )


def trouble(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["worry"] += 1
    hero.meters[challenge.meter_key] = 0.0
    propagate(world, narrate=False)
    world.say(challenge.wobble_line)
    world.say(challenge.why_line)


def friend_notices(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    friend.memes["kindness"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} saw {hero.id} pause and did not laugh, rush, or tease."
    )
    world.say(challenge.comfort_line)


def help_attempt(world: World, place: Place, hero: Entity, friend: Entity, move: HelpMove, patience: int) -> None:
    friend.memes["patience"] = float(patience)
    hero.memes["courage"] += 1
    world.say(move.offer_line)
    if patience <= 1:
        world.say(
            f"{friend.id} tried to help quickly, but the hurry left the air a little fluttery."
        )
    else:
        world.say(
            f"{friend.id} stayed close at {place.nook}, calm as a lamp, and gave the moment room to breathe."
        )
    world.say(move.action_line)
    propagate(world, narrate=False)


def present_shared(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["voice_steady"] += 1
    hero.meters["beat_steady"] += 1
    hero.meters["cards_secure"] += 1
    hero.memes["joy"] += 1
    hero.memes["courage"] += 1
    friend.memes["joy"] += 1
    world.say(
        "Soon the bell chimed clear, the children drew near, and the pair stepped into the ring."
    )
    world.say(
        f"{hero.id} and {friend.id} shared the rhyme with bright, even words. The circle clapped along, and the ending line landed with a happy sing."
    )
    world.say(
        "What had started with a wobble finished warm and sweet: two friends in step at retreat."
    )


def present_private(world: World, place: Place, hero: Entity, friend: Entity) -> None:
    hero.meters["voice_steady"] += 1
    hero.memes["courage"] += 1
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"The big circle still felt a little too wide, so they took their rhyme to {place.nook} instead."
    )
    world.say(
        f"There, {hero.id} said every line more bravely, and {friend.id} answered with the last line in a voice soft and true."
    )
    world.say(
        "Only a few birds heard it, but that was enough for the day. The rhyme was smaller, yet the friendship grew."
    )


def parent_closes(world: World, parent: Entity, hero: Entity, friend: Entity, outcome: str) -> None:
    if outcome == "shared":
        world.say(
            f'{parent.label_word.capitalize()} clapped and said, "That is what friendship can do. A kind helper makes a hard thing easier for you."'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} came by with a warm smile and said, "A good friend does not push. A good friend stays."'
        )
    world.say(
        f"{hero.id} squeezed {friend.id}'s hand, and both children knew the best line in the rhyme was not on the card at all."
    )


def tell(
    place: Place,
    challenge: Challenge,
    move: HelpMove,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    friend_trait: str,
    patience: int,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=[friend_trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))

    hero.attrs["name"] = hero_name
    friend.attrs["name"] = friend_name
    parent.attrs["name"] = parent.label_word

    introduce(world, place, hero, friend, parent)
    build_hope(world, place, hero, friend)

    world.para()
    trouble(world, hero, challenge)
    friend_notices(world, hero, friend, challenge)

    world.para()
    help_attempt(world, place, hero, friend, move, patience)

    outcome = outcome_of(
        StoryParams(
            place=place.id,
            challenge=challenge.id,
            help=move.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            parent=parent_type,
            friend_trait=friend_trait,
            patience=patience,
        )
    )
    if outcome == "shared":
        present_shared(world, hero, friend)
    else:
        present_private(world, place, hero, friend)

    world.para()
    parent_closes(world, parent, hero, friend, outcome)

    world.facts.update(
        place=place,
        challenge=challenge,
        help=move,
        hero=hero,
        friend=friend,
        parent=parent,
        hero_name=hero_name,
        friend_name=friend_name,
        outcome=outcome,
        patience=patience,
        retreat_name=place.retreat_name,
        friend_trait=friend_trait,
        problem_started=hero.memes["worry"] >= THRESHOLD,
        stepped_back=hero.meters["steps_back"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "friendship": [
        (
            "What does a good friend do when you feel stuck?",
            "A good friend stays kind and helps in a way that matches the problem. They do not tease or hurry you when you are worried.",
        )
    ],
    "retreat": [
        (
            "What is a retreat?",
            "A retreat is a special time away from ordinary routines, often for rest, learning, or being together. Children might visit a quiet camp or garden and do activities there.",
        )
    ],
    "duet": [
        (
            "What is a duet?",
            "A duet is when two people say or sing something together. Sharing the sound can make a shy job feel safer.",
        )
    ],
    "clap": [
        (
            "Why does clapping help with a rhyme?",
            "Clapping can mark the beat, so the words land in order. A steady beat helps your mouth and ears work together.",
        )
    ],
    "clip": [
        (
            "What does a clip do for loose papers?",
            "A clip holds papers in place so they do not slide or blow away. That makes it easier to keep reading the right words.",
        )
    ],
    "shy": [
        (
            "What does it mean to feel shy?",
            "Feeling shy means you want to speak or join in, but your body feels small or nervous. Kind company can make that feeling softer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["retreat", "friendship", "shy", "duet", "clap", "clip"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    challenge = f["challenge"]
    move = f["help"]
    retreat_name = f["retreat_name"]
    outcome = f["outcome"]
    if outcome == "shared":
        ending = "ends with the two friends sharing their rhyme with the whole group"
    else:
        ending = "ends with the two friends sharing their rhyme quietly together"
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the word "retreat" and centers Friendship.',
        f"Tell a gentle story set at {retreat_name} where {hero_name} hits {challenge.label} and {friend_name} helps with {move.label}.",
        f"Write a child-facing rhyming story about friendship at a retreat that {ending}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero_name = f["hero_name"]
    friend_name = f["friend_name"]
    retreat_name = f["retreat_name"]
    challenge = f["challenge"]
    move = f["help"]
    parent = f["parent"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {friend_name}, two friends at {retreat_name}. {hero_name}'s {parent.label_word} is nearby too.",
        ),
        (
            "What did the children want to do at the retreat?",
            f"They wanted to share a friendship rhyme in the welcome circle. The retreat gave them a place to practice and perform together.",
        ),
        (
            f"What problem did {hero_name} have?",
            f"{hero_name} ran into {challenge.label}. That made the rhyme wobble just when it was time to say it.",
        ),
        (
            f"How did {friend_name} help?",
            f"{friend_name} {move.qa_line}. The help matched the problem instead of making {hero_name} feel lonelier.",
        ),
    ]
    if outcome == "shared":
        qa.append(
            (
                "How did the story end?",
                f"It ended with {hero_name} and {friend_name} sharing the rhyme with the whole group. Their friendship turned a worried moment into a bright one.",
            )
        )
        qa.append(
            (
                f"Why was {friend_name}'s help important?",
                f"The problem started because {challenge.why_line[0].lower() + challenge.why_line[1:]} {friend_name}'s help gave the rhyme the exact support it needed, so the children could finish together.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with the two friends saying the rhyme together in a smaller spot. They did not need a big crowd to prove the friendship was real.",
            )
        )
        qa.append(
            (
                f"Why did they move to a quieter place?",
                f"The big circle still felt too hard after the first try. Moving to a smaller place let {hero_name} be brave without feeling pushed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"friendship", "retreat"}
    challenge = world.facts["challenge"]
    move = world.facts["help"]
    if "shy" in challenge.tags or "voice" in challenge.tags:
        tags.add("shy")
    if move.id == "duet":
        tags.add("duet")
    if move.id == "clap_count":
        tags.add("clap")
    if move.id == "ribbon_clip":
        tags.add("clip")
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
    for key, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {key:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(H) :- help(H), sense(H, S), sense_min(M), S >= M.
matches(C, H) :- support(H, C).
valid(P, C, H) :- place(P), challenge(C), help(H), sensible(H), matches(C, H).

bonus(1) :- patience(PA), PA >= 2.
bonus(0) :- patience(PA), PA < 2.
strength(V) :- chosen_help(H), power(H, P), bonus(B), V = P + B.
need(N) :- chosen_challenge(C), severity(C, N).

outcome(shared)  :- chosen_help(H), chosen_challenge(C), matches(C, H), strength(V), need(N), V >= N + 1.
outcome(private) :- chosen_help(H), chosen_challenge(C), matches(C, H), strength(V), need(N), V < N + 1.
outcome(stuck)   :- chosen_help(H), chosen_challenge(C), not matches(C, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("severity", cid, challenge.severity))
    for hid, move in HELPS.items():
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("sense", hid, move.sense))
        lines.append(asp.fact("power", hid, move.power))
        for cid in sorted(move.supports):
            lines.append(asp.fact("support", hid, cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_challenge", params.challenge),
            asp.fact("chosen_help", params.help),
            asp.fact("patience", params.patience),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="pine_lodge",
        challenge="shy_voice",
        help="duet",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        friend_trait="patient",
        patience=3,
    ),
    StoryParams(
        place="lakeside_lawn",
        challenge="lost_beat",
        help="clap_count",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        parent="father",
        friend_trait="steady",
        patience=2,
    ),
    StoryParams(
        place="apple_yard",
        challenge="wind_cards",
        help="ribbon_clip",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        friend_trait="thoughtful",
        patience=3,
    ),
    StoryParams(
        place="pine_lodge",
        challenge="shy_voice",
        help="duet",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Lucy",
        friend_gender="girl",
        parent="father",
        friend_trait="gentle",
        patience=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: friendship at a retreat, a wobbling rhyme, and help that must fit the problem."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--help", choices=HELPS, dest="help_move")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--patience", type=int, choices=[1, 2, 3])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [name for name in pool if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    help_id = args.help_move
    if args.challenge and help_id:
        challenge = CHALLENGES[args.challenge]
        move = HELPS[help_id]
        if move.sense < SENSE_MIN or args.challenge not in move.supports:
            raise StoryError(explain_rejection(challenge, move))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.challenge is None or combo[1] == args.challenge)
        and (help_id is None or combo[2] == help_id)
    ]
    if not combos:
        if args.challenge and help_id:
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], HELPS[help_id]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, challenge_id, chosen_help = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    friend_trait = rng.choice(TRAITS)
    patience = args.patience if args.patience is not None else rng.choice([1, 2, 3])

    return StoryParams(
        place=place_id,
        challenge=challenge_id,
        help=chosen_help,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent_type,
        friend_trait=friend_trait,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    if params.help not in HELPS:
        raise StoryError(f"(Unknown help move: {params.help})")

    challenge = CHALLENGES[params.challenge]
    move = HELPS[params.help]
    if move.sense < SENSE_MIN or params.challenge not in move.supports:
        raise StoryError(explain_rejection(challenge, move))

    world = tell(
        place=PLACES[params.place],
        challenge=challenge,
        move=move,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        friend_trait=params.friend_trait,
        patience=params.patience,
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
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    default_args = parser.parse_args([])
    for seed in range(30):
        try:
            p = resolve_params(default_args, random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    smoke = cases[:3]
    try:
        for params in smoke:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, challenge, help) combos:\n")
        for place_id, challenge_id, help_id in combos:
            print(f"  {place_id:13} {challenge_id:11} {help_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            sample = generate(params)
            samples.append(sample)
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.challenge} with {p.help} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
