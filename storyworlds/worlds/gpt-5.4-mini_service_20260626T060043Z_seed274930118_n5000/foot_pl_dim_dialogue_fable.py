#!/usr/bin/env python3
"""
storyworlds/worlds/foot_pl_dim_dialogue_fable.py
=================================================

A small fable-style story world about a dim footpath, a little traveler,
and a wiser helper who speaks in dialogue.

Seed theme:
- foot-pl-dim

This world is built as a tiny classical simulation:
- a path can be dim or bright
- a traveler can be brave, hasty, and unsteady
- a lantern can brighten the path
- a guide can advise, warn, and help
- the ending proves what changed in the world state

The story is intentionally fable-like: concrete, simple, and ending with a
clear lesson image.
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
    bearer: Optional[str] = None
    helps: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dark": 0.0, "rough": 0.0, "bright": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "bravery": 0.0, "patience": 0.0, "pride": 0.0, "gratitude": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hare", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old footpath"
    dim_level: int = 2
    hazards: set[str] = field(default_factory=lambda: {"stones", "roots"})
    affords: set[str] = field(default_factory=lambda: {"walk", "cross"})


@dataclass
class Choice:
    id: str
    verb: str
    gerund: str
    hazard: str
    stress: str
    remedy: str
    tag: str


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    burdens: set[str] = field(default_factory=set)
    plural: bool = False


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


def _r_dark(world: World) -> list[str]:
    out = []
    guide = world.entities.get("guide")
    lantern = world.entities.get("lantern")
    traveler = world.entities.get("traveler")
    if not guide or not lantern or not traveler:
        return out
    if lantern.bearer == traveler.id:
        return out
    if traveler.memes["worry"] < THRESHOLD:
        return out
    sig = ("dark",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.meters["dark"] += 1
    out.append("The footpath looked even dimmer to the little traveler.")
    return out


def _r_lantern(world: World) -> list[str]:
    out = []
    lantern = world.entities.get("lantern")
    traveler = world.entities.get("traveler")
    if not lantern or not traveler:
        return out
    if lantern.bearer != traveler.id:
        return out
    sig = ("bright",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.meters["bright"] += 1
    traveler.meters["dark"] = max(0.0, traveler.meters["dark"] - 1.0)
    out.append("The lantern made a small circle of bright gold on the stones.")
    return out


def _r_slow(world: World) -> list[str]:
    out = []
    traveler = world.entities.get("traveler")
    if not traveler:
        return out
    if traveler.memes["pride"] < THRESHOLD or traveler.meters["dark"] < THRESHOLD:
        return out
    sig = ("slow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.memes["patience"] += 1
    out.append("The dim path taught the traveler to slow down.")
    return out


CAUSAL_RULES = [_r_dark, _r_lantern, _r_slow]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def path_is_hard(setting: Setting, choice: Choice) -> bool:
    return choice.hazard in setting.hazards and setting.dim_level >= 2


def can_help(choice: Choice, aid: Aid) -> bool:
    return choice.tag in aid.helps


def predict(world: World, choice: Choice, aid: Optional[Aid]) -> dict:
    sim = world.copy()
    traveler = sim.get("traveler")
    traveler.memes["worry"] += 1
    if aid is not None:
        sim.get(aid.id).bearer = traveler.id
    if path_is_hard(sim.setting, choice):
        traveler.meters["rough"] += 1
        traveler.meters["dark"] += 1
    if aid is not None and choice.tag in aid.helps:
        traveler.meters["bright"] += 1
        traveler.memes["patience"] += 1
    return {"stumble": traveler.meters["rough"] > 0 and traveler.meters["bright"] == 0}


def intro(world: World, traveler: Entity) -> None:
    world.say(f"{traveler.id} was a small {traveler.type} who liked to go farther than the others.")
    world.say(f"{traveler.pronoun().capitalize()} trusted quick feet more than careful thoughts.")


def setting_line(world: World, choice: Choice) -> None:
    world.say(f"At dusk, {world.setting.place} grew quiet and long.")
    world.say(f"The stones felt rough, and the shadows on the path were {choice.stress}.")
    world.facts["dusk"] = True


def desire(world: World, traveler: Entity, choice: Choice) -> None:
    traveler.memes["bravery"] += 1
    traveler.memes["pride"] += 1
    world.say(f'"I can cross it alone," said {traveler.id}.')
    world.say(f'"I know the way," said {traveler.id}, and {traveler.pronoun()} stepped onto the {world.setting.place}.')


def warn(world: World, guide: Entity, traveler: Entity, choice: Choice) -> None:
    traveler.memes["worry"] += 1
    world.say(f'"The path is {choice.stress}," said {guide.id}. "Small feet should not rush here."')
    world.say(f'"I am not small in courage," said {traveler.id}.')
    propagate(world, narrate=False)


def stumble(world: World, traveler: Entity, choice: Choice) -> None:
    if traveler.meters["dark"] < THRESHOLD:
        return
    traveler.meters["rough"] += 1
    traveler.memes["worry"] += 1
    world.say(f"{traveler.id}'s foot slipped on a root.")
    world.say(f'"Oh!" {traveler.id} said. "The path is trickier than I thought."')


def offer_aid(world: World, guide: Entity, traveler: Entity, aid: Aid) -> None:
    world.say(f'"Take this {aid.label}," said {guide.id}. "{aid.phrase}"')
    if aid.plural:
        world.say(f"{guide.id} held it up so {traveler.id} could see the little light it could make.")
    traveler.memes["gratitude"] += 1


def accept_aid(world: World, traveler: Entity, aid: Aid) -> None:
    lantern = world.get(aid.id)
    lantern.bearer = traveler.id
    traveler.memes["patience"] += 1
    traveler.memes["worry"] = max(0.0, traveler.memes["worry"] - 1.0)
    world.say(f'"All right," said {traveler.id}, more softly now. "I will carry it."')
    world.say(f"{traveler.id} lifted the {aid.label} and the dim path began to shine.")
    propagate(world, narrate=True)


def ending(world: World, traveler: Entity, guide: Entity, aid: Aid) -> None:
    world.say(f"{traveler.id} crossed the last stones without hurrying.")
    world.say(f"At the end, {traveler.id} was still small, but {traveler.pronoun('possessive')} feet were sure.")
    world.say(f'{guide.id} smiled. "The brave one is not always the fastest," {guide.id} said.')
    world.say(f'"Sometimes," answered {traveler.id}, "the brave one is the one who takes the light."')


def tell(setting: Setting, choice: Choice, aid: Aid,
         traveler_name: str = "Pip", traveler_type: str = "fox",
         guide_name: str = "Moss", guide_type: str = "hare") -> World:
    world = World(setting)
    traveler = world.add(Entity(id=traveler_name, kind="character", type=traveler_type))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type))
    lantern = world.add(Entity(id=aid.id, type="lantern", label=aid.label, phrase=aid.phrase))
    lantern.bearer = None

    intro(world, traveler)
    world.para()
    setting_line(world, choice)
    desire(world, traveler, choice)
    warn(world, guide, traveler, choice)
    stumble(world, traveler, choice)
    world.para()
    offer_aid(world, guide, traveler, aid)
    accept_aid(world, traveler, aid)
    ending(world, traveler, guide, aid)

    world.facts.update(
        traveler=traveler,
        guide=guide,
        aid=aid,
        choice=choice,
        setting=setting,
        resolved=lantern.bearer == traveler.id,
        worry=traveler.memes["worry"],
        bright=traveler.meters["bright"],
        rough=traveler.meters["rough"],
    )
    return world


SETTINGS = {
    "footpath": Setting(place="the old footpath", dim_level=2, hazards={"stones", "roots"}, affords={"cross"}),
    "woodpath": Setting(place="the wood path", dim_level=2, hazards={"stones", "roots"}, affords={"cross"}),
    "hillpath": Setting(place="the hill path", dim_level=3, hazards={"stones", "roots"}, affords={"cross"}),
}

CHOICES = {
    "crossing": Choice(
        id="crossing",
        verb="cross the path",
        gerund="crossing the path",
        hazard="roots",
        stress="full of long shadows",
        remedy="a lantern",
        tag="cross",
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="It will make the stones easy to see.",
        helps={"cross"},
    ),
}

TRAVELER_NAMES = ["Pip", "Tala", "Nim", "Suri", "Bram", "Lio"]
GUIDE_NAMES = ["Moss", "Wren", "Ira", "Sol", "Fern"]


@dataclass
class StoryParams:
    place: str
    choice: str
    aid: str
    traveler_name: str
    traveler_type: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for choice_id, choice in CHOICES.items():
            if not path_is_hard(setting, choice):
                continue
            for aid_id, aid in AIDS.items():
                if can_help(choice, aid):
                    combos.append((place, choice_id, aid_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about a dim footpath, dialogue, and a useful light.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--traveler-name")
    ap.add_argument("--guide-name")
    ap.add_argument("--traveler-type", choices=["fox", "hare"])
    ap.add_argument("--guide-type", choices=["fox", "hare"])
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
    if args.choice and args.aid:
        choice, aid = CHOICES[args.choice], AIDS[args.aid]
        if not can_help(choice, aid):
            raise StoryError("That aid cannot help with that choice.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.choice is None or c[1] == args.choice)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, choice, aid = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        choice=choice,
        aid=aid,
        traveler_name=args.traveler_name or rng.choice(TRAVELER_NAMES),
        traveler_type=args.traveler_type or rng.choice(["fox", "hare"]),
        guide_name=args.guide_name or rng.choice(GUIDE_NAMES),
        guide_type=args.guide_type or "hare",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about "{f["choice"].stress}" and a traveler who learns to listen.',
        f"Tell a dialogue-heavy story where {f['traveler'].id} wants to cross {f['setting'].place} and a guide offers a lantern.",
        f"Write a child-friendly story with a dim footpath, a careful helper, and a lesson about slowing down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t, g, a, c = f["traveler"], f["guide"], f["aid"], f["choice"]
    return [
        QAItem(
            question=f"Who wanted to cross the dim path alone?",
            answer=f"{t.id}, the little {t.type}, wanted to cross alone at first.",
        ),
        QAItem(
            question=f"What did {g.id} offer to help on the footpath?",
            answer=f"{g.id} offered a {a.label} so {t.id} could see the stones better.",
        ),
        QAItem(
            question=f"Why did {t.id} begin to move more carefully?",
            answer=f"{t.id} slipped on a root, then took the lantern and learned to slow down.",
        ),
        QAItem(
            question=f"How did the story end for {t.id}?",
            answer=f"{t.id} crossed the path safely with the lantern, and the ending showed sure feet instead of hasty ones.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives off light so people can see in the dark.",
        ),
        QAItem(
            question="What does it mean for a path to be dim?",
            answer="A dim path is hard to see because there is not much light on it.",
        ),
        QAItem(
            question="Why should someone slow down on a rough path?",
            answer="Slowing down helps a traveler notice stones and roots before tripping.",
        ),
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        ms = {k: v for k, v in e.meters.items() if v}
        mem = {k: v for k, v in e.memes.items() if v}
        bits = []
        if ms:
            bits.append(f"meters={ms}")
        if mem:
            bits.append(f"memes={mem}")
        if e.bearer:
            bits.append(f"bearer={e.bearer}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
hard_path(P,C) :- place(P), choice(C), dim(P,D), D >= 2, hazard(C,H), hazard_in(P,H).
helps(A,C) :- aid(A), choice(C), aid_help(A,T), choice_tag(C,T).
valid(P,C,A) :- hard_path(P,C), helps(A,C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("dim", pid, s.dim_level))
        for h in sorted(s.hazards):
            lines.append(asp.fact("hazard_in", pid, h))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("hazard", cid, c.hazard))
        lines.append(asp.fact("choice_tag", cid, c.tag))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for t in sorted(a.helps):
            lines.append(asp.fact("aid_help", aid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CHOICES[params.choice],
        AIDS[params.aid],
        traveler_name=params.traveler_name,
        traveler_type=params.traveler_type,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
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
    StoryParams("footpath", "crossing", "lantern", "Pip", "fox", "Moss", "hare"),
    StoryParams("woodpath", "crossing", "lantern", "Tala", "hare", "Wren", "fox"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        for row in sorted(set(asp.atoms(model, "valid"))):
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
