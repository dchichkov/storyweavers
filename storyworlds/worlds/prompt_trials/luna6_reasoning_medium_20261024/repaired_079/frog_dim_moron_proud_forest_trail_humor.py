#!/usr/bin/env python3
"""
A small superhero storyworld about Frog-Dim, a forest-trail mystery, and the
difference a shared idea can make.

Seed image:
---
Frog-Dim, a frog superhero whose glow grows dim when she gets nervous, finds
that the trail's silver bell has gone missing. A funny, confusing clue leads
her and her friend toward the answer. By listening, sharing, and testing their
ideas, they solve the mystery and help the forest feel welcoming again.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in para) for para in self.paragraphs if para)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Frog-Dim"
    helper: str = "Pip"
    trail: str = "Fernbell Trail"


HEROES = ["Frog-Dim", "Captain Croak", "Lily Leap"]
HELPERS = ["Pip", "Moss", "Tumble"]
TRAILS = ["Fernbell Trail", "Mossy Loop", "Blueberry Path"]


# Each mystery has a concrete clue, a testable solution, and a visible result.
MYSTERIES = [
    {
        "title": "the vanishing silver bell",
        "problem": "the silver bell that marked the safe trail crossing had disappeared",
        "clue": "a muddy sign seemed to say MORON",
        "first_guess": "someone had left a very rude message",
        "test": "they brushed away the mud and noticed a faint space between the letters",
        "discovery": "the carving said MORE ON: keep walking and look for the next blue stone",
        "action": "followed the blue stones and listened between gusts of wind",
        "answer": "a young squirrel had moved the bell beside a fallen branch so it would not roll into the stream",
        "humor": "Pip tried to look stern, but a leaf stuck to his nose and gave him a leafy mustache",
        "ending": "the silver bell rang once beside the cleared crossing, and fireflies blinked along the safe path",
        "lesson": "sharing a guess gives a team more clues to test",
    },
    {
        "title": "the trail's missing blue markers",
        "problem": "three blue trail markers had vanished near a bend",
        "clue": "a line of tiny footprints curved around a mushroom, then stopped",
        "first_guess": "a miniature monster had tiptoed into the ferns",
        "test": "Frog-Dim and Pip compared the footprints with the round prints left by fallen pinecones",
        "discovery": "the marks came from a beetle dragging blue petals toward a little nest",
        "action": "followed the petal trail slowly and checked each turn against the map",
        "answer": "a beetle had gathered the loose blue petals, while the wooden markers had toppled beneath a fern",
        "humor": "Pip saluted a pinecone, which promptly rolled away as if it had important superhero business",
        "ending": "the blue markers stood upright again, and the beetle's petal trail made a tiny bright border",
        "lesson": "a careful comparison can turn a wild guess into a useful answer",
    },
    {
        "title": "the whispering hollow log",
        "problem": "a soft whisper from a hollow log made hikers stop before the footbridge",
        "clue": "the whisper repeated the same three-note tune whenever the wind blew",
        "first_guess": "a shy forest ghost was asking for a secret password",
        "test": "they took turns listening from beside the log and from behind the wind-bent grass",
        "discovery": "the breeze was blowing through a reed tucked into a crack in the wood",
        "action": "lifted the reed together and checked that the footbridge boards were still firm",
        "answer": "a loose reed had made the hollow log sing whenever the breeze crossed the trail",
        "humor": "Pip whispered hello to the log, and the log answered with a noise like a very small duck",
        "ending": "the quiet log rested beside the sound footbridge while the friends crossed in the afternoon light",
        "lesson": "sharing what each person hears can make a mystery easier to solve",
    },
    {
        "title": "the upside-down acorn arrow",
        "problem": "the acorn arrow at a fork pointed toward a patch of prickly brambles",
        "clue": "one side of the wooden arrow was scratched, but the other side was smooth",
        "first_guess": "a badger had secretly changed the trail overnight",
        "test": "they shared the map and checked where the arrow's old paint matched the post",
        "discovery": "the arrow had spun around on its loose peg during the windy night",
        "action": "turned the arrow back toward the marked path and wedged its peg with a flat stone",
        "answer": "the wind had spun the loose arrow; no one had meant to send hikers into the brambles",
        "humor": "Pip announced that the arrow had been doing cartwheels, then tried one and landed sitting down",
        "ending": "the acorn arrow pointed toward the open path as a sunbeam warmed the safe fork",
        "lesson": "checking a clue together is kinder and wiser than blaming someone",
    },
]


@dataclass
class TrailMystery:
    clue: str
    solved: bool = False
    shared_ideas: int = 0


@dataclass
class Rescue:
    safe_crossing: bool = False
    trail_marked: bool = False


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.hero}|{params.helper}|{params.trail}"
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(params.hero, "character", "frog_superhero", params.hero))
    helper = world.add(Entity(params.helper, "character", "forest_friend", params.helper))
    trail = world.add(Entity("trail", "place", "forest_trail", params.trail))
    bell = world.add(Entity("silver_bell", "thing", "trail_bell", "silver bell"))
    map_entity = world.add(Entity("map", "thing", "trail_map", "folded trail map"))

    hero.meters.update(bravery=0.5, glow=0.35, confidence=0.3)
    hero.memes.update(worry=0.6, pride=0.0)
    helper.meters.update(observation=0.7, kindness=0.8)
    helper.memes.update(curiosity=0.8, confidence=0.4)
    trail.meters.update(safety=0.5, markers=0.5)
    bell.meters.update(found=0.0, sound=1.0)
    map_entity.meters["usefulness"] = 0.7

    world.facts.update(
        hero=hero,
        helper=helper,
        trail=trail,
        bell=bell,
        map=map_entity,
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def tell_story(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("Choose a registered hero, helper, and forest trail; the hero and helper must be different.")

    world = World()
    _setup(world, params)
    token = _selection_token(params)
    mystery_index = token % len(MYSTERIES)
    mystery = MYSTERIES[mystery_index]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    trail = world.facts["trail"]
    bell = world.facts["bell"]
    mystery_state = TrailMystery(clue=mystery["clue"])
    rescue = Rescue()

    world.say(
        f"On {trail.label}, {hero.label} wore a bright leaf cape and listened for the silver bell "
        "that helped hikers find the safe crossing."
    )
    world.say(
        f"But that morning, {mystery['problem']}. {hero.label}'s superhero glow shrank to a nervous little dot."
    )

    world.para()
    world.say(
        f"{helper.label} spotted a clue: {mystery['clue']}. At first, {hero.label} thought "
        f"{mystery['first_guess']}."
    )
    world.say(
        f'"Let us share what we noticed," said {helper.label}. "{hero.label}, what do you see?" '
        f'"A smudge, and maybe a space," {hero.label} replied. "Let us check before we decide."'
    )
    mystery_state.shared_ideas += 1
    hero.memes["worry"] = 0.35
    hero.meters["confidence"] = 0.55
    world.fired.add(("share_observations", mystery_index))
    world.say(
        f"They tested the clue together: {mystery['test']}. {mystery['humor']} "
        "For one moment, even Frog-Dim's glow seemed to giggle."
    )

    world.para()
    world.say(
        f"The letters made sense at last: {mystery['discovery']}. "
        f"They {mystery['action']}."
    )
    mystery_state.solved = True
    hero.meters["bravery"] = 1.0
    hero.meters["glow"] = 1.0
    hero.meters["confidence"] = 1.0
    helper.memes["curiosity"] = 1.0
    world.fired.add(("solve_mystery", mystery_index))
    world.say(
        f"Together they found the answer: {mystery['answer']}. "
        f'"We can help without taking over," said {helper.label}. '
        f'"And we can make the trail safer together," {hero.label} answered.'
    )

    bell.meters["found"] = 1.0
    trail.meters["safety"] = 1.0
    trail.meters["markers"] = 1.0
    rescue.safe_crossing = True
    rescue.trail_marked = True
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0
    world.fired.add(("restore_trail", mystery_index))

    world.para()
    world.say(
        f"They shared the work, made the crossing safe, and put the trail clue where hikers could read it. "
        f"{hero.label} felt proud, not because she had solved everything alone, but because {mystery['lesson']}."
    )
    world.say(f"At the end of {trail.label}, {mystery['ending']}.")

    world.facts.update(
        params=params,
        mystery=mystery,
        mystery_index=mystery_index,
        mystery_state=mystery_state,
        rescue=rescue,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(params: Optional[StoryParams] = None) -> bool:
    if params is None:
        return True
    if params.hero not in HEROES or params.helper not in HELPERS or params.trail not in TRAILS:
        return False
    if params.hero == params.helper:
        return False
    token = _selection_token(params)
    mystery = MYSTERIES[token % len(MYSTERIES)]
    return all(mystery.get(key) for key in ("problem", "clue", "test", "discovery", "answer", "ending"))


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        f"Write a child-friendly superhero story on {params.trail} about {params.hero} solving {mystery['title']}.",
        f"Include a funny but harmless clue, a brief exchange between {params.hero} and {params.helper}, and a mystery they solve by sharing observations.",
        "End with a concrete image showing how the forest trail became safer and how the hero's feelings changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What trouble did {params.hero} find on {params.trail}?",
            answer=f"{mystery['problem'].capitalize()}. The missing or confusing trail clue made it harder for hikers to know what to do.",
        ),
        QAItem(
            question="What clue first made the mystery confusing?",
            answer=f"The clue was {mystery['clue']}. The friends did not trust their first guess, so they checked it together.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.helper} work as a team?",
            answer=f"They shared what each had noticed and tested the clue together: {mystery['test']}. That let them discover that {mystery['discovery']}.",
        ),
        QAItem(
            question="What did they learn from solving the mystery?",
            answer=f"They learned that {mystery['lesson']}. They shared the work instead of blaming anyone or expecting one hero to do everything.",
        ),
        QAItem(
            question="How could a reader tell that the trail was safer at the end?",
            answer=f"They made the crossing safe and left the trail clue where hikers could read it. At the end, {mystery['ending']}.",
        ),
        QAItem(
            question=f"Why did {params.hero} feel proud?",
            answer=f"{params.hero} felt proud because the friends solved the mystery and helped the forest together, rather than because she had done everything alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people use markers on a forest trail?",
            answer="Trail markers help walkers recognize the right path, especially where a trail bends or splits.",
        ),
        QAItem(
            question="Why is it useful to share clues when solving a mystery?",
            answer="Different people may notice different details, so sharing clues gives a group more evidence to check before choosing an answer.",
        ),
        QAItem(
            question="What does a superhero do in a story?",
            answer="A superhero uses special abilities and thoughtful choices to help others, often by facing a difficult problem.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story has a mystery and gives its characters a chance to share observations.
team_search(S) :- forest_mystery(S), shares_clue(S).

% The mystery is solved by a team that checks its evidence.
team_solution(S) :- team_search(S), checks_evidence(S), solves_mystery(S).

% A safe, proud finish follows the team's solution.
happy_trail(S) :- team_solution(S), restores_trail(S), hero_proud(S).

% This domain accepts stories that include the mystery, teamwork, solution, and result.
valid_story(S) :- forest_mystery(S), shares_clue(S), checks_evidence(S),
                  solves_mystery(S), restores_trail(S), hero_proud(S).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    params = params or StoryParams()
    if not valid_story(params):
        raise StoryError("Cannot make ASP facts for an invalid story choice.")
    lines = [
        asp.fact("forest_mystery", "story1"),
        asp.fact("shares_clue", "story1"),
        asp.fact("checks_evidence", "story1"),
        asp.fact("solves_mystery", "story1"),
        asp.fact("restores_trail", "story1"),
        asp.fact("hero_proud", "story1"),
    ]
    return "\n".join(lines)


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    cases = [
        StoryParams(seed=i, hero=HEROES[i % len(HEROES)], helper=HELPERS[i % len(HELPERS)],
                    trail=TRAILS[i % len(TRAILS)])
        for i in range(len(MYSTERIES))
    ]
    for params in cases:
        try:
            sample = generate(params)
        except StoryError as exc:
            print(f"Verification failed while generating a story: {exc}")
            return 1
        if not sample.story or len(sample.story_qa) < 4 or not sample.world.facts["mystery_state"].solved:
            print("Verification failed: a generated story was incomplete.")
            return 1
        model = asp.one_model(asp_program("#show valid_story/1.", params))
        atoms = set(asp.atoms(model, "valid_story"))
        py = {("story1",)} if valid_story(params) else set()
        if atoms != py:
            print("MISMATCH between ASP and Python gate.")
            print("ASP:", sorted(atoms))
            print("Python:", sorted(py))
            return 1
    print("OK: ASP/Python parity matches and generated stories passed.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous forest-trail superhero storyworld about Frog-Dim, sharing, and solving a mystery."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trail", choices=TRAILS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    available_helpers = [name for name in HELPERS if name != hero]
    helper = args.helper or rng.choice(available_helpers)
    if helper == hero:
        raise StoryError("The hero and helper must be different characters.")
    trail = args.trail or rng.choice(TRAILS)
    return StoryParams(hero=hero, helper=helper, trail=trail)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:14} ({entity.kind:9}) {' '.join(state)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
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


CURATED = [
    StoryParams(seed=0, hero="Frog-Dim", helper="Pip", trail="Fernbell Trail"),
    StoryParams(seed=1, hero="Captain Croak", helper="Moss", trail="Mossy Loop"),
    StoryParams(seed=2, hero="Lily Leap", helper="Tumble", trail="Blueberry Path"),
    StoryParams(seed=3, hero="Frog-Dim", helper="Tumble", trail="Blueberry Path"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 0:
        raise StoryError("The number of stories must be zero or greater.")
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
