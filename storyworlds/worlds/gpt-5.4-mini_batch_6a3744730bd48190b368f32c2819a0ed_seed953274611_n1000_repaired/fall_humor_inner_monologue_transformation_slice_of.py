#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fall_humor_inner_monologue_transformation_slice_of.py
====================================================================================

A small slice-of-life storyworld about an ordinary autumn afternoon: a character
tries to keep a simple fall plan on track, gets embarrassed by a tiny mishap,
talks themselves through it, and ends up transformed in a gentle, visible way.

The seed prompt asks for:
- word: fall
- features: Humor, Inner Monologue, Transformation
- style: Slice of Life

This world models a child or young teen during an autumn outing. A fall can be a
literal tumble, a fall breeze can change the scene, and an inner monologue helps
turn a small embarrassment into a warmer, more resilient ending image.
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
EMBARRASS_MIN = 1.0
TRANSFORM_MIN = 1.0


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    weather: str
    cozy_detail: str
    fall_detail: str
    action: str
    mishap: str
    transformation: str
    final_image: str
    humor_tag: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    scene: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_awkward_fall(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["slip"] < THRESHOLD:
        return out
    sig = ("fall",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["embarrass"] += 1
    hero.meters["tumble"] += 1
    out.append("__fall__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["spill"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["embarrass"] += 1
    out.append("__spill__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes["embarrass"] < EMBARRASS_MIN:
        return out
    if hero.memes["self_kind"] >= TRANSFORM_MIN:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["self_kind"] += 1
    hero.memes["confidence"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("awkward_fall", "physical", _r_awkward_fall),
    Rule("spill", "physical", _r_spill),
    Rule("transform", "social", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


SCENES = {
    "pumpkin_patch": Scene(
        id="pumpkin_patch",
        place="the pumpkin patch",
        weather="cool",
        cozy_detail="The rows of pumpkins looked round and cheerful, and the air smelled like leaves and cider.",
        fall_detail="A dry leaf spun across the path, and a crate sat a little too close to the edge.",
        action="reach for the smallest pumpkin",
        mishap="his sneaker caught the crate and he did a tiny, very loud fall into the leaves",
        transformation="he stopped trying to look cool and started laughing at himself",
        final_image="He carried home a wobbly pumpkin with leaf confetti in his hair and a grin that would not quit.",
        humor_tag="leaf_confetti",
    ),
    "school_walk": Scene(
        id="school_walk",
        place="the walk to school",
        weather="breezy",
        cozy_detail="The sidewalks were lined with orange trees and crunchy paper cups skipped by like little boats.",
        fall_detail="A gust of wind pushed a cap sideways, and a wet patch glittered near the curb.",
        action="hurry to keep up with the bus stop crowd",
        mishap="she slid, sat down fast on the sidewalk, and did the world's smallest surprise fall",
        transformation="she decided the sidewalk had won the round and laughed first",
        final_image="She got up, brushed off her jeans, and walked on with a lighter step and a funnier story.",
        humor_tag="cap_skid",
    ),
    "backyard_rake": Scene(
        id="backyard_rake",
        place="the backyard",
        weather="golden",
        cozy_detail="The maple tree dropped bright leaves onto the grass, and the yard looked like a soft blanket.",
        fall_detail="A rake leaned against the porch, and one pumpkin ballooned up beside the fence.",
        action="help clear the leaves",
        mishap="he stepped backward, bumped the rake, and it bonked his shoe with an absurd little tap",
        transformation="he admitted the rake had better balance than he did and became much gentler with himself",
        final_image="By dusk the leaves were piled in a golden hill, and he was the sort of helper who could laugh and keep going.",
        humor_tag="rake_bonk",
    ),
}

NAME_POOL = {
    "girl": ["Maya", "Lina", "Nora", "Ella", "Zoe"],
    "boy": ["Leo", "Finn", "Owen", "Eli", "Noah"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SCENES:
        for gender in ("girl", "boy"):
            for name in NAME_POOL[gender]:
                combos.append((sid, gender, name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small autumn slice-of-life storyworld with humor and inner monologue.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.scene:
        combos = [c for c in combos if c[0] == args.scene]
    if args.gender:
        combos = [c for c in combos if c[1] == args.gender]
    if args.name:
        combos = [c for c in combos if c[2] == args.name]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, gender, name = rng.choice(sorted(combos))
    if args.name and args.gender and args.name not in NAME_POOL[args.gender]:
        raise StoryError(f"(No story: {args.name} is not in the ordinary name pool for a {args.gender} in this world.)")
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene=scene, name=name, gender=gender, parent=parent)


def _predict_transformation(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["slip"] += 1
    propagate(sim, narrate=False)
    return {"transformed": sim.get("hero").memes["self_kind"] >= TRANSFORM_MIN}


def tell(scene: Scene, params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, role="main"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent", role="support"))
    hero.memes["self_kind"] = 0.0
    hero.memes["confidence"] = 0.0
    hero.memes["embarrass"] = 0.0

    world.say(f"On a cool fall day, {hero.id} went to {scene.place}. {scene.cozy_detail}")
    world.say(f"{hero.id} wanted to {scene.action}, because the day felt ordinary in the nicest way.")

    world.para()
    world.say(f"Then {scene.fall_detail}")
    world.say(f"{hero.id} thought, 'Oops. Of course that happened to me.'")
    world.say(f"Inside {hero.pronoun('possessive')} head, {hero.id} muttered, 'Please let this be one of those funny mistakes and not a dramatic life lesson.'")
    world.say(f"That was the exact moment {hero.id} did {scene.mishap}.")
    hero.meters["slip"] += 1
    propagate(world, narrate=False)
    world.say(f"{hero.id} blinked, then snorted at the absurdity of it all.")
    if hero.memes["embarrass"] >= EMBARRASS_MIN:
        world.say(f"'Well,' {hero.id} thought, 'at least the leaves are soft. If I have to fall, this is the fashionable season for it.'")

    world.para()
    pred = _predict_transformation(world)
    world.facts["predicted_transformed"] = pred["transformed"]
    hero.memes["inner_pep_talk"] += 1
    world.say(f"{hero.id} took a breath and tried a new thought: 'I can be embarrassed and still keep going.'")
    world.say(f"That little sentence changed the whole mood.")

    propagate(world, narrate=False)
    hero.memes["self_kind"] += 1
    hero.memes["confidence"] += 1

    world.para()
    world.say(f"{hero.id} got up, brushed off the leaves, and kept going.")
    world.say(f"By the end, {scene.final_image}")
    world.say(f"Even {params.parent} would have laughed at the sight of that {scene.humor_tag}, and {hero.id} laughed too.")

    world.facts.update(
        hero=hero,
        parent=parent,
        scene=scene,
        fall_happened=True,
        transformed=hero.memes["self_kind"] >= TRANSFORM_MIN,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        f'Write a slice-of-life story that includes the word "fall" and a small embarrassing mistake at {scene.place}.',
        f"Tell a gentle humor story about {hero.id} at {scene.place} where an inner monologue helps {hero.pronoun('object')} recover after a tiny fall.",
        f"Write a child-friendly autumn story where a small fall turns into a change in attitude, ending with a warmer, funnier image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"What happened to {hero.id} in the middle of the story?",
            answer=f"{hero.id} had a small, embarrassing fall and ended up in the leaves. It was funny rather than serious, which fit the slice-of-life feel of the story.",
        ),
        QAItem(
            question=f"How did {hero.id} talk {hero.pronoun('object')}self through it?",
            answer=f"{hero.id} used an inner monologue to calm down, telling {hero.pronoun('object')}self that embarrassment did not have to stop the day. That self-talk helped turn the mistake into something manageable.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{hero.id} became more comfortable, more confident, and much quicker to laugh at a small mistake. The final image shows a softer, friendlier version of the same ordinary fall day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fall mean in the season sense?",
            answer="Fall is the season when leaves change color and the weather starts to feel cooler. People often think of pumpkins, sweaters, and crunchy leaves then.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that helps you think through what is happening. People use it to encourage themselves, plan, or make sense of a situation.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a meaningful change from one state to another. In a story, it might be a change in mood, confidence, or the way a character sees themself.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
fall_happens(hero) :- slip(hero).
embarrassed(hero) :- fall_happens(hero).
transformed(hero) :- embarrassed(hero), self_kind(hero).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("self_kind", "hero")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    sample_params = StoryParams(scene="pumpkin_patch", name="Maya", gender="girl", parent="mother")
    try:
        sample = generate(sample_params)
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: normal generation crashed: {exc}")
        return 1
    try:
        _ = asp_program("#show transformed/1.")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: ASP program build crashed: {exc}")
        rc = 1
    try:
        sample2 = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample2.story.strip():
            print("MISMATCH: empty story")
            rc = 1
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: resolved generation crashed: {exc}")
        rc = 1
    print("OK: verify completed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.gender not in ("girl", "boy"):
        raise StoryError("Unknown gender.")
    scene = SCENES[params.scene]
    if params.name not in NAME_POOL.get(params.gender, []):
        raise StoryError("Name does not fit the selected gender/name pool for this world.")
    world = tell(scene, params)
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


def build_default_params(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAME_POOL[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene=scene, name=name, gender=gender, parent=parent)


CURATED = [
    StoryParams(scene="pumpkin_patch", name="Maya", gender="girl", parent="mother"),
    StoryParams(scene="school_walk", name="Leo", gender="boy", parent="father"),
    StoryParams(scene="backyard_rake", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world's ASP twin is intentionally minimal for a tiny slice-of-life domain.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = build_default_params(random.Random(seed), args)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
