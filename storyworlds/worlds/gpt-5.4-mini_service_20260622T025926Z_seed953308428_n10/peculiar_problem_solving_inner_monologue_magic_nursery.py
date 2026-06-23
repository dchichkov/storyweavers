#!/usr/bin/env python3
"""
storyworlds/worlds/peculiar_problem_solving_inner_monologue_magic_nursery.py
===========================================================================

A small nursery-rhyme storyworld about a child, a peculiar little problem, and
a magical, sensible fix.

The seed premise:
- Something peculiar goes wrong in a nursery-like room.
- The child thinks aloud, notices the snag, and solves it with a small spell.
- The ending shows what changed in the room.

This script keeps a compact world model with typed entities, physical meters,
emotional memes, a simple predictive check, QA grounded in the simulated state,
and an ASP twin for parity checking.
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Luna", "Tilly", "Poppy", "Nora", "Elly"]
BOY_NAMES = ["Theo", "Rory", "Milo", "Benny", "Ollie", "Finn"]
TRAITS = ["tiny", "brave", "curious", "gentle", "cheery"]
MAGIC_WORDS = ["twinkle", "bibbity", "lullaby", "sparkle", "hush"]
PROBLEMS = {
    "stuck_stars": ("a row of star garlands", "stuck to the curtain rod", "stuck"),
    "sleepy_toys": ("a pile of sleepy toys", "stuck in a high basket", "stuck"),
    "lost_ribbon": ("a ribbon loop", "caught on the chair", "caught"),
    "tiptoeing_lamp": ("a little lamp", "tilting on a shelf", "tilting"),
}
TOOLS = {
    "wand": ("a tiny wand", {"sparkle"}),
    "bell": ("a silver bell", {"hush"}),
    "glove": ("a soft mitten-glove", {"twinkle"}),
    "kite_string": ("a spool of kite string", {"bibbity"}),
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    target: str = ""
    fix_word: str = ""
    safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    problem: str
    room_word: str
    mood: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child_name: str
    child_gender: str
    parent_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.history = list(self.history)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    item = world.entities.get("item")
    if not child or not item:
        return out
    if child.meters["magic"] < THRESHOLD:
        return out
    sig = ("settle", item.id)
    if sig in world.fired:
        return out
    if item.meters["problem"] >= THRESHOLD:
        world.fired.add(sig)
        item.meters["problem"] = 0.0
        item.meters["tidy"] += 1
        child.memes["joy"] += 1
        out.append("__fixed__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _r_settle(world)
        if sents:
            changed = True
            produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_at_risk(problem_key: str) -> bool:
    return problem_key in PROBLEMS


def select_tool(problem_key: str, tool_key: str) -> bool:
    return tool_key in TOOLS and problem_key in PROBLEMS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for problem in PROBLEMS:
            for tool in TOOLS:
                if select_tool(problem, tool):
                    combos.append((setting, problem, tool))
    return combos


def predict_fix(world: World, child: Entity, item: Entity, tool: Entity) -> bool:
    sim = world.copy()
    sim.get("child").meters["magic"] += 1
    sim.get("item").meters["problem"] += 1
    propagate(sim, narrate=False)
    return sim.get("item").meters["problem"] < THRESHOLD


def speak_inner(world: World, child: Entity, item: Entity, tool: Entity) -> None:
    world.say(
        f"{child.id} looked and thought, “What a peculiar thing this is.” "
        f"“If I use {tool.phrase}, maybe I can help {item.label}.”"
    )


def setup(world: World, child: Entity, parent: Entity, item: Entity, tool: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Under {world.setting.name}, {child.id} woke to a peculiar sight: "
        f"{item.phrase} {world.setting.problem}."
    )
    world.say(
        f"{child.id}'s {parent.label} was nearby, and the room felt soft and "
        f"{world.setting.mood}."
    )
    world.say(
        f"{child.id} liked {tool.label} because it was small, bright, and just right "
        f"for a careful fix."
    )


def problem_beats(world: World, child: Entity, item: Entity) -> None:
    child.memes["worry"] += 1
    item.meters["problem"] += 1
    world.say(
        f"The little trouble would not budge. {item.label.capitalize()} stayed "
        f"{world.setting.problem}, and the day grew a bit too still."
    )


def cast_spell(world: World, child: Entity, tool: Entity, item: Entity) -> None:
    word = tool.fix_word
    child.meters["magic"] += 1
    child.memes["courage"] += 1
    world.say(
        f'{child.id} whispered "{word}, {word}," and gave the {tool.label} a gentle wave.'
    )
    propagate(world, narrate=False)
    if item.meters["problem"] < THRESHOLD:
        world.say(
            f"A soft twinkle danced through the room, and {item.label} slipped free '
            f"at last."
        )


def ending(world: World, child: Entity, parent: Entity, item: Entity, tool: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{parent.label.capitalize()} smiled, and {child.id} smiled back. "
        f"Now {item.label} was neat and near, and the {tool.label} lay quiet as a feather."
    )


SETTINGS = {
    "nursery": Setting(name="the nursery", problem="was tucked up on a high shelf", room_word="nursery", mood="gentle"),
    "playroom": Setting(name="the playroom", problem="was tangled by the window", room_word="playroom", mood="sunny"),
    "bedroom": Setting(name="the bedroom", problem="was hanging from the lamp", room_word="bedroom", mood="dreamy"),
}

PROBLEM_FX = {
    "stuck_stars": "stuck on the curtain rod",
    "sleepy_toys": "stuck in a high basket",
    "lost_ribbon": "caught on the chair",
    "tiptoeing_lamp": "tilting on a shelf",
}

TOOLS = {
    "wand": Entity(id="wand", type="thing", label="wand", phrase="a tiny wand", fix_word="twinkle", safe=True, tags={"magic", "twinkle"}),
    "bell": Entity(id="bell", type="thing", label="bell", phrase="a silver bell", fix_word="hush", safe=True, tags={"magic", "hush"}),
    "glove": Entity(id="glove", type="thing", label="mitten-glove", phrase="a soft mitten-glove", fix_word="sparkle", safe=True, tags={"magic", "sparkle"}),
    "kite_string": Entity(id="kite_string", type="thing", label="spool of string", phrase="a spool of kite string", fix_word="bibbity", safe=True, tags={"magic", "bibbity"}),
}

PROBLEMS = {
    "stuck_stars": Entity(id="item", type="thing", label="the star garland", phrase="a row of star garlands", target="stuck", meters=defaultdict(float), memes=defaultdict(float), tags={"stars", "stuck"}),
    "sleepy_toys": Entity(id="item", type="thing", label="the toy basket", phrase="a pile of sleepy toys", target="stuck", meters=defaultdict(float), memes=defaultdict(float), tags={"toys", "stuck"}),
    "lost_ribbon": Entity(id="item", type="thing", label="the ribbon", phrase="a ribbon loop", target="caught", meters=defaultdict(float), memes=defaultdict(float), tags={"ribbon", "caught"}),
    "tiptoeing_lamp": Entity(id="item", type="thing", label="the lamp", phrase="a little lamp", target="tilting", meters=defaultdict(float), memes=defaultdict(float), tags={"lamp", "tilting"}),
}

GIRL_NAMES = GIRL_NAMES
BOY_NAMES = BOY_NAMES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: peculiar, magical problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.problem and args.tool and not select_tool(args.problem, args.tool):
        raise StoryError("That tool cannot solve that problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, tool=tool, child_name=name, child_gender=gender, parent_name=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child", attrs={"trait": params.trait}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_name, label=params.parent_name, role="parent"))
    item = world.add(Entity(id="item", type="thing", label=PROBLEMS[params.problem].label, phrase=PROBLEMS[params.problem].phrase, tags=PROBLEMS[params.problem].tags))
    tool = world.add(TOOLS[params.tool])
    world.facts.update(child=child, parent=parent, item=item, tool=tool, params=params, setting=setting)
    setup(world, child, parent, item, tool)
    world.para()
    speak_inner(world, child, item, tool)
    problem_beats(world, child, item)
    world.para()
    cast_spell(world, child, tool, item)
    ending(world, child, parent, item, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]  # type: ignore[assignment]
    return [
        f'Write a nursery-rhyme story that uses the word "peculiar" and shows {p.child_name} solving a small problem with magic.',
        f"Tell a gentle story where {p.child_name} thinks aloud, notices a strange problem in {world.setting.name}, and uses {p.tool} to fix it.",
        f'Write a short child-friendly rhyme about a peculiar room problem, inner monologue, and a magical fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    tool: Entity = f["tool"]  # type: ignore[assignment]
    p: StoryParams = f["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was peculiar in {world.setting.name}?",
            answer=f"There was {item.phrase} {world.setting.problem}. It looked peculiar because it would not stay put until {child.id} helped.",
        ),
        QAItem(
            question=f"What did {child.id} think could help with {item.label}?",
            answer=f"{child.id} thought {tool.phrase} might help. In the inner monologue, {child.id} decided to try a small magic word and a gentle wave.",
        ),
        QAItem(
            question=f"How did {child.id} solve the problem in the end?",
            answer=f"{child.id} whispered '{tool.fix_word}, {tool.fix_word}' and used {tool.label}. The magic settled the trouble, so {item.label} ended neat and near.",
        ),
        QAItem(
            question=f"Who smiled when the room was fixed?",
            answer=f"{parent.label.capitalize()} smiled, and {child.id} smiled too. The ending image shows the room calm again and the tool quiet at the side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Entity = f["tool"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    qas = []
    if "magic" in tool.tags:
        qas.append(QAItem(question=f"What is {tool.label} for in this story world?", answer=f"It is a small magical helper for gentle fixing. It helps a child nudge a stuck or tricky thing back into place without rough pulling."))
    if "stuck" in item.tags or "caught" in item.tags or "tilting" in item.tags:
        qas.append(QAItem(question="What does it mean when something is stuck?", answer="It means it cannot move the way it should. A careful helper may need a small idea, a good tool, or a gentle twist to set it right."))
    qas.append(QAItem(question="What does an inner monologue do in a story?", answer="It lets the character think quietly to themselves. Readers can hear the idea forming before the character acts."))
    return qas


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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS:
        raise StoryError("Invalid StoryParams.")
    world = make_world(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind}/{e.type}) meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)} tags={sorted(e.tags)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), can_solve(P,T).
can_solve(P,T) :- problem(P), tool(T), solution(P,T).
solution(stuck_stars, wand).
solution(stuck_stars, kite_string).
solution(sleepy_toys, bell).
solution(lost_ribbon, kite_string).
solution(tiptoeing_lamp, glove).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for p, t in [("stuck_stars", "wand"), ("stuck_stars", "kite_string"), ("sleepy_toys", "bell"), ("lost_ribbon", "kite_string"), ("tiptoeing_lamp", "glove")]:
        lines.append(asp.fact("solution", p, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        ok = False
        print("MISMATCH between ASP and Python valid_combos().")
        print("only in asp:", sorted(cl - py))
        print("only in python:", sorted(py - cl))
    # smoke tests
    try:
        default = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not default.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generation smoke test")
        for s in (1, 7, 42):
            args = build_parser().parse_args(["--seed", str(s)])
            p = resolve_params(args, random.Random(s))
            sample = generate(p)
            if not sample.story.strip():
                raise RuntimeError("empty story")
        print("OK: resolve/generate smoke tests for seeds 1, 7, 42")
        multi = [generate(resolve_params(build_parser().parse_args(["-n", "3", "--seed", "777", "--qa"]), random.Random(777 + i))) for i in range(3)]
        if any(len(s.story_qa) == 0 or len(s.world_qa) == 0 for s in multi):
            raise RuntimeError("QA missing")
        print("OK: -n 3 --seed 777 --qa smoke test")
        j = json.loads(generate(resolve_params(build_parser().parse_args(["--seed", "9"]), random.Random(9))).to_json())
        if "story" not in j:
            raise RuntimeError("bad json")
        print("OK: JSON smoke test")
        if len(valid_combos()) <= 20:
            _ = [generate(StoryParams(setting=s, problem=p, tool=t, child_name="Mina", child_gender="girl", parent_name="mother", trait="curious")) for s, p, t in valid_combos()]
            print("OK: --all-equivalent curated generation smoke test")
        # emit smoke
        emit(default, trace=False, qa=False)
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return 0 if ok else 1


def build_curated() -> list[StoryParams]:
    combos = valid_combos()
    if not combos:
        return []
    out = []
    for i, (s, p, t) in enumerate(combos[:5]):
        out.append(StoryParams(setting=s, problem=p, tool=t, child_name=GIRL_NAMES[i % len(GIRL_NAMES)], child_gender="girl" if i % 2 == 0 else "boy", parent_name="mother", trait=TRAITS[i % len(TRAITS)]))
    return out


def resolve_params_from_seed(args: argparse.Namespace, seed: int) -> StoryParams:
    rng = random.Random(seed)
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in build_curated() or [StoryParams(setting=s, problem=p, tool=t, child_name="Mina", child_gender="girl", parent_name="mother", trait="curious") for s, p, t in valid_combos()]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params_from_seed(args, seed)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
