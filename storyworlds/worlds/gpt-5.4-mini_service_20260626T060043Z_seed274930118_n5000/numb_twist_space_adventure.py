#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/numb_twist_space_adventure.py
===========================================================================================================

A compact space-adventure story world with a child-friendly twist:
a brave spacer starts with a small problem, feels numb in the cold, then
finds a smart twist that fixes the day.

The premise is intentionally tiny and classical:
- a young astronaut loves a space chore or space trip,
- something in the cold or vacuum makes a part of their body feel numb,
- a helper notices the risk,
- the helper suggests a better tool or a clever twist,
- the hero uses the twist and the ending proves the change.

The story prose is driven by a real world model:
- physical meters track coldness, numbness, suit safety, and tool state,
- memes track worry, courage, delight, and relief,
- a simple rule engine turns state into narration.

This file is standalone except for the shared result containers and the shared
ASP helper used only in ASP mode.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def _init_maps(self) -> None:
        for k in ("cold", "numb", "safe", "broken", "tapped"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "courage", "relief", "joy", "twist"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    consequence: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    zone: set[str] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        ent._init_maps()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        return clone


def _r_cold_to_numb(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["cold"] < THRESHOLD:
            continue
        sig = ("numb", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["numb"] += 1
        actor.memes["worry"] += 1
        out.append(f"{actor.id}'s fingers felt numb from the cold.")
    return out


def _r_break_warning(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["broken"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("warn", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would worry {carer.label or carer.id}.")
    return out


CAUSAL_RULES = [
    _r_cold_to_numb,
    _r_break_warning,
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


def prize_at_risk(activity: Activity, prize: Entity) -> bool:
    return prize.owner is not None and any(r in activity.zone for r in ("hands", "torso", "head"))


def select_gear(activity: Activity, prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.hazard in gear.guards and prize.owner is not None and any(r in gear.covers for r in ("hands", "torso", "head", "feet")):
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "numb": bool(actor.meters["numb"] >= THRESHOLD),
        "broken": bool(prize and prize.meters["broken"] >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} does not support {activity.verb}.)")
    world.zone = set(activity.zone)
    actor.meters["cold"] += 1
    if activity.id == "twist":
        actor.memes["twist"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} astronaut who loved the quiet of space.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} because it made the ship feel like an adventure.")


def gets_gear(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Before launch, {hero.id}'s {parent.label or parent.type} handed {hero.pronoun('object')} {prize.phrase}.")


def values_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label or parent.type} went to {world.setting.place}.")
    world.say(f"The {world.setting.kind} was {activity.keyword} quiet, with stars shining beyond the window.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["courage"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} hands were already feeling chilly.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["numb"]:
        return False
    world.facts["predicted_numb"] = True
    world.say(f'"Your fingers may go numb if you {activity.verb}," {parent.pronoun("possessive")} {parent.label or parent.type} said.')
    return True


def twist(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["twist"] += 1
    world.say(f"{hero.id} paused, then had a clever twist of an idea.")


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))
    gear.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label or parent.type} smiled and said, \"How about we {gear_def.prep}?\"")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"{hero.id} grinned, put on the {gear_def.label}, and nodded.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, and {hero.pronoun('possessive')} {prize.label} stayed safe and snug.")


def tell(setting: Setting, activity: Activity, prize_cfg: Gear, hero_name: str = "Nova", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["brave", "curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(
        id="prize",
        type="gloves",
        label=prize_cfg.label,
        phrase="a pair of warm space gloves",
        owner=hero.id,
        caretaker=parent.id,
        plural=True,
    ))
    introduce(world, hero)
    loves_activity(world, hero, activity)
    gets_gear(world, parent, hero, prize)
    values_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    twist(world, hero, activity)
    gear_def = offer_gear(world, parent, hero, activity, prize)
    world.para()
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "moon_base": Setting(place="the moon base", kind="space base", affords={"spacewalk", "twist"}),
    "star_ship": Setting(place="the starship", kind="ship", affords={"spacewalk", "twist"}),
    "ice_station": Setting(place="the ice station", kind="orbital station", affords={"spacewalk", "twist"}),
}

ACTIVITIES = {
    "spacewalk": Activity(
        id="spacewalk",
        verb="step outside on a spacewalk",
        gerund="floating on a spacewalk",
        rush="rush out into the black",
        hazard="cold",
        consequence="too cold and numb",
        zone={"hands", "head"},
        keyword="space",
        tags={"space", "cold"},
    ),
    "twist": Activity(
        id="twist",
        verb="turn the antenna with a careful twist",
        gerund="twisting the antenna",
        rush="grab the antenna and turn fast",
        hazard="cold",
        consequence="stiff and numb",
        zone={"hands"},
        keyword="twist",
        tags={"space", "twist"},
    ),
}

GEAR = [
    Gear(
        id="mittens",
        label="mittens",
        covers={"hands"},
        guards={"cold"},
        prep="put on the warm mittens first",
        tail="floated back to the hatch with their mittens on",
        plural=True,
    ),
    Gear(
        id="helmet_liner",
        label="a soft helmet liner",
        covers={"head"},
        guards={"cold"},
        prep="add a soft helmet liner",
        tail="waved through the window with the liner snug under the helmet",
    ),
]

PRIZES = {
    "gloves": Gear(
        id="gloves",
        label="space gloves",
        covers={"hands"},
        guards={"cold"},
        prep="put on the warm space gloves first",
        tail="turned back toward the airlock with warm gloves on",
        plural=True,
    )
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ada", "Ivy", "Zia"]
BOY_NAMES = ["Orion", "Pax", "Jett", "Leo", "Finn", "Kai"]
TRAITS = ["brave", "curious", "cheerful", "steady", "bold", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, Entity(id=prize_id, owner="hero")) and select_gear(act, Entity(id=prize_id, owner="hero")):
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


KNOWLEDGE = {
    "space": [("What is space?", "Space is the huge, dark area beyond Earth where stars, planets, and moons are found.")],
    "cold": [("Why do hands feel numb in the cold?", "Hands can feel numb in the cold because chilly air makes the nerves work more slowly.")],
    "twist": [("What does twist mean?", "A twist is a turn, often made with your hand, wrist, or body to change direction.")],
    "gloves": [("What do gloves do?", "Gloves cover your hands and help keep them warm and clean.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a short space adventure for a young child that includes the word "{act.keyword}" and a clever twist.',
        f"Tell a gentle story about {f['hero'].id} on {f['setting'].place} who wants to {act.verb} but feels numb in the cold.",
        f"Write a child-friendly story where a helper offers warm gloves and the ending shows a happy space fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type} who loves space.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {act.verb} while wearing {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"Why did {parent.label or parent.type} worry about the plan?",
            answer=f"{parent.label or parent.type} worried because the cold could make {hero.pronoun('possessive')} hands numb.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {hero.id} put on the warm mittens and kept {prize.label} safe while playing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("gloves")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_base", activity="spacewalk", prize="gloves", name="Nova", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="star_ship", activity="twist", prize="gloves", name="Orion", gender="boy", parent="father", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Gear) -> str:
    return f"(No story: {activity.verb} and {prize.label} do not make a safe, matched problem/fix pair.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: try a different gender for {prize_id}; this world does not constrain that pair.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.hazard))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for r in sorted(p.covers):
            lines.append(asp.fact("covers", pid, r))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        lines.append(asp.fact("worn_on", pid, "hands"))
        for g in ["girl", "boy"]:
            lines.append(asp.fact("wears", g, pid))
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space adventure story world with a numb twist.")
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
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:10} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
