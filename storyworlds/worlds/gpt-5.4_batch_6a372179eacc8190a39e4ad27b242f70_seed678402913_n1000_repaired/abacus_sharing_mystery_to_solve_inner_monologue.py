#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py
==============================================================================

A standalone storyworld about a child who must count food to share at a village
feast, notices that the basket and the abacus do not agree, and solves the
mystery gently. The domain is built to stay small and plausible: a missing treat
must have a believable taker for that place and food, and the hero's temper
changes whether the story becomes a wise investigation or a rash accusation
followed by apology.

Run it
------
    python storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py --setting orchard --treat pears --cause goat
    python storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py --treat rice_cakes --cause goat
    python storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py --qa --json
    python storyworlds/worlds/gpt-5.4/abacus_sharing_mystery_to_solve_inner_monologue.py --verify
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
PATIENT_TRAITS = {"patient", "careful", "gentle", "humble"}


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    clue_path: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    plural_label: str
    tags: set[str] = field(default_factory=set)
    counting_word: str = "piece"


@dataclass
class Cause:
    id: str
    taker_label: str
    needs_tags: set[str] = field(default_factory=set)
    any_treat: bool = False
    settings: set[str] = field(default_factory=set)
    clue: str = ""
    trail: str = ""
    reveal: str = ""
    reason: str = ""
    share_end: str = ""
    count_word: str = "one"


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_missing(world: World) -> list[str]:
    basket = world.get("basket")
    hero = world.get("hero")
    abacus = world.get("abacus")
    if basket.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing", int(basket.meters["missing"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    abacus.meters["difference"] = basket.meters["missing"]
    hero.memes["worry"] += 1
    if "helper" in world.entities:
        world.get("helper").memes["worry"] += 1
    return ["__missing__"]


def _r_suspicion(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("hurt", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    return ["__hurt__"]


def _r_relief(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["truth"] < THRESHOLD or hero.memes["generosity"] < THRESHOLD:
        return []
    sig = ("relief", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing", tag="physical", apply=_r_missing),
    Rule(name="suspicion", tag="social", apply=_r_suspicion),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def cause_matches_treat(cause: Cause, treat: Treat) -> bool:
    return cause.any_treat or bool(cause.needs_tags & treat.tags)


def valid_combo(setting_id: str, treat_id: str, cause_id: str) -> bool:
    setting = SETTINGS[setting_id]
    treat = TREATS[treat_id]
    cause = CAUSES[cause_id]
    return cause.id in setting.allows and cause_matches_treat(cause, treat) and setting.id in cause.settings


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for treat_id in TREATS:
            for cause_id in CAUSES:
                if valid_combo(setting_id, treat_id, cause_id):
                    combos.append((setting_id, treat_id, cause_id))
    return combos


def is_patient(trait: str) -> bool:
    return trait in PATIENT_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "wise" if is_patient(params.trait) else "mended"


def predict_missing(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "difference": sim.get("abacus").meters["difference"],
        "worry": sim.get("hero").memes["worry"],
    }


def opening(world: World, hero: Entity, helper: Entity, elder: Entity, treat: Treat, expected: int) -> None:
    basket = world.get("basket")
    abacus = world.get("abacus")
    basket.meters["count"] = float(expected - 1)
    basket.meters["missing"] = 1.0
    abacus.meters["expected"] = float(expected)
    abacus.meters["counted"] = float(expected)
    hero.memes["duty"] += 1
    helper.memes["duty"] += 1
    world.say(
        f"In the days when the village still listened to wind and well-water, {hero.id} and "
        f"{helper.id} were asked by {hero.pronoun('possessive')} {elder.label_word} to carry "
        f"{treat.plural_label} to the sharing table in {world.setting.place}."
    )
    world.say(
        f"Beside the basket lay an old abacus with smooth wooden beads. For every {treat.counting_word} "
        f"that should reach the feast, {hero.id} slid one bead with a careful finger."
    )


def count_and_notice(world: World, hero: Entity, helper: Entity, treat: Treat) -> None:
    pred = predict_missing(world)
    diff = int(pred["difference"])
    world.facts["predicted_difference"] = diff
    propagate(world, narrate=False)
    world.say(
        f"When the counting was done, the beads said {int(world.get('abacus').meters['expected'])}, "
        f"but the basket held only {int(world.get('basket').meters['count'])}. One place in the row looked empty."
    )
    world.say(
        f'"One bead does not lie," {hero.id} thought. "If I blame the wrong hands, I will make two hurts instead of one."'
    )


def first_reaction(world: World, hero: Entity, helper: Entity, cause: Cause, trait: str) -> None:
    if is_patient(trait):
        hero.memes["patience"] += 1
        world.say(
            f"{hero.id} drew a slow breath and looked at the ground instead of at {helper.id}'s face."
        )
        world.say(
            f'"The road will tell its own tale," {hero.pronoun()} thought. "I must listen before I speak."'
        )
    else:
        hero.memes["suspicion"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Worry pricked {hero.id} like a thorn. {hero.pronoun().capitalize()} turned too quickly to {helper.id} and asked "
            f'if {helper.pronoun()} had taken a {cause.count_word} {world.get("basket").label[:-1] if world.get("basket").label.endswith("s") else world.get("basket").label}.'
        )
        world.say(
            f"{helper.id}'s eyes grew round, and the question hung between them like a cold string in winter."
        )
        world.say(
            f'"My tongue ran ahead of my good sense," {hero.id} thought, though {hero.pronoun()} had not yet found the truth.'
        )


def inspect_clue(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    world.say(
        f"Then {helper.id} pointed toward {world.setting.clue_path}. There lay {cause.clue}."
    )
    world.say(
        f"{hero.id} knelt, touched the sign lightly, and followed {cause.trail}."
    )


def reveal_truth(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    hero.memes["truth"] += 1
    world.facts["solved"] = True
    world.say(cause.reveal)
    world.say(
        f'"So that is the whole of it," {hero.id} thought. "{cause.reason}"'
    )


def mend_if_needed(world: World, hero: Entity, helper: Entity) -> None:
    if hero.memes["suspicion"] >= THRESHOLD:
        hero.memes["shame"] += 1
        hero.memes["kindness"] += 1
        world.say(
            f"{hero.id} turned at once to {helper.id}. \"I spoke before I knew,\" {hero.pronoun()} said. "
            f"\"Please forgive me.\""
        )
        world.say(
            f"{helper.id} nodded, because a soft apology can untie a hard knot."
        )


def share_and_close(world: World, hero: Entity, helper: Entity, elder: Entity, treat: Treat, cause: Cause) -> None:
    hero.memes["generosity"] += 1
    helper.memes["generosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Instead of guarding the basket with a closed heart, {hero.id} set it down and {cause.share_end}"
    )
    world.say(
        f"After that, {hero.id} and {helper.id} carried the rest to the sharing table, and even the old abacus seemed to smile in its wooden frame."
    )
    world.say(
        f"At supper the village said that numbers are useful, but kinder still is the heart that knows what to do after the numbers speak."
    )
    world.facts["shared"] = True


def tell(
    setting: Setting,
    treat: Treat,
    cause: Cause,
    hero_name: str = "Mei",
    hero_gender: str = "girl",
    helper_name: str = "Jun",
    helper_gender: str = "boy",
    elder_type: str = "aunt",
    trait: str = "patient",
    expected_count: int = 7,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait], label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label=helper_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="basket",
            label=treat.plural_label,
            phrase=f"a willow basket of {treat.plural_label}",
            tags=set(treat.tags),
        )
    )
    abacus = world.add(
        Entity(
            id="abacus",
            kind="thing",
            type="abacus",
            label="abacus",
            phrase="an old abacus",
        )
    )

    opening(world, hero, helper, elder, treat, expected_count)
    world.para()
    count_and_notice(world, hero, helper, treat)
    first_reaction(world, hero, helper, cause, trait)
    world.para()
    inspect_clue(world, hero, helper, cause)
    reveal_truth(world, hero, helper, cause)
    mend_if_needed(world, hero, helper)
    world.para()
    share_and_close(world, hero, helper, elder, treat, cause)

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        basket=basket,
        abacus=abacus,
        setting=setting,
        treat=treat,
        cause=cause,
        expected_count=expected_count,
        missing_count=1,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                treat=treat.id,
                cause=cause.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                helper_name=helper_name,
                helper_gender=helper_gender,
                elder=elder_type,
                trait=trait,
                expected_count=expected_count,
            )
        ),
        accused=hero.memes["suspicion"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the stone courtyard",
        scene="a courtyard where jars of pickles warmed in the sun",
        clue_path="the low wall under the eaves",
        allows={"sparrow", "little_brother"},
    ),
    "bridge": Setting(
        id="bridge",
        place="the willow bridge",
        scene="a bridge where the river made talking sounds below",
        clue_path="the post by the bridge rope",
        allows={"goat", "little_brother"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the plum orchard",
        scene="an orchard where shadows lay in rows between the trees",
        clue_path="the grass beside the cart path",
        allows={"sparrow", "goat", "little_brother"},
    ),
}

TREATS = {
    "rice_cakes": Treat(
        id="rice_cakes",
        label="rice cake",
        phrase="soft rice cakes wrapped in leaves",
        plural_label="rice cakes",
        tags={"grain"},
        counting_word="cake",
    ),
    "pears": Treat(
        id="pears",
        label="pear",
        phrase="golden pears from the late tree",
        plural_label="pears",
        tags={"fruit", "goat_ok"},
        counting_word="pear",
    ),
    "sesame_buns": Treat(
        id="sesame_buns",
        label="sesame bun",
        phrase="warm sesame buns with shiny tops",
        plural_label="sesame buns",
        tags={"grain", "bread", "goat_ok"},
        counting_word="bun",
    ),
}

CAUSES = {
    "sparrow": Cause(
        id="sparrow",
        taker_label="a sparrow",
        needs_tags={"grain"},
        settings={"courtyard", "orchard"},
        clue="a gray feather and a drift of tiny crumbs",
        trail="the crumbs along the wall to a nervous sparrow hopping with its head bent low",
        reveal="Behind a jar in the shade sat a little sparrow pecking at the missing morsel, too hungry even to fly at once.",
        reason="It was hunger, not mischief, that stole the bite.",
        share_end="crumbled one small cake for the sparrow and left a few safe crumbs where the other birds could find them.",
        count_word="single",
    ),
    "goat": Cause(
        id="goat",
        taker_label="a goat",
        needs_tags={"goat_ok"},
        settings={"bridge", "orchard"},
        clue="fresh hoofprints and a leaf chewed into a half-moon",
        trail="the hoofprints to a tethered goat blinking from behind a cart wheel",
        reveal="There stood the miller's goat, chewing the missing treat with the innocent patience that only goats possess.",
        reason="A low basket and a greedy nose make quick friends.",
        share_end="cut another treat into fair pieces so the goat's keeper, the children, and the workers at the feast all had enough.",
        count_word="whole",
    ),
    "little_brother": Cause(
        id="little_brother",
        taker_label="a little brother",
        any_treat=True,
        settings={"courtyard", "bridge", "orchard"},
        clue="sticky fingers on the basket handle and a tiny red thread from a child's sleeve",
        trail="the small prints behind a bench to a little brother trying to quiet a crying baby with the missing treat",
        reveal="There crouched a little brother with wide guilty eyes, holding the treat out to the baby on his lap.",
        reason="He had tried to mend one hunger with another person's share.",
        share_end="broke the treats more evenly and let the little ones eat first, so nobody had to snatch in secret again.",
        count_word="whole",
    ),
}

GIRL_NAMES = ["Mei", "Lian", "Yuna", "Asha", "Sora", "Nila", "Rin", "Tara"]
BOY_NAMES = ["Jun", "Bao", "Kenji", "Hari", "Toma", "Niko", "Ravi", "Tao"]
TRAITS = ["patient", "careful", "gentle", "humble", "hasty", "proud", "restless", "quick"]
ELDERS = ["aunt", "uncle", "mother", "father"]


@dataclass
class StoryParams:
    setting: str
    treat: str
    cause: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    elder: str
    trait: str
    expected_count: int = 7
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="courtyard",
        treat="rice_cakes",
        cause="sparrow",
        hero_name="Mei",
        hero_gender="girl",
        helper_name="Jun",
        helper_gender="boy",
        elder="aunt",
        trait="patient",
        expected_count=7,
    ),
    StoryParams(
        setting="bridge",
        treat="pears",
        cause="goat",
        hero_name="Bao",
        hero_gender="boy",
        helper_name="Lian",
        helper_gender="girl",
        elder="uncle",
        trait="hasty",
        expected_count=8,
    ),
    StoryParams(
        setting="orchard",
        treat="sesame_buns",
        cause="little_brother",
        hero_name="Yuna",
        hero_gender="girl",
        helper_name="Tao",
        helper_gender="boy",
        elder="mother",
        trait="gentle",
        expected_count=6,
    ),
    StoryParams(
        setting="orchard",
        treat="pears",
        cause="goat",
        hero_name="Ravi",
        hero_gender="boy",
        helper_name="Nila",
        helper_gender="girl",
        elder="father",
        trait="proud",
        expected_count=9,
    ),
]


KNOWLEDGE = {
    "abacus": [
        (
            "What is an abacus?",
            "An abacus is a counting tool with beads that slide on rods or wires. People move the beads to help keep track of numbers.",
        )
    ],
    "sharing": [
        (
            "Why is sharing food kind?",
            "Sharing food helps everyone feel included and cared for. It can turn a small meal into a happier one because no one is left out.",
        )
    ],
    "sparrow": [
        (
            "What is a sparrow?",
            "A sparrow is a small bird that often lives near houses and fields. It pecks seeds and crumbs with a quick little beak.",
        )
    ],
    "goat": [
        (
            "Why do goats nibble so many things?",
            "Goats explore the world with their mouths and like to nibble leaves and food. That is why people keep baskets and gardens out of their reach.",
        )
    ],
    "counting": [
        (
            "Why do people count food before sharing it?",
            "They count so they know whether there is enough for everyone. Counting helps people share fairly.",
        )
    ],
    "apology": [
        (
            "Why is it good to apologize after blaming someone unfairly?",
            "An apology tells the other person you know you hurt them and want to mend the hurt. It helps trust grow back.",
        )
    ],
}
KNOWLEDGE_ORDER = ["abacus", "counting", "sharing", "sparrow", "goat", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treat = f["treat"]
    setting = f["setting"]
    cause = f["cause"]
    prompts = [
        f'Write a short folk-tale-style story for a 3-to-5-year-old that includes the word "abacus".',
        f"Tell a gentle mystery where {hero.id} counts {treat.plural_label} on an abacus in {setting.place}, finds one missing, and solves the puzzle kindly.",
        f"Write a story with inner monologue, sharing, and a small village mystery in which {helper.id} helps discover that {cause.taker_label} is part of the answer.",
    ]
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    treat = f["treat"]
    cause = f["cause"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, two children carrying {treat.plural_label} for others to eat. {hero.id}'s {elder.label_word} trusts them with the basket and the old abacus.",
        ),
        (
            "What was the mystery?",
            f"The abacus said there should be {f['expected_count']} {treat.plural_label}, but the basket held only {f['expected_count'] - 1}. That told {hero.id} that one treat was missing before the sharing began.",
        ),
        (
            f"How did {hero.id} try to solve the mystery?",
            f"{hero.id} looked for signs near the basket instead of guessing wildly. The clue was {cause.clue}, and that clue led along {cause.trail}.",
        ),
        (
            "What was really happening?",
            f"{cause.reveal} {cause.reason}",
        ),
    ]
    if outcome == "wise":
        qa.append(
            (
                f"Did {hero.id} blame {helper.id}?",
                f"No. {hero.id} worried, but chose to pause and think first. That patient choice kept the mystery small and kept {helper.id}'s feelings safe.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} blame {helper.id} at first?",
                f"Yes. Worry made {hero.id} speak too quickly, and {helper.id}'s feelings were hurt for a moment. After the clue showed the truth, {hero.id} apologized and the friendship was mended.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with sharing instead of scolding. {hero.id} {cause.share_end[:-1] if cause.share_end.endswith('.') else cause.share_end}, and the rest went on to the feast.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"abacus", "sharing", "counting"}
    cause = world.facts["cause"]
    if cause.id == "sparrow":
        tags.add("sparrow")
    if cause.id == "goat":
        tags.add("goat")
    if world.facts["outcome"] == "mended":
        tags.add("apology")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, treat_id: str, cause_id: str) -> str:
    setting = SETTINGS[setting_id]
    treat = TREATS[treat_id]
    cause = CAUSES[cause_id]
    if cause.id not in setting.allows or setting.id not in cause.settings:
        return (
            f"(No story: {cause.taker_label.capitalize()} does not fit naturally in {setting.place}. "
            f"Choose a cause that belongs there.)"
        )
    return (
        f"(No story: {cause.taker_label.capitalize()} is not a believable taker of {treat.plural_label}. "
        f"Pick a treat that matches the cause.)"
    )


ASP_RULES = r"""
compatible(C, T) :- cause_any(C), treat(T).
compatible(C, T) :- cause_needs(C, Tag), treat_tag(T, Tag).

valid(S, T, C) :- setting(S), treat(T), cause(C),
                  setting_allows(S, C), cause_setting(C, S), compatible(C, T).

patient_trait(T) :- trait(T), patient_word(T).
outcome(wise)   :- patient_trait(T).
outcome(mended) :- trait(T), not patient_trait(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(setting.allows):
            lines.append(asp.fact("setting_allows", sid, cid))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        for tag in sorted(treat.tags):
            lines.append(asp.fact("treat_tag", tid, tag))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.any_treat:
            lines.append(asp.fact("cause_any", cid))
        for tag in sorted(cause.needs_tags):
            lines.append(asp.fact("cause_needs", cid, tag))
        for sid in sorted(cause.settings):
            lines.append(asp.fact("cause_setting", cid, sid))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient_word", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp_program(asp.fact("trait", params.trait), "#show outcome/1.")
    model = asp.one_model(scenario)
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an abacus, a missing treat, and a gentle mystery solved through sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--expected-count", type=int, choices=[6, 7, 8, 9])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.treat and args.cause:
        if not valid_combo(args.setting, args.treat, args.cause):
            raise StoryError(explain_rejection(args.setting, args.treat, args.cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.treat is None or combo[1] == args.treat)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, treat_id, cause_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    expected_count = args.expected_count if args.expected_count is not None else rng.choice([6, 7, 8, 9])

    return StoryParams(
        setting=setting_id,
        treat=treat_id,
        cause=cause_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        elder=elder,
        trait=trait,
        expected_count=expected_count,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if not valid_combo(params.setting, params.treat, params.cause):
        raise StoryError(explain_rejection(params.setting, params.treat, params.cause))

    world = tell(
        setting=SETTINGS[params.setting],
        treat=TREATS[params.treat],
        cause=CAUSES[params.cause],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
        trait=params.trait,
        expected_count=params.expected_count,
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
        print(f"{len(combos)} compatible (setting, treat, cause) combos:\n")
        for setting_id, treat_id, cause_id in combos:
            print(f"  {setting_id:10} {treat_id:12} {cause_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.treat} at {p.setting} ({p.cause}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
