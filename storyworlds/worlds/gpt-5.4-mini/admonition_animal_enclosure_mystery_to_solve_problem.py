#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/admonition_animal_enclosure_mystery_to_solve_problem.py
=======================================================================================

A standalone story world for a small nursery-rhyme-style mystery in an animal
enclosure: a child gets an admonition, a problem appears, a few clues are
followed, and a twist reveals what was really happening. The story stays
grounded in a tiny simulated world with physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
EMOTION_HIGH = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    rhyme: str
    sounds: str


@dataclass
class Mystery:
    id: str
    clue: str
    misread: str
    truth: str
    problem: str
    twist: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    kind: str
    label: str
    noise: str
    trail: str
    likes: str
    meter_kind: str
    can_move: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.entities.get("keeper")
    if not keeper:
        return out
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        keeper.memes["alert"] += 1
        out.append("__admonition__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts["mystery"]
    for animal in world.facts["animals"]:
        if animal.meters[mystery.solved_by] < THRESHOLD:
            sig = ("clue", animal.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{animal.label.capitalize()} left a clue.")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("clue", "mystery", _r_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solveable(mystery: Mystery, animal: Animal, tool: Tool) -> bool:
    return mystery.solved_by == tool.id and animal.can_move


def predict_mystery(world: World, animal: Animal, mystery: Mystery, tool: Tool) -> dict:
    sim = world.copy()
    sim.get(animal.id).meters[mystery.solved_by] += 1
    propagate(sim, narrate=False)
    return {
        "clues": sum(1 for e in sim.facts["animals"] if e.meters[mystery.solved_by] >= THRESHOLD),
        "alert": sim.get("keeper").memes["alert"],
    }


def start(world: World, child: Entity, keeper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At the animal enclosure, {child.id} went with {keeper.label_word} to see "
        f"the creatures by the fence. {setting.rhyme}"
    )
    world.say(
        f'"{child.id}, heed my admonition," {keeper.label_word} said, "and keep your hands '
        f"still and your eyes wide."'
    )


def mystery_appears(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"But oh dear me, a little mystery came to play: {mystery.problem}. "
        f"{mystery.clue}"
    )
    world.say(
        f'{child.id} frowned and whispered, "Why is {mystery.misread}?"'
    )


def search(world: World, child: Entity, keeper: Entity, mystery: Mystery) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{child.id} peeked by the gate and counted the signs, while "
        f"{keeper.label_word} looked for a tidy way to solve the riddle."
    )


def explain_twist(world: World, keeper: Entity, animal: Animal, mystery: Mystery) -> None:
    keeper.memes["relief"] += 1
    world.say(
        f"Then came the twist with a tiny trilling hiss: {mystery.twist}. "
        f"It was only {animal.label} carrying {animal.likes} in a cloth pouch."
    )


def solve(world: World, keeper: Entity, tool: Tool, mystery: Mystery, animal: Animal) -> None:
    world.get(animal.id).meters[mystery.solved_by] += 1
    propagate(world, narrate=False)
    world.say(
        f"{keeper.label_word} used {tool.label}, because {tool.helps}, and soon the clue made sense."
    )
    world.say(
        f"The mystery was solved at once: {animal.label} had been the one making the trail, "
        f"and the trail matched {mystery.truth}."
    )


def ending(world: World, child: Entity, keeper: Entity, animal: Animal, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    keeper.memes["joy"] += 1
    world.say(
        f"{child.id} giggled, {keeper.label_word} smiled, and {animal.label} trotted off with a friendly {animal.noise}. "
        f"The little enclosure felt calm again, and the moon seemed to nod."
    )


THEMES = {
    "nursery": Setting(
        "nursery",
        "In the little animal enclosure, the lambs bleated soft and low, and the ducks went quack in a tidy row.",
        "The gate was white, the path was neat, and pebbles clicked beneath small feet.",
        "The breeze said shoo and the straw said hush, a sleepy song in the hush-hush bush.",
    )
}

MYSTERIES = {
    "missing_hat": Mystery(
        "missing_hat",
        clue="A feather on the ground pointed toward the goat pen.",
        misread="the feather belonged to a bird",
        truth="the feather had brushed against a goat's hat-string",
        problem="the little straw hat had vanished from the bench",
        twist="the 'bird' was only a goat with a hat and a feather stuck to its horn",
        solved_by="sniff",
        tags={"hat", "feather", "goat"},
    ),
    "lost_bell": Mystery(
        "lost_bell",
        clue="A bright jingle came from behind the sheep shed.",
        misread="the bell had rolled away forever",
        truth="the bell was tied to a rabbit toy",
        problem="the tiny brass bell was gone from the cart",
        twist="the sound came from a rabbit tugging a ribbon",
        solved_by="listen",
        tags={"bell", "rabbit"},
    ),
    "muddy_track": Mystery(
        "muddy_track",
        clue="Little muddy prints went round and round by the pond.",
        misread="a big monster had visited",
        truth="a piglet had spun in circles after rain",
        problem="the clean path had become a mystery of muddy prints",
        twist="the 'monster' was a piglet chasing its own tail",
        solved_by="track",
        tags={"mud", "piglet"},
    ),
}

ANIMALS = {
    "goat": Animal("goat", "animal", "goat", "baa", "trail", "hay", "sniff", tags={"goat", "hat"}),
    "rabbit": Animal("rabbit", "animal", "rabbit", "squeak", "trail", "carrots", "listen", tags={"rabbit", "bell"}),
    "piglet": Animal("piglet", "animal", "piglet", "oink", "trail", "mud", "track", tags={"piglet", "mud"}),
}

TOOLS = {
    "sniff": Tool("sniff", "a sniff around", "sniff", "sniffing follows the scent"),
    "listen": Tool("listen", "a careful listen", "listen", "listening catches the jingly sound"),
    "track": Tool("track", "a tidy track map", "track", "tracking shows where prints go"),
}

GIRL_NAMES = ["Mabel", "Nina", "Lily", "Poppy", "Nell", "Betsy"]
BOY_NAMES = ["Tom", "Teddy", "Jack", "Milo", "Benny", "Finn"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    animal: str
    tool: str
    child: str
    child_gender: str
    keeper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in THEMES:
        for mid, mystery in MYSTERIES.items():
            for aid, animal in ANIMALS.items():
                if solveable(mystery, animal, TOOLS[mystery.solved_by]):
                    combos.append((sid, mid, aid, mystery.solved_by))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme mystery in an animal enclosure.")
    ap.add_argument("--setting", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=["keeper", "mom", "dad"])
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
    if args.mystery and args.tool and args.tool != MYSTERIES[args.mystery].solved_by:
        raise StoryError("That tool does not solve this mystery.")
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.mystery in (None, c[1])
              and args.animal in (None, c[2])
              and args.tool in (None, c[3])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, animal, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper = args.keeper or rng.choice(["mom", "dad", "keeper"])
    return StoryParams(setting, mystery, animal, tool, child, gender, keeper)


def tell(params: StoryParams) -> World:
    setting = THEMES[params.setting]
    mystery = MYSTERIES[params.mystery]
    animal = ANIMALS[params.animal]
    tool = TOOLS[params.tool]
    world = World(setting)
    child = world.add(Entity(params.child, "character", params.child_gender, role="child"))
    keeper = world.add(Entity("keeper", "character", "adult", role=params.keeper, type=params.keeper if params.keeper in {"mom", "dad"} else "adult"))
    world.facts["mystery"] = mystery
    world.facts["animals"] = [world.add(Entity(animal.id, "thing", "animal", traits=[animal.label]))]

    start(world, child, keeper, setting)
    world.para()
    mystery_appears(world, child, mystery)
    search(world, child, keeper, mystery)
    explain_twist(world, keeper, animal, mystery)
    world.para()
    solve(world, keeper, tool, mystery, animal)
    ending(world, child, keeper, animal, mystery)

    world.facts.update(child=child, keeper=keeper, animal=animal, tool=tool, setting=setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story in an animal enclosure that uses the word "admonition" and solves a small mystery.',
        f"Tell a gentle story where {f['child'].id} hears an admonition from {f['keeper'].label_word}, notices a clue, and discovers a twist about {f['animal'].label}.",
        f"Write a soft rhyming story about a missing thing in the animal enclosure, where careful problem solving reveals what really happened.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    mystery = f["mystery"]
    animal = f["animal"]
    tool = f["tool"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who went to the animal enclosure with {keeper.label_word}. The little scene is built around a mystery and a calm solve-it-together moment."),
        ("What was the mystery?",
         f"The mystery was that {mystery.problem}. The clue and the twist showed that it was not what it first seemed."),
        ("How was it solved?",
         f"They used {tool.label}, because {tool.helps}. That helped them follow the clue and learn that {animal.label} was involved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal"].label
    out = [
        ("What does an admonition mean?",
         "An admonition is a careful warning or reminder to behave safely and wisely."),
        ("What is an animal enclosure?",
         "An animal enclosure is a fenced or walled place where animals are kept so people can watch them safely."),
        ("What is a mystery?",
         "A mystery is something puzzling that needs clues and careful thinking to solve."),
        ("What does a keeper do?",
         "A keeper cares for animals, watches over them, and makes sure their home stays safe and tidy."),
        (f"What sound does a {animal} make?",
         f"A {animal} makes a small friendly sound like {f['animal'].noise}."),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, A, T) :- setting(S), mystery(M), animal(A), tool(T), solved_by(M, T).
outcome(solved) :- valid(_, _, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in THEMES:
        lines.append(asp.fact("setting", s))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("solved_by", mid, m.solved_by))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, animal=None, tool=None, child=None, gender=None, keeper=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as ex:
        print(f"FAILED: generation smoke test crashed: {ex}")
        rc = 1
    return rc


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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("nursery", "missing_hat", "goat", "sniff", "Mabel", "girl", "keeper"),
            StoryParams("nursery", "lost_bell", "rabbit", "listen", "Tom", "boy", "mom"),
            StoryParams("nursery", "muddy_track", "piglet", "track", "Nell", "girl", "dad"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
