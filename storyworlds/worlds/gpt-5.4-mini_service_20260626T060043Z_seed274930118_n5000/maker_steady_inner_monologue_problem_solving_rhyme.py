#!/usr/bin/env python3
"""
Standalone storyworld: maker, steady, inner monologue, problem solving, rhyme.

A small space-adventure world where a steady maker must repair a ship using
tools, calm thinking, and a rhyming plan.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["charge", "leak", "repair", "fear", "calm", "pride", "hope", "worry", "delay"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain", "maker"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    problem: str
    rhyme: str
    fix: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    purpose: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.task_zone: set[str] = set()
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.task_zone = set(self.task_zone)
        return w


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["repair"] < THRESHOLD:
            continue
        for ship in world.entities.values():
            if ship.type != "ship":
                continue
            if ship.meters["leak"] < THRESHOLD:
                continue
            sig = ("repair", ship.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ship.meters["leak"] = max(0.0, ship.meters["leak"] - 1.0)
            ship.meters["repair"] += 1.0
            out.append(f"The fix held and {ship.label} stopped leaking.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["calm"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = max(0.0, actor.memes["fear"] - 1.0)
        actor.memes["hope"] += 1.0
        out.append(f"{actor.id} breathed slowly and felt braver.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_repair, _r_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    do_task(sim, sim.get(actor.id), task, narrate=False)
    ship = next(e for e in sim.entities.values() if e.type == "ship")
    return {"leak": ship.meters["leak"], "repair": ship.meters["repair"]}


def do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot support {task.id}.)")
    world.task_zone = set(task.zone)
    actor.memes["worry"] += 1.0
    actor.memes["calm"] += 1.0
    actor.meters["repair"] += 1.0
    ship = next(e for e in world.entities.values() if e.type == "ship")
    if ship.meters["leak"] >= THRESHOLD:
        ship.meters["leak"] -= 1.0
    propagate(world, narrate=narrate)


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.guards:
            return tool
    return None


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    hero_type: str
    assistant: str
    seed: Optional[int] = None


SETTINGS = {
    "orbital_bay": Setting("the orbital bay", {"seal", "tune"}),
    "star_port": Setting("the star port", {"seal"}),
    "moon_dock": Setting("the moon dock", {"seal", "patch"}),
}

TASKS = {
    "seal": Task(
        id="seal",
        verb="seal the crack",
        gerund="sealing the crack",
        problem="a bright leak in the hull",
        rhyme="If the hull lets light in, make the patch begin",
        fix="seal the leak",
        zone={"hull"},
        tags={"space", "repair", "rhyme"},
    ),
    "patch": Task(
        id="patch",
        verb="patch the panel",
        gerund="patching the panel",
        problem="a torn panel that hissed softly",
        rhyme="Patch it tight and patch it neat, so the ship can cruise and greet",
        fix="patch the panel",
        zone={"panel"},
        tags={"space", "repair"},
    ),
    "tune": Task(
        id="tune",
        verb="tune the engine",
        gerund="tuning the engine",
        problem="a wobbling engine that coughed and paused",
        rhyme="Turn the dial, keep a smile, let the engine sing awhile",
        fix="tune the engine",
        zone={"engine"},
        tags={"space", "maker"},
    ),
}

TOOLS = [
    Tool("sealant", "sealant tube", {"seal"}, {"hull", "panel"}, "press the sealant into the crack", "pressed the sealant into the crack"),
    Tool("patch_kit", "patch kit", {"patch"}, {"panel"}, "smooth the patch across the tear", "smoothed the patch across the tear"),
    Tool("wrench", "steady wrench", {"tune"}, {"engine"}, "turn the bolts with a steady hand", "turned the bolts with a steady hand"),
]

HEROES = ["Mira", "Nova", "Tess", "Aria", "Luna"]
ASSISTANTS = ["robot", "pilot", "friend", "copilot"]
TRAITS = ["steady", "curious", "brave", "gentle"]


def tell(setting: Setting, task: Task, hero_name: str, hero_type: str, assistant_type: str) -> World:
    world = World(setting)
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="Star Lantern", phrase="the Star Lantern"))
    ship.meters["leak"] = 1.0
    ship.meters["repair"] = 0.0

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["maker", "steady"]))
    assistant = world.add(Entity(id="assistant", kind="character", type=assistant_type))

    world.say(f"{hero.id} was a maker who stayed steady even when space went quiet.")
    world.say(f"{hero.id} loved {task.gerund}, and {hero.id}'s mind often hummed with a soft inner monologue: {task.rhyme.lower()}.")
    world.say(f"Nearby, the {assistant_type} waited with a tool tray and a hopeful blink.")

    world.para()
    world.say(f"One day at {setting.place}, {ship.label} showed {task.problem}.")
    world.say(f"{hero.id} wanted to {task.verb}, but first {hero.id} whispered, \"Think, plan, then win.\"")
    world.say(f"The steady maker looked at the problem, looked at the room, and kept breathing slow.")

    tool = select_tool(task)
    if not tool:
        raise StoryError("(No story: no tool in this world can solve that task.)")

    tool_ent = world.add(Entity(
        id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.label,
        protective=True, plural=tool.plural
    ))
    tool_ent.worn_by = hero.id
    world.say(f"{hero.id} picked up {tool.label} and remembered the rhyme: {task.rhyme.lower()}.")
    world.say(f"\"{task.rhyme},\" {hero.id} said. \"{tool.purpose.capitalize()}.\"")

    world.para()
    before = predict(world, hero, task)
    if before["leak"] >= THRESHOLD:
        world.say(f"The first try still left a drip, so {hero.id} tried again with a calmer grip.")
    do_task(world, hero, task)
    world.say(f"{hero.id} worked carefully while {assistant_type} held the light steady.")
    if ship.meters["leak"] < THRESHOLD:
        world.say(f"At last, {ship.label} stopped leaking, and the stars outside looked friendly again.")
    world.say(f"{hero.id} smiled, proud of the fix, and the ship felt safe for the next jump.")

    world.facts.update(hero=hero, assistant=assistant, ship=ship, task=task, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f'Write a small space adventure about a steady maker named {hero.id} who must {task.fix}.',
        f"Tell a child-friendly story where a maker uses inner monologue, problem solving, and rhyme to help a ship.",
        f'Write a calm, rhythmic story set in {f["setting"].place} with a bright leak and a clever fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ship = f["ship"]
    task = f["task"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"What kind of helper was {hero.id}?",
            answer=f"{hero.id} was a steady maker who liked to solve problems carefully.",
        ),
        QAItem(
            question=f"What problem did {ship.label} have at {f['setting'].place}?",
            answer=f"{ship.label} had {task.problem}, so {hero.id} needed to {task.fix}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help fix the ship?",
            answer=f"{hero.id} used {tool.label} and a calm, careful plan.",
        ),
        QAItem(
            question=f"How did the story show {hero.id}'s inner monologue?",
            answer=f"{hero.id} whispered a rhyme to themself before working, which showed steady thinking and self-talk.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maker?",
            answer="A maker is someone who builds, repairs, or creates useful things.",
        ),
        QAItem(
            question="What does it mean to stay steady?",
            answer="To stay steady means to keep calm and keep going without panicking.",
        ),
        QAItem(
            question="Why do people use rhymes sometimes?",
            answer="People use rhymes to help words sound catchy and easier to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
leak_fixed(S) :- ship(S), leak(S,1), tool(T), fits(T,seal), shown_repair(T,S).
calm_gain(H) :- maker(H), steady(H), inner_monologue(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for z in sorted(task.zone):
            lines.append(asp.fact("zone", tid, z))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld: a steady maker solves a ship problem.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["maker", "captain", "pilot"], default="maker")
    ap.add_argument("--assistant", choices=ASSISTANTS)
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
    task = args.task or rng.choice(sorted(SETTINGS[place].affords))
    if task not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {place} cannot host {task}.)")
    hero = args.hero or rng.choice(HEROES)
    assistant = args.assistant or rng.choice(ASSISTANTS)
    return StoryParams(place=place, task=task, hero=hero, hero_type=args.hero_type, assistant=assistant)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], params.hero, params.hero_type, params.assistant)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            combos.append((place, task))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show afford/2."))
    return sorted(set(asp.atoms(model, "afford")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show afford/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show afford/2."))
        model = asp.one_model(asp_program("#show afford/2."))
        for t in sorted(set(asp.atoms(model, "afford"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, task in valid_combos():
            p = StoryParams(place=place, task=task, hero="Mira", hero_type="maker", assistant="robot")
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
