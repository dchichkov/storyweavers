#!/usr/bin/env python3
"""
A child-friendly mystery storyworld about a minister, strange sound effects,
kindness, and a misunderstanding that is solved by careful listening.
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

_repo_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Hall:
    name: str
    location: str
    doors: int
    bell_tuned: bool = True


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    minister_name: str
    seed: Optional[int] = None


@dataclass
class World:
    hall: Hall
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


HALLS = {
    "chapel": Hall("the moonlit chapel", "beside the village pond", 3, True),
    "meetinghouse": Hall("the old meetinghouse", "at the end of Lantern Lane", 2, True),
    "garden_hall": Hall("the garden hall", "behind the community garden", 2, True),
}

NAMES = ["Luna", "Milo", "Nia", "Theo", "Pip", "Mara", "Jonah", "Ivy"]
MINISTERS = ["Minister Rowan", "Minister Bell", "Minister Ada", "Minister Sam"]

MYSTERIES = [
    {
        "key": "midnight_bell",
        "premise": "the hall bell rang three times before the evening gathering",
        "sound": "clang-clang-clang",
        "clue": "a loose blue ribbon was caught around the bell rope",
        "truth": "the wind had pulled the ribbon against the rope through an open window",
        "misunderstanding": "Luna thought the minister had rung the warning bell because someone had broken a rule",
        "action": "closed the window, freed the ribbon, and tested the bell rope gently",
        "ending": "the bell gave one warm note as the ribbon was tied safely to the notice board",
        "lesson": "a surprising sound is a clue, not proof of blame",
    },
    {
        "key": "hollow_steps",
        "premise": "heavy footsteps echoed behind the storage room",
        "sound": "thump, thump, scrape",
        "clue": "dusty flour marks led from a tipped basket to the echoing wall",
        "truth": "a rolling sack had bumped the wall and made the floorboards answer back",
        "misunderstanding": "Luna thought Minister Rowan was hiding an angry visitor",
        "action": "followed the flour marks, moved the basket with permission, and listened beside the wall",
        "ending": "the last scrape became a cheerful drumbeat for the gathering",
        "lesson": "kind questions can turn a frightening guess into a simple answer",
    },
    {
        "key": "whispering_pipe",
        "premise": "a whisper seemed to travel through the pipes beneath the kitchen",
        "sound": "pssst... plink... pssssst",
        "clue": "a spoon trembled whenever the water tap was turned halfway",
        "truth": "air in the old pipe was making the whisper and tapping the spoon",
        "misunderstanding": "Luna thought the minister had promised a secret meeting without telling anyone",
        "action": "turned off the tap, placed a cup beneath the drip, and asked the caretaker to inspect the pipe",
        "ending": "the repaired tap made only a quiet, ordinary drop",
        "lesson": "checking a sound kindly is wiser than inventing a secret around it",
    },
    {
        "key": "creaking_puppet",
        "premise": "a puppet in the children's room groaned whenever the door moved",
        "sound": "creeeak... groan",
        "clue": "a paper star was wedged between the puppet's wooden shoe and the floor",
        "truth": "the shoe was pressing the paper star against a loose board",
        "misunderstanding": "Luna thought the minister disliked the children's noisy play",
        "action": "asked the children to pause, removed the paper star, and rubbed wax on the loose board",
        "ending": "the puppet bowed silently while the children applauded",
        "lesson": "kindness makes room for play while still caring for a shared place",
    },
    {
        "key": "rattling_window",
        "premise": "a window rattled during Minister Ada's quiet welcome",
        "sound": "rat-a-tat-tat",
        "clue": "a pebble sat on the outside sill beneath a branch of shaking ivy",
        "truth": "the branch had dropped the pebble against the glass",
        "misunderstanding": "Luna thought an impatient guest was tapping to interrupt the minister",
        "action": "looked outside with the minister, moved the pebble, and tied back the ivy",
        "ending": "the window showed the stars without making another sound",
        "lesson": "patience lets everyone be heard before a judgment begins",
    },
    {
        "key": "hidden_chimes",
        "premise": "soft chimes drifted from a locked side room",
        "sound": "ting... ting-ting",
        "clue": "a trail of bright beads ran from the room to a vent above the choir shelf",
        "truth": "air from the warming stove was moving a forgotten string of beads",
        "misunderstanding": "Luna thought the minister had locked away a sad child",
        "action": "asked Minister Bell to unlock the room, checked it together, and lifted the beads from the vent",
        "ending": "the beads became a kindness chain on the welcome table",
        "lesson": "when worry grows, bring another person close and look together",
    },
]

OPENINGS = [
    "At dusk,",
    "Just before the village gathering,",
    "On a cool evening,",
    "When the lanterns first glowed,",
    "As rain softened the road,",
]

QUESTIONS = [
    "Did you hear that?",
    "Could we check before we decide what it means?",
    "What if the sound has an ordinary cause?",
    "May I look with you?",
    "Should we ask the minister instead of guessing?",
]

REPLIES = [
    "Yes. We can investigate gently.",
    "Of course. No one should be blamed without knowing the facts.",
    "That is a kind idea. Let us listen carefully.",
    "Please do. A mystery is easier when we share it.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A ministerial sound-effects mystery.")
    parser.add_argument("--setting", choices=HALLS.keys())
    parser.add_argument("--name")
    parser.add_argument("--minister")
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
    hero = args.name or rng.choice(NAMES)
    ministers = [m for m in MINISTERS if m != hero]
    minister = args.minister or rng.choice(ministers)
    setting = args.setting or rng.choice(list(HALLS))
    return StoryParams(setting=setting, hero_name=hero, minister_name=minister)


def tell(params: StoryParams) -> World:
    if params.setting not in HALLS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_name == params.minister_name:
        raise StoryError("The listener and minister must have different names.")

    template = HALLS[params.setting]
    hall = Hall(template.name, template.location, template.doors, template.bell_tuned)
    world = World(hall)
    rng = random.Random(params.seed if params.seed is not None else 0)
    mystery = rng.choice(MYSTERIES)
    question = rng.choice(QUESTIONS)
    reply = rng.choice(REPLIES)

    hero = world.add(Entity(
        id=params.hero_name,
        type="child",
        label=params.hero_name,
        role="careful listener",
        meters={"curiosity": 1.0, "worry": 0.7},
        memes={"kindness": 1.0, "uncertainty": 1.0},
    ))
    minister = world.add(Entity(
        id=params.minister_name,
        type="person",
        label=params.minister_name,
        role="minister",
        meters={"patience": 1.0, "attention": 1.0},
        memes={"welcome": 1.0, "trust": 1.0},
    ))

    world.say(
        f"{OPENINGS[rng.randrange(len(OPENINGS))]} {params.hero_name} arrived at "
        f"{hall.name}, which stood {hall.location}. {params.minister_name}, the minister, "
        "was arranging lanterns for the evening gathering."
    )
    world.say(f"Then the quiet place filled with a strange sound: {mystery['sound']}.")
    world.say(f"It began when {mystery['premise']}.")
    world.para()

    world.say(
        f"{mystery['misunderstanding']}. The sound made {params.hero_name}'s worry rise, "
        "but the minister did not scold or laugh."
    )
    world.say(f"'{question}' {params.hero_name} asked.")
    world.say(f"'{reply}' {params.minister_name} answered.")
    world.say(
        f"Together they found this clue: {mystery['clue']}. "
        "That small detail changed the mystery from a frightening guess into a question they could test."
    )
    world.para()

    world.say(
        f"{params.minister_name} said, 'Let us be kind to everyone involved, even while we investigate.'"
    )
    world.say(
        f"They {mystery['action']}. At last they discovered that {mystery['truth']}."
    )
    world.say(
        f"{params.hero_name} apologized for the misunderstanding, and {params.minister_name} "
        "thanked the child for speaking honestly instead of keeping the worry secret."
    )
    world.para()

    hero.meters["worry"] = 0.0
    hero.meters["curiosity"] = 1.0
    hero.memes["uncertainty"] = 0.0
    hero.memes["kindness"] = 2.0
    minister.meters["patience"] = 1.0
    minister.memes["trust"] = 2.0

    world.say(
        f"The mystery ended with a promise: when a sound seems strange, they would listen, "
        "ask kindly, and check the evidence before blaming anyone."
    )
    world.say(
        f"The lesson was that {mystery['lesson']}. {mystery['ending']}."
    )

    world.facts.update(
        hero=hero,
        minister=minister,
        mystery=mystery,
        question=question,
        reply=reply,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        f"Write a child-friendly mystery about a minister and the sound effect {mystery['sound']}.",
        "Tell a dialogue-rich story in which kindness resolves a misunderstanding.",
        f"Write a gentle mystery whose lesson is that {mystery['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    mystery = facts["mystery"]
    hero: Entity = facts["hero"]
    minister: Entity = facts["minister"]
    return [
        QAItem(
            question=f"What sound started {hero.id}'s mystery?",
            answer=f"The mystery began with the sound effect {mystery['sound']}, heard when {mystery['premise']}.",
        ),
        QAItem(
            question=f"What misunderstanding did {hero.id} have?",
            answer=f"{hero.id} thought that {mystery['misunderstanding'].split(' thought ', 1)[-1].rstrip('.')}. "
            "That guess was worrying, but it was not supported by evidence.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {minister.id} solve the mystery?",
            answer=f"They noticed that {mystery['clue']}. The clue pointed them toward the real cause instead of blame.",
        ),
        QAItem(
            question=f"How did {hero.id} and {minister.id} investigate kindly?",
            answer=f"They {mystery['action']}. They listened to each other and checked the facts together.",
        ),
        QAItem(
            question="What lesson did the mystery teach?",
            answer=f"It taught that {mystery['lesson']}. The ending showed this when {mystery['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a minister do?",
            answer="A minister is a person who leads or serves a community's religious gatherings and helps care for its people.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a noise used to represent an action, object, or event, such as a bell ringing or a window rattling.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong meaning from a situation or from another person's actions.",
        ),
        QAItem(
            question="Why is kindness useful during a mystery?",
            answer="Kindness helps people ask questions without blaming others, so they can share information and discover what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(
        f"hall={world.hall.name!r} location={world.hall.location!r} "
        f"doors={world.hall.doors} bell_tuned={world.hall.bell_tuned}"
    )
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"mystery={world.facts['mystery']['key']}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(chapel).
setting(meetinghouse).
setting(garden_hall).
feature(sound_effects).
feature(kindness).
feature(misunderstanding).
role(minister).
resolved_by(kindness,misunderstanding).
requires(mystery,sound_effects).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join([
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("role", "minister"),
        asp.fact("resolved_by", "kindness", "misunderstanding"),
        asp.fact("requires", "mystery", "sound_effects"),
    ])


def asp_program(show: str = "#show feature/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show feature/1."))
    found = set(asp.atoms(model, "feature"))
    expected = {
        ("sound_effects",),
        ("kindness",),
        ("misunderstanding",),
    }
    if found != expected:
        print(f"Mismatch in ASP features: expected {expected}, got {found}")
        return 1

    for seed in range(5):
        params = StoryParams(
            setting="chapel",
            hero_name="Luna",
            minister_name="Minister Rowan",
            seed=seed,
        )
        sample = generate(params)
        if not sample.story or "minister" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
        if not any(item.answer for item in sample.story_qa):
            print("Generated QA verification failed.")
            return 1

    print("OK: ASP/Python parity and generated stories verified.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show feature/1."))
        print(sorted(set(asp.atoms(model, "feature"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(HALLS):
            params = StoryParams(
                setting=setting,
                hero_name="Luna",
                minister_name=MINISTERS[index % len(MINISTERS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
