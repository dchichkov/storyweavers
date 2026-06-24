#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/paralyze_loft_forest_trail_foreshadowing_twist_tall.py
========================================================================================================

A standalone storyworld for a Tall Tale on a forest trail, built from the seed words
"paralyze" and "loft" and shaped around foreshadowing and a twist.

Premise:
- A tall, strong traveler hikes a forest trail with a prize to carry.
- A looming snag is hinted at early through foreshadowing signs in the woods.
- The twist resolves the danger in a surprising but reasonable way.

The world models physical meters and emotional memes. The prose is driven by state:
anticipation, trouble, method, and consequence.
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


# ----------------------------- World model ---------------------------------

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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the forest trail"
    trail_name: str = "forest trail"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.weather = self.weather
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


def _rule_paralyze(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("fear", 0) < THRESHOLD:
            continue
        if actor.meters.get("blocked", 0) < THRESHOLD:
            continue
        sig = ("paralyze", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["freeze"] = actor.memes.get("freeze", 0) + 1
        out.append(f"{actor.pronoun().capitalize()} felt paralyzed for a moment.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_paralyze,):
            out = rule(world)
            if out:
                produced.extend(out)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_problem(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["blocked"] = sim.get(actor.id).meters.get("blocked", 0) + 1
    sim.get(actor.id).memes["fear"] = sim.get(actor.id).memes.get("fear", 0) + 1
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("jostled", 0) >= THRESHOLD


# ----------------------------- Registries ----------------------------------

SETTINGS = {
    "forest_trail": Setting(place="the forest trail", trail_name="forest trail", affords={"loft"}),
}

ACTIVITIES = {
    "loft": Activity(
        id="loft",
        verb="loft the lantern high",
        gerund="lofting the lantern high",
        rush="lift the lantern up fast",
        effect="glow",
        risk="the lantern could bump branches and go dim",
        keyword="loft",
        tags={"loft", "light", "trail"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a bright brass lantern",
        region="hand",
    ),
    "bundle": Prize(
        id="bundle",
        label="bundle",
        phrase="a tied-up bundle of trail maps",
        region="arms",
        plural=False,
    ),
}

TOOLS = [
    Tool(
        id="hook_staff",
        label="a hook staff",
        prep="take up a hook staff and keep the lantern steady",
        tail="used the hook staff to guide the lantern past the branches",
        helps={"loft"},
    ),
    Tool(
        id="strap",
        label="a shoulder strap",
        prep="fasten a shoulder strap and hold the bundle close",
        tail="used the shoulder strap to keep the bundle from bumping",
        helps={"carry"},
    ),
]

NAMES = ["Hank", "Mabel", "Jeb", "June", "Cal", "Nell", "Bo", "Ivy"]
TRAITS = ["tall", "strong", "steady", "plainspoken", "spry"]


# ----------------------------- Story params --------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ----------------------------- Story logic ---------------------------------

def foreshadow_line(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    world.say(
        f"At the edge of the forest trail, {hero.id} noticed a low branch bent like a knuckle, "
        f"and the wind kept whispering through it as if warning about {act.risk}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had come with {hero.pronoun('possessive')} {prize.label}, "
        f"and the little creek beside the trail glittered like it knew a secret."
    )


def introduce(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('height_word', 0) and 'tall'} {hero.type} who loved "
        f"{act.gerund} on the forest trail."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {prize.label} "
        f"as carefully as if it were a nest egg made of moonlight."
    )


def trouble(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    hero.meters["blocked"] = hero.meters.get("blocked", 0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(
        f"Then a thorny tangle snagged the path, and {hero.id} had to stop short just when "
        f"{hero.pronoun()} meant to {act.verb}."
    )
    world.say(
        f"The snag made {hero.pronoun('possessive')} hands go still, almost as if the trail itself "
        f"had tried to paralyze {hero.pronoun('object')}."
    )
    propagate(world)


def twist_solution(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    tool = TOOLS[0] if act.id == "loft" else TOOLS[-1]
    world.say(
        f"That was when the twist came: {hero.id} used {tool.label} not to fight the branch, "
        f"but to loft the lantern over it."
    )
    world.say(
        f"{tool.tail.capitalize()}, and the bright beam slid ahead on the trail like a gold ribbon."
    )
    prize.meters["jostled"] = 0
    hero.memes["fear"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"Soon the forest was all safe light and long shadows, and {hero.id} kept walking with "
        f"{hero.pronoun('possessive')} {prize.label} shining steady in {hero.pronoun('possessive')} hand."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="man", meters={"height_word": 1}))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    hero.meters["height_word"] = 1
    world.weather = "clear"

    hero.meters["tall"] = 1
    hero.memes["confidence"] = 1
    world.say(
        f"{hero.id} was a {trait} tall fellow with a smile big enough to light a porch."
    )
    world.say(
        f"{hero.id} loved the {setting.trail_name} and {activity.gerund} after supper."
    )
    foreshadow_line(world, hero, activity, prize)
    world.para()
    trouble(world, hero, activity, prize)
    world.para()
    twist_solution(world, hero, activity, prize)

    world.facts.update(hero=hero, prize=prize, activity=activity, setting=setting)
    return world


# ----------------------------- Q&A -----------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f"Write a tall tale about {hero.id} on a {f['setting'].trail_name} with a twist and a foreshadowed danger.",
        f"Tell a child-friendly story where someone tries to {act.keyword} on the forest trail and keeps a {prize.label} safe.",
        f"Make a short tall tale that includes the words 'paralyze' and 'loft' and ends with a surprising fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a tall fellow on the forest trail."
        ),
        QAItem(
            question=f"What warning hinted that trouble was coming?",
            answer=f"The bent branch and whispering wind foreshadowed that the trail could paralyze the moment and snag the lantern."
        ),
        QAItem(
            question=f"What was the twist that solved the problem?",
            answer=f"{hero.id} did not push through the branch. {hero.id} used a hook staff to loft the lantern over it and kept going safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a forest trail?",
            answer="A forest trail is a narrow path through the woods where people can walk, look for birds, and keep an eye out for roots and branches."
        ),
        QAItem(
            question="What does it mean to loft something?",
            answer="To loft something means to lift it up high, often so it can clear an obstacle or be seen from far away."
        ),
        QAItem(
            question="What is a foreshadowing clue in a story?",
            answer="A foreshadowing clue is a small sign early in the story that hints something important may happen later."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how the problem gets solved."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ----------------------------- ASP twin ------------------------------------

ASP_RULES = r"""
% A trail story is valid when the activity is supported by the setting and a
% compatible fix exists that can carry the story through the obstacle.
supported(S, A) :- affords(S, A).
foreshadowed(A) :- activity(A).
twist(A) :- activity(A).

valid_story(S, A, P) :- supported(S, A), prize(P), foreshadowed(A), twist(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_ok = {(s, a, p) for s in SETTINGS for a in SETTINGS[s].affords for p in PRIZES}
    asp_ok = set(asp_valid_stories())
    if asp_ok == python_ok:
        print(f"OK: ASP matches Python ({len(asp_ok)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_ok - python_ok:
        print(" only in ASP:", sorted(asp_ok - python_ok))
    if python_ok - asp_ok:
        print(" only in Python:", sorted(python_ok - asp_ok))
    return 1


# ----------------------------- CLI -----------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale on a forest trail with foreshadowing and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    prize = args.prize or rng.choice(list(PRIZES))
    if activity not in SETTINGS[place].affords:
        raise StoryError("This activity does not fit the forest trail setting.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = StoryParams(place="forest_trail", activity="loft", prize="lantern", name="Hank", trait="tall")
        samples = [generate(cur)]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
