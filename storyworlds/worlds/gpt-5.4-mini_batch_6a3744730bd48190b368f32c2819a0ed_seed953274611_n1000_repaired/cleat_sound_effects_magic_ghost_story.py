#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cleat_sound_effects_magic_ghost_story.py
=======================================================================

A standalone storyworld sketch for a small ghost-story domain with sound
effects, a little magic, and one important cleat. The world is built around a
child who hears spooky sounds near an old dock, thinks the noises mean a ghost,
then discovers the noises come from something real and fixable. Magic helps
solve the mystery, and the ending proves the change with a bright, safe image.

This world keeps the story child-facing, concrete, and state-driven:
- a cleat is a dock post or boat fitting that can trap a rope;
- sound effects are part of the tension and the turn;
- a little magic reveals what is happening;
- the ghost-story feeling comes from fog, echoes, and the unknown, not from
  anything grim.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/cleat_sound_effects_magic_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/cleat_sound_effects_magic_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/cleat_sound_effects_magic_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/cleat_sound_effects_magic_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/cleat_sound_effects_magic_ghost_story.py --verify
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

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    mood: str
    fog: str
    echo: str
    haunt_word: str
    sound_label: str
    magic_label: str
    reveal_word: str
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
class Problem:
    id: str
    sound: str
    label: str
    source_phrase: str
    start_phrase: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    glow: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    scene: str
    problem: str
    magic: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["haunted"] < THRESHOLD:
            continue
        sig = ("haunt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "night" in world.entities:
            world.get("night").meters["spook"] += 1
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["unease"] += 1
        out.append("__spook__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("ghostlight") and world.get("ghostlight").meters["glow"] >= THRESHOLD:
        sig = ("reveal", "ghostlight")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        if "rope" in world.entities:
            world.get("rope").meters["seen"] += 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("haunt", _r_haunt), Rule("reveal", _r_reveal)]


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SCENES = {
    "dock": Scene(
        id="dock",
        place="an old dock by the water",
        mood="foggy",
        fog="The dock was wrapped in fog, and the water made soft black ripples below.",
        echo="Every sound came back a little slower, like the dock was listening.",
        haunt_word="haunted dock",
        sound_label="creak",
        magic_label="lantern charm",
        reveal_word="sparkle",
        ending_image="the rope lying neatly beside a glowing lantern",
    ),
    "boathouse": Scene(
        id="boathouse",
        place="a little boathouse",
        mood="misty",
        fog="The boathouse was misty, and the windows looked pale in the dusk.",
        echo="The walls made every sound bounce around in funny ways.",
        haunt_word="haunted boathouse",
        sound_label="rattle",
        magic_label="moon charm",
        reveal_word="glimmer",
        ending_image="the open crate with moonlight and a tidy rope coil",
    ),
    "shore": Scene(
        id="shore",
        place="a quiet shore path",
        mood="foggy",
        fog="The shore path was covered with fog, and the reeds whispered in the wind.",
        echo="The little bells on nearby boats chimed and chimed again.",
        haunt_word="haunted shore",
        sound_label="clink",
        magic_label="shell charm",
        reveal_word="shine",
        ending_image="the cleat, the rope, and the safe lantern all shining together",
    ),
}

PROBLEMS = {
    "cleat": Problem(
        id="cleat",
        sound="clank!",
        label="the cleat",
        source_phrase="a rope that had snagged around the cleat",
        start_phrase="something around the dock made a sudden clank",
        tags={"cleat", "dock"},
    ),
    "chain": Problem(
        id="chain",
        sound="clang!",
        label="the chain",
        source_phrase="a chain that had caught on the piling",
        start_phrase="a metal clang rang out from the side of the pier",
        tags={"chain", "dock"},
    ),
}

MAGICS = {
    "lantern": MagicTool(
        id="lantern",
        label="a lantern charm",
        phrase="a little charm shaped like a lantern",
        glow="it glowed like a warm firefly",
        reveal="showed the rope and cleat in a soft gold light",
        tags={"magic", "lantern"},
    ),
    "bell": MagicTool(
        id="bell",
        label="a bell charm",
        phrase="a tiny silver bell charm",
        glow="it shivered with silver light",
        reveal="made the hidden rope line shine like a ribbon",
        tags={"magic", "bell"},
    ),
    "shell": MagicTool(
        id="shell",
        label="a shell charm",
        phrase="a smooth shell charm",
        glow="it gleamed with pearly light",
        reveal="revealed the tangled line with a pearly shimmer",
        tags={"magic", "shell"},
    ),
}

FIXES = {
    "untangle": Fix(
        id="untangle",
        sense=3,
        power=3,
        text="carefully lifted the rope, slipped it free, and untangled the knot around {target}",
        fail="tried to pull the rope loose, but the knot held fast around {target}",
        qa_text="carefully lifted the rope and untangled the knot around {target}",
        tags={"rope", "help"},
    ),
    "lift": Fix(
        id="lift",
        sense=2,
        power=2,
        text="lifted the rope up and slid it off {target}",
        fail="pulled at the rope, but it only tightened around {target}",
        qa_text="lifted the rope up and slid it off {target}",
        tags={"rope", "help"},
    ),
    "beam": Fix(
        id="beam",
        sense=3,
        power=4,
        text="pointed the lantern charm at the cleat and made the knot easy to see",
        fail="held the charm up, but the dark stayed too thick to help",
        qa_text="pointed the lantern charm at the cleat and made the knot easy to see",
        tags={"light", "help"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tia", "June", "Maya"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Finn", "Jasper", "Ari"]
TRAITS = ["careful", "curious", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for problem in PROBLEMS:
            for magic in MAGICS:
                if "cleat" in PROBLEMS[problem].tags and "magic" in MAGICS[magic].tags:
                    combos.append((scene, problem, magic))
    return combos


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pronoun_word(entity: Entity) -> str:
    return entity.pronoun()


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    sim.get("mystery").meters["haunted"] += 1
    propagate(sim, narrate=False)
    return {"spook": sim.get("night").meters["spook"]}


def reasonableness_gate(problem: Problem, magic: MagicTool, fix: Fix) -> bool:
    return problem.id == "cleat" and "magic" in magic.tags and fix.sense >= SENSE_MIN


# ---------------------------------------------------------------------------
# Narrative verbs
# ---------------------------------------------------------------------------
def opening(world: World, child: Entity, helper: Entity, scene: Scene) -> None:
    world.say(
        f"On a foggy evening, {child.id} and {helper.id} walked to {scene.place}. "
        f"{scene.fog} {scene.echo}"
    )
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1


def hear_sound(world: World, child: Entity, problem: Problem, scene: Scene) -> None:
    world.say(
        f"Then came a sudden {problem.sound} from the dark water's edge. "
        f"{child.id} froze and stared at {scene.haunt_word} like it might be real."
    )
    child.memes["fear"] += 1
    world.add(Entity(id="night", kind="thing", type="thing"))
    world.add(Entity(id="mystery", kind="thing", type="thing"))
    world.add(Entity(id="rope", kind="thing", type="thing", label="rope"))
    world.add(Entity(id="ghostlight", kind="thing", type="thing", label="ghostlight"))


def scare(world: World, child: Entity, scene: Scene) -> None:
    world.say(
        f'"Did you hear that?" {child.id} whispered. "It sounds like a ghost on {scene.place}."'
    )
    child.memes["spook"] += 1


def magic_glow(world: World, helper: Entity, magic: MagicTool, problem: Problem) -> None:
    world.say(
        f"{helper.id} took out {magic.phrase}. {magic.glow}. "
        f"It {magic.reveal}."
    )
    world.get("ghostlight").meters["glow"] += 1
    world.get("mystery").meters["haunted"] += 1


def reveal(world: World, child: Entity, problem: Problem) -> None:
    world.say(
        f"Under the glow, the scary noise made sense at last: {problem.source_phrase}. "
        f"The {problem.label} had only been trapping the rope."
    )
    world.get("mystery").meters["haunted"] = 0


def fix_problem(world: World, helper: Entity, fix: Fix, problem: Problem) -> None:
    body = fix.text.replace("{target}", problem.label)
    world.say(
        f"{helper.id} {body}."
    )
    world.get("rope").meters["seen"] += 1


def closing(world: World, child: Entity, helper: Entity, scene: Scene, problem: Problem) -> None:
    child.memes["fear"] = 0
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, the dock was quiet again. The only thing left was "
        f"{scene.ending_image}, and {child.id} laughed because the 'ghost' had been "
        f"just a rope and {problem.label} all along."
    )


def tell(scene: Scene, problem: Problem, magic: MagicTool, fix: Fix,
         child: str = "Mina", child_gender: str = "girl",
         helper: str = "Aunt Wren", helper_gender: str = "woman") -> World:
    world = World()
    kid = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    grown = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="dock", kind="thing", type="thing", label="dock"))
    world.facts["scene"] = scene
    world.facts["problem"] = problem
    world.facts["magic"] = magic
    world.facts["fix"] = fix
    world.facts["child"] = kid
    world.facts["helper"] = grown

    opening(world, kid, grown, scene)
    world.para()
    hear_sound(world, kid, problem, scene)
    scare(world, kid, scene)
    world.para()
    magic_glow(world, grown, magic, problem)
    reveal(world, kid, problem)
    world.para()
    fix_problem(world, grown, fix, problem)
    closing(world, kid, grown, scene, problem)

    world.facts["outcome"] = "solved"
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    problem = f["problem"]
    magic = f["magic"]
    return [
        f'Write a ghost-story for a 3-to-5-year-old set at {scene.place} that includes the word "cleat" and uses a spooky sound effect.',
        f"Tell a gentle ghost story where a child hears a spooky noise near a cleat, but magic helps explain what is really happening.",
        f"Write a child-friendly mystery with fog, a sound effect, magic, and a cleat that turns out to be important for the ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene = f["scene"]
    problem = f["problem"]
    magic = f["magic"]
    child = f["child"]
    helper = f["helper"]
    return [
        ("Where does the story happen?",
         f"It happens at {scene.place}. The fog and echoes make it feel spooky at first."),
        ("What scary sound did the child hear?",
         f"{child.id} heard a sudden {problem.sound}. It sounded like a ghost, but it was really a rope near {problem.label}."),
        ("How did the magic help?",
         f"{helper.id} used {magic.phrase}, and its light showed what was hidden. That made the dark sound easy to understand."),
        ("What was the cleat doing?",
         f"The cleat was holding part of the rope, and the rope had snagged around it. That is why the noise sounded strange in the fog."),
        ("How did the story end?",
         f"The noise was solved, the rope was untangled, and the dock was quiet again. The ending image was {scene.ending_image}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cleat?",
         "A cleat is a sturdy post or fitting on a dock or boat. People use it to tie ropes fast so they do not drift away."),
        ("What is a sound effect?",
         "A sound effect is a sound that helps tell a story or make it feel exciting. In a story, it can be something like clank, creak, or whoosh."),
        ("What does magic do in a story?",
         "Magic can make strange things happen, like glowing or revealing hidden things. In a story, it often helps solve a mystery."),
        ("Why does fog make things feel spooky?",
         "Fog hides what is far away and makes shapes hard to see. That can make ordinary things feel mysterious for a while."),
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem(cleat).
magic(M) :- magic_item(M).
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(Scene, Problem, Magic) :- scene(Scene), problem(Problem), magic(Magic).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic_item", mid))
        lines.append(asp.fact("label", mid, m.label))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and python valid_combos()")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: verified {len(clingo_set)} combos and story generation smoke test.")
    return 0


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(scene="dock", problem="cleat", magic="lantern", fix="untangle", child="Mina", child_gender="girl", helper="Aunt Wren", helper_gender="woman"),
    StoryParams(scene="boathouse", problem="cleat", magic="bell", fix="beam", child="Owen", child_gender="boy", helper="Uncle Bram", helper_gender="man"),
    StoryParams(scene="shore", problem="cleat", magic="shell", fix="lift", child="Nora", child_gender="girl", helper="Grandma June", helper_gender="woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with cleats, sound effects, and a little magic.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.problem is None or c[1] == args.problem)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, problem, magic = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or _choose_name(rng, child_gender)
    helper = args.helper or rng.choice(["Aunt Wren", "Uncle Bram", "Grandma June", "Mr. Finch"])
    if FIXES[fix].sense < SENSE_MIN:
        raise StoryError("Fix is too weak for this story.")
    return StoryParams(scene=scene, problem=problem, magic=magic, fix=fix,
                       child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"Unknown scene: {params.scene}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.magic not in MAGICS:
        raise StoryError(f"Unknown magic: {params.magic}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")
    if not reasonableness_gate(PROBLEMS[params.problem], MAGICS[params.magic], FIXES[params.fix]):
        raise StoryError("That combination does not make a reasonable ghost-story.")
    world = tell(SCENES[params.scene], PROBLEMS[params.problem], MAGICS[params.magic], FIXES[params.fix],
                 child=params.child, child_gender=params.child_gender,
                 helper=params.helper, helper_gender=params.helper_gender)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            parts = []
            if meters:
                parts.append(f"meters={dict(meters)}")
            if memes:
                parts.append(f"memes={dict(memes)}")
            if e.role:
                parts.append(f"role={e.role}")
            print(f"  {e.id}: {' '.join(parts)}")
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
        print(f"{len(combos)} compatible scenes:\n")
        for scene, problem, magic in combos:
            print(f"  {scene:10} {problem:8} {magic}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at {p.scene} with {p.magic} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
