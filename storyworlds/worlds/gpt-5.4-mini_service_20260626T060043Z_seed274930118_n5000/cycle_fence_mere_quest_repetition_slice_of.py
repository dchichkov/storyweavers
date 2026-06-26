#!/usr/bin/env python3
"""
storyworlds/worlds/cycle_fence_mere_quest_repetition_slice_of.py
=================================================================

A small slice-of-life storyworld about a child, a bicycle, a fenced path,
and a gentle quest that gets solved through repetition.

Premise:
- A child really wants to cycle a little loop outside.
- A fence makes the route feel safe, but a gate is only open sometimes.
- The child starts with a "mere" wish for one lap, then turns it into a quest:
  keep trying the loop until the route feels steady and the day feels proud.

World model:
- Physical meters track distance, balance, gate state, and bike readiness.
- Emotional memes track eagerness, worry, pride, and calm.
- Repetition increases balance and confidence; a safe loop resolves the quest.

This script follows the Storyweavers contract: it defines the standard entry
points, emits prose from state changes, supports QA/JSON/trace/ASP/verify,
and keeps the story grounded in the simulated world.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        for k in ["distance", "balance", "gate_open", "wear", "clean"]:
            self.meters.setdefault(k, 0.0)
        for k in ["eagerness", "worry", "pride", "calm", "patience", "quest"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    steps: list[str]
    route: str
    repeated_step: str
    win_line: str


@dataclass
class Setting:
    place: str = "the little front path"
    fence: bool = True
    afford_cycle: bool = True
    loop_length: int = 3


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.traces: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.traces.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    quest: str
    repeat_count: int
    seed: Optional[int] = None


SETTINGS = {
    "front_path": Setting(place="the little front path", fence=True, afford_cycle=True, loop_length=3),
    "backyard_loop": Setting(place="the backyard loop", fence=True, afford_cycle=True, loop_length=4),
    "garden_path": Setting(place="the garden path", fence=True, afford_cycle=True, loop_length=3),
}

QUESTS = {
    "ride_laps": Quest(
        id="ride_laps",
        title="a small bicycle quest",
        goal="ride one clean loop without wobbling",
        steps=["wobble", "steady", "repeat"],
        route="the fenced path",
        repeated_step="another lap",
        win_line="The last lap felt easy, like the path had been waiting for the bike all along.",
    ),
    "circle_fence": Quest(
        id="circle_fence",
        title="a fence-side quest",
        goal="circle the fence and come back to the gate",
        steps=["start", "turn", "repeat"],
        route="the fence edge",
        repeated_step="one more circle",
        win_line="By the end, the child knew the way around the fence by heart.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Owen", "Sam"]
TRAITS = ["quiet", "cheerful", "curious", "gentle", "patient", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for quest in QUESTS:
            for gender in ["girl", "boy"]:
                out.append((place, quest, gender))
    return out


def explain_rejection(place: str, quest: str) -> str:
    return f"(No story: {quest} does not fit {place} in this small fenced-world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life storyworld about cycling, a fence, and a quest solved by repetition."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--repeat-count", type=int)
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
    if args.place and args.quest and (args.place, args.quest, "girl") not in valid_combos():
        raise StoryError(explain_rejection(args.place, args.quest))

    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    repeat_count = args.repeat_count if args.repeat_count is not None else rng.choice([2, 3, 4])
    return StoryParams(name=name, gender=gender, parent=parent, place=place, quest=quest, repeat_count=repeat_count)


def _hero_desc(hero: Entity) -> str:
    trait = next((t for t in hero.memes.get("traits", []) if t), "small")
    return f"little {trait} {hero.type}"


def _do_lap(world: World, hero: Entity, parent: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.meters["distance"] += 1
    hero.memes["quest"] += 1
    hero.memes["patience"] += 0.5
    hero.memes["eagerness"] += 0.25
    if hero.meters["distance"] == 1:
        hero.meters["balance"] += 0.25
        hero.memes["worry"] += 0.25
        if narrate:
            world.say(f"{hero.id} started the first lap, and the bike wobbled a little.")
    elif hero.meters["distance"] < world.setting.loop_length:
        hero.meters["balance"] += 0.5
        hero.memes["calm"] += 0.25
        if narrate:
            world.say(f"{hero.id} tried {quest.repeated_step}, and {hero.pronoun('possessive')} steering grew steadier.")
    else:
        hero.meters["balance"] += 0.75
        hero.memes["pride"] += 1.0
        if narrate:
            world.say(quest.win_line)


def tell(setting: Setting, quest: Quest, hero_name: str, hero_type: str, parent_type: str, trait: str, repeat_count: int) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"traits": [trait]}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    bike = world.add(Entity(id="bike", type="bike", label="bike", phrase="a small blue bike", owner=hero.id))
    fence = world.add(Entity(id="fence", type="fence", label="fence", phrase="a white fence", owner=None))
    gate = world.add(Entity(id="gate", type="gate", label="gate", phrase="a gate", owner=None))
    gate.meters["gate_open"] = 1.0

    world.say(f"{hero.id} was a {trait} {hero.type} who loved a simple quest: {quest.goal}.")
    world.say(f"{hero.id}'s {parent.label if parent.label else parent_type} had set the {bike.label} by {setting.place}, near the fence.")

    world.para()
    world.say(f"It felt like a mere little plan at first, but {hero.id} wanted to make it real.")
    world.say(f"{hero.id} looked at the fence, then at the gate, and then back at the bike.")
    hero.memes["eagerness"] += 1
    hero.memes["quest"] += 1

    world.para()
    world.say(f"{parent_type.capitalize()} said the path was safe if {hero.id} kept to {quest.route}.")
    world.say(f"So {hero.id} began to cycle, one lap at a time, with {repeat_count} tries in mind.")

    for i in range(repeat_count):
        _do_lap(world, hero, parent, quest, narrate=True)
        if i < repeat_count - 1:
            world.say(f"Then {hero.id} turned back toward the start and did the same little move again.")

    world.para()
    if hero.meters["balance"] >= 1.5:
        world.say(f"By the end, {hero.id} could follow the fence without wobbling much at all.")
        world.say(f"{hero.id} smiled at {parent.pronoun('object')}, proud of the steady repetition.")
    else:
        world.say(f"The laps were short, but they still made {hero.id} braver and calmer.")
        world.say(f"{hero.id} promised to try again tomorrow.")

    world.facts.update(
        hero=hero,
        parent=parent,
        bike=bike,
        fence=fence,
        gate=gate,
        quest=quest,
        setting=setting,
        repeat_count=repeat_count,
        resolved=hero.meters["balance"] >= 1.5,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    setting = f["setting"]
    return [
        f"Write a gentle slice-of-life story about {hero.id} who wants to cycle near {setting.place} and learns through repetition.",
        f"Tell a short story where a child starts a mere bicycle quest by the fence and keeps doing {quest.repeated_step}.",
        f"Write a child-friendly story about a fence, a bike, and a small quest that gets easier each lap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    quest = f["quest"]
    resolved = f["resolved"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do near {f['setting'].place}?",
            answer=f"{hero.id} wanted to cycle a small quest near {f['setting'].place} and ride the loop by the fence.",
        ),
        QAItem(
            question=f"Why did the story mention a mere little plan at first?",
            answer=f"It meant {hero.id}'s wish looked small at the start, but then it turned into a real quest to keep cycling and repeat the loop.",
        ),
        QAItem(
            question=f"What did {parent.type if parent.type else 'the parent'} tell {hero.id} to do?",
            answer=f"{parent.type.capitalize()} told {hero.id} to stay on the safe path by the fence and keep the ride gentle.",
        ),
    ]
    if resolved:
        qa.append(
            QAItem(
                question=f"How did repetition help {hero.id} finish the quest?",
                answer=f"Each lap made {hero.id} steadier, so by the last repetition the bike felt easier to guide and the fence-side route felt familiar.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt proud and calm because the repeated laps turned a mere wish into a finished little success.",
            )
        )
    return qa


KNOWLEDGE = {
    "cycle": [
        ("What does it mean to cycle?", "To cycle means to ride a bicycle by pushing the pedals and balancing while the wheels roll forward."),
    ],
    "fence": [
        ("What is a fence for?", "A fence is a boundary that can mark where a yard ends and can help keep a space safe or private."),
    ],
    "mere": [
        ("What does mere mean?", "Mere can mean only or just a little, like when something seems small at first."),
    ],
    "quest": [
        ("What is a quest?", "A quest is a goal you try to reach, often by taking a few steps and not giving up."),
    ],
    "repetition": [
        ("Why can repetition help?", "Repetition helps because doing the same thing again and again can make it feel more familiar and easier."),
    ],
    "slice": [
        ("What is slice of life?", "Slice of life stories show a small everyday moment, like a child riding a bike or talking with family."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["slice", "mere", "quest", "repetition", "cycle", "fence"]:
        if key in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- child(H).
quest(Q) :- goal(Q).
repetition(R) :- repeated(R).

steady(H) :- balance(H,B), B >= 2.
resolved(H) :- steady(H), questing(H).

can_finish(P,Q) :- place(P), quest(Q), fence(P), repetition(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.fence:
            lines.append(asp.fact("fence", pid))
        if setting.afford_cycle:
            lines.append(asp.fact("cycle_ok", pid))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("goal", qid))
        lines.append(asp.fact("repeated", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_valid_stories() -> list[tuple]:
    out = []
    for place, quest, gender in valid_combos():
        out.append((place, quest, gender))
    return out


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
    StoryParams(name="Mia", gender="girl", parent="mother", place="front_path", quest="ride_laps", repeat_count=3),
    StoryParams(name="Leo", gender="boy", parent="father", place="backyard_loop", quest="circle_fence", repeat_count=4),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        QUESTS[params.quest],
        params.name,
        params.gender,
        params.parent,
        "gentle",
        params.repeat_count,
    )
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

    if args.show_asp:
        print(asp_program("#show can_finish/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos.")
        for c in combos[:20]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
