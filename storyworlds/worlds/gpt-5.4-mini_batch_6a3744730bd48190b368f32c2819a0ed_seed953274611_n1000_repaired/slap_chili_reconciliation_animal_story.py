#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slap_chili_reconciliation_animal_story.py
========================================================================

A tiny animal-story world about a small kitchen misunderstanding, a too-spicy
bowl of chili, and a reconciliation that mends the hurt.

Seed words:
- slap
- chili

Feature:
- reconciliation

Style:
- animal story

The world is intentionally simple: two animal friends are sharing a meal in a
small setting, one makes an upsetting move, the hurt is felt in the state, and
the ending proves the friendship was repaired.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "cat", "kitten", "mouse", "fox", "bear", "dog", "panda"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    setting: str = "cozy cabin"
    animal1: str = "Pip"
    animal1_type: str = "rabbit"
    animal2: str = "Milo"
    animal2_type: str = "bear"
    dish: str = "chili"
    spice: str = "mild"
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


@dataclass
class Setting:
    id: str
    place: str
    shared_table: str
    quiet_line: str
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


@dataclass
class Dish:
    id: str
    label: str
    hot_words: list[str]
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


@dataclass
class Move:
    id: str
    verb: str
    kind: str
    impact: int
    apology_text: str
    repair_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("animal1")
    b = world.get("animal2")
    if a.meters["slapped"] >= THRESHOLD and (("hurt",) not in world.fired):
        world.fired.add(("hurt",))
        b.memes["hurt"] += 1
        b.memes["sad"] += 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [Rule("hurt", _r_hurt)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def is_reconcilable(move: Move, dish: Dish) -> bool:
    return move.kind == "apology" and dish.id == "chili"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for did in DISHES:
            for mid in MOVES:
                if is_reconcilable(MOVES[mid], DISHES[did]):
                    combos.append((sid, did, mid))
    return combos


def setting_detail(setting: Setting) -> str:
    return f"{setting.place} had {setting.shared_table} and {setting.quiet_line}"


def tell(setting: Setting, dish: Dish, move: Move, params: StoryParams) -> World:
    world = World(setting)
    a = world.add(Entity(id="animal1", kind="character", type=params.animal1_type, label=params.animal1, role="first"))
    b = world.add(Entity(id="animal2", kind="character", type=params.animal2_type, label=params.animal2, role="second"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="thing", label=dish.label, tags=set(dish.tags)))
    a.memes["eager"] += 1
    b.memes["hopeful"] += 1

    world.say(
        f"In the {setting.place}, {a.label} and {b.label} sat at {setting.shared_table}. "
        f"They were ready to share a warm bowl of {dish.label}."
    )
    world.say(
        f"{a.label} liked the smell, but {dish.hot_words[0]} made the steam curl up like a tiny red flag."
    )
    world.para()
    world.say(
        f'"This {dish.label} is too hot!" {b.label} cried.'
    )
    world.say(
        f"{a.label} got cross and gave {b.label} a quick slap on the paw."
    )
    a.meters["slapped"] += 1
    b.memes["shocked"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{b.label} blinked back tears and held still. The table went quiet."
    )
    a.memes["regret"] += 1
    world.say(
        f"Then {a.label}'s ears drooped. '{move.apology_text.format(dish=dish.label)}' {a.label} said."
    )
    b.memes["forgive"] += 1
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f"{b.label} sniffed once, then nodded. '{move.repair_text.format(dish=dish.label)}' {b.label} said."
    )
    world.para()
    world.say(
        f"So they cooled the {dish.label}, shared it again, and ate side by side. "
        f"{a.label} passed the spoon carefully this time, and {b.label} passed it back with a smile."
    )

    world.facts.update(
        setting=setting,
        dish=dish,
        move=move,
        animal1=a,
        animal2=b,
        bowl=bowl,
        reconciled=True,
    )
    return world


SETTINGS = {
    "cabin": Setting(
        id="cabin",
        place="a cozy cabin",
        shared_table="a little pine table",
        quiet_line="the fire cracked softly in the corner",
        tags={"cabin", "indoors"},
    ),
    "barn": Setting(
        id="barn",
        place="a warm barn kitchen",
        shared_table="a wobbly wooden table",
        quiet_line="the hens slept in their coop nearby",
        tags={"barn", "indoors"},
    ),
    "picnic": Setting(
        id="picnic",
        place="a sunny picnic blanket",
        shared_table="a red checkered cloth",
        quiet_line="the grass waved in the breeze",
        tags={"picnic", "outdoors"},
    ),
}

DISHES = {
    "chili": Dish(
        id="chili",
        label="chili",
        hot_words=["pepper"],
        tags={"food", "hot"},
    ),
    "bean_chili": Dish(
        id="bean_chili",
        label="bean chili",
        hot_words=["spicy bean"],
        tags={"food", "hot"},
    ),
}

MOVES = {
    "apology": Move(
        id="apology",
        verb="apologize",
        kind="apology",
        impact=1,
        apology_text="I was grumpy because the chili was too hot. I'm sorry for the slap.",
        repair_text="I forgive you. Let's share the chili after it cools.",
        tags={"reconciliation", "apology"},
    ),
    "gentle_talk": Move(
        id="gentle_talk",
        verb="talk gently",
        kind="apology",
        impact=1,
        apology_text="I shouldn't have slapped you. Let's start over.",
        repair_text="It's okay. We can sit together and calm down.",
        tags={"reconciliation", "apology"},
    ),
}


TRAITS = ["kind", "shy", "brave", "curious", "gentle", "helpful"]
ANIMALS = ["rabbit", "bear", "fox", "cat", "dog", "mouse", "badger", "otter", "panda"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal reconciliation storyworld with slap and chili.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--type1", choices=ANIMALS)
    ap.add_argument("--type2", choices=ANIMALS)
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
    if args.move and args.move not in MOVES:
        raise StoryError("Unknown move.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.dish is None or c[1] == args.dish)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, dish, move = rng.choice(sorted(combos))
    n1 = args.name1 or rng.choice(["Pip", "Mina", "Otto", "Luna", "Nori", "Bram"])
    n2 = args.name2 or rng.choice([n for n in ["Pip", "Mina", "Otto", "Luna", "Nori", "Bram"] if n != n1])
    t1 = args.type1 or rng.choice(ANIMALS)
    t2 = args.type2 or rng.choice([a for a in ANIMALS if a != t1])
    return StoryParams(setting=setting, animal1=n1, animal1_type=t1, animal2=n2, animal2_type=t2, dish=dish, spice="mild", seed=None)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the words "{f["move"].id}" and "{f["dish"].label}".',
        f"Tell a small animal story where {f['animal1'].label} and {f['animal2'].label} get upset over {f['dish'].label} and then reconcile.",
        "Write a gentle story about two animals, a mistake, an apology, and friends making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["animal1"]
    b = world.facts["animal2"]
    dish = world.facts["dish"]
    return [
        QAItem(question="What was the problem in the story?", answer=f"{a.label} slapped {b.label}, and that made {b.label} feel hurt. The argument started because the bowl of {dish.label} was too hot."),
        QAItem(question="How did they make up?", answer=f"{a.label} apologized, and {b.label} forgave them. After that, they cooled the {dish.label} and shared it again at the table."),
        QAItem(question="What changed by the end?", answer=f"At the end, the animals were sitting together instead of arguing. The same {dish.label} that caused the fuss became part of their peaceful meal."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is chili?", answer="Chili is a warm, often spicy food made in a pot and served in bowls. It can steam and feel very hot."),
        QAItem(question="Why should animals use gentle words when they are angry?", answer="Gentle words help stop a fight from getting worse. They give everyone a chance to calm down and listen."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation means making up after a fight. It happens when both sides feel sorry, forgive, and become friendly again."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cabin", animal1="Pip", animal1_type="rabbit", animal2="Mina", animal2_type="fox", dish="chili", spice="mild"),
    StoryParams(setting="barn", animal1="Otto", animal1_type="bear", animal2="Luna", animal2_type="cat", dish="bean_chili", spice="mild"),
    StoryParams(setting="picnic", animal1="Nori", animal1_type="mouse", animal2="Bram", animal2_type="otter", dish="chili", spice="mild"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.dish not in DISHES:
        raise StoryError("Invalid dish.")
    if params.animal1_type not in ANIMALS or params.animal2_type not in ANIMALS:
        raise StoryError("Invalid animal type.")
    world = tell(SETTINGS[params.setting], DISHES[params.dish], MOVES["apology"], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
hurt(B) :- slapped(A,B), animal(A), animal(B).
reconciled :- apology(A,B), hurt(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DISHES:
        lines.append(asp.fact("dish", did))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
        if MOVES[mid].kind == "apology":
            lines.append(asp.fact("apology", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/0."))
    asp_ok = bool(asp.atoms(model, "reconciled"))
    py_ok = bool(valid_combos())
    if not asp_ok or not py_ok:
        print("MISMATCH in ASP gate.")
        return 1
    print("OK: ASP twin loads and the world has valid reconciliation stories.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generate() smoke test passed.")
    return 0


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
        print(asp_program("#show reconciled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for combo in valid_combos():
            print(combo)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
