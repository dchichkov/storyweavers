#!/usr/bin/env python3
"""
storyworlds/worlds/warn_bruise_poop_bravery_problem_solving_happy.py
=====================================================================

A small mystery-flavored story world about a brave child who notices a problem,
warns someone in time, and helps reach a happy ending.

Seed tale:
---
Nia liked to solve little mysteries. One afternoon, she found a blue ribbon on the sidewalk,
then a muddy paw print near the garden gate. Her little brother Otis was hopping on one foot
because he had bumped his knee and it hurt like a bruise. Just then, Nia spotted a fresh
mess in the grass and warned Otis not to step there. Together they followed the clues,
cleaned the path, and found the missing garden bell hidden under a bench. Otis laughed,
the bruise stopped hurting so much, and everyone felt proud and happy.

World idea:
---
- Physical meters: clues, mess, bruise, tidiness, safety
- Emotional memes: worry, bravery, confidence, relief, joy
- A warning can prevent a worse mess.
- A brave child can solve a small mystery by noticing clues, staying calm, and helping.

The prose engine, Q&A, and ASP twin are all in this file.
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
    kind: str = "thing"  # character | thing
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    clues: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    warning: str
    problem: str
    solution: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", clues={"ribbon", "pawprint", "bell"}),
    "yard": Setting(place="the backyard", clues={"stick", "shoeprint", "shovel"}),
    "hall": Setting(place="the school hall", indoor=True, clues={"note", "mudprint", "locker"}),
}

MYSTERIES = {
    "garden_bell": Mystery(
        id="garden_bell",
        clue="a blue ribbon and a muddy paw print",
        warning="fresh poop near the grass",
        problem="the garden bell was missing",
        solution="follow the clues and look under the bench",
        reveal="the bell was tucked under a bench by the flower bed",
        tags={"clue", "warning", "poop"},
    ),
    "lost_cookie": Mystery(
        id="lost_cookie",
        clue="crumbs by the step and a tiny shoe mark",
        warning="a bruise on the knee from bumping a table",
        problem="the cookie tin had vanished",
        solution="search the shelf and open the old drawer",
        reveal="the tin was on the top shelf all along",
        tags={"clue", "bruise", "problem_solving"},
    ),
    "missing_crayon": Mystery(
        id="missing_crayon",
        clue="a red smear and a folded note",
        warning="a bruise from the slippery floor",
        problem="the red crayon was missing",
        solution="check the basket and listen for a rattle",
        reveal="the crayon was hiding in the basket of scarves",
        tags={"clue", "bruise", "mystery"},
    ),
}

HEROES = [("Nia", "girl"), ("Eli", "boy"), ("Mina", "girl"), ("Otto", "boy")]
SIDEKICKS = [("Otis", "boy"), ("June", "girl"), ("Pip", "boy"), ("Luna", "girl")]


class StoryWorld(World):
    pass


def _note(world: World, ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _feel(world: World, ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def investigate(world: World, hero: Entity, mystery: Mystery) -> None:
    _feel(world, hero, "curiosity", 1.0)
    world.say(
        f"{hero.id} liked mysteries, so {hero.pronoun()} looked closely at the quiet path."
    )
    world.say(
        f"Then {hero.id} spotted {mystery.clue}, and that made {hero.pronoun('object')} pause."
    )
    _note(world, hero, "clues", 1.0)
    _feel(world, hero, "bravery", 1.0)


def warn_about_poop(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    sidekick.memes["risk"] = sidekick.memes.get("risk", 0.0) + 1.0
    hero.memes["protection"] = hero.memes.get("protection", 0.0) + 1.0
    world.say(
        f'{hero.id} sniffed the air and warned, "Stop! There is poop in the grass."'
    )
    world.say(
        f"{hero.id} spoke in a brave voice, because {hero.pronoun()} did not want {sidekick.id} to get hurt."
    )
    _note(world, world.get(sidekick.id), "safety", 1.0)


def bruise_and_calm(world: World, sidekick: Entity) -> None:
    _note(world, sidekick, "bruise", 1.0)
    _feel(world, sidekick, "worry", 1.0)
    world.say(
        f"{sidekick.id} had a bruise on {sidekick.pronoun('possessive')} knee and walked slowly."
    )
    world.say(
        f"But {sidekick.id} took a deep breath, because {sidekick.pronoun()} knew help was near."
    )


def solve_mystery(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    _feel(world, hero, "problem_solving", 1.0)
    world.say(
        f"{hero.id} followed the clue, then checked the place {mystery.solution.split(' and ')[0]}."
    )
    world.say(
        f"{hero.id} and {sidekick.id} worked together, and that turned the little problem into a plan."
    )
    world.say(
        f"They found that {mystery.reveal}."
    )
    world.say(
        f"{hero.id} smiled, because the mystery had an answer at last."
    )


def happy_ending(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    _feel(world, hero, "joy", 1.0)
    _feel(world, sidekick, "relief", 1.0)
    _note(world, world.get("scene"), "tidiness", 1.0)
    world.say(
        f"Then {hero.id} helped clean the path, and the poop was gone."
    )
    world.say(
        f"{sidekick.id} felt better, the bruise was not the only thing that faded, and both friends laughed."
    )
    world.say(
        f"In the end, the garden felt safe again, and the day ended with a happy ending."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str,
         sidekick_name: str, sidekick_type: str) -> World:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type))
    scene = world.add(Entity(id="scene", kind="thing", type="place", label=setting.place))
    world.facts.update(hero=hero, sidekick=sidekick, mystery=mystery, setting=setting)

    world.say(f"One morning, {hero.id} and {sidekick.id} went to {setting.place}.")
    world.say(
        f"The place was quiet, and it felt like a mystery might be hiding there."
    )
    world.para()

    investigate(world, hero, mystery)
    bruise_and_calm(world, sidekick)
    warn_about_poop(world, hero, sidekick, mystery)
    world.para()

    solve_mystery(world, hero, sidekick, mystery)
    happy_ending(world, hero, sidekick, mystery)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mystery = f["mystery"]
    return [
        f"Write a child-friendly mystery story about {hero.id} and {sidekick.id} where someone warns about poop.",
        f"Tell a brave problem-solving story that includes a bruise, a warning, and a happy ending.",
        f"Write a small mystery in which {hero.id} notices clues and helps {sidekick.id} stay safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who warned about the poop in {setting.place}?",
            answer=f"{hero.id} warned about the poop so {sidekick.id} would not step in it."
        ),
        QAItem(
            question=f"What problem was the mystery about?",
            answer=f"The mystery was about {mystery.problem}, and the children had to solve it."
        ),
        QAItem(
            question=f"How did the story show bravery?",
            answer=f"{hero.id} was brave by speaking up, staying calm, and helping solve the problem."
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The children solved the mystery, cleaned the mess, and ended the day laughing together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bruise?",
            answer="A bruise is a sore spot on the body that can look blue, purple, or dark after a bump."
        ),
        QAItem(
            question="Why do people warn others about danger?",
            answer="People warn others so they can stay safe and avoid getting hurt."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a way to fix a problem or answer a question."
        ),
        QAItem(
            question="Why do mysteries make people look closely?",
            answer="Mysteries make people look closely because clues help them figure out what happened."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", mystery="garden_bell", hero="Nia", hero_type="girl", sidekick="Otis", sidekick_type="boy"),
    StoryParams(place="yard", mystery="lost_cookie", hero="Eli", hero_type="boy", sidekick="June", sidekick_type="girl"),
    StoryParams(place="hall", mystery="missing_crayon", hero="Mina", hero_type="girl", sidekick="Pip", sidekick_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with bravery, problem solving, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero, hero_type = (args.hero, args.hero_type) if args.hero and args.hero_type else rng.choice(HEROES)
    sidekick, sidekick_type = (args.sidekick, args.sidekick_type) if args.sidekick and args.sidekick_type else rng.choice(SIDEKICKS)
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(place=place, mystery=mystery, hero=hero, hero_type=hero_type, sidekick=sidekick, sidekick_type=sidekick_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.hero, params.hero_type, params.sidekick, params.sidekick_type)
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


ASP_RULES = r"""
hero(H).
sidekick(S).
mystery(M).
place(P).

warns(H,S) :- hero(H), sidekick(S).
brave(H) :- hero(H), warns(H,_).
problem_solving(H) :- hero(H), mystery(_).
happy_ending :- brave(_), problem_solving(_), warns(_, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for h, _ in HEROES:
        lines.append(asp.fact("hero", h))
    for s, _ in SIDEKICKS:
        lines.append(asp.fact("sidekick", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show warns/2.\n#show brave/1.\n#show problem_solving/1.\n#show happy_ending/0."))
    atoms = {str(sym) for sym in model}
    expected = {"warns(nia,otis)", "brave(nia)", "problem_solving(nia)", "happy_ending"}
    if atoms == expected:
        print("OK: ASP twin matches the Python story shape.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("got:", sorted(atoms))
    print("exp:", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show warns/2.\n#show brave/1.\n#show problem_solving/1.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show happy_ending/0."))
        print("ASP model atoms:", " ".join(str(a) for a in model))
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
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
