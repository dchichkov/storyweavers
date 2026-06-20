#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crummy_poultry_twist_rhyme_pirate_tale.py
===========================================================================

A standalone storyworld for a tiny pirate-tale domain featuring Twist and Rhyme,
a crummy poultry basket, and a safe turn toward a sturdier carry crate.

The story is built from simulated state:
- characters have physical meters and emotional memes
- a crummy basket can jostle poultry and crack eggs
- one child rushes ahead, the other warns
- a grown-up fixes the problem with a sturdier crate
- the ending proves what changed

This world is designed to be child-facing, compact, and constraint-checked.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Basket:
    id: str
    label: str
    phrase: str
    crummy: bool = False
    sturdy: bool = False
    holds: int = 0
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Poultry:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    rush: str
    fix: str
    success: str
    fail: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    twist_name: str
    rhyme_name: str
    basket: str
    poultry: str
    action: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


TWIST_NAMES = ["Twist", "Milo", "Pip", "Nell", "Bea"]
RHYME_NAMES = ["Rhyme", "Lina", "Joss", "Tess", "Bo"]
BASKETS = {
    "crummy_basket": Basket("crummy_basket", "basket", "a crummy basket", crummy=True, tags={"crummy"}),
    "sturdy_crate": Basket("sturdy_crate", "crate", "a sturdy crate", sturdy=True, tags={"sturdy"}),
}
POULTRY = {
    "hen": Poultry("hen", "hen", "a sleepy hen", tags={"poultry", "hen"}),
    "chicks": Poultry("chicks", "chicks", "three fluffy chicks", plural=True, tags={"poultry", "chicks"}),
}
ACTIONS = {
    "carry": Action("carry", "carry", "ran ahead with the basket", "swapped the crummy basket for a crate",
                    "carried the poultry safely to the ship", "dropped the poultry and had to chase feathers",
                    3, 3, tags={"carry"}),
    "feed": Action("feed", "feed", "hopped in with the feed", "set out a neat little dish",
                   "fed the poultry without a mess", "spilled the feed all over the deck",
                   2, 2, tags={"feed"}),
}
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for bid, basket in BASKETS.items():
        for pid in POULTRY:
            for aid in ACTIONS:
                combos.append((bid, pid, aid))
    return combos


def reason_ok(basket: Basket, poultry: Poultry, action: Action) -> bool:
    return basket.crummy or basket.sturdy


ASP_RULES = r"""
valid(B, P, A) :- basket(B), poultry(P), action(A).
safe(B) :- sturdy(B).
crummy(B) :- basket(B), not sturdy(B).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for bid, b in BASKETS.items():
        lines.append(asp.fact("basket", bid))
        if b.crummy:
            lines.append(asp.fact("crummy", bid))
        if b.sturdy:
            lines.append(asp.fact("sturdy", bid))
    for pid in POULTRY:
        lines.append(asp.fact("poultry", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: valid_combos() matches ASP ({len(p)} combos).")
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: smoke test story generated.")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(p - c))
    print("only asp:", sorted(c - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with Twist, Rhyme, crummy poultry, and a safer turn.")
    ap.add_argument("--twist-name", choices=TWIST_NAMES)
    ap.add_argument("--rhyme-name", choices=RHYME_NAMES)
    ap.add_argument("--basket", choices=BASKETS)
    ap.add_argument("--poultry", choices=POULTRY)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.basket and args.action and BASKETS[args.basket].crummy and args.action == "carry":
        pass
    combo = rng.choice(valid_combos())
    basket, poultry, action = combo
    return StoryParams(
        twist_name=args.twist_name or rng.choice(TWIST_NAMES),
        rhyme_name=args.rhyme_name or rng.choice([n for n in RHYME_NAMES if n != (args.twist_name or "")]),
        basket=args.basket or basket,
        poultry=args.poultry or poultry,
        action=args.action or action,
        parent=args.parent or rng.choice(PARENTS),
    )


def _do_action(world: World, action: Action, basket: Entity, poultry: Entity, narrate: bool = True) -> None:
    if action.id == "carry" and basket.meters["bumped"] >= THRESHOLD:
        basket.meters["jostled"] += 1
    if action.id == "feed":
        basket.meters["spilled"] += 1
    if narrate:
        world.say("")


def story_setup(world: World, twist: Entity, rhyme: Entity) -> None:
    twist.memes["bravery"] += 1
    rhyme.memes["care"] += 1
    world.say(f"On a windy pirate day, {twist.id} and {rhyme.id} found a little job by the dock.")
    world.say("A crummy poultry basket sat beside a flap of rope, and a sleepy bird waited in the shade.")


def tempt(world: World, twist: Entity, basket: Basket, action: Action) -> None:
    world.say(f'"I can do it fast," said {twist.id}, and {action.rush}.')


def warn(world: World, rhyme: Entity, basket: Basket, action: Action, poultry: Poultry) -> None:
    rhyme.memes["warning"] += 1
    world.say(f'"Wait," said {rhyme.id}. "That {basket.label} looks crummy. The {poultry.label} will get jostled."')


def twist_event(world: World, twist: Entity, basket: Basket, action: Action, poultry: Poultry) -> None:
    twist.memes["defiance"] += 1
    world.say(f"{twist.id} tried anyway, and the {basket.label} bounced on the boards.")
    world.say(f"The little deck gave a twist, and the bird squawked in surprise.")


def mishap(world: World, basket: Basket, poultry: Poultry) -> None:
    basket.holds = 0
    basket.crummy = True
    world.get("ship").meters["mess"] += 1
    world.say(f"The crummy {basket.label} tipped, and feathers and feed puffed across the deck.")


def fix(world: World, parent: Entity, action: Action, basket: Basket, poultry: Poultry) -> None:
    parent.memes["help"] += 1
    world.say(f"Then {parent.label_word} came running with a sturdy crate.")
    world.say(f'"No worry," {parent.label_word} said. "{action.fix}."')
    basket.sturdy = True


def ending(world: World, twist: Entity, rhyme: Entity, action: Action, poultry: Poultry, basket: Basket) -> None:
    twist.memes["relief"] += 1
    rhyme.memes["relief"] += 1
    if action.id == "carry":
        world.say(f"At last, {twist.id} and {rhyme.id} {action.success}, and the bird stayed calm.")
    else:
        world.say(f"At last, {twist.id} and {rhyme.id} fed the poultry without another spill.")
    world.say("The ship looked neat again, and the gulls circled over the calm blue sea.")


def tell(params: StoryParams) -> World:
    world = World()
    twist = world.add(Entity(params.twist_name, kind="character", type="boy", role="instigator"))
    rhyme = world.add(Entity(params.rhyme_name, kind="character", type="girl", role="cautioner"))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    ship = world.add(Entity("ship", type="place", label="the ship"))
    basket = BASKETS[params.basket]
    poultry = POULTRY[params.poultry]
    action = ACTIONS[params.action]

    world.facts.update(twist=twist, rhyme=rhyme, parent=parent, basket=basket, poultry=poultry, action=action)

    story_setup(world, twist, rhyme)
    world.para()
    tempt(world, twist, basket, action)
    warn(world, rhyme, basket, action, poultry)
    twist_event(world, twist, basket, action, poultry)
    mishap(world, basket, poultry)
    world.para()
    fix(world, parent, action, basket, poultry)
    ending(world, twist, rhyme, action, poultry, basket)

    world.facts["outcome"] = "fixed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate tale for a young child that includes the words "crummy" and "poultry".',
        f"Tell a short pirate story where {f['twist'].id} rushes ahead, {f['rhyme'].id} warns about a crummy basket, and a grown-up helps.",
        f"Write a rhyming, twisty pirate story about {f['poultry'].phrase} on a ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="Who are the two children in the story?",
               answer=f"They are {f['twist'].id} and {f['rhyme'].id}, two little pirate kids by the dock."),
        QAItem(question="What was wrong with the basket?",
               answer="It was crummy, so it bounced and tipped when the child rushed ahead. That is why the poultry got jostled and feathers spilled."),
        QAItem(question="How did the problem get fixed?",
               answer="The parent brought a sturdy crate and helped them move the poultry safely. After that, the deck was calm again and the bird stayed safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is poultry?",
               answer="Poultry means birds that people keep for eggs or food, like hens and chicks."),
        QAItem(question="What does crummy mean?",
               answer="Crummy means poor, weak, or not very good. A crummy basket can fall apart or tip over."),
        QAItem(question="What is sturdy?",
               answer="Sturdy means strong and hard to break. A sturdy crate can hold things more safely."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("Twist", "Rhyme", "crummy_basket", "hen", "carry", "mother"),
    StoryParams("Twist", "Rhyme", "crummy_basket", "chicks", "feed", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
