#!/usr/bin/env python3
"""
storyworlds/worlds/protection_humor_friendship_detective_story.py
===================================================================

A small detective-story world about friendship, protection, and a gentle joke
that helps solve the case.

Premise:
- A young detective notices a strange little problem.
- A friend is worried someone will be blamed.
- The detective follows clues, learns the truth, and protects the friend.

State model:
- Physical meters track things like wetness, mess, and guarded objects.
- Emotional memes track worry, trust, relief, and laughter.

The story is intentionally small and constraint-driven:
- Only plausible detective cases are generated.
- The resolution requires a meaningful protective action.
- Humor comes from the clues or the culprit's goofy mistake.
"""

from __future__ import annotations

import argparse
import copy
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
    guarded_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Case:
    id: str
    clue: str
    twist: str
    culprit: str
    mess: str
    protection: str
    protected_object: str
    action: str
    risk: str


@dataclass
class StoryParams:
    case: str
    detective: str
    friend: str
    suspect: str
    seed: Optional[int] = None


@dataclass
class World:
    detective: Entity
    friend: Entity
    suspect: Entity
    object_: Entity
    case: Case
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return copy.deepcopy(self)


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _ensure_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def setup_world(case: Case, detective_name: str, friend_name: str, suspect_name: str) -> World:
    detective = Entity(
        id=detective_name,
        kind="character",
        type="detective",
        label=detective_name,
        traits=["sharp", "curious", "kind"],
        meters={"focus": 1.0},
        memes={"confidence": 1.0, "curiosity": 1.0},
    )
    friend = Entity(
        id=friend_name,
        kind="character",
        type="girl" if friend_name in {"Mia", "Lena", "Nora", "Ivy", "Lily"} else "boy",
        label=friend_name,
        traits=["friendly", "nervous"],
        meters={"worry": 1.0},
        memes={"trust": 1.0, "worry": 1.0},
    )
    suspect = Entity(
        id=suspect_name,
        kind="character",
        type="boy" if suspect_name in {"Ben", "Max", "Owen", "Noah", "Finn"} else "girl",
        label=suspect_name,
        traits=["silly", "messy"],
        meters={"mess": 1.0},
        memes={"hiding": 1.0, "humor": 1.0},
    )
    object_ = Entity(
        id=case.protected_object,
        kind="thing",
        type="thing",
        label=case.protected_object,
        phrase=f"a small {case.protected_object}",
        owner=friend.id,
        caretaker=detective.id,
        guarded_by=detective.id,
        meters={"risk": 1.0},
        memes={"importance": 1.0},
    )
    return World(detective, friend, suspect, object_, case)


def clue_points_to_suspect(world: World) -> bool:
    return _ensure_meter(world.suspect, "mess") >= THRESHOLD


def friend_needs_protection(world: World) -> bool:
    return _ensure_meme(world.friend, "worry") >= THRESHOLD and _ensure_meter(world.object_, "risk") >= THRESHOLD


def predict_harm(world: World) -> bool:
    sim = world.copy()
    sim.object_.meters["risk"] += 1.0
    sim.friend.memes["worry"] += 1.0
    return friend_needs_protection(sim)


def investigate(world: World) -> None:
    world.say(
        f"{world.detective.id} was a little detective who liked tidy clues and tidy endings."
    )
    world.say(
        f"{world.friend.id} came looking worried because {world.case.protected_object} was missing from the shelf."
    )
    world.say(
        f'"I did not take it," {world.friend.id} whispered. '
        f'"Please find it before someone blames me."'
    )
    world.facts["setup"] = True


def follow_clue(world: World) -> None:
    world.para()
    world.say(
        f"{world.detective.id} found a tiny clue: {world.case.clue}."
    )
    world.say(
        f"{world.detective.id} looked at {world.suspect.id}, who was trying very hard to look innocent and not at all sticky."
    )
    world.suspect.meters["mess"] = 1.0
    world.suspect.memes["humor"] += 1.0
    world.detective.memes["curiosity"] += 1.0
    world.facts["clue_seen"] = True


def joke_breaks_tension(world: World) -> None:
    world.say(
        f"Then {world.suspect.id} sneezed and a string of crumbs slid out of {world.suspect.pronoun('possessive')} pocket."
    )
    world.say(
        f"{world.detective.id} blinked, then laughed. "
        f'"That is the least sneaky hiding place I have ever seen," {world.detective.id} said.'
    )
    world.friend.memes["worry"] = max(0.0, world.friend.memes.get("worry", 0.0) - 1.0)
    world.friend.memes["trust"] += 1.0
    world.suspect.memes["humor"] += 1.0
    world.facts["humor"] = True


def reveal_and_protect(world: World) -> None:
    world.para()
    world.say(
        f"{world.suspect.id} pointed to the curtain and admitted the truth: {world.case.twist}."
    )
    world.say(
        f"The missing {world.case.protected_object} was there the whole time, tucked where it would stay {world.case.risk}."
    )
    world.say(
        f"{world.detective.id} put {world.case.protection} over it and said, "
        f'"Now it is protected, and nobody has to worry."'
    )
    world.object_.guarded_by = world.detective.id
    world.object_.meters["risk"] = 0.0
    world.friend.memes["worry"] = 0.0
    world.friend.memes["relief"] = 1.0
    world.detective.memes["satisfaction"] = 1.0
    world.facts["protected"] = True


def end_image(world: World) -> None:
    world.say(
        f"{world.friend.id} smiled again, {world.detective.id} tucked the clue in a notebook, and the whole room felt safe and silly at once."
    )


CASES = {
    "cookie": Case(
        id="cookie",
        clue="a trail of flour footprints crossed the hall",
        twist="the 'thief' only hid it from the rain because a window had been left open",
        culprit="suspect",
        mess="flour",
        protection="a clean bowl",
        protected_object="cookie",
        action="bake",
        risk="dry",
    ),
    "toy": Case(
        id="toy",
        clue="a ribbon was tied around the doorknob like a clue on purpose",
        twist="the suspect had moved the toy to keep a younger sibling from stepping on it",
        culprit="suspect",
        mess="dust",
        protection="a soft blanket",
        protected_object="toy robot",
        action="play",
        risk="safe",
    ),
    "book": Case(
        id="book",
        clue="there was a pawprint on the chair and a feather on the floor",
        twist="the suspect had tucked the book away so the cat could not spill juice on it",
        culprit="suspect",
        mess="ink",
        protection="a little shelf cover",
        protected_object="picture book",
        action="read",
        risk="clean",
    ),
}


def valid_cases() -> list[str]:
    return list(CASES.keys())


GIRL_NAMES = ["Mia", "Lena", "Nora", "Ivy", "Lily"]
BOY_NAMES = ["Ben", "Max", "Owen", "Noah", "Finn"]
DETECTIVE_NAMES = ["Dot", "June", "Rae", "Pip", "Tess"]
SUSPECT_NAMES = ["Ben", "Max", "Owen", "Noah", "Finn", "Milo", "Ava", "Zoe"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about protection, humor, and friendship.")
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--suspect")
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
    case = args.case or rng.choice(valid_cases())
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES + BOY_NAMES)
    suspect_pool = [n for n in SUSPECT_NAMES if n != detective and n != friend]
    suspect = args.suspect or rng.choice(suspect_pool)
    if suspect in {detective, friend}:
        raise StoryError("The suspect must be a different person from the detective and friend.")
    return StoryParams(case=case, detective=detective, friend=friend, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    case = CASES[params.case]
    world = setup_world(case, params.detective, params.friend, params.suspect)
    investigate(world)
    follow_clue(world)
    joke_breaks_tension(world)
    reveal_and_protect(world)
    end_image(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    c = world.case
    return [
        f'Write a short detective story for a small child that includes the word "{c.protected_object}" and the idea of protection.',
        f"Tell a gentle mystery where {world.detective.id} helps {world.friend.id} and learns the truth about {world.case.protected_object}.",
        f"Write a funny friendship story where a detective follows a clue, laughs, and protects something important.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.case
    qa = [
        QAItem(
            question=f"What problem brought {world.friend.id} to {world.detective.id}?",
            answer=f"{world.friend.id} was worried because the {c.protected_object} was missing, and {world.friend.id} feared being blamed.",
        ),
        QAItem(
            question=f"What clue helped {world.detective.id} start solving the mystery?",
            answer=f"{world.detective.id} noticed {c.clue}. That clue pointed toward {world.suspect.id}.",
        ),
        QAItem(
            question=f"How did the story stay friendly instead of scary?",
            answer=f"{world.detective.id} listened kindly, laughed at the silly hiding place, and helped {world.friend.id} feel safe again.",
        ),
        QAItem(
            question=f"What did {world.detective.id} do to protect the important thing at the end?",
            answer=f"{world.detective.id} put {c.protection} over the {c.protected_object} so it would stay protected.",
        ),
    ]
    if world.facts.get("humor"):
        qa.append(
            QAItem(
                question=f"What made {world.detective.id} laugh during the case?",
                answer=f"{world.suspect.id} had a very silly hiding place, and crumbs slipped out in a funny way.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why do friends help each other in stories?",
            answer="Friends help each other because they care, share worries, and make hard problems feel smaller.",
        ),
        QAItem(
            question="What is protection?",
            answer="Protection means keeping someone or something safe from harm, mess, or trouble.",
        ),
        QAItem(
            question="Why can humor help in a mystery?",
            answer="Humor can make people relax and think more clearly, especially when a problem feels tense.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in [world.detective, world.friend, world.suspect, world.object_]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.guarded_by:
            bits.append(f"guarded_by={ent.guarded_by}")
        lines.append(f"{ent.id}: {', '.join(bits) if bits else 'quiet'}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_case/1.

valid_case(cookie) :- case(cookie).
valid_case(toy) :- case(toy).
valid_case(book) :- case(book).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/1."))
    return sorted({args[0] for args in asp.atoms(model, "valid_case")})


def asp_verify() -> int:
    py = set(valid_cases())
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} cases.")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_valid_cases()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for case in valid_cases():
            params = StoryParams(
                case=case,
                detective=DETECTIVE_NAMES[0],
                friend=GIRL_NAMES[0],
                suspect=SUSPECT_NAMES[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
