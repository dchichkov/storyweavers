#!/usr/bin/env python3
"""
storyworlds/worlds/gain_incubator_misunderstanding_humor_fable.py
===================================================================

A small, fable-shaped story world about an incubator, a mistaken idea, and a
humorous turn that leads to a lesson.

The seed premise:
- A young helper hears about a new incubator and thinks it is meant to help
  "gain" something visible and immediate.
- A careful character explains that the incubator is for warmth and patience,
  not for instant gain.
- The misunderstanding causes a comical mix-up before the characters learn a
  better way to think about growth.

The world is intentionally small, classical, and constraint-checked:
- typed entities with physical meters and emotional memes
- a reasonableness gate for valid story combinations
- a matching inline ASP twin for parity checks
- child-facing prose with a fable ending and a moral image
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "mother", "woman"}
        male = {"boy", "fox", "farmer", "man", "rooster"}
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    gain: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Insight:
    id: str
    label: str
    explanation: str
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    action: str
    misunderstanding: str
    hero: str
    hero_kind: str
    mentor: str
    mentor_kind: str
    seed: Optional[int] = None


SETTINGS = {
    "farmyard": Setting(place="the farmyard", affords={"gain", "warmth"}),
    "henhouse": Setting(place="the henhouse", indoors=True, affords={"gain", "warmth"}),
    "barn": Setting(place="the barn", indoors=True, affords={"gain", "warmth"}),
}

ACTIONS = {
    "gain": Action(
        id="gain",
        verb="gain more eggs",
        gerund="gaining more eggs",
        rush="rush to the incubator and count the eggs",
        gain="gain",
        consequence="nothing grows quicker just because you wish it",
        keyword="gain",
        tags={"gain", "eggs", "humor"},
    ),
    "warmth": Action(
        id="warmth",
        verb="keep the eggs warm",
        gerund="keeping the eggs warm",
        rush="hurry to check the heat",
        gain="grow",
        consequence="warmth helps eggs hatch when they are ready",
        keyword="incubator",
        tags={"incubator", "warmth", "eggs"},
    ),
}

MISUNDERSTANDINGS = {
    "profit": Insight(
        id="profit",
        label="profit",
        explanation="The incubator is not a coin box; it warms eggs, it does not make instant treasure.",
        fixes={"gain"},
    ),
    "hatch": Insight(
        id="hatch",
        label="hatching",
        explanation="The incubator helps with hatching, which takes time and care.",
        fixes={"warmth"},
    ),
    "noise": Insight(
        id="noise",
        label="noise",
        explanation="A loud plan is not always a better plan; the gentlest way often works best.",
        fixes={"gain", "warmth"},
    ),
}

KINDS = {
    "fox": "fox",
    "hen": "hen",
    "rooster": "rooster",
    "farmer": "farmer",
    "boy": "boy",
    "girl": "girl",
}

NAMES = {
    "fox": ["Felix", "Milo", "Rufus", "Toby"],
    "hen": ["Hattie", "Mabel", "Dot", "Nell"],
    "rooster": ["Clive", "Pip", "Sunny", "Bram"],
    "farmer": ["Mara", "Iris", "Otto", "Jules"],
    "boy": ["Tom", "Ben", "Leo", "Ned"],
    "girl": ["Ada", "Lia", "Mia", "Nora"],
}

TRAITS = ["curious", "bouncy", "eager", "silly", "gentle", "proud"]

CURATED = [
    StoryParams("barn", "gain", "profit", "fox", "fox", "hen", "hen"),
    StoryParams("henhouse", "warmth", "hatch", "boy", "boy", "hen", "hen"),
    StoryParams("farmyard", "gain", "noise", "girl", "girl", "farmer", "farmer"),
]


def valid_story(setting: Setting, action: Action, misunderstanding: Insight) -> bool:
    return action.id in setting.affords and action.id in misunderstanding.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for a_id, action in ACTIONS.items():
            for m_id, mis in MISUNDERSTANDINGS.items():
                if valid_story(setting, action, mis):
                    out.append((s_id, a_id, m_id))
    return out


def select_name(kind: str, rng: random.Random) -> str:
    return rng.choice(NAMES[kind])


def choose_kind(rng: random.Random) -> str:
    return rng.choice(list(KINDS))


def choose_role(kind: str, rng: random.Random) -> str:
    return choose_name_for_kind(kind, rng)


def choose_name_for_kind(kind: str, rng: random.Random) -> str:
    return rng.choice(NAMES[kind])


def make_entity(eid: str, kind: str, label: str, phrase: str = "", owner: Optional[str] = None) -> Entity:
    return Entity(id=eid, kind="character" if kind in KINDS.values() else "thing", type=kind, label=label, phrase=phrase, owner=owner)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero_name = params.hero
    mentor_name = params.mentor
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_kind, label=hero_name))
    mentor = world.add(Entity(id="mentor", kind="character", type=params.mentor_kind, label=mentor_name))
    incubator = world.add(Entity(id="incubator", kind="thing", type="incubator", label="incubator", phrase="a wooden incubator with a warm lid", caretaker=mentor.id))
    eggs = world.add(Entity(id="eggs", kind="thing", type="eggs", label="eggs", phrase="a small basket of pale eggs", owner=mentor.id, plural=True))
    world.facts.update(hero=hero, mentor=mentor, incubator=incubator, eggs=eggs, setting=world.setting, action=ACTIONS[params.action], misunderstanding=MISUNDERSTANDINGS[params.misunderstanding])
    return world


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mentor = world.get("mentor")
    act: Action = world.facts["action"]

    sig = ("confusion", act.id)
    if sig not in world.fired:
        world.fired.add(sig)
        hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
        hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
        out.append(f"{hero.label} felt puzzled, because the incubator sounded like a way to gain something fast.")

    if hero.memes.get("confusion", 0.0) >= THRESHOLD and ("humor", act.id) not in world.fired:
        world.fired.add(("humor", act.id))
        hero.memes["amusement"] = hero.memes.get("amusement", 0.0) + 1
        out.append(f"The thought was so funny that even the hen blinked twice, then tried not to laugh.")

    if ("lesson", act.id) not in world.fired:
        world.fired.add(("lesson", act.id))
        mentor.memes["wisdom"] = mentor.memes.get("wisdom", 0.0) + 1
        hero.memes["confusion"] = 0.0
        hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1
        out.append(f"{mentor.label} explained that an incubator helps eggs grow warm, and gain comes later, after care and patience.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def tell_story(world: World) -> None:
    hero = world.get("hero")
    mentor = world.get("mentor")
    act: Action = world.facts["action"]
    mis: Insight = world.facts["misunderstanding"]
    incubator = world.get("incubator")
    eggs = world.get("eggs")

    world.say(f"{hero.label} was a {hero.type} with a bright nose and a bigger wish: {act.gerund}.")
    world.say(f"Near {world.setting.place}, {mentor.label} kept {eggs.label} beside {incubator.phrase}, and {hero.label} stared at it with a curious grin.")
    world.para()
    world.say(f'"If it is called an incubator," said {hero.label}, "then surely it is for making a quick {act.gain}!"')
    world.say(f"{mentor.label} shook {mentor.pronoun('possessive')} head, because that was the misunderstanding: {mis.explanation}")
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.label} peered inside, saw the warm eggs, and let out a sheepish snort.")
    world.say(f'"Oh," {hero.label} said, "it does not make treasure. It helps little things become ready."')
    world.say(f"So {hero.label} helped keep watch, and the incubator stayed warm all afternoon while everyone waited.")
    world.say(f"In the end, the eggs were still eggs, but the room was kinder, quieter, and full of the right kind of {act.gain}.'")
    world.say("Moral: a quick gain is not always real gain; patience can look small before it looks wise.")
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a child that includes an incubator and the word "gain".',
        f"Tell a humorous story where {f['hero'].label} misunderstands what an incubator does, and {f['mentor'].label} gently corrects the mistake.",
        "Write a simple animal-fable with a misunderstanding, a laugh, and a moral about patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    act: Action = f["action"]
    mis: Insight = f["misunderstanding"]
    return [
        QAItem(
            question=f"What did {hero.label} think the incubator was for?",
            answer=f"{hero.label} thought the incubator was for making a quick {act.gain}, but that was the misunderstanding.",
        ),
        QAItem(
            question=f"What did {mentor.label} explain about the incubator?",
            answer=f"{mentor.label} explained that the incubator keeps eggs warm so they can grow and hatch later.",
        ),
        QAItem(
            question=f"Why was the story funny?",
            answer=f"It was funny because {hero.label} mixed up the incubator's real job with a silly idea about instant gain.",
        ),
        QAItem(
            question="What was the lesson at the end?",
            answer="The lesson was that patience and care matter more than wanting a quick result.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an incubator?",
            answer="An incubator is a warm place or machine that helps eggs stay cozy until they hatch.",
        ),
        QAItem(
            question="What does gain mean?",
            answer="Gain means to get more of something or to make progress, but it usually takes time and work.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,A,M) :- setting(S), action(A), misunderstanding(M),
                      affords(S,A), fixes(M,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        for fix in sorted(m.fixes):
            lines.append(asp.fact("fixes", mid, fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.action and args.misunderstanding:
        if not valid_story(SETTINGS[args.setting], ACTIONS[args.action], MISUNDERSTANDINGS[args.misunderstanding]):
            raise StoryError("That setting/action/misunderstanding combination does not make a reasonable fable.")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.action is None or c[1] == args.action)
        and (args.misunderstanding is None or c[2] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("No valid story matches those options.")
    setting_id, action_id, mis_id = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(["fox", "hen", "boy", "girl"])
    mentor_kind = args.mentor_kind or ("hen" if hero_kind != "hen" else "farmer")
    hero = args.hero or select_name(hero_kind, rng)
    mentor = args.mentor or select_name(mentor_kind, rng)
    return StoryParams(
        setting=setting_id,
        action=action_id,
        misunderstanding=mis_id,
        hero=hero,
        hero_kind=hero_kind,
        mentor=mentor,
        mentor_kind=mentor_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: gain, incubator, misunderstanding, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", dest="hero_kind", choices=["fox", "hen", "boy", "girl"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-kind", dest="mentor_kind", choices=["fox", "hen", "boy", "girl", "farmer"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible (setting, action, misunderstanding) combos:\n")
        for s, a, m in models:
            print(f"  {s:10} {a:12} {m:14}")
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
            header = f"### {p.hero}: {p.action} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
