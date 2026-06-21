#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pertain_system_suspense_problem_solving_comedy.py
==================================================================================

A tiny storyworld about a child noticing a strange message in a home system,
feeling suspense, then solving the problem with a funny, concrete fix.

Seed words to include in story text:
- pertain
- system

Style target:
- Comedy
- Suspense
- Problem solving

The domain is a small household "system" of notes, chores, buttons, and labels.
A child discovers a mysterious beep and follows clues to discover that the
"kitchen system" only needed a tiny maintenance fix: a sticky button and a
misplaced note. The result should be child-facing, state-driven, and complete.

This script follows the Storyweavers contract:
- standalone stdlib script under storyworlds/worlds/
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class SystemPart:
    id: str
    label: str
    needs: set[str] = field(default_factory=set)
    can_stick: bool = False
    can_be_misplaced: bool = False
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
class FixTool:
    id: str
    label: str
    power: int
    sense: int
    text: str
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


@dataclass
class StoryParams:
    home: str
    system: str
    problem: str
    clue: str
    fix: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
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


HOMES = {
    "kitchen": "the kitchen",
    "laundry": "the laundry room",
    "garage": "the garage",
    "hallway": "the hallway",
}

SYSTEMS = {
    "announcement": {
        "name": "the home announcement system",
        "parts": ["speaker", "button", "screen"],
        "theme": "a tiny mystery beep",
    },
    "sorting": {
        "name": "the label sorting system",
        "parts": ["tray", "sticker", "switch"],
        "theme": "a weird shuffle of labels",
    },
    "chore": {
        "name": "the chore reminder system",
        "parts": ["beeper", "list", "magnet"],
        "theme": "a beep about chores",
    },
}

PROBLEMS = {
    "sticky_button": SystemPart(
        id="sticky_button",
        label="sticky button",
        needs={"press"},
        can_stick=True,
        tags={"button", "sticky"},
    ),
    "misplaced_note": SystemPart(
        id="misplaced_note",
        label="missing note",
        needs={"read"},
        can_be_misplaced=True,
        tags={"note", "paper"},
    ),
    "jammed_screen": SystemPart(
        id="jammed_screen",
        label="jammed screen",
        needs={"tap"},
        can_stick=True,
        tags={"screen", "stuck"},
    ),
}

CLUES = {
    "crumbs": "a trail of crumbs",
    "loud": "an extra loud beep",
    "arrow": "a crooked arrow sticker",
}

FIXES = {
    "wipe": FixTool(
        id="wipe",
        label="a damp cloth",
        power=2,
        sense=3,
        text="wiped the button clean with a damp cloth",
        tags={"clean", "cloth"},
    ),
    "relabel": FixTool(
        id="relabel",
        label="a bright label sheet",
        power=2,
        sense=3,
        text="made a new label and stuck it in the right spot",
        tags={"label", "paper"},
    ),
    "reboot": FixTool(
        id="reboot",
        label="the reset switch",
        power=3,
        sense=4,
        text="pressed the reset switch and watched the lights blink like sleepy eyes",
        tags={"reset", "switch"},
    ),
    "tape": FixTool(
        id="tape",
        label="a roll of tape",
        power=1,
        sense=2,
        text="used a tiny piece of tape to hold the note in place",
        tags={"tape"},
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Ava", "Nora", "Ella"]
NAMES_BOY = ["Ben", "Theo", "Max", "Leo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for home in HOMES:
        for system in SYSTEMS:
            for problem in PROBLEMS:
                if home in {"kitchen", "laundry", "garage", "hallway"} and system in SYSTEMS:
                    if problem in {"sticky_button", "misplaced_note", "jammed_screen"}:
                        combos.append((home, system, problem))
    return combos


def reasonableness_ok(system_id: str, problem_id: str, fix_id: str) -> bool:
    problem = PROBLEMS[problem_id]
    fix = FIXES[fix_id]
    if problem_id == "sticky_button":
        return "clean" in fix.tags or fix.power >= 3
    if problem_id == "misplaced_note":
        return "label" in fix.tags or "tape" in fix.tags
    if problem_id == "jammed_screen":
        return fix.power >= 3
    return False


def explain_rejection(problem_id: str, fix_id: Optional[str] = None) -> str:
    if fix_id is None:
        return "(No story: the setup is too vague.)"
    problem = PROBLEMS[problem_id]
    fix = FIXES[fix_id]
    return (
        f"(No story: {fix.label} would not honestly solve the {problem.label}. "
        f"Pick a fix that actually fits the problem.)"
    )


def should_spook(problem_id: str) -> bool:
    return problem_id in {"sticky_button", "jammed_screen"}


def generate_story_state(home: str, system: str, problem: str, fix: str,
                         hero: str, hero_gender: str,
                         helper: str, helper_gender: str, adult: str) -> World:
    w = World()
    hero_ent = w.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    helper_ent = w.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    adult_ent = w.add(Entity(id=adult, kind="character", type="adult", role="adult"))

    problem_ent = w.add(Entity(id="problem", kind="thing", type=problem, label=PROBLEMS[problem].label, tags=set(PROBLEMS[problem].tags)))
    fix_ent = w.add(Entity(id="fix", kind="thing", type=fix, label=FIXES[fix].label, tags=set(FIXES[fix].tags)))

    hero_ent.memes["curiosity"] += 1
    helper_ent.memes["worry"] += 1 if should_spook(problem) else 0.5
    w.facts.update(home=home, system=system, problem=problem, fix=fix, hero=hero_ent,
                   helper=helper_ent, adult=adult_ent, problem_ent=problem_ent, fix_ent=fix_ent)
    return w


def _rule_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.get("problem").meters["active"] >= THRESHOLD:
        sig = ("spook",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("helper").memes["suspense"] += 1
            out.append("__spook__")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("problem").meters["fixed"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["joy"] += 1
            world.get("helper").memes["joy"] += 1
            out.append("__relief__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_rule_spook, _rule_relief):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def intro(world: World) -> None:
    f = world.facts
    world.say(
        f"On a quiet afternoon, {f['hero'].id} and {f['helper'].id} heard a beep from {f['home']}. "
        f"It came from {SYSTEMS[f['system']]['name']}, which was doing its best to act normal."
    )
    world.say(
        f"The system seemed to pertain to everything in the room, which sounded official and suspicious at the same time."
    )


def clue_scene(world: World) -> None:
    f = world.facts
    clue_word = CLUES.get("crumbs")
    world.say(
        f"{f['helper'].id} pointed at {clue_word} and whispered, \"This is either a clue or lunch for a very tiny detective.\""
    )
    world.say(
        f"{f['hero'].id} leaned closer. The screen flashed once, then blinked again, like it was hiding a joke."
    )


def problem_scene(world: World) -> None:
    f = world.facts
    problem = PROBLEMS[f["problem"]]
    prob = world.get("problem")
    prob.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They found the trouble: the {problem.label} in the system. "
        f"One part was stuck, and the beep kept happening every few seconds."
    )
    world.say(
        f'\"That does not pertain to mystery at all,\" {f["helper"].id} said. \"It pertains to being annoying.\"'
    )


def suspense_scene(world: World) -> None:
    f = world.facts
    world.say(
        f"They opened the panel very slowly. For one second nothing happened, which was somehow even scarier."
    )
    world.say(
        f"Then a little paper note slid out of the side and landed upside down. {f['hero'].id} gasped."
    )


def solve_scene(world: World) -> None:
    f = world.facts
    fix = FIXES[f["fix"]]
    prob = world.get("problem")
    prob.meters["fixed"] += 1
    world.say(
        f"{f['adult'].id} came over, looked once, and said, \"Ah. A practical problem.\" "
        f"Then {f['adult'].pronoun()} {fix.text}."
    )
    if f["fix"] == "reboot":
        world.say("The lights blinked, the beep stopped, and everyone looked proud of the machine for ten whole seconds.")
    elif f["fix"] == "wipe":
        world.say("The sticky button clicked free with a cheerful pop, as if it had only been waiting for a napkin and applause.")
    elif f["fix"] == "relabel":
        world.say("The note went back where it belonged, and the system finally read the right instruction instead of the old joke.")
    else:
        world.say("The tiny piece of tape held the note in place, and the system stopped acting like a dramatic squirrel.")


def ending_scene(world: World) -> None:
    f = world.facts
    world.say(
        f"After that, the whole system hummed nicely, and {f['hero'].id} laughed because the biggest mystery had been a tiny stuck thing all along."
    )
    world.say(
        f"Nobody forgot the lesson: if a beep sounds important, check it carefully, fix the small thing, and then tell the story with a grin."
    )


def tell(home: str, system: str, problem: str, clue: str, fix: str,
         hero: str = "Mia", hero_gender: str = "girl",
         helper: str = "Ben", helper_gender: str = "boy",
         adult: str = "Mom") -> World:
    world = generate_story_state(home, system, problem, fix, hero, hero_gender, helper, helper_gender, adult)
    intro(world)
    world.para()
    clue_scene(world)
    suspense_scene(world)
    world.para()
    problem_scene(world)
    solve_scene(world)
    ending_scene(world)
    world.facts.update(clue=clue, outcome="solved", solved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short funny suspense story for a 3-to-5-year-old about a child noticing a strange beep in a {f["home"]} system.',
        f'Tell a comedy story where {f["hero"].id} and {f["helper"].id} investigate a system problem, use the words "pertain" and "system", and solve it with a clever fix.',
        f"Write a child-friendly problem-solving story with a tiny mystery and a happy ending about a {SYSTEMS[f['system']]['name']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {f['hero'].id} and {f['helper'].id} hearing a strange beep in {f['home']}. They followed the clues, found a small problem in the system, and fixed it together.",
        ),
        QAItem(
            question="Why did the story feel suspenseful?",
            answer="The beep kept happening, and they had to open the panel slowly to see what was wrong. For a moment they could not tell what the system was hiding, so everything felt extra suspenseful.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{f['adult'].id} looked at the trouble, chose the right fix, and made the system behave again. The children learned that a small, careful fix can solve a noisy problem without making things bigger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a system?",
            answer="A system is a set of parts that work together to do a job. If one small part gets stuck, the whole thing may act funny until it is fixed.",
        ),
        QAItem(
            question="What does pertain mean?",
            answer="Pertain means to belong to something or to be about it. A beep can pertain to a system if the beep is part of that system's job or warning.",
        ),
        QAItem(
            question="What should you do when something seems broken?",
            answer="Check it carefully, ask for help if needed, and fix the small problem first. That is often the safest and smartest way to solve it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(home="kitchen", system="announcement", problem="sticky_button", clue="crumbs",
                fix="wipe", hero="Mia", hero_gender="girl", helper="Ben", helper_gender="boy", adult="Mom"),
    StoryParams(home="hallway", system="sorting", problem="misplaced_note", clue="arrow",
                fix="relabel", hero="Theo", hero_gender="boy", helper="Ava", helper_gender="girl", adult="Dad"),
    StoryParams(home="garage", system="chore", problem="jammed_screen", clue="loud",
                fix="reboot", hero="Lina", hero_gender="girl", helper="Max", helper_gender="boy", adult="Dad"),
]


def explain_response(rid: str) -> str:
    return f"(Refusing fix '{rid}': it does not reason about this problem well enough.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.problem and not reasonableness_ok(args.system or "announcement", args.problem, args.fix):
        raise StoryError(explain_rejection(args.problem, args.fix))
    systems = [args.system] if args.system else list(SYSTEMS)
    homes = [args.home] if args.home else list(HOMES)
    problems = [args.problem] if args.problem else list(PROBLEMS)
    fixes = [args.fix] if args.fix else list(FIXES)
    combos = [(h, s, p, fx) for h in homes for s in systems for p in problems for fx in fixes if reasonableness_ok(s, p, fx)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    home, system, problem, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES_GIRL if hero_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_GIRL + NAMES_BOY) if n != hero])
    adult = args.adult or rng.choice(["Mom", "Dad"])
    return StoryParams(home=home, system=system, problem=problem, clue="crumbs", fix=fix,
                       hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, adult=adult)


def generate(params: StoryParams) -> StorySample:
    if params.home not in HOMES or params.system not in SYSTEMS or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    if not reasonableness_ok(params.system, params.problem, params.fix):
        raise StoryError(explain_rejection(params.problem, params.fix))
    world = tell(params.home, params.system, params.problem, params.clue, params.fix,
                 params.hero, params.hero_gender, params.helper, params.helper_gender, params.adult)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy suspense storyworld with a tiny system problem.")
    ap.add_argument("--home", choices=list(HOMES))
    ap.add_argument("--system", choices=list(SYSTEMS))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--fix", choices=list(FIXES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
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


ASP_RULES = r"""
problem(p1). problem(p2). problem(p3).
fix(f1). fix(f2). fix(f3). fix(f4).

reasonable(f1,p1) :- problem(p1).   % wipe -> sticky_button
reasonable(f2,p2) :- problem(p2).   % relabel -> misplaced_note
reasonable(f3,p3) :- problem(p3).   % reboot -> jammed_screen
reasonable(f4,p2).                  % tape can help a misplaced note
reasonable(f4,p1) :- not problem(p3). % harmless fallback fact-ish support
valid(problem, fix) :- problem(P), fix(F), reasonable(F,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for h in HOMES:
        lines.append(asp.fact("home", h))
    for s in SYSTEMS:
        lines.append(asp.fact("system", s))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = {(p[1], p[2]) for p in valid_combos()}
    asp_set = {(p, f) for (p, f) in asp_valid_combos()}
    if python_set != asp_set:
        rc = 1
        print("MISMATCH in ASP parity.")
        print("python-only:", sorted(python_set - asp_set))
        print("asp-only:", sorted(asp_set - python_set))
    else:
        print(f"OK: ASP parity matches ({len(python_set)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAILED: generate() smoke test: {e}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, f in asp_valid_combos():
            print(p, f)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {s.params.hero} & {s.params.helper}: {s.params.problem} in {s.params.system}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
