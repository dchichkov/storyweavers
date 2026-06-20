#!/usr/bin/env python3
"""A meadow-themed splash-pad mystery about opening a crystal door by solving the right physical problem.

Internal source tale:
At a meadow-themed splash pad, two children hurry toward a clear crystal door
that only opens when the water path is healthy. The door suddenly stays shut.
The children first wonder if someone locked it, but a real clue in the water
points toward the true blockage. With a splash helper's calm advice, they match
the clue to the mechanism, fix the physical problem, and watch the crystal door
open again.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Meadow:
    id: str
    name: str
    opening: str
    door_play: str
    ending: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Clue:
    id: str
    place: str
    text: str
    hint: str
    doubt: str


@dataclass(frozen=True)
class Cause:
    id: str
    place: str
    kind: str
    motion: str
    discovery: str
    result: str


@dataclass(frozen=True)
class Method:
    id: str
    solves: str
    tool: str
    action: str
    proof: str


@dataclass
class StoryParams:
    meadow: str
    clue: str
    cause: str
    method: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class SplashWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.entities[entity.role] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


MEADOWS: dict[str, Meadow] = {
    "clover_loop": Meadow(
        id="clover_loop",
        name="Clover Loop",
        opening="At the Clover Loop splash pad, green tiles curved like a tiny meadow path and the sprays hopped in neat circles around bare feet.",
        door_play="Behind the clear crystal door waited a bell wheel that sent a cool fan of water across the whole pad.",
        ending="the clover sprays stitched bright rings around their ankles while the crystal door flashed like a happy window",
        sites=("grate", "latch"),
    ),
    "daisy_steps": Meadow(
        id="daisy_steps",
        name="Daisy Steps",
        opening="At Daisy Steps, a daisy meadow of white petal tiles shone under the late sun, and the splash pad smelled like warm stone and clean water.",
        door_play="The crystal door guarded the daisy bell inside the last spray nook, where the biggest splash only came after the gate popped wide.",
        ending="the daisy jets leaped in tidy rows while the crystal door swung clear and blue",
        sites=("hinge", "latch"),
    ),
    "reed_bend": Meadow(
        id="reed_bend",
        name="Reed Bend",
        opening="At Reed Bend, long painted reeds lined the splash pad wall, and silver arcs hissed low across the meadow-colored floor like rain on a tiny marsh meadow.",
        door_play="At the far end stood a crystal door with water running through its frame, like a secret gate made out of rain.",
        ending="the reed sprays whispered over the tiles while the crystal door opened with a shining shiver",
        sites=("grate", "hinge"),
    ),
}

CLUES: dict[str, Clue] = {
    "leaf_swirl": Clue(
        id="leaf_swirl",
        place="grate",
        text="A little whirl of clover leaves kept circling one silver grate instead of washing away.",
        hint="The spinning leaves kept pointing to the grate as if the water wanted someone to look there.",
        doubt="Nia almost decided an older kid had pressed the wrong button, because a stuck door felt too sudden to be anything else.",
    ),
    "bubble_ring": Clue(
        id="bubble_ring",
        place="hinge",
        text="A fat ring of bubbles burped beside the crystal door hinge every time the spray cycle tried to start.",
        hint="The bubbles hugged the hinge in the very same place each time, as if they were hiding a tiny sore spot.",
        doubt="Omar whispered that maybe the door was being moody on purpose, because the clear panel looked too magical to have an ordinary reason.",
    ),
    "clicking_cup": Clue(
        id="clicking_cup",
        place="latch",
        text="A small clicking sound came from the latch cup whenever water filled it and slipped away again.",
        hint="The click was sharp and trapped, not smooth like the cheerful pop the door made when it opened.",
        doubt="For one worried moment the children wondered if the crystal door had been locked before they arrived.",
    ),
}

CAUSES: dict[str, Cause] = {
    "leaf_clog": Cause(
        id="leaf_clog",
        place="grate",
        kind="clog",
        motion="A mat of meadow leaves had plastered itself over the intake grate, stealing the water push that should have nudged the crystal door open.",
        discovery="When they knelt, they could see green leaves pinned flat to the grate while the water tugged at the edges.",
        result="As soon as the grate could breathe again, the pipes gave one eager rush and the crystal door unlocked with a wet sigh.",
    ),
    "foam_sensor": Cause(
        id="foam_sensor",
        place="hinge",
        kind="foam",
        motion="A stripe of sticky bubble foam had dried around the hinge sensor, so the crystal door kept waiting for a signal that never cleared.",
        discovery="Sunlight through the clear panel showed a cloudy white ring around the little sensor eye by the hinge.",
        result="Once the cloudy ring washed away, the hinge light turned blue and the crystal door swung free.",
    ),
    "pebble_jam": Cause(
        id="pebble_jam",
        place="latch",
        kind="pebble",
        motion="A shiny pebble had bounced into the latch cup and wedged it before the splash cycle could pop the crystal door open.",
        discovery="The sharp click came from a pebble trapped in the tiny cup where the latch should have risen and fallen.",
        result="When the cup was clear, the latch jumped up and the crystal door opened like a bright secret.",
    ),
}

METHODS: dict[str, Method] = {
    "rake_clear": Method(
        id="rake_clear",
        solves="clog",
        tool="the long drain rake",
        action="Nia slid the long drain rake through the water while Omar held the grate steady, and the leaf mat peeled away in one green sheet.",
        proof="The nearby sprays lifted taller at once, which showed the water could finally move the way it was meant to.",
    ),
    "bucket_rinse": Method(
        id="bucket_rinse",
        solves="foam",
        tool="a rinse bucket and a soft cloth",
        action="Omar poured clean water from a rinse bucket while Nia rubbed the sensor eye with a soft cloth tied around her wrist.",
        proof="The white ring melted off the hinge, and the tiny light changed color before their eyes.",
    ),
    "rubber_scoop": Method(
        id="rubber_scoop",
        solves="pebble",
        tool="the rubber scoop",
        action="Nia slipped the rubber scoop into the latch cup and lifted the pebble out while Omar listened for the click to stop.",
        proof="With the cup empty, the latch could rise instead of catching on the stone.",
    ),
}

PLACE_LABELS = {
    "grate": "the silver grate beside the spray stones",
    "hinge": "the crystal door hinge",
    "latch": "the little latch cup below the crystal door",
}

KIND_LABELS = {
    "clog": "a blocked water path",
    "foam": "a sticky foam ring on the sensor",
    "pebble": "a pebble jam in the latch cup",
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def end_sentence(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else f"{text}."


def explain_rejection(meadow_id: str, clue_id: str, cause_id: str, method_id: str) -> str:
    if meadow_id not in MEADOWS:
        return f"unknown meadow: {meadow_id}"
    if clue_id not in CLUES:
        return f"unknown clue: {clue_id}"
    if cause_id not in CAUSES:
        return f"unknown cause: {cause_id}"
    if method_id not in METHODS:
        return f"unknown method: {method_id}"
    meadow = MEADOWS[meadow_id]
    clue = CLUES[clue_id]
    cause = CAUSES[cause_id]
    method = METHODS[method_id]
    reasons: list[str] = []
    if clue.place != cause.place:
        reasons.append("the clue must point to the same part of the splash pad where the real problem lives")
    if method.solves != cause.kind:
        reasons.append("the repair method has to match the physical thing stopping the crystal door")
    if cause.place not in meadow.sites:
        reasons.append(f"{meadow.name} does not route this crystal door mystery through {PLACE_LABELS[cause.place]}")
    if not reasons:
        return "the requested story is valid"
    return "; ".join(reasons)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(params.meadow, params.clue, params.cause, params.method)
    return (reason == "the requested story is valid", reason)


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for meadow in MEADOWS:
        for clue in CLUES:
            for cause in CAUSES:
                for method in METHODS:
                    params = StoryParams(meadow=meadow, clue=clue, cause=cause, method=method)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    combos = all_params()
    if args.meadow:
        combos = [combo for combo in combos if combo.meadow == args.meadow]
    if args.clue:
        combos = [combo for combo in combos if combo.clue == args.clue]
    if args.cause:
        combos = [combo for combo in combos if combo.cause == args.cause]
    if args.method:
        combos = [combo for combo in combos if combo.method == args.method]
    return combos


def make_world(params: StoryParams) -> SplashWorld:
    meadow = MEADOWS[params.meadow]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    world = SplashWorld(params)
    world.add(Entity("nia", "character", "girl", "Nia", role="hero", traits=["observant", "quick"]))
    world.add(Entity("omar", "character", "boy", "Omar", role="friend", traits=["steady", "kind"]))
    world.add(Entity("sol", "character", "woman", "Helper Sol", role="helper", traits=["calm"]))
    world.add(Entity("team", "group", "pair", "the two children", role="team"))
    world.add(Entity("pad", "place", "splash_pad", "the splash pad"))
    world.add(Entity("door", "object", "door", "the crystal door"))
    world.add(Entity("grate", "mechanism", "grate", PLACE_LABELS["grate"]))
    world.add(Entity("hinge", "mechanism", "hinge", PLACE_LABELS["hinge"]))
    world.add(Entity("latch", "mechanism", "latch", PLACE_LABELS["latch"]))
    world.add(Entity("bell", "object", "bell", "the bell wheel"))

    world.get("pad").meters["water_pressure"] = 3.0
    world.get("pad").meters["sparkle"] = 2.0
    world.get("door").meters["stuckness"] = 2.0
    world.get("door").meters["open"] = 0.0
    world.get("door").meters["clear_glow"] = 1.0
    world.get("team").memes["trust"] = 2.0
    world.get("team").memes["worry"] = 0.0
    world.get("nia").memes["curiosity"] = 1.0
    world.get("omar").memes["patience"] = 1.0
    world.get("sol").memes["steadiness"] = 2.0
    world.get(cause.place).meters["problem_here"] = 1.0

    world.facts.update(
        meadow_name=meadow.name,
        clue_text=clue.text,
        clue_hint=clue.hint,
        doubt=clue.doubt,
        place_label=PLACE_LABELS[cause.place],
        kind_label=KIND_LABELS[cause.kind],
        tool=method.tool,
    )
    return world


def opening(world: SplashWorld) -> None:
    meadow = MEADOWS[world.params.meadow]
    world.get("team").memes["joy"] += 1.0
    world.record(
        "opening",
        f"{meadow.opening} {meadow.door_play}",
        "pad",
        "door",
    )
    world.record(
        "setup",
        "Nia and Omar wanted to ring that bell before the end-of-play whistle, so they ran through the cool arcs and lined up on the stepping stones together.",
        "team",
        "bell",
    )


def problem_appears(world: SplashWorld) -> None:
    meadow = MEADOWS[world.params.meadow]
    team = world.get("team")
    door = world.get("door")
    pad = world.get("pad")
    team.meters["goal_reached"] = 0.0
    team.memes["worry"] += 1.0
    team.memes["trust"] -= 0.2
    door.meters["stuckness"] += 1.0
    pad.meters["water_pressure"] -= 1.0
    world.record(
        "problem",
        f"When Nia slapped the last stepping stone, the crystal door did not open. Instead the sprays in {meadow.name} gave a tired shiver, and the bell wheel behind the clear panel stayed still.",
        "door",
        "bell",
    )


def notice_clue(world: SplashWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("nia").memes["curiosity"] += 1.0
    world.record(
        "clue",
        f"{clue.text} {end_sentence(sentence_start(clue.hint))}",
        "hero",
        clue.place,
    )


def false_guess(world: SplashWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("team").memes["worry"] += 0.5
    world.record(
        "guess",
        f"{clue.doubt} But Omar shook his head. \"If someone had only pushed a button,\" he said, \"the water would not keep whispering in the same place.\"",
        "friend",
        "hero",
    )


def turn_to_reasoning(world: SplashWorld) -> None:
    cause = CAUSES[world.params.cause]
    if cause.kind == "clog":
        theory = "If the water path was choked at the grate, the door would never get the push it needed."
    elif cause.kind == "foam":
        theory = "If the sensor eye could not see clearly, the door would keep waiting even when the path was open."
    else:
        theory = "If the latch cup could not rise and fall, the door would stay shut no matter how hard the cycle tried."
    world.facts["theory"] = theory
    world.get("team").memes["trust"] += 0.6
    world.get("sol").memes["guidance"] += 1.0
    world.record(
        "turn",
        f'Helper Sol knelt beside them and said, "A splash-pad mystery likes a real reason. Follow the water, not the worry." Nia listened again, looked again, and made a careful guess: {theory}',
        "helper",
        cause.place,
    )


def inspect_problem(world: SplashWorld) -> None:
    cause = CAUSES[world.params.cause]
    world.get("nia").memes["curiosity"] += 1.0
    world.get("omar").memes["patience"] += 0.5
    world.get("team").memes["teamwork"] += 1.0
    world.record(
        "inspect",
        f"So the children crouched by {PLACE_LABELS[cause.place]} instead of guessing at magic. {cause.motion} Soon they found the proof: {end_sentence(cause.discovery)}",
        "team",
        cause.place,
    )


def solve_problem(world: SplashWorld) -> None:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    pad = world.get("pad")
    door = world.get("door")
    team = world.get("team")
    pad.meters["water_pressure"] += 2.0
    door.meters["stuckness"] = 0.0
    door.meters["open"] = 1.0
    team.memes["relief"] += 1.0
    team.memes["trust"] += 0.8
    team.meters["goal_reached"] = 1.0
    world.facts["solved"] = True
    world.record(
        "solve",
        f"{method.action} {method.proof} {cause.result}",
        "team",
        "door",
    )


def ending(world: SplashWorld) -> None:
    meadow = MEADOWS[world.params.meadow]
    world.get("team").memes["joy"] += 1.0
    world.record(
        "ending",
        f"The children splashed through the opening together, rang the bell wheel, and laughed when the biggest fan of water flew over their shoulders. By the time the whistle blew, {meadow.ending}.",
        "team",
        "bell",
    )


def tell(params: StoryParams) -> SplashWorld:
    world = make_world(params)
    opening(world)
    world.para()
    problem_appears(world)
    notice_clue(world)
    false_guess(world)
    turn_to_reasoning(world)
    world.para()
    inspect_problem(world)
    solve_problem(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: SplashWorld) -> list[str]:
    return [
        'Write a child-facing mystery set in a splash pad that clearly includes the words "meadow" and "crystal door."',
        f"Build the middle around one physical clue at {world.facts['place_label']} and let problem solving, not luck, unlock the door.",
        "End with a vivid image that proves the mechanism changed and the children can play again.",
    ]


def story_grounded_qa(world: SplashWorld) -> list[QAItem]:
    clue = CLUES[world.params.clue]
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why did the crystal door stay shut at the splash pad?",
            answer=(
                f"The crystal door stayed shut because of {KIND_LABELS[cause.kind]}. "
                f"{cause.motion} That physical problem kept the door from getting the signal or push it needed."
            ),
        ),
        QAItem(
            question="What clue helped Nia and Omar stop guessing?",
            answer=(
                f"The clue was that {clue.text.lower()} "
                f"Because the same sign kept happening in one spot, the children understood that the water was pointing to a real mechanism instead of a prank."
            ),
        ),
        QAItem(
            question="How did the children solve the mystery?",
            answer=(
                f"They inspected {PLACE_LABELS[cause.place]} and used {method.tool} to fix the problem. "
                f"{method.proof} After that, the crystal door finally opened and the bell wheel could run."
            ),
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=(
                "The children could go through the crystal door and ring the bell wheel at last. "
                "The taller sprays and the moving gate proved that the splash pad was healthy again."
            ),
        ),
    ]


def world_knowledge_qa(world: SplashWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why is a repeating clue useful in a mystery?",
            answer=(
                "A repeating clue matters because it points to a cause that is still happening in the world. "
                "When the same bubble, click, or swirl appears in one place, careful searchers know where to test their idea."
            ),
        ),
        QAItem(
            question="Why did the children need the right tool instead of just pulling harder on the door?",
            answer=(
                f"They needed the right tool because the real trouble was {KIND_LABELS[cause.kind]}, not weak hands. "
                f"Using {method.tool} let them fix the mechanism safely without forcing the crystal door."
            ),
        ),
        QAItem(
            question="What makes this splash-pad solution an example of problem solving?",
            answer=(
                "The children observed a clue, formed a reasonable theory, and tested it on the real mechanism. "
                "They solved the mystery by matching evidence to the right action instead of blaming someone or making a wild guess."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(M,C,A,X) :-
    meadow(M), clue(C), cause(A), method(X),
    clue_place(C, P), cause_place(A, P),
    cause_kind(A, K), method_solves(X, K),
    meadow_site(M, P).

ok :- chosen(M, C, A, X), valid(M, C, A, X).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    lines: list[str] = []
    for meadow_id, meadow in MEADOWS.items():
        lines.append(fact("meadow", meadow_id))
        for site in meadow.sites:
            lines.append(fact("meadow_site", meadow_id, site))
    for clue_id, clue in CLUES.items():
        lines.append(fact("clue", clue_id))
        lines.append(fact("clue_place", clue_id, clue.place))
    for cause_id, cause in CAUSES.items():
        lines.append(fact("cause", cause_id))
        lines.append(fact("cause_place", cause_id, cause.place))
        lines.append(fact("cause_kind", cause_id, cause.kind))
    for method_id, method in METHODS.items():
        lines.append(fact("method", method_id))
        lines.append(fact("method_solves", method_id, method.solves))
    if params is not None:
        lines.append(fact("chosen", params.meadow, params.clue, params.cause, params.method))
    return "\n".join(lines) + "\n"


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    if "meadow" not in story_lower:
        raise AssertionError("story is missing 'meadow'")
    if "crystal door" not in story_lower:
        raise AssertionError("story is missing 'crystal door'")
    if "splash pad" not in story_lower:
        raise AssertionError("story is missing 'splash pad'")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if world.get("door").meters.get("open", 0) < 1:
        raise AssertionError("crystal door never opened")
    if world.get("door").meters.get("stuckness", 1) != 0:
        raise AssertionError("door stayed stuck")
    if world.get("team").meters.get("goal_reached", 0) < 1:
        raise AssertionError("children never reached the bell wheel")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted((params.meadow, params.clue, params.cause, params.method) for params in all_params())
    lp = sorted(asp_valid_combos())
    if py != lp:
        print("MISMATCH between Python and ASP gates:")
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        if only_py:
            print("  only in Python:", only_py)
        if only_lp:
            print("  only in ASP:", only_lp)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid splash-pad mysteries).")
    for params in all_params():
        verify_sample(generate(params))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a meadow splash-pad mystery about a crystal door and problem solving."
    )
    parser.add_argument("--meadow", choices=sorted(MEADOWS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = all(getattr(args, field) is not None for field in ("meadow", "clue", "cause", "method"))
    if explicit:
        params = StoryParams(args.meadow, args.clue, args.cause, args.method, args.seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    combos = matching_params(args)
    if not combos:
        meadow = args.meadow or next(iter(MEADOWS))
        clue = args.clue or next(iter(CLUES))
        cause = args.cause or next(iter(CAUSES))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(meadow, clue, cause, method))
    chosen = StoryParams(**vars(rng.choice(combos)))
    chosen.seed = args.seed
    return chosen


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_params(args)
        if not combos:
            meadow = args.meadow or next(iter(MEADOWS))
            clue = args.clue or next(iter(CLUES))
            cause = args.cause or next(iter(CAUSES))
            method = args.method or next(iter(METHODS))
            raise StoryError(explain_rejection(meadow, clue, cause, method))
        samples = []
        for index, params in enumerate(combos):
            chosen = StoryParams(**vars(params))
            chosen.seed = args.seed + index if args.seed is not None else None
            samples.append(generate(chosen))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    combos = matching_params(args)
    if not combos:
        meadow = args.meadow or next(iter(MEADOWS))
        clue = args.clue or next(iter(CLUES))
        cause = args.cause or next(iter(CAUSES))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(meadow, clue, cause, method))
    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = base_seed + index
        rng = random.Random(seed)
        chosen = StoryParams(**vars(rng.choice(combos)))
        chosen.seed = seed
        samples.append(generate(chosen))
    return samples


def dump_trace(world: SplashWorld) -> str:
    lines = ["TRACE", f"meadow: {world.facts['meadow_name']}"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("ENTITIES")
    for entity in world.entities.values():
        if entity.role and entity.role != entity.id:
            continue
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
        if meters:
            lines.append(f"    meters={meters}")
        if memes:
            lines.append(f"    memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines: list[str] = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid meadow crystal door splash-pad mysteries:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return 0
    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== meadow_crystal_door_splash_pad_problem_solving #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
