#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/press_surprise_whodunit.py
=========================================================

A tiny whodunit storyworld about a newspaper press, a surprise, and a careful
search for clues.

The domain:
- Children help a small newspaper office before a big print run.
- Something odd happens: the press won't start, then a surprise clue appears.
- A calm search reveals who caused the snag, and the team fixes it in a sensible
  way.
- The ending proves what changed by showing the paper coming off the press.

This file is standalone, stdlib-only, and follows the Storyweavers contract.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    scene: str
    workplace: str

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
class Press:
    id: str
    label: str
    phrase: str
    sound: str
    requires_ink: bool = True
    loud: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    found_where: str
    surprising: bool = True
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
class Problem:
    id: str
    label: str
    cause: str
    fix_text: str
    fail_text: str
    power: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clue_known: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.clue_known = self.clue_known
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    press: str
    clue: str
    problem: str
    investigator: str
    investigator_gender: str
    helper: str
    helper_gender: str
    suspect: str
    suspect_gender: str
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
    "office": Setting("office", "the newspaper office", "a room full of desks and papers", "the old press"),
    "school": Setting("school", "the school newspaper room", "a bright room with a bulletin board", "the little press"),
    "library": Setting("library", "the library's news corner", "a quiet room behind the shelves", "the community press"),
}

PRESSES = {
    "old_press": Press("old_press", "press", "the press", "WHUMP!", tags={"press", "ink", "news"}),
    "little_press": Press("little_press", "press", "the press", "THUMP!", tags={"press", "ink", "news"}),
    "community_press": Press("community_press", "press", "the press", "BUMP!", tags={"press", "ink", "news"}),
}

CLUES = {
    "ink_smudge": Clue("ink_smudge", "ink smudge", "a dark ink smudge", "under the desk", tags={"ink", "clue"}),
    "footprint": Clue("footprint", "muddy footprint", "a muddy footprint", "by the paper bin", tags={"clue", "mud"}),
    "paper_note": Clue("paper_note", "note", "a folded note", "inside a paper tray", tags={"clue", "note"}),
}

PROBLEMS = {
    "stuck_roller": Problem("stuck_roller", "stuck roller", "a tiny paper scrap jammed the roller", "pulled the scrap free and cleaned the roller", "could not free the jam in time", 2, tags={"press"}),
    "missing_ink": Problem("missing_ink", "missing ink", "the ink tray was empty", "fetched fresh ink and filled the tray", "could not find ink quickly enough", 1, tags={"ink"}),
    "switched_switch": Problem("switched_switch", "switched switch", "someone had turned the power switch the wrong way", "flipped the switch back on", "had to wait for the repair cart", 2, tags={"press"}),
}

GIRL_NAMES = ["Maya", "Lina", "Tess", "Nora", "Ivy", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Eli", "Noah", "Ben", "Leo", "Max", "Owen", "Finn", "Theo"]


def reasonableness_ok(press: Press, clue: Clue, problem: Problem) -> bool:
    return "press" in press.tags and "clue" in clue.tags and "press" in problem.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for pid in PRESSES:
            for cid in CLUES:
                for probid in PROBLEMS:
                    if reasonableness_ok(PRESSES[pid], CLUES[cid], PROBLEMS[probid]):
                        combos.append((sid, pid, cid, probid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a press, a surprise clue, and a whodunit.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--press", choices=PRESSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--investigator")
    ap.add_argument("--investigator-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.press and args.clue and args.problem:
        if not reasonableness_ok(PRESSES[args.press], CLUES[args.clue], PROBLEMS[args.problem]):
            raise StoryError("That combination does not make a sensible press mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.press is None or c[1] == args.press)
              and (args.clue is None or c[2] == args.clue)
              and (args.problem is None or c[3] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, press, clue, problem = rng.choice(sorted(combos))
    ig = args.investigator_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    sg = args.suspect_gender or rng.choice(["girl", "boy"])
    inv = args.investigator or _pick_name(rng, ig)
    helper = args.helper or _pick_name(rng, hg)
    suspect = args.suspect or _pick_name(rng, sg)
    return StoryParams(setting, press, clue, problem, inv, ig, helper, hg, suspect, sg)


def _smoke_test_params() -> StoryParams:
    return StoryParams("office", "old_press", "ink_smudge", "stuck_roller", "Maya", "girl", "Eli", "boy", "Theo", "boy")


def apply_problem(world: World, press: Entity, problem: Problem) -> None:
    press.meters["stopped"] += 1
    press.memes["worry"] += 1
    if problem.id == "missing_ink":
        press.meters["inkless"] += 1
    elif problem.id == "switched_switch":
        press.meters["silent"] += 1
    else:
        press.meters["jammed"] += 1


def solve_problem(world: World, press: Entity, problem: Problem) -> None:
    press.meters["stopped"] = 0
    press.meters["working"] += 1
    press.memes["relief"] += 1


def tell(setting: Setting, press_cfg: Press, clue_cfg: Clue, problem: Problem,
         investigator: str, investigator_gender: str,
         helper: str, helper_gender: str,
         suspect: str, suspect_gender: str) -> World:
    world = World(setting)
    a = world.add(Entity(investigator, "character", investigator_gender, role="investigator", traits=["curious"]))
    b = world.add(Entity(helper, "character", helper_gender, role="helper", traits=["careful"]))
    c = world.add(Entity(suspect, "character", suspect_gender, role="suspect", traits=["quiet"]))
    press = world.add(Entity(press_cfg.id, "thing", "press", label=press_cfg.label, attrs={"sound": press_cfg.sound}))
    clue = world.add(Entity(clue_cfg.id, "thing", clue_cfg.label, label=clue_cfg.label_word if hasattr(clue_cfg, "label_word") else clue_cfg.label))
    world.add(Entity(problem.id, "thing", problem.label, label=problem.label))

    a.memes["curiosity"] += 1
    b.memes["helpfulness"] += 1
    c.memes["nervousness"] += 1

    world.say(
        f"At {setting.place}, {a.id} and {b.id} came to help before the morning paper was printed. "
        f"{setting.scene} made the room feel like the start of a mystery."
    )
    world.say(
        f"The {press_cfg.label} stood in the middle of the room, ready to make the pages. "
        f"{a.id} liked how the press could turn blank sheets into news."
    )

    world.para()
    apply_problem(world, press, problem)
    world.say(
        f"Then the trouble began: {problem.cause}. The {press_cfg.label} stopped with a stubborn little silence."
    )
    world.say(
        f'{b.id} frowned. "We need to find out what happened before the papers are late."'
    )

    world.para()
    world.clue_known = True
    world.facts["surprise"] = clue_cfg.id
    world.say(
        f"While they searched, {a.id} found a surprise: {clue_cfg.phrase} {clue_cfg.found_where}. "
        f"That clue changed the whole guess."
    )
    if clue_cfg.id == "ink_smudge":
        world.say(f"The smudge showed that someone had been close to the ink tray.")
    elif clue_cfg.id == "footprint":
        world.say(f"The footprint showed that someone had walked straight to the paper bin.")
    else:
        world.say(f"The note gave a tidy hint, written like someone who wanted to be found.")

    world.para()
    world.say(
        f"{a.id} and {b.id} looked at {c.id} and asked kind questions. Soon the answer was clear: "
        f"{c.id} had meant to help, but {problem.cause.lower()}."
    )
    world.say(
        f"{c.id} looked sorry and nodded. {a.id} was surprised, but not angry."
    )

    world.para()
    solve_problem(world, press, problem)
    world.say(
        f"Together they used the clue and the fix: {problem.fix_text}. "
        f"The {press_cfg.label} began to move again, {press_cfg.sound}."
    )
    world.say(
        f"At last, the first page came out clean and bright, and the headline was ready for the town to read."
    )

    world.facts.update(
        setting=setting, press_cfg=press_cfg, clue_cfg=clue_cfg, problem=problem,
        investigator=a, helper=b, suspect=c, press=press, clue=clue
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit about a press where a surprise clue is found and the team solves the problem. Include the word "press".',
        f"Tell a mystery story where {f['investigator'].id} notices a surprise clue near the press and figures out what went wrong.",
        f"Write a short suspense story with a hidden clue, a press, and a calm reveal at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inv, helper, suspect = f["investigator"], f["helper"], f["suspect"]
    press_cfg, clue_cfg, problem = f["press_cfg"], f["clue_cfg"], f["problem"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small whodunit about a press, a surprising clue, and a careful search that finds the answer."
        ),
        QAItem(
            question=f"What surprise did {inv.id} find?",
            answer=f"{inv.id} found {clue_cfg.phrase} {clue_cfg.found_where}. That surprise clue helped point the mystery in the right direction."
        ),
        QAItem(
            question=f"Why did the press stop working?",
            answer=f"It stopped because {problem.cause}. The room needed someone to notice the clue and fix the problem before the papers could print."
        ),
        QAItem(
            question=f"What did {inv.id}, {helper.id}, and {suspect.id} do at the end?",
            answer=f"They talked it through, solved the problem together, and got the {press_cfg.label} moving again. After that, the first page came out clean and ready."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does a press do?",
            answer="A press squeezes or prints things into shape. In a newspaper room, a press turns blank paper into printed pages."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery. It can be a mark, a note, or something odd that points to the answer."
        ),
        QAItem(
            question="What should you do in a mystery before guessing?",
            answer="You should look carefully, ask kind questions, and check the facts. Good detectives do not rush; they follow the clues first."
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, C, R) :- setting(S), press(P), clue(C), problem(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRESSES:
        lines.append(asp.fact("press", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid in PROBLEMS:
        lines.append(asp.fact("problem", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
        rc = 1
    try:
        sample = generate(_smoke_test_params())
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = format_qa(sample)
    except Exception as exc:
        print(f"MISMATCH: story generation smoke test failed: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and story generation smoke test passed.")
    return rc


def tell_from_params(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PRESSES[params.press],
        CLUES[params.clue],
        PROBLEMS[params.problem],
        params.investigator,
        params.investigator_gender,
        params.helper,
        params.helper_gender,
        params.suspect,
        params.suspect_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_from_params(params)


CURATED = [
    _smoke_test_params(),
    StoryParams("school", "little_press", "paper_note", "switched_switch", "Nora", "girl", "Ben", "boy", "Ivy", "girl"),
    StoryParams("library", "community_press", "footprint", "missing_ink", "Theo", "boy", "Ella", "girl", "Max", "boy"),
]


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
              and (args.press is None or c[1] == args.press)
              and (args.clue is None or c[2] == args.clue)
              and (args.problem is None or c[3] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, press, clue, problem = rng.choice(sorted(combos))
    ig = args.investigator_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    sg = args.suspect_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting, press, clue, problem,
        args.investigator or _pick_name(rng, ig), ig,
        args.helper or _pick_name(rng, hg), hg,
        args.suspect or _pick_name(rng, sg), sg,
    )


def _sample_with_seed(seed: int) -> StorySample:
    params = resolve_params(build_parser().parse_args([]), random.Random(seed))
    params.seed = seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, press, clue, problem) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.investigator}: {p.press} mystery at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
