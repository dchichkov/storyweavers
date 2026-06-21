#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py
=========================================================

A standalone storyworld about a child who wants to use a stump as a tiny stage
for a silly rhyming dialogue show. The setup is playful and comic, but the
world still enforces ordinary reasonableness: a slippery stump should be dried,
a muddy ring needs a mat, and marching ants mean the show should move.

The stories are state-driven. A child may either listen to a warning right away
or try first and have a small comic mishap, after which the sensible fix lets
the rhyme show go on safely.

Run it
------
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py --show king --trouble mossy
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py --trouble ants --fix mat
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py --all
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py --asp
    python storyworlds/worlds/gpt-5.4/stump_rhyme_dialogue_comedy.py --verify
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
CAREFUL_TRAITS = {"careful", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ShowTheme:
    id: str
    title: str
    costume: str
    opening: str
    reply: str
    extra_rhyme: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    risk: str
    warning: str
    mishap: str
    safe_after: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    works_for: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
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


def _r_embarrassment(world: World) -> list[str]:
    performer = world.entities.get("performer")
    if performer is None:
        return []
    if performer.meters["mishap"] < THRESHOLD:
        return []
    sig = ("embarrassment", performer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    performer.memes["embarrassed"] += 1
    performer.memes["need_help"] += 1
    return []


def _r_laughter(world: World) -> list[str]:
    performer = world.entities.get("performer")
    partner = world.entities.get("partner")
    if performer is None or partner is None:
        return []
    if performer.meters["mishap"] < THRESHOLD:
        return []
    sig = ("laughter", performer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    performer.memes["giggles"] += 1
    partner.memes["giggles"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="embarrassment", tag="social", apply=_r_embarrassment),
    Rule(name="laughter", tag="emotion", apply=_r_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def fix_works(trouble: Trouble, fix: Fix) -> bool:
    return trouble.id in fix.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for trouble_id in sorted(setting.affords):
            trouble = TROUBLES[trouble_id]
            for show_id in SHOWS:
                for fix_id, fix in FIXES.items():
                    if fix_works(trouble, fix):
                        combos.append((setting_id, show_id, trouble_id, fix_id))
    return combos


def would_listen(relation: str, performer_age: int, partner_age: int, trait: str) -> bool:
    if relation == "siblings" and partner_age > performer_age:
        return True
    return trait in CAREFUL_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "listened" if would_listen(
        params.relation,
        params.performer_age,
        params.partner_age,
        params.performer_trait,
    ) else "mishap"


def predict_trouble(world: World, trouble: Trouble) -> dict:
    sim = world.copy()
    performer = sim.get("performer")
    performer.meters["mishap"] += 1
    performer.meters[trouble.risk] += 1
    propagate(sim, narrate=False)
    return {
        "mishap": performer.meters["mishap"] >= THRESHOLD,
        "risk": trouble.risk,
        "embarrassed": performer.memes["embarrassed"] >= THRESHOLD,
    }


def introduce(world: World, performer: Entity, partner: Entity, theme: ShowTheme) -> None:
    world.say(
        f"One bright afternoon, {performer.id} and {partner.id} found a stump in {world.setting.place} "
        f"and decided it was much too grand to be only a stump."
    )
    world.say(
        f"{world.setting.detail} {performer.id} put on {theme.costume} and announced, "
        f'"Today this stump is our stage!"'
    )


def begin_show(world: World, performer: Entity, partner: Entity, theme: ShowTheme) -> None:
    performer.memes["pride"] += 1
    partner.memes["joy"] += 1
    world.say(
        f'{performer.id} climbed toward the stump, spread both arms, and boomed, '
        f'"{theme.opening}"'
    )
    world.say(
        f'{partner.id} bowed from the grass and answered, "{theme.reply}"'
    )
    world.say(
        f'That made {performer.id} grin even wider. "{theme.extra_rhyme}"'
    )


def warn(world: World, partner: Entity, performer: Entity, trouble: Trouble, parent: Entity) -> None:
    pred = predict_trouble(world, trouble)
    partner.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'But {partner.id} stopped the show with a little gasp. "{trouble.warning}" '
        f'{partner.pronoun().capitalize()} pointed at the stump. '
        f'"If you hop up there now, this royal show might turn into a royal {trouble.label}."'
    )
    if pred["mishap"]:
        world.say(
            f'{parent.label_word.capitalize()} looked over too and said, '
            f'"Let us fix the stump before the rhyme gets bumpier than the climb."'
        )


def listen(world: World, performer: Entity, partner: Entity) -> None:
    performer.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'{performer.id} froze with one foot in the air, blinked, and then laughed. '
        f'"Oh! I nearly made a silly start. Good catch, {partner.id}."'
    )


def ignore_warning(world: World, performer: Entity, partner: Entity) -> None:
    performer.memes["defiance"] += 1
    world.say(
        f'"I can still rhyme just fine," {performer.id} said. '
        f'"Watch me shine on my stump and thump!"'
    )
    if performer.attrs.get("relation") == "siblings" and performer.age > partner.age:
        world.say(
            f"{partner.id} looked doubtful, but {performer.id} was the older child and bounded ahead anyway."
        )
    else:
        world.say(
            f"{partner.id} reached out, but {performer.id} had already bounced toward the stump."
        )


def mishap(world: World, performer: Entity, trouble: Trouble) -> None:
    performer.meters["mishap"] += 1
    performer.meters[trouble.risk] += 1
    propagate(world, narrate=False)
    world.say(trouble.mishap)
    if performer.memes["embarrassed"] >= THRESHOLD:
        world.say(
            f"For one tiny second, {performer.id}'s cheeks turned pink. Then a snort of laughter slipped out."
        )


def apply_fix(world: World, parent: Entity, performer: Entity, partner: Entity, trouble: Trouble, fix: Fix) -> None:
    performer.meters[trouble.risk] = 0.0
    performer.meters["mishap"] = 0.0
    performer.memes["relief"] += 1
    performer.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {fix.action}"
    )
    world.say(
        f'Soon the stump was {trouble.safe_after}. "{performer.id}," said {parent.label_word}, '
        f'"now your show can be silly without being slippery."'
    )


def finale(world: World, performer: Entity, partner: Entity, theme: ShowTheme, trouble: Trouble, fix: Fix) -> None:
    performer.memes["confidence"] += 1
    partner.memes["confidence"] += 1
    world.say(
        f'{performer.id} hopped up with care and tried again. "{theme.opening}"'
    )
    world.say(
        f'"{theme.reply}" said {partner.id}, trying very hard not to giggle first.'
    )
    if trouble.id == "ants":
        add = "Not even one ant dared interrupt the kingly nonsense."
    elif trouble.id == "muddy":
        add = "This time there was no squish underfoot, only proud little thumps."
    else:
        add = "This time the top of the stump held steady under the tiny speech."
    world.say(
        f'{performer.id} finished with a deep bow. "{theme.closing}" {add}'
    )
    world.say(
        f"The two children laughed so hard that even the stump seemed pleased to be part of the joke."
    )


def tell(
    setting: Setting,
    theme: ShowTheme,
    trouble: Trouble,
    fix: Fix,
    *,
    performer_name: str = "Nora",
    performer_gender: str = "girl",
    performer_trait: str = "bold",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    partner_trait: str = "careful",
    parent_type: str = "mother",
    relation: str = "friends",
    performer_age: int = 5,
    partner_age: int = 6,
) -> World:
    world = World(setting)
    performer = world.add(Entity(
        id=performer_name,
        kind="character",
        type=performer_gender,
        role="performer",
        traits=[performer_trait],
        age=performer_age,
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=[partner_trait],
        age=partner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    stump = world.add(Entity(
        id="stump",
        type="stump",
        label="stump",
        phrase="the little stump stage",
        tags={"stump"},
    ))
    stump.meters[trouble.risk] += 1

    introduce(world, performer, partner, theme)
    begin_show(world, performer, partner, theme)

    world.para()
    warn(world, partner, performer, trouble, parent)

    if would_listen(relation, performer_age, partner_age, performer_trait):
        listen(world, performer, partner)
        outcome = "listened"
    else:
        ignore_warning(world, performer, partner)
        world.para()
        mishap(world, performer, trouble)
        outcome = "mishap"

    world.para()
    apply_fix(world, parent, performer, partner, trouble, fix)

    world.para()
    finale(world, performer, partner, theme, trouble, fix)

    world.facts.update(
        performer=performer,
        partner=partner,
        parent=parent,
        stump=stump,
        setting=setting,
        theme=theme,
        trouble=trouble,
        fix=fix,
        outcome=outcome,
        relation=relation,
        performer_age=performer_age,
        partner_age=partner_age,
        listened=(outcome == "listened"),
        had_mishap=(outcome == "mishap"),
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        detail="Beans climbed a fence nearby, and the stump sat beside a crooked row of carrots.",
        affords={"mossy", "ants"},
        tags={"garden"},
    ),
    "park": Setting(
        id="park",
        place="the park",
        detail="A duck pond glimmered beyond the path, and the stump waited under a chestnut tree.",
        affords={"mossy", "muddy"},
        tags={"park"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard",
        detail="Fallen apples dotted the grass, and the stump stood between two sleepy pear trees.",
        affords={"ants", "muddy"},
        tags={"orchard"},
    ),
}

SHOWS = {
    "king": ShowTheme(
        id="king",
        title="the King of Rhyme",
        costume="a saucepan crown and a towel cape",
        opening="I am the King of Stump and Drum!",
        reply="Then thump, Your Lumpiness, thump-thump-thump!",
        extra_rhyme="I rule by rhyme, by chime, by plumptious time!",
        closing="The royal rhyme is done. Now somebody fetch me a bun!",
        tags={"rhyme", "dialogue"},
    ),
    "pirate": ShowTheme(
        id="pirate",
        title="the Pirate of Rhyme",
        costume="a paper hat and one cardboard telescope",
        opening="I am the Pirate of Stump and Sea!",
        reply="Then rhyme, brave captain, and rhyme with me!",
        extra_rhyme="I sail for treasure, for measure, for peas if you please!",
        closing="The captain bows with a pirate vow: no fish, just giggles now!",
        tags={"rhyme", "dialogue"},
    ),
    "chef": ShowTheme(
        id="chef",
        title="the Chef of Chatter",
        costume="a puffy oven mitt and a wooden spoon",
        opening="I am the Chef of Soup and Stump!",
        reply="Then stir your words and do not slump!",
        extra_rhyme="I cook up rhyme with thyme and a plum-crumb clump!",
        closing="The menu says: one laugh, two claps, and no more soup mishaps!",
        tags={"rhyme", "dialogue"},
    ),
}

TROUBLES = {
    "mossy": Trouble(
        id="mossy",
        label="slide",
        risk="slippery",
        warning="That top is green and slick.",
        mishap="The moment the foot touched the stump, it skidded. Down went the great performer in one surprised little plop onto the grass.",
        safe_after="dry instead of slick",
        tags={"moss", "stump"},
    ),
    "muddy": Trouble(
        id="muddy",
        label="squish",
        risk="muddy",
        warning="There is a muddy ring around the stump.",
        mishap="One shoe sank at the edge with a loud squish, and the grand speech came out as, \"I am the king of stuuump and muuud!\"",
        safe_after="ringed with a clean dry place to stand",
        tags={"mud", "stump"},
    ),
    "ants": Trouble(
        id="ants",
        label="dance",
        risk="itchy",
        warning="An ant parade is marching over that stump like it owns the place.",
        mishap="Before the first bow was finished, an ant tickled an ankle. Up popped the performer, hopping and flapping in a wild ant dance.",
        safe_after="free for the show while the ants kept their own trail",
        tags={"ants", "stump"},
    ),
}

FIXES = {
    "towel": Fix(
        id="towel",
        label="a dry towel",
        works_for={"mossy"},
        action="rubbed the top with a dry towel until the green wet shine was gone.",
        qa_text="dried the slippery stump with a towel",
        tags={"towel"},
    ),
    "mat": Fix(
        id="mat",
        label="a picnic mat",
        works_for={"muddy"},
        action="spread a picnic mat around the stump so small shoes had a clean dry place to land.",
        qa_text="put a picnic mat around the muddy stump",
        tags={"mat"},
    ),
    "move_show": Fix(
        id="move_show",
        label="a moved stage",
        works_for={"ants"},
        action="set a crate beside the stump and said the ants could keep the old stage while the children borrowed a new one.",
        qa_text="moved the show beside the stump so the ants could keep marching",
        tags={"move"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam", "Noah", "Eli"]
PERFORMER_TRAITS = ["bold", "bouncy", "giggly", "careful", "thoughtful"]
PARTNER_TRAITS = ["careful", "steady", "thoughtful", "curious"]


@dataclass
class StoryParams:
    setting: str
    show: str
    trouble: str
    fix: str
    performer_name: str
    performer_gender: str
    performer_trait: str
    partner_name: str
    partner_gender: str
    partner_trait: str
    parent: str
    relation: str = "friends"
    performer_age: int = 5
    partner_age: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "stump": [
        (
            "What is a stump?",
            "A stump is the short bottom part of a tree left in the ground after the rest of the tree is cut or falls down.",
        )
    ],
    "moss": [
        (
            "Why can moss be slippery?",
            "Moss is a soft green plant that can hold water. When it is wet, it can make a surface slick.",
        )
    ],
    "mud": [
        (
            "Why does mud make shoes squish?",
            "Mud is wet dirt, so it is soft and squishy. When you step in it, your shoe sinks and makes a squish sound.",
        )
    ],
    "ants": [
        (
            "Why do ants walk in lines?",
            "Ants often follow smell trails left by other ants. That helps them find food and find their way home.",
        )
    ],
    "towel": [
        (
            "What does a towel do?",
            "A towel soaks up water and helps dry things off. A dry surface is usually less slippery.",
        )
    ],
    "mat": [
        (
            "What is a picnic mat for?",
            "A picnic mat gives you a cleaner, drier place to sit or stand on the ground.",
        )
    ],
    "move": [
        (
            "Why is moving sometimes the best fix?",
            "Sometimes the smartest fix is to change places. If a spot has a problem, moving can be easier than fighting the problem.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like cat and hat. Rhymes can make speech sound bouncy and funny.",
        )
    ],
    "dialogue": [
        (
            "What is dialogue in a story?",
            "Dialogue is when characters speak to each other. It lets you hear their words right in the story.",
        )
    ],
}

KNOWLEDGE_ORDER = ["stump", "moss", "mud", "ants", "towel", "mat", "move", "rhyme", "dialogue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    performer = f["performer"]
    partner = f["partner"]
    trouble = f["trouble"]
    theme = f["theme"]
    if f["outcome"] == "listened":
        turn = f"{performer.id} listens before the joke turns into a bigger flop"
    else:
        turn = f"{performer.id} tries first and has a comic {trouble.label}"
    return [
        'Write a funny story for a 3-to-5-year-old that includes the word "stump" and uses rhyme and dialogue.',
        f"Tell a comedy where {performer.id} and {partner.id} turn a stump into a stage for {theme.title}, but {turn}.",
        f"Write a child-facing story with bouncy dialogue, silly rhymes, a stump stage, and a safe happy ending after a {trouble.label}.",
    ]


def pair_noun(performer: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if performer.type == "boy" and partner.type == "boy":
            return "two brothers"
        if performer.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    performer = f["performer"]
    partner = f["partner"]
    parent = f["parent"]
    trouble = f["trouble"]
    fix = f["fix"]
    theme = f["theme"]
    relation = f["relation"]
    pair = pair_noun(performer, partner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {performer.id} and {partner.id}, who turned a stump into a tiny stage. {parent.label_word.capitalize()} also helped them fix the problem so the show could go on.",
        ),
        (
            "What were they pretending to do?",
            f"They were putting on a silly stump show called {theme.title}. They spoke in rhymes to make the pretend performance sound extra funny.",
        ),
        (
            f"Why did {partner.id} stop the show?",
            f"{partner.id} noticed that the stump had a problem: {trouble.warning.lower()} {partner.pronoun().capitalize()} knew the show might turn into a {trouble.label} instead of a smooth performance.",
        ),
    ]
    if f["outcome"] == "listened":
        qa.append(
            (
                f"What did {performer.id} do after the warning?",
                f"{performer.id} listened and stopped before stepping all the way up. That kept the joke gentle, because the children could fix the stump before anything silly happened.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {performer.id} tried anyway?",
                f"{trouble.mishap.split('.')[0]}. The mishap was funny instead of scary, but it showed why {partner.id}'s warning mattered.",
            )
        )
    qa.append(
        (
            "How did the grown-up help?",
            f"{parent.label_word.capitalize()} {fix.qa_text}. That changed the little stage into a safer place for the rhyme show.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children finishing their silly dialogue and laughing together. The stump stayed part of the game, but after the fix it helped the show instead of spoiling it.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"stump", "rhyme", "dialogue"}
    tags |= set(f["trouble"].tags)
    tags |= set(f["fix"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        show="king",
        trouble="ants",
        fix="move_show",
        performer_name="Nora",
        performer_gender="girl",
        performer_trait="bold",
        partner_name="Ben",
        partner_gender="boy",
        partner_trait="careful",
        parent="mother",
        relation="friends",
        performer_age=5,
        partner_age=5,
    ),
    StoryParams(
        setting="park",
        show="pirate",
        trouble="mossy",
        fix="towel",
        performer_name="Max",
        performer_gender="boy",
        performer_trait="careful",
        partner_name="Lucy",
        partner_gender="girl",
        partner_trait="thoughtful",
        parent="father",
        relation="friends",
        performer_age=6,
        partner_age=6,
    ),
    StoryParams(
        setting="orchard",
        show="chef",
        trouble="muddy",
        fix="mat",
        performer_name="Ella",
        performer_gender="girl",
        performer_trait="bouncy",
        partner_name="Theo",
        partner_gender="boy",
        partner_trait="steady",
        parent="mother",
        relation="siblings",
        performer_age=7,
        partner_age=5,
    ),
    StoryParams(
        setting="garden",
        show="king",
        trouble="mossy",
        fix="towel",
        performer_name="Leo",
        performer_gender="boy",
        performer_trait="giggly",
        partner_name="Sam",
        partner_gender="boy",
        partner_trait="careful",
        parent="father",
        relation="siblings",
        performer_age=4,
        partner_age=7,
    ),
]


def explain_rejection(trouble: Trouble, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not sensibly solve the {trouble.label} problem on the stump. "
        f"Pick a fix that matches the trouble.)"
    )


ASP_RULES = r"""
works(Fx, Tr) :- fix(Fx), trouble(Tr), compatible(Fx, Tr).
valid(S, Sh, Tr, Fx) :- setting(S), show(Sh), affords(S, Tr), works(Fx, Tr).

older_partner :- relation(siblings), partner_age(PA), performer_age(FA), PA > FA.
careful_performer :- performer_trait(T), careful_trait(T).
listen :- older_partner.
listen :- careful_performer.

outcome(listened) :- listen.
outcome(mishap) :- not listen.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for trouble_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, trouble_id))
    for show_id in SHOWS:
        lines.append(asp.fact("show", show_id))
    for trouble_id in TROUBLES:
        lines.append(asp.fact("trouble", trouble_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for trouble_id in sorted(fix.works_for):
            lines.append(asp.fact("compatible", fix_id, trouble_id))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
        asp.fact("relation", params.relation),
        asp.fact("performer_age", params.performer_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("performer_trait", params.performer_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, asp in mismatches[:5]:
            print(f"  {params} -> python={py} asp={asp}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a stump stage, rhyming dialogue, and a comic little problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--show", choices=SHOWS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name_pool = [name for name in pool if name != avoid]
    return rng.choice(name_pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.fix:
        if not fix_works(TROUBLES[args.trouble], FIXES[args.fix]):
            raise StoryError(explain_rejection(TROUBLES[args.trouble], FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.show is None or combo[1] == args.show)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, show_id, trouble_id, fix_id = rng.choice(sorted(combos))
    performer_name, performer_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=performer_name)
    return StoryParams(
        setting=setting_id,
        show=show_id,
        trouble=trouble_id,
        fix=fix_id,
        performer_name=performer_name,
        performer_gender=performer_gender,
        performer_trait=rng.choice(PERFORMER_TRAITS),
        partner_name=partner_name,
        partner_gender=partner_gender,
        partner_trait=rng.choice(PARTNER_TRAITS),
        parent=args.parent or rng.choice(["mother", "father"]),
        relation=rng.choice(["friends", "siblings"]),
        performer_age=rng.randint(4, 7),
        partner_age=rng.randint(4, 7),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.show not in SHOWS:
        raise StoryError(f"(Unknown show: {params.show})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    setting = SETTINGS[params.setting]
    show = SHOWS[params.show]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]

    if params.trouble not in setting.affords:
        raise StoryError("(No story: that trouble does not fit the chosen setting.)")
    if not fix_works(trouble, fix):
        raise StoryError(explain_rejection(trouble, fix))

    world = tell(
        setting=setting,
        theme=show,
        trouble=trouble,
        fix=fix,
        performer_name=params.performer_name,
        performer_gender=params.performer_gender,
        performer_trait=params.performer_trait,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        partner_trait=params.partner_trait,
        parent_type=params.parent,
        relation=params.relation,
        performer_age=params.performer_age,
        partner_age=params.partner_age,
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
        print(f"{len(combos)} compatible (setting, show, trouble, fix) combos:\n")
        for setting_id, show_id, trouble_id, fix_id in combos:
            print(f"  {setting_id:8} {show_id:7} {trouble_id:7} {fix_id}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.performer_name} & {p.partner_name}: {p.show} on a stump "
                f"({p.setting}, {p.trouble}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
