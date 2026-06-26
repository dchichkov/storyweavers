#!/usr/bin/env python3
"""
A small animal-story world about Gaga learning a lesson through curiosity.

Seed premise:
A curious animal named Gaga keeps poking at something shiny or tempting,
gets into a small jam, then learns a gentle lesson and ends with wiser curiosity.
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

ANIMAL_TYPES = {
    "rabbit": {"ears": "long ears", "home": "burrow", "food": "carrot"},
    "fox": {"ears": "pointy ears", "home": "den", "food": "berries"},
    "bear": {"ears": "small ears", "home": "cave", "food": "honey"},
    "cat": {"ears": "soft ears", "home": "basket", "food": "fish"},
    "squirrel": {"ears": "tiny ears", "home": "nest", "food": "nuts"},
}

SETTINGS = {
    "meadow": {"place": "the meadow", "surface": "grass", "wonder": "a shining pebble"},
    "forest": {"place": "the forest", "surface": "leaves", "wonder": "a hollow acorn"},
    "riverbank": {"place": "the riverbank", "surface": "mud", "wonder": "a bright shell"},
    "garden": {"place": "the garden", "surface": "soil", "wonder": "a tiny blue flower"},
}

TEMPTATIONS = {
    "pebble": {"thing": "a shiny pebble", "mess": "scratched", "risk": "toes", "lesson": "not every pretty thing should be grabbed right away"},
    "berries": {"thing": "some ripe berries", "mess": "smeared", "risk": "muzzle", "lesson": "it is kinder to ask before taking food"},
    "puddle": {"thing": "a muddy puddle", "mess": "splashed", "risk": "paws", "lesson": "slow steps keep fur cleaner"},
    "nest": {"thing": "a tucked-away nest", "mess": "disturbed", "risk": "heart", "lesson": "curiosity should be gentle and careful"},
}

LESSON_MORAL = {
    "pebble": "Gaga learned that pretty things can be left alone until they are safe to touch.",
    "berries": "Gaga learned that curiosity is best when it is polite and patient.",
    "puddle": "Gaga learned that little paws can avoid a lot of mess by slowing down.",
    "nest": "Gaga learned to look first, then step softly.",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    animal: str
    setting: str
    temptation: str
    name: str = "Gaga"
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.params)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "place": v.place, "meters": dict(v.meters), "memes": dict(v.memes),
            "traits": list(v.traits),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: Gaga learns a lesson through curiosity.")
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--name", default="Gaga")
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


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMAL_TYPES:
        lines.append(asp.fact("animal", a))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t, d in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", t))
        lines.append(asp.fact("lesson", t, d["lesson"]))
    lines.append("\n".join([]))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,S,T) :- animal(A), setting(S), temptation(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(a, s, t) for a in ANIMAL_TYPES for s in SETTINGS for t in TEMPTATIONS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("Mismatch between clingo and python.")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    animal = args.animal or rng.choice(sorted(ANIMAL_TYPES))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    temptation = args.temptation or rng.choice(sorted(TEMPTATIONS))
    return StoryParams(animal=animal, setting=setting, temptation=temptation, name=args.name)


def _do_wonder(world: World) -> None:
    hero = world.get("hero")
    temp = world.get("temptation")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.label} noticed {temp.phrase} and leaned closer, because curiosity made {hero.pronoun('object')} brave.")


def _do_misstep(world: World) -> None:
    hero = world.get("hero")
    temp = world.get("temptation")
    if temp.type == "pebble":
        hero.meters["scratched"] = hero.meters.get("scratched", 0.0) + 1
        world.say(f"{hero.label} tapped the pebble too fast and scratched a paw.")
    elif temp.type == "berries":
        hero.meters["smeared"] = hero.meters.get("smeared", 0.0) + 1
        world.say(f"{hero.label} nibbled too eagerly and got berry juice on {hero.pronoun('possessive')} muzzle.")
    elif temp.type == "puddle":
        hero.meters["splashed"] = hero.meters.get("splashed", 0.0) + 1
        world.say(f"{hero.label} hopped into the puddle and splashed muddy water everywhere.")
    else:
        hero.meters["disturbed"] = hero.meters.get("disturbed", 0.0) + 1
        world.say(f"{hero.label} poked around the nest and made the little twigs shake.")


def _lesson_learned(world: World) -> None:
    hero = world.get("hero")
    temp = world.get("temptation")
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1
    world.say(f"Then {hero.label} paused and remembered a kind lesson: {LESSON_MORAL[temp.type]}")


def tell(params: StoryParams) -> World:
    if params.animal not in ANIMAL_TYPES:
        raise StoryError("Unknown animal.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.temptation not in TEMPTATIONS:
        raise StoryError("Unknown temptation.")
    world = World(params)
    animal = ANIMAL_TYPES[params.animal]
    temp = TEMPTATIONS[params.temptation]

    hero = world.add(Entity(
        id="hero", kind="character", type=params.animal, label=params.name,
        phrase=f"a curious {params.animal}", traits=["curious", "little"],
        meters={}, memes={"curiosity": 0.0, "understanding": 0.0},
    ))
    setting = world.add(Entity(
        id="setting", kind="thing", type="place", label=SETTINGS[params.setting]["place"],
        phrase=SETTINGS[params.setting]["place"],
    ))
    temptation = world.add(Entity(
        id="temptation", kind="thing", type=params.temptation, label=temp["thing"],
        phrase=temp["thing"], place=SETTINGS[params.setting]["place"],
    ))

    world.say(f"On a bright day in {setting.label}, {hero.label} was a little {params.animal} with {animal['ears']}.")
    world.say(f"{hero.label} liked to wander near the {SETTINGS[params.setting]['surface']} and ask questions about everything.")
    world.para()
    world.say(f"At the edge of the {setting.label}, {hero.label} spotted {temptation.phrase}.")
    _do_wonder(world)
    _do_misstep(world)
    world.para()
    _lesson_learned(world)
    world.say(f"After that, {hero.label} was still curious, but {hero.label} chose to look first and step softly.")
    world.say(f"The little {params.animal} went home with clean paws and a wiser heart.")

    world.facts.update(hero=hero, setting=setting, temptation=temptation, animal=params.animal)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short animal story about {f['hero'].label}, a curious {f['animal']} named Gaga, who learns a lesson.",
        f"Tell a child-friendly story where Gaga sees {f['temptation'].phrase} and discovers a gentle lesson.",
        f"Write an Animal Story with curiosity, a small mistake, and a lesson learned in {f['setting'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    temp = f["temptation"]
    setting = f["setting"]
    animal = f["animal"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a curious {animal} named Gaga.",
        ),
        QAItem(
            question=f"What did Gaga notice in {setting.label}?",
            answer=f"Gaga noticed {temp.phrase} and got very curious about it.",
        ),
        QAItem(
            question=f"What lesson did Gaga learn?",
            answer=f"Gaga learned that {LESSON_MORAL[temp.type].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and to look closely at new things.",
        ),
        QAItem(
            question="What should an animal do before touching something unfamiliar?",
            answer="It should look carefully first and make sure it is safe.",
        ),
        QAItem(
            question="Why is it good to learn a lesson?",
            answer="Learning a lesson helps you make better choices next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.type} {e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for animal in sorted(ANIMAL_TYPES):
            for setting in sorted(SETTINGS):
                for temptation in sorted(TEMPTATIONS):
                    samples.append(generate(StoryParams(animal=animal, setting=setting, temptation=temptation, seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 and not args.all else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
