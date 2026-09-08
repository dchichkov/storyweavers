#!/usr/bin/env python3
"""A playful Tall Tale StoryWorld about escorting a millionaire through camouflage."""

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the enormous green valley"
    guide_name: str = "Luna"
    millionaire_name: str = "Mr. Goldleaf"
    treasure: str = "a silver suitcase"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    landscape: str
    danger: str
    camouflage: str
    clue: str
    plan: str
    jobs: tuple[str, str]
    result: str
    lesson: str
    ending: str


SETTINGS = {
    "the enormous green valley": True,
    "the whispering jungle": True,
    "the upside-down mountain": True,
    "the moonlit prairie": True,
}
NAMES = ["Luna", "Mabel", "Pip", "Toby", "Zara", "Nico", "Wren", "Otis"]
MILLIONAIRES = ["Mr. Goldleaf", "Lady Plenty", "Count Coinwell", "Madam Moneypenny"]
TREASURES = ["a silver suitcase", "a golden lunchbox", "a velvet money bag", "a diamond umbrella"]

SCENARIOS = [
    Scenario(
        "fern-fleet",
        "where ferns grew taller than castle towers",
        "a flock of noisy parrots mistook the millionaire for a walking snack",
        "a fern-colored cloak and a hat shaped like a leaf",
        "the parrots ignored anything that stood still and smelled of mint",
        "camouflage the escort pair, walk like quiet ferns, and follow the minty breeze",
        ("painted the cloak with broad green stripes", "rubbed mint leaves along the safe path"),
        "The parrots flew past while the millionaire reached the valley gate without a single feather landing on his hat.",
        "good escorts notice danger before showing off their courage",
        "the giant leaf hat rested by the gate while the suitcase gleamed safely beneath it",
    ),
    Scenario(
        "thunder-steps",
        "where stepping stones rumbled like drums",
        "each loud footstep woke a sleepy thundercloud",
        "boots padded with clouds and a coat patterned like the gray sky",
        "the clouds snored whenever footsteps matched the slow valley rhythm",
        "copy the clouds' rhythm and cross without making a startling sound",
        ("counted three soft steps between each stone", "held the millionaire's suitcase level and copied the rumble"),
        "They crossed so quietly that the thundercloud rolled over and went back to sleep.",
        "a careful escort protects a traveler better than a noisy boast",
        "the millionaire waved from the far bank as one small cloud puffed a peaceful hello",
    ),
    Scenario(
        "cactus-court",
        "where cactuses wore crowns and gave directions",
        "the crown cactuses demanded a royal password from every traveler",
        "a prickly green disguise with a paper crown tucked behind one ear",
        "the cactuses bowed only to travelers who carried no unnecessary sparkle",
        "hide the treasure's shine, answer politely, and escort the millionaire through the cactus court",
        ("wrapped the suitcase in a dull brown blanket", "practiced the valley's most respectful bow"),
        "The cactus court opened a path, and not one royal thorn touched the millionaire.",
        "humility can open a path that money cannot",
        "the paper crown hung on a cactus while the millionaire's dull-wrapped treasure passed safely",
    ),
    Scenario(
        "giant-shadow",
        "where one tiny pebble cast a shadow across half the country",
        "a suspicious giant followed the shadow, looking for a famous millionaire",
        "matching gray capes that blended with the pebble's enormous shade",
        "the giant watched moving colors but never noticed quiet gray shapes",
        "move only when the shadow moved and escort the millionaire beneath its cool cover",
        ("marked the shadow's edge with white pebbles", "stepped only on the shaded side"),
        "The giant searched the sunny road while the travelers slipped into a friendly village.",
        "wise camouflage turns danger into a chance to travel calmly",
        "the pebble's shadow stretched behind them like a gray road to safety",
    ),
    Scenario(
        "river-riddle",
        "where a river flowed uphill and asked questions in rhyme",
        "the river refused to carry anyone who could not answer its bouncy riddle",
        "blue-striped coats that matched the water's dancing ripples",
        "the river's riddle always ended with the word that rhymed with 'guide'",
        "listen closely, answer in rhyme, and escort the millionaire across the rising water",
        ("found a rhyme for the river's final word", "kept the treasure dry inside a floating shell"),
        "The river sang 'glide,' Luna answered 'side,' and the travelers floated safely across.",
        "listening is a powerful kind of courage",
        "the uphill river hummed beneath their boat as the millionaire thanked his careful guide",
    ),
    Scenario(
        "golden-goose",
        "where geese grew large enough to pull wagons",
        "a golden goose chased every glittering thing in sight",
        "sun-colored scarves that looked like ordinary straw",
        "the goose turned away whenever something shiny became dull",
        "cover the treasure, dress like straw, and walk behind the goose's broad tail",
        ("tied straw-colored scarves around both travelers", "covered the suitcase with a muddy sack"),
        "The goose led them straight to the village, believing they were two very boring hay bundles.",
        "a plain appearance can protect something precious",
        "the golden goose honked beside the gate while the dull sack hid every sparkle",
    ),
    Scenario(
        "echo-pass",
        "where every word bounced back seven times",
        "an echo repeated the millionaire's name until a crowd of curious giants came running",
        "a whispering cloak stitched from soft, soundless moss",
        "the echo vanished when words were spoken into a hollow reed",
        "use the reed, whisper a rhyme, and escort the millionaire between the quiet cliffs",
        ("held the hollow reed before each careful phrase", "guided the suitcase along the mossy trail"),
        "Their words disappeared into the reed, and the giants chased an old echo instead.",
        "a small clever tool can make a very large difference",
        "the cliffs held still while the millionaire's last whisper curled away like a green ribbon",
    ),
    Scenario(
        "cloud-market",
        "where merchants sold clouds by the handful",
        "a greedy wind tried to blow the millionaire's treasure into the sky",
        "a cloud-gray poncho with pockets stitched like little clouds",
        "the wind dropped when it heard a steady rhyme repeated together",
        "hold the treasure low, chant the market rhyme, and walk against the gust",
        ("fastened the suitcase to a broad belt", "kept the rhyme's beat with two firm claps"),
        "The wind settled into a breeze, and the travelers reached the market's sturdy bridge.",
        "steady teamwork can tame a wild surprise",
        "cloud merchants clapped as the silver suitcase crossed the bridge without floating away",
    ),
]


OPENINGS = [
    "Once, in {setting}, {guide} was hired to escort {millionaire}.",
    "People still tell the tall tale of how {guide} became the escort of {millionaire} in {setting}.",
    "On a morning big enough to need two suns, {guide} met {millionaire} in {setting}.",
    "In {setting}, even the pebbles knew that {millionaire} needed a brave escort.",
    "The day began with a trumpet blast from a beetle, and {guide} promised to escort {millionaire}.",
    "Long ago, when roads were taller than trees, {guide} accepted a very unusual escort job.",
]

RHYME = [
    "Hide low, stride slow, let the safe green pathway show.",
    "Step by step, keep the treasure in your grip; rhyme by rhyme, we make the danger slip.",
    "Quiet feet, steady beat, every traveler stays complete.",
    "By leaf and stone, we guide our own; by song and care, we travel there.",
    "No flash, no fright, we blend with light; together we make the crossing right.",
    "A careful guide, a covered prize, can fool the biggest watching eyes.",
]

REACTIONS = [
    "'A millionaire is not a mountain,' said Luna, 'but trouble may still spot him.'",
    "'Please do not panic,' Luna said. 'Panic is terribly bright camouflage.'",
    "The millionaire puffed up proudly, but Luna pointed to the danger ahead.",
    "'My fortune can buy a castle,' said the millionaire. 'Can it buy a quiet path?'",
    "Luna shook her head. 'A grand name needs a small, sensible plan.'",
    "The millionaire wanted to charge forward, yet Luna noticed what the danger was watching.",
]

TURN_LINES = [
    "That was the turn in the tale: Luna stopped trying to look heroic and started trying to look ordinary.",
    "Then the two travelers discovered that the safest disguise was one they could use together.",
    "The danger changed their question from 'Who is strongest?' to 'What will fool the watcher?'",
    "Luna listened to the land, and the land offered a plan stranger than any treasure.",
    "The millionaire lowered his chin. For the first time, he understood that an escort must notice more than money.",
    "A huge problem became smaller when each traveler accepted one useful job.",
]


def generate_world(p: StoryParams) -> World:
    if p.guide_name == p.millionaire_name:
        raise StoryError("The escort and the millionaire must have different names.")
    world = World(p.setting)
    guide = world.add(Entity("G", "escort", p.guide_name))
    millionaire = world.add(Entity("M", "millionaire", p.millionaire_name))
    treasure = world.add(Entity("T", "treasure", p.treasure))

    seed = abs(p.seed or 0)
    scene = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // 9) % len(OPENINGS)]
    rhyme = RHYME[(seed // 81) % len(RHYME)]
    reaction = REACTIONS[(seed // 729) % len(REACTIONS)]
    turn = TURN_LINES[(seed // 6561) % len(TURN_LINES)]

    world.say(opening.format(setting=p.setting, guide=guide.label, millionaire=millionaire.label))
    world.say(f"The millionaire carried {treasure.label}, which was valuable enough to make three dragons sneeze.")
    world.say(f"Their journey led through {scene.landscape}. Before leaving, they sang, '{rhyme}'")
    world.para()
    world.say(f"But {scene.danger}")
    world.say(reaction)
    world.say(f"Luna's first idea failed because {scene.clue}.")
    world.say(f"Then {millionaire.label} asked, 'What should we do?'")
    world.say(f"Luna answered, 'We should {scene.plan}.'")
    world.para()
    world.say(turn)
    world.say(f"The camouflage plan was to {scene.camouflage}.")
    world.say(f"{guide.label} {scene.jobs[0]}, while {millionaire.label} {scene.jobs[1]}.")
    world.say(f"Together they sang, '{rhyme}'")
    world.say(scene.result)
    world.para()
    world.say(f"The millionaire whispered, 'You did not merely lead me; you helped me understand the danger.'")
    world.say(f"Luna replied, 'A good escort watches, listens, and keeps a traveler safe.'")
    world.say(f"They learned that {scene.lesson}.")
    world.say(f"At sunset, {scene.ending}")

    guide.memes.update(courage=1.0, cleverness=1.0, care=1.0)
    millionaire.memes.update(trust=1.0, patience=1.0)
    treasure.meters.update(protected=1.0, traveled=1.0)
    world.facts.update(
        guide=guide.label,
        millionaire=millionaire.label,
        treasure=treasure.label,
        scenario=scene.key,
        danger=scene.danger,
        camouflage=scene.camouflage,
        clue=scene.clue,
        plan=scene.plan,
        first_job=scene.jobs[0],
        second_job=scene.jobs[1],
        result=scene.result,
        lesson=scene.lesson,
        ending=scene.ending,
        rhyme=rhyme,
        escorted=True,
        protected=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    danger = str(f["danger"])
    return [
        QAItem(
            question=f"Why did {f['guide']} need to escort {f['millionaire']}?",
            answer=f"{f['guide']} escorted {f['millionaire']} because {danger[0].lower() + danger[1:]} The journey was too unusual to make safely without a careful guide.",
        ),
        QAItem(
            question="What clue helped them choose their camouflage?",
            answer=f"They noticed that {f['clue']}. This clue showed them how to blend in instead of attracting attention.",
        ),
        QAItem(
            question="How did the escort and the millionaire divide the work?",
            answer=f"{f['guide']} {f['first_job']}, while {f['millionaire']} {f['second_job']}. Their two jobs made the camouflage useful.",
        ),
        QAItem(
            question="How did the rhyme help the travelers?",
            answer=f"The rhyme helped them stay together and follow their plan. They sang, '{f['rhyme']}'",
        ),
        QAItem(
            question="What changed by the end of the tale?",
            answer=f"The treasure and millionaire reached safety because {f['result']} They learned that {f['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escort?",
            answer="An escort is a person who travels with someone to guide, protect, or help that traveler.",
        ),
        QAItem(
            question="What is a millionaire?",
            answer="A millionaire is a person whose wealth is at least one million units of money.",
        ),
        QAItem(
            question="What is camouflage?",
            answer="Camouflage is a color, shape, or covering that helps something blend into its surroundings.",
        ),
        QAItem(
            question="Why can a rhyme help during a journey?",
            answer="A rhyme can help travelers remember instructions, keep a shared rhythm, and encourage one another.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Tall Tale about {f['guide']} escorting {f['millionaire']} through a remarkable landscape.",
        f"Tell a child-friendly adventure in which camouflage helps protect {f['treasure']}.",
        f"Create a rhyming Tall Tale where an escort and a millionaire solve this danger: {f['danger']}",
    ]


ASP_RULES = r"""
protected_treasure(T) :- treasure(T), escorted(M,G), carries(M,T), safe(M).
safe(M) :- escorted(M,G), camouflage_used(G,M), listened(G).
successful_escort(G,M) :- escorted(M,G), protected_treasure(T), carries(M,T).
#show protected_treasure/1.
#show successful_escort/2.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("treasure", "silver_suitcase"),
        asp.fact("millionaire", "goldleaf"),
        asp.fact("escort", "luna"),
        asp.fact("escorted", "goldleaf", "luna"),
        asp.fact("carries", "goldleaf", "silver_suitcase"),
        asp.fact("camouflage_used", "luna", "goldleaf"),
        asp.fact("listened", "luna"),
        asp.fact("safe", "goldleaf"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show successful_escort/2. #show protected_treasure/1."))
    escorts = asp.atoms(symbols, "successful_escort")
    protected = asp.atoms(symbols, "protected_treasure")
    if escorts and protected:
        print("OK: ASP program found a successful escorted journey.")
        return 0
    print("MISMATCH: ASP program did not find a successful escorted journey.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--guide-name")
    ap.add_argument("--millionaire-name")
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    guide = args.guide_name or rng.choice(NAMES)
    millionaire = args.millionaire_name or rng.choice(
        [name for name in MILLIONAIRES if name != guide]
    )
    if guide == millionaire:
        raise StoryError("The escort and the millionaire must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        guide_name=guide,
        millionaire_name=millionaire,
        treasure=args.treasure or rng.choice(TREASURES),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the enormous green valley", "Luna", "Mr. Goldleaf", "a silver suitcase", 7),
    StoryParams("the whispering jungle", "Mabel", "Lady Plenty", "a golden lunchbox", 49),
    StoryParams("the upside-down mountain", "Pip", "Count Coinwell", "a velvet money bag", 103),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        f = sample.world.facts
        print(
            f"\n--- world model state ---\n"
            f"scenario={f['scenario']} escorted={f['escorted']} protected={f['protected']}"
        )
    if qa:
        for i, item in enumerate(sample.story_qa, 1):
            print(f"Q{i}: {item.question}\nA{i}: {item.answer}")
        for i, item in enumerate(sample.world_qa, 1):
            print(f"W{i}: {item.question}\nA{i}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show successful_escort/2. #show protected_treasure/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show successful_escort/2. #show protected_treasure/1."))
        print(json.dumps({"successful_escort": asp.atoms(symbols, "successful_escort"),
                          "protected_treasure": asp.atoms(symbols, "protected_treasure")}))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
