#!/usr/bin/env python3
"""
storyworlds/worlds/madame_melody_confuse_surprise_foreshadowing_fairy_tale.py
===============================================================================

A small fairy-tale storyworld about a child, a missing melody, a puzzled heart,
and a surprise that was quietly foreshadowed all along.

The seed words are preserved as world content:
- madame
- melody
- confuse

Story premise:
- In a castle garden, a young singer cannot find the right melody.
- Madame, a kindly teacher, notices the confusion and gives small clues.
- Tiny foreshadowing details appear early: a humming teacup, a silver ribbon,
  a lantern that glows when songs are near.
- The ending reveals a surprise: the missing melody was already hidden in a
  gift prepared for the child.

This script follows the Storyweavers contract:
- self-contained stdlib script
- shared results imported eagerly
- ASP imported lazily
- StoryParams, registries, parser, resolver, generate, emit, main defined
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "madame"}
        male = {"boy", "man", "father", "sir"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    mood: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Melody:
    id: str
    name: str
    source: str
    sign: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Foreshadow:
    id: str
    image: str
    clue: str
    predicts: str


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    delight: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.melody: Optional[Melody] = None
        self.foreshadow: Optional[Foreshadow] = None
        self.surprise: Optional[Surprise] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.melody = copy.deepcopy(self.melody)
        clone.foreshadow = copy.deepcopy(self.foreshadow)
        clone.surprise = copy.deepcopy(self.surprise)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "castle_garden": Setting(
        place="the castle garden",
        indoor=False,
        mood="golden",
        affords={"listen", "sing", "search"},
    ),
    "music_room": Setting(
        place="the music room",
        indoor=True,
        mood="soft",
        affords={"listen", "sing", "search"},
    ),
    "lantern_hall": Setting(
        place="the lantern hall",
        indoor=True,
        mood="glowing",
        affords={"listen", "sing", "search"},
    ),
}

MELODIES = {
    "lullaby": Melody(
        id="lullaby",
        name="a lullaby",
        source="a silver music box",
        sign="a tune like a gentle cradle",
        reveal="soft and sweet",
        tags={"music", "soft"},
    ),
    "waltz": Melody(
        id="waltz",
        name="a waltz",
        source="a painted fan",
        sign="a tune with little turning steps",
        reveal="bright and spinning",
        tags={"music", "dance"},
    ),
    "hymn": Melody(
        id="hymn",
        name="a hymn",
        source="an old bell",
        sign="a tune that sounded brave and clear",
        reveal="clear and shining",
        tags={"music", "bright"},
    ),
}

FORESHADOWS = {
    "humming_cup": Foreshadow(
        id="humming_cup",
        image="a teacup that hummed very softly",
        clue="it carried a tiny note as it trembled",
        predicts="a melody hiding nearby",
    ),
    "silver_ribbon": Foreshadow(
        id="silver_ribbon",
        image="a silver ribbon tied to a chair",
        clue="it pointed toward a secret drawer",
        predicts="a gift waiting to be found",
    ),
    "glow_lantern": Foreshadow(
        id="glow_lantern",
        image="a lantern that glowed whenever music was near",
        clue="it brightened when the child sang",
        predicts="the song would be found by singing",
    ),
}

SURPRISES = {
    "music_box": Surprise(
        id="music_box",
        label="a tiny music box",
        reveal="the missing melody was tucked inside a velvet box",
        delight="its lid opened with a sparkling chime",
        tags={"music", "gift"},
    ),
    "bell_charm": Surprise(
        id="bell_charm",
        label="a bell charm",
        reveal="the melody was hidden inside a bell-shaped charm on a ribbon",
        delight="it rang in a single bright note",
        tags={"music", "gift"},
    ),
    "bird_whistle": Surprise(
        id="bird_whistle",
        label="a wooden bird whistle",
        reveal="the melody had been waiting in a little bird whistle all along",
        delight="its tune fluttered out like a bird taking wing",
        tags={"music", "gift"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Anya", "Clara", "Nora", "Elise", "Tilda"]
BOY_NAMES = ["Pip", "Oren", "Milo", "Theo", "Bram", "Eli"]
TRAITS = ["curious", "gentle", "brave", "wistful", "bright"]


# ---------------------------------------------------------------------------
# Core world helpers
# ---------------------------------------------------------------------------

def foreshadow_text(world: World) -> str:
    f = world.foreshadow
    if not f:
        return ""
    return f"The story had already shown {f.image}, and {f.clue}."


def melody_presence(world: World) -> str:
    m = world.melody
    return m.source if m else "something musical"


def predict_confusion(world: World, hero: Entity) -> bool:
    sim = world.copy()
    return hero.memes.get("confuse", 0.0) >= 1.0 and sim.melody is not None


def sing_search(world: World, hero: Entity) -> None:
    hero.meters["voice"] = hero.meters.get("voice", 0.0) + 1.0
    hero.memes["confuse"] = hero.memes.get("confuse", 0.0) + 1.0
    world.say(
        f"{hero.id} tried to sing the missing tune, but the notes slipped away "
        f"like minnows in a stream."
    )
    world.say(
        f"{hero.id} felt confuse and looked around the {world.setting.place.split('the ')[-1]}."
    )


def gentle_warning(world: World, madame: Entity, hero: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1.0
    world.say(
        f"{madame.label.capitalize()} smiled kindly and said, "
        f'"Listen for the smallest sign first. Some songs hide in plain sight."'
    )


def clue_sequence(world: World, hero: Entity) -> None:
    if world.foreshadow:
        world.say(
            f"Near the bench, {world.foreshadow.image} waited. "
            f"It seemed odd at first, but {world.foreshadow.clue}."
        )
    if world.setting.indoor:
        world.say(
            f"The lantern light trembled, as if it knew a secret about the tune."
        )
    else:
        world.say(
            f"The roses leaned toward the path, as if they had heard the tune before."
        )


def resolve_surprise(world: World, hero: Entity, madame: Entity) -> None:
    s = world.surprise
    m = world.melody
    if not s or not m:
        return
    hero.memes["confuse"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2.0
    world.say(
        f"Then Madame {madame.label} opened a little box with a ribbon and said, "
        f'"I kept one last gift for you."'
    )
    world.say(
        f"{s.delight}. Inside was {s.reveal}, and it was {m.reveal}."
    )
    world.say(
        f"{hero.id} laughed, because the tune had been there all along."
    )


def ending_image(world: World, hero: Entity) -> None:
    m = world.melody
    s = world.surprise
    if m and s:
        world.say(
            f"By the end, {hero.id} was singing again, and {s.label} sat open in the "
            f"sunlight while the castle garden listened."
        )


# ---------------------------------------------------------------------------
# Narrative screenplay
# ---------------------------------------------------------------------------

def tell(setting: Setting, melody: Melody, foreshadow: Foreshadow, surprise: Surprise,
         hero_name: str, hero_type: str, hero_trait: str) -> World:
    world = World(setting)
    world.melody = melody
    world.foreshadow = foreshadow
    world.surprise = surprise

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        memes={"confuse": 0.0, "joy": 0.0, "wonder": 0.0},
        meters={"voice": 0.0},
        tags={"child", "music"},
    ))
    madame = world.add(Entity(
        id="Madame",
        kind="character",
        type="madame",
        label="Madame Melody",
        tags={"teacher", "music"},
        memes={"calm": 1.0, "kindness": 1.0},
    ))
    secret = world.add(Entity(
        id="secret",
        type="thing",
        label=surprise.label,
        phrase=surprise.label,
        owner=madame.id,
        tags=surprise.tags,
    ))

    world.facts.update(
        hero=hero,
        madame=madame,
        secret=secret,
        setting=setting,
        melody=melody,
        foreshadow=foreshadow,
        surprise=surprise,
        hero_trait=hero_trait,
    )

    # Act 1: a fairy-tale setup with a missing tune and a clue.
    world.say(
        f"Once in {setting.place}, there lived a {hero_trait} child named {hero.id} "
        f"who loved songs."
    )
    world.say(
        f"{hero.id} was trying to find {melody.name}, but the tune kept hiding "
        f"behind the flower pots and stone steps."
    )
    world.say(
        f"Madame Melody watched with a gentle smile, and {foreshadow_text(world)}"
    )

    # Act 2: confusion grows, then a clue turns the search.
    world.para()
    sing_search(world, hero)
    gentle_warning(world, madame, hero)
    clue_sequence(world, hero)

    # Act 3: the surprise reveal resolves the confusion.
    world.para()
    resolve_surprise(world, hero, madame)
    ending_image(world, hero)
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    m = f["melody"]
    s = f["surprise"]
    return [
        f'Write a short fairy-tale story for a child named {hero.id} who feels confuse while looking for {m.name}.',
        f"Tell a gentle story with Madame Melody, a hidden tune, and a surprise revealed at the end.",
        f'Write a fairy tale that uses the words "madame", "melody", and "confuse", and includes a foreshadowing clue.',
        f"Make the ending feel magical when {s.label} finally reveals the missing song.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    madame = f["madame"]
    melody = f["melody"]
    foreshadow = f["foreshadow"]
    surprise = f["surprise"]

    return [
        QAItem(
            question=f"Who was looking for the missing melody in the story?",
            answer=f"{hero.id} was looking for {melody.name} in the castle garden.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel confuse at the beginning?",
            answer=(
                f"{hero.id} felt confuse because the melody kept seeming to hide, "
                f"and the child could not find where the tune had gone."
            ),
        ),
        QAItem(
            question=f"What did Madame Melody say to help {hero.id} search?",
            answer=(
                f"Madame Melody said to listen for the smallest sign first, because "
                f"some songs hide in plain sight."
            ),
        ),
        QAItem(
            question=f"What clue was foreshadowed before the surprise ending?",
            answer=(
                f"The story foreshadowed {foreshadow.image}. That clue hinted that "
                f"{foreshadow.predicts}."
            ),
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=(
                f"The surprise was {surprise.label}. It revealed that {surprise.reveal}."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"{hero.id} stopped feeling confuse, laughed, and sang again while the "
                f"castle garden listened."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    m = f["melody"]
    s = f["surprise"]
    out = [
        QAItem(
            question="What is a melody?",
            answer="A melody is a tune made by notes that go together in a pattern.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer=(
                "Foreshadowing gives a small clue early so the ending feels surprising "
                "but also makes sense."
            ),
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer=(
                "A surprise is something that the reader does not expect right away, "
                "but that feels exciting when it appears."
            ),
        ),
        QAItem(
            question="Why do people like music boxes?",
            answer=(
                "People like music boxes because they can play a little tune when "
                "they are opened or wound up."
            ),
        ),
    ]
    if "gift" in s.tags or "music" in s.tags:
        out.append(
            QAItem(
                question="What can a music box do?",
                answer="A music box can hide a tune inside and play it when opened.",
            )
        )
    if "music" in m.tags:
        out.append(
            QAItem(
                question="What is special about a tune?",
                answer="A tune can be remembered and recognized even after the notes are gone.",
            )
        )
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the child is confused, Madame offers a clue,
% and the surprise is compatible with the foreshadowing theme.
valid_story(S, M, F, U) :- setting(S), melody(M), foreshadow(F), surprise(U).

% The foreshadowing is meaningful if the clue mentions a hidden or waiting thing.
foreshadows(F) :- foreshadow(F), clue(F, _).

% The ending is reasonable if the surprise reveals the melody.
surprise_resolves(U, M) :- surprise(U), melody(M), reveal(U, M).

% A complete fairy-tale arc requires setup, confusion, clue, and resolution.
complete_story(S, M, F, U) :- valid_story(S, M, F, U),
                              foreshadows(F),
                              surprise_resolves(U, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MELODIES.items():
        lines.append(asp.fact("melody", mid))
        lines.append(asp.fact("source", mid, m.source))
        lines.append(asp.fact("reveal", mid, m.reveal))
    for fid, f in FORESHADOWS.items():
        lines.append(asp.fact("foreshadow", fid))
        lines.append(asp.fact("image", fid, f.image))
        lines.append(asp.fact("clue", fid, f.clue))
    for uid, u in SURPRISES.items():
        lines.append(asp.fact("surprise", uid))
        lines.append(asp.fact("label", uid, u.label))
        lines.append(asp.fact("reveal", uid, u.reveal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show complete_story/4."))
    asp_set = set(asp.atoms(model, "complete_story"))
    py_set = set(
        (s, m, f, u)
        for s in SETTINGS
        for m in MELODIES
        for f in FORESHADOWS
        for u in SURPRISES
    )
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry cross-product ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    melody: str
    foreshadow: str
    surprise: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: madame, melody, confuse, surprise, and foreshadowing.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--melody", choices=sorted(MELODIES))
    ap.add_argument("--foreshadow", choices=sorted(FORESHADOWS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    melody = args.melody or rng.choice(sorted(MELODIES))
    foreshadow = args.foreshadow or rng.choice(sorted(FORESHADOWS))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, melody=melody, foreshadow=foreshadow, surprise=surprise,
                       name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MELODIES[params.melody],
        FORESHADOWS[params.foreshadow],
        SURPRISES[params.surprise],
        params.name,
        params.gender,
        params.trait,
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  melody: {world.melody.id if world.melody else 'none'}")
    lines.append(f"  foreshadow: {world.foreshadow.id if world.foreshadow else 'none'}")
    lines.append(f"  surprise: {world.surprise.id if world.surprise else 'none'}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle_garden", "lullaby", "humming_cup", "music_box", "Mina", "girl", "curious"),
    StoryParams("music_room", "waltz", "silver_ribbon", "bell_charm", "Pip", "boy", "gentle"),
    StoryParams("lantern_hall", "hymn", "glow_lantern", "bird_whistle", "Clara", "girl", "brave"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show complete_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.melody} / {p.foreshadow} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
