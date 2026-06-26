#!/usr/bin/env python3
"""
storyworlds/worlds/barfo_aviary_cyst_rhyme_suspense_pirate_tale.py
===================================================================

A small pirate-tale story world about a child captain, a noisy aviary,
a worrisome cyst, a rhyming rescue, and a suspenseful search for a fix.

Seed tale idea:
---
A little pirate child named Nori visits the aviary with a captain's helper.
A beloved parrot named Brine has a sore cyst on one foot, and the child
wants to race around the aviary to see the birds. But the keeper warns that
the bustle could scare Brine and make the lump hurt more. Nori hears a rhyme
from the keeper, follows the clues, finds a soft wrap and a little barfo
shell charm, and helps Brine rest safely while the birds sing.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("sore", "safe", "stolen", "searched", "storm"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "fear", "care", "suspense", "relief", "pride", "worry", "song"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "daughter"}
        male = {"boy", "father", "man", "son"}
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sore"] < THRESHOLD and actor.meters["storm"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stained"] = item.meters.get("stained", 0) + 1
            out.append(f"{actor.id}'s {item.label} got splashed and shabby.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["sore"] >= THRESHOLD and ent.caretaker and ("worry", ent.id) not in world.fired:
            world.fired.add(("worry", ent.id))
            carer = world.get(ent.caretaker)
            carer.memes["worry"] += 1
            out.append(f"That made {carer.label} worry about the little cyst.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("safe", 0) >= THRESHOLD and ("relief", ent.id) not in world.fired:
            world.fired.add(("relief", ent.id))
            ent.memes["relief"] += 1
            out.append(f"{ent.id} felt relief ripple through the deck.")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("worry", _r_worry), Rule("relief", _r_relief)]


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
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": prize.meters.get("stained", 0) >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] += 1
    actor.memes["suspense"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little pirate who loved every creak of the ship and every cry of the gulls.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["song"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.gerund}, and {activity.keyword} rhymes made the day feel bright and brave."
    )


def arrive(world: World, hero: Entity, keeper: Entity, setting: Setting, activity: Activity) -> None:
    world.say(
        f"One dusky day, {hero.id} and {keeper.label} stepped into {setting.place}, where the birds blinked like tiny lanterns."
    )
    if activity.id == "search":
        world.say("The aviary had narrow paths, high perches, and plenty of places for a secret to hide.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["care"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but the keeper lifted a hand and said to look slow and soft.")


def warn(world: World, keeper: Entity, hero: Entity, prize: Entity, activity: Activity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"If you rush," {keeper.label} warned, "the {prize.label} might get jostled, and that sore cyst could ache more."'
    )
    return True


def suspense_search(world: World, hero: Entity, keeper: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"{hero.id} tiptoed past the blue-feathered birds, listening for a clue, while the wind tapped the aviary roof."
    )
    world.say(
        f"At last, {hero.id} spotted a tucked-away shelf with a soft wrap, a little salve tin, and a bright barfo shell charm."
    )
    world.facts["found_barfo"] = True
    world.facts["found_wrap"] = True


def compromise(world: World, keeper: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> Optional[Gear]:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=keeper.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, ACTIVITIES["search"], prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{keeper.label} smiled and said, "How about we {gear_def.prep} first, then {hero.id} can search safely?"'
    )
    return gear


def accept(world: World, hero: Entity, keeper: Entity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    prize.meters["safe"] = prize.meters.get("safe", 0) + 1
    world.say(
        f"{hero.id} grinned, gave a tiny pirate bow, and helped {keeper.label} wrap the sore foot."
    )
    world.say(
        f"With the {gear_def.label} in place, the little barfo charm jingled, the cyst rested easy, and the birds sang a soft sea-song."
    )


SETTING = Setting(place="the aviary", indoors=True, affords={"search", "care", "rhyme"})
ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search the aviary",
        gerund="searching the aviary",
        rush="rush through the aviary",
        mess="storm",
        soil="shaken",
        zone={"feet", "torso"},
        keyword="barfo",
        tags={"barfo", "aviary"},
    ),
    "care": Activity(
        id="care",
        verb="care for the parrot",
        gerund="caring for the parrot",
        rush="hurry to the perch",
        mess="sore",
        soil="hurt",
        zone={"feet"},
        keyword="cyst",
        tags={"cyst"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="sing a rhyme",
        gerund="singing a rhyme",
        rush="burst into song",
        mess="song",
        soil="distracted",
        zone={"feet"},
        keyword="rhyme",
        tags={"rhyme"},
    ),
}

PRIZES = {
    "parrot": Prize(
        label="parrot",
        phrase="a proud sea parrot",
        type="parrot",
        region="feet",
    ),
    "shell": Prize(
        label="shell",
        phrase="a bright shell token",
        type="shell",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="soft_wrap",
        label="a soft wrap",
        covers={"feet"},
        guards={"sore", "storm"},
        prep="lay a soft wrap by the perch",
        tail="laid a soft wrap by the perch",
    ),
    Gear(
        id="quiet_boots",
        label="quiet deck boots",
        covers={"feet"},
        guards={"storm"},
        prep="put on quiet deck boots",
        tail="put on quiet deck boots",
        plural=True,
    ),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    keeper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="aviary", activity="care", prize="parrot", name="Nori", keeper="keeper"),
    StoryParams(place="aviary", activity="search", prize="parrot", name="Mara", keeper="captain"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        'Write a short pirate tale for a young child with the words "barfo", "aviary", and "cyst".',
        f"Tell a suspenseful rhyme-riddled story where {hero.id} wants to {act.verb} and help the {prize.label}.",
        f"Write a gentle pirate story in which the aviary holds a worry, then a clever fix, then a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, keeper, prize, act = f["hero"], f["keeper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to the aviary with {keeper.label}, where the birds and the salty air made the day feel like a pirate adventure.",
        ),
        QAItem(
            question=f"What was making the {prize.label} hard to ignore?",
            answer=f"The {prize.label} had a sore cyst, so everyone had to move gently and keep the little bird calm.",
        ),
        QAItem(
            question=f"What did {hero.id} find during the suspenseful search?",
            answer="The search turned up a soft wrap, a little salve tin, and a bright barfo shell charm on a hidden shelf.",
        ),
        QAItem(
            question=f"How did the story end for {prize.label}?",
            answer=f"By the end, the {prize.label} was wrapped safely, the cyst could rest, and the aviary sounded peaceful instead of tense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aviary?",
            answer="An aviary is a place built for birds, with perches, safe walls, and room for wings to flutter.",
        ),
        QAItem(
            question="What is a cyst?",
            answer="A cyst is a small lump or bump under the skin, and if it is sore, it can make moving uncomfortable.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words end with matching sounds, like 'star' and 'far' or 'boat' and 'coat'.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when a problem has not been solved yet.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nori", keeper_type: str = "keeper") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the keeper"))
    prize = world.add(Entity(
        id=prize_cfg.type,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=keeper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts.update(hero=hero, keeper=keeper, prize=prize, activity=activity, setting=setting)

    introduce(world, hero)
    loves_activity(world, hero, activity)
    world.say(f"The keeper watched over the birds, especially the one with the sore cyst.")
    world.para()
    arrive(world, hero, keeper, setting, activity)
    wants(world, hero, activity)
    warn(world, keeper, hero, prize, activity)
    suspense_search(world, hero, keeper, activity, prize)
    world.para()
    gear_def = compromise(world, keeper, hero, prize, GEAR[0])
    if gear_def:
        accept(world, hero, keeper, prize, gear_def)
    world.facts["gear"] = gear_def
    world.facts["resolved"] = gear_def is not None
    return world


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: that activity would not threaten the prize in this world, so there is no honest worry to solve.)"
    if not select_gear(activity, prize):
        return "(No story: there is no gear in this world that both fits the at-risk spot and keeps the mess away.)"
    return "(No story: the chosen options do not make a reasonable pirate problem.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "aviary"))
    lines.append(asp.fact("affords", "aviary", "search"))
    lines.append(asp.fact("affords", "aviary", "care"))
    lines.append(asp.fact("affords", "aviary", "rhyme"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
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
valid_story(Place,A,P,G) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P), wears(G,P).
valid_combo(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid_story/4.
#show valid_combo/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in [("aviary", SETTING)]:
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld in an aviary with rhyme and suspense.")
    ap.add_argument("--place", choices=["aviary"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=["keeper", "captain"])
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
    _, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Nori", "Mara", "Pip", "Sail", "Tessa"])
    keeper = args.keeper or rng.choice(["keeper", "captain"])
    return StoryParams(place="aviary", activity=activity, prize=prize, name=name, keeper=keeper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.keeper)
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
        print(f"{len(triples)} compatible combos ({len(stories)} with character selection):\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
