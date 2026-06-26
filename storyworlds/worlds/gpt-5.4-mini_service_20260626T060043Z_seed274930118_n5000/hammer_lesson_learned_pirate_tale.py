#!/usr/bin/env python3
"""
storyworlds/worlds/hammer_lesson_learned_pirate_tale.py
=======================================================

A small pirate-tale story world about a noisy hammer, a bad choice, and a
lesson learned.

Premise:
- A young pirate loves a useful hammer.
- The hammer can fix ship things, but if used carelessly it can cause trouble.

Turn:
- A shipmate warns that hammering at the wrong time will wake the crew, dent
  the lantern box, or crack a plank.

Resolution:
- The pirate slows down, uses a better method, and learns that a good tool only
  helps when the hands using it are careful.

This world is deliberately tiny and classical: one domain, one tension, one
turn, one ending image.
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
    held_by: Optional[str] = None
    useful: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "pirate-girl"}
        male = {"boy", "man", "father", "pirate-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Setting:
    place: str = "the ship"
    night: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    risk: str
    keyword: str = "hammer"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    method: str
    closing: str
    careful: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.activity: str = ""

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
        clone.activity = self.activity
        return clone


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("hammering", 0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["noise"] = actor.memes.get("noise", 0) + 1
        out.append(f"The loud bang-bang echoed through the ship.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    actor = next((a for a in world.characters() if a.meters.get("hammering", 0) >= THRESHOLD), None)
    if not actor:
        return out
    for item in world.entities.values():
        if not item.fragile or item.held_by == actor.id:
            continue
        if item.meters.get("risk", 0) < THRESHOLD:
            continue
        sig = ("damage", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["dented"] = item.meters.get("dented", 0) + 1
        out.append(f"{item.label.capitalize()} got dented.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("regret", 0) < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson_learned"] = actor.memes.get("lesson_learned", 0) + 1
        out.append(f"{actor.pronoun().capitalize()} learned to use the hammer with care.")
    return out


CAUSAL_RULES = [_r_noise, _r_damage, _r_lesson]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def predict_damage(world: World, actor: Entity, action: Action, target_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, target_id, narrate=False)
    target = sim.entities[target_id]
    return {
        "damaged": target.meters.get("dented", 0) >= THRESHOLD,
        "noise": actor.memes.get("noise", 0),
    }


def _do_action(world: World, actor: Entity, action: Action, target_id: str, narrate: bool = True) -> None:
    actor.meters[action.mess] = actor.meters.get(action.mess, 0) + 1
    if target_id in world.entities:
        world.entities[target_id].meters["risk"] = world.entities[target_id].meters.get("risk", 0) + 1
    propagate(world)
    if narrate:
        world.say(f"{actor.id} used the hammer to {action.verb}.")


def tell(setting: Setting, action: Action, hero_name: str, hero_type: str, shipmate_name: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    shipmate = world.add(Entity(id=shipmate_name, kind="character", type="pirate", meters={}, memes={}))
    hammer = world.add(Entity(id="hammer", type="hammer", label="hammer", phrase="a sturdy little hammer", owner=hero.id, held_by=hero.id, useful=True))
    lantern_box = world.add(Entity(id="lantern_box", type="box", label="lantern box", phrase="the lantern box", fragile=True, caret 
aker=shipmate.id))
    plank = world.add(Entity(id="plank", type="plank", label="loose plank", phrase="a loose plank", fragile=True, caretaker=shipmate.id))

    world.activity = action.id

    world.say(
        f"{hero.id} was a small pirate with bright eyes and a favorite hammer."
    )
    world.say(
        f"{hero.id} loved fixing things on {world.setting.place}, and {hero.pronoun('possessive')} hammer felt like a tiny treasure."
    )

    world.para()
    world.say(
        f"One { 'night' if world.setting.night else 'day' }, {hero.id} saw that a {action.id} needed fixing."
    )
    world.say(
        f"{hero.id} wanted to {action.verb}, but {shipmate_name} warned, "
        f"\"Careful now. That {action.keyword} could make trouble {action.risk}.\""
    )

    if action.id == "lantern":
        lantern_box.meters["risk"] = 1
    else:
        plank.meters["risk"] = 1

    predicted = predict_damage(world, hero, action, lantern_box.id if action.id == "lantern" else plank.id)
    if predicted["damaged"]:
        world.say(
            f"{hero.id} frowned and held the hammer still for a moment."
        )
        world.say(
            f"{shipmate_name} pointed to the safer way: use a softer tool, or wait until the deck was clear."
        )
        hero.memes["regret"] = 1

    world.para()
    world.say(
        f"{hero.id} took a breath, set the hammer down, and chose a gentler fix."
    )
    world.say(
        f"Together they mended the {action.id} without making a mess."
    )
    hero.memes["lesson_learned"] = 1
    world.say(
        f"By the end, {hero.id} smiled at the steady work and remembered that a good hammer is best in careful hands."
    )

    world.facts.update(
        hero=hero,
        shipmate=shipmate,
        hammer=hammer,
        action=action,
        setting=setting,
        target=lantern_box if action.id == "lantern" else plank,
        lesson=True,
    )
    return world


SETTINGS = {
    "ship": Setting(place="the ship", night=False, affords={"lantern", "plank"}),
    "dock": Setting(place="the dock", night=True, affords={"plank"}),
    "harbor": Setting(place="the harbor", night=False, affords={"lantern", "plank"}),
}

ACTIONS = {
    "lantern": Action(
        id="lantern",
        verb="fix the lantern box",
        gerund="fixing the lantern box",
        rush="bang it fast",
        mess="hammering",
        soil="dented and noisy",
        risk="by the sleeping crew",
        tags={"hammer", "lesson", "ship"},
    ),
    "plank": Action(
        id="plank",
        verb="mend the loose plank",
        gerund="mending the loose plank",
        rush="strike the nails hard",
        mess="hammering",
        soil="cracked and crooked",
        risk="near the edge",
        tags={"hammer", "lesson", "ship"},
    ),
}

GIRL_NAMES = ["Mara", "Tess", "Nina", "Pip", "Rosa"]
BOY_NAMES = ["Finn", "Rowan", "Ned", "Jack", "Bram"]
SHIPMATE_NAMES = ["Captain Reed", "Molly", "Old Tom", "Sailor June", "Matey Finn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            combos.append((place, act_id))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    gender: str
    shipmate: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, action = f["hero"], f["action"]
    return [
        f'Write a short pirate tale for a child that includes the word "hammer" and ends with a lesson learned.',
        f"Tell a gentle pirate story where {hero.id} wants to {action.verb} with a hammer but learns to be careful.",
        f"Write a tiny shipboard story about a hammer, a warning, and a smarter way to fix things.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, shipmate, action = f["hero"], f["shipmate"], f["action"]
    target = f["target"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with the hammer?",
            answer=f"{hero.id} wanted to {action.verb}."
        ),
        QAItem(
            question=f"Who warned {hero.id} to be careful?",
            answer=f"{shipmate.id} warned {hero.id} to be careful because the {action.id} could cause trouble."
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that a hammer works best when it is used carefully, and not in a rush."
        ),
        QAItem(
            question=f"What was getting fixed in the story?",
            answer=f"They were working on {target.phrase}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hammer for?",
            answer="A hammer is a tool used to hit nails, fix wood, and help build or mend things."
        ),
        QAItem(
            question="Why should a hammer be used carefully?",
            answer="A hammer can dent, crack, or hurt things if it is swung too hard or too fast."
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand a better way to act after something goes wrong."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} ({e.type:10}) "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
valid(Place, Action) :- affords(Place, Action).
useful_hammer(Action) :- valid(Place, Action), action(Action).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world: hammer, warning, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--shipmate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.action and args.action not in SETTINGS[args.place].affords:
        raise StoryError("That place cannot support that action.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    shipmate = args.shipmate or rng.choice(SHIPMATE_NAMES)
    return StoryParams(place=place, action=action, name=name, gender=gender, shipmate=shipmate)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], params.name, "pirate-boy" if params.gender == "boy" else "pirate-girl", params.shipmate)
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
    StoryParams(place="ship", action="lantern", name="Mara", gender="girl", shipmate="Captain Reed"),
    StoryParams(place="dock", action="plank", name="Finn", gender="boy", shipmate="Old Tom"),
    StoryParams(place="harbor", action="lantern", name="Pip", gender="girl", shipmate="Sailor June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a[0]} {a[1]}" for a in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
