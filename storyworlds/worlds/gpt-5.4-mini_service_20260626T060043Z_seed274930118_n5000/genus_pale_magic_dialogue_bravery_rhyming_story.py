#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/genus_pale_magic_dialogue_bravery_rhyming_story.py
============================================================================================================================

A small standalone storyworld about a pale moonlit place, a little bit of magic,
talking things through, and brave choices that change the ending image.

Seed image:
- A pale child or creature visits a moon garden.
- A magical lantern, gate, or bloom only opens after a brave dialogue.
- The story should sound lightly rhyming, child-facing, and complete.

This world keeps the simulation tiny and classical:
- physical state is tracked with meters
- emotional state is tracked with memes
- the plot turns when dialogue and bravery change the state enough to unlock magic

The words "genus" and "pale" are included in the world by design.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    glow: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    prompt: str
    whisper: str
    rhyme: str
    risk: str
    fixes: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    need: str
    unlock: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, val: float) -> None:
    ent.meters[key] = val


def _add_meter(ent: Entity, key: str, amt: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _set_meme(ent: Entity, key: str, val: float) -> None:
    ent.memes[key] = val


def _add_meme(ent: Entity, key: str, amt: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _capitalized(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def _join_rhyme(a: str, b: str) -> str:
    return f"{a} {b}".strip()


def _rhyming_end(word: str) -> str:
    return {
        "moon": "soon",
        "glow": "show",
        "night": "bright",
        "gate": "wait",
        "bloom": "room",
        "song": "strong",
        "cave": "brave",
    }.get(word, "light")


def reasonableness_gate(setting: Setting, challenge: Challenge, artifact: Artifact) -> None:
    if challenge.id not in setting.affords:
        raise StoryError("This setting cannot host that kind of magical challenge.")
    if challenge.id not in artifact.need and challenge.id not in artifact.unlock and challenge.id not in challenge.fixes:
        raise StoryError("This artifact does not reasonably answer the challenge.")
    if not challenge.fixes:
        raise StoryError("The story needs at least one plausible brave fix.")


def setup_story(world: World, hero: Entity, guide: Entity, challenge: Challenge, artifact: Artifact) -> None:
    world.say(
        f"{hero.id} was {hero.label}, a pale little {hero.type} with a head full of wonder."
    )
    world.say(
        f"Near the {world.setting.place}, {guide.label} kept a {artifact.phrase} that shimmered like a {world.setting.glow}."
    )
    world.say(
        f"{hero.id} liked the {challenge.id} and its gentle, jingle-jangling rhyme; "
        f"{challenge.whisper} was the sort of whisper that asked for time."
    )


def predict_unlock(world: World, hero: Entity, challenge: Challenge, artifact: Artifact) -> bool:
    sim = world.copy()
    attempt_dialogue(sim, sim.get(hero.id), challenge, narrate=False)
    return _meme(sim.get(hero.id), "courage") >= THRESHOLD and _meme(sim.get(artifact.id), "opened") >= THRESHOLD


def challenge_state(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    _add_meme(hero, "curiosity", 1)
    world.say(
        f"{hero.id} stepped a little closer, where {challenge.rhyme} softly hummed in the air."
    )


def hear_whisper(world: World, hero: Entity, guide: Entity, challenge: Challenge) -> None:
    _add_meme(hero, "hesitation", 1)
    world.say(
        f"Then {guide.id} said, \"{challenge.whisper}\" and the words sat like dew in the dark."
    )


def attempt_dialogue(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    if _meme(hero, "courage") < THRESHOLD:
        _add_meme(hero, "courage", 1)
        _add_meter(hero, "voice", 1)
        if narrate:
            world.say(
                f"{hero.id} took a breath and spoke right back: \"I can try, I can be spry.\""
            )
    if _meme(hero, "courage") >= THRESHOLD and narrate:
        world.say(
            f"{hero.id} did not run; {hero.pronoun()} stayed and talked, and the tune felt less shy."
        )


def magic_rule(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if _meme(ent, "courage") < THRESHOLD or _meter(ent, "voice") < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.id != "artifact":
                continue
            if _meme(item, "opened") >= THRESHOLD:
                continue
            sig = ("open", ent.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _set_meme(item, "opened", 1)
            item.meters["glow"] = item.meters.get("glow", 0.0) + 1
            out.append(
                f"The {item.label} answered the brave voice and opened wide."
            )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for line in magic_rule(world):
            changed = True
            produced.append(line)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def resolve_scene(world: World, hero: Entity, guide: Entity, challenge: Challenge, artifact: Artifact) -> None:
    if _meme(hero, "courage") < THRESHOLD:
        return
    propagate(world, narrate=False)
    if _meme(artifact, "opened") >= THRESHOLD:
        world.say(
            f"Inside was a tiny bright key, and the key was the shape of a smile."
        )
        world.say(
            f"{hero.id} and {guide.id} laughed together, and the moon looked kind and mild."
        )


def tell(setting: Setting, challenge: Challenge, artifact: Artifact,
         hero_name: str, hero_type: str, guide_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=f"{_article('pale')} pale {hero_type}",
        traits=["pale", "curious"],
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        label="the moon-keeper",
        traits=["gentle", "wise"],
    ))
    thing = world.add(Entity(
        id="artifact",
        type="thing",
        label=artifact.label,
        phrase=artifact.phrase,
        owner=guide.id,
        meters={"glow": 0.0},
        memes={"opened": 0.0},
    ))

    setup_story(world, hero, guide, challenge, artifact)
    world.para()
    challenge_state(world, hero, challenge)
    hear_whisper(world, hero, guide, challenge)
    attempt_dialogue(world, hero, challenge)
    resolve_scene(world, hero, guide, challenge, thing)

    world.facts.update(
        hero=hero,
        guide=guide,
        artifact=thing,
        setting=setting,
        challenge=challenge,
        artifact_cfg=artifact,
    )
    return world


SETTINGS = {
    "moon_garden": Setting(place="moon garden", glow="moon-lace glow", affords={"gate", "bloom", "mirror"}),
    "pale_hall": Setting(place="pale hall", glow="candle-milk glow", affords={"mirror", "gate"}),
    "quiet_copse": Setting(place="quiet copse", glow="dew-gleam glow", affords={"bloom", "gate"}),
}

CHALLENGES = {
    "gate": Challenge(
        id="gate",
        prompt="a little silver gate",
        whisper="The gate will open if you speak true and steady.",
        rhyme="the gate that waits by the moonlit slate",
        risk="stays shut",
        fixes={"courage", "voice"},
        tags={"gate", "moon"},
    ),
    "bloom": Challenge(
        id="bloom",
        prompt="a pale bloom in the grass",
        whisper="The bloom will lift if you say your wish out loud.",
        rhyme="the bloom in the room of the moonbeam plume",
        risk="stays asleep",
        fixes={"courage", "kindness"},
        tags={"bloom", "flower"},
    ),
    "mirror": Challenge(
        id="mirror",
        prompt="a moon mirror",
        whisper="The mirror will shine if you answer your own question.",
        rhyme="the mirror that clears with a brave little cheer",
        risk="stays dim",
        fixes={"courage", "voice"},
        tags={"mirror", "light"},
    ),
}

ARTIFACTS = {
    "lantern_key": Artifact(
        id="lantern_key",
        label="lantern key",
        phrase="a lantern key of pearl and pine",
        need="gate",
        unlock="gate",
    ),
    "moon_flute": Artifact(
        id="moon_flute",
        label="moon flute",
        phrase="a moon flute with a silver spine",
        need="bloom",
        unlock="bloom",
    ),
    "glass_mirror": Artifact(
        id="glass_mirror",
        label="glass mirror",
        phrase="a glass mirror with a pale blue line",
        need="mirror",
        unlock="mirror",
    ),
}

GENERA = ["luma", "cera", "nocta", "palea", "aurora"]
NAMES = ["Mina", "Tao", "Rin", "Lio", "Nora", "Ezra", "Mila", "Jules"]
TYPES = ["girl", "boy", "child"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    artifact: str
    name: str
    hero_type: str
    guide_type: str
    genus: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for c_id in setting.affords:
            challenge = CHALLENGES[c_id]
            for a_id, art in ARTIFACTS.items():
                if c_id in art.need or c_id in art.unlock:
                    combos.append((s_id, c_id, a_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child using the words "genus" and "pale".',
        f"Tell a magical dialogue story where {f['hero'].id} is pale, brave, and asks a moon-keeper about the {f['challenge'].id}.",
        f"Write a gentle rhyme about a pale child who uses brave words to wake a magic {f['artifact_cfg'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    challenge = f["challenge"]
    art = f["artifact_cfg"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a pale little {hero.type}, and the moon-keeper who helped with the {challenge.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} need to do to make the magic work?",
            answer=f"{hero.id} needed to speak bravely and keep talking instead of backing away.",
        ),
        QAItem(
            question=f"What kind of thing was waiting to open?",
            answer=f"It was {art.phrase}, and it opened when the brave dialogue began.",
        ),
        QAItem(
            question=f"Who spoke the helpful whisper?",
            answer=f"{guide.id} did, saying that the {challenge.id} would open if {hero.id} spoke true and steady.",
        ),
        QAItem(
            question=f"Which seed word showed up in the story world?",
            answer=f"The story used the word genus, and it also described the hero as pale.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does pale mean?",
            answer="Pale means having a light color, like soft cream, mist, or moonlight.",
        ),
        QAItem(
            question="What is a genus?",
            answer="A genus is a group used to sort living things that are alike, like cousins in a big family of nature.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is talking back and forth between characters.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being scared or unsure but still choosing to do the right thing.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, challenge: Challenge, artifact: Artifact) -> str:
    return (
        f"(No story: {setting.place} cannot reasonably host the {challenge.id} with {artifact.label}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.challenge and args.artifact:
        if (args.setting, args.challenge, args.artifact) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], CHALLENGES[args.challenge], ARTIFACTS[args.artifact]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.artifact is None or c[2] == args.artifact)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, challenge, artifact = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(TYPES)
    guide_type = args.guide_type or "keeper"
    genus = args.genus or rng.choice(GENERA)
    return StoryParams(setting=setting, challenge=challenge, artifact=artifact, name=name, hero_type=hero_type, guide_type=guide_type, genus=genus)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHALLENGES[params.challenge],
        ARTIFACTS[params.artifact],
        params.name,
        params.hero_type,
        params.guide_type,
    )
    story = world.render()
    if "genus" not in story.lower():
        story += " The old book of genus names shone pale beside the path."
    return StorySample(
        params=params,
        story=story,
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
goal_ok(S,C,A) :- setting(S), challenge(C), artifact(A), affords(S,C), unlocks(A,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", sid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("unlocks", aid, a.unlock))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show goal_ok/3."))
    return sorted(set(asp.atoms(model, "goal_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming magic storyworld with dialogue and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--guide-type")
    ap.add_argument("--genus")
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


CURATED = [
    StoryParams(setting="moon_garden", challenge="gate", artifact="lantern_key", name="Mina", hero_type="girl", guide_type="keeper", genus="palea"),
    StoryParams(setting="pale_hall", challenge="mirror", artifact="glass_mirror", name="Tao", hero_type="boy", guide_type="keeper", genus="luma"),
    StoryParams(setting="quiet_copse", challenge="bloom", artifact="moon_flute", name="Rin", hero_type="child", guide_type="keeper", genus="nocta"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show goal_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for c in combos:
            print("  ", c)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            seed = rng_base + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.challenge} in {p.setting} ({p.artifact})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
