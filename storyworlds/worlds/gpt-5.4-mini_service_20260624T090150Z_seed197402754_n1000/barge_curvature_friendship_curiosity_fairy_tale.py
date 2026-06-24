#!/usr/bin/env python3
"""
storyworlds/worlds/barge_curvature_friendship_curiosity_fairy_tale.py
======================================================================

A small fairy-tale story world about a curious child, a loyal friend, and a
barge that must travel through a river's curvature without getting stuck.

Seed tale:
---
In a kingdom of reeds and moonlight, a little ferryman named Pippin loved to
watch barges glide along the river. One bright morning, Pippin and his friend
Mira found a painted barge with a tall lantern mast. They wanted to carry honey
to the market, but the river bent sharply around a willow island, and the mast
looked too high for the low bridge ahead.

Pippin grew curious and wanted to peek at the sparkling water under the bridge,
while Mira worried the barge would scrape the stones. Together they lowered the
mast, tied the lantern safe, and steered carefully through the curve. In the end
the barge slipped past the bend, the honey stayed safe, and their friendship
shone brighter than the river moon.

World model:
---
- physical meters: height, weight, drift, damage, shine, cargo, current
- emotional memes: curiosity, friendship, worry, relief, pride

Story beats:
---
setup -> friendship and curiosity at the riverside
tension -> a barge must fit a curved river bend and low bridge
turn -> curiosity causes risk, friendship chooses a careful method
resolution -> the mast is lowered, the barge passes, and the ending image proves
              what changed
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    curve: str
    bridge: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    tags: set[str]


@dataclass
class Cargo:
    label: str
    phrase: str
    region: str
    fragile: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    method: str
    tail: str
    lowers: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.curvature: str = setting.curve

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.curvature = self.curvature
        return c


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for boat in world.entities.values():
        if boat.type != "barge":
            continue
        if boat.meters.get("height", 0) < THRESHOLD:
            continue
        if boat.meters.get("lowered", 0) >= THRESHOLD:
            continue
        if boat.meters.get("at_bridge", 0) < THRESHOLD:
            continue
        sig = ("scrape", boat.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        boat.meters["damage"] = boat.meters.get("damage", 0) + 1
        out.append("The barge scraped the bridge stones.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("danger", 0) < THRESHOLD:
            continue
        if e.memes.get("worry", 0) >= THRESHOLD:
            continue
        e.memes["worry"] = e.memes.get("worry", 0) + 1
        out.append(f"{e.id} felt worry tug at the edge of {e.pronoun('possessive')} heart.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_scrape, _r_worry):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risky(quest: Quest, cargo: Cargo) -> bool:
    return cargo.region in quest.zone


def select_fix(quest: Quest, cargo: Cargo) -> Optional[Fix]:
    for fx in FIXES:
        if fx.lowers and cargo.region in quest.zone:
            return fx
    return None


def predict(world: World, hero: Entity, quest: Quest, cargo_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    cargo = sim.get(cargo_id)
    return {"damaged": cargo.meters.get("damage", 0) >= THRESHOLD}


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.meters[quest.id] = hero.meters.get(quest.id, 0) + 1
    hero.meters["danger"] = hero.meters.get("danger", 0) + 1
    world.get("barge").meters["at_bridge"] = 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, quest: Quest, cargo_def: Cargo, hero_name: str, friend_name: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type="girl", meters={"danger": 0}, memes={"curiosity": 0, "friendship": 0}))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl", meters={}, memes={"friendship": 1, "worry": 0}))
    barge = world.add(Entity(id="barge", kind="thing", type="barge", label="a painted barge", phrase="a painted barge with a lantern mast", meters={"height": 2, "lowered": 0, "at_bridge": 0, "damage": 0}))
    cargo = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo_def.label, phrase=cargo_def.phrase, owner=hero.id, caretaker=friend.id, meters={"damage": 0}))

    hero.memes["curiosity"] = 1
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1

    world.say(f"In a kingdom beside {setting.place}, {hero.id} was a little ferryman who loved the river's {setting.curve}.")
    world.say(f"{hero.id} and {friend.id} shared {cargo.phrase} on {barge.phrase}, and their friendship made the morning feel golden.")
    world.para()
    world.say(f"One day they came to {setting.bridge}, where the river bent in a long, silver curve.")
    world.say(f"{hero.id} wanted to peek at the sparkling water under the bridge, but the barge's mast stood very tall.")
    world.say(f"{friend.id} worried the mast would scrape the stone, because the bend was narrow and the bridge was low.")
    hero.meters["danger"] = 1
    world.para()
    world.say(f'"We must choose carefully," said {friend.id}, while {hero.id}'s curiosity still flickered like a tiny lantern.')
    fix = select_fix(quest, cargo_def)
    if fix:
        world.say(f"They used {fix.method}, and {hero.id} listened because friendship was stronger than rushing ahead.")
        world.get("barge").meters["lowered"] = 1
        world.get("barge").meters["height"] = 0
        world.get("cargo").meters["safe"] = 1
        world.say(f"The mast went down, the barge slid through the curvature of the river, and the bridge stayed whole.")
        world.say(f"Then {fix.tail}, and the honey {cargo.label} stayed safe while moonlight danced on the water.")
    else:
        world.say("But no wise way could be found, so the tale would not be told.")
    world.facts.update(hero=hero, friend=friend, barge=barge, cargo=cargo, setting=setting, quest=quest, fix=fix, resolved=fix is not None)
    return world


SETTINGS = {
    "willow_bend": Setting(place="the willow bend", curve="curvature", bridge="the low willow bridge", affords={"cross"}),
    "moon_river": Setting(place="the moon river", curve="curvature", bridge="the moonstone arch", affords={"cross"}),
    "reed_harbor": Setting(place="the reed harbor", curve="curvature", bridge="the harbor gate", affords={"cross"}),
}

QUESTS = {
    "cross": Quest(id="cross", verb="cross the bend", gerund="crossing the bend", risk="scrape the bridge", zone={"height"}, tags={"barge", "curvature"}),
}

CARGOES = {
    "honey": Cargo(label="honey", phrase="a jar of honey", region="height", fragile=True),
    "flowers": Cargo(label="flowers", phrase="a basket of flowers", region="height", fragile=True),
    "songbook": Cargo(label="songbook", phrase="a little songbook", region="height", fragile=False),
}

FIXES = [
    Fix(id="lower_mast", label="a lower-mast rope", method="they tied the rope and lowered the mast", tail="the barge floated on like a silver duck", lowers=True),
    Fix(id="fold_banner", label="a folded banner", method="they folded the banner and tucked it close", tail="their lantern shone safely at the river's curve", lowers=True),
]

GIRL_NAMES = ["Pippin", "Mira", "Lila", "Nina", "Tessa", "Wren"]
TRAITS = ["curious", "gentle", "brave", "kind", "bright"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    cargo: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy-tale story about {f["hero"].id}, {f["friend"].id}, and a barge traveling through a river curve.',
        f"Tell a gentle story where curiosity and friendship help a barge pass a curved bridge without harm.",
        f'Write a child-friendly tale that includes the words "barge" and "curvature" and ends with a safe crossing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, cargo, setting, quest = f["hero"], f["friend"], f["cargo"], f["setting"], f["quest"]
    return [
        QAItem(
            question=f"Who in the story loved the river and wanted to cross the {setting.curve}?",
            answer=f"It was {hero.id}, a little {hero.memes.get('curiosity') and 'curious'} ferryman who wanted to cross the bend with {friend.id}.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the barge at {setting.bridge}?",
            answer=f"{friend.id} worried because the barge's mast was tall and the bridge was low, so the barge might scrape the stones on the curved river path.",
        ),
        QAItem(
            question=f"What did they carry on the barge?",
            answer=f"They carried {cargo.phrase}, and they wanted it to stay safe during the crossing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a barge?", answer="A barge is a long, flat boat that can carry heavy things on rivers or canals."),
        QAItem(question="What does curvature mean?", answer="Curvature means the way a line or path bends instead of staying straight."),
        QAItem(question="What is friendship?", answer="Friendship is the caring bond between friends who help and enjoy each other."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to look, ask, and learn about something new."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for q_id in s.affords:
            q = QUESTS[q_id]
            for c_id in CARGOES:
                if risky(q, CARGOES[c_id]) and select_fix(q, CARGOES[c_id]):
                    combos.append((s_id, q_id, c_id))
    return combos


def explain_rejection(quest: Quest, cargo: Cargo) -> str:
    return f"(No story: the barge's {quest.verb} would not honestly endanger {cargo.phrase}, or no safe lowering fix exists.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world: friendship, curiosity, and a barge through curvature.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.quest and args.cargo:
        q, c = QUESTS[args.quest], CARGOES[args.cargo]
        if not (risky(q, c) and select_fix(q, c)):
            raise StoryError(explain_rejection(q, c))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, cargo = rng.choice(sorted(combos))
    hero = args.name or rng.choice(GIRL_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, cargo=cargo, hero=hero, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], CARGOES[params.cargo], params.hero, params.friend)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for z in sorted(q.zone):
            lines.append(asp.fact("zone", qid, z))
    for cid, c in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_region", cid, c.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        if fx.lowers:
            lines.append(asp.fact("lowers", fx.id))
    return "\n".join(lines)


ASP_RULES = r"""
risky(Q, C) :- zone(Q, Z), cargo_region(C, Z).
has_fix(Q, C) :- risky(Q, C), lowers(F).
valid(S, Q, C) :- affords(S, Q), risky(Q, C), has_fix(Q, C).
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in [StoryParams(*c) for c in valid_combos()]:
            samples.append(generate(s))
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
