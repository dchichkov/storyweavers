#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reversible_rapids_kindness_humor_slice_of_life.py
=================================================================================

A small slice-of-life story world about a child, a reversible jacket, and a day
by the rapids that turns from awkward to kind and funny.

This world models one gentle everyday problem:
- a child wants to keep playing near the river
- a light reversible jacket can be worn the wrong way or the right way
- a small kindness helps someone else feel included
- a little humor comes from a playful mismatch and a silly fix

The seed words "reversible" and "rapids" are built into the world model and the
story text. The stories are short, child-facing, concrete, and state-driven.
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
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    label: str
    near: str
    sound: str
    water: bool = False

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
class Item:
    id: str
    label: str
    phrase: str
    reversible: bool = False
    warm_side: str = ""
    bright_side: str = ""
    helps: set[str] = field(default_factory=set)
    plural: bool = False

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
class Action:
    id: str
    verb: str
    consequence: str
    joke: str
    kindness: str
    risk: int
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    river = world.facts.get("place")
    for e in world.characters():
        if e.meters["wet"] < THRESHOLD:
            continue
        sig = ("splash", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if river and river.water:
            e.memes["surprised"] += 1
            out.append("__splash__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("splash", "physical", _r_splash), Rule("kindness", "social", _r_kindness)]


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


def risky(action: Action, item: Item) -> bool:
    return action.risk >= 1 and item.reversible


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.risk >= SENSE_MIN]


def selected_action() -> Action:
    return max(ACTIONS.values(), key=lambda a: a.risk)


def predict(world: World, action_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get("hero"), ACTIONS[action_id], narrate=False)
    item = sim.get("item")
    return {"wet": item.meters["wet"] >= THRESHOLD, "joy": sim.get("hero").memes["joy"]}


def _do_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    hero.meters["wet"] += 1
    hero.memes["humor"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, friend: Entity, place: Place, item: Item) -> None:
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} went to {place.label}. "
        f"The {place.sound} of the {place.near} made the day feel lively."
    )
    world.say(
        f"{hero.id} wore a {item.phrase} and kept turning it because it was "
        f"{item.reversible}."
    )


def setup(world: World, hero: Entity, friend: Entity, place: Place, item: Item) -> None:
    hero.memes["curious"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"They watched the {place.near} from the path and laughed when the wind "
        f"puffed {item.label} inside out like a tiny cape."
    )
    world.say(f'"This jacket has a reversible side," {hero.id} said, grinning.')


def need_help(world: World, hero: Entity, friend: Entity, place: Place, item: Item) -> None:
    world.say(
        f"But near the rapids, a small gust made the {item.label} flap the wrong "
        f"way again. {friend.id} laughed so hard {friend.pronoun()} had to lean on "
        f"a rail."
    )
    world.say(
        f'Then {friend.id} noticed a little child holding a dropped snack near the '
        f'{place.near}. "Let me help," {friend.id} said.'
    )


def warn(world: World, hero: Entity, action: Action) -> None:
    pred = predict(world, action.id)
    world.facts["predicted_wet"] = pred["wet"]
    world.say(
        f'"If you splash too close to the rapids, your {action.consequence}," '
        f"{hero.id} said, sounding half serious and half silly."
    )


def act(world: World, hero: Entity, action: Action) -> None:
    hero.memes["bold"] += 1
    world.say(
        f"{hero.id} tried to {action.verb}, but the water at the rapids had other "
        f"ideas."
    )
    _do_action(world, hero, action)


def kindness_turn(world: World, friend: Entity, hero: Entity, action: Action) -> None:
    friend.memes["kindness"] += 1
    world.say(
        f"{friend.id} bent down, picked up the snack, and handed it back with a "
        f"smile. {action.kindness}"
    )
    world.say(
        f"{hero.id} laughed too, because the whole thing looked like a parade of "
        f"wind and wobbling crumbs."
    )


def resolve(world: World, hero: Entity, friend: Entity, item: Item) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, {hero.id} flipped the {item.label} to the warmer side and "
        f"stood beside {friend.id} while they watched the rapids sparkle."
    )
    world.say(
        f"The day ended with dry shoes, a kinder mood, and one reversible jacket "
        f"that had somehow become the funniest thing by the river."
    )


def tell(place: Place, item: Item, action: Action, hero_name: str = "Mina",
         hero_gender: str = "girl", friend_name: str = "Owen",
         friend_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id="item", type="thing", label=item.label))
    world.facts["place"] = place
    world.facts["item_cfg"] = item
    world.facts["action"] = action

    intro(world, hero, friend, place, item)
    setup(world, hero, friend, place, item)
    world.para()
    need_help(world, hero, friend, place, item)
    warn(world, hero, action)
    world.para()
    act(world, hero, action)
    kindness_turn(world, friend, hero, action)
    world.para()
    resolve(world, hero, friend, item)
    world.facts.update(hero=hero, friend=friend, outcome="kind")
    return world


PLACES = {
    "riverwalk": Place("riverwalk", "the riverwalk", "rapids", "water rushed", water=True),
    "picnic_spot": Place("picnic_spot", "the picnic spot", "rapids", "water shimmered", water=True),
    "park_bench": Place("park_bench", "the park bench by the river", "rapids", "water roared", water=True),
}

ITEMS = {
    "jacket": Item("jacket", "reversible jacket", "a reversible jacket", reversible=True,
                   warm_side="blue side", bright_side="yellow side", helps={"warmth"}),
    "cape": Item("cape", "reversible cape", "a reversible cape", reversible=True,
                 warm_side="red side", bright_side="green side", helps={"warmth"}),
    "tote": Item("tote", "reversible tote bag", "a reversible tote bag", reversible=True,
                 warm_side="plain side", bright_side="striped side", helps={"carry"}),
}

ACTIONS = {
    "skip_stones": Action("skip_stones", "skip stones near the rapids", "jacket might get wet",
                          "the stones bounced like tiny frogs", "helped the little child",
                          2, tags={"rapids", "kindness"}),
    "wave": Action("wave", "wave at the rapids", "hair might get damp",
                   "the wave looked like a giant fish", "showed the child where to stand",
                   2, tags={"rapids", "humor"}),
    "picnic": Action("picnic", "share cookies by the rapids", "snacks might scatter",
                     "one cookie tried to roll away", "shared a napkin with the child",
                     2, tags={"rapids", "kindness", "humor"}),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    action: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
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
    return [(p, a, i) for p in PLACES for a in ACTIONS for i in ITEMS if risky(ACTIONS[a], ITEMS[i])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with reversible things and rapids.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.item and args.action and not risky(ACTIONS[args.action], ITEMS[args.item]):
        raise StoryError("That item-action pair does not create a believable little problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, item = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(["Mina", "Lila", "Nora", "Tess", "June"])
    friend_name = args.friend or rng.choice(["Owen", "Theo", "Parker", "Ben", "Eli"])
    return StoryParams(place, item, action, hero_name, hero_gender, friend_name, friend_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "reversible" and "rapids".',
        f"Tell a gentle story about {f['hero'].id} and {f['friend'].id} by the rapids, "
        f"where a reversible {f['item_cfg'].label} becomes part of a funny kind moment.",
        f"Write a child-facing story that feels like an ordinary afternoon, with a small joke, a small kindness, and the word rapids.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, item, action = f["hero"], f["friend"], f["item_cfg"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two children spending an ordinary day by the rapids."),
        ("What made the jacket funny?",
         f"The jacket was reversible, so it could be worn on two sides. That made it funny when the wind flipped it the wrong way like a tiny cape."),
        ("How did the story end?",
         f"It ended with kindness and laughter by the rapids. {friend.id} helped another child, and {hero.id} wore the jacket the warmer way while everyone settled down."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does reversible mean?",
         "Reversible means something can be turned around or worn on either side."),
        ("What are rapids?",
         "Rapids are a part of a river where the water moves fast and makes a lively rushing sound."),
        ("Why is kindness important?",
         "Kindness helps people feel noticed and cared for, especially when they are having a small problem or a busy day."),
        ("Why can humor help?",
         "Humor can make a small mistake feel less upsetting because it helps people laugh and keep going."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("riverwalk", "jacket", "skip_stones", "Mina", "girl", "Owen", "boy"),
    StoryParams("picnic_spot", "cape", "picnic", "Lila", "girl", "Theo", "boy"),
    StoryParams("park_bench", "tote", "wave", "Nora", "girl", "Ben", "boy"),
]


def explain_rejection(item: Item, action: Action) -> str:
    return f"(No story: a {item.label} does not fit a believable little moment around {action.verb}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i, item in ITEMS.items():
        lines.append(asp.fact("item", i))
        if item.reversible:
            lines.append(asp.fact("reversible", i))
    for a, act in ACTIONS.items():
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("risk", a, act.risk))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,I) :- place(P), action(A), item(I), reversible(I), risk(A,R), R >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, action=None, name=None, friend=None, gender=None, friend_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print("MISMATCH: generate() smoke test failed:", exc)
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], ACTIONS[params.action],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
