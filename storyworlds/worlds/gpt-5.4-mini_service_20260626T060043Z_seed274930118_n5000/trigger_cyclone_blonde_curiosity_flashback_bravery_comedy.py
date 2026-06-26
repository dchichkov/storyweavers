#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trigger_cyclone_blonde_curiosity_flashback_bravery_comedy.py
==============================================================================================================================

A standalone comedy storyworld about a curious blonde child, a harmless
cyclone-like mess, a remembered lesson, and a brave cleanup.

The world is intentionally tiny:
- one child
- one small setting
- one risky action that stirs a toy cyclone / wind spiral
- one remembered warning
- one brave, funny fix

The core causal question is simple:
Can curiosity trigger the silly cyclone, and can bravery use a remembered trick
to make things right?

The story is built from simulation state, not a frozen paragraph.
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
    wears: Optional[str] = None
    is_trigger: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def was(self) -> str:
        return "were" if self.type in {"children"} else "was"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class TriggerItem:
    id: str
    label: str
    phrase: str
    risk: str
    zone: set[str]
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    calming: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.memes.get("curiosity", 0.0) >= THRESHOLD and child.meters.get("triggered", 0.0) >= THRESHOLD:
            if ("cyclone", child.id) not in world.fired:
                world.fired.add(("cyclone", child.id))
                child.meters["cyclone"] = child.meters.get("cyclone", 0.0) + 1.0
                out.append(f"A silly little cyclone spun up around {child.id}'s feet.")
        if child.meters.get("cyclone", 0.0) >= THRESHOLD and child.memes.get("bravery", 0.0) >= THRESHOLD:
            if ("clean", child.id) not in world.fired:
                world.fired.add(("clean", child.id))
                child.meters["cyclone"] = 0.0
                child.meters["cleanup"] = child.meters.get("cleanup", 0.0) + 1.0
                out.append(f"{child.id} bravely used the remembered trick and calmed the spinning mess.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_cyclone(world: World, child: Entity, trigger: TriggerItem) -> dict:
    sim = world.copy()
    do_trigger(sim, sim.get(child.id), trigger, narrate=False)
    return {
        "cyclone": sim.get(child.id).meters.get("cyclone", 0.0) >= THRESHOLD,
        "cleanup": sim.get(child.id).meters.get("cleanup", 0.0) >= THRESHOLD,
    }


def do_trigger(world: World, child: Entity, trigger: TriggerItem, narrate: bool = True) -> None:
    if trigger.id not in world.setting.affords:
        raise StoryError("That setting cannot host this trigger.")
    world.zone = set(trigger.zone)
    child.meters["triggered"] = child.meters.get("triggered", 0.0) + 1.0
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    child.meters[trigger.mess] = child.meters.get(trigger.mess, 0.0) + 1.0
    _propagate(world, narrate=narrate)


def story_intro(world: World, child: Entity, trigger: TriggerItem, fix: Fix) -> None:
    world.say(
        f"{child.id} was a little blonde kid with a curious nose for trouble and a grin that asked questions before words did."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} loved {trigger.keyword} because it looked like a game, and {fix.phrase} was tucked nearby for later."
    )


def story_setup(world: World, child: Entity, trigger: TriggerItem) -> None:
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"One day at {world.setting.place}, {child.id} wandered {where} and noticed {trigger.phrase}."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} leaned closer, because curiosity is a funny thing when it sees a shiny button to poke."
    )


def story_flashback(world: World, child: Entity, fix: Fix) -> None:
    child.memes["flashback"] = child.memes.get("flashback", 0.0) + 1.0
    world.say(
        f"Then {child.id} remembered something from earlier: {fix.calming}, just like a grown-up had shown before."
    )


def story_brave_fix(world: World, child: Entity, fix: Fix) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    _propagate(world, narrate=False)
    world.say(
        f"Even with the goofy cyclone wobbling around, {child.id} took a brave breath and did the remembered trick."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} used {fix.action}, and the spinning air shooed itself away like it had been caught being silly."
    )
    world.say(
        f"In the end, {child.id} was laughing, the room was calm again, and the blonde hair was only a little wind-tossed."
    )


def tell(setting: Setting, trigger: TriggerItem, fix: Fix, name: str, child_type: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=child_type))
    world.add(Entity(id=fix.id, type="thing", label=fix.label, phrase=fix.phrase))
    story_intro(world, child, trigger, fix)
    world.para()
    story_setup(world, child, trigger)
    do_trigger(world, child, trigger, narrate=True)
    world.para()
    story_flashback(world, child, fix)
    story_brave_fix(world, child, fix)
    world.facts.update(child=child, trigger=trigger, fix=fix, setting=setting)
    return world


SETTINGS = {
    "playroom": Setting(place="the playroom", indoor=True, affords={"button"}),
    "hall": Setting(place="the hallway", indoor=True, affords={"button"}),
    "yard": Setting(place="the backyard", indoor=False, affords={"windup"}),
}

TRIGGERS = {
    "button": TriggerItem(
        id="button",
        label="silver button",
        phrase="a shiny silver button on a toy fan",
        risk="spin",
        zone={"feet"},
        mess="triggered",
        keyword="curiosity",
        tags={"trigger", "cyclone", "curiosity"},
    ),
    "windup": TriggerItem(
        id="windup",
        label="windup toy",
        phrase="a windy little windup toy",
        risk="spin",
        zone={"feet"},
        mess="triggered",
        keyword="curiosity",
        tags={"trigger", "cyclone", "curiosity"},
    ),
}

FIXES = {
    "hug": Fix(
        id="hug",
        label="big hug",
        phrase="a big hug from a grown-up",
        action="a big steadying hug",
        calming="a big hug could stop a wobble faster than a jelly spoon",
        covers={"torso"},
        guards={"triggered"},
    ),
    "book": Fix(
        id="book",
        label="story book",
        phrase="a favorite story book",
        action="a quiet counting game",
        calming="counting slowly had helped the spinning stop before",
        covers={"torso"},
        guards={"triggered"},
    ),
    "towel": Fix(
        id="towel",
        label="kitchen towel",
        phrase="a soft kitchen towel",
        action="a quick towel wrap",
        calming="wrapping the toy first had made the wind behave",
        covers={"feet"},
        guards={"triggered"},
    ),
}

NAMES = ["Mina", "Lily", "Nora", "Pia", "Zoe", "Anya"]
TRAITS = ["curious", "brave", "cheerful", "funny"]


@dataclass
class StoryParams:
    place: str
    trigger: str
    fix: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trig_id in setting.affords:
            for fix_id, fix in FIXES.items():
                if trig_id == "button" and fix_id in {"hug", "book"}:
                    combos.append((place, trig_id, fix_id))
                if trig_id == "windup" and fix_id in {"hug", "towel"}:
                    combos.append((place, trig_id, fix_id))
    return combos


def explain_rejection(trigger: TriggerItem, fix: Fix) -> str:
    return f"(No story: {fix.label} does not fit this silly cyclone problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with curiosity, flashback, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.trigger and args.fix:
        trig, fix = TRIGGERS[args.trigger], FIXES[args.fix]
        if not ((trig.id == "button" and fix.id in {"hug", "book"}) or (trig.id == "windup" and fix.id in {"hug", "towel"})):
            raise StoryError(explain_rejection(trig, fix))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trigger, fix = rng.choice(sorted(combos))
    gender = args.gender or "girl"
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trigger=trigger, fix=fix, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, trig, fix = f["child"], f["trigger"], f["fix"]
    return [
        f'Write a funny story for a small child about curiosity, a "{trig.phrase}", and a brave fix.',
        f"Tell a comedy story where {child.id} notices {trig.phrase}, gets a little spinny, remembers {fix.calming}, and stays brave.",
        f"Write a short child-friendly story that includes a cyclone-like mishap, a flashback, and a brave cleanup.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, trig, fix = f["child"], f["trigger"], f["fix"]
    qa = [
        QAItem(
            question=f"What did {child.id} notice that started the trouble?",
            answer=f"{child.id} noticed {trig.phrase}, and curiosity made {child.pronoun('subject')} poke at it.",
        ),
        QAItem(
            question=f"What did {child.id} remember before being brave?",
            answer=f"{child.id} remembered that {fix.calming}. That flashback helped {child.pronoun('object')} choose the safe, funny fix.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} stayed brave, used {fix.action}, and the silly cyclone calmed down so the room could be peaceful again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story remembers something from earlier, as if the past pops back into view for a moment.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when you feel a little nervous or wobbly.",
        ),
        QAItem(
            question="What does a cyclone mean in a story like this?",
            answer="Here it means a little whirling mess of air and silliness, not a real storm.",
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
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TRIGGERS[params.trigger], FIXES[params.fix], params.name, params.gender)
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
triggered(C) :- curiosity(C), touched(C).
cyclone(C) :- triggered(C).
brave_fix(C) :- cyclone(C), bravery(C), remembers(C).
resolved(C) :- brave_fix(C).
valid_story(Place, Trigger, Fix) :- affords(Place, Trigger), compatible(Trigger, Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("keyword", tid, t.keyword))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for c in sorted(f.covers):
            lines.append(asp.fact("covers", fid, c))
        for g in sorted(f.guards):
            lines.append(asp.fact("guards", fid, g))
    lines.append(asp.fact("compatible", "button", "hug"))
    lines.append(asp.fact("compatible", "button", "book"))
    lines.append(asp.fact("compatible", "windup", "hug"))
    lines.append(asp.fact("compatible", "windup", "towel"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="playroom", trigger="button", fix="hug", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="hall", trigger="button", fix="book", name="Nora", gender="girl", trait="brave"),
    StoryParams(place="yard", trigger="windup", fix="towel", name="Lily", gender="girl", trait="funny"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
