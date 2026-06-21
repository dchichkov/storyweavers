#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/substitute_bop_bad_ending_curiosity_surprise_comedy.py
======================================================================================

A small, self-contained storyworld about curiosity, a surprise substitute, and a
comic bop that goes wrong. The world is built from a tiny simulated domain: a child
is making a treat or craft, wants a substitute ingredient or tool, gets surprised by
the result, and the story ends with a bad but harmless ending that still feels like
a comedy.

This world is intentionally narrow. It only generates plausible combinations in
which a substitute is genuinely used, the bop is physically small, and the bad
ending is comedic rather than scary.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/substitute_bop_bad_ending_curiosity_surprise_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/substitute_bop_bad_ending_curiosity_surprise_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/substitute_bop_bad_ending_curiosity_surprise_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/substitute_bop_bad_ending_curiosity_surprise_comedy.py --verify
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
SENSE_MIN = 2


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
class Recipe:
    id: str
    name: str
    substitute: str
    base_need: str
    where: str
    surprise: str
    bad_mishap: str
    bop_target: str
    bop_sound: str
    comedy_tail: str
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["messy"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "kitchen" in world.entities:
            world.get("kitchen").meters["chaos"] += 1
        out.append("__mess__")
    return out


def _r_boop(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["bopped"] < THRESHOLD:
            continue
        sig = ("bop", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["dazed"] += 1
        out.append("__bop__")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess), Rule("bop", "social", _r_boop)]


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


def hazard_at_risk(recipe: Recipe) -> bool:
    return bool(recipe.substitute and recipe.base_need)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def severity(recipe: Recipe, delay: int) -> int:
    return 1 + delay if recipe.bad_mishap else delay + 1


def contained(resp: Response, recipe: Recipe, delay: int) -> bool:
    return resp.power >= severity(recipe, delay)


def _do_substitute(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["messy"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, recipe_id: str) -> dict:
    sim = world.copy()
    recipe = sim.facts["recipe_cfg"]
    _do_substitute(sim, sim.get(recipe_id), narrate=False)
    return {
        "messy": sim.get(recipe_id).meters["messy"] >= THRESHOLD,
        "chaos": sim.get("kitchen").meters["chaos"],
    }


def intro(world: World, kid: Entity, parent: Entity, recipe: Recipe) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"On a bright afternoon, {kid.id} and {parent.label_word} were making "
        f"{recipe.name} in the kitchen."
    )
    world.say(
        f"{kid.id} stared at the bowl and asked curious questions about every "
        f"little thing."
    )


def surprise(world: World, kid: Entity, recipe: Recipe) -> None:
    kid.memes["surprised"] += 1
    world.say(
        f"Then came a surprise: the usual thing was gone, so {kid.id} found "
        f"{recipe.substitute} instead."
    )
    world.say(
        f'"This will work," {kid.id} said, trying the substitute with a grin.'
    )


def warn(world: World, parent: Entity, kid: Entity, recipe: Recipe) -> None:
    pred = predict(world, "target")
    world.facts["predicted_chaos"] = pred["chaos"]
    if pred["messy"]:
        world.say(
            f'"Careful," {parent.label_word} said. "{recipe.substitute} can make '
            f"a funny mess if it goes wrong."
        )


def mischief(world: World, kid: Entity, recipe: Recipe) -> None:
    kid.memes["bold"] += 1
    world.say(
        f"{kid.id} leaned in too close, curious as a kitten. The bowl wobbled, "
        f"and then the whole thing went {recipe.bop_sound}."
    )


def bop(world: World, target: Entity, recipe: Recipe) -> None:
    target.meters["bopped"] += 1
    world.say(
        f"{recipe.bop_sound} {target.label_word.capitalize()} got a tiny bop on "
        f"the nose from {recipe.bop_target}."
    )


def bad_ending(world: World, kid: Entity, parent: Entity, recipe: Recipe, response: Response) -> None:
    if contained(response, recipe, 0):
        world.say(
            f"{parent.label_word.capitalize()} came over and {response.text}."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} came over and {response.fail}."
        )
    world.say(
        f"The treat was lumpy, the spoon was crooked, and the kitchen looked like "
        f"a tiny comedy stage."
    )
    world.say(
        f"{kid.id} blinked, then laughed so hard {kid.pronoun()} nearly dropped "
        f"the bowl again. That was the bad ending: no perfect treat, just a silly "
        f"mess and a lesson about curious substitutes."
    )


def tell(recipe: Recipe, response: Response, kid_name: str = "Mia", kid_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="curious"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    target = world.add(Entity(id="target", label=recipe.substitute))
    world.add(Entity(id="kitchen", type="room", label="the kitchen"))
    world.facts["recipe_cfg"] = recipe

    intro(world, kid, parent, recipe)
    world.para()
    surprise(world, kid, recipe)
    warn(world, parent, kid, recipe)
    mischief(world, kid, recipe)
    world.para()
    bop(world, target, recipe)
    bad_ending(world, kid, parent, recipe, response)
    world.facts.update(
        kid=kid, parent=parent, target=target, recipe=recipe, response=response,
        delay=delay, outcome="bad", bop=True
    )
    return world


RECIPES = {
    "cake": Recipe(
        "cake", "a birthday cake", "a banana", "flour", "the counter",
        "squishy frosting surprise", "the batter splattered onto the floor",
        "the mixing bowl", "bop", "Everyone had to laugh and clean up",
        tags={"substitute", "bop", "curiosity", "surprise", "comedy"},
    ),
    "pudding": Recipe(
        "pudding", "chocolate pudding", "applesauce", "milk", "the fridge shelf",
        "wobbly pudding surprise", "the pudding slid off the spoon",
        "the whisk", "bop", "The spoon ended up wearing dessert",
        tags={"substitute", "bop", "curiosity", "surprise", "comedy"},
    ),
    "pancakes": Recipe(
        "pancakes", "pancakes", "yogurt", "eggs", "the cupboard",
        "slippery batter surprise", "the pan flipped the batter onto the cat",
        "the spatula", "bop", "The cat left with a frosting mustache",
        tags={"substitute", "bop", "curiosity", "surprise", "comedy"},
    ),
}

RESPONSES = {
    "towel": Response("towel", 3, 3, "grabbed a towel and wiped the mess in a flash",
                      "reached for a towel, but the mess was too wild", "wiped the mess away"),
    "napkin": Response("napkin", 2, 2, "used a napkin and saved the counter",
                       "used a napkin, but it was too small", "saved the counter"),
    "laugh": Response("laugh", 2, 1, "laughed first and then cleaned up together",
                      "laughed first, but the mess stayed put", "laughed and cleaned up together"),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ava", "Ella", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Eli", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for rid in RECIPES:
        for resp in RESPONSES:
            combos.append((rid, resp))
    return combos


@dataclass
@dataclass
class StoryParams:
    recipe: str
    response: str
    name: str
    gender: str
    parent: str
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


KNOWLEDGE = {
    "substitute": [("What is a substitute?",
                    "A substitute is something you use instead of the usual thing. It can help when the first thing is missing.")],
    "bop": [("What does bop mean?",
             "A bop is a light hit or tap. In a silly story, it can make a comic surprise without being serious.")],
    "curiosity": [("What is curiosity?",
                    "Curiosity is wanting to know more and asking questions about things.")],
    "surprise": [("What is a surprise?",
                   "A surprise is something you did not expect, so it makes you open your eyes wide.")],
    "comedy": [("What is comedy?",
                "Comedy is a kind of funny story meant to make you smile or laugh.")],
}
KNOWLEDGE_ORDER = ["substitute", "bop", "curiosity", "surprise", "comedy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    recipe = f["recipe_cfg"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "{recipe.substitute}" and "bop".',
        f"Tell a comic story where {f['kid'].id} uses a substitute while making {recipe.name}, gets a surprise, and the ending goes a little wrong.",
        f'Write a playful story with curiosity, surprise, and a bad ending where a tiny bop changes the day.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, parent, recipe = f["kid"], f["parent"], f["recipe_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {parent.label_word}, who were making {recipe.name} together."),
        ("What unexpected thing happened?",
         f"{recipe.substitute} showed up as a substitute, and that was a surprise for {kid.id}."),
        ("What small thing happened to make the story funny?",
         f"The bowl gave a little bop to {recipe.bop_target}, which made everyone stop and stare."),
    ]
    if f.get("outcome") == "bad":
        qa.append((
            "How did the story end?",
            f"It ended badly for the recipe but not for anyone's feelings. The kitchen became a silly mess, and the family had to laugh and clean up."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["recipe_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cake", "towel", "Mia", "girl", "mother", 0),
    StoryParams("pudding", "napkin", "Ben", "boy", "father", 0),
    StoryParams("pancakes", "laugh", "Luna", "girl", "mother", 0),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(R, S) :- recipe(R), response(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in RECIPES.items():
        lines.append(asp.fact("recipe", rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: valid combos match.")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        generate(CURATED[0])
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic substitute-and-bop storyworld.")
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, default=0)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.recipe is None or c[0] == args.recipe)
              and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    recipe, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(recipe, response, name, gender, parent, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(RECIPES[params.recipe], RESPONSES[params.response], params.name, params.gender, params.parent, params.delay)
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
        print(asp_program("", "#show sensible/1.\n#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
