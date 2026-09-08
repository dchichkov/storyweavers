#!/usr/bin/env python3
"""
A small standalone bedtime-story world about a scallywag, a thong, and the
gentle sound effects that help a nighttime mistake become a peaceful repair.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "scallywag"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class NightWorld:
    setting: str
    moon: str = "the sleepy moon"
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    scallywag: str
    sleeper: str
    setting: str
    bedtime_object: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    object_name: str
    premise: str
    mischief: str
    sound: str
    consequence: str
    clue: str
    dialogue_problem: str
    careful_action: str
    reveal: str
    repair: str
    outcome: str
    lesson: str
    ending: str


SCALLYWAGS = ["Pip", "Milo", "Nell", "Toby", "Rory", "Bram"]
SLEEPERS = ["Luna", "Mara", "Bea", "Ollie", "Ivy", "Sami"]
SETTINGS = [
    "a little cottage beside the whispering marsh",
    "an attic room above a moonlit bakery",
    "a snug tree house at the edge of the dark garden",
    "a tiny lighthouse on a quiet hill",
]
BEDTIME_OBJECTS = [
    "a striped blanket",
    "a brass night-lamp",
    "a soft pillow",
    "a wooden music box",
    "a blue bedtime book",
]

SCENARIOS = [
    Scenario(
        key="window_ribbon",
        object_name="a red ribbon thong",
        premise="had promised to tuck the windows closed before bedtime",
        mischief="tied a bright thong around the window latch and gave it a cheeky tug",
        sound="twang",
        consequence="the latch sprang open and moonlight spilled across the sleeping room",
        clue="the ribbon hummed only when the cold night air touched it",
        dialogue_problem="The window is singing because I pulled the thong too tightly.",
        careful_action="loosened the knot while listening for the softest twang",
        reveal="the thong was not a toy at all but a wind marker that showed which latch was loose",
        repair="retied the ribbon gently and fastened the latch",
        outcome="the window rested quietly and the room grew warm again",
        lesson="a playful thing still needs careful hands",
        ending="the red ribbon curled like a tiny smile while everyone drifted toward sleep",
    ),
    Scenario(
        key="bell_pouch",
        object_name="a silver bell thong",
        premise="was carrying a little bedtime bell to the nursery",
        mischief="swung the bell thong in a wide circle to make the hallway feel like a parade",
        sound="jingle-jangle",
        consequence="the noise woke the baby birds nesting above the door",
        clue="the bell grew quiet whenever someone held the thong with two fingers",
        dialogue_problem="I made the sound too big, and now the little birds are frightened.",
        careful_action="held the thong lightly and hummed a slower tune",
        reveal="the bell's tiny loop had been made for a quiet goodnight signal",
        repair="guided the birds back to their nest and hung the bell beside the cradle",
        outcome="one soft jingle told the whole house that bedtime had begun",
        lesson="gentleness can turn a loud mistake into a kind message",
        ending="the silver bell whispered once, and the baby birds tucked their heads beneath their wings",
    ),
    Scenario(
        key="slippery_rope",
        object_name="a blue bedtime thong",
        premise="had promised to bring a warm blanket across the creaky porch",
        mischief="dragged the thong behind him like a pirate rope",
        sound="scritch-scritch",
        consequence="the blanket snagged on a nail and slid into a puddle",
        clue="the thong made a different sound where the porch boards were cracked",
        dialogue_problem="It was warning me about the broken board, but I was pretending to be a captain.",
        careful_action="followed the sound and tied a bright loop around the dangerous board",
        reveal="the thong was a trail marker left by the housekeeper for nighttime feet",
        repair="lifted the blanket, dried it, and placed a lantern beside the marked board",
        outcome="the blanket reached the porch chair without another scrape",
        lesson="listening is wiser than pretending not to hear",
        ending="the blue thong rested by the lantern as the porch settled into a sleepy creak",
    ),
    Scenario(
        key="sleepy_drum",
        object_name="a golden drum thong",
        premise="was helping prepare a quiet goodnight song",
        mischief="pulled the thong across an empty tin to make a drum",
        sound="boom-boom",
        consequence="the sound startled the old cat from its warm basket",
        clue="the cat purred whenever the thong was plucked softly",
        dialogue_problem="I thought a bedtime song needed a big boom, but the cat wanted a little sound.",
        careful_action="changed the beat to a gentle plink and stroked the cat's fur",
        reveal="the thong was an old music string meant to copy a purring rhythm",
        repair="made a quiet song and returned the cat to its basket",
        outcome="the cat's purr became the final note of the lullaby",
        lesson="the right size of sound depends on who is listening",
        ending="purr, plink, hush—the whole room floated softly toward dreams",
    ),
    Scenario(
        key="moonlit_sash",
        object_name="a green thong sash",
        premise="had promised to put away the dress-up clothes before the lamps went out",
        mischief="wore the thong as a pirate sash and marched across the rug",
        sound="tap-tap-tap",
        consequence="his wooden boots knocked over a tower of story blocks",
        clue="the thong brushed the blocks whenever he turned too quickly",
        dialogue_problem="I was watching my pirate feet instead of the green sash at my side.",
        careful_action="removed the sash, gathered the blocks, and walked slowly around the room",
        reveal="the thong had a tiny bell woven into its edge to warn of nearby treasures",
        repair="folded the sash into the costume chest and rebuilt the tower",
        outcome="the blocks stood taller than before and no one had to stumble over them",
        lesson="noticing what is close can prevent a bigger tumble",
        ending="the green sash slept in the chest beneath a patch of friendly moonlight",
    ),
    Scenario(
        key="rainy_roof",
        object_name="a yellow thong cord",
        premise="was checking the small roof above the bedroom before the rain grew heavy",
        mischief="flicked the cord at the rain barrel like a sailor's whip",
        sound="plop-plop",
        consequence="the barrel tipped and water ran toward the doorstep",
        clue="the cord made a hollow tap where the drain was blocked",
        dialogue_problem="The cord showed me the stopped drain, but I was busy making sailor sounds.",
        careful_action="cleared the leaves and tied the cord beside the drain as a reminder",
        reveal="the thong cord had been used to test whether rainwater could pass",
        repair="righted the barrel and swept the water away from the door",
        outcome="the roof held firm while the rain tapped a peaceful rhythm",
        lesson="a tool becomes useful when play makes room for purpose",
        ending="plop, patter, hush—the yellow cord gleamed beside the clear drain",
    ),
]

TELLING_MODES = ["whisper", "dialogue", "moonlight", "rain", "lullaby", "mystery"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime Story storyworld with a scallywag, a thong, and sound effects."
    )
    parser.add_argument("--scallywag", choices=SCALLYWAGS)
    parser.add_argument("--sleeper", choices=SLEEPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--bedtime-object", choices=BEDTIME_OBJECTS)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scallywag = args.scallywag or rng.choice(SCALLYWAGS)
    sleeper = args.sleeper or rng.choice([name for name in SLEEPERS if name != scallywag])
    setting = args.setting or rng.choice(SETTINGS)
    bedtime_object = args.bedtime_object or rng.choice(BEDTIME_OBJECTS)
    return StoryParams(
        scallywag=scallywag,
        sleeper=sleeper,
        setting=setting,
        bedtime_object=bedtime_object,
        seed=None,
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("domain", "bedtime_story"),
        asp.fact("feature", "sound_effects"),
        asp.fact("style", "bedtime"),
        asp.fact("seed_word", "scallywag"),
        asp.fact("seed_word", "thong"),
        asp.fact("value", "gentleness"),
        asp.fact("value", "repair"),
    ]
    return "\n".join(facts)


ASP_RULES = r"""
required_feature(sound_effects).
required_style(bedtime).
required_word(scallywag).
required_word(thong).

covered :-
    feature(sound_effects),
    style(bedtime),
    seed_word(scallywag),
    seed_word(thong).

#show covered/0.
#show feature/1.
#show style/1.
#show seed_word/1.
"""


def asp_program(show: str = "#show covered/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    covered = asp.atoms(model, "covered")
    features = asp.atoms(model, "feature")
    styles = asp.atoms(model, "style")
    words = sorted(asp.atoms(model, "seed_word"))
    if covered and features == [("sound_effects",)] and styles == [("bedtime",)] and words == [("scallywag",), ("thong",)]:
        print("OK: ASP facts and rules cover the bedtime sound-effects domain.")
        return 0
    print("MISMATCH: ASP domain coverage is incomplete.")
    return 1


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    mode = params.telling_mode or "whisper"
    name = params.scallywag
    sleeper = params.sleeper
    setting = params.setting

    if mode == "dialogue":
        return [
            f'"Is it bedtime already?" {sleeper} asked.',
            f'"Almost," said {name}, the little scallywag, as the house settled in {setting}.',
        ]
    if mode == "moonlight":
        return [
            f"Moonlight lay in a silver square across {setting}.",
            f"{name}, a small scallywag with a large plan, was helping {sleeper} get ready for sleep.",
        ]
    if mode == "rain":
        return [
            f"Rain whispered beyond {setting}, and the clouds tucked the stars away.",
            f"{name}, the household scallywag, carried a bedtime object while {sleeper} waited under the covers.",
        ]
    if mode == "lullaby":
        return [
            f"The night began with a lullaby so soft that even the curtains seemed to listen.",
            f"Then {name}, the little scallywag, found a new way to join the song in {setting}.",
        ]
    if mode == "mystery":
        return [
            f"Something made a curious sound in {setting}.",
            f"{sleeper} opened one sleepy eye, while {name}, the scallywag, tried to look innocent.",
        ]
    return [
        f"At bedtime, {setting} grew quiet except for the soft settling sounds of the house.",
        f"{name}, a cheerful scallywag, was helping {sleeper} prepare for sleep.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.scallywag == params.sleeper:
        raise StoryError("The scallywag and sleeper must be different characters.")
    if params.scenario not in {scenario.key for scenario in SCENARIOS}:
        raise StoryError(f"Unknown bedtime scenario: {params.scenario!r}.")
    scenario = next(item for item in SCENARIOS if item.key == params.scenario)

    world = NightWorld(setting=params.setting)
    scallywag = world.add(
        Entity(
            id=params.scallywag,
            kind="character",
            type="scallywag",
            label="little scallywag",
            phrase=params.scallywag,
            location="bedroom",
            meters={"energy": 0.9, "carefulness": 0.3},
            memes={"mischief": 1.0, "curiosity": 0.8},
            traits=["playful", "restless"],
        )
    )
    sleeper = world.add(
        Entity(
            id=params.sleeper,
            kind="character",
            type="child",
            label="sleepy friend",
            phrase=params.sleeper,
            location="bed",
            meters={"sleepiness": 0.8, "comfort": 0.6},
            memes={"trust": 0.8},
            traits=["patient", "kind"],
        )
    )
    thong = world.add(
        Entity(
            id="thong",
            kind="thing",
            type="cord",
            label="bedtime thong",
            phrase=scenario.object_name,
            owner=params.scallywag,
            location="bedroom",
            meters={"tension": 0.8, "volume": 0.7},
            memes={"purpose_hidden": 1.0, "usefulness": 0.4},
            traits=["bright", "springy"],
        )
    )
    world.facts.update(
        scenario=scenario.key,
        setting=params.setting,
        bedtime_object=params.bedtime_object,
        sound_effect=scenario.sound,
        premise=scenario.premise,
        mischief=scenario.mischief,
        consequence=scenario.consequence,
        clue=scenario.clue,
        reveal=scenario.reveal,
        repair=scenario.repair,
        outcome=scenario.outcome,
        lesson=scenario.lesson,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(
        f"The bedtime plan was simple: {params.scallywag} {scenario.premise}, "
        f"with {params.bedtime_object} waiting nearby."
    )

    world.para()
    world.say(
        random.Random(params.seed).choice(
            [
                f"But a scallywag's fingers are often quicker than a bedtime promise. {params.scallywag} {scenario.mischief}.",
                f'"Just one little trick," {params.scallywag} whispered, and {params.scallywag} {scenario.mischief}.',
                f"The thong looked too tempting to ignore, so {params.scallywag} {scenario.mischief}.",
            ]
        )
    )
    world.say(f"{scenario.sound}! {scenario.consequence}.")
    world.say(f'"What happened?" {sleeper} asked. "{scenario.dialogue_problem}" {params.scallywag} replied.')

    world.para()
    world.say(f"The room became still. Then they noticed that {scenario.clue}.")
    world.say(f'"Let us listen before we fix it," {sleeper} said.')
    world.say(f"{params.scallywag} nodded and {scenario.careful_action}.")
    world.say(f"In the quiet, they discovered that {scenario.reveal}.")

    world.para()
    world.say(f"{params.scallywag} lowered {scallywag.pronoun('possessive')} head and said, “I am sorry.”")
    world.say(f"{sleeper} answered, “Thank you for telling me. We can mend it together.”")
    world.say(f"Together, they {scenario.repair}.")
    world.say(f"{scenario.outcome}.")

    world.para()
    world.say(f"That night, they remembered that {scenario.lesson}.")
    world.say(f"The house became quiet again, and the sound effects softened to a sleepy {scenario.sound}.")
    world.say(f"At last, {scenario.ending}.")

    thong.location = "beside the bedtime object"
    thong.meters["tension"] = 0.1
    thong.meters["volume"] = 0.1
    thong.memes["purpose_hidden"] = 0.0
    thong.memes["usefulness"] = 1.0
    scallywag.meters["energy"] = 0.2
    scallywag.meters["carefulness"] = 0.9
    scallywag.memes["mischief"] = 0.4
    scallywag.memes["accountability"] = 1.0
    sleeper.meters["comfort"] = 1.0
    sleeper.memes["trust"] = 1.0
    world.facts.update(repaired=True, bedtime_restored=True, sound_effects_used=True)

    prompts = [
        f"Write a gentle Bedtime Story about {params.scallywag}, a playful scallywag, and {params.sleeper}. Include a thong and the sound effect “{scenario.sound}.”",
        f"Tell a child-friendly bedtime tale in {params.setting} where a sound helps {params.scallywag} understand a mistake and repair it.",
        f"Write a sleepy story whose ending shows that {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.scallywag} do with the thong?",
            answer=f"{params.scallywag} {scenario.mischief}, which caused {scenario.consequence}.",
        ),
        QAItem(
            question=f"What sound effect appeared when the trouble began?",
            answer=f"The story used the sound effect “{scenario.sound}” when {scenario.consequence}.",
        ),
        QAItem(
            question="What clue helped the characters understand the thong?",
            answer=f"They noticed that {scenario.clue}. This showed them that {scenario.reveal}.",
        ),
        QAItem(
            question=f"How did {params.scallywag} repair the mistake?",
            answer=f"{params.scallywag} apologized and, together with {params.sleeper}, {scenario.repair}. As a result, {scenario.outcome}.",
        ),
        QAItem(
            question="What lesson did the bedtime story teach?",
            answer=f"It taught that {scenario.lesson}. The careful repair made the house peaceful again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a scallywag in a gentle story?",
            answer="A scallywag is a playful character who may make mischief but can still learn, apologize, and help repair the trouble.",
        ),
        QAItem(
            question="How can sound effects help a bedtime story?",
            answer="Sound effects make an action easy to imagine, and a soft sound can show when a noisy problem becomes calm.",
        ),
        QAItem(
            question="What makes this story a bedtime story?",
            answer="It uses a quiet nighttime setting, gentle language, a small repair, and a peaceful ending that leads toward sleep.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            parts = []
            if entity.location:
                parts.append(f"location={entity.location}")
            if entity.meters:
                parts.append(f"meters={entity.meters}")
            if entity.memes:
                parts.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(parts)}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _curated() -> list[StoryParams]:
    return [
        StoryParams(
            scallywag="Pip",
            sleeper="Luna",
            setting=SETTINGS[0],
            bedtime_object=BEDTIME_OBJECTS[0],
            seed=101,
            scenario="window_ribbon",
            telling_mode="whisper",
        ),
        StoryParams(
            scallywag="Milo",
            sleeper="Mara",
            setting=SETTINGS[1],
            bedtime_object=BEDTIME_OBJECTS[3],
            seed=202,
            scenario="sleepy_drum",
            telling_mode="dialogue",
        ),
        StoryParams(
            scallywag="Nell",
            sleeper="Bea",
            setting=SETTINGS[2],
            bedtime_object=BEDTIME_OBJECTS[1],
            seed=303,
            scenario="moonlit_sash",
            telling_mode="moonlight",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        for symbol in model:
            print(symbol)
        return
    if args.verify:
        exit_code = asp_verify()
        if exit_code:
            sys.exit(exit_code)
        test_params = _curated()
        for params in test_params:
            sample = generate(params)
            if not sample.story.strip():
                print("MISMATCH: generated story is empty.")
                sys.exit(1)
            if "scallywag" not in sample.story.lower():
                print("MISMATCH: generated story lacks the required character word.")
                sys.exit(1)
            if "thong" not in sample.story.lower():
                print("MISMATCH: generated story lacks the required object word.")
                sys.exit(1)
            if not any(item.question for item in sample.story_qa):
                print("MISMATCH: generated story lacks story QA.")
                sys.exit(1)
        print("OK: generated stories and QA passed.")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in _curated()]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 20):
            attempts += 1
            attempt_seed = base_seed + attempts
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
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
        if args.all:
            params = sample.params
            header = f"### {params.scallywag} and the bedtime thong"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
