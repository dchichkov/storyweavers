#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/extraction_foreshadowing_cautionary_bedtime_story.py
====================================================================================

A tiny standalone storyworld for a bedtime-style cautionary tale about a child,
a small object that needs extraction, and a helpful grown-up who notices the
warning signs early enough to act gently.

The world is built around a few simple constraints:

* a child goes to bed with something stuck, trapped, or tangled;
* the story foreshadows the problem before it becomes scary;
* a cautious grown-up uses the right extraction method;
* the ending proves what changed in the room, the object, and the child.

The prose is state-driven rather than template-swapped: physical meters track
what is stuck, strained, wet, or safely freed, and emotional memes track worry,
relief, trust, and sleepiness.  The renderer turns the simulated world into a
complete bedtime story with a clear beginning, middle turn, and ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/extraction_foreshadowing_cautionary_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/extraction_foreshadowing_cautionary_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/extraction_foreshadowing_cautionary_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/extraction_foreshadowing_cautionary_bedtime_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/extraction_foreshadowing_cautionary_bedtime_story.py --json
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
    age: int = 0
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
class Scene:
    id: str
    room: str
    bedtime_line: str
    object_noun: str
    foreshadow: str
    stuck_reason: str
    extraction_note: str
    gentle_image: str
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
class Problem:
    id: str
    label: str
    stuck_kind: str
    trouble: str
    severity: int
    safe_method: str
    fail_method: str
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
class Rescue:
    id: str
    label: str
    power: int
    text: str
    fail: str
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


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if not child or not parent:
        return out
    if child.meters["stuck"] >= THRESHOLD and parent.memes["calm"] >= THRESHOLD:
        sig = ("trust",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["trust"] += 1
        out.append("__trust__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    obj = world.entities.get("object")
    if not child or not obj:
        return out
    if obj.meters["freed"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["relief"] += 1
        child.memes["sleepy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("trust", "social", _r_trust), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_requires(p: Problem, scene: Scene) -> bool:
    return p.stuck_kind in scene.tags and p.severity >= 1


def select_rescue(p: Problem) -> Optional[Rescue]:
    for r in RESCUES:
        if r.power >= p.severity:
            return r
    return None


def predict(world: World, problem: Problem, rescue: Rescue) -> dict:
    sim = world.copy()
    _attempt_extraction(sim, sim.get("parent"), sim.get("child"), sim.get("object"), problem, rescue, narrate=False)
    obj = sim.get("object")
    child = sim.get("child")
    return {"freed": obj.meters["freed"] >= THRESHOLD, "worry": child.memes["worry"]}


def _attempt_extraction(world: World, parent: Entity, child: Entity, obj: Entity,
                        problem: Problem, rescue: Rescue, narrate: bool = True) -> None:
    child.meters["stuck"] += 1
    obj.meters["stuck"] += 1
    child.memes["worry"] += 1
    parent.memes["calm"] += 1
    if rescue.power >= problem.severity:
        obj.meters["freed"] += 1
        child.meters["stuck"] = 0.0
        propagate(world, narrate=narrate)
        if narrate:
            world.say(rescue.text.replace("{object}", obj.label).replace("{problem}", problem.label))
    else:
        child.memes["worry"] += 1
        if narrate:
            world.say(rescue.fail.replace("{object}", obj.label).replace("{problem}", problem.label))


def bedtime_setup(world: World, scene: Scene, child: Entity, parent: Entity, obj: Entity) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"At bedtime, {child.id} snuggled into {scene.room} while {parent.label_word} "
        f"read softly by the lamp. {scene.bedtime_line}"
    )
    world.say(
        f"{child.id} noticed {scene.foreshadow}."
    )
    world.say(
        f"When {child.id} reached for {scene.object_noun}, {scene.stuck_reason}."
    )


def caution(world: World, parent: Entity, child: Entity, problem: Problem, scene: Scene) -> None:
    parent.memes["caution"] += 1
    pred = predict(world, problem, RESCUES[0] if RESCUES[0].power >= problem.severity else RESCUES[-1])
    world.facts["predicted"] = pred
    world.say(
        f"{parent.label_word.capitalize()} paused. \"Careful,\" {parent.pronoun()} said, "
        f"\"that could turn into {scene.extraction_note}.\""
    )
    if pred["worry"] > 0:
        world.say(f"{child.id} held still and listened.")


def rescue_scene(world: World, parent: Entity, child: Entity, obj: Entity, problem: Problem, rescue: Rescue) -> None:
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} used {rescue.label} and kept {child.id} calm."
    )
    _attempt_extraction(world, parent, child, obj, problem, rescue, narrate=True)
    world.say(
        f"After that, {scene_end(world)}"
    )


def scene_end(world: World) -> str:
    child = world.get("child")
    obj = world.get("object")
    scene = world.facts["scene"]
    return (
        f"{child.id} yawned, {obj.label} rested safely again, and the room felt "
        f"soft and quiet with {scene.gentle_image}."
    )


def tell(scene: Scene, problem: Problem, rescue: Rescue,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    obj = world.add(Entity(id="object", kind="thing", label=problem.label))
    world.facts["scene"] = scene

    bedtime_setup(world, scene, child, parent, obj)
    world.para()
    caution(world, parent, child, problem, scene)
    _attempt_extraction(world, parent, child, obj, problem, rescue, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} took a breath, checked the small problem, and began the extraction gently."
    )
    if obj.meters["freed"] >= THRESHOLD:
        world.say(
            f"The {problem.label} slipped free with a tiny pop, like a knot loosening."
        )
        world.say(
            f"{child.id} smiled, and {obj.label} looked easy and safe in the light."
        )
    else:
        world.say(
            f"The first try was not enough, so {parent.label_word} stopped and tried again with more care."
        )
    world.para()
    if obj.meters["freed"] >= THRESHOLD:
        world.say(
            f"By the end, {child.id} was sleepy, {obj.label} was no longer stuck, and the room was peaceful again."
        )
    else:
        world.say(
            f"In the end, {child.id} stayed safe, and the problem waited for a better grown-up fix."
        )

    world.facts.update(
        child=child, parent=parent, object=obj, scene=scene, problem=problem,
        rescue=rescue, freed=obj.meters["freed"] >= THRESHOLD,
    )
    return world


SCENES = {
    "bedroom": Scene(
        "bedroom", "the bedroom",
        "The lamp glowed low, and the quilt was folded beside the pillow.",
        "the little zipper pull",
        "a tiny snag on the blanket had been hiding there all evening",
        "the thread had looped around it",
        "a careful little extraction before it turned into a bigger tangle",
        "the moon made a silver shape on the wall",
        tags={"fabric", "tangle"},
    ),
    "bathroom": Scene(
        "bathroom", "the bathroom",
        "The night-light shone on the sink, and the towel waited on the hook.",
        "the small bath toy",
        "the drain glimmered like it might sip at the toy",
        "the toy had slipped too close to the drain",
        "a slow extraction before the toy got trapped for real",
        "the tiles looked clean and sleepy",
        tags={"drain", "stuck"},
    ),
    "hallway": Scene(
        "hallway", "the hallway",
        "The stair light was on, and the house breathed quietly around them.",
        "the lost slipper",
        "the edge of the rug had curled up like a tiny wave",
        "the slipper had caught under the rug",
        "a careful extraction before someone tripped on it",
        "the hallway clock ticked like a lullaby",
        tags={"rug", "stuck"},
    ),
}

PROBLEMS = {
    "snag": Problem("snag", "snag", "fabric", "the thread had looped around it", 1, "unthread", "pull"),
    "drain": Problem("drain", "drain", "drain", "the drain had started to tug at it", 2, "lift", "yank"),
    "rug": Problem("rug", "rug", "rug", "the rug had caught it at the edge", 1, "slide", "kick"),
}

RESCUES = [
    Rescue("careful_fingers", "careful fingers", 1,
           "used careful fingers to slide {object} free from the {problem}",
           "could not free {object} from the {problem} yet",
           tags={"gentle"}),
    Rescue("twist", "a gentle twist", 2,
           "gave {object} a gentle twist and eased it out of the {problem}",
           "tried a gentle twist, but {object} stayed stuck in the {problem}",
           tags={"gentle"}),
    Rescue("towel", "a soft towel", 3,
           "wrapped a soft towel around {object} and lifted it out of the {problem}",
           "wrapped the towel around {object}, but the {problem} held on",
           tags={"helper"}),
]

NAMES = ["Mina", "Lily", "Noa", "Ari", "Elsie", "Nina", "Theo", "Owen"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    problem: str
    rescue: str
    child: str
    gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for pid, problem in PROBLEMS.items():
            if problem_requires(problem, scene):
                for rid, rescue in RESCUES:
                    if rescue.power >= problem.severity:
                        combos.append((sid, pid, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that uses the word "extraction" and includes a gentle warning before the rescue.',
        f"Tell a cautious bedtime story where {f['child'].id} notices a small problem in {f['scene'].room} and a grown-up performs an extraction.",
        f'Write a soft, child-friendly story with foreshadowing, caution, and a safe ending about {f["problem"].label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["object"]
    scene = f["scene"]
    problem = f["problem"]
    rescue = f["rescue"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, who are together in {scene.room} at bedtime."),
        ("What warning signs were there before the problem got worse?",
         f"The story foreshadowed trouble with {scene.foreshadow}. That hint made the small problem feel real before anyone touched {obj.label}."),
        ("How was the problem solved?",
         f"{parent.label_word.capitalize()} used {rescue.label} and performed a careful extraction on {obj.label}. That gentle method fit the problem and kept the bedtime mood calm."),
    ]
    if f["freed"]:
        qa.append((
            f"What changed by the end?",
            f"{obj.label} was no longer stuck, {child.id} felt sleepy and relieved, and {scene.room} felt quiet again. The ending proves the extraction worked because the object rested safely instead of tugging in place."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["scene"].tags) | set(f["problem"].tags) | set(f["rescue"].tags)
    qa = []
    if "fabric" in tags:
        qa.append(("What is a snag?",
                    "A snag is a little place where cloth catches on something sharp or rough. It can pull and make a tiny tangle." ))
    if "drain" in tags:
        qa.append(("Why should a child be careful near a drain?",
                    "A drain can pull small things down into the water. That is why a grown-up should help if something gets close to it."))
    if "gentle" in tags:
        qa.append(("What does gentle mean?",
                    "Gentle means soft and careful, without grabbing too hard or hurting anything."))
    qa.append(("What is extraction?",
                "Extraction means taking something out carefully when it is stuck or trapped. Grown-ups should use the safest method for the situation."))
    return qa


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(scene: Scene, problem: Problem) -> str:
    return (f"(No story: this scene does not support a real extraction hazard. "
            f"Try one of the valid combinations where {problem.label} is actually stuck in {scene.room}.)")


def explain_rescue(rid: str) -> str:
    rescue = RESCUES[[r.id for r in RESCUES].index(rid)]
    return f"(No story: the rescue '{rid}' is too weak for this problem; choose a safer method.)"


ASP_RULES = r"""
hazard(S, P) :- scene(S), problem(P), needs(P, Need), scene_tag(S, Need).
valid(S, P, R) :- hazard(S, P), rescue(R), power(R, Pow), severity(P, Sev), Pow >= Sev.
outcome(freed) :- chosen_scene(S), chosen_problem(P), chosen_rescue(R), valid(S, P, R).
outcome(stuck) :- chosen_scene(S), chosen_problem(P), chosen_rescue(R), not valid(S, P, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for t in sorted(scene.tags):
            lines.append(asp.fact("scene_tag", sid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.stuck_kind))
        lines.append(asp.fact("severity", pid, p.severity))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_scene", params.scene),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_rescue", params.rescue),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations.")
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: empty story from smoke test.")
    else:
        print("OK: generate() smoke test produced story text.")
    cases = list(CURATED)
    for seed in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p)
            break
    if rc == 0:
        print("OK: ASP and Python outcomes agree.")
    return rc


def outcome_of(params: StoryParams) -> str:
    if params.scene not in SCENES or params.problem not in PROBLEMS or params.rescue not in [r.id for r in RESCUES]:
        return "?"
    if not problem_requires(PROBLEMS[params.problem], SCENES[params.scene]):
        return "invalid"
    return "freed" if RESCUES[[r.id for r in RESCUES].index(params.rescue)].power >= PROBLEMS[params.problem].severity else "stuck"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime cautionary extraction storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--rescue", choices=RESCUES_KEYS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


RESCUES_KEYS = [r.id for r in RESCUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.problem is None or c[1] == args.problem)
              and (args.rescue is None or c[2] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, problem, rescue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene, problem, rescue, child, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], PROBLEMS[params.problem], next(r for r in RESCUES if r.id == params.rescue), params.child, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams("bedroom", "snag", "careful_fingers", "Mina", "girl", "mother"),
    StoryParams("bathroom", "drain", "twist", "Theo", "boy", "father"),
    StoryParams("hallway", "rug", "towel", "Elsie", "girl", "mother"),
]


def valid_combo_set() -> set[tuple[str, str, str]]:
    return set(valid_combos())


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for s, p, r in asp_valid_combos():
            print(s, p, r)
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
if __name__ == "__main__":
    main()
