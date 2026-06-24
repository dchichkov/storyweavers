#!/usr/bin/env python3
"""
A small adventure storyworld about an employee, a repeated warning, and a brave
choice that turns a risky errand into a successful trip.

The source-tale seed behind this world:
---
An employee named Mina worked in a little expedition office. One day, the boss
asked her to carry a sealed map packet across the windy plaza to the archive
shed. Mina wanted to hurry because the sun was sinking, but the packet could
get lost or torn if she was careless.

At the door, the boss said, "Hold it tight." Mina nodded, but the wind tugged
at the papers outside. The boss repeated the warning: "Hold it tight." Mina
heard the same words again and realized the packet needed a strap, not speed.

So Mina looped a messenger satchel over her shoulder, tucked the packet inside,
and walked the rest of the way like a careful explorer. When she arrived, the
map packet was safe, and the boss smiled at her brave patience.

World model:
- typed entities with meters and memes
- physical risk from wind, distance, and loose cargo
- emotional tension from repeated dialogue
- resolution from a practical gear choice
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

EMPLOYEE_TYPES = ["employee", "assistant", "messenger", "clerk"]
BOSS_TYPES = ["boss", "supervisor", "manager"]
LOCATIONS = {
    "office": {
        "place": "the expedition office",
        "indoor": True,
        "dist": 1,
        "wind": False,
        "affords": {"packet_run"},
    },
    "plaza": {
        "place": "the windy plaza",
        "indoor": False,
        "dist": 3,
        "wind": True,
        "affords": {"packet_run"},
    },
    "dock": {
        "place": "the old dock",
        "indoor": False,
        "dist": 4,
        "wind": True,
        "affords": {"packet_run"},
    },
}
TASKS = {
    "packet": {
        "verb": "carry the sealed map packet",
        "gerund": "carrying the sealed map packet",
        "rush": "dash across the plaza",
        "risk": "lost or torn",
        "soil": "scuffed and bent",
        "tags": {"paper", "wind"},
    },
    "lantern": {
        "verb": "carry the glass lantern",
        "gerund": "carrying the glass lantern",
        "rush": "hurry through the dark",
        "risk": "bumped or cracked",
        "soil": "shaken and chipped",
        "tags": {"glass", "dark"},
    },
    "crate": {
        "verb": "move the little supply crate",
        "gerund": "moving the little supply crate",
        "rush": "lug it through the gate",
        "risk": "dropped or banged",
        "soil": "dented and dusty",
        "tags": {"wood", "heavy"},
    },
}
GEAR = {
    "satchel": {
        "label": "a messenger satchel",
        "guard": {"packet"},
        "cover": {"paper"},
        "prep": "put on a messenger satchel",
        "tail": "strapped on the messenger satchel",
    },
    "lantern_case": {
        "label": "a padded lantern case",
        "guard": {"lantern"},
        "cover": {"glass"},
        "prep": "slip the lantern into a padded case",
        "tail": "slid the lantern into the padded case",
    },
    "cart": {
        "label": "a handcart",
        "guard": {"crate"},
        "cover": {"wood", "heavy"},
        "prep": "wheel out a handcart",
        "tail": "rolled the crate on a handcart",
    },
}
NAMES = ["Mina", "Theo", "Iris", "Nico", "June", "Eli", "Sana", "Ravi"]
TRAITS = ["brave", "careful", "curious", "steady", "quick", "lively"]


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    task: str
    gear: str
    name: str
    employee_type: str
    boss_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: dict) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.risk_tag: str = ""
        self.dialogue_repetition: int = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.risk_tag = self.risk_tag
        c.dialogue_repetition = self.dialogue_repetition
        return c


def _place_detail(setting: dict) -> str:
    if setting["indoor"]:
        return "The office felt quiet, but the doorway still hinted at the wind outside."
    return f"{setting['place'].capitalize()} was open to the sky, and the wind kept moving everything a little."


def _risk_text(task: dict, gear_ok: bool) -> str:
    if gear_ok:
        return f"That kept the {task['risk']} packet safe."
    return f"The {task['risk']} packet would not survive a careless dash."


def predict(world: World, emp: Entity, task_id: str, gear_id: str) -> dict:
    sim = world.copy()
    task = TASKS[task_id]
    gear = GEAR[gear_id]
    sim.risk_tag = task_id
    sim.dialogue_repetition = 2
    item_safe = gear_id and task_id in gear["guard"]
    return {
        "safe": item_safe and sim.setting["wind"],
        "stress": 2 if sim.setting["wind"] else 1,
    }


def reasonableness_ok(task_id: str, gear_id: str) -> bool:
    return task_id in GEAR[gear_id]["guard"]


def tell(setting: dict, task_id: str, gear_id: str, name: str, employee_type: str,
         boss_type: str, trait: str) -> World:
    world = World(setting)
    task = TASKS[task_id]
    gear = GEAR[gear_id]
    hero = world.add(Entity(id=name, kind="character", type=employee_type, meters={}, memes={}))
    boss = world.add(Entity(id="Boss", kind="character", type=boss_type, label="the boss", meters={}, memes={}))
    cargo = world.add(Entity(
        id="cargo", type=task_id, label=task_id, phrase=task["verb"], owner=hero.id,
        caretaker=boss.id, meters={"risk": 0.0}, memes={}
    ))

    world.say(f"{hero.id} was a {trait} {hero.type} who worked at {setting['place']}.")
    world.say(f"{hero.pronoun().capitalize()} loved {task['gerund']} on little errand days.")
    world.say(f"The boss handed over {hero.pronoun('object')} {task['verb']}.")
    world.say(_place_detail(setting))

    world.para()
    hero.memes["desire"] = 1
    world.say(f"{hero.id} wanted to {task['verb']}, but the wind made the route tricky.")
    world.say(f'"Hold it tight," the boss said.')
    world.say(f'{hero.id} nodded, and the boss repeated, "Hold it tight."')

    gear_ok = reasonableness_ok(task_id, gear_id)
    pred = predict(world, hero, task_id, gear_id)
    world.facts.update(hero=hero, boss=boss, cargo=cargo, task=task, gear=gear, setting=setting,
                       repeated="Hold it tight.", prediction=pred)

    world.para()
    if not gear_ok:
        raise StoryError("This gear does not honestly protect the cargo from the task.")

    world.say(f'{hero.id} listened to the repeated warning and chose a smarter way.')
    world.say(f"{hero.pronoun().capitalize()} {gear['prep']} before leaving.")

    world.para()
    cargo.meters["risk"] = 0.0
    hero.memes["stress"] = 0.0
    hero.memes["pride"] = 1
    world.say(f"Then {hero.id} {gear['tail']} and walked on like a careful explorer.")
    world.say(
        f"At the end, {hero.id} reached the archive shed with the cargo safe and the boss smiling."
    )
    world.say(_risk_text(task, True))
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, s in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if s["indoor"]:
            lines.append(asp.fact("indoor", lid))
        if s["wind"]:
            lines.append(asp.fact("windy", lid))
        lines.append(asp.fact("distance", lid, s["dist"]))
        for a in sorted(s["affords"]):
            lines.append(asp.fact("affords", lid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t["tags"]):
            lines.append(asp.fact("tag", tid, tag))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for tg in sorted(g["guard"]):
            lines.append(asp.fact("guards", gid, tg))
        for cov in sorted(g["cover"]):
            lines.append(asp.fact("covers", gid, cov))
    return "\n".join(lines)


ASP_RULES = r"""
task_risky(T) :- tag(T, paper); tag(T, glass); tag(T, heavy).
compatible(G, T) :- gear(G), guards(G, T).
valid_story(L, T, G) :- location(L), task(T), gear(G), affords(L, packet_run), compatible(G, T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for lid in LOCATIONS:
        for tid in TASKS:
            for gid in GEAR:
                if reasonableness_ok(tid, gid):
                    out.append((lid, tid, gid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about employee dialogue and repetition.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--employee-type", choices=EMPLOYEE_TYPES)
    ap.add_argument("--boss-type", choices=BOSS_TYPES)
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
    combos = valid_combos()
    if args.task and args.gear and not reasonableness_ok(args.task, args.gear):
        raise StoryError("This task and gear do not match in a reasonable way.")
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.gear:
        combos = [c for c in combos if c[2] == args.gear]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, gear = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    employee_type = args.employee_type or "employee"
    boss_type = args.boss_type or rng.choice(BOSS_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, gear=gear, name=name, employee_type=employee_type,
                       boss_type=boss_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f'Write a short adventure story about an {hero.type} named {hero.id} who must {task["verb"]}.',
        f"Tell a gentle workplace adventure where the boss repeats a warning and the employee finds a safer way.",
        f'Write a simple story that includes the repeated line "Hold it tight." and ends with the cargo safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, boss, task, gear = f["hero"], f["boss"], f["task"], f["gear"]
    return [
        QAItem(
            question=f"What kind of worker was {hero.id}?",
            answer=f"{hero.id} was a {world.facts['hero'].type} who worked in the expedition office.",
        ),
        QAItem(
            question=f"What did the boss repeat to {hero.id}?",
            answer='The boss repeated, "Hold it tight."',
        ),
        QAItem(
            question=f"How did {hero.id} keep {task['verb']} from going wrong?",
            answer=f"{hero.id} used {gear['label']} and took the careful route instead of rushing.",
        ),
        QAItem(
            question=f"Why did the repeated warning matter in the story?",
            answer=(
                f"It mattered because the wind could make the {task['risk']} cargo unsafe, "
                f"so hearing the warning twice helped {hero.id} choose a smarter plan."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a messenger satchel for?",
            answer="A messenger satchel is a bag you wear across your body so you can carry important things safely while moving.",
        ),
        QAItem(
            question="Why can wind be a problem for paper?",
            answer="Wind can catch paper and blow it around, which makes loose papers easy to lose or tear.",
        ),
        QAItem(
            question="Why do people repeat important instructions?",
            answer="People repeat important instructions so the listener remembers them and stays safe or careful.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  repetition: {world.dialogue_repetition}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.place], params.task, params.gear, params.name,
                 params.employee_type, params.boss_type, params.trait)
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


CURATED = [
    StoryParams(place="plaza", task="packet", gear="satchel", name="Mina", employee_type="employee", boss_type="boss", trait="brave"),
    StoryParams(place="dock", task="crate", gear="cart", name="Theo", employee_type="messenger", boss_type="manager", trait="careful"),
    StoryParams(place="office", task="lantern", gear="lantern_case", name="Iris", employee_type="assistant", boss_type="supervisor", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (location, task, gear) combos:\n")
        for loc, task, gear in combos:
            print(f"  {loc:10} {task:10} {gear}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
