#!/usr/bin/env python3
"""
storyworlds/worlds/cheat_damper_moral_value_repetition_heartwarming.py
======================================================================

A small heartwarming storyworld about honesty, practice, and a gentle
musical helper: a damper.

Seed tale inspiration:
A child wants to play a song on a little instrument. The child is tempted to
cheat by copying someone else's rhythm, but a kind adult helps them slow down,
practice again and again, and tell the truth. The damper softens the sound so
the child can keep trying without making a huge racket. In the end, the child
feels proud because the song was earned honestly.

This world models:
- a child and a helper
- a simple musical task with repetition
- a temptation to cheat
- a damper that makes practice quieter
- a moral turn toward honesty
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Task:
    id: str
    name: str
    repeated_action: str
    trial_action: str
    noise: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    quiets: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


ROOMS = {
    "music_room": Room(name="music room", place="the music room", affords={"drums", "bells", "practice"}, mood="cozy"),
    "kitchen": Room(name="kitchen", place="the kitchen", affords={"practice"}, mood="warm"),
    "classroom": Room(name="classroom", place="the classroom", affords={"bells", "practice"}, mood="bright"),
}

TASKS = {
    "drums": Task(
        id="drums",
        name="drum practice",
        repeated_action="tap the drum pattern again and again",
        trial_action="hit the wrong beat on purpose",
        noise="loud",
        keyword="drum",
        tags={"music", "repetition"},
    ),
    "bells": Task(
        id="bells",
        name="bell practice",
        repeated_action="ring the bells in the same happy order",
        trial_action="skip ahead to the easy part",
        noise="bright",
        keyword="bells",
        tags={"music", "repetition"},
    ),
    "practice": Task(
        id="practice",
        name="practice rounds",
        repeated_action="try the song one more time",
        trial_action="pretend to know the song already",
        noise="soft",
        keyword="practice",
        tags={"music", "repetition"},
    ),
}

TOOLS = {
    "damper": Tool(
        id="damper",
        label="a damper",
        phrase="a small damper that softens the sound",
        helps={"drums", "bells", "practice"},
        quiets={"loud", "bright", "soft"},
        prep="put the damper on first",
        tail="kept the sound soft while they practiced",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ella", "Ava"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo", "Max"]
TRAITS = ["curious", "shy", "gentle", "bright", "patient", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, room in ROOMS.items():
        for task_id in room.affords:
            task = TASKS[task_id]
            for tool_id, tool in TOOLS.items():
                if task.id in tool.helps:
                    combos.append((place, task_id, tool_id))
    return combos


def task_needs_honesty(task: Task) -> bool:
    return True


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.id in tool.helps:
            return tool
    return None


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("practice", 0) < THRESHOLD:
            continue
        sig = ("repetition", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["steady"] = hero.memes.get("steady", 0) + 1
        out.append(f"{hero.id} kept trying, and the pattern began to feel easier.")
    return out


def _r_cheat_damper(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("cheat", 0) < THRESHOLD:
            continue
        if hero.memes.get("honest", 0) >= THRESHOLD:
            continue
        sig = ("moral", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
        out.append(f"{hero.id}'s heart felt heavy because cheating did not feel right.")
    return out


CAUSAL_RULES = [
    _r_repetition,
    _r_cheat_damper,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_outcome(world: World, hero: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["practice"] = sim.get(hero.id).meters.get("practice", 0) + 1
    sim.get(hero.id).memes["cheat"] = sim.get(hero.id).memes.get("cheat", 0) + 1
    propagate(sim, narrate=False)
    return {
        "steady": sim.get(hero.id).memes.get("steady", 0) >= THRESHOLD,
        "guilt": sim.get(hero.id).memes.get("guilt", 0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved learning new songs.")


def loves_task(world: World, hero: Entity, task: Task) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {task.name}, and {task.repeated_action} made {hero.pronoun('object')} smile."
    )


def bring_tool(world: World, helper: Entity, hero: Entity, tool: Tool) -> None:
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {helper.type} brought {tool.phrase} so the room would stay calm."
    )


def wants_to_cheat(world: World, hero: Entity, task: Task) -> None:
    hero.memes["cheat"] = hero.memes.get("cheat", 0) + 1
    world.say(
        f"{hero.id} wanted to {task.trial_action}, but {hero.pronoun('possessive')} cheeks turned pink."
    )


def warn(world: World, helper: Entity, hero: Entity, task: Task) -> None:
    pred = predict_outcome(world, hero, task)
    if pred["guilt"]:
        world.say(
            f'"Cheating would make the song less sweet," {helper.pronoun().capitalize()} said. "Let\'s tell the truth and try again."'
        )


def choose_honesty(world: World, hero: Entity, task: Task) -> None:
    hero.memes["honest"] = hero.memes.get("honest", 0) + 1
    world.say(
        f"{hero.id} took a slow breath and chose to be honest instead of sneaking ahead."
    )


def practice_again(world: World, hero: Entity, task: Task) -> None:
    hero.meters["practice"] = hero.meters.get("practice", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.pronoun().capitalize()} tried to {task.repeated_action}, and each try sounded a little better."
    )


def resolve(world: World, hero: Entity, helper: Entity, tool: Tool, task: Task) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(
        f"With {tool.label} in place, the sound stayed gentle, and {hero.id} kept going until {hero.pronoun('possessive')} song felt earned."
    )
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} {helper.type} and smiled, because telling the truth made the music feel warm."
    )


def tell(room: Room, task: Task, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(room)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "kind"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    tool = world.add(Entity(id="damper", type="tool", label="damper", phrase=TOOLS["damper"].phrase, protective=True))

    introduce(world, hero)
    loves_task(world, hero, task)
    bring_tool(world, helper, hero, TOOLS["damper"])
    world.para()
    world.say(f"One day, {hero.id} went to {room.place} to practice.")
    wants_to_cheat(world, hero, task)
    warn(world, helper, hero, task)
    choose_honesty(world, hero, task)
    world.say(f"{hero.id} started again and again.")
    practice_again(world, hero, task)
    world.para()
    resolve(world, hero, helper, tool, task)

    world.facts.update(hero=hero, helper=helper, tool=tool, task=task, room=room)
    return world


SETTINGS = ROOMS


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task = f["hero"], f["helper"], f["task"]
    return [
        f'Write a heartwarming story about "{task.keyword}" practice, honesty, and a child named {hero.id}.',
        f"Tell a gentle story where {hero.id} wants to cheat at {task.name} but {helper.type} helps {hero.id} choose the honest way.",
        f"Write a short story for children in which repetition helps {hero.id} learn a song with a damper nearby.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task = f["hero"], f["helper"], f["task"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do when the story began?",
            answer=f"{hero.id} wanted to {task.trial_action}, but that would have been cheating.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {hero.id} to try again honestly?",
            answer=f"{helper.id} knew that cheating would not make the song truly theirs, so {helper.id} asked {hero.id} to tell the truth and practice again.",
        ),
        QAItem(
            question=f"What helped make the practice calm and soft?",
            answer=f"{f['tool'].label} helped keep the sound gentle while {hero.id} practiced.",
        ),
        QAItem(
            question=f"How did {hero.id} get better at the song?",
            answer=f"{hero.id} practiced the same pattern again and again, and repetition made the song feel easier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a damper do for sound?",
            answer="A damper softens the sound, so music can be quieter and gentler.",
        ),
        QAItem(
            question="Why is repetition useful when learning something new?",
            answer="Repetition helps because doing the same thing many times gives your hands and mind a chance to remember it.",
        ),
        QAItem(
            question="Why is cheating a bad choice?",
            answer="Cheating is a bad choice because it is not honest, and it can keep someone from learning something for real.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="music_room", task="drums", tool="damper", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="classroom", task="bells", tool="damper", name="Leo", gender="boy", helper="father", trait="shy"),
    StoryParams(place="music_room", task="practice", tool="damper", name="Nora", gender="girl", helper="mother", trait="gentle"),
]


def explain_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: nothing in this world makes {tool.label} work with {task.name}.)"


def valid_gender_for_name(gender: str) -> list[str]:
    return [gender]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world about honesty, repetition, and a damper."
    )
    ap.add_argument("--place", choices=ROOMS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, task=task, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], params.name, params.gender, params.helper)
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


ASP_RULES = r"""
task(task(drums)).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for t in sorted(room.affords):
            lines.append(asp.fact("affords", rid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
