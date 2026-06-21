#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/climate_doctor_lesson_learned_mystery_to_solve.py
===================================================================================

A small standalone storyworld about a curious child, a doctor, and a climate
mystery that is solved with care. The stories are built as a tiny simulation:
temperature, dryness, clouds, worry, and relief all change the telling.

The world aims for a rhyming, child-friendly style with:
- Lesson Learned
- Mystery to Solve
- Rhyme
- the seed words "climate" and "doctor"

Run:
    python storyworlds/worlds/gpt-5.4-mini/climate_doctor_lesson_learned_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4-mini/climate_doctor_lesson_learned_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/climate_doctor_lesson_learned_mystery_to_solve.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doctor"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    scene: str
    climate_word: str
    clue: str
    solved_by: str
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
class Clue:
    id: str
    object_name: str
    problem: str
    fix: str
    rhyme_a: str
    rhyme_b: str
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
class Diagnosis:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    lesson: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        other = World()
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} / {b}"


def temperature_signal(setting: Setting, clue: Clue) -> str:
    if "hot" in setting.tags and "steam" in clue.tags:
        return "The air felt hot and the clue felt strange."
    if "dry" in setting.tags:
        return "The day felt dry, and the mystery felt sly."
    return "The air felt soft, but something was off."


def solve_mystery(world: World) -> list[str]:
    out: list[str] = []
    doctor = world.get("doctor")
    clue = world.facts["clue"]
    setting = world.facts["setting"]
    for token in ("worry", "mystery", "dryness"):
        if doctor.memes.get(token, 0.0) >= THRESHOLD and token not in world.fired:
            world.fired.add((token, "solve"))
            out.append("__solve__")
    if clue and setting:
        if world.get("scene").meters.get("dryness", 0.0) >= THRESHOLD:
            world.get("scene").meters["health"] = 1.0
    return out


@dataclass
class StoryParams:
    setting: str
    clue: str
    diagnosis: str
    child_name: str
    child_gender: str
    doctor_name: str
    doctor_gender: str
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


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        scene="a quiet garden",
        climate_word="climate",
        clue="wilting leaves",
        solved_by="shade",
        tags={"dry", "hot"},
    ),
    "school": Setting(
        id="school",
        place="the schoolyard",
        scene="a busy schoolyard",
        climate_word="climate",
        clue="bent flags",
        solved_by="windbreak",
        tags={"windy"},
    ),
    "clinic": Setting(
        id="clinic",
        place="the clinic yard",
        scene="a tiny clinic yard",
        climate_word="climate",
        clue="thirsty pots",
        solved_by="water",
        tags={"dry", "sunny"},
    ),
}

CLUES = {
    "wilting": Clue(
        id="wilting",
        object_name="wilting leaves",
        problem="the leaves drooped like sleepy eaves",
        fix="the plants needed shade and a sip to drink",
        rhyme_a="wilt and tilt",
        rhyme_b="sprout and shout",
        tags={"dry", "plants"},
    ),
    "steam": Clue(
        id="steam",
        object_name="steam on the window",
        problem="a misty window hummed like a kettle plume",
        fix="the room needed air to clear the foggy bloom",
        rhyme_a="steam and gleam",
        rhyme_b="breeze and ease",
        tags={"hot", "steam"},
    ),
    "whistle": Clue(
        id="whistle",
        object_name="a whistling vent",
        problem="a whistling vent kept singing all day long",
        fix="the vent needed checking, because that sound was wrong",
        rhyme_a="whistle and tristle",
        rhyme_b="fit and fix",
        tags={"windy", "noise"},
    ),
}

DIAGNOSES = {
    "shade": Diagnosis(
        id="shade",
        sense=3,
        power=3,
        text="checked the garden, found thirsty soil, and stretched a cloth for cool shade",
        fail="looked around, but the sun was still too strong to help",
        lesson="sometimes a gentle change can help the whole place feel right",
        tags={"shade", "plants"},
    ),
    "air": Diagnosis(
        id="air",
        sense=3,
        power=2,
        text="opened the window wide and let fresh air chase the mist away",
        fail="opened the window, but the fog stayed put",
        lesson="fresh air can solve a smoky little mystery",
        tags={"air", "steam"},
    ),
    "fix_vent": Diagnosis(
        id="fix_vent",
        sense=2,
        power=2,
        text="found the vent, tightened the loose cover, and quieted the whistle",
        fail="looked at the vent, but the sound kept on and on",
        lesson="small noises can be clues, and clues can lead to care",
        tags={"windy", "noise"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Luna", "Nora", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for cid, c in CLUES.items():
            for did, d in DIAGNOSES.items():
                if d.sense >= 2 and c.id == "wilting" and sid in {"garden", "clinic"} and did == "shade":
                    out.append((sid, cid, did))
                elif d.sense >= 2 and c.id == "steam" and sid == "clinic" and did == "air":
                    out.append((sid, cid, did))
                elif d.sense >= 2 and c.id == "whistle" and sid == "school" and did == "fix_vent":
                    out.append((sid, cid, did))
    return out


def explain_rejection(setting: Setting, clue: Clue, diagnosis: Diagnosis) -> str:
    return (
        f"(No story: this combination does not make a reasonable mystery. "
        f"Try a clue and diagnosis that fit the setting better.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming climate-doctor mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--diagnosis", choices=DIAGNOSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--doctor")
    ap.add_argument("--doctor-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.diagnosis is None or c[2] == args.diagnosis)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, diagnosis = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    doctor_gender = args.doctor_gender or "girl"
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    doctor = args.doctor or "Dr. Vale"
    return StoryParams(setting=setting, clue=clue, diagnosis=diagnosis, child_name=child, child_gender=child_gender, doctor_name=doctor, doctor_gender=doctor_gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    diagnosis = DIAGNOSES[params.diagnosis]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", memes={"worry": 1.0, "mystery": 1.0}))
    doctor = world.add(Entity(id=params.doctor_name, kind="character", type="doctor", role="doctor", label="the doctor", memes={"care": 1.0, "worry": 1.0}))
    scene = world.add(Entity(id="scene", kind="thing", type="scene", label=setting.scene, meters={"dryness": 1.0 if "dry" in setting.tags else 0.0}))
    world.facts.update(setting=setting, clue=clue, diagnosis=diagnosis, child=child, doctor=doctor, scene=scene)

    world.say(f"{params.child_name} had a question about the {setting.climate_word} of the day, in {setting.place}.")
    world.say(f"{temperature_signal(setting, clue)} {params.child_name} found {clue.object_name}, and the clue made a little riddle to say.")
    world.say(f'"{clue.rhyme_a}," whispered {params.child_name}, "what could it mean?"')
    world.para()
    world.say(f"The child called for {params.doctor_name}, the kind {params.doctor_gender if params.doctor_gender else 'doctor'} who listened with care.")
    doctor.memes["mystery"] = 1.0
    doctor.memes["worry"] = 1.0
    world.say(f'"Let us look," said {params.doctor_name}. "A mystery to solve should not stay unseen."')
    if diagnosis.id == "shade":
        world.say(f"{params.doctor_name} knelt by the leaves, and found the soil was dry and small. The garden needed shade and water after all.")
        world.say(f'{params.doctor_name} fixed the clue with a cloth and a careful call.')
        scene.meters["health"] = 1.0
    elif diagnosis.id == "air":
        world.say(f"{params.doctor_name} opened the window and let the fresh breeze run free. The mist drifted off like a white little sea.")
        scene.meters["health"] = 1.0
    else:
        world.say(f"{params.doctor_name} checked the wall and found the whistle in the vent. A loose cover made the strange sound that came and went.")
        scene.meters["health"] = 1.0
    world.say(f'"{diagnosis.lesson}," said {params.doctor_name}, with a smile so light and airy.')
    world.say(f"{params.child_name} nodded hard. The mystery was solved, and the air felt bright and merry.")
    world.say(f'The lesson was clear: when something feels odd, be calm, ask for help, and see. A careful look can solve a clue, like a rhyme in a nursery tree.')
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    clue: Clue = f["clue"]
    diagnosis: Diagnosis = f["diagnosis"]
    child: Entity = f["child"]
    doctor: Entity = f["doctor"]
    return [
        f'Write a rhyming mystery story for a child that includes the words "climate" and "doctor".',
        f"Tell a child-friendly mystery where {child.id} notices {clue.object_name}, then asks {doctor.id} to help solve it.",
        f"Write a short rhyming story about a {setting.place} problem, a doctor, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    doctor: Entity = f["doctor"]
    setting: Setting = f["setting"]
    clue: Clue = f["clue"]
    diagnosis: Diagnosis = f["diagnosis"]
    return [
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{doctor.id} helped solve it. {doctor.id} looked carefully, listened kindly, and found the clue that explained the problem."
        ),
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about {clue.object_name} and the strange change in {setting.place}. The clue showed that something in the place needed attention."
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson was: {diagnosis.lesson}. The story shows that calm questions and careful looking can turn a mystery into an answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is climate?",
            answer="Climate means the usual kind of weather a place has over a long time. It can be dry, wet, hot, windy, or cool."
        ),
        QAItem(
            question="What does a doctor do?",
            answer="A doctor helps people stay healthy and listens carefully when something feels wrong. Doctors use clues, questions, and care."
        ),
        QAItem(
            question="What should you do when a mystery feels scary?",
            answer="Stay calm, ask a trusted grown-up for help, and keep looking for the real clue. Careful help is better than guessing."
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
        lines.append(f"  {e.id:10} ({e.kind}) meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,D) :- setting(S), clue(C), diagnosis(D), fit(S,C,D).
fit(garden,wilting,shade).
fit(clinic,wilting,shade).
fit(clinic,steam,air).
fit(school,whistle,fix_vent).
"""


def asp_facts() -> str:
    import asp
    out = []
    for sid in SETTINGS:
        out.append(asp.fact("setting", sid))
    for cid in CLUES:
        out.append(asp.fact("clue", cid))
    for did, d in DIAGNOSES.items():
        out.append(asp.fact("diagnosis", did))
        out.append(asp.fact("sense", did, d.sense))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp  # noqa: F401
    ok = set(asp_valid_combos()) == set(valid_combos())
    sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, diagnosis=None, child=None, child_gender=None, doctor=None, doctor_gender=None), random.Random(7)))
    if not sample.story:
        ok = False
    if ok:
        print("OK: ASP parity and story generation smoke test passed.")
        return 0
    print("MISMATCH or smoke test failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.diagnosis not in DIAGNOSES:
        raise StoryError("Invalid StoryParams.")
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


CURATED = [
    StoryParams(setting="garden", clue="wilting", diagnosis="shade", child_name="Mia", child_gender="girl", doctor_name="Dr. Vale", doctor_gender="girl"),
    StoryParams(setting="clinic", clue="steam", diagnosis="air", child_name="Leo", child_gender="boy", doctor_name="Dr. Vale", doctor_gender="girl"),
    StoryParams(setting="school", clue="whistle", diagnosis="fix_vent", child_name="Nora", child_gender="girl", doctor_name="Dr. Vale", doctor_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
