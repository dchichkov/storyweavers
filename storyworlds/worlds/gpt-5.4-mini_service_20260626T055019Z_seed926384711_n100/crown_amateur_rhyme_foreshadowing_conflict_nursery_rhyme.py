#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/crown_amateur_rhyme_foreshadowing_conflict_nursery_rhyme.py
================================================================================

A tiny nursery-rhyme storyworld about an amateur child, a crown, a windy
foreshadowed problem, and a gentle compromise.

The story is simulated, not swapped from a template: world state tracks
physical meters and emotional memes, a crown can wobble loose, conflict rises
when a warning is ignored, and a helper step resolves the trouble.

This world keeps the prose simple, rhythmic, and child-facing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
        if not self.meters:
            self.meters = {"wind": 0.0, "tilt": 0.0, "scruff": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "pride": 0.0, "worry": 0.0, "conflict": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    breeze: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    meter: str
    soil: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(i.protective and region in i.covers for i in self.worn_items(actor))

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


def _r_wind_wobble(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wind"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            sig = ("wobble", actor.id, item.id)
            if sig in world.fired:
                continue
            if item.region == "head":
                world.fired.add(sig)
                item.meters["tilt"] += 1
                actor.memes["worry"] += 1
                out.append(f"The breeze gave {actor.id}'s {item.label} a little wobble-wink.")
    return out


def _r_scruff(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wind"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region != "head":
                continue
            if actor.covered(actor, "head"):
                continue
            sig = ("scruff", actor.id, item.id)
            if sig in world.fired:
                continue
            if item.meters["tilt"] >= THRESHOLD:
                world.fired.add(sig)
                item.meters["scruff"] += 1
                actor.memes["conflict"] += 1
                out.append(f"The crown slid a bit and looked ready to scruff.")
    return out


CAUSAL_RULES = [_r_wind_wobble, _r_scruff]


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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}, in a merry little ring."


SETTINGS = {
    "garden": Setting(place="the garden", breeze="a breezy", affords={"parade", "sing"}),
    "green": Setting(place="the village green", breeze="a windy", affords={"parade", "sing"}),
    "stage": Setting(place="the tiny stage", breeze="a drafty", affords={"sing"}),
}

ACTIVITIES = {
    "parade": Activity(
        id="parade",
        verb="lead the parade",
        gerund="leading the parade",
        rush="trot to the front",
        meter="wind",
        soil="wonky",
        keyword="parade",
        tags={"wind"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing the rhyme",
        gerund="singing the rhyme",
        rush="step up to sing",
        meter="wind",
        soil="shivery",
        keyword="rhyme",
        tags={"rhyme"},
    ),
}

PRIZES = {
    "crown": Prize(
        label="crown",
        phrase="a bright little crown",
        type="crown",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="ribbon",
        label="a blue ribbon",
        covers={"head"},
        guards={"wind"},
        prep="tie on a blue ribbon first",
        tail="tied the ribbon snug and neat",
    ),
    Gear(
        id="pin",
        label="a small gold pin",
        covers={"head"},
        guards={"wind"},
        prep="pin the crown in place",
        tail="pinned it safe and sweet",
    ),
]


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


GIRL_NAMES = ["Mina", "Lily", "Nora", "Pia", "June"]
BOY_NAMES = ["Toby", "Finn", "Milo", "Theo", "Ned"]
TRAITS = ["amateur", "shy", "brave", "cheery", "tiny"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "head" and activity.meter == "wind"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.meter in gear.guards:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not create a reasonable crown problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about an amateur and a crown.")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else "amateur"
    if trait not in TRAITS:
        trait = "amateur"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait', 'amateur')} {hero.type}, neat and sweet.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"joy": 0.0, "pride": 0.0, "worry": 0.0, "conflict": 0.0, "hope": 0.0, "trait": 0.0}))
    hero.memes["trait"] = 1.0
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    crown = world.add(Entity(id="crown", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region))
    hero.memes["pride"] += 1
    world.say(f"{hero.id} was an amateur in a rhyme, but {hero.pronoun()} had a crown so fine.")
    world.say(f"{hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} crown would gleam in time.")
    world.say(f"{parent.label or 'The parent'} bought {hero.pronoun('object')} {crown.phrase}, bright as moonlit snow.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} crown and walked along, feeling proud and slow.")
    world.para()
    world.say(f"One day at {world.setting.place}, where {world.setting.breeze} breeze could blow,")
    world.say(f"{hero.id} wanted to {activity.verb}, with feet all set to go.")
    world.say(f"But the air said a foreshadowing hush: 'Watch the crown, oh so light.'")
    hero.meters["wind"] += 1
    hero.memes["hope"] += 1
    if activity.id == "parade":
        world.say(f"{hero.id} heard the drum and wanted to {activity.rush}, quick and bright.")
    else:
        world.say(f"{hero.id} heard the song and wanted to {activity.rush}, high as kite.")
    world.say(f'"Your crown may slide," {parent.pronoun("subject") if False else parent.label_word if hasattr(parent, "label_word") else "the parent"} said, "and that may cause a fright."')
    hero.memes["worry"] += 1
    world.say(f"{hero.id} kept on smiling, but the crown began to tilt.")
    propagate(world)
    world.say(f"The little crown made a wobble-wink, and then it nearly spilt.")
    hero.memes["conflict"] += 1
    world.para()
    world.say(f'"No, no," said {hero.id}, "I can do it all alone!"')
    world.say(f"But {parent.label or 'the parent'} came close beside and spoke in a kind, soft tone.")
    gear = select_gear(activity, crown)
    if gear is not None:
        world.say(f'"Let us {gear.prep}," said {parent.label or "the parent"}, "and keep that crown well known."')
        helper = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), owner=hero.id, caretaker=parent.id))
        helper.worn_by = hero.id
        hero.memes["conflict"] = 0.0
        hero.memes["joy"] += 1
        hero.memes["pride"] += 1
        world.say(f"{hero.id} nodded, and {gear.tail}.")
        world.say(f"Then {hero.id} was {activity.gerund}, and the crown stayed snug and trim.")
        world.say(f"So the amateur in the rhyme found help, and won the happy hymn.")
    world.facts.update(hero=hero, parent=parent, prize=crown, activity=activity, setting=setting, gear=gear)
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f"Write a short nursery rhyme about {hero.id}, an amateur child, and a crown.",
        f"Tell a gentle rhyme where {hero.id} wants to {act.verb} but must face a windy worry.",
        f"Write a child-friendly story with foreshadowing, conflict, and a happy crown-saving fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little amateur {hero.type}, and {hero.pronoun('possessive')} parent who helps keep the crown safe.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because the rhyme made the day feel bright and bold.",
        ),
        QAItem(
            question=f"Why was the crown in trouble?",
            answer=f"The breeze at {world.setting.place} was windy enough to make the crown tilt, so it could slip from {hero.pronoun('possessive')} head.",
        ),
    ]
    if gear:
        qs.append(QAItem(
            question="How did the family fix the problem?",
            answer=f"They used {gear.label} first, so the crown stayed snug while {hero.id} kept {act.gerund}.",
        ))
    return qs


KNOWLEDGE = {
    "crown": [("What is a crown?", "A crown is a special headpiece, often worn by a king, queen, or someone in a parade.")],
    "wind": [("What does wind do?", "Wind is moving air. It can make hats wobble and leaves flutter.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a pair of words that sound alike at the end, like bell and dell.")],
    "amateur": [("What does amateur mean?", "An amateur is someone who is still learning and doing something for fun, not as a job.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"crown", "wind", "rhyme", "amateur"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- windy(A), worn_on(P, head).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G, head), guards(G, wind).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("windy", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(valid_stories_asp())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(python_set - asp_set))
    print("only asp:", sorted(asp_set - python_set))
    return 1


CURATED = [
    StoryParams(place="garden", activity="parade", prize="crown", name="Mina", gender="girl", parent="mother", trait="amateur"),
    StoryParams(place="green", activity="parade", prize="crown", name="Toby", gender="boy", parent="father", trait="amateur"),
    StoryParams(place="stage", activity="sing", prize="crown", name="Lily", gender="girl", parent="mother", trait="amateur"),
]


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
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = valid_stories_asp()
        print(f"{len(triples)} compatible story combos:")
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
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait="amateur")


if __name__ == "__main__":
    main()
