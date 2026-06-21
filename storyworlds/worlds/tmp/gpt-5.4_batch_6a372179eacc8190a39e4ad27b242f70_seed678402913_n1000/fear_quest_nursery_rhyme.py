#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py
======================================================

A tiny storyworld for gentle nursery-rhyme-like quest tales about fear.

In this world, a small child must go on a little quest to fetch a needed thing
before bedtime. The path holds one clear kind of fear: shadows, wind, or an owl
hoot. A helper aid only belongs in the story when it honestly meets that fear.
The simulation tracks both physical state (walking, carrying, found objects) and
emotional state (fear, comfort, pride), then renders a short, rhyming tale from
that state.

Run it
------
    python storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py --place willow_gate --fear shadows --aid lantern
    python storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py --fear owl_hoot --aid lantern
    python storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fear_quest_nursery_rhyme.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    # physical and emotional state
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


# ---------------------------------------------------------------------------
# Domain knobs.
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    phrase: str
    path_line: str
    hiding_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FearKind:
    id: str
    label: str
    source: str
    warning_line: str
    rising_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    action_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    use_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world params.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    fear: str
    aid: str
    prize: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World container.
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


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_path_fear(world: World) -> list[str]:
    hero = world.entities.get("hero")
    place = world.entities.get("place")
    fear = world.entities.get("fear")
    if hero is None or place is None or fear is None:
        return []
    if hero.meters["on_path"] < THRESHOLD:
        return []
    sig = ("path_fear", fear.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 2
    place.meters["spooky"] += 1
    return ["__fear_rises__"]


def _r_aid_comfort(world: World) -> list[str]:
    hero = world.entities.get("hero")
    aid = world.entities.get("aid")
    fear = world.entities.get("fear")
    if hero is None or aid is None or fear is None:
        return []
    if hero.meters["using_aid"] < THRESHOLD:
        return []
    if fear.id not in aid.attrs.get("helps", set()):
        return []
    sig = ("aid_comfort", aid.id, fear.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["comfort"] += 2
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 2)
    hero.memes["brave"] += 1
    return ["__aid_works__"]


def _r_found_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    child = world.entities.get("little_one")
    prize = world.entities.get("prize")
    if hero is None or child is None or prize is None:
        return []
    if prize.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    hero.memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="path_fear", tag="emotional", apply=_r_path_fear),
    Rule(name="aid_comfort", tag="emotional", apply=_r_aid_comfort),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if not bit.startswith("__"):
                world.say(bit)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def aid_fits(fear_id: str, aid_id: str) -> bool:
    return fear_id in AIDS[aid_id].helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for fear_id in FEARS:
            for aid_id in AIDS:
                if not aid_fits(fear_id, aid_id):
                    continue
                for prize_id in PRIZES:
                    combos.append((place_id, fear_id, aid_id, prize_id))
    return combos


def explain_rejection(fear_id: str, aid_id: str) -> str:
    fear = FEARS[fear_id]
    aid = AIDS[aid_id]
    good = ", ".join(sorted(a.id for a in AIDS.values() if fear_id in a.helps))
    return (
        f"(No story: {aid.label} does not honestly help with {fear.label}. "
        f"In this world, the quest tool must answer the fear itself. "
        f"For {fear.label}, try: {good}.)"
    )


# ---------------------------------------------------------------------------
# Prediction.
# ---------------------------------------------------------------------------
def predict_trip(world: World) -> dict:
    sim = world.copy()
    start_quest(sim, narrate=False)
    use_aid(sim, narrate=False)
    return {
        "fear_after_path": sim.get("hero").memes["fear"],
        "comfort_after_aid": sim.get("hero").memes["comfort"],
        "brave_after_aid": sim.get("hero").memes["brave"],
    }


# ---------------------------------------------------------------------------
# Screenplay verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, child: Entity, prize: Prize) -> None:
    hero.memes["care"] += 1
    child.memes["sad"] += 1
    world.say(
        f"{hero.id} had little feet and a little song, and the dusk was soft and mild."
    )
    world.say(
        f"But {child.id}, the {helper.attrs['kin_word']} baby, could not rest without {prize.phrase}."
    )
    world.say(
        f"So {helper.id} bent low and said, "
        f'"Dear {hero.id}, will you go on a quest and bring it home before the moon grows old?"'
    )


def name_the_place(world: World, place: Place, prize: Prize) -> None:
    world.say(
        f"{prize.phrase.capitalize()} had slipped away to {place.phrase}, {place.hiding_line}."
    )


def feel_fear(world: World, hero: Entity, fear: FearKind) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} whispered, 'I feel fear in my knees, for {fear.source} does not sound kind to me.'"
    )


def offer_aid(world: World, helper: Entity, aid: Aid, fear: FearKind) -> None:
    pred = predict_trip(world)
    world.facts["predicted_fear_after_path"] = pred["fear_after_path"]
    world.facts["predicted_comfort_after_aid"] = pred["comfort_after_aid"]
    world.say(
        f'{helper.id} gave {helper.pronoun("object")} {aid.phrase} and said, '
        f'"Take this with you. {fear.warning_line} {aid.action_line}"'
    )


def start_quest(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    place = world.get("place")
    fear = world.get("fear")
    hero.meters["on_path"] += 1
    hero.meters["walking"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"So {hero.id} tip-tap went by {place.path_line}, and {fear.rising_line}"
        )


def use_aid(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    aid = world.get("aid")
    hero.meters["using_aid"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{hero.id} held {aid.label} close. {aid.action_line}"
        )


def find_prize(world: World, prize: Prize, place: Place) -> None:
    hero = world.get("hero")
    prize_ent = world.get("prize")
    prize_ent.meters["found"] += 1
    prize_ent.meters["carried"] += 1
    hero.meters["carrying"] += 1
    propagate(world, narrate=False)
    world.say(
        f"And there by {place.label}, tucked small and bright, lay {prize.phrase} in the silver light."
    )


def return_home(world: World, hero: Entity, child: Entity, prize: Prize) -> None:
    hero.meters["home_again"] += 1
    hero.meters["on_path"] = 0.0
    hero.memes["pride"] += 2
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    child.memes["sad"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"Back came {hero.id}, quick as a rhyme, with {prize.phrase} just in time."
    )
    world.say(
        f"{child.id} cuddled it close, gave a sleepy sigh, and the fretful tears went drifting by."
    )


def ending(world: World, hero: Entity, aid: Aid) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"Then {hero.id} smiled and stood up tall. The fear was small, not big at all."
    )
    world.say(
        f"For a brave little heart may tremble and quiver, yet still step on with song and shiver."
    )
    world.say(
        f"And {aid.label} rested by the bed, while moonlight stitched the dreams ahead."
    )


# ---------------------------------------------------------------------------
# Full tell.
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    fear: FearKind,
    aid: Aid,
    prize: Prize,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    helper_role: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait, "small"],
        attrs={"name": hero_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        phrase=helper_name,
        role="helper",
        traits=["gentle"],
        attrs={"kin_word": helper_role, "name": helper_name},
    ))
    child = world.add(Entity(
        id="little_one",
        kind="character",
        type="child",
        label="the little one",
        phrase="the little one",
        role="recipient",
        traits=["sleepy"],
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=place.label,
        phrase=place.phrase,
        tags=set(place.tags),
    ))
    fear_ent = world.add(Entity(
        id="fear",
        kind="thing",
        type="fear",
        label=fear.label,
        phrase=fear.source,
        tags=set(fear.tags),
    ))
    aid_ent = world.add(Entity(
        id="aid",
        kind="thing",
        type="aid",
        label=aid.label,
        phrase=aid.phrase,
        portable=True,
        tags=set(aid.tags),
        attrs={"helps": set(aid.helps)},
    ))
    prize_ent = world.add(Entity(
        id="prize",
        kind="thing",
        type="prize",
        label=prize.label,
        phrase=prize.phrase,
        portable=True,
        tags=set(prize.tags),
    ))

    introduce(world, hero, helper, child, prize)
    name_the_place(world, place, prize)

    world.para()
    feel_fear(world, hero, fear)
    offer_aid(world, helper, aid, fear)

    world.para()
    start_quest(world, narrate=True)
    use_aid(world, narrate=True)
    find_prize(world, prize, place)

    world.para()
    return_home(world, hero, child, prize)
    ending(world, hero, aid)

    world.facts.update(
        hero=hero,
        helper=helper,
        child=child,
        place_cfg=place,
        fear_cfg=fear,
        aid_cfg=aid,
        prize_cfg=prize,
        outcome="success",
        hero_name=hero_name,
        helper_name=helper_name,
        fear_before=1.0,
        fear_after=hero.memes["fear"],
        comfort=hero.memes["comfort"],
        pride=hero.memes["pride"],
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
PLACES = {
    "willow_gate": Place(
        id="willow_gate",
        label="the willow gate",
        phrase="the willow gate",
        path_line="the bent willow gate",
        hiding_line="where the leaves made a hush-hush shade",
        tags={"garden", "night"},
    ),
    "mossy_step": Place(
        id="mossy_step",
        label="the mossy step",
        phrase="the mossy step by the shed",
        path_line="the mossy step by the shed",
        hiding_line="where the corner stayed cool and green",
        tags={"garden", "shed"},
    ),
    "berry_arbor": Place(
        id="berry_arbor",
        label="the berry arbor",
        phrase="the berry arbor",
        path_line="the berry arbor in the lane",
        hiding_line="where the vines made a little screen",
        tags={"garden", "berries"},
    ),
}

FEARS = {
    "shadows": FearKind(
        id="shadows",
        label="shadows",
        source="the long black shadows",
        warning_line="When shadows stretch, let a kind light show you what is only a bush and what is only a stone.",
        rising_line="the long black shadows wiggled and grew",
        tags={"shadows", "fear"},
    ),
    "wind": FearKind(
        id="wind",
        label="wind",
        source="the windy hush in the leaves",
        warning_line="When wind goes woo, keep a steady thing in hand and take one good breath after another.",
        rising_line="the windy hush went woo-woo through the blue",
        tags={"wind", "fear"},
    ),
    "owl_hoot": FearKind(
        id="owl_hoot",
        label="an owl hoot",
        source="the owl that called from the dark pear tree",
        warning_line="When the owl calls out, answer with your own soft sound, and the night will feel less strange.",
        rising_line="the owl went hoo from the dark pear tree",
        tags={"owl", "fear"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="the lantern",
        phrase="a tin-star lantern",
        helps={"shadows"},
        action_line="Its little gold glow made the path plain and true.",
        qa_line="The lantern helped by turning shadows back into ordinary leaves, stones, and gateposts.",
        tags={"lantern", "light"},
    ),
    "breathing_ribbon": Aid(
        id="breathing_ribbon",
        label="the ribbon",
        phrase="a breathing ribbon to squeeze in a fist",
        helps={"wind"},
        action_line="With each squeeze and each breath, the rushy wind seemed smaller.",
        qa_line="The ribbon gave the child a steady thing to hold while breathing slowly through the windy fear.",
        tags={"breathing", "ribbon"},
    ),
    "humming_song": Aid(
        id="humming_song",
        label="the humming song",
        phrase="a pocket humming song",
        helps={"owl_hoot"},
        action_line="A soft hum answered the hoot, and the strange sound no longer felt lonely.",
        qa_line="The humming song answered the owl sound with a gentle sound of its own, so the night felt friendlier.",
        tags={"song", "owl"},
    ),
}

PRIZES = {
    "lullaby_bell": Prize(
        id="lullaby_bell",
        label="lullaby bell",
        phrase="the little lullaby bell",
        use_line="Its tiny ring made sleepy eyes blink slow.",
        tags={"bell", "bedtime"},
    ),
    "moon_kerchief": Prize(
        id="moon_kerchief",
        label="moon kerchief",
        phrase="the moon-stitched kerchief",
        use_line="It tucked warm under a chin at bedtime.",
        tags={"kerchief", "bedtime"},
    ),
    "soft_bunny": Prize(
        id="soft_bunny",
        label="soft bunny",
        phrase="the soft bedtime bunny",
        use_line="Its velvet ears brushed sleepy cheeks.",
        tags={"bunny", "bedtime"},
    ),
}

GIRL_NAMES = ["Milly", "Daisy", "Tessa", "Lula", "Poppy", "Nell"]
BOY_NAMES = ["Toby", "Bram", "Ned", "Otis", "Pip", "Robin"]
TRAITS = ["timid", "gentle", "careful", "soft-hearted", "small and steady"]
HELPER_ROLES = ["mother", "father", "sister", "brother"]


# ---------------------------------------------------------------------------
# QA generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "fear": [
        (
            "What is fear?",
            "Fear is the feeling that tells your body something might be scary. It can make your heart beat faster, but it does not mean you cannot be brave."
        )
    ],
    "shadows": [
        (
            "Why can shadows look scary at night?",
            "Shadows get long and wobbly in dim light, so ordinary things can look strange. When more light shines on them, they often turn back into familiar shapes."
        )
    ],
    "wind": [
        (
            "Why can wind sound spooky?",
            "Wind pushes through leaves, cracks, and branches, and that can make wooing or rushing noises. The sound is real, but it does not mean danger is hiding there."
        )
    ],
    "owl": [
        (
            "Why do owls hoot?",
            "Owls hoot to talk to other owls and mark where they are. A hoot can sound eerie at night, but it is just part of how an owl lives."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so you can see where you are going. Seeing clearly can make a dark place feel less frightening."
        )
    ],
    "breathing": [
        (
            "Why can slow breathing help when you feel afraid?",
            "Slow breathing helps your body settle down. It gives you something steady to do while the scary feeling grows smaller."
        )
    ],
    "song": [
        (
            "How can singing or humming help with fear?",
            "A soft song gives your mind a friendly sound to follow. That can make a strange noise feel less big and lonely."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a little journey with a purpose. Someone goes somewhere to find, fetch, or fix something important."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime objects matter to little children?",
            "A familiar bedtime thing can help a child feel safe and ready to rest. It becomes part of the calm pattern that tells the body it is time to sleep."
        )
    ],
}
KNOWLEDGE_ORDER = ["fear", "quest", "shadows", "wind", "owl", "lantern", "breathing", "song", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    fear = f["fear_cfg"]
    aid = f["aid_cfg"]
    prize = f["prize_cfg"]
    place = f["place_cfg"]
    return [
        f'Write a nursery-rhyme-style quest story for a young child that includes the word "fear".',
        f"Tell a gentle bedtime quest where {hero.label} feels fear of {fear.label}, goes to {place.phrase}, and uses {aid.label} to bring back {prize.phrase}.",
        f"Write a short rhyming story in which a small child trembles at first but still finishes a quest and comes home proud."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    child = f["child"]
    fear = f["fear_cfg"]
    aid = f["aid_cfg"]
    prize = f["prize_cfg"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who goes on a small quest at dusk, and {helper.label}, who helps {hero.pronoun('object')} get ready. The quest matters because {child.label} cannot settle without {prize.phrase}."
        ),
        (
            f"Why did {hero.label} go to {place.label}?",
            f"{hero.label} went there to fetch {prize.phrase} before bedtime. The little one needed it in order to feel calm enough to rest."
        ),
        (
            f"What was {hero.label} afraid of?",
            f"{hero.label} felt fear because of {fear.source}. The path itself was ordinary, but that sound or sight made the dusk feel much bigger."
        ),
        (
            f"How did {helper.label} help with the fear?",
            f"{helper.label} gave {hero.label} {aid.phrase}. {aid.qa_line}"
        ),
        (
            "How did the quest end?",
            f"The quest ended well because {hero.label} found {prize.phrase} and carried it home. The little one grew calm, and {hero.label}'s fear shrank into pride."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fear", "quest", "bedtime"} | set(world.facts["fear_cfg"].tags) | set(world.facts["aid_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="willow_gate",
        fear="shadows",
        aid="lantern",
        prize="lullaby_bell",
        hero_name="Milly",
        hero_gender="girl",
        helper_name="Mama",
        helper_gender="mother",
        helper_role="mother",
        trait="timid",
    ),
    StoryParams(
        place="mossy_step",
        fear="wind",
        aid="breathing_ribbon",
        prize="moon_kerchief",
        hero_name="Toby",
        hero_gender="boy",
        helper_name="Papa",
        helper_gender="father",
        helper_role="father",
        trait="careful",
    ),
    StoryParams(
        place="berry_arbor",
        fear="owl_hoot",
        aid="humming_song",
        prize="soft_bunny",
        hero_name="Daisy",
        hero_gender="girl",
        helper_name="Ned",
        helper_gender="boy",
        helper_role="brother",
        trait="gentle",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(F, A) :- fear(F), aid(A), helps(A, F).
valid(P, F, A, Z) :- place(P), fear(F), aid(A), prize(Z), compatible(F, A).

outcome(success) :- chosen_fear(F), chosen_aid(A), compatible(F, A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FEARS:
        lines.append(asp.fact("fear", fid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for fear_id in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, fear_id))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
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
        asp.fact("chosen_fear", params.fear),
        asp.fact("chosen_aid", params.aid),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    cases = list(CURATED)
    for s in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py_outcome = "success" if aid_fits(params.fear, params.aid) else "?"
        if asp_outcome(params) != py_outcome:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme quest stories about fear. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fear", choices=FEARS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father", "girl", "boy"])
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fear and args.aid and not aid_fits(args.fear, args.aid):
        raise StoryError(explain_rejection(args.fear, args.aid))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fear is None or combo[1] == args.fear)
        and (args.aid is None or combo[2] == args.aid)
        and (args.prize is None or combo[3] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, fear_id, aid_id, prize_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)

    helper_role = args.helper_role or rng.choice(HELPER_ROLES)
    if args.helper_gender is not None:
        helper_gender = args.helper_gender
    else:
        helper_gender = {"mother": "mother", "father": "father", "sister": "girl", "brother": "boy"}[helper_role]

    if args.helper_name is not None:
        helper_name = args.helper_name
    else:
        if helper_role == "mother":
            helper_name = rng.choice(["Mama", "Mom", "Mother"])
        elif helper_role == "father":
            helper_name = rng.choice(["Papa", "Dad", "Father"])
        else:
            helper_name = rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
            if helper_name == hero_name:
                pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name]
                helper_name = rng.choice(pool)

    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        fear=fear_id,
        aid=aid_id,
        prize=prize_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.fear not in FEARS:
        raise StoryError(f"(Unknown fear: {params.fear})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if not aid_fits(params.fear, params.aid):
        raise StoryError(explain_rejection(params.fear, params.aid))

    world = tell(
        place=PLACES[params.place],
        fear=FEARS[params.fear],
        aid=AIDS[params.aid],
        prize=PRIZES[params.prize],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_role=params.helper_role,
        trait=params.trait,
    )

    # Replace ids with display names in final story.
    story = world.render().replace("hero", params.hero_name).replace("helper", params.helper_name)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, fear, aid, prize) combos:\n")
        for place_id, fear_id, aid_id, prize_id in combos:
            print(f"  {place_id:12} {fear_id:10} {aid_id:17} {prize_id}")
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
            header = f"### {p.hero_name}: {p.fear} at {p.place} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
