#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/register_relay_friendship_reconciliation_magic_rhyming_story.py
============================================================================================

A standalone storyworld about two friends, a relay sign-up register, a magical
mix-up, and a warm reconciliation. The prose aims for a gentle rhyming-story
feel while still being driven by a small simulated world model.

Premise
-------
Two children want to join a relay together. Their names go onto a register.
A burst of magic smudges or hides the names. One child misunderstands what
happened and feels hurt. A sensible magical repair reveals the truth, the
friends reconcile, and they run side by side at the end.

Reasonableness gate
-------------------
Not every magical repair works on every kind of register or every kind of
accident. This world only tells stories where the chosen repair can actually
restore or reveal the lost sign-up.

Run it
------
    python storyworlds/worlds/gpt-5.4/register_relay_friendship_reconciliation_magic_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/register_relay_friendship_reconciliation_magic_rhyming_story.py --register chalkboard --magic sneeze_sparkles --repair echo_rhyme
    python storyworlds/worlds/gpt-5.4/register_relay_friendship_reconciliation_magic_rhyming_story.py --register ribbon_board --repair moon_ink
    python storyworlds/worlds/gpt-5.4/register_relay_friendship_reconciliation_magic_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/register_relay_friendship_reconciliation_magic_rhyming_story.py --verify
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
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class RegisterCfg:
    id: str
    label: str
    phrase: str
    material: str
    place: str
    line_word: str
    repair_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicCfg:
    id: str
    label: str
    phrase: str
    effect: str
    cue: str
    hides_mode: str
    repair_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairCfg:
    id: str
    label: str
    phrase: str
    method_text: str
    reveal_text: str
    restore_text: str
    works_on: set[str] = field(default_factory=set)
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


def _r_hurt_distance(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["hurt"] < THRESHOLD:
            continue
        sig = ("distance", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["distance"] += 1
        out.append("__distance__")
    return out


def _r_truth_softens(world: World) -> list[str]:
    out: list[str] = []
    if "friend_a" not in world.entities or "friend_b" not in world.entities:
        return out
    a = world.get("friend_a")
    b = world.get("friend_b")
    register = world.get("register")
    if register.meters["restored"] < THRESHOLD:
        return out
    sig = ("soften", "pair")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    if a.memes["hurt"] >= THRESHOLD:
        a.memes["hurt"] = 0.0
    if b.memes["hurt"] >= THRESHOLD:
        b.memes["hurt"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_distance", tag="social", apply=_r_hurt_distance),
    Rule(name="truth_softens", tag="social", apply=_r_truth_softens),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(s for s in result if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(register: RegisterCfg, magic: MagicCfg, repair: RepairCfg) -> bool:
    needed = set(register.repair_tags) | set(magic.repair_tags)
    return needed.issubset(repair.works_on)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for reg_id, reg in REGISTERS.items():
        for magic_id, magic in MAGICS.items():
            for repair_id, repair in REPAIRS.items():
                if valid_combo(reg, magic, repair):
                    combos.append((reg_id, magic_id, repair_id))
    return combos


def explain_rejection(register: RegisterCfg, magic: MagicCfg, repair: RepairCfg) -> str:
    need = sorted(set(register.repair_tags) | set(magic.repair_tags))
    return (
        f"(No story: {repair.label} cannot sensibly fix a {register.label} after "
        f"{magic.label}. This repair would need to handle {', '.join(need)}.)"
    )


def predict_repair(register: RegisterCfg, magic: MagicCfg, repair: RepairCfg) -> dict:
    return {
        "works": valid_combo(register, magic, repair),
        "need": sorted(set(register.repair_tags) | set(magic.repair_tags)),
    }


def opening(world: World, a: Entity, b: Entity, teacher: Entity, event: Entity, register: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At morning school beneath a sky so bright, {a.id} and {b.id} skipped with light delight. "
        f"Today was {event.phrase}, all ribbons, cheers, and play, and {teacher.label_word} smiled to start the day."
    )
    world.say(
        f"By {register.attrs['place']} stood {register.phrase}, neat and grand to see. "
        f'"Pick your teams for the relay, dear hearts, and write your names with glee," said {teacher.label_word}.'
    )


def register_together(world: World, a: Entity, b: Entity, register: Entity, baton: Entity) -> None:
    register.attrs["signed_names"] = [a.id, b.id]
    register.meters["signed"] += 1
    a.attrs["teammate"] = b.id
    b.attrs["teammate"] = a.id
    baton.attrs["planned_pair"] = [a.id, b.id]
    world.say(
        f'{a.id} wrote first with careful loops, then passed the chalk along. '
        f'{b.id} added one more twirling line and hummed a relay song.'
    )
    world.say(
        f'"We run together, you and me, quick feet and steady sway. '
        f"We start as friends, we finish friends, and pass the baton all the way."'
    )


def magic_mishap(world: World, a: Entity, b: Entity, register: Entity, magic: MagicCfg) -> None:
    register.meters["hidden"] += 1
    register.attrs["visible_names"] = []
    world.facts["accident_who"] = a.id if a.memes["eager"] >= b.memes["eager"] else b.id
    world.say(
        f"But then {magic.cue}, and {magic.phrase} gave a sudden little swish. "
        f"{magic.effect} across the register danced exactly where they'd written their wish."
    )
    if magic.hides_mode == "smudge":
        world.say(
            "The tidy letters blurred to curls, then slid in cloudy weather. "
            "Where two bright names had proudly shone, no names could stay together."
        )
    elif magic.hides_mode == "vanish":
        world.say(
            "The tidy letters blinked away like minnows in a stream. "
            "The line went pale and silver-thin, as if erased in dream."
        )
    else:
        world.say(
            "The names tucked under shining threads that fluttered in the air. "
            "The line looked blank to worried eyes, though hidden writing lingered there."
        )
    propagate(world, narrate=False)


def misunderstanding(world: World, a: Entity, b: Entity, register: Entity) -> None:
    b.memes["hurt"] += 1
    a.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{b.id} looked at the register and felt a stinging sting. '
        f'"Did you sign without me after all? That is a hurtful thing."'
    )
    world.say(
        f'{a.id} blinked hard and shook {a.pronoun("possessive")} head. '
        f'"No, truly, I wrote both names," {a.pronoun()} said.'
    )
    if b.memes["distance"] >= THRESHOLD:
        world.say(
            f"But {b.id} took one backward step, with eyes no longer merry. "
            "A friendship can feel very small when hearts grow sore and wary."
        )


def helper_intervenes(world: World, teacher: Entity, register_cfg: RegisterCfg, magic: MagicCfg, repair: RepairCfg) -> None:
    pred = predict_repair(register_cfg, magic, repair)
    world.facts["predicted_repair"] = pred
    world.say(
        f"{teacher.label_word.capitalize()} knelt beside them both and spoke in tones so kind, "
        f'"Before we guess the worst of friends, let patient magic find."'
    )
    world.say(
        f"{teacher.label_word.capitalize()} chose {repair.phrase} and began {repair.method_text}."
    )


def apply_repair(world: World, a: Entity, b: Entity, register: Entity, repair: RepairCfg) -> None:
    register.meters["restored"] += 1
    register.meters["hidden"] = 0.0
    register.attrs["visible_names"] = [a.id, b.id]
    propagate(world, narrate=False)
    world.say(repair.reveal_text)
    world.say(repair.restore_text.format(a=a.id, b=b.id))
    world.say(
        f"There on the register, plain at last, both names shone brave and clear: "
        f"{a.id} and {b.id} for the relay, side by side and near."
    )


def reconcile(world: World, a: Entity, b: Entity) -> None:
    a.memes["care"] += 1
    b.memes["care"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f'{b.id} let out a shaky breath. "I thought you left me out." '
        f'"I am sorry," {b.pronoun()} said. "I should have asked, not pout."'
    )
    world.say(
        f'{a.id} reached out a waiting hand. "I am sorry too for the fright. '
        f'I should have called for help at once and set the muddle right."'
    )
    world.say(
        "Their fingers met, the worry fled, and warm trust fluttered back. "
        "A mended heart can glow again and pull a friendship on its track."
    )


def run_relay(world: World, a: Entity, b: Entity, event: Entity, baton: Entity) -> None:
    baton.meters["passed"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Soon came {event.label}, bright and brisk, along the chalky way. "
        f"{a.id} ran first, then passed the baton to {b.id} without delay."
    )
    world.say(
        f"They raced in rhythm, laugh by laugh, in sunshine soft and sweet. "
        "The crowd clapped out a happy beat beneath their flying feet."
    )
    world.say(
        "And when they crossed the finish line, they grinned in golden light: "
        "the register was right again, and so was friendship's kite."
    )


def tell(
    event_id: str,
    register_id: str,
    magic_id: str,
    repair_id: str,
    friend_a_name: str,
    friend_a_gender: str,
    friend_b_name: str,
    friend_b_gender: str,
    teacher_type: str,
    eager_trait: str,
    careful_trait: str,
) -> World:
    event_cfg = EVENTS[event_id]
    register_cfg = REGISTERS[register_id]
    magic_cfg = MAGICS[magic_id]
    repair_cfg = REPAIRS[repair_id]
    if not valid_combo(register_cfg, magic_cfg, repair_cfg):
        raise StoryError(explain_rejection(register_cfg, magic_cfg, repair_cfg))

    world = World()
    a = world.add(Entity(
        id="friend_a",
        kind="character",
        type=friend_a_gender,
        label=friend_a_name,
        role="friend_a",
        traits=[eager_trait],
    ))
    b = world.add(Entity(
        id="friend_b",
        kind="character",
        type=friend_b_gender,
        label=friend_b_name,
        role="friend_b",
        traits=[careful_trait],
    ))
    teacher = world.add(Entity(
        id="teacher",
        kind="character",
        type=teacher_type,
        label="the teacher",
        role="teacher",
    ))
    event = world.add(Entity(
        id="event",
        type="event",
        label=event_cfg["label"],
        phrase=event_cfg["phrase"],
        attrs=event_cfg,
        tags={"relay"},
    ))
    register = world.add(Entity(
        id="register",
        type="register",
        label=register_cfg.label,
        phrase=register_cfg.phrase,
        attrs={"material": register_cfg.material, "place": register_cfg.place, "line_word": register_cfg.line_word},
        tags=set(register_cfg.tags),
    ))
    baton = world.add(Entity(
        id="baton",
        type="baton",
        label="baton",
        phrase="a ribbon-wrapped relay baton",
        tags={"relay"},
    ))

    a.id = friend_a_name
    b.id = friend_b_name
    teacher.id = "Ms. Wren" if teacher_type == "teacher" else "Parent"

    a.memes["eager"] = 2.0
    b.memes["eager"] = 1.0
    b.memes["trust"] = 1.0
    a.memes["trust"] = 1.0

    opening(world, a, b, teacher, event, register)
    register_together(world, a, b, register, baton)

    world.para()
    magic_mishap(world, a, b, register, magic_cfg)
    misunderstanding(world, a, b, register)

    world.para()
    helper_intervenes(world, teacher, register_cfg, magic_cfg, repair_cfg)
    apply_repair(world, a, b, register, repair_cfg)
    reconcile(world, a, b)

    world.para()
    run_relay(world, a, b, event, baton)

    world.facts.update(
        friend_a=a,
        friend_b=b,
        teacher=teacher,
        event=event,
        register=register,
        register_cfg=register_cfg,
        magic_cfg=magic_cfg,
        repair_cfg=repair_cfg,
        baton=baton,
        misread=b.memes["distance"] >= THRESHOLD or True,
        repaired=register.meters["restored"] >= THRESHOLD,
        reconciled=a.memes["friendship"] >= THRESHOLD and b.memes["friendship"] >= THRESHOLD,
    )
    return world


EVENTS = {
    "school_yard": {
        "label": "the school-yard relay",
        "phrase": "the school-yard relay day",
    },
    "garden_track": {
        "label": "the garden relay",
        "phrase": "the garden relay afternoon",
    },
    "lantern_run": {
        "label": "the lantern relay",
        "phrase": "the lantern relay fair",
    },
}

REGISTERS = {
    "chalkboard": RegisterCfg(
        id="chalkboard",
        label="chalkboard register",
        phrase="a tall chalkboard register",
        material="chalk",
        place="the hopscotch wall",
        line_word="line",
        repair_tags={"surface", "chalk"},
        tags={"register", "chalkboard"},
    ),
    "paper_sheet": RegisterCfg(
        id="paper_sheet",
        label="paper register",
        phrase="a paper register clipped to a stand",
        material="paper",
        place="the red beanbag stand",
        line_word="row",
        repair_tags={"surface", "paper"},
        tags={"register", "paper"},
    ),
    "ribbon_board": RegisterCfg(
        id="ribbon_board",
        label="ribbon register",
        phrase="a ribbon-woven register board",
        material="ribbon",
        place="the flower fence",
        line_word="ribbon row",
        repair_tags={"surface", "ribbon"},
        tags={"register", "ribbon"},
    ),
}

MAGICS = {
    "sneeze_sparkles": MagicCfg(
        id="sneeze_sparkles",
        label="sneeze sparkles",
        phrase="a sneeze of silver sparkles",
        effect="Shimmering dust",
        cue="a tiny enchanted sneeze skipped from the breeze",
        hides_mode="smudge",
        repair_tags={"smudge"},
        tags={"magic", "sparkles"},
    ),
    "hiccup_hum": MagicCfg(
        id="hiccup_hum",
        label="a hiccup hum",
        phrase="a hiccup of humming moonlight",
        effect="Moonlit ripples",
        cue="a humming hiccup twinkled from the inkpot nearby",
        hides_mode="vanish",
        repair_tags={"vanish"},
        tags={"magic", "moonlight"},
    ),
    "wand_whirl": MagicCfg(
        id="wand_whirl",
        label="wand whirl",
        phrase="a small wand-whirl of ribbon light",
        effect="Ribbony light",
        cue="a practice wand spun too quickly by the craft table",
        hides_mode="veil",
        repair_tags={"veil"},
        tags={"magic", "wand"},
    ),
}

REPAIRS = {
    "echo_rhyme": RepairCfg(
        id="echo_rhyme",
        label="echo rhyme",
        phrase="an echo rhyme",
        method_text="a soft couplet that called back the last true names spoken there",
        reveal_text="The board gave back a humming rhyme, as clear as chiming weather.",
        restore_text='"{a} and {b}," it sang aloud, "these friends signed up together."',
        works_on={"surface", "smudge", "vanish"},
        tags={"magic", "reconciliation"},
    ),
    "moon_ink": RepairCfg(
        id="moon_ink",
        label="moon ink",
        phrase="a drop of moon ink",
        method_text="one bright silver drop across the empty place",
        reveal_text="The missing strokes returned in pale blue loops that brightened with the air.",
        restore_text="Each letter settled back in place for {a} and {b} to share.",
        works_on={"surface", "paper", "chalk", "smudge", "vanish"},
        tags={"magic", "repair"},
    ),
    "kindness_chime": RepairCfg(
        id="kindness_chime",
        label="kindness chime",
        phrase="a kindness chime",
        method_text="three gentle notes and a promise not to blame before the truth was known",
        reveal_text="The hidden writing glowed like thread when kindness rang nearby.",
        restore_text="On ribbon rows appeared the names of {a} and {b}, side by side and high.",
        works_on={"surface", "ribbon", "veil"},
        tags={"magic", "friendship"},
    ),
}


GIRL_NAMES = ["Lila", "Mina", "Nora", "Poppy", "Tessa", "Ruby", "Ada", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Jude", "Luca", "Ben", "Eli"]
TRAITS_EAGER = ["bouncy", "hopeful", "bright", "eager"]
TRAITS_CAREFUL = ["gentle", "careful", "thoughtful", "steady"]


@dataclass
class StoryParams:
    event: str
    register: str
    magic: str
    repair: str
    friend_a_name: str
    friend_a_gender: str
    friend_b_name: str
    friend_b_gender: str
    teacher_type: str
    eager_trait: str
    careful_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        event="school_yard",
        register="chalkboard",
        magic="sneeze_sparkles",
        repair="echo_rhyme",
        friend_a_name="Lila",
        friend_a_gender="girl",
        friend_b_name="Milo",
        friend_b_gender="boy",
        teacher_type="teacher",
        eager_trait="bouncy",
        careful_trait="gentle",
    ),
    StoryParams(
        event="garden_track",
        register="paper_sheet",
        magic="hiccup_hum",
        repair="moon_ink",
        friend_a_name="Owen",
        friend_a_gender="boy",
        friend_b_name="Ruby",
        friend_b_gender="girl",
        teacher_type="teacher",
        eager_trait="hopeful",
        careful_trait="careful",
    ),
    StoryParams(
        event="lantern_run",
        register="ribbon_board",
        magic="wand_whirl",
        repair="kindness_chime",
        friend_a_name="Poppy",
        friend_a_gender="girl",
        friend_b_name="Theo",
        friend_b_gender="boy",
        teacher_type="teacher",
        eager_trait="bright",
        careful_trait="steady",
    ),
    StoryParams(
        event="school_yard",
        register="paper_sheet",
        magic="sneeze_sparkles",
        repair="moon_ink",
        friend_a_name="Finn",
        friend_a_gender="boy",
        friend_b_name="Ivy",
        friend_b_gender="girl",
        teacher_type="teacher",
        eager_trait="eager",
        careful_trait="thoughtful",
    ),
]


KNOWLEDGE = {
    "register": [
        (
            "What is a register?",
            "A register is a list where people write their names to join something. It helps everyone see who is taking part."
        )
    ],
    "relay": [
        (
            "What is a relay?",
            "A relay is a race where teammates take turns. One runner passes something, often a baton, to the next runner."
        )
    ],
    "baton": [
        (
            "What is a baton in a relay?",
            "A baton is the object runners pass from one teammate to another. Passing it carefully helps the team keep going."
        )
    ],
    "friendship": [
        (
            "How can friendship heal after a misunderstanding?",
            "Friends can slow down, ask what really happened, and listen honestly. Saying sorry and telling the truth helps trust grow back."
        )
    ],
    "magic": [
        (
            "Can magic in a story help people tell the truth?",
            "Yes, in a story magic can reveal hidden things or fix a mix-up. But the kindest part is still how people choose to act after the truth appears."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    reg = f["register_cfg"]
    magic = f["magic_cfg"]
    return [
        f'Write a gentle rhyming story for a 3-to-5-year-old that includes the words "register" and "relay".',
        f"Tell a magical friendship story where {a.id} and {b.id} sign a register for a relay together, then a mix-up makes one friend feel left out until the truth is revealed.",
        f"Write a rhyming reconciliation tale where {magic.label} hides names on a {reg.label}, and the ending shows two friends running happily together again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    teacher = f["teacher"]
    register_cfg = f["register_cfg"]
    magic_cfg = f["magic_cfg"]
    repair_cfg = f["repair_cfg"]
    event = f["event"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, and {teacher.id}, who helps them at school. The story follows how their friendship wobbles and then mends."
        ),
        (
            "Why were they using the register?",
            f"They were using the register to sign up for {event.label}. The register showed that they wanted to run the relay as a team."
        ),
        (
            f"What went wrong at the register?",
            f"{magic_cfg.phrase.capitalize()} hid the names they had written on the {register_cfg.label}. When the writing disappeared, {b.id} thought {a.id} had left {b.pronoun('object')} out."
        ),
        (
            f"Why did {b.id} feel hurt?",
            f"{b.id} looked at the blank register and believed the team plan had been broken. The hurt came from a misunderstanding, not from unkindness."
        ),
        (
            f"How was the problem fixed?",
            f"{teacher.id} used {repair_cfg.phrase} to reveal what had really been written. Once both names showed again, the truth made it possible for the friends to talk and reconcile."
        ),
        (
            "How did the story end?",
            f"It ended with both friends running the relay together and passing the baton safely. The last image proves that the register was repaired and the friendship was repaired too."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = {"register", "relay", "baton", "friendship", "magic"}
    for key in ["register", "relay", "baton", "friendship", "magic"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
needs(Reg, Mag, Tag) :- reg_need(Reg, Tag).
needs(Reg, Mag, Tag) :- magic_need(Mag, Tag).

missing(Reg, Mag, Rep) :- needs(Reg, Mag, Tag), not works(Rep, Tag).
valid(Reg, Mag, Rep) :- register(Reg), magic(Mag), repair(Rep), not missing(Reg, Mag, Rep).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for reg_id, reg in REGISTERS.items():
        lines.append(asp.fact("register", reg_id))
        for tag in sorted(reg.repair_tags):
            lines.append(asp.fact("reg_need", reg_id, tag))
    for magic_id, magic in MAGICS.items():
        lines.append(asp.fact("magic", magic_id))
        for tag in sorted(magic.repair_tags):
            lines.append(asp.fact("magic_need", magic_id, tag))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for tag in sorted(repair.works_on):
            lines.append(asp.fact("works", repair_id, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical register mix-up before a relay, ending in friendship and reconciliation."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--register", choices=REGISTERS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--teacher", choices=["teacher"], dest="teacher_type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.register and args.magic and args.repair:
        reg = REGISTERS[args.register]
        magic = MAGICS[args.magic]
        repair = REPAIRS[args.repair]
        if not valid_combo(reg, magic, repair):
            raise StoryError(explain_rejection(reg, magic, repair))

    combos = [
        c for c in valid_combos()
        if (args.register is None or c[0] == args.register)
        and (args.magic is None or c[1] == args.magic)
        and (args.repair is None or c[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    register_id, magic_id, repair_id = rng.choice(sorted(combos))
    event_id = args.event or rng.choice(sorted(EVENTS))
    gender_a = rng.choice(["girl", "boy"])
    gender_b = rng.choice(["girl", "boy"])
    name_a = _pick_name(rng, gender_a)
    name_b = _pick_name(rng, gender_b, avoid=name_a)
    return StoryParams(
        event=event_id,
        register=register_id,
        magic=magic_id,
        repair=repair_id,
        friend_a_name=name_a,
        friend_a_gender=gender_a,
        friend_b_name=name_b,
        friend_b_gender=gender_b,
        teacher_type=args.teacher_type or "teacher",
        eager_trait=rng.choice(TRAITS_EAGER),
        careful_trait=rng.choice(TRAITS_CAREFUL),
    )


def generate(params: StoryParams) -> StorySample:
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.register not in REGISTERS:
        raise StoryError(f"(Unknown register: {params.register})")
    if params.magic not in MAGICS:
        raise StoryError(f"(Unknown magic: {params.magic})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    world = tell(
        event_id=params.event,
        register_id=params.register,
        magic_id=params.magic,
        repair_id=params.repair,
        friend_a_name=params.friend_a_name,
        friend_a_gender=params.friend_a_gender,
        friend_b_name=params.friend_b_name,
        friend_b_gender=params.friend_b_gender,
        teacher_type=params.teacher_type,
        eager_trait=params.eager_trait,
        careful_trait=params.careful_trait,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (register, magic, repair) combos:\n")
        for register_id, magic_id, repair_id in combos:
            print(f"  {register_id:12} {magic_id:16} {repair_id}")
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
            header = f"### {p.friend_a_name} & {p.friend_b_name}: {p.register}, {p.magic}, {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
