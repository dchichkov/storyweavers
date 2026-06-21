#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/military_reconciliation_bad_ending_detective_story.py
====================================================================================

A small standalone storyworld in a detective-story style about a military case,
a hard reconciliation, and a bad ending.

Premise:
- A careful detective and a military liaison investigate a missing radio and a
  broken message.
- The case turns on pride, duty, and a chance to make peace.
- Reconciliation is possible, but the ending stays bad because the damage has
  already spread too far.

The world model uses typed entities with physical meters and emotional memes.
State changes drive the prose: clues are found, trust shifts, a warning is
ignored, and a final loss closes the case.

This script follows the shared Storyweavers contract:
- uses storyworlds.results eagerly
- imports storyworlds.asp lazily in ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
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
TRUST_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    rank: str = ""
    faction: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "sister"}
        male = {"man", "boy", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    clue: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    risk: int
    severity: int
    setup: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    effect: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    scene: str
    conflict: str
    resolution: str
    detective: str
    detective_gender: str
    officer: str
    officer_gender: str
    seed: Optional[int] = None


SCENES = {
    "depot": Scene(
        id="depot",
        place="the supply depot",
        mood="dim and echoing",
        clue="a torn map page on a metal desk",
        detail="The hall smelled like dust, oil, and old boots.",
        tags={"military", "depot", "map"},
    ),
    "gate": Scene(
        id="gate",
        place="the barracks gate",
        mood="windy and gray",
        clue="a dented radio on the ground",
        detail="The chain-link gate rattled in the wind like loose teeth.",
        tags={"military", "gate", "radio"},
    ),
    "yard": Scene(
        id="yard",
        place="the drill yard",
        mood="quiet and tense",
        clue="muddy footprints by the fence",
        detail="Boots had stamped the dirt into hard, wet shapes.",
        tags={"military", "yard", "boots"},
    ),
}

CONFLICTS = {
    "missing_radio": Conflict(
        id="missing_radio",
        risk=2,
        severity=2,
        setup="someone had hidden a field radio",
        consequence="the unit could not hear the warning in time",
        tags={"radio", "warning"},
    ),
    "broken_signal": Conflict(
        id="broken_signal",
        risk=3,
        severity=3,
        setup="a critical message had been cut off",
        consequence="the patrol walked into danger blind",
        tags={"signal", "warning"},
    ),
    "wrong_order": Conflict(
        id="wrong_order",
        risk=4,
        severity=4,
        setup="an old order had been passed along by mistake",
        consequence="the team marched the wrong way and lost daylight",
        tags={"order", "march"},
    ),
}

RESOLUTIONS = {
    "apology": Resolution(
        id="apology",
        sense=3,
        effect=2,
        text="sat down with the other side and spoke calmly until the room went still",
        fail="tried to calm everyone down, but the anger was already too hot",
        qa_text="sat down and spoke calmly until the room went still",
        tags={"reconciliation"},
    ),
    "return": Resolution(
        id="return",
        sense=3,
        effect=3,
        text="returned the missing radio and admitted the mistake out loud",
        fail="returned the radio, but the damage had already spread too far",
        qa_text="returned the missing radio and admitted the mistake",
        tags={"reconciliation"},
    ),
    "meeting": Resolution(
        id="meeting",
        sense=2,
        effect=2,
        text="called a small meeting and let both sides say what hurt",
        fail="called a meeting, but nobody was ready to listen",
        qa_text="called a small meeting and let both sides speak",
        tags={"reconciliation"},
    ),
    "coverup": Resolution(
        id="coverup",
        sense=1,
        effect=1,
        text="hid the problem under a cloth and hoped nobody noticed",
        fail="hid the problem for a little while",
        qa_text="hid the problem and hoped nobody noticed",
        tags={"bad"},
    ),
}

DETECTIVE_NAMES = ["Nora", "Mina", "Theo", "June", "Eli", "Iris", "Sam", "Leah"]
OFFICER_NAMES = ["Captain Hart", "Sergeant Vale", "Lieutenant Rowan", "Major Finn"]
TRAITS = ["patient", "sharp-eyed", "careful", "steady", "kind", "stern"]


def hazard_at_risk(scene: Scene, conflict: Conflict) -> bool:
    return "military" in scene.tags and conflict.risk >= 2


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= 2]


def best_resolution() -> Resolution:
    return max(RESOLUTIONS.values(), key=lambda r: r.sense)


def can_reconcile(trust: float, conflict: Conflict) -> bool:
    return trust >= TRUST_MIN and conflict.risk <= 3


def can_still_fail(scene: Scene, conflict: Conflict, resolution: Resolution) -> bool:
    return resolution.effect < conflict.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_resolutions():
        return combos
    for s in SCENES:
        for c_id, c in CONFLICTS.items():
            for r_id, r in RESOLUTIONS.items():
                if hazard_at_risk(SCENES[s], c) and r.sense >= 2:
                    combos.append((s, c_id, r_id))
    return combos


def r_clue(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["found"] < THRESHOLD:
            continue
        sig = ("clue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("detective").memes["curiosity"] += 1
        out.append("__clue__")
    return out


def r_pressure(world: World) -> list[str]:
    out: list[str] = []
    if world.get("officer").memes["shame"] >= THRESHOLD and world.get("detective").memes["curiosity"] >= THRESHOLD:
        sig = ("pressure",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("officer").meters["pressure"] += 1
            out.append("__pressure__")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [r_clue, r_pressure]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_failure(world: World, conflict: Conflict, resolution: Resolution) -> dict:
    sim = world.copy()
    sim.get("case").meters["damaged"] += 1
    return {
        "bad": can_still_fail(SCENES[world.facts["scene_id"]], conflict, resolution),
        "pressure": sim.get("officer").meters["pressure"],
    }


def introduce(world: World, detective: Entity, officer: Entity, scene: Scene) -> None:
    world.say(
        f"{detective.id} was a {detective.pronoun('subject')} detective, the kind who "
        f"noticed small things others missed."
    )
    world.say(
        f"One evening, {detective.id} and {officer.id} met at {scene.place}. "
        f"{scene.detail}"
    )
    world.say(f"They found {scene.clue}.")


def set_case(world: World, conflict: Conflict) -> None:
    case = world.add(Entity(id="case", kind="thing", type="thing", label="the case"))
    case.meters["found"] += 1
    world.say(
        f"The clue pointed to a hard case: {conflict.setup}, and that meant {conflict.consequence}."
    )


def warn(world: World, detective: Entity, officer: Entity, conflict: Conflict) -> None:
    detective.memes["doubt"] += 1
    world.say(
        f"{detective.id} looked at {officer.id} and said the missing piece could hurt everyone if nobody spoke soon."
    )
    officer.memes["shame"] += 1
    world.say(
        f"{officer.id} stared at the floor. {officer.pronoun('subject').capitalize()} already knew the military rules had been bent."
    )


def reconcile(world: World, detective: Entity, officer: Entity, resolution: Resolution) -> None:
    detective.memes["trust"] += 1
    officer.memes["trust"] += 1
    world.say(
        f"At last, {detective.id} and {officer.id} chose peace. {officer.id} {resolution.text}."
    )
    world.say(
        f"For a moment, the room felt softer, as if the long tense night might finally end well."
    )


def bad_ending(world: World, conflict: Conflict) -> None:
    world.get("case").meters["damaged"] += 1
    world.get("officer").memes["loss"] += 1
    world.get("detective").memes["regret"] += 1
    world.say(
        f"But the bad part had already happened: {conflict.consequence}, and the evidence was gone."
    )
    world.say(
        "By morning, the apology still mattered, but it could not fix the broken trail or bring back the lost time."
    )


def tell(scene: Scene, conflict: Conflict, resolution: Resolution,
         detective_name: str = "Nora", detective_gender: str = "girl",
         officer_name: str = "Captain Hart", officer_gender: str = "man",
         trait: str = "careful", trust: int = 2, delay: int = 1) -> World:
    world = World()
    det = world.add(Entity(
        id=detective_name, kind="character", type=detective_gender,
        role="detective", traits=[trait], rank="detective"
    ))
    officer = world.add(Entity(
        id=officer_name, kind="character", type=officer_gender,
        role="officer", traits=["military"], rank="officer", faction="military"
    ))
    world.facts["scene_id"] = scene.id
    world.facts["conflict_id"] = conflict.id
    world.facts["resolution_id"] = resolution.id
    world.facts["trust"] = trust
    world.facts["delay"] = delay

    intro = (
        f"The case began in {scene.place}, where everything felt {scene.mood}."
        f" {scene.detail}"
    )
    world.say(intro)
    introduce(world, det, officer, scene)
    world.para()
    set_case(world, conflict)
    warn(world, det, officer, conflict)

    if can_reconcile(trust, conflict):
        world.para()
        reconcile(world, det, officer, resolution)
        if can_still_fail(scene, conflict, resolution):
            world.para()
            bad_ending(world, conflict)
        else:
            world.say("The case ended cleanly.")
    else:
        world.para()
        world.say(
            f"{officer.id} would not listen, and the chance to reconcile slipped away."
        )
        bad_ending(world, conflict)

    world.facts.update(
        detective=det,
        officer=officer,
        scene=scene,
        conflict=conflict,
        resolution=resolution,
        outcome="bad",
        reconciled=can_reconcile(trust, conflict),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    conflict = f["conflict"]
    return [
        f'Write a detective story for a child set at {scene.place} that includes the word "military".',
        f"Tell a short mystery where a detective uncovers {conflict.setup} and tries to make peace with a military officer.",
        f"Write a story with reconciliation, but keep the ending bad because the damage is already too late to undo.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, officer = f["detective"], f["officer"]
    conflict, resolution, scene = f["conflict"], f["resolution"], f["scene"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {det.id}, a detective, and {officer.id}, a military officer. They work through a hard case together.",
        ),
        QAItem(
            question="What clue started the case?",
            answer=f"The case started with {scene.clue}. That clue led them toward {conflict.setup}.",
        ),
        QAItem(
            question="Did the detective and the officer make peace?",
            answer=f"Yes. They tried {resolution.qa_text}, and that was the reconciliation part of the story.",
        ),
        QAItem(
            question="Why is the ending bad?",
            answer=f"The ending is bad because {conflict.consequence}, and the loss could not be taken back. Even after they made peace, the damage was already done.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery by paying attention to small details.",
        ),
        QAItem(
            question="What is the military?",
            answer="The military is a group of people who work together to defend a country and follow strict rules and orders.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset or divided try to make peace and understand each other again.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things do not turn out well, even if the characters tried hard to fix the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.rank:
            bits.append(f"rank={e.rank}")
        if e.faction:
            bits.append(f"faction={e.faction}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="depot", conflict="missing_radio", resolution="return",
                detective="Nora", detective_gender="girl",
                officer="Captain Hart", officer_gender="man", trait="careful",
                seed=7),
    StoryParams(scene="gate", conflict="broken_signal", resolution="apology",
                detective="Theo", detective_gender="boy",
                officer="Sergeant Vale", officer_gender="man", trait="steady",
                seed=8),
    StoryParams(scene="yard", conflict="wrong_order", resolution="meeting",
                detective="Iris", detective_gender="girl",
                officer="Major Finn", officer_gender="man", trait="sharp-eyed",
                seed=9),
]


def explain_rejection(scene: Scene, conflict: Conflict) -> str:
    return f"(No story: this scene and conflict do not make a reasonable military mystery.)"


def explain_resolution(rid: str) -> str:
    r = RESOLUTIONS[rid]
    return f"(Refusing resolution '{rid}': it scores too low on common sense.)"


ASP_RULES = r"""
hazard(S,C) :- scene(S), conflict(C), military_scene(S), risk(C,R), R >= 2.
sensible(R) :- resolution(R), sense(R,S), S >= 2.
valid(S,C,R) :- hazard(S,C), sensible(R).
reconciled :- trust(T), T >= 2, conflict_risk(C,R), R <= 3.
bad_ending :- reconciled.
bad_ending :- not reconciled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("military_scene", sid))
    for cid, c in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("risk", cid, c.risk))
        lines.append(asp.fact("conflict_risk", cid, c.risk))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_resolutions()}:
        print("OK: sensible resolution list matches.")
    else:
        print("MISMATCH in sensible resolutions.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            scene=None, conflict=None, resolution=None, detective=None,
            detective_gender=None, officer=None, officer_gender=None, n=1,
            seed=123, all=False, trace=False, qa=False, json=False, asp=False,
            verify=False, show_asp=False
        ), random.Random(123)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style military reconciliation storyworld with a bad ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--detective", choices=DETECTIVE_NAMES)
    ap.add_argument("--detective-gender", choices=["woman", "girl", "man", "boy"])
    ap.add_argument("--officer", choices=OFFICER_NAMES)
    ap.add_argument("--officer-gender", choices=["woman", "girl", "man", "boy"])
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
    if args.resolution and RESOLUTIONS[args.resolution].sense < 2:
        raise StoryError(explain_resolution(args.resolution))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.conflict is None or c[1] == args.conflict)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, conflict, resolution = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    officer = args.officer or rng.choice(OFFICER_NAMES)
    return StoryParams(
        scene=scene,
        conflict=conflict,
        resolution=resolution,
        detective=detective,
        detective_gender=args.detective_gender or rng.choice(["woman", "girl", "man", "boy"]),
        officer_gender=args.officer_gender or rng.choice(["man", "woman"]),
        officer=officer,
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.conflict not in CONFLICTS or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid StoryParams values.")
    world = tell(SCENES[params.scene], CONFLICTS[params.conflict], RESOLUTIONS[params.resolution],
                 detective_name=params.detective, detective_gender=params.detective_gender,
                 officer_name=params.officer, officer_gender=params.officer_gender,
                 trait=params.trait)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible resolutions: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print(row)
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
            header = f"### {p.detective} vs {p.officer} ({p.scene}, {p.conflict}, {p.resolution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
