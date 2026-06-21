#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hutch_aviary_lesson_learned_foreshadowing_inner_monologue.py
========================================================================================

A small folk-tale storyworld about a child caretaker in a cottage garden with a
rabbit hutch and a bird aviary. The child is tempted to save time by leaving a
latch loose "just for a blink." A warning sign foreshadows trouble, the child's
inner monologue reveals the temptation, and the ending proves the lesson:
kindness must be careful, not hurried.

Run it
------
python storyworlds/worlds/gpt-5.4/hutch_aviary_lesson_learned_foreshadowing_inner_monologue.py
python storyworlds/worlds/gpt-5.4/hutch_aviary_lesson_learned_foreshadowing_inner_monologue.py --target hutch --hazard fox
python storyworlds/worlds/gpt-5.4/hutch_aviary_lesson_learned_foreshadowing_inner_monologue.py --response chase
python storyworlds/worlds/gpt-5.4/hutch_aviary_lesson_learned_foreshadowing_inner_monologue.py --all
python storyworlds/worlds/gpt-5.4/hutch_aviary_lesson_learned_foreshadowing_inner_monologue.py --verify
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    home: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Garden:
    id: str
    place: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    home_word: str
    resident_kind: str
    resident_phrase: str
    resident_name: str
    open_text: str
    return_text: str
    lesson_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    target: str
    sign: str
    omen: str
    threat_text: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    target: str
    sense: int
    power: int
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
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
        clone = World(self.garden)
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


def _r_escape(world: World) -> list[str]:
    out: list[str] = []
    resident = world.entities.get("resident")
    if resident is None:
        return out
    target_id = world.facts.get("target_id")
    hazard_id = world.facts.get("hazard_id")
    if not target_id or not hazard_id:
        return out
    target = TARGETS[target_id]
    hazard = HAZARDS[hazard_id]
    if hazard.target != target.id:
        return out
    enclosure = world.get(target.id)
    if enclosure.meters["open"] < THRESHOLD:
        return out
    sig = ("escape", target.id, hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    resident.meters["escaped"] += 1
    resident.meters["lost"] += 1
    resident.memes["fear"] += 1
    child = world.get("child")
    child.memes["fear"] += 1
    out.append("__escape__")
    return out


CAUSAL_RULES = [
    Rule(name="escape", tag="physical", apply=_r_escape),
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


def valid_hazard_for_target(target: Target, hazard: Hazard) -> bool:
    return hazard.target == target.id


def sensible_responses_for_target(target_id: str) -> list[Response]:
    return [
        response
        for response in RESPONSES.values()
        if response.target == target_id and response.sense >= SENSE_MIN
    ]


def best_response_for_target(target_id: str) -> Response:
    candidates = sensible_responses_for_target(target_id)
    if not candidates:
        raise StoryError(f"(No sensible response is registered for {target_id}.)")
    return max(candidates, key=lambda r: (r.sense, r.power, r.id))


def risk_severity(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def is_recovered(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= risk_severity(hazard, delay)


def explain_rejection(target: Target, hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.id} is a danger for the {TARGETS[hazard.target].home_word}, "
        f"not for the {target.home_word}. Pick a hazard that truly threatens that home.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses_for_target(response.target)))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer, wiser response such as {better}.)"
    )


def predict_escape(world: World, target_id: str, hazard_id: str) -> dict:
    sim = world.copy()
    sim.facts["target_id"] = target_id
    sim.facts["hazard_id"] = hazard_id
    sim.get(target_id).meters["open"] += 1
    propagate(sim, narrate=False)
    resident = sim.get("resident")
    return {
        "escaped": resident.meters["escaped"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity, target: Target) -> None:
    world.say(
        f"In the days when people still listened to the wind for advice, {child.id} lived with "
        f"{child.pronoun('possessive')} {helper.label_word} beside {world.garden.place}. "
        f"There stood an old {TARGETS['hutch'].home_word} under the pear tree and a painted "
        f"{TARGETS['aviary'].home_word} near the herbs."
    )
    world.say(
        f"In the {TARGETS['hutch'].home_word} lived {TARGETS['hutch'].resident_name}, "
        f"{TARGETS['hutch'].resident_phrase}; in the {TARGETS['aviary'].home_word} fluttered "
        f"{TARGETS['aviary'].resident_phrase}. {child.id} loved them all and liked to think "
        f"the little garden beat like one small heart."
    )
    child.memes["care"] += 1


def chore_setup(world: World, child: Entity, target: Target) -> None:
    world.say(
        f"Each evening {child.id} carried water and feed from one home to the other. "
        f"That dusk, {child.pronoun('possessive')} hands were full, and the path between the "
        f"{TARGETS['hutch'].home_word} and the {TARGETS['aviary'].home_word} seemed longer than usual."
    )
    world.say(
        f"{child.id} paused by the {target.home_word} and looked at the latch. "
        f'"If I leave it loose only for a blink," {child.pronoun()} thought, '
        f'"I can be quick as a swallow and no harm will wake."'
    )
    child.memes["hurry"] += 1


def foreshadow(world: World, hazard: Hazard) -> None:
    world.say(
        f"But the old stories had already cleared their throats: {hazard.sign}. "
        f"{hazard.omen}"
    )
    world.facts["foreshadowing"] = hazard.sign


def warn(world: World, child: Entity, helper: Entity, target: Target, hazard: Hazard) -> None:
    pred = predict_escape(world, target.id, hazard.id)
    world.facts["predicted_escape"] = pred["escaped"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["caution"] += 1
    world.say(
        f'{helper.label_word.capitalize()} had often said, "A kind hand must also be a careful hand. '
        f'The {target.home_word} keeps its small life safe."'
    )
    if pred["escaped"]:
        world.say(
            f"{child.id} remembered those words and felt them tug like a sleeve. "
            f"{hazard.threat_text}"
        )


def leave_latch(world: World, child: Entity, target: Target) -> None:
    enclosure = world.get(target.id)
    enclosure.meters["open"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"Still, hurry spoke louder for one foolish moment. {child.id} tucked the latch aside, "
        f"balanced the pail on one hip, and turned away from the {target.home_word}."
    )


def keep_latch(world: World, child: Entity, target: Target) -> None:
    child.memes["relief"] += 1
    world.say(
        f"Then {child.id} drew a long breath, set the pail down, and fastened the latch firmly. "
        f'"No," {child.pronoun()} told {child.pronoun("object")}self, "quick is not the same as wise."'
    )


def escape(world: World, target: Target, hazard: Hazard) -> None:
    propagate(world, narrate=False)
    resident = world.get("resident")
    world.say(
        f"Before the pail had stopped swinging, the warning came true. {hazard.threat_text} "
        f"{target.open_text}"
    )
    if resident.meters["escaped"] >= THRESHOLD:
        if target.id == "hutch":
            world.say(
                f"{target.resident_name} flashed away like a scrap of moonlight, and the grass "
                f"closed behind {resident.pronoun('object')}."
            )
        else:
            world.say(
                f"The air burst into wings. For one startled breath, feathers spun above the thyme "
                f"and the open roof of the dusk."
            )


def recover(world: World, child: Entity, helper: Entity, target: Target, response: Response) -> None:
    resident = world.get("resident")
    resident.meters["lost"] = 0.0
    resident.meters["escaped"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came softly, not with scolding first but with sense. "
        f"{response.success_text}"
    )
    world.say(
        f"Soon {target.return_text} The evening let out its breath, and so did {child.id}."
    )


def fail_search(world: World, child: Entity, helper: Entity, target: Target, response: Response) -> None:
    child.memes["fear"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{helper.label_word.capitalize()} tried to help at once. {response.fail_text}"
    )
    world.say(
        f"They searched until the moon rose over the beans, but the garden stayed too wide and too dim. "
        f"{child.id} went to bed with the empty {target.home_word} in {child.pronoun('possessive')} mind."
    )
    world.para()
    world.say(
        f"At dawn, when the world was pale as milk, {target.return_text} {child.id} closed the latch with both hands."
    )


def lesson(world: World, child: Entity, helper: Entity, target: Target, recovered: bool) -> None:
    child.memes["love"] += 1
    world.para()
    if recovered:
        world.say(
            f'{helper.label_word.capitalize()} laid a hand on {child.id}\'s shoulder. '
            f'"Remember this," {helper.pronoun()} said. "{target.lesson_line}"'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} sat beside {child.id} on the step. '
            f'"Remember this," {helper.pronoun()} said. "{target.lesson_line}"'
        )
    world.say(
        f"{child.id} nodded. The lesson stung because it was true, and truths worth keeping often do."
    )


def ending(world: World, child: Entity, target: Target) -> None:
    world.say(
        f"After that night, {child.id} never praised hurry over care again. "
        f"Whenever {child.pronoun()} passed the {TARGETS['hutch'].home_word} and the "
        f"{TARGETS['aviary'].home_word}, {child.pronoun()} touched each latch once, "
        f"and the small lives inside rested easy."
    )


def tell(
    garden: Garden,
    target: Target,
    hazard: Hazard,
    response: Response,
    child_name: str = "Anya",
    child_type: str = "girl",
    helper_type: str = "grandmother",
    delay: int = 0,
    heed_warning: bool = False,
) -> World:
    world = World(garden)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            label=child_name,
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label=helper_type,
            tags={"adult"},
        )
    )
    enclosure = world.add(
        Entity(
            id=target.id,
            kind="thing",
            type="enclosure",
            label=target.label,
            phrase=target.phrase,
            role="target",
            tags=set(target.tags),
        )
    )
    resident = world.add(
        Entity(
            id="resident",
            kind="thing",
            type=target.resident_kind,
            label=target.resident_name,
            phrase=target.resident_phrase,
            home=target.id,
            role="resident",
            tags=set(target.tags),
        )
    )

    world.facts["garden"] = garden
    world.facts["target_id"] = target.id
    world.facts["hazard_id"] = hazard.id
    world.facts["response_id"] = response.id
    world.facts["delay"] = delay
    world.facts["heed_warning"] = heed_warning

    introduce(world, child, helper, target)
    world.para()
    chore_setup(world, child, target)
    foreshadow(world, hazard)
    warn(world, child, helper, target, hazard)

    if heed_warning:
        keep_latch(world, child, target)
        outcome = "averted"
        recovered_now = True
    else:
        leave_latch(world, child, target)
        world.para()
        escape(world, target, hazard)
        recovered_now = is_recovered(response, hazard, delay)
        world.para()
        if recovered_now:
            recover(world, child, helper, target, response)
            outcome = "recovered"
        else:
            fail_search(world, child, helper, target, response)
            outcome = "overnight"

    lesson(world, child, helper, target, recovered_now)
    ending(world, child, target)

    world.facts.update(
        child=child,
        helper=helper,
        target_cfg=target,
        hazard_cfg=hazard,
        response_cfg=response,
        escaped=resident.meters["escaped"] >= THRESHOLD or outcome != "averted",
        outcome=outcome,
        resident_returned=recovered_now or outcome == "overnight",
        moral=target.lesson_line,
    )
    return world


@dataclass
class StoryParams:
    garden: str
    target: str
    hazard: str
    response: str
    child_name: str
    child_type: str
    helper_type: str
    delay: int = 0
    heed_warning: bool = False
    seed: Optional[int] = None


GARDENS = {
    "pear_orchard": Garden(
        id="pear_orchard",
        place="the edge of a pear orchard",
        image="pear leaves whispering over a narrow path",
        tags={"garden", "orchard"},
    ),
    "mill_lane": Garden(
        id="mill_lane",
        place="a small yard by the mill lane",
        image="dusty stones and a crooked well",
        tags={"garden", "village"},
    ),
    "river_bank": Garden(
        id="river_bank",
        place="a cottage garden above the river bank",
        image="mint by the path and reeds below",
        tags={"garden", "river"},
    ),
}

TARGETS = {
    "hutch": Target(
        id="hutch",
        label="rabbit hutch",
        phrase="the old rabbit hutch",
        home_word="hutch",
        resident_kind="rabbit",
        resident_phrase="a silver-gray rabbit called Moss",
        resident_name="Moss",
        open_text="The hutch stood open to the grass and the hedge",
        return_text="Moss came nosing back to the hutch for clover and the sound of the familiar bowl.",
        lesson_line="Love is not proved by opening every door; it is proved by guarding the right one.",
        tags={"hutch", "rabbit"},
    ),
    "aviary": Target(
        id="aviary",
        label="garden aviary",
        phrase="the painted garden aviary",
        home_word="aviary",
        resident_kind="bird",
        resident_phrase="three gold birds that sang at sunrise",
        resident_name="the gold birds",
        open_text="The aviary door fluttered wide against its hook",
        return_text="one by one the gold birds dipped back through the aviary door to the seed tray and the willow perch.",
        lesson_line="A gentle heart must also keep watch, or kindness will scatter like feathers in a gust.",
        tags={"aviary", "birds"},
    ),
}

HAZARDS = {
    "fox": Hazard(
        id="fox",
        target="hutch",
        sign="a fox print lay fresh in the soft earth by the beans",
        omen="Even the hens had gone quiet, as if the garden itself were holding its breath.",
        threat_text="From the hedge came the sly rustle of a hunting fox",
        severity=2,
        tags={"fox", "danger"},
    ),
    "gust": Hazard(
        id="gust",
        target="aviary",
        sign="the willow leaves turned their pale undersides to the sky",
        omen="A sharp wind worried the gate and made the chimes knock together like teeth.",
        threat_text="A sudden gust rolled down from the river",
        severity=2,
        tags={"wind", "danger"},
    ),
}

RESPONSES = {
    "clover_trail": Response(
        id="clover_trail",
        target="hutch",
        sense=3,
        power=2,
        success_text="She crouched low, laid a little trail of clover leaves, and waited without stamping or shouting.",
        fail_text="She laid out clover and called softly, but the hedge kept its secret till morning.",
        qa_text="Grandmother used a quiet clover trail and patience to draw Moss back.",
        tags={"clover", "patience"},
    ),
    "seed_bell": Response(
        id="seed_bell",
        target="aviary",
        sense=3,
        power=2,
        success_text="She rang the tiny feeding bell and held the seed pan still until the birds remembered home.",
        fail_text="She rang the feeding bell and lifted the seed pan, but the wind had carried the birds too high and too far to trust it before nightfall.",
        qa_text="Grandmother rang the feeding bell and held up the seed pan until the birds came home.",
        tags={"seed", "patience"},
    ),
    "chase": Response(
        id="chase",
        target="hutch",
        sense=1,
        power=1,
        success_text="She ran after the frightened creature with flapping skirts until it stopped.",
        fail_text="She ran after the frightened creature, but chasing only drove it farther from the yard.",
        qa_text="Someone chased after the frightened animal.",
        tags={"chasing"},
    ),
    "wave_arms": Response(
        id="wave_arms",
        target="aviary",
        sense=1,
        power=1,
        success_text="She waved her arms and hurried the birds back with noise.",
        fail_text="She waved her arms beneath the open sky, and the noise only scattered the birds farther.",
        qa_text="Someone tried to wave the birds back.",
        tags={"chasing"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Lina", "Tessa", "Nina", "Vera"]
BOY_NAMES = ["Ivo", "Milan", "Toma", "Pavel", "Nico", "Stefan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for garden_id in GARDENS:
        for target_id, target in TARGETS.items():
            for hazard_id, hazard in HAZARDS.items():
                if valid_hazard_for_target(target, hazard):
                    combos.append((garden_id, target_id, hazard_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.heed_warning:
        return "averted"
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    return "recovered" if is_recovered(response, hazard, params.delay) else "overnight"


KNOWLEDGE = {
    "hutch": [
        (
            "What is a hutch?",
            "A hutch is a small house or pen for an animal such as a rabbit. It keeps the animal safe from weather and danger.",
        )
    ],
    "aviary": [
        (
            "What is an aviary?",
            "An aviary is a large cage or house for birds, with room for them to perch and flutter. It protects them while giving them space.",
        )
    ],
    "fox": [
        (
            "Why is a fox dangerous to a rabbit?",
            "A fox hunts small animals. If a rabbit is left out in the open, a fox may chase it or catch it.",
        )
    ],
    "wind": [
        (
            "Why can strong wind be a problem for birds?",
            "A strong gust can startle birds and push them away from a safe place. Frightened birds may fly farther than they meant to.",
        )
    ],
    "patience": [
        (
            "Why is patience useful with frightened animals?",
            "Frightened animals do not think clearly when people rush at them. Quiet waiting helps them feel safe enough to come back.",
        )
    ],
    "latch": [
        (
            "Why does a latch matter?",
            "A latch keeps a door safely closed. Small careless moments can matter when a latch is all that stands between safety and danger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hutch", "aviary", "fox", "wind", "patience", "latch"]


def pair_narrative_name(target_id: str) -> str:
    return "Moss the rabbit" if target_id == "hutch" else "the gold birds"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    target = f["target_cfg"]
    hazard = f["hazard_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short folk tale for a 3-to-5-year-old that includes the words "hutch" and "aviary", uses foreshadowing and inner monologue, and ends with a lesson learned.',
            f"Tell a gentle folk-style story where {child.id} almost leaves the {target.home_word} unlatched, remembers a warning, and chooses care over hurry.",
            f'Write a story with the thought "quick is not the same as wise" and a calm ending that teaches a lesson about being careful with small creatures.',
        ]
    if outcome == "recovered":
        return [
            f'Write a short folk tale that includes a hutch, an aviary, foreshadowing, and inner monologue. A child makes a small mistake, a wise elder helps, and the story ends with a lesson learned.',
            f"Tell a story where {child.id} leaves the {target.home_word} loose to save time, {hazard.id} makes the danger real, and a calm grown-up fixes the problem wisely.",
            f'Write a child-facing cautionary tale about hurry, care, and home, ending with the lesson that kindness must also be careful.',
        ]
    return [
        f'Write a folk tale for young children using the words "hutch" and "aviary", with foreshadowing and inner monologue, where a careless choice leads to a long worried night and a lesson learned at dawn.',
        f"Tell a story where {child.id} leaves the {target.home_word} open, the warning sign comes true, and the small creature does not return until morning.",
        f'Write a gentle but serious story showing that one hurried mistake can trouble the whole night, even when things are made right in the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    target = f["target_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child caring for a hutch and an aviary, and {child.pronoun('possessive')} {helper.label_word} who teaches the lesson. The story follows one small mistake and what it changes.",
        ),
        (
            f"What was {child.id} thinking before the trouble began?",
            f"{child.id} told {child.pronoun('object')}self that leaving the latch loose for only a blink would save time. That inner thought shows how hurry tried to sound wise even when it was not.",
        ),
        (
            "What was the warning sign?",
            f"The warning sign was that {hazard.sign}. That foreshadowing hinted that the danger was already near before the latch was left loose.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"How did {child.id} stop the trouble before it started?",
                f"{child.id} remembered the warning, fastened the {target.home_word}, and chose care over hurry. Nothing escaped because the wise choice happened in time.",
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"What happened when {child.id} left the {target.home_word} open?",
                f"{pair_narrative_name(target.id)} got loose when {hazard.threat_text.lower()}. The danger became real because a safe home was left unguarded.",
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} help?",
                f"{response.qa_text} The calm method worked because frightened creatures trust familiar food and quiet more than noise and rushing.",
            )
        )
    else:
        qa.append(
            (
                f"Did the creature come back right away?",
                f"No. {helper.label_word.capitalize()} tried to help, but the creature stayed away until dawn. The long wait showed {child.id} how heavy one careless moment can feel.",
            )
        )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that {target.lesson_line} The story proves the lesson by showing what happened when hurry touched the latch.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    target = f["target_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response_cfg"]
    tags: set[str] = {"latch", target.id}
    if hazard.id == "fox":
        tags.add("fox")
    if hazard.id == "gust":
        tags.add("wind")
    if response.sense >= SENSE_MIN:
        tags.add("patience")
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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.home:
            bits.append(f"home={entity.home}")
        lines.append(f"  {entity.id:10} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        garden="pear_orchard",
        target="hutch",
        hazard="fox",
        response="clover_trail",
        child_name="Anya",
        child_type="girl",
        helper_type="grandmother",
        delay=0,
        heed_warning=False,
    ),
    StoryParams(
        garden="river_bank",
        target="aviary",
        hazard="gust",
        response="seed_bell",
        child_name="Toma",
        child_type="boy",
        helper_type="grandfather",
        delay=0,
        heed_warning=False,
    ),
    StoryParams(
        garden="mill_lane",
        target="hutch",
        hazard="fox",
        response="clover_trail",
        child_name="Mira",
        child_type="girl",
        helper_type="grandmother",
        delay=1,
        heed_warning=False,
    ),
    StoryParams(
        garden="pear_orchard",
        target="aviary",
        hazard="gust",
        response="seed_bell",
        child_name="Ivo",
        child_type="boy",
        helper_type="grandfather",
        delay=0,
        heed_warning=True,
    ),
]


ASP_RULES = r"""
valid(G, T, H) :- garden(G), target(T), hazard(H), threatens(H, T).

sensible_response(T, R) :- response(R), responds_to(R, T), sense(R, S), sense_min(M), S >= M.

recovered :- chosen_response(R), power(R, P), chosen_hazard(H), severity(H, Sev), delay(D), P >= Sev + D.
outcome(averted) :- heed_warning.
outcome(recovered) :- not heed_warning, recovered.
outcome(overnight) :- not heed_warning, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for garden_id in GARDENS:
        lines.append(asp.fact("garden", garden_id))
    for target_id in TARGETS:
        lines.append(asp.fact("target", target_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("threatens", hazard_id, hazard.target))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("responds_to", response_id, response.target))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_for_target(target_id: str) -> list[str]:
    import asp

    model = asp.one_model(
        asp_program(
            f"chosen_target({target_id}).",
            "#show sensible_response/2.",
        )
    )
    pairs = asp.atoms(model, "sensible_response")
    return sorted(r for t, r in pairs if t == target_id)


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            "heed_warning." if params.heed_warning else "",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    for target_id in TARGETS:
        clingo_sens = set(asp_sensible_for_target(target_id))
        python_sens = {r.id for r in sensible_responses_for_target(target_id)}
        if clingo_sens == python_sens:
            print(f"OK: sensible responses match for {target_id} ({sorted(clingo_sens)}).")
        else:
            rc = 1
            print(
                f"MISMATCH in sensible responses for {target_id}: "
                f"clingo={sorted(clingo_sens)} python={sorted(python_sens)}"
            )

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk tale about the hutch, the aviary, and the danger of hurry."
    )
    ap.add_argument("--garden", choices=GARDENS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the creature is loose before help settles the problem")
    ap.add_argument("--heed-warning", action="store_true", help="the child remembers the warning and fastens the latch in time")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (garden, target, hazard) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.hazard:
        target = TARGETS[args.target]
        hazard = HAZARDS[args.hazard]
        if not valid_hazard_for_target(target, hazard):
            raise StoryError(explain_rejection(target, hazard))

    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))
        if args.target and response.target != args.target:
            raise StoryError(
                f"(No story: response '{args.response}' fits the {response.target}, not the {args.target}.)"
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.garden is None or combo[0] == args.garden)
        and (args.target is None or combo[1] == args.target)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    garden_id, target_id, hazard_id = rng.choice(sorted(combos))
    target = TARGETS[target_id]

    if args.response:
        response_id = args.response
        if RESPONSES[response_id].target != target_id:
            raise StoryError(
                f"(No story: response '{response_id}' does not belong to the {target_id} branch.)"
            )
    else:
        response_id = rng.choice(sorted(r.id for r in sensible_responses_for_target(target_id)))

    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    heed_warning = bool(args.heed_warning)
    return StoryParams(
        garden=garden_id,
        target=target_id,
        hazard=hazard_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        delay=delay,
        heed_warning=heed_warning,
    )


def generate(params: StoryParams) -> StorySample:
    if params.garden not in GARDENS:
        raise StoryError(f"(Unknown garden '{params.garden}'.)")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target '{params.target}'.)")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard '{params.hazard}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")

    target = TARGETS[params.target]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]

    if not valid_hazard_for_target(target, hazard):
        raise StoryError(explain_rejection(target, hazard))
    if response.target != target.id:
        raise StoryError(
            f"(No story: response '{params.response}' does not fit the {target.home_word}.)"
        )
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        garden=GARDENS[params.garden],
        target=target,
        hazard=hazard,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        delay=params.delay,
        heed_warning=params.heed_warning,
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
        print(asp_program("", "#show valid/3.\n#show sensible_response/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (garden, target, hazard) combos:\n")
        for garden_id, target_id, hazard_id in combos:
            sensible = ", ".join(asp_sensible_for_target(target_id))
            print(f"  {garden_id:12} {target_id:7} {hazard_id:5}  [responses: {sensible}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            params = sample.params
            header = (
                f"### {params.child_name}: {params.target} / {params.hazard} / "
                f"{outcome_of(params)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
