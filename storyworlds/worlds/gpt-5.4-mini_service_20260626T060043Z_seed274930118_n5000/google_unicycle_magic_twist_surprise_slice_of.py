#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/google_unicycle_magic_twist_surprise_slice_of.py
================================================================================

A small slice-of-life storyworld about a child, a unicycle, a careful parent,
and a tiny plan found through a Google search.

Seed-tale premise:
---
A child wants to try a unicycle trick called the Magic Twist Surprise. The child
is excited, but a parent worries the trick is too wobbly for a brand-new paper
crown. A quick Google search suggests a safer setup: start by holding the wall,
wear a helmet, and practice one small step at a time. The child tries it, finds
the balance, and ends the day proud, a little tired, and still wearing the crown.
---

This world keeps the style close to slice of life: ordinary rooms, small worries,
practical help, and one gentle surprise at the end.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wobble": 0.0, "scratched": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "desire": 0.0, "worry": 0.0, "pride": 0.0, "calm": 0.0}

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool = False
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
        self.facts: dict = {}
        self.predicted: dict = {}

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting("the kitchen", indoor=True, affords={"google", "twist"}),
    "driveway": Setting("the driveway", indoor=False, affords={"google", "twist"}),
    "park_path": Setting("the park path", indoor=False, affords={"google", "twist"}),
}

ACTIVITIES = {
    "google": Activity(
        id="google",
        verb="google a safe way to practice",
        gerund="googling a safer way to practice",
        rush="open the search page again and again",
        mess="wobbled",
        soil="too wobbly",
        zone={"torso"},
        keyword="google",
        tags={"google", "surprise"},
    ),
    "twist": Activity(
        id="twist",
        verb="try the Magic Twist Surprise",
        gerund="trying the Magic Twist Surprise",
        rush="jump onto the unicycle too fast",
        mess="wobbled",
        soil="wobbly and shaky",
        zone={"head", "torso"},
        keyword="twist",
        tags={"magic", "twist", "surprise"},
    ),
}

PRIZES = {
    "paper_crown": Prize(
        label="paper crown",
        phrase="a shiny paper crown",
        type="crown",
        region="head",
        genders={"girl", "boy"},
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a clean striped shirt",
        type="shirt",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="helmet",
        label="a bicycle helmet",
        covers={"head"},
        guards={"wobbled"},
        prep="put on a bicycle helmet first",
        tail="went back to the door to fetch the helmet",
    ),
    Gear(
        id="wall",
        label="the wall for balance",
        covers={"torso", "head"},
        guards={"wobbled"},
        prep="practice beside the wall first",
        tail="stayed near the wall and took tiny turns",
    ),
]

NAMES = {
    "girl": ["Mia", "Zoe", "Luna", "Ava", "Nora"],
    "boy": ["Leo", "Ben", "Noah", "Eli", "Theo"],
}
TRAITS = ["curious", "cheerful", "careful", "spirited", "patient"]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} only risks {sorted(activity.zone)}, "
        f"but {prize.label} sits on the {prize.region}. There is no reasonable "
        f"reason to warn about that combination.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["desire"] += 0.5
    actor.memes["worry"] += 0.25
    if narrate:
        world.say(f"{actor.id} tried to {activity.verb}.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    soiled = bool(prize and prize.meters.get(activity.mess, 0.0) >= THRESHOLD)
    return {"soiled": soiled}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"wobble": 0.0, "scratched": 0.0, "tidy": 0.0}, memes={"joy": 0.0, "desire": 0.0, "worry": 0.0, "pride": 0.0, "calm": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={"wobble": 0.0, "scratched": 0.0, "tidy": 0.0}, memes={"joy": 0.0, "desire": 0.0, "worry": 0.0, "pride": 0.0, "calm": 0.0}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"wobble": 0.0, "scratched": 0.0, "tidy": 1.0},
        memes={"joy": 0.0, "desire": 0.0, "worry": 0.0, "pride": 0.0, "calm": 0.0},
    ))
    gear = None

    hero.memes["joy"] += 0.5
    world.say(f"{hero.id} was a {hero_traits[0]} little {hero.type} who liked trying new things slowly.")
    world.say(f"{hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} favorite thing that day was the unicycle.")
    world.say(f"That morning, {parent.label_word} bought {hero.pronoun('object')} {prize.phrase} for the ride.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} wanted to {activity.verb}, but the unicycle kept looking tall and tricky.")
    world.say(f"{hero.id} sat beside the seat and searched Google for help.")
    world.say(f"The page suggested one careful twist: start near a wall, keep both hands ready, and breathe before moving.")
    if prize.region == "head":
        world.say(f"{parent.label_word} worried that the {prize.label} would get bent in a wobble.")
    else:
        world.say(f"{parent.label_word} worried that the {prize.label} would get wrinkled in a wobble.")

    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'{parent.label_word} said, "If you rush, your {prize.label} will get {activity.soil}."')
    hero.memes["worry"] += 0.5

    world.para()
    world.say(f"{hero.id} started to rush, then paused. {hero.id} looked at the Google note again and nodded.")
    gear = select_gear(activity, prize)
    if gear:
        world.say(f'"{How about we {gear.prep}?" {parent.label_word} asked.')
        world.say(f"{hero.id} agreed, and the surprise was that the tiny advice really worked.")
        helper = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers)))
        helper.worn_by = hero.id

    _do_activity(world, hero, activity, narrate=False)
    if gear:
        hero.meters["wobble"] = 0.0
        prize.meters["scratched"] = 0.0
    hero.memes["joy"] += 1.0
    hero.memes["pride"] += 1.0
    hero.memes["calm"] += 0.5
    world.say(f"{hero.id} made one small push, then another, and the unicycle finally rolled straight.")
    world.say(f"The Magic Twist Surprise was not magic at all; it was patience, balance, and a good pause at the right moment.")
    world.say(f"By the end, {hero.id} was smiling under {hero.pronoun('possessive')} {prize.label}, and {parent.label_word} was smiling too.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
        predicted_soil=activity.soil,
    )
    return world


SETTINGS_ORDER = ["driveway", "park_path", "kitchen"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a child named {hero.id} who uses Google before trying a unicycle trick.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label_word} worries about {prize.label}.",
        f'Write a tiny story that includes the words "Google", "unicycle", "Magic", "Twist", and "Surprise".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} search for before trying the unicycle trick?",
            answer=f"{hero.id} searched Google for a safer way to practice {act.verb}.",
        ),
        QAItem(
            question=f"Why was {parent.label_word} careful about the {prize.label}?",
            answer=f"{parent.label_word} was careful because a wobble could have made the {prize.label} get {act.soil}.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=(
                f"The surprise was that the small Google tip worked, so {hero.id} could {act.verb} "
                f"without ruining the {prize.label}."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} end the story?",
            answer=(
                f"{hero.id} ended the story smiling, more confident, and still wearing "
                f"{hero.pronoun('possessive')} {prize.label} after the practice."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} stay safe while practicing?",
            answer=f"{gear.label if gear else 'Careful practice'} helped {hero.id} stay safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Google used for?",
            answer="Google is a search tool that helps people look up information on the internet.",
        ),
        QAItem(
            question="What is a unicycle?",
            answer="A unicycle is a one-wheeled bike that takes balance and practice.",
        ),
        QAItem(
            question="Why do people practice a new skill in small steps?",
            answer="Small steps make new skills feel less scary and help people stay safe while learning.",
        ),
        QAItem(
            question="What does patience mean when learning something tricky?",
            answer="Patience means taking your time and keeping going even when something is not easy yet.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("driveway", "twist", "paper_crown", "Mia", "girl", "mother", "curious"),
    StoryParams("park_path", "twist", "shirt", "Leo", "boy", "father", "patient"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about Google, a unicycle, and a small surprise.")
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:7} {prize:12}  [{', '.join(genders)}]")
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
