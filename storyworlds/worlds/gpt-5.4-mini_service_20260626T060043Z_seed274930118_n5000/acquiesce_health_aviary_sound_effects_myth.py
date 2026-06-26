#!/usr/bin/env python3
"""
storyworlds/worlds/acquiesce_health_aviary_sound_effects_myth.py
=================================================================

A small mythic story world about a child-bird in an aviary, a worried healer,
and the moment of acquiescence that lets health return.

The seed words are baked into the world:
- acquiesce
- health
- aviary

The story instrument is sound: the world is full of soft and sharp sound
effects that help drive the narrative and the child's experience.
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
# Core world model
# ---------------------------------------------------------------------------
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("health", "tired", "noise", "joy", "worry", "peace", "defiance", "resolve"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
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
    affords: set[str] = field(default_factory=set)
    myth_note: str = ""


@dataclass
class Symptom:
    id: str
    label: str
    sign: str
    sound: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    heals: set[str] = field(default_factory=set)
    sound: str = ""
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.soundline: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "aviary": Setting(
        place="the moonlit aviary",
        affords={"rest", "drink", "listen"},
        myth_note="Its rafters were old as a hymn, and every cage had a bell of its own.",
    ),
    "sanctum": Setting(
        place="the quiet sanctum beside the aviary",
        affords={"rest", "drink"},
        myth_note="Even the stones seemed to ask for hush there.",
    ),
}

SYMPTOMS = {
    "hoarse": Symptom(
        id="hoarse",
        label="hoarse throat",
        sign="a rough little cough",
        sound="kheh-kheh",
        risk="the voice could fray",
        keyword="cough",
        tags={"health", "sound"},
    ),
    "tired": Symptom(
        id="tired",
        label="tired wings",
        sign="drooping wings",
        sound="flap... flutter...",
        risk="the wings could go weak",
        keyword="wings",
        tags={"health", "aviary"},
    ),
    "feverish": Symptom(
        id="feverish",
        label="feverish feathers",
        sign="warm feathers and a glassy eye",
        sound="hmmf",
        risk="the body could burn too hot",
        keyword="fever",
        tags={"health"},
    ),
}

REMEDIES = {
    "rest": Remedy(
        id="rest",
        label="a moss nest",
        phrase="a soft moss nest near the rafters",
        prep="settle into the moss nest and keep still for a while",
        tail="rested under the rafters until the breath grew easy again",
        covers={"voice", "wings", "body"},
        heals={"hoarse", "tired", "feverish"},
        sound="hush...",
    ),
    "honey": Remedy(
        id="honey",
        label="warm honey water",
        phrase="a little cup of warm honey water",
        prep="sip the warm honey water slowly",
        tail="drank the honey water and let the sweetness calm the throat",
        covers={"voice"},
        heals={"hoarse"},
        sound="glug-glug",
    ),
    "cooling": Remedy(
        id="cooling",
        label="a cool feather bath",
        phrase="a shallow bath with cool, clean water",
        prep="step into the cool feather bath and spread the wings gently",
        tail="came out fresher, with the heat easing from the feathers",
        covers={"body", "wings"},
        heals={"feverish", "tired"},
        sound="splish-splash",
    ),
}

GIRL_NAMES = ["Iris", "Mira", "Nia", "Lyra", "Thea", "Asha"]
BOY_NAMES = ["Orin", "Seth", "Taro", "Kellan", "Milo", "Darin"]
TYPES = ["bird", "sparrow", "swallow", "robin", "owl"]
TRAITS = ["curious", "brave", "gentle", "bright", "restless", "small"]


@dataclass
class StoryParams:
    place: str
    symptom: str
    remedy: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def symptom_at_risk(symptom: Symptom, remedy: Remedy) -> bool:
    return symptom.id in remedy.heals


def select_remedy(symptom: Symptom) -> Optional[Remedy]:
    for rem in REMEDIES.values():
        if symptom.id in rem.heals:
            return rem
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for sid, sym in SYMPTOMS.items():
            for rid, rem in REMEDIES.items():
                if symptom_at_risk(sym, rem) and "rest" in setting.affords:
                    out.append((place, sid, rid))
    return out


def _do_rest(world: World, actor: Entity, symptom: Symptom, remedy: Remedy, narrate: bool = True) -> None:
    if symptom.id not in remedy.heals:
        return
    actor.meters["health"] += 1
    actor.meters["tired"] = max(0.0, actor.meters["tired"] - 1)
    actor.memes["peace"] += 1
    if narrate:
        world.say(f"{remedy.sound} The {actor.type}'s breath slowed and the aviary grew gentle.")


def predict_health(world: World, hero: Entity, symptom: Symptom, remedy: Remedy) -> dict:
    sim = world.copy()
    _do_rest(sim, sim.get(hero.id), symptom, remedy, narrate=False)
    return {"health": sim.get(hero.id).meters["health"]}


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was quiet and old, and {setting.myth_note.lower()}"


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Long ago, {hero.id} lived in {world.setting.place}, where the bells knew the wind by name."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was a little {hero.traits[0]} {hero.type} who loved every echo and whistle."
    )


def love_sound(world: World, hero: Entity) -> None:
    world.soundline.append("chirp-chirp")
    world.say(
        f"When the morning came, the aviary answered with chirp-chirp and flutter-flap, "
        f"and {hero.id} listened as if the song were a map."
    )


def show_symptom(world: World, hero: Entity, symptom: Symptom) -> None:
    hero.meters["health"] = 0.0
    hero.memes["worry"] += 1
    world.soundline.append(symptom.sound)
    world.say(
        f"Then a small trouble arrived: {hero.pronoun('possessive')} {symptom.label} brought {symptom.sign}."
    )
    world.say(
        f"The sound of it was {symptom.sound}, and everyone in the aviary heard that the health of {hero.id} had gone thin."
    )


def warn(world: World, elder: Entity, hero: Entity, symptom: Symptom) -> None:
    world.say(
        f"{elder.id} lifted a wing and said, \"If you keep rushing about, {hero.id}, {symptom.risk}.\""
    )


def resist(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} wanted to keep playing beneath the arches and almost said no."
    )
    world.say(
        f"With a soft frrt of wings, {hero.id} tried to leap again, though the body still felt weak."
    )


def acquiesce(world: World, hero: Entity, elder: Entity, symptom: Symptom, remedy: Remedy) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"At last, {hero.id} looked at the old rafters, took a slow breath, and acquiesced."
    )
    world.say(
        f"{elder.id} guided {hero.id} to {remedy.prep}, and the little room answered with {remedy.sound}."
    )


def heal(world: World, hero: Entity, symptom: Symptom, remedy: Remedy) -> None:
    _do_rest(world, hero, symptom, remedy, narrate=True)
    hero.meters["health"] += 1
    hero.memes["peace"] += 1
    world.say(
        f"By dusk, the {hero.type}'s health was stronger, and {hero.pronoun('possessive')} eyes had gone bright again."
    )


def closing(world: World, hero: Entity, remedy: Remedy) -> None:
    world.say(
        f"In the moonlight, {hero.id} lay in the {remedy.label}, listening to the aviary breathe softly around {hero.pronoun('object')}."
    )
    world.say(
        f"Only hush, only warmth, only the small sound of healing remained."
    )


def tell(setting: Setting, symptom: Symptom, remedy: Remedy, hero_name: str,
         hero_type: str, elder_type: str, hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=(hero_traits or ["curious", "restless"])
    ))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    world.facts.update(hero=hero, elder=elder, symptom=symptom, remedy=remedy, setting=setting)

    introduce(world, hero)
    world.para()
    love_sound(world, hero)
    show_symptom(world, hero, symptom)
    warn(world, elder, hero, symptom)
    resist(world, hero)
    world.para()
    acquiesce(world, hero, elder, symptom, remedy)
    heal(world, hero, symptom, remedy)
    closing(world, hero, remedy)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "health": [
        ("What is health?",
         "Health is how well a body is doing. Good health means a body can move, breathe, and play more easily."),
    ],
    "aviary": [
        ("What is an aviary?",
         "An aviary is a place where birds live, rest, and fly a little inside a safe space."),
    ],
    "sound": [
        ("What is a sound effect?",
         "A sound effect is a sound that helps tell what is happening, like chirp-chirp, rustle, or splash."),
    ],
    "rest": [
        ("Why do tired bodies need rest?",
         "Rest gives a tired body time to get stronger again."),
    ],
    "honey": [
        ("Why do people sometimes drink warm honey water when their throat hurts?",
         "Warm honey water can feel soothing and help a sore throat feel calmer."),
    ],
    "cooling": [
        ("Why can cool water help on a hot day?",
         "Cool water can help a body feel less hot and more comfortable."),
    ],
}
KNOWLEDGE_ORDER = ["aviary", "sound", "health", "rest", "honey", "cooling"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, symptom, remedy = f["hero"], f["elder"], f["symptom"], f["remedy"]
    return [
        f'Write a short myth for a child about an aviary, a weak health spell, and the moment someone chooses to acquiesce.',
        f"Tell a gentle story where {hero.id} in {world.setting.place} hears {symptom.sound} sounds, resists at first, and then listens to {elder.id}.",
        f'Write a mythic bedtime story that uses the words "aviary", "health", and "acquiesce" and ends with a healing image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, symptom, remedy = f["hero"], f["elder"], f["symptom"], f["remedy"]
    q = [
        QAItem(
            question=f"What happened to {hero.id} in the aviary?",
            answer=(
                f"{hero.id} grew unwell with {symptom.label}, so {hero.pronoun('possessive')} health became weak "
                f"and the aviary heard the little sign of trouble."
            ),
        ),
        QAItem(
            question=f"Why did {elder.id} tell {hero.id} to slow down?",
            answer=(
                f"{elder.id} saw that if {hero.id} kept rushing about, {symptom.risk}. "
                f"So the elder warned {hero.pronoun('object')} to rest."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} do after at first not wanting to listen?",
            answer=(
                f"At first {hero.id} wanted to keep playing, but then {hero.pronoun('subject')} acquiesced "
                f"and followed {elder.id} to {remedy.label}."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}'s health?",
            answer=(
                f"The ending was a calm one: {hero.id} rested in the {remedy.label}, "
                f"and {hero.pronoun('possessive')} health grew stronger again."
            ),
        ),
    ]
    return q


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["symptom"].tags) | set(world.facts["remedy"].heals)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags or (key == "health" and "health" in tags):
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
symptom_at_risk(S, R) :- heals(R, S).
compatible(Place, S, R) :- affords(Place, rest), symptom(S), remedy(R), symptom_at_risk(S, R).
valid_story(Place, S, R) :- compatible(Place, S, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SYMPTOMS.items():
        lines.append(asp.fact("symptom", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for s in sorted(r.heals):
            lines.append(asp.fact("heals", rid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Resolution / generation
# ---------------------------------------------------------------------------
def explain_rejection(symptom: Symptom, remedy: Remedy) -> str:
    return (
        f"(No story: {symptom.label} is not healed by {remedy.label}, so the elder has no honest reason to offer that cure.)"
    )


def valid_selection(place: str, symptom_id: str, remedy_id: str) -> bool:
    return (place, symptom_id, remedy_id) in valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.symptom and args.remedy:
        sym, rem = SYMPTOMS[args.symptom], REMEDIES[args.remedy]
        if not symptom_at_risk(sym, rem):
            raise StoryError(explain_rejection(sym, rem))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.symptom is None or c[1] == args.symptom)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, symptom_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["owl", "heron", "sage"])
    trait = args.trait or rng.choice(TRAITS)
    hero_type = args.hero_type or rng.choice(TYPES)
    return StoryParams(place=place, symptom=symptom_id, remedy=remedy_id,
                       name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SYMPTOMS[params.symptom],
        REMEDIES[params.remedy],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.elder,
        [params.trait, "soft-hearted"],
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="aviary", symptom="hoarse", remedy="honey", name="Iris", gender="girl", elder="owl", trait="gentle"),
    StoryParams(place="aviary", symptom="tired", remedy="rest", name="Orin", gender="boy", elder="heron", trait="restless"),
    StoryParams(place="sanctum", symptom="feverish", remedy="cooling", name="Lyra", gender="girl", elder="sage", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic aviary story world with health, sound effects, and acquiescence.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--symptom", choices=SYMPTOMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["owl", "heron", "sage"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-type", choices=TYPES)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for p, s, r in triples:
            print(f"  {p:8} {s:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.symptom} at {p.place} (remedy: {p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
