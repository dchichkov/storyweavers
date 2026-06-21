#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/worrisome_application_repetition_conflict_bad_ending_detective.py
=================================================================================================

A small detective-story world about a worrisome application, repeated alibis,
a growing conflict, and a bad ending.

Seed prompt:
- Words: worrisome, application
- Features: Repetition, Conflict, Bad Ending
- Style: Detective Story

This script creates a standalone storyworld with typed entities, physical meters,
emotional memes, a reasonableness gate, an ASP twin, and Q&A generated from the
simulated world state.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "detective"}
        male = {"boy", "father", "man", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    mood: str
    places: list[str]

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
class CaseFile:
    id: str
    label: str
    subject: str
    clues: list[str]
    repeated_phrase: str
    conflict_line: str
    bad_outcome: str
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
class Application:
    id: str
    label: str
    title: str
    section: str
    worry: str
    outcome: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    casefile: str
    application: str
    detective: str
    partner: str
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


SETTINGS = {
    "office": Setting("office", "the little detective office", "rainy and quiet", ["desk", "hall"]),
    "station": Setting("station", "the police station", "busy and echoing", ["desk", "hall"]),
    "library": Setting("library", "the old library", "silent and dusty", ["desk", "hall"]),
}

CASEFILES = {
    "missing_cookie": CaseFile(
        "missing_cookie", "the missing cookie case", "a jar of cookies",
        ["crumbs", "a sticky note", "a tiny shoe print"],
        "I did not take the cookies", "You said that twice.",
        "the trail ended at the open window", {"case", "repetition", "conflict", "bad"}
    ),
    "borrowed_bike": CaseFile(
        "borrowed_bike", "the borrowed bike case", "a shiny bike",
        ["mud on the tire", "a bent bell", "a torn flyer"],
        "I only borrowed it", "You only borrowed it twice.",
        "the bike was gone from the alley", {"case", "repetition", "conflict", "bad"}
    ),
    "lost_map": CaseFile(
        "lost_map", "the lost map case", "a treasure map",
        ["faint pencil marks", "a torn corner", "an ink smear"],
        "I saw nothing strange", "You said that three times.",
        "the map was burned in the stove", {"case", "repetition", "conflict", "bad"}
    ),
}

APPLICATIONS = {
    "job_form": Application("job_form", "the job application", "work at the museum", "address line",
                            "the handwriting looked shaky", "the form was torn", {"application", "worrisome"}),
    "club_form": Application("club_form", "the club application", "join the detective club", "reason line",
                             "the answers kept changing", "the paper was crumpled", {"application", "worrisome"}),
    "permit_form": Application("permit_form", "the permit application", "borrow the key ring", "signature line",
                               "the dates did not match", "the stamp was missing", {"application", "worrisome"}),
}

NAMES = {
    "detective": ["Mina", "Leo", "Nora", "Sam", "Ivy", "Ben"],
    "partner": ["Pip", "Jo", "Max", "Tia", "Zed", "Liv"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for case in CASEFILES:
            for app in APPLICATIONS:
                combos.append((setting, case, app))
    return combos


def repeated_warning(text: str, times: int) -> str:
    if times == 2:
        return f"{text} {text}"
    if times == 3:
        return f"{text} {text} {text}"
    return " ".join([text] * times)


def _up(world: World, eid: str, meter: str, amount: float = 1.0) -> None:
    world.get(eid).meters[meter] += amount


def setup_scene(world: World, detective: Entity, partner: Entity, setting: Setting, app: Application) -> None:
    detective.memes["curiosity"] += 1
    partner.memes["worry"] += 1
    world.say(
        f"On a rainy afternoon, {detective.id} and {partner.id} worked in {setting.label}. "
        f"The room felt {setting.mood}, and a worrisome application sat on the desk."
    )
    world.say(
        f"{detective.id} studied the {app.label} for {app.title}. "
        f"{partner.id} kept glancing at the same line again and again."
    )


def inspect_case(world: World, detective: Entity, casefile: CaseFile) -> None:
    detective.memes["focus"] += 1
    world.say(
        f'{detective.id} leaned over the file and said, "This is the {casefile.label}." '
        f"The clues were {', '.join(casefile.clues[:-1])}, and {casefile.clues[-1]}."
    )


def repeat_phrase(world: World, casefile: CaseFile) -> None:
    world.say(
        f"The suspect kept repeating one thing: \"{casefile.repeated_phrase}\" "
        f"\"{casefile.repeated_phrase}\"."
    )


def argue(world: World, detective: Entity, partner: Entity, casefile: CaseFile, app: Application) -> None:
    detective.memes["stress"] += 1
    partner.memes["stress"] += 1
    partner.memes["fear"] += 1
    world.say(
        f'{partner.id} pointed at the application and whispered, "That form is worrisome." '
        f"{detective.id} did not answer at once."
    )
    world.say(
        f'Then the two of them argued about it: "{casefile.conflict_line}" "{casefile.conflict_line}"'
    )


def chase_leads(world: World, detective: Entity, casefile: CaseFile) -> None:
    world.say(
        f"{detective.id} hurried down the hall, following the clues one by one. "
        f"But every clue led to the same empty place."
    )
    world.say(
        f"At the end of the trail, {casefile.bad_outcome}."
    )


def bad_finish(world: World, detective: Entity, partner: Entity, app: Application) -> None:
    detective.memes["failure"] += 1
    partner.memes["sadness"] += 1
    world.say(
        f"By sunset, the case was lost. The {app.label} stayed on the desk, and no one trusted it."
    )
    world.say(
        f"{detective.id} closed the file slowly, while {partner.id} stared at the dark window. "
        f"The room was quiet, but the answer was gone."
    )


def tell(setting: Setting, casefile: CaseFile, app: Application,
         detective_name: str, partner_name: str) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", role="detective"))
    partner = world.add(Entity(id=partner_name, kind="character", type="detective", role="partner"))

    world.add(Entity(id="desk", label="the desk"))
    world.add(Entity(id="file", label=casefile.label))
    world.add(Entity(id="app", label=app.label))

    setup_scene(world, detective, partner, setting, app)
    world.para()
    inspect_case(world, detective, casefile)
    repeat_phrase(world, casefile)
    argue(world, detective, partner, casefile, app)
    world.para()
    chase_leads(world, detective, casefile)
    bad_finish(world, detective, partner, app)

    world.facts.update(
        setting=setting, casefile=casefile, app=app,
        detective=detective, partner=partner,
        repetition=True, conflict=True, bad_ending=True,
    )
    _up(world, detective.id, "stress", 1)
    _up(world, partner.id, "stress", 1)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child that uses the words "worrisome" and "application".',
        f"Tell a short detective mystery where {f['detective'].id} finds a {f['app'].label} that looks worrisome, and the story repeats a line again and again.",
        f"Write a sad detective story with repetition and a disagreement, ending with the case going badly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, par, app, casefile = f["detective"], f["partner"], f["app"], f["casefile"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {det.id} and {par.id}, two detectives trying to solve a case. The story also centers on a worrisome application on the desk."
        ),
        QAItem(
            question="Why did the detectives argue?",
            answer=f"They argued because the application looked worrisome and the clues pointed in different directions. The same warning came up again and again, which made the tension grow."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: {casefile.bad_outcome}. The detectives were left with an empty answer instead of a solved case."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve mysteries."
        ),
        QAItem(
            question="What does an application mean?",
            answer="An application is a form or paper that someone fills out to ask for a job, a club, or permission."
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing something again and again. Writers use it to make a feeling stronger."
        ),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
repeated :- casefile(C), repetition(C).
conflict  :- application(A), worrisome(A).
bad_end   :- casefile(C), application(A), repeated, conflict.
valid(S,C,A) :- setting(S), casefile(C), application(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASEFILES:
        lines.append(asp.fact("casefile", cid))
        lines.append(asp.fact("repetition", cid))
    for aid in APPLICATIONS:
        lines.append(asp.fact("application", aid))
        lines.append(asp.fact("worrisome", aid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a worrisome application.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--casefile", choices=CASEFILES)
    ap.add_argument("--application", choices=APPLICATIONS)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
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
              and (args.casefile is None or c[1] == args.casefile)
              and (args.application is None or c[2] == args.application)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, casefile, application = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(NAMES["detective"])
    partner = args.partner or rng.choice([n for n in NAMES["partner"] if n != detective])
    return StoryParams(setting, casefile, application, detective, partner)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CASEFILES[params.casefile], APPLICATIONS[params.application],
                 params.detective, params.partner)
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


CURATED = [
    StoryParams("office", "missing_cookie", "job_form", "Mina", "Pip"),
    StoryParams("station", "borrowed_bike", "club_form", "Leo", "Jo"),
    StoryParams("library", "lost_map", "permit_form", "Nora", "Liv"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, c, a in asp_valid_combos():
            print(f"  {s} {c} {a}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
