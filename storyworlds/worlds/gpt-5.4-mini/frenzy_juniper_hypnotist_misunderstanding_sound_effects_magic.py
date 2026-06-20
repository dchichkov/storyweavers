#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frenzy_juniper_hypnotist_misunderstanding_sound_effects_magic.py
==============================================================================================

A standalone storyworld about a spooky-but-safe ghost-story misunderstanding:
a child hears strange sound effects in a juniper grove, mistakes a hypnotist's
magic show for something eerie, panics into a frenzy, and then learns the noises
are only a trick made with props, voice, and sparkle.

The world is small on purpose: one setting, a few typed entities, physical meters
and emotional memes, a forward causal turn, a calm reveal, and a child-facing
ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/frenzy_juniper_hypnotist_misunderstanding_sound_effects_magic.py
    python storyworlds/worlds/gpt-5.4-mini/frenzy_juniper_hypnotist_misunderstanding_sound_effects_magic.py --trace
    python storyworlds/worlds/gpt-5.4-mini/frenzy_juniper_hypnotist_misunderstanding_sound_effects_magic.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/frenzy_juniper_hypnotist_misunderstanding_sound_effects_magic.py --all
    python storyworlds/worlds/gpt-5.4-mini/frenzy_juniper_hypnotist_misunderstanding_sound_effects_magic.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    props: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    dark_spot: str
    quiet: str


@dataclass
class Trick:
    id: str
    label: str
    props: str
    sound: str
    glow: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    fear_label: str
    story_guess: str
    correction: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    if kid.memes["unease"] >= THRESHOLD and ("fear", "child") not in world.fired:
        world.fired.add(("fear", "child"))
        kid.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_frenzy(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    if kid.memes["fear"] >= THRESHOLD and kid.meters["frenzy"] < THRESHOLD:
        sig = ("frenzy", "child")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        kid.meters["frenzy"] += 1
        kid.memes["panic"] += 1
        out.append("__frenzy__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    guide = world.get("hypnotist")
    if guide.meters["reveal"] >= THRESHOLD and kid.memes["panic"] >= THRESHOLD:
        sig = ("calm", "child")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        kid.memes["calm"] += 1
        kid.memes["fear"] = 0.0
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("frenzy", _r_frenzy), Rule("calm", _r_calm)]


def hazard_reasonable(trick: Trick, m: Misunderstanding) -> bool:
    return "sound" in trick.tags and "magic" in trick.tags and "misunderstanding" in m.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in TRICKS:
            for mid in MISUNDERSTANDINGS:
                if hazard_reasonable(TRICKS[tid], MISUNDERSTANDINGS[mid]):
                    combos.append((sid, tid, mid))
    return combos


def predict(world: World, child: Entity, trick: Trick, misunderstanding: Misunderstanding) -> dict:
    sim = world.copy()
    _do_scene(sim, sim.get("child"), sim.get("hypnotist"), trick, misunderstanding, narrate=False)
    return {
        "frenzy": sim.get("child").meters["frenzy"] >= THRESHOLD,
        "calm": sim.get("child").memes["calm"] >= THRESHOLD,
    }


def _do_scene(world: World, child: Entity, hypnotist: Entity, trick: Trick,
              misunderstanding: Misunderstanding, narrate: bool = True) -> None:
    child.memes["unease"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)
    world.say(f"The evening air hung over {world.setting.place}, quiet and cold.")
    world.say(
        f"{child.id} wandered beneath the juniper branches, where the needles made "
        f"shadowy curtains and the dark looked deeper than it was."
    )
    world.say(
        f"Then {hypnotist.id} stepped into the lantern glow with {trick.props}. "
        f'{hypnotist.id} whispered, "{trick.sound}" and let the little {trick.glow} '
        f"flicker at the edge of the path."
    )
    world.say(
        f"{child.id}'s heart jumped. {child.id} thought the whisper was a ghostly "
        f"{misunderstanding.story_guess}, and the thought sent {child.id} into a "
        f"frenzy."
    )
    child.memes["unease"] += 1
    propagate(world, narrate=narrate)
    world.say(
        f"{child.id} backed into the soft needles, breathing fast, while the night "
        f"felt full of strange magic."
    )


def reveal(world: World, child: Entity, hypnotist: Entity, trick: Trick,
           misunderstanding: Misunderstanding) -> None:
    hypnotist.meters["reveal"] += 1
    child.meters["frenzy"] = 0.0
    world.say(
        f"Then {hypnotist.id} smiled and lifted the {trick.label}. "
        f"It was only a trick, a gentle piece of magic made for fun."
    )
    world.say(
        f"{hypnotist.id} showed how the {trick.sound.lower()} came from a tiny speaker "
        f"and how the {trick.glow} came from a lantern, not a spell."
    )
    world.say(
        f"{child.id} blinked, then let out a shaky laugh. The spooky guess had been "
        f"a misunderstanding all along."
    )
    propagate(world, narrate=False)
    world.say(
        f"The juniper branches still swayed in the wind, but now they looked like "
        f"ordinary branches instead of a haunted doorway."
    )


def end_image(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} stood beside {world.get('hypnotist').id} under the juniper tree, "
        f"holding a small lantern and smiling at the harmless shadows."
    )
    world.say(
        f"The night was still dark, but it was no longer frightening; it was just a "
        f"quiet place for a little magic trick and a child who had learned the truth."
    )


def tell(setting: Setting, trick: Trick, misunderstanding: Misunderstanding,
         child_name: str = "Juniper", child_gender: str = "girl",
         hypnotist_name: str = "Aster", hypnotist_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child"))
    hypnotist = world.add(Entity(id=hypnotist_name, kind="character",
                                 type=hypnotist_gender, role="hypnotist"))
    world.add(Entity(id="juniper_tree", kind="thing", type="tree",
                     label="juniper branches"))
    child.memes["unease"] = 1.0

    world.say(
        f"In {setting.place}, the juniper trees made a silver hush around the path, "
        f"and {setting.mood} shadows gathered where the lantern light stopped."
    )
    world.say(
        f"{child.id} loved the whispery grove, but tonight the quiet spot near "
        f"{setting.dark_spot} felt strange."
    )
    world.para()
    _do_scene(world, child, hypnotist, trick, misunderstanding)
    world.para()
    reveal(world, child, hypnotist, trick, misunderstanding)
    world.para()
    end_image(world, child)
    world.facts.update(
        setting=setting,
        trick=trick,
        misunderstanding=misunderstanding,
        child=child,
        hypnotist=hypnotist,
        outcome="calm" if child.memes["calm"] >= THRESHOLD else "frenzy",
    )
    return world


SETTINGS = {
    "grove": Setting("grove", "the juniper grove", "eerie", "the old stone gate", "soft"),
    "porch": Setting("porch", "the porch", "blue-black", "the rain barrel", "still"),
    "garden": Setting("garden", "the moonlit garden", "hushed", "the hedge tunnel", "deep"),
}

TRICKS = {
    "bells": Trick("bells", "bell box", "a velvet box and a silver wand", "listen to the bells", "sparkle",
                   "the bells came from a hidden charm, not a spirit", {"sound", "magic"}),
    "rattle": Trick("rattle", "rattle charm", "a painted cane and a silk scarf", "hear the rattle-rattle", "glimmer",
                    "the rattling came from loose beads", {"sound", "magic"}),
    "whistle": Trick("whistle", "whistle ribbon", "a ribbon stick and a mirror coin", "whooo, whooo", "twinkle",
                     "the whistle came from the ribbon, not a ghost", {"sound", "magic"}),
}

MISUNDERSTANDINGS = {
    "ghost": Misunderstanding("ghost", "ghost", "ghost was calling from the dark", "it was only stage magic", {"misunderstanding"}),
    "haunt": Misunderstanding("haunt", "haunt", "haunted helper was hiding nearby", "it was only a playful show", {"misunderstanding"}),
    "spell": Misunderstanding("spell", "spell", "spell had trapped the path", "it was only a trick with props", {"misunderstanding"}),
}

GIRL_NAMES = ["Juniper", "Mina", "Lila", "Nora", "Elsie"]
BOY_NAMES = ["Theo", "Finn", "Milo", "Owen", "Ezra"]

CURATED = [
    StoryParams("grove", "bells", "ghost", "Juniper", "girl", "Aster", "woman"),
    StoryParams("porch", "rattle", "haunt", "Milo", "boy", "Poppy", "woman"),
    StoryParams("garden", "whistle", "spell", "Nora", "girl", "Iris", "woman"),
]


@dataclass
class StoryParams:
    setting: str
    trick: str
    misunderstanding: str
    child_name: str
    child_gender: str
    hypnotist_name: str
    hypnotist_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "juniper": [("What is a juniper tree?",
                 "A juniper tree is a tree with small sharp needles and blue berries. Its branches can make a place feel quiet and shady.")],
    "hypnotist": [("What is a hypnotist?",
                   "A hypnotist is a performer who uses voice, timing, and props to make a show feel mysterious. In a story, a hypnotist can seem spooky, but it is usually just a trick.")],
    "sound": [("What is a sound effect?",
               "A sound effect is a noise made to help a story or show feel exciting. It is often created with a speaker, a tool, or a person's voice.")],
    "magic": [("What is stage magic?",
               "Stage magic is a show with clever tricks that looks mysterious. The trick can surprise people even though nothing spooky is really happening.")],
    "misunderstanding": [("What is a misunderstanding?",
                          "A misunderstanding happens when someone guesses the wrong thing. When they learn the truth, the scary idea often goes away.")],
    "frenzy": [("What does frenzy mean?",
                "Frenzy means a burst of wild, panicky energy. A frightened child might move fast, breathe hard, and feel out of control for a moment.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story-style tale for a young child that includes the words '
        f'"frenzy", "{f["setting"].place.split()[-1]}", and "hypnotist".',
        f"Tell a spooky-sounding story where {f['child'].id} hears {f['trick'].sound} "
        f"in the juniper grove and thinks it means a ghost, but the hypnotist reveals "
        f"the truth.",
        f'Write a gentle story about a misunderstanding, sound effects, and magic, '
        f'ending with the dark place feeling safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    hyp = f["hypnotist"]
    trick = f["trick"]
    m = f["misunderstanding"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {hyp.id}. {child.id} is the child who gets scared, and {hyp.id} is the hypnotist who helps explain the trick.",
        ),
        QAItem(
            question="Why did the child go into a frenzy?",
            answer=f"{child.id} heard {trick.sound} in the dark juniper grove and guessed that {m.story_guess}. That wrong guess made the moment feel spooky, so {child.id} panicked for a little while.",
        ),
        QAItem(
            question="How was the scary idea fixed?",
            answer=f"{hyp.id} showed that the noise and glow came from {trick.props}. Once the child saw it was only a trick, the misunderstanding faded and the fear went away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trick"].tags) | set(world.facts["misunderstanding"].tags) | {"juniper", "hypnotist"}
    out: list[QAItem] = []
    for key in ["juniper", "hypnotist", "sound", "magic", "misunderstanding", "frenzy"]:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sound_effect(T) :- trick(T), tag(T, sound).
magic_trick(T) :- trick(T), tag(T, magic).
misunderstanding(M) :- misunderstanding_cfg(M), tag(M, misunderstanding).
reasonable(S, T, M) :- setting(S), sound_effect(T), magic_trick(T), misunderstanding(M).
outcome(calm) :- reveal_done, not panic_only.
outcome(frenzy) :- panic_only.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding_cfg", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        rc = 1
    else:
        print(f"OK: ASP and Python combos match ({len(valid_combos())} combos).")
    # smoke test on a curated default generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: generation smoke test failed: {exc}")
        return 1
    print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Spooky small storyworld with a hypnotist, sound effects, and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.trick is None or c[1] == args.trick)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trick, misunderstanding = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        trick=trick,
        misunderstanding=misunderstanding,
        child_name=args.__dict__.get("child_name") or rng.choice(GIRL_NAMES + BOY_NAMES),
        child_gender=rng.choice(["girl", "boy"]),
        hypnotist_name=args.__dict__.get("hypnotist_name") or rng.choice(["Aster", "Iris", "Poppy", "Rowan"]),
        hypnotist_gender="woman",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TRICKS[params.trick], MISUNDERSTANDINGS[params.misunderstanding],
                 params.child_name, params.child_gender, params.hypnotist_name, params.hypnotist_gender)
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
        print(asp_program(show="#show reasonable/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        if len(samples) > 1 and not args.all:
            print(f"### variant {i + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.child_name} / {p.setting} / {p.trick} / {p.misunderstanding}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
