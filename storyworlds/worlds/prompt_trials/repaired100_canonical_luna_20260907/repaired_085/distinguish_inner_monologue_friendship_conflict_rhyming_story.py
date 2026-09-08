#!/usr/bin/env python3
"""A child-safe rhyming storyworld about distinguishing friendship from conflict."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "noise", "tension", "progress"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "calm", "trust", "joy", "surprise"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


@dataclass
class StoryParams:
    hero: str
    friend: str
    place: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Conflict:
    title: str
    task: str
    misunderstanding: str
    clue: str
    repair: str
    lesson: str
    ending: str


CONFLICTS = [
    Conflict(
        "the crooked kite",
        "painting a bright kite for the spring fair",
        "the kite flew away after the friends argued over its tail",
        "one loose blue ribbon was caught on the fence",
        "they listened, retied the tail, and tested the kite together",
        "A disagreement is a problem to solve, not proof that friendship has flown away.",
        "the kite dipped, rose, and danced like a blue bird above the fair",
    ),
    Conflict(
        "the missing rhyme",
        "writing a welcome poem for the class garden",
        "one friend thought the other had erased the best line",
        "a green pencil mark showed that the line was hidden beneath a fold",
        "they unfolded the page, apologized, and made the couplet sing",
        "Questions can distinguish a mistake from an unkind act.",
        "their poem rhymed on the garden gate while bees hummed near the flowers",
    ),
    Conflict(
        "the wobbly bridge",
        "building a block bridge for toy animals",
        "the bridge fell when both friends reached for the same block",
        "the heavy blocks belonged at the bottom, not the top",
        "they shared the blocks and rebuilt from a steady foundation",
        "Taking turns can turn a clash into teamwork.",
        "the toy deer crossed safely as the little bridge held firm",
    ),
    Conflict(
        "the red paint splash",
        "decorating a sign for the neighborhood reading corner",
        "a red splash made one friend suspect the other had spoiled the sign",
        "the paint jar had tipped beside an uneven table leg",
        "they cleaned the spill, steadied the table, and painted a new sign",
        "An accident needs care, while deliberate harm needs a different response.",
        "the new sign shone red and gold beneath the library window",
    ),
    Conflict(
        "the shared drum",
        "practicing a rhythm for the school parade",
        "both friends pulled the drum because each thought the other was refusing to share",
        "the practice card showed that they had different starting turns",
        "they read the card aloud and played alternating beats",
        "Clear words help friends distinguish a mix-up from a quarrel.",
        "their two drumsticks tapped one happy rhythm down the sunny street",
    ),
    Conflict(
        "the scattered shells",
        "sorting shells for a seaside science display",
        "a gust scattered the shells just after one friend moved the tray",
        "sand beneath the tray made it tilt when the wind blew",
        "they moved indoors and sorted the shells by color",
        "Blame grows smaller when careful observation finds the real cause.",
        "pink, white, and golden shells made a calm beach inside the room",
    ),
]


HEROES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Arlo"]
FRIENDS = ["Maya", "Finn", "Zoe", "Eli", "Ruby", "Owen"]
PLACES = ["the school courtyard", "the community art room", "the sunny library", "the village green"]
OBJECTS = ["a paper kite", "a folded poem", "a block bridge", "a painted sign", "a parade drum", "a shell tray"]


def choose_conflict(seed: Optional[int]) -> Conflict:
    if seed is None:
        return CONFLICTS[0]
    return CONFLICTS[seed % len(CONFLICTS)]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("hero and friend must have different names")
    if not params.hero or not params.friend:
        raise StoryError("hero and friend names cannot be empty")
    conflict = choose_conflict(params.seed)
    world = World(place=params.place)

    hero = world.add(Entity(params.hero, "character", "child", params.hero))
    friend = world.add(Entity(params.friend, "character", "child", params.friend))
    prop = world.add(Entity("shared_object", "object", "project", params.object_name, owner=None))
    hero.memes.update(worry=1.0, trust=0.5)
    friend.memes.update(worry=1.0, trust=0.5)
    prop.meters.update(tension=1.0, progress=0.2)

    world.say(f"In {params.place}, {params.hero} and {params.friend} worked on {params.object_name}.")
    world.say(f"They planned to {conflict.task}, with a tune in the air and a moon-bright flair.")
    world.say(f"Then came {conflict.title}: {conflict.misunderstanding}.")
    world.say(
        f'"You did it!" cried {params.hero}. "Wait," said {params.friend}. '
        f'"Let us ask before we decide what happened."'
    )
    world.say(
        f"{params.hero} thought, *I feel cross and small, but I do not know the whole story at all.* "
        f"That quiet inner voice helped {params.hero} pause."
    )
    world.say(f"They looked closely and found that {conflict.clue}.")
    world.say(
        f'"We had a conflict, not a friendship end," said {params.hero}. '
        f'"I trust you," replied {params.friend}. "Let us mend this together, too."'
    )
    world.say(f"Together they {conflict.repair}.")
    world.say(f"The tension eased, their progress grew, and the shared project became bright and true.")
    world.say(f"{params.hero} said, '"{conflict.lesson}"')
    world.say(f"At the end, {conflict.ending}.")
    world.say(
        f"The friends smiled in the gentle light: they could distinguish a hurt feeling from a harmful deed, "
        f"and choose kind words to make things right."
    )

    hero.memes.update(worry=0.0, calm=1.0, trust=1.0, joy=1.0)
    friend.memes.update(worry=0.0, calm=1.0, trust=1.0, joy=1.0)
    prop.meters.update(tension=0.0, progress=1.0)
    world.facts.update(
        hero=hero,
        friend=friend,
        prop=prop,
        conflict=conflict,
        clue=conflict.clue,
        resolved=True,
        friendship_preserved=True,
        child_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    conflict = world.facts["conflict"]
    return [
        'Write a child-safe rhyming story using the word "distinguish."',
        f"Tell a story about {world.facts['hero'].id} and {world.facts['friend'].id} facing {conflict.title}.",
        "Include inner monologue, friendship, conflict, dialogue, a careful discovery, and a kind repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    conflict = world.facts["conflict"]
    return [
        QAItem(
            f"What were {hero.id} and {friend.id} doing?",
            f"They were working together to {conflict.task}. Their shared project gave them a reason to cooperate.",
        ),
        QAItem(
            f"What caused the conflict between {hero.id} and {friend.id}?",
            f"The conflict began with this misunderstanding: {conflict.misunderstanding}.",
        ),
        QAItem(
            "What clue helped them understand the problem?",
            f"They found that {conflict.clue}. That clue showed that their first assumption was incomplete.",
        ),
        QAItem(
            f"How did {hero.id} and {friend.id} repair their friendship?",
            f"They {conflict.repair}. They used calm words, listened, and worked together again.",
        ),
        QAItem(
            "What did the friends learn?",
            f"They learned that {conflict.lesson}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does distinguish mean?",
            "To distinguish means to notice or explain how two things are different.",
        ),
        QAItem(
            "What is inner monologue?",
            "Inner monologue is a character's private thought. It lets readers hear what the character is thinking inside.",
        ),
        QAItem(
            "What is a conflict?",
            "A conflict is a problem or disagreement between people or forces. It can be handled with listening, evidence, and respectful choices.",
        ),
        QAItem(
            "How can friendship survive a disagreement?",
            "Friends can pause, speak honestly without blaming, listen to each other, and repair the problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    conflict = world.facts["conflict"]
    lines.append(f"conflict: {conflict.title}")
    lines.append(f"resolved: {world.facts['resolved']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming friendship conflict storyworld.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = rng.choice(HEROES)
    friend = rng.choice([name for name in FRIENDS if name != hero])
    return StoryParams(
        hero=hero,
        friend=friend,
        place=rng.choice(PLACES),
        object_name=rng.choice(OBJECTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


ASP_RULES = """
place(school_courtyard).
feature(inner_monologue).
feature(friendship).
feature(conflict).
style(rhyming_story).
theme(distinguish).
resolved :- feature(inner_monologue), feature(friendship), feature(conflict), theme(distinguish).
safe_friendship :- resolved.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("place", "school_courtyard"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "friendship"),
        asp.fact("feature", "conflict"),
        asp.fact("style", "rhyming_story"),
        asp.fact("theme", "distinguish"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        symbols = asp.one_model(asp_program("#show resolved/0.\n#show safe_friendship/0."))
        names = {symbol.name for symbol in symbols}
        if not {"resolved", "safe_friendship"}.issubset(names):
            return 1
    except Exception:
        return 1

    for seed in range(len(CONFLICTS)):
        params = StoryParams(
            hero="Luna",
            friend="Maya",
            place="the school courtyard",
            object_name="a paper kite",
            seed=seed,
        )
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            return 1
        if "distinguish" not in sample.story:
            return 1
        if len(sample.story_qa) < 3:
            return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp or args.asp:
        print(asp_program("#show place/1.\n#show resolved/0.\n#show safe_friendship/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [
            generate(
                StoryParams(
                    hero="Luna",
                    friend="Maya",
                    place="the school courtyard",
                    object_name="a paper kite",
                    seed=index,
                )
            )
            for index in range(len(CONFLICTS))
        ]
    else:
        samples = []
        for offset in range(max(1, args.n)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
