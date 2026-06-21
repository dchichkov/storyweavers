#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trample_entire_slush_humor_rhyme_rhyming_story.py
=============================================================================

A tiny rhyming storyworld about a child who wants to trample spring slush while
wearing something special. The world model checks whether the slush would really
reach that clothing item and whether the offered over-gear actually protects it.

The stories lean playful and child-facing, with gentle humor and a light rhyme.

Run it
------
    python storyworlds/worlds/gpt-5.4/trample_entire_slush_humor_rhyme_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/trample_entire_slush_humor_rhyme_rhyming_story.py --activity trample --prize socks
    python storyworlds/worlds/gpt-5.4/trample_entire_slush_humor_rhyme_rhyming_story.py --prize cape --activity trample
    python storyworlds/worlds/gpt-5.4/trample_entire_slush_humor_rhyme_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/trample_entire_slush_humor_rhyme_rhyming_story.py --verify
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

# Make storyworlds/results.py importable when this script is run directly from
# the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

MESS_KINDS = {"wet", "slushy", "dirty"}
IMPULSIVE_TRAITS = {"bouncy", "zany", "bold"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    weather_line: str = ""
    slush_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str] = field(default_factory=set)
    boast: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str, mess: str) -> bool:
        for item in self.worn_items(actor):
            if item.protective and region in item.covers and mess in item.guards:
                return True
        return False

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
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region, mess):
                    continue
                sig = ("soak", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append("__splash__")
    return out


def _r_chill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["slushy"] < THRESHOLD:
            continue
        sig = ("chill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["discomfort"] += 1
        out.append("__chill__")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append("__work__")
    return out


CAUSAL_RULES = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="chill", tag="physical", apply=_r_chill),
    Rule(name="workload", tag="physical", apply=_r_workload),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def compatible_gears(activity: Activity, prize: Prize) -> list[str]:
    out: list[str] = []
    for gid, gear in GEARS.items():
        if activity.mess in gear.guards and prize.region in gear.covers:
            out.append(gid)
    return sorted(out)


def select_best_gear(activity: Activity, prize: Prize) -> Optional[str]:
    choices = compatible_gears(activity, prize)
    return choices[0] if choices else None


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    if activity.mess != "wet":
        actor.meters["wet"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=False)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity)
    prize = sim.get(prize_id)
    return {
        "soiled": prize.meters["dirty"] >= THRESHOLD,
        "actor_wet": sim.get(actor.id).meters["wet"] >= THRESHOLD,
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def introduce(world: World, hero: Entity, prize: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "merry")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} with a giggle-springy stride. "
        f"{hero.pronoun().capitalize()} wore {prize.phrase} and felt as grand as a glide."
    )


def scene_set(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{world.setting.weather_line} {world.setting.slush_line} "
        f"To {hero.id}, the {activity.id} looked like a drum with a squish for a tune."
    )


def desire(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'"I want to {activity.verb}!" sang {hero.id}. "{activity.boast}" '
        f"{hero.pronoun().capitalize()} bounced as if ready to zoom."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'{parent.label_word.capitalize()} knelt by the door and spoke in a practical croon: '
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil} soon. '
        f'Then I must wash {prize.it()}, and cold little toes are no boon."'
    )
    return True


def lunge(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the slush made a comic plop-plop, a sillily splashable rune, "
        f"and {hero.id} tried to {activity.rush} before breakfast had finished its tune."
    )


def splash(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    _do_activity(world, hero, activity)
    if prize.meters["dirty"] >= THRESHOLD:
        world.say(
            f"SQUISH went the step, and SPLISH went the spray in a slapdash monsoon. "
            f"{hero.id}'s {prize.label} turned {activity.soil}, which ended the boasting quite soon."
        )
    else:
        world.say(
            f"SQUISH went the step, but only a tiny drop hopped up too soon. "
            f"It was a good thing the grown-up was thinking ahead that noon."
        )


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, gear: Gear) -> None:
    world.say(
        f'{parent.label_word.capitalize()} hid a smile and pointed instead. '
        f'"How about we {gear.prep}, then {activity.gerund} can still go ahead?"'
    )


def put_on_gear(world: World, hero: Entity, parent: Entity, gear: Gear) -> Entity:
    ent = world.add(
        Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            phrase=gear.phrase,
            owner=hero.id,
            caretaker=parent.id,
            worn_by=hero.id,
            protective=True,
            covers=set(gear.covers),
            guards=set(gear.guards),
            plural=gear.plural,
            tags=set(gear.tags),
        )
    )
    return ent


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    world.say(
        f"{hero.id}'s frown folded up small, like a letter and not like a feud. "
        f"{hero.pronoun().capitalize()} nodded and laughed, for the plan was both clever and shrewd."
    )
    world.say(
        f"They {gear.tail}. Soon the entire path rang with a thumpety, slumpety beat, "
        f"and {hero.id} could {activity.verb} while warm, dry, and sweet on {hero.pronoun('possessive')} feet."
    )


def ending(world: World, hero: Entity, parent: Entity, prize: Entity, gear: Gear, activity: Activity) -> None:
    safe = predict_mess(world, hero, activity, prize.id)
    if not safe["soiled"]:
        world.say(
            f"{hero.id}'s {prize.label} stayed neat, and that felt like a triumph complete. "
            f'Even {parent.label_word} laughed, "What a fine slush-band drummer you meet!"'
        )
    else:
        world.say(
            f"The game went on softly and sensibly after the street-side retreat. "
            f"The rhyme still bounced on, but now it had warm, careful feet."
        )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, gear_cfg: Gear,
         hero_name: str = "Milo", hero_type: str = "boy",
         trait: str = "bouncy", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little", trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            worn_by=hero.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
            tags=set(prize_cfg.tags),
        )
    )

    introduce(world, hero, prize)
    scene_set(world, hero, activity)

    world.para()
    desire(world, hero, activity)
    warned = warn(world, parent, hero, activity, prize)

    impulsive = trait in IMPULSIVE_TRAITS
    if warned and impulsive:
        lunge(world, hero, activity)
        splash(world, hero, prize, activity)

    world.para()
    gear_ent = put_on_gear(world, hero, parent, gear_cfg)
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        raise StoryError(
            f"(No story: {gear_cfg.label} does not really protect the {prize_cfg.label} "
            f"from {activity.gerund}.)"
        )
    offer_gear(world, parent, hero, activity, gear_cfg)
    accept(world, hero, parent, activity, gear_cfg)

    world.para()
    _do_activity(world, hero, activity)
    ending(world, hero, parent, prize, gear_cfg, activity)

    outcome = "splashed_then_fixed" if prize.meters["dirty"] >= THRESHOLD else "careful_then_fixed"
    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        setting=setting,
        activity=activity,
        gear=gear_ent,
        gear_cfg=gear_cfg,
        warned=warned,
        impulsive=impulsive,
        early_splash=prize.meters["dirty"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


SETTINGS = {
    "sidewalk": Setting(
        id="sidewalk",
        place="the front sidewalk",
        affords={"trample", "march"},
        weather_line="Morning sun dripped from the roof with a plinkety, tinkly hush.",
        slush_line="Along the curb, the entire sidewalk sagged into silver-brown slush.",
        tags={"slush"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard gate",
        affords={"trample", "skip"},
        weather_line="The snowbanks were shrinking in crooked, drippy rows.",
        slush_line="By the gate, the entire yard-edge bubbled with slush between the stones.",
        tags={"slush"},
    ),
    "park": Setting(
        id="park",
        place="the park path",
        affords={"march", "skip"},
        weather_line="Clouds floated by like sheep with damp wool and rosy cheeks.",
        slush_line="The path held slush in long wobbly ribbons that squeaked when a boot would speak.",
        tags={"slush"},
    ),
}

ACTIVITIES = {
    "trample": Activity(
        id="trample",
        verb="trample the slush",
        gerund="trampling the slush",
        rush="dash out and trample the slush",
        mess="slushy",
        soil="slushy and brown",
        zone={"feet", "legs"},
        boast="I'll stamp a pudding-band beat till the sparrows all swoon",
        tags={"slush", "boots"},
    ),
    "march": Activity(
        id="march",
        verb="march through the slush",
        gerund="marching through the slush",
        rush="march straight into the slush",
        mess="wet",
        soil="wet and muddy",
        zone={"feet", "legs"},
        boast="I'll march like a duck in a pudding parade this noon",
        tags={"slush", "boots"},
    ),
    "skip": Activity(
        id="skip",
        verb="skip by the slushy edge",
        gerund="skipping by the slushy edge",
        rush="skip toward the slush",
        mess="wet",
        soil="wet and speckled",
        zone={"feet"},
        boast="I'll skip with a plip and a flip and a slippery tune",
        tags={"slush", "boots"},
    ),
}

PRIZES = {
    "socks": Prize(
        id="socks",
        label="socks",
        phrase="stripy lemon socks",
        type="socks",
        region="feet",
        plural=True,
        tags={"socks"},
    ),
    "trousers": Prize(
        id="trousers",
        label="trousers",
        phrase="blue twirly trousers with starry knees",
        type="trousers",
        region="legs",
        plural=True,
        tags={"trousers"},
    ),
    "cape": Prize(
        id="cape",
        label="cape",
        phrase="a bright red cape that flapped like soup on the wind",
        type="cape",
        region="torso",
        plural=False,
        tags={"cape"},
    ),
}

GEARS = {
    "boots": Gear(
        id="boots",
        label="rubber boots",
        phrase="a pair of rubber boots",
        covers={"feet"},
        guards={"wet", "slushy"},
        prep="pull on the rubber boots first",
        tail="went inside, wiggled into the rubber boots, and came back with a stomp",
        plural=True,
        tags={"boots"},
    ),
    "rain_pants": Gear(
        id="rain_pants",
        label="rain pants",
        phrase="a pair of swishy rain pants",
        covers={"legs"},
        guards={"wet", "slushy"},
        prep="pull on the swishy rain pants first",
        tail="went inside, swished into the rain pants, and came back sounding like a tiny parade",
        plural=True,
        tags={"rain_pants"},
    ),
    "snow_suit": Gear(
        id="snow_suit",
        label="snow suit",
        phrase="a puffy snow suit",
        covers={"feet", "legs", "torso"},
        guards={"wet", "slushy"},
        prep="zip into the puffy snow suit first",
        tail="went inside, zipped into the snow suit, and came back looking like a bouncing blueberry bun",
        plural=False,
        tags={"snow_suit"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Tess"]
BOY_NAMES = ["Milo", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["bouncy", "zany", "careful", "bold", "curious", "merry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in sorted(setting.affords):
            activity = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(activity, prize) and compatible_gears(activity, prize):
                    combos.append((place, act_id, prize_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    gear: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="sidewalk",
        activity="trample",
        prize="socks",
        gear="boots",
        name="Milo",
        gender="boy",
        parent="mother",
        trait="bouncy",
    ),
    StoryParams(
        place="schoolyard",
        activity="trample",
        prize="trousers",
        gear="rain_pants",
        name="Nora",
        gender="girl",
        parent="father",
        trait="bold",
    ),
    StoryParams(
        place="park",
        activity="march",
        prize="trousers",
        gear="rain_pants",
        name="Leo",
        gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        place="schoolyard",
        activity="skip",
        prize="socks",
        gear="boots",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="zany",
    ),
]


KNOWLEDGE = {
    "slush": [
        (
            "What is slush?",
            "Slush is partly melted snow mixed with water, and often a little dirt too. It feels squishy under your feet and can splash high when you step in it.",
        )
    ],
    "boots": [
        (
            "Why do rubber boots help in slush?",
            "Rubber boots keep wet slush away from your feet. They let you stomp and splash without soaking your socks.",
        )
    ],
    "rain_pants": [
        (
            "What do rain pants do?",
            "Rain pants cover your legs with a water-shedding layer. That helps keep splashes off the clothes underneath.",
        )
    ],
    "snow_suit": [
        (
            "Why is a snow suit good for wet snow?",
            "A snow suit covers much more of your body than ordinary clothes. That makes it useful when wet snow or slush can splash in many places.",
        )
    ],
    "socks": [
        (
            "Why do wet socks feel uncomfortable?",
            "Wet socks cling to your skin and lose warmth fast. That can make your feet feel cold and squishy.",
        )
    ],
    "trousers": [
        (
            "Why are muddy trousers hard to ignore?",
            "Mud and slush stick to cloth and dry into marks. Someone usually has to wash the trousers before they feel nice again.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    activity = world.facts["activity"]
    prize = world.facts["prize_cfg"]
    return [
        f'Write a humorous rhyming story for a 3-to-5-year-old that includes the words "trample", "entire", and "slush".',
        f"Tell a playful rhyme about {hero.id}, who wants to {activity.verb} while wearing {prize.phrase}, and a grown-up who finds a sensible fix.",
        f"Write a child-facing story in bouncing couplets where slush is tempting, clothes are at risk, and the ending proves the child can still play safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    prize = world.facts["prize"]
    activity = world.facts["activity"]
    gear = world.facts["gear"]
    prize_cfg = world.facts["prize_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type} who badly wanted to {activity.verb}, and {hero.pronoun('possessive')} {pw} who helped make that possible in a safer way.",
        ),
        (
            f"Why did {hero.id}'s {pw} worry?",
            f"{pw.capitalize()} worried because {activity.verb} would splash the {prize_cfg.region}, and {hero.id}'s {prize.label} could get {activity.soil}. That would make the clothes uncomfortable and create extra washing too.",
        ),
    ]
    if world.facts.get("early_splash"):
        qa.append(
            (
                f"What happened when {hero.id} rushed toward the slush?",
                f"{hero.id} got one splash in before the plan changed, and the {prize.label} turned {activity.soil}. That quick mess proved the warning was right, because the slush really could reach that clothing item.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} ruin the {prize.label} before the fix?",
                f"No. The warning came in time, so the special {prize.label} stayed neat before the safer gear went on. The story's tension comes from what almost happened, not from a big disaster.",
            )
        )
    qa.append(
        (
            "How was the problem solved?",
            f"The grown-up had {hero.id} put on {gear.label} first. That gear covered the part of the body the slush could hit, so {hero.id} could still play without ruining the special clothes underneath.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {hero.id} back outside, still full of bounce, making happy noise in the slush instead of a soggy fuss. The final image shows that the play continued, but now it was warm and sensible.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"slush"}
    prize_cfg = world.facts["prize_cfg"]
    gear_cfg = world.facts["gear_cfg"]
    tags |= set(prize_cfg.tags)
    tags |= set(gear_cfg.tags)
    out: list[tuple[str, str]] = []
    order = ["slush", "boots", "rain_pants", "snow_suit", "socks", "trousers"]
    for tag in order:
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
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)} guards={sorted(e.guards)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} only splashes {sorted(activity.zone)}, but "
            f"the {prize.label} sits on the {prize.region}. The warning would not be honest.)"
        )
    return (
        f"(No story: nothing in the gear catalog really protects the {prize.label} "
        f"from {activity.gerund}. The fix must cover the part that gets splashed.)"
    )


def explain_gear(activity: Activity, prize: Prize, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} does not properly protect the {prize.label} from "
        f"{activity.gerund}. Pick gear that covers the {prize.region} and guards against {activity.mess}.)"
    )


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, G) :- valid(Place, A, P), protects(G, A, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act_id, activity in ACTIVITIES.items():
        lines.append(asp.fact("activity", act_id))
        lines.append(asp.fact("mess_of", act_id, activity.mess))
        for region in sorted(activity.zone):
            lines.append(asp.fact("splashes", act_id, region))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("worn_on", prize_id, prize.region))
    for gear_id, gear in GEARS.items():
        lines.append(asp.fact("gear", gear_id))
        for region in sorted(gear.covers):
            lines.append(asp.fact("covers", gear_id, region))
        for mess in sorted(gear.guards):
            lines.append(asp.fact("guards", gear_id, mess))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming slush storyworld: a child wants to trample the slush, and a sensible grown-up finds gear that really works."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.prize:
        activity = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(activity, prize) and compatible_gears(activity, prize)):
            raise StoryError(explain_rejection(activity, prize))
    if args.gear and args.activity and args.prize:
        activity = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        gear = GEARS[args.gear]
        if args.gear not in compatible_gears(activity, prize):
            raise StoryError(explain_gear(activity, prize, gear))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.activity is None or combo[1] == args.activity)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity_id, prize_id = rng.choice(sorted(combos))
    activity = ACTIVITIES[activity_id]
    prize = PRIZES[prize_id]

    legal_gears = compatible_gears(activity, prize)
    if args.gear:
        if args.gear not in legal_gears:
            raise StoryError(explain_gear(activity, prize, GEARS[args.gear]))
        gear_id = args.gear
    else:
        gear_id = rng.choice(legal_gears)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        activity=activity_id,
        prize=prize_id,
        gear=gear_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"(Unknown activity: {params.activity})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")

    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    gear = GEARS[params.gear]

    if params.activity not in setting.affords:
        raise StoryError(f"(No story: {setting.place} does not support {activity.gerund}.)")
    if params.prize not in PRIZES or not prize_at_risk(activity, prize):
        raise StoryError(explain_rejection(activity, prize))
    if params.gear not in compatible_gears(activity, prize):
        raise StoryError(explain_gear(activity, prize, gear))

    world = tell(
        setting=setting,
        activity=activity,
        prize_cfg=prize,
        gear_cfg=gear,
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
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

    stories = asp_valid_stories()
    python_story_set = set()
    for place, activity_id, prize_id in python_set:
        for gear_id in compatible_gears(ACTIVITIES[activity_id], PRIZES[prize_id]):
            python_story_set.add((place, activity_id, prize_id, gear_id))
    clingo_story_set = set(stories)
    if clingo_story_set == python_story_set:
        print(f"OK: gear-level ASP stories match ({len(clingo_story_set)} cases).")
    else:
        rc = 1
        print("MISMATCH in gear-level valid stories:")
        if clingo_story_set - python_story_set:
            print("  only in clingo:", sorted(clingo_story_set - python_story_set))
        if python_story_set - clingo_story_set:
            print("  only in python:", sorted(python_story_set - clingo_story_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "slush" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missing slush.)")
        _ = sample.to_dict()
        print("OK: smoke-tested normal generation.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            _ = generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, activity, prize in triples:
            gears = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, activity, prize))
            print(f"  {place:10} {activity:8} {prize:10} [{', '.join(gears)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize}, gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
