#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py
============================================================================

A standalone story world for a tall-tale flavored story about a giant reflector,
a bottle of ammonia, and a piece of koa wood. The core premise is simple and
state-driven: a child wants to make an enormous festival reflector shine, reaches
for a harsh cleaner, and either listens to a wiser warning or makes a small mess
that a calm grown-up repairs the sensible way. Every ending is happy, but the
world still insists on a real problem and a real fix.

Run it
------
    python storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py
    python storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py --project moon_wagon
    python storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py --cleaner soap
    python storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/reflector_ammonia_koa_happy_ending_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    material: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Project:
    id: str
    title: str
    boast: str
    place: str
    need: str
    ending: str
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
class Cleaner:
    id: str
    label: str
    phrase: str
    harsh: bool
    fumes: int
    dries_wood: bool
    warning: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
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
class StoryParams:
    project: str
    cleaner: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    helper_role: str
    trait: str
    child_age: int = 6
    helper_age: int = 8
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


def _r_fumes(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    air = world.get("air")
    child = world.get("child")
    helper = world.get("helper")
    if tool.meters["sprayed"] < THRESHOLD:
        return out
    sig = ("fumes", int(tool.meters["sprayed"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    strength = int(tool.attrs.get("fumes", 0))
    if strength > 0:
        air.meters["sting"] += float(strength)
        child.memes["alarm"] += 1
        helper.memes["concern"] += 1
        out.append("__fumes__")
    return out


def _r_koa_dries(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    tool = world.get("tool")
    if target.material != "koa":
        return out
    if tool.meters["sprayed"] < THRESHOLD:
        return out
    if not tool.attrs.get("dries_wood", False):
        return out
    sig = ("dry_finish", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["finish_dry"] += 1
    target.meters["dull"] += 1
    out.append("__dry__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fumes", tag="physical", apply=_r_fumes),
    Rule(name="dry_finish", tag="physical", apply=_r_koa_dries),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


PROJECTS = {
    "moon_wagon": Project(
        id="moon_wagon",
        title="the Moon Wagon",
        boast="It was so tall that crows used the axle for a weather vane, and its reflector was broad enough to wink at three hills at once.",
        place="on the windy ridge above town",
        need="needed to flash moonlight over the whole harvest dance",
        ending="when the moon climbed up, the wagon sent a silver stripe clear across the valley",
        tags={"reflector", "festival", "moon"},
    ),
    "river_lantern": Project(
        id="river_lantern",
        title="the River Lantern",
        boast="It was such a great contraption that the catfish were said to blink when its reflector turned their way.",
        place="beside the broad river bend",
        need="needed to toss a bright beam over the regatta after sunset",
        ending="when evening settled in, the lantern laid a bright road across the water",
        tags={"reflector", "river", "festival"},
    ),
    "cloud_sled": Project(
        id="cloud_sled",
        title="the Cloud Sled",
        boast="Folks claimed it was built so high that a goose could pass under the tongue without ducking.",
        place="at the fairground edge",
        need="needed to gleam for the night parade",
        ending="by dark, the sled shone so bright that even the stars looked newly polished",
        tags={"reflector", "parade", "moon"},
    ),
}

CLEANERS = {
    "ammonia": Cleaner(
        id="ammonia",
        label="ammonia",
        phrase="a bottle of ammonia",
        harsh=True,
        fumes=2,
        dries_wood=True,
        warning="That sharp stuff can bite your nose and drink the oil right out of koa.",
        tags={"ammonia", "fumes", "cleaner"},
    ),
    "soap": Cleaner(
        id="soap",
        label="soap",
        phrase="a bucket of lemon soap",
        harsh=False,
        fumes=0,
        dries_wood=False,
        warning="Soap is gentle and honest, so there is no real trouble in it.",
        tags={"soap", "cleaner"},
    ),
    "rainwater": Cleaner(
        id="rainwater",
        label="rainwater",
        phrase="a tin of rainwater",
        harsh=False,
        fumes=0,
        dries_wood=False,
        warning="Rainwater may be plain, but it makes no proper story trouble here.",
        tags={"water", "cleaner"},
    ),
}

RESPONSES = {
    "rinse_and_oil": Response(
        id="rinse_and_oil",
        sense=3,
        power=3,
        text="flung open every door, whisked the bottle away, wiped the koa with clean water, and rubbed sweet oil back into the thirsty grain",
        qa_text="opened the air, wiped the ammonia away, and rubbed oil back into the koa",
        tags={"fresh_air", "oil", "koa"},
    ),
    "soap_and_buff": Response(
        id="soap_and_buff",
        sense=3,
        power=2,
        text="threw the windows wide, chased the smell outside, cleaned the spill with a soft soapy cloth, and buffed the koa until the grain glowed like warm honey",
        qa_text="aired the place out, cleaned the spill with a soft cloth, and buffed the koa",
        tags={"fresh_air", "soap", "koa"},
    ),
    "dusty_rag": Response(
        id="dusty_rag",
        sense=1,
        power=1,
        text="rubbed at the mess with a dusty rag",
        qa_text="rubbed at it with a dusty rag",
        tags={"rag"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Sadie", "Lula", "Dora", "Maisie", "Tess"]
BOY_NAMES = ["Jeb", "Toby", "Hank", "Eli", "Beau", "Cal", "Otis", "Wade"]
TRAITS = ["careful", "steady", "thoughtful", "sensible", "curious", "bold"]
HELPER_ROLES = ["mother", "father", "aunt", "uncle"]


def hazard(project: Project, cleaner: Cleaner) -> bool:
    return "reflector" in project.tags and cleaner.harsh


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def damage_severity(project: Project) -> int:
    if project.id == "moon_wagon":
        return 3
    if project.id == "river_lantern":
        return 2
    return 2


def response_works(response: Response, project: Project) -> bool:
    return response.power >= damage_severity(project)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(helper_age: int, child_age: int, trait: str) -> bool:
    authority = initial_caution(trait) + (2.0 if helper_age > child_age else 0.0)
    return helper_age > child_age and authority > BRAVERY_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    tool = sim.get("tool")
    target = sim.get("target")
    tool.meters["sprayed"] += 1
    target.meters["splashed"] += 1
    propagate(sim, narrate=False)
    return {
        "fumes": sim.get("air").meters["sting"],
        "dry_finish": sim.get("target").meters["finish_dry"],
    }


def introduce(world: World, child: Entity, helper: Entity, project: Project) -> None:
    child.memes["wonder"] += 1
    helper.memes["purpose"] += 1
    world.say(
        f"On a day big enough to need two sunrises, {child.id} helped {helper.label_word} finish {project.title} {project.place}. {project.boast}"
    )
    world.say(
        f"The grand reflector at the front had to shine, because it {project.need}."
    )


def show_koa(world: World) -> None:
    world.say(
        "Around that reflector ran a smooth koa frame, striped and golden, with grain that curled like little rivers in old wood."
    )


def tempt(world: World, child: Entity, cleaner: Cleaner) -> None:
    child.memes["bravado"] += 1
    world.say(
        f"{child.id} spotted {cleaner.phrase} on the bench and grinned. "
        f'"One splash of {cleaner.label}, and this reflector will shine so bright it can comb the moon," {child.pronoun()} said.'
    )


def warn(world: World, helper: Entity, child: Entity, cleaner: Cleaner) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_fumes"] = pred["fumes"]
    world.facts["predicted_dry_finish"] = pred["dry_finish"]
    helper.memes["caution"] += 1
    extra = ""
    if pred["fumes"] >= THRESHOLD and pred["dry_finish"] >= THRESHOLD:
        extra = " The smell would sting, and the koa would go thirsty and pale."
    world.say(
        f'{helper.label_word.capitalize()} shook {helper.pronoun("possessive")} head. "{cleaner.warning}{extra}"'
    )


def back_down(world: World, child: Entity, helper: Entity) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} looked at the koa again, looked at the bottle again, and decided that some shortcuts were too sharp to trust."
    )
    world.say(
        f"Instead of grabbing the ammonia, {child.pronoun()} set it back on the bench and reached for a soft cloth."
    )


def defy(world: World, child: Entity, cleaner: Cleaner) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But the reflector was sitting there dull as a sleepy pond, and {child.id} could not resist. Before anyone could stop {child.pronoun("object")}, {child.pronoun()} tipped the {cleaner.label}.'
    )


def spray(world: World, cleaner: Cleaner) -> None:
    tool = world.get("tool")
    target = world.get("target")
    tool.meters["sprayed"] += 1
    target.meters["splashed"] += 1
    propagate(world, narrate=False)
    if world.get("air").meters["sting"] >= THRESHOLD and target.meters["finish_dry"] >= THRESHOLD:
        world.say(
            "The smell jumped up first, sharp enough to make the room blink, and the proud koa lost its rich glow in one sad swipe."
        )
    elif world.get("air").meters["sting"] >= THRESHOLD:
        world.say(
            "A sharp smell snapped into the air at once, and everybody took one step backward."
        )
    else:
        world.say(
            "The splash went wrong at once."
        )


def rescue(world: World, helper: Entity, response: Response) -> None:
    target = world.get("target")
    air = world.get("air")
    helper.memes["care"] += 1
    target.meters["finish_dry"] = 0.0
    target.meters["dull"] = 0.0
    target.meters["oiled"] += 1
    air.meters["sting"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} moved fast and calm, {helper.pronoun()} {response.text}."
    )
    world.say(
        "Little by little the color came back, deep and striped and warm, and the whole shed smelled like soap and fresh boards instead of trouble."
    )


def finish_shine(world: World, child: Entity, helper: Entity, project: Project) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.label_word} handed {child.id} the clean polishing cloth. Together they buffed the reflector until it caught the light in a broad silver smile."
    )
    world.say(
        f"By evening, {project.ending}. {child.id} laughed to see it and promised from then on to treat koa kindly and leave harsh bottles alone."
    )


def tell(
    project: Project,
    cleaner: Cleaner,
    response: Response,
    child_name: str = "Mabel",
    child_gender: str = "girl",
    helper_name: str = "Aunt June",
    helper_gender: str = "aunt",
    helper_role: str = "aunt",
    trait: str = "careful",
    child_age: int = 6,
    helper_age: int = 8,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        age=child_age,
        traits=["eager"],
        label=child_name,
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_role,
        role="helper",
        age=helper_age,
        traits=[trait],
        label=helper_name,
    ))
    world.add(Entity(id="target", type="frame", label="koa frame", role="target", material="koa", tags={"koa", "wood"}))
    world.add(Entity(
        id="tool",
        type="cleaner",
        label=cleaner.label,
        role="tool",
        attrs={"fumes": cleaner.fumes, "dries_wood": cleaner.dries_wood},
        tags=set(cleaner.tags),
    ))
    world.add(Entity(id="air", type="air", label="the air", role="air"))

    world.facts.update(
        project=project,
        cleaner=cleaner,
        response=response,
        child=child,
        helper=helper,
        target=world.get("target"),
        tool=world.get("tool"),
        outcome="",
        predicted_fumes=0.0,
        predicted_dry_finish=0.0,
    )

    introduce(world, child, helper, project)
    show_koa(world)

    world.para()
    tempt(world, child, cleaner)
    warn(world, helper, child, cleaner)

    averted = would_avert(helper_age, child_age, trait)
    if averted:
        back_down(world, child, helper)
        world.para()
        finish_shine(world, child, helper, project)
        outcome = "averted"
    else:
        defy(world, child, cleaner)
        world.para()
        spray(world, cleaner)
        world.para()
        rescue(world, helper, response)
        finish_shine(world, child, helper, project)
        outcome = "repaired"

    world.facts["outcome"] = outcome
    world.facts["averted"] = averted
    world.facts["repaired"] = outcome == "repaired"
    return world


KNOWLEDGE = {
    "reflector": [
        (
            "What is a reflector?",
            "A reflector is something that throws light back instead of making its own light. When it is clean and aimed well, it can make a dark place look much brighter.",
        )
    ],
    "ammonia": [
        (
            "What is ammonia?",
            "Ammonia is a strong cleaner with a sharp smell. Grown-ups may use it carefully, but children should not handle it on their own.",
        )
    ],
    "koa": [
        (
            "What is koa?",
            "Koa is a beautiful kind of wood known for warm color and curled grain. Wood like that needs gentle care so its finish stays rich and smooth.",
        )
    ],
    "fresh_air": [
        (
            "Why is fresh air important around strong smells?",
            "Fresh air helps carry strong fumes away so people do not keep breathing them. Opening doors and windows can make a space safer and more comfortable.",
        )
    ],
    "oil": [
        (
            "Why do some wooden things need oil?",
            "Oil can help keep finished wood from looking dry and tired. It brings back some glow and helps the surface stay cared for.",
        )
    ],
    "soap": [
        (
            "Why is soft soap gentler than a harsh cleaner?",
            "Soft soap cleans without biting as hard as a sharp chemical can. That makes it a better choice for many delicate surfaces.",
        )
    ],
}
KNOWLEDGE_ORDER = ["reflector", "ammonia", "koa", "fresh_air", "oil", "soap"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    project = f["project"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a tall-tale story for a young child that includes the words "reflector," "ammonia," and "koa." Make it about {project.title} and end happily.',
            f"Tell a funny frontier-style story where {child.id} wants to use ammonia on a giant reflector set in koa, but listens to a wiser warning before any damage is done.",
            "Write a gentle exaggerated story in tall-tale style where a child chooses patience over a risky shortcut and the great shining machine is ready by nightfall.",
        ]
    return [
        f'Write a tall-tale story for a young child that includes the words "reflector," "ammonia," and "koa." Make it about {project.title} and end happily.',
        f"Tell a big, boastful story where {child.id} tries ammonia on a giant reflector with koa around it, a calm grown-up fixes the mistake, and the night celebration still goes on.",
        "Write a simple happy-ending tall tale where a sharp cleaner causes a small scare, but fresh air, gentle hands, and hard work save the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    project = f["project"]
    cleaner = f["cleaner"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was helping {helper.label_word} with {project.title}. They were trying to get the giant reflector ready for a big evening show.",
        ),
        (
            "Why did they care so much about the reflector?",
            f"They needed the reflector to shine because {project.need}. In this tall tale, the machine was so enormous that its light was meant to reach far beyond one little yard.",
        ),
        (
            f"Why did {helper.label_word} warn {child.id} about the ammonia?",
            f'{helper.label_word.capitalize()} warned that the ammonia was too sharp for the koa frame. It could sting noses with fumes and make the wood finish look dry and pale.',
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {child.id} do after the warning?",
                f"{child.id} set the ammonia back down and chose the soft cloth instead. That kept the koa safe and let the work go on without any sharp-smelling trouble.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the reflector shining and {project.ending}. The ending proves that careful choices can still lead to a grand and glorious result.",
            )
        )
    else:
        qa.append(
            (
                f"What went wrong when {child.id} used the ammonia?",
                f"The air turned sharp, and the koa lost its rich glow for a moment. The trouble came because the cleaner was too harsh for both noses and the wood finish.",
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} fix the problem?",
                f'{helper.label_word.capitalize()} {response.qa_text}. That worked because the harsh cleaner was removed and the wood was treated gently afterward.',
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It still ended happily, because the reflector shone in time and {project.ending}. The scare turned into a lesson, not a disaster.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["project"].tags) | set(f["cleaner"].tags)
    if f["outcome"] == "repaired":
        tags |= set(f["response"].tags)
    else:
        tags |= {"soap"}
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
        if e.material:
            bits.append(f"material={e.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, project in PROJECTS.items():
        for cid, cleaner in CLEANERS.items():
            for rid, response in RESPONSES.items():
                if hazard(project, cleaner) and response.sense >= SENSE_MIN and response_works(response, project):
                    combos.append((pid, cid, rid))
    return combos


def explain_rejection(project: Project, cleaner: Cleaner, response: Optional[Response] = None) -> str:
    if not cleaner.harsh:
        return (
            f"(No story: {cleaner.label} is too gentle here. Without a real risk to the koa around the reflector, there is no honest problem to fix.)"
        )
    if response is not None and response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense. This world prefers calm, sensible repairs like rinse_and_oil or soap_and_buff.)"
        )
    if response is not None and not response_works(response, project):
        return (
            f"(No story: {response.id} is too weak for {project.title}. The fix must actually restore the koa and clear the sharp fumes.)"
        )
    return "(No story: this combination does not make a solid tall tale.)"


ASP_RULES = r"""
hazard(P, C) :- project(P), cleaner(C), harsh(C), has_reflector(P).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
works(P, R)  :- project(P), response(R), severity(P, Need), power(R, Pow), Pow >= Need.
valid(P, C, R) :- hazard(P, C), sensible(R), works(P, R).

careful(T)   :- trait(T), careful_trait(T).
authority(5) :- trait(T), careful(T), older_helper.
authority(3) :- trait(T), not careful(T), older_helper.
authority(0) :- not older_helper.
older_helper :- helper_age(H), child_age(C), H > C.
averted      :- authority(A), bravery_init(B), A + 2 > B.

outcome(averted) :- averted.
outcome(repaired) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        if "reflector" in project.tags:
            lines.append(asp.fact("has_reflector", pid))
        lines.append(asp.fact("severity", pid, damage_severity(project)))
    for cid, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cid))
        if cleaner.harsh:
            lines.append(asp.fact("harsh", cid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("child_age", params.child_age),
            asp.fact("helper_age", params.helper_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.helper_age, params.child_age, params.trait) else "repaired"


CURATED = [
    StoryParams(
        project="moon_wagon",
        cleaner="ammonia",
        response="rinse_and_oil",
        child="Mabel",
        child_gender="girl",
        helper="Aunt June",
        helper_gender="aunt",
        helper_role="aunt",
        trait="careful",
        child_age=6,
        helper_age=9,
    ),
    StoryParams(
        project="river_lantern",
        cleaner="ammonia",
        response="soap_and_buff",
        child="Jeb",
        child_gender="boy",
        helper="Uncle Roy",
        helper_gender="uncle",
        helper_role="uncle",
        trait="curious",
        child_age=7,
        helper_age=8,
    ),
    StoryParams(
        project="cloud_sled",
        cleaner="ammonia",
        response="soap_and_buff",
        child="Ruby",
        child_gender="girl",
        helper="Mama Flo",
        helper_gender="mother",
        helper_role="mother",
        trait="steady",
        child_age=5,
        helper_age=7,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant reflector, a risky bottle of ammonia, and a piece of koa saved by calm good sense."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_person(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender in {"girl"} else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def _pick_helper_name(rng: random.Random, role: str) -> str:
    if role == "mother":
        return rng.choice(["Mama Flo", "Mama June", "Mom"])
    if role == "father":
        return rng.choice(["Papa Ray", "Dad", "Pa"])
    if role == "aunt":
        return rng.choice(["Aunt June", "Aunt May", "Aunt Nell"])
    return rng.choice(["Uncle Roy", "Uncle Ben", "Uncle Wade"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cleaner is not None:
        cleaner = CLEANERS[args.cleaner]
        if not cleaner.harsh:
            project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
            raise StoryError(explain_rejection(project, cleaner))
    if args.response is not None:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
            cleaner = CLEANERS[args.cleaner] if args.cleaner else CLEANERS["ammonia"]
            raise StoryError(explain_rejection(project, cleaner, response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.cleaner is None or combo[1] == args.cleaner)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, cleaner_id, response_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child = _pick_person(rng, child_gender)
    helper_role = args.helper_role or rng.choice(HELPER_ROLES)
    helper_name = _pick_helper_name(rng, helper_role)
    trait = rng.choice(TRAITS)
    child_age = rng.randint(4, 7)
    helper_age = rng.randint(max(child_age + 1, 6), 10)
    return StoryParams(
        project=project_id,
        cleaner=cleaner_id,
        response=response_id,
        child=child,
        child_gender=child_gender,
        helper=helper_name,
        helper_gender=helper_role,
        helper_role=helper_role,
        trait=trait,
        child_age=child_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.cleaner not in CLEANERS:
        raise StoryError(f"(Unknown cleaner: {params.cleaner})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    project = PROJECTS[params.project]
    cleaner = CLEANERS[params.cleaner]
    response = RESPONSES[params.response]

    if not hazard(project, cleaner):
        raise StoryError(explain_rejection(project, cleaner, response))
    if response.sense < SENSE_MIN or not response_works(response, project):
        raise StoryError(explain_rejection(project, cleaner, response))

    world = tell(
        project=project,
        cleaner=cleaner,
        response=response,
        child_name=params.child,
        child_gender=params.child_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        helper_role=params.helper_role,
        trait=params.trait,
        child_age=params.child_age,
        helper_age=params.helper_age,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(25):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    bad = sum(1 for p in cases if outcome_of(p) != asp_outcome(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_sample = generate(smoke_params)
        with redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, cleaner, response) combos:\n")
        for project, cleaner, response in combos:
            print(f"  {project:13} {cleaner:8} {response}")
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
            header = f"### {p.child}: {p.project} with {p.cleaner} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
