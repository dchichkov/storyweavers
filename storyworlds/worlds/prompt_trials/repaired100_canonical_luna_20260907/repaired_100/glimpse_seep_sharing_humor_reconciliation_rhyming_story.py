#!/usr/bin/env python3
"""
A small rhyming storyworld about a glimpse, a seep, sharing, humor, and
reconciliation.
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
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    name: str
    object_name: str
    weather: str
    dry_spot: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "garden": Setting(
        name="the moonlit garden",
        object_name="a little blue tent",
        weather="a soft spring shower",
        dry_spot="the old oak tree",
    )
}

NAMES = ["Luna", "Milo", "Pip", "Nia", "Toby", "Mira", "Sol", "Cleo"]

SCENES = [
    {
        "key": "rainbow_beetle",
        "premise": "a rainbow beetle flashed beneath a leaf",
        "seep": "rain began to seep through the tent's silver seam",
        "share": "held the lantern while the other tucked a broad leaf over the seam",
        "object": "a bright beetle-shaped button",
        "ending": "the button shone on a shared ribbon beside the dry tent",
        "lesson": "a small glimpse grows brighter when friends share it",
    },
    {
        "key": "cloud_window",
        "premise": "a tiny window in the clouds showed a castle made of light",
        "seep": "a thin stream began to seep under the blanket",
        "share": "passed the blanket back and forth while moving their picnic basket",
        "object": "a cloud-white pebble",
        "ending": "the pebble rested between them as the castle faded into stars",
        "lesson": "sharing the view matters more than claiming the best seat",
    },
    {
        "key": "firefly_map",
        "premise": "one firefly gave a glimpse of a glowing path",
        "seep": "water started to seep into the corner where their map lay",
        "share": "shared the dry paper and copied the path together",
        "object": "a folded firefly map",
        "ending": "the map hung above the oak, marked with two friendly names",
        "lesson": "a shared plan can guide two hearts home",
    },
    {
        "key": "silver_frog",
        "premise": "a silver frog gave a quick glimpse and sprang behind a stone",
        "seep": "muddy water began to seep across the stepping stones",
        "share": "took turns making stepping stones from fallen bark",
        "object": "a smooth silver leaf",
        "ending": "the silver leaf floated in their puddle boat",
        "lesson": "taking turns makes a tricky crossing feel funny and fair",
    },
]

JOKES = [
    "I wanted a dry tent, but the tent wanted a tiny indoor river.",
    "That cloud castle needs a door, a flag, and perhaps a cloud-sized cat.",
    "Our map is not lost; it is merely taking a damp adventure.",
    "If the puddle grows any more, we shall need tickets for the boat ride.",
]

APOLOGIES = [
    "I am sorry I grabbed the best spot instead of asking you to share it.",
    "I was wrong to laugh at your worry before I helped.",
    "I should have listened first and joked second.",
    "I wanted the glimpse for myself, but friendship is brighter when it is shared.",
]

REFLECTIONS = [
    "Their laughter did not erase the trouble; it helped them face it kindly.",
    "The rain kept falling, but the friends no longer felt caught alone.",
    "A glimpse can be brief, while a repaired friendship can last all day.",
    "They discovered that a good joke opens a door, but listening keeps it open.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming glimpse-and-sharing storyworld.")
    parser.add_argument("--setting", choices=SETTINGS.keys())
    parser.add_argument("--name")
    parser.add_argument("--friend")
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
    setting = args.setting or "garden"
    hero = args.name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(choices)
    if hero == friend:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(setting=setting, hero_name=hero, friend_name=friend)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")

    setting_template = SETTINGS[params.setting]
    setting = Setting(**setting_template.__dict__)
    world = World(setting)
    hero = world.add(
        Entity(
            id=params.hero_name,
            type="rabbit",
            label="a quick rabbit",
            traits=["eager", "funny"],
            meters={"curiosity": 1.0},
            memes={"impatience": 1.0, "humor": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            type="mouse",
            label="a careful mouse",
            traits=["observant", "kind"],
            meters={"caution": 1.0},
            memes={"hurt": 0.0, "trust": 1.0},
        )
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    joke = rng.choice(JOKES)
    apology = rng.choice(APOLOGIES)
    reflection = rng.choice(REFLECTIONS)

    friend.memes["hurt"] = 1.0
    world.facts.update(scene=scene, joke=joke, apology=apology, reflection=reflection)

    world.say(
        f"By the oak in the garden, where raindrops danced in a bright silver ring, "
        f"{hero.id} and {friend.id} found {setting.object_name}, snug and small beneath the spring."
    )
    world.say(
        f"Then {scene['premise']}; it was gone in a blink, a sparkling little glimpse "
        f"at the edge of the pink."
    )
    world.para()

    world.say(
        f"But {scene['seep']}, drip by drip, through the floor and along the side. "
        f"{hero.id} pulled the lantern close, while {friend.id} tried to keep the treasure dry inside."
    )
    world.say(
        f"'{hero.id}, you took the best place, and you did not ask me,' said {friend.id}. "
        f"'I wanted to see the glimpse too, not watch it slip away from me.'"
    )
    world.say(f"'{joke}' said {hero.id}, then saw that {friend.id} did not smile.")
    world.para()

    world.say(f"'{apology}' {hero.id} said. 'Will you help me mend the day?'")
    world.say(
        f"{friend.id} nodded. Together they {scene['share']}, while the drops went "
        f"pitter-pat, pitter-patter, away."
    )
    world.say(
        f"They shared the {scene['object']} and the view, then laughed at the "
        f"puddle's silly little shoe. The joke became gentle, the hurt grew light, "
        f"and both friends chose what to do."
    )
    world.para()

    hero.memes.update(impatience=0.0, humor=1.0, reconciled=1.0, sharing=1.0)
    friend.memes.update(hurt=0.0, trust=2.0, reconciled=1.0, sharing=1.0)
    hero.meters["kindness"] = 1.0
    friend.meters["belonging"] = 1.0

    world.say(
        f"They learned that {scene['lesson']}; it was simple and true. "
        f"{reflection}"
    )
    world.say(
        f"At last, {scene['ending']}, while the moon peeked through the blue. "
        f"Two friends, one laugh, and a shared glimpse made the whole wet world new."
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
    scene = world.facts["scene"]
    return [
        f"Write a child-friendly rhyming story in which {scene['premise']}.",
        "Tell a dialogue-rich story about sharing, humor, and reconciliation during a small rainstorm.",
        f"Write a gentle rhyme whose lesson is that {scene['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    hero = world.entities[world.facts.get("hero", next(iter(world.entities)))]
    friend = world.entities[world.facts.get("friend", list(world.entities)[1])]
    return [
        QAItem(
            question=f"What glimpse did {hero.id} and {friend.id} see?",
            answer=f"They saw that {scene['premise']}, giving them a brief, sparkling glimpse.",
        ),
        QAItem(
            question="What problem interrupted their adventure?",
            answer=f"The problem was that {scene['seep']}. The dampness put their shelter and their shared treasure at risk.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel hurt?",
            answer=f"{friend.id} felt hurt because {hero.id} took the best place without asking and did not share the glimpse fairly.",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"{hero.id} apologized, and together they {scene['share']}. They then shared the treasure, used gentle humor, and chose to cooperate.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"They learned that {scene['lesson']}. The ending showed this when {scene['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a glimpse?",
            answer="A glimpse is a quick or brief look at something.",
        ),
        QAItem(
            question="What does seep mean?",
            answer="To seep means to move slowly through a small opening or material, often like water through a crack.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing lets people enjoy resources or experiences together and can make everyone feel included.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of making peace after people have been upset with one another.",
        ),
        QAItem(
            question="How can humor help a friendship?",
            answer="Gentle humor can ease tension, but it should come with listening and care rather than laughing at someone's feelings.",
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
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"setting={world.setting.name}; weather={world.setting.weather}; "
        f"shared=True; reconciled=True"
    )
    return "\n".join(lines)


ASP_RULES = r"""
setting(garden).
seed_word(glimpse).
seed_word(seep).
feature(sharing).
feature(humor).
feature(reconciliation).
style(rhyming_story).
story_ok :- setting(garden), seed_word(glimpse), seed_word(seep),
    feature(sharing), feature(humor), feature(reconciliation),
    style(rhyming_story).
#show story_ok/0.
#show seed_word/1.
#show feature/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "garden"),
            asp.fact("seed_word", "glimpse"),
            asp.fact("seed_word", "seep"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "reconciliation"),
            asp.fact("style", "rhyming_story"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show story_ok/0."))
    if not asp.atoms(model, "story_ok"):
        print("Mismatch: ASP did not approve the storyworld.")
        return 1

    params = StoryParams(
        setting="garden",
        hero_name="Luna",
        friend_name="Milo",
        seed=17,
    )
    sample = generate(params)
    required = ["glimpse", "seep", "sharing", "humor", "reconcil"]
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print(f"Mismatch: generated story lacks required ideas: {', '.join(missing)}")
        return 1
    if len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
        print("Mismatch: generated story lacks required QA coverage.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
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
        print(asp_program("#show story_ok/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show story_ok/0."))
        print(sorted(asp.atoms(model, "story_ok")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            setting="garden",
            hero_name="Luna",
            friend_name="Milo",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        attempts = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and attempts < limit:
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            sample = generate(params)
            attempts += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
