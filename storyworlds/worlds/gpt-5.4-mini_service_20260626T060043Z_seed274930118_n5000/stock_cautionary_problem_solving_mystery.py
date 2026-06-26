#!/usr/bin/env python3
"""
storyworlds/worlds/stock_cautionary_problem_solving_mystery.py
==============================================================

A small cautionary, problem-solving mystery storyworld about stock, shelves,
missing counts, and careful clue-following.

Premise:
- A child notices that a shop's stock is off.
- The shopkeeper worries because the missing item is needed soon.
- The child and keeper look for clues instead of guessing.
- The solution is careful, ordinary, and slightly surprising.
- The ending shows the stock put back in order.

This world is designed to feel like a tiny mystery: there is a gap in stock,
there are clues, there is a cautious search, and there is a satisfying fix.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    basket: object | None = None
    child: object | None = None
    keeper: object | None = None
    shelf: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    indoor: bool = True
    SETTING: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StockItem:
    id: str
    label: str
    phrase: str
    count: int
    clue: str
    caution: str
    fix: str
    risky: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    item: str
    child_name: str
    child_gender: str
    keeper: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def stock_phrase(item: StockItem, count: int) -> str:
    return f"{count} {item.label}" if count != 1 else f"1 {item.label}"


def build_inventory() -> dict[str, StockItem]:
    return {
        "candles": StockItem(
            id="candles",
            label="box of candles",
            phrase="a box of candles",
            count=12,
            clue="one side of the box had a clean stripe where a hand had slid it",
            caution="Don't guess or blame someone before looking at the shelves.",
            fix="put the box back where the cold air could not hide it behind other stock",
        ),
        "beans": StockItem(
            id="beans",
            label="bag of beans",
            phrase="a bag of beans",
            count=9,
            clue="a small trail of bean dust led to the counter",
            caution="Do not shake open bags when you are not sure what is missing.",
            fix="check the back shelf and count each bag one by one",
        ),
        "plums": StockItem(
            id="plums",
            label="crate of plums",
            phrase="a crate of plums",
            count=7,
            clue="one crate had a smudged label that looked turned around",
            caution="Be careful with fruit stock; a rushed hand can bruise it.",
            fix="turn the crate, read the label, and sort the fruit by name",
        ),
        "soap": StockItem(
            id="soap",
            label="stack of soap bars",
            phrase="a stack of soap bars",
            count=14,
            clue="the top bar had rolled into a paper bag near the till",
            caution="Quiet hands work better than quick hands in a crowded shop.",
            fix="count the bars in the bag and move them back to the display",
        ),
    }


INVENTORY = build_inventory()
SETTING = Setting(place="the corner shop", indoor=True)
GIRL_NAMES = ["Mina", "Tess", "Lila", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Arlo", "Finn", "Noah", "Eli"]


def caution_reason(item: StockItem) -> str:
    return item.caution


def story_turn(item: StockItem) -> str:
    return f"The missing count became a little mystery, so they followed the clue instead of guessing."


def simulate_shortage(world: World, child: Entity, item: StockItem, keeper: Entity) -> None:
    shelf = world.get("shelf")
    shelf.meters["stock"] = item.count
    shelf.meters["missing"] = 1
    child.memes["curiosity"] += 1
    keeper.memes["worry"] += 1
    world.facts["missing_item"] = item.id
    world.facts["clue"] = item.clue
    world.facts["fix"] = item.fix
    world.facts["starting_stock"] = item.count
    world.facts["ending_stock"] = item.count + 1


def _r_find_hidden_item(world: World) -> list[str]:
    out: list[str] = []
    shelf = world.get("shelf")
    basket = world.get("basket")
    if shelf.meters.get("missing", 0) < THRESHOLD:
        return out
    sig = ("found",)
    if sig in world.fired:
        return out
    if basket.meters.get("hidden_item", 0) >= THRESHOLD:
        world.fired.add(sig)
        shelf.meters["missing"] = 0
        shelf.meters["stock"] += 1
        basket.meters["hidden_item"] = 0
        out.append("The missing item was hiding in a basket, tucked under a receipt.")
    return out


def _r_calmed(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.get("keeper")
    shelf = world.get("shelf")
    if shelf.meters.get("missing", 0) >= THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["worry"] = 0
    keeper.memes["relief"] += 1
    out.append("The shopkeeper breathed out and smiled when the counts matched again.")
    return out


CAUSAL_RULES = [_r_find_hidden_item, _r_calmed]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def predict_resolution(world: World, item: StockItem) -> bool:
    sim = world.copy()
    sim.get("basket").meters["hidden_item"] = 1
    simulate_shortage(sim, sim.get("child"), item, sim.get("keeper"))
    propagate(sim, narrate=False)
    return sim.get("shelf").meters.get("missing", 0) == 0


def tell(item: StockItem, child_name: str, child_gender: str, keeper_type: str) -> World:
    world = World(SETTING)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label=f"the {keeper_type}"))
    shelf = world.add(Entity(id="shelf", type="shelf", label="front shelf"))
    basket = world.add(Entity(id="basket", type="basket", label="basket near the till"))
    basket.meters["hidden_item"] = 1

    world.say(
        f"{child.label} went with {keeper.label} to {SETTING.place} and noticed the stock on the front shelf."
    )
    world.say(
        f"There were {stock_phrase(item, item.count)} at first, but one space looked wrong."
    )

    world.para()
    world.say(
        f"{child.label} pointed to the shelf and said it looked as if one {item.label} had slipped away."
    )
    world.say(
        f"{keeper.label.capitalize()} did not rush to a guess. {caution_reason(item)}"
    )
    world.say(
        f"Instead, they followed the clue: {item.clue}."
    )

    world.para()
    simulate_shortage(world, child, item, keeper)
    world.say(story_turn(item))
    world.say(
        f"They checked the basket, counted slowly, and found the missing {item.label} tucked away by mistake."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{keeper.label.capitalize()} put the {item.label} back in its place, and the shelf looked tidy again."
    )
    world.say(
        f"By the end, the stock was back to {item.count + 1} {item.label}s, and the little mystery was solved."
    )

    world.facts.update(
        child=child,
        keeper=keeper,
        shelf=shelf,
        basket=basket,
        item=item,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    item = _safe_fact(world, world.facts, "item")
    child = _safe_fact(world, world.facts, "child")
    keeper = _safe_fact(world, world.facts, "keeper")
    return [
        f"Write a short mystery about a child named {child.label} who notices a problem with the stock of {item.label}s in a shop.",
        f"Tell a cautious, child-friendly story where {child.label} and {keeper.label} solve a small stock mystery without guessing too fast.",
        f"Write a simple problem-solving story about missing stock, careful counting, and a clue in a basket.",
    ]


def story_qa(world: World) -> list[QAItem]:
    item = _safe_fact(world, world.facts, "item")
    child = _safe_fact(world, world.facts, "child")
    keeper = _safe_fact(world, world.facts, "keeper")
    return [
        QAItem(
            question=f"What mystery did {child.label} notice at {SETTING.place}?",
            answer=f"{child.label} noticed that the stock of {item.label}s was not quite right and that one was missing from the shelf.",
        ),
        QAItem(
            question=f"Why did {keeper.label} avoid guessing right away?",
            answer=f"{keeper.label} knew it was safer to look for clues and count the stock carefully before blaming anyone or moving things too quickly.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They followed the clue, checked the basket near the till, found the missing {item.label}, and put it back on the shelf.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The stock was back in order, the missing item was found, and the shopkeeper felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is stock in a shop?",
            answer="Stock is the set of things a shop keeps on hand to sell, like boxes, bags, or fruit.",
        ),
        QAItem(
            question="Why is counting stock carefully useful?",
            answer="Counting carefully helps people notice when something is missing and keeps mistakes from spreading.",
        ),
        QAItem(
            question="Why is it a bad idea to guess before checking?",
            answer="Guessing too fast can lead to unfair blame or a wrong fix, so it is better to look for clues first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(Item) :- stock(Item, N), hidden(Item), N > 0.
solved(Item) :- stock(Item, N), recovered(Item), N > 0.
careful :- clue_seen.
safe_fix :- careful, solved(_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "shop"))
    for item_id, item in INVENTORY.items():
        lines.append(asp.fact("stock", item_id, item.count))
        lines.append(asp.fact("item", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary, problem-solving mystery about shop stock.")
    ap.add_argument("--item", choices=sorted(INVENTORY))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=["shopkeeper", "manager", "clerk"])
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
    item = getattr(args, "item", None) or rng.choice(sorted(INVENTORY))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper = getattr(args, "keeper", None) or rng.choice(["shopkeeper", "manager", "clerk"])
    return StoryParams(item=item, child_name=name, child_gender=gender, keeper=keeper)


def generate(params: StoryParams) -> StorySample:
    item = INVENTORY[params.item]
    world = tell(item, params.child_name, params.child_gender, params.keeper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def valid_combos() -> list[tuple[str, str]]:
    return [("shop", item_id) for item_id in INVENTORY]


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show stock/2."))
    asp_set = set(asp.atoms(model, "stock"))
    py_set = {(k, v.count) for k, v in INVENTORY.items()}
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} items).")
        return 0
    print("MISMATCH between clingo and python inventories:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show stock/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show stock/2."))
        print(f"{len(asp.atoms(model, 'stock'))} stock facts:")
        for item_id, count in sorted(asp.atoms(model, "stock")):
            print(f"  {item_id}: {count}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams(item=item_id, child_name="Mina", child_gender="girl", keeper="shopkeeper")
            for item_id in sorted(INVENTORY)
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
