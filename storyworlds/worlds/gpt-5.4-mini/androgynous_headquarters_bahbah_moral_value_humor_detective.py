#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/androgynous_headquarters_bahbah_moral_value_humor_detective.py
================================================================================================

A standalone story world for a tiny detective domain with moral value and humor.

Seed words:
- androgynous
- headquarters
- bahbah

Style:
- Detective story

The world centers on a small detective at headquarters, a harmless mystery, a
choice about honesty, and a funny sheepish clue that leads to a moral lesson.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    label: str
    room: str
    desk: str
    shelf: str
    window: str
    sound: str


@dataclass
class Mystery:
    id: str
    object_name: str
    place: str
    clue_sound: str
    hidden: str
    value: str
    risky: bool = False


@dataclass
class Solution:
    id: str
    method: str
    effect: str
    moral: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "headquarters": Setting(
        "headquarters",
        "the detectives' headquarters",
        room="front room",
        desk="a big wooden desk",
        shelf="a shelf of case folders",
        window="a square window",
        sound="tap-tap-tap",
    ),
    "library": Setting(
        "library",
        "the quiet library office",
        room="reading room",
        desk="a round desk",
        shelf="a shelf of maps",
        window="a tall window",
        sound="whisper-whisper",
    ),
}

MYSTERIES = {
    "missing_badge": Mystery(
        "missing_badge",
        "badge",
        "on the desk",
        "bahbah",
        "behind a filing tray",
        "honest badge",
    ),
    "vanished_cookie": Mystery(
        "vanished_cookie",
        "cookie tin",
        "near the shelf",
        "bahbah",
        "under a coat",
        "shared cookie",
    ),
}

SOLUTIONS = {
    "ask": Solution("ask", "asked kindly", "the truth came out", "honesty makes a case easier"),
    "search": Solution("search", "looked under the papers", "the clue was found", "looking carefully beats guessing"),
    "laugh": Solution("laugh", "laughed at the silly clue", "everyone smiled", "kind humor can calm a tense room"),
}

NAMES = ["Ari", "Rowan", "Sky", "Remy", "Parker", "Quinn", "Morgan", "Jamie", "Robin", "Taylor"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    solution: str
    detective: str
    sidekick: str
    detective_gender: str
    sidekick_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("headquarters", "missing_badge", "ask", "Rowan", "Jamie", "androgynous", "androgynous"),
    StoryParams("library", "vanished_cookie", "laugh", "Ari", "Taylor", "androgynous", "androgynous"),
    StoryParams("headquarters", "missing_badge", "search", "Sky", "Remy", "androgynous", "androgynous"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            for sol in SOLUTIONS:
                if sid == "headquarters" and m.id == "missing_badge":
                    combos.append((sid, mid, sol))
                if sid == "library" and m.id == "vanished_cookie":
                    combos.append((sid, mid, sol))
    return combos


def _shadow(value: str) -> str:
    return f"the {value}" if not value.startswith("the ") else value


def tell(setting: Setting, mystery: Mystery, solution: Solution,
         detective_name: str, sidekick_name: str,
         detective_gender: str = "androgynous",
         sidekick_gender: str = "androgynous") -> World:
    world = World(setting)
    det = world.add(Entity(id=detective_name, kind="character", type=detective_gender,
                           role="detective", traits=["curious", "fair"]))
    side = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender,
                            role="sidekick", traits=["funny", "kind"]))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label=mystery.object_name))
    world.facts.update(setting=setting, mystery=mystery, solution=solution,
                       detective=det, sidekick=side, clue=clue)

    det.memes["duty"] += 1
    side.memes["humor"] += 1
    world.say(
        f"At {setting.label}, {detector_name := det.id} sat at {setting.desk} beside "
        f"{setting.shelf}. The room was neat, the window was bright, and the case board "
        f"waited for a clue."
    )
    world.say(
        f"{detector_name} was an androgynous detective with a calm voice and sharp eyes. "
        f"{side.id} liked the jokes at headquarters, especially when the day felt long."
    )
    world.para()
    world.say(
        f"Then a problem arrived: the {mystery.object_name} was gone from {mystery.place}. "
        f"Only a tiny sound was left behind: \"{mystery.clue_sound}!\""
    )
    side.memes["humor"] += 1
    world.say(
        f'"{mystery.clue_sound}?" {side.id} said. "That sounds less like a clue and more like '
        f'a sheep practicing detective work."'
    )
    world.say(
        f"{detector_name} frowned, but {detector_name} did not rush. "
        f"{detector_name.capitalize()} checked the desk, the shelf, and the floor."
    )
    world.para()
    if solution.id == "ask":
        world.say(
            f"{detector_name} asked kindly who had moved {mystery.object_name}. "
            f"{side.id} listened, and soon the truth came out: the item had been set "
            f"{mystery.hidden} so it would stay safe."
        )
    elif solution.id == "search":
        world.say(
            f"{detector_name} looked under the papers and behind the folders. "
            f"At last, {detector_name} found the clue tucked {mystery.hidden}."
        )
    else:
        world.say(
            f"{side.id} laughed at the silly little \"{mystery.clue_sound}!\" and the whole room "
            f"laughed too. The laughter made everyone calm enough to think."
        )
        world.say(
            f"That calm helped {detector_name} notice the clue tucked {mystery.hidden}."
        )
    world.para()
    det.memes["satisfaction"] += 1
    side.memes["satisfaction"] += 1
    world.say(
        f"In the end, the {mystery.object_name} was back where it belonged, "
        f"and the case was closed with a smile."
    )
    world.say(
        f"{solution.effect.capitalize()}, and {solution.moral}. "
        f"At headquarters, even the funny \"bahbah\" clue had helped the detectives do the right thing."
    )
    world.facts["outcome"] = "solved"
    world.facts["moral"] = solution.moral
    return world


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: {setting} and {mystery} do not make a sensible tiny detective case.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"].id
    side = f["sidekick"].id
    mystery = f["mystery"]
    return [
        f'Write a detective story for a young child that includes the word "bahbah" and takes place at {f["setting"].label}.',
        f"Tell a gentle mystery where {det}, an androgynous detective, and {side} solve a missing-object case by being honest and kind.",
        f"Write a short humorous detective story about {mystery.object_name} disappearing from headquarters, with a moral ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    side = f["sidekick"]
    mystery = f["mystery"]
    sol = f["solution"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {det.id} and {side.id}, two detectives at {f['setting'].label}. {det.id} is androgynous, and the pair work together to solve a small mystery.",
        ),
        QAItem(
            question="What was the mystery?",
            answer=f"The {mystery.object_name} had gone missing from {mystery.place}. The strange clue was the little sound \"{mystery.clue_sound}!\"",
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"They solved it by {sol.method}. That worked because it led them to the truth instead of guessing, and the case became easy to finish.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned that {sol.moral}. The story shows that honesty and careful looking can solve a problem better than making things up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a headquarters?",
            answer="A headquarters is the main place where a team works, plans, and keeps important things together.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="Why can a funny clue help in a mystery?",
            answer="A funny clue can make people relax and pay attention. Sometimes a calm and happy room helps everyone think more clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting, mystery, solution) :- setting(setting), mystery(mystery), solution(solution).
solved :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid combos:")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: smoke-tested generate() successfully.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--detective")
    ap.add_argument("--sidekick")
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, solution = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != detective])
    return StoryParams(setting, mystery, solution, detective, sidekick, "androgynous", "androgynous")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], SOLUTIONS[params.solution],
                 params.detective, params.sidekick, params.detective_gender, params.sidekick_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for setting, mystery, solution in combos:
            print(f"  {setting:12} {mystery:16} {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.detective} at {p.setting} ({p.mystery}, {p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
