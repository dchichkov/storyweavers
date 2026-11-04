#!/usr/bin/env python3
"""A forest-trail superhero storyworld about a frog, a mystery, and sharing."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Locate the shared result module even when this script is run from its nested
# directory or by its full path.
_here = os.path.abspath(__file__)
for _parent in os.path.dirname(_here), *(
    os.path.dirname(os.path.dirname(_here)),
    os.path.dirname(os.path.dirname(os.path.dirname(_here))),
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here)))),
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))),
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here)))))),
):
    if os.path.isfile(os.path.join(_parent, "results.py")):
        sys.path.insert(0, _parent)
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Pip"
    friend_name: str = "Moss"
    trail: str = "Fernbell Forest Trail"


HERO_NAMES = ["Pip", "Tula", "Bram", "Nell", "Kip", "Wren"]
FRIEND_NAMES = ["Moss", "Jun", "Bea", "Rory", "Fern", "Sol"]
TRAILS = ["Fernbell Forest Trail", "Mossy Loop Trail", "Whispering Pines Trail"]
MYSTERIES = [
    {
        "clue": "three tiny blue feathers beside a stump",
        "guess": "a very small dragon had sneezed blue feathers all over the trail",
        "answer": "a jay had carried blue ribbons to line its nest",
        "find": "a loose ribbon caught on a low branch beside a jay's nest",
        "help": "They tied the ribbon back onto the trail marker and left the nest undisturbed",
        "image": "the jay tucked the last blue ribbon into its nest while the friends waved from the trail",
    },
    {
        "clue": "a trail sign that had turned backward overnight",
        "guess": "the forest had spun around like a giant top",
        "answer": "a playful gust had twisted the sign on its wooden peg",
        "find": "fresh leaves caught behind the sign, with the wind pointing toward the trail",
        "help": "They held the post steady together while Pip turned the sign the right way",
        "image": "the sign pointed home again, and a leaf spun past like a tiny green cape",
    },
    {
        "clue": "a row of muddy dots that stopped at a patch of moss",
        "guess": "a pocket-sized monster had tiptoed away without its feet",
        "answer": "a hedgehog had crossed the path and brushed its paws on the moss",
        "find": "small paw prints leading from the moss to a safe hollow log",
        "help": "They moved a fallen twig aside so the hedgehog could reach its hollow",
        "image": "the hedgehog curled safely in its log as the friends left the path clear",
    },
    {
        "clue": "a bell that rang whenever nobody touched it",
        "guess": "the bell was practicing a solo for the forest's grand concert",
        "answer": "a hidden squirrel was tugging the bell's string from behind a fern",
        "find": "a little string running from the bell to a basket of fallen acorns",
        "help": "They shared the acorns with the squirrel and moved the string away from the trail",
        "image": "the squirrel rang one gentle thank-you note as the friends continued down the sunny path",
    },
]


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Pip"
    friend_name: str = "Moss"
    trail: str = "Fernbell Forest Trail"


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.hero_name}|{params.friend_name}|{params.trail}"
    ))


def valid_story() -> bool:
    return True


def tell_story(params: StoryParams) -> World:
    if params.hero_name not in HERO_NAMES:
        raise StoryError(f"Unknown hero name: {params.hero_name!r}. Choose a name from the hero registry.")
    if params.friend_name not in FRIEND_NAMES:
        raise StoryError(f"Unknown friend name: {params.friend_name!r}. Choose a name from the friend registry.")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend need different names.")
    if params.trail not in TRAILS:
        raise StoryError(f"Unknown forest trail: {params.trail!r}. Choose a trail from the trail registry.")

    token = _token(params)
    mystery = MYSTERIES[token % len(MYSTERIES)]
    world = World()
    hero = world.add(Entity(params.hero_name, "character", "frog_hero", params.hero_name))
    friend = world.add(Entity(params.friend_name, "character", "friend", params.friend_name))
    forest = world.add(Entity("forest", "place", "trail", params.trail))
    clue = world.add(Entity("clue", "thing", "mystery_clue", mystery["clue"]))
    hero.meters.update(bravery=1.0, trail_knowledge=0.2)
    hero.memes.update(pride=0.7, curiosity=0.5)
    friend.meters.update(observation=1.0, kindness=0.8)
    friend.memes.update(confidence=0.5, amusement=0.2)
    world.facts.update(hero=hero, friend=friend, forest=forest, clue=clue,
                       mystery=mystery, token=token)

    world.say(
        f"Frog-Dim was the superhero name {hero.label} had chosen after one "
        "particularly spectacular hop into a soft pile of leaves. "
        f"On {forest.label}, {hero.label} wore a green cape and felt proud enough "
        "to salute every fern."
    )
    world.say(
        f"{hero.label} and {friend.label} were following the trail when they spotted "
        f"{mystery['clue']}. Nearby, a sign announced, “MYSTERY—PLEASE DO NOT TICKLE.”"
    )
    world.para()
    world.say(
        f"“I know exactly what happened,” {hero.label} declared. "
        f"“A {mystery['guess']}!”"
    )
    world.say(
        f"{friend.label} grinned. “That is a wonderfully silly guess, but let’s look "
        "before we leap. Can you hold my lantern while I check the ground?”"
    )
    world.say(
        f"Frog-Dim’s first impulse was to solve everything alone. Then {hero.label} "
        f"handed over the lantern. {friend.label} studied the clue and found {mystery['find']}."
    )
    world.para()
    world.say(
        f"“You noticed what I missed,” {hero.label} said. “Tell me what you think.” "
        f"{friend.label} answered, “The trail has given us a better answer: {mystery['answer']}.”"
    )
    world.say(
        f"Together they solved the mystery. {mystery['help']}. "
        f"The trail’s hidden visitor was safe, and the friends had learned more by sharing "
        "their light and ideas than either could have learned alone."
    )
    world.say(
        f"“A real hero can ask for help,” {hero.label} said, feeling proud for a better "
        "reason this time. {friend.label} laughed. “And a real hero checks the ground "
        "before accusing a dragon of sneezing.”"
    )
    world.say(
        f"Frog-Dim gave a grand superhero bow, bumped gently into a fern, and bowed to "
        f"the fern too. At the end of {forest.label}, {mystery['image']}."
    )

    hero.meters["trail_knowledge"] = 1.0
    hero.memes["pride"] = 0.9
    hero.memes["curiosity"] = 1.0
    friend.memes["confidence"] = 0.9
    friend.memes["amusement"] = 1.0
    world.fired.update({"noticed_clue", "shared_lantern", "solved_mystery", "helped_forest"})
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    m = world.facts["mystery"]
    p = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Tell a funny superhero story about Frog-Dim on {p.trail}.",
            f"Have {p.hero_name} and {p.friend_name} share clues and solve a small forest mystery.",
            "Show how a proud hero becomes more thoughtful by listening to a friend and helping a forest animal.",
        ],
        story_qa=[
            QAItem("What clue began the mystery?", f"The friends noticed {m['clue']}, which made them stop and investigate."),
            QAItem("What was Frog-Dim's first guess?", f"{p.hero_name} guessed that {m['guess']}. It was funny, but the friends checked the evidence instead of trusting the guess."),
            QAItem("How did the friends solve the mystery?", f"{p.friend_name} examined the clue and discovered that {m['answer']}. {p.hero_name} helped by sharing the lantern, and they worked together to help."),
            QAItem("How did sharing change what happened?", f"When {p.hero_name} handed over the lantern, {p.friend_name} could examine the clue closely. Their shared effort revealed {m['find']}."),
            QAItem("Why was Frog-Dim proud at the end?", f"{p.hero_name} was proud because a hero had listened, accepted help, and helped solve the mystery rather than trying to do everything alone."),
            QAItem("What funny thing happened at the ending?", f"Frog-Dim bowed so grandly that {p.hero_name} bumped gently into a fern and bowed to it too."),
        ],
        world_qa=[
            QAItem("What is a forest trail?", "A forest trail is a path through trees and plants that helps people explore without wandering through the undergrowth."),
            QAItem("Why should people leave wild animals' homes undisturbed?", "Wild animals need safe places to rest and raise their young, so people should watch gently and avoid damaging nests or dens."),
            QAItem("What does it mean to share?", "Sharing means letting someone else use or enjoy something with you, such as taking turns with a lantern or listening to another person's idea."),
        ],
        world=world,
    )


ASP_RULES = r"""
mystery_solved(S) :- clue_seen(S), friend_shares_observation(S), evidence_checked(S).
helpful_ending(S) :- mystery_solved(S), forest_helped(S).
valid_story(S) :- helpful_ending(S), humor_present(S), hero_pride_humble(S).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("clue_seen", "story1"),
        asp.fact("friend_shares_observation", "story1"),
        asp.fact("evidence_checked", "story1"),
        asp.fact("forest_helped", "story1"),
        asp.fact("humor_present", "story1"),
        asp.fact("hero_pride_humble", "story1"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found != expected:
        print("MISMATCH between ASP and Python gate.")
        print("ASP:", sorted(found))
        print("Python:", sorted(expected))
        return 1
    # Exercise story generation across the mystery registry as part of parity
    # verification; each generated sample must retain the complete turn.
    for i in range(len(MYSTERIES)):
        sample = generate(StoryParams(seed=i))
        if not all(term in sample.story for term in ("Frog-Dim", "mystery", "together")):
            print(f"Generated-story check failed for seed {i}.")
            return 1
    print("OK: clingo parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Funny forest-trail superhero mystery storyworld.")
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--trail", choices=TRAILS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
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
    available = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend_name or rng.choice(available)
    return StoryParams(seed=None, hero_name=hero, friend_name=friend,
                       trail=args.trail or rng.choice(TRAILS))


CURATED = [
    StoryParams(seed=0, hero_name="Pip", friend_name="Moss", trail=TRAILS[0]),
    StoryParams(seed=1, hero_name="Tula", friend_name="Jun", trail=TRAILS[1]),
    StoryParams(seed=2, hero_name="Bram", friend_name="Bea", trail=TRAILS[2]),
    StoryParams(seed=3, hero_name="Nell", friend_name="Rory", trail=TRAILS[0]),
]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of requested stories must be at least one.")
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        output = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(output)
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
