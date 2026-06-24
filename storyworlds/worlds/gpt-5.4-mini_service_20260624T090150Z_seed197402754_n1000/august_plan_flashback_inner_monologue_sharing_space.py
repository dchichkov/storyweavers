#!/usr/bin/env python3
"""
A tiny space-adventure storyworld about an astronaut, a plan, a flashback,
inner monologue, and sharing space during a long August mission.
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

ASP_RULES = r"""
% A mission is reasonable when the station has the needed space and the helper
% action is compatible with the shared item or task.
compatible(Mission, Item) :- needs_space(Mission, Space), has_space(Item, Space),
                             safe_share(Item), planned(Mission).
valid_story(Mission, Item) :- compatible(Mission, Item), flashback_help(Mission),
                              inner_monologue(Mission), sharing(Mission).
"""

SPACE_KINDS = {"cabin", "corridor", "cargo_bay", "docking_port"}
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot", "engineer", "astronaut"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str = "the station"
    place: str = "August Station"
    space: str = "cabin"
    stars: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    title: str
    task: str
    inner_line: str
    flashback_line: str
    sharing_line: str
    risk: str
    fix: str
    keyword: str = "plan"


@dataclass
class Item:
    label: str
    phrase: str
    space: str
    shared: bool = True
    fragile: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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


def make_world() -> World:
    return World(SETTING)


def propagate(world: World) -> None:
    crew = world.get("Ari")
    item = world.get("map")
    if crew.memes.get("worry", 0) >= THRESHOLD and item.meters.get("scuffed", 0) < THRESHOLD:
        sig = ("care", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.say("Ari carefully folded the map so it would not get scuffed in the cabin.")
    if crew.memes.get("shared", 0) >= THRESHOLD:
        sig = ("share", crew.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.say("The small cabin felt easier to share once the plan was spoken out loud.")


def flashback(world: World, mission: Mission) -> None:
    crew = world.get("Ari")
    crew.memes["memory"] = crew.memes.get("memory", 0) + 1
    world.say(
        f"August made Ari think back to the last long trip, when a stormy dock taught "
        f"{crew.pronoun('object')} that a good plan could keep everyone calm."
    )
    world.say(mission.flashback_line)


def inner_monologue(world: World, mission: Mission) -> None:
    crew = world.get("Ari")
    crew.memes["worry"] = crew.memes.get("worry", 0) + 1
    world.say(
        f"Ari looked at the narrow cabin and thought, '{mission.inner_line}'"
    )
    world.say(
        f"Then {crew.pronoun('subject')} remembered that a brave plan is one you can explain."
    )


def sharing(world: World, mission: Mission) -> None:
    crew = world.get("Ari")
    ally = world.get("Bo")
    crew.memes["shared"] = crew.memes.get("shared", 0) + 1
    ally.memes["shared"] = ally.memes.get("shared", 0) + 1
    world.say(
        f"Ari shared the task with Bo, and together they made room for both helmets, "
        f"both boots, and the same careful plan."
    )
    world.say(mission.sharing_line)
    world.say(
        f"By the end, the August station was quiet, the map was safe, and the plan "
        f"felt bigger than the little cabin."
    )


SETTING = Setting(
    name="the station",
    place="August Station",
    space="cabin",
    stars=True,
    affords={"repair", "share", "plan"},
)

MISSION = Mission(
    id="dock_repair",
    title="dock repair",
    task="repair the docking light",
    inner_line="If the light fails, the whole station will feel lost, but if I share the job, it will fit",
    flashback_line="She remembered how the old captain once said, 'A plan works best when it leaves room for a friend.'",
    sharing_line="Bo nodded and slid the toolkit over, because sharing made the tiny cabin feel wide enough for both of them.",
    risk="the map might get scuffed in the tight cabin",
    fix="share the toolkit and move slowly",
)

ITEMS = {
    "map": Item(label="map", phrase="a star map", space="cabin", shared=True, fragile=True),
    "toolkit": Item(label="toolkit", phrase="a small toolkit", space="cabin", shared=True, fragile=False),
}

CREW_NAMES = ["Ari", "Bo", "Mina", "Jett", "Rin"]
TITLES = ["astronaut", "pilot", "engineer", "captain"]


@dataclass
class StoryParams:
    name: str = "Ari"
    ally: str = "Bo"
    title: str = "astronaut"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld about August, a plan, and sharing space.")
    ap.add_argument("--name")
    ap.add_argument("--ally")
    ap.add_argument("--title", choices=TITLES)
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "august_station"),
        asp.fact("space", SETTING.space),
        asp.fact("planned", "dock_repair"),
        asp.fact("flashback_help", "dock_repair"),
        asp.fact("inner_monologue", "dock_repair"),
        asp.fact("sharing", "dock_repair"),
        asp.fact("needs_space", "dock_repair", SETTING.space),
        asp.fact("has_space", "map", SETTING.space),
        asp.fact("safe_share", "map"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("dock_repair", "map")}
    if clingo_set == python_set:
        print("OK: clingo gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(CREW_NAMES),
        ally=args.ally or rng.choice([n for n in CREW_NAMES if n != (args.name or "Ari")]),
        title=args.title or rng.choice(TITLES),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.ally:
        raise StoryError("The astronaut and the helper must be different people.")
    if SETTING.space != "cabin":
        raise StoryError("This storyworld expects a small shared cabin.")
    if "plan" not in SETTING.affords:
        raise StoryError("The station must afford planning for this story.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = make_world()
    hero = world.add(Entity(id="Ari", kind="character", type=params.title, label=params.name))
    ally = world.add(Entity(id="Bo", kind="character", type="astronaut", label=params.ally))
    map_item = world.add(Entity(id="map", type="map", label="map"))
    toolkit = world.add(Entity(id="toolkit", type="toolkit", label="toolkit"))

    world.say(
        f"In August Station, {hero.label} was a little {params.title} with a careful plan."
    )
    world.say(
        f"{hero.label} wanted to {MISSION.task}, and the star map was waiting on the table."
    )

    world.para()
    flashback(world, MISSION)
    inner_monologue(world, MISSION)
    propagate(world)

    world.para()
    world.say(
        f"{hero.label} did not want the cabin to feel crowded, because the map needed a safe place."
    )
    sharing(world, MISSION)
    world.facts.update(hero=hero, ally=ally, mission=MISSION, map_item=map_item, toolkit=toolkit)

    story_qa = [
        QAItem(
            question=f"Who was the story about in August Station?",
            answer=f"It was about {hero.label}, a little {params.title} named {params.name}, and {ally.label}, who helped share the work.",
        ),
        QAItem(
            question=f"What was {hero.label}'s plan?",
            answer=f"{hero.label}'s plan was to {MISSION.task}, and to do it safely in the small cabin.",
        ),
        QAItem(
            question="Why did Ari think about an old trip?",
            answer="Ari had a flashback because August made the memory come back, and the old lesson helped with the new plan.",
        ),
        QAItem(
            question="How did they make the space easier to share?",
            answer="They shared the toolkit, moved carefully, and made room for both of them in the cabin.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows an older memory that helps explain what a character feels now.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thinking, like words said inside their own head.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use something or take part in the same space or task.",
        ),
    ]

    prompts = [
        "Write a short Space Adventure story set in August Station about a careful plan, a flashback, and sharing space in a small cabin.",
        f"Tell a child-friendly story where {hero.label} thinks in an inner monologue, remembers an older mission, and shares a job with {ally.label}.",
        "Write a simple space story that includes the words august and plan, and ends with a calm shared workspace.",
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [StoryParams(name="Ari", ally="Bo", title="astronaut")]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
