#!/usr/bin/env python3
"""
A standalone story world for a small Space Adventure domain.

Premise:
- A crew works on a ground station / moon outpost.
- A fragile moral value field ("kindness", "honesty", "fairness") must be
  insulated from cosmic interference.
- The story turns when a character wants to rush ahead, but a guide warns them
  that without insulation the value will be damaged.
- They solve the problem by installing the right insulating layer and making a
  careful choice together.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of results.py
- lazy import of asp.py only in ASP helpers
- inline ASP_RULES twin and a Python reasonableness gate
- simulated world with physical meters and emotional memes
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    insulates: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["cold", "radiation", "dust", "damage", "shield"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "hope", "trust", "urgency", "doubt", "pride", "care", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moon base"
    outdoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ValuePrize:
    id: str
    label: str
    phrase: str
    place: str
    type: str = "artifact"


@dataclass
class Insulation:
    id: str
    label: str
    phrase: str
    covers: set[str]
    blocks: set[str]
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def protected(self, actor: Entity, region: str) -> bool:
        return any(it.protective and region in it.covers for it in self.worn_items(actor))

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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.zone = set(self.zone)
        other.paragraphs = [[]]
        return other


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    role: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_base": Setting(place="the moon base", outdoors=False, affords={"panel", "ground"}),
    "crater_rim": Setting(place="the crater rim", outdoors=True, affords={"ground"}),
    "orbital_dock": Setting(place="the orbital dock", outdoors=False, affords={"panel"}),
}

ACTIVITIES = {
    "ground": Activity(
        id="ground",
        verb="walk on the ground",
        gerund="walking over the ground",
        rush="step quickly onto the ground",
        mess="cold",
        risk="frostbite",
        zone={"feet", "legs"},
        keyword="ground",
        tags={"ground", "cold"},
    ),
    "panel": Activity(
        id="panel",
        verb="inspect the solar panel",
        gerund="inspecting solar panels",
        rush="lean over the panel",
        mess="radiation",
        risk="burned charge",
        zone={"torso", "hands"},
        keyword="panel",
        tags={"panel", "radiation"},
    ),
}

PRIZES = {
    "moral_value": ValuePrize(
        id="moral_value",
        label="moral value",
        phrase="the bright moral value core",
        place="the glass cradle",
    ),
    "promise": ValuePrize(
        id="promise",
        label="promise stone",
        phrase="the promise stone",
        place="the locked tray",
    ),
    "signal": ValuePrize(
        id="signal",
        label="signal compass",
        phrase="the signal compass",
        place="the control shelf",
    ),
}

INSULATION = [
    Insulation(
        id="thermal_blanket",
        label="a thermal blanket",
        phrase="a thermal blanket",
        covers={"feet", "legs", "torso"},
        blocks={"cold"},
        prep="wrap the core in a thermal blanket first",
        tail="carefully wrapped the core in the thermal blanket",
    ),
    Insulation(
        id="lead_shell",
        label="a lead shell",
        phrase="a lead shell",
        covers={"torso", "hands"},
        blocks={"radiation"},
        prep="put the lead shell around it first",
        tail="slid the lead shell into place",
    ),
]

CREW_NAMES = ["Ari", "Nova", "Miko", "Tess", "Kai", "Luna", "Remy", "Juno"]
TRAITS = ["curious", "steady", "brave", "gentle", "thoughtful", "eager"]


def prize_at_risk(activity: Activity, prize: ValuePrize) -> bool:
    if prize.id == "moral_value":
        return activity.id == "ground"
    return True


def select_insulation(activity: Activity, prize: ValuePrize) -> Optional[Insulation]:
    for ins in INSULATION:
        if activity.mess in ins.blocks:
            return ins
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_insulation(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: ValuePrize) -> str:
    return f"(No story: {activity.gerund} does not have a believable insulation fix for {prize.label}.)"


def explain_role(prize_id: str, role: str) -> str:
    return f"(No story: this {PRIZES[prize_id].label} story does not fit the role '{role}'.)"


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ["cold", "radiation"]:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective:
                    continue
                if item.worn_by != actor.id:
                    continue
                if item.type == "prize":
                    sig = ("risk", item.id, mess)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["damage"] += 1
                    out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} was at risk.")
    return out


def _r_insulate(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for ins in world.worn_items(actor):
            if not ins.protective:
                continue
            for region in ins.covers:
                if actor.meters["cold"] >= THRESHOLD and "cold" in ins.insulates:
                    sig = ("insulate", ins.id, "cold", region)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        actor.memes["calm"] += 1
                        out.append(f"The insulation kept the chill away.")
                if actor.meters["radiation"] >= THRESHOLD and "radiation" in ins.insulates:
                    sig = ("insulate", ins.id, "radiation", region)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        actor.memes["trust"] += 1
                        out.append(f"The insulation blocked the harsh glare.")
    return out


CAUSAL_RULES = [
    _r_risk,
    _r_insulate,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_detail(activity: Activity) -> str:
    if activity.id == "ground":
        return "The ground outside the base looked gray and sharp, like a frozen path waiting for careful boots."
    return "The panel room hummed softly, and the bright squares on the wall waited to be checked."


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.meters if False), '')}".rstrip())


def tell(setting: Setting, activity: Activity, prize_cfg: ValuePrize,
         hero_name: str = "Ari", role: str = "engineer",
         trait: str = "curious", companion: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role))
    guide = world.add(Entity(id="Guide", kind="character", type=companion))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type="prize",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
    ))

    hero.memes["care"] += 1
    hero.memes["trust"] += 1

    world.say(f"{hero.id} was a little {trait} {role} who worked at {setting.place}.")
    world.say(f"{hero.id} guarded {prize.phrase} because the crew said it held the station's moral value.")
    world.para()
    world.say(activity_detail(activity))
    world.say(f"One day, {hero.id} wanted to {activity.verb}, but {hero.id}'s {companion} looked worried.")
    world.say(f'"If you rush," {companion} said, "the cold can reach the core and damage its {prize.label} glow."')

    pred = predict_mess(world, hero, activity, prize.id)
    world.facts["predicted_damage"] = pred["damage"]
    world.facts["predicted_risk"] = activity.risk

    hero.memes["urgency"] += 1
    hero.meters[activity.mess] += 1

    world.para()
    world.say(f"{hero.id} paused and looked at the {prize.label}.")
    ins = select_insulation(activity, prize)
    if ins is None:
        return world
    ins_ent = world.add(Entity(
        id=ins.id,
        kind="thing",
        type="insulation",
        label=ins.label,
        phrase=ins.phrase,
        protective=True,
        covers=set(ins.covers),
        insulates=set(ins.blocks),
        owner=hero.id,
    ))
    ins_ent.worn_by = hero.id
    world.say(f"{companion} pointed to {ins.label} and said, \"Let's {ins.prep}.\"")
    world.say(f"{hero.id} agreed, and together they {ins.tail}.")
    propagate(world)
    hero.memes["hope"] += 1
    hero.memes["doubt"] = 0.0
    world.say(f"Then {hero.id} could still {activity.verb}, and the {prize.label} stayed safe and bright.")
    world.facts.update(hero=hero, guide=guide, prize=prize, activity=activity, insulation=ins_ent, setting=setting)
    return world


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim_actor = sim.get(actor.id)
    sim_actor.meters[activity.mess] += 1
    prize = sim.get(prize_id)
    if activity.mess == "cold":
        prize.meters["damage"] += 1
    return {"damage": prize.meters["damage"]}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short Space Adventure story for a preschooler about a {hero.type} named {hero.id}, a {act.keyword}, and a moral value that needs to be kept safe.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but must insulate {prize.phrase} first.",
        f'Write a simple space story that includes the words "{act.keyword}" and "insulate" and ends with a safe, happy choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    prize: Entity = f["prize"]
    act: Activity = f["activity"]
    ins: Entity = f["insulation"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb} while working at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {guide.id} warn {hero.id} about the {prize.label}?",
            answer=f"{guide.id} warned {hero.id} because the {act.keyword} danger could damage the {prize.label} and weaken its moral value glow.",
        ),
        QAItem(
            question=f"What helped keep the {prize.label} safe?",
            answer=f"{ins.label} helped because it insulated the {prize.label} from the cold or other harm.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{hero.id} could still {act.verb}, and the {prize.label} stayed safe, bright, and ready for the crew.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to insulate something?",
            answer="To insulate something means to wrap or cover it so heat, cold, or other harsh effects cannot reach it easily.",
        ),
        QAItem(
            question="Why is the ground cold in space stories?",
            answer="The ground can be very cold in space stories because there is no warm air to hold heat nearby.",
        ),
        QAItem(
            question="What is moral value in a story world?",
            answer="Moral value is the good meaning or good feeling a story object stands for, like kindness, honesty, or fairness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
            bits.append(f"insulates={sorted(e.insulates)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_base", activity="ground", prize="moral_value", name="Ari", role="engineer", companion="captain", trait="curious"),
    StoryParams(place="crater_rim", activity="ground", prize="promise", name="Nova", role="pilot", companion="captain", trait="steady"),
]


def explain_gender(_: str, __: str) -> str:
    return "(No story: this world does not use gender gating.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("touches", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_at", pid, p.place))
        lines.append(asp.fact("has_moral_value", pid))
    for ins in INSULATION:
        lines.append(asp.fact("insulation", ins.id))
        for b in sorted(ins.blocks):
            lines.append(asp.fact("blocks", ins.id, b))
        for c in sorted(ins.covers):
            lines.append(asp.fact("covers", ins.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A, P) :- mess_of(A, cold), prize(P), has_moral_value(P).
can_insulate(I, A, P) :- insulation(I), at_risk(A, P), blocks(I, cold), touches(A, R), covers(I, R).
valid(Place, A, P) :- affords(Place, A), at_risk(A, P), can_insulate(_, A, P).
"""


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
    print("MISMATCH between clingo and Python valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world about insulating a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["engineer", "pilot", "navigator", "mechanic"])
    ap.add_argument("--companion", choices=["captain", "mentor"])
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
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_insulation(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(CREW_NAMES),
        role=args.role or rng.choice(["engineer", "pilot", "navigator", "mechanic"]),
        companion=args.companion or "captain",
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 hero_name=params.name, role=params.role, trait=params.trait, companion=params.companion)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
