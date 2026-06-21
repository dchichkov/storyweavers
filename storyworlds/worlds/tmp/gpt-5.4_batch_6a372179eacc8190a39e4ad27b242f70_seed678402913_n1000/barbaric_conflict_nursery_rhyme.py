#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py
=============================================================

A small standalone storyworld for gentle nursery-rhyme-like conflict tales.

Premise
-------
Two little children in a make-believe royal nook begin with a bright game.
One shared toy or treasure becomes the center of a quarrel. The quarrel grows
rough enough that a grown-up calls the noise "barbaric," which is the story's
featured word. Then the grown-up chooses a calming, concrete way to settle the
conflict. If the calming move is strong enough for the roughness of the quarrel,
the children end by sharing and singing. If not, the game ends in a quiet sulk.

The world model is deliberately small and classical:
- typed entities with physical meters and emotional memes
- a tiny forward-chaining causal engine
- a reasonableness gate for compatible sparks and peaceful fixes
- an inline ASP twin for the compatibility gate and outcome model
- prose driven by simulated state, not by one frozen template

Run it
------
    python storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/barbaric_conflict_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "nurse", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "nurse": "nurse"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    scene: str = ""
    image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str = ""
    phrase: str = ""
    plural: bool = False
    fragility: int = 1
    tags: set[str] = field(default_factory=set)
    damage_word: str = ""
    ending_image: str = ""


@dataclass
class SparkCfg:
    id: str
    label: str = ""
    rough: int = 1
    needs_any_tag: set[str] = field(default_factory=set)
    damage_line: str = ""
    cry_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class PeaceCfg:
    id: str
    label: str = ""
    sense: int = 2
    power: int = 2
    needs_any_tag: set[str] = field(default_factory=set)
    intro_line: str = ""
    success_line: str = ""
    fail_line: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    spark: str
    peace: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    caretaker: str
    delay: int = 0
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "child"]

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


def _r_clamor(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["jostled"] >= THRESHOLD:
        sig = ("clamor", "item")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["noise"] += 1
            out.append("__clamor__")
    return out


def _r_conflict_hurts(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["conflict"] < THRESHOLD:
            continue
        sig = ("hurt", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["sadness"] += 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule(name="clamor", tag="physical", apply=_r_clamor),
    Rule(name="conflict_hurts", tag="social", apply=_r_conflict_hurts),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def spark_compatible(item: ItemCfg, spark: SparkCfg) -> bool:
    if not spark.needs_any_tag:
        return True
    return bool(item.tags & spark.needs_any_tag)


def peace_applicable(item: ItemCfg, peace: PeaceCfg) -> bool:
    if peace.sense < SENSE_MIN:
        return False
    if not peace.needs_any_tag:
        return True
    return bool(item.tags & peace.needs_any_tag)


def sensible_peaces() -> list[PeaceCfg]:
    return [p for p in PEACES.values() if p.sense >= SENSE_MIN]


def conflict_severity(item: ItemCfg, spark: SparkCfg, delay: int) -> int:
    return item.fragility + spark.rough + delay


def is_settled(item: ItemCfg, spark: SparkCfg, peace: PeaceCfg, delay: int) -> bool:
    return peace.power >= conflict_severity(item, spark, delay)


def explain_spark_rejection(item: ItemCfg, spark: SparkCfg) -> str:
    need = ", ".join(sorted(spark.needs_any_tag))
    have = ", ".join(sorted(item.tags))
    return (
        f"(No story: {spark.label} does not fit {item.label}. "
        f"The spark needs an item with one of [{need}], but this item has [{have}].)"
    )


def explain_peace_rejection(item: ItemCfg, peace: PeaceCfg) -> str:
    if peace.sense < SENSE_MIN:
        return (
            f"(Refusing peace plan '{peace.id}': it scores too low on common sense "
            f"(sense={peace.sense} < {SENSE_MIN}). Pick a calmer, clearer fix.)"
        )
    need = ", ".join(sorted(peace.needs_any_tag))
    have = ", ".join(sorted(item.tags))
    return (
        f"(No story: {peace.label} does not really fit {item.label}. "
        f"It needs an item with one of [{need}], but this item has [{have}].)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in ITEMS.items():
            for spark_id, spark in SPARKS.items():
                if spark_compatible(item, spark):
                    combos.append((place_id, item_id, spark_id))
    return combos


def applicable_peaces_for_item(item_id: str) -> list[str]:
    item = ITEMS[item_id]
    return sorted(pid for pid, peace in PEACES.items() if peace_applicable(item, peace))


def predict_quarrel(world: World, spark: SparkCfg) -> dict:
    sim = world.copy()
    _do_spark(sim, spark, narrate=False)
    return {
        "noise": sim.get("room").meters["noise"],
        "sad_kids": sum(1 for kid in sim.kids() if kid.memes["sadness"] >= THRESHOLD),
        "damage": sim.get("item").meters["damage"],
    }


def _do_spark(world: World, spark: SparkCfg, narrate: bool = True) -> None:
    item = world.get("item")
    item.meters["jostled"] += 1
    item.meters["damage"] += 1
    for kid in world.kids():
        kid.memes["conflict"] += 1
        kid.memes["anger"] += 1
    propagate(world, narrate=narrate)


def open_rhyme(world: World, a: Entity, b: Entity, item_cfg: ItemCfg) -> None:
    world.say(
        f"In {world.place.scene}, where nursery breezes ran, "
        f"{a.id} and {b.id} played as grandly as they can."
    )
    world.say(
        f"Between them lay {item_cfg.phrase}; it shone in merry light, "
        f"and for a little while their game went skipping bright."
    )


def want_same_thing(world: World, a: Entity, b: Entity, item_cfg: ItemCfg) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f'"Mine for one more turn," said {a.id}. "Then mine," said {b.id} too. '
        f"The same small wish in two small hearts began to pull in two."
    )


def roughen(world: World, a: Entity, b: Entity, spark: SparkCfg, item_cfg: ItemCfg) -> None:
    a.memes["defiance"] += 1
    b.memes["defiance"] += 1
    _do_spark(world, spark)
    world.say(
        f"Soon they {spark.label} at once; the play grew hard and sharp. "
        f"{spark.damage_line}"
    )
    world.say(
        f'{spark.cry_line} The grown-up at the door cried, '
        f'"What barbaric noise is this? A game should not grow sore."'
    )


def warn(world: World, caretaker: Entity, spark: SparkCfg, item_cfg: ItemCfg) -> None:
    pred = predict_quarrel(world, spark)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_sad_kids"] = pred["sad_kids"]
    if pred["damage"] >= THRESHOLD:
        world.say(
            f"{caretaker.label_word.capitalize()} saw that {item_cfg.label} would soon "
            f"be {item_cfg.damage_word}, and that both small faces had already gone tight."
        )


def calm_success(world: World, caretaker: Entity, a: Entity, b: Entity,
                 item_cfg: ItemCfg, peace: PeaceCfg) -> None:
    for kid in (a, b):
        kid.memes["conflict"] = 0.0
        kid.memes["anger"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["love"] += 1
    world.get("room").meters["noise"] = 0.0
    world.say(
        f"{caretaker.label_word.capitalize()} stepped between them and {peace.intro_line}"
    )
    world.say(peace.success_line.format(item=item_cfg.label, child1=a.id, child2=b.id))
    world.say(
        f"Then off they went in measured turns, each waiting sweet and slow, "
        f"and {item_cfg.ending_image} as evening bells grew low."
    )


def calm_fail(world: World, caretaker: Entity, a: Entity, b: Entity,
              item_cfg: ItemCfg, peace: PeaceCfg) -> None:
    for kid in (a, b):
        kid.memes["conflict"] += 1
        kid.memes["sadness"] += 1
        kid.memes["anger"] = 0.0
        kid.memes["joy"] = 0.0
    world.say(
        f"{caretaker.label_word.capitalize()} tried to help and {peace.fail_line.format(item=item_cfg.label)}"
    )
    world.say(
        f"But the storm in two small hearts was bigger than that plan. "
        f"{a.id} sat on one small stool, and {b.id} sat on another."
    )
    world.say(
        f"The room grew quiet at the last, yet not with merry peace; "
        f"they learned that rough beginnings make the nicest music cease."
    )


def tell(place: Place, item_cfg: ItemCfg, spark: SparkCfg, peace: PeaceCfg,
         child1: str = "Molly", child1_gender: str = "girl",
         child2: str = "Robin", child2_gender: str = "boy",
         caretaker_type: str = "nurse", delay: int = 0) -> World:
    world = World(place)
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="child"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="child"))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, role="caretaker", label="the caretaker"))
    room = world.add(Entity(id="room", type="room", label=place.scene))
    item = world.add(Entity(id="item", type="toy", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))

    world.facts["delay"] = delay

    open_rhyme(world, a, b, item_cfg)
    want_same_thing(world, a, b, item_cfg)

    world.para()
    roughen(world, a, b, spark, item_cfg)
    warn(world, caretaker, spark, item_cfg)

    severity = conflict_severity(item_cfg, spark, delay)
    item.meters["severity"] = float(severity)
    outcome = "shared" if is_settled(item_cfg, spark, peace, delay) else "sulk"

    world.para()
    if outcome == "shared":
        calm_success(world, caretaker, a, b, item_cfg, peace)
    else:
        calm_fail(world, caretaker, a, b, item_cfg, peace)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        spark=spark,
        peace=peace,
        child1=a,
        child2=b,
        caretaker=caretaker,
        item=item,
        outcome=outcome,
        severity=severity,
        damaged=item.meters["damage"] >= THRESHOLD,
        conflict_started=True,
    )
    return world


PLACES = {
    "nursery_green": Place(
        id="nursery_green",
        scene="the nursery green",
        image="a little gate, a thyme-soft lane, and flags of clover",
        tags={"outdoor", "garden"},
    ),
    "moon_hall": Place(
        id="moon_hall",
        scene="the moonlit hall",
        image="a checker floor, a silver lamp, and curtains swaying over",
        tags={"indoor", "hall"},
    ),
    "pillow_court": Place(
        id="pillow_court",
        scene="the pillow court",
        image="a ring of cushions, a low toy chest, and a painted wall",
        tags={"indoor", "soft"},
    ),
}

ITEMS = {
    "drum": ItemCfg(
        id="drum",
        label="drum",
        phrase="a tin drum with a red wool cord",
        plural=False,
        fragility=1,
        tags={"noisy", "round", "parade"},
        damage_word="dented",
        ending_image="the little drum tapped tidy beats beneath the willow shade",
    ),
    "crown": ItemCfg(
        id="crown",
        label="crown",
        phrase="a paper crown with golden stars",
        plural=False,
        fragility=2,
        tags={"wearable", "delicate", "royal"},
        damage_word="crumpled",
        ending_image="the paper crown sat straight again on alternating heads",
    ),
    "horse": ItemCfg(
        id="horse",
        label="hobby-horse",
        phrase="a painted hobby-horse with a blue yarn mane",
        plural=False,
        fragility=2,
        tags={"ride", "parade", "tall"},
        damage_word="scuffed and toppled",
        ending_image="the hobby-horse trotted from one child to the next in patient little steps",
    ),
}

SPARKS = {
    "snatch": SparkCfg(
        id="snatch",
        label="snatch the toy",
        rough=1,
        needs_any_tag=set(),
        damage_line="Hands crossed, sleeves brushed, and the poor thing gave a wobbling sigh.",
        cry_line='"Stop, stop, stop!" cried one. "No, I had it first!" cried the other.',
        tags={"grab", "quarrel"},
    ),
    "bang": SparkCfg(
        id="bang",
        label="bang it between them",
        rough=2,
        needs_any_tag={"noisy", "parade"},
        damage_line="A clatter skipped across the floor, and the merry sound turned wild.",
        cry_line='"Too loud, too loud!" cried one. "Then hear it louder still!" cried the other.',
        tags={"noise", "quarrel"},
    ),
    "tug": SparkCfg(
        id="tug",
        label="tug from either side",
        rough=2,
        needs_any_tag={"wearable", "ride"},
        damage_line="There came a pull, a twist, a skid, and play lost all its grace.",
        cry_line='"Let go!" cried one. "You let go!" cried the other in the race.',
        tags={"pull", "quarrel"},
    ),
}

PEACES = {
    "turn_rhyme": PeaceCfg(
        id="turn_rhyme",
        label="a counting rhyme for turns",
        sense=3,
        power=4,
        needs_any_tag=set(),
        intro_line='sang a counting rhyme with palms held low and voices soft as wool.',
        success_line='"One for {child1}, one for {child2}, and none for pushing hands," said the grown-up. '
                     'By the rhyme, the quarrel folded up, and both children nodded to share the {item}.',
        fail_line='sang a counting rhyme, but the sore feelings still stuck like burrs to the {item}.',
        qa_text="used a counting rhyme so they could take turns",
        tags={"sharing", "rhyme"},
    ),
    "marching_duet": PeaceCfg(
        id="marching_duet",
        label="a marching duet",
        sense=3,
        power=3,
        needs_any_tag={"noisy", "parade", "ride"},
        intro_line='clapped a gentle beat and turned the quarrel into a two-child march.',
        success_line='Soon {child1} led one lap, then {child2} led the next, and the {item} belonged to the song instead of the squabble.',
        fail_line='clapped a gentle beat, but neither child was ready to step together around the {item}.',
        qa_text="turned the quarrel into a little march with turns",
        tags={"sharing", "music"},
    ),
    "ribbon_bow": PeaceCfg(
        id="ribbon_bow",
        label="a smoothing ribbon bow",
        sense=2,
        power=2,
        needs_any_tag={"wearable", "royal", "delicate"},
        intro_line='smoothed the creases with careful fingers and tied on a fresh ribbon bow.',
        success_line='That neat small fixing gave both children time to breathe, and they agreed the {item} could visit one head and then the other.',
        fail_line='smoothed the creases and tied a ribbon bow, but the children still glared across the {item}.',
        qa_text="smoothed it, tied on a ribbon bow, and made a turn-taking plan",
        tags={"mending", "sharing"},
    ),
    "stern_scold": PeaceCfg(
        id="stern_scold",
        label="a stern scolding alone",
        sense=1,
        power=1,
        needs_any_tag=set(),
        intro_line='spoke in a sharp voice without giving the children a better way to play.',
        success_line='The children froze for a blink, but this line is never used because the plan is refused.',
        fail_line='spoke sharply at them from across the room, which stopped the shouting for only a breath around the {item}.',
        qa_text="scolded from across the room",
        tags={"warning"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Poppy", "Lila", "Nell", "Tess", "Ivy", "Mabel"]
BOY_NAMES = ["Robin", "Toby", "Jem", "Ned", "Alfie", "Miles", "Otto", "Pip"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    item_cfg = f["item_cfg"]
    spark = f["spark"]
    outcome = f["outcome"]
    if outcome == "shared":
        return [
            f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the word "barbaric" and a conflict over a {item_cfg.label}.',
            f"Tell a gentle rhyme where {a.id} and {b.id} quarrel because they both want the same {item_cfg.label}, and a grown-up helps them share.",
            f"Write a playful conflict story with bright rhythm, a rough middle where children {spark.label}, and a peaceful ending image that proves they learned turns.",
        ]
    return [
        f'Write a nursery-rhyme-style cautionary story for a 3-to-5-year-old that includes the word "barbaric" and a conflict over a {item_cfg.label}.',
        f"Tell a rhyme where {a.id} and {b.id} quarrel so roughly that the room grows quiet and sad at the end.",
        f"Write a short poem-story with conflict, a grown-up trying to help, and an ending where the children learn that rough play spoils the game.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two little girls"
    if a.type == "boy" and b.type == "boy":
        return "two little boys"
    return "two little children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    caretaker = f["caretaker"]
    item_cfg = f["item_cfg"]
    spark = f["spark"]
    peace = f["peace"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, who both wanted the same {item_cfg.label}. It also includes their {caretaker.label_word}, who stepped in when the game turned rough.",
        ),
        (
            f"Why did {a.id} and {b.id} start to fight?",
            f"They both wanted the same {item_cfg.label} at the same time. One small wish pulled against another until the game turned into conflict.",
        ),
        (
            "Why did the grown-up call the noise barbaric?",
            f"The grown-up called it barbaric because the children had stopped playing kindly and had begun to {spark.label}. The rough noise and pulling showed that the game had lost its gentle rules.",
        ),
    ]
    if f.get("damaged"):
        qa.append(
            (
                f"What happened to the {item_cfg.label} during the quarrel?",
                f"It was jostled and nearly became {item_cfg.damage_word}. The object showed the conflict on the outside, just as the children were feeling upset on the inside.",
            )
        )
    if outcome == "shared":
        qa.append(
            (
                f"How did the {caretaker.label_word} solve the problem?",
                f"The {caretaker.label_word} {peace.qa_text}. That plan gave each child a fair turn, so the conflict could settle instead of growing sharper.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with sharing. The children took turns with the {item_cfg.label}, and the final image showed their game had become gentle again.",
            )
        )
    else:
        qa.append(
            (
                f"Did the {caretaker.label_word}'s plan work?",
                f"No, not fully. The plan was too small for feelings that had already grown big, so the quarrel stopped the fun instead of mending it.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly but sadly, with the children apart instead of sharing. They learned that rough conflict can make a happy game fall flat.",
            )
        )
    return qa


KNOWLEDGE = {
    "sharing": [
        (
            "Why do turns help when two children want the same toy?",
            "Turns help because each child knows a fair chance is coming. That makes the waiting easier and keeps grabbing from starting."
        )
    ],
    "rhyme": [
        (
            "What is a counting rhyme?",
            "A counting rhyme is a short sing-song verse people use while they count. It can help children slow down and take turns."
        )
    ],
    "music": [
        (
            "Why can clapping or marching calm a quarrel?",
            "A steady beat helps bodies slow down and move together. When children follow one rhythm, they often stop pulling against each other."
        )
    ],
    "mending": [
        (
            "What does mending mean?",
            "Mending means fixing something that got bent, torn, or rumpled. A small repair can also give people time to calm down."
        )
    ],
    "warning": [
        (
            "Why is scolding by itself sometimes not enough?",
            "Scolding can stop noise for a moment, but it does not always show children what kind thing to do next. A good fix often needs both a boundary and a better plan."
        )
    ],
    "grab": [
        (
            "Why does grabbing start conflicts?",
            "Grabbing feels sudden and unfair. The other person often grabs back, and the problem grows bigger very quickly."
        )
    ],
    "pull": [
        (
            "Why is tugging a delicate thing a bad idea?",
            "Tugging pulls the object in two directions at once. That can crumple it and also make both children feel cross."
        )
    ],
    "noise": [
        (
            "Why can loud rough play upset a room?",
            "Very loud rough play makes it hard for everyone to think and feel calm. Noise can be a sign that a game has stopped being gentle."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["spark"].tags) | set(world.facts["peace"].tags)
    out: list[tuple[str, str]] = []
    for tag in ["sharing", "rhyme", "music", "mending", "warning", "grab", "pull", "noise"]:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="nursery_green",
        item="drum",
        spark="bang",
        peace="marching_duet",
        child1="Molly",
        child1_gender="girl",
        child2="Robin",
        child2_gender="boy",
        caretaker="nurse",
        delay=0,
    ),
    StoryParams(
        place="moon_hall",
        item="crown",
        spark="tug",
        peace="ribbon_bow",
        child1="Daisy",
        child1_gender="girl",
        child2="Pip",
        child2_gender="boy",
        caretaker="mother",
        delay=0,
    ),
    StoryParams(
        place="pillow_court",
        item="horse",
        spark="snatch",
        peace="turn_rhyme",
        child1="Nell",
        child1_gender="girl",
        child2="Otto",
        child2_gender="boy",
        caretaker="father",
        delay=1,
    ),
    StoryParams(
        place="moon_hall",
        item="horse",
        spark="tug",
        peace="marching_duet",
        child1="Ivy",
        child1_gender="girl",
        child2="Miles",
        child2_gender="boy",
        caretaker="nurse",
        delay=2,
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
spark_ok(I, S) :- spark(S), item(I), spark_any(S).
spark_ok(I, S) :- spark(S), item(I), needs_tag(S, T), has_tag(I, T).

valid(P, I, S) :- place(P), item(I), spark(S), spark_ok(I, S).

applicable_peace(I, Pe) :- peace(Pe), item(I), sense(Pe, Sc), sense_min(M), Sc >= M, peace_any(Pe).
applicable_peace(I, Pe) :- peace(Pe), item(I), sense(Pe, Sc), sense_min(M), Sc >= M,
                           peace_needs_tag(Pe, T), has_tag(I, T).

% --- outcome model ---------------------------------------------------------
severity(F + R + D) :- chosen_item(I), fragility(I, F), chosen_spark(S), rough(S, R), delay(D).
settled :- chosen_item(I), chosen_peace(Pe), applicable_peace(I, Pe), power(Pe, Pw), severity(V), Pw >= V.

outcome(shared) :- settled.
outcome(sulk)   :- not settled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("fragility", item_id, item.fragility))
        for tag in sorted(item.tags):
            lines.append(asp.fact("has_tag", item_id, tag))
    for spark_id, spark in SPARKS.items():
        lines.append(asp.fact("spark", spark_id))
        lines.append(asp.fact("rough", spark_id, spark.rough))
        if spark.needs_any_tag:
            for tag in sorted(spark.needs_any_tag):
                lines.append(asp.fact("needs_tag", spark_id, tag))
        else:
            lines.append(asp.fact("spark_any", spark_id))
    for peace_id, peace in PEACES.items():
        lines.append(asp.fact("peace", peace_id))
        lines.append(asp.fact("sense", peace_id, peace.sense))
        lines.append(asp.fact("power", peace_id, peace.power))
        if peace.needs_any_tag:
            for tag in sorted(peace.needs_any_tag):
                lines.append(asp.fact("peace_needs_tag", peace_id, tag))
        else:
            lines.append(asp.fact("peace_any", peace_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_applicable_peaces(item_id: str) -> list[str]:
    import asp
    extra = f"chosen_item({item_id})."
    model = asp.one_model(asp_program(extra, "#show applicable_peace/2."))
    return sorted(peace for (_, peace) in asp.atoms(model, "applicable_peace") if _ == item_id)


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_spark", params.spark),
        asp.fact("chosen_peace", params.peace),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared" if is_settled(ITEMS[params.item], SPARKS[params.spark], PEACES[params.peace], params.delay) else "sulk"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: compatibility gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    for item_id in ITEMS:
        c_peaces = set(asp_applicable_peaces(item_id))
        p_peaces = set(applicable_peaces_for_item(item_id))
        if c_peaces == p_peaces:
            print(f"OK: applicable peaces match for {item_id}: {sorted(c_peaces)}")
        else:
            rc = 1
            print(f"MISMATCH in applicable peaces for {item_id}: clingo={sorted(c_peaces)} python={sorted(p_peaces)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme conflict storyworld. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--peace", choices=PEACES)
    ap.add_argument("--caretaker", choices=["nurse", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time for hurt feelings to grow before the calming plan takes hold")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.spark and not spark_compatible(ITEMS[args.item], SPARKS[args.spark]):
        raise StoryError(explain_spark_rejection(ITEMS[args.item], SPARKS[args.spark]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.spark is None or combo[2] == args.spark)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, spark_id = rng.choice(sorted(combos))

    allowed_peaces = applicable_peaces_for_item(item_id)
    if args.peace:
        if args.peace not in PEACES:
            raise StoryError(f"(Unknown peace plan: {args.peace})")
        if args.peace not in allowed_peaces:
            raise StoryError(explain_peace_rejection(ITEMS[item_id], PEACES[args.peace]))
        peace_id = args.peace
    else:
        peace_id = rng.choice(allowed_peaces)

    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    caretaker = args.caretaker or rng.choice(["nurse", "mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        item=item_id,
        spark=spark_id,
        peace=peace_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        caretaker=caretaker,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in [("place", PLACES), ("item", ITEMS), ("spark", SPARKS), ("peace", PEACES)]:
        key = getattr(params, field_name)
        if key not in registry:
            raise StoryError(f"(Invalid {field_name}: {key})")

    item_cfg = ITEMS[params.item]
    spark = SPARKS[params.spark]
    peace = PEACES[params.peace]

    if not spark_compatible(item_cfg, spark):
        raise StoryError(explain_spark_rejection(item_cfg, spark))
    if not peace_applicable(item_cfg, peace):
        raise StoryError(explain_peace_rejection(item_cfg, peace))

    world = tell(
        place=PLACES[params.place],
        item_cfg=item_cfg,
        spark=spark,
        peace=peace,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        caretaker_type=params.caretaker,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show applicable_peace/2.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, spark) combos:\n")
        for place_id, item_id, spark_id in combos:
            peaces = ", ".join(applicable_peaces_for_item(item_id))
            print(f"  {place_id:14} {item_id:7} {spark_id:7}  peaces=[{peaces}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for idx, params in enumerate(CURATED):
            p = StoryParams(**vars(params))
            p.seed = base_seed + idx if args.seed is not None else None
            samples.append(generate(p))
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
            header = f"### {p.child1} & {p.child2}: {p.item} / {p.spark} / {p.peace} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
