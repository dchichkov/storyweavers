#!/usr/bin/env python3
"""
A small adventure storyworld: a traveler, a stack, a refuge, and a misunderstood
change that reveals a moral value.

The domain is built around three story instruments:
- mode: the way the hero is traveling or acting
- stack: a physical pile that can hide, protect, or become a clue
- refuge: a safe place where the turn resolves

Theme instruments:
- Transformation
- Misunderstanding
- Moral Value

The stories are short, concrete, and state-driven: a child or young hero sets
out, misreads the meaning of something in the world, changes mode to respond,
and finds refuge after learning a value such as honesty, kindness, courage, or
care.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old trail"
    refuge: str = "the lantern cave"
    weather: str = "windy"


@dataclass
class Mode:
    id: str
    name: str
    verb: str
    pace: str
    risk: str
    counter: str


@dataclass
class Stack:
    id: str
    label: str
    phrase: str
    role: str
    size: str
    can_hide: bool = False


@dataclass
class Refuge:
    id: str
    label: str
    phrase: str
    comfort: str
    moral: str


@dataclass
class StoryParams:
    mode: str
    stack: str
    refuge: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "trail": Setting(place="the old trail", refuge="the lantern cave", weather="windy"),
    "ruins": Setting(place="the stone ruins", refuge="the hidden arch", weather="misty"),
    "harbor": Setting(place="the harbor road", refuge="the watch shed", weather="stormy"),
}

MODES = {
    "walk": Mode(
        id="walk",
        name="walking",
        verb="walk carefully",
        pace="carefully",
        risk="slipping on loose stones",
        counter="slow down and watch each step",
    ),
    "sneak": Mode(
        id="sneak",
        name="sneaking",
        verb="sneak quietly",
        pace="quietly",
        risk="being mistaken for a thief",
        counter="show the truth plainly",
    ),
    "climb": Mode(
        id="climb",
        name="climbing",
        verb="climb up",
        pace="upward",
        risk="falling from a steep stack",
        counter="hold on and move with care",
    ),
    "carry": Mode(
        id="carry",
        name="carrying",
        verb="carry the bundle",
        pace="steadily",
        risk="dropping a heavy stack",
        counter="share the load with a friend",
    ),
}

STACKS = {
    "rockpile": Stack(
        id="rockpile",
        label="rock pile",
        phrase="a tall rock pile",
        role="it hid a small path marker",
        size="tall",
        can_hide=True,
    ),
    "crate_stack": Stack(
        id="crate_stack",
        label="crate stack",
        phrase="a wobbling stack of crates",
        role="it held spare supplies",
        size="wobbly",
        can_hide=True,
    ),
    "log_stack": Stack(
        id="log_stack",
        label="log stack",
        phrase="a neat stack of logs",
        role="it sheltered dry tinder",
        size="neat",
        can_hide=False,
    ),
}

REFUGES = {
    "cave": Refuge(
        id="cave",
        label="lantern cave",
        phrase="the lantern cave",
        comfort="warm light and dry stone",
        moral="courage can be quiet",
    ),
    "arch": Refuge(
        id="arch",
        label="hidden arch",
        phrase="the hidden arch",
        comfort="a safe roof and a view of the road",
        moral="truth is a kind of kindness",
    ),
    "shed": Refuge(
        id="shed",
        label="watch shed",
        phrase="the watch shed",
        comfort="a dry bench and a kettle",
        moral="sharing makes hard jobs lighter",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Tess", "Maya"]
BOY_NAMES = ["Arlo", "Jude", "Finn", "Eli", "Theo", "Pax"]
COMPANIONS = ["sister", "brother", "friend", "uncle", "mother", "father"]
TRAITS = ["brave", "curious", "gentle", "patient", "steady", "bright"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A stack matters when it can hide a clue or create a risky shape.
stack_matters(S) :- stack(S), hides_path(S).
stack_matters(S) :- stack(S), risky_height(S).

% A misunderstanding happens when the meaning of the stack is read the wrong way.
misunderstanding(M) :- mode(M), stack(S), clue_hidden(S), sees_warning_as_threat(M, S).

% A moral-value turn happens when the hero chooses a value-based response.
moral_turn(V) :- value(V), chosen_after_misunderstanding(V).

% A refuge resolves the story when it is reachable and comforting.
safe_refuge(R) :- refuge(R), comforting(R), reachable(R).

valid_story(M,S,R) :- mode(M), stack(S), refuge(R), stack_matters(S), safe_refuge(R).
#show valid_story/3.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for mid, m in MODES.items():
        lines.append(asp.fact("mode", mid))
        if m.risk == "being mistaken for a thief":
            lines.append(asp.fact("sees_warning_as_threat", mid, "rockpile"))
        if m.risk == "slipping on loose stones":
            lines.append(asp.fact("risky_height", "rockpile"))
    for sid, s in STACKS.items():
        lines.append(asp.fact("stack", sid))
        if s.can_hide:
            lines.append(asp.fact("hides_path", sid))
        if s.role:
            lines.append(asp.fact("clue_hidden", sid))
    for rid, r in REFUGES.items():
        lines.append(asp.fact("refuge", rid))
        lines.append(asp.fact("comforting", rid))
        lines.append(asp.fact("reachable", rid))
    for v in ["honesty", "kindness", "courage", "care", "sharing"]:
        lines.append(asp.fact("value", v))
    lines.append(asp.fact("chosen_after_misunderstanding", "honesty"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for m in MODES:
        for s in STACKS:
            for r in REFUGES:
                if m == "sneak" and s == "log_stack":
                    continue
                combos.append((m, s, r))
    return combos


def explain_rejection(mode: Mode, stack: Stack) -> str:
    return (
        f"(No story: {mode.name} and {stack.label} do not make a good adventure pair "
        f"for a misunderstanding. Try a stack that can hide a clue or make the hero "
        f"look suspicious.)"
    )


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def build_story(world: World, hero: Entity, companion: Entity, mode: Mode, stack: Stack, refuge: Refuge) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait']} {hero.type} who liked {mode.name} on the trail."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {companion.label} reached {world.setting.place}, "
        f"where they found {stack.phrase}."
    )
    hero.memes["wonder"] += 1
    world.say(
        f"{stack.phrase.capitalize()} looked strange, and {hero.id} thought {stack.role}, which made {hero.pronoun()} pause."
    )

    world.para()
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} tried to {mode.verb}, but the stack cast a long shadow, and the odd shape caused a misunderstanding."
    )
    world.say(
        f"{hero.id} worried the stack was a warning and almost turned back."
    )

    world.para()
    hero.memes["insight"] += 1
    world.say(
        f"Then {hero.pronoun('possessive')} {companion.label} noticed the truth: the stack was only hiding a trail marker."
    )
    hero.memes["transformation"] += 1
    hero.memes["moral_value"] += 1
    world.say(
        f"{hero.id} changed mode and chose to {mode.counter}, showing {refuge.moral}."
    )
    world.say(
        f"They followed the marker to {refuge.phrase}, where {refuge.comfort} waited, and the adventure felt safe again."
    )
    world.say(
        f"In the end, {hero.id} learned that {refuge.moral}."
    )


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child that uses the words "{f["mode"].name}", "{f["stack"].label}", and "{f["refuge"].label}".',
        f"Tell a gentle adventure where {f['hero'].id} misunderstands a {f['stack'].label} and finds a safe refuge.",
        f"Write a child-facing story about a change of mode, a mistaken clue, and a moral value like honesty or courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    mode: Mode = f["mode"]
    stack: Stack = f["stack"]
    refuge: Refuge = f["refuge"]
    return [
        QAItem(
            question=f"What did {hero.id} think the {stack.label} meant at first?",
            answer=f"{hero.id} thought the {stack.label} was a warning, so {hero.pronoun()} almost turned back.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"The misunderstanding was that {hero.id} read the {stack.phrase} the wrong way, even though it was only hiding a trail marker.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} changed from worry to calm courage, chose to {mode.counter}, and learned to trust the truth before reacting.",
        ),
        QAItem(
            question=f"Where did the children go for safety?",
            answer=f"They followed the marker to {refuge.phrase}, which was their refuge.",
        ),
        QAItem(
            question=f"What moral value did the adventure teach?",
            answer=f"It taught that {refuge.moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a refuge?",
            answer="A refuge is a safe place where someone can rest, hide from danger, or feel protected.",
        ),
        QAItem(
            question="What can a stack be used for in a story?",
            answer="A stack can hide something, make a place look tall, or become a clue the hero must understand.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes in an important way, such as a brave choice replacing fear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------
def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.mode] if params.mode in SETTINGS else SETTINGS["trail"]
    world = World(setting)
    mode = MODES[params.mode]
    stack = STACKS[params.stack]
    refuge = REFUGES[params.refuge]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"trait": params.companion, "joy": 0.0, "fear": 0.0, "insight": 0.0, "transformation": 0.0, "moral_value": 0.0, "wonder": 0.0},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type="person",
        label=params.companion,
    ))

    hero.memes["trait"] = params.companion
    world.facts.update(hero=hero, companion=companion, mode=mode, stack=stack, refuge=refuge)
    build_story(world, hero, companion, mode, stack, refuge)
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mode and args.stack:
        mode = MODES[args.mode]
        stack = STACKS[args.stack]
        if args.mode == "sneak" and args.stack == "log_stack":
            raise StoryError(explain_rejection(mode, stack))
    combos = [c for c in valid_combos()
              if (args.mode is None or c[0] == args.mode)
              and (args.stack is None or c[1] == args.stack)
              and (args.refuge is None or c[2] == args.refuge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mode, stack, refuge = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(mode=mode, stack=stack, refuge=refuge, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(mode="walk", stack="rockpile", refuge="cave", name="Mina", gender="girl", companion="friend"),
    StoryParams(mode="sneak", stack="crate_stack", refuge="arch", name="Arlo", gender="boy", companion="brother"),
    StoryParams(mode="carry", stack="log_stack", refuge="shed", name="Nora", gender="girl", companion="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: mode, stack, refuge, transformation, misunderstanding, moral value.")
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--stack", choices=STACKS)
    ap.add_argument("--refuge", choices=REFUGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.mode} / {p.stack} / {p.refuge}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
