#!/usr/bin/env python3
"""
A standalone storyworld about a space supper, a silly transformation, and a
careful lesson about checking strange buttons before pressing them.
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
    name: str
    rooms: list[str]


@dataclass(frozen=True)
class Adventure:
    id: str
    place: str
    supper: str
    button: str
    mistake: str
    transformation: str
    danger: str
    clue: str
    friend_line: str
    repair: str
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "starship": Setting(
        name="the starship Comet Cricket",
        rooms=["the moonlit galley", "the observation deck", "the humming engine hall"],
    )
}

ADVENTURES = [
    Adventure(
        "comet_soup",
        "the moonlit galley",
        "comet-tail soup with floating noodles",
        "the silver button marked COSMIC CRUNCH",
        "pressed the button to make the soup sparkle before asking what it did",
        "a tiny purple comet with boots and a spoon for a tail",
        "the comet began zooming around the galley, slurping every noodle and bumping the soup cups",
        "a warning stripe under the button that said TEST WITH ONE CRUMB",
        '"That button changes supper into a traveler. Let us read first and press second."',
        "placed one noodle in the test bowl, switched the button to STEADY, and guided the little comet into a warm serving pot",
        "curiosity is bright, but careful questions keep bright ideas from causing a mess",
        "the little comet became a harmless swirl of steam above the supper table",
    ),
    Adventure(
        "moon_muffins",
        "the moonlit galley",
        "moon muffins filled with blueberry stars",
        "the gold button marked GROW",
        "pressed it because the smallest muffin looked lonely",
        "a giant muffin with a helmet and six buttery legs",
        "the muffin rolled through the galley, gathering crumbs and blocking the food hatch",
        "a tiny picture showed one crumb beside a measuring spoon",
        '"A giant change needs a tiny test. We can ask the recipe panel first."',
        "fed the machine one crumb, turned the dial to SMALL, and divided the giant muffin into sharing-sized moons",
        "kind intentions still need careful steps when a machine can make things much bigger",
        "six little muffins orbited the plates like a cheerful moon family",
    ),
    Adventure(
        "nebula_noodles",
        "the moonlit galley",
        "nebula noodles that glow green and blue",
        "the red button marked MIX ALL",
        "pressed it to make supper more colorful without checking the lid",
        "a wobbling noodle dragon with sauce-colored scales",
        "the dragon sneezed glowing sauce across the ceiling and chased the captain's hat",
        "the closed-lid symbol and a note reading ASK THE COOK",
        '"A recipe is a map, not a race. Let us close the lid and ask for help."',
        "scooped the dragon into a covered pot, followed the recipe, and served calm bowls",
        "a funny shortcut can become a real mess when we ignore a clear warning",
        "the noodle dragon curled into a harmless garnish beside the captain's spoon",
    ),
    Adventure(
        "asteroid_pie",
        "the moonlit galley",
        "asteroid pie with a crisp cracker crust",
        "the black button marked HARDEN",
        "pressed it to make the crust extra strong before supper",
        "a bouncing stone pie with a frosting crater",
        "the pie ricocheted between the walls and nearly knocked over the navigation globe",
        "a blinking sign that said SOFT SETTING FOR FOOD",
        '"The strongest setting is not always the safest setting for supper."',
        "caught the pie in a serving net, selected SOFT, and let it cool on a steady tray",
        "choosing the gentlest useful setting can protect both food and friends",
        "the pie rested quietly while its frosting crater shone like a tiny moon",
    ),
    Adventure(
        "starfruit_cake",
        "the moonlit galley",
        "starfruit cake dusted with sugar",
        "the blue button marked FLOAT",
        "pressed it so the cake would look like a planet",
        "a spinning cake planet with a jam river",
        "the cake drifted toward the open airlock and carried three napkins after it",
        "a tether icon beside the button and a hook labeled SECURE FIRST",
        '"A floating supper needs a tether. Space is too big for runaway cake."',
        "hooked a serving cord to the pan, lowered the power, and brought the cake back to the table",
        "before using a clever feature, secure what could drift away",
        "the cake floated gently above the table, tethered like a friendly little planet",
    ),
]

NAMES = {
    "girl": ["Luna", "Mira", "Pia", "Nova"],
    "boy": ["Orin", "Theo", "Jax", "Milo"],
}
TRAITS = ["curious", "cheerful", "brave", "inventive", "watchful"]


@dataclass
class StoryParams:
    place: str = "starship"
    activity: str = "supper"
    name: str = "Luna"
    gender: str = "girl"
    friend_name: str = "Orin"
    friend_gender: str = "boy"
    trait: str = "curious"
    seed: Optional[int] = None


def reasonable(params: StoryParams) -> bool:
    return (
        params.place in SETTINGS
        and params.activity == "supper"
        and params.gender in NAMES
        and params.friend_gender in NAMES
        and params.name != params.friend_name
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous space-supper storyworld about transformation and caution."
    )
    parser.add_argument("--place", choices=list(SETTINGS))
    parser.add_argument("--activity", choices=["supper"])
    parser.add_argument("--gender", choices=list(NAMES))
    parser.add_argument("--friend-gender", choices=list(NAMES), dest="friend_gender")
    parser.add_argument("--name")
    parser.add_argument("--friend-name", dest="friend_name")
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
    place = args.place or "starship"
    activity = args.activity or "supper"
    gender = args.gender or "girl"
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(NAMES[gender])
    friend_name = args.friend_name or rng.choice(NAMES[friend_gender])
    if name == friend_name:
        raise StoryError("The two space cooks must have different names.")
    return StoryParams(
        place=place,
        activity=activity,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
    )


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(params.name, "character", params.gender))
    friend = world.add(Entity(params.friend_name, "character", params.friend_gender))
    cooker = world.add(Entity("supper_machine", "thing", "machine", "the supper machine"))
    route = params.seed if params.seed is not None else sum(map(ord, params.name + params.friend_name))
    adventure = ADVENTURES[route % len(ADVENTURES)]

    world.say(
        f"On the starship Comet Cricket, {params.trait} {child.id} and {friend.id} "
        f"prepared {adventure.supper} in {adventure.place}."
    )
    world.say(
        f"The stars glittered beyond the window, and the supper machine hummed as if "
        f"it knew a very funny secret."
    )
    world.say(f"Beside the cooker sat {adventure.button}.")
    world.say(
        f"{child.id} wanted to make supper special, so {child.id} "
        f"{adventure.mistake}."
    )

    world.para()
    add_meter(child, "distance", 1.0)
    add_meter(cooker, "energy", 1.0)
    add_meme(child, "excitement", 1.0)
    add_meme(child, "confusion", 1.0)
    world.say(f"With a bright flash, the supper changed into {adventure.transformation}.")
    world.say(f"It was funny for exactly three seconds. Then {adventure.danger}.")
    world.say(f"{child.id} tried to catch it, but the faster {child.id} moved, the sillier the supper became.")

    world.para()
    add_meme(friend, "worry", 1.0)
    world.say(f"{friend.id} spotted {adventure.clue}.")
    world.say(f'{friend.id} said, {adventure.friend_line}')
    world.say(
        f"{child.id} stopped, took a slow breath, and admitted that pressing a mysterious "
        f"button before reading it had been a poor recipe for space supper."
    )
    add_meme(friend, "kindness", 1.0)
    add_meter(friend, "support", 1.0)
    add_meter(child, "attention", 1.0)

    world.para()
    world.say(f"Together, the friends {adventure.repair}.")
    add_meter(child, "care", 1.0)
    add_meter(friend, "care", 1.0)
    add_meme(child, "relief", 1.0)
    add_meme(child, "friendship", 1.0)
    add_meme(friend, "friendship", 1.0)
    world.say(
        f"The machine settled into a quiet purr, and {child.id} thanked {friend.id} "
        f"for giving a warning without giving a scolding."
    )
    world.say(f"They learned that {adventure.lesson}.")
    world.say(f"At last, {adventure.ending}.")
    world.say(
        f"Then the two space cooks sat down together, because even an adventurous supper "
        f"tastes best after everyone is safe."
    )

    world.facts.update(
        child=child,
        friend=friend,
        cooker=cooker,
        adventure=adventure,
        transformed=True,
        cautioned=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    adventure = world.facts["adventure"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        f"Write a humorous space adventure about {child.id} and {friend.id} preparing {adventure.supper}.",
        f"Include a transformation caused by {adventure.button}, a caution from {friend.id}, and a safe repair.",
        "End with a concrete supper image that proves the strange change has been resolved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    adventure = world.facts["adventure"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        QAItem(
            f"What did {child.id} press, and what happened to the supper?",
            f"{child.id} pressed {adventure.button}, and the supper transformed into {adventure.transformation}.",
        ),
        QAItem(
            f"What danger followed the transformation?",
            f"{adventure.danger.capitalize()}. The transformed supper became difficult to control in the starship galley.",
        ),
        QAItem(
            f"How did {friend.id} help?",
            f"{friend.id} noticed {adventure.clue} and said, {adventure.friend_line} The advice helped {child.id} stop and check the machine.",
        ),
        QAItem(
            "What did the friends do to repair the problem?",
            f"Together, the friends {adventure.repair}. This returned the supper to a safe state.",
        ),
        QAItem(
            "What lesson did the space cooks learn?",
            f"They learned that {adventure.lesson}.",
        ),
        QAItem(
            "What final image showed that everything was safe?",
            f"At the end, {adventure.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should someone read a machine's warning before pressing a button?",
            "A warning explains what the button may do, so reading it can prevent a surprising or dangerous mistake.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a change in form, shape, or condition, such as food becoming a moving creature.",
        ),
        QAItem(
            "Why is a caution not the same as a scolding?",
            "A caution gives useful information to help someone act safely, while a scolding mainly expresses blame.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("This world requires a starship supper and two different characters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:16} ({entity.type:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
character(C) :- child(C).
character(F) :- friend(F).
transformed :- used_button, supper.
cautioned :- friend(F), gives_warning(F).
repaired :- transformed, cautioned, safe_action.
resolved :- repaired.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("supper"),
            asp.fact("child", "child"),
            asp.fact("friend", "friend"),
            asp.fact("used_button"),
            asp.fact("gives_warning", "friend"),
            asp.fact("safe_action"),
        ]
    )


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    ok = bool(asp.atoms(model, "resolved"))
    if ok:
        print("OK: ASP and Python resolution agree.")
        return 0
    print("MISMATCH between ASP and Python resolution.")
    return 1


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(name="Luna", gender="girl", friend_name="Orin", friend_gender="boy", trait="curious"),
        StoryParams(name="Milo", gender="boy", friend_name="Nova", friend_gender="girl", trait="cheerful"),
        StoryParams(name="Pia", gender="girl", friend_name="Jax", friend_gender="boy", trait="inventive"),
        StoryParams(name="Theo", gender="boy", friend_name="Mira", friend_gender="girl", trait="watchful"),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        import asp

        model = asp.one_model(asp_program())
        print("resolved:", bool(asp.atoms(model, "resolved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in valid_story_params()]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 30):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {sample.params.name} and {sample.params.friend_name} aboard the Comet Cricket"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
