#!/usr/bin/env python3
"""
Story world: petticoat, noise, bench, cautionary repetition, bad ending.

A small folk-tale style domain about a child who is told again and again to
mind the bench and the noise her petticoat makes, but keeps choosing the
same careless path until the ending turns sour.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "noise": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"warning": 0.0, "stubbornness": 0.0, "worry": 0.0, "shame": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Bench:
    label: str
    has_splinters: bool = False
    creaky: bool = False


@dataclass
class Petticoat:
    label: str
    phrase: str
    color: str
    delicate: bool = True


@dataclass
class StoryParams:
    setting: str
    name: str
    gender: str
    elder: str
    tone: str = "folk tale"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.repetition_count: int = 0
        self.bad_ending: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.repetition_count = self.repetition_count
        w.bad_ending = self.bad_ending
        return w


def pronoun_for_gender(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village_green": "the village green",
    "old_cottage": "the old cottage yard",
    "market_lane": "the market lane",
    "riverside": "the riverside walk",
}

BENCHES = {
    "oak_bench": Bench(label="the oak bench", has_splinters=True, creaky=True),
    "stone_bench": Bench(label="the stone bench", has_splinters=False, creaky=False),
    "garden_bench": Bench(label="the garden bench", has_splinters=False, creaky=True),
}

PETTICOATS = {
    "red_petticoat": Petticoat(label="petticoat", phrase="a bright red petticoat", color="red"),
    "white_petticoat": Petticoat(label="petticoat", phrase="a clean white petticoat", color="white"),
    "blue_petticoat": Petticoat(label="petticoat", phrase="a soft blue petticoat", color="blue"),
}

NAMES = {
    "girl": ["Mara", "Elsie", "Nell", "Tilly", "Ada", "Hattie"],
    "boy": ["Jon", "Tom", "Pip", "Owen", "Ben", "Will"],
}

ELDERS = ["grandmother", "mother", "aunt"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def setting_line(place: str) -> str:
    return {
        "village_green": "The village green was wide and quiet, with one bench beneath a linden tree.",
        "old_cottage": "Near the old cottage yard, a lonely bench stood by the gate and listened to every sound.",
        "market_lane": "In the market lane, carts rattled by and a bench waited beside the baker's wall.",
        "riverside": "By the riverside walk, a bench faced the water and heard every splash and whisper.",
    }[place]


def caution_line(elder: str, name: str) -> str:
    return f'"Mind the bench and mind the noise," said {elder}. "{name}, do not fidget and do not swing your feet."'


def repeat_line(name: str, count: int) -> str:
    if count == 1:
        return f"{name} nodded once, but the petticoat still whispered as {pronoun_for_gender('girl') if False else 'she'} shifted."
    if count == 2:
        return f"Again {name} was warned, and again the little petticoat brushed the boards."
    return f"Once more {name} tried to sit still, but once more the bench answered with a creak."


def build_world(params: StoryParams) -> World:
    world = World(params.setting)
    bench = world.add(Entity(id="bench", kind="object", type="bench", label=BENCHES[params.setting].label))
    child = world.add(Entity(id="child", kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder))
    pet = world.add(Entity(
        id="petticoat",
        kind="object",
        type="petticoat",
        label="petticoat",
        phrase=PETTICOATS["red_petticoat"].phrase,
        owner=child.id,
        worn_by=child.id,
    ))
    world.facts.update(
        child=child,
        elder=elder,
        bench=bench,
        petticoat=pet,
        place=params.setting,
        name=params.name,
        gender=params.gender,
    )
    return world


def warn(world: World, name: str, elder: Entity) -> None:
    elder.memes["warning"] += 1
    world.say(caution_line(elder.type, name))


def make_noise(world: World, child: Entity, bench: Entity, petticoat: Entity) -> None:
    key = ("noise", child.id, world.repetition_count)
    if key in world.fired:
        return
    world.fired.add(key)
    world.repetition_count += 1
    child.meters["noise"] += 1
    petticoat.meters["noise"] += 1
    if BENCHES[world.setting].creaky:
        bench.meters["noise"] += 1
    if BENCHES[world.setting].has_splinters:
        petticoat.meters["damage"] += 1
    world.say(
        f"The petticoat made a little swish-swish noise, and the bench gave a small creak in return."
    )


def repeat_caution(world: World, name: str, elder: Entity, child: Entity, bench: Entity, petticoat: Entity) -> None:
    warn(world, name, elder)
    world.para()
    world.say(f"{name} tried to sit more quietly, but the old habit came back.")
    make_noise(world, child, bench, petticoat)
    world.say(repeat_line(name, world.repetition_count))


def bad_ending(world: World, name: str, elder: Entity, child: Entity, bench: Entity, petticoat: Entity) -> None:
    world.bad_ending = True
    child.memes["shame"] += 1
    elder.memes["worry"] += 1
    petticoat.meters["damage"] += 2
    bench.meters["damage"] += 1
    world.say(
        f"At last the oak split a splinter into the petticoat's hem, and the bright cloth tore with a sharp little rip."
    )
    world.say(
        f"{name} stood up at once, but the song was gone from the afternoon, and {pronoun_for_gender(child.type)} had to go home with a torn hem and a red face."
    )


def narrate_story(world: World, params: StoryParams) -> None:
    child = world.get("child")
    elder = world.get("elder")
    bench = world.get("bench")
    petticoat = world.get("petticoat")

    world.say(
        f"Once in {SETTINGS[params.setting]}, there lived {params.name}, a {params.gender} child who loved to wear {petticoat.phrase}."
    )
    world.say(setting_line(params.setting))
    world.para()
    world.say(f"{params.name} found the bench and sat down with a little hop.")
    make_noise(world, child, bench, petticoat)
    world.say(f"{params.name} listened for a moment, but the petticoat kept whispering against the wood.")

    world.para()
    repeat_caution(world, params.name, elder, child, bench, petticoat)

    world.para()
    repeat_caution(world, params.name, elder, child, bench, petticoat)

    world.para()
    repeat_caution(world, params.name, elder, child, bench, petticoat)

    world.para()
    bad_ending(world, params.name, elder, child, bench, petticoat)

    world.facts.update(
        warning_count=3,
        noise_level=child.meters["noise"],
        damage=pet.meters["damage"],
        ended_bad=world.bad_ending,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a petticoat, a bench, and a warning about noise.',
        f"Tell a cautionary story where {f['name']} keeps being warned about the bench and the petticoat, but does not listen.",
        f'Write a repetitive little tale with the words "petticoat", "noise", and "bench", ending badly because of carelessness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    name = f["name"]
    elder = f["elder"].type
    qa = [
        QAItem(
            question=f"What was {name} wearing in the story?",
            answer=f"{name} was wearing a petticoat.",
        ),
        QAItem(
            question=f"What did {elder} warn {name} about?",
            answer=f"{elder.capitalize()} warned {name} to mind the bench and the noise.",
        ),
        QAItem(
            question=f"How many times was {name} warned before the ending?",
            answer="The warning was said three times, in the same careful way.",
        ),
        QAItem(
            question=f"What happened to the petticoat at the end?",
            answer="The petticoat caught a splinter and tore at the hem.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer="The ending was bad because the child kept ignoring the warning, so the bench damaged the petticoat and the child had to go home upset.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petticoat?",
            answer="A petticoat is a light under-skirt or slip worn beneath a dress or skirt.",
        ),
        QAItem(
            question="What is a bench for?",
            answer="A bench is a long seat where one or more people can sit down and rest.",
        ),
        QAItem(
            question="What is noise?",
            answer="Noise is a loud or rough sound that may be unpleasant or distracting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"repetition_count={world.repetition_count}")
    out.append(f"bad_ending={world.bad_ending}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    name: str
    gender: str
    elder: str
    tone: str = "folk tale"
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="village_green", name="Mara", gender="girl", elder="grandmother"),
    StoryParams(setting="old_cottage", name="Nell", gender="girl", elder="mother"),
    StoryParams(setting="market_lane", name="Pip", gender="boy", elder="aunt"),
    StoryParams(setting="riverside", name="Tilly", gender="girl", elder="grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: petticoat, noise, bench.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "mother", "aunt"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(ELDERS)
    if args.gender and args.name is None:
        pass
    return StoryParams(setting=setting, name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world, params)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(village_green; old_cottage; market_lane; riverside).

worn(P) :- petticoat(P).
at_risk(P) :- worn(P), delicate(P).

warning_needed(S) :- setting(S).
repeated_warning(S) :- warning_needed(S).

noise_event(S) :- setting(S), bench(S), petticoat(P), worn(P).
bad_ending(S) :- noise_event(S), repeated_warning(S).

#show warning_needed/1.
#show repeated_warning/1.
#show noise_event/1.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("bench", sid))
    for pid, p in PETTICOATS.items():
        lines.append(asp.fact("petticoat", pid))
        if p.delicate:
            lines.append(asp.fact("delicate", pid))
        lines.append(asp.fact("worn", pid))
    return "\n".join(lines)


def asp_program(show: str = "#show bad_ending/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    asp_bad = bool(asp.atoms(model, "bad_ending"))
    py_bad = True
    if asp_bad == py_bad:
        print("OK: ASP and Python both produce the cautionary bad ending.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def asp_compat() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show noise_event/1."))
    return [str(a) for a in asp.atoms(model, "noise_event")]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_compat()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n) * 40):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
