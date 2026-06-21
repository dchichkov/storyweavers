#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py
===================================================================

A standalone storyworld about a child noticing a garden problem, choosing a
simple defense, and learning what happens when the defense is missing or too
weak. The prose stays gentle and heartwarming even when the ending is sad:
the plants can be lost, but love, help, and a wiser plan remain.

The tiny domain:
- A child grows something tender in a small garden patch or pot.
- A hungry visitor (rabbits, birds, or snails) keeps coming.
- The child can ask for help and build a defense.
- Some defenses fit some visitors; weak or mismatched defenses are refused.
- Delay matters: if help comes too late, the plants are eaten anyway.
- The ending can be happy or sad, but the family still comforts each other.
- The story uses light rhyme in repeated lines and the closing image.

Run it
------
    python storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py --plant lettuce --visitor rabbits
    python storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py --defense ribbon
    python storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/defense_rhyme_bad_ending_heartwarming.py --verify
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
SENSE_MIN = 2


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
class Plant:
    id: str
    label: str
    phrase: str
    plural: bool
    need: str
    fragility: int
    rhyme_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Visitor:
    id: str
    label: str
    plural: bool
    sneak: str
    nibble: str
    hunger: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Defense:
    id: str
    label: str
    phrase: str
    works_for: set[str]
    power: int
    sense: int
    build: str
    ending: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    detail: str
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


def _r_nibble(world: World) -> list[str]:
    out: list[str] = []
    plants = [e for e in world.entities.values() if e.role == "plant"]
    visitors = [e for e in world.entities.values() if e.role == "visitor"]
    if not plants or not visitors:
        return out
    plant = plants[0]
    visitor = visitors[0]
    if visitor.meters["inside"] < THRESHOLD:
        return out
    sig = ("nibble", plant.id, int(visitor.meters["inside"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["nibbled"] += 1
    plant.meters["health"] -= 1
    out.append("__nibble__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    plants = [e for e in world.entities.values() if e.role == "plant"]
    childs = [e for e in world.entities.values() if e.role == "child"]
    if not plants:
        return out
    plant = plants[0]
    if plant.meters["nibbled"] < THRESHOLD * 2:
        return out
    sig = ("loss", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["lost"] += 1
    for child in childs:
        child.memes["sadness"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule(name="nibble", tag="physical", apply=_r_nibble),
    Rule(name="loss", tag="physical", apply=_r_loss),
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
    "yard": Place(
        id="yard",
        label="the little backyard garden",
        detail="Behind the house sat a little garden bed with dark crumbly soil and a low wooden edge.",
        tags={"garden"},
    ),
    "porch": Place(
        id="porch",
        label="the sunny porch pots",
        detail="On the sunny porch stood a row of flowerpots where morning light warmed the leaves.",
        tags={"garden"},
    ),
    "window": Place(
        id="window",
        label="the kitchen windowsill",
        detail="On the kitchen windowsill, a small pot leaned into the light beside the glass.",
        tags={"garden", "indoor"},
    ),
}

PLANTS = {
    "lettuce": Plant(
        id="lettuce",
        label="lettuce",
        phrase="a neat row of lettuce leaves",
        plural=True,
        need="crisp green leaves for sandwiches",
        fragility=2,
        rhyme_line="Leaf by leaf, safe from grief",
        tags={"lettuce", "garden"},
    ),
    "strawberries": Plant(
        id="strawberries",
        label="strawberries",
        phrase="three shy strawberry plants with white blossoms",
        plural=True,
        need="sweet berries for a summer bowl",
        fragility=2,
        rhyme_line="Berry red, safe in bed",
        tags={"strawberry", "garden"},
    ),
    "beans": Plant(
        id="beans",
        label="beans",
        phrase="little bean vines reaching up a string",
        plural=True,
        need="long green beans for supper",
        fragility=1,
        rhyme_line="Bean so bright, hold on tight",
        tags={"beans", "garden"},
    ),
    "sunflower": Plant(
        id="sunflower",
        label="sunflower",
        phrase="one young sunflower with a fuzzy stem",
        plural=False,
        need="a tall yellow face by summer",
        fragility=1,
        rhyme_line="Sunny flower, stand with power",
        tags={"sunflower", "garden"},
    ),
}

VISITORS = {
    "rabbits": Visitor(
        id="rabbits",
        label="rabbits",
        plural=True,
        sneak="under the fence at dusk",
        nibble="took quick crunchy bites",
        hunger=2,
        tags={"rabbit", "garden"},
    ),
    "birds": Visitor(
        id="birds",
        label="birds",
        plural=True,
        sneak="down from the fence rail",
        nibble="pecked and tugged at the tender parts",
        hunger=1,
        tags={"bird", "garden"},
    ),
    "snails": Visitor(
        id="snails",
        label="snails",
        plural=True,
        sneak="through the damp shade after dark",
        nibble="left tiny shiny trails and chewed holes in the leaves",
        hunger=1,
        tags={"snail", "garden"},
    ),
}

DEFENSES = {
    "fence": Defense(
        id="fence",
        label="fence",
        phrase="a small wire fence",
        works_for={"rabbits"},
        power=3,
        sense=3,
        build="pushed small stakes into the soil and wrapped a small wire fence around the bed",
        ending="The little fence made a silver ring around the green things.",
        qa_text="built a small wire fence around the plants",
        tags={"fence", "defense"},
    ),
    "net": Defense(
        id="net",
        label="net",
        phrase="a light garden net",
        works_for={"birds"},
        power=2,
        sense=3,
        build="draped a light garden net over the plants and tucked the edges down neatly",
        ending="The fine net hung softly like a tiny cloud over the leaves.",
        qa_text="covered the plants with a light garden net",
        tags={"net", "defense"},
    ),
    "copper": Defense(
        id="copper",
        label="copper tape ring",
        phrase="a copper tape ring",
        works_for={"snails"},
        power=2,
        sense=3,
        build="pressed a shining ring of copper tape around the rim and patted it smooth",
        ending="The copper ring gleamed like a careful little moon.",
        qa_text="made a shining copper tape ring around the pot",
        tags={"copper", "defense"},
    ),
    "scare_pinwheel": Defense(
        id="scare_pinwheel",
        label="pinwheel",
        phrase="a bright pinwheel",
        works_for={"birds"},
        power=1,
        sense=2,
        build="stuck a bright pinwheel beside the plants so it could flutter in the breeze",
        ending="The pinwheel clicked and flashed in the sun.",
        qa_text="set up a bright pinwheel beside the plants",
        tags={"pinwheel", "defense"},
    ),
    "ribbon": Defense(
        id="ribbon",
        label="ribbon",
        phrase="a pretty ribbon",
        works_for=set(),
        power=0,
        sense=1,
        build="tied a pretty ribbon near the plants",
        ending="The ribbon was lovely, but it was not much of a defense.",
        qa_text="tied a pretty ribbon near the plants",
        tags={"ribbon", "defense"},
    ),
}


def visitor_can_reach(place_id: str, visitor_id: str) -> bool:
    if place_id == "window" and visitor_id == "rabbits":
        return False
    return True


def effective_defense(defense_id: str, visitor_id: str, delay: int) -> bool:
    defense = DEFENSES[defense_id]
    visitor = VISITORS[visitor_id]
    return visitor_id in defense.works_for and defense.power >= visitor.hunger + delay


def hazard_exists(place_id: str, visitor_id: str) -> bool:
    return visitor_can_reach(place_id, visitor_id)


def sensible_defenses() -> list[Defense]:
    return [d for d in DEFENSES.values() if d.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for plant_id in PLANTS:
            for visitor_id in VISITORS:
                if not hazard_exists(place_id, visitor_id):
                    continue
                for defense_id, defense in DEFENSES.items():
                    if defense.sense < SENSE_MIN:
                        continue
                    if visitor_id in defense.works_for:
                        combos.append((place_id, plant_id, visitor_id, defense_id))
    return sorted(combos)


def explain_place(place_id: str, visitor_id: str) -> str:
    if not visitor_can_reach(place_id, visitor_id):
        return (
            f"(No story: {VISITORS[visitor_id].label} cannot reasonably reach plants on "
            f"{PLACES[place_id].label}, so there is no honest need for a defense.)"
        )
    return "(No story: this place does not create a reasonable garden problem.)"


def explain_defense(defense_id: str) -> str:
    defense = DEFENSES[defense_id]
    better = ", ".join(sorted(d.id for d in sensible_defenses()))
    return (
        f"(Refusing defense '{defense_id}': it scores too low on common sense "
        f"(sense={defense.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_mismatch(defense_id: str, visitor_id: str) -> str:
    defense = DEFENSES[defense_id]
    visitor = VISITORS[visitor_id]
    return (
        f"(No story: {defense.phrase} is not a sensible defense against {visitor.label} "
        f"in this little world. Pick a defense that actually blocks that visitor.)"
    )


def predict_loss(world: World, delay: int, defense_id: str) -> dict:
    sim = world.copy()
    child = sim.get("child")
    parent = sim.get("parent")
    _build_defense(sim, child, parent, defense_id, narrate=False)
    _visitor_arrives(sim, delay=delay, narrate=False)
    plant = sim.get("plant")
    return {
        "nibbled": plant.meters["nibbled"],
        "lost": plant.meters["lost"] >= THRESHOLD,
    }


def _build_defense(world: World, child: Entity, parent: Entity, defense_id: str, narrate: bool = True) -> None:
    defense = DEFENSES[defense_id]
    guard = world.get("guard")
    guard.attrs["defense_id"] = defense_id
    guard.meters["ready"] += 1
    guard.meters["power"] = float(defense.power)
    child.memes["hope"] += 1
    parent.memes["care"] += 1
    if narrate:
        world.say(
            f"Together they {defense.build}. "
            f'"A gentle defense, a patient defense," {parent.label_word} said. '
            f'"Let us help the garden make its stand."'
        )


def _visitor_arrives(world: World, delay: int, narrate: bool = True) -> None:
    visitor_cfg = world.facts["visitor_cfg"]
    defense_id = world.get("guard").attrs.get("defense_id", "")
    blocked = bool(defense_id) and effective_defense(defense_id, visitor_cfg.id, delay)
    visitor = world.get("visitor")
    plant = world.get("plant")
    visitor.meters["arrived"] += 1
    if blocked:
        visitor.meters["outside"] += 1
        plant.memes["safe"] += 1
        if narrate:
            world.say(
                f"That evening the {visitor_cfg.label} came {visitor_cfg.sneak}, "
                f"but the defense held. They sniffed or peered, then turned away."
            )
    else:
        visitor.meters["inside"] += 2
        propagate(world, narrate=False)
        propagate(world, narrate=False)
        if narrate:
            world.say(
                f"That evening the {visitor_cfg.label} came {visitor_cfg.sneak}. "
                f"They {visitor_cfg.nibble}, and by morning the plants looked hurt."
            )


def introduce(world: World, child: Entity, parent: Entity, place: Place, plant: Plant) -> None:
    child.memes["love"] += 1
    world.say(
        f"{child.id} loved to check {place.label} each morning with {child.pronoun('possessive')} "
        f"{parent.label_word}. {place.detail}"
    )
    world.say(
        f"There grew {plant.phrase}, and {child.id} already imagined {plant.need}."
    )
    world.say(f'{child.id} liked to whisper, "{plant.rhyme_line}."')


def notice_problem(world: World, child: Entity, visitor: Visitor, plant: Plant) -> None:
    child.memes["worry"] += 1
    world.say(
        f"One morning, {child.id} saw that something had been near the {plant.label}. "
        f'"Oh no," {child.pronoun()} said. "Maybe {visitor.label} will come back."'
    )


def ask_help(world: World, child: Entity, parent: Entity, visitor: Visitor) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{child.id} ran to {child.pronoun('possessive')} {parent.label_word} and asked for help. "
        f'{parent.label_word.capitalize()} knelt beside the leaves and said, '
        f'"A garden can be small, but love can be tall. We can make a defense for these tender things."'
    )
    world.say(
        f'Together they named the trouble plainly: hungry {visitor.label}. '
        f'Together they named the job plainly too: a defense.'
    )


def decide(world: World, child: Entity, parent: Entity, defense_id: str, delay: int) -> None:
    defense = DEFENSES[defense_id]
    pred = predict_loss(world, delay=delay, defense_id=defense_id)
    world.facts["predicted_loss"] = pred["lost"]
    world.facts["predicted_nibbled"] = pred["nibbled"]
    if pred["lost"]:
        world.say(
            f'{child.id} looked at {defense.phrase} and hoped it would be enough, but '
            f'{parent.label_word} worried the hungry visitors might still get through if they waited too long.'
        )
    else:
        world.say(
            f'{child.id} looked at {defense.phrase} and nodded. '
            f'"Soft hands, wise plans," {child.pronoun()} said.'
        )


def comfort_after_loss(world: World, child: Entity, parent: Entity, plant: Plant) -> None:
    child.memes["comforted"] += 1
    parent.memes["comfort"] += 1
    world.say(
        f"{child.id}'s eyes filled with tears when {child.pronoun()} saw the damage. "
        f"But {parent.label_word} sat beside {child.pronoun('object')} on the step and put an arm around {child.pronoun('object')}."
    )
    world.say(
        f'"We are sad, and that is true," {parent.label_word} said softly. '
        f'"Still, roots teach patient hearts what loving hands can do. We can plant again."'
    )
    world.say(
        f"Together they gathered the broken bits of {plant.label}, saved the good soil, "
        f"and made a new plan before the sun went down."
    )


def happy_ending(world: World, child: Entity, parent: Entity, defense_id: str, plant: Plant) -> None:
    defense = DEFENSES[defense_id]
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(defense.ending)
    world.say(
        f"In the morning the {plant.label} still stood there, green and quiet. "
        f'{child.id} clapped and said, "{plant.rhyme_line}."'
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled, and together they watered the roots. "
        f"The little garden looked ordinary again, which felt like a kind of treasure."
    )


def sad_ending(world: World, child: Entity, parent: Entity, plant: Plant) -> None:
    world.say(
        f"By morning, too much of the {plant.label} was gone. The defense had come too late, "
        f"and the tender garden had lost this round."
    )
    comfort_after_loss(world, child, parent, plant)


def tell(
    place: Place,
    plant_cfg: Plant,
    visitor_cfg: Visitor,
    defense_id: str,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child", traits=[trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label=plant_cfg.label, phrase=plant_cfg.phrase, role="plant"))
    visitor = world.add(Entity(id="visitor", kind="thing", type="visitor", label=visitor_cfg.label, role="visitor"))
    guard = world.add(Entity(id="guard", kind="thing", type="defense", label="defense", role="defense"))

    plant.meters["health"] = float(plant_cfg.fragility + 1)
    world.facts.update(place=place, plant_cfg=plant_cfg, visitor_cfg=visitor_cfg, child=child, parent=parent)

    introduce(world, child, parent, place, plant_cfg)
    world.para()
    notice_problem(world, child, visitor_cfg, plant_cfg)
    ask_help(world, child, parent, visitor_cfg)
    decide(world, child, parent, defense_id, delay)
    world.para()
    _build_defense(world, child, parent, defense_id, narrate=True)
    _visitor_arrives(world, delay=delay, narrate=True)
    world.para()

    outcome = "saved" if effective_defense(defense_id, visitor_cfg.id, delay) else "lost"
    if outcome == "saved":
        happy_ending(world, child, parent, defense_id, plant_cfg)
    else:
        sad_ending(world, child, parent, plant_cfg)

    world.facts.update(
        defense=DEFENSES[defense_id],
        delay=delay,
        outcome=outcome,
        nibbled=plant.meters["nibbled"],
        lost=plant.meters["lost"] >= THRESHOLD,
        child_name=child_name,
    )
    return world


@dataclass
class StoryParams:
    place: str
    plant: str
    visitor: str
    defense: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]
TRAITS = ["careful", "gentle", "hopeful", "patient", "curious"]

CURATED = [
    StoryParams(
        place="yard",
        plant="lettuce",
        visitor="rabbits",
        defense="fence",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        place="porch",
        plant="strawberries",
        visitor="birds",
        defense="net",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        place="window",
        plant="sunflower",
        visitor="snails",
        defense="copper",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        trait="patient",
        delay=1,
    ),
    StoryParams(
        place="yard",
        plant="lettuce",
        visitor="rabbits",
        defense="fence",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="hopeful",
        delay=2,
    ),
    StoryParams(
        place="porch",
        plant="beans",
        visitor="birds",
        defense="scare_pinwheel",
        child_name="Ava",
        child_gender="girl",
        parent="mother",
        trait="curious",
        delay=1,
    ),
]


KNOWLEDGE = {
    "rabbit": [
        (
            "Why do rabbits nibble garden leaves?",
            "Rabbits are plant eaters, so soft green leaves can smell like food to them. A garden may feel like a tasty dinner table."
        )
    ],
    "bird": [
        (
            "Why do birds peck at plants?",
            "Birds peck for food, seeds, bugs, or soft fruit. Tender new growth can be easy for them to reach."
        )
    ],
    "snail": [
        (
            "Why do snails come out after dark or damp weather?",
            "Snails like damp places because their bodies dry out easily. Cool shade and wet evenings help them move safely."
        )
    ],
    "fence": [
        (
            "What does a garden fence do?",
            "A garden fence makes a small barrier around plants. It can help keep nibbling animals from getting close."
        )
    ],
    "net": [
        (
            "What does garden netting do?",
            "Garden netting covers plants with a light barrier. It lets in light and air while making it harder for birds to peck."
        )
    ],
    "copper": [
        (
            "Why do some gardeners use copper tape for snails?",
            "Copper tape is used as a barrier around pots or beds. In simple child terms, it helps tell the snails to turn back."
        )
    ],
    "pinwheel": [
        (
            "How can a pinwheel help in a garden?",
            "A fluttering pinwheel can startle some birds for a while. It is a gentle scare tool, though it may not work forever."
        )
    ],
    "garden": [
        (
            "What is a defense?",
            "A defense is something you set up to protect a place or thing from harm. In a garden, a defense can help keep hungry visitors away."
        )
    ],
    "lettuce": [
        (
            "What kind of plant is lettuce?",
            "Lettuce is a leafy plant people often eat in salads or sandwiches. Its soft leaves can be tempting to hungry animals."
        )
    ],
    "strawberry": [
        (
            "What do strawberry plants grow?",
            "Strawberry plants grow small flowers first and then sweet berries. Animals and people both like the fruit."
        )
    ],
    "beans": [
        (
            "How do bean plants grow?",
            "Many bean plants climb as they grow, so they often like a string or pole for support. Their young leaves can still be tender."
        )
    ],
    "sunflower": [
        (
            "Why do sunflowers turn into tall flowers?",
            "Sunflowers begin as small plants and grow upward toward the light. Later they can make a big bright flower head."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "garden",
    "rabbit",
    "bird",
    "snail",
    "fence",
    "net",
    "copper",
    "pinwheel",
    "lettuce",
    "strawberry",
    "beans",
    "sunflower",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    plant = f["plant_cfg"]
    visitor = f["visitor_cfg"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old that includes the word "defense", uses a light rhyme, and has a sad garden ending.',
            f"Tell a gentle story where {child.label} tries to protect {plant.label} in {place.label} from {visitor.label}, but the defense comes too late and the family comforts each other.",
            f'Write a simple rhyming story with a bad ending where plants are lost, but a loving grown-up helps a child make a new plan.'
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "defense" and uses a light rhyme.',
        f"Tell a gentle story where {child.label} and {child.pronoun('possessive')} {world.facts['parent'].label_word} build a defense to protect {plant.label} from {visitor.label}.",
        f'Write a cozy garden story with a rhyming line and an ending image that shows what changed after a wise defense was built.'
    ]


def pair_answer_name(world: World) -> str:
    return world.facts["child"].label


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    plant = f["plant_cfg"]
    visitor = f["visitor_cfg"]
    defense = f["defense"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child caring for {plant.label}, and {child.pronoun('possessive')} {parent.label_word} who helps. They are trying to protect a small garden in {place.label}."
        ),
        (
            f"What problem did {child.label} notice?",
            f"{child.label} noticed signs that {visitor.label} had been near the {plant.label}. That made {child.pronoun('object')} worry the plants might be eaten."
        ),
        (
            "What does the word defense mean in this story?",
            f"In this story, a defense means something built to protect the plants. They needed it because hungry {visitor.label} might come back."
        ),
        (
            f"How did {child.label} try to protect the plants?",
            f"{child.label} and {child.pronoun('possessive')} {parent.label_word} {defense.qa_text}. They chose that defense because it was meant for {visitor.label} in this little garden world."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "Did the defense work?",
                f"Yes. When the {visitor.label} came, the defense held and the plants stayed safe. The morning image of green leaves shows that the problem had changed."
            )
        )
        qa.append(
            (
                f"Why did the ending feel happy?",
                f"The garden was protected, so {child.label} felt relieved and proud. The family could go back to watering and caring instead of losing the plants."
            )
        )
    else:
        qa.append(
            (
                "Did the defense work in time?",
                f"No. The visitors still got through, and too much of the {plant.label} was gone by morning. The sad ending came from delay and hunger, not from anyone being unkind."
            )
        )
        qa.append(
            (
                f"Why is the ending sad but still heartwarming?",
                f"It is sad because the plants were lost. It is still heartwarming because {child.label}'s {parent.label_word} stayed close, comforted {child.pronoun('object')}, and helped make a new plan together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["plant_cfg"].tags) | set(f["visitor_cfg"].tags) | set(f["defense"].tags)
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            parts.append(f"attrs={ent.attrs}")
        if ent.role:
            parts.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reachability
hazard(P, V) :- place(P), visitor(V), reachable(P, V).

% sensible defenses
sensible(D) :- defense(D), sense(D, S), sense_min(M), S >= M.

% fit between defense and visitor
fits(D, V) :- works_for(D, V).

% valid combo means a real hazard and a sensible fitted defense
valid(P, Pl, V, D) :- place(P), plant(Pl), visitor(V), defense(D),
                      hazard(P, V), sensible(D), fits(D, V).

% outcome model
severity(V, Dly, H + Dly) :- hunger(V, H), delay(Dly).
holds(D, V, Dly) :- chosen_defense(D), chosen_visitor(V), delay(Dly),
                    works_for(D, V), power(D, P), severity(V, Dly, Need), P >= Need.
outcome(saved) :- holds(D, V, Dly), chosen_defense(D), chosen_visitor(V), delay(Dly).
outcome(lost) :- not outcome(saved).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for visitor_id, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", visitor_id))
        lines.append(asp.fact("hunger", visitor_id, visitor.hunger))
    for defense_id, defense in DEFENSES.items():
        lines.append(asp.fact("defense", defense_id))
        lines.append(asp.fact("sense", defense_id, defense.sense))
        lines.append(asp.fact("power", defense_id, defense.power))
        for vid in sorted(defense.works_for):
            lines.append(asp.fact("works_for", defense_id, vid))
    for place_id in PLACES:
        for visitor_id in VISITORS:
            if visitor_can_reach(place_id, visitor_id):
                lines.append(asp.fact("reachable", place_id, visitor_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_defense", params.defense),
        asp.fact("chosen_visitor", params.visitor),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if effective_defense(params.defense, params.visitor, params.delay) else "lost"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child builds a garden defense, with gentle rhyme and either a happy or sad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--defense", choices=DEFENSES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="How late the defense is finished.")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.visitor and not hazard_exists(args.place, args.visitor):
        raise StoryError(explain_place(args.place, args.visitor))
    if args.defense and DEFENSES[args.defense].sense < SENSE_MIN:
        raise StoryError(explain_defense(args.defense))
    if args.visitor and args.defense and args.visitor not in DEFENSES[args.defense].works_for:
        raise StoryError(explain_mismatch(args.defense, args.visitor))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plant is None or combo[1] == args.plant)
        and (args.visitor is None or combo[2] == args.visitor)
        and (args.defense is None or combo[3] == args.defense)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, plant_id, visitor_id, defense_id = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        place=place_id,
        plant=plant_id,
        visitor=visitor_id,
        defense=defense_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        plant_cfg = PLANTS[params.plant]
        visitor_cfg = VISITORS[params.visitor]
        defense = DEFENSES[params.defense]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc.args[0]})") from exc

    if not hazard_exists(params.place, params.visitor):
        raise StoryError(explain_place(params.place, params.visitor))
    if defense.sense < SENSE_MIN:
        raise StoryError(explain_defense(params.defense))
    if params.visitor not in defense.works_for:
        raise StoryError(explain_mismatch(params.defense, params.visitor))

    world = tell(
        place=place,
        plant_cfg=plant_cfg,
        visitor_cfg=visitor_cfg,
        defense_id=params.defense,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
    )
    child = world.facts["child"]
    story_text = world.render().replace("child", child.label)
    story_text = story_text.replace("parent", world.facts["parent"].label_word)
    return StorySample(
        params=params,
        story=story_text,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve on seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, plant, visitor, defense) combos:\n")
        for place_id, plant_id, visitor_id, defense_id in combos:
            print(f"  {place_id:8} {plant_id:12} {visitor_id:8} {defense_id}")
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
            header = f"### {p.child_name}: {p.plant} vs {p.visitor} with {p.defense} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
