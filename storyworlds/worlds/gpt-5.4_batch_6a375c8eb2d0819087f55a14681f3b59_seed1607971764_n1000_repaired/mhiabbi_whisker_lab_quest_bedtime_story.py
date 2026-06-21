#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py
=====================================================================

A standalone story world for a bedtime quest: mhiabbi and Whisker the cat have
built a tiny "lab" out of blankets and pillows, but something about the nest is
not right yet. Instead of a generic paragraph with swapped nouns, this world
models a small physical and emotional state: a sleepy place, one bedtime
trouble, a sensible remedy, and a whispered quest through the house to make the
lab ready for sleep.

Run it
------
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py --lab window_lab --trouble chilly --remedy quilt
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py --trouble thirsty --remedy moon_lamp
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/mhiabbi_whisker_lab_quest_bedtime_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"cat", "kitten"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class LabSetting:
    id: str
    label: str
    phrase: str
    scene: str
    affords: set[str] = field(default_factory=set)
    opening: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Trouble:
    id: str
    label: str
    need: str
    sign: str
    whisper: str
    quest_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    need: str
    source: str
    carry: str
    apply_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: LabSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "trouble_active": False,
            "remedy_applied": False,
            "quest_started": False,
            "hummed": False,
            "resolved": False,
        }

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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_trouble_unsettles(world: World) -> list[str]:
    if not world.facts["trouble_active"] or world.facts["resolved"]:
        return []
    whisker = world.get("Whisker")
    child = world.get("mhiabbi")
    lab = world.get("lab")
    sig = ("trouble_unsettles", world.facts["trouble"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    whisker.meters["restless"] += 1
    lab.meters["unsettled"] += 1
    child.memes["worry"] += 1
    return ["__trouble__"]


def _r_remedy_soothes(world: World) -> list[str]:
    if not world.facts["remedy_applied"] or world.facts["resolved"]:
        return []
    remedy = world.facts["remedy"]
    trouble = world.facts["trouble"]
    if remedy.need != trouble.need:
        return []
    sig = ("remedy_soothes", remedy.id, trouble.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    whisker = world.get("Whisker")
    child = world.get("mhiabbi")
    lab = world.get("lab")
    whisker.meters["restless"] = 0.0
    whisker.meters["sleepy"] += 1
    whisker.memes["calm"] += 1
    child.memes["hope"] += 1
    child.memes["relief"] += 1
    lab.meters["cozy"] += 1
    return ["__soothed__"]


def _r_hum_to_sleep(world: World) -> list[str]:
    if not world.facts["hummed"] or world.facts["resolved"]:
        return []
    whisker = world.get("Whisker")
    if whisker.memes["calm"] < THRESHOLD:
        return []
    sig = ("hum_to_sleep",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    whisker.meters["asleep"] += 1
    world.get("mhiabbi").memes["peace"] += 1
    world.facts["resolved"] = True
    return ["__sleep__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble_unsettles", tag="bedtime", apply=_r_trouble_unsettles),
    Rule(name="remedy_soothes", tag="comfort", apply=_r_remedy_soothes),
    Rule(name="hum_to_sleep", tag="bedtime", apply=_r_hum_to_sleep),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def trouble_fits(setting: LabSetting, trouble: Trouble) -> bool:
    return trouble.id in setting.affords


def remedy_fits(trouble: Trouble, remedy: Remedy) -> bool:
    return trouble.need == remedy.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lab_id, lab in LABS.items():
        for trouble_id, trouble in TROUBLES.items():
            for remedy_id, remedy in REMEDIES.items():
                if trouble_fits(lab, trouble) and remedy_fits(trouble, remedy):
                    combos.append((lab_id, trouble_id, remedy_id))
    return combos


def predict_rest(world: World, remedy: Remedy) -> dict[str, bool]:
    sim = world.copy()
    sim.facts["remedy"] = remedy
    sim.facts["remedy_applied"] = True
    propagate(sim, narrate=False)
    sim.facts["hummed"] = True
    propagate(sim, narrate=False)
    whisker = sim.get("Whisker")
    return {
        "calm": whisker.memes["calm"] >= THRESHOLD,
        "asleep": whisker.meters["asleep"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, cat: Entity, parent: Entity, setting: LabSetting) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"At bedtime, mhiabbi built {setting.phrase} in {setting.scene}. "
        f"{setting.opening}"
    )
    world.say(
        f"Whisker padded in with his tail held high, and {child.id} whispered that "
        f"the little lab was ready for one last Quest before sleep."
    )
    world.say(
        f"{parent.label_word.capitalize()} tucked the last blanket edge smooth and "
        f"smiled from the doorway."
    )


def observe_trouble(world: World, child: Entity, cat: Entity, trouble: Trouble) -> None:
    world.facts["trouble_active"] = True
    propagate(world, narrate=False)
    world.say(
        f"But Whisker did not curl into his nest. {trouble.sign}"
    )
    world.say(
        f'"Oh, Whisker," mhiabbi whispered. "{trouble.whisper}"'
    )


def declare_quest(world: World, child: Entity, trouble: Trouble) -> None:
    world.facts["quest_started"] = True
    child.memes["brave"] += 1
    world.say(
        f"Mhiabbi touched the cardboard star pinned to the lab wall. "
        f'"Then this is a bedtime Quest," {child.pronoun()} said softly. '
        f'"{trouble.quest_line}"'
    )


def seek_remedy(world: World, child: Entity, parent: Entity, remedy: Remedy) -> None:
    child.meters["steps"] += 1
    world.say(
        f"So mhiabbi and {parent.label_word} tiptoed to {remedy.source}. "
        f"{remedy.carry}"
    )


def apply_remedy(world: World, child: Entity, cat: Entity, remedy: Remedy) -> None:
    world.facts["remedy_applied"] = True
    propagate(world, narrate=False)
    world.say(remedy.apply_text)
    if cat.memes["calm"] >= THRESHOLD:
        world.say(
            "Whisker's ears softened, and the tight little worry in the lab melted away."
        )


def hum_goodnight(world: World, child: Entity, parent: Entity, cat: Entity, trouble: Trouble) -> None:
    parent.memes["gentle"] += 1
    world.facts["hummed"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word} hummed a sleepy tune while mhiabbi sat beside "
        f"Whisker and counted three slow breaths."
    )
    if cat.meters["asleep"] >= THRESHOLD:
        world.say(
            f"Soon Whisker was asleep at last, and {trouble.ending_image}"
        )


def close_story(world: World, child: Entity, parent: Entity, setting: LabSetting) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"Mhiabbi crawled into the lab too, feeling proud and small and sleepy all at once."
    )
    world.say(
        f'"Good work, bedtime scientist," {parent.label_word} whispered. '
        f'The {setting.label} held its quiet shape until even the moon looked drowsy.'
    )


def tell(setting: LabSetting, trouble: Trouble, remedy: Remedy, parent_type: str = "mother") -> World:
    world = World(setting)

    child = world.add(Entity(
        id="mhiabbi",
        kind="character",
        type="girl",
        label="mhiabbi",
        role="child",
        traits=["careful", "sleepy", "kind"],
        attrs={"quest_name": "Bedtime Quest"},
        tags={"child"},
    ))
    cat = world.add(Entity(
        id="Whisker",
        kind="character",
        type="cat",
        label="Whisker",
        role="cat",
        traits=["soft", "curious"],
        attrs={"favorite_place": setting.label},
        tags={"cat"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        traits=["gentle"],
        tags={"grownup"},
    ))
    lab = world.add(Entity(
        id="lab",
        kind="thing",
        type="lab",
        label=setting.label,
        phrase=setting.phrase,
        tags=set(setting.tags),
    ))

    child.memes["care"] = 1.0
    cat.meters["restless"] = 0.0
    cat.meters["sleepy"] = 0.0
    cat.meters["asleep"] = 0.0
    cat.memes["calm"] = 0.0
    lab.meters["cozy"] = 0.0
    lab.meters["unsettled"] = 0.0

    world.facts.update({
        "child": child,
        "cat": cat,
        "parent": parent,
        "lab_cfg": setting,
        "trouble": trouble,
        "remedy": remedy,
    })

    introduce(world, child, cat, parent, setting)
    world.para()
    observe_trouble(world, child, cat, trouble)
    declare_quest(world, child, trouble)
    world.para()
    seek_remedy(world, child, parent, remedy)
    apply_remedy(world, child, cat, remedy)
    hum_goodnight(world, child, parent, cat, trouble)
    world.para()
    close_story(world, child, parent, setting)

    world.facts.update({
        "resolved": world.facts["resolved"],
        "quest_steps": int(child.meters["steps"]),
        "asleep": cat.meters["asleep"] >= THRESHOLD,
    })
    return world


LABS = {
    "window_lab": LabSetting(
        id="window_lab",
        label="window lab",
        phrase="a moon-blue lab of pillows under the window",
        scene="the corner of mhiabbi's room",
        affords={"chilly", "dark"},
        opening="A silver line of moonlight lay across the floor like a tiny road.",
        tags={"lab", "moon"},
    ),
    "blanket_lab": LabSetting(
        id="blanket_lab",
        label="blanket lab",
        phrase="a soft blanket lab between the bed and the bookshelf",
        scene="the warmest spot in the room",
        affords={"dark", "lonely"},
        opening="A toy flashlight lay nearby, but its batteries had long ago gone to sleep.",
        tags={"lab", "blanket"},
    ),
    "hall_lab": LabSetting(
        id="hall_lab",
        label="hall lab",
        phrase="a hush-hush lab beside the night hall",
        scene="the little landing outside the bedroom",
        affords={"lonely", "thirsty"},
        opening="The night-light made a small puddle of gold on the wall.",
        tags={"lab", "hall"},
    ),
}

TROUBLES = {
    "dark": Trouble(
        id="dark",
        label="too dark",
        need="light",
        sign="He blinked at the dim corners and gave one puzzled little mew.",
        whisper="The lab is too shadowy for your brave whisker work.",
        quest_line="We need a softer light, not a bigger noise.",
        ending_image="his paws tucked under him while the lamplight rested like butter on his fur",
        tags={"dark", "light"},
    ),
    "chilly": Trouble(
        id="chilly",
        label="too chilly",
        need="warmth",
        sign="He stepped in, then stepped out again, lifting one paw from the cool floor.",
        whisper="Your paws are telling me this lab feels cold.",
        quest_line="We need a warmer nest, quiet as a cloud.",
        ending_image="his nose disappeared beneath the quilt and only one pleased whisker showed",
        tags={"cold", "warmth"},
    ),
    "lonely": Trouble(
        id="lonely",
        label="too lonely",
        need="company",
        sign="He circled twice and looked back toward the doorway instead of settling down.",
        whisper="You want the lab to feel closer to home.",
        quest_line="We need a little company for a heart that is still awake.",
        ending_image="his purr hummed against mhiabbi's sleeve until both of them went still",
        tags={"lonely", "company"},
    ),
    "thirsty": Trouble(
        id="thirsty",
        label="too thirsty",
        need="water",
        sign="He licked his lips, nosed the blanket edge, and would not lie down.",
        whisper="A thirsty explorer cannot sleep yet.",
        quest_line="We need one small drink before dreams can begin.",
        ending_image="he drank, sighed, and folded himself into a neat sleepy comma",
        tags={"thirsty", "water"},
    ),
}

REMEDIES = {
    "moon_lamp": Remedy(
        id="moon_lamp",
        label="moon lamp",
        phrase="a little moon lamp",
        need="light",
        source="the top shelf of the hallway table",
        carry="Dad lifted down a little moon lamp, and mhiabbi carried it with two careful hands as if it were a tiny moon egg.",
        apply_text="Back in the lab, mhiabbi clicked on the moon lamp and set it near Whisker's pillow. A round honey-colored glow spread across the blankets without hurting the quiet.",
        qa_text="used a little moon lamp to make the lab softly bright",
        tags={"lamp", "light"},
    ),
    "quilt": Remedy(
        id="quilt",
        label="quilt",
        phrase="the patchwork quilt",
        need="warmth",
        source="the linen closet",
        carry="Mom opened the linen closet, and mhiabbi chose the smallest patchwork quilt, warm from the stack and smelling faintly of soap.",
        apply_text="Back in the lab, mhiabbi draped the quilt over the pillow nest and tucked the edges around Whisker's paws. The cool place turned snug at once.",
        qa_text="tucked a warm quilt around Whisker's nest",
        tags={"blanket", "warmth"},
    ),
    "sleep_song_box": Remedy(
        id="sleep_song_box",
        label="sleep song box",
        phrase="the sleep song box",
        need="company",
        source="the bedroom dresser",
        carry="Dad wound the tiny sleep song box, and mhiabbi carried it cupped against her pajamas so the music would not spill too soon.",
        apply_text="Back in the lab, mhiabbi set the sleep song box beside the nest. It played a slow, friendly tune that made the blankets feel less empty.",
        qa_text="set a little sleep song box beside Whisker so the lab felt friendly",
        tags={"music", "company"},
    ),
    "water_bowl": Remedy(
        id="water_bowl",
        label="water bowl",
        phrase="a fresh water bowl",
        need="water",
        source="the kitchen sink",
        carry="Mom filled a shallow bowl with fresh water, and mhiabbi walked beside her at careful mouse-steps so not one silver drop would leap out.",
        apply_text="Back in the lab, mhiabbi slid the water bowl onto a folded towel near Whisker. He bent to drink, and the whole room seemed to loosen its shoulders.",
        qa_text="brought Whisker a fresh bowl of water",
        tags={"water", "drink"},
    ),
}

PARENTS = ["mother", "father"]


@dataclass
class StoryParams:
    lab: str
    trouble: str
    remedy: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "lab": [
        ("What is a lab in this story?",
         "Here, a lab is a pretend little place for trying gentle ideas and seeing what helps. It is not a noisy science room, but a child-made nest for a bedtime Quest.")
    ],
    "light": [
        ("Why can a soft light help at bedtime?",
         "A soft light lets you see without making the room feel busy or bright. That can help bodies calm down when they are getting ready for sleep.")
    ],
    "warmth": [
        ("Why does warmth help someone rest?",
         "Warmth helps muscles relax and makes a nest feel safe and comfortable. When a body is not cold, it is easier to settle down.")
    ],
    "company": [
        ("Why can company help at bedtime?",
         "A gentle nearby sound or presence can make a place feel less lonely. Feeling safe with company can help a worried heart grow calm.")
    ],
    "water": [
        ("Why is it hard to sleep when you are thirsty?",
         "When you are thirsty, your body keeps asking for a drink instead of rest. A little water can fix that simple problem so sleep can come.")
    ],
    "lamp": [
        ("What is a moon lamp?",
         "A moon lamp is a small lamp shaped like the moon or glowing like it. It gives a gentle light that feels calm instead of harsh.")
    ],
    "blanket": [
        ("What does a quilt do?",
         "A quilt is a thick blanket that holds warmth. It can make a bed or nest feel cozy and snug.")
    ],
    "music": [
        ("What is a sleep song box?",
         "A sleep song box is a little music box that plays a quiet tune. Soft, steady sounds can help a place feel peaceful.")
    ],
    "drink": [
        ("Why do cats need fresh water?",
         "Cats need fresh water to stay comfortable and healthy. If a cat is thirsty, drinking can help it settle.")
    ],
}
KNOWLEDGE_ORDER = ["lab", "light", "warmth", "company", "water", "lamp", "blanket", "music", "drink"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trouble = f["trouble"]
    remedy = f["remedy"]
    setting = f["lab_cfg"]
    return [
        f'Write a bedtime story that includes the words "mhiabbi", "whisker", and "lab", and make it feel like a whispered Quest.',
        f"Tell a gentle story where mhiabbi helps Whisker settle in a {setting.label} because it feels {trouble.label}, and the fix is {remedy.phrase}.",
        f'Write a child-facing bedtime tale in which a tiny problem in a pretend lab sends a child and a grown-up on one soft, careful quest before sleep.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trouble = f["trouble"]
    remedy = f["remedy"]
    setting = f["lab_cfg"]
    parent = f["parent"]
    child = f["child"]
    cat = f["cat"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about mhiabbi, Whisker the cat, and {child.pronoun('possessive')} {parent.label_word}. They were trying to make a little lab feel ready for sleep."
        ),
        (
            "What was the bedtime Quest?",
            f"The Quest was to help Whisker settle inside the {setting.label}. It began when the lab felt {trouble.label} and he would not curl up."
        ),
        (
            "How could mhiabbi tell something was wrong?",
            f"Mhiabbi watched Whisker closely and noticed that {trouble.sign[:-1].lower()}. That small sign showed what the lab still needed before bedtime could work."
        ),
        (
            f"How did they help Whisker?",
            f"They {remedy.qa_text}. That worked because Whisker was unsettled by a need for {trouble.need}, and the remedy matched that need."
        ),
    ]
    if f["resolved"]:
        qa.append((
            "Why did Whisker fall asleep at the end?",
            f"Whisker fell asleep because the real problem in the lab was fixed first, so his body could relax. After that, the gentle humming and quiet company helped the calm feeling last."
        ))
        qa.append((
            "How did the ending show that the Quest was over?",
            f"The ending showed the Quest was over because Whisker finally slept and the lab turned peaceful. Mhiabbi felt proud and sleepy too, which proves the room had changed from worried to cozy."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lab"} | set(world.facts["trouble"].tags) | set(world.facts["remedy"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {{'resolved': {world.facts.get('resolved')}, 'quest_started': {world.facts.get('quest_started')}, 'trouble_active': {world.facts.get('trouble_active')}, 'remedy_applied': {world.facts.get('remedy_applied')}, 'hummed': {world.facts.get('hummed')}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lab="window_lab",
        trouble="chilly",
        remedy="quilt",
        parent="mother",
    ),
    StoryParams(
        lab="blanket_lab",
        trouble="dark",
        remedy="moon_lamp",
        parent="father",
    ),
    StoryParams(
        lab="hall_lab",
        trouble="thirsty",
        remedy="water_bowl",
        parent="mother",
    ),
    StoryParams(
        lab="blanket_lab",
        trouble="lonely",
        remedy="sleep_song_box",
        parent="father",
    ),
]


def explain_rejection(lab: LabSetting, trouble: Trouble, remedy: Remedy) -> str:
    if not trouble_fits(lab, trouble):
        supported = ", ".join(sorted(lab.affords))
        return (
            f"(No story: the {lab.label} does not naturally have the trouble '{trouble.id}'. "
            f"It supports: {supported}.)"
        )
    if not remedy_fits(trouble, remedy):
        return (
            f"(No story: {remedy.label} helps with {remedy.need}, but the trouble "
            f"'{trouble.id}' needs {trouble.need}. The bedtime Quest needs an honest fix.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
trouble_fits(L, T) :- lab(L), trouble(T), affords(L, T).
remedy_fits(T, R)  :- trouble(T), remedy(R), needs(T, N), soothes(R, N).
valid(L, T, R)     :- trouble_fits(L, T), remedy_fits(T, R).

chosen_valid :- chosen_lab(L), chosen_trouble(T), chosen_remedy(R), valid(L, T, R).
outcome(resolved) :- chosen_valid.
outcome(invalid)  :- chosen_lab(_), chosen_trouble(_), chosen_remedy(_), not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lab_id, lab in LABS.items():
        lines.append(asp.fact("lab", lab_id))
        for trouble_id in sorted(lab.affords):
            lines.append(asp.fact("affords", lab_id, trouble_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("needs", trouble_id, trouble.need))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("soothes", remedy_id, remedy.need))
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
        asp.fact("chosen_lab", params.lab),
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_remedy", params.remedy),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def outcome_of(params: StoryParams) -> str:
    try:
        lab = LABS[params.lab]
        trouble = TROUBLES[params.trouble]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter: {err.args[0]})") from err
    return "resolved" if trouble_fits(lab, trouble) and remedy_fits(trouble, remedy) else "invalid"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos() matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: mhiabbi, Whisker, a tiny lab, and a bedtime Quest."
    )
    ap.add_argument("--lab", choices=LABS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lab is not None and args.lab not in LABS:
        raise StoryError(f"(Unknown lab: {args.lab})")
    if args.trouble is not None and args.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {args.trouble})")
    if args.remedy is not None and args.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {args.remedy})")
    if args.parent is not None and args.parent not in PARENTS:
        raise StoryError(f"(Unknown parent type: {args.parent})")

    if args.lab and args.trouble and args.remedy:
        lab = LABS[args.lab]
        trouble = TROUBLES[args.trouble]
        remedy = REMEDIES[args.remedy]
        if not (trouble_fits(lab, trouble) and remedy_fits(trouble, remedy)):
            raise StoryError(explain_rejection(lab, trouble, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.lab is None or combo[0] == args.lab)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        if args.lab and args.trouble and args.remedy:
            raise StoryError(explain_rejection(LABS[args.lab], TROUBLES[args.trouble], REMEDIES[args.remedy]))
        raise StoryError("(No valid combination matches the given options.)")

    lab, trouble, remedy = rng.choice(sorted(combos))
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(
        lab=lab,
        trouble=trouble,
        remedy=remedy,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lab not in LABS:
        raise StoryError(f"(Unknown lab: {params.lab})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.parent not in PARENTS:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    setting = LABS[params.lab]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    if not trouble_fits(setting, trouble) or not remedy_fits(trouble, remedy):
        raise StoryError(explain_rejection(setting, trouble, remedy))

    world = tell(setting=setting, trouble=trouble, remedy=remedy, parent_type=params.parent)

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
        print(f"{len(combos)} valid (lab, trouble, remedy) combos:\n")
        for lab, trouble, remedy in combos:
            print(f"  {lab:12} {trouble:8} {remedy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.lab}: {p.trouble} -> {p.remedy} ({p.parent})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
