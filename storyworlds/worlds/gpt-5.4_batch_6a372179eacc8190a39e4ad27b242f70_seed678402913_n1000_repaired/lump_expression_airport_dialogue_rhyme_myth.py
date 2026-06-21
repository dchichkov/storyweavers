#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py
========================================================================

A standalone storyworld about a child at an airport that is told in a gentle,
myth-tinged style. In this little domain, a child is about to board a plane,
fear rises, a helper notices the child's worried expression and the lump in
their throat, and a fitting comfort ritual uses dialogue and rhyme to change
what happens next.

The airport is rendered as a "sky harbor" without leaving ordinary common
sense behind: planes are still planes, gates are still gates, and helpers only
offer comforts they could really provide. The reasonableness gate checks two
things:

1. The comfort must actually match the kind of fear.
2. The chosen helper must plausibly be able to provide that comfort.

A second, outcome-level check models whether the comfort is strong enough for
the fear level and the bustle of the airport. If not, the story does not force
the child onto the plane. Instead, the adult chooses a calm, safe delay.

Run it
------
    python storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py
    python storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py --fear noise --comfort earmuffs
    python storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py --comfort candy
    python storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py --all
    python storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lump_expression_airport_dialogue_rhyme_myth.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman", "agent_female"}
        male = {"boy", "father", "grandfather", "uncle", "man", "agent_male"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
            "agent_female": "gate agent",
            "agent_male": "gate agent",
        }.get(self.type, self.type)


@dataclass
class Fear:
    id: str
    label: str
    cause: str
    sight: str
    child_line: str
    signal: str
    tags: set[str] = field(default_factory=set)
    severity: int = 2


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    sense: int = 2
    power: int = 2
    text: str = ""
    rhyme_a: str = ""
    rhyme_b: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    helper_type: str
    title: str
    can_give: set[str] = field(default_factory=set)
    gentle: str = ""
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_visible_fear(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    if child.memes["fear"] < THRESHOLD:
        return []
    sig = ("visible_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["voice_small"] += 1
    child.meters["tears_near"] += 1
    return []


def _r_comfort_softens(world: World) -> list[str]:
    child = world.entities.get("child")
    charm = world.entities.get("comfort")
    if child is None or charm is None:
        return []
    if charm.meters["in_use"] < THRESHOLD:
        return []
    sig = ("comfort_softens", charm.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["trust"] += 1
    child.meters["steady_breath"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - charm.meters["relief"])
    return []


CAUSAL_RULES = [
    Rule(name="visible_fear", tag="emotion", apply=_r_visible_fear),
    Rule(name="comfort_softens", tag="emotion", apply=_r_comfort_softens),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


FEARS = {
    "noise": Fear(
        id="noise",
        label="the roaring engines",
        cause="when the engines roared and the whole hall trembled a little",
        sight="the silver plane shook its wings with noise",
        child_line="The engines sound like thunder giants.",
        signal="the roar of takeoff",
        tags={"airport", "airplane", "noise"},
        severity=2,
    ),
    "height": Fear(
        id="height",
        label="the high sky",
        cause="when the child looked out at the long runway and thought of the high sky above it",
        sight="the plane looked small under the wide morning sky",
        child_line="What if the sky feels too big for me?",
        signal="the thought of flying so high",
        tags={"airport", "airplane", "sky"},
        severity=2,
    ),
    "goodbye": Fear(
        id="goodbye",
        label="the parting at the gate",
        cause="when it was time to wave to the family member who could not come past security",
        sight="the bright doors stood between this gate and home",
        child_line="I do not want the goodbye to feel so far.",
        signal="the parting at the gate",
        tags={"airport", "goodbye"},
        severity=3,
    ),
}

COMFORTS = {
    "earmuffs": Comfort(
        id="earmuffs",
        label="earmuffs",
        phrase="soft blue earmuffs",
        protects={"noise"},
        sense=3,
        power=2,
        text="settled soft blue earmuffs over the child's ears until the roar became a faraway sea",
        rhyme_a="Hush, little thunder, soften and slow.",
        rhyme_b="Small heart, steady heart, ready to go.",
        qa_text="used earmuffs and a calming rhyme to make the engines sound smaller",
        tags={"earmuffs", "rhyme", "airport"},
    ),
    "map": Comfort(
        id="map",
        label="window map",
        phrase="a little paper map of clouds and cities",
        protects={"height"},
        sense=3,
        power=2,
        text="opened a little paper map of clouds and cities and traced the route like a hero's road through the air",
        rhyme_a="Sky road, bright road, carry us through.",
        rhyme_b="Wing above, heart below, brave and true.",
        qa_text="turned the flight into a map-guided journey and paired it with a rhyme",
        tags={"map", "rhyme", "airport"},
    ),
    "ribbon": Comfort(
        id="ribbon",
        label="promise ribbon",
        phrase="a small promise ribbon tied around the child's wrist",
        protects={"goodbye"},
        sense=3,
        power=3,
        text="tied a small promise ribbon around the child's wrist and said it was a road that reached all the way back to love",
        rhyme_a="Thread of home, do not break or roam.",
        rhyme_b="Round my hand, love will find me home.",
        qa_text="gave the child a promise ribbon and words to hold during the goodbye",
        tags={"ribbon", "rhyme", "goodbye"},
    ),
    "breathing": Comfort(
        id="breathing",
        label="breathing rhyme",
        phrase="a breathing rhyme tapped on two fingers",
        protects={"noise", "height"},
        sense=2,
        power=1,
        text="tapped two fingers together and matched the child's breathing to a small gate-side rhyme",
        rhyme_a="Breathe in light, breathe out slow.",
        rhyme_b="Feet stay here while brave winds blow.",
        qa_text="used a breathing rhyme to steady the child's body",
        tags={"breathing", "rhyme", "calm"},
    ),
    "candy": Comfort(
        id="candy",
        label="candy",
        phrase="a sweet candy",
        protects=set(),
        sense=1,
        power=0,
        text="offered a sweet candy",
        rhyme_a="Sweet in hand, sweet in cheek.",
        rhyme_b="But sweets do not mend what fears still speak.",
        qa_text="offered candy",
        tags={"candy"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        helper_type="mother",
        title="mom",
        can_give={"earmuffs", "map", "ribbon", "breathing"},
        gentle="knelt beside the child so their eyes were level",
        tags={"parent"},
    ),
    "grandfather": HelperCfg(
        id="grandfather",
        helper_type="grandfather",
        title="grandpa",
        can_give={"map", "ribbon", "breathing"},
        gentle="rested one warm hand on the handle of the little suitcase and one on the child's shoulder",
        tags={"grandparent"},
    ),
    "agent": HelperCfg(
        id="agent",
        helper_type="agent_female",
        title="gate agent",
        can_give={"earmuffs", "map", "breathing"},
        gentle="leaned over the counter with a kind, patient smile",
        tags={"worker", "airport"},
    ),
}

CHILD_GIRL_NAMES = ["Lina", "Mira", "Nora", "Tali", "Aya", "Zoe", "Rina", "Etta"]
CHILD_BOY_NAMES = ["Leo", "Milo", "Tarin", "Eli", "Nico", "Oren", "Sami", "Theo"]
TRAITS = ["curious", "gentle", "watchful", "bright-eyed", "thoughtful", "small"]
DESTINATIONS = [
    "the island where Aunt Sela baked honey cakes",
    "the mountain city where the family festival would begin",
    "the sea town where Grandma kept a blue house",
    "the northern village where lanterns were lit at dusk",
]


def comfort_matches(fear: Fear, comfort: Comfort) -> bool:
    return fear.id in comfort.protects


def helper_can_offer(helper: HelperCfg, comfort: Comfort) -> bool:
    return comfort.id in helper.can_give


def sensible_comforts() -> list[Comfort]:
    return [c for c in COMFORTS.values() if c.sense >= SENSE_MIN]


def distress_level(fear: Fear, bustle: int) -> int:
    return fear.severity + bustle


def can_board(fear: Fear, comfort: Comfort, bustle: int) -> bool:
    return comfort.power >= distress_level(fear, bustle)


def predict_outcome(world: World, fear: Fear, comfort: Comfort, bustle: int) -> dict:
    sim = world.copy()
    child = sim.get("child")
    charm = sim.get("comfort")
    child.memes["fear"] = float(distress_level(fear, bustle))
    charm.meters["in_use"] = 1.0
    charm.meters["relief"] = float(comfort.power)
    propagate(sim, narrate=False)
    return {
        "fear_after": child.memes["fear"],
        "can_board": child.memes["fear"] < THRESHOLD,
    }


@dataclass
class StoryParams:
    fear: str
    comfort: str
    helper: str
    name: str
    gender: str
    trait: str
    destination: str
    bustle: int = 0
    seed: Optional[int] = None


def introduce(world: World, child: Entity, helper: Entity, destination: str) -> None:
    trait = next((t for t in child.traits if t), "small")
    world.say(
        f"At dawn the airport seemed less like a building than a sky harbor, where silver birds slept nose to tail under panes of gold. "
        f"{child.id}, a {trait} little {child.type}, stood beside {child.pronoun('possessive')} {helper.label_word} with one hand on a rolling suitcase."
    )
    world.say(
        f"They were bound for {destination}, and the loud hall shone with signs, windows, and the far glitter of wings."
    )


def tension(world: World, child: Entity, helper: Entity, fear: Fear, bustle: int) -> None:
    child.memes["fear"] = float(distress_level(fear, bustle))
    propagate(world, narrate=False)
    crowd = "The airport was busy, and every sound seemed to bounce from wall to wall." if bustle else "This early hour was gentler, but even gentle places can feel large to a child."
    world.say(crowd)
    world.say(
        f"When {fear.cause}, a worried expression crossed {child.id}'s face. There was a lump in {child.pronoun('possessive')} throat, as if one small stone had rolled into the place where words should be."
    )
    world.say(
        f'{helper.label_word.capitalize()} noticed at once. "{child.id}," {helper.pronoun()} said softly, "what is it?"'
    )
    world.say(f'"{fear.child_line}" {child.id} whispered.')


def offer(world: World, child: Entity, helper: Entity, fear: Fear, comfort: Comfort) -> None:
    charm = world.get("comfort")
    world.say(f"{helper.label_word.capitalize()} {HELPERS[world.facts['helper_cfg'].id].gentle}.")
    pred = predict_outcome(world, fear, comfort, world.facts["bustle"])
    world.facts["predicted_fear_after"] = pred["fear_after"]
    world.say(
        f'"Then we will not wrestle the fear with bare hands," {helper.pronoun()} said. "We will use {comfort.phrase}."'
    )
    charm.meters["in_use"] = 1.0
    charm.meters["relief"] = float(comfort.power)
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {comfort.text}."
    )
    world.say(
        f'"Listen," {helper.pronoun()} said. "{comfort.rhyme_a} {comfort.rhyme_b}"'
    )
    child.memes["courage"] += 1
    child.memes["trust"] += 1


def brave_boarding(world: World, child: Entity, helper: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    child.meters["boarding_pass_ready"] += 1
    child.meters["boarded"] += 1
    world.say(
        f'{child.id} said the little rhyme back, once softly and then again with a steadier voice. The hard lump in {child.pronoun("possessive")} throat loosened.'
    )
    world.say(
        f'Soon the gate opened. "{helper.label_word.capitalize()}, I can do it now," {child.id} said.'
    )
    world.say(
        f"Hand in hand, they walked down the bright tunnel toward the waiting plane, and {child.id}'s expression had changed. It was no longer pinched with fear. It shone with the brave seriousness of someone stepping onto a story-road in the sky."
    )


def gentle_delay(world: World, child: Entity, helper: Entity, comfort: Comfort) -> None:
    child.memes["fear"] = max(1.0, child.memes["fear"])
    child.memes["relief"] += 1
    world.say(
        f"{child.id} tried the rhyme and held onto {comfort.label}, but the airport still felt too huge all at once."
    )
    world.say(
        f'"Then we wait," said {helper.label_word}. "A sky road is never worth tears forced too fast."'
    )
    world.say(
        f"They sat by the wide window and watched one plane lift slowly into the morning. By the time its silver shape had become a speck, {child.id}'s expression was calmer, and the fear had turned from a storm into something small enough to name."
    )


def ending_lesson(world: World, child: Entity, helper: Entity, fear: Fear, comfort: Comfort, boarded: bool) -> None:
    child.memes["lesson"] += 1
    if boarded:
        world.say(
            f"After that, whenever {fear.signal} returned, {child.id} remembered the rhyme and the kind voice beside it. Even in the busy airport, courage no longer had to arrive alone."
        )
    else:
        world.say(
            f"After that morning, {child.id} knew that fear could be spoken before it grew too large. In the airport of shining wings, that was its own kind of brave magic."
        )


def tell(
    fear: Fear,
    comfort: Comfort,
    helper_cfg: HelperCfg,
    name: str = "Lina",
    gender: str = "girl",
    trait: str = "watchful",
    destination: str = "the sea town where Grandma kept a blue house",
    bustle: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=gender,
        label=name,
        role="child",
        traits=[trait],
        attrs={"display_name": name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.helper_type,
        label=helper_cfg.title,
        role="helper",
    ))
    charm = world.add(Entity(
        id="comfort",
        kind="thing",
        type="comfort",
        label=comfort.label,
        phrase=comfort.phrase,
        tags=set(comfort.tags),
    ))
    world.facts.update(
        child=child,
        helper=helper,
        fear_cfg=fear,
        comfort_cfg=comfort,
        helper_cfg=helper_cfg,
        bustle=bustle,
        destination=destination,
    )

    introduce(world, child, helper, destination)
    world.para()
    tension(world, child, helper, fear, bustle)
    world.para()
    offer(world, child, helper, fear, comfort)

    boarded = can_board(fear, comfort, bustle)
    world.para()
    if boarded:
        brave_boarding(world, child, helper)
    else:
        gentle_delay(world, child, helper, comfort)

    world.para()
    ending_lesson(world, child, helper, fear, comfort, boarded)
    world.facts.update(
        boarded=boarded,
        outcome="boarded" if boarded else "waited",
        visible_fear=child.meters["voice_small"] >= THRESHOLD,
        rhyme_used=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for fear_id, fear in FEARS.items():
        for comfort_id, comfort in COMFORTS.items():
            if comfort.sense < SENSE_MIN:
                continue
            if not comfort_matches(fear, comfort):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_can_offer(helper, comfort):
                    combos.append((fear_id, comfort_id, helper_id))
    return combos


KNOWLEDGE = {
    "airport": [
        (
            "What happens at an airport?",
            "People come to an airport to check in, wait at gates, and board airplanes. It is a place where journeys begin and end."
        )
    ],
    "airplane": [
        (
            "What does an airplane do?",
            "An airplane carries people through the sky from one place to another. It needs runways, pilots, and careful rules to travel safely."
        )
    ],
    "noise": [
        (
            "Why are airplanes loud?",
            "Airplanes are loud because their engines push a great deal of air to make the plane move. That strong sound can feel scary when you are close to it."
        )
    ],
    "sky": [
        (
            "Why can flying high feel strange?",
            "Flying high can feel strange because the ground looks far away and everything seems very big or very small. New heights can make your body feel nervous even when you are safe."
        )
    ],
    "goodbye": [
        (
            "Why can goodbyes feel hard at an airport?",
            "Goodbyes can feel hard because one person is staying and another is leaving. Even a short parting can feel bigger in a busy place."
        )
    ],
    "earmuffs": [
        (
            "What do earmuffs help with?",
            "Earmuffs cover the ears and make loud sounds feel softer. They can help when noise is the part that feels hardest."
        )
    ],
    "map": [
        (
            "How can a map help a worried traveler?",
            "A map makes a journey feel knowable because it shows where you are and where you are going. Seeing a path can make a big trip feel smaller."
        )
    ],
    "ribbon": [
        (
            "What can a ribbon mean in a story?",
            "A ribbon can be a small thing that stands for love, promise, or remembrance. Holding it can help a child remember that care stays with them."
        )
    ],
    "breathing": [
        (
            "Why does slow breathing help when you feel afraid?",
            "Slow breathing helps your body settle down. When your body grows steadier, your thoughts can feel steadier too."
        )
    ],
    "rhyme": [
        (
            "Why do rhymes help people remember words?",
            "Rhymes repeat sounds in a pleasing pattern, so they are easier to remember. A short rhyme can feel like something steady to hold in your mind."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "airport",
    "airplane",
    "noise",
    "sky",
    "goodbye",
    "earmuffs",
    "map",
    "ribbon",
    "breathing",
    "rhyme",
]


def child_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    fear = world.facts["fear_cfg"]
    comfort = world.facts["comfort_cfg"]
    outcome = world.facts["outcome"]
    name = child_name(child)
    base = (
        f'Write a short myth-like airport story for a 3-to-5-year-old that includes the words "lump" and "expression", uses dialogue, and includes a rhyme.'
    )
    if outcome == "boarded":
        return [
            base,
            f"Tell a gentle story where {name} feels afraid of {fear.label} in an airport, but {helper.label_word} helps with {comfort.phrase} and a rhyme until the child can board.",
            f"Write a child-facing tale in which a worried expression changes into a brave one after a helper at the airport speaks in rhyme.",
        ]
    return [
        base,
        f"Tell a gentle airport story where {name} is frightened by {fear.label}, and {helper.label_word} uses {comfort.phrase} and a rhyme, but wisely chooses to wait instead of forcing the child onto the plane.",
        f"Write a myth-tinged tale showing that naming fear and waiting calmly can be brave too.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    fear = world.facts["fear_cfg"]
    comfort = world.facts["comfort_cfg"]
    destination = world.facts["destination"]
    name = child_name(child)
    helper_word = helper.label_word
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child at an airport, and {name}'s {helper_word}. They are starting a journey to {destination}."
        ),
        (
            f"Why did {name} feel afraid?",
            f"{name} felt afraid because of {fear.label}. The story shows that the fear rose when {fear.cause}, and that is why the child's expression changed."
        ),
        (
            "What does the word lump mean in this story?",
            f"Here, lump means the hard feeling in {name}'s throat when big feelings made speaking difficult. It shows fear in a physical, child-sized way."
        ),
        (
            f"What did {helper_word} do to help?",
            f"{helper_word.capitalize()} {comfort.qa_text}. The helper also spoke in rhyme so the comfort became something {name} could repeat and remember."
        ),
    ]
    if outcome == "boarded":
        qa.append(
            (
                f"How did {name} change by the end?",
                f"By the end, {name}'s expression was brave instead of pinched with fear. The rhyme and the fitting comfort helped the child board the plane with a steadier body and voice."
            )
        )
    else:
        qa.append(
            (
                f"Why did they wait instead of boarding right away?",
                f"They waited because the airport still felt too overwhelming even after the first comfort. The safe choice was to slow down and let the fear grow smaller before trying again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    fear = world.facts["fear_cfg"]
    comfort = world.facts["comfort_cfg"]
    tags: set[str] = {"airport", "airplane", "rhyme"} | set(fear.tags) | set(comfort.tags)
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        fear="noise",
        comfort="earmuffs",
        helper="mother",
        name="Mira",
        gender="girl",
        trait="watchful",
        destination="the sea town where Grandma kept a blue house",
        bustle=0,
    ),
    StoryParams(
        fear="height",
        comfort="map",
        helper="grandfather",
        name="Leo",
        gender="boy",
        trait="curious",
        destination="the mountain city where the family festival would begin",
        bustle=0,
    ),
    StoryParams(
        fear="goodbye",
        comfort="ribbon",
        helper="mother",
        name="Aya",
        gender="girl",
        trait="gentle",
        destination="the northern village where lanterns were lit at dusk",
        bustle=1,
    ),
    StoryParams(
        fear="noise",
        comfort="breathing",
        helper="agent",
        name="Nico",
        gender="boy",
        trait="small",
        destination="the island where Aunt Sela baked honey cakes",
        bustle=1,
    ),
]


def explain_comfort_mismatch(fear: Fear, comfort: Comfort) -> str:
    return (
        f"(No story: {comfort.label} does not really address {fear.label}. "
        f"The comfort must match the fear, not just fill a line of dialogue.)"
    )


def explain_helper_mismatch(helper: HelperCfg, comfort: Comfort) -> str:
    return (
        f"(No story: {helper.title} cannot plausibly provide {comfort.label} in this world. "
        f"Choose a helper who could really offer it.)"
    )


def explain_low_sense(comfort: Comfort) -> str:
    return (
        f"(Refusing comfort '{comfort.id}': it scores too low on common sense "
        f"(sense={comfort.sense} < {SENSE_MIN}). A sweet is not a real answer to this kind of fear.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.fear not in FEARS or params.comfort not in COMFORTS:
        return "?"
    return "boarded" if can_board(FEARS[params.fear], COMFORTS[params.comfort], params.bustle) else "waited"


ASP_RULES = r"""
% Reasonableness gate
matched(F, C) :- fear(F), comfort(C), protects(C, F).
sensible(C)   :- comfort(C), sense(C, S), sense_min(M), S >= M.
plausible(H, C) :- helper(H), can_give(H, C).
valid(F, C, H) :- matched(F, C), sensible(C), plausible(H, C).

% Outcome model
distress(D) :- chosen_fear(F), severity(F, S), bustle(B), D = S + B.
boarded :- chosen_comfort(C), power(C, P), distress(D), P >= D.
outcome(boarded) :- boarded.
outcome(waited) :- not boarded.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fear_id, fear in FEARS.items():
        lines.append(asp.fact("fear", fear_id))
        lines.append(asp.fact("severity", fear_id, fear.severity))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("sense", comfort_id, comfort.sense))
        lines.append(asp.fact("power", comfort_id, comfort.power))
        for fear_id in sorted(comfort.protects):
            lines.append(asp.fact("protects", comfort_id, fear_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for comfort_id in sorted(helper.can_give):
            lines.append(asp.fact("can_give", helper_id, comfort_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_fear", params.fear),
        asp.fact("chosen_comfort", params.comfort),
        asp.fact("bustle", params.bustle),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("smoke test failed: empty story")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    if "lump" not in sample.story or "expression" not in sample.story:
        raise StoryError("smoke test failed: seed words missing from story")


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

    clingo_sense = set(asp_sensible())
    python_sense = {c.id for c in sensible_comforts()}
    if clingo_sense == python_sense:
        print(f"OK: sensible comforts match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible comforts: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generate/emit passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: an airport fear, a fitting comfort, and a rhyme. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--fear", choices=FEARS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--bustle", type=int, choices=[0, 1], help="0 = early and calmer, 1 = busy and louder")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.comfort is not None:
        comfort = COMFORTS[args.comfort]
        if comfort.sense < SENSE_MIN:
            raise StoryError(explain_low_sense(comfort))
    if args.fear is not None and args.comfort is not None:
        fear = FEARS[args.fear]
        comfort = COMFORTS[args.comfort]
        if not comfort_matches(fear, comfort):
            raise StoryError(explain_comfort_mismatch(fear, comfort))
    if args.helper is not None and args.comfort is not None:
        helper = HELPERS[args.helper]
        comfort = COMFORTS[args.comfort]
        if not helper_can_offer(helper, comfort):
            raise StoryError(explain_helper_mismatch(helper, comfort))

    combos = [
        c for c in valid_combos()
        if (args.fear is None or c[0] == args.fear)
        and (args.comfort is None or c[1] == args.comfort)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    fear_id, comfort_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = CHILD_GIRL_NAMES if gender == "girl" else CHILD_BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)
    destination = args.destination or rng.choice(DESTINATIONS)
    bustle = args.bustle if args.bustle is not None else rng.choice([0, 1])

    return StoryParams(
        fear=fear_id,
        comfort=comfort_id,
        helper=helper_id,
        name=name,
        gender=gender,
        trait=trait,
        destination=destination,
        bustle=bustle,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        fear = FEARS[params.fear]
        comfort = COMFORTS[params.comfort]
        helper_cfg = HELPERS[params.helper]
    except KeyError as exc:
        raise StoryError(f"(No story: invalid parameter {exc.args[0]!r}.)") from None

    if comfort.sense < SENSE_MIN:
        raise StoryError(explain_low_sense(comfort))
    if not comfort_matches(fear, comfort):
        raise StoryError(explain_comfort_mismatch(fear, comfort))
    if not helper_can_offer(helper_cfg, comfort):
        raise StoryError(explain_helper_mismatch(helper_cfg, comfort))

    world = tell(
        fear=fear,
        comfort=comfort,
        helper_cfg=helper_cfg,
        name=params.name,
        gender=params.gender,
        trait=params.trait,
        destination=params.destination,
        bustle=params.bustle,
    )
    world.get("child").attrs["display_name"] = params.name
    story = world.render().replace("child", params.name)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible comforts: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (fear, comfort, helper) combos:\n")
        for fear_id, comfort_id, helper_id in combos:
            print(f"  {fear_id:8} {comfort_id:10} {helper_id}")
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
            header = f"### {p.name}: {p.fear} with {p.comfort} ({p.helper}, {outcome_of(p)})"
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
