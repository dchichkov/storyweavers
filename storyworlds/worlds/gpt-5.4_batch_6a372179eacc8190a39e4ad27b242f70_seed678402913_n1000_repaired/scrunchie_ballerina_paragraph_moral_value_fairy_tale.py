#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scrunchie_ballerina_paragraph_moral_value_fairy_tale.py
===================================================================================

A standalone storyworld for a tiny fairy-tale domain built from the seed words
"scrunchie", "ballerina", and "paragraph".

Premise
-------
A child is chosen to dance as the moon garden's little ballerina. She is tempted
to ignore a plain scrunchie because a sparkling crown-pin looks prettier. An
older helper points to a short paragraph in the festival card explaining that a
steady bun matters more than glitter. The storyworld simulates whether the child
listens, whether the dance stays safe, and how the ending proves the moral value:
care and humility can shine brighter than showy things.

Run it
------
python storyworlds/worlds/gpt-5.4/scrunchie_ballerina_paragraph_moral_value_fairy_tale.py
python storyworlds/worlds/gpt-5.4/scrunchie_ballerina_paragraph_moral_value_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/scrunchie_ballerina_paragraph_moral_value_fairy_tale.py --hair_choice jeweled_pin
python storyworlds/worlds/gpt-5.4/scrunchie_ballerina_paragraph_moral_value_fairy_tale.py --verify
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
    worn_by: Optional[str] = None
    secures_hair: bool = False
    sparkle: int = 0
    stability: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "fairy_godmother", "aunt", "queen"}
        male = {"boy", "man", "father"}
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
            "fairy_godmother": "fairy godmother",
            "aunt": "aunt",
            "queen": "queen",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    glow: str
    floor: str
    witness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HairChoice:
    id: str
    label: str
    phrase: str
    sparkle: int
    stability: int
    secures_hair: bool
    tempting_line: str
    safe_line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CardText:
    id: str
    paragraph: str
    moral_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LessonGift:
    id: str
    phrase: str
    closing: str
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


def _r_loose_hair(world: World) -> list[str]:
    out: list[str] = []
    dancer = world.get("dancer")
    adornment = world.get("adornment")
    breeze = world.get("breeze")
    if dancer.meters["turning"] < THRESHOLD or breeze.meters["blowing"] < THRESHOLD:
        return out
    if adornment.meters["holding"] >= THRESHOLD:
        return out
    sig = ("loose_hair", adornment.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dancer.meters["hair_loose"] += 1
    dancer.memes["alarm"] += 1
    out.append("__loose__")
    return out


def _r_stumble(world: World) -> list[str]:
    out: list[str] = []
    dancer = world.get("dancer")
    if dancer.meters["hair_loose"] < THRESHOLD:
        return out
    sig = ("stumble", dancer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dancer.meters["stumbled"] += 1
    dancer.memes["embarrassment"] += 1
    out.append("__stumble__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="loose_hair", tag="physical", apply=_r_loose_hair),
    Rule(name="stumble", tag="physical", apply=_r_stumble),
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


def choice_is_reasonable(choice: HairChoice) -> bool:
    return choice.stability >= SENSE_MIN


def best_choice() -> HairChoice:
    return max(HAIR_CHOICES.values(), key=lambda item: item.stability)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for card_id in CARD_TEXTS:
            for choice_id, choice in HAIR_CHOICES.items():
                if choice_is_reasonable(choice):
                    combos.append((setting_id, card_id, choice_id))
    return combos


def would_listen(helper_relation: str, dancer_age: int, helper_age: int, trust: int) -> bool:
    older_helper = helper_age > dancer_age
    return older_helper and helper_relation in {"sister", "cousin"} and trust >= 6


def dance_succeeds(choice: HairChoice, wind: int) -> bool:
    return choice.stability >= wind


def predict_dance(world: World, hair_choice: HairChoice, wind: int) -> dict:
    sim = world.copy()
    dancer = sim.get("dancer")
    adornment = sim.get("adornment")
    breeze = sim.get("breeze")
    adornment.label = hair_choice.label
    adornment.phrase = hair_choice.phrase
    adornment.secures_hair = hair_choice.secures_hair
    adornment.sparkle = hair_choice.sparkle
    adornment.stability = hair_choice.stability
    adornment.meters["holding"] = float(hair_choice.stability)
    breeze.meters["blowing"] = float(wind)
    dancer.meters["turning"] += 1
    propagate(sim, narrate=False)
    return {
        "hair_loose": dancer.meters["hair_loose"] >= THRESHOLD,
        "stumbled": dancer.meters["stumbled"] >= THRESHOLD,
    }


def introduce(world: World, dancer: Entity, helper: Entity, setting: Setting) -> None:
    dancer.memes["wonder"] += 1
    world.say(
        f"Once, in {setting.place}, there lived a little ballerina named {dancer.id}. "
        f"Every evening, {setting.glow}, and {setting.witness} seemed to lean close "
        f"whenever {dancer.pronoun()} danced."
    )
    world.say(
        f"{helper.id}, {dancer.pronoun('possessive')} {helper.attrs.get('relation_word', 'dear helper')}, "
        f"often watched with a warm smile from the edge of {setting.floor}."
    )


def invitation(world: World, dancer: Entity, card: CardText) -> None:
    dancer.memes["hope"] += 1
    world.say(
        f"One silver dusk, a festival card arrived tied with moon-thread. "
        f"In the middle of it sat a neat paragraph that {dancer.id} read twice:"
    )
    world.say(f'"{card.paragraph}"')


def choice_scene(world: World, dancer: Entity, choice: HairChoice, plain_choice: HairChoice) -> None:
    dancer.memes["vanity"] += float(choice.sparkle)
    world.say(
        f"Beside the card lay two ways to gather {dancer.id}'s hair: {plain_choice.phrase} "
        f"and {choice.phrase}. {choice.tempting_line}"
    )


def helper_warning(world: World, helper: Entity, dancer: Entity, card: CardText,
                   risky_choice: HairChoice, wind: int) -> None:
    pred = predict_dance(world, risky_choice, wind)
    world.facts["predicted_stumble"] = pred["stumbled"]
    helper.memes["care"] += 1
    if pred["stumbled"]:
        extra = "and a dancer cannot bow beautifully while chasing flying curls"
    else:
        extra = "and steady hair helps every turn look clear"
    world.say(
        f'{helper.id} touched the card and said, "Listen to the paragraph, {dancer.id}. '
        f'{card.moral_line}, {extra}. The pretty thing is not always the helpful thing."'
    )


def back_down(world: World, dancer: Entity, helper: Entity, scrunchie: HairChoice) -> None:
    dancer.memes["humility"] += 1
    dancer.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{dancer.id} looked again, not at the sparkle first, but at what would let "
        f"{dancer.pronoun('object')} dance well. With a small nod, {dancer.pronoun()} chose {scrunchie.phrase}."
    )


def defy(world: World, dancer: Entity, helper: Entity, choice: HairChoice) -> None:
    dancer.memes["defiance"] += 1
    world.say(
        f'"It glitters like a star," said {dancer.id}. {dancer.pronoun().capitalize()} thanked '
        f"{helper.id} for the warning, yet reached for {choice.phrase} anyway."
    )


def prepare(world: World, dancer: Entity, choice: HairChoice, wind: int) -> None:
    adornment = world.get("adornment")
    breeze = world.get("breeze")
    adornment.label = choice.label
    adornment.phrase = choice.phrase
    adornment.secures_hair = choice.secures_hair
    adornment.sparkle = choice.sparkle
    adornment.stability = choice.stability
    adornment.meters["holding"] = float(choice.stability)
    breeze.meters["blowing"] = float(wind)
    world.say(
        f"Soon the bells rang for the dance, and a light wind began to wander through the garden paths."
    )


def perform(world: World, dancer: Entity, setting: Setting) -> None:
    dancer.meters["turning"] += 1
    dancer.memes["courage"] += 1
    propagate(world, narrate=False)
    if dancer.meters["stumbled"] >= THRESHOLD:
        world.say(
            f"{dancer.id} stepped onto {setting.floor} and spun. Then a teasing gust tugged at {dancer.pronoun('possessive')} hair."
        )
        world.say(
            "A shining lock slipped free, brushed across her eyes, and her careful feet missed one silver beat."
        )
    else:
        world.say(
            f"{dancer.id} stepped onto {setting.floor} and spun. The wind brushed by, "
            f"but {dancer.pronoun('possessive')} hair stayed neat, and every turn opened like a flower."
        )


def rescue_and_finish(world: World, helper: Entity, dancer: Entity, scrunchie: HairChoice) -> None:
    adornment = world.get("adornment")
    adornment.label = scrunchie.label
    adornment.phrase = scrunchie.phrase
    adornment.secures_hair = scrunchie.secures_hair
    adornment.sparkle = scrunchie.sparkle
    adornment.stability = scrunchie.stability
    adornment.meters["holding"] = float(scrunchie.stability)
    dancer.meters["hair_loose"] = 0.0
    dancer.memes["gratitude"] += 1
    dancer.memes["humility"] += 1
    world.say(
        f"{helper.id} hurried forward, gentle as a lantern-bird, and tied {scrunchie.phrase} snugly around the loose hair."
    )
    world.say(
        f'"Try again," {helper.pronoun()} whispered. This time {dancer.id} finished the dance with quiet, steady grace.'
    )


def praise(world: World, dancer: Entity, card: CardText, gift: LessonGift) -> None:
    dancer.memes["joy"] += 1
    dancer.memes["lesson"] += 1
    world.say(
        f"When the music ended, the garden clapped in a soft rustle of leaves. "
        f"{gift.phrase} was laid in {dancer.id}'s hands, and {gift.closing}"
    )
    world.say(
        f"{dancer.id} remembered the paragraph and smiled, because {card.moral_line.lower()}."
    )


def closing_moral(world: World, dancer: Entity, helper: Entity, choice_id: str) -> None:
    if choice_id == "scrunchie":
        world.say(
            f"After that night, {dancer.id} still loved lovely things, but {dancer.pronoun()} learned to ask which one was kindest to the work before the applause."
        )
    else:
        world.say(
            f"After that night, {dancer.id} hugged {helper.id} and said that the plain scrunchie had been wiser than all the glitter in the garden."
        )


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the Moonlit Garden behind the old castle",
        glow="moonflowers shone like tiny lamps",
        floor="the round white dance-stone",
        witness="the roses and moths",
        tags={"garden", "fairy_tale"},
    ),
    "dew_hall": Setting(
        id="dew_hall",
        place="the Dewdrop Hall beneath the hill",
        glow="glass leaves on the ceiling shimmered with pearly light",
        floor="the polished petal floor",
        witness="the crickets and candle-fairies",
        tags={"hall", "fairy_tale"},
    ),
    "thistle_green": Setting(
        id="thistle_green",
        place="the Thistle Green beside the brook",
        glow="fireflies stitched gold over the grass",
        floor="the flat moss stage",
        witness="the lilies and frogs",
        tags={"meadow", "fairy_tale"},
    ),
}

HAIR_CHOICES = {
    "scrunchie": HairChoice(
        id="scrunchie",
        label="scrunchie",
        phrase="a soft silver scrunchie",
        sparkle=1,
        stability=3,
        secures_hair=True,
        tempting_line="It was plain beside the jewels, yet it promised to hold every curl where it belonged.",
        safe_line="The scrunchie held the bun fast.",
        fail_line="",
        tags={"scrunchie", "safe_choice"},
    ),
    "jeweled_pin": HairChoice(
        id="jeweled_pin",
        label="jeweled pin",
        phrase="a jeweled pin shaped like a falling star",
        sparkle=3,
        stability=1,
        secures_hair=False,
        tempting_line="It flashed so brightly that it seemed made for a princess in a storybook.",
        safe_line="",
        fail_line="The jeweled pin glittered, but it did not hold the dancer's hair firmly.",
        tags={"pin", "showy_choice"},
    ),
}

CARD_TEXTS = {
    "care_first": CardText(
        id="care_first",
        paragraph="Little ballerina, remember this: grace begins before the music starts. Tie your hair with care, keep your steps true, and let kindness guide your choices more than sparkle.",
        moral_line="care is part of beauty",
        tags={"paragraph", "care"},
    ),
    "steady_before_shiny": CardText(
        id="steady_before_shiny",
        paragraph="Dear dancer of the moon, the finest turn is not the flashiest one. A steady ribbon, a patient heart, and honest practice shine longest.",
        moral_line="steadiness shines longer than glitter",
        tags={"paragraph", "steadiness"},
    ),
    "humble_tools": CardText(
        id="humble_tools",
        paragraph="To the child who will dance tonight: never laugh at a small helper. Plain things often keep great promises, and brave hearts listen before they leap.",
        moral_line="small helpers can carry great wisdom",
        tags={"paragraph", "humility"},
    ),
}

GIFTS = {
    "bell": LessonGift(
        id="bell",
        phrase="A tiny silver bell",
        closing="it chimed once, as if agreeing that wise choices can sound sweet too.",
        tags={"gift"},
    ),
    "rose": LessonGift(
        id="rose",
        phrase="A moon-rose with cool glowing petals",
        closing="its light rested quietly in her palms, gentler than any jewel.",
        tags={"gift"},
    ),
    "ribbon_bookmark": LessonGift(
        id="ribbon_bookmark",
        phrase="A satin ribbon bookmark",
        closing="it was tucked into the festival card so the good paragraph would never be lost.",
        tags={"gift", "paragraph"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Elin", "Poppy", "Willa", "Iris"]
HELPER_NAMES = ["Aunt Dove", "Cousin May", "Sister Fern", "Aunt Lark", "Cousin Pearl"]
TRAITS = ["hopeful", "gentle", "eager", "thoughtful", "bright-eyed", "careful"]


@dataclass
class StoryParams:
    setting: str
    card_text: str
    hair_choice: str
    gift: str
    dancer_name: str
    helper_name: str
    helper_relation: str
    dancer_trait: str
    dancer_age: int
    helper_age: int
    trust: int
    wind: int
    seed: Optional[int] = None


KNOWLEDGE = {
    "scrunchie": [
        (
            "What is a scrunchie?",
            "A scrunchie is a soft ring of cloth with elastic inside. People use it to hold hair together gently."
        )
    ],
    "ballerina": [
        (
            "What does a ballerina do?",
            "A ballerina is a dancer who practices balance, turns, and graceful steps. Good dancing takes care as well as beauty."
        )
    ],
    "paragraph": [
        (
            "What is a paragraph?",
            "A paragraph is a group of sentences that belong together. It helps hold one clear idea in one place."
        )
    ],
    "care": [
        (
            "Why can a plain tool be better than a fancy one?",
            "A plain tool can be better when it does the job safely and well. Looking pretty is not the same as being useful."
        )
    ],
    "steadiness": [
        (
            "Why does a dancer need steady hair and clothes?",
            "A dancer needs things to stay in place so she can see, balance, and move safely. Small distractions can spoil careful steps."
        )
    ],
    "humility": [
        (
            "What does humility mean?",
            "Humility means you do not think shiny or showy things make you better than others. You are willing to choose the sensible thing and learn from help."
        )
    ],
}
KNOWLEDGE_ORDER = ["scrunchie", "ballerina", "paragraph", "care", "steadiness", "humility"]


def pair_relation_word(rel: str) -> str:
    return {
        "sister": "older sister",
        "cousin": "older cousin",
        "aunt": "kind aunt",
    }[rel]


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.card_text not in CARD_TEXTS:
        raise StoryError(f"(Unknown card_text '{params.card_text}'.)")
    if params.hair_choice not in HAIR_CHOICES:
        raise StoryError(f"(Unknown hair_choice '{params.hair_choice}'.)")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift '{params.gift}'.)")

    setting = SETTINGS[params.setting]
    card = CARD_TEXTS[params.card_text]
    requested_choice = HAIR_CHOICES[params.hair_choice]
    scrunchie = HAIR_CHOICES["scrunchie"]
    gift = GIFTS[params.gift]

    world = World(setting)
    dancer = world.add(Entity(
        id="dancer",
        kind="character",
        type="girl",
        label=params.dancer_name,
        phrase=params.dancer_name,
        role="dancer",
        traits=[params.dancer_trait],
        attrs={"age": params.dancer_age},
        tags={"ballerina"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="woman",
        label=params.helper_name,
        phrase=params.helper_name,
        role="helper",
        attrs={
            "age": params.helper_age,
            "relation": params.helper_relation,
            "relation_word": pair_relation_word(params.helper_relation),
        },
        tags={"care"},
    ))
    world.add(Entity(
        id="adornment",
        type="hair_tool",
        label=requested_choice.label,
        phrase=requested_choice.phrase,
        secures_hair=requested_choice.secures_hair,
        sparkle=requested_choice.sparkle,
        stability=requested_choice.stability,
    ))
    world.add(Entity(
        id="breeze",
        type="wind",
        label="breeze",
        phrase="a silver breeze",
    ))

    introduce(world, dancer, helper, setting)
    invitation(world, dancer, card)

    world.para()
    choice_scene(world, dancer, requested_choice, scrunchie)

    listened = False
    if params.hair_choice != "scrunchie":
        helper_warning(world, helper, dancer, card, requested_choice, params.wind)
        listened = would_listen(params.helper_relation, params.dancer_age, params.helper_age, params.trust)
        if listened:
            back_down(world, dancer, helper, scrunchie)
            final_choice = scrunchie
            outcome = "listened"
        else:
            defy(world, dancer, helper, requested_choice)
            final_choice = requested_choice
            outcome = "tried_showy"
    else:
        dancer.memes["humility"] += 1
        world.say(
            f"{dancer.label} smiled at the plain helper and chose {scrunchie.phrase} at once."
        )
        final_choice = scrunchie
        outcome = "careful"

    world.para()
    prepare(world, dancer, final_choice, params.wind)
    perform(world, dancer, setting)

    stumbled = dancer.meters["stumbled"] >= THRESHOLD
    if stumbled:
        world.para()
        rescue_and_finish(world, helper, dancer, scrunchie)
        outcome = "rescued"
    else:
        dancer.memes["joy"] += 1
        dancer.memes["lesson"] += 1

    world.para()
    praise(world, dancer, card, gift)
    closing_moral(world, dancer, helper, final_choice.id)

    world.facts.update(
        setting=setting,
        card=card,
        gift=gift,
        dancer=dancer,
        helper=helper,
        requested_choice=requested_choice,
        final_choice=final_choice,
        wind=params.wind,
        listened=listened,
        stumbled=stumbled,
        outcome=outcome,
        moral=card.moral_line,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dancer = f["dancer"]
    helper = f["helper"]
    setting = f["setting"]
    final_choice = f["final_choice"]
    card = f["card"]
    prompts = [
        'Write a short fairy tale for a 3-to-5-year-old that includes the words "scrunchie", "ballerina", and "paragraph".',
        f"Tell a gentle fairy-tale story about a little ballerina named {dancer.label} in {setting.place} who must choose between sparkle and steadiness before a dance.",
        f'Write a moral-value story where a helper warns a child to listen to a paragraph that teaches "{card.moral_line}".',
    ]
    if final_choice.id == "scrunchie":
        prompts.append(
            f"End the tale with the child choosing a scrunchie and discovering that quiet care can be more beautiful than glitter."
        )
    else:
        prompts.append(
            f"Let the child first choose a showy hair pin, then learn through a small mistake why the scrunchie was wiser."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dancer = f["dancer"]
    helper = f["helper"]
    card = f["card"]
    requested = f["requested_choice"]
    final_choice = f["final_choice"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little ballerina named {dancer.label} and {helper.label}, her {helper.attrs.get('relation_word')}. They are together in {setting.place} on the night of a special dance."
        ),
        (
            "What did the festival card say?",
            f"The card held a paragraph telling the little dancer to choose care and steadiness before sparkle. Its lesson was that {card.moral_line}."
        ),
        (
            f"Why was the scrunchie important?",
            f"The scrunchie mattered because it could hold {dancer.label}'s hair firmly while she danced. A steady hair tie helped her move safely and gracefully."
        ),
    ]
    if requested.id != "scrunchie":
        qa.append(
            (
                f"Why did {helper.label} warn {dancer.label} about the jeweled pin?",
                f"{helper.label} warned her because the pin looked pretty but was not strong enough for a windy turning dance. The warning came from the paragraph's lesson that useful care matters more than glitter."
            )
        )
    if f["listened"]:
        qa.append(
            (
                f"What did {dancer.label} do after hearing the warning?",
                f"She listened and chose the scrunchie instead of the jeweled pin. That choice showed humility, because she cared more about dancing well than looking grand."
            )
        )
    elif f["stumbled"]:
        qa.append(
            (
                f"What happened during the dance?",
                f"A gust loosened her hair and she stumbled for one beat. Then {helper.label} gently tied on the scrunchie so she could finish with steady grace."
            )
        )
    else:
        qa.append(
            (
                "How did the dance go?",
                f"The dance went smoothly, and her hair stayed neat through the wind. The ending proved that a careful choice made the beautiful moment possible."
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is that {card.moral_line}. A small, sensible helper can be more valuable than a showy ornament."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"scrunchie", "ballerina", "paragraph"}
    moral = f["card"].moral_line
    if "care" in moral:
        tags.add("care")
    if "stead" in moral:
        tags.add("steadiness")
    if "small helper" in moral or "wisdom" in moral:
        tags.add("humility")
    tags.add("steadiness")
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
    for e in list(world.entities.values()):
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
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.secures_hair:
            bits.append("secures_hair=True")
        if e.sparkle:
            bits.append(f"sparkle={e.sparkle}")
        if e.stability:
            bits.append(f"stability={e.stability}")
        lines.append(f"  {e.id:9} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_garden",
        card_text="care_first",
        hair_choice="scrunchie",
        gift="bell",
        dancer_name="Mira",
        helper_name="Aunt Dove",
        helper_relation="aunt",
        dancer_trait="eager",
        dancer_age=5,
        helper_age=30,
        trust=8,
        wind=2,
    ),
    StoryParams(
        setting="dew_hall",
        card_text="steady_before_shiny",
        hair_choice="jeweled_pin",
        gift="rose",
        dancer_name="Lina",
        helper_name="Sister Fern",
        helper_relation="sister",
        dancer_trait="bright-eyed",
        dancer_age=5,
        helper_age=8,
        trust=8,
        wind=2,
    ),
    StoryParams(
        setting="thistle_green",
        card_text="humble_tools",
        hair_choice="jeweled_pin",
        gift="ribbon_bookmark",
        dancer_name="Nora",
        helper_name="Cousin Pearl",
        helper_relation="cousin",
        dancer_trait="hopeful",
        dancer_age=6,
        helper_age=7,
        trust=4,
        wind=2,
    ),
]


def explain_choice_rejection(choice_id: str) -> str:
    choice = HAIR_CHOICES[choice_id]
    best = best_choice()
    return (
        f"(Refusing hair_choice '{choice_id}': it is too weak for this storyworld's "
        f"reasonableness gate (stability={choice.stability} < {SENSE_MIN}). "
        f"Try '{best.id}', which actually keeps a ballerina's hair secure.)"
    )


def explain_relation_rejection(relation: str) -> str:
    return (
        f"(No story: helper_relation '{relation}' is unknown here. "
        f"Try one of: sister, cousin, aunt.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.hair_choice == "scrunchie":
        return "careful"
    if would_listen(params.helper_relation, params.dancer_age, params.helper_age, params.trust):
        return "listened"
    return "smooth" if dance_succeeds(HAIR_CHOICES[params.hair_choice], params.wind) else "rescued"


ASP_RULES = r"""
reasonable_choice(H) :- hair_choice(H), stability(H, S), sense_min(M), S >= M.
valid(Setting, Card, H) :- setting(Setting), card_text(Card), reasonable_choice(H).

older_helper :- helper_age(H), dancer_age(D), H > D.
listens :- helper_relation(sister), older_helper, trust(T), T >= 6.
listens :- helper_relation(cousin), older_helper, trust(T), T >= 6.

smooth_dance :- chosen_choice(H), stability(H, S), wind(W), S >= W.

outcome(careful) :- chosen_choice(scrunchie).
outcome(listened) :- chosen_choice(jeweled_pin), listens.
outcome(smooth) :- chosen_choice(jeweled_pin), not listens, smooth_dance.
outcome(rescued) :- chosen_choice(jeweled_pin), not listens, not smooth_dance.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CARD_TEXTS:
        lines.append(asp.fact("card_text", cid))
    for hid, choice in HAIR_CHOICES.items():
        lines.append(asp.fact("hair_choice", hid))
        lines.append(asp.fact("stability", hid, choice.stability))
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
    extra = "\n".join([
        asp.fact("chosen_choice", params.hair_choice),
        asp.fact("helper_relation", params.helper_relation),
        asp.fact("helper_age", params.helper_age),
        asp.fact("dancer_age", params.dancer_age),
        asp.fact("trust", params.trust),
        asp.fact("wind", params.wind),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="## smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a fairy-tale ballerina learns that careful choices can shine brighter than glitter."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--card_text", choices=CARD_TEXTS)
    ap.add_argument("--hair_choice", choices=HAIR_CHOICES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--helper_relation", choices=["sister", "cousin", "aunt"])
    ap.add_argument("--wind", type=int, choices=[1, 2, 3])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_helper_name(relation: str, rng: random.Random) -> str:
    if relation == "aunt":
        pool = [n for n in HELPER_NAMES if n.startswith("Aunt")]
    elif relation == "sister":
        pool = [n for n in HELPER_NAMES if n.startswith("Sister")]
    else:
        pool = [n for n in HELPER_NAMES if n.startswith("Cousin")]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper_relation and args.helper_relation not in {"sister", "cousin", "aunt"}:
        raise StoryError(explain_relation_rejection(args.helper_relation))
    if args.hair_choice and not choice_is_reasonable(HAIR_CHOICES[args.hair_choice]):
        raise StoryError(explain_choice_rejection(args.hair_choice))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.card_text is None or combo[1] == args.card_text)
        and (args.hair_choice is None or combo[2] == args.hair_choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, card_text, hair_choice = rng.choice(sorted(combos))
    gift = args.gift or rng.choice(sorted(GIFTS))
    relation = args.helper_relation or rng.choice(["sister", "cousin", "aunt"])
    dancer_name = rng.choice(GIRL_NAMES)
    helper_name = _pick_helper_name(relation, rng)
    dancer_trait = rng.choice(TRAITS)
    if relation == "aunt":
        dancer_age = rng.randint(4, 7)
        helper_age = rng.randint(20, 40)
    else:
        ages = rng.sample([5, 6, 7, 8, 9], 2)
        dancer_age = min(ages)
        helper_age = max(ages)
    trust = rng.randint(4, 9)
    wind = args.wind if args.wind is not None else rng.randint(1, 3)
    return StoryParams(
        setting=setting,
        card_text=card_text,
        hair_choice=hair_choice,
        gift=gift,
        dancer_name=dancer_name,
        helper_name=helper_name,
        helper_relation=relation,
        dancer_trait=dancer_trait,
        dancer_age=dancer_age,
        helper_age=helper_age,
        trust=trust,
        wind=wind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"{len(combos)} compatible (setting, card_text, hair_choice) combos:\n")
        for setting, card_text, hair_choice in combos:
            print(f"  {setting:13} {card_text:20} {hair_choice}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = (
                f"### {p.dancer_name}: {p.hair_choice} in {p.setting} "
                f"({outcome_of(p)})"
            )
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
