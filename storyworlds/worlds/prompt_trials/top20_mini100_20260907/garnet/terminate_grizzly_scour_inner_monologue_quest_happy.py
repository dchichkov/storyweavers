#!/usr/bin/env python3
"""
A small superhero storyworld about a brave helper, a grizzly problem, and a quest
to scour the city clean before the day can end happily.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Entity
    ally: Entity
    villain: Entity
    city: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    hero_name: str
    ally_name: str
    city: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Jett", "Piper", "Sol", "Mira", "Ace", "Luna", "Zane"]
ALLY_NAMES = ["Captain Bell", "Aunt Comet", "Rook", "Dr. Lantern", "Mayor Bright", "Spark"]
CITIES = ["Metro Harbor", "Silver Avenue", "Skyline Square", "Bricklight City", "North Star Block"]


ASP_RULES = r"""
#show brave/1.
#show scour/1.
#show happy_end/1.

brave(H) :- chooses_quest(H).
scour(H) :- cleans_city(H).
happy_end(H) :- stops_grizzly(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("chooses_quest", "hero"),
        asp.fact("cleans_city", "hero"),
        asp.fact("stops_grizzly", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave/1.\n#show scour/1.\n#show happy_end/1."))
    atoms = set((a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model)
    expected = {("brave", ("hero",)), ("scour", ("hero",)), ("happy_end", ("hero",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about a grizzly mess and a cleaning quest.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--ally-name", choices=ALLY_NAMES)
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        ally_name=args.ally_name or rng.choice(ALLY_NAMES),
        city=args.city or rng.choice(CITIES),
    )


def build_world(params: StoryParams) -> World:
    hero = Entity(id="hero", label=params.hero_name, phrase=f"hero {params.hero_name}", kind="character")
    ally = Entity(id="ally", label=params.ally_name, phrase=params.ally_name, kind="character")
    villain = Entity(
        id="villain",
        label="Grizzly",
        phrase="a grizzly troublemaker with muddy paws",
        kind="character",
        memes={"mean": 8.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.hero_name}|{params.ally_name}|{params.city}")
    hero.meters["bravery"] = 7.0
    ally.meters["helpfulness"] = 6.0
    villain.meters["mess"] = 9.0
    return World(hero=hero, ally=ally, villain=villain, city=params.city, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    arc: str,
    trouble: str,
    cause: str,
    quest: str,
    turn: str,
    resolution: str,
    ending: str,
    inner: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        trouble=trouble,
        cause=cause,
        quest=quest,
        turn=turn,
        resolution=resolution,
        ending=ending,
        inner=inner,
        happy_end=True,
    )
    return " ".join(lines)


def _rooftop_arc(world: World, rng: random.Random) -> str:
    h, a, c = world.hero.label, world.ally.label, world.city
    place = _choice(rng, ["the museum roof", "the clock tower ledge", "the river bridge", "the library dome"])
    mess = _choice(rng, ["sticky tar", "smashed paint cans", "windblown feathers", "a tumble of soot sacks"])
    tool = _choice(rng, ["a wide mop", "a silver scraper", "a suction glove", "a cloud broom"])
    trouble = f"{place} was coated in {mess} after Grizzly stomped through during the night"
    cause = "the villain had tossed a prank cart into the wind, and it burst across the high ledge"
    quest = f"the hero and ally began a quest to scour the roof before sunrise"
    turn = f"inside their helmets, the hero thought, 'If I hurry, I can still fix this before anyone slips.'"
    resolution = f"{h} used {tool} while {a} guided the lantern and bagged every piece of debris"
    ending = f"By morning, {place} shone over {c} again, and the last black smear was gone"
    inner = "The hero's inner monologue turned worry into a plan, then into action"
    lines = [
        f"At dusk in {c}, {h} saw Grizzly's muddy pawprints climbing toward {place}.",
        f'"We need to stop this," said {h}. {a} answered, "Then we clean, we scout, and we do not quit."',
        f"The climb was steep, and the mess was worse: {trouble}.",
        f"{h} swallowed hard and thought, \"{turn}\"",
        f"Together they started the quest to scour the rooftop. {h} scraped, {a} held the light, and the city wind carried the stink away bit by bit.",
        f"Grizzly lurked at the edge and growled, but the pair kept moving until the ledge was safe again.",
        f'"One more pass," said {a}. "{h}, can you reach the corner?" "Yes," said {h}, because courage sounded better when someone asked for help.',
        f"When the last streak vanished, the roof looked bold and bright again. {h} smiled at {a}; even the clouds seemed to relax.",
        f"{ending}. That was when {h} knew the quest had a happy ending.",
    ]
    return _record_story(world, arc="rooftop", trouble=trouble, cause=cause, quest=quest, turn=turn, resolution=resolution, ending=ending, inner=inner, lines=lines)


def _sewer_arc(world: World, rng: random.Random) -> str:
    h, a, c = world.hero.label, world.ally.label, world.city
    place = _choice(rng, ["the old storm drain", "the subway tunnel", "the canal tunnel", "the lower maintenance hall"])
    mess = _choice(rng, ["a sludge trail", "crumbled posters", "gritty dust", "a spill of gray foam"])
    tool = _choice(rng, ["a magnetic rake", "a rubber brush", "a bright pump", "a rescue net"])
    trouble = f"{place} was blocked by {mess} after Grizzly dragged junk into the dark"
    cause = "rainwater could not move through the blocked passage, so the block risked flooding a whole street"
    quest = f"{h} and {a} set out on a secret quest to scour the tunnel and reopen the flow"
    turn = f"The hero's inner voice whispered, 'This looks huge, but one step at a time is still a step.'"
    resolution = f"{h} used {tool} while {a} labeled the piles and hauled each dirty bundle away"
    ending = f"At last the water ran clear through {place}, and the street above stayed dry and safe"
    inner = "The inner monologue kept the hero calm until the mess became manageable"
    lines = [
        f"On a rainy night in {c}, {h} heard Grizzly laughing beneath the grate.",
        f'"We have to go down there," said {h}. {a} nodded. "Then we bring light and finish the job."',
        f"The tunnel smelled awful. {trouble}.",
        f"{h} paused, then thought, \"{turn}\"",
        f"They moved in a careful line. The quest was to scour every corner until the blockage was gone.",
        f"Each time {h} found a wet bundle, {a} called out the label so nothing got missed.",
        f"Grizzly tried to splash them, but the hero and ally stayed steady and cleaned faster than the villain could mess.",
        f'"Almost done!" shouted {a}. "Almost," said {h}, and reached one last dark bend.',
        f"{ending}. The city hummed softly above them, safe at last.",
    ]
    return _record_story(world, arc="sewer", trouble=trouble, cause=cause, quest=quest, turn=turn, resolution=resolution, ending=ending, inner=inner, lines=lines)


def _park_arc(world: World, rng: random.Random) -> str:
    h, a, c = world.hero.label, world.ally.label, world.city
    place = _choice(rng, ["the fountain plaza", "the playground", "the kite field", "the square garden"])
    mess = _choice(rng, ["muddy trash", "painted graffiti", "broken snack wrappers", "a heap of snapped branches"])
    tool = _choice(rng, ["a scrub brush", "a water wand", "a folding scoop", "a big blue net"])
    trouble = f"Grizzly had left {mess} all over {place}"
    cause = "the villain wanted the park to look grim and give everyone a gloomy morning"
    quest = f"{h} and {a} began a clean-up quest to scour the place until it sparkled"
    turn = f"{h} thought, 'Heroes do not need perfect plans. They need brave hands and a friend.'"
    resolution = f"{h} and {a} used {tool} and sorted the mess into neat piles for recycling"
    ending = f"By sunset, {place} in {c} was bright again, and children raced back laughing"
    inner = "The hero's inner monologue turned doubt into determination"
    lines = [
        f"At sunrise in {c}, {h} found Grizzly's muddy tracks circling {place}.",
        f'"This is our quest," said {h}. {a} gave a grin. "Then let us scour every inch."',
        f"The sight was grim: {trouble}.",
        f"{h} looked at the piles and thought, \"{turn}\"",
        f"Step by step, they cleaned. {h} scrubbed the stones while {a} gathered the sharp bits and tucked them away.",
        f"Grizzly stomped in once to boast, but the hero pointed to the half-shining path and said, \"Not today.\"",
        f"That answer worked better than a shout. The villain snarled and backed away as the clean path grew longer.",
        f'"Look!" said {a}. "The fountain is shining again!" {h} laughed because the water reflected the sky like a medal.',
        f"{ending}. The park had a happy ending, and so did the day.",
    ]
    return _record_story(world, arc="park", trouble=trouble, cause=cause, quest=quest, turn=turn, resolution=resolution, ending=ending, inner=inner, lines=lines)


def _archive_arc(world: World, rng: random.Random) -> str:
    h, a, c = world.hero.label, world.ally.label, world.city
    place = _choice(rng, ["the city archive", "the old courthouse", "the history room", "the bell cellar"])
    mess = _choice(rng, ["ash footprints", "scattered papers", "ink smears", "dusty web clumps"])
    tool = _choice(rng, ["soft gloves", "a tidy brush", "a page press", "a careful vacuum"])
    trouble = f"{place} was covered in {mess} after Grizzly searched for a map"
    cause = "the villain had ripped open storage boxes while hunting for a secret key"
    quest = f"{h} swore a quest to scour and restore the room before the mayor arrived"
    turn = f"Inside, the hero thought, 'If I can find the key, I can end this fast and keep everyone calm.'"
    resolution = f"{h} followed crumbs of paper to the missing key while {a} sorted the damaged files"
    ending = f"By evening, {place} looked neat again, and the recovered key sat safely in a glass dish"
    inner = "The hero's inner monologue guided the search from panic to purpose"
    lines = [
        f"Late in the day, {h} and {a} heard a thump from {place} in {c}.",
        f'"Grizzly is in there," said {a}. {h} nodded. "Then we make a plan."',
        f"When they entered, the room was a mess: {trouble}.",
        f"{h} looked at the ruin and thought, \"{turn}\"",
        f"The quest began at once. They scoured shelves, checked under crates, and brushed every page flat.",
        f"{h} found the key hidden in a paper boat. {a} laughed. \"A pirate's idea of tidy,\" said {a}.",
        f"Grizzly burst out with a growl, but the room was already being restored, and that made the villain look smaller.",
        f'"Put it back," said {h}. The villain hesitated, then dropped the key when the bright flashlight found its face.',
        f"{ending}. The archive had a happy ending, and the city could remember its stories again.",
    ]
    return _record_story(world, arc="archive", trouble=trouble, cause=cause, quest=quest, turn=turn, resolution=resolution, ending=ending, inner=inner, lines=lines)


ARC_BUILDERS = [_rooftop_arc, _sewer_arc, _park_arc, _archive_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x6A4E37)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What quest did {h} go on?",
            answer=f"{h} went on a quest to {facts['quest'].replace('the hero and ally', 'the hero and ally').replace('the hero', h)}.",
        ),
        QAItem(
            question="What caused the main problem?",
            answer=f"The main problem happened because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} use inner monologue in the story?",
            answer=f"{h} thought, '{facts['turn']}' and used that thought to keep going.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{facts['resolution']}. {facts['ending']}, so the story finished with a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or mission to do something important, often with danger or difficulty along the way.",
        ),
        QAItem(
            question="What does it mean to scour something?",
            answer="To scour something means to clean it very carefully and thoroughly, or to search through it closely.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the characters solve the problem and finish the story feeling safe, relieved, or joyful.",
        ),
    ]
    arc_item = {
        "rooftop": QAItem("Why was the roof problem dangerous?", "A slick rooftop can make someone slip and fall, so it needed to be cleaned quickly."),
        "sewer": QAItem("Why does blocked water matter?", "Blocked water can back up and flood nearby places, so clearing the path keeps the city safe."),
        "park": QAItem("Why clean a park carefully?", "A park is safer and nicer when sharp pieces and trash are removed before people return."),
        "archive": QAItem("Why restore an archive?", "Archives protect important records, so cleaning and repairing them keeps the city’s memories safe."),
    }[world.facts["arc"]]
    return [common[0], arc_item, common[1], common[2]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a superhero story with inner monologue, a quest, and a happy ending.",
        f"Tell a child-friendly tale set in {world.city} where a hero must scour away a grizzly mess.",
        "Make the story feel like a comic-book rescue, but simple and warm for young readers.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.ally, world.villain]:
        lines.append(f"  {ent.id:7} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  city={world.city}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave/1.\n#show scour/1.\n#show happy_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: brave(hero), scour(hero), happy_end(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(hero_name="Nova", ally_name="Captain Bell", city="Metro Harbor"),
            StoryParams(hero_name="Piper", ally_name="Aunt Comet", city="Silver Avenue"),
            StoryParams(hero_name="Mira", ally_name="Dr. Lantern", city="Skyline Square"),
            StoryParams(hero_name="Ace", ally_name="Spark", city="North Star Block"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.city}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
