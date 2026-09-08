#!/usr/bin/env python3
"""A child-facing pirate tale world about a historic shutter, friendship, and problem solving."""

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

ROOT = Path(__file__).resolve().parents[3]
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
class Port:
    place: str
    weather: str
    mood: str


@dataclass
class StoryParams:
    port: str
    shutter: str
    captain: str
    friend: str
    problem: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    missing: str
    worry: str
    test: str
    failed: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, port: Port) -> None:
        self.port = port
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


PORTS = {
    "harbor": Port("the old harbor", "salt-bright", "busy and brave"),
    "cove": Port("the hidden cove", "windy", "hushed and curious"),
    "dock": Port("the wooden dock", "misty", "creaky and calm"),
}
SHUTTERS = {
    "historic": "a historic shutter with brass paint and carved waves",
    "oak": "an oak shutter with a star-shaped latch",
    "blue": "a blue shutter striped like a sailor's flag",
}
CAPTAINS = {"Mira": "girl", "Toby": "boy", "Nia": "girl", "Finn": "boy"}
FRIENDS = {"Rae": "girl", "Pip": "boy", "Lina": "girl", "Joss": "boy"}

TALKS = {
    "rope": Tale(
        "the rope ladder for the lighthouse",
        "the crew feared they could not reach the lantern room before dusk",
        "tested the ladder one rung at a time with a sack of sand",
        "the rope held, but the ladder still scraped the wrong side of the wall",
        "a salt-stiff thread snagged on the historic shutter's edge",
        "the ladder had been tied to the shutter, which swung and blocked the climb",
        "moved the knot to a firm post and guided the ladder free",
        "a good helper checks the whole path, not only the strongest rope",
        "the ladder climbed straight up beside the shining lighthouse",
    ),
    "chart": Tale(
        "the map to the safe channel",
        "the tide was rising and the crew needed the correct turn quickly",
        "checked the map against the rocks and counted three dark posts",
        "the posts matched, but the water still curled the wrong way",
        "a wet line of ink bent under the shutter frame like a hook",
        "the map had been folded backward behind the shutter and read from the wrong side",
        "unfolded the chart, pressed it flat, and marked the true turn",
        "friends who compare notes can solve a problem faster than friends who guess",
        "the ship glided through the safe channel as gulls circled above",
    ),
    "lantern": Tale(
        "the deck lantern for the night watch",
        "the crew could not agree who had taken it",
        "traced the light's last path with a hand over the rail",
        "the path ended at an empty hook, which did not answer the question",
        "a bright reflection flashed through the historic shutter slats",
        "the lantern had rolled into a sheltered nook and shone through the slats",
        "retrieved it gently and added a hook with a deeper lip",
        "looking for the final place of an object can be kinder than blaming a friend",
        "the lantern glowed safely while the crew shared watch duty",
    ),
    "flag": Tale(
        "the ship's small signal flag",
        "the captain worried the harbor master would think they had sailed away",
        "checked every line that could have pulled the flag loose",
        "none of the knots had broken, so the first idea failed",
        "a fringe of salt blew across the shutter and caught the flag's corner",
        "the wind had tucked the flag behind the open shutter and pinned it there",
        "closed the shutter partway, freed the flag, and tied it to a higher line",
        "small changes in wind can cause big surprises on a ship",
        "the flag snapped once above the mast and everyone laughed in relief",
    ),
    "barrel": Tale(
        "the water barrel for the cabin plants",
        "the plants drooped while the barrel seemed strangely light",
        "measured the barrel and listened for a drip",
        "the drip came from the roof, not from the barrel itself",
        "a pale trail curled from the shutter hinge to the floorboards",
        "rain had run through a cracked seal and hid behind the shutter",
        "sealed the crack with pitch and moved the barrel away from the wall",
        "steady repairs keep a shipfriend safe and a plant alive",
        "the plants stood up tall beside a dry, mended barrel",
    ),
    "bell": Tale(
        "the little bell that called the crew to supper",
        "hunger made everyone grumpy and the bell was nowhere to be seen",
        "listened for the faintest ring and followed the sound",
        "the ring stopped at the pantry door, which was not the end of the search",
        "a shining hook mark lined up with the shutter latch",
        "the bell had caught on the shutter while someone opened the pantry",
        "lifted it free and hung it on a safer nail",
        "a fair search can calm a ship faster than a loud accusation",
        "the supper bell rang clear while friends passed warm bread",
    ),
}
ROUTES = ("first_light", "dialogue_first", "map_first", "test_first", "wind_first", "memory_first", "two_theories", "quiet_first")
PROBLEMS = tuple(sorted(TALKS))
ASP_RULES = "valid(Port, Problem) :- port(Port), problem(Problem)."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale world with a historic shutter and friendship.")
    ap.add_argument("--port", choices=sorted(PORTS))
    ap.add_argument("--shutter", choices=sorted(SHUTTERS))
    ap.add_argument("--captain")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(p, pr) for p in sorted(PORTS) for pr in sorted(PROBLEMS)]


def asp_facts() -> str:
    import asp
    return "\n".join([*(asp.fact("port", p) for p in PORTS), *(asp.fact("problem", pr) for pr in PROBLEMS)])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/2.")), "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if (not args.port or c[0] == args.port) and (not args.problem or c[1] == args.problem)]
    if not combos:
        raise StoryError("No valid pirate tale fits those options.")
    port, problem = rng.choice(combos)
    captain = args.captain or "Mira"
    others = [f for f in sorted(FRIENDS) if f != captain] or sorted(FRIENDS)
    return StoryParams(
        port=port,
        shutter=args.shutter or rng.choice(sorted(SHUTTERS)),
        captain=captain,
        friend=args.friend or rng.choice(others),
        problem=problem,
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (params.seed, params.port, params.shutter, params.captain, params.friend, params.problem, params.route))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    port, tale, rng = PORTS[params.port], TALKS[params.problem], story_rng(params)
    world = World(port)
    captain = world.add(Entity(id=params.captain, kind="character", type="pirate"))
    friend = world.add(Entity(id=params.friend, kind="character", type=FRIENDS[params.friend]))
    shutter = world.add(Entity(id=params.shutter, kind="object", type="shutter", label=SHUTTERS[params.shutter]))
    opening = {
        "first_light": f"At {port.place}, {captain.id} spotted {SHUTTERS[params.shutter]} on a weather-worn wall. It was a historic shutter, and beside it was trouble: {tale.missing}.",
        "dialogue_first": f'"Wait," {captain.id} said at {port.place}. "{tale.missing.capitalize()} is missing, but we should not blame the sea too fast." {friend.id} nodded at the historic shutter nearby.',
        "map_first": f"{captain.id} spread a little map on a barrel at {port.place}. The map showed the dock, the shutters, and the place where {tale.missing} should have been.",
        "test_first": f"The crew of friends liked to solve problems by testing clues. That morning, {tale.missing} was gone from {port.place}, and the historic shutter looked important.",
        "wind_first": f"The wind whipped across {port.place}, rattling every board. {tale.missing.capitalize()} had vanished, and the historic shutter creaked like it knew why.",
        "memory_first": f"Later, {friend.id} would remember the salty hush at {port.place}. First there was a missing {tale.missing}, then a glance at the historic shutter.",
        "two_theories": f"Two ideas sailed into the same storm at {port.place}: the tide took {tale.missing}, or a mistake hid it. {captain.id} found the historic shutter between them.",
        "quiet_first": f"Nothing looked wrong at first at {port.place}. Then {friend.id} pointed at an empty spot where {tale.missing} should have been, right beside the historic shutter.",
    }
    world.say(opening[params.route])
    world.say(rng.choice([
        f'{friend.id} whispered, "Let us check, not guess."',
        f'{captain.id} answered, "A good crew solves the problem together."',
        f'The two friends leaned close and said, "We can find it if we follow the clues."',
        f'{friend.id} said, "I will hold the lantern, and you look high and low."',
    ]))
    world.para()
    world.say(rng.choice([
        f"A worry started when someone blamed the wind because {tale.worry}.",
        f"One sailor pointed and said, \"The sea did it,\" because {tale.worry}.",
        f"A grumpy voice blamed the nearest helper, since {tale.worry}.",
        f"The blame drifted toward the crew before anyone had checked the facts, because {tale.worry}.",
    ]))
    world.say("That made the harbor tense, but the friends stayed gentle and kept working.")
    captain.memes["calm"] = 1
    friend.memes["friendship"] = 1
    world.say(rng.choice([
        f'"Being near the problem is not the same as causing it," {captain.id} said.',
        f'"We should solve this fairly," {friend.id} said, standing beside the accused helper.',
        f'{captain.id} tapped the chart. "First we test the idea. Then we speak."',
        f'{friend.id} smiled. "A friend helps with the truth, not with a guess."',
    ]))
    world.para()
    world.say(f"First, {captain.id} {tale.test}. But {tale.failed}.")
    world.say(rng.choice([
        f"That failed test did not end the search; it only showed where the answer was not hiding.",
        f"{friend.id} crossed out the wrong idea and looked again with bright eyes.",
        f"The mistake made the crew quieter, which helped them notice the next clue.",
        f'The friends said, "That one does not fit," and turned toward the shutter.',
    ]))
    world.say(f"Then they found the clue: {tale.clue}.")
    world.say(rng.choice([
        f"{captain.id} traced it with one finger and saw how it pointed to the real answer.",
        f"{friend.id} lifted the shutter just enough to peek behind it without breaking it.",
        f"Working together, they followed the clue from the floor to the wall and back again.",
        f"The clue matched the wind, the wall, and the missing item all at once.",
    ]))
    world.para()
    world.say(f"The truth was that {tale.truth}. The historic shutter had helped hide the mistake, but it was not to blame.")
    shutter.meters["openings"] = 1
    world.say(rng.choice([
        f"The crew apologized, then {tale.repair}.",
        f"With the problem solved, the friends {tale.repair}.",
        f"After the apology, everyone worked together to {tale.repair}.",
        f"The harbor grew calm again when they all {tale.repair}.",
    ]))
    world.say(f"{captain.id} remembered the lesson: {tale.lesson}.")
    world.say(rng.choice([
        f"At last, {tale.ending}.",
        f"When the sun leaned low, {tale.ending}.",
        f"By evening, {tale.ending}.",
        f"Before the next watch began, {tale.ending}.",
    ]))
    world.facts.update(
        captain=captain,
        friend=friend,
        shutter=shutter,
        port=port,
        tale=tale,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f, t = world.facts, world.facts["tale"]
    return [
        f"Write a short pirate tale for a child about {f['captain'].id}, friendship, and a historic shutter at {f['port'].place}.",
        f"Tell a problem-solving story in which {f['captain'].id} and {f['friend'].id} test a clue before deciding what happened to {t.missing}.",
        f"Write a gentle sea-faring adventure that ends with {t.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f, t = world.facts, world.facts["tale"]
    return [
        QAItem(
            question=f"What went missing at {f['port'].place} when {f['captain'].id} noticed the historic shutter?",
            answer=f"{t.missing.capitalize()} went missing at {f['port'].place}, which started the problem-solving adventure.",
        ),
        QAItem(
            question=f"How did {f['friend'].id} help {f['captain'].id} when people began to blame the wrong thing?",
            answer=f"{f['friend'].id} stayed calm, said to check the facts, and helped protect the search from unfair blame.",
        ),
        QAItem(
            question=f"What was the first test {f['captain'].id} tried, and why did it not solve the mystery?",
            answer=f"{f['captain'].id} {t.test}, but {t.failed}. That meant the crew needed a new idea.",
        ),
        QAItem(
            question=f"Which clue finally showed the truth about the historic shutter?",
            answer=f"The clue was {t.clue}. It led the friends to learn that {t.truth}.",
        ),
        QAItem(
            question=f"How did the friends end the story after the problem was solved?",
            answer=f"They repaired things by {t.repair} and remembered that {t.lesson}. The ending image was {t.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is friendship useful in a problem-solving story?",
            answer="Friends can share ideas, calm each other down, and check clues together so a guess does not turn into unfair blame.",
        ),
        QAItem(
            question="What makes a clue better than a rumor?",
            answer="A clue is something you can test against the scene, while a rumor is just a claim. Good stories follow clues, not gossip.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel that can cover a window or opening. It can move, swing, or hide things behind it.",
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
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  truth={world.facts['tale'].truth}")
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
    StoryParams(port="harbor", shutter="historic", captain="Mira", friend="Rae", problem="rope", route="first_light", seed=11),
    StoryParams(port="cove", shutter="oak", captain="Toby", friend="Pip", problem="chart", route="dialogue_first", seed=22),
    StoryParams(port="dock", shutter="blue", captain="Nia", friend="Lina", problem="lantern", route="quiet_first", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for port, problem in combos:
            print(f"  {port:8} {problem}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples, seen, attempts = [], set(), 0
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header="### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
