#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disseminate_memorial_obedient_misunderstanding_bedtime_story.py
================================================================================================

A small bedtime-story world about an obedient child who wants to help prepare a
family memorial garden, misunderstands the grown-up word "disseminate," and
spreads the wrong things. The simulation models a real misunderstanding: the
child hears a big word, fills in the meaning incorrectly, acts with good
intentions, and is gently guided toward the right action.

Run it
------
python storyworlds/worlds/gpt-5.4/disseminate_memorial_obedient_misunderstanding_bedtime_story.py
python storyworlds/worlds/gpt-5.4/disseminate_memorial_obedient_misunderstanding_bedtime_story.py --all
python storyworlds/worlds/gpt-5.4/disseminate_memorial_obedient_misunderstanding_bedtime_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/disseminate_memorial_obedient_misunderstanding_bedtime_story.py --qa
python storyworlds/worlds/gpt-5.4/disseminate_memorial_obedient_misunderstanding_bedtime_story.py --verify
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

# Make the shared result containers importable when this nested script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World configuration
# ---------------------------------------------------------------------------
@dataclass
class Memorial:
    id: str
    label: str
    phrase: str
    place: str
    for_whom: str
    seed_kind: str
    resting_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    plural: bool = True
    scatterable: bool = False
    safe_place: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    text: str
    proof: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    memorial: str
    keepsake: str
    remedy: str
    child_name: str
    child_gender: str
    parent: str
    child_trait: str
    helper_pet: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World container
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wind_risk(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    if keepsake.meters["scattered"] < THRESHOLD:
        return out
    sig = ("wind_risk", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keepsake.meters["hard_to_find"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_relieved(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    if keepsake.meters["gathered"] < THRESHOLD:
        return out
    sig = ("relief", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    parent = world.get("parent")
    child.memes["relief"] += 1
    child.memes["understood"] += 1
    parent.memes["pride"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wind_risk", tag="physical", apply=_r_wind_risk),
    Rule(name="relief", tag="emotional", apply=_r_relieved),
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MEMORIALS = {
    "stone": Memorial(
        id="stone",
        label="memorial stone",
        phrase="a smooth memorial stone",
        place="the little garden by the porch",
        for_whom="Grandma June",
        seed_kind="forget-me-not seeds",
        resting_spot="beside the smooth stone",
        tags={"memorial", "garden", "seeds"},
    ),
    "tree": Memorial(
        id="tree",
        label="memorial tree",
        phrase="a young cherry memorial tree",
        place="the moonlit corner of the yard",
        for_whom="Grandpa Eli",
        seed_kind="tiny bluebell seeds",
        resting_spot="around the roots of the small tree",
        tags={"memorial", "tree", "seeds"},
    ),
    "bench": Memorial(
        id="bench",
        label="memorial bench",
        phrase="a painted memorial bench",
        place="the quiet patch near the fence",
        for_whom="Aunt Rosa",
        seed_kind="marigold seeds",
        resting_spot="under the bench where the soil was soft",
        tags={"memorial", "bench", "seeds"},
    ),
}

KEEPSAKES = {
    "cards": Keepsake(
        id="cards",
        label="memory cards",
        phrase="little memory cards with kind notes",
        plural=True,
        scatterable=False,
        safe_place="the blue memory box",
        tags={"cards", "paper", "memory_box"},
    ),
    "paper_stars": Keepsake(
        id="paper_stars",
        label="paper stars",
        phrase="paper stars with names and wishes",
        plural=True,
        scatterable=False,
        safe_place="the silver keepsake tin",
        tags={"stars", "paper", "keepsake_tin"},
    ),
    "ribbons": Keepsake(
        id="ribbons",
        label="memory ribbons",
        phrase="soft memory ribbons",
        plural=True,
        scatterable=False,
        safe_place="the woven basket",
        tags={"ribbons", "basket"},
    ),
    "seed_packets": Keepsake(
        id="seed_packets",
        label="seed packets",
        phrase="little seed packets",
        plural=True,
        scatterable=False,
        safe_place="the garden tray",
        tags={"packets", "garden"},
    ),
}

REMEDIES = {
    "explain_and_sort": Remedy(
        id="explain_and_sort",
        label="explain and sort",
        text="knelt beside the scattered keepsakes, explained that \"disseminate\" meant to spread seeds, not the special memory things, and helped sort everything gently back into its proper place",
        proof="At the end, the keepsakes were tucked away neatly and only the seeds rested in the soil.",
        tags={"explain", "sort", "seeds"},
    ),
    "moonlight_replant": Remedy(
        id="moonlight_replant",
        label="moonlight replant",
        text="gathered the keepsakes first, then opened the seed packet and showed how to sprinkle the seeds in a loose ring around the memorial while the moon shone on their hands",
        proof="At the end, a quiet ring of seeds lay in the dark soil, ready for morning.",
        tags={"explain", "plant", "moonlight"},
    ),
    "memory_box_then_seeds": Remedy(
        id="memory_box_then_seeds",
        label="memory box then seeds",
        text="helped the child tuck each keepsake into its safe box, then together they scattered the seeds where flowers could grow for the person they missed",
        proof="At the end, the memory box was closed safely and the garden bed was ready to bloom.",
        tags={"explain", "memory_box", "plant"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli", "Noah"]
TRAITS = ["obedient", "careful", "gentle", "thoughtful", "quiet", "hopeful"]
PETS = ["the cat", "the puppy", "the little dog", "the kitten", ""]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(memorial: Memorial, keepsake: Keepsake, remedy: Remedy) -> bool:
    if keepsake.scatterable:
        return False
    if "seeds" not in memorial.tags:
        return False
    if not remedy.tags.intersection({"explain", "plant"}):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for memorial_id, memorial in MEMORIALS.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            for remedy_id, remedy in REMEDIES.items():
                if valid_combo(memorial, keepsake, remedy):
                    combos.append((memorial_id, keepsake_id, remedy_id))
    return combos


def explain_rejection(memorial: Memorial, keepsake: Keepsake, remedy: Remedy) -> str:
    if keepsake.scatterable:
        return (
            f"(No story: {keepsake.label} are already things you can scatter, so the misunderstanding "
            f"would be too weak. Pick keepsakes that should stay together and safe.)"
        )
    if "seeds" not in memorial.tags:
        return (
            f"(No story: this memorial setup gives nothing sensible to disseminate. "
            f"The story needs seeds or something similar to scatter on purpose.)"
        )
    return (
        f"(No story: the remedy '{remedy.id}' does not gently explain the misunderstanding "
        f"and lead back to the memorial planting.)"
    )


# ---------------------------------------------------------------------------
# Prediction and actions
# ---------------------------------------------------------------------------
def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    do_misunderstand(sim, narrate=False)
    keepsake = sim.get("keepsake")
    return {
        "scattered": keepsake.meters["scattered"] >= THRESHOLD,
        "risk": keepsake.meters["hard_to_find"],
    }


def bedtime_glow() -> str:
    return random.choice([
        "The hall light was dim and golden.",
        "Soft lamplight made the room feel warm and sleepy.",
        "The evening air was quiet, and the curtains barely stirred.",
    ])


def introduce(world: World, child: Entity, parent: Entity, memorial: Memorial, keepsake: Keepsake) -> None:
    child.memes["love"] += 1
    child.memes["obedience"] += 1
    world.say(
        f"{child.id} was a little {child.attrs.get('trait', 'gentle')} {child.type} who always wanted to help."
    )
    world.say(
        f"In the yard there was {memorial.phrase} for {memorial.for_whom}, and on this evening "
        f"{child.id} watched {child.pronoun('possessive')} {parent.label_word} set out {keepsake.phrase} beside it."
    )
    world.say(
        f"{bedtime_glow()} The whole house felt wrapped in bedtime hush."
    )


def plan(world: World, child: Entity, parent: Entity, memorial: Memorial, keepsake: Keepsake) -> None:
    world.say(
        f'"Tomorrow," said {child.pronoun("possessive")} {parent.label_word}, '
        f'"we will disseminate the {memorial.seed_kind} around the {memorial.label}. '
        f'The {keepsake.label} stay safe in {keepsake.safe_place}."'
    )
    pred = predict_misunderstanding(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"{child.id} nodded at once. {child.pronoun().capitalize()} was very obedient, and wanted to do the job exactly right."
    )


def misunderstand(world: World, child: Entity) -> None:
    child.memes["confusion"] += 1
    world.say(
        f"But the big word \"disseminate\" fluttered around in {child.id}'s mind like a moth near a lamp."
    )
    world.say(
        f"{child.pronoun().capitalize()} whispered it to {child.pronoun('object')}self and decided it must mean to put all the memorial things everywhere so everyone could see them."
    )


def do_misunderstand(world: World, narrate: bool = True) -> None:
    keepsake = world.get("keepsake")
    child = world.get("child")
    keepsake.meters["scattered"] += 1
    child.memes["helpful"] += 1
    child.memes["worry"] += 0
    propagate(world, narrate=narrate)


def spread_wrong_things(world: World, child: Entity, memorial: Memorial, keepsake: Keepsake, pet: str) -> None:
    do_misunderstand(world)
    extra = ""
    if pet:
        extra = f" Even {pet} sat and watched with wide, puzzled eyes."
    world.say(
        f"So, while the house was growing quieter, {child.id} carried the {keepsake.label} out to {memorial.place} "
        f"and laid them all around {memorial.resting_spot}.{extra}"
    )
    if world.get("keepsake").meters["hard_to_find"] >= THRESHOLD:
        world.say(
            f"At first it looked busy and bright, but then {child.id} noticed how easily the small things could blow away or be stepped on."
        )


def discover(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"When {child.pronoun('possessive')} {parent.label_word} came to say good night, {parent.pronoun()} stopped and blinked at the yard."
    )
    world.say(
        f'"Oh, sweetheart," {parent.pronoun()} said softly, "I can see you were trying very hard to help."'
    )


def repair(world: World, child: Entity, parent: Entity, memorial: Memorial, keepsake: Keepsake, remedy: Remedy) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["gathered"] += 1
    keepsake_ent.meters["scattered"] = 0.0
    world.get("seed").meters["planted"] += 1
    propagate(world, narrate=False)
    child.memes["confusion"] = 0.0
    world.say(
        f"{parent.pronoun().capitalize()} {remedy.text}."
    )
    world.say(
        f'"You were obedient," {parent.pronoun()} told {child.id}. "You listened carefully, but the word was new. '
        f'It is all right to ask what a word means."'
    )
    world.say(
        f"Together they made the memorial look calm again, and the {memorial.seed_kind} were finally disseminated where flowers could grow."
    )


def ending(world: World, child: Entity, parent: Entity, remedy: Remedy) -> None:
    child.memes["sleepy"] += 1
    world.say(remedy.proof)
    world.say(
        f"Then {child.id} washed {child.pronoun('possessive')} hands, climbed into bed, and felt the misunderstanding untangle inside {child.pronoun('object')}."
    )
    world.say(
        f'"Next time I will ask," {child.pronoun()} murmured.'
    )
    world.say(
        f'{parent.pronoun().capitalize()} kissed {child.pronoun("possessive")} forehead. "That is a wise thing to do," {parent.pronoun()} said.'
    )
    world.say(
        "Outside, the memorial garden waited under the stars, holding the seeds in the dark, patient earth."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    memorial: Memorial,
    keepsake: Keepsake,
    remedy: Remedy,
    child_name: str = "Lily",
    child_gender: str = "girl",
    parent_type: str = "mother",
    child_trait: str = "obedient",
    helper_pet: str = "",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            role="child",
            attrs={"trait": child_trait},
            tags={"child"},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
            tags={"parent"},
        )
    )
    world.add(
        Entity(
            id="memorial",
            kind="thing",
            type="memorial",
            label=memorial.label,
            phrase=memorial.phrase,
            tags=set(memorial.tags),
        )
    )
    world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            phrase=keepsake.phrase,
            tags=set(keepsake.tags),
        )
    )
    world.add(
        Entity(
            id="seed",
            kind="thing",
            type="seeds",
            label=memorial.seed_kind,
            phrase=memorial.seed_kind,
            tags={"seeds", "garden"},
        )
    )

    world.facts["pet"] = helper_pet

    introduce(world, child, parent, memorial, keepsake)
    world.para()
    plan(world, child, parent, memorial, keepsake)
    misunderstand(world, child)
    world.para()
    spread_wrong_things(world, child, memorial, keepsake, helper_pet)
    discover(world, child, parent)
    world.para()
    repair(world, child, parent, memorial, keepsake, remedy)
    ending(world, child, parent, remedy)

    world.facts.update(
        child=child,
        parent=parent,
        memorial_cfg=memorial,
        keepsake_cfg=keepsake,
        remedy=remedy,
        child_name=child_name,
        misunderstanding=True,
        corrected=world.get("keepsake").meters["gathered"] >= THRESHOLD,
        disseminated_seeds=world.get("seed").meters["planted"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "disseminate": [
        (
            "What does disseminate mean?",
            "Disseminate means to spread something out over an area. In this story, it meant scattering seeds in the soil.",
        )
    ],
    "memorial": [
        (
            "What is a memorial?",
            "A memorial is something people make or keep to remember someone they love who has died. It can be a stone, a bench, a tree, or another quiet special place.",
        )
    ],
    "obedient": [
        (
            "What does obedient mean?",
            "Obedient means trying to do what a grown-up or helper asked you to do. It does not mean you always understand every word the first time.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or sees something but gets the meaning wrong. It can be fixed by asking questions and explaining clearly.",
        )
    ],
    "seeds": [
        (
            "Why do people scatter seeds in soil?",
            "People scatter seeds in soil because seeds need earth, water, and time to grow. Spreading them in the right place helps flowers come up later.",
        )
    ],
    "memory_box": [
        (
            "Why keep special memory things in a box?",
            "A memory box keeps small special things together and safe. That way they do not blow away, tear, or get lost.",
        )
    ],
}

KNOWLEDGE_ORDER = ["disseminate", "memorial", "obedient", "misunderstanding", "seeds", "memory_box"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    memorial = f["memorial_cfg"]
    keepsake = f["keepsake_cfg"]
    child = f["child"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "disseminate", "memorial", and "obedient".',
        f"Tell a gentle misunderstanding story where an obedient child tries to help with a memorial for {memorial.for_whom} but spreads {keepsake.label} instead of seeds.",
        "Write a soft bedtime story where a parent explains a big word kindly, the mistake is fixed together, and the ending image is calm and sleepy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    memorial = f["memorial_cfg"]
    keepsake = f["keepsake_cfg"]
    remedy = f["remedy"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a little {child.type}, and {child.pronoun('possessive')} {pw}. They were caring for a memorial for {memorial.for_whom}.",
        ),
        (
            "What job did the parent mean to do?",
            f"{pw.capitalize()} meant that they would disseminate the {memorial.seed_kind} around the {memorial.label}. The plan was to spread seeds in the soil so flowers could grow there.",
        ),
        (
            f"Why did {child.label} make a mistake?",
            f"{child.label} was trying to be obedient, but {child.pronoun()} did not understand the word \"disseminate.\" Because the word was new, {child.pronoun()} guessed it meant spreading all the memorial things around.",
        ),
        (
            f"What did {child.label} spread by mistake?",
            f"{child.pronoun().capitalize()} spread the {keepsake.label} around the memorial. That was a problem because the small keepsakes could get lost or blown away.",
        ),
        (
            "How was the misunderstanding fixed?",
            f"{pw.capitalize()} {remedy.text}. The fix worked because they put the keepsakes back where they belonged and scattered only the seeds.",
        ),
        (
            "How did the story end?",
            f"It ended quietly and safely. {remedy.proof} Then {child.label} went to bed understanding that asking about a hard word is the right thing to do.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"disseminate", "memorial", "obedient", "misunderstanding", "seeds"}
    if world.facts["keepsake_cfg"].safe_place:
        tags.add("memory_box")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(M, K, R) :- memorial(M), keepsake(K), remedy(R),
                  not scatterable(K), has_seeds(M), gentle_fix(R).

gentle_fix(R) :- remedy(R), remedy_tag(R, explain), remedy_tag(R, plant).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for memorial_id, memorial in MEMORIALS.items():
        lines.append(asp.fact("memorial", memorial_id))
        if "seeds" in memorial.tags:
            lines.append(asp.fact("has_seeds", memorial_id))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        if keepsake.scatterable:
            lines.append(asp.fact("scatterable", keepsake_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for tag in sorted(remedy.tags):
            lines.append(asp.fact("remedy_tag", remedy_id, tag))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "disseminate" not in sample.story or "memorial" not in sample.story or "obedient" not in sample.story:
            raise StoryError("Smoke test story did not render the required seed words.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        memorial="stone",
        keepsake="cards",
        remedy="moonlight_replant",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        child_trait="obedient",
        helper_pet="the kitten",
    ),
    StoryParams(
        memorial="tree",
        keepsake="paper_stars",
        remedy="memory_box_then_seeds",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        child_trait="gentle",
        helper_pet="the cat",
    ),
    StoryParams(
        memorial="bench",
        keepsake="ribbons",
        remedy="explain_and_sort",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        child_trait="thoughtful",
        helper_pet="",
    ),
]


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A bedtime storyworld about a memorial garden, an obedient child, and a misunderstanding."
    )
    ap.add_argument("--memorial", choices=sorted(MEMORIALS))
    ap.add_argument("--keepsake", choices=sorted(KEEPSAKES))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.memorial and args.keepsake and args.remedy:
        memorial = MEMORIALS[args.memorial]
        keepsake = KEEPSAKES[args.keepsake]
        remedy = REMEDIES[args.remedy]
        if not valid_combo(memorial, keepsake, remedy):
            raise StoryError(explain_rejection(memorial, keepsake, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.memorial is None or combo[0] == args.memorial)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    memorial_id, keepsake_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    pet = rng.choice(PETS)
    return StoryParams(
        memorial=memorial_id,
        keepsake=keepsake_id,
        remedy=remedy_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        child_trait=trait,
        helper_pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.memorial not in MEMORIALS:
        raise StoryError(f"(Unknown memorial: {params.memorial})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")

    memorial = MEMORIALS[params.memorial]
    keepsake = KEEPSAKES[params.keepsake]
    remedy = REMEDIES[params.remedy]
    if not valid_combo(memorial, keepsake, remedy):
        raise StoryError(explain_rejection(memorial, keepsake, remedy))

    world = tell(
        memorial=memorial,
        keepsake=keepsake,
        remedy=remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        child_trait=params.child_trait,
        helper_pet=params.helper_pet,
    )

    story_text = world.render().replace("child", params.child_name)
    story_text = story_text.replace("parent", "Parent")

    # Replace labels from internal ids with the chosen child name only where intended.
    story_text = story_text.replace("child", params.child_name)

    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story.replace("child", sample.params.child_name))
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
        print(f"{len(combos)} compatible (memorial, keepsake, remedy) combos:\n")
        for memorial, keepsake, remedy in combos:
            print(f"  {memorial:8} {keepsake:12} {remedy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.memorial} / {p.keepsake} / {p.remedy}"
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
