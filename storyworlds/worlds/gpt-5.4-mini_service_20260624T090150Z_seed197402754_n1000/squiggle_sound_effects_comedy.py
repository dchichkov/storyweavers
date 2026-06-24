#!/usr/bin/env python3
"""
Story world: squiggle sound effects comedy.

A small, state-driven comedy domain about a child who wants to perform sound
effects with a squiggle toy, a noisy problem, and a funny compromise.
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
    worn_by: Optional[str] = None
    plural: bool = False
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
    place: str = "the living room"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    consequence: str
    tag: str


@dataclass
class Prop:
    label: str
    phrase: str
    type: str
    suitable_for: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gizmo:
    id: str
    label: str
    prep: str
    tail: str
    quiets: set[str] = field(default_factory=set)
    boosts: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "living_room": Setting(place="the living room", indoors=True, affords={"squiggle"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"squiggle"}),
    "hall": Setting(place="the hallway", indoors=True, affords={"squiggle"}),
}

ACTIONS = {
    "squiggle": Act(
        id="squiggle",
        verb="make squiggle sound effects",
        gerund="making squiggle sound effects",
        rush="grab the squiggle toy and go bzzzt-bzzzt",
        sound="bzzzt-bzzzt",
        consequence="the room turned into a giggle machine",
        tag="squiggle",
    ),
    "whistle": Act(
        id="whistle",
        verb="whistle a silly tune",
        gerund="whistling a silly tune",
        rush="pucker up and toot-toot-toot",
        sound="toot-toot-toot",
        consequence="the tune bounced off the walls",
        tag="sound",
    ),
    "drum": Act(
        id="drum",
        verb="drum on a box",
        gerund="drumming on a box",
        rush="tap-tap on the cardboard",
        sound="tap-tap-tap",
        consequence="the beat bounced like a funny ball",
        tag="sound",
    ),
}

PROPS = {
    "squiggle_toy": Prop(
        label="squiggle toy",
        phrase="a bright squiggle toy with a bendy tail",
        type="toy",
    ),
    "snack": Prop(
        label="snack bowl",
        phrase="a small bowl of crackers",
        type="snack",
    ),
    "hat": Prop(
        label="party hat",
        phrase="a wobbly party hat",
        type="hat",
    ),
}

GIZMOS = [
    Gizmo(
        id="whisper_muffler",
        label="a whisper muffler",
        prep="put on a whisper muffler first",
        tail="put on the whisper muffler",
        quiets={"whistle"},
    ),
    Gizmo(
        id="soft_box",
        label="a soft box",
        prep="switch to a soft box",
        tail="switched to the soft box",
        quiets={"drum"},
    ),
    Gizmo(
        id="stage_lights",
        label="stage lights",
        prep="turn on the stage lights and make it a show",
        tail="turned on the stage lights",
        boosts={"squiggle", "whistle", "drum"},
    ),
]

GIRLS = ["Mia", "Luna", "Zoe", "Ava", "Ivy", "Nora"]
BOYS = ["Max", "Leo", "Finn", "Eli", "Theo", "Sam"]
TRAITS = ["playful", "curious", "silly", "cheerful", "wiggly", "busy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prop_id in PROPS:
                combos.append((place, act_id, prop_id))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    prop: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def _narrate_intro(world: World, hero: Entity, prop: Entity, act: Act) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in ['playful','curious','silly','cheerful','wiggly','busy'])} {hero.type} "
        f"who loved {act.gerund} with {prop.label}."
    )
    world.say(
        f"{hero.id} could make {act.sound} noises and then giggle at the echo."
    )


def _predict_noise(world: World, hero: Entity, act: Act, prop: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["noise"] = 1
    return {"too_loud": act.id == "drum" or act.id == "whistle", "messy": False}


def _do_act(world: World, hero: Entity, act: Act) -> None:
    hero.meters[act.id] = hero.meters.get(act.id, 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    if act.id == "drum":
        hero.memes["noise"] = hero.memes.get("noise", 0) + 1


def _offer_fix(world: World, act: Act) -> Optional[Gizmo]:
    for g in GIZMOS:
        if act.id in g.quiets or act.id in g.boosts:
            return g
    return None


def tell(setting: Setting, act: Act, prop_cfg: Prop, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    prop = world.add(Entity(id="prop", type=prop_cfg.type, label=prop_cfg.label, phrase=prop_cfg.phrase, owner=hero.id))
    prop.worn_by = hero.id

    _narrate_intro(world, hero, prop, act)
    world.para()
    world.say(f"One afternoon, {hero.id} was in {setting.place} and wanted to {act.verb}.")
    world.say(f"{hero.id} leaned in and went {act.sound}, which made {act.consequence}.")
    _do_act(world, hero, act)

    if act.id == "drum":
        world.say("Then the snack bowl shivered like it had heard a joke.")
    elif act.id == "whistle":
        world.say("The whistle bounced off the cabinets and tickled everyone's ears.")
    else:
        world.say("The squiggle toy wriggled like a tiny noodle with a mission.")

    world.para()
    pred = _predict_noise(world, hero, act, prop)
    world.say(f"That made the grown-up look over with a careful face.")

    fix = _offer_fix(world, act)
    if fix:
        world.say(
            f'"How about we {fix.prep}?" the grown-up said. '
            f"{hero.id} blinked, then smiled because that sounded even funnier."
        )
        hero.memes["joy"] += 1
        if act.id == "drum":
            world.say(f"They {fix.tail}, and the box got a softer beat.")
        elif act.id == "whistle":
            world.say(f"They {fix.tail}, and the tune turned into a tiny, polite toot.")
        else:
            world.say(f"They {fix.tail}, and the squiggle sound got even wobblier.")
        world.say(
            f"At the end, {hero.id} was still {act.gerund}, and everyone was laughing."
        )
    else:
        world.say(
            f"Still, {hero.id} tried again more gently, and the silly noise calmed down all by itself."
        )
        world.say(f"The room stayed cheerful, and the joke landed softly.")

    world.facts.update(hero=hero, prop=prop, act=act, setting=setting, fix=fix, predicted=pred)
    return world


KNOWLEDGE = {
    "squiggle": [
        (
            "What is a squiggle?",
            "A squiggle is a twisty, wiggly line or shape that bends back and forth like a doodle having fun.",
        )
    ],
    "sound": [
        (
            "What are sound effects?",
            "Sound effects are special noises made to match a story, a game, or a funny action.",
        )
    ],
    "bzzzt": [
        (
            "Why do buzzing sounds seem funny in stories?",
            "Buzzing sounds can seem funny because they are wiggly, bouncy noises that feel a little silly.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prop = f["hero"], f["act"], f["prop"]
    return [
        f'Write a short comedy story for a child about "{act.tag}" and the word "squiggle".',
        f"Tell a funny story where {hero.id} wants to {act.verb} with {prop.label} and makes everybody laugh.",
        f"Write a simple story about sound effects, a squiggle toy, and a grown-up who finds a silly fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, act, prop = f["hero"], f["act"], f["prop"]
    fix = f.get("fix")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} with {prop.label}.",
        ),
        QAItem(
            question=f"What sound did {hero.id} make when trying to be funny?",
            answer=f"{hero.id} made {act.sound} sound effects.",
        ),
        QAItem(
            question=f"Why did the grown-up look over with a careful face?",
            answer=f"Because the noise got big and silly, and the room was getting extra wiggly.",
        ),
    ]
    if fix:
        qa.append(
            QAItem(
                question=f"What did they use to make the noisy joke gentler?",
                answer=f"They used {fix.label} so the sound could stay funny without getting too loud.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["act"].tag, "sound", "squiggle"}
    out: list[QAItem] = []
    for tag in ["squiggle", "sound", "bzzzt"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="living_room", action="squiggle", prop="squiggle_toy", name="Mia", gender="girl", trait="playful"),
    StoryParams(place="kitchen", action="whistle", prop="hat", name="Max", gender="boy", trait="silly"),
    StoryParams(place="hall", action="drum", prop="snack", name="Luna", gender="girl", trait="cheerful"),
]


ASP_RULES = r"""
place(P) :- setting(P).
act(A) :- action(A).
prop(R) :- prop(R).
valid(P,A,R) :- setting(P), affords(P,A), prop(R).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about squiggle sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS := ["playful", "curious", "silly", "cheerful", "wiggly", "busy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRLS if gender == "girl" else BOYS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prop=prop, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PROPS[params.prop], params.name, params.gender, params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
