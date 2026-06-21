#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scone_obscure_magic_cautionary_surprise_rhyming_story.py
===================================================================================

A standalone story world for a small rhyming, cautionary magic tale about a
child who wants to make a scone, finds an obscure bit of kitchen magic, and
learns that quick secret tricks can make a lovely mess.

The world model is classical and state-driven:

    curious child + obscure magic on dough -> dough becomes lively
    lively dough                           -> bowl/tray/room get messy
    lively dough                           -> child fear rises
    calm grown-up fix                      -> dough settles or the mess is contained
    safe baking lesson                     -> child finishes with plain baking steps

The coverage constraint is small and deliberate: only obscure magic that
animates dough, applied to an actual dough vessel, yields a plausible story.
A fix is only accepted when it matches the kind of magical trouble. This keeps
the domain tight rather than broad and weak.

Run it
------
    python storyworlds/worlds/gpt-5.4/scone_obscure_magic_cautionary_surprise_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/scone_obscure_magic_cautionary_surprise_rhyming_story.py --magic moon_dust --target towel
    python storyworlds/worlds/gpt-5.4/scone_obscure_magic_cautionary_surprise_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/scone_obscure_magic_cautionary_surprise_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/scone_obscure_magic_cautionary_surprise_rhyming_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    edible: bool = False
    dough_vessel: bool = False
    magic_fix: bool = False
    safe_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mood:
    id: str
    room: str
    opening: str
    tray_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicThing:
    id: str
    label: str
    phrase: str
    hiding_place: str
    glow: str
    chant: str
    trouble: str
    tags: set[str] = field(default_factory=set)
    animates_dough: bool = True


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    vessel_image: str
    rise_word: str
    spread: int = 2
    dough_vessel: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    works_on: set[str] = field(default_factory=set)
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
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


def _r_lively_spreads(world: World) -> list[str]:
    out: list[str] = []
    dough = world.get("dough")
    if dough.meters["lively"] < THRESHOLD:
        return out
    target = world.get("target")
    sig = ("lively_spreads", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["messy"] += 1
    world.get("room").meters["danger"] += 1
    child = world.get("child")
    child.memes["fear"] += 1
    out.append("__lively__")
    return out


CAUSAL_RULES = [
    Rule(name="lively_spreads", tag="physical", apply=_r_lively_spreads),
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


def hazard_at_risk(magic: MagicThing, target: Target) -> bool:
    return magic.animates_dough and target.dough_vessel


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def magic_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def can_fix(fix: Fix, magic: MagicThing, target: Target, delay: int) -> bool:
    if magic.id not in fix.works_on:
        return False
    return fix.power >= magic_severity(target, delay)


def explain_rejection(magic: MagicThing, target: Target) -> str:
    if not target.dough_vessel:
        return (
            f"(No story: {magic.label} can only stir living dough trouble, but "
            f"{target.phrase} is not holding any dough. Pick a bowl or tray for the scone dough.)"
        )
    return "(No story: this combination does not create a plausible magical baking mishap.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    dough = sim.get("dough")
    dough.meters["lively"] += 1
    dough.meters["risen"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("target").meters["messy"],
        "danger": sim.get("room").meters["danger"],
    }


def opening_rhyme(world: World, child: Entity, elder: Entity, mood: Mood) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{mood.opening} In {mood.room}, with a spoon and a song, "
        f"{child.id} felt busy and merry all day long."
    )
    world.say(
        f"Beside {child.pronoun('object')} stood {elder.id}, calm and kind, "
        f"with jam for a scone and a kettle in mind."
    )


def set_baking_goal(world: World, child: Entity, target: Target) -> None:
    world.say(
        f'"I will make one small scone, round, warm, and bright, '
        f'and set it for tea on the tray just right," said {child.id}.'
    )
    world.say(
        f"The flour sat soft in {target.phrase}, "
        f"and the dough waited quiet in its floury place."
    )


def discover_magic(world: World, child: Entity, magic: MagicThing) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then high on {magic.hiding_place}, tucked back in the gloom, "
        f"{child.id} found an obscure tin that perfumed the room."
    )
    world.say(
        f'It gave a {magic.glow}, and a curl of old light; '
        f'its label was wobbly and hard to read right.'
    )


def warn(world: World, elder: Entity, child: Entity, magic: MagicThing) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_mess"] = pred["mess"]
    child.memes["caution_heard"] += 1
    world.say(
        f'"Leave that be," said {elder.id}. "{magic.label} is obscure. '
        f'Quick secret kitchen spells are seldom safe or sure."'
    )
    world.say(
        f'"A scone needs steady hands, not a shortcut that might roam. '
        f'If magic wakes the dough, it may dance around the home."'
    )


def defy(world: World, child: Entity, magic: MagicThing) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the tin looked bright and tiny, and the promise sounded grand; "
        f"{child.id} whispered {magic.chant} with a daring, floury hand."
    )


def back_down(world: World, child: Entity, elder: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} looked at {elder.id}, then at the old tin's gleam, "
        f"and put it back untouched upon the dusty beam."
    )
    world.say(
        f'"No obscure little shortcut," {child.pronoun()} said with care. '
        f'"I want a real warm scone, not trouble in the air."'
    )


def ignite_magic(world: World, child: Entity, magic: MagicThing, target: Target) -> None:
    dough = world.get("dough")
    dough.meters["lively"] += 1
    dough.meters["risen"] += 1
    world.facts["ignited"] = True
    propagate(world, narrate=False)
    world.say(
        f"At once the dough went bobbing with a hiccup, hop, and groan; "
        f"it puffed up past {target.vessel_image} and tried to flee alone."
    )
    world.say(
        f"{magic.trouble} The little lump that should have stayed "
        f"now bounced and rolled and would not do as it was made."
    )


def alarm(world: World, child: Entity, target: Target) -> None:
    world.say(
        f'"Oh dear!" cried {child.id}. "{target.label} is in a whirl! '
        f'The scone has turned to mischief and is spinning like a twirl!"'
    )


def calm_fix(world: World, elder: Entity, fix: Fix, target: Target) -> None:
    dough = world.get("dough")
    dough.meters["lively"] = 0.0
    dough.meters["settled"] += 1
    world.get("room").meters["danger"] = 0.0
    world.get("target").meters["messy"] += 0.0
    body = fix.success_text.replace("{target}", target.label)
    world.say(
        f"{elder.id} did not shout or stomp or race. "
        f"{elder.pronoun().capitalize()} {body}, all calm and full of grace."
    )
    world.say(
        "The strange bright fizz grew smaller, then folded to a sigh, "
        "and flour drifted softly like a cloud across the sky."
    )


def failed_fix(world: World, elder: Entity, fix: Fix, target: Target) -> None:
    world.get("room").meters["danger"] += 1
    world.get("room").meters["messy"] += 1
    world.get("dough").meters["wild"] += 1
    body = fix.fail_text.replace("{target}", target.label)
    world.say(
        f"{elder.id} tried to help, but {body}. "
        f"The dough sprang from the {target.label} and streaked across the floor."
    )
    world.say(
        "It bounced onto the curtain rod, then thumped the teacup stand, "
        "and left a trail of floury stars all through the kitchen land."
    )


def lesson(world: World, elder: Entity, child: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"Then {elder.id} knelt beside {child.id} and brushed away the flour. "
        f'"A surprise can seem delightful for a blink or half an hour," '
        f'said {elder.pronoun()}.'
    )
    world.say(
        '"But if a thing is obscure and you do not know its way, '
        'ask first, then bake the simple way, and keep the mess at bay."'
    )


def surprise_finish(world: World, child: Entity, elder: Entity, mood: Mood) -> None:
    child.memes["joy"] += 1
    child.memes["trust"] += 1
    world.say(
        f"Together then they mixed again, this time with measured care, "
        f"and soon a golden scone sent cozy butter through the air."
    )
    world.say(
        f"Here came the happy surprise at last, gentle, warm, and clear: "
        f"inside the finished scone was a heart of jam like ruby cheer."
    )
    world.say(
        f"{mood.tray_image} {child.id} laughed and set the treat by tea. "
        f'"The best surprise," {child.pronoun()} said, "is one made safely with {elder.id} and me."'
    )


def near_miss_finish(world: World, child: Entity, elder: Entity, mood: Mood) -> None:
    child.memes["joy"] += 1
    child.memes["trust"] += 1
    world.say(
        f"Together then they stirred the dough in an honest, simple tone, "
        f"and soon the room smelled sweet and warm around one golden scone."
    )
    world.say(
        f"The surprise was not a wild one hiding in obscure old dust. "
        f"It was the way a plain small bake could bloom from care and trust."
    )
    world.say(
        f"{mood.tray_image} {child.id} smiled a quiet, wiser smile. "
        f"The safe way made the tea-time shine, and that was best by far awhile."
    )


def burn_finish(world: World, child: Entity, elder: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f"At last the kitchen settled, though the room looked wild and white. "
        f"{child.id} was safe, but sorry for the long and floury fright."
    )
    world.say(
        f'"No secret obscure kitchen spell before I understand," said {child.id}. '
        f'"I would rather wait for help than chaos from my hand."'
    )
    world.say(
        f"And when they baked the next week's scone, {elder.id} stayed close to see "
        f"that every gentle step was plain, and safe as safe could be."
    )


def tell(
    mood: Mood,
    magic: MagicThing,
    target: Target,
    fix: Fix,
    child_name: str,
    child_gender: str,
    elder_name: str,
    elder_type: str,
    delay: int,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="elder"))
    room = world.add(Entity(id="room", type="room", label=mood.room))
    dough = world.add(Entity(id="dough", type="dough", label="scone dough", edible=True))
    vessel = world.add(
        Entity(
            id="target",
            type="vessel",
            label=target.label,
            phrase=target.phrase,
            dough_vessel=target.dough_vessel,
        )
    )

    opening_rhyme(world, child, elder, mood)
    set_baking_goal(world, child, target)

    world.para()
    discover_magic(world, child, magic)
    warn(world, elder, child, magic)

    averted = delay < 0
    if averted:
        back_down(world, child, elder)
        world.para()
        near_miss_finish(world, child, elder, mood)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        defy(world, child, magic)
        world.para()
        ignite_magic(world, child, magic, target)
        alarm(world, child, target)
        severity = magic_severity(target, delay)
        contained = can_fix(fix, magic, target, delay)
        world.para()
        if contained:
            calm_fix(world, elder, fix, target)
            lesson(world, elder, child)
            world.para()
            surprise_finish(world, child, elder, mood)
            outcome = "contained"
        else:
            failed_fix(world, elder, fix, target)
            lesson(world, elder, child)
            world.para()
            burn_finish(world, child, elder)
            outcome = "spilled"

    world.facts.update(
        mood=mood,
        magic=magic,
        target_cfg=target,
        fix=fix,
        child=child,
        elder=elder,
        dough=dough,
        target=vessel,
        outcome=outcome,
        severity=severity,
        delay=delay,
        ignited=world.facts.get("ignited", False),
        contained=contained,
    )
    return world


MOODS = {
    "teatime": Mood(
        id="teatime",
        room="the kitchen",
        opening="One silver afternoon, not loud but long,",
        tray_image="On a blue tea tray beneath the window tree,",
        tags={"tea"},
    ),
    "rainy": Mood(
        id="rainy",
        room="the warm kitchen",
        opening="One rainy afternoon with a pattering song,",
        tray_image="On a checked tea cloth by the steamy pane,",
        tags={"rain"},
    ),
    "sunny": Mood(
        id="sunny",
        room="the bright kitchen",
        opening="One honeyed afternoon with the daylight strong,",
        tray_image="On a sunny tray beside the geraniums red,",
        tags={"sun"},
    ),
}

MAGIC = {
    "moon_dust": MagicThing(
        id="moon_dust",
        label="moon dust",
        phrase="a pinch of moon dust",
        hiding_place="the obscure back shelf",
        glow="pearly shimmer",
        chant="Rise too soon beneath the moon",
        trouble="The bowl gave a wobble, the spoon gave a swoon.",
        tags={"magic", "powder"},
    ),
    "whisper_spice": MagicThing(
        id="whisper_spice",
        label="whisper spice",
        phrase="a shake of whisper spice",
        hiding_place="a crooked obscure cupboard",
        glow="silver-green blink",
        chant="Whirl and wake for goodness' sake",
        trouble="The tray made a rattle, the napkins took flight.",
        tags={"magic", "spice"},
    ),
    "star_yeast": MagicThing(
        id="star_yeast",
        label="star yeast",
        phrase="a spoon of star yeast",
        hiding_place="an obscure tin behind the flour jar",
        glow="tiny blue wink",
        chant="Leap and swell from shelf to shell",
        trouble="The dough puffed in bumps like a comet at night.",
        tags={"magic", "yeast"},
    ),
}

TARGETS = {
    "mixing_bowl": Target(
        id="mixing_bowl",
        label="mixing bowl",
        phrase="the mixing bowl",
        vessel_image="the bowl's blue rim",
        rise_word="bloomed",
        spread=2,
        dough_vessel=True,
        tags={"bowl"},
    ),
    "baking_tray": Target(
        id="baking_tray",
        label="baking tray",
        phrase="the baking tray",
        vessel_image="the tray's thin edge",
        rise_word="skittered",
        spread=3,
        dough_vessel=True,
        tags={"tray"},
    ),
    "tea_plate": Target(
        id="tea_plate",
        label="tea plate",
        phrase="the tea plate",
        vessel_image="the plate's round lip",
        rise_word="quivered",
        spread=1,
        dough_vessel=True,
        tags={"plate"},
    ),
    "towel": Target(
        id="towel",
        label="kitchen towel",
        phrase="the kitchen towel",
        vessel_image="the towel's hem",
        rise_word="did nothing",
        spread=0,
        dough_vessel=False,
        tags={"towel"},
    ),
}

FIXES = {
    "counter_charm": Fix(
        id="counter_charm",
        label="counter-charm",
        sense=3,
        power=3,
        works_on={"moon_dust", "whisper_spice", "star_yeast"},
        success_text="spoke a plain counter-charm and tucked the {target} under a clean cloth",
        fail_text="spoke a counter-charm, but the old spell had grown too wild to settle",
        qa_text="used a counter-charm and a clean cloth to settle the dough",
        tags={"counter_charm", "magic"},
    ),
    "cold_butter": Fix(
        id="cold_butter",
        label="cold butter trick",
        sense=2,
        power=2,
        works_on={"moon_dust", "star_yeast"},
        success_text="dropped in a curl of cold butter and stirred the {target} in a steady circle",
        fail_text="tried the cold butter trick, but the dough kept bouncing higher",
        qa_text="used cold butter and steady stirring to calm the dough",
        tags={"butter", "baking"},
    ),
    "wooden_lid": Fix(
        id="wooden_lid",
        label="wooden lid",
        sense=2,
        power=1,
        works_on={"whisper_spice"},
        success_text="set a wooden lid over the {target} and hummed the noise right down",
        fail_text="set a wooden lid over the {target}, but the dough pushed it up again",
        qa_text="covered the dough with a wooden lid and calmed it down",
        tags={"lid", "baking"},
    ),
    "clap_at_it": Fix(
        id="clap_at_it",
        label="clapping at it",
        sense=1,
        power=1,
        works_on={"moon_dust", "whisper_spice", "star_yeast"},
        success_text="clapped at the {target} until the magic stopped",
        fail_text="clapped at the {target}, which only made the bouncing worse",
        qa_text="clapped at the dough",
        tags={"bad_fix"},
    ),
}


@dataclass
class StoryParams:
    mood: str
    magic: str
    target: str
    fix: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    delay: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Lila", "Mina", "Poppy", "Nora", "Elsie", "Tess", "Mabel", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Benji", "Milo", "Jasper", "Finn", "Toby", "Ned"]
ELDER_NAMES = {
    "mother": ["Mama", "Mum", "Mother"],
    "father": ["Papa", "Dad", "Father"],
}

KNOWLEDGE = {
    "magic": [
        (
            "Why should children be careful with magic they do not understand?",
            "If a spell or powder is obscure, you do not know what it will do next. Asking a grown-up first helps keep surprises safe instead of messy."
        )
    ],
    "scone": [
        (
            "What is a scone?",
            "A scone is a small baked bread, often soft inside and a little crumbly outside. People often eat it warm with butter or jam."
        )
    ],
    "baking": [
        (
            "Why does baking go best when you measure carefully?",
            "Careful measuring helps dough behave the way you expect. Small changes can make a bake too flat, too hard, or too wild."
        )
    ],
    "counter_charm": [
        (
            "What is a counter-charm?",
            "A counter-charm is a magic spell used to stop or undo another spell. In stories, it is the calm answer to troublesome magic."
        )
    ],
    "butter": [
        (
            "Why might cold butter help pastry or scone dough?",
            "Cold butter helps dough stay tender and flaky because the little cold bits melt slowly as it bakes. Bakers often keep butter cool for that reason."
        )
    ],
    "lid": [
        (
            "What does putting a lid on something do?",
            "A lid helps keep what is inside from splashing or jumping out. It can also quiet things down and hold in a mess."
        )
    ],
    "jam": [
        (
            "Why is jam a nice surprise inside a baked treat?",
            "Jam is sweet and soft, so finding it inside can feel like a happy little treasure. It changes the middle of the bite in a fun way."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "scone", "baking", "counter_charm", "butter", "lid", "jam"]


def pair_name(ent: Entity) -> str:
    return ent.label or ent.id


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    magic = f["magic"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short rhyming story for a 3-to-5-year-old that includes the words "scone" and "obscure".',
            f"Tell a gentle cautionary magic poem where {pair_name(child)} finds {magic.label} on an obscure shelf, listens to {pair_name(elder)}, and chooses the safe way to bake a scone.",
            "Write a rhyming story with magic, a warning, and a happy surprise that comes from patience instead of a secret shortcut.",
        ]
    if outcome == "contained":
        return [
            'Write a cautionary rhyming story for a young child that includes the words "scone" and "obscure" and uses a magical kitchen surprise.',
            f"Tell a story in rhyme where {pair_name(child)} uses obscure {magic.label}, the dough goes wild, and {pair_name(elder)} calmly fixes the problem before tea time.",
            "Write a magical baking poem with a warning, a mess, and a safe, cozy ending with a surprise inside the scone.",
        ]
    return [
        'Write a rhyming cautionary tale for a 3-to-5-year-old that includes the words "scone" and "obscure".',
        f"Tell a kitchen magic story where {pair_name(child)} ignores a warning about {magic.label}, and the surprise becomes a bigger floury mess than expected.",
        "Write a magic poem where an unsafe shortcut turns into trouble, and the child learns to ask before using strange old things.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    magic = f["magic"]
    target = f["target_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    child_name = pair_name(child)
    elder_name = pair_name(elder)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who wanted to bake a scone, and {elder_name}, who tried to help keep the baking safe."
        ),
        (
            "What obscure thing did the child find?",
            f"{child_name} found {magic.phrase} hidden on {magic.hiding_place}. It looked mysterious and promising, which made it tempting."
        ),
        (
            f"Why did {elder_name} warn {child_name} not to use it?",
            f"{elder_name} warned that the magic was obscure, which meant they did not really know how it would behave. In this story, the warning matters because the magic could wake the dough and make a messy surprise."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {child_name} do after the warning?",
                f"{child_name} put the old tin back and chose the plain baking way instead. That choice stopped the trouble before any magical mess could begin."
            )
        )
        qa.append(
            (
                "What was the surprise at the end?",
                "The surprise was gentle and happy: the finished scone turned out warm and lovely because it was made with care. The story shows that safe patience can still bring a wonderful surprise."
            )
        )
    elif outcome == "contained":
        body = fix.qa_text.replace("{target}", target.label)
        qa.append(
            (
                "What happened when the magic touched the dough?",
                f"The dough became lively and started bouncing out of the {target.label}. It turned a simple scone into a magical mess because the child used a shortcut they did not understand."
            )
        )
        qa.append(
            (
                f"How did {elder_name} solve the problem?",
                f"{elder_name} {body}. That calm fix worked before the trouble grew too big, so the baking could begin again safely."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child_name} learned not to trust obscure shortcuts just because they sparkle or promise speed. The child saw that asking first and baking carefully leads to a safer kind of surprise."
            )
        )
    else:
        qa.append(
            (
                "Did the first fix work?",
                f"No. {elder_name} tried to help, but the trouble kept growing and the dough bounced around the kitchen. The mess became bigger because the magic had too much time to spread."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The child ended safe but sorry in a very floury kitchen. After that, {child_name} understood that strange magic is not a toy or a shortcut."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"magic", "scone", "baking", "jam"}
    fix = f.get("fix")
    if isinstance(fix, Fix):
        tags |= set(fix.tags)
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_fixes():
        return combos
    for mood_id in MOODS:
        for magic_id, magic in MAGIC.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(magic, target):
                    combos.append((mood_id, magic_id, target_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.delay < 0:
        return "averted"
    fix = FIXES[params.fix]
    magic = MAGIC[params.magic]
    target = TARGETS[params.target]
    return "contained" if can_fix(fix, magic, target, params.delay) else "spilled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(M, T) :- animates_dough(M), dough_vessel(T).
sensible_fix(F) :- fix(F), sense(F, S), sense_min(Min), S >= Min.
valid(Mood, M, T) :- mood(Mood), magic(M), target(T), hazard(M, T).

% --- outcome inference -----------------------------------------------------
averted :- delay(D), D < 0.

severity(Sp + D) :- chosen_target(T), spread(T, Sp), delay(D), D >= 0.
works_now :- chosen_fix(F), chosen_magic(M), works_on(F, M).
contained :- not averted, works_now, chosen_fix(F), power(F, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in sorted(MOODS):
        lines.append(asp.fact("mood", mid))
    for mid, magic in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        if magic.animates_dough:
            lines.append(asp.fact("animates_dough", mid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if target.dough_vessel:
            lines.append(asp.fact("dough_vessel", tid))
        lines.append(asp.fact("spread", tid, target.spread))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
        for mid in sorted(fix.works_on):
            lines.append(asp.fact("works_on", fid, mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_magic", params.magic),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
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

    clingo_fixes, python_fixes = set(asp_sensible_fixes()), {f.id for f in sensible_fixes()}
    if clingo_fixes == python_fixes:
        print(f"OK: sensible fixes match ({sorted(clingo_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fixes)} python={sorted(python_fixes)}")

    cases = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(
        mood="teatime",
        magic="moon_dust",
        target="mixing_bowl",
        fix="counter_charm",
        child_name="Lila",
        child_gender="girl",
        elder_name="Mama",
        elder_type="mother",
        delay=0,
    ),
    StoryParams(
        mood="rainy",
        magic="whisper_spice",
        target="tea_plate",
        fix="wooden_lid",
        child_name="Owen",
        child_gender="boy",
        elder_name="Dad",
        elder_type="father",
        delay=0,
    ),
    StoryParams(
        mood="sunny",
        magic="star_yeast",
        target="baking_tray",
        fix="cold_butter",
        child_name="Mina",
        child_gender="girl",
        elder_name="Mum",
        elder_type="mother",
        delay=1,
    ),
    StoryParams(
        mood="teatime",
        magic="moon_dust",
        target="mixing_bowl",
        fix="counter_charm",
        child_name="Theo",
        child_gender="boy",
        elder_name="Papa",
        elder_type="father",
        delay=-1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a child, an obscure magic shortcut, a scone, and a safer surprise."
    )
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[-1, 0, 1, 2], help="how long the magic trouble runs before help settles it; -1 means the child backs down")
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
    if args.target and not TARGETS[args.target].dough_vessel:
        magic = MAGIC[args.magic] if args.magic else next(iter(MAGIC.values()))
        raise StoryError(explain_rejection(magic, TARGETS[args.target]))
    if args.magic and args.target:
        magic = MAGIC[args.magic]
        target = TARGETS[args.target]
        if not hazard_at_risk(magic, target):
            raise StoryError(explain_rejection(magic, target))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c
        for c in valid_combos()
        if (args.mood is None or c[0] == args.mood)
        and (args.magic is None or c[1] == args.magic)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mood, magic, target = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["mother", "father"])
    elder_name = rng.choice(ELDER_NAMES[elder_type])
    delay = args.delay if args.delay is not None else rng.choice([-1, 0, 0, 1, 2])

    return StoryParams(
        mood=mood,
        magic=magic,
        target=target,
        fix=fix,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if params.magic not in MAGIC:
        raise StoryError(f"(Unknown magic: {params.magic})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.elder_type not in {"mother", "father"}:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")

    magic = MAGIC[params.magic]
    target = TARGETS[params.target]
    fix = FIXES[params.fix]
    if not hazard_at_risk(magic, target):
        raise StoryError(explain_rejection(magic, target))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        mood=MOODS[params.mood],
        magic=magic,
        target=target,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mood, magic, target) combos:\n")
        for mood, magic, target in combos:
            print(f"  {mood:8} {magic:13} {target}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.magic} in {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
