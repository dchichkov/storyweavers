#!/usr/bin/env python3
"""
storyworlds/worlds/rib_thunk_reconciliation_superhero_story.py
===============================================================

A small superhero story world about a loud thunk, a sore rib, and a friendly
reconciliation.

Source tale sketch:
---
A young superhero heard a thunk on a city roof and rushed to help. In the hurry,
their sidekick bumped into them and made their rib ache. They got cross for a
moment because the mission was important. Then they found the real problem, fixed
it together, and made up before flying home.

World shape:
---
- A hero, a sidekick, a city setting, and one small rescue mission.
- A thunk can come from a loose vent, a falling crate, or a clumsy landing.
- The hero may hurt a rib if they collide while wearing a heavy cape or chest gear.
- Reconciliation happens when they notice the same problem, help each other, and
  apologize. The ending should prove the hurt calmed down and the team is back
  together.

The prose is driven by world state: risk, bump, concern, apology, and repair.
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
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "team":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city roof"
    afford: set[str] = field(default_factory=lambda: {"thunk", "rescue"})


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    thunk_source: str
    risk: str
    recovery: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    protects: set[str]
    comfort: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)


def _hero(w: World) -> Entity:
    return next(e for e in w.entities.values() if e.kind == "character" and e.type == "hero")


def _sidekick(w: World) -> Entity:
    return next(e for e in w.entities.values() if e.kind == "character" and e.type == "sidekick")


def _mission_item(w: World) -> Entity:
    return w.get("mission")


def _gear_item(w: World) -> Optional[Entity]:
    return w.entities.get("gear")


def _do_thunk(w: World, source: str) -> None:
    hero = _hero(w)
    mission = _mission_item(w)
    if ("thunk", source) in w.fired:
        return
    w.fired.add(("thunk", source))
    w.facts["thunk_source"] = source
    hero.memes["alert"] = hero.memes.get("alert", 0.0) + 1
    if source == "crate":
        hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
        w.say("From above came a sudden thunk.")
        w.say("A crate had tipped near the edge and made the roof shake.")
    elif source == "vent":
        w.say("From the vent came a sudden thunk.")
        w.say("A loose metal cover had popped and clanged against the wall.")
    else:
        w.say("From the alley came a sudden thunk.")
        w.say("A clumsy landing had knocked something hard on the roof.")
    if mission.meters.get("risk", 0.0) < THRESHOLD:
        mission.meters["risk"] = 1.0


def _bump_rib(w: World) -> None:
    hero = _hero(w)
    sidekick = _sidekick(w)
    if hero.memes.get("shoved", 0.0) < THRESHOLD:
        return
    if ("rib", hero.id) in w.fired:
        return
    w.fired.add(("rib", hero.id))
    hero.meters["rib"] = hero.meters.get("rib", 0.0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    hero.memes["grumpy"] = hero.memes.get("grumpy", 0.0) + 1
    sidekick.memes["guilty"] = sidekick.memes.get("guilty", 0.0) + 1
    w.say(f"In the rush, {sidekick.id} bumped into {hero.id}, and {hero.id}'s rib ached.")


def _reconcile(w: World) -> None:
    hero = _hero(w)
    sidekick = _sidekick(w)
    mission = _mission_item(w)
    if hero.memes.get("grumpy", 0.0) < THRESHOLD:
        return
    if mission.memes.get("understood", 0.0) < THRESHOLD:
        return
    if ("reconcile", hero.id) in w.fired:
        return
    w.fired.add(("reconcile", hero.id))
    hero.memes["grumpy"] = 0.0
    hero.memes["kind"] = hero.memes.get("kind", 0.0) + 1
    sidekick.memes["guilty"] = 0.0
    sidekick.memes["kind"] = sidekick.memes.get("kind", 0.0) + 1
    hero.meters["rib"] = max(0.0, hero.meters.get("rib", 0.0) - 1)
    w.say(f"Then {hero.id} and {sidekick.id} saw the same problem and understood each other.")
    w.say(f"{sidekick.id} said sorry. {hero.id} said sorry too, and the two friends made up.")
    w.say("That was the moment of reconciliation.")


def _repair_mission(w: World) -> None:
    hero = _hero(w)
    sidekick = _sidekick(w)
    mission = _mission_item(w)
    if mission.meters.get("risk", 0.0) < THRESHOLD:
        return
    if ("repair", mission.id) in w.fired:
        return
    w.fired.add(("repair", mission.id))
    mission.meters["risk"] = 0.0
    mission.memes["understood"] = 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    sidekick.memes["pride"] = sidekick.memes.get("pride", 0.0) + 1
    w.say(f"They followed the thunk and found the real trouble: {mission.phrase}.")
    w.say(f"Together they fixed it, and {sidekick.id} steadied the spot while {hero.id} worked.")


def propagate(w: World) -> None:
    changed = True
    while changed:
        changed = False
        before = len(w.fired)
        _repair_mission(w)
        _bump_rib(w)
        _reconcile(w)
        _repair_mission(w)
        _do_thunk(w, w.facts.get("thunk_source", "crate"))
        if len(w.fired) != before:
            changed = True


def story_setup() -> tuple[Setting, Mission, Gear]:
    setting = Setting()
    mission = Mission(
        id="mission",
        verb="fix the roof problem",
        gerund="fixing the roof problem",
        thunk_source="crate",
        risk="a falling crate could hurt someone",
        recovery="the loose crate was tied down",
        tags={"thunk", "rib", "rescue"},
    )
    gear = Gear(
        id="gear",
        label="soft chest padding",
        protects={"rib"},
        comfort="gentle padding made the hug feel better",
    )
    return setting, mission, gear


def tell(name: str = "Nova", sidekick_name: str = "Zip", seed: Optional[int] = None) -> World:
    rng = random.Random(seed)
    setting, mission_cfg, gear_cfg = story_setup()
    w = World(setting)
    hero = w.add(Entity(id=name, kind="character", type="hero", label=name))
    sidekick = w.add(Entity(id=sidekick_name, kind="character", type="sidekick", label=sidekick_name))
    mission = w.add(Entity(
        id=mission_cfg.id,
        kind="thing",
        type="mission",
        label="roof mission",
        phrase="a loose crate near the antenna",
        owner=hero.id,
        caretaker=sidekick.id,
    ))
    gear = w.add(Entity(
        id=gear_cfg.id,
        kind="thing",
        type="gear",
        label=gear_cfg.label,
        owner=hero.id,
    ))
    gear.worn_by = hero.id
    w.facts.update(hero=hero, sidekick=sidekick, mission=mission, gear=gear, setting=setting)
    w.say(f"{hero.id} was a brave little superhero who loved helping in {setting.place}.")
    w.say(f"{sidekick.id} stayed close with {hero.id}, ready to help whenever a thunk sounded.")
    w.para()
    sources = ["crate", "vent", "landing"]
    source = rng.choice(sources)
    w.facts["thunk_source"] = source
    _do_thunk(w, source)
    w.say(f"{hero.id} rushed toward the sound because {hero.pronoun('possessive')} mission was to help fast.")
    hero.memes["shoved"] = 1.0
    sidekick.memes["rush"] = 1.0
    w.say(f"In the hurry, {sidekick.id} reached the same spot at the same time.")
    propagate(w)
    w.para()
    if hero.meters.get("rib", 0.0) > 0:
        w.say(f"{hero.id} held {hero.pronoun('possessive')} side for a moment, then took a slow breath.")
    if _gear_item(w):
        w.say(f"{gear.label.capitalize()} under the cape helped the sore rib feel calmer.")
    if mission.meters.get("risk", 0.0) <= 0:
        w.say(f"By the end, the roof was safe, and the city felt quiet again.")
    w.facts["resolved"] = True
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mission = f["mission"]
    return [
        "Write a small superhero story for a young child about a loud thunk, a sore rib, and friends making up.",
        f"Tell a story where {hero.id} hears a thunk, {sidekick.id} helps, and the two heroes end in reconciliation.",
        f"Write a gentle superhero tale that includes the word thunk and ends with {hero.id} and {sidekick.id} working together again.",
        f"Make a child-friendly rescue story about {mission.label} on a city roof and a friendship that heals after a mistake.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mission = f["mission"]
    source = f.get("thunk_source", "crate")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a brave little superhero, and {sidekick.id}, the friend who stayed close during the roof mission.",
        ),
        QAItem(
            question=f"What made the loud thunk on the roof?",
            answer=f"The thunk came from the {source}, which made everyone look up and hurry toward the problem.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s rib hurt?",
            answer=f"{hero.id}'s rib hurt because {sidekick.id} bumped into {hero.id} in the rush to reach the roof problem.",
        ),
        QAItem(
            question=f"How did the friends fix things?",
            answer=f"They found {mission.phrase}, fixed it together, said sorry, and made up in reconciliation.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the roof safe again, {hero.id}'s rib feeling calmer, and the two friends working together side by side.",
        ),
    ]
    return qa


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word thunk mean?",
            answer="Thunk is a heavy, hard sound, like something bumping or hitting with a strong knock.",
        ),
        QAItem(
            question="What is a rib?",
            answer="A rib is one of the bones in your chest that helps protect your body and hold it up.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset stop arguing, say sorry, and become friendly again.",
        ),
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


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(w.fired)}")
    return "\n".join(lines)


# ASP twin
ASP_RULES = r"""
hero(hero1).
sidekick(side1).
setting(city_roof).
mission(mission1).
gear(gear1).

thunk_source(crate).
thunk_source(vent).
thunk_source(landing).

causes_thunk(crate).
causes_thunk(vent).
causes_thunk(landing).

hurts_rib(bump).
hurts_rib(collision).

repairable(mission1).
reconciliation_when(sorry).
reconciliation_when(help).
reconciliation_when(shared_problem).

valid_story(Source) :- thunk_source(Source), causes_thunk(Source).
can_reconcile :- reconciliation_when(sorry), reconciliation_when(help), reconciliation_when(shared_problem).
makes_story(Source) :- valid_story(Source), can_reconcile.
#show valid_story/1.
#show can_reconcile/0.
#show makes_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero1"),
        asp.fact("sidekick", "side1"),
        asp.fact("setting", "city_roof"),
        asp.fact("mission", "mission1"),
        asp.fact("gear", "gear1"),
    ]
    for s in ["crate", "vent", "landing"]:
        lines.append(asp.fact("thunk_source", s))
        lines.append(asp.fact("causes_thunk", s))
    lines.append(asp.fact("hurts_rib", "bump"))
    lines.append(asp.fact("hurts_rib", "collision"))
    lines.append(asp.fact("repairable", "mission1"))
    lines.append(asp.fact("reconciliation_when", "sorry"))
    lines.append(asp.fact("reconciliation_when", "help"))
    lines.append(asp.fact("reconciliation_when", "shared_problem"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1.\n#show can_reconcile/0.\n#show makes_story/1."))
    atoms = set((sym.name, tuple(a.number if a.type == a.type.Number else a.string if a.type == a.type.String else a.name for a in sym.arguments)) for sym in model)
    expected = {
        ("valid_story", ("crate",)),
        ("valid_story", ("vent",)),
        ("valid_story", ("landing",)),
        ("can_reconcile", ()),
        ("makes_story", ("crate",)),
        ("makes_story", ("vent",)),
        ("makes_story", ("landing",)),
    }
    if atoms == expected:
        print("OK: ASP rules match the Python story gate.")
        return 0
    print("MISMATCH:")
    print(sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with thunk, rib, and reconciliation.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--sidekick", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--all", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, int]:
    names = ["Nova", "Spark", "Comet", "Pixel", "Bolt", "Mira"]
    sidekicks = ["Zip", "Pip", "Dash", "Beep", "Glow", "Toto"]
    return (
        args.name or rng.choice(names),
        args.sidekick or rng.choice(sidekicks),
        rng.randrange(2**31),
    )


def generate(params) -> StorySample:
    name, sidekick, seed = params
    world = tell(name=name, sidekick_name=sidekick, seed=seed)
    return StorySample(
        params=type("StoryParams", (), {"name": name, "sidekick": sidekick, "seed": seed})(),
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
        print(asp_program("#show valid_story/1.\n#show can_reconcile/0.\n#show makes_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1.\n#show can_reconcile/0.\n#show makes_story/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    for i in range(args.n):
        name, sidekick, seed = resolve_params(args, random.Random(base_seed + i))
        sample = generate((name, sidekick, seed))
        samples.append(sample)
        if len(samples) == args.n:
            break

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
