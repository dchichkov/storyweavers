#!/usr/bin/env python3
"""
storyworlds/worlds/dentist_problem_solving_kindness_misunderstanding_ghost_story.py
===================================================================================

A standalone storyworld about a dentist, a small ghostly misunderstanding, and a
kindly solved problem. The domain aims for a gentle ghost-story mood: a quiet
office, a nervous child, a misunderstood rattling sound, and a careful fix that
turns fear into relief.

The world is state-driven. Actors have physical meters and emotional memes, and
the story is generated from simulated changes rather than from a frozen template.

Core premise:
- A child comes to the dentist for a tooth problem.
- A strange sound or sight causes a ghost misunderstanding.
- Kindness and problem solving reveal the "ghost" to be something ordinary.
- The ending proves what changed by showing relief and a calmer room.

This file is self-contained and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "dentist"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    hush: str
    light: str
    smells: str


@dataclass
class Problem:
    id: str
    label: str
    tooth_issue: str
    sound: str
    shadow: str
    misunderstanding: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters["fear"] >= THRESHOLD and ("fear", ent.id) not in world.fired:
                world.fired.add(("fear", ent.id))
                ent.meters["shiver"] += 1
                produced.append(f"{ent.id} shivered and looked around the room.")
                changed = True
            if ent.meters["calm"] >= THRESHOLD and ("calm", ent.id) not in world.fired:
                world.fired.add(("calm", ent.id))
                ent.meters["fear"] = max(0.0, ent.meters["fear"] - 1)
                produced.append(f"{ent.id} felt a little steadier.")
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "evening_clinic": Setting(
        place="the quiet dental clinic",
        hush="soft",
        light="low and gold",
        smells="mint and soap",
    ),
    "small_town_office": Setting(
        place="the little dentist office",
        hush="still",
        light="bright and gentle",
        smells="clean gloves and mint",
    ),
}

PROBLEMS = {
    "rattling_drawer": Problem(
        id="rattling_drawer",
        label="a rattling drawer",
        tooth_issue="a loose tooth",
        sound="rattle",
        shadow="a wobbling shadow",
        misunderstanding="a ghost hiding in the office",
        fix_hint="the drawer was not haunted at all; it just needed to be closed",
        tags={"ghost", "misunderstanding"},
    ),
    "mask_shadow": Problem(
        id="mask_shadow",
        label="a mask on the chair",
        tooth_issue="a sore tooth",
        sound="soft rustle",
        shadow="a pale face in the chair",
        misunderstanding="a friendly ghost sitting by the lamp",
        fix_hint="the mask was only hanging on the chair back",
        tags={"ghost", "misunderstanding"},
    ),
    "vent_whisper": Problem(
        id="vent_whisper",
        label="a whisper from the vent",
        tooth_issue="a chipped tooth",
        sound="whisper",
        shadow="a thin white shape",
        misunderstanding="a ghost in the ceiling",
        fix_hint="the vent was simply moving air",
        tags={"ghost", "misunderstanding"},
    ),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="the lamp", use="shine a clear light", solves={"shadow"}),
    "mirror": Tool(id="mirror", label="a small mirror", use="show the hidden drawer", solves={"drawer"}),
    "tape": Tool(id="tape", label="quiet tape", use="hold the drawer shut", solves={"rattle"}),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Elsie", "June", "Poppy"]
BOY_NAMES = ["Ben", "Owen", "Theo", "Sam", "Leo", "Finn"]
DENTIST_NAMES = ["Dr. Hall", "Dr. Green", "Dr. Snow", "Dr. Reed"]
TRAITS = ["nervous", "curious", "brave", "gentle", "quiet"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child_name: str
    child_gender: str
    dentist_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if pid == "rattling_drawer" and tid in {"mirror", "tape"}:
                    combos.append((sid, pid, tid))
                elif pid == "mask_shadow" and tid == "lamp":
                    combos.append((sid, pid, tid))
                elif pid == "vent_whisper" and tid == "lamp":
                    combos.append((sid, pid, tid))
    return combos


ASP_RULES = r"""
problem_valid(S,P,T) :- setting(S), problem(P), tool(T), allowed(P,T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid, pid, tid in valid_combos():
        lines.append(asp.fact("allowed", pid, tid))
        lines.append(asp.fact("valid", sid, pid, tid))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story dentist world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--dentist")
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    dentist_name = args.dentist or rng.choice(DENTIST_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        problem=problem,
        tool=tool,
        child_name=child_name,
        child_gender=child_gender,
        dentist_name=dentist_name,
        trait=trait,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if (params.setting, params.problem, params.tool) not in valid_combos():
        raise StoryError("This problem and tool do not make a sensible story here.")


def predict(world: World) -> dict:
    child = world.get("child")
    prob = world.facts["problem"]
    tool = world.facts["tool"]
    sim = world.copy()
    if prob.id == "rattling_drawer" and tool.id in {"mirror", "tape"}:
        sim.get("child").memes["calm"] += 1
    return {"fear": child.meters["fear"], "calm": child.meters["calm"]}


def tell(setting: Setting, problem: Problem, tool: Tool, child_name: str, child_gender: str,
         dentist_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    dentist = world.add(Entity(id="dentist", kind="character", type="dentist", label=dentist_name))
    room = world.add(Entity(id="room", kind="place", type="room", label=setting.place))
    child.attrs["trait"] = trait
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["room"] = room
    world.say(f"{child_name} came to {setting.place} with a sore tooth and a nervous heart.")
    world.say(f"The room was {setting.hush}, with {setting.light} light and a smell of {setting.smells}.")
    world.say(f"{dentist_name} smiled kindly and asked what was wrong.")
    world.para()
    child.meters["fear"] += 1
    world.say(f"Then {child_name} heard {problem.sound} from {problem.label} and thought of {problem.misunderstanding}.")
    world.say(f"{child_name} whispered that the office might be haunted.")
    dentist.memes["kindness"] += 1
    child.memes["misunderstanding"] += 1
    world.say(f"{dentist_name} did not laugh. {dentist_name} looked carefully and promised to help.")
    world.para()
    if problem.id == "rattling_drawer":
        world.say(f"With {tool.label}, {dentist_name} showed that the noise came from the drawer itself.")
        world.say(f"The little drawer was only stuck open, and {problem.fix_hint}.")
        child.meters["fear"] = max(0.0, child.meters["fear"] - 1)
        child.memes["relief"] += 1
        child.memes["kindness"] += 1
    elif problem.id == "mask_shadow":
        world.say(f"{dentist_name} lifted {tool.label} and showed that the pale face was only {problem.fix_hint}.")
        child.meters["fear"] = max(0.0, child.meters["fear"] - 1)
        child.memes["relief"] += 1
        child.memes["kindness"] += 1
    else:
        world.say(f"{dentist_name} shone {tool.label} toward the vent and showed that {problem.fix_hint}.")
        child.meters["fear"] = max(0.0, child.meters["fear"] - 1)
        child.memes["relief"] += 1
        child.memes["kindness"] += 1
    world.para()
    world.say(f"At last, the tooth was cleaned and gently fixed.")
    world.say(f"{child_name} smiled, because the ghost was only a misunderstanding, and the dentist had solved it with kindness.")
    world.facts.update(child=child, dentist=dentist, setting=setting, problem=problem, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story for a child named {f['child'].label} who visits a dentist and thinks an office sound is a ghost.",
        f"Tell a kind story where {f['child'].label} meets {f['dentist'].label_word} at {world.setting.place} and the scary thing turns out to be ordinary.",
        f"Write a short story with a misunderstanding, problem solving, and kindness in a quiet dentist office.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    dentist = f["dentist"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Why did {child.label} think the office might be haunted?",
            answer=f"{child.label} heard {problem.sound} from {problem.label}, so the child thought a ghost might be hiding there. It was a misunderstanding caused by a strange little noise and shadow.",
        ),
        QAItem(
            question=f"How did {dentist.label_word} help {child.label}?",
            answer=f"{dentist.label_word} helped by staying calm, looking carefully, and using {tool.label} to show what the strange sound really was. The dentist solved the problem kindly instead of scaring the child more.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{child.label} felt calmer and braver, and the office no longer seemed haunted. The ghost turned out to be only {problem.fix_hint}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a dentist do?", answer="A dentist looks after teeth, helps clean them, and fixes tooth problems so a mouth stays healthy."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something is one thing, but it is really something else."),
        QAItem(question="Why can kindness help when someone is scared?", answer="Kindness helps because a calm voice and a gentle action can make scary things feel smaller and safer."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def valid_asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n"


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.child_name, params.child_gender, params.dentist_name, params.trait)
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


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(valid_asp_program())
    triples = set(asp.atoms(model, "valid"))
    py = set(valid_combos())
    if triples == py:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(triples - py))
    print("PY only:", sorted(py - triples))
    return 1


CURATED = [
    StoryParams(setting="evening_clinic", problem="rattling_drawer", tool="mirror", child_name="Mia", child_gender="girl", dentist_name="Dr. Snow", trait="nervous"),
    StoryParams(setting="small_town_office", problem="mask_shadow", tool="lamp", child_name="Ben", child_gender="boy", dentist_name="Dr. Green", trait="curious"),
    StoryParams(setting="evening_clinic", problem="vent_whisper", tool="lamp", child_name="Nora", child_gender="girl", dentist_name="Dr. Reed", trait="quiet"),
]


def build_random_sample(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(valid_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(valid_asp_program())
        combos = sorted(set(asp.atoms(model, "valid")))
        for t in combos:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = build_random_sample(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
