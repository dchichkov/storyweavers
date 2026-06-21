#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/absorb_confine_magic_problem_solving_animal_story.py
====================================================================================

A small animal story world about a little magical mishap that can be fixed with
careful problem solving. The seed words are "absorb" and "confine"; the domain
turns them into a gentle child-facing tale about an animal friend who makes a
mess of magic, then learns how to contain it with help.

The world is built around a few moving parts:
- an animal protagonist and a helper
- a magical item that can overflow with shimmer
- a real-world problem that must be solved
- a confining object that keeps magic from spreading
- an absorbent object that soaks up the stray sparkle

The story engine is state-driven: physical meters and emotional memes change as
the tale unfolds. The ending shows what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/absorb_confine_magic_problem_solving_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/absorb_confine_magic_problem_solving_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/absorb_confine_magic_problem_solving_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/absorb_confine_magic_problem_solving_animal_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/absorb_confine_magic_problem_solving_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
MAGIC_THRESHOLD = 1.0
SPILL_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    confining: bool = False
    absorbent: bool = False
    magical: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"magic": 0.0, "spill": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "calm": 0.0, "joy": 0.0, "pride": 0.0}

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
        return self.label or self.id
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
class StoryParams:
    animal: str
    animal_type: str
    helper: str
    helper_type: str
    magic_item: str
    problem: str
    confine_object: str
    absorb_object: str
    setting: str
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


@dataclass(frozen=True)
class AnimalSpec:
    id: str
    type: str
    label: str
    trait: str
    pronoun_type: str
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


@dataclass(frozen=True)
class MagicItemSpec:
    id: str
    label: str
    phrase: str
    cause: str
    spill_text: str
    colors: str
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


@dataclass(frozen=True)
class ProblemSpec:
    id: str
    label: str
    issue: str
    danger: str
    solution_hint: str
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


@dataclass(frozen=True)
class ToolSpec:
    id: str
    label: str
    use_text: str
    outcome_text: str
    kind: str
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
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


ANIMALS = {
    "rabbit": AnimalSpec("rabbit", "rabbit", "rabbit", "quick", "they"),
    "fox": AnimalSpec("fox", "fox", "fox", "clever", "they"),
    "bear": AnimalSpec("bear", "bear", "bear", "gentle", "they"),
    "cat": AnimalSpec("cat", "cat", "cat", "curious", "they"),
    "dog": AnimalSpec("dog", "dog", "dog", "loyal", "they"),
}

HELPERS = {
    "mouse": AnimalSpec("mouse", "mouse", "mouse", "tiny", "they"),
    "owl": AnimalSpec("owl", "owl", "owl", "wise", "they"),
    "turtle": AnimalSpec("turtle", "turtle", "turtle", "patient", "they"),
}

MAGIC_ITEMS = {
    "wand": MagicItemSpec("wand", "wand", "a little wand", "a sparkle sneeze", "sparkles spilled out", "gold"),
    "lamp": MagicItemSpec("lamp", "lamp", "a moon lamp", "a dream glow", "light leaked out", "blue"),
    "jar": MagicItemSpec("jar", "jar", "a glitter jar", "a giggle gust", "glitter poured out", "silver"),
}

PROBLEMS = {
    "glow": ProblemSpec("glow", "glow", "the room got too bright and jumpy", "the sparkles might bother the little animals", "the magic needed to be kept still"),
    "trail": ProblemSpec("trail", "trail", "sparkles were leaving a shining trail", "the trail could lead curious paws into trouble", "the trail had to be confined"),
}

TOOLS = {
    "basket": ToolSpec("basket", "basket", "placed the magic inside a woven basket", "the basket held it snugly", "contain"),
    "blanket": ToolSpec("blanket", "blanket", "wrapped the magic in a thick blanket", "the blanket absorbed the loose shimmer", "absorb"),
    "box": ToolSpec("box", "box", "closed the magic in a little box", "the box confine the sparkle", "confine"),
}

SETTINGS = ["meadow", "burrow", "barn", "moonlit tree hollow"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal magic story world about absorb and confine.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--confine-object", choices=TOOLS)
    ap.add_argument("--absorb-object", choices=TOOLS)
    ap.add_argument("--setting", choices=SETTINGS)
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


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for a in ANIMALS:
        for h in HELPERS:
            for m in MAGIC_ITEMS:
                for p in PROBLEMS:
                    combos.append((a, h, m, p, "basket", "blanket"))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for m in MAGIC_ITEMS:
        lines.append(asp.fact("magic_item", m))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,H,M,P) :- animal(A), helper(H), magic_item(M), problem(P).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid animal magic stories exist.")
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    magic_item = args.magic_item or rng.choice(sorted(MAGIC_ITEMS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    confine_object = args.confine_object or "box"
    absorb_object = args.absorb_object or "blanket"
    setting = args.setting or rng.choice(SETTINGS)
    if confine_object not in TOOLS or absorb_object not in TOOLS:
        raise StoryError("Unknown tool choice.")
    return StoryParams(
        animal=animal,
        animal_type=ANIMALS[animal].type,
        helper=helper,
        helper_type=HELPERS[helper].type,
        magic_item=magic_item,
        problem=problem,
        confine_object=confine_object,
        absorb_object=absorb_object,
        setting=setting,
    )


def _story_setup(world: World, a: Entity, h: Entity, item: Entity, prob: ProblemSpec) -> None:
    a.memes["joy"] += 1
    h.memes["calm"] += 1
    world.say(
        f"In a quiet {world.setting}, a {a.label_word} named {a.id} found {item.label} "
        f"while {h.id} watched nearby."
    )
    world.say(
        f"When {a.id} made a wish, {item.label} answered with a {prob.issue}."
    )


def _release_magic(world: World, a: Entity, item: Entity, prob: ProblemSpec) -> None:
    a.memes["worry"] += 1
    item.meters["magic"] += 1
    item.meters["spill"] += 1
    world.say(
        f"{item.label.capitalize()} began to glow, and {prob.label} turned real. "
        f"{prob.danger.capitalize()}."
    )


def _solve(world: World, h: Entity, conf: Entity, absb: Entity, item: Entity, prob: ProblemSpec) -> None:
    h.memes["pride"] += 1
    conf.meters["magic"] += 1
    absb.meters["spill"] += 1
    absb.meters["mess"] += 0.5
    world.say(
        f"{h.id} had an idea: first they {TOOLS[conf.id].use_text}, then they {TOOLS[absb.id].use_text}."
    )
    world.say(
        f"That plan worked because it could {TOOLS[absb.id].kind} the loose shimmer and {TOOLS[conf.id].kind} the rest."
    )


def _finish(world: World, a: Entity, h: Entity, item: Entity, conf: Entity, absb: Entity) -> None:
    a.memes["joy"] += 1
    h.memes["joy"] += 1
    a.memes["worry"] = 0.0
    world.say(
        f"Soon the {item.label} was quiet again. {item.label.capitalize()} stayed in the {conf.label}, "
        f"and the {absb.label} drank up the last sparkles."
    )
    world.say(
        f"{a.id} smiled at {h.id}. The little {a.label_word} had solved the problem, and the room felt safe and warm again."
    )


def tell(params: StoryParams) -> World:
    world = World(setting=params.setting)
    if params.animal not in ANIMALS or params.helper not in HELPERS or params.magic_item not in MAGIC_ITEMS or params.problem not in PROBLEMS:
        raise StoryError("Invalid story parameters.")
    animal = world.add(Entity(id=params.animal, kind="character", type=params.animal_type, label=params.animal))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, label=params.helper))
    item_spec = MAGIC_ITEMS[params.magic_item]
    prob_spec = PROBLEMS[params.problem]
    conf_spec = TOOLS[params.confine_object]
    abs_spec = TOOLS[params.absorb_object]
    item = world.add(Entity(id="magic_item", type="thing", label=item_spec.phrase, magical=True))
    conf = world.add(Entity(id="confine_object", type="thing", label=conf_spec.label, confining=True))
    absb = world.add(Entity(id="absorb_object", type="thing", label=abs_spec.label, absorbent=True))

    _story_setup(world, animal, helper, item, prob_spec)
    world.para()
    _release_magic(world, animal, item, prob_spec)
    world.para()
    _solve(world, helper, conf, absb, item, prob_spec)
    world.para()
    _finish(world, animal, helper, item, conf, absb)

    world.facts.update(animal=animal, helper=helper, item=item, conf=conf, absb=absb, prob=prob_spec, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a child that uses the words "absorb" and "confine" and includes a little magic problem.',
        f"Tell a gentle story about {f['animal'].id} and {f['helper'].id} where magic gets loose, then a smart idea confine it.",
        f"Write a problem-solving animal story with a magical object, a helpful friend, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal: Entity = f["animal"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"What problem did {animal.id} have?",
            answer=f"{animal.id} had a magical problem because the {item.label_word} got too lively and started to spill sparkle into the room. {helper.id} helped keep everyone calm while they fixed it.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used one thing to confine the magic and another thing to absorb the loose shimmer. That way the sparkle stayed in one place instead of spreading everywhere.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the magic quiet again, the room tidy, and {animal.id} smiling at {helper.id}. The ending proves their careful plan worked.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to absorb something?",
            answer="To absorb means to soak something up or take it in, like a towel soaking up water.",
        ),
        QAItem(
            question="What does it mean to confine something?",
            answer="To confine means to keep something inside a small place so it cannot spread around.",
        ),
        QAItem(
            question="Why is it good to solve problems with a plan?",
            answer="A plan helps you choose the right steps in the right order, so the problem gets smaller instead of bigger.",
        ),
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
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} flags={['confining' if e.confining else '', 'absorbent' if e.absorbent else '', 'magical' if e.magical else '']}")
    return "\n".join(lines)


CURATED = [
    StoryParams(animal="rabbit", animal_type="rabbit", helper="owl", helper_type="owl", magic_item="jar", problem="trail", confine_object="box", absorb_object="blanket", setting="meadow"),
    StoryParams(animal="fox", animal_type="fox", helper="mouse", helper_type="mouse", magic_item="wand", problem="glow", confine_object="basket", absorb_object="blanket", setting="burrow"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        rc = asp_verify()
        try:
            sample = generate(CURATED[0])
            _ = sample.story
            print("OK: generate() smoke test passed.")
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            rc = 1
        sys.exit(rc)
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
