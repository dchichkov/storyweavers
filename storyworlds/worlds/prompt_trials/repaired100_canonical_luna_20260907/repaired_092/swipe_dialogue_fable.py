#!/usr/bin/env python3
"""A child-friendly fable about a swipe, a fair question, and a changed heart."""

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Tale:
    key: str
    place: str
    treasure: str
    owner: str
    swipe: str
    clue: str
    question: str
    truth: str
    repair: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Pip"
    elder: str = "the old owl"
    tale: str = "berry_crown"
    mood: str = "golden"
    narrative_mode: int = 0
    dialogue_mode: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


TALES = {
    "berry_crown": Tale(
        key="berry_crown",
        place="a sunny woodland clearing",
        treasure="a crown woven from red berries",
        owner="the young deer",
        swipe="Luna's paw made a quick swipe, and the berry crown vanished beneath her leaf cloak",
        clue="a red berry rolled from the cloak and stopped beside the old owl's stone",
        question="Did you see the crown fall, or did you see Luna take it?",
        truth="the crown had snagged on a thorn when Luna reached for a fallen leaf, and the quick swipe only pulled it free",
        repair="Luna returned the crown, helped weave a stronger vine through it, and admitted what she had done",
        ending="the deer wore the mended crown while Luna carried the loose berries to every hungry bird",
        lesson="A quick swipe may hide a mistake, but an honest word can begin to mend it.",
    ),
    "moon_ribbon": Tale(
        key="moon_ribbon",
        place="a quiet meadow under a pale moon",
        treasure="a silver ribbon tied to the rabbit's gate",
        owner="the moon rabbit",
        swipe="Luna's wing made a playful swipe, and the silver ribbon fluttered into the tall grass",
        clue="a bright thread shone between two bent reeds",
        question="What did you notice before the ribbon flew?",
        truth="the ribbon was already loose, and Luna's swipe only showed the weak knot",
        repair="Luna found a smooth reed, retied the ribbon, and asked before touching another creature's things",
        ending="the ribbon shone at the gate while Luna waited for the rabbit's nod before helping",
        lesson="Permission makes helping kind instead of surprising.",
    ),
    "acorn_token": Tale(
        key="acorn_token",
        place="an oak grove beside a little stream",
        treasure="the squirrel's polished acorn token",
        owner="the busy squirrel",
        swipe="Luna's tail gave a careless swipe, and the polished acorn skittered toward the stream",
        clue="three tiny marks crossed the dust beside the water",
        question="Could the marks show where the acorn came from rather than who pushed it?",
        truth="a beetle had loosened the acorn from its nest, and Luna's swipe had merely sent it farther",
        repair="Luna fetched it with a twig, apologized, and built a small rim around the nest",
        ending="the squirrel placed the token safely inside while Luna watched the stream carry only fallen leaves",
        lesson="Before blaming a friend, look for the smaller cause hiding nearby.",
    ),
}


OPENINGS = (
    "In a bright little forest, every creature believed that a good name was worth more than a fine treasure.",
    "One golden morning, Luna learned that even a gentle heart can make a clumsy mistake.",
    "The woodland was peaceful until one quick movement made several friends wonder what had happened.",
    "Among the ferns and flowers, a small fable began with a treasure, a question, and a nervous silence.",
)

DIALOGUES = (
    (
        '"I saw a swipe, but I did not see a theft," said Pip.',
        '"Then we must ask before we accuse," replied the old owl.',
        '"I was reaching for the leaf," Luna said. "I should have spoken sooner."',
    ),
    (
        '"A mark can tell us where to look," said Pip, "but not whom to blame."',
        '"Good," said the old owl. "Let the truth have room to walk."',
        '"Please listen," Luna said. "My quick paw caused trouble, though not in the way you thought."',
    ),
    (
        '"Did you see the whole event?" Pip asked.',
        '"No," admitted the old owl. "I saw only the ending."',
        '"Then I will tell the whole truth," said Luna. "I made a swipe, and I will help repair what followed."',
    ),
)

ASP_RULES = r"""
object(X) :- object_fact(X).
owner(O) :- owner_fact(O).
swipe_event(T) :- swipe_fact(T).
honest_repair(T) :- repair_fact(T).
safe_story(T) :- tale_fact(T), swipe_fact(T), repair_fact(T).
"""


OBJECTS = {
    "berry_crown": "berry_crown",
    "moon_ribbon": "moon_ribbon",
    "acorn_token": "acorn_token",
}


def asp_facts() -> str:
    import asp

    lines = []
    for key in TALES:
        tale = TALES[key]
        lines.extend(
            (
                asp.fact("tale_fact", key),
                asp.fact("object_fact", OBJECTS[key]),
                asp.fact("owner_fact", tale.owner.replace(" ", "_")),
                asp.fact("swipe_fact", key),
                asp.fact("repair_fact", key),
            )
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A dialogue-rich fable about a thoughtful swipe.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--elder")
    parser.add_argument("--tale", choices=sorted(TALES))
    parser.add_argument("--mood", choices=("golden", "quiet", "breezy", "warm"))
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
    if args.n is not None and args.n < 1:
        raise StoryError("-n must be at least 1")
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(("Luna", "Milo", "Nia")),
        helper=args.helper or rng.choice(("Pip", "Tavi", "Moss")),
        elder=args.elder or rng.choice(("the old owl", "Grandmother Badger", "the patient tortoise")),
        tale=args.tale or rng.choice(list(TALES)),
        mood=args.mood or rng.choice(("golden", "quiet", "breezy", "warm")),
        narrative_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
    )


def tell(params: StoryParams) -> World:
    if params.tale not in TALES:
        raise StoryError(f"unknown tale: {params.tale}")
    tale = TALES[params.tale]
    world = World()

    hero = world.add(Entity(params.hero, "character", "young_animal", params.hero, memes={"honesty": 1.0, "worry": 0.4}))
    helper = world.add(Entity(params.helper, "character", "friend", params.helper, memes={"fairness": 1.0}))
    elder = world.add(Entity("elder", "character", "wise_helper", params.elder, memes={"patience": 2.0}))
    treasure = world.add(Entity("treasure", "object", "keepsake", tale.treasure, meters={"distance": 0.0, "security": 0.2}))

    world.say(OPENINGS[params.narrative_mode])
    world.say(f"On a {params.mood} day, {params.hero} visited {tale.place}. There, {tale.owner} proudly showed everyone {tale.treasure}.")
    world.say(f"Then {tale.swipe}. The treasure moved, and the clearing grew still.")
    world.para()

    world.say(f"{params.helper} noticed that {tale.clue}.")
    for line in DIALOGUES[params.dialogue_mode]:
        world.say(line)
    world.say(f"The question changed the search: {tale.question}")
    world.say(f"When they looked carefully, they discovered that {tale.truth}.")
    world.say("The first guess faded, because a clue could describe a movement without proving a motive.")
    world.para()

    world.say(f"{params.hero} lowered her head, then chose honesty. {tale.repair}.")
    world.say(f"{tale.owner.capitalize()} accepted the repair, and the woodland's worried silence softened.")
    world.say(f"As the sun dipped behind the trees, {tale.ending}.")
    world.say(f"The old wisdom was clear: {tale.lesson}")

    treasure.meters.update(distance=1.0, security=1.0)
    hero.memes.update(honesty=2.0, worry=0.0, care=2.0)
    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        treasure=treasure,
        tale=tale,
        swipe=tale.swipe,
        truth=tale.truth,
        repair=tale.repair,
        lesson=tale.lesson,
    )
    world.trace.extend(
        (
            f"swipe:{tale.key}",
            f"clue:{tale.clue}",
            f"question:{tale.question}",
            f"truth:{tale.truth}",
            f"repair:{tale.repair}",
            "ending:honest_repair",
        )
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a child-friendly fable about {hero.label}, a quick swipe, and {tale.treasure}.",
        "Include dialogue in which a character separates an observation from an accusation.",
        f"Reveal that {tale.truth}, then end with a concrete repair and a moral.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question="What happened at the beginning of the fable?",
            answer=f"{hero.label} made a quick swipe, and {tale.treasure} moved unexpectedly.",
        ),
        QAItem(
            question="What clue helped the friends investigate?",
            answer=f"They noticed that {tale.clue}, which gave them a place to look without blaming anyone.",
        ),
        QAItem(
            question=f"How did {helper.label}'s words change the investigation?",
            answer=f"{helper.label} reminded everyone that seeing a swipe was not the same as seeing a theft, so the friends asked a fair question.",
        ),
        QAItem(
            question="What was the truth?",
            answer=f"They discovered that {tale.truth}.",
        ),
        QAItem(
            question="How did the problem end?",
            answer=f"{hero.label} made things right: {tale.repair}.",
        ),
        QAItem(
            question="What is the fable's lesson?",
            answer=tale.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    return [
        QAItem(
            question="Why should a person ask questions before blaming someone?",
            answer="A quick movement or clue may have more than one cause. Asking questions helps separate what was observed from what was only guessed.",
        ),
        QAItem(
            question="What makes an apology useful?",
            answer="A useful apology names the mistake, tells the truth, and includes a real effort to repair the harm.",
        ),
        QAItem(
            question="What kind of change does this fable show?",
            answer=f"The important change is from worry and suspicion to honesty and care, shown when the treasure is repaired: {tale.repair}.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        lines.append(f"  {entity.id} ({entity.kind}/{entity.type}) meters={entity.meters} memes={entity.memes}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(tale="berry_crown", hero="Luna", helper="Pip", elder="the old owl"),
    StoryParams(tale="moon_ribbon", hero="Nia", helper="Tavi", elder="Grandmother Badger", narrative_mode=2, dialogue_mode=1),
    StoryParams(tale="acorn_token", hero="Milo", helper="Moss", elder="the patient tortoise", narrative_mode=3, dialogue_mode=2),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    show = "#show object/1.\n#show owner/1.\n#show swipe_event/1.\n#show honest_repair/1.\n#show safe_story/1.\n"
    model = asp.one_model(asp_program(show))
    if not model:
        print("ASP produced no model.")
        return 1
    atoms = asp.atoms(model, "safe_story")
    if len(atoms) != len(TALES):
        print("ASP parity check failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "swipe" not in sample.story.lower() or not sample.story_qa:
            print("Story verification failed.")
            return 1
    print("OK: ASP and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    show = "#show object/1.\n#show owner/1.\n#show swipe_event/1.\n#show honest_repair/1.\n#show safe_story/1.\n"

    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP unavailable: {exc}") from exc
        model = asp.one_model(asp_program(show))
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(args.n):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
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
