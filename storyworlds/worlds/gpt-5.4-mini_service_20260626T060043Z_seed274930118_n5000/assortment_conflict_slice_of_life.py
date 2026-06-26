#!/usr/bin/env python3
"""
A small slice-of-life storyworld about an assortment, a little conflict, and a
gentle compromise.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class ItemType:
    id: str
    label: str
    phrase: str
    taste: str  # sweet | plain | savory
    category: str


@dataclass
class Assortment:
    id: str
    label: str
    contents: list[str]
    balance: dict[str, int]
    cost: int


@dataclass
class StoryParams:
    setting: str
    assortment: str
    hero_name: str
    hero_type: str
    parent_type: str
    taste_preference: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "corner_shop": Setting(place="the corner shop", afford={"browse", "buy"}),
    "kitchen_table": Setting(place="the kitchen table", afford={"sort", "share"}),
    "school_fair": Setting(place="the school fair stall", afford={"buy", "share"}),
}

ITEMS = {
    "apple": ItemType("apple", "apples", "red apples", "plain", "fruit"),
    "banana": ItemType("banana", "bananas", "yellow bananas", "plain", "fruit"),
    "cookie": ItemType("cookie", "cookies", "buttery cookies", "sweet", "snack"),
    "cracker": ItemType("cracker", "crackers", "salty crackers", "savory", "snack"),
    "berry": ItemType("berry", "berries", "tiny berries", "sweet", "fruit"),
    "cheese": ItemType("cheese", "cheese cubes", "little cheese cubes", "savory", "dairy"),
}

ASSORTMENTS = {
    "fruit_mix": Assortment(
        id="fruit_mix",
        label="a fruit assortment",
        contents=["apple", "banana", "berry"],
        balance={"plain": 2, "sweet": 1},
        cost=5,
    ),
    "snack_mix": Assortment(
        id="snack_mix",
        label="a snack assortment",
        contents=["cookie", "cracker", "cheese"],
        balance={"sweet": 1, "savory": 2},
        cost=6,
    ),
    "party_mix": Assortment(
        id="party_mix",
        label="a mixed assortment",
        contents=["apple", "cookie", "cracker", "berry"],
        balance={"plain": 2, "sweet": 2},
        cost=7,
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Leo", "Ben", "Ava", "Zoe", "Sam", "Tia"]
PARENT_TYPES = ["mother", "father"]
CHILD_TYPES = ["girl", "boy"]
TASTE_PREFS = ["sweet", "plain", "savory"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable


def _r_budget(world: World) -> list[str]:
    out = []
    basket = world.get("basket")
    if basket.meters.get("cost", 0) > world.facts.get("budget", 0):
        sig = ("budget",)
        if sig not in world.fired:
            world.fired.add(sig)
            basket.memes["stress"] = basket.memes.get("stress", 0) + 1
            out.append("The basket looked a little too full for the coins in hand.")
    return out


def _r_balance(world: World) -> list[str]:
    out = []
    basket = world.get("basket")
    if basket.meters.get("sweet", 0) >= 2 and basket.meters.get("savory", 0) >= 1:
        sig = ("balance",)
        if sig not in world.fired:
            world.fired.add(sig)
            basket.memes["harmony"] = basket.memes.get("harmony", 0) + 1
            out.append("The mix started to look like a good in-between choice.")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    if child.memes.get("want", 0) >= THRESHOLD and parent.memes.get("worry", 0) >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["conflict"] = child.memes.get("conflict", 0) + 1
            parent.memes["conflict"] = parent.memes.get("conflict", 0) + 1
            return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("budget", _r_budget),
    Rule("balance", _r_balance),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def assortment_is_reasonable(setting: Setting, assortment: Assortment) -> bool:
    return "buy" in setting.afford and len(assortment.contents) >= 3


def choose_assortment(assortment: Assortment, preference: str) -> bool:
    return any(ITEMS[item].taste == preference for item in assortment.contents)


def predict_conflict(world: World, assortment: Assortment, preference: str) -> bool:
    sim = world.copy()
    child = sim.get("child")
    parent = sim.get("parent")
    if choose_assortment(assortment, preference):
        child.memes["want"] = 1
    else:
        child.memes["want"] = 1
    parent.memes["worry"] = 1
    basket = sim.get("basket")
    basket.meters["cost"] = assortment.cost
    for item_id in assortment.contents:
        item = ITEMS[item_id]
        basket.meters[item.taste] = basket.meters.get(item.taste, 0) + 1
    propagate(sim, narrate=False)
    return child.memes.get("conflict", 0) >= THRESHOLD


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def story_intro(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    a = world.facts["assortment_obj"]
    world.say(f"{c.id} was a little {c.type} who liked watching the shelves at {world.setting.place}.")
    world.say(f"{c.pronoun().capitalize()} loved choosing an assortment, because each little thing felt like part of a bigger treat.")
    world.say(f"That afternoon, {p.pronoun('possessive')} {p.type} brought {c.id} to look at {a.label}.")


def story_turn(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    a = world.facts["assortment_obj"]
    c.memes["want"] = 1
    p.memes["worry"] = 1
    world.para()
    world.say(f"{c.id} wanted the assortment that was mostly {world.facts['favorite_taste']} things.")
    world.say(f"{p.pronoun().capitalize()} looked at the price and said the best pick should be something everyone could enjoy.")
    propagate(world, narrate=True)
    if c.memes.get("conflict", 0) >= THRESHOLD:
        world.say(f"{c.id} frowned and stared at the basket, not happy about giving up the sweetest pieces.")


def story_resolution(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    a = world.facts["assortment_obj"]
    basket = world.get("basket")
    world.para()
    world.say(f"Then {p.pronoun('possessive')} {p.type} pointed out the mixed assortment with a little bit of everything.")
    world.say(f"{c.id} nodded, because the box still had {world.facts['favorite_taste']} bites and a few calmer choices beside them.")
    c.memes["conflict"] = 0
    c.memes["joy"] = c.memes.get("joy", 0) + 1
    p.memes["relief"] = p.memes.get("relief", 0) + 1
    world.say(f"They took {a.label} home, and the basket felt balanced instead of fussy.")
    world.say(f"At the table, {c.id} smiled at the neat little assortment, and the afternoon stayed simple and warm.")


def tell(setting: Setting, assortment: Assortment, hero_name: str, hero_type: str, parent_type: str, preference: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type))
    basket = world.add(Entity(id="basket", label="the basket", type="basket"))

    world.facts["assortment_obj"] = basket
    world.facts["favorite_taste"] = preference
    world.facts["budget"] = 6 if setting.place != "the school fair stall" else 7

    story_intro(world)

    world.para()
    world.say(f"The assortment had {', '.join(ITEMS[i].label for i in assortment.contents[:-1])}, and {ITEMS[assortment.contents[-1]].label} too.")
    basket.meters["cost"] = assortment.cost
    for item_id in assortment.contents:
        item = ITEMS[item_id]
        basket.meters[item.taste] = basket.meters.get(item.taste, 0) + 1

    story_turn(world)
    story_resolution(world)

    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["assortment"] = assortment
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about an assortment that causes a small conflict in {world.setting.place}.',
        f"Tell a gentle story where {f['child'].id} wants {f['favorite_taste']} treats, but the parent wants a balanced assortment.",
        "Write a simple story about choosing a mixed basket, worrying over the price, and ending with a calm compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    p = f["parent"]
    a = f["assortment"]
    basket = f["assortment_obj"]
    return [
        QAItem(
            question=f"Why did {c.id} and {p.pronoun('possessive')} {p.type} disagree about the basket?",
            answer=f"{c.id} wanted {f['favorite_taste']} treats, but {p.pronoun('subject').capitalize()} worried about the price and wanted a more balanced assortment.",
        ),
        QAItem(
            question=f"What kind of assortment did they pick in the end?",
            answer=f"They picked {a.label}, which had a little bit of different tastes instead of only one kind.",
        ),
        QAItem(
            question=f"What changed after they talked it through?",
            answer=f"The tension settled down, {c.id} stopped sulking, and the basket felt like a thoughtful choice instead of an argument.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "assortment": (
        "What is an assortment?",
        "An assortment is a mix of different things put together, like a basket with several kinds of snacks or fruit.",
    ),
    "conflict": (
        "What is a conflict in a story?",
        "A conflict is a problem or disagreement that makes the characters pause, think, and try to find a better way.",
    ),
    "balance": (
        "Why do people like balanced choices?",
        "Balanced choices are helpful because they give a little of different things, so one person does not get too much of only one kind.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
assortment(A) :- assortment_fact(A).
contains(A,I) :- assortment_item(A,I).
sweet(I) :- item_taste(I,sweet).
plain(I) :- item_taste(I,plain).
savory(I) :- item_taste(I,savory).

has_mix(A) :- assortment(A), 3 <= #count { I : contains(A,I) }.
balanced(A) :- assortment(A), sweet_item(A), savory_item(A).
sweet_item(A) :- contains(A,I), item_taste(I,sweet).
savory_item(A) :- contains(A,I), item_taste(I,savory).

reasonable(S,A) :- setting(S), assortment(A), afford(S,buy), has_mix(A).
conflict(S,A) :- setting(S), assortment(A), reasonable(S,A), not balanced(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for act in sorted(s.afford):
            lines.append(asp.fact("afford", sid, act))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_taste", iid, item.taste))
    for aid, a in ASSORTMENTS.items():
        lines.append(asp.fact("assortment_fact", aid))
        for i in a.contents:
            lines.append(asp.fact("assortment_item", aid, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_set() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return set(asp.atoms(model, "reasonable"))


def py_reasonable_set() -> set[tuple[str, str]]:
    out = set()
    for sid, s in SETTINGS.items():
        for aid, a in ASSORTMENTS.items():
            if assortment_is_reasonable(s, a):
                out.add((sid, aid))
    return out


def asp_verify() -> int:
    a = asp_reasonable_set()
    p = py_reasonable_set()
    if a == p:
        print(f"OK: ASP and Python agree on {len(a)} reasonable pairs.")
        return 0
    print("MISMATCH")
    print("only ASP:", sorted(a - p))
    print("only Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("corner_shop", "fruit_mix", "Mia", "girl", "mother", "sweet"),
    StoryParams("kitchen_table", "snack_mix", "Leo", "boy", "father", "plain"),
    StoryParams("school_fair", "party_mix", "Ava", "girl", "mother", "sweet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about an assortment and a small conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--assortment", choices=ASSORTMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=EASY := PARENT_TYPES)
    ap.add_argument("--taste", choices=TASTE_PREFS)
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
    if args.setting and args.assortment:
        if not assortment_is_reasonable(SETTINGS[args.setting], ASSORTMENTS[args.assortment]):
            raise StoryError("That setting cannot support that assortment story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    assortment = args.assortment or rng.choice(list(ASSORTMENTS))
    if not assortment_is_reasonable(SETTINGS[setting], ASSORTMENTS[assortment]):
        raise StoryError("No reasonable story matches the given setting and assortment.")
    taste = args.taste or rng.choice(TASTE_PREFS)
    gender = args.gender or rng.choice(CHILD_TYPES)
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(setting, assortment, name, gender, parent, taste)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ASSORTMENTS[params.assortment],
        params.hero_name,
        params.hero_type,
        params.parent_type,
        params.taste_preference,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        print(sorted(set(asp.atoms(model, "reasonable"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
