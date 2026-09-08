#!/usr/bin/env python3
"""
Story world: Scruff the brave wood-carrying animal.

A small animal story about Scruff, a shaggy creature who uses bravery and
humor to help friends repair a little woodland bridge.
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
class Character:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"path": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"bravery": 0.0, "humor": 0.0, "worry": 0.0})


@dataclass
class Object:
    name: str
    kind: str
    material: str = "wood"
    meters: dict[str, float] = field(default_factory=lambda: {"length": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"usefulness": 0.0})


@dataclass
class World:
    setting: str
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.name] = obj
        return obj


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Scruff"
    helper_name: str = "Pip"
    setting: str = "woodland creek"


@dataclass(frozen=True)
class Adventure:
    name: str
    danger: str
    comic_moment: str
    brave_action: str
    cause: str
    repair: str
    ending: str
    lesson: str


ADVENTURES = [
    Adventure(
        name="the windy crossing",
        danger="a strong wind tore away one plank from the little bridge",
        comic_moment="Scruff's fur puffed up until he looked like a walking haystack",
        brave_action="stepped onto the wobbling bank and held a branch steady while Pip tied the rope",
        cause="rain had loosened the old peg beneath the missing plank",
        repair="carried a stout piece of wood from the fallen willow and fitted it across the gap",
        ending="the bridge gave a friendly creak as the animals crossed together",
        lesson="bravery can mean helping carefully while everyone works as a team",
    ),
    Adventure(
        name="the noisy night",
        danger="a dark hollow log rolled against the bridge and blocked the path home",
        comic_moment="Scruff told the log, 'Please stop pretending to be a potato'",
        brave_action="walked close enough to place his shoulder against the log while Pip pushed from behind",
        cause="the creek bank had become slippery after a long rain",
        repair="used two short pieces of wood as levers and rolled the log safely aside",
        ending="moonlight shone on a clear path and the log rested like a harmless brown hill",
        lesson="a joke can make a frightening job feel possible, but careful teamwork does the work",
    ),
    Adventure(
        name="the sleepy squirrel",
        danger="a baby squirrel was stranded on a tiny island when the creek rose",
        comic_moment="Scruff crossed his eyes and announced, 'I am now a very serious rescue boat'",
        brave_action="waded into the shallow edge and carried a long branch so the squirrel could climb toward shore",
        cause="a pile of wood had made the water divide around the island",
        repair="moved the loose wood one piece at a time until the creek flowed freely again",
        ending="the squirrel curled its tail around Scruff's scruff while the water sang past",
        lesson="bravery is strongest when it protects someone smaller",
    ),
    Adventure(
        name="the crooked cart",
        danger="the animals' cart of firewood tipped beside the steep trail",
        comic_moment="Scruff sat in the cart and declared, 'I meant to invent a furry wheel'",
        brave_action="stood on the downhill side and braced the cart while the others unloaded it",
        cause="one wooden wheel had cracked along a hidden knot",
        repair="found a smooth branch, carved a round peg, and helped fit it into the wheel",
        ending="the cart rolled home with its wood stacked low and safe",
        lesson="a brave helper admits a problem before it becomes a bigger one",
    ),
]


NAMES = ["Scruff", "Moss", "Bramble", "Fuzz", "Clover"]
HELPERS = ["Pip", "Nell", "Tumble", "Fern", "Wren"]


def build_world(params: StoryParams) -> World:
    if params.setting != "woodland creek":
        raise StoryError("This story domain only supports the woodland creek setting.")
    world = World(setting=params.setting)
    hero = world.add_character(Character(params.hero_name, "shaggy woodland animal", "hero"))
    helper = world.add_character(Character(params.helper_name, "small woodland animal", "helper"))
    bridge = world.add_object(Object("little bridge", "bridge", "wood"))
    branch = world.add_object(Object("fallen branch", "repair piece", "wood"))
    world.facts.update(hero=hero, helper=helper, bridge=bridge, branch=branch)
    return world


def narrate_story(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xA71C9)
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    bridge: Object = world.facts["bridge"]
    branch: Object = world.facts["branch"]
    adventure = rng.choice(ADVENTURES)
    opening = rng.choice([
        "Early one bright morning",
        "After a night of soft rain",
        "When the forest birds began their first song",
        "On a golden afternoon",
    ])
    hero_line, helper_line = rng.choice([
        (
            f'"I can help!" {hero.name} said, though his knees wobbled.',
            f'"Then we will help together," {helper.name} replied.',
        ),
        (
            f'"That looks enormous," {hero.name} whispered. "Fortunately, I am enormous too."',
            f'"You are mostly scruff," {helper.name} said, "but scruff can be useful."',
        ),
        (
            f'"I am scared," {hero.name} admitted. "I will take one careful step."',
            f'"One careful step is a splendid beginning," said {helper.name}.',
        ),
    ])

    world.facts.update(adventure=adventure, opening=opening)
    world.say(f"{opening}, {hero.name} and {helper.name} followed the creek through the woods.")
    world.say(
        f"{hero.name} was covered in soft scruff, and he liked to make his friends laugh "
        "when a serious job made their paws tremble."
    )
    world.say(f"Then they reached the {bridge.name}. {adventure.danger}.")
    world.say(f"{hero.name} tried to look brave, but {adventure.comic_moment}.")

    world.para()
    hero.memes["worry"] += 1.0
    world.say(hero_line)
    world.say(helper_line)
    world.say(f"Together they looked at the creek, the bridge, and the scattered wood.")
    world.say(f"They did not rush. {helper.name} checked the bank while {hero.name} watched the safest place to stand.")
    world.say(f"At last they learned that {adventure.cause}.")
    world.say(f"{hero.name} took a slow breath. His bravery grew when he remembered that he was not alone.")

    world.para()
    hero.memes["bravery"] += 1.0
    hero.memes["humor"] += 1.0
    branch.meters["length"] = 2.0
    branch.memes["usefulness"] = 1.0
    world.say(f"With a brave heart, {hero.name} {adventure.brave_action}.")
    world.say(f"Then {hero.name} {adventure.repair}.")
    bridge.memes["usefulness"] = 1.0
    world.say(f"The {bridge.name} held firm, and the creek slipped underneath it without a splash.")

    world.para()
    world.say(f"{helper.name} laughed. 'Your joke helped, but your careful paws helped even more.'")
    world.say(f"{hero.name} smiled. 'My paws are very serious. My scruff is in charge of the jokes.'")
    world.say(f"They crossed the repaired bridge together. {adventure.ending}.")
    world.say(f"{hero.name} learned that {adventure.lesson}.")


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    return [
        f"Write an animal story about {hero.name}, a scruffy woodland helper.",
        "Include wood, a small danger, bravery, humor, a brief dialogue exchange, and a repaired ending.",
        "Show the animal's courage through a careful helpful action rather than a boast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    adventure: Adventure = world.facts["adventure"]
    return [
        QAItem(
            question=f"Who is {hero.name}?",
            answer=f"{hero.name} is a shaggy woodland animal whose scruff and brave actions help the other animals.",
        ),
        QAItem(
            question="What problem did the animals face?",
            answer=f"They faced a problem because {adventure.danger}.",
        ),
        QAItem(
            question=f"How did {hero.name} show bravery?",
            answer=f"{hero.name} showed bravery when he {adventure.brave_action}.",
        ),
        QAItem(
            question="How did humor help in the story?",
            answer=f"Humor helped because {adventure.comic_moment}, making a frightening job feel less frightening while the animals worked carefully.",
        ),
        QAItem(
            question=f"What did {hero.name} learn?",
            answer=f"{hero.name} learned that {adventure.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wood?",
            answer="Wood is a strong natural material that comes from trees and can be used for branches, tools, carts, and bridges.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing a needed or kind thing even when you feel worried, while still thinking carefully about safety.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is a playful way of making someone laugh or helping a difficult moment feel lighter.",
        ),
        QAItem(
            question="Why can friends make a hard job easier?",
            answer="Friends can share ideas, watch for danger, and give one another courage while they solve the problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
wood_used :- branch_ready, repaired.
brave(H) :- hero(H), careful_step(H), helper_present.
humorous(H) :- hero(H), joke_told(H).
safe_crossing :- brave(H), wood_used, repaired, bridge_present.
lesson(bravery_and_teamwork) :- safe_crossing.

#show brave/1.
#show humorous/1.
#show wood_used/0.
#show safe_crossing/0.
#show lesson/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "scruff"),
        asp.fact("helper_name", "pip"),
        asp.fact("branch_ready"),
        asp.fact("repaired"),
        asp.fact("careful_step", "scruff"),
        asp.fact("helper_present"),
        asp.fact("joke_told", "scruff"),
        asp.fact("bridge_present"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(
        "#show brave/1.\n#show humorous/1.\n#show wood_used/0.\n#show safe_crossing/0.\n#show lesson/1."
    ))
    found = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("brave", ("scruff",)),
        ("humorous", ("scruff",)),
        ("wood_used", ()),
        ("safe_crossing", ()),
        ("lesson", ("bravery_and_teamwork",)),
    }
    if found != expected:
        print("MISMATCH between ASP and Python story facts.")
        print("ASP atoms:", sorted(found))
        print("Expected:", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=17))
    if not sample.story or "Scruff" not in sample.story or "wood" not in sample.story:
        print("Generated story exercise failed.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous animal story about Scruff, wood, and bravery.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name}: species={character.species} memes={dict(character.memes)}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.name}: kind={obj.kind} material={obj.material} "
            f"meters={dict(obj.meters)} memes={dict(obj.memes)}"
        )
    return "\n".join(lines)


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
        print(asp_program(
            "#show brave/1.\n#show humorous/1.\n#show wood_used/0.\n#show safe_crossing/0.\n#show lesson/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show brave/1.\n#show humorous/1.\n#show wood_used/0.\n#show safe_crossing/0.\n#show lesson/1."
        ))
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams(seed=base_seed, hero_name="Scruff", helper_name="Pip"),
            StoryParams(seed=base_seed + 1, hero_name="Moss", helper_name="Nell"),
            StoryParams(seed=base_seed + 2, hero_name="Bramble", helper_name="Wren"),
            StoryParams(seed=base_seed + 3, hero_name="Fuzz", helper_name="Tumble"),
        ]
        samples = [generate(params) for params in presets]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

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
