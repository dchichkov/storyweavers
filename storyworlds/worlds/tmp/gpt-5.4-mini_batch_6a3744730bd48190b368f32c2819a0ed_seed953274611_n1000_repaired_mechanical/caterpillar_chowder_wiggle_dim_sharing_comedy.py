#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caterpillar_chowder_wiggle_dim_sharing_comedy.py
=================================================================================

A tiny story world built from the seed words:
- caterpillar
- chowder
- wiggle-dim

The domain is a small comedy about sharing a bowl of chowder with a hungry
caterpillar, where the "wiggle-dim" is a ridiculous pretend measurement that
matters because it changes who can reach the bowl, how much gets spilled, and
whether the characters end up sharing happily.

The simulation is deliberately small, concrete, and state-driven:
- characters and objects have physical meters and emotional memes;
- a caterpillar's hunger and wiggle-dim drive the tension;
- sharing a bowl can either go smoothly, require a helper, or get messy;
- the ending image proves what changed.

This script follows the Storyweavers contract:
- standalone stdlib Python
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- --verify checks ASP/Python parity and runs a normal generation smoke test
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Setting:
    id: str
    place: str
    detail: str
    bowl_name: str
    support_name: str
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
class Recipe:
    id: str
    flavor: str
    steam: str
    spoonful: str
    spill_kind: str
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
class CaterpillarConfig:
    id: str
    name: str
    type: str = "caterpillar"
    hungry: float = 2.0
    wiggle_dim: int = 1
    traits: list[str] = field(default_factory=list)
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
class HumanConfig:
    id: str
    name: str
    type: str
    patience: float = 2.0
    traits: list[str] = field(default_factory=list)
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
class StoryParams:
    setting: str
    recipe: str
    caterpillar: str
    sharing: str
    helper: str
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


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_hunger(world: World) -> list[str]:
    out = []
    cat = world.get("cat")
    bowl = world.get("bowl")
    if cat.meters["hunger"] >= THRESHOLD and bowl.meters["full"] >= THRESHOLD:
        sig = ("hunger",)
        if sig not in world.fired:
            world.fired.add(sig)
            cat.memes["want"] += 1
            out.append("__want__")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    bowl = world.get("bowl")
    if bowl.meters["spill"] >= THRESHOLD and "floor" in world.entities:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("floor").meters["mess"] += 1
            for e in list(world.entities.values()):
                if e.kind == "character":
                    e.memes["surprise"] += 1
            out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("hunger", _r_hunger), Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, recipe in RECIPES.items():
            if recipe.spill_kind == "splash":
                combos.append((sid, rid, "cat"))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.recipe not in RECIPES:
        raise StoryError("Unknown chowder recipe.")
    if params.caterpillar not in CATERPILLARS:
        raise StoryError("Unknown caterpillar.")
    if params.sharing not in SHARING_MOVES:
        raise StoryError("Unknown sharing move.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.helper == "none" and params.sharing == "ladle":
        raise StoryError("The sharing move needs a helper in this tiny comedy.")
    if params.caterpillar == "giant" and params.sharing == "small_spoon":
        raise StoryError("A giant caterpillar cannot share from a tiny spoon here.")


def setup_scene(world: World, setting: Setting, recipe: Recipe, cat_cfg: CaterpillarConfig,
                helper_cfg: HumanConfig, share_move: str) -> None:
    cat = world.add(Entity(id="cat", kind="character", type="caterpillar",
                           label=cat_cfg.name, traits=cat_cfg.traits))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type,
                              label=helper_cfg.name, traits=helper_cfg.traits))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label=setting.bowl_name))
    floor = world.add(Entity(id="floor", kind="thing", type="floor", label="the floor"))
    spoon = world.add(Entity(id="spoon", kind="thing", type="spoon", label=share_move))
    world.facts.update(setting=setting, recipe=recipe, cat_cfg=cat_cfg, helper_cfg=helper_cfg,
                       share_move=share_move)
    cat.meters["hunger"] = cat_cfg.hungry
    cat.memes["hope"] = 1.0
    cat.memes["glee"] = 0.0
    helper.memes["patience"] = helper_cfg.patience
    bowl.meters["full"] = 1.0
    bowl.meters["spill"] = 0.0
    bowl.meters["shared"] = 0.0
    floor.meters["mess"] = 0.0
    world.say(
        f"In {setting.place}, {cat_cfg.name} the caterpillar found {setting.detail} "
        f"and a bowl of {recipe.flavor} chowder."
    )
    world.say(
        f'{helper_cfg.name} laughed and said, "This is a sharing day, not a snatching day."'
    )


def ask_for_share(world: World, cat: Entity, helper: Entity, recipe: Recipe, share_move: str) -> None:
    cat.memes["want"] += 1
    world.say(
        f'{cat.label_word} wiggled in place. "I want some chowder," {cat.pronoun()} said, '
        f'and {cat.pronoun("possessive")} wiggle-dim was {cat.meters["wiggle_dim"]}.'
    )
    if cat.meters["wiggle_dim"] > 1:
        world.say(
            f"That many wiggle-dims made {cat.label_word} bump the table once and wobble twice."
        )
    else:
        world.say(
            f"{cat.label_word} could reach the bowl only with a careful little lean."
        )


def share_attempt(world: World, cat: Entity, helper: Entity, recipe: Recipe, share_move: str) -> None:
    bowl = world.get("bowl")
    cat.memes["sharing"] += 1
    world.say(
        f'{helper.label_word} slid the {share_move} over and said, "We can share one spoonful at a time."'
    )
    if cat.meters["wiggle_dim"] > 1:
        bowl.meters["spill"] += 1
        world.say(
            f"The caterpillar did a dramatic wiggle-dim and the spoon made a little splat."
        )
    bowl.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{cat.label_word} slurped the first spoonful of {recipe.flavor} chowder."
    )


def ending(world: World, cat: Entity, helper: Entity, recipe: Recipe, share_move: str) -> None:
    bowl = world.get("bowl")
    floor = world.get("floor")
    if bowl.meters["spill"] >= THRESHOLD:
        world.say(
            f"Everyone paused, then laughed when a single drop of chowder slid down the bowl like a tiny comet."
        )
        world.say(
            f"{helper.label_word} wiped the spot, and {cat.label_word} politely held the spoon still."
        )
    cat.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the end, the bowl was shared, the joke was shared, and even the floor had only a tiny mess."
    )
    world.say(
        f"{cat.label_word} sat proudly beside the half-empty bowl of chowder, wobbling like a champion."
    )
    world.facts["floor_mess"] = floor.meters["mess"]


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", detail="a warm counter by the sink",
                       bowl_name="the big bowl", support_name="the table"),
    "porch": Setting(id="porch", place="the porch", detail="sunlight on a little round table",
                     bowl_name="the blue bowl", support_name="the porch rail"),
    "picnic": Setting(id="picnic", place="the picnic table", detail="a checkered cloth and a breezy bench",
                      bowl_name="the picnic bowl", support_name="the table"),
}

RECIPES = {
    "clam": Recipe(id="clam", flavor="clam", steam="steamy", spoonful="slurp", spill_kind="splash",
                   tags={"chowder"}),
    "corn": Recipe(id="corn", flavor="corn", steam="golden", spoonful="sip", spill_kind="splash",
                   tags={"chowder"}),
    "potato": Recipe(id="potato", flavor="potato", steam="thick", spoonful="glop", spill_kind="splash",
                     tags={"chowder"}),
}

CATERPILLARS = {
    "small": CaterpillarConfig(id="small", name="Milo", hungry=2.0, wiggle_dim=1, traits=["polite", "hungry"]),
    "bouncy": CaterpillarConfig(id="bouncy", name="Pip", hungry=2.0, wiggle_dim=2, traits=["bouncy", "comic"]),
    "giant": CaterpillarConfig(id="giant", name="Nibs", hungry=3.0, wiggle_dim=3, traits=["grand", "silly"]),
}

HELPERS = {
    "kid": HumanConfig(id="kid", name="Junie", type="girl", patience=2.0, traits=["kind", "laughing"]),
    "parent": HumanConfig(id="parent", name="Dad", type="father", patience=3.0, traits=["patient", "dry"]),
    "neighbor": HumanConfig(id="neighbor", name="Mira", type="girl", patience=2.5, traits=["friendly", "practical"]),
}

SHARING_MOVES = {
    "ladle": "the ladle",
    "spoon": "the spoon",
    "tiny_bowl": "the tiny bowl",
}

CURATED = [
    StoryParams(setting="kitchen", recipe="clam", caterpillar="small", sharing="ladle", helper="parent"),
    StoryParams(setting="porch", recipe="corn", caterpillar="bouncy", sharing="spoon", helper="kid"),
    StoryParams(setting="picnic", recipe="potato", caterpillar="giant", sharing="tiny_bowl", helper="neighbor"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about sharing chowder with a caterpillar.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--caterpillar", choices=CATERPILLARS)
    ap.add_argument("--sharing", choices=SHARING_MOVES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.recipe and args.recipe not in RECIPES:
        raise StoryError("Unknown recipe.")
    if args.caterpillar and args.caterpillar not in CATERPILLARS:
        raise StoryError("Unknown caterpillar.")
    if args.sharing and args.sharing not in SHARING_MOVES:
        raise StoryError("Unknown sharing move.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.recipe:
        combos = [c for c in combos if c[1] == args.recipe]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, recipe, cat_key = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        recipe=recipe,
        caterpillar=args.caterpillar or cat_key,
        sharing=args.sharing or rng.choice(list(SHARING_MOVES)),
        helper=args.helper or rng.choice(list(HELPERS)),
    )


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World()
    setup_scene(world, SETTINGS[params.setting], RECIPES[params.recipe],
                CATERPILLARS[params.caterpillar], HELPERS[params.helper],
                SHARING_MOVES[params.sharing])
    cat = world.get("cat")
    helper = world.get("helper")
    recipe = RECIPES[params.recipe]
    world.para()
    ask_for_share(world, cat, helper, recipe, SHARING_MOVES[params.sharing])
    share_attempt(world, cat, helper, recipe, SHARING_MOVES[params.sharing])
    world.para()
    ending(world, cat, helper, recipe, SHARING_MOVES[params.sharing])
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cat = f["cat_cfg"]
    setting = f["setting"]
    recipe = f["recipe"]
    return [
        f'Write a funny sharing story for a young child that includes the words "caterpillar", "chowder", and "wiggle-dim".',
        f"Tell a comedy about {cat.name} the caterpillar who wants {recipe.flavor} chowder in {setting.place} and learns to share.",
        f"Write a short, cheerful story where a hungry caterpillar and a helper share chowder without becoming mean about it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cat = f["cat_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting"]
    recipe = f["recipe"]
    return [
        ("Who is the story about?",
         f"It is about {cat.name} the caterpillar and {helper.name}. They are trying to share chowder in {setting.place}."),
        ("What did the caterpillar want?",
         f"{cat.name} wanted some {recipe.flavor} chowder. The caterpillar was hungry and kept wiggling toward the bowl."),
        ("Why was this a comedy and not a tragedy?",
         f"Because the problem was small and silly, not scary. The wiggle-dim caused a comic splash, and everyone ended up sharing and laughing."),
        ("How did they solve the problem?",
         f"They used {SHARING_MOVES[f['share_move']]} and took turns. That let the caterpillar eat without grabbing everything at once."),
        ("How did the story end?",
         f"It ended with the bowl shared and only a tiny mess on the floor. The final image shows the caterpillar proudly beside the chowder instead of fighting over it."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a caterpillar?",
         "A caterpillar is a little crawling insect with many legs. It wiggles and munches as it grows."),
        ("What is chowder?",
         "Chowder is a thick soup, often served warm in a bowl. People usually eat it with a spoon or ladle."),
        ("What is wiggle-dim?",
         "Wiggle-dim is a silly pretend measurement for how much a caterpillar wiggles. In this story it is funny because it changes how awkward the sharing becomes."),
        ("What does sharing mean?",
         "Sharing means letting someone else have some of the same thing too. It is a kind way to take turns or split a treat."),
    ]


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:6} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, setting.place))
    for rid in RECIPES:
        lines.append(asp.fact("recipe", rid))
    for cid in CATERPILLARS:
        lines.append(asp.fact("caterpillar", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for move in SHARING_MOVES:
        lines.append(asp.fact("share_move", move))
    lines.append(asp.fact("threshold", int(THRESHOLD)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R, C) :- setting(S), recipe(R), caterpillar(C).
shared(C) :- valid(_, _, C).
#show valid/3.
#show shared/1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set != python_set:
        print("MISMATCH in valid combos.")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        rc = 1
    else:
        print(f"OK: ASP parity for {len(clingo_set)} combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_story_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.setting} / {p.recipe} / {p.caterpillar}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
