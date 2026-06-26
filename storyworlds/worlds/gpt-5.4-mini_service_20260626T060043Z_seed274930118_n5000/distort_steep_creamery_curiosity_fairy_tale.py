#!/usr/bin/env python3
"""
A small fairy-tale storyworld about curiosity, a steep path, and a creamery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the creamery"
    steep: bool = False
    weather: str = "bright"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    treat: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace_log: list[str] = field(default_factory=list)

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

    def clone(self) -> "World":
        return World(
            setting=replace(self.setting),
            entities={k: Entity(**{
                **vars(v),
                "meters": dict(v.meters),
                "memes": dict(v.memes),
                "caretakers": list(v.caretakers),
            }) for k, v in self.entities.items()},
            paragraphs=[[]],
            facts=dict(self.facts),
            trace_log=list(self.trace_log),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "creamery": Setting(place="the creamery", steep=False, weather="bright"),
    "hillside_creamery": Setting(place="the creamery on the steep hill", steep=True, weather="bright"),
}

TREATS = {
    "vanilla": "a vanilla cone with a sugar curl",
    "berry": "a berry cup with a silver spoon",
    "honey": "a honey swirl in a little glass dish",
}

GIRL_NAMES = ["Ayla", "Mira", "Nora", "Lina", "Elsa", "Faye"]
BOY_NAMES = ["Owen", "Pip", "Rowan", "Finn", "Jules", "Eli"]
TRAITS = ["curious", "brave", "gentle", "cheerful", "lively"]


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def start_story(world: World, child: Entity, parent: Entity, treat: Entity) -> None:
    world.say(
        f"Once upon a time, there was a little {child.memes['trait']} {child.type} named {child.id}."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} loved visiting {world.setting.place} "
        f"because the sweet smell of cream and sugar made every day feel like a storybook."
    )
    world.say(
        f"{child.id}'s {parent.type} bought {child.pronoun('object')} {treat.phrase}, and {child.id} treasured it."
    )


def arrive(world: World, child: Entity, parent: Entity) -> None:
    if world.setting.steep:
        world.say(
            f"One bright day, {child.id} and {child.pronoun('possessive')} {parent.type} walked up the steep hill to the creamery."
        )
    else:
        world.say(
            f"One bright day, {child.id} and {child.pronoun('possessive')} {parent.type} walked to the creamery."
        )


def curiosity_tug(world: World, child: Entity, treat: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} grew curious about how the creamery made such smooth scoops."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} peeked past the counter and wanted to see the churn and the jars and the tall spoon rack."
    )
    child.meters["lean"] = child.meters.get("lean", 0) + 1
    if world.setting.steep:
        child.meters["wobble"] = child.meters.get("wobble", 0) + 1
        world.trace_log.append("curiosity + steep hill -> wobble")


def warn_about_distort(world: World, parent: Entity, child: Entity, treat: Entity) -> None:
    world.say(
        f'"Careful," said {parent.id}. "If you lean too far, you might distort the cream and spill {treat.phrase}."'
    )
    world.facts["warning"] = True


def wobble_event(world: World, child: Entity, treat: Entity) -> bool:
    if child.meters.get("wobble", 0) < 1:
        return False
    world.say(
        f"{child.id} took one curious step too many on the steep path, and the little cup tilted."
    )
    world.say(
        f"The swirl did not break, but the spoon and cup tipped just enough to distort the pretty pattern on top."
    )
    treat.meters["distorted"] = treat.meters.get("distorted", 0) + 1
    world.facts["distorted"] = True
    return True


def fix_story(world: World, parent: Entity, child: Entity, treat: Entity) -> None:
    if treat.meters.get("distorted", 0) < 1:
        return
    world.para()
    world.say(
        f"{parent.id} did not scold. {parent.pronoun('subject').capitalize()} simply set the cup down and showed {child.id} a safer way to look."
    )
    world.say(
        f"Together they steeped their curiosity in patience, one small question at a time, until the answer felt sweet instead of slippery."
    )
    world.say(
        f"{child.id} laughed, held the treat carefully with both hands, and the creamery felt magical again."
    )
    world.say(
        f"In the end, the cup stayed a little distorted on top, but {child.id}'s curiosity was no longer a trouble; it had become a lesson."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"curiosity": 0.0, "trait": 1.0},
    ))
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait_name"] = 1.0
    child.memes["curious"] = 1.0
    child.memes["trait_word"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait_label"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait_name"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait_name"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait_word"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait"] = 1.0
    child.memes["trait_name"] = params.parent

    parent = world.add(Entity(
        id=params.parent,
        kind="character",
        type=params.parent,
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label="treat",
        phrase=TREATS[params.treat],
        owner=child.id,
        meters={"delicacy": 1.0},
    ))

    world.facts.update(
        child=child.id,
        parent=parent.id,
        treat=params.treat,
        place=params.place,
        setting=setting,
    )

    start_story(world, child, parent, treat)
    world.para()
    arrive(world, child, parent)
    curiosity_tug(world, child, treat)
    warn_about_distort(world, parent, child, treat)
    wobble_event(world, child, treat)
    fix_story(world, parent, child, treat)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy tale about curiosity at a creamery on a steep hill.',
        f"Tell a child-friendly story where {f['child']} becomes curious in {f['place']} and learns a careful lesson.",
        'Write a short fairy tale that includes the words "distort", "steep", and "creamery".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    place = f["place"]
    treat = f["treat"]
    resolved = f.get("resolved", False)
    distorted = f.get("distorted", False)
    answers = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child}, a curious little child who visits {place} with {parent}.",
        ),
        QAItem(
            question=f"What did {child} want to learn about at the creamery?",
            answer=f"{child} wanted to learn how the creamery made its sweet treats and smooth scoops.",
        ),
        QAItem(
            question=f"What did {parent} warn might happen if {child} leaned too far?",
            answer=f"{parent} warned that the treat could distort or spill if {child} leaned too far on the steep path.",
        ),
    ]
    if distorted:
        answers.append(
            QAItem(
                question=f"What happened to the treat when curiosity made {child} wobble?",
                answer=f"The top of the treat tilted and became a little distorted, but it did not fall apart.",
            )
        )
    if resolved:
        answers.append(
            QAItem(
                question=f"How did the story end for {child} and the treat?",
                answer=f"{child} learned to be careful, held the treat with both hands, and left the creamery happily.",
            )
        )
    return answers


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a creamery?",
        answer="A creamery is a place where milk and cream are turned into treats like ice cream and other sweet desserts.",
    ),
    QAItem(
        question="What does steep mean when talking about a hill?",
        answer="A steep hill goes up or down quickly, so it can be harder to walk on than a gentle path.",
    ),
    QAItem(
        question="What does curiosity mean?",
        answer="Curiosity is the wish to know more and to ask questions or look closely at things.",
    ),
    QAItem(
        question="What does distort mean?",
        answer="To distort something is to bend it, twist it, or change its shape so it does not look quite right.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(X) :- person(X).
curious(X) :- curiosity(X).
steep_place(P) :- place(P), steep(P).
at_risk(T) :- treat(T), steep_place(_), curiosity(_).

distorts(T) :- treat(T), wobble(T), lean_too_far(_), curiosity(_).

resolved :- child(_), parent(_), treat(_), warning(_), careful_hold(_).
#show child/1.
#show curious/1.
#show steep_place/1.
#show distorts/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("place", "creamery"))
    lines.append(asp.fact("place", "hillside_creamery"))
    lines.append(asp.fact("steep", "hillside_creamery"))
    lines.append(asp.fact("person", "child"))
    lines.append(asp.fact("person", "parent"))
    lines.append(asp.fact("curiosity", "child"))
    lines.append(asp.fact("warning", "parent"))
    lines.append(asp.fact("careful_hold", "child"))
    lines.append(asp.fact("treat", "treat"))
    lines.append(asp.fact("wobble", "treat"))
    lines.append(asp.fact("lean_too_far", "child"))
    return "\n".join(lines)


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show resolved/0."))
    has_resolved = any(sym.name == "resolved" for sym in model)
    py_ok = True
    if not has_resolved:
        py_ok = False
    if py_ok == has_resolved:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    if world.trace_log:
        lines.append("events:")
        for item in world.trace_log:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about curiosity at a creamery.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--treat", choices=TREATS.keys())
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    treat = args.treat or rng.choice(list(TREATS.keys()))
    return StoryParams(name=name, gender=gender, parent=parent, place=place, treat=treat)


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
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print([str(s) for s in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name="Ayla", gender="girl", parent="mother", place="hillside_creamery", treat="vanilla"),
            StoryParams(name="Rowan", gender="boy", parent="father", place="hillside_creamery", treat="berry"),
            StoryParams(name="Mira", gender="girl", parent="mother", place="creamery", treat="honey"),
        ]
        samples = [generate(p) for p in combos]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
