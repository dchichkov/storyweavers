#!/usr/bin/env python3
"""
storyworlds/worlds/shake_dim_conflict_curiosity_fable.py
=======================================================

A small fable-style story world about curiosity, conflict, and a dimming
lantern that should not be shaken.

Premise:
- In a little orchard after dusk, a curious child-animal wants to shake a
  lantern to see what happens.
- The lantern is meant to stay steady; shaking it makes the light dim.
- A worried friend warns that the path will go dark.
- The curious one tries anyway, causing conflict.
- A wiser compromise appears: use the lantern gently, or use a mirror/chime
  trick that reveals the same wonder without ruining the light.

This world is designed as a compact, constraint-checked fable:
- only sensible story combinations are allowed,
- emotional state drives the prose,
- physical state matters (light level, shaken state, path safety),
- the ending image proves the change.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"   # "character" | "thing"
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

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
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
    mood: str = ""


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = False


@dataclass
class Situation:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    dimming: float
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    situation: str
    object: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c == "_") or "story"


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"shake-dim", "listen", "peek"}, mood="dusk"),
    "garden": Setting(place="the garden", affords={"shake-dim", "listen", "peek"}, mood="evening"),
    "hill": Setting(place="the hill", affords={"shake-dim", "listen", "peek"}, mood="twilight"),
    "lantern_room": Setting(place="the lantern room", affords={"peek", "listen"}, mood="soft lamplight"),
}

SITUATIONS = {
    "shake-dim": Situation(
        id="shake-dim",
        verb="shake the lantern",
        gerund="shaking the lantern",
        rush="grab the lantern and shake it hard",
        effect="dimming",
        dimming=1.0,
        keyword="shake-dim",
        tags={"shake-dim", "curiosity", "light", "lantern"},
    ),
    "peek": Situation(
        id="peek",
        verb="peek inside the lantern",
        gerund="peeking inside the lantern",
        rush="lean in and peek too close",
        effect="wobbling",
        dimming=0.5,
        keyword="peek",
        tags={"curiosity", "lantern"},
    ),
    "listen": Situation(
        id="listen",
        verb="listen to the lantern hum",
        gerund="listening to the lantern hum",
        rush="hold the lantern up to the ear",
        effect="steadying",
        dimming=0.0,
        keyword="listen",
        tags={"curiosity", "calm", "lantern"},
    ),
}

OBJECTS = {
    "lantern": ObjectConfig(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern with glass sides",
        location="hand",
        fragile=True,
    ),
    "path": ObjectConfig(
        id="path",
        label="path",
        phrase="the stone path",
        location="ground",
        fragile=False,
    ),
    "mirror": ObjectConfig(
        id="mirror",
        label="mirror",
        phrase="a small round mirror",
        location="basket",
        fragile=False,
    ),
}

FIXES = [
    Fix(
        id="steady_hand",
        label="a steady hand",
        prep="hold the lantern still and let the mirror catch the light",
        tail="kept the lantern steady and used the mirror instead",
        protects={"dim", "conflict"},
    ),
    Fix(
        id="use_mirror",
        label="the mirror",
        prep="set the lantern on the bench and use the mirror for a bright shine",
        tail="used the mirror to make a bright spot on the path",
        protects={"dim"},
    ),
]

GIRL_NAMES = ["Mira", "Lina", "Nora", "Ivy", "Ada", "Mina"]
BOY_NAMES = ["Tobin", "Perry", "Jasper", "Eli", "Finn", "Robin"]
TRAITS = ["curious", "restless", "thoughtful", "gentle", "brave", "bright"]


def activity_at_risk(sit: Situation, obj: ObjectConfig) -> bool:
    return sit.id == "shake-dim" and obj.id == "lantern"


def choose_fix(sit: Situation, obj: ObjectConfig) -> Optional[Fix]:
    if not activity_at_risk(sit, obj):
        return None
    return FIXES[0]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for sit_id in setting.affords:
            sit = SITUATIONS[sit_id]
            for obj_id, obj in OBJECTS.items():
                if activity_at_risk(sit, obj) and choose_fix(sit, obj):
                    out.append((place, sit_id, obj_id))
    return out


def predict(world: World, actor: Entity, sit: Situation, obj_id: str) -> dict:
    sim = world.copy()
    lantern = sim.get(obj_id)
    actor2 = sim.get(actor.id)
    actor2.memes["curiosity"] = actor2.memes.get("curiosity", 0.0) + 1.0
    lantern.meters["dim"] = lantern.meters.get("dim", 0.0) + sit.dimming
    lantern.meters["shaken"] = lantern.meters.get("shaken", 0.0) + 1.0
    path_dark = lantern.meters["dim"] >= THRESHOLD
    return {"dark": path_dark, "dim": lantern.meters["dim"]}


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(
        f"In {world.setting.place}, there was a little {trait} {hero.type} named {hero.id} "
        f"who noticed every small thing."
    )


def love(world: World, hero: Entity, sit: Situation) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.pronoun().capitalize()} loved {sit.gerund}, because wondering felt like a game."
    )


def present(world: World, friend: Entity, hero: Entity, obj: Entity) -> None:
    world.say(
        f"One dusk, {hero.id} and {friend.pronoun('possessive')} friend found {hero.pronoun('object')} "
        f"{obj.phrase} beside the path."
    )


def warning(world: World, friend: Entity, hero: Entity, sit: Situation, obj: Entity) -> bool:
    pred = predict(world, hero, sit, obj.id)
    if not pred["dark"]:
        return False
    world.facts["predicted_dim"] = pred["dim"]
    world.say(
        f'"If you {sit.verb}, the light will dim," {friend.pronoun("possessive")} friend said. '
        f'"Then the path may grow dark."'
    )
    return True


def conflict(world: World, hero: Entity, sit: Situation) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(f"But {hero.id} was too curious to stop.")
    world.say(f"{hero.pronoun().capitalize()} tried to {sit.rush}.")


def resolve(world: World, friend: Entity, hero: Entity, sit: Situation, obj: Entity) -> Optional[Fix]:
    fix = choose_fix(sit, OBJECTS[obj.id])
    if fix is None:
        return None
    world.say(
        f"{friend.pronoun('possessive').capitalize()} friend smiled and said, "
        f'"How about we {fix.prep}?"'
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    lantern = world.get(obj.id)
    lantern.meters["shaken"] = 0.0
    lantern.meters["dim"] = 0.0
    world.say(
        f"{hero.id} nodded, and they {fix.tail}. The lantern stayed bright, and the path kept its silver shine."
    )
    return fix


def tell(setting: Setting, sit: Situation, obj_cfg: ObjectConfig,
         hero_name: str, hero_gender: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        traits=["little", trait, "curious"],
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type=friend_type,
        label="friend",
        traits=["wise", "gentle"],
    ))
    obj = world.add(Entity(
        id=obj_cfg.id,
        type=obj_cfg.id,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        caretaker=friend.id,
    ))
    obj.meters["dim"] = 0.0
    obj.meters["shaken"] = 0.0

    intro(world, hero)
    world.para()
    love(world, hero, sit)
    present(world, friend, hero, obj)
    world.para()
    if warning(world, friend, hero, sit, obj):
        conflict(world, hero, sit)
        world.para()
        resolve(world, friend, hero, sit, obj)

    world.facts.update(
        hero=hero,
        friend=friend,
        object=obj,
        object_cfg=obj_cfg,
        situation=sit,
        setting=setting,
        resolved=True,
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sit = f["situation"]
    obj = f["object_cfg"]
    return [
        f'Write a short fable for children about curiosity, a warning, and the word "{sit.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {sit.verb} but a friend worries about {obj.label} and the dim path.",
        f'Write a simple moral tale that includes "{sit.keyword}" and ends with a brighter, safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    sit: Situation = f["situation"]
    obj: ObjectConfig = f["object_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to {sit.verb}?",
            answer=f"{hero.id} wanted to {sit.verb} because {hero.pronoun('subject')} was curious and loved finding out what things could do.",
        ),
        QAItem(
            question=f"What did {friend.pronoun('possessive')} friend worry would happen to the {obj.label}?",
            answer=f"{friend.pronoun('subject').capitalize()} worried the {obj.label} would get dim if someone shook it, and then the path would be harder to see.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the lantern?",
            answer=f"They chose a safer way and used the lantern gently, so it stayed bright and the path still glowed like a little silver ribbon.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do at dusk?",
            answer="A lantern gives off light when the world is getting dark, so people can see the way.",
        ),
        QAItem(
            question="Why is shaking something fragile a bad idea?",
            answer="Shaking a fragile thing can make it wobble, break, or stop working the way it should.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
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
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", situation="shake-dim", object="lantern", name="Mira", gender="girl", friend="fox", trait="curious"),
    StoryParams(place="garden", situation="shake-dim", object="lantern", name="Tobin", gender="boy", friend="owl", trait="thoughtful"),
    StoryParams(place="hill", situation="shake-dim", object="lantern", name="Nora", gender="girl", friend="fox", trait="bright"),
]


def explain_rejection(sit: Situation, obj: ObjectConfig) -> str:
    return f"(No story: {sit.verb} only makes sense with the lantern, because that is the object whose light can dim.)"


def valid_gender(object_id: str, gender: str) -> bool:
    return object_id == "lantern" and gender in {"girl", "boy"}


def explain_gender(object_id: str, gender: str) -> str:
    return f"(No story: this fable is built for a child hero, so {gender} is fine, but the object must still be the lantern.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: curiosity, conflict, and the shake-dim lantern fable.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=["fox", "owl"])
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
    if args.situation and args.object:
        sit = SITUATIONS[args.situation]
        obj = OBJECTS[args.object]
        if not activity_at_risk(sit, obj):
            raise StoryError(explain_rejection(sit, obj))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.situation is None or c[1] == args.situation)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sit_id, obj_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if not valid_gender(obj_id, gender):
        raise StoryError(explain_gender(obj_id, gender))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(["fox", "owl"])
    trait = args.gender and rng.choice(TRAITS) or rng.choice(TRAITS)
    return StoryParams(place=place, situation=sit_id, object=obj_id, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SITUATIONS[params.situation],
        OBJECTS[params.object],
        params.name,
        params.gender,
        params.friend,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
% A story is valid when the situation can truly endanger the chosen object.
risk(A, O) :- shake_like(A), fragile(O).
valid(Place, A, O) :- affords(Place, A), risk(A, O), has_fix(A, O).

% The single chosen fix for shake-dim is a steady hand.
has_fix(shake_dim, lantern) :- fix(steady_hand).

% Curiosity is the emotional engine of the fable.
featured_emotion(curiosity).
featured_emotion(conflict).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a.replace("-", "_")))
    for sid, sit in SITUATIONS.items():
        lines.append(asp.fact("situation", sid.replace("-", "_")))
        if sid == "shake-dim":
            lines.append(asp.fact("shake_like", sid.replace("-", "_")))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.fragile:
            lines.append(asp.fact("fragile", oid))
    lines.append(asp.fact("fix", "steady_hand"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
        print(f"{len(combos)} compatible (place, situation, object) combos:\n")
        for place, sit, obj in combos:
            print(f"  {place:12} {sit:12} {obj}")
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
            header = f"### {p.name}: {p.situation} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
