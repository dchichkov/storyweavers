#!/usr/bin/env python3
"""A child-facing mystery world about Joey, webbed clues, and fair conflict."""

from __future__ import annotations

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
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    friend: str
    suspect: str
    case: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    missing: str
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
    "garden": Scene("the garden", "leafy", "a mild breeze"),
    "pond": Scene("the pond", "glassy", "a silver drizzle"),
    "shed": Scene("the shed", "hushed", "warm afternoon light"),
}
CLUES = {
    "webbed": "a webbed print crossed with tiny lines",
    "muddy": "a muddy print with a webbed edge",
    "shiny": "a shiny thread woven into a webbed pattern",
}
FRIENDS = {"Mina": "girl", "Theo": "boy", "Iris": "girl", "Ned": "boy"}
SUSPECTS = {"duck": "duck", "cat": "cat", "raccoon": "raccoon", "frog": "frog"}

# Each case carries its own cause, failed theory, repair, lesson, and final image.
CASES = {
    "seed_packets": MysteryCase(
        "three packets of moonflower seeds", "a torn packet lay beside the animal's tracks",
        "matched the tracks against a sketch in the club notebook", "the sizes did not match, so the easy answer fell apart",
        "a webbed strand snagged high on the watering-can handle", "a gust had lifted the packets into a loose shade net",
        "lowered the net together and sorted every seed into a labeled jar", "a nearby track is not proof of blame",
        "moonflower seeds rested in neat jars while the empty net fluttered overhead"),
    "bell_rope": MysteryCase(
        "the little brass bell from the gate", "someone heard a clink just after the animal passed",
        "followed the sound with pauses so echoes would not fool them", "the loudest clink came from an empty bucket, not the bell",
        "a shiny webbed knot showed where the bell rope had frayed", "the bell had rolled through a drain channel and lodged beneath a grate",
        "lifted it safely with a hooked stick and braided a stronger rope", "sounds can point the wrong way unless clues agree",
        "the rehung bell gave one clear note above a grate swept clean"),
    "painted_sign": MysteryCase(
        "the newly painted welcome sign", "a tail-shaped smear seemed to point toward the animal",
        "measured the smear with string and compared its height", "it was too straight and high to be a tail mark",
        "webbed mesh fibers clung to the still-tacky blue paint", "the sign had stuck to a windbreak screen and swung behind a hedge",
        "peeled it free with an adult's help and built a stable drying rack", "a familiar shape is not proof of what made it",
        "the blue sign shone on its rack with one tiny mesh square left as a reminder"),
    "picnic_crackers": MysteryCase(
        "a basket of oat crackers for the club picnic", "crumbs formed a trail near the animal's resting place",
        "counted the crumbs and checked where the trail widened", "the trail grew wider uphill, where no rolling basket could go",
        "a webbed carrying bag was wedged beneath a loose cart wheel", "the cart had bumped the basket into the bag before anyone arrived",
        "freed the basket, tightened the wheel, and shared the unbroken crackers", "sharing facts calmly can end a conflict",
        "friends and animals crunched crackers together beside the mended cart"),
    "paper_boats": MysteryCase(
        "the children's fleet of folded paper boats", "wet prints circled the launch shelf after the animal visited",
        "placed one test boat on the shelf and watched the moving air", "the boat stayed still, so the breeze alone was not enough",
        "a webbed reflection trembled under a gap in the rain barrel", "drips had filled a groove and floated the boats under the footbridge",
        "corked the leak and rescued the boats with a long net", "a fair test changes one thing at a time",
        "the rescued boats dried in a bright row above the newly corked barrel"),
    "lantern_covers": MysteryCase(
        "the colored covers from four garden lanterns", "red light flashed across the animal's shelter",
        "turned each lantern separately to trace the wandering colors", "none could cast the red patch at that angle",
        "a webbed pattern of red and gold glimmered inside a spider-safe frame", "the covers had slid into the frame and overlapped like stained glass",
        "opened the frame gently, returned the covers, and added holding clips", "surprising light can be a clue instead of a reason to panic",
        "four steady lantern colors made quiet circles on the evening path"),
    "tool_tags": MysteryCase(
        "the picture tags showing where every tool belonged", "one tag had caught on the animal's fur or feathers",
        "searched the low shelves where fallen tags should land", "only blank dust rectangles remained there",
        "webbed glue strings stretched from the shelf to a rolled work apron", "warm glue had softened and the apron gathered the tags as it rolled",
        "unrolled the apron, cleaned the tags, and fastened them with clips", "looking at what changed can reveal how a mystery began",
        "each tool hung beneath its picture while the clean apron dried on a peg"),
    "music_pages": MysteryCase(
        "the pages of a song written for pond night", "a croak or purr interrupted rehearsal when the pages vanished",
        "replayed the tune and watched where each loose scrap moved", "the scraps moved toward the wall, not toward the sound",
        "a webbed shadow appeared behind a vent whenever the fan turned", "the fan had drawn the pages against the vent in their original order",
        "switched off the fan, recovered the song, and clipped its pages", "two events together do not prove one caused the other",
        "the complete song rested under a star-shaped clip as rehearsal began"),
    "berry_ribbons": MysteryCase(
        "the ribbons marking which berries were ready", "a berry-colored stain appeared beside the animal's path",
        "dabbed the stain with water to see whether it came from fruit", "the color did not run, proving it was chalk rather than juice",
        "webbed ribbon ends peeked from holes in a chalkboard frame", "a cleaning cloth had swept the ribbons behind the board",
        "tilted the board forward, retrieved the ribbons, and tied them by color", "testing a clue is kinder than turning a guess into blame",
        "bright ribbons bobbed above ripe berries and no stain marked the path"),
    "tiny_bridge": MysteryCase(
        "the model bridge built for a stream experiment", "the animal stood beside a heap of sticks shaped like the bridge",
        "checked a photograph and counted every stick in the heap", "two curved rails were absent, so it was a different structure",
        "webbed cord from the bridge was taut beneath a rolling door", "the closing door had dragged the intact model into a storage slot",
        "raised the door, slid out the bridge, and moved the experiment table", "counting details can protect an innocent neighbor",
        "water whispered under the model bridge while its cord lay safely coiled"),
    "weather_chart": MysteryCase(
        "the week's weather chart", "the animal's damp shelter held a corner of similar paper",
        "fitted the corner against a copy of the chart", "its torn edge belonged to an old seed catalog",
        "a webbed trail of thumbtack holes climbed toward the roof gutter", "rain had loosened the chart and carried it into the clear gutter guard",
        "asked an adult to retrieve it and covered the replacement with a sleeve", "similar-looking objects still need careful comparison",
        "the dry new chart showed a sun while rain tapped its clear sleeve"),
    "story_tokens": MysteryCase(
        "the carved tokens used to choose the evening story", "the animal was beside the empty token bowl",
        "asked everyone when they had last seen the bowl full", "their memories disagreed, and arguing made nothing clearer",
        "a webbed pattern pressed into dust beneath the rotating book display", "the display's mesh base had scooped up the tokens when it turned",
        "rotated it back, collected the tokens, and fitted a smooth base cover", "listening to every witness works better than shouting a guess",
        "one moon token gleamed in the bowl as everyone settled for the story"),
}
ROUTES = ("clue_first", "dialogue_first", "test_first", "memory_first", "map_first", "quiet_first", "race_clock", "two_theories")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery world about Joey and a webbed clue.")
    ap.add_argument("--place", choices=sorted(PLACES)); ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--name"); ap.add_argument("--friend", choices=sorted(FRIENDS)); ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("-n", type=int, default=1); ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in sorted(PLACES) for c in sorted(CLUES)]


ASP_RULES = "valid(Place, Clue) :- place(Place), clue(Clue)."


def asp_facts() -> str:
    import asp
    return "\n".join([*(asp.fact("place", p) for p in PLACES), *(asp.fact("clue", c) for c in CLUES)])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/2.")), "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos)."); return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py)); return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos() if (not args.place or c[0] == args.place) and (not args.clue or c[1] == args.clue)]
    if not combos:
        raise StoryError("No valid mystery fits those options.")
    place, clue = rng.choice(combos)
    name = args.name or "Joey"
    friends = [f for f in sorted(FRIENDS) if f != name] or sorted(FRIENDS)
    return StoryParams(place=place, clue=clue, name=name, friend=args.friend or rng.choice(friends),
                       suspect=args.suspect or rng.choice(sorted(SUSPECTS)), case=rng.choice(sorted(CASES)), route=rng.choice(ROUTES))


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (params.seed, params.place, params.clue, params.name, params.friend, params.suspect, params.case, params.route))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene, case, rng = PLACES[params.place], CASES[params.case], story_rng(params)
    world = World(scene)
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Joey", "Theo", "Ned"} else "girl"))
    friend = world.add(Entity(id=params.friend, kind="character", type=FRIENDS[params.friend]))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=SUSPECTS[params.suspect], label=params.suspect))
    clue = CLUES[params.clue]
    openings = {
        "clue_first": f"The first thing {hero.id} noticed was {clue} beside {scene.place}. Only then did the young detective learn that {case.missing} had vanished.",
        "dialogue_first": f'"Please do not decide yet," {hero.id} said as voices rose at {scene.place}. {case.missing.capitalize()} had vanished, and {clue} was the only quiet witness.',
        "test_first": f"At {hero.id}'s Webbed-Clue Club, every mystery began with a test. This one began when {case.missing} disappeared from {scene.place} under {scene.weather}.",
        "memory_first": f"Later, {friend.id} would remember the {scene.mood} hush of {scene.place}. Everyone was searching for {case.missing}, and Joey had spotted {clue}.",
        "map_first": f"{hero.id} drew a map of {scene.place}: the doorway, the shelves, and {clue}. In the center the young detective wrote what was missing: {case.missing}.",
        "quiet_first": f"Nothing seemed wrong at {scene.place} until {friend.id} noticed an empty space. {case.missing.capitalize()} was gone, and nearby lay {clue}.",
        "race_clock": f"There was little time before visitors arrived at {scene.place}. {case.missing.capitalize()} had disappeared, while {clue} waited where it should not be.",
        "two_theories": f"Two explanations competed at {scene.place}: an animal had taken {case.missing}, or the weather had moved it. {hero.id} found {clue} between the theories.",
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"{friend.id} stayed beside {hero.id}, writing facts instead of rumors.",
        f"{hero.id} opened the club notebook while {friend.id} guarded the clue from careless feet.",
        f"Together, {hero.id} and {friend.id} agreed that every claim needed more than a guess.",
        f"The mystery made {friend.id} uneasy, but {hero.id} promised they would check each detail."]))
    world.para()
    world.say(rng.choice([
        f"Suspicion settled on the {suspect.label} because {case.accusation}.",
        f'"The {suspect.label} did it," someone declared, pointing out that {case.accusation}.',
        f"A sharp disagreement began when people noticed that {case.accusation} and blamed the {suspect.label}.",
        f"Because {case.accusation}, a worried neighbor tried to send the {suspect.label} away."]))
    world.say("That unfair accusation turned the mystery into a conflict between worried neighbors.")
    suspect.memes["blamed"] = 1; hero.memes["fairness"] = 1
    world.say(rng.choice([
        f'"Being close is not the same as being guilty," {hero.id} replied. "Let us find a clue that explains how."',
        f'{hero.id} raised one hand. "That may be a lead, but it is not a fair answer yet."',
        f'"We can disagree without frightening anyone," {friend.id} said, protecting the {suspect.label}.',
        f'{hero.id} felt the conflict tighten. "We need evidence that fits every part," {hero.id} said.']))
    world.para()
    world.say(f"First, {hero.id} {case.test}. But {case.failed}.")
    world.say(rng.choice([
        f"Instead of hiding the failed test, {hero.id} crossed out the theory and invited {friend.id} to look again.",
        f"The mistake showed which idea to release. {friend.id} turned the notebook to a clean page.",
        f'"Wrong ideas can teach good detectives," {friend.id} whispered, and the search changed direction.',
        "That result quieted the argument. Even the loudest accuser leaned closer to see the evidence."]))
    world.say(f"Then they found the decisive clue: {case.clue}.")
    world.say(rng.choice([
        f"{hero.id} traced its direction without touching it and saw the hidden chain of events.",
        "Working backward from that clue, the children reconstructed each small movement.",
        "They compared the clue with the map, the weather, and the empty space; all three agreed.",
        "The clue did more than point at a place. It explained why the earlier evidence misled them."]))
    world.para()
    world.say(f"The truth was that {case.truth}. The {suspect.label} had not caused the loss at all.")
    suspect.memes["blamed"] = 0; hero.meters["tests_completed"] = 2
    world.say(rng.choice([
        f"The accusers apologized to the {suspect.label}, then {hero.id} and {friend.id} {case.repair}.",
        f'"We were too quick," the neighbors admitted. After making peace with the {suspect.label}, everyone {case.repair}.',
        f"The conflict ended with an apology, not a victory. Side by side, the group {case.repair}.",
        f"Once the {suspect.label} was welcomed back, blame became useful work: they {case.repair}." ]))
    world.say(f"{hero.id} wrote the lesson in the mystery book: {case.lesson}.")
    world.say(rng.choice([
        f"At sunset, {case.ending}.", f"When the last question was answered, {case.ending}.",
        f"Peace returned in a picture everyone could see: {case.ending}.", f"Before leaving, they looked back. {case.ending.capitalize()}." ]))
    world.facts.update(hero=hero, friend=friend, suspect=suspect, scene=scene, clue=clue, case=case,
                       truth=case.truth, repair=case.repair, lesson=case.lesson, ending=case.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    f, c = world.facts, world.facts["case"]
    return [f"Write a short mystery for a young child about {f['hero'].id}, {f['clue']}, and the disappearance of {c.missing}.",
            f"Tell a gentle conflict mystery in which {f['hero'].id} tests evidence before deciding whether the {f['suspect'].label} is responsible.",
            f"Write a detective story set at {f['scene'].place}; reveal that {f['truth']}, and end with {f['ending']}."]


def story_qa(world: World) -> list[QAItem]:
    f, c = world.facts, world.facts["case"]
    return [
        QAItem(question=f"What went missing when {f['friend'].id} and {f['hero'].id} found {f['clue']} at {f['scene'].place}?", answer=f"{c.missing.capitalize()} went missing at {f['scene'].place}, beginning {f['hero'].id}'s mystery."),
        QAItem(question=f"Why did {f['friend'].id} help {f['hero'].id} challenge the accusation against the {f['suspect'].label}?", answer=f"The {f['suspect'].label} was blamed because {c.accusation}. That detail did not prove what caused the loss."),
        QAItem(question=f"How did {f['hero'].id}'s first test at {f['scene'].place} change {f['friend'].id}'s investigation?", answer=f"{f['hero'].id} {c.test}, but {c.failed}. The friends abandoned their first theory and inspected new evidence."),
        QAItem(question=f"Which webbed clue did {f['hero'].id} and {f['friend'].id} use to reveal what happened at {f['scene'].place}?", answer=f"The decisive clue was that {c.clue}. It helped the children discover that {c.truth}."),
        QAItem(question=f"How did the group repair the loss and make peace with the {f['suspect'].label}?", answer=f"After apologizing to the {f['suspect'].label}, they worked together: they {c.repair}. {f['hero'].id} recorded the lesson that {c.lesson}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Why should a detective test more than one explanation?", answer="One clue can fit several explanations. Comparing tests finds the cause that accounts for all the evidence."),
        QAItem(question="How can children handle a disagreement about blame?", answer="They can pause, speak calmly, protect anyone accused, and examine evidence together. They should apologize when a guess was unfair."),
        QAItem(question="What can a webbed pattern look like?", answer="A webbed pattern can have crossing lines, linked loops, or mesh-like spaces. Its source must be checked rather than guessed."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)), "", "== story qa =="]
    for item in sample.story_qa: lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa: lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values(): lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  truth={world.facts['truth']}"); return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header: print(header)
    print(sample.story)
    if trace and sample.world: print(dump_trace(sample.world))
    if qa: print("\n" + format_qa(sample))


CURATED = [
    StoryParams(place="garden", clue="webbed", name="Joey", friend="Mina", suspect="duck", case="seed_packets", route="clue_first", seed=11),
    StoryParams(place="pond", clue="muddy", name="Joey", friend="Theo", suspect="frog", case="paper_boats", route="test_first", seed=22),
    StoryParams(place="shed", clue="shiny", name="Joey", friend="Iris", suspect="cat", case="tool_tags", route="dialogue_first", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp: print(asp_program("#show valid/2.")); return
    if args.verify: sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos(); print(f"{len(combos)} compatible combos:\n")
        for place, clue in combos: print(f"  {place:8} {clue}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples, seen, attempts = [], set(), 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts; attempts += 1
            try: params = resolve_params(args, random.Random(seed))
            except StoryError as error: print(error); return
            params.seed = seed; sample = generate(params)
            if sample.story in seen: continue
            seen.add(sample.story); samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)); return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header="### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1: print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
