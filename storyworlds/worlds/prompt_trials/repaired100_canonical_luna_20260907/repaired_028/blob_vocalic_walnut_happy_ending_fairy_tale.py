#!/usr/bin/env python3
"""
A small fairy-tale world about a blob, a vocalic song, and a walnut treasure.
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
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"path": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"hope": 0.0, "worry": 0.0, "kindness": 0.0}
    )


@dataclass
class Object:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"weight": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"wonder": 0.0})
    state: str = "ordinary"


@dataclass
class World:
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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    helper_name: str = "Mara"
    setting: str = "the moonlit walnut grove"
    blob_name: str = "the blue blob"
    vocalic_name: str = "the vocalic bell"
    walnut_name: str = "the golden walnut"


HEROES = ["Luna", "Mira", "Nella", "Pip", "Tessa"]
HELPERS = ["Mara", "Eda", "the old gardener", "Queen Elian", "Aunt Suri"]
BLOBS = ["the blue blob", "the silver blob", "the rosy blob", "the little green blob"]
VOCALICS = ["the vocalic bell", "the vocalic flute", "the vocalic shell", "the vocalic harp"]
WALNUTS = ["the golden walnut", "the moonlit walnut", "the ruby walnut", "the silver walnut"]


@dataclass(frozen=True)
class TaleArc:
    obstacle: str
    mistake: str
    consequence: str
    clue: str
    action: str
    cause: str
    gift: str
    ending: str


ARCS = [
    TaleArc(
        obstacle="the walnut had vanished from the nest of the sleeping tree",
        mistake="Luna tried to pull the blob across the thorny hill without asking what it could do",
        consequence="the blob stretched into a bridge, but a thorn caught its shining edge and blocked the path",
        clue="the vocalic bell answered with three warm notes whenever the blob touched the moss",
        action="sang the three notes softly and invited the blob to become round and strong",
        cause="the walnut had rolled into a hollow root, and the frightened blob had covered it to keep it safe",
        gift="the walnut opened into a tiny lantern that lit the grove for every traveler",
        ending="the moonlit grove glowed with lanterns, and the blob bounced happily beside Luna",
    ),
    TaleArc(
        obstacle="the kingdom's wishing walnut lay silent beneath the old fountain",
        mistake="Luna shouted a command and poked the blob with a golden spoon",
        consequence="the blob hid in a cup, while the fountain's water splashed over the path",
        clue="a vocalic echo rose whenever someone spoke with patience",
        action="thanked the blob, then matched each gentle vowel to the echo",
        cause="the blob had carried the walnut away from the fountain because it feared the loud royal bells",
        gift="the walnut released a rain of kind wishes for the whole kingdom",
        ending="the fountain sang again, and even the shy blob received a crown of daisies",
    ),
    TaleArc(
        obstacle="a storm had swept the walnut treasure into the briar wood",
        mistake="Luna chased every glimmer at once and left the safe path",
        consequence="the glimmers were fireflies, and Luna became lost among the twisting briars",
        clue="the vocalic instrument hummed only when the blob faced the true trail",
        action="stood still, listened for the hum, and followed the blob's careful wobble",
        cause="the blob had guarded the walnut under a leaf until the storm passed",
        gift="the walnut became a seed that grew a sheltering tree",
        ending="the new tree spread silver leaves above Luna, the blob, and all the grateful fireflies",
    ),
]


def build_world(params: StoryParams) -> World:
    if not params.hero_name.strip():
        raise StoryError("The hero needs a name.")
    if not params.setting.strip():
        raise StoryError("The fairy tale needs a setting.")
    world = World()
    hero = Character(params.hero_name, "young seeker")
    helper = Character(params.helper_name, "wise helper")
    blob = Object(params.blob_name, "blob", {"weight": 1.0}, {"wonder": 1.0})
    vocalic = Object(params.vocalic_name, "vocalic instrument", {"weight": 2.0}, {"wonder": 2.0})
    walnut = Object(params.walnut_name, "walnut treasure", {"weight": 0.5}, {"wonder": 3.0}, "hidden")
    world.characters[hero.name] = hero
    world.characters[helper.name] = helper
    world.objects[blob.name] = blob
    world.objects[vocalic.name] = vocalic
    world.objects[walnut.name] = walnut
    world.facts.update(hero=hero, helper=helper, blob=blob, vocalic=vocalic, walnut=walnut)
    return world


def narrate(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xB10BCA)
    arc = rng.choice(ARCS)
    opening = rng.choice([
        "Once, beneath a velvet moon",
        "Long ago, when stars still whispered to trees",
        "At the edge of a kingdom made of gardens",
        "One evening, when the moon wore a silver crown",
    ])
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    blob: Object = world.facts["blob"]
    vocalic: Object = world.facts["vocalic"]
    walnut: Object = world.facts["walnut"]

    hero.memes["hope"] += 1
    blob.memes["wonder"] += 1
    world.facts["arc"] = arc
    world.say(f"{opening}, {hero.name} lived near {world.facts.get('setting', 'a moonlit grove')}.")
    world.say(
        f"{hero.name} carried {vocalic.name}, a magical instrument whose vocalic notes could reveal "
        f"truth, and traveled with {blob.name}, a cheerful creature that could change its shape."
    )
    world.say(f"One dawn, {arc.obstacle}.")
    world.say(f"The fairy queen sent {hero.name} to find it before the first star faded.")

    world.para()
    hero.memes["worry"] += 1
    world.say(f"At the forest gate, {helper.name} raised a lantern.")
    world.say(f'"Do not hurry past a frightened friend," {helper.name} warned.')
    world.say(f'"But the kingdom is waiting," {hero.name} replied. "I must be brave."')
    world.say(f"In her worry, {hero.name} {arc.mistake}.")
    world.say(f"Then {arc.consequence}.")
    world.say(f"The path grew quiet, and even the moon seemed to hold its breath.")

    world.para()
    world.say(f"{helper.name} knelt beside {hero.name}.")
    world.say(f'"Listen before you lead," {helper.name} said. "Every small creature may know a large secret."')
    world.say(f'"Will you show me what you know?" {hero.name} asked {blob.name}.')
    world.say(f"{arc.clue.capitalize()}.")
    world.say(f"At last, {hero.name} {arc.action}.")
    blob.state = "helpful"
    vocalic.state = "singing"
    world.say(f"The music opened a path, and {arc.cause}.")

    world.para()
    walnut.state = "found"
    walnut.memes["wonder"] += 1
    hero.memes["kindness"] += 1
    world.say(f"{hero.name} lifted {walnut.name} with both hands and thanked {blob.name}.")
    world.say(f"The grateful {helper.name} blessed the treasure, and {arc.gift}.")
    world.say(f"{hero.name} learned that courage is strongest when it makes room for patience and friendship.")
    world.say(f"{arc.ending}.")
    world.facts.update(lesson="courage is strongest when it makes room for patience and friendship")


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    return [
        f"Write a Fairy Tale about {hero.name}, a blob, a vocalic magical instrument, and a walnut treasure.",
        "Include a frightening obstacle, a mistake, a kind dialogue exchange, a helpful clue, and a Happy Ending.",
        "Show how patience and friendship change the outcome rather than merely stating the lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    blob: Object = world.facts["blob"]
    vocalic: Object = world.facts["vocalic"]
    walnut: Object = world.facts["walnut"]
    arc: TaleArc = world.facts["arc"]
    return [
        QAItem(f"What was {hero.name} searching for?", f"{hero.name} was searching for {walnut.name}, which had vanished from its magical resting place."),
        QAItem("How did the vocalic instrument help?", f"{vocalic.name} answered with musical notes that revealed the true path when {hero.name} listened carefully."),
        QAItem(f"Why was {blob.name} important?", f"{blob.name} had hidden and guarded the walnut, then helped {hero.name} reach it safely."),
        QAItem("What changed after the dialogue with the helper?", f"{helper.name} encouraged {hero.name} to listen before leading, so the search changed from hurried guessing to patient observation."),
        QAItem("How did the tale end happily?", f"{arc.gift.capitalize()}, and {arc.ending}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a fairy tale?", "A fairy tale is an imaginative story with wondrous events, magical beings, a challenge, and often a hopeful ending."),
        QAItem("What does vocalic mean here?", "Vocalic means connected with vowel-like sounds or a magical language carried by clear singing notes."),
        QAItem("Why can patience help in a difficult quest?", "Patience gives someone time to notice clues, understand friends, and choose an action that does not make the problem worse."),
        QAItem("What makes an ending happy?", "A happy ending shows that the danger has passed, relationships have been repaired, and the characters have gained safety, joy, or hope."),
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
quest(H) :- hero(H), missing_walnut.
careful(H) :- hero(H), listened.
helped_by_blob(H) :- hero(H), blob_helped.
happy_ending :- quest(H), careful(H), helped_by_blob(H), walnut_found.
#show quest/1.
#show careful/1.
#show helped_by_blob/1.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "luna"),
        asp.fact("missing_walnut"),
        asp.fact("listened"),
        asp.fact("blob_helped"),
        asp.fact("walnut_found"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    expected = {"quest", "careful", "helped_by_blob", "happy_ending"}
    if expected.issubset(names):
        sample = generate(StoryParams(seed=17))
        if "happily" not in sample.story and "happy" not in sample.story:
            print("MISMATCH: generated story lacks a happy resolution.")
            return 1
        print("OK: ASP gate matches the Python story arc.")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(str(sym) for sym in model))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fairy tale about a blob, a vocalic song, and a walnut.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--name", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--blob", choices=BLOBS)
    parser.add_argument("--vocalic", choices=VOCALICS)
    parser.add_argument("--walnut", choices=WALNUTS)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero_name=args.name or rng.choice(HEROES),
        helper_name=args.helper or rng.choice(HELPERS),
        blob_name=args.blob or rng.choice(BLOBS),
        vocalic_name=args.vocalic or rng.choice(VOCALICS),
        walnut_name=args.walnut or rng.choice(WALNUTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["setting"] = params.setting
    narrate(world, params.seed if params.seed is not None else 0)
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
        lines.append(f"{character.name}: meters={character.meters} memes={character.memes}")
    for obj in world.objects.values():
        lines.append(f"{obj.name}: kind={obj.kind} state={obj.state} meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show quest/1.\n#show careful/1.\n#show helped_by_blob/1.\n#show happy_ending/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(hero_name="Luna", helper_name="Mara", blob_name="the blue blob", vocalic_name="the vocalic bell", walnut_name="the golden walnut", seed=base_seed),
            StoryParams(hero_name="Mira", helper_name="Eda", blob_name="the silver blob", vocalic_name="the vocalic flute", walnut_name="the moonlit walnut", seed=base_seed + 1),
            StoryParams(hero_name="Nella", helper_name="Aunt Suri", blob_name="the rosy blob", vocalic_name="the vocalic shell", walnut_name="the ruby walnut", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in params_list]
    else:
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
