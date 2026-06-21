#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py
========================================================

A standalone story world for a small fairy-tale domain built around **truth**
and **repetition**.

In this world, a child sets out to fetch a needed magical thing. Along the way,
three forest guardians ask the same question again and again:

    "Little traveler, what do you carry, and what do you seek?"

The story changes according to the simulated state:
- a quest requires the right kind of container,
- the hero may begin by speaking truly or proudly,
- truth wins trust and guidance,
- pride causes a detour before the hero learns to speak true.

Run it
------
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py --quest healing_water --vessel bottle
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py --quest golden_seed --vessel bottle
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly.
# File path is storyworlds/worlds/gpt-5.4/true_repetition_fairy_tale.py, so
# three dirname() calls reach storyworlds/.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def family_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Quest:
    id: str
    label: str
    need_kind: str
    need_phrase: str
    trouble: str
    fix_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    holds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    give_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ReplyStyle:
    id: str
    label: str
    true_first: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Guardian:
    id: str
    label: str
    phrase: str
    place: str
    token: str
    clue: str
    kind_tag: str = ""


@dataclass
class StoryParams:
    quest: str
    vessel: str
    gift: str
    reply_style: str
    hero_name: str
    hero_gender: str
    elder_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict] = []
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


QUESTS = {
    "healing_water": Quest(
        id="healing_water",
        label="healing water",
        need_kind="liquid",
        need_phrase="a little healing water from the Moon Spring",
        trouble="the rosebush by the cottage door had gone pale and drooping",
        fix_line="A sip of healing water would wake the roots again.",
        ending_image="By dawn the rosebush held up its head, and one red flower opened like a smile.",
        tags={"spring", "water", "garden"},
    ),
    "golden_seed": Quest(
        id="golden_seed",
        label="golden seed",
        need_kind="seed",
        need_phrase="a golden seed from the Sun Meadow",
        trouble="the village mill field had grown bare, and no wheat was rising there",
        fix_line="One golden seed would begin the green again.",
        ending_image="Soon a tall green shoot stood in the field, shining with a gold tip in the morning light.",
        tags={"seed", "garden", "field"},
    ),
    "silver_thread": Quest(
        id="silver_thread",
        label="silver thread",
        need_kind="thread",
        need_phrase="a length of silver thread from the Weaver Tree",
        trouble="the winter blanket on the elder's bed had torn straight through the middle",
        fix_line="Silver thread could mend it so warmth would stay in the cottage.",
        ending_image="That night the blanket lay smooth again, and the room looked soft and warm as a nest.",
        tags={"thread", "blanket", "weaving"},
    ),
}

VESSELS = {
    "bottle": Vessel(
        id="bottle",
        label="glass bottle",
        phrase="a small glass bottle",
        holds={"liquid"},
        tags={"bottle"},
    ),
    "pouch": Vessel(
        id="pouch",
        label="linen pouch",
        phrase="a linen pouch with a drawstring",
        holds={"seed"},
        tags={"pouch"},
    ),
    "spool": Vessel(
        id="spool",
        label="wooden spool",
        phrase="a smooth wooden spool",
        holds={"thread"},
        tags={"spool"},
    ),
    "basket": Vessel(
        id="basket",
        label="reed basket",
        phrase="a little reed basket",
        holds={"seed"},
        tags={"basket"},
    ),
}

GIFTS = {
    "oatcake": Gift(
        id="oatcake",
        label="oat cake",
        phrase="an oat cake wrapped in cloth",
        give_line="broke off a piece of oat cake",
        tags={"food", "cake"},
    ),
    "berries": Gift(
        id="berries",
        label="berries",
        phrase="a pouch of sweet berries",
        give_line="poured a few sweet berries into waiting paws and beaks",
        tags={"food", "berries"},
    ),
    "nuts": Gift(
        id="nuts",
        label="hazelnuts",
        phrase="three bright hazelnuts",
        give_line="set down a shining hazelnut",
        tags={"food", "nuts"},
    ),
}

REPLY_STYLES = {
    "true": ReplyStyle(
        id="true",
        label="true",
        true_first=True,
        tags={"truth"},
    ),
    "proud": ReplyStyle(
        id="proud",
        label="proud",
        true_first=False,
        tags={"truth", "lesson"},
    ),
}

GUARDIANS = [
    Guardian(
        id="robin",
        label="red robin",
        phrase="a red robin on the gate",
        place="at the mossy gate",
        token="a red feather",
        clue="Follow the white stones to the brook.",
        kind_tag="bird",
    ),
    Guardian(
        id="fish",
        label="silver fish",
        phrase="a silver fish in the brook",
        place="in the clear brook",
        token="a silver scale",
        clue="Climb where the hill is lit by one crooked pine.",
        kind_tag="fish",
    ),
    Guardian(
        id="deer",
        label="white deer",
        phrase="a white deer on the hill",
        place="on the hill of thyme",
        token="a pale hoofprint in the dust",
        clue="Knock three times at the hidden place, and it will open to a true heart.",
        kind_tag="deer",
    ),
]

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "Ada", "Tessa", "Wren", "Rose"]
BOY_NAMES = ["Rowan", "Tobin", "Milo", "Finn", "Ari", "Leo", "Ned", "Hugh"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for qid, quest in QUESTS.items():
        for vid, vessel in VESSELS.items():
            if quest.need_kind in vessel.holds:
                combos.append((qid, vid))
    return combos


def vessel_fits(quest: Quest, vessel: Vessel) -> bool:
    return quest.need_kind in vessel.holds


def explain_rejection(quest: Quest, vessel: Vessel) -> str:
    need = quest.need_kind
    holds = ", ".join(sorted(vessel.holds)) or "nothing useful"
    return (
        f"(No story: {quest.label} needs a container for {need}, but {vessel.label} "
        f"is for {holds}. Pick a vessel that can honestly carry the quest item.)"
    )


def opening_truth(style: ReplyStyle, index: int) -> bool:
    if style.true_first:
        return True
    return index > 0


def outcome_of(params: StoryParams) -> str:
    style = REPLY_STYLES[params.reply_style]
    return "straight" if style.true_first else "detour"


def setup_story(world: World, hero: Entity, elder: Entity, quest: Quest, vessel: Vessel, gift: Gift) -> None:
    hero.memes["love"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"Once, in a little cottage at the edge of the wood, lived {hero.id}, "
        f"a child with bright eyes and a listening heart."
    )
    world.say(
        f"One evening, {hero.id} saw that {quest.trouble}."
    )
    world.say(
        f'{hero.id}\'s {elder.family_word} spoke softly. "{quest.fix_line}"'
    )
    world.say(
        f"So {hero.id} took {vessel.phrase} and {gift.phrase}, and set out to seek {quest.need_phrase}."
    )


def guardian_question() -> str:
    return '"Little traveler, what do you carry, and what do you seek?"'


def answer_true(hero: Entity, quest: Quest, vessel: Vessel) -> str:
    return (
        f'"I carry {vessel.phrase}, and I seek {quest.label} for home. '
        f'I speak true, because I need help."'
    )


def answer_proud(hero: Entity, quest: Quest) -> str:
    return (
        f'"I need no help," said {hero.id}. "I can find {quest.label} alone."'
    )


def meet_guardian(
    world: World,
    hero: Entity,
    gift_ent: Entity,
    guardian: Guardian,
    quest: Quest,
    vessel: Vessel,
    gift: Gift,
    style: ReplyStyle,
    index: int,
) -> None:
    truthful = opening_truth(style, index)
    world.say(
        f"First" if index == 0 else ("Next" if index == 1 else "Last")
        + f", {hero.id} came to {guardian.place}, where {guardian.phrase} waited."
    )
    world.say(guardian_question())

    if truthful:
        hero.memes["truth"] += 1
        hero.memes["humility"] += 1
        world.say(answer_true(hero, quest, vessel))
        if gift_ent.meters["pieces"] >= THRESHOLD:
            gift_ent.meters["pieces"] -= 1
            world.say(
                f"{hero.id} {gift.give_line} too. The {guardian.label} was pleased."
            )
        hero.meters["clues"] += 1
        hero.memes["trust"] += 1
        world.say(f'"Then listen well," said the {guardian.label}. "{guardian.clue}"')
        world.history.append(
            {
                "guardian": guardian.label,
                "truthful": True,
                "clue": guardian.clue,
                "token": guardian.token,
            }
        )
    else:
        hero.memes["pride"] += 1
        hero.memes["fear"] += 1
        hero.meters["lost"] += 1
        world.say(answer_proud(hero, quest))
        world.say(
            f'The {guardian.label} tilted its head. "A proud answer is not a true one," it said.'
        )
        world.say(
            f"{hero.id} took the wrong path among the thorns and walked in a circle until the moon rose higher."
        )
        world.history.append(
            {
                "guardian": guardian.label,
                "truthful": False,
                "clue": "",
                "token": "",
            }
        )


def turn_to_truth(world: World, hero: Entity) -> None:
    if hero.meters["lost"] < THRESHOLD:
        return
    hero.memes["humility"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"At last {hero.id} stopped beside a black pool and saw the stars trembling there."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered that crooked roads grow from crooked words."
    )
    world.say(
        f'So {hero.id} whispered, "From now on I will speak the true thing, even if it makes me small."'
    )


def arrival(world: World, hero: Entity, quest: Quest, vessel_ent: Entity) -> None:
    hero.meters["distance"] += 1
    if quest.id == "healing_water":
        vessel_ent.meters["filled"] += 1
        world.say(
            "Beyond the hill, the Moon Spring shone in a ring of stones. The water was so clear that it held a little moon of its own."
        )
        world.say(
            f"{hero.id} filled the vessel very carefully, and the spring gave one bright silver ripple as if in blessing."
        )
    elif quest.id == "golden_seed":
        vessel_ent.meters["filled"] += 1
        world.say(
            "Beyond the hill, the Sun Meadow opened wide. In its center stood one stalk with a single golden seed at the top."
        )
        world.say(
            f"{hero.id} caught the seed in the vessel before the wind could carry it away."
        )
    else:
        vessel_ent.meters["filled"] += 1
        world.say(
            "Beyond the hill, the Weaver Tree stood with shining bark. One loose thread of silver hung from a low branch like moonlight made soft."
        )
        world.say(
            f"{hero.id} wound the silver thread onto the vessel until it lay smooth and gleaming."
        )


def return_home(world: World, hero: Entity, elder: Entity, quest: Quest, style: ReplyStyle) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    if style.true_first:
        world.say(
            f"When {hero.id} came home again, the cottage windows were still warm with lamplight."
        )
    else:
        world.say(
            f"When {hero.id} came home again, the sky was paling, but {hero.pronoun('possessive')} steps were sure at last."
        )
    world.say(
        f"{hero.id} gave the {quest.label} to {hero.pronoun('possessive')} {elder.family_word}, and together they used it at once."
    )
    world.say(quest.ending_image)
    if style.true_first:
        world.say(
            f"From that day on, people said that {hero.id} could walk straight through any wood, because true words had gone ahead."
        )
    else:
        world.say(
            f"From that day on, {hero.id} remembered that the true road is often the one that begins with a true word."
        )


def tell(
    quest: Quest,
    vessel: Vessel,
    gift: Gift,
    style: ReplyStyle,
    hero_name: str,
    hero_gender: str,
    elder_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    elder = world.add(
        Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder")
    )
    vessel_ent = world.add(
        Entity(id="vessel", kind="thing", type="vessel", label=vessel.label, phrase=vessel.phrase, tags=set(vessel.tags))
    )
    gift_ent = world.add(
        Entity(id="gift", kind="thing", type="gift", label=gift.label, phrase=gift.phrase, tags=set(gift.tags))
    )
    gift_ent.meters["pieces"] = 3.0

    setup_story(world, hero, elder, quest, vessel, gift)

    world.para()
    meet_guardian(world, hero, gift_ent, GUARDIANS[0], quest, vessel, gift, style, 0)
    turn_to_truth(world, hero)
    meet_guardian(world, hero, gift_ent, GUARDIANS[1], quest, vessel, gift, style, 1)
    meet_guardian(world, hero, gift_ent, GUARDIANS[2], quest, vessel, gift, style, 2)

    world.para()
    arrival(world, hero, quest, vessel_ent)

    world.para()
    return_home(world, hero, elder, quest, style)

    truthful_count = sum(1 for h in world.history if h["truthful"])
    world.facts.update(
        hero=hero,
        elder=elder,
        quest=quest,
        vessel=vessel,
        gift=gift,
        style=style,
        truthful_count=truthful_count,
        detour=hero.meters["lost"] >= THRESHOLD,
        outcome="straight" if style.true_first else "detour",
        shared_food=max(0, 3 - int(gift_ent.meters["pieces"])),
        vessel_full=vessel_ent.meters["filled"] >= THRESHOLD,
        history=list(world.history),
    )
    return world


KNOWLEDGE = {
    "truth": [
        (
            "What does it mean to tell the truth?",
            "To tell the truth is to say what is real and honest. True words help other people trust you."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up from the ground. In stories, a spring can seem magical because it is clear and fresh."
        )
    ],
    "seed": [
        (
            "What does a seed do?",
            "A seed is the small beginning of a plant. With soil, water, and time, it can grow into something much bigger."
        )
    ],
    "thread": [
        (
            "What is thread for?",
            "Thread is a thin strand used for sewing and mending. It can join torn cloth back together."
        )
    ],
    "bottle": [
        (
            "Why is a bottle good for carrying water?",
            "A bottle can hold liquid without letting it spill out. That makes it useful for carrying water from one place to another."
        )
    ],
    "pouch": [
        (
            "What is a pouch good for?",
            "A pouch is a small soft bag. It is good for carrying little dry things like seeds."
        )
    ],
    "spool": [
        (
            "What is a spool?",
            "A spool is a small holder you wind thread around. It keeps the thread neat so it does not tangle."
        )
    ],
    "berries": [
        (
            "What are berries?",
            "Berries are small fruits that grow on bushes or vines. Birds and people can both eat many kinds of berries."
        )
    ],
    "nuts": [
        (
            "What are hazelnuts?",
            "Hazelnuts are small round nuts with hard shells. Forest animals and people can eat them."
        )
    ],
    "cake": [
        (
            "What is an oat cake?",
            "An oat cake is a small cake or biscuit made with oats. It is simple food that travels well."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "truth",
    "spring",
    "seed",
    "thread",
    "bottle",
    "pouch",
    "spool",
    "berries",
    "nuts",
    "cake",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    vessel = f["vessel"]
    style = f["style"]
    if style.true_first:
        return [
            f'Write a fairy tale for a 3-to-5-year-old that includes the word "true" and uses repetition, where a child asks for help three times on the way to find {quest.label}.',
            f"Tell a fairy tale about {hero.id}, who carries {vessel.phrase} and wins help from three guardians by speaking the true thing each time.",
            f'Write a gentle repetitive fairy tale in which the same question is asked three times, and the child reaches home because true words open the road.',
        ]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the word "true" and uses repetition, where a child first speaks proudly, gets lost, and then learns to answer truly on the way to find {quest.label}.',
        f"Tell a fairy tale about {hero.id}, who meets three guardians asking the same question, and only finds the right road after choosing a true answer.",
        f'Write a repetitive fairy tale in which a child learns that the true road begins with a true word, and show the lesson with three similar encounters.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    vessel = f["vessel"]
    gift = f["gift"]
    hist = f["history"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who went into the wood to fetch {quest.label} for {hero.pronoun('possessive')} {elder.family_word}. The trip matters because something at home needed mending or saving."
        ),
        (
            f"What did {hero.id} carry on the journey?",
            f"{hero.id} carried {vessel.phrase} and {gift.phrase}. The vessel was needed to bring the quest item home safely."
        ),
        (
            "What question did the guardians keep asking?",
            'They kept asking, "Little traveler, what do you carry, and what do you seek?" The repeated question tested whether the child would answer honestly each time.'
        ),
    ]
    if f["detour"]:
        first = hist[0]["guardian"]
        qa.append(
            (
                f"Why did {hero.id} get lost at first?",
                f"{hero.id} answered proudly to the first guardian, the {first}, instead of speaking the true thing. Because the answer was crooked, the path turned crooked too, and the child wandered among the thorns before choosing truth."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} move through the wood so smoothly?",
                f"{hero.id} spoke truly at every meeting and shared food kindly as well. That helped the guardians trust the child and give clear directions."
            )
        )
    qa.append(
        (
            f"How did truth help {hero.id} finish the quest?",
            f"Truth won help from the guardians, and their clues led {hero.id} to {quest.label}. The story shows that honest words change the world around the child, not just the child's feelings."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"{hero.id} brought the {quest.label} home, and {quest.ending_image} The final image proves that the journey changed the home for the better."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"truth"}
    tags |= set(f["quest"].tags)
    tags |= set(f["vessel"].tags)
    tags |= set(f["gift"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append("  encounters:")
    for item in world.history:
        truth = "true" if item["truthful"] else "proud"
        clue = item["clue"] or "no clue"
        lines.append(f"    - {item['guardian']}: {truth}; {clue}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="healing_water",
        vessel="bottle",
        gift="oatcake",
        reply_style="true",
        hero_name="Lina",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="golden_seed",
        vessel="pouch",
        gift="berries",
        reply_style="proud",
        hero_name="Rowan",
        hero_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        quest="silver_thread",
        vessel="spool",
        gift="nuts",
        reply_style="true",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="golden_seed",
        vessel="basket",
        gift="nuts",
        reply_style="true",
        hero_name="Finn",
        hero_gender="boy",
        elder_type="grandfather",
    ),
]


ASP_RULES = r"""
valid(Q, V) :- quest(Q), vessel(V), needs(Q, K), holds(V, K).

straight :- chosen_style(S), style_true(S).
detour   :- chosen_style(S), not style_true(S).

outcome(straight) :- straight.
outcome(detour)   :- detour.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, quest.need_kind))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        for kind in sorted(vessel.holds):
            lines.append(asp.fact("holds", vid, kind))
    for sid, style in REPLY_STYLES.items():
        lines.append(asp.fact("style", sid))
        if style.true_first:
            lines.append(asp.fact("style_true", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_style", params.reply_style)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for params in cases:
        a = asp_outcome(params)
        p = outcome_of(params)
        if a != p:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={a} python={p}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generated a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fairy tale of true words, repeated questions, and a small quest."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--reply-style", choices=REPLY_STYLES, dest="reply_style")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"], dest="hero_gender")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"], dest="elder_type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible quest and vessel combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.vessel:
        quest = QUESTS[args.quest]
        vessel = VESSELS[args.vessel]
        if not vessel_fits(quest, vessel):
            raise StoryError(explain_rejection(quest, vessel))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.vessel is None or combo[1] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, vessel_id = rng.choice(sorted(combos))
    gift_id = args.gift or rng.choice(sorted(GIFTS))
    reply_style = args.reply_style or rng.choice(sorted(REPLY_STYLES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        quest=quest_id,
        vessel=vessel_id,
        gift=gift_id,
        reply_style=reply_style,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.reply_style not in REPLY_STYLES:
        raise StoryError(f"(Unknown reply style: {params.reply_style})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")

    quest = QUESTS[params.quest]
    vessel = VESSELS[params.vessel]
    if not vessel_fits(quest, vessel):
        raise StoryError(explain_rejection(quest, vessel))

    world = tell(
        quest=quest,
        vessel=vessel,
        gift=GIFTS[params.gift],
        style=REPLY_STYLES[params.reply_style],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, vessel) combos:\n")
        for quest, vessel in combos:
            print(f"  {quest:14} {vessel}")
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
            header = f"### {p.hero_name}: {p.quest} with {p.vessel} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
