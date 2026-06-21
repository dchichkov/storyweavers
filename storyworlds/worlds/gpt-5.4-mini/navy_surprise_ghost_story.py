#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/navy_surprise_ghost_story.py
============================================================

A small standalone storyworld for a child-facing ghost-story style tale with a
navy clue and a surprise turn.

Premise
-------
A child in navy pajamas hears spooky sounds while helping prepare a surprise.
The dark and the rustles feel ghostly, but the story turns on a friendly reveal:
the "ghost" is only a surprise setup, and the child learns to call for help and
look more carefully.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-chained rule engine, a reasonableness gate, Q&A from world state, and an
inline ASP twin for parity checks.
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
SCARED_MIN = 1.0


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
class Setting:
    id: str
    place: str
    dark_spot: str
    sound: str
    surprise_place: str
    atmosphere: str

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
class SpookyClue:
    id: str
    label: str
    sound: str
    clue_place: str
    harmless: bool = True

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
class SurprisePlan:
    id: str
    kind: str
    hide_place: str
    reveal: str
    gift: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_scared(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["unease"] < THRESHOLD:
        return out
    sig = ("scared",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["alert"] += 1
    out.append("__scared__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    plan = world.get("plan")
    if child.memes["alert"] < THRESHOLD or plan.meters["hidden"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plan.meters["hidden"] = 0.0
    plan.meters["revealed"] = 1.0
    out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("scared", "social", _r_scared), Rule("reveal", "plot", _r_reveal)]


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


def clue_is_ghostly(clue: SpookyClue) -> bool:
    return clue.harmless


def plan_is_reasonable(plan: SurprisePlan, clue: SpookyClue) -> bool:
    return plan.kind == "surprise" and clue_is_ghostly(clue)


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    plan: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


SETTINGS = {
    "attic": Setting("attic", "the attic", "the dark attic corner", "a thump", "the old trunk", "creaky and cold"),
    "hall": Setting("hall", "the hallway", "the dark hallway end", "a tap-tap", "the coat rack", "long and shadowy"),
    "bedroom": Setting("bedroom", "the bedroom", "the closet door", "a rustle", "the pillow pile", "small and moonlit"),
}

CLUES = {
    "sheet": SpookyClue("sheet", "a white sheet", "a soft flapping sound", "the old trunk", harmless=True),
    "ribbon": SpookyClue("ribbon", "a ribbon", "a whispery swish", "the pillow pile", harmless=True),
    "toy": SpookyClue("toy", "a navy toy whale", "a bump against the wall", "the coat rack", harmless=True),
}

PLANS = {
    "surprise": SurprisePlan("surprise", "surprise", "the old trunk", "a birthday surprise", "a navy ribboned box"),
    "gift": SurprisePlan("gift", "surprise", "the pillow pile", "a hidden gift", "a tiny lantern"),
}

NAMES_GIRL = ["Mia", "Nora", "Lily", "Ava", "Rose"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Eli", "Max"]
HELPERS = ["mom", "dad", "grandma", "grandpa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for pid, plan in PLANS.items():
                if plan_is_reasonable(plan, clue):
                    combos.append((sid, cid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story style navy surprise world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    if args.clue and args.plan:
        if not plan_is_reasonable(PLANS[args.plan], CLUES[args.clue]):
            raise StoryError("That clue and plan do not make a reasonable ghost-story surprise.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, plan = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting, clue, plan, name, gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    plan = PLANS[params.plan]
    world = World(setting)
    child = world.add(Entity("child", "character", params.child_gender, label=params.child_name, role="child"))
    helper = world.add(Entity("helper", "character", params.helper_gender, label=params.helper_name, role="helper"))
    clue_ent = world.add(Entity("clue", "thing", "thing", label=clue.label))
    plan_ent = world.add(Entity("plan", "thing", "thing", label=plan.kind))
    child.memes["curiosity"] = 1.0
    world.say(f"At {setting.place}, {child.label} wore navy pajamas and listened to the house breathe.")
    world.say(f"{setting.atmosphere.capitalize()} air curled around {setting.dark_spot}, and a {clue.sound} came from {clue.clue_place}.")
    world.say(f"{child.label} hugged {child.pronoun('possessive')} navy blanket and whispered, 'Is there a ghost in there?'")
    world.para()
    child.meters["unease"] += 1
    propagate(world, narrate=False)
    world.say(f"{helper.label.capitalize()} smiled and said it was only {clue.label}, part of a {plan.reveal}.")
    world.say(f"Still, {child.label} tiptoed closer, and the shadows seemed to wiggle like sleepy ghosts.")
    world.para()
    if child.memes["alert"] >= THRESHOLD:
        world.say(f"Then the surprise was revealed: from {plan.hide_place} came {plan.gift}, and everyone laughed with relief.")
        world.say(f"{child.label} blinked, then grinned, because the spooky noise had been only a kind surprise all along.")
    else:
        world.say(f"The surprise waited quietly, and the room stayed still and moonlit.")
    child.memes["calm"] += 1
    clue_ent.meters["seen"] = 1.0
    plan_ent.meters["hidden"] = 0.0
    world.facts.update(child=child, helper=helper, clue=clue_ent, plan=plan_ent, setting=setting, params=params)
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
    return [
        f'Write a ghost-story style tale with the word "navy" and a surprise reveal for {f["child"].label}.',
        f"Tell a spooky-but-gentle story where {f['child'].label} thinks a sound in {f['setting'].place} is a ghost, but it turns out to be a surprise.",
        f"Write a child-friendly ghost story with navy pajamas, a dark room, and a happy surprise at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, h, s = f["child"], f["helper"], f["setting"]
    return [
        ("Who is the story about?", f"It is about {c.label}, who was in {s.place} with {h.label}. The dark place and the surprise sound made the story feel ghostly."),
        ("What did {0} think the sound was?".format(c.label), f"{c.label} thought the sound might be a ghost. It was really a harmless clue for a surprise."),
        ("How did the story end?", f"It ended with a happy surprise, because the spooky noise was only part of the plan. {c.label} felt calm and laughed once the surprise was revealed."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does navy mean?", "Navy is a dark blue color. People often use it for clothes, blankets, and toys."),
        ("Why can a dark room feel spooky?", "Dark rooms hide shapes and shadows, so ordinary things can seem strange. That is why a little sound can feel ghostly at first."),
        ("What is a surprise?", "A surprise is something that is hidden for a little while and then shown. It can make someone gasp, smile, or laugh."),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.kind:9}) meters={meters} memes={memes} label={e.label!r}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_good(S,C,P) :- setting(S), clue(C), plan(P), harmless(C), surprise_plan(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.harmless:
            lines.append(asp.fact("harmless", cid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("surprise_plan", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_good/3."))
    return sorted(set(asp.atoms(model, "reasonably_good")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, plan=None, name=None, gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
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


CURATED = [
    StoryParams("attic", "sheet", "surprise", "Mia", "girl", "mom", "woman"),
    StoryParams("hall", "toy", "gift", "Leo", "boy", "dad", "man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonably_good/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
