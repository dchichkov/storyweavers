#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marry_pail_conflict_whodunit.py
===============================================================

A standalone storyworld for a tiny whodunit in which a child hears about a
marriage plan, a pail goes missing, and a small conflict gets solved by careful
clue-following instead of shouting.

The world is built around a few concrete things:
- a person who wants to marry,
- a person who is worried about a pail,
- a missing pail or a misleading pail,
- a small set of clues that reveal who moved what and why.

The tone is child-facing and mystery-like: there is a question, a tense middle,
and a tidy ending that proves the truth. The simulation keeps physical meters and
emotional memes, and the prose is driven by state changes rather than a frozen
template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/marry_pail_conflict_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/marry_pail_conflict_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/marry_pail_conflict_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/marry_pail_conflict_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"missing": 0.0, "moved": 0.0, "closed": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "anger": 0.0}

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
    scene: str
    place: str
    clue_place: str
    weather: str
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
class Suspect:
    id: str
    label: str
    motive: str
    clue: str
    honest: bool = True
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
class Pail:
    id: str
    label: str
    phrase: str
    size: str
    color: str
    use: str
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
class Conflict:
    id: str
    title: str
    trigger: str
    pressure: str
    resolution: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["missing"] >= THRESHOLD and ("worry" not in ent.memes or ent.memes["worry"] < THRESHOLD):
            sig = ("worry", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["missing"] < THRESHOLD or ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["anger"] += 1
        out.append("__conflict__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["closed"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relief"] += 1
        ent.memes["worry"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("conflict", "social", _r_conflict),
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


def clue_suggests(setting: Setting, suspect: Suspect, pail: Pail) -> bool:
    return "pail" in suspect.tags and "pail" in pail.tags and setting.id in suspect.tags


def missing_reason(suspect: Suspect, conflict: Conflict) -> str:
    return f"{suspect.label} had moved the pail so the {conflict.title.lower()} could happen"


def reasonableness_gate(setting: Setting, suspect: Suspect, pail: Pail, conflict: Conflict) -> bool:
    return clue_suggests(setting, suspect, pail) and conflict.id == "conflict"


def sleuth_predict(world: World, suspect_id: str) -> dict:
    sim = world.copy()
    _move_pail(sim, sim.get("pail"), sim.get(suspect_id), narrate=False)
    return {
        "missing": sim.get("pail").meters["missing"] >= THRESHOLD,
        "relief": sim.get("kid").memes["relief"],
    }


def _move_pail(world: World, pail_ent: Entity, suspect_ent: Entity, narrate: bool = True) -> None:
    pail_ent.meters["missing"] = 1.0
    pail_ent.meters["moved"] = 1.0
    suspect_ent.attrs["handled"] = "pail"
    propagate(world, narrate=narrate)


def ask_question(world: World, kid: Entity, setting: Setting, conflict: Conflict) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"{kid.id} stared at the empty spot by {setting.clue_place} and whispered, "
        f'"Who took the {world.facts["pail"].label}?"'
    )
    world.say(
        f"It was the sort of question that made a small {conflict.title.lower()} feel like a big one."
    )


def suspect_move(world: World, suspect: Entity, pail: Pail, setting: Setting) -> None:
    suspect.memes["curiosity"] += 1
    world.say(
        f"{suspect.id} had been near {setting.place}, where the {pail.label} was kept for water and chores."
    )
    world.say(
        f"But {suspect.id} said {suspect.pronoun()} only wanted to {suspect.attrs.get('motive', 'help')}."
    )


def argue(world: World, kid: Entity, suspect: Entity, conflict: Conflict) -> None:
    kid.memes["anger"] += 1
    suspect.memes["worry"] += 1
    world.say(
        f'"{suspect.id}, you moved it!" {kid.id} said, and the room filled with {conflict.pressure}.'
    )


def reveal(world: World, kid: Entity, suspect: Entity, pail: Pail, setting: Setting) -> None:
    suspect.meters["closed"] += 1
    pail.meters["missing"] = 0.0
    kid.memes["relief"] += 1
    world.say(
        f"Then {kid.id} found the clue by {setting.clue_place}: a wet ring, the same shape as the {pail.label}."
    )
    world.say(
        f"That was enough to show the truth. {suspect.id} had set the {pail.label} by the door after helping carry water."
    )


def resolution(world: World, kid: Entity, suspect: Entity, conflict: Conflict) -> None:
    kid.memes["anger"] = 0.0
    world.say(
        f'"So you were helping," {kid.id} said at last. The {conflict.title.lower()} softened right away.'
    )
    world.say(
        f"{suspect.id} nodded, and the two of them laughed because the mystery had been solved without any more fuss."
    )


def ending_image(world: World, pail: Pail, setting: Setting, conflict: Conflict) -> None:
    world.say(
        f"By the end, the {pail.label} was back in its spot by {setting.place}, and the little {conflict.title.lower()} was over."
    )
    world.say(
        "The room felt quiet again, like a mystery that had finally told the truth."
    )


def tell(setting: Setting, suspect: Suspect, pail: Pail, conflict: Conflict,
         kid_name: str = "Mina", kid_type: str = "girl") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="sleuth"))
    adult = world.add(Entity(id=suspect.id, kind="character", type="adult", role="suspect"))
    bucket = world.add(Entity(id="pail", type="thing", label=pail.label))
    world.facts["kid"] = kid
    world.facts["suspect"] = adult
    world.facts["pail"] = bucket
    world.facts["setting"] = setting
    world.facts["conflict"] = conflict
    world.facts["pail_cfg"] = pail

    world.say(
        f"On a quiet {setting.weather} afternoon, {kid.id} noticed that the {pail.label} was gone from {setting.place}."
    )
    world.say(
        f"{kid.id} liked the little {pail.label}; it was used for {pail.use}, and its {pail.color} color always stood out."
    )
    world.para()
    ask_question(world, kid, setting, conflict)
    suspect_move(world, adult, pail, setting)
    argue(world, kid, adult, conflict)

    world.para()
    reveal(world, kid, adult, pail, setting)
    resolution(world, kid, adult, conflict)
    world.para()
    ending_image(world, pail, setting, conflict)

    world.facts["outcome"] = "solved"
    return world


SETTINGS = {
    "hall": Setting("hall", "a quiet hall", "the shelf", "the doorway", "rainy", {"hall", "pail"}),
    "garden": Setting("garden", "a back garden", "the bench", "the gate", "sunny", {"garden", "pail"}),
    "kitchen": Setting("kitchen", "a tidy kitchen", "the table", "the sink", "cloudy", {"kitchen", "pail"}),
}

PAILS = {
    "red": Pail("red", "red pail", "a red pail", "small", "red", "carry water", {"pail", "red"}),
    "blue": Pail("blue", "blue pail", "a blue pail", "small", "blue", "fetch water", {"pail", "blue"}),
    "tin": Pail("tin", "tin pail", "a tin pail", "small", "silver", "hold pebbles", {"pail", "tin"}),
}

SUSPECTS = {
    "nora": Suspect("Nora", "Nora", "carry water", "the porch", honest=True, tags={"garden", "pail"}),
    "ben": Suspect("Ben", "Ben", "help with chores", "the sink", honest=True, tags={"kitchen", "pail"}),
    "jo": Suspect("Jo", "Jo", "set things right", "the shelf", honest=True, tags={"hall", "pail"}),
}

CONFLICTS = {
    "marry": Conflict("marry", "marry", "a wedding plan was being discussed", "a sharp argument", "the truth made everyone calm", {"marry", "conflict"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    pail: str
    conflict: str
    kid: str
    kid_type: str
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


KNOWLEDGE = {
    "pail": [("What is a pail?", "A pail is a bucket with a handle. People use it to carry water or other small things.")],
    "marry": [("What does it mean to marry?", "To marry means to become husband and wife in a wedding.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery.")],
    "conflict": [("What is a conflict in a story?", "A conflict is a problem or disagreement that the characters have to work through.")],
    "water": [("Why keep a pail near water?", "A pail can help carry water for chores, cleaning, or gardening.")],
    "mystery": [("What does a detective do?", "A detective looks for clues, asks questions, and tries to solve a mystery.")],
}

KNOWLEDGE_ORDER = ["mystery", "clue", "pail", "water", "marry", "conflict"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for sus_id, suspect in SUSPECTS.items():
            for pid, pail in PAILS.items():
                for cid, conflict in CONFLICTS.items():
                    if reasonableness_gate(setting, suspect, pail, conflict):
                        combos.append((sid, sus_id, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the words "marry" and "{f["pail_cfg"].label}".',
        f"Tell a mystery where {f['kid'].id} wonders who moved the {f['pail_cfg'].label}, and the answer leads to a small conflict being solved.",
        f'Write a calm detective story for a young child with a missing pail, a clue, and an ending that proves who was helping.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    suspect = f["suspect"]
    pail = f["pail_cfg"]
    setting = f["setting"]
    conflict = f["conflict"]
    return [
        ("What was missing?",
         f"The {pail.label} was missing from {setting.place}, which is why {kid.id} started asking questions."),
        ("Who was the mystery about?",
         f"It was about {suspect.id}, because the clues showed {suspect.id} had moved the {pail.label} while helping."),
        ("Why did the conflict happen?",
         f"The conflict happened because {kid.id} thought the {pail.label} had been taken for no good reason. The clue by {setting.clue_place} showed it was really part of {suspect.id}'s helpful work."),
        ("How did the story end?",
         f"It ended with the truth found and the {pail.label} back where it belonged. The conflict faded, and everyone was calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = set(world.facts["pail_cfg"].tags) | {"mystery", "clue", "conflict", "marry"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "nora", "red", "marry", "Mina", "girl"),
    StoryParams("garden", "jo", "blue", "marry", "Pip", "boy"),
    StoryParams("kitchen", "ben", "tin", "marry", "Ada", "girl"),
]


def explain_rejection() -> str:
    return "(No story: the chosen pieces do not create a believable pail mystery.)"


ASP_RULES = r"""
missing(P) :- pail(P), moved(P).
worry(K) :- kid(K), missing(_).
conflict(K) :- worry(K), kid(K).
solved(P) :- clue(P), missing(P), honest_move(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for pid in PAILS:
        lines.append(asp.fact("pail", pid))
        lines.append(asp.fact("clue", pid))
    lines.append(asp.fact("kid", "kid"))
    lines.append(asp.fact("moved", "red"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show missing/1.\n#show conflict/1.\n"))
    ok = bool(model)
    if ok:
        print("OK: ASP program loaded.")
    else:
        print("MISMATCH: ASP program failed.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"MISMATCH: generation failed: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with marry and pail.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--pail", choices=PAILS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--kid")
    ap.add_argument("--kid-type", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.pail is None or c[2] == args.pail)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, suspect, pail = rng.choice(sorted(combos))
    conflict = args.conflict or "marry"
    kid_type = args.kid_type or rng.choice(["girl", "boy"])
    kid = args.kid or rng.choice(["Mina", "Pip", "Ada", "June", "Noa", "Lena"])
    return StoryParams(setting, suspect, pail, conflict, kid, kid_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SUSPECTS[params.suspect], PAILS[params.pail], CONFLICTS[params.conflict], params.kid, params.kid_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show missing/1.\n#show conflict/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if args.all:
            p = sample.params
            header = f"### {p.kid}: {p.pail} in {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
