#!/usr/bin/env python3
"""
storyworlds/worlds/momma_pier_reconciliation_bad_ending_comedy.py
==================================================================

A small comedy-leaning pier storyworld with a reconciliation beat and a bad
ending. The world is narrow on purpose: a child and momma at the pier, a windy
or seagull-filled mistake, a laugh, a make-up moment, and a final image that
proves the mishap still happened.

Seed tale idea:
- A child at the pier wants to do something splashy and funny.
- Momma sees the trouble coming.
- The child goes ahead anyway, causing a silly problem.
- They reconcile, but the ending stays a little bad, in a comic way.

The simulated state tracks:
- meters: physical conditions like wind-blown, soggy, spilled, tangled, stolen
- memes: emotional conditions like worry, mischief, embarrassment, warmth, relief

This script follows the shared storyworld contract:
- build_parser / resolve_params / generate / emit / main
- QAItem / StoryError / StorySample from storyworlds.results
- lazy import of storyworlds.asp inside ASP helpers
- inline ASP_RULES twin for the reasonableness gate
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

    def __post_init__(self) -> None:
        for k in ["windblown", "soggy", "spilled", "tangled", "stolen", "scratched", "messy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "mischief", "embarrassment", "warmth", "relief", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "momma", "woman", "mom"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pier"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    breeze: str = ""
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


SETTINGS = {
    "pier": Setting(place="the pier", affords={"kites", "seagulls", "icecream"}),
}

ACTIVITIES = {
    "kites": Activity(
        id="kites",
        verb="fly the silly kite",
        gerund="flying the silly kite",
        rush="run to the very end of the pier",
        risk="the wind would snatch it and tug it loose",
        soil="wind-blown and tangled",
        zone={"sky", "hands"},
        keyword="kite",
        tags={"wind", "kite", "silly"},
    ),
    "seagulls": Activity(
        id="seagulls",
        verb="feed the seagulls",
        gerund="feeding the seagulls",
        rush="shake the snack bag near the rail",
        risk="the gulls would swoop down and steal the snack",
        soil="stolen",
        zone={"hands"},
        keyword="gull",
        tags={"gull", "snack", "bird"},
    ),
    "icecream": Activity(
        id="icecream",
        verb="eat the ice cream cone",
        gerund="eating ice cream",
        rush="walk faster before the drips fell",
        risk="the cone would melt and drip all over everything",
        soil="soggy and spilled",
        zone={"hands", "shirt"},
        keyword="ice cream",
        tags={"icecream", "sweet", "drip"},
    ),
}

PRIZES = {
    "kite": Prize(
        label="kite",
        phrase="a bright red kite",
        type="kite",
        region="hands",
    ),
    "cone": Prize(
        label="ice cream",
        phrase="a tall vanilla ice cream cone",
        type="cone",
        region="hands",
    ),
    "snack": Prize(
        label="snack bag",
        phrase="a bag of buttery snacks",
        type="snack bag",
        region="hands",
        plural=False,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Noah", "Ben", "Jack", "Eli"]
TRAITS = ["curious", "silly", "cheerful", "lively", "spunky", "playful"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["windblown"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id or item.protective:
                continue
            if item.region not in {"hands", "shirt"}:
                continue
            sig = ("tangle", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["tangled"] += 1
            item.memes["embarrassment"] += 1
            out.append(f"The wind made {actor.id}'s {item.label} all tangled.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["embarrassment"] += 1
        out.append("That made a sticky little mess.")
    return out


CAUSAL_RULES = [Rule("tangle", _r_tangle), Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or activity.id == "seagulls" or activity.id == "icecream"


def select_gear(activity: Activity, prize: Prize) -> Optional[str]:
    if activity.id == "kites" and prize.label == "kite":
        return "string spool"
    if activity.id == "seagulls" and prize.label == "snack bag":
        return "paper napkin"
    if activity.id == "icecream" and prize.label == "ice cream":
        return "extra napkins"
    return None


def introduction(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {next((t for t in child.memes.keys() if t == 'joy'), '')}".strip() or
              f"{child.id} was a little {child.type} who loved the pier.")
    world.say(f"{child.id} liked the boards, the gulls, and the big windy open air.")


def set_scene(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f"One breezy day, {child.id} and {child.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say(f"{child.id} wanted to {activity.verb}, and {child.pronoun('possessive')} {prize.label} looked ready for trouble.")


def warn(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> bool:
    if not prize_at_risk(activity, prize):
        return False
    world.facts["risk"] = activity.risk
    world.say(f'"{activity.risk}," {parent.id} said. "That could end in a very silly mess."')
    return True


def disobey(world: World, child: Entity, activity: Activity) -> None:
    child.memes["mischief"] += 1
    child.meters["windblown"] += 1
    world.say(f"{child.id} grinned anyway and tried to {activity.rush}.")
    world.say(f"The breeze grabbed at {child.id}'s sleeves like it had a joke to tell.")


def mishap(world: World, child: Entity, activity: Activity, prize: Entity) -> None:
    if activity.id == "kites":
        prize.meters["windblown"] += 1
        prize.meters["tangled"] += 1
        world.say(f"Whoosh! The kite shot sideways and wrapped itself around a lamppost sign.")
        world.say(f"{child.id} stared up with a tiny open mouth, because the kite was gone and the joke was on {child.pronoun('object')}.")
    elif activity.id == "seagulls":
        prize.meters["stolen"] += 1
        world.say(f"A gull swooped down, grabbed the snack bag, and bobbed away like a fluffy thief.")
        world.say(f"{child.id} had only one snack left in the whole world, and now it was in a gull's beak.")
    else:
        prize.meters["spilled"] += 1
        world.say(f"The ice cream leaned, wobbled, and plopped onto the boards in one sleepy heap.")
        world.say(f"{child.id} looked down at the cone and the cone looked down at {child.id}.")
    propagate(world, narrate=True)


def reconciliation(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> None:
    child.memes["warmth"] += 1
    parent.memes["warmth"] += 1
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(f"Then {parent.id} snorted a laugh, and {child.id} laughed too, because the whole thing was so absurd.")
    world.say(f'{parent.id} said, "Next time we can be brave and funny with a better plan."')
    world.say(f"{child.id} leaned in for a hug, and the two of them made up right there beside the rail.")
    world.say(f"They were okay again, even if the day was still a bit of a mess.")


def ending_image(world: World, child: Entity, activity: Activity, prize: Entity) -> None:
    if activity.id == "kites":
        world.say(f"At the end, {child.id} held only a twisted string, and the kite stayed stuck on the sign like a banner for a very confused party.")
    elif activity.id == "seagulls":
        world.say(f"At the end, {child.id} had one crumb in {child.pronoun('possessive')} palm, and a gull watched from the rail like it wanted a sequel.")
    else:
        world.say(f"At the end, {child.id} had sticky hands, an empty cone, and a napkin that lost the battle.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mia",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "momma") -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Momma", kind="character", type=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=child.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    child.memes["joy"] += 1

    world.say(f"{child.id} was a little {hero_traits[0] if hero_traits else 'cheerful'} {hero_type} who loved the pier.")
    world.say(f"{child.id} liked the wind, the gulls, and the jokes the waves seemed to make.")
    world.para()
    set_scene(world, child, parent, activity, prize)
    warn(world, parent, child, activity, prize)
    disobey(world, child, activity)
    mishap(world, child, activity, prize)
    world.para()
    reconciliation(world, parent, child, activity, prize)
    ending_image(world, child, activity, prize)

    world.facts.update(hero=child, parent=parent, prize=prize, activity=activity, setting=setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return sorted(out)


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
    "kite": [("What is a kite?", "A kite is a light toy that flies in the wind on a string.")],
    "gull": [("What is a seagull?", "A seagull is a bird that lives near the sea and likes to look for food.")],
    "icecream": [("Why does ice cream melt?", "Ice cream melts when it gets warm because it is made from frozen milk and sugar.")],
    "wind": [("What is wind?", "Wind is moving air. It can be gentle or strong, and it can push light things around.")],
    "snack": [("Why do birds like snacks?", "Many birds like snacks because they are easy to peck up and eat.")],
    "sweet": [("What makes a sweet treat different?", "A sweet treat usually has sugar in it, so it tastes pleasant and dessert-like.")],
    "drip": [("What happens when something drips?", "When something drips, small drops fall off it one by one.")],
    "silly": [("What does silly mean?", "Silly means funny in a playful way, often in a way that makes people laugh.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy story for a young child set on a pier with the word "{act.keyword}".',
        f"Tell a story where {hero.id} wants to {act.verb} at the pier, but {parent.id} worries about {prize.label}, then they make up after a funny mishap.",
        f"Write a gentle, funny story ending with a reconciliation but a bad result that is still a little messy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"Who went to the pier with {hero.id}?",
            answer=f"{parent.id} went with {hero.id} to the pier.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry?",
            answer=f"{parent.id} worried because {act.risk} and {prize.label} could end up in trouble.",
        ),
        QAItem(
            question="What changed between them at the end?",
            answer=f"They reconciled, laughed together, and hugged, even though the day ended badly for {prize.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not realistically threaten {prize.label}, so there is no honest pier problem.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), risky(A,P).
has_fix(A,P) :- prize_at_risk(A,P), fix(A,P).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for p in PRIZES.values():
            if prize_at_risk(a, p):
                lines.append(asp.fact("risky", aid, p.label))
            if select_gear(a, p):
                lines.append(asp.fact("fix", aid, p.label))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
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
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pier comedy storyworld with reconciliation and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["momma", "mother", "father", "dad"])
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
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "momma"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:10} {prize:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, act, prize in valid_combos():
            p = StoryParams(place=place, activity=act, prize=prize, name="Mia", gender="girl", parent="momma", trait="silly")
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
