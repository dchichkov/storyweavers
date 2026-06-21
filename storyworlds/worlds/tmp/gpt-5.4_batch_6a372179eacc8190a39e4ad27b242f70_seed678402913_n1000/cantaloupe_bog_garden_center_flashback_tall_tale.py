#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py
==============================================================================

A standalone story world about a giant cantaloupe at a garden center, rebuilt as
a small classical simulation with a flashback and a tall-tale voice.

Premise
-------
A child visits a garden center and falls in love with an enormous cantaloupe
vine meant for a bragging contest. But the vine has been left in soggy bog
conditions near the water-loving plants, and the heavy fruit begins to droop.
A grown-up helper remembers an old lesson in a flashback: giant melons need
high, dry support, not a boggy bed. They act on that memory. If they act soon
and use the right fix, the cantaloupe rises into a happy, ridiculous tall-tale
ending. If they wait too long, the fruit slumps and the lesson lands harder.

Run it
------
python storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py
python storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py --bog peat_bog --remedy hay_mound
python storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py --remedy ribbon_bow
python storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/cantaloupe_bog_garden_center_flashback_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "clerk_f"}
        male = {"boy", "man", "father", "uncle", "clerk_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "clerk_f": "clerk",
            "clerk_m": "clerk",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class MelonKind:
    id: str
    label: str
    phrase: str
    boast: str
    heft: int
    growth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BogKind:
    id: str
    label: str
    phrase: str
    sogginess: int
    image: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StandKind:
    id: str
    label: str
    phrase: str
    wobble: int
    tags: set[str] = field(default_factory=set)


@dataclass
class RemedyKind:
    id: str
    label: str
    phrase: str
    drain_power: int
    brace_power: int
    sense: int
    move_text: str
    success_text: str
    fail_text: str
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


def _r_bog_sag(world: World) -> list[str]:
    melon = world.get("melon")
    if melon.meters["waterlogged"] < THRESHOLD:
        return []
    sig = ("bog_sag",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    melon.meters["droop"] += 1
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return ["__droop__"]


def _r_recover(world: World) -> list[str]:
    melon = world.get("melon")
    if melon.meters["drained"] < THRESHOLD or melon.meters["braced"] < THRESHOLD:
        return []
    sig = ("recover",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    melon.meters["lifted"] += 1
    melon.meters["droop"] = 0.0
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["hope"] += 1
    return ["__lift__"]


CAUSAL_RULES = [
    Rule(name="bog_sag", tag="physical", apply=_r_bog_sag),
    Rule(name="recover", tag="physical", apply=_r_recover),
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


@dataclass
class StoryParams:
    melon: str
    bog: str
    stand: str
    remedy: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    contest: str
    delay: int = 0
    seed: Optional[int] = None


MELONS = {
    "striped_giant": MelonKind(
        id="striped_giant",
        label="cantaloupe",
        phrase="a striped cantaloupe so round it looked as if the moon had rolled into the produce aisle",
        boast="as wide as a wash tub",
        heft=2,
        growth="By noon it seemed to swell just from hearing nice things.",
        tags={"cantaloupe", "melon"},
    ),
    "golden_rumbler": MelonKind(
        id="golden_rumbler",
        label="cantaloupe",
        phrase="a golden cantaloupe with a rind netted like an old fishing rope",
        boast="as heavy as a sleepy bulldog",
        heft=3,
        growth="Every time someone gasped, the rind seemed to puff one stripe bigger.",
        tags={"cantaloupe", "melon"},
    ),
    "honey_band": MelonKind(
        id="honey_band",
        label="cantaloupe",
        phrase="a honey-sweet cantaloupe with pale bands glowing under the greenhouse glass",
        boast="as proud as a parade drum",
        heft=1,
        growth="It sat there shining as if it had swallowed a pocketful of sunrise.",
        tags={"cantaloupe", "melon"},
    ),
}

BOGS = {
    "peat_bog": BogKind(
        id="peat_bog",
        label="peat bog",
        phrase="the peat bog display where pitcher plants and moss liked to keep their toes wet",
        sogginess=2,
        image="The tray below it gleamed black and shiny, as if the floor itself had turned to soup.",
        warning="Roots can sip from damp soil, but they cannot paddle in a bog all day.",
        tags={"bog", "peat", "wet"},
    ),
    "rain_barrel_bog": BogKind(
        id="rain_barrel_bog",
        label="rain barrel bog",
        phrase="the rain-barrel bog corner beside the dripping water plants",
        sogginess=3,
        image="Water winked around the pot in little dark rings, the way a swamp winks around a log.",
        warning="A melon likes a drink, not a bathtub.",
        tags={"bog", "rain", "wet"},
    ),
    "moss_table": BogKind(
        id="moss_table",
        label="moss bog table",
        phrase="the mossy bog table where every saucer stayed damp as a sponge",
        sogginess=1,
        image="The pot sat in a greenish puddle soft enough to make even a trowel look sleepy.",
        warning="Too much wet makes roots lazy and heavy.",
        tags={"bog", "moss", "wet"},
    ),
}

STANDS = {
    "rolling_cart": StandKind(
        id="rolling_cart",
        label="rolling cart",
        phrase="a rolling cart with squeaky wheels",
        wobble=2,
        tags={"cart"},
    ),
    "cedar_bench": StandKind(
        id="cedar_bench",
        label="cedar bench",
        phrase="a cedar bench stacked with seed trays",
        wobble=1,
        tags={"bench"},
    ),
    "upside_pots": StandKind(
        id="upside_pots",
        label="stack of upside-down pots",
        phrase="a stack of upside-down pots pretending to be a display stand",
        wobble=3,
        tags={"pots"},
    ),
}

REMEDIES = {
    "hay_mound": RemedyKind(
        id="hay_mound",
        label="hay mound",
        phrase="a high hay mound over a dry wooden crate",
        drain_power=3,
        brace_power=3,
        sense=3,
        move_text="built a high hay mound over a slatted crate, lifted the vine onto it, and tucked the fruit so the wet could drain away",
        success_text="The crate drank off the extra water, and the hay held the round fruit like a soft throne.",
        fail_text="The hay helped some, but the roots had already soaked too long and the big fruit still sagged lower.",
        qa_text="moved the vine onto a high hay mound over a dry crate",
        tags={"drainage", "hay", "crate"},
    ),
    "gravel_rack": RemedyKind(
        id="gravel_rack",
        label="gravel rack",
        phrase="a gravel rack tied with jute and set above the puddles",
        drain_power=2,
        brace_power=2,
        sense=3,
        move_text="slid the pot onto a gravel rack, tied the vine with jute, and raised the fruit above the wet tray",
        success_text="The gravel let the water slip away, and the jute stopped the melon from lolling like a sleepy bell.",
        fail_text="The rack was sound, but the bog had already done too much soaking for such a heavy fruit.",
        qa_text="raised the vine on a gravel rack and tied it with jute",
        tags={"drainage", "gravel", "jute"},
    ),
    "plank_bridge": RemedyKind(
        id="plank_bridge",
        label="plank bridge",
        phrase="a little plank bridge with straw under the fruit",
        drain_power=1,
        brace_power=2,
        sense=2,
        move_text="laid a plank bridge across two tubs and slid straw under the melon so it would not sit in the wet",
        success_text="The plank lifted the weight and the straw kept the rind out of the boggy puddle.",
        fail_text="The plank held the melon up, but not enough water drained from the roots to cheer it.",
        qa_text="set the melon on a plank bridge with straw under it",
        tags={"support", "straw"},
    ),
    "ribbon_bow": RemedyKind(
        id="ribbon_bow",
        label="ribbon bow",
        phrase="a shiny ribbon bow tied around the stem",
        drain_power=0,
        brace_power=0,
        sense=1,
        move_text="tied a shiny ribbon around the stem and hoped prettiness would do the work of roots and wood",
        success_text="For one blink the vine looked grand, but grand is not the same as dry.",
        fail_text="The bow was pretty as a parade, but it could not drain a bog or hold a giant cantaloupe steady.",
        qa_text="tied a ribbon around the stem",
        tags={"decoration"},
    ),
}

HERO_NAMES = {
    "girl": ["Della", "Mabel", "June", "Tess", "Pearl", "Nell"],
    "boy": ["Eli", "Hank", "Otis", "Beau", "Cal", "Wade"],
}

HELPERS = [
    {"name": "Miss Tilly", "type": "clerk_f"},
    {"name": "Mr. Reed", "type": "clerk_m"},
    {"name": "Aunt May", "type": "aunt"},
    {"name": "Uncle Dorsey", "type": "uncle"},
]

CONTESTS = {
    "porch_pride": "the Porch Pride Produce Parade",
    "county_boast": "the County Boast-and-Brag Weigh-In",
    "melon_day": "the Saturday Melon Day Show",
}

KNOWLEDGE = {
    "cantaloupe": [
        (
            "What is a cantaloupe?",
            "A cantaloupe is a round melon with sweet orange fruit inside. It grows on a vine and needs sun, room, and careful watering.",
        )
    ],
    "bog": [
        (
            "What is a bog?",
            "A bog is very wet ground where water stays for a long time. Some plants love boggy soil, but many garden plants do not.",
        )
    ],
    "wet": [
        (
            "Why can too much water hurt a plant?",
            "Plants need water, but roots also need air in the soil. If the soil stays too wet, the roots can struggle and the plant can droop.",
        )
    ],
    "drainage": [
        (
            "What does drainage mean for a plant?",
            "Drainage means extra water can move away instead of sitting around the roots. Good drainage helps roots stay healthy.",
        )
    ],
    "crate": [
        (
            "Why would a gardener raise a plant on a crate or rack?",
            "Raising a plant helps water drain away and keeps heavy fruit from sitting in a puddle. It can also give the vine better support.",
        )
    ],
    "hay": [
        (
            "Why might hay or straw go under a melon?",
            "Hay or straw can keep the fruit up off wet ground. That helps it stay cleaner and drier.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened before. It helps explain why a character remembers what to do now.",
        )
    ],
}


def risk_score(melon: MelonKind, bog: BogKind, stand: StandKind) -> int:
    return melon.heft + bog.sogginess + stand.wobble


def remedy_works(melon: MelonKind, bog: BogKind, stand: StandKind, remedy: RemedyKind) -> bool:
    needs_brace = melon.heft + stand.wobble
    return remedy.drain_power >= bog.sogginess and remedy.brace_power >= needs_brace - 1


def sensible_remedies() -> list[RemedyKind]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for melon_id, melon in MELONS.items():
        for bog_id, bog in BOGS.items():
            for stand_id, stand in STANDS.items():
                for remedy_id, remedy in REMEDIES.items():
                    if remedy.sense >= SENSE_MIN and remedy_works(melon, bog, stand, remedy):
                        combos.append((melon_id, bog_id, stand_id, remedy_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    melon = MELONS[params.melon]
    bog = BOGS[params.bog]
    stand = STANDS[params.stand]
    remedy = REMEDIES[params.remedy]
    severity = risk_score(melon, bog, stand) + params.delay
    power = remedy.drain_power + remedy.brace_power
    return "saved" if power >= severity else "slumped"


def explain_rejection(melon: MelonKind, bog: BogKind, stand: StandKind, remedy: RemedyKind) -> str:
    if remedy.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_remedies()))
        return (
            f"(Refusing remedy '{remedy.id}': it is too flimsy and fanciful for a real garden fix. "
            f"Try one of these instead: {better}.)"
        )
    return (
        f"(No story: {remedy.phrase} does not honestly handle a {melon.label} this heavy on "
        f"{stand.phrase} in {bog.label} conditions. The fix must drain the bogginess and brace the fruit.)"
    )


def predict_slump(world: World) -> dict:
    sim = world.copy()
    melon = sim.get("melon")
    melon.meters["waterlogged"] += 1
    propagate(sim, narrate=False)
    return {
        "droops": melon.meters["droop"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"] + sim.get("helper").memes["worry"],
    }


def introduce(world: World, hero: Entity, helper: Entity, melon_cfg: MelonKind, contest_name: str) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"At the garden center, {hero.id} stopped so suddenly by the melon tables that a row of seed packets nearly saluted. "
        f"There, under the glass roof, sat {melon_cfg.phrase}, marked for {contest_name}."
    )
    world.say(
        f'"Land alive," said {hero.id}, "that cantaloupe is {melon_cfg.boast}!" '
        f"And in the hot, happy air of the place, that did not sound one bit too big."
    )
    world.say(
        f"{helper.id}, the {helper.label_word}, laughed and tipped {helper.pronoun('possessive')} hat. "
        f"{melon_cfg.growth}"
    )


def show_bog(world: World, bog: BogKind, stand: StandKind) -> None:
    melon = world.get("melon")
    melon.attrs["bog_label"] = bog.label
    world.say(
        f"But someone had left the vine on {stand.phrase} beside {bog.phrase}. {bog.image}"
    )


def warning(world: World, helper: Entity, bog: BogKind, stand: StandKind) -> None:
    pred = predict_slump(world)
    helper.memes["concern"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} bent close to the pot and gave a low whistle. "{bog.warning} '
        f"On {stand.label} like this, a big fruit can start to sag before a person can count to ten fence posts.\""
    )


def trouble(world: World, hero: Entity, helper: Entity) -> None:
    melon = world.get("melon")
    melon.meters["waterlogged"] += 1
    propagate(world, narrate=False)
    world.say(
        "Sure enough, the vine drooped at the middle, and the great striped ball gave one slow, worried sink."
    )
    world.say(
        f"{hero.id} clapped both hands to {hero.pronoun('possessive')} cheeks. "
        f'"Don\'t let it sink into the bog," {hero.pronoun()} cried.'
    )
    world.say(
        f"{helper.id} steadied the stem with both hands, for even a tall tale needs somebody sensible in it."
    )


def flashback(world: World, helper: Entity, melon_cfg: MelonKind) -> None:
    helper.memes["remember"] += 1
    world.facts["flashback_used"] = True
    world.say(
        f"Then a memory came back to {helper.id} bright as a lantern in a shed."
    )
    world.say(
        f"Years before, at a county fair, {helper.pronoun()} had seen an old grower lift a champion {melon_cfg.label} onto a dry hill of straw and slats. "
        f'"A giant melon," the old grower had said, "must never sit down in a bog unless you aim to raise melon soup."'
    )


def apply_remedy(world: World, hero: Entity, helper: Entity, remedy: RemedyKind) -> None:
    melon = world.get("melon")
    hero.memes["helpfulness"] += 1
    helper.memes["purpose"] += 1
    melon.meters["drained"] += remedy.drain_power
    melon.meters["braced"] += remedy.brace_power
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} fetched twine and {helper.id} {remedy.move_text}."
    )


def saved_ending(world: World, hero: Entity, helper: Entity, remedy: RemedyKind, contest_name: str) -> None:
    melon = world.get("melon")
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    melon.meters["gleam"] += 1
    world.say(remedy.success_text)
    world.say(
        f"The vine lifted again, as if the cantaloupe had remembered it was supposed to act grand in public."
    )
    world.say(
        f'By closing time, shoppers swore the saved cantaloupe looked big enough to need its own wheelbarrow ticket for {contest_name}. '
        f"{hero.id} walked past it slow and proud, while the melon sat high and dry like a green king on a hay throne."
    )


def slumped_ending(world: World, hero: Entity, helper: Entity, remedy: RemedyKind) -> None:
    melon = world.get("melon")
    hero.memes["sadness"] += 1
    helper.memes["resolve"] += 1
    melon.meters["scar"] += 1
    world.say(remedy.fail_text)
    world.say(
        "The giant fruit did not burst or roll away, but it slumped deep enough to prove that waiting is a poor helper in any greenhouse."
    )
    world.say(
        f"{helper.id} patted {hero.id}'s shoulder and promised they would start the next vine high and dry from the very first day. "
        f"In the evening light, the old cantaloupe rested quiet above the boggy table, and the lesson stood taller than the fruit."
    )


def tell(
    melon_cfg: MelonKind,
    bog: BogKind,
    stand: StandKind,
    remedy: RemedyKind,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_type: str,
    contest_name: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, phrase=helper_name, role="helper"))
    melon = world.add(Entity(id="melon", kind="thing", type="melon", label=melon_cfg.label, phrase=melon_cfg.phrase, role="melon"))
    stand_ent = world.add(Entity(id="stand", kind="thing", type="stand", label=stand.label, phrase=stand.phrase))
    bog_ent = world.add(Entity(id="bog", kind="thing", type="bog", label=bog.label, phrase=bog.phrase))
    world.add(Entity(id="place", kind="thing", type="garden_center", label="garden center", phrase="the garden center"))

    melon.meters["heft"] = float(melon_cfg.heft)
    stand_ent.meters["wobble"] = float(stand.wobble)
    bog_ent.meters["sogginess"] = float(bog.sogginess)

    introduce(world, hero, helper, melon_cfg, contest_name)
    show_bog(world, bog, stand)

    world.para()
    warning(world, helper, bog, stand)
    trouble(world, hero, helper)

    world.para()
    flashback(world, helper, melon_cfg)

    if delay > 0:
        melon.meters["droop"] += float(delay)
        hero.memes["worry"] += float(delay)
        helper.memes["worry"] += float(delay)
        world.say(
            f"But in a busy garden center, even one little delay can feel as long as a summer railroad. "
            f"For {delay} slow spell{'s' if delay != 1 else ''}, they had to dodge customers, hose carts, and a lady hunting purple petunias."
        )

    apply_remedy(world, hero, helper, remedy)

    world.para()
    outcome = "saved" if outcome_of(
        StoryParams(
            melon=melon_cfg.id,
            bog=bog.id,
            stand=stand.id,
            remedy=remedy.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            helper_name=helper_name,
            helper_type=helper_type,
            contest=next(k for k, v in CONTESTS.items() if v == contest_name),
            delay=delay,
        )
    ) == "saved" else "slumped"

    if outcome == "saved":
        saved_ending(world, hero, helper, remedy, contest_name)
    else:
        slumped_ending(world, hero, helper, remedy)

    world.facts.update(
        hero=hero,
        helper=helper,
        melon_cfg=melon_cfg,
        bog_cfg=bog,
        stand_cfg=stand,
        remedy_cfg=remedy,
        contest_name=contest_name,
        delay=delay,
        outcome=outcome,
        flashback_used=world.facts.get("flashback_used", False),
        melon_saved=outcome == "saved",
        severe_risk=risk_score(melon_cfg, bog, stand),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    melon = f["melon_cfg"]
    bog = f["bog_cfg"]
    remedy = f["remedy_cfg"]
    contest_name = f["contest_name"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old set in a garden center that includes the words "cantaloupe" and "bog" and uses a flashback.',
            f"Tell a playful story where {hero.label} and {helper.label} save a giant {melon.label} from {bog.label} trouble by remembering an old gardening lesson.",
            f"Write a story about a brag-sized melon meant for {contest_name}, where a flashback leads to {remedy.label} and a happy ending.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old set in a garden center that includes the words "cantaloupe" and "bog" and uses a flashback.',
        f"Tell a cautionary tall tale where {hero.label} and {helper.label} try to rescue a giant {melon.label} from {bog.label} trouble, but they act too late.",
        "Write a story where an old memory gives good advice, yet delay still matters when a plant has been sitting too wet.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    melon = f["melon_cfg"]
    bog = f["bog_cfg"]
    stand = f["stand_cfg"]
    remedy = f["remedy_cfg"]
    contest_name = f["contest_name"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child at a garden center, and {helper.label}, the clerk who helps with the giant cantaloupe. Together they notice that the melon is in trouble.",
        ),
        (
            "What was special about the cantaloupe?",
            f"It was an enormous cantaloupe meant for {contest_name}. The story treats it like a tall-tale melon, big enough to make everyone stare.",
        ),
        (
            "Why was the melon in danger?",
            f"The vine had been left on {stand.phrase} beside {bog.phrase}. That boggy wetness could soak the roots, and the heavy fruit began to droop.",
        ),
        (
            "What was the flashback about?",
            f"{helper.label} remembered an old grower at a fair saying a giant melon should never sit down in a bog. That memory gave them the idea to lift the fruit high and dry.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they save the cantaloupe?",
                f"They {remedy.qa_text}. That worked because the fix both drained the wet and supported the heavy fruit.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the cantaloupe sitting high and dry again. By closing time it looked ready to show off at {contest_name}.",
            )
        )
    else:
        qa.append(
            (
                "Why did the rescue fail?",
                f"They used a sensible idea, but the vine had sat in the bog too long before the work was done. The roots were already too soaked, so the fruit still slumped.",
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that a good fix works best when you do it quickly. The flashback gave the right advice, but delay let the bog trouble grow bigger.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"cantaloupe", "bog", "wet", "flashback"}
    remedy = f["remedy_cfg"]
    if "drainage" in remedy.tags:
        tags.add("drainage")
    if "crate" in remedy.tags:
        tags.add("crate")
    if "hay" in remedy.tags or "straw" in remedy.tags:
        tags.add("hay")
    order = ["cantaloupe", "bog", "wet", "drainage", "crate", "hay", "flashback"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        melon="striped_giant",
        bog="peat_bog",
        stand="cedar_bench",
        remedy="hay_mound",
        hero_name="Della",
        hero_gender="girl",
        helper_name="Miss Tilly",
        helper_type="clerk_f",
        contest="porch_pride",
        delay=0,
    ),
    StoryParams(
        melon="golden_rumbler",
        bog="moss_table",
        stand="rolling_cart",
        remedy="gravel_rack",
        hero_name="Hank",
        hero_gender="boy",
        helper_name="Mr. Reed",
        helper_type="clerk_m",
        contest="county_boast",
        delay=0,
    ),
    StoryParams(
        melon="golden_rumbler",
        bog="rain_barrel_bog",
        stand="upside_pots",
        remedy="hay_mound",
        hero_name="Pearl",
        hero_gender="girl",
        helper_name="Aunt May",
        helper_type="aunt",
        contest="melon_day",
        delay=2,
    ),
    StoryParams(
        melon="honey_band",
        bog="peat_bog",
        stand="rolling_cart",
        remedy="plank_bridge",
        hero_name="Cal",
        hero_gender="boy",
        helper_name="Uncle Dorsey",
        helper_type="uncle",
        contest="porch_pride",
        delay=0,
    ),
]


ASP_RULES = r"""
valid(M, B, S, R) :-
    melon(M), bog(B), stand(S), remedy(R),
    sense(R, Se), sense_min(Min), Se >= Min,
    sogginess(B, Bg), drain_power(R, D), D >= Bg,
    heft(M, H), wobble(S, W), brace_power(R, Br), Br >= H + W - 1.

severity(V) :-
    chosen_melon(M), chosen_bog(B), chosen_stand(S), delay(D),
    heft(M, H), sogginess(B, Bg), wobble(S, W),
    V = H + Bg + W + D.

power(P) :-
    chosen_remedy(R), drain_power(R, D), brace_power(R, B), P = D + B.

outcome(saved) :- power(P), severity(V), P >= V.
outcome(slumped) :- power(P), severity(V), P < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for melon_id, melon in MELONS.items():
        lines.append(asp.fact("melon", melon_id))
        lines.append(asp.fact("heft", melon_id, melon.heft))
    for bog_id, bog in BOGS.items():
        lines.append(asp.fact("bog", bog_id))
        lines.append(asp.fact("sogginess", bog_id, bog.sogginess))
    for stand_id, stand in STANDS.items():
        lines.append(asp.fact("stand", stand_id))
        lines.append(asp.fact("wobble", stand_id, stand.wobble))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("drain_power", remedy_id, remedy.drain_power))
        lines.append(asp.fact("brace_power", remedy_id, remedy.brace_power))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
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

    extra = "\n".join(
        [
            asp.fact("chosen_melon", params.melon),
            asp.fact("chosen_bog", params.bog),
            asp.fact("chosen_stand", params.stand),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test_generation() -> None:
    args = build_parser().parse_args([])
    params = resolve_params(args, random.Random(123))
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    with io.StringIO() as buf, redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
        text = buf.getvalue()
    if "cantaloupe" not in sample.story.lower() or "bog" not in sample.story.lower():
        raise StoryError("Smoke test failed: seed words missing from story.")
    if "flashback" in text.lower():
        pass


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        py_outcome = outcome_of(params)
        asp_ans = asp_outcome(params)
        if py_outcome != asp_ans:
            mismatches.append((params, py_outcome, asp_ans))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")
        for params, py_outcome, asp_ans in mismatches[:5]:
            print(" ", params, py_outcome, asp_ans)

    try:
        smoke_test_generation()
        print("OK: smoke test generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant cantaloupe, bog trouble, and a remembered fix at a garden center."
    )
    ap.add_argument("--melon", choices=sorted(MELONS))
    ap.add_argument("--bog", choices=sorted(BOGS))
    ap.add_argument("--stand", choices=sorted(STANDS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["clerk_f", "clerk_m", "aunt", "uncle"])
    ap.add_argument("--contest", choices=sorted(CONTESTS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the rescue is delayed")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_helper(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    if args.helper_name and not args.helper_type:
        matches = [h for h in HELPERS if h["name"] == args.helper_name]
        if not matches:
            raise StoryError("(Unknown helper name. Try one of the built-in helper names.)")
        return matches[0]["name"], matches[0]["type"]
    if args.helper_type and not args.helper_name:
        matches = [h for h in HELPERS if h["type"] == args.helper_type]
        pick = rng.choice(matches)
        return pick["name"], pick["type"]
    if args.helper_type and args.helper_name:
        matches = [h for h in HELPERS if h["name"] == args.helper_name and h["type"] == args.helper_type]
        if not matches:
            raise StoryError("(Helper name and helper type do not match.)")
        return args.helper_name, args.helper_type
    pick = rng.choice(HELPERS)
    return pick["name"], pick["type"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_rejection(MELONS[next(iter(MELONS))], BOGS[next(iter(BOGS))], STANDS[next(iter(STANDS))], REMEDIES[args.remedy]))

    if args.melon and args.bog and args.stand and args.remedy:
        melon = MELONS[args.melon]
        bog = BOGS[args.bog]
        stand = STANDS[args.stand]
        remedy = REMEDIES[args.remedy]
        if not remedy_works(melon, bog, stand, remedy) or remedy.sense < SENSE_MIN:
            raise StoryError(explain_rejection(melon, bog, stand, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.melon is None or combo[0] == args.melon)
        and (args.bog is None or combo[1] == args.bog)
        and (args.stand is None or combo[2] == args.stand)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    melon_id, bog_id, stand_id, remedy_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[hero_gender])
    helper_name, helper_type = resolve_helper(args, rng)
    contest = args.contest or rng.choice(sorted(CONTESTS))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        melon=melon_id,
        bog=bog_id,
        stand=stand_id,
        remedy=remedy_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        contest=contest,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        melon = MELONS[params.melon]
        bog = BOGS[params.bog]
        stand = STANDS[params.stand]
        remedy = REMEDIES[params.remedy]
        contest_name = CONTESTS[params.contest]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err})") from err

    if remedy.sense < SENSE_MIN or not remedy_works(melon, bog, stand, remedy):
        raise StoryError(explain_rejection(melon, bog, stand, remedy))

    world = tell(
        melon_cfg=melon,
        bog=bog,
        stand=stand,
        remedy=remedy,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        contest_name=contest_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (melon, bog, stand, remedy) combos:\n")
        for melon, bog, stand, remedy in combos:
            print(f"  {melon:15} {bog:16} {stand:12} {remedy}")
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
            header = f"### {p.hero_name}: {p.melon} in {p.bog} trouble ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
