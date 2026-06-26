#!/usr/bin/env python3
"""
A small fable-style storyworld about sound effects, a little parmesan, and a
problem that gets solved by listening carefully.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rat", "bird", "fox", "wolf"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, setting: str, tone: str = "fable") -> None:
        self.setting = setting
        self.tone = tone
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


@dataclass
class SoundItem:
    word: str
    description: str
    effect: str


@dataclass
class StoryParams:
    setting: str
    sound: str
    parmesan: str
    hero: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": "a warm kitchen",
    "barn": "a cozy barn",
    "garden": "a little garden",
    "cellar": "a cool cellar",
}

HEROES = {
    "mouse": {"kind": "character", "type": "mouse", "label": "mouse"},
    "bird": {"kind": "character", "type": "bird", "label": "bird"},
    "fox": {"kind": "character", "type": "fox", "label": "fox"},
}

HELPERS = {
    "sparrow": {"kind": "character", "type": "bird", "label": "sparrow"},
    "cat": {"kind": "character", "type": "cat", "label": "cat"},
    "hen": {"kind": "character", "type": "bird", "label": "hen"},
}

PARMESANS = {
    "wedge": "a small wedge of parmesan",
    "shavings": "a paper bowl of parmesan shavings",
    "rind": "a hard parmesan rind",
}

SOUNDS = {
    "crunch": SoundItem("crunch", "a dry little bite of parmesan", "crunch-crunch"),
    "scrape": SoundItem("scrape", "a grate against a hard rind", "scrrrape"),
    "clink": SoundItem("clink", "a tiny cheese bowl touching the floor", "clink"),
    "plop": SoundItem("plop", "a soft cheese piece dropping into place", "plop"),
}

CURATED = [
    StoryParams(setting="kitchen", sound="crunch", parmesan="wedge", hero="mouse", helper="sparrow"),
    StoryParams(setting="barn", sound="scrape", parmesan="rind", hero="bird", helper="cat"),
    StoryParams(setting="garden", sound="clink", parmesan="shavings", hero="fox", helper="hen"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about parmesan and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--parmesan", choices=PARMESANS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combo(setting: str, sound: str, parmesan: str, hero: str, helper: str) -> bool:
    if hero == helper:
        return False
    if setting == "cellar" and sound == "clink":
        return False
    if parmesan == "rind" and sound not in {"scrape", "crunch"}:
        return False
    if hero == "mouse" and parmesan == "shavings" and sound == "scrape":
        return False
    return True


def all_valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for sound in SOUNDS:
            for parmesan in PARMESANS:
                for hero in HEROES:
                    for helper in HELPERS:
                        if valid_combo(setting, sound, parmesan, hero, helper):
                            combos.append((setting, sound, parmesan, hero, helper))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in all_valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.sound is None or c[1] == args.sound)
        and (args.parmesan is None or c[2] == args.parmesan)
        and (args.hero is None or c[3] == args.hero)
        and (args.helper is None or c[4] == args.helper)
    ]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, sound, parmesan, hero, helper = rng.choice(sorted(combos))
    return StoryParams(setting=setting, sound=sound, parmesan=parmesan, hero=hero, helper=helper)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for p in PARMESANS:
        lines.append(asp.fact("parmesan", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, So, P, H, He) :- setting(S), sound(So), parmesan(P), hero(H), helper(He),
                          H != He, not bad(S, So, P, H, He).
bad(cellar, clink, _, _, _).
bad(_, scrape, shavings, mouse, _).
bad(_, plop, rind, _, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(all_valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def make_world(params: StoryParams) -> World:
    w = World(SETTINGS[params.setting])
    hero = w.add(Entity(id="hero", **HEROES[params.hero]))
    helper = w.add(Entity(id="helper", **HELPERS[params.helper]))
    parmesan = w.add(Entity(
        id="parmesan",
        kind="thing",
        type="cheese",
        label="parmesan",
        phrase=PARMESANS[params.parmesan],
        owner=hero.id,
        carried_by=hero.id,
    ))
    sound = SOUNDS[params.sound]

    hero.memes["curiosity"] = 1
    hero.memes["delight"] = 1
    helper.memes["wisdom"] = 1

    w.say(
        f"Once in {w.setting}, a little {hero.type} found {parmesan.phrase} and listened to the world."
    )
    w.say(
        f'Every time {hero.pronoun()} nibbled it, the air went "{sound.effect}," and the sound seemed almost magical.'
    )
    w.para()
    w.say(
        f"The little {hero.type} wanted more of that sweet {params.sound} sound, but {helper.label} warned that not every noise was wise."
    )

    if params.sound == "crunch":
        hero.memes["greed"] = 1
        parmesan.meters["smaller"] = 1
        w.say(f"The {hero.type} took one bite too many, and the {params.sound} sound became a whole habit.")
    elif params.sound == "scrape":
        helper.memes["concern"] = 1
        w.say(f"The hard {params.parmesan} made a loud {sound.effect}, and the helper frowned at the roughness of it.")
    elif params.sound == "clink":
        helper.memes["care"] = 1
        parmesan.meters["fell"] = 1
        w.say(f"With a little {sound.effect}, the parmesan bowl tipped, and everyone paused before laughing.")
    else:
        helper.memes["care"] = 1
        w.say(f"The soft {sound.effect} was gentle, and the helper showed how to share it without waste.")

    w.para()
    if params.sound == "crunch":
        w.say(
            f"The helper said, 'A pleasant sound is a good teacher, but a greedy sound can leave only crumbs.'"
        )
        w.say(
            f"The {hero.type} listened, then set aside the parmesan so the next nibble would be a treat, not a tumble."
        )
    elif params.sound == "scrape":
        w.say(
            f"The helper said, 'Use a careful touch, for a rough sound can become rough manners.'"
        )
        w.say(
            f"So the {hero.type} softened the hold, and the parmesan stayed useful instead of becoming a mess."
        )
    elif params.sound == "clink":
        w.say(
            f"The helper said, 'A mistake can ring loudly, but a quick apology rings sweeter.'"
        )
        w.say(
            f"The {hero.type} smiled, picked up the parmesan, and the little {sound.effect} became a lesson about patience."
        )
    else:
        w.say(
            f"The helper said, 'Gentle sounds belong to gentle hands.'"
        )
        w.say(
            f"The {hero.type} shared the parmesan, and the room grew calm, as if the day itself had learned to whisper."
        )

    w.facts.update(params=params, hero=hero, helper=helper, parmesan=parmesan, sound=sound)
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a short fable about a {p.hero} who hears "{p.sound}" around parmesan.',
        f"Tell a child-friendly story where parmesan makes a {p.sound} sound and a helper gives wise advice.",
        f'Create a gentle fable in which "{p.sound}" teaches a little creature about sharing parmesan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    parmesan: Entity = world.facts["parmesan"]
    sound: SoundItem = world.facts["sound"]
    return [
        QAItem(
            question=f"What did the little {hero.type} find in {world.setting}?",
            answer=f"The little {hero.type} found {parmesan.phrase} and listened to it very carefully.",
        ),
        QAItem(
            question=f"What sound did the parmesan make?",
            answer=f"It made a {p.sound} sound that went '{sound.effect}'.",
        ),
        QAItem(
            question=f"Who gave the wise advice in the story?",
            answer=f"The helper, {helper.label}, gave the wise advice and helped the little {hero.type} choose well.",
        ),
        QAItem(
            question=f"What did the little {hero.type} learn?",
            answer=f"The little {hero.type} learned that a pleasant sound can be enjoyed best when it is handled with care.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is parmesan?",
            answer="Parmesan is a hard, salty cheese that people often grate or shave over food.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound that helps tell a story or make a scene feel lively.",
        ),
        QAItem(
            question="What does it mean to be wise?",
            answer="Being wise means making careful choices and learning from what happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/5."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} valid combinations:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
