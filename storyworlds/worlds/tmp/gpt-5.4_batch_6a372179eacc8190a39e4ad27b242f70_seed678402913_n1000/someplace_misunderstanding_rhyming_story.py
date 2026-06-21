#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py
======================================================================

A standalone story world for a tiny rhyming tale about a misunderstanding:
one child says where to meet, another child hears a similar-sounding place,
and the mix-up is gently fixed.

The domain is intentionally small and constrained. A setting must contain both
the intended place and the misheard place, and the chosen repair method must
actually be available there. The simulated state drives the story: the children
separate, worry rises, a clue or helper clarifies the mistake, and the ending
image shows they reached the right someplace at last.

Run it
------
    python storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py --setting fair --mixup gate_crate
    python storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py --setting park --mixup hill_mill
    python storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4/someplace_misunderstanding_rhyming_story.py --verify
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

# Make shared result containers importable when this nested script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Location:
    id: str
    label: str
    the: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    label: str
    intro: str
    sparkle: str
    locations: set[str] = field(default_factory=set)
    signs_at: set[str] = field(default_factory=set)
    helpers_at: set[str] = field(default_factory=set)
    helper_types: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mixup:
    id: str
    said: str
    heard: str
    said_word: str
    heard_word: str
    opener: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    via: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"speaker", "hearer"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lost_worry(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.entities.get("speaker")
    hearer = world.entities.get("hearer")
    if speaker is None or hearer is None:
        return out
    if speaker.attrs.get("place") and hearer.attrs.get("place") and speaker.attrs["place"] != hearer.attrs["place"]:
        sig = ("split_worry", speaker.attrs["place"], hearer.attrs["place"])
        if sig not in world.fired:
            world.fired.add(sig)
            speaker.memes["worry"] += 1
            hearer.memes["worry"] += 1
            out.append("__split__")
    return out


def _r_clarity_relief(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("clarified"):
        return out
    for kid in world.kids():
        sig = ("relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["relief"] += 1
        kid.memes["worry"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="lost_worry", tag="social", apply=_r_lost_worry),
    Rule(name="clarity_relief", tag="social", apply=_r_clarity_relief),
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
                produced.extend(sents)
    return produced


LOCATIONS = {
    "gate": Location(
        id="gate",
        label="blue gate",
        the="the blue gate",
        detail="painted bright as a blueberry plate",
        tags={"gate"},
    ),
    "crate": Location(
        id="crate",
        label="berry crate",
        the="the berry crate",
        detail="stacked with baskets and a wobbling slate",
        tags={"crate"},
    ),
    "hill": Location(
        id="hill",
        label="sunny hill",
        the="the sunny hill",
        detail="soft with grass and daffodils still",
        tags={"hill"},
    ),
    "mill": Location(
        id="mill",
        label="old mill",
        the="the old mill",
        detail="turning its wheel with a whispery trill",
        tags={"mill"},
    ),
    "bridge": Location(
        id="bridge",
        label="little bridge",
        the="the little bridge",
        detail="arched over water with ducks by the edge",
        tags={"bridge", "ducks"},
    ),
    "ridge": Location(
        id="ridge",
        label="stone ridge",
        the="the stone ridge",
        detail="a long gray ledge above fern and sedge",
        tags={"ridge"},
    ),
}

SETTINGS = {
    "fair": Setting(
        id="fair",
        label="spring fair",
        intro="At the spring fair, streamers twirled in the air.",
        sparkle="Drums went boom, and sweet buns scented the square.",
        locations={"gate", "crate"},
        signs_at={"crate"},
        helpers_at={"crate"},
        helper_types={"vendor", "mother", "father"},
        tags={"fair"},
    ),
    "park": Setting(
        id="park",
        label="sunny park",
        intro="At the sunny park, the path made a silver mark.",
        sparkle="Leaves gave a clap, and the pond gave a spark.",
        locations={"bridge", "ridge"},
        signs_at={"ridge"},
        helpers_at={"ridge"},
        helper_types={"gardener", "mother", "father"},
        tags={"park"},
    ),
    "meadow": Setting(
        id="meadow",
        label="windy meadow",
        intro="At the windy meadow, clouds sailed light and mellow.",
        sparkle="Kites tugged high, and buttercups lined the hollow.",
        locations={"hill", "mill"},
        signs_at={"mill"},
        helpers_at={"mill"},
        helper_types={"miller", "mother", "father"},
        tags={"meadow"},
    ),
}

MIXUPS = {
    "gate_crate": Mixup(
        id="gate_crate",
        said="gate",
        heard="crate",
        said_word="gate",
        heard_word="crate",
        opener="\"Meet me by the gate,\"",
        ending="shared warm seed cakes by the blue gate",
        tags={"mishearing", "gate", "crate"},
    ),
    "bridge_ridge": Mixup(
        id="bridge_ridge",
        said="bridge",
        heard="ridge",
        said_word="bridge",
        heard_word="ridge",
        opener="\"Meet me by the bridge,\"",
        ending="fed little crumbs to ducks by the bridge",
        tags={"mishearing", "bridge", "ridge", "ducks"},
    ),
    "hill_mill": Mixup(
        id="hill_mill",
        said="hill",
        heard="mill",
        said_word="hill",
        heard_word="mill",
        opener="\"Meet me on the hill,\"",
        ending="flew a red kite high on the hill",
        tags={"mishearing", "hill", "mill", "kite"},
    ),
}

REPAIRS = {
    "sign": Repair(
        id="sign",
        label="sign",
        via="sign",
        tags={"sign"},
    ),
    "helper": Repair(
        id="helper",
        label="helper",
        via="helper",
        tags={"helper"},
    ),
}

HELPER_LABELS = {
    "mother": "mom",
    "father": "dad",
    "vendor": "berry seller",
    "gardener": "gardener",
    "miller": "miller",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Finn", "Noah", "Eli", "Theo", "Max"]
TRAITS = ["careful", "bouncy", "gentle", "curious", "cheerful", "thoughtful"]


def valid_combo(setting: Setting, mixup: Mixup, repair: Repair, helper_type: str) -> bool:
    if mixup.said not in setting.locations or mixup.heard not in setting.locations:
        return False
    if repair.via == "sign":
        return mixup.heard in setting.signs_at
    if repair.via == "helper":
        return mixup.heard in setting.helpers_at and helper_type in setting.helper_types
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mixup_id, mixup in MIXUPS.items():
            for repair_id, repair in REPAIRS.items():
                for helper_type in sorted(setting.helper_types):
                    if valid_combo(setting, mixup, repair, helper_type):
                        combos.append((setting_id, mixup_id, repair_id, helper_type))
    return combos


@dataclass
class StoryParams:
    setting: str
    mixup: str
    repair: str
    helper: str
    speaker_name: str
    speaker_gender: str
    hearer_name: str
    hearer_gender: str
    speaker_trait: str
    hearer_trait: str
    seed: Optional[int] = None


def introduce(world: World, setting: Setting, speaker: Entity, hearer: Entity, said_loc: Location) -> None:
    speaker.memes["joy"] += 1
    hearer.memes["joy"] += 1
    world.say(setting.intro)
    world.say(setting.sparkle)
    world.say(
        f"{speaker.id} and {hearer.id} skipped along with a skip and a sway, "
        f"looking for someplace nice to pause in the play."
    )
    world.say(
        f"They chose {said_loc.the}, {said_loc.detail}, "
        f"as the next little meeting spot later that day."
    )


def send_and_say(world: World, speaker: Entity, hearer: Entity, mixup: Mixup) -> None:
    speaker.memes["confidence"] += 1
    world.say(
        f'"I am going ahead for one quick minute," said {speaker.id}. '
        f'{mixup.opener} {speaker.pronoun()} sang, "please remember the word I say."'
    )
    world.say(
        f"But the music went thump and the chatter went skitter, "
        f"and {hearer.id} heard \"{mixup.heard_word}\" instead of \"{mixup.said_word}\" that day."
    )


def separate(world: World, speaker: Entity, hearer: Entity, said_loc: Location, heard_loc: Location) -> None:
    speaker.attrs["place"] = said_loc.id
    hearer.attrs["place"] = heard_loc.id
    speaker.meters["steps"] += 1
    hearer.meters["steps"] += 1
    hearer.memes["certainty"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"So {speaker.id} ran to {said_loc.the}, light on {speaker.pronoun('possessive')} feet, "
        f"while {hearer.id} hurried to {heard_loc.the}, sure the rhyme was neat."
    )
    world.say(
        f"One waited by the right place. One waited by the wrong. "
        f"The breeze kept blowing softly, but the wait felt rather long."
    )


def notice_missing(world: World, speaker: Entity, hearer: Entity, said_loc: Location, heard_loc: Location) -> None:
    speaker.memes["worry"] += 1
    hearer.memes["worry"] += 1
    world.say(
        f'{speaker.id} looked left and right at {said_loc.the}. "{hearer.id} should be here," '
        f'{speaker.pronoun()} said. Meanwhile, at {heard_loc.the}, {hearer.id} whispered, '
        f'"I hope I heard the meeting place right in my head."'
    )


def repair_by_sign(world: World, hearer: Entity, mixup: Mixup, heard_loc: Location, said_loc: Location) -> None:
    world.facts["clarified"] = True
    hearer.meters["noticed_clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hearer.id} spotted a sign near {heard_loc.the}. "
        f'It showed a map and a bright blue gate with an arrow neat and straight.'
    )
    world.say(
        f'"Oh!" cried {hearer.id}. "I heard {mixup.heard_word}, but {speaker_name(world)} said '
        f'{mixup.said_word}. I mixed the sound and lost the way."'
    )
    hearer.attrs["place"] = said_loc.id
    hearer.meters["steps"] += 1
    world.say(
        f"Off {hearer.pronoun()} went, quick as a kite, "
        f"toward {said_loc.the} in the friendly light."
    )


def repair_by_helper(world: World, hearer: Entity, helper: Entity, mixup: Mixup, heard_loc: Location, said_loc: Location) -> None:
    world.facts["clarified"] = True
    helper.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then a kind {helper.label_word} stood near {heard_loc.the} and gave a patient grin. "
        f'"Who are you trying to find?" {helper.pronoun()} asked.'
    )
    world.say(
        f'"{speaker_name(world)} told me {mixup.heard_word}," said {hearer.id}. '
        f'The {helper.label_word} shook {helper.pronoun("possessive")} head. '
        f'"Maybe you heard a rhyme and not the plan. {mixup.said_word} and {mixup.heard_word} sound close, '
        f'but {speaker_name(world)} is waiting at {said_loc.the}."'
    )
    hearer.attrs["place"] = said_loc.id
    hearer.meters["steps"] += 1
    world.say(
        f"{hearer.id} thanked the {helper.label_word} and scampered away, "
        f"ready to fix the muddle that very same day."
    )


def reunite(world: World, speaker: Entity, hearer: Entity, said_loc: Location) -> None:
    speaker.attrs["place"] = said_loc.id
    hearer.attrs["place"] = said_loc.id
    speaker.memes["relief"] += 1
    hearer.memes["relief"] += 1
    speaker.memes["trust"] += 1
    hearer.memes["trust"] += 1
    world.para()
    world.say(
        f"When {hearer.id} reached {said_loc.the}, {speaker.id} gave a clap. "
        f"Their frowns fell away like rain from a cap."
    )
    world.say(
        f'"I said {world.facts["mixup"].said_word}," said {speaker.id}, "not {world.facts["mixup"].heard_word} at all." '
        f'"Now I know," said {hearer.id}. "Next time I will ask again before I run tall."'
    )


def ending(world: World, setting: Setting, speaker: Entity, hearer: Entity, mixup: Mixup) -> None:
    speaker.memes["joy"] += 1
    hearer.memes["joy"] += 1
    world.say(
        f"Together they laughed at the tiny mistake, "
        f"and soon they {mixup.ending}."
    )
    world.say(
        f"In {setting.label}, under soft sky so great, "
        f"they learned that a question can straighten a fate."
    )


def speaker_name(world: World) -> str:
    sp = world.entities.get("speaker")
    return sp.id if sp else "the other child"


def tell(
    setting: Setting,
    mixup: Mixup,
    repair: Repair,
    helper_type: str,
    speaker_name_value: str,
    speaker_gender: str,
    hearer_name_value: str,
    hearer_gender: str,
    speaker_trait: str,
    hearer_trait: str,
) -> World:
    world = World()
    speaker = world.add(Entity(
        id="speaker",
        kind="character",
        type=speaker_gender,
        label=speaker_name_value,
        role="speaker",
        attrs={"name": speaker_name_value, "trait": speaker_trait, "place": ""},
    ))
    hearer = world.add(Entity(
        id="hearer",
        kind="character",
        type=hearer_gender,
        label=hearer_name_value,
        role="hearer",
        attrs={"name": hearer_name_value, "trait": hearer_trait, "place": ""},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type if helper_type in {"mother", "father"} else "person",
        label=HELPER_LABELS[helper_type],
        role="helper",
        attrs={"helper_type": helper_type},
    ))
    said_loc = LOCATIONS[mixup.said]
    heard_loc = LOCATIONS[mixup.heard]

    world.facts.update(
        setting=setting,
        mixup=mixup,
        repair=repair,
        helper_type=helper_type,
        said_loc=said_loc,
        heard_loc=heard_loc,
        clarified=False,
    )

    introduce(world, setting, speaker, hearer, said_loc)
    world.para()
    send_and_say(world, speaker, hearer, mixup)
    separate(world, speaker, hearer, said_loc, heard_loc)
    notice_missing(world, speaker, hearer, said_loc, heard_loc)

    world.para()
    if repair.via == "sign":
        repair_by_sign(world, hearer, mixup, heard_loc, said_loc)
    else:
        repair_by_helper(world, hearer, helper, mixup, heard_loc, said_loc)

    reunite(world, speaker, hearer, said_loc)
    ending(world, setting, speaker, hearer, mixup)

    world.facts.update(
        speaker=speaker,
        hearer=hearer,
        helper=helper,
        outcome="clarified" if world.facts["clarified"] else "lost",
    )
    return world


KNOWLEDGE = {
    "mishearing": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what another person meant. It can happen if words sound alike or if a message is not heard clearly.",
        )
    ],
    "sign": [
        (
            "Why can a sign help when someone is confused?",
            "A sign gives clear information with words or pictures. It can help people check where to go when they are not sure.",
        )
    ],
    "helper": [
        (
            "What should you do if you are not sure where to go?",
            "You should stop and ask a trusted grown-up or helper. Asking a question is a smart way to stay safe and find the right place.",
        )
    ],
    "gate": [
        (
            "What is a gate?",
            "A gate is a small door or opening in a fence or wall. People use it to go in or out of a place.",
        )
    ],
    "bridge": [
        (
            "What is a bridge?",
            "A bridge is something built so people can cross over water, a road, or a dip in the ground. It helps you get from one side to the other.",
        )
    ],
    "hill": [
        (
            "What is a hill?",
            "A hill is a piece of land that rises up higher than the ground around it. It is smaller and gentler than a mountain.",
        )
    ],
    "ducks": [
        (
            "Where do ducks often like to be?",
            "Ducks often like ponds, lakes, and slow water where they can paddle and look for food. They are water birds.",
        )
    ],
    "kite": [
        (
            "Why does a kite fly better in a breezy place?",
            "A kite needs moving air to lift it up. A breeze pushes on the kite and helps it float in the sky.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mishearing", "sign", "helper", "gate", "bridge", "hill", "ducks", "kite"]


def pair_noun(speaker: Entity, hearer: Entity) -> str:
    if speaker.type == "boy" and hearer.type == "boy":
        return "two boys"
    if speaker.type == "girl" and hearer.type == "girl":
        return "two girls"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    mixup = f["mixup"]
    repair = f["repair"]
    speaker = f["speaker"]
    hearer = f["hearer"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "someplace" and centers on a misunderstanding at {setting.label}.',
        f"Tell a gentle rhyming story where {speaker.label} says {mixup.said_word}, but {hearer.label} hears {mixup.heard_word}, and the mistake is fixed by a {repair.label}.",
        f"Write a child-facing poem-story about two children who get separated by a misheard place name and find each other again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    speaker = f["speaker"]
    hearer = f["hearer"]
    setting = f["setting"]
    mixup = f["mixup"]
    said_loc = f["said_loc"]
    heard_loc = f["heard_loc"]
    repair = f["repair"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(speaker, hearer)}, {speaker.label} and {hearer.label}. They were trying to meet again in {setting.label}.",
        ),
        (
            "What was the misunderstanding?",
            f"{speaker.label} said {mixup.said_word}, but {hearer.label} heard {mixup.heard_word}. The two words sounded alike, so they went to different places.",
        ),
        (
            f"Why did the children end up apart?",
            f"They ended up apart because {speaker.label} went to {said_loc.the} while {hearer.label} hurried to {heard_loc.the}. The mix-up came from a misheard rhyming word.",
        ),
    ]
    if repair.via == "sign":
        qa.append(
            (
                f"How was the mistake fixed?",
                f"The mistake was fixed when {hearer.label} noticed a sign near {heard_loc.the}. The sign showed where {said_loc.the} was, so {hearer.pronoun()} realized what {speaker.label} had really said.",
            )
        )
    else:
        qa.append(
            (
                f"How was the mistake fixed?",
                f"The mistake was fixed when a {helper.label_word} helped {hearer.label}. The helper explained that {mixup.said_word} and {mixup.heard_word} sounded close but meant different places.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The children found each other at {said_loc.the} and felt relieved. Then they {mixup.ending}, which showed the misunderstanding was over.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["mixup"].tags) | set(f["repair"].tags)
    if f["mixup"].id == "bridge_ridge":
        tags.add("ducks")
    if f["mixup"].id == "hill_mill":
        tags.add("kite")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} repair={world.facts.get('repair').id}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="fair",
        mixup="gate_crate",
        repair="sign",
        helper="vendor",
        speaker_name="Lily",
        speaker_gender="girl",
        hearer_name="Ben",
        hearer_gender="boy",
        speaker_trait="cheerful",
        hearer_trait="curious",
    ),
    StoryParams(
        setting="park",
        mixup="bridge_ridge",
        repair="helper",
        helper="gardener",
        speaker_name="Mia",
        speaker_gender="girl",
        hearer_name="Leo",
        hearer_gender="boy",
        speaker_trait="gentle",
        hearer_trait="bouncy",
    ),
    StoryParams(
        setting="meadow",
        mixup="hill_mill",
        repair="helper",
        helper="miller",
        speaker_name="Theo",
        speaker_gender="boy",
        hearer_name="Ruby",
        hearer_gender="girl",
        speaker_trait="thoughtful",
        hearer_trait="cheerful",
    ),
    StoryParams(
        setting="park",
        mixup="bridge_ridge",
        repair="sign",
        helper="mother",
        speaker_name="Ava",
        speaker_gender="girl",
        hearer_name="Nora",
        hearer_gender="girl",
        speaker_trait="careful",
        hearer_trait="curious",
    ),
]


def explain_rejection(setting: Setting, mixup: Mixup, repair: Repair, helper_type: str) -> str:
    if mixup.said not in setting.locations or mixup.heard not in setting.locations:
        return (
            f"(No story: {setting.label} does not contain both {mixup.said_word} and {mixup.heard_word}, "
            f"so this misunderstanding would not make sense there.)"
        )
    if repair.via == "sign" and mixup.heard not in setting.signs_at:
        return (
            f"(No story: there is no useful sign near the {mixup.heard_word} in {setting.label}, "
            f"so the misunderstanding cannot be fixed that way.)"
        )
    if repair.via == "helper":
        if mixup.heard not in setting.helpers_at:
            return (
                f"(No story: there is no helper near the {mixup.heard_word} in {setting.label}, "
                f"so the child would have nobody to ask.)"
            )
        if helper_type not in setting.helper_types:
            allowed = ", ".join(sorted(setting.helper_types))
            return (
                f"(No story: helper '{helper_type}' does not fit {setting.label}. "
                f"Try one of: {allowed}.)"
            )
    return "(No story: this combination is not reasonable in this tiny world.)"


ASP_RULES = r"""
has_place(S, M) :- setting(S), mixup(M), said(M, L), in_setting(S, L).
has_heard(S, M) :- setting(S), mixup(M), heard(M, L), in_setting(S, L).
base_ok(S, M) :- has_place(S, M), has_heard(S, M).

valid(S, M, sign, H) :-
    base_ok(S, M),
    repair(sign),
    helper(H),
    heard(M, L),
    sign_at(S, L),
    helper_allowed(S, H).

valid(S, M, helper, H) :-
    base_ok(S, M),
    repair(helper),
    helper(H),
    heard(M, L),
    helper_at(S, L),
    helper_allowed(S, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for loc in sorted(setting.locations):
            lines.append(asp.fact("in_setting", setting_id, loc))
        for loc in sorted(setting.signs_at):
            lines.append(asp.fact("sign_at", setting_id, loc))
        for loc in sorted(setting.helpers_at):
            lines.append(asp.fact("helper_at", setting_id, loc))
        for helper_type in sorted(setting.helper_types):
            lines.append(asp.fact("helper_allowed", setting_id, helper_type))
    for mixup_id, mixup in MIXUPS.items():
        lines.append(asp.fact("mixup", mixup_id))
        lines.append(asp.fact("said", mixup_id, mixup.said))
        lines.append(asp.fact("heard", mixup_id, mixup.heard))
    for repair_id in REPAIRS:
        lines.append(asp.fact("repair", repair_id))
    helpers = sorted(set(h for s in SETTINGS.values() for h in s.helper_types))
    for helper_type in helpers:
        lines.append(asp.fact("helper", helper_type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python gate and ASP gate:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    smoke_cases = [CURATED[0]]
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        default_params.seed = 0
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params() raised {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story or "someplace" not in sample.story.lower():
                raise StoryError("story missing text or required seed word")
            buf = io.StringIO()
            with redirect_stdout(buf):
                emit(sample, trace=False, qa=True, header=f"### smoke {idx}")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming misunderstanding storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mixup", choices=MIXUPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--helper", choices=sorted(set(h for s in SETTINGS.values() for h in s.helper_types)))
    ap.add_argument("--speaker-name")
    ap.add_argument("--hearer-name")
    ap.add_argument("--speaker-gender", choices=["girl", "boy"])
    ap.add_argument("--hearer-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible scenario set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mixup and args.repair and args.helper:
        if not valid_combo(SETTINGS[args.setting], MIXUPS[args.mixup], REPAIRS[args.repair], args.helper):
            raise StoryError(explain_rejection(SETTINGS[args.setting], MIXUPS[args.mixup], REPAIRS[args.repair], args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mixup is None or combo[1] == args.mixup)
        and (args.repair is None or combo[2] == args.repair)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        if args.setting and args.mixup and args.repair:
            helper_probe = args.helper or next(iter(sorted(SETTINGS[args.setting].helper_types)))
            raise StoryError(explain_rejection(SETTINGS[args.setting], MIXUPS[args.mixup], REPAIRS[args.repair], helper_probe))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mixup_id, repair_id, helper_type = rng.choice(sorted(combos))
    speaker_gender = args.speaker_gender or rng.choice(["girl", "boy"])
    hearer_gender = args.hearer_gender or rng.choice(["girl", "boy"])
    speaker_name_value = args.speaker_name or pick_name(rng, speaker_gender)
    hearer_name_value = args.hearer_name or pick_name(rng, hearer_gender, avoid=speaker_name_value)
    speaker_trait = rng.choice(TRAITS)
    hearer_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        mixup=mixup_id,
        repair=repair_id,
        helper=helper_type,
        speaker_name=speaker_name_value,
        speaker_gender=speaker_gender,
        hearer_name=hearer_name_value,
        hearer_gender=hearer_gender,
        speaker_trait=speaker_trait,
        hearer_trait=hearer_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.mixup not in MIXUPS:
        raise StoryError(f"(Invalid mixup: {params.mixup})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Invalid repair: {params.repair})")
    if params.helper not in HELPER_LABELS:
        raise StoryError(f"(Invalid helper: {params.helper})")

    setting = SETTINGS[params.setting]
    mixup = MIXUPS[params.mixup]
    repair = REPAIRS[params.repair]
    if not valid_combo(setting, mixup, repair, params.helper):
        raise StoryError(explain_rejection(setting, mixup, repair, params.helper))

    world = tell(
        setting=setting,
        mixup=mixup,
        repair=repair,
        helper_type=params.helper,
        speaker_name_value=params.speaker_name,
        speaker_gender=params.speaker_gender,
        hearer_name_value=params.hearer_name,
        hearer_gender=params.hearer_gender,
        speaker_trait=params.speaker_trait,
        hearer_trait=params.hearer_trait,
    )

    # Replace entity ids with display names in rendered story.
    story = world.render()
    story = story.replace("speaker", params.speaker_name).replace("hearer", params.hearer_name)

    # Also store display names directly for QA generators.
    world.facts["speaker"].id = params.speaker_name
    world.facts["hearer"].id = params.hearer_name

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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mixup, repair, helper) combos:\n")
        for setting_id, mixup_id, repair_id, helper_type in combos:
            print(f"  {setting_id:7} {mixup_id:13} {repair_id:6} {helper_type}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.speaker_name} & {p.hearer_name}: {p.mixup} at {p.setting} via {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
