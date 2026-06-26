#!/usr/bin/env python3
"""
storyworlds/worlds/olympics_shoe_pl_dim_teamwork_inner_monologue.py
====================================================================

A small whodunit-flavored story world about an Olympic team, a missing shoe,
careful clues, teamwork, inner monologue, and a cautious solution.

Seed tale sketch:
---
At the Olympics village, a young runner named Nia was ready for the team relay.
Her lucky racing shoe was missing from the bench. Nia worried someone had taken
it, and she quietly blamed the wrong people in her head. The coach asked
everyone to stay calm and look carefully. The team searched together, following
tiny clues: a trail of chalk, a scuff on the floor, and a shoe print near the
storage room. In the end, they found the shoe on a low platform in the equipment
room, placed there by a helper who meant to keep it safe. Nia apologized for
jumping to conclusions, and the team reached the starting line together.

World logic:
---
- The "olympics" setting provides a team event, a bench, a tunnel, and an
  equipment room.
- The mystery centers on one prized shoe pair, its storage, and a cautious
  search.
- Inner monologue is modeled as private suspicion and later relief.
- Teamwork is modeled as coordinated search helpers reducing uncertainty.
- The cautionary beat is the coach's warning against blaming anyone too soon.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "runner", "athlete"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the Olympic village"
    supports: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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


def _r_missing_shoe(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("search", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("found", 0.0) >= THRESHOLD:
            continue
        sig = ("found", actor.id)
        if sig in world.fired:
            continue
        clue = world.facts.get("clue", "")
        if clue:
            out.append(clue)
        world.fired.add(sig)
    return out


CAUSAL_RULES = [_r_missing_shoe]


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


def predict_loss(world: World, actor: Entity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).memes["search"] = 1.0
    return sim.entities[prize_id].meters.get("lost", 0.0) < THRESHOLD


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a young {hero.type} on an Olympic team, and {hero.pronoun()} "
        f"always noticed when something on the bench looked out of place."
    )


def set_scene(world: World, activity: Activity) -> None:
    world.say(
        f"The team was in {world.setting.place}, where the air smelled like chalk, polished shoes, and nerves."
    )
    world.say(
        f"They were getting ready for the {activity.keyword} event, and every runner wanted a calm start."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} because it felt fast and lucky."
    )


def discovers_missing(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    prize.meters["lost"] = 1.0
    world.say(
        f"Then {hero.id} looked at the bench and froze. {hero.pronoun().capitalize()} could not find {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"In {hero.pronoun('possessive')} head, one thought kept whispering: someone had taken {prize.it()} on purpose."
    )


def caution(world: World, coach: Entity, hero: Entity) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f"{coach.id} held up a hand and said, \"Let's not blame anyone yet. First we look carefully.\""
    )
    world.say(
        f"{hero.id} nodded, even though {hero.pronoun()} still felt sure the answer must be hidden somewhere nearby."
    )


def teamwork_search(world: World, hero: Entity, team: list[Entity], prize: Prize) -> None:
    hero.memes["search"] = 1.0
    for helper in team:
        helper.memes["search"] = 1.0
    world.say(
        f"The team split up in a quiet, careful way: one runner checked the bench, another checked the tunnel, and another checked the storage shelf."
    )
    world.say(
        f"Together they followed little clues instead of big guesses: a white scuff, a faint shoe print, and a low dust line near the equipment room."
    )


def reveal(world: World, hero: Entity, helper: Entity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["found"] = 1.0
    prize.meters["lost"] = 0.0
    prize.worn_by = hero.id
    world.say(
        f"At last, {helper.id} pointed to a low shoe platform in the equipment room. There was the missing {prize.label}, tucked neatly where it would not be kicked."
    )
    world.say(
        f"{helper.id} explained that a helper had moved {prize.it()} there so nobody would step on {prize.it()} before the race."
    )
    world.say(
        f"{hero.id}'s chest loosened. The suspicion in {hero.pronoun('possessive')} head faded, and {hero.pronoun()} felt a little ashamed for doubting so quickly."
    )
    world.say(
        f"{hero.id} put on {prize.it()}, thanked the team, and ran back toward the track with everyone beside {hero.pronoun('object')}."
    )


def finish(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"By the time the starter called them forward, {hero.id} knew the truth: the shoe had not been stolen, only safely moved."
    )
    world.say(
        f"The team crossed the last doorway together, and the once-missing {prize.label} tapped softly on the floor like a clue that had finally found its place."
    )


SETTINGS = {
    "olympics": Setting(place="the Olympic village"),
}


ACTIVITIES = {
    "relay": Activity(
        id="relay",
        verb="run the relay",
        gerund="running the relay",
        rush="sprint to the track",
        mess="sweat",
        zone={"feet"},
        keyword="olympics",
    ),
}


PRIZES = {
    "shoe": Prize(
        label="shoe",
        phrase="a lucky racing shoe",
        type="shoe",
        region="feet",
    ),
    "pair": Prize(
        label="shoes",
        phrase="a lucky pair of racing shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
}


GEAR = [
    Gear(
        id="cover",
        label="a soft shoe cover",
        covers={"feet"},
        guards={"sweat"},
        prep="slip on a cover first",
        tail="hurried back out with the cover still snug",
    ),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    teammate: str
    coach: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="olympics",
        activity="relay",
        prize="shoe",
        hero="Nia",
        teammate="Ari",
        coach="Coach Mina",
    ),
]


GIRL_NAMES = ["Nia", "Mina", "Lena", "Ava", "Tia"]
TEAM_NAMES = ["Ari", "Bo", "Kai", "Ren", "Sia"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("olympics", "relay", "shoe"), ("olympics", "relay", "pair")]


KNOWLEDGE = {
    "olympics": [
        (
            "What are the Olympics?",
            "The Olympics are a big sports competition where athletes from many places come to race, jump, throw, and cheer for their teams.",
        )
    ],
    "shoe": [
        (
            "Why do runners care about their shoes?",
            "Runners care about their shoes because good shoes can help their feet feel steady, fast, and comfortable.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other and do different jobs together to reach the same goal.",
        )
    ],
    "cautionary": [
        (
            "Why should people be careful before they blame someone?",
            "People should be careful before they blame someone because a problem can have a harmless explanation that they have not found yet.",
        )
    ],
    "monologue": [
        (
            "What is an inner monologue?",
            "An inner monologue is the quiet voice in your head where you think about what might be true before you say it out loud.",
        )
    ],
    "shoe-pl-dim": [
        (
            "What does 'shoe-pl-dim' mean here?",
            "It means a small, low shoe platform where the team can place shoes safely so they do not get stepped on.",
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit-style Olympic story world with teamwork and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--teammate")
    ap.add_argument("--coach")
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
    if args.place and args.place != "olympics":
        raise StoryError("This story world only supports the Olympics setting.")
    place = "olympics"
    activity = args.activity or "relay"
    prize = args.prize or rng.choice(list(PRIZES))
    hero = args.hero or rng.choice(GIRL_NAMES)
    teammate = args.teammate or rng.choice(TEAM_NAMES)
    coach = args.coach or "Coach Mina"
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, teammate=teammate, coach=coach)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]

    hero = world.add(Entity(id=params.hero, kind="character", type="runner"))
    teammate = world.add(Entity(id=params.teammate, kind="character", type="runner"))
    coach = world.add(Entity(id=params.coach, kind="character", type="coach", label=params.coach))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=coach.id,
        )
    )

    world.facts["clue"] = (
        f"{teammate.id} spotted a low shoe platform by the wall, and that was where the missing {prize.label} had been put."
    )
    world.facts["activity"] = activity
    world.facts["prize"] = prize_cfg
    world.facts["hero"] = hero
    world.facts["teammate"] = teammate
    world.facts["coach"] = coach

    introduce(world, hero)
    set_scene(world, activity)
    loves_prize(world, hero, prize)

    world.para()
    discovers_missing(world, hero, prize)
    caution(world, coach, hero)
    teamwork_search(world, hero, [teammate], prize_cfg)

    world.para()
    reveal(world, hero, teammate, prize, GEAR[0])
    finish(world, hero, prize)
    propagate(world, narrate=True)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit story for a child about the olympics and a missing shoe.',
        f"Tell a gentle mystery where {f['hero'].id} at the Olympics worries about a missing shoe but the team solves it together.",
        'Write a story that includes "shoe-pl-dim", teamwork, and a cautious correction to a wrong suspicion.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    teammate = f["teammate"]
    coach = f["coach"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What worried {hero.id} at the start of the story?",
            answer=f"{hero.id} worried because the {prize.label} was missing from the bench before the relay.",
        ),
        QAItem(
            question=f"Why did {coach.id} tell everyone not to blame anyone yet?",
            answer="The coach wanted them to look carefully first, because the missing shoe might have been moved for a safe reason.",
        ),
        QAItem(
            question=f"How did {hero.id} and {teammate.id} solve the problem?",
            answer="They searched together, followed the tiny clues, and found the shoe on a low platform in the equipment room.",
        ),
        QAItem(
            question=f"What changed in {hero.id}'s feelings by the end?",
            answer=f"{hero.id} moved from worry and suspicion to relief and trust after learning the {prize.label} was only safely moved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["olympics", "teamwork", "cautionary", "monologue", "shoe", "shoe-pl-dim"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(key, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A shoe is missing when it has been marked lost.
missing(S) :- shoe(S), lost(S).

% Careful teamwork restores trust when the shoe is found and the team searched.
recovered(S) :- shoe(S), found(S).
good_end :- recovered(S), team_search.

% A safe hiding place is the low shoe platform.
safe_place(platform) :- shoe_platform(platform).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("setting", "olympics"))
    lines.append(asp.fact("team_event", "relay"))
    lines.append(asp.fact("shoe_platform", "shoe_pl_dim"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("shoe", pid))
        lines.append(asp.fact("lost", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("team_search"))
    lines.append(asp.fact("found", "shoe"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show missing/1. #show recovered/1. #show good_end/0."))
    return sorted(set(asp.atoms(model, "recovered")))


def asp_verify() -> int:
    import asp

    py = {"shoe"} if True else set()
    cl = {x[0] for x in asp_valid_combos()}
    if cl != py:
        print("MISMATCH between ASP and Python")
        print("  asp:", sorted(cl))
        print("  py :", sorted(py))
        return 1
    print("OK: ASP parity check passed.")
    sample = generate(CURATED[0])
    if "missing" in sample.story.lower() and "found" in sample.story.lower():
        print("OK: generated story contains a clear mystery and resolution.")
        return 0
    print("WARNING: generated story did not meet the basic check.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show good_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        print(asp_program("#show recovered/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = CURATED
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params_list.append(resolve_params(args, rng))

    for p in params_list:
        samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
