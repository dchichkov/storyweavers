#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/afford_conflict_teamwork_mystery.py
==============================================================================================================

A small standalone storyworld in a mystery style: a child notices a puzzling
problem, meets conflict while searching for answers, and ends with teamwork that
makes the clue make sense.

The seed idea is a TinyStories-like tale:
- something small goes missing or looks wrong,
- the hero and a helper disagree about what it means,
- they work together, follow clues, and uncover the truth.

This world models:
- physical meters: where things are, what is missing, what is found, and how
  close clues are to being understood;
- emotional memes: worry, conflict, curiosity, trust, relief, and teamwork.

The world is intentionally small and constraint-checked. We only generate
stories when the setting, clue, and solution fit together in a plausible way.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    located_at: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)
    clue_places: set[str] = field(default_factory=set)
    mystery_kind: str = ""


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    points_to: str
    located_at: str


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    kind: str
    reveal: str
    needs_teamwork: bool = True


@dataclass
class StoryParams:
    setting: str
    mystery: str
    solution: str
    name: str
    friend_name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_worry(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    clue = world.facts["clue"]
    sol = world.facts["solution"]
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("worry", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if clue.kind == "sound":
        hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
        out.append(f"{hero.id} felt sure the strange sound meant trouble.")
    elif clue.kind == "missing":
        hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
        out.append(f"{hero.id} worried because something small had gone missing.")
    else:
        out.append(f"{hero.id} kept staring at the clue, trying to make it fit.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    if hero.memes.get("teamwork", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork", friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    out.append(f"{hero.id} and {friend.id} decided to look together instead of alone.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("teamwork", _r_teamwork)]


def propagate(world: World) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


def afford_reasonable(setting: Setting, mystery: Clue, solution: Solution) -> bool:
    return mystery.located_at in setting.clue_places and solution.kind in setting.afford


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = CLUES[params.mystery]
    solution = SOLUTIONS[params.solution]
    if not afford_reasonable(setting, mystery, solution):
        raise StoryError("The setting does not afford this mystery and solution together.")
    world = World(setting)
    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        traits=["curious", "careful"],
        meters={"search": 0.0},
        memes={"worry": 0.0, "conflict": 0.0, "teamwork": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name, kind="character", type="boy" if params.gender == "girl" else "girl",
        traits=["helpful", "brave"],
        meters={"search": 0.0},
        memes={"trust": 0.0, "teamwork": 0.0},
    ))
    clue = world.add(Entity(
        id="clue", kind="thing", type=mystery.kind, label=mystery.label,
        phrase=mystery.phrase, located_at=mystery.located_at,
    ))
    sol = world.add(Entity(
        id="solution", kind="thing", type=solution.kind, label=solution.label,
        phrase=solution.phrase, located_at=solution.reveal,
    ))
    world.facts.update(hero=hero, friend=friend, clue=clue, solution=sol, setting=setting)

    world.say(f"{hero.id} was a little {hero.type} who loved quiet places and small puzzles.")
    world.say(f"At {setting.place}, {hero.id} noticed {clue.phrase}. It did not seem right.")
    world.para()
    hero.memes["worry"] += 1
    hero.meters["search"] += 1
    world.say(f"{hero.id} started to look around, but the clue only made {hero.pronoun('object')} more worried.")
    world.say(f"{friend.id} thought it was nothing, and that caused a small conflict between them.")
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.para()
    hero.memes["teamwork"] += 1
    propagate(world)
    if mystery.kind == "sound":
        world.say(f"Then {hero.id} and {friend.id} followed the sound together.")
    else:
        world.say(f"Then {hero.id} and {friend.id} searched side by side until they found a useful clue.")
    world.say(f"They found {sol.phrase}, and the mystery finally made sense.")
    hero.memes["relief"] += 1
    world.say(f"{hero.id} smiled, because teamwork had turned confusion into an answer.")
    world.facts["resolved"] = True
    return world


def story_prompt(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    sol = f["solution"]
    return [
        f'Write a short mystery story for a child about {hero.id} at {world.setting.place}, '
        f"where a small clue like {clue.label} leads to an answer.",
        f"Tell a gentle story where {hero.id} and a friend disagree at first, then use teamwork to solve the mystery.",
        f'Write a simple story that includes the word "afford" in the sense that the place can afford a safe way to search.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    clue = f["clue"]
    sol = f["solution"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} notice the mystery first?",
            answer=f"{hero.id} noticed it at {setting.place}, where {clue.phrase} caught {hero.pronoun('possessive')} attention.",
        ),
        QAItem(
            question=f"Why was there a conflict between {hero.id} and {friend.id}?",
            answer=f"They disagreed because {hero.id} thought the clue meant trouble, while {friend.id} wanted to dismiss it at first.",
        ),
        QAItem(
            question=f"How did teamwork help solve the mystery?",
            answer=f"{hero.id} and {friend.id} searched together, and that teamwork helped them find {sol.phrase} and understand the clue.",
        ),
    ]


KNOWLEDGE = {
    "sound": [("What can a strange sound mean?", "A strange sound can be a clue that something nearby is moving, stuck, or hidden.")],
    "missing": [("What does it mean when something is missing?", "If something is missing, it is not where it should be, so someone may need to look for it.")],
    "teamwork": [("What is teamwork?", "Teamwork means people work together and help each other reach the same goal.")],
    "mystery": [("What is a mystery?", "A mystery is something puzzling that people try to understand by looking for clues.")],
    "map": [("Why do people use a map?", "People use a map to find where places are and to choose a good path.")],
}


def world_qa(world: World) -> list[QAItem]:
    tags = {world.setting.mystery_kind}
    tags.update({world.facts["clue"].kind, world.facts["solution"].kind})
    out = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    out.append(QAItem(question="What does afford mean here?", answer="Here, afford means the place can safely support the needed search or action."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


SETTINGS = {
    "library": Setting(place="the library", afford={"map", "note", "key"}, clue_places={"shelf", "desk", "page"}, mystery_kind="mystery"),
    "garden": Setting(place="the garden", afford={"map", "key", "tool"}, clue_places={"path", "bench", "gate"}, mystery_kind="missing"),
    "station": Setting(place="the station", afford={"map", "ticket", "lamp"}, clue_places={"bench", "platform", "clock"}, mystery_kind="sound"),
}

CLUES = {
    "note": Clue(id="note", label="a folded note", phrase="a folded note on the desk", kind="note", points_to="desk", located_at="desk"),
    "missing_key": Clue(id="missing_key", label="a missing key", phrase="an empty hook where a key should hang", kind="missing", points_to="hook", located_at="bench"),
    "odd_sound": Clue(id="odd_sound", label="an odd tapping sound", phrase="an odd tapping sound near the clock", kind="sound", points_to="clock", located_at="clock"),
}

SOLUTIONS = {
    "map": Solution(id="map", label="a map", phrase="a map tucked under a loose page", kind="map", reveal="page"),
    "key": Solution(id="key", label="a key", phrase="the missing key in a pocket", kind="key", reveal="pocket"),
    "lamp": Solution(id="lamp", label="a lamp", phrase="a lamp that had been switched on by mistake", kind="lamp", reveal="desk"),
}

CURATED = [
    StoryParams(setting="library", mystery="note", solution="map", name="Mina", friend_name="Noah", gender="girl"),
    StoryParams(setting="garden", mystery="missing_key", solution="key", name="Leo", friend_name="Mia", gender="boy"),
    StoryParams(setting="station", mystery="odd_sound", solution="lamp", name="Ava", friend_name="Ben", gender="girl"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in CLUES:
            for sol in SOLUTIONS:
                if afford_reasonable(SETTINGS[s], CLUES[m], SOLUTIONS[sol]):
                    out.append((s, m, sol))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with conflict and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
        raise StoryError("No valid mystery story matches those choices.")
    setting, mystery, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Leo", "Ava", "Noah", "Ivy", "Zoe", "Eli"])
    friend_name = args.friend_name or rng.choice(["Noah", "Mia", "Ben", "Lia", "Owen", "June"])
    if friend_name == name:
        friend_name = "Sam"
    return StoryParams(setting=setting, mystery=mystery, solution=solution, name=name, friend_name=friend_name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompt(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.located_at:
            bits.append(f"at={e.located_at}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_name(S).
mystery(M) :- mystery_name(M).
solution(S) :- solution_name(S).

affords(S, K) :- setting_afford(S, K).
clue_at(C, L) :- clue_place(C, L).
solution_kind(S, K) :- solution_type(S, K).

valid(S, M, Sol) :- setting(S), mystery(M), solution(Sol),
                    setting_afford(S, Kind), clue_kind(M, Kind),
                    solution_kind(Sol, K), setting_afford(S, K).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sname, setting in SETTINGS.items():
        lines.append(asp.fact("setting_name", sname))
        for a in sorted(setting.afford):
            lines.append(asp.fact("setting_afford", sname, a))
        for c in sorted(setting.clue_places):
            lines.append(asp.fact("clue_place", sname, c))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("mystery_name", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
        lines.append(asp.fact("clue_place", cid, clue.located_at))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution_name", sid))
        lines.append(asp.fact("solution_type", sid, sol.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between Python and ASP.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(sorted(asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
