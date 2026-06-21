#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prevent_missy_retain_moral_value_transformation_detective.py
=============================================================================================

A tiny detective-story world with a child witness, a missing trinket, and a
moral turn: the detective prevents a bad choice, Missy retains the truth, and a
small transformation happens in how she sees right and wrong.

Seed words and features:
- prevent
- missy
- retain
- Moral Value
- Transformation
- style: Detective Story
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    id: str
    place: str
    mood: str
    afford: set[str] = field(default_factory=set)
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
class Case:
    id: str
    title: str
    object_label: str
    object_phrase: str
    risk: str
    clue: str
    value_word: str
    transform_word: str
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
class Intervention:
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


def _r_remorse(world: World) -> list[str]:
    out: list[str] = []
    missy = world.entities.get("missy")
    if not missy or missy.meters.get("truth", 0.0) < THRESHOLD:
        return out
    sig = ("remorse",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    missy.memes["remorse"] = 1.0
    out.append("__remorse__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    missy = world.entities.get("missy")
    if not missy or missy.memes.get("remorse", 0.0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    missy.memes["moral_growth"] = 1.0
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("remorse", _r_remorse), Rule("transform", _r_transform)]


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


def case_at_risk(case: Case, setting: Setting) -> bool:
    return case.id in setting.afford


def sensible_interventions() -> list[Intervention]:
    return [i for i in INTERVENTIONS.values() if i.sense >= 2]


def story_outcome(case: Case, intervention: Intervention, delay: int) -> str:
    if intervention.sense < 2:
        return "refused"
    return "contained" if intervention.power >= 1 + delay else "missed"


def predicted_moral_world(world: World, case_id: str) -> dict:
    sim = world.copy()
    missy = sim.get("missy")
    missy.meters["truth"] = 1.0
    propagate(sim, narrate=False)
    return {
        "truth": missy.meters.get("truth", 0.0) >= THRESHOLD,
        "growth": missy.memes.get("moral_growth", 0.0) >= THRESHOLD,
    }


def setup(world: World, detective: Entity, missy: Entity, case: Case) -> None:
    world.say(
        f"On a gray afternoon at {world.setting.place}, Detective {detective.id} "
        f"studied a small puzzle. {case.title} had gone missing, and everyone kept "
        f"looking at Missy."
    )
    world.say(
        f"Missy looked scared, but she wanted to {case.risk} and keep the secret. "
        f"The room felt like a locked box full of clues."
    )


def clue_scene(world: World, detective: Entity, case: Case) -> None:
    world.say(
        f"The detective found one sharp clue: {case.clue}. That clue did not point "
        f"to a monster or a trick. It pointed to a simple choice."
    )


def prevent_scene(world: World, detective: Entity, missy: Entity, case: Case) -> None:
    world.say(
        f'"Wait," Detective {detective.id} said. "We can prevent the wrong thing '
        f'from happening. Missy, tell the truth and we can still retain what matters."'
    )
    missy.memes["fear"] = 1.0
    missy.meters["truth"] += 1.0
    propagate(world, narrate=True)


def confession_scene(world: World, detective: Entity, missy: Entity, case: Case) -> None:
    world.say(
        f"Missy took a shaky breath. She admitted she had moved {case.object_phrase} "
        f"out of place, but she had not meant to break it."
    )
    world.say(
        f"Because she told the truth, the detective could return the item and "
        f"retain the real evidence without blaming the wrong person."
    )


def resolution_scene(world: World, detective: Entity, missy: Entity, case: Case) -> None:
    world.say(
        f"The detective closed the notebook and smiled. The case was solved, "
        f"and Missy had changed. She had learned that a kind truth could be "
        f"braver than a secret."
    )
    world.say(
        f"By the end, Missy retained her courage, the room retained its calm, "
        f"and her small moral value transformation showed on her face."
    )


def tell(setting: Setting, case: Case, intervention: Intervention, *,
         detective_name: str = "June", missy_name: str = "Missy",
         detective_type: str = "woman", missy_type: str = "girl",
         delay: int = 0) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective"))
    missy = world.add(Entity(id="missy", kind="character", type=missy_type, role="witness"))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="case", type="thing", label=case.object_label))
    detective.memes["calm"] = 1.0
    missy.memes["worry"] = 1.0

    setup(world, detective, missy, case)
    world.para()
    clue_scene(world, detective, case)
    prevent_scene(world, detective, missy, case)
    if story_outcome(case, intervention, delay) == "missed":
        world.say(
            f"The chance to prevent the mistake had passed by too fast, but the "
            f"detective still helped Missy tell the truth."
        )
    world.para()
    confession_scene(world, detective, missy, case)
    resolution_scene(world, detective, missy, case)

    world.facts.update(
        detective=detective,
        missy=missy,
        case=case,
        intervention=intervention,
        setting=setting,
        delay=delay,
        outcome=story_outcome(case, intervention, delay),
    )
    return world


SETTINGS = {
    "museum": Setting(id="museum", place="the small museum", mood="quiet", afford={"frame", "coin", "statue"}),
    "library": Setting(id="library", place="the old library", mood="hushed", afford={"book", "letter", "key"}),
    "hall": Setting(id="hall", place="the front hall", mood="busy", afford={"badge", "note", "key"}),
}

CASES = {
    "coin": Case(
        id="coin",
        title="A shiny coin",
        object_label="coin",
        object_phrase="the shiny coin",
        risk="hide the coin",
        clue="a clean shoe print near the display",
        value_word="honesty",
        transform_word="care",
        tags={"coin", "truth"},
    ),
    "key": Case(
        id="key",
        title="A lost key",
        object_label="key",
        object_phrase="the little brass key",
        risk="keep the key",
        clue="a torn note with Missy's name",
        value_word="honesty",
        transform_word="truth",
        tags={"key", "truth"},
    ),
    "badge": Case(
        id="badge",
        title="A missing badge",
        object_label="badge",
        object_phrase="the brass badge",
        risk="hide the badge",
        clue="dust on the windowsill and a neat stack of books",
        value_word="responsibility",
        transform_word="courage",
        tags={"badge", "truth"},
    ),
}

INTERVENTIONS = {
    "gentle": Intervention(
        id="gentle",
        sense=3,
        power=1,
        text="spoke gently and asked for the truth",
        fail="spoke gently, but the secret stayed hidden",
        qa_text="spoke gently and asked her to tell the truth",
        tags={"talk", "truth"},
    ),
    "notebook": Intervention(
        id="notebook",
        sense=3,
        power=2,
        text="showed the notebook and matched the clue",
        fail="showed the notebook, but the clue was too weak",
        qa_text="used the notebook and matched the clue",
        tags={"clue", "truth"},
    ),
    "alarm": Intervention(
        id="alarm",
        sense=1,
        power=1,
        text="shouted too loudly and scared everyone",
        fail="shouted too loudly and made the room worse",
        qa_text="shouted too loudly",
        tags={"bad", "noise"},
    ),
}

NAMES = ["June", "Iris", "Maya", "Ada", "Nora", "Lina"]
MISSY_NAMES = ["Missy", "Mimi", "Moss", "Mina"]


@dataclass
class StoryParams:
    setting: str
    case: str
    intervention: str
    detective_name: str
    missy_name: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, case in CASES.items():
            if not case_at_risk(case, setting):
                continue
            for iid, intervention in INTERVENTIONS.items():
                if intervention.sense >= 2:
                    combos.append((sid, cid, iid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a child where Detective {f["detective"].id} '
        f'prevents Missy from making a bad choice and helps her retain the truth.',
        f"Tell a small mystery in {f['setting'].place} using the words "
        f"prevent, Missy, and retain.",
        f'Write a moral-value story where a clue leads to a transformation and '
        f'Missy learns to keep the truth.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective, missy, case = f["detective"], f["missy"], f["case"]
    qa = [
        ("Who solved the mystery?",
         f"Detective {detective.id} solved it by paying attention to the clues and "
         f"helping Missy tell the truth."),
        ("What did Missy learn?",
         f"Missy learned that it was better to tell the truth than to hide the "
         f"{case.object_label}. That choice helped her retain her good name."),
        ("Why did the detective prevent the bad choice?",
         f"The detective saw that the secret would hurt the case and the people in "
         f"it. Preventing it kept the story fair and calm."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the case end?",
            f"It ended safely because the detective used {f['intervention'].qa_text} "
            f"and Missy listened. The truth stayed in the room, and the wrong choice "
            f"never got bigger."
        ))
    else:
        qa.append((
            "How did the case end?",
            f"It still ended with the truth, even though the chance to prevent the "
            f"mistake was late. Missy told what happened, and that truth kept the "
            f"case honest."
        ))
    qa.append((
        "What changed in Missy?",
        f"She changed from hiding things to keeping the truth. That was her small "
        f"moral value transformation."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["case"].tags) | set(world.facts["intervention"].tags)
    out = []
    if "truth" in tags:
        out.append(("Why is telling the truth important?",
                    "Telling the truth helps people solve problems fairly and keeps "
                    "trust between people. It can also stop a small mistake from "
                    "turning into a bigger one."))
    if "clue" in tags or "truth" in tags:
        out.append(("What is a clue?",
                    "A clue is a small piece of information that helps solve a mystery. "
                    "A detective uses clues to figure out what happened."))
    if "coin" in tags:
        out.append(("Why can a shiny coin be important in a mystery?",
                    "A shiny coin can matter because people may notice where it was "
                    "moved or who touched it. That helps a detective follow the trail."))
    if "key" in tags:
        out.append(("What does a key do?",
                    "A key opens something that is locked. In a mystery, a key can "
                    "also be a clue about who was there."))
    if "badge" in tags:
        out.append(("What is a badge?",
                    "A badge is a small sign or pin that shows who someone is or "
                    "what job they do. It can be important in a detective story."))
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="museum", case="coin", intervention="gentle", detective_name="June", missy_name="Missy", delay=0),
    StoryParams(setting="library", case="key", intervention="notebook", detective_name="Iris", missy_name="Missy", delay=0),
    StoryParams(setting="hall", case="badge", intervention="gentle", detective_name="Ada", missy_name="Missy", delay=0),
]


def explain_rejection(case: Case, setting: Setting) -> str:
    return f"(No story: {case.object_label} does not fit this setting.)"


def explain_intervention(rid: str) -> str:
    r = INTERVENTIONS[rid]
    return f"(Refusing intervention '{rid}': it scores too low on common sense (sense={r.sense} < 2).)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: prevent, Missy, retain.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--intervention", choices=INTERVENTIONS)
    ap.add_argument("--detective-name")
    ap.add_argument("--missy-name")
    ap.add_argument("--delay", type=int, default=0)
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
    if args.intervention and INTERVENTIONS[args.intervention].sense < 2:
        raise StoryError(explain_intervention(args.intervention))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.case is None or c[1] == args.case)
              and (args.intervention is None or c[2] == args.intervention)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case, intervention = rng.choice(sorted(combos))
    detective_name = args.detective_name or rng.choice(NAMES)
    missy_name = args.missy_name or rng.choice(MISSY_NAMES)
    return StoryParams(
        setting=setting, case=case, intervention=intervention,
        detective_name=detective_name, missy_name=missy_name, delay=args.delay
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("case", CASES), ("intervention", INTERVENTIONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)!r}")
    world = tell(
        SETTINGS[params.setting], CASES[params.case], INTERVENTIONS[params.intervention],
        detective_name=params.detective_name, missy_name=params.missy_name,
        delay=params.delay,
    )
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


ASP_RULES = r"""
at_risk(C,S) :- case(C), setting(S), affords(S,C).
sensible(I) :- intervention(I), sense(I,N), N >= 2.
contained(C,I) :- at_risk(C,_), intervention(I), power(I,P), P >= 1.
outcome(safe) :- contained(_,I), sensible(I).
outcome(safe) :- case(_), setting(_), sensible(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for iid, i in INTERVENTIONS.items():
        lines.append(asp.fact("intervention", iid))
        lines.append(asp.fact("sense", iid, i.sense))
        lines.append(asp.fact("power", iid, i.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import storyworlds.asp as asp
    scenario = "\n".join([asp.fact("chosen", params.setting, params.case, params.intervention)])
    model = asp.one_model(asp_program(scenario + "\n#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "unknown"


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {k for k, v in INTERVENTIONS.items() if v.sense >= 2}:
        rc = 1
        print("MISMATCH in sensible interventions.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible interventions: {', '.join(asp_sensible())}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
