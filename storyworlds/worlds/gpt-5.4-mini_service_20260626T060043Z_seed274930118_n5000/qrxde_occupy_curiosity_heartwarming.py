#!/usr/bin/env python3
"""
Standalone storyworld: qrxde_occupy_curiosity_heartwarming

A small heartwarming simulation about a curious child who wants to occupy a
cozy space with treasures, while a caring adult worries about something
delicate nearby. The world turns on curiosity, careful sharing, and a gentle
compromise that makes room for both play and safety.

Seed words kept in-world: qrxde, occupy.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        self.zone: set[str] = set()
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


@dataclass
class Rule:
    name: str
    apply: callable


def _copy_entity(e: Entity) -> Entity:
    return Entity(
        id=e.id, kind=e.kind, type=e.type, label=e.label, phrase=e.phrase,
        owner=e.owner, caretaker=e.caretaker, worn_by=e.worn_by, region=e.region,
        protective=e.protective, covers=set(e.covers), plural=e.plural,
        meters=dict(e.meters), memes=dict(e.memes),
    )


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("curiosity", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.id == actor.id:
                continue
            if item.region not in world.zone:
                continue
            if item.protective or world.setting.place == "the window seat" and item.label == "cushion":
                continue
            sig = ("scatter", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scattered"] = item.meters.get("scattered", 0.0) + 1
            out.append(f"Their curious reaching made {item.label} feel a little crowded.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("scattered", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0.0) + 1
        out.append(f"That made {caretaker.label} worry about {item.label}.")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("comfort", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("soothe", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0.0
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        out.append(f"The gentle plan helped everyone feel calm again.")
    return out


CAUSAL_RULES = [
    Rule("scatter", _r_scatter),
    Rule("worry", _r_worry),
    Rule("soothe", _r_soothe),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: _copy_entity(v) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    sim.fired = set(world.fired)
    sim.get(actor.id).meters["curiosity"] = actor.meters.get("curiosity", 0.0)
    sim.get(actor.id).memes["comfort"] = actor.memes.get("comfort", 0.0)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"scattered": prize.meters.get("scattered", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["curiosity"] = actor.meters.get("curiosity", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def setting_detail(setting: Setting) -> str:
    if setting.place == "the window seat":
        return "Sunlight lay across the cushion, and the window was bright with tiny raindrops."
    if setting.place == "the kitchen table":
        return "The table was warm from breakfast and ready for little hands and careful eyes."
    return f"{setting.place.capitalize()} looked cozy and calm."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved curiosity more than anything."
    )


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.gerund} and notice every tiny thing."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {parent.label} brought home {hero.pronoun('object')} {prize.phrase}."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, and even said the seed word qrxde "
        f"like a secret for the day."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict(world, hero, activity, prize.id)["scattered"]:
        return False
    world.say(
        f'"If you {activity.verb}, {prize.label} might get too crowded," {parent.label} said.'
    )
    world.facts["warning"] = True
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} frowned, because curiosity still wanted to occupy the whole corner.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id, type="thing", label=gear.label, protective=True,
        covers=set(gear.covers), plural=gear.plural, owner=hero.id,
    ))
    g.worn_by = hero.id
    world.say(
        f'{parent.label} smiled and said, "How about we use {gear.label} first?"'
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["comfort"] = hero.memes.get("comfort", 0.0) + 1
    hero.memes["stubborn"] = 0.0
    world.say(
        f'{hero.id} nodded, then scooted over to make room. '
        f'Together they {gear.tail}.'
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed safe, and "
        f"{parent.label} was laughing beside {hero.pronoun('object')}."
    )


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "window": Setting("the window seat", indoor=True, affords={"curiosity"}),
    "kitchen": Setting("the kitchen table", indoor=True, affords={"curiosity"}),
    "porch": Setting("the porch bench", indoor=False, affords={"curiosity"}),
}

ACTIVITIES = {
    "curiosity": Activity(
        id="curiosity",
        verb="occupy the cozy corner with curious things",
        gerund="arranging curious things",
        rush="occupy the corner all at once",
        mess="scattered",
        soil="too crowded",
        zone={"tabletop", "seat"},
        keyword="curiosity",
        tags={"curiosity"},
    )
}

PRIZES = {
    "teacup": Prize("teacup", "a little blue teacup", "teacup", "tabletop"),
    "lamp": Prize("lamp", "a soft yellow lamp", "lamp", "tabletop"),
    "book": Prize("book", "a favorite storybook", "book", "tabletop"),
    "plant": Prize("plant", "a tiny potted plant", "plant", "sill"),
}

GEAR = [
    Gear("tray", "a small tray", {"tabletop"}, {"scattered"}, "slide the little things onto a tray", "set the tray down neatly"),
    Gear("cloth", "a soft cloth", {"tabletop"}, {"scattered"}, "lay out a soft cloth", "spread the cloth carefully"),
    Gear("cushion", "a floor cushion", {"seat"}, {"scattered"}, "add a floor cushion beside the seat", "place the cushion right where it belongs"),
]

GIRL_NAMES = ["Mina", "Tess", "Nina", "Lila", "Ruby"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Finn", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act in ACTIVITIES.values():
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act.id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} is not in the crowded zone, so curiosity would not endanger it.)"
    return f"(No story: no gear in this world can safely handle {activity.gerund} for {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming curiosity storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize_id].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(place, activity, prize_id, name, parent, gender)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="Prize", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region))
    introduce(world, hero)
    loves(world, hero, activity)
    buys(world, parent, hero, prize)
    world.para()
    world.say(setting_detail(setting))
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    world.para()
    gear = offer(world, parent, hero, activity, prize)
    if gear:
        accept(world, hero, parent, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story about a curious child named {hero.id} who wants to "{act.verb}" and includes the word "qrxde".',
        f"Tell a gentle story where {hero.id} tries to {act.verb} but a parent worries about {prize.phrase}.",
        f"Write a cozy story about making room, sharing space, and choosing a safer way to {act.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb}?",
            answer=f"{hero.id} wanted to {act.verb} because {hero.pronoun('subject')} was full of curiosity.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {prize.label} could get too crowded if {hero.id} tried to occupy the whole corner at once.",
        ),
        QAItem(
            question=f"What helped {hero.id} and {parent.label} solve the problem?",
            answer=f"They used {f['gear'].label} so {hero.id} could keep exploring while {prize.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is curiosity?", "Curiosity is the feeling that makes someone want to look, ask, and learn about new things."),
        QAItem("What does it mean to occupy a space?", "To occupy a space means to take up room there, like sitting on a bench or standing in a corner."),
        QAItem("Why do people use a tray?", "People use a tray to carry or hold small things together so they do not spill or scatter."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.region:
            parts.append(f"region={e.region}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(P,A,Pr) :- setting(P), activity(A), prize(Pr), affords(P,A), prize_at_risk(A,Pr), has_fix(A,Pr).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams("window", "curiosity", "teacup", "Mina", "mother", "girl"),
    StoryParams("kitchen", "curiosity", "lamp", "Owen", "father", "boy"),
    StoryParams("porch", "curiosity", "plant", "Lila", "grandmother", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.place} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
