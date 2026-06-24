#!/usr/bin/env python3
"""A small detective-story world with a bad ending.

A child-friendly detective notices a strange thunk, follows clues, and tries to
restore accord between two friends or neighbors. The twist is that the final
choice goes wrong: the clue is misread, the wrong person is blamed, and the
ending leaves the neighborhood feeling off-balance.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # detective | suspect | witness | thing
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"detective", "suspect", "witness"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the little station"
    clue_place: str = "the alley"
    object_name: str = "tin box"
    sound: str = "thunk"
    accord_word: str = "accord"


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    detective_name: str
    suspect_name: str
    witness_name: str
    place: str = "the little station"
    clue_place: str = "the alley"
    sound: str = "thunk"
    object_name: str = "tin box"
    seed: Optional[int] = None


PLACES = {
    "the little station": Scene(place="the little station", clue_place="the alley", object_name="tin box", sound="thunk", accord_word="accord"),
    "the market corner": Scene(place="the market corner", clue_place="the stairwell", object_name="wooden crate", sound="thunk", accord_word="accord"),
    "the school yard": Scene(place="the school yard", clue_place="the shed", object_name="lunch pail", sound="thunk", accord_word="accord"),
}

DETECTIVE_NAMES = ["Mina", "Noel", "Tess", "Ivy", "Rowan", "Pip", "June", "Eli"]
SUSPECT_NAMES = ["Mr. Bell", "Aunt Ora", "Benji", "Nina", "Coach Sam", "Mrs. Lane"]
WITNESS_NAMES = ["Lulu", "Omar", "Ria", "Tom", "Mila", "Jae"]


ASP_RULES = r"""
place(P) :- place_name(P).
clue(C) :- clue_name(C).
sound(S) :- sound_name(S).
object(O) :- object_name(O).

heard_thunk(D) :- detective(D), sound(S), thunk_sound(S), hears(D, S).
has_clue(D) :- heard_thunk(D), clue_found(D).
bad_ending :- wrong_blame.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    lines.append(asp.fact("sound_name", "thunk"))
    lines.append(asp.fact("thunk_sound", "thunk"))
    for obj in {s.object_name for s in PLACES.values()}:
        lines.append(asp.fact("object_name", obj))
    for c in {s.clue_place for s in PLACES.values()}:
        lines.append(asp.fact("clue_name", c))
    lines.append(asp.fact("detective", "detective"))
    lines.append(asp.fact("hears", "detective", "thunk"))
    lines.append(asp.fact("clue_found", "detective"))
    lines.append(asp.fact("wrong_blame"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show bad_ending/0."))
    atoms = {str(a) for a in model}
    ok = "bad_ending" in atoms
    if ok:
        print("OK: ASP model confirms the bad ending.")
        return 0
    print("MISMATCH: ASP did not produce the expected bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--detective-name")
    ap.add_argument("--suspect-name")
    ap.add_argument("--witness-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    suspect_name = args.suspect_name or rng.choice(SUSPECT_NAMES)
    witness_name = args.witness_name or rng.choice(WITNESS_NAMES)
    if detective_name == suspect_name:
        raise StoryError("The detective and suspect must be different people.")
    if detective_name == witness_name or suspect_name == witness_name:
        raise StoryError("The witness must be a different person from the detective and suspect.")
    return StoryParams(
        detective_name=detective_name,
        suspect_name=suspect_name,
        witness_name=witness_name,
        place=scene.place,
        clue_place=scene.clue_place,
        sound=scene.sound,
        object_name=scene.object_name,
    )


def _build_world(params: StoryParams) -> World:
    scene = PLACES[params.place]
    world = World(scene)
    det = world.add(Entity(id="det", kind="detective", label=params.detective_name, role="detective"))
    sus = world.add(Entity(id="sus", kind="suspect", label=params.suspect_name, role="suspect"))
    wit = world.add(Entity(id="wit", kind="witness", label=params.witness_name, role="witness"))

    det.memes["curious"] = 1
    det.memes["hope"] = 1
    sus.memes["nervous"] = 1
    wit.memes["uneasy"] = 1

    world.say(f"{det.label} was a small detective at {scene.place}, and {det.pronoun('subject')} liked neat clues and quiet maps.")
    world.say(f"One evening, {det.label} heard a soft {scene.sound} from {scene.clue_place}, where a {scene.object_name} sat in the dark.")
    world.say(f"{det.label} wanted to keep the town in {scene.accord_word}, so {det.pronoun('subject')} followed the sound.")

    world.para()
    world.say(f"At {scene.clue_place}, {wit.label} pointed at the {scene.object_name} and said it had rolled there after a bump.")
    world.say(f"{sus.label} stood nearby, looking worried, and {det.label} thought the worry itself was a clue.")
    world.say(f"{det.label} asked careful questions, but the answers came out mixed, like footprints in wet paint.")

    world.para()
    world.say(f"Then {det.label} found a shiny button under a bench and decided it must belong to {sus.label}.")
    world.say(f"{det.label} announced the answer too fast, and the nice plan for {scene.accord_word} began to crack.")
    world.say(f"In the end, the button came from {wit.label}'s coat, not from the suspect at all.")
    world.say(f"{sus.label} walked away hurt, {wit.label} looked ashamed, and the little station felt less peaceful than before.")
    world.say(f"{det.label} had solved the sound of the {scene.sound}, but not the trouble it caused.")

    world.facts.update(
        detective=det,
        suspect=sus,
        witness=wit,
        place=scene.place,
        clue_place=scene.clue_place,
        object_name=scene.object_name,
        sound=scene.sound,
        accord_word=scene.accord_word,
        wrong_blame=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    wit = f["witness"]
    return [
        f"Write a short detective story for a young child that includes the word '{f['sound']}' and ends badly.",
        f"Tell a story where {det.label} tries to keep {f['accord_word']} at {f['place']}, but the clue from {f['clue_place']} is misunderstood.",
        f"Write a gentle mystery about {det.label}, {sus.label}, and {wit.label} with a clear clue, a mistake, and a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    wit = f["witness"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det.label}. {det.label} listened for clues and tried to keep things calm.",
        ),
        QAItem(
            question=f"What sound started the mystery?",
            answer=f"The mystery started with a soft {f['sound']} from {f['clue_place']}. That sound led {det.label} to look closer.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {det.label} blamed {sus.label} too quickly, but the button really belonged to {wit.label}. That mistake hurt feelings and broke the accord.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is an accord?",
            answer="Accord means people are getting along and agreeing with one another.",
        ),
        QAItem(
            question="What does thunk sound like?",
            answer="Thunk is a short, heavy sound, like something small bumping or falling onto wood or stone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} role={e.role} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams("Mina", "Mr. Bell", "Lulu", place="the little station", clue_place="the alley", sound="thunk", object_name="tin box"),
    StoryParams("Tess", "Aunt Ora", "Omar", place="the market corner", clue_place="the stairwell", sound="thunk", object_name="wooden crate"),
    StoryParams("Ivy", "Mrs. Lane", "Ria", place="the school yard", clue_place="the shed", sound="thunk", object_name="lunch pail"),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show bad_ending/0."))
        print("bad ending atoms:", asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
