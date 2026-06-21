#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wrench_mystery_to_solve_myth.py
===============================================================

A standalone storyworld for a small mythic mystery: a child or young helper
follows clues through an old temple, finds a hidden mechanism that needs a wrench,
and solves the puzzle with a careful turn instead of brute force.

The prose aims for a myth-like, child-facing style: moonlight, old stone, a quiet
guardian, a riddle, and a reveal that changes the world state at the end.

Run:
    python storyworlds/worlds/gpt-5.4-mini/wrench_mystery_to_solve_myth.py
    python storyworlds/worlds/gpt-5.4-mini/wrench_mystery_to_solve_myth.py --qa
    python storyworlds/worlds/gpt-5.4-mini/wrench_mystery_to_solve_myth.py --verify
"""

from __future__ import annotations

import argparse
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
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
    id: str
    place: str
    mood: str
    dark_space: str
    threshold: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    line: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    reveal: str
    mechanism: str
    locked_state: str
    solved_state: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    line: str
    fit: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    setting: str
    seeker: str
    seeker_gender: str
    guide: str
    guide_gender: str
    mystery: str
    clue1: str
    clue2: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "temple": Setting(
        id="temple",
        place="an old hill temple",
        mood="the stone halls were cool and hushed",
        dark_space="the moonless inner chamber",
        threshold="a sealed bronze door",
        tags={"temple", "stone"},
    ),
    "ruins": Setting(
        id="ruins",
        place="the sleeping ruins by the river",
        mood="the broken arches glimmered with dew",
        dark_space="the shadow under the fallen arch",
        threshold="a hidden gate of roots and stone",
        tags={"ruins", "stone"},
    ),
    "cave": Setting(
        id="cave",
        place="a cave beneath the stars",
        mood="the cave breathed cold air like a sleeping beast",
        dark_space="the far chamber behind the echoing wall",
        threshold="a round iron hatch",
        tags={"cave", "stone"},
    ),
}

MYSTERIES = {
    "moon_door": Mystery(
        id="moon_door",
        reveal="a moon-marked door slid open",
        mechanism="a hidden bolt",
        locked_state="sealed tight",
        solved_state="open at last",
        tags={"moon", "door", "mechanism"},
    ),
    "stone_lion": Mystery(
        id="stone_lion",
        reveal="the stone lion's eyes lit with gold",
        mechanism="a rusted hinge",
        locked_state="frozen shut",
        solved_state="moving again",
        tags={"lion", "mechanism"},
    ),
    "river_gate": Mystery(
        id="river_gate",
        reveal="a secret path to the river shrine appeared",
        mechanism="a buried latch",
        locked_state="hidden and stuck",
        solved_state="found and freed",
        tags={"gate", "mechanism"},
    ),
}

CLUES = {
    "riddle": Clue(
        id="riddle",
        line="a line in the dust said, 'Turn what is bent, and the quiet will answer.'",
        hint="The answer was not magic words, but a tool that could turn stubborn metal.",
        tags={"riddle"},
    ),
    "rune": Clue(
        id="rune",
        line="a carved rune showed a twisted shape beside a silver circle.",
        hint="The mark looked like the shape of a wrench head.",
        tags={"rune"},
    ),
    "footprints": Clue(
        id="footprints",
        line="small footprints led from the threshold to the wall and back again.",
        hint="Someone had already tried the wall and found something that moved.",
        tags={"track"},
    ),
    "bell": Clue(
        id="bell",
        line="a bronze bell lay silent beside the sealed place.",
        hint="Metal things nearby meant the mystery could be solved by fit and turn.",
        tags={"metal"},
    ),
}

TOOLS = {
    "wrench": Tool(
        id="wrench",
        label="wrench",
        line="a small brass wrench hidden in a cloth pouch",
        fit="It matched the hidden bolt perfectly.",
        tags={"wrench", "tool"},
    ),
    "key": Tool(
        id="key",
        label="key",
        line="an old key with a lion-shaped head",
        fit="It fit no lock here at all.",
        tags={"key", "tool"},
    ),
}

GIRL_NAMES = ["Mira", "Luna", "Sera", "Nia", "Aria", "Tala"]
BOY_NAMES = ["Orin", "Bram", "Eli", "Kian", "Ravi", "Jory"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for c1 in CLUES:
                for c2 in CLUES:
                    if c1 != c2:
                        combos.append((s, m, c1, c2))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic mystery storyworld with a wrench.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue1 is None or c[2] == args.clue1)
              and (args.clue2 is None or c[3] == args.clue2)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, mystery, clue1, clue2 = rng.choice(sorted(combos))
    tool = args.tool or "wrench"
    if tool != "wrench":
        raise StoryError("This world only solves the mystery with a wrench.")
    gender = args.gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice([n for n in (GIRL_NAMES if guide_gender == "girl" else BOY_NAMES) if n != name])
    return StoryParams(
        setting=setting,
        seeker=name,
        seeker_gender=gender,
        guide=guide,
        guide_gender=guide_gender,
        mystery=mystery,
        clue1=clue1,
        clue2=clue2,
        tool=tool,
    )


def build_world(params: StoryParams) -> World:
    world = World()
    seeker = world.add(Entity(id=params.seeker, kind="character", type=params.seeker_gender, role="seeker"))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    clue1 = CLUES[params.clue1]
    clue2 = CLUES[params.clue2]
    tool = TOOLS[params.tool]
    world.facts.update(seeker=seeker, guide=guide, setting=setting, mystery=mystery, clue1=clue1, clue2=clue2, tool=tool)
    seeker.memes["wonder"] += 1
    guide.memes["calm"] += 1
    world.say(f"Long ago, {seeker.id} and {guide.id} entered {setting.place}. {setting.mood}.")
    world.say(f"At its heart stood {setting.threshold}, and the mystery was {mystery.locked_state}.")
    world.para()
    world.say(f"{clue1.line} {clue2.line}")
    world.say(f"{clue1.hint} {clue2.hint}")
    world.para()
    seeker.memes["curiosity"] += 1
    world.say(f'{seeker.id} whispered, "Something here is waiting to be understood."')
    world.say(f"{guide.id} knelt beside the stone and pointed to the hidden sign.")
    if params.tool == "wrench":
        seeker.meters["holds_tool"] += 1
        world.say(f"In a cloth pouch lay a wrench, small but sure, like a star made for turning.")
        world.say(f"{guide.id} said the answer was not force, but fit.")
        world.para()
        seeker.meters["turning"] += 1
        world.say(f"{seeker.id} set the wrench to the secret bolt and turned it slowly.")
        world.say(f"{tool.fit} With a deep click, the stone loosened.")
        mystery_state_before = mystery.locked_state
        mystery_state_after = mystery.solved_state
        world.facts["solved"] = True
        world.facts["before"] = mystery_state_before
        world.facts["after"] = mystery_state_after
        world.para()
        world.say(f"Then {mystery.reveal}. The old place was no longer {mystery_state_before}; it was {mystery_state_after}.")
        seeker.memes["joy"] += 1
        guide.memes["joy"] += 1
        world.say(f"{seeker.id} smiled at {guide.id}, and the temple answered with light.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like mystery story for a young child set in {f["setting"].place} that includes the word "wrench".',
        f"Tell a calm, ancient-feeling story where {f['seeker'].id if isinstance(f['seeker'], Entity) else f['seeker']} solves a hidden temple mystery with a wrench.",
        f"Write a short myth about clues in stone, a quiet guide, and a wrench that opens a secret.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    guide = f["guide"]
    mystery = f["mystery"]
    tool = f["tool"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a myth-like mystery story about old stone, careful clues, and a hidden secret that can be solved with a tool.",
        ),
        QAItem(
            question=f"What did {seeker.id} and {guide.id} do?",
            answer=f"They followed the clues in the old place and solved the mystery together. {guide.id} helped by noticing the sign, and {seeker.id} used the wrench to make the hidden part turn.",
        ),
        QAItem(
            question=f"What happened when {seeker.id} used the wrench?",
            answer=f"The wrench matched the hidden bolt, so the stone loosened and the secret opened. That turned the mystery from locked and quiet into something revealed and bright.",
        ),
        QAItem(
            question="How did the ending change the place?",
            answer=f"The place went from being sealed and still to being open at last. The secret came alive, and the old stones seemed to wake up with light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wrench?",
            answer="A wrench is a hand tool used to grip and turn nuts, bolts, and other metal pieces. It helps when something is stuck and needs a careful twist.",
        ),
        QAItem(
            question="Why would a wrench help in a mystery?",
            answer="A mystery can hide a stuck latch or bolt, and a wrench can turn it without breaking it. That makes it a good tool for opening secret things the gentle way.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign that helps you figure something out. Clues can be marks, lines, sounds, or little things left behind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,C1,C2) :- setting(S), mystery(M), clue(C1), clue(C2), C1 != C2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # Smoke test normal generation first.
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, mystery=None, clue1=None, clue2=None, tool=None,
            name=None, guide=None, gender=None, guide_gender=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between Python and ASP valid combo sets.")
        print("python-only:", sorted(py - asp_set))
        print("asp-only:", sorted(asp_set - py))
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos).")
    print("OK: smoke test generation succeeded.")
    return 0


CURATED = [
    StoryParams(setting="temple", seeker="Mira", seeker_gender="girl", guide="Orin", guide_gender="boy",
                mystery="moon_door", clue1="riddle", clue2="rune", tool="wrench"),
    StoryParams(setting="ruins", seeker="Luna", seeker_gender="girl", guide="Bram", guide_gender="boy",
                mystery="stone_lion", clue1="footprints", clue2="bell", tool="wrench"),
    StoryParams(setting="cave", seeker="Eli", seeker_gender="boy", guide="Tala", guide_gender="girl",
                mystery="river_gate", clue1="rune", clue2="riddle", tool="wrench"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.clue1 not in CLUES or params.clue2 not in CLUES:
        raise StoryError("Unknown clue.")
    if params.clue1 == params.clue2:
        raise StoryError("A mystery story needs two different clues.")
    if params.tool != "wrench":
        raise StoryError("This mythic mystery is solved with a wrench.")
    world = build_world(params)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos[:20]:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
