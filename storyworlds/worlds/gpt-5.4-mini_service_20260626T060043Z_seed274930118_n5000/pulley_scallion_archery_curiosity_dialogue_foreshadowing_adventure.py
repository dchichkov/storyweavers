#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pulley_scallion_archery_curiosity_dialogue_foreshadowing_adventure.py
================================================================================================================

A compact adventure storyworld about a curious child, a helpful pulley,
a bundle of scallions, and an archery practice problem that becomes a safe
rescue.

The world premise:
- A child loves exploring the old yard behind a garden shed.
- A heavy basket of scallions is stuck up on a ledge.
- Nearby, an archery target is waiting for practice.
- The child wants to pull the basket down and still get to practice archery.
- The grown-up worries that the string, the basket, and the arrows could become
  tangled or unsafe.
- The solution is to use the pulley first, move the scallions safely, and then
  set up archery practice away from the rope.

This is a small state-driven simulation with physical meters and emotional memes.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden yard"
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
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str
    protects_from: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "garden_yard": Setting(place="the garden yard", affords={"pulley", "scallion", "archery"}),
    "shed_lane": Setting(place="the shed lane", affords={"pulley", "scallion", "archery"}),
    "orchard_edge": Setting(place="the orchard edge", affords={"pulley", "scallion", "archery"}),
}

ACTIVITIES = {
    "pulley": Activity(
        id="pulley",
        verb="use the pulley",
        gerund="pulling on the pulley rope",
        rush="grab the rope and yank too hard",
        mess="tugged",
        zone={"rope"},
        keyword="pulley",
        tags={"pulley", "rope", "helper"},
    ),
    "scallion": Activity(
        id="scallion",
        verb="lift the scallions",
        gerund="lifting the scallion basket",
        rush="haul the basket by hand",
        mess="swayed",
        zone={"basket"},
        keyword="scallion",
        tags={"scallion", "garden"},
    ),
    "archery": Activity(
        id="archery",
        verb="practice archery",
        gerund="practicing archery",
        rush="run to the target with arrows",
        mess="scattered",
        zone={"target", "arrow"},
        keyword="archery",
        tags={"archery", "target", "arrow"},
    ),
}

PRIZES = {
    "basket": Prize(label="basket", phrase="a heavy basket of scallions", region="basket", plural=False),
    "target": Prize(label="target", phrase="a bright paper target", region="target", plural=False),
    "arrows": Prize(label="arrows", phrase="a little quiver of practice arrows", region="arrow", plural=True),
}

TOOLS = {
    "pulley": Tool(
        id="pulley",
        label="the pulley",
        helps={"pulley"},
        prep="tie the basket to the pulley and pull slowly",
        tail="pulled the scallions down one safe inch at a time",
        protects_from={"tugged", "scattered"},
    ),
    "screen": Tool(
        id="screen",
        label="the target screen",
        helps={"archery"},
        prep="move the target screen behind the fence",
        tail="set the target up far from the rope",
        protects_from={"tugged"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Leo", "Ben", "Eli", "Theo", "Milo", "Owen"]


def _narrate_state_change(world: World, actor: Entity, kind: str, amount: float = 1.0) -> None:
    actor.meters[kind] = actor.meters.get(kind, 0.0) + amount


def predict_problem(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    act = sim.get(actor.id)
    if activity.id == "pulley":
        act.meters["tugged"] = act.meters.get("tugged", 0.0) + 1
    elif activity.id == "scallion":
        act.meters["swayed"] = act.meters.get("swayed", 0.0) + 1
    else:
        act.meters["scattered"] = act.meters.get("scattered", 0.0) + 1
    risky = activity.id == "archery" and prize.id == "arrows"
    return {"risky": risky, "messy": risky or activity.id == "pulley"}


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved curious adventures, and "
        f"{helper.label} often came along with patient advice."
    )


def setting_line(world: World, activity: Activity) -> None:
    world.say(
        f"At {world.setting.place}, a rope hung beside a high ledge, a basket of scallions waited nearby, "
        f"and an archery target stood in the open grass."
    )


def curiosity(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} noticed the pulley first and asked, \"What happens if I pull it?\" "
        f"{hero.pronoun().capitalize()} also peeked at the scallions and the target, wondering how all three things fit together."
    )


def dialogue_warning(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    pred = predict_problem(world, hero, activity, prize)
    if pred["risky"]:
        world.say(
            f'"Careful," {helper.id} said. "If you rush the rope and then run to archery, the basket could swing, '
            f"and the arrows could get mixed up."
        )
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1


def foreshadowing(world: World, hero: Entity) -> None:
    world.say(
        f"Near the fence, a loose knot fluttered in the wind, and {hero.id} remembered that tricky knots usually meant slower steps later."
    )


def choose_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    if activity.id == "pulley" and prize.id == "basket":
        return TOOLS["pulley"]
    if activity.id == "archery" and prize.id == "target":
        return TOOLS["screen"]
    return None


def do_pulley(world: World, hero: Entity, helper: Entity, prize: Entity, tool: Tool) -> None:
    if "pulley" not in world.setting.affords:
        raise StoryError("This setting cannot support the pulley scene.")
    hero.meters["tugged"] = hero.meters.get("tugged", 0.0) + 1
    world.zone = {"rope", "basket"}
    world.say(
        f"{hero.id} and {helper.label} chose to {tool.prep}. {hero.id} pulled gently, and {tool.tail}."
    )
    prize.meters["safe"] = prize.meters.get("safe", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1


def do_scallions(world: World, hero: Entity, prize: Entity) -> None:
    hero.meters["swayed"] = hero.meters.get("swayed", 0.0) + 1
    world.say(
        f"The basket swayed once, then settled. Fresh scallions spilled into a tidy pile, and the garden smelled bright and green."
    )
    prize.meters["delivered"] = prize.meters.get("delivered", 0.0) + 1


def do_archery(world: World, hero: Entity, helper: Entity, prize: Entity, tool: Tool) -> None:
    if "archery" not in world.setting.affords:
        raise StoryError("This setting cannot support archery practice.")
    hero.meters["focused"] = hero.meters.get("focused", 0.0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    world.zone = {"target", "arrow"}
    world.say(
        f"After that, {helper.label} helped {hero.id} {tool.prep if tool.id == 'screen' else 'set up the target'}."
    )
    world.say(
        f"{hero.id} practiced archery with a calm breath, and the arrows thudded safely into the paper target."
    )
    prize.meters["hit"] = prize.meters.get("hit", 0.0) + 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, tool_id: str, hero_name: str, gender: str, helper_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label="the helper"))
    prize = world.add(Entity(id=prize_cfg.label, kind="thing", type=prize_cfg.label, label=prize_cfg.label))
    tool = TOOLS[tool_id]

    introduce(world, hero, helper)
    setting_line(world, activity)
    curiosity(world, hero, activity, prize)
    world.para()
    dialogue_warning(world, helper, hero, activity, prize)
    foreshadowing(world, hero)
    world.para()

    if activity.id == "pulley":
        do_pulley(world, hero, helper, prize, tool)
        do_scallions(world, hero, prize)
        world.para()
        do_archery(world, hero, helper, prize, TOOLS["screen"])
    elif activity.id == "scallion":
        do_scallions(world, hero, prize)
        world.say(f"{hero.id} packed the scallions into a basket before moving the target away for practice.")
        do_archery(world, hero, helper, prize, TOOLS["screen"])
    else:
        do_archery(world, hero, helper, prize, tool)

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, tool=tool, setting=setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if act_id == "pulley" and prize_id == "basket":
                    combos.append((place, act_id, prize_id))
                elif act_id == "archery" and prize_id == "target":
                    combos.append((place, act_id, prize_id))
                elif act_id == "scallion" and prize_id == "basket":
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with pulley, scallion, and archery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    tool = args.tool or ("pulley" if activity == "pulley" else "screen")
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, name=name, gender=gender, helper=helper)


def story_text(world: World) -> str:
    return world.render()


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for children that includes a pulley, a scallion basket, and archery practice.',
        f"Tell a curious, gentle adventure about {f['hero'].id} and the helper at {f['setting'].place}.",
        f'Write a story where a child asks about a pulley, listens to dialogue, notices a foreshadowing clue, and then solves a garden problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} first wonder about at {world.setting.place}?",
            answer=f"{hero.id} first wondered about the pulley rope, and then about the scallions and the archery target nearby."
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.id} to be careful?",
            answer=f"{helper.label} warned {hero.id} because rushing the rope could make the basket swing, and then archery gear could get mixed up."
        ),
        QAItem(
            question=f"What happened after the pulley was used safely?",
            answer=f"The scallions came down in a tidy pile, and then {hero.id} could practice archery without getting tangled in the rope."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pulley for?",
            answer="A pulley is a wheel and rope that helps lift or lower heavy things more easily."
        ),
        QAItem(
            question="What are scallions?",
            answer="Scallions are long green onions with a mild taste."
        ),
        QAItem(
            question="What is archery?",
            answer="Archery is the sport of using a bow to shoot arrows at a target."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
        for p in sorted(tool.protects_from):
            lines.append(asp.fact("protects_from", tid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Act,Prize) :- place(Place), activity(Act), prize(Prize), combo(Place,Act,Prize).

combo(Place,pulley,basket) :- place(Place).
combo(Place,scallion,basket) :- place(Place).
combo(Place,archery,target) :- place(Place).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.tool,
        params.name,
        params.gender,
        params.helper,
    )
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="garden_yard", activity="pulley", prize="basket", tool="pulley", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="shed_lane", activity="archery", prize="target", tool="screen", name="Leo", gender="boy", helper="father"),
    StoryParams(place="orchard_edge", activity="scallion", prize="basket", tool="pulley", name="Nora", gender="girl", helper="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
