#!/usr/bin/env python3
"""
storyworlds/worlds/insurance_hoe_dialogue_superhero_story.py
============================================================

A small superhero storyworld about careful heroing, a garden hoe, and
insurance-backed responsibility.

Seed tale used to build the world:
---
Captain Sprout loved helping in the community garden. One bright morning, he
wanted to use a hoe to clear the weeds around the tomato beds. His partner,
Mira, worried the hoe might crack the thin glass of the nearby greenhouse.

Captain Sprout had a little insurance card from the garden club, and he joked
that even superheroes needed paperwork. Mira reminded him that insurance was
for accidents, not for careless choices. So Captain Sprout slowed down, used
the hoe only in the safe rows, and kept the greenhouse safe.

Dialogue beats:
---
- hero wants to hoe the garden
- partner warns about fragile property
- insurance is discussed as a backup, not a license to be sloppy
- hero chooses a careful method and saves the day
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "damage", "work", "risk", "calm", "joy", "worry", "pride"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the community garden"
    affords: set[str] = field(default_factory=lambda: {"hoe"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "hoe"
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
class Policy:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "garden": Setting(place="the community garden", affords={"hoe"}),
    "yard": Setting(place="the backyard garden", affords={"hoe"}),
}

ACTIVITIES = {
    "hoe": Activity(
        id="hoe",
        verb="hoe the weeds",
        gerund="hoeing the weeds",
        rush="swing the hoe faster",
        mess="scraped",
        soil="scraped and messy",
        zone={"ground"},
        keyword="hoe",
        tags={"garden", "hoe", "insurance"},
    )
}

PRIZES = {
    "greenhouse": Prize(
        label="greenhouse window",
        phrase="the thin glass greenhouse window",
        type="window",
        region="ground",
    ),
    "statue": Prize(
        label="garden statue",
        phrase="the little stone garden statue",
        type="statue",
        region="ground",
    ),
}

POLICIES = {
    "garden_insurance": Policy(
        id="garden_insurance",
        label="garden insurance",
        covers={"greenhouse", "statue"},
        guards={"scraped"},
        prep="take a careful look at the garden insurance card",
        tail="used the policy only as a backup",
    )
}

HEROES = [
    ("Captain Sprout", "boy", "spirited"),
    ("Star Bloom", "girl", "brave"),
    ("Sunny Shield", "girl", "cheerful"),
]

SIDEKICKS = [
    ("Mira", "girl", "careful"),
    ("Nico", "boy", "gentle"),
    ("Pip", "boy", "smart"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    sidekick_name: str
    sidekick_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero garden storyworld with hoe, dialogue, and insurance.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: the hoe would not reasonably threaten {prize.label} in a way "
        f"that insurance could matter. Try the greenhouse window or the stone statue.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if act_id == "hoe" and prize_id in POLICIES["garden_insurance"].covers:
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if (args.place or "garden") not in SETTINGS:
            raise StoryError("(No valid setting matches the requested place.)")
        if (args.activity, args.prize) not in [("hoe", "greenhouse"), ("hoe", "statue")]:
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and args.activity is None or c[1] == args.activity
              and args.prize is None or c[2] == args.prize]
    if not combos:
        combos = valid_combos()
    place, act_id, prize_id = rng.choice(sorted(combos))
    name, gender, trait = rng.choice(HEROES)
    side_name, side_gender, _ = rng.choice(SIDEKICKS)
    return StoryParams(
        place=place,
        activity=act_id,
        prize=prize_id,
        hero_name=args.name or name,
        hero_gender=args.gender or gender,
        hero_trait=args.trait or trait,
        sidekick_name=args.sidekick or side_name,
        sidekick_gender=args.sidekick_gender or side_gender,
    )


def _risk_check(world: World, actor: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    hero = sim.get(actor.id)
    hero.memes["worry"] += 0.0
    sim.zone = set(activity.zone)
    if prize.region in sim.zone:
        return True
    return False


def _do_hoe(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1


def _apply_damage(world: World, actor: Entity, prize: Entity) -> None:
    if prize.region in world.zone:
        if any(item.protective and prize.label in item.covers for item in world.worn_items(actor)):
            return
        if actor.meters["mess"] >= THRESHOLD:
            sig = ("damage", prize.id)
            if sig in world.fired:
                return
            world.fired.add(sig)
            prize.meters["damage"] += 1
            prize.memes["worry"] += 1
            world.say(f"The {prize.label} got a little chipped.")


def story_setup(world: World, hero: Entity, sidekick: Entity, activity: Activity, prize: Entity, policy: Entity) -> None:
    world.say(
        f"{hero.id} was a superhero who loved helping in {world.setting.place}. "
        f"{hero.pronoun().capitalize()} wore a bright cape and smiled at every weed."
    )
    world.say(
        f"{hero.id} liked {activity.gerund}, and {sidekick.id} liked watching {hero.id} save the day."
    )
    world.say(
        f"That morning, {hero.id} carried {hero.pronoun('possessive')} {policy.label} card in a little pocket."
    )
    world.say(f"The card was for {prize.label}, just in case something went wrong.")


def story_conflict(world: World, hero: Entity, sidekick: Entity, activity: Activity, prize: Entity) -> None:
    world.para()
    world.say(f'"Can I {activity.verb}?" {hero.id} asked, lifting the hoe.')
    world.say(
        f'"Maybe," said {sidekick.id}, "but that hoe is close to the {prize.label}. '
        f'I do not want the glass to crack."'
    )
    world.say(
        f'"That is why we have insurance," {hero.id} said, "but I would rather use it as a backup, not a plan."'
    )
    hero.memes["worry"] += 0.5
    sidekick.memes["worry"] += 1.0


def story_resolution(world: World, hero: Entity, sidekick: Entity, activity: Activity, prize: Entity, policy: Entity) -> None:
    world.para()
    world.say(
        f'"Then use the safe rows," said {sidekick.id}. "The insurance card can stay in your pocket."'
    )
    world.say(
        f'{hero.id} nodded. {hero.id} moved one careful step at a time and kept the hoe low.'
    )
    _do_hoe(world, hero, activity)
    _apply_damage(world, hero, prize)
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    sidekick.memes["worry"] = max(0.0, sidekick.memes["worry"] - 0.5)
    hero.memes["pride"] += 1
    sidekick.memes["calm"] += 1
    world.say(
        f'Soon the weeds were gone, the {prize.label} stayed safe, and {hero.id} smiled. '
        f'"See?" {hero.id} said. "A real superhero uses care before claims."'
    )
    world.say(
        f"{sidekick.id} laughed. " f'"And the best insurance is a careful hero," {sidekick.id} said.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_gender))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region))
    policy_def = POLICIES["garden_insurance"]
    policy = world.add(Entity(id=policy_def.id, type="policy", label=policy_def.label, protective=True, covers=set(policy_def.covers)))
    world.facts.update(hero=hero, sidekick=sidekick, prize=prize, activity=activity, policy=policy, setting=setting)
    story_setup(world, hero, sidekick, activity, prize, policy)
    story_conflict(world, hero, sidekick, activity, prize)
    story_resolution(world, hero, sidekick, activity, prize, policy)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes "{f["activity"].keyword}" and "insurance".',
        f"Tell a dialogue story where {f['hero'].id} wants to {f['activity'].verb} but {f['sidekick'].id} worries about {f['prize'].label}.",
        f"Write a gentle superhero story about a hoe, a fragile garden thing, and a careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, prize, activity = f["hero"], f["sidekick"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the garden?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why was {sidekick.id} worried?",
            answer=f"{sidekick.id} worried that the hoe might hurt the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} say insurance was for?",
            answer="Insurance was for accidents, not for careless choices.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} used the hoe carefully, the {prize.label} stayed safe, and the garden got tidier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is insurance for?",
            answer="Insurance is a plan that can help pay for damage after an accident.",
        ),
        QAItem(
            question="What is a hoe used for?",
            answer="A hoe is a garden tool used to loosen soil and pull weeds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(P) :- prize(P), in_zone(P), hoe_activity.
valid_story(P) :- at_risk(P), policy_covers(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("hoe_activity"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        if pid in POLICIES["garden_insurance"].covers:
            lines.append(asp.fact("policy_covers", pid))
            lines.append(asp.fact("in_zone", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {("greenhouse",), ("statue",)}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", sorted(cl))
    print("  python:", sorted(py))
    return 1


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
    StoryParams(place="garden", activity="hoe", prize="greenhouse", hero_name="Captain Sprout", hero_gender="boy", hero_trait="spirited", sidekick_name="Mira", sidekick_gender="girl"),
    StoryParams(place="yard", activity="hoe", prize="statue", hero_name="Star Bloom", hero_gender="girl", hero_trait="brave", sidekick_name="Nico", sidekick_gender="boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
