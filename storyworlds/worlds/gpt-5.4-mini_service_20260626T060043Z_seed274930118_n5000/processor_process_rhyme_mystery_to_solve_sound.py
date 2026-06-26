#!/usr/bin/env python3
"""
storyworlds/worlds/processor_process_rhyme_mystery_to_solve_sound.py
=====================================================================

A small mythic story world about a village processor, a process that must be
performed, a rhyme that guides the work, a mystery to solve, and sound effects
that prove the world has changed.

Seed premise:
A village keeps a sacred Processor that can only begin its Process when the
right Rhyme is spoken. When a strange Mystery arrives in the sound of the
market bells, the keeper must listen to the Sound Effects, follow the Process,
and solve the Mystery before the village's song goes silent.
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
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    tone: str
    noise: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    line: str
    reply: str
    cadence: str
    unlocks: str


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    solved_by: str
    hidden: str


@dataclass
class SoundEffect:
    id: str
    sound: str
    source: str
    meaning: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "temple": Setting(
        place="the hill temple",
        tone="ancient",
        noise="a low bell hum",
        affords={"process", "listen", "solve"},
    ),
    "forge": Setting(
        place="the bronze forge",
        tone="bright",
        noise="a hot ring",
        affords={"process", "listen", "solve"},
    ),
    "harbor": Setting(
        place="the salt harbor",
        tone="windy",
        noise="a wave clap",
        affords={"process", "listen", "solve"},
    ),
}

RHYMES = {
    "first": Rhyme(
        id="first",
        line="If the bells hum low, let the bright words flow.",
        reply="Then the path will show.",
        cadence="soft and steady",
        unlocks="start",
    ),
    "second": Rhyme(
        id="second",
        line="If the mystery hides, follow what the sound provides.",
        reply="Then truth arrives.",
        cadence="slow and clear",
        unlocks="observe",
    ),
    "third": Rhyme(
        id="third",
        line="When the final note is near, let the answer stand here.",
        reply="Then the dark grows clear.",
        cadence="bright and brave",
        unlocks="resolve",
    ),
}

MYSTERIES = {
    "missing_bell": Mystery(
        id="missing_bell",
        clue="the temple bell was silent at dawn",
        cause="a vine had wrapped the clapper",
        solved_by="listening for the faint ring",
        hidden="the clapper was not broken",
    ),
    "split_drum": Mystery(
        id="split_drum",
        clue="the drum made a strange hollow thump",
        cause="a crack had opened under the skin",
        solved_by="tapping the rim and hearing the echo",
        hidden="the drum could still be mended",
    ),
    "lost_chime": Mystery(
        id="lost_chime",
        clue="the chime sounded thin and far away",
        cause="dust had clogged the little tube",
        solved_by="shaking it and hearing the rattle",
        hidden="the chime was only sleepy",
    ),
}

SOUNDS = {
    "bells": SoundEffect(id="bells", sound="ding-ding", source="bells", meaning="a call to begin"),
    "drums": SoundEffect(id="drums", sound="boom-boom", source="drums", meaning="a warning to listen"),
    "wind": SoundEffect(id="wind", sound="whoosh", source="wind", meaning="a sign that something moved"),
    "water": SoundEffect(id="water", sound="plip-plop", source="water", meaning="a clue hidden in motion"),
}

PROCESSORS = {
    "temple_processor": "a stone processor with a bowl of carved runes",
    "forge_processor": "a copper processor with a ring of hot gears",
    "harbor_processor": "a shell processor with a spiral drum",
}


@dataclass
class StoryParams:
    setting: str
    rhyme: str
    mystery: str
    sound: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about a processor, a process, a rhyme, a mystery, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--name")
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        lines.append(asp.fact("unlocks", rid, r.unlocks))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("solved_by", mid, m.solved_by))
    for sid, sfx in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,M,So) :- setting(S), rhyme(R), mystery(M), sound(So), affords(S,process), unlocks(R,start), solved_by(M,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RHYMES:
            for m in MYSTERIES:
                for so in SOUNDS:
                    combos.append((s, r, m, so))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rhyme is None or c[1] == args.rhyme)
              and (args.mystery is None or c[2] == args.mystery)
              and (args.sound is None or c[3] == args.sound)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    setting, rhyme, mystery, sound = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Ari", "Mira", "Tavi", "Niko", "Ilya"])
    return StoryParams(setting=setting, rhyme=rhyme, mystery=mystery, sound=sound, name=name)


def _intro(world: World, hero: Entity, proc: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} kept watch over {proc.label}, "
        f"the old processor of the village."
    )
    world.say(
        f"The place was {world.setting.tone}, and the air held {world.setting.noise}."
    )


def _present_mystery(world: World, mystery: Mystery, sound: SoundEffect) -> None:
    world.say(
        f"Then a mystery came: {mystery.clue}. "
        f"It arrived with {sound.sound}, and everyone turned their heads."
    )


def _process(world: World, hero: Entity, rhyme: Rhyme, mystery: Mystery, sound: SoundEffect) -> None:
    world.say(
        f"{hero.id} stood before the processor and spoke the rhyme: "
        f'"{rhyme.line}"'
    )
    world.say(f"The reply was answered in a low voice: \"{rhyme.reply}\"")
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(
        f"At once the process began, steady as a drumbeat, while {sound.sound} "
        f"kept time around the room."
    )
    world.say(
        f"{hero.id} listened for what the sound meant and solved the mystery: "
        f"{mystery.cause}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"The hidden truth was this: {mystery.hidden}. "
        f"By the end, the village heard {sound.sound} as a sound of peace."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    rhyme = RHYMES[params.rhyme]
    mystery = MYSTERIES[params.mystery]
    sound = SOUNDS[params.sound]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="keeper"))
    proc = world.add(Entity(
        id="processor",
        kind="thing",
        label="the Processor",
        phrase=PROCESSORS[f"{params.setting}_processor"],
        type="processor",
    ))
    world.facts.update(hero=hero, proc=proc, rhyme=rhyme, mystery=mystery, sound=sound, setting=setting)
    _intro(world, hero, proc)
    world.para()
    _present_mystery(world, mystery, sound)
    world.para()
    _process(world, hero, rhyme, mystery, sound)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a child about a processor that can begin only after a rhyme is spoken.',
        f"Tell a short myth where {f['hero'].id} must follow a process, listen to sound effects, and solve a mystery.",
        f"Write a gentle legend in which the word 'process' and the word 'processor' both matter, and the ending proves the mystery was solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rhyme = f["rhyme"]
    mystery = f["mystery"]
    sound = f["sound"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who kept watch over the Processor in {setting.place}?",
            answer=f"{hero.id} kept watch over the Processor in {setting.place} and guided the old village work.",
        ),
        QAItem(
            question=f"What rhyme helped begin the process?",
            answer=f"The rhyme was: \"{rhyme.line}\" It opened the way for the process to begin.",
        ),
        QAItem(
            question=f"What mystery had to be solved in the story?",
            answer=f"The mystery was that {mystery.clue}. {hero.id} solved it by following the sound and checking the clue.",
        ),
        QAItem(
            question=f"What sound effect helped prove the ending?",
            answer=f"The story used {sound.sound}, the sound effect from the {sound.source}, and it helped show the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a processor?",
            answer="A processor is something that takes in parts, follows a process, and helps turn them into an organized result.",
        ),
        QAItem(
            question="What is a process?",
            answer="A process is a set of steps that happen in order to do a job or make something happen.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects can help listeners imagine what is happening and notice clues in the world.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing or unknown that people try to understand by looking for clues.",
        ),
        QAItem(
            question="Why do rhymes feel special in myths?",
            answer="Rhymes feel special because their repeating sounds make them memorable, like an old chant or spell.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label!r} phrase={e.phrase!r} meters={e.meters} memes={e.memes}")
    lines.append(f"setting: {world.setting.place}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:\n")
        for s, r, m, so in combos:
            print(f"  {s:8} {r:8} {m:14} {so:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="temple", rhyme="first", mystery="missing_bell", sound="bells", name="Ari"),
            StoryParams(setting="forge", rhyme="second", mystery="split_drum", sound="drums", name="Mira"),
            StoryParams(setting="harbor", rhyme="third", mystery="lost_chime", sound="wind", name="Tavi"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
