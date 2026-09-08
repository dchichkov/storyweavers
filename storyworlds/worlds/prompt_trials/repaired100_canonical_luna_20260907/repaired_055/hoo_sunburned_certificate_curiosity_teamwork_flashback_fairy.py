#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about Hoo, a sunburned helper, and a
certificate earned through curiosity and teamwork.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the Sunlit Meadow"
    landmarks: list[str] = field(
        default_factory=lambda: [
            "the whispering oak",
            "the silver hill",
            "the old fairy bridge",
        ]
    )


@dataclass(frozen=True)
class Quest:
    id: str
    object_name: str
    clue: str
    danger: str
    first_guess: str
    discovery: str
    helper_action: str
    words: str
    lesson: str
    ending: str


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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {"meadow": Setting()}

QUESTS = [
    Quest(
        "sunstone",
        "the Sunstone",
        "a trail of warm golden feathers leading toward the shadow of the oak",
        "the noon sun burned so brightly that the fairy path shimmered",
        "followed the shining road straight across the open meadow",
        "the feathers were not arrows but invitations to search where shade met sunlight",
        "spread a blue cloak beneath the oak so both friends could study the feathers safely",
        "Look where light and shade touch",
        "curiosity asks a second question, while teamwork makes the answer safe to follow",
        "the Sunstone glowed softly beneath the oak, cool enough for both hands",
    ),
    Quest(
        "moonbell",
        "the Moonbell",
        "three pale bells ringing from different sides of the silver hill",
        "the wind tangled every sound until the hill seemed to sing in circles",
        "climbed the steepest side and chased the loudest ringing",
        "the bells were echoes, and the quietest note pointed toward a hidden hollow",
        "made a listening circle and covered the compass with a leaf so the breeze could not move it",
        "Listen twice before you choose a path",
        "patient curiosity notices what noise tries to hide, and teamwork gives every voice a turn",
        "the Moonbell chimed once in the hollow, like a tiny star waking",
    ),
    Quest(
        "rainbow_thread",
        "the Rainbow Thread",
        "a red gleam caught on the fairy bridge after a brief rain",
        "the bridge stones were slippery and the river rushed below",
        "reached for the gleam from the highest wet stone",
        "the gleam belonged to a thread tied safely to the bridge rail",
        "held the rail while the other friend untied the thread with a twig",
        "A bright clue may still need a careful hand",
        "curiosity finds the treasure, but teamwork remembers how to reach it safely",
        "the Rainbow Thread curled around the certificate like a cheerful ribbon",
    ),
    Quest(
        "acorn_crown",
        "the Acorn Crown",
        "tiny acorn caps arranged in a spiral beneath the whispering oak",
        "the oldest acorn lay under a thorny branch",
        "pulled at the branch without noticing the spiral's missing place",
        "the empty place pointed to a loose twig that could be lifted, not dragged",
        "count the spiral, then lift together",
        "Small patterns can hold large secrets",
        "curiosity sees the pattern, and teamwork frees what one pair of hands cannot move",
        "the Acorn Crown rested on Hoo's head while oak leaves applauded",
    ),
]

NAMES = {
    "girl": ["Luna", "Mira", "Pia", "Nell"],
    "boy": ["Hoo", "Toby", "Finn", "Milo"],
}
TRAITS = ["curious", "bright", "patient", "brave"]
MODES = ["flashback", "moonlight", "question", "riddle", "arrival"]


@dataclass
class StoryParams:
    place: str = "meadow"
    name: str = "Luna"
    gender: str = "girl"
    friend_name: str = "Hoo"
    friend_gender: str = "boy"
    trait: str = "curious"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale storyworld about curiosity, teamwork, and a certificate."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--friend-name", dest="friend_name")
    parser.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "meadow"
    if place not in SETTINGS:
        raise StoryError("This fairy tale belongs in the Sunlit Meadow.")
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(NAMES[gender])
    friend_name = args.friend_name or ("Hoo" if friend_gender == "boy" else rng.choice(NAMES[friend_gender]))
    if name == friend_name:
        raise StoryError("The two companions must have different names.")
    return StoryParams(
        place=place,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
    )


def reasonable(params: StoryParams) -> bool:
    return (
        params.place in SETTINGS
        and params.gender in NAMES
        and params.friend_gender in NAMES
        and params.name != params.friend_name
    )


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    if not reasonable(params):
        raise StoryError("These names and setting cannot form a reasonable tale.")

    world = World(SETTINGS[params.place])
    luna = world.add(Entity(params.name, "character", params.gender))
    hoo = world.add(Entity(params.friend_name, "character", params.friend_gender))
    certificate = world.add(
        Entity("certificate", "thing", "certificate", "a silver-edged certificate")
    )

    route = params.seed if params.seed is not None else sum(
        ord(ch) for ch in params.name + params.friend_name
    )
    quest = QUESTS[route % len(QUESTS)]
    mode = MODES[(route // len(QUESTS)) % len(MODES)]

    if mode == "flashback":
        world.say(
            f"Years later, {luna.id} still remembered the day a fairy certificate "
            f"changed the way she looked at questions."
        )
        world.say(
            f"The memory returned whenever she saw a sunburned traveler or heard "
            f"{hoo.id}'s famous call: \"Hoo!\""
        )
    elif mode == "moonlight":
        world.say(
            f"At moonrise, {luna.id} and {hoo.id} entered the Sunlit Meadow beneath a veil of stars."
        )
        world.say("The fairies had promised a reward to anyone who could solve a hidden riddle.")
    elif mode == "question":
        world.say(f'"Why does the meadow hide its brightest treasures?" {luna.id} asked.')
        world.say(
            f"{hoo.id} scratched his sunburned nose. \"Perhaps it wants us to be curious.\""
        )
    elif mode == "riddle":
        world.say(
            f"A silver leaf fluttered down to {luna.id} and {hoo.id}, bearing a riddle:"
        )
        world.say(f'"{quest.words}," it read.')
    else:
        world.say(
            f"When {luna.id} and {hoo.id} reached the Sunlit Meadow, a fairy bell rang over the grass."
        )
        world.say(
            "The queen had hidden a small treasure and promised a certificate to the team "
            "that found it kindly."
        )

    world.say(
        f"Near {quest.object_name}, {luna.id}, a {params.trait} adventurer, saw "
        f"{quest.clue}."
    )
    world.say(
        f"{hoo.id} was eager to help, although the long walk had left him sunburned "
        "and thirsty."
    )

    world.para()
    add_meme(luna, "curiosity")
    add_meme(hoo, "hope")
    add_meter(luna, "attention")
    add_meter(hoo, "effort")
    world.say(
        f"{luna.id} made a quick guess and {quest.first_guess}. The clue vanished, "
        f"and the danger grew: {quest.danger}."
    )
    world.say(
        f'"Hoo, I think I have failed," {luna.id} said. "Should we give up?"'
    )
    world.say(
        f'"Hoo! No," said {hoo.id}. "Your question brought us here. Let us ask one more."'
    )

    world.para()
    add_meme(hoo, "teamwork")
    add_meme(luna, "patience")
    add_meter(hoo, "helping", 1)
    add_meter(luna, "careful_thinking", 1)
    world.say(f"Together they noticed that {quest.discovery}.")
    world.say(f"{hoo.id} said, 'Let us remember the clue and move slowly.'")
    world.say(f"{luna.id} answered, 'And let us do it together.'")
    world.say(f"Then they {quest.helper_action}.")
    world.say(
        f"The hidden meaning became clear: {quest.words}. Their curiosity had found "
        "the question, and their teamwork had found the answer."
    )

    world.para()
    add_meme(luna, "relief")
    add_meme(hoo, "joy")
    add_meter(luna, "understanding", 1)
    add_meter(hoo, "shared_success", 1)
    world.say(
        f"A fairy queen stepped from behind the grass and placed {quest.object_name} "
        "inside a little crystal box."
    )
    world.say(
        f"She gave {luna.id} and {hoo.id} the {certificate.label}, writing both names "
        "beneath the words: Curiosity and Teamwork."
    )
    world.say(
        f"{luna.id} touched the certificate. \"I will remember this day,\" she said."
    )
    world.say(
        f"{hoo.id} smiled, even though his sunburned cheeks still glowed. \"Hoo! "
        "Then remember it with a friend.\""
    )
    world.say(f"At sunset, {quest.ending}.")
    world.say(
        f"And whenever {luna.id} told the tale again, the old flashback ended with "
        "two voices laughing beneath the fairy stars."
    )

    world.facts.update(
        child=luna,
        friend=hoo,
        certificate=certificate,
        quest=quest,
        mode=mode,
        resolved=True,
        curiosity=True,
        teamwork=True,
        flashback=mode == "flashback",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    quest = world.facts["quest"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        "Write a child-friendly Fairy Tale about curiosity and teamwork in a magical meadow.",
        f"Tell how {child.id} and {friend.id} solved a clue leading to {quest.object_name}.",
        "Include the words hoo, sunburned, and certificate, plus a brief flashback and spoken dialogue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    quest = world.facts["quest"]
    return [
        QAItem(
            f"What first mistake did {child.id} make?",
            f"{child.id} {quest.first_guess}. The quick guess made the clue harder to understand and increased the danger.",
        ),
        QAItem(
            f"How did {friend.id} help?",
            f"{friend.id} encouraged {child.id} to ask one more question and then {quest.helper_action}.",
        ),
        QAItem(
            "What did curiosity and teamwork accomplish?",
            f"Curiosity helped the friends notice that {quest.discovery}, while teamwork helped them act safely and find {quest.object_name}.",
        ),
        QAItem(
            "Why did the fairy queen give them a certificate?",
            f"She gave them a certificate because they solved the mystery through curiosity, patience, and teamwork rather than giving up.",
        ),
        QAItem(
            "What final image showed that the quest was complete?",
            f"At sunset, {quest.ending}. The image showed that the treasure was safe and the friends had succeeded.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is curiosity?",
            "Curiosity is the wish to ask questions, notice details, and learn how something works.",
        ),
        QAItem(
            "What is teamwork?",
            "Teamwork is people sharing ideas and effort so they can solve a problem together.",
        ),
        QAItem(
            "What is a certificate?",
            "A certificate is a written award that recognizes an achievement or a special effort.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
traveler(luna).
helper(hoo).
curious(luna).
teamwork(hoo,luna).
sunburned(hoo).
certificate_awarded(luna,hoo) :- curious(luna), teamwork(hoo,luna).
quest_resolved(luna,hoo) :- certificate_awarded(luna,hoo).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("traveler", "luna"),
            asp.fact("helper", "hoo"),
            asp.fact("curious", "luna"),
            asp.fact("teamwork", "hoo", "luna"),
            asp.fact("sunburned", "hoo"),
        ]
    )


def asp_program(show: str = "#show quest_resolved/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    result = bool(asp.atoms(model, "quest_resolved"))
    if result:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) {' '.join(details)}"
        )
    facts = world.facts
    lines.append(
        f"  resolved={facts.get('resolved')} curiosity={facts.get('curiosity')} "
        f"teamwork={facts.get('teamwork')} flashback={facts.get('flashback')}"
    )
    return "\n".join(lines)


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


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams("meadow", "Luna", "girl", "Hoo", "boy", "curious"),
        StoryParams("meadow", "Mira", "girl", "Toby", "boy", "bright"),
        StoryParams("meadow", "Finn", "boy", "Pia", "girl", "patient"),
        StoryParams("meadow", "Nell", "girl", "Milo", "boy", "brave"),
    ]


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("This world needs a meadow, two different companions, and valid names.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in valid_story_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name} in the Sunlit Meadow"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
