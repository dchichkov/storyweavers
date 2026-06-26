#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/virtual_shotgun_soccer_field_repetition_mystery.py
===============================================================================================================

A small, self-contained story world for a child-friendly mystery set on a soccer field.

Premise:
- A kid detective and a coach are trying to solve a repeated-clue mystery.
- A virtual scoreboard keeps making the same strange sound.
- A "shotgun" is not a weapon here; it is a noisy starter prop from a training app:
  a virtual shotgun sound that kicks off drills with a loud pop.
- The clue repeats three times, and the answer comes from noticing the pattern.

The story is built from world state rather than a frozen paragraph:
- physical meters track things like sound, mud, hiding, and clue trail strength
- emotional memes track worry, curiosity, relief, and suspicion
- the mystery resolves when the right repeated clue is connected to the right hidden object

The world supports a few tightly constrained variations, but all stories stay in
the same small domain: a soccer field, a repeated-clue mystery, and a gentle solve.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the soccer field"
    afford_repetition: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    noise: str
    pattern: str
    repeats: int


@dataclass
class Mystery:
    id: str
    question: str
    answer: str
    hide_spot: str
    reveal_spot: str


@dataclass
class StoryParams:
    clue: str
    mystery: str
    detective_name: str
    detective_gender: str
    coach_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clue_count: int = 0
        self.trail_strength: float = 0.0

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.clue_count = self.clue_count
        clone.trail_strength = self.trail_strength
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["heard_noise"] >= THRESHOLD and ent.meters["noticed_pattern"] < THRESHOLD:
            sig = ("pattern", ent.id)
            if sig in world.fired:
                continue
            if world.clue_count >= 3:
                world.fired.add(sig)
                ent.memes["curiosity"] += 1
                ent.meters["noticed_pattern"] += 1
                out.append("The same clue had come back again and again, and that made the shape of the mystery easier to see.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_repetition,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def get_pronouns(kind: str) -> tuple[str, str, str]:
    if kind == "girl":
        return "she", "her", "her"
    if kind == "boy":
        return "he", "him", "his"
    return "it", "it", "its"


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_gender,
        traits=["little", params.trait, "curious"],
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=params.coach_gender,
        label="the coach",
        traits=["patient", "calm"],
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label=CLUES[params.clue].label,
        phrase=CLUES[params.clue].phrase,
        hidden_in=MYSTERIES[params.mystery].hide_spot,
    ))
    mystery = world.add(Entity(
        id="mystery",
        type="thing",
        label=MYSTERIES[params.mystery].question,
        phrase=MYSTERIES[params.mystery].answer,
    ))
    world.facts.update(
        detective=detective,
        coach=coach,
        clue=clue,
        mystery=mystery,
        clue_cfg=CLUES[params.clue],
        mystery_cfg=MYSTERIES[params.mystery],
        params=params,
    )

    # Act 1: setup
    world.say(
        f"{detective.id} was a little {params.trait} detective who loved solving mysteries at {world.setting.place}."
    )
    world.say(
        f"{detective.pronoun('subject').capitalize()} was especially interested in a weird little thing called a virtual shotgun sound, because it kept popping up in the practice app."
    )
    world.say(
        f"The coach asked {detective.pronoun('object')} to find out why the same clue kept repeating near the goal."
    )

    # Act 2: mystery begins
    world.para()
    world.say(
        f"At first, {detective.id} heard the clue once: {clue.phrase}. Then it came again, and again."
    )
    world.clue_count = clue.repeats
    detective.meters["heard_noise"] += 1
    detective.memes["suspicion"] += 1
    world.trail_strength = float(clue.repeats)
    world.say(
        f"Each time the virtual shotgun sound popped, the same small mark showed up by the sideline."
    )
    world.say(
        f"{detective.id} looked from the mark to the bench, then to the goal net, trying to notice the pattern."
    )
    propagate(world)

    # Act 3: reveal
    world.para()
    hidden = MYSTERIES[params.mystery].reveal_spot
    world.say(
        f"At last, {detective.id} checked the {hidden}, because that was the one place the repeating clue pointed to."
    )
    clue.meters["found"] += 1
    detective.memes["relief"] += 1
    coach.memes["relief"] += 1
    world.say(
        f"There, tucked away, was the answer: {mystery.phrase}"
    )
    world.say(
        f"The coach laughed softly, and {detective.id} smiled, because the mystery was not scary after all."
    )
    world.say(
        f"The virtual shotgun sound had only been a noisy starter signal, and the real secret was the pattern it left behind."
    )

    world.facts["solved"] = True
    world.facts["trail_strength"] = world.trail_strength
    return world


CLUES = {
    "whistle": Clue(
        id="whistle",
        label="a whistle",
        phrase="a sharp whistle note",
        noise="whistle",
        pattern="three short peeps",
        repeats=3,
    ),
    "cones": Clue(
        id="cones",
        label="orange cones",
        phrase="three orange cones in a row",
        noise="tap",
        pattern="three taps",
        repeats=3,
    ),
    "shoe": Clue(
        id="shoe",
        label="a lost shoe",
        phrase="a tiny scuff and a toe mark",
        noise="scrape",
        pattern="three scuffs",
        repeats=3,
    ),
}

MYSTERIES = {
    "bench": Mystery(
        id="bench",
        question="where the missing thing was hiding",
        answer="the bench seat",
        hide_spot="bench seat",
        reveal_spot="bench",
    ),
    "net": Mystery(
        id="net",
        question="where the missing thing was hiding",
        answer="the goal net",
        hide_spot="goal net",
        reveal_spot="net",
    ),
    "bag": Mystery(
        id="bag",
        question="where the missing thing was hiding",
        answer="the coach's bag",
        hide_spot="coach's bag",
        reveal_spot="bag",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Max", "Finn", "Sam"]
TRAITS = ["careful", "brave", "patient", "sharp-eyed", "quiet", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    return [(c, m) for c in CLUES for m in MYSTERIES]


@dataclass
class StoryParams:
    clue: str
    mystery: str
    detective_name: str
    detective_gender: str
    coach_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    clue = f["clue_cfg"]
    mystery = f["mystery_cfg"]
    return [
        f'Write a short mystery story for a young child set on a soccer field, using the phrase "virtual shotgun".',
        f"Tell a gentle detective story where {p.detective_name} hears {clue.pattern} over and over and learns what the repeating clue means.",
        f"Write a story about a {p.trait} detective who solves a small mystery at the soccer field by noticing repetition.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    detective = f["detective"]
    clue = f["clue_cfg"]
    mystery = f["mystery_cfg"]
    det_sub, det_obj, det_pos = detective.pronoun("subject"), detective.pronoun("object"), detective.pronoun("possessive")
    return [
        QAItem(
            question=f"Who solved the mystery at the soccer field?",
            answer=f"{p.detective_name}, the little {p.trait} detective, solved it by noticing the same clue again and again.",
        ),
        QAItem(
            question=f"What kept repeating and making the mystery feel strange?",
            answer=f"The clue repeated {clue.repeats} times, and the virtual shotgun sound helped make the pattern noticeable.",
        ),
        QAItem(
            question=f"Where was the answer hiding?",
            answer=f"It was hiding in the {mystery.reveal_spot}, which matched the clue pattern the detective noticed.",
        ),
        QAItem(
            question=f"Why did {p.detective_name} start to suspect a pattern?",
            answer=f"Because {det_obj} heard the same clue over and over at {world.setting.place}, and repetition made the mystery easier to read.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{p.detective_name} found the hidden answer, and the coach felt relieved because the mystery was solved safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story problem where something is hidden or confusing, and someone looks carefully for clues to figure it out.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again. In stories, repeating clues can help you notice a pattern.",
        ),
        QAItem(
            question="What is a soccer field?",
            answer="A soccer field is a big grassy place where people play soccer, run after the ball, and try to score goals.",
        ),
        QAItem(
            question="What is a virtual thing?",
            answer="A virtual thing is something made by a computer or screen, like a game sound or a pretend tool inside an app.",
        ),
        QAItem(
            question="What is a shotgun in this story?",
            answer="In this story, shotgun means a loud starter sound from a practice app, not a weapon.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clue_count={world.clue_count} trail_strength={world.trail_strength}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, mystery: Mystery) -> str:
    return f"(No story: this world only allows clue patterns that repeat cleanly, and the selected pair does not fit the mystery rhythm.)"


ASP_RULES = r"""
clue(C) :- clue_id(C).
mystery(M) :- mystery_id(M).
valid(C,M) :- clue(C), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("clue_repeats", cid, c.repeats))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_id", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly soccer-field mystery with repetition and a virtual shotgun clue.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--coach", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.clue and args.mystery and (args.clue, args.mystery) not in combos:
        raise StoryError(explain_rejection(CLUES[args.clue], MYSTERIES[args.mystery]))
    if args.clue or args.mystery:
        combos = [c for c in combos if (args.clue is None or c[0] == args.clue) and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clue, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    coach = args.coach or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(clue=clue, mystery=mystery, detective_name=name, detective_gender=gender, coach_gender=coach, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(clue="whistle", mystery="bench", detective_name="Mia", detective_gender="girl", coach_gender="mother", trait="sharp-eyed"),
    StoryParams(clue="cones", mystery="net", detective_name="Theo", detective_gender="boy", coach_gender="father", trait="quiet"),
    StoryParams(clue="shoe", mystery="bag", detective_name="Nora", detective_gender="girl", coach_gender="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(f"{len(set(asp.atoms(model, 'valid')))} compatible clue/mystery pairs:")
        for c, m in sorted(set(asp.atoms(model, "valid"))):
            print(f"  {c:8} {m:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.detective_name}: {p.clue} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
