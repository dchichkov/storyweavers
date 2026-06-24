#!/usr/bin/env python3
"""
Storyworld: Grump Pitcher Inner Monologue Flashback Space Adventure

A tiny, constraint-checked story domain about a grumpy space traveler, a pitcher,
and a small mess on a ship that gets solved by remembering a kind past moment.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    location: str = ""
    portable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the starship corridor"
    indoors: bool = True
    afford: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tag: str
    requires: set[str] = field(default_factory=set)
    flashback_hook: str = ""


@dataclass
class Gear:
    id: str
    label: str
    protects: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.trace = []
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("jostle", 0) < THRESHOLD:
            continue
        for ent in world.entities.values():
            if ent.owner != actor.id or ent.location != world.setting.place:
                continue
            sig = ("spill", actor.id, ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if "liquid" in ent.traits:
                ent.meters["spilled"] = ent.meters.get("spilled", 0) + 1
                ent.meters["dirty"] = ent.meters.get("dirty", 0) + 1
                out.append(f"{ent.label_word.capitalize()} splashed the deck with a little spill.")
    return out


def _r_mood(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("spilled", 0) >= THRESHOLD and actor.memes.get("grump", 0) < THRESHOLD:
            sig = ("grump", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["grump"] = actor.memes.get("grump", 0) + 1
            out.append(f"{actor.id}'s face turned grumpy at the mess.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("grump", 0) < THRESHOLD:
            continue
        if world.facts.get("flashback_seen"):
            continue
        world.facts["flashback_seen"] = True
        actor.memes["soft"] = actor.memes.get("soft", 0) + 1
        out.append("__flashback__")
    return out


CAUSAL_RULES = [
    Rule("spill", _r_spill),
    Rule("mood", _r_mood),
    Rule("flashback", _r_flashback),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__flashback__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, actor: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["jostle"] = 1
    propagate(sim, narrate=False)
    pitcher = next((e for e in sim.entities.values() if e.type == "pitcher"), None)
    return {
        "spilled": bool(pitcher and pitcher.meters.get("spilled", 0) >= THRESHOLD),
        "grump": sum(e.memes.get("grump", 0) for e in sim.characters()),
    }


def setup_line(world: World, hero: Entity, pitcher: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.label_word} aboard the {world.setting.place}, "
        f"and {hero.pronoun('possessive')} favorite {pitcher.label_word} sat nearby like a shiny moon."
    )


def inciting_incident(world: World, hero: Entity, pitcher: Entity, action: Action) -> None:
    hero.meters["jostle"] = hero.meters.get("jostle", 0) + 1
    world.say(
        f"On a quiet space day, {hero.id} wanted to {action.verb}, but the corridor rocked."
    )
    world.say(
        f"{hero.pronoun().capitalize()} thought, 'If I hurry, the {pitcher.label_word} could slip.'"
    )


def warning(world: World, hero: Entity, pitcher: Entity, action: Action) -> bool:
    pred = predict_spill(world, hero)
    if not pred["spilled"]:
        return False
    world.facts["warning"] = True
    world.say(
        f'"Careful," {hero.pronoun("possessive")} captain said. "That {pitcher.label_word} may spill if you rush."'
    )
    return True


def grump_turn(world: World, hero: Entity, action: Action) -> None:
    hero.memes["grump"] = hero.memes.get("grump", 0) + 1
    world.say(f"{hero.id} frowned and tried to {action.rush}.")
    propagate(world, narrate=True)


def flashback(world: World, hero: Entity) -> None:
    world.para()
    world.say(
        f"Then a flashback flickered in {hero.pronoun('possessive')} mind: once, "
        f"the captain had shared a warm drink after a cold comet watch."
    )
    world.say(
        f"Inner Monologue: 'When I remember kind moments, my chest feels less stormy.'"
    )
    hero.memes["soft"] = hero.memes.get("soft", 0) + 1
    hero.memes["grump"] = 0


def compromise(world: World, hero: Entity, pitcher: Entity, gear: Gear, action: Action) -> None:
    world.say(
        f"{hero.id} held the {pitcher.label_word} with both hands and took one slow step at a time."
    )
    world.say(
        f"With {gear.label}, {hero.id} could {action.verb} without spilling the water."
    )


def ending(world: World, hero: Entity, pitcher: Entity) -> None:
    world.say(
        f"In the end, the {pitcher.label_word} stayed full, the deck stayed dry, and {hero.id} smiled at the stars."
    )


def tell(setting: Setting, action: Action, hero_name: str = "Nori") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label="space kid", traits=["grumpy", "curious"]))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="captain"))
    pitcher = world.add(Entity(id="Pitcher", type="pitcher", label="pitcher", phrase="a silver pitcher", owner=hero.id, caretaker=captain.id, location=setting.place, traits=["liquid"]))
    gear = world.add(Entity(id="GripGloves", type="gear", label="grip gloves", owner=hero.id, location=setting.place, traits=["protective"]))

    setup_line(world, hero, pitcher)
    world.para()
    inciting_incident(world, hero, pitcher, action)
    warning(world, hero, pitcher, action)
    grump_turn(world, hero, action)
    flashback(world, hero)
    world.para()
    compromise(world, hero, pitcher, Gear(id="GripGloves", label="grip gloves", protects={"spill"}, prep="wear grip gloves", tail="wore the grip gloves"))
    ending(world, hero, pitcher)

    world.facts.update(hero=hero, captain=captain, pitcher=pitcher, gear=gear, action=action, setting=setting)
    return world


SETTINGS = {
    "corridor": Setting(place="the starship corridor", indoors=True, afford={"carry"}),
    "galley": Setting(place="the ship's galley", indoors=True, afford={"pour"}),
    "observation": Setting(place="the observation deck", indoors=True, afford={"carry"}),
}

ACTIONS = {
    "carry": Action(
        id="carry",
        verb="carry the pitcher to the table",
        gerund="carrying the pitcher",
        rush="dash around the bend",
        mess="spill",
        soil="spilled",
        tag="space",
        flashback_hook="warm drink",
    ),
    "pour": Action(
        id="pour",
        verb="pour water for the crew",
        gerund="pouring water",
        rush="tip it too fast",
        mess="spill",
        soil="spilled",
        tag="space",
        flashback_hook="shared drink",
    ),
}

GEAR = [
    Gear(id="grip_gloves", label="grip gloves", protects={"spill"}, prep="wear grip gloves", tail="wore the grip gloves"),
]

TRAITS = ["grumpy", "curious", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, act) for place, setting in SETTINGS.items() for act in setting.afford]


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a small space adventure story about a grump and a pitcher, with an inner monologue and a flashback.",
        f"Tell a child-friendly story where {f['hero'].id} must carry a pitcher safely through {f['setting'].place}.",
        "Write a simple story that begins with a grumpy mood, includes a remembered kind moment, and ends with a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    pitcher = f["pitcher"]
    action = f["action"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=f"It is about {hero.id}, a little space kid who has to handle the {pitcher.label_word} carefully.",
        ),
        QAItem(
            question=f"Why did {hero.id} get grumpy?",
            answer=f"{hero.id} got grumpy because the ship rocked and the {pitcher.label_word} might spill if {hero.pronoun('subject')} rushed.",
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer="The flashback was about a warm drink the captain once shared during a cold comet watch.",
        ),
        QAItem(
            question=f"How did {hero.id} finally solve the problem?",
            answer=f"{hero.id} slowed down, used grip gloves, and carried the {pitcher.label_word} carefully so nothing spilled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pitcher?",
            answer="A pitcher is a container used for carrying and pouring drinks or water.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a quick memory of something that happened earlier.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thinking a character does in their own mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="corridor", action="carry", name="Nori"),
    StoryParams(place="galley", action="pour", name="Mika"),
    StoryParams(place="observation", action="carry", name="Tess"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld: a grump, a pitcher, an inner monologue, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
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
              and (args.action is None or c[1] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Nori", "Mika", "Tess", "Jin", "Luma"])
    return StoryParams(place=place, action=action, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], params.name)
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
valid(Place, Action) :- affords(Place, Action).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
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
