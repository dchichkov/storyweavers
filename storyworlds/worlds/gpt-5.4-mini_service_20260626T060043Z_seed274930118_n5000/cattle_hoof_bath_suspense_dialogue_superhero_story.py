#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero-style cattle tale with suspense
and dialogue centered on a hoof bath.

Seed inspiration:
- cattle
- hoof
- bath

Premise:
A young calf with a brave heart wants to help the herd, but a muddy hoof makes
the rescue risky. A careful bath becomes the fix, and the story ends with the
cattle safe and the hoof clean.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cow", "calf", "heifer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"bull", "steer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


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
    genders: set[str] = field(default_factory=lambda: {"cow", "calf", "heifer", "bull", "steer"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("muddy", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dirty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("That would mean more work for the grown-up.")
    return out


CAUSAL_RULES = [("soil", _r_soil), ("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def activity_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by, "region": v.region,
        "plural": v.plural, "protective": v.protective, "covers": set(v.covers),
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    sim.weather = world.weather
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "cow" else "dad"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    cape = world.add(Entity(
        id="cape", type="cape", label="a red cape", phrase="a red cape", owner=hero.id,
        worn_by=hero.id, protective=True, covers={"torso"}
    ))
    cape.meters["shine"] = 1

    world.say(f"{hero.id} was a little {trait} calf with a red cape and a big wish to help the cattle.")
    world.say(f"{hero.id} loved {activity.gerund}. It made {hero.pronoun('subject')} feel like a real superhero.")
    world.say(f"That morning, {hero.pronoun('possessive')} {prize.label} was bright and new.")
    world.say(f"{hero.id} said, \"I can save the day!\"")
    world.para()

    world.say(f"At the barn, the air was quiet. Then the storm clouds rolled closer.")
    world.say(f"{hero.id} heard a cow cry, \"The gate is stuck!\"")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} hoof was muddy and slippery.")
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} frowned and said, \"If you charge out there now, your {prize.label} will get {activity.soil}.\"")
    world.say(f"{hero.id} whispered, \"But the herd needs help right now.\"")
    world.say(f"{parent.label.capitalize()} answered, \"Then we need a safer plan.\"")
    world.para()

    world.say(f"{hero.id} stepped toward the gate anyway, and the mud made a sly little splash.")
    _do_activity(world, hero, activity, narrate=True)
    world.say(f"{hero.id} froze. A beam groaned in the wind.")
    world.say(f"\"Hold still,\" said {parent.label}. \"I have an idea.\"")
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable bath solution exists for this story.")
    bath = world.add(Entity(
        id=gear.id, type="gear", label=gear.label, phrase=gear.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear.covers)
    ))
    bath.worn_by = hero.id
    world.say(f"\"How about we {gear.prep}?\" {parent.label} asked.")
    world.say(f"{hero.id} blinked. \"A bath? For my hoof?\"")
    world.say(f"\"Yes,\" said {parent.label}. \"A warm hoof bath will clean the mud and keep you steady.\"")
    world.say(f"{hero.id} nodded. \"Okay,\" {hero.id} said. \"Let me be brave the smart way.\"")
    world.say(f"They {gear.tail}. Warm water swirled around {hero.pronoun('possessive')} hoof, and the mud slid away.")
    prize.meters["dirty"] = 0.0
    hero.meters["muddy"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(f"Then {hero.id} trotted back to the gate, light on {hero.pronoun('possessive')} hoof and strong in {hero.pronoun('possessive')} cape.")
    world.say(f"With one careful push, the gate opened, and the cattle hurried to safety before the rain arrived.")
    world.say(f"{hero.id} grinned. \"The bath saved the day!\"")
    world.say(f"{parent.label.capitalize()} laughed. \"Every superhero needs a clean hoof and a wise plan.\"")

    world.facts.update(
        hero=hero, parent=parent, prize=prize, activity=activity, setting=setting,
        gear=gear, conflict=True, resolved=True
    )
    return world


SETTINGS = {
    "barn": Setting(place="the barn", afford={"mud"}),
    "yard": Setting(place="the yard", afford={"mud"}),
    "washbay": Setting(place="the wash bay", afford={"mud"}),
}

ACTIVITIES = {
    "mud": Activity(
        id="mud",
        verb="charge through the mud",
        gerund="charging through mud",
        rush="dash through the mud",
        mess="muddy",
        soil="muddy",
        zone={"feet", "legs", "hoof"},
        keyword="hoof",
        tags={"cattle", "hoof", "bath", "suspense", "dialogue"},
    ),
}

PRIZES = {
    "hoof": Prize(
        label="hoof",
        phrase="a strong front hoof",
        type="hoof",
        region="hoof",
    ),
}

GEAR = [
    Gear(
        id="hoof_bath",
        label="a warm hoof bath",
        covers={"hoof"},
        guards={"muddy"},
        prep="set up a warm hoof bath",
        tail="set up the warm hoof bath",
    ),
]

NAMES = ["Bessie", "MooMira", "Clover", "Ruby", "Pepper", "Dot"]
TRAITS = ["brave", "curious", "lively", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.afford:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short superhero-style story for a young child about cattle, a hoof, and a bath.',
        f'Write a suspenseful dialogue story about {hero.id}, a brave calf, and a muddy hoof that needs a bath before the herd can be saved.',
        f'Write a simple story where the cattle stay in danger until a hoof bath helps a superhero calf act safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little brave calf who wants to help the cattle.",
        ),
        QAItem(
            question=f"What problem did {hero.id} have before helping the herd?",
            answer=f"{hero.id} had a muddy hoof, so running straight to the gate could have made the hoof messier and less steady.",
        ),
        QAItem(
            question=f"What did {parent.label} suggest to solve the problem?",
            answer=f"{parent.label.capitalize()} suggested a warm hoof bath, which would wash the mud away and help {hero.id} move safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The hoof bath cleaned {hero.id}'s hoof, the gate opened, and the cattle got to safety before the rain came.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cattle?",
            answer="Cattle are farm animals like cows and bulls that live in herds and need care, food, and shelter.",
        ),
        QAItem(
            question="What is a hoof?",
            answer="A hoof is the hard foot of an animal like a cow or horse. It helps the animal stand and walk.",
        ),
        QAItem(
            question="What is a bath for?",
            answer="A bath is used to wash dirt away so a person or animal can feel clean again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.activity or args.prize:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.activity is None or c[1] == args.activity)
            and (args.prize is None or c[2] == args.prize)
        ]
    if not combos:
        raise StoryError("No valid cattle-hoof-bath story matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or "cow"
    parent = args.parent or "cow"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(A,P) :- at_risk(A,P), guards(G, muddy), covers(G,R), worn_on(P,R), gear(G).
valid(Place,A,P) :- affords(Place,A), at_risk(A,P), fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero-style cattle-hoof-bath storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["cow", "calf", "heifer", "bull", "steer"])
    ap.add_argument("--parent", choices=["cow", "calf", "heifer", "bull", "steer"])
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


CURATED = [
    StoryParams(place="barn", activity="mud", prize="hoof", name="Bessie", gender="cow", parent="cow", trait="brave"),
    StoryParams(place="yard", activity="mud", prize="hoof", name="Ruby", gender="calf", parent="cow", trait="curious"),
    StoryParams(place="washbay", activity="mud", prize="hoof", name="Clover", gender="heifer", parent="cow", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible stories:")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
