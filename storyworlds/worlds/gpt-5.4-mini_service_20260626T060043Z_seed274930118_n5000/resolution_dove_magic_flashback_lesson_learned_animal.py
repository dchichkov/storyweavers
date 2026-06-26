#!/usr/bin/env python3
"""
Story world: a small Animal Story about a dove, a bit of Magic, a Flashback,
and a clear Lesson Learned.

The premise is deliberately simple: a gentle dove wants to help, magic makes
the problem a little stranger, a flashback explains why the dove cares so much,
and the ending proves the lesson through a changed world state.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Animal:
    id: str
    species: str
    label: str
    phrase: str
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hope": 0.0, "curiosity": 0.0, "kindness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.id


@dataclass
class Place:
    name: str
    detail: str
    kind: str = "outdoors"


@dataclass
class Magic:
    name: str
    effect: str
    risk: str
    helpful: str


@dataclass
class Problem:
    missing: str
    frightened_of: str
    caused_by: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Animal] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.flashback_used = False
        self.lesson_used = False
        self.magic_used = False

    def add(self, animal: Animal) -> Animal:
        self.entities[animal.id] = animal
        return animal

    def get(self, eid: str) -> Animal:
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.flashback_used = self.flashback_used
        w.lesson_used = self.lesson_used
        w.magic_used = self.magic_used
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place(name="the meadow", detail="soft grass swayed under a bright sky"),
    "pond": Place(name="the pond", detail="the water shone like a silver mirror"),
    "tree": Place(name="the old tree", detail="its branches made a round, leafy home"),
}

MAGICS = {
    "glow": Magic(
        name="glow",
        effect="the moon-spark glow made tiny feathers shine",
        risk="it could startle shy birds",
        helpful="it could help a lost friend find the way",
    ),
    "wind": Magic(
        name="wind",
        effect="a warm magic wind could carry a small note across the field",
        risk="it could blow things out of reach",
        helpful="it could deliver a message quickly",
    ),
    "sparkle": Magic(
        name="sparkle",
        effect="a glittering spell could hide a clue in plain sight",
        risk="it could make the wrong thing look special",
        helpful="it could reveal where care was needed",
    ),
}

PROBLEMS = {
    "lost_note": Problem(
        missing="a lost note",
        frightened_of="that the note would never reach its friend",
        caused_by="a gust that blew it into the reeds",
    ),
    "sad_chick": Problem(
        missing="a sad chick",
        frightened_of="that the chick would stay lonely",
        caused_by="a misunderstanding after a game of tag",
    ),
    "stuck_feather": Problem(
        missing="a stuck feather",
        frightened_of="that the feather would never come loose",
        caused_by="a sticky berry patch",
    ),
}

DOVE_NAMES = ["Daisy", "Milo", "Pip", "Luna", "Snow", "Tiko"]
OTHER_NAMES = ["Fin", "Moss", "Nina", "Beck", "Wren", "Clover"]
TRAITS = ["gentle", "curious", "brave", "patient", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    magic: str
    problem: str
    dove_name: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

class StoryWorld:
    def __init__(self, place: Place, magic: Magic, problem: Problem) -> None:
        self.place = place
        self.magic = magic
        self.problem = problem
        self.world = World(place)
        self.dove = self.world.add(
            Animal(
                id="dove",
                species="dove",
                label="a white dove",
                phrase="a small white dove with bright eyes",
                role="helper",
                traits=["gentle", "watchful"],
            )
        )
        self.friend = self.world.add(
            Animal(
                id="friend",
                species="bird",
                label="a little friend",
                phrase="a little bird friend",
                role="friend",
                traits=["small", "shy"],
            )
        )
        self.world.magic_used = False

    def intro(self) -> None:
        self.world.say(
            f"{self.dove.name} was {self.dove.phrase}, and {self.place.detail}."
        )
        self.dove.memes["joy"] += 1
        self.dove.memes["kindness"] += 1
        self.world.say(
            f"{self.dove.name} liked helping other birds, because {self.dove.name} "
            f"wanted every day to feel safe and warm."
        )

    def problem_setup(self) -> None:
        self.friend.memes["worry"] += 1
        self.world.say(
            f"One day, {self.friend.name} faced {self.problem.missing} and felt sad, "
            f"because {self.problem.caused_by}."
        )
        self.world.say(
            f"{self.friend.name} worried {self.problem.frightened_of}."
        )

    def flashback(self) -> None:
        self.world.flashback_used = True
        self.dove.memes["curiosity"] += 1
        self.world.para()
        self.world.say(
            f"Flashback: {self.dove.name} remembered a tiny day long ago."
        )
        self.world.say(
            f"Back then, a lost sparrow had waited in silence until a kind friend "
            f"shared a path home."
        )
        self.world.say(
            f"{self.dove.name} had learned that small help could turn worry into hope."
        )

    def use_magic(self) -> None:
        self.world.magic_used = True
        self.dove.meters["distance"] += 1
        self.dove.memes["hope"] += 1
        self.world.para()
        self.world.say(
            f"Then {self.dove.name} tried {self.magic.name} magic."
        )
        self.world.say(self.magic.effect + ".")
        self.world.say(
            f"It was a little risky, because {self.magic.risk}, but {self.magic.helpful}."
        )

    def resolve(self) -> None:
        self.world.para()
        self.friend.memes["worry"] = 0.0
        self.friend.memes["joy"] += 1
        self.dove.memes["joy"] += 1
        self.dove.memes["kindness"] += 1
        self.world.lesson_used = True
        self.world.say(
            f"The magic found {self.problem.missing}, and {self.dove.name} gently "
            f"gave it back to {self.friend.name}."
        )
        self.world.say(
            f"{self.friend.name} smiled, because the problem was no longer scary."
        )
        self.world.say(
            f"Lesson learned: when a friend is scared, a calm helper, a careful plan, "
            f"and a little magic can make things right."
        )
        self.world.say(
            f"At the end, {self.dove.name} stood beside {self.friend.name} under "
            f"the open sky, and both birds felt safe."
        )


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for magic in MAGICS:
            for problem in PROBLEMS:
                combos.append((place, magic, problem))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,R) :- place(P), magic(M), problem(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world about a dove, magic, flashback, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, magic, problem = rng.choice(sorted(combos))
    dove_name = args.name or rng.choice(DOVE_NAMES)
    friend_name = args.friend or rng.choice(OTHER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, problem=problem, dove_name=dove_name, friend_name=friend_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    sw = StoryWorld(PLACES[params.place], MAGICS[params.magic], PROBLEMS[params.problem])
    sw.dove.id = params.dove_name
    sw.dove.label = f"a white dove named {params.dove_name}"
    sw.dove.phrase = f"a small white dove named {params.dove_name}"
    sw.friend.id = params.friend_name
    sw.friend.label = f"a little friend named {params.friend_name}"
    sw.friend.phrase = f"a little bird named {params.friend_name}"
    sw.friend.traits.append(params.trait)

    sw.intro()
    sw.problem_setup()
    sw.flashback()
    sw.use_magic()
    sw.resolve()

    world = sw.world
    world.facts = {
        "params": params,
        "dove_name": params.dove_name,
        "friend_name": params.friend_name,
        "trait": params.trait,
        "place": params.place,
        "magic": params.magic,
        "problem": params.problem,
        "magic_used": world.magic_used,
        "flashback_used": world.flashback_used,
        "lesson_used": world.lesson_used,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story for a young child about a dove, "{f["magic"]}" magic, and a lesson learned.',
        f"Tell a short story where {f['dove_name']} the dove helps {f['friend_name']} after a problem, then remembers a flashback and makes a careful choice.",
        f'Write a child-friendly story that includes the words "Magic", "Flashback", and "Lesson Learned" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {f['dove_name']}, a gentle dove who wants to help a friend.",
        ),
        QAItem(
            question=f"What happened in the flashback?",
            answer=f"In the flashback, {f['dove_name']} remembered a lost sparrow and learned that kind help can lead a scared bird home.",
        ),
        QAItem(
            question=f"What was the lesson learned?",
            answer="The lesson learned was that calm help, careful choices, and a little magic can solve a problem without making anyone feel worse.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {f['dove_name']} giving help to {f['friend_name']}, so both birds felt safe and happy under the open sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dove?",
            answer="A dove is a small bird. Doves often look gentle and can be seen as peaceful helpers in stories.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that goes back to an earlier time to explain something important.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something important that changes how you act later.",
        ),
        QAItem(
            question="Why can magic be useful in a story?",
            answer="Magic can help solve a problem in a surprising way, but good stories still show careful choices and clear results.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: species={e.species} memes={dict(e.memes)} meters={dict(e.meters)}")
    lines.append(f"flags: magic_used={world.magic_used} flashback_used={world.flashback_used} lesson_used={world.lesson_used}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", magic="glow", problem="lost_note", dove_name="Daisy", friend_name="Pip", trait="gentle"),
    StoryParams(place="pond", magic="wind", problem="sad_chick", dove_name="Milo", friend_name="Nina", trait="kind"),
    StoryParams(place="tree", magic="sparkle", problem="stuck_feather", dove_name="Luna", friend_name="Clover", trait="patient"),
]


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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos")
        for t in sorted(set(asp.atoms(model, "valid"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
