#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/zone_hood_pl_dim_teach_foreshadowing_mystery.py
===============================================================================

A standalone storyworld in a small fable-like domain: a child in a garden zone
notices a dim hood, learns to teach by looking closely, and solves a little
mystery through foreshadowing.

The world is built around:
- zones in a garden
- a dim hooded lantern ("hood-pl-dim" in the seed)
- a teaching moment
- foreshadowing
- a mystery to solve

The story is intentionally tiny and classical: a problem appears, clues matter,
a calm helper teaches a better way, and the ending proves what changed.
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
class Zone:
    id: str
    label: str
    clue: str
    shadow: str
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
class HoodLamp:
    id: str
    label: str
    phrase: str
    dim_phrase: str
    bright_phrase: str
    safe: bool = True
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
class Mystery:
    id: str
    question: str
    solve_verb: str
    reveal: str
    solved_with: str
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
class Lesson:
    id: str
    phrase: str
    teach_line: str
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


def _r_dim_hint(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.get("lamp")
    child = world.get("child")
    if lamp.meters["dim"] >= THRESHOLD and ("hint", "dim") not in world.fired:
        world.fired.add(("hint", "dim"))
        child.memes["curiosity"] += 1
        out.append("__hint__")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["noticed"] >= THRESHOLD and ("solved",) not in world.fired:
        world.fired.add(("solved",))
        world.get("mystery").meters["solved"] += 1
        out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule("dim_hint", "social", _r_dim_hint),
    Rule("solved", "social", _r_solved),
]


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


def _inspect(world: World, child: Entity, lamp: Entity, zone: Zone, mystery: Mystery) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"One evening, {child.id} wandered into the {zone.label} zone, where "
        f"{zone.clue}."
    )
    world.say(
        f"There on a low shelf sat {lamp.phrase}. It looked useful, but {lamp.dim_phrase}."
    )
    world.say(
        f"{child.id} noticed that the shadow near the path matched the shape of the clue, "
        f"as if the garden wanted to teach a secret."
    )


def _ask(world: World, child: Entity, zone: Zone, mystery: Mystery) -> None:
    child.memes["question"] += 1
    world.say(
        f'"Why is the path so strange?" {child.id} asked. '
        f'The little mystery was simple to name: {mystery.question}.'
    )


def _foreshadow(world: World, child: Entity, lamp: Entity) -> None:
    child.memes["foreshadowing"] += 1
    world.say(
        f"Before anyone touched anything, {child.id} remembered the old warning: "
        f"when a light is too dim, you should look for what it hides."
    )


def _teach(world: World, teacher: Entity, child: Entity, lamp: Entity, mystery: Mystery, lesson: Lesson) -> None:
    teacher.memes["patience"] += 1
    world.say(
        f"{teacher.id} knelt beside {child.id} and smiled. "
        f'"Let me teach you something," {teacher.pronoun()} said. '
        f'{lesson.teach_line}'
    )
    world.say(
        f"{teacher.id} showed how {lamp.label} could be lifted, turned, and held steady "
        f"so the dark corner would stop hiding the answer."
    )


def _solve(world: World, child: Entity, teacher: Entity, lamp: Entity, zone: Zone, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    child.meters["noticed"] += 1
    world.get("clue").meters["noticed"] += 1
    world.say(
        f"Then {child.id} looked again and saw the tiny thing everyone had missed. "
        f"It was {mystery.reveal}."
    )
    world.say(
        f"The clue fit the shadow, the shadow fit the zone, and the mystery was solved "
        f"with {mystery.solved_with}."
    )
    lamp.meters["lit"] += 1


def tell(zone: Zone, lamp: HoodLamp, mystery: Mystery, lesson: Lesson,
         child_name: str = "Milo", child_gender: str = "boy",
         teacher_name: str = "Grandma", teacher_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    teacher = world.add(Entity(id=teacher_name, kind="character", type=teacher_gender, role="teacher"))
    world.add(Entity(id="zone", type="zone", label=zone.label))
    lamp_ent = world.add(Entity(id="lamp", type="thing", label=lamp.label))
    clue = world.add(Entity(id="clue", type="thing", label="the clue"))
    m = world.add(Entity(id="mystery", type="thing", label=mystery.question))

    child.memes["curiosity"] = 1.0
    child.memes["hope"] = 1.0
    lamp_ent.meters["dim"] = 1.0

    _inspect(world, child, lamp_ent, zone, mystery)
    world.para()
    _ask(world, child, zone, mystery)
    _foreshadow(world, child, lamp_ent)
    propagate(world, narrate=True)

    world.para()
    _teach(world, teacher, child, lamp_ent, mystery, lesson)
    _solve(world, child, teacher, lamp_ent, zone, mystery)

    world.say(
        f"In the end, the {zone.label} zone felt peaceful again, and the dim hooded light "
        f"shone just enough to guide a kinder look."
    )

    world.facts.update(
        child=child,
        teacher=teacher,
        zone_cfg=zone,
        lamp_cfg=lamp,
        mystery_cfg=mystery,
        lesson_cfg=lesson,
        clue=clue,
        mystery=m,
        solved=m.meters["solved"] >= THRESHOLD,
    )
    return world


ZONES = {
    "garden": Zone(
        "garden",
        "garden",
        "the ivy by the gate whispered that something small was missing",
        "the hedge cast a long, quiet shadow",
        tags={"zone", "garden", "mystery"},
    ),
    "orchard": Zone(
        "orchard",
        "orchard",
        "the apple trees dropped one fruit too few from one branch",
        "the grass held a neat patch of shade",
        tags={"zone", "orchard", "mystery"},
    ),
    "courtyard": Zone(
        "courtyard",
        "courtyard",
        "the fountain circle had one dry stone where water should have sparkled",
        "the wall made a soft blue shadow",
        tags={"zone", "courtyard", "mystery"},
    ),
}

LAMPS = {
    "hood-pl-dim": HoodLamp(
        "hood-pl-dim",
        "hooded lamp",
        "a small hooded lamp",
        "its glow was dim, like a sleepy firefly",
        "its glow grew bright and warm",
        tags={"hood", "dim", "light"},
    ),
    "lantern": HoodLamp(
        "lantern",
        "lantern",
        "a brass lantern",
        "its light was low and shy",
        "its light opened wide",
        tags={"light", "dim"},
    ),
}

MYSTERIES = {
    "lost_key": Mystery(
        "lost_key",
        "Who took the garden key?",
        "notice",
        "a little brass key tucked under a leaf",
        "the dim lamp beam",
        tags={"mystery", "key"},
    ),
    "hidden_seed": Mystery(
        "hidden_seed",
        "Where did the seed go?",
        "notice",
        "a seed resting in a crack beside the path",
        "the soft hooded light",
        tags={"mystery", "seed"},
    ),
}

LESSONS = {
    "look_close": Lesson(
        "look_close",
        "look close before you guess",
        "Grandma taught that careful eyes can solve a mystery faster than loud voices can",
        tags={"teach", "lesson"},
    ),
    "share_light": Lesson(
        "share_light",
        "a steady light helps everyone see",
        "Grandma taught that light is kinder when it is held still and shared",
        tags={"teach", "light"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tia", "Mina"]
BOY_NAMES = ["Milo", "Theo", "Ezra", "Ari", "Levi"]


@dataclass
@dataclass
class StoryParams:
    zone: str
    lamp: str
    mystery: str
    lesson: str
    child_name: str
    child_gender: str
    teacher_name: str
    teacher_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for z in ZONES:
        for l in LAMPS:
            for m in MYSTERIES:
                for le in LESSONS:
                    combos.append((z, l, m, le))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-like mystery storyworld.")
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--teacher-name")
    ap.add_argument("--teacher-gender", choices=["man", "woman"])
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
    zone = args.zone or rng.choice(sorted(ZONES))
    lamp = args.lamp or rng.choice(sorted(LAMPS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(BOY_NAMES if child_gender == "boy" else GIRL_NAMES)
    teacher_gender = args.teacher_gender or rng.choice(["woman", "man"])
    teacher_name = args.teacher_name or rng.choice(["Grandma", "Grandpa", "Aunt Rose", "Uncle Ben"])
    return StoryParams(zone, lamp, mystery, lesson, child_name, child_gender, teacher_name, teacher_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small fable about a child in the {f["zone_cfg"].label} zone, where a dim hooded lamp points to a mystery.',
        f'Tell a gentle story with foreshadowing and a mystery to solve, using the word "zone" and the phrase "hood-pl-dim".',
        f'Write a child-facing story where {f["teacher"].id} teaches {f["child"].id} how careful looking solves a hidden problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who is the story about?",
            answer=f'It is about {f["child"].id} and {f["teacher"].id}, who visit the {f["zone_cfg"].label} zone and solve a small mystery together.',
        ),
        QAItem(
            question="What was the mystery?",
            answer=f'The mystery was: {f["mystery_cfg"].question} The answer appeared when they used the hooded lamp to look closely.',
        ),
        QAItem(
            question="How did the teacher help?",
            answer=f'{f["teacher"].id} taught {f["child"].id} to look close, keep the light steady, and trust the clue instead of guessing too fast.',
        ),
        QAItem(
            question="What changed at the end?",
            answer=f'The hidden thing was found, the mystery was solved, and the {f["zone_cfg"].label} zone felt calm and clear again.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zone?",
            answer="A zone is a small area or part of a place. In a story, it can mean one special corner of a garden or yard.",
        ),
        QAItem(
            question="What does a dim light mean?",
            answer="A dim light is weak light that does not shine very far. It can make things hard to see until it is held steady or made brighter.",
        ),
        QAItem(
            question="What does it mean to teach someone?",
            answer="To teach someone means to help them learn something new. A teacher explains, shows, and helps the learner try it too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "hood-pl-dim", "lost_key", "look_close", "Milo", "boy", "Grandma", "woman"),
    StoryParams("orchard", "lantern", "hidden_seed", "share_light", "Mira", "girl", "Aunt Rose", "woman"),
    StoryParams("courtyard", "hood-pl-dim", "hidden_seed", "look_close", "Theo", "boy", "Grandpa", "man"),
]


ASP_RULES = r"""
zone(Z) :- zone_fact(Z).
lamp(L) :- lamp_fact(L).
mystery(M) :- mystery_fact(M).
lesson(Ls) :- lesson_fact(Ls).
valid(Z, L, M, Ls) :- zone(Z), lamp(L), mystery(M), lesson(Ls).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for z in ZONES:
        lines.append(asp.fact("zone_fact", z))
    for l in LAMPS:
        lines.append(asp.fact("lamp_fact", l))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    for ls in LESSONS:
        lines.append(asp.fact("lesson_fact", ls))
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

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        p = CURATED[0]
        sample = generate(p)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        _ = buf.getvalue()
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(ZONES[params.zone], LAMPS[params.lamp], MYSTERIES[params.mystery], LESSONS[params.lesson],
                 params.child_name, params.child_gender, params.teacher_name, params.teacher_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
                p.seed = base_seed + i
                s = generate(p)
            except StoryError as err:
                print(err)
                return
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} in the {p.zone} zone"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
