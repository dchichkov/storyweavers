#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py
=============================================================

A standalone story world for a small child-facing mystery: a child doing
research loses a notebook, follows a few clues, and discovers a kind twist.
The "mystery" is grounded in world state rather than a frozen template:

- a notebook is left in a risky place
- a nearby hazard threatens it
- a helper quietly moves it to a safer place
- the helper leaves a clue
- the child notices the notebook is gone, worries, and investigates
- the twist is that nobody stole it; someone protected it out of kindness

The reasonableness gate is simple and explicit: each setting supports only some
research topics, and each safe place must genuinely protect the notebook from
the local hazard. The inline ASP program mirrors that gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py
    python storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py --setting library --topic moths
    python storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py --setting greenhouse --safe-place atlas_drawer
    python storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py --all
    python storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/research_twist_kindness_mystery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "groundskeeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    research_spots: list[str] = field(default_factory=list)
    supports: set[str] = field(default_factory=set)
    hazard: str = ""
    hazard_text: str = ""
    risky_place: str = ""
    clue_style: str = ""


@dataclass
class Topic:
    id: str
    object_label: str
    plural_label: str
    wonder_line: str
    question_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafePlace:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    reveal_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    opening: str
    kindness: str
    note: str
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


def _r_hazard(world: World) -> list[str]:
    notebook = world.get("notebook")
    if notebook.attrs.get("location") != world.setting.risky_place:
        return []
    if notebook.meters["moved_to_safety"] >= THRESHOLD:
        return []
    sig = ("hazard", world.setting.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    notebook.meters["at_risk"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return ["__risk__"]


def _r_clue(world: World) -> list[str]:
    notebook = world.get("notebook")
    clue = world.get("clue")
    if notebook.meters["moved_to_safety"] < THRESHOLD:
        return []
    sig = ("clue", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["visible"] += 1
    hero = world.get("hero")
    hero.memes["curiosity"] += 1
    return ["__clue__"]


def _r_relief(world: World) -> list[str]:
    notebook = world.get("notebook")
    if notebook.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", notebook.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    helper.memes["kindness"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="hazard", tag="physical", apply=_r_hazard),
    Rule(name="clue", tag="mystery", apply=_r_clue),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
    return produced


def topic_supported(setting: Setting, topic: Topic) -> bool:
    return topic.id in setting.supports


def safe_from(setting: Setting, safe_place: SafePlace) -> bool:
    return setting.hazard in safe_place.protects


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for topic_id, topic in TOPICS.items():
            if not topic_supported(setting, topic):
                continue
            for safe_id, safe_place in SAFE_PLACES.items():
                if not safe_from(setting, safe_place):
                    continue
                for helper_id in HELPERS:
                    combos.append((setting_id, topic_id, safe_id, helper_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    topic: str
    safe_place: str
    helper: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(
        id="library",
        place="the old library",
        mood="The tall shelves made long shadows, and every step sounded small and secret.",
        research_spots=["the window table", "the atlas shelf", "the reading rug"],
        supports={"moths", "owls", "maps"},
        hazard="drip",
        hazard_text="Rain tapped the high window, and a thin drip had started sneaking across the sill.",
        risky_place="the window table",
        clue_style="a neat pencil arrow on a scrap of paper",
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the school greenhouse",
        mood="Glass walls shivered with light, and the leaves made soft whispering sounds.",
        research_spots=["the potting bench", "the seed shelf", "the watering table"],
        supports={"beans", "butterflies", "snails"},
        hazard="spray",
        hazard_text="A sprinkler arm gave a sudden hiss, and cool drops began to sweep across the bench.",
        risky_place="the potting bench",
        clue_style="a tiny leaf set beside a chalk arrow",
    ),
    "museum": Setting(
        id="museum",
        place="the small town museum",
        mood="The rooms were quiet as holding-breath, and the glass cases shone like moonlit boxes.",
        research_spots=["the vent-side stool", "the fossil cabinet", "the guide desk"],
        supports={"shells", "bones", "maps"},
        hazard="draft",
        hazard_text="A vent clicked awake, and a restless draft began flipping the corners of loose paper.",
        risky_place="the vent-side stool",
        clue_style="a folded ticket with a careful arrow drawn on the back",
    ),
}

TOPICS = {
    "moths": Topic(
        id="moths",
        object_label="moth",
        plural_label="moths",
        wonder_line="Their dusty wings looked like tiny folded secrets.",
        question_line="How could such soft wings make such quiet patterns?",
        tags={"research", "moths"},
    ),
    "owls": Topic(
        id="owls",
        object_label="owl",
        plural_label="owls",
        wonder_line="The pictures of round owl eyes made the page feel awake.",
        question_line="How could an owl fly so quietly at night?",
        tags={"research", "owl"},
    ),
    "maps": Topic(
        id="maps",
        object_label="map",
        plural_label="maps",
        wonder_line="Curvy blue rivers and dotted paths made the paper look full of adventures.",
        question_line="How did people know where to draw every road and hill?",
        tags={"research", "map"},
    ),
    "beans": Topic(
        id="beans",
        object_label="bean plant",
        plural_label="bean plants",
        wonder_line="The little shoots were brave enough to push right up through the soil.",
        question_line="How did a bean know which way was up?",
        tags={"research", "plants"},
    ),
    "butterflies": Topic(
        id="butterflies",
        object_label="butterfly",
        plural_label="butterflies",
        wonder_line="Every wing looked painted with a different bright idea.",
        question_line="Why did some butterflies rest with their wings closed and some with them open?",
        tags={"research", "butterfly"},
    ),
    "snails": Topic(
        id="snails",
        object_label="snail",
        plural_label="snails",
        wonder_line="Their shiny trails curled behind them like silver writing.",
        question_line="Why did a snail carry its home wherever it went?",
        tags={"research", "snail"},
    ),
    "shells": Topic(
        id="shells",
        object_label="shell",
        plural_label="shells",
        wonder_line="The shells seemed to hold faraway seaside whispers in their spirals.",
        question_line="How did shells grow such smooth curves?",
        tags={"research", "shell"},
    ),
    "bones": Topic(
        id="bones",
        object_label="bone",
        plural_label="bones",
        wonder_line="The old bones looked still and patient, as if they remembered enormous footsteps.",
        question_line="How could one small piece help someone guess a whole ancient animal?",
        tags={"research", "bones"},
    ),
}

SAFE_PLACES = {
    "atlas_drawer": SafePlace(
        id="atlas_drawer",
        label="atlas drawer",
        phrase="the deep atlas drawer under the map cabinet",
        protects={"drip", "draft"},
        reveal_line="Inside the drawer, the notebook lay flat and dry beside a stack of giant maps.",
        tags={"drawer", "maps"},
    ),
    "seed_box": SafePlace(
        id="seed_box",
        label="seed box",
        phrase="the dry seed box on the highest shelf",
        protects={"spray"},
        reveal_line="Inside the seed box, the notebook rested on clean paper packets that smelled faintly green.",
        tags={"seeds", "plants"},
    ),
    "guide_desk": SafePlace(
        id="guide_desk",
        label="guide desk",
        phrase="the guide desk with the wide wooden top",
        protects={"draft", "drip", "spray"},
        reveal_line="On the guide desk, the notebook waited under a smooth paperweight shaped like a little globe.",
        tags={"desk", "safe"},
    ),
}

HELPERS = {
    "librarian": Helper(
        id="librarian",
        type="librarian",
        label="the librarian",
        opening="A cardigan sleeve slipped past the shelf corner and was gone again.",
        kindness="I saw the danger first and moved your notebook before anything bad could happen.",
        note="For your research: follow the arrow to the dry place.",
        tags={"librarian", "kindness"},
    ),
    "groundskeeper": Helper(
        id="groundskeeper",
        type="groundskeeper",
        label="the groundskeeper",
        opening="A pair of soft work shoes whispered once across the floor.",
        kindness="I did not want your careful work to get spoiled, so I tucked it somewhere safer.",
        note="Little detective, look where papers stay safe.",
        tags={"helper", "kindness"},
    ),
    "teacher": Helper(
        id="teacher",
        type="teacher",
        label="the teacher",
        opening="A familiar gentle voice murmured to someone far down the hall and then faded.",
        kindness="Your pages mattered, so I moved them before the wet or wind could reach them.",
        note="Good research deserves a safe resting place.",
        tags={"teacher", "kindness"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Lucy", "Ella", "Zoe", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Noah", "Finn", "Leo"]


def introduce(world: World, hero: Entity, friend: Entity, topic: Topic) -> None:
    world.say(
        f"{hero.id} had come to {world.setting.place} with {friend.id} to do research about {topic.plural_label}."
    )
    world.say(world.setting.mood)
    world.say(
        f"{hero.id} wrote notes in a small blue notebook. {topic.wonder_line} "
        f'On the first page, {hero.pronoun()} had written, "{topic.question_line}"'
    )
    hero.memes["curiosity"] += 1


def settle_in(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Together they looked carefully, whispered guesses, and felt proud of how serious their little investigation seemed."
    )
    hero.memes["focus"] += 1
    friend.memes["focus"] += 1


def leave_notebook(world: World, hero: Entity) -> None:
    notebook = world.get("notebook")
    notebook.attrs["location"] = world.setting.risky_place
    world.say(
        f"When {hero.id} hopped away to compare one more clue, {hero.pronoun('possessive')} notebook stayed behind on {world.setting.risky_place}."
    )


def danger_stirs(world: World, hero: Entity) -> None:
    propagate(world, narrate=False)
    world.say(world.setting.hazard_text)
    world.say(
        f"Anyone watching closely could have seen that the notebook was in trouble."
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"But {hero.id} did not know that yet."
        )


def helper_moves(world: World, helper_cfg: Helper, safe_place: SafePlace) -> None:
    notebook = world.get("notebook")
    clue = world.get("clue")
    helper = world.get("helper")
    notebook.attrs["location"] = safe_place.label
    notebook.meters["moved_to_safety"] += 1
    clue.attrs["text"] = helper_cfg.note
    clue.attrs["style"] = world.setting.clue_style
    helper.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(helper_cfg.opening)
    world.say(
        f"A moment later the notebook was gone from {world.setting.risky_place}."
    )


def discover_loss(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["suspicion"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"When {hero.id} came back, the empty space on {world.setting.risky_place} made {hero.pronoun('possessive')} stomach feel cold."
    )
    world.say(
        f'"My notebook is gone," {hero.pronoun()} whispered. "All my research was in there."'
    )
    world.say(
        f'{friend.id} looked around the room instead of blaming anyone right away. "Let\'s look for a clue first," {friend.pronoun()} said.'
    )


def notice_clue(world: World, hero: Entity, friend: Entity) -> None:
    clue = world.get("clue")
    if clue.meters["visible"] < THRESHOLD:
        return
    hero.memes["suspicion"] -= 0.5
    world.say(
        f"Near the empty spot lay {clue.attrs['style']}. It did not look mean or sneaky. It looked careful."
    )
    world.say(
        f'{hero.id} picked it up and read, "{clue.attrs["text"]}"'
    )


def investigate(world: World, hero: Entity, friend: Entity, safe_place: SafePlace) -> None:
    hero.memes["detective"] += 1
    friend.memes["helpfulness"] += 1
    world.say(
        f"That was the twist in the mystery: perhaps the missing notebook had not been stolen at all."
    )
    world.say(
        f"So the two children followed the arrow and small signs until they reached {safe_place.phrase}."
    )


def find_notebook(world: World, hero: Entity, friend: Entity, safe_place: SafePlace) -> None:
    notebook = world.get("notebook")
    notebook.meters["found"] += 1
    notebook.attrs["location"] = safe_place.label
    propagate(world, narrate=False)
    world.say(safe_place.reveal_line)
    world.say(
        f"{hero.id} pressed both hands over {hero.pronoun('possessive')} heart and let out a long breath."
    )


def reveal_kindness(world: World, hero: Entity, helper_cfg: Helper) -> None:
    helper = world.get("helper")
    world.say(
        f"Then {helper_cfg.label} stepped forward with a warm smile. "
        f'"{helper_cfg.kindness}"'
    )
    world.say(
        f"{hero.id} blinked. The frightening mystery turned gentle all at once."
    )


def ending(world: World, hero: Entity, friend: Entity, topic: Topic) -> None:
    helper = world.get("helper")
    world.say(
        f'"Thank you for saving it," {hero.id} said. {friend.id} smiled too, because kindness had solved the mystery better than guessing ever could.'
    )
    world.say(
        f"Soon the notebook was open again, dry and safe, and {hero.id} bent over the page to keep writing research about {topic.plural_label}."
    )
    world.say(
        f"The room no longer felt spooky. It felt full of helpers, careful clues, and one very happy detective."
    )
    hero.memes["trust"] += 1
    helper.memes["kindness"] += 1


def tell(
    setting: Setting,
    topic: Topic,
    safe_place: SafePlace,
    helper_cfg: Helper,
    name: str = "Lina",
    gender: str = "girl",
    friend: str = "Milo",
    friend_gender: str = "boy",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, role="hero"))
    friend_ent = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend, role="friend"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper"))
    notebook = world.add(Entity(id="notebook", type="notebook", label="notebook", phrase="a small blue notebook"))
    clue = world.add(Entity(id="clue", type="clue", label="clue"))
    hero.attrs["name"] = name
    friend_ent.attrs["name"] = friend

    introduce(world, hero, friend_ent, topic)
    settle_in(world, hero, friend_ent)

    world.para()
    leave_notebook(world, hero)
    danger_stirs(world, hero)
    helper_moves(world, helper_cfg, safe_place)

    world.para()
    discover_loss(world, hero, friend_ent)
    notice_clue(world, hero, friend_ent)
    investigate(world, hero, friend_ent, safe_place)

    world.para()
    find_notebook(world, hero, friend_ent, safe_place)
    reveal_kindness(world, hero, helper_cfg)
    ending(world, hero, friend_ent, topic)

    world.facts.update(
        hero=hero,
        friend=friend_ent,
        helper=helper,
        setting=setting,
        topic=topic,
        safe_place=safe_place,
        notebook=notebook,
        clue=clue,
        clue_visible=clue.meters["visible"] >= THRESHOLD,
        found=notebook.meters["found"] >= THRESHOLD,
        risk=notebook.meters["at_risk"] >= THRESHOLD,
        kindness=helper.memes["kindness"] >= THRESHOLD or helper.memes["care"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "research": [
        (
            "What is research?",
            "Research means looking carefully to learn more about something. You ask questions, notice details, and write down what you find."
        )
    ],
    "moths": [
        (
            "What is a moth?",
            "A moth is an insect with wings covered in tiny scales. Many moths fly at night and rest quietly in the day."
        )
    ],
    "owl": [
        (
            "Why do owls seem so quiet?",
            "Owls have special feathers that help them fly softly. That is why they can seem almost silent."
        )
    ],
    "map": [
        (
            "What does a map show?",
            "A map shows where places are. It can help people find roads, rivers, buildings, and paths."
        )
    ],
    "plants": [
        (
            "What does a seed need to start growing?",
            "A seed needs the right mix of water, warmth, and air. Then it can begin to sprout."
        )
    ],
    "butterfly": [
        (
            "What is a butterfly?",
            "A butterfly is an insect with four wings and a long life change from caterpillar to chrysalis to butterfly."
        )
    ],
    "snail": [
        (
            "Why does a snail have a shell?",
            "A snail's shell helps protect its soft body. The snail carries that shelter with it."
        )
    ],
    "shell": [
        (
            "How are shells made?",
            "A shell is made by the animal living inside it. The shell grows as the animal grows."
        )
    ],
    "bones": [
        (
            "Why do bones matter in a museum?",
            "Bones can help people learn what an animal looked like and how it moved. They are clues from long ago."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help, protect, or comfort someone. Sometimes kindness is quiet and careful."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You solve it by looking for clues and thinking carefully."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "research",
    "moths",
    "owl",
    "map",
    "plants",
    "butterfly",
    "snail",
    "shell",
    "bones",
    "kindness",
    "mystery",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    topic = f["topic"]
    setting = f["setting"]
    helper = f["helper"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the word "research" and ends with a kind twist.',
        f"Tell a story about a child named {hero.label} doing research about {topic.plural_label} in {setting.place}, where a missing notebook seems mysterious at first but is found because someone was being kind.",
        f"Write a child-facing mystery where clues lead to a safe hiding place, and the ending reveals that {helper.label_word} protected the notebook instead of taking it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    topic = f["topic"]
    setting = f["setting"]
    safe_place = f["safe_place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who was doing research about {topic.plural_label}, {friend.label}, who helped look for clues, and {helper.label_word}, who moved the notebook."
        ),
        (
            f"What was {hero.label} researching?",
            f"{hero.label} was researching {topic.plural_label} in {setting.place}. The notebook held the careful notes and questions from that work."
        ),
        (
            "Why did the notebook seem to disappear?",
            f"It seemed to disappear because it was gone from {setting.risky_place} when {hero.label} came back. That made the room feel mysterious before anyone knew what had really happened."
        ),
    ]
    if f.get("risk"):
        qa.append(
            (
                "Why did someone move the notebook?",
                f"Someone moved it because a nearby danger could have ruined it. The notebook had been left at {setting.risky_place}, where {setting.hazard_text[0].lower() + setting.hazard_text[1:]}."
            )
        )
    if f.get("clue_visible"):
        qa.append(
            (
                "How did the children solve the mystery?",
                f"They stopped and looked for a clue instead of blaming anyone. The note and arrow led them to {safe_place.phrase}, where the notebook was waiting dry and safe."
            )
        )
    if f.get("found") and f.get("kindness"):
        qa.append(
            (
                "What was the twist at the end?",
                f"The twist was that nobody had stolen the notebook at all. {helper.label_word.capitalize()} had moved it to protect {hero.label}'s research, so the mystery turned out to be an act of kindness."
            )
        )
        qa.append(
            (
                f"How did {hero.label} feel at the end?",
                f"{hero.label} felt relieved and grateful. The notebook was safe again, and the scary feeling changed into trust and thankfulness."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"research", "kindness", "mystery"}
    tags |= set(f["topic"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="library",
        topic="moths",
        safe_place="atlas_drawer",
        helper="librarian",
        name="Lina",
        gender="girl",
        friend="Milo",
        friend_gender="boy",
    ),
    StoryParams(
        setting="greenhouse",
        topic="snails",
        safe_place="seed_box",
        helper="teacher",
        name="Owen",
        gender="boy",
        friend="Ava",
        friend_gender="girl",
    ),
    StoryParams(
        setting="museum",
        topic="bones",
        safe_place="guide_desk",
        helper="groundskeeper",
        name="Nora",
        gender="girl",
        friend="Theo",
        friend_gender="boy",
    ),
    StoryParams(
        setting="library",
        topic="maps",
        safe_place="guide_desk",
        helper="teacher",
        name="Finn",
        gender="boy",
        friend="Lucy",
        friend_gender="girl",
    ),
]


def explain_rejection(setting: Optional[Setting], topic: Optional[Topic], safe_place: Optional[SafePlace]) -> str:
    if setting is not None and topic is not None and not topic_supported(setting, topic):
        choices = ", ".join(sorted(setting.supports))
        return (
            f"(No story: {setting.place} does not fit research about {topic.plural_label} here. "
            f"Try a topic supported in that setting, such as: {choices}.)"
        )
    if setting is not None and safe_place is not None and not safe_from(setting, safe_place):
        return (
            f"(No story: {safe_place.phrase} would not protect a notebook from the {setting.hazard} in {setting.place}. "
            f"The safe place must really keep the notebook safe.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
supports_topic(S, T) :- setting(S), topic(T), supports(S, T).
safe_for(S, P) :- setting(S), safe_place(P), hazard_of(S, H), protects(P, H).
valid(S, T, P, H) :- setting(S), topic(T), safe_place(P), helper(H),
                     supports_topic(S, T), safe_for(S, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("hazard_of", setting_id, setting.hazard))
        for topic_id in sorted(setting.supports):
            lines.append(asp.fact("supports", setting_id, topic_id))
    for topic_id in TOPICS:
        lines.append(asp.fact("topic", topic_id))
    for safe_id, safe_place in SAFE_PLACES.items():
        lines.append(asp.fact("safe_place", safe_id))
        for hazard in sorted(safe_place.protects):
            lines.append(asp.fact("protects", safe_id, hazard))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        parser = build_parser()
        for seed in range(10):
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
    except StoryError as err:
        print(f"SMOKE SETUP FAILED: {err}")
        return 1

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header="" if idx > 1 else "")
        except Exception as err:  # pragma: no cover - CLI smoke
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
            return 1
    print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing research notebook, a kind twist, and a gentle mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--safe-place", choices=SAFE_PLACES, dest="safe_place")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"], dest="friend_gender")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test stories")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    topic = TOPICS.get(args.topic) if args.topic else None
    safe_place = SAFE_PLACES.get(args.safe_place) if args.safe_place else None

    if setting is not None and topic is not None and not topic_supported(setting, topic):
        raise StoryError(explain_rejection(setting, topic, None))
    if setting is not None and safe_place is not None and not safe_from(setting, safe_place):
        raise StoryError(explain_rejection(setting, None, safe_place))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.topic is None or combo[1] == args.topic)
        and (args.safe_place is None or combo[2] == args.safe_place)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError(explain_rejection(setting, topic, safe_place))

    chosen_setting, chosen_topic, chosen_safe_place, chosen_helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    name = args.name or pick_name(rng, gender)
    friend = args.friend or pick_name(rng, friend_gender, avoid=name)
    return StoryParams(
        setting=chosen_setting,
        topic=chosen_topic,
        safe_place=chosen_safe_place,
        helper=chosen_helper,
        name=name,
        gender=gender,
        friend=friend,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.topic not in TOPICS:
        raise StoryError(f"(Unknown topic: {params.topic})")
    if params.safe_place not in SAFE_PLACES:
        raise StoryError(f"(Unknown safe place: {params.safe_place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    topic = TOPICS[params.topic]
    safe_place = SAFE_PLACES[params.safe_place]
    helper_cfg = HELPERS[params.helper]

    if not topic_supported(setting, topic):
        raise StoryError(explain_rejection(setting, topic, None))
    if not safe_from(setting, safe_place):
        raise StoryError(explain_rejection(setting, None, safe_place))

    world = tell(
        setting=setting,
        topic=topic,
        safe_place=safe_place,
        helper_cfg=helper_cfg,
        name=params.name,
        gender=params.gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, topic, safe_place, helper) combos:\n")
        for setting, topic, safe_place, helper in combos:
            print(f"  {setting:10} {topic:12} {safe_place:12} {helper}")
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
            header = f"### {p.name}: {p.topic} in {p.setting} ({p.safe_place}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
