#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/weasel_rink_misunderstanding_moral_value_sound_effects.py
=========================================================================================

A standalone story world for a comedy of misunderstandings at an ice rink:
a curious weasel hears playful sound effects, jumps to the wrong conclusion,
and learns the moral value of asking before accusing.

This world is tiny on purpose.  It uses a forward-chained world model with
typed entities, physical meters, emotional memes, a reasonableness gate, and an
inline ASP twin so the Python and declarative versions can be checked together.

Seed words:
- weasel
- rink

Required features:
- Misunderstanding
- Moral Value
- Sound Effects

Style:
- Comedy
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

# Add the storyworlds/ package directory so ``results`` resolves when this file
# is run directly from the repo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

MOODS = {"wary", "curious", "embarrassed", "cheerful", "relieved", "amused"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    noisy: bool = False
    reflective: bool = False
    slippery: bool = False
    breakable: bool = False
    kind_of_sound: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    floor: str
    echoes: bool = False
    slippery: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    label: str
    sound: str
    cause_word: str
    can_fool: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    label: str
    mistaken_about: str
    wrong_reason: str
    comedic_beat: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    lesson: str
    kindly: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reaction:
    id: str
    label: str
    action: str
    effect: str
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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    rink = world.entities.get("rink")
    if not rink:
        return out
    for e in world.characters():
        if e.meters["noise"] < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if rink.attrs.get("echoes"):
            e.memes["startle"] += 1
            out.append("__echo__")
    return out


def _r_look_closer(world: World) -> list[str]:
    out: list[str] = []
    weasel = world.entities.get("weasel")
    if not weasel:
        return out
    if weasel.meters["suspicion"] < THRESHOLD:
        return out
    sig = ("look_closer", "weasel")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    weasel.memes["embarrassable"] += 1
    out.append("__look__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("weasel") is None or world.entities.get("rink") is None:
        return out
    if world.entities["weasel"].meters["understanding"] < THRESHOLD:
        return out
    sig = ("relief", "weasel")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["weasel"].memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("echo", "sound", _r_echo),
    Rule("look_closer", "social", _r_look_closer),
    Rule("relief", "social", _r_relief),
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


def prank_credible(trigger: Trigger, place: Place) -> bool:
    return trigger.can_fool and place.echoes


def wrong_but_funny(trigger: Trigger, misunderstanding: Misunderstanding) -> bool:
    return trigger.id == misunderstanding.mistaken_about and trigger.can_fool


def moral_clear(reaction: Reaction, moral: Moral) -> bool:
    return reaction.id in {"ask_first", "apologize"} and moral.id == "ask_before_accusing"


def would_blunder(trigger: Trigger, place: Place, misunderstanding: Misunderstanding) -> bool:
    return prank_credible(trigger, place) and wrong_but_funny(trigger, misunderstanding)


def resolve_noise(world: World, trigger: Trigger, reaction: Reaction) -> None:
    weasel = world.get("weasel")
    rink = world.get("rink")
    weasel.meters["understanding"] += 1
    weasel.memes["amused"] += 1
    body = reaction.effect
    world.say(
        f"The sound kept going: {trigger.sound} {trigger.sound.lower()}! Then "
        f"{body}, and the joke of it became clear."
    )
    world.say(
        f"{weasel.id} blinked, then laughed. The {rink.label_word} was not in trouble at all."
    )


def worry(world: World, weasel: Entity, trigger: Trigger, place: Place) -> None:
    weasel.meters["suspicion"] += 1
    weasel.memes["wary"] += 1
    world.say(
        f"At the {place.label}, {weasel.id} heard {trigger.sound} from the ice and "
        f"froze mid-scamper."
    )
    world.say(
        f'"Did someone just {trigger.cause_word} the rink?" {weasel.id} whispered, '
        f"taking the smallest possible step."
    )


def misread(world: World, weasel: Entity, trigger: Trigger, misunderstanding: Misunderstanding) -> None:
    weasel.meters["noise"] += 1
    weasel.meters["suspicion"] += 1
    weasel.memes["confused"] += 1
    world.say(
        f"{weasel.id} heard {trigger.sound} again and made the wrong guess: "
        f"{misunderstanding.wrong_reason}."
    )
    world.say(
        f"{misunderstanding.comedic_beat.capitalize()}, so {weasel.id}'s whiskers "
        f"went straight up like tiny flagpoles."
    )


def helper(world: World, friend: Entity, weasel: Entity, reaction: Reaction, moral: Moral) -> None:
    friend.memes["kind"] += 1
    world.say(
        f"A friend skated over and said, \"Maybe ask before you accuse.\" "
        f"That was {moral.kindly}."
    )
    world.say(
        f"Then {friend.id} showed how {reaction.action}, and the squeaky mystery shrank to size."
    )


def apology(world: World, weasel: Entity, friend: Entity, trigger: Trigger, moral: Moral) -> None:
    weasel.memes["embarrassed"] += 1
    weasel.memes["relieved"] += 1
    world.say(
        f"{weasel.id} peeked at the rink again and saw {trigger.label} was only "
        f"making playful sound effects."
    )
    world.say(
        f'"Oops," said {weasel.id}. "I thought the rink was being attacked by noise." '
        f"{weasel.pronoun().capitalize()} bowed to {friend.id} and promised the moral: "
        f"{moral.lesson}."
    )


def ending(world: World, weasel: Entity, place: Place, trigger: Trigger) -> None:
    weasel.memes["cheerful"] += 1
    world.say(
        f"In the end, {weasel.id} skated in circles past the {place.label}, "
        f"now giggling at every {trigger.sound} the ice made."
    )
    world.say(
        f"The rink stayed shiny, the joke stayed gentle, and {weasel.id} left with a grin."
    )


def tell(place: Place, trigger: Trigger, misunderstanding: Misunderstanding,
         moral: Moral, reaction: Reaction,
         weasel_name: str = "Wally", weasel_type: str = "weasel",
         friend_name: str = "Mina", friend_type: str = "girl") -> World:
    world = World()
    weasel = world.add(Entity(
        id=weasel_name, kind="character", type=weasel_type, role="troublemaker",
        traits=["curious", "tiny"], kind_of_sound=trigger.sound, reflective=True
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type, role="helper",
        traits=["kind", "quick"], reflective=True
    ))
    rink = world.add(Entity(
        id="rink", kind="place", type="place", label=place.label,
        attrs={"echoes": place.echoes, "floor": place.floor}
    ))

    world.facts["place"] = place
    world.facts["trigger"] = trigger
    world.facts["misunderstanding"] = misunderstanding
    world.facts["moral"] = moral
    world.facts["reaction"] = reaction

    world.say(
        f"{weasel.id} the weasel loved the {place.label}. It was bright, breezy, and "
        f"full of long, slippery loops."
    )
    world.say(
        f"Every time the skates went {trigger.sound}, {weasel.id}'s ears twitched as if "
        f"the sound had a secret."
    )

    world.para()
    worry(world, weasel, trigger, place)
    misread(world, weasel, trigger, misunderstanding)

    world.para()
    helper(world, friend, weasel, reaction, moral)
    resolve_noise(world, trigger, reaction)
    apology(world, weasel, friend, trigger, moral)

    world.para()
    ending(world, weasel, place, trigger)

    world.facts.update(
        weasel=weasel,
        friend=friend,
        rink=rink,
        resolved=True,
        embarrassed=weasel.memes["embarrassed"] >= THRESHOLD,
        understood=weasel.meters["understanding"] >= THRESHOLD,
    )
    return world


PLACES = {
    "rink": Place("rink", "rink", "ice", echoes=True, slippery=True,
                  tags={"rink", "ice", "sound"}),
    "tiny_rink": Place("tiny_rink", "tiny rink", "ice", echoes=True, slippery=True,
                       tags={"rink", "ice", "sound"}),
    "practice_rink": Place("practice_rink", "practice rink", "ice", echoes=True, slippery=True,
                           tags={"rink", "ice", "sound"}),
}

TRIGGERS = {
    "skate_squeak": Trigger("skate_squeak", "the skate squeaks", "Squeak!", "squeak", True,
                            tags={"sound", "squeak"}),
    "puck_ping": Trigger("puck_ping", "the puck ping", "Ping!", "ping", True,
                         tags={"sound", "ping"}),
    "whistle_boop": Trigger("whistle_boop", "the referee whistle", "Toot!", "toot", True,
                            tags={"sound", "whistle"}),
}

MISUNDERSTANDINGS = {
    "rampage": Misunderstanding(
        "rampage",
        "a rampage",
        "skate_squeak",
        "the rink had been attacked by a noisy villain",
        "That was a mighty leap for one little brain",
        tags={"misunderstanding", "comedy"},
    ),
    "secret_game": Misunderstanding(
        "secret_game",
        "a secret game",
        "puck_ping",
        "the rink was hiding a joke just for weasels",
        "That is what happens when curiosity wears boots",
        tags={"misunderstanding", "comedy"},
    ),
    "lost_call": Misunderstanding(
        "lost_call",
        "a lost call",
        "whistle_boop",
        "someone was yelling at the ice",
        "The whiskers heard drama where there was only sports",
        tags={"misunderstanding", "comedy"},
    ),
}

MORALS = {
    "ask_before_accusing": Moral(
        "ask_before_accusing",
        "ask before accusing",
        "kind and calm",
        tags={"moral", "ask", "kind"},
    ),
    "check_first": Moral(
        "check_first",
        "check first",
        "gentle and wise",
        tags={"moral", "check", "kind"},
    ),
}

REACTIONS = {
    "ask_first": Reaction(
        "ask_first",
        "ask first",
        "ask one simple question",
        "the mystery turned into an ordinary answer",
        tags={"ask", "moral"},
    ),
    "listen_closer": Reaction(
        "listen_closer",
        "listen closer",
        "tilt one's head and listen again",
        "the sound became clearly friendly",
        tags={"listen", "moral"},
    ),
    "apologize": Reaction(
        "apologize",
        "apologize",
        "say sorry and make room to laugh",
        "the weasel's cheeks cooled down",
        tags={"apologize", "moral"},
    ),
}

WEASEL_NAMES = ["Wally", "Pip", "Milo", "Nibbles", "Tilly", "Dot", "Pogo", "Merry"]
FRIEND_NAMES = ["Mina", "Nora", "Rae", "Toby", "Jules", "Bea", "Finn", "Ivy"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for trig_id, trig in TRIGGERS.items():
            for mis_id, mis in MISUNDERSTANDINGS.items():
                if not would_blunder(trig, place, mis):
                    continue
                for moral_id, moral in MORALS.items():
                    for react_id, react in REACTIONS.items():
                        if moral_clear(react, moral):
                            combos.append((place_id, trig_id, mis_id, moral_id, react_id))
    return combos


@dataclass
class StoryParams:
    place: str
    trigger: str
    misunderstanding: str
    moral: str
    reaction: str
    weasel_name: str
    weasel_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    trig = f["trigger"]
    mis = f["misunderstanding"]
    moral = f["moral"]
    return [
        f'Write a short comedy for a young child set at a {place.label} with a weasel and the sound "{trig.sound}".',
        f"Tell a funny story where {f['weasel'].id} misunderstands {mis.label} at the rink, then learns to {moral.lesson}.",
        f'Write a gentle story with sound effects, a weasel, and the line "{moral.lesson}" at the rink.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    weasel = f["weasel"]
    friend = f["friend"]
    place = f["place"]
    trig = f["trigger"]
    mis = f["misunderstanding"]
    moral = f["moral"]
    react = f["reaction"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {weasel.id} the weasel and {friend.id}, who are at the {place.label}. "
            f"The funny part is that one little sound causes a big mix-up before everyone laughs.",
        ),
        (
            "What sound kept making trouble?",
            f"The trouble was really just {trig.sound}. {weasel.id} kept hearing it and thinking it meant something bigger than it was.",
        ),
        (
            "What did {0} think was happening?".format(weasel.id),
            f"{weasel.id} thought {mis.wrong_reason}. That was not true, but it was a very comic mistake.",
        ),
        (
            "How was the problem fixed?",
            f"{friend.id} helped by telling {weasel.id} to {react.action}. Then the weird noise turned into a normal rink sound, and the worry melted away.",
        ),
        (
            "What did {0} learn?".format(weasel.id),
            f"{weasel.id} learned to {moral.lesson}. That moral value matters because asking first is kinder than guessing wrong.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["trigger"].tags) | set(f["misunderstanding"].tags) | set(f["moral"].tags)
    if f.get("reaction"):
        tags |= set(f["reaction"].tags)
    know = []
    knowledge = {
        "rink": [
            ("What is a rink?",
             "A rink is a smooth place for skating, usually made of ice or another slippery surface."),
        ],
        "ice": [
            ("Why is ice slippery?",
             "Ice is slippery because a thin layer of water can form on top, which makes it easy to slide."),
        ],
        "sound": [
            ("What is a sound effect?",
             "A sound effect is a special noise that helps you notice action, like squeaks, pings, or toots."),
        ],
        "squeak": [
            ("What is a squeak?",
             "A squeak is a short, high sound, like a skate making noise on the ice."),
        ],
        "ping": [
            ("What is a ping?",
             "A ping is a sharp little sound, often quick and bright."),
        ],
        "whistle": [
            ("What does a whistle do?",
             "A whistle makes a sharp sound so people can hear a signal quickly."),
        ],
        "misunderstanding": [
            ("What is a misunderstanding?",
             "A misunderstanding is when someone thinks the wrong thing because they do not have the full story."),
        ],
        "moral": [
            ("What is a moral in a story?",
             "A moral is a lesson the story wants to teach, often about being kind, honest, or careful."),
        ],
        "ask": [
            ("Why is asking a question helpful?",
             "Asking a question can clear up confusion and stop people from guessing the wrong thing."),
        ],
        "kind": [
            ("Why should you be kind when you are confused?",
             "Kindness gives everyone room to explain and makes it easier to fix the mix-up without hurting feelings."),
        ],
    }
    order = ["rink", "ice", "sound", "squeak", "ping", "whistle", "misunderstanding", "moral", "ask", "kind"]
    for key in order:
        if key in tags and key in knowledge:
            know.extend(knowledge[key])
    return know


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "place":
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, trig: Trigger, mis: Misunderstanding, moral: Moral, react: Reaction) -> str:
    return (
        f"(No story: this combination does not create a believable comedy of misunderstanding. "
        f"Need a sound that can fool the weasel at the rink, plus a moral turn where the reaction is to ask or listen first.)"
    )


ASP_RULES = r"""
% A story is valid when the rink can fool the weasel, the misunderstanding fits,
% and the chosen reaction supports the moral lesson.
blunder(P, T, M) :- place(P), trigger(T), misunderstanding(M), prank_credible(P, T), wrong_but_funny(T, M).
valid(P, T, M, Mo, R) :- blunder(P, T, M), moral(Mo), reaction(R), moral_clear(R, Mo).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
        if p.slippery:
            lines.append(asp.fact("slippery", pid))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        if t.can_fool:
            lines.append(asp.fact("can_fool", tid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("mistaken_about", mid, m.mistaken_about))
    for moid, mo in MORALS.items():
        lines.append(asp.fact("moral", moid))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    cases = list(CURATED)
    bad = 0
    for p in cases:
        if not would_blunder(TRIGGERS[p.trigger], PLACES[p.place], MISUNDERSTANDINGS[p.misunderstanding]):
            bad += 1
    if bad == 0:
        print(f"OK: curated cases are reasonable ({len(cases)} cases).")
    else:
        rc = 1
        print(f"MISMATCH: {bad} curated cases failed reasonableness.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a weasel, a rink, sound effects, a misunderstanding, and a moral value."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--weasel-name", choices=WEASEL_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.trigger and args.misunderstanding and args.moral and args.reaction:
        if (args.place, args.trigger, args.misunderstanding, args.moral, args.reaction) not in valid_combos():
            raise StoryError(explain_rejection(PLACES[args.place], TRIGGERS[args.trigger],
                                               MISUNDERSTANDINGS[args.misunderstanding],
                                               MORALS[args.moral], REACTIONS[args.reaction]))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.trigger is None or c[1] == args.trigger)
        and (args.misunderstanding is None or c[2] == args.misunderstanding)
        and (args.moral is None or c[3] == args.moral)
        and (args.reaction is None or c[4] == args.reaction)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trig, mis, moral, react = rng.choice(sorted(combos))
    weasel_name = args.weasel_name or rng.choice(WEASEL_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(place, trig, mis, moral, react, weasel_name, "weasel", friend_name, "girl")


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TRIGGERS[params.trigger],
        MISUNDERSTANDINGS[params.misunderstanding],
        MORALS[params.moral],
        REACTIONS[params.reaction],
        params.weasel_name,
        params.weasel_type,
        params.friend_name,
        params.friend_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams("rink", "skate_squeak", "rampage", "ask_before_accusing", "ask_first", "Wally", "weasel", "Mina", "girl"),
    StoryParams("tiny_rink", "puck_ping", "secret_game", "check_first", "listen_closer", "Pip", "weasel", "Nora", "girl"),
    StoryParams("practice_rink", "whistle_boop", "lost_call", "ask_before_accusing", "apologize", "Milo", "weasel", "Rae", "girl"),
]


def tell_story_from_params(params: StoryParams) -> World:
    return tell(
        PLACES[params.place],
        TRIGGERS[params.trigger],
        MISUNDERSTANDINGS[params.misunderstanding],
        MORALS[params.moral],
        REACTIONS[params.reaction],
        params.weasel_name,
        params.weasel_type,
        params.friend_name,
        params.friend_type,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  " + " ".join(combo))
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
            header = f"### {p.weasel_name} at the {p.place} ({p.trigger}, {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
