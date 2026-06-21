#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/feel_gerund_dentist_tension_humor_twist_rhyming.py
=============================================================================

A standalone storyworld about a child's nervous trip to the dentist, rebuilt as
a tiny classical simulation with typed entities, stateful tension, a humor beat,
a twist, and rhyming prose.

The seed asked for:
- words: "feel-gerund", "dentist", "tension"
- features: Humor, Twist
- style: Rhyming Story

This world treats the visit as a small, reasoned domain:
- a tooth problem creates the need for a visit,
- a specific fear creates tension,
- the dentist chooses a fitting calming move,
- the feared thing turns out to be something silly or helpful,
- the child ends in either a calm grin or a brave little sniffle.

Run it
------
    python storyworlds/worlds/gpt-5.4/feel_gerund_dentist_tension_humor_twist_rhyming.py
    python storyworlds/worlds/gpt-5.4/feel_gerund_dentist_tension_humor_twist_rhyming.py --issue wiggly --fear shiny_hook --comfort mirror_peek
    python storyworlds/worlds/gpt-5.4/feel_gerund_dentist_tension_humor_twist_rhyming.py --issue jam --fear buzzy_brush
    python storyworlds/worlds/gpt-5.4/feel_gerund_dentist_tension_humor_twist_rhyming.py --all --qa
    python storyworlds/worlds/gpt-5.4/feel_gerund_dentist_tension_humor_twist_rhyming.py --verify
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
        female = {"girl", "mother", "mom", "woman", "dentist_woman"}
        male = {"boy", "father", "dad", "man", "dentist_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Issue:
    id: str
    label: str = ""
    line: str = ""
    procedure: str = ""
    tension: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Fear:
    id: str
    label: str = ""
    phrase: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str = ""
    phrase: str = ""
    soothe_fear: str = ""
    power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Humor:
    id: str
    line: str = ""
    payoff: str = ""
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


def _r_tension_shows(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["tension"] < THRESHOLD:
        return []
    sig = ("tension_shows", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return ["__tension__"]


def _r_comfort_works(world: World) -> list[str]:
    child = world.get("child")
    comfort = world.get("comfort")
    if comfort.meters["used"] < THRESHOLD:
        return []
    sig = ("comfort_works", comfort.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tension"] = max(0.0, child.meters["tension"] - comfort.attrs.get("power", 0))
    child.memes["trust"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["tension"] >= THRESHOLD:
        return []
    sig = ("relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tension_shows", tag="emotion", apply=_r_tension_shows),
    Rule(name="comfort_works", tag="emotion", apply=_r_comfort_works),
    Rule(name="relief", tag="emotion", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ISSUES = {
    "wiggly": Issue(
        id="wiggly",
        label="a wiggly tooth",
        line="A tiny tooth kept wobbling with every nibble and grin.",
        procedure="gentle_pull",
        tension=3,
        tags={"tooth", "dentist", "wiggly_tooth"},
    ),
    "jam": Issue(
        id="jam",
        label="an apple-skin bit stuck by a tooth",
        line="A stubborn bit of apple skin was tucked where the toothbrush could not win.",
        procedure="rinse_and_slurp",
        tension=1,
        tags={"tooth", "dentist", "rinse"},
    ),
    "plaque": Issue(
        id="plaque",
        label="sugary fuzz on a tooth",
        line="A sleepy sugar spot had settled on a tooth and made it feel less smooth than new.",
        procedure="brush_and_polish",
        tension=2,
        tags={"tooth", "dentist", "cleaning"},
    ),
}

FEARS = {
    "shiny_hook": Fear(
        id="shiny_hook",
        label="the shiny hook",
        phrase="a hook that looked like a silver crook",
        reveal="it was only a tiny helper for a gentle look",
        tags={"tools", "dentist"},
    ),
    "buzzy_brush": Fear(
        id="buzzy_brush",
        label="the buzzy brush",
        phrase="a buzzy brush that sounded like a bee in a bush",
        reveal="it was only a tickly brush that whirred to make the tooth clean",
        tags={"tools", "buzz"},
    ),
    "slurpy_tube": Fear(
        id="slurpy_tube",
        label="the slurpy tube",
        phrase="a tube that seemed to slurp like a pond in a storm",
        reveal="it was only a thirsty straw that sipped water where it did not belong",
        tags={"tools", "slurp"},
    ),
    "tall_chair": Fear(
        id="tall_chair",
        label="the tall chair",
        phrase="a tall chair that rose with a hum and a sigh",
        reveal="it was only a gentle lift so the dentist could see up high",
        tags={"chair", "dentist"},
    ),
}

COMFORTS = {
    "mirror_peek": Comfort(
        id="mirror_peek",
        label="a hand mirror peek",
        phrase="holding up a little mirror so the child could peek",
        soothe_fear="shiny_hook",
        power=1,
        tags={"mirror", "dentist"},
    ),
    "counting_rhyme": Comfort(
        id="counting_rhyme",
        label="a counting rhyme",
        phrase="counting in rhyme from one to ten, then back again",
        soothe_fear="tall_chair",
        power=2,
        tags={"counting", "rhyme"},
    ),
    "thirsty_fish_game": Comfort(
        id="thirsty_fish_game",
        label="the thirsty fish game",
        phrase="pretending the little tube was a thirsty fish asking for a sip",
        soothe_fear="slurpy_tube",
        power=2,
        tags={"game", "slurp"},
    ),
    "balloon_breath": Comfort(
        id="balloon_breath",
        label="balloon breathing",
        phrase="taking slow balloon breaths, puffing cheeks and letting the air float out",
        soothe_fear="buzzy_brush",
        power=3,
        tags={"breathing", "calm"},
    ),
}

HUMORS = {
    "banana_gloves": Humor(
        id="banana_gloves",
        line="The dentist wore yellow gloves and whispered, \"Banana hands, ready to help where little teeth stand.\"",
        payoff="Even the gloves looked too silly for gloom to keep growing.",
        tags={"humor", "banana"},
    ),
    "walrus_sticker": Humor(
        id="walrus_sticker",
        line="A walrus sticker sat on the lamp with paper whiskers long and grand.",
        payoff="The child snorted a laugh, because the walrus seemed to be in command.",
        tags={"humor", "sticker"},
    ),
    "squeaky_stool": Humor(
        id="squeaky_stool",
        line="When the dentist sat down, the stool gave a comic squeak like a toy mouse under a cheek.",
        payoff="That tiny squeak popped the room's stiffness like a bubble.",
        tags={"humor", "squeak"},
    ),
    "sock_joke": Humor(
        id="sock_joke",
        line="The dentist pointed at striped socks and said, \"These are my brave-tooth socks. They never walk away from a job.\"",
        payoff="The striped socks made the whole room feel less grand and more friendly.",
        tags={"humor", "socks"},
    ),
}

ISSUE_FEARS = {
    "wiggly": {"shiny_hook", "tall_chair"},
    "jam": {"slurpy_tube", "tall_chair"},
    "plaque": {"buzzy_brush", "tall_chair"},
}

PROCEDURE_LINES = {
    "gentle_pull": "One soft tug was all it took, quick as a blink and neat as a book.",
    "rinse_and_slurp": "A swish, a sip, a careful clean, and the stuck bit vanished from the scene.",
    "brush_and_polish": "The brush went whirr, then soft and bright, until the tooth felt smooth and right.",
}

KNOWLEDGE = {
    "dentist": [
        (
            "What does a dentist do?",
            "A dentist looks after teeth. Dentists check teeth, clean them, and help when something hurts or feels stuck.",
        )
    ],
    "wiggly_tooth": [
        (
            "Why do children get wiggly teeth?",
            "Children get wiggly teeth because their baby teeth loosen when their grown-up teeth are getting ready underneath.",
        )
    ],
    "rinse": [
        (
            "Why might a dentist rinse your mouth?",
            "A dentist might rinse your mouth to wash away bits of food or toothpaste. The water helps the dentist see and clean better.",
        )
    ],
    "cleaning": [
        (
            "Why do teeth need cleaning?",
            "Teeth need cleaning because sticky sugar and food can sit on them. Cleaning helps keep teeth smooth and healthy.",
        )
    ],
    "tools": [
        (
            "Why do dentist tools sometimes look strange?",
            "Dentist tools are made to help the dentist see and clean small places in your mouth. They can look strange at first, but they are helpers, not monsters.",
        )
    ],
    "buzz": [
        (
            "Why can a buzzy toothbrush sound loud?",
            "A little brush can sound loud when it is close to your ears and mouth. The sound feels bigger because your head is very near it.",
        )
    ],
    "slurp": [
        (
            "What does the slurpy tube at the dentist do?",
            "It gently sips up water and spit so your mouth does not get too full. Some children say it sounds like a tiny straw or fish.",
        )
    ],
    "chair": [
        (
            "Why does a dentist chair go up and down?",
            "The chair goes up and down so the dentist can see your teeth clearly without bending in a hard way. It helps the dentist work gently and safely.",
        )
    ],
    "mirror": [
        (
            "What is a dentist mirror for?",
            "A dentist mirror helps the dentist peek at the sides and backs of teeth. It can also help a child see what is happening.",
        )
    ],
    "counting": [
        (
            "Why can counting help when you feel nervous?",
            "Counting gives your mind a small job to do. That can make a worried moment feel shorter and steadier.",
        )
    ],
    "breathing": [
        (
            "How can slow breathing help with big feelings?",
            "Slow breathing can calm your body and make tight muscles soften. It gives your body a signal that you are safe enough to slow down.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "dentist",
    "wiggly_tooth",
    "rinse",
    "cleaning",
    "tools",
    "buzz",
    "slurp",
    "chair",
    "mirror",
    "counting",
    "breathing",
]


def issue_supports_fear(issue_id: str, fear_id: str) -> bool:
    return fear_id in ISSUE_FEARS.get(issue_id, set())


def comfort_matches_fear(comfort_id: str, fear_id: str) -> bool:
    comfort = COMFORTS[comfort_id]
    return comfort.soothe_fear == fear_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for issue_id in ISSUES:
        for fear_id in FEARS:
            if not issue_supports_fear(issue_id, fear_id):
                continue
            for comfort_id in COMFORTS:
                if comfort_matches_fear(comfort_id, fear_id):
                    combos.append((issue_id, fear_id, comfort_id))
    return combos


def outcome_for(issue_id: str, comfort_id: str) -> str:
    issue = ISSUES[issue_id]
    comfort = COMFORTS[comfort_id]
    return "calm" if comfort.power >= issue.tension else "sniffly"


def predict_visit(world: World, issue_id: str, comfort_id: str) -> dict:
    sim = world.copy()
    sim.get("child").meters["tension"] = float(ISSUES[issue_id].tension)
    sim.get("comfort").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "remaining_tension": sim.get("child").meters["tension"],
        "outcome": "calm" if sim.get("child").meters["tension"] < THRESHOLD else "sniffly",
    }


def child_opening(world: World, child: Entity, parent: Entity, issue: Issue) -> None:
    world.say(
        f"{child.id} skipped by the window in the morning light, "
        f"but {issue.line}"
    )
    world.say(
        f"So {child.id}'s {parent.label_word} zipped up a coat, held a hand tight, "
        f"and said they would visit the dentist before noon turned bright."
    )


def waiting_room(world: World, child: Entity) -> None:
    chart = "On the wall hung a feel-gerund chart: shaking, waiting, hoping, grinning."
    world.say(
        f"In the waiting room, fish on a poster seemed to swish and spin. {chart}"
    )
    world.say(
        f"{child.id} looked at the words and whispered that one small word fit best: tension."
    )


def enter_room(world: World, child: Entity, dentist: Entity, humor: Humor) -> None:
    world.say(
        f"Soon the dentist came with a smile so mild, and bent low to greet the child."
    )
    world.say(humor.line)


def fear_rises(world: World, child: Entity, fear: Fear) -> None:
    child.meters["tension"] = float(world.facts["issue"].tension)
    propagate(world, narrate=False)
    toes = "toes" if child.type in {"girl", "boy"} else "shoes"
    world.say(
        f"But then {child.id} saw {fear.phrase}, and a little tension curled clear down to {child.pronoun('possessive')} {toes}."
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.pronoun().capitalize()} held still in the chair and did more watching than chatting."
        )


def parent_names_feeling(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f'"It is all right to feel scared while sitting here," said {parent.label_word}. '
        f'"You can be shaking and waiting and still be brave, my dear."'
    )


def dentist_offers_comfort(world: World, child: Entity, dentist: Entity, comfort: Comfort, fear: Fear) -> None:
    world.say(
        f'The dentist noticed the still little chin and said, '
        f'"Shall we try {comfort.phrase}? It helps when {fear.label} looks bigger than it is."'
    )
    world.add(
        Entity(
            id="comfort",
            type="comfort",
            label=comfort.label,
            attrs={"power": comfort.power, "soothe_fear": comfort.soothe_fear},
            tags=set(comfort.tags),
        )
    )
    world.get("comfort").meters["used"] += 1
    pred = predict_visit(world, world.facts["issue"].id, comfort.id)
    world.facts["predicted_outcome"] = pred["outcome"]
    world.facts["predicted_remaining_tension"] = pred["remaining_tension"]
    propagate(world, narrate=False)


def twist_reveal(world: World, child: Entity, fear: Fear, humor: Humor) -> None:
    world.say(
        f"Then came the twist, not grim or shook: {fear.reveal}."
    )
    world.say(humor.payoff)


def procedure(world: World, child: Entity, issue: Issue) -> None:
    child.meters["procedure_done"] += 1
    line = PROCEDURE_LINES[issue.procedure]
    world.say(line)


def ending(world: World, child: Entity, dentist: Entity, issue: Issue) -> None:
    outcome = world.facts["outcome"]
    if outcome == "calm":
        child.memes["pride"] += 1
        world.say(
            f"When it was done, {child.id} gave a blink, then a grin so wide it seemed to clink."
        )
        world.say(
            f"The dentist handed over a bright star sticker, and {child.id} walked out lighter, calmer, and quicker."
        )
    else:
        child.memes["bravery"] += 1
        world.say(
            f"{child.id} let out one brave sniffle, then one long breath, and stayed still enough to finish with careful teeth."
        )
        world.say(
            f"Outside, the air felt cooler and thin, and {child.id} touched the sticker and said, \"I was shaky, but I still got through and can grin.\""
        )
    world.say(
        f"The tooth trouble was smaller than before, and the dentist door did not feel quite so giant anymore."
    )


def tell(
    issue: Issue,
    fear: Fear,
    comfort: Comfort,
    humor: Humor,
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "thoughtful",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            label=child_name,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    dentist_type = "dentist_woman" if parent_type == "father" else "dentist_man"
    dentist = world.add(
        Entity(
            id="Dentist",
            kind="character",
            type=dentist_type,
            role="dentist",
            label="the dentist",
        )
    )
    world.add(Entity(id="fear", type="fear", label=fear.label, tags=set(fear.tags)))
    world.facts.update(
        issue=issue,
        fear=fear,
        comfort_cfg=comfort,
        humor=humor,
        child=child,
        parent=parent,
        dentist=dentist,
    )

    child_opening(world, child, parent, issue)
    waiting_room(world, child)

    world.para()
    enter_room(world, child, dentist, humor)
    fear_rises(world, child, fear)
    parent_names_feeling(world, child, parent)

    world.para()
    dentist_offers_comfort(world, child, dentist, comfort, fear)
    twist_reveal(world, child, fear, humor)
    procedure(world, child, issue)

    outcome = "calm" if child.meters["tension"] < THRESHOLD else "sniffly"
    world.facts["outcome"] = outcome

    world.para()
    ending(world, child, dentist, issue)
    return world


@dataclass
class StoryParams:
    issue: str
    fear: str
    comfort: str
    humor: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella", "Zoe", "Rose", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Eli", "Noah"]
TRAITS = ["thoughtful", "bouncy", "careful", "curious", "gentle", "bright"]

CURATED = [
    StoryParams(
        issue="wiggly",
        fear="shiny_hook",
        comfort="mirror_peek",
        humor="banana_gloves",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        issue="jam",
        fear="slurpy_tube",
        comfort="thirsty_fish_game",
        humor="squeaky_stool",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        issue="plaque",
        fear="buzzy_brush",
        comfort="balloon_breath",
        humor="walrus_sticker",
        child_name="Ella",
        child_gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        issue="wiggly",
        fear="tall_chair",
        comfort="counting_rhyme",
        humor="sock_joke",
        child_name="Max",
        child_gender="boy",
        parent="father",
        trait="bouncy",
    ),
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    issue = world.facts["issue"]
    fear = world.facts["fear"]
    comfort = world.facts["comfort_cfg"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "feel-gerund", "dentist", and "tension".',
        f"Tell a rhyming story where {child.id} goes to the dentist because of {issue.label}, feels afraid of {fear.label}, and feels better through {comfort.label}.",
        "Write a gentle humorous dentist story with a twist where the scary-looking thing turns out to be helpful, and end with a changed feeling the child can name.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    issue = world.facts["issue"]
    fear = world.facts["fear"]
    comfort = world.facts["comfort_cfg"]
    humor = world.facts["humor"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who went to the dentist with {child.pronoun('possessive')} {parent.label_word}. The visit began because {issue.label} needed help.",
        ),
        (
            f"Why did {child.id} go to the dentist?",
            f"{child.id} went because of {issue.label}. That tooth trouble is what brought the family to the dentist that day.",
        ),
        (
            f"What made {child.id} feel tension in the room?",
            f"{child.id} felt tense after seeing {fear.label}. The worry came from thinking the strange-looking thing might be scary or hurtful.",
        ),
        (
            f"How did the dentist help when {child.id} felt nervous?",
            f"The dentist used {comfort.label}. That gave {child.id} a better way to look at the moment, so the tension could shrink instead of grow.",
        ),
        (
            "What was the twist?",
            f"The twist was that the thing that looked scary was not dangerous at all: {fear.reveal}. That surprise changed the whole feeling of the room.",
        ),
        (
            "What was funny in the story?",
            f"The humor came from {humor.line[0].lower() + humor.line[1:] if humor.line else 'a silly dentist moment'}. The joke helped loosen the room before the careful work began.",
        ),
    ]
    if outcome == "calm":
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt calm and proud by the end. After the twist and the helpful comfort, the dentist room no longer felt quite so huge.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} stop feeling scared all at once?",
                f"No. {child.id} still had a brave little sniffle, but stayed long enough to finish. The comfort helped even though some tension was still there.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    issue = world.facts["issue"]
    fear = world.facts["fear"]
    comfort = world.facts["comfort_cfg"]
    tags = set(issue.tags) | set(fear.tags) | set(comfort.tags) | {"dentist"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(issue_id: str, fear_id: str, comfort_id: str) -> str:
    if not issue_supports_fear(issue_id, fear_id):
        return (
            f"(No story: {FEARS[fear_id].label} is not a natural source of worry for "
            f"{ISSUES[issue_id].label} in this little world. Pick a fear that fits the visit.)"
        )
    if not comfort_matches_fear(comfort_id, fear_id):
        return (
            f"(No story: {COMFORTS[comfort_id].label} does not address fear of {FEARS[fear_id].label}. "
            f"The calming move should match the child's specific worry.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
supports(wiggly, shiny_hook).
supports(wiggly, tall_chair).
supports(jam, slurpy_tube).
supports(jam, tall_chair).
supports(plaque, buzzy_brush).
supports(plaque, tall_chair).

matches(mirror_peek, shiny_hook).
matches(counting_rhyme, tall_chair).
matches(thirsty_fish_game, slurpy_tube).
matches(balloon_breath, buzzy_brush).

valid(I, F, C) :- issue(I), fear(F), comfort(C), supports(I, F), matches(C, F).

outcome(calm) :- chosen_issue(I), chosen_comfort(C), issue_tension(I, T), comfort_power(C, P), P >= T.
outcome(sniffly) :- chosen_issue(I), chosen_comfort(C), issue_tension(I, T), comfort_power(C, P), P < T.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for issue_id, issue in ISSUES.items():
        lines.append(asp.fact("issue", issue_id))
        lines.append(asp.fact("issue_tension", issue_id, issue.tension))
    for fear_id in FEARS:
        lines.append(asp.fact("fear", fear_id))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("comfort_power", comfort_id, comfort.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_issue", params.issue),
            asp.fact("chosen_comfort", params.comfort),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story or "dentist" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story was empty or missing dentist.")
    if "feel-gerund" not in sample.story:
        raise StoryError("Smoke test failed: generated story was missing 'feel-gerund'.")
    if "tension" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story was missing 'tension'.")


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for params in cases:
        py = outcome_for(params.issue, params.comfort)
        asp_val = asp_outcome(params)
        if py != asp_val:
            rc = 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp_val}")

    try:
        smoke_test()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming dentist storyworld with humor, tension, and a twist."
    )
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--fear", choices=FEARS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--humor", choices=HUMORS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.issue and args.fear and not issue_supports_fear(args.issue, args.fear):
        comfort_id = args.comfort or next(iter(COMFORTS))
        raise StoryError(explain_rejection(args.issue, args.fear, comfort_id))
    if args.fear and args.comfort and not comfort_matches_fear(args.comfort, args.fear):
        issue_id = args.issue or next(iter(ISSUES))
        raise StoryError(explain_rejection(issue_id, args.fear, args.comfort))

    combos = [
        combo
        for combo in valid_combos()
        if (args.issue is None or combo[0] == args.issue)
        and (args.fear is None or combo[1] == args.fear)
        and (args.comfort is None or combo[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    issue_id, fear_id, comfort_id = rng.choice(sorted(combos))
    humor_id = args.humor or rng.choice(sorted(HUMORS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        issue=issue_id,
        fear=fear_id,
        comfort=comfort_id,
        humor=humor_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.issue not in ISSUES:
        raise StoryError(f"Unknown issue: {params.issue}")
    if params.fear not in FEARS:
        raise StoryError(f"Unknown fear: {params.fear}")
    if params.comfort not in COMFORTS:
        raise StoryError(f"Unknown comfort: {params.comfort}")
    if params.humor not in HUMORS:
        raise StoryError(f"Unknown humor: {params.humor}")
    if not issue_supports_fear(params.issue, params.fear):
        raise StoryError(explain_rejection(params.issue, params.fear, params.comfort))
    if not comfort_matches_fear(params.comfort, params.fear):
        raise StoryError(explain_rejection(params.issue, params.fear, params.comfort))

    world = tell(
        issue=ISSUES[params.issue],
        fear=FEARS[params.fear],
        comfort=COMFORTS[params.comfort],
        humor=HUMORS[params.humor],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (issue, fear, comfort) combos:\n")
        for issue_id, fear_id, comfort_id in combos:
            print(f"  {issue_id:8} {fear_id:12} {comfort_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.child_name}: {p.issue}, {p.fear}, {p.comfort} ({outcome_for(p.issue, p.comfort)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
