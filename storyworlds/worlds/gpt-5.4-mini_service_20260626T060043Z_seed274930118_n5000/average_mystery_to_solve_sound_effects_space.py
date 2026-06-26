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
class SoundEffect:
    id: str
    onomatopoeia: str
    source: str
    clue: str
    volume: str
    can_startle: bool = True


@dataclass
class Setting:
    place: str
    nearby: str
    oddity: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    owner: str = ""
    used_for: str = ""
    plural: bool = False


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "captain", "pilot"}
        female = {"girl", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") or self.type in {"tools"} else "it"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    sound: str
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    seed: Optional[int] = None


SETTINGS = {
    "orbit": Setting(place="the orbiting station", nearby="the silver window", oddity="a drifting cargo crate", affords={"beeps", "clang", "whirr"}),
    "moonbase": Setting(place="the moonbase", nearby="the airlock", oddity="a tunnel of dust", affords={"beeps", "buzz", "clang"}),
    "cargo": Setting(place="the cargo bay", nearby="the stacked crates", oddity="a loose hatch panel", affords={"whirr", "clang", "beeps"}),
}

SOUNDS = {
    "beeps": SoundEffect(id="beeps", onomatopoeia="beep-beep", source="a broken beacon", clue="it was signaling a tiny stuck tracker", volume="soft"),
    "whirr": SoundEffect(id="whirr", onomatopoeia="whirrr", source="a spinning fan", clue="it was a cooling fan turning too fast", volume="steady"),
    "clang": SoundEffect(id="clang", onomatopoeia="clang!", source="a bouncing tool", clue="it was a wrench tapping the wall", volume="loud"),
    "buzz": SoundEffect(id="buzz", onomatopoeia="bzzz", source="a sleepy drone", clue="it was a helper drone rubbing a loose screw", volume="thin"),
}

MYSTERIES = {
    "lost_signal": "who kept making the little beep-beep sound",
    "mystery_draft": "where the cold draft was coming from",
    "mystery_noise": "what was making the loud clang",
}

NAMES = ["Mira", "Tala", "Nico", "Juno", "Pip", "Rin", "Zed", "Luna"]
TYPES = ["girl", "boy"]
PARTNERS = [("captain", "captain"), ("pilot", "pilot"), ("mechanic", "mechanic")]

CURATED = [
    StoryParams(setting="orbit", mystery="lost_signal", sound="beeps", hero="Mira", hero_type="girl", partner="Tala", partner_type="pilot"),
    StoryParams(setting="moonbase", mystery="mystery_draft", sound="whirr", hero="Nico", hero_type="boy", partner="Juno", partner_type="mechanic"),
    StoryParams(setting="cargo", mystery="mystery_noise", sound="clang", hero="Luna", hero_type="girl", partner="Zed", partner_type="captain"),
]

TRAITS = ["curious", "brave", "patient", "steady", "clever", "calm"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure mystery stories with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--partner")
    ap.add_argument("--partner-type", choices=["captain", "pilot", "mechanic"])
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


def _reasonable(setting: Setting, mystery: str, sound: str) -> bool:
    return sound in setting.affords and mystery in MYSTERIES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.sound:
        setting_name = args.setting or rng.choice(list(SETTINGS))
        if not _reasonable(SETTINGS[setting_name], args.mystery, args.sound):
            raise StoryError("That mystery and sound do not fit this space setting.")
    choices = []
    for s_name, setting in SETTINGS.items():
        if args.setting and args.setting != s_name:
            continue
        for m_name in MYSTERIES:
            if args.mystery and args.mystery != m_name:
                continue
            for snd_name in SOUNDS:
                if args.sound and args.sound != snd_name:
                    continue
                if not _reasonable(setting, m_name, snd_name):
                    continue
                choices.append((s_name, m_name, snd_name))
    if not choices:
        raise StoryError("No valid combination matches the requested options.")
    setting, mystery, sound = rng.choice(sorted(choices))
    hero_type = args.hero_type or rng.choice(TYPES)
    hero = args.hero or rng.choice(NAMES)
    partner_type = args.partner_type or rng.choice(["captain", "pilot", "mechanic"])
    partner = args.partner or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(setting=setting, mystery=mystery, sound=sound, hero=hero, hero_type=hero_type,
                       partner=partner, partner_type=partner_type)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add_entity(Entity(id=params.hero, kind="character", type=params.hero_type, traits=["little", random.choice(TRAITS)]))
    partner = world.add_entity(Entity(id=params.partner, kind="character", type=params.partner_type, traits=[random.choice(TRAITS)]))
    sound = SOUNDS[params.sound]
    world.facts.update(hero=hero, partner=partner, sound=sound, mystery=params.mystery, setting=world.setting)
    hero.memes["curiosity"] = 1.0
    partner.memes["calm"] = 1.0

    world.say(f"{hero.id} was a little {hero.traits[1]} {hero.type} aboard {world.setting.place}.")
    world.say(f"{hero.id} liked the steady hum of the ship and the bright view near {world.setting.nearby}.")
    world.say(f"One day, {hero.id} heard {sound.onomatopoeia} from somewhere nearby.")
    world.para()
    world.say(f'"That sound is a mystery," said {partner.id}. "Let’s solve {sound.clue}."')
    world.say(f"{hero.id} listened near {world.setting.oddity}, then tiptoed toward the noise.")
    if sound.id == "beeps":
        world.say(f"The beeps got a little faster, {sound.onomatopoeia}, {sound.onomatopoeia}, like a tiny message asking for help.")
    elif sound.id == "whirr":
        world.say(f"The whirr grew smoother and steadier, {sound.onomatopoeia}, as if a machine was trying hard to keep working.")
    elif sound.id == "clang":
        world.say(f"The clang rang again, {sound.onomatopoeia}! It bounced off the walls and made {hero.id} blink.")
    else:
        world.say(f"The buzz tickled the air, {sound.onomatopoeia}, and the crew followed it carefully.")
    world.say(f"{partner.id} checked behind the panels while {hero.id} looked under the crate lids.")
    world.para()
    world.say(f"Then they found it: {sound.clue}.")
    world.say(f"{hero.id} smiled because the mystery was solved, and the strange sound became an ordinary ship sound again.")
    world.say(f"At the end, the station felt quiet and safe, and {hero.id} and {partner.id} waved at the stars.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a child that includes the sound word "{f["sound"].onomatopoeia}".',
        f"Tell a gentle mystery story on {world.setting.place} where {f['hero'].id} and {f['partner'].id} solve a noisy problem together.",
        f'Write a simple story about a curious child who hears "{f["sound"].source}" and learns what it really is.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    sound = f["sound"]
    setting = world.setting
    return [
        QAItem(
            question=f"What mystery did {hero.id} want to solve on {setting.place}?",
            answer=f"{hero.id} wanted to solve {MYSTERIES[f['mystery']]}, and {partner.id} helped look for the answer.",
        ),
        QAItem(
            question=f"What sound did {hero.id} hear near {setting.nearby}?",
            answer=f"{hero.id} heard {sound.onomatopoeia}, which led them to search the ship carefully.",
        ),
        QAItem(
            question=f"What did they discover at the end of the story?",
            answer=f"They discovered that the sound came from {sound.source}, so the mystery was solved.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the mystery was solved?",
            answer=f"{hero.id} felt happy and calm because the strange sound made sense at last.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mystery?", answer="A mystery is something you do not understand yet, so you look for clues to solve it."),
        QAItem(question="What does a sound effect do in a story?", answer="A sound effect helps readers imagine a noise, like beep-beep or clang, in a vivid way."),
        QAItem(question="What is a space station?", answer="A space station is a place made by people that orbits in space so astronauts can work and live there."),
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps solve a problem or mystery."),
        QAItem(question="Why do people listen carefully in a mystery?", answer="People listen carefully because sounds and details can point them toward the answer."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}) memes={e.memes} meters={e.meters}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(space).
sound_ok(orbit, beeps).
sound_ok(orbit, whirr).
sound_ok(orbit, clang).
sound_ok(moonbase, beeps).
sound_ok(moonbase, buzz).
sound_ok(moonbase, clang).
sound_ok(cargo, whirr).
sound_ok(cargo, clang).
sound_ok(cargo, beeps).

valid(S, M, X) :- sound_ok(S, X), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for sid, snds in {"orbit": {"beeps", "whirr", "clang"}, "moonbase": {"beeps", "buzz", "clang"}, "cargo": {"whirr", "clang", "beeps"}}.items():
        for s in snds:
            lines.append(asp.fact("sound_ok", sid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for s in SETTINGS:
        for m in MYSTERIES:
            for x in SOUNDS:
                if _reasonable(SETTINGS[s], m, x):
                    py.add((s, m, x))
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - clingo))
    print("clingo-only:", sorted(clingo - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
