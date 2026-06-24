#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/revenge_option_guardian_soccer_field_happy_ending.py
===============================================================================================================================

A small Fairy Tale storyworld about a soccer field, a guardian, revenge, and
an option that leads to a happy ending through transformation.

Seed-tale inspiration:
---
A child wanted revenge after a mean shove during a soccer game. A wise guardian
offered an option: choose the kinder path, or choose the revenge path and lose
the game. The child changed their mind, helped the other player, and the field
felt bright again.

World model:
- meters: distance, possession, trust, damage, repair, grace
- memes: anger, fear, hope, shame, joy, pride

The story is driven by state changes:
- a shove raises anger and damage
- a guardian offers a concrete option
- choosing revenge causes harm and more shame
- choosing repair transforms the child, increasing grace and joy
- the happy ending is shown by the final field state
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

FAMILY_TYPES = {"girl", "boy", "child", "mother", "father", "guardian", "coach"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    guardian: str
    option: str
    seed: Optional[int] = None


@dataclass
class Option:
    id: str
    label: str
    action: str
    method: str
    outcome: str
    transforms: bool = False
    dangerous: bool = False


@dataclass
class Setting:
    place: str
    banner: str


SOCCER_FIELD = Setting(
    place="the soccer field",
    banner="The grass was bright, the goal waited at the end, and the white lines looked like a story drawn on the earth.",
)

OPTIONS = {
    "revenge": Option(
        id="revenge",
        label="revenge",
        action="kick the ball at the other child to get even",
        method="a hard, angry kick",
        outcome="the game would turn mean and lonely",
        transforms=False,
        dangerous=True,
    ),
    "repair": Option(
        id="repair",
        label="kind repair",
        action="give back the ball and help the other child up",
        method="a careful, honest step",
        outcome="the hurt would soften and the game could begin again",
        transforms=True,
        dangerous=False,
    ),
}

TRAITS = ["brave", "gentle", "curious", "stubborn", "hopeful", "playful"]
NAMES = {
    "girl": ["Mira", "Lina", "Tess", "Nora"],
    "boy": ["Otis", "Evan", "Theo", "Ben"],
    "child": ["Robin", "Perry", "Sunny", "Rowan"],
}


class StoryWorld(World):
    pass


def _bump(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _raise(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def predict(world: World, child: Entity, option: Option) -> dict:
    sim = world.copy()
    c = sim.get(child.id)
    if option.dangerous:
        _raise(c, "anger", 1)
        _bump(c, "damage", 1)
        _raise(c, "shame", 1)
    if option.transforms:
        _raise(c, "grace", 1)
        _raise(c, "joy", 1)
    return {
        "damage": c.meters.get("damage", 0.0),
        "grace": c.memes.get("grace", 0.0),
    }


def setup_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(SOCCER_FIELD.place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    guardian = world.add(Entity(id="guardian", kind="character", type="guardian", label=params.guardian))
    rival = world.add(Entity(id="rival", kind="character", type="child", label="the other child"))
    ball = world.add(Entity(id="ball", kind="thing", type="ball", label="the ball"))
    field = world.add(Entity(id="field", kind="thing", type="field", label="the field"))

    child.memes.update({"anger": 0.0, "fear": 0.0, "hope": 0.0, "shame": 0.0, "joy": 0.0, "pride": 0.0, "grace": 0.0})
    child.meters.update({"distance": 0.0, "possession": 1.0, "trust": 0.0, "damage": 0.0, "repair": 0.0})
    guardian.memes.update({"calm": 1.0, "hope": 1.0})
    rival.memes.update({"hurt": 1.0})
    ball.meters.update({"possession": 1.0})
    field.meters.update({"damage": 0.0, "repair": 0.0})

    world.facts.update(child=child, guardian=guardian, rival=rival, ball=ball, field=field)
    return world


def tell(world: StoryWorld, option: Option) -> None:
    child: Entity = world.facts["child"]
    guardian: Entity = world.facts["guardian"]
    rival: Entity = world.facts["rival"]
    field: Entity = world.facts["field"]

    world.say(
        f"Once upon a time, {child.id} came to {world.place} and saw the other child push {child.pronoun('object')} during the game."
    )
    _raise(child, "anger", 1)
    _raise(child, "fear", 1)
    _bump(field, "damage", 1)
    world.say(
        f"{child.id} felt anger rise like a small storm, and even the grass seemed bent where the shove had landed."
    )

    world.para()
    world.say(
        f"Then {guardian.label} stepped close and offered an option: choose {OPTIONS['revenge'].label} or choose the kinder path."
    )
    world.say(
        f'\"If you choose revenge,\" said the guardian, \"the hurt will grow; if you choose repair, the game can heal.\"'
    )
    world.facts["offered_option"] = option.id

    world.para()
    if option.dangerous:
        _raise(child, "anger", 1)
        _raise(child, "shame", 1)
        _bump(child, "damage", 1)
        _bump(rival, "damage", 1)
        world.say(
            f"{child.id} tried the revenge option and made a hard kick instead of a fair one."
        )
        world.say(
            f"The ball skidded away, {rival.label} cried out, and the field grew heavier with hurt."
        )
        world.say(
            f"At once, {child.id} knew the mean choice was not a victory at all."
        )
        world.facts["transformed"] = False
    else:
        _raise(child, "hope", 1)
        _raise(child, "grace", 1)
        _raise(child, "joy", 1)
        _bump(child, "repair", 1)
        _bump(rival, "repair", 1)
        _bump(field, "repair", 1)
        child.meters["possession"] = 0.0
        world.say(
            f"{child.id} chose the repair option and handed the ball back with both hands."
        )
        world.say(
            f"Then {child.id} helped {rival.label} stand, and the tense knot in the air loosened into laughter."
        )
        world.say(
            f"Something changed inside {child.id}: the anger became courage, and courage became grace."
        )
        world.facts["transformed"] = True

    world.para()
    if option.dangerous:
        world.say(
            f"Still, the guardian did not scold. {guardian.label} showed {child.id} how to stop, breathe, and begin again."
        )
        _raise(child, "hope", 1)
        _raise(child, "grace", 1)
        _bump(child, "repair", 1)
        world.say(
            f"{child.id} put the revenge idea down like a heavy stone and chose to make things right."
        )
        world.say(
            f"By the last whistle, {child.id} was kinder than before, and the field felt ready for a better game."
        )
        world.facts["transformed"] = True
    else:
        world.say(
            f"By the last whistle, {child.id} was smiling, {rival.label} was smiling too, and the guardian could see the change plainly."
        )
        world.say(
            f"The soccer field looked the same, but the people on it had become gentler, and that made it feel brighter than gold."
        )


def build_story(params: StoryParams) -> StoryWorld:
    world = setup_world(params)
    tell(world, OPTIONS[params.option])
    return world


def generation_prompts(params: StoryParams) -> list[str]:
    opt = OPTIONS[params.option]
    return [
        f"Write a Fairy Tale story set on a soccer field about a child who faces a choice between revenge and a kinder option.",
        f"Tell a short story where a guardian offers {opt.label} as a choice and the child changes through transformation.",
        f"Write a happy ending story with a soccer field, a guardian, and an option that turns anger into grace.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    child: Entity = world.facts["child"]
    guardian: Entity = world.facts["guardian"]
    rival: Entity = world.facts["rival"]
    option = OPTIONS[world.facts["offered_option"]]
    qa = [
        QAItem(
            question=f"Why did {guardian.label} offer {child.id} an option on the soccer field?",
            answer=(
                f"{guardian.label} saw that {child.id} was angry after the shove and wanted to keep the game from turning mean. "
                f"The guardian offered a choice so {child.id} could avoid revenge and choose a kinder path."
            ),
        ),
        QAItem(
            question=f"What happened when {child.id} chose the {option.label} path?",
            answer=(
                f"{child.id} changed from anger toward grace. The child gave back what was taken, helped {rival.label}, and the field became calm again."
            ),
        ),
        QAItem(
            question=f"What proved that the story had a happy ending?",
            answer=(
                f"By the end, {child.id} and {rival.label} were smiling, and the guardian could see that the hurt had turned into repair. "
                f"That final calm scene proved the ending was happy."
            ),
        ),
    ]
    if world.facts.get("transformed"):
        qa.append(
            QAItem(
                question=f"How did {child.id} transform during the story?",
                answer=(
                    f"{child.id} transformed from wanting revenge into choosing repair and kindness. "
                    f"The anger shrank, grace grew, and the child became gentler by the end."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is revenge?",
            answer="Revenge is trying to hurt someone back because you feel wronged, but it usually makes a problem worse instead of better.",
        ),
        QAItem(
            question="What is an option?",
            answer="An option is a choice you can make between two or more different paths.",
        ),
        QAItem(
            question="What does a guardian do?",
            answer="A guardian watches over someone, gives guidance, and helps them stay safe and wise.",
        ),
        QAItem(
            question="What is a soccer field?",
            answer="A soccer field is a grassy place with lines and goals where people play soccer.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means a big change, like when a person becomes kinder, braver, or wiser.",
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


def dump_trace(world: StoryWorld) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(parts)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy", "child"])
    name = args.name or rng.choice(NAMES.get(gender, NAMES["child"]))
    guardian = args.guardian or rng.choice(["wise guardian", "kind guardian", "old guardian"])
    option = args.option or rng.choice(list(OPTIONS))
    if option not in OPTIONS:
        raise StoryError("Unknown option.")
    return StoryParams(name=name, gender=gender, guardian=guardian, option=option)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy Tale storyworld set on a soccer field.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
    ap.add_argument("--guardian")
    ap.add_argument("--option", choices=list(OPTIONS))
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


ASP_RULES = r"""
#show chosen/1.
#show transformed/1.
has_revenge_choice(revenge).
has_kind_choice(repair).

chosen(revenge) :- opt(revenge).
chosen(repair) :- opt(repair).

transformed(C) :- choice(C), kind(C).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("opt", oid) for oid in OPTIONS]
    lines.append(asp.fact("choice", "revenge"))
    lines.append(asp.fact("choice", "repair"))
    lines.append(asp.fact("kind", "repair"))
    lines.append(asp.fact("danger", "revenge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_options() -> list[str]:
    return sorted(OPTIONS)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show chosen/1."))
    chosen = sorted(set(asp.atoms(model, "chosen")))
    py = [("revenge",), ("repair",)]
    if chosen == py:
        print("OK: ASP and Python option registry agree.")
        return 0
    print("MISMATCH:")
    print("ASP:", chosen)
    print("PY :", py)
    return 1


CURATED = [
    StoryParams(name="Mira", gender="girl", guardian="wise guardian", option="revenge"),
    StoryParams(name="Robin", gender="child", guardian="kind guardian", option="repair"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show chosen/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("available options:", ", ".join(valid_options()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
