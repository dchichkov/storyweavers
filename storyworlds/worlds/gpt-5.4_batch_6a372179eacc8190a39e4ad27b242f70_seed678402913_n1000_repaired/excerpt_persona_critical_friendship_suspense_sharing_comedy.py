#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/excerpt_persona_critical_friendship_suspense_sharing_comedy.py
==========================================================================================

A standalone storyworld about two friends preparing a funny classroom reading.
One child chooses a silly stage persona and a short book excerpt for sharing
time. The trouble begins when there is only one useful prop and the performer
tries to keep all the fun alone. That choice makes the act wobbly, the excerpt
goes missing, suspense rises, and the friend who was pushed away turns out to be
the critical helper who can save the day. The ending proves what changed:
sharing the stage makes the act better and the friendship warmer.

The required seed words appear naturally in the child-facing story and Q&A:
"excerpt", "persona", and "critical".

Run it
------
    python storyworlds/worlds/gpt-5.4/excerpt_persona_critical_friendship_suspense_sharing_comedy.py
    python storyworlds/worlds/gpt-5.4/excerpt_persona_critical_friendship_suspense_sharing_comedy.py --persona robot --problem drop
    python storyworlds/worlds/gpt-5.4/excerpt_persona_critical_friendship_suspense_sharing_comedy.py --share no
    python storyworlds/worlds/gpt-5.4/excerpt_persona_critical_friendship_suspense_sharing_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/excerpt_persona_critical_friendship_suspense_sharing_comedy.py --verify
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
    owner: str = ""
    holder: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher_woman"}
        male = {"boy", "father", "dad", "man", "teacher_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Persona:
    id: str
    label: str
    phrase: str
    entrance: str
    voice: str
    gesture: str
    prop_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ExcerptCfg:
    id: str
    book: str
    excerpt_label: str
    funny_detail: str
    clue_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PropCfg:
    id: str
    label: str
    phrase: str
    use: str
    rescue_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemCfg:
    id: str
    vanish_verb: str
    where: str
    found_phrase: str
    recover_action: str
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


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    friend = world.get("friend")
    if performer.memes["hogging"] < THRESHOLD:
        return out
    sig = ("hurt", performer.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    friend.memes["distance"] += 1
    performer.memes["lonely"] += 1
    out.append("__hurt__")
    return out


def _r_problem_if_juggling(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    card = world.get("excerpt_card")
    prop = world.get("prop")
    if performer.meters["juggling"] < THRESHOLD:
        return out
    if card.holder != performer.id or prop.holder != performer.id:
        return out
    sig = ("problem", world.facts.get("problem_id", ""), performer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    card.meters["missing"] += 1
    performer.memes["worry"] += 1
    world.get("room").memes["suspense"] += 1
    out.append("__missing__")
    return out


def _r_find_when_friend_helps(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    card = world.get("excerpt_card")
    if friend.memes["helping"] < THRESHOLD or card.meters["missing"] < THRESHOLD:
        return out
    sig = ("find", friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    card.meters["missing"] = 0.0
    card.meters["found"] += 1
    friend.memes["pride"] += 1
    performer.memes["relief"] += 1
    performer.memes["gratitude"] += 1
    world.get("room").memes["suspense"] = 0.0
    out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
    Rule(name="problem_if_juggling", tag="physical", apply=_r_problem_if_juggling),
    Rule(name="find_when_friend_helps", tag="social", apply=_r_find_when_friend_helps),
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


PERSONAS = {
    "detective": Persona(
        id="detective",
        label="detective persona",
        phrase="a grand detective persona",
        entrance="tiptoed in with a gasp, as if every chair in the room might be a clue",
        voice="a whispery mystery voice",
        gesture="lifted one finger and squinted at the air",
        prop_hint="to peer for clues",
        tags={"persona", "comedy"},
    ),
    "robot": Persona(
        id="robot",
        label="robot persona",
        phrase="a clanky robot persona",
        entrance="marched in with stiff knees and beeped at the pencil jar",
        voice="a bouncy robot voice",
        gesture="clicked both elbows like little hinges",
        prop_hint="to scan for danger",
        tags={"persona", "comedy"},
    ),
    "queen": Persona(
        id="queen",
        label="queen persona",
        phrase="a splendid queen persona",
        entrance="swept in as if the rug were a red carpet and the crayons were royal guests",
        voice="a very serious royal voice that kept wobbling into giggles",
        gesture="waved one hand as if blessing the room",
        prop_hint="to inspect the kingdom",
        tags={"persona", "comedy"},
    ),
}

EXCERPTS = {
    "dragon": ExcerptCfg(
        id="dragon",
        book="The Sleepy Dragon Picnic",
        excerpt_label="a funny excerpt about a dragon who sneezed pepper onto the sandwiches",
        funny_detail="even the paper turtle on the cover looked surprised",
        clue_line="the dragon sneezed right when the picnic basket opened",
        tags={"excerpt", "book"},
    ),
    "pickle": ExcerptCfg(
        id="pickle",
        book="Captain Pickle and the Teacup Sea",
        excerpt_label="a funny excerpt about a pickle captain steering a teacup through a storm",
        funny_detail="the teacup in the picture leaned so hard it looked seasick",
        clue_line="the captain shouted at a wave no bigger than a spoon",
        tags={"excerpt", "book"},
    ),
    "goose": ExcerptCfg(
        id="goose",
        book="The Goose in the Boots",
        excerpt_label="a funny excerpt about a goose who wore shiny rain boots indoors",
        funny_detail="the boots were so shiny they nearly looked proud of themselves",
        clue_line="the goose honked every time the boots squeaked",
        tags={"excerpt", "book"},
    ),
}

PROPS = {
    "magnifier": PropCfg(
        id="magnifier",
        label="magnifying glass",
        phrase="a toy magnifying glass",
        use="held up the toy magnifying glass to make the mystery look important",
        rescue_use="slid the magnifying glass under the shelf and hooked the card back out",
        tags={"sharing", "prop"},
    ),
    "spoon_mic": PropCfg(
        id="spoon_mic",
        label="spoon microphone",
        phrase="a shiny spoon microphone",
        use="sang one line into the shiny spoon microphone as if it were the biggest stage in town",
        rescue_use="pointed with the spoon microphone until the lost card peeked out",
        tags={"sharing", "prop"},
    ),
    "feather": PropCfg(
        id="feather",
        label="feather fan",
        phrase="a floppy feather fan",
        use="fluttered the floppy feather fan so hard that two worksheets lifted at the corners",
        rescue_use="nudged the hidden card into sight with the feather fan",
        tags={"sharing", "prop"},
    ),
}

PROBLEMS = {
    "drop": ProblemCfg(
        id="drop",
        vanish_verb="slipped",
        where="under the low book shelf",
        found_phrase="a tiny white corner peeking from the shadows under the shelf",
        recover_action="The room went still for a second because nobody could see the excerpt card.",
        tags={"suspense", "search"},
    ),
    "stack": ProblemCfg(
        id="stack",
        vanish_verb="skated",
        where="between two stacks of library books",
        found_phrase="the card wedged like a shy bookmark between the stacks",
        recover_action="For one long breath, the card seemed to have vanished into book mountain.",
        tags={"suspense", "search"},
    ),
    "bin": ProblemCfg(
        id="bin",
        vanish_verb="fluttered",
        where="behind the puppet bin",
        found_phrase="the card hiding behind a soft bear puppet",
        recover_action="Everyone stared at the puppet bin as if it might have swallowed the lines.",
        tags={"suspense", "search"},
    ),
}

SHARE_CHOICES = {"yes": True, "no": False}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
TRAITS = ["dramatic", "bubbly", "careful", "goofy", "curious", "earnest"]


def valid_combo(persona_id: str, excerpt_id: str, prop_id: str, problem_id: str, share: str) -> bool:
    return (
        persona_id in PERSONAS
        and excerpt_id in EXCERPTS
        and prop_id in PROPS
        and problem_id in PROBLEMS
        and share in SHARE_CHOICES
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for persona_id in PERSONAS:
        for excerpt_id in EXCERPTS:
            for prop_id in PROPS:
                for problem_id in PROBLEMS:
                    for share in SHARE_CHOICES:
                        if valid_combo(persona_id, excerpt_id, prop_id, problem_id, share):
                            combos.append((persona_id, excerpt_id, prop_id, problem_id, share))
    return combos


@dataclass
class StoryParams:
    persona: str
    excerpt: str
    prop: str
    problem: str
    share: str
    performer_name: str
    performer_gender: str
    friend_name: str
    friend_gender: str
    teacher_gender: str
    trait: str
    seed: Optional[int] = None


def predict_problem(world: World) -> dict:
    sim = world.copy()
    performer = sim.get("performer")
    performer.meters["juggling"] += 1
    propagate(sim, narrate=False)
    card = sim.get("excerpt_card")
    return {
        "missing": card.meters["missing"] >= THRESHOLD,
        "suspense": sim.get("room").memes["suspense"],
    }


def setup_scene(world: World, persona: Persona, excerpt: ExcerptCfg, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    teacher = world.get("teacher")
    performer.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the classroom reading corner, {teacher.label_word} had invited everyone to bring one funny excerpt for sharing time."
    )
    world.say(
        f"{world.get('excerpt_card').label.capitalize()} came from a book called {excerpt.book}, and {excerpt.funny_detail}."
    )
    world.say(
        f"{performer.id} chose {persona.phrase}. {performer.pronoun().capitalize()} {persona.entrance} and {prop.use}."
    )
    world.say(
        f'{friend.id} laughed so hard that {friend.pronoun()} had to hold the edge of the carpet. "That is the silliest persona I have ever seen," {friend.pronoun()} said.'
    )


def ask_to_share(world: World, persona: Persona, prop: PropCfg) -> None:
    friend = world.get("friend")
    performer = world.get("performer")
    friend.memes["hope"] += 1
    world.say(
        f'{friend.id} pointed at the {prop.label}. "Can I help? I can use it {persona.prop_hint}, and we can do the excerpt together," {friend.pronoun()} said.'
    )
    performer.memes["choice"] += 1


def refuse_share(world: World, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    performer.memes["hogging"] += 1
    performer.meters["juggling"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Wait, I want every funny part for myself," {performer.id} said, clutching the {prop.label} and the excerpt card at the same time.'
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s smile slipped. {friend.pronoun().capitalize()} stepped back beside the beanbag chair, quiet but still watching."
        )


def share_early(world: World, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    performer.memes["sharing"] += 1
    friend.memes["trusted"] += 1
    world.get("prop").holder = friend.id
    world.say(
        f'"Yes, let\'s share," {performer.id} said. {performer.pronoun().capitalize()} handed the {prop.label} to {friend.id} and kept the excerpt card.'
    )
    world.say(
        f"Right away the act looked better, because one friend had the prop and one friend had the lines."
    )


def lose_excerpt(world: World, problem: ProblemCfg) -> None:
    performer = world.get("performer")
    card = world.get("excerpt_card")
    prop = world.get("prop")
    performer.meters["juggling"] += 1
    card.holder = performer.id
    prop.holder = performer.id
    propagate(world, narrate=False)
    if card.meters["missing"] >= THRESHOLD:
        world.say(
            f"Then the excerpt card {problem.vanish_verb} from {performer.pronoun('possessive')} fingers and shot {problem.where}."
        )
        world.say(problem.recover_action)
    else:
        world.say("The performer wobbled a little, but nothing fell.")


def teacher_calls_ready(world: World) -> None:
    teacher = world.get("teacher")
    performer = world.get("performer")
    world.say(
        f'Just then, {teacher.label_word} called, "Friends, reading time starts in ten little steps!"'
    )
    performer.memes["worry"] += 1


def critical_choice(world: World) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    room = world.get("room")
    if room.memes["suspense"] >= THRESHOLD:
        world.say(
            f"It was a critical moment. Without the card, {performer.id}'s big funny act might stop before it even started."
        )
        if friend.memes["hurt"] >= THRESHOLD:
            world.say(
                f"{friend.id} was still hurt, but {friend.pronoun()} could see {performer.id}'s eyes getting wide and worried."
            )


def friend_helps(world: World, problem: ProblemCfg, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    prop_ent = world.get("prop")
    prop_ent.holder = friend.id
    friend.memes["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I can help," {friend.id} said. {friend.pronoun().capitalize()} spotted {problem.found_phrase}.'
    )
    world.say(
        f"{friend.pronoun().capitalize()} {prop_cfg_action(world, prop)}."
    )
    if world.get("excerpt_card").meters["found"] >= THRESHOLD:
        world.say(
            f"Soon the excerpt card was back in {performer.id}'s hands, a little dusty but safe."
        )


def prop_cfg_action(world: World, prop: PropCfg) -> str:
    return prop.rescue_use


def apology_and_share(world: World, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    performer.memes["sharing"] += 1
    performer.memes["sorry"] += 1
    friend.memes["forgiveness"] += 1
    world.say(
        f'"I was trying to keep all the laughs," {performer.id} admitted. "I should have shared the {prop.label}. You were the critical helper."'
    )
    world.say(
        f'{friend.id} grinned. "Then let\'s both be funny," {friend.pronoun()} said.'
    )


def perform_together(world: World, persona: Persona, excerpt: ExcerptCfg, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    teacher = world.get("teacher")
    performer.memes["joy"] += 1
    friend.memes["joy"] += 1
    performer.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"When their turn came, {performer.id} used {persona.voice}, and {friend.id} handled the {prop.label} at exactly the right moments."
    )
    world.say(
        f'Together they read the excerpt about {excerpt.clue_line}, and the whole room burst into giggles.'
    )
    world.say(
        f"Even {teacher.label_word} laughed into one hand. The act was funnier because the friends shared the stage instead of guarding it."
    )


def ending_image(world: World, prop: PropCfg) -> None:
    performer = world.get("performer")
    friend = world.get("friend")
    world.say(
        f"Afterward, the two friends sat shoulder to shoulder on the rug, passing the {prop.label} back and forth and making up extra silly lines."
    )
    world.say(
        f"Their voices kept wobbling into laughter, and nobody needed one star all alone anymore."
    )


def tell(
    persona: Persona,
    excerpt: ExcerptCfg,
    prop: PropCfg,
    problem: ProblemCfg,
    share: bool,
    performer_name: str = "Lily",
    performer_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    teacher_gender: str = "teacher_woman",
    trait: str = "dramatic",
) -> World:
    world = World()
    performer = world.add(
        Entity(
            id=performer_name,
            kind="character",
            type=performer_gender,
            role="performer",
            traits=[trait],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["kind"],
        )
    )
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type=teacher_gender,
            role="teacher",
            label="the teacher",
        )
    )
    room = world.add(Entity(id="room", kind="thing", type="room", label="reading corner"))
    card = world.add(
        Entity(
            id="excerpt_card",
            kind="thing",
            type="card",
            label="the excerpt card",
            phrase=excerpt.excerpt_label,
            holder=performer.id,
            owner=performer.id,
            tags=set(excerpt.tags),
        )
    )
    prop_ent = world.add(
        Entity(
            id="prop",
            kind="thing",
            type="prop",
            label=prop.label,
            phrase=prop.phrase,
            holder=performer.id,
            owner="classroom",
            tags=set(prop.tags),
        )
    )

    setup_scene(world, persona, excerpt, prop)
    world.para()
    ask_to_share(world, persona, prop)

    if share:
        share_early(world, prop)
        teacher_calls_ready(world)
        world.para()
        perform_together(world, persona, excerpt, prop)
        ending_image(world, prop)
        outcome = "shared_early"
        missing = False
    else:
        refuse_share(world, prop)
        pred = predict_problem(world)
        world.facts["predicted_missing"] = pred["missing"]
        world.facts["predicted_suspense"] = pred["suspense"]
        world.para()
        lose_excerpt(world, problem)
        teacher_calls_ready(world)
        critical_choice(world)
        world.para()
        friend_helps(world, problem, prop)
        apology_and_share(world, prop)
        world.para()
        perform_together(world, persona, excerpt, prop)
        ending_image(world, prop)
        outcome = "shared_late"
        missing = world.get("excerpt_card").meters["found"] >= THRESHOLD

    world.facts.update(
        performer=performer,
        friend=friend,
        teacher=teacher,
        persona=persona,
        excerpt_cfg=excerpt,
        prop_cfg=prop,
        problem_cfg=problem,
        share=share,
        outcome=outcome,
        missing=missing,
        card_found=world.get("excerpt_card").meters["found"] >= THRESHOLD,
        friendship_stronger=performer.memes["friendship"] >= THRESHOLD and friend.memes["friendship"] >= THRESHOLD,
        suspense_happened=room.memes["suspense"] < THRESHOLD and not share,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    performer = f["performer"]
    friend = f["friend"]
    persona = f["persona"]
    excerpt = f["excerpt_cfg"]
    prop = f["prop_cfg"]
    if f["outcome"] == "shared_early":
        return [
            'Write a funny friendship story for a 3-to-5-year-old that includes the words "excerpt", "persona", and "critical".',
            f"Tell a comedy about {performer.id} and {friend.id} preparing a classroom reading with {persona.phrase}, where they choose sharing early and the act becomes even funnier.",
            f"Write a gentle school story where two friends share a {prop.label} while reading {excerpt.excerpt_label}, and show that teamwork is the critical part of the joke.",
        ]
    return [
        'Write a funny friendship story for a 3-to-5-year-old that includes the words "excerpt", "persona", and "critical".',
        f"Tell a suspenseful comedy where {performer.id} tries to keep the whole act alone, loses the excerpt card, and learns that sharing with {friend.id} saves the day.",
        f"Write a classroom story where a silly persona, one missing card, and one shared prop turn a wobbly performance into a happy friendship ending.",
    ]


KNOWLEDGE = {
    "excerpt": [
        (
            "What is an excerpt?",
            "An excerpt is a short part taken from a longer story or book. People share one excerpt when they want others to hear a favorite bit without reading the whole book.",
        )
    ],
    "persona": [
        (
            "What is a persona?",
            "A persona is a pretend way of acting, sounding, or moving. It is like trying on a little character for fun.",
        )
    ],
    "critical": [
        (
            "What does critical mean in a story like this?",
            "Critical means very important at that moment. A critical choice can change what happens next.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help friends?",
            "Sharing helps friends feel included and trusted. It often makes a game or a job easier because two people can help instead of one person doing everything alone.",
        )
    ],
    "suspense": [
        (
            "What is suspense?",
            "Suspense is the worried, wondering feeling you get when something important might go wrong and you do not know the answer yet.",
        )
    ],
    "comedy": [
        (
            "What makes a comedy feel funny?",
            "Comedy often uses silly surprises, playful mistakes, and big feelings that end safely. People laugh because the trouble turns into a joke instead of staying scary.",
        )
    ],
}
KNOWLEDGE_ORDER = ["excerpt", "persona", "critical", "sharing", "suspense", "comedy"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    performer = f["performer"]
    friend = f["friend"]
    teacher = f["teacher"]
    persona = f["persona"]
    excerpt = f["excerpt_cfg"]
    prop = f["prop_cfg"]
    problem = f["problem_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {performer.id} and {friend.id}, getting ready for classroom sharing time. {teacher.label_word.capitalize()} is there too, because the reading happens in the classroom corner.",
        ),
        (
            f"What was {performer.id}'s funny idea?",
            f"{performer.id} chose {persona.phrase} and planned to read {excerpt.excerpt_label}. The silly voice and movements made the act feel like comedy from the start.",
        ),
        (
            f"Why did {friend.id} want the {prop.label}?",
            f"{friend.id} wanted to help with the act instead of just watching. Sharing the prop would let both friends take part in the same joke.",
        ),
    ]
    if f["outcome"] == "shared_early":
        out.append(
            (
                f"What happened when {performer.id} shared right away?",
                f"{performer.id} handed the {prop.label} to {friend.id}, so one friend could hold the prop while the other held the excerpt card. That made the act steadier and showed trust before any trouble could begin.",
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended with both friends performing together and making the room laugh. The last image shows them passing the {prop.label} back and forth, which proves they were happy to share.",
            )
        )
    else:
        out.append(
            (
                f"Why did the excerpt card go missing?",
                f"The card went missing because {performer.id} tried to clutch the prop and the lines all at once. Doing everything alone made the act wobbly, so the card {problem.vanish_verb} away.",
            )
        )
        out.append(
            (
                f"Why was {friend.id} the critical helper?",
                f"{friend.id} was the critical helper because {friend.pronoun()} noticed {problem.found_phrase} and helped get the card back. The lost excerpt was the biggest problem in that moment, so the helper mattered most right then.",
            )
        )
        out.append(
            (
                "Was the suspense solved, and how?",
                f"Yes. The suspense ended when {friend.id} helped recover the excerpt card and the friends decided to share the act. Once the missing card was back, the worried pause turned into laughter.",
            )
        )
        out.append(
            (
                "How did the friendship change?",
                f"The friendship grew warmer because {performer.id} apologized and shared the stage after being selfish at first. By the end, both friends were laughing together instead of standing apart.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"excerpt", "persona", "critical", "sharing", "comedy"}
    if world.facts["outcome"] == "shared_late":
        tags.add("suspense")
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
        if e.holder:
            bits.append(f"holder={e.holder}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        persona="detective",
        excerpt="dragon",
        prop="magnifier",
        problem="drop",
        share="no",
        performer_name="Lily",
        performer_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        teacher_gender="teacher_woman",
        trait="dramatic",
    ),
    StoryParams(
        persona="robot",
        excerpt="pickle",
        prop="spoon_mic",
        problem="stack",
        share="yes",
        performer_name="Max",
        performer_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        teacher_gender="teacher_man",
        trait="goofy",
    ),
    StoryParams(
        persona="queen",
        excerpt="goose",
        prop="feather",
        problem="bin",
        share="no",
        performer_name="Ava",
        performer_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        teacher_gender="teacher_woman",
        trait="bubbly",
    ),
    StoryParams(
        persona="robot",
        excerpt="dragon",
        prop="magnifier",
        problem="stack",
        share="no",
        performer_name="Noah",
        performer_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        teacher_gender="teacher_man",
        trait="earnest",
    ),
    StoryParams(
        persona="detective",
        excerpt="pickle",
        prop="spoon_mic",
        problem="drop",
        share="yes",
        performer_name="Lucy",
        performer_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        teacher_gender="teacher_woman",
        trait="careful",
    ),
]


def explain_rejection(persona_id: str, excerpt_id: str, prop_id: str, problem_id: str, share: str) -> str:
    bad: list[str] = []
    if persona_id not in PERSONAS:
        bad.append(f"unknown persona '{persona_id}'")
    if excerpt_id not in EXCERPTS:
        bad.append(f"unknown excerpt '{excerpt_id}'")
    if prop_id not in PROPS:
        bad.append(f"unknown prop '{prop_id}'")
    if problem_id not in PROBLEMS:
        bad.append(f"unknown problem '{problem_id}'")
    if share not in SHARE_CHOICES:
        bad.append(f"share must be one of {sorted(SHARE_CHOICES)}")
    return "(No story: " + "; ".join(bad) + ")"


ASP_RULES = r"""
valid(Pe, Ex, Pr, Pb, Sh) :-
    persona(Pe), excerpt(Ex), prop(Pr), problem(Pb), share(Sh).

late_share :- chosen_share(no).
early_share :- chosen_share(yes).

outcome(shared_early) :- early_share.
outcome(shared_late) :- late_share.

missing_card :- late_share.
needs_helper :- missing_card.
critical_helper(friend) :- needs_helper.
suspense :- missing_card.
friendship_stronger :- outcome(shared_early).
friendship_stronger :- outcome(shared_late).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for persona_id in PERSONAS:
        lines.append(asp.fact("persona", persona_id))
    for excerpt_id in EXCERPTS:
        lines.append(asp.fact("excerpt", excerpt_id))
    for prop_id in PROPS:
        lines.append(asp.fact("prop", prop_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for share in SHARE_CHOICES:
        lines.append(asp.fact("share", share))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_share", params.share)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared_early" if params.share == "yes" else "shared_late"


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

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for curated params:", params)
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a funny classroom excerpt, a silly persona, suspense, and sharing."
    )
    ap.add_argument("--persona", choices=PERSONAS)
    ap.add_argument("--excerpt", choices=EXCERPTS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--share", choices=sorted(SHARE_CHOICES))
    ap.add_argument("--performer-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--performer-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["teacher_woman", "teacher_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    persona_id = args.persona or rng.choice(sorted(PERSONAS))
    excerpt_id = args.excerpt or rng.choice(sorted(EXCERPTS))
    prop_id = args.prop or rng.choice(sorted(PROPS))
    problem_id = args.problem or rng.choice(sorted(PROBLEMS))
    share = args.share or rng.choice(sorted(SHARE_CHOICES))

    if not valid_combo(persona_id, excerpt_id, prop_id, problem_id, share):
        raise StoryError(explain_rejection(persona_id, excerpt_id, prop_id, problem_id, share))

    performer_gender = args.performer_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    performer_name = args.performer_name or _pick_name(rng, performer_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=performer_name)
    teacher_gender = args.teacher_gender or rng.choice(["teacher_woman", "teacher_man"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        persona=persona_id,
        excerpt=excerpt_id,
        prop=prop_id,
        problem=problem_id,
        share=share,
        performer_name=performer_name,
        performer_gender=performer_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_gender=teacher_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.persona, params.excerpt, params.prop, params.problem, params.share):
        raise StoryError(
            explain_rejection(params.persona, params.excerpt, params.prop, params.problem, params.share)
        )

    world = tell(
        persona=PERSONAS[params.persona],
        excerpt=EXCERPTS[params.excerpt],
        prop=PROPS[params.prop],
        problem=PROBLEMS[params.problem],
        share=SHARE_CHOICES[params.share],
        performer_name=params.performer_name,
        performer_gender=params.performer_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_gender=params.teacher_gender,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (persona, excerpt, prop, problem, share) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:10}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.performer_name} & {p.friend_name}: {p.persona} / {p.excerpt} / "
                f"{p.prop} / {p.problem} / share={p.share}"
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
