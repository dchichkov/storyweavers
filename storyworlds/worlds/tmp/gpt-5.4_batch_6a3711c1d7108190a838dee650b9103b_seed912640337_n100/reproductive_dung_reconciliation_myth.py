#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py
===================================================================

A small mythic storyworld about two sacred dung beetle siblings whose quarrel
halts the rolling of the dawn-ball. The ball is made of dung, and the old
stories say it shelters a tiny reproductive promise for the next season of
grass, birds, and beetles. When pride or hurt makes the siblings stop working
together, the ball cracks or stalls, the light weakens, and the world droops.
A fitting reconciliation rite can mend both trust and the work itself, so the
ball rolls again and the day is restored.

Run it
------
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py --dung elephant --rite apology_song
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py --all
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py --trace
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py --asp
    python storyworlds/worlds/gpt-5.4/reproductive_dung_reconciliation_myth.py --verify
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
        female = {"girl", "woman", "sister", "queen"}
        male = {"boy", "man", "brother", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Realm:
    id: str
    opening: str
    horizon: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DungKind:
    id: str
    label: str
    phrase: str
    source: str
    weight: int
    scent: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Dispute:
    id: str
    spark: str
    wound: str
    needs: set[str]
    cracks_ball: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    label: str
    opening: str
    action: str
    closing: str
    repairs: set[str]
    strength: int
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stalled_world(world: World) -> list[str]:
    out: list[str] = []
    ball = world.get("ball")
    sky = world.get("sky")
    earth = world.get("earth")
    if ball.meters["stalled"] >= THRESHOLD:
        sig = ("stalled_world",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["dim"] += 1
            earth.meters["thirst"] += 1
            for eid in ("first", "second"):
                world.get(eid).memes["worry"] += 1
            out.append("__stall__")
    if ball.meters["cracked"] >= THRESHOLD:
        sig = ("cracked_world",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["dim"] += 1
            earth.meters["thirst"] += 1
            earth.meters["risk"] += 1
            for eid in ("first", "second"):
                world.get(eid).memes["fear"] += 1
            out.append("__crack__")
    return out


def _r_repaired_world(world: World) -> list[str]:
    out: list[str] = []
    ball = world.get("ball")
    sky = world.get("sky")
    earth = world.get("earth")
    if (
        ball.meters["rolling"] >= THRESHOLD
        and ball.meters["whole"] >= THRESHOLD
        and world.get("first").memes["peace"] >= THRESHOLD
        and world.get("second").memes["peace"] >= THRESHOLD
    ):
        sig = ("repaired_world",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["dim"] = 0.0
            earth.meters["thirst"] = 0.0
            earth.meters["risk"] = 0.0
            out.append("__restored__")
    return out


CAUSAL_RULES = [
    Rule("stalled_world", "physical", _r_stalled_world),
    Rule("repaired_world", "physical", _r_repaired_world),
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
        for item in produced:
            if item == "__stall__":
                world.say("At once the dawn-ball sat still, and the edge of morning lost its shine.")
            elif item == "__crack__":
                world.say("A dark seam opened in the ball, and a hush of fear ran over the plain.")
            elif item == "__restored__":
                world.say("Then the dim edge of the world brightened again, as if dawn had taken a full breath.")
    return produced


def needs_met(dispute: Dispute, rite: Rite) -> bool:
    return dispute.needs.issubset(rite.repairs)


def strong_enough(dung: DungKind, rite: Rite) -> bool:
    return rite.strength >= dung.weight


def valid_combo(dung: DungKind, dispute: Dispute, rite: Rite) -> bool:
    return needs_met(dispute, rite) and strong_enough(dung, rite)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id in REALMS:
        for dung_id, dung in DUNG_KINDS.items():
            for dispute_id, dispute in DISPUTES.items():
                for rite_id, rite in RITES.items():
                    if valid_combo(dung, dispute, rite):
                        combos.append((realm_id, dung_id, dispute_id, rite_id))
    return combos


def explain_rejection(dung: DungKind, dispute: Dispute, rite: Rite) -> str:
    if not needs_met(dispute, rite):
        missing = sorted(dispute.needs - rite.repairs)
        return (
            f"(No story: the rite '{rite.id}' cannot heal the kind of hurt caused by "
            f"'{dispute.id}'. It is missing repairs for {missing}, so the siblings "
            f"would not truly reconcile.)"
        )
    if not strong_enough(dung, rite):
        return (
            f"(No story: {rite.label} is too slight for a {dung.label} ball. "
            f"The ball is too heavy to mend and roll with that rite alone.)"
        )
    return "(No story: that combination does not make a sensible reconciliation myth.)"


def predict_harm(world: World, dispute: Dispute) -> dict:
    sim = world.copy()
    cause_quarrel(sim, dispute, narrate=False)
    return {
        "dim": sim.get("sky").meters["dim"],
        "thirst": sim.get("earth").meters["thirst"],
        "risk": sim.get("earth").meters["risk"],
    }


def opening(world: World, realm: Realm, dung: DungKind, first: Entity, second: Entity) -> None:
    ball = world.get("ball")
    first.memes["duty"] += 1
    second.memes["duty"] += 1
    ball.meters["whole"] += 1
    ball.meters["rolling"] += 1
    world.say(
        f"In the first days, when stories still walked beside the wind, {realm.opening}. "
        f"There lived two sacred beetle siblings, {first.id} and {second.id}, who rolled the dawn-ball each morning."
    )
    world.say(
        f"The ball was made of {dung.phrase}, rich from {dung.source}, and it carried a warm reproductive promise inside it. "
        f"The old ones said that promise helped grasses rise again, chicks hatch, and young beetles wake when their season came."
    )
    world.say(
        f"As the siblings pushed, the air smelled of {dung.scent}, and {realm.horizon}."
    )


def cause_quarrel(world: World, dispute: Dispute, narrate: bool = True) -> None:
    first = world.get("first")
    second = world.get("second")
    ball = world.get("ball")
    first.memes["pride"] += 1
    second.memes["hurt"] += 1
    first.memes["trust"] = 0.0
    second.memes["trust"] = 0.0
    ball.meters["rolling"] = 0.0
    ball.meters["stalled"] += 1
    if dispute.cracks_ball:
        ball.meters["cracked"] += 1
        ball.meters["whole"] = 0.0
    if narrate:
        world.say(dispute.spark)
        world.say(dispute.wound)
    propagate(world, narrate=narrate)


def witness_harm(world: World, first: Entity, second: Entity, realm: Realm) -> None:
    earth = world.get("earth")
    ball = world.get("ball")
    first.memes["shame"] += 1
    second.memes["sorrow"] += 1
    clause = "A pale light lay over everything" if world.get("sky").meters["dim"] >= THRESHOLD else "The light was wrong"
    world.say(
        f"{clause}, and {realm.horizon.lower()} no longer looked glad."
    )
    if ball.meters["cracked"] >= THRESHOLD:
        world.say(
            "Through the dark seam in the ball they glimpsed the tiny hidden chamber inside, and both remembered the reproductive promise they had nearly spoiled."
        )
    if earth.meters["thirst"] >= THRESHOLD:
        world.say(
            "The reeds bent low, and even the small thirsty things under the roots seemed to wait."
        )


def choose_rite(world: World, rite: Rite, elder: Entity) -> None:
    world.say(
        f"Then {elder.id}, the old scarab elder, came softly over the dust and said, "
        f'"If hands quarrel, dawn limps. If hearts reconcile, dawn walks. Begin {rite.opening}."'
    )


def perform_rite(world: World, rite: Rite, dung: DungKind, first: Entity, second: Entity) -> None:
    ball = world.get("ball")
    first.memes["peace"] += 1
    second.memes["peace"] += 1
    first.memes["love"] += 1
    second.memes["love"] += 1
    first.memes["trust"] += 1
    second.memes["trust"] += 1
    ball.meters["whole"] = 1.0
    ball.meters["cracked"] = 0.0
    ball.meters["stalled"] = 0.0
    ball.meters["rolling"] = 1.0
    world.say(rite.action)
    if dung.weight >= 3:
        world.say(
            f"The {dung.label} ball was heavy, yet together they leaned until it answered their strength."
        )
    else:
        world.say(
            f"The {dung.label} ball answered their joined legs and turned beneath them."
        )
    world.say(rite.closing)
    propagate(world, narrate=True)


def ending(world: World, realm: Realm, dung: DungKind, first: Entity, second: Entity) -> None:
    first.memes["joy"] += 1
    second.memes["joy"] += 1
    world.say(
        f"From then on, when one sibling felt pride rise like hot dust, the other remembered this day and spoke gently first."
    )
    world.say(
        f"So the people of that place say that {dung.label} is humble and holy at once, and that reconciliation keeps the world moving. "
        f"{realm.ending}"
    )


def tell(
    realm: Realm,
    dung: DungKind,
    dispute: Dispute,
    rite: Rite,
    first_name: str = "Ketu",
    first_type: str = "brother",
    second_name: str = "Luma",
    second_type: str = "sister",
    elder_name: str = "Old Shell",
) -> World:
    world = World()
    first = world.add(Entity(id=first_name, kind="character", type=first_type, role="first", label=first_name))
    second = world.add(Entity(id=second_name, kind="character", type=second_type, role="second", label=second_name))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", role="elder", label=elder_name))
    world.add(Entity(id="ball", type="ball", label="dawn-ball"))
    world.add(Entity(id="sky", type="sky", label="sky"))
    world.add(Entity(id="earth", type="earth", label="earth"))

    opening(world, realm, dung, first, second)
    world.para()

    harm = predict_harm(world, dispute)
    world.facts["predicted_harm"] = harm
    cause_quarrel(world, dispute, narrate=True)

    world.para()
    witness_harm(world, first, second, realm)
    choose_rite(world, rite, elder)

    world.para()
    perform_rite(world, rite, dung, first, second)
    ending(world, realm, dung, first, second)

    world.facts.update(
        realm=realm,
        dung=dung,
        dispute=dispute,
        rite=rite,
        first=first,
        second=second,
        elder=elder,
        ball=world.get("ball"),
        reconciled=first.memes["peace"] >= THRESHOLD and second.memes["peace"] >= THRESHOLD,
        cracked=dispute.cracks_ball,
    )
    return world


REALMS = {
    "reed_marsh": Realm(
        "reed_marsh",
        "the reed marsh touched the belly of the sky",
        "the water mirrored gold between the reeds",
        "At sunset the marsh glowed softly, and the reeds whispered over calm water",
        tags={"marsh", "dawn"},
    ),
    "red_plain": Realm(
        "red_plain",
        "the red plain stretched wide as a sleeping lion",
        "the far grass shone copper under the newborn light",
        "At evening the plain held a red shine, and the little burrows felt safe again",
        tags={"plain", "dawn"},
    ),
    "river_bend": Realm(
        "river_bend",
        "the great river bent like a blue bracelet around the earth",
        "the banks flashed silver where kingfishers waited",
        "By evening the river carried bright pieces of sky, and the fish leapt without fear",
        tags={"river", "dawn"},
    ),
}

DUNG_KINDS = {
    "antelope": DungKind(
        "antelope",
        "small antelope-dung",
        "a neat antelope-dung ball",
        "the grazing paths of the swift antelope",
        1,
        "sun-warm grass",
        tags={"dung", "light"},
    ),
    "buffalo": DungKind(
        "buffalo",
        "buffalo-dung",
        "a broad buffalo-dung ball",
        "the wallowing place of the buffalo herd",
        2,
        "wet earth and crushed reeds",
        tags={"dung", "strength"},
    ),
    "elephant": DungKind(
        "elephant",
        "elephant-dung",
        "a huge elephant-dung ball",
        "the shaded trail of the old elephants",
        3,
        "leaf-shadow after rain",
        tags={"dung", "strength"},
    ),
}

DISPUTES = {
    "boast": Dispute(
        "boast",
        '"I push harder than you," said the first sibling, lifting his horned head too high.',
        "The second sibling stopped at once, hurt by the boast, and the work of two became the work of none.",
        {"trust"},
        False,
        tags={"pride", "trust"},
    ),
    "broken_promise": Dispute(
        "broken_promise",
        "The first sibling had promised to take the steeper side of the ball, but when the slope grew hard, he slipped away to the easier side.",
        "The second sibling felt the weight bite into her legs alone, and her hurt turned to anger before either one could swallow it.",
        {"trust", "work"},
        False,
        tags={"promise", "labor"},
    ),
    "careless_shove": Dispute(
        "careless_shove",
        "In a rush of temper, the first sibling shoved too sharply instead of matching the second sibling's step.",
        "The dawn-ball lurched against a stone, and the second sibling cried out as both trust and the smooth work broke together.",
        {"trust", "work"},
        True,
        tags={"temper", "crack"},
    ),
}

RITES = {
    "apology_song": Rite(
        "apology_song",
        "the apology song",
        "the apology song beneath the paling sky",
        "The first sibling lowered his head and sang the old names of kinship until the second sibling's anger softened.",
        "When the song ended, they touched feelers in peace.",
        {"trust"},
        1,
        tags={"song", "trust"},
    ),
    "dew_washing": Rite(
        "dew_washing",
        "the dew washing",
        "the dew washing at the roots",
        "Together they gathered bright dew on their forelegs and cleaned the dust from one another's shells before speaking the truth of their hurt.",
        "Cleaned of dust and hot words, they stood close again.",
        {"trust"},
        2,
        tags={"dew", "trust"},
    ),
    "shared_push": Rite(
        "shared_push",
        "the shared push",
        "the shared push with joined steps",
        "Without speaking much, they set shoulder and horn together and found one rhythm again.",
        "The hard work itself taught their breathing to agree.",
        {"work"},
        3,
        tags={"labor", "strength"},
    ),
    "vow_and_push": Rite(
        "vow_and_push",
        "the vow and push",
        "the vow and push before the elder",
        'The first sibling said, "I hurt you and left you with my share. I will not do so again," and the second sibling answered, "Then let us mend it together."',
        "With the vow spoken aloud, they bent to the ball as one family again.",
        {"trust", "work"},
        3,
        tags={"vow", "labor", "trust"},
    ),
    "reed_braid": Rite(
        "reed_braid",
        "the braid of reeds",
        "the braid of river reeds",
        "They braided a thin green ring of reeds around the split place, and while their legs worked, they traded honest words until hurt gave way to listening.",
        "The green braid held the seam while their new kindness held the rest.",
        {"trust", "work"},
        2,
        tags={"reeds", "mending", "trust"},
    ),
}

FIRST_NAMES = ["Ketu", "Rami", "Naro", "Sefu", "Tamu", "Bako"]
SECOND_NAMES = ["Luma", "Sira", "Miri", "Zali", "Nema", "Tula"]
ELDER_NAMES = ["Old Shell", "Grandmother Carapace", "River Back", "Dust Aunt"]

KNOWLEDGE = {
    "dung": [(
        "What is dung?",
        "Dung is animal poop. In nature it can feed soil and small creatures, and some beetles even use it to make food balls and nursery balls."
    )],
    "reproductive": [(
        "What does reproductive mean?",
        "Reproductive means connected to making new living things, like eggs, seeds, or babies. In this myth, it means the hidden promise of new life for the next season."
    )],
    "reconciliation": [(
        "What is reconciliation?",
        "Reconciliation means making peace after a quarrel. It usually needs honest words, listening, and a choice to work kindly again."
    )],
    "beetle": [(
        "What is a dung beetle?",
        "A dung beetle is a kind of beetle that rolls balls of dung. Some dung beetles use those balls for food or for raising their young."
    )],
    "dew": [(
        "What is dew?",
        "Dew is tiny drops of water that gather on plants when the air turns cool. In stories it often feels gentle and clean."
    )],
    "marsh": [(
        "What is a marsh?",
        "A marsh is a wet place with shallow water and many reeds or grasses. Birds, insects, and frogs often live there."
    )],
    "myth": [(
        "What is a myth?",
        "A myth is an old story people tell to explain the world or teach a lesson. Myths often make the sun, rivers, animals, and feelings seem full of meaning."
    )],
}
KNOWLEDGE_ORDER = ["myth", "dung", "beetle", "reproductive", "reconciliation", "dew", "marsh"]


@dataclass
class StoryParams:
    realm: str
    dung: str
    dispute: str
    rite: str
    first_name: str
    first_type: str
    second_name: str
    second_type: str
    elder_name: str
    seed: Optional[int] = None


def pair_noun(first: Entity, second: Entity) -> str:
    if first.type == "brother" and second.type == "sister":
        return "a brother and a sister"
    if first.type == "brother" and second.type == "brother":
        return "two brothers"
    if first.type == "sister" and second.type == "sister":
        return "two sisters"
    return "two siblings"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    realm, dung, dispute, rite = f["realm"], f["dung"], f["dispute"], f["rite"]
    return [
        f'Write a short myth for a young child that includes the words "reproductive" and "{dung.id if dung.id != "antelope" else "dung"}" and ends with reconciliation.',
        f"Tell a myth where sacred beetle siblings quarrel over a dawn-ball of {dung.label}, causing trouble in {realm.id.replace('_', ' ')}, and then heal the hurt through {rite.label}.",
        f"Write a child-facing origin tale where a quarrel born from {dispute.id.replace('_', ' ')} makes the morning falter until family members choose peace and shared work again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    first, second, elder = f["first"], f["second"], f["elder"]
    realm, dung, dispute, rite = f["realm"], f["dung"], f["dispute"], f["rite"]
    pair = pair_noun(first, second)
    harm = f.get("predicted_harm", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {first.id} and {second.id}, and {elder.id}, the old scarab elder. They live in a mythic place where the siblings help roll the dawn-ball."
        ),
        (
            "What was special about the dung ball?",
            f"It was a dawn-ball made of {dung.phrase}, and the elders believed it carried a reproductive promise inside it. That promise stood for new life returning to the world."
        ),
        (
            "Why did the world grow dim?",
            f"The world grew dim because the siblings quarreled and stopped rolling the ball together. When the ball stalled, morning weakened and the earth began to thirst."
        ),
    ]
    if dispute.cracks_ball:
        qa.append((
            "Did the ball break?",
            "Yes. The quarrel made the dawn-ball strike a stone and crack open. Seeing that dark seam helped the siblings understand how serious their anger had become."
        ))
    qa.append((
        "How did they reconcile?",
        f"They reconciled through {rite.label}. The rite worked because it healed the hurt between them and gave them a way to move the ball together again."
    ))
    if harm.get("risk", 0) >= THRESHOLD:
        qa.append((
            "Why were they frightened after the quarrel?",
            "They were frightened because the crack showed the hidden life inside the ball was in danger. The fear came from seeing that their angry moment could hurt more than just their feelings."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the siblings in peace, rolling the {dung.label} ball together again. The brightening sky showed that reconciliation had changed the whole world."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"myth", "dung", "beetle", "reproductive", "reconciliation"}
    if "dew" in f["rite"].tags:
        tags.add("dew")
    if f["realm"].id == "reed_marsh":
        tags.add("marsh")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("reed_marsh", "antelope", "boast", "apology_song", "Ketu", "brother", "Luma", "sister", "Old Shell"),
    StoryParams("red_plain", "buffalo", "broken_promise", "reed_braid", "Rami", "brother", "Sira", "sister", "Grandmother Carapace"),
    StoryParams("river_bend", "elephant", "careless_shove", "vow_and_push", "Naro", "brother", "Miri", "sister", "River Back"),
    StoryParams("reed_marsh", "buffalo", "broken_promise", "vow_and_push", "Sefu", "brother", "Tula", "sister", "Dust Aunt"),
]


ASP_RULES = r"""
needs_met(Ds, Rt) :- dispute(Ds), rite(Rt), not missing_need(Ds, Rt).
missing_need(Ds, Rt) :- needs(Ds, N), not repairs(Rt, N).

strong_enough(Dg, Rt) :- dung(Dg), rite(Rt), weight(Dg, W), strength(Rt, S), S >= W.

valid(Realm, Dg, Ds, Rt) :- realm(Realm), dung(Dg), dispute(Ds), rite(Rt),
                            needs_met(Ds, Rt), strong_enough(Dg, Rt).
outcome(reconciled) :- chosen_dung(Dg), chosen_dispute(Ds), chosen_rite(Rt),
                       needs_met(Ds, Rt), strong_enough(Dg, Rt).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for did, dung in DUNG_KINDS.items():
        lines.append(asp.fact("dung", did))
        lines.append(asp.fact("weight", did, dung.weight))
    for sid, dispute in DISPUTES.items():
        lines.append(asp.fact("dispute", sid))
        for need in sorted(dispute.needs):
            lines.append(asp.fact("needs", sid, need))
    for rid, rite in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("strength", rid, rite.strength))
        for rep in sorted(rite.repairs):
            lines.append(asp.fact("repairs", rid, rep))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_dung", params.dung),
        asp.fact("chosen_dispute", params.dispute),
        asp.fact("chosen_rite", params.rite),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    return "reconciled" if valid_combo(DUNG_KINDS[params.dung], DISPUTES[params.dispute], RITES[params.rite]) else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    for seed in range(12):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        smoke_cases.append(params)

    bad = 0
    for params in smoke_cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(smoke_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(smoke_cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: sacred dung beetle siblings quarrel, then reconcile and restore dawn."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--dung", choices=DUNG_KINDS)
    ap.add_argument("--dispute", choices=DISPUTES)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--first-name")
    ap.add_argument("--second-name")
    ap.add_argument("--elder-name")
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


def _pick_names(rng: random.Random, first_arg: Optional[str], second_arg: Optional[str], elder_arg: Optional[str]) -> tuple[str, str, str]:
    first = first_arg or rng.choice(FIRST_NAMES)
    second_pool = [n for n in SECOND_NAMES if n != first]
    second = second_arg or rng.choice(second_pool)
    elder = elder_arg or rng.choice(ELDER_NAMES)
    return first, second, elder


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dung and args.dispute and args.rite:
        dung, dispute, rite = DUNG_KINDS[args.dung], DISPUTES[args.dispute], RITES[args.rite]
        if not valid_combo(dung, dispute, rite):
            raise StoryError(explain_rejection(dung, dispute, rite))

    combos = [
        c for c in valid_combos()
        if (args.realm is None or c[0] == args.realm)
        and (args.dung is None or c[1] == args.dung)
        and (args.dispute is None or c[2] == args.dispute)
        and (args.rite is None or c[3] == args.rite)
    ]
    if not combos:
        if args.dung and args.dispute and args.rite:
            raise StoryError(explain_rejection(DUNG_KINDS[args.dung], DISPUTES[args.dispute], RITES[args.rite]))
        raise StoryError("(No valid combination matches the given options.)")

    realm, dung, dispute, rite = rng.choice(sorted(combos))
    first_name, second_name, elder_name = _pick_names(rng, args.first_name, args.second_name, args.elder_name)
    return StoryParams(
        realm=realm,
        dung=dung,
        dispute=dispute,
        rite=rite,
        first_name=first_name,
        first_type="brother",
        second_name=second_name,
        second_type="sister",
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        REALMS[params.realm],
        DUNG_KINDS[params.dung],
        DISPUTES[params.dispute],
        RITES[params.rite],
        params.first_name,
        params.first_type,
        params.second_name,
        params.second_type,
        params.elder_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, dung, dispute, rite) combos:\n")
        for realm, dung, dispute, rite in combos:
            print(f"  {realm:11} {dung:9} {dispute:15} {rite}")
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
            header = f"### {p.first_name} and {p.second_name}: {p.dispute} with {p.dung} dung in {p.realm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
