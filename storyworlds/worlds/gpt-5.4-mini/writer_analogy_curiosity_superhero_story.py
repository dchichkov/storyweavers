#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/writer_analogy_curiosity_superhero_story.py
===========================================================================

A standalone story world for a child-facing superhero story about a writer,
curiosity, and the power of analogy.

Core premise:
- A young writer-hero gets curious about a mysterious sound or hidden clue.
- They almost rush into a risky choice, but a guide figure warns them.
- They use a safe, clever tool or method to investigate instead.
- Their curiosity becomes a strength, not a problem, and the ending proves
  what changed in the world: a solved problem, a written page, and a brighter,
  safer feeling.

The world is intentionally small and classical:
- typed entities with meters (physical) and memes (emotional)
- a forward-chained causal model
- a reasonableness gate
- a declarative ASP twin
- state-driven prose and three Q&A sets
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
CURIOUS_MIN = 2
HELPFUL_MIN = 2


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
    label: str
    place: str
    hidden_spot: str
    danger_word: str
    mood: str

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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = True

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
class Problem:
    id: str
    label: str
    phrase: str
    risky: bool = True

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
class Analogy:
    id: str
    setup: str
    mapping: str
    payoff: str

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


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("anxiety", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["buzz"] += 1
        out.append("")
    return out


def _r_discovery(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("used_analogy") and not world.facts.get("problem_fixed"):
        sig = ("discovery",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["problem_fixed"] = True
        out.append("__discover__")
    return out


CAUSAL_RULES = [Rule("anxiety", "social", _r_anxiety), Rule("discovery", "social", _r_discovery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(problem: Problem, tool: Tool) -> bool:
    return tool.safe and problem.risky


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROBLEMS:
            for tid in TOOLS:
                if reasonableness_ok(PROBLEMS[pid], TOOLS[tid]):
                    combos.append((sid, pid, tid))
    return combos


def _do_investigate(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    world.facts["used_analogy"] = True
    world.say(
        f"{hero.id} used {tool.phrase} to look closely at the mystery, and "
        f"their curious mind started making connections."
    )
    propagate(world, narrate=False)


def _smoke_test_story(world: World) -> None:
    if not world.render().strip():
        raise StoryError("Story generation produced empty prose.")


def predict(world: World, tool: Tool, problem: Problem, hero_id: str) -> dict:
    sim = world.copy()
    _do_investigate(sim, sim.get(hero_id), tool, problem)
    return {"fixed": bool(sim.facts.get("problem_fixed"))}


def setup_scene(world: World, hero: Entity, guide: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright day, {hero.id} was a young writer-hero in {setting.place}. "
        f"{hero.id} kept a notebook ready for every brave idea."
    )
    hero.memes["joy"] += 1
    guide.memes["care"] += 1


def feel_curious(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"When {hero.id} noticed {setting.hidden_spot}, {hero.pronoun()} felt a "
        f"strong tug of curiosity."
    )


def compare(world: World, hero: Entity, analogy: Analogy) -> None:
    world.say(
        f'{hero.id} whispered an analogy to {hero.pronoun("object")}self: '
        f'"{analogy.setup}" {analogy.mapping} {analogy.payoff}"'
    )
    hero.memes["understanding"] += 1


def warn(world: World, guide: Entity, hero: Entity, problem: Problem, tool: Tool) -> None:
    pred = predict(world, tool, problem, hero.id)
    if not pred["fixed"]:
        world.say(
            f'{guide.id} held up a calm hand. "{hero.id}, let\'s not dash in. '
            f"We can solve this safely with {tool.label} instead of rushing."
        )
        guide.memes["wisdom"] += 1


def act(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"{hero.id} listened, opened {hero.pronoun('possessive')} notebook, and "
        f"used {tool.phrase} to follow the clue."
    )
    _do_investigate(world, hero, tool, problem)


def resolve(world: World, hero: Entity, guide: Entity, setting: Setting, tool: Tool) -> None:
    world.get("problem").meters["solved"] = 1
    world.say(
        f"The hidden issue turned out to be harmless: just a stuck panel, not a monster. "
        f"{hero.id} fixed it, wrote the discovery down, and smiled."
    )
    world.say(
        f"By the end, the notebook had a new page, {setting.hidden_spot} looked safe again, "
        f"and {hero.id}'s curiosity felt like a real superpower."
    )
    hero.memes["pride"] += 1
    guide.memes["relief"] += 1


def tell(setting: Setting, problem: Problem, tool: Tool, analogy: Analogy,
         hero_name: str = "Mina", hero_gender: str = "girl",
         guide_name: str = "Aunt Ray", guide_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    world.add(Entity(id="problem", type="problem", label=problem.label))
    setup_scene(world, hero, guide, setting)
    world.para()
    feel_curious(world, hero, setting)
    compare(world, hero, analogy)
    warn(world, guide, hero, problem, tool)
    world.para()
    act(world, hero, problem, tool)
    resolve(world, hero, guide, setting, tool)
    world.facts.update(hero=hero, guide=guide, setting=setting, problem=problem, tool=tool,
                       analogy=analogy, fixed=True)
    _smoke_test_story(world)
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "the attic", "a dusty trunk", "a mystery", "brave"),
    "studio": Setting("studio", "the studio", "the studio", "a tall shelf", "a puzzle", "bright"),
    "library": Setting("library", "the library corner", "the library corner", "a quiet nook", "a clue", "calm"),
}

PROBLEMS = {
    "stuck_panel": Problem("stuck_panel", "stuck panel", "a panel that would not budge"),
    "lost_page": Problem("lost_page", "lost page", "a missing page from the notebook"),
    "odd_noise": Problem("odd_noise", "odd noise", "a strange tapping sound behind the wall"),
}

TOOLS = {
    "flashlight": Tool("flashlight", "flashlight", "a small flashlight", "shine on the clue"),
    "magnifier": Tool("magnifier", "magnifying glass", "a magnifying glass", "read tiny details"),
    "sticky_notes": Tool("sticky_notes", "sticky notes", "a stack of sticky notes", "mark ideas"),
}

ANALOGIES = {
    "lantern": Analogy("lantern", "a clue is like a lantern,", "it does not solve the mystery alone, but", "it helps you see what to do next."),
    "bridge": Analogy("bridge", "an idea is like a bridge,", "it may look small, but", "it can carry you to the answer."),
    "lens": Analogy("lens", "curiosity is like a lens,", "it does not change the world, but", "it helps you notice what matters."),
}


GIRL_NAMES = ["Mina", "Tessa", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Arlo", "Jude"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    analogy: str
    hero_name: str
    hero_gender: str
    guide_name: str
    guide_gender: str
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

CURATED = [
    ("attic", "stuck_panel", "flashlight", "lens"),
    ("studio", "lost_page", "magnifier", "bridge"),
    ("library", "odd_noise", "sticky_notes", "lantern"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a child that includes the words "writer" and "analogy" and shows curiosity as a strength.',
        f"Tell a story about {f['hero'].id}, a writer-hero, who gets curious about {f['problem'].label} and solves it safely with an analogy.",
        f"Write a gentle superhero story where curiosity leads a young writer to investigate a mystery without rushing in.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, setting, problem, tool, analogy = f["hero"], f["guide"], f["setting"], f["problem"], f["tool"], f["analogy"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, a young writer-hero, and {guide.id}, who helped keep the investigation safe. {hero.id}'s curiosity led the story forward."
        ),
        QAItem(
            question="Why did the hero need help?",
            answer=f"{hero.id} was curious about {setting.hidden_spot} and almost rushed toward the mystery. {guide.id} helped by pointing out a safer way to investigate {problem.label}."
        ),
        QAItem(
            question="How did the analogy help?",
            answer=f"The analogy helped {hero.id} think clearly before acting. It made the mystery feel like something {hero.id} could understand and solve step by step."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The problem was fixed, the hidden spot was safe again, and {hero.id} had a new notebook page about the discovery. Curiosity became a superpower instead of a worry."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn, explore, or understand something new. It can help you find answers when you use it carefully."
        ),
        QAItem(
            question="What is a writer?",
            answer="A writer is a person who puts ideas into words on paper or on a screen. Writers can tell stories, share facts, or save a memory."
        ),
        QAItem(
            question="What is an analogy?",
            answer="An analogy compares one thing to another so it is easier to understand. It is like saying, 'This idea works like that idea.'"
        ),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, tool: Tool) -> str:
    if not reasonableness_ok(problem, tool):
        return f"(No story: {tool.label} is not a sensible tool for this kind of problem.)"
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid(S, P, T) :- setting(S), problem(P), tool(T), risky(P), safe(T).
used_analogy :- chosen_analogy(A).
solved :- used_analogy, valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
    for aid in ANALOGIES:
        lines.append(asp.fact("analogy", aid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool=None, analogy=None,
                                                            hero_name=None, hero_gender=None, guide_name=None,
                                                            guide_gender=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test story generated.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a writer, analogy, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--analogy", choices=ANALOGIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    analogy = args.analogy or rng.choice(sorted(ANALOGIES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    guide_name = args.guide_name or ("Aunt Ray" if guide_gender == "woman" else "Uncle Ray")
    return StoryParams(setting, problem, tool, analogy, hero_name, hero_gender, guide_name, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool],
                 ANALOGIES[params.analogy], params.hero_name, params.hero_gender,
                 params.guide_name, params.guide_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s, p, t in CURATED:
            params = StoryParams(s, p, t, "lens", "Mina", "girl", "Aunt Ray", "woman")
            samples.append(generate(params))
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
