#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/represent_cumbersome_grocery_store_humor_rhyming_story.py
=======================================================================================

A standalone storyworld for a tiny grocery-store rhyming-humor tale.

Premise
-------
A child wants to be "helpful" at a grocery store and tries to represent the
family by pushing an absurdly cumbersome cart. The cart gets stuck in a silly
way, a calm adult spots the problem, and the child learns a lighter, funnier,
more sensible job that still lets them help. The story keeps a playful rhyming
beat, a clear middle turn, and a cheerful ending image.

This world includes:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate and an inline ASP twin
- three QA sets grounded in world state
- a complete CLI compatible with the repo contract
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
class Cart:
    id: str
    label: str
    cumbersome: bool
    wheels: int
    packed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Task:
    id: str
    label: str
    rhyme: str
    help_kind: str
    gentle: str
    useful: str
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
        self.cart: Optional[Cart] = None
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        clone.cart = copy.deepcopy(self.cart)
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


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    cart = world.cart
    if not kid or not cart:
        return out
    if kid.meters["pushing"] < THRESHOLD or not cart.cumbersome:
        return out
    sig = ("stuck", cart.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cart.meters["stuck"] += 1
    kid.memes["frustration"] += 1
    out.append("__stuck__")
    return out


def _r_help_needed(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    adult = world.entities.get("adult")
    cart = world.cart
    if not kid or not adult or not cart:
        return out
    if cart.meters["stuck"] < THRESHOLD:
        return out
    sig = ("help", cart.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["alert"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [Rule("stuck", "physical", _r_stuck), Rule("help_needed", "social", _r_help_needed)]


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
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(task: Task, cart: Cart) -> bool:
    return task.id in {"shop", "snack", "recycle"} and cart.cumbersome


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def response_for(task: Task) -> Response:
    return RESPONSES["helpful_sort"] if task.id != "snack" else RESPONSES["sample_carry"]


def is_success(response: Response, cart: Cart, delay: int) -> bool:
    return response.power >= (2 + delay if cart.cumbersome else 1)


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def setup(world: World, child: Entity, adult: Entity, task: Task, cart: Cart) -> None:
    child.memes["joy"] += 1
    child.memes["helpful"] += 1
    world.say(
        f"At the grocery store, {child.id} came in with a grin, "
        f"to help with the carts and the aisle game spin."
    )
    world.say(
        f"{child.id} wanted to represent the family well, "
        f"so {child.pronoun()} eyed {task.label} with a wink and a bell."
    )
    world.say(
        f"There stood a cart so {('cumbersome' if cart.cumbersome else 'light')} and tall, "
        f"with a wobble-wobble frame and a squeaky-wheel call."
    )


def tempt(world: World, child: Entity, task: Task, cart: Cart) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I can do it!" said {child.id} with a bashful cheer, '
        f'"I\'ll show I can help and steer this cart right here."'
    )
    world.say(
        f"To represent the shoppers, {child.id} gave a push and a shove, "
        f"but the cart rolled one inch, then balked with a grunt above."
    )


def warn(world: World, adult: Entity, child: Entity, cart: Cart) -> None:
    adult.memes["caution"] += 1
    world.say(
        f'{adult.label_word.capitalize()} glanced over and chuckled, not mean but kind: '
        f'"That cart is cumbersome, kiddo. It jams from behind."'
    )
    world.say(
        f'"Let\'s find a smaller job," {adult.label_word.capitalize()} said with a beam, '
        f'"so your helping hands can join the store-team dream."'
    )


def act(world: World, child: Entity, cart: Cart) -> None:
    child.meters["pushing"] += 1
    cart.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} pushed once more, and the cart gave a squeak, "
        f"then leaned toward a freezer and twirled to one side cheek to cheek."
    )
    if cart.meters["stuck"] >= THRESHOLD:
        world.say(
            f"It wedged by the cereal, all fussy and bent, "
            f"as if the whole store had been built for a tent."
        )


def rescue(world: World, adult: Entity, response: Response, cart: Cart, task: Task) -> None:
    cart.meters["stuck"] = 0.0
    body = response.text
    world.say(
        f"{adult.label_word.capitalize()} came over at once and {body}."
    )
    world.say(
        f"The silly jam loosened, the aisle felt bright, "
        f"and {child_name(world)} got a new job that felt just right."
    )


def child_name(world: World) -> str:
    return world.facts["child"].id


def lesson(world: World, adult: Entity, child: Entity, task: Task) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{adult.label_word.capitalize()} smiled and said, "
        f'"Helping can be clever, but it should also be light; '
        f"choose a task that fits you, and everything feels right."
    )
    world.say(
        f"{child.id} nodded, then carried napkins from shelf to shelf, "
        f"which was small, neat, and merry, and worked pretty well."
    )


def ending(world: World, child: Entity, adult: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f"By the end, {child.id} was still a helper, and that was the fun, "
        f"with a tidy little errand and a happy rhyme done."
    )
    world.say(
        f"They left with a grin and a bag of good cheer, "
        f"while the too-cumbersome cart stood still in the rear."
    )


def tell(task: Task, cart: Cart, delay: int = 0, child_name: str = "Milo",
         child_gender: str = "boy", adult_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id="Parent", kind="character", type=adult_type, role="adult"))
    world.cart = cart
    world.add(Entity(id="cart", type="cart", label=cart.label))

    setup(world, child, adult, task, cart)
    world.para()
    tempt(world, child, task, cart)
    warn(world, adult, child, cart)

    if not is_reasonable(task, cart):
        raise StoryError("That cart/task pair does not make a sensible grocery-store story.")

    act(world, child, cart)
    response = response_for(task)
    if is_success(response, cart, delay):
        world.para()
        rescue(world, adult, response, cart, task)
        lesson(world, adult, child, task)
        world.para()
        ending(world, child, adult)
        outcome = "fixed"
    else:
        world.para()
        world.say(
            f"{adult.label_word.capitalize()} tried to help, but the jam held fast. "
            f"The cart stayed crooked until the very last."
        )
        world.say(
            f"So {child.id} carried a lighter basket instead, "
            f"and the store trip ended with humor and zest."
        )
        outcome = "stuck"
    world.facts.update(child=child, adult=adult, task=task, cart=cart, outcome=outcome,
                       response=response, delay=delay)
    return world


TASKS = {
    "shop": Task("shop", "shopping", "shop-hop", "help", "light and bright", "useful", {"store"}),
    "snack": Task("snack", "snack sorting", "snack-track", "help", "quick and slick", "useful", {"store"}),
    "recycle": Task("recycle", "recycling returns", "return-spurn", "help", "small and tidy", "useful", {"store"}),
}

CARTS = {
    "giant": Cart("giant", "giant cart", True, 4),
    "wobbly": Cart("wobbly", "wobbly cart", True, 3),
    "tiny": Cart("tiny", "tiny cart", False, 2),
}

RESPONSES = {
    "helpful_sort": Response(
        "helpful_sort", 3, 3,
        "sorted the cereal boxes into a neat little row",
        "sorted the cereal boxes, but the cart still jammed in place",
        "sorted the boxes into a neat little row",
        {"help"}),
    "sample_carry": Response(
        "sample_carry", 3, 2,
        "carried sample cups from cart to cart without any fuss",
        "carried sample cups, but the cart kept grumbling and stuck",
        "carried sample cups without any fuss",
        {"help"}),
    "quick_nudge": Response(
        "quick_nudge", 1, 1,
        "nudged the cart with a laugh",
        "nudged the cart, but it was too big to budge",
        "nudged the cart",
        {"help"}),
}

CURATED = [
    StoryParams("shop", "giant", "Ari", "boy", "mother", "patient"),
    StoryParams("snack", "wobbly", "Nia", "girl", "father", "curious"),
    StoryParams("recycle", "giant", "Eli", "boy", "mother", "cheerful"),
]


@dataclass
class StoryParams:
    task: str
    cart: str
    name: str
    gender: str
    adult: str
    trait: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for task_id, task in TASKS.items():
        for cart_id, cart in CARTS.items():
            if is_reasonable(task, cart):
                combos.append((task_id, cart_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    return [
        f"Write a short rhyming humor story set in a grocery store that uses the words 'represent' and 'cumbersome'.",
        f"Tell a funny rhyme about {f['child'].id} trying to {task.label} with a cumbersome cart, then finding a smaller helpful job.",
        f"Write a gentle grocery-store story where a child wants to represent the family and learns a better way to help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    task = f["task"]
    cart = f["cart"]
    qa = [
        ("Where does the story happen?",
         "It happens in a grocery store, where the aisles are full of carts, shelves, and busy people." ),
        (f"Why was {cart.label} hard to move?",
         f"It was cumbersome, so it felt heavy and awkward instead of quick and easy. That made it hard for {child.id} to steer it neatly." ),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to represent the family by helping well at the store. That is why {child.pronoun()} kept trying to do the job." ),
    ]
    if f["outcome"] == "fixed":
        qa.append((
            "How did the problem get solved?",
            f"{adult.label_word.capitalize()} gave {child.id} a smaller job that fit the moment better. The cart stopped being the problem, and the helper job let {child.id} still feel proud."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {child.id} helping in a lighter way and smiling through the aisle. The ending image proves the child still helped, but without wrestling the cumbersome cart."
        ))
    else:
        qa.append((
            "What happened when the cart would not move?",
            f"It stayed stuck, so {child.id} switched to carrying a lighter basket instead. The joke is that the big cart acted grand, but the small job won."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a grocery store?",
         "A grocery store is a place where people buy food and household things from shelves and carts."),
        ("What does cumbersome mean?",
         "Cumbersome means big, awkward, or hard to move smoothly."),
        ("What does represent mean?",
         "Represent means to stand for someone or show them in a good way."),
        ("Why is humor fun in a story?",
         "Humor makes a story playful and smiley, so the reader can laugh while still learning something."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.cart is not None:
        lines.append(f"  cart     ({world.cart.label}) meters={dict(world.cart.meters)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(C) :- cumbersome(C), pushing_child.
help_needed(C) :- stuck(C).
valid_story(T, C) :- task(T), cart(C), cumbersome(C).
outcome(fixed) :- helper_job.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for cid, c in CARTS.items():
        lines.append(asp.fact("cart", cid))
        if c.cumbersome:
            lines.append(asp.fact("cumbersome", cid))
        lines.append(asp.fact("wheels", cid, c.wheels))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    # smoke test: at least one normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Grocery-store rhyming humor storyworld.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--cart", choices=CARTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.task and args.cart and not is_reasonable(TASKS[args.task], CARTS[args.cart]):
        raise StoryError("That cart is too small or too ordinary for the chosen task.")
    combos = [c for c in valid_combos()
              if (args.task is None or c[0] == args.task)
              and (args.cart is None or c[1] == args.cart)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    task, cart = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Milo", "Ava", "Nora", "Finn", "Lena", "Owen"])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(task, cart, name, gender, adult, rng.choice(["funny", "cheery", "patient"]), args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(TASKS[params.task], CARTS[params.cart], params.delay, params.name, params.gender, params.adult)
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
        print(asp_program(show="#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("shop", "giant", "Milo", "boy", "mother", "patient", 0),
    StoryParams("snack", "wobbly", "Ava", "girl", "father", "cheery", 0),
]


def _pick_task_task() -> None:
    pass
if __name__ == "__main__":
    main()
