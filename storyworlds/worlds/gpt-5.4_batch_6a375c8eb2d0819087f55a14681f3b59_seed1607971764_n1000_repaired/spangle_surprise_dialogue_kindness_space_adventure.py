#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py
================================================================================

A standalone story world for a tiny "space adventure rescue" domain.

Two children turn an ordinary room or yard into a spaceship. In the middle of
their pretend mission, they discover a surprising little stowaway. One child
first wants to solve the problem quickly, but the kinder plan is to notice what
the creature actually needs. When they choose the matching gentle helper, the
"rescue mission" works and the ending image proves that the children changed:
their adventure grows bigger because they made room for kindness.

Run it
------
    python storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py
    python storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py --theme rocket_den --creature moth
    python storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py --helper net
    python storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/spangle_surprise_dialogue_kindness_space_adventure.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    mission: str
    nook: str
    sendoff: str
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
class Creature:
    id: str
    label: str
    reveal: str
    sound: str
    needs: set[str]
    move_text: str
    farewell: str
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
class Helper:
    id: str
    label: str
    phrase: str
    sense: int
    provides: set[str]
    plan_text: str
    success_text: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "heard_sound": False,
            "surprise_revealed": False,
            "kind_plan": False,
            "rescued": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"eager", "kind"}]

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


def _r_surprise_fear(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["noticed"] < THRESHOLD or creature.meters["safe"] >= THRESHOLD:
        return []
    sig = ("surprise_fear", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
        kid.memes["wonder"] += 1
    return []


def _r_guided_safe(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["guided"] < THRESHOLD:
        return []
    sig = ("guided_safe", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["safe"] += 1
    creature.meters["trapped"] = 0.0
    creature.memes["fear"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="surprise_fear", tag="emotional", apply=_r_surprise_fear),
    Rule(name="guided_safe", tag="physical", apply=_r_guided_safe),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def helper_fits(creature: Creature, helper: Helper) -> bool:
    return creature.needs.issubset(helper.provides)


def kind_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for creature_id, creature in CREATURES.items():
            for helper_id, helper in HELPERS.items():
                if helper.sense >= SENSE_MIN and helper_fits(creature, helper):
                    combos.append((theme_id, creature_id, helper_id))
    return combos


def explain_helper_rejection(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in kind_helpers()))
    return (
        f"(Refusing helper '{helper_id}': it is too grabby for this world "
        f"(sense={helper.sense} < {SENSE_MIN}). This story prefers gentle, kind "
        f"rescue plans. Try one of: {better}.)"
    )


def explain_combo_rejection(creature: Creature, helper: Helper) -> str:
    missing = sorted(creature.needs - helper.provides)
    return (
        f"(No story: {helper.label} does not meet what the {creature.label} needs. "
        f"It is missing {missing}, so the rescue would not be gentle or plausible.)"
    )


def predict_rescue(world: World, helper: Helper) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    creature.meters["guided"] += 1 if helper_fits(CREATURES[sim.facts["creature_cfg"].id], helper) else 0
    propagate(sim, narrate=False)
    return {
        "safe": creature.meters["safe"] >= THRESHOLD,
        "fear": creature.memes["fear"],
    }


def play_setup(world: World, eager: Entity, kind: Entity, theme: Theme) -> None:
    for kid in (eager, kind):
        kid.memes["joy"] += 1
    world.say(
        f"After supper, {eager.id} and {kind.id} turned the room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"Captain {eager.id}," {kind.id} said, saluting with a grin, '
        f'"our mission is {theme.mission}."'
    )
    world.say(
        f"{eager.id} tucked a tiny silver spangle into a paper cup and called it "
        f"the mission star."
    )


def hear_sound(world: World, eager: Entity, kind: Entity, theme: Theme, creature_cfg: Creature) -> None:
    world.facts["heard_sound"] = True
    world.say(
        f"Just as they crawled toward {theme.nook}, a soft {creature_cfg.sound} came from the dark."
    )
    world.say(
        f'"Did the ship just answer us?" {eager.id} whispered. '
        f'{kind.id} held still and listened again.'
    )


def discover_surprise(world: World, eager: Entity, kind: Entity, creature: Entity, creature_cfg: Creature) -> None:
    creature.meters["noticed"] += 1
    world.facts["surprise_revealed"] = True
    propagate(world, narrate=False)
    world.say(
        f"They peeped inside and found {creature_cfg.reveal}. It was not a blinking machine at all."
    )
    world.say(
        f'"Oh!" said {kind.id}. "It is only {creature.label}, and it looks scared."'
    )


def quick_idea(world: World, eager: Entity, helper: Helper) -> None:
    eager.memes["hurry"] += 1
    world.say(
        f'"I can fix this fast," said {eager.id}. "{helper.plan_text}"'
    )


def kind_turn(world: World, eager: Entity, kind: Entity, creature_cfg: Creature, helper: Helper) -> None:
    kind.memes["kindness"] += 1
    eager.memes["patience"] += 1
    world.facts["kind_plan"] = True
    pred = predict_rescue(world, helper)
    world.facts["predicted_safe"] = pred["safe"]
    world.say(
        f'{kind.id} shook {kind.pronoun("possessive")} head. '
        f'"Let us be gentle. The {creature_cfg.label} is telling us what it needs."'
    )
    world.say(
        f'{kind.id} pointed to {helper.phrase} and said, "{helper.plan_text}. '
        f'If we stay quiet, it can choose the safe way by itself."'
    )


def rescue(world: World, eager: Entity, kind: Entity, creature: Entity,
           creature_cfg: Creature, helper: Helper, theme: Theme) -> None:
    creature.meters["guided"] += 1
    propagate(world, narrate=False)
    world.facts["rescued"] = True
    world.facts["ending_image"] = creature_cfg.farewell
    world.say(helper.success_text.format(creature=creature_cfg.label))
    world.say(
        f"Soon {creature_cfg.move_text}, and both children let out the breath they had been holding."
    )
    world.say(
        f'"Rescue mission complete," {eager.id} said softly. "{theme.sendoff}"'
    )


def close_story(world: World, eager: Entity, kind: Entity, creature_cfg: Creature) -> None:
    eager.memes["kindness"] += 1
    kind.memes["joy"] += 1
    world.say(
        f'Then {kind.id} smiled and said, "The bravest space captains are kind ones."'
    )
    world.say(
        f"They set the little cup with the silver spangle on the windowsill like a tiny star medal, "
        f"and watched {creature_cfg.farewell}."
    )


def tell(theme: Theme, creature_cfg: Creature, helper: Helper,
         eager_name: str = "Tao", eager_gender: str = "boy",
         kind_name: str = "Mina", kind_gender: str = "girl") -> World:
    world = World()
    eager = world.add(Entity(id=eager_name, kind="character", type=eager_gender, role="eager"))
    kind = world.add(Entity(id=kind_name, kind="character", type=kind_gender, role="kind"))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="animal",
        label=f"the {creature_cfg.label}",
        role="stowaway",
        tags=set(creature_cfg.tags),
    ))
    creature.meters["trapped"] = 1.0
    creature.meters["noticed"] = 0.0
    creature.meters["guided"] = 0.0
    creature.meters["safe"] = 0.0
    creature.memes["fear"] = 0.0
    eager.memes["joy"] = 0.0
    kind.memes["joy"] = 0.0

    world.facts.update(
        theme=theme,
        creature_cfg=creature_cfg,
        helper=helper,
        eager=eager,
        kind=kind,
        creature=creature,
    )

    play_setup(world, eager, kind, theme)
    hear_sound(world, eager, kind, theme, creature_cfg)

    world.para()
    discover_surprise(world, eager, kind, creature, creature_cfg)
    quick_idea(world, eager, helper)
    kind_turn(world, eager, kind, creature_cfg, helper)

    world.para()
    rescue(world, eager, kind, creature, creature_cfg, helper, theme)
    close_story(world, eager, kind, creature_cfg)
    return world


THEMES = {
    "rocket_den": Theme(
        id="rocket_den",
        scene="a rocket den bound for the far side of the moon",
        rig="A blanket over two chairs became the cockpit, couch cushions became moon rocks, and a string of paper stars hung over the floor.",
        mission="to carry one bright star sample home",
        nook="the cargo tunnel under the blanket",
        sendoff="Next time, we listen before we launch",
        tags={"space", "rocket"},
    ),
    "comet_lab": Theme(
        id="comet_lab",
        scene="a comet lab floating above a ringed planet",
        rig="A big cardboard box became the lab, a mixing bowl became the radar dish, and crayons marked glowing planets on scrap paper.",
        mission="to study a strange new shimmer",
        nook="the shadowy supply hatch behind the box",
        sendoff="Good crews make room for small travelers",
        tags={"space", "planet"},
    ),
    "star_porch": Theme(
        id="star_porch",
        scene="a porch station looking out over a pretend galaxy garden",
        rig="The porch steps became launch decks, flowerpots became red planets, and a broom handle wore a paper flag like a mast.",
        mission="to map the quiet corners of the galaxy",
        nook="the little landing bay beside the plant stand",
        sendoff="Even surprise visitors deserve a gentle welcome",
        tags={"space", "porch"},
    ),
}

CREATURES = {
    "moth": Creature(
        id="moth",
        label="moth",
        reveal="a dusty little moth clinging to the fabric like a folded moon map",
        sound="flutter-flutter",
        needs={"light", "exit"},
        move_text="the moth followed the kind light and slipped out into the evening air",
        farewell="the moth spin once past the window, pale as a moon petal",
        tags={"moth", "light", "window"},
    ),
    "mouse": Creature(
        id="mouse",
        label="mouse",
        reveal="a tiny gray mouse with bright bead eyes tucked behind a box flap",
        sound="scritch-scritch",
        needs={"food", "box"},
        move_text="the mouse scampered into the little box, nibbled a crumb, and rode outside without panic",
        farewell="the mouse dart into the ivy and vanish like a quick comet",
        tags={"mouse", "garden", "box"},
    ),
    "gecko": Creature(
        id="gecko",
        label="gecko",
        reveal="a small green gecko pressed against the cool wall, still as a painted star",
        sound="tiny tap-tap",
        needs={"warm", "perch"},
        move_text="the gecko stepped onto the warm mitten and blinked until it was set on a sunny pot",
        farewell="the gecko lift its head on the warm pot like a little green captain",
        tags={"gecko", "warmth", "perch"},
    ),
}

HELPERS = {
    "lamp_path": Helper(
        id="lamp_path",
        label="lamp path",
        phrase="the flashlight with the low beam and the open window",
        sense=3,
        provides={"light", "exit"},
        plan_text="We can turn off the big room light, open the window, and make a small path of light",
        success_text="They dimmed the room, opened the window wide, and painted a soft path with the flashlight beam for the {creature}.",
        qa_text="They used a soft path of light to guide it to the open window.",
        tags={"flashlight", "window", "kindness"},
    ),
    "snack_box": Helper(
        id="snack_box",
        label="snack box",
        phrase="a cracker crumb and a shoebox turned on its side",
        sense=3,
        provides={"food", "box"},
        plan_text="Let us leave one crumb by the box and wait very still",
        success_text="They set down the little shoebox, left a cracker crumb at the edge, and waited without making any sudden noise for the {creature}.",
        qa_text="They used a crumb and a small box so it could walk into safety by itself.",
        tags={"box", "food", "kindness"},
    ),
    "warm_mitten": Helper(
        id="warm_mitten",
        label="warm mitten",
        phrase="a soft mitten warmed between their hands",
        sense=3,
        provides={"warm", "perch"},
        plan_text="We can warm the mitten first and hold it out like a tiny landing pad",
        success_text="They warmed the mitten, held it close like a quiet landing pad, and gave the {creature} time to step onto it.",
        qa_text="They offered a warm, soft place to stand and moved slowly.",
        tags={"warmth", "mitten", "kindness"},
    ),
    "net": Helper(
        id="net",
        label="toy net",
        phrase="the toy net from the dress-up basket",
        sense=1,
        provides={"grab"},
        plan_text="I can swoop the toy net over it before it runs",
        success_text="",
        qa_text="",
        tags={"grab"},
    ),
    "broom_shoo": Helper(
        id="broom_shoo",
        label="broom",
        phrase="the broom by the door",
        sense=1,
        provides={"push"},
        plan_text="I can shoo it out with the broom",
        success_text="",
        qa_text="",
        tags={"push"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Ava", "Nora", "Zoe", "Ivy", "Sana", "Ella"]
BOY_NAMES = ["Tao", "Leo", "Ben", "Milo", "Noah", "Finn", "Eli", "Max"]


@dataclass
class StoryParams:
    theme: str
    creature: str
    helper: str
    eager_name: str
    eager_gender: str
    kind_name: str
    kind_gender: str
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
    "moth": [(
        "Why might a moth move toward a light?",
        "Many moths notice light and fly toward it. A gentle light can help guide one toward an open way out."
    )],
    "mouse": [(
        "Why is it kinder to stay still around a mouse?",
        "A mouse is a small prey animal, so sudden movement can scare it badly. Staying quiet helps it choose a safe path instead of panicking."
    )],
    "gecko": [(
        "Why might a cold gecko like a warm place to stand?",
        "A gecko is a little reptile, and warm surfaces help it feel comfortable enough to move. A warm perch can calm it without hurting it."
    )],
    "flashlight": [(
        "What is a flashlight good for?",
        "A flashlight helps you see in the dark without fire. A soft beam can also show a safe path."
    )],
    "box": [(
        "Why is a small box useful in a gentle animal rescue?",
        "A small box gives a tiny animal a clear space to step into. It is calmer than chasing with hands."
    )],
    "warmth": [(
        "Why can warmth help a small cold creature?",
        "Warmth can help a little creature feel safe enough to move. Gentle warmth is comforting when the air or surface is chilly."
    )],
    "window": [(
        "Why open a window for a flying bug indoors?",
        "An open window gives the bug a way back outside. Then it does not have to stay trapped in the room."
    )],
    "kindness": [(
        "What does kindness mean when you help a small creature?",
        "Kindness means noticing what the creature needs and helping without grabbing or scaring it. You use gentle actions so it can be safe."
    )],
}
KNOWLEDGE_ORDER = ["kindness", "moth", "mouse", "gecko", "flashlight", "box", "warmth", "window"]


def generation_prompts(world: World) -> list[str]:
    theme = world.facts["theme"]
    creature_cfg = world.facts["creature_cfg"]
    eager = world.facts["eager"]
    kind = world.facts["kind"]
    helper = world.facts["helper"]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the word "spangle" and a surprise rescue.',
        f"Tell a gentle story where {eager.id} and {kind.id} are pretending to explore space, discover a {creature_cfg.label}, and solve the problem with kindness and dialogue.",
        f"Write a tiny mission story set in {theme.scene} where the children stop hurrying, use {helper.label}, and end by helping a small stowaway safely."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    eager = world.facts["eager"]
    kind = world.facts["kind"]
    creature_cfg = world.facts["creature_cfg"]
    helper = world.facts["helper"]
    theme = world.facts["theme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {eager.id} and {kind.id}, two children playing a space adventure together. In the middle of their game, they discover a surprising little {creature_cfg.label}."
        ),
        (
            "What surprise did the children find?",
            f"They expected a spaceship sound in {theme.nook}, but instead they found {creature_cfg.reveal}. That surprise changed their pretend mission into a real rescue."
        ),
        (
            f"Why did {kind.id} ask {eager.id} to be gentle?",
            f"{kind.id} could see the {creature_cfg.label} was scared, not naughty. Being gentle mattered because a frightened little creature needs help that feels safe."
        ),
        (
            f"How did the children help the {creature_cfg.label}?",
            f"{helper.qa_text} They stayed quiet and let the {creature_cfg.label} move in its own time."
        ),
        (
            "How did the story end?",
            f"The creature got to safety, and the children understood that kindness can be part of an adventure. They even left the silver spangle behind like a tiny star medal to remember the rescue."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    creature_cfg = world.facts["creature_cfg"]
    helper = world.facts["helper"]
    tags = {"kindness"} | set(creature_cfg.tags) | set(helper.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
kind_helper(H) :- helper(H), sense(H,S), sense_min(M), S >= M.
missing_need(C,H) :- needs(C,N), not provides(H,N).
valid(T,C,H) :- theme(T), creature(C), kind_helper(H), not missing_need(C,H).

outcome(rescued) :- chosen_creature(C), chosen_helper(H), kind_helper(H), not missing_need(C,H).
outcome(stuck)   :- chosen_creature(C), chosen_helper(H), not outcome(rescued), creature(C), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        for need in sorted(creature.needs):
            lines.append(asp.fact("needs", creature_id, need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        for item in sorted(helper.provides):
            lines.append(asp.fact("provides", helper_id, item))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_helpers() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show kind_helper/1."))
    return sorted(h for (h,) in asp.atoms(model, "kind_helper"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_creature", params.creature),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.creature not in CREATURES or params.helper not in HELPERS:
        return "?"
    helper = HELPERS[params.helper]
    creature = CREATURES[params.creature]
    return "rescued" if helper.sense >= SENSE_MIN and helper_fits(creature, helper) else "stuck"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure rescue stories with surprise, dialogue, and kindness."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper_rejection(args.helper))
    if args.creature and args.helper:
        creature = CREATURES[args.creature]
        helper = HELPERS[args.helper]
        if helper.sense >= SENSE_MIN and not helper_fits(creature, helper):
            raise StoryError(explain_combo_rejection(creature, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.creature is None or combo[1] == args.creature)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, creature_id, helper_id = rng.choice(sorted(combos))
    eager_name, eager_gender = pick_child(rng)
    kind_name, kind_gender = pick_child(rng, avoid=eager_name)
    return StoryParams(
        theme=theme_id,
        creature=creature_id,
        helper=helper_id,
        eager_name=eager_name,
        eager_gender=eager_gender,
        kind_name=kind_name,
        kind_gender=kind_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    helper = HELPERS[params.helper]
    creature_cfg = CREATURES[params.creature]
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper_rejection(params.helper))
    if not helper_fits(creature_cfg, helper):
        raise StoryError(explain_combo_rejection(creature_cfg, helper))

    world = tell(
        theme=THEMES[params.theme],
        creature_cfg=creature_cfg,
        helper=helper,
        eager_name=params.eager_name,
        eager_gender=params.eager_gender,
        kind_name=params.kind_name,
        kind_gender=params.kind_gender,
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


CURATED = [
    StoryParams(
        theme="rocket_den",
        creature="moth",
        helper="lamp_path",
        eager_name="Tao",
        eager_gender="boy",
        kind_name="Mina",
        kind_gender="girl",
    ),
    StoryParams(
        theme="comet_lab",
        creature="mouse",
        helper="snack_box",
        eager_name="Ava",
        eager_gender="girl",
        kind_name="Ben",
        kind_gender="boy",
    ),
    StoryParams(
        theme="star_porch",
        creature="gecko",
        helper="warm_mitten",
        eager_name="Leo",
        eager_gender="boy",
        kind_name="Nora",
        kind_gender="girl",
    ),
]


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid combo gate matches ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_kind = set(asp_kind_helpers())
    python_kind = {h.id for h in kind_helpers()}
    if clingo_kind == python_kind:
        print(f"OK: kind helpers match ({sorted(clingo_kind)}).")
    else:
        rc = 1
        print(f"MISMATCH in kind helpers: clingo={sorted(clingo_kind)} python={sorted(python_kind)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed on seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show kind_helper/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        helpers = ", ".join(asp_kind_helpers())
        print(f"kind helpers: {helpers}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (theme, creature, helper) combos:\n")
        for theme, creature, helper in combos:
            print(f"  {theme:11} {creature:7} {helper}")
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
            header = f"### {p.eager_name} & {p.kind_name}: {p.creature} with {p.helper} at {p.theme}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
