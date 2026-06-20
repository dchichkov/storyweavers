#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py
===================================================================================

A small myth-shaped story world about a child following a sacred thread to solve
a village mystery. The thread points toward a hidden guardian, curiosity pulls
the child onward, conflict rises at the gate, and a respectful gift restores the
missing charm so the wounded place can recuperate.

Run it
------
    python storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py
    python storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py --mystery silent_spring
    python storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py --helper swallow --mystery buried_door
    python storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py --offering bread --mystery moon_brazier
    python storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/straight_thread_recuperate_mystery_to_solve_curiosity.py --verify
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
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    place: str
    opening: str
    ending: str
    elder_title: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    source_label: str
    source_the: str
    ail_text: str
    item_label: str
    item_the: str
    item_place: str
    guardian_label: str
    guardian_type: str
    guardian_title: str
    terrain: str
    clue_text: str
    heal_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

    @property
    def Source(self) -> str:
        return self.source_the[0].upper() + self.source_the[1:]


@dataclass
class Helper:
    id: str
    label: str
    type: str
    move_text: str
    advice: str
    domains: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    speech: str
    guardians: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm_cfg = realm
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
        clone = World(self.realm_cfg)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_need(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["missing"] < THRESHOLD:
        return []
    sig = ("need", "source")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("realm").meters["need"] += 1
    world.get("hero").memes["worry"] += 1
    return ["__need__"]


def _r_clash(world: World) -> list[str]:
    guardian = world.get("guardian")
    hero = world.get("hero")
    if guardian.memes["blocking"] < THRESHOLD or hero.memes["push"] < THRESHOLD:
        return []
    sig = ("clash", "gate")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    guardian.memes["anger"] += 1
    world.get("helper").memes["concern"] += 1
    world.get("realm").meters["conflict"] += 1
    return ["__clash__"]


def _r_heal(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["restored"] < THRESHOLD:
        return []
    sig = ("heal", "source")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["ailing"] = 0.0
    source.meters["renewed"] += 1
    world.get("realm").meters["need"] = 0.0
    world.get("realm").meters["conflict"] = 0.0
    world.get("hero").memes["relief"] += 1
    world.get("hero").memes["wonder"] += 1
    world.get("guardian").memes["trust"] += 1
    return ["__heal__"]


CAUSAL_RULES = [
    Rule("need", "physical", _r_need),
    Rule("clash", "social", _r_clash),
    Rule("heal", "physical", _r_heal),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


REALMS = {
    "laurel_vale": Realm(
        "laurel_vale",
        "Laurel Vale, where old stones kept the memories of songs",
        "the valley listened as if every hill had leaned closer",
        "keeper",
        tags={"valley", "myth"},
    ),
    "reed_marsh": Realm(
        "reed_marsh",
        "Reed Marsh, where moonlit pools shone between silver reeds",
        "the marsh held its breath beneath the stars",
        "keeper",
        tags={"marsh", "myth"},
    ),
    "amber_hill": Realm(
        "amber_hill",
        "Amber Hill, where warm wind moved through little shrines",
        "the hill glowed softly in the evening light",
        "keeper",
        tags={"hill", "myth"},
    ),
}

MYSTERIES = {
    "silent_spring": Mystery(
        "silent_spring",
        "spring of songs",
        "the spring of songs",
        "its water only shivered in silence",
        "shell spindle",
        "the shell spindle",
        "beneath a ring of wet stones",
        "Reed Mother",
        "spirit",
        "reed spirit",
        "water",
        "A pale thread clung to a reed, then ran away in a line so straight it looked drawn by a careful finger.",
        "When the spindle touched the pool again, the water began to recuperate its bright voice.",
        "Soon the spring sang clear enough for dragonflies to dance over it.",
        tags={"spring", "water", "thread"},
    ),
    "moon_brazier": Mystery(
        "moon_brazier",
        "moon brazier",
        "the moon brazier",
        "its blue flame had fallen to a weak ember",
        "sun coal",
        "the sun coal",
        "inside a soot-dark bowl",
        "Ash Lion",
        "spirit",
        "ash lion",
        "fire",
        "A golden thread lay over the altar and stretched away, straight across the flagstones toward the sleeping kiln-cave.",
        "When the coal rolled back into place, the brazier seemed to recuperate its hidden fire one breath at a time.",
        "Soon the flame stood tall and silver moths circled it like tiny moons.",
        tags={"fire", "light", "thread"},
    ),
    "buried_door": Mystery(
        "buried_door",
        "door of dawn",
        "the door of dawn",
        "its carved face would not open, and morning light stayed thin",
        "copper key-seed",
        "the copper key-seed",
        "under a shelf of dusty roots",
        "Root Keeper",
        "spirit",
        "root keeper",
        "earth",
        "A red thread had slipped from the keyhole and lay straight over the moss as if it wanted to be followed.",
        "When the key-seed settled back into the lock, the old door began to recuperate its strength and opened with a long golden sigh.",
        "Soon warm light streamed through the doorway and painted the roots with dawn.",
        tags={"door", "earth", "light"},
    ),
}

HELPERS = {
    "swallow": Helper(
        "swallow",
        "swallow",
        "bird",
        "skimmed low and swift",
        "bows before proud fire and clean words before old stone",
        {"fire", "open"},
        tags={"bird", "guide"},
    ),
    "mole": Helper(
        "mole",
        "mole",
        "animal",
        "patted the ground and found the soft places under it",
        "old things under earth listen when footsteps grow gentle",
        {"earth", "burrow"},
        tags={"animal", "earth"},
    ),
    "otter": Helper(
        "otter",
        "otter",
        "animal",
        "slid through the shallows with bright wet whiskers",
        "water spirits trust gifts that can be shared, not grabbed",
        {"water", "shore"},
        tags={"animal", "water"},
    ),
    "goat": Helper(
        "goat",
        "goat",
        "animal",
        "picked a neat path along rock and root",
        "stubborn gates open faster for the humble than for the hurried",
        {"earth", "fire", "open"},
        tags={"animal", "hill"},
    ),
}

OFFERINGS = {
    "bread": Offering(
        "bread",
        "bread",
        "a warm round of bread",
        '“I brought bread for hungry watchfulness,”',
        {"Root Keeper", "Ash Lion"},
        tags={"gift", "bread"},
    ),
    "song": Offering(
        "song",
        "song",
        "a patient little song",
        '“I brought a song to sit beside your silence,”',
        {"Reed Mother"},
        tags={"gift", "song"},
    ),
    "water": Offering(
        "water",
        "water",
        "a small bowl of clear water",
        '“I brought clear water for tired paws and thirsty roots,”',
        {"Ash Lion", "Root Keeper"},
        tags={"gift", "water"},
    ),
    "reeds": Offering(
        "reeds",
        "reed braid",
        "a braid of fresh green reeds",
        '“I brought new reeds to mend what the wind has frayed,”',
        {"Reed Mother"},
        tags={"gift", "reeds"},
    ),
}

GIRL_NAMES = ["Ione", "Thaleia", "Mira", "Dora", "Lysa", "Neris"]
BOY_NAMES = ["Timon", "Leandros", "Pyrros", "Nikos", "Orin", "Damon"]
TRAITS = ["patient", "hasty", "curious", "steady", "bright-eyed"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mid, mystery in MYSTERIES.items():
        for hid, helper in HELPERS.items():
            if mystery.terrain not in helper.domains and "open" not in helper.domains:
                continue
            for oid, offering in OFFERINGS.items():
                if mystery.guardian_label in offering.guardians:
                    combos.append((mid, hid, oid))
    return combos


def helper_fits(helper: Helper, mystery: Mystery) -> bool:
    return mystery.terrain in helper.domains or "open" in helper.domains


def offering_fits(offering: Offering, mystery: Mystery) -> bool:
    return mystery.guardian_label in offering.guardians


def explain_helper(helper: Helper, mystery: Mystery) -> str:
    return (
        f"(No story: the {helper.label} does not travel the {mystery.terrain} paths "
        f"around {mystery.source_the}, so it would not honestly find the clue there.)"
    )


def explain_offering(offering: Offering, mystery: Mystery) -> str:
    good = ", ".join(sorted(o.id for o in OFFERINGS.values() if mystery.guardian_label in o.guardians))
    return (
        f"(No story: {offering.phrase} would not soothe {mystery.guardian_label}. "
        f"Try an offering that fits this guardian, such as: {good}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    return "smooth" if params.temperament == "patient" else "strained"


def predict_gate(world: World, temperament: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    guardian = sim.get("guardian")
    guardian.memes["blocking"] += 1
    if temperament != "patient":
        hero.memes["push"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": hero.memes["fear"],
        "conflict": sim.get("realm").meters["conflict"],
    }


def invoke_loss(world: World) -> None:
    source = world.get("source")
    source.meters["missing"] += 1
    source.meters["ailing"] += 1
    propagate(world)


def open_story(world: World, hero: Entity, elder: Entity, mystery: Mystery) -> None:
    world.say(
        f"In {world.realm_cfg.opening}, there lived a child named {hero.id}. "
        f"{hero.pronoun().capitalize()} was known for curiosity that walked a little ahead of caution."
    )
    world.say(
        f"One dawn, {mystery.source_the} looked wrong. {mystery.ail_text}."
    )
    world.say(
        f'The {world.realm_cfg.elder_title}, {elder.id}, touched the old stones and whispered, '
        f'"Something has been taken from {mystery.source_the}. Until it is brought home, it cannot recuperate."'
    )


def discover_clue(world: World, hero: Entity, helper: Entity, mystery: Mystery, helper_cfg: Helper) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"As {hero.id} knelt beside the altar, a {helper_cfg.label} {helper_cfg.move_text}. "
        f"{mystery.clue_text}"
    )
    world.say(
        f'"A thread," {hero.id} breathed. "And it points somewhere." '
        f'The little {helper_cfg.label} seemed to agree.'
    )


def set_out(world: World, hero: Entity, helper_cfg: Helper, mystery: Mystery) -> None:
    world.say(
        f"So {hero.id} followed the thread past fig roots and weathered stones, "
        f"keeping it as straight as {hero.pronoun('possessive')} own shadow. "
        f"It led at last to {mystery.item_place} near the dwelling of the {mystery.guardian_title}."
    )


def gate_conflict(world: World, hero: Entity, helper: Entity, guardian: Entity,
                  helper_cfg: Helper, offering: Offering, mystery: Mystery,
                  temperament: str) -> None:
    pred = predict_gate(world, temperament)
    world.facts["predicted_conflict"] = pred["conflict"]
    guardian.memes["blocking"] += 1
    world.say(
        f'Before {hero.id} could step closer, the {mystery.guardian_title} rose and barred the way. '
        f'"Who follows my path?" {guardian.label} asked. "Many come wanting treasures. Few come wanting to mend."'
    )
    if temperament != "patient":
        hero.memes["push"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} took one quick step anyway. At once the guardian swept the thread into a tangle, "
            f"and {hero.pronoun('possessive')} brave heart thumped with sudden fear."
        )
        world.say(
            f'The {helper_cfg.label} stayed close and seemed to say, in its own small way, '
            f'"{helper_cfg.advice}."'
        )
        hero.memes["humility"] += 1
    else:
        hero.memes["humility"] += 1
        world.say(
            f"{hero.id} did not rush. {hero.pronoun().capitalize()} remembered that a mystery is not solved by snatching at it."
        )
    guardian.memes["listening"] += 1
    world.say(
        f"{hero.id} held out {offering.phrase} and said {offering.speech} "
        f'"I came for {mystery.item_the}, so {mystery.source_the} may heal."'
    )
    guardian.memes["trust"] += 1
    guardian.memes["blocking"] = 0.0
    world.say(
        f"The guardian studied the gift, then the child, and the hard line in {guardian.pronoun('possessive')} face softened."
    )


def recover_item(world: World, hero: Entity, guardian: Entity, mystery: Mystery) -> None:
    item = world.get("item")
    item.meters["found"] += 1
    hero.memes["hope"] += 1
    world.say(
        f'"Then take it," {guardian.label} said. "I hid it because careless hands had grown too bold. '
        f'I wished to see whether a kind heart would follow the thread."'
    )
    world.say(
        f"Beneath the hidden place, {hero.id} found {mystery.item_the} and lifted it carefully in both hands."
    )


def restore(world: World, hero: Entity, mystery: Mystery) -> None:
    item = world.get("item")
    source = world.get("source")
    item.meters["home"] += 1
    source.meters["restored"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} carried {mystery.item_the} back along the same straight thread, "
        f"which now seemed to shine for the whole path home."
    )
    world.say(
        f"When {mystery.item_the} was set again in {mystery.source_the}, the old place gave a quiet shiver. "
        f"{mystery.heal_text}"
    )


def ending(world: World, hero: Entity, elder: Entity, mystery: Mystery, temperament: str) -> None:
    if temperament == "patient":
        line = f'{elder.id} smiled and said, "Curiosity is brightest when it walks hand in hand with patience."'
    else:
        line = f'{elder.id} touched {hero.id}\'s shoulder and said, "Even a hurried heart can learn the gentler road."'
    world.say(line)
    world.say(
        f"{mystery.ending_image} {world.realm_cfg.ending}. "
        f"And from that day on, whenever {hero.id} saw a wandering thread, {hero.pronoun()} looked twice before pulling once."
    )


def tell(realm: Realm, mystery: Mystery, helper_cfg: Helper, offering: Offering,
         hero_name: str = "Ione", hero_type: str = "girl", elder_type: str = "mother",
         temperament: str = "patient") -> World:
    world = World(realm)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            traits=[temperament]))
    elder = world.add(Entity(id="The Keeper", kind="character", type=elder_type, role="elder",
                             label="the keeper"))
    helper = world.add(Entity(id=helper_cfg.label.capitalize(), kind="character",
                              type=helper_cfg.type, role="helper", label=helper_cfg.label))
    guardian = world.add(Entity(id=mystery.guardian_label, kind="character",
                                type=mystery.guardian_type, role="guardian",
                                label=mystery.guardian_label))
    source = world.add(Entity(id="source", type="source", label=mystery.source_label))
    item = world.add(Entity(id="item", type="charm", label=mystery.item_label))
    realm_ent = world.add(Entity(id="realm", type="realm", label=realm.place))

    open_story(world, hero, elder, mystery)
    invoke_loss(world)

    world.para()
    discover_clue(world, hero, helper, mystery, helper_cfg)
    set_out(world, hero, helper_cfg, mystery)

    world.para()
    gate_conflict(world, hero, helper, guardian, helper_cfg, offering, mystery, temperament)
    recover_item(world, hero, guardian, mystery)

    world.para()
    restore(world, hero, mystery)
    ending(world, hero, elder, mystery, temperament)

    world.facts.update(
        realm=realm,
        mystery=mystery,
        helper_cfg=helper_cfg,
        offering=offering,
        hero=hero,
        elder=elder,
        helper=helper,
        guardian=guardian,
        source=source,
        item=item,
        outcome=outcome_of(StoryParams(realm.id, mystery.id, helper_cfg.id, offering.id,
                                       hero_name, hero_type, elder_type, temperament)),
        conflict=world.get("realm").meters["conflict"] >= THRESHOLD or temperament != "patient",
        solved=item.meters["home"] >= THRESHOLD,
        recuperated=source.meters["renewed"] >= THRESHOLD,
        temperament=temperament,
    )
    return world


@dataclass
class StoryParams:
    realm: str
    mystery: str
    helper: str
    offering: str
    name: str
    gender: str
    elder: str
    temperament: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "thread": [(
        "What is a thread?",
        "A thread is a very thin strand of fiber. People use thread for sewing, tying, or tracing a tiny line from one place to another."
    )],
    "spring": [(
        "What is a spring?",
        "A spring is a place where water comes up from the ground. It can feed a stream or a pool."
    )],
    "fire": [(
        "What is a brazier?",
        "A brazier is a bowl or stand that safely holds burning coals or a flame. People use one for warmth or light."
    )],
    "door": [(
        "Why would an old key matter in a myth?",
        "In myths, a key can stand for permission, memory, or a promise. When the right key returns, something important can open again."
    )],
    "curiosity": [(
        "What is curiosity?",
        "Curiosity is the feeling that makes you want to know more. It helps you notice clues and ask good questions."
    )],
    "patience": [(
        "Why is patience useful when solving a mystery?",
        "Patience helps you slow down and notice what is really happening. If you rush, you can miss clues or make a problem bigger."
    )],
    "gift": [(
        "Why do stories use gifts to calm a guardian?",
        "A fitting gift shows respect. In many old tales, respect matters more than force."
    )],
}
KNOWLEDGE_ORDER = ["thread", "spring", "fire", "door", "curiosity", "patience", "gift"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    hero = f["hero"]
    return [
        f'Write a child-friendly myth about a mystery to solve in which a straight thread leads {hero.id} toward {mystery.source_the}. Include the words "straight", "thread", and "recuperate".',
        f"Tell a gentle myth where curiosity leads a child to follow a clue, face a guardian in conflict, and return a missing charm so {mystery.source_the} can heal.",
        f"Write a short mythic story in which respect solves a mystery better than grabbing, and the ending proves what changed in the land.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    helper = f["helper_cfg"]
    guardian = f["guardian"]
    elder = f["elder"]
    offering = f["offering"]
    qa = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {mystery.source_the} was failing: {mystery.ail_text}. Something important had been taken away, so the old place could not recuperate."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found a thread leading away from {mystery.source_the}. It ran so straight that it clearly looked like a clue instead of an accident."
        ),
        (
            f"Why did {hero.id} follow the thread?",
            f"{hero.id} was curious and wanted to solve the mystery. The thread seemed to promise that it knew where {mystery.item_the} had been hidden."
        ),
        (
            "Who stopped the child, and why?",
            f"{guardian.label} blocked the path near the hidden place. The guardian believed too many people wanted treasure without caring for what was hurt."
        ),
    ]
    if f["temperament"] != "patient":
        qa.append((
            f"What made the conflict stronger at first?",
            f"{hero.id} hurried forward instead of waiting. That made the guardian tangle the thread and turned the meeting from tense to frightening."
        ))
    qa.append((
        f"How was the conflict solved?",
        f"{hero.id} did not fight the guardian. {hero.pronoun().capitalize()} offered {offering.phrase} and spoke with respect, which showed {hero.pronoun('possessive')} real purpose."
    ))
    qa.append((
        f"What happened after {hero.id} brought back {mystery.item_the}?",
        f"{hero.id} returned it to {mystery.source_the}, and the wounded place began to recuperate. {mystery.ending_image}"
    ))
    qa.append((
        f"What did {elder.id} want {hero.id} to learn?",
        f"{elder.id} wanted {hero.id} to see that curiosity is good, but it must walk with patience and kindness. That is why the mystery was solved by listening instead of grabbing."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mystery = world.facts["mystery"]
    tags = {"thread", "curiosity", "gift"}
    if mystery.id == "silent_spring":
        tags.add("spring")
    elif mystery.id == "moon_brazier":
        tags.add("fire")
    else:
        tags.add("door")
    if world.facts["temperament"] == "patient":
        tags.add("patience")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("laurel_vale", "silent_spring", "otter", "song", "Ione", "girl", "mother", "patient"),
    StoryParams("amber_hill", "moon_brazier", "swallow", "bread", "Timon", "boy", "father", "hasty"),
    StoryParams("reed_marsh", "buried_door", "mole", "water", "Mira", "girl", "mother", "patient"),
    StoryParams("amber_hill", "buried_door", "goat", "bread", "Orin", "boy", "father", "hasty"),
]


ASP_RULES = r"""
valid(M, H, O) :- mystery(M), helper(H), offering(O),
                  terrain(M, T), domain(H, T), appeases(O, G), guardian(M, G).
valid(M, H, O) :- mystery(M), helper(H), offering(O),
                  domain(H, open), appeases(O, G), guardian(M, G).

smooth :- temperament(patient).
strained :- temperament(hasty).

outcome(smooth) :- smooth.
outcome(strained) :- strained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("terrain", mid, m.terrain))
        lines.append(asp.fact("guardian", mid, m.guardian_label))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for d in sorted(h.domains):
            lines.append(asp.fact("domain", hid, d))
    for oid, o in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        for g in sorted(o.guardians):
            lines.append(asp.fact("appeases", oid, g))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("temperament", params.temperament)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for s in range(80):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(p)
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
            raise StoryError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a child follows a sacred thread to solve a mystery."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--temperament", choices=["patient", "hasty"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.mystery:
        helper = HELPERS[args.helper]
        mystery = MYSTERIES[args.mystery]
        if not helper_fits(helper, mystery):
            raise StoryError(explain_helper(helper, mystery))
    if args.offering and args.mystery:
        offering = OFFERINGS[args.offering]
        mystery = MYSTERIES[args.mystery]
        if not offering_fits(offering, mystery):
            raise StoryError(explain_offering(offering, mystery))

    combos = [
        c for c in valid_combos()
        if (args.mystery is None or c[0] == args.mystery)
        and (args.helper is None or c[1] == args.helper)
        and (args.offering is None or c[2] == args.offering)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, helper_id, offering_id = rng.choice(sorted(combos))
    realm_id = args.realm or rng.choice(sorted(REALMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder = args.elder or rng.choice(["mother", "father"])
    temperament = args.temperament or rng.choice(["patient", "hasty"])
    return StoryParams(realm_id, mystery_id, helper_id, offering_id, name, gender, elder, temperament)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        REALMS[params.realm],
        MYSTERIES[params.mystery],
        HELPERS[params.helper],
        OFFERINGS[params.offering],
        params.name,
        params.gender,
        params.elder,
        params.temperament,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, helper, offering) combos:\n")
        for mystery, helper, offering in combos:
            print(f"  {mystery:14} {helper:8} {offering}")
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
                f"### {p.name}: {p.mystery} with {p.helper} and {p.offering} "
                f"({p.realm}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
