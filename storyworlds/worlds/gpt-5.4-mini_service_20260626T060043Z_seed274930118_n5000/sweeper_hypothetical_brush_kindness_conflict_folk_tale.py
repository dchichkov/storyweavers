#!/usr/bin/env python3
"""
storyworlds/worlds/sweeper_hypothetical_brush_kindness_conflict_folk_tale.py
============================================================================

A small folk-tale storyworld about a village sweeper, a hypothetical problem,
a brush, and the tug between Kindness and Conflict.

Premise:
- A village sweeper cares for a shared path, using a stout brush.
- A small doubt appears: what if the brush is lost, or what if the road is
  too dusty for one person to manage alone?
- Kindness offers a way forward; Conflict argues for pride, blame, and hurry.
- The story resolves when help is accepted and the path is made bright again.

This script follows the Storyweavers contract:
- standalone stdlib world script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- optional QA, JSON, trace, ASP, and verification modes
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "daughter"}
        male = {"boy", "man", "father", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    helps: set[str]
    plural: bool = False


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _entity_mood(e: Entity, key: str) -> float:
    return float(e.memes.get(key, 0.0))


def _do_sweep(world: World, sweeper: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"The place {world.setting.place} does not support sweeping.")
    sweeper.meters["dust"] = max(0.0, sweeper.meters.get("dust", 0.0) - 1.0)
    sweeper.memes["duty"] = sweeper.memes.get("duty", 0.0) + 1.0
    if narrate:
        world.say(f"{sweeper.label} swept the path with steady strokes.")
    _propagate(world, narrate=narrate)


def _r_shared_burden(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("dust", 0.0) >= THRESHOLD and ent.memes.get("help_offered", 0.0) >= THRESHOLD:
            sig = ("shared_burden", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1.0
            out.append(f"With help beside {ent.pronoun('object')}, the load felt lighter.")
    return out


def _r_conflict_softens(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("conflict", 0.0) >= THRESHOLD and ent.memes.get("kindness", 0.0) >= THRESHOLD:
            sig = ("soften", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["conflict"] = 0.0
            ent.memes["peace"] = ent.memes.get("peace", 0.0) + 1.0
            out.append(f"The sharp words fell quiet, like pebbles sinking into a pond.")
    return out


def _r_brush_found(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.entities.get("keeper")
    brush = world.entities.get("brush")
    if not keeper or not brush:
        return out
    if keeper.memes.get("searching", 0.0) < THRESHOLD:
        return out
    if brush.carried_by == keeper.id:
        sig = ("found", brush.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        keeper.memes["relief"] = keeper.memes.get("relief", 0.0) + 1.0
        out.append(f"The brush was safe after all, tucked where careful hands had left it.")
    return out


CAUSAL_RULES = [
    Rule("shared_burden", _r_shared_burden),
    Rule("conflict_softens", _r_conflict_softens),
    Rule("brush_found", _r_brush_found),
]


def _propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def conclude_kindness(world: World, sweeper: Entity, helper: Entity, brush: Entity) -> None:
    sweeper.memes["kindness"] = sweeper.memes.get("kindness", 0.0) + 1.0
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    helper.memes["help_offered"] = helper.memes.get("help_offered", 0.0) + 1.0
    world.say(
        f"{helper.label} brought a kind hand and offered to help."
    )
    _propagate(world, narrate=True)
    world.say(
        f"Together they used the {brush.label} until the lane shone clean and bright."
    )


def tell(setting: Setting, activity: Activity, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    sweeper = world.add(Entity(
        id="sweeper",
        kind="character",
        type="man",
        label=hero_name,
        traits=["steady", "kind"],
        meters={"dust": 1.0},
        memes={"kindness": 1.0, "searching": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="woman",
        label=helper_name,
        traits=["gentle", "brave"],
        memes={"kindness": 0.0, "help_offered": 0.0, "conflict": 0.0},
    ))
    brush = world.add(Entity(
        id="brush",
        kind="thing",
        type="brush",
        label="brush",
        phrase="a stout brush with a wooden handle",
        owner=sweeper.id,
        carried_by=sweeper.id,
    ))

    world.say(
        f"In a village at the edge of the woods, {sweeper.label} kept the shared lane neat with a stout brush."
    )
    world.say(
        f"{sweeper.label} had a good heart, and {helper.label} trusted that heart."
    )

    world.para()
    world.say(
        f"One morning, a hypothetical worry stepped into the sun: what if the brush went missing, and what if the lane stayed dusty?"
    )
    sweeper.memes["searching"] = 1.0
    sweeper.memes["conflict"] = 1.0
    world.say(
        f"{sweeper.label} grew worried and began to search."
    )
    if activity.id == "sweep":
        _do_sweep(world, sweeper, activity, narrate=True)

    world.para()
    world.say(
        f"Then the helper remembered the old lesson of kindness: one pair of hands can do much, but two can do more."
    )
    conclude_kindness(world, sweeper, helper, brush)

    world.facts.update(
        sweeper=sweeper,
        helper=helper,
        brush=brush,
        activity=activity,
        setting=setting,
    )
    return world


SETTINGS = {
    "village": Setting(place="the village lane", indoor=False, affords={"sweep"}),
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"sweep"}),
    "threshold": Setting(place="the cottage threshold", indoor=False, affords={"sweep"}),
}

ACTIVITIES = {
    "sweep": Activity(
        id="sweep",
        verb="sweep the lane",
        gerund="sweeping the lane",
        rush="rush to sweep",
        mess="dust",
        soil="dusty",
        keyword="brush",
        tags={"brush", "dust", "kindness", "conflict"},
    ),
}

TOOLS = {
    "brush": Tool(
        id="brush",
        label="brush",
        phrase="a stout brush with a wooden handle",
        guards={"dust"},
        helps={"sweep"},
    )
}

NAMES = ["Mara", "Anya", "Bela", "Sorin", "Ivo", "Toma", "Nia", "Elin"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sweeper = f["sweeper"]
    helper = f["helper"]
    return [
        f"Write a short folk tale about {sweeper.label}, a village sweeper, and a brush that must not be lost.",
        f"Tell a gentle story where {sweeper.label} worries about a hypothetical problem, and {helper.label} answers with kindness.",
        "Write a child-friendly story about duty, worry, and a kind helper who makes a dusty lane bright again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sweeper = f["sweeper"]
    helper = f["helper"]
    brush = f["brush"]
    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {sweeper.label}, the village sweeper, and {helper.label}, who helps with kindness.",
        ),
        QAItem(
            question=f"What did {sweeper.label} carry for the work?",
            answer=f"{sweeper.label} carried a stout brush for sweeping the lane.",
        ),
        QAItem(
            question=f"What was the hypothetical worry in the middle of the story?",
            answer=f"The worry was that the brush might be lost and the lane might stay dusty.",
        ),
        QAItem(
            question=f"What helped end the conflict?",
            answer=f"Kindness ended the conflict, because {helper.label} offered help instead of blame.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, the lane was clean and bright, and the brush was safe again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brush used for?",
            answer="A brush is used to sweep, scrub, or smooth things by moving its bristles over a surface.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, care, and speak gently instead of hurting or blaming.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when people want different things or feel upset with each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            out.append((place, act_id))
    return out


def explain_rejection(place: str, activity: str) -> str:
    return f"(No story: {place} does not support {activity}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(f"Unknown place: {args.place}")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {args.activity}")

    combos = [
        (p, a) for p, a in valid_combos()
        if (args.place is None or args.place == p)
        and (args.activity is None or args.activity == a)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, activity=activity, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.helper)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a sweeper, a brush, kindness, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- activity(A).
tool(T) :- tool(T).

valid(P,A) :- affords(P,A).

#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import per contract
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for tag in sorted(a.tags):
            lines.append(asp.fact("tag", aid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", tid, m))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for p, a in combos:
            print(f"  {p:12} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, name="Mara", helper="Anya")) for p, a in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {sample.params.name}: {sample.params.activity} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
