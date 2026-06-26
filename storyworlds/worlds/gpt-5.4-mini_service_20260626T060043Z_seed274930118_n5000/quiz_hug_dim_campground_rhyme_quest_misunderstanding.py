#!/usr/bin/env python3
"""
Standalone storyworld: campground space-adventure with a quiz, a hug-dim
helper, a rhyme quest, and a misunderstanding that gets cleared up.

This world tells a small classical simulation story where a crew at a
campground prepares for a night quest. A mistaken clue causes tension, but
a rhyme-based quiz reveals the real path and a gentle hug-dim device helps
resolve the confusion.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the campground"
    affords: set[str] = field(default_factory=set)


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
        return any(g.id in GEAR_BY_ID and region in GEAR_BY_ID[g.id].covers and g.worn_by == actor.id for g in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act in ACTIVITIES.values():
            if actor.meters.get(act.mess, 0.0) < THRESHOLD:
                continue
            sig = ("mess", actor.id, act.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            for item in world.worn_items(actor):
                if item.region in world.zone and item.id not in PROTECTED_IDS:
                    item.meters[act.mess] = item.meters.get(act.mess, 0.0) + 1
                    item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                    out.append(f"{actor.id}'s {item.label} got messy.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("confused", 0.0) < THRESHOLD:
            continue
        sig = ("misunderstanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["tension"] = actor.memes.get("tension", 0.0) + 1
        out.append(f"{actor.id} felt tangled up by the misunderstanding.")
    return out


CAUSAL_RULES = [_r_mess, _r_misunderstanding]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters[activity.mess] = sim.get(actor.id).meters.get(activity.mess, 0.0) + 1
    sim.zone = set(activity.zone)
    for item in sim.worn_items(sim.get(actor.id)):
        if item.region in sim.zone and item.id not in PROTECTED_IDS:
            return True
    return False


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def setup_story(world: World, hero: Entity, mate: Entity, prize: Entity, clue: Entity) -> None:
    world.say(f"{hero.id} was a brave little space explorer at the campground.")
    world.say(f"{hero.id} loved the night sky, shiny maps, and tiny campfire missions.")
    world.say(f"{mate.id} was {hero.id}'s friend, and together they packed a {prize.label}.")
    world.say(f"They also carried a {clue.label} that promised a rhyme quest under the stars.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, buddy_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"curious": 1}))
    buddy = world.add(Entity(id=buddy_name, kind="character", type="boy", meters={}, memes={"helpful": 1}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region, plural=prize_cfg.plural, owner=hero.id))
    clue = world.add(Entity(id="clue", type="scroll", label="starlight clue card", phrase="a clue card with a rhyme", owner=buddy.id))
    quiz = world.add(Entity(id="quiz", type="device", label="camp quiz panel", phrase="a glowing quiz panel", owner=buddy.id))
    hugdim = world.add(Entity(id="hugdim", type="device", label="a hug-dim pouch", phrase="a soft pouch that made hugs feel bigger", owner=hero.id))
    world.add(quiz)
    world.add(hugdim)

    setup_story(world, hero, buddy, prize, clue)
    world.para()
    world.say(f"One evening, {hero.id} and {buddy.id} walked to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the path ahead looked tricky.")

    if predict_mess(world, hero, activity, prize.id):
        hero.memes["confused"] = hero.memes.get("confused", 0.0) + 1
        world.say(f"{buddy.id} read the clue wrong and said the trail pointed to the smoky rocks.")
        world.say(f"{hero.id} frowned, because that sounded like a misunderstanding.")
        world.say(f"Then the camp quiz panel blinked and asked a rhyme question.")
        world.say(f'"What rhymes with light?" it asked. "{activity.keyword} in sight!" {buddy.id} answered.')
        world.say(f"The right answer pointed to the lantern hill instead of the rocks.")
        gear = choose_gear(activity, prize)
        if gear is None:
            raise StoryError("No reasonable hug-dim story: no gear can protect the prize.")
        g = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, plural=gear.plural, worn_by=hero.id))
        PROTECTED_IDS.add(g.id)
        world.say(f"{hero.id} opened {g.label} and gave {buddy.id} a hug-dim squeeze.")
        world.say(f"The squeeze made the mistake feel smaller, and both friends could think again.")
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        hero.memes["confused"] = 0.0
        world.para()
        world.say(f"At last they followed the rhyme quest to the lantern hill and {activity.gerund}.")
        world.say(f"{hero.id}'s {prize.label} stayed safe, and the campground shone like a tiny space port.")
        world.facts.update(hero=hero, buddy=buddy, prize=prize, clue=clue, quiz=quiz, hugdim=g, activity=activity, setting=setting, trait=trait)
        return world

    raise StoryError("This story needs a real misunderstanding; choose a more risky activity.")


SETTING = Setting(place="the campground", affords={"starlight"})
ACTIVITIES = {
    "starlight": Activity(
        id="starlight",
        verb="follow the starlight trail",
        gerund="following the starlight trail",
        rush="dash toward the wrong lantern",
        mess="sparkle",
        zone={"torso", "hands"},
        keyword="light",
        tags={"rhyme", "quest", "misunderstanding"},
    )
}
PRIZES = {
    "badge": Prize(label="badge", phrase="a shiny explorer badge", type="badge", region="torso"),
}
GEAR = [
    Gear(
        id="hugdim",
        label="a hug-dim pouch",
        covers={"torso"},
        guards={"sparkle"},
        prep="use the hug-dim pouch",
        tail="used the hug-dim pouch",
    )
]
GEAR_BY_ID = {g.id: g for g in GEAR}
PROTECTED_IDS: set[str] = set()


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    buddy_name: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space-adventure story set at a campground about a quiz, a rhyme quest, and a misunderstanding.',
        f"Tell a gentle story where {f['hero'].id} and {f['buddy'].id} solve a mistake with a camp quiz and a hug-dim pouch.",
        "Write a child-facing adventure with stars, a wrong clue, and a happy ending at the campground.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Who went on the rhyme quest at the campground?",
            answer=f"{hero.id} and {buddy.id} went on the rhyme quest together at the campground.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do during the story?",
            answer=f"{hero.id} wanted to {activity.verb} under the stars.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"{buddy.id} read the clue wrong at first, so the friends almost went to the wrong place.",
        ),
        QAItem(
            question=f"How did the hug-dim pouch help?",
            answer=f"It made the mistake feel smaller, so {hero.id} and {buddy.id} could calm down and fix the plan.",
        ),
        QAItem(
            question=f"What stayed safe by the end?",
            answer=f"{hero.id}'s {prize.label} stayed safe, and the campground adventure ended well.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people can camp outdoors, sleep in tents, and watch the night sky.",
        ),
        QAItem(
            question="What is a quiz?",
            answer="A quiz is a set of questions that helps people check what they know or find the right answer.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and sight.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea at first.",
        ),
    ]


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground space-adventure storyworld.")
    ap.add_argument("--place", choices=["campground"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--buddy-name")
    ap.add_argument("--trait", default="curious")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Nova", "Mira", "Leo", "Pax"])
    buddy_name = args.buddy_name or rng.choice(["Orbit", "Comet", "Tess", "Juno"])
    return StoryParams(
        place="campground",
        activity=args.activity or "starlight",
        prize=args.prize or "badge",
        name=name,
        gender=gender,
        buddy_name=buddy_name,
        trait=args.trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.buddy_name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
setting(campground).
affords(campground,starlight).
activity(starlight).
mess_of(starlight,sparkle).
splashes(starlight,torso).
splashes(starlight,hands).
prize(badge).
worn_on(badge,torso).
wears(girl,badge).
wears(boy,badge).
gear(hugdim).
guards(hugdim,sparkle).
covers(hugdim,torso).

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid_story(Place,A,P,G) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P), wears(G,P).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "campground"), asp.fact("affords", "campground", "starlight"),
             asp.fact("activity", "starlight"), asp.fact("mess_of", "starlight", "sparkle"),
             asp.fact("splashes", "starlight", "torso"), asp.fact("splashes", "starlight", "hands"),
             asp.fact("prize", "badge"), asp.fact("worn_on", "badge", "torso"),
             asp.fact("wears", "girl", "badge"), asp.fact("wears", "boy", "badge"),
             asp.fact("gear", "hugdim"), asp.fact("guards", "hugdim", "sparkle"),
             asp.fact("covers", "hugdim", "torso")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("campground", "starlight", "badge", "girl"), ("campground", "starlight", "badge", "boy")}
    if asp_set == py_set:
        print("OK: clingo gate matches python gate.")
        return 0
    print("MISMATCH")
    print("asp:", sorted(asp_set))
    print("py :", sorted(py_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    for i in range(args.n):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
        if args.all:
            break
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
