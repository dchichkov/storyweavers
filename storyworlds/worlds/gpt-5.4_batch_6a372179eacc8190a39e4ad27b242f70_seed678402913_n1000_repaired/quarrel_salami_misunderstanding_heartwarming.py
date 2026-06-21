#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py
===========================================================================

A standalone story world about a small misunderstanding over salami that grows
into a quarrel and then softens into a warm ending. The world model tracks what
snack was prepared, what clue was left behind, who misunderstood what, and how a
calm grown-up or helper clears it up.

The core pattern is:

    wish to share a treat
    -> one piece goes missing or seems changed
    -> a child forms the wrong belief
    -> a quarrel starts
    -> a clue or helper reveals the truth
    -> the children repair the feeling and share food kindly

The domain stays narrow on purpose: fewer strong stories are better than a wide
catalog of weak ones.

Run it
------
    python storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py
    python storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py --snack sandwich --cause cat
    python storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py --cause wind --snack lunchbox
    python storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4/quarrel_salami_misunderstanding_heartwarming.py --verify
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
KIND_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "sister", "grandmother"}
        male = {"boy", "father", "dad", "man", "brother", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    part_word: str
    place: str
    setup: str
    safe_for: set[str] = field(default_factory=lambda: {"cat", "wind", "sibling", "parent_move"})
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    clue: str
    reveal: str
    true_actor: str
    kind: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    action: str
    ending: str
    kind: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"owner", "accused"}]

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


def _r_quarrel(world: World) -> list[str]:
    owner = world.get("owner")
    accused = world.get("accused")
    snack = world.get("snack")
    if owner.memes["blame"] < THRESHOLD or owner.memes["hurt"] < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["quarrel"] += 1
    accused.memes["quarrel"] += 1
    snack.meters["peace"] -= 1
    return ["__quarrel__"]


def _r_repair(world: World) -> list[str]:
    owner = world.get("owner")
    accused = world.get("accused")
    if world.facts.get("truth_known") is not True:
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (owner, accused):
        kid.memes["quarrel"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    owner.memes["blame"] = 0.0
    accused.memes["sad"] = 0.0
    return ["__repair__"]


CAUSAL_RULES = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="repair", tag="social", apply=_r_repair),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def misunderstanding_possible(snack: Snack, cause: Cause) -> bool:
    return cause.id in snack.safe_for


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.kind >= KIND_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for snack_id, snack in SNACKS.items():
        for cause_id, cause in CAUSES.items():
            if not misunderstanding_possible(snack, cause):
                continue
            for repair_id, repair in REPAIRS.items():
                if repair.kind >= KIND_MIN:
                    combos.append((snack_id, cause_id, repair_id))
    return combos


def predict_quarrel(snack: Snack, cause: Cause) -> dict:
    blamed = cause.true_actor != "accused"
    return {
        "misunderstanding": blamed,
        "quarrel": blamed and misunderstanding_possible(snack, cause),
    }


def setup_scene(world: World, owner: Entity, accused: Entity, helper: Entity, snack: Snack) -> None:
    owner.memes["joy"] += 1
    accused.memes["joy"] += 1
    world.say(
        f"After the afternoon nap, {owner.id} and {accused.id} sat at the kitchen table with "
        f"{helper.label_word} and watched {snack.setup}."
    )
    world.say(
        f"On the plate waited {snack.phrase}. The warm room smelled buttery, and the salty salami made both children smile."
    )


def promise_share(world: World, owner: Entity, accused: Entity, snack: Snack) -> None:
    owner.memes["trust"] += 1
    accused.memes["trust"] += 1
    world.say(
        f'"Let\'s split it fair and square," {owner.id} said, pointing at {snack.label}.'
    )
    world.say(
        f'{accused.id} nodded. "{snack.part_word.capitalize()} for you, {snack.part_word} for me," {accused.pronoun()} said.'
    )


def missing_piece(world: World, snack: Snack, cause: Cause) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["missing_part"] += 1
    world.facts["clue"] = cause.clue
    world.say(
        f"But when they looked again, one {snack.part_word} was gone. {cause.clue}"
    )


def accuse(world: World, owner: Entity, accused: Entity, snack: Snack, cause: Cause) -> None:
    pred = predict_quarrel(snack, cause)
    world.facts["predicted_quarrel"] = pred["quarrel"]
    if not pred["misunderstanding"]:
        raise StoryError("(No misunderstanding: the missing food was really taken by the other child.)")
    owner.memes["blame"] += 1
    owner.memes["hurt"] += 1
    accused.memes["sad"] += 1
    accused.memes["confusion"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{owner.id} frowned. "Did you take my {snack.part_word} of the salami?" {owner.pronoun()} asked.'
    )
    world.say(
        f'"No," said {accused.id}, sitting up very straight. "{accused.pronoun().capitalize()} didn\'t touch it."'
    )
    if owner.memes["quarrel"] >= THRESHOLD:
        world.say(
            f"Soon a little quarrel puffed up between them, as quick and prickly as steam from soup."
        )


def helper_notices(world: World, helper: Entity, cause: Cause) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.label_word.capitalize()} did not scold either child. {helper.pronoun().capitalize()} just looked closely at the table and noticed {cause.clue.lower()}."
    )


def reveal_truth(world: World, helper: Entity, owner: Entity, accused: Entity, cause: Cause) -> None:
    world.facts["truth_known"] = True
    propagate(world, narrate=False)
    actor_map = {
        "cat": world.facts.get("pet_name", "the cat"),
        "wind": "the open window",
        "parent_move": f"{helper.label_word}",
    }
    actor_text = actor_map.get(cause.true_actor, cause.true_actor)
    world.say(
        f'"Wait a moment," said {helper.label_word}. "{cause.reveal}"'
    )
    world.say(
        f"It had not been {accused.id} at all. It had been {actor_text}, and the misunderstanding melted almost as fast as it had formed."
    )
    owner.memes["guilt"] += 1
    accused.memes["relief"] += 1


def apology(world: World, owner: Entity, accused: Entity) -> None:
    owner.memes["kindness"] += 1
    accused.memes["kindness"] += 1
    world.say(
        f'{owner.id} looked at {accused.id} with wet, sorry eyes. "I am sorry I blamed you," {owner.pronoun()} said.'
    )
    world.say(
        f'{accused.id} slid a little closer. "It hurt my feelings, but I know you were upset," {accused.pronoun()} answered.'
    )


def repair_action(world: World, helper: Entity, owner: Entity, accused: Entity, snack: Snack, repair: Repair) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["shared"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {repair.action}"
    )
    world.say(
        f"Together they made the snack look welcoming again, and the sharp feeling in the room softened."
    )
    world.say(repair.ending)


def tell(
    snack: Snack,
    cause: Cause,
    repair: Repair,
    owner_name: str = "Nina",
    owner_type: str = "girl",
    accused_name: str = "Owen",
    accused_type: str = "boy",
    helper_type: str = "mother",
    pet_name: str = "Mittens",
) -> World:
    world = World()
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_type, role="owner"))
    accused = world.add(Entity(id=accused_name, kind="character", type=accused_type, role="accused"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the parent"))
    snack_ent = world.add(Entity(id="snack", kind="thing", type="food", label=snack.label, phrase=snack.phrase))
    if cause.true_actor == "cat":
        world.add(Entity(id="pet", kind="thing", type="cat", label=pet_name, phrase=f"the cat {pet_name}"))
        world.facts["pet_name"] = pet_name

    setup_scene(world, owner, accused, helper, snack)
    promise_share(world, owner, accused, snack)

    world.para()
    missing_piece(world, snack, cause)
    accuse(world, owner, accused, snack, cause)

    world.para()
    helper_notices(world, helper, cause)
    reveal_truth(world, helper, owner, accused, cause)
    apology(world, owner, accused)
    world.para()
    repair_action(world, helper, owner, accused, snack, repair)

    world.facts.update(
        snack_cfg=snack,
        cause_cfg=cause,
        repair_cfg=repair,
        owner=owner,
        accused=accused,
        helper=helper,
        snack=snack_ent,
        outcome="repaired",
        misunderstanding=True,
    )
    return world


SNACKS = {
    "sandwich": Snack(
        id="sandwich",
        label="the sandwich",
        phrase="a warm sandwich cut into two neat triangles",
        part_word="triangle",
        place="on a blue plate",
        setup="toast shine under a pat of butter",
        safe_for={"cat", "wind", "parent_move"},
        tags={"sandwich", "salami", "sharing"},
    ),
    "crackers": Snack(
        id="crackers",
        label="the crackers",
        phrase="round crackers topped with cream cheese and little curls of salami",
        part_word="cracker",
        place="on a small wooden board",
        setup="the snack board waiting by the juice cups",
        safe_for={"cat", "parent_move"},
        tags={"crackers", "salami", "sharing"},
    ),
    "lunchbox": Snack(
        id="lunchbox",
        label="the lunchbox snack",
        phrase="a lunchbox with apple slices and a tiny salami roll cut in two",
        part_word="half",
        place="inside a bright lunchbox",
        setup="the lunchbox being packed for tomorrow",
        safe_for={"wind", "parent_move"},
        tags={"lunchbox", "salami", "sharing"},
    ),
}

CAUSES = {
    "cat": Cause(
        id="cat",
        label="cat",
        clue="A tiny greasy paw print sat near the plate.",
        reveal="Mittens reached up, stole a piece, and is hiding under the chair with it now.",
        true_actor="cat",
        kind=3,
        tags={"cat", "misunderstanding"},
    ),
    "wind": Cause(
        id="wind",
        label="wind",
        clue="A paper napkin had fluttered to the floor beside an open window.",
        reveal="The breeze nudged the napkin over the food and blew one piece behind the bread basket.",
        true_actor="wind",
        kind=3,
        tags={"wind", "misunderstanding"},
    ),
    "parent_move": Cause(
        id="parent_move",
        label="parent moved it",
        clue="The mustard jar stood where it had not been a minute before.",
        reveal="I moved one piece aside while reaching for the mustard, and it slid onto the little side plate.",
        true_actor="parent_move",
        kind=2,
        tags={"kitchen", "misunderstanding"},
    ),
    "sibling": Cause(
        id="sibling",
        label="really eaten by sibling",
        clue="There was a crumb on the other child's sleeve.",
        reveal="You did take it after all.",
        true_actor="accused",
        kind=1,
        tags={"not_misunderstanding"},
    ),
}

REPAIRS = {
    "extra_slice": Repair(
        id="extra_slice",
        label="extra slice",
        action="opened the bread box, added one more slice of bread and one more round of salami, and made an extra little piece for sharing.",
        ending="When they ate, they leaned shoulder to shoulder, and even the salami tasted softer after the truth was spoken.",
        kind=3,
        tags={"sharing", "food"},
    ),
    "cut_smaller": Repair(
        id="cut_smaller",
        label="cut smaller",
        action="cut the snack into smaller bites so there was enough for both children and a tiny safe treat for the cat to smell from far away.",
        ending="They each chose a bite, then traded one just for fun, and the table felt friendly again.",
        kind=3,
        tags={"sharing", "food", "cat"},
    ),
    "tea_towel_picnic": Repair(
        id="tea_towel_picnic",
        label="tea towel picnic",
        action="spread a clean tea towel by the sunny window and turned the rescued snack into a tiny indoor picnic.",
        ending="By the time the crumbs were gone, the quarrel was gone too, and the room held only quiet chewing and small smiles.",
        kind=2,
        tags={"sharing", "picnic"},
    ),
    "send_to_room": Repair(
        id="send_to_room",
        label="send away",
        action="sent the children to their room without listening to either of them.",
        ending="They ate later in silence.",
        kind=1,
        tags={"harsh"},
    ),
}

GIRL_NAMES = ["Nina", "Lila", "Maya", "Ella", "Rosa", "June", "Tess", "Lucy"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Theo", "Sam", "Eli", "Noah", "Finn"]
PET_NAMES = ["Mittens", "Pepper", "Button", "Socks"]
TRAITS = ["gentle", "bright", "careful", "eager"]


@dataclass
class StoryParams:
    snack: str
    cause: str
    repair: str
    owner_name: str
    owner_type: str
    accused_name: str
    accused_type: str
    helper_type: str
    pet_name: str = "Mittens"
    seed: Optional[int] = None


KNOWLEDGE = {
    "salami": [
        (
            "What is salami?",
            "Salami is a kind of sausage sliced into little round pieces for sandwiches or snacks. Grown-ups often serve it with bread or crackers."
        )
    ],
    "sharing": [
        (
            "Why is sharing food kindly important?",
            "Sharing helps everyone feel included and cared for. When people speak kindly and make room for each other, mealtime feels safe and warm."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something happened, but the real story is different. Talking and checking clues can help people understand each other."
        )
    ],
    "cat": [
        (
            "Why do cats sometimes sneak food?",
            "Cats are curious and they follow good smells. If food is left where they can reach it, they may try to grab a bite."
        )
    ],
    "wind": [
        (
            "How can wind move light things in a kitchen?",
            "A breeze can push napkins, wrappers, or even a very light piece of food if it is loose on the table. Open windows can make small things slide or flutter."
        )
    ],
    "sandwich": [
        (
            "What makes a sandwich easy to share?",
            "A sandwich can be cut into halves or triangles, so each person gets a clear piece. Cutting food neatly can make sharing feel fair."
        )
    ],
    "crackers": [
        (
            "Why are crackers easy for snacks?",
            "Crackers are small and easy to divide into turns or equal pieces. That makes them simple to share at a table."
        )
    ],
    "lunchbox": [
        (
            "What is a lunchbox for?",
            "A lunchbox carries food so it stays together until mealtime. It helps keep snacks neat and ready to pack."
        )
    ],
}

KNOWLEDGE_ORDER = ["salami", "misunderstanding", "sharing", "cat", "wind", "sandwich", "crackers", "lunchbox"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    accused = f["accused"]
    snack = f["snack_cfg"]
    cause = f["cause_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "quarrel" and "salami".',
        f"Tell a gentle misunderstanding story where {owner.id} thinks {accused.id} took part of a salami snack, but {cause.label} is the real reason it went missing.",
        f"Write a cozy kitchen story about a quarrel that starts over {snack.label} and ends with apology, sharing, and warm feelings."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    accused = f["accused"]
    helper = f["helper"]
    snack = f["snack_cfg"]
    cause = f["cause_cfg"]
    repair = f["repair_cfg"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id} and {accused.id}, two children who wanted to share a salami snack, and their {helper_word} who helped them slow down and see the truth."
        ),
        (
            "Why did the quarrel begin?",
            f"The quarrel began because one {snack.part_word} was missing, and {owner.id} thought {accused.id} had taken it. That was a misunderstanding, because the real cause was {cause.label}."
        ),
        (
            f"What clue helped {helper_word} understand what happened?",
            f"{helper_word.capitalize()} noticed this clue: {f.get('clue', cause.clue)} That small detail showed the missing food had not simply been snatched by {accused.id}."
        ),
        (
            f"How was the misunderstanding solved?",
            f"{helper_word.capitalize()} looked carefully and explained the real truth. Once {owner.id} knew {accused.id} had not taken the salami, the angry feeling dropped away and the children could talk kindly again."
        ),
        (
            f"What did {owner.id} do after learning the truth?",
            f"{owner.id} apologized for blaming {accused.id}. That apology mattered because it helped mend the hurt feeling the quarrel had caused."
        ),
        (
            "How did the story end?",
            f"It ended with {helper_word} helping them repair the snack by {repair.label.replace('_', ' ')}. They shared the food together, and the ending image proves the room had changed from prickly and tense to warm and peaceful."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["snack_cfg"].tags) | set(f["cause_cfg"].tags) | {"sharing", "salami", "misunderstanding"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        snack="sandwich",
        cause="cat",
        repair="extra_slice",
        owner_name="Nina",
        owner_type="girl",
        accused_name="Owen",
        accused_type="boy",
        helper_type="mother",
        pet_name="Mittens",
    ),
    StoryParams(
        snack="lunchbox",
        cause="wind",
        repair="tea_towel_picnic",
        owner_name="Maya",
        owner_type="girl",
        accused_name="Ben",
        accused_type="boy",
        helper_type="father",
        pet_name="Pepper",
    ),
    StoryParams(
        snack="crackers",
        cause="parent_move",
        repair="cut_smaller",
        owner_name="Lucy",
        owner_type="girl",
        accused_name="Theo",
        accused_type="boy",
        helper_type="mother",
        pet_name="Button",
    ),
]


def explain_combo(snack: Snack, cause: Cause) -> str:
    if cause.id == "sibling":
        return "(No story: that cause is not a misunderstanding, so it cannot support this misunderstanding world.)"
    return f"(No story: {cause.label} does not fit naturally with {snack.label} in this tiny domain.)"


def explain_repair(repair: Repair) -> str:
    return (
        f"(Refusing repair '{repair.id}': it is too harsh for this heartwarming world "
        f"(kind={repair.kind} < {KIND_MIN}). Pick a gentler repair such as "
        f"{', '.join(sorted(r.id for r in sensible_repairs()))}.)"
    )


ASP_RULES = r"""
fits(S, C) :- snack(S), cause(C), allowed(S, C).
gentle(R)  :- repair(R), kindness(R, K), kind_min(M), K >= M.
valid(S, C, R) :- fits(S, C), gentle(R), real_misunderstanding(C).

real_misunderstanding(C) :- cause(C), true_actor(C, A), A != accused.
not_misunderstanding(C)  :- cause(C), true_actor(C, accused).

outcome(repaired) :- chosen_snack(S), chosen_cause(C), chosen_repair(R),
                     fits(S, C), gentle(R), real_misunderstanding(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        for cause_id in sorted(snack.safe_for):
            lines.append(asp.fact("allowed", snack_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("true_actor", cause_id, cause.true_actor))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("kindness", repair_id, repair.kind))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py_out = "repaired" if (
            misunderstanding_possible(SNACKS[params.snack], CAUSES[params.cause])
            and CAUSES[params.cause].true_actor != "accused"
            and REPAIRS[params.repair].kind >= KIND_MIN
        ) else "invalid"
        if asp_outcome(params) != py_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Heartwarming misunderstanding story world about a quarrel over salami."
    )
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--owner-name")
    ap.add_argument("--accused-name")
    ap.add_argument("--owner-type", choices=["girl", "boy"])
    ap.add_argument("--accused-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and CAUSES[args.cause].true_actor == "accused":
        raise StoryError(explain_combo(SNACKS[args.snack] if args.snack else next(iter(SNACKS.values())), CAUSES[args.cause]))
    if args.repair and REPAIRS[args.repair].kind < KIND_MIN:
        raise StoryError(explain_repair(REPAIRS[args.repair]))
    if args.snack and args.cause:
        snack = SNACKS[args.snack]
        cause = CAUSES[args.cause]
        if not misunderstanding_possible(snack, cause) or cause.true_actor == "accused":
            raise StoryError(explain_combo(snack, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.snack is None or combo[0] == args.snack)
        and (args.cause is None or combo[1] == args.cause)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, cause_id, repair_id = rng.choice(sorted(combos))
    owner_type = args.owner_type or rng.choice(["girl", "boy"])
    accused_type = args.accused_type or rng.choice(["girl", "boy"])
    owner_name = args.owner_name or _pick_name(rng, owner_type)
    accused_name = args.accused_name or _pick_name(rng, accused_type, avoid=owner_name)
    helper_type = args.helper or rng.choice(["mother", "father"])
    pet_name = rng.choice(PET_NAMES)
    return StoryParams(
        snack=snack_id,
        cause=cause_id,
        repair=repair_id,
        owner_name=owner_name,
        owner_type=owner_type,
        accused_name=accused_name,
        accused_type=accused_type,
        helper_type=helper_type,
        pet_name=pet_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    snack = SNACKS[params.snack]
    cause = CAUSES[params.cause]
    repair = REPAIRS[params.repair]

    if not misunderstanding_possible(snack, cause) or cause.true_actor == "accused":
        raise StoryError(explain_combo(snack, cause))
    if repair.kind < KIND_MIN:
        raise StoryError(explain_repair(repair))

    world = tell(
        snack=snack,
        cause=cause,
        repair=repair,
        owner_name=params.owner_name,
        owner_type=params.owner_type,
        accused_name=params.accused_name,
        accused_type=params.accused_type,
        helper_type=params.helper_type,
        pet_name=params.pet_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (snack, cause, repair) combos:\n")
        for snack, cause, repair in combos:
            print(f"  {snack:10} {cause:12} {repair}")
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
            header = f"### {p.owner_name} and {p.accused_name}: {p.snack}, {p.cause}, {p.repair}"
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
