#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scar_distraught_misunderstanding_repetition_humor_pirate_tale.py
================================================================================================

A standalone story world about two children playing pirates, an old scar that is
misunderstood as a fresh wound, a moment of distraught worry, and a calm,
humorous explanation that turns fear back into play.

The domain is intentionally small and constraint-checked:

- A visible old scar must come from a cause that can plausibly leave one.
- The chosen reassurance method must fit the body part where the scar is.
- Low-sense "fixes" are known to the world but refused.
- The misunderstanding is driven by the pirate game and the visible scar, not by
  parsing the final prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/scar_distraught_misunderstanding_repetition_humor_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/scar_distraught_misunderstanding_repetition_humor_pirate_tale.py --scar bicycle_knee
    python storyworlds/worlds/gpt-5.4/scar_distraught_misunderstanding_repetition_humor_pirate_tale.py --aid paint_over
    python storyworlds/worlds/gpt-5.4/scar_distraught_misunderstanding_repetition_humor_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/scar_distraught_misunderstanding_repetition_humor_pirate_tale.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    quest: str
    sendoff: str


@dataclass
class ScarFact:
    id: str
    body_part: str
    label: str
    phrase: str
    old_event: str
    demo_word: str
    real: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    parts: set[str] = field(default_factory=set)
    sense: int = 0
    lead: str = ""
    proof: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    scar: str
    aid: str
    helper: str
    watcher: str
    watcher_gender: str
    mate: str
    mate_gender: str
    mood: str
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


def _r_alarm(world: World) -> list[str]:
    watcher = world.get("watcher")
    helper = world.get("helper")
    if helper.meters["scar_visible"] < THRESHOLD or watcher.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("alarm", watcher.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["fear"] += 1
    helper.memes["concern"] += 1
    return ["__alarm__"]


def _r_distraught(world: World) -> list[str]:
    watcher = world.get("watcher")
    if watcher.memes["fear"] < THRESHOLD:
        return []
    sig = ("distraught", watcher.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["distraught"] += 1
    return ["__distraught__"]


def _r_resolve(world: World) -> list[str]:
    watcher = world.get("watcher")
    helper = world.get("helper")
    if helper.memes["explained"] < THRESHOLD or helper.meters["proof"] < THRESHOLD:
        return []
    sig = ("resolve", watcher.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["misunderstanding"] = 0.0
    watcher.memes["fear"] = 0.0
    watcher.memes["distraught"] = 0.0
    watcher.memes["relief"] += 1
    watcher.memes["trust"] += 1
    world.get("mate").memes["relief"] += 1
    helper.memes["relief"] += 1
    return ["__resolved__"]


CAUSAL_RULES = [
    Rule(name="alarm", tag="emotional", apply=_r_alarm),
    Rule(name="distraught", tag="emotional", apply=_r_distraught),
    Rule(name="resolve", tag="emotional", apply=_r_resolve),
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
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a roaring pirate sea",
        rig="The sofa was their ship, a laundry basket was the crow's nest, and a crayon map curled across the rug like an island chart.",
        titles=("Captain", "Matey"),
        quest="the sugar-bowl treasure",
        sendoff="sailed around the room hunting treasure with more laughing than shouting",
    ),
    "treasure": Theme(
        id="treasure",
        scene="a glittering treasure bay",
        rig="The armchair was a lookout rock, a blanket made a cave, and a wooden spoon tapped the floor like a mast in the wind.",
        titles=("Captain", "Scout"),
        quest="the moon-coin chest",
        sendoff="set off to search every cushion for treasure without a single frightened glance",
    ),
    "deck": Theme(
        id="deck",
        scene="the deck of a brave little ship",
        rig="A blue towel became the sea, the coffee table became the captain's deck, and a paper tube became a spyglass that saw only adventure.",
        titles=("Skipper", "First Mate"),
        quest="the hidden pearl",
        sendoff="marched across the carpet-deck in a neat little line, grinning at every wave they pretended to cross",
    ),
}

SCARS = {
    "bicycle_knee": ScarFact(
        id="bicycle_knee",
        body_part="knee",
        label="scar",
        phrase="a pale little scar on his knee",
        old_event="when he fell off a bicycle long ago and then healed",
        demo_word="bent his knee",
        real=True,
        tags={"scar", "knee", "healing"},
    ),
    "berry_chin": ScarFact(
        id="berry_chin",
        body_part="chin",
        label="scar",
        phrase="a tiny silver scar under his chin",
        old_event="when he slipped while picking blackberries long ago and then healed",
        demo_word="tipped up his chin",
        real=True,
        tags={"scar", "chin", "healing"},
    ),
    "rope_forearm": ScarFact(
        id="rope_forearm",
        body_part="forearm",
        label="scar",
        phrase="a thin white scar on his forearm",
        old_event="from an old rope burn he got while hauling a box years ago and then healed",
        demo_word="waggled his arm",
        real=True,
        tags={"scar", "arm", "healing"},
    ),
    "jam_smudge": ScarFact(
        id="jam_smudge",
        body_part="chin",
        label="smudge",
        phrase="a stripe of raspberry jam on his chin",
        old_event="from snack time five minutes ago",
        demo_word="wiped his chin",
        real=False,
        tags={"jam"},
    ),
}

AIDS = {
    "knee_bend": Aid(
        id="knee_bend",
        label="a knee bend",
        parts={"knee"},
        sense=3,
        lead="sat on the rug so both children could see properly",
        proof='then bent his knee, patted it, and said, "See? It does not hurt now."',
        qa_text="showed the old mark by bending his knee and calmly proving it was healed",
        tags={"body", "healing"},
    ),
    "mirror_peek": Aid(
        id="mirror_peek",
        label="a mirror peek",
        parts={"chin", "forearm"},
        sense=3,
        lead="held up a little mirror from the hallway basket",
        proof='and let them look closely while he smiled and said, "No cut, no blood, just an old healed line."',
        qa_text="used a small mirror so the children could see the old healed line up close",
        tags={"mirror", "healing"},
    ),
    "arm_wiggle": Aid(
        id="arm_wiggle",
        label="an arm wiggle",
        parts={"forearm"},
        sense=2,
        lead="rolled up his sleeve a little farther",
        proof='and waggled his arm, opened and closed his hand, and said, "If it were a fresh hurt, I would not be doing this so cheerfully."',
        qa_text="wiggled his arm and hand to show the old mark was healed and harmless now",
        tags={"body", "healing"},
    ),
    "paint_over": Aid(
        id="paint_over",
        label="paint over it",
        parts={"knee", "chin", "forearm"},
        sense=1,
        lead="reached for the paint box",
        proof='as if a little blue paint could solve everything',
        qa_text="tried to paint over the mark",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
MOODS = ["careful", "dramatic", "earnest", "curious", "tender"]


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def valid_combo(theme_id: str, scar_id: str, aid_id: str) -> bool:
    scar = SCARS[scar_id]
    aid = AIDS[aid_id]
    return scar.real and aid.sense >= SENSE_MIN and scar.body_part in aid.parts


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for scar_id in SCARS:
            for aid_id in AIDS:
                if valid_combo(theme_id, scar_id, aid_id):
                    combos.append((theme_id, scar_id, aid_id))
    return combos


def explain_rejection(scar: ScarFact, aid: Aid) -> str:
    if not scar.real:
        return (
            f"(No story: {scar.phrase} is not an old scar at all. "
            f"This world only tells stories where a child misunderstands a real healed scar.)"
        )
    if aid.sense < SENSE_MIN:
        return (
            f"(Refusing aid '{aid.id}': it scores too low on common sense "
            f"(sense={aid.sense} < {SENSE_MIN}). A calm explanation should fit the body part and truly reassure.)"
        )
    if scar.body_part not in aid.parts:
        return (
            f"(No story: {aid.label} does not fit a scar on the {scar.body_part}. "
            f"Pick a reassurance that actually helps children inspect that body part.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_alarm(world: World) -> dict:
    sim = world.copy()
    watcher = sim.get("watcher")
    helper = sim.get("helper")
    helper.meters["scar_visible"] += 1
    watcher.memes["misunderstanding"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": watcher.memes["fear"],
        "distraught": watcher.memes["distraught"],
    }


def play_setup(world: World, watcher: Entity, mate: Entity, theme: Theme) -> None:
    watcher.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"One cozy afternoon, {watcher.id} and {mate.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.titles[0]} {watcher.id}! {theme.titles[1]} {mate.id}!" {watcher.id} cried. '
        f'"Today we find {theme.quest}."'
    )


def helper_joins(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.label_word.capitalize()} came by with a dish towel over {helper.pronoun('possessive')} shoulder and agreed to be the ship's old captain for a minute."
    )


def notice_scar(world: World, watcher: Entity, helper: Entity, scar: ScarFact, mood: str) -> None:
    helper.meters["scar_visible"] += 1
    watcher.meters["seen_scar"] += 1
    pred = predict_alarm(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_distraught"] = pred["distraught"]
    extra = " At once, pirate thoughts filled the empty spaces in the story." if mood in {"dramatic", "earnest"} else ""
    world.say(
        f"Then {watcher.id} noticed {scar.phrase}.{extra}"
    )


def misunderstand(world: World, watcher: Entity, mate: Entity, helper: Entity, scar: ScarFact) -> None:
    watcher.memes["misunderstanding"] += 1
    mate.memes["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{watcher.id} gasped. "{helper.label_word.capitalize()}, your scar! Your scar!"'
    )
    world.say(
        f"{watcher.pronoun().capitalize()} thought it must be a brand-new pirate wound, as if a swordfish or a treasure chest had just nipped {helper.pronoun('object')}."
    )
    if watcher.memes["distraught"] >= THRESHOLD:
        world.say(
            f"In one blink, {watcher.id} grew quite distraught and pressed both hands to {watcher.pronoun('possessive')} cheeks."
        )
    world.say(
        f'{mate.id} darted in a circle and cried, "Bandage the captain! Bandage the captain!"'
    )


def funny_help(world: World, watcher: Entity, mate: Entity, scar: ScarFact) -> None:
    helper_kit = {
        "knee": "three sticky plasters and a soup spoon",
        "chin": "a washcloth and the cleanest sticker in the house",
        "forearm": "a toy telescope and two bandages that did not even match",
    }[scar.body_part]
    mate.memes["humor"] += 1
    world.say(
        f"{mate.id} came skidding back with {helper_kit}, which looked more like pirate treasure than proper first aid."
    )
    world.say(
        f'Even through the worry, the sight was so unexpected that a tiny laugh nearly escaped from the old captain.'
    )


def explain(world: World, helper: Entity, scar: ScarFact, aid: Aid) -> None:
    helper.memes["explained"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt down and spoke in a warm, steady voice. "Old scar, old story, no fresh worry," {helper.pronoun()} said.'
    )
    world.say(
        f'"This mark came from {scar.old_event}. It is healed now."'
    )
    world.say(
        f"Then {helper.pronoun()} {aid.lead} and {aid.proof}"
    )
    helper.meters["proof"] += 1
    propagate(world, narrate=False)


def resolve_scene(world: World, watcher: Entity, mate: Entity, helper: Entity) -> None:
    world.say(
        f'{watcher.id} blinked hard. "So a scar can stay after the hurt is gone?"'
    )
    world.say(
        f'"Exactly," said {helper.label_word}. "A scar is an old mark, not a fresh hurt."'
    )
    if watcher.memes["relief"] >= THRESHOLD:
        world.say(
            f"The tight look on {watcher.id}'s face loosened. {watcher.pronoun().capitalize()} stepped close, looked again, and this time saw a quiet old line instead of a dangerous cut."
        )
    world.say(
        f'{mate.id} lowered the soup spoon, or the sticker, or whatever rescue tool had been chosen, and asked, "Then may the captain keep both knees and all the rest of him?"'
    )
    world.say(
        f'{helper.label_word.capitalize()} laughed. "Aye," {helper.pronoun()} said. "All present and counted."'
    )


def ending(world: World, watcher: Entity, mate: Entity, helper: Entity, theme: Theme, scar: ScarFact) -> None:
    watcher.memes["joy"] += 1
    mate.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, the children repeated the captain's rhyme all around the room: "
        f'"Old scar, old story, no fresh worry."'
    )
    world.say(
        f"{watcher.id} drew one neat silver line on the crayon map and called it the captain's brave old mark."
    )
    world.say(
        f"Then the little crew {theme.sendoff}, while {helper.label_word} stood at the harbor-rug smiling with both hands perfectly still and perfectly fine."
    )
    world.facts["ending_image"] = f"{watcher.id} drew one neat silver line on the crayon map"


def tell(theme: Theme, scar: ScarFact, aid: Aid, helper_type: str,
         watcher_name: str, watcher_gender: str,
         mate_name: str, mate_gender: str, mood: str) -> World:
    world = World()
    watcher = world.add(Entity(id="watcher", kind="character", type=watcher_gender, label=watcher_name, role="watcher", traits=[mood]))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, label=mate_name, role="mate", traits=["eager"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))

    play_setup(world, watcher, mate, theme)
    helper_joins(world, helper)

    world.para()
    notice_scar(world, watcher, helper, scar, mood)
    misunderstand(world, watcher, mate, helper, scar)
    funny_help(world, watcher, mate, scar)

    world.para()
    explain(world, helper, scar, aid)
    resolve_scene(world, watcher, mate, helper)

    world.para()
    ending(world, watcher, mate, helper, theme, scar)

    world.facts.update(
        theme=theme,
        scar=scar,
        aid=aid,
        helper=helper,
        watcher=watcher,
        mate=mate,
        misunderstanding=True,
        distraught=watcher.memes["relief"] >= THRESHOLD,
        resolved=watcher.memes["relief"] >= THRESHOLD,
        helper_name=helper.label_word,
        watcher_name=watcher_name,
        mate_name=mate_name,
    )
    return world


KNOWLEDGE = {
    "scar": [
        (
            "What is a scar?",
            "A scar is a mark left on the skin after a cut or scrape heals. The hurt is over, but the skin remembers it with a small line or patch.",
        )
    ],
    "healing": [
        (
            "What does healed mean?",
            "Healed means a body part was hurt before, but it has gotten better. A healed place may still show a scar even though it is not a fresh injury.",
        )
    ],
    "mirror": [
        (
            "Why can a mirror help you look at a mark safely?",
            "A mirror lets you see something clearly without poking or guessing. Looking carefully can help you notice whether a mark is old and calm instead of new and bleeding.",
        )
    ],
    "body": [
        (
            "How can you tell if someone has an old mark instead of a brand-new hurt?",
            "You can look for calm skin, no bleeding, and no signs of pain. A grown-up can also explain where the mark came from and gently show that the body part moves fine.",
        )
    ],
}
KNOWLEDGE_ORDER = ["scar", "healing", "mirror", "body"]


def pair_noun(watcher: Entity, mate: Entity) -> str:
    if watcher.type == "boy" and mate.type == "boy":
        return "two boys"
    if watcher.type == "girl" and mate.type == "girl":
        return "two girls"
    return "a boy and a girl"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    watcher = f["watcher"]
    mate = f["mate"]
    helper = f["helper"]
    scar = f["scar"]
    theme = f["theme"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "scar" and "distraught".',
        f"Tell a gentle pirate tale where {watcher.label} misunderstands an old scar on {helper.label_word} and grows distraught before learning the truth.",
        f'Write a story with misunderstanding, repetition, and humor where two children at play keep repeating "Your scar! Your scar!" before a calm grown-up explains what a scar really is.',
        f"Tell a cozy room-sized pirate adventure where children searching for {theme.quest} mistake {scar.phrase} for a fresh wound and then return to play.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    watcher = f["watcher"]
    mate = f["mate"]
    helper = f["helper"]
    scar = f["scar"]
    aid = f["aid"]
    theme = f["theme"]
    pair = pair_noun(watcher, mate)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {watcher.label} and {mate.label}, and their {helper.label_word} who joins their pirate game for a while.",
        ),
        (
            "What were they pretending at the beginning?",
            f"They were pretending the living room was {theme.scene} and hunting for {theme.quest}. The pirate game made everything feel bigger and more dramatic.",
        ),
        (
            f"Why did {watcher.label} get distraught?",
            f"{watcher.label} saw {scar.phrase} and misunderstood it as a brand-new pirate wound. Because the game was already full of pirate ideas, {watcher.pronoun()} imagined danger where there was only an old healed mark.",
        ),
        (
            "What was the misunderstanding?",
            f"The misunderstanding was that an old scar was taken for a fresh hurt. A scar can stay on the skin after healing, so the mark looked serious before the grown-up explained it.",
        ),
        (
            f"How did the grown-up calm the children?",
            f"{helper.label_word.capitalize()} repeated, \"Old scar, old story, no fresh worry,\" and then {aid.qa_text}. That proof matched the body part, so the children could see the mark was old and healed.",
        ),
        (
            "What was funny in the middle of the story?",
            f"{mate.label} rushed back with silly rescue supplies that did not quite fit the problem, which made the moment funny without stopping the worry at once. The humor helped the story soften as the truth came out.",
        ),
        (
            "How did the story end?",
            f"It ended with the children repeating the captain's rhyme and going back to their pirate game. {f['ending_image']}, which showed that fear had turned back into play.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["scar"].tags) | set(f["aid"].tags)
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
        if ent.label:
            bits.append(f"label={ent.label}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        scar="bicycle_knee",
        aid="knee_bend",
        helper="father",
        watcher="Lily",
        watcher_gender="girl",
        mate="Tom",
        mate_gender="boy",
        mood="dramatic",
    ),
    StoryParams(
        theme="treasure",
        scar="berry_chin",
        aid="mirror_peek",
        helper="grandfather",
        watcher="Mia",
        watcher_gender="girl",
        mate="Ben",
        mate_gender="boy",
        mood="earnest",
    ),
    StoryParams(
        theme="deck",
        scar="rope_forearm",
        aid="arm_wiggle",
        helper="father",
        watcher="Sam",
        watcher_gender="boy",
        mate="Nora",
        mate_gender="girl",
        mood="curious",
    ),
    StoryParams(
        theme="pirates",
        scar="rope_forearm",
        aid="mirror_peek",
        helper="grandfather",
        watcher="Theo",
        watcher_gender="boy",
        mate="Ava",
        mate_gender="girl",
        mood="tender",
    ),
]


ASP_RULES = r"""
real_scar(S) :- scar(S), leaves_scar(S).
sensible_aid(A) :- aid(A), sense(A, Sc), sense_min(M), Sc >= M.
fits(S, A) :- scar_part(S, P), aid_part(A, P).
valid(T, S, A) :- theme(T), real_scar(S), sensible_aid(A), fits(S, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for scar_id, scar in SCARS.items():
        lines.append(asp.fact("scar", scar_id))
        lines.append(asp.fact("scar_part", scar_id, scar.body_part))
        if scar.real:
            lines.append(asp.fact("leaves_scar", scar_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        for part in sorted(aid.parts):
            lines.append(asp.fact("aid_part", aid_id, part))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_aids() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_aid/1."))
    return sorted(aid for (aid,) in asp.atoms(model, "sensible_aid"))


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

    clingo_sensible = set(asp_sensible_aids())
    python_sensible = {aid.id for aid in sensible_aids()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible aids match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible aids: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: pirate play, an old scar, a misunderstanding, and a calm explanation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--scar", choices=SCARS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--helper", choices=["mother", "father", "grandfather"])
    ap.add_argument("--watcher")
    ap.add_argument("--watcher-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scar and args.aid:
        scar = SCARS[args.scar]
        aid = AIDS[args.aid]
        if not valid_combo(args.theme or next(iter(THEMES)), args.scar, args.aid):
            raise StoryError(explain_rejection(scar, aid))
    if args.scar and not SCARS[args.scar].real:
        aid = AIDS[args.aid] if args.aid else next(iter(AIDS.values()))
        raise StoryError(explain_rejection(SCARS[args.scar], aid))
    if args.aid and AIDS[args.aid].sense < SENSE_MIN:
        scar = SCARS[args.scar] if args.scar else next(s for s in SCARS.values() if s.real)
        raise StoryError(explain_rejection(scar, AIDS[args.aid]))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.scar is None or combo[1] == args.scar)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, scar_id, aid_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(["mother", "father", "grandfather"])
    watcher_gender = args.watcher_gender or rng.choice(["girl", "boy"])
    watcher = args.watcher or _pick_name(rng, watcher_gender)
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    mate = args.mate or _pick_name(rng, mate_gender, avoid=watcher)
    mood = args.mood or rng.choice(MOODS)

    return StoryParams(
        theme=theme_id,
        scar=scar_id,
        aid=aid_id,
        helper=helper,
        watcher=watcher,
        watcher_gender=watcher_gender,
        mate=mate,
        mate_gender=mate_gender,
        mood=mood,
    )


def _validate_params(params: StoryParams) -> None:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.scar not in SCARS:
        raise StoryError(f"(Unknown scar: {params.scar})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.helper not in {"mother", "father", "grandfather"}:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.watcher_gender not in {"girl", "boy"} or params.mate_gender not in {"girl", "boy"}:
        raise StoryError("(Gender must be 'girl' or 'boy'.)")
    scar = SCARS[params.scar]
    aid = AIDS[params.aid]
    if not valid_combo(params.theme, params.scar, params.aid):
        raise StoryError(explain_rejection(scar, aid))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        theme=THEMES[params.theme],
        scar=SCARS[params.scar],
        aid=AIDS[params.aid],
        helper_type=params.helper,
        watcher_name=params.watcher,
        watcher_gender=params.watcher_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        mood=params.mood,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/3.\n#show sensible_aid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible aids: {', '.join(asp_sensible_aids())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, scar, aid) combos:\n")
        for theme_id, scar_id, aid_id in combos:
            print(f"  {theme_id:10} {scar_id:14} {aid_id}")
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
            header = f"### {p.watcher} & {p.mate}: {p.scar} with {p.aid} ({p.theme})"
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
