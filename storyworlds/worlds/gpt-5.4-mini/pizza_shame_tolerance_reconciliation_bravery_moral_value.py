#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pizza_shame_tolerance_reconciliation_bravery_moral_value.py
==========================================================================================

A standalone story world for a small rhyming tale about pizza, shame, tolerance,
bravery, moral value, and reconciliation.

A child brings a pizza to a shared table, another child feels ashamed about a
mistake, and a brave, tolerant response turns embarrassment into a repaired
friendship. The world model uses typed entities with physical meters and
emotional memes so the story grows from state changes instead of fixed prose.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/pizza_shame_tolerance_reconciliation_bravery_moral_value.py
    python storyworlds/worlds/gpt-5.4-mini/pizza_shame_tolerance_reconciliation_bravery_moral_value.py --all
    python storyworlds/worlds/gpt-5.4-mini/pizza_shame_tolerance_reconciliation_bravery_moral_value.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/pizza_shame_tolerance_reconciliation_bravery_moral_value.py --verify
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
BRAVERY_BASE = 5.0
SHAME_ALERT = 1.0


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
class Table:
    id: str
    place: str
    phrase: str
    cozy: str

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
class Pizza:
    id: str
    label: str
    phrase: str
    smell: str
    sharing: str
    moral_value: str
    toppings: list[str] = field(default_factory=list)

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
    text: str
    qa_text: str

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
    for e in list(world.entities.values()):
        if e.memes["shame"] < THRESHOLD:
            continue
        sig = ("reconcile", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.facts.get("helper")
        if helper:
            helper.memes["tolerance"] += 1
            helper.memes["bravery"] += 1
        e.memes["shame"] = 0.0
        e.memes["relief"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("reconcile", "social", _r_reconcile)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in TABLES:
        for pid in PIZZAS:
            for rid in RESPONSES:
                combos.append((tid, pid, rid))
    return combos


def tiny_rhyme(a: str, b: str, c: str, d: str) -> str:
    return f"{a} {b}. {c} {d}."


def tell(table: Table, pizza: Pizza, response: Response,
         baker_name: str = "Mia", baker_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy") -> World:
    world = World()
    baker = world.add(Entity(id=baker_name, kind="character", type=baker_gender, role="teller"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    pie = world.add(Entity(id="pizza", type="food", label=pizza.label))
    helper.memes["tolerance"] = 2.0
    helper.memes["bravery"] = BRAVERY_BASE
    baker.memes["shame"] = 0.0
    world.facts["helper"] = helper

    world.say(
        f"In a sunny room by the little round table, {baker.id} brought {pizza.phrase}, "
        f"and the warm smell of cheese made the whole day feel bold."
    )
    world.say(
        f"{helper.id} smiled to see the feast, but when a small spill and a wobble went wrong, "
        f"{baker.id} felt a hot, red blush of shame."
    )

    world.para()
    baker.memes["shame"] += 1
    baker.meters["spilled"] += 1
    helper.memes["tolerance"] += 1
    helper.memes["concern"] += 1
    world.say(
        f"{baker.id} looked down and wished to hide; the sauce had slipped, and the crust had bent."
    )
    world.say(
        f'But {helper.id} spoke soft and true: "It is all right. We all make mistakes."'
    )

    world.para()
    if response.sense < 2:
        raise StoryError("The chosen response is too weak-minded for a reconciliation story.")
    helper.memes["bravery"] += 1
    world.say(
        f"{helper.id} stayed brave and kind, and {response.text}."
    )
    baker.memes["bravery"] += 1
    propagate(world, narrate=False)

    world.para()
    pie.meters["shared"] += 1
    baker.memes["shame"] = 0.0
    baker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Together they wiped the table clean and cut the pizza into two fair parts."
    )
    world.say(
        f"{baker.id} said sorry, {helper.id} said yes, and their hearts grew light."
    )
    world.say(
        f"That little act had moral value: kindness can mend what clumsy hands can bruise."
    )
    world.say(
        f"They ate side by side, and the room rang with a soft rhyme of cheer: "
        f"{tiny_rhyme('A slice for you', 'a slice for me', 'we share', 'we agree')}"
    )

    world.facts.update(
        baker=baker,
        helper=helper,
        pizza_cfg=pizza,
        table=table,
        response=response,
        reconciled=True,
    )
    return world


TABLES = {
    "kitchen": Table("kitchen", "the kitchen", "a little round table", "cozy"),
    "picnic": Table("picnic", "the picnic blanket", "a checkered blanket", "bright"),
}

PIZZAS = {
    "cheese": Pizza("cheese", "cheese pizza", "a cheesy pizza", "a warm smell of cheese", "share it kindly", "sharing", ["cheese"]),
    "pepper": Pizza("pepper", "pepper pizza", "a pepper pizza", "a peppery smell", "share it fairly", "sharing", ["pepper"]),
    "rainbow": Pizza("rainbow", "rainbow pizza", "a rainbow pizza", "a happy smell of herbs", "share it gently", "sharing", ["pepper", "corn"]),
}

RESPONSES = {
    "hug": Response("hug", 3, "gave a brave little hug and said the mistake could be fixed", "gave a brave little hug"),
    "sweep": Response("sweep", 3, "swept the crumbs away and said they could try again", "swept the crumbs away"),
    "calm_talk": Response("calm_talk", 2, "calmly said that everyone deserves a fair chance to try again", "calmly spoke kind words"),
}

GIRL_NAMES = ["Mia", "Ava", "Lily", "Nora", "Zoe"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Eli", "Theo"]


@dataclass
@dataclass
class StoryParams:
    table: str
    pizza: str
    response: str
    baker: str
    baker_gender: str
    helper: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about pizza, shame, tolerance, and repair.")
    ap.add_argument("--table", choices=TABLES)
    ap.add_argument("--pizza", choices=PIZZAS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--baker")
    ap.add_argument("--baker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is not brave or tolerant enough for this story.")
    table = args.table or rng.choice(sorted(TABLES))
    pizza = args.pizza or rng.choice(sorted(PIZZAS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    baker_gender = args.baker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if baker_gender == "girl" else "girl")
    baker = args.baker or rng.choice(GIRL_NAMES if baker_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != baker]
    helper = args.helper or rng.choice(helper_pool)
    return StoryParams(table, pizza, response, baker, baker_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pizza = f["pizza_cfg"]
    return [
        f'Write a rhyming story for a young child that includes the words "pizza", "shame", and "tolerance".',
        f"Tell a short story where {f['baker'].id} feels shame after a pizza mishap, but {f['helper'].id} shows tolerance and bravery.",
        f"Write a gentle story about moral value and reconciliation, using {pizza.label} as the shared treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    baker = f["baker"]
    helper = f["helper"]
    pizza = f["pizza_cfg"]
    return [
        QAItem(
            question=f"Why did {baker.id} feel shame?",
            answer=f"{baker.id} felt shame because the pizza got messy and the mistake seemed embarrassing. {helper.id} stayed calm, which gave {baker.id} room to tell the truth and fix it."
        ),
        QAItem(
            question="How did the children make things better?",
            answer=f"They cleaned the table, split the pizza fairly, and said sorry and yes with kind hearts. That is why the story ends in reconciliation instead of hurt feelings."
        ),
        QAItem(
            question=f"What moral value did the story show with {pizza.label}?",
            answer=f"It showed that tolerance and bravery can turn a small mistake into a kind repair. Sharing the pizza fairly mattered more than staying embarrassed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is pizza?", "Pizza is a round food with a crust and toppings that people often share. It is easy to cut into slices."),
        QAItem("What does shame feel like?", "Shame is a sore, embarrassed feeling that can make someone want to hide. A kind friend can help that feeling fade."),
        QAItem("What is tolerance?", "Tolerance means being patient and kind when someone makes a mistake or is different. It helps people stay together."),
        QAItem("What does reconciliation mean?", "Reconciliation means making up after a problem. People listen, forgive, and become friends again."),
        QAItem("What is bravery?", "Bravery means doing the kind and right thing even when it feels a little hard or scary."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "cheese", "hug", "Mia", "girl", "Noah", "boy"),
    StoryParams("picnic", "pepper", "sweep", "Leo", "boy", "Ava", "girl"),
    StoryParams("kitchen", "rainbow", "calm_talk", "Nora", "girl", "Eli", "boy"),
]


ASP_RULES = r"""
reconciled :- brave(helper), tolerant(helper), shame(baker), response_ok.
response_ok :- response(hug).
response_ok :- response(sweep).
response_ok :- response(calm_talk).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TABLES:
        lines.append(asp.fact("table", tid))
    for pid in PIZZAS:
        lines.append(asp.fact("pizza", pid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    lines.append(asp.fact("brave", "helper"))
    lines.append(asp.fact("tolerant", "helper"))
    lines.append(asp.fact("shame", "baker"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show reconciled/0."))
    atoms = set(asp.atoms(model, "reconciled"))
    rc = 0
    if atoms == {()}:
        print("OK: ASP recognizes reconciliation.")
    else:
        rc = 1
        print("MISMATCH: ASP did not derive reconciliation.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(TABLES[params.table], PIZZAS[params.pizza], RESPONSES[params.response],
                 params.baker, params.baker_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reconciled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for t, p, r in valid_combos():
            print(f"  {t:8} {p:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
