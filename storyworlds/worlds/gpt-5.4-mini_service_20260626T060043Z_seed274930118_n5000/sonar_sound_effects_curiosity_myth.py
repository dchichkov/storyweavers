#!/usr/bin/env python3
"""
storyworlds/worlds/sonar_sound_effects_curiosity_myth.py
=========================================================

A standalone story world about a curious child, a mythic sea, and a sonar
signal that sounds like a tiny song.

The seed image:
---
A child on the shore hears a strange sonar pulse from the dark water.
The sound goes "ping... ping... ping..." like a silver drum under the waves.
Curious, the child wants to follow it, but the elder warns that the deep sea
belongs to old spirits. The child keeps listening, finds the source, and
discovers the signal is calling for help. By helping, the child earns a
blessing and learns the sea was not frightening after all.

This script models that premise as a small causal world:
- a setting with one mythic shore or bay
- a sonar sound source that can be followed
- a curious hero who may disobey a warning
- a hidden object or creature that is only found by listening closely
- a resolution that proves curiosity helped, not harmed

The prose is authored from the world state; the sound effects are narrated as
concrete story beats, not as raw event logs.
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
    caretaker: Optional[str] = None
    tethered_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "elderwoman"}
        male = {"boy", "father", "man", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    shore_name: str
    sea_name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    sound: str
    source: str
    danger: str
    reveals: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    kind: str
    risk: str
    region: str = "deep"
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.signal_strength: float = 0.0
        self.hidden_revealed: bool = False

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
        clone.fired = set(self.fired)
        clone.signal_strength = self.signal_strength
        clone.hidden_revealed = self.hidden_revealed
        return clone


def _r_signal_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.signal_strength < THRESHOLD or world.hidden_revealed:
        return out
    if ("reveal", world.facts.get("signal_id")) in world.fired:
        return out
    world.fired.add(("reveal", world.facts.get("signal_id")))
    world.hidden_revealed = True
    out.append("The sound grew sharp and clear, and something hidden began to show itself.")
    return out


def _r_blessing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero or not world.hidden_revealed:
        return out
    if ("bless", hero.id) in world.fired:
        return out
    world.fired.add(("bless", hero.id))
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    out.append("The sea answered with a blessing, as if it had been waiting to be noticed.")
    return out


CAUSAL_RULES = [_r_signal_reveal, _r_blessing]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_signal(world: World, hero: Entity, signal: Signal) -> bool:
    sim = world.copy()
    sim.signal_strength += 1.0
    propagate(sim, narrate=False)
    return sim.hidden_revealed


def setting_detail(setting: Setting) -> str:
    return {
        "cove": f"The {setting.shore_name} was quiet, and the {setting.sea_name} breathed against the stones.",
        "cliff": f"High above the {setting.sea_name}, the cliff faced the wind like an old guardian.",
        "harbor": f"At the {setting.place}, boats slept while the {setting.sea_name} shimmered in moonlight.",
    }.get(setting.place, f"{setting.shore_name} stood near the {setting.sea_name}, wrapped in a deep, old hush.")


def signal_sound(signal: Signal) -> str:
    return signal.sound


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who listened to every whisper of the sea.")


def loves_sound(world: World, hero: Entity, signal: Signal) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.signal_strength += 1.0
    world.say(
        f"{hero.pronoun().capitalize()} heard the sonar go {signal.sound} and loved how it echoed like a tiny silver drum."
    )


def arrive(world: World, hero: Entity) -> None:
    world.say(f"One evening, {hero.id} stood at {world.setting.shore_name} and watched the dark water glitter.")
    world.say(setting_detail(world.setting))


def warn(world: World, elder: Entity, hero: Entity, signal: Signal) -> bool:
    if not predict_signal(world, hero, signal):
        return False
    world.facts["warning"] = signal.danger
    world.say(
        f'"Do not follow the {signal.label}," {elder.pronoun("subject")} said. '
        f'"Old things sleep below the waves."'
    )
    return True


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(f"{hero.id} held still for a moment, listening to the pinging water and wondering what called from below.")


def follow_sound(world: World, hero: Entity, signal: Signal) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(f'But {hero.id} followed the sound anyway: "{signal.sound}"')
    world.signal_strength += 1.0
    propagate(world, narrate=True)


def reveal(world: World, signal: Signal, prize: Prize) -> None:
    world.say(
        f"Down in the blue dark, the {signal.label} led to {prize.phrase}. "
        f"The noise was not a threat at all; it was a plea for help."
    )


def help_source(world: World, hero: Entity, prize: Prize) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    world.say(
        f"{hero.id} reached for the lost {prize.label} and brought it back into the light."
    )


def resolve(world: World, hero: Entity, prize: Prize, charm: Optional[Charm]) -> None:
    if charm:
        world.say(
            f"Then {hero.id} wore {charm.phrase}, and the waves stayed calm around {hero.pronoun('object')}."
        )
    world.say(
        f"The sea quieted to a soft hush. {hero.id} walked home with salt on {hero.pronoun('possessive')} hands and wonder in {hero.pronoun('possessive')} heart."
    )


def tell(setting: Setting, signal: Signal, prize: Prize, charm: Optional[Charm],
         hero_name: str, hero_type: str, parent_type: str, elder_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "curious", "brave"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    elder = world.add(Entity(id=elder_name, kind="character", type="elderwoman", label="the elder"))
    prize_ent = world.add(Entity(
        id=prize.id, type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=parent.id, meters={"hidden": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, elder=elder, prize=prize_ent, signal_id=signal.id, signal=signal, charm=charm)

    introduce(world, hero)
    loves_sound(world, hero, signal)
    world.para()
    arrive(world, hero)
    warn(world, elder, hero, signal)
    hesitate(world, hero)
    follow_sound(world, hero, signal)
    world.para()
    reveal(world, signal, prize)
    help_source(world, hero, prize_ent)
    if charm is not None:
        world.say(
            f'{hero.id} accepted the {charm.label} as a gift from the sea, because help deserved thanks.'
        )
    resolve(world, hero, prize_ent, charm)
    return world


SETTINGS = {
    "cove": Setting(place="cove", shore_name="the moon cove", sea_name="the listening sea", mood="mythic", affords={"sonar"}),
    "cliff": Setting(place="cliff", shore_name="the black cliff", sea_name="the deep sea", mood="stormy", affords={"sonar"}),
    "harbor": Setting(place="harbor", shore_name="the old harbor", sea_name="the silver water", mood="gentle", affords={"sonar"}),
}

SIGNALS = {
    "sonar_call": Signal(
        id="sonar_call",
        label="sonar call",
        sound="ping... ping... ping...",
        source="a lost pearl horn",
        danger="the deep was full of old secrets",
        reveals="a hidden pearl horn",
        requires={"curiosity"},
        tags={"sonar", "sound", "curiosity"},
    ),
    "sonar_echo": Signal(
        id="sonar_echo",
        label="sonar echo",
        sound="thrum... ping... thrum...",
        source="a shell gate beneath the waves",
        danger="the water was dark and strange",
        reveals="a sunken shell gate",
        requires={"curiosity"},
        tags={"sonar", "sound"},
    ),
}

PRIZES = {
    "pearl_horn": Prize(
        id="pearl_horn",
        label="pearl horn",
        phrase="a silver pearl horn",
        type="thing",
        kind="instrument",
        risk="lost in the deep",
    ),
    "star_map": Prize(
        id="star_map",
        label="star map",
        phrase="a sea-stained star map",
        type="thing",
        kind="map",
        risk="washed away",
    ),
}

CHARMS = {
    "shell_cloak": Charm(
        id="shell_cloak",
        label="shell cloak",
        phrase="a cloak of shell-blue light",
        guards={"fear"},
        helps={"curiosity"},
        prep="accept the cloak",
        tail="the waves quieted",
    ),
}


@dataclass
class StoryParams:
    place: str
    signal: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mira", "Luna", "Asha", "Nina", "Tala", "Suri"]
BOY_NAMES = ["Kai", "Oren", "Milo", "Niko", "Ravi", "Eli"]
PARENT_TYPES = ["mother", "father"]
CURATED = [
    StoryParams(place="cove", signal="sonar_call", prize="pearl_horn", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="harbor", signal="sonar_echo", prize="star_map", name="Kai", gender="boy", parent="father"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, s, r) for p in SETTINGS for s in SIGNALS for r in PRIZES]


def explain_rejection(signal: Signal, prize: Prize) -> str:
    return f"(No story: the chosen sonar and prize do not make a mythic enough problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about sonar, curiosity, and a sea blessing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.signal:
        combos = [c for c in combos if c[1] == args.signal]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, signal, prize = rng.choice(combos)
    prize_obj = PRIZES[prize]
    gender = args.gender or rng.choice(sorted({"girl", "boy"}))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, signal=signal, prize=prize, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    signal = f["signal"]
    prize = f["prize"]
    return [
        f'Write a short mythic story for a child about sonar and curiosity using "{signal.sound}".',
        f"Tell a gentle sea myth where {hero.id} follows a {signal.label} to find a lost {prize.label}.",
        f"Write a story in which a child hears sonar, is warned by an elder, and discovers that the sound means help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, elder, prize, signal = f["hero"], f["parent"], f["elder"], f["prize"], f["signal"]
    return [
        QAItem(
            question=f"What did {hero.id} hear near the shore?",
            answer=f"{hero.id} heard a {signal.label} go {signal.sound} near the sea.",
        ),
        QAItem(
            question=f"Why did the elder warn {hero.id}?",
            answer=f"The elder warned {hero.id} because old things slept below the waves and the deep sea seemed dangerous.",
        ),
        QAItem(
            question=f"What did curiosity lead {hero.id} to find?",
            answer=f"Curiosity led {hero.id} to the lost {prize.label}, and that sound was really a call for help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sonar?",
            answer="Sonar is a way of sending out sound and listening for the echo that comes back, so people can find things in dark water.",
        ),
        QAItem(
            question="Why do echoes matter in the sea?",
            answer="Echoes matter because sound can bounce off hidden objects, helping someone learn what is below the surface.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, listen, and learn about something unknown.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  signal_strength={world.signal_strength}")
    lines.append(f"  hidden_revealed={world.hidden_revealed}")
    return "\n".join(lines)


ASP_RULES = r"""
shown_valid(Place, Signal, Prize) :- setting(Place), sonar_signal(Signal), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for s in SIGNALS:
        lines.append(asp.fact("sonar_signal", s))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown_valid/3."))
    return sorted(set(asp.atoms(model, "shown_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SIGNALS[params.signal],
        PRIZES[params.prize],
        CHARMS["shell_cloak"],
        params.name,
        params.gender,
        params.parent,
        "Nera",
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shown_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.signal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
