#!/usr/bin/env python3
"""
A tiny ghost-story world about putty, a holder, and a surprise that becomes
friendly when two children investigate together.
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    visible: bool = True
    held_by: Optional[str] = None


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Scene:
    name: str
    opening: str
    sound: str
    clue: str
    reveal: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


SCENES = [
    Scene(
        "attic_window",
        "Moonlight lay across the attic floor where old toys waited under a sheet.",
        "From the window shelf came three soft taps.",
        "A dusty line of putty led from the shelf to a little wooden holder.",
        "The holder tipped forward and showed a tiny ghost wearing a button as a hat.",
        "The ghost waved from the holder, and the taps became a gentle good-night song.",
    ),
    Scene(
        "hallway_clock",
        "The hallway clock had stopped just before midnight, and the house seemed to hold its breath.",
        "A pale shape drifted beside the clock and whispered, \"Not yet.\"",
        "A blob of putty stuck to the clock case pointed toward a brass holder beneath it.",
        "Inside the holder was a lost silver key, and the ghost had been trying to return it.",
        "When the key was placed by the door, the hallway clock began ticking warmly again.",
    ),
    Scene(
        "rainy_playroom",
        "Rain tapped the playroom windows while a night-light made long shadows on the rug.",
        "A toy holder slid across the floor without anyone touching it.",
        "Fresh putty marks curved around its base like tiny footprints.",
        "A friendly ghost rose from the holder and revealed a drawing hidden beneath the putty.",
        "The drawing showed the house in sunlight, and the ghost faded into its brightest corner.",
    ),
    Scene(
        "library_stairs",
        "The library stairs creaked although everyone in the house was downstairs.",
        "A whisper floated up: \"Please look in the holder.\"",
        "A neat lump of putty kept a loose step from wobbling.",
        "Under the step rested a photograph, and the surprised ghost pointed to its smiling family.",
        "The children placed the photograph in a frame, and the stairs stopped creaking.",
    ),
]

NAMES = ["Luna", "Milo", "Nia", "Theo", "Pip"]
FRIENDS = ["Mara", "Owen", "Tess", "Juno", "Kai"]
TOOLS = ["small flashlight", "blue candle", "round mirror"]
MOODS = ["curious", "brave", "careful", "sleepy"]


@dataclass
class StoryParams:
    name: str
    friend_name: str
    mood: str
    tool: str
    scene: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Putty Holder Surprise Ghost Story")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("--scene", choices=[s.name for s in SCENES])
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in FRIENDS if n != name])
    return StoryParams(
        name=name,
        friend_name=friend,
        mood=args.mood or rng.choice(MOODS),
        tool=args.tool or rng.choice(TOOLS),
        scene=args.scene or rng.choice([s.name for s in SCENES]),
    )


def _scene(params: StoryParams) -> Scene:
    for scene in SCENES:
        if scene.name == params.scene:
            return scene
    raise StoryError(f"Unknown ghost-story scene: {params.scene}")


def tell(params: StoryParams) -> World:
    scene = _scene(params)
    world = World(Setting(place="the old house", affords={"surprise", "investigation", "friendship"}))
    hero = world.add(Entity(
        params.name,
        "character",
        "child",
        params.name,
        meters={"courage": 0.0, "attention": 0.0},
        memes={"worry": 0.0, "curiosity": 1.0},
    ))
    friend = world.add(Entity(
        params.friend_name,
        "character",
        "child",
        params.friend_name,
        meters={"helpfulness": 0.0},
        memes={"calm": 1.0},
    ))
    putty = world.add(Entity(
        "putty",
        "thing",
        "putty",
        "a soft lump of putty",
        meters={"stickiness": 1.0},
    ))
    holder = world.add(Entity(
        "holder",
        "thing",
        "holder",
        "a small wooden holder",
        meters={"stability": 0.0},
    ))
    ghost = world.add(Entity(
        "ghost",
        "character",
        "ghost",
        "a pale little ghost",
        meters={"visibility": 0.0},
        memes={"loneliness": 1.0},
        visible=False,
    ))
    world.facts.update(
        hero=hero,
        friend=friend,
        putty=putty,
        holder=holder,
        ghost=ghost,
        scene=scene,
        params=params,
    )

    hero.memes["worry"] = 1.0
    world.say(f"{scene.opening} {params.name}, a {params.mood} child, was visiting with {params.friend_name}.")
    world.say(f"They carried a {params.tool}, but they did not yet know what the old house was hiding.")
    world.para()
    world.say(scene.sound)
    world.say(f'"Did you hear that?" {params.name} whispered.')
    world.say(f'"I did," said {params.friend_name}. "Let us look together."')
    world.say(f"They found {putty.label} pressed against {holder.label}. {scene.clue}")
    hero.meters["attention"] = 1.0
    friend.meters["helpfulness"] = 1.0
    world.say(
        f"{params.friend_name} held the {params.tool} steady while {params.name} touched the putty. "
        "It was warm, although the room was cold."
    )
    world.say(f'"Something is inside," said {params.name}.')
    world.say(f'"Then we will ask before we open it," {params.friend_name} replied.')
    world.para()
    ghost.visible = True
    ghost.meters["visibility"] = 1.0
    ghost.memes["loneliness"] = 0.0
    holder.meters["stability"] = 1.0
    hero.meters["courage"] = 1.0
    hero.memes["worry"] = 0.0
    world.fired.add("surprise_revealed")
    world.say(scene.reveal)
    world.say(
        f"The surprise was not a frightening monster. It was a lonely ghost who had used the putty "
        f"to keep the holder from falling."
    )
    world.say(f'"Were you making the tapping sound?" asked {params.name}.')
    world.say(f'"Only because I wanted a friend," said the ghost.')
    world.say(
        f"{params.friend_name} smiled and placed the holder where everyone could see it. "
        f"{params.name} promised to visit again."
    )
    world.para()
    world.say(scene.ending)
    world.say(
        f"After that night, every small sound in the old house brought a question before it brought fear, "
        f"and the ghost was never lonely for long."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f"Write a gentle Ghost Story about {params.name}, {params.friend_name}, putty, and a holder.",
        f"Tell a surprise story in which putty gives {params.name} a clue in {scene.name.replace('_', ' ')}.",
        f"Write a child-facing ghost story where curiosity and friendship change a scary sound.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scene: Scene = world.facts["scene"]
    return [
        QAItem(
            f"Where did {params.name} and {params.friend_name} hear the strange sound?",
            scene.opening,
        ),
        QAItem(
            "What clue did the putty provide?",
            scene.clue,
        ),
        QAItem(
            "What did the holder contain or reveal?",
            scene.reveal,
        ),
        QAItem(
            f"How did {params.friend_name} help {params.name}?",
            f"{params.friend_name} held the {params.tool} steady and investigated together instead of letting {params.name} face the surprise alone.",
        ),
        QAItem(
            "What was the surprise?",
            "The surprise was a lonely little ghost, not a frightening monster.",
        ),
        QAItem(
            "How did the ending prove that the ghost was safe?",
            scene.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is putty?",
            "Putty is a soft, moldable material that can stick to surfaces and hold small things in place.",
        ),
        QAItem(
            "What is a holder?",
            "A holder is an object made to support or keep another object safely in one place.",
        ),
        QAItem(
            "What is a ghost story?",
            "A ghost story is a tale about a ghost or mysterious spirit, often filled with suspense and a surprising discovery.",
        ),
        QAItem(
            "What does surprise mean?",
            "A surprise is something unexpected that someone discovers suddenly.",
        ),
        QAItem(
            "Why can investigating with a friend help?",
            "Investigating with a friend can make a mystery feel safer because two people can share clues, ideas, and courage.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        visibility = "visible" if entity.visible else "hidden"
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) {visibility} meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return (
        params.name in NAMES
        and params.friend_name in FRIENDS
        and params.name != params.friend_name
        and params.mood in MOODS
        and params.tool in TOOLS
        and params.scene in {scene.name for scene in SCENES}
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The names, mood, tool, and scene must fit the small ghost-story world.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
valid_story(N,F,M,T,S) :-
    name(N), friend(F), mood(M), tool(T), scene(S),
    different(N,F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for friend in FRIENDS:
        lines.append(asp.fact("friend", friend))
    for mood in MOODS:
        lines.append(asp.fact("mood", mood))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    for scene in SCENES:
        lines.append(asp.fact("scene", scene.name))
    for name in NAMES:
        for friend in FRIENDS:
            if name != friend:
                lines.append(asp.fact("different", name, friend))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {
        (name, friend, mood, tool, scene.name)
        for name in NAMES
        for friend in FRIENDS
        for mood in MOODS
        for tool in TOOLS
        for scene in SCENES
        if name != friend
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combinations).")
        return 0
    print("MISMATCH between clingo and python")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams("Luna", "Mara", "curious", "small flashlight", "attic_window", 0),
    StoryParams("Milo", "Owen", "brave", "blue candle", "hallway_clock", 1),
    StoryParams("Nia", "Tess", "careful", "round mirror", "rainy_playroom", 2),
    StoryParams("Theo", "Juno", "sleepy", "small flashlight", "library_stairs", 3),
]


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    index = 0
    while len(samples) < args.n and index < max(50, args.n * 50):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        combinations = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combinations)} valid story combinations.")
        for combination in combinations[:20]:
            print(combination)
        return

    samples = [generate(params) for params in CURATED] if args.all else build_story_from_args(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
