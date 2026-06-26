#!/usr/bin/env python3
"""
storyworlds/worlds/grip_mystery_to_solve_lesson_learned_foreshadowing.py
=========================================================================

A small superhero-flavored story world about a mystery to solve, a lesson
learned, and a bit of foreshadowing.

Premise:
- A young hero notices something odd in the city.
- Early clues foreshadow who is involved.
- The hero chases the wrong idea first, then learns to look closely.
- The mystery is solved by tracing a physical clue and choosing a kinder,
  smarter response.

The world keeps a light simulation of:
- physical meters: clues, damage, distance, grip
- emotional memes: worry, confidence, teamwork, relief, blame

The final story should read like a complete tiny superhero story, not a log of
events.
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
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    detail: str
    afford: str


@dataclass(frozen=True)
class Mystery:
    id: str
    thing: str
    trouble: str
    clue_word: str
    clue_place: str
    culprit: str
    solution: str
    lesson: str
    foreshadow: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Power:
    id: str
    name: str
    use: str


SETTINGS: dict[str, Setting] = {
    "rooftop": Setting(
        id="rooftop",
        place="the rooftop",
        detail="The city lights blinked far below, and the wind tugged at capes and sleeves.",
        afford="climb",
    ),
    "museum": Setting(
        id="museum",
        place="the museum hall",
        detail="Glass cases gleamed under bright lamps, and every step sounded extra important.",
        afford="inspect",
    ),
    "subway": Setting(
        id="subway",
        place="the subway station",
        detail="The tunnels hummed, and the tiles echoed every footstep like a secret whisper.",
        afford="search",
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "signal_lamp": Mystery(
        id="signal_lamp",
        thing="signal lamp",
        trouble="its beam kept flickering and making the rescue map look wrong",
        clue_word="smudge",
        clue_place="the lamp glass",
        culprit="a sticky handprint from the snack stand",
        solution="wipe the glass clean and replace the cracked bulb cover",
        lesson="look closely before guessing",
        foreshadow="Earlier, a shiny wrapper had stuck to a railing in the same spot.",
        tags={"light", "clue", "clean"},
    ),
    "missing_medal": Mystery(
        id="missing_medal",
        thing="gold medal",
        trouble="it had vanished from its display case",
        clue_word="scratch",
        clue_place="the floor near the case",
        culprit="a tiny rolling magnet toy that pulled the medal along",
        solution="follow the scratch marks to the toy and return the medal",
        lesson="small clues can point to the real answer",
        foreshadow="A little metal click had echoed under the bench before anyone looked up.",
        tags={"metal", "clue", "truth"},
    ),
    "stuck_gate": Mystery(
        id="stuck_gate",
        thing="garden gate",
        trouble="it would not close all the way, so the courtyard felt unsafe",
        clue_word="mudprint",
        clue_place="the bottom rail",
        culprit="a clump of mud on the hinge and a loose pebble in the track",
        solution="clear the hinge and roll the pebble out with a careful push",
        lesson="patience can fix what rushing breaks",
        foreshadow="A muddy bootprint had appeared by the gate before the wind picked up.",
        tags={"gate", "repair", "clue"},
    ),
}

POWERS: dict[str, Power] = {
    "grip": Power(
        id="grip",
        name="grip gloves",
        use="hold on tight and climb where others could not",
    ),
    "scan": Power(
        id="scan",
        name="scan visor",
        use="spot tiny details hidden in plain sight",
    ),
    "pull": Power(
        id="pull",
        name="pull rope",
        use="reach things that were just out of grasp",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Sky", "Juno", "Iris", "Pip", "Zara", "Finn"]
HELPER_NAMES = ["Bolt", "Comet", "Echo", "Gale", "Penny"]
VILLAIN_NAMES = ["Moth Mask", "Drift", "The Whisper", "Captain Nudge"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: Setting
    mystery: Mystery
    power: Power
    hero: Entity
    helper: Entity
    villain: Entity
    clue_seen: bool = False
    wrong_guess: bool = False
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mystery: str
    power: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen power can help with the chosen mystery in
% the chosen setting. We keep the rules simple and deterministic.
valid_story(S, M, P) :- setting(S), mystery(M), power(P), compatible(S, M, P).

% Grip gloves are especially good for rooftop and gate stories.
compatible(rooftop, signal_lamp, grip).
compatible(subway, missing_medal, scan).
compatible(museum, missing_medal, scan).
compatible(rooftop, stuck_gate, grip).
compatible(museum, stuck_gate, pull).
compatible(subway, signal_lamp, grip).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.id))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
    for p in POWERS.values():
        lines.append(asp.fact("power", p.id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_triples())
    if py == asp_set:
        print(f"OK: ASP matches Python validity gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Validation / selection
# ---------------------------------------------------------------------------

def compatible(setting: Setting, mystery: Mystery, power: Power) -> bool:
    if mystery.id == "signal_lamp":
        return power.id in {"grip", "scan"} and setting.id in {"rooftop", "subway"}
    if mystery.id == "missing_medal":
        return power.id in {"scan", "pull"} and setting.id in {"museum", "subway"}
    if mystery.id == "stuck_gate":
        return power.id in {"grip", "pull"} and setting.id in {"rooftop", "museum"}
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS.values():
        for m in MYSTERIES.values():
            for p in POWERS.values():
                if compatible(s, m, p):
                    out.append((s.id, m.id, p.id))
    return out


def explain_rejection(setting: Setting, mystery: Mystery, power: Power) -> str:
    return (
        f"(No story: {power.name} does not make sense for a {mystery.thing} mystery at "
        f"{setting.place}. The clue and the power need to fit together.)"
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    power = POWERS[params.power]

    hero = Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Nova", "Mira", "Sky", "Juno", "Iris", "Pip", "Zara"} else "boy",
        label=params.name,
        meters={"grip": 1.0 if power.id == "grip" else 0.0, "distance": 0.0},
        memes={"curiosity": 1.0, "confidence": 1.0, "worry": 0.0, "relief": 0.0, "lesson": 0.0},
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        type="friend",
        label=params.helper,
        meters={"distance": 0.0},
        memes={"helpful": 1.0},
    )
    villain = Entity(
        id="Shadow",
        kind="character",
        type="villain",
        label="Shadow",
        meters={"distance": 1.0},
        memes={"mystery": 1.0, "blame": 0.0},
    )
    return World(setting=setting, mystery=mystery, power=power, hero=hero, helper=helper, villain=villain)


def narrate_story(world: World) -> None:
    h, f, v = world.hero, world.helper, world.villain
    s, m, p = world.setting, world.mystery, world.power

    world.say(
        f"{h.label} was the city’s young hero, and {p.name} was {h.pronoun('possessive')} favorite gear."
    )
    world.say(
        f"One evening at {s.place}, {s.detail} {m.foreshadow}"
    )
    world.say(
        f"Then {h.label} saw that {m.thing} had a strange problem: {m.trouble}."
    )
    world.para()
    h.memes["worry"] += 1.0
    world.say(
        f"{h.label} frowned and used {p.name} to look for the answer. {h.pronoun().capitalize()} thought the trouble must be caused by {v.label}."
    )
    world.say(
        f"But that guess felt shaky, because the first clue was really {m.clue_word} by {m.clue_place}."
    )
    world.say(
        f"{f.label} pointed to the clue and said, \"Slow down. The smallest marks often tell the truest story.\""
    )
    world.para()
    world.say(
        f"{h.label} climbed closer with {p.name}, checked the clue again, and noticed {m.culprit}."
    )
    world.say(
        f"That meant the mystery was not a big evil plot after all. It was a small problem hiding in plain sight."
    )
    world.say(
        f"{h.label} fixed it by choosing to {m.solution}."
    )
    h.memes["relief"] += 1.0
    h.memes["lesson"] += 1.0
    world.para()
    world.say(
        f"When the job was done, {m.thing} worked again, and {h.label} smiled at {f.label}."
    )
    world.say(
        f"{h.label} had learned the lesson: {m.lesson}."
    )
    world.say(
        f"And this time, the city felt safe because the hero had listened, looked twice, and solved the mystery the careful way."
    )

    world.facts.update(
        hero=h,
        helper=f,
        villain=v,
        setting=s,
        mystery=m,
        power=p,
        solved=True,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child where {f["hero"].label} uses {f["power"].name} to solve a mystery.',
        f'Tell a gentle story with a clue, a wrong guess, and a lesson learned at {f["setting"].place}.',
        f'Write a small mystery adventure that includes the word "grip" and ends with the answer being found by careful looking.',
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, m, p, s = world.hero, world.helper, world.mystery, world.power, world.setting
    return [
        QAItem(
            question=f"What mystery did {h.label} solve at {s.place}?",
            answer=f"{h.label} solved the mystery of the {m.thing}, which had been having trouble because {m.trouble}.",
        ),
        QAItem(
            question=f"What clue helped {h.label} figure it out?",
            answer=f"The important clue was the {m.clue_word} near {m.clue_place}. That clue helped point to the real answer.",
        ),
        QAItem(
            question=f"How did {p.name} help in the story?",
            answer=f"{p.name} helped {h.label} get close enough to inspect the problem carefully and solve the mystery.",
        ),
        QAItem(
            question=f"What lesson did {h.label} learn?",
            answer=f"{h.label} learned to {m.lesson}. That was the lesson at the end of the story.",
        ),
        QAItem(
            question=f"Who reminded {h.label} to slow down?",
            answer=f"{f.label} reminded {h.label} that small clues matter and that careful looking is better than rushing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m = world.mystery
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of evidence that helps you figure out what really happened.",
        ),
        QAItem(
            question="Why do heroes sometimes check things twice?",
            answer="Heroes check things twice so they do not jump to the wrong answer and miss an important clue.",
        ),
        QAItem(
            question="What does a lesson learned mean in a story?",
            answer="A lesson learned is the good idea or wise thought the character understands by the end.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint early on about something important that will matter later.",
        ),
        QAItem(
            question=f"Why might a {m.thing} need careful attention?",
            answer=f"A {m.thing} matters because if it stops working, the people who depend on it may get confused or unsafe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.villain]:
        lines.append(
            f"  {e.id:8} ({e.kind:9}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  setting: {world.setting.id}")
    lines.append(f"  mystery: {world.mystery.id}")
    lines.append(f"  power:   {world.power.id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery story world with grip and a lesson learned.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--power", choices=sorted(POWERS))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = valid_combos()
    if args.setting and args.mystery and args.power:
        if not compatible(SETTINGS[args.setting], MYSTERIES[args.mystery], POWERS[args.power]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], MYSTERIES[args.mystery], POWERS[args.power]))
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.power is None or c[2] == args.power)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, power = rng.choice(sorted(filtered))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, mystery=mystery, power=power, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="rooftop", mystery="signal_lamp", power="grip", name="Nova", helper="Comet"),
    StoryParams(setting="museum", mystery="missing_medal", power="scan", name="Mira", helper="Bolt"),
    StoryParams(setting="rooftop", mystery="stuck_gate", power="grip", name="Juno", helper="Gale"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_triples()
        print(f"{len(combos)} compatible stories:\n")
        for s, m, p in combos:
            print(f"  {s:9} {m:14} {p}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
