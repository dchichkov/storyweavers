#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/state_climb_rough_flashback_bravery_cautionary_pirate.py
========================================================================================

A standalone storyworld for a tiny pirate tale about a child, a rough climb, a
flashback, bravery, and a cautious helper. The simulated domain is simple:
children want to climb to a high pirate lookout or ship mast, one child feels
brave enough to try the rough way, a flashback reminds them of a past scrape,
and a cautious companion helps them choose a safer route and a better ending.

The story uses stateful meters and memes:
- meters track physical things like height, scrapes, and rope wear
- memes track emotional things like bravery, caution, relief, and worry

The same simulated state drives prose, Q&A, JSON, and a lightweight ASP twin.
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
BRAVERY_MIN = 5.0
CAUTION_MIN = 4.0


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
class Setting:
    id: str
    place: str
    lookout: str
    height_word: str
    surface: str
    roughness: str
    ship_frame: str

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
class Path:
    id: str
    label: str
    phrase: str
    rough: bool
    safe: bool
    climb_gain: int
    scrape_risk: int

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
class Memory:
    id: str
    label: str
    phrase: str
    lesson: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
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
        c = World(self.setting)
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


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["climbing"] < THRESHOLD:
            continue
        if ent.meters["scrape"] < THRESHOLD:
            continue
        sig = ("scrape", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__scrape__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["flashback"] < THRESHOLD:
            continue
        sig = ("flashback", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["caution"] += 1
        out.append("__flashback__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["relief"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("scrape", "physical", _r_scrape),
    Rule("flashback", "social", _r_flashback),
    Rule("relief", "social", _r_relief),
]


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


def climb_is_rough(path: Path) -> bool:
    return path.rough


def path_is_safe(path: Path) -> bool:
    return path.safe


def can_choose_path(path: Path, memory: Memory) -> bool:
    return path.safe or (path.rough and memory.lesson == "learned")


def predict_climb(world: World, climber_id: str, path_id: str) -> dict:
    sim = world.copy()
    _do_climb(sim, sim.get(climber_id), PATHS[path_id], narrate=False)
    climber = sim.get(climber_id)
    return {
        "scraped": climber.meters["scrape"] >= THRESHOLD,
        "height": climber.meters["height"],
        "worry": climber.memes["worry"],
    }


def _do_climb(world: World, climber: Entity, path: Path, narrate: bool = True) -> None:
    climber.meters["climbing"] += 1
    climber.meters["height"] += path.climb_gain
    if path.rough:
        climber.meters["scrape"] += path.scrape_risk
        climber.meters["rope_wear"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"On a bright day by the harbor, {child.id} and {helper.id} stood by the "
        f"{world.setting.ship_frame}. The {world.setting.surface} looked like a pirate's path up to the "
        f"{world.setting.lookout}."
    )
    world.say(
        f"{child.id} wanted to climb to the {world.setting.lookout}, and "
        f"{helper.id} was ready to watch carefully."
    )


def show_bravery(world: World, child: Entity, path: Path) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'"I can do it," {child.id} said, patting {child.pronoun("possessive")} own chest. '
        f'"A brave pirate can climb {path.phrase}."'
    )


def flashback(world: World, child: Entity, memory: Memory) -> None:
    child.memes["flashback"] += 1
    world.say(
        f"Then a flashback tugged at {child.id}'s mind. {memory.phrase} "
        f"{memory.lesson}"
    )


def caution(world: World, helper: Entity, child: Entity, path: Path, memory: Memory) -> None:
    helper.memes["caution"] += 1
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip. "
        f'"That path is rough," {helper.id} said. "It climbs fast, but it can scrape you."'
    )
    world.say(
        f'"Remember {memory.label}," {helper.id} added softly. '
        f'"Being brave does not mean being careless."'
    )


def choose_safe_way(world: World, child: Entity, helper: Entity, safe_path: Path) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{child.id} looked from the rough path to the safer rope steps. "
        f'"Okay," {child.id} said. "I can climb the kinder way."'
    )
    world.say(
        f"So they took {safe_path.phrase}, one steady step at a time, until the "
        f"{world.setting.lookout} came into view."
    )


def rough_climb(world: World, child: Entity, helper: Entity, path: Path) -> None:
    world.say(
        f"{child.id} tried to climb {path.phrase}. The wood was rough, the rope was gritty, "
        f"and the climb felt harder than it had looked."
    )
    world.say(
        f"After a few careful steps, {child.id} got a small scrape and had to slow down."
    )


def ending_image(world: World, child: Entity, helper: Entity, safe_path: Path) -> None:
    world.say(
        f"At the top, {child.id} grinned beside {helper.id}, with a fresh breeze on "
        f"the face and steady feet on the platform. The pirate lookout was reached "
        f"without another scrape."
    )


def tell(
    setting: Setting,
    rough_path: Path,
    safe_path: Path,
    memory: Memory,
    child_name: str = "Mia",
    child_gender: str = "girl",
    helper_name: str = "Nora",
    helper_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="climber"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="cautionary"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))

    child.memes["bravery"] = 5.0
    helper.memes["caution"] = 5.0

    world.facts["setting"] = setting
    world.facts["rough_path"] = rough_path
    world.facts["safe_path"] = safe_path
    world.facts["memory"] = memory
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["parent"] = parent

    setup(world, child, helper)
    world.para()
    show_bravery(world, child, rough_path)
    flashback(world, child, memory)
    caution(world, helper, child, rough_path, memory)

    if can_choose_path(rough_path, memory):
        rough_climb(world, child, helper, rough_path)
        world.para()
        choose_safe_way(world, child, helper, safe_path)
    else:
        rough_climb(world, child, helper, rough_path)

    world.para()
    ending_image(world, child, helper, safe_path)

    world.facts["scraped"] = child.meters["scrape"] >= THRESHOLD
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "dock": Setting("dock", "the dock", "the crow's nest", "mast", "rough boards", "rough", "ship mast"),
    "island": Setting("island", "the island beach", "the cliff lookout", "cliff", "rough stones", "rough", "pirate camp"),
    "ship": Setting("ship", "the ship deck", "the top sail platform", "mast", "rope ladders", "rough", "ship deck"),
}

PATHS = {
    "rope": Path("rope", "the rope ladder", "the rope ladder", rough=True, safe=False, climb_gain=2, scrape_risk=1),
    "steps": Path("steps", "the rope steps", "the rope steps", rough=False, safe=True, climb_gain=2, scrape_risk=0),
    "stair": Path("stair", "the narrow stair", "the narrow stair", rough=False, safe=True, climb_gain=3, scrape_risk=0),
    "planks": Path("planks", "the rough planks", "the rough planks", rough=True, safe=False, climb_gain=3, scrape_risk=1),
}

MEMORIES = {
    "slip": Memory("slip", "the slippery slip", "A little while ago, the child had slipped on wet wood and scraped a knee.", "That memory made the child slower and wiser now."),
    "sting": Memory("sting", "the sharp sting", "Last time, the child had rushed up a rough path and felt the sting of splinters.", "That memory taught patience and caution."),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Sam", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "curious", "careful", "bold", "cautious"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, path in PATHS.items():
            for mid, memory in MEMORIES.items():
                if climb_is_rough(path) and path_is_safe(PATHS["steps"]):
                    combos.append((sid, pid, mid, "yes"))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    path: str
    safe_path: str
    memory: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, p, m = f["setting"], f["rough_path"], f["memory"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "state", "climb", and "rough".',
        f"Tell a short story where {f['child'].id} wants to {p.label} at the {s.place}, remembers {m.label}, and listens to a cautious helper.",
        f"Write a cautionary pirate story with a brave child, a rough climb, a flashback, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    rough: Path = f["rough_path"]
    memory: Memory = f["memory"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {helper.id}, who are playing pirate near the {setting.lookout}.",
        ),
        QAItem(
            question="Why did the child hesitate?",
            answer=f"{child.id} had a flashback to an earlier slip. That memory made the rough climb feel risky instead of exciting.",
        ),
        QAItem(
            question="What did the cautious helper say about the climb?",
            answer=f"{helper.id} warned that the path was rough and could scrape the child. The helper also reminded the child that bravery should still be careful.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"They chose the safer path and reached the top without another scrape. The child ended brave, but also wiser about the rough climb.",
        ),
    ]
    if f.get("scraped"):
        items.append(
            QAItem(
                question="What happened on the rough path?",
                answer=f"{child.id} got a small scrape while climbing {rough.phrase}. The rough wood and gritty rope made the climb harder than it looked.",
            )
        )
    return items


WORLD_KNOWLEDGE = {
    "bravery": [("What is bravery?", "Bravery means doing something hard or scary without giving up. It is best when you also stay careful.")],
    "caution": [("What does caution mean?", "Caution means being careful and watching for danger before you move.")],
    "flashback": [("What is a flashback in a story?", "A flashback is when the story remembers something that happened before. It helps explain why a character feels worried or brave.")],
    "rough": [("What does rough mean?", "Rough means bumpy or scratchy, not smooth. A rough path can scrape your hands or knees.")],
    "climb": [("What is a climb?", "A climb is going up something high, like stairs, rocks, or a ladder.")],
    "state": [("What is a state in a story?", "A state is how things are right now, like whether someone feels brave, worried, or safe.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"bravery", "caution", "flashback", "rough", "climb", "state"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(q, a) for q, a in WORLD_KNOWLEDGE.get(tag, []))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ship", "rope", "steps", "slip", "Mia", "girl", "Nora", "girl", "mother", "brave"),
    StoryParams("dock", "planks", "steps", "sting", "Finn", "boy", "Leo", "boy", "father", "cautious"),
    StoryParams("island", "rope", "steps", "slip", "Ava", "girl", "Ella", "girl", "mother", "bold"),
]


def explain_rejection(path: Path) -> str:
    return "(No story: that climb has no clear rough-versus-safe choice.)"


def outcome_of(params: StoryParams) -> str:
    return "safe"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about a rough climb, a flashback, bravery, and caution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--safe-path", choices=[k for k, p in PATHS.items() if p.safe])
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        if p.rough:
            lines.append(asp.fact("rough", pid))
        if p.safe:
            lines.append(asp.fact("safe", pid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, M) :- setting(S), path(P), memory(M), rough(P), safe(steps).
outcome(safe) :- valid(_, _, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in asp:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.path and args.memory:
        if (args.setting, args.path, args.memory, "yes") not in combos:
            raise StoryError(explain_rejection(PATHS[args.path]))
    setting, path, memory, _ = rng.choice(combos)
    safe_path = args.safe_path or "steps"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, path, safe_path, memory, child, child_gender, helper, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PATHS[params.path], PATHS[params.safe_path], MEMORIES[params.memory],
                 params.child, params.child_gender, params.helper, params.helper_gender, params.parent)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
            header = f"### {p.child} at {p.setting} ({p.path} -> {p.safe_path})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
