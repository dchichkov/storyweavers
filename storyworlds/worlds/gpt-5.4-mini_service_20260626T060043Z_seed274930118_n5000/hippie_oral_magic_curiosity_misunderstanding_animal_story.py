#!/usr/bin/env python3
"""
A small standalone storyworld for an Animal Story about a hippie, oral magic,
curiosity, and misunderstanding.

Premise:
A gentle animal child hears a funny magical rumor about an oral spell. The child
gets curious, tries to repeat the spell, and a misunderstanding makes a friend
worry. A calm helper explains the magic, and the animals end with a kinder,
clearer way to share the enchantment.

The simulation tracks physical meters and emotional memes:
- meters: physical state such as carrying, noise, glow, or distance
- memes: emotional state such as curiosity, misunderstanding, worry, delight

The domain is intentionally small and constraint-checked:
- the story only exists when the chosen magic is the kind that can actually
  trigger the misunderstanding
- invalid combinations raise StoryError
- the ASP twin mirrors the Python reasonableness gate
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    spell: str
    chant: str
    glow: str
    effect: str
    can_misunderstand: bool = True
    keyword: str = ""


@dataclass
class StoryParams:
    place: str
    magic: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "meadow": Setting(place="the sunny meadow", affords={"oral"}),
    "garden": Setting(place="the flower garden", affords={"oral"}),
    "riverbank": Setting(place="the riverbank path", affords={"oral"}),
    "camp": Setting(place="the little camp circle", affords={"oral"}),
}

MAGICS = {
    "oral": Magic(
        id="oral",
        spell="say the glowing word aloud",
        chant="a soft round chant",
        glow="golden",
        effect="the word hopped from mouth to mouth like a tiny warm song",
        can_misunderstand=True,
        keyword="oral",
    ),
    "whisper": Magic(
        id="whisper",
        spell="whisper the secret word",
        chant="a hush of moonlight",
        glow="silver",
        effect="the word floated on the breeze like a feather",
        can_misunderstand=False,
        keyword="whisper",
    ),
}

NAMES = {
    "animal": ["Milo", "Pip", "Nina", "Tala", "Juno", "Bram", "Luna"],
    "helper": ["Moss", "Fern", "Otto", "Wren"],
}

TRAITS = ["curious", "gentle", "merry", "spirited", "brave"]


def reasonableness_gate(place: str, magic: str) -> bool:
    return place in SETTINGS and magic in MAGICS and magic in SETTINGS[place].affords


def explain_rejection(place: str, magic: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not part of this small animal world.)"
    if magic not in MAGICS:
        return "(No story: that kind of magic is not available here.)"
    return "(No story: this place does not support that kind of magical speaking.)"


def story_prompt(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    magic = f["magic"]
    return [
        f'Write a short Animal Story for a young child about {hero.id} and the word "{magic.keyword}".',
        f"Tell a gentle story where an animal named {hero.id} gets curious about a magical word and a misunderstanding is fixed kindly.",
        f"Write a simple story with magic speech, curiosity, and a misunderstanding in {world.setting.place}.",
    ]


def apply_magic(world: World, hero: Entity, magic: Magic) -> None:
    hero.meters["glow"] = hero.meters.get("glow", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.id} listened to the {magic.chant} and felt {magic.glow} light gather near {hero.pronoun('possessive')} nose."
    )
    world.say(
        f"{hero.id} wanted to try it too, because {magic.effect}."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, magic: Magic) -> None:
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1.0
    friend.memes["misunderstanding"] = friend.memes.get("misunderstanding", 0.0) + 1.0
    world.say(
        f"When {hero.id} said the magical word aloud, {friend.id} startled and blinked."
    )
    world.say(
        f"{friend.id} thought {hero.id} was naming the {magic.keyword} as if it were a secret trouble."
    )


def helper_explains(world: World, helper: Entity, hero: Entity, friend: Entity, magic: Magic) -> None:
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1.0
    friend.memes["worry"] = max(0.0, friend.memes.get("worry", 0.0) - 1.0)
    friend.memes["misunderstanding"] = 0.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"Then {helper.id} smiled and explained that the word was only magic, not a hurtful warning."
    )
    world.say(
        f"{helper.id} showed them how the spell worked: {magic.spell}, and the glow only made the air sparkle."
    )


def ending(world: World, hero: Entity, friend: Entity, helper: Entity) -> None:
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1.0
    friend.memes["delight"] = friend.memes.get("delight", 0.0) + 1.0
    world.say(
        f"{hero.id} and {friend.id} laughed, and {hero.id} repeated the word more slowly so it sounded friendly."
    )
    world.say(
        f"By the end, the little group sat together in {world.setting.place}, and the magic felt warm instead of confusing."
    )


def tell(setting: Setting, magic: Magic, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["little", "soft-hearted"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["older", "wise"]))

    hero.memes["curiosity"] = 1.0

    world.say(
        f"In {setting.place}, {hero.id} was a little {hero_type} with a {random.choice(TRAITS)} heart."
    )
    world.say(
        f"{hero.id} loved magical sounds, especially the {magic.keyword} word that seemed to tickle the air."
    )
    world.say(
        f"{friend.id} stayed nearby, while {helper.id} listened from the edge of the path with a kind smile."
    )

    world.para()
    apply_magic(world, hero, magic)
    misunderstanding(world, hero, friend, magic)
    world.para()
    helper_explains(world, helper, hero, friend, magic)
    ending(world, hero, friend, helper)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        magic=magic,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return story_prompt(world)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    helper: Entity = f["helper"]
    magic: Magic = f["magic"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Where did {hero.id} hear the magical word?",
            answer=f"{hero.id} heard it in {place}, where the air felt calm and sparkly.",
        ),
        QAItem(
            question=f"Why did {friend.id} get worried when {hero.id} said the word aloud?",
            answer=f"{friend.id} thought the word was a warning or secret trouble, so there was a misunderstanding.",
        ),
        QAItem(
            question=f"How did {helper.id} fix the misunderstanding?",
            answer=f"{helper.id} explained that the word was only magic and showed how {magic.spell} made harmless sparkle.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the worry was gone, the animals understood each other, and the magic felt friendly.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "oral": [
        QAItem(
            question="What does oral mean?",
            answer="Oral means spoken with the mouth, like a word, a song, or a story told aloud.",
        ),
        QAItem(
            question="Why can spoken words be magical in stories?",
            answer="In stories, spoken words can be magical because saying them can start a spell or change what happens next.",
        ),
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn, look, and ask questions about something new.",
        ),
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what another person meant.",
        ),
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful or impossible in real life that can happen in a story, like a glowing word or a talking star.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["magic"].keyword, "magic", "curiosity", "misunderstanding"}
    out: list[QAItem] = []
    for tag in ["oral", "curiosity", "misunderstanding", "magic"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    magic = args.magic or "oral"
    if not reasonableness_gate(place, magic):
        raise StoryError(explain_rejection(place, magic))
    hero_type = args.hero_type or rng.choice(["rabbit", "fox", "deer", "mouse", "badger"])
    friend_type = args.friend_type or rng.choice(["rabbit", "fox", "deer", "mouse", "hedgehog"])
    helper_type = args.helper_type or rng.choice(["owl", "turtle", "goat", "heron"])
    hero = args.hero or rng.choice(NAMES["animal"])
    friend = args.friend or rng.choice([n for n in NAMES["animal"] if n != hero])
    helper = args.helper or rng.choice(NAMES["helper"])
    return StoryParams(
        place=place,
        magic=magic,
        hero=hero,
        hero_type=hero_type,
        friend=friend,
        friend_type=friend_type,
        helper=helper,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MAGICS[params.magic],
        params.hero,
        params.hero_type,
        params.friend,
        params.friend_type,
        params.helper,
        params.helper_type,
    )
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
% A story is reasonable when the place affords the magic type.
valid_story(Place, Magic) :- place(Place), magic_kind(Magic), affords(Place, Magic).

% Oral magic is the only kind that can create the misunderstanding beat.
can_misunderstand(Magic) :- magic_kind(Magic), magic_is_oral(Magic).

% A valid story here needs both the place and the misunderstanding-capable magic.
compatible(Place, Magic) :- valid_story(Place, Magic), can_misunderstand(Magic).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for m in sorted(setting.affords):
            lines.append(asp.fact("affords", place, m))
    for magic_id, magic in MAGICS.items():
        lines.append(asp.fact("magic_kind", magic_id))
        if magic_id == "oral":
            lines.append(asp.fact("magic_is_oral", magic_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = {(place, magic) for place in SETTINGS for magic in MAGICS if reasonableness_gate(place, magic) and magic == "oral"}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", sorted(python_set))
    print("clingo:", sorted(clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: hippie oral magic, curiosity, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type")
    ap.add_argument("--friend")
    ap.add_argument("--friend-type")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(place="meadow", magic="oral", hero="Milo", hero_type="rabbit", friend="Pip", friend_type="mouse", helper="Moss", helper_type="owl"),
    StoryParams(place="garden", magic="oral", hero="Nina", hero_type="fox", friend="Luna", friend_type="deer", helper="Fern", helper_type="turtle"),
    StoryParams(place="riverbank", magic="oral", hero="Tala", hero_type="badger", friend="Juno", friend_type="rabbit", helper="Otto", helper_type="heron"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid_combos()
        print(f"{len(model)} compatible combos:")
        for item in model:
            print(item)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
