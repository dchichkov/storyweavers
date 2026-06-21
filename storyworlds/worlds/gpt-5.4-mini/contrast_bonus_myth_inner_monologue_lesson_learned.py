#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/contrast_bonus_myth_inner_monologue_lesson_learned.py
======================================================================================

A small whodunit story world about a child detective, a missing bonus prize, a
rumor that feels like a myth, and a final lesson learned after a flashback.

Story shape:
- A child notices a contrast between what they expected and what they see.
- An inner monologue nudges them toward a suspect.
- A flashback reveals a clue from earlier in the day.
- A grown-up or helper explains the real cause.
- The ending proves what changed: the child learns to check facts before believing
  a story.

This world is intentionally tiny and constraint-checked. It uses typed entities,
physical meters and emotional memes, a forward-chained rule engine, QA sets
grounded in simulated state, and an inline ASP twin for parity checks.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/contrast_bonus_myth_inner_monologue_lesson_learned.py
    python storyworlds/worlds/gpt-5.4-mini/contrast_bonus_myth_inner_monologue_lesson_learned.py --qa
    python storyworlds/worlds/gpt-5.4-mini/contrast_bonus_myth_inner_monologue_lesson_learned.py --verify
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
    hush: str
    contrast: str
    bonus_spot: str
    myth: str

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
class Clue:
    id: str
    label: str
    place: str
    seen_from: str
    hint: str

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
class Suspicion:
    id: str
    label: str
    certainty: int
    line: str
    wrong_line: str

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
class Reveal:
    id: str
    label: str
    line: str
    lesson: str
    bonus_kind: str

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


def _r_memory(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("flashback") and ("memory", "flashback") not in world.fired:
        world.fired.add(("memory", "flashback"))
        kid = world.get("kid")
        kid.memes["uncertainty"] += 1
        out.append("__flashback__")
    return out


def _r_contrast(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    setting = world.facts["setting"]
    clue = world.facts["clue"]
    if kid.meters["noticed"] >= THRESHOLD and ("contrast",) not in world.fired:
        world.fired.add(("contrast",))
        kid.memes["curiosity"] += 1
        out.append(
            f"{kid.id} noticed a sharp contrast: {setting.contrast} beside {setting.bonus_spot}."
        )
        out.append(
            f"The neat place felt too quiet for the missing bonus, so {kid.id} started thinking."
        )
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reveal") and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        kid = world.get("kid")
        kid.memes["relief"] += 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("memory", "social", _r_memory), Rule("contrast", "social", _r_contrast), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def reasonableness_gate(setting: Setting, clue: Clue, suspicion: Suspicion, reveal: Reveal) -> bool:
    return clue.place == setting.bonus_spot and suspicion.certainty <= 7 and reveal.bonus_kind in {"bookmark", "badge", "coin"}


def settings() -> dict[str, Setting]:
    return {
        "library": Setting("library", "the library", "soft and quiet", "a bright hallway", "the return cart", "the old myth of the whispering stack"),
        "museum": Setting("museum", "the museum", "cool and echoey", "a glass case", "the coat check", "the myth of the sneaky statue"),
        "classroom": Setting("classroom", "the classroom", "tidy and still", "a row of desks", "the cubby shelf", "the myth of the invisible helper"),
    }


def clues() -> dict[str, Clue]:
    return {
        "bookmark": Clue("bookmark", "a shiny bookmark", "the return cart", "the shelf row", "It had a blue ribbon and a tiny star."),
        "badge": Clue("badge", "a gold reading badge", "the coat check", "the hallway", "It was clipped to a jacket by the door."),
        "coin": Clue("coin", "a bonus coin", "the cubby shelf", "the back table", "It sat under a lunchbox with a bright sticker."),
    }


def suspicions() -> dict[str, Suspicion]:
    return {
        "cat": Suspicion("cat", "the cat did it", 4, "The cat had been near the room, but that was only a guess.", "The cat looked innocent, with paws too clean for the job."),
        "wind": Suspicion("wind", "a gust of wind took it", 3, "A gust seemed possible, but the windows were shut tight.", "No wind could have reached the missing bonus."),
        "myth": Suspicion("myth", "the myth is true", 6, "The old myth sounded dramatic, like a story people repeat when they do not know.", "It felt grand, but grand stories are not always true."),
    }


def reveals() -> dict[str, Reveal]:
    return {
        "sibling": Reveal("sibling", "a sibling moved it", "The truth was simple: a sibling had moved the bonus to keep it safe.", "Lesson learned: check the facts before believing a rumor.", "bookmark"),
        "teacher": Reveal("teacher", "the teacher stored it", "The helper at the desk had put the bonus away for safekeeping.", "Lesson learned: a missing thing may be safely stored, not stolen.", "badge"),
        "parent": Reveal("parent", "a parent tucked it away", "A parent had hidden it on purpose as a surprise.", "Lesson learned: not every missing thing is a mystery.", "coin"),
    }


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in settings().items():
        for cid, c in clues().items():
            for xid, x in suspicions().items():
                for rid, r in reveals().items():
                    if reasonableness_gate(s, c, x, r):
                        combos.append((sid, cid, xid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspicion: str
    reveal: str
    kid: str
    kid_gender: str
    helper: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: contrast, bonus, myth.")
    ap.add_argument("--setting", choices=settings())
    ap.add_argument("--clue", choices=clues())
    ap.add_argument("--suspicion", choices=suspicions())
    ap.add_argument("--reveal", choices=reveals())
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
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


KID_NAMES = ["Mina", "Leo", "Nora", "Owen", "Ivy", "Theo", "Maya", "Finn"]
HELPER_NAMES = ["Ms. Lane", "Mr. Park", "Ms. Reed", "Mr. Bell"]
SETTINGS_REG = settings()
CLUES_REG = clues()
SUSP_REG = suspicions()
REVEALS_REG = reveals()

CURATED = [
    StoryParams("library", "bookmark", "myth", "sibling", "Mina", "girl", "Ms. Lane", "woman"),
    StoryParams("museum", "badge", "cat", "teacher", "Leo", "boy", "Mr. Bell", "man"),
    StoryParams("classroom", "coin", "wind", "parent", "Ivy", "girl", "Ms. Reed", "woman"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not support a believable whodunit.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspicion is None or c[2] == args.suspicion)
              and (args.reveal is None or c[3] == args.reveal)]
    if not combos:
        raise StoryError(explain_rejection())
    sid, cid, xid, rid = rng.choice(sorted(combos))
    kid = args.kid or rng.choice(KID_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    return StoryParams(sid, cid, xid, rid, kid, kid_gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS_REG[params.setting]
    clue = CLUES_REG[params.clue]
    suspicion = SUSP_REG[params.suspicion]
    reveal = REVEALS_REG[params.reveal]
    kid = world.add(Entity("kid", "character", params.kid_gender, label=params.kid, role="detective"))
    helper = world.add(Entity("helper", "character", params.helper_gender, label=params.helper, role="helper"))
    item = world.add(Entity("bonus", "thing", "thing", label="the missing bonus", role="mystery"))
    world.facts.update(setting=setting, clue=clue, suspicion=suspicion, reveal=reveal, flashback=True)
    kid.meters["noticed"] += 1
    kid.memes["worry"] += 1
    world.say(f"{kid.label} had promised to find the missing bonus.")
    world.say(f"The room looked {setting.hush}, but that was the odd part: the {clue.label} should have been right there.")
    world.say(f"{kid.label} thought, 'This does not fit the picture. Something is off.'")
    world.para()
    world.say(f"At first, {kid.label} had a suspicion: {suspicion.line} {suspicion.wrong_line}")
    world.say(f"{kid.label} wondered about the old myth. 'What if the myth is true?' {kid.pronoun()} asked in {kid.pronoun('possessive')} head.")
    propagate(world)
    world.para()
    world.say(f"Then came a flashback: earlier, {helper.label} had said, 'Let's keep {clue.label} safe for now.'")
    world.say(f"That memory made the answer feel less spooky and more clear.")
    world.facts["flashback"] = True
    world.facts["reveal"] = reveal
    world.say(reveal.line)
    propagate(world)
    world.para()
    world.say(f"{helper.label} smiled and pointed to {clue.place}.")
    world.say(f"{reveal.lesson}")
    kid.memes["lesson"] += 1
    item.meters["found"] += 1
    world.facts.update(kid=kid, helper=helper, item=item, outcome=reveal.id)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Setting = f["setting"]
    clue: Clue = f["clue"]
    return [
        f'Write a whodunit story for a child that includes the words "contrast", "bonus", and "myth".',
        f"Tell a mystery story set in {s.place} where something bonus-like goes missing, the child notices a contrast, and a myth turns out to be wrong.",
        f"Write a story with inner monologue, a flashback, and a lesson learned after someone finds a hidden {clue.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid: Entity = f["kid"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    clue: Clue = f["clue"]
    reveal: Reveal = f["reveal"]
    suspect: Suspicion = f["suspicion"]
    return [
        QAItem(
            question="What was the child trying to solve?",
            answer=f"{kid.label} was trying to solve the mystery of the missing bonus. The child noticed that the quiet room did not match where the bonus should have been."
        ),
        QAItem(
            question="What made the child start thinking something was wrong?",
            answer=f"The child saw a strong contrast between {setting.hush} and the empty place where {clue.label} should have been. That mismatch made the mystery feel real instead of ordinary."
        ),
        QAItem(
            question="What did the child think at first?",
            answer=f"At first, {kid.label} thought the old myth might be true and suspected {suspect.label}. But that was only a guess, not proof."
        ),
        QAItem(
            question="What changed the answer?",
            answer=f"A flashback brought back an earlier remark about keeping {clue.label} safe. That memory led to the truth: {reveal.line.lower()}"
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{reveal.lesson} The ending shows {kid.label} choosing facts over a spooky rumor."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a contrast?",
            answer="A contrast is when two things are very different, like a quiet empty spot beside a busy room."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory scene that brings back something from earlier, so the story can explain a clue."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking voice. It lets us hear worries, guesses, and careful thoughts."
        ),
        QAItem(
            question="Why should you be careful with myths?",
            answer="Myths can be fun to hear, but they are not always true. It is better to check facts before deciding."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
clue(C) :- clue_fact(C).
suspicion(X) :- suspicion_fact(X).
reveal(R) :- reveal_fact(R).

valid(S, C, X, R) :- setting(S), clue(C), suspicion(X), reveal(R),
                     clue_place(C, SP), setting_bonus(S, SB),
                     SP = SB, suspicion_certainty(X, N), N =< 7,
                     reveal_bonus_kind(R, K), good_kind(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS_REG.items():
        lines.append(asp.fact("setting_fact", sid))
        lines.append(asp.fact("setting_bonus", sid, s.bonus_spot))
    for cid, c in CLUES_REG.items():
        lines.append(asp.fact("clue_fact", cid))
        lines.append(asp.fact("clue_place", cid, c.place))
    for xid, x in SUSP_REG.items():
        lines.append(asp.fact("suspicion_fact", xid))
        lines.append(asp.fact("suspicion_certainty", xid, x.certainty))
    for rid, r in REVEALS_REG.items():
        lines.append(asp.fact("reveal_fact", rid))
        lines.append(asp.fact("reveal_bonus_kind", rid, r.bonus_kind))
    for k in ["bookmark", "badge", "coin"]:
        lines.append(asp.fact("good_kind", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    else:
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspicion is None or c[2] == args.suspicion)
              and (args.reveal is None or c[3] == args.reveal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, cid, xid, rid = rng.choice(sorted(combos))
    return StoryParams(
        sid, cid, xid, rid,
        args.kid or rng.choice(KID_NAMES),
        args.kid_gender or rng.choice(["girl", "boy"]),
        args.helper or rng.choice(HELPER_NAMES),
        args.helper_gender or rng.choice(["woman", "man"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible scenarios:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.kid} in {p.setting} ({p.clue} / {p.suspicion} / {p.reveal})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
