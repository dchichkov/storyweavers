#!/usr/bin/env python3
"""
storyworlds/worlds/gust_conflict_dialogue_bravery_tall_tale.py
===============================================================

A tiny, self-contained storyworld about a gusty day, a small conflict, a bold
bit of dialogue, and a brave choice in a tall-tale style.

Seed tale:
---
On the windiest morning in the whole county, a child named Pippa loved to wear
a tall straw hat and march across the hill like a tiny captain. One day a wild
gust nearly took the hat clean off her head. Pippa wanted to chase it, but her
grandpa warned her to be careful. Pippa argued back, then took a brave breath,
tied the hat on with a ribbon, and stepped into the wind anyway. The gust
huffed and puffed, but the hat stayed put, and Pippa laughed all the way home.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
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
    weather: str = ""
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
        self.weather: str = ""
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_gust_blow(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("gust", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("gust_blow", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["windblown"] = item.meters.get("windblown", 0.0) + 1.0
            out.append(f"The gust tugged at {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("brave", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["confidence"] = actor.memes.get("confidence", 0.0) + 1.0
        out.append(f"{actor.id} squared {actor.pronoun('possessive')} shoulders.")
    return out


CAUSAL_RULES = [
    _r_gust_blow,
    _r_brave,
]


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


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "blown": bool(prize and prize.meters.get("windblown", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pippa", hero_type: str = "girl",
         parent_type: str = "grandfather", trait: str = "bold") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        memes={"bravery": 0.0, "conflict": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    # Act 1
    world.say(f"{hero.id} was a {trait} little {hero.type} who loved the wind as if it were a singing train.")
    world.say(f"{hero.id} loved {activity.gerund} on the hill, where the grass leaned over like tall green whispers.")
    world.say(f"{parent.label_word if hasattr(parent, 'label_word') else 'grandpa'} had bought {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a captain wears a feathered crown.")

    # Act 2
    world.para()
    world.say(f"One blustery day, {hero.id} and {hero.pronoun('possessive')} {parent_type} went to {setting.place}.")
    world.say(f"The air had a grin in it, and a big gust came rolling through like a runaway wagon.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent_type} warned, \"That gust will snatch your {prize.label} clean away.\"")
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(f"\"I can hold it!\" {hero.id} called back. \"I'm not made of lace!\"")
    hero.meters["gust"] = hero.meters.get("gust", 0.0) + 1.0
    predict = predict_mess(world, hero, activity, prize.id)
    if predict["blown"]:
        world.say(f"{hero.id} rushed ahead anyway, and the gust began to worry at {hero.pronoun('possessive')} {prize.label}.")
    propagate(world, narrate=True)

    # Act 3
    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable gear can protect this prize from the gust.")
    fix = world.add(Entity(
        id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=parent.id,
        protective=True, covers=set(gear.covers), plural=gear.plural,
    ))
    fix.worn_by = hero.id
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(f"{hero.id} took a brave breath, and {hero.pronoun('possessive')} {parent_type} said, \"Let's tie on the {gear.label} and face the wind proper.\"")
    world.say(f"\"All right,\" {hero.id} said. \"If the gust wants a contest, then it can meet my chin strap first.\"")
    _do_activity(world, hero, activity, narrate=True)
    prize.meters["windblown"] = 0.0
    world.say(f"The {gear.tail}, and the {prize.label} stayed put as neat as a nail in a fence board.")
    world.say(f"{hero.id} marched on through the gusts, laughing, with {hero.pronoun('possessive')} {prize.label} snug and safe.")

    world.facts.update(
        hero=hero, parent=parent, prize=prize, activity=activity, setting=setting,
        gear=gear, resolved=True, conflict=True
    )
    return world


SETTINGS = {
    "hill": Setting(place="the windy hill", affords={"kite"}),
    "field": Setting(place="the open field", affords={"kite"}),
    "dock": Setting(place="the river dock", affords={"kite"}),
}

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="race the gusts with a kite",
        gerund="racing a kite",
        rush="dash after the kite",
        mess="gust",
        soil="blown about",
        zone={"head"},
        weather="windy",
        keyword="gust",
        tags={"gust", "wind"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a tall straw hat",
        type="hat",
        region="head",
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a bright ribbon tied for luck",
        type="ribbon",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="strap",
        label="chin strap",
        covers={"head"},
        guards={"gust"},
        prep="tie on the chin strap",
        tail="chin strap held fast",
    ),
    Gear(
        id="ties",
        label="hat ties",
        covers={"head"},
        guards={"gust"},
        prep="loop the hat ties under the chin",
        tail="hat ties stayed knotted tight",
    ),
]

NAMES = ["Pippa", "Nora", "Mabel", "June", "Lina", "Mina"]
TRAITS = ["bold", "brave", "lively", "tall-tale", "cheery"]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a tall-tale style story for a little child about a {act.keyword} gust and a brave {hero.id} named {hero.id}.',
        f"Tell a story where {hero.id} wants to {act.verb} at {world.setting.place} but {parent.id} worries about {hero.pronoun('possessive')} {prize.label}.",
        f'Write a story that uses the word "{act.keyword}" and ends with a brave choice and a safe ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {hero.type} who loved the wind and had the courage to face it.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the windy hill?",
            answer=f"{hero.id} wanted to {act.verb}. That wish pulled the story forward even while the gust made things tricky.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=f"{parent.id} worried because a strong gust could snatch {hero.pronoun('possessive')} {prize.label} right off {hero.pronoun('possessive')} head.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} say?",
            answer=f"{hero.id} said, \"I can hold it!\" and later chose to face the wind with a chin strap so the {prize.label} would stay on.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} marching through the gusts, laughing, while the {prize.label} stayed snug and safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gust?",
            answer="A gust is a quick, strong puff of wind that can make hats flap and hair blow around.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared, especially when you know it matters.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="Dialogue is when characters talk to each other in a story.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", activity="kite", prize="hat", name="Pippa", gender="girl", parent="grandfather", trait="bold"),
    StoryParams(place="field", activity="kite", prize="ribbon", name="Nora", gender="girl", parent="grandfather", trait="brave"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
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
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if p - c:
        print("  only in python:", sorted(p - c))
    if c - p:
        print("  only in clingo:", sorted(c - p))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    return f"(No story: nothing in the gear catalog protects {noun} from this gust.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale story world about gusts, courage, and a small conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandfather", "grandmother"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    place, activity, prize = rng.choice(sorted(combos))
    prize_cfg = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_cfg.genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["grandfather", "grandmother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
