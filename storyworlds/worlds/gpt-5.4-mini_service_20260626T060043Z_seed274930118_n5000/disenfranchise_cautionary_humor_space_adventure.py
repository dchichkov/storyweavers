#!/usr/bin/env python3
"""
A small space-adventure storyworld with a cautionary/humorous civic twist.

Premise:
- A young crew member loves a noisy, playful activity on a tiny space station.
- That activity can make a special item messy and can also risk losing trust.
- The captain warns that if the child keeps ignoring the rules, the crew could
  be disenfranchised from the next vote in the mission hall.
- A simple, physical compromise keeps the fun and protects the important item.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
        for k in ["dusty", "sticky", "bent", "clean", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "trust", "worry", "conflict", "defiance", "pride", "humor"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    place: str = "the little space station"
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
    def __init__(self, station: Station) -> None:
        self.station = station
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
        import copy as _copy

        clone = World(self.station)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            for mess in ("sticky", "dusty"):
                if actor.meters[mess] < THRESHOLD:
                    continue
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["clean"] = 0
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.caretaker and (item.meters["sticky"] >= THRESHOLD or item.meters["dusty"] >= THRESHOLD):
            sig = ("work", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            caretaker = world.get(item.caretaker)
            caretaker.meters["workload"] += 1
            out.append(f"That would mean more work for {caretaker.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] >= THRESHOLD and actor.memes["worry"] >= THRESHOLD:
            sig = ("conflict", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["conflict"] += 1
            return ["__conflict__"]
    return []


RULES = [_r_soil, _r_workload, _r_conflict]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and (prize.meters["sticky"] >= THRESHOLD or prize.meters["dusty"] >= THRESHOLD)),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.station.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved everything bright and buzzy aboard the station.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["humor"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because it made the hallway feel like a joke told by the stars.")


def prize_intro(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["trust"] += 1
    prize.worn_by = hero.id
    world.say(f"Before the mission bell rang, {hero.id}'s {prize.label} shone like {prize.phrase}.")


def arrive(world: World, hero: Entity, captain: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {captain.label} went to {world.station.place}.")
    world.say(f"The {world.station.place.removeprefix('the ')} was humming, and the control room waited nearby.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} eyes kept drifting to the shiny vote board.")


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    word = "disenfranchise"
    world.say(
        f'"If you keep using the console that way," {captain.label} said, '
        f'"the council might {word} you from the next crew vote, and I will have to clean up the mess."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.id} made a face and tried to {activity.rush}, even though the warning was very clear.")


def clash(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["conflict"] += 1
    world.say(f"{captain.label} held up a hand, and {hero.id} stopped with a tiny grumble.")


def compromise(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f'{captain.label} smiled. "How about we {gear_def.prep} and then {activity.verb} together?"')
    return gear_def


def resolve(world: World, hero: Entity, captain: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} laughed, nodded, and hugged {hero.pronoun('possessive')} {captain.label}.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{hero.pronoun('possessive')} {prize.label} stayed clean, and the vote board glittered peacefully."
    )


def tell(station: Station, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip", hero_type: str = "boy", parent_type: str = "captain", hero_traits: Optional[list[str]] = None) -> World:
    world = World(station)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "silly"])))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(id="badge", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    prize_intro(world, hero, prize)

    world.para()
    arrive(world, hero, captain, activity)
    warn(world, captain, hero, activity, prize)
    defies(world, hero, activity)
    clash(world, captain, hero)

    world.para()
    gear_def = compromise(world, captain, hero, activity, prize)
    if gear_def:
        resolve(world, hero, captain, activity, prize, gear_def)

    world.facts.update(hero=hero, captain=captain, prize=prize, activity=activity, station=station, gear=gear_def)
    return world


STATION = Station(place="the little space station", affords={"stickerstorm", "dustdive"})


ACTIVITIES = {
    "stickerstorm": Activity(
        id="stickerstorm",
        verb="stick bright vote stickers on the console",
        gerund="sticking bright stickers everywhere",
        rush="dash toward the vote board",
        mess="sticky",
        soil="sticky",
        zone={"torso"},
        keyword="sticker",
        tags={"stickers", "vote", "sticky", "humor"},
    ),
    "dustdive": Activity(
        id="dustdive",
        verb="scoop moon-dust into tiny towers",
        gerund="building moon-dust towers",
        rush="run toward the cargo bin",
        mess="dusty",
        soil="dusty",
        zone={"torso"},
        keyword="dust",
        tags={"dust", "space", "cautionary"},
    ),
}


PRIZES = {
    "badge": Prize(label="mission badge", phrase="a shiny silver mission badge", type="badge", region="torso"),
    "patch": Prize(label="station patch", phrase="a bright patch with a rocket on it", type="patch", region="torso"),
}


GEAR = [
    Gear(
        id="clearcover",
        label="a clear cover",
        covers={"torso"},
        guards={"sticky"},
        prep="put a clear cover over the console badge first",
        tail="slid the clear cover on and carefully used the stickers",
    ),
    Gear(
        id="dustcloak",
        label="a dust cloak",
        covers={"torso"},
        guards={"dusty"},
        prep="put on a dust cloak first",
        tail="pulled on the dust cloak and built the towers without a sneeze",
    ),
]


GIRL_NAMES = ["Nova", "Mira", "Zia", "Luna", "Pia", "Rin"]
BOY_NAMES = ["Pip", "Jax", "Bo", "Tao", "Finn", "Kai"]
TRAITS = ["curious", "silly", "brave", "bouncy", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, station in {"station": STATION}.items():
        for act_id in station.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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
    "disenfranchise": [(
        "What does disenfranchise mean?",
        "To disenfranchise someone means to take away their right to vote or help choose what happens."
    )],
    "vote": [(
        "What is a vote?",
        "A vote is a choice people make to help decide something together."
    )],
    "sticker": [(
        "Why can stickers make a mess?",
        "Stickers can get stuck in the wrong place and leave sticky bits behind."
    )],
    "dust": [(
        "What is moon dust?",
        "Moon dust is very fine powdery dirt that can drift and cling to things."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, act = f["hero"], f["captain"], f["activity"]
    return [
        f'Write a short space-adventure story for a young child about {hero.id}, a {hero.type}, and a warning about being disenfranchised from a crew vote.',
        f"Tell a cautionary but funny story where {hero.id} wants to {act.verb} on {world.station.place}, but the captain helps with a safer plan.",
        f'Write a simple story that uses the word "disenfranchise" in a kid-friendly way and ends with the hero still getting to play.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.station.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {f['captain'].label} warn {hero.id} about the crew vote?",
            answer="The captain warned that if the messy plan kept going, the child could lose trust and be disenfranchised from the next vote.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {prize.label} need during the story?",
            answer=f"The {prize.label} needed to stay clean while {hero.id} played.",
        ),
    ]
    gear = f.get("gear")
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"It protected the {prize.label} so {hero.id} could keep playing without making a mess.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags or tag == "disenfranchise":
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("station", "station"))
    for a in sorted(STATION.affords):
        lines.append(asp.fact("affords", "station", a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
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
    ap = argparse.ArgumentParser(description="A cautionary, humorous space-adventure storyworld.")
    ap.add_argument("--place", choices=["station"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
            raise StoryError("No valid story: that activity would not have a sensible cautionary fix.")
    combos = valid_combos()
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, act_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place="station",
        activity=act_id,
        prize=prize_id,
        name=name,
        gender=gender,
        parent="captain",
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(STATION, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, [params.trait, "stubborn"])
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="station", activity="stickerstorm", prize="badge", name="Pip", gender="boy", parent="captain", trait="curious"),
            StoryParams(place="station", activity="dustdive", prize="patch", name="Nova", gender="girl", parent="captain", trait="silly"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
