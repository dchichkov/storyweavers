#!/usr/bin/env python3
"""
storyworlds/worlds/rock_n_roll_humor_dialogue_slice_of.py
========================================================

A small slice-of-life storyworld about a kid, a band practice, and a tiny
rock'n'roll problem that gets solved with humor and dialogue.

Premise:
A child wants to make a loud, fun rock'n'roll song at home. Something small gets
in the way -- a missing pick, a stubborn amp knob, a sleepy sibling, or a shy
neighbor -- and the family has to decide how to make the music work without
turning the room into a mess.

This world keeps the scale humble: one practice space, one tune, one little
tension, one practical fix. Stories are built from simulated meters and memes
and end with an image that proves what changed.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    vibe: str
    space: str
    noise_ok: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Groove:
    id: str
    label: str
    verb: str
    sound: str
    fun: str
    mess: str
    mess_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    problem: str
    fix_hint: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bedroom_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["loud"] < THRESHOLD:
            continue
        if world.place.noise_ok:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("neighbor").memes["bothered"] += 1
        out.append("__neighbor__")
    return out


def _r_missing_picks(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["frustration"] < THRESHOLD:
            continue
        sig = ("pick", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("hero").memes["focus"] += 1
        out.append("__pick__")
    return out


CAUSAL_RULES = [Rule(name="noise", apply=_r_bedroom_noise), Rule(name="pick", apply=_r_missing_picks)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(place: Place, groove: Groove, trouble: Trouble) -> bool:
    if not place.noise_ok and groove.mess_kind == "noise":
        return True
    return trouble.id in {"pick", "amp", "neighbor", "lyric"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for gid, groove in GROOVES.items():
            for tid, trouble in TROUBLES.items():
                if reasonableness_ok(place, groove, trouble):
                    combos.append((pid, gid, tid))
    return combos


@dataclass
class StoryParams:
    place: str
    groove: str
    trouble: str
    fix: str
    name: str
    name2: str
    relation: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom", vibe="cozy", space="small", noise_ok=False, tags={"home"}),
    "garage": Place(id="garage", label="the garage", vibe="open", space="wide", noise_ok=True, tags={"home"}),
    "porch": Place(id="porch", label="the porch", vibe="sunny", space="bright", noise_ok=True, tags={"home"}),
}

GROOVES = {
    "rock_riff": Groove(id="rock_riff", label="rock'n'roll riff", verb="play a rock'n'roll riff", sound="twang", fun="it made everyone grin", mess="the song got louder", mess_kind="noise", tags={"rock'n'roll", "music"}),
    "air_drums": Groove(id="air_drums", label="air-drums beat", verb="play air drums", sound="bam-bam", fun="it felt like a parade", mess="the beat got louder", mess_kind="noise", tags={"rock'n'roll", "music"}),
    "hand_clap": Groove(id="hand_clap", label="hand-clap chorus", verb="clap a chorus", sound="clap-clap", fun="it felt like a silly dance", mess="the chorus got louder", mess_kind="noise", tags={"music", "humor"}),
}

TROUBLES = {
    "pick": Trouble(id="pick", label="missing pick", problem="the guitar pick was gone", fix_hint="a spoon will not sound the same", risk="the song would stop", tags={"music"}),
    "amp": Trouble(id="amp", label="stubborn amp", problem="the amp knob stayed tiny", fix_hint="turn it with both hands", risk="the riff would stay quiet", tags={"music"}),
    "neighbor": Trouble(id="neighbor", label="sleepy neighbor", problem="the next-door neighbor was trying to nap", fix_hint="play softer or move outside", risk="the neighbor would grumble", tags={"humor"}),
    "lyric": Trouble(id="lyric", label="silly lyric", problem="the chorus line made no sense", fix_hint="change one word", risk="the song would sound wobbly", tags={"humor"}),
}

FIXES = {
    "spoon_pick": Fix(id="spoon_pick", label="a spoon", action="borrowed a spoon for a fake pick", result="the riff still worked, only a little clinkier", tags={"humor"}),
    "both_hands": Fix(id="both_hands", label="both hands", action="turned the amp knob with both hands", result="the music finally woke up", tags={"music"}),
    "move_out": Fix(id="move_out", label="the porch", action="moved the whole jam to the porch", result="the song could sing out loud without waking anyone", tags={"slice_of_life"}),
    "new_word": Fix(id="new_word", label="one new word", action="swapped one word in the chorus", result="the line became funny in the good way", tags={"humor"}),
}

NAMES = ["Maya", "Noah", "Lena", "Owen", "Ivy", "Jude", "Nina", "Theo"]
TRAITS = ["curious", "cheerful", "sly", "patient", "goofy", "earnest"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.noise_ok:
            lines.append(asp.fact("noise_ok", pid))
    for gid, g in GROOVES.items():
        lines.append(asp.fact("groove", gid))
        lines.append(asp.fact("mess_kind", gid, g.mess_kind))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,G,T) :- place(P), groove(G), trouble(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life rock'n'roll humor storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--groove", choices=GROOVES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--name2")
    ap.add_argument("--relation", choices=["friends", "siblings"], default=None)
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in NAMES if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.groove is None or c[1] == args.groove)
              and (args.trouble is None or c[2] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, groove, trouble = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    name = args.name or rng.choice(NAMES)
    name2 = args.name2 or _pick_name(rng, avoid=name)
    relation = args.relation or rng.choice(["friends", "siblings"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, groove=groove, trouble=trouble, fix=fix, name=name, name2=name2, relation=relation, trait=trait)


def tell(place: Place, groove: Groove, trouble: Trouble, fix: Fix, hero: str, sidekick: str, relation: str, trait: str) -> World:
    world = World(place)
    hero_ent = world.add(Entity(id="hero", kind="character", type="boy" if hero in {"Noah", "Owen", "Jude", "Theo"} else "girl", label=hero, attrs={"relation": relation}, tags={"hero"}))
    side_ent = world.add(Entity(id="sidekick", kind="character", type="boy" if sidekick in {"Noah", "Owen", "Jude", "Theo"} else "girl", label=sidekick, attrs={"relation": relation}, tags={"sidekick"}))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="woman", label="the neighbor", tags={"neighbor"}))
    speaker = world.add(Entity(id="speaker", kind="thing", label=groove.label, tags={"music"}))
    # initialize everything before propagation
    hero_ent.memes["joy"] = 1
    side_ent.memes["joy"] = 1
    neighbor.memes["sleepy"] = 1
    speaker.meters["loud"] = 0
    speaker.meters["frustration"] = 0
    world.facts["hero"] = hero_ent
    world.facts["sidekick"] = side_ent
    world.facts["neighbor"] = neighbor
    world.facts["groove"] = groove
    world.facts["trouble"] = trouble
    world.facts["fix"] = fix
    world.facts["relation"] = relation

    world.say(f"{hero} and {sidekick} were in {place.label}, trying to make a little rock'n'roll moment after school.")
    world.say(f'"Let\'s do {groove.verb}," {hero} said, and {sidekick} laughed. "{groove.sound}!"')

    world.para()
    if trouble.id == "neighbor":
        world.say(f"But {trouble.problem}. {sidekick} whispered, \"Maybe we should not wake the whole street.\"")
        world.say(f'{hero} grinned. "{fix.action}, maybe?"')
        side_ent.meters["frustration"] += 1
        propagate(world, narrate=False)
        world.say(f'"That is one way to have a quiet anthem," {sidekick} said.')
        world.say(f'They {fix.action}, and {fix.result}.')
    elif trouble.id == "pick":
        world.say(f"But {trouble.problem}. {hero} searched the couch, the floor, and even a cereal bowl.")
        world.say(f'"A spoon will do in a pinch," {sidekick} said. "{fix.action}."')
        hero_ent.meters["frustration"] += 1
        propagate(world, narrate=False)
        world.say(f'They {fix.action}, and {fix.result}.')
    elif trouble.id == "amp":
        world.say(f"But {trouble.problem}. {sidekick} leaned close and said, \"It is not broken. It is just dramatic.\"")
        world.say(f'"Then let us be dramatic too," {hero} said. "{fix.action}."')
        hero_ent.meters["frustration"] += 1
        propagate(world, narrate=False)
        world.say(f'They {fix.action}, and {fix.result}.')
    else:
        world.say(f"But {trouble.problem}. {hero} frowned at the chorus line.")
        world.say(f'"{fix.action}," {sidekick} said. \"A song can be silly without falling apart.\"')
        hero_ent.meters["frustration"] += 1
        propagate(world, narrate=False)
        world.say(f'They {fix.action}, and {fix.result}.')
    world.para()
    world.say(f"By the end, {hero} and {sidekick} were smiling over a tiny, tidy rock'n'roll tune that fit the day just right.")
    world.facts["place"] = place
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a young child about {f["hero"].label} and {f["sidekick"].label} making rock\'n\'roll music at {f["place"].label}.',
        f"Tell a humorous dialogue story where {f['hero'].label} wants a {f['groove'].label}, but a small problem gets in the way and a simple fix helps.",
        f'Write a gentle everyday story with humor, dialogue, and the phrase "rock\'n\'roll" that ends with the children smiling after practice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, groove, trouble, fix = f["hero"], f["sidekick"], f["groove"], f["trouble"], f["fix"]
    return [
        QAItem(question=f"What were {hero.label} and {sidekick.label} trying to do?", answer=f"They were trying to make a little rock'n'roll tune together."),
        QAItem(question=f"What problem got in the way?", answer=f"{trouble.problem.capitalize()}."),
        QAItem(question=f"How did they solve it?", answer=f"They {fix.action}, and that let the music keep going."),
        QAItem(question=f"How did {hero.label} feel at the end?", answer=f"{hero.label} felt happy and relieved because the song worked out."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is rock'n'roll?", answer="Rock'n'roll is lively music with a strong beat, guitars, and lots of energy."),
        QAItem(question="Why do people joke during band practice?", answer="People joke during band practice because music can be fun, and a little laughter helps everyone relax and keep trying."),
        QAItem(question="What is a pick for?", answer="A guitar pick helps a person strum or pluck the strings more clearly."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", groove="rock_riff", trouble="neighbor", fix="move_out", name="Maya", name2="Noah", relation="siblings", trait="goofy"),
    StoryParams(place="garage", groove="air_drums", trouble="amp", fix="both_hands", name="Ivy", name2="Jude", relation="friends", trait="earnest"),
    StoryParams(place="porch", groove="hand_clap", trouble="lyric", fix="new_word", name="Lena", name2="Theo", relation="siblings", trait="sly"),
    StoryParams(place="garage", groove="rock_riff", trouble="pick", fix="spoon_pick", name="Nina", name2="Owen", relation="friends", trait="patient"),
]


def generate(params: StoryParams) -> StorySample:
    sample_world = tell(PLACES[params.place], GROOVES[params.groove], TROUBLES[params.trouble], FIXES[params.fix], params.name, params.name2, params.relation, params.trait)
    return StorySample(
        params=params,
        story=sample_world.render(),
        prompts=generation_prompts(sample_world),
        story_qa=story_qa(sample_world),
        world_qa=world_knowledge_qa(sample_world),
        world=sample_world,
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


def resolve_validated(params: StoryParams) -> StoryParams:
    if params.fix not in FIXES:
        raise StoryError("Invalid fix.")
    if params.place not in PLACES or params.groove not in GROOVES or params.trouble not in TROUBLES:
        raise StoryError("Invalid selected values.")
    return params


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid_combos().")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
        return 1
    print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        print("ERROR: smoke test produced empty story.")
        return 1
    print("OK: smoke test story generation works.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.name2} ({p.place}, {p.groove}, {p.trouble})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
