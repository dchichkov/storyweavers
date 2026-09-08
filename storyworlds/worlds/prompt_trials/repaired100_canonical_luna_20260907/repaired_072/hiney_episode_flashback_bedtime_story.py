#!/usr/bin/env python3
"""
A gentle bedtime-story world about a child, a funny hiney episode, and a
flashback that helps turn an embarrassing memory into a kind lesson.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    bedtime_place: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Episode:
    id: str
    place: str
    occasion: str
    mishap: str
    first_feeling: str
    flashback_detail: str
    helpful_action: str
    truth: str
    lesson: str
    ending: str


NAMES = {
    "girl": ["Luna", "Mira", "Nora", "Iris", "Tessa"],
    "boy": ["Leo", "Milo", "Owen", "Theo", "Finn"],
}
COMPANIONS = ["her mother", "her father", "her grandmother", "her grandfather",
              "her older brother", "her older sister"]
PLACES = ["the little bedroom", "the moonlit attic room", "the cozy blue room"]

EPISODES = [
    Episode(
        "painted_stool",
        "the family art room",
        "a rainy afternoon of making star pictures",
        "Luna slipped from a painted stool and landed with a soft plop on her hiney",
        "sure everyone would laugh forever",
        "a flashback to her aunt bringing a cushion and saying that falling only meant she needed a safer place to sit",
        "checking the stool, moving it beside the table, and choosing a cushion",
        "the stool had one loose leg, so the tumble was not Luna's fault",
        "a funny accident can be handled with care instead of shame",
        "the moon outside looked like a small smile above her neatly finished stars",
    ),
    Episode(
        "garden_puddle",
        "the community garden",
        "a morning of watering bean plants",
        "Luna backed into a muddy puddle and splashed her hiney and yellow boots",
        "trying to hide behind the pumpkin leaves",
        "a flashback to a gardener who had laughed kindly, fetched a towel, and helped mark the slippery path",
        "warning the others, drying the path, and putting a bright ribbon beside the puddle",
        "the puddle was hidden by tall leaves, and the warning sign had blown away",
        "telling the truth can help everyone stay safe",
        "clean boots stood by the bed while moonlight silvered the garden ribbon",
    ),
    Episode(
        "picnic_blanket",
        "the park picnic",
        "a family lunch beneath a wide maple tree",
        "Luna sat on a blanket fold and tumbled backward onto her hiney",
        "feeling red-cheeked when the sandwiches wobbled",
        "a flashback to her cousin steadying the basket and saying that even picnics have surprise bumps",
        "smoothing the blanket, sharing the fallen apples, and making a new safe sitting spot",
        "the blanket had been folded under a basket and could not lie flat",
        "kind helpers make a small embarrassment feel small again",
        "the picnic basket rested by the door, and Luna dreamed of apples rolling like red moons",
    ),
    Episode(
        "costume_tail",
        "the bedroom costume corner",
        "a bedtime parade with a soft dragon costume",
        "Luna turned too quickly and sat on the costume's long fabric tail with her hiney",
        "worrying that the dragon parade was ruined",
        "a flashback to her parent tying a loose ribbon into a safe loop and praising her careful asking",
        "shortening the tail, checking the floor, and practicing a slow dragon turn",
        "the tail was too long for the small room",
        "asking for help can turn a tricky moment into a better plan",
        "the dragon costume hung neatly on its hook while Luna slept beneath a blanket of stars",
    ),
    Episode(
        "swinging_cushion",
        "the reading nook",
        "a quiet afternoon of building a pillow fort",
        "Luna missed the cushion and landed on her hiney with a gentle thump",
        "thinking she had spoiled the whole fort",
        "a flashback to her friend placing cushions close together and saying that forts need soft landing places",
        "adding two cushions, testing the floor, and inviting her friend to rebuild",
        "one cushion had slid too far from the fort entrance",
        "a mistake can teach a room how to become kinder and safer",
        "the pillow fort glowed with a night-light like a tiny house for peaceful dreams",
    ),
]

OPENINGS = [
    "Just before bedtime,",
    "On a quiet evening,",
    "When the first star appeared,",
    "After a long day of small adventures,",
]

DIALOGUE = [
    '"Was that the famous hiney episode?" {companion} asked softly.',
    '"It felt enormous," {name} said, rubbing the sore place.',
    '"Let us remember what really happened," {companion} replied.',
    '"I can look again instead of hiding," {name} decided.',
]


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    episode = rng.choice(EPISODES)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUE)

    world = World()
    child = world.add(Entity(params.name, "character", params.gender))
    companion = world.add(Entity("companion", "character", "adult", label=params.companion))
    memory = world.add(Entity("flashback", "thing", "memory", label=episode.flashback_detail))
    body = world.add(Entity("hiney", "thing", "body", label="a safely cared-for hiney"))
    place = world.add(Entity("bedroom", "place", "room", label=params.bedtime_place))

    world.say(
        f"{opening} {params.name} was tucked into {params.bedtime_place} while "
        f"{params.companion} listened to the day's story. Earlier, at {episode.place}, "
        f"{episode.occasion}, and {episode.mishap}."
    )
    world.say(f'{params.companion} noticed {params.name} still looked worried. {dialogue.format(companion=params.companion.capitalize(), name=params.name)}')
    world.say(
        f'"It was a hiney episode, but not a bad-child episode," {params.companion} said. '
        f'"We can look at it gently."'
    )

    world.para()
    world.say(
        f"Then the bedtime story slipped into a Flashback. {params.name} remembered "
        f"{episode.flashback_detail}. The memory made the room feel less dark and the "
        f"problem feel more understandable."
    )
    world.say(
        f'"I remember now," {params.name} whispered. "The important part was what happened next."'
    )
    world.say(
        f'"Exactly," said {params.companion}. "You {episode.helpful_action}."'
    )
    world.say(
        f"Together they saw the truth: {episode.truth}. {params.name} let out a slow breath "
        f"and felt the tight worry loosen."
    )

    world.para()
    world.say(
        f"{params.name} decided that {episode.lesson}. The small episode had changed from a "
        f"scary secret into a story that could help someone else."
    )
    world.say(
        f'"Good night," {params.name} said. "Good night, brave rememberer," replied {params.companion}.'
    )
    world.say(
        f"At last, {episode.ending}. The house grew quiet, and the bedtime story floated "
        f"softly into a peaceful dream."
    )

    child.memes["relief"] = 1.0
    child.memes["self_kindness"] = 1.0
    memory.meters["understood"] = 1.0
    body.meters["safe"] = 1.0
    world.facts.update(
        child=child,
        companion=companion,
        memory=memory,
        body=body,
        place=place,
        episode=episode,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    episode: Episode = world.facts["episode"]
    child: Entity = world.facts["child"]
    return [
        f"Write a gentle bedtime story about {child.id}, a hiney episode, and a helpful Flashback.",
        f"Tell a cozy story in which {child.id} remembers how {episode.truth}.",
        "Write a child-safe bedtime story where a funny accident becomes a lesson in self-kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child: Entity = facts["child"]
    companion: Entity = facts["companion"]
    episode: Episode = facts["episode"]
    return [
        QAItem(
            f"What happened during {child.id}'s hiney episode?",
            f"{episode.mishap}. It happened during {episode.occasion}.",
        ),
        QAItem(
            "What did the Flashback help the child remember?",
            f"The Flashback helped {child.id} remember {episode.flashback_detail}.",
        ),
        QAItem(
            f"How did {companion.label} help?",
            f"{companion.label.capitalize()} helped when they {episode.helpful_action}.",
        ),
        QAItem(
            "What was the truth about the accident?",
            f"The truth was that {episode.truth}.",
        ),
        QAItem(
            "What did the child learn before falling asleep?",
            f"The child learned that {episode.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a flashback?",
            "A flashback is a part of a story that returns to an earlier event so a character or reader can understand it better.",
        ),
        QAItem(
            "Why can bedtime stories use funny accidents?",
            "A bedtime story can use a funny accident to show that mistakes are survivable and that kind helpers can make things feel safe.",
        ),
        QAItem(
            "What does self-kindness mean?",
            "Self-kindness means treating yourself gently when something goes wrong instead of blaming or shaming yourself.",
        ),
        QAItem(
            "Why should an adult help after a tumble?",
            "An adult can check that the child is safe, notice hazards, and help make the place safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
flashback_used :- episode(hiney_episode), memory(understood).
safe_resolution :- flashback_used, body_safe(hiney), kindness(learned).
#show flashback_used/0.
#show safe_resolution/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("episode", "hiney_episode"),
            asp.fact("memory", "understood"),
            asp.fact("body_safe", "hiney"),
            asp.fact("kindness", "learned"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_resolution/0."))
    if asp.atoms(model, "safe_resolution"):
        print("OK: ASP reasoning confirms a safe bedtime resolution.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm a safe bedtime resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime story world with a hiney episode and Flashback.")
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--companion")
    parser.add_argument("--bedtime-place")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    inferred = next((gender for gender, names in NAMES.items() if args.name in names), None)
    gender = args.gender or inferred or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    bedtime_place = args.bedtime_place or rng.choice(PLACES)
    if not name.strip():
        raise StoryError("name must not be empty")
    return StoryParams(name, gender, companion, bedtime_place)


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
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:10}) {' '.join(details)}")
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
    StoryParams("Luna", "girl", "her mother", "the little bedroom", 7101),
    StoryParams("Leo", "boy", "his grandmother", "the moonlit attic room", 7102),
    StoryParams("Mira", "girl", "her father", "the cozy blue room", 7103),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show flashback_used/0. #show safe_resolution/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show flashback_used/0. #show safe_resolution/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
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
