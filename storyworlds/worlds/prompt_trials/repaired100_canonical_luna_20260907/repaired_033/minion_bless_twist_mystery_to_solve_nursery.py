#!/usr/bin/env python3
"""
A standalone nursery-rhyme storyworld about a tiny minion, a blessing,
and a mystery to solve in a moonlit nursery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    nursery: str
    hero: str
    minion: str
    moon: str
    mystery: str = "missing_lullaby"
    rhyme_style: int = 0
    twist_style: int = 0
    blessing_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    opening: str
    clue: str
    false_answer: str
    hidden_truth: str
    first_action: str
    blessing: str
    helpful_action: str
    ending: str
    lesson: str


NURSERIES = {
    "moonroom": "the moonroom nursery",
    "starroom": "the starroom nursery",
    "cloudroom": "the cloudroom nursery",
    "sunroom": "the sunroom nursery",
}

HERO_NAMES = ["Luna", "Mimi", "Nell", "Pip", "Tess", "Wren"]
MINION_NAMES = ["Bobo", "Nub", "Midge", "Tink", "Mop", "Pogo"]
MOONS = ["silver moon", "round moon", "pearl moon", "little moon"]

MYSTERIES = {
    "missing_lullaby": Mystery(
        opening="the nursery's blue music box would not sing its usual lullaby",
        clue="found three soft crumbs beside the silent box and a trail of blanket fuzz under the cot",
        false_answer="a naughty minion had swallowed the song",
        hidden_truth="the minion had tucked the music-box key beneath a warm blanket to keep a shivering mouse cozy",
        first_action="searched the toy chest and blamed the minion before asking a question",
        blessing="placed a gentle blessing on the blanket: 'May every small heart find a warm and safe place'",
        helpful_action="brought the key back and tucked the mouse into a basket beside the music box",
        ending="The blue box chimed, and the mouse curled up as if each note were a tiny moonbeam.",
        lesson="A mystery grows kinder when we seek the reason before choosing blame.",
    ),
    "vanishing_star": Mystery(
        opening="the gold star above the cradle vanished just before bedtime",
        clue="noticed a golden thread leading from the empty hook to a pile of folded bibs",
        false_answer="the minion had stolen the star to crown himself king",
        hidden_truth="the minion had moved it away from the window because a frightened moth kept bumping into its sharp edge",
        first_action="looked beneath the pillows and announced that the minion must be hiding the prize",
        blessing="whispered a blessing over the bib pile: 'May bright things guide, but never hurt, the small'",
        helpful_action="hung the star safely above the reading rug and made a soft paper shade for the moth",
        ending="The star shone above the rug while the moth rested in the shade, calm as a folded wing.",
        lesson="The brightest answer is not always the truest one.",
    ),
    "backward_bells": Mystery(
        opening="the crib bells rang backward, dinging before anyone touched them",
        clue="saw that one bell was tied to a long red thread beneath the rug",
        false_answer="the minion had learned a backwards spell",
        hidden_truth="the minion had tied the thread to pull a fallen rattle away from a sleeping baby",
        first_action="pulled the rug and made the bells clatter louder",
        blessing="gave the quiet room a blessing: 'May gentle hands mend what noisy hands disturb'",
        helpful_action="freed the rattle, loosened the thread, and retied the bells so they rang only when touched",
        ending="Ding went the bell, then hush went the room, and the rattle rested beside the crib.",
        lesson="Careful hands can turn a puzzling noise into peaceful quiet.",
    ),
    "crooked_shadow": Mystery(
        opening="a crooked shadow danced across the nursery wall though the night lamp stood still",
        clue="heard a tiny hiccup each time the shadow jumped",
        false_answer="a goblin had crept into the nursery",
        hidden_truth="the minion was hiding behind the lamp because a lost chick had flown into the room",
        first_action="chased the shadow with a slipper and startled the chick into a curtain",
        blessing="blessed the curtain: 'May frightened wings find a kindly way home'",
        helpful_action="dimmed the lamp, opened the window, and guided the chick toward the garden",
        ending="The shadow became straight, and the chick gave one bright chirp before flying home.",
        lesson="A strange shadow may be a small creature asking for help.",
    ),
    "whispering_drawer": Mystery(
        opening="the sock drawer whispered, 'Help me,' whenever the nursery grew quiet",
        clue="found a loose button and a trail of blue thread beneath the drawer",
        false_answer="the minion had put a talking spell on the socks",
        hidden_truth="the minion had heard a beetle trapped behind the drawer and was trying to pull it free",
        first_action="opened every drawer and scattered socks across the floor",
        blessing="blessed the scattered socks: 'May every pair find its partner and every beetle find its path'",
        helpful_action="lifted the drawer with a wooden block and let the beetle crawl into the garden",
        ending="The drawer whispered no more, while two matching socks marched together to the basket.",
        lesson="Listening closely can reveal a quiet creature in need.",
    ),
    "lost_lantern": Mystery(
        opening="the little night lantern kept wandering from the bedside table",
        clue="saw tiny wheel marks leading toward the toy train tunnel",
        false_answer="the minion was rolling the lantern away to make a secret sun",
        hidden_truth="the minion was carrying it toward a lost duckling that could not see beneath the bed",
        first_action="snatched up the lantern and left the duckling in the dark",
        blessing="gave a warm blessing: 'May this small light travel where small feet need it most'",
        helpful_action="rolled the lantern slowly beside the duckling and guided it back to its toy pond",
        ending="The lantern glowed by the pond, and the duckling quacked a sleepy thank-you.",
        lesson="A helpful light belongs where it can guide someone safely.",
    ),
}

RHYME_OPENINGS = [
    "{hero} lived in a nursery, tidy and bright, where moonbeams tucked toys in a row for the night.",
    "When the moon wore a bonnet and stars filled the sky, {hero} heard a strange sound and went to find why.",
    "In the hush of the nursery, soft as a tune, {hero} watched a small puzzle appear by the moon.",
    "{hero} kept watch by the cradle, with slippers of blue, while a curious mystery peeked into view.",
    "A night bird sang low and the curtains swung slow; {hero} found a riddle where dream-dwellers go.",
]

TWISTS = [
    "But the first answer wore a crooked disguise, and the truth hid in kinder-sized eyes.",
    "Yet the riddle turned round with a flip and a flit, for the minion was helping, not causing it.",
    "Then came the twist, like a turn of a top: the blame that went up had to tumble and stop.",
    "The clue made a circle, the circle made two; what seemed to be trouble was help shining through.",
    "A mystery may giggle and turn on its heel when a secret good reason is ready to reveal.",
]

BLESSINGS = [
    "May warm beds and brave hearts be near",
    "May every small worry grow quiet and clear",
    "May kind hands remember to listen and see",
    "May lost little creatures find shelter and glee",
    "May moonlight bless helpers who quietly care",
]

ASP_RULES = r"""
% A mystery is valid when a clue leads to a hidden need,
% a blessing follows understanding, and the minion helps.
valid_story(N) :-
    nursery(N),
    clue_found,
    hidden_need,
    blessing_given,
    minion_helped.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("nursery", key) for key in NURSERIES]
    lines.extend(
        [
            asp.fact("clue_found"),
            asp.fact("hidden_need"),
            asp.fact("blessing_given"),
            asp.fact("minion_helped"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_names = set(NURSERIES)
    asp_names = {name for (name,) in asp_valid()}
    if python_names == asp_names:
        print(f"OK: ASP model covers {len(python_names)} nursery settings.")
        return 0
    print("MISMATCH between Python and ASP nursery coverage.")
    print("only python:", sorted(python_names - asp_names))
    print("only asp:", sorted(asp_names - python_names))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme mystery about a minion and a blessing."
    )
    parser.add_argument("--nursery", choices=NURSERIES)
    parser.add_argument("--hero")
    parser.add_argument("--minion")
    parser.add_argument("--moon")
    parser.add_argument("--mystery", choices=MYSTERIES)
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
    return StoryParams(
        nursery=args.nursery or rng.choice(list(NURSERIES)),
        hero=args.hero or rng.choice(HERO_NAMES),
        minion=args.minion or rng.choice(MINION_NAMES),
        moon=args.moon or rng.choice(MOONS),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        rhyme_style=rng.randrange(len(RHYME_OPENINGS)),
        twist_style=rng.randrange(len(TWISTS)),
        blessing_style=rng.randrange(len(BLESSINGS)),
    )


def validate(params: StoryParams) -> None:
    if params.hero.strip().lower() == params.minion.strip().lower():
        raise StoryError("The child and the minion need different names.")
    if not params.hero.strip() or not params.minion.strip():
        raise StoryError("The hero and minion names must not be empty.")
    if params.nursery not in NURSERIES:
        raise StoryError(f"Unknown nursery: {params.nursery}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World(NURSERIES[params.nursery])

    hero = world.add(
        Entity(
            id="hero",
            kind="human",
            label=params.hero,
            phrase=f"{params.hero}, a small nursery watcher",
            memes={"curiosity": 1.0, "worry": 0.0, "kindness": 0.0},
            location="bedside",
        )
    )
    minion = world.add(
        Entity(
            id="minion",
            kind="creature",
            label=params.minion,
            phrase=f"a tiny minion named {params.minion}",
            meters={"helpfulness": 0.0, "hiding": 1.0, "problem": 0.0},
            memes={"worry": 1.0, "pride": 0.0, "relief": 0.0},
            location="toy chest",
        )
    )
    moon = world.add(
        Entity(
            id="moon",
            kind="object",
            label=params.moon,
            phrase=params.moon,
            meters={"brightness": 1.0},
            location="window",
        )
    )
    mystery = world.add(
        Entity(
            id="mystery",
            kind="object",
            label="mystery",
            phrase="the nursery mystery",
            meters={"solved": 0.0},
            location="nursery",
        )
    )
    world.facts.update(
        params=params,
        mystery=MYSTERIES[params.mystery],
        hero=hero,
        minion=minion,
        moon=moon,
        mystery_entity=mystery,
        clue_found=False,
        truth_known=False,
        blessing_given=False,
        minion_helped=False,
    )
    return world


def act_open(world: World) -> None:
    params = world.facts["params"]
    hero = world.get("hero")
    mystery = world.facts["mystery"]
    world.say(RHYME_OPENINGS[params.rhyme_style].format(hero=hero.label))
    world.say(f"By the glow of {params.moon}, {hero.label} heard that {mystery.opening}.")


def act_search(world: World) -> None:
    hero = world.get("hero")
    minion = world.get("minion")
    mystery = world.facts["mystery"]
    world.say(
        f"{hero.label} followed the clue, while {minion.label} hid near the toy chest, "
        f"quiet as a button in a mitten."
    )
    world.say(f"The clue was this: {mystery.clue}.")
    world.facts["clue_found"] = True
    hero.memes["worry"] = 1.0
    minion.meters["problem"] = 1.0
    world.say(f'"Did you do it, {minion.label}?" {hero.label} asked.')
    world.say(f'"I did not mean harm," said {minion.label}. "I was trying to help."')
    world.say(f"{hero.label} nearly chose the easy answer: {mystery.false_answer}.")
    world.say(TWISTS[world.facts["params"].twist_style])


def act_understand(world: World) -> None:
    hero = world.get("hero")
    minion = world.get("minion")
    mystery = world.facts["mystery"]
    hero.memes["kindness"] = 1.0
    hero.memes["worry"] = 0.0
    world.say(f"Then {hero.label} knelt low and listened instead of scolding.")
    world.say(f"The hidden truth was plain: {mystery.hidden_truth}.")
    world.say(f'"Show me what you need," said {hero.label}.')
    world.say(f'"This way, please," said {minion.label}, pointing with one tiny hand.')
    world.facts["truth_known"] = True


def act_bless(world: World) -> None:
    hero = world.get("hero")
    mystery = world.facts["mystery"]
    blessing = BLESSINGS[world.facts["params"].blessing_style]
    world.say(f"{hero.label} lifted both hands and gave a gentle blessing: “{blessing}.”")
    world.say(f"The blessing was not a spell to hide the trouble. It was a promise to help mend it.")
    world.say(f"Then {hero.label} {mystery.first_action}, paused, and chose a kinder path.")
    world.facts["blessing_given"] = True


def act_resolve(world: World) -> None:
    hero = world.get("hero")
    minion = world.get("minion")
    mystery = world.facts["mystery"]
    minion.meters["problem"] = 0.0
    minion.meters["helpfulness"] = 1.0
    minion.meters["hiding"] = 0.0
    minion.memes["worry"] = 0.0
    minion.memes["pride"] = 1.0
    minion.memes["relief"] = 1.0
    world.get("mystery_entity").meters["solved"] = 1.0
    world.say(f"Together, {hero.label} and the minion {mystery.helpful_action}.")
    world.say(f'"We solved it!" cried {hero.label}.')
    world.say(f'"We helped it," said {minion.label}, with a smile as small as a pea.')
    world.facts["minion_helped"] = True
    world.say(mystery.ending)
    world.say(mystery.lesson)


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_open(world)
    world.para()
    act_search(world)
    act_understand(world)
    act_bless(world)
    act_resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        f"Write a nursery rhyme set in {world.setting} about {params.hero} and a minion named {params.minion}.",
        f"Include a mystery to solve: {mystery.opening}.",
        "Use a twist showing that the minion was helping, then include a spoken blessing and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What mystery did {params.hero} discover in {world.setting}?",
            answer=f"{params.hero} discovered that {mystery.opening}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was that {mystery.clue}.",
        ),
        QAItem(
            question=f"What was the twist about {params.minion}?",
            answer=f"The twist was that {mystery.hidden_truth}; the minion was trying to help rather than cause harm.",
        ),
        QAItem(
            question=f"What blessing did {params.hero} give?",
            answer=f"{params.hero} gave a gentle blessing: “{BLESSINGS[world.facts['params'].blessing_style]}.”",
        ),
        QAItem(
            question="How was the mystery resolved?",
            answer=f"Together, {params.hero} and the minion {mystery.helpful_action}.",
        ),
        QAItem(
            question="What did the final image show?",
            answer=mystery.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nursery?",
            answer="A nursery is a room prepared for a baby or young child, often with a crib, toys, and gentle lights.",
        ),
        QAItem(
            question="What is a minion in this storyworld?",
            answer="A minion is a tiny helper creature. The minion may look mischievous, but its actions should be understood before they are judged.",
        ),
        QAItem(
            question="What does bless mean here?",
            answer="Here, bless means to offer kind words or a good wish for someone's safety, peace, or happiness.",
        ),
        QAItem(
            question="What makes a mystery kind to solve?",
            answer="A kind mystery uses clues, careful listening, and helpful action instead of blame alone.",
        ),
        QAItem(
            question="What is the twist in these stories?",
            answer="The twist is that an action that first looks troublesome has a caring reason behind it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = [f"type={entity.kind}"]
        if entity.location:
            parts.append(f"location={entity.location}")
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {entity.label}; " + "; ".join(parts))
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


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
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        nursery="moonroom",
        hero="Luna",
        minion="Bobo",
        moon="silver moon",
        mystery="missing_lullaby",
        rhyme_style=0,
        twist_style=1,
        blessing_style=0,
    ),
    StoryParams(
        nursery="starroom",
        hero="Mimi",
        minion="Tink",
        moon="round moon",
        mystery="vanishing_star",
        rhyme_style=1,
        twist_style=2,
        blessing_style=2,
    ),
    StoryParams(
        nursery="cloudroom",
        hero="Nell",
        minion="Pogo",
        moon="pearl moon",
        mystery="crooked_shadow",
        rhyme_style=3,
        twist_style=0,
        blessing_style=3,
    ),
    StoryParams(
        nursery="sunroom",
        hero="Pip",
        minion="Midge",
        moon="little moon",
        mystery="lost_lantern",
        rhyme_style=4,
        twist_style=4,
        blessing_style=4,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible ASP nursery settings:")
        for (name,) in asp_valid():
            print(f"  {name}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not generate enough distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.hero} / {params.minion} in {params.nursery}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
