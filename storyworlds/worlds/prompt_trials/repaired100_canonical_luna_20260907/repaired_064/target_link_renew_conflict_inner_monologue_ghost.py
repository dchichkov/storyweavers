#!/usr/bin/env python3
"""A gentle ghost story about a broken link, a lost target, and renewal."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    atmosphere: str
    weather: str


@dataclass
class StoryParams:
    place: str
    target: str
    link: str
    name: str
    friend: str
    ghost: str
    renewal: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class GhostCase:
    missing: str
    conflict: str
    sign: str
    truth: str
    renewal: str
    lesson: str
    ending: str


PLACES = {
    "old_station": Scene("the old station", "dusty and echoing", "a cold drizzle"),
    "moon_library": Scene("the moonlit library", "quiet and silver", "a soft autumn wind"),
    "clock_tower": Scene("the clock tower", "hushed and shadowy", "a pale fog"),
}

TARGETS = {
    "brass_lantern": "the little brass lantern",
    "blue_ribbon": "the blue ribbon",
    "story_key": "the key to the story room",
}

LINKS = {
    "silver_thread": "a silver thread",
    "bell_rope": "the bell rope",
    "paper_chain": "a paper chain",
}

RENEWALS = {
    "mend": "mended the broken link",
    "remember": "remembered the promise attached to it",
    "share": "shared its purpose with someone new",
}

FRIENDS = {"Mara": "girl", "Theo": "boy", "Iris": "girl", "Ned": "boy"}
GHOSTS = {"Lumen": "a small station ghost", "Wisp": "a library ghost", "Echo": "a clock-tower ghost"}

CASES = {
    "brass_lantern": GhostCase(
        "the brass lantern that once guided travelers",
        "Mara said the ghost had hidden it on purpose, while Theo insisted the old caretaker had moved it",
        "a cold glow appeared beneath a loose floorboard",
        "the lantern had slipped through the floor and was still calling for the person who first carried it",
        "cleaned its wick, tied it to a new silver thread, and placed it by the station door",
        "a ghost may be lonely without being dangerous",
        "the lantern shone softly while a new traveler followed its welcoming light",
    ),
    "blue_ribbon": GhostCase(
        "the blue ribbon used to mark the library's welcome chair",
        "Iris blamed the ghost for pulling it from the chair, but Mara thought the wind had taken it",
        "a faint blue reflection trembled inside a closed book",
        "the ribbon had been caught in the book's springy pages when the ghost tried to return it",
        "pressed the ribbon flat, renewed the welcome mark, and invited the ghost to choose the next book",
        "fear can turn a helpful mistake into a frightening story",
        "the blue ribbon rested on the chair as a ghostly page turned by itself",
    ),
    "story_key": GhostCase(
        "the old key that opened the story room",
        "Ned claimed the ghost had stolen it, and the ghost answered with a sharp bang from the tower",
        "the key's tiny chime came from inside a cracked clock case",
        "the key had fallen into the clock and was caught beside a broken gear",
        "lifted the case with care, repaired the clock link, and returned the key to its hook",
        "an angry sound can hide a frightened need",
        "the story-room door opened while the clock ticked in a calm new rhythm",
    ),
}


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


ROUTES = ("whisper_first", "argument_first", "memory_first", "shadow_first", "bell_first")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story about a target, a link, and renewal.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--target", choices=sorted(TARGETS))
    ap.add_argument("--link", choices=sorted(LINKS))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--ghost", choices=sorted(GHOSTS))
    ap.add_argument("--renewal", choices=sorted(RENEWALS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, l) for p in sorted(PLACES) for t in sorted(TARGETS) for l in sorted(LINKS)]


ASP_RULES = """
compatible(Place,Target,Link) :- place(Place), target(Target), link(Link).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", value) for value in PLACES),
            *(asp.fact("target", value) for value in TARGETS),
            *(asp.fact("link", value) for value in LINKS),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.target or combo[1] == args.target
        if not args.link or combo[2] == args.link
    ]
    if not combos:
        raise StoryError("No valid ghost story fits those target, link, and place choices.")
    place, target, link = rng.choice(combos)
    name = args.name or "Luna"
    friends = [f for f in sorted(FRIENDS) if f != name] or sorted(FRIENDS)
    return StoryParams(
        place=place,
        target=target,
        link=link,
        name=name,
        friend=args.friend or rng.choice(friends),
        ghost=args.ghost or rng.choice(sorted(GHOSTS)),
        renewal=args.renewal or rng.choice(sorted(RENEWALS)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.target,
            params.link,
            params.name,
            params.friend,
            params.ghost,
            params.renewal,
            params.route,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = CASES[params.target]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="girl" if params.name in {"Luna", "Mara", "Iris"} else "child",
            memes={"curiosity": 1.0, "courage": 0.0},
        )
    )
    friend = world.add(Entity(id=params.friend, kind="character", type=FRIENDS[params.friend]))
    ghost = world.add(
        Entity(
            id=params.ghost,
            kind="spirit",
            type=GHOSTS[params.ghost],
            label=GHOSTS[params.ghost],
            memes={"loneliness": 1.0, "trust": 0.0},
        )
    )
    target = world.add(
        Entity(
            id=params.target,
            kind="object",
            type="target",
            label=TARGETS[params.target],
            meters={"distance": 4.0, "brightness": 0.2},
        )
    )
    link = world.add(
        Entity(
            id=params.link,
            kind="object",
            type="link",
            label=LINKS[params.link],
            meters={"strength": 0.1},
        )
    )

    opening = {
        "whisper_first": f"At {scene.place}, under {scene.weather}, {hero.id} heard a whisper asking for {TARGETS[params.target]}.",
        "argument_first": f"{hero.id} and {friend.id} were already arguing in {scene.place} when {TARGETS[params.target]} vanished.",
        "memory_first": f"{hero.id} remembered the first time the old ghost had smiled in {scene.place}. Then {TARGETS[params.target]} disappeared.",
        "shadow_first": f"A long shadow crossed {scene.place}, and {hero.id} saw that {TARGETS[params.target]} was gone.",
        "bell_first": f"The {LINKS[params.link]} gave one lonely sound in {scene.place}. When {hero.id} looked up, {TARGETS[params.target]} had vanished.",
    }
    world.say(opening[params.route])
    world.say(
        rng.choice(
            [
                f"{friend.id} took {hero.id}'s hand, though the air felt colder near {ghost.id}.",
                f"{hero.id} tried to be brave, while {friend.id} watched the pale shape by the wall.",
                f"The ghost's outline flickered, as if it were made from moonlight and an unfinished goodbye.",
            ]
        )
    )
    world.para()

    world.say(f"{friend.id} pointed toward the ghost. \"It took {TARGETS[params.target]}!\"")
    world.say(
        f"{hero.id} felt fear prick like frost. *Maybe {friend.id} is right, and maybe the ghost will never let us leave,* {hero.id} thought."
    )
    world.say(
        f'"I did not take it," {ghost.id} whispered. "I tried to return it, but the {LINKS[params.link]} broke."'
    )
    world.say(f"{case.conflict}.")
    hero.memes["courage"] = 1.0
    ghost.memes["trust"] = 0.2
    world.say(
        rng.choice(
            [
                f'"We can be frightened and still listen," {hero.id} said. "{ghost.id}, show us where the link failed."',
                f'"Let us check before we blame anyone," {hero.id} said. {friend.id} lowered their accusing finger.',
                f'{hero.id} swallowed hard. "If you are asking for help, we will hear the whole story."',
            ]
        )
    )
    world.para()

    world.say(f"{ghost.id} drifted toward the forgotten corner, and {hero.id} noticed {case.sign}.")
    world.say(
        f"The clue connected {TARGETS[params.target]} to {LINKS[params.link]}: it was not a haunting trick but a broken promise waiting to be renewed."
    )
    world.say(
        f"*The ghost is not chasing us,* {hero.id} thought. *It is trying to finish something kind.*"
    )
    world.say(f"Together, they discovered the truth: {case.truth}.")
    target.meters["distance"] = 0.0
    link.meters["strength"] = 0.8
    ghost.memes["loneliness"] = 0.3
    world.para()

    world.say(f"{hero.id}, {friend.id}, and {ghost.id} worked together and {case.renewal}.")
    world.say(f"The {params.renewal} in their hearts mattered as much as the repair in their hands.")
    world.say(
        f'"Thank you for staying," {ghost.id} said. "I thought no one remembered." "We remember now," {hero.id} answered.'
    )
    ghost.memes["trust"] = 1.0
    hero.meters["kindness"] = 1.0
    world.say(f"{case.lesson}.")
    world.say(rng.choice([f"At dawn, {case.ending}.", f"When the fog lifted, {case.ending}.", f"After the last ghostly whisper, {case.ending}."]))

    world.facts.update(
        hero=hero,
        friend=friend,
        ghost=ghost,
        target=target,
        link=link,
        case=case,
        scene=scene,
        renewal=params.renewal,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    target = facts["target"].label
    link = facts["link"].label
    return [
        f"Write a gentle ghost story for a child about {target}, {link}, and {facts['hero'].id}.",
        f"Tell a conflict story in which {facts['hero'].id} listens to {facts['ghost'].id} before deciding who caused the broken {link}.",
        f"Write an inner-monologue ghost tale revealing that {case.truth}, ending with {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    hero = facts["hero"].id
    friend = facts["friend"].id
    ghost = facts["ghost"].id
    target = facts["target"].label
    link = facts["link"].label
    return [
        QAItem(
            question=f"What disappeared from {facts['scene'].place}?",
            answer=f"{target} disappeared from {facts['scene'].place}, which started {hero}'s ghostly investigation.",
        ),
        QAItem(
            question=f"Why did {friend} first blame {ghost}?",
            answer=f"{friend} blamed {ghost} because {case.conflict}. The accusation was a guess, not proof.",
        ),
        QAItem(
            question=f"What did {hero} think while the conflict was growing?",
            answer=f"{hero} thought, \"The ghost is not chasing us. It is trying to finish something kind.\" This helped {hero} listen instead of running away.",
        ),
        QAItem(
            question=f"How did the broken {link} explain the missing target?",
            answer=f"The clue showed that {case.truth}. The broken {link} had interrupted the ghost's attempt to return {target}.",
        ),
        QAItem(
            question=f"How was the conflict renewed into friendship?",
            answer=f"{hero}, {friend}, and {ghost} worked together and {case.renewal}. They listened, repaired the link, and remembered that {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a link?",
            answer="A link is something that joins people, objects, or ideas. It can be a thread, a rope, a promise, or a helpful connection.",
        ),
        QAItem(
            question="How can someone handle a conflict fairly?",
            answer="They can pause, listen to each side, check what happened, and repair the harm instead of blaming too quickly.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought. It lets readers understand a feeling or decision that is not spoken aloud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)), "", "== story qa =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  truth={world.facts['case'].truth}")
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="old_station",
        target="brass_lantern",
        link="silver_thread",
        name="Luna",
        friend="Theo",
        ghost="Lumen",
        renewal="mend",
        route="whisper_first",
        seed=11,
    ),
    StoryParams(
        place="moon_library",
        target="blue_ribbon",
        link="paper_chain",
        name="Luna",
        friend="Mara",
        ghost="Wisp",
        renewal="remember",
        route="memory_first",
        seed=22,
    ),
    StoryParams(
        place="clock_tower",
        target="story_key",
        link="bell_rope",
        name="Luna",
        friend="Iris",
        ghost="Echo",
        renewal="share",
        route="bell_first",
        seed=33,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("Generated story verification failed.")
                sys.exit(1)
        print("OK: generated stories pass.")
        return

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for place, target, link in combos:
            print(f"  {place:14} {target:14} {link}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = "### curated story" if args.all else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
