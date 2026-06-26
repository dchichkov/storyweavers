#!/usr/bin/env python3
"""
storyworlds/worlds/carol_diet_ask_happy_ending_humor_fable.py
==============================================================

A small fable-like story world about Carol, a diet, and the courage to ask
for help. The domain stays narrow on purpose: the hero wants a sweet snack,
follows a chosen diet, asks a friend or keeper for a better plan, and ends in a
happy, slightly humorous resolution.

The simulated state matters:
- Carol has physical meters like hunger, energy, and fullness.
- Carol also has memes like worry, hope, and pride.
- Foods change those meters.
- Asking can uncover a gentler substitute that keeps the diet promise.

The tone aims for a short fable with a warm ending and a tiny smile.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["hunger", "energy", "fullness", "sweet_craving"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "pride", "delight", "humor"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Diet:
    id: str
    label: str
    avoids: set[str] = field(default_factory=set)
    allows: set[str] = field(default_factory=set)
    theme: str = ""


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    kind: str
    sweetness: int
    fullness: int
    humor: str
    healthy: bool = False
    diet_fit: set[str] = field(default_factory=set)


@dataclass
class AskPlan:
    id: str
    prompt: str
    request: str
    answer: str
    substitute_food: str
    cheers: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy as _copy

        other = World()
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def _r_hunger(world: World) -> list[str]:
    out = []
    carol = world.entities.get("carol")
    if not carol:
        return out
    if carol.meters["hunger"] < THRESHOLD:
        return out
    if ("hunger",) in world.fired:
        return out
    world.fired.add(("hunger",))
    carol.memes["worry"] += 1
    out.append("Carol's tummy complained like a little drum.")
    return out


def _r_still_smile(world: World) -> list[str]:
    out = []
    carol = world.entities.get("carol")
    if not carol:
        return out
    if carol.memes["hope"] < THRESHOLD or carol.memes["pride"] < THRESHOLD:
        return out
    sig = ("smile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carol.memes["humor"] += 1
    out.append("Carol still found the joke in her own grumbly stomach.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_hunger, _r_still_smile):
            sent = rule(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


DIETS = {
    "light": Diet(
        id="light",
        label="a light diet",
        avoids={"cake", "pie", "syrup"},
        allows={"apple", "carrot", "oat", "berry"},
        theme="keep the belly light",
    ),
    "no_sugar": Diet(
        id="no_sugar",
        label="a no-sugar diet",
        avoids={"cake", "pie", "syrup"},
        allows={"apple", "carrot", "berry", "yogurt"},
        theme="skip the sugar",
    ),
    "small_plate": Diet(
        id="small_plate",
        label="a small-plate diet",
        avoids={"pie", "syrup"},
        allows={"apple", "carrot", "berry", "oat", "salad"},
        theme="eat only a little at a time",
    ),
}

FOODS = {
    "cake": Food(
        id="cake",
        label="cake",
        phrase="a slice of berry cake",
        kind="cake",
        sweetness=3,
        fullness=2,
        humor="it wore a berry hat of frosting",
        healthy=False,
        diet_fit=set(),
    ),
    "apple": Food(
        id="apple",
        label="apple slices",
        phrase="a bowl of apple slices",
        kind="apple",
        sweetness=1,
        fullness=1,
        humor="the slices looked like tiny smiles",
        healthy=True,
        diet_fit={"light", "no_sugar", "small_plate"},
    ),
    "carrot": Food(
        id="carrot",
        label="carrot sticks",
        phrase="a plate of carrot sticks",
        kind="carrot",
        sweetness=0,
        fullness=1,
        humor="they stood in a neat orange row like little flags",
        healthy=True,
        diet_fit={"light", "no_sugar", "small_plate"},
    ),
    "berry": Food(
        id="berry",
        label="berries",
        phrase="a little cup of berries",
        kind="berry",
        sweetness=1,
        fullness=1,
        humor="they looked like shiny beads from the hedge",
        healthy=True,
        diet_fit={"light", "no_sugar", "small_plate"},
    ),
    "oat": Food(
        id="oats",
        label="warm oats",
        phrase="a warm bowl of oats",
        kind="oat",
        sweetness=0,
        fullness=2,
        humor="the oats puffed up like a sleepy cloud",
        healthy=True,
        diet_fit={"light", "small_plate"},
    ),
    "salad": Food(
        id="salad",
        label="salad",
        phrase="a crisp little salad",
        kind="salad",
        sweetness=0,
        fullness=1,
        humor="the leaves crinkled like secret whispers",
        healthy=True,
        diet_fit={"small_plate"},
    ),
}

ASKS = {
    "baker": AskPlan(
        id="baker",
        prompt="ask the baker",
        request="for a gentler treat",
        answer="for a basket of fruit instead of cake",
        substitute_food="berry",
        cheers="The baker laughed and said Carol had asked for the smartest sweet in town.",
    ),
    "friend": AskPlan(
        id="friend",
        prompt="ask her friend",
        request="for help choosing",
        answer="for a snack that fit the plan",
        substitute_food="apple",
        cheers="Her friend grinned and said the safest snack could also be the cheeriest one.",
    ),
    "keeper": AskPlan(
        id="keeper",
        prompt="ask the keeper of the pantry",
        request="for a tidy lunch",
        answer="for warm oats and carrot sticks",
        substitute_food="oat",
        cheers="The keeper nodded and said good sense often came with a spoon.",
    ),
}

CAROL_NAMES = ["Carol"]
FRIENDS = ["Moss", "Pip", "Wren", "Bram"]
SETTINGS = ["the lane", "the orchard", "the market", "the pantry"]

CURATED = [
    ("light", "cake", "baker"),
    ("no_sugar", "cake", "friend"),
    ("small_plate", "cake", "keeper"),
]


@dataclass
class StoryParams:
    diet: str
    food: str
    ask: str
    setting: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for d in DIETS:
        for f in FOODS:
            for a in ASKS:
                if f in DIETS[d].avoids and ASKS[a].substitute_food in FOODS:
                    combos.append((d, f, a))
    return combos


def explain_rejection(diet: Diet, food: Food, ask: AskPlan) -> str:
    return (
        f"(No story: {food.label} is too tempting for {diet.label}, and the ask "
        f"plan must lead to a sensible substitute. Try a different snack or a different ask.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Carol, a diet, and a fable-like ask for help."
    )
    ap.add_argument("--diet", choices=DIETS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--ask", choices=ASKS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--friend", choices=FRIENDS)
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
    if args.diet and args.food and args.ask:
        d, f, a = DIETS[args.diet], FOODS[args.food], ASKS[args.ask]
        if f.id not in d.avoids:
            raise StoryError("(No story: Carol must be tempted by food that conflicts with the diet.)")
        if a.substitute_food not in FOODS:
            raise StoryError("(No story: the ask needs a real substitute.)")
    combos = [c for c in valid_combos()
              if (args.diet is None or c[0] == args.diet)
              and (args.food is None or c[1] == args.food)
              and (args.ask is None or c[2] == args.ask)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    diet, food, ask = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(SETTINGS)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(diet=diet, food=food, ask=ask, setting=setting, friend=friend)


def predict_outcome(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    carol = sim.get("carol")
    food = FOODS[params.food]
    carol.meters["hunger"] += 1
    carol.meters["sweet_craving"] += food.sweetness
    propagate(sim, narrate=False)
    return {"worry": carol.memes["worry"], "humor": carol.memes["humor"]}


def tell(params: StoryParams) -> World:
    world = World()
    diet = DIETS[params.diet]
    food = FOODS[params.food]
    ask = ASKS[params.ask]

    carol = world.add(Entity(id="carol", kind="character", type="rabbit", label="Carol", traits=["kind", "careful"]))
    friend = world.add(Entity(id="friend", kind="character", type="mouse", label=params.friend))
    pantry = world.add(Entity(id="place", kind="thing", type="place", label=params.setting))

    carol.meters["hunger"] = 1
    carol.meters["sweet_craving"] = food.sweetness
    carol.memes["pride"] = 1
    world.facts.update(carol=carol, friend=friend, diet=diet, food=food, ask=ask, setting=pantry)

    world.say(f"Carol the rabbit was trying to keep {diet.label} in the little lane of the day.")
    world.say(f"She loved sweet things, and {food.phrase} winked at her from the counter.")
    world.para()
    world.say(
        f"Carol's tummy rumbled, because {food.label} was exactly the kind of treat her diet told her to avoid."
    )
    world.say(f"The trouble was funny in a small way: the cake looked as if it had dressed up to be irresistible.")
    world.para()
    world.say(f"Instead of grabbing it, Carol did something wiser. She decided to {ask.prompt}.")
    world.say(
        f"She asked {friend.label} {ask.request}, and then she asked for {ask.answer}."
    )
    if food.id in diet.avoids:
        world.say(
            f"{friend.label} listened, blinked, and said, 'That is a brave question. Brave questions often chew the problem for you.'"
        )
    substitute = FOODS[ask.substitute_food]
    world.say(
        f"So they chose {substitute.phrase} instead. {substitute.humor.capitalize()}."
    )
    world.para()
    carol.meters["fullness"] += substitute.fullness
    carol.meters["hunger"] = max(0.0, carol.meters["hunger"] - 1)
    carol.memes["hope"] += 1
    carol.memes["delight"] += 1
    carol.memes["pride"] += 1
    carol.memes["worry"] = 0.0
    carol.memes["humor"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Carol ate the right snack for her promise, and her little smile was bigger than the cake's frosting."
    )
    world.say(
        f"She learned that a good diet is easier to keep when a fox-sized worry becomes a mouse-sized question."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about Carol, a {f["diet"].label}, and the courage to ask for help.',
        f'Write a humorous little story where Carol wants {f["food"].phrase} but chooses a wiser food after she asks.',
        f'Write a happy-ending fable featuring Carol, a diet, and a gentle question that leads to a better snack.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    carol: Entity = f["carol"]
    friend: Entity = f["friend"]
    diet: Diet = f["diet"]
    food: Food = f["food"]
    ask: AskPlan = f["ask"]
    sub = FOODS[ask.substitute_food]

    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Carol, a kind rabbit who is trying to keep her diet.",
        ),
        QAItem(
            question=f"Why was {food.label} a problem for Carol?",
            answer=f"It did not fit {diet.label}, so it was the kind of snack Carol was trying to avoid.",
        ),
        QAItem(
            question=f"What did Carol do instead of taking {food.label}?",
            answer=f"She asked {friend.label} for help and chose {sub.phrase} instead.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with Carol keeping her promise and enjoying a better snack.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    food: Food = f["food"]
    ask: AskPlan = f["ask"]
    diet: Diet = f["diet"]
    out = [
        QAItem(
            question="What is a diet?",
            answer="A diet is a choice about what kind of food someone will eat, often to stay healthy or follow a rule.",
        ),
        QAItem(
            question="Why can it help to ask for help?",
            answer="Asking can bring another idea, and another idea can be easier than trying to solve everything alone.",
        ),
        QAItem(
            question="Why can cake be a tricky snack?",
            answer="Cake is sweet and tempting, so it can be hard to stop at just one bite.",
        ),
        QAItem(
            question="What makes this story feel like a fable?",
            answer="It uses an animal character, a small lesson, and a simple ending that teaches a gentle choice.",
        ),
    ]
    if food.id == "cake":
        out.append(QAItem(
            question="Why did the cake look funny in the story?",
            answer="The cake looked funny because it seemed to be wearing a berry hat of frosting, almost like it was dressed up.",
        ))
    if ask.id == "keeper":
        out.append(QAItem(
            question="What does a pantry keeper do?",
            answer="A pantry keeper watches over the food and helps choose what belongs on the table.",
        ))
    if "sugar" in diet.id:
        out.append(QAItem(
            question="Why avoid sugar?",
            answer="Some diets avoid sugar to keep meals simpler and healthier.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
diet_conflict(D,F) :- diet(D), avoids(D,F), food(F).
valid_story(D,F,A) :- diet_conflict(D,F), askplan(A), substitute(A,S), food(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for did, d in DIETS.items():
        lines.append(asp.fact("diet", did))
        for f in sorted(d.avoids):
            lines.append(asp.fact("avoids", did, f))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
    for aid, a in ASKS.items():
        lines.append(asp.fact("askplan", aid))
        lines.append(asp.fact("substitute", aid, a.substitute_food))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for d, f, a in CURATED:
            params = StoryParams(
                diet=d,
                food=f,
                ask=a,
                setting=random.choice(SETTINGS),
                friend=random.choice(FRIENDS),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.diet} / {p.food} / {p.ask}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
