#!/usr/bin/env python3
"""
Thin Chalk Sound Effects Teamwork Tall Tale
===========================================

A small storyworld about a thin stick of chalk, booming sound effects, and a
team that solves a big problem together in tall-tale style.

Premise:
- A child-led crew must use a thin piece of chalk to mark a safe path.
- The path is tricky because the bridge, wind, and mud keep changing the way.
- The team succeeds only when they work together and keep their rhythm.

The story is simulated from world state:
- chalk can wear down as it is used;
- footsteps, hammer taps, and shouted sound effects can raise tension;
- teamwork lowers fear and lets the crew finish the job;
- the ending image proves the route was marked and the town can cross safely.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    soundscape: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    strain: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    gives: set[str]
    thin: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _rule_chalk_wears(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.type != "chalk":
            continue
        if ent.meters.get("used", 0.0) < THRESHOLD:
            continue
        sig = ("wears", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["thin"] = ent.meters.get("thin", 0.0) + 1.0
        out.append("The chalk grew thinner and thinner from all the marking.")
    return out


def _rule_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    if hero.memes.get("fear", 0.0) >= THRESHOLD and helper.memes.get("encourage", 0.0) >= THRESHOLD:
        sig = ("teamwork", hero.id, helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
            hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
            out.append("Working together made the crew feel bigger than the bridge.")
    return out


def _rule_finish(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("route_marked") and world.facts.get("crossed"):
        sig = ("finish",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The path held, and the town could cross without a single wobble.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_rule_chalk_wears, _rule_teamwork, _rule_finish):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        traits=["little", params.trait],
        memes={"pride": 1.0, "fear": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="character", type=params.helper_type,
        traits=["steady"],
        memes={"encourage": 1.0, "joy": 0.0},
    ))
    chalk = world.add(Entity(
        id="chalk", type="chalk", label="chalk", phrase="a thin stick of chalk",
        owner=hero.id, caretaker=hero.id,
        meters={"used": 0.0, "thin": 0.0},
        memes={"hope": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, chalk=chalk, task=TASKS[params.task], tool=TOOLS[params.tool])

    return world


def intro(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    task = world.facts["task"]
    chalk = world.facts["chalk"]
    world.say(
        f"{hero.id} was a little {hero.type} with a brave heart and a love for big jobs. "
        f"{helper.id} was the steady helper who never missed a beat."
    )
    world.say(
        f"One morning, they found a thin stick of chalk waiting by the door, "
        f"small as a match and bright as a moonbeam."
    )
    world.say(
        f"They needed it for {task.verb}, and the whole town was humming about the job."
    )


def tension(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    task = world.facts["task"]
    chalk = world.facts["chalk"]
    world.para()
    world.say(
        f"When they reached {world.setting.place}, the air went {world.setting.soundscape}. "
        f"The bridge gave a grumpy creak: {task.sound}."
    )
    world.say(
        f"{hero.id} wanted to {task.verb} right away, but the way ahead was slick, "
        f"and the route had to be marked just so."
    )
    hero.memes["fear"] = 1.0
    helper.memes["encourage"] = 1.0
    world.say(
        f"{helper.id} said, \"Easy now. One mark at a time.\" Then the wind went whoosh-whoosh "
        f"and tried to blow the chalk from {hero.pronoun('possessive')} hand."
    )
    chalk.meters["used"] += 1.0
    propagate(world)


def turn_and_resolution(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    task = world.facts["task"]
    chalk = world.facts["chalk"]

    world.para()
    world.say(
        f"{hero.id} planted one foot, {helper.id} planted the other, and together they began: "
        f"tap-tap, scrape-scrape, steady as a drum."
    )
    world.say(
        f"{hero.id} drew the line while {helper.id} held the lantern, and every careful inch said "
        f"\"here, here, here\" in white chalk."
    )
    chalk.meters["used"] += 1.0
    world.facts["route_marked"] = True
    propagate(world)

    world.say(
        f"Then came the biggest step of all. {hero.id} lifted a hand, {helper.id} lifted the rope, "
        f"and together they crossed the bridge without a slip."
    )
    world.facts["crossed"] = True
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    propagate(world)

    world.say(
        f"By sunset, the chalk line shone pale and proud on the boards, and the town marched over "
        f"it like a parade of caterpillars with happy feet."
    )
    world.say(
        f"{hero.id} grinned so wide it looked like the moon had borrowed {hero.pronoun('possessive')} face, "
        f"and {helper.id} laughed a deep old laugh that rolled all the way down the hill."
    )


def tell(params: StoryParams) -> World:
    world = setup_story_world(params)
    intro(world)
    tension(world)
    turn_and_resolution(world)
    return world


SETTINGS = {
    "bridge": Setting(place="the crooked bridge", soundscape="full of whistle and wind", affords={"mark_path"}),
    "barn": Setting(place="the red barn loft", soundscape="warm with creaks and clucks", affords={"mark_path"}),
    "yard": Setting(place="the dusty yard", soundscape="wide and echoing", affords={"mark_path"}),
}

TASKS = {
    "mark_path": Task(
        id="mark_path",
        verb="mark the safe path",
        gerund="marking the safe path",
        rush="dash across without a plan",
        sound="skrrt-skrik",
        strain="a careful climb",
        tags={"chalk", "teamwork", "bridge"},
    ),
}

TOOLS = {
    "thin_chalk": Tool(
        id="thin_chalk",
        label="thin chalk",
        phrase="a thin piece of chalk",
        helps={"mark_path"},
        gives={"clarity"},
        thin=True,
    )
}

GIRL_NAMES = ["Mabel", "Rose", "Nora", "Ivy", "June"]
BOY_NAMES = ["Bram", "Otis", "Eli", "Theo", "Finn"]
HELPER_NAMES = ["Aunt June", "Uncle Ben", "Mrs. Wren", "Old Joe"]
TRAITS = ["bold", "quick-thinking", "sunny", "stubborn", "cheerful"]


@dataclass
class StoryWorldFacts:
    hero: Entity
    helper: Entity
    chalk: Entity
    task: Task
    tool: Tool
    setting: Setting


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "mark_path", "thin_chalk") for place in SETTINGS]


def explain_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: the task {task.id} needs {tool.label} to make a safe mark.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.tool:
        if (args.task, args.tool) != ("mark_path", "thin_chalk"):
            raise StoryError(explain_rejection(TASKS["mark_path"], TOOLS["thin_chalk"]))

    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or "mark_path"
    tool = args.tool or "thin_chalk"

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man", "aunt", "uncle"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        task=task,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f"Write a tall tale about {hero.id} and {helper.id} using a thin piece of chalk to solve a big problem.",
        f"Tell a child-friendly story with sound effects like tap-tap and skrrt-skrik, and make teamwork the answer.",
        f"Make the chalk feel important, the trouble feel enormous, and the ending feel cheerful and earned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    chalk = world.facts["chalk"]
    return [
        QAItem(
            question=f"Who used the thin chalk in the story?",
            answer=f"{hero.id} used the thin chalk, while {helper.id} helped keep the work steady.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} need to do at {world.setting.place}?",
            answer=f"They needed to {world.facts['task'].verb}, so they could guide everyone across safely.",
        ),
        QAItem(
            question=f"How did the two of them solve the problem?",
            answer=f"They solved it by working together, with {helper.id} holding things steady while {hero.id} made the chalk marks.",
        ),
        QAItem(
            question=f"What proved the job was finished at the end?",
            answer="The chalk line stayed on the path, and the town crossed safely without slipping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does chalk do?",
            answer="Chalk makes pale marks on hard surfaces like boards, stone, or floors.",
        ),
        QAItem(
            question="Why do people work together?",
            answer="People work together so a big job becomes easier, safer, and faster.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a written sound like tap-tap or whoosh that helps the reader hear the action.",
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


def asp_facts() -> str:
    import asp

    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        if u.thin:
            lines.append(asp.fact("thin", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Tool) :- setting(Place), task(Task), tool(Tool), affords(Place, Task), helps(Tool, Task), thin(Tool).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with thin chalk and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man", "aunt", "uncle"])
    ap.add_argument("--trait", choices=TRAITS)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos.")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, task, tool in valid_combos():
            params = StoryParams(
                place=place,
                task=task,
                tool=tool,
                hero_name="Mabel",
                hero_type="girl",
                helper_name="Aunt June",
                helper_type="aunt",
                trait="bold",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
