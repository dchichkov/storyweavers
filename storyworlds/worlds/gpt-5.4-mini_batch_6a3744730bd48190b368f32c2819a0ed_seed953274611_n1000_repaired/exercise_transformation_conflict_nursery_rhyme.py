#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exercise_transformation_conflict_nursery_rhyme.py
=================================================================================

A small standalone story world for a nursery-rhyme-style tale about a child,
an exercise challenge, a conflict, and a transformation.

The seed image here is simple: a little rhyme-like scene where someone resists
exercise, a quarrel grows, and then movement changes the mood and shape of the
day. The world keeps the story grounded in state: posture, energy, stiffness,
and cheer all change as the tale goes on.

The stories are written to feel like a child-facing rhyme with a clear turn:
beginning -> conflict -> transformation -> ending image.
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Scene:
    id: str
    setting: str
    rhyme: str
    activity: str
    step: str
    conflict_line: str
    turn_line: str
    ending_image: str
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
class Exercise:
    id: str
    noun: str
    verb: str
    sound: str
    body: str
    boosts: list[str]
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
class Transformation:
    id: str
    from_state: str
    to_state: str
    result_line: str
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
class Resolution:
    id: str
    sense: int
    power: int
    line: str
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


def _r_breath(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["winded"] < THRESHOLD:
        return out
    sig = ("breath",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["determined"] += 1
    out.append("__breath__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    if child.meters["steps"] < 2:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.meters["stiff"] = 0
    friend.meters["bounce"] += 1
    friend.memes["joy"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("breath", _r_breath), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonability_gate(exercise: Exercise, scene: Scene) -> bool:
    return scene.id in {"yard", "playroom", "sidewalk"} and exercise.id in EXERCISES


def exercise_effect(world: World, exercise: Exercise) -> None:
    child = world.get("child")
    friend = world.get("friend")
    child.meters["steps"] += 1
    child.meters["winded"] += 1
    child.memes["joy"] += 1
    friend.meters["stiff"] = max(0.0, friend.meters["stiff"] - 0.5)
    friend.meters["bounce"] += 0.5
    friend.memes["mood"] += 1
    propagate(world, narrate=True)


def predict_transformation(world: World, exercise: Exercise) -> dict:
    sim = world.copy()
    exercise_effect(sim, exercise)
    friend = sim.get("friend")
    return {
        "bounce": friend.meters["bounce"],
        "stiff": friend.meters["stiff"],
        "joy": friend.memes["joy"],
    }


def intro(world: World, child: Entity, friend: Entity, scene: Scene) -> None:
    world.say(
        f"At {scene.setting}, {child.id} and {friend.id} went skip-a-step, hop-a-step, "
        f"with a nursery-rhyme smile and a tap-tap beat."
    )
    world.say(scene.rhyme)


def conflict(world: World, child: Entity, friend: Entity, exercise: Exercise, scene: Scene) -> None:
    child.memes["wanting"] += 1
    friend.memes["grumpy"] += 1
    world.say(
        f'But {friend.id} frowned and said, "{scene.conflict_line}"'
    )
    world.say(
        f'{child.id} stamped one foot. "{exercise.sound} {exercise.sound}," '
        f"{child.id} sang, but the room felt full of crossed arms."
    )


def turn(world: World, child: Entity, friend: Entity, exercise: Exercise, resolution: Resolution) -> None:
    friend.meters["stiff"] += 1
    pred = predict_transformation(world, exercise)
    world.facts["predicted"] = pred
    world.say(
        f"{child.id} began {exercise.verb}, little by little, and the beat got steadier."
    )
    world.say(
        f'Then {resolution.line}'
    )
    world.say(
        f"{friend.id} looked in the mirror and saw {friend.id} as {scene_transform_word(friend)}."
    )


def scene_transform_word(friend: Entity) -> str:
    if friend.meters["bounce"] >= 1:
        return "less stiff and more springy"
    return "the same old self"


def ending(world: World, child: Entity, friend: Entity, scene: Scene, exercise: Exercise) -> None:
    world.say(scene.ending_image)
    world.say(
        f"After the steps and skips, {child.id} was not out of breath for long, and "
        f"{friend.id} was all bounce and grin."
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for ex_id, ex in EXERCISES.items():
            for tr_id, tr in TRANSFORMATIONS.items():
                if reasonability_gate(ex, scene) and tr_id in {"spry", "bright"}:
                    combos.append((sid, ex_id, tr_id))
    return combos


@dataclass
class StoryParams:
    scene: str
    exercise: str
    transformation: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
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


SCENES = {
    "yard": Scene(
        id="yard",
        setting="the little front yard",
        rhyme="One two, buckle my shoe; three four, exercise some more.",
        activity="a skipping game",
        step="step-hop",
        conflict_line="I won't stretch. I won't jump. My knees are grumpy and my toes are bump-bump-bump.",
        turn_line="the grumpy knees loosened, and the toes began to tap.",
        ending_image="And there, in the grass, the pair bounced like bright little beans in a bowl.",
    ),
    "playroom": Scene(
        id="playroom",
        setting="the sunny playroom",
        rhyme="Pat-a-cake, pat-a-cake, turn and bend; every little stretch is a happy friend.",
        activity="a movement game",
        step="bend-reach",
        conflict_line="No more bends for me. I'm stiff as a broom, and I don't want to move.",
        turn_line="the stiff back softened, and the shoulders sang.",
        ending_image="So the playroom shone with a wiggle and a giggle, warm as toast.",
    ),
    "sidewalk": Scene(
        id="sidewalk",
        setting="the warm sidewalk by the flowers",
        rhyme="Humpty dumpty sat on a wall, then he hopped right down to join the call.",
        activity="a hopping rhyme",
        step="hop",
        conflict_line="I am too sleepy for hops. My feet are flat as pancakes.",
        turn_line="the sleepy feet found a spring.",
        ending_image="And the flowers seemed to clap as the footsteps went clip-clop, clip-clop.",
    ),
}

EXERCISES = {
    "jumps": Exercise(
        id="jumps",
        noun="jumping jacks",
        verb="doing jumping jacks",
        sound="jump-jump",
        body="arms and legs",
        boosts=["heat", "bounce"],
        tags={"exercise", "jump"},
    ),
    "stretches": Exercise(
        id="stretches",
        noun="stretches",
        verb="stretching tall",
        sound="stretch-stretch",
        body="back and arms",
        boosts=["softness", "reach"],
        tags={"exercise", "stretch"},
    ),
    "march": Exercise(
        id="march",
        noun="marching steps",
        verb="marching in place",
        sound="march-march",
        body="knees and feet",
        boosts=["rhythm", "lift"],
        tags={"exercise", "march"},
    ),
}

TRANSFORMATIONS = {
    "spry": Transformation(
        id="spry",
        from_state="stiff",
        to_state="spry",
        result_line="the stiff little helper turned spry as a kite in a kind wind",
        tags={"transformation", "exercise"},
    ),
    "bright": Transformation(
        id="bright",
        from_state="grumpy",
        to_state="bright",
        result_line="the grumpy face turned bright as a button",
        tags={"transformation", "exercise"},
    ),
    "bouncy": Transformation(
        id="bouncy",
        from_state="sleepy",
        to_state="bouncy",
        result_line="the sleepy feet turned bouncy, bounce-a-bounce-a-bounce",
        tags={"transformation", "exercise"},
    ),
}

RESPONSES = {
    "gentle": Resolution(
        id="gentle",
        sense=3,
        power=3,
        line="a gentle count of one-two-three helped the quarrel melt away",
        tags={"kind", "conflict"},
    ),
    "coach": Resolution(
        id="coach",
        sense=4,
        power=4,
        line="a kindly rhyme coached the steps, and the steps coached the heart",
        tags={"kind", "conflict"},
    ),
    "music": Resolution(
        id="music",
        sense=2,
        power=2,
        line="a tiny song came along, and the song made the feet listen",
        tags={"kind", "conflict"},
    ),
}


GIRL_NAMES = ["Mina", "Lily", "Nora", "Tilly", "Mabel", "Pippa"]
BOY_NAMES = ["Benny", "Toby", "Robin", "Milo", "Felix", "Harvey"]
TRAITS = ["bouncy", "cheerful", "curious", "gentle", "lively"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about exercise, conflict, and transformation.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--exercise", choices=EXERCISES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def sensible_transformations() -> list[Transformation]:
    return [t for t in TRANSFORMATIONS.values() if t.id in {"spry", "bright", "bouncy"}]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for eid, ex in EXERCISES.items():
        lines.append(asp.fact("exercise", eid))
        if "exercise" in ex.tags:
            lines.append(asp.fact("exercise_tag", eid))
    for tid, tr in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,E,T) :- scene(S), exercise(E), transformation(T), allowed_scene(S), allowed_exercise(E), allowed_transformation(T).
allowed_scene(S) :- scene(S).
allowed_exercise(E) :- exercise(E).
allowed_transformation(T) :- transformation(T), not bad_transformation(T).
bad_transformation(T) :- transformation(T), T = nope.
sensible(R) :- resolution(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def explain_rejection(scene: Scene, exercise: Exercise) -> str:
    return f"(No story: {exercise.id} doesn't fit this tiny rhyme scene.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.exercise:
        if (args.scene, args.exercise, args.transformation or "spry") not in valid_combos():
            raise StoryError(explain_rejection(SCENES[args.scene], EXERCISES[args.exercise]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.exercise is None or c[1] == args.exercise)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, exercise, transformation = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    return StoryParams(
        scene=scene,
        exercise=exercise,
        transformation=transformation,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    scene = SCENES[params.scene]
    exercise = EXERCISES[params.exercise]
    transformation = TRANSFORMATIONS[params.transformation]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender, role="friend"))
    world.add(Entity(id="rhythm", kind="thing", type="thing", label="little rhyme"))
    child.meters["steps"] = 0.0
    child.meters["winded"] = 0.0
    child.memes["joy"] = 1.0
    friend.meters["stiff"] = 1.0
    friend.meters["bounce"] = 0.0
    friend.memes["grumpy"] = 1.0

    world.say(f"At {scene.setting}, {child.id} and {friend.id} began a bright little rhyme.")
    world.say(scene.rhyme)
    world.para()
    conflict(world, child, friend, exercise, scene)
    world.para()
    exercise_effect(world, exercise)
    world.say(
        f"As the knees went bend and the arms went sweep, {transformation.result_line}."
    )
    world.say(
        f"{friend.id} gave a little laugh, and the quarrel folded up like a paper kite."
    )
    world.para()
    ending(world, child, friend, scene, exercise)
    child.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.facts.update(scene=scene, exercise=exercise, transformation=transformation,
                       child=child, friend=friend, outcome="transformed")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    scene = f["scene"]
    ex = f["exercise"]
    return [
        f'Write a nursery-rhyme story about exercise, conflict, and transformation in {scene.setting}.',
        f"Tell a short child-friendly rhyme where someone resists {ex.verb} at first, then changes after the quarrel softens.",
        f'Write a story that uses the word "exercise" and ends with a cheerful transformation.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    scene = f["scene"]
    ex = f["exercise"]
    tr = f["transformation"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {friend.id}, two little friends in a nursery-rhyme game."),
        ("What did the child want to do?", f"{child.id} wanted to keep up the exercise and do {ex.verb}."),
        ("What was the conflict?", f"{friend.id} did not want to move at first, so there was a small quarrel before the rhyme could go on."),
        ("What changed by the end?", f"The stiff, grumpy feeling changed into {tr.to_state} energy, so the ending image is bright and bouncy."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is exercise?", "Exercise is moving your body on purpose, like stretching, hopping, or marching, so your muscles get strong and awake."),
        ("Why can exercise change how you feel?", "Exercise can warm you up, loosen stiff muscles, and make a sleepy mood feel brighter."),
        ("What is a conflict?", "A conflict is when two people want different things, so they disagree for a little while."),
        ("What is a transformation?", "A transformation is a change from one state to another, like stiff turning to spry or grumpy turning bright."),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"  {e.id} ({e.type}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(bits)


CURATED = [
    StoryParams(scene="yard", exercise="jumps", transformation="spry", child_name="Mina", child_gender="girl", friend_name="Toby", friend_gender="boy"),
    StoryParams(scene="playroom", exercise="stretches", transformation="bright", child_name="Lily", child_gender="girl", friend_name="Robin", friend_gender="boy"),
    StoryParams(scene="sidewalk", exercise="march", transformation="bouncy", child_name="Benny", child_gender="boy", friend_name="Mabel", friend_gender="girl"),
]


def asp_verify() -> int:
    import asp
    ok = True
    c = set(asp_valid_combos())
    p = set(valid_combos())
    if c != p:
        ok = False
        print("MISMATCH in valid combos")
    s = set(asp_sensible())
    if s != set(RESPONSES):
        ok = False
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            ok = False
            print("SMOKE TEST FAILED: empty story")
    except Exception as exc:  # pragma: no cover
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: verify passed.")
        return 0
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for exercise in EXERCISES:
            for transformation in TRANSFORMATIONS:
                combos.append((scene, exercise, transformation))
    return combos


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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    ex = f["exercise"]
    return [
        f'Write a nursery-rhyme story about exercise, conflict, and transformation in {scene.setting}.',
        f"Tell a short child-friendly rhyme where someone resists {ex.verb} at first, then changes after the quarrel softens.",
        f'Write a story that uses the word "exercise" and ends with a cheerful transformation.',
    ]


if __name__ == "__main__":
    main()
