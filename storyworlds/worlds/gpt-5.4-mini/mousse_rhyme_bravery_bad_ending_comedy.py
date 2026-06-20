#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mousse_rhyme_bravery_bad_ending_comedy.py
=========================================================================

A standalone storyworld about a child, a mousse dessert, a rhyming dare, and a
brave-but-bad comedy ending. The model simulates a tiny kitchen contest: a child
tries to make a fancy mousse for a family game, keeps speaking in rhyme to feel
braver, and pushes ahead despite warnings. The result is funny, messy, and a bit
sad: the dessert collapses, the floor gets slippery, and the ending proves that
bravery without care can still lead to a bad outcome.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- world state drives prose
- story, prompts, story-grounded QA, and world-knowledge QA
- Python reasonableness gate plus inline ASP twin
- --verify checks parity and smoke-tests generation
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    caretaker: str = ""
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
class Setting:
    id: str
    label: str
    mood: str
    place_detail: str

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
class Ingredient:
    id: str
    label: str
    phrase: str
    rhymes_with: str
    spillable: bool = True
    sweet: bool = True
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
    rhyme: str
    risk: str
    comedy: str
    power: int
    sense: int
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
        return clone

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    floor = world.entities.get("floor")
    if bowl is None or floor is None:
        return out
    if bowl.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor.meters["slippery"] += 1
    world.get("kid").memes["embarrassment"] += 1
    out.append("__spill__")
    return out


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    floor = world.entities.get("floor")
    apron = world.entities.get("apron")
    if floor is None:
        return out
    if floor.meters["slippery"] < THRESHOLD:
        return out
    if apron is not None and apron.meters["dirty"] < THRESHOLD:
        sig = ("smear",)
        if sig not in world.fired:
            world.fired.add(sig)
            apron.meters["dirty"] += 1
            out.append("The apron got a sticky little moustache of mousse.")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("smear", "physical", _r_smear),
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


def reasonable(action: Action, ingredient: Ingredient) -> bool:
    return action.sense >= SENSE_MIN and ingredient.spillable and action.power >= 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for aid, action in ACTIONS.items():
        for iid, ing in INGREDIENTS.items():
            if reasonable(action, ing):
                combos.append((aid, iid))
    return combos


def choose_name(rng: random.Random) -> tuple[str, str]:
    girl = ["Mia", "Lily", "Zoe", "Nora", "Ava"]
    boy = ["Leo", "Max", "Theo", "Finn", "Ben"]
    gender = rng.choice(["girl", "boy"])
    return (rng.choice(girl if gender == "girl" else boy), gender)


def rhyme_line(a: str, b: str, c: str) -> str:
    return f"{a} and {b} in a whirl, with {c} that twirls."


def predict_badness(world: World, ingredient_id: str) -> dict:
    sim = world.copy()
    _make_mousse(sim, narrate=False)
    return {
        "spilled": sim.get("bowl").meters["spilled"] >= THRESHOLD,
        "slippery": sim.get("floor").meters["slippery"] >= THRESHOLD,
        "embarrassed": sim.get("kid").memes["embarrassment"] >= THRESHOLD,
    }


def _make_mousse(world: World, narrate: bool = True) -> None:
    kid = world.get("kid")
    bowl = world.get("bowl")
    spoon = world.get("spoon")
    whisk = world.get("whisk")
    kid.memes["bravery"] += 1
    bowl.meters["spilled"] += 1
    spoon.meters["sticky"] += 1
    whisk.meters["sticky"] += 1
    propagate(world, narrate=narrate)


def opener(world: World, kid: Entity, helper: Entity, action: Action, ingredient: Ingredient) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"At {world.setting.label}, {kid.id} found a whisk and a bowl and wanted to make {ingredient.label} mousse."
    )
    world.say(
        f"{helper.id} smiled and said, \"A mousse with a groove?\" {kid.id} laughed. "
        f'"{action.rhyme}," {kid.id} sang, as if bravery were a song.'
    )


def warn(world: World, helper: Entity, kid: Entity, ingredient: Ingredient) -> None:
    pred = predict_badness(world, ingredient.id)
    helper.memes["caution"] += 1
    world.facts["pred"] = pred
    world.say(
        f"{helper.id} peered at the cream. \"That bowl looks too full for the move,\" {helper.pronoun()} warned. "
        f"\"A mousse made fast can make a mess; it may land on the floor and make a slip, I guess.\""
    )


def defy(world: World, kid: Entity, action: Action) -> None:
    kid.memes["defiance"] += 1
    world.say(
        f"{kid.id} puffed {kid.pronoun('possessive')} chest. \"I can do it! I'm bold!\" "
        f"{kid.pronoun().capitalize()} kept the beat and would not fold."
    )
    world.say(f"Then {kid.id} tried to {action.verb}, bravely and quick, like a comic-stick trick.")


def spill_world(world: World, ingredient: Ingredient) -> None:
    _make_mousse(world)
    world.say(
        f"The bowl tipped. Plop! The mousse flew slop. It slithered down the counter and would not stop."
    )
    world.say(
        f"Sweet cream swished on the floor, and the kitchen wore a silly white beard and more."
    )


def rescue_fail(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.id} hurried in with paper towels, but the mousse had already taken a stroll. "
        f"The towels got sticky, the shoes got shiny, and the whole kitchen looked tiny."
    )


def bad_ending(world: World, kid: Entity, helper: Entity, ingredient: Ingredient) -> None:
    kid.memes["embarrassment"] += 1
    helper.memes["sympathy"] += 1
    world.say(
        f"For a moment they both stood still, one sticky shoe, one wobble, one spill."
    )
    world.say(
        f"{helper.id} sighed, then chuckled softly. \"Brave rhymes are fine, but a careful line is loftier.\""
    )
    world.say(
        f"{kid.id} stared at the ruined mousse. No dessert parade, no sweet round prize, just a funny white puddle and surprised eyes."
    )


def ending_image(world: World) -> None:
    world.say(
        "The last thing the kitchen remembered was a floor with a slippery shine, a whisk in a sugar beard, and one brave child learning that bold is better with time."
    )


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "bright and busy", "A timer ticked by the sink."),
    "bakery": Setting("bakery", "the bakery corner", "warm and bustling", "A tray of cups waited nearby."),
}

INGREDIENTS = {
    "mousse": Ingredient("mousse", "mousse", "a bowl of chocolate mousse", "goose", True, True, {"sweet"}),
    "cream": Ingredient("cream", "cream", "a bowl of whipped cream", "dream", True, True, {"sweet"}),
    "berries": Ingredient("berries", "berries", "a bowl of berries", "fairies", True, True, {"sweet"}),
}

ACTIONS = {
    "whip": Action("whip", "whip it up", "zip-zap flip-flip", "spill the sweet cloud", "comedy", 2, 3, {"rhyming"}),
    "stir": Action("stir", "stir it fast", "whirr and whirl", "slosh the bowl", "comedy", 1, 2, {"rhyming"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    ingredient: str
    action: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
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


KNOWLEDGE = {
    "mousse": [("What is mousse?", "Mousse is a soft, fluffy dessert. It is light and airy, and people often eat it with a spoon.")],
    "whisk": [("What does a whisk do?", "A whisk is a kitchen tool with loops of wire. It helps mix and fluff ingredients together.")],
    "cream": [("What is whipped cream?", "Whipped cream is cream that has been beaten until it is light and fluffy.")],
    "slippery": [("Why is a slippery floor dangerous?", "A slippery floor can make someone slide or fall, so people should clean spills right away.")],
    "bravery": [("What is bravery?", "Bravery means doing something even when you feel nervous. It is good when you also stay careful.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like day and play.")],
}
KNOWLEDGE_ORDER = ["mousse", "whisk", "cream", "slippery", "bravery", "rhyme"]


def tell(setting: Setting, ingredient: Ingredient, action: Action, kid_name: str, kid_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    kid = world.add(Entity("kid", "character", kid_gender, role="hero", traits=["brave", "rhyming"]))
    kid.id = kid_name
    helper = world.add(Entity("helper", "character", helper_gender, role="helper", traits=["careful"]))
    helper.id = helper_name
    bowl = world.add(Entity("bowl", label="bowl"))
    spoon = world.add(Entity("spoon", label="spoon"))
    whisk = world.add(Entity("whisk", label="whisk"))
    floor = world.add(Entity("floor", label="floor"))
    apron = world.add(Entity("apron", label="apron", caretaker=helper_name))
    world.add(Entity("mousse", label=ingredient.label))
    opener(world, kid, helper, action, ingredient)
    world.para()
    warn(world, helper, kid, ingredient)
    defy(world, kid, action)
    world.para()
    spill_world(world, ingredient)
    rescue_fail(world, helper)
    world.para()
    bad_ending(world, kid, helper, ingredient)
    ending_image(world)
    world.facts.update(
        kid=kid, helper=helper, bowl=bowl, spoon=spoon, whisk=whisk, floor=floor, apron=apron,
        ingredient=ingredient, action=action, setting=setting,
        pred=world.facts.get("pred", {}),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid, helper, ing, action = f["kid"], f["helper"], f["ingredient"], f["action"]
    return [
        f'Write a comedic story for a young child that includes the word "{ing.label}" and has a rhyming child who acts bravely.',
        f"Tell a funny kitchen story where {kid.id} tries to {action.verb} a mousse dessert, keeps speaking in rhyme, and things go wrong in a silly way.",
        f'Write a short story about bravery that ends badly, but in a humorous way, and includes "{ing.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, helper, ing, action = f["kid"], f["helper"], f["ingredient"], f["action"]
    return [
        QAItem("Who is the story about?", f"It is about {kid.id} and {helper.id} in the kitchen, with {kid.id} trying to make {ing.label}."),
        QAItem("What did the child want to do?", f"{kid.id} wanted to {action.verb}, and {kid.id} kept saying things in rhyme to feel brave."),
        QAItem("Why did the story end badly?", f"The mousse spilled out of the bowl and made the floor slippery. That made the dessert ruined and turned the ending into a funny mess."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["ingredient"].id, "bravery", "rhyme", "slippery"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
    return out


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "mousse", "whip", "Mia", "girl", "Nora", "girl"),
    StoryParams("bakery", "cream", "stir", "Leo", "boy", "Max", "boy"),
]


def explain_rejection(action: Action, ingredient: Ingredient) -> str:
    if not reasonable(action, ingredient):
        return "(No story: this combination is too weak for the comic-bravery mousse setup.)"
    return "(No story: invalid combination.)"


def valid_story_params() -> list[tuple[str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(A, I) :- action(A), ingredient(I), sense(A, S), sense_min(M), S >= M, spillable(I).
outcome(bad) :- chosen_action(A), chosen_ingredient(I), action_power(A, P), P >= 1, ingredient(I), spillable(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INGREDIENTS:
        lines.append(asp.fact("ingredient", iid))
        lines.append(asp.fact("spillable", iid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("action_power", aid, a.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_story_params())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in asp:", sorted(a - b))
        print("  only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, ingredient=None, action=None, kid=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic mousse story world with rhyme, bravery, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--kid")
    ap.add_argument("--helper")
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
              if (args.setting is None or True)
              and (args.ingredient is None or c[1] == args.ingredient)
              and (args.action is None or c[0] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    action_id, ingredient_id = rng.choice(sorted(combos))
    kid_name, kid_gender = choose_name(rng)
    helper_name, helper_gender = choose_name(rng)
    while helper_name == kid_name:
        helper_name, helper_gender = choose_name(rng)
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        ingredient=ingredient_id,
        action=action_id,
        kid_name=args.kid or kid_name,
        kid_gender="girl" if kid_gender == "girl" else "boy",
        helper_name=args.helper or helper_name,
        helper_gender="girl" if helper_gender == "girl" else "boy",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], INGREDIENTS[params.ingredient], ACTIONS[params.action],
                 params.kid_name, params.kid_gender, params.helper_name, params.helper_gender)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (action, ingredient) combos:")
        for action, ingredient in asp_valid_combos():
            print(f"  {action:8} {ingredient}")
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
