#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gristle_inter_prompt_transformation_foreshadowing_suspense_heartwarming.py
=============================================================================================================

A tiny heartwarming storyworld about a child helping in a kitchen, where an
unpleasant ingredient, a worrying wait, and a gentle prompt lead to a small
transformation.

The seed words are woven into the world model:
- gristle: a tough bit in a stew or soup that can worry the cook
- inter: an interruption / interval / intermission / in-between moment
- prompt: a gentle prompt to keep going or to ask for help

The style aims for warm, concrete, child-facing prose with foreshadowing and
suspense, but a reassuring ending image that proves what changed.
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
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    steam: str
    has_gristle: bool
    transform_to: str
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
class PromptTool:
    id: str
    label: str
    phrase: str
    gentle: str
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
class Setting:
    id: str
    place: str
    sound: str
    nook: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_wait(world: World) -> list[str]:
    out: list[str] = []
    pot = world.entities.get("pot")
    if not pot:
        return out
    if pot.meters["simmering"] < THRESHOLD:
        return out
    sig = ("wait",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for child in list(world.entities.values()):
        if child.role == "helper":
            child.memes["worry"] += 1
    out.append("__wait__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    dish = world.entities.get("dish")
    if not dish or dish.meters["soft"] >= THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    if dish.meters["gristle_removed"] < THRESHOLD:
        return out
    world.fired.add(sig)
    dish.meters["soft"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("wait", "suspense", _r_wait), Rule("transform", "physical", _r_transform)]


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


def predict_result(world: World, remove_gristle: bool) -> dict:
    sim = world.copy()
    if remove_gristle:
        sim.get("dish").meters["gristle_removed"] += 1
        propagate(sim, narrate=False)
    return {
        "soft": sim.get("dish").meters["soft"] >= THRESHOLD,
        "worry": sim.get("helper").memes["worry"],
    }


def simmer(world: World, setting: Setting, dish: Dish, cook: Entity, helper: Entity) -> None:
    world.say(
        f"At {setting.place}, {cook.id} set down {dish.phrase}. {dish.steam} drifted up from the pot."
    )
    world.say(
        f"{helper.id} stood beside {cook.id} in the little {setting.nook}, listening to the soft sound of the pot and the hush between spoon-stirs."
    )
    if dish.has_gristle:
        world.say(
            f"Then {helper.id} noticed one tough bit of gristle peeking through the broth, and {helper.id}'s face went still."
        )
    world.facts["foreshadow"] = setting.sound


def prompt(world: World, helper: Entity, cook: Entity, tool: PromptTool) -> None:
    helper.memes["hope"] += 1
    world.say(
        f'{helper.id} gave a gentle prompt: "{tool.phrase}, {cook.id}." {tool.gentle}'
    )


def suspense(world: World, dish: Dish) -> None:
    dish.meters["simmering"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The pot kept bubbling. For a tiny inter, nobody spoke, and the gristle bobbed at the top like a little knot."
    )


def remove_gristle(world: World, cook: Entity, dish: Dish) -> None:
    cook.memes["care"] += 1
    dish.meters["gristle_removed"] += 1
    world.say(
        f"{cook.id} smiled, reached in with a spoon, and lifted the gristle out so the soup could become tender and kind."
    )
    propagate(world, narrate=False)


def transform(world: World, cook: Entity, dish: Dish) -> None:
    dish.meters["served"] += 1
    world.say(
        f"The broth changed at last. The broth had looked nervous before, but now it shone warm and smooth."
    )
    world.say(
        f"{cook.id} ladled it into bowls, and the last spoonfuls no longer caught on anything tough."
    )


def ending(world: World, setting: Setting, dish: Dish, helper: Entity) -> None:
    helper.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the table, {helper.id} took a careful sip and grinned. The soup was softer now, and the little kitchen felt bright again."
    )
    world.say(
        f"Even the empty pot seemed to smile back from its place beside the sink."
    )


def tell(setting: Setting, dish: Dish, tool: PromptTool, cook_name: str = "Mina",
         helper_name: str = "Oli", cook_gender: str = "woman", helper_gender: str = "boy") -> World:
    world = World()
    cook = world.add(Entity(id=cook_name, kind="character", type=cook_gender, role="cook"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    pot = world.add(Entity(id="pot", type="thing", label="the pot"))
    thing = world.add(Entity(id="dish", type="thing", label=dish.label))
    world.facts["setting"] = setting
    world.facts["dish"] = dish
    world.facts["tool"] = tool
    world.facts["cook"] = cook
    world.facts["helper"] = helper
    world.facts["pot"] = pot
    simmer(world, setting, dish, cook, helper)
    world.para()
    prompt(world, helper, cook, tool)
    suspense(world, pot)
    if dish.has_gristle:
        world.para()
        remove_gristle(world, cook, thing)
        transform(world, cook, thing)
    else:
        world.para()
        world.say(
            f"{cook.id} listened, nodded, and kept stirring until the broth was smooth on its own."
        )
        thing.meters["soft"] += 1
        transform(world, cook, thing)
    world.para()
    ending(world, setting, thing, helper)
    world.facts["outcome"] = "transformed"
    world.facts["soft"] = thing.meters["soft"] >= THRESHOLD
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "soft bubbling", "little window nook", {"kitchen", "warm"}),
    "grandma": Setting("grandma", "Grandma's kitchen", "gentle clinks", "sunny corner", {"kitchen", "warm"}),
    "camp": Setting("camp", "the camp cabin kitchen", "quiet simmering", "wooden table nook", {"kitchen", "warm"}),
}

DISHES = {
    "stew": Dish("stew", "stew", "a pot of beef stew", "Steam curled from the lid.", True, "soft", {"stew", "gristle"}),
    "soup": Dish("soup", "soup", "a pot of chicken soup", "Steam floated in the air.", False, "soft", {"soup"}),
    "broth": Dish("broth", "broth", "a pot of broth", "Steam made a little cloud.", True, "soft", {"broth", "gristle"}),
}

PROMPTS = {
    "spoon": PromptTool("spoon", "spoon", "Maybe use a spoon.", "That would help the soup stay safe and warm.", {"prompt", "help"}),
    "knife": PromptTool("knife", "knife", "Use the knife carefully.", "The knife is for a grown-up hand here.", {"prompt", "careful"}),
    "sieve": PromptTool("sieve", "sieve", "Maybe strain it first.", "That could lift out the tough bits and keep the rest gentle.", {"prompt", "help"}),
}

NAMES = ["Mina", "Oli", "Nia", "Theo", "June", "Mara", "Pip", "Luca"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    dish: str
    prompt_tool: str
    cook: str
    cook_gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DISHES:
            for p in PROMPTS:
                if DISHES[d].has_gristle or p != "knife":
                    combos.append((s, d, p))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d: Dish = f["dish"]
    return [
        f'Write a heartwarming story that uses the words "gristle", "inter", and "prompt".',
        f"Tell a gentle suspense story about {f['helper'].id} helping {f['cook'].id} cook {d.label} and noticing a bit of gristle.",
        f"Write a cozy transformation story where a child gives a prompt, there is a tiny inter of suspense, and the meal becomes soft and good.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cook, helper, dish = f["cook"], f["helper"], f["dish"]
    return [
        QAItem("Who is the story about?", f"It is about {cook.id} and {helper.id} in the kitchen. They work together, and the child helps turn a worrisome moment into a kind one."),
        QAItem("What worried the helper?", f"{helper.id} noticed a bit of gristle in the pot. That made the cooking feel suspenseful for a moment, because the food was not tender yet."),
        QAItem("What happened after the prompt?", f"{helper.id} gave a gentle prompt, and {cook.id} listened. After a tiny inter of waiting, the gristle came out and the soup changed into something soft and warm."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is gristle?", "Gristle is a tough, chewy bit you can find in some meat. People often take it out or cook until the food becomes tender."),
        QAItem("What does prompt mean?", "To prompt someone is to gently nudge or remind them to do something. A prompt can be a kind little hint."),
        QAItem("What is suspense?", "Suspense is the feeling of wondering what will happen next. It can make a story feel tense for a moment."),
        QAItem("What does transform mean?", "To transform means to change into something else. Food can transform when it becomes softer, warmer, or easier to eat."),
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "stew", "spoon", "Mina", "woman", "Oli", "boy"),
    StoryParams("grandma", "broth", "sieve", "Nia", "girl", "Theo", "boy"),
    StoryParams("camp", "soup", "spoon", "Mara", "woman", "Pip", "boy"),
]


def explain_rejection(dish: Dish, tool: PromptTool) -> str:
    if not dish.has_gristle:
        return f"(No story: {dish.label} has no gristle here, so there is no real suspense to build or transformation to show.)"
    return f"(No story: the chosen prompt tool cannot support this gentle kitchen problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming kitchen storyworld with gristle, inter, and prompt.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--prompt-tool", choices=PROMPTS)
    ap.add_argument("--cook")
    ap.add_argument("--helper")
    ap.add_argument("--cook-gender", choices=["woman", "girl", "man", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "girl", "man", "boy"])
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
    if args.dish and args.prompt_tool:
        if not DISHES[args.dish].has_gristle and args.prompt_tool == "knife":
            raise StoryError(explain_rejection(DISHES[args.dish], PROMPTS[args.prompt_tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.dish is None or c[1] == args.dish)
              and (args.prompt_tool is None or c[2] == args.prompt_tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, dish, prompt_tool = rng.choice(sorted(combos))
    cook = args.cook or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != cook])
    cook_gender = args.cook_gender or rng.choice(["woman", "girl", "man", "boy"])
    helper_gender = args.helper_gender or rng.choice(["boy", "girl"])
    return StoryParams(setting, dish, prompt_tool, cook, cook_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DISHES[params.dish], PROMPTS[params.prompt_tool],
                 params.cook, params.helper, params.cook_gender, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
valid(S, D, P) :- setting(S), dish(D), prompt(P), has_gristle(D), not bad_combo(D, P).
bad_combo(D, knife) :- dish(D), not has_gristle(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DISHES.items():
        lines.append(asp.fact("dish", did))
        if d.has_gristle:
            lines.append(asp.fact("has_gristle", did))
    for pid in PROMPTS:
        lines.append(asp.fact("prompt", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
