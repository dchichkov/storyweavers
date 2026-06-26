#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/growl_contrary_survival_conflict_happy_ending_suspense.py
==============================================================================================================================

A small fairy-tale storyworld about a brave child, a warning growl, a contrary
choice, and a survival-minded compromise that leads to a happy ending.

Premise:
- A child in a fairy-tale village wants to cross the woods to bring food to a
  loved one.
- A wolf's growl and a coming storm make the path dangerous.
- The child is contrary and wants to go anyway.
- A sensible helper offers gear that makes survival plausible.
- The tale ends with the child safe, proud, and laughing at dusk.

This module follows the Storyworld contract:
- self-contained stdlib script
- imports results eagerly; imports asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["cold", "wet", "dark", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "conflict", "defiance", "hope", "relief", "suspense"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "daughter"}
        male = {"boy", "father", "king", "man", "son"}
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    label: str
    growl: str
    danger: str
    zones: set[str]
    mess: str
    weather: str
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
        self.story: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.story = [[]]
        return clone


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD:
            continue
        for d in DANGERS.values():
            if actor.meters[d.id] < THRESHOLD:
                continue
            sig = ("danger", actor.id, d.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["fear"] += 1
            actor.memes["suspense"] += 1
            out.append(f"A low growl curled through the trees.")
    return out


def _r_survival(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["cold"] < THRESHOLD and actor.meters["wet"] < THRESHOLD:
            continue
        for gear in world.worn_items(actor):
            if not gear.protective:
                continue
            if not (world.covered(actor, "torso") or world.covered(actor, "head")):
                continue
            sig = ("survival", actor.id, gear.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["hope"] += 1
            actor.meters["cold"] = max(0.0, actor.meters["cold"] - 1)
            out.append(f"The brave little one kept warm enough to go on.")
    return out


CAUSAL_RULES = [("danger", _r_danger), ("survival", _r_survival)]


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


def risk_check(danger: Danger, prize: Prize) -> bool:
    return prize.region in danger.zones


def select_gear(danger: Danger, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if danger.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, danger: Danger, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters[danger.id] += 1
    sim.get(actor.id).memes["defiance"] += 1
    sim.get(actor.id).meters["cold"] += 1
    sim.get(actor.id).meters["wet"] += 1
    prize = sim.entities[prize_id]
    ruined = prize.region in danger.zones and not any(
        g.protective and prize.region in g.covers for g in sim.worn_items(sim.get(actor.id))
    )
    return {"ruined": ruined, "cold": sim.get(actor.id).meters["cold"]}


def add_activity(world: World, actor: Entity, danger: Danger) -> None:
    actor.meters[danger.id] += 1
    actor.meters["cold"] += 1
    actor.meters["wet"] += 1
    propagate(world, narrate=False)


def story_open(world: World, hero: Entity, prize: Entity, danger: Danger) -> None:
    world.say(
        f"In a little village at the edge of the old woods, {hero.id} was a bright {hero.type} who loved moonlit errands and tidy promises."
    )
    world.say(
        f"One evening, {hero.id} carried {hero.pronoun('possessive')} {prize.label} and listened to tales of a {danger.label} that could make even honest leaves tremble."
    )
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} still believed the night could be kind, if one knew the right path."
    )


def tension(world: World, hero: Entity, parent: Entity, danger: Danger, prize: Entity) -> None:
    world.para()
    world.say(
        f"At dusk, {hero.id} reached the lane by the woods, and the air felt thin and suspenseful."
    )
    world.say(
        f"{hero.id} wanted to go at once, but {hero.pronoun('possessive')} {parent.type} held up a hand and warned, \"Listen for the {danger.growl}.\""
    )
    hero.memes["defiance"] += 1
    world.say(
        f"That only made {hero.id} more contrary. {hero.pronoun().capitalize()} tried to step toward the dark trees anyway."
    )
    hero.memes["suspense"] += 1
    world.say(
        f"Then, from behind the brambles, there came a low {danger.growl}."
    )


def compromise(world: World, hero: Entity, parent: Entity, danger: Danger, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(danger, prize)
    if gear_def is None:
        return None
    if predict(world, hero, danger, prize.id)["ruined"]:
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
    world.say(
        f"{parent.pronoun('possessive').capitalize()} {parent.type} hurried to fetch {gear_def.label} and said, \"For survival, we choose the smarter road.\""
    )
    return gear_def


def ending(world: World, hero: Entity, parent: Entity, prize: Entity, danger: Danger, gear_def: Gear) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 2
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} nodded at last, and the contrary spark turned into courage."
    )
    world.say(
        f"They went together by the lantern glow; {gear_def.tail}, and the woods did not seem so cruel anymore."
    )
    world.say(
        f"At the far gate, {hero.id} delivered {hero.pronoun('possessive')} {prize.label} safely, and the storm passed by without stealing the night."
    )
    world.say(
        f"{hero.id} laughed, {parent.id} smiled, and the little village tucked the happy ending into memory like a warm loaf by the fire."
    )


SETTINGS = {
    "woodland": Setting(place="the old woods", indoors=False, affords={"walk"}),
    "village": Setting(place="the village lane", indoors=False, affords={"walk"}),
    "cottage": Setting(place="the cottage door", indoors=True, affords={"walk"}),
}

DANGERS = {
    "wolf": Danger(
        id="wolf",
        label="wolf",
        growl="growl",
        danger="wolf",
        zones={"torso", "legs"},
        mess="fear",
        weather="night",
        keyword="growl",
        tags={"growl", "wolf", "suspense"},
    ),
    "storm": Danger(
        id="storm",
        label="storm",
        growl="rumble",
        danger="storm",
        zones={"torso", "legs", "head"},
        mess="wet",
        weather="stormy",
        keyword="storm",
        tags={"storm", "suspense", "survival"},
    ),
}

PRIZES = {
    "basket": Prize("basket", "a small basket of bread", "basket", "arms"),
    "cloak": Prize("cloak", "a wool cloak with a silver clasp", "cloak", "torso"),
    "lantern": Prize("lantern", "a little lantern", "lantern", "hands"),
}

GEAR = [
    Gear("cloakgear", "a thick cloak", {"torso"}, {"wolf", "storm"}, "wrap themselves in a thick cloak", "walked on wrapped in the cloak"),
    Gear("lanterngear", "a lantern", {"hands"}, {"storm"}, "carry a lantern", "followed the lantern's bright path"),
]

HEROES = ["Mira", "Elin", "Pip", "Talia", "Nico"]
PARENTS = ["mother", "father"]
TRAITS = ["brave", "little", "curious", "kind", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    danger: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about growl, contrary choice, survival, suspense, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for did, d in DANGERS.items():
            for pid, p in PRIZES.items():
                if risk_check(d, p) and select_gear(d, p):
                    out.append((sid, did, pid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.danger and args.prize:
        d, p = DANGERS[args.danger], PRIZES[args.prize]
        if not (risk_check(d, p) and select_gear(d, p)):
            raise StoryError("That danger and prize do not make a fair survival challenge.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.danger is None or c[1] == args.danger)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches those options.")
    setting, danger, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, danger=danger, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    world.weather = DANGERS[params.danger].weather
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy", traits=[params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    prize_cfg = PRIZES[params.prize]
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    danger = DANGERS[params.danger]

    story_open(world, hero, prize, danger)
    tension(world, hero, parent, danger, prize)
    gear_def = compromise(world, hero, parent, danger, prize)
    if gear_def is None:
        raise StoryError("No reasonable compromise exists for this fairy tale.")
    ending(world, hero, parent, prize, danger, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, danger=danger, gear=gear_def, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    danger = f["danger"]
    prize = f["prize"]
    return [
        f'Write a fairy tale for young children about {hero.id}, a contrary child, a {danger.label}, and survival by a wise compromise.',
        f'Tell a suspenseful but gentle story where a growl in the woods makes {hero.id} pause before taking {prize.phrase} home.',
        f'Create a happy-ending tale in which a child meets a {danger.label}, chooses safety, and returns with {prize.phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, danger = f["hero"], f["parent"], f["prize"], f["danger"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, a little {hero.type} who had a contrary moment but learned to choose survival wisely.",
        ),
        QAItem(
            question=f"What sound made the woods feel suspenseful?",
            answer=f"The woods felt suspenseful because there was a low {danger.growl} in the dark trees.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} to be careful?",
            answer=f"{parent.id} warned {hero.id} because the path could be dangerous, and a child needed warmth and caution for survival.",
        ),
        QAItem(
            question=f"What helped {hero.id} get through the night safely?",
            answer=f"{gear.label} helped {hero.id} stay safe, so the child could keep going without losing the happy ending.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {hero.id} reached the gate safely, {prize.label} was delivered, and everyone could smile by the fire.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a growl usually mean in a fairy tale?",
            answer="A growl usually means something fierce or dangerous is nearby, so the characters should be careful.",
        ),
        QAItem(
            question="What does contrary mean?",
            answer="Contrary means someone wants to do the opposite of good advice, even when that advice is meant to help.",
        ),
        QAItem(
            question="What does survival mean?",
            answer="Survival means staying alive and safe through a hard or risky time.",
        ),
        QAItem(
            question="Why is a lantern helpful at night?",
            answer="A lantern makes a bright light, which helps people see the path and avoid trouble in the dark.",
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(D,P) :- danger(D), prize(P), zone(D,R), region(P,R).
fix(D,P) :- risk(D,P), gear(G), guards(G,D), covers(G,R), region(P,R).
valid(S,D,P) :- setting(S), danger(D), prize(P), afford(S,walk), risk(D,P), fix(D,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", sid, a))
    for did, d in DANGERS.items():
        lines.append(asp.fact("danger", did))
        for z in sorted(d.zones):
            lines.append(asp.fact("zone", did, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
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
        print(f"OK: clingo matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
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
    StoryParams(setting="woodland", danger="wolf", prize="cloak", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="village", danger="storm", prize="lantern", name="Pip", gender="boy", parent="father", trait="contrary"),
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
        print(f"{len(combos)} compatible combos:\n")
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
            header = f"### {p.name}: {p.danger} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
