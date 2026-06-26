#!/usr/bin/env python3
"""
A small fairy-tale story world: a dude, a beetle, and a warning about the noggin.

This world models a simple cautionary fairy tale with foreshadowing and a
transformation turn. A curious dude ignores a beetle's warning, bops his noggin,
and learns a gentler way to act. The story is driven by state changes in a tiny
simulated world, not by a fixed paragraph template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dude", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    warning: str
    consequence: str
    change: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Curse:
    id: str
    label: str
    phrase: str
    target: str
    trigger: str
    transform_to: str
    antidote: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "grove": Setting(place="the moonlit grove", affords={"peek", "taunt", "tip"}),
    "tower": Setting(place="the old tower", affords={"peek", "taunt", "tip"}),
    "brook": Setting(place="the silver brook", affords={"peek", "taunt", "tip"}),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        verb="peek into the hollow log",
        gerund="peeking into hollows",
        rush="lean closer to the hollow log",
        warning="the dark in the log looked sleepy but not empty",
        consequence="a tumble and a rude bump",
        change="learn caution",
        tags={"foreshadowing", "cautionary"},
    ),
    "taunt": Action(
        id="taunt",
        verb="taunt the strange beetle",
        gerund="mocking the beetle",
        rush="snatch at the beetle's shiny shell",
        warning="the beetle's shell flashed like a tiny shield",
        consequence="a spell and a sudden swap",
        change="learn kindness",
        tags={"foreshadowing", "cautionary", "transformation"},
    ),
    "tip": Action(
        id="tip",
        verb="tip the lantern toward the roots",
        gerund="tipping lanterns toward roots",
        rush="raise the lantern high",
        warning="the roots were braided like hidden fingers",
        consequence="a misstep and a wandering spell",
        change="learn steadiness",
        tags={"foreshadowing", "cautionary", "transformation"},
    ),
}

CURSES = {
    "beetle_spell": Curse(
        id="beetle_spell",
        label="beetle charm",
        phrase="a beetle charm that glittered like a warning star",
        target="dude",
        trigger="taunt",
        transform_to="beetle",
        antidote="apologize",
        tags={"transformation", "cautionary"},
    ),
    "noggin_bump": Curse(
        id="noggin_bump",
        label="noggin bump",
        phrase="a bump to the noggin",
        target="dude",
        trigger="peek",
        transform_to="dizzy",
        antidote="rest",
        tags={"foreshadowing", "cautionary"},
    ),
}

DUDE_NAMES = ["Otto", "Bram", "Eli", "Milo", "Gus", "Tobin"]
TONE_WORDS = ["careful", "curious", "silly", "proud", "hasty", "gentle"]


def _apply_peek(world: World, dude: Entity, action: Action) -> None:
    if ("peek", dude.id) in world.fired:
        return
    world.fired.add(("peek", dude.id))
    dude.memes["curiosity"] = dude.memes.get("curiosity", 0) + 1
    world.say(
        f"At {world.setting.place}, {dude.id} was a curious fellow who liked to test every shadow."
    )
    world.say(
        f"Before anything went wrong, {ACTIONS['peek'].warning}; the beetle had already vanished under the roots."
    )
    world.say(
        f"{dude.id} still tried to {action.rush}, and the stone slipped under {dude.pronoun('possessive')} boot."
    )
    dude.meters["noggin_bump"] = dude.meters.get("noggin_bump", 0) + 1
    world.say(
        f"{dude.pronoun('possessive').capitalize()} noggin met the edge of the log with a sorry bonk."
    )


def _apply_taunt(world: World, dude: Entity, action: Action) -> None:
    if ("taunt", dude.id) in world.fired:
        return
    world.fired.add(("taunt", dude.id))
    beetle = world.get("beetle")
    beetle.memes["worry"] = beetle.memes.get("worry", 0) + 1
    world.say(
        f"A little beetle with a bright shell watched from a fern, as if it knew a lesson was coming."
    )
    world.say(
        f"{dude.id} laughed and tried to {action.rush}, but the beetle's shell flashed like a warning coin."
    )
    world.say(
        f"The beetle gave one tiny shake, and a spell curled through the moss."
    )
    dude.type = "beetle"
    dude.label = "a beetle-sized dude"
    dude.memes["shame"] = dude.memes.get("shame", 0) + 1
    dude.memes["humbled"] = dude.memes.get("humbled", 0) + 1
    world.say(
        f"In a blink, {dude.id} was changed into a beetle-sized fellow with a beetle's busy legs."
    )


def _apply_tip(world: World, dude: Entity, action: Action) -> None:
    if ("tip", dude.id) in world.fired:
        return
    world.fired.add(("tip", dude.id))
    world.say(
        f"At the silver brook, the roots looked braided and sly, just as the beetle had seemed to promise."
    )
    world.say(
        f"{dude.id} lifted the lantern too high and missed a root; the lantern wobbled, and so did {dude.pronoun('subject')}."
    )
    dude.memes["caution"] = dude.memes.get("caution", 0) + 1
    dude.meters["unsteady"] = dude.meters.get("unsteady", 0) + 1
    world.say(
        f"Only then did {dude.id} see that the warning had been kind all along."
    )


def tell(setting: Setting, action: Action, curse: Curse, name: str) -> World:
    world = World(setting)
    dude = world.add(Entity(id=name, kind="character", type="dude", label="dude"))
    beetle = world.add(Entity(id="beetle", kind="character", type="beetle", label="beetle"))
    world.facts["action"] = action
    world.facts["curse"] = curse
    world.facts["dude"] = dude
    world.facts["beetle"] = beetle

    world.say(
        f"Once in a moonlit grove lived {dude.id}, a proud dude with a restless noggin and a nose for trouble."
    )
    world.say(
        f"He had heard old tales that a beetle could be a warning in a shiny shell, but he only smiled."
    )

    world.para()
    if action.id == "peek":
        _apply_peek(world, dude, action)
        world.para()
        world.say(
            f"{dude.id} sat still while the dizziness passed, and the grove seemed softer after the blow."
        )
        world.say(
            f"From then on, {dude.id} took slow steps, because a bruised noggin can teach a sharp lesson."
        )
    elif action.id == "taunt":
        _apply_taunt(world, dude, action)
        world.para()
        world.say(
            f"The transformed dude bowed to the beetle and said sorry in a whisper as small as a leaf curl."
        )
        world.say(
            f"The spell lifted at once, and {dude.id} became a human again, wiser and much less boastful."
        )
    else:
        _apply_tip(world, dude, action)
        world.para()
        world.say(
            f"He set the lantern down and walked home with both hands free, remembering the beetle's warning shine."
        )
        world.say(
            f"The next evening, {dude.id} chose patience over pride, and the grove kept its secret safely."
        )

    world.facts["resolved"] = True
    return world


def build_story(world: World) -> str:
    return world.render()


def qa_story(world: World) -> list[QAItem]:
    dude = world.facts["dude"]
    action = world.facts["action"]
    curse = world.facts["curse"]
    qa = [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {dude.id}, a curious dude who had to learn a careful lesson.",
        ),
        QAItem(
            question=f"What did {dude.id} try to do?",
            answer=f"{dude.id} tried to {action.verb}, which was not a safe idea.",
        ),
        QAItem(
            question=f"What warning showed up before the trouble?",
            answer=f"The beetle and the dark place both foreshadowed trouble, because the story warned that something was waiting there.",
        ),
        QAItem(
            question=f"What changed in the middle of the story?",
            answer=f"A transformation happened: the beetle spell changed {dude.id} into a beetle-sized fellow for a moment, and that made the lesson impossible to ignore.",
        ),
        QAItem(
            question=f"What lesson did {dude.id} learn?",
            answer=f"{dude.id} learned a cautionary lesson: when a warning seems small, it may still keep you safe if you listen to it.",
        ),
    ]
    if curse.transform_to == "beetle":
        qa.append(
            QAItem(
                question=f"Why did the beetle spell matter?",
                answer=f"It mattered because the beetle charm turned pride into humility and showed {dude.id} that mocking a warning can lead to a bad surprise.",
            )
        )
    return qa


def qa_world(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beetle?",
            answer="A beetle is a small insect with a hard shell.",
        ),
        QAItem(
            question="What is a noggin?",
            answer="A noggin is a funny word for a head.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a little hint about trouble or change before it happens.",
        ),
        QAItem(
            question="What does transformation mean in a fairy tale?",
            answer="Transformation means something changes into something else, often by magic.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means the story teaches you to be careful and learn from a mistake.",
        ),
    ]


def prompts(world: World) -> list[str]:
    action = world.facts["action"]
    return [
        f"Write a short fairy tale about a dude, a beetle, and a warning in the woods that ends with a lesson about {action.id}.",
        f"Tell a child-friendly story where {world.facts['dude'].id} ignores a beetle's hint and learns a cautionary lesson.",
        f"Write a fairy tale with foreshadowing, transformation, and a gentle ending image about a mischievous dude and his noggin.",
    ]


def generation_params() -> list[str]:
    return list(SETTINGS)


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: dude, noggin, beetle.")
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    name = args.name or rng.choice(DUDE_NAMES)
    return StoryParams(place=place, action=action, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], CURSE, params.name)
    return StorySample(
        params=params,
        story=build_story(world),
        prompts=prompts(world),
        story_qa=qa_story(world),
        world_qa=qa_world(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(sample: StorySample) -> str:
    world = sample.world
    if world is None:
        return ""
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
% A tale is valid when it has a place, a dude, a beetle, and one of the
% cautionary fairy-tale turns.
place(grove). place(tower). place(brook).
action(peek). action(taunt). action(tip).

foreshadows(peek).
foreshadows(taunt).
foreshadows(tip).

transforms(taunt).

cautionary(peek).
cautionary(taunt).
cautionary(tip).

valid_story(P,A) :- place(P), action(A), foreshadows(A), cautionary(A).
has_transformation(A) :- transforms(A).
#show valid_story/2.
#show has_transformation/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for a in ACTIONS:
        lines.append(asp.fact("foreshadows", a))
        lines.append(asp.fact("cautionary", a))
    lines.append(asp.fact("transforms", "taunt"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, a) for p in SETTINGS for a in ACTIONS}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: ASP matches Python for {len(cl)} story shapes.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show has_transformation/1."))
        return
    if args.asp:
        for p, a in asp_valid():
            print(p, a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for action in ACTIONS:
                params = StoryParams(place=place, action=action, name=random.choice(DUDE_NAMES))
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
