#!/usr/bin/env python3
"""
A standalone story world for an amber cautionary, heartwarming tale.

This script models a small child-centered domain where an amber keepsake is
precious, a risky play choice can make it fall or get lost, and a gentle parent
helps the child choose a safer way to enjoy the moment without losing the thing
they love.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fragile": 0.0, "lost": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"love": 0.0, "worry": 0.0, "joy": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)


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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.meters["fragile"] < THRESHOLD and item.meters["lost"] < THRESHOLD:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("lost", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["lost"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} slipped away in the rush.")
    return out


def _r_caretaker_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["lost"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That gave {carer.label} a worried look.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("lost", "physical", _r_lost),
    Rule("worry", "social", _r_caretaker_worry),
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"lost": prize.meters["lost"] >= THRESHOLD, "worry": sim.get("Parent").memes["worry"]}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.risk] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "sweet")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved to keep special things close.")


def loves_amber(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, "
        f"and {hero.pronoun()} wore {prize.it()} like a tiny sunny treasure."
    )


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"One bright afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} "
        f"went to {world.setting.place}."
    )
    world.say(f"{hero.id} wanted to {activity.verb}, because {activity.keyword} made the day feel bright.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_risk(world, hero, activity, prize.id)
    if not pred["lost"]:
        return False
    world.facts["predicted_loss"] = True
    world.say(
        f'"If you {activity.verb}, your {prize.label} could slip away," '
        f"{hero.pronoun('possessive')} {parent.label} said. "
        f'"Let\'s keep it safe first."'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["resolve"] += 1
    world.say(f"{hero.id} still wanted to go, and {hero.pronoun()} started to {activity.rush}.")


def gentle_stop(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["held"] = 1.0
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label} held out a hand and said, "
        f'"We can still have fun. We just need a safer way."'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_risk(world, hero, activity, prize.id)["lost"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled and said, "
        f'"How about we {gear_def.prep} before we {activity.verb}?"'
    )
    return gear_def


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["resolve"] = 0.0
    world.say(
        f"{hero.id} nodded, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label}. "
        f'"Okay," {hero.pronoun()} said. "I want the fun *and* I want to keep my {prize.label}."'
    )
    world.say(
        f"They used the {gear_def.label}, and soon {hero.id} was {activity.gerund}, "
        f"with {prize.label} still shining safely at home."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id="Amber",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_amber(world, hero, prize)
    world.para()
    setup(world, hero, parent, prize, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    gentle_stop(world, parent, hero)
    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, hero, parent, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"run", "collect"}),
    "porch": Setting(place="the porch", indoor=False, affords={"run", "collect"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"collect"}),
}

ACTIVITIES = {
    "run": Activity(
        id="run",
        verb="run between the flower pots",
        gerund="running between the flower pots",
        rush="dash around the garden",
        risk="jostled",
        keyword="amber",
        zone={"torso", "hands"},
        tags={"amber", "bright"},
    ),
    "collect": Activity(
        id="collect",
        verb="collect shiny pebbles",
        gerund="collecting shiny pebbles",
        rush="hurry from stone to stone",
        risk="slipped",
        keyword="amber",
        zone={"hands"},
        tags={"amber", "careful"},
    ),
}

PRIZES = {
    "pendant": Prize(label="amber pendant", phrase="a small amber pendant", type="pendant", region="torso"),
    "charm": Prize(label="amber charm", phrase="a tiny amber charm", type="charm", region="hands"),
}

GEAR = [
    Gear(
        id="pouch",
        label="a soft cloth pouch",
        covers={"hands"},
        guards={"slipped"},
        prep="put the amber charm in a soft cloth pouch",
        tail="tucked the charm safely into the pouch",
    ),
    Gear(
        id="ribboncase",
        label="a ribbon case",
        covers={"torso"},
        guards={"jostled"},
        prep="tie the amber pendant into a ribbon case",
        tail="slid the pendant into the ribbon case",
    ),
]

NAMES = ["Mina", "Owen", "Pia", "Theo", "Luna", "Nora"]
TRAITS = ["gentle", "curious", "careful", "bright", "soft-hearted"]


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


KNOWLEDGE = {
    "amber": [("What is amber?", "Amber is old tree resin that hardened long ago and turned into a warm, golden stone.")],
    "pouch": [("What is a pouch for?", "A pouch is a small bag that can hold little things so they do not fall out.")],
    "pendant": [("What is a pendant?", "A pendant is something you wear on a chain or string, often for decoration or luck.")],
    "charm": [("What is a charm?", "A charm is a small object people like to keep because it feels special.")],
    "careful": [("Why should you be careful with special things?", "Being careful helps special things stay safe and keeps them from getting lost or broken.")],
}

KNOWLEDGE_ORDER = ["amber", "pouch", "pendant", "charm", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short heartwarming story for a young child about amber and a gentle compromise.',
        f"Tell a cautionary story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about the {prize.label}.",
        f"Write a simple story that includes the word \"amber\" and ends with a safer way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label} worry about the {prize.label}?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label} worried because {act.verb} could make the {prize.label} slip away.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question="How did they keep the amber safe?",
            answer=f"They used {gear.label} first, so the {prize.label} stayed safe while {hero.id} played.",
        ))
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended warmly, with {hero.id} happy, {hero.pronoun('possessive')} {parent.label} smiling, and the amber still shining safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in {"amber", "careful"} or tag in world.facts["activity"].tags or tag == world.facts["gear"].id if world.facts.get("gear") else False:
            if tag in KNOWLEDGE:
                out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    if world.facts.get("gear"):
        gear = world.facts["gear"]
        if gear.id in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[gear.id])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), risk_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Amber cautionary heartwarming story world.")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not reasonably endanger the {prize.label} in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="garden", activity="run", prize="pendant", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="porch", activity="collect", prize="charm", name="Owen", gender="boy", parent="father", trait="careful"),
    StoryParams(place="playroom", activity="collect", prize="pendant", name="Luna", gender="girl", parent="mother", trait="soft-hearted"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
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
