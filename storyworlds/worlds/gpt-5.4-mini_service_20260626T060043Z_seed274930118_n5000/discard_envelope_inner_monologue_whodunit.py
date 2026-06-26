#!/usr/bin/env python3
"""
storyworlds/worlds/discard_envelope_inner_monologue_whodunit.py
===============================================================

A small whodunit-style story world about a discarded envelope, with the
detective's inner monologue carrying the clues forward.

Seed tale premise:
- A child notices an envelope has gone missing during cleanup.
- The child wonders who discarded it, follows the clues, and finds the truth.
- The ending proves the change: the envelope is rescued, the mistake is named,
  and the mystery is solved without turning mean.

The world keeps the classical small-simulation shape used by the Storyweavers
repo: entities have meters and memes, events mutate state, and the prose is
rendered from that state rather than from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "brother", "grandfather"}
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
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_discard(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("discarding", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.held_by != actor.id:
                continue
            sig = ("discard", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.held_by = None
            item.place = "bin"
            item.meters["lost"] = 1.0
            out.append(f"{actor.id} dropped {item.label} into the bin.")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    envelope = world.entities.get("envelope")
    if not envelope or envelope.place != "bin":
        return out
    sig = ("alarm", envelope.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for actor in world.characters():
        if actor.type == "girl":
            actor.memes["concern"] = actor.memes.get("concern", 0.0) + 1
    out.append("Mina felt a little jolt in her chest; that envelope did not belong in the bin.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("discard", "physical", _r_discard),
    Rule("alarm", "social", _r_alarm),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_discard(world: World, actor: Entity, item_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["discarding"] = 1.0
    propagate(sim, narrate=False)
    item = sim.entities[item_id]
    return item.place == "bin"


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def setting_detail(setting: Setting) -> str:
    return {
        "study": "The little study was tidy, with a desk, a lamp, and one open bin by the door.",
        "kitchen": "The kitchen was warm and bright, and the trash pail waited under the sink.",
        "hallway": "The hallway was narrow, with shoes lined up and a basket of mail on the shelf.",
    }[setting.place]


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str = "Mina",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, traits=["curious", "careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    sibling = world.add(Entity(id="Sibling", kind="character", type="brother", label="the brother"))
    envelope = world.add(Entity(
        id="envelope", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, place="desk", meters={"clean": 1.0}
    ))

    hero.memes["doubt"] = 0.0
    hero.memes["curiosity"] = 1.0

    world.say(f"{hero.id} was a curious little detective who liked noticing small things.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because every clue seemed to have a shape.")
    world.say(f"One afternoon, {hero.id} found a {prize_cfg.label} on the desk and kept it safe.")
    world.say(setting_detail(setting))

    world.para()
    world.say(f"{sibling.id} was clearing the table, and {sibling.pronoun()} thought the envelope looked like trash.")
    world.say(f"{hero.id} noticed {sibling.pronoun('possessive')} hand reaching for it and frowned inside {hero.pronoun('possessive')} head.")
    world.say(f'Mina thought, "That does not feel right. People do not leave a sealed envelope in the bin on purpose."')
    world.say(f"{hero.id} wanted to {activity.verb}, but first {hero.pronoun()} needed to solve the tiny mystery.")

    world.para()
    world.say(f"{hero.id} watched the desk, the bin, and {sibling.pronoun('possessive')} pockets.")
    if predict_discard(world, sibling, "envelope"):
        world.say(f'Mina thought, "If the envelope gets discarded, the message inside will be lost."')
    world.get("Sibling").meters["discarding"] = 1.0
    propagate(world, narrate=True)

    world.say(f"{hero.id} asked, " + f"'" + f"Did you mean to throw that away?" + f"'")
    world.say(f"{sibling.id} blushed and said it looked like an empty scrap of paper.")
    world.say(f"Mina looked again and noticed the neat seal, the return address, and a tiny pencil mark near the corner.")

    world.para()
    world.say(f'Mina thought, "A real scrap would not have a seal. Someone important sent this."')
    world.say(f"{hero.id} reached into the bin, lifted out the envelope, and set it on the desk like precious evidence.")
    world.say(f"{parent.id} smiled when the message was found, because it was an invitation for a supper party.")
    world.say(f"{sibling.id} apologized, and {hero.id} answered kindly that accidents can happen during cleanup.")

    world.para()
    world.say(f"In the end, the envelope was safe on the desk, not discarded.")
    world.say(f"{hero.id} still felt like a detective, but now the mystery was solved and the room felt lighter.")

    world.facts.update(
        hero=hero,
        parent=parent,
        sibling=sibling,
        envelope=envelope,
        activity=activity,
        setting=setting,
        prize_cfg=prize_cfg,
        resolved=True,
        discarded=False,
    )
    return world


SETTINGS = {
    "study": Setting(place="study", indoor=True, affords={"sorting"}),
    "kitchen": Setting(place="kitchen", indoor=True, affords={"sorting"}),
    "hallway": Setting(place="hallway", indoor=True, affords={"sorting"}),
}

ACTIVITIES = {
    "sorting": Activity(
        id="sorting",
        verb="sort the papers",
        gerund="sorting papers",
        rush="grab the wrong stack",
        mess="discarded",
        soil="thrown away",
        zone={"desk", "bin"},
        keyword="envelope",
        tags={"paper", "mail", "clue"},
    ),
}

PRIZES = {
    "envelope": Prize(
        label="envelope",
        phrase="a sealed envelope with a neat return address",
        type="envelope",
        region="desk",
    ),
}

GEAR = [
    Gear(
        id="evidence_tray",
        label="an evidence tray",
        covers={"desk"},
        guards={"discarded"},
        prep="put it in an evidence tray first",
        tail="moved the envelope to the evidence tray",
    )
]

GIRL_NAMES = ["Mina", "Nora", "Lina", "Ivy", "Tess"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Finn", "Theo"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and choose_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about an {f["prize_cfg"].label} that might get discarded.',
        f'Tell a mystery story where {f["hero"].id} uses inner monologue to notice who almost threw away the envelope.',
        f'Write a gentle detective tale with clues, a mistaken discard, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    envelope = f["envelope"]
    return [
        QAItem(
            question=f"What was the missing thing in the story?",
            answer=f"It was the envelope. Mina noticed it might get discarded during cleanup, so she watched it closely.",
        ),
        QAItem(
            question=f"Who almost threw the envelope away?",
            answer=f"{sibling.id} almost threw it away while clearing the table, because it looked like scrap at first.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} used careful looking and inner monologue, noticed the seal and return address, and pulled the envelope out of the bin.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The envelope stayed safe on the desk instead of being discarded, and the mistake was fixed kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an envelope?",
            answer="An envelope is a paper cover that holds a letter or card inside it.",
        ),
        QAItem(
            question="What does discard mean?",
            answer="To discard something means to throw it away or set it aside as not wanted.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.place:
            bits.append(f"place={e.place}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="study", activity="sorting", prize="envelope", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="hallway", activity="sorting", prize="envelope", name="Nora", gender="girl", parent="father"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the activity {activity.id} does not make {prize.label} risk being discarded in a believable way.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about a discarded envelope and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and choose_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), prize_region(P, R).
has_fix(A, P) :- prize_at_risk(A, P), gear_covers(G, R), zone(A, R), gear_guards(G, M), mess_of(A, M).
valid(Place, A, P) :- afford(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("gear_covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("gear_guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
