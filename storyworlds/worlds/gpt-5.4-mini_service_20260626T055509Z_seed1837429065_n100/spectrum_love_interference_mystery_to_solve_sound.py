#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/spectrum_love_interference_mystery_to_solve_sound.py
============================================================================================

A small nursery-rhyme story world about a child, a mystery, a spectrum of
colors, a little bit of love, and a sound-interference puzzle that must be
solved gently.

The premise:
- A child hears a lovely song or chime.
- The sound gets muddled by interference.
- The child follows clues in a spectrum of colors and sounds.
- A friend or caregiver helps solve the mystery.
- The ending proves what changed: the sound is clear again, and the feeling of
  love stays warm.

This file is self-contained and uses only stdlib unless ASP verification is
requested.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
    glow: str
    sounds: list[str] = field(default_factory=list)
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    noise: str
    source: str
    solved_by: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    effect: str
    guards: set[str]
    solves: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.meters[key] = _meter(ent, key) + value


def _add_meme(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.memes[key] = _meme(ent, key) + value


def _is_solved(world: World) -> bool:
    return bool(world.facts.get("solved"))


def _child_name(hero: Entity) -> str:
    return hero.id


def _song_line(mood: str) -> str:
    return {
        "bells": "ding-a-ling, ding-a-ling",
        "whistle": "whish-a-whish, whish-a-whish",
        "harp": "plinny-plonny, plinny-plonny",
        "flute": "tootle-ee, tootle-ee",
    }.get(mood, "la-la-lum, la-la-lum")


def _find_interference(world: World, hero: Entity, mystery: Mystery) -> bool:
    sig = ("interference", mystery.id)
    if sig in world.fired:
        return False
    if _meter(hero, "confusion") < THRESHOLD:
        return False
    world.fired.add(sig)
    _add_meme(hero, "worry", 1.0)
    return True


def _solve_mystery(world: World, hero: Entity, helper: Entity, mystery: Mystery, device: Device) -> bool:
    sig = ("solve", mystery.id, device.id)
    if sig in world.fired:
        return False
    if _meter(hero, "clue_found") < THRESHOLD:
        return False
    if device.effect != mystery.solved_by:
        return False
    world.fired.add(sig)
    _set_meter(hero, "confusion", 0.0)
    _set_meter(hero, "clue_found", 2.0)
    _add_meme(hero, "joy", 1.0)
    _add_meme(helper, "love", 1.0)
    world.facts["solved"] = True
    return True


def _ripple(world: World, hero: Entity) -> None:
    _add_meter(hero, "listening", 1.0)
    _add_meme(hero, "wonder", 1.0)


def introduce(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved a bright tune and a tender kind of love."
    )
    world.say(
        f"Near {world.setting.place}, there came a mystery: {mystery.clue}, "
        f"{mystery.noise}, and a hush that did not feel quite right."
    )
    world.say(
        f"{helper.id} stayed close and said, \"Let's listen, let's look, let's solve this little riddle.\""
    )


def listen(world: World, hero: Entity, mystery: Mystery) -> None:
    _ripple(world, hero)
    _add_meter(hero, "confusion", 1.0)
    world.say(
        f"{hero.id} listened hard: {_song_line(world.setting.sounds[0] if world.setting.sounds else 'bells')}, "
        f"but the tune wiggled with interference."
    )
    world.say(
        f"It sounded like {_song_line('whistle')}, then {_song_line('harp')}, all mixed up in the air."
    )


def clue_hunt(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    _add_meter(hero, "clue_found", 1.0)
    _add_meme(hero, "courage", 1.0)
    world.say(
        f"{hero.id} followed a spectrum of colors: red, orange, yellow, green, blue, and violet, "
        f"each one shining like a tiny lantern."
    )
    world.say(
        f"One color glimmered where the mystery hid, and {helper.id} whispered, "
        f"\"A clue can hide in a sound, a glow, or a gentle touch.\""
    )


def choose_device(world: World, hero: Entity, helper: Entity, mystery: Mystery, device: Device) -> bool:
    if mystery.id not in device.solves:
        return False
    world.say(
        f"{helper.id} brought {device.label} and said, \"{device.prep}.\""
    )
    return True


def repair_sound(world: World, hero: Entity, helper: Entity, mystery: Mystery, device: Device) -> None:
    _add_meter(hero, "clarity", 1.0)
    _add_meme(hero, "love", 1.0)
    _add_meme(helper, "joy", 1.0)
    world.say(
        f"{hero.id} gave the device a try: {device.effect}. The interference thinned away like mist."
    )
    world.say(
        f"Then the mystery was solved: {mystery.reveal}. {device.tail.capitalize()}, and the little song came back."
    )
    world.say(
        f"{hero.id} smiled at {helper.id}, and the love in the room sounded as clear as a bell."
    )


def tell(setting: Setting, mystery: Mystery, device: Device,
         hero_name: str = "Mina", hero_type: str = "girl",
         helper_name: str = "Grandma", helper_type: str = "woman") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))

    intro_verse = [
        f"By {setting.place}, where bright things gleam,",
        f"{hero.id} heard a curious little beam.",
    ]
    world.say(" ".join(intro_verse))
    introduce(world, hero, helper, mystery)
    world.para()
    listen(world, hero, mystery)
    clue_hunt(world, hero, helper, mystery)
    if choose_device(world, hero, helper, mystery, device):
        _solve_mystery(world, hero, helper, mystery, device)
        world.para()
        repair_sound(world, hero, helper, mystery, device)

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        device=device,
        setting=setting,
        solved=_is_solved(world),
    )
    return world


SETTINGS = {
    "lantern_lane": Setting(
        place="Lantern Lane",
        indoor=False,
        glow="golden",
        sounds=["bells", "flute"],
        affords={"listen", "clue"},
    ),
    "nursery_nook": Setting(
        place="Nursery Nook",
        indoor=True,
        glow="soft",
        sounds=["harp", "whistle"],
        affords={"listen", "clue"},
    ),
    "meadow_mill": Setting(
        place="Meadow Mill",
        indoor=False,
        glow="sparkling",
        sounds=["bells", "harp"],
        affords={"listen", "clue"},
    ),
}

MYSTERIES = {
    "tin_tinkle": Mystery(
        id="tin_tinkle",
        clue="a tinny tinkle behind the daisies",
        noise="tink-tink, clink-clink",
        source="a jar of chimes under a striped cloth",
        solved_by="quieting",
        reveal="a row of little chimes had fallen together",
        tags={"sound", "mystery", "spectrum"},
    ),
    "moth_murmur": Mystery(
        id="moth_murmur",
        clue="a murmuring hum near the window",
        noise="mmmm-mmm, bzz-bzz",
        source="a fan with a ribbon caught on its edge",
        solved_by="blocking",
        reveal="a ribbon was brushing the spinning fan",
        tags={"sound", "mystery", "interference"},
    ),
    "hush_harp": Mystery(
        id="hush_harp",
        clue="a hush where a song should live",
        noise="shh-shoo, shh-shoo",
        source="a blanket draped over a singing bowl",
        solved_by="lifting",
        tags={"sound", "mystery", "love"},
        reveal="the blanket had muffled the music all along",
    ),
}

DEVICES = [
    Device(
        id="soft_cloth",
        label="a soft cloth",
        effect="it gently covered the noisy edge",
        guards={"blocking"},
        solves={"moth_murmur"},
        prep="Let's cover the spinning fan so the ribbon stops whispering",
        tail="the tiny hum turned calm at once",
    ),
    Device(
        id="bright_mirror",
        label="a bright mirror",
        effect="it bounced the spectrum of light across the room",
        guards={"quieting"},
        solves={"tin_tinkle"},
        prep="Let's angle the mirror so the colors can point us to the chimes",
        tail="the chimes stood still and sang in order again",
    ),
    Device(
        id="little_lifter",
        label="a little wooden stick",
        effect="it lifted the blanket just enough",
        guards={"lifting"},
        solves={"hush_harp"},
        prep="Let's lift the blanket and let the song breathe",
        tail="the harp sound fluttered free like a bird",
    ),
]

CURATED = [
    ("lantern_lane", "tin_tinkle", "bright_mirror"),
    ("nursery_nook", "moth_murmur", "soft_cloth"),
    ("meadow_mill", "hush_harp", "little_lifter"),
]

GIRL_NAMES = ["Mina", "Lily", "Nora", "Pippa", "Miri"]
BOY_NAMES = ["Theo", "Robin", "Eli", "Finn", "Toby"]
HELPERS = [("Grandma", "woman"), ("Grandpa", "man"), ("Aunt June", "woman")]


@dataclass
class StoryParams:
    place: str
    mystery: str
    device: str
    name: str
    gender: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about spectrum, love, and sound interference."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--device", choices=[d.id for d in DEVICES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"])
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


def valid_choices() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for dev in DEVICES:
                if mystery.id in dev.solves:
                    combos.append((place, mid, dev.id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_choices()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.device:
        combos = [c for c in combos if c[2] == args.device]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery_id, device_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
        helper_name, helper_type = args.helper or rng.choice([h[0] for h in HELPERS]), args.helper_type or "woman"
        if not args.helper:
            helper_name, helper_type = rng.choice(HELPERS)
    else:
        name = args.name or rng.choice(BOY_NAMES)
        helper_name, helper_type = args.helper or rng.choice([h[0] for h in HELPERS]), args.helper_type or "man"
        if not args.helper:
            helper_name, helper_type = rng.choice(HELPERS)
    return StoryParams(
        place=place,
        mystery=mystery_id,
        device=device_id,
        name=name,
        gender=gender,
        helper=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        next(d for d in DEVICES if d.id == params.device),
        params.name,
        params.gender,
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a child, a mystery, and a spectrum of colors.',
        f"Tell a gentle story where {f['hero'].id} hears interference and then solves the mystery with {f['device'].label}.",
        f'Write a child-friendly rhyme about "{f["mystery"].clue}" and how love helps a sound become clear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    device = f["device"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What kind of place is {setting.place} in this story?",
            answer=f"{setting.place} is where {hero.id} hears the mystery and follows the clues.",
        ),
        QAItem(
            question=f"What problem made the song hard to hear?",
            answer=f"The sound had interference, so the tune mixed with {mystery.noise} and did not sound clear.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper.id} helped by bringing {device.label} and guiding {hero.id} kindly.",
        ),
    ] + (
        [QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved when {device.label} was used to match the clue and reveal that {mystery.reveal}.",
        )] if f.get("solved") else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spectrum?",
            answer="A spectrum is a rainbow-like range of colors that changes little by little from one shade to another.",
        ),
        QAItem(
            question="What is interference?",
            answer="Interference is something that gets in the way of a signal or sound and makes it harder to hear clearly.",
        ),
        QAItem(
            question="Why do people solve mysteries carefully?",
            answer="People solve mysteries carefully so they can find the true cause and choose a safe, kind answer.",
        ),
        QAItem(
            question="What does love do in a gentle story?",
            answer="Love helps characters stay patient, kind, and willing to help one another when a problem appears.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} {e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable when a device's effect matches the mystery's solution type.
solvable(M, D) :- mystery(M), device(D), solves(D, M).
compatible(P, M, D) :- place(P), mystery(M), device(D), solvable(M, D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    for d in DEVICES:
        lines.append(asp.fact("device", d.id))
        for m in sorted(d.solves):
            lines.append(asp.fact("solves", d.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_choices())
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: clingo gate matches valid_choices() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: that choice does not fit the little mystery-and-device match.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible (place, mystery, device) combos:\n")
        for p, m, d in combos:
            print(f"  {p:12} {m:12} {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, mid, did in CURATED:
            params = StoryParams(
                place=place,
                mystery=mid,
                device=did,
                name="Mina",
                gender="girl",
                helper="Grandma",
                helper_type="woman",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
