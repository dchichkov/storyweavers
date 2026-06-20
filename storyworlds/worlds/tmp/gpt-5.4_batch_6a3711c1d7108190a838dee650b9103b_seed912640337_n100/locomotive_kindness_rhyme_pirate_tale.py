#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/locomotive_kindness_rhyme_pirate_tale.py
===================================================================

A small story world about pirate-play around a little locomotive, where a kind
child notices someone being left out and uses a gift plus a rhyme to help them
join the adventure.

The domain is deliberately narrow: a miniature locomotive is the children's
"pirate ship on rails", a shy or stuck child is at risk of missing the ride, and
the turn comes when kindness is made concrete through a shared object and a
simple rhyme. The ending image proves the change: the once-left-out child rides
along and helps the crew.

Run it
------
    python storyworlds/worlds/gpt-5.4/locomotive_kindness_rhyme_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/locomotive_kindness_rhyme_pirate_tale.py --obstacle no_token
    python storyworlds/worlds/gpt-5.4/locomotive_kindness_rhyme_pirate_tale.py --gift kerchief
    python storyworlds/worlds/gpt-5.4/locomotive_kindness_rhyme_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/locomotive_kindness_rhyme_pirate_tale.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class Locomotive:
    id: str
    label: str
    place: str
    paint: str
    whistle: str
    route: str
    tunnel: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    opening: str
    need_gift: str
    need_rhyme: str
    fear_word: str
    later_help: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    gives: str
    text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    label: str
    solves: str
    words: tuple[str, str]
    text: str
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


def _r_left_out(world: World) -> list[str]:
    out: list[str] = []
    newcomer = world.get("newcomer")
    if newcomer.meters["can_board"] >= THRESHOLD:
        return out
    if newcomer.meters["needs_help"] < THRESHOLD:
        return out
    sig = ("left_out", newcomer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    newcomer.memes["sad"] += 1
    out.append("__sad__")
    return out


def _r_ready_to_board(world: World) -> list[str]:
    out: list[str] = []
    newcomer = world.get("newcomer")
    if newcomer.meters["has_gift_help"] < THRESHOLD:
        return out
    if newcomer.meters["knows_rhyme"] < THRESHOLD:
        return out
    sig = ("ready", newcomer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    newcomer.meters["can_board"] += 1
    newcomer.memes["courage"] += 1
    newcomer.memes["belonging"] += 1
    out.append("__ready__")
    return out


def _r_joined_joy(world: World) -> list[str]:
    out: list[str] = []
    newcomer = world.get("newcomer")
    captain = world.get("captain")
    mate = world.get("mate")
    if newcomer.meters["boarded"] < THRESHOLD:
        return out
    sig = ("joy", newcomer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    newcomer.memes["joy"] += 1
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    out.append("__joined__")
    return out


CAUSAL_RULES = [
    Rule("left_out", "social", _r_left_out),
    Rule("ready_to_board", "social", _r_ready_to_board),
    Rule("joined_joy", "social", _r_joined_joy),
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


def gift_matches(obstacle: Obstacle, gift: Gift) -> bool:
    return obstacle.need_gift == gift.gives


def rhyme_matches(obstacle: Obstacle, rhyme: Rhyme) -> bool:
    return obstacle.need_rhyme == rhyme.solves


def valid_combo(obstacle: Obstacle, gift: Gift, rhyme: Rhyme) -> bool:
    return gift_matches(obstacle, gift) and rhyme_matches(obstacle, rhyme)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loco_id in LOCOMOTIVES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for gift_id, gift in GIFTS.items():
                for rhyme_id, rhyme in RHYMES.items():
                    if valid_combo(obstacle, gift, rhyme):
                        combos.append((loco_id, obstacle_id, gift_id, rhyme_id))
    return combos


def predict_join(world: World, obstacle: Obstacle, gift: Gift, rhyme: Rhyme) -> dict:
    sim = world.copy()
    newcomer = sim.get("newcomer")
    newcomer.meters["needs_help"] = 1
    if gift_matches(obstacle, gift):
        newcomer.meters["has_gift_help"] += 1
    if rhyme_matches(obstacle, rhyme):
        newcomer.meters["knows_rhyme"] += 1
    propagate(sim, narrate=False)
    return {
        "can_board": newcomer.meters["can_board"] >= THRESHOLD,
        "sad": newcomer.memes["sad"] >= THRESHOLD,
    }


def opening_scene(world: World, captain: Entity, mate: Entity, loco: Locomotive) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} found the little "
        f"{loco.paint} locomotive at {loco.place} and turned it into a pirate ship on rails."
    )
    world.say(
        f'The brass whistle gave a {loco.whistle} sound, the cars waited along {loco.route}, '
        f'and to the two children it all looked ready for treasure.'
    )
    world.say(
        f'"Captain {captain.id} and First Mate {mate.id}!" {captain.id} cried. '
        f'"Full steam to the gold!"'
    )


def spot_newcomer(world: World, newcomer: Entity, obstacle: Obstacle, loco: Locomotive) -> None:
    newcomer.meters["needs_help"] = 1
    world.say(
        f"Then they saw {newcomer.id} near the gate, not climbing aboard at all. "
        f"{obstacle.opening}"
    )
    world.say(
        f"The little locomotive puffed and waited, but {newcomer.id} stayed still, "
        f"as if the ride to {loco.tunnel} belonged to everyone else."
    )


def warn_of_missing_out(world: World, mate: Entity, newcomer: Entity,
                        obstacle: Obstacle, gift: Gift, rhyme: Rhyme) -> None:
    pred = predict_join(world, obstacle, gift, rhyme)
    world.facts["predicted_can_board"] = pred["can_board"]
    world.facts["predicted_sad"] = pred["sad"]
    mate.memes["care"] += 1
    if pred["sad"]:
        world.say(
            f'{mate.id} watched {newcomer.id}\'s face. "{newcomer.id} looks {obstacle.fear_word}," '
            f'{mate.pronoun()} said softly. "If we rush on, {newcomer.pronoun()} will be left behind."'
        )
    else:
        world.say(
            f'{mate.id} looked back at {newcomer.id}. "{newcomer.pronoun().capitalize()} needs a hand," '
            f'{mate.pronoun()} said.'
        )


def rush_beat(world: World, captain: Entity, loco: Locomotive) -> None:
    captain.memes["hurry"] += 1
    world.say(
        f'{captain.id} put one foot on the step of the locomotive. "The treasure train is leaving!" '
        f'{captain.pronoun()} said, hearing the whistle sing over {loco.route}.'
    )


def choose_kindness(world: World, captain: Entity, mate: Entity, newcomer: Entity,
                    gift: Gift, rhyme: Rhyme, obstacle: Obstacle) -> None:
    captain.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    newcomer.meters["has_gift_help"] += 1
    newcomer.meters["knows_rhyme"] += 1
    world.say(
        f"But the game changed inside {captain.id}. Treasure did not feel shiny anymore "
        f"if someone had to stand outside it."
    )
    world.say(
        f"{captain.id} {gift.text} Then {mate.id} taught {newcomer.id} a little rhyme: "
        f'"{rhyme.words[0]} / {rhyme.words[1]}"'
    )
    world.say(
        f"The words were small enough to hold in one brave breath, and kind enough to share."
    )
    propagate(world, narrate=False)


def board_together(world: World, captain: Entity, mate: Entity, newcomer: Entity,
                   loco: Locomotive, rhyme: Rhyme) -> None:
    newcomer.meters["boarded"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{newcomer.id} whispered the rhyme once, then again a little louder. {rhyme.text}'
    )
    world.say(
        f"Soon {captain.id}, {mate.id}, and {newcomer.id} were climbing aboard the little "
        f"{loco.label} together, shoulder to shoulder like a true crew."
    )


def ride_and_return(world: World, captain: Entity, mate: Entity, newcomer: Entity,
                    loco: Locomotive, obstacle: Obstacle) -> None:
    captain.memes["gratitude"] += 1
    mate.memes["gratitude"] += 1
    newcomer.memes["pride"] += 1
    world.say(
        f"The locomotive chuffed past flower beds and fence posts, then into {loco.tunnel}. "
        f"Inside the dim tunnel, the pirate game felt real enough to taste."
    )
    world.say(
        f"That was when {newcomer.id} {obstacle.later_help}"
    )
    world.say(
        f'"Crewmate eyes!" {captain.id} cheered. By the time the train rolled back into the sun, '
        f'nobody looked like a stranger anymore.'
    )


def ending_image(world: World, captain: Entity, mate: Entity, newcomer: Entity,
                 loco: Locomotive) -> None:
    world.say(
        f"When the ride ended, the three children stood beside the little {loco.label} and said the rhyme once more, "
        f"this time laughing together."
    )
    world.say(
        f"The brass whistle gave one last {loco.whistle} note, and the pirate crew hurried off toward the next bit of pretend gold -- "
        f"kind, brave, and all together."
    )


def tell(loco: Locomotive, obstacle: Obstacle, gift: Gift, rhyme: Rhyme,
         captain_name: str = "Tom", captain_gender: str = "boy",
         mate_name: str = "Lily", mate_gender: str = "girl",
         newcomer_name: str = "Mia", newcomer_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    newcomer = world.add(Entity(id=newcomer_name, kind="character", type=newcomer_gender, role="newcomer"))
    parent = world.add(Entity(id="Conductor", kind="character", type=parent_type, role="conductor", label="the conductor"))
    world.add(Entity(id="loco", type="locomotive", label=loco.label))

    opening_scene(world, captain, mate, loco)
    world.para()
    spot_newcomer(world, newcomer, obstacle, loco)
    rush_beat(world, captain, loco)
    warn_of_missing_out(world, mate, newcomer, obstacle, gift, rhyme)

    world.para()
    choose_kindness(world, captain, mate, newcomer, gift, rhyme, obstacle)
    board_together(world, captain, mate, newcomer, loco, rhyme)

    world.para()
    ride_and_return(world, captain, mate, newcomer, loco, obstacle)
    ending_image(world, captain, mate, newcomer, loco)

    world.facts.update(
        locomotive=loco,
        obstacle=obstacle,
        gift=gift,
        rhyme=rhyme,
        captain=captain,
        mate=mate,
        newcomer=newcomer,
        conductor=parent,
        joined=newcomer.meters["boarded"] >= THRESHOLD,
        courageous=newcomer.memes["courage"] >= THRESHOLD,
        belonging=newcomer.memes["belonging"] >= THRESHOLD,
    )
    return world


LOCOMOTIVES = {
    "seaside": Locomotive(
        "seaside", "locomotive", "the seaside park", "red-and-gold",
        "toot-toot", "the shell path", "the tunnel under the willow", tags={"locomotive", "train"}
    ),
    "garden": Locomotive(
        "garden", "locomotive", "the garden railway", "green-and-brass",
        "peep-peep", "the hedge track", "the rose-arch tunnel", tags={"locomotive", "train"}
    ),
    "harbor": Locomotive(
        "harbor", "locomotive", "the harbor fair", "blue-and-silver",
        "woo-woo", "the painted rails", "the cave tunnel by the dock mural", tags={"locomotive", "train"}
    ),
}

OBSTACLES = {
    "no_token": Obstacle(
        "no_token",
        "missing token",
        "One empty hand was open in front of her. She had reached the front of the line and found no ride token there.",
        "ticket",
        "ticket",
        "worried",
        "spotted the shiny shell sign that marked the pretend treasure stop before anyone else did.",
        tags={"sharing", "ticket"},
    ),
    "shy_name": Obstacle(
        "shy_name",
        "too shy to ask",
        "He knew the ride was for children, but the asking part felt big in his throat, and the words would not come.",
        "role",
        "brave",
        "shy",
        "called out the hidden turn in the track just before the tunnel, so the whole crew shouted with delight.",
        tags={"shy", "kindness"},
    ),
    "lost_place": Obstacle(
        "lost_place",
        "lost place in line",
        "She had stepped aside to pick up a dropped mitten, and now the line had slid past her like a tide.",
        "comfort",
        "welcome",
        "small",
        "held the paper treasure map steady when a gust tried to snatch it away.",
        tags={"welcome", "kindness"},
    ),
}

GIFTS = {
    "token": Gift(
        "token", "brass token", "a spare brass token", "ticket",
        "reached into his pocket, found a spare brass token, and pressed it into her palm.",
        tags={"sharing", "ticket"},
    ),
    "captain_badge": Gift(
        "captain_badge", "captain badge", "a cardboard captain badge", "role",
        "took off a cardboard captain badge from his own shirt and pinned it gently onto his chest.",
        tags={"role", "belonging"},
    ),
    "kerchief": Gift(
        "kerchief", "striped kerchief", "a striped pirate kerchief", "comfort",
        "untied a striped pirate kerchief from her wrist and wrapped it around her shoulders like a welcome flag.",
        tags={"comfort", "welcome"},
    ),
}

RHYMES = {
    "ticket_song": Rhyme(
        "ticket_song", "ticket rhyme", "ticket",
        ("Token bright, token small,", "please let one more pirate call."),
        "The conductor smiled at the polite little rhyme and waved them toward a seat.",
        tags={"rhyme", "ticket"},
    ),
    "brave_breath": Rhyme(
        "brave_breath", "brave rhyme", "brave",
        ("Brave breath in, brave words out,", "now my pirate voice can shout."),
        "The rhyme steadied his voice, and the conductor bent close enough to hear every word.",
        tags={"rhyme", "brave"},
    ),
    "welcome_wave": Rhyme(
        "welcome_wave", "welcome rhyme", "welcome",
        ("Room on deck and room on rail,", "kind hands make the grandest sail."),
        "The rhyme made the moment feel shared, and the conductor nodded them forward together.",
        tags={"rhyme", "welcome"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    locomotive: str
    obstacle: str
    gift: str
    rhyme: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    newcomer: str
    newcomer_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "locomotive": [(
        "What is a locomotive?",
        "A locomotive is the engine that pulls a train. It makes the train move along the track."
    )],
    "train": [(
        "What does a train ride on?",
        "A train rides on rails called tracks. The wheels fit the tracks so the train can roll the right way."
    )],
    "sharing": [(
        "What does sharing mean?",
        "Sharing means letting someone else use or have something too. It is one way to show kindness."
    )],
    "ticket": [(
        "What is a ride token or ticket for?",
        "A ride token or ticket shows that it is your turn for the ride. A grown-up may collect it before you get on."
    )],
    "shy": [(
        "What does shy mean?",
        "Shy means you want to do something or say something, but the words feel hard to push out. A kind person can help you feel safer."
    )],
    "welcome": [(
        "How can you make someone feel welcome?",
        "You can smile, make room, and invite them kindly. Small warm actions help a person feel they belong."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help, include, or comfort someone. It makes hard moments feel lighter."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words have matching sounds, like 'small' and 'call'. Rhymes can be fun and easy to remember."
    )],
}
KNOWLEDGE_ORDER = ["locomotive", "train", "sharing", "ticket", "shy", "welcome", "kindness", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cap, mate, newcomer = f["captain"], f["mate"], f["newcomer"]
    loco, obstacle, gift, rhyme = f["locomotive"], f["obstacle"], f["gift"], f["rhyme"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the word "locomotive" and ends with kindness changing the adventure.',
        f"Tell a gentle story where {cap.id} and {mate.id} treat a little {loco.label} like a pirate ship, notice that {newcomer.id} is stuck because of {obstacle.label}, and use {gift.label} plus a rhyme to help.",
        f'Write a simple story with a locomotive, a child who might be left out, and a small rhyme that helps everyone belong.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cap, mate, newcomer = f["captain"], f["mate"], f["newcomer"]
    loco, obstacle, gift, rhyme = f["locomotive"], f["obstacle"], f["gift"], f["rhyme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {cap.id}, {mate.id}, and {newcomer.id} at {loco.place}. They turn a little locomotive ride into a pirate adventure."
        ),
        (
            "What problem did they notice?",
            f"They noticed that {newcomer.id} might miss the ride because of {obstacle.label}. That made the pirate game feel wrong, because someone was being left outside it."
        ),
        (
            f"How did the children help {newcomer.id}?",
            f"They helped by sharing {gift.phrase} and teaching {newcomer.id} a small rhyme. The gift solved the practical problem, and the rhyme gave {newcomer.pronoun('object')} courage for the next moment."
        ),
        (
            "Why did the rhyme matter?",
            f'The rhyme mattered because it turned a scary or lonely moment into words {newcomer.id} could carry. Once the words were easy to remember, joining in felt possible.'
        ),
    ]
    if f.get("joined"):
        qa.append((
            f"What changed by the end of the story?",
            f"At the end, {newcomer.id} was no longer standing apart but riding with the others. Kindness changed the crew from two children playing alone into three children belonging together."
        ))
        qa.append((
            f"How did {newcomer.id} help later on the ride?",
            f"Later, {newcomer.id} {obstacle.later_help} That shows the kindness came back to the group, because the child who had been helped became a helper too."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["locomotive"].tags)
    tags |= set(world.facts["obstacle"].tags)
    tags |= set(world.facts["gift"].tags)
    tags |= set(world.facts["rhyme"].tags)
    tags.add("kindness")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("seaside", "no_token", "token", "ticket_song", "Tom", "boy", "Lily", "girl", "Mia", "girl", "mother"),
    StoryParams("garden", "shy_name", "captain_badge", "brave_breath", "Ben", "boy", "Zoe", "girl", "Leo", "boy", "father"),
    StoryParams("harbor", "lost_place", "kerchief", "welcome_wave", "Ava", "girl", "Max", "boy", "Nora", "girl", "mother"),
]


def explain_rejection(obstacle: Obstacle, gift: Gift, rhyme: Rhyme) -> str:
    reasons = []
    if not gift_matches(obstacle, gift):
        reasons.append(
            f"{gift.label} does not solve {obstacle.label}; this problem needs {obstacle.need_gift}-help"
        )
    if not rhyme_matches(obstacle, rhyme):
        reasons.append(
            f"{rhyme.label} is the wrong kind of rhyme; this problem needs a {obstacle.need_rhyme} rhyme"
        )
    return "(No story: " + "; ".join(reasons) + ".)"


ASP_RULES = r"""
gift_matches(O, G) :- obstacle(O), gift(G), needs_gift(O, X), gives(G, X).
rhyme_matches(O, R) :- obstacle(O), rhyme(R), needs_rhyme(O, X), solves(R, X).
valid(L, O, G, R) :- locomotive(L), obstacle(O), gift(G), rhyme(R),
                     gift_matches(O, G), rhyme_matches(O, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid in LOCOMOTIVES:
        lines.append(asp.fact("locomotive", lid))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs_gift", oid, o.need_gift))
        lines.append(asp.fact("needs_rhyme", oid, o.need_rhyme))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gives", gid, g.gives))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        lines.append(asp.fact("solves", rid, r.solves))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story or "locomotive" not in sample.story.lower():
            raise StoryError("smoke test story missing locomotive or empty output")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate-play around a locomotive, with kindness and rhyme."
    )
    ap.add_argument("--locomotive", choices=LOCOMOTIVES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.gift and args.rhyme:
        obstacle = OBSTACLES[args.obstacle]
        gift = GIFTS[args.gift]
        rhyme = RHYMES[args.rhyme]
        if not valid_combo(obstacle, gift, rhyme):
            raise StoryError(explain_rejection(obstacle, gift, rhyme))

    combos = [
        c for c in valid_combos()
        if (args.locomotive is None or c[0] == args.locomotive)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.gift is None or c[2] == args.gift)
        and (args.rhyme is None or c[3] == args.rhyme)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    loco_id, obstacle_id, gift_id, rhyme_id = rng.choice(sorted(combos))
    used: set[str] = set()
    captain, captain_gender = _pick_name(rng, used)
    used.add(captain)
    mate, mate_gender = _pick_name(rng, used)
    used.add(mate)
    newcomer, newcomer_gender = _pick_name(rng, used)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        loco_id, obstacle_id, gift_id, rhyme_id,
        captain, captain_gender, mate, mate_gender,
        newcomer, newcomer_gender, parent
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        LOCOMOTIVES[params.locomotive],
        OBSTACLES[params.obstacle],
        GIFTS[params.gift],
        RHYMES[params.rhyme],
        params.captain, params.captain_gender,
        params.mate, params.mate_gender,
        params.newcomer, params.newcomer_gender,
        params.parent,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (locomotive, obstacle, gift, rhyme) combos:\n")
        for loco, obstacle, gift, rhyme in combos:
            print(f"  {loco:8} {obstacle:10} {gift:13} {rhyme}")
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
            header = f"### {p.captain}, {p.mate}, and {p.newcomer}: {p.obstacle} on {p.locomotive}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
