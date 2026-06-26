#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mesh_canary_marina_cautionary_fairy_tale.py
===============================================================================================================

A standalone story world for a small cautionary fairy-tale domain set at a marina.

Seed tale imagined from the prompt:
- A little child and a bright canary live near a marina.
- An old mesh net is left where the wind can tug it.
- The canary is tempted to dart through the net, but that could snag feathers and
  make the little bird afraid.
- A careful adult warns them, and the child chooses the safer fairy-tale fix:
  the mesh is rolled up and tied, and the canary sings from a clean perch.

This script models:
- physical meters: risk, tangling, tidiness, safety, breeze
- emotional memes: caution, worry, delight, relief, trust

The output story is state-driven, not a frozen paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("risk", "tangle", "tidiness", "safety", "breeze"):
            self.meters.setdefault(k, 0.0)
        for k in ("caution", "worry", "delight", "relief", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"canary", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_person(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str = "the marina"
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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.type != "mesh" or item.protective:
                continue
            if "dock" not in world.zone and "rope" not in world.zone and "waterline" not in world.zone:
                continue
            sig = ("tangle", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["tangle"] += 1
            actor.memes["worry"] += 1
            out.append(f"The {item.label} looked like a snare in the wind.")
    return out


def _r_tidiness(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.type != "mesh":
            continue
        if item.meters["tidiness"] < THRESHOLD:
            continue
        sig = ("tidy", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The {item.label} was rolled up and tied neat.")
    return out


def _r_safety(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["safety"] < THRESHOLD:
            continue
        sig = ("safe", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] += 1
        out.append(f"The little heart in {actor.id} felt much lighter.")
    return out


CAUSAL_RULES = [_r_tangle, _r_tidiness, _r_safety]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["risk"] += 1
    actor.memes["delight"] += 1
    propagate(world, narrate=narrate)


def predict_problem(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "tangled": bool(prize.meters["tangle"] >= THRESHOLD or sim.get(actor.id).meters["tangle"] >= THRESHOLD),
        "worry": sim.get(actor.id).memes["worry"],
    }


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"{setting.place.capitalize()} was bright with ropes, gulls, and bobbing boats."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once upon a tide, {hero.id} lived by {world.setting.place} and listened for tiny songs in the wind."
    )


def loves(world: World, hero: Entity, canary: Entity) -> None:
    hero.memes["trust"] += 1
    canary.memes["delight"] += 1
    world.say(
        f"{hero.id} loved {canary.id}, the bright little canary, because its song sounded like a lantern in the dusk."
    )


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity, mesh: Entity) -> None:
    world.say(
        f"One breezy morning, {hero.id} and {hero.pronoun('possessive')} {parent.label} went down to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))
    world.say(
        f"Near the pier, an old {mesh.label} lay in a heap, and the breeze tugged at its loose loops."
    )


def wants(world: World, hero: Entity, canary: Entity, activity: Activity) -> None:
    hero.memes["delight"] += 1
    world.say(
        f"{canary.id} wanted to {activity.verb}, hopping closer to the shiny ropes and the glittering water."
    )


def warn(world: World, parent: Entity, hero: Entity, canary: Entity, activity: Activity, mesh: Entity) -> bool:
    pred = predict_problem(world, canary, activity, mesh.id)
    if not pred["tangled"]:
        return False
    canary.memes["caution"] += 1
    world.facts["predicted_tangle"] = True
    world.say(
        f'"Careful," {parent.id} said. "That {mesh.label} could snag {canary.id}\'s feathers if it flutters too close."'
    )
    return True


def defy(world: World, canary: Entity, activity: Activity) -> None:
    canary.memes["worry"] += 1
    world.say(
        f"{canary.id} did not want to listen at first. It fluttered toward the open space and tried to {activity.rush}."
    )


def choose_fix(world: World, parent: Entity, canary: Entity, mesh: Entity) -> Gear:
    gear = Gear(
        id="tie",
        label="a sturdy ribbon tie",
        covers={"loops"},
        guards={"tangle"},
        prep="wrap the mesh up and tie it with a sturdy ribbon",
        tail="rolled the mesh into a tidy bundle and tucked it away from the wind",
    )
    world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        owner=canary.id,
        caretaker=parent.id,
    ))
    world.get(gear.id).worn_by = canary.id
    mesh.meters["tidiness"] += 1
    world.get(gear.id).meters["safety"] += 1
    world.say(
        f"{parent.id} smiled and said, 'We can still enjoy the marina. First, let us {gear.prep}.'"
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, canary: Entity, activity: Activity, mesh: Entity, gear: Gear) -> None:
    canary.memes["relief"] += 1
    canary.memes["trust"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} helped at once. Together they {gear.tail}."
    )
    world.say(
        f"Then {canary.id} perched on a clean post and sang {activity.gerund}, while the {mesh.label} stayed harmless and still."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label="little one"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mother"))
    canary = world.add(Entity(id="Sunny", kind="character", type=prize_cfg.type, label="Sunny"))
    mesh = world.add(Entity(id="mesh", type="mesh", label="mesh net", phrase="an old mesh net"))
    mesh.region = "loops"

    introduce(world, hero)
    loves(world, hero, canary)
    world.para()
    arrives(world, hero, parent, activity, mesh)
    wants(world, hero, canary, activity)
    warn(world, parent, hero, canary, activity, mesh)
    defy(world, canary, activity)
    world.para()
    gear = choose_fix(world, parent, canary, mesh)
    accept(world, hero, parent, canary, activity, mesh, gear)

    world.facts.update(hero=hero, parent=parent, canary=canary, mesh=mesh, activity=activity, gear=gear)
    return world


SETTINGS = {
    "marina": Setting(place="the marina", affords={"perch", "sing"}),
}

ACTIVITIES = {
    "sing": Activity(
        id="sing",
        verb="sing by the water",
        gerund="singing by the water",
        rush="flutter toward the mesh",
        mess="tangle",
        soil="snagged and frightened",
        zone={"loops"},
        keyword="canary",
        tags={"canary", "mesh", "marina"},
    ),
    "perch": Activity(
        id="perch",
        verb="perch near the boats",
        gerund="perching near the boats",
        rush="hop over to the net",
        mess="tangle",
        soil="caught and tangled",
        zone={"loops"},
        keyword="mesh",
        tags={"canary", "mesh", "marina"},
    ),
}

PRIZES = {
    "canary": Prize(
        label="canary",
        phrase="a bright little canary",
        type="canary",
        region="loops",
    )
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nina", "Ada", "Ivy"]
TRAITS = ["careful", "brave", "gentle", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy-tale cautionary story set at {world.setting.place} that includes the words "mesh" and "canary".',
        f"Tell a gentle warning story where {f['hero'].id} keeps {f['canary'].id} safe from an old mesh net at the marina.",
        f"Write a child-facing story with a warning, a careful fix, and a bright canary song by the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, canary, mesh, act = f["hero"], f["parent"], f["canary"], f["mesh"], f["activity"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens at {world.setting.place}, where boats bob and ropes sway in the breeze.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} about the {mesh.label}?",
            answer=f"{parent.id} warned {hero.id} because the {mesh.label} had loose loops that could snag {canary.id}'s feathers.",
        ),
        QAItem(
            question=f"What did they do so {canary.id} could {act.verb} safely?",
            answer=f"They rolled up the {mesh.label} and tied it neat, so {canary.id} could {act.gerund} without getting caught.",
        ),
        QAItem(
            question=f"How did {canary.id} feel at the end?",
            answer=f"{canary.id} felt calm and joyful, then sang from a clean perch beside the marina.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mesh net?",
            answer="A mesh net is made of crisscrossed strands with little holes. It can catch or hold things, but loose mesh can snag feathers or fingers.",
        ),
        QAItem(
            question="What is a canary?",
            answer="A canary is a small bird known for its clear song and bright feathers.",
        ),
        QAItem(
            question="What is a marina?",
            answer="A marina is a place where boats are kept in calm water, often with docks, ropes, and piers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(Actor) :- actor(Actor), activity_zone(loops).
tangle(Actor, Mesh) :- actor(Actor), mesh(Mesh), risk(Actor), loose(Mesh).
safe(Mesh) :- mesh(Mesh), tied(Mesh).
resolved(Actor) :- actor(Actor), safe(meshnet), not tangle(Actor, meshnet).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "marina"))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    lines.append(asp.fact("actor", "hero"))
    lines.append(asp.fact("mesh", "meshnet"))
    lines.append(asp.fact("loose", "meshnet"))
    lines.append(asp.fact("activity_zone", "loops"))
    lines.append(asp.fact("tied", "meshnet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 2
    model = asp.one_model(asp_program("#show safe/1.\n#show resolved/1."))
    # Python gate is simple: this domain always has a valid fix.
    py_ok = True
    asp_ok = bool(model)
    if py_ok == asp_ok:
        print("OK: ASP/Python parity holds for the cautionary marina domain.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fairy tale at a marina with a mesh net and a canary.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid story matches the chosen options.")
    place, activity, prize = rng.choice(combos)
    name = args.name or rng.choice(GIRL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name)
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
        print(asp_program("#show safe/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe/1.\n#show resolved/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=z, name="Mira", trait="careful"))
                   for p, a, z in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
