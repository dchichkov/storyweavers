#!/usr/bin/env python3
"""
A small Space Adventure storyworld about a quest, teamwork, pee, and spite.

This world follows a tiny crew on a starship. One astronaut wants to finish a
quest, but a spiteful choice and a growing need to pee create trouble. The team
must cooperate, pause at the right place, and help each other reach the station
bathroom before the mission can continue.
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

SPACE_ACTIONS = {
    "quest": {
        "verb": "finish the quest",
        "noun": "quest",
        "goal": "find the glowing map chip",
    },
    "repair": {
        "verb": "repair the broken panel",
        "noun": "repair mission",
        "goal": "fix the blinking control panel",
    },
}

LOCATIONS = {
    "ship": "the starship",
    "hall": "the moon hall",
    "dock": "the space dock",
    "moon": "the moon base",
}

NAMES = ["Nova", "Zin", "Milo", "Tara", "Pip", "Luna", "Rae", "Sol"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    location: str
    action: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with quest, teamwork, pee, and spite.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--action", choices=SPACE_ACTIONS)
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--sidekick-name", dest="sidekick_name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    location = args.location or rng.choice(list(LOCATIONS))
    action = args.action or rng.choice(list(SPACE_ACTIONS))
    hero_name = args.hero_name or rng.choice(NAMES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(location=location, action=action, hero_name=hero_name, sidekick_name=sidekick_name)


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _urge_threshold() -> float:
    return 1.0


def _spite_threshold() -> float:
    return 1.0


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    bathroom = world.get("bathroom")

    if hero.meters.get("pee", 0.0) >= _urge_threshold() and ("need_warning", "hero") not in world.fired:
        world.fired.add(("need_warning", "hero"))
        _add_meme(hero, "worry", 1.0)
        out.append(f"{hero.id} wiggled and held still because {hero.pronoun('possessive')} bladder felt full.")

    if hero.memes.get("spite", 0.0) >= _spite_threshold() and ("spite_tension", "hero") not in world.fired:
        world.fired.add(("spite_tension", "hero"))
        _add_meme(sidekick, "concern", 1.0)
        out.append(f"{sidekick.id} saw the stubborn look on {hero.id}'s face and grew concerned.")

    if hero.meters.get("pee", 0.0) >= 2.0 and bathroom.meters.get("near", 0.0) >= 1.0 and ("bathroom_help", "hero") not in world.fired:
        world.fired.add(("bathroom_help", "hero"))
        _add_meme(hero, "relief", 1.0)
        _add_meme(sidekick, "pride", 1.0)
        out.append("The bathroom lights glowed ahead, and the crew knew the problem had a safe fix.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_need(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    _add_meter(hero, "pee", 1.0)
    propagate(sim, narrate=False)
    return hero.meters.get("pee", 0.0) >= 2.0


def tell(params: StoryParams) -> World:
    world = World(params.location)
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="child", label=params.sidekick_name))
    bathroom = world.add(Entity(id="bathroom", kind="thing", type="place", label="the station bathroom"))
    mapchip = world.add(Entity(id="mapchip", kind="thing", type="device", label="the glowing map chip"))

    world.facts.update(hero=hero, sidekick=sidekick, bathroom=bathroom, mapchip=mapchip, params=params)

    world.say(f"{hero.label} and {sidekick.label} were on a small quest at {LOCATIONS[params.location]}.")
    world.say(f"They wanted to {SPACE_ACTIONS[params.action]['verb']} and find {SPACE_ACTIONS[params.action]['goal']}.")
    world.say(f"{hero.label} loved space adventure missions, but {hero.pronoun('possessive')} tummy started saying pee, pee, pee.")

    world.para()
    _add_meter(hero, "pee", 1.0)
    _add_meme(hero, "spite", 1.0)
    world.say(f"Instead of asking right away, {hero.label} crossed {hero.pronoun('possessive')} arms in spite.")
    if predict_need(world):
        world.say(f"{sidekick.label} noticed that waiting would only make {hero.pronoun('object')} more uncomfortable.")
    world.say(f'"We can do this together," {sidekick.label} said. "First we find the bathroom, then we finish the quest."')
    _add_meter(bathroom, "near", 1.0)
    propagate(world, narrate=True)

    world.para()
    if hero.meters.get("pee", 0.0) >= 1.0:
        world.say(f"{hero.label} nodded, let the spite go, and walked with {sidekick.label} toward the bright door.")
    _add_meter(hero, "pee", 1.0)
    propagate(world, narrate=True)
    world.say(f"After a quick stop, {hero.label} felt light and happy again.")
    world.say(f"The two friends hurried back, finished the quest, and found {SPACE_ACTIONS[params.action]['goal']} together.")
    world.say(f"At the end, teamwork had beaten spite, and the starship hummed softly as the little crew smiled.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short Space Adventure story for a young child about a {p.action} quest, teamwork, and a need to pee.',
        f"Tell a story where {p.hero_name} feels spiteful, then learns to cooperate with {p.sidekick_name} on a space mission.",
        f'Write a gentle story set at {LOCATIONS[p.location]} that uses the words "pee" and "spite" and ends with teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    return [
        QAItem(
            question=f"Who was on the space quest at {LOCATIONS[p.location]}?",
            answer=f"{p.hero_name} was on the quest with {p.sidekick_name}, and they worked like a tiny team in space.",
        ),
        QAItem(
            question=f"What did {p.hero_name} need during the mission?",
            answer=f"{p.hero_name} needed to pee, so the team had to pause and find the bathroom first.",
        ),
        QAItem(
            question=f"What changed when the spite went away?",
            answer=f"Once the spite went away, {hero.label} relaxed, listened to {sidekick.label}, and the two friends finished the quest together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the job so the group can do something together.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special trip or mission to find something, fix something, or reach a goal.",
        ),
        QAItem(
            question="Why should someone go to the bathroom when they need to pee?",
            answer="Going to the bathroom helps the body feel better and keeps a person comfortable and clean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(Action, Location) :- action(Action), location(Location).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for act in SPACE_ACTIONS:
        lines.append(asp.fact("action", act))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    seen = set(asp.atoms(model, "valid"))
    expected = {(a, l) for a in SPACE_ACTIONS for l in LOCATIONS}
    if seen == expected:
        print(f"OK: ASP parity matches ({len(seen)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in ASP:", sorted(seen - expected))
    print(" only in Python:", sorted(expected - seen))
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(asp.atoms(model, "valid")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(location="ship", action="quest", hero_name="Nova", sidekick_name="Pip"),
            StoryParams(location="dock", action="repair", hero_name="Luna", sidekick_name="Rae"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(max(1, args.n)):
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
