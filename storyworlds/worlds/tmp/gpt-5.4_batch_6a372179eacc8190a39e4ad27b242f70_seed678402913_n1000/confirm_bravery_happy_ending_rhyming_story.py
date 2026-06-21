#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py
=========================================================================

A standalone storyworld about a child being brave enough to check a scary sound
the safe way, confirm who is hiding, and bring a little pet back out.

The domain is deliberately small and constraint-checked:
- a pet slips into a hiding place
- the child feels fear, but chooses a sensible brave method
- the method must fit the hiding place and the pet
- the story ends with a happy image proving the fear changed into relief

The prose aims for a gentle rhyming-story style without turning into nonsense
verse. State still drives the lines: fear, courage, being stuck, and being found
all come from the simulated world.

Run it
------
    python storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py --pet kitten --hideout berry_bush
    python storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py --hideout apple_branch --method treat_trail
    python storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/confirm_bravery_happy_ending_rhyming_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives one level deeper than usual under worlds/.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    ground_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pet:
    id: str
    label: str
    phrase: str
    sound: str
    tiny_sound: str
    climbs_low: bool = False
    fits_gap: bool = False
    likes_treats: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    reach: str = "ground"   # ground | low | gap
    scary_line: str = ""
    after_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    reaches: set[str] = field(default_factory=set)
    needs_treats: bool = False
    brave_style: str = ""
    success_line: str = ""
    qa_line: str = ""
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


def _r_child_worries(world: World) -> list[str]:
    pet = world.get("pet")
    child = world.get("child")
    out: list[str] = []
    if pet.meters["stuck"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__worry__")
    return out


def _r_comfort_after_rescue(world: World) -> list[str]:
    pet = world.get("pet")
    child = world.get("child")
    helper = world.get("helper")
    out: list[str] = []
    if pet.meters["found"] >= THRESHOLD:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            pet.meters["stuck"] = 0.0
            pet.memes["fear"] = 0.0
            child.memes["fear"] = 0.0
            child.memes["relief"] += 1
            child.memes["joy"] += 1
            child.memes["bravery"] += 1
            helper.memes["pride"] += 1
            out.append("__comfort__")
    return out


CAUSAL_RULES = [
    Rule(name="child_worries", tag="emotion", apply=_r_child_worries),
    Rule(name="comfort_after_rescue", tag="emotion", apply=_r_comfort_after_rescue),
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


SETTINGS = {
    "yard": Setting(
        id="yard",
        place="the moonlit yard",
        sky="A silver moon hung high",
        ground_line="the grass whispered softly by",
        tags={"night", "yard"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the little orchard",
        sky="A pale moon peeped through the leaves",
        ground_line="the trees swayed slow in the breeze",
        tags={"night", "orchard"},
    ),
    "barn": Setting(
        id="barn",
        place="the warm old barn",
        sky="A lantern glow lay low",
        ground_line="the hay made a sleepy gold show",
        tags={"night", "barn"},
    ),
}

PETS = {
    "kitten": Pet(
        id="kitten",
        label="kitten",
        phrase="a soft gray kitten",
        sound="mew",
        tiny_sound="a tiny mew",
        climbs_low=True,
        fits_gap=True,
        likes_treats=False,
        tags={"kitten", "pet"},
    ),
    "puppy": Pet(
        id="puppy",
        label="puppy",
        phrase="a round little puppy",
        sound="yip",
        tiny_sound="a tiny yip",
        climbs_low=False,
        fits_gap=False,
        likes_treats=True,
        tags={"puppy", "pet", "treats"},
    ),
    "duckling": Pet(
        id="duckling",
        label="duckling",
        phrase="a fluffy yellow duckling",
        sound="peep",
        tiny_sound="a tiny peep",
        climbs_low=False,
        fits_gap=True,
        likes_treats=False,
        tags={"duckling", "pet"},
    ),
}

HIDEOUTS = {
    "berry_bush": Hideout(
        id="berry_bush",
        label="berry bush",
        phrase="a scratchy berry bush",
        reach="ground",
        scary_line="The leaves looked thick, and the middle was dark as a hush.",
        after_line="Its little nose poked out of the bush with a wiggle and a swish.",
        tags={"bush", "ground"},
    ),
    "apple_branch": Hideout(
        id="apple_branch",
        label="apple branch",
        phrase="a low apple branch",
        reach="low",
        scary_line="The branch looked wobbly and high to small eyes on the ground.",
        after_line="Soon small paws were safe below, and no more trembly sounds were found.",
        tags={"tree", "branch"},
    ),
    "porch_gap": Hideout(
        id="porch_gap",
        label="porch gap",
        phrase="the dark gap under the porch",
        reach="gap",
        scary_line="The boards made a narrow shadow stripe, snug and hard to see through.",
        after_line="Bright eyes blinked from the gap, then pattered out into the dew.",
        tags={"porch", "gap"},
    ),
}

METHODS = {
    "blanket_coax": Method(
        id="blanket_coax",
        label="blanket and whisper",
        phrase="a soft blanket and a whisper",
        reaches={"ground"},
        needs_treats=False,
        brave_style="knelt close and spoke in a low, steady voice",
        success_line="With the blanket spread and a whisper so sweet, the little one shuffled out on cautious feet.",
        qa_line="used a soft blanket and a calm whisper to coax the pet out",
        tags={"blanket", "gentle"},
    ),
    "step_stool": Method(
        id="step_stool",
        label="step stool",
        phrase="a sturdy step stool",
        reaches={"low"},
        needs_treats=False,
        brave_style="climbed one safe step while a grown-up held the stool still",
        success_line="Up went one step, no more, no less, and brave small hands untangled the mess.",
        qa_line="used a steady step stool while the grown-up held it",
        tags={"stool", "safe_reach"},
    ),
    "treat_trail": Method(
        id="treat_trail",
        label="treat trail",
        phrase="a neat little trail of treats",
        reaches={"ground", "gap"},
        needs_treats=True,
        brave_style="shook the treat tin and waited without grabbing",
        success_line="Tap, tap, treat by treat, a hopeful nose came out to eat.",
        qa_line="laid a careful trail of treats and waited for the pet to come out",
        tags={"treats", "gentle"},
    ),
}


def pet_fits_hideout(pet: Pet, hideout: Hideout) -> bool:
    if hideout.reach == "low":
        return pet.climbs_low
    if hideout.reach == "gap":
        return pet.fits_gap
    return True


def method_fits(pet: Pet, hideout: Hideout, method: Method) -> bool:
    if hideout.reach not in method.reaches:
        return False
    if method.needs_treats and not pet.likes_treats:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for pet_id, pet in PETS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if not pet_fits_hideout(pet, hideout):
                    continue
                for method_id, method in METHODS.items():
                    if method_fits(pet, hideout, method):
                        combos.append((setting_id, pet_id, hideout_id, method_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    pet: str
    hideout: str
    method: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


CHILD_NAMES = {
    "girl": ["Lila", "Mia", "Nora", "Tess", "Ruby", "Ivy"],
    "boy": ["Owen", "Max", "Leo", "Finn", "Eli", "Jude"],
}
HELPER_NAMES = {
    "mother": ["Mama", "Mom"],
    "father": ["Dad", "Papa"],
    "aunt": ["Aunt May", "Aunt June"],
    "uncle": ["Uncle Ben", "Uncle Ray"],
}
TRAITS = ["careful", "steady", "gentle", "bright", "thoughtful"]


def explain_rejection(pet: Pet, hideout: Hideout, method: Optional[Method] = None) -> str:
    if not pet_fits_hideout(pet, hideout):
        if hideout.reach == "low":
            return (
                f"(No story: a {pet.label} would not plausibly end up perched on {hideout.phrase}. "
                f"Choose a climber like a kitten, or choose a ground or gap hideout.)"
            )
        if hideout.reach == "gap":
            return (
                f"(No story: a {pet.label} is too big for {hideout.phrase}. "
                f"Choose a smaller pet or a less snug hiding place.)"
            )
    if method is not None and not method_fits(pet, hideout, method):
        if hideout.reach not in method.reaches:
            return (
                f"(No story: {method.phrase} does not safely reach {hideout.phrase}. "
                f"Pick a method that matches that kind of hiding place.)"
            )
        if method.needs_treats and not pet.likes_treats:
            return (
                f"(No story: {method.phrase} only makes sense for a pet that follows treats. "
                f"Choose the puppy, or choose a different rescue method.)"
            )
    return "(No story: that combination is not reasonable in this world.)"


def predict_confirmation(world: World, method: Method) -> dict:
    sim = world.copy()
    pet = sim.get("pet")
    child = sim.get("child")
    child.memes["courage"] += 1
    if method_fits(PETS[sim.facts["pet_cfg"].id], HIDEOUTS[sim.facts["hideout_cfg"].id], method):
        pet.meters["confirmed"] += 1
        pet.meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "confirmed": pet.meters["confirmed"] >= THRESHOLD,
        "child_relief": child.memes["relief"] >= THRESHOLD,
    }


def opening(world: World, setting: Setting, child: Entity, helper: Entity, pet: Entity) -> None:
    child.memes["joy"] += 1
    pet.memes["trust"] += 1
    world.say(
        f"{setting.sky}, and {setting.ground_line}. "
        f"{child.id} and {helper.id} played outside with {pet.phrase}, and everything felt fine."
    )
    world.say(
        f"{pet.phrase.capitalize()} bounced near {child.id}'s shoes; "
        f"the night felt soft, and the game felt new."
    )


def pet_slips_away(world: World, pet: Entity, hideout: Hideout) -> None:
    pet.meters["stuck"] += 1
    pet.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then there came {pet.attrs['tiny_sound']} from {hideout.phrase}, "
        f"and playtime changed its tune too soon."
    )
    world.say(hideout.scary_line)


def child_hesitates(world: World, child: Entity, hideout: Hideout) -> None:
    world.say(
        f"{child.id} took one step, then stopped mid-way. "
        f"{child.pronoun().capitalize()} felt a fluttery fear that wanted to say, "
        f'"Not tonight. Not that way."'
    )
    if hideout.reach == "gap":
        world.say("The dark little slot looked tight and gray; it made brave thoughts wobble, just for a day.")
    elif hideout.reach == "low":
        world.say("Looking up from the ground made the branch seem taller than before, and a bit more strange than a game at the door.")
    else:
        world.say("The thorny leaves made a prickly screen, and what hid inside could not be seen.")


def helper_guides(world: World, child: Entity, helper: Entity, pet: Entity, hideout: Hideout, method: Method) -> None:
    pred = predict_confirmation(world, method)
    world.facts["predicted_confirmed"] = pred["confirmed"]
    world.say(
        f'{helper.id} knelt beside {child.id}. "Brave does not mean rushing in," '
        f"{helper.pronoun()} said with a smile so thin. "
        f'"We can go slowly, safely, and confirm what we hear before we draw near."'
    )
    world.say(
        f"So {child.id} chose {method.phrase}. "
        f"{child.pronoun().capitalize()} {method.brave_style}, and that careful choice began the brave part of the night."
    )


def rescue(world: World, child: Entity, helper: Entity, pet: Entity, hideout: Hideout, method: Method) -> None:
    pet.meters["confirmed"] += 1
    pet.meters["found"] += 1
    child.memes["courage"] += 1
    world.facts["confirmed_by_child"] = True
    propagate(world, narrate=False)
    world.say(
        f"At last {child.id} could confirm the sound was really {pet.phrase}. "
        f"It was not a monster, not a mystery deep; it was only a frightened little peep."
    )
    world.say(method.success_line)
    world.say(hideout.after_line)
    world.say(
        f"{helper.id} opened warm arms wide, and {pet.label} nestled safe at {child.id}'s side."
    )


def ending(world: World, setting: Setting, child: Entity, helper: Entity, pet: Entity) -> None:
    world.say(
        f"Soon the fear was small and the smiles were bright. "
        f"{child.id} laughed as {pet.label} cuddled close in the light."
    )
    world.say(
        f"Back in {setting.place}, they walked slow and merry together. "
        f"{child.id} had learned that brave can be gentle in any kind of weather."
    )


def tell(
    setting: Setting,
    pet_cfg: Pet,
    hideout_cfg: Hideout,
    method_cfg: Method,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    pet = world.add(
        Entity(
            id="pet",
            kind="thing",
            type="pet",
            label=pet_cfg.label,
            phrase=pet_cfg.phrase,
            role="pet",
            attrs={"tiny_sound": pet_cfg.tiny_sound, "sound": pet_cfg.sound},
        )
    )
    place = world.add(
        Entity(
            id="hideout",
            kind="thing",
            type="hideout",
            label=hideout_cfg.label,
            phrase=hideout_cfg.phrase,
            role="hideout",
        )
    )

    child.memes["care"] += 1
    helper.memes["calm"] += 1
    world.facts.update(
        setting=setting,
        pet_cfg=pet_cfg,
        hideout_cfg=hideout_cfg,
        method_cfg=method_cfg,
        child=child,
        helper=helper,
        pet=pet,
        place=place,
    )

    opening(world, setting, child, helper, pet)
    world.para()
    pet_slips_away(world, pet, hideout_cfg)
    child_hesitates(world, child, hideout_cfg)
    world.para()
    helper_guides(world, child, helper, pet, hideout_cfg, method_cfg)
    rescue(world, child, helper, pet, hideout_cfg, method_cfg)
    world.para()
    ending(world, setting, child, helper, pet)

    world.facts.update(
        confirmed=pet.meters["confirmed"] >= THRESHOLD,
        rescued=pet.meters["found"] >= THRESHOLD,
        happy=child.memes["joy"] >= THRESHOLD and child.memes["relief"] >= THRESHOLD,
        brave=child.memes["bravery"] >= THRESHOLD or child.memes["courage"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "kitten": [
        (
            "Why might a kitten hide in a small place?",
            "Kittens like little hiding spots when they feel startled. Small places can feel snug and safe to them."
        )
    ],
    "puppy": [
        (
            "Why does a puppy follow treats?",
            "A puppy often follows treats because the smell is exciting and familiar. A careful treat trail can guide it without grabbing or scaring it."
        )
    ],
    "duckling": [
        (
            "Why does a duckling make soft peeping sounds?",
            "A duckling peeps to call for help or company. The sound lets bigger helpers know where it is."
        )
    ],
    "blanket": [
        (
            "Why can a soft blanket help a scared pet?",
            "A soft blanket can feel warm and gentle. That helps a frightened pet come closer without feeling chased."
        )
    ],
    "stool": [
        (
            "Why should a child use a step stool carefully?",
            "A step stool should stay steady on the ground while a grown-up watches. Using one safe step is better than climbing on something wobbly."
        )
    ],
    "treats": [
        (
            "What is a treat trail?",
            "A treat trail is a few small treats placed one after another. It can gently guide a pet out of a hiding place."
        )
    ],
    "brave": [
        (
            "What does brave mean?",
            "Brave does not mean doing something wild or unsafe. Brave means feeling scared and still choosing a careful, helpful action."
        )
    ],
    "confirm": [
        (
            "What does confirm mean?",
            "To confirm something is to check and make sure it is really true. In a story, you might confirm a sound before you decide what to do next."
        )
    ],
}
KNOWLEDGE_ORDER = ["confirm", "brave", "kitten", "puppy", "duckling", "blanket", "stool", "treats"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    pet_cfg = f["pet_cfg"]
    hideout = f["hideout_cfg"]
    method = f["method_cfg"]
    return [
        (
            f'Write a gentle rhyming story for a 3-to-5-year-old that includes the word '
            f'"confirm" and shows bravery ending in relief.'
        ),
        (
            f"Tell a rhyming bedtime story where {child.id} hears {pet_cfg.tiny_sound} in "
            f"{hideout.phrase}, feels scared, and bravely uses {method.phrase} to confirm what is there."
        ),
        (
            f"Write a happy-ending story in a soft rhyme where a child chooses the safe way to help "
            f"a frightened {pet_cfg.label} instead of rushing."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    pet_cfg = f["pet_cfg"]
    hideout = f["hideout_cfg"]
    method = f["method_cfg"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who heard a frightened sound in the night, and {helper.id}, the {helper_word} who stayed close and calm."
        ),
        (
            f"What problem began the story?",
            f"{pet_cfg.phrase.capitalize()} slipped into {hideout.phrase} and sounded scared. That made the game stop and turned the night tense."
        ),
        (
            f"Why was {child.id} afraid at first?",
            f"{child.id} could hear the sound, but could not see what was hiding in the dark place. Not knowing what was there made the hiding spot feel bigger and scarier."
        ),
        (
            f"How was {child.id} brave?",
            f"{child.id} did not rush or grab wildly. Instead, {child.pronoun()} chose {method.phrase} and used it carefully to confirm what was there, which is a safe kind of bravery."
        ),
        (
            "What did confirm mean in the story?",
            f"It meant checking carefully to make sure the sound really came from {pet_cfg.phrase}. Once {child.id} confirmed that, the right help became clear."
        ),
        (
            f"How did they help the {pet_cfg.label}?",
            f"They {method.qa_line}. The method fit the hiding place, so the pet could come out without getting more scared."
        ),
        (
            "How did the story end?",
            f"It ended happily with the {pet_cfg.label} safe again and close beside {child.id}. The last image shows fear turning into smiles, which proves something changed."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pet_cfg = f["pet_cfg"]
    method = f["method_cfg"]
    tags = {"confirm", "brave"} | set(pet_cfg.tags) | set(method.tags)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="yard",
        pet="kitten",
        hideout="berry_bush",
        method="blanket_coax",
        child_name="Lila",
        child_gender="girl",
        helper_name="Mama",
        helper_type="mother",
        trait="gentle",
    ),
    StoryParams(
        setting="orchard",
        pet="kitten",
        hideout="apple_branch",
        method="step_stool",
        child_name="Finn",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="steady",
    ),
    StoryParams(
        setting="barn",
        pet="puppy",
        hideout="porch_gap",
        method="treat_trail",
        child_name="Ruby",
        child_gender="girl",
        helper_name="Uncle Ben",
        helper_type="uncle",
        trait="bright",
    ),
    StoryParams(
        setting="yard",
        pet="duckling",
        hideout="porch_gap",
        method="blanket_coax",
        child_name="Owen",
        child_gender="boy",
        helper_name="Aunt May",
        helper_type="aunt",
        trait="careful",
    ),
]


ASP_RULES = r"""
% pet and hideout compatibility
pet_fits(P, H) :- hideout_reach(H, ground), pet(P).
pet_fits(P, H) :- hideout_reach(H, low), climbs_low(P).
pet_fits(P, H) :- hideout_reach(H, gap), fits_gap(P).

% method compatibility
method_fits(P, H, M) :- pet_fits(P, H), hideout_reach(H, R), reaches(M, R),
                        not needs_treats(M).
method_fits(P, H, M) :- pet_fits(P, H), hideout_reach(H, R), reaches(M, R),
                        needs_treats(M), likes_treats(P).

valid(S, P, H, M) :- setting(S), pet(P), hideout(H), method(M), method_fits(P, H, M).
happy(S, P, H, M) :- valid(S, P, H, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, pet in PETS.items():
        lines.append(asp.fact("pet", pid))
        if pet.climbs_low:
            lines.append(asp.fact("climbs_low", pid))
        if pet.fits_gap:
            lines.append(asp.fact("fits_gap", pid))
        if pet.likes_treats:
            lines.append(asp.fact("likes_treats", pid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("hideout_reach", hid, hideout.reach))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for r in sorted(method.reaches):
            lines.append(asp.fact("reaches", mid, r))
        if method.needs_treats:
            lines.append(asp.fact("needs_treats", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if "confirm" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story did not include 'confirm'.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child safely confirms a scary sound, shows bravery, and reaches a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pet and args.hideout:
        pet = PETS[args.pet]
        hideout = HIDEOUTS[args.hideout]
        if not pet_fits_hideout(pet, hideout):
            raise StoryError(explain_rejection(pet, hideout))
    if args.pet and args.hideout and args.method:
        pet = PETS[args.pet]
        hideout = HIDEOUTS[args.hideout]
        method = METHODS[args.method]
        if not method_fits(pet, hideout, method):
            raise StoryError(explain_rejection(pet, hideout, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.pet is None or c[1] == args.pet)
        and (args.hideout is None or c[2] == args.hideout)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, pet_id, hideout_id, method_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    child_name = args.child_name or rng.choice(CHILD_NAMES[child_gender])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES[helper_type])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        pet=pet_id,
        hideout=hideout_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    pet = PETS[params.pet]
    hideout = HIDEOUTS[params.hideout]
    method = METHODS[params.method]
    if not pet_fits_hideout(pet, hideout):
        raise StoryError(explain_rejection(pet, hideout))
    if not method_fits(pet, hideout, method):
        raise StoryError(explain_rejection(pet, hideout, method))

    world = tell(
        setting=SETTINGS[params.setting],
        pet_cfg=pet,
        hideout_cfg=hideout,
        method_cfg=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program("#show valid/4.\n#show happy/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, pet, hideout, method) combos:\n")
        for setting_id, pet_id, hideout_id, method_id in combos:
            print(f"  {setting_id:8} {pet_id:8} {hideout_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.pet} in {p.hideout} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
