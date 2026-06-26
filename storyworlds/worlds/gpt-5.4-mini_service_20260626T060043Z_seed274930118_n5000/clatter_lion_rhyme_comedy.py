#!/usr/bin/env python3
"""
storyworlds/worlds/clatter_lion_rhyme_comedy.py
================================================

A small comedy storyworld with rhyme, a lion, and the trouble of clatter.

Seed tale idea:
---
A young lion loves to make a grand clatter while he performs silly little
rhymes. His loud fun keeps bumping into breakable things. A grown-up notices
the risk, tries to stop the noisy fuss, and then offers a quieter stage so the
lion can keep the joke without making a mess.

World idea:
---
- The lion has emotional meters for pride, delight, embarrassment, and relief.
- Loud activities raise clatter and may threaten nearby fragile things.
- A sensible compromise uses soft gear or a quieter prop so the comic rhyme can
  continue without a crash.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "lion":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"lion", "child"})


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


def _apply_clatter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("clatter", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("clatter", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["jolt"] = item.meters.get("jolt", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"The {item.label} gave a nervous little wobble.")
    return out


def _apply_embarrassment(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("clatter", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("embarrassed", 0.0) >= THRESHOLD:
            continue
        actor.memes["embarrassed"] = 1.0
        out.append(f"{actor.id} blinked and gave a sheepish grin.")
    return out


CAUSAL_RULES = [_apply_clatter, _apply_embarrassment]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world_copy(world)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def world_copy(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    return clone


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This place cannot host that activity.")
    world.zone = set(activity.zone)
    actor.meters["clatter"] = actor.meters.get("clatter", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little lion with a big grin and an even bigger love of rhyme. "
        f"He liked to roar, to snore, and then ask for one joke more."
    )


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} loved to {activity.verb}. {activity.rhyme} "
        f"made {hero.pronoun('possessive')} whiskers twitch with glee."
    )


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One bright day,"
    world.say(
        f"{day} {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}."
    )
    world.say(f"The place felt ready for play, but not for a booming display.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} at once, with a bounce and a pounce."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you make that {activity.keyword} clatter, your {prize.label} will get {activity.soil}," '
        f"{parent.pronoun('possessive')} {parent.label} said. "
        f'"We need a calmer pattern."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{hero.id} tried to {activity.rush}, because a lion likes to feel bold."
    )


def ask_for_help(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["embarrassed"] = hero.memes.get("embarrassed", 0.0) + 1
    world.say(
        f"{parent.id} held up a hand and laughed softly. "
        f'"Let us not make a crashy splashy dashy mess," {parent.pronoun("possessive")} said.'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
            worn_by=hero.id,
        )
    )
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.id} smiled and said, "How about we {gear_def.prep} and still {activity.verb}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["embarrassed"] = 0.0
    world.say(
        f"{hero.id} gave a tiny cheer. "
        f'"Yes, yes, no stress!" {hero.pronoun()} said with a grin.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize.label} stayed clean, and the room had a comic beat without a crash."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Leo",
    parent_name: str = "Mara",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="lion", label="the lion"))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent", label="the grown-up"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    intro(world, hero)
    loves(world, hero, activity)
    world.say(f"{parent.id} had brought {prize.phrase}, and it sat near the action like a shy little star.")
    world.para()
    arrives(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    ask_for_help(world, parent, hero, activity)
    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "hall": Setting(place="the hall", indoor=True, affords={"drum", "parade"}),
    "stage": Setting(place="the stage", indoor=True, affords={"drum", "parade"}),
    "yard": Setting(place="the yard", indoor=False, affords={"drum", "parade"}),
}

ACTIVITIES = {
    "drum": Activity(
        id="drum",
        verb="beat on the drum",
        gerund="beating on the drum",
        rush="rush to the drum",
        mess="clatter",
        soil="jiggly and noisy",
        zone={"floor", "table"},
        keyword="clatter",
        rhyme="Clatter, patter, chatter, splatters; the lion laughed and said, 'It matters!'",
        tags={"clatter", "noise"},
    ),
    "parade": Activity(
        id="parade",
        verb="lead a tiny parade",
        gerund="parading and singing",
        rush="march in a mighty parade",
        mess="clatter",
        soil="jiggly and noisy",
        zone={"floor"},
        keyword="clatter",
        rhyme="March and lurch, but softly now; the lion can still take a bow.",
        tags={"clatter", "noise"},
    ),
}

PRIZES = {
    "vase": Prize(label="vase", phrase="a glass vase", type="vase", region="table"),
    "stack": Prize(label="stack of cups", phrase="a stack of cups", type="cups", region="table", plural=True),
    "lantern": Prize(label="lantern", phrase="a little lantern", type="lantern", region="floor"),
}

GEAR = [
    Gear(
        id="softpaws",
        label="soft paw slippers",
        covers={"floor"},
        guards={"clatter"},
        prep="put on soft paw slippers first",
        tail="walked back in soft paw slippers",
    ),
    Gear(
        id="feltsticks",
        label="felt drumsticks",
        covers={"table", "floor"},
        guards={"clatter"},
        prep="switch to felt drumsticks",
        tail="took up the felt drumsticks",
    ),
]

GIRLISH = ["Mara", "Nia", "Pip", "June"]
BOYISH = ["Leo", "Toby", "Milo", "Otis"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short funny story about a lion named {hero.id} who loves "{act.keyword}" and keeps making clatter.',
        f"Tell a rhyming comedy where {hero.id} wants to {act.verb} near {prize.phrase}, but {parent.id} worries.",
        f"Write a child-friendly story where the lion learns a quieter way to play and the rhyme still stays lively.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little lion who loves rhyme and comic clatter.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} while making a silly show of it.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=f"{parent.id} worried because the clatter could leave the {prize.label} {act.soil}.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the grown-up help {hero.id} keep playing without trouble?",
                answer=f"They used {gear.label} so {hero.id} could keep going without ruining the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy and relieved, because the joke stayed fun and the room stayed safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is clatter?",
            answer="Clatter is a noisy, rattly sound made by hard things bumping or tapping together.",
        ),
        QAItem(
            question="What is a lion?",
            answer="A lion is a big cat with a strong voice, a fluffy mane, and a very bold walk.",
        ),
        QAItem(
            question="What does rhyme mean?",
            answer="Rhyme means words or lines end with similar sounds, like play and stay.",
        ),
    ]


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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", activity="drum", prize="vase", name="Leo", parent="Mara"),
    StoryParams(place="stage", activity="parade", prize="stack", name="Milo", parent="Mara"),
    StoryParams(place="yard", activity="drum", prize="lantern", name="Otis", parent="Mara"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.label}.)"
    return f"(No story: there is no gear that keeps the {prize.label} safe from {activity.gerund}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming comedy storyworld about a lion and clatter.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(BOYISH)
    parent = args.parent or "Mara"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t in combos:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
