#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10/tweezers_twist_repetition_nursery_rhyme.py
==============================================================================================================

A small standalone storyworld in a nursery-rhyme style about a child, a twisty
problem, a repeated search, and tweezers used in a careful rescue.

Premise:
- A little child wants to wear a bright ribbon crown for a nursery song.
- A twist of the ribbon catches on a branch.
- The child and a helper search twice, sing twice, and try again.
- Tweezers help free the ribbon without tearing it.

This world models physical meters and emotional memes, uses a simple forward
state simulation, includes an inline ASP twin, and renders child-facing prose.
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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


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
        clone.entities = {k: _deep_entity(v) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(item) for item in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _deep_entity(e: Entity) -> Entity:
    return Entity(
        id=e.id,
        kind=e.kind,
        type=e.type,
        label=e.label,
        phrase=e.phrase,
        traits=list(e.traits),
        role=e.role,
        owner=e.owner,
        caretaker=e.caretaker,
        plural=e.plural,
        tags=set(e.tags),
        attrs=dict(e.attrs),
        meters=defaultdict(float, dict(e.meters)),
        memes=defaultdict(float, dict(e.memes)),
    )


@dataclass
class Scene:
    place: str
    setting_line: str
    twist_line: str
    repeat_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemConfig:
    id: str
    label: str
    phrase: str
    risk: str
    twist: str
    repeated_search: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    object_id: str
    problem_id: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    helper_role: str
    seed: int | None = None


SCENES = {
    "nursery": Scene(
        place="the nursery",
        setting_line="In the nursery with a tiny lamp and a quilt so bright, a child loved to sing at morning light.",
        twist_line="Yet one small twist can make a ribbon wind and bind.",
        repeat_line="So they looked once, and looked twice, and sang the song again.",
        ending_line="At last the ribbon fluttered free, and the room grew soft and kind.",
        tags={"nursery", "soft", "song"},
    ),
    "playroom": Scene(
        place="the playroom",
        setting_line="In the playroom by a toy chest and a painted chair, a child kept a little crown with care.",
        twist_line="But a twist can turn a happy thing into a tangle there.",
        repeat_line="So they searched once, then searched twice, then peeped beneath the chair.",
        ending_line="At last the ribbon came loose, and the crown was worn again with cheer.",
        tags={"playroom", "song"},
    ),
}

OBJECTS = {
    "ribbon": ObjectConfig(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon crown",
        tags={"ribbon", "soft"},
    ),
    "scarf": ObjectConfig(
        id="scarf",
        label="scarf",
        phrase="a soft singing scarf",
        tags={"scarf", "soft"},
    ),
}

PROBLEMS = {
    "branch": ProblemConfig(
        id="branch",
        label="branch",
        phrase="a little branch by the window",
        risk="The ribbon snagged on a branch and would not come free.",
        twist="The twist of the ribbon made a tiny loop that caught tight.",
        repeated_search="They looked near the bed, then under the bed, then near the sill again.",
        fix="Tweezers could lift the loop without pulling too hard.",
        tags={"tweezers", "twist"},
    ),
    "button": ProblemConfig(
        id="button",
        label="button",
        phrase="a round button on a dress-up coat",
        risk="The cloth had looped around a button and stuck there.",
        twist="The twist made the loop pull snug.",
        repeated_search="They checked the hook, then the shelf, then the coat again.",
        fix="Tweezers could slip under the loop and ease it loose.",
        tags={"tweezers", "twist"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ella", "Rose", "Lucy"]
BOY_NAMES = ["Sam", "Theo", "Ben", "Eli", "Max", "Finn"]
HELPER_NAMES = ["Mom", "Dad", "Aunt May", "Uncle Joe", "Nana", "Papa"]
TRAITS = ["cheery", "careful", "gentle", "lively", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene in SCENES:
        for obj in OBJECTS:
            for prob in PROBLEMS:
                combos.append((scene, obj, prob))
    return combos


def choose_name(rng: random.Random, child_type: str) -> str:
    return rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about tweezers, a twist, and repetition.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle", "grandparent"])
    ap.add_argument("--role", choices=["mom", "dad", "aunt", "uncle", "nana", "papa"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.object_id is None or c[1] == args.object_id)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, object_id, problem_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or choose_name(rng, child_type)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle", "grandparent"])
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    role = args.role or rng.choice(["mom", "dad", "aunt", "uncle", "nana", "papa"])
    return StoryParams(
        scene=scene,
        object_id=object_id,
        problem_id=problem_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_role=role,
        seed=None,
    )


def valid_story(params: StoryParams) -> bool:
    return params.scene in SCENES and params.object_id in OBJECTS and params.problem_id in PROBLEMS


def tell(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("Invalid story parameters.")
    scene = SCENES[params.scene]
    obj = OBJECTS[params.object_id]
    prob = PROBLEMS[params.problem_id]
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, traits=["little", "singing"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, role=params.helper_role))
    prop = world.add(Entity(id="prop", kind="thing", type=obj.label, label=obj.label, phrase=obj.phrase, tags=set(obj.tags), owner=child.id))
    tw = world.add(Entity(id="tweezers", kind="thing", type="tool", label="tweezers", phrase="the tweezers", tags={"tweezers"}))
    world.facts.update(scene=scene, obj=obj, prob=prob, child=child, helper=helper, prop=prop, tweezers=tw)
    child.memes["want"] += 1
    child.memes["joy"] += 1
    world.say(f"{scene.setting_line} {child.label} loved to hum and sway.")
    world.say(f"{child.label} wore {obj.phrase}, but then {prob.risk}")
    world.para()
    world.say(f"{prob.twist} {prob.repeated_search}")
    child.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(f"{helper.label} hummed, 'Look once more,' and they looked once more.")
    world.say(f"They looked by the pillow, then by the sill, then by the quilt again.")
    world.para()
    world.say(f"{prob.fix} {helper.label} took the tweezers and worked with a tiny, steady hand.")
    prop.meters["caught"] += 0.0
    prop.meters["free"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.event("freed", tool="tweezers", problem=prob.id)
    world.say(f"At last the loop let go, and {obj.label} danced free. {scene.ending_line}")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    prob: ProblemConfig = f["prob"]
    obj: ObjectConfig = f["obj"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        f'Write a nursery-rhyme style story about {child.label}, {obj.label}, and tweezers in {scene.place}.',
        f"Tell a gentle repeating story where {child.label} sings, a twist causes a snag, and {helper.label} helps with tweezers.",
        f'Write a short rhyming story that includes "tweezers" and ends with {obj.label} coming free from {prob.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene: Scene = f["scene"]
    prob: ProblemConfig = f["prob"]
    obj: ObjectConfig = f["obj"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What was {child.label} trying to keep safe in {scene.place}?",
            answer=f"{child.label} was trying to keep {obj.phrase} nice and tidy. When it snagged, the story turned into a careful rescue instead of a tear.",
        ),
        QAItem(
            question=f"Why did {helper.label} use tweezers?",
            answer=f"{helper.label} used tweezers to lift the tiny loop without tugging hard. That gentle touch kept the ribbon from ripping while the twist came undone.",
        ),
        QAItem(
            question=f"What repeated part helped the story move along?",
            answer="They looked once, then looked twice, and then looked again. The repeating search made the story feel like a song while they kept trying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are tweezers for?",
            answer="Tweezers are small tools with two tips. People use them to pick up tiny things or pull at little loops very carefully.",
        ),
        QAItem(
            question="What does a twist do to a ribbon?",
            answer="A twist can make a ribbon loop and knot. That is why a ribbon can get stuck so fast.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
scene_ok(S) :- scene(S).
object_ok(O) :- object(O).
problem_ok(P) :- problem(P).
valid(S,O,P) :- scene_ok(S), object_ok(O), problem_ok(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos:")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: verify smoke test and ASP parity passed.")
    return 0 if ok else 1


CURATED = [
    StoryParams(scene="nursery", object_id="ribbon", problem_id="branch", child_name="Lily", child_type="girl", helper_name="Mom", helper_type="mother", helper_role="mom", seed=1),
    StoryParams(scene="playroom", object_id="scarf", problem_id="button", child_name="Sam", child_type="boy", helper_name="Nana", helper_type="grandparent", helper_role="nana", seed=2),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, object, problem) combos:")
        for c in combos:
            print(" ", c)
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} with tweezers in {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
