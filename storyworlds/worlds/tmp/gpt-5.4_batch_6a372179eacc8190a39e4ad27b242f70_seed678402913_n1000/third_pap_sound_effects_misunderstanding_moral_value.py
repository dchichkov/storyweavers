#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/third_pap_sound_effects_misunderstanding_moral_value.py
==================================================================================

A small slice-of-life storyworld about a child who hears a soft "pap, pap, pap,"
misunderstands what another child is doing, and learns to ask before blaming.

The world model keeps a tiny household simulation:
- a grown-up prepares three snacks
- one child is trusted with the third snack
- a helper makes an innocent sound nearby
- the first child jumps to the wrong conclusion
- the misunderstanding is cleared up
- the children repair the moment with honesty, apology, and kindness

The key constraint is simple and explicit: not every sound can reasonably be
misheard as every action.  The Python gate and the inline ASP twin both insist
that a sound family and location must fit the misunderstanding.

Run it
------
    python storyworlds/worlds/gpt-5.4/third_pap_sound_effects_misunderstanding_moral_value.py
    python storyworlds/worlds/gpt-5.4/third_pap_sound_effects_misunderstanding_moral_value.py --snack pancake --sound spoon_tap --mistake made_mess
    python storyworlds/worlds/gpt-5.4/third_pap_sound_effects_misunderstanding_moral_value.py --sound wet_slippers --mistake made_mess
    python storyworlds/worlds/gpt-5.4/third_pap_sound_effects_misunderstanding_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/third_pap_sound_effects_misunderstanding_moral_value.py --qa --json
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

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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


# ---------------------------------------------------------------------------
# Domain configs.
# ---------------------------------------------------------------------------
@dataclass
class Snack:
    id: str = ""
    label: str = ""
    plural_label: str = ""
    one_phrase: str = ""
    tray_phrase: str = ""
    warm_detail: str = ""
    count_word: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundSource:
    id: str = ""
    label: str = ""
    noise: str = ""
    cause: str = ""
    reveal: str = ""
    location: str = ""
    family: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str = ""
    thought: str = ""
    accuse_line: str = ""
    correction: str = ""
    family: str = ""
    locations: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and forward-chaining rules.
# ---------------------------------------------------------------------------
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


def _r_worry(world: World) -> list[str]:
    heard = world.get("sound")
    lead = world.get("lead")
    if heard.meters["heard"] < THRESHOLD or lead.memes["responsibility"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["worry"] += 1
    return []


def _r_hurt(world: World) -> list[str]:
    helper = world.get("helper")
    lead = world.get("lead")
    if helper.memes["accused"] < THRESHOLD or helper.memes["innocent"] < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    lead.memes["certainty"] += 1
    return []


def _r_guilt(world: World) -> list[str]:
    lead = world.get("lead")
    helper = world.get("helper")
    if world.get("truth").meters["shown"] < THRESHOLD and helper.meters["truth_shown"] < THRESHOLD:
        return []
    if helper.memes["accused"] < THRESHOLD:
        return []
    sig = ("guilt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["guilt"] += 1
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="guilt", tag="moral", apply=_r_guilt),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def mistake_fits(sound: SoundSource, mistake: Mistake) -> bool:
    return sound.family == mistake.family and sound.location in mistake.locations


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for snack_id in SNACKS:
        for sound_id, sound in SOUNDS.items():
            for mistake_id, mistake in MISTAKES.items():
                if mistake_fits(sound, mistake):
                    combos.append((snack_id, sound_id, mistake_id))
    return sorted(combos)


def explain_rejection(sound: SoundSource, mistake: Mistake) -> str:
    if sound.family != mistake.family:
        return (
            f"(No story: {sound.label} makes a {sound.family}-type sound, but the "
            f"mistake '{mistake.id}' expects a {mistake.family}-type clue. The "
            f"misunderstanding would feel forced instead of believable.)"
        )
    return (
        f"(No story: {sound.label} happens in the {sound.location}, but the mistake "
        f"'{mistake.id}' only makes sense in {sorted(mistake.locations)}. The child "
        f"would not honestly jump to that conclusion from that place.)"
    )


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------
def kitchen_setup(world: World, lead: Entity, helper: Entity, parent: Entity, snack: Snack) -> None:
    lead.memes["care"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f"After school, {lead.id} and {helper.id} stood in the warm kitchen with "
        f"{lead.pronoun('possessive')} {parent.label_word}. On the rack sat three "
        f"{snack.plural_label}, and the whole room smelled of {snack.warm_detail}."
    )
    world.say(
        f'"One for us, one for next door, and the third {snack.label} goes on the '
        f'blue plate," {parent.label_word.capitalize()} said.'
    )
    world.get("tray").meters["loaded"] = 3
    world.get("third").meters["reserved"] = 1
    lead.memes["responsibility"] += 1
    world.say(
        f"{lead.id} felt very important carrying the blue plate and keeping an eye "
        f"on the third {snack.label}."
    )


def assign_tasks(world: World, lead: Entity, helper: Entity, snack: Snack) -> None:
    world.say(
        f"{helper.id} stayed by the table to help with napkins and cups while "
        f"{lead.id} counted softly, \"one, two, three.\""
    )
    world.say(
        f"The third {snack.label} looked especially neat, sitting in the middle of "
        f"the plate like a tiny promise."
    )


def hear_sound(world: World, lead: Entity, sound: SoundSource) -> None:
    world.get("sound").meters["heard"] += 1
    world.facts["heard_noise"] = sound.noise
    propagate(world, narrate=False)
    world.say(
        f"Then a little sound came from the {sound.location}: "
        f'"{sound.noise}"'
    )
    if lead.memes["worry"] >= THRESHOLD:
        world.say(
            f"{lead.id} tightened {lead.pronoun('possessive')} hands around the blue plate. "
            f"The soft noise made {lead.pronoun('object')} worry about the snack right away."
        )


def misunderstand(world: World, lead: Entity, helper: Entity, mistake: Mistake, snack: Snack) -> None:
    lead.memes["suspicion"] += 1
    world.get("third").meters["hidden"] += 1
    world.say(
        f"In that one small moment, {lead.id} thought {mistake.thought}."
    )
    world.say(
        f'{lead.id} pulled the plate a little closer and blurted, "{mistake.accuse_line}"'
    )
    helper.memes["accused"] += 1
    propagate(world, narrate=False)
    if helper.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{helper.id} blinked and went still. Being blamed for the third "
            f"{snack.label} made {helper.pronoun('object')} look surprised and hurt."
        )


def reveal_truth(world: World, lead: Entity, helper: Entity, sound: SoundSource, mistake: Mistake) -> None:
    helper.memes["innocent"] += 1
    helper.meters["truth_shown"] += 1
    world.get("truth").meters["shown"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {lead.id} looked properly and saw the real reason for the sound. "
        f"{helper.id} had only {sound.cause}."
    )
    world.say(
        f'"I was not {mistake.correction}," {helper.id} said. "{sound.reveal}"'
    )


def apology_and_lesson(world: World, lead: Entity, helper: Entity, parent: Entity, snack: Snack) -> None:
    lead.memes["honesty"] += 1
    lead.memes["kindness"] += 1
    helper.memes["forgiveness"] += 1
    world.get("third").meters["hidden"] = 0
    world.get("third").meters["shared"] += 1
    world.say(
        f"A hot blush climbed into {lead.id}'s cheeks. "
        f'"I am sorry," {lead.pronoun()} said. "I heard the pap sound and guessed before I asked."'
    )
    world.say(
        f"{parent.label_word.capitalize()} touched both children on the shoulder. "
        f'"Ears can start a story, but eyes and questions finish it," {parent.pronoun()} said. '
        f'"Next time, ask first and be fair."'
    )
    world.say(
        f"{helper.id} nodded, and the tight feeling left the room. Together they set "
        f"the third {snack.label} back in the middle of the blue plate."
    )


def ending(world: World, lead: Entity, helper: Entity, snack: Snack) -> None:
    lead.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"When they carried the plates to the door, {lead.id} let {helper.id} hold "
        f"the blue one too. This time the kitchen only had the gentle sounds of cups, "
        f"steps, and a last tiny \"pap\" from the table, and nobody minded at all."
    )
    world.say(
        f"The third {snack.label} reached its place, warm and whole, and both children "
        f"felt a little kinder than before."
    )


def tell(
    snack: Snack,
    sound: SoundSource,
    mistake: Mistake,
    *,
    lead_name: str = "Nina",
    lead_gender: str = "girl",
    helper_name: str = "Owen",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent")
    )
    world.add(Entity(id="tray", type="tray", label="blue plate"))
    world.add(Entity(id="third", type="snack", label=f"third {snack.label}"))
    world.add(Entity(id="sound", type="sound", label=sound.label))
    world.add(Entity(id="truth", type="truth", label="what really happened"))

    kitchen_setup(world, lead, helper, parent, snack)
    assign_tasks(world, lead, helper, snack)
    world.para()
    hear_sound(world, lead, sound)
    misunderstand(world, lead, helper, mistake, snack)
    world.para()
    reveal_truth(world, lead, helper, sound, mistake)
    apology_and_lesson(world, lead, helper, parent, snack)
    world.para()
    ending(world, lead, helper, snack)

    world.facts.update(
        lead=lead,
        helper=helper,
        parent=parent,
        snack=snack,
        sound_cfg=sound,
        mistake_cfg=mistake,
        accused=helper.memes["accused"] >= THRESHOLD,
        helper_hurt=helper.memes["hurt"] >= THRESHOLD,
        truth_revealed=world.get("truth").meters["shown"] >= THRESHOLD,
        apologized=lead.memes["honesty"] >= THRESHOLD,
        moral="ask_first",
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SNACKS = {
    "pancake": Snack(
        id="pancake",
        label="pancake",
        plural_label="golden pancakes",
        one_phrase="a golden pancake",
        tray_phrase="a blue plate",
        warm_detail="butter and warm milk",
        count_word="third",
        tags={"pancake", "snack"},
    ),
    "bun": Snack(
        id="bun",
        label="bun",
        plural_label="soft buns",
        one_phrase="a soft bun",
        tray_phrase="a blue plate",
        warm_detail="sweet yeast and jam",
        count_word="third",
        tags={"bun", "snack"},
    ),
    "rice_cake": Snack(
        id="rice_cake",
        label="rice cake",
        plural_label="round rice cakes",
        one_phrase="a round rice cake",
        tray_phrase="a blue plate",
        warm_detail="toasted sesame",
        count_word="third",
        tags={"rice_cake", "snack"},
    ),
}

SOUNDS = {
    "spoon_tap": SoundSource(
        id="spoon_tap",
        label="a spoon on a bowl",
        noise="pap, pap, pap",
        cause="tapped a sticky spoon against the mixing bowl to clean it",
        reveal="I was just getting the spoon clean for washing",
        location="table",
        family="sticky",
        tags={"sound_effect", "kitchen"},
    ),
    "bag_pat": SoundSource(
        id="bag_pat",
        label="a paper bag being patted flat",
        noise="pap, pap, pap",
        cause="patted the paper bag flat so the napkins would fit inside",
        reveal="I was making room in the bag for the napkins",
        location="table",
        family="paper",
        tags={"sound_effect", "paper"},
    ),
    "wet_slippers": SoundSource(
        id="wet_slippers",
        label="damp slippers on the floor",
        noise="pap, pap, pap",
        cause="walked in from the porch with damp slippers and careful little steps",
        reveal="I had wet slippers and did not want to drip on the rug",
        location="hallway",
        family="steps",
        tags={"sound_effect", "hallway"},
    ),
}

MISTAKES = {
    "stole_third": Mistake(
        id="stole_third",
        thought="the helper was sneaking a hand toward the third snack",
        accuse_line="Hey, that third one is not yours. Please do not sneak it.",
        correction="trying to take the third snack",
        family="paper",
        locations={"table"},
        tags={"misunderstanding", "fairness"},
    ),
    "made_mess": Mistake(
        id="made_mess",
        thought="the helper was squashing something sticky and making a mess near the plate",
        accuse_line="Please stop making a mess by the blue plate.",
        correction="making a mess",
        family="sticky",
        locations={"table"},
        tags={"misunderstanding", "mess"},
    ),
    "bumped_cups": Mistake(
        id="bumped_cups",
        thought="the helper was stomping too fast and bumping the cups in a hurry",
        accuse_line="Slow down. You are going to bump the cups.",
        correction="racing into the cups",
        family="steps",
        locations={"hallway", "table"},
        tags={"misunderstanding", "carefulness"},
    ),
}

GIRL_NAMES = ["Nina", "Maya", "Lila", "June", "Ava", "Ruby", "Tess", "Mina"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Ben", "Milo", "Theo", "Finn", "Sam"]


# ---------------------------------------------------------------------------
# StoryParams must appear before CURATED / resolve / generate.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    snack: str
    sound: str
    mistake: str
    lead_name: str
    lead_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "sound_effect": [
        (
            "What is a sound effect in a story?",
            "A sound effect is a word or phrase that helps you hear a noise in your mind. "
            "Words like 'pap, pap, pap' make a scene feel close and real."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what is going on, but they are wrong. "
            "It often gets better when people ask questions and listen carefully."
        )
    ],
    "ask_first": [
        (
            "Why is it good to ask before blaming someone?",
            "Asking first gives you a chance to learn what really happened. "
            "It helps you be fair and keeps small mistakes from turning into hurt feelings."
        )
    ],
    "apology": [
        (
            "Why does saying sorry matter?",
            "A real apology shows that you understand the hurt you caused. "
            "It helps people trust each other again."
        )
    ],
    "pancake": [
        (
            "What is a pancake?",
            "A pancake is a soft, flat cake cooked on a hot pan or griddle. "
            "People often eat it warm."
        )
    ],
    "bun": [
        (
            "What is a bun?",
            "A bun is a small round bread. "
            "It can be plain or sweet, and it is easy to share at snack time."
        )
    ],
    "rice_cake": [
        (
            "What is a rice cake?",
            "A rice cake is a small cake made from rice. "
            "Some are chewy and soft, and some are toasted and crisp."
        )
    ],
}
KNOWLEDGE_ORDER = ["sound_effect", "misunderstanding", "ask_first", "apology", "pancake", "bun", "rice_cake"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead, helper, snack, sound = f["lead"], f["helper"], f["snack"], f["sound_cfg"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "third" and "pap".',
        f"Tell a homey story where {lead.id} hears {sound.noise} and misunderstands what {helper.id} is doing near the third {snack.label}.",
        "Write a story about asking before blaming, with a small kitchen sound, a misunderstanding, and a kind apology at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead, helper, parent = f["lead"], f["helper"], f["parent"]
    snack, sound, mistake = f["snack"], f["sound_cfg"], f["mistake_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {helper.id} helping in the kitchen with {lead.pronoun('possessive')} {pw}. "
            f"They were getting three {snack.plural_label} ready."
        ),
        (
            f"Why did the third {snack.label} matter so much to {lead.id}?",
            f"{lead.id} had been trusted to watch the blue plate and keep the third {snack.label} safe. "
            f"That special job is why the small noise made {lead.pronoun('object')} worry so fast."
        ),
        (
            f"What sound did {lead.id} hear, and what mistake did {lead.pronoun()} make?",
            f"{lead.id} heard '{sound.noise}' from the {sound.location}. "
            f"{lead.pronoun().capitalize()} guessed that {mistake.thought}, even though that was not true."
        ),
    ]
    if f.get("truth_revealed"):
        qa.append(
            (
                f"What was really making the pap sound?",
                f"The sound came because {helper.id} had only {sound.cause}. "
                f"The noise was innocent, but it sounded suspicious before {lead.id} looked carefully."
            )
        )
    if f.get("apologized"):
        qa.append(
            (
                f"What did {lead.id} do after learning the truth?",
                f"{lead.id} said sorry and admitted that {lead.pronoun()} had guessed too quickly. "
                f"That apology mattered because {helper.id} had been hurt by the unfair blame."
            )
        )
        qa.append(
            (
                "What lesson did the family learn?",
                "They learned to ask first and blame later, or not at all. "
                "The story shows that a quick question can be kinder than a quick accusation."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sound_effect", "misunderstanding", "ask_first", "apology", f["snack"].id}
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        snack="pancake",
        sound="spoon_tap",
        mistake="made_mess",
        lead_name="Nina",
        lead_gender="girl",
        helper_name="Owen",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        snack="bun",
        sound="bag_pat",
        mistake="stole_third",
        lead_name="Maya",
        lead_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="father",
    ),
    StoryParams(
        snack="rice_cake",
        sound="wet_slippers",
        mistake="bumped_cups",
        lead_name="Theo",
        lead_gender="boy",
        helper_name="June",
        helper_gender="girl",
        parent="mother",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(S, M) :- sound_family(S, F), mistake_family(M, F), sound_location(S, L), mistake_location(M, L).
valid(Sn, S, M) :- snack(Sn), sound(S), mistake(M), fits(S, M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for snack_id in SNACKS:
        lines.append(asp.fact("snack", snack_id))
    for sound_id, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sound_id))
        lines.append(asp.fact("sound_family", sound_id, sound.family))
        lines.append(asp.fact("sound_location", sound_id, sound.location))
    for mistake_id, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", mistake_id))
        lines.append(asp.fact("mistake_family", mistake_id, mistake.family))
        for loc in sorted(mistake.locations):
            lines.append(asp.fact("mistake_location", mistake_id, loc))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    # Smoke-test ordinary generation and emission.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    # Exercise a few random valid scenarios too.
    tried = 0
    for seed in range(5):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated blank story.)")
            tried += 1
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    if tried:
        print(f"OK: generated {tried} random smoke-test stories.")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a soft 'pap' sound, a misunderstanding, and a kind apology."
    )
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.mistake:
        sound = SOUNDS[args.sound]
        mistake = MISTAKES[args.mistake]
        if not mistake_fits(sound, mistake):
            raise StoryError(explain_rejection(sound, mistake))

    combos = [
        combo for combo in valid_combos()
        if (args.snack is None or combo[0] == args.snack)
        and (args.sound is None or combo[1] == args.sound)
        and (args.mistake is None or combo[2] == args.mistake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, sound_id, mistake_id = rng.choice(combos)
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=lead_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        snack=snack_id,
        sound=sound_id,
        mistake=mistake_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.mistake not in MISTAKES:
        raise StoryError(f"(Unknown mistake: {params.mistake})")

    snack = SNACKS[params.snack]
    sound = SOUNDS[params.sound]
    mistake = MISTAKES[params.mistake]
    if not mistake_fits(sound, mistake):
        raise StoryError(explain_rejection(sound, mistake))

    world = tell(
        snack=snack,
        sound=sound,
        mistake=mistake,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (snack, sound, mistake) combos:\n")
        for snack, sound, mistake in combos:
            print(f"  {snack:10} {sound:12} {mistake}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.lead_name} and {p.helper_name}: {p.snack}, {p.sound}, {p.mistake}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
