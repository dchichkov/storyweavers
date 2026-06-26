#!/usr/bin/env python3
"""
storyworlds/worlds/footie_sound_effects_folk_tale.py
=====================================================

A small story world about footie, sound effects, and a folk-tale style turn:
a child wants to kick a ball, a careful elder worries about a cherished item,
and the story finds a sensible way to play without harm.

The world is intentionally tiny and state-driven. The hero's wish to play footie
pushes on the world model, the warning comes from a predicted mess or damage,
and the ending image proves what changed.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mud": 0.0, "scratch": 0.0, "dust": 0.0, "broken": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "love": 0.0, "worry": 0.0, "defiance": 0.0, "peace": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    sounds: list[str] = field(default_factory=list)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    mess: str
    risk: str
    zone: set[str]
    keyword: str = "footie"


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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mud"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mud"] += 1
            item.meters["scratch"] += 1
            out.append(f"Softly, softly, {item.label} got muddy from the footie play.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["mud"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more washing for {caretaker.label}.")
    return out


def _r_worry(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_mess, _r_work, _r_worry):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"damaged": prize.meters["mud"] >= THRESHOLD, "workload": sum(e.meters["workload"] for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["mud"] += 1
    actor.memes["joy"] += 1
    if narrate:
        world.say(f"Then came the {activity.sound}: {activity.gerund} made the lane feel alive.")
    propagate(world, narrate=narrate)


def setting_line(place: Place, activity: Activity) -> str:
    if place.indoors:
        return f"Inside {place.name}, the boards were still and the air waited for a game."
    return f"At {place.name}, the grass was bright, and the wind went whisper, whisper."


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(place: Place, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["love"] += 1
    hero.memes["joy"] += 1
    world.say(f"Once in a little village, {hero.id} was a {trait} {hero.type} who loved the game of footie.")
    world.say(f"{hero.pronoun().capitalize()} liked the far-off thump-thump of a ball and the merry shout of boots on stone.")
    world.say(f"{hero.id}'s {('mother' if parent_type == 'mother' else 'father')} had bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.it()} dearly and wore {prize.it()} as if it had been spun for {hero.pronoun('object')} by the moon.")

    world.para()
    world.say(setting_line(place, activity))
    world.say(f"{hero.id} wanted to {activity.verb}, and the whole field seemed to answer, {activity.sound}!")
    world.say(f"But {hero.pronoun('possessive')} {('mother' if parent_type == 'mother' else 'father')} frowned, for the {activity.keyword} could {activity.risk} {prize.it()}.")

    predicted = predict_damage(world, hero, activity, prize.id)
    if predicted["damaged"]:
        world.say(f'"If you rush to the ball," said {parent.label}, "your {prize.label} will get {activity.risk}."')
        world.facts["predicted_damage"] = activity.risk
        world.facts["predicted_workload"] = predicted["workload"]
        hero.memes["defiance"] += 1
        world.say(f"{hero.id} heard that, but the wish to play still hopped like a hare in the chest.")
        world.say(f"{hero.id} tried to {activity.rush}, {activity.sound}, {activity.sound}, {activity.sound}!")
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No fair compromise exists for this footie story.")
        gear_ent = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
        ))
        gear_ent.worn_by = hero.id
        if predict_damage(world, hero, activity, prize.id)["damaged"]:
            gear_ent.worn_by = None
            del world.entities[gear_ent.id]
            raise StoryError("The chosen gear did not truly protect the prize.")
        world.para()
        hero.memes["joy"] += 1
        hero.memes["love"] += 1
        hero.memes["peace"] += 1
        hero.memes["defiance"] = 0
        world.say(f"Then the {parent_type} smiled a folk-tale smile and said, {gear.prep}.")
        world.say(f"{hero.id} agreed at once, and they {gear.tail}.")
        world.say(f"After that, {hero.id} was {activity.gerund}, while {prize.label} stayed clean and bright.")
        world.say(f"And so the field sang {activity.sound}, and the story ended with a happy ball and a clean prize.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_ent, resolved=True, place=place)
    else:
        world.say(f"So {hero.id} played carefully, and the old {prize.label} stayed safe.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=None, resolved=False, place=place)
    return world


SETTINGS = {
    "village_green": Place(name="the village green", indoors=False, sounds=["thump-thump", "tap-tap"]),
    "barn_loft": Place(name="the barn loft", indoors=True, sounds=["bump", "pat-pat"]),
}

ACTIVITIES = {
    "footie": Activity(
        id="footie",
        verb="play footie",
        gerund="playing footie",
        rush="dash after the ball",
        sound="thump-thump",
        mess="mud",
        risk="get muddy",
        zone={"feet", "legs"},
        keyword="footie",
    )
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a red wool cloak", type="cloak", region="torso"),
    "boots": Prize(label="boots", phrase="good black boots", type="boots", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="old_boots",
        label="old mud boots",
        covers={"feet"},
        guards={"mud"},
        prep="put on the old mud boots first",
        tail="went back to the green in the old mud boots",
        plural=True,
    ),
    Gear(
        id="play_girdle",
        label="a play-girdle",
        covers={"legs"},
        guards={"mud"},
        prep="tie on a play-girdle first",
        tail="returned to the lane with the play-girdle on",
    ),
]

NAMES = ["Mara", "Toby", "Nell", "Pip", "Rowan", "Aster"]
TRAITS = ["brave", "curious", "cheerful", "stubborn", "lively", "gentle"]


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
    "footie": [("What is footie?", "Footie is a game where people kick a ball and try to score.")],
    "mud": [("What is mud?", "Mud is wet earth that clings to shoes and clothes.")],
    "boots": [("What are boots for?", "Boots protect your feet and help keep them dry or safe.")],
    "cloak": [("What is a cloak?", "A cloak is a loose outer garment that covers the body and keeps it warm.")],
}

ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
protected(A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protected(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in place.sounds:
            lines.append(asp.fact("sound", pid, a))
        for a in [ACTIVITIES["footie"].id]:
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, pr.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place_id, act_id, prize_id))
    return combos


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child that includes the word "{f["activity"].keyword}" and a sound like "{f["activity"].sound}".',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} but a careful {f['parent'].type} worries about {f['prize'].label}.",
        f"Write a story about footie, a little warning, and a happy compromise that ends with a clean {f['prize'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    qas = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.place.name}?",
            answer=f"{hero.id} wanted to {activity.verb}. The story keeps returning to that wish, {activity.sound}, like a drumbeat.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because footie could get the {prize.label} {activity.risk}. That would have made extra work and ruined the clean look of the prize.",
        ),
    ]
    if f.get("gear") is not None:
        gear: Entity = f["gear"]
        qas.append(
            QAItem(
                question=f"How did the family make it safe for {hero.id} to play?",
                answer=f"They used {gear.label} first, so {hero.id} could keep {prize.label} safe and still enjoy {activity.gerund}.",
            )
        )
    qas.append(
        QAItem(
            question=f"What sound filled the field while {hero.id} played?",
            answer=f"The field rang with {activity.sound}. That sound made the tale feel lively and merry.",
        )
    )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"footie", "mud", "boots", "cloak"} if any(e.type == "cloak" for e in world.entities.values()) else {"footie", "mud", "boots"}
    out: list[QAItem] = []
    for tag in ("footie", "mud", "boots", "cloak"):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: footie, sound effects, and a folk-tale compromise.")
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
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        gender = sorted(PRIZES[prize].genders)[0]
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
    StoryParams(place="village_green", activity="footie", prize="cloak", name="Mara", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="village_green", activity="footie", prize="boots", name="Toby", gender="boy", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
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
