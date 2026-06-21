#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quadruple_tailor_inventory_reconciliation_tall_tale.py
=====================================================================================

A tiny tall-tale storyworld about a tailor, an inventory ledger, a quadruple
order mix-up, and a reconciliation that puts the shop right again.

The world is deliberately small and classical:
- one tailor shop
- one big inventory ledger
- one overblown mistaken order
- one child-facing reconciliation beat
- one ending image that proves what changed

The story stays state-driven: cloth bolts get counted, promises get made,
feelings rise and settle, and the shop ends with a repaired inventory and a
reconciled friendship.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/quadruple_tailor_inventory_reconciliation_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/quadruple_tailor_inventory_reconciliation_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/quadruple_tailor_inventory_reconciliation_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/quadruple_tailor_inventory_reconciliation_tall_tale.py --verify
    python storyworlds/worlds/gpt-5.4-mini/quadruple_tailor_inventory_reconciliation_tall_tale.py --json
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Pattern:
    id: str
    scene: str
    tale: str
    boast: str
    mishap: str
    mended: str
    finish: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Cloth:
    id: str
    label: str
    phrase: str
    color: str
    count: int
    unit: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class InventoryItem:
    id: str
    label: str
    phrase: str
    count: int
    unit: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    tailor = world.get("tailor")
    partner = world.get("partner")
    if tailor.memes["shame"] >= THRESHOLD and partner.memes["hurt"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            tailor.memes["apology"] += 1
            partner.memes["forgive"] += 1
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("reconcile", "social", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tally_inventory(world: World) -> int:
    return sum(v for e in list(world.entities.values()) for v in e.meters.values())


def predict_mistake(world: World, order: Cloth, inventory: InventoryItem) -> dict:
    sim = world.copy()
    sim.get("tailor").memes["panic"] += 1
    sim.get("partner").memes["hurt"] += 1
    sim.get("ledger").meters["missing"] += order.count
    return {
        "missing": sim.get("ledger").meters["missing"] + max(0, order.count - inventory.count),
        "hurt": sim.get("partner").memes["hurt"],
    }


def setup(world: World, pattern: Pattern, tailor: Entity, partner: Entity,
          cloth: Cloth, stock: InventoryItem) -> None:
    tailor.memes["pride"] += 1
    partner.memes["trust"] += 1
    world.say(
        f"On a windy morning, {tailor.id} kept a tailor shop where the needles "
        f"rang like little bells. The shelves held an inventory ledger, and the "
        f"ledger was so wide it could have been a wagon wheel lying flat."
    )
    world.say(
        f"{partner.id} helped at the counter, and together they watched the "
        f"{pattern.scene}. {pattern.tale}"
    )
    world.say(
        f'{tailor.id} puffed up and said, "{pattern.boast}"'
    )
    world.say(
        f"The shop had {cloth.count} {cloth.unit} of {cloth.color} {cloth.label} "
        f"and {stock.count} {stock.unit} of {stock.label} in the inventory."
    )


def mistake(world: World, tailor: Entity, partner: Entity, cloth: Cloth,
            stock: InventoryItem) -> None:
    tailor.memes["greed"] += 1
    partner.memes["worry"] += 1
    world.say(
        f"A customer order came in for a {cloth.label} as long as a barn roof, "
        f"but {tailor.id} misread the inventory and thought the shop had a "
        f"quadruple load of cloth."
    )
    world.say(
        f'By candlelight, {tailor.id} started cutting too much at once, and '
        f'{partner.id} gasped because the shelves were not nearly that full.'
    )


def warn(world: World, partner: Entity, tailor: Entity, cloth: Cloth,
         stock: InventoryItem) -> bool:
    pred = predict_mistake(world, cloth, stock)
    if pred["missing"] < 4:
        return False
    partner.memes["hurt"] += 1
    tailor.memes["shame"] += 1
    world.say(
        f'"Stop!" {partner.id} cried. "If you cut quadruple what we have, the '
        f"inventory will come up short, and the whole shop will look foolish."
    )
    world.say(
        f"{partner.id} pointed at the ledger, where the counted stacks did not "
        f"match the boast."
    )
    return True


def defy(world: World, tailor: Entity) -> None:
    tailor.memes["stubborn"] += 1
    world.say(
        f"{tailor.id} thumped {tailor.pronoun('possessive')} chest and said the "
        f"tallest tale in town: that a tailor could always sew first and count "
        f"later."
    )


def reconciliation(world: World, tailor: Entity, partner: Entity, cloth: Cloth,
                   stock: InventoryItem) -> None:
    tailor.memes["shame"] += 1
    partner.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {tailor.id} looked at the torn layout, looked at the honest ledger, "
        f"and took a deep breath."
    )
    world.say(
        f'"I was wrong," {tailor.id} said. "I should have checked the inventory '
        f"before I bragged."
    )
    world.say(
        f'{partner.id} softened at once. "Let’s mend it together," {partner.id} '
        f'said, and the two of them began sorting every bolt by hand.'
    )


def repair(world: World, tailor: Entity, partner: Entity, cloth: Cloth,
           stock: InventoryItem) -> None:
    tailor.memes["relief"] += 1
    partner.memes["relief"] += 1
    stock.meters["sorted"] += 1
    world.get("ledger").meters["reconciled"] += 1
    world.say(
        f"They counted the inventory again, one bright bolt at a time, until the "
        f"ledger matched the shelves and the shelves matched the truth."
    )
    world.say(
        f"Together they trimmed the cloth to fit the real order, and not a thread "
        f"more."
    )


def ending(world: World, pattern: Pattern, tailor: Entity, partner: Entity) -> None:
    tailor.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{pattern.mended} {pattern.finish}. The shop window glowed with the "
        f"finished work, and the inventory ledger now sat square and neat on the "
        f"counter like a contented bluejay."
    )
    world.say(
        f"{tailor.id} and {partner.id} laughed, shoulder to shoulder, because "
        f"their reconciliation had turned a brag into a better day."
    )


def tell(pattern: Pattern, cloth: Cloth, stock: InventoryItem,
         tailor_name: str = "Milo", partner_name: str = "June",
         tailor_gender: str = "boy", partner_gender: str = "girl") -> World:
    world = World()
    tailor = world.add(Entity(id=tailor_name, kind="character", type=tailor_gender, role="tailor"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    ledger = world.add(Entity(id="ledger", type="ledger", label="inventory ledger"))
    cloth_ent = world.add(Entity(id="cloth", type="cloth", label=cloth.label))
    stock_ent = world.add(Entity(id="stock", type="stock", label=stock.label))
    cloth_ent.meters["count"] = cloth.count
    stock_ent.meters["count"] = stock.count
    ledger.meters["counted"] = stock.count

    setup(world, pattern, tailor, partner, cloth, stock)
    world.para()
    mistake(world, tailor, partner, cloth, stock)
    warn(world, partner, tailor, cloth, stock)
    defy(world, tailor)
    world.para()
    reconciliation(world, tailor, partner, cloth, stock)
    repair(world, tailor, partner, cloth, stock)
    world.para()
    ending(world, pattern, tailor, partner)

    world.facts.update(
        tailor=tailor,
        partner=partner,
        pattern=pattern,
        cloth=cloth,
        stock=stock,
        ledger=ledger,
        reconciled=True,
        inventory_after=stock.count,
        tally=tally_inventory(world),
    )
    return world


PATTERNS = {
    "river": Pattern(
        "river",
        "the river of ribbon and rain",
        "The tailor shop sat beside a river so talkative it could gossip through the windows.",
        "I can stitch a quadruple cape before the kettle boils!",
        "But the inventory was not a mountain, and the extra cuts would leave the shelves bare.",
        "In the end, the tailor and the helper reconciled their quarrel with honest counting.",
        "By dusk, the cape hung straight as a fence post, and peace shone brighter than the brass buttons.",
    ),
    "fair": Pattern(
        "fair",
        "the county fair with its brass band",
        "A brass band played down the street, and the tailor shop shook with the thump of parade drums.",
        "I can make a quadruple banner fit from one little stack of cloth!",
        "But the inventory did not stretch like taffy, and the helper knew it would not be enough.",
        "Soon the tailor and the helper reconciled and set about the job with calmer hands.",
        "By sunset, the banner fluttered fine and the ledger was neat as a prayer book.",
    ),
    "harbor": Pattern(
        "harbor",
        "the harbor wind and the gulls",
        "Seagulls argued over crumbs on the roof, as if they too kept an inventory of treasure.",
        "I can sew a quadruple coat and still have cloth left for a crown!",
        "But the inventory was smaller than the boast, and the helper saw the danger at once.",
        "After a proper apology, the tailor and the helper reconciled and worked side by side.",
        "At last the coat gleamed on its hook, and the shop felt as steady as a lighthouse.",
    ),
}

CLOTHS = {
    "cape": Cloth("cape", "cape", "a cape", "blue", 4, "bolts", {"tall-tale"}),
    "banner": Cloth("banner", "banner", "a banner", "red", 4, "bolts", {"tall-tale"}),
    "coat": Cloth("coat", "coat", "a coat", "green", 4, "bolts", {"tall-tale"}),
}

INVENTORY = {
    "bolts": InventoryItem("bolts", "bolts of cloth", "bolts of cloth", 3, "bolts", {"inventory"}),
    "spools": InventoryItem("spools", "spools of thread", "spools of thread", 6, "spools", {"inventory"}),
    "buttons": InventoryItem("buttons", "tin buttons", "tin buttons", 12, "buttons", {"inventory"}),
}

GIRL_NAMES = ["June", "Nell", "Ada", "Mina", "Ivy", "Rose"]
BOY_NAMES = ["Milo", "Otto", "Ezra", "Finn", "Levi", "Noel"]


@dataclass
@dataclass
class StoryParams:
    pattern: str
    cloth: str
    inventory: str
    tailor_name: str
    tailor_gender: str
    partner_name: str
    partner_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PATTERNS:
        for c in CLOTHS:
            for inv in INVENTORY:
                combos.append((p, c, inv))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about a tailor, inventory, and reconciliation.")
    ap.add_argument("--pattern", choices=PATTERNS)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--inventory", choices=INVENTORY)
    ap.add_argument("--tailor-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--tailor-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.pattern is None or c[0] == args.pattern)
              and (args.cloth is None or c[1] == args.cloth)
              and (args.inventory is None or c[2] == args.inventory)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pattern, cloth, inv = rng.choice(sorted(combos))
    tailor_gender = args.tailor_gender or rng.choice(["boy", "girl"])
    partner_gender = args.partner_gender or ("girl" if tailor_gender == "boy" else "boy")
    tailor_name = args.tailor_name or rng.choice(GIRL_NAMES if tailor_gender == "girl" else BOY_NAMES)
    partner_pool = [n for n in (GIRL_NAMES if partner_gender == "girl" else BOY_NAMES) if n != tailor_name]
    partner_name = args.partner_name or rng.choice(partner_pool)
    return StoryParams(pattern, cloth, inv, tailor_name, tailor_gender, partner_name, partner_gender)


def reasonableness_gate(params: StoryParams) -> bool:
    return True


ASP_RULES = r"""
valid(P, C, I) :- pattern(P), cloth(C), inventory(I).
reconcile_story(P, C, I) :- valid(P, C, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PATTERNS:
        lines.append(asp.fact("pattern", p))
    for c in CLOTHS:
        lines.append(asp.fact("cloth", c))
    for i in INVENTORY:
        lines.append(asp.fact("inventory", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        return 1
    print("OK: smoke-test generate() produced a story.")
    return rc


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the words "quadruple", "tailor", and "inventory".',
        f"Tell a playful story where {f['tailor'].id} boasts about a quadruple order, then makes peace with {f['partner'].id} after checking the inventory.",
        f'Write a story about a tailor, a mistaken inventory count, and reconciliation that ends with everyone feeling proud.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tailor = f["tailor"]
    partner = f["partner"]
    pattern = f["pattern"]
    cloth = f["cloth"]
    stock = f["stock"]
    qa = [
        ("Who is the story about?",
         f"It is about {tailor.id}, a tailor, and {partner.id}, who helped at the counter. They worked in a shop with an inventory ledger and a big cloth order."),
        ("What went wrong?",
         f"{tailor.id} bragged about a quadruple job and misread the inventory, so there was not enough cloth for the order. That mistake could have left the shelves short and the helper worried."),
        ("How did they fix it?",
         f"They reconciled by apologizing, counting the inventory again, and cutting the cloth to match the real stock. Working together helped them turn the problem into a neat finish."),
        ("How did the story end?",
         f"It ended with the {cloth.label} finished, the inventory put back in order, and the two of them smiling together. The reconciliation made the shop calm again."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tailor?",
         "A tailor is a person who makes or repairs clothes by cutting and sewing cloth."),
        ("What is inventory?",
         "Inventory is the list or count of things a shop has on hand, like cloth, thread, or buttons."),
        ("What does reconciliation mean?",
         "Reconciliation means making peace after a disagreement, often by apologizing and working together again."),
        ("What does quadruple mean?",
         "Quadruple means four times as much or four parts together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("river", "cape", "bolts", "Milo", "boy", "June", "girl"),
    StoryParams("fair", "banner", "spools", "Ada", "girl", "Otto", "boy"),
    StoryParams("harbor", "coat", "buttons", "Ezra", "boy", "Nell", "girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PATTERNS[params.pattern], CLOTHS[params.cloth], INVENTORY[params.inventory],
                 params.tailor_name, params.partner_name, params.tailor_gender, params.partner_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
