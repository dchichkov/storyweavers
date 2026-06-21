#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/coarse_bad_ending_surprise_moral_value_comedy.py
================================================================================

A standalone storyworld about a small comedy mishap: a child wants to make a
"coarse" craft treat, a surprise goes sideways, an adult teaches a moral value
about honesty and cleanup, and the ending is bad in a funny, child-facing way.

Domain sketch:
- Two children are making a surprise snack/craft for a parent.
- One child wants a coarse topping or texture that is not meant for the treat.
- The mess causes a comedy chain reaction in the kitchen.
- The surprise is revealed too early.
- A moral lesson lands: tell the truth, ask for help, and clean up sooner.
- Ending is "bad" but gentle: the treat is ruined, the surprise is spoiled, yet
  everyone stays safe and laughs at the silly disaster.

This world is intentionally small and constraint-driven. It models:
- typed entities with physical meters and emotional memes
- a forward-chained causal engine
- a reasonableness gate
- an inline ASP twin
- prompt/story QA generation from world state
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
    owner: str = ""
    contents: list[str] = field(default_factory=list)
    fragile: bool = False
    messy: bool = False
    edible: bool = False
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
class Scene:
    id: str
    place: str
    backdrop: str
    surprise_item: str
    moral: str
    ending_image: str

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
class Ingredient:
    id: str
    label: str
    texture: str
    coarse: bool = False
    edible: bool = True

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
class Mistake:
    id: str
    label: str
    effect: str
    chaos: int
    reveal: str
    lesson: str

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
        clone.facts = dict(self.facts)
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    counter = world.entities.get("counter")
    if not bowl or not counter:
        return out
    if bowl.meters["tipped"] < THRESHOLD:
        return out
    sig = ("spill", bowl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["spilled"] += 1
    counter.meters["mess"] += 1
    out.append("__spill__")
    return out


def _r_crash(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("floor", Entity("floor")).meters["mess"] < THRESHOLD:
        return out
    for key in ("cookie", "frosting"):
        ent = world.entities.get(key)
        if not ent:
            continue
        sig = ("crash", key)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["ruined"] += 1
        out.append("__crash__")
    return out


def _r_embarrass(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("childA", Entity("x")).meters["mess"] < THRESHOLD:
        return out
    a = world.entities.get("childA")
    b = world.entities.get("childB")
    if a and a.memes["guilt"] >= THRESHOLD:
        sig = ("embarrass", a.id)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["embarrassment"] += 1
            out.append("__embarrass__")
    if b and b.memes["surprise"] >= THRESHOLD:
        sig = ("surprise", b.id)
        if sig not in world.fired:
            world.fired.add(sig)
            b.memes["surprise"] += 1
            out.append("__surprise__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("crash", "physical", _r_crash),
    Rule("embarrass", "social", _r_embarrass),
]


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


def reasonableness_ok(scene: Scene, ingredient: Ingredient, mistake: Mistake) -> bool:
    return ingredient.coarse and mistake.chaos >= 1 and scene.place == "kitchen"


def quiet_gate(ingredient: Ingredient) -> bool:
    return ingredient.edible


def predict_mess(world: World) -> dict:
    sim = world.copy()
    sim.get("bowl").meters["tipped"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("counter").meters["mess"],
        "ruined": sim.get("cookie").meters["ruined"],
    }


def start_story(world: World, a: Entity, b: Entity, scene: Scene, ingredient: Ingredient) -> None:
    world.say(
        f"On a busy afternoon, {a.id} and {b.id} turned the kitchen into a small "
        f"party. {scene.backdrop}"
    )
    world.say(
        f"They were making a surprise for {b.label_word} with {scene.surprise_item}. "
        f"{a.id} wanted it to look fancy, while {b.id} wanted it to stay secret."
    )
    world.say(
        f'"Let’s make it extra {ingredient.texture}," said {a.id}, grinning at the bowl.'
    )


def build_suspense(world: World, a: Entity, b: Entity, ingredient: Ingredient, mistake: Mistake) -> None:
    a.memes["excitement"] += 1
    b.memes["surprise"] += 1
    world.say(
        f"{b.id} peeked at the counter and froze. In the bowl was {ingredient.label}, "
        f"all {ingredient.texture} and funny-looking."
    )
    world.say(
        f'"Wait," {b.id} whispered, "is that supposed to be there?" '
        f'{a.id} just laughed and said it was part of the plan.'
    )
    world.say(
        f"That was the surprise: the treat would not stay smooth at all, and "
        f"{mistake.reveal} was about to happen."
    )


def do_mistake(world: World, a: Entity, b: Entity, ingredient: Ingredient, mistake: Mistake) -> None:
    bowl = world.get("bowl")
    bowl.meters["tipped"] += 1
    a.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the bowl wobbled, tipped, and went whoops -- straight over the counter."
    )
    world.say(
        f"{mistake.effect}. The kitchen got a little messy, and the secret got revealed at the worst possible time."
    )
    world.say(
        f'{b.id} stared, then burst out laughing because the whole thing was so silly.'
    )


def moral_value(world: World, parent: Entity, a: Entity, b: Entity, ingredient: Ingredient, mistake: Mistake) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say("For a moment, nobody moved.")
    world.say(
        f"Then {parent.label_word.capitalize()} came in, saw the mess, and sighed in a funny, not-scary way."
        f' "{mistake.lesson}," {parent.pronoun()} said. "And next time, tell me before the bowl turns into a disaster."'
    )
    world.say(
        f"{a.id} nodded and admitted the truth. {b.id} nodded too, because laughing at a mistake is easier when the truth is out."
    )


def bad_ending(world: World, scene: Scene, a: Entity, b: Entity, ingredient: Ingredient) -> None:
    world.say(
        f"They tried to save the surprise, but the cookie was already cracked, the frosting was a lopsided blob, and the coarse topping had gone everywhere."
    )
    world.say(
        f"In the end, the surprise was not a surprise anymore, and the treat looked like a tiny hill after a raccoon picnic."
    )
    world.say(
        f"Still, {a.id} and {b.id} wiped the counter together and promised to ask for help sooner."
    )
    world.say(scene.ending_image)


def tell(scene: Scene, ingredient: Ingredient, mistake: Mistake,
         child_a: str = "Milo", child_b: str = "Tess",
         child_a_type: str = "boy", child_b_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type=child_a_type, role="planner"))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_type, role="surprised"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="bowl", type="container", label="the bowl"))
    world.add(Entity(id="counter", type="place", label="the counter"))
    world.add(Entity(id="cookie", type="treat", label="the cookie", fragile=True, edible=True))
    world.add(Entity(id="frosting", type="topping", label="the frosting", fragile=True, messy=True))
    world.add(Entity(id="floor", type="place", label="the floor", messy=True))

    start_story(world, a, b, scene, ingredient)
    world.para()
    build_suspense(world, a, b, ingredient, mistake)
    world.para()
    do_mistake(world, a, b, ingredient, mistake)
    world.para()
    moral_value(world, parent, a, b, ingredient, mistake)
    world.para()
    bad_ending(world, scene, a, b, ingredient)

    world.facts.update(
        child_a=a, child_b=b, parent=parent, scene=scene, ingredient=ingredient, mistake=mistake,
        tipped=world.get("bowl").meters["tipped"] >= THRESHOLD,
        ruined=world.get("cookie").meters["ruined"] >= THRESHOLD,
    )
    return world


SCENES = {
    "kitchen": Scene(
        "kitchen",
        "the kitchen",
        "The table was covered with flour, a spoon rolled near the sink, and the oven hummed like a sleepy bee.",
        "a surprise cookie",
        "tell the truth, ask for help, and clean up early",
        "At the end, the cookie looked lumpy, the frosting slid sideways, and everyone laughed while wiping the counter.",
    ),
    "bakery": Scene(
        "bakery",
        "the little bakery room",
        "The shelves smelled sweet, paper liners waited in neat rows, and the mixing bowl looked as round as a moon.",
        "a surprise cake pop",
        "honesty makes a mess smaller",
        "At the end, the cake pop had fallen apart, but the crumbs made a funny smile on the tray.",
    ),
}

INGREDIENTS = {
    "coarse_sugar": Ingredient("coarse_sugar", "coarse sugar", "coarse", coarse=True),
    "coarse_salt": Ingredient("coarse_salt", "coarse salt", "coarse", coarse=True),
    "sprinkles": Ingredient("sprinkles", "sprinkles", "sparkly", coarse=False),
}

MISTAKES = {
    "spill": Mistake(
        "spill",
        "a spill",
        "the coarse topping slid all over the counter and into the frosting",
        2,
        "the frosting would slide right off",
        "It is better to tell the truth before a small mistake turns into a big one",
    ),
    "crack": Mistake(
        "crack",
        "a crack",
        "the cookie cracked like a tiny sidewalk",
        2,
        "the cookie would split apart",
        "If you need help, ask before the treat starts wobbling",
    ),
}

GIRL_NAMES = ["Tess", "Nina", "Maya", "Zoe", "Lena", "Ruby"]
BOY_NAMES = ["Milo", "Otto", "Finn", "Noah", "Theo", "Pip"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for iid, ing in INGREDIENTS.items():
            for mid, mistake in MISTAKES.items():
                if reasonableness_ok(scene, ing, mistake) and quiet_gate(ing):
                    combos.append((sid, iid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    ingredient: str
    mistake: str
    child_a: str
    child_a_type: str
    child_b: str
    child_b_type: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ing, scene, mistake = f["ingredient"], f["scene"], f["mistake"]
    a, b = f["child_a"], f["child_b"]
    return [
        f'Write a funny story for a 3-to-5-year-old about a kitchen surprise with "{ing.label}" and the word "coarse".',
        f"Tell a comedy story where {a.id} tries to make a surprise snack, but {b.id} notices the coarse topping and the plan goes wrong.",
        f'Write a short moral story where a child learns to tell the truth after a messy surprise in {scene.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent = f["child_a"], f["child_b"], f["parent"]
    ing, scene, mistake = f["ingredient"], f["scene"], f["mistake"]
    qa = [
        QAItem(
            question="What were the children making?",
            answer=f"They were making a surprise treat in {scene.place}, and they wanted it to be ready before {b.id} saw it. The idea was to make something special for their {parent.label_word}."
        ),
        QAItem(
            question="Why was the topping a problem?",
            answer=f"The topping was {ing.texture}, so it did not stay smooth. That made the treat wobble and helped the mistake happen."
        ),
        QAItem(
            question=f"What happened after the bowl tipped?",
            answer=f"The bowl spilled, the counter got messy, and the secret got revealed right away. It turned into a silly disaster instead of a neat surprise."
        ),
        QAItem(
            question="What moral did the parent teach?",
            answer=f"{mistake.lesson}. The parent wanted the children to tell the truth and ask for help sooner, because that makes cleanup and fixing problems easier."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly but in a funny way: the treat was ruined, the surprise was spoiled, and the children had to wipe up the mess. They were safe, and they learned from it."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ing = f["ingredient"]
    scene = f["scene"]
    return [
        QAItem(
            question="What does coarse mean?",
            answer="Coarse means rough, not smooth, or made of big little pieces that you can feel."
        ),
        QAItem(
            question=f"Why is a kitchen a busy place?",
            answer="A kitchen has counters, bowls, spoons, and food, so lots of little things can happen there at once."
        ),
        QAItem(
            question=f"What is a surprise?",
            answer="A surprise is something hidden or not told ahead of time, so it appears when someone least expects it."
        ),
        QAItem(
            question="Why should children ask for help when something starts to wobble?",
            answer="A grown-up can help stop a small problem before it becomes a bigger mess. Asking early is usually faster and safer."
        ),
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
        if e.fragile:
            bits.append("fragile")
        if e.messy:
            bits.append("messy")
        if e.edible:
            bits.append("edible")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "coarse_sugar", "spill", "Milo", "boy", "Tess", "girl", "mother"),
    StoryParams("kitchen", "coarse_salt", "crack", "Nina", "girl", "Pip", "boy", "father"),
]


def explain_rejection(scene: Scene, ingredient: Ingredient, mistake: Mistake) -> str:
    if scene.place != "kitchen":
        return "(No story: this world needs a kitchen so the comedy mess can spread across the counter.)"
    if not ingredient.coarse:
        return "(No story: the seed asks for coarse, but this ingredient is not coarse enough to cause the intended mishap.)"
    return "(No story: the chosen combination does not produce a believable surprise mess.)"


def outcome_of(params: StoryParams) -> str:
    return "bad"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("place", sid, "kitchen"))
    for iid, ing in INGREDIENTS.items():
        lines.append(asp.fact("ingredient", iid))
        if ing.coarse:
            lines.append(asp.fact("coarse", iid))
        if ing.edible:
            lines.append(asp.fact("edible", iid))
    for mid, m in MISTAKES.items():
        lines.append(asp.fact("mistake", mid))
        lines.append(asp.fact("chaos", mid, m.chaos))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, M) :- scene(S), ingredient(I), mistake(M), coarse(I), edible(I), chaos(M, C), C >= 1.
bad_ending :- valid(S, I, M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in python:", sorted(p - c))
        print("  only in clingo:", sorted(c - p))
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, ingredient=None, mistake=None, child_a=None, child_a_type=None, child_b=None, child_b_type=None, parent=None, seed=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with a coarse surprise and a bad ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--child-a")
    ap.add_argument("--child-a-type", choices=["boy", "girl"])
    ap.add_argument("--child-b")
    ap.add_argument("--child-b-type", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.scene is None or c[0] == args.scene)
              and (args.ingredient is None or c[1] == args.ingredient)
              and (args.mistake is None or c[2] == args.mistake)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, ingredient, mistake = rng.choice(sorted(combos))
    return StoryParams(
        scene=scene,
        ingredient=ingredient,
        mistake=mistake,
        child_a=args.child_a or rng.choice(GIRL_NAMES + BOY_NAMES),
        child_a_type=args.child_a_type or rng.choice(["boy", "girl"]),
        child_b=args.child_b or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != args.child_a]),
        child_b_type=args.child_b_type or rng.choice(["boy", "girl"]),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene],
        INGREDIENTS[params.ingredient],
        MISTAKES[params.mistake],
        params.child_a,
        params.child_b,
        params.child_a_type,
        params.child_b_type,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, i, m in combos:
            print(f"  {s:10} {i:14} {m}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a} and {p.child_b}: coarse surprise in the {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
