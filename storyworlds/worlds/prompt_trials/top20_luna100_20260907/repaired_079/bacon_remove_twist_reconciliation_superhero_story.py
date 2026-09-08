#!/usr/bin/env python3
"""
A child-facing superhero storyworld about bacon, a dangerous breakfast beacon,
a surprising twist, and reconciliation.
"""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    city_name: str = "Brighton"
    diner_name: str = "The Golden Pan"


HERO_NAMES = ["Luna", "Nova", "Zara", "Kai", "Milo", "Juno", "Rex", "Tess"]
CITY_NAMES = ["Brighton", "Sunbeam City", "Moonrise", "Maple Harbor"]
DINER_NAMES = ["The Golden Pan", "Rocket Diner", "The Blue Spoon", "Sunny Skillet"]

INCIDENTS = [
    {
        "threat": "a runaway bacon-powered breakfast robot",
        "wrong": "Luna thought Milo had stolen the bacon and chased him away from the diner",
        "twist": "the missing bacon had been placed inside the robot as its emergency fuel",
        "action": "remove the bacon from the robot's warm engine with a pair of silver tongs",
        "rescue": "the robot stopped before it could crash into the school parade",
        "ending": "the friends served the rescued bacon on small plates while the robot folded napkins",
        "lesson": "A hero should ask what happened before choosing someone to blame",
    },
    {
        "threat": "a giant bacon balloon floating above the city festival",
        "wrong": "Luna tried to pop it, while Milo shouted that the bacon should be removed first",
        "twist": "the balloon was not a villain's weapon; it was carrying a lost puppy in a basket",
        "action": "remove the sharp fireworks from its ropes and guide it gently toward the park",
        "rescue": "the puppy landed safely beside its worried owner",
        "ending": "the festival lights glowed below them as Luna and Milo shared a quiet apology",
        "lesson": "Careful listening can turn a frightening picture into a rescue",
    },
    {
        "threat": "a smoky bacon cloud covering the town library",
        "wrong": "Luna blamed Milo's new smoke machine and ordered him to leave",
        "twist": "the cloud came from a cooking lesson that had lost its vent fan",
        "action": "remove the blocked vent cover and open every library window",
        "rescue": "the smoke cleared before the books were harmed",
        "ending": "the librarian invited both friends to finish the cooking lesson together",
        "lesson": "Reconciliation begins when people examine the real problem together",
    },
    {
        "threat": "a bacon-shaped comet racing toward the playground",
        "wrong": "Luna pulled Milo away from the controls because she believed he had changed the route",
        "twist": "Milo had changed it to steer the comet away from a crowded hospital",
        "action": "remove the comet's sticky sugar fins while Milo guided its harmless landing",
        "rescue": "the comet splashed into an empty field as bright breakfast crumbs",
        "ending": "the playground reopened, and Luna gave Milo the first crispy crumb",
        "lesson": "A teammate's strange choice may hide a brave reason",
    },
]

MODES = [
    ("The city woke beneath a bright blue sky, but its breakfast trouble was already growing.", "That mistake taught Luna to slow down before using her powers."),
    ("Luna's cape fluttered over the rooftops as the first alarm rang.", "A true rescue needed more than strength; it needed trust."),
    ("The morning looked ordinary until the smell of bacon curled through the streets.", "The surprise forced both friends to look past their first guesses."),
]


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(params.hero_name, "character", "hero", params.hero_name))
    friend = world.add(Entity(params.friend_name, "character", "friend", params.friend_name))
    city = world.add(Entity("city", "place", "city", params.city_name))
    bacon = world.add(Entity("bacon", "thing", "food", "bacon"))
    alarm = world.add(Entity("alarm", "thing", "signal", "hero alarm"))

    hero.meters.update(courage=1.0, power=1.0)
    hero.memes.update(trust=0.4, worry=0.2)
    friend.meters.update(inventiveness=1.0)
    friend.memes.update(hurt=0.0, trust=0.6)
    bacon.meters.update(safety=1.0, usefulness=1.0)
    alarm.memes["urgency"] = 1.0

    world.facts.update(hero=hero, friend=friend, city=city, bacon=bacon, alarm=alarm)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join([params.hero_name, params.friend_name, params.city_name, params.diner_name])
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    token = _token(params)
    incident = INCIDENTS[token % len(INCIDENTS)]
    mode = MODES[(token // len(INCIDENTS)) % len(MODES)]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    city = world.facts["city"]
    bacon = world.facts["bacon"]

    world.say(mode[0])
    world.say(
        f"{hero.label}, the superhero of {city.label}, patrolled above {params.diner_name} "
        f"with {friend.label}, who knew how to fix almost anything."
    )
    world.say(f"Then the alarm cried out: {incident['threat']} was heading toward the city, powered by a sizzling smell of bacon.")

    world.say(
        f"{hero.label} saw {friend.label} near the danger and decided too quickly that {incident['wrong']}."
    )
    world.say(f'"Wait!" {friend.label} called. "You do not know the whole story."')
    world.say(f'"I have to protect everyone," {hero.label} answered. "I cannot risk waiting."')
    world.say(mode[1])

    world.say(
        f"The first rescue attempt went badly. {hero.label}'s cape gusted through the street, "
        f"and the bacon-powered trouble grew louder instead of smaller."
    )
    world.say(
        f"Just before the disaster reached the city square, {friend.label} pointed to a hidden panel. "
        f"The twist was that {incident['twist']}."
    )
    world.say(f'"So you were trying to help?" {hero.label} asked.')
    world.say(f'"Yes," {friend.label} said. "But I should have explained before changing anything."')

    world.say(
        f"Together they {incident['action']}. "
        f"{incident['rescue']} The danger faded, and the smell of bacon became warm and delicious instead of frightening."
    )
    world.say(f"{hero.label} lowered the cape. 'I am sorry I blamed you without asking.'")
    world.say(f"{friend.label} smiled. 'I am sorry I kept my plan secret. Next time, we tell each other the whole truth.'")
    world.say(
        f"The reconciliation mattered as much as the rescue: {incident['lesson']}. "
        f"At {params.diner_name}, {incident['ending']}."
    )

    hero.memes["trust"] = 1.0
    hero.memes["worry"] = 0.0
    friend.memes["hurt"] = 0.0
    friend.memes["trust"] = 1.0
    bacon.meters["safety"] = 1.0
    world.fired.update({
        ("twist_revealed",),
        ("bacon_removed",),
        ("rescue_complete",),
        ("reconciliation",),
    })
    world.facts.update(
        params=params,
        incident=incident,
        incident_index=token % len(INCIDENTS),
        mode_index=(token // len(INCIDENTS)) % len(MODES),
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a superhero story about {p.hero_name}, {p.friend_name}, bacon, and a danger in {p.city_name}.",
        f"Show how {p.hero_name} makes a mistaken accusation, discovers that {incident['twist']}, and works with {p.friend_name}.",
        "Include a clear twist, a bacon-related rescue, spoken dialogue, and reconciliation between two friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"Who protected {p.city_name}?",
            answer=f"{p.hero_name}, a superhero, protected {p.city_name} with help from {p.friend_name}.",
        ),
        QAItem(
            question="What danger threatened the city?",
            answer=f"The danger was {incident['threat']}.",
        ),
        QAItem(
            question="What mistake did the hero make?",
            answer=f"{p.hero_name} decided too quickly that {incident['wrong']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {incident['twist']}.",
        ),
        QAItem(
            question="How did the friends stop the danger?",
            answer=f"Together they {incident['action']}, and then {incident['rescue'].lower()}",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"{p.hero_name} apologized for blaming {p.friend_name}, and {p.friend_name} admitted that the plan should have been explained earlier. They promised to tell each other the whole truth.",
        ),
        QAItem(
            question="What lesson did the rescue teach?",
            answer=f"It taught that {incident['lesson'].lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bacon?",
            answer="Bacon is a food usually made from cured pork and cooked until it is tender or crisp.",
        ),
        QAItem(
            question="Why might someone remove bacon from a machine?",
            answer="Someone might remove bacon from a machine to stop it from blocking, overheating, or powering the wrong part.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing a relationship after people understand a mistake, apologize, and make a better plan.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero uses special abilities, courage, and good judgment to help people and protect them from danger.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- alarm(S), bacon_threat(S), blamed_friend(S).
twist(S) :- hidden_reason(S), confused(S).
bacon_removed(S) :- twist(S), remove_action(S).
rescue_complete(S) :- bacon_removed(S), danger_stopped(S).
reconciliation(S) :- apology(S), promise_truth(S).
valid_story(S) :- rescue_complete(S), reconciliation(S).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("alarm", "story1"),
        asp.fact("bacon_threat", "story1"),
        asp.fact("blamed_friend", "story1"),
        asp.fact("hidden_reason", "story1"),
        asp.fact("remove_action", "story1"),
        asp.fact("danger_stopped", "story1"),
        asp.fact("apology", "story1"),
        asp.fact("promise_truth", "story1"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about bacon, removal, a twist, and reconciliation."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--friend-name", choices=HERO_NAMES)
    parser.add_argument("--city-name", choices=CITY_NAMES)
    parser.add_argument("--diner-name", choices=DINER_NAMES)
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
    hero = args.hero_name or rng.choice(HERO_NAMES)
    possible = [name for name in HERO_NAMES if name != hero]
    friend = args.friend_name or rng.choice(possible)
    return StoryParams(
        seed=None,
        hero_name=hero,
        friend_name=friend,
        city_name=args.city_name or rng.choice(CITY_NAMES),
        diner_name=args.diner_name or rng.choice(DINER_NAMES),
    )


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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    StoryParams(hero_name="Luna", friend_name="Milo", city_name="Brighton", diner_name="The Golden Pan"),
    StoryParams(hero_name="Nova", friend_name="Juno", city_name="Moonrise", diner_name="Rocket Diner"),
    StoryParams(hero_name="Zara", friend_name="Kai", city_name="Maple Harbor", diner_name="Sunny Skillet"),
]


def main() -> None:
    args = build_parser().parse_args()

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
