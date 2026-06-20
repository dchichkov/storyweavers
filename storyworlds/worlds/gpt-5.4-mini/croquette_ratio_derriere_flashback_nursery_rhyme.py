#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/croquette_ratio_derriere_flashback_nursery_rhyme.py
====================================================================================

A tiny storyworld in a nursery-rhyme voice about a child helping in the kitchen,
learning a recipe ratio, and remembering a warm flashback from a grandparent's
song.

Domain:
- Croquettes are shaped and fried in a small pan.
- The recipe has a ratio: one potato scoop to two crumb scoops.
- The child learns not to sit their derriere on the counter while the food is hot.
- A flashback lets the story remember an earlier rhyme that taught the safe rule.

The engine is classical and state-driven: character emotions rise and fall,
physical meters change as the kitchen work changes, and the ending proves what
changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/croquette_ratio_derriere_flashback_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/croquette_ratio_derriere_flashback_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/croquette_ratio_derriere_flashback_nursery_rhyme.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
# ---------------------------------------------------------------------------
# Entities and world
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "granny"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "granny", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

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


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Recipe:
    id: str
    name: str
    ratio_num: int
    ratio_den: int
    flashback_line: str
    ending_image: str


@dataclass(frozen=True)
class KitchenRule:
    id: str
    text: str


RECIPES = {
    "plain": Recipe(
        "plain",
        "plain croquettes",
        1, 2,
        "Once before, in a song by the stove, the granny had laughed, 'One potato, two crumbs, and the croquettes will be done.'",
        "A little plate of golden croquettes sat like sunbeams on a cloth.",
    ),
    "herb": Recipe(
        "herb",
        "herb croquettes",
        1, 2,
        "In the flashback, the granny had tapped the spoon and sung, 'Keep the ratio neat, and the little bites will be sweet.'",
        "A neat row of herb croquettes waited, golden and tidy, in a dish.",
    ),
    "tiny": Recipe(
        "tiny",
        "tiny croquettes",
        2, 3,
        "Long ago, the granny had hummed, 'Count the scoops and count them right, or the croquettes won't hold at night.'",
        "Tiny croquettes lined up like beads on a bright blue plate.",
    ),
}

RULES = {
    "hot_counter": KitchenRule("hot_counter", "The counter was hot, and hot counters are no place for a derriere."),
    "measure_right": KitchenRule("measure_right", "The ratio must stay right, so the croquettes stay kind and light."),
    "ask_help": KitchenRule("ask_help", "If the bowl feels tricky, ask a grown-up for a handy hand."),
}

NAMES = ["Mia", "Pip", "Nora", "Ben", "Luna", "Toby", "Ada", "Finn"]
GRAND_NAMES = ["Granny", "Grandma", "Grandpa", "Grandda"]
PARENTS = ["mother", "father"]


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    grownup: str
    grownup_type: str
    recipe: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about croquettes, ratio, and a flashback.")
    ap.add_argument("--child")
    ap.add_argument("--grownup", choices=GRAND_NAMES)
    ap.add_argument("--recipe", choices=RECIPES)
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


def _pick_name(rng: random.Random) -> tuple[str, str]:
    name = rng.choice(NAMES)
    gender = "girl" if name in {"Mia", "Nora", "Luna", "Ada"} else "boy"
    return name, gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child, gender = (_pick_name(rng) if not args.child else (args.child, "girl" if args.child in {"Mia", "Nora", "Luna", "Ada"} else "boy"))
    grownup = args.grownup or rng.choice(GRAND_NAMES)
    grownup_type = "grandmother" if grownup in {"Granny", "Grandma"} else "grandfather"
    recipe = args.recipe or rng.choice(list(RECIPES))
    return StoryParams(child, gender, grownup, grownup_type, recipe)


def valid_combos() -> list[tuple[str, str, str]]:
    return [("kitchen", g, r) for g in GRAND_NAMES for r in RECIPES]


ASP_RULES = r"""
valid(kitchen, G, R) :- grownup(G), recipe(R).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("grownup", g) for g in GRAND_NAMES]
    lines += [asp.fact("recipe", r) for r in RECIPES]
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    m = asp.one_model(asp_program("#show valid/3."))
    clingo = set(asp.atoms(m, "valid"))
    py = set(valid_combos())
    if clingo == py:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH:", clingo ^ py)
        return 1

    try:
        sample = generate(resolve_params(argparse.Namespace(child=None, grownup=None, recipe=None), random.Random(7)))
        assert sample.story.strip()
        print("OK: smoke-test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def _r_hot(world: World) -> list[str]:
    out = []
    if world.facts.get("counter_hot") and not world.fired:
        world.fired.add(("hot",))
        world.get("child").memes["careful"] += 1
        out.append("__hot__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for s in _r_hot(world):
        if not s.startswith("__"):
            produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="child"))
    grownup = world.add(Entity("grownup", kind="character", type=params.grownup_type, role="guide", label=params.grownup))
    bowl = world.add(Entity("bowl", label="mixing bowl"))
    counter = world.add(Entity("counter", label="counter"))
    spoon = world.add(Entity("spoon", label="wooden spoon"))
    recipe = RECIPES[params.recipe]
    rule = RULES["hot_counter"]

    child.memes["curious"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.id} was a small bright child in the kitchen, with {grownup.label_word} near at hand.")
    world.say(f"They wanted to make {recipe.name}, and the spoon went clickety-clack in the bowl.")
    world.say(f"The recipe asked for a careful ratio: {recipe.ratio_num} scoop of potatoes to {recipe.ratio_den} scoops of crumbs.")

    world.para()
    world.say(rule.text)
    world.say(f"{child.id} leaned close and said, 'I can sit my derriere right here and keep watch.'")
    world.say(f"But {grownup.label_word} shook {grownup.pronoun('possessive')} head and said, 'No, no, dearie, not on the hot counter.'")
    child.memes["defiance"] += 1

    world.para()
    world.facts["counter_hot"] = True
    propagate(world, narrate=False)
    world.say(recipe.flashback_line)
    world.say(f"That memory made the rule feel true, and {child.id} slid back from the heat.")
    child.memes["fear"] += 1
    child.memes["trust"] += 1

    world.para()
    world.say(f"{grownup.label_word.capitalize()} showed {child.id} how to count the crumbs just so, and the ratio stayed neat.")
    world.say(f"{child.id} stirred with {spoon.label} until the mixture held together like soft, friendly clay.")
    world.say(f"Then the croquettes were shaped, sizzled, and lifted out with care.")
    child.memes["joy"] += 1
    child.meters["helped"] += 1
    world.say(recipe.ending_image)
    world.say(f"{child.id} grinned, safe on the floor, while {grownup.label_word} called the day a good one.")
    world.facts.update(
        child=child, grownup=grownup, recipe=recipe, bowl=bowl, counter=counter, spoon=spoon,
        outcome="safe", remembered=True, ratio_ok=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    recipe: Recipe = f["recipe"]
    child: Entity = f["child"]
    return [
        f"Write a nursery-rhyme style story that includes the words croquette, ratio, and derriere.",
        f"Tell a gentle kitchen story where {child.id} learns the right ratio for {recipe.name} and remembers an earlier rhyme.",
        f"Write a child-facing flashback story in a sing-song voice about making croquettes safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    grownup: Entity = f["grownup"]
    recipe: Recipe = f["recipe"]
    return [
        QAItem(
            question="What was the child helping make?",
            answer=f"{child.id} was helping make {recipe.name}. The little croquettes were the special treat that needed patience and a steady hand."
        ),
        QAItem(
            question="What was the ratio the child had to remember?",
            answer=f"The recipe called for {recipe.ratio_num} scoop of potatoes to {recipe.ratio_den} scoops of crumbs. That ratio helped the croquettes stay together and turn out right."
        ),
        QAItem(
            question="Why did the grown-up stop the child from sitting on the counter?",
            answer=f"Because the counter was hot, and a derriere should not sit on a hot counter. The grown-up wanted {child.id} to stay safe while the food cooked."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    recipe: Recipe = f["recipe"]
    return [
        QAItem(
            question="What is a croquette?",
            answer="A croquette is a small food shaped into a little piece and often cooked until it is crisp and golden."
        ),
        QAItem(
            question="What does ratio mean?",
            answer="A ratio tells how much of one thing goes with how much of another thing. It helps keep cooking neat and balanced."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story remembers something that happened earlier. It lets the reader hear an old lesson or see an earlier moment again."
        ),
        QAItem(
            question="Why should hot counters be handled carefully?",
            answer="Hot counters can burn skin. It is safer to keep away from them and ask a grown-up for help."
        ),
        QAItem(
            question="Why does the recipe ratio matter for croquettes?",
            answer=f"The ratio matters because {recipe.name} need the right mix to hold together. If the mix is off, the croquettes can fall apart or feel too heavy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        out.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(out)


CURATED = [StoryParams("Mia", "girl", "Granny", "grandmother", "plain")]


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos")
        for c in valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
