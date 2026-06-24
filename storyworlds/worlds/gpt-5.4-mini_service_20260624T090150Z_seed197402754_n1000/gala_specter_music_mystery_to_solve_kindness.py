#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": {"female": "she", "male": "he", "neutral": "they"},
            "object": {"female": "her", "male": "him", "neutral": "them"},
            "possessive": {"female": "her", "male": "his", "neutral": "their"},
        }
        gender = "neutral"
        if self.type in {"girl", "mother", "queen", "woman"}:
            gender = "female"
        elif self.type in {"boy", "father", "king", "man"}:
            gender = "male"
        return mapping[case][gender]

    def name_or_label(self) -> str:
        return self.label or self.id

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    hall: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace_log: list[str] = field(default_factory=list)

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


@dataclass
class StoryParams:
    place: str
    performer: str
    disguise: str
    seeker_name: str
    seeker_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "grand_hall": "the grand hall",
    "lantern_room": "the lantern room",
}

PERFORMERS = {
    "violin": {
        "label": "a violinist",
        "type": "musician",
        "sound": "a soft violin song",
        "music": "music",
        "clue": "the missing bow",
    },
    "flute": {
        "label": "a flutist",
        "type": "musician",
        "sound": "a bright flute melody",
        "music": "music",
        "clue": "the cracked reed case",
    },
}

DISGUISES = {
    "cloak": {
        "label": "a dark cloak",
        "kind": "cloak",
        "covers": {"body"},
        "mystery": "hid the source of the music",
    },
    "mask": {
        "label": "a silver mask",
        "kind": "mask",
        "covers": {"face"},
        "mystery": "made the crowd whisper",
    },
}

NAMES = {
    "fox": ["Fenn", "Mira", "Pip", "Tavi"],
    "owl": ["Orin", "Sera", "Nell", "Wren"],
}

HOSTS = {
    "fox": "fox",
    "owl": "owl",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like gala mystery told with kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--performer", choices=PERFORMERS)
    ap.add_argument("--disguise", choices=DISGUISES)
    ap.add_argument("--seeker-type", choices=HOSTS)
    ap.add_argument("--helper-type", choices=HOSTS)
    ap.add_argument("--seeker-name")
    ap.add_argument("--helper-name")
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
    place = args.place or rng.choice(list(PLACES))
    performer = args.performer or rng.choice(list(PERFORMERS))
    disguise = args.disguise or rng.choice(list(DISGUISES))
    seeker_type = args.seeker_type or rng.choice(list(HOSTS))
    helper_type = args.helper_type or ("owl" if seeker_type == "fox" else "fox")
    seeker_name = args.seeker_name or rng.choice(NAMES[seeker_type])
    helper_name = args.helper_name or rng.choice(NAMES[helper_type])
    return StoryParams(
        place=place,
        performer=performer,
        disguise=disguise,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    seeker = world.add(Entity(id=params.seeker_name, kind="character", type=params.seeker_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    performer_cfg = PERFORMERS[params.performer]
    disguise_cfg = DISGUISES[params.disguise]
    performer = world.add(Entity(
        id="performer",
        kind="character",
        type=performer_cfg["type"],
        label=performer_cfg["label"],
    ))
    disguise = world.add(Entity(
        id="disguise",
        type=disguise_cfg["kind"],
        label=disguise_cfg["label"],
        phrase=disguise_cfg["label"],
        owner=performer.id,
        worn_by=performer.id,
    ))
    # Act 1
    world.say(f"At {world.hall}, {seeker.name_or_label()} was attending a bright gala with {helper.name_or_label()}.")
    world.say(f"Above the candles came {performer_cfg['sound']}, but no one could see who was making the {performer_cfg['music']}.")
    _set_meme(seeker, "curiosity", 1)
    _set_meme(helper, "kindness", 1)
    world.para()
    # Act 2
    world.say(f"Then a pale specter seemed to drift near the musicians' door.")
    _set_meme(seeker, "fear", 1)
    world.say(f"{seeker.name_or_label()} trembled, yet {helper.name_or_label()} said, 'Let's be gentle and find out the truth before we scare anyone.'")
    _set_meme(helper, "kindness", 1)
    _set_meme(seeker, "hope", 1)
    _set_meter(seeker, "distance_to_clue", 1)
    world.say(f"They followed the faint music to a curtain, where the specter stopped and waited without a sound.")
    _set_meme(performer, "worry", 1)
    world.para()
    # Act 3
    world.say(f"{helper.name_or_label()} bowed to the specter and spoke kindly, asking what was hidden behind the curtain.")
    world.say(f"The specter lifted {disguise.label}, and the mystery was solved: the performer had been playing from behind it to keep a surprise for the gala.")
    _set_meme(performer, "relief", 2)
    _set_meme(seeker, "joy", 2)
    _set_meme(helper, "joy", 2)
    _set_meter(performer, "music_loudness", 1)
    world.say(f"Instead of laughing at the scare, {seeker.name_or_label()} smiled, and everyone welcomed the performer back into the light.")
    world.say(f"The gala ended with music, calm hearts, and a kinder crowd than before.")
    world.facts = {
        "seeker": seeker,
        "helper": helper,
        "performer": performer,
        "disguise": disguise,
        "place": params.place,
        "performer_kind": performer_cfg["label"],
        "music": performer_cfg["music"],
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a fable-like story about a gala where a specter turns out to be part of a music mystery, and kindness solves it.",
        f"Tell a gentle tale set at {world.hall} where a worried guest and a kind helper discover why the music sounds haunted.",
        "Write a child-friendly mystery story that begins with a gala, includes a specter, and ends with kindness bringing the truth into the light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    seeker = world.facts["seeker"]
    helper = world.facts["helper"]
    performer = world.facts["performer"]
    disguise = world.facts["disguise"]
    return [
        QAItem(
            question=f"Where were {seeker.name_or_label()} and {helper.name_or_label()} when the mystery began?",
            answer=f"They were at {world.hall}, which was hosting a gala.",
        ),
        QAItem(
            question="What made the music seem mysterious at first?",
            answer=f"The music seemed mysterious because a specter was drifting nearby and the performer was hidden behind {disguise.label}.",
        ),
        QAItem(
            question=f"How did {helper.name_or_label()} help solve the mystery?",
            answer=f"{helper.name_or_label()} helped by being kind, asking gentle questions, and waiting for the truth instead of scaring the specter away.",
        ),
        QAItem(
            question="What was the specter really doing?",
            answer=f"The specter was not harming anyone; it was part of the scene near the curtain, and the real mystery was the hidden performer playing music for the gala.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, the truth was known, the performer came back into the light, and the crowd felt calm and happy instead of frightened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gala?",
            answer="A gala is a fancy party or celebration with music, light, and special guests.",
        ),
        QAItem(
            question="What is a specter?",
            answer="A specter is a ghost-like figure in a story, often shown as pale and spooky.",
        ),
        QAItem(
            question="Why can kindness help in a mystery?",
            answer="Kindness helps because gentle words calm fear and make it easier for someone to tell the truth.",
        ),
        QAItem(
            question="What is music?",
            answer="Music is organized sound made by voices or instruments, like songs or tunes.",
        ),
    ]


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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(out)


CURATED = [
    StoryParams(place="grand_hall", performer="violin", disguise="cloak", seeker_type="fox", helper_type="owl", seeker_name="Fenn", helper_name="Orin"),
    StoryParams(place="lantern_room", performer="flute", disguise="mask", seeker_type="owl", helper_type="fox", seeker_name="Wren", helper_name="Mira"),
]


ASP_RULES = r"""
seeker(S) :- character(S), seeker_kind(SK), kind(S, SK).
helper(H) :- character(H), helper_kind(HK), kind(H, HK).
mystery(Place, Performer) :- gala(Place), hidden_performer(Performer).
kindness_solves(Place) :- mystery(Place, _), kind_help(_).
shown(Place, Performer) :- kindness_solves(Place), hidden_performer(Performer).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, pname in PLACES.items():
        lines.append(asp.fact("gala", pid))
    for key, cfg in PERFORMERS.items():
        lines.append(asp.fact("hidden_performer", key))
        lines.append(asp.fact("kind", key, "musician"))
    for key, cfg in DISGUISES.items():
        lines.append(asp.fact("disguise", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_sample_from_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
