#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/intermediate_mystery_to_solve_space_adventure.py
=================================================================================

A standalone story world for a small space-adventure mystery.

Premise
-------
A child crew explores a tiny moon base, finds an odd intermediate clue, and must
solve a missing-item mystery before their launch window closes. The world model
tracks characters, places, clues, meters, and memes so the story is driven by
state, not by a frozen paragraph swap.

The domain stays close to a classic space adventure feel:
- a small crew
- a moon/base/station setting
- a mystery to solve
- a final reveal that changes the world state

It also includes the required word "intermediate" in a natural way.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    mystery_spot: str
    launch_window: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    found_in: str
    importance: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    revealed_by: str
    reveal_text: str
    fix_text: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["mystery"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in world.entities.values():
            if char.kind == "character":
                char.memes["curiosity"] += 1
        out.append("__worry__")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_found") and not world.facts.get("cause_revealed"):
        sig = ("discover", world.facts["clue_found"])
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__discovery__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("discover", _r_discover)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_truth(world: World, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("mystery").meters["mystery"] += 1
    sim.facts["clue_found"] = clue.id
    propagate(sim, narrate=False)
    return {
        "clue_found": True,
        "pressure": sum(e.memes["curiosity"] for e in sim.entities.values() if e.kind == "character"),
    }


def introduce(world: World, pilot: Entity, helper: Entity, setting: Setting) -> None:
    pilot.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a quiet evening at {setting.label}, {pilot.id} and {helper.id} "
        f"glided through {setting.scene}."
    )
    world.say(
        f'Their ship hummed like a sleepy bee, and the crew kept one eye on '
        f'{setting.launch_window}.'
    )


def mystery_found(world: World, clue: Clue, setting: Setting) -> None:
    world.get("mystery").meters["mystery"] += 1
    world.facts["clue_found"] = clue.id
    world.say(
        f"Then {clue.phrase} appeared in {setting.mystery_spot}. "
        f'It was an intermediate clue, not the answer, but it was too neat to ignore.'
    )


def ask_about(world: World, helper: Entity, pilot: Entity, clue: Clue, cause: Cause) -> None:
    helper.memes["curiosity"] += 1
    world.say(
        f'{helper.id} blinked. "If this clue is here, what moved it?" '
        f"{helper.pronoun().capitalize()} asked."
    )
    world.say(
        f"{pilot.id} leaned closer and began to sort the clues in order, one step at a time."
    )


def inspect(world: World, pilot: Entity, clue: Clue, cause: Cause) -> None:
    pred = predict_truth(world, clue)
    world.facts["predicted_pressure"] = pred["pressure"]
    world.say(
        f'{pilot.id} checked the marks, the dust, and the little gap beside the panel. '
        f"{pilot.id} saw that the clue had been moved by something small, not by a storm of space junk."
    )


def reveal(world: World, pilot: Entity, helper: Entity, cause: Cause, setting: Setting) -> None:
    cause.meters["revealed"] += 1
    world.facts["cause_revealed"] = cause.id
    world.say(
        f"At last, {pilot.id} found the answer: {cause.revealed_by}. "
        f"{cause.reveal_text}"
    )
    world.say(
        f"Together they fixed it with a careful twist and a steady hand. {cause.fix_text}"
    )
    pilot.memes["pride"] += 1
    helper.memes["pride"] += 1


def end_story(world: World, pilot: Entity, helper: Entity, setting: Setting) -> None:
    pilot.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"By the time {setting.launch_window} opened, the base was calm again. "
        f"{pilot.id} and {helper.id} floated home under the bright station lights, "
        f"happy that the mystery had been solved."
    )
    world.say(
        f"Their little ship drifted past the window, and the solved clue sat safely in its tray."
    )


def tell(
    setting: Setting,
    clue: Clue,
    cause: Cause,
    pilot_name: str = "Mia",
    pilot_gender: str = "girl",
    helper_name: str = "Bo",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    pilot = world.add(Entity(id=pilot_name, kind="character", type=pilot_gender, role="pilot"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    mystery = world.add(Entity(id="mystery", type="thing", label="the mystery"))
    scene = world.add(Entity(id="scene", type="thing", label=setting.label))

    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["cause"] = cause
    world.facts["parent"] = parent
    world.facts["pilot"] = pilot
    world.facts["helper"] = helper

    introduce(world, pilot, helper, setting)
    world.para()
    mystery_found(world, clue, setting)
    ask_about(world, helper, pilot, clue, cause)
    inspect(world, pilot, clue, cause)
    world.para()
    reveal(world, pilot, helper, cause, setting)
    end_story(world, pilot, helper, setting)

    world.facts["outcome"] = "solved"
    world.facts["scene"] = scene
    world.facts["mystery"] = mystery
    return world


SETTINGS = {
    "moonbase": Setting(
        id="moonbase",
        label="Moonbase Nine",
        scene="a silver hallway with round windows and soft floor lights",
        mystery_spot="the middle locker by the airlock",
        launch_window="the next launch window",
        tags={"space", "moon"},
    ),
    "orbit": Setting(
        id="orbit",
        label="the orbiting station",
        scene="a curved corridor lined with blinking panels and tiny viewports",
        mystery_spot="the storage nook near the scanner room",
        launch_window="sunrise over Earth",
        tags={"space", "station"},
    ),
    "redplanet": Setting(
        id="redplanet",
        label="the red planet camp",
        scene="a dusty dome with a little rover parked nearby",
        mystery_spot="the tool shelf beside the dome door",
        launch_window="the evening return flight",
        tags={"space", "planet"},
    ),
}

CLUES = {
    "glove": Clue("glove", "single glove", "a single glove", "the corridor floor", 1, {"tool"}),
    "badge": Clue("badge", "missing badge", "a missing badge", "the scanner bench", 1, {"badge"}),
    "chip": Clue("chip", "star chip", "a star chip", "inside a loose panel", 2, {"chip"}),
}

CAUSES = {
    "pet": Cause("pet", "a small space mouse", "the pet mouse", "A tiny gray mouse had hidden it for nesting.",
                 "They set out little crumbs and guided the mouse back outside.", 1, {"animal"}),
    "drone": Cause("drone", "a sleepy helper drone", "the helper drone",
                   "A sleepy helper drone had nudged it while charging.",
                   "They reset the drone and returned the item to its tray.", 2, {"machine"}),
    "wind": Cause("wind", "a burst from the air vent", "the air vent",
                  "A burst from the air vent had pushed it across the floor.",
                  "They tightened the vent cover so nothing could blow away again.", 3, {"air"}),
}

PILOT_NAMES = ["Mia", "Nina", "Luna", "Tara", "Ivy", "Noah", "Bo", "Zed"]
HELPER_NAMES = ["Bo", "Kai", "Rex", "Jo", "Max", "Eli", "Nia", "Ada"]
GENDERS = ["girl", "boy"]
TRAITS = ["careful", "curious", "brave", "patient", "smart"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    cause: str
    pilot: str
    pilot_gender: str
    helper: str
    helper_gender: str
    trait: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, a) for s in SETTINGS for c in CLUES for a in CAUSES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--pilot")
    ap.add_argument("--pilot-gender", choices=GENDERS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=GENDERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.cause is None or c[2] == args.cause)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, cause = rng.choice(sorted(combos))
    pilot_gender = args.pilot_gender or rng.choice(GENDERS)
    helper_gender = args.helper_gender or ("boy" if pilot_gender == "girl" else "girl")
    pilot = args.pilot or rng.choice(PILOT_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != pilot])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, clue, cause, pilot, pilot_gender, helper, helper_gender, trait, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], CAUSES[params.cause],
                 params.pilot, params.pilot_gender, params.helper, params.helper_gender,
                 params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("importance", cid, clue.importance))
    for aid, cause in CAUSES.items():
        lines.append(asp.fact("cause", aid))
        lines.append(asp.fact("power", aid, cause.power))
    return "\n".join(lines)


ASP_RULES = r"""
solved(C) :- clue(C), importance(C, I), I >= 1.
worthy(A) :- cause(A), power(A, P), P >= 1.
valid(S, C, A) :- setting(S), clue(C), cause(A), solved(C), worthy(A).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp  # noqa: F401
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos() vs ASP")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def asp_all() -> list[tuple[str, str, str]]:
    return asp_valid_combos()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure mystery story that uses the word "intermediate" and includes a clue that is not the final answer.',
        f"Tell a child-friendly story where {f['pilot'].id} and {f['helper'].id} explore {f['setting'].label} and solve a mystery about a missing item.",
        f"Write a story with a space station setting, a clue, and a calm reveal that shows how the item moved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pilot, helper, clue, cause, setting = f["pilot"], f["helper"], f["clue"], f["cause"], f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {pilot.id} and {helper.id}, who explored {setting.label} and solved a mystery together."),
        ("What was the intermediate clue?",
         f"The intermediate clue was {clue.phrase}. It was not the final answer, but it helped them think in the right direction."),
        ("What caused the item to move?",
         f"{cause.reveal_text} That is why the clue ended up where it did."),
        ("How did the story end?",
         f"It ended with the mystery solved and the base calm again. {pilot.id} and {helper.id} reached the launch window with the answer in hand."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?",
         "A clue is a small piece of information that helps solve a mystery. Good clues point you toward the answer."),
        ("What is a mystery?",
         "A mystery is a puzzling problem with something unknown. You solve it by looking carefully and thinking step by step."),
        ("What does intermediate mean?",
         "Intermediate means something in the middle. It is not the first thing and not the final thing."),
        ("What is a space station?",
         "A space station is a place people live and work in space. It usually circles a planet and has rooms for science and sleeping."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moonbase", "badge", "drone", "Mia", "girl", "Bo", "boy", "curious", "mother"),
    StoryParams("orbit", "glove", "wind", "Noah", "boy", "Ada", "girl", "patient", "father"),
    StoryParams("redplanet", "chip", "pet", "Luna", "girl", "Kai", "boy", "smart", "mother"),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_all())} compatible (setting, clue, cause) combos:\n")
        for s, c, a in asp_all():
            print(f"  {s:10} {c:8} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.pilot} & {p.helper}: {p.setting} mystery ({p.clue} -> {p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
