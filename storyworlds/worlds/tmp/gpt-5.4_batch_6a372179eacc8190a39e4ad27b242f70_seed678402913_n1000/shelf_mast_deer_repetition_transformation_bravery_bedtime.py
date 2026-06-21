#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shelf_mast_deer_repetition_transformation_bravery_bedtime.py
========================================================================================

A standalone bedtime-story world about a child who sees a worrying shadow in a
bedroom. On a high shelf sit a toy boat with a tall mast and a little wooden
deer. In dim light, those shapes can combine into a frightening shadow. The
story's tension comes from bedtime fear; the turn comes from a brave, reasonable
choice; the transformation comes when the shadow is understood and changed.

Core domain
-----------
A child is trying to fall asleep. A shelf holds a toy sailboat and a deer
figure. Depending on the light and where the toys sit, the wall shadow can look
gentle or scary. The child may freeze, call a parent, or walk over to look
closely. If the child or parent adjusts the objects or turns on a softer light,
the shadow transforms from something alarming into something friendly.

This world emphasizes:
- Repetition: recurring bedtime refrain and repeated brave steps.
- Transformation: the same objects making a different shadow after a change.
- Bravery: the child chooses a sensible action instead of hiding forever.

Run it
------
    python storyworlds/worlds/gpt-5.4/shelf_mast_deer_repetition_transformation_bravery_bedtime.py
    python storyworlds/worlds/gpt-5.4/shelf_mast_deer_repetition_transformation_bravery_bedtime.py --light moon --layout crossed
    python storyworlds/worlds/gpt-5.4/shelf_mast_deer_repetition_transformation_bravery_bedtime.py --act hide
    python storyworlds/worlds/gpt-5.4/shelf_mast_deer_repetition_transformation_bravery_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/shelf_mast_deer_repetition_transformation_bravery_bedtime.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to the path from this nested world folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
COURAGE_MIN = 2


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


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    strength: int
    warmth: str
    bedtime: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Layout:
    id: str
    boat_place: str
    deer_place: str
    shadow_shape: str
    scary: bool
    transform_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BraveAct:
    id: str
    label: str
    courage: int
    parent_help: bool
    changes_shadow: bool
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


def _r_shadow_fear(world: World) -> list[str]:
    child = world.get("child")
    wall = world.get("wall")
    if wall.meters["shadow_scary"] < THRESHOLD:
        return []
    sig = ("shadow_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return ["__fear__"]


def _r_brave_settle(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["courage"] < THRESHOLD or world.get("wall").meters["shadow_gentle"] < THRESHOLD:
        return []
    sig = ("brave_settle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] += 1
    child.memes["fear"] = 0.0
    return ["__calm__"]


CAUSAL_RULES = [
    Rule(name="shadow_fear", tag="emotional", apply=_r_shadow_fear),
    Rule(name="brave_settle", tag="emotional", apply=_r_brave_settle),
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


LIGHTS = {
    "moon": Light(
        id="moon",
        label="moonlight",
        phrase="a pale stripe of moonlight from the window",
        strength=1,
        warmth="silver",
        bedtime=True,
        tags={"moon", "shadow"},
    ),
    "hall": Light(
        id="hall",
        label="hall light",
        phrase="a thin line of hall light under the door",
        strength=1,
        warmth="soft yellow",
        bedtime=True,
        tags={"light", "shadow"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="a small night-light glowing by the bed",
        strength=2,
        warmth="warm gold",
        bedtime=True,
        tags={"nightlight", "light"},
    ),
}

LAYOUTS = {
    "crossed": Layout(
        id="crossed",
        boat_place="near the edge of the shelf",
        deer_place="just behind the mast",
        shadow_shape="a tall antlered giant",
        scary=True,
        transform_to="a neat boat and a tiny deer standing apart",
        tags={"shelf", "mast", "deer", "shadow"},
    ),
    "beside": Layout(
        id="beside",
        boat_place="in the middle of the shelf",
        deer_place="beside the boat",
        shadow_shape="a long crooked deer with a sail for a back",
        scary=True,
        transform_to="a little boat and deer facing the moonlight",
        tags={"shelf", "mast", "deer", "shadow"},
    ),
    "calm": Layout(
        id="calm",
        boat_place="flat against the books on the shelf",
        deer_place="sleeping beside a storybook",
        shadow_shape="a small, ordinary bedtime shadow",
        scary=False,
        transform_to="a small, ordinary bedtime shadow",
        tags={"shelf", "mast", "deer", "shadow"},
    ),
}

ACTS = {
    "look": BraveAct(
        id="look",
        label="walk over and look closely",
        courage=3,
        parent_help=False,
        changes_shadow=True,
        tags={"bravery", "look"},
    ),
    "call": BraveAct(
        id="call",
        label="call for a parent and point at the wall",
        courage=2,
        parent_help=True,
        changes_shadow=True,
        tags={"bravery", "help"},
    ),
    "hide": BraveAct(
        id="hide",
        label="pull the blanket over the face and wait",
        courage=0,
        parent_help=False,
        changes_shadow=False,
        tags={"hiding"},
    ),
}

CHILD_NAMES = ["Mina", "Nora", "Luca", "Eli", "Tara", "June", "Owen", "Ivy", "Theo", "Maya"]
TRAITS = ["sleepy", "gentle", "thoughtful", "quiet", "careful", "small"]


def valid_combo(light: Light, layout: Layout, act: BraveAct) -> bool:
    if not layout.scary:
        return act.id in {"look", "call"}
    if act.courage < COURAGE_MIN:
        return False
    if not act.changes_shadow:
        return False
    if light.strength < 1:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for light_id, light in LIGHTS.items():
        for layout_id, layout in LAYOUTS.items():
            for act_id, act in ACTS.items():
                if valid_combo(light, layout, act):
                    out.append((light_id, layout_id, act_id))
    return out


@dataclass
class StoryParams:
    light: str
    layout: str
    act: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def set_shadow(world: World, layout: Layout, light: Light) -> None:
    wall = world.get("wall")
    wall.meters["shadow_scary"] = 1.0 if layout.scary and light.strength >= 1 else 0.0
    wall.meters["shadow_gentle"] = 0.0 if wall.meters["shadow_scary"] >= THRESHOLD else 1.0
    propagate(world, narrate=False)


def transformed_shape(layout: Layout, act: BraveAct) -> str:
    if act.parent_help:
        return "two clear little shadows, one for the boat and one for the deer"
    return layout.transform_to


def introduction(world: World, child: Entity, parent: Entity, light: Light, layout: Layout) -> None:
    shelf = world.get("shelf")
    boat = world.get("boat")
    deer = world.get("deer")
    world.say(
        f"It was bedtime, and {child.id}'s room had gone very quiet. "
        f"Only {light.phrase} lay across the wall."
    )
    world.say(
        f"On the {shelf.label}, a toy boat rested {layout.boat_place}. "
        f"Its slim mast reached up beside a little wooden deer {layout.deer_place}."
    )
    world.say(
        f"{child.id} tucked under the blanket while {child.pronoun('possessive')} "
        f"{parent.label_word} smoothed the covers and whispered good night."
    )
    boat.memes["noticed"] += 1
    deer.memes["noticed"] += 1


def repetition_beat(world: World, child: Entity, layout: Layout) -> None:
    world.say(
        f"{child.id} looked once at the shelf, once at the wall, and once at the door. "
        f"The shelf was still. The mast was still. The deer was still."
    )
    if layout.scary:
        world.say(
            f"But the shadow was not still inside {child.pronoun('possessive')} thoughts. "
            f"It looked like {layout.shadow_shape}, and that made the room feel larger and darker."
        )
    else:
        world.say(
            f"The shadow stayed small and plain, and the room felt ready for sleep."
        )


def fear_beat(world: World, child: Entity, layout: Layout) -> None:
    if world.get("wall").meters["shadow_scary"] >= THRESHOLD:
        child.memes["worry"] += 1
        world.say(
            f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin. "
            f"The tall shape on the wall did not move, yet it seemed to be watching."
        )


def brave_choice(world: World, child: Entity, parent: Entity, act: BraveAct) -> None:
    if act.id == "look":
        child.memes["courage"] += 1
        world.say(
            f"{child.id} took one deep breath, then another, then one more. "
            f'"I can look," {child.pronoun()} whispered, and slid carefully out of bed.'
        )
    elif act.id == "call":
        child.memes["courage"] += 1
        world.say(
            f"{child.id} took one deep breath, then another, then one more. "
            f'Then {child.pronoun()} called softly, "{parent.label_word.capitalize()}, will you come see?"'
        )


def inspect_and_transform(world: World, child: Entity, parent: Entity, light: Light, layout: Layout, act: BraveAct) -> None:
    wall = world.get("wall")
    boat = world.get("boat")
    deer = world.get("deer")
    shelf = world.get("shelf")

    if act.id == "look":
        world.say(
            f"Step by step, {child.id} went closer to the {shelf.label}. "
            f"The nearer {child.pronoun()} came, the clearer the shapes became."
        )
        world.say(
            f"{child.pronoun().capitalize()} saw the truth at last: the giant on the wall was only "
            f"the boat's mast crossing the deer's antlers."
        )
        boat.meters["moved"] += 1
        deer.meters["moved"] += 1
        wall.meters["shadow_scary"] = 0.0
        wall.meters["shadow_gentle"] = 1.0
        world.say(
            f"{child.id} turned the little boat a little and nudged the deer a little. "
            f"At once the shadow changed into {transformed_shape(layout, act)}."
        )
    elif act.id == "call":
        parent.memes["care"] += 1
        child.memes["help_trust"] += 1
        world.say(
            f"{parent.label_word.capitalize()} came back, sat on the bed, and looked where {child.id} pointed."
        )
        world.say(
            f'"Let us see what the shadow is made of," {parent.pronoun()} said. '
            f'Together they looked at the shelf, then the wall, then the shelf again.'
        )
        boat.meters["moved"] += 1
        deer.meters["moved"] += 1
        wall.meters["shadow_scary"] = 0.0
        wall.meters["shadow_gentle"] = 1.0
        world.say(
            f"{parent.label_word.capitalize()} moved the boat with its mast a finger-width to one side "
            f"and set the deer beside a book. The huge shape broke apart into {transformed_shape(layout, act)}."
        )
    propagate(world, narrate=False)


def calm_resolution(world: World, child: Entity, parent: Entity, light: Light, layout: Layout, act: BraveAct) -> None:
    propagate(world, narrate=False)
    child.memes["sleepy"] += 1
    child.memes["brave_memory"] += 1
    gentle = transformed_shape(layout, act)
    if act.parent_help:
        world.say(
            f"{child.id} looked once at the shelf, once at the wall, and once at {child.pronoun('possessive')} {parent.label_word}. "
            f"Now the shelf was still. The mast was still. The deer was still. And now the shadow was gentle too."
        )
    else:
        world.say(
            f"{child.id} looked once at the shelf, once at the wall, and once at the bed. "
            f"Now the shelf was still. The mast was still. The deer was still. And the shadow had become gentle too."
        )
    world.say(
        f"{child.pronoun().capitalize()} climbed back under the blanket, feeling bigger inside than before. "
        f"Soon {light.warmth} light held only {gentle}, and {child.id}'s eyes grew heavy."
    )
    world.say(
        f"Before sleep came, {child.id} gave the little deer and the toy boat one last glance from the pillow. "
        f"They had not turned into monsters at all. They had turned into ordinary room-things again, and that was the best magic of all."
    )


def gentle_resolution(world: World, child: Entity, light: Light) -> None:
    child.memes["courage"] += 1
    child.memes["calm"] += 1
    world.say(
        f"{child.id} listened to the quiet room and smiled a sleepy little smile. "
        f"There was nothing to fight tonight, only a shelf, a mast, a deer, and {light.warmth} light."
    )
    world.say(
        f"{child.pronoun().capitalize()} turned over, hugged the blanket, and drifted toward sleep."
    )


def tell(light: Light, layout: Layout, act: BraveAct, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, role="child", attrs={"name": name}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    shelf = world.add(Entity(id="shelf", type="furniture", label="shelf", phrase="the high shelf", tags={"shelf"}))
    boat = world.add(Entity(id="boat", type="toy_boat", label="toy boat", phrase="a toy sailboat", tags={"boat", "mast"}))
    deer = world.add(Entity(id="deer", type="deer", label="wooden deer", phrase="a little wooden deer", tags={"deer"}))
    wall = world.add(Entity(id="wall", type="wall", label="wall", phrase="the bedroom wall", tags={"shadow"}))
    child.id = name

    child.attrs["trait"] = trait
    child.memes["sleepiness"] = 1.0
    parent.memes["care"] = 1.0

    set_shadow(world, layout, light)

    introduction(world, child, parent, light, layout)
    repetition_beat(world, child, layout)

    if layout.scary:
        world.para()
        fear_beat(world, child, layout)
        brave_choice(world, child, parent, act)
        world.para()
        inspect_and_transform(world, child, parent, light, layout, act)
        world.para()
        calm_resolution(world, child, parent, light, layout, act)
        outcome = "transformed"
    else:
        world.para()
        gentle_resolution(world, child, light)
        outcome = "peaceful"

    world.facts.update(
        child=child,
        parent=parent,
        shelf=shelf,
        boat=boat,
        deer=deer,
        wall=wall,
        light=light,
        layout=layout,
        act=act,
        outcome=outcome,
        shadow_scary=layout.scary,
        parent_help=act.parent_help,
        transformed=world.get("wall").meters["shadow_gentle"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "shelf": [
        ("What is a shelf?",
         "A shelf is a flat board fixed to a wall or a piece of furniture where you can keep books or toys.")
    ],
    "mast": [
        ("What is a mast on a boat?",
         "A mast is the tall pole on a sailboat that holds the sail up. Even on a toy boat, it can make a long thin shape.")
    ],
    "deer": [
        ("What is a deer?",
         "A deer is a gentle animal with long legs, and some deer have antlers. From far away, antlers can make a shape look bigger.")
    ],
    "shadow": [
        ("What makes a shadow?",
         "A shadow happens when something blocks light. The shape can look different depending on where the light and object are.")
    ],
    "nightlight": [
        ("What is a night-light?",
         "A night-light is a small light that helps a room stay soft and visible at bedtime without being bright.")
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery means doing a wise thing even when you feel scared. It does not mean never feeling afraid.")
    ],
    "help": [
        ("Is asking for help brave?",
         "Yes. Asking a trusted grown-up for help is a brave and sensible choice when something feels scary or confusing.")
    ],
}
KNOWLEDGE_ORDER = ["shelf", "mast", "deer", "shadow", "nightlight", "bravery", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    light = f["light"]
    act = f["act"]
    if f["outcome"] == "peaceful":
        return [
            'Write a short bedtime story for a 3-to-5-year-old that includes the words "shelf," "mast," and "deer."',
            f"Tell a gentle bedtime story where {child.id} notices a shelf with a toy boat mast and a little deer, and the quiet room stays peaceful.",
            'Write a bedtime story with soft repetition and a calm ending, using ordinary bedroom objects in a reassuring way.',
        ]
    if act.parent_help:
        return [
            'Write a bedtime story for a 3-to-5-year-old that includes the words "shelf," "mast," and "deer," plus the themes of transformation and bravery.',
            f"Tell a story where {child.id} sees a scary shadow made by a toy boat mast and a deer on a shelf, then bravely asks a parent for help and the shadow changes.",
            'Write a child-facing bedtime story with repetition, a brave call for help, and a final calm image that makes the bedroom feel safe again.',
        ]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "shelf," "mast," and "deer," plus repetition, transformation, and bravery.',
        f"Tell a story where {child.id} thinks a shadow is scary, then bravely walks closer and discovers it is only a boat mast and a deer on a shelf.",
        'Write a bedtime story with a repeated line, a frightening shape that transforms into something harmless, and a cozy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    light = f["light"]
    layout = f["layout"]
    act = f["act"]
    pw = parent.label_word

    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} at bedtime, with {child.pronoun('possessive')} {pw} nearby and a toy boat and wooden deer on a shelf."
        ),
        (
            "What was on the shelf?",
            "There was a toy boat with a mast and a little wooden deer on the shelf. Those small objects were the real things making the strange shadow."
        ),
        (
            "Why did the room feel scary at first?",
            f"The light and the toy shapes made a shadow that looked like {layout.shadow_shape}. "
            "It felt scary because it looked bigger and stranger than the real objects."
        ),
    ]
    if f["outcome"] == "transformed":
        if act.parent_help:
            out.append((
                f"What brave thing did {child.id} do?",
                f"{child.id} called for {pw} and pointed at the wall instead of hiding alone. "
                "That was brave because asking for help is a wise thing to do when something feels frightening."
            ))
            out.append((
                "How did the shadow change?",
                "The parent moved the boat and deer so their shapes no longer crossed. "
                "When the objects changed places, the giant shadow broke into small ordinary shadows."
            ))
        else:
            out.append((
                f"What brave thing did {child.id} do?",
                f"{child.id} got out of bed and walked over to look closely. "
                "That was brave because {child.pronoun()} chose to learn the truth instead of letting the fear keep growing."
            ))
            out.append((
                "How did the shadow change?",
                "The child saw that the mast and the deer's antlers were crossing, then nudged the toys apart. "
                "When the shapes stopped crossing, the shadow turned gentle and easy to understand."
            ))
        out.append((
            "How did the story end?",
            f"It ended peacefully, with {child.id} back in bed and the room feeling safe again. "
            "The ending image shows that the scary idea had transformed back into ordinary bedtime things."
        ))
    else:
        out.append((
            "How did the story end?",
            f"It ended quietly, with {child.id} feeling calm and sleepy in the soft {light.label}. "
            "Nothing dangerous was there, and the peaceful room helped the child drift off to sleep."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"shelf", "mast", "deer", "shadow", "bravery"}
    if f["light"].id == "nightlight":
        tags.add("nightlight")
    if f["act"].parent_help:
        tags.add("help")
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


CURATED = [
    StoryParams(
        light="moon",
        layout="crossed",
        act="look",
        name="Mina",
        gender="girl",
        parent="mother",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        light="hall",
        layout="beside",
        act="call",
        name="Owen",
        gender="boy",
        parent="father",
        trait="quiet",
        seed=2,
    ),
    StoryParams(
        light="nightlight",
        layout="calm",
        act="look",
        name="Ivy",
        gender="girl",
        parent="mother",
        trait="sleepy",
        seed=3,
    ),
]


def explain_rejection(light: Light, layout: Layout, act: BraveAct) -> str:
    if act.id == "hide":
        return (
            "(No story: hiding under the blanket does not change the shadow or solve the bedtime worry. "
            "Pick a brave act like looking closely or asking a parent for help.)"
        )
    if layout.scary and act.courage < COURAGE_MIN:
        return "(No story: this act is not brave enough to carry the story's turn.)"
    return "(No story: this combination does not make a complete bedtime transformation.)"


ASP_RULES = r"""
light_ok(L) :- light(L), strength(L, S), S >= 1.
scary_layout(X) :- layout(X), scary(X).
calm_layout(X) :- layout(X), not scary(X).

valid(L, X, A) :- light(L), layout(X), act(A), calm_layout(X), changes_shadow(A), courage(A, C), C >= 2.
valid(L, X, A) :- light_ok(L), scary_layout(X), act(A), changes_shadow(A), courage(A, C), C >= 2.

outcome(peaceful) :- chosen_layout(X), calm_layout(X).
outcome(transformed) :- chosen_layout(X), scary_layout(X), chosen_act(A), changes_shadow(A), courage(A, C), C >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("strength", light_id, light.strength))
    for layout_id, layout in LAYOUTS.items():
        lines.append(asp.fact("layout", layout_id))
        if layout.scary:
            lines.append(asp.fact("scary", layout_id))
    for act_id, act in ACTS.items():
        lines.append(asp.fact("act", act_id))
        lines.append(asp.fact("courage", act_id, act.courage))
        if act.changes_shadow:
            lines.append(asp.fact("changes_shadow", act_id))
        if act.parent_help:
            lines.append(asp.fact("parent_help", act_id))
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
        asp.fact("chosen_layout", params.layout),
        asp.fact("chosen_act", params.act),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    layout = LAYOUTS[params.layout]
    if not layout.scary:
        return "peaceful"
    return "transformed"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a shelf, a mast, a deer, and a brave child who changes a shadow."
    )
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--layout", choices=LAYOUTS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.light is not None and args.light not in LIGHTS:
        raise StoryError("(Unknown light.)")
    if args.layout is not None and args.layout not in LAYOUTS:
        raise StoryError("(Unknown layout.)")
    if args.act is not None and args.act not in ACTS:
        raise StoryError("(Unknown act.)")

    if args.light and args.layout and args.act:
        light = LIGHTS[args.light]
        layout = LAYOUTS[args.layout]
        act = ACTS[args.act]
        if not valid_combo(light, layout, act):
            raise StoryError(explain_rejection(light, layout, act))

    combos = [
        c for c in valid_combos()
        if (args.light is None or c[0] == args.light)
        and (args.layout is None or c[1] == args.layout)
        and (args.act is None or c[2] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    light_id, layout_id, act_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = CHILD_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        light=light_id,
        layout=layout_id,
        act=act_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.light not in LIGHTS or params.layout not in LAYOUTS or params.act not in ACTS:
        raise StoryError("(Invalid params for this story world.)")

    light = LIGHTS[params.light]
    layout = LAYOUTS[params.layout]
    act = ACTS[params.act]
    if not valid_combo(light, layout, act):
        raise StoryError(explain_rejection(light, layout, act))

    world = tell(
        light=light,
        layout=layout,
        act=act,
        name=params.name,
        gender=params.gender,
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
    for seed in range(10):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print("MISMATCH: resolve_params unexpectedly failed during verification.")
            break

    for p in cases:
        py = outcome_of(p)
        asp_out = asp_outcome(p)
        if py != asp_out:
            rc = 1
            print(f"MISMATCH outcome for {p}: python={py} asp={asp_out}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story in smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (light, layout, act) combos:\n")
        for light, layout, act in combos:
            print(f"  {light:10} {layout:8} {act}")
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
            header = f"### {p.name}: {p.layout} shadow with {p.light} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
