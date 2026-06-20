#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thrill_sharing_lesson_learned_foreshadowing_pirate_tale.py
===========================================================================================

A standalone storyworld for a small pirate-tale domain built around a shared
thrill, a lesson learned, and a bit of foreshadowing.

Premise
-------
Two children are pretending to be pirates on a sunny dock. They discover a map,
feel a thrill, and want to keep the fun to themselves. A looming sign of trouble
foreshadows that the best treasure is not the shiny object, but sharing and
helping the whole crew.

The world model tracks:
- typed entities with physical `meters` and emotional `memes`
- a small causal chain: discovery -> thrill -> possession -> sharing -> lesson
- explicit invalid choices rejected with `StoryError`
- three Q&A sets grounded in simulated state rather than rendered English
- an inline ASP twin with a Python reasonableness gate

This script is stdlib-only and is designed to run directly from the repo root.
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
    place: str
    scent: str
    sound: str
    cover: str
    bright: str
    clue: str

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
class Treasure:
    id: str
    label: str
    kind: str
    tempt: str
    shareable: bool = True
    shiny: bool = True
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
class Warning:
    id: str
    sign: str
    consequence: str
    foreshadow: str
    lesson: str
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

    def chars(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

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


def _r_thrill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.chars():
        if e.memes["thrill"] < THRESHOLD:
            continue
        sig = ("thrill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["glee"] += 1
        out.append("")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared"):
        return out
    for e in world.chars():
        if e.role == "captain":
            e.memes["pride"] += 1
        if e.role == "mate":
            e.memes["trust"] += 1
    return out


CAUSAL_RULES = [Rule("thrill", "social", _r_thrill), Rule("share", "social", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if x)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foreshadows(scene: Scene, warning: Warning) -> bool:
    return bool(scene.clue and warning.sign)


def reasonable_combo(scene: Scene, treasure: Treasure, warning: Warning) -> bool:
    return treasure.shareable and treasure.shiny and foreshadows(scene, warning)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SCENES.items():
        for tid, t in TREASURES.items():
            for wid, w in WARNINGS.items():
                if reasonable_combo(s, t, w):
                    out.append((sid, tid, wid))
    return out


def _do_find(world: World, captain: Entity, mate: Entity, scene: Scene, treasure: Treasure, warning: Warning) -> None:
    captain.memes["thrill"] += 1
    mate.memes["curiosity"] += 1
    world.say(
        f"At {scene.place}, {captain.id} and {mate.id} heard {scene.sound} under the boards, "
        f"and the air smelled like {scene.scent}. The sight of {treasure.label} sent a thrill through them."
    )
    if foreshadows(scene, warning):
        world.say(
            f"Near the edge of the dock, {warning.sign} promised trouble later, though the children did not know it yet."
        )


def _do_keep(world: World, captain: Entity, treasure: Treasure) -> None:
    captain.memes["possessive"] += 1
    world.say(
        f'{captain.id} clutched the {treasure.label} close and said, "This one is ours."'
    )


def _do_share(world: World, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    captain.memes["generous"] += 1
    mate.memes["joy"] += 1
    world.facts["shared"] = True
    world.say(
        f'{mate.id} smiled and said, "A pirate crew is stronger when it shares." '
        f'{captain.id} nodded and split the {treasure.label} into two fair parts.'
    )
    propagate(world, narrate=False)


def _do_lesson(world: World, parent: Entity, captain: Entity, mate: Entity, warning: Warning) -> None:
    captain.memes["lesson"] += 1
    mate.memes["lesson"] += 1
    world.say(
        f"Then {parent.label_word} pointed at {warning.consequence} and said, "
        f'"That was the clue. The best treasure is the kind that leaves everyone smiling."'
    )
    world.say(
        f'{captain.id} and {mate.id} looked at their halves and learned {warning.lesson}.'
    )


def tell(scene: Scene, treasure: Treasure, warning: Warning,
         captain_name: str = "Mia", captain_gender: str = "girl",
         mate_name: str = "Tom", mate_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="treasure", type=treasure.kind, label=treasure.label))
    world.facts["scene"] = scene
    world.facts["treasure"] = treasure
    world.facts["warning"] = warning

    world.say(
        f"One bright morning, {captain.id} and {mate.id} turned the dock into a pirate deck."
    )
    world.say(
        f"{scene.cover} {scene.bright}. {captain.id} loved the little adventure, and {mate.id} loved the company."
    )
    world.para()
    _do_find(world, captain, mate, scene, treasure, warning)
    world.say(f'{captain.id} held the {treasure.label} up. It looked shiny enough to make everyone grin.')
    world.para()
    _do_keep(world, captain, treasure)
    world.say(
        f"{mate.id} hesitated, because {warning.sign.lower()} was still on the edge of the scene like a quiet promise."
    )
    world.para()
    _do_share(world, captain, mate, treasure)
    world.say(
        f"Later, when the sun sank low, the two pirates used their matching halves to mark the way home."
    )
    world.para()
    _do_lesson(world, parent, captain, mate, warning)
    world.say(
        f"In the last light of day, the dock seemed less like a playground and more like a place that had taught them something kind."
    )

    world.facts.update(captain=captain, mate=mate, parent=parent, shared=world.facts.get("shared", False))
    return world


SCENES = {
    "dock": Scene("dock", "the old harbor dock", "salt", "a creaky tap-tap", "The rope rails bobbed", "sunlight flashed on the water", "a gull circling low"),
    "beach": Scene("beach", "the sandy beach", "sea air", "waves whispering", "The tide left glittering shells", "the water glittered like coins", "a dark cloud far off"),
    "island": Scene("island", "the little island cove", "warm sand", "shells clicking", "The palms leaned over the shore", "the tide sparkled around the rocks", "a half-buried bottle"),
}

TREASURES = {
    "compass": Treasure("compass", "little brass compass", "compass", "pointed north with a bright needle", tags={"shiny", "share"}),
    "coin": Treasure("coin", "gold coin", "coin", "winked like a tiny sun", tags={"shiny", "share"}),
    "shell": Treasure("shell", "pearl shell", "shell", "gleamed with a soft white glow", tags={"shiny", "share"}),
}

WARNINGS = {
    "gull": Warning("gull", "a gull circling low", "a splashy slip near the edge", "the gull was a foreshadowing clue", "that treasure should be shared", tags={"foreshadow"}),
    "cloud": Warning("cloud", "a dark cloud far off", "rain would soon chase them home", "the cloud foreshadowed the end of play", "sharing kept the trip from turning sour", tags={"foreshadow"}),
    "bottle": Warning("bottle", "a half-buried bottle", "someone else might be looking for it", "the bottle hinted the dock had an older story", "not every shiny thing should be kept", tags={"foreshadow"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Max", "Finn", "Eli"]
PARENT_TYPES = ["mother", "father"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    treasure: str
    warning: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
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


def explain_rejection(scene: Scene, treasure: Treasure, warning: Warning) -> str:
    if not reasonable_combo(scene, treasure, warning):
        return "No story: this combination does not support both the thrill and the foreshadowing in a believable pirate tale."
    return "No story: invalid choices."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    treasure: Treasure = f["treasure"]
    warning: Warning = f["warning"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "thrill" and a clear lesson learned.',
        f"Tell a story on a dock where two children find a {treasure.label}, feel a thrill, notice {warning.sign}, and learn to share.",
        f"Write a short pirate story with foreshadowing: a small clue on {scene.place} hints that sharing the treasure is the right ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain: Entity = f["captain"]
    mate: Entity = f["mate"]
    warning: Warning = f["warning"]
    treasure: Treasure = f["treasure"]
    scene: Scene = f["scene"]
    qa = [
        ("What did the children find?", f"They found {treasure.label} at {scene.place}, and it made them feel a real thrill."),
        ("What clue foreshadowed the lesson?", f"{warning.sign} was the clue. It hinted that the shiny treasure would be better when it was shared."),
        ("What did they learn?", f"They learned {warning.lesson}, and they ended the story by sharing the treasure fairly."),
    ]
    if f.get("shared"):
        qa.append((
            f"How did {captain.id} and {mate.id} solve the problem?",
            f"They split the {treasure.label} into two fair parts and used it together. Sharing turned the shiny prize into a happy ending for both of them."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["treasure"].tags) | set(world.facts["warning"].tags)
    out = []
    knowledge = {
        "shiny": ("Why do shiny things grab your attention?", "Shiny things catch the eye because they reflect light and sparkle."),
        "share": ("Why should friends share?", "Sharing helps everyone feel included, and it can make play fair and happy."),
        "foreshadow": ("What is foreshadowing?", "Foreshadowing is when a story gives a small clue about what may happen later."),
    }
    for key, item in knowledge.items():
        if key in tags:
            out.append(item)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadows(S, W) :- scene(S), warning(W), clue(S, C), sign(W, C).
valid(S, T, W) :- scene(S), treasure(T), warning(W), shareable(T), foreshadows(S, W).
thrill(C) :- character(C), feels_thrill(C).
shared(C1, C2) :- character(C1), character(C2), crew(C1, C2).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("clue", sid, s.clue))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for wid, w in WARNINGS.items():
        lines.append(asp.fact("warning", wid))
        lines.append(asp.fact("sign", wid, w.sign))
    lines.append(asp.fact("feels_thrill", "captain"))
    lines.append(asp.fact("crew", "captain", "mate"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generate smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate-tale storyworld with sharing, lesson learned, and foreshadowing.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
              and (args.treasure is None or c[1] == args.treasure)
              and (args.warning is None or c[2] == args.warning)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, treasure, warning = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if captain_gender == "girl" else "girl")
    captain = args.captain or rng.choice(GIRL_NAMES if captain_gender == "girl" else BOY_NAMES)
    mate_pool = [n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES) if n != captain]
    mate = args.mate or rng.choice(mate_pool)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(scene, treasure, warning, captain, captain_gender, mate, mate_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], TREASURES[params.treasure], WARNINGS[params.warning],
                 params.captain, params.captain_gender, params.mate, params.mate_gender, params.parent)
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
    StoryParams("dock", "compass", "gull", "Mia", "girl", "Tom", "boy", "mother"),
    StoryParams("beach", "coin", "cloud", "Leo", "boy", "Nora", "girl", "father"),
    StoryParams("island", "shell", "bottle", "Ava", "girl", "Ben", "boy", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
