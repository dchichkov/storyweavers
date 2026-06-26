#!/usr/bin/env python3
"""
A small standalone fairy-tale storyworld about an orchard quarrel over postage,
with a walleye as the surprising helper.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Remedy:
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.region == region and e.type == "remedy" for e in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    remedy: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"postage", "walleye"}),
}

ACTIVITIES = {
    "postage": Activity(
        id="postage",
        verb="carry the postage to market",
        gerund="carrying the postage",
        rush="dash toward the gate with the postage",
        mess="lost",
        soil="scattered and lost",
        zone={"hands"},
        keyword="postage",
        tags={"postage", "letter", "lost"},
    ),
    "walleye": Activity(
        id="walleye",
        verb="look after the walleye in the stream",
        gerund="watching the walleye",
        rush="run to the stream for the walleye",
        mess="splashed",
        soil="splashed and wet",
        zone={"hands", "shoes"},
        keyword="walleye",
        tags={"walleye", "water"},
    ),
}

PRIZES = {
    "satchel": Prize(
        label="satchel",
        phrase="a stitched satchel for the letters",
        type="satchel",
        region="hands",
    ),
    "bundle": Prize(
        label="bundle",
        phrase="a little bundle of sealed letters",
        type="bundle",
        region="hands",
        plural=True,
    ),
}

REMEDIES = [
    Remedy(
        id="ribbon",
        label="a red ribbon tie",
        covers={"hands"},
        guards={"lost"},
        prep="tie the satchel with a red ribbon first",
        tail="walked back beneath the apple boughs with the ribbon tied tight",
    ),
    Remedy(
        id="waxwrap",
        label="a wax wrap",
        covers={"hands"},
        guards={"splashed"},
        prep="wrap the letters in wax first",
        tail="returned with the wax wrap fastened snugly",
    ),
]

GIRL_NAMES = ["Mira", "Elin", "Rosy", "Lina", "Thea"]
BOY_NAMES = ["Robin", "Perry", "Jasper", "Finn", "Alden"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    for rem in REMEDIES:
                        if act.mess in rem.guards:
                            combos.append((place, act_id, prize_id, rem.id))
    return combos


def reason_invalid(act: Activity, prize: Prize) -> str:
    if prize.region not in act.zone:
        return f"(No story: {act.keyword} does not endanger a prize worn on the {prize.region}.)"
    return "(No story: the catalog has no remedy that can honestly fix that trouble.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale orchard storyworld about postage and a walleye.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--remedy", choices=[r.id for r in REMEDIES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
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
        if pr.region not in act.zone:
            raise StoryError(reason_invalid(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, remedy=remedy, name=name, gender=gender, parent=parent)


def _predicted_trouble(world: World, actor: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    p = sim.get(prize.id)
    return bool(p.meters.get(activity.mess, 0.0) >= THRESHOLD)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["desire"] = actor.memes.get("desire", 0.0) + 1
    for item in world.worn_items(actor):
        if item.region in world.zone and not world.covered(actor, item.region):
            item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1
    if narrate:
        pass


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    remedy_def = next(r for r in REMEDIES if r.id == params.remedy)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    hero.memes["love_orchard"] = 1
    hero.memes["love"] = 1
    prize.worn_by = hero.id

    world.say(f"Once upon a time, {hero.id} was a little {params.gender} who loved the orchard and its sweet air.")
    world.say(f"{hero.pronoun().capitalize()} also loved {act.gerund}, for the orchard felt like a kingdom made for small feet and brave errands.")
    world.say(f"One bright day, {parent.label_word if hasattr(parent, 'label_word') else params.parent} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.")

    world.para()
    world.say(f"At the orchard gate, {hero.id} wanted to {act.verb}, but the path led too close to trouble.")
    if _predicted_trouble(world, hero, act, prize):
        world.say(f'"You will get your {prize.label} {act.soil}," {params.parent} warned. "And then the task will be a sad one."')
    hero.memes["conflict"] = 1
    world.say(f"{hero.id} frowned, because the wish to go on was pulling hard at {hero.pronoun('possessive')} heart.")

    world.para()
    world.say(f"Then {params.parent} noticed {params.name} was not being stubborn on purpose, only torn between duty and delight.")
    world.say(f"So {params.parent} chose a kinder answer: {remedy_def.prep}.")
    if act.id == "walleye":
        world.say("A wise walleye in the stream flicked its tail and made the water sparkle, as if to bless the plan.")
    else:
        world.say("The apple leaves rustled softly, as if the orchard itself approved.")

    world.say(f"{hero.id} agreed at once. Together they {remedy_def.tail}.")
    world.say(f"After that, {hero.id} could {act.gerund}, and {prize.label} stayed clean and safe.")
    hero.memes["conflict"] = 0
    hero.memes["joy"] = 1
    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": act,
        "remedy": remedy_def,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story set in an orchard that includes "{f["activity"].keyword}" and "postage".',
        f"Tell a gentle conflict story about {f['hero'].id} in the orchard, where a parent worries about {f['prize'].label}.",
        f"Write a child-friendly tale in which a {f['activity'].keyword} errand ends with a happy compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    rem = f["remedy"]
    return [
        QAItem(
            question=f"Who was the story about in the orchard?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {parent.label if parent.label else f'the {parent.type}'}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do that caused the conflict?",
            answer=f"{hero.id} wanted to {act.verb}, but that would have put {prize.label} in danger.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"They used {rem.label}, which let {hero.id} {act.gerund} while keeping {prize.label} safe.",
        ),
        QAItem(
            question=f"Why did the parent worry about the prize?",
            answer=f"The parent worried because if {hero.id} went ahead, {prize.label} would get {act.soil}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is postage?", answer="Postage is the fee or mark that helps a letter or parcel travel to where it should go."),
        QAItem(question="What is a walleye?", answer="A walleye is a kind of fish that lives in water and has sharp senses for finding food."),
        QAItem(question="What is an orchard?", answer="An orchard is a place where fruit trees grow in rows."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== (2) Story questions ==",]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} region={e.region} worn_by={e.worn_by}")
    return "\n".join(lines)


ASP_RULES = r"""
place(orchard).
activity(postage).
activity(walleye).
prize(satchel).
prize(bundle).
remedy(ribbon).
remedy(waxwrap).

affords(orchard, postage).
affords(orchard, walleye).

zone(postage, hands).
zone(walleye, hands).
zone(walleye, shoes).

mess(postage, lost).
mess(walleye, splashed).

worn_on(satchel, hands).
worn_on(bundle, hands).

guards(ribbon, lost).
guards(waxwrap, splashed).

covers(ribbon, hands).
covers(waxwrap, hands).

valid(P, A, R, M) :- affords(P, A), zone(A, Z), worn_on(R, Z), mess(A, M), guards(MR, M), covers(MR, Z).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        lines.append(asp.fact("mess", a.id, a.mess))
        for z in a.zone:
            lines.append(asp.fact("zone", a.id, z))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.label))
        lines.append(asp.fact("worn_on", p.label, p.region))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
        for g in r.guards:
            lines.append(asp.fact("guards", r.id, g))
        for c in r.covers:
            lines.append(asp.fact("covers", r.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_python() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos_python())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="orchard", activity="postage", prize="satchel", remedy="ribbon", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="orchard", activity="walleye", prize="bundle", remedy="waxwrap", name="Robin", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
