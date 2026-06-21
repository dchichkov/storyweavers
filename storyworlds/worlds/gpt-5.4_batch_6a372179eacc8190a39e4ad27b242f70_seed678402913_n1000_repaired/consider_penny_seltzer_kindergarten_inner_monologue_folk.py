#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/consider_penny_seltzer_kindergarten_inner_monologue_folk.py
======================================================================================

A small storyworld about honesty in a kindergarten told in a light folk-tale
voice. A child finds a penny, feels tempted, pauses to consider what is right,
and resolves the trouble either quickly or after a guilty delay. Every story
includes a cup of seltzer at the end, so the found coin is never treated as a
real way for a kindergartener to buy a drink.

Run it
------
    python storyworlds/worlds/gpt-5.4/consider_penny_seltzer_kindergarten_inner_monologue_folk.py
    python storyworlds/worlds/gpt-5.4/consider_penny_seltzer_kindergarten_inner_monologue_folk.py --place art_table --need rubbing --choice ask_teacher
    python storyworlds/worlds/gpt-5.4/consider_penny_seltzer_kindergarten_inner_monologue_folk.py --choice buy_seltzer
    python storyworlds/worlds/gpt-5.4/consider_penny_seltzer_kindergarten_inner_monologue_folk.py --all --qa
    python storyworlds/worlds/gpt-5.4/consider_penny_seltzer_kindergarten_inner_monologue_folk.py --verify
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
SENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    owner_name: str
    owner_gender: str
    reason: str
    place_tags: set[str] = field(default_factory=set)
    opening: str = ""
    loss_line: str = ""
    return_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    sense: int
    prompt: str
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


def _r_owner_sad(world: World) -> list[str]:
    penny = world.get("penny")
    owner = world.get("owner")
    sig = ("owner_sad",)
    if sig in world.fired:
        return []
    if penny.meters["lost"] >= THRESHOLD and owner.memes["needs_penny"] >= THRESHOLD:
        world.fired.add(sig)
        owner.memes["sad"] += 1
        return ["__owner_sad__"]
    return []


def _r_return_relief(world: World) -> list[str]:
    penny = world.get("penny")
    owner = world.get("owner")
    finder = world.get("finder")
    teacher = world.get("teacher")
    sig = ("return_relief",)
    if sig in world.fired:
        return []
    if penny.meters["returned"] >= THRESHOLD:
        world.fired.add(sig)
        owner.memes["sad"] = 0.0
        owner.memes["relief"] += 1
        finder.memes["pride"] += 1
        finder.memes["worry"] = 0.0
        teacher.memes["trust"] += 1
        return ["__returned__"]
    return []


def _r_hidden_worry(world: World) -> list[str]:
    finder = world.get("finder")
    penny = world.get("penny")
    sig = ("hidden_worry",)
    if sig in world.fired:
        return []
    if penny.meters["hidden"] >= THRESHOLD:
        world.fired.add(sig)
        finder.memes["worry"] += 1
        return ["__worry__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="owner_sad", tag="social", apply=_r_owner_sad),
    Rule(name="return_relief", tag="social", apply=_r_return_relief),
    Rule(name="hidden_worry", tag="inner", apply=_r_hidden_worry),
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


PLACES = {
    "art_table": Place(
        id="art_table",
        label="the art table",
        phrase="by the art table where paper leaves waited in neat stacks",
        clue="a smear of green crayon lay nearby",
        tags={"art"},
    ),
    "coat_hooks": Place(
        id="coat_hooks",
        label="the coat hooks",
        phrase="under the coat hooks where little sweaters hung like sleepy birds",
        clue="a red mitten rested beside it",
        tags={"hooks"},
    ),
    "counting_rug": Place(
        id="counting_rug",
        label="the counting rug",
        phrase="on the counting rug with its stitched numbers and bright squares",
        clue="a wooden counting bear was tipped on its side",
        tags={"math"},
    ),
}

NEEDS = {
    "rubbing": Need(
        id="rubbing",
        owner_name="Junie",
        owner_gender="girl",
        reason="for a leaf-rubbing picture",
        place_tags={"art"},
        opening="Junie had brought a penny for a leaf-rubbing picture, so she could make one bright round moon on her paper.",
        loss_line="Soon Junie patted her pocket and whispered that the penny for her picture was gone.",
        return_line="Junie held the penny over her leaf page as if someone had returned a small moon to the sky.",
        tags={"art", "honesty"},
    ),
    "lucky": Need(
        id="lucky",
        owner_name="Owen",
        owner_gender="boy",
        reason="as a lucky penny from his grandmother",
        place_tags={"hooks"},
        opening="Owen kept a lucky penny from his grandmother in the tiny pocket of his cardigan.",
        loss_line="Soon Owen searched his cardigan pocket with round, worried eyes and said his lucky penny was gone.",
        return_line="Owen closed his hand around the penny and smiled the slow smile of someone who has found a small treasure twice.",
        tags={"luck", "honesty"},
    ),
    "counting": Need(
        id="counting",
        owner_name="Mara",
        owner_gender="girl",
        reason="for counting game time",
        place_tags={"math"},
        opening="Mara had brought a penny for counting game time, where the class made towers of little numbers on the rug.",
        loss_line="Soon Mara looked at the counting rug and said the penny she needed for game time was missing.",
        return_line="Mara set the penny on the rug with the careful joy of placing the number one back where it belonged.",
        tags={"math", "honesty"},
    ),
}

CHOICES = {
    "ask_teacher": Choice(
        id="ask_teacher",
        sense=2,
        prompt="ask the teacher who it belongs to",
        tags={"honest", "teacher_help"},
    ),
    "keep_then_confess": Choice(
        id="keep_then_confess",
        sense=1,
        prompt="hide it in a pocket first and confess later",
        tags={"confess", "worry"},
    ),
    "buy_seltzer": Choice(
        id="buy_seltzer",
        sense=0,
        prompt="try to buy the class seltzer with it",
        tags={"unreasonable"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Ella", "Ruby", "Maya", "Tess"]
BOY_NAMES = ["Ben", "Noah", "Finn", "Theo", "Sam", "Eli", "Leo", "Max"]
TRAITS = ["careful", "curious", "gentle", "bright", "quiet", "thoughtful"]


def need_fits(place: Place, need: Need) -> bool:
    return bool(place.tags & need.place_tags)


def sensible_choices() -> list[Choice]:
    return [choice for choice in CHOICES.values() if choice.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for need_id, need in NEEDS.items():
            if not need_fits(place, need):
                continue
            for choice_id, choice in CHOICES.items():
                if choice.sense >= SENSE_MIN:
                    combos.append((place_id, need_id, choice_id))
    return combos


def explain_rejection(place: Place, need: Need) -> str:
    return (
        f"(No story: {need.reason} does not fit {place.label}. "
        f"Choose a place that matches the reason the penny matters.)"
    )


def explain_choice(choice_id: str) -> str:
    if choice_id == "buy_seltzer":
        return (
            "(No story: a single penny is not a sensible way for a kindergartener "
            "to buy the class seltzer. In this world, the right choices are to ask "
            "the teacher or confess and return the coin.)"
        )
    return "(No story: that choice is not allowed here.)"


def predict_owner_tears(world: World) -> dict:
    sim = world.copy()
    penny = sim.get("penny")
    penny.meters["lost"] = 1.0
    propagate(sim, narrate=False)
    owner = sim.get("owner")
    return {
        "owner_sad": owner.memes["sad"] >= THRESHOLD,
    }


def introduce(world: World, finder: Entity, place: Place, need: Need) -> None:
    world.say(
        f"In a kindergarten bright as a buttercup, {finder.id} came in with a "
        f"{finder.attrs['trait']} heart and watchful eyes."
    )
    world.say(
        f"That morning the children were busy {place.phrase}, and even the sunlight "
        f"looked as if it had stopped to listen."
    )
    world.say(need.opening)


def find_penny(world: World, finder: Entity, place: Place) -> None:
    penny = world.get("penny")
    penny.meters["found"] += 1
    world.say(
        f"Then {finder.id} saw a penny on the floor {place.phrase}. It winked up "
        f"from the linoleum as bright as a tiny brass eye, and {place.clue}"
    )


def inner_monologue(world: World, finder: Entity, need: Need) -> None:
    pred = predict_owner_tears(world)
    world.facts["predicted_owner_sad"] = pred["owner_sad"]
    finder.memes["temptation"] += 1
    second = ""
    if pred["owner_sad"]:
        second = f' Then a smaller thought answered, "I should consider whose penny this is."'
    world.say(
        f'Inside, {finder.id} thought, "It is only one penny. I could close my fist '
        f'and no one would know."{second}'
    )


def teacher_sets_snack(world: World, teacher: Entity) -> None:
    world.say(
        f"Across the room, {teacher.label_word.capitalize()} was setting little paper cups "
        f"beside a cold bottle of lemon seltzer for snack time later."
    )


def choose_ask_teacher(world: World, finder: Entity, teacher: Entity) -> None:
    penny = world.get("penny")
    finder.memes["honesty"] += 1
    penny.meters["carried_to_teacher"] += 1
    world.say(
        f'So {finder.id} opened {finder.pronoun("possessive")} hand and walked to '
        f'{teacher.label_word}. "I found this penny," {finder.pronoun()} said. '
        f'"Will you help me find its home?"'
    )


def choose_keep(world: World, finder: Entity) -> None:
    penny = world.get("penny")
    penny.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But temptation tugged once more, and {finder.id} slipped the penny into "
        f"{finder.pronoun('possessive')} pocket. At once the coin felt heavier than a stone."
    )


def owner_notices(world: World, owner: Entity, need: Need) -> None:
    penny = world.get("penny")
    penny.meters["lost"] += 1
    owner.memes["needs_penny"] += 1
    propagate(world, narrate=False)
    world.say(need.loss_line)


def teacher_asks(world: World, teacher: Entity, owner: Entity) -> None:
    world.say(
        f'{teacher.label_word.capitalize()} lifted the penny where all the children could see. '
        f'"Who is missing this small brown coin?" {teacher.pronoun()} asked.'
    )
    world.say(
        f"{owner.id} looked up at once, as if someone had spoken the secret name of "
        f"{owner.pronoun('possessive')} trouble."
    )


def confess(world: World, finder: Entity, teacher: Entity) -> None:
    finder.memes["honesty"] += 1
    finder.memes["shame"] += 1
    penny = world.get("penny")
    penny.meters["hidden"] = 0.0
    penny.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Before {teacher.label_word} could say more, {finder.id} felt the hot pinch of '
        f'worry and whispered, "I found it first and hid it in my pocket. I am sorry."'
    )
    world.say(
        f'{finder.id} held the penny out on a small open palm, and the truth looked '
        f'brighter than the coin.'
    )


def return_direct(world: World, finder: Entity, teacher: Entity) -> None:
    penny = world.get("penny")
    penny.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{teacher.label_word.capitalize()} nodded, and {finder.id} placed the penny '
        f'in {teacher.pronoun("possessive")} hand for its real owner.'
    )


def owner_receives(world: World, owner: Entity, need: Need) -> None:
    world.say(need.return_line)


def lesson(world: World, teacher: Entity, finder: Entity, choice: Choice) -> None:
    if choice.id == "ask_teacher":
        world.say(
            f'{teacher.label_word.capitalize()} bent down and said, "A small coin can '
            f'carry a big choice. You chose the straight path first."'
        )
    else:
        world.say(
            f'{teacher.label_word.capitalize()} bent down and said, "The straight path is '
            f'best at the start, but I am glad you turned toward it while there was still time."'
        )
    world.say(
        f"{finder.id} felt {finder.pronoun('possessive')} tight little worry loosen, the way a knot loosens when kind hands untie it."
    )


def seltzer_ending(world: World, teacher: Entity, finder: Entity, owner: Entity) -> None:
    finder.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f"When snack time came, {teacher.label_word} poured the lemon seltzer into "
        f"little cups. The bubbles climbed and whispered like tiny silver ladders."
    )
    world.say(
        f"{finder.id} and {owner.id} stood side by side, and the penny was where it "
        f"belonged. They clinked their paper cups softly, and the day tasted light again."
    )


def tell(
    place: Place,
    need: Need,
    choice: Choice,
    *,
    finder_name: str = "Mina",
    finder_gender: str = "girl",
    finder_trait: str = "thoughtful",
    teacher_gender: str = "teacher_f",
) -> World:
    world = World()
    finder = world.add(Entity(
        id=finder_name,
        kind="character",
        type=finder_gender,
        role="finder",
        attrs={"trait": finder_trait},
    ))
    owner = world.add(Entity(
        id=need.owner_name,
        kind="character",
        type=need.owner_gender,
        role="owner",
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_gender,
        role="teacher",
        label="the teacher",
    ))
    world.add(Entity(
        id="penny",
        kind="thing",
        type="coin",
        label="penny",
        phrase="a penny",
    ))

    introduce(world, finder, place, need)
    find_penny(world, finder, place)
    inner_monologue(world, finder, need)
    teacher_sets_snack(world, teacher)

    world.para()
    if choice.id == "ask_teacher":
        choose_ask_teacher(world, finder, teacher)
        owner_notices(world, owner, need)
        teacher_asks(world, teacher, owner)
        return_direct(world, finder, teacher)
    elif choice.id == "keep_then_confess":
        choose_keep(world, finder)
        owner_notices(world, owner, need)
        world.say(
            f'Inside, {finder.id} thought, "This pocket feels too dark. I do not want '
            f'to keep another child\'s sadness next to my heart."'
        )
        confess(world, finder, teacher)
    else:
        raise StoryError(explain_choice(choice.id))

    world.para()
    owner_receives(world, owner, need)
    lesson(world, teacher, finder, choice)
    world.para()
    seltzer_ending(world, teacher, finder, owner)

    outcome = "direct_return" if choice.id == "ask_teacher" else "confession"
    world.facts.update(
        place=place,
        need=need,
        choice=choice,
        finder=finder,
        owner=owner,
        teacher=teacher,
        outcome=outcome,
        owner_was_sad=owner.memes["relief"] >= THRESHOLD,
        honest=finder.memes["honesty"] >= THRESHOLD,
        worried=finder.memes["shame"] >= THRESHOLD or finder.memes["worry"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    need: str
    choice: str
    finder_name: str
    finder_gender: str
    teacher_gender: str
    finder_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="art_table",
        need="rubbing",
        choice="ask_teacher",
        finder_name="Mina",
        finder_gender="girl",
        teacher_gender="teacher_f",
        finder_trait="thoughtful",
    ),
    StoryParams(
        place="coat_hooks",
        need="lucky",
        choice="keep_then_confess",
        finder_name="Ben",
        finder_gender="boy",
        teacher_gender="teacher_m",
        finder_trait="curious",
    ),
    StoryParams(
        place="counting_rug",
        need="counting",
        choice="ask_teacher",
        finder_name="Ruby",
        finder_gender="girl",
        teacher_gender="teacher_f",
        finder_trait="gentle",
    ),
    StoryParams(
        place="art_table",
        need="rubbing",
        choice="keep_then_confess",
        finder_name="Theo",
        finder_gender="boy",
        teacher_gender="teacher_m",
        finder_trait="bright",
    ),
]


KNOWLEDGE = {
    "penny": [
        (
            "What is a penny?",
            "A penny is a small coin. In the United States, it is worth one cent."
        )
    ],
    "honesty": [
        (
            "Why is it important to return something you find?",
            "Returning something you find helps the person who lost it and shows honesty. Even a small thing can matter a lot to someone else."
        )
    ],
    "seltzer": [
        (
            "What is seltzer?",
            "Seltzer is bubbly water. The bubbles are what make it fizz on your tongue."
        )
    ],
    "art": [
        (
            "How can a penny be used in art?",
            "A penny can be rubbed under paper with a crayon to make its round shape appear. Children sometimes use coins for simple texture art with a grown-up helping."
        )
    ],
    "math": [
        (
            "How can coins help with counting?",
            "Coins can be lined up, moved, and counted one by one. That makes them useful for simple number games."
        )
    ],
    "luck": [
        (
            "What is a lucky coin?",
            "A lucky coin is a coin someone keeps because it feels special or reminds them of a person they love. The luck is in the meaning, not in magic."
        )
    ],
    "teacher_help": [
        (
            "Why should a child tell a teacher about a found coin?",
            "A teacher can help find the owner in a fair way. Asking a grown-up keeps the problem small and honest."
        )
    ],
    "worry": [
        (
            "Why can hiding a small wrong thing feel heavy?",
            "A hidden wrong choice can make your body feel tight and your mind feel busy. Worry grows because you know the choice is not right."
        )
    ],
}
KNOWLEDGE_ORDER = ["penny", "honesty", "seltzer", "art", "math", "luck", "teacher_help", "worry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    need = f["need"]
    choice = f["choice"]
    place = f["place"]
    if choice.id == "ask_teacher":
        return [
            'Write a folk-tale-style kindergarten story that includes the words "consider", "penny", and "seltzer", and uses inner monologue.',
            f"Tell a gentle story where a {finder.type} named {finder.id} finds a penny near {place.label}, pauses to consider who might need it, and asks the teacher for help.",
            f"Write a simple tale for young children in which a found penny matters because it is needed {need.reason}, and the ending shows honesty making snack time feel light again.",
        ]
    return [
        'Write a folk-tale-style kindergarten story that includes the words "consider", "penny", and "seltzer", and uses inner monologue.',
        f"Tell a gentle story where a {finder.type} named {finder.id} hides a found penny for a moment, then listens to an uneasy inner voice and confesses.",
        f"Write a simple kindergarten tale where a child keeps a penny too long, returns it before snack, and learns that honesty feels lighter than secrecy.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    owner = f["owner"]
    teacher = f["teacher"]
    need = f["need"]
    place = f["place"]
    choice = f["choice"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {finder.id}, who found a penny in kindergarten, {owner.id}, who needed it {need.reason}, and the teacher who helped set things right."
        ),
        (
            f"Where did {finder.id} find the penny?",
            f"{finder.id} found it near {place.label}. The place matters because that clue fit the reason the penny belonged to {owner.id}."
        ),
        (
            f"Why did the penny matter to {owner.id}?",
            f"It mattered because {owner.id} needed it {need.reason}. That made the coin small in size but important in the story."
        ),
        (
            f"What did {finder.id} think inside?",
            f"{finder.id} first felt tempted, but then thought about what was right. The inner monologue shows {finder.pronoun('object')} stopping to consider another child's loss before choosing."
        ),
    ]
    if choice.id == "ask_teacher":
        out.append(
            (
                f"How was the problem solved?",
                f"{finder.id} took the penny to the teacher right away, and together they asked who it belonged to. Because the truth came quickly, {owner.id} got the coin back before the sadness could grow much larger."
            )
        )
    else:
        out.append(
            (
                f"Why did {finder.id} confess?",
                f"{finder.id} confessed because hiding the penny made {finder.pronoun('object')} feel worried and heavy inside. When {owner.id} spoke about the missing coin, the finder understood the hurt was real and chose honesty."
            )
        )
    out.append(
        (
            "How did the story end?",
            f"It ended with the penny returned, the teacher giving a gentle lesson, and the children drinking lemon seltzer at snack time. The bright ending proves that the room felt peaceful again after the honest choice."
        )
    )
    return out


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"penny", "honesty", "seltzer"}
    tags |= set(f["need"].tags)
    tags |= set(f["choice"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid setting/need pairs
need_fits(P, N) :- place(P), need(N), place_tag(P, T), need_tag(N, T).

% only sensible choices are storyworthy
sensible(C) :- choice(C), sense(C, S), sense_min(M), S >= M.

valid(P, N, C) :- need_fits(P, N), sensible(C).

outcome(C, direct_return) :- chosen_choice(C), C = ask_teacher.
outcome(C, confession)    :- chosen_choice(C), C = keep_then_confess.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", place_id, tag))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        for tag in sorted(need.place_tags):
            lines.append(asp.fact("need_tag", need_id, tag))
    for choice_id, choice in CHOICES.items():
        lines.append(asp.fact("choice", choice_id))
        lines.append(asp.fact("sense", choice_id, choice.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    if params.choice == "ask_teacher":
        return "direct_return"
    if params.choice == "keep_then_confess":
        return "confession"
    raise StoryError(explain_choice(params.choice))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_choice", params.choice)
    model = asp.one_model(asp_program(extra, "#show outcome/2."))
    atoms = asp.atoms(model, "outcome")
    if not atoms:
        return "?"
    return atoms[0][1]


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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_out != asp_out:
                bad += 1
        except StoryError:
            continue
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A kindergarten folk-tale storyworld about finding a penny and choosing honesty."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--need", choices=sorted(NEEDS))
    ap.add_argument("--choice", choices=sorted(CHOICES))
    ap.add_argument("--finder-name")
    ap.add_argument("--finder-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_finder(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    picked_gender = gender or rng.choice(["girl", "boy"])
    if name:
        return name, picked_gender
    pool = GIRL_NAMES if picked_gender == "girl" else BOY_NAMES
    return rng.choice(pool), picked_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.choice and CHOICES[args.choice].sense < SENSE_MIN:
        raise StoryError(explain_choice(args.choice))
    if args.place and args.need:
        if not need_fits(PLACES[args.place], NEEDS[args.need]):
            raise StoryError(explain_rejection(PLACES[args.place], NEEDS[args.need]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.need is None or combo[1] == args.need)
        and (args.choice is None or combo[2] == args.choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, need, choice = rng.choice(sorted(combos))
    finder_name, finder_gender = _pick_finder(rng, args.finder_gender, args.finder_name)
    teacher_gender = args.teacher_gender or rng.choice(["teacher_f", "teacher_m"])
    finder_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        need=need,
        choice=choice,
        finder_name=finder_name,
        finder_gender=finder_gender,
        teacher_gender=teacher_gender,
        finder_trait=finder_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.need not in NEEDS:
        raise StoryError(f"(Invalid need: {params.need})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Invalid choice: {params.choice})")
    if CHOICES[params.choice].sense < SENSE_MIN:
        raise StoryError(explain_choice(params.choice))
    if not need_fits(PLACES[params.place], NEEDS[params.need]):
        raise StoryError(explain_rejection(PLACES[params.place], NEEDS[params.need]))

    world = tell(
        PLACES[params.place],
        NEEDS[params.need],
        CHOICES[params.choice],
        finder_name=params.finder_name,
        finder_gender=params.finder_gender,
        finder_trait=params.finder_trait,
        teacher_gender=params.teacher_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, need, choice) combos:\n")
        for place, need, choice in combos:
            print(f"  {place:12} {need:10} {choice}")
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
            header = f"### {p.finder_name}: {p.choice} at {p.place} ({p.need})"
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
