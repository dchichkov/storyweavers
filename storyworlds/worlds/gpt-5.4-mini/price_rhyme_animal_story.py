#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/price_rhyme_animal_story.py
===========================================================

A standalone story world for a tiny animal tale with a price, a choice, and a
rhyming ending.

Premise
-------
A small animal wants a bright or tasty prize at a market or shop, but the price
is high. Another animal or a gentle grown-up helps them compare, save, or trade
wisely. The story ends with a clear change in the world state: the item is
bought, or the animal decides to wait, earn, or choose something smaller.

Style
-----
Animal Story, with light rhyme woven into the prose.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib only
- imports shared results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness gates and inline ASP twin
- produces grounded QA from world state, not by parsing rendered text
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
BUDGET_INIT = 4.0
PRICE_LIMIT = 5

ANIMAL_PRONOUNS = {"mouse", "cat", "dog", "fox", "bear", "rabbit", "owl", "bird"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "animal" | "thing" | "adult"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    scene: str
    rhyme1: str
    rhyme2: str
    afford: set[str] = field(default_factory=set)

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
class Prize:
    id: str
    label: str
    phrase: str
    wants: str
    price: int
    sparkle: str
    rhymes_with: str
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
class Choice:
    id: str
    label: str
    action: str
    result: str
    cost: int
    joy: int
    wise: bool
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_spend(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["want"] < THRESHOLD:
            continue
        if ent.meters["paid"] >= THRESHOLD:
            continue
        if ent.meters["coins"] < THRESHOLD:
            continue
        sig = ("spend", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__spent__")
    return out


CAUSAL_RULES = [Rule("spend", "money", _r_spend)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhymes(a: str, b: str) -> bool:
    return a[-2:] == b[-2:] or a[-3:] == b[-3:]


def item_eligible(prize: Prize, choice: Choice) -> bool:
    return choice.wise and choice.cost <= price_cap(prize)


def price_cap(prize: Prize) -> int:
    return PRICE_LIMIT


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for prize_id, prize in PRIZES.items():
            for choice_id, choice in CHOICES.items():
                if choice.wise and choice.cost <= prize.price:
                    combos.append((place, prize_id, choice_id))
    return combos


def reason_ok(prize: Prize, choice: Choice) -> bool:
    return choice.cost <= prize.price and choice.wise


def explain_rejection(prize: Prize, choice: Choice) -> str:
    if not choice.wise:
        return f"(No story: {choice.label} is not a wise choice for this little tale.)"
    return f"(No story: the {choice.label} costs more than the {prize.label} price.)"


def outcome_of(params: "StoryParams") -> str:
    prize = PRIZES[params.prize]
    choice = CHOICES[params.choice]
    if params.delay >= 2 and choice.cost < prize.price:
        return "wait"
    return "buy" if choice.cost <= prize.price else "wait"


def setup(world: World, child: Entity, helper: Entity, prize: Prize) -> None:
    child.memes["hope"] += 1
    helper.memes["kind"] += 1
    world.say(
        f"At {world.place.label}, a small {child.type} named {child.id} went with "
        f"{helper.id} to see a {prize.label}. {world.place.scene}"
    )
    world.say(
        f'{child.id} sighed, "I like its shine, but what is the price?"'
    )


def worry(world: World, child: Entity, helper: Entity, prize: Prize) -> None:
    child.memes["want"] += 1
    child.meters["want"] += 1
    helper.memes["care"] += 1
    world.say(
        f'The tag said "{prize.price}" and that made {child.id} slow down. '
        f'The little heart inside {child.pronoun("possessive")} chest went tap-tap.'
    )


def compare(world: World, helper: Entity, child: Entity, prize: Prize, choice: Choice) -> None:
    world.say(
        f'{helper.id} said, "Let\'s look and think. If we choose {choice.label}, '
        f'we can keep our coins and still have fun."'
    )
    if rhymes(prize.rhymes_with, choice.result[-2:]):
        world.say(
            f'The words even danced a little: {prize.label} and {choice.result} '
            f'shared a soft rhyme, neat and bright.'
        )


def buy(world: World, child: Entity, helper: Entity, prize: Prize, choice: Choice) -> None:
    child.meters["coins"] -= choice.cost
    child.meters["paid"] += 1
    child.memes["joy"] += choice.joy
    world.say(
        f"{child.id} counted out the coins and bought the {prize.label}. "
        f"It cost {choice.cost}, and the price was paid."
    )
    world.say(
        f'{child.id} grinned wide. "A little price, a happy slice!" '
        f'{helper.id} laughed, and they went home side by side.'
    )


def wait_and_choose(world: World, child: Entity, helper: Entity, prize: Prize, choice: Choice) -> None:
    child.meters["waited"] += 1
    child.memes["patience"] += 1
    world.say(
        f'{helper.id} gave a tiny nod, and {child.id} chose to wait. '
        f'The shiny thing stayed on the shelf, and the coins stayed safe.'
    )
    world.say(
        f'"No need to rush; we can hush the wish," {helper.id} said. '
        f'So {child.id} picked {choice.label} instead, light as a fish.'
    )


def ending_image(world: World, child: Entity, helper: Entity, prize: Prize, choice: Choice) -> None:
    if choice.wise and choice.cost <= prize.price and child.meters["paid"] >= THRESHOLD:
        world.say(
            f"By evening, {child.id} held the {prize.label} close, while "
            f"{helper.id} tucked the last coin away. The day had begun with a price, "
            f"and ended with a prize."
        )
    else:
        world.say(
            f"By evening, {child.id} smiled at {choice.label} and did not feel sad "
            f"about waiting. The wish was still there, but the worry was gone."
        )


def tell(place: Place, prize: Prize, choice: Choice, child_name: str, child_kind: str,
         helper_name: str, helper_kind: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="animal", type=child_kind, role="child"))
    helper = world.add(Entity(id=helper_name, kind="animal", type=helper_kind, role="helper"))
    child.meters["coins"] = float(prize.price + 1)
    child.meters["want"] = 0.0
    child.meters["paid"] = 0.0
    setup(world, child, helper, prize)
    world.para()
    worry(world, child, helper, prize)
    compare(world, helper, child, prize, choice)
    if choice.cost <= prize.price:
        buy(world, child, helper, prize, choice)
    else:
        wait_and_choose(world, child, helper, prize, choice)
    world.para()
    ending_image(world, child, helper, prize, choice)
    world.facts.update(child=child, helper=helper, prize=prize, choice=choice, place=place)
    return world


PLACES = {
    "meadow": Place("meadow", "the meadow market", "The stalls were bright with apples and bells.", "glow", "show", {"market"}),
    "barn": Place("barn", "the barn fair", "Hay bales made soft seats beside the carts.", "chime", "time", {"market"}),
    "dock": Place("dock", "the dock shop", "The water winked beside the wooden boards.", "wave", "save", {"shop"}),
}

PRIZES = {
    "apple": Prize("apple", "apple", "a shiny apple", "want to nibble", 2, "bright", "vapple", {"food"}),
    "bell": Prize("bell", "bell", "a little brass bell", "want to ring", 4, "small", "fell", {"toy"}),
    "kite": Prize("kite", "kite", "a red kite", "want to fly", 5, "high", "light", {"toy"}),
    "shell": Prize("shell", "shell", "a pearl shell", "want to hold", 3, "white", "well", {"treasure"}),
}

CHOICES = {
    "save_for_later": Choice("save_for_later", "save for later", "save", "later", 0, 1, True, {"wise"}),
    "choose_smaller": Choice("choose_smaller", "choose something smaller", "choose", "smaller", 2, 2, True, {"wise"}),
    "trade": Choice("trade", "trade a berry for it", "trade", "trade", 3, 3, True, {"wise"}),
    "spend_all": Choice("spend_all", "spend every coin", "spend", "spent", 6, 4, False, {"unwise"}),
}

CHILD_NAMES = ["Milo", "Pip", "Nell", "Tess", "Bram", "Wren", "Luna", "Otis"]
HELPER_NAMES = ["Moss", "Bibi", "Fern", "Toby", "Sage", "Nina", "June"]


@dataclass
@dataclass
class StoryParams:
    place: str
    prize: str
    choice: str
    child_name: str
    child_kind: str
    helper_name: str
    helper_kind: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story with the word "price" in it, where {f["child"].id} wants {f["prize"].label} and has to think carefully.',
        f"Tell a rhyming animal story about {f['child'].id} and {f['helper'].id} at {f['place'].label}, where the price matters and a wise choice is made.",
        f'Write a gentle story for a young child that includes price, animals, and a soft rhyme at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, prize, choice = f["child"], f["helper"], f["prize"], f["choice"]
    if choice.wise and choice.cost <= prize.price:
        ending = (
            f"{child.id} bought the {prize.label}, so the price was paid and the prize came home. "
            f"That happened because {choice.label} cost no more than the tag said."
        )
    else:
        ending = (
            f"{child.id} did not buy the {prize.label}; instead, {child.pronoun('subject')} chose to wait. "
            f"That kept the coins safe for another day."
        )
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, two animals at {f['place'].label}."),
        ("What did the child want?",
         f"{child.id} wanted {prize.phrase}, because it looked bright and lovely."),
        ("What did the helper do?",
         f"{helper.id} helped {child.id} think about the price and choose wisely. {ending}"),
        ("How did the story end?",
         f"It ended with a clear change: {ending}"),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is price?",
         "Price is how much something costs. You can look at the price tag to know what you must pay."),
        ("Why do animals in stories talk?",
         "In animal stories, animals talk so the tale can feel playful and easy for children to follow."),
        ("What is rhyme?",
         "Rhyme is when words sound alike at the end, like cat and hat. It can make a story feel bouncy and fun."),
    ]


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
        bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "apple", "choose_smaller", "Milo", "mouse", "Fern", "rabbit"),
    StoryParams("barn", "bell", "save_for_later", "Pip", "cat", "Moss", "fox"),
    StoryParams("dock", "kite", "trade", "Nell", "bird", "June", "owl"),
    StoryParams("meadow", "shell", "choose_smaller", "Tess", "dog", "Bibi", "cat"),
]


def valid_story_params(params: StoryParams) -> bool:
    return reason_ok(PRIZES[params.prize], CHOICES[params.choice])


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("price", pid, p.price))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("cost", cid, c.cost))
        if c.wise:
            lines.append(asp.fact("wise", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, C) :- prize(Pr), choice(C), price(Pr, X), cost(C, Y), wise(C), Y =< X, place(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story with price and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-kind")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-kind")
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
    if args.prize and args.choice and not reason_ok(PRIZES[args.prize], CHOICES[args.choice]):
        raise StoryError(explain_rejection(PRIZES[args.prize], CHOICES[args.choice]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prize is None or c[1] == args.prize)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize, choice = rng.choice(sorted(combos))
    child_kind = args.child_kind or rng.choice(["mouse", "cat", "dog", "rabbit", "fox", "bird"])
    helper_kind = args.helper_kind or rng.choice(["rabbit", "fox", "owl", "cat", "dog"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(place, prize, choice, child_name, child_kind, helper_name, helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PRIZES[params.prize], CHOICES[params.choice],
                 params.child_name, params.child_kind, params.helper_name, params.helper_kind)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
