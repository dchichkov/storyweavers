#!/usr/bin/env python3
"""
storyworlds/worlds/recover_extensive_perform_conflict_cautionary_ghost_story.py
===============================================================================

A small ghost-story world about a child performer, a cautionary haunted place,
and a conflict that is resolved by recovering a lost stage charm.

Premise:
- A young performer wants to perform an extensive ghost play in an old hall.
- A warning says the hall is not safe because the ghost in it only likes quiet.
- The child pushes forward, then the haunting grows into a conflict.
- A trusted helper reveals a lantern-charm and the performer recovers it,
  calming the ghost and changing the ending image.

This world is built for short, child-facing, classical story generation.
It uses physical meters and emotional memes, supports trace/QA/JSON/ASP, and
keeps the ASP rules inline as the declarative twin of the Python reasoner.
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
    worn_by: Optional[str] = None
    protective: bool = False
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


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Play:
    id: str
    name: str
    extensive: str
    perform: str
    caution: str
    danger: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.weather: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def bump_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def bump_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


def covered_by_charm(actor: Entity, charm: Entity) -> bool:
    return charm.protective and bool(charm.meters.get("held", 0.0) >= THRESHOLD)


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if meter(actor, "fear") < THRESHOLD:
            continue
        sig = ("haunt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bump_meme(actor, "conflict")
        out.append(f"The shadows seemed to lean closer around {actor.id}.")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if meter(actor, "tired") < THRESHOLD or meter(actor, "lost") < THRESHOLD:
            continue
        sig = ("recover", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bump_meme(actor, "hope")
        out.append(f"{actor.id} found enough breath to keep going.")
    return out


CAUSAL_RULES = [_r_haunt, _r_recover]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_conflict(world: World, actor: Entity, play: Play) -> bool:
    sim = world.copy()
    _perform(sim, sim.get(actor.id), play, narrate=False)
    return any(meme(e, "conflict") >= THRESHOLD for e in sim.characters())


def _perform(world: World, actor: Entity, play: Play, narrate: bool = True) -> None:
    if play.id not in world.setting.affords:
        raise StoryError("That place cannot host this performance.")
    world.zone = {"stage", "hall"}
    bump_meter(actor, "exertion")
    bump_meter(actor, "tired")
    bump_meme(actor, "pride")
    bump_meter(actor, play.danger)
    if play.id == "ghost_show":
        bump_meter(actor, "fear")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "careful")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved to perform."
    )


def setup(world: World, hero: Entity, helper: Entity, play: Play) -> None:
    world.say(
        f"{hero.id} had an extensive little ghost play ready: {play.extensive}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to perform {play.perform}, even though "
        f"{helper.label} had a cautionary feeling about the old hall."
    )


def warning(world: World, helper: Entity, hero: Entity, play: Play) -> None:
    world.say(
        f'"{play.caution}," {helper.id} warned. "{play.danger.capitalize()} can make a night feel cold."'
    )


def conflict_beat(world: World, hero: Entity, helper: Entity, play: Play) -> None:
    bump_meme(hero, "defiance")
    bump_meme(hero, "conflict")
    world.say(
        f"{hero.id} still stepped onto the stage and tried to perform."
    )
    world.say(
        f"Then the room went hush, and the candlelight shook with conflict."
    )
    if predict_conflict(world, hero, play):
        world.say(
            f"{helper.id} hurried closer, because the warning had been real."
        )


def recover_charm(world: World, hero: Entity, helper: Entity, charm: Charm) -> Optional[Entity]:
    charm_ent = world.add(Entity(
        id=charm.id,
        kind="thing",
        type="charm",
        label=charm.label,
        phrase=charm.phrase,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        meters={"held": 1.0},
    ))
    bump_meter(hero, "lost")
    bump_meter(hero, "tired")
    bump_meme(hero, "hope")
    world.say(
        f"{helper.id} remembered a small lantern-charm and helped {hero.id} recover it."
    )
    world.say(
        f"When the charm glowed, the room stopped feeling so hungry."
    )
    return charm_ent


def resolution(world: World, hero: Entity, helper: Entity, play: Play, charm_ent: Entity) -> None:
    bump_meme(hero, "joy")
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} performed again, this time with a steady voice and the glowing charm in hand."
    )
    world.say(
        f"The ghost did not roar anymore; it only swayed like a sleepy curtain."
    )
    world.say(
        f"At the end, {hero.id} and {helper.id} walked home with the lantern-light safe and warm."
    )


def tell(
    setting: Setting,
    play: Play,
    charm: Charm,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    world.weather = play.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "careful", "brave"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="Grandma",
        traits=["gentle", "wary"],
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        traits=["quiet", "lonely"],
    ))

    introduce(world, hero)
    setup(world, hero, helper, play)
    world.para()
    warning(world, helper, hero, play)
    conflict_beat(world, hero, helper, play)
    world.para()
    charm_ent = recover_charm(world, hero, helper, charm)
    resolution(world, hero, helper, play, charm_ent)

    world.facts.update(hero=hero, helper=helper, ghost=ghost, play=play, charm=charm, setting=setting)
    return world


SETTINGS = {
    "old_hall": Setting(place="the old hall", mood="echoing", affords={"ghost_show", "lantern_song"}),
    "attic_stage": Setting(place="the attic stage", mood="dusty", affords={"ghost_show"}),
    "moon_room": Setting(place="the moon room", mood="silver", affords={"ghost_show", "whisper_play"}),
}

PLAYS = {
    "ghost_show": Play(
        id="ghost_show",
        name="ghost show",
        extensive="there were curtains that whispered, a moon made from paper, and three tiny knocks behind the chair",
        perform="the ghost show under the old rafters",
        caution="Do not rush the ghost show when the room already feels cold",
        danger="fear",
        weather="foggy",
        tags={"ghost", "conflict", "cautionary"},
    ),
    "whisper_play": Play(
        id="whisper_play",
        name="whisper play",
        extensive="there were soft lines, a silver mask, and a slow ending that asked the audience to listen closely",
        perform="the whisper play with careful voices",
        caution="Keep your voice low in a room that remembers every sound",
        danger="echo",
        weather="misty",
        tags={"ghost", "cautionary"},
    ),
    "lantern_song": Play(
        id="lantern_song",
        name="lantern song",
        extensive="there were bright paper stars, a small lantern tune, and a brave step for each beat",
        perform="the lantern song at center stage",
        caution="A bright light can fade if nobody guards it",
        danger="fade",
        weather="windy",
        tags={"ghost", "cautionary"},
    ),
}

CHARMS = {
    "lantern_charm": Charm(
        id="lantern_charm",
        label="a little lantern charm",
        phrase="a tiny charm with a warm glow",
        covers={"hand"},
        guards={"fear", "echo"},
    ),
    "bell_charm": Charm(
        id="bell_charm",
        label="a bell charm",
        phrase="a small charm that rang like a whisper",
        covers={"hand"},
        guards={"echo"},
    ),
}

NAMES = ["Mina", "Lena", "Toby", "Noah", "Iris", "Pip", "June", "Owen"]
TRAITS = ["careful", "brave", "gentle", "bright", "curious"]


@dataclass
class StoryParams:
    place: str
    play: str
    charm: str
    name: str
    gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: recover, perform, and resolve a cautionary conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--play", choices=PLAYS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["grandmother", "grandfather"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, setting in SETTINGS.items():
        for play_id in setting.affords:
            for charm_id in CHARMS:
                if play_id == "ghost_show" and charm_id == "lantern_charm":
                    combos.append((p, play_id, charm_id))
                if play_id != "ghost_show":
                    combos.append((p, play_id, charm_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.play is None or c[1] == args.play)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid ghost-story combination matches the given options.)")
    place, play_id, charm_id = rng.choice(sorted(combos))
    play = PLAYS[play_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, play=play_id, charm=charm_id, name=name, gender=gender, helper_type=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PLAYS[params.play], CHARMS[params.charm], params.name, params.gender, params.helper_type)
    world.facts["trait"] = params.trait
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
        f'Write a short ghost story for a child about a performer who wants to recover a charm before an extensive show.',
        f"Tell a cautious story where {f['hero'].id} tries to perform {f['play'].perform} in {f['setting'].place} but must recover a helper's charm first.",
        f'Write a gentle story with conflict, a ghostly warning, and a safe ending image involving "{f["charm"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    play = f["play"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to perform {play.perform}. {play.extensive.capitalize()}.",
        ),
        QAItem(
            question=f"Why did {helper.label} give a cautionary warning?",
            answer=f"{helper.label} warned because the room felt cold and {play.danger} could make the show turn into a conflict.",
        ),
        QAItem(
            question=f"How did {hero.id} recover {charm.label}?",
            answer=f"{helper.label} helped {hero.id} recover {charm.label}, and the warm glow made the ghost feel less scary.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The conflict settled, {hero.id} performed again, and the old hall ended in a calm, lantern-lit image.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a story about a spooky person or place that feels eerie, but it can still end safely.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning so someone can avoid a mistake or stay safe.",
        ),
        QAItem(
            question="What does recover mean?",
            answer="Recover means to get something back after it was lost, or to feel better again.",
        ),
        QAItem(
            question="What does perform mean?",
            answer="Perform means to act, sing, dance, or put on a show for others.",
        ),
        QAItem(
            question="What does extensive mean?",
            answer="Extensive means something is big, long, or has many parts.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_hall", play="ghost_show", charm="lantern_charm", name="Mina", gender="girl", helper_type="grandmother", trait="careful"),
    StoryParams(place="moon_room", play="whisper_play", charm="bell_charm", name="Toby", gender="boy", helper_type="grandfather", trait="curious"),
    StoryParams(place="attic_stage", play="ghost_show", charm="lantern_charm", name="Iris", gender="girl", helper_type="grandmother", trait="brave"),
]


ASP_RULES = r"""
place(P) :- setting(P).
play(A) :- activity(A).
charm(C) :- charm_fact(C).

valid(P,A,C) :- setting(P), affords(P,A), charm_fact(C), safe_combo(P,A,C).
safe_combo(P,A,C) :- affords(P,A), charm_fact(C), compatible(A,C).

% A cautious ghost story should involve a warning-worthy performance and a charm
% that can recover the mood.
needs_warning(P,A) :- affords(P,A), ghostly(A).
requires_recovery(A,C) :- ghostly(A), recovery_charm(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, p in PLAYS.items():
        lines.append(asp.fact("activity", aid))
        if "ghost" in p.tags:
            lines.append(asp.fact("ghostly", aid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", aid, tag))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm_fact", cid))
        if "fear" in c.guards:
            lines.append(asp.fact("recovery_charm", cid))
        if "echo" in c.guards:
            lines.append(asp.fact("compatible", "whisper_play", cid))
        lines.append(asp.fact("compatible", "ghost_show", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.play} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
