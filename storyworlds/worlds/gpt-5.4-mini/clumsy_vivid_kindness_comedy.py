#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clumsy_vivid_kindness_comedy.py
===============================================================

A standalone story world about a clumsy, vivid little kindness-comedy:
a child tries to help, makes a mess, stays kind, and turns the mishap into a
funny, warm ending.

The domain is tiny on purpose:
- a helper child
- a friend or sibling with a small problem
- a fragile, colorful object or scene
- a kind act that goes a bit clumsy before it succeeds

The stories are state-driven: meters and memes change as the scene unfolds.
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
    phrase: str = ""
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
    tone: str
    mess_surface: str
    cleanup_surface: str

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
class Problem:
    id: str
    label: str
    vivid_thing: str
    need: str
    clumsy_risk: str
    help_verb: str
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
class KindMove:
    id: str
    label: str
    power: int
    style: str
    result: str
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
        return clone


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
    for e in list(world.entities.values()):
        if e.meters["spill"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "table" in world.entities:
            world.get("table").meters["mess"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["embarrassment"] += 1
        out.append("__spill__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.facts.get("helper")
    friend = world.facts.get("friend")
    if not helper or not friend:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["warmth"] += 1
    friend.memes["relief"] += 1
    out.append("__kind__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("kindness", "social", _r_kindness)]


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


def reasonableness_gate(problem: Problem, move: KindMove) -> bool:
    return problem.id in PROBLEMS and move.power >= 1


def predict(world: World, helper: Entity, problem: Problem) -> dict:
    sim = world.copy()
    _attempt_help(sim, sim.get(helper.id), problem, narrate=False)
    return {
        "spill": sim.get("tray").meters["spill"] >= THRESHOLD,
        "mess": sim.get("table").meters["mess"] if "table" in sim.entities else 0,
    }


def _attempt_help(world: World, helper: Entity, problem: Problem, narrate: bool = True) -> None:
    helper.meters["reach"] += 1
    helper.memes["kindness"] += 1
    target = world.get("tray")
    target.meters["spill"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, friend: Entity, setting: Setting, problem: Problem) -> None:
    child.memes["joy"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {friend.id} were in {setting.place}. "
        f"The whole place looked vivid, like a painting that had learned how to laugh."
    )
    world.say(
        f"{friend.id} had a small problem: {friend.pronoun('possessive')} {problem.label} needed help."
    )


def clumsy_try(world: World, child: Entity, problem: Problem) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f"{child.id} wanted to help right away, but {child.pronoun()} was clumsy in the funniest way. "
        f"{child.pronoun().capitalize()} leaned too far, waved too wide, and nearly bowed to the table."
    )
    world.say(
        f'"I can do it!" {child.id} said, and reached for the {problem.vivid_thing}.'
    )


def spill_event(world: World, child: Entity, problem: Problem) -> None:
    _attempt_help(world, child, problem)
    world.say(
        f"Oops. The {problem.vivid_thing} tipped, splashed, and made a shiny little mess."
    )
    world.say(
        f"The spill was not scary, just dramatic enough to make everyone blink twice."
    )


def comfort_and_fix(world: World, helper: Entity, friend: Entity, problem: Problem,
                    move: KindMove) -> None:
    helper.memes["kindness"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{helper.id} froze for a moment, then smiled and said, "
        f'"Sorry! Let me fix it with {move.label}."'
    )
    world.say(
        f"With {move.style}, {helper.id} cleaned the mess, steadied the {problem.label}, "
        f"and turned the tumble into a joke."
    )
    world.say(
        f"{friend.id} laughed too, because kindness had shown up wearing a slightly crooked hat."
    )


def ending(world: World, child: Entity, friend: Entity, setting: Setting, problem: Problem) -> None:
    world.say(
        f"In the end, the {setting.cleanup_surface} was tidy again, the vivid colors still glowed, "
        f"and {child.id} and {friend.id} sat side by side like two little heroes who had both learned something."
    )
    world.say(
        f"{child.id} was still clumsy, but now everyone knew {child.pronoun()} could be clumsy, kind, and helpful all at once."
    )


def tell(setting: Setting, problem: Problem, move: KindMove,
         child_name: str = "Mia", child_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy",
         parent_name: str = "Mom") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="helper"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent"))
    tray = world.add(Entity(id="tray", label=problem.label, phrase=problem.vivid_thing))
    table = world.add(Entity(id="table", label=setting.mess_surface))
    world.facts["helper"] = child
    world.facts["friend"] = friend
    world.facts["parent"] = parent
    world.facts["problem"] = problem
    world.facts["move"] = move
    world.facts["setting"] = setting

    setup(world, child, friend, setting, problem)
    world.para()
    clumsy_try(world, child, problem)
    spill_event(world, child, problem)
    world.para()
    comfort_and_fix(world, child, friend, problem, move)
    world.para()
    ending(world, child, friend, setting, problem)
    world.facts["resolved"] = True
    world.facts["spill"] = tray.meters["spill"] >= THRESHOLD
    return world


SETTINGS = {
    "art_room": Setting("art_room", "the art room", "bright and funny", "table", "table"),
    "kitchen": Setting("kitchen", "the kitchen", "warm and busy", "counter", "counter"),
    "classroom": Setting("classroom", "the classroom", "neat but cheerful", "desk", "desk"),
}

PROBLEMS = {
    "paint": Problem("paint", "paint cup", "vivid paint cup", "help put the colors away", "paint all over the table", "wipe"),
    "juice": Problem("juice", "juice box", "vivid juice box", "carry it to the sink", "juice on the cloth", "wipe"),
    "sprinkles": Problem("sprinkles", "sprinkle bowl", "vivid sprinkle bowl", "bring it to the party tray", "sprinkles on the floor", "sweep"),
}

MOVES = {
    "napkins": KindMove("napkins", "paper napkins", 2, "with quick, careful swipes", "the mess vanished", {"wipe"}),
    "cloth": KindMove("cloth", "a soft cloth", 2, "with gentle circles", "the shine came back", {"wipe"}),
    "broom": KindMove("broom", "a broom", 2, "with careful little pushes", "the floor looked happy again", {"sweep"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Leo", "Max", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for mid in MOVES:
                combos.append((sid, pid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    move: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
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
    ap = argparse.ArgumentParser(description="A clumsy, vivid kindness-comedy story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, move = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != child])
    return StoryParams(setting, problem, move, child, child_gender, friend, friend_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a young child that includes the word "clumsy" and the word "vivid".',
        f"Tell a kind, funny story where {f['helper'].id} tries to help with {f['problem'].label} and makes a small mess before fixing it.",
        f"Write a cheerful story about kindness, a little accident, and a happy ending in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["helper"]
    friend = f["friend"]
    problem = f["problem"]
    move = f["move"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}. {child.id} tries to help, and {friend.id} is the one who needs help at first."),
        ("What made the story funny?",
         f"{child.id} was clumsy in a harmless way, so the help turned into a little spill before it turned into a fix. That mistake made the story silly instead of scary."),
        ("How did they solve the problem?",
         f"They used {move.label} and cleaned up the mess together. The kind act mattered as much as the cleaning, because it helped {friend.id} feel better."),
        ("How did the story end?",
         f"It ended with the place tidy again in {setting.place}, and both children smiling. The vivid colors stayed, but the mess did not."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["move"].tags)
    out = []
    if "wipe" in tags:
        out.append(("What does it mean to wipe something?",
                     "To wipe something is to clean it by rubbing it with a cloth, napkin, or paper towel."))
    if "sweep" in tags:
        out.append(("What does a broom do?",
                     "A broom is used to sweep dirt or little bits off the floor."))
    out.append(("What is kindness?",
                 "Kindness means being gentle, helpful, and caring to someone else, especially when they make a mistake."))
    out.append(("What does vivid mean?",
                 "Vivid means bright, strong, and easy to see, like colors that seem to pop off the page."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
spill(T) :- spill_meter(T, V), V >= 1.
kindness(H) :- kindness_meter(H, V), V >= 1.
resolved(H, F) :- kindness(H), friend(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("power", mid, m.power))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, move=None, child=None, child_gender=None, friend=None, friend_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], MOVES[params.move],
                 params.child, params.child_gender, params.friend, params.friend_gender)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c, child="Mia", child_gender="girl", friend="Noah", friend_gender="boy")) for c in [
            ("art_room", "paint", "napkins"),
            ("kitchen", "juice", "cloth"),
            ("classroom", "sprinkles", "broom"),
        ]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
