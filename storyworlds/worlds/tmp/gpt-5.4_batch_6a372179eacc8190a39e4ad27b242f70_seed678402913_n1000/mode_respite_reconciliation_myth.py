#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py
==============================================================

A standalone story world for a tiny mythic domain: two great powers fall into
conflict, the land grows strained, and a small mediator creates a place of
respite where true reconciliation can happen.

The seed asked for the words "mode" and "respite", the feature
"Reconciliation", and a myth-like style. This world models a child-facing myth
rather than a frozen template: powers carry emotional memes and physical meters,
their quarrel changes the world, and the ending proves balance has returned.

Run it
------
    python storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py
    python storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py --pair sun_moon
    python storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py --cause stolen_song --offering apology_bowl
    python storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py --all
    python storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mode_respite_reconciliation_myth.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly
# from a nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
PATIENCE_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "goddess", "sister", "mother", "queen"}
        male = {"boy", "man", "god", "brother", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class PairCfg:
    id: str
    left_name: str = ""
    left_type: str = "god"
    left_domain: str = ""
    right_name: str = ""
    right_type: str = "goddess"
    right_domain: str = ""
    place: str = ""
    imbalance: str = ""
    opening: str = ""
    closing: str = ""
    shelter_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class CauseCfg:
    id: str
    title: str = ""
    wound: str = ""
    scene: str = ""
    need: str = ""
    repair_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class OfferingCfg:
    id: str
    label: str = ""
    phrase: str = ""
    repair: str = ""
    action: str = ""
    peace_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ShelterCfg:
    id: str
    label: str = ""
    phrase: str = ""
    suits: set[str] = field(default_factory=set)
    hush: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MediatorCfg:
    id: str
    name: str = ""
    type: str = "girl"
    title: str = ""
    trait: str = ""
    patience: int = 2
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def offering_fits(cause: CauseCfg, offering: OfferingCfg) -> bool:
    return cause.need == offering.repair


def shelter_fits(pair: PairCfg, shelter: ShelterCfg) -> bool:
    return bool(pair.shelter_tags & shelter.suits)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for pair_id, pair in PAIRS.items():
        for cause_id, cause in CAUSES.items():
            for offering_id, offering in OFFERINGS.items():
                for shelter_id, shelter in SHELTERS.items():
                    if offering_fits(cause, offering) and shelter_fits(pair, shelter):
                        combos.append((pair_id, cause_id, offering_id, shelter_id))
    return combos


def explain_bad_offering(cause: CauseCfg, offering: OfferingCfg) -> str:
    return (
        f"(No story: {offering.label} repairs '{offering.repair}', but the hurt in "
        f"'{cause.title}' needs '{cause.need}'. In this world, reconciliation must "
        f"answer the real wound.)"
    )


def explain_bad_shelter(pair: PairCfg, shelter: ShelterCfg) -> str:
    wanted = ", ".join(sorted(pair.shelter_tags))
    got = ", ".join(sorted(shelter.suits))
    return (
        f"(No story: {shelter.label} offers respite for [{got}], but {pair.left_name} "
        f"and {pair.right_name} need a meeting place suited to [{wanted}].)"
    )


def outcome_of(params: "StoryParams") -> str:
    patience = MEDIATORS[params.mediator].patience
    if patience < PATIENCE_MIN:
        return "strained"
    if not offering_fits(CAUSES[params.cause], OFFERINGS[params.offering]):
        return "strained"
    if not shelter_fits(PAIRS[params.pair], SHELTERS[params.shelter]):
        return "strained"
    return "reconciled"


def rise_quarrel(world: World, left: Entity, right: Entity, pair: PairCfg, cause: CauseCfg) -> None:
    left.memes["hurt"] += 1
    right.memes["hurt"] += 1
    left.memes["pride"] += 1
    right.memes["pride"] += 1
    world.say(pair.opening)
    world.say(cause.scene)
    world.say(
        f"After that, {left.id} and {right.id} would not walk the same path in the sky or the water. "
        f"The world slipped into a hard mode of waiting, and {pair.imbalance}."
    )


def burden_land(world: World, left: Entity, right: Entity) -> None:
    land = world.get("land")
    land.meters["strain"] += 1
    for spirit in (left, right):
        spirit.memes["lonely"] += 1
    world.say(
        "People grew quiet under the quarrel. Bakers watched their ovens, fishers watched their nets, "
        "and children listened for the old harmony that was missing."
    )


def mediator_sets_out(
    world: World,
    mediator: Entity,
    pair: PairCfg,
    cause: CauseCfg,
    offering: OfferingCfg,
    shelter: ShelterCfg,
) -> None:
    mediator.memes["care"] += 1
    mediator.memes["resolve"] += 1
    world.say(
        f"In that village lived {mediator.attrs['title']} {mediator.id}, a {mediator.attrs['trait']} child "
        f"who believed even proud powers could be led back to kindness."
    )
    world.say(
        f"{mediator.id} gathered {offering.phrase} and climbed toward {shelter.phrase}, "
        f"for {shelter.label} was known as a place of respite where angry voices had to soften."
    )
    world.facts["journey_reason"] = (
        f"{mediator.id} chose {shelter.label} because it gave both powers a quiet place to rest, "
        f"and chose {offering.label} because it matched the hurt from {cause.title}."
    )


def invite_rest(world: World, mediator: Entity, left: Entity, right: Entity, shelter: ShelterCfg) -> None:
    mediator.memes["patience"] += 1
    left.memes["listening"] += 1
    right.memes["listening"] += 1
    world.say(
        f"There {mediator.id} lit no fire and rang no bell. {mediator.pronoun('subject').capitalize()} simply waited, "
        f"and the place itself did the first work: {shelter.hush}."
    )
    world.say(
        f"When {left.id} came from one side and {right.id} from the other, {mediator.id} bowed and said, "
        f'"Before you speak, take this respite. Sit. Rest your anger. Let your true names remember each other."'
    )


def repair(world: World, mediator: Entity, left: Entity, right: Entity, cause: CauseCfg, offering: OfferingCfg) -> None:
    mediator.memes["bridge"] += 1
    left.memes["hurt"] = 0.0
    right.memes["hurt"] = 0.0
    left.memes["pride"] = 0.0
    right.memes["pride"] = 0.0
    left.memes["peace"] += 1
    right.memes["peace"] += 1
    world.say(
        f"Then {mediator.id} placed {offering.phrase} between them and spoke of the wound plainly: "
        f"{cause.wound}"
    )
    world.say(
        f"{offering.action} {cause.repair_line} At last {left.id} looked at {right.id}, "
        f"and {right.id} looked back."
    )
    world.say(offering.peace_text)


def restore(world: World, pair: PairCfg, shelter: ShelterCfg) -> None:
    land = world.get("land")
    land.meters["strain"] = 0.0
    land.meters["balance"] += 1
    world.say(
        f"From that hour, {pair.left_name} and {pair.right_name} moved in balance again. "
        f"{pair.closing}"
    )
    world.say(shelter.ending_image)


def tell(pair: PairCfg, cause: CauseCfg, offering: OfferingCfg, shelter: ShelterCfg, mediator_cfg: MediatorCfg) -> World:
    world = World()
    left = world.add(
        Entity(
            id=pair.left_name,
            kind="character",
            type=pair.left_type,
            label=pair.left_name,
            role="left_spirit",
            tags=set(pair.tags),
            attrs={"domain": pair.left_domain},
        )
    )
    right = world.add(
        Entity(
            id=pair.right_name,
            kind="character",
            type=pair.right_type,
            label=pair.right_name,
            role="right_spirit",
            tags=set(pair.tags),
            attrs={"domain": pair.right_domain},
        )
    )
    mediator = world.add(
        Entity(
            id=mediator_cfg.name,
            kind="character",
            type=mediator_cfg.type,
            label=mediator_cfg.name,
            role="mediator",
            tags=set(mediator_cfg.tags),
            attrs={"title": mediator_cfg.title, "trait": mediator_cfg.trait, "patience": mediator_cfg.patience},
        )
    )
    world.add(Entity(id="land", kind="thing", type="land", label=pair.place, phrase=pair.place))

    rise_quarrel(world, left, right, pair, cause)
    world.para()
    burden_land(world, left, right)
    mediator_sets_out(world, mediator, pair, cause, offering, shelter)
    world.para()
    invite_rest(world, mediator, left, right, shelter)
    repair(world, mediator, left, right, cause, offering)
    world.para()
    restore(world, pair, shelter)

    world.facts.update(
        pair=pair,
        cause=cause,
        offering=offering,
        shelter=shelter,
        mediator=mediator,
        left=left,
        right=right,
        outcome="reconciled",
        respite_used=True,
    )
    return world


@dataclass
class StoryParams:
    pair: str
    cause: str
    offering: str
    shelter: str
    mediator: str
    seed: Optional[int] = None


PAIRS = {
    "sun_moon": PairCfg(
        id="sun_moon",
        left_name="Aru",
        left_type="god",
        left_domain="daylight",
        right_name="Neri",
        right_type="goddess",
        right_domain="night",
        place="the hill-ringed valley",
        imbalance="days grew too bright and nights came late and thin",
        opening="In the first days, Aru of the Sun and Neri of the Moon crossed the heavens like brother and sister dancers, and the hill-ringed valley slept and woke by their shared measure.",
        closing="Morning became gentle, evening became deep, and the valley learned once more when to work and when to dream.",
        shelter_tags={"sky", "stone"},
        tags={"sun", "moon", "sky"},
    ),
    "river_wind": PairCfg(
        id="river_wind",
        left_name="Seli",
        left_type="goddess",
        left_domain="river-water",
        right_name="Tor",
        right_type="god",
        right_domain="wandering wind",
        place="the reed-woven marsh",
        imbalance="boats spun in circles and the reeds hissed all night",
        opening="Long ago, Seli of the River and Tor of the Wind played together across the reed-woven marsh, and every boat found its home by their joined song.",
        closing="The reeds bowed instead of hissing, and boats slid home as if the marsh itself were smiling.",
        shelter_tags={"water", "reed"},
        tags={"river", "wind", "water"},
    ),
    "mountain_sea": PairCfg(
        id="mountain_sea",
        left_name="Oren",
        left_type="god",
        left_domain="stone heights",
        right_name="Mira",
        right_type="goddess",
        right_domain="salt sea",
        place="the cliff villages",
        imbalance="the cliffs cracked with thirst while the tide pounded without rhythm",
        opening="When the world was young, Oren of the Mountain and Mira of the Sea traded mist for stone, and the cliff villages grew strong between them.",
        closing="Mist curled up the mountain again, and the sea struck the shore in calm blue breaths.",
        shelter_tags={"stone", "salt"},
        tags={"mountain", "sea", "stone"},
    ),
}

CAUSES = {
    "broken_turn": CauseCfg(
        id="broken_turn",
        title="the broken turn",
        wound="One had taken more than a fair share, and the other had carried the silence of that hurt too long.",
        scene="But in one season of pride, one kept the sky-path past the promised hour, and the other waited in shadow until waiting turned into anger.",
        need="apology",
        repair_line="The words of apology were small, but because they were true, they were stronger than thunder.",
        tags={"apology"},
    ),
    "stolen_song": CauseCfg(
        id="stolen_song",
        title="the stolen song",
        wound="A precious song had been taken and not returned, and the loss had made both memory and trust ache.",
        scene="One evening a secret song was borrowed for glory and not given back, and the one who had sung it first felt strangely emptied.",
        need="return",
        repair_line="What was taken was given back with both hands, and the old melody found its proper heart again.",
        tags={"return"},
    ),
    "harsh_boast": CauseCfg(
        id="harsh_boast",
        title="the harsh boast",
        wound="Cruel words had made one power feel small, and pride had kept the other from admitting the harm.",
        scene="At a feast of clouds and gulls, one boasted that the other's gifts were weak, and laughter cut deeper than any blade.",
        need="shared_work",
        repair_line="Working side by side made the proud words shrink, because hands that build together learn humility.",
        tags={"shared_work"},
    ),
}

OFFERINGS = {
    "apology_bowl": OfferingCfg(
        id="apology_bowl",
        label="apology bowl",
        phrase="a clay bowl painted with two open hands",
        repair="apology",
        action="The bowl was filled with clear water, and each spirit saw the other's face trembling there before speaking.",
        peace_text="Aru and Neri, or Seli and Tor, or Oren and Mira depending on the telling, let their anger loosen. The one who had held too much bowed first, and the other answered with forgiveness.",
        tags={"apology", "water"},
    ),
    "echo_shell": OfferingCfg(
        id="echo_shell",
        label="echo shell",
        phrase="an echo shell wrapped in silver thread",
        repair="return",
        action="When the shell was opened, the hidden song rose out of it exactly as it had been kept, bright and unbroken.",
        peace_text="The stolen music returned to its first owner, and with it came trust. The two powers heard their old harmony inside the shell and knew it should never have been divided.",
        tags={"return", "song"},
    ),
    "bridge_thread": OfferingCfg(
        id="bridge_thread",
        label="bridge thread",
        phrase="a long golden thread for binding a little bridge of reeds and twigs",
        repair="shared_work",
        action="Instead of arguing over who was greater, the two powers used the thread to bind a small bridge together and watched it hold.",
        peace_text="By the time the bridge stood, neither spirit wished to keep the old boast alive. They had made one strong thing together, and shared work cooled their pride.",
        tags={"shared_work", "bridge"},
    ),
}

SHELTERS = {
    "cedar_cave": ShelterCfg(
        id="cedar_cave",
        label="the Cedar Cave",
        phrase="the Cedar Cave above the old goat paths",
        suits={"sky", "stone"},
        hush="Cedar smoke drifted along the cave roof, and even proud sky voices became low and thoughtful",
        ending_image="At sunset, swallows wheeled over the cave mouth while children below counted the first stars without fear.",
        tags={"stone", "rest"},
    ),
    "reed_island": ShelterCfg(
        id="reed_island",
        label="the Reed Island",
        phrase="the Reed Island in the still heart of the marsh",
        suits={"water", "reed"},
        hush="Reeds bent close around the island, and water tapped the roots so softly that no shout could keep its sharp edge",
        ending_image="That night lanterns floated between the reeds, and every little boat found the bank before the frogs began their songs.",
        tags={"water", "rest"},
    ),
    "salt_arch": ShelterCfg(
        id="salt_arch",
        label="the Salt Arch",
        phrase="the Salt Arch where cliff and spray touched",
        suits={"salt", "stone"},
        hush="Sea mist cooled the rocks there, and the crash of waves turned fierce voices into slow, measured speech",
        ending_image="By dawn pearls of mist hung on the cliff grass, and the shore children woke to a tide that sounded like breathing, not battle.",
        tags={"salt", "stone", "rest"},
    ),
}

MEDIATORS = {
    "mina": MediatorCfg(
        id="mina",
        name="Mina",
        type="girl",
        title="goatherd",
        trait="steady",
        patience=3,
        tags={"child", "patient"},
    ),
    "tarin": MediatorCfg(
        id="tarin",
        name="Tarin",
        type="boy",
        title="boat-keeper",
        trait="gentle",
        patience=2,
        tags={"child", "patient"},
    ),
    "suri": MediatorCfg(
        id="suri",
        name="Suri",
        type="girl",
        title="shell-gatherer",
        trait="thoughtful",
        patience=3,
        tags={"child", "patient"},
    ),
    "peb": MediatorCfg(
        id="peb",
        name="Peb",
        type="boy",
        title="shepherd",
        trait="restless",
        patience=1,
        tags={"child"},
    ),
}


CURATED = [
    StoryParams(
        pair="sun_moon",
        cause="broken_turn",
        offering="apology_bowl",
        shelter="cedar_cave",
        mediator="mina",
    ),
    StoryParams(
        pair="river_wind",
        cause="stolen_song",
        offering="echo_shell",
        shelter="reed_island",
        mediator="tarin",
    ),
    StoryParams(
        pair="mountain_sea",
        cause="harsh_boast",
        offering="bridge_thread",
        shelter="salt_arch",
        mediator="suri",
    ),
    StoryParams(
        pair="sun_moon",
        cause="harsh_boast",
        offering="bridge_thread",
        shelter="cedar_cave",
        mediator="mina",
    ),
]


KNOWLEDGE = {
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that uses big images, like spirits or gods, to explain feelings and the world. Myths often teach what happens when pride, kindness, or courage grows strong."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people who were hurt or angry find a way to make peace again. It usually needs truth, listening, and a choice to stop holding the hurt so tightly."
        )
    ],
    "respite": [
        (
            "What is respite?",
            "Respite is a time or place of rest in the middle of trouble. A little quiet can help hearts slow down enough to listen."
        )
    ],
    "mode": [
        (
            "What does mode mean in this story?",
            "Mode means a way something is acting or feeling for a while. When the world slips into a hard mode, it is stuck in a harsh pattern until something changes."
        )
    ],
    "apology": [
        (
            "Why can an apology help?",
            "A true apology names the hurt and admits it was real. That can open the door for forgiveness because the pain is no longer being ignored."
        )
    ],
    "return": [
        (
            "Why does returning something matter?",
            "Giving back what was wrongly taken shows respect. It helps trust grow again because the person who was hurt sees the loss has been taken seriously."
        )
    ],
    "shared_work": [
        (
            "Why can working together heal a quarrel?",
            "Shared work turns two people toward one task instead of one fight. Building something together can make pride soften and trust come back."
        )
    ],
    "sun": [
        (
            "Why do many old stories talk about the sun and moon like people?",
            "Old stories often turn the sun and moon into people so children can picture balance and change. It makes day and night feel like a relationship instead of only a pattern."
        )
    ],
    "river": [
        (
            "Why is a river important in stories?",
            "A river carries water, travel, and life. When a river is troubled in a story, it often means the whole land feels the trouble too."
        )
    ],
    "sea": [
        (
            "Why does the sea stand for big feelings in stories?",
            "The sea can be calm or fierce, so it is a good picture for strong feelings. A peaceful sea at the end of a story shows that something inside the world has settled."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "myth",
    "reconciliation",
    "respite",
    "mode",
    "apology",
    "return",
    "shared_work",
    "sun",
    "river",
    "sea",
]


def generation_prompts(world: World) -> list[str]:
    pair = world.facts["pair"]
    cause = world.facts["cause"]
    offering = world.facts["offering"]
    shelter = world.facts["shelter"]
    mediator = world.facts["mediator"]
    return [
        'Write a short child-facing myth that includes the exact words "mode" and "respite" and ends in reconciliation.',
        f"Tell a myth where {pair.left_name} and {pair.right_name} quarrel because of {cause.title}, and {mediator.id}, a {mediator.attrs['title']}, leads them to {shelter.label} with {offering.phrase}.",
        f"Write a simple mythic story in which a child creates a place of respite, the real wound is named honestly, and the land is healed when reconciliation finally happens.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    pair = world.facts["pair"]
    cause = world.facts["cause"]
    offering = world.facts["offering"]
    shelter = world.facts["shelter"]
    mediator = world.facts["mediator"]
    left = world.facts["left"]
    right = world.facts["right"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {left.id} and {right.id}, two great powers whose quarrel hurts the land, and {mediator.id}, the child who helps them meet again."
        ),
        (
            f"Why were {left.id} and {right.id} fighting?",
            f"They were divided by {cause.title}. {cause.wound} That hurt stayed alive until someone named it honestly."
        ),
        (
            f"Why did {mediator.id} bring them to {shelter.label}?",
            f"{mediator.id} wanted them to rest before arguing again. The shelter gave them respite, so their anger could slow down enough for listening."
        ),
        (
            f"Why was {offering.label} the right thing to bring?",
            f"It matched the wound at the center of the quarrel. In this story, reconciliation works because the gift answers the real hurt instead of hiding it."
        ),
        (
            "How did the world change after they made peace?",
            f"The old strain lifted and balance returned. {pair.closing}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    pair = world.facts["pair"]
    cause = world.facts["cause"]
    tags = {"myth", "reconciliation", "respite", "mode"}
    tags |= set(cause.tags)
    if "sun" in pair.tags or "moon" in pair.tags:
        tags.add("sun")
    if "river" in pair.tags:
        tags.add("river")
    if "sea" in pair.tags:
        tags.add("sea")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
repairs(C, O) :- cause_need(C, N), offering_repair(O, N).
restful(P, S) :- pair_needs(P, T), shelter_suits(S, T).
valid(P, C, O, S) :- pair(P), cause(C), offering(O), shelter(S), repairs(C, O), restful(P, S).

reconciled :- chosen_mediator(M), patience(M, P), patience_min(Mn), P >= Mn,
              chosen_cause(C), chosen_offering(O), repairs(C, O),
              chosen_pair(P), chosen_shelter(S), restful(P, S).
outcome(reconciled) :- reconciled.
outcome(strained) :- not reconciled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pair_id, pair in PAIRS.items():
        lines.append(asp.fact("pair", pair_id))
        for tag in sorted(pair.shelter_tags):
            lines.append(asp.fact("pair_needs", pair_id, tag))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_need", cause_id, cause.need))
    for offering_id, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", offering_id))
        lines.append(asp.fact("offering_repair", offering_id, offering.repair))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        for tag in sorted(shelter.suits):
            lines.append(asp.fact("shelter_suits", shelter_id, tag))
    for mediator_id, mediator in MEDIATORS.items():
        lines.append(asp.fact("mediator", mediator_id))
        lines.append(asp.fact("patience", mediator_id, mediator.patience))
    lines.append(asp.fact("patience_min", PATIENCE_MIN))
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
            asp.fact("chosen_pair", params.pair),
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_offering", params.offering),
            asp.fact("chosen_shelter", params.shelter),
            asp.fact("chosen_mediator", params.mediator),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "respite" not in sample.story or "mode" not in sample.story:
        raise StoryError("Smoke test failed: generated story missing required mythic core.")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    if "### smoke" not in buf.getvalue():
        raise StoryError("Smoke test failed: emit() did not produce output.")


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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic reconciliation story world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--mediator", choices=MEDIATORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.offering:
        cause = CAUSES[args.cause]
        offering = OFFERINGS[args.offering]
        if not offering_fits(cause, offering):
            raise StoryError(explain_bad_offering(cause, offering))
    if args.pair and args.shelter:
        pair = PAIRS[args.pair]
        shelter = SHELTERS[args.shelter]
        if not shelter_fits(pair, shelter):
            raise StoryError(explain_bad_shelter(pair, shelter))

    combos = [
        combo
        for combo in valid_combos()
        if (args.pair is None or combo[0] == args.pair)
        and (args.cause is None or combo[1] == args.cause)
        and (args.offering is None or combo[2] == args.offering)
        and (args.shelter is None or combo[3] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pair_id, cause_id, offering_id, shelter_id = rng.choice(sorted(combos))
    mediator_id = args.mediator or rng.choice(sorted(m for m, cfg in MEDIATORS.items() if cfg.patience >= PATIENCE_MIN))
    return StoryParams(
        pair=pair_id,
        cause=cause_id,
        offering=offering_id,
        shelter=shelter_id,
        mediator=mediator_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pair not in PAIRS:
        raise StoryError(f"(Unknown pair: {params.pair})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Unknown offering: {params.offering})")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(Unknown shelter: {params.shelter})")
    if params.mediator not in MEDIATORS:
        raise StoryError(f"(Unknown mediator: {params.mediator})")

    if outcome_of(params) != "reconciled":
        if not offering_fits(CAUSES[params.cause], OFFERINGS[params.offering]):
            raise StoryError(explain_bad_offering(CAUSES[params.cause], OFFERINGS[params.offering]))
        if not shelter_fits(PAIRS[params.pair], SHELTERS[params.shelter]):
            raise StoryError(explain_bad_shelter(PAIRS[params.pair], SHELTERS[params.shelter]))
        raise StoryError("(No story: this mediator is too impatient for reconciliation in this myth.)")

    world = tell(
        PAIRS[params.pair],
        CAUSES[params.cause],
        OFFERINGS[params.offering],
        SHELTERS[params.shelter],
        MEDIATORS[params.mediator],
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
        print(f"{len(combos)} compatible (pair, cause, offering, shelter) combos:\n")
        for pair_id, cause_id, offering_id, shelter_id in combos:
            print(f"  {pair_id:13} {cause_id:12} {offering_id:13} {shelter_id}")
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
            try:
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.pair}: {p.cause} with {p.offering} at {p.shelter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
