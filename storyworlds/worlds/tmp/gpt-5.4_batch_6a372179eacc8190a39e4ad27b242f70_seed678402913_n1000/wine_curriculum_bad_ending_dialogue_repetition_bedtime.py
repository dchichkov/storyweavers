#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py
=====================================================================================

A standalone story world about a sleepy evening, a grown-up's curriculum papers,
and a glass of wine that can be knocked over. The seed asked for the words
"wine" and "curriculum" plus the features Bad Ending, Dialogue, and Repetition,
in a bedtime-story style, so this world models exactly that small domain.

Premise
-------
A child wants to stay close to a parent or teacher-like grown-up who is finishing
curriculum pages before bedtime. A glass of red wine sits nearby. The child is
sleepy, wants to help, and reaches or leans too close. If the adult makes the
safe move in time -- moving the wine far away or covering the papers -- the
evening ends gently. If not, the wine spills over the curriculum and the ending
is sad: the papers are ruined, bedtime comes with tears, and the work must be
done again.

Coverage rule
-------------
Not every drink/work pairing makes a strong story. This world only accepts
combinations where the drink can stain and the work is paper-based enough to be
ruined by a spill. It also refuses low-sense safeguards.

Run it
------
    python storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py
    python storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py --drink wine --work curriculum_pages
    python storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py --safeguard ignore
    python storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wine_curriculum_bad_ending_dialogue_repetition_bedtime.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    stain_level: int = 0
    soak_level: int = 0
    paper_work: bool = False
    has_lid: bool = False
    far_away: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    glow: str
    bedtime_sound: str
    table: str
    tags: set[str] = field(default_factory=set)


@dataclass
class WorkItem:
    id: str
    label: str
    phrase: str
    paper_work: bool
    absorbency: int
    bedtime_task: str
    ruin_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    stain_level: int
    soak_level: int
    adult_only: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Safeguard:
    id: str
    label: str
    sense: int
    power: int
    setup_text: str
    save_text: str
    fail_text: str
    qa_text: str
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


def _r_spill_ruins_work(world: World) -> list[str]:
    out: list[str] = []
    if "drink" not in world.entities or "work" not in world.entities:
        return out
    drink = world.get("drink")
    work = world.get("work")
    if drink.meters["spilled"] < THRESHOLD or not work.paper_work:
        return out
    sig = ("spill", drink.id, work.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    work.meters["wet"] += drink.soak_level
    work.meters["stained"] += drink.stain_level
    if work.meters["wet"] + work.meters["stained"] >= world.facts.get("ruin_need", 3):
        work.meters["ruined"] += 1
    out.append("__spill__")
    return out


def _r_ruin_saddens_people(world: World) -> list[str]:
    out: list[str] = []
    if "work" not in world.entities:
        return out
    work = world.get("work")
    if work.meters["ruined"] < THRESHOLD:
        return out
    sig = ("sad", work.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.role in {"child", "adult"}:
            ent.memes["sadness"] += 1
    world.get("adult").meters["redo_work"] += 1
    out.append("__sad__")
    return out


CAUSAL_RULES = [
    Rule(name="spill_ruins_work", tag="physical", apply=_r_spill_ruins_work),
    Rule(name="ruin_saddens_people", tag="emotional", apply=_r_ruin_saddens_people),
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


def hazard_at_risk(drink: Drink, work: WorkItem) -> bool:
    return drink.stain_level > 0 and drink.soak_level > 0 and work.paper_work


def sensible_safeguards() -> list[Safeguard]:
    return [s for s in SAFEGUARDS.values() if s.sense >= SENSE_MIN]


def risk_severity(drink: Drink, work: WorkItem, delay: int) -> int:
    return drink.stain_level + work.absorbency + delay


def is_saved(safeguard: Safeguard, drink: Drink, work: WorkItem, delay: int) -> bool:
    return safeguard.power >= risk_severity(drink, work, delay)


def explain_rejection(drink: Drink, work: WorkItem) -> str:
    if drink.stain_level <= 0 or drink.soak_level <= 0:
        return (
            f"(No story: {drink.label} would not make a strong spill hazard for {work.label}. "
            f"Pick a staining drink like wine or berry tea.)"
        )
    if not work.paper_work:
        return (
            f"(No story: {work.label} is not paper work that can be ruined by a spill. "
            f"Pick paper plans or curriculum pages.)"
        )
    return "(No story: this combination does not create a plausible spill problem.)"


def explain_safeguard(sid: str) -> str:
    sg = SAFEGUARDS[sid]
    better = ", ".join(sorted(s.id for s in sensible_safeguards()))
    return (
        f"(Refusing safeguard '{sid}': it scores too low on common sense "
        f"(sense={sg.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_spill(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    drink = sim.get("drink")
    work = sim.get("work")
    child.meters["reach"] += 1
    if not drink.far_away and not drink.has_lid:
        drink.meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": drink.meters["spilled"] >= THRESHOLD,
        "ruined": work.meters["ruined"] >= THRESHOLD,
    }


def bedtime_opening(world: World, child: Entity, adult: Entity, work: WorkItem, drink: Drink) -> None:
    world.say(
        f"In {world.setting.place}, the lamp made {world.setting.glow}. "
        f"{world.setting.bedtime_sound}"
    )
    world.say(
        f"{child.id} was almost ready for bed, but {adult.id} was still at {world.setting.table} "
        f"finishing {work.phrase}. Beside the papers stood {drink.phrase}."
    )


def bedtime_pull(world: World, child: Entity, adult: Entity) -> None:
    child.memes["attachment"] += 1
    child.memes["sleepiness"] += 1
    world.say(
        f'{child.id} padded closer in soft pajamas. "Are you coming soon?" {child.pronoun()} whispered.'
    )
    world.say(
        f'"Soon," said {adult.id}. "Just a few more lines, then bed. Sleepy now, sleepy now, sleepy now."'
    )


def child_offers_help(world: World, child: Entity, adult: Entity, work: WorkItem) -> None:
    child.memes["wish_to_help"] += 1
    world.say(
        f'"Can I help?" asked {child.id}. {adult.id} smiled a tired smile at the {work.label}.'
    )


def adult_warns(world: World, adult: Entity, child: Entity, drink: Drink, work: WorkItem) -> None:
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_ruin"] = pred["ruined"]
    adult.memes["worry"] += 1
    world.say(
        f'"You may sit beside me," said {adult.id}, "but not near the {drink.label}. '
        f'If it tips, it will spill on the {work.label}, and the curriculum will be ruined."'
    )
    world.say(
        f'{child.id} looked at the papers. "{work.label.capitalize()}?" {child.pronoun()} asked.'
    )
    world.say(
        f'"Yes," said {adult.id}. "These pages are my curriculum for tomorrow."'
    )


def adult_sets_safeguard(world: World, adult: Entity, safeguard: Safeguard) -> None:
    drink = world.get("drink")
    work = world.get("work")
    world.say(safeguard.setup_text)
    if safeguard.id == "move_far":
        drink.far_away = True
    elif safeguard.id == "tray_cover":
        work.meters["shielded"] += 1
    elif safeguard.id == "lidded_mug":
        drink.has_lid = True
    adult.memes["care"] += 1


def child_reaches(world: World, child: Entity, drink: Entity) -> None:
    child.meters["reach"] += 1
    child.memes["sleepiness"] += 1
    world.say(
        f'{child.id} nodded, but sleepiness made {child.pronoun("possessive")} body loose and wobbly. '
        f'"I only want to see," {child.pronoun()} said.'
    )
    if not drink.far_away:
        world.say(
            f'{child.pronoun("subject").capitalize()} leaned one small elbow onto the table edge. '
            f'Lean, lean, lean.'
        )


def spill(world: World, child: Entity, drink: Entity, work: Entity, drink_cfg: Drink, work_cfg: WorkItem) -> None:
    if not drink.far_away and not drink.has_lid:
        drink.meters["spilled"] += 1
    elif work.meters["shielded"] < THRESHOLD and not drink.far_away:
        drink.meters["spilled"] += 1
    propagate(world, narrate=False)
    if drink.meters["spilled"] >= THRESHOLD:
        world.say(
            f'Tap. Tip. Splash. The {drink_cfg.label} ran across the table and into the {work_cfg.label}.'
        )
        if work.meters["ruined"] >= THRESHOLD:
            world.say(work_cfg.ruin_line)
    else:
        world.say(
            f'The table gave a little shake, but the {drink_cfg.label} could not spill.'
        )


def saved_ending(world: World, adult: Entity, child: Entity, safeguard: Safeguard, work: WorkItem) -> None:
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(
        safeguard.save_text.replace("{work}", work.label)
    )
    world.say(
        f'"Oh," breathed {child.id}. "{work.label.capitalize()} is safe."'
    )
    world.say(
        f'"Safe," said {adult.id}. "And now it is bedtime for you." {child.id} climbed into bed '
        f'while the room stayed quiet and the pages stayed dry.'
    )


def bad_ending(world: World, adult: Entity, child: Entity, work: WorkItem, drink: Drink, safeguard: Safeguard) -> None:
    child.memes["guilt"] += 1
    adult.memes["sadness"] += 1
    world.say(
        safeguard.fail_text.replace("{work}", work.label)
    )
    world.say(
        f'{adult.id} pressed both hands to the table. "{work.label.capitalize()}," {adult.pronoun()} said softly. '
        f'"My curriculum pages."'
    )
    world.say(
        f'"I am sorry," whispered {child.id}. "Sorry, sorry, sorry."'
    )
    world.say(
        f'{adult.id} gave {child.id} a tired hug. "{adult.pronoun().capitalize()} know you did not mean to," '
        f'{adult.pronoun()} said. "But the {drink.label} ruined the work, and now I must start again."'
    )
    world.say(
        f'That night {child.id} went to bed with a heavy heart, and the warm room no longer felt cozy. '
        f'Behind the door, {adult.id} sat up late beside the stained curriculum, while the spilled {drink.label} smell '
        f'seemed sadder and sadder in the dark.'
    )


def tell(
    setting: Setting,
    work_cfg: WorkItem,
    drink_cfg: Drink,
    safeguard: Safeguard,
    *,
    child_name: str,
    child_gender: str,
    adult_name: str,
    adult_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait, "sleepy"],
        )
    )
    adult = world.add(
        Entity(
            id=adult_name,
            kind="character",
            type=adult_type,
            label=adult_name,
            role="adult",
            traits=["tired", "careful"],
        )
    )
    drink = world.add(
        Entity(
            id="drink",
            type="drink",
            label=drink_cfg.label,
            phrase=drink_cfg.phrase,
            role="drink",
            stain_level=drink_cfg.stain_level,
            soak_level=drink_cfg.soak_level,
            tags=set(drink_cfg.tags),
        )
    )
    work = world.add(
        Entity(
            id="work",
            type="papers",
            label=work_cfg.label,
            phrase=work_cfg.phrase,
            role="work",
            paper_work=work_cfg.paper_work,
            tags=set(work_cfg.tags),
        )
    )
    world.facts["ruin_need"] = drink_cfg.stain_level + work_cfg.absorbency
    world.facts["delay"] = delay

    bedtime_opening(world, child, adult, work_cfg, drink_cfg)
    bedtime_pull(world, child, adult)

    world.para()
    child_offers_help(world, child, adult, work_cfg)
    adult_warns(world, adult, child, drink_cfg, work_cfg)
    adult_sets_safeguard(world, adult, safeguard)

    for _ in range(delay + 1):
        child.memes["sleepiness"] += 1

    world.para()
    child_reaches(world, child, drink)
    spill(world, child, drink, work, drink_cfg, work_cfg)

    saved = is_saved(safeguard, drink_cfg, work_cfg, delay)
    world.para()
    if saved:
        saved_ending(world, adult, child, safeguard, work_cfg)
        outcome = "saved"
    else:
        bad_ending(world, adult, child, work_cfg, drink_cfg, safeguard)
        outcome = "ruined"

    world.facts.update(
        child=child,
        adult=adult,
        drink_cfg=drink_cfg,
        work_cfg=work_cfg,
        safeguard=safeguard,
        outcome=outcome,
        saved=saved,
        drink=drink,
        work=work,
        setting=setting,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    work: str
    drink: str
    safeguard: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_type: str
    trait: str
    delay: int = 1
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the quiet kitchen",
        glow="a small honey-colored circle on the table",
        bedtime_sound="Outside, the house had gone hush-hush for the night.",
        table="the round kitchen table",
        tags={"bedtime", "kitchen"},
    ),
    "study": Setting(
        id="study",
        place="the little study by the hall",
        glow="a sleepy puddle of lamplight on the desk",
        bedtime_sound="The hallway was dim, and every floorboard seemed to whisper bedtime.",
        table="the writing desk",
        tags={"bedtime", "study"},
    ),
    "dining_room": Setting(
        id="dining_room",
        place="the dining room after supper",
        glow="a soft yellow shine over the long table",
        bedtime_sound="The dishes were done, and the night had turned slow and still.",
        table="the big wooden table",
        tags={"bedtime", "dining"},
    ),
}

WORKS = {
    "curriculum_pages": WorkItem(
        id="curriculum_pages",
        label="curriculum pages",
        phrase="a stack of curriculum pages with little notes in the margins",
        paper_work=True,
        absorbency=2,
        bedtime_task="finishing tomorrow's curriculum",
        ruin_line="Red drops spread through the paper, curling the corners and blurring the careful writing.",
        tags={"curriculum", "paper"},
    ),
    "lesson_plan": WorkItem(
        id="lesson_plan",
        label="lesson plan sheets",
        phrase="lesson plan sheets for next morning's curriculum",
        paper_work=True,
        absorbency=2,
        bedtime_task="checking the lesson plan",
        ruin_line="The ink feathered out in purple-red rivers until the lines could hardly be read.",
        tags={"curriculum", "paper"},
    ),
    "reading_chart": WorkItem(
        id="reading_chart",
        label="reading chart pages",
        phrase="reading chart pages tucked inside the curriculum folder",
        paper_work=True,
        absorbency=1,
        bedtime_task="sorting reading chart pages",
        ruin_line="The chart boxes went soggy at once, and the little marks washed into clouds.",
        tags={"curriculum", "paper"},
    ),
    "tablet_notes": WorkItem(
        id="tablet_notes",
        label="tablet notes",
        phrase="notes on a bright tablet beside the curriculum folder",
        paper_work=False,
        absorbency=0,
        bedtime_task="checking notes on a tablet",
        ruin_line="",
        tags={"tablet"},
    ),
}

DRINKS = {
    "wine": Drink(
        id="wine",
        label="wine",
        phrase="a glass of red wine",
        stain_level=2,
        soak_level=1,
        adult_only=True,
        tags={"wine", "spill"},
    ),
    "berry_tea": Drink(
        id="berry_tea",
        label="berry tea",
        phrase="a mug of dark berry tea",
        stain_level=1,
        soak_level=1,
        adult_only=False,
        tags={"tea", "spill"},
    ),
    "water": Drink(
        id="water",
        label="water",
        phrase="a glass of water",
        stain_level=0,
        soak_level=1,
        adult_only=False,
        tags={"water"},
    ),
}

SAFEGUARDS = {
    "move_far": Safeguard(
        id="move_far",
        label="move the drink far away",
        sense=3,
        power=5,
        setup_text='Before anything else, the grown-up slid the drink to a high side shelf, far from the papers and far from small elbows.',
        save_text='Because the drink was far away, nothing touched the {work}.',
        fail_text='But the papers were still too near the edge, and trouble found them anyway.',
        qa_text="moved the drink far from the papers",
        tags={"move", "safety"},
    ),
    "tray_cover": Safeguard(
        id="tray_cover",
        label="put the papers on a tray",
        sense=3,
        power=4,
        setup_text='The grown-up tucked the papers onto a tray with raised sides and drew them close.',
        save_text='The little tray wall caught the mess before it could soak the {work}.',
        fail_text='The tray helped a little, but not enough to stop the spill from reaching the {work}.',
        qa_text="put the papers on a tray to protect them",
        tags={"tray", "safety"},
    ),
    "lidded_mug": Safeguard(
        id="lidded_mug",
        label="pour the drink into a lidded mug",
        sense=2,
        power=3,
        setup_text='The grown-up poured the drink into a travel mug with a lid and set it beside the lamp.',
        save_text='The lid kept the mess inside, so the {work} stayed dry.',
        fail_text='The mug wobbled, and even that small protection was not enough for the {work}.',
        qa_text="used a lidded mug so the drink could not spill easily",
        tags={"lid", "safety"},
    ),
    "ignore": Safeguard(
        id="ignore",
        label="leave everything as it is",
        sense=1,
        power=0,
        setup_text='The grown-up meant to be careful, but left the drink and papers crowded together on the table.',
        save_text='Nothing bad happened this time.',
        fail_text='Nothing stood between the drink and the {work} when the table shook.',
        qa_text="did not protect the papers at all",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Noah", "Eli"]
ADULT_NAMES = ["Mama", "Dad", "Aunt June", "Teacher May"]
TRAITS = ["gentle", "curious", "sleepy", "helpful", "soft-voiced"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for work_id, work in WORKS.items():
            for drink_id, drink in DRINKS.items():
                if hazard_at_risk(drink, work):
                    combos.append((setting_id, work_id, drink_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    return "saved" if is_saved(SAFEGUARDS[params.safeguard], DRINKS[params.drink], WORKS[params.work], params.delay) else "ruined"


KNOWLEDGE = {
    "wine": [
        (
            "What is wine?",
            "Wine is a grown-up drink made from fruit, often grapes. Children should not drink it, and any drink near papers can make a mess if it spills.",
        )
    ],
    "curriculum": [
        (
            "What is a curriculum?",
            "A curriculum is a plan for what children will learn. A teacher or parent may write curriculum pages to help guide lessons.",
        )
    ],
    "spill": [
        (
            "Why can a spill ruin paper?",
            "Paper soaks up liquid very quickly. When a dark drink spills on it, the writing can blur and the pages can tear or wrinkle.",
        )
    ],
    "tray": [
        (
            "How can a tray help keep papers safe?",
            "A tray can lift papers a little and catch small drips around them. It gives the mess one more wall to stop against.",
        )
    ],
    "lid": [
        (
            "Why does a lid help with a drink?",
            "A lid makes it harder for a drink to splash out when something bumps it. It is a simple way to make spills less likely.",
        )
    ],
    "bedtime": [
        (
            "Why do small children get clumsy when they are sleepy?",
            "When children are very sleepy, their bodies may feel slow and wobbly. That can make bumps and spills happen more easily.",
        )
    ],
    "move": [
        (
            "Why is moving a drink farther away a smart idea?",
            "Distance makes accidents less likely. If a drink is far from important things, a little bump cannot reach them.",
        )
    ],
}
KNOWLEDGE_ORDER = ["wine", "curriculum", "spill", "tray", "lid", "bedtime", "move"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    work = f["work_cfg"]
    drink = f["drink_cfg"]
    outcome = f["outcome"]
    if outcome == "ruined":
        return [
            f'Write a bedtime story for ages 3 to 5 that includes the words "wine" and "curriculum", uses dialogue and repetition, and ends sadly when a spill ruins important papers.',
            f"Tell a soft, child-facing bad-ending story where {child.id} stays up past bedtime, leans too close to {adult.id}'s {drink.label}, and the {work.label} are ruined.",
            f'Write a quiet nighttime story with repeated words, whispered dialogue, and a sad last image showing a grown-up still awake beside stained curriculum papers.',
        ]
    return [
        f'Write a bedtime story for ages 3 to 5 that includes the words "wine" and "curriculum", uses dialogue and repetition, and ends with the papers kept safe.',
        f"Tell a gentle nighttime story where {child.id} wants to help, but {adult.id} protects the {work.label} from the {drink.label} in time.",
        f'Write a soft, dialogue-rich story where bedtime comes only after a careful grown-up prevents a spill and keeps the curriculum safe.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    work = f["work_cfg"]
    drink = f["drink_cfg"]
    safeguard = f["safeguard"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was sleepy but wanted to stay near {adult.id}, and about {adult.id}, who was finishing {work.phrase}. The quiet room and the late hour made the whole story feel close to bedtime.",
        ),
        (
            f"What was {adult.id} working on?",
            f"{adult.id} was working on {work.label}. {adult.pronoun('possessive').capitalize()} pages were part of the curriculum for the next day.",
        ),
        (
            f"Why did {adult.id} warn {child.id} about the {drink.label}?",
            f"{adult.id} knew the {drink.label} could spill onto the {work.label} and ruin them. The warning came because the papers were important and paper soaks up liquid fast.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How were the papers kept safe?",
                f"{adult.id} {safeguard.qa_text}. That safety step stopped the spill problem before it could reach the {work.label}.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. {child.id} went to bed while the {work.label} stayed dry, which showed that being careful changed the night.",
            )
        )
    else:
        qa.append(
            (
                "What went wrong in the story?",
                f"{child.id} leaned too close while feeling sleepy, and the {drink.label} spilled across the {work.label}. The pages were ruined because the liquid soaked in and blurred the careful writing.",
            )
        )
        qa.append(
            (
                "Why is the ending sad?",
                f"The ending is sad because {adult.id}'s work was spoiled and had to be done again late at night. {child.id} was sorry too, so bedtime came with guilt instead of comfort.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bedtime"}
    f = world.facts
    tags |= set(f["drink_cfg"].tags)
    tags |= set(f["work_cfg"].tags)
    tags |= set(f["safeguard"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.far_away:
            bits.append("far_away=True")
        if ent.has_lid:
            bits.append("has_lid=True")
        if ent.paper_work:
            bits.append("paper_work=True")
        if ent.stain_level:
            bits.append(f"stain={ent.stain_level}")
        if ent.soak_level:
            bits.append(f"soak={ent.soak_level}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(D, W) :- drink(D), work(W), staining(D), soaking(D), paper_work(W).
sensible(S)  :- safeguard(S), sense(S, X), sense_min(M), X >= M.
valid(Place, W, D) :- setting(Place), work(W), drink(D), hazard(D, W).

severity(V) :- chosen_drink(D), stain(D, SD), chosen_work(W), absorbency(W, A), delay(Del), V = SD + A + Del.
saved :- chosen_safeguard(S), power(S, P), severity(V), P >= V.
outcome(saved) :- saved.
outcome(ruined) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid, work in WORKS.items():
        lines.append(asp.fact("work", wid))
        lines.append(asp.fact("absorbency", wid, work.absorbency))
        if work.paper_work:
            lines.append(asp.fact("paper_work", wid))
    for did, drink in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("stain", did, drink.stain_level))
        if drink.stain_level > 0:
            lines.append(asp.fact("staining", did))
        if drink.soak_level > 0:
            lines.append(asp.fact("soaking", did))
    for sgid, sg in SAFEGUARDS.items():
        lines.append(asp.fact("safeguard", sgid))
        lines.append(asp.fact("sense", sgid, sg.sense))
        lines.append(asp.fact("power", sgid, sg.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(atom[0] for atom in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_drink", params.drink),
            asp.fact("chosen_work", params.work),
            asp.fact("chosen_safeguard", params.safeguard),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="kitchen",
        work="curriculum_pages",
        drink="wine",
        safeguard="ignore",
        child_name="Lily",
        child_gender="girl",
        adult_name="Mama",
        adult_type="mother",
        trait="helpful",
        delay=1,
    ),
    StoryParams(
        setting="study",
        work="lesson_plan",
        drink="wine",
        safeguard="tray_cover",
        child_name="Ben",
        child_gender="boy",
        adult_name="Dad",
        adult_type="father",
        trait="curious",
        delay=2,
    ),
    StoryParams(
        setting="dining_room",
        work="reading_chart",
        drink="berry_tea",
        safeguard="lidded_mug",
        child_name="Nora",
        child_gender="girl",
        adult_name="Teacher May",
        adult_type="teacher",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        setting="kitchen",
        work="curriculum_pages",
        drink="wine",
        safeguard="move_far",
        child_name="Max",
        child_gender="boy",
        adult_name="Aunt June",
        adult_type="aunt",
        trait="sleepy",
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime, curriculum papers, and a spill hazard."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--work", choices=WORKS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--safeguard", choices=SAFEGUARDS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "teacher", "aunt"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how slow the grown-up is to settle the moment")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.drink and args.work:
        drink = DRINKS[args.drink]
        work = WORKS[args.work]
        if not hazard_at_risk(drink, work):
            raise StoryError(explain_rejection(drink, work))
    if args.safeguard and SAFEGUARDS[args.safeguard].sense < SENSE_MIN:
        raise StoryError(explain_safeguard(args.safeguard))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.work is None or combo[1] == args.work)
        and (args.drink is None or combo[2] == args.drink)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, work_id, drink_id = rng.choice(sorted(combos))
    safeguard_id = args.safeguard or rng.choice(sorted(s.id for s in sensible_safeguards()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father", "teacher", "aunt"])
    if adult_type == "mother":
        adult_name = "Mama"
    elif adult_type == "father":
        adult_name = "Dad"
    elif adult_type == "teacher":
        adult_name = "Teacher May"
    else:
        adult_name = "Aunt June"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        work=work_id,
        drink=drink_id,
        safeguard=safeguard_id,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_type=adult_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.work not in WORKS:
        raise StoryError(f"(Unknown work item: {params.work})")
    if params.drink not in DRINKS:
        raise StoryError(f"(Unknown drink: {params.drink})")
    if params.safeguard not in SAFEGUARDS:
        raise StoryError(f"(Unknown safeguard: {params.safeguard})")

    work_cfg = WORKS[params.work]
    drink_cfg = DRINKS[params.drink]
    safeguard = SAFEGUARDS[params.safeguard]

    if not hazard_at_risk(drink_cfg, work_cfg):
        raise StoryError(explain_rejection(drink_cfg, work_cfg))
    if safeguard.sense < SENSE_MIN:
        raise StoryError(explain_safeguard(params.safeguard))

    world = tell(
        SETTINGS[params.setting],
        work_cfg,
        drink_cfg,
        safeguard,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_type=params.adult_type,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {s.id for s in sensible_safeguards()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible safeguards match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible safeguards: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            case = resolve_params(parser.parse_args([]), random.Random(seed))
            case.seed = seed
            cases.append(case)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible safeguards: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, work, drink) combos:\n")
        for setting_id, work_id, drink_id in combos:
            print(f"  {setting_id:12} {work_id:18} {drink_id}")
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
            header = f"### {p.child_name}: {p.drink} near {p.work} ({p.setting}, {p.safeguard}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
