#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deceive_priority_transformation_slice_of_life.py
=================================================================================

A small slice-of-life storyworld about a child, a hidden worry, and a gentle
transformation from ordinary things into something useful.

Seed words:
- deceive
- priority

Feature:
- Transformation

Style:
- Slice of Life
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    transformed: bool = False
    honest: bool = True

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
class Scene:
    id: str
    place: str
    mood: str
    ordinary: str
    transformed: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Priority:
    id: str
    concern: str
    why: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    from_word: str
    to_word: str
    method: str
    result: str
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_transform(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if not ent.transformed or ent.meters["made"] < THRESHOLD:
            continue
        sig = ("transformed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["pride"] += 1
        out.append("__transformed__")
    return out


CAUSAL_RULES = [Rule("transform", _r_transform)]


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


def predict_mess(world: World) -> bool:
    sim = world.copy()
    return sim.get("thing").meters["made"] >= THRESHOLD and sim.get("child").memes["dishonesty"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for pr in PRIORITIES:
            for tr in TRANSFORMATIONS:
                if pr.id == "clean_first" and tr.id in {"cardboard_stage", "paper_flower", "rain_boot_art"}:
                    combos.append((scene.id, pr.id, tr.id))
                if pr.id == "be_honest" and tr.id in {"cardboard_stage", "paper_flower"}:
                    combos.append((scene.id, pr.id, tr.id))
    return combos


@dataclass
class StoryParams:
    scene: str
    priority: str
    transformation: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


SCENES = [
    Scene("kitchen_table", "the kitchen table", "busy", "a plain cardboard box", "a tiny puppet stage", {"indoor", "craft"}),
    Scene("porch", "the porch", "soft", "a paper bag", "a flower crown", {"outdoor", "craft"}),
    Scene("living_room", "the living room", "quiet", "a pair of old rain boots", "a bright painted planter", {"indoor", "home"}),
]

PRIORITIES = [
    Priority("clean_first", "cleaning up the spill", "the floor would be slippery otherwise", "wipe the juice first", {"clean", "honest"}),
    Priority("be_honest", "telling the truth about the broken cup", "grown-ups can fix things better when they know the truth", "say what happened right away", {"honest"}),
    Priority("snack_first", "sharing a snack before play", "everyone gets calmer after a small snack", "finish the apple slices", {"snack"}),
]

TRANSFORMATIONS = [
    Transformation("cardboard_stage", "box", "puppet stage", "folding, taping, and drawing curtains", "the box becomes a tiny puppet stage", {"craft"}),
    Transformation("paper_flower", "bag", "flower crown", "cutting petals and stringing them together", "the bag becomes a flower crown", {"craft"}),
    Transformation("rain_boot_art", "boots", "planter", "painting and filling", "the boots become a bright planter", {"home"}),
]

CHILDREN = [("Mina", "girl"), ("Owen", "boy"), ("Tara", "girl"), ("Noah", "boy")]
ADULTS = [("Mom", "mother"), ("Dad", "father")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life transformation storyworld.")
    ap.add_argument("--scene", choices=[s.id for s in SCENES])
    ap.add_argument("--priority", choices=[p.id for p in PRIORITIES])
    ap.add_argument("--transformation", choices=[t.id for t in TRANSFORMATIONS])
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
              if (args.scene is None or c[0] == args.scene)
              and (args.priority is None or c[1] == args.priority)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, priority, transformation = rng.choice(sorted(combos))
    child_name, child_gender = rng.choice(CHILDREN)
    adult_name, adult_gender = rng.choice(ADULTS)
    return StoryParams(scene=scene, priority=priority, transformation=transformation,
                       child_name=child_name, child_gender=child_gender,
                       adult_name=adult_name, adult_gender=adult_gender)


def tell(scene: Scene, priority: Priority, transformation: Transformation,
         child_name: str, child_gender: str, adult_name: str, adult_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_gender, label=adult_name, role="adult"))
    thing = world.add(Entity(id="thing", kind="thing", type="thing", label=transformation.from_word))

    child.memes["curious"] += 1
    child.memes["want"] += 1
    world.say(
        f"{child_name} was at {scene.place}, where the day felt {scene.mood} and ordinary."
    )
    world.say(
        f"{child_name} had a small idea: make {scene.ordinary} into {scene.transformed}."
    )
    world.para()
    world.say(
        f"Then {child_name} noticed a different priority. {adult_name} said, "
        f'"{priority.action}. {priority.why}."'
    )
    child.memes["deceive"] += 1
    world.say(
        f"{child_name} almost tried to deceive {adult_name} and hide the mess, but "
        f"{child_name} looked at the floor and stopped."
    )
    world.say(
        f'"You are right," {child_name} said. "I will help first."'
    )
    world.para()
    child.meters["made"] += 1
    thing.transformed = True
    world.say(
        f"Together they spent a little while {transformation.method}, and the ordinary thing changed."
    )
    propagate(world, narrate=False)
    world.say(
        f"{transformation.result.capitalize()}, and the room felt neat again."
    )
    world.say(
        f"Afterward, {child_name} could enjoy the new {transformation.to_word} with a clear mind."
    )
    world.facts.update(scene=scene, priority=priority, transformation=transformation,
                       child=child, adult=adult, thing=thing)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "deceive" and "priority" and shows {f["child"].label} making a small transformation with craft materials.',
        f"Tell a gentle everyday story where {f['child'].label} learns that {f['priority'].concern} is the priority before play, then turns an ordinary thing into something useful.",
        f"Write a short story about a child who almost tries to deceive a grown-up, but then chooses honesty and a simple transformation instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    pr = f["priority"]
    tr = f["transformation"]
    return [
        ("What did the child want to make?", f"{child.label} wanted to make {f['scene'].transformed} from {f['scene'].ordinary}."),
        ("What was the priority?", f"{pr.concern} was the priority, because {pr.why}."),
        ("Did the child deceive the grown-up?", f"{child.label} almost tried to deceive {adult.label}, but stopped and told the truth instead."),
        ("What changed by the end?", f"The ordinary thing became {tr.result}, and the room felt tidy and peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to transform something?", "To transform something means to change it into a different form or use. A plain thing can become something new with a little work."),
        ("Why is honesty important?", "Honesty helps other people know what is really happening. That makes it easier to solve problems together."),
        ("What is a priority?", "A priority is the thing that should be done first because it matters most right now."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- scene(S), priority(P), transformation(T), compatible(P,T).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s.id))
    for p in PRIORITIES:
        lines.append(asp.fact("priority", p.id))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t.id))
    for p in PRIORITIES:
        for t in TRANSFORMATIONS:
            if p.id == "clean_first" and t.id in {"cardboard_stage", "paper_flower", "rain_boot_art"}:
                lines.append(asp.fact("compatible", p.id, t.id))
            if p.id == "be_honest" and t.id in {"cardboard_stage", "paper_flower"}:
                lines.append(asp.fact("compatible", p.id, t.id))
            if p.id == "snack_first" and t.id in {"paper_flower", "rain_boot_art"}:
                lines.append(asp.fact("compatible", p.id, t.id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import io
    old = sys.stdout
    try:
        world = tell(SCENES[0], PRIORITIES[0], TRANSFORMATIONS[0], "Mina", "girl", "Mom", "mother")
        _ = world.render()
        sample = generate(StoryParams(scene=SCENES[0].id, priority=PRIORITIES[0].id, transformation=TRANSFORMATIONS[0].id, child_name="Mina", child_gender="girl", adult_name="Mom", adult_gender="mother"))
        assert sample.story
        print("OK: smoke test story generation worked.")
    finally:
        sys.stdout = old
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        return 1
    print("OK: ASP and Python valid-combos agree.")
    return 0


def generate(params: StoryParams) -> StorySample:
    scene = next((s for s in SCENES if s.id == params.scene), None)
    priority = next((p for p in PRIORITIES if p.id == params.priority), None)
    transformation = next((t for t in TRANSFORMATIONS if t.id == params.transformation), None)
    if not scene or not priority or not transformation:
        raise StoryError("Invalid StoryParams value.")
    world = tell(scene, priority, transformation, params.child_name, params.child_gender, params.adult_name, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.priority is None or c[1] == args.priority)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, priority, transformation = rng.choice(sorted(combos))
    child_name, child_gender = rng.choice(CHILDREN)
    adult_name, adult_gender = rng.choice(ADULTS)
    return StoryParams(scene=scene, priority=priority, transformation=transformation,
                       child_name=child_name, child_gender=child_gender,
                       adult_name=adult_name, adult_gender=adult_gender)


def generate_default_sample(seed: int) -> StorySample:
    return generate(StoryParams(
        scene=SCENES[0].id,
        priority=PRIORITIES[0].id,
        transformation=TRANSFORMATIONS[0].id,
        child_name="Mina",
        child_gender="girl",
        adult_name="Mom",
        adult_gender="mother",
        seed=seed,
    ))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for p in PRIORITIES:
            for t in TRANSFORMATIONS:
                if p.id == "clean_first" and t.id in {"cardboard_stage", "paper_flower", "rain_boot_art"}:
                    combos.append((s.id, p.id, t.id))
                if p.id == "be_honest" and t.id in {"cardboard_stage", "paper_flower"}:
                    combos.append((s.id, p.id, t.id))
                if p.id == "snack_first" and t.id in {"paper_flower", "rain_boot_art"}:
                    combos.append((s.id, p.id, t.id))
    return combos


def build_parser2() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(scene="kitchen_table", priority="clean_first", transformation="cardboard_stage", child_name="Mina", child_gender="girl", adult_name="Mom", adult_gender="mother"),
            StoryParams(scene="porch", priority="be_honest", transformation="paper_flower", child_name="Owen", child_gender="boy", adult_name="Dad", adult_gender="father"),
            StoryParams(scene="living_room", priority="snack_first", transformation="rain_boot_art", child_name="Tara", child_gender="girl", adult_name="Mom", adult_gender="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
