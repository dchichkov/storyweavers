#!/usr/bin/env python3
"""
storyworlds/worlds/shiny_river_wagon_ghost.py
=============================================

Seed prompt used:
    Words: shiny river, cozy wagon
    Features: Flashback, Conflict
    Style: Ghost Story

Source tale written from the seed
----------------------------------
Theo and June pulled their cozy wagon beside the shiny river. In the reeds they
found a silver bell tied with a blue thread. Theo wanted to keep it for their
wagon. June said it felt like it belonged to someone.

The river flashed white, and a small ghost appeared in the mist. In a soft
flashback, she showed them a stormy day long ago when her bell slipped from her
boat and sank near the willow dock. Theo still wanted to keep the bell, but the
ghost looked lonelier each time he closed his hand around it.

June predicted that if they ran along the slick bank with the bell loose, it
could fall into the river again. So they wrapped it in the wagon blanket, pulled
the cozy wagon slowly to the dock, and hung the bell on the willow branch. It
rang once. The ghost smiled, the river shone silver instead of cold white, and
Theo said the wagon sounded better carrying friends than keeping treasures.

This world turns that tale into a tiny state model: a found keepsake carries
memory, sibling conflict accumulates when one child wants to keep it, a ghostly
flashback embeds the ownership claim, and a return plan is valid only when its
carrier can protect the object across the risky riverbank.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def name(self) -> str:
        return self.label or self.id

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "sister", "mother", "woman", "ghost_girl"}
        male = {"boy", "brother", "father", "man", "ghost_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class River:
    id: str
    phrase: str
    bank: str
    risk: int
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    fragility: int
    flashback: str
    return_place: str
    final_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    cushion: int
    steady: int
    sense: int
    packing: str
    travel: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, river: River) -> None:
        self.river = river
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.carrier: Optional[Carrier] = None

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
        clone = World(self.river)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.carrier = copy.deepcopy(self.carrier)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _carrier_safe(world: World, keepsake: Keepsake) -> bool:
    c = world.carrier
    return bool(c and c.sense >= SENSE_MIN and c.cushion >= keepsake.fragility and c.steady >= world.river.risk)


def _r_unsettled_ghost(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    keepsake = world.entities.get("keepsake")
    if not ghost or not keepsake:
        return []
    if keepsake.meters["found"] < THRESHOLD or keepsake.meters["returned"] >= THRESHOLD:
        return []
    sig = ("unsettled", ghost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["longing"] += 1
    keepsake.memes["memory"] += 1
    return []


def _r_conflict(world: World) -> list[str]:
    keeper = world.entities.get("keeper")
    returner = world.entities.get("returner")
    if not keeper or not returner:
        return []
    if keeper.memes["want_keep"] < THRESHOLD or returner.memes["want_return"] < THRESHOLD:
        return []
    sig = ("conflict", keeper.id, returner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper.memes["conflict"] += 1
    returner.memes["conflict"] += 1
    return []


def _r_river_loss_risk(world: World) -> list[str]:
    keepsake = world.entities.get("keepsake")
    if not keepsake:
        return []
    if keepsake.meters["carried_bank"] < THRESHOLD:
        return []
    cfg: Keepsake = keepsake.attrs["cfg"]
    if _carrier_safe(world, cfg):
        return []
    sig = ("loss_risk", keepsake.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keepsake.meters["loss_risk"] += 1
    return []


def _r_release(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    keepsake = world.entities.get("keepsake")
    river = world.entities.get("river")
    if not ghost or not keepsake or not river:
        return []
    if keepsake.meters["returned"] < THRESHOLD:
        return []
    sig = ("release", ghost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["peace"] += 1
    ghost.memes["longing"] = 0
    river.meters["gentle_shine"] += 1
    return []


CAUSAL_RULES = [
    Rule("unsettled_ghost", "memeplex", _r_unsettled_ghost),
    Rule("conflict", "social", _r_conflict),
    Rule("river_loss_risk", "physical", _r_river_loss_risk),
    Rule("release", "memeplex", _r_release),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def keepsake_at_risk(river: River, keepsake: Keepsake) -> bool:
    return river.risk > 0 and keepsake.fragility > 0


def carrier_addresses(river: River, keepsake: Keepsake, carrier: Carrier) -> bool:
    return (keepsake_at_risk(river, keepsake)
            and carrier.sense >= SENSE_MIN
            and carrier.cushion >= keepsake.fragility
            and carrier.steady >= river.risk)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for rid, river in RIVERS.items():
        for kid, keepsake in KEEPSAKES.items():
            for cid, carrier in CARRIERS.items():
                if carrier_addresses(river, keepsake, carrier):
                    out.append((rid, kid, cid))
    return out


def _carry_bank(world: World, keepsake: Entity) -> None:
    keepsake.meters["carried_bank"] += 1
    propagate(world)


def predict_loss(world: World, keepsake: Entity) -> dict:
    sim = world.copy()
    _carry_bank(sim, sim.get(keepsake.id))
    return {"loss_risk": sim.get(keepsake.id).meters["loss_risk"]}


def arrive(world: World, keeper: Entity, returner: Entity) -> None:
    world.say(
        f"{keeper.name} and {returner.name} pulled their cozy wagon beside "
        f"{world.river.phrase}. {world.river.shine}"
    )
    world.add(Entity("river", "thing", "river", "river"))


def find_keepsake(world: World, keeper: Entity, returner: Entity, keepsake: Keepsake) -> None:
    item = world.get("keepsake")
    item.meters["found"] += 1
    keeper.memes["wonder"] += 1
    returner.memes["wonder"] += 1
    propagate(world)
    world.say(
        f"In the reeds they found {keepsake.phrase}. {keeper.name} wanted to tie "
        f"the {keepsake.label} to the wagon handle, but {returner.name} said it "
        f"felt like it belonged to someone."
    )


def appear_and_flashback(world: World, ghost: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"The river flashed pale white, and a small ghost appeared where the "
        f"water touched the reeds."
    )
    ghost.memes["memory"] += 1
    world.say(f"In a soft flashback, {ghost.pronoun()} showed them {keepsake.flashback}.")


def argue(world: World, keeper: Entity, returner: Entity, keepsake: Keepsake) -> None:
    keeper.memes["want_keep"] += 1
    returner.memes["want_return"] += 1
    propagate(world)
    if keeper.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{keeper.name} closed {keeper.pronoun("possessive")} hand around the '
            f'{keepsake.label}. "We found it," {keeper.pronoun()} said. '
            f'{returner.name} shook {returner.pronoun("possessive")} head. '
            f'"The river remembers it," {returner.pronoun()} answered.'
        )


def warn_loss(world: World, returner: Entity, keepsake: Keepsake) -> None:
    pred = predict_loss(world, world.get("keepsake"))
    world.facts["predicted_loss"] = pred["loss_risk"]
    if pred["loss_risk"] >= THRESHOLD:
        world.say(
            f"{returner.name} looked at {world.river.bank}. If they ran with the "
            f"{keepsake.label} loose, it could slip into {world.river.phrase} all over again."
        )


def pack_and_return(world: World, keeper: Entity, returner: Entity,
                    ghost: Entity, keepsake: Keepsake, carrier: Carrier) -> None:
    world.carrier = carrier
    item = world.get("keepsake")
    packing = carrier.packing.replace("the keepsake", f"the {keepsake.label}")
    world.say(f"So they chose the careful way. {packing}")
    _carry_bank(world, item)
    if item.meters["loss_risk"] >= THRESHOLD:
        raise StoryError("(Internal error: unsafe carrier reached the renderer.)")
    world.say(carrier.travel)
    item.meters["returned"] += 1
    keeper.memes["conflict"] = 0
    returner.memes["conflict"] = 0
    propagate(world)
    world.say(
        f"At {keepsake.return_place}, they placed the {keepsake.label} where the "
        f"ghost could see it. {keepsake.final_sound}"
    )
    if ghost.memes["peace"] >= THRESHOLD:
        world.say(
            f"The ghost smiled, the river shone silver instead of cold white, "
            f"and {keeper.name} said the wagon sounded better carrying friends "
            f"than keeping treasures."
        )


def tell(river: River, keepsake: Keepsake, carrier: Carrier, keeper_name: str,
         keeper_gender: str, returner_name: str, returner_gender: str,
         ghost_gender: str, trait: str) -> World:
    world = World(river)
    keeper = world.add(Entity("keeper", "character", keeper_gender, keeper_name, "keeper", [trait]))
    returner = world.add(Entity("returner", "character", returner_gender, returner_name, "returner", ["careful"]))
    ghost_type = "ghost_girl" if ghost_gender == "girl" else "ghost_boy"
    ghost = world.add(Entity("ghost", "character", ghost_type, "the ghost", "ghost"))
    world.add(Entity("keepsake", "thing", "keepsake", keepsake.label, attrs={"cfg": keepsake}))

    arrive(world, keeper, returner)
    find_keepsake(world, keeper, returner, keepsake)
    world.para()
    appear_and_flashback(world, ghost, keepsake)
    argue(world, keeper, returner, keepsake)
    warn_loss(world, returner, keepsake)
    world.para()
    pack_and_return(world, keeper, returner, ghost, keepsake, carrier)

    world.facts.update(
        keeper=keeper, returner=returner, ghost=ghost, river=river,
        keepsake=keepsake, carrier=carrier,
        conflict=True, released=ghost.memes["peace"] >= THRESHOLD,
        predicted_loss=world.facts.get("predicted_loss", 0),
    )
    return world


RIVERS = {
    "shiny": River(
        "shiny", "the shiny river", "the slick clay bank", 2,
        "Sunlight made the water flash like a ribbon of coins.",
        tags={"river", "shiny"}),
    "moonlit": River(
        "moonlit", "the moonlit river", "the mossy stones near the old dock", 2,
        "The water held a stripe of moonlight even before evening came.",
        tags={"river", "moonlight"}),
    "reed": River(
        "reed", "the reed-fringed river", "the tangly reed bank", 1,
        "Dragonflies hovered over the bright green reeds.",
        tags={"river", "reeds"}),
}

KEEPSAKES = {
    "silver_bell": Keepsake(
        "silver_bell", "bell", "a silver bell tied with a blue thread", 2,
        "a stormy day long ago when the bell slipped from a small boat and sank near the willow dock",
        "the willow dock", "The bell rang once, clear and small.",
        tags={"bell", "memory"}),
    "glass_button": Keepsake(
        "glass_button", "button", "a glass coat button glowing like a drop of rain", 3,
        "a winter morning when the coat button popped away during a goodbye wave from the ferry",
        "the ferry post", "The button caught the light and warmed like a tiny window.",
        tags={"glass", "memory"}),
    "wooden_whistle": Keepsake(
        "wooden_whistle", "whistle", "a wooden whistle carved with little stars", 1,
        "a summer evening when the whistle fell from a wagon as the river fog rolled in",
        "the leaning alder tree", "The whistle gave one soft note that sounded like thank you.",
        tags={"whistle", "memory"}),
}

CARRIERS = {
    "cozy_wagon": Carrier(
        "cozy_wagon", "cozy wagon blanket", 3, 3, 3,
        "They wrapped the keepsake in the wagon blanket and nested it in the cozy wagon.",
        "Then they pulled the cozy wagon slowly along the safe path to the water.",
        tags={"wagon", "care"}),
    "padded_box": Carrier(
        "padded_box", "padded button box", 3, 2, 3,
        "They tucked the keepsake inside a padded button box before setting it in the wagon.",
        "The box rode in the wagon without rattling as they followed the dry stones.",
        tags={"box", "care"}),
    "mittens": Carrier(
        "mittens", "soft mittens", 2, 1, 2,
        "They cupped the keepsake between two soft mittens.",
        "They walked slowly, passing it from mitten to mitten whenever the path narrowed.",
        tags={"care"}),
    "paper_bag": Carrier(
        "paper_bag", "paper bag", 1, 1, 1,
        "They dropped the keepsake into a paper bag.",
        "The paper bag swung from one hand.",
        tags={"paper"}),
}

GIRL_NAMES = ["June", "Mia", "Nora", "Ava", "Rose"]
BOY_NAMES = ["Theo", "Sam", "Leo", "Ben", "Max"]
TRAITS = ["curious", "stubborn", "gentle", "bold", "thoughtful"]


@dataclass
class StoryParams:
    river: str
    keepsake: str
    carrier: str
    keeper: str
    keeper_gender: str
    returner: str
    returner_gender: str
    ghost_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "river": [("What is a river?",
               "A river is moving water that flows across land. Its banks can be slippery, so people should be careful near it.")],
    "shiny": [("Why can a river look shiny?",
               "Sunlight or moonlight can bounce off moving water. That reflected light makes the river sparkle.")],
    "memory": [("What is a keepsake?",
                "A keepsake is a small object someone saves because it reminds them of a person, place, or important moment.")],
    "wagon": [("What is a wagon good for?",
               "A wagon can carry things slowly and steadily. A blanket inside can keep delicate things from bumping around.")],
    "bell": [("How does a bell make sound?",
              "A bell rings when something inside or beside it taps the metal and makes it vibrate.")],
    "glass": [("Why should glass be carried carefully?",
               "Glass can chip or break if it hits something hard, so it needs padding and a steady hand.")],
    "care": [("Why is going slowly sometimes safer?",
              "Going slowly gives you time to see slippery places and hold things carefully, especially near water.")],
}
KNOWLEDGE_ORDER = ["river", "shiny", "memory", "wagon", "bell", "glass", "care"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a ghost story for a 3-to-5-year-old that includes "shiny river" and "cozy wagon" plus a flashback and a conflict.',
        f"Tell a gentle ghost story where {f['keeper'].name} wants to keep {f['keepsake'].phrase}, but {f['returner'].name} helps return it.",
        "Write a story where a found keepsake carries a memory, and the ending proves the ghost is at peace.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    keeper, returner, ghost = f["keeper"], f["returner"], f["ghost"]
    keepsake, carrier, river = f["keepsake"], f["carrier"], f["river"]
    return [
        ("Who is the story about?",
         f"It is about {keeper.name}, {returner.name}, and a small ghost by {river.phrase}. The children have a cozy wagon and find a keepsake near the water."),
        ("What did the children find?",
         f"They found {keepsake.phrase}. {keeper.name} wanted to keep it, but {returner.name} felt it belonged to someone else."),
        ("What did the flashback show?",
         f"The flashback showed {keepsake.flashback}. That memory explained why the ghost was lonely and why the keepsake should be returned."),
        ("Why did the children argue?",
         f"They argued because {keeper.name} wanted to keep the {keepsake.label}, while {returner.name} wanted to return it to the ghost. The conflict grew from two different feelings about the same object."),
        ("Why did they use the careful carrier?",
         f"They used the {carrier.label} because {river.bank} could make the {keepsake.label} slip into the river again. The carrier protected the object and kept the promise from being broken."),
        ("How did the story end?",
         f"They returned the {keepsake.label} at {keepsake.return_place}, and the ghost found peace. The final image is the river shining gently while the wagon carries friends instead of kept treasure."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["river"].tags) | set(f["keepsake"].tags) | set(f["carrier"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:9} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  carrier: {world.carrier.id if world.carrier else 'none'}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("shiny", "silver_bell", "cozy_wagon", "Theo", "boy", "June", "girl", "girl", "stubborn"),
    StoryParams("moonlit", "glass_button", "cozy_wagon", "Mia", "girl", "Sam", "boy", "boy", "curious"),
    StoryParams("reed", "wooden_whistle", "mittens", "Leo", "boy", "Nora", "girl", "girl", "bold"),
]


def explain_rejection(river: River, keepsake: Keepsake, carrier: Carrier) -> str:
    if carrier.sense < SENSE_MIN:
        return f"(No story: {carrier.label} is too flimsy to be a trustworthy ghost-story solution.)"
    if carrier.cushion < keepsake.fragility:
        return (f"(No story: {keepsake.phrase} needs more padding than {carrier.label} gives. "
                "The return plan must protect the charged object.)")
    return (f"(No story: {carrier.label} is not steady enough for {river.bank}. "
            "The carrier must answer the actual riverbank risk.)")


ASP_RULES = r"""
at_risk(R,K) :- river(R), risk(R,N), N > 0, keepsake(K), fragility(K,F), F > 0.
sensible(C) :- carrier(C), sense(C,S), sense_min(M), S >= M.
protects(C,K) :- carrier(C), keepsake(K), cushion(C,N), fragility(K,F), N >= F.
steady_for(C,R) :- carrier(C), river(R), steady(C,N), risk(R,F), N >= F.
valid(R,K,C) :- at_risk(R,K), sensible(C), protects(C,K), steady_for(C,R).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for rid, river in RIVERS.items():
        lines.append(asp.fact("river", rid))
        lines.append(asp.fact("risk", rid, river.risk))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("fragility", kid, keepsake.fragility))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("cushion", cid, carrier.cushion))
        lines.append(asp.fact("steady", cid, carrier.steady))
        lines.append(asp.fact("sense", cid, carrier.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: shiny river, cozy wagon, ghostly flashback, and conflict.")
    ap.add_argument("--river", choices=RIVERS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--keeper-gender", choices=["girl", "boy"])
    ap.add_argument("--returner-gender", choices=["girl", "boy"])
    ap.add_argument("--ghost-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--returner")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.river and args.keepsake and args.carrier:
        rv, ks, ca = RIVERS[args.river], KEEPSAKES[args.keepsake], CARRIERS[args.carrier]
        if not carrier_addresses(rv, ks, ca):
            raise StoryError(explain_rejection(rv, ks, ca))
    if args.carrier and CARRIERS[args.carrier].sense < SENSE_MIN:
        rv = RIVERS[args.river] if args.river else RIVERS["shiny"]
        ks = KEEPSAKES[args.keepsake] if args.keepsake else KEEPSAKES["silver_bell"]
        raise StoryError(explain_rejection(rv, ks, CARRIERS[args.carrier]))
    combos = [c for c in valid_combos()
              if (args.river is None or c[0] == args.river)
              and (args.keepsake is None or c[1] == args.keepsake)
              and (args.carrier is None or c[2] == args.carrier)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    river, keepsake, carrier = rng.choice(sorted(combos))
    kg = args.keeper_gender or rng.choice(["girl", "boy"])
    rg = args.returner_gender or rng.choice(["girl", "boy"])
    keeper = args.keeper or _pick_name(rng, kg)
    returner = args.returner or _pick_name(rng, rg, avoid=keeper)
    ghost_gender = args.ghost_gender or rng.choice(["girl", "boy"])
    trait = rng.choice(TRAITS)
    return StoryParams(river, keepsake, carrier, keeper, kg, returner, rg, ghost_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(RIVERS[params.river], KEEPSAKES[params.keepsake], CARRIERS[params.carrier],
                 params.keeper, params.keeper_gender, params.returner, params.returner_gender,
                 params.ghost_gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (river, keepsake, carrier) combos:\n")
        for river, keepsake, carrier in combos:
            print(f"  {river:8} {keepsake:14} {carrier}")
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
            header = f"### {p.keeper} & {p.returner}: {p.keepsake} at the {p.river} river ({p.carrier})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
