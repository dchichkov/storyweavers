#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/bolt_dismal_school_library_surprise_inner_monologue.py
================================================================================================

A small animal-story world set in a school library, built from the seed words
"bolt" and "dismal" and the narrative instruments Surprise, Inner Monologue,
and Flashback.

The story space is intentionally tiny and constraint-checked:
- an animal child is in the school library on a gloomy day,
- something important goes missing or gets blocked,
- a surprise reveal changes the plan,
- an inner monologue surfaces the child's feelings,
- a flashback explains the key clue,
- the ending image shows the physical change.

The world is written to be self-contained and to support:
default generation, -n, --all, --seed, --trace, --qa, --json,
--asp, --verify, and --show-asp.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the school library"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    description: str
    cause: str
    emotional: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    action: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    id: str
    label: str
    flashback: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    use: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "library"
    animal: str = ""
    name: str = ""
    problem: str = ""
    surprise: str = ""
    memory: str = ""
    goal: str = ""
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dismal(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("dismal", 0.0) >= THRESHOLD and ("dismal", e.id) not in world.fired:
            world.fired.add(("dismal", e.id))
            e.memes["heavy"] = e.memes.get("heavy", 0.0) + 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("dismal", "emotional", _r_dismal)]


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


def inner_thought(a: Entity) -> str:
    if a.memes.get("dismal", 0.0) >= THRESHOLD:
        return f"{a.id} felt dismal and small, as if the library's hush had sat on {a.pronoun('possessive')} back."
    return f"{a.id} felt calm enough to listen to the quiet shelves."


def flashback_text(mem: Memory, goal: Goal) -> str:
    return f"That reminded {goal.label} of a flashback: {mem.flashback} {mem.clue}"


def surprise_text(sp: Surprise, animal: Entity, goal: Goal) -> str:
    return f"Then came a surprise: {sp.reveal} {animal.id} {sp.action}, and the {goal.label} was no longer stuck."


def valid_story_combo(problem: Problem, surprise: Surprise, memory: Memory, goal: Goal) -> bool:
    return "bolt" in problem.tags and "surprise" in surprise.tags and "flashback" in memory.tags and "library" in goal.tags


SETTINGS = {
    "library": Setting(place="the school library", affordances={"read", "sort", "fetch"}),
}

ANIMALS = {
    "mouse": {"type": "mouse", "label": "mouse"},
    "fox": {"type": "fox", "label": "fox"},
    "cat": {"type": "cat", "label": "cat"},
}

PROBLEMS = {
    "locked": Problem(
        id="locked",
        description="a small reading nook was shut by a stubborn bolt",
        cause="the bolt had slid into place",
        emotional="dismal",
        tags={"bolt", "library"},
    ),
    "lost_card": Problem(
        id="lost_card",
        description="the checkout card was missing from the basket",
        cause="it had slipped under a book cart",
        emotional="dismal",
        tags={"library"},
    ),
    "stuck_box": Problem(
        id="stuck_box",
        description="a craft box was stuck behind a low shelf",
        cause="the shelf had been nudged too close",
        emotional="dismal",
        tags={"library"},
    ),
    "quiet_alarm": Problem(
        id="quiet_alarm",
        description="a display case had a tiny bolt that would not turn",
        cause="the bolt was too tight",
        emotional="dismal",
        tags={"bolt", "library"},
    ),
}

SURPRISES = {
    "janitor_key": Surprise(
        id="janitor_key",
        label="surprise",
        reveal="the janitor jingled over with a tiny key",
        action="used the key to open the nook",
        fix="opened it at once",
        tags={"surprise", "library"},
    ),
    "hidden_hook": Surprise(
        id="hidden_hook",
        label="surprise",
        reveal="a librarian found a hidden hook behind the sign",
        action="pulled the bolt free with it",
        fix="freed the stuck part",
        tags={"surprise", "library"},
    ),
    "class_note": Surprise(
        id="class_note",
        label="surprise",
        reveal="a class note fluttered out from behind a book",
        action="realized the missing item was in the return tray",
        fix="put the search on the right shelf",
        tags={"surprise", "library"},
    ),
}

MEMORIES = {
    "story_time": Memory(
        id="story_time",
        label="flashback",
        flashback="Earlier, during story time, the librarian had shown",
        clue="how a bolt could slide only when the latch lined up.",
        tags={"flashback", "bolt"},
    ),
    "window_day": Memory(
        id="window_day",
        label="flashback",
        flashback="Yesterday, while rain tapped the windows, the animal child had seen",
        clue="where the return tray sat beside the lamp table.",
        tags={"flashback"},
    ),
    "shelf_run": Memory(
        id="shelf_run",
        label="flashback",
        flashback="At the last shelf race, the fox had noticed",
        clue="that small things often rolled under the lowest cart.",
        tags={"flashback"},
    ),
}

GOALS = {
    "open_nook": Goal(
        id="open_nook",
        label="reading nook",
        use="read there",
        ending="the reading nook stood open and the bookmark lay on the bench",
        tags={"library"},
    ),
    "find_card": Goal(
        id="find_card",
        label="checkout card",
        use="check out the books",
        ending="the checkout card was back in the basket, neat and ready",
        tags={"library"},
    ),
    "reach_box": Goal(
        id="reach_box",
        label="craft box",
        use="make paper stars",
        ending="the craft box rested on the table beside the paper stars",
        tags={"library"},
    ),
    "open_case": Goal(
        id="open_case",
        label="display case",
        use="see the old shell",
        ending="the display case was open and the shell shone in the light",
        tags={"library", "bolt"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Poppy", "Nia"]
BOY_NAMES = ["Toby", "Finn", "Otis", "Bram"]
NEUTRAL_NAMES = ["Sunny", "Pebble", "Milo", "Sage"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, p in PROBLEMS.items():
        for sid, s in SURPRISES.items():
            for mid, m in MEMORIES.items():
                for gid, g in GOALS.items():
                    if valid_story_combo(p, s, m, g):
                        combos.append((pid, sid, mid, gid))
    return combos


def explain_rejection(problem: Problem, surprise: Surprise, memory: Memory, goal: Goal) -> str:
    return f"(No story: this combination does not fit the school-library bolt-and-surprise premise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a dismal school library surprise with a flashback.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
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
              if (args.problem is None or c[0] == args.problem)
              and (args.surprise is None or c[1] == args.surprise)
              and (args.memory is None or c[2] == args.memory)
              and (args.goal is None or c[3] == args.goal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pid, sid, mid, gid = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES + NEUTRAL_NAMES)
    return StoryParams(setting="library", animal=animal, name=name, problem=pid, surprise=sid, memory=mid, goal=gid)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem"]
    goal = f["goal"]
    sp = f["surprise"]
    mem = f["memory"]
    return [
        QAItem(
            question=f"What made {hero.id} feel dismal in the school library?",
            answer=f"{hero.id} felt dismal because {prob.description}. The problem made the quiet room feel even heavier.",
        ),
        QAItem(
            question=f"What surprise helped {hero.id} solve the problem?",
            answer=f"{sp.reveal} {hero.id} {sp.action}. That surprise changed the stuck situation into a fix.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the flashback?",
            answer=f"{mem.flashback} {mem.clue} That memory helped {hero.id} understand what to do next.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{goal.ending}. The small fix proved the problem had been solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bolt?", "A bolt is a metal fastener that slides or turns to lock something in place."),
        QAItem("What does dismal mean?", "Dismal means gloomy, sad, or cheerless."),
        QAItem("What is a flashback in a story?", "A flashback is a moment that goes back to an earlier memory."),
        QAItem("What is a surprise in a story?", "A surprise is an unexpected moment that changes what happens next."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write an animal story set in a school library where {hero.id} feels dismal and a bolt causes trouble.",
        f"Tell a gentle story with a surprise, an inner monologue, and a flashback in the school library.",
        f"Write a short animal story that includes the words bolt and dismal and ends with a clear change in the library.",
    ]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero_cfg = ANIMALS[params.animal]
    hero = world.add(Entity(id=params.name, kind="character", type=hero_cfg["type"], label=params.name))
    problem = PROBLEMS[params.problem]
    surprise = SURPRISES[params.surprise]
    memory = MEMORIES[params.memory]
    goal = GOALS[params.goal]
    world.facts.update(hero=hero, problem=problem, surprise=surprise, memory=memory, goal=goal, setting=setting)

    hero.memes["dismal"] = 1.0
    hero.meters["waiting"] = 1.0

    world.say(f"In the school library, {hero.id} padded between the shelves while the afternoon felt dismal.")
    world.say(f"{hero.id} stopped beside {problem.description}.")
    world.say(f'"{inner_thought(hero)}"')

    world.para()
    world.say(f"Then came a surprise: {surprise.reveal}.")
    world.say(f"{hero.id} {surprise.action}.")

    world.para()
    world.say(f"{memory.flashback} {memory.clue}")
    world.say(f"That thought helped {hero.id} know where to go, and {goal.ending}.")

    world.para()
    world.say(f"{hero.id} smiled at the quiet shelves, and the school library no longer felt dismal.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", animal="mouse", name="Mina", problem="locked", surprise="janitor_key", memory="story_time", goal="open_nook"),
    StoryParams(setting="library", animal="fox", name="Toby", problem="quiet_alarm", surprise="hidden_hook", memory="shelf_run", goal="open_case"),
    StoryParams(setting="library", animal="cat", name="Lulu", problem="stuck_box", surprise="class_note", memory="window_day", goal="reach_box"),
    StoryParams(setting="library", animal="mouse", name="Poppy", problem="locked", surprise="hidden_hook", memory="story_time", goal="open_nook"),
]


ASP_RULES = r"""
valid(P,S,M,G) :- problem(P), surprise(S), memory(M), goal(G),
                  bolt_problem(P), surprise_tag(S), flashback_tag(M), library_goal(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "bolt" in p.tags:
            lines.append(asp.fact("bolt_problem", pid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if "surprise" in s.tags:
            lines.append(asp.fact("surprise_tag", sid))
    for mid, m in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
        if "flashback" in m.tags:
            lines.append(asp.fact("flashback_tag", mid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        if "library" in g.tags:
            lines.append(asp.fact("library_goal", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH between ASP and Python valid_combos()")
            return 1
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sample = generate(CURATED[0])
            emit(sample)
        print(f"OK: {len(valid_combos())} combos; generate/emit smoke test passed.")
        return 0
    except Exception as err:
        print(f"VERIFY FAILED: {err}")
        return 1


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
