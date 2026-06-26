#!/usr/bin/env python3
"""
A standalone storyworld for a heartwarming, cautionary misunderstanding in a
vegetable garden.

Seed tale premise:
- A child and a grown-up are in a vegetable garden.
- A worried misunderstanding causes a small conflict.
- The child learns a cautionary lesson, says pardon, and the ending turns warm.

The world model tracks:
- physical meters: dirt, thirst, ripeness, damage, warmth, tidiness
- emotional memes: worry, kindness, confusion, relief, gratitude, love

The simulated turn is driven by garden state:
- picking the wrong vegetable damages the wrong plant
- a careful correction and apology repair the misunderstanding
- a snuggle closes the story with warmth and connection
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
    edible: bool = False
    ripe: bool = False
    planted: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str = "the vegetable garden"


@dataclass
class Action:
    id: str
    verb: str
    caution: str
    mistake: str
    fix: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _narrate_meter_change(entity: Entity, key: str, amount: float, label: str) -> str:
    val = entity.meters.get(key, 0.0)
    if val >= THRESHOLD:
        return f"{entity.label or entity.id} grew {label}."
    return ""


def _rule_damage(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("confused", 0.0) < THRESHOLD:
        return out
    if child.meters.get("pluck", 0.0) < THRESHOLD:
        return out
    plant = world.get("plant")
    sig = ("damage", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["damage"] = plant.meters.get("damage", 0.0) + 1.0
    plant.meters["tidy"] = max(0.0, plant.meters.get("tidy", 0.0) - 1.0)
    out.append(f"The wrong leaves bent and the plant looked sad.")
    return out


def _rule_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("grownup").memes.get("worry", 0.0) < THRESHOLD:
        return out
    if world.get("child").memes.get("confused", 0.0) < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["worry"] = world.get("child").memes.get("worry", 0.0) + 0.5
    out.append("The little pause between them felt heavy for a moment.")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grownup = world.get("grownup")
    if child.memes.get("pardoned", 0.0) < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    grownup.memes["relief"] = grownup.memes.get("relief", 0.0) + 1.0
    out.append("Their faces softened right away.")
    return out


CAUSAL_RULES = [_rule_damage, _rule_worry, _rule_relief]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


SETTING = Setting(place="the vegetable garden")

ACTIVITIES = {
    "snip": Action(
        id="snip",
        verb="snip the lettuce",
        caution="The leaves should be checked before cutting.",
        mistake="The child snipped the wrong green sprig.",
        fix="They slowed down and looked again.",
        risk="cutting the wrong plant",
        tags={"garden", "cautionary", "misunderstanding"},
    ),
    "pick": Action(
        id="pick",
        verb="pick the ripe tomato",
        caution="Only the ripe tomato should be picked.",
        mistake="The child reached for the wrong vine.",
        fix="They asked which tomato was ready.",
        risk="pulling a plant too soon",
        tags={"garden", "cautionary", "misunderstanding"},
    ),
    "weed": Action(
        id="weed",
        verb="pull the weeds",
        caution="Weeds are okay to pull, but not seedlings.",
        mistake="The child mistook a baby carrot for a weed.",
        fix="They learned to check the tiny leaves first.",
        risk="uprooting a seedling",
        tags={"garden", "cautionary", "misunderstanding"},
    ),
}

CURATED = ["snip", "pick", "weed"]

NAMES = ["Mina", "Leo", "Pia", "Noah", "Ivy", "Ben"]
GROWNUP_NAMES = ["Mama", "Papa", "Aunt June", "Uncle Ray"]


@dataclass
class StoryParams:
    activity: str
    name: str
    grownup: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming garden misunderstanding storyworld.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--grownup", choices=GROWNUP_NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in ACTIVITIES:
        for n in NAMES:
            for g in GROWNUP_NAMES:
                combos.append((a, n, g))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    return StoryParams(
        activity=args.activity or rng.choice(list(ACTIVITIES)),
        name=args.name or rng.choice(NAMES),
        grownup=args.grownup or rng.choice(GROWNUP_NAMES),
    )


def introduce(world: World, child: Entity, grownup: Entity, action: Action) -> None:
    world.say(
        f"{child.label} loved helping in {world.setting.place}, and {grownup.label} liked working beside {child.pronoun('object')}."
    )
    world.say(
        f"One bright day, they planned to {action.verb}, because the garden looked ready."
    )


def set_up_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id="child", kind="character", type="girl" if params.name in {"Mina", "Pia", "Ivy"} else "boy",
        label=params.name, meters={"warmth": 0.0, "dirt": 0.0}, memes={"curious": 1.0}
    ))
    grownup = world.add(Entity(
        id="grownup", kind="character", type="mother" if params.grownup in {"Mama", "Aunt June"} else "father",
        label=params.grownup, meters={"warmth": 1.0}, memes={"kindness": 1.0}
    ))
    plant = world.add(Entity(
        id="plant", kind="thing", type="vegetable",
        label="the little carrot plant", phrase="a tiny carrot plant",
        edible=True, ripe=False, planted=True, meters={"damage": 0.0, "ripeness": 0.4, "tidy": 1.0},
    ))
    basket = world.add(Entity(
        id="basket", kind="thing", type="basket",
        label="the basket", phrase="a woven basket", meters={"tidy": 1.0}
    ))
    action = ACTIVITIES[params.activity]
    child.memes["curious"] = 1.0
    child.memes["confused"] = 0.0
    child.memes["pardon"] = 0.0
    grownup.memes["worry"] = 0.0
    introduce(world, child, grownup, action)
    world.para()
    world.say(f"{grownup.label} pointed out {action.caution.lower()}")
    world.say(f"{child.label} had a different thought and reached toward the green row.")
    child.memes["confused"] += 1.0
    child.meters["pluck"] = 1.0
    world.say(f"{child.label} thought the wrong sprig was the one to snip.")
    propagate(world)
    world.para()
    if world.get("plant").meters.get("damage", 0.0) >= THRESHOLD:
        world.say(f"{grownup.label} knelt down and gently explained the mistake.")
        grownup.memes["worry"] += 1.0
        child.memes["guilt"] = 1.0
        world.say(f"{child.label} took a breath and said, 'Pardon me, I thought that was the right one.'")
        child.memes["pardon"] = 1.0
        child.memes["confused"] = 0.0
        propagate(world)
        world.say(f"{grownup.label} smiled and said it was okay to learn slowly.")
        grownup.memes["love"] = grownup.memes.get("love", 0.0) + 1.0
        child.memes["love"] = child.memes.get("love", 0.0) + 1.0
        world.say(f"Then {grownup.label} showed {child.pronoun('object')} the right stem and the careful way to check it.")
        world.say(f"At the end, {child.label} gave {grownup.pronoun('object')} a snuggle, and the garden felt warm again.")
        child.meters["warmth"] = child.meters.get("warmth", 0.0) + 1.0
        grownup.meters["warmth"] = grownup.meters.get("warmth", 0.0) + 1.0
        world.get("plant").meters["tidy"] = 1.0
    world.facts.update(child=child, grownup=grownup, plant=plant, basket=basket, action=action)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    return [
        f'Write a heartwarming story for a small child about a garden misunderstanding using the word "pardon".',
        f"Tell a cautionary story in {world.setting.place} where {child.label} tries to {action.verb} but learns to look carefully first.",
        f"Write a gentle story with a mistake, an apology, and a snuggle at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, grownup, plant, action = f["child"], f["grownup"], f["plant"], f["action"]
    return [
        QAItem(
            question=f"Who was in the vegetable garden with {child.label}?",
            answer=f"{child.label} was in the vegetable garden with {grownup.label}, and they worked beside the little carrot plant.",
        ),
        QAItem(
            question=f"What did {child.label} think at first?",
            answer=f"{child.label} thought the wrong sprig was the right one to {action.verb.split(' ', 1)[0]}, which caused the misunderstanding.",
        ),
        QAItem(
            question=f"What did {child.label} say after the mistake?",
            answer=f"{child.label} said, 'Pardon me, I thought that was the right one,' and that helped calm everything down.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a snuggle, a smile, and a careful lesson about looking twice before touching a plant.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should someone look carefully before picking things in a garden?",
            answer="Because some plants are still growing, and looking carefully helps keep the wrong plant from getting hurt.",
        ),
        QAItem(
            question="What does a pardon mean?",
            answer="Pardon is a polite word people use when they want to say sorry or ask someone to forgive a mistake.",
        ),
        QAItem(
            question="Why can a snuggle help after a misunderstanding?",
            answer="A snuggle can help people feel safe and loved again after a worry or mix-up.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(garden).
activity(snip).
activity(pick).
activity(weed).
misunderstanding(snip).
misunderstanding(pick).
misunderstanding(weed).
cautionary(snip).
cautionary(pick).
cautionary(weed).

valid(A) :- activity(A), misunderstanding(A), cautionary(A).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "vegetable_garden"),
    ]
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("misunderstanding", aid))
        lines.append(asp.fact("cautionary", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(a,) for a in ACTIVITIES}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = set_up_world(params)
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, act in enumerate(CURATED):
            p = StoryParams(activity=act, name=NAMES[i % len(NAMES)], grownup=GROWNUP_NAMES[i % len(GROWNUP_NAMES)], seed=base_seed + i)
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
