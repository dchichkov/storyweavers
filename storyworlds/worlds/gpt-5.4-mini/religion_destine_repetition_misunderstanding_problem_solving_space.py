#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/religion_destine_repetition_misunderstanding_problem_solving_space.py
=====================================================================================================

A standalone story world for a small space-adventure tale built from the seed
words "religion" and "destine", with repeated calls, a misunderstanding, and a
problem-solving turn.

The world is child-facing and concrete: two young space explorers are preparing
a tiny ship for a station visit, then a mix-up about the word "destine" leads to
confusion. They repeat the clue, solve the problem by checking the map and labels,
and end in a bright, safe space image.

Supported commands:
    python .../religion_destine_repetition_misunderstanding_problem_solving_space.py
    python ... --all
    python ... -n 5 --seed 7 --qa
    python ... --json
    python ... --trace
    python ... --verify
    python ... --asp
    python ... --show-asp
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
class Place:
    id: str
    label: str
    glow: str
    route: str
    religion: bool = False
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
class Clue:
    id: str
    phrase: str
    meaning: str
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
        self.step: int = 0

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
        c.step = self.step
        return c


def repeat_line(word: str, count: int = 2) -> str:
    return " ".join([word] * count)


def _r_confusion(world: World) -> list[str]:
    out = []
    if world.facts.get("confused") and ("confusion",) not in world.fired:
        world.fired.add(("confusion",))
        world.get("pilot").memes["worry"] += 1
        world.get("navigator").memes["worry"] += 1
        out.append("The tiny ship felt stuck for a moment.")
    return out


CAUSAL_RULES = [(_r_confusion, "social")]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn, _tag in CAUSAL_RULES:
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    misunderstanding: str
    solution: str
    pilot: str
    navigator: str
    parent: str
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


PLACES = {
    "station": Place("station", "the moon station", "silver lights", "the ring hallway", religion=True, tags={"space", "station", "religion"}),
    "ship": Place("ship", "the tiny ship", "blue gauges", "the launch bay", tags={"space", "ship"}),
    "dome": Place("dome", "the glass dome", "warm stars", "the map table", tags={"space", "dome"}),
}

CLUES = {
    "label": Clue("label", "destine", "meant to go to a place", tags={"destine"}),
    "map": Clue("map", "the route marker", "the line on the map showing where to go", tags={"map"}),
    "radio": Clue("radio", "the radio note", "the message that names the landing spot", tags={"radio"}),
}

PILOTS = ["Ari", "Mina", "Noa", "Tali", "Juno", "Kai"]
NAVS = ["Bo", "Lumi", "Suri", "Pip", "Rin", "Zed"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, "solve") for p in PLACES for c in CLUES]


def explain_rejection() -> str:
    return "(No story: the chosen pieces do not make a clear space problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space story world with religion, destine, repetition, misunderstanding, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--pilot")
    ap.add_argument("--navigator")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    pilot = args.pilot or rng.choice(PILOTS)
    navigator = args.navigator or rng.choice([n for n in NAVS if n != pilot])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, clue, "mixup", "solve", pilot, navigator, parent)


def tell(params: StoryParams) -> World:
    world = World()
    pilot = world.add(Entity(id=params.pilot, kind="character", type="boy", role="pilot"))
    navigator = world.add(Entity(id=params.navigator, kind="character", type="girl", role="navigator"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))

    place = PLACES[params.place]
    clue = CLUES[params.clue]

    pilot.memes["hope"] += 1
    navigator.memes["care"] += 1

    world.say(
        f"{pilot.id} and {navigator.id} floated through {place.label}. "
        f"The station lights blinked soft and calm, and a quiet room for religion sat farther down the hall, "
        f"where people could sit still, whisper, and rest."
    )
    world.say(
        f'They had one little note: "{clue.phrase}." {pilot.id} read it again and again: '
        f'{repeat_line(clue.phrase)}.'
    )

    world.para()
    world.say(
        f"{pilot.id} pointed at the note. \"It says {clue.phrase}! That means the ship is destine "
        f"to stay here,\" {pilot.id} said."
    )
    world.say(
        f"{navigator.id} frowned. \"Maybe it means the ship is destine for {place.route}, not stuck forever,\" "
        f"{navigator.id} said."
    )
    world.say(
        f'They read it again: "{clue.phrase}." Then again: "{clue.phrase}." '
        f'The repeated words made the clue feel clearer, not trickier.'
    )
    world.facts["confused"] = True
    propagate(world)

    world.para()
    if clue.id == "label":
        world.say(
            f"{navigator.id} tapped the map table. \"Look. destine means meant to go. "
            f"The note is not about being trapped. It is about where we should fly.\""
        )
    elif clue.id == "map":
        world.say(
            f"{parent.label_word.capitalize()} came closer and pointed to the route marker. "
            f"\"The line says where to go. The ship is not lost; it just needed a careful reader.\""
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} checked the radio note and smiled. "
            f"\"This message is not a riddle. It names the landing spot, so we can choose the right path.\""
        )

    world.say(
        f"Together they solved the mix-up. {pilot.id} steered, {navigator.id} checked the labels, "
        f"and the little ship drifted toward {place.glow} with a bright new plan."
    )
    world.say(
        f"By the end, the station felt bigger and friendlier. Even the room for religion seemed gentle and calm, "
        f"and the explorers knew that careful reading could turn a confusing note into a safe trip."
    )

    world.facts.update(
        pilot=pilot, navigator=navigator, parent=parent, place=place, clue=clue,
        misunderstanding="destine", outcome="solved"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a young child that includes the words "religion" and "destine" and has a misunderstanding that gets solved.',
        f"Tell a story where {f['pilot'].id} and {f['navigator'].id} keep repeating a clue, get confused by the word destine, and then figure it out together.",
        f'Write a gentle astronaut story with a quiet space station, a repeated note, and a problem solved by careful reading.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pilot = f["pilot"]
    nav = f["navigator"]
    place = f["place"]
    clue = f["clue"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {pilot.id} and {nav.id}, two little space explorers who were trying to understand a clue. They worked together at {place.label}."
        ),
        QAItem(
            question="What was misunderstood?",
            answer=f"{pilot.id} misunderstood the word destine. {pilot.id} thought it meant stuck in one place, but it really meant meant to go somewhere."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They repeated the clue again and again, then checked the map and labels. That careful reading showed them the right route and fixed the mix-up."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is religion?",
            answer="Religion is a way that some people practice faith, prayer, and special customs. Different people have different religions, and they are all part of life in many places."
        ),
        QAItem(
            question="What does destine mean?",
            answer="Destine means meant to go somewhere or meant to happen. In a space story, it can be a clue about the place a ship should travel to."
        ),
        QAItem(
            question="Why is repeating a clue helpful?",
            answer="Repeating a clue can help you notice the words more clearly. If something sounded confusing the first time, saying it again can make the meaning easier to see."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        memes = {k: v for k, v in e.memes.items() if v}
        if memes:
            lines.append(f"  {e.id}: {memes}")
        else:
            lines.append(f"  {e.id}:")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place(P), clue(C)) :- place(P), clue(C).
confused :- clue(destine).
solved :- confused.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2.\n#show solved/0."))
    _ = asp.atoms(model, "valid")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(exc)
        return 1
    print("OK: ASP helper works and generation smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("station", "label", "mixup", "solve", "Ari", "Lumi", "mother"),
    StoryParams("dome", "map", "mixup", "solve", "Kai", "Bo", "father"),
    StoryParams("ship", "radio", "mixup", "solve", "Mina", "Suri", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        clue=args.clue or rng.choice(list(CLUES)),
        misunderstanding="mixup",
        solution="solve",
        pilot=args.pilot or rng.choice(PILOTS),
        navigator=args.navigator or rng.choice([n for n in NAVS if n != (args.pilot or "")]),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with religion, destine, repetition, misunderstanding, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--pilot")
    ap.add_argument("--navigator")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
