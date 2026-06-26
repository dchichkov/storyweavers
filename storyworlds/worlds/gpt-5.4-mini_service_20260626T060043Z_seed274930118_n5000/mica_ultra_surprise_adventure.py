#!/usr/bin/env python3
"""
storyworlds/worlds/mica_ultra_surprise_adventure.py
===================================================

A small adventure storyworld about a child on a surprise outing to find mica,
with a little tension, a careful turn, and a bright ending image.

Premise:
- A child loves adventure.
- They are taken on a surprise trip to a place where mica can be found.
- Something important could get scratched, spilled, or lost during the outing.

Turn:
- The adult notices the risk and offers a safer way to continue.

Resolution:
- The child accepts the helper gear, the adventure continues, and the mica
  shines in the ending.

The world is intentionally compact: fewer combinations, but each one is
consistent and narratively complete.
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

    def __post_init__(self) -> None:
        for k in ("scratched", "dusty", "wet", "dirty", "found", "moved"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "wonder", "surprise", "worry", "trust", "patience"):
            self.memes.setdefault(k, 0.0)

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
class Site:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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
    def __init__(self, site: Site) -> None:
        self.site = site
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


def _step_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["wonder"] += 1
    actor.memes["surprise"] += 1


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters["scratched"] >= THRESHOLD:
                for item in world.worn_items(actor):
                    if item.protective or item.region not in world.zone:
                        continue
                    if world.covered(actor, item.region):
                        continue
                    sig = ("scratch", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["scratched"] += 1
                    item.meters["dirty"] += 1
                    changed = True


def risk_prize(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for site_id, site in SITES.items():
        for act_id in site.affordances:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if risk_prize(act, prize) and select_gear(act, prize):
                    combos.append((site_id, act_id, prize_id))
    return combos


def tell(site: Site, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         parent_type: str, trait: str) -> World:
    world = World(site)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        meters={"scratched": 0.0, "dusty": 0.0, "wet": 0.0, "dirty": 0.0},
        memes={"joy": 0.0, "wonder": 0.0, "surprise": 0.0, "worry": 0.0, "trust": 0.0, "patience": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    hero.memes["joy"] += 1
    hero.memes["surprise"] += 1
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved adventure.")
    world.say(f"{hero.id}'s {parent.label} brought {hero.pronoun('object')} a surprise outing.")
    world.say(f"They packed {hero.pronoun('object')} {prize.phrase} because {hero.id} liked it so much.")
    prize.worn_by = hero.id

    world.para()
    world.say(f"One bright day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {site.place}.")
    world.say(f"{hero.id} wanted to {activity.verb} right away, and the surprise made {hero.pronoun('object')} grin.")
    world.say(f"The mica trail looked shiny, like little bits of evening light.")
    hero.meters[activity.mess] += 1
    if risk_prize(activity, prize):
        hero.memes["worry"] += 1
        world.say(f"But {hero.pronoun('possessive')} {prize.label} could get scratched in the rough path.")
    hero.meters["scratched"] += 1
    propagate(world)

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable gear exists for this story.")
    helper = world.add(Entity(
        id=gear.id, type=gear.label, label=gear.label, protective=True,
        covers=set(gear.covers), plural=gear.plural, owner=hero.id, caretaker=parent.id
    ))
    helper.worn_by = hero.id
    hero.memes["trust"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled and offered {gear.label}.")
    world.say(f'"Let\'s put this on first," {hero.pronoun("possessive")} {parent.label} said, "and then you can {activity.verb} safely."')
    world.say(f"{hero.id} agreed, because the gear covered the right spot and kept the prize safe.")
    hero.meters[activity.mess] += 1
    hero.memes["joy"] += 1
    propagate(world)

    world.para()
    world.say(f"Soon {hero.id} was {activity.gerund}, and the mica sparkled in {hero.pronoun('possessive')} hands.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {prize.label} stayed clean, and the surprise adventure turned into a happy treasure hunt.")
    world.say(f"At the end, {hero.id} held up a tiny shining piece of mica, laughing with {hero.pronoun('possessive')} {parent.label} beside {hero.pronoun('object')}.")

    world.facts.update(
        hero=hero, parent=parent, prize=prize, activity=activity, site=site, gear=gear,
        resolved=True, risky=risk_prize(activity, prize),
    )
    return world


SITES = {
    "cave": Site(place="the cave", affordances={"search"}),
    "hill": Site(place="the hill path", affordances={"climb"}),
    "creek": Site(place="the creek bank", affordances={"search"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search for mica",
        gerund="searching for mica",
        rush="run to the sparkling rocks",
        mess="dusty",
        zone={"hands", "torso"},
        keyword="mica",
        tags={"mica", "rock"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the rocky hill",
        gerund="climbing the rocky hill",
        rush="hurry up the stones",
        mess="scratched",
        zone={"feet", "legs", "hands"},
        keyword="adventure",
        tags={"rock", "adventure"},
    ),
}

PRIZES = {
    "jacket": Prize(label="jacket", phrase="a bright rain jacket", type="jacket", region="torso"),
    "hat": Prize(label="hat", phrase="a soft red hat", type="hat", region="head"),
    "pack": Prize(label="backpack", phrase="a small blue backpack", type="backpack", region="torso"),
}

GEAR = [
    Gear(id="gloves", label="work gloves", covers={"hands"}, guards={"dusty", "scratched"}, prep="put on work gloves", tail="wore the gloves for the rest of the trail"),
    Gear(id="coat", label="a sturdy coat", covers={"torso"}, guards={"scratched"}, prep="button up a sturdy coat", tail="buttoned the coat and walked on"),
    Gear(id="satchel", label="a shoulder satchel", covers={"torso"}, guards={"dusty"}, prep="switch to a shoulder satchel", tail="swung the satchel on and kept going"),
]

GIRL_NAMES = ["Maya", "Lila", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Owen"]
TRAITS = ["curious", "brave", "playful", "lively", "cheerful"]


@dataclass
class StoryParams:
    site: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short adventure story for a child named {hero.id} that includes the word "mica".',
        f"Tell a surprise adventure where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Write a gentle story about a surprise trip, a little risk, and a happy fix with simple, child-friendly language.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, site, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["site"], f["gear"]
    return [
        QAItem(
            question=f"Why was the trip a surprise for {hero.id}?",
            answer=f"It was a surprise because {hero.pronoun('possessive')} {parent.label} brought {hero.pronoun('object')} to {site.place} without telling {hero.pronoun('object')} ahead of time.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {site.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because the shiny mica trail looked exciting and the adventure felt fun.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label} offer {gear.label}?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label} saw that {hero.pronoun('possessive')} {prize.label} could get scratched on the rough path, so the gear helped keep it safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} was happily {act.gerund}, {prize.label} stayed clean, and the surprise adventure ended with a shining piece of mica in hand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mica?",
            answer="Mica is a shiny mineral that breaks into thin, glittery pieces.",
        ),
        QAItem(
            question="Why can rocks on a trail be hard on clothes?",
            answer="Rocks can rub and scratch clothes, especially when the path is rough and you move around a lot.",
        ),
        QAItem(
            question="What do gloves help protect?",
            answer="Gloves help protect your hands from dirt, rough stones, and small scratches.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        extra = []
        if meters:
            extra.append(f"meters={meters}")
        if memes:
            extra.append(f"memes={memes}")
        if e.protective:
            extra.append(f"covers={sorted(e.covers)}")
        elif e.region:
            extra.append(f"region={e.region}")
        bits.append(f"{e.id}: {e.type} {' '.join(extra)}")
    return "\n".join(bits)


CURATED = [
    StoryParams(site="cave", activity="search", prize="jacket", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(site="hill", activity="climb", prize="pack", name="Theo", gender="boy", parent="father", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not reasonably threaten a {prize.label} in this setup.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (risk_prize(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.site is None or c[0] == args.site)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    site, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(site=site, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SITES[params.site], ACTIVITIES[params.activity], PRIZES[params.prize],
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
risk(A,P) :- zone(A,R), region(P,R).
fix(A,P) :- risk(A,P), gear(G), guards(G,M), mess(A,M), covers(G,R), region(P,R).
valid(S,A,P) :- site(S), afford(S,A), risk(A,P), fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, site in SITES.items():
        lines.append(asp.fact("site", sid))
        for a in sorted(site.affordances):
            lines.append(asp.fact("afford", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with mica and surprise.")
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        print(f"{len(triples)} compatible stories:\n")
        for s, a, p in triples:
            print(f"  {s:8} {a:8} {p:8}")
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
