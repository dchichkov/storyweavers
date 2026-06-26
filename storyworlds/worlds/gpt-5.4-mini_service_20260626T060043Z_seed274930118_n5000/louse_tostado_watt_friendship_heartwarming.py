#!/usr/bin/env python3
"""
A small heartwarming friendship storyworld built from the seed words
louse, tostado, and watt.

Premise:
- A gentle child finds a tiny louse friend in a cozy kitchen world.
- The child wants to keep the louse safe and share a tostado snack.
- A warm lamp, measured in watts, helps them make a tiny friendship nook.
- The story resolves when the child and the louse help each other and
  sit together under the lamp with tostado crumbs.

This file follows the Storyweavers world contract with:
- StoryParams
- registries
- build_parser / resolve_params / generate / emit / main
- Python gate + inline ASP twin
- --verify parity checks
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "child"


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    watt: int = 0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.light_watts: int = 0

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.light_watts = self.light_watts
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_warm(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("cold", 0) >= THRESHOLD and world.light_watts >= 40:
            sig = ("warm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["comfort"] = e.memes.get("comfort", 0) + 1
            out.append(f"The warm lamp made {e.id} feel safer.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    louse = world.entities.get("louse")
    if not child or not louse:
        return out
    if child.memes.get("kindness", 0) >= THRESHOLD and louse.memes.get("trust", 0) >= THRESHOLD:
        sig = ("friends",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        louse.memes["joy"] = louse.memes.get("joy", 0) + 1
        out.append("They felt like true friends at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_warm, _r_friendship):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("crumbed", 0) >= THRESHOLD)}


def introduce(world: World, child: Entity, louse: Entity) -> None:
    world.say(
        f"{child.id} was a gentle child who loved tiny friends, and {louse.id} was a little louse with a brave heart."
    )


def setup_snack(world: World, child: Entity, snack: Entity) -> None:
    world.say(f"{child.id} found a {snack.phrase} on the table and wanted to share it with a tiny friend.")


def meet(world: World, child: Entity, louse: Entity, activity: Activity) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    louse.memes["trust"] = louse.memes.get("trust", 0) + 1
    world.say(
        f"One quiet morning in {world.setting.place}, {child.id} noticed {louse.id} near a crumb and softly said, "
        f"'{louse.id}, you can stay with me.'"
    )
    world.say(f"{child.id} wanted to {activity.verb}, but first {child.id} made a tiny safe place for a new friend.")


def warn_about_lamp(world: World, parent: Entity, child: Entity, lamp: Entity, activity: Activity, snack: Entity) -> bool:
    pred = predict_mess(world, child, activity, snack.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you rush, the {snack.label} will get crumbs everywhere," {parent.id} said, "
        f"and {parent.pronoun("possessive")} voice stayed calm and kind.'
    )
    return True


def choose_lamp(world: World, parent: Entity, child: Entity, lamp: Entity) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.light_watts = lamp.meters.get("watt", 0)
    lamp.worn_by = child.id
    world.say(
        f"{parent.id} plugged in the little lamp, and its {lamp.meters.get('watt', 0)} watts made the corner glow like a tiny sunrise."
    )


def share(world: World, child: Entity, louse: Entity, snack: Entity) -> None:
    child.memes["love"] = child.memes.get("love", 0) + 1
    louse.memes["trust"] = louse.memes.get("trust", 0) + 1
    louse.memes["cold"] = 0
    world.say(
        f"{child.id} broke the {snack.label} into soft crumbs and set them beside {louse.id}. "
        f"{louse.id} nibbled happily, and the room felt even warmer."
    )


def ending(world: World, child: Entity, louse: Entity, snack: Entity) -> None:
    world.say(
        f"By the end, {child.id} and {louse.id} sat together under the lamp, sharing {snack.it()} and smiling at the little glow."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"share"}),
    "sunroom": Setting(place="the sunroom", indoor=True, affords={"share"}),
}


ACTIVITIES = {
    "share": Activity(
        id="share",
        verb="share a snack",
        gerund="sharing a snack",
        rush="rush to the table",
        mess="crumbed",
        soil="crumbly",
        keyword="tostado",
        tags={"friendship", "tostado"},
    )
}


PRIZES = {
    "tostado": Prize(
        label="tostado",
        phrase="a warm tostado snack",
        type="snack",
        owner_kind="child",
    )
}


GEAR = [
    Gear(
        id="lamp",
        label="a little lamp",
        prep="turn on the lamp",
        tail="kept the corner bright",
        guards={"cold"},
        watt=40,
    )
]

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Mia"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Ben"]
TRAITS = ["gentle", "kind", "patient", "quiet"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name, traits=[params.trait]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    louse = world.add(Entity(id="louse", kind="character", type="louse", label="louse"))
    snack = world.add(Entity(id="snack", type="snack", label="tostado", phrase="a warm tostado"))
    lamp = world.add(Entity(id="lamp", type="lamp", label="lamp", phrase="a little lamp"))
    lamp.meters["watt"] = 40
    louse.memes["cold"] = 1
    world.light_watts = 0

    activity = ACTIVITIES[params.activity]

    introduce(world, child, louse)
    setup_snack(world, child, snack)

    world.para()
    meet(world, child, louse, activity)
    warn_about_lamp(world, parent, child, lamp, activity, snack)
    choose_lamp(world, parent, child, lamp)

    world.para()
    share(world, child, louse, snack)
    ending(world, child, louse, snack)

    world.facts.update(child=child, parent=parent, louse=louse, snack=snack, lamp=lamp, activity=activity, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a heartwarming story about a child named {child.label} who finds a tiny louse friend and shares a tostado.',
        f"Tell a gentle friendship story where {child.label} and a louse become friends under a warm lamp.",
        f'Write a child-friendly story that includes the words "louse", "tostado", and "watt" and ends with a cozy smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    louse = f["louse"]
    snack = f["snack"]
    lamp = f["lamp"]
    return [
        QAItem(
            question=f"Who became friends in the story?",
            answer=f"{child.label} and {louse.id} became friends after {child.label} chose to be gentle and share the {snack.label}.",
        ),
        QAItem(
            question=f"What did {child.label} share with the louse?",
            answer=f"{child.label} shared a {snack.phrase} with the louse.",
        ),
        QAItem(
            question=f"How bright was the lamp?",
            answer=f"The lamp had {lamp.meters.get('watt', 0)} watts, so it made a warm little glow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a watt?",
            answer="A watt is a unit that tells how much power a light or another electrical thing uses.",
        ),
        QAItem(
            question="What does a warm lamp do?",
            answer="A warm lamp gives a gentle glow that helps a room feel cozy and safe.",
        ),
        QAItem(
            question="What is a tostado?",
            answer="A tostado is a warm, toasted snack or bread that can be shared in small bites.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or tiny creatures care about each other, help each other, and enjoy being together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"light_watts={world.light_watts}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), can_soil(A,P).
has_fix(A,P) :- prize_at_risk(A,P), lamp(L), watts(L,W), W >= 40.
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("can_soil", aid, "tostado"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for g in GEAR:
        lines.append(asp.fact("lamp", g.id))
        lines.append(asp.fact("watts", g.id, g.watt))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming friendship storyworld with louse, tostado, and watt.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="kitchen", activity="share", prize="tostado", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="sunroom", activity="share", prize="tostado", name="Theo", gender="boy", parent="father", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
