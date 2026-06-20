#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/digestion_incessant_lesson_learned_rhyme_adventure.py
======================================================================================

A standalone storyworld for a tiny adventure about a child, an incessant tummy
rumble, and a lesson learned at the end. The world is built as a small physical
and emotional simulation: a child goes on a make-believe adventure, eats the
wrong thing, gets persistent tummy troubles, asks a helper for the right remedy,
and ends with a clear change in state and a closing rhyme.

This world supports the Storyweavers contract:
- typed entities with meters and memes
- a reasonableness gate
- an inline ASP twin
- three QA sets grounded in the simulated world
- default, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    place: str
    vibe: str
    path: str
    dusk: str

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
class Food:
    id: str
    label: str
    phrase: str
    digestion: int
    nuisance: int
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
class Aid:
    id: str
    label: str
    phrase: str
    relief: int
    calm: int
    rhyme: str
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
    setting: Setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_rumble(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child or child.meters["rumbling"] < THRESHOLD:
        return out
    sig = ("rumble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    out.append("__rumble__")
    return out


def _r_incessant(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child or child.meters["rumbling"] < 2 * THRESHOLD:
        return out
    sig = ("incessant",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__incessant__")
    return out


CAUSAL_RULES = [Rule("rumble", "physical", _r_rumble), Rule("incessant", "physical", _r_incessant)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid, food in FOODS.items():
            for aid, aidv in AIDS.items():
                if food.digestion >= 1 and aidv.relief >= 1:
                    combos.append((sid, fid, aid))
    return combos


def reasonableness_gate(food: Food, aid: Aid) -> bool:
    return food.digestion >= 1 and aid.relief >= 1


def severity(food: Food, delay: int) -> int:
    return food.nuisance + delay


def can_contain(aid: Aid, food: Food, delay: int) -> bool:
    return aid.relief >= severity(food, delay)


def _tell_rhyme(world: World, child: Entity, helper: Entity, aid: Aid) -> None:
    world.say(f'"{aid.rhyme}" {helper.id} said with a grin.')


def tell(setting: Setting, food: Food, aid: Aid, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="adventurer"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    child.memes["curiosity"] = 1.0
    helper.memes["kindness"] = 1.0

    world.say(
        f"On {setting.place}, {child.id} began a little adventure along {setting.path}. "
        f"{setting.vibe}"
    )
    world.say(
        f"{child.id} had packed {food.phrase}, hoping it would help keep the journey lively."
    )

    world.para()
    world.say(
        f"But by {setting.dusk}, {child.id}'s tummy started to {food.label}. "
        f"It was {food.label} with an {food.label} feeling, and the rumble was incessant."
    )
    child.meters["rumbling"] += 1 + food.digestion
    propagate(world, narrate=False)
    child.memes["fear"] += 1

    world.para()
    world.say(
        f"{helper.id} heard the complaint and came over at once. "
        f'"Let\'s choose the calm path," {helper.id} said.'
    )
    if can_contain(aid, food, delay):
        child.meters["rumbling"] = 0.0
        child.memes["fear"] = 0.0
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        world.say(
            f"{helper.id} gave {child.id} {aid.phrase}, and the tummy trouble eased."
        )
        _tell_rhyme(world, child, helper, aid)
        world.say(
            f"Before long, {child.id} could walk again, lighter and smiling, "
            f"with {aid.label} in hand and the adventure back on track."
        )
    else:
        child.meters["rumbling"] += 1
        child.memes["fear"] += 1
        world.say(
            f"{helper.id} tried to help, but the tummy kept rumbling too hard at first."
        )
        world.say(
            f"So they sat together, breathed slowly, and waited until the feeling passed."
        )
        world.say(
            f"Even then, {child.id} learned that the safest adventure is the one that "
            f"listens to the body."
        )

    world.para()
    world.say(
        f"In the end, {child.id} said, 'Lesson learned: when digestion feels incessant, "
        f"ask for help and choose the gentle thing.'"
    )
    world.say(
        f"{setting.place} looked bright again, and the little adventurer took the next step "
        f"with a calmer tummy and a wiser heart."
    )

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        food=food,
        aid=aid,
        delay=delay,
        outcome="calm" if can_contain(aid, food, delay) else "slow",
        lesson=child.memes["lesson"] >= THRESHOLD,
        soothed=child.meters["rumbling"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "forest": Setting("forest", "the forest trail", "The trees arched overhead like friendly giants.", "a winding path", "evening"),
    "harbor": Setting("harbor", "the harbor dock", "The waves tapped the posts like sleepy fingers.", "a boardwalk", "sunset"),
    "hill": Setting("hill", "the hill road", "The grass rolled away in green waves.", "a long path", "late afternoon"),
}

FOODS = {
    "spicy_berries": Food("spicy_berries", "spicy berries", "a pocket of spicy berries", 2, 1, {"food", "digest"}),
    "greasy_pie": Food("greasy_pie", "greasy pie", "a slice of greasy pie", 3, 2, {"food", "digest"}),
    "sour_stew": Food("sour_stew", "sour stew", "a bowl of sour stew", 2, 2, {"food", "digest"}),
}

AIDS = {
    "warm_tea": Aid("warm_tea", "warm tea", "warm tea", 2, 2, "A warm cup, a calm stop, and the rumble will drop.", {"help", "calm"}),
    "plain_bread": Aid("plain_bread", "plain bread", "plain bread", 1, 1, "A plain bite, a steady pace, and the tummy finds grace.", {"help", "calm"}),
    "rest": Aid("rest", "a rest", "a quiet rest on a blanket", 1, 3, "Rest and hush, then breathe and wait; the tummy need not race.", {"help", "calm"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Leo", "Max", "Sam"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    food: str
    aid: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story for a young child about {f['child'].id} on {f['setting'].place} who eats {f['food'].phrase} and gets an incessant tummy rumble.",
        f"Tell a gentle adventure where {f['child'].id} learns a lesson about digestion, gets help from {f['helper'].id}, and ends with a rhyme.",
        "Write a story that includes the words digestion and incessant, with a brave but careful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, food, aid = f["child"], f["helper"], f["food"], f["aid"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, who went on a small adventure and had a tummy problem. {helper.id} came to help, and that changed the ending."),
        ("What problem did {child} have?".replace("{child}", child.id), f"{child.id} had an incessant tummy rumble after eating {food.phrase}. The trouble came from digestion feeling rough on the journey."),
        ("How did the helper help?", f"{helper.id} gave {child.id} {aid.phrase} and a calm plan. That eased the rumble and helped {child.pronoun()} feel better."),
    ]
    if f["lesson"]:
        qa.append((
            "What lesson did the child learn?",
            "The child learned to listen to the body and ask for help when digestion feels wrong. The story ends with a wiser choice and a steadier step."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is digestion?", "Digestion is what your body does to break food down after you eat it, so you can use it for energy."),
        ("What does incessant mean?", "Incessant means something keeps going and does not stop for a long time."),
        ("Why can a tummy ache be important?", "A tummy ache can be a sign that the body needs rest, gentle food, or a grown-up's help."),
        ("What helps a stomach feel better sometimes?", "Rest, water, and gentle food can help, and sometimes a child should ask a grown-up."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "greasy_pie", "warm_tea", "Mina", "girl", "Grandma", "woman", 0),
    StoryParams("harbor", "sour_stew", "rest", "Theo", "boy", "Dad", "man", 0),
    StoryParams("hill", "spicy_berries", "plain_bread", "Lily", "girl", "Mom", "woman", 0),
]


def explain_rejection(food: Food, aid: Aid) -> str:
    return f"(No story: {food.label} and {aid.label} do not make a sensible lesson-learned adventure.)"


def outcome_of(params: StoryParams) -> str:
    return "calm" if can_contain(AIDS[params.aid], FOODS[params.food], params.delay) else "slow"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("digestion", fid, f.digestion))
        lines.append(asp.fact("nuisance", fid, f.nuisance))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("relief", aid, a.relief))
        lines.append(asp.fact("calm", aid, a.calm))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,F,A) :- setting(S), food(F), aid(A), digestion(F,D), D >= 1, relief(A,R), R >= 1.
calm_outcome(F,A,D) :- digestion(F,FD), nuisance(F,N), relief(A,R), N + D =< R.
outcome(calm) :- chosen_food(F), chosen_aid(A), delay(D), calm_outcome(F,A,D).
outcome(slow) :- chosen_food(F), chosen_aid(A), delay(D), not calm_outcome(F,A,D).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_food", params.food), asp.fact("chosen_aid", params.aid), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        print("FAIL: smoke story empty")
        return 1
    if outcome_of(CURATED[0]) != asp_outcome(CURATED[0]):
        rc = 1
        print("MISMATCH in outcome.")
    print("OK: smoke generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: digestion, incessant, lesson learned, rhyme, adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.food and args.aid and not reasonableness_gate(FOODS[args.food], AIDS[args.aid]):
        raise StoryError(explain_rejection(FOODS[args.food], AIDS[args.aid]))
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting)
              and (args.food is None or c[1] == args.food)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, food, aid = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(["Aunt June", "Grandma", "Dad", "Mom", "Uncle Ray"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, food, aid, child_name, child_gender, helper_name, helper_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FOODS[params.food], AIDS[params.aid],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, f, a in combos:
            print(f"  {s:8} {f:12} {a}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.food} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
