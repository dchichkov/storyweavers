#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/script_constipate_rejoice_transformation_humor_mystery.py
===============================================================================================================================

A standalone story world about a tiny stage mystery: a child, a rehearsal script,
a stuck tummy, a comic transformation, and a final burst of rejoicing.

Seed words: script, constipate, rejoice
Style: Mystery
Features: Transformation, Humor
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    effect: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    cheers: str
    solves: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "school_stage": Setting("the school stage", affords={"rehearse", "investigate"}),
    "library_corner": Setting("the library corner", affords={"rehearse", "investigate"}),
    "backyard_box": Setting("the backyard box of props", affords={"investigate"}),
}

PROBLEMS = {
    "stuck_tummy": Problem(
        id="stuck_tummy",
        label="a stuck tummy",
        clue="the puppet kept shuffling and groaning near the prop table",
        effect="could not dance or bow",
        fix="a warm drink, a slow walk, and a laugh",
        tags={"tummy", "funny", "mystery"},
    ),
    "missing_script": Problem(
        id="missing_script",
        label="a missing script page",
        clue="one page had vanished from the rehearsal folder",
        effect="nobody knew the final line",
        fix="finding the page under a hat stand",
        tags={"script", "mystery"},
    ),
    "muddy_shoes": Problem(
        id="muddy_shoes",
        label="muddy shoes",
        clue="tiny footprints pointed from the door to the curtain",
        effect="the stage could get messy",
        fix="clean cloth and a careful swap",
        tags={"funny", "mystery"},
    ),
}

REMEDIES = {
    "tea_walk": Remedy(
        id="tea_walk",
        label="warm tea and a slow walk",
        action="sip warm tea and take a slow walk",
        cheers="felt lighter and smiled again",
        solves={"stuck_tummy"},
    ),
    "page_find": Remedy(
        id="page_find",
        label="find the missing page",
        action="peek under the hat stand",
        cheers="found the missing line and grinned",
        solves={"missing_script"},
    ),
    "shoe_wipe": Remedy(
        id="shoe_wipe",
        label="wipe the muddy shoes",
        action="wipe the shoes with a soft cloth",
        cheers="the stage looked neat again",
        solves={"muddy_shoes"},
    ),
}

NAMES = ["Mina", "Toby", "Luna", "Jasper", "Ruby", "Noah"]
KINDS = ["girl", "boy"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    remedy: str
    name: str
    kind: str
    seed: Optional[int] = None


ASP_RULES = r"""
problem_with_clue(P) :- problem(P), clue(P, _).
has_fix(P) :- problem(P), remedy(R), solves(R, P).
valid_story(S, P, R) :- setting(S), problem_with_clue(P), has_fix(P), allowed(S, P, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("clue", pid, p.clue))
        lines.append(asp.fact("effect", pid, p.effect))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for p in sorted(r.solves):
            lines.append(asp.fact("solves", rid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(setting: str, problem: str, remedy: str) -> bool:
    return setting in SETTINGS and problem in PROBLEMS and remedy in REMEDIES and problem in REMEDIES[remedy].solves


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: script, constipate, rejoice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for r in REMEDIES:
                if reasonableness_gate(s, p, r):
                    out.append((s, p, r))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("No valid story matches the requested options.")
    s, p, r = rng.choice(sorted(combos))
    kind = args.kind or rng.choice(KINDS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=s, problem=p, remedy=r, name=name, kind=kind)


def tell(params: StoryParams) -> World:
    w = World(SETTINGS[params.setting])
    hero = w.add(Entity(id=params.name, kind="character", type=params.kind, traits=["curious", "humorous"]))
    script = w.add(Entity(id="script", type="script", label="the rehearsal script", owner=hero.id))
    prop = w.add(Entity(id="prop", type="thing", label="the prop box", caretaker=hero.id))
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.remedy]

    hero.memes["curiosity"] = 1
    hero.memes["hope"] = 1
    w.say(f"{hero.id} came to {w.setting.place} with a rehearsal script tucked under one arm.")
    w.say(f"The mystery was simple at first: {problem.clue}.")
    w.say(f"Everyone said {problem.label} had made the show silly and stuck, because it {problem.effect}.")
    w.para()
    w.say(f"{hero.id} read the script again and noticed one clue: the final joke was missing a beat.")
    w.say(f"That made {hero.id} suspect the trouble was not just funny bad luck.")
    if params.problem == "missing_script":
        w.say("A careful look under the hat stand revealed the lost page, folded like a secret note.")
    elif params.problem == "muddy_shoes":
        w.say("Small footprints led from the door to the curtain, so the shoes were the real clue.")
    else:
        w.say("The puppet kept patting its belly and making a face, as if a tiny drum were stuck inside.")
    w.para()
    w.say(f"Then {hero.id} tried to {remedy.action}, and the whole room held its breath.")
    hero.memes["worry"] = 0
    hero.memes["joy"] = 1
    w.say(f"After that, {hero.id} {remedy.cheers}, and the show turned from puzzling to playful.")
    w.say(f"At the end, {hero.id} could finally rejoice, because the mystery was solved and the script could be read aloud with a grin.")
    if params.problem == "stuck_tummy":
        w.facts["transformation"] = "stuck to relieved"
    elif params.problem == "missing_script":
        w.facts["transformation"] = "confused to sure"
    else:
        w.facts["transformation"] = "messy to neat"
    w.facts.update(hero=hero, script=script, prop=prop, problem=problem, remedy=remedy)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    r = world.facts["remedy"]
    h = world.facts["hero"]
    return [
        f"Write a short mystery for children about a script, a clue, and {p.label}.",
        f"Tell a funny story where {h.id} uses {r.label} to solve a stage problem and rejoice at the end.",
        f"Write a simple transformation story with a rehearsal script and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    p = world.facts["problem"]
    r = world.facts["remedy"]
    return [
        QAItem(question=f"What was {h.id} carrying when {h.id} came to the stage?", answer=f"{h.id} was carrying a rehearsal script."),
        QAItem(question=f"What mystery did the room have?", answer=f"The room had {p.label}. The clue was that {p.clue}."),
        QAItem(question=f"What did {h.id} do to fix things?", answer=f"{h.id} used {r.label} to solve the problem, and the story ended in rejoice and relief."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a script?", answer="A script is a written set of lines and stage directions for a play."),
        QAItem(question="What does rejoice mean?", answer="Rejoice means to feel and show great happiness."),
        QAItem(question="What is a mystery story?", answer="A mystery story gives clues and asks the reader to figure out what is happening."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={world.facts.get('transformation')}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="school_stage", problem="stuck_tummy", remedy="tea_walk", name="Mina", kind="girl"),
    StoryParams(setting="library_corner", problem="missing_script", remedy="page_find", name="Toby", kind="boy"),
    StoryParams(setting="backyard_box", problem="muddy_shoes", remedy="shoe_wipe", name="Luna", kind="girl"),
]


def asp_verify() -> int:
    import asp
    # Simple parity check: the ASP twin should at least recognize every Python-valid combo.
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_set - py_set))
    print("PY only:", sorted(py_set - asp_set))
    return 1


def build_asp_list() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_list())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
