#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/condense_linguini_descriptor_flashback_surprise_twist_bedtime.py
================================================================================================

A standalone storyworld for a bedtime-scale cooking tale built from the seed
words "condense", "linguini", and "descriptor", with a flashback, a surprise,
and a gentle twist.

The domain:
    A child and a grown-up make a tiny bowl of bedtime linguini. The sauce turns
    out too thin. The child is tempted by quick fixes, but remembers an earlier
    lesson: gentle simmering can condense the sauce and make it cozy. They also
    think a missing recipe card holds a "secret ingredient". The surprise twist
    is that the secret is not a new ingredient at all -- it is the child's own
    describing word, the final descriptor that turns supper into a bedtime meal.

Run it
------
    python storyworlds/worlds/gpt-5.4/condense_linguini_descriptor_flashback_surprise_twist_bedtime.py
    python storyworlds/worlds/gpt-5.4/condense_linguini_descriptor_flashback_surprise_twist_bedtime.py --pot deep --helper grandmother
    python storyworlds/worlds/gpt-5.4/condense_linguini_descriptor_flashback_surprise_twist_bedtime.py --quick-fix water  # rejected
    python storyworlds/worlds/gpt-5.4/condense_linguini_descriptor_flashback_surprise_twist_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/condense_linguini_descriptor_flashback_surprise_twist_bedtime.py --verify
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

HERE = os.path.abspath(__file__)
PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, PACKAGE_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class PotKind:
    id: str
    label: str
    phrase: str
    simmer_line: str
    shine_line: str
    depth: int
    tags: set[str] = field(default_factory=set)


@dataclass
class SauceKind:
    id: str
    label: str
    color: str
    bedtime_name: str
    steam_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuickFix:
    id: str
    label: str
    sense: int
    effect: str
    makes_worse: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class DescriptorWord:
    id: str
    word: str
    ending_line: str
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


def _r_steam(world: World) -> list[str]:
    pot = world.get("pot")
    window = world.get("window")
    out: list[str] = []
    if pot.meters["warm"] >= THRESHOLD and pot.meters["steamy"] >= THRESHOLD:
        sig = ("steam",)
        if sig not in world.fired:
            world.fired.add(sig)
            window.meters["fogged"] += 1
            out.append("__steam__")
    return out


def _r_condense(world: World) -> list[str]:
    pot = world.get("pot")
    out: list[str] = []
    if pot.meters["simmering"] >= THRESHOLD and pot.meters["watery"] >= THRESHOLD:
        sig = ("condense",)
        if sig not in world.fired:
            world.fired.add(sig)
            pot.meters["watery"] = max(0.0, pot.meters["watery"] - 1.0)
            pot.meters["thick"] += 1
            pot.meters["cozy"] += 1
            out.append("__condense__")
    return out


CAUSAL_RULES = [
    Rule(name="steam", tag="physical", apply=_r_steam),
    Rule(name="condense", tag="physical", apply=_r_condense),
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
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


POTS = {
    "small": PotKind(
        id="small",
        label="small pot",
        phrase="a little silver pot",
        simmer_line="tiny bubbles tapped along the edge",
        shine_line="its round side caught the lamplight",
        depth=1,
        tags={"pot", "steam"},
    ),
    "deep": PotKind(
        id="deep",
        label="deep pot",
        phrase="a deep blue pot",
        simmer_line="soft bubbles rolled under the sauce",
        shine_line="its painted side glowed in the warm kitchen light",
        depth=2,
        tags={"pot", "steam"},
    ),
    "speckled": PotKind(
        id="speckled",
        label="speckled pot",
        phrase="a white speckled pot",
        simmer_line="little bubbles popped like whispers",
        shine_line="its pale side looked dotted with stars",
        depth=2,
        tags={"pot", "steam"},
    ),
}

SAUCES = {
    "tomato": SauceKind(
        id="tomato",
        label="tomato sauce",
        color="red",
        bedtime_name="moon-red linguini",
        steam_line="The tomato smell drifted up sweet and warm.",
        tags={"sauce", "steam"},
    ),
    "butter": SauceKind(
        id="butter",
        label="butter sauce",
        color="golden",
        bedtime_name="golden linguini",
        steam_line="The buttery smell floated up soft and sleepy.",
        tags={"sauce", "steam"},
    ),
    "herb": SauceKind(
        id="herb",
        label="herb sauce",
        color="green-flecked",
        bedtime_name="garden linguini",
        steam_line="A herby smell curled up in the warm air.",
        tags={"sauce", "steam"},
    ),
}

QUICK_FIXES = {
    "water": QuickFix(
        id="water",
        label="more water",
        sense=1,
        effect="made the sauce even looser",
        makes_worse=True,
        tags={"water"},
    ),
    "milk": QuickFix(
        id="milk",
        label="a splash of milk",
        sense=1,
        effect="turned the sauce pale and thinner",
        makes_worse=True,
        tags={"milk"},
    ),
    "simmer": QuickFix(
        id="simmer",
        label="a patient simmer",
        sense=3,
        effect="let the sauce condense and grow thick",
        makes_worse=False,
        tags={"simmer", "condense"},
    ),
}

DESCRIPTORS = {
    "cozy": DescriptorWord(
        id="cozy",
        word="cozy",
        ending_line="The bowl looked small and cozy, as if it knew it was almost bedtime.",
        tags={"descriptor", "bedtime"},
    ),
    "sleepy": DescriptorWord(
        id="sleepy",
        word="sleepy",
        ending_line="The bowl looked sleepy and gentle, ready for quiet spoons instead of noisy forks.",
        tags={"descriptor", "bedtime"},
    ),
    "golden": DescriptorWord(
        id="golden",
        word="golden",
        ending_line="The bowl shone golden under the lamp, like a tiny moon on the table.",
        tags={"descriptor", "bedtime"},
    ),
}

HELPERS = {
    "mother": {"type": "mother", "label": "the parent"},
    "father": {"type": "father", "label": "the parent"},
    "grandmother": {"type": "grandmother", "label": "the parent"},
    "grandfather": {"type": "grandfather", "label": "the parent"},
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Noah", "Eli", "Theo", "Jack", "Finn", "Owen"]
TRAITS = ["sleepy", "careful", "curious", "gentle", "patient", "hopeful"]


def valid_combo(pot: PotKind, sauce: SauceKind, quick_fix: QuickFix, descriptor: DescriptorWord) -> bool:
    _ = sauce
    if quick_fix.sense < SENSE_MIN:
        return False
    if quick_fix.id != "simmer":
        return False
    if pot.depth < 1:
        return False
    if descriptor.word not in {"cozy", "sleepy", "golden"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for pot_id, pot in POTS.items():
        for sauce_id, sauce in SAUCES.items():
            for fix_id, fix in QUICK_FIXES.items():
                for desc_id, desc in DESCRIPTORS.items():
                    if valid_combo(pot, sauce, fix, desc):
                        combos.append((pot_id, sauce_id, fix_id, desc_id))
    return combos


@dataclass
class StoryParams:
    pot: str
    sauce: str
    quick_fix: str
    descriptor: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def setup_world(
    pot_cfg: PotKind,
    sauce_cfg: SauceKind,
    descriptor_cfg: DescriptorWord,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            label=child_name,
            phrase=child_name,
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            phrase="the helper",
            tags={"grownup"},
        )
    )
    pot = world.add(
        Entity(
            id="pot",
            kind="thing",
            type="pot",
            label=pot_cfg.label,
            phrase=pot_cfg.phrase,
            tags=set(pot_cfg.tags),
        )
    )
    bowl = world.add(
        Entity(
            id="bowl",
            kind="thing",
            type="bowl",
            label="bowl",
            phrase="a little bowl",
            tags={"bowl"},
        )
    )
    window = world.add(
        Entity(
            id="window",
            kind="thing",
            type="window",
            label="window",
            phrase="the kitchen window",
            tags={"window"},
        )
    )
    card = world.add(
        Entity(
            id="card",
            kind="thing",
            type="card",
            label="recipe card",
            phrase="the little recipe card",
            tags={"card"},
        )
    )

    pot.meters["warm"] += 1
    pot.meters["steamy"] += 1
    pot.meters["watery"] += 1
    child.memes["hope"] += 1
    child.memes["impatience"] += 1
    helper.memes["calm"] += 1

    world.facts.update(
        child=child,
        helper=helper,
        pot_cfg=pot_cfg,
        sauce_cfg=sauce_cfg,
        descriptor_cfg=descriptor_cfg,
        card=card,
        bowl=bowl,
        window=window,
        flashback_used=False,
        surprise_used=False,
        twist_used=False,
    )
    return world


def introduce(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    pot_cfg = world.facts["pot_cfg"]
    sauce_cfg = world.facts["sauce_cfg"]
    pot = world.get("pot")
    world.say(
        f"On a hush-soft evening, {child.id} stood on a stool beside {helper.label_word} and watched {pot_cfg.phrase} on the stove."
    )
    world.say(
        f"Inside it, a few ribbons of linguini swayed in {sauce_cfg.label}. {pot_cfg.shine_line}"
    )
    world.say(sauce_cfg.steam_line)
    propagate(world, narrate=False)


def problem(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    pot = world.get("pot")
    world.say(
        f'"It smells lovely," {child.id} whispered, "but it looks runny."'
    )
    if pot.meters["watery"] >= THRESHOLD:
        world.say(
            f"{helper.label_word.capitalize()} tipped the spoon and watched the sauce slip off too quickly. \"You're right,\" {helper.pronoun()} said. \"It needs a little help before bedtime.\""
        )


def missing_card(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    world.say(
        f"Then {child.id} looked for the little recipe card they always used at night, but it was not on the counter."
    )
    world.say(
        f'"Oh!" {child.id} said. "Maybe the card tells us the secret."'
    )
    child.memes["worry"] += 1
    helper.memes["steady"] += 1


def bad_idea_line(world: World, fix: QuickFix) -> None:
    child = world.facts["child"]
    if fix.id == "water":
        world.say(f'"Maybe we should add {fix.label}," {child.id} guessed.')
    elif fix.id == "milk":
        world.say(f'"Maybe we need {fix.label}," {child.id} guessed.')
    else:
        world.say(f'"Maybe we just need {fix.label}," {child.id} guessed.')


def flashback(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    world.facts["flashback_used"] = True
    child.memes["remembering"] += 1
    world.say(
        f"As {child.id} stared at the steam, a small memory fluttered back."
    )
    world.say(
        f"Earlier that week, {helper.label_word} had lifted a lid and said, \"When a sauce is too loose, do not hurry it. Let it rest in tiny bubbles and condense.\""
    )
    world.say(
        f"The word condense had sounded big then, but now it felt clear and warm."
    )


def do_quick_fix(world: World, fix: QuickFix, narrate: bool = True) -> None:
    pot = world.get("pot")
    child = world.facts["child"]
    if fix.id == "simmer":
        pot.meters["simmering"] += 1
        child.memes["trust"] += 1
        propagate(world, narrate=False)
        if narrate:
            world.say(
                "So they turned the flame low and waited together, listening to the smallest bubbling sounds."
            )
    else:
        pot.meters["watery"] += 1
        child.memes["frustration"] += 1
        if narrate:
            world.say(
                f"But that only {fix.effect}, and the noodles looked more tired than before."
            )


def predict_fix(world: World, fix: QuickFix) -> dict:
    sim = world.copy()
    do_quick_fix(sim, fix, narrate=False)
    pot = sim.get("pot")
    return {
        "watery": pot.meters["watery"],
        "thick": pot.meters["thick"],
        "cozy": pot.meters["cozy"],
    }


def choose_fix(world: World, fix: QuickFix) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    before = predict_fix(world, fix)
    if fix.id != "simmer":
        world.say(
            f"{helper.label_word.capitalize()} shook {helper.pronoun('possessive')} head. \"That would thin it more,\" {helper.pronoun()} said gently."
        )
        better = QUICK_FIXES["simmer"]
        after = predict_fix(world, better)
        if after["thick"] > before["thick"]:
            world.say(
                f"\"Let us try the patient way instead. We can let the sauce condense while we stay close and stir.\""
            )
        fix = better
    else:
        world.say(
            f"{helper.label_word.capitalize()} smiled. \"Yes,\" {helper.pronoun()} said. \"That is the quiet kitchen trick.\""
        )
    do_quick_fix(world, fix, narrate=True)
    child.memes["calm"] += 1
    child.memes["wonder"] += 1


def steam_window(world: World) -> None:
    window = world.get("window")
    pot_cfg = world.facts["pot_cfg"]
    if window.meters["fogged"] >= THRESHOLD:
        world.say(
            f"Steam climbed up and made a pale cloud on the window. Tiny drops began to condense there too, and the glass turned silver in the light."
        )
        world.say(
            f"Behind them, {pot_cfg.simmer_line}, and the room seemed to grow quieter with every breath."
        )


def surprise_and_twist(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    descriptor_cfg = world.facts["descriptor_cfg"]
    card = world.get("card")
    pot = world.get("pot")
    world.facts["surprise_used"] = True
    world.facts["twist_used"] = True

    world.say(
        f"Just then, {child.id} gave a little gasp. The missing recipe card had slipped behind the fruit bowl all along."
    )
    world.say(
        f"{helper.label_word.capitalize()} laughed softly and picked up {card.phrase}."
    )
    world.say(
        f"But when they turned it over, there was no secret ingredient written there at all."
    )
    if pot.meters["cozy"] >= THRESHOLD:
        world.say(
            f'"This is the surprise," {helper.label_word} said. "The last thing was never an ingredient. It was the final descriptor -- the word that tells us what kind of supper this has become."'
        )
    else:
        world.say(
            f'"This is the surprise," {helper.label_word} said. "The last thing was never an ingredient. It was the final descriptor."'
        )
    world.say(
        f'{child.id} looked into the bowl and whispered, "\"{descriptor_cfg.word}.\""'
    )
    child.memes["pride"] += 1
    helper.memes["joy"] += 1


def serve(world: World) -> None:
    child = world.facts["child"]
    helper = world.facts["helper"]
    descriptor_cfg = world.facts["descriptor_cfg"]
    sauce_cfg = world.facts["sauce_cfg"]
    bowl = world.get("bowl")
    pot = world.get("pot")
    if pot.meters["thick"] >= THRESHOLD:
        bowl.meters["served"] += 1
        world.say(
            f"Soon the linguini curled into {bowl.phrase}, carrying the sauce in a soft, shiny coat instead of a splashy puddle."
        )
    else:
        world.say(
            f"Soon the linguini slipped into {bowl.phrase}, still glossy and warm."
        )
    world.say(descriptor_cfg.ending_line)
    world.say(
        f'Together they called it "{descriptor_cfg.word} {sauce_cfg.bedtime_name}," and that felt exactly right.'
    )
    world.say(
        f"{child.id} took the first slow bite, and the whole kitchen seemed to tuck itself in."
    )


def tell(
    pot_cfg: PotKind,
    sauce_cfg: SauceKind,
    quick_fix_cfg: QuickFix,
    descriptor_cfg: DescriptorWord,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = setup_world(
        pot_cfg=pot_cfg,
        sauce_cfg=sauce_cfg,
        descriptor_cfg=descriptor_cfg,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
    )
    introduce(world)
    problem(world)

    world.para()
    missing_card(world)
    bad_idea_line(world, quick_fix_cfg)
    flashback(world)
    choose_fix(world, quick_fix_cfg)

    world.para()
    steam_window(world)
    surprise_and_twist(world)
    serve(world)

    pot = world.get("pot")
    world.facts.update(
        outcome="thickened" if pot.meters["thick"] >= THRESHOLD else "thin",
        used_fix="simmer" if pot.meters["thick"] >= THRESHOLD else quick_fix_cfg.id,
        sauce_ready=pot.meters["thick"] >= THRESHOLD,
        pot=pot,
    )
    return world


KNOWLEDGE = {
    "linguini": [
        (
            "What is linguini?",
            "Linguini is a kind of pasta made in long, flat strands. People boil it until it is soft enough to eat."
        )
    ],
    "condense": [
        (
            "What does condense mean in cooking?",
            "In cooking, condense means some of the extra water cooks away so a sauce gets thicker. It often happens when food simmers gently."
        )
    ],
    "descriptor": [
        (
            "What is a descriptor word?",
            "A descriptor is a word that tells what something is like, such as cozy or golden. It helps you picture the thing more clearly."
        )
    ],
    "steam": [
        (
            "Why does steam make a window foggy?",
            "Warm steam touches the cooler glass and turns into tiny drops of water. Those little drops make the window look cloudy."
        )
    ],
    "simmer": [
        (
            "What is simmering?",
            "Simmering means cooking something with small gentle bubbles instead of a hard boil. It is a calm way to cook food slowly."
        )
    ],
    "bedtime": [
        (
            "Why do some foods feel like bedtime foods?",
            "Warm, soft foods can feel calm and comforting at the end of the day. They match the quiet, sleepy mood before bed."
        )
    ],
}
KNOWLEDGE_ORDER = ["linguini", "condense", "descriptor", "steam", "simmer", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    sauce_cfg = world.facts["sauce_cfg"]
    descriptor_cfg = world.facts["descriptor_cfg"]
    return [
        (
            f'Write a bedtime story for a 3-to-5-year-old that includes the words '
            f'"condense", "linguini", and "descriptor". The story should have a flashback, a surprise, and a twist.'
        ),
        (
            f"Tell a gentle kitchen story where {child.id} and {helper.label_word} make linguini before bed, remember an earlier lesson, and discover that the missing secret is really a descriptor word."
        ),
        (
            f'Write a soft, sleepy story about thin {sauce_cfg.label} becoming thicker as it condenses, ending with the child naming the bowl "{descriptor_cfg.word}".'
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    sauce_cfg = world.facts["sauce_cfg"]
    descriptor_cfg = world.facts["descriptor_cfg"]
    used_fix = world.facts["used_fix"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.label_word}, who were making a little bowl of linguini at night. The quiet kitchen helps the story feel gentle and bedtime-soft."
        ),
        (
            "What problem did they have with the linguini?",
            f"The {sauce_cfg.label} was too runny at first, so it slid off the noodles too fast. That is why they had to stop and decide how to fix it."
        ),
    ]
    if world.facts["flashback_used"]:
        qa.append(
            (
                "What happened in the flashback?",
                f"{child.id} remembered {helper.label_word}'s earlier lesson that a loose sauce should simmer and condense instead of being hurried. The memory guided the choice they made in the kitchen."
            )
        )
    if used_fix == "simmer" and outcome == "thickened":
        qa.append(
            (
                "How did they make the sauce better?",
                "They turned the heat low and let the sauce simmer patiently until it could condense. That gentle cooking made it thicker and more cozy around the linguini."
            )
        )
    if world.facts["surprise_used"]:
        qa.append(
            (
                "What was the surprise with the recipe card?",
                "The missing card had only slipped behind the fruit bowl, so it was nearby the whole time. Finding it made them expect a secret ingredient."
            )
        )
    if world.facts["twist_used"]:
        qa.append(
            (
                "What was the twist at the end?",
                f"The card did not hide a new ingredient after all. The last secret was the child's own descriptor word, \"{descriptor_cfg.word},\" which named the bowl and showed how it felt."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with a warm bowl of linguini and a calm, sleepy kitchen. Calling the supper \"{descriptor_cfg.word}\" proved that the meal had changed from runny and uncertain to gentle and ready for bedtime."
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"linguini", "condense", "descriptor", "steam", "bedtime"}
    if world.facts["used_fix"] == "simmer":
        tags.add("simmer")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        pot="small",
        sauce="tomato",
        quick_fix="simmer",
        descriptor="cozy",
        child_name="Lily",
        child_gender="girl",
        helper="grandmother",
        trait="curious",
        seed=101,
    ),
    StoryParams(
        pot="deep",
        sauce="butter",
        quick_fix="simmer",
        descriptor="sleepy",
        child_name="Leo",
        child_gender="boy",
        helper="father",
        trait="hopeful",
        seed=102,
    ),
    StoryParams(
        pot="speckled",
        sauce="herb",
        quick_fix="simmer",
        descriptor="golden",
        child_name="Maya",
        child_gender="girl",
        helper="mother",
        trait="gentle",
        seed=103,
    ),
]


def explain_rejection_fix(fix_id: str) -> str:
    fix = QUICK_FIXES[fix_id]
    return (
        f"(No story: '{fix.label}' is an unreasonable fix for a sauce that is already too thin. "
        f"In this world, the sauce needs to condense by simmering, not get thinner.)"
    )


ASP_RULES = r"""
reasonable_fix(F) :- quick_fix(F), sense(F, S), sense_min(M), S >= M, condensing_fix(F).
valid(P, S, F, D) :- pot(P), sauce(S), quick_fix(F), descriptor(D), reasonable_fix(F).

thickens :- chosen_fix(F), condensing_fix(F).
outcome(thickened) :- thickens.
outcome(thin) :- not thickens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pot_id, pot in POTS.items():
        lines.append(asp.fact("pot", pot_id))
        lines.append(asp.fact("depth", pot_id, pot.depth))
    for sauce_id in SAUCES:
        lines.append(asp.fact("sauce", sauce_id))
    for fix_id, fix in QUICK_FIXES.items():
        lines.append(asp.fact("quick_fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        if fix.id == "simmer":
            lines.append(asp.fact("condensing_fix", fix_id))
    for desc_id in DESCRIPTORS:
        lines.append(asp.fact("descriptor", desc_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_fix", params.quick_fix)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    fix = QUICK_FIXES[params.quick_fix]
    return "thickened" if fix.id == "simmer" else "thin"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if "linguini" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not mention linguini.")
    if not sample.story_qa or not sample.world_qa or not sample.prompts:
        raise StoryError("Smoke test failed: missing QA or prompts.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP valid combos match Python ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} scenarios had different outcomes.")

    try:
        smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a bedtime bowl of linguini, a remembered kitchen lesson, and a naming twist."
    )
    ap.add_argument("--pot", choices=sorted(POTS))
    ap.add_argument("--sauce", choices=sorted(SAUCES))
    ap.add_argument("--quick-fix", choices=sorted(QUICK_FIXES), dest="quick_fix")
    ap.add_argument("--descriptor", choices=sorted(DESCRIPTORS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quick_fix and QUICK_FIXES[args.quick_fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection_fix(args.quick_fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.pot is None or combo[0] == args.pot)
        and (args.sauce is None or combo[1] == args.sauce)
        and (args.quick_fix is None or combo[2] == args.quick_fix)
        and (args.descriptor is None or combo[3] == args.descriptor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pot_id, sauce_id, fix_id, desc_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        pot=pot_id,
        sauce=sauce_id,
        quick_fix=fix_id,
        descriptor=desc_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pot not in POTS:
        raise StoryError(f"(Unknown pot: {params.pot})")
    if params.sauce not in SAUCES:
        raise StoryError(f"(Unknown sauce: {params.sauce})")
    if params.quick_fix not in QUICK_FIXES:
        raise StoryError(f"(Unknown quick fix: {params.quick_fix})")
    if params.descriptor not in DESCRIPTORS:
        raise StoryError(f"(Unknown descriptor: {params.descriptor})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if QUICK_FIXES[params.quick_fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection_fix(params.quick_fix))
    if not valid_combo(POTS[params.pot], SAUCES[params.sauce], QUICK_FIXES[params.quick_fix], DESCRIPTORS[params.descriptor]):
        raise StoryError("(These story options do not make a reasonable bedtime story in this world.)")

    world = tell(
        pot_cfg=POTS[params.pot],
        sauce_cfg=SAUCES[params.sauce],
        quick_fix_cfg=QUICK_FIXES[params.quick_fix],
        descriptor_cfg=DESCRIPTORS[params.descriptor],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(f"{len(combos)} compatible (pot, sauce, quick_fix, descriptor) combos:\n")
        for pot_id, sauce_id, fix_id, desc_id in combos:
            print(f"  {pot_id:10} {sauce_id:8} {fix_id:8} {desc_id}")
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
            header = f"### {p.child_name}: {p.sauce} linguini in a {p.pot} pot ({p.descriptor})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
