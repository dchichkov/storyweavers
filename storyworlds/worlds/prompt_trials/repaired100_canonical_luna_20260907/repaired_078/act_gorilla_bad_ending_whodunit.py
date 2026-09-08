#!/usr/bin/env python3
"""A child-friendly whodunit about an act, a gorilla, and a bad ending."""
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))
from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "The Gorilla's Missing Act"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective: str = "Luna"
    gorilla: str = "Bobo"
    place: str = "the Moonbeam Theater"
    act: str = "the banana-juggling act"
    culprit: str = "the windy stage door"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CASES = [
    {
        "act": "the banana-juggling act",
        "culprit": "the windy stage door",
        "clue": "a yellow peel lay beside the door, although Bobo always kept his peels in a red bucket",
        "mistake": "Luna blamed Bobo because one banana was missing",
        "bad": "the curtain rose before Luna checked the stage door, and the wind scattered the props across the floor",
        "fix": "Luna followed the peel trail, shut the loose door, and found the missing banana behind a sandbag",
        "ending": "the audience saw a messy pile of bananas instead of Bobo's smooth juggling act",
    },
    {
        "act": "the drum-and-dance act",
        "culprit": "a loose curtain cord",
        "clue": "three drumbeats had rolled toward the curtain, where a fresh knot was pulled crooked",
        "mistake": "Luna questioned Bobo but ignored the crooked knot",
        "bad": "the curtain cord tugged the drum away during the act, and the dance stopped with a loud bump",
        "fix": "Luna traced the cord, tied it safely, and placed the drum back on its marked spot",
        "ending": "the final dance ended in silence while the fallen drum rested under the curtain",
    },
    {
        "act": "the moon-mask magic act",
        "culprit": "a cracked prop box",
        "clue": "silver glitter leaked from a crack leading from the box to the empty mask hook",
        "mistake": "Luna decided that Bobo had hidden the mask as a joke",
        "bad": "the act began without the mask, and the magic trick revealed only an empty hook",
        "fix": "Luna followed the glitter, opened the cracked box, and found the mask beneath a folded cape",
        "ending": "the audience watched a magic act with no moon-mask surprise",
    },
    {
        "act": "the red-ball balancing act",
        "culprit": "a tilted prop shelf",
        "clue": "dust made a straight line beneath the shelf, ending where the missing ball should have been",
        "mistake": "Luna searched Bobo's costume instead of checking the shelf",
        "bad": "the shelf tipped during the act, and the red balls rolled into the audience",
        "fix": "Luna steadied the shelf, followed the dust line, and recovered the ball from behind a trunk",
        "ending": "the balancing act became a chase after rolling red balls",
    },
]

DETECTIVES = ["Luna", "Mira", "Nico"]
GORILLAS = ["Bobo", "Kito", "Zuri"]
PLACES = ["the Moonbeam Theater", "the Lantern Hall", "the Little Comet Circus"]


def validate(params: StoryParams) -> None:
    if params.detective == params.gorilla:
        raise StoryError("The detective and gorilla must be different characters.")
    if not params.act.strip():
        raise StoryError("The act must not be empty.")
    if not params.place.strip():
        raise StoryError("The setting must not be empty.")


def choose_case(params: StoryParams) -> dict:
    seed = params.seed if params.seed is not None else 0
    return CASES[seed % len(CASES)]


def tell(params: StoryParams) -> World:
    validate(params)
    case = choose_case(params)
    world = World()
    detective = world.add(Entity("detective", "character", params.detective))
    gorilla = world.add(Entity("gorilla", "animal", params.gorilla))
    stage = world.add(Entity("stage", "place", params.place))
    prop = world.add(Entity("prop", "thing", params.act))
    detective.memes.update(curiosity=1.0, confidence=0.0)
    gorilla.memes.update(worry=1.0, trust=1.0)
    prop.meters.update(ready=1.0, evidence=0.0)
    world.facts.update(case=case, detective=detective, gorilla=gorilla, stage=stage, prop=prop)
    world.say(
        f"At {params.place}, {params.detective} was the young detective for the evening show. "
        f"{params.gorilla} the gorilla was ready to perform {params.act}."
    )
    world.say(
        f"Just before the curtain, the main prop vanished. {case['clue'].capitalize()}."
    )
    world.para()
    world.say(
        f'"Did you take it, {params.gorilla}?" {params.detective} asked. '
        f'"No," said {params.gorilla}. "I was warming up beside the painted moon."'
    )
    world.say(
        f"{params.detective} hurried and {case['mistake']}. "
        "Bobo's worried face made the question harder, but it was not proof."
    )
    detective.memes["confidence"] = 0.2
    gorilla.memes["worry"] = 0.8
    prop.meters["evidence"] = 0.3
    world.fired.add("suspect_without_proof")
    world.para()
    world.say(
        f'"Wait," said {params.gorilla}. "A real detective checks every clue." '
        f'"You are right," said {params.detective}. "Show me what I missed."'
    )
    world.say(
        f"{params.detective} followed the clue toward {case['culprit']}, but the stage manager called, "
        "and the curtain began to rise."
    )
    world.say(
        f"That was the bad ending: {case['bad']} "
        f"{params.detective} had almost solved the mystery, but waiting too long let the wrong moment arrive."
    )
    detective.memes["confidence"] = 0.5
    gorilla.memes["worry"] = 1.0
    prop.meters["ready"] = 0.0
    world.fired.add("bad_ending")
    world.para()
    world.say(
        f"Afterward, {params.detective} found the truth anyway. {case['fix'].capitalize()}."
    )
    world.say(
        f'"Next time, I will listen before I accuse," {params.detective} told {params.gorilla}. '
        f'"And next time," said {params.gorilla}, "we will test the stage before the curtain rises."'
    )
    world.say(
        f"The lights dimmed on {case['ending']}. "
        "The mystery was solved, but the missing clue had taught Luna that a correct answer found too late can still lead to a bad ending."
    )
    prop.meters["ready"] = 1.0
    prop.meters["evidence"] = 1.0
    detective.memes["curiosity"] = 1.0
    gorilla.memes["trust"] = 1.0
    world.fired.add("mystery_solved_after_bad_ending")
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a whodunit for children about {facts['detective'].label} investigating a missing prop from {facts['prop'].label}.",
        f"Include {facts['gorilla'].label}, a clue involving {case['culprit']}, and a bad ending caused by acting too late.",
        "Show dialogue in which the gorilla changes the detective's decision, even though the first performance still goes badly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    detective = facts["detective"].label
    gorilla = facts["gorilla"].label
    return [
        QAItem(
            question=f"What was {detective} investigating?",
            answer=f"{detective} was investigating the missing prop for {facts['prop'].label} at {facts['stage'].label}.",
        ),
        QAItem(
            question=f"Why did {detective} first suspect {gorilla}?",
            answer=f"{detective} made a quick guess because the prop was missing, but that guess was not proof. {gorilla} said they had been warming up beside the painted moon.",
        ),
        QAItem(
            question="What clue pointed toward the real cause?",
            answer=f"The clue was that {case['clue']}. It led toward {case['culprit']} rather than toward the gorilla.",
        ),
        QAItem(
            question="What made the ending bad?",
            answer=f"The curtain rose before the investigation was finished, so {case['bad']}",
        ),
        QAItem(
            question="What lesson did the detective learn?",
            answer=f"The detective learned to listen and check every clue before accusing someone, because solving a mystery too late can still cause a bad ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a whodunit?", answer="A whodunit is a mystery story in which characters look for clues to discover who caused a problem."),
        QAItem(question="What is an act?", answer="An act is a planned performance, such as juggling, dancing, drumming, or magic."),
        QAItem(question="How can a detective investigate fairly?", answer="A detective can listen to each person, compare clues, and avoid accusing anyone without evidence."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("role", "detective"),
        asp.fact("role", "gorilla"),
        asp.fact("clue", "evidence"),
        asp.fact("outcome", "bad_ending"),
        "listens.",
        "checks_clues.",
    ]
    return "\n".join(lines)


ASP_RULES = r"""
mystery_ready :- role(detective), clue(evidence), listens, checks_clues.
bad_story :- outcome(bad_ending), not mystery_ready.
lesson :- mystery_ready.
#show mystery_ready/0.
#show bad_story/0.
#show lesson/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery_ready/0. #show bad_story/0. #show lesson/0."))
    if asp.atoms(model, "mystery_ready") and asp.atoms(model, "bad_story") and asp.atoms(model, "lesson"):
        for seed in range(8):
            sample = generate(StoryParams(seed=seed))
            if "bad ending" not in sample.story.lower():
                print("ASP verification failed: generated story lacks the required bad ending.")
                return 1
        print("OK: ASP and Python agree on the mystery, bad ending, and lesson.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Whodunit story world about an act and a gorilla.")
    parser.add_argument("--detective", choices=DETECTIVES, default=None)
    parser.add_argument("--gorilla", choices=GORILLAS, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--act", choices=[c["act"] for c in CASES], default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        detective=args.detective or rng.choice(DETECTIVES),
        gorilla=args.gorilla or rng.choice(GORILLAS),
        place=args.place or rng.choice(PLACES),
        act=args.act or rng.choice([c["act"] for c in CASES]),
        seed=args.seed,
    )


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
    StoryParams(detective="Luna", gorilla="Bobo", place="the Moonbeam Theater", act="the banana-juggling act", seed=0),
    StoryParams(detective="Mira", gorilla="Kito", place="the Lantern Hall", act="the drum-and-dance act", seed=1),
    StoryParams(detective="Nico", gorilla="Zuri", place="the Little Comet Circus", act="the moon-mask magic act", seed=2),
    StoryParams(detective="Luna", gorilla="Zuri", place="the Moonbeam Theater", act="the red-ball balancing act", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_ready/0. #show bad_story/0. #show lesson/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show mystery_ready/0. #show bad_story/0. #show lesson/0."))
        for predicate in ("mystery_ready", "bad_story", "lesson"):
            print(asp.atoms(model, predicate))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.detective} / {sample.params.gorilla} / {sample.params.act}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
