#!/usr/bin/env python3
"""
A small folk-tale storyworld about a spare auditorium, a surprising turn,
sharing, and the sound effects that bring a quiet stage to life.
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

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Auditorium:
    name: str
    spare: bool = True
    seats: int = 0
    curtain: str = "patched blue"


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, auditorium: Auditorium) -> None:
        self.auditorium = auditorium
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


AUDITORIUMS = {
    "auditorium": Auditorium(
        name="the spare village auditorium",
        spare=True,
        seats=12,
        curtain="patched blue",
    )
}

NAMES = ["Luna", "Milo", "Pip", "Nia", "Oren", "Tavi", "Suri", "Bram"]

TALES = [
    {
        "key": "empty_stage",
        "premise": "the village play was meant to begin in a spare auditorium with no painted scenery",
        "problem": "the audience could not see the actors clearly behind the dim curtain",
        "first_plan": "kept the only lantern beside the storyteller's chair",
        "twist": "a loose floorboard tapped whenever someone crossed the stage, making a perfect drumbeat",
        "sound": "tap, tap, tap",
        "sharing": "moved the lantern to the middle and invited every actor to make a useful sound",
        "ending": "the patched curtain glowed while the whole village clapped to the floorboard's beat",
        "lesson": "a small resource grows when everyone is allowed to share it",
    },
    {
        "key": "missing_dragon",
        "premise": "the village play was ready in a spare auditorium, but the dragon puppet had vanished",
        "problem": "the hero feared the story would have no exciting ending",
        "first_plan": "searched alone beneath the tallest prop table",
        "twist": "the missing dragon was not a puppet at all but a shadow cast by three friends holding blankets",
        "sound": "whoosh, whoosh",
        "sharing": "shared the blankets, the lantern, and the dragon's roar among the waiting actors",
        "ending": "three blanket wings swept across the spare auditorium as the little dragon bowed",
        "lesson": "a story can become richer when many hands carry one idea",
    },
    {
        "key": "quiet_thunder",
        "premise": "rain kept the village performers inside a spare auditorium on festival morning",
        "problem": "the storm outside was so loud that nobody could hear the important lines",
        "first_plan": "asked one performer to shout over the rain",
        "twist": "the old stage drum could copy the storm more gently than any voice",
        "sound": "boom, rumble, patter",
        "sharing": "passed the drum around and let each child choose one soft sound for the story",
        "ending": "the audience heard every word while the shared drum made a friendly indoor storm",
        "lesson": "listening and sharing can turn a troublesome noise into music",
    },
    {
        "key": "two_crowns",
        "premise": "two actors arrived at the spare auditorium wearing one bright paper crown between them",
        "problem": "each believed the king's part belonged only to them",
        "first_plan": "hid the crown behind the curtain until the argument ended",
        "twist": "the play's old script revealed that the kingdom had always needed two kings who ruled together",
        "sound": "ta-da, ta-da",
        "sharing": "cut the crown into two matching bands and shared the royal speech",
        "ending": "two paper crowns shone as the actors spoke the final line together",
        "lesson": "sharing a role can make a friendship stronger than winning it alone",
    },
    {
        "key": "echoing_well",
        "premise": "a folk tale about a well was rehearsed in the spare auditorium",
        "problem": "the pretend well made no sound, so the tale felt flat",
        "first_plan": "claimed the loudest drum for one performer",
        "twist": "the empty auditorium itself answered with a long, warm echo",
        "sound": "hello-o, hello-o",
        "sharing": "placed the drum in the center and let every actor add a voice to the echo",
        "ending": "the final hello-o traveled from the stage to every seat",
        "lesson": "what seems empty may be waiting for many voices",
    },
]

OPENINGS = [
    "Long ago,",
    "In a village where everyone knew the old stories,",
    "One bright morning,",
    "At the edge of the market day,",
    "When the festival bell rang,",
]

DIALOGUE_CONCERNS = [
    "If I keep the best part, the play will be safe",
    "What if the audience laughs at our empty stage",
    "I want the story to sound alive",
    "We cannot solve this by pulling the props away from one another",
]

DIALOGUE_REPLIES = [
    "Then let us test what the room can teach us",
    "A spare place is not a useless place",
    "We can give each person one part to carry",
    "The story belongs to the village, not to one pair of hands",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about sharing sound effects in a spare auditorium."
    )
    parser.add_argument("--setting", choices=sorted(AUDITORIUMS))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "auditorium"
    hero_name = args.name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero_name]
    friend_name = args.friend or rng.choice(choices)
    if hero_name == friend_name:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(setting=setting, hero_name=hero_name, friend_name=friend_name)


def tell(params: StoryParams) -> World:
    if params.setting not in AUDITORIUMS:
        raise StoryError(f"Unknown setting: {params.setting}")

    template = AUDITORIUMS[params.setting]
    world = World(
        Auditorium(
            name=template.name,
            spare=template.spare,
            seats=template.seats,
            curtain=template.curtain,
        )
    )
    rng = random.Random(params.seed if params.seed is not None else 0)
    tale = rng.choice(TALES)
    concern = rng.choice(DIALOGUE_CONCERNS)
    reply = rng.choice(DIALOGUE_REPLIES)

    hero = world.add(
        Entity(
            id=params.hero_name,
            type="hare",
            label="a quick young storyteller",
            traits=["eager", "inventive"],
            meters={"confidence": 1.0, "patience": 0.4},
            memes={"ownership": 1.0, "hope": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            type="wren",
            label="a careful young performer",
            traits=["thoughtful", "musical"],
            meters={"confidence": 0.8, "patience": 0.8},
            memes={"belonging": 1.0, "curiosity": 1.0},
        )
    )

    world.auditorium.seats = rng.choice([10, 12, 14])
    world.say(
        f"{OPENINGS[rng.randrange(len(OPENINGS))]} {hero.id}, {hero.label}, "
        f"and {friend.id}, {friend.label}, prepared a village tale in "
        f"{world.auditorium.name}. It was spare: {world.auditorium.curtain} hung "
        f"over a plain stage, and only {world.auditorium.seats} seats waited in the room."
    )
    world.say(f"{tale['premise'].capitalize()}.")
    world.para()

    world.say(
        f"The trouble was that {tale['problem']}. {hero.id} {tale['first_plan']}, "
        f"while {friend.id} held the script close."
    )
    world.say(f'"{concern}," said {friend.id}.')
    world.say(
        f'"{reply}," said {hero.id}. "Let us listen before we decide what the stage lacks."'
    )
    world.say(
        f"Then came the twist: {tale['twist']}. From behind the curtain rose the sound "
        f"{tale['sound']}."
    )
    world.para()

    hero.memes["ownership"] = 0.0
    hero.memes["generosity"] = 1.0
    hero.meters["patience"] = 1.0
    friend.memes["belonging"] = 2.0
    friend.memes["sharing"] = 1.0
    friend.meters["confidence"] = 1.0

    world.say(f'"You found a way for all of us," said {friend.id}.')
    world.say(
        f'"And you heard the room," said {hero.id}. "Let us use it together."'
    )
    world.say(
        f"At once, the performers {tale['sharing']}. The sound effects became part of "
        f"the tale instead of a prize kept by one actor."
    )
    world.say(
        f"The play began. Every sound had a purpose, every performer had a turn, and "
        f"the spare auditorium seemed less empty with each shared beat."
    )
    world.para()

    world.say(
        f"When the tale ended, {tale['ending']}. The villagers carried home the lesson "
        f"that {tale['lesson']}."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        tale=tale,
        concern=concern,
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
    tale = world.facts["tale"]
    return [
        f"Write a folk tale set in a spare auditorium where {tale['premise']}.",
        f"Tell a dialogue-rich story with a twist involving {tale['sound']}.",
        f"Write a child-friendly tale about sharing sound effects so that {tale['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    tale = facts["tale"]
    hero = facts["hero"]
    friend = facts["friend"]
    return [
        QAItem(
            question=f"What problem did {hero.id} and {friend.id} face?",
            answer=f"They faced this problem: {tale['problem']}. {hero.id} first {tale['first_plan']}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {tale['twist']}. The sound effect was {tale['sound']}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} use sharing to solve the problem?",
            answer=f"They {tale['sharing']}. This gave every performer a meaningful part in the play.",
        ),
        QAItem(
            question="Why was the auditorium called spare?",
            answer="It was called spare because it had simple scenery, a patched curtain, and few supplies, but the performers discovered that the room still had useful possibilities.",
        ),
        QAItem(
            question="What lesson did the villagers learn?",
            answer=f"They learned that {tale['lesson']}. The ending showed this when {tale['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an auditorium?",
            answer="An auditorium is a large room where people gather to watch performances, hear talks, or listen to music.",
        ),
        QAItem(
            question="What does spare mean in this story?",
            answer="Spare means simple or lacking extra decorations and supplies. A spare place can still become useful through imagination.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made or recorded sound that helps an audience understand a scene or feel its mood.",
        ),
        QAItem(
            question="Why is sharing helpful in a performance?",
            answer="Sharing lets several performers contribute ideas and take turns, so the performance can become richer and fairer.",
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
        f"{world.auditorium.name}: spare={world.auditorium.spare}, "
        f"seats={world.auditorium.seats}, curtain={world.auditorium.curtain!r}"
    )
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    tale = world.facts.get("tale", {})
    if tale:
        lines.append(
            f"turn={tale['key']}, sound_effect={tale['sound']}, "
            "resolution=shared performance"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(auditorium).
feature(twist).
feature(sharing).
feature(sound_effects).
style(folk_tale).
resource(spare).
shared_resource(sound_effects).
has_turn(twist).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "auditorium"),
            asp.fact("resource", "spare"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "sound_effects"),
            asp.fact("style", "folk_tale"),
            asp.fact("shared_resource", "sound_effects"),
        ]
    )


def asp_program(show: str = "#show feature/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show setting/1.\n#show resource/1.\n#show feature/1.\n#show style/1."
        )
    )
    settings = set(asp.atoms(model, "setting"))
    resources = set(asp.atoms(model, "resource"))
    features = set(asp.atoms(model, "feature"))
    styles = set(asp.atoms(model, "style"))

    if settings != {("auditorium",)}:
        print("Mismatch in ASP setting facts.")
        return 1
    if resources != {("spare",)}:
        print("Mismatch in ASP resource facts.")
        return 1
    if features != {("twist",), ("sharing",), ("sound_effects",)}:
        print("Mismatch in ASP feature facts.")
        return 1
    if styles != {("folk_tale",)}:
        print("Mismatch in ASP style facts.")
        return 1

    sample = generate(
        StoryParams(
            setting="auditorium",
            hero_name="Luna",
            friend_name="Milo",
            seed=17,
        )
    )
    required = ["spare", "auditorium", "twist", "sharing", "sound"]
    if not all(word in sample.story.lower() for word in required):
        print("Generated story did not exercise the required narrative concepts.")
        return 1
    if len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
        print("Generated story did not provide sufficient QA.")
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show setting/1.\n#show resource/1.\n#show feature/1.\n#show style/1."
            )
        )
        atoms = []
        for predicate in ("setting", "resource", "feature", "style"):
            atoms.extend((predicate, value) for value, in asp.atoms(model, predicate))
        print(sorted(atoms))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, tale in enumerate(TALES):
            params = StoryParams(
                setting="auditorium",
                hero_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target and attempt < max(50, target * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
