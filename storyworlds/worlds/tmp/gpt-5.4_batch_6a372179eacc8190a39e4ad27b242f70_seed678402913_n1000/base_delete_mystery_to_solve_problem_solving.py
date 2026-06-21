#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py
============================================================================

A small folk-tale-style story world about a village mystery: food keeps going
missing from a storehouse at the base of a hill, and a child solves the problem
by noticing clues before anyone deletes the chalk tally on the counting board.

The world model prefers a few strong, reasonable combinations:
- a culprit that would really want the missing food
- clues that match that culprit
- a fix that honestly prevents the same trouble next time

Run it
------
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py --goods turnips --culprit goat
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py --culprit raven --goods grain
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py --qa --json
    python storyworlds/worlds/gpt-5.4/base_delete_mystery_to_solve_problem_solving.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
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
class Place:
    id: str
    village_line: str
    storehouse: str
    path: str
    clue_surface: str
    weather_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goods:
    id: str
    label: str
    phrase: str
    container: str
    tally_word: str
    stolen_verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    kind: str
    appetite_for: set[str]
    clue: str
    clue_line: str
    sound: str
    hideout: str
    fix_ids: set[str]
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    works_for: set[str]
    action_line: str
    ending_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    goods = world.get("goods")
    if goods.meters["missing"] >= THRESHOLD:
        for eid in ("child", "elder"):
            sig = ("worry", eid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get(eid).memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_clue_suspicion(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["noticed"] >= THRESHOLD:
        sig = ("suspect",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["curiosity"] += 1
            world.get("elder").memes["hope"] += 1
            out.append("__suspect__")
    return out


def _r_fix_relief(world: World) -> list[str]:
    out: list[str] = []
    gate = world.get("fix")
    goods = world.get("goods")
    culprit = world.get("culprit")
    if gate.meters["set"] >= THRESHOLD and culprit.meters["caught"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            goods.meters["safe"] += 1
            world.get("child").memes["relief"] += 1
            world.get("elder").memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_suspicion", tag="mystery", apply=_r_clue_suspicion),
    Rule(name="fix_relief", tag="resolution", apply=_r_fix_relief),
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
    "hill": Place(
        id="hill",
        village_line="At the base of the green hill stood a village of round ovens and little red roofs.",
        storehouse="the stone storehouse beside the well",
        path="a narrow path curling around the hill",
        clue_surface="the damp earth by the threshold",
        weather_line="Mist still clung to the grass from the cool morning.",
        tags={"village", "hill"},
    ),
    "river": Place(
        id="river",
        village_line="At the base of the riverbank stood a village where reeds whispered and boats rocked softly.",
        storehouse="the cool grain shed near the ferry post",
        path="a pebbled lane beside the water",
        clue_surface="the soft mud near the door",
        weather_line="The river breathed a silver fog into the morning air.",
        tags={"village", "river"},
    ),
    "pinewood": Place(
        id="pinewood",
        village_line="At the base of the dark pinewood stood a village with smoke curling from every chimney.",
        storehouse="the wooden food shed near the bread oven",
        path="a needle-strewn track between the pines",
        clue_surface="the powdery dust on the floorboards",
        weather_line="The trees held the night smell of resin and rain.",
        tags={"village", "pinewood"},
    ),
}

GOODS = {
    "turnips": Goods(
        id="turnips",
        label="turnips",
        phrase="a basket of white turnips",
        container="basket",
        tally_word="turnips",
        stolen_verb="nibbled away",
        tags={"turnip", "vegetable"},
    ),
    "grain": Goods(
        id="grain",
        label="grain",
        phrase="a bin of winter grain",
        container="bin",
        tally_word="scoops of grain",
        stolen_verb="eaten down",
        tags={"grain", "food"},
    ),
    "honeycakes": Goods(
        id="honeycakes",
        label="honeycakes",
        phrase="a tray of round honeycakes",
        container="tray",
        tally_word="honeycakes",
        stolen_verb="picked away",
        tags={"honeycake", "cake"},
    ),
}

CULPRITS = {
    "goat": Culprit(
        id="goat",
        label="a shaggy goat",
        kind="animal",
        appetite_for={"turnips"},
        clue="hoofprints",
        clue_line="In the damp ground were neat split hoofprints, and one turnip leaf lay torn beside them.",
        sound="soft crunching",
        hideout="behind the brewer's fence",
        fix_ids={"latch_gate", "high_shelf"},
        reveal_line="From behind the fence came a beard, two bright eyes, and a guilty chew-chew-chew.",
        tags={"goat", "hoofprints"},
    ),
    "donkey": Culprit(
        id="donkey",
        label="a gray donkey",
        kind="animal",
        appetite_for={"grain"},
        clue="long gray hair",
        clue_line="Across the lid of the grain bin lay a few long gray hairs beside deep round hoof marks.",
        sound="a sleepy snort",
        hideout="near the mill cart",
        fix_ids={"bar_door", "latch_gate"},
        reveal_line="By the mill cart stood a gray donkey with grain dust on its whiskers.",
        tags={"donkey", "hoofprints", "grain"},
    ),
    "raven": Culprit(
        id="raven",
        label="a shiny raven",
        kind="animal",
        appetite_for={"honeycakes"},
        clue="black feathers",
        clue_line="On the sill glittered two black feathers, and sweet crumbs shone in the dust like tiny stars.",
        sound="a sharp caw",
        hideout="up on the roof beam",
        fix_ids={"cover_tray", "mend_roof"},
        reveal_line="Above them, on the roof beam, a shiny raven cocked its head with a crumb on its beak.",
        tags={"raven", "feather"},
    ),
}

FIXES = {
    "latch_gate": Fix(
        id="latch_gate",
        label="a tight new gate-latch",
        sense=2,
        works_for={"goat", "donkey"},
        action_line="They fastened a tight new latch on the yard gate and led the hungry wanderer back outside.",
        ending_line="After that, the gate clicked shut each evening, and no hungry muzzle reached the food shed again.",
        qa_line="They solved the problem by closing the wandering animal out with a tight gate-latch.",
        tags={"latch", "gate"},
    ),
    "high_shelf": Fix(
        id="high_shelf",
        label="a high hanging shelf",
        sense=2,
        works_for={"goat"},
        action_line="They hung the basket from a high shelf where eager teeth could not reach it.",
        ending_line="After that, the turnips swung safely above the floor, far beyond nibbling teeth.",
        qa_line="They solved the problem by hanging the turnips high where the goat could not reach them.",
        tags={"shelf", "storage"},
    ),
    "bar_door": Fix(
        id="bar_door",
        label="a stout wooden bar",
        sense=3,
        works_for={"donkey"},
        action_line="They slid a stout wooden bar across the shed door and swept the spilled grain away from the crack.",
        ending_line="After that, the barred door held firm, and the grain stayed in its bin for winter.",
        qa_line="They solved the problem by barring the shed door so the donkey could not nose it open.",
        tags={"door", "bar"},
    ),
    "cover_tray": Fix(
        id="cover_tray",
        label="a cloth cover",
        sense=2,
        works_for={"raven"},
        action_line="They covered the tray with a cloth and tucked the edges down so no beak could steal a cake.",
        ending_line="After that, the honeycakes rested under cloth like little moons under a cloud.",
        qa_line="They solved the problem by covering the honeycakes so the raven could not peck them.",
        tags={"cloth", "cover"},
    ),
    "mend_roof": Fix(
        id="mend_roof",
        label="a patched roof hole",
        sense=3,
        works_for={"raven"},
        action_line="They patched the loose place in the roof and brushed every sweet crumb from the beam below it.",
        ending_line="After that, no wing slipped through the roof, and the cakes stayed on the tray.",
        qa_line="They solved the problem by patching the roof hole the raven had been using.",
        tags={"roof", "patch"},
    ),
    "splash_water": Fix(
        id="splash_water",
        label="a splash of water",
        sense=1,
        works_for=set(),
        action_line="They splashed water at the doorway, but that did not truly solve anything.",
        ending_line="The doorway dried, yet the real trouble would have returned the next night.",
        qa_line="They only splashed water, which would not stop a hungry animal from coming back.",
        tags={"water"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tala", "Rosa", "Nia", "Asha", "Pia", "Suri"]
BOY_NAMES = ["Toma", "Milo", "Niko", "Jori", "Pavel", "Arlo", "Beni", "Sami"]
TRAITS = ["patient", "careful", "curious", "thoughtful", "steady", "bright"]


def likes_goods(culprit: Culprit, goods: Goods) -> bool:
    return goods.id in culprit.appetite_for


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def valid_fix(culprit: Culprit, fix: Fix) -> bool:
    return fix.id in culprit.fix_ids and culprit.id in fix.works_for and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for goods_id, goods in GOODS.items():
            for culprit_id, culprit in CULPRITS.items():
                if not likes_goods(culprit, goods):
                    continue
                for fix_id, fix in FIXES.items():
                    if valid_fix(culprit, fix):
                        combos.append((place_id, goods_id, culprit_id, fix_id))
    return combos


def explain_rejection(goods: Goods, culprit: Culprit) -> str:
    return (
        f"(No story: {culprit.label.capitalize()} would not be the likely thief of {goods.label}. "
        f"The mystery should follow a believable appetite so the clues and solution make sense.)"
    )


def explain_fix_rejection(culprit: Culprit, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try a sturdier solution such as {better}.)"
        )
    return (
        f"(No story: {fix.label} does not honestly stop {culprit.label} from returning. "
        f"The ending must solve the mystery's problem, not only wave at it.)"
    )


def predict_thief(world: World, culprit_id: str) -> dict:
    sim = world.copy()
    culprit = sim.get("culprit")
    if culprit.attrs.get("config_id") == culprit_id:
        sim.get("goods").meters["missing"] += 1
        sim.get("clue").meters["noticed"] += 1
        propagate(sim, narrate=False)
    return {
        "missing": sim.get("goods").meters["missing"],
        "clue": sim.get("clue").meters["noticed"],
        "worry": sim.get("child").memes["worry"] + sim.get("elder").memes["worry"],
    }


def opening(world: World, child: Entity, elder: Entity, goods: Goods) -> None:
    world.say(PLACES[world.place.id].village_line)
    world.say(
        f"There {child.id} lived with {child.pronoun('possessive')} {elder.label_word}, "
        f"and each dusk they counted {goods.tally_word} in {world.place.storehouse}."
    )
    world.say(world.place.weather_line)


def counting_board(world: World, child: Entity, elder: Entity, goods: Goods) -> None:
    world.say(
        f"On the wall hung a little chalk board with white marks for every {goods.tally_word}. "
        f"That morning one mark had to be crossed away, because some of the {goods.label} were gone."
    )
    world.say(
        f'"Do not delete that mark yet," said {child.id}. "Let it stay until we learn who took the food."'
    )
    elder.memes["respect"] += 1
    world.facts["delete_line"] = True


def discover_loss(world: World, goods_ent: Entity, goods: Goods, child: Entity, elder: Entity) -> None:
    goods_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they lifted the lid, they found that the {goods.phrase} had been {goods.stolen_verb}. "
        f"Neither lock nor hinge was broken, which made the matter stranger still."
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} felt a small worried flutter, but {child.pronoun()} knelt to look more closely instead of guessing."
        )
    if elder.memes["worry"] >= THRESHOLD:
        world.say(
            f"{elder.label_word.capitalize()} frowned and said, "
            f'"A mystery is best met with open eyes and a slow breath."'
        )


def inspect_clue(world: World, child: Entity, elder: Entity, culprit_cfg: Culprit) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    world.facts["clue_kind"] = culprit_cfg.clue
    propagate(world, narrate=False)
    world.say(
        f"Near {world.place.clue_surface}, {child.id} found the first true sign. {culprit_cfg.clue_line}"
    )
    world.say(
        f'{child.id} touched the mark lightly and whispered, "This clue belongs to someone real, not to a ghost in a tale."'
    )


def reason_out(world: World, child: Entity, elder: Entity, goods: Goods, culprit_cfg: Culprit) -> None:
    pred = predict_thief(world, culprit_cfg.id)
    child.memes["reasoning"] += 1
    elder.memes["hope"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{child.id} looked from the missing {goods.label} to the {culprit_cfg.clue} and thought aloud. '
        f'"Who loves {goods.label}, walks this way, and would come quietly before breakfast?"'
    )
    world.say(
        f'{elder.label_word.capitalize()} nodded. "Not magic," {elder.pronoun()} said. '
        f'"Tracks, crumbs, and habits. Let us follow what the world is telling us."'
    )


def follow_path(world: World, child: Entity, elder: Entity, culprit_cfg: Culprit) -> None:
    child.memes["bravery"] += 1
    elder.memes["trust"] += 1
    world.say(
        f"So they followed the signs along {world.place.path}. Soon they heard {culprit_cfg.sound} near {culprit_cfg.hideout}."
    )
    world.say(culprit_cfg.reveal_line)
    culprit = world.get("culprit")
    culprit.meters["caught"] += 1
    world.facts["solved"] = True


def choose_fix(world: World, child: Entity, elder: Entity, fix_cfg: Fix) -> None:
    gate = world.get("fix")
    gate.meters["set"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Then the riddle has an answer," said {child.id}. "Now the answer needs a good ending."'
    )
    world.say(fix_cfg.action_line)
    if world.get("goods").meters["safe"] >= THRESHOLD:
        world.say(
            f"{elder.label_word.capitalize()} smiled, proud that they had mended the trouble instead of merely scolding at it."
        )


def closing(world: World, child: Entity, elder: Entity, goods: Goods, fix_cfg: Fix) -> None:
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"That evening they went back to the chalk board in the warm lamplight."
    )
    world.say(
        f'"Now we may delete the old mark," said {elder.label_word}, "for we know the truth and have guarded the rest."'
    )
    world.say(
        f"{child.id} rubbed away the sad chalk line and drew a bright new one beside it. {fix_cfg.ending_line}"
    )
    world.say(
        f"And so the people at the base of the village hill said that a careful mind can be as useful as any key."
    )


def tell(
    place: Place,
    goods: Goods,
    culprit_cfg: Culprit,
    fix_cfg: Fix,
    child_name: str = "Lina",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    elder_name: str = "Nona",
    trait: str = "curious",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"display": child_name},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_name,
        role="elder",
        attrs={"display": elder_name},
    ))
    goods_ent = world.add(Entity(
        id="goods",
        type="goods",
        label=goods.label,
        phrase=goods.phrase,
        role="goods",
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=culprit_cfg.clue,
        role="clue",
    ))
    culprit = world.add(Entity(
        id="culprit",
        type=culprit_cfg.kind,
        label=culprit_cfg.label,
        role="culprit",
        attrs={"config_id": culprit_cfg.id},
    ))
    fix = world.add(Entity(
        id="fix",
        type="fix",
        label=fix_cfg.label,
        role="fix",
        attrs={"config_id": fix_cfg.id},
    ))

    world.facts.update(
        child=child,
        elder=elder,
        goods_cfg=goods,
        culprit_cfg=culprit_cfg,
        fix_cfg=fix_cfg,
        place_cfg=place,
        solved=False,
    )

    opening(world, child, elder, goods)
    counting_board(world, child, elder, goods)

    world.para()
    discover_loss(world, goods_ent, goods, child, elder)
    inspect_clue(world, child, elder, culprit_cfg)
    reason_out(world, child, elder, goods, culprit_cfg)

    world.para()
    follow_path(world, child, elder, culprit_cfg)
    choose_fix(world, child, elder, fix_cfg)

    world.para()
    closing(world, child, elder, goods, fix_cfg)

    world.facts.update(
        mystery_solved=world.facts.get("solved", False),
        safe=goods_ent.meters["safe"] >= THRESHOLD,
        delete_used=world.facts.get("delete_line", False),
        clue_kind=world.facts.get("clue_kind", culprit_cfg.clue),
    )
    return world


@dataclass
class StoryParams:
    place: str
    goods: str
    culprit: str
    fix: str
    child_name: str
    child_gender: str
    elder_type: str
    elder_name: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    goods = f["goods_cfg"]
    culprit = f["culprit_cfg"]
    return [
        f'Write a short folk-tale-style mystery for a 3-to-5-year-old that includes the words "base" and "delete".',
        f"Tell a gentle village mystery where {child.attrs['display']} and {elder.label_word} notice missing {goods.label}, follow clues, and solve the problem with calm thinking.",
        f"Write a story set at the base of a hill where a child solves the mystery of stolen {goods.label} and discovers that {culprit.label} was responsible.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    goods = f["goods_cfg"]
    culprit = f["culprit_cfg"]
    fix = f["fix_cfg"]
    child_name = child.attrs["display"]
    elder_name = elder.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name} and {elder_name}, who live in a village storehouse world at the base of the hill or bank. Together they face a small mystery and solve it with patience."
        ),
        (
            f"What was the mystery?",
            f"Some of the {goods.label} kept disappearing from the village storehouse. That was strange because nothing looked broken, so they had to search for a hidden cause."
        ),
        (
            'Why did the child say, "Do not delete that mark yet"?',
            f"{child_name} wanted to keep the chalk tally as a sign that something was wrong. The mark stayed on the board until they found the truth about the missing {goods.label}."
        ),
        (
            "What clue helped them solve the mystery?",
            f"They found {f['clue_kind']} near the storehouse. That clue matched the thief's habits and gave them a real path to follow instead of a wild guess."
        ),
        (
            "Who had taken the food, and how did they know?",
            f"It was {culprit.label}. They knew because the clue near the door fit that animal, and the trail led them straight to the hiding place."
        ),
        (
            "How did they solve the problem after they knew the answer?",
            f"{fix.qa_line} That changed the storehouse itself, so the same trouble would not happen again."
        ),
        (
            "How did the story end?",
            f"They went back to the chalk board, deleted the sad old mark, and made a fresh one after the mystery was solved. The ending shows that the food was safe and the village had learned a wiser way."
        ),
    ]
    return qa


KNOWLEDGE = {
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that you do not understand at first. You solve it by noticing clues and thinking carefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you find an answer. Footprints, feathers, and crumbs can all be clues."
        )
    ],
    "hoofprints": [
        (
            "What are hoofprints?",
            "Hoofprints are marks left on the ground by an animal with hooves, like a goat or a donkey. They can show where the animal walked."
        )
    ],
    "feather": [
        (
            "Why can a feather be a clue?",
            "A feather can show that a bird was nearby. If food is missing, a feather may help you guess which bird came."
        )
    ],
    "gate": [
        (
            "What does a gate-latch do?",
            "A gate-latch keeps a gate shut. If it closes tightly, wandering animals cannot push their way in."
        )
    ],
    "roof": [
        (
            "Why would patching a roof help?",
            "Patching a hole in the roof closes an opening. That keeps rain out and can also stop birds from sneaking inside."
        )
    ],
    "storage": [
        (
            "Why put food on a high shelf?",
            "A high shelf keeps food farther from noses and teeth on the ground. It is a simple way to protect food from hungry animals."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means finding out what is wrong and choosing a fix that really helps. It is more useful than guessing or blaming."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "clue", "hoofprints", "feather", "gate", "roof", "storage", "problem_solving"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "clue", "problem_solving"}
    culprit = f["culprit_cfg"]
    fix = f["fix_cfg"]
    if culprit.id in {"goat", "donkey"}:
        tags.add("hoofprints")
    if culprit.id == "raven":
        tags.add("feather")
    if fix.id == "latch_gate":
        tags.add("gate")
    if fix.id == "mend_roof":
        tags.add("roof")
    if fix.id == "high_shelf":
        tags.add("storage")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
likes(C, G) :- appetite(C, G).
usable_fix(C, F) :- fix(F), works_for(F, C), sense(F, S), sense_min(M), S >= M.
valid(P, G, C, F) :- place(P), goods(G), culprit(C), fix(F), likes(C, G), usable_fix(C, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for goods_id in GOODS:
        lines.append(asp.fact("goods", goods_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for goods_id in sorted(culprit.appetite_for):
            lines.append(asp.fact("appetite", culprit_id, goods_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for culprit_id in sorted(fix.works_for):
            lines.append(asp.fact("works_for", fix_id, culprit_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        place="hill",
        goods="turnips",
        culprit="goat",
        fix="high_shelf",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        elder_name="Nona",
        trait="curious",
    ),
    StoryParams(
        place="river",
        goods="grain",
        culprit="donkey",
        fix="bar_door",
        child_name="Milo",
        child_gender="boy",
        elder_type="grandfather",
        elder_name="Ivo",
        trait="careful",
    ),
    StoryParams(
        place="pinewood",
        goods="honeycakes",
        culprit="raven",
        fix="mend_roof",
        child_name="Tala",
        child_gender="girl",
        elder_type="grandmother",
        elder_name="Bela",
        trait="thoughtful",
    ),
    StoryParams(
        place="hill",
        goods="turnips",
        culprit="goat",
        fix="latch_gate",
        child_name="Arlo",
        child_gender="boy",
        elder_type="grandfather",
        elder_name="Petar",
        trait="steady",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk-tale mystery solved by clues and problem solving."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goods and args.culprit:
        goods = GOODS[args.goods]
        culprit = CULPRITS[args.culprit]
        if not likes_goods(culprit, goods):
            raise StoryError(explain_rejection(goods, culprit))
    if args.fix:
        fix = FIXES[args.fix]
        if fix.sense < SENSE_MIN:
            culprit = CULPRITS[args.culprit] if args.culprit else next(iter(CULPRITS.values()))
            raise StoryError(explain_fix_rejection(culprit, fix))
    if args.culprit and args.fix:
        culprit = CULPRITS[args.culprit]
        fix = FIXES[args.fix]
        if not valid_fix(culprit, fix):
            raise StoryError(explain_fix_rejection(culprit, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.goods is None or combo[1] == args.goods)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, goods_id, culprit_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    elder_name = rng.choice(
        ["Nona", "Bela", "Rada", "Mara"] if elder_type == "grandmother" else ["Ivo", "Petar", "Stefan", "Miro"]
    )
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        goods=goods_id,
        culprit=culprit_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        elder_name=elder_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        goods = GOODS[params.goods]
        culprit = CULPRITS[params.culprit]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not likes_goods(culprit, goods):
        raise StoryError(explain_rejection(goods, culprit))
    if not valid_fix(culprit, fix):
        raise StoryError(explain_fix_rejection(culprit, fix))

    world = tell(
        place=place,
        goods=goods,
        culprit_cfg=culprit,
        fix_cfg=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        elder_name=params.elder_name,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if "base" not in sample.story.lower() or "delete" not in sample.story.lower():
            raise StoryError("(Seed words missing from generated story.)")
        print("OK: default random generation smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, goods, culprit, fix) combos:\n")
        for place, goods, culprit, fix in combos:
            print(f"  {place:8} {goods:10} {culprit:8} {fix}")
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
            p = sample.params
            header = f"### {p.child_name}: {p.goods} mystery at {p.place} ({p.culprit}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
