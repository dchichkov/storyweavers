#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stab_improve_swords_cautionary_sharing_nursery_rhyme.py
======================================================================================

A tiny nursery-rhyme storyworld about two children, a pair of toy swords, and a
sharing lesson: one child wants to stab the paper knight, but the other child
cautions them, and they improve the game by sharing the swords and fencing
safely with a soft paper target.

The domain is small and state-driven:
- physical meters track things like sharpness, damaged paper, and safety;
- emotional memes track worry, pride, delight, and trust;
- a simple forward rule engine turns a risky play into a safer shared game.

The generated stories keep close to a nursery rhyme feel: short, concrete,
repetitive, and child-facing.

Run:
    python storyworlds/worlds/gpt-5.4-mini/stab_improve_swords_cautionary_sharing_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/stab_improve_swords_cautionary_sharing_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4-mini/stab_improve_swords_cautionary_sharing_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)
    sharp: bool = False
    toy: bool = False
    shareable: bool = False
    breakable: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    rhyme: str
    props: str


@dataclass
class ToySword:
    id: str
    label: str
    phrase: str
    sparkle: str
    shareable: bool = True
    sharp: bool = False


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    breakable: bool = True


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    sword: str
    target: str
    cautioner: str = "Nora"
    cautioner_gender: str = "girl"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        rhyme="The room was round and soft with rugs",
        props="A teddy sat by blocks and mugs.",
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        rhyme="The floor was bright with paint and strings",
        props="A toy box held their little things.",
    ),
    "garden_nook": Setting(
        id="garden_nook",
        place="the garden nook",
        rhyme="The little nook was green and neat",
        props="A bench stood close beside the street.",
    ),
}

SWORDS = {
    "tin_sword": ToySword(
        id="tin_sword",
        label="tin swords",
        phrase="two tin swords with silver paint",
        sparkle="They flashed and sparkled, neat and quaint.",
        shareable=True,
        sharp=False,
    ),
    "wood_sword": ToySword(
        id="wood_sword",
        label="wooden swords",
        phrase="two wooden swords with ribboned hilts",
        sparkle="They tapped like clocks on cozy quilts.",
        shareable=True,
        sharp=False,
    ),
    "card_sword": ToySword(
        id="card_sword",
        label="cardboard swords",
        phrase="two cardboard swords from boxes cut",
        sparkle="They made a swish, a swoop, a strut.",
        shareable=True,
        sharp=False,
    ),
}

TARGETS = {
    "paper_knight": Target(
        id="paper_knight",
        label="paper knight",
        phrase="a little paper knight",
        breakable=True,
    ),
    "straw_castle": Target(
        id="straw_castle",
        label="straw castle",
        phrase="a tiny straw castle",
        breakable=True,
    ),
    "pillow_king": Target(
        id="pillow_king",
        label="pillow king",
        phrase="a soft pillow king",
        breakable=False,
    ),
}

HERO_NAMES = ["Mia", "Toby", "Lena", "Owen", "Ruby", "Finn", "Pip", "Lily"]
FRIEND_NAMES = ["Ben", "Penny", "Max", "Ada", "Jules", "Milo", "Zara", "Kit"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for sw in SWORDS:
            for tg in TARGETS:
                out.append((s, sw, tg))
    return out


def hazard_at_risk(sword: ToySword, target: Target) -> bool:
    return sword.sharp and target.breakable


def reasonableness_gate(sword: ToySword, target: Target) -> bool:
    return sword.shareable and target.breakable


def cannot_generate(sword: ToySword, target: Target) -> str:
    return f"(No story: {sword.label} are toys, but {target.phrase} is not a good target for a cautionary sharing tale.)"


def initial_world() -> World:
    return World()


def predict_damage(world: World, sword_id: str, target_id: str) -> dict:
    sim = world.copy()
    _stab_attempt(sim, sim.get(sword_id), sim.get(target_id), narrate=False)
    return {
        "damage": sim.get(target_id).meters.get("torn", 0.0),
        "fear": sim.get("hero").memes.get("worry", 0.0),
    }


def _stab_attempt(world: World, sword: Entity, target: Entity, narrate: bool = True) -> None:
    target.meters["torn"] = target.meters.get("torn", 0.0) + 1
    world.get("hero").memes["worry"] = world.get("hero").memes.get("worry", 0.0) + 1
    world.get("friend").memes["worry"] = world.get("friend").memes.get("worry", 0.0) + 1
    if narrate:
        world.say(f"One child gave a jab and tried to stab {target.label_word}, and the paper sighed and split a bit.")


def tell(setting: Setting, sword: ToySword, target: Target, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, cautioner_name: str, cautioner_gender: str) -> World:
    world = initial_world()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=["curious"], meters={}, memes={}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=["kind"], meters={}, memes={}))
    cautioner = world.add(Entity(id="cautioner", kind="character", type=cautioner_gender, label=cautioner_name, role="cautioner", traits=["careful"], meters={}, memes={}))
    sw = world.add(Entity(id=sword.id, kind="thing", type="toy", label=sword.label, sharp=sword.sharp, toy=True, shareable=sword.shareable))
    tg = world.add(Entity(id=target.id, kind="thing", type="target", label=target.label, breakable=target.breakable))
    world.facts.update(setting=setting, sword=sword, target=target, hero=hero, friend=friend, cautioner=cautioner, sword_ent=sw, target_ent=tg)

    hero.memes["want"] = 1
    friend.memes["trust"] = 1
    cautioner.memes["care"] = 1

    world.say(f"Near {setting.place}, the day was light and the children played.")
    world.say(f"{setting.rhyme} {setting.props}")
    world.say(f"{hero_name} and {friend_name} found {sword.phrase}. {sword.sparkle}")
    world.para()

    world.say(f"They wanted to play knightly games with {target.phrase}.")
    world.say(f"But {cautioner_name} lifted a hand and said, \"No, no, no; do not stab the pretty show.\"")

    if hazard_at_risk(sword, target):
        world.say("The pointed play was too sharp for a little show, and the paper would surely hurt and go.")
    else:
        world.say("The game was not meant for pokes or tears; a softer game would save their cheers.")

    if reasonableness_gate(sword, target):
        world.say(f"{hero_name} paused and listened well.")
        world.say(f"{friend_name} shared the swords, one by one, and that made the game much kinder and fun.")
        target.meters["safe_play"] = 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
        world.para()
        world.say(f"They improved the game with sharing hands: one held a sword, the other made plans.")
        world.say(f"Then they tapped the air and bowed with grace, while {target.phrase} stayed whole in its place.")
    else:
        _stab_attempt(world, hero, tg, narrate=True)
        world.para()
        world.say(f"{cautioner_name} frowned and said the game must mend; a rough little jab would not make a friend.")
        world.say(f"They set the swords aside and shared a soft game instead, with no more pokes at the paper bed.")

    world.facts["outcome"] = "shared"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "stab", "improve", and "swords".',
        f"Tell a cautionary sharing story where {f['hero'].label_word} and {f['friend'].label_word} want to play with swords, but a careful child helps them improve the game.",
        f"Write a small child-facing rhyme about toy swords, one wrong poke, and a better shared game instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    cautioner: Entity = f["cautioner"]
    sword: ToySword = f["sword"]
    target: Target = f["target"]
    return [
        ("What did the children find?", f"They found {sword.phrase}. It made them eager to play, but it was meant for careful toy play, not a real poke."),
        ("Why did the cautioner speak up?", f"{cautioner.label_word} saw that trying to stab {target.label} would hurt the paper show. The warning helped them choose a safer game."),
        ("What did they do instead?", f"They shared the swords and improved the game together. Each child took turns, so the play stayed friendly and safe."),
        ("How did the story end?", f"It ended with the children playing kindly and the {target.label} still whole. The better game came from sharing, not from a sharp poke."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to improve something?", "To improve something means to make it better. You can improve a game by making it safer, kinder, or more fun."),
        ("Why should children share toys?", "Sharing helps everyone take turns and feel included. It can also stop fights and make playtime happier."),
        ("Why is it wrong to stab things in play?", "Stabbing can hurt people or break things, even if the tool looks like a toy. Safe play keeps hands, faces, and toys from getting damaged."),
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.sharp:
            bits.append("sharp")
        if e.shareable:
            bits.append("shareable")
        if e.breakable:
            bits.append("breakable")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme cautionary sharing storyworld with toy swords.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sword", choices=SWORDS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.sword is None or c[1] == args.sword)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sword, target = rng.choice(sorted(combos))
    hero = rng.choice(HERO_NAMES)
    friend = rng.choice([n for n in FRIEND_NAMES if n != hero])
    cautioner = rng.choice([n for n in sorted(set(HERO_NAMES + FRIEND_NAMES)) if n not in {hero, friend}])
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_gender=rng.choice(["girl", "boy"]),
        friend=friend,
        friend_gender=rng.choice(["girl", "boy"]),
        sword=sword,
        target=target,
        cautioner=cautioner,
        cautioner_gender=rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.sword not in SWORDS or params.target not in TARGETS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        SWORDS[params.sword],
        TARGETS[params.target],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.cautioner,
        params.cautioner_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
valid(S, W, T) :- setting(S), sword(W), target(T), shareable(W), breakable(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    parts = []
    for s in SETTINGS:
        parts.append(asp.fact("setting", s))
    for w in SWORDS:
        parts.append(asp.fact("sword", w))
        parts.append(asp.fact("shareable", w))
    for t in TARGETS:
        parts.append(asp.fact("target", t))
        parts.append(asp.fact("breakable", t))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, sword=None, target=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"FAIL: smoke test failed: {exc}")
        return 1
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, w, t in combos:
            print(f"  {s:12} {w:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="nursery", hero="Mia", hero_gender="girl", friend="Ben", friend_gender="boy", sword="tin_sword", target="paper_knight", cautioner="Nora", cautioner_gender="girl"),
            StoryParams(setting="playroom", hero="Toby", hero_gender="boy", friend="Ada", friend_gender="girl", sword="wood_sword", target="straw_castle", cautioner="Penny", cautioner_gender="girl"),
            StoryParams(setting="garden_nook", hero="Ruby", hero_gender="girl", friend="Kit", friend_gender="boy", sword="card_sword", target="pillow_king", cautioner="Lily", cautioner_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
