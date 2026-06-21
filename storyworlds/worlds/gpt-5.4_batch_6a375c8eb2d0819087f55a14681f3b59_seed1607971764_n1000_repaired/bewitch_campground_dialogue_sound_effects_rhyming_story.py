#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bewitch_campground_dialogue_sound_effects_rhyming_story.py
======================================================================================

A standalone storyworld for a tiny rhyming campground tale:

two children hear a strange night sound, wonder if something might bewitch the
campground, and a calm grown-up helps them discover the true cause and fix the
problem in a sensible way.

The world model drives the prose:
- physical meters: darkness, noise, secured, revealed
- emotional memes: wonder, fear, relief, bravery, trust

The story always keeps a child-facing, rhyming tone, with dialogue and sound
effects woven into the narration.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_f"}
        male = {"boy", "father", "man", "ranger_m"}
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
            "ranger_f": "ranger",
            "ranger_m": "ranger",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class EveningPlan:
    id: str
    opening: str
    prop_line: str
    closing: str
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
class Disturber:
    id: str
    label: str
    kind: str
    location: str
    sound: str
    first_clue: str
    reveal: str
    fix: str
    spooky_name: str
    animal: bool = False
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
class Response:
    id: str
    label: str
    sense: int
    handles: set[str] = field(default_factory=set)
    inspect_line: str = ""
    success_line: str = ""
    qa_text: str = ""
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
    plan: str
    disturber: str
    response: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    helper: str
    helper_type: str
    trait: str
    comfort: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child1", "child2"}]

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


def _r_spook(world: World) -> list[str]:
    site = world.get("site")
    source = world.get("source")
    if site.meters["dark"] < THRESHOLD or source.meters["noise"] < THRESHOLD:
        return []
    sig = ("spook", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["wonder"] += 1
    return ["__spook__"]


def _r_reveal(world: World) -> list[str]:
    helper = world.get("helper")
    source = world.get("source")
    if helper.meters["light"] < THRESHOLD or source.meters["noise"] < THRESHOLD:
        return []
    sig = ("reveal", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["revealed"] += 1
    for kid in world.kids():
        if kid.memes["fear"] >= THRESHOLD:
            kid.memes["fear"] -= 1
        kid.memes["relief"] += 1
        kid.memes["bravery"] += 1
    return ["__reveal__"]


def _r_secure(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["secured"] < THRESHOLD:
        return []
    sig = ("secure", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["noise"] = 0.0
    site = world.get("site")
    if site.meters["disturbance"] >= THRESHOLD:
        site.meters["disturbance"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="spook", tag="emotion", apply=_r_spook),
    Rule(name="reveal", tag="emotion", apply=_r_reveal),
    Rule(name="secure", tag="physical", apply=_r_secure),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


PLANS = {
    "marshmallows": EveningPlan(
        id="marshmallows",
        opening="At the campground, the little fire made a gold-rimmed glow.",
        prop_line="The sticks were ready for marshmallows, soft in a row.",
        closing="Soon sweet smoke curled up while the bright stars leaned low.",
        tags={"campfire"},
    ),
    "stargazing": EveningPlan(
        id="stargazing",
        opening="At the campground, dusk painted the pine tops blue.",
        prop_line="A blanket lay open for star-counting two by two.",
        closing="Soon noses tipped upward as the first small star came through.",
        tags={"stars"},
    ),
    "songtime": EveningPlan(
        id="songtime",
        opening="At the campground, the fire ring glimmered red and round.",
        prop_line="The children clapped soft to a humming camping sound.",
        closing="Soon a song was skipping in a hop-around bound.",
        tags={"song"},
    ),
}

DISTURBERS = {
    "owl_pine": Disturber(
        id="owl_pine",
        label="owl",
        kind="animal",
        location="the tall pine above the tent",
        sound="Hoo-hoo! Hoo-hoo!",
        first_clue="two round eyes blinked high in the branches",
        reveal="an owl was perched in the pine, turning its head like a slow little moon",
        fix="The owl stayed in the tree, and its call stopped sounding scary once the children knew what it was.",
        spooky_name="a bewitching branch ghost",
        animal=True,
        tags={"owl", "night_sound"},
    ),
    "raccoon_cooler": Disturber(
        id="raccoon_cooler",
        label="raccoon",
        kind="animal",
        location="the snack cooler by the picnic table",
        sound="Clink-clank! Scritch-scratch!",
        first_clue="a striped tail flicked beside the cooler latch",
        reveal="a hungry raccoon was nudging the snack cooler with its clever paws",
        fix="Once the cooler clicked shut and was moved onto the table, the raccoon sniffed the air and padded away.",
        spooky_name="a bewitching snack sprite",
        animal=True,
        tags={"raccoon", "food"},
    ),
    "tent_flap": Disturber(
        id="tent_flap",
        label="tent flap",
        kind="object",
        location="the loose corner of the tent flap",
        sound="Flap-flap! Whiff-whuff!",
        first_clue="the loose canvas kept tapping the tent pole",
        reveal="the tent flap was dancing in the wind and slapping the pole",
        fix="When the flap was tied snug, the wild clapping quit and the tent stood still.",
        animal=False,
        tags={"tent", "wind"},
    ),
}

RESPONSES = {
    "lantern_peek": Response(
        id="lantern_peek",
        label="lantern peek",
        sense=3,
        handles={"owl_pine"},
        inspect_line='lifted a camping lantern and said, "Let us look before we leap. Night sounds can be odd, but not every odd sound is deep."',
        success_line="The warm lantern glow climbed up the bark and showed the harmless singer there.",
        qa_text="used a camping lantern to show the children what was in the tree",
        tags={"lantern", "light"},
    ),
    "latch_cooler": Response(
        id="latch_cooler",
        label="latch the cooler",
        sense=3,
        handles={"raccoon_cooler"},
        inspect_line='clicked on a flashlight and said, "Snacks left loose invite curious feet. We will check the cooler before that rustling repeats."',
        success_line="The beam found the cooler first, then the visitor beside it, and quick hands fixed the latch.",
        qa_text="shone a flashlight on the cooler and latched it shut",
        tags={"flashlight", "food"},
    ),
    "tie_flap": Response(
        id="tie_flap",
        label="tie the tent flap",
        sense=3,
        handles={"tent_flap"},
        inspect_line='held up a flashlight and said, "A windy old corner can bluff and bluster. We will tie what is loose and quiet the fluster."',
        success_line="The light caught the wobbling canvas, and a simple knot turned the racket into rest.",
        qa_text="used a flashlight to find the loose flap and tied it neatly",
        tags={"flashlight", "wind"},
    ),
    "shout_into_dark": Response(
        id="shout_into_dark",
        label="shout into the dark",
        sense=1,
        handles=set(),
        inspect_line='called into the dark without checking',
        success_line="That only made the campground feel louder.",
        qa_text="shouted into the dark",
        tags={"poor_choice"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "June", "Ivy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Owen", "Eli"]
TRAITS = ["careful", "curious", "gentle", "brave", "thoughtful", "cheery"]
COMFORTS = ["patchwork blanket", "small bear", "soft bunny", "striped pillow", ""]

KNOWLEDGE = {
    "owl": [(
        "Why do owls make sounds at night?",
        "Owls are awake at night, and they call to each other or hunt when it is dark. Their hoots can sound spooky until you know an owl is making them."
    )],
    "raccoon": [(
        "Why do raccoons visit campgrounds?",
        "Raccoons come to campgrounds because they smell food and want an easy snack. If coolers and food boxes are shut tight, raccoons are less likely to poke around."
    )],
    "tent": [(
        "Why can a tent flap make loud sounds?",
        "When wind pushes loose tent cloth, it can slap poles or snap in the air. Tying the flap snug helps the tent stay quiet."
    )],
    "lantern": [(
        "What is a camping lantern for?",
        "A camping lantern gives soft light so people can see at night around a campsite. It helps campers look carefully instead of guessing in the dark."
    )],
    "flashlight": [(
        "Why is a flashlight useful at a campground?",
        "A flashlight shines a bright beam where you point it. That makes it easier to check a strange sound safely at night."
    )],
    "food": [(
        "Why should campers close their coolers?",
        "Closed coolers keep food cleaner and make fewer smells drift into the night. That helps keep animals from coming too close to camp."
    )],
    "wind": [(
        "What does wind do to loose things?",
        "Wind can make loose cloth flap and loose lids rattle. A simple knot or a closed latch can make the noise stop."
    )],
}
KNOWLEDGE_ORDER = ["owl", "raccoon", "tent", "lantern", "flashlight", "food", "wind"]


def valid_combo(disturber_id: str, response_id: str) -> bool:
    if disturber_id not in DISTURBERS or response_id not in RESPONSES:
        return False
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return False
    return disturber_id in response.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for plan_id in PLANS:
        for disturber_id in DISTURBERS:
            for response_id in RESPONSES:
                if valid_combo(disturber_id, response_id):
                    combos.append((plan_id, disturber_id, response_id))
    return combos


def explain_rejection(disturber_id: str, response_id: str) -> str:
    if response_id not in RESPONSES:
        return "(No story: unknown response.)"
    if disturber_id not in DISTURBERS:
        return "(No story: unknown disturber.)"
    response = RESPONSES[response_id]
    disturber = DISTURBERS[disturber_id]
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Choose a calm, checking response instead.)"
        )
    return (
        f"(No story: '{response.label}' does not sensibly solve the sound from the "
        f"{disturber.label}. Pick a response that actually fits the cause.)"
    )


def predict_fear(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    total_fear = sum(k.memes["fear"] for k in sim.kids())
    return {"fear": total_fear, "dark": sim.get("site").meters["dark"]}


def introduce(world: World, a: Entity, b: Entity, helper: Entity, plan: EveningPlan) -> None:
    world.say(
        f"{plan.opening} {a.id} and {b.id} sat close while {helper.label_word} smiled hello."
    )
    world.say(
        f"{plan.prop_line} {plan.closing}"
    )


def play_line(world: World, a: Entity, b: Entity, trait: str, comfort: str) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    comfort_line = ""
    if comfort:
        comfort_line = f" {b.id} hugged a {comfort} tight,"
    world.say(
        f'"Camp night is bright," sang {a.id}. "Till the stars take flight!" '
        f'"And I will count them left and right," laughed {b.id}.{comfort_line}'
    )
    if trait in {"curious", "thoughtful"}:
        world.say(f"They liked to ask what every rustle meant, and where each night-time whisper went.")


def darken(world: World) -> None:
    site = world.get("site")
    site.meters["dark"] += 1
    world.say("Then the fire burned low with a soft red wink, and shadows grew long at the campground brink.")


def strange_sound(world: World, disturber: Disturber) -> None:
    source = world.get("source")
    source.meters["noise"] += 1
    world.get("site").meters["disturbance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Suddenly: "{disturber.sound}" came skipping around. '
        f'The odd little noise hopped over the ground.'
    )


def fear_talk(world: World, a: Entity, b: Entity, disturber: Disturber) -> None:
    pred = predict_fear(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"Did something bewitch the campground tonight?" whispered {b.id}. '
        f'"That sound does not sound small or light."'
    )
    extra = ""
    if pred["fear"] >= 2:
        extra = f" {a.id} scooted closer, trying to look bold though the dark felt deep and cold."
    world.say(
        f'"Maybe {disturber.spooky_name} is rattling around," said {a.id}.{extra}'
    )


def inspect(world: World, helper: Entity, response: Response) -> None:
    helper.meters["light"] += 1
    world.say(f'{helper.label_word.capitalize()} {response.inspect_line}')
    propagate(world, narrate=False)
    world.say(response.success_line)


def reveal(world: World, disturber: Disturber) -> None:
    world.say(
        f"There in {disturber.location}, {disturber.reveal}."
    )


def fix(world: World, disturber: Disturber) -> None:
    source = world.get("source")
    source.meters["secured"] += 1
    propagate(world, narrate=False)
    world.say(disturber.fix)


def soothe(world: World, helper: Entity, a: Entity, b: Entity, disturber: Disturber) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f'"See?" said {helper.label_word}. "The night can surprise, but a careful look makes the truth rise."'
    )
    if disturber.animal:
        world.say(
            f'"So it was not magic?" asked {b.id}. '
            f'"Only a creature with night-time habit?"'
        )
    else:
        world.say(
            f'"So it was not magic?" asked {a.id}. '
            f'"Only the wind making cloth sound tragic?"'
        )


def ending(world: World, a: Entity, b: Entity, plan: EveningPlan, disturber: Disturber) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    if disturber.id == "owl_pine":
        world.say(
            f'Soon "{disturber.sound}" felt round and mild, and both campers listened, calm as a child. '
            f'They sat by the glow and counted the sky, while the owl stitched moon-song softly on high.'
        )
    elif disturber.id == "raccoon_cooler":
        world.say(
            "Soon the cooler was tidy, the campsite neat, and the night felt safe and small and sweet. "
            "They laughed at the clinking that had seemed grand, then shared their marshmallows hand in hand."
        )
    else:
        world.say(
            "Soon the tent stood quiet with hardly a flap, and the whole campground settled into a nap. "
            "The children breathed slow, then smiled at the sight of a still little campsite tucked into night."
        )


def tell(
    plan: EveningPlan,
    disturber: Disturber,
    response: Response,
    child1: str,
    child1_gender: str,
    child2: str,
    child2_gender: str,
    helper_name: str,
    helper_type: str,
    trait: str,
    comfort: str,
) -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="child1", traits=[trait], label=child1))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="child2", traits=["sleepy"], label=child2, attrs={"comfort": comfort}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, role="helper", label=helper_name))
    world.add(Entity(id="site", kind="thing", type="campground", label="campground"))
    world.add(Entity(id="source", kind="thing", type=disturber.kind, label=disturber.label))

    world.facts["comfort"] = comfort
    world.facts["plan"] = plan
    world.facts["disturber_cfg"] = disturber
    world.facts["response_cfg"] = response

    introduce(world, a, b, helper, plan)
    play_line(world, a, b, trait, comfort)

    world.para()
    darken(world)
    strange_sound(world, disturber)
    fear_talk(world, a, b, disturber)

    world.para()
    inspect(world, helper, response)
    reveal(world, disturber)
    fix(world, disturber)
    soothe(world, helper, a, b, disturber)

    world.para()
    ending(world, a, b, plan, disturber)

    world.facts.update(
        child1=a,
        child2=b,
        helper=helper,
        source=world.get("source"),
        site=world.get("site"),
        fear_after_sound=sum(k.memes["fear"] for k in world.kids()),
        relieved=sum(k.memes["relief"] for k in world.kids()),
        secured=world.get("source").meters["secured"] >= THRESHOLD,
        revealed=world.get("source").meters["revealed"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    d = f["disturber_cfg"]
    r = f["response_cfg"]
    return [
        'Write a short rhyming campground story for a 3-to-5-year-old that uses the word "bewitch," includes dialogue, and includes sound effects.',
        f"Tell a rhyming story where {a.id} and {b.id} hear '{d.sound}' at a campground and wonder if something might bewitch the night, but a grown-up checks calmly and solves it.",
        f"Write a gentle rhyme with quoted speech and sound effects in which a strange campground noise comes from a {d.label}, and the helper {r.qa_text}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    helper = f["helper"]
    d = f["disturber_cfg"]
    r = f["response_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id} at a campground, with a calm {helper.label_word} nearby. They start the evening happy, then grow nervous when a strange sound jumps through the dark."
        ),
        (
            "Why did the children think something might bewitch the campground?",
            f"They heard '{d.sound}' in the dark before they knew what was making it. The night felt bigger and stranger because the sound came first and the answer came later."
        ),
        (
            f"What was really making the sound?",
            f"It was {d.reveal}. Once the helper shone a light and looked carefully, the mystery stopped feeling like magic."
        ),
        (
            f"How did the {helper.label_word} help?",
            f"The {helper.label_word} {r.qa_text}. That worked because the helper checked the real cause instead of guessing at the dark."
        ),
        (
            "How did the story end?",
            f"The children felt relieved and brave again, and the campground felt gentle instead of spooky. The ending image shows that nothing had to bewitch the night once the truth was plainly seen."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    d = world.facts["disturber_cfg"]
    r = world.facts["response_cfg"]
    tags |= set(d.tags)
    tags |= set(r.tags)
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        plan="marshmallows",
        disturber="raccoon_cooler",
        response="latch_cooler",
        child1="Lily",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        helper="Ranger May",
        helper_type="ranger_f",
        trait="curious",
        comfort="patchwork blanket",
    ),
    StoryParams(
        plan="stargazing",
        disturber="owl_pine",
        response="lantern_peek",
        child1="Sam",
        child1_gender="boy",
        child2="Ivy",
        child2_gender="girl",
        helper="Dad",
        helper_type="father",
        trait="thoughtful",
        comfort="small bear",
    ),
    StoryParams(
        plan="songtime",
        disturber="tent_flap",
        response="tie_flap",
        child1="Mia",
        child1_gender="girl",
        child2="Tom",
        child2_gender="boy",
        helper="Mom",
        helper_type="mother",
        trait="cheery",
        comfort="",
    ),
]


ASP_RULES = r"""
valid(P,D,R) :- plan(P), disturber(D), response(R), sense(R,S), sense_min(M), S >= M, handles(R,D).
calm(D,R) :- valid(_,D,R).

#show valid/3.
#show calm/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    for disturber_id in DISTURBERS:
        lines.append(asp.fact("disturber", disturber_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for handle in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, handle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("missing QA or prompts in smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming campground storyworld with dialogue, sound effects, and a bewitching night mystery."
    )
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--disturber", choices=DISTURBERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["mother", "father", "ranger_f", "ranger_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def helper_name_and_type(helper_key: str) -> tuple[str, str]:
    mapping = {
        "mother": ("Mom", "mother"),
        "father": ("Dad", "father"),
        "ranger_f": ("Ranger May", "ranger_f"),
        "ranger_m": ("Ranger Jay", "ranger_m"),
    }
    return mapping[helper_key]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.disturber and args.response and not valid_combo(args.disturber, args.response):
        raise StoryError(explain_rejection(args.disturber, args.response))
    if args.response and args.response in RESPONSES and RESPONSES[args.response].sense < SENSE_MIN:
        chosen_disturber = args.disturber or next(iter(DISTURBERS))
        raise StoryError(explain_rejection(chosen_disturber, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.plan is None or combo[0] == args.plan)
        and (args.disturber is None or combo[1] == args.disturber)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plan_id, disturber_id, response_id = rng.choice(sorted(combos))
    child1, child1_gender = pick_child(rng)
    child2, child2_gender = pick_child(rng, avoid=child1)
    helper_key = args.helper or rng.choice(["mother", "father", "ranger_f", "ranger_m"])
    helper_name, helper_type = helper_name_and_type(helper_key)
    trait = rng.choice(TRAITS)
    comfort = rng.choice(COMFORTS)
    return StoryParams(
        plan=plan_id,
        disturber=disturber_id,
        response=response_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        helper=helper_name,
        helper_type=helper_type,
        trait=trait,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    if params.plan not in PLANS:
        raise StoryError(f"(No story: unknown plan '{params.plan}'.)")
    if params.disturber not in DISTURBERS:
        raise StoryError(f"(No story: unknown disturber '{params.disturber}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if not valid_combo(params.disturber, params.response):
        raise StoryError(explain_rejection(params.disturber, params.response))

    world = tell(
        plan=PLANS[params.plan],
        disturber=DISTURBERS[params.disturber],
        response=RESPONSES[params.response],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
        trait=params.trait,
        comfort=params.comfort,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (plan, disturber, response) combos:\n")
        for plan_id, disturber_id, response_id in combos:
            print(f"  {plan_id:12} {disturber_id:16} {response_id}")
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
            header = f"### {p.child1} & {p.child2}: {p.disturber} with {p.response} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
