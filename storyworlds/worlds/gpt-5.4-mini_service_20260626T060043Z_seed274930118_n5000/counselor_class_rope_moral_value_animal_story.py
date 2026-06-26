#!/usr/bin/env python3
"""
A small animal-story world about a class, a counselor, and a rope.

Premise:
- A counselor leads a class of young animals.
- The class wants to use a rope for a game or task.
- The counselor watches for a moral value issue: sharing, patience, honesty,
  kindness, or listening.

Tension:
- A child wants to grab, tug, hoard, or rush the rope.
- The counselor sees that this could cause a mess, a tear, a tumble, or hurt
  feelings.

Turn:
- The counselor offers a better way: take turns, ask first, hold gently, or
  share the job.

Resolution:
- The class chooses the kinder way, and the rope stays useful and safe.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "counselor"}
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
    place: str = "the animal class"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    counselor = world.entities.get("counselor")
    rope = world.entities.get("rope")
    if not counselor or not rope:
        return out
    if counselor.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rope.meters["risk"] = rope.meters.get("risk", 0.0) + 1.0
    out.append("The rope looked a little unsafe if everyone grabbed it at once.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("grabby", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] = ent.memes.get("conflict", 0.0) + 1.0
        out.append("The eager tug made the class feel tense.")
    return out


CAUSAL_RULES = [Rule("risk", _r_risk), Rule("conflict", _r_conflict)]


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


def story_setting_detail(setting: Setting) -> str:
    return {
        "the animal class": "The class sat in a bright room with a soft mat on the floor.",
        "the den": "The den was cozy, with little paws and tails tucked close.",
        "the yard": "The yard was open and sunny, with a rope looped near a fence.",
    }.get(setting.place, f"{setting.place.capitalize()} waited quietly for the lesson.")


def choose_moral() -> str:
    return random.choice(["sharing", "patience", "kindness", "listening", "taking turns"])


def moral_lesson_text(moral: str) -> str:
    return {
        "sharing": "share the rope",
        "patience": "wait for a turn",
        "kindness": "use gentle paws",
        "listening": "listen to the counselor",
        "taking turns": "take turns with the rope",
    }[moral]


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).memes["grabby"] = sim.get(actor.id).memes.get("grabby", 0.0) + 1.0
    propagate(sim, narrate=False)
    rope = sim.entities[prize_id]
    return rope.meters.get("risk", 0.0) >= THRESHOLD


def tell(setting: Setting, activity: Activity, prize: Prize, hero_name: str,
         hero_type: str, counselor_type: str, moral: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["young", "eager", "small"],
        meters={}, memes={"joy": 0.0, "grabby": 0.0, "worry": 0.0},
    ))
    counselor = world.add(Entity(
        id="counselor", kind="character", type=counselor_type,
        label="the counselor", traits=["kind", "calm"], memes={"worry": 0.0}
    ))
    rope = world.add(Entity(
        id="rope", type=prize.type, label=prize.label, phrase=prize.phrase,
        plural=prize.plural, owner=hero.id, caretaker=counselor.id,
        meters={"clean": 1.0},
    ))

    world.say(f"{hero.id} was a little {hero.type} who came to {setting.place}.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved {activity.gerund}, and {hero.pronoun('possessive')} favorite thing was the rope.")
    world.say(f"The counselor brought out {rope.phrase} for the class to use.")
    world.say(story_setting_detail(setting))

    world.para()
    world.say(f"Then {hero.id} wanted to {activity.verb}.")
    world.say(f"{hero.pronoun('subject').capitalize()} reached for the rope with quick paws.")
    hero.memes["grabby"] += 1.0
    world.facts["activity"] = activity
    world.facts["moral"] = moral
    world.facts["hero"] = hero
    world.facts["counselor"] = counselor
    world.facts["rope"] = rope
    world.facts["predicted_risk"] = predict_risk(world, hero, activity, rope.id)
    if world.facts["predicted_risk"]:
        counselor.memes["worry"] += 1.0
        world.say(f"The counselor saw the problem at once.")
        world.say(f'"If everyone tugs at once, the rope could get {activity.soil}," {counselor.pronoun("subject")} said.')
        propagate(world, narrate=True)
        world.say(f'"Let’s {moral_lesson_text(moral)} instead," {counselor.pronoun("subject")} said.')
        hero.memes["grabby"] = 0.0
        hero.memes["joy"] += 1.0
        counselor.memes["worry"] = 0.0
        world.para()
        world.say(f"{hero.id} nodded and chose to {activity.verb} the careful way.")
        world.say(f"The class {activity.gerund}, and the rope stayed neat and strong.")
        world.say(f"In the end, {hero.id} learned to {moral_lesson_text(moral)}.")
    else:
        world.say(f"The counselor smiled, because the rope plan looked safe.")
        world.say(f"The class used it kindly, and no one hurt the rope.")
        world.para()
        world.say(f"{hero.id} felt proud for remembering how to {moral_lesson_text(moral)}.")
        world.say(f"The rope stayed ready for the next lesson.")
    return world


SETTINGS = {
    "classroom": Setting(place="the animal class", indoor=True, affords={"rope"}),
    "den": Setting(place="the den", indoor=True, affords={"rope"}),
    "yard": Setting(place="the yard", indoor=False, affords={"rope"}),
}

ACTIVITIES = {
    "tug": Activity(
        id="tug",
        verb="tug the rope",
        gerund="tugging on the rope",
        rush="pull harder",
        risk="fray",
        soil="frayed",
        keyword="rope",
        tags={"rope", "sharing"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the rope",
        gerund="climbing the rope",
        rush="clamber up fast",
        risk="stretch",
        soil="stretched out of shape",
        keyword="rope",
        tags={"rope", "patience"},
    ),
    "drag": Activity(
        id="drag",
        verb="drag the rope",
        gerund="dragging the rope",
        rush="yank it across the floor",
        risk="knot",
        soil="twisted into knots",
        keyword="rope",
        tags={"rope", "listening"},
    ),
}

PRIZES = {
    "rope": Prize(label="rope", phrase="a long classroom rope", type="rope"),
}

MORALS = ["sharing", "patience", "kindness", "listening", "taking turns"]

ANIMAL_NAMES = ["Milo", "Luna", "Pip", "Nori", "Tiko", "Bibi", "Kiki", "Pogo"]
ANIMAL_TYPES = ["rabbit", "fox", "bear", "squirrel", "otter", "mouse", "panda", "turtle"]
COUNSELOR_TYPES = ["rabbit", "fox", "bear", "otter"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    hero_type: str
    counselor_type: str
    moral: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, act, prize) for place in SETTINGS for act in ACTIVITIES for prize in PRIZES]


def explain_rejection() -> str:
    return "(No story: this domain only supports the rope lesson right now.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world about a class, a counselor, and a rope.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", dest="hero_type", choices=ANIMAL_TYPES)
    ap.add_argument("--counselor-type", dest="counselor_type", choices=COUNSELOR_TYPES)
    ap.add_argument("--moral", choices=MORALS)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or "rope"
    name = args.name or rng.choice(ANIMAL_NAMES)
    hero_type = args.hero_type or rng.choice(ANIMAL_TYPES)
    counselor_type = args.counselor_type or rng.choice(COUNSELOR_TYPES)
    moral = args.moral or rng.choice(MORALS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name,
                       hero_type=hero_type, counselor_type=counselor_type, moral=moral)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short animal story about a counselor, a class, and a rope.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} but learns to {moral_lesson_text(f['moral'])}.",
        f"Write a child-friendly story set in {world.setting.place} with a moral about {f['moral']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    counselor = f["counselor"]
    activity = f["activity"]
    moral = f["moral"]
    rope = f["rope"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} in the class, and the counselor who helped everyone use the rope safely.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the rope?",
            answer=f"{hero.id} wanted to {activity.verb}, but first had to learn to {moral_lesson_text(moral)}.",
        ),
        QAItem(
            question=f"Why did the counselor speak up about the rope?",
            answer=f"The counselor worried that if everyone grabbed the rope at once, it could get {activity.soil}.",
        ),
        QAItem(
            question=f"What stayed safe in the end?",
            answer=f"The rope stayed neat and useful, and the class chose a kinder way to play.",
        ),
    ]
    if world.facts.get("predicted_risk"):
        qa.append(QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to {moral_lesson_text(moral)} instead of rushing the rope.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a counselor?",
            answer="A counselor is a grown-up who helps children make good choices and solve problems kindly.",
        ),
        QAItem(
            question="What is a class?",
            answer="A class is a group of children who learn and play together.",
        ),
        QAItem(
            question="What is a rope for?",
            answer="A rope can help people pull, tie, swing, or play, but it works best when they handle it carefully.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use something too, instead of keeping it all for yourself.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Prize) :- place(Place), activity(Act), prize(Prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
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
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.hero_type,
        params.counselor_type,
        params.moral,
    )
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
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams(place="classroom", activity="tug", prize="rope", name="Milo", hero_type="rabbit", counselor_type="fox", moral="sharing"),
            StoryParams(place="den", activity="climb", prize="rope", name="Luna", hero_type="squirrel", counselor_type="bear", moral="patience"),
            StoryParams(place="yard", activity="drag", prize="rope", name="Pip", hero_type="otter", counselor_type="rabbit", moral="listening"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
