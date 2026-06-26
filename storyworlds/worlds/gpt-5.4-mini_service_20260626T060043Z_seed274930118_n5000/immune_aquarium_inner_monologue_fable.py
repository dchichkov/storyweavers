#!/usr/bin/env python3
"""
A small storyworld: an aquarium fable told with inner monologue.

Premise:
- A tiny aquarium has one gentle caretaker, one small animal, one useful
  cleaning tool, and one invisible problem: an immune response that can
  become too worried.
- The story turns on a quiet mistake, an inner thought, and a kinder choice.

The world is designed so the simulated state drives the prose:
- a tank can get cloudy
- a fish can feel itchy, frightened, or relieved
- the caretaker can notice, pause, and change the water
- the ending proves the change in the water and the animal's mood
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "keeper"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the aquarium"
    water_kind: str = "fresh"


@dataclass
class Creature:
    id: str
    label: str
    type: str
    species: str
    mood: str
    need: str
    vulnerability: str
    immune: str
    inner_tone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    result: str
    protects: set[str]
    removes: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_cloud(world: World) -> list[str]:
    out: list[str] = []
    tank = world.get("tank")
    if tank.meters.get("cloudy", 0.0) < THRESHOLD:
        return out
    sig = ("cloud",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tank.memes["uncertainty"] = tank.memes.get("uncertainty", 0.0) + 1
    out.append("The water turned cloudy, and the little world felt unsure of itself.")
    return out


def _r_itch(world: World) -> list[str]:
    out: list[str] = []
    fish = world.get("fish")
    tank = world.get("tank")
    if tank.meters.get("cloudy", 0.0) < THRESHOLD or fish.meters.get("germs", 0.0) < THRESHOLD:
        return out
    sig = ("itch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fish.memes["uneasy"] = fish.memes.get("uneasy", 0.0) + 1
    out.append("The little fish felt itchy and worried, as if it had to guard its whole small home.")
    return out


def _r_immune(world: World) -> list[str]:
    out: list[str] = []
    fish = world.get("fish")
    if fish.memes.get("uneasy", 0.0) < THRESHOLD:
        return out
    sig = ("immune",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fish.meters["immune_response"] = fish.meters.get("immune_response", 0.0) + 1
    fish.memes["protective"] = fish.memes.get("protective", 0.0) + 1
    out.append("Its immune strength woke up, ready to chase away trouble.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    tank = world.get("tank")
    fish = world.get("fish")
    if tank.meters.get("clean", 0.0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fish.memes["calm"] = fish.memes.get("calm", 0.0) + 1
    fish.memes["uneasy"] = 0.0
    out.append("When the water was clean again, the fish's worries could drift away.")
    return out


RULES = [
    _r_cloud,
    _r_itch,
    _r_immune,
    _r_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    creature: str
    problem: str
    remedy: str
    name: str
    keeper: str
    seed: Optional[int] = None


SETTING = Setting()

CREATURES = {
    "goldfish": Creature(
        id="goldfish",
        label="goldfish",
        type="fish",
        species="goldfish",
        mood="small and brave",
        need="clear water",
        vulnerability="cloudy water",
        immune="quick immune system",
        inner_tone="I must stay calm and keep swimming",
        tags={"immune", "fish", "water"},
    ),
    "guppy": Creature(
        id="guppy",
        label="guppy",
        type="fish",
        species="guppy",
        mood="tiny and bright",
        need="fresh water",
        vulnerability="dirty pebbles",
        immune="alert immune system",
        inner_tone="I can wait and let the water settle",
        tags={"immune", "fish", "water"},
    ),
    "betta": Creature(
        id="betta",
        label="betta",
        type="fish",
        species="betta",
        mood="bold but careful",
        need="still water",
        vulnerability="sudden mess",
        immune="watchful immune system",
        inner_tone="I do not need to panic to be protected",
        tags={"immune", "fish", "water"},
    ),
}

PROBLEMS = {
    "crumbs": ("crumbs from too much feeding", "crumbs drifted into the water"),
    "algae": ("green algae on the glass", "green algae spread and blurred the glass"),
    "dust": ("dust from a lid left open", "dust slipped into the tank"),
}

REMEDIES = {
    "net": Remedy(
        id="net",
        label="a small net",
        action="scoop out the crumbs",
        result="the water looked lighter",
        protects={"crumbs"},
        removes={"crumbs"},
    ),
    "scrub": Remedy(
        id="scrub",
        label="a soft scrubber",
        action="wipe the glass clean",
        result="the view became bright again",
        protects={"algae"},
        removes={"algae"},
    ),
    "cover": Remedy(
        id="cover",
        label="a tight lid",
        action="close the lid",
        result="nothing else could drift in",
        protects={"dust"},
        removes={"dust"},
    ),
}

KEEPERS = [
    ("Mina", "mother"),
    ("Tobin", "father"),
    ("Lena", "keeper"),
    ("Arlo", "keeper"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for creature in CREATURES:
        for prob in PROBLEMS:
            for rem in REMEDIES:
                if prob in REMEDIES[rem].protects:
                    combos.append((SETTING.place, creature, prob))
    return combos


def tell(creature: Creature, problem_key: str, remedy: Remedy, name: str, keeper: str) -> World:
    world = World(SETTING)
    tank = world.add(Entity(id="tank", type="thing", label="the aquarium"))
    fish = world.add(Entity(
        id="fish", kind="character", type="fish", label=creature.label, phrase=creature.label
    ))
    carer = world.add(Entity(id="keeper", kind="character", type=keeper, label=keeper))
    tool = world.add(Entity(id="remedy", type="thing", label=remedy.label))
    world.facts["name"] = name
    world.facts["problem_key"] = problem_key
    world.facts["remedy"] = remedy
    world.facts["creature"] = creature
    world.facts["keeper_entity"] = carer

    tank.meters["clean"] = 1.0
    fish.memes["peace"] = 1.0
    fish.meters["germs"] = 0.0

    world.say(f"In the {SETTING.place}, a little {creature.label} named {name} lived with a careful {keeper}.")
    world.say(
        f"{name} was small, but {name} had a brave inner voice: "
        f'"{creature.inner_tone}."'
    )
    world.say(
        f"{name} also knew {creature.immune}, and it felt like a lantern inside a tiny shell."
    )

    world.para()
    world.say(
        f"One day, {problem_key} came to the aquarium, and the water did not look as clear."
    )
    tank.meters["cloudy"] = 1.0
    fish.meters["germs"] = 1.0
    fish.memes["uneasy"] = 1.0
    world.say(
        f"{name} thought, '{creature.inner_tone} But this water feels wrong.'"
    )
    propagate(world, narrate=True)

    world.para()
    world.say(f"The {keeper} leaned close and said, 'Let's not let worry grow bigger than it must.'")
    world.say(f"Together they chose {remedy.label} to {remedy.action}.")
    if problem_key not in remedy.protects:
        raise StoryError("chosen remedy does not fit the problem")
    tank.meters["cloudy"] = 0.0
    tank.meters["clean"] = 1.0
    fish.meters["germs"] = 0.0
    world.say(f"They worked gently, and soon {remedy.result}.")
    propagate(world, narrate=True)

    world.para()
    fish.memes["peace"] = fish.memes.get("peace", 0.0) + 1
    world.say(
        f"{name} swam in bright water again and thought, 'Being careful is wise, but kindness keeps the tank alive.'"
    )
    world.say(
        f"The {keeper} smiled, because the small home was clear once more, and the brave little {creature.label} was calm."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["creature"]
    rem = world.facts["remedy"]
    prob = world.facts["problem_key"]
    return [
        f'Write a short fable set in an aquarium about "{c.label}" and the word "immune".',
        f"Tell a gentle inner-monologue story where a little {c.label} worries about {prob} and learns to trust care, not panic.",
        f"Write a child-friendly aquarium tale in which a keeper uses {rem.label} to solve a small problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["creature"]
    rem = world.facts["remedy"]
    prob = world.facts["problem_key"]
    return [
        QAItem(
            question=f"Who lived in the aquarium?",
            answer=f"A little {c.label} named {world.facts['name']} lived in the aquarium with a careful {world.facts['keeper_entity'].type}.",
        ),
        QAItem(
            question=f"What problem made the water look wrong?",
            answer=f"{prob.capitalize()} made the water cloudy and uneasy at first.",
        ),
        QAItem(
            question=f"What did the fish think inside its own head?",
            answer=f"It thought, '{c.inner_tone}'",
        ),
        QAItem(
            question=f"How did the keeper help?",
            answer=f"The keeper used {rem.label} to {rem.action}, and that made the water clear again.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The aquarium became bright and clean, and the fish felt calm instead of worried.",
        ),
    ]


KNOWLEDGE = {
    "immune": [
        QAItem(
            question="What does immune mean?",
            answer="Immune means protected from harm or able to fight off a problem before it grows bigger.",
        ),
        QAItem(
            question="Why do bodies have immune systems?",
            answer="Bodies have immune systems to notice trouble, help defend against germs, and keep living things healthy.",
        ),
    ],
    "fish": [
        QAItem(
            question="What do fish need to live in an aquarium?",
            answer="Fish need clean water, room to swim, and care from someone who keeps their home safe.",
        )
    ],
    "water": [
        QAItem(
            question="Why should aquarium water stay clean?",
            answer="Clean water helps fish breathe, swim, and stay comfortable.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["immune"])
    out.extend(KNOWLEDGE["fish"])
    out.extend(KNOWLEDGE["water"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
cloudy(tank) :- problem(crumbs).
uneasy(fish) :- cloudy(tank).
immune_response(fish) :- uneasy(fish).
calm(fish) :- clean(tank).
valid_story(C,P,R) :- creature(C), problem(P), remedy(R), protects(R,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for c in CREATURES.values():
        lines.append(asp.fact("creature", c.id))
        for tag in sorted(c.tags):
            lines.append(asp.fact("tag", c.id, tag))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for r in REMEDIES.values():
        lines.append(asp.fact("remedy", r.id))
        for p in sorted(r.protects):
            lines.append(asp.fact("protects", r.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only python:", sorted(py - cl))
    if cl - py:
        print(" only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aquarium fable with inner monologue and an immune little fish.")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=[k for _, k in KEEPERS])
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
    creature = args.creature or rng.choice(list(CREATURES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    remedy = args.remedy or next(r for r, rm in REMEDIES.items() if problem in rm.protects)
    if problem not in REMEDIES[remedy].protects:
        raise StoryError("that remedy does not fit that problem")
    name = args.name or rng.choice(["Pip", "Nori", "Milo", "Luma", "Tavi"])
    keeper = args.keeper or rng.choice([k for _, k in KEEPERS])
    return StoryParams(
        setting="aquarium",
        creature=creature,
        problem=problem,
        remedy=remedy,
        name=name,
        keeper=keeper,
    )


def generate(params: StoryParams) -> StorySample:
    creature = CREATURES[params.creature]
    world = tell(creature, params.problem, REMEDIES[params.remedy], params.name, params.keeper)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for creature in CREATURES:
            for problem in PROBLEMS:
                remedy = next(r for r, rm in REMEDIES.items() if problem in rm.protects)
                params = StoryParams(
                    setting="aquarium",
                    creature=creature,
                    problem=problem,
                    remedy=remedy,
                    name="Pip",
                    keeper="keeper",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
