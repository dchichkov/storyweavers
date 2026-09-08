#!/usr/bin/env python3
"""A child-facing mystery world about a mechanism, friendship, caution, and a twist."""

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
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    missing: str
    mechanism: str
    friend: str
    witness: str
    suspect: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryBeat:
    opening: str
    accusation: str
    test: str
    failed: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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


PLACES = {
    "garden": Scene("the garden", "leafy and bright", "a warm breeze"),
    "library": Scene("the library", "quiet and twinkly", "soft afternoon light"),
    "workshop": Scene("the workshop", "busy and tidy", "dusty sunbeams"),
    "pond": Scene("the pond", "still and green", "a silver drizzle"),
}

PEOPLE = {
    "Mina": "girl",
    "Theo": "boy",
    "Iris": "girl",
    "Ned": "boy",
    "Luca": "boy",
    "Pia": "girl",
}

SUSPECTS = {
    "cat": "cat",
    "duck": "duck",
    "raccoon": "raccoon",
    "frog": "frog",
}

MISSING = {
    "bells": "the silver bells",
    "crayons": "the red crayons",
    "buttons": "the jar of buttons",
    "seeds": "the seed packets",
    "maps": "the paper maps",
}

MECHANISMS = {
    "spinning_hook": "a spinning hook mechanism",
    "sliding_latch": "a sliding latch mechanism",
    "windup_cart": "a windup cart mechanism",
    "pulley_box": "a pulley box mechanism",
    "turntable": "a turntable mechanism",
}

BEATS = {
    "bells": MysteryBeat(
        opening="When the day began, {hero} noticed the silver bells were gone from the display shelf at {scene}.",
        accusation='"The {suspect} must have taken them," someone said, because {accusation}.',
        test="{hero} tied a ribbon to the shelf and watched the mechanism move",
        failed="but the ribbon did not travel toward the {suspect}; it swung toward the back wall instead",
        clue="a twist of string was caught in the {mechanism}",
        truth="the bells had rolled under the shelf when the mechanism bumped a tray, and nobody had stolen them",
        repair="{friend} and {hero} lifted the shelf, found the bells, and set a soft stopper beside the mechanism",
        lesson="a quick guess can sound clever, but a careful test tells the true story",
        ending="the silver bells rested safely in a bowl, and the soft stopper kept the shelf from bumping again",
    ),
    "crayons": MysteryBeat(
        opening="At {scene}, the red crayons vanished from the art basket just before painting time.",
        accusation='"The {suspect} did it," a child whispered, because {accusation}.',
        test="{hero} checked the basket and watched the mechanism with a paper strip",
        failed="but the strip slipped down the wrong side, so the first idea could not be right",
        clue="tiny red dust specks were stuck inside the {mechanism}",
        truth="the crayons had dropped into a hidden drawer when the cart hit the table leg",
        repair="{friend} and {hero} opened the drawer, returned the crayons, and added a gentle brake",
        lesson="friends should protect each other from blame until the facts are clear",
        ending="the art basket was full again, and the gentle brake made the cart glide slowly",
    ),
    "buttons": MysteryBeat(
        opening="Near the window at {scene}, the jar of buttons had disappeared from the low table.",
        accusation='"It has to be the {suspect}," said one neighbor, because {accusation}.',
        test="{hero} marked the floor with chalk and watched the mechanism roll past",
        failed="but the chalk line stayed clean, so the first path was a false trail",
        clue="one bright button was caught beneath the {mechanism}",
        truth="the jar had tipped when the wind pushed the curtain into the table",
        repair="{friend} and {hero} rescued the jar, straightened the curtain, and closed the latch",
        lesson="a mystery can have a twist that points away from the loudest rumor",
        ending="the buttons shone in their jar while the curtain stayed neatly tied back",
    ),
    "seeds": MysteryBeat(
        opening="In the garden shed, the seed packets were missing from the blue box.",
        accusation='"The {suspect} must be guilty," someone said, because {accusation}.',
        test="{hero} set a cup beneath the mechanism and waited for a trace to fall",
        failed="but nothing fell there, so the first guess lost its hold",
        clue="a thin trail of dirt ran through the {mechanism}",
        truth="the packets had slipped into the watering shelf when the latch opened too fast",
        repair="{friend} and {hero} sorted the packets, closed the latch gently, and labeled every shelf",
        lesson="caution keeps a small accident from becoming an unfair accusation",
        ending="the seed packets stood in tidy rows, and the labeled shelves looked proud and calm",
    ),
    "maps": MysteryBeat(
        opening="At {scene}, the paper maps vanished from the travel board right before the club meeting.",
        accusation='"The {suspect} did it," a voice said, because {accusation}.',
        test="{hero} turned the mechanism one click at a time and listened",
        failed="but the sound came from an empty hinge, not from the missing maps",
        clue="a folded corner was tucked under the {mechanism}",
        truth="the maps had slipped behind the board when the turntable spun too quickly",
        repair="{friend} and {hero} pulled the maps free and added a slower setting",
        lesson="friendship means slowing down together when a surprise might hurt someone",
        ending="the maps hung flat again, and the slow setting made the turntable hum softly",
    ),
}

ROUTES = ("clue_first", "dialogue_first", "witness_first", "mistake_first", "quiet_first", "twist_first")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery world about a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing", choices=sorted(MISSING))
    ap.add_argument("--mechanism", choices=sorted(MECHANISMS))
    ap.add_argument("--friend", choices=sorted(PEOPLE))
    ap.add_argument("--witness", choices=sorted(PEOPLE))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, mech) for p in sorted(PLACES) for m in sorted(MISSING) for mech in sorted(MECHANISMS)]


ASP_RULES = """
valid(Place, Missing, Mechanism) :- place(Place), missing(Missing), mechanism(Mechanism).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", p) for p in PLACES),
            *(asp.fact("missing", m) for m in MISSING),
            *(asp.fact("mechanism", mech) for mech in MECHANISMS),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c
        for c in valid_combos()
        if (not args.place or c[0] == args.place)
        and (not args.missing or c[1] == args.missing)
        and (not args.mechanism or c[2] == args.mechanism)
    ]
    if not combos:
        raise StoryError("No valid story fits those options.")
    place, missing, mechanism = rng.choice(combos)
    friend = args.friend or rng.choice(sorted(PEOPLE))
    witness = args.witness or rng.choice([p for p in sorted(PEOPLE) if p != friend])
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    return StoryParams(place=place, missing=missing, mechanism=mechanism, friend=friend, witness=witness, suspect=suspect)


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (params.seed, params.place, params.missing, params.mechanism, params.friend, params.witness, params.suspect))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    beat = BEATS[params.missing]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(Entity(id="hero", kind="character", type="child", label="child detective"))
    friend = world.add(Entity(id=params.friend, kind="character", type=PEOPLE[params.friend]))
    witness = world.add(Entity(id=params.witness, kind="character", type=PEOPLE[params.witness]))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=SUSPECTS[params.suspect]))
    mechanism = world.add(Entity(id=params.mechanism, kind="mechanism", type="mechanism"))
    hero.memes["careful"] = 1
    friend.memes["loyal"] = 1
    suspect.memes["blamed"] = 1

    opening_choices = [
        beat.opening.format(hero=hero.id, scene=scene.place),
        f"At {scene.place}, {hero.id} found a strange problem near {params.mechanism.replace('_', ' ')} and knew it was time to ask questions.",
        f"Something small had gone missing at {scene.place}, and the clue was tied to {params.mechanism.replace('_', ' ')}.",
        f"On a bright day at {scene.place}, {hero.id}, {friend.id}, and {witness.id} faced a mystery with a twist.",
    ]
    world.say(rng.choice(opening_choices))
    world.say(f"{friend.id} stayed close and said, \"We can solve it together.\" {hero.id} answered, \"Then we will be careful and fair.\"")
    world.para()
    world.say(beat.accusation.format(suspect=params.suspect, accusation=f"{params.suspect} tracks were seen near the shelf"))
    world.say(f"{witness.id} frowned, but {friend.id} said, \"A nearby shape is not the whole answer.\"")
    world.say(f"That warning kept the friendship steady while the rumor tried to turn into blame.")
    world.para()
    world.say(f"First, {hero.id} {beat.test}.")
    world.say(f"Still, {beat.failed}.")
    world.say(f"Then came the twist: {beat.clue.format(mechanism=params.mechanism.replace('_', ' '))}.")
    world.say(f"{friend.id} gasped. \"So the mechanism moved it!\" {hero.id} nodded. \"That explains the missing piece.\"")
    world.para()
    world.say(f"The truth was that {beat.truth}.")
    world.say(f"{witness.id} apologized to the {params.suspect} for the unfair guess, and {friend.id} and {hero.id} {beat.repair}.")
    world.say(f"{hero.id} wrote the lesson in the notebook: {beat.lesson}.")
    world.say(f"By the end, {beat.ending}.")
    mechanism.meters["safe_setting"] = 1
    mechanism.memes["slow"] = 1
    world.facts.update(
        hero=hero,
        friend=friend,
        witness=witness,
        suspect=suspect,
        mechanism=mechanism,
        beat=beat,
        scene=scene,
        missing=params.missing,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly mystery about {f['hero'].id}, {f['friend'].id}, and a {f['mechanism'].id} at {f['scene'].place}.",
        f"Include a cautious test, an unfair accusation, and a twist that explains why {f['missing']} vanished.",
        f"End with friendship, apology, and a clear image showing what changed at {f['scene'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    beat: MysteryBeat = f["beat"]
    return [
        QAItem(
            question=f"What went missing in the story?",
            answer=f"The missing item was {f['missing'].replace('_', ' ')}. That loss started the mystery at {f['scene'].place}.",
        ),
        QAItem(
            question=f"Why did people first blame the {f['suspect'].type}?",
            answer=f"They noticed {f['suspect'].type} tracks nearby, but that was only a rumor, not proof.",
        ),
        QAItem(
            question="How did the hero test the mystery before deciding?",
            answer=f"{f['hero'].id} {beat.test}. The first test failed, so the friends looked for a better clue.",
        ),
        QAItem(
            question="What was the twist clue?",
            answer=f"The twist clue was {beat.clue.format(mechanism=f['mechanism'].id.replace('_', ' '))}. It showed the mechanism had moved the missing item.",
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"{f['friend'].id} helped {f['hero'].id} stay calm, ask fair questions, and repair the mistake after the truth was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should children be cautious before blaming someone?",
            answer="Because a clue near someone does not always mean they caused the problem. Careful testing prevents unfair blame.",
        ),
        QAItem(
            question="What is a mechanism in a story like this?",
            answer="A mechanism is a moving part or machine that can shift, spin, open, close, or carry something from one place to another.",
        ),
        QAItem(
            question="How can a twist change a mystery?",
            answer="A twist can reveal that the first explanation was wrong and that the real cause was something surprising but sensible.",
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
    StoryParams(place="workshop", missing="bells", mechanism="spinning_hook", friend="Mina", witness="Theo", suspect="cat", seed=11),
    StoryParams(place="library", missing="maps", mechanism="turntable", friend="Iris", witness="Luca", suspect="duck", seed=22),
    StoryParams(place="garden", missing="seeds", mechanism="sliding_latch", friend="Pia", witness="Ned", suspect="raccoon", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, missing, mechanism in combos:
            print(f"  {place:10} {missing:10} {mechanism}")
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
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        )
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header="### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else ""),
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
