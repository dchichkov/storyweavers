#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py
===================================================================

A small story world about a child riding a tandem bicycle with a helper to carry
a kiwi treat across the neighborhood. The core value is cooperation: on a tandem,
two people only move smoothly when they listen to each other and pedal together.

The world model tracks physical state (wobble, bruises, spills, arrival) and
emotional state (eagerness, worry, shame, relief, pride). A rough route plus a
fragile kiwi snack can turn a rushed ride into a small mess, but the ending still
shows a gentle moral turn: the child tells the truth, accepts help, and shares
what is left.

Run it
------
    python storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py --route cobbles --cargo kiwi_slices --choice race
    python storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py --cargo kiwi_juice
    python storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tandem_kiwi_moral_value_slice_of_life.py --verify
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
        female = {"girl", "mother", "woman", "aunt", "grandmother", "teacher"}
        male = {"boy", "father", "man", "uncle", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.label or self.type)


@dataclass
class Route:
    id: str
    place: str
    scene: str
    bumps: int
    slope: int
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    container: str
    fragility: int
    share_word: str
    impossible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Recipient:
    id: str
    label: str
    type: str
    waiting_place: str
    reason: str
    thanks_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    label: str
    careful: bool
    pace: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    route: str
    cargo: str
    recipient: str
    choice: str
    child_name: str
    child_gender: str
    partner_name: str
    partner_type: str
    seed: Optional[int] = None


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


def _r_wobble_fear(world: World) -> list[str]:
    out: list[str] = []
    basket = world.get("basket")
    if basket.meters["wobble"] >= THRESHOLD:
        sig = ("fear", "basket")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["worry"] += 1
            world.get("partner").memes["worry"] += 1
            out.append("__wobble__")
    return out


def _r_spill_shame(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["spilled"] >= THRESHOLD:
        sig = ("shame", "cargo")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["shame"] += 1
            world.get("recipient").memes["disappointment"] += 1
            out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble_fear", tag="physical", apply=_r_wobble_fear),
    Rule(name="spill_shame", tag="social", apply=_r_spill_shame),
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


ROUTES = {
    "riverside": Route(
        id="riverside",
        place="the riverside path",
        scene="The morning river shone between willow leaves.",
        bumps=0,
        slope=1,
        line="The path was smooth, with only one gentle rise near the bridge.",
        tags={"bike", "outside"},
    ),
    "bridge": Route(
        id="bridge",
        place="the little bridge road",
        scene="The houses looked sleepy, and the bridge rail flashed silver in the sun.",
        bumps=1,
        slope=1,
        line="The road narrowed at the bridge, so the riders had to keep one calm rhythm.",
        tags={"bike", "outside"},
    ),
    "cobbles": Route(
        id="cobbles",
        place="the cobbled lane",
        scene="The lane curved past flower pots and old brick walls.",
        bumps=2,
        slope=1,
        line="The stones made the wheels tap and rattle under the bicycle.",
        tags={"bike", "outside"},
    ),
}

CARGOES = {
    "kiwi_slices": Cargo(
        id="kiwi_slices",
        label="kiwi slices",
        phrase="a little box of kiwi slices",
        container="a paper box",
        fragility=2,
        share_word="sweet green kiwi slices",
        impossible=False,
        tags={"kiwi", "fruit", "sharing"},
    ),
    "whole_kiwis": Cargo(
        id="whole_kiwis",
        label="whole kiwis",
        phrase="three fuzzy kiwi fruits",
        container="a cloth bag",
        fragility=0,
        share_word="cool kiwi fruits",
        impossible=False,
        tags={"kiwi", "fruit", "sharing"},
    ),
    "kiwi_muffins": Cargo(
        id="kiwi_muffins",
        label="kiwi muffins",
        phrase="two kiwi muffins",
        container="a tin",
        fragility=1,
        share_word="warm kiwi muffins",
        impossible=False,
        tags={"kiwi", "baking", "sharing"},
    ),
    "kiwi_juice": Cargo(
        id="kiwi_juice",
        label="kiwi juice",
        phrase="a glass jar of kiwi juice without a lid",
        container="an open glass jar",
        fragility=3,
        share_word="kiwi juice",
        impossible=True,
        tags={"kiwi", "drink"},
    ),
}

RECIPIENTS = {
    "grandma": Recipient(
        id="grandma",
        label="Grandma",
        type="grandmother",
        waiting_place="on a shady park bench",
        reason="because Grandma had watered the tomatoes all morning",
        thanks_line='"This tastes like a kind morning," Grandma said.',
        tags={"family", "kindness"},
    ),
    "neighbor": Recipient(
        id="neighbor",
        label="Niko",
        type="boy",
        waiting_place="by the apartment garden gate",
        reason="because Niko had just moved in and did not know many people yet",
        thanks_line='"I was hoping someone would sit with me," Niko said.',
        tags={"friendship", "kindness"},
    ),
    "teacher": Recipient(
        id="teacher",
        label="Ms. June",
        type="teacher",
        waiting_place="outside the library steps",
        reason="because Ms. June always saved the best picture books for rainy afternoons",
        thanks_line='"You two remembered me," Ms. June said with a smile.',
        tags={"community", "kindness"},
    ),
}

CHOICES = {
    "match": Choice(
        id="match",
        label="match pace",
        careful=True,
        pace="slow and together",
        tags={"cooperation"},
    ),
    "race": Choice(
        id="race",
        label="race ahead",
        careful=False,
        pace="too fast for the basket",
        tags={"impatience"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
PARTNERS = [
    ("Mara", "mother"),
    ("Dad", "father"),
    ("Aunt Jo", "aunt"),
    ("Uncle Ray", "uncle"),
]


def cargo_risk(route: Route, cargo: Cargo, choice: Choice) -> int:
    return route.bumps + route.slope + cargo.fragility + (1 if not choice.careful else 0)


def valid_combo(route: Route, cargo: Cargo) -> bool:
    return not cargo.impossible


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_id, route in ROUTES.items():
        for cargo_id, cargo in CARGOES.items():
            if not valid_combo(route, cargo):
                continue
            for recipient_id in RECIPIENTS:
                for choice_id in CHOICES:
                    combos.append((route_id, cargo_id, recipient_id, choice_id))
    return combos


def causes_spill(route: Route, cargo: Cargo, choice: Choice) -> bool:
    return cargo_risk(route, cargo, choice) >= 4


def predict_ride(world: World, route: Route, cargo_cfg: Cargo, choice: Choice) -> dict:
    sim = world.copy()
    basket = sim.get("basket")
    cargo = sim.get("cargo")
    risk = cargo_risk(route, cargo_cfg, choice)
    basket.meters["wobble"] += 1 if risk >= 3 else 0
    if risk >= 4:
        cargo.meters["spilled"] += 1
        cargo.meters["bruised"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": basket.meters["wobble"] >= THRESHOLD,
        "spill": cargo.meters["spilled"] >= THRESHOLD,
    }


def setup_scene(world: World, route: Route, cargo_cfg: Cargo, recipient_cfg: Recipient) -> None:
    child = world.get("child")
    partner = world.get("partner")
    tandem = world.get("tandem")
    world.say(
        f"On a bright morning, {child.id} and {partner.label} wheeled {tandem.phrase} out of the yard."
    )
    world.say(
        f"In the front basket sat {cargo_cfg.phrase}, meant for {recipient_cfg.label} {recipient_cfg.reason}."
    )
    world.say(route.scene)
    child.memes["eagerness"] += 1
    partner.memes["care"] += 1


def explain_tandem(world: World) -> None:
    child = world.get("child")
    partner = world.get("partner")
    world.say(
        f"{child.id} liked the tandem best because {child.pronoun()} could feel {partner.label}'s steady pedaling behind {child.pronoun('object')}."
    )
    world.say("On a tandem, one rider can start the song of the wheels, but two riders have to keep the beat.")


def begin_ride(world: World, route: Route, choice: Choice) -> None:
    child = world.get("child")
    partner = world.get("partner")
    world.say(
        f"They set off toward {route.place}. {route.line}"
    )
    if choice.careful:
        world.say(
            f'"Easy now," {partner.label} said. "{choice.pace.capitalize()}." {child.id} nodded and listened for the soft click of matching pedals.'
        )
        world.get("tandem").meters["steady"] += 1
        child.memes["cooperation"] += 1
    else:
        world.say(
            f'{child.id} felt the wind on {child.pronoun("possessive")} cheeks and wanted to hurry. "{recipient_name(world)} will like it if we get there first!" {child.pronoun()} said.'
        )
        world.say(f'"Not first," {partner.label} answered. "Just together."')
        child.memes["impatience"] += 1


def recipient_name(world: World) -> str:
    return world.get("recipient").label


def ride_challenge(world: World, route: Route, cargo_cfg: Cargo, choice: Choice) -> None:
    basket = world.get("basket")
    cargo = world.get("cargo")
    risk = cargo_risk(route, cargo_cfg, choice)
    if risk >= 3:
        basket.meters["wobble"] += 1
    if risk >= 4:
        cargo.meters["spilled"] += 1
        cargo.meters["bruised"] += 1
    propagate(world, narrate=False)

    child = world.get("child")
    partner = world.get("partner")
    if basket.meters["wobble"] >= THRESHOLD and cargo.meters["spilled"] < THRESHOLD:
        world.say(
            "Halfway there, the basket gave a little shake. The box bumped the wicker sides, then settled again."
        )
        world.say(
            f'{child.id} tightened {child.pronoun("possessive")} hands on the handlebar, and {partner.label} slowed the pedals until the bicycle found its balance.'
        )
        child.memes["learning"] += 1
        partner.memes["trust"] += 1
        world.get("tandem").meters["steady"] += 1
    elif cargo.meters["spilled"] >= THRESHOLD:
        world.say(
            "At the rattliest part of the lane, the basket tipped sideways."
        )
        world.say(
            f"The {cargo_cfg.container} slid, opened, and some of the kiwi tumbled into the corner of the basket."
        )
        world.say(
            f'{child.id} felt a hot little pinch in {child.pronoun("possessive")} chest. All at once, hurrying did not feel clever anymore.'
        )


def arrive(world: World, recipient_cfg: Recipient) -> None:
    world.get("tandem").meters["arrived"] += 1
    world.say(
        f"When they reached the end of the ride, {recipient_cfg.label} was waiting {recipient_cfg.waiting_place}."
    )


def truth_and_repair(world: World, cargo_cfg: Cargo) -> None:
    child = world.get("child")
    partner = world.get("partner")
    recipient = world.get("recipient")
    child.memes["honesty"] += 1
    partner.memes["pride"] += 1
    recipient.memes["warmth"] += 1
    world.say(
        f'{child.id} looked at the basket and then up at {recipient.label}. "I tried to rush," {child.pronoun()} said quietly. "Some of the kiwi got squished."'
    )
    world.say(
        f"{partner.label} did not scold. {partner.pronoun().capitalize()} set the bicycle stand, straightened the box, and helped choose the neat pieces that were still good."
    )
    world.say(
        f'{recipient.label} smiled and said there was still plenty for a small shared snack. Telling the truth made the morning feel lighter again.'
    )
    world.get("cargo").meters["shared"] += 1
    world.facts["repair"] = "sorted the good pieces from the squished ones"


def calm_arrival(world: World, cargo_cfg: Cargo) -> None:
    child = world.get("child")
    recipient = world.get("recipient")
    child.memes["pride"] += 1
    recipient.memes["warmth"] += 1
    world.say(
        f"The basket arrived neat and still. {child.id} lifted out {cargo_cfg.phrase} as carefully as if it were a tiny present."
    )
    world.say(recipient_thanks(world))
    world.get("cargo").meters["shared"] += 1


def recipient_thanks(world: World) -> str:
    return world.facts["recipient_cfg"].thanks_line


def ending_image(world: World, cargo_cfg: Cargo) -> None:
    child = world.get("child")
    partner = world.get("partner")
    recipient = world.get("recipient")
    spilled = world.get("cargo").meters["spilled"] >= THRESHOLD
    world.para()
    if spilled:
        world.say(
            f"Soon the three of them were sharing the best pieces of {cargo_cfg.share_word}, with the tandem resting nearby and one wheel still ticking softly as it cooled."
        )
        world.say(
            f"{child.id} leaned against the front bar and remembered what the ride had taught: going kindly together mattered more than getting there fast."
        )
    else:
        world.say(
            f"Soon the three of them were sharing {cargo_cfg.share_word} in the shade, and the tandem stood beside the bench as if it too had done its small good deed."
        )
        world.say(
            f"{child.id} could still feel the easy rhythm of the pedals in {child.pronoun('possessive')} legs. Working together had carried the kindness all the way there."
        )
    partner.memes["love"] += 1
    recipient.memes["belonging"] += 1


def tell(route: Route, cargo_cfg: Cargo, recipient_cfg: Recipient, choice: Choice,
         child_name: str, child_gender: str, partner_name: str, partner_type: str) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=["eager"],
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_type,
        label=partner_name,
        phrase=partner_name,
        role="partner",
        traits=["steady"],
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=recipient_cfg.type,
        label=recipient_cfg.label,
        phrase=recipient_cfg.label,
        role="recipient",
        tags=set(recipient_cfg.tags),
    ))
    tandem = world.add(Entity(
        id="tandem",
        type="bicycle",
        label="tandem",
        phrase="the cherry-red tandem",
        role="vehicle",
        tags={"tandem", "bike"},
    ))
    basket = world.add(Entity(
        id="basket",
        type="basket",
        label="basket",
        phrase="the front basket",
        role="container",
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="food",
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        role="cargo",
        tags=set(cargo_cfg.tags),
    ))

    world.facts.update(
        route_cfg=route,
        cargo_cfg=cargo_cfg,
        recipient_cfg=recipient_cfg,
        choice_cfg=choice,
        child=child,
        partner=partner,
        recipient=recipient,
    )

    setup_scene(world, route, cargo_cfg, recipient_cfg)
    explain_tandem(world)

    world.para()
    begin_ride(world, route, choice)
    ride_challenge(world, route, cargo_cfg, choice)

    world.para()
    arrive(world, recipient_cfg)
    if cargo.meters["spilled"] >= THRESHOLD:
        truth_and_repair(world, cargo_cfg)
        outcome = "spill"
    else:
        calm_arrival(world, cargo_cfg)
        outcome = "smooth"

    ending_image(world, cargo_cfg)
    world.facts.update(
        outcome=outcome,
        spilled=cargo.meters["spilled"] >= THRESHOLD,
        shared=cargo.meters["shared"] >= THRESHOLD,
        truthful=child.memes["honesty"] >= THRESHOLD,
        cooperative=child.memes["cooperation"] >= THRESHOLD or child.memes["learning"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "tandem": [(
        "What is a tandem bicycle?",
        "A tandem bicycle is a bike made for two riders. The riders pedal together, so they have to keep the same rhythm."
    )],
    "kiwi": [(
        "What is a kiwi fruit?",
        "A kiwi is a small brown fruit with bright green flesh inside. It tastes sweet and a little tangy."
    )],
    "cooperation": [(
        "Why do people need to cooperate on a tandem?",
        "On a tandem, both riders help move and balance the bike. If they work together, the ride feels smoother and safer."
    )],
    "honesty": [(
        "Why is it good to tell the truth after a mistake?",
        "Telling the truth helps other people understand what happened. It also makes it easier to fix the problem together."
    )],
    "sharing": [(
        "Why does sharing food feel kind?",
        "Sharing lets someone else enjoy something good with you. It can make an ordinary snack feel warm and welcoming."
    )],
    "bike": [(
        "Why should riders go carefully over bumps?",
        "Bumps can make a bicycle wobble and shake what it is carrying. Slowing down helps the riders keep control."
    )],
}
KNOWLEDGE_ORDER = ["tandem", "kiwi", "bike", "cooperation", "honesty", "sharing"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    recipient_cfg = world.facts["recipient_cfg"]
    cargo_cfg = world.facts["cargo_cfg"]
    route = world.facts["route_cfg"]
    if world.facts["outcome"] == "spill":
        return [
            'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "tandem" and "kiwi" and teaches cooperation.',
            f"Tell a neighborhood story where {child.label} rides a tandem to bring {cargo_cfg.label} to {recipient_cfg.label}, rushes over {route.place}, and then tells the truth about the small mess.",
            "Write a warm moral-value story where hurrying causes a problem, but honesty and teamwork turn the ending kind again.",
        ]
    return [
        'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "tandem" and "kiwi" and teaches cooperation.',
        f"Tell a neighborhood story where {child.label} rides a tandem to bring {cargo_cfg.label} to {recipient_cfg.label} and learns that going together matters more than going fast.",
        "Write a warm moral-value story with a small errand, a calm grown-up helper, and a final shared snack.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    partner = world.facts["partner"]
    recipient = world.facts["recipient"]
    cargo_cfg = world.facts["cargo_cfg"]
    route = world.facts["route_cfg"]
    choice = world.facts["choice_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {partner.label}, and {recipient.label}. {child.label} and {partner.label} ride the tandem together to bring a kiwi treat."
        ),
        (
            f"What were they carrying on the tandem?",
            f"They were carrying {cargo_cfg.phrase} in the front basket. It was meant to be a small kind gift for {recipient.label}."
        ),
        (
            "Why did the tandem matter in the story?",
            f"The tandem mattered because it only rides smoothly when both people work together. That made the trip itself part of the lesson."
        ),
    ]
    if world.facts["spilled"]:
        qa.append((
            f"What went wrong on the way to {recipient.label}?",
            f"The ride got too bumpy for the basket because {child.label} tried to go {choice.pace}. The container tipped, and some of the kiwi was squished."
        ))
        qa.append((
            f"What did {child.label} do after the spill?",
            f"{child.label} told the truth instead of pretending nothing had happened. That honesty let {partner.label} and {recipient.label} help fix the small problem together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the three of them still sharing kiwi beside the parked tandem. The ending shows that kindness and honesty were stronger than the little accident."
        ))
    else:
        qa.append((
            f"How did they keep the kiwi safe on {route.place}?",
            f"They listened to each other and pedaled in one calm rhythm. Going carefully kept the basket steady and the kiwi neat."
        ))
        qa.append((
            f"How did {recipient.label} feel when they arrived?",
            f"{recipient.label} felt remembered and cared for. The careful ride turned the snack into a real act of kindness."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child.label} learned that working together mattered more than rushing. The smooth ride proved that cooperation can carry a small kindness all the way home."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tandem", "kiwi", "bike", "sharing"}
    if world.facts["spilled"]:
        tags.add("honesty")
    else:
        tags.add("cooperation")
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(cargo_cfg: Cargo) -> str:
    return (
        f"(No story: {cargo_cfg.phrase} rides in {cargo_cfg.container}, which is too spill-prone for a tandem. "
        "Pick a snack in a closed box, tin, or bag so the small trip stays believable.)"
    )


def outcome_of(params: StoryParams) -> str:
    route = ROUTES[params.route]
    cargo_cfg = CARGOES[params.cargo]
    choice = CHOICES[params.choice]
    return "spill" if causes_spill(route, cargo_cfg, choice) else "smooth"


ASP_RULES = r"""
valid(R, C, Rcpt, Ch) :- route(R), cargo(C), recipient(Rcpt), choice(Ch), not impossible(C).

risk(R, C, Ch, N) :- route_bumps(R, B), route_slope(R, S), fragility(C, F), careful(Ch, Care), rush_bonus(Care, X), N = B + S + F + X.
rush_bonus(yes, 0).
rush_bonus(no, 1).

spill(R, C, Ch) :- risk(R, C, Ch, N), N >= 4.
outcome(R, C, Ch, spill) :- spill(R, C, Ch).
outcome(R, C, Ch, smooth) :- valid(R, C, _, Ch), not spill(R, C, Ch).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_bumps", route_id, route.bumps))
        lines.append(asp.fact("route_slope", route_id, route.slope))
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("fragility", cargo_id, cargo.fragility))
        if cargo.impossible:
            lines.append(asp.fact("impossible", cargo_id))
    for recipient_id in RECIPIENTS:
        lines.append(asp.fact("recipient", recipient_id))
    for choice_id, choice in CHOICES.items():
        lines.append(asp.fact("choice", choice_id))
        lines.append(asp.fact("careful", choice_id, "yes" if choice.careful else "no"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_choice", params.choice),
        f"picked_outcome(O) :- outcome({params.route}, {params.cargo}, {params.choice}, O).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if "tandem" not in sample.story.lower() or "kiwi" not in sample.story.lower():
        raise StoryError("Smoke test failed: story missing required seed words.")
    if not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: QA generation did not produce items.")


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    scenarios = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    bad = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated a normal story and QA.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        route="riverside",
        cargo="whole_kiwis",
        recipient="grandma",
        choice="match",
        child_name="Lily",
        child_gender="girl",
        partner_name="Dad",
        partner_type="father",
    ),
    StoryParams(
        route="bridge",
        cargo="kiwi_muffins",
        recipient="teacher",
        choice="match",
        child_name="Ben",
        child_gender="boy",
        partner_name="Aunt Jo",
        partner_type="aunt",
    ),
    StoryParams(
        route="cobbles",
        cargo="kiwi_slices",
        recipient="neighbor",
        choice="race",
        child_name="Mia",
        child_gender="girl",
        partner_name="Uncle Ray",
        partner_type="uncle",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tandem ride, a kiwi snack, and a small lesson in cooperation."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo:
        cargo_cfg = CARGOES[args.cargo]
        if cargo_cfg.impossible:
            raise StoryError(explain_rejection(cargo_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.recipient is None or combo[2] == args.recipient)
        and (args.choice is None or combo[3] == args.choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, cargo_id, recipient_id, choice_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or pick_name(rng, gender)
    partner_name, partner_type = rng.choice(PARTNERS)

    return StoryParams(
        route=route_id,
        cargo=cargo_id,
        recipient=recipient_id,
        choice=choice_id,
        child_name=child_name,
        child_gender=gender,
        partner_name=partner_name,
        partner_type=partner_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        route = ROUTES[params.route]
        cargo_cfg = CARGOES[params.cargo]
        recipient_cfg = RECIPIENTS[params.recipient]
        choice = CHOICES[params.choice]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from err

    if cargo_cfg.impossible:
        raise StoryError(explain_rejection(cargo_cfg))

    world = tell(
        route=route,
        cargo_cfg=cargo_cfg,
        recipient_cfg=recipient_cfg,
        choice=choice,
        child_name=params.child_name,
        child_gender=params.child_gender,
        partner_name=params.partner_name,
        partner_type=params.partner_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, cargo, recipient, choice) combos:\n")
        for route_id, cargo_id, recipient_id, choice_id in combos:
            outcome = "spill" if causes_spill(ROUTES[route_id], CARGOES[cargo_id], CHOICES[choice_id]) else "smooth"
            print(f"  {route_id:10} {cargo_id:12} {recipient_id:10} {choice_id:6} -> {outcome}")
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
            header = f"### {p.child_name}: {p.cargo} on {p.route} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
