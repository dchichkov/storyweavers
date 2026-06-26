#!/usr/bin/env python3
"""
storyworlds/worlds/funeral_sound_effects_comedy.py
===================================================

A small story world about a funeral, a sound-effects toy, and a gentle comedy
turn: somebody wants to press the funny button at the wrong time, but the adults
find a better moment so the tribute stays warm instead of disruptive.

Seed premise:
---
A child arrives at a funeral with a sound-effects box. The child loves silly
noises, but the family wants the ceremony to stay respectful. The child starts
to press the buttons anyway. A grown-up notices the problem, then suggests a
planned goodbye where one tiny sound effect becomes a happy memory instead of a
messy interruption.

World model:
---
- physical meters: sound, startedle, spill, rumple, tidiness
- emotional memes: sorrow, grin, relief, mischief, respect, love, worry

The story is comedy, but it stays gentle: the joke is in timing, not cruelty.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    label: str
    verb: str
    sound_word: str
    risk: str
    tone: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tribute:
    label: str
    phrase: str
    type: str
    value: str
    sound: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class World:
    setting: Setting

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.sound_level: float = 0.0
        self.true_scene: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.sound_level = self.sound_level
        clone.true_scene = self.true_scene
        return clone


SETTINGS = {
    "chapel": Setting("the small chapel", indoors=True, affords={"button", "hush", "tribute"}),
    "living_room": Setting("the living room", indoors=True, affords={"button", "tribute"}),
    "garden": Setting("the garden", indoors=False, affords={"button", "tribute", "wind"}),
}

SOUNDS = {
    "drumroll": SoundEffect(
        id="drumroll", label="a drumroll button", verb="press the drumroll button",
        sound_word="rum-rum-rum", risk="made the room bounce", tone="comic",
        fix="save it for the memory slide", keyword="drumroll", tags={"funny", "music"},
    ),
    "kazoo": SoundEffect(
        id="kazoo", label="a kazoo button", verb="press the kazoo button",
        sound_word="wheee-honk", risk="made people snort with laughter", tone="silly",
        fix="use it at the goodbye story", keyword="kazoo", tags={"funny", "music"},
    ),
    "squeak": SoundEffect(
        id="squeak", label="a squeak button", verb="press the squeak button",
        sound_word="eeek", risk="startled the quiet faces", tone="tiny",
        fix="tap it only once at the end", keyword="squeak", tags={"tiny", "noise"},
    ),
    "thunder": SoundEffect(
        id="thunder", label="a thunder button", verb="press the thunder button",
        sound_word="BOOM", risk="shook the flowers", tone="big",
        fix="save it for the stormy story", keyword="thunder", tags={"big", "noise"},
    ),
}

TRIBUTES = {
    "photo": Tribute("photo", "a framed photo of the one they loved", "photo", "memory", "flash"),
    "flowers": Tribute("flowers", "a small bouquet of bright flowers", "flowers", "petals", "soft chime"),
    "hat": Tribute("hat", "a favorite funny hat on a pillow", "hat", "memory", "honk"),
    "program": Tribute("program", "a little paper program", "program", "order", "rustle"),
}

NAMES = ["Milo", "Pia", "Ben", "Nora", "Ada", "Leo", "June", "Finn"]
RELATIVES = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    sound: str
    tribute: str
    name: str
    relative: str
    seed: Optional[int] = None


def reasonableness_gate(setting: Setting, sound: SoundEffect, tribute: Tribute) -> bool:
    return bool(setting.affords) and sound.id in SOUNDS and tribute.label in TRIBUTES


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for s in SOUNDS:
            for t in TRIBUTES:
                out.append((place, s, t))
    return out


def make_sound(world: World, hero: Entity, sound: SoundEffect, narrate: bool = True) -> None:
    world.sound_level += 1
    hero.memes["mischief"] += 1
    if narrate:
        world.say(f"{hero.id} reached for {sound.label} and wanted to make the room go {sound.sound_word}.")


def predict_scene(world: World, hero: Entity, sound: SoundEffect, tribute: Entity) -> dict:
    sim = world.copy()
    make_sound(sim, sim.get(hero.id), sound, narrate=False)
    sim.facts["sound_level"] = sim.sound_level
    return {
        "too_loud": sim.sound_level >= THRESHOLD,
        "worry": sim.get(hero.id).memes.get("mischief", 0.0) >= THRESHOLD,
    }


def tell(setting: Setting, sound: SoundEffect, tribute_cfg: Tribute, name: str, relative: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="boy" if relative in {"uncle", "father"} else "girl"))
    grownup = world.add(Entity(id="Grownup", kind="character", type=relative, label=f"the {relative}"))
    tribute = world.add(Entity(
        id="tribute", type=tribute_cfg.type, label=tribute_cfg.label, phrase=tribute_cfg.phrase,
        owner=grownup.id, caretaker=grownup.id, plural=False,
    ))

    hero.memes.update({"mischief": 0.0, "love": 1.0, "worry": 0.0})
    grownup.memes.update({"sorrow": 1.0, "love": 1.0, "worry": 0.5, "respect": 1.0})

    world.say(
        f"{hero.id} came to {setting.place} holding {hero.pronoun('possessive')} {sound.label}. "
        f"It was a day for saying goodbye, so everybody tried to keep their voices soft."
    )
    world.say(
        f"The {relative} stood by {tribute_cfg.phrase}, and the whole room felt quiet and careful."
    )

    world.para()
    world.say(
        f"{hero.id} loved little noises and kept looking at {sound.label} like it was a toy built for a joke."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {sound.verb}, but that could {sound.risk}."
    )

    pred = predict_scene(world, hero, sound, tribute)
    if pred["too_loud"]:
        world.say(
            f'"That is not a now-button," {grownup.pronoun("subject").capitalize()} said. '
            f'"This is a quiet-goodbye moment."'
        )
        hero.memes["worry"] += 1
        grownup.memes["worry"] += 0.5

    world.para()
    hero.memes["mischief"] += 1
    world.say(
        f"{hero.id} made a tiny face and almost pressed it anyway, but then {grownup.pronoun('subject')} leaned close."
    )
    world.say(
        f'"How about we keep {sound.keyword} for the ending?" {grownup.pronoun("subject").capitalize()} said. '
        f'"We can use it when we tell the funniest memory."'
    )

    world.say(
        f"{hero.id} paused. That idea felt better than sneaking a noisy surprise into the middle of the room."
    )
    hero.memes["mischief"] = 0.0
    hero.memes["respect"] = 1.0
    hero.memes["love"] += 1.0
    grownup.memes["relief"] = 1.0

    world.say(
        f"At the end, {hero.id} pressed {sound.label} once, right on purpose, and the room answered with "
        f"{sound.sound_word}. It sounded funny, but it also sounded like a little salute."
    )
    world.say(
        f"People smiled through their tears. The goodbye stayed gentle, and the {tribute.label} still looked neat and loved."
    )

    world.facts.update(
        hero=hero,
        grownup=grownup,
        tribute=tribute,
        sound=sound,
        setting=setting,
        resolved=True,
        predicted_too_loud=pred["too_loud"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    sound = f["sound"]
    tribute = f["tribute"]
    return [
        f'Write a gentle comedy story for a young child about a funeral and a {sound.keyword} button.',
        f"Tell a short story where {hero.id} wants to {sound.verb} at {world.setting.place}, but {grownup.label} worries about the funeral.",
        f"Write a story about keeping a funeral respectful until the right moment for one silly sound effect.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    sound = f["sound"]
    tribute = f["tribute"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Where did {hero.id} go with {sound.label}?",
            answer=f"{hero.id} went to {place} for a funeral, holding {sound.label} and trying to stay quiet at first.",
        ),
        QAItem(
            question=f"Why did {grownup.label} worry when {hero.id} wanted to {sound.verb}?",
            answer=(
                f"{grownup.label} worried because the funeral was supposed to be a quiet goodbye, "
                f"and {sound.risk}. The grown-up wanted the {tribute.label} and the room to stay calm."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, {hero.id} used {sound.label} on purpose at the very end, so the sound became a funny tribute "
                f"instead of a disruption. The funeral stayed respectful and also became a warm memory."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sound = f["sound"]
    out = [
        QAItem(
            question="What is a funeral?",
            answer="A funeral is a gathering where people say goodbye to someone who died and remember them with care.",
        ),
        QAItem(
            question="Why can a sound effect be funny?",
            answer="A sound effect can be funny because it surprises people in a playful way, like a silly honk or a tiny squeak.",
        ),
    ]
    if sound.id == "kazoo":
        out.append(QAItem(
            question="What does a kazoo sound like?",
            answer="A kazoo makes a buzzy, silly sound that can turn a simple tune into a joke.",
        ))
    if sound.id == "thunder":
        out.append(QAItem(
            question="What does thunder sound like?",
            answer="Thunder sounds loud and booming, like the sky is rolling a giant drum.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  sound_level={world.sound_level}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="chapel", sound="squeak", tribute="flowers", name="Milo", relative="aunt"),
    StoryParams(place="living_room", sound="kazoo", tribute="photo", name="Pia", relative="uncle"),
    StoryParams(place="garden", sound="drumroll", tribute="hat", name="Ben", relative="father"),
]


@dataclass
class ASPFacts:
    pass


ASP_RULES = r"""
place(P) :- setting(P).
sound(S) :- sound_effect(S).
tribute(T) :- tribute_item(T).

compatible(P,S,T) :- setting(P), sound_effect(S), tribute_item(T).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for s in SOUNDS:
        lines.append(asp.fact("sound_effect", s))
    for t in TRIBUTES:
        lines.append(asp.fact("tribute_item", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: funeral sound effects comedy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--tribute", choices=TRIBUTES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--relative", choices=RELATIVES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sound is None or c[1] == args.sound)
              and (args.tribute is None or c[2] == args.tribute)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, tribute = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    relative = args.relative or rng.choice(RELATIVES)
    return StoryParams(place=place, sound=sound, tribute=tribute, name=name, relative=relative)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SOUNDS[params.sound], TRIBUTES[params.tribute], params.name, params.relative)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sound, tribute) combos:\n")
        for p, s, t in combos:
            print(f"  {p:12} {s:10} {t:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.sound} at {p.place} (tribute: {p.tribute})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
