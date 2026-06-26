#!/usr/bin/env python3
"""
storyworlds/worlds/slurp_hallmnopqrstuv_bus_depot_curiosity_conflict_repetition.py
===================================================================================

A small folk-tale storyworld set in a bus depot, built around curiosity,
conflict, and repetition.

Premise:
A curious child at a busy bus depot keeps hearing a strange slurp from an
oddly named hallmnopqrstuv corridor. The child wants to follow it, but a
caregiver worries the place is not safe and keeps saying no.

World model:
- Curiosity grows when the child notices the slurp again and again.
- Repetition strengthens a loop: every time the sound returns, curiosity rises.
- Conflict grows when the child disobeys or argues.
- Resolution comes when the caregiver turns the repeated sound into a shared
  search, revealing a harmless cause and calming the conflict.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bus depot"
    hall: str = "hallmnopqrstuv"
    indoors: bool = True


@dataclass
class StoryParams:
    name: str = "Mira"
    gender: str = "girl"
    parent: str = "grandmother"
    trait: str = "curious"
    seed: Optional[int] = None


@dataclass
class SoundEvent:
    keyword: str = "slurp"
    place_hint: str = "hallmnopqrstuv"
    cause: str = "a leaky cup under a bench"
    result: str = "the puddle was harmless"


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    sound = world.facts.get("sound")
    if not isinstance(sound, SoundEvent):
        return out
    if child.memes.get("heard_slurp", 0.0) < THRESHOLD:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    out.append(f"The slurp came again, and the child's curiosity grew stronger.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if parent.memes.get("warning", 0.0) < THRESHOLD:
        return out
    if child.memes.get("defiance", 0.0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0
    out.append("The child and the caretaker fell into a fretful conflict.")
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    sound = world.facts.get("sound")
    if not isinstance(sound, SoundEvent):
        return out
    if child.memes.get("conflict", 0.0) < THRESHOLD:
        return out
    if parent.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("resolution",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    out.append(f"They followed the slurp together and found that {sound.result}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_repetition, _r_conflict, _r_resolution):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"feet": 0.0},
        memes={"curiosity": 0.0, "joy": 0.0, "conflict": 0.0, "heard_slurp": 0.0, "defiance": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        memes={"warning": 0.0, "kindness": 0.0},
    ))
    sound = SoundEvent()
    world.facts["sound"] = sound

    # Act I: setup.
    world.say(
        f"At the bus depot, little {params.name} was as curious as a sparrow in a barn."
    )
    world.say(
        f"Near the {setting.hall}, the air kept making a soft {sound.keyword}, "
        f"as if a secret had a slippery tongue."
    )
    world.say(
        f"{params.name} listened again and again, because folk tales always teach that some sounds ask to be followed."
    )

    # Act II: tension.
    world.para()
    child.memes["heard_slurp"] += 1.0
    child.memes["curiosity"] += 1.0
    parent.memes["warning"] += 1.0
    parent.memes["kindness"] += 1.0
    world.say(
        f"{params.name} wanted to walk toward the {setting.hall}, but the caretaker lifted a hand and said, "
        f'"No little one, not alone at the bus depot."'
    )
    world.say(
        f"{params.name} heard the warning, yet the {sound.keyword} came back from the corridor, and curiosity tugged harder."
    )
    child.memes["defiance"] += 1.0
    world.say(
        f"So {params.name} took one small step, then another, and the air seemed to repeat the same slippery note."
    )
    propagate(world, narrate=True)

    # Act III: resolution.
    world.para()
    world.say(
        f"The caretaker did not scold. Instead, {params.parent} walked beside {params.name} and listened carefully."
    )
    world.say(
        f"Together they followed the repeated {sound.keyword} to the {setting.hall}, where the sound had a humble cause."
    )
    propagate(world, narrate=True)
    world.say(
        f"At last they smiled, because the strange little mystery was only {sound.cause}, and the bus depot felt safe again."
    )

    world.facts.update(child=child, parent=parent, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a folk-tale style story about a curious child named {p.name} at a bus depot who keeps hearing a slurp from hallmnopqrstuv.",
        f"Tell a gentle story where curiosity causes conflict, but repetition helps the child and caretaker solve the slurp mystery.",
        f"Write a small child-facing story set in a bus depot with the words slurp and hallmnopqrstuv, ending in a safe discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    sound = world.facts["sound"]
    return [
        QAItem(
            question=f"Where was {p.name} when the slurp sound kept coming back?",
            answer=f"{p.name} was at the bus depot, near the {world.setting.hall}, where the slurp kept returning.",
        ),
        QAItem(
            question=f"Why did {p.name} feel torn between listening and obeying?",
            answer=f"{p.name} felt curious about the slurp, but {parent.label} warned {child.pronoun('object')} not to go alone, so curiosity and conflict pulled in different directions.",
        ),
        QAItem(
            question=f"What did the repeated slurp help the grown-up notice?",
            answer=f"The repeated slurp helped the grown-up notice that the sound had a simple cause, {sound.cause}.",
        ),
        QAItem(
            question=f"How did the story end for {p.name} and the caretaker?",
            answer=f"They followed the slurp together, found that it was harmless, and left the bus depot calm and safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, look closer, and ask questions.",
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict is a struggle or disagreement that makes the characters worry or argue before things are fixed.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means something happens again and again, which can make a pattern easy to notice.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, wait, and get ready for the next trip.",
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about slurp, curiosity, conflict, and repetition at a bus depot.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"], default=None)
    ap.add_argument("--trait", default=None)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name_choices = ["Mira", "Tavi", "Nina", "Poe", "Lena", "Bram", "Suri", "Arlo"]
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(["curious", "careful", "bright-eyed", "gentle"])
    name = args.name or rng.choice(name_choices)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
#show valid/1.

curiosity(child).
conflict(child).
repetition(sound).

valid(bus_depot) :- curiosity(child), conflict(child), repetition(sound).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "bus_depot"),
        asp.fact("place", "hallmnopqrstuv"),
        asp.fact("keyword", "slurp"),
        asp.fact("theme", "curiosity"),
        asp.fact("theme", "conflict"),
        asp.fact("theme", "repetition"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid/1."))
    from_model = sorted(set(asp.atoms(model, "valid")))
    python_valid = [("bus_depot",)]
    if from_model == python_valid:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", from_model)
    print("PY :", python_valid)
    return 1


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
    StoryParams(name="Mira", gender="girl", parent="grandmother", trait="curious"),
    StoryParams(name="Tavi", gender="boy", parent="father", trait="careful"),
    StoryParams(name="Suri", gender="girl", parent="mother", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
