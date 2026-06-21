#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/viaduct_visible_misunderstanding_curiosity_problem_solving_slice.py
===================================================================================================

A small slice-of-life storyworld about a child, a caregiver, a viaduct, and a
bright misunderstanding that curiosity turns into problem solving.

Seed-shaped premise:
- Words: viaduct, visible
- Features: Misunderstanding, Curiosity, Problem Solving
- Style: Slice of Life

This world models a short everyday outing where something on or under a viaduct
looks puzzling at first, the child gets curious, the caregiver misreads the
situation, and together they solve the practical problem in a calm, concrete way.
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    viaduct_view: str
    nearby: str
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
class Clue:
    id: str
    label: str
    visible: bool = True
    kind: str = "small_object"
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
class Misunderstanding:
    id: str
    mistaken_reading: str
    correction: str
    question: str
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
class Problem:
    id: str
    label: str
    method: str
    result: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy as _copy
        other = World()
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


SETTINGS = {
    "riverwalk": Setting(
        id="riverwalk",
        place="the riverwalk",
        viaduct_view="the viaduct arched over the water",
        nearby="a small kiosk and a bench",
        tags={"viaduct", "visible"},
    ),
    "station_path": Setting(
        id="station_path",
        place="the station path",
        viaduct_view="the viaduct was visible above the street",
        nearby="a newspaper stand and a bike rack",
        tags={"viaduct", "visible"},
    ),
}

CLUES = {
    "kite_string": Clue(
        id="kite_string",
        label="a bright string from a kite",
        visible=True,
        tags={"visible", "string"},
    ),
    "lost_button": Clue(
        id="lost_button",
        label="a shiny button",
        visible=True,
        tags={"visible", "button"},
    ),
    "paper_map": Clue(
        id="paper_map",
        label="a folded paper map",
        visible=True,
        tags={"visible", "paper"},
    ),
}

MISUNDERSTANDINGS = {
    "ticket": Misunderstanding(
        id="ticket",
        mistaken_reading="thought it was a dropped ticket",
        correction="it was only a kite string tied to the railing",
        question="What did that line look like at first?",
        tags={"misunderstanding", "visible"},
    ),
    "snake": Misunderstanding(
        id="snake",
        mistaken_reading="thought it was a tiny snake",
        correction="it was only a bent ribbon snagged on a bolt",
        question="Why did it seem confusing?",
        tags={"misunderstanding", "curiosity"},
    ),
}

PROBLEMS = {
    "snag": Problem(
        id="snag",
        label="a snagged cord",
        method="untangling it carefully with a stick",
        result="the path was clear again",
        tags={"problem_solving"},
    ),
    "stuck_gate": Problem(
        id="stuck_gate",
        label="a gate that would not close",
        method="lifting it a little and nudging the latch straight",
        result="the gate clicked shut neatly",
        tags={"problem_solving"},
    ),
}

KID_NAMES = ["Mina", "Jules", "Tara", "Noah", "Iris", "Eli", "Maya", "Owen"]


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    clue: str
    misunderstanding: str
    problem: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for m in MISUNDERSTANDINGS:
                for p in PROBLEMS:
                    out.append((s, c, m))
    return out


def explain_rejection(_: Optional[str] = None) -> str:
    return "(No story: the chosen options do not fit the viaduct/visible everyday scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world about a visible viaduct misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mom", "dad", "mother", "father"])
    ap.add_argument("--adult-gender", choices=["girl", "boy", "woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    if args.child_gender:
        child_gender = args.child_gender
    else:
        child_gender = rng.choice(["girl", "boy"])
    child = args.child or rng.choice(KID_NAMES)
    adult = args.adult or rng.choice(["mom", "dad"])
    adult_gender = args.adult_gender or ("woman" if adult in {"mom", "mother"} else "man")
    return StoryParams(setting, child, child_gender, adult, adult_gender, clue, misunderstanding, problem)


def _make_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.misunderstanding not in MISUNDERSTANDINGS or params.problem not in PROBLEMS:
        raise StoryError("Invalid parameters for this storyworld.")

    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    problem = PROBLEMS[params.problem]

    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender, role="adult", label=params.adult))
    viaduct = world.add(Entity(id="viaduct", kind="thing", type="landmark", label="the viaduct", tags={"viaduct"}))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="thing", label=clue.label, tags=set(clue.tags)))
    problem_ent = world.add(Entity(id="problem", kind="thing", type="thing", label=problem.label))
    world.facts.update(setting=setting, clue=clue, misunderstanding=misunderstanding, problem=problem,
                       child=child, adult=adult, viaduct=viaduct, clue_ent=clue_ent, problem_ent=problem_ent)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    setting: Setting = f["setting"]
    clue: Clue = f["clue"]
    misunderstanding: Misunderstanding = f["misunderstanding"]
    problem: Problem = f["problem"]

    child.memes["curiosity"] += 1
    world.say(
        f"After lunch, {child.id} walked with {adult.id} at {setting.place}. "
        f"{setting.viaduct_view}, and {setting.nearby} sat below it."
    )
    world.say(
        f"Then {child.id} noticed {clue.label} {misunderstanding.mistaken_reading if clue.visible else 'hidden in the shade'}."
    )
    world.para()
    child.memes["curiosity"] += 1
    adult.memes["worry"] += 1
    world.say(
        f'{child.id} pointed up. "Look, {adult.id}! {misunderstanding.question}" '
        f"{child.pronoun()} asked, leaning closer so it would stay visible."
    )
    world.say(
        f'{adult.id} frowned and answered, "{adult.id} thought it was a mistake, but '
        f'{misunderstanding.correction}."'
    )
    world.para()
    child.memes["focus"] += 1
    world.say(
        f"{child.id} looked again and noticed the real problem: {problem.label}. "
        f"It was {problem.method}, and that would help because {problem.result}."
    )
    world.say(
        f"Together they fixed it without hurrying. Soon {problem.result}, "
        f"and the viaduct stayed calm and visible in the afternoon light."
    )
    child.memes["pride"] += 1
    adult.memes["relief"] += 1
    world.facts["resolved"] = True
    world.facts["ending"] = f"{child.id} and {adult.id} went on, with the viaduct still visible and the path neat again."


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story that includes the words viaduct and visible, where {f['child'].id} notices something puzzling and asks about it.",
        f"Tell a gentle everyday story about a child near a viaduct, a misunderstanding, and a calm fix by {f['adult'].id}.",
        f"Write a short story for a young child where curiosity helps solve a small problem beside something visible and tall.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    setting: Setting = f["setting"]
    misunderstanding: Misunderstanding = f["misunderstanding"]
    problem: Problem = f["problem"]
    qa = [
        ("Where were they walking?",
         f"They were walking at {setting.place}, where the viaduct was easy to see. The tall bridge-like shape made the scene feel ordinary but interesting."),
        (f"What did {child.id} notice?",
         f"{child.id} noticed {f['clue'].label}. It was visible, so it caught {child.id}'s eye right away."),
        (f"What did {child.id} first misunderstand?",
         f"{child.id} {misunderstanding.mistaken_reading}. That was the misunderstanding, and it made the moment feel puzzling for a minute."),
        ("How did they solve the problem?",
         f"They solved it by {problem.method}. That worked because {problem.result}, so the little trouble was handled calmly."),
    ]
    qa.append((
        "How did the story end?",
        f"It ended with {f['ending']}. The child and adult kept walking with the viaduct still visible and the small problem fixed."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a viaduct?",
         "A viaduct is a long bridge that carries a road or path over low ground. It is usually easy to see from nearby streets or sidewalks."),
        ("What does visible mean?",
         "Visible means something can be seen with your eyes. If it is visible, it is not hidden."),
        ("What is curiosity?",
         "Curiosity is the wish to look, ask, and find out more about something."),
        ("What is problem solving?",
         "Problem solving means noticing a problem and trying careful steps to fix it."),
    ]


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
visible(clue).
viaduct(setting).
story_ok(S,C,M,P) :- setting(S), clue(C), misunderstanding(M), problem(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("viaduct", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        if CLUES[cid].visible:
            lines.append(asp.fact("visible", cid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/4."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s, c, m) for s, c, m in valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(
            StoryParams(
                setting="riverwalk",
                child="Mina",
                child_gender="girl",
                adult="mom",
                adult_gender="woman",
                clue="kite_string",
                misunderstanding="ticket",
                problem="snag",
                seed=1,
            )
        )
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="riverwalk", child="Mina", child_gender="girl", adult="mom", adult_gender="woman",
                clue="kite_string", misunderstanding="ticket", problem="snag"),
    StoryParams(setting="station_path", child="Owen", child_gender="boy", adult="dad", adult_gender="man",
                clue="lost_button", misunderstanding="snake", problem="stuck_gate"),
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
        print(asp_program("#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show story_ok/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
