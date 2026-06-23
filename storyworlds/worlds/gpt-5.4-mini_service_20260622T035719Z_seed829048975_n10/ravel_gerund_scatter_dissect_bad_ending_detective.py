#!/usr/bin/env python3
"""
storyworlds/worlds/ravel_gerund_scatter_dissect_bad_ending_detective.py
=======================================================================

A small detective storyworld about a child sleuth, a clue board, and a bad
ending where the case falls apart. The world uses typed entities with physical
meters and emotional memes, a small causal model, grounded QA, and an inline ASP
twin for the reasonableness gate.

Seed premise:
- Detective-style mystery
- Required words: ravel-gerund, scatter, dissect
- Feature: Bad Ending

Core idea:
A young detective follows a trail of clues in a tiny neighborhood case. If the
case is well-formed, the clues can be raveled into a thread, then scattered by
a windy setback, then dissected by careful sorting. But because the requested
feature is a bad ending, the story resolves with the clues too damaged to solve
the case, leaving the detective with a ruined notebook and a missed answer.

This file is standalone and stdlib-only apart from the shared Storyweavers
results helper and optional clingo-backed ASP helper.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    weather: str
    clue_spot: str
    quiet_spot: str
    wind_spot: str
    thread_name: str
    style: str = "Detective Story"
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueSet:
    id: str
    label: str
    phrase: str
    thread: str
    scatter_source: str
    dissect_tool: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class BadEnd:
    id: str
    label: str
    crack: str
    loss: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: _copy_entity(v) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(x) for x in self.history]
        clone.paragraphs = [list(p) for p in self.paragraphs]
        clone.fired = set(self.fired)
        return clone


def _copy_entity(e: Entity) -> Entity:
    return Entity(
        id=e.id, kind=e.kind, type=e.type, label=e.label, phrase=e.phrase,
        traits=list(e.traits), role=e.role, owner=e.owner, caretaker=e.caretaker,
        plural=e.plural, tags=set(e.tags), attrs=dict(e.attrs),
        meters=defaultdict(float, e.meters), memes=defaultdict(float, e.memes),
    )


@dataclass
class StoryParams:
    scene: str
    clueset: str
    badend: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seed: int | None = None


SCENES = {
    "alley": Scene("alley", "the old alley", "windy", "the brick wall", "the quiet stoop", "the open gate", "thread", tags={"wind", "street"}),
    "library": Scene("library", "the little library", "quiet", "the back table", "the reading corner", "the doorway", "thread", tags={"paper", "quiet"}),
    "porch": Scene("porch", "the front porch", "blowy", "the railing", "the bench", "the screen door", "thread", tags={"wind", "home"}),
}

CLUESETS = {
    "notebook": ClueSet("notebook", "a detective notebook", "a fresh detective notebook", "thread", "wind", "magnifier", tags={"paper", "clue"}),
    "photos": ClueSet("photos", "photo prints", "three photo prints", "thread", "wind", "magnifier", tags={"paper", "clue"}),
    "tickets": ClueSet("tickets", "bus tickets", "two bus tickets", "thread", "wind", "tweezers", tags={"paper", "clue"}),
}

BADENDS = {
    "missed": BadEnd("missed", "a missed case", "the clue trail broke apart", "the answer was lost", "A detective must protect clues before the wind gets them", tags={"bad", "wind"}),
    "muddy": BadEnd("muddy", "a muddy loss", "the page smeared in rain", "the notes could not be read", "A detective must keep evidence dry and neat", tags={"bad", "paper"}),
}

DETECTIVE_NAMES = ["Mia", "Nora", "Ivy", "Ada", "Elsa", "June", "Leo", "Finn", "Owen", "Max"]
HELPER_NAMES = ["Ben", "Zoe", "Pip", "Tess", "Sam", "Lia", "Noah", "Eve"]
TRAITS = ["careful", "curious", "patient", "sharp-eyed"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SCENES:
        for c in CLUESETS:
            for b in BADENDS:
                combos.append((s, c, b))
    return combos


def tell(scene: Scene, clueset: ClueSet, badend: BadEnd,
         detective: str, detective_gender: str,
         helper: str, helper_gender: str) -> World:
    world = World()
    d = world.add(Entity(id=detective, kind="character", type=detective_gender, role="detective", traits=["little", "sharp-eyed"]))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper", traits=["little", "helpful"]))
    board = world.add(Entity(id="board", type="board", label="the clue board"))
    clue = world.add(Entity(id="clue", type="clue", label=clueset.label, phrase=clueset.phrase, owner=d.id, caretaker=d.id, tags=set(clueset.tags)))
    fan = world.add(Entity(id="fan", type="thing", label="the ceiling fan"))
    notebook = clue
    world.facts["scene"] = scene
    world.facts["clueset"] = clueset
    world.facts["badend"] = badend
    world.facts["detective"] = d
    world.facts["helper"] = h
    world.facts["board"] = board
    world.facts["clue"] = clue
    world.facts["fan"] = fan
    world.facts["notebook"] = notebook

    d.memes["focus"] = 1
    h.memes["curiosity"] = 1

    world.say(f"{d.id} was a little detective who kept a {clueset.label} close and looked for patterns in every tiny thing.")
    world.say(f"{h.id} stayed near {d.pronoun('possessive')} side, ready to help at {scene.place}.")
    world.say(f"That day, the case began at {scene.place}, where {scene.clue_spot} held the first good clue.")
    world.para()

    _ravel(world, d, clue, scene)
    _scatter(world, d, clue, scene)
    _dissect(world, d, h, clue, clueset)
    world.para()
    _bad_ending(world, d, h, clue, badend, scene)
    world.facts["resolved"] = False
    world.facts["ended_bad"] = True
    return world


def _ravel(world: World, detective: Entity, clue: Entity, scene: Scene) -> None:
    detective.memes["focus"] += 1
    clue.meters["together"] += 1
    world.event("ravel", who=detective.id, clue=clue.id, place=scene.place)
    world.say(f"{detective.id} started {scene.thread_name}-raveling the case, pulling the notes into one neat thread.")
    world.say(f"The clues looked linked for a moment, as if the whole mystery could be read in one long line.")


def _scatter(world: World, detective: Entity, clue: Entity, scene: Scene) -> None:
    clue.meters["scattered"] += 1
    clue.memes["order"] -= 1
    world.event("scatter", who=detective.id, clue=clue.id, place=scene.wind_spot)
    world.say(f"Then a sudden gust at {scene.wind_spot} made the papers scatter across the floor.")
    world.say(f"{detective.id} lunged after them, but the neat trail broke into slips and corners.")


def _dissect(world: World, detective: Entity, helper: Entity, clue: Entity, clueset: ClueSet) -> None:
    clue.meters["sorted"] += 1
    helper.memes["help"] += 1
    detective.memes["worry"] += 1
    world.event("dissect", who=detective.id, helper=helper.id, clue=clue.id)
    world.say(f"{helper.id} tried to dissect the evidence piece by piece, lining each scrap beside the magnifier.")
    world.say(f"But the wind had already bent the edges, and the hidden message was no longer easy to read.")


def _bad_ending(world: World, detective: Entity, helper: Entity, clue: Entity, badend: BadEnd, scene: Scene) -> None:
    detective.memes["sadness"] += 2
    helper.memes["sadness"] += 1
    clue.meters["ruined"] += 1
    world.say(f"In the end, the case closed the wrong way: {badend.crack}.")
    world.say(f"{badend.loss.capitalize()}, and {detective.id} stood under {scene.quiet_spot} with an empty stare and a torn page.")
    world.say(f"{badend.lesson}.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d, h, scene, clueset, badend = f["detective"], f["helper"], f["scene"], f["clueset"], f["badend"]
    return [
        f'Write a short detective story for a young child that includes the words "ravel-gerund", "scatter", and "dissect".',
        f"Tell a tiny mystery where {d.id} and {h.id} work at {scene.place}, but the clues {badend.crack} before the answer is found.",
        f"Write a detective story with a bad ending where {clueset.label} are hard to read after they scatter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, scene, clueset, badend = f["detective"], f["helper"], f["scene"], f["clueset"], f["badend"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery at {scene.place}?",
            answer=f"It was {d.id}, a little detective, with {h.id} helping nearby. They were working on {clueset.label}, but the case never stayed neat for long.",
        ),
        QAItem(
            question=f"What happened after {d.id} started raveling the clues?",
            answer=f"The clues looked tied together for a moment, but then a gust made them scatter. That meant the trail became messy before the detective could finish the job.",
        ),
        QAItem(
            question=f"Why couldn't {h.id} dissect the evidence and find the answer?",
            answer=f"The papers had already scattered and bent in the wind, so the pieces were hard to sort. Without a clean trail, the answer stayed hidden.",
        ),
        QAItem(
            question=f"How did the story end for {d.id}?",
            answer=f"It ended badly. The clue trail broke apart, the page was ruined, and {d.id} was left with a mystery that could not be solved that day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    clueset = f["clueset"]
    out: list[QAItem] = []
    if "wind" in scene.tags:
        out.append(QAItem(
            question="What does wind sometimes do to paper clues?",
            answer="Wind can blow paper clues away and make them scatter. That is why a detective has to hold evidence carefully.",
        ))
    if "paper" in clueset.tags:
        out.append(QAItem(
            question="Why should a detective keep paper evidence flat?",
            answer="Paper evidence should stay flat so the writing is easy to read. If it bends or tears, the clues can be lost.",
        ))
    out.append(QAItem(
        question="What does it mean to dissect clues?",
        answer="To dissect clues means to look at each piece closely and sort them one by one. A detective does that to find patterns and hidden meaning.",
    ))
    return out


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="alley", clueset="notebook", badend="missed", detective="Mia", detective_gender="girl", helper="Ben", helper_gender="boy", seed=1),
    StoryParams(scene="library", clueset="photos", badend="muddy", detective="Leo", detective_gender="boy", helper="Zoe", helper_gender="girl", seed=2),
]


def explain_rejection(scene: Scene, clueset: ClueSet) -> str:
    return f"(No story: {clueset.label} would not make a good detective mystery at {scene.place}.)"


def valid_story(params: StoryParams) -> bool:
    return params.scene in SCENES and params.clueset in CLUESETS and params.badend in BADENDS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.clueset and not valid_story(StoryParams(scene=args.scene, clueset=args.clueset, badend=args.badend or "missed", detective="Mia", detective_gender="girl", helper="Ben", helper_gender="boy")):
        raise StoryError(explain_rejection(SCENES[args.scene], CLUESETS[args.clueset]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.clueset is None or c[1] == args.clueset)
              and (args.badend is None or c[2] == args.badend)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene_id, clueset_id, badend_id = rng.choice(sorted(combos))
    dgender = args.detective_gender or rng.choice(["girl", "boy"])
    hgender = args.helper_gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != detective])
    return StoryParams(
        scene=scene_id,
        clueset=clueset_id,
        badend=badend_id,
        detective=detective,
        detective_gender=dgender,
        helper=helper,
        helper_gender=hgender,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("(Invalid story parameters.)")
    world = tell(SCENES[params.scene], CLUESETS[params.clueset], BADENDS[params.badend], params.detective, params.detective_gender, params.helper, params.helper_gender)
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
    ap = argparse.ArgumentParser(description="Detective storyworld with a bad ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clueset", choices=CLUESETS)
    ap.add_argument("--badend", choices=BADENDS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


ASP_RULES = r"""
scene(S) :- scene_fact(S).
clueset(C) :- clueset_fact(C).
badend(B) :- badend_fact(B).
valid(S,C,B) :- scene(S), clueset(C), badend(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene_fact", s))
    for c in CLUESETS:
        lines.append(asp.fact("clueset_fact", c))
    for b in BADENDS:
        lines.append(asp.fact("badend_fact", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        ok = False
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    if ok:
        print("OK: verify passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
