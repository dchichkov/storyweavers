#!/usr/bin/env python3
"""
storyworlds/worlds/plant_anorexic_teamwork_quest_lesson_learned_fable.py
=========================================================================

A small fable-style storyworld about a fragile plant, a teamwork quest, and
the lesson learned when friends share care, water, and sunlight.

Seed tale:
---
A tiny plant in a stony yard was so thin and pale that the rabbits called it
anorexic, though the word only meant it was terribly undergrown. The plant
wanted to reach the bright sun but could not climb the wall on its own. A bee,
an ant, and a sparrow joined together to help. The bee brought pollen, the ant
loosened the soil, and the sparrow scattered water from a leaf. With teamwork,
the plant grew strong enough to bloom. The lesson was simple: even the smallest
living thing can grow when helpers work together.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"size": 0.0, "health": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "need": 0.0, "joy": 0.0, "bond": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sun: str
    soil: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    goal: str
    obstacle: str
    method: str
    reward: str
    keyword: str = "quest"


@dataclass
class Helper:
    id: str
    label: str
    role: str
    gift: str
    verb: str


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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_starved(world: World) -> list[str]:
    out = []
    plant = world.entities.get("plant")
    if not plant:
        return out
    if plant.meters["health"] >= THRESHOLD:
        return out
    sig = ("starved")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.memes["need"] += 1
    out.append("The little plant looked so thin and tired that even the wind felt sorry for it.")
    return out


def _r_bloom(world: World) -> list[str]:
    out = []
    plant = world.entities.get("plant")
    if not plant:
        return out
    if plant.meters["size"] < 2 or plant.meters["health"] < 2:
        return out
    sig = ("bloom")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["bloom"] = 1.0
    plant.memes["joy"] += 1
    out.append("At last, a bright bloom opened on the plant like a tiny sun.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    plant = world.entities.get("plant")
    if not plant:
        return out
    helpers = [e for e in world.entities.values() if e.kind == "helper"]
    if len(helpers) < 2:
        return out
    sig = ("teamwork")
    if sig in world.fired:
        return out
    if sum(h.memes.get("bond", 0) for h in helpers) < 2:
        return out
    if plant.memes["hope"] < THRESHOLD:
        return out
    world.fired.add(sig)
    plant.meters["health"] += 1
    plant.meters["size"] += 1
    out.append("Together, the helpers made the poor plant stronger than before.")
    return out


CAUSAL_RULES = [_r_starved, _r_teamwork, _r_bloom]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def introduce(world: World) -> None:
    world.say("In a stony yard stood a tiny plant that was so small and pale that the rabbits called it anorexic.")
    world.say("The plant was not proud of the word, but it knew it was weak and wanted very badly to grow.")


def desire_quest(world: World, quest: Quest) -> None:
    plant = world.get("plant")
    plant.memes["hope"] += 1
    plant.memes["need"] += 1
    world.say(
        f"It wanted to {quest.goal}, but {quest.obstacle}."
    )
    world.say(
        f"So the plant waited for a {quest.keyword} that could lead it toward {quest.reward}."
    )


def meet_helpers(world: World, helpers: list[Helper]) -> None:
    for h in helpers:
        ent = world.add(Entity(id=h.id, kind="helper", type=h.id, label=h.label, phrase=h.label, meters={"size": 0.0}, memes={"bond": 0.0, "joy": 0.0}))
        ent.memes["bond"] += 1
        world.say(f"A {h.label} came by and offered to {h.verb}.")


def teamwork_scene(world: World, quest: Quest, helpers: list[Helper]) -> None:
    plant = world.get("plant")
    world.para()
    world.say(f"The {world.setting.place} was dry, and the plant could not reach the {world.setting.sun} on its own.")
    world.say(f"Then the friends chose to work as a team: each one would do a small part of the {quest.keyword}.")
    for h in helpers:
        if h.id == "bee":
            world.say("The bee brought pollen and circled kindly above the leaves.")
            plant.meters["health"] += 1
        elif h.id == "ant":
            world.say("The ant loosened the soil around the roots so water could sink in.")
            plant.meters["size"] += 1
        elif h.id == "sparrow":
            world.say("The sparrow shook a cool drop of water from a leaf right onto the roots.")
            plant.meters["health"] += 1
        plant.memes["bond"] += 1
    plant.memes["hope"] += 1
    propagate(world)


def lesson_learned(world: World) -> None:
    plant = world.get("plant")
    world.para()
    world.say("By the end, the little plant stood taller, green and calm, with a bloom opening near the top.")
    world.say("The plant learned that even a small life can become strong when helpers work together.")


SETTINGS = {
    "yard": Setting(place="stony yard", sun="sun", soil="dry soil", affords={"quest"}),
    "garden": Setting(place="quiet garden", sun="sun", soil="soft soil", affords={"quest"}),
    "hill": Setting(place="windy hill", sun="sun", soil="thin soil", affords={"quest"}),
}

QUESTS = {
    "reach_sun": Quest(
        goal="reach the sun",
        obstacle="the wall was too high and the roots were stuck in hard ground",
        method="teamwork",
        reward="a bright bloom",
        keyword="quest",
    ),
}

HELPERS = [
    Helper(id="bee", label="bee", role="pollinator", gift="pollen", verb="bring pollen"),
    Helper(id="ant", label="ant", role="digger", gift="strength", verb="loosen the soil"),
    Helper(id="sparrow", label="sparrow", role="carrier", gift="water", verb="scatter water"),
]


@dataclass
class StoryParams:
    place: str
    quest: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about a plant, teamwork, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
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
    quest = args.quest or "reach_sun"
    return StoryParams(place=place, quest=quest)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    plant = world.add(Entity(id="plant", kind="character", type="plant", label="plant"))
    plant.meters["health"] = 0.0
    plant.meters["size"] = 0.0
    introduce(world)
    desire_quest(world, QUESTS[params.quest])
    world.para()
    meet_helpers(world, HELPERS)
    teamwork_scene(world, QUESTS[params.quest], HELPERS)
    lesson_learned(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short fable about a plant that is too weak to grow alone, but learns teamwork on a quest.",
        f"Tell a child-friendly lesson-learned story set in the {world.setting.place} about helpers and a small plant.",
        "Write a simple fable with a clear moral about sharing effort so a tiny plant can bloom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did the plant need help?",
            answer="The plant was too weak and small to reach the sun or grow well on its own, so it needed friends to help.",
        ),
        QAItem(
            question="Who helped the plant?",
            answer="A bee, an ant, and a sparrow worked together to help the plant.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson was that teamwork can help even the smallest living thing grow strong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a plant need to grow?",
            answer="Most plants need water, sunlight, air, and soil so their roots can stay healthy.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when several helpers work together to do something that is hard to do alone.",
        ),
        QAItem(
            question="What is a lesson learned in a fable?",
            answer="A lesson learned is the helpful idea the story wants you to remember after the characters are done.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
plant_strong(P) :- plant(P), health(P,H), H >= 2.
teamwork_help(P) :- helper(H1), helper(H2), helper(H3), plant(P).
lesson_learned(P) :- teamwork_help(P), plant_strong(P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("plant", "plant")]
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/1."))
    atoms = set(asp.atoms(model, "lesson_learned"))
    ok = ("plant",) in atoms
    if ok:
        print("OK: ASP gate says the lesson is learned.")
        return 0
    print("MISMATCH: ASP gate did not derive lesson_learned(plant).")
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
        print(asp_program("#show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            samples.append(generate(StoryParams(place=place, quest="reach_sun", seed=base_seed)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20 + 20:
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
