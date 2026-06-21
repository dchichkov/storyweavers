#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/squatching_repetition_fairy_tale.py
==============================================================

A standalone storyworld for a small fairy-tale domain built around an enchanted
marsh, the muddy sound word "squatching", and deliberate repetition.

Reference seed
--------------
Write a story that includes the following words and narrative instruments.
Words: squatching
Features: Repetition
Style: Fairy Tale

World idea
----------
A child sets out on a tiny fairy-tale errand toward something lovely on the far
side of an enchanted marsh. The child first tests the marsh with bare feet or
thin shoes and hears the wet sound -- squatching. A wise forest helper sees the
danger, judges how deep and sticky the crossing is, and offers an aid that
really fits that marsh and that burden. Then the child crosses in a repeated
three-beat pattern: first step, second step, third step. The ending image shows
the errand fulfilled and the child changed from rash to careful.

Reasonableness constraint
-------------------------
Not every aid can cross every marsh, and not every aid can carry every errand.
A light errand (a silver bell or moonblossom) can go over lighter aids, but a
heavier burden (a basket of honey cakes) needs stronger support. The world model
refuses mismatches.

Run it
------
python storyworlds/worlds/gpt-5.4/squatching_repetition_fairy_tale.py
python storyworlds/worlds/gpt-5.4/squatching_repetition_fairy_tale.py --crossing peat_mire --quest honey_cakes --aid stepping_stones
python storyworlds/worlds/gpt-5.4/squatching_repetition_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/squatching_repetition_fairy_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/squatching_repetition_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/<model>/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTIOUS_TRAITS = {"careful", "patient", "gentle"}
HASTY_TRAITS = {"hasty", "bold", "restless"}


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
        female = {"girl", "woman", "mother", "grandmother", "fairy"}
        male = {"boy", "man", "father", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Crossing:
    id: str
    label: str
    place_line: str
    far_side: str
    depth: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    item: str
    phrase: str
    reason: str
    burden: int
    return_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    support: int
    capacity: int
    provider: str
    provider_type: str
    provider_intro: str
    step_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    crossing: str
    quest: str
    aid: str
    hero_name: str
    hero_gender: str
    helper_name: str
    trait: str
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
    apply: Callable[[World], list[str]]


def _r_stuck_fear(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if hero is None or helper is None:
        return []
    if hero.meters["stuck"] < THRESHOLD:
        return []
    sig = ("stuck_fear", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    helper.memes["urgency"] += 1
    return ["__stuck__"]


def _r_three_steps_complete(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["progress"] < 3:
        return []
    sig = ("complete", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["arrived"] += 1
    hero.memes["confidence"] += 1
    return ["__arrived__"]


CAUSAL_RULES = [
    Rule(name="stuck_fear", apply=_r_stuck_fear),
    Rule(name="three_steps_complete", apply=_r_three_steps_complete),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


CROSSINGS = {
    "dew_marsh": Crossing(
        id="dew_marsh",
        label="the Dew Marsh",
        place_line="Beyond the cottage garden lay the Dew Marsh, green as glass at the edges and soft in the middle.",
        far_side="the moonblossom bank",
        depth=1,
        tags={"marsh", "wet", "crossing"},
    ),
    "reed_bog": Crossing(
        id="reed_bog",
        label="the Reed Bog",
        place_line="Past the hazel gate waited the Reed Bog, where thin reeds bowed and the mud shivered under them.",
        far_side="the heron mound",
        depth=2,
        tags={"bog", "wet", "crossing"},
    ),
    "peat_mire": Crossing(
        id="peat_mire",
        label="the Peat Mire",
        place_line="At the edge of the fir wood spread the Peat Mire, dark and deep, with bubbles blinking in its black water.",
        far_side="the grandmother willow",
        depth=3,
        tags={"mire", "wet", "crossing"},
    ),
}

QUESTS = {
    "moonblossom": Quest(
        id="moonblossom",
        item="moonblossom",
        phrase="a moonblossom",
        reason="for the windowsill cup at home",
        burden=1,
        return_image="The moonblossom glowed in the cottage window that night like a little star caught in a teacup.",
        tags={"flower", "light_burden"},
    ),
    "silver_bell": Quest(
        id="silver_bell",
        item="silver bell",
        phrase="the silver bell",
        reason="for the lamb who had lost its sound",
        burden=1,
        return_image="Soon the lamb wore the silver bell again, and its bright tinkle skipped through the yard.",
        tags={"bell", "light_burden"},
    ),
    "honey_cakes": Quest(
        id="honey_cakes",
        item="honey cakes",
        phrase="a basket of honey cakes",
        reason="for the grandmother beyond the marsh",
        burden=2,
        return_image="The grandmother willow-house smelled of warm honey, and not one cake had slipped into the mud.",
        tags={"food", "heavy_burden"},
    ),
}

AIDS = {
    "fern_slippers": Aid(
        id="fern_slippers",
        label="fern slippers",
        phrase="a pair of wide fern slippers woven with rushes",
        support=1,
        capacity=1,
        provider="Moss",
        provider_type="fairy",
        provider_intro="a moss fairy no bigger than a pinecone",
        step_style="wide",
        tags={"slippers", "fairy_help"},
    ),
    "stepping_stones": Aid(
        id="stepping_stones",
        label="stepping stones",
        phrase="three flat stepping stones spotted with lichen",
        support=2,
        capacity=2,
        provider="Heron",
        provider_type="thing",
        provider_intro="a tall gray heron with patient eyes",
        step_style="stone",
        tags={"stones", "bird_help"},
    ),
    "moon_bridge": Aid(
        id="moon_bridge",
        label="moon bridge",
        phrase="a pale moon bridge made of silver boards and willow rope",
        support=3,
        capacity=2,
        provider="Grandmother Hazel",
        provider_type="woman",
        provider_intro="old Grandmother Hazel with a lantern shaped like a pear",
        step_style="bridge",
        tags={"bridge", "elder_help"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsa", "Nora", "Tessa", "Wren"]
BOY_NAMES = ["Tobin", "Milo", "Rowan", "Finn", "Evan", "Pip"]
TRAITS = ["careful", "patient", "gentle", "hasty", "bold", "restless"]


def valid_combo(crossing: Crossing, quest: Quest, aid: Aid) -> bool:
    return aid.support >= crossing.depth and aid.capacity >= quest.burden


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for crossing_id, crossing in CROSSINGS.items():
        for quest_id, quest in QUESTS.items():
            for aid_id, aid in AIDS.items():
                if valid_combo(crossing, quest, aid):
                    out.append((crossing_id, quest_id, aid_id))
    return sorted(out)


def explain_rejection(crossing: Crossing, quest: Quest, aid: Aid) -> str:
    if aid.support < crossing.depth:
        return (
            f"(No story: {aid.label} cannot safely cross {crossing.label}. "
            f"It supports depth {aid.support}, but that marsh needs {crossing.depth}.)"
        )
    if aid.capacity < quest.burden:
        return (
            f"(No story: {aid.label} can cross, but it cannot carry {quest.phrase}. "
            f"That errand is too heavy for it.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    crossing = CROSSINGS[params.crossing]
    if params.trait in CAUTIOUS_TRAITS:
        return "steady"
    if crossing.depth >= 3:
        return "rescued"
    return "muddy"


def helper_provider_entity(aid: Aid) -> Entity:
    return Entity(
        id="helper",
        kind="character",
        type=aid.provider_type,
        label=aid.provider.lower(),
        phrase=aid.provider_intro,
        role="helper",
    )


def first_warning(world: World, hero: Entity, crossing: Crossing) -> None:
    world.say(
        f"{hero.id} put one foot onto the edge of {crossing.label}, and the mud answered with a small wet sound: squatching."
    )
    hero.meters["mud"] += 1
    hero.memes["wonder"] += 1
    world.say(
        "The child listened. The reeds bent. The water winked. Again came the sound -- squatching, squatching."
    )


def second_misstep(world: World, hero: Entity, crossing: Crossing) -> None:
    hero.meters["mud"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} was eager, and a second step went in deeper. The marsh said it again, only lower and wetter: squatching, squatching, squatching."
    )
    if crossing.depth >= 3:
        hero.meters["stuck"] += 1
    else:
        hero.meters["wobble"] += 1
    propagate(world, narrate=False)


def helper_arrives(world: World, hero: Entity, helper: Entity, aid: Aid, crossing: Crossing, quest: Quest) -> None:
    world.say(
        f"Just then there came {aid.provider_intro}. {helper.label_word.capitalize()} looked from the dark water to {quest.phrase} and said, "
        f'"Little one, {crossing.label} keeps what is stepped on carelessly. You need {aid.phrase}."'
    )


def rescue_if_needed(world: World, hero: Entity, helper: Entity, aid: Aid) -> None:
    if hero.meters["stuck"] < THRESHOLD:
        return
    hero.meters["stuck"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.label_word.capitalize()} reached out with {aid.label} and drew {hero.id} free before the marsh could steal another shoe."
    )


def repeated_crossing(world: World, hero: Entity, helper: Entity, crossing: Crossing, aid: Aid) -> None:
    steps = [
        "First",
        "Then",
        "Last",
    ]
    endings = {
        "wide": [
            "the first broad slipper floated and held",
            "the second broad slipper sighed but did not sink",
            "the third broad slipper kissed the far grass",
        ],
        "stone": [
            "the first stone sat firm under a careful foot",
            "the second stone waited bright and still",
            "the third stone touched the bank like a promise kept",
        ],
        "bridge": [
            "the first silver board gave a soft moonlit creak",
            "the second silver board shone straight over the dark water",
            "the third silver board ended on safe roots",
        ],
    }
    phrases = endings[aid.step_style]
    for index in range(3):
        hero.meters["progress"] += 1
        hero.memes["care"] += 1
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
        propagate(world, narrate=False)
        world.say(
            f"{steps[index]}, {hero.id} stepped; {phrases[index]}. And under everything, far below now, the marsh could only mutter squatching."
        )


def receive_quest_item(world: World, hero: Entity, crossing: Crossing, quest: Quest) -> None:
    hero.meters["carrying"] += 1
    world.say(
        f"On the far side, at {crossing.far_side}, {hero.id} found {quest.phrase} {quest.reason}."
    )


def return_home(world: World, hero: Entity, helper: Entity, quest: Quest, outcome: str) -> None:
    hero.memes["joy"] += 1
    hero.memes["wisdom"] += 1
    if outcome == "steady":
        line = f"{hero.id} thanked {helper.label_word} and came home with clean feet and a careful heart."
    elif outcome == "muddy":
        line = f"{hero.id} thanked {helper.label_word} and came home with muddy toes, but with sense enough now to laugh softly at them."
    else:
        line = f"{hero.id} thanked {helper.label_word} and came home shaking a little, yet wiser than before."
    world.say(line)
    world.say(quest.return_image)


def tell(crossing: Crossing, quest: Quest, aid: Aid, hero_name: str, hero_gender: str, trait: str) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"trait": trait},
            tags={trait},
        )
    )
    helper = world.add(helper_provider_entity(aid))
    world.add(Entity(id="crossing", kind="thing", type="marsh", label=crossing.label, tags=set(crossing.tags)))
    world.add(Entity(id="aid", kind="thing", type="aid", label=aid.label, phrase=aid.phrase, tags=set(aid.tags)))
    world.add(Entity(id="quest", kind="thing", type="quest_item", label=quest.item, phrase=quest.phrase, tags=set(quest.tags)))

    world.say(
        f"Once, when the evening sky was pale as milk, {hero_name} set out from a little cottage to fetch {quest.phrase} {quest.reason}."
    )
    world.say(crossing.place_line)
    world.say(
        f"{hero_name} was a {trait} child, but even a {trait} child can be tempted by the shortest path."
    )

    world.para()
    first_warning(world, hero, crossing)
    if trait in HASTY_TRAITS:
        second_misstep(world, hero, crossing)

    world.para()
    helper_arrives(world, hero, helper, aid, crossing, quest)
    rescue_if_needed(world, hero, helper, aid)
    repeated_crossing(world, hero, helper, crossing, aid)

    world.para()
    receive_quest_item(world, hero, crossing, quest)
    return_home(world, hero, helper, quest, outcome_of(StoryParams(
        crossing=crossing.id,
        quest=quest.id,
        aid=aid.id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=aid.provider,
        trait=trait,
        seed=None,
    )))

    world.facts.update(
        crossing=crossing,
        quest=quest,
        aid=aid,
        hero=hero,
        helper=helper,
        trait=trait,
        outcome=outcome_of(StoryParams(
            crossing=crossing.id,
            quest=quest.id,
            aid=aid.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            helper_name=aid.provider,
            trait=trait,
            seed=None,
        )),
        repeated_steps=3,
        heard_squatching=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    crossing = world.facts["crossing"]
    quest = world.facts["quest"]
    aid = world.facts["aid"]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the exact word "squatching" and uses repetition in the crossing scene.',
        f"Tell a gentle fairy tale where {hero.label} must cross {crossing.label} to fetch {quest.phrase}, first hears the marsh go squatching, and then crosses safely with {aid.label}.",
        f'Write a story in fairy-tale style with a repeated three-beat pattern -- first step, second step, third step -- and end with a warm image showing that the errand was finished.',
    ]


KNOWLEDGE = {
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is soft wet ground with shallow water and plants growing in it. Your feet can sink if the ground is muddy."
        )
    ],
    "bog": [
        (
            "Why can a bog be hard to cross?",
            "A bog is soft and squishy, so your feet can sink down into it. That makes walking slow and slippery."
        )
    ],
    "mire": [
        (
            "What is a mire?",
            "A mire is a very wet patch of ground with deep sticky mud. People use the word when the earth can trap your feet."
        )
    ],
    "wet": [
        (
            "Why does mud make squishy sounds?",
            "Wet mud moves and squeezes when you step in it. The air and water shift around your foot and make soft sounds."
        )
    ],
    "stones": [
        (
            "Why do stepping stones help?",
            "Stepping stones give your feet firm places to land. They keep you up above the soft mud."
        )
    ],
    "bridge": [
        (
            "Why is a bridge useful over mud or water?",
            "A bridge gives you a strong path over a hard place to cross. It helps you stay dry and steady."
        )
    ],
    "slippers": [
        (
            "Why would wide slippers help in soft mud?",
            "Wide slippers spread your weight out more than a narrow shoe. That can help you sink less in soft ground."
        )
    ],
    "fairy_help": [
        (
            "What do helpers do in fairy tales?",
            "Helpers give wise advice or a useful gift when the hero does not know the safe way. They often appear just when they are needed."
        )
    ],
}
KNOWLEDGE_ORDER = ["marsh", "bog", "mire", "wet", "stones", "bridge", "slippers", "fairy_help"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    crossing = world.facts["crossing"]
    quest = world.facts["quest"]
    aid = world.facts["aid"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who had to cross {crossing.label}, and {helper.label_word}, who showed the safe way."
        ),
        (
            f"Why did {hero.label} go toward the marsh?",
            f"{hero.label} went to fetch {quest.phrase} {quest.reason}. The errand is what drew the child toward the dangerous ground."
        ),
        (
            "What did the marsh sound like?",
            'It sounded like "squatching." The repeated muddy sound showed that the ground was soft and sticky underfoot.'
        ),
    ]
    if outcome == "steady":
        qa.append(
            (
                f"How did {hero.label} get across safely?",
                f"{helper.label_word.capitalize()} offered {aid.phrase}, and {hero.label} crossed in three careful steps. Because {hero.pronoun('subject')} listened in time, the marsh never trapped {hero.pronoun('object')}."
            )
        )
    elif outcome == "muddy":
        qa.append(
            (
                f"Why were {hero.label}'s feet muddy?",
                f"{hero.label} took an extra eager step before listening, so the marsh smeared mud over {hero.pronoun('possessive')} feet. After that, {helper.label_word} gave {hero.pronoun('object')} {aid.label}, and the crossing became safe."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} need help getting free?",
                f"{hero.label} took a second hasty step in a very deep mire and got stuck. {helper.label_word.capitalize()} reached out with {aid.label} and pulled {hero.pronoun('object')} free before the marsh could keep {hero.pronoun('possessive')} shoe."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"{hero.label} came home wiser and finished the errand. {quest.return_image}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    crossing = world.facts["crossing"]
    aid = world.facts["aid"]
    tags = set(crossing.tags) | set(aid.tags) | {"wet"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
        parts: list[str] = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crossing="dew_marsh",
        quest="moonblossom",
        aid="fern_slippers",
        hero_name="Lina",
        hero_gender="girl",
        helper_name="Moss",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        crossing="reed_bog",
        quest="silver_bell",
        aid="stepping_stones",
        hero_name="Milo",
        hero_gender="boy",
        helper_name="Heron",
        trait="bold",
        seed=None,
    ),
    StoryParams(
        crossing="peat_mire",
        quest="honey_cakes",
        aid="moon_bridge",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Grandmother Hazel",
        trait="hasty",
        seed=None,
    ),
]


ASP_RULES = r"""
valid(C, Q, A) :- crossing(C), quest(Q), aid(A), depth(C, D), support(A, S), S >= D,
                  burden(Q, B), capacity(A, K), K >= B.

steady_trait(T) :- cautious_trait(T).
hasty_trait(T)  :- trait(T), not steady_trait(T).

outcome(steady)  :- trait(T), steady_trait(T).
outcome(rescued) :- trait(T), hasty_trait(T), chosen_crossing(C), depth(C, D), D >= 3.
outcome(muddy)   :- trait(T), hasty_trait(T), chosen_crossing(C), depth(C, D), D < 3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for crossing_id, crossing in CROSSINGS.items():
        lines.append(asp.fact("crossing", crossing_id))
        lines.append(asp.fact("depth", crossing_id, crossing.depth))
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        lines.append(asp.fact("burden", quest_id, quest.burden))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("support", aid_id, aid.support))
        lines.append(asp.fact("capacity", aid_id, aid.capacity))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
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
        asp.fact("chosen_crossing", params.crossing),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos parity holds ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    scenarios = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    mismatches = []
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append((params, asp_outcome(params), outcome_of(params)))
    if not mismatches:
        print(f"OK: outcome parity holds on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, a_out, p_out in mismatches[:5]:
            print(" ", params, a_out, p_out)

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=False, header="smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE FAILURE: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child, a marsh, a wise helper, and the repeated sound 'squatching'."
    )
    ap.add_argument("--crossing", choices=sorted(CROSSINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--aid", choices=sorted(AIDS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crossing is not None and args.quest is not None and args.aid is not None:
        crossing = CROSSINGS[args.crossing]
        quest = QUESTS[args.quest]
        aid = AIDS[args.aid]
        if not valid_combo(crossing, quest, aid):
            raise StoryError(explain_rejection(crossing, quest, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.crossing is None or combo[0] == args.crossing)
        and (args.quest is None or combo[1] == args.quest)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crossing_id, quest_id, aid_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    helper_name = AIDS[aid_id].provider
    return StoryParams(
        crossing=crossing_id,
        quest=quest_id,
        aid=aid_id,
        hero_name=name,
        hero_gender=gender,
        helper_name=helper_name,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crossing not in CROSSINGS:
        raise StoryError(f"(Unknown crossing: {params.crossing})")
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    crossing = CROSSINGS[params.crossing]
    quest = QUESTS[params.quest]
    aid = AIDS[params.aid]
    if not valid_combo(crossing, quest, aid):
        raise StoryError(explain_rejection(crossing, quest, aid))

    world = tell(
        crossing=crossing,
        quest=quest,
        aid=aid,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (crossing, quest, aid) combos:\n")
        for crossing_id, quest_id, aid_id in combos:
            print(f"  {crossing_id:10} {quest_id:12} {aid_id}")
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

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.crossing}, {p.quest}, {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
