#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lodge_conflict_mystery_to_solve_moral_value.py
===============================================================================

A standalone storyworld about a small space-adventure lodge mystery:
the crew arrives at a snowy lodge base, a shared tool goes missing, the crew
argues over blame, they solve the mystery by following clues, and the ending
lands on a moral value: honesty and fairness beat suspicion.

The world uses a tiny simulation with typed entities, physical meters, emotional
memes, a forward causal pass, a reasonableness gate, and an inline ASP twin.
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
VALUE_TRUST = "trust"
VALUE_HONESTY = "honesty"
VALUE_FAIRNESS = "fairness"


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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "engineer"}
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
    detail: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue1: str
    clue2: str
    clue3: str
    found_where: str
    culprit: str
    is_misunderstanding: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    accusation: str
    blame_target: str
    calming_phrase: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    lesson: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    conflict: str
    value: str
    crew_a: str
    crew_a_type: str
    crew_b: str
    crew_b_type: str
    leader: str
    leader_type: str
    seed: Optional[int] = None


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["accusation"] >= THRESHOLD and ("tension", e.id) not in world.fired:
            world.fired.add(("tension", e.id))
            e.memes["hurt"] += 1
            out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)


def mystery_risk(mystery: Mystery) -> bool:
    return mystery.is_misunderstanding


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for cid, conflict in CONFLICTS.items():
                if mystery_risk(mystery) and conflict.severity >= 1 and setting.id in {"lodge", "ice_lodge"}:
                    combos.append((sid, mid, cid))
    return combos


def _clue_chain(world: World, mystery: Mystery) -> None:
    world.say(
        f"In the {world.get('setting').label_word}, the crew found a small mystery: "
        f"{mystery.missing} was gone, and the cold air hummed like a faraway engine."
    )
    world.say(
        f"Near the bunk room, {mystery.clue1}, {mystery.clue2}, and {mystery.clue3}."
    )


def _argument(world: World, a: Entity, b: Entity, conflict: Conflict) -> None:
    a.meters["accusation"] += 1
    b.meters["accusation"] += 1
    a.memes["doubt"] += 1
    b.memes["doubt"] += 1
    world.get("room").meters["noise"] += 1
    world.say(
        f'{a.id} pointed at {conflict.blame_target} and said, "{conflict.accusation}"'
        f" Then {b.id} crossed {b.pronoun('possessive')} arms, because nobody liked being blamed."
    )


def _steady(world: World, leader: Entity, a: Entity, b: Entity, conflict: Conflict) -> None:
    leader.memes["calm"] += 1
    world.say(
        f"{leader.id} raised a hand and spoke softly. \"{conflict.calming_phrase}\""
    )
    world.say(
        f"{leader.id} asked them to look for clues instead of guessing. That made the room quieter."
    )


def _solve(world: World, mystery: Mystery, leader: Entity) -> None:
    mystery_ent = world.get("missing")
    mystery_ent.meters["found"] = 1
    world.get("room").meters["noise"] = 0
    leader.memes["pride"] += 1
    world.say(
        f"Together they followed the clues to {mystery.found_where}, where the missing tool waited."
    )
    world.say(
        f"It had not been stolen at all. {mystery.culprit} had moved it there to keep it warm and dry."
    )


def _moral(world: World, value: MoralValue, leader: Entity, a: Entity, b: Entity) -> None:
    for e in (leader, a, b):
        e.memes["trust"] += 1
        e.memes["shame"] = 0
    world.say(
        f"{leader.id} smiled and said, \"{value.lesson}\""
    )
    world.say(value.closing_image)


def tell(setting: Setting, mystery: Mystery, conflict: Conflict, value: MoralValue,
         crew_a: str, crew_a_type: str, crew_b: str, crew_b_type: str,
         leader: str, leader_type: str) -> World:
    world = World()
    a = world.add(Entity(id=crew_a, kind="character", type=crew_a_type, role="crew"))
    b = world.add(Entity(id=crew_b, kind="character", type=crew_b_type, role="crew"))
    l = world.add(Entity(id=leader, kind="character", type=leader_type, role="leader"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="setting", type="place", label=setting.place, attrs={"detail": setting.detail}, tags=set(setting.tags)))
    world.add(Entity(id="missing", type="thing", label=mystery.missing, tags=set(mystery.tags)))
    world.facts.update(setting=setting, mystery=mystery, conflict=conflict, value=value)

    world.say(
        f"The {setting.place} lodge sat under a bright field of stars, its windows glowing gold against the snow."
    )
    world.say(
        f"{a.id} and {b.id} arrived with {l.id} after a long space flight, and the wind outside sounded like tiny rockets."
    )
    _clue_chain(world, mystery)

    world.para()
    _argument(world, a, b, conflict)
    _steady(world, l, a, b, conflict)

    world.para()
    _solve(world, mystery, l)
    _moral(world, value, l, a, b)
    return world


SETTINGS = {
    "lodge": Setting(
        id="lodge",
        place="lodge",
        detail="a warm lodge on an ice moon",
        mood="cozy",
        tags={"lodge", "space", "snow"},
    ),
    "ice_lodge": Setting(
        id="ice_lodge",
        place="ice lodge",
        detail="a small ice lodge beside a landing pad",
        mood="cold",
        tags={"lodge", "space", "ice"},
    ),
}

MYSTERIES = {
    "missing_map": Mystery(
        id="missing_map",
        missing="the star map",
        clue1="a boot print led toward the heater",
        clue2="a folded corner showed a name tag",
        clue3="a little trail of snow melted near the bench",
        found_where="the coat rack",
        culprit="the wind",
        tags={"map", "clue", "lodge"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="the cabin key",
        clue1="silver dust glittered by the desk",
        clue2="a note fluttered under a mug",
        clue3="the key-shaped mark pointed to the shelf",
        found_where="the shelf by the window",
        culprit="the caretaker",
        tags={"key", "clue", "lodge"},
    ),
}

CONFLICTS = {
    "blame": Conflict(
        id="blame",
        accusation="You took it!",
        blame_target="the quiet corner",
        calming_phrase="Maybe the answer is hiding in the clues.",
        severity=2,
        tags={"argument", "blame"},
    ),
    "accuse_wind": Conflict(
        id="accuse_wind",
        accusation="The storm stole it!",
        blame_target="the snowy door",
        calming_phrase="Let's not blame the storm before we look.",
        severity=1,
        tags={"argument", "storm"},
    ),
}

VALUES = {
    "honesty": MoralValue(
        id="honesty",
        lesson="Honesty helps more than guessing.",
        closing_image="By the end, the crew stood together by the window, glad they had told the truth and found the tool.",
        tags={"honesty"},
    ),
    "fairness": MoralValue(
        id="fairness",
        lesson="Fairness means listening before deciding who is at fault.",
        closing_image="By the end, the crew shared a warm drink and looked at the same clues, one by one.",
        tags={"fairness"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-lodge mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--crew-a")
    ap.add_argument("--crew-a-type", choices=["girl", "boy"])
    ap.add_argument("--crew-b")
    ap.add_argument("--crew-b-type", choices=["girl", "boy"])
    ap.add_argument("--leader")
    ap.add_argument("--leader-type", choices=["girl", "boy", "captain", "engineer"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.conflict and args.conflict not in CONFLICTS:
        raise StoryError("Unknown conflict.")
    if args.value and args.value not in VALUES:
        raise StoryError("Unknown moral value.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, conflict = rng.choice(sorted(combos))
    value = args.value or rng.choice(sorted(VALUES))
    crew_a = args.crew_a or rng.choice(["Ari", "Nova", "Milo", "Jin"])
    crew_b = args.crew_b or rng.choice(["Bea", "Pax", "Luz", "Tess"])
    leader = args.leader or rng.choice(["Captain Sol", "Engineer Ray", "Commander Ivo"])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        conflict=conflict,
        value=value,
        crew_a=crew_a,
        crew_a_type=args.crew_a_type or rng.choice(["girl", "boy"]),
        crew_b=crew_b,
        crew_b_type=args.crew_b_type or rng.choice(["girl", "boy"]),
        leader=leader,
        leader_type=args.leader_type or rng.choice(["captain", "engineer"]),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mystery = MYSTERIES[params.mystery]
        conflict = CONFLICTS[params.conflict]
        value = VALUES[params.value]
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc.args[0]}") from exc
    world = tell(setting, mystery, conflict, value,
                 params.crew_a, params.crew_a_type, params.crew_b, params.crew_b_type,
                 params.leader, params.leader_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a space-adventure story set in a lodge where {f['mystery'].missing} goes missing and the crew argues.",
        f"Tell a child-friendly mystery at the lodge that teaches {f['value'].lesson.lower()}",
        f"Write a calm space story with a lodge, clues, and a moral about fairness and honesty.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    m: Mystery = f["mystery"]
    c: Conflict = f["conflict"]
    v: MoralValue = f["value"]
    return [
        ("What was missing?", f"{m.missing} was missing from the lodge."),
        ("Why did the crew argue?", f"They argued because {c.accusation.lower()} and they were not sure who to trust."),
        ("How did they solve the mystery?", f"They followed the clues and found {m.missing} in {m.found_where}. It was not a real theft; {m.culprit} had moved it."),
        ("What moral did the story teach?", f"It taught that {v.lesson.lower()}"),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a lodge?", "A lodge is a cozy building where travelers can sleep and rest, often in a cold place."),
        ("What is a mystery?", "A mystery is a problem where something is unknown, so you look for clues to solve it."),
        ("What is honesty?", "Honesty means telling the truth, even when it feels hard."),
        ("What is fairness?", "Fairness means giving people a fair chance and not blaming them too quickly."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="lodge", mystery="missing_map", conflict="blame", value="honesty",
                crew_a="Ari", crew_a_type="girl", crew_b="Milo", crew_b_type="boy",
                leader="Captain Sol", leader_type="captain"),
    StoryParams(setting="ice_lodge", mystery="missing_key", conflict="accuse_wind", value="fairness",
                crew_a="Nova", crew_a_type="girl", crew_b="Jin", crew_b_type="boy",
                leader="Engineer Ray", leader_type="engineer"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid, c in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("severity", cid, c.severity))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    lines.append(asp.fact("valid_setting", "lodge"))
    lines.append(asp.fact("valid_setting", "ice_lodge"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, C) :- valid_setting(S), mystery(M), conflict(C).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        rc = 1
        print("MISMATCH between ASP and Python.")
        print("ASP only:", sorted(a - p))
        print("Python only:", sorted(p - a))
    else:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_story(sample_params: StoryParams) -> StorySample:
    return generate(sample_params)


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = build_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate_story(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
