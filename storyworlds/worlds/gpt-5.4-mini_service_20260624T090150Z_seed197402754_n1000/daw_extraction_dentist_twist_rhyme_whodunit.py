#!/usr/bin/env python3
"""
storyworlds/worlds/daw_extraction_dentist_twist_rhyme_whodunit.py
=================================================================

A tiny whodunit story world set in a dental clinic.

Seed tale:
---
Daw goes to the dentist for an extraction. Something small and important goes
missing in the clinic. The dentist, Twist, and Rhyme follow the clues and solve
the mystery. In the end, the extraction is done, the missing thing is found,
and the truth is spoken plainly.

Story shape:
- setup: Daw arrives at the clinic for an extraction
- tension: a small dental tool or token goes missing
- turn: Twist and Rhyme uncover the clue pattern
- resolution: the dentist explains who did it, and the work finishes safely

The story is intentionally simple, child-facing, and mystery-flavored.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dental clinic"
    affords: set[str] = field(default_factory=lambda: {"extraction"})


@dataclass
class Incident:
    id: str
    verb: str
    noun: str
    clue: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    incident: str
    culprit: str
    name: str
    age: int
    seed: Optional[int] = None


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_worry(world: World) -> list[str]:
    out = []
    daw = world.get("Daw")
    if daw.memes.get("pain", 0) >= THRESHOLD and ("worry", "Daw") not in world.fired:
        world.fired.add(("worry", "Daw"))
        daw.memes["fear"] = daw.memes.get("fear", 0) + 1
        out.append("Daw kept still, but worry sat in the chair beside the pain.")
    return out


def _r_find_clue(world: World) -> list[str]:
    out = []
    if world.facts.get("clue_found") and ("find_clue",) not in world.fired:
        world.fired.add(("find_clue",))
        out.append("The clue mattered because it pointed to the real culprit.")
    return out


CAUSAL_RULES = [
    ("worry", _r_worry),
    ("find_clue", _r_find_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_extraction(world: World, incident: Incident, narrate: bool = True) -> None:
    daw = world.get("Daw")
    dentist = world.get("Dentist")
    daw.meters["pain"] = max(0.0, daw.meters.get("pain", 0.0) - 1.0)
    dentist.memes["care"] = dentist.memes.get("care", 0.0) + 1
    world.facts["done"] = True
    propagate(world, narrate=narrate)


SETTINGS = {
    "clinic": Setting(place="the dental clinic", affords={"extraction"}),
}

INCIDENTS = {
    "tooth": Incident(
        id="tooth",
        verb="remove the bad tooth",
        noun="tooth",
        clue="a tiny tooth-shaped sticker",
        risk="keep the mouth safe",
        tags={"tooth", "clinic", "mystery"},
    ),
    "cap": Incident(
        id="cap",
        verb="take out the loose cap",
        noun="cap",
        clue="a shining cap tray",
        risk="keep the toothwork clean",
        tags={"cap", "clinic", "mystery"},
    ),
}

CULPRITS = {
    "Twist": "Twist",
    "Rhyme": "Rhyme",
    "mirror": "the mirror",
}

NAMES = ["Daw", "Milo", "Nina", "Pip", "Tara", "Bea"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("clinic", inc.id, c) for inc in INCIDENTS.values() for c in CULPRITS]


@dataclass
class StoryState:
    world: World
    incident: Incident
    culprit: str


def tell(setting: Setting, incident: Incident, culprit: str, name: str) -> World:
    world = World(setting)
    daw = world.add(Entity(id="Daw", kind="character", type="child", label=name))
    dentist = world.add(Entity(id="Dentist", kind="character", type="dentist", label="the dentist"))
    twist = world.add(Entity(id="Twist", kind="character", type="helper", label="Twist"))
    rhyme = world.add(Entity(id="Rhyme", kind="character", type="helper", label="Rhyme"))
    object_ = world.add(Entity(
        id="Object",
        type="thing",
        label=incident.noun,
        phrase=incident.clue,
        owner="Dentist",
        caretaker="Dentist",
    ))

    daw.meters["pain"] = 1.0
    daw.memes["worry"] = 1.0

    world.say(f"Daw went to {setting.place} because a sore {incident.noun} needed an extraction.")
    world.say(f"The dentist smiled kindly and said the work would be quick and careful.")
    world.say(f"Twist and Rhyme were there too, watching the little room with bright eyes.")

    world.para()
    world.say(f"Then something small went missing: {object_.phrase}.")
    world.say(f"The dentist looked at the tray, and Daw looked at {incident.noun} with a frightened face.")
    world.say(f'"This is a mystery," said the dentist. "But good clues always tell the truth."')

    world.para()
    if culprit == "Twist":
        world.say("Twist had only spun the chair to cheer Daw up, and the clue was caught in the chair wheel.")
        world.say("Rhyme noticed the loop of movement and followed it back to the tray.")
    elif culprit == "Rhyme":
        world.say("Rhyme had moved the clue to make a little song with the tools, then forgot to put it back.")
        world.say("Twist spotted the rhyme pattern and asked the right question.")
    else:
        world.say("The mirror had reflected the tray in a tricky way, so everyone searched the wrong place first.")
        world.say("Twist and Rhyme compared what they saw, and the answer finally made sense.")

    world.facts.update(
        daw=daw,
        dentist=dentist,
        twist=twist,
        rhyme=rhyme,
        object=object_,
        culprit=culprit,
        incident=incident,
        setting=setting,
        clue_found=True,
        done=True,
    )

    world.para()
    world.say(f"The dentist found the missing clue, and the extraction could finally begin.")
    if incident.id == "tooth":
        world.say("The bad tooth came out cleanly, and Daw could breathe easier at once.")
    else:
        world.say(f"The loose {incident.noun} came out smoothly, and the little mouth stayed calm.")
    world.say("By the end, Daw was safe, the room was tidy, and the mystery had an honest answer.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inc = f["incident"]
    return [
        f'Write a short whodunit for a child named {f["daw"].label} at {world.setting.place} with a {inc.noun} extraction.',
        f"Tell a mystery story where the dentist, Twist, and Rhyme solve what happened to a tiny clue.",
        f'Write a simple whodunit that includes the words "daw", "extraction", and "dentist".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inc = f["incident"]
    culprit = f["culprit"]
    return [
        QAItem(
            question=f"Why did Daw go to the dental clinic?",
            answer=f"Daw went there for an extraction, because the {inc.noun} needed careful help from the dentist.",
        ),
        QAItem(
            question=f"What small mystery had to be solved before the extraction could begin?",
            answer=f"A tiny clue went missing, and Twist and Rhyme helped the dentist find out where it had gone.",
        ),
        QAItem(
            question=f"Who did the clues point to in the end?",
            answer=f'The clues pointed to {culprit}, and once everyone understood that, the dentist could finish the extraction safely.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist helps keep teeth healthy, checks mouths, and treats teeth that hurt or need to come out.",
        ),
        QAItem(
            question="What is an extraction?",
            answer="An extraction is when a dentist carefully removes a tooth or another small problem tooth part from the mouth.",
        ),
        QAItem(
            question="What does it mean to solve a whodunit?",
            answer="To solve a whodunit means to follow clues and figure out who did something or what really happened.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, I, C) :- setting(S), incident(I), culprit(C).
needed_extraction(I) :- incident(I).
mystery_before(I) :- incident(I).
twist_or_rhyme(C) :- culprit(C), C = Twist.
twist_or_rhyme(C) :- culprit(C), C = Rhyme.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in INCIDENTS:
        lines.append(asp.fact("incident", i))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit dental story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--incident", choices=INCIDENTS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
    ap.add_argument("--age", type=int)
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
    setting = args.setting or "clinic"
    incident = args.incident or rng.choice(list(INCIDENTS))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    name = args.name or rng.choice(NAMES)
    age = args.age or rng.randint(4, 7)
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if incident not in INCIDENTS:
        raise StoryError("Unknown incident.")
    if culprit not in CULPRITS:
        raise StoryError("Unknown culprit.")
    return StoryParams(setting=setting, incident=incident, culprit=culprit, name=name, age=age)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], INCIDENTS[params.incident], params.culprit, params.name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="clinic", incident="tooth", culprit="Twist", name="Daw", age=6),
            StoryParams(setting="clinic", incident="tooth", culprit="Rhyme", name="Daw", age=5),
            StoryParams(setting="clinic", incident="cap", culprit="mirror", name="Daw", age=7),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.incident} / {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
