#!/usr/bin/env python3
"""
Standalone storyworld for a small mystery domain.

Premise:
A curious child notices a repeating clue in a quiet place, follows it step by
step, and learns the reason behind the mystery.

The simulated world centers on:
- repetition: the clue appears again and again
- curiosity: the child keeps looking and asking
- reason: the final explanation makes the odd pattern make sense
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
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


@dataclass
class Setting:
    place: str
    indoors: bool
    mood: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    symptom: str
    repeated_symptom: str
    cause: str
    trail: str
    reveal: str
    clue_word: str
    action: str
    ask: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(self.setting, copy.deepcopy(self.entities), set(self.fired), [[]], dict(self.facts))


@dataclass
class Rule:
    name: str
    apply: callable


def _r_curiosity(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if child.meters.get("asked", 0.0) >= 2 and ("curiosity", "notice") not in world.fired:
        world.fired.add(("curiosity", "notice"))
        child.meters["noticed"] = child.meters.get("noticed", 0.0) + 1
        out.append("The odd pattern stayed on the child's mind, so the child looked again.")
    return out


def _r_repetition(world: World) -> list[str]:
    out = []
    clue = world.get("clue")
    if clue.meters.get("seen", 0.0) < 2:
        return out
    if ("repetition", "pattern") in world.fired:
        return out
    world.fired.add(("repetition", "pattern"))
    clue.memes["mystery"] = clue.memes.get("mystery", 0.0) + 1
    out.append("The same clue appeared again, and that made the puzzle harder to ignore.")
    return out


def _r_reason(world: World) -> list[str]:
    out = []
    child = world.get("child")
    cause = world.get("cause")
    clue = world.get("clue")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if clue.meters.get("seen", 0.0) < 3:
        return out
    if ("reason", "reveal") in world.fired:
        return out
    world.fired.add(("reason", "reveal"))
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    cause.meters["revealed"] = 1
    out.append(f"At last, the reason was clear: {cause.label}.")
    return out


RULES = [Rule("curiosity", _r_curiosity), Rule("repetition", _r_repetition), Rule("reason", _r_reason)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for c in s.clues:
            lines.append(asp.fact("clueword", sid, c))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("symptom", mid, m.symptom))
        lines.append(asp.fact("repeated", mid, m.repeated_symptom))
        lines.append(asp.fact("cause", mid, m.cause))
        lines.append(asp.fact("trail", mid, m.trail))
        lines.append(asp.fact("reveal", mid, m.reveal))
    return "\n".join(lines)


ASP_RULES = r"""
curious(M) :- mystery(M), symptom(M,_).
repeating(M) :- mystery(M), repeated(M,_).
explained(M) :- mystery(M), cause(M,_), reveal(M,_).
valid(S,M) :- setting(S), mystery(M), curious(M), repeating(M), explained(M).
#show valid/2.
"""


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class WorldModel(World):
    pass


SETTINGS = {
    "library": Setting(place="the library", indoors=True, mood="quiet", clues=["book"]),
    "hallway": Setting(place="the hallway", indoors=True, mood="echoing", clues=["door"]),
    "garden": Setting(place="the garden path", indoors=False, mood="still", clues=["footprint"]),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        id="missing_cookie",
        symptom="a cookie kept disappearing",
        repeated_symptom="one more cookie was gone each time the child looked",
        cause="the little dog was carrying the cookie to the rug",
        trail="crumbs and tiny paw prints",
        reveal="the dog was hiding the cookie under the rug",
        clue_word="crumbs",
        action="follow the crumbs",
        ask="Who kept taking the cookie?",
    ),
    "tapping_pipe": Mystery(
        id="tapping_pipe",
        symptom="a tapping sound came from the wall",
        repeated_symptom="tap-tap-tap came again and again",
        cause="the rainwater in a loose pipe was knocking softly",
        trail="drips and silver lines",
        reveal="the pipe was loose and needed a careful fix",
        clue_word="tap",
        action="listen at the wall",
        ask="What made the tapping sound?",
    ),
    "lost_bell": Mystery(
        id="lost_bell",
        symptom="the small bell rang by itself",
        repeated_symptom="ding-ding came back each time the child paused",
        cause="the breeze kept swinging a ribbon tied to the bell",
        trail="a ribbon and a moving shadow",
        reveal="the breeze was tugging the ribbon near the window",
        clue_word="ding",
        action="look by the window",
        ask="Why did the bell keep ringing?",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "June", "Ada"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Noah", "Ben", "Eli"]
HELPERS = ["mother", "father", "librarian", "neighbor"]
TRAITS = ["curious", "careful", "bright-eyed", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            combos.append((s, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with repetition, curiosity, and reason.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    setting, mystery = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_word))
    cause = world.add(Entity(id="cause", type="thing", label=mystery.cause))
    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 1.0
    helper.memes["calm"] = 1.0
    world.facts.update(params=params, child=child, helper=helper, clue=clue, cause=cause, mystery=mystery)
    return world


def tell(world: World) -> None:
    f = world.facts
    params: StoryParams = f["params"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    clue: Entity = f["clue"]
    mystery: Mystery = f["mystery"]
    place = SETTINGS[params.setting].place

    world.say(f"At {place}, {params.name} was the sort of child who noticed small things.")
    world.say(f"{params.name} kept asking about {mystery.symptom}, because {params.name} was very curious.")
    world.para()
    world.say(f"Then the same clue showed up again: {mystery.repeated_symptom}.")
    clue.meters["seen"] = clue.meters.get("seen", 0.0) + 1
    propagate(world)
    world.say(f"{params.name} looked at {clue.label}, then looked again, trying to reason it out.")
    clue.meters["seen"] += 1
    world.say(f"{helper.label.capitalize()} helped {params.name} {mystery.action}.")
    propagate(world)
    world.para()
    clue.meters["seen"] += 1
    world.say(f"One more time, the clue came back: {mystery.repeated_symptom}.")
    propagate(world)
    world.say(f"That was enough. {params.name} followed {mystery.trail} and learned the reason.")
    world.say(f"In the end, {mystery.reveal}.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short mystery story for a child named {params.name} who keeps noticing {mystery.clue_word}.',
        f"Tell a gentle story where {params.name} is curious, sees the same clue again and again, and finds the reason behind it.",
        f'Write a simple story about repetition, curiosity, and reason that ends with the mystery being explained.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Why did {params.name} keep looking at the clue?",
            answer=f"{params.name} kept looking because {params.name} was curious and wanted the reason behind the mystery.",
        ),
        QAItem(
            question=f"What happened more than once in the story?",
            answer=f"The clue kept coming back, so the child noticed the same pattern again and again.",
        ),
        QAItem(
            question=f"Who helped {params.name} look more closely?",
            answer=f"{helper.label.capitalize()} helped {params.name} follow the clue and think it through.",
        ),
        QAItem(
            question=f"What was the reason behind {mystery.symptom}?",
            answer=f"The reason was that {mystery.cause}. That made the strange clue make sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something unknown.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition is when the same thing happens again and again.",
        ),
        QAItem(
            question="What is a reason?",
            answer="A reason is the explanation for why something happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id} ({e.type}) meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    StoryParams(setting="library", mystery="missing_cookie", name="Mia", gender="girl", helper="mother"),
    StoryParams(setting="hallway", mystery="tapping_pipe", name="Leo", gender="boy", helper="father"),
    StoryParams(setting="garden", mystery="lost_bell", name="Nora", gender="girl", helper="neighbor"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
