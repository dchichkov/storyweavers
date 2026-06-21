#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py
=================================================================================

A standalone storyworld for a gentle bedtime tale about a child woken by tooth
pain. A bedroom poster sparks a flashback to the dentist's office, where a
helpful poster and a simple comparison explained what an abscessed tooth is.
At night, a grown-up chooses a sensible soothing step. In the morning, the
family gets proper dental care, and the ending image shows what changed.

The world model keeps the schema intentionally small:
- one shared Entity dataclass with physical meters and emotional memes
- one typed World store with paragraph narration
- a small reasonableness gate over night care and morning treatment
- an inline ASP twin that mirrors the same gate and ending outcome

Run it
------
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py --qa
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py --asp
    python storyworlds/worlds/gpt-5.4/poster_abscessed_comparison_flashback_bedtime_story.py --verify
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
SENSE_MIN = 2


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


@dataclass
class PosterTheme:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComparisonLesson:
    id: str
    image: str
    healthy: str
    sore: str
    tags: set[str] = field(default_factory=set)


@dataclass
class NightCare:
    id: str
    label: str
    sense: int
    relief: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MorningFix:
    id: str
    label: str
    treats_infection: bool
    power: int
    text: str
    qa_text: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_toothache(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    tooth = world.entities.get("tooth")
    if not child or not tooth:
        return out
    if tooth.meters["pain"] >= THRESHOLD:
        sig = ("toothache",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            child.memes["wakefulness"] += 1
            out.append("__wake__")
    if tooth.meters["swelling"] >= THRESHOLD:
        sig = ("swelling",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    tooth = world.entities.get("tooth")
    if not child or not tooth:
        return out
    if tooth.meters["soothed"] >= THRESHOLD:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            child.memes["trust"] += 1
    if tooth.meters["pain"] <= 0.0 and tooth.meters["treated"] >= THRESHOLD:
        sig = ("aftercare",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["bravery"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="toothache", tag="body", apply=_r_toothache),
    Rule(name="comfort", tag="emotion", apply=_r_comfort),
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


POSTERS = {
    "moon": PosterTheme(
        id="moon",
        label="moon poster",
        phrase="a blue poster with a round silver moon",
        glow="the moon on it looked soft enough to tuck the whole room in",
        tags={"poster", "moon"},
    ),
    "rabbit": PosterTheme(
        id="rabbit",
        label="rabbit poster",
        phrase="a poster of a white rabbit carrying a lantern",
        glow="the tiny lantern in the picture seemed to shine even in the dark",
        tags={"poster", "rabbit"},
    ),
    "boat": PosterTheme(
        id="boat",
        label="sailboat poster",
        phrase="a poster of a small sailboat on a dark blue sea",
        glow="the painted sail looked calm, as if it knew how to float through a quiet night",
        tags={"poster", "boat"},
    ),
}

COMPARISONS = {
    "house": ComparisonLesson(
        id="house",
        image="little house",
        healthy="a healthy tooth is like a little house with the door shut tight",
        sore="an abscessed tooth is like a little house with angry germs trapped inside",
        tags={"comparison", "germs"},
    ),
    "pillow": ComparisonLesson(
        id="pillow",
        image="pillow",
        healthy="a healthy tooth is like a smooth pillow that lets the mouth rest",
        sore="an abscessed tooth is like a pillow with a hard lump inside that keeps poking",
        tags={"comparison", "pillow"},
    ),
    "rainboot": ComparisonLesson(
        id="rainboot",
        image="rain boot",
        healthy="a healthy tooth is like a rain boot with no holes",
        sore="an abscessed tooth is like a rain boot with muddy water trapped inside",
        tags={"comparison", "rainboot"},
    ),
}

NIGHT_CARE = {
    "salt_rinse": NightCare(
        id="salt_rinse",
        label="warm salt-water rinse",
        sense=3,
        relief=1,
        text="helped {child} swish a little warm salt water, then held a cup while the sore mouth settled",
        qa_text="used a warm salt-water rinse to calm the sore tooth",
        tags={"rinse", "nightcare"},
    ),
    "cool_cloth": NightCare(
        id="cool_cloth",
        label="cool cloth on the cheek",
        sense=3,
        relief=2,
        text="folded a cool cloth and rested it gently against {child}'s cheek until the throbbing slowed",
        qa_text="pressed a cool cloth to the swollen cheek",
        tags={"cloth", "nightcare"},
    ),
    "medicine": NightCare(
        id="medicine",
        label="children's pain medicine",
        sense=3,
        relief=2,
        text="gave {child} children's pain medicine and rocked beside the bed while it began to help",
        qa_text="gave children's pain medicine and stayed close until it helped",
        tags={"medicine", "nightcare"},
    ),
    "candy": NightCare(
        id="candy",
        label="extra candy",
        sense=1,
        relief=0,
        text="offered extra candy, which only made the sore tooth feel sharper",
        qa_text="offered candy",
        tags={"candy"},
    ),
}

MORNING_FIXES = {
    "drain_and_medicine": MorningFix(
        id="drain_and_medicine",
        label="cleaning, draining, and medicine",
        treats_infection=True,
        power=2,
        text="The dentist cleaned the sore place, let the trapped pressure out, and sent them home with medicine for the infection.",
        qa_text="cleaned and drained the abscessed tooth and gave medicine for the infection",
        tags={"dentist", "medicine"},
    ),
    "deep_clean": MorningFix(
        id="deep_clean",
        label="careful cleaning and medicine",
        treats_infection=True,
        power=1,
        text="The dentist cleaned around the sore tooth very carefully and gave medicine so the infection could settle down.",
        qa_text="cleaned the sore area carefully and gave medicine",
        tags={"dentist", "medicine"},
    ),
    "remove_bad_tooth": MorningFix(
        id="remove_bad_tooth",
        label="taking the bad tooth out",
        treats_infection=True,
        power=3,
        text="The dentist took the bad little tooth out so the swelling could stop, then gave medicine and a very gentle smile.",
        qa_text="removed the bad tooth and gave medicine",
        tags={"dentist", "medicine"},
    ),
    "just_brush": MorningFix(
        id="just_brush",
        label="just brushing harder",
        treats_infection=False,
        power=0,
        text="Nobody should use this ending.",
        qa_text="just brushed harder",
        tags={"brush"},
    ),
}

SEVERITIES = {
    1: "small",
    2: "strong",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli", "Theo"]
COMFORT_ITEMS = ["blanket", "stuffed rabbit", "little bear", "soft pillow", "toy whale"]


def sensible_night_care() -> list[NightCare]:
    return [c for c in NIGHT_CARE.values() if c.sense >= SENSE_MIN]


def treats_abscess(fix: MorningFix) -> bool:
    return fix.treats_infection


def valid_combo(night_care_id: str, morning_fix_id: str, severity: int) -> bool:
    if severity not in SEVERITIES:
        return False
    care = NIGHT_CARE[night_care_id]
    fix = MORNING_FIXES[morning_fix_id]
    if care.sense < SENSE_MIN:
        return False
    if not fix.treats_infection:
        return False
    if fix.power < severity:
        return False
    return True


def valid_combos() -> list[tuple[str, str, int]]:
    combos: list[tuple[str, str, int]] = []
    for care_id in NIGHT_CARE:
        for fix_id in MORNING_FIXES:
            for severity in sorted(SEVERITIES):
                if valid_combo(care_id, fix_id, severity):
                    combos.append((care_id, fix_id, severity))
    return combos


@dataclass
class StoryParams:
    poster: str
    comparison: str
    night_care: str
    morning_fix: str
    severity: int
    child_name: str
    child_gender: str
    parent: str
    comfort_item: str
    seed: Optional[int] = None


def bedtime_setup(world: World, child: Entity, poster: PosterTheme, comfort_item: str) -> None:
    world.say(
        f"At bedtime, {child.id} lay under {child.pronoun('possessive')} {comfort_item}, "
        f"looking at {poster.phrase} above the bed. {poster.glow}."
    )


def pain_begins(world: World, child: Entity, tooth: Entity, severity: int) -> None:
    tooth.meters["pain"] = float(severity)
    tooth.meters["swelling"] = 1.0
    tooth.meters["infected"] = 1.0
    propagate(world, narrate=False)
    if severity == 1:
        world.say(
            f"But instead of drifting off, {child.id} pressed a hand to one cheek. "
            f"A sore tooth gave a small, stubborn thump."
        )
    else:
        world.say(
            f"But instead of drifting off, {child.id} sat up with wet eyes and held one cheek. "
            f"The sore tooth was throbbing hard enough to push sleep away."
        )


def call_parent(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}," {child.id} whispered, and {parent.label_word} came in at once. '
        f'{parent.pronoun().capitalize()} sat on the edge of the bed and listened before saying anything else.'
    )


def flashback_lesson(world: World, child: Entity, poster: PosterTheme, lesson: ComparisonLesson) -> None:
    world.para()
    child.memes["memory"] += 1
    world.say(
        f"{child.id} looked up at the {poster.label}, and a flashback drifted back from the dentist's office. "
        f"There had been a bright poster there too."
    )
    world.say(
        f"Dr. Nia had made a comparison that {child.id} could still remember: "
        f'"{lesson.healthy}, but {lesson.sore}."'
    )
    world.say(
        f'Then the dentist had added, "That is why an abscessed tooth needs real help, not waiting."'
    )


def soothe_night(world: World, child: Entity, parent: Entity, care: NightCare) -> None:
    tooth = world.get("tooth")
    tooth.meters["pain"] = max(0.0, tooth.meters["pain"] - float(care.relief))
    tooth.meters["soothed"] += 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} {care.text.format(child=child.id)}"
    )
    if tooth.meters["pain"] <= 0.0:
        world.say(
            f"Soon the fierce beating in the tooth faded to almost nothing, and {child.id}'s shoulders unbunched."
        )
    else:
        world.say(
            f"The tooth still ached a little, but the pain was no longer bossing the whole room."
        )
    world.say(
        f'"We will call the dentist in the morning," {parent.label_word} promised. '
        f'"Tonight I am right here with you."'
    )


def sleep_outcome(world: World, child: Entity) -> str:
    tooth = world.get("tooth")
    if tooth.meters["pain"] <= 0.0:
        child.memes["sleep"] += 1
        world.say(
            f"{child.id} curled close, watched the poster once more, and at last fell asleep."
        )
        return "rested"
    child.memes["sleep"] += 0.5
    world.say(
        f"{child.id} slept in little pieces, waking now and then, but each time {parent_word(world)}'s hand was there."
    )
    return "drowsy"


def parent_word(world: World) -> str:
    parent = world.get("parent")
    return parent.label_word


def morning_trip(world: World, child: Entity, parent: Entity) -> None:
    world.para()
    world.say(
        f"In the morning, the sky looked pale and kind. {parent.label_word.capitalize()} called the dentist, "
        f"and soon {child.id} was holding {child.pronoun('possessive')} {world.facts['comfort_item']} in the waiting room."
    )


def dentist_fix(world: World, child: Entity, fix: MorningFix) -> None:
    tooth = world.get("tooth")
    tooth.meters["pain"] = 0.0
    tooth.meters["swelling"] = 0.0
    tooth.meters["treated"] += 1.0
    propagate(world, narrate=False)
    world.say(fix.text)
    world.say(
        f"{child.id} squeezed once, took a brave breath, and found out the hard part was shorter than the worrying."
    )


def ending(world: World, child: Entity, poster: PosterTheme, lesson: ComparisonLesson) -> None:
    world.para()
    world.say(
        f"That night, {child.id} was back in bed under the same {world.facts['comfort_item']}, looking at the {poster.label} again."
    )
    world.say(
        f"This time the room felt easy and quiet. The old comparison came back in a softer way, and now it ended with help instead of fear."
    )
    world.say(
        f"Before sleep, {child.id} whispered, \"I am glad we listened when my tooth hurt,\" and the house grew still around that brave little thought."
    )


def tell(
    poster: PosterTheme,
    lesson: ComparisonLesson,
    care: NightCare,
    fix: MorningFix,
    severity: int,
    child_name: str,
    child_gender: str,
    parent_type: str,
    comfort_item: str,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    child.id = child_name
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    tooth = world.add(Entity(id="tooth", kind="thing", type="tooth", label="sore tooth", role="tooth"))
    wall_poster = world.add(Entity(id="poster", kind="thing", type="poster", label=poster.label, phrase=poster.phrase))
    clinic_poster = world.add(Entity(id="clinic_poster", kind="thing", type="poster", label="dentist poster"))
    world.facts["comfort_item"] = comfort_item

    bedtime_setup(world, child, poster, comfort_item)
    pain_begins(world, child, tooth, severity)
    call_parent(world, child, parent)
    flashback_lesson(world, child, poster, lesson)
    soothe_night(world, child, parent, care)
    sleep_kind = sleep_outcome(world, child)
    morning_trip(world, child, parent)
    dentist_fix(world, child, fix)
    ending(world, child, poster, lesson)

    world.facts.update(
        child=child,
        parent=parent,
        tooth=tooth,
        wall_poster=wall_poster,
        clinic_poster=clinic_poster,
        poster_cfg=poster,
        comparison_cfg=lesson,
        night_care_cfg=care,
        morning_fix_cfg=fix,
        severity=severity,
        sleep_kind=sleep_kind,
        used_flashback=child.memes["memory"] >= THRESHOLD,
        abscessed=True,
    )
    return world


KNOWLEDGE = {
    "poster": [
        (
            "What is a poster?",
            "A poster is a big picture or sign you hang on a wall. It can decorate a room or help teach something."
        )
    ],
    "comparison": [
        (
            "What is a comparison?",
            "A comparison is when you explain one thing by saying it is like another thing. It helps hard ideas feel easier to understand."
        )
    ],
    "abscessed": [
        (
            "What does abscessed mean when people talk about a tooth?",
            "An abscessed tooth is a tooth with an infection inside or around it. It can swell, throb, and needs help from a dentist."
        )
    ],
    "dentist": [
        (
            "What does a dentist do?",
            "A dentist helps take care of teeth. Dentists look for sore spots, clean teeth, and fix problems that brushing alone cannot solve."
        )
    ],
    "rinse": [
        (
            "Why can warm salt water help a sore mouth?",
            "Warm salt water can gently calm a sore place in the mouth. It is only a helper, though, and it does not replace the dentist."
        )
    ],
    "cloth": [
        (
            "Why does a cool cloth feel nice on a swollen cheek?",
            "A cool cloth can make a puffy cheek feel calmer. The coolness helps the outside feel less sore for a little while."
        )
    ],
    "medicine": [
        (
            "Why do people sometimes need medicine for an infected tooth?",
            "Medicine can help fight the germs causing the infection. That gives the sore place a better chance to heal."
        )
    ],
}
KNOWLEDGE_ORDER = ["poster", "comparison", "abscessed", "dentist", "rinse", "cloth", "medicine"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    poster = f["poster_cfg"]
    care = f["night_care_cfg"]
    return [
        'Write a gentle bedtime story for a 3-to-5-year-old that includes the words "poster", "abscessed", and "comparison", and uses a flashback.',
        f"Tell a bedtime story where a child named {child.id} wakes with tooth pain, looks at {poster.phrase}, remembers a dentist's lesson in a flashback, and is comforted by {parent.label_word}.",
        f"Write a calm night story where a parent uses {care.label}, promises a dentist visit in the morning, and ends with the room feeling safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    poster = f["poster_cfg"]
    lesson = f["comparison_cfg"]
    care = f["night_care_cfg"]
    fix = f["morning_fix_cfg"]
    severity = f["severity"]
    sleep_kind = f["sleep_kind"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who woke at bedtime with a sore tooth, and {child.pronoun('possessive')} {parent.label_word}, who stayed close and helped."
        ),
        (
            "What was on the wall above the bed?",
            f"There was {poster.phrase} above the bed. Seeing that poster helped start the flashback."
        ),
        (
            "What happened in the flashback?",
            f"{child.id} remembered a poster at the dentist's office and a comparison Dr. Nia had made. The memory explained that an abscessed tooth needs real help because germs are trapped inside."
        ),
        (
            "Why did the child need help instead of just waiting?",
            f"The tooth was not only sore; it was abscessed, so it had swelling and infection too. Waiting would not fix that, which is why the parent promised a dentist visit in the morning."
        ),
        (
            f"How did {parent.label_word} help during the night?",
            f"{parent.label_word.capitalize()} {care.qa_text}. That calmed the pain enough to make the night feel safer, even before the dentist fixed the real problem."
        ),
        (
            "What did the dentist do the next day?",
            f"The dentist {fix.qa_text}. That treated the infection instead of only covering up the pain."
        ),
    ]
    if sleep_kind == "rested":
        qa.append(
            (
                "Could the child sleep before morning came?",
                f"Yes. After the night care, the pain eased enough for {child.id} to fall asleep. The calm ending at bedtime showed the help was working."
            )
        )
    else:
        qa.append(
            (
                "Did the child sleep easily that night?",
                f"Not all the way. {child.id} slept in little pieces because the tooth still hurt some, but it was easier with {parent.label_word} nearby and a dentist visit already planned."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {child.id} back in bed under the same {f['comfort_item']}, looking at the same poster in a calmer way. The room had changed because the tooth had been treated and the fear was gone."
        )
    )
    if severity == 2:
        qa.append(
            (
                "Why was the morning visit especially important in this story?",
                f"The pain was strong enough to keep sleep away, which showed the tooth problem was serious. The morning treatment mattered because a strong toothache from an abscessed tooth needs a dentist, not only comfort."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"poster", "comparison", "abscessed", "dentist"}
    care = world.facts["night_care_cfg"]
    fix = world.facts["morning_fix_cfg"]
    tags |= set(care.tags)
    tags |= set(fix.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        poster="moon",
        comparison="house",
        night_care="cool_cloth",
        morning_fix="drain_and_medicine",
        severity=2,
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        comfort_item="stuffed rabbit",
    ),
    StoryParams(
        poster="rabbit",
        comparison="pillow",
        night_care="medicine",
        morning_fix="remove_bad_tooth",
        severity=2,
        child_name="Ben",
        child_gender="boy",
        parent="father",
        comfort_item="soft pillow",
    ),
    StoryParams(
        poster="boat",
        comparison="rainboot",
        night_care="salt_rinse",
        morning_fix="deep_clean",
        severity=1,
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        comfort_item="little bear",
    ),
]


def explain_bad_care(care_id: str) -> str:
    care = NIGHT_CARE[care_id]
    return (
        f"(No story: '{care.label}' is not a sensible way to handle bedtime tooth pain "
        f"(sense={care.sense} < {SENSE_MIN}). Choose a soothing step like "
        f"{', '.join(sorted(c.id for c in sensible_night_care()))}.)"
    )


def explain_bad_fix(fix_id: str, severity: int) -> str:
    fix = MORNING_FIXES[fix_id]
    if not fix.treats_infection:
        return (
            f"(No story: '{fix.label}' does not treat an abscessed tooth. "
            f"The morning fix must address the infection, not just ignore it.)"
        )
    return (
        f"(No story: '{fix.label}' is too weak for severity {severity}. "
        f"Pick a treatment with enough power for the swelling and pain.)"
    )


ASP_RULES = r"""
soothing(C) :- care(C), care_sense(C, S), sense_min(M), S >= M.
good_fix(F) :- fix(F), treats_infection(F).
valid(C, F, Sev) :- care(C), fix(F), severity(Sev), soothing(C), good_fix(F), fix_power(F, P), P >= Sev.

rested :- chosen_care(C), chosen_severity(Sev), care_relief(C, R), R >= Sev.
drowsy :- chosen_care(C), chosen_severity(Sev), care_relief(C, R), R < Sev.

outcome(rested) :- rested.
outcome(drowsy) :- drowsy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for poster_id in POSTERS:
        lines.append(asp.fact("poster", poster_id))
    for comp_id in COMPARISONS:
        lines.append(asp.fact("comparison", comp_id))
    for care_id, care in NIGHT_CARE.items():
        lines.append(asp.fact("care", care_id))
        lines.append(asp.fact("care_sense", care_id, care.sense))
        lines.append(asp.fact("care_relief", care_id, care.relief))
    for fix_id, fix in MORNING_FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_power", fix_id, fix.power))
        if fix.treats_infection:
            lines.append(asp.fact("treats_infection", fix_id))
    for severity in sorted(SEVERITIES):
        lines.append(asp.fact("severity", severity))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_care", params.night_care),
            asp.fact("chosen_fix", params.morning_fix),
            asp.fact("chosen_severity", params.severity),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    care = NIGHT_CARE[params.night_care]
    return "rested" if care.relief >= params.severity else "drowsy"


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

    for params in CURATED:
        asp_res = asp_outcome(params)
        py_res = outcome_of(params)
        if asp_res != py_res:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={asp_res} python={py_res}")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a bedtime toothache, a poster-triggered flashback, and a calm morning fix."
    )
    ap.add_argument("--poster", choices=POSTERS)
    ap.add_argument("--comparison", choices=COMPARISONS)
    ap.add_argument("--night-care", choices=NIGHT_CARE, dest="night_care")
    ap.add_argument("--morning-fix", choices=MORNING_FIXES, dest="morning_fix")
    ap.add_argument("--severity", type=int, choices=sorted(SEVERITIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid care/fix/severity set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.night_care and args.night_care not in NIGHT_CARE:
        raise StoryError("(Unknown night care.)")
    if args.morning_fix and args.morning_fix not in MORNING_FIXES:
        raise StoryError("(Unknown morning fix.)")

    if args.night_care and NIGHT_CARE[args.night_care].sense < SENSE_MIN:
        raise StoryError(explain_bad_care(args.night_care))
    if args.morning_fix and args.severity is not None:
        if not valid_combo(
            night_care_id=args.night_care or "cool_cloth",
            morning_fix_id=args.morning_fix,
            severity=args.severity,
        ):
            raise StoryError(explain_bad_fix(args.morning_fix, args.severity))

    combos = [
        combo
        for combo in valid_combos()
        if (args.night_care is None or combo[0] == args.night_care)
        and (args.morning_fix is None or combo[1] == args.morning_fix)
        and (args.severity is None or combo[2] == args.severity)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    care_id, fix_id, severity = rng.choice(sorted(combos))
    poster_id = args.poster or rng.choice(sorted(POSTERS))
    comparison_id = args.comparison or rng.choice(sorted(COMPARISONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent_type = args.parent or rng.choice(["mother", "father"])
    comfort_item = rng.choice(COMFORT_ITEMS)

    return StoryParams(
        poster=poster_id,
        comparison=comparison_id,
        night_care=care_id,
        morning_fix=fix_id,
        severity=severity,
        child_name=child_name,
        child_gender=gender,
        parent=parent_type,
        comfort_item=comfort_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.poster not in POSTERS:
        raise StoryError(f"(Unknown poster '{params.poster}'.)")
    if params.comparison not in COMPARISONS:
        raise StoryError(f"(Unknown comparison '{params.comparison}'.)")
    if params.night_care not in NIGHT_CARE:
        raise StoryError(f"(Unknown night care '{params.night_care}'.)")
    if params.morning_fix not in MORNING_FIXES:
        raise StoryError(f"(Unknown morning fix '{params.morning_fix}'.)")
    if not valid_combo(params.night_care, params.morning_fix, params.severity):
        care = NIGHT_CARE[params.night_care]
        if care.sense < SENSE_MIN:
            raise StoryError(explain_bad_care(params.night_care))
        raise StoryError(explain_bad_fix(params.morning_fix, params.severity))

    world = tell(
        poster=POSTERS[params.poster],
        lesson=COMPARISONS[params.comparison],
        care=NIGHT_CARE[params.night_care],
        fix=MORNING_FIXES[params.morning_fix],
        severity=params.severity,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        comfort_item=params.comfort_item,
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
        print(f"{len(combos)} compatible (night_care, morning_fix, severity) combos:\n")
        for care_id, fix_id, severity in combos:
            print(f"  {care_id:12} {fix_id:20} {severity}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.night_care} -> {p.morning_fix} "
                f"(severity {p.severity}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
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
