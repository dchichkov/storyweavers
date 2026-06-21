#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flour_paint_shorts_reconciliation_twist_rhyme_heartwarming.py
=========================================================================================

A small story world about two children making a loving surprise with flour and
paint, a favorite pair of shorts getting messy, a mistaken blame, a twist that
shows one child was actually helping, and a warm reconciliation sealed with a
little rhyme.

The world model tracks simple physical meters (flour, paint, dirty, saved) and
emotional memes (joy, hurt, guilt, relief, love). The prose is driven from that
state: a cause disturbs the work, the shorts get messy, feelings get hurt, the
children discover the heart-shaped shield that proves helpful intent, and they
make up while finishing their surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/flour_paint_shorts_reconciliation_twist_rhyme_heartwarming.py
    python storyworlds/worlds/gpt-5.4/flour_paint_shorts_reconciliation_twist_rhyme_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/flour_paint_shorts_reconciliation_twist_rhyme_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4/flour_paint_shorts_reconciliation_twist_rhyme_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root even though this file lives under storyworlds/worlds/gpt-5.4/.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandma": "grandma",
            "grandpa": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    indoor: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Occasion:
    id: str
    guest_type: str
    guest_label: str
    banner: str
    treat: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    text: str
    severity: int
    needs_indoor: bool = False
    needs_outdoor: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    text: str
    patch_text: str
    power: int
    needs_sink: bool = False
    needs_hose: bool = False
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dirty(world: World) -> list[str]:
    shorts = world.entities.get("shorts")
    if shorts is None:
        return []
    if shorts.meters["dirty"] >= THRESHOLD:
        return []
    if shorts.meters["flour"] >= THRESHOLD or shorts.meters["paint"] >= THRESHOLD:
        shorts.meters["dirty"] += 1
        return ["The little shorts no longer looked fresh and tidy."]
    return []


def _r_hurt(world: World) -> list[str]:
    wearer = world.entities.get("wearer")
    helper = world.entities.get("helper")
    if wearer is None or helper is None:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    if wearer.memes["accuse"] >= THRESHOLD:
        world.fired.add(sig)
        wearer.memes["hurt"] += 1
        helper.memes["hurt"] += 1
        return ["__hurt__"]
    return []


def _r_relief(world: World) -> list[str]:
    wearer = world.entities.get("wearer")
    helper = world.entities.get("helper")
    shorts = world.entities.get("shorts")
    if wearer is None or helper is None or shorts is None:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    if world.facts.get("truth_seen") and shorts.meters["cleaned"] >= THRESHOLD:
        world.fired.add(sig)
        wearer.memes["relief"] += 1
        helper.memes["relief"] += 1
        wearer.memes["love"] += 1
        helper.memes["love"] += 1
        return ["__relief__"]
    return []


CAUSAL_RULES = [
    Rule(name="dirty", tag="physical", apply=_r_dirty),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="relief", tag="social", apply=_r_relief),
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


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the sunny kitchen", indoor=True, tags={"sink"}),
    "porch": Setting(id="porch", place="the front porch", indoor=False, tags={"sink"}),
    "backyard": Setting(id="backyard", place="the backyard table", indoor=False, tags={"hose"}),
}

OCCASIONS = {
    "grandma_visit": Occasion(
        id="grandma_visit",
        guest_type="grandma",
        guest_label="Grandma",
        banner="WELCOME, GRANDMA",
        treat="small moon cookies",
        rhyme="Hearts so bright, home feels right!",
        tags={"family", "visit"},
    ),
    "dad_return": Occasion(
        id="dad_return",
        guest_type="father",
        guest_label="Dad",
        banner="WELCOME HOME, DAD",
        treat="tiny star cakes",
        rhyme="Home today, hooray, hooray!",
        tags={"family", "home"},
    ),
    "aunt_visit": Occasion(
        id="aunt_visit",
        guest_type="aunt",
        guest_label="Aunt Bea",
        banner="HELLO, AUNT BEA",
        treat="little honey buns",
        rhyme="Hug and grin, welcome in!",
        tags={"family", "visit"},
    ),
}

CAUSES = {
    "elbow_bump": Cause(
        id="elbow_bump",
        label="an elbow bump",
        text="their elbows bumped at the same time, wobbling the flour bowl and the little paint jar",
        severity=2,
        tags={"bump"},
    ),
    "kitten_tail": Cause(
        id="kitten_tail",
        label="a kitten tail",
        text="a curious kitten flicked its tail across the table, nudging the flour bowl and the paint jar together",
        severity=2,
        needs_indoor=True,
        tags={"pet"},
    ),
    "breeze_swirl": Cause(
        id="breeze_swirl",
        label="a breeze swirl",
        text="a playful breeze curled under the paper, tipping the flour bowl and nudging the paint jar toward the edge",
        severity=1,
        needs_outdoor=True,
        tags={"wind"},
    ),
}

REPAIRS = {
    "sink_rinse": Repair(
        id="sink_rinse",
        label="the sink rinse",
        text="hurried to the sink and rinsed the shorts with cool water and a dab of soap",
        patch_text="rinsed the shorts at the sink, but one soft speck of color stayed behind",
        power=2,
        needs_sink=True,
        tags={"soap", "sink"},
    ),
    "washcloth": Repair(
        id="washcloth",
        label="a soapy washcloth",
        text="worked together with a warm, soapy washcloth until the flour and paint slipped away",
        patch_text="rubbed with a warm washcloth, but a tiny blush of color still clung near the hem",
        power=1,
        tags={"soap"},
    ),
    "garden_hose": Repair(
        id="garden_hose",
        label="the garden hose",
        text="rinsed the shorts under the garden hose and laughed as the flour melted away and the paint thinned out",
        patch_text="rinsed the shorts with the garden hose, but one pale dot of paint still stayed",
        power=2,
        needs_hose=True,
        tags={"hose", "water"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Rose"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Sam", "Leo", "Finn"]
TRAITS = ["gentle", "eager", "careful", "cheerful", "busy", "thoughtful"]


def cause_allowed(setting: Setting, cause: Cause) -> bool:
    if cause.needs_indoor and not setting.indoor:
        return False
    if cause.needs_outdoor and setting.indoor:
        return False
    return True


def repair_allowed(setting: Setting, repair: Repair) -> bool:
    if repair.needs_sink and "sink" not in setting.tags:
        return False
    if repair.needs_hose and "hose" not in setting.tags:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for occasion_id in OCCASIONS:
            for cause_id, cause in CAUSES.items():
                if not cause_allowed(setting, cause):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_allowed(setting, repair):
                        combos.append((setting_id, occasion_id, cause_id, repair_id))
    return combos


def effective_severity(cause: Cause) -> int:
    return max(0, cause.severity - 1)


def outcome_for(cause: Cause, repair: Repair) -> str:
    return "clean" if repair.power >= effective_severity(cause) else "patch"


def explain_cause_rejection(setting: Setting, cause: Cause) -> str:
    if cause.needs_indoor and not setting.indoor:
        return f"(No story: {cause.label} fits an indoor table better than {setting.place}.)"
    if cause.needs_outdoor and setting.indoor:
        return f"(No story: {cause.label} needs open air, not {setting.place}.)"
    return "(No story: that disturbance does not fit this setting.)"


def explain_repair_rejection(setting: Setting, repair: Repair) -> str:
    if repair.needs_sink and "sink" not in setting.tags:
        return f"(No story: {repair.label} needs a sink, but {setting.place} has no easy sink nearby.)"
    if repair.needs_hose and "hose" not in setting.tags:
        return f"(No story: {repair.label} needs a garden hose, but {setting.place} has no hose nearby.)"
    return "(No story: that repair method does not fit this place.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def project_intro(occasion: Occasion) -> str:
    return (
        f"They wanted to make a surprise for {occasion.guest_label}: "
        f"a bright banner that said {occasion.banner!r} and a plate of {occasion.treat}."
    )


def predict_result(setting: Setting, cause: Cause, repair: Repair) -> dict:
    return {
        "setting_ok": cause_allowed(setting, cause) and repair_allowed(setting, repair),
        "effective_severity": effective_severity(cause),
        "outcome": outcome_for(cause, repair),
    }


def introduce(world: World, wearer: Entity, helper: Entity, occasion: Occasion) -> None:
    world.say(
        f"{wearer.id} and {helper.id} were busy in {world.setting.place}, whispering over a secret plan."
    )
    world.say(project_intro(occasion))
    world.say(
        f"{wearer.id} was wearing favorite green shorts, and a small bowl of flour sat near the mixing spoon while pots of paint waited by the paper hearts."
    )
    for child in (wearer, helper):
        child.memes["joy"] += 1


def begin_work(world: World, wearer: Entity, helper: Entity, occasion: Occasion) -> None:
    world.say(
        f"{helper.id} dusted flour onto tiny dough rounds while {wearer.id} painted red loops around the banner letters."
    )
    world.say(
        f"Now and then they practiced the rhyme they wanted to say together: {occasion.rhyme!r}"
    )
    wearer.memes["pride"] += 1
    helper.memes["care"] += 1


def disturb(world: World, wearer: Entity, helper: Entity, cause: Cause) -> None:
    shorts = world.get("shorts")
    heart = world.get("heart")
    world.say(
        f"Then {cause.text}. In one surprised blink, flour puffed up white and the paint jumped blue."
    )
    helper.memes["care"] += 1
    helper.meters["shield"] += 1
    heart.meters["used"] += 1
    shorts.meters["saved"] += 1
    shorts.meters["flour"] += 1
    shorts.meters["paint"] += float(effective_severity(cause))
    propagate(world, narrate=True)
    world.say(
        f"{helper.id} snatched up a paper heart and held it in front of the shorts, trying to stop the splash."
    )
    if shorts.meters["paint"] >= THRESHOLD:
        world.say(
            f"But a blue splash still spotted the green shorts, and flour settled over everything like soft white snow."
        )
    else:
        world.say(
            f"The heart blocked most of the paint, but flour still settled over the shorts in a powdery cloud."
        )


def accuse(world: World, wearer: Entity, helper: Entity) -> None:
    wearer.memes["accuse"] += 1
    helper.memes["sad"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{wearer.id} looked down at the shorts and cried, \"Oh no! You got flour and paint on them!\""
    )
    world.say(
        f"{helper.id}'s face fell. {helper.pronoun().capitalize()} had been trying to help, but the moment felt too fast and messy to explain."
    )


def quiet_after(world: World, wearer: Entity, helper: Entity) -> None:
    if helper.memes["hurt"] >= THRESHOLD:
        world.say(
            f"For a moment, neither child touched the banner. The room felt smaller than it had a minute before."
        )


def repair_scene(world: World, wearer: Entity, helper: Entity, repair: Repair, cause: Cause) -> None:
    shorts = world.get("shorts")
    world.say(
        f"Still, {helper.id} reached for the shorts and whispered, \"Let me help.\" Together they {repair.text if outcome_for(cause, repair) == 'clean' else repair.patch_text}."
    )
    if outcome_for(cause, repair) == "clean":
        shorts.meters["paint"] = 0.0
        shorts.meters["flour"] = 0.0
        shorts.meters["dirty"] = 0.0
        shorts.meters["cleaned"] += 1
    else:
        shorts.meters["paint"] = 0.5
        shorts.meters["flour"] = 0.0
        shorts.meters["dirty"] = 0.5
        shorts.meters["cleaned"] += 1
    world.facts["truth_seen"] = True
    propagate(world, narrate=False)


def reveal(world: World, wearer: Entity, helper: Entity) -> None:
    world.say(
        f"As the flour slid away, a neat heart-shaped dry spot appeared on the cloth."
    )
    world.say(
        f"That was the twist: the little paper heart had been there because {helper.id} had thrown it up like a shield. {helper.pronoun().capitalize()} had not been spoiling the shorts at all; {helper.pronoun()} had been trying to save them."
    )
    wearer.memes["guilt"] += 1
    wearer.memes["understanding"] += 1


def reconcile(world: World, wearer: Entity, helper: Entity, occasion: Occasion, cause: Cause, repair: Repair) -> None:
    clean = outcome_for(cause, repair) == "clean"
    shorts = world.get("shorts")
    if clean:
        world.say(
            f"{wearer.id} touched the heart-shaped spot and said, \"I'm sorry. I thought you made the mess, but you were helping me.\""
        )
    else:
        world.say(
            f"{wearer.id} touched the tiny pale dot by the hem and the heart-shaped spot above it. \"I'm sorry,\" {wearer.pronoun()} said. \"I thought you made the mess, but you were helping me.\""
        )
    world.say(
        f"{helper.id} gave a small nod. \"We can finish together,\" {helper.pronoun()} said, and the hurt in the air began to melt."
    )
    wearer.memes["hurt"] = 0.0
    helper.memes["hurt"] = 0.0
    wearer.memes["love"] += 1
    helper.memes["love"] += 1
    if not clean:
        shorts.meters["patch"] += 1
        world.say(
            f"Because one faint dot of paint stayed, they added a tiny stitched heart there and decided it made the shorts look even kinder than before."
        )
    world.say(
        f"They finished the banner, set out the {occasion.treat}, and when {occasion.guest_label} arrived, the two children chimed together, {occasion.rhyme!r}"
    )
    if clean:
        world.say(
            f"The shorts were clean again, the banner shone bright, and the surprise felt extra warm because the children had made up with honest hearts."
        )
    else:
        world.say(
            f"The shorts still wore their little heart, the banner shone bright, and the surprise felt extra warm because the children had made up with honest hearts."
        )


def tell(
    setting: Setting,
    occasion: Occasion,
    cause: Cause,
    repair: Repair,
    wearer_name: str = "Milo",
    wearer_gender: str = "boy",
    helper_name: str = "Lila",
    helper_gender: str = "girl",
) -> World:
    world = World(setting)
    wearer = world.add(
        Entity(
            id=wearer_name,
            kind="character",
            type=wearer_gender,
            role="wearer",
            traits=["proud"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=["kind"],
        )
    )
    guest = world.add(
        Entity(
            id="Guest",
            kind="character",
            type=occasion.guest_type,
            role="guest",
            label=occasion.guest_label,
        )
    )
    shorts = world.add(
        Entity(
            id="shorts",
            type="shorts",
            label="shorts",
            phrase="favorite green shorts",
            tags={"shorts"},
        )
    )
    heart = world.add(
        Entity(
            id="heart",
            type="paper_heart",
            label="paper heart",
            phrase="a paper heart cut from the banner scraps",
            tags={"heart"},
        )
    )
    banner = world.add(
        Entity(
            id="banner",
            type="banner",
            label="banner",
            phrase="the surprise banner",
            tags={"paint"},
        )
    )
    bowl = world.add(
        Entity(
            id="bowl",
            type="bowl",
            label="flour bowl",
            phrase="the little flour bowl",
            tags={"flour"},
        )
    )

    introduce(world, wearer, helper, occasion)
    begin_work(world, wearer, helper, occasion)
    world.para()
    disturb(world, wearer, helper, cause)
    accuse(world, wearer, helper)
    quiet_after(world, wearer, helper)
    world.para()
    repair_scene(world, wearer, helper, repair, cause)
    reveal(world, wearer, helper)
    reconcile(world, wearer, helper, occasion, cause, repair)

    world.facts.update(
        setting=setting,
        occasion=occasion,
        cause=cause,
        repair=repair,
        wearer=wearer,
        helper=helper,
        guest=guest,
        shorts=shorts,
        heart=heart,
        outcome=outcome_for(cause, repair),
        truth_seen=True,
        rhyme=occasion.rhyme,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    occasion: str
    cause: str
    repair: str
    wearer_name: str
    wearer_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="kitchen",
        occasion="grandma_visit",
        cause="kitten_tail",
        repair="sink_rinse",
        wearer_name="Milo",
        wearer_gender="boy",
        helper_name="Lila",
        helper_gender="girl",
    ),
    StoryParams(
        setting="porch",
        occasion="dad_return",
        cause="breeze_swirl",
        repair="washcloth",
        wearer_name="Nora",
        wearer_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
    ),
    StoryParams(
        setting="backyard",
        occasion="aunt_visit",
        cause="elbow_bump",
        repair="garden_hose",
        wearer_name="Theo",
        wearer_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
    ),
    StoryParams(
        setting="porch",
        occasion="grandma_visit",
        cause="elbow_bump",
        repair="sink_rinse",
        wearer_name="Rose",
        wearer_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
    ),
]


KNOWLEDGE = {
    "flour": [
        (
            "What is flour?",
            "Flour is a soft powder made from ground grain. People use it to make dough for bread, cakes, and cookies.",
        )
    ],
    "paint": [
        (
            "What is paint?",
            "Paint is a colored liquid or paste used to make pictures and cover surfaces with color.",
        )
    ],
    "shorts": [
        (
            "What are shorts?",
            "Shorts are clothes that cover the waist and the top part of the legs, but not the whole legs like long pants do.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like bright and right. Rhymes can make songs and little sayings feel playful.",
        )
    ],
    "sorry": [
        (
            "Why does saying sorry help?",
            "Saying sorry can help because it shows you understand someone else's hurt feelings. It opens the door for people to trust each other again.",
        )
    ],
    "soap": [
        (
            "Why does soap help clean paint and flour?",
            "Soap helps loosen dirt and some sticky messes so water can carry them away. Flour also washes off more easily once it gets wet.",
        )
    ],
    "heart": [
        (
            "Why is a heart shape often used in stories?",
            "A heart shape is often used to show love, care, and kindness. It is a simple sign that someone was thinking warmly of another person.",
        )
    ],
}
KNOWLEDGE_ORDER = ["flour", "paint", "shorts", "soap", "rhyme", "sorry", "heart"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    occasion = f["occasion"]
    wearer = f["wearer"]
    helper = f["helper"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "flour," "paint," and "shorts."',
        f"Tell a warm story where {wearer.id} and {helper.id} make a surprise for {occasion.guest_label}, a mess leads to hurt feelings, and a gentle twist brings reconciliation.",
        f'Write a small story with a rhyme, a mistake in the middle, and an ending where the children make up and finish their loving surprise together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    wearer = f["wearer"]
    helper = f["helper"]
    occasion = f["occasion"]
    cause = f["cause"]
    repair = f["repair"]
    shorts = f["shorts"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {wearer.id} and {helper.id}, two children making a surprise for {occasion.guest_label}. The trouble starts when their happy work suddenly turns messy.",
        ),
        (
            f"What were {wearer.id} and {helper.id} making?",
            f"They were making a painted banner and a treat with flour for {occasion.guest_label}. They also practiced a little rhyme so the surprise would sound extra cheerful.",
        ),
        (
            f"Why did {wearer.id} get upset?",
            f"{wearer.id} saw flour and paint on the shorts and thought {helper.id} had caused the mess. The moment happened so quickly that {wearer.pronoun()} did not see {helper.id} trying to help.",
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the heart-shaped dry spot showed {helper.id} had lifted a paper heart like a shield. {helper.pronoun().capitalize()} was not ruining the shorts at all; {helper.pronoun()} was trying to save them.",
        ),
    ]
    if f["outcome"] == "clean":
        qa.append(
            (
                "How did the children fix the problem?",
                f"They {repair.text}, and the shorts came clean. Cleaning them together helped calm the hurt feelings too.",
            )
        )
    else:
        qa.append(
            (
                "How did the children fix the problem?",
                f"They {repair.patch_text}, and then they turned the last tiny dot into a little heart. That made the shorts feel special instead of spoiled.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They reconciled, finished the banner, and said the rhyme together for {occasion.guest_label}. The ending feels warm because the children understood the truth and chose kindness again.",
        )
    )
    if shorts.meters["saved"] >= THRESHOLD:
        qa.append(
            (
                f"Why is the heart shape important on the shorts?",
                f"It proves {helper.id} had tried to protect the shorts in the middle of the mess. The heart becomes a sign of care, not just a decoration.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"flour", "paint", "shorts", "rhyme", "sorry", "heart"}
    if world.facts["repair"].tags & {"soap", "sink", "hose"}:
        tags.add("soap")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
cause_ok(S, C) :- setting(S), cause(C), indoor(S), needs_indoor(C).
cause_ok(S, C) :- setting(S), cause(C), outdoor(S), needs_outdoor(C).
cause_ok(S, C) :- setting(S), cause(C), not needs_indoor(C), not needs_outdoor(C).

repair_ok(S, R) :- setting(S), repair(R), needs_sink(R), has_sink(S).
repair_ok(S, R) :- setting(S), repair(R), needs_hose(R), has_hose(S).
repair_ok(S, R) :- setting(S), repair(R), not needs_sink(R), not needs_hose(R).

valid(S, O, C, R) :- setting(S), occasion(O), cause_ok(S, C), repair_ok(S, R).

shield_bonus(1).
effective(C, E) :- severity(C, S), shield_bonus(B), E = S - B, E >= 0.
effective(C, 0) :- severity(C, S), shield_bonus(B), S - B < 0.
outcome(clean) :- chosen_cause(C), chosen_repair(R), effective(C, E), power(R, P), P >= E.
outcome(patch) :- chosen_cause(C), chosen_repair(R), effective(C, E), power(R, P), P < E.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.indoor:
            lines.append(asp.fact("indoor", setting_id))
        else:
            lines.append(asp.fact("outdoor", setting_id))
        if "sink" in setting.tags:
            lines.append(asp.fact("has_sink", setting_id))
        if "hose" in setting.tags:
            lines.append(asp.fact("has_hose", setting_id))
    for occasion_id in OCCASIONS:
        lines.append(asp.fact("occasion", occasion_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("severity", cause_id, cause.severity))
        if cause.needs_indoor:
            lines.append(asp.fact("needs_indoor", cause_id))
        if cause.needs_outdoor:
            lines.append(asp.fact("needs_outdoor", cause_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("power", repair_id, repair.power))
        if repair.needs_sink:
            lines.append(asp.fact("needs_sink", repair_id))
        if repair.needs_hose:
            lines.append(asp.fact("needs_hose", repair_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story is empty.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=False, header="smoke")
    if "flour" not in sample.story or "paint" not in sample.story or "shorts" not in sample.story:
        raise StoryError("Smoke test failed: seed words missing from ordinary story.")


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_for(CAUSES[params.cause], REPAIRS[params.repair])
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: flour, paint, shorts, a mistaken blame, and a warm reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--wearer-name")
    ap.add_argument("--wearer-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause:
        setting = SETTINGS[args.setting]
        cause = CAUSES[args.cause]
        if not cause_allowed(setting, cause):
            raise StoryError(explain_cause_rejection(setting, cause))
    if args.setting and args.repair:
        setting = SETTINGS[args.setting]
        repair = REPAIRS[args.repair]
        if not repair_allowed(setting, repair):
            raise StoryError(explain_repair_rejection(setting, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.occasion is None or combo[1] == args.occasion)
        and (args.cause is None or combo[2] == args.cause)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, occasion_id, cause_id, repair_id = rng.choice(sorted(combos))

    wearer_gender = args.wearer_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    wearer_name = args.wearer_name or _pick_name(rng, wearer_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=wearer_name)

    return StoryParams(
        setting=setting_id,
        occasion=occasion_id,
        cause=cause_id,
        repair=repair_id,
        wearer_name=wearer_name,
        wearer_gender=wearer_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(Invalid occasion: {params.occasion})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Invalid repair: {params.repair})")

    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    repair = REPAIRS[params.repair]
    if not cause_allowed(setting, cause):
        raise StoryError(explain_cause_rejection(setting, cause))
    if not repair_allowed(setting, repair):
        raise StoryError(explain_repair_rejection(setting, repair))

    world = tell(
        setting=setting,
        occasion=OCCASIONS[params.occasion],
        cause=cause,
        repair=repair,
        wearer_name=params.wearer_name,
        wearer_gender=params.wearer_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, occasion, cause, repair) combos:\n")
        for setting_id, occasion_id, cause_id, repair_id in combos:
            print(f"  {setting_id:9} {occasion_id:14} {cause_id:12} {repair_id}")
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
            header = (
                f"### {p.wearer_name} & {p.helper_name}: {p.setting}, {p.occasion}, "
                f"{p.cause}, {p.repair}, {world_outcome_label(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def world_outcome_label(params: StoryParams) -> str:
    return outcome_for(CAUSES[params.cause], REPAIRS[params.repair])




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
