#!/usr/bin/env python3
"""
storyworlds/worlds/willow_pirate_twist.py
=========================================

A standalone storyworld sketch for a child-facing pirate tale: a young deckhand
on a creek studies a willow clue, thinks through a tempting shortcut, and finds
the twist without stealing treasure.

The world keeps the moral constraint in state. A shortcut may look fast, but if
it means stealing, cutting, or lying, the deckhand's code refuses it. The clue
must actually solve the twist: a willow shadow clue reveals a shadow twist, a
reflection clue reveals a reflection twist, and so on. The ASP twin below mirrors
that gate and the outcome calculation.

Run it
------
    python storyworlds/worlds/willow_pirate_twist.py
    python storyworlds/worlds/willow_pirate_twist.py -n 5 --seed 7 --qa
    python storyworlds/worlds/willow_pirate_twist.py --all --trace
    python storyworlds/worlds/willow_pirate_twist.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CODE_MIN = 4


# ---------------------------------------------------------------------------
# Entities: people, clues, and treasure carriers share one state container.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Creek:
    id: str
    place: str
    boat: str
    captain: str
    mood: str
    landmark: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class WillowClue:
    id: str
    object: str
    mark: str
    rhyme: str
    study: str
    key: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    temptation: str
    thought: str
    refuse: str
    required: str
    lure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    apparent: str
    truth: str
    key: str
    reveal: str
    payoff: str
    owner: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, creek: Creek) -> None:
        self.creek = creek
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
        clone = World(self.creek)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules: physical clue state and emotional state use the same forward chain.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_study_clue(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get("hero")
    sig = ("study", clue.id)
    if clue.meters["studied"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["insight"] += 1
    return []


def _r_shortcut_tempts(world: World) -> list[str]:
    hero = world.get("hero")
    shortcut = world.get("shortcut")
    sig = ("tempt", shortcut.id)
    if shortcut.meters["noticed"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        hero.memes["temptation"] += shortcut.meters["lure"]
    return []


def _r_honest_choice(world: World) -> list[str]:
    hero = world.get("hero")
    sig = ("honest", hero.id)
    if hero.memes["code"] >= CODE_MIN and hero.memes["insight"] >= THRESHOLD:
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["honor"] += 1
            world.get("treasure").meters["stolen"] = 0.0
    return []


def _r_reveal_twist(world: World) -> list[str]:
    hero = world.get("hero")
    treasure = world.get("treasure")
    sig = ("reveal", treasure.id)
    if hero.memes["honor"] >= THRESHOLD and hero.memes["insight"] >= THRESHOLD:
        if sig not in world.fired:
            world.fired.add(sig)
            treasure.meters["revealed"] += 1
            hero.memes["wonder"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("study", "concept", _r_study_clue),
    Rule("tempt", "moral", _r_shortcut_tempts),
    Rule("honest", "moral", _r_honest_choice),
    Rule("reveal", "physical", _r_reveal_twist),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


# ---------------------------------------------------------------------------
# Reasonableness gate and prediction.
# ---------------------------------------------------------------------------
def clue_solves_twist(clue: WillowClue, twist: Twist) -> bool:
    return clue.key == twist.key


def shortcut_is_tempting_but_wrong(shortcut: Shortcut) -> bool:
    return shortcut.required in {"steal", "cut", "lie"} and shortcut.lure >= 2


def honest_code_sufficient(shortcut: Shortcut, code: int) -> bool:
    return code >= CODE_MIN and code >= shortcut.lure


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for creek_id, creek in CREEKS.items():
        for clue_id in creek.affords:
            clue = CLUES[clue_id]
            for shortcut_id, shortcut in SHORTCUTS.items():
                if not shortcut_is_tempting_but_wrong(shortcut):
                    continue
                for twist_id, twist in TWISTS.items():
                    if clue_solves_twist(clue, twist):
                        combos.append((creek_id, clue_id, shortcut_id, twist_id))
    return sorted(combos)


def place_name(creek: Creek) -> str:
    for prefix in ("down ", "past ", "along "):
        if creek.place.startswith(prefix):
            return creek.place[len(prefix):]
    return creek.place


def required_action(required: str) -> str:
    return {
        "steal": "stealing",
        "cut": "cutting",
        "lie": "lying",
    }.get(required, required)


def sentence_cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def outcome_of(params: "StoryParams") -> str:
    clue = CLUES[params.clue]
    shortcut = SHORTCUTS[params.shortcut]
    twist = TWISTS[params.twist]
    if not clue_solves_twist(clue, twist):
        return "wrong_clue"
    if not shortcut_is_tempting_but_wrong(shortcut):
        return "no_moral_turn"
    if not honest_code_sufficient(shortcut, params.code):
        return "at_risk"
    return "twist_uncovered"


def predict_shortcut(world: World, shortcut: Shortcut) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    treasure = sim.get("treasure")
    treasure.meters["stolen"] += 1
    hero.memes["worry"] += 1
    return {
        "would_steal": treasure.meters["stolen"] >= THRESHOLD,
        "worry": hero.memes["worry"],
        "required": shortcut.required,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, lookout: Entity, creek: Creek) -> None:
    hero.memes["curiosity"] += 1
    lookout.memes["trust"] += 1
    world.say(
        f"Once upon a time, a young deckhand named {hero.id} sailed {creek.place} "
        f"on {creek.boat}. {creek.captain} let {hero.pronoun('object')} polish "
        f"the little brass bell and watch the water for clues."
    )
    world.say(
        f"The creek was {creek.mood}, and {creek.landmark} leaned over it like "
        f"a green sail."
    )


def find_clue(world: World, hero: Entity, clue: WillowClue, twist: Twist) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["found"] += 1
    world.say(
        f"One morning the crew hunted for {twist.apparent}. Instead, {hero.id} "
        f"found {clue.object}. It had {clue.mark} on it."
    )
    world.say(f'The words made a tiny rhyme: "{clue.rhyme}"')


def study_clue(world: World, hero: Entity, clue: WillowClue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["studied"] += 1
    world.say(
        f"{hero.id} did not hurry. {hero.pronoun('subject').capitalize()} crouched "
        f"by the roots and studied the clue: {clue.study}."
    )
    world.say(
        f'"The willow is pointing, but not with a finger," {hero.id} whispered. '
        f'"It is pointing with {clue.hint}."'
    )
    propagate(world)


def tempt_shortcut(world: World, hero: Entity, shortcut: Shortcut) -> None:
    shortcut_ent = world.get("shortcut")
    shortcut_ent.meters["noticed"] += 1
    shortcut_ent.meters["lure"] = float(shortcut.lure)
    pred = predict_shortcut(world, shortcut)
    world.facts["shortcut_prediction"] = pred
    world.say(f"Then {hero.id} saw a fast way: {shortcut.temptation}.")
    world.say(
        f'{shortcut.thought} {hero.id} thought. "But fast is not the same as fair."'
    )
    propagate(world)


def refuse_shortcut(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["code"] = max(hero.memes["code"], CODE_MIN)
    hero.memes["patience"] += 1
    world.say(
        f"So {hero.id} left the shortcut alone. {shortcut.refuse} "
        f"No treasure clinked in {hero.pronoun('possessive')} pocket."
    )
    propagate(world)


def reveal_twist(world: World, hero: Entity, clue: WillowClue, twist: Twist) -> None:
    treasure = world.get("treasure")
    if treasure.meters["revealed"] < THRESHOLD:
        propagate(world)
    world.say(
        f"{hero.id} followed the willow clue the slow way. {twist.reveal}"
    )
    world.say(
        f"That was the twist: {twist.truth}. The pirates stared, then laughed "
        f"softly, because a good secret had opened without a single stolen coin."
    )


def ending(world: World, hero: Entity, lookout: Entity, twist: Twist) -> None:
    hero.memes["joy"] += 1
    lookout.memes["respect"] += 1
    world.say(
        f"{lookout.id} rang the brass bell once, clear and bright. {twist.payoff}"
    )
    world.say(
        f"At sunset {hero.id} tied a willow leaf to the mast. It fluttered like "
        f"a small green flag, and the creek carried the honest pirates home."
    )


def tell(creek: Creek, clue: WillowClue, shortcut: Shortcut, twist: Twist,
         hero_name: str = "Mara", hero_type: str = "girl",
         lookout_name: str = "Pip", lookout_type: str = "boy",
         captain: str = "Captain Brine", trait: str = "curious",
         code: int = CODE_MIN) -> World:
    world = World(creek)
    hero = world.add(Entity("hero", kind="character", type=hero_type, label=hero_name,
                            role="deckhand", traits=[trait]))
    hero.id = hero_name
    hero.memes["code"] = float(code)
    lookout = world.add(Entity("lookout", kind="character", type=lookout_type,
                               label=lookout_name, role="lookout", traits=["kind"]))
    lookout.id = lookout_name
    world.add(Entity("captain", kind="character", type="captain", label=captain,
                     role="captain"))
    world.add(Entity("clue", type="willow clue", label=clue.object,
                     attrs={"key": clue.key}))
    world.add(Entity("shortcut", type="shortcut", label=shortcut.label,
                     attrs={"required": shortcut.required}))
    world.add(Entity("treasure", type="treasure", label=twist.apparent,
                     owner=twist.owner, attrs={"key": twist.key}))

    introduce(world, hero, lookout, creek)
    find_clue(world, hero, clue, twist)

    world.para()
    study_clue(world, hero, clue)
    tempt_shortcut(world, hero, shortcut)
    refuse_shortcut(world, hero, shortcut)

    world.para()
    reveal_twist(world, hero, clue, twist)
    ending(world, hero, lookout, twist)

    world.facts.update(
        hero=hero, lookout=lookout, creek=creek, clue=clue, shortcut=shortcut,
        twist=twist, outcome=outcome_of(StoryParams(
            creek.id, clue.id, shortcut.id, twist.id, hero_name, hero_type,
            lookout_name, lookout_type, captain, trait, code)),
        treasure=world.get("treasure"), code=code,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
CREEKS = {
    "willow_bend": Creek(
        "willow_bend", "down Willow Bend Creek", "the patched skiff Minnow",
        "Captain Brine", "brown and sparkly after rain",
        "an old willow tree", {"shadow_leaf", "mirror_root", "tide_knot"},
        tags={"willow", "creek", "pirate"}),
    "frog_jetty": Creek(
        "frog_jetty", "past Frog Jetty", "the tiny sloop Picklefin",
        "Captain Sable", "quiet except for frogs",
        "a willow with toes in the mud", {"mirror_root", "mud_print", "shadow_leaf"},
        tags={"willow", "creek", "pirate"}),
    "silver_rill": Creek(
        "silver_rill", "along Silver Rill", "the creek boat Pepper",
        "Captain Marigold", "thin and silver under the sun",
        "a bent willow by the stepping stones", {"tide_knot", "mud_print", "mirror_root"},
        tags={"willow", "creek", "pirate"}),
}

CLUES = {
    "shadow_leaf": WillowClue(
        "shadow_leaf", "a flat willow leaf", "three black dots",
        "Willow low, willow lean, show the thing that can't be seen.",
        "the dots matched the leaf shadows when the sun slid west",
        "shadow", "a shadow", tags={"willow", "shadow"}),
    "mirror_root": WillowClue(
        "mirror_root", "a pale willow root", "a curl shaped like a moon",
        "Root below and sky between, look in water, not in green.",
        "the moon curl only lined up when the creek was still",
        "reflection", "a reflection", tags={"willow", "reflection"}),
    "tide_knot": WillowClue(
        "tide_knot", "a willow twig tied in two knots", "a little blue thread",
        "Two knots wait and waters lean, low creek tells what high creek seen.",
        "the knots marked where the water would fall by afternoon",
        "tide", "the falling water", tags={"willow", "tide"}),
    "mud_print": WillowClue(
        "mud_print", "a strip of willow bark", "a tiny heel print",
        "Soft mud keeps a secret clean, step beside where boots have been.",
        "the print was not a boot at all, but a stamp pressed sideways",
        "print", "a careful print", tags={"willow", "mud"}),
}

SHORTCUTS = {
    "pocket_coin": Shortcut(
        "pocket_coin", "pocketing the first bright coin from the captain's chest",
        "one silver coin winked from a loose lid",
        '"If I take that coin, I can say I found treasure first,"',
        "The coin stayed where its owner had put it.", "steal", 3,
        tags={"stealing", "honesty"}),
    "cut_net": Shortcut(
        "cut_net", "cutting the fisher's net to drag up the hidden box",
        "a net rope crossed the shallows like an easy ladder",
        '"If I cut the rope, the box may bob right up,"',
        "The net stayed whole, and the fish stayed safe.", "cut", 4,
        tags={"care", "honesty"}),
    "fake_map": Shortcut(
        "fake_map", "claiming the map said the treasure was already theirs",
        "a dry corner of the map had room for one sneaky mark",
        '"If I draw one more X, the crew will believe me,"',
        "The map stayed true, with no extra X.", "lie", 3,
        tags={"truth", "honesty"}),
    "snatch_key": Shortcut(
        "snatch_key", "snatching the lock key from the sleeping ferryman",
        "the ferryman's key ring glittered beside his boot",
        '"If I borrow the key without asking, the lock will open fast,"',
        "The key stayed beside the ferryman, exactly where it belonged.", "steal", 5,
        tags={"permission", "honesty"}),
    # Decoy for the gate: useful for --shortcut wait_turn, but it is not a
    # tempting dishonest shortcut, so this specific story has no moral turn.
    "wait_turn": Shortcut(
        "wait_turn", "waiting for the ferry bell",
        "the ferry bell would ring soon if everyone waited",
        '"If I wait, no one is tricked,"',
        "They waited their turn.", "honest", 1,
        tags={"patience"}),
}

TWISTS = {
    "shadow_chest": Twist(
        "shadow_chest", "the captain's lost gold",
        "the black X was only the willow's shadow, and under it lay a seed chest "
        "for planting the bare bank",
        "shadow",
        "When the sun tipped low, the willow's shadow made an X on a patch of "
        "plain dirt. Under the dirt was a little chest, but it held acorns and "
        "willow seeds, not gold.",
        "They planted the seeds along the bank, and each spot promised shade for "
        "future creek boats.",
        "the creek village", tags={"willow", "seed", "shadow"}),
    "mirror_shell": Twist(
        "mirror_shell", "a pearl as big as a plum",
        "the pearl on the map was the moon's reflection, showing where a lost "
        "bell shell had sunk",
        "reflection",
        "In the still water, the moon curl became a bright round pearl. Beneath "
        "that shining place rested a shell-shaped bell, green with creek moss.",
        "The bell went back to the ferry post, where it could call boats home.",
        "the ferryman", tags={"willow", "reflection", "bell"}),
    "low_water_box": Twist(
        "low_water_box", "a box of pirate rubies",
        "the rubies were red warning beads for a broken bridge plank",
        "tide",
        "When the creek sank lower, red beads gleamed under the bridge. They "
        "were not rubies for pockets; they were warning beads tied to a cracked "
        "plank.",
        "The crew marked the bridge and helped fix it before any wagon crossed.",
        "the bridge keeper", tags={"willow", "tide", "repair"}),
    "stamp_secret": Twist(
        "stamp_secret", "buried pirate silver",
        "the silver mark was a stamp for returning a lost mail pouch",
        "print",
        "Beside the willow, {hero} pressed the bark strip into soft mud. The heel "
        "print made the sign of the ferry post, and a lost mail pouch peeked "
        "from under a root.",
        "The pouch was returned unopened, and every letter reached the right door.",
        "the mail boat", tags={"willow", "mud", "letters"}),
}

GIRL_NAMES = ["Mara", "Nia", "Lily", "Zoe", "Poppy", "Anna", "Rose", "Mina"]
BOY_NAMES = ["Finn", "Pip", "Theo", "Sam", "Leo", "Ben", "Noah", "Jory"]
TRAITS = ["curious", "careful", "bright", "steady", "kind", "brave"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    creek: str
    clue: str
    shortcut: str
    twist: str
    deckhand: str
    deckhand_gender: str
    lookout: str
    lookout_gender: str
    captain: str
    trait: str
    code: int = CODE_MIN
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "willow": [("What is a willow tree?",
                "A willow is a tree with long, bendy branches and narrow leaves. "
                "It often grows near water, so it belongs naturally beside a creek.")],
    "creek": [("What is a creek?",
               "A creek is a small stream of moving water. It can be shallow enough "
               "for little boats, frogs, and muddy banks.")],
    "pirate": [("What makes this a pirate tale?",
                "It has a crew, a captain, a map-like clue, and a hunt for treasure. "
                "The pirates are gentle pretend pirates who choose honesty.")],
    "shadow": [("How can a shadow be a clue?",
                "A shadow moves when the sun moves, so it can point to a spot only "
                "at the right time of day. Watching carefully can reveal what a "
                "quick look misses.")],
    "reflection": [("What is a reflection?",
                    "A reflection is an image you see in water, glass, or something "
                    "shiny. Still creek water can work like a small mirror.")],
    "tide": [("Why can falling water reveal something?",
              "When water gets lower, things that were hidden under it can show. "
              "That is why waiting can be part of solving a creek clue.")],
    "honesty": [("Why should the deckhand not steal treasure?",
                 "Taking what belongs to someone else hurts trust. In this story, "
                 "honesty is also what lets the real secret be found.")],
    "permission": [("Why is asking permission important?",
                    "Permission means the owner gets to say yes or no. It keeps "
                    "people and their things respected.")],
}
KNOWLEDGE_ORDER = ["willow", "creek", "pirate", "shadow", "reflection", "tide",
                   "honesty", "permission"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, creek, clue, shortcut, twist = (
        f["hero"], f["creek"], f["clue"], f["shortcut"], f["twist"])
    return [
        f'Write a TinyStories-style pirate tale for a young child that includes '
        f'the word "willow", a rhyme clue, a twist, and no stolen treasure.',
        f"Tell a story where {hero.id}, a young deckhand near {place_name(creek)}, studies "
        f"{clue.object}, resists {shortcut.label}, and discovers that "
        f"{twist.apparent} is really something helpful.",
        f"Write a child-facing adventure with inner monologue: a pirate shortcut "
        f"looks tempting, but the hero thinks it through and solves the willow "
        f"clue honestly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, lookout = f["hero"], f["lookout"]
    creek, clue, shortcut, twist = f["creek"], f["clue"], f["shortcut"], f["twist"]
    prediction = f.get("shortcut_prediction", {})
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a young deckhand, and {lookout.id}, the lookout, "
         f"on a little pirate boat near {place_name(creek)}. They are hunting for a secret "
         f"near a willow tree."),
        ("What clue did the deckhand find?",
         f"{hero.id} found {clue.object} with {clue.mark} on it. The clue came "
         f"with a rhyme, so {hero.pronoun()} had to study it instead of rushing."),
        ("What shortcut tempted the deckhand?",
         f"The tempting shortcut was {shortcut.label}. It looked faster, but it "
         f"would have required {required_action(shortcut.required)}, so it would "
         f"not be fair."),
        ("What did the deckhand think before choosing?",
         f"{hero.id} thought through the shortcut and saw that fast was not the "
         f"same as fair. That inner pause helped {hero.pronoun('object')} choose "
         f"the willow clue instead of taking treasure."),
        ("What was the twist?",
         f"The hunt was not really for {twist.apparent}. {sentence_cap(twist.truth)}. "
         f"The treasure was useful to its owner, not something for pirates to steal."),
        ("Did anyone steal treasure?",
         f"No. Thinking ahead showed the shortcut would hurt trust or take something "
         f"that belonged to someone else. {hero.id} left the temptation alone and uncovered the "
         f"secret honestly."),
        ("How did the story end?",
         f"It ended with the secret returned to its proper use and the crew sailing "
         f"home under a willow leaf. The ending proves the world changed because "
         f"{twist.payoff[0].lower()}{twist.payoff[1:]}"),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["creek"].tags) | set(f["clue"].tags) | set(f["shortcut"].tags)
    tags |= set(f["twist"].tags) | {"honesty"}
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("willow_bend", "shadow_leaf", "pocket_coin", "shadow_chest",
                "Mara", "girl", "Pip", "boy", "Captain Brine", "curious", 4),
    StoryParams("frog_jetty", "mirror_root", "fake_map", "mirror_shell",
                "Finn", "boy", "Nia", "girl", "Captain Sable", "careful", 4),
    StoryParams("silver_rill", "tide_knot", "cut_net", "low_water_box",
                "Zoe", "girl", "Theo", "boy", "Captain Marigold", "steady", 5),
    StoryParams("frog_jetty", "mud_print", "snatch_key", "stamp_secret",
                "Leo", "boy", "Rose", "girl", "Captain Sable", "bright", 5),
]


def explain_rejection(creek: Creek, clue: WillowClue,
                      shortcut: Shortcut, twist: Twist) -> str:
    if clue.id not in creek.affords:
        return (f"(No story: {creek.place} does not have the {clue.object} clue. "
                f"Choose a clue found at this creek.)")
    if not clue_solves_twist(clue, twist):
        return (f"(No story: the {clue.object} clue points by {clue.key}, but "
                f"the twist needs {twist.key}. The clue must actually solve the "
                f"secret.)")
    if not shortcut_is_tempting_but_wrong(shortcut):
        return (f"(No story: {shortcut.label} is not a tempting dishonest shortcut, "
                f"so this tale loses its moral turn.)")
    return "(No story: this combination is outside the willow pirate world.)"


# ---------------------------------------------------------------------------
# ASP twin of the gate and outcome.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue solves a twist only when they use the same physical key.
solves(C, T) :- clue_key(C, K), twist_key(T, K).

% The story's shortcut must be tempting and morally wrong.
dishonest(S) :- requires(S, steal).
dishonest(S) :- requires(S, cut).
dishonest(S) :- requires(S, lie).
tempting(S)  :- shortcut_lure(S, L), L >= 2.

valid(Creek, Clue, Shortcut, Twist) :-
    creek(Creek), affords(Creek, Clue), solves(Clue, Twist),
    dishonest(Shortcut), tempting(Shortcut).

code_ok :- chosen_shortcut(S), shortcut_lure(S, L), chosen_code(C),
           code_min(M), C >= M, C >= L.

outcome(wrong_clue) :-
    chosen_clue(C), chosen_twist(T), not solves(C, T).
outcome(no_moral_turn) :-
    chosen_shortcut(S), not dishonest(S).
outcome(no_moral_turn) :-
    chosen_shortcut(S), not tempting(S).
outcome(at_risk) :-
    chosen_clue(C), chosen_twist(T), solves(C, T),
    chosen_shortcut(S), dishonest(S), tempting(S), not code_ok.
outcome(twist_uncovered) :-
    chosen_clue(C), chosen_twist(T), solves(C, T),
    chosen_shortcut(S), dishonest(S), tempting(S), code_ok.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for creek_id, creek in CREEKS.items():
        lines.append(asp.fact("creek", creek_id))
        for clue_id in sorted(creek.affords):
            lines.append(asp.fact("affords", creek_id, clue_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_key", clue_id, clue.key))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("requires", shortcut_id, shortcut.required))
        lines.append(asp.fact("shortcut_lure", shortcut_id, shortcut.lure))
    for twist_id, twist in TWISTS.items():
        lines.append(asp.fact("twist", twist_id))
        lines.append(asp.fact("twist_key", twist_id, twist.key))
    lines.append(asp.fact("code_min", CODE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_twist", params.twist),
        asp.fact("chosen_code", params.code),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    empty = build_parser().parse_args([])
    for s in range(250):
        cases.append(resolve_params(empty, random.Random(s)))
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for p in bad[:5]:
            print(" ", p, asp_outcome(p), outcome_of(p))
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a willow clue, a pirate shortcut, and "
                    "an honest twist. Unspecified choices are randomized.")
    ap.add_argument("--creek", choices=CREEKS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--lookout")
    ap.add_argument("--lookout-gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
    ap.add_argument("--code", type=int, choices=[4, 5, 6],
                    help="deckhand honesty/nerve score; must withstand the shortcut")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    creek_id = args.creek or rng.choice(sorted(CREEKS))
    clue_id = args.clue or rng.choice(sorted(CREEKS[creek_id].affords))
    shortcut_id = args.shortcut or rng.choice(sorted(
        sid for sid, s in SHORTCUTS.items() if shortcut_is_tempting_but_wrong(s)))
    valid_twists = [tid for tid, t in TWISTS.items()
                    if clue_solves_twist(CLUES[clue_id], t)]
    twist_id = args.twist or rng.choice(sorted(valid_twists))

    creek, clue = CREEKS[creek_id], CLUES[clue_id]
    shortcut, twist = SHORTCUTS[shortcut_id], TWISTS[twist_id]
    if (creek_id, clue_id, shortcut_id, twist_id) not in set(valid_combos()):
        raise StoryError(explain_rejection(creek, clue, shortcut, twist))

    code = args.code if args.code is not None else rng.randint(
        max(CODE_MIN, shortcut.lure), 6)
    if not honest_code_sufficient(shortcut, code):
        raise StoryError(
            f"(No story: code={code} is not strong enough to resist "
            f"{shortcut.label}; try --code {max(CODE_MIN, shortcut.lure)}.)")

    gender = args.gender or rng.choice(["girl", "boy"])
    deckhand = args.name or _pick_name(rng, gender)
    lookout_gender = args.lookout_gender or rng.choice(["girl", "boy"])
    lookout = args.lookout or _pick_name(rng, lookout_gender, avoid=deckhand)
    captain = args.captain or creek.captain
    trait = rng.choice(TRAITS)
    return StoryParams(creek_id, clue_id, shortcut_id, twist_id,
                       deckhand, gender, lookout, lookout_gender,
                       captain, trait, code)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CREEKS[params.creek], CLUES[params.clue], SHORTCUTS[params.shortcut],
        TWISTS[params.twist], params.deckhand, params.deckhand_gender,
        params.lookout, params.lookout_gender, params.captain, params.trait,
        params.code,
    )
    # Late format of the one twist sentence that needs the hero name.
    story = world.render().replace("{hero}", params.deckhand)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creek, clue, shortcut, twist) combos:\n")
        for creek, clue, shortcut, twist in combos:
            print(f"  {creek:12} {clue:12} {shortcut:12} {twist}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 80, 80):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.deckhand}: {p.clue} / {p.shortcut} / "
                      f"{p.twist} ({outcome_of(p)})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
