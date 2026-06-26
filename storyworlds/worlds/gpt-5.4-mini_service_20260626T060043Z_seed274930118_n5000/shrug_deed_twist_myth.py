#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shrug_deed_twist_myth.py
=====================================================================================================

A small myth-style storyworld about a young helper, a sacred task, and a
twisting trial that can be solved by a fitting deed.

The seed tale behind this world is simple:
- A child in a hill-village must carry a lantern or offering to a shrine.
- A winding path creates a danger or delay.
- A proud shrug turns into a brave deed.
- The ending proves the world has changed by showing a completed rite and a
  calmer sky.

This file keeps the domain compact and constraint-checked:
- state drives prose
- invalid choices raise StoryError
- an inline ASP twin mirrors the Python reasonableness gate
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    path_twist: bool = True
    weather: str = "windy"

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.path_twist = self.path_twist
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    role: str
    deed: str
    offering: str
    guardian: str
    twist: str
    seed: Optional[int] = None


@dataclass
class Path:
    label: str
    danger: str
    twist_kind: str
    ritual: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    label: str
    phrase: str
    region: str
    gender_ok: set[str] = field(default_factory=lambda: {"girl", "boy"})
    plural: bool = False


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
    prep: str
    tail: str
    plural: bool = False


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_scatter(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters.get("fear", 0.0) < THRESHOLD:
            continue
        if not world.path_twist:
            continue
        sig = ("scatter", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["lost"] = hero.meters.get("lost", 0.0) + 1
        out.append(f"The path twisted, and the road seemed to forget {hero.id}.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("courage", 0.0) < THRESHOLD:
            continue
        if hero.memes.get("resolve", 0.0) < THRESHOLD:
            continue
        sig = ("calm", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["fear"] = 0.0
        hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
        out.append(f"At last, the old worry fell quiet in {hero.id}'s chest.")
    return out


CAUSAL_RULES = [Rule("scatter", _r_scatter), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def path_at_risk(path: Path, offering: Offering) -> bool:
    return offering.region in {"hands", "torso"} and path.twist_kind in {"wind", "dark", "stone"}


def select_charm(path: Path, offering: Offering) -> Optional[Charm]:
    for charm in CHARMS:
        if path.twist_kind in charm.wards and offering.region in charm.covers:
            return charm
    return None


def predict(world: World, hero: Entity, path: Path, offering_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["fear"] = sim.get(hero.id).meters.get("fear", 0.0) + 1
    if path.twist_kind == "wind":
        sim.get(hero.id).meters["lost"] = sim.get(hero.id).meters.get("lost", 0.0) + 1
    return {
        "lost": bool(sim.get(hero.id).meters.get("lost", 0.0) >= THRESHOLD),
        "peace": sim.get(hero.id).memes.get("peace", 0.0),
    }


def tell_story(place: str, path: Path, offering_cfg: Offering, hero_name: str,
               hero_type: str, guardian_type: str, twist_word: str) -> World:
    world = World(place=place, weather="windy")
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="the elder"))
    offering = world.add(Entity(
        id="offering",
        label=offering_cfg.label,
        phrase=offering_cfg.phrase,
        owner=hero.id,
        caretaker=guardian.id,
        region=offering_cfg.region,
        plural=offering_cfg.plural,
    ))

    hero.memes["hope"] = 1
    world.say(f"In the old hill village, {hero.id} was a small {hero_type} with a steady heart.")
    world.say(f"{hero.id} had been chosen for a holy deed: to carry {offering_cfg.phrase} to the shrine.")
    world.say(f"{hero.id} loved the task, for the bells at {place} rang like bright water.")

    world.para()
    world.say(f"On the day of the deed, the wind came early, and the road to the shrine was full of {twist_word}.")
    world.say(f"{hero.id} set out with {offering_cfg.phrase} held close, while {guardian.label or 'the elder'} watched.")
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1

    if path_at_risk(path, offering_cfg):
        pred = predict(world, hero, path, offering.id)
        world.facts["predicted_lost"] = pred["lost"]
        world.facts["predicted_peace"] = pred["peace"]
        world.say(f"{hero.id} stopped at the first bend and gave a little shrug.")
        world.say(f'"The road is twisted," {hero.id} said, "but I will not turn back from my deed."')
        hero.memes["shrug"] = hero.memes.get("shrug", 0.0) + 1
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
        charm = select_charm(path, offering_cfg)
        if charm:
            charm_ent = world.add(Entity(
                id=charm.id,
                kind="thing",
                type="charm",
                label=charm.label,
                protective=True,
                covers=set(charm.covers),
            ))
            charm_ent.worn_by = hero.id
            world.say(f"Then {guardian.label or 'the elder'} brought {charm.label} and said, "
                      f"\"{charm.prep}, and the twist will not steal the offering.\"")
            hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
            world.say(f"{hero.id} accepted the charm, and the path no longer felt like a trick.")
            world.say(f"They {charm.tail}.")
            hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1
            hero.meters["offering_safe"] = hero.meters.get("offering_safe", 0.0) + 1
            propagate(world)
            world.para()
            world.say(f"At the shrine, {hero.id} laid down {offering_cfg.phrase}.")
            world.say(f"The bells answered, the wind softened, and the deed was complete.")
            world.say(f"{hero.id} stood smaller than the hill, yet brighter than before.")
            world.facts["charm"] = charm
            world.facts["resolved"] = True
        else:
            raise StoryError("(No story: this twist has no fitting charm to guard the offering.)")
    else:
        raise StoryError("(No story: the offering is not truly at risk on this path.)")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        offering=offering,
        path=path,
        place=place,
        hero_type=hero_type,
        guardian_type=guardian_type,
        twist_word=twist_word,
    )
    return world


SETTINGS = {
    "shrine_hill": "the shrine hill",
    "river_steps": "the river steps",
    "oak_gate": "the oak gate",
}

PATHS = {
    "twist_wind": Path(
        label="wind-twisted road",
        danger="the wind could confuse a traveler",
        twist_kind="wind",
        ritual="carry the lantern",
        resolution="The wind was answered with a lantern-scarf.",
        tags={"wind", "twist"},
    ),
    "twist_stone": Path(
        label="stone-twisted road",
        danger="the stones could turn an ankle",
        twist_kind="stone",
        ritual="carry the offering bowl",
        resolution="The stones were answered with a sure-footed sash.",
        tags={"stone", "twist"},
    ),
    "twist_dark": Path(
        label="dark-twisted road",
        danger="the dark could make the trail vanish",
        twist_kind="dark",
        ritual="carry the shrine lamp",
        resolution="The dark was answered with a bright veil.",
        tags={"dark", "twist"},
    ),
}

OFFERINGS = {
    "lantern": Offering(label="lantern", phrase="a small brass lantern", region="hands"),
    "bowl": Offering(label="bowl", phrase="a carved offering bowl", region="hands"),
    "lamp": Offering(label="lamp", phrase="a shrine lamp with a red flame", region="torso"),
    "veil": Offering(label="veil", phrase="a white veil of honor", region="torso", gender_ok={"girl"}),
}

CHARMS = [
    Charm(id="scarf", label="a lantern-scarf", covers={"hands", "torso"}, wards={"wind"}, prep="wrap the lantern-scarf around your shoulders", tail="walked with the wind at their backs"),
    Charm(id="sash", label="a sure-footed sash", covers={"hands", "legs"}, wards={"stone"}, prep="tie on the sure-footed sash", tail="stepped lightly over the turning stones"),
    Charm(id="veil_charm", label="a bright veil", covers={"torso"}, wards={"dark"}, prep="place the bright veil over your head", tail="moved as if a small star had joined them"),
]

HEROES = ["Nara", "Ivo", "Mira", "Tavi", "Sera", "Lio"]
TRAITS = ["brave", "gentle", "proud", "curious", "steadfast"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for path_id, path in PATHS.items():
            for off_id, offering in OFFERINGS.items():
                if path.twist_kind == "dark" and "girl" not in offering.gender_ok and off_id == "veil":
                    continue
                if path_at_risk(path, offering) and select_charm(path, offering):
                    combos.append((place, path_id, off_id))
    return combos


def explain_rejection(path: Path, offering: Offering) -> str:
    if not path_at_risk(path, offering):
        return f"(No story: the {offering.label} is not truly threatened by the {path.label}.)"
    return f"(No story: no charm in this world can honestly guard a {offering.label} on the {path.label}.)"


def explain_gender(offering_id: str, gender: str) -> str:
    ok = " / ".join(sorted(OFFERINGS[offering_id].gender_ok))
    return f"(No story: a {OFFERINGS[offering_id].label} is not a typical {gender}'s ritual object here; try {ok}.)"


@dataclass
class StoryParams:
    place: str
    path: str
    offering: str
    hero_name: str
    hero_type: str
    guardian_type: str
    twist: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a deed, a shrug, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guardian", choices=["elder", "priest", "mother", "father"])
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
    if args.path and args.offering:
        path, off = PATHS[args.path], OFFERINGS[args.offering]
        if not path_at_risk(path, off) or not select_charm(path, off):
            raise StoryError(explain_rejection(path, off))
    if args.gender and args.offering and args.gender not in OFFERINGS[args.offering].gender_ok:
        raise StoryError(explain_gender(args.offering, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.path is None or c[1] == args.path)
              and (args.offering is None or c[2] == args.offering)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, path_id, offering_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if offering_id == "veil":
        gender = "girl"
    hero_name = args.name or rng.choice(HEROES)
    hero_type = gender
    guardian_type = args.guardian or rng.choice(["elder", "priest", "mother", "father"])
    twist = rng.choice(["twist", "coil", "crook"])
    return StoryParams(place=place, path=path_id, offering=offering_id, hero_name=hero_name,
                       hero_type=hero_type, guardian_type=guardian_type, twist=twist)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    path = f["path"]
    offering = f["offering"]
    return [
        f'Write a short myth for a young child about {hero.id}, a deed, and a {f["twist_word"]} in the road.',
        f"Tell a gentle legend in which {hero.id} carries {offering.phrase} to {world.place} despite a {path.label}.",
        f'Write a simple myth that includes the words "shrug" and "deed" and ends with a shrine ritual being completed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    offering = f["offering"]
    path = f["path"]
    qa = [
        QAItem(
            question=f"What was {hero.id}'s holy task in the story?",
            answer=f"{hero.id} had to carry {offering.phrase} to the shrine as a sacred deed.",
        ),
        QAItem(
            question=f"Why did the road make {hero.id} pause?",
            answer=f"The road was {path.label}, so the twist in it could threaten the offering.",
        ),
        QAItem(
            question=f"What did {guardian.label or 'the elder'} give {hero.id} to help?",
            answer=f"{guardian.label or 'The elder'} gave {hero.id} {f['charm'].label} so the offering could be carried safely.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel after the shrine deed was finished?",
            answer=f"{hero.id} felt calm and proud after the deed was done and the wind softened.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "wind": [("What does wind do?", "Wind is moving air that can rustle leaves, push cloaks, and make a road feel tricky.")],
    "shrine": [("What is a shrine?", "A shrine is a special place where people go to show respect, say prayers, or leave offerings.")],
    "lantern": [("What does a lantern do?", "A lantern gives light, especially when the road is dark.")],
    "bowl": [("What is an offering bowl for?", "An offering bowl can carry gifts neatly so they do not spill.")],
    "veil": [("What is a veil?", "A veil is a light cloth that can be worn for honor or ceremony.")],
    "twist": [("What is a twist?", "A twist is a turn or curl in something, like a path that bends or a rope that winds.")],
    "deed": [("What is a deed?", "A deed is an action, and a good deed is a helpful thing someone chooses to do.")],
    "shrug": [("What does shrug mean?", "To shrug is to lift your shoulders a little, often to show 'I will try anyway' or 'I do not know.'")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["path"].tags)
    tags.add("deed")
    tags.add("shrug")
    if world.facts.get("offering"):
        tags.add(world.facts["offering"].label)
    out = []
    for key in ["wind", "shrine", "lantern", "bowl", "veil", "twist", "deed", "shrug"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
path_at_risk(P, O) :- path(P), offering(O), needs_region(O, R), twist_of(P, T), twist_threat(T, R).
has_charm(P, O) :- path_at_risk(P, O), charm(C), wards(C, T), twist_of(P, T), covers(C, R), needs_region(O, R).
valid(Place, Path, Offering) :- place(Place), path(Path), offering(Offering), path_at_risk(Path, Offering), has_charm(Path, Offering).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("twist_of", pid, p.twist_kind))
    for oid, o in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("needs_region", oid, o.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for w in sorted(c.wards):
            lines.append(asp.fact("wards", c.id, w))
        for cv in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, cv))
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


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        SETTINGS[params.place],
        PATHS[params.path],
        OFFERINGS[params.offering],
        params.hero_name,
        params.hero_type,
        params.guardian_type,
        params.twist,
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


CURATED = [
    StoryParams(place="shrine_hill", path="twist_wind", offering="lantern", hero_name="Nara", hero_type="girl", guardian_type="elder", twist="twist"),
    StoryParams(place="river_steps", path="twist_stone", offering="bowl", hero_name="Ivo", hero_type="boy", guardian_type="priest", twist="twist"),
    StoryParams(place="oak_gate", path="twist_dark", offering="lamp", hero_name="Mira", hero_type="girl", guardian_type="mother", twist="twist"),
]


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, path, offering) combos:")
        for t in combos:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero_name}: {p.path} at {p.place} (offering: {p.offering})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
