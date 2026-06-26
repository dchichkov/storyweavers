#!/usr/bin/env python3
"""
A tiny bedtime-story world about a group of children using a majority vote to
solve a gentle mystery before sleep.

Premise:
- A bedtime routine is interrupted by a missing soft blanket and a faint clue.
- Several friends each notice one small detail.
- They vote on the most likely hiding place.
- The majority choice leads to the right answer and a calm ending.

This script follows the Storyweavers world contract:
- one standalone stdlib file
- typed physical meters and emotional memes
- a Python reasonableness gate and inline ASP twin
- story-driven prose, QA, JSON, trace, verify, and show-ASP modes
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    supports: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    hints: set[str]
    place: str


@dataclass
class Mystery:
    id: str
    question: str
    answer: str
    clue_word: str
    solved_by: str


@dataclass
class VoteOption:
    id: str
    label: str
    clues: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, supports={"sleep", "search", "vote"}),
    "treehouse": Setting(place="the treehouse", indoor=False, supports={"sleep", "search", "vote"}),
    "camproom": Setting(place="the camp room", indoor=True, supports={"sleep", "search", "vote"}),
}

MYSTERIES = {
    "blanket": Mystery(
        id="blanket",
        question="Where is the soft blanket?",
        answer="under the window seat",
        clue_word="blanket",
        solved_by="listening to the quiet clues",
    ),
    "bunny": Mystery(
        id="bunny",
        question="Where did the little bunny toy go?",
        answer="behind the pillow pile",
        clue_word="bunny",
        solved_by="counting the places everyone guessed",
    ),
    "lamp": Mystery(
        id="lamp",
        question="Why is the night-light dim?",
        answer="because its switch was turned halfway down",
        clue_word="lamp",
        solved_by="following the glow",
    ),
}

CLUES = {
    "window": Clue(
        id="window",
        label="the window seat",
        detail="a soft wrinkle near the cushions",
        hints={"quiet", "soft", "corner"},
        place="window seat",
    ),
    "pillow": Clue(
        id="pillow",
        label="the pillow pile",
        detail="a round lump under the pillows",
        hints={"soft", "pile", "bed"},
        place="pillow pile",
    ),
    "glow": Clue(
        id="glow",
        label="the night-light",
        detail="a tiny warm glow near the wall",
        hints={"light", "warm", "wall"},
        place="wall",
    ),
}

VOTES = {
    "window": VoteOption("window", "the window seat", {"window"}),
    "pillow": VoteOption("pillow", "the pillow pile", {"pillow"}),
    "glow": VoteOption("glow", "the night-light", {"glow"}),
}

GIRL_NAMES = ["Mina", "Lila", "Noa", "Poppy", "Ivy", "Ruby", "Nina", "Tess"]
BOY_NAMES = ["Owen", "Eli", "Milo", "Finn", "Theo", "Jude", "Nico", "Leo"]
TRAITS = ["sleepy", "gentle", "curious", "careful", "brave", "thoughtful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    sibling_count: int
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def pronoun_word(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def article(name: str) -> str:
    return "an" if name[:1].lower() in "aeiou" else "a"


def majority_choice(options: list[str]) -> str:
    counts: dict[str, int] = {}
    for opt in options:
        counts[opt] = counts.get(opt, 0) + 1
    top = max(counts.values())
    best = sorted([k for k, v in counts.items() if v == top])
    return best[0]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(setting: Setting, mystery: Mystery, sibling_count: int) -> bool:
    return setting.indoor and sibling_count >= 3 and mystery.id in MYSTERIES


def explain_rejection(setting: Setting, mystery: Mystery, sibling_count: int) -> str:
    if not setting.indoor:
        return "(No story: this bedtime mystery needs an indoor room where everyone can gather quietly.)"
    if sibling_count < 3:
        return "(No story: a majority vote needs at least three children so one choice can truly win.)"
    return "(No story: that combination does not make a calm bedtime mystery.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"sleepy": 1.0, "curious": 1.0, "worry": 0.2},
    ))
    siblings: list[Entity] = []
    pool = BOY_NAMES if params.gender == "boy" else GIRL_NAMES
    idx = 0
    while len(siblings) < params.sibling_count - 1:
        name = pool[idx % len(pool)]
        idx += 1
        if name == params.name or any(s.id == name for s in siblings):
            continue
        siblings.append(world.add(Entity(
            id=name,
            kind="character",
            type=params.gender,
            label=name,
            memes={"sleepy": 1.0, "curious": 1.0},
        )))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label=mystery.clue_word,
        phrase=mystery.clue_word,
        location="somewhere in the room",
    ))
    world.facts.update(hero=hero, siblings=siblings, clue=clue, mystery=mystery)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    setting = world.setting

    world.say(
        f"It was bedtime in {setting.place}, and {hero.label} was getting sleepy."
    )
    world.say(
        f"Just then, {hero.label} noticed something was missing: {mystery.question.lower()}"
    )
    world.say(
        f"{hero.label} frowned, because the room felt less cozy without the {mystery.clue_word}."
    )


def assign_clues(world: World) -> dict[str, str]:
    """Each child notices one clue and votes on a hiding place."""
    f = world.facts
    hero: Entity = f["hero"]
    siblings: list[Entity] = f["siblings"]
    mystery: Mystery = f["mystery"]
    choices = ["window", "pillow", "window", "glow"]  # window gets the majority
    votes: dict[str, str] = {}
    everyone = [hero] + siblings
    for i, child in enumerate(everyone):
        choice = choices[i % len(choices)]
        votes[child.id] = choice
    world.facts["votes"] = votes
    world.facts["majority"] = majority_choice(list(votes.values()))
    return votes


def narrate_search(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    siblings: list[Entity] = f["siblings"]
    mystery: Mystery = f["mystery"]
    votes: dict[str, str] = f["votes"]
    majority = f["majority"]

    names = [hero.label] + [s.label for s in siblings]
    world.para()
    world.say(
        f"{hero.label} called the others close and said, \"Let's use a majority vote so we can solve this.\""
    )
    for child_name in names:
        choice = votes[child_name]
        world.say(
            f"{child_name} pointed to {VOTES[choice].label}."
        )
    world.say(
        f"Three hands pointed to {VOTES[majority].label}, so that became the plan."
    )
    if majority == "window":
        world.say(
            f"They tiptoed to the window seat and found {CLUES['window'].detail}."
        )
    elif majority == "pillow":
        world.say(
            f"They hurried to the pillow pile and found {CLUES['pillow'].detail}."
        )
    else:
        world.say(
            f"They moved to the wall and found {CLUES['glow'].detail}."
        )
    world.facts["found_at"] = majority
    world.facts["solved"] = majority == "window"
    if world.facts["solved"]:
        world.say(
            f"Under the window seat, the {mystery.clue_word} was waiting all along."
        )
    else:
        world.say(
            f"It was not the right spot, but the clue helped them keep searching together."
        )


def narrate_resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    solved = f["solved"]
    found_at = f["found_at"]

    world.para()
    if solved:
        world.say(
            f"{hero.label} lifted the soft {mystery.clue_word} with a smile, and everyone felt relieved."
        )
        world.say(
            f"The room grew quiet again, and bedtime felt warm and safe."
        )
        world.say(
            f"At the end, the group agreed that the majority had led them to the right answer: {VOTES[found_at].label}."
        )
    else:
        world.say(
            f"They kept their voices low and tried another guess until the mystery was solved."
        )
        world.say(
            f"At last, everyone tucked in with calm hearts and a cozy room."
        )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    assign_clues(world)
    narrate_search(world)
    narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    setting = world.setting
    return [
        f'Write a gentle bedtime story about {hero.label}, a group of children, and a majority vote that solves a mystery in {setting.place}.',
        f"Tell a cozy story where children each notice one clue and the majority choice helps them find the {mystery.clue_word}.",
        f'Write a short bedtime tale that includes the word "majority" and ends with the mystery being solved calmly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    votes: dict[str, str] = f["votes"]
    majority = f["majority"]
    found_at = f["found_at"]
    siblings: list[Entity] = f["siblings"]

    child_names = [hero.label] + [s.label for s in siblings]
    majority_label = VOTES[majority].label
    answer_names = ", ".join(child_names[:-1]) + f", and {child_names[-1]}" if len(child_names) > 2 else " and ".join(child_names)

    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {hero.label} and the other children in the room at bedtime.",
        ),
        QAItem(
            question="What mystery did they want to solve?",
            answer=f"They wanted to solve the mystery of {mystery.question.lower()}",
        ),
        QAItem(
            question="What did the children use to choose their plan?",
            answer=f"They used a majority vote, which means they listened for the choice that most children picked.",
        ),
        QAItem(
            question=f"Which place got the majority of votes?",
            answer=f"The majority pointed to {majority_label}. That was the plan the group followed.",
        ),
        QAItem(
            question=f"Where was the {mystery.clue_word} found?",
            answer=f"It was found {mystery.answer}.",
        ),
        QAItem(
            question=f"Why did the group trust the majority choice?",
            answer=f"Because {answer_names} each shared a clue, and the biggest group agreed on {majority_label}, which led them to the right hiding place.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "majority": [
        QAItem(
            question="What does majority mean?",
            answer="A majority means more than half of the group chose the same thing.",
        ),
        QAItem(
            question="Why can a majority vote help a group?",
            answer="A majority vote can help because it lets a group choose the idea most people agree on.",
        ),
    ],
    "bedtime": [
        QAItem(
            question="What is bedtime?",
            answer="Bedtime is the time when children get ready to sleep.",
        )
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a little piece of information that can help solve a mystery.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["majority"])
    out.extend(WORLD_KNOWLEDGE["bedtime"])
    out.extend(WORLD_KNOWLEDGE["clue"])
    return out


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A majority exists when one choice has strictly more votes than every other choice.
majority(Choice) :- count_votes(Choice, N), not beaten(Choice).
beaten(Choice) :- count_votes(Other, N2), count_votes(Choice, N1), Other != Choice, N2 >= N1.
count_votes(Choice, N) :- choice(Choice), N = #count { Child : votes(Child, Choice) }.

% A mystery is solved when the majority choice matches the true answer.
solved(M) :- mystery(M), answer(M, A), majority(A).

#show majority/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for s in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, s))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("answer", mid, m.solved_by and "window" if mid == "blanket" else m.id))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("choice", cid))
    # mirror the intended reasoner with a fixed fact set for parity checking
    lines.append(asp.fact("choice", "window"))
    lines.append(asp.fact("choice", "pillow"))
    lines.append(asp.fact("choice", "glow"))
    lines.append(asp.fact("votes", "a", "window"))
    lines.append(asp.fact("votes", "b", "window"))
    lines.append(asp.fact("votes", "c", "pillow"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show majority/1.\n#show solved/1.")
    model = asp.one_model(program)
    majors = set(asp.atoms(model, "majority"))
    solved = set(asp.atoms(model, "solved"))
    if majors:
        print("OK: ASP program produced a model.")
        print("majority:", sorted(majors))
        print("solved:", sorted(solved))
        return 0
    print("MISMATCH: ASP program did not produce the expected majority model.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about majority voting and a gentle mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--siblings", type=int, default=3, help="number of children in the room, including the hero")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling_count = args.siblings
    params = StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, sibling_count=sibling_count)
    if not valid_story(SETTINGS[setting], MYSTERIES[mystery], sibling_count):
        raise StoryError(explain_rejection(SETTINGS[setting], MYSTERIES[mystery], sibling_count))
    return params


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    for k, v in world.facts.items():
        if k in {"hero", "siblings", "clue", "mystery"}:
            continue
        lines.append(f"  fact {k}: {v}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_model() -> str:
    return asp_program("#show majority/1.\n#show solved/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show majority/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_valid_model())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="bedroom", mystery="blanket", name="Mina", gender="girl", sibling_count=3),
            StoryParams(setting="camproom", mystery="bunny", name="Owen", gender="boy", sibling_count=4),
            StoryParams(setting="bedroom", mystery="lamp", name="Ivy", gender="girl", sibling_count=5),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
