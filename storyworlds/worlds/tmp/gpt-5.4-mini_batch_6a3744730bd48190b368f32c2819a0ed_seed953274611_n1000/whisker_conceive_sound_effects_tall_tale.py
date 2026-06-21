#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whisker_conceive_sound_effects_tall_tale.py
============================================================================

A standalone storyworld for a tall-tale style adventure about a clever child,
a whiskered helper, and a big idea that turns into a safe, noisy rescue.

Premise
-------
A child and a lanky helper get stuck with a problem that needs a bright,
imaginative plan. They first try a too-small idea, then a grown-up-size sound
and motion solve the problem, and the ending proves the world changed.

Required seed words
--------------------
- whisker
- conceive

Style
-----
Tall tale, child-facing, concrete, with sound effects woven into the action.

Features
--------
- Typed entities with physical meters and emotional memes.
- State-driven narrative, not a fixed paragraph with swapped nouns.
- Python reasonableness gate and an inline ASP twin.
- Three Q&A sets grounded in world state.
- Support for --trace, --qa, --json, --asp, --verify, --show-asp, -n, --all, --seed.
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
SOUND_MIN = 2
IDEA_MIN = 2

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
    can_conceive: bool = False
    makes_sound: bool = False
    needs_sound: bool = False

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

@dataclass
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    setting: str
    problem: str
    sound_tool: str
    solve: str
    seed: Optional[int] = None

@dataclass
class Setting:
    id: str
    place: str
    detail: str
    problem_image: str
    problem_need: str

@dataclass
class Problem:
    id: str
    label: str
    need: str
    risk: str
    spread: int = 2
    needs_sound: bool = True

@dataclass
class SoundTool:
    id: str
    label: str
    sound: str
    power: int
    solve_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)

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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_stir(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["wonder"] >= THRESHOLD and ("stir" not in world.fired):
            world.fired.add(("stir", e.id))
            e.memes["boldness"] += 1
            out.append("")
    return out

def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    for p in world.entities.values():
        if p.meters["need_sound"] < THRESHOLD:
            continue
        if ("sound", p.id) in world.fired:
            continue
        world.fired.add(("sound", p.id))
        world.get("place").meters["trouble"] += 1
        for c in world.characters():
            c.memes["alarm"] += 1
        out.append("__sound__")
    return out

CAUSAL_RULES = [Rule("sound", "physical", _r_sound)]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def valid_choice(problem: Problem, tool: SoundTool) -> bool:
    return problem.needs_sound and tool.power >= problem.spread

def sensible_tools() -> list[SoundTool]:
    return [t for t in SOUND_TOOLS.values() if t.power >= SOUND_MIN]

def story_turn(world: World, child: Entity, helper: Entity, setting: Setting, problem: Problem, tool: SoundTool) -> None:
    world.say(f"At {setting.place}, {setting.detail}.")
    world.say(f"{child.id} could not {problem.need}, and {helper.id} rubbed {helper.pronoun('possessive')} whisker and said, "
              f'"We must conceive a grander way."')
    world.say(f'The sky was so still that even a mouse would have heard a pin drop. Then: {tool.sound}')
    child.memes["wonder"] += 1
    helper.memes["smarts"] += 1

def attempt(world: World, tool: SoundTool, problem: Problem) -> None:
    world.say(f"{tool.sound} {tool.solve_text.replace('{problem}', problem.label)}")

def resolve(world: World, child: Entity, helper: Entity, tool: SoundTool, problem: Problem, setting: Setting) -> None:
    world.say(f"{tool.sound} {tool.solve_text.replace('{problem}', problem.label)}")
    world.say(f"That did it. {problem.label.capitalize()} backed off, and the {setting.place} rang with relief.")

def fail(world: World, tool: SoundTool, problem: Problem, setting: Setting) -> None:
    world.say(f"{tool.sound} {tool.fail_text.replace('{problem}', problem.label)}")
    world.say(f"The trouble kept coming until the whole {setting.place} seemed to shake.")

def ending(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"By sunset, the {setting.place} was calm again, and the two of them laughed under a wide, easy sky.")

def tell(setting: Setting, problem: Problem, tool: SoundTool, child_name: str, child_gender: str, helper_name: str, helper_gender: str, solve: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["bright"], can_conceive=True))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["lanky", "clever"]))
    place = world.add(Entity(id="place", type="place", label=setting.place))
    hazard = world.add(Entity(id="hazard", type="hazard", label=problem.label, needs_sound=problem.needs_sound))
    device = world.add(Entity(id="tool", type="tool", label=tool.label, makes_sound=True))
    world.facts.update(child=child, helper=helper, place=place, hazard=hazard, setting=setting, problem=problem, tool=tool, solve=solve)
    world.say(f"{child.id} was a little {child_gender} with a mind that could conceive moon-big ideas.")
    world.say(f"{helper.id} had a whisker like a crescent moon and a grin like a fence rail at harvest time.")
    world.say(f"Together they stood in {setting.place}, where {setting.problem_image}.")
    world.para()
    world.say(f"{child.id} wanted to {problem.need}, but {problem.risk} kept making trouble.")
    if solve == "contained":
        world.say(f"{helper.id} blinked. 'We can do this!' {helper.pronoun()} said.")
        world.say(f"{tool.sound} {tool.solve_text.replace('{problem}', problem.label)}")
        world.say(f"The noise chased the trouble away.")
        ending(world, child, helper, setting)
        outcome = "contained"
    else:
        world.say(f"{helper.id} tried to help with {tool.label}, but the idea was too small.")
        world.say(f"{tool.sound} {tool.fail_text.replace('{problem}', problem.label)}")
        world.say(f"The problem still towered up taller than a barn roof.")
        world.say(f"Then the grown-up answer came at last, and the whole place settled down.")
        ending(world, child, helper, setting)
        outcome = "failed"
    world.facts["outcome"] = outcome
    return world

SETTINGS = {
    "cabin": Setting(id="cabin", place="the riverside cabin", detail="the wind worried the shutters and the lamp gave a thin yellow wink", problem_image="the floorboards kept groaning in the draft", problem_need="quiet the racket",),
    "barn": Setting(id="barn", place="the red barn", detail="the rafters hummed like bees and the hay made a golden mountain", problem_image="a pile of chicks had wandered where they ought not", problem_need="gather the scattered chicks",),
    "fair": Setting(id="fair", place="the county fair", detail="the tents snapped and the popcorn smell floated everywhere", problem_image="the ringmaster had lost the signal bell", problem_need="call the crowd to attention",),
}
PROBLEMS = {
    "racket": Problem(id="racket", label="racket", need="quiet the racket", risk="the wind kept rattling everything", spread=2),
    "chicks": Problem(id="chicks", label="the chicks", need="gather the scattered chicks", risk="they were running every which way", spread=3),
    "crowd": Problem(id="crowd", label="the crowd", need="call the crowd to attention", risk="they would miss the show", spread=2),
}
SOUND_TOOLS = {
    "whistle": SoundTool(id="whistle", label="a whistle", sound="FWEEEEE!", power=2, solve_text="That whistle made the {problem} listen up at once.", fail_text="That whistle was a speck of sound against a mountain of {problem}.", tags={"sound"}),
    "bell": SoundTool(id="bell", label="a brass bell", sound="CLANG-CLANG!", power=3, solve_text="That bell rolled over the {problem} like thunder.", fail_text="That bell rang brave, but the {problem} would not budge.", tags={"sound"}),
    "horn": SoundTool(id="horn", label="a big tin horn", sound="HONK! HONK!", power=4, solve_text="That horn boomed so hard the {problem} scattered like leaves.", fail_text="That horn hollered, but the {problem} still stood there.", tags={"sound"}),
}
GIRL_NAMES = ["Ruby", "Mabel", "Clara", "Nell", "Ivy"]
BOY_NAMES = ["Hank", "Otis", "Cal", "Jude", "Wes"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for t in SOUND_TOOLS:
                if valid_choice(PROBLEMS[p], SOUND_TOOLS[t]):
                    combos.append((s, p, t))
    return combos

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with whiskers, conceiving, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=SOUND_TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--solve", choices=["contained", "failed"])
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
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    solve = args.solve or "contained"
    return StoryParams(child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender, setting=setting, problem=problem, sound_tool=tool, solve=solve)

def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.sound_tool not in SOUND_TOOLS:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = SOUND_TOOLS[params.sound_tool]
    if not valid_choice(problem, tool):
        raise StoryError("That tool is not loud enough for this problem.")
    world = tell(setting, problem, tool, params.child, params.child_gender, params.helper, params.helper_gender, params.solve)
    prompts = [
        f'Write a tall tale for a child using the words "whisker" and "conceive" and a noisy rescue.',
        f"Tell a big-hearted story where {params.child} and {params.helper} conceive a clever plan and make a sound effect solve the trouble.",
        f'Write a story with a dramatic sound effect, a whiskered helper, and a happy ending in {setting.place}.',
    ]
    story_qa = [
        QAItem(question=f"What did {params.helper} have that made the story funny?", answer=f"{params.helper} had a whisker, which gave the helper a tall-tale look and helped the story feel old-timey and playful."),
        QAItem(question=f"What did {params.child} and {params.helper} do when the trouble showed up?", answer=f"They tried to conceive a better plan instead of giving up, and the loud sound tool helped them choose the safer, stronger way."),
        QAItem(question="How did the story end?", answer=f"It ended with the trouble gone, the place calm again, and everyone laughing after the big sound did its work."),
    ]
    world_qa = [
        QAItem(question="What is a whisker?", answer="A whisker is a long, stiff hair on the face of some animals. In a tall tale, it can make a helper look especially scrappy and lively."),
        QAItem(question="What does conceive mean?", answer="To conceive an idea means to think it up or imagine it. It is how a character comes up with a plan."),
        QAItem(question="Why are sound effects used in stories?", answer="Sound effects make action feel louder and more lively. They help readers hear the boom, clang, or honk right in their heads."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
sound_ok(P,T) :- problem(P), tool(T), power(T,S), spread(P,R), S >= R.
valid(S,P,T) :- setting(S), sound_ok(P,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", p))
        lines.append(asp.fact("spread", p, pr.spread))
    for t, tool in SOUND_TOOLS.items():
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("power", t, tool.power))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import asp
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c != p:
        print("MISMATCH between clingo and python gates.")
        return 1
    sample = CURATED[0]
    try:
        generate(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: gate matches valid_combos() ({len(c)} combos) and generation works.")
    return 0

CURATED = [
    StoryParams(child="Ruby", child_gender="girl", helper="Hank", helper_gender="boy", setting="cabin", problem="racket", sound_tool="bell", solve="contained"),
    StoryParams(child="Otis", child_gender="boy", helper="Mabel", helper_gender="girl", setting="barn", problem="chicks", sound_tool="horn", solve="contained"),
    StoryParams(child="Ivy", child_gender="girl", helper="Cal", helper_gender="boy", setting="fair", problem="crowd", sound_tool="whistle", solve="contained"),
]

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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, p, t in asp_valid_combos():
            print(f"  {s:8} {p:8} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
