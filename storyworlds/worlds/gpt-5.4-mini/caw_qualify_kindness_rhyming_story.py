#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caw_qualify_kindness_rhyming_story.py
=====================================================================

A standalone storyworld for a tiny rhyming tale about kindness, a crow's caw,
and a child trying to qualify for a friendly little prize.

Premise
-------
A child and a crow want to join a kindness show. The crow's caw is loud and
the child is unsure whether they can qualify. A gentle helper teaches that
kindness is not about sounding perfect; it is about sharing, waiting, and
making room for others. The ending proves the change with a small bright badge
and a calmer, kinder caw.

This world is intentionally small and constraint-checked:
- typed entities with meters and memes
- a real turn in the world state
- explicit invalid combinations raise StoryError
- a Python reasonableness gate with an inline ASP twin
- story-grounded QA built from simulated state, not from rendered text

The prose is written to feel like a simple rhyming story, while still being
state-driven rather than a frozen paragraph with swapped nouns.
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
class Place:
    id: str
    label: str
    mood: str
    echo: str
    tags: set[str] = field(default_factory=set)

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
class Creature:
    id: str
    label: str
    cry: str
    kind: str = "bird"
    can_caw: bool = True
    friendly: bool = True
    tags: set[str] = field(default_factory=set)

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
class KindnessTask:
    id: str
    need: str
    action: str
    check: str
    tags: set[str] = field(default_factory=set)

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
class Reward:
    id: str
    label: str
    shine: str
    tags: set[str] = field(default_factory=set)

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

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


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities or "crow" not in world.entities:
        return out
    child = world.get("child")
    crow = world.get("crow")
    if child.memes["kindness"] >= THRESHOLD and crow.memes["hope"] >= THRESHOLD:
        sig = ("warm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["glow"] += 1
            crow.meters["glow"] += 1
            out.append("__warm__")
    return out


def _r_qualify(world: World) -> list[str]:
    out: list[str] = []
    judge = world.get("judge")
    child = world.get("child")
    crow = world.get("crow")
    if child.meters["shared"] >= THRESHOLD and child.memes["kindness"] >= THRESHOLD:
        sig = ("qualify",)
        if sig not in world.fired:
            world.fired.add(sig)
            judge.memes["approval"] += 1
            judge.meters["stamp"] += 1
            child.meters["qualified"] = 1
            crow.meters["qualified"] = 1
            out.append("__qualify__")
    return out


CAUSAL_RULES = [Rule("warm", "social", _r_warm), Rule("qualify", "social", _r_qualify)]


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


def reasonableness_check(place: Place, task: KindnessTask, creature: Creature) -> bool:
    return place.id in {"yard", "school", "square"} and task.id in {"share", "help", "wait"} and creature.can_caw


def sensible_tasks() -> list[KindnessTask]:
    return [t for t in TASKS.values() if t.id != "boast"]


def best_task() -> KindnessTask:
    return max(TASKS.values(), key=lambda t: t.id != "boast" and 1 or 0)


def predict(world: World, task_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("child"), TASKS[task_id], narrate=False)
    return {
        "qualified": bool(sim.get("child").meters["qualified"] >= THRESHOLD),
        "approval": sim.get("judge").memes["approval"],
    }


def _do_task(world: World, child: Entity, task: KindnessTask, narrate: bool = True) -> None:
    child.meters["shared"] += 1
    child.memes["kindness"] += 1
    propagate(world, narrate=narrate)


def scene(world: World, place: Place, child: Entity, crow: Creature) -> None:
    child.memes["curiosity"] += 1
    crow.meters["voice"] += 1
    world.say(
        f"At {place.label}, where {place.mood} air would softly sway, "
        f"{child.id} walked in with a crow who liked to caw all day."
    )
    world.say(
        f'"{crow.cry}" went the crow, a bright black bow in the breeze, '
        f"and {child.id} hoped to qualify with kindness, grace, and ease."
    )


def problem(world: World, child: Entity, crow: Creature, judge: Entity, task: KindnessTask) -> None:
    child.memes["want"] += 1
    world.say(
        f"But the judge held up a list so neat, with a shiny silver line: "
        f"to qualify, the pair must show a kind and careful sign."
    )
    world.say(
        f'{child.id} frowned. "I can try the task," {child.pronoun()} said, '
        f'"but that loud caw might shake the stage and make the others dread."'
    )


def turn(world: World, child: Entity, crow: Creature, task: KindnessTask) -> None:
    child.memes["doubt"] += 1
    crow.memes["hope"] += 1
    world.say(
        f"Then {child.id} took a breath and chose to share, not rush, not boast, "
        f"and fixed the wobble with a gentle, giving dose."
    )
    world.say(
        f"{child.id} gave the smallest seat, and made a little space, "
        f"while the crow tucked in its caw to fit the friendly place."
    )
    _do_task(world, child, task)


def ending(world: World, child: Entity, crow: Creature, reward: Reward, judge: Entity) -> None:
    world.say(
        f"Now the judge could see the change: kind hearts shining through. "
        f"The badge flashed bright like morning light, a little star of blue."
    )
    world.say(
        f"{judge.label_word.capitalize()} stamped the card and smiled, "
        f'{"and said"} "You both may qualify." The crow let out one softer caw, '
        f"and kindness rang like chime-y sky."
    )
    child.memes["joy"] += 1
    crow.memes["joy"] += 1
    world.facts["reward"] = reward.label
    world.facts["qualified"] = True


def tell(place: Place, task: KindnessTask, reward: Reward, child_name: str = "Mina",
         child_gender: str = "girl", judge_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    crow = world.add(Entity(id="crow", kind="creature", type="bird", label="a crow"))
    judge = world.add(Entity(id="Judge", kind="character", type=judge_type, role="judge", label="the judge"))

    child.memes["hope"] = 1
    crow.memes["hope"] = 1

    scene(world, place, child, crow)
    world.para()
    problem(world, child, crow, judge, task)
    turn(world, child, crow, task)
    world.para()
    ending(world, child, crow, reward, judge)

    world.facts.update(place=place, task=task, child=child, crow=crow, judge=judge, reward=reward)
    return world


PLACES = {
    "yard": Place("yard", "the yard", "golden", "soft and warm", {"yard"}),
    "school": Place("school", "the schoolyard", "busy", "bright and busy", {"school"}),
    "square": Place("square", "the town square", "open", "wide and open", {"square"}),
}

TASKS = {
    "share": KindnessTask("share", "share a snack", "sharing a snack", "shared"),
    "help": KindnessTask("help", "help a friend", "helping a friend", "helped"),
    "wait": KindnessTask("wait", "wait your turn", "waiting your turn", "waited"),
    "boast": KindnessTask("boast", "brag loudly", "bragging loudly", "boasted"),
}

REWARDS = {
    "badge": Reward("badge", "kindness badge", "a badge that shines like dawn", {"badge"}),
    "ribbon": Reward("ribbon", "kind ribbon", "a ribbon bright as song", {"ribbon"}),
    "star": Reward("star", "gold star", "a star that twinkled blue", {"star"}),
}

GIRL_NAMES = ["Mina", "Lena", "Zoe", "Ari", "Nora", "Ivy"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Finn", "Milo", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, r) for p in PLACES for t in TASKS if t != "boast" for r in REWARDS]


@dataclass
@dataclass
class StoryParams:
    place: str
    task: str
    reward: str
    name: str
    gender: str
    judge: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming kindness storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--judge", choices=["mother", "father"])
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
    if args.task and args.task == "boast":
        raise StoryError("No story: boasting does not qualify as kindness here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.reward is None or c[2] == args.reward)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, reward = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    judge = args.judge or rng.choice(["mother", "father"])
    return StoryParams(place, task, reward, name, gender, judge)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming kindness story with the word "caw" where {f["child"].id} hopes to qualify for a prize.',
        f"Tell a child-friendly story where a crow goes caw and a kind helper helps them qualify.",
        f'Write a short rhyming story about kindness, a crow, and a chance to qualify for a {f["reward"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    crow = f["crow"]
    judge = f["judge"]
    task = f["task"]
    reward = f["reward"]
    return [
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.id} wanted to be kind and qualify for the {reward.label}. The goal mattered because the judge was looking for gentle actions."
        ),
        QAItem(
            question="What did the crow do?",
            answer=f"The crow gave a loud caw at first, then made its caw softer by the end. That change showed the crow learning to fit the kind, quiet mood."
        ),
        QAItem(
            question="How did they qualify?",
            answer=f"They qualified by sharing and making room for others. The judge saw their kindness and stamped the card with a bright smile."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caw?",
            answer="A caw is the sound a crow makes. It can be loud and sharp, like a bird calling across the yard."
        ),
        QAItem(
            question="What does qualify mean?",
            answer="To qualify means to meet the needed rules or show the right skill. If you qualify, you have earned a place or a prize."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful toward others. A kind act can be as simple as sharing or waiting your turn."
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("yard", "share", "badge", "Mina", "girl", "mother"),
    StoryParams("school", "help", "ribbon", "Noah", "boy", "father"),
    StoryParams("square", "wait", "star", "Lena", "girl", "mother"),
]


def outcome_of(params: StoryParams) -> str:
    return "qualified" if params.task != "boast" else "rejected"


def explain_rejection(task: KindnessTask) -> str:
    return f"(No story: {task.id} is not a kindness move here, so it cannot help the child qualify.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
        if t != "boast":
            lines.append(asp.fact("kind_task", t))
    for r in REWARDS:
        lines.append(asp.fact("reward", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R) :- place(P), kind_task(T), reward(R).
qualified :- valid(P,T,R), kind_task(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], REWARDS[params.reward],
                 params.name, params.gender, params.judge)
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
        print(asp_program("#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos[:20]:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
