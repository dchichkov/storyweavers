#!/usr/bin/env python3
"""
storyworlds/worlds/cougar_yack_cautionary_dialogue_mystery.py
==============================================================

A small, self-contained storyworld about a cougar, a yack, and a cautionary
mystery told through dialogue.

Premise:
- A curious cougar and a talkative yack discover a small problem in a quiet
  night setting.
- The cougar is cautious; the yack keeps talking.
- Their dialogue uncovers clues, a risk is avoided, and the missing thing is
  found.

World model:
- Physical meters track distance, heat, light, wetness, and hiddenness.
- Emotional memes track caution, worry, curiosity, relief, and trust.

The story is designed to feel like a compact mystery with a warning beat,
conversation, clue-finding, and a safe resolution.
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


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    id: str
    name: str
    light: str
    mood: str
    clues: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    id: str
    missing: str
    threat: str
    clue: str
    fix: str
    caution: str


@dataclass(frozen=True)
class CharacterSpec:
    id: str
    kind: str
    label: str
    voice: str
    trait: str


SETTINGS: dict[str, Setting] = {
    "canyon_path": Setting(
        id="canyon_path",
        name="the canyon path",
        light="moonlight",
        mood="quiet",
        clues=("scratches on stone", "a bent tuft of grass", "tiny pawprints"),
    ),
    "pine_camp": Setting(
        id="pine_camp",
        name="the pine camp",
        light="campfire glow",
        mood="still",
        clues=("ash on a log", "a snapped string", "a little trail of dust"),
    ),
    "river_bend": Setting(
        id="river_bend",
        name="the river bend",
        light="silver water",
        mood="cool",
        clues=("wet footprints", "a ripple by reeds", "a shiny pebble"),
    ),
}

PROBLEMS: dict[str, Problem] = {
    "lantern": Problem(
        id="lantern",
        missing="the lantern",
        threat="the dark path could hide a fall",
        clue="a warm circle of light left on the dirt",
        fix="find the lantern and light the way",
        caution="Do not rush into the dark before looking for clues.",
    ),
    "bell": Problem(
        id="bell",
        missing="the camp bell",
        threat="nobody would hear a warning call",
        clue="a tiny ring mark on a branch",
        fix="follow the ring mark to the branch basket",
        caution="A warning is safest when someone listens first.",
    ),
    "map": Problem(
        id="map",
        missing="the folded map",
        threat="they might wander in the wrong direction",
        clue="a paper corner caught under a rock",
        fix="pull the map free and check the marks",
        caution="When a guide is missing, slow down and look carefully.",
    ),
}

COUGAR = CharacterSpec(
    id="cougar",
    kind="character",
    label="cougar",
    voice="low",
    trait="cautious",
)

YACK = CharacterSpec(
    id="yack",
    kind="character",
    label="yack",
    voice="lively",
    trait="talkative",
)

COMPANIONS = [COUGAR, YACK]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    holding: Optional[str] = None

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class World:
    setting: Setting
    problem: Problem
    characters: dict[str, Entity] = field(default_factory=dict)
    objects: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, spec: CharacterSpec) -> Entity:
        ent = Entity(id=spec.id, kind=spec.kind, label=spec.label)
        self.characters[spec.id] = ent
        return ent

    def add_object(self, oid: str, label: str) -> Entity:
        ent = Entity(id=oid, kind="thing", label=label)
        self.objects[oid] = ent
        return ent


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a setting has a clue, a problem is missing, and the
% cougar and yack can both participate in the cautionary dialogue mystery.
valid_story(S, P) :- setting(S), problem(P), clue(S, P), caution(P).

% The mystery turns on a warning, a clue, and a safe resolution.
safe_resolution(P) :- problem(P), has_fix(P).

% Dialogue is central.
dialogue_story(S, P) :- valid_story(S, P), dialogue(S), mystery(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_name", sid, s.name))
        lines.append(asp.fact("light", sid, s.light))
        lines.append(asp.fact("mood", sid, s.mood))
        for clue in s.clues:
            lines.append(asp.fact("clue", sid, clue))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("missing", pid, p.missing))
        lines.append(asp.fact("threat", pid, p.threat))
        lines.append(asp.fact("clue_text", pid, p.clue))
        lines.append(asp.fact("has_fix", pid))
        lines.append(asp.fact("caution", pid))
    lines.append(asp.fact("dialogue", "world"))
    lines.append(asp.fact("mystery", "world"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2.\n#show safe_resolution/1.\n"))
    shown_valid = set(asp.atoms(model, "valid_story"))
    shown_safe = set(asp.atoms(model, "safe_resolution"))
    python_valid = set((s, p) for s in SETTINGS for p in PROBLEMS)
    python_safe = set(PROBLEMS.keys())
    if shown_valid == python_valid and shown_safe == python_safe:
        print(f"OK: clingo gate matches Python registry shape ({len(shown_valid)} stories).")
        return 0
    print("MISMATCH between clingo and Python.")
    if shown_valid != python_valid:
        print("  valid_story differs.")
    if shown_safe != python_safe:
        print("  safe_resolution differs.")
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    problem: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary dialogue mystery with a cougar and a yack.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    return StoryParams(setting=setting, problem=problem)


def _init_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    world = World(setting=setting, problem=problem)
    cougar = world.add_character(COUGAR)
    yack = world.add_character(YACK)
    world.add_object(problem.id, problem.missing)
    cougar.location = setting.name
    yack.location = setting.name
    cougar.meters.update({"distance": 0.0, "light": 0.0, "hiddenness": 0.0})
    yack.meters.update({"distance": 0.0, "light": 0.0, "hiddenness": 0.0})
    cougar.memes.update({"caution": 2.0, "worry": 0.5, "trust": 1.0})
    yack.memes.update({"curiosity": 2.0, "worry": 0.2, "trust": 1.0})
    return world


def generate(params: StoryParams) -> StorySample:
    world = _init_world(params)
    setting = world.setting
    problem = world.problem
    cougar = world.characters["cougar"]
    yack = world.characters["yack"]
    obj = world.objects[problem.id]

    world.say(f"At {setting.name}, {setting.light} softened the shadows, and the air felt {setting.mood}.")
    world.say(f"The {cougar.label} was {COUGAR.trait}, while the {yack.label} was {YACK.trait} and kept yacking about every little sound.")

    world.para()
    world.say(f"Then they noticed {problem.missing} was gone.")
    world.say(f"The loss mattered because {problem.threat}.")
    world.say(f'The {cougar.label} said, "{problem.caution}"')
    world.say(f'The {yack.label} said, "Let me yack about the clues before we move a paw."')

    world.para()
    cougar.memes["caution"] += 1.0
    yack.memes["curiosity"] += 1.0
    yack.meters["distance"] += 1.0
    world.say(f"The {yack.label} spotted {problem.clue}, and the {cougar.label} froze to think.")
    world.say(f'The {cougar.label} answered, "Good eye. We will follow that clue, not the dark road."')
    world.say(f"That careful choice kept them from a risky stumble.")

    world.para()
    obj.meters["hiddenness"] = 0.0
    cougar.meters["distance"] += 1.0
    yack.meters["distance"] += 1.0
    cougar.memes["worry"] -= 0.5
    yack.memes["worry"] -= 0.2
    cougar.memes["trust"] += 0.5
    yack.memes["trust"] += 0.5
    world.say(f"Under a rock, they found {problem.missing}.")
    world.say(f'The {yack.label} yacked, "There it is!"')
    world.say(f'The {cougar.label} smiled and said, "See? Slow eyes found what fast feet could miss."')
    world.say(f"With {problem.missing} safe again, the path looked less scary and the night felt kinder.")

    world.facts.update(
        setting=params.setting,
        problem=params.problem,
        missing=problem.missing,
        clue=problem.clue,
        caution=problem.caution,
        threat=problem.threat,
    )

    story = world.render()
    prompts = [
        f'Write a short mystery story for young children featuring a cougar, a yack, and the word "cautionary".',
        f"Tell a dialogue-driven story where a {COUGAR.label} and a {YACK.label} solve a small problem by listening carefully.",
        f'Write a gentle story with a clue, a warning, and a safe ending in {setting.name}.',
    ]
    story_qa = [
        QAItem(
            question="Who was cautious in the story?",
            answer="The cougar was cautious. It slowed the pair down so they would not rush into danger.",
        ),
        QAItem(
            question="What did the yack keep doing?",
            answer="The yack kept yacking and talking about the clues, which helped them notice small details.",
        ),
        QAItem(
            question=f"What was missing at {setting.name}?",
            answer=f"{problem.missing} was missing, and that created the mystery they had to solve.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They listened to the clue, followed it carefully, and found {problem.missing} under a rock.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a cougar?", answer="A cougar is a wild cat that is quiet, strong, and careful when it moves."),
        QAItem(question="What is a yack?", answer="A yack is a talkative creature in this storyworld, and it keeps talking while it thinks."),
        QAItem(question="What does caution mean?", answer="Caution means being careful and avoiding danger before acting."),
        QAItem(question="What is a mystery?", answer="A mystery is a problem where something is missing or unclear, so characters must look for clues."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.characters.values()) + list(world.objects.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.holding:
            bits.append(f"holding={e.holding}")
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show safe_resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2.\n#show safe_resolution/1."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        safe = sorted(set(asp.atoms(model, "safe_resolution")))
        print(f"{len(stories)} compatible stories; {len(safe)} safe resolutions.")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in sorted(SETTINGS):
            for pid in sorted(PROBLEMS):
                samples.append(generate(StoryParams(setting=sid, problem=pid, seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.setting} / {p.problem}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
