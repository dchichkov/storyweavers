#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py
=================================================================================

A standalone storyworld for a gentle cautionary magic animal story.

Premise
-------
A young animal receives an expensive wearable item, then longs to try a small
weather charm. A grown-up warns that using the charm carelessly could spoil the
item and make the child shiver. Depending on temperament, the child either uses
protective gear and learns the safe way, or makes a rash choice, gets cold, and
learns the lesson after a magical rescue.

Run it
------
python storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py
python storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py --spell frost_spark --prize velvet_hat
python storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py --temperament rash
python storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py --all
python storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py --qa --json
python storyworlds/worlds/gpt-5.4/rash_expensive_shiver_cautionary_magic_animal_story.py --verify
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
SAFE_TEMPERAMENTS = {"careful", "patient", "gentle"}
REGIONS = {"head", "torso", "feet"}


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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "doe", "hen", "female"}
        male = {"boy", "father", "uncle", "buck", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    label: str
    practice: str
    cast_line: str
    effect_line: str
    mess: str
    chill: int
    zone: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    spoil_text: str
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
        return any(
            g.protective and region in g.covers and mess in g.attrs.get("guards", set())
            for g in self.worn_items(actor)
        )

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spoil_item(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    spell = world.facts.get("spell")
    if not isinstance(hero, Entity) or spell is None:
        return out
    for item in world.worn_items(hero):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(hero, item.region, spell.mess):
            continue
        sig = ("spoil", item.id, spell.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["spoiled"] += 1
        item.meters[spell.mess] += 1
        hero.memes["worry"] += 1
        out.append("__spoil__")
    return out


def _r_shiver(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not isinstance(hero, Entity):
        return out
    if hero.meters["cold"] < THRESHOLD:
        return out
    sig = ("shiver", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["shiver"] += 1
    hero.memes["fear"] += 1
    out.append("__shiver__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spoil_item", tag="physical", apply=_r_spoil_item),
    Rule(name="shiver", tag="physical", apply=_r_shiver),
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


def prize_at_risk(spell: Spell, prize: Prize) -> bool:
    return prize.region in spell.zone


def select_gear(spell: Spell, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if spell.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def is_rash(temperament: str) -> bool:
    return temperament == "rash"


def predict_risk(world: World, hero: Entity, spell: Spell, prize_id: str) -> dict:
    sim = world.copy()
    sim.facts["hero"] = sim.get(hero.id)
    sim.facts["spell"] = spell
    _do_spell(sim, sim.get(hero.id), spell, narrate=False)
    prize = sim.get(prize_id)
    return {
        "spoiled": prize.meters["spoiled"] >= THRESHOLD,
        "shiver": sim.get(hero.id).meters["shiver"] >= THRESHOLD,
    }


def _do_spell(world: World, hero: Entity, spell: Spell, narrate: bool = True) -> None:
    world.zone = set(spell.zone)
    hero.meters[spell.mess] += 1
    hero.meters["cold"] += float(spell.chill)
    hero.memes["wonder"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, guardian: Entity, prize: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {world.setting.detail} {hero.id}, a small {hero.type}, "
        f"had just been given {prize.phrase}."
    )
    world.say(
        f"It was expensive enough that {hero.pronoun('possessive')} {guardian.label_word} had saved up berry coins for it, "
        f"and {hero.id} wore {prize.it()} as proudly as a prince in a picture book."
    )


def desire_magic(world: World, hero: Entity, spell: Spell) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"That evening, the air felt full of secrets. {hero.id} wanted to {spell.practice}, "
        f"because the little charm promised a bit of real magic."
    )


def warning(world: World, guardian: Entity, hero: Entity, spell: Spell, prize: Entity) -> None:
    pred = predict_risk(world, hero, spell, prize.id)
    world.facts["predicted_spoiled"] = pred["spoiled"]
    world.facts["predicted_shiver"] = pred["shiver"]
    world.say(
        f'"Not while you are wearing {prize.phrase}," said {hero.pronoun("possessive")} {guardian.label_word}. '
        f'"If you try that charm now, {prize.it()} could be spoiled, and you may shiver before the moon is up."'
    )


def offer_safe_way(world: World, guardian: Entity, hero: Entity, spell: Spell, prize: Entity, gear: Gear) -> None:
    world.say(
        f'{guardian.label_word.capitalize()} looked at the sky, then at the magic charm, and smiled. '
        f'"We can still have magic," {guardian.pronoun()} said. "First we will {gear.prep}, and then you may {spell.practice}."'
    )


def accept_safe_way(world: World, guardian: Entity, hero: Entity, spell: Spell, prize: Entity, gear: Gear) -> None:
    gear_ent = world.add(
        Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            phrase=gear.phrase,
            owner=hero.id,
            caretaker=guardian.id,
            worn_by=hero.id,
            protective=True,
            covers=set(gear.covers),
            attrs={"guards": set(gear.guards)},
            plural=gear.plural,
        )
    )
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} was not pleased to wait, but {hero.pronoun()} listened. Soon {gear_ent.phrase} was in place, "
        f"and the expensive {prize.label} stayed safe."
    )
    world.say(
        f"They {gear.tail}. When {hero.id} at last used the charm, {spell.effect_line} "
        f"{hero.pronoun().capitalize()} laughed, and not even one thread of {prize.label} was harmed."
    )


def defy(world: World, hero: Entity, guardian: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the wish to try it right away tugged too hard. " 
        f'"Just one little spell," said {hero.id}, making a rash choice before {guardian.label_word} could stop {hero.pronoun("object")}.'
    )


def mishap(world: World, hero: Entity, spell: Spell, prize: Entity) -> None:
    _do_spell(world, hero, spell, narrate=False)
    spoiled = prize.meters["spoiled"] >= THRESHOLD
    shiver = hero.meters["shiver"] >= THRESHOLD
    world.say(spell.cast_line)
    if spoiled:
        world.say(
            f"{spell.effect_line} At once, {prize.phrase} was {prize.attrs.get('spoil_text', prize.label)}."
        )
    if shiver:
        world.say(
            f"The magic felt pretty for one blink, and then it bit with cold. {hero.id} began to shiver."
        )


def rescue(world: World, guardian: Entity, hero: Entity, prize: Entity) -> None:
    hero.meters["cold"] = 0.0
    hero.meters["shiver"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} hurried over, wrapped {hero.pronoun('object')} in a warm blanket charm, "
        f"and carried {hero.pronoun('object')} indoors by the stove."
    )
    world.say(
        f'"Magic is not bad," {guardian.pronoun()} said softly, "but it must not be used in a rash way. '
        f'An expensive thing is worth protecting, and so are you."'
    )
    if prize.meters["spoiled"] >= THRESHOLD:
        world.say(
            f"{hero.id} looked sadly at the {prize.label}. The sight of it helped the lesson settle deep."
        )


def better_tomorrow(world: World, guardian: Entity, hero: Entity, spell: Spell, gear: Gear) -> None:
    world.say(
        f"The next day, {guardian.label_word} set the charm on the table again beside {gear.phrase}. "
        f'"Now we do it the careful way," {guardian.pronoun()} said.'
    )
    world.say(
        f"{hero.id} nodded. This time there was no grabbing, no hurry, and no shiver at all."
    )
    world.say(
        f"Soon the magic danced in the safe little space, and {hero.id} watched with bright eyes, wiser than before."
    )


SETTINGS = {
    "mossy_glen": Setting(
        id="mossy_glen",
        place="the Mossy Glen",
        detail="where fern tips leaned over a round burrow door,",
        affords={"frost_spark", "rain_ribbon", "wind_whirl"},
    ),
    "willow_hollow": Setting(
        id="willow_hollow",
        place="Willow Hollow",
        detail="where lantern bugs glowed under the roots,",
        affords={"frost_spark", "rain_ribbon", "wind_whirl"},
    ),
    "thimble_meadow": Setting(
        id="thimble_meadow",
        place="Thimble Meadow",
        detail="where clover heads bobbed beside a stone path,",
        affords={"frost_spark", "rain_ribbon", "wind_whirl"},
    ),
}

SPELLS = {
    "frost_spark": Spell(
        id="frost_spark",
        label="frost spark",
        practice="whisper the frost-spark charm over the stepping stones",
        cast_line='Tiny silver stars spun from the charm and drifted in a ring around the stones.',
        effect_line="The air turned white and crisp, and cold glitter dust settled everywhere.",
        mess="frosted",
        chill=2,
        zone={"head", "torso"},
        tags={"magic", "cold", "frost"},
    ),
    "rain_ribbon": Spell(
        id="rain_ribbon",
        label="rain ribbon",
        practice="twirl the rain-ribbon charm in the yard",
        cast_line='A blue ribbon of rain curled out of the charm and looped through the air like a skipping rope.',
        effect_line="Drops pattered down in a cheerful circle, splashing anything beneath them.",
        mess="wet",
        chill=1,
        zone={"torso", "feet"},
        tags={"magic", "rain", "cold"},
    ),
    "wind_whirl": Spell(
        id="wind_whirl",
        label="wind whirl",
        practice="tap the wind-whirl pebble by the hill",
        cast_line='The pebble hummed, and a spinning breeze jumped up as if it had tiny feet.',
        effect_line="The gust tugged and twirled at everything nearby with chilly little fingers.",
        mess="ruffled",
        chill=1,
        zone={"head", "torso"},
        tags={"magic", "wind", "cold"},
    ),
}

PRIZES = {
    "velvet_hat": Prize(
        id="velvet_hat",
        label="velvet hat",
        phrase="an expensive velvet hat with a silver acorn clasp",
        type="hat",
        region="head",
        spoil_text="damp, droopy, and no longer grand",
        tags={"hat", "expensive"},
    ),
    "silk_cape": Prize(
        id="silk_cape",
        label="silk cape",
        phrase="an expensive silk cape stitched with moon-thread",
        type="cape",
        region="torso",
        spoil_text="spotted, limp, and sadly clinging to its hem",
        tags={"cape", "expensive"},
    ),
    "satin_boots": Prize(
        id="satin_boots",
        label="satin boots",
        phrase="a pair of expensive satin boots with pearl buttons",
        type="boots",
        region="feet",
        spoil_text="splashed and sagging at the toes",
        plural=True,
        tags={"boots", "expensive"},
    ),
}

GEAR = {
    "earmuffs": Gear(
        id="earmuffs",
        label="earmuffs",
        phrase="soft wool earmuffs",
        covers={"head"},
        guards={"frosted", "ruffled"},
        prep="pull on your wool earmuffs",
        tail="fetched the earmuffs and stepped to the dry porch",
        plural=True,
        tags={"warmth"},
    ),
    "rain_cloak": Gear(
        id="rain_cloak",
        label="rain cloak",
        phrase="a waxed rain cloak",
        covers={"torso"},
        guards={"wet", "frosted", "ruffled"},
        prep="fasten your rain cloak",
        tail="fastened the rain cloak and went to the little porch",
        tags={"warmth", "raincoat"},
    ),
    "galoshes": Gear(
        id="galoshes",
        label="galoshes",
        phrase="sturdy little galoshes",
        covers={"feet"},
        guards={"wet"},
        prep="pull on your galoshes",
        tail="found the galoshes and hopped to the stepping stones",
        plural=True,
        tags={"boots"},
    ),
    "winter_wrap": Gear(
        id="winter_wrap",
        label="winter wrap",
        phrase="a soft winter wrap with a hood",
        covers={"head", "torso"},
        guards={"frosted", "wet", "ruffled"},
        prep="put on your winter wrap",
        tail="put on the winter wrap and chose a dry patch by the door",
        tags={"warmth"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    spell: str
    prize: str
    gear: str
    hero_name: str
    hero_species: str
    guardian_type: str
    temperament: str
    seed: Optional[int] = None


def tell(
    setting: Setting,
    spell: Spell,
    prize_cfg: Prize,
    gear_cfg: Gear,
    hero_name: str = "Pip",
    hero_species: str = "rabbit",
    guardian_type: str = "mother",
    temperament: str = "careful",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_species,
            label=hero_name,
            traits=[temperament, "small"],
        )
    )
    guardian = world.add(
        Entity(
            id="Guardian",
            kind="character",
            type=guardian_type,
            label="the guardian",
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=guardian.id,
            worn_by=hero.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
            tags=set(prize_cfg.tags),
            attrs={"spoil_text": prize_cfg.spoil_text},
        )
    )

    world.facts.update(
        hero=hero,
        guardian=guardian,
        spell=spell,
        prize=prize,
        prize_cfg=prize_cfg,
        gear=gear_cfg,
        setting=setting,
        temperament=temperament,
    )

    introduce(world, hero, guardian, prize)
    desire_magic(world, hero, spell)

    world.para()
    warning(world, guardian, hero, spell, prize)

    safe = not is_rash(temperament)
    if safe:
        offer_safe_way(world, guardian, hero, spell, prize, gear_cfg)
        world.para()
        accept_safe_way(world, guardian, hero, spell, prize, gear_cfg)
        outcome = "safe"
    else:
        defy(world, hero, guardian)
        world.para()
        mishap(world, hero, spell, prize)
        world.para()
        rescue(world, guardian, hero, prize)
        world.para()
        better_tomorrow(world, guardian, hero, spell, gear_cfg)
        outcome = "lesson"

    world.facts.update(
        outcome=outcome,
        spoiled=prize.meters["spoiled"] >= THRESHOLD,
        shivered=hero.meters["shiver"] >= THRESHOLD,
        safe=safe,
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for spell_id in sorted(setting.affords):
            spell = SPELLS[spell_id]
            for prize_id, prize in PRIZES.items():
                if not prize_at_risk(spell, prize):
                    continue
                gear = select_gear(spell, prize)
                if gear is None:
                    continue
                combos.append((setting_id, spell_id, prize_id, gear.id))
    return combos


KNOWLEDGE = {
    "magic": [
        (
            "What is a charm in a magic story?",
            "A charm is a small magical word or object that makes something happen. In stories, it should be used carefully and with help from a wise grown-up."
        )
    ],
    "cold": [
        (
            "Why do you shiver when you get too cold?",
            "Your body shivers to help warm you up. The tiny shakes are your muscles working to make heat."
        )
    ],
    "frost": [
        (
            "What is frost?",
            "Frost is a thin layer of ice that forms when things get very cold. It can make cloth stiff and chilly."
        )
    ],
    "rain": [
        (
            "Why can rain ruin fancy clothes?",
            "Rain can soak cloth and leave it heavy, wrinkled, or stained. Fine clothes need extra care so they stay nice."
        )
    ],
    "wind": [
        (
            "How can wind bother a hat or cape?",
            "Wind can tug at light things, twist them, and flap them around. That can make them messy or hard to wear."
        )
    ],
    "expensive": [
        (
            "What does expensive mean?",
            "Expensive means something costs a lot and is hard to replace. That is why people try to keep expensive things safe."
        )
    ],
    "warmth": [
        (
            "Why do warm clothes help in cold weather?",
            "Warm clothes trap your body heat close to you. That helps stop the cold air from stealing it away."
        )
    ],
    "raincoat": [
        (
            "What does a rain cloak do?",
            "A rain cloak covers your body and helps keep water off. It is useful when rain or spray might soak your clothes."
        )
    ],
    "boots": [
        (
            "Why are galoshes good in wet places?",
            "Galoshes are waterproof boots. They help keep feet dry when the ground is splashy."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "expensive", "cold", "frost", "rain", "wind", "warmth", "raincoat", "boots"]

GIRL_NAMES = ["Poppy", "Mira", "Tansy", "Luna", "Hazel"]
BOY_NAMES = ["Pip", "Nibb", "Rowan", "Bram", "Ollie"]
SPECIES = ["rabbit", "fox", "mouse", "squirrel"]
TEMPERAMENTS = ["careful", "patient", "gentle", "rash"]
GUARDIANS = ["mother", "father", "aunt", "uncle"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    spell = world.facts["spell"]
    prize_cfg = world.facts["prize_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "lesson":
        return [
            f'Write a cautionary magic animal story for ages 3 to 5 that includes the words "rash", "expensive", and "shiver".',
            f"Tell a story about a young {hero.type} who uses a {spell.label} too quickly while wearing {prize_cfg.phrase}, gets cold, and learns to be careful.",
            "Write a gentle animal story where magic is beautiful but must be used wisely, and the ending shows the child changed."
        ]
    return [
        f'Write a magic animal story for ages 3 to 5 that includes the words "rash", "expensive", and "shiver".',
        f"Tell a story about a young {hero.type} who wants to try a {spell.label} but listens to a grown-up and keeps {prize_cfg.label} safe.",
        "Write a child-facing story where a careful choice lets a magical game stay fun without anyone getting cold or ruining something precious."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    spell = world.facts["spell"]
    prize = world.facts["prize"]
    gear = world.facts["gear"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type}, and {hero.pronoun('possessive')} {guardian.label_word}. The story follows a magical choice that had to be made carefully."
        ),
        (
            f"What did {hero.id} want to do?",
            f"{hero.id} wanted to {spell.practice}. The charm looked beautiful and tempting, so it was hard to wait."
        ),
        (
            f"Why did {hero.id}'s {guardian.label_word} warn {hero.pronoun('object')}?",
            f"{guardian.label_word.capitalize()} warned {hero.pronoun('object')} because the spell could spoil the expensive {prize.label} and make {hero.pronoun('object')} cold enough to shiver. The warning came from the danger in the charm, not from meanness."
        ),
    ]
    if outcome == "lesson":
        qa.extend(
            [
                (
                    f"What happened when {hero.id} made the rash choice?",
                    f"{hero.id} used the charm too soon, and the magic touched the {prize.label}. Then the cold made {hero.pronoun('object')} shiver, which showed the warning had been true."
                ),
                (
                    f"How did {hero.id}'s {guardian.label_word} help?",
                    f"{guardian.label_word.capitalize()} wrapped {hero.pronoun('object')} in warmth and took {hero.pronoun('object')} inside. After that, {guardian.pronoun()} explained that magic must be used carefully and not in a rash way."
                ),
                (
                    "How did the story end?",
                    f"The next day, {hero.id} tried the magic again the safe way with {gear.phrase}. The ending image shows a wiser child enjoying magic without a shiver."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"How did they solve the problem?",
                    f"They used {gear.phrase} first and only then tried the charm. The gear protected the expensive {prize.label}, so the magic could stay playful instead of becoming a mistake."
                ),
                (
                    f"Did {hero.id} shiver in the end?",
                    f"No. {hero.id} listened, used the safe plan, and stayed warm. The story proves the careful choice worked because the magic stayed lovely and harmless."
                ),
                (
                    "How did the story end?",
                    f"It ended with safe magic, laughter, and the expensive {prize.label} still fine. The last image shows that being patient kept both the fun and the precious thing safe."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    spell = world.facts["spell"]
    gear = world.facts["gear"]
    tags = set(spell.tags) | set(world.facts["prize_cfg"].tags) | set(gear.tags)
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
        if ent.kind == "character":
            bits.append("kind=character")
        if ent.region:
            bits.append(f"region={ent.region}")
        if ent.protective:
            bits.append(f"covers={sorted(ent.covers)}")
            bits.append(f"guards={sorted(ent.attrs.get('guards', set()))}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(S, P) :- hits(S, R), worn_on(P, R).
protects(G, S, P) :- gear(G), prize_at_risk(S, P),
                     mess_of(S, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
valid(St, S, P, G) :- setting(St), affords(St, S), prize_at_risk(S, P), protects(G, S, P).

rash_outcome(lesson) :- temperament(rash).
rash_outcome(safe)   :- temperament(T), not temperament(rash), temperament(T).
outcome(O) :- rash_outcome(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for spell_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, spell_id))
    for spell_id, spell in SPELLS.items():
        lines.append(asp.fact("spell", spell_id))
        lines.append(asp.fact("mess_of", spell_id, spell.mess))
        for region in sorted(spell.zone):
            lines.append(asp.fact("hits", spell_id, region))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("worn_on", prize_id, prize.region))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        for region in sorted(gear.covers):
            lines.append(asp.fact("covers", gear_id, region))
        for mess in sorted(gear.guards):
            lines.append(asp.fact("guards", gear_id, mess))
    for temperament in TEMPERAMENTS:
        lines.append(asp.fact("temperament", temperament))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(temperament: str) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("temperament", temperament),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="mossy_glen",
        spell="frost_spark",
        prize="silk_cape",
        gear="winter_wrap",
        hero_name="Pip",
        hero_species="rabbit",
        guardian_type="mother",
        temperament="rash",
    ),
    StoryParams(
        setting="willow_hollow",
        spell="rain_ribbon",
        prize="satin_boots",
        gear="galoshes",
        hero_name="Mira",
        hero_species="mouse",
        guardian_type="aunt",
        temperament="careful",
    ),
    StoryParams(
        setting="thimble_meadow",
        spell="wind_whirl",
        prize="velvet_hat",
        gear="earmuffs",
        hero_name="Bram",
        hero_species="fox",
        guardian_type="father",
        temperament="patient",
    ),
    StoryParams(
        setting="mossy_glen",
        spell="rain_ribbon",
        prize="silk_cape",
        gear="rain_cloak",
        hero_name="Luna",
        hero_species="squirrel",
        guardian_type="uncle",
        temperament="gentle",
    ),
]


def explain_rejection(spell: Spell, prize: Prize) -> str:
    if not prize_at_risk(spell, prize):
        return (
            f"(No story: the {spell.label} touches {sorted(spell.zone)}, but the {prize.label} sits on the {prize.region}. "
            f"There is no honest danger to that item, so the warning would be weak.)"
        )
    return (
        f"(No story: nothing in the gear catalog protects the {prize.label} on the {prize.region} from the {spell.label}. "
        f"A safe fix must really cover the thing at risk.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "lesson" if is_rash(params.temperament) else "safe"


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.spell not in SPELLS:
        raise StoryError(f"(Unknown spell: {params.spell})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.gear not in GEAR:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")
    setting = SETTINGS[params.setting]
    spell = SPELLS[params.spell]
    prize = PRIZES[params.prize]
    if params.spell not in setting.affords:
        raise StoryError(f"(No story: {setting.place} is not used for the {spell.label}.)")
    if not prize_at_risk(spell, prize) or select_gear(spell, prize) is None:
        raise StoryError(explain_rejection(spell, prize))
    needed = select_gear(spell, prize)
    if needed is None or needed.id != params.gear:
        raise StoryError(
            f"(No story: the safe gear for {params.spell} with {params.prize} is {needed.id if needed else 'none'}, "
            f"not {params.gear}.)"
        )


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    bad = 0
    for temperament in TEMPERAMENTS:
        py = "lesson" if is_rash(temperament) else "safe"
        asp_val = asp_outcome(temperament)
        if py != asp_val:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(TEMPERAMENTS)} temperaments.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(TEMPERAMENTS)} temperament outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a young animal, a magic charm, and a careful or rash choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spell and args.prize:
        spell = SPELLS[args.spell]
        prize = PRIZES[args.prize]
        if not prize_at_risk(spell, prize) or select_gear(spell, prize) is None:
            raise StoryError(explain_rejection(spell, prize))
    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spell is None or combo[1] == args.spell)
        and (args.prize is None or combo[2] == args.prize)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, spell_id, prize_id, gear_id = rng.choice(sorted(combos))
    hero_species = args.species or rng.choice(SPECIES)
    hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    guardian_type = args.guardian or rng.choice(GUARDIANS)
    temperament = args.temperament or rng.choice(TEMPERAMENTS)
    params = StoryParams(
        setting=setting_id,
        spell=spell_id,
        prize=prize_id,
        gear=gear_id,
        hero_name=hero_name,
        hero_species=hero_species,
        guardian_type=guardian_type,
        temperament=temperament,
    )
    _validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        spell=SPELLS[params.spell],
        prize_cfg=PRIZES[params.prize],
        gear_cfg=GEAR[params.gear],
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        guardian_type=params.guardian_type,
        temperament=params.temperament,
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
        print(f"{len(combos)} compatible (setting, spell, prize, gear) combos:\n")
        for setting_id, spell_id, prize_id, gear_id in combos:
            print(f"  {setting_id:14} {spell_id:12} {prize_id:12} {gear_id}")
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
            header = f"### {p.hero_name}: {p.spell} with {p.prize} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
