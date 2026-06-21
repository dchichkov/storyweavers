#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distribute_even_suspense_kindness_heartwarming.py
===================================================================================

A small, heartwarming storyworld about a child, a surprise shortage, and a kind
choice that keeps everyone calm.  The seed words are "distribute" and "even";
the world turns them into a tiny suspenseful problem: one child must distribute
a small number of warm treats or candles evenly among neighbors, notice that one
guest is left out, and then solve it with kindness.

The story stays concrete and state-driven:
- physical meters track counts, shares, and warmth
- emotional memes track worry, trust, relief, and kindness
- suspense comes from uncertainty about whether everyone will get one
- heartwarming resolution comes from making an even, kind distribution

This script follows the shared StorySample / QAItem / StoryError contract and
supports prose, QA, JSON, ASP, and verification modes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    night: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    count: int
    warm: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class DistributionRule:
    id: str
    kind: str
    even_required: bool
    motive: str
    suspense_line: str
    kindness_line: str
    fix_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for name, ent in world.entities.items():
        if ent.meters.get("missing_share", 0) < THRESHOLD:
            continue
        sig = ("worry", name)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] = ent.memes.get("worry", 0) + 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved") and not world.facts.get("relief_spoken"):
        helper = world.get("helper")
        helper.memes["relief"] = helper.memes.get("relief", 0) + 1
        out.append("__relief__")
        world.facts["relief_spoken"] = True
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_even(world: World, count: int, guests: int) -> dict:
    sim = world.copy()
    sim.facts["guests"] = guests
    sim.facts["count"] = count
    sim.facts["remaining"] = max(0, count - guests)
    sim.get("basket").meters["missing_share"] = 1 if count < guests else 0
    propagate(sim, narrate=False)
    return {
        "even": count >= guests and count % guests == 0,
        "short": count < guests,
        "leftover": count % guests if guests else 0,
    }


def distribute(world: World, child: Entity, item: Item, guests: int) -> None:
    world.say(
        f"At the little table, {child.id} had to distribute the {item.label} to "
        f"{guests} waiting neighbors."
    )
    world.say(
        f"{child.id} counted again and again. The room felt very quiet, because "
        f"everybody wanted the answer to be even."
    )


def suspense(world: World, child: Entity, item: Item, guests: int) -> None:
    pred = predict_even(world, item.count, guests)
    child.memes["care"] = child.memes.get("care", 0) + 1
    if pred["short"]:
        world.say(
            f"{child.id} frowned. There were only {item.count} treats, but {guests} "
            f"faces were turned toward {child.pronoun('object')}."
        )
    elif pred["leftover"]:
        world.say(
            f"{child.id} paused. The treats were not even yet, and one small pile "
            f"would be left over."
        )
    else:
        world.say(
            f"{child.id} held the tray very still. The count looked even, but nobody "
            f"knew if the last piece would still be needed."
        )
    world.facts["predicted"] = pred
    world.facts["missing"] = pred["short"]


def kindness(world: World, child: Entity, helper: Entity, item: Item, guests: int) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    world.say(
        f"Then {helper.id} smiled and said, \"We can make this kind.\" "
        f"{helper.id} helped {child.id} think about every person, even the shy one at the end."
    )
    if item.count < guests:
        world.say(
            f"{helper.id} suggested sharing the warm drink first and then making a little more, "
            f"so nobody would go without."
        )
    else:
        world.say(
            f"{helper.id} suggested using the treats one by one so each neighbor would get the same."
        )


def fix_even(world: World, child: Entity, helper: Entity, item: Item, guests: int) -> None:
    item.count = max(item.count, guests)
    if item.count % guests != 0:
        item.count += guests - (item.count % guests)
    child.meters["missing_share"] = 0
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.facts["resolved"] = True
    world.say(
        f"{child.id} nodded and made the pile even. Soon there were exactly {item.count} "
        f"{item.label}, enough to hand one to each guest."
    )
    world.say(
        f"No one had to wait with empty hands. The room grew warm and soft, and the little "
        f"job turned into a happy one."
    )


def ending(world: World, child: Entity, helper: Entity, item: Item, guests: int) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"In the end, {child.id} smiled at the last neighbor and passed out the final {item.label}."
    )
    world.say(
        f"Because {helper.id} had been kind, the whole table felt calm, and everything was "
        f"distributed evenly at last."
    )


THEMES = {
    "winter": Setting(id="winter", place="the warm kitchen", mood="snowy evening", night=True),
    "rainy": Setting(id="rainy", place="the front porch", mood="rainy dusk", night=True),
    "sunny": Setting(id="sunny", place="the picnic blanket", mood="bright afternoon", night=False),
}

ITEMS = {
    "cookies": Item(id="cookies", label="cookies", phrase="a plate of cookies", kind="treat", count=5, warm=True),
    "candles": Item(id="candles", label="candles", phrase="a tray of candles", kind="light", count=4, warm=True),
    "apples": Item(id="apples", label="apples", phrase="a basket of apples", kind="fruit", count=6, warm=False),
}

RULES = {
    "share": DistributionRule(
        id="share",
        kind="treat",
        even_required=True,
        motive="everyone should get one",
        suspense_line="counting the treats made the room go still",
        kindness_line="a gentle helper made the choice feel safe",
        fix_line="one more was added so the pile could be even",
        tags={"even", "distribute", "kindness", "heartwarming", "suspense"},
    ),
    "lanterns": DistributionRule(
        id="lanterns",
        kind="light",
        even_required=True,
        motive="everyone needed a lamp for the dark walk home",
        suspense_line="the last lantern mattered most",
        kindness_line="sharing the glow made the lane feel friendly",
        fix_line="the lamps were lined up evenly so nobody walked in the dark",
        tags={"even", "distribute", "kindness", "heartwarming", "suspense"},
    ),
}

CHILDREN = ["Mina", "Noah", "Ivy", "Leo", "Mila", "Ben"]
HELPERS = ["Mom", "Dad", "Grandma", "Grandpa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for item in ITEMS:
            for rule in RULES:
                if ITEMS[item].kind == RULES[rule].kind:
                    combos.append((theme, item, rule))
    return combos


@dataclass
class StoryParams:
    theme: str
    item: str
    rule: str
    child: str = "Mina"
    helper: str = "Mom"
    guests: int = 4
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming distribute-even storyworld with suspense and kindness.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--rule", choices=RULES)
    ap.add_argument("--child")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--guests", type=int)
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
              if (args.theme is None or c[0] == args.theme)
              and (args.item is None or c[1] == args.item)
              and (args.rule is None or c[2] == args.rule)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, item, rule = rng.choice(sorted(combos))
    guests = args.guests if args.guests is not None else rng.randint(3, 6)
    if guests < 1:
        raise StoryError("Guests must be at least 1.")
    return StoryParams(
        theme=theme,
        item=item,
        rule=rule,
        child=args.child or rng.choice(CHILDREN),
        helper=args.helper or rng.choice(HELPERS),
        guests=guests,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = THEMES[params.theme]
    item = ITEMS[params.item]
    rule = RULES[params.rule]
    child = world.add(Entity(id=params.child, kind="character", type="girl" if params.child in {"Mina", "Ivy", "Mila"} else "boy", role="distributor"))
    helper = world.add(Entity(id=params.helper, kind="character", type="mother" if params.helper in {"Mom", "Grandma"} else "father", role="helper"))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label=item.label, attrs={"count": item.count}))
    world.facts.update(setting=setting, item=item, rule=rule, child=child, helper=helper, basket=basket, guests=params.guests)
    child.meters["missing_share"] = 0
    helper.memes["kindness"] = 0
    world.say(
        f"That evening at {setting.place}, the air felt like {setting.mood}. "
        f"{params.child} wanted to {rule.id} the {item.label} for {params.guests} guests."
    )
    distribute(world, child, item, params.guests)
    world.para()
    suspense(world, child, item, params.guests)
    world.say(f"The little worry made the table go quiet, but nobody rushed {params.child}.")
    world.para()
    kindness(world, child, helper, item, params.guests)
    fix_even(world, child, helper, item, params.guests)
    world.para()
    ending(world, child, helper, item, params.guests)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story with suspense where {f["child"].id} must distribute {f["item"].label} evenly to everyone.',
        f'Tell a gentle story using the words "distribute" and "even" about a kind helper who makes sure nobody is left out.',
        f'Write a cozy story where a child counts carefully, feels suspense, and then chooses kindness to make things even.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    item: Item = f["item"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    guests = f["guests"]
    qa = [
        QAItem(
            question="Why was the child worried?",
            answer=f"{child.id} was worried because there were {item.count} {item.label} for {guests} guests, and the pile did not yet feel even. That made the room quiet and suspenseful until a kinder plan was found."
        ),
        QAItem(
            question="How did the helper show kindness?",
            answer=f"{helper.id} showed kindness by helping {child.id} think about every guest and by suggesting a fair way to share. That turned the problem into something warm instead of scary."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with everyone getting a share and the treats distributed evenly. The child smiled because nobody was left out."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to distribute something?",
            answer="To distribute something means to hand it out among a group so the people each get some of it."
        ),
        QAItem(
            question="What does even mean when sharing?",
            answer="Even means the shares are the same size, or as close to the same as possible, so nobody gets much more or much less."
        ),
        QAItem(
            question="Why is kindness important when someone is waiting?",
            answer="Kindness helps people feel safe and cared for. It makes it easier to solve small problems without hurting anyone's feelings."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="winter", item="cookies", rule="share", child="Mina", helper="Mom", guests=4),
    StoryParams(theme="rainy", item="candles", rule="lanterns", child="Noah", helper="Dad", guests=4),
    StoryParams(theme="sunny", item="apples", rule="share", child="Ivy", helper="Grandma", guests=6),
]


def explain_rejection(item: Item, guests: int) -> str:
    return f"(No story: the count of {item.label} cannot be distributed evenly among {guests} guests in this setup.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in THEMES:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("kind", iid, item.kind))
        lines.append(asp.fact("count", iid, item.count))
    for rid, rule in RULES.items():
        lines.append(asp.fact("rule", rid))
        lines.append(asp.fact("rule_kind", rid, rule.kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,I,R) :- setting(S), item(I), rule(R), kind(I,K), rule_kind(R,K).
even_possible(I,G) :- count(I,C), G > 0, C >= G.
even_share(I,G) :- count(I,C), G > 0, C >= G, 0 == C mod G.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, item=None, rule=None, child=None, helper=None, guests=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.item not in ITEMS or params.rule not in RULES:
        raise StoryError("Invalid parameters.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, i, r in asp_valid_combos():
            print(f"  {s:8} {i:8} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
