#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smith_humidity_elevator_magic_rhyme_conflict_bedtime.py
========================================================================================

A standalone story world for a bedtime tale set in an elevator, with a small
magic-and-rhyme conflict that is soothed by a careful, sensible ending.

The seed words are folded into the world:
- smith: a child character whose name quietly anchors the story
- humidity: a physical condition that makes the elevator air sticky and sleepy
- Magic, Rhyme, Conflict: three narrative instruments that shape the causal turn
- elevator: the single setting
- style: bedtime story

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates story-grounded QA and world-knowledge QA from world state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
MOOD_UPLIFT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    hum: str
    quiet: str


@dataclass
class NameToken:
    id: str
    label: str
    type: str
    gender: str
    role: str
    traits: list[str] = field(default_factory=list)


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    safe: bool = True


@dataclass
class Rhyme:
    id: str
    label: str
    line: str
    calm: int
    charm: bool = True


@dataclass
class ConflictPlan:
    id: str
    spark: str
    worry: str
    resolution: str
    sense: int
    power: int


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.conflict_kind: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.conflict_kind = self.conflict_kind
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sticky_air(world: World) -> list[str]:
    out: list[str] = []
    if world.setting.id != "elevator":
        return out
    for ent in world.entities.values():
        sig = ("sticky_air", ent.id)
        if sig in world.fired:
            continue
        if ent.kind == "character":
            ent.memes["sleepy"] += 1
            ent.meters["humidity"] += 1
            world.fired.add(sig)
            out.append("__ambient__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("conflict_seen"):
        return out
    if world.get("child").memes["frustration"] < THRESHOLD:
        return out
    world.facts["conflict_seen"] = True
    world.get("child").memes["tension"] += 1
    world.get("parent").memes["worry"] += 1
    out.append("__conflict__")
    return out


def _r_rhyme_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("rhyme_used"):
        return out
    if world.get("child").memes["calm"] < THRESHOLD:
        return out
    world.facts["rhyme_used"] = True
    world.get("child").memes["joy"] += 1
    world.get("parent").memes["worry"] = max(0.0, world.get("parent").memes["worry"] - 1)
    out.append("__rhyme__")
    return out


CAUSAL_RULES = [
    Rule("sticky_air", "physical", _r_sticky_air),
    Rule("conflict", "social", _r_conflict),
    Rule("rhyme_calm", "social", _r_rhyme_calm),
]


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


def objection_reason(plan: ConflictPlan, setting: Setting) -> str:
    return (
        f"(No story: the conflict must feel like a bedtime-sized problem in the {setting.place}. "
        f"This plan '{plan.id}' is not reasonable for the seed world.)"
    )


def sensible_plans() -> list[ConflictPlan]:
    return [p for p in PLANS.values() if p.sense >= 2 and p.power >= 1]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for plan_id, plan in PLANS.items():
            for rhyme_id, rhyme in RHYMES.items():
                if plan.sense >= 2 and rhyme.calm >= 1:
                    combos.append((setting_id, plan_id, rhyme_id))
    return combos


def _do_magic(world: World, charm: Charm, rhyme: Rhyme) -> None:
    child = world.get("child")
    child.meters["magic"] += 1
    child.memes["curiosity"] += 1
    child.memes["frustration"] += 1
    world.conflict_kind = world.facts.get("plan").id
    world.say(
        f"In the elevator, {child.id} whispered a little magic spell. "
        f'{charm.label} shimmered, and {rhyme.line}.'
    )
    world.say(
        f"The air felt thick with humidity, like a warm blanket waiting at the end of the day."
    )
    world.say(
        f"But the spell did not settle the feeling inside {child.id}; it only made the want to change the mood grow bigger."
    )


def _warn(world: World, parent: Entity, child: Entity, plan: ConflictPlan) -> None:
    parent.memes["care"] += 1
    world.say(
        f'{parent.id} noticed {child.id} getting fussy. "{plan.worry}," {parent.id} said softly, '
        f'"and bedtime is already close."'
    )


def _argue(world: World, child: Entity, plan: ConflictPlan) -> None:
    child.memes["frustration"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} crossed {child.pronoun("possessive")} arms and answered, '
        f'"{plan.spark}"'
    )


def _repair(world: World, parent: Entity, child: Entity, rhyme: Rhyme, plan: ConflictPlan) -> None:
    child.memes["calm"] += rhyme.calm
    child.memes["frustration"] = max(0.0, child.memes["frustration"] - 1)
    parent.memes["worry"] = max(0.0, parent.memes["worry"] - 1)
    world.say(
        f'{parent.id} took a slow breath and answered with a rhyme: "{rhyme.line}"'
    )
    world.say(
        f"It sounded silly and sweet, and the little conflict loosened its grip."
    )
    world.say(
        f'"{plan.resolution}," {child.id} murmured, now quieter and ready for sleep.'
    )


def _bedtime_finish(world: World, child: Entity, parent: Entity, charm: Charm) -> None:
    child.memes["joy"] += 1
    child.memes["sleepiness"] += 1
    world.say(
        f'{child.id} tucked {child.pronoun("possessive")} hands under the blanket of the evening, '
        f'and the elevator stopped with a gentle ding.'
    )
    world.say(
        f'By then, {child.id} felt calm enough for a yawn. {parent.id} smiled, '
        f'and the magic {charm.label} became just a quiet bedtime story to remember.'
    )


def tell(setting: Setting, name: NameToken, charm: Charm, rhyme: Rhyme, plan: ConflictPlan) -> World:
    world = World(setting)
    child = world.add(Entity(id=name.label, kind="character", type=name.gender, role="child", traits=name.traits))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", role="parent", label="the parent"))
    world.add(Entity(id="elevator", kind="thing", type="room", label="the elevator"))
    world.facts["plan"] = plan

    child.memes["calm"] = 0.0
    child.memes["frustration"] = 0.0
    child.memes["joy"] = 0.0

    world.say(
        f"It was bedtime, and {child.id} rode the elevator with {parent.id}. "
        f"The air had a soft humidity to it, and the metal walls felt sleepy."
    )
    world.say(
        f'{child.id} loved the tiny shine of {charm.label}, because {charm.effect}.'
    )
    world.say(
        f'{child.id} hummed the rhyme {rhyme.label}, a little song that matched the hum of the elevator.'
    )
    world.para()

    _do_magic(world, charm, rhyme)
    _warn(world, parent, child, plan)
    _argue(world, child, plan)
    propagate(world, narrate=False)
    world.say(
        f"The conflict made the elevator feel smaller for a moment, as if the walls were listening."
    )
    world.para()
    _repair(world, parent, child, rhyme, plan)
    _bedtime_finish(world, child, parent, charm)

    world.facts.update(
        child=child, parent=parent, charm=charm, rhyme=rhyme, setting=setting,
        outcome="settled", conflict=True, resolved=True
    )
    return world


SETTINGS = {
    "elevator": Setting("elevator", "the elevator", "humid", "sleepy"),
}

CHILDREN = {
    "smith": NameToken("smith", "smith", "character", "girl", "child", ["small", "curious"]),
    "smitty": NameToken("smitty", "smitty", "character", "boy", "child", ["small", "curious"]),
}

CHARMS = {
    "magic_lamp": Charm("magic_lamp", "magic lamp", "it glowed with a moon-pale light"),
    "magic_key": Charm("magic_key", "magic key", "it looked like it could open any sleepy door"),
}

RHYMES = {
    "soft_bell": Rhyme("soft_bell", "soft bell", "ding-ding, dream in spring", calm=2),
    "night_train": Rhyme("night_train", "night train", "click-clack, worry comes back", calm=1),
}

PLANS = {
    "stuck_door": ConflictPlan("stuck_door", "Open the door!", "That door is not our toy.", "We can wait together.", sense=3, power=2),
    "bounce": ConflictPlan("bounce", "Let's bounce and make it faster!", "This is a waiting game, not a racing game.", "We can breathe and be patient.", sense=2, power=1),
    "shout": ConflictPlan("shout", "Shout louder!", "Inside voices help the elevator stay gentle.", "We can use soft voices now.", sense=1, power=0),
}


@dataclass
class StoryParams:
    setting: str
    child: str
    charm: str
    rhyme: str
    plan: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story set in an elevator that includes the words "smith" and "humidity".',
        f'Tell a quiet story about {f["child"].id} in the elevator where magic and a rhyme lead to a small conflict that gets soothed by a parent.',
        f'Write a child-facing bedtime story where a magic charm, a rhyme, and a conflict all happen in a humid elevator, and the ending feels calm.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, charm, rhyme, plan = f["child"], f["parent"], f["charm"], f["rhyme"], f["plan"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, sharing a bedtime ride in the elevator. The little story stays close to them so it can end calmly."),
        ("Why did the elevator feel sticky and sleepy?",
         f"The air had humidity, so it felt warm and a little heavy. That made the elevator seem like a sleepy room instead of a bright play place."),
        ("What caused the conflict?",
         f"{child.id} used magic and then grew frustrated when the feeling inside did not settle right away. {parent.id} answered carefully because bedtime was close and the best fix was a gentle one."),
        ("How was the conflict solved?",
         f"{parent.id} used a rhyme to calm the moment, and {child.id} listened. The rhyme and the soft voice mattered because they gave the magic a peaceful ending instead of a louder one."),
        ("How did the story end?",
         f"It ended with {child.id} feeling sleepy, calm, and ready for bed. The elevator stopped, and the last image is a quiet yawn instead of an argument."),
    ]
    if f["resolved"]:
        qa.append((
            "What changed by the end?",
            f"{child.id} began with restless energy, but ended with calm in {child.pronoun('possessive')} body. The small conflict became a bedtime feeling, which is why the ending is gentle."
        ))
    return qa


WORLD_KNOWLEDGE = {
    "humidity": [("What is humidity?",
                  "Humidity is water in the air. When there is a lot of it, the air can feel warm, sticky, or heavy.")],
    "elevator": [("What is an elevator?",
                  "An elevator is a box that moves people up and down in a building. It helps people travel between floors.")],
    "magic": [("What does magic mean in a story?",
               "Magic is pretend power in a story. It can make strange or wonderful things happen.")],
    "rhyme": [("What is a rhyme?",
              "A rhyme is when words sound alike at the end, like bell and spell. Rhymes can make a story feel musical.")],
    "conflict": [("What is a conflict in a story?",
                 "A conflict is a problem or disagreement in a story. It is the part that needs care, patience, or a fix.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"humidity", "elevator", "magic", "rhyme", "conflict"}
    out: list[tuple[str, str]] = []
    for tag in ["humidity", "elevator", "magic", "rhyme", "conflict"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for rid, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        lines.append(asp.fact("calm", rid, rhyme.calm))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        lines.append(asp.fact("power", pid, plan.power))
    for chid in CHARMS:
        lines.append(asp.fact("charm", chid))
    lines.append(asp.fact("sense_min", 2))
    lines.append(asp.fact("magic_required", 1))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(P) :- plan(P), sense(P,S), sense_min(M), S >= M.
valid(S, P, R) :- setting(S), plan(P), rhyme(R), sensible(P), calm(R,C), C >= 1.
outcome(settled) :- sensible(P), rhyme(R), calm(R,C), C >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos matches ASP ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        rc = 1

    if set(asp_sensible()) == {p.id for p in sensible_plans()}:
        print("OK: sensible plans match.")
    else:
        print("MISMATCH in sensible plans.")
        rc = 1

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: smith, humidity, elevator, magic, rhyme, conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--plan", choices=PLANS)
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
              and (args.plan is None or c[1] == args.plan)
              and (args.rhyme is None or c[2] == args.rhyme)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, plan, rhyme = rng.choice(sorted(combos))
    child = args.child or rng.choice(sorted(CHILDREN))
    charm = args.charm or rng.choice(sorted(CHARMS))
    return StoryParams(setting=setting, child=child, charm=charm, rhyme=rhyme, plan=plan)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHILDREN[params.child], CHARMS[params.charm], RHYMES[params.rhyme], PLANS[params.plan])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams("elevator", "smith", "magic_lamp", "soft_bell", "stuck_door"),
    StoryParams("elevator", "smitty", "magic_key", "night_train", "bounce"),
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
        print(asp_program(show="#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, p, r in combos:
            print(f"  {s:10} {p:12} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.child}: {p.plan} in the {p.setting} ({p.charm}, {p.rhyme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
