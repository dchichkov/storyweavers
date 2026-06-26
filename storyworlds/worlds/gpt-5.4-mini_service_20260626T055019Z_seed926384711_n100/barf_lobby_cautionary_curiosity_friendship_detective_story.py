#!/usr/bin/env python3
"""
storyworlds/worlds/barf_lobby_cautionary_curiosity_friendship_detective_story.py
================================================================================

A small detective-style story world about a curious friend in a lobby, a
cautionary clue, and a barf-related mystery that ends with friendship and a
careful choice.

Initial story premise:
---
A child detective visits a hotel lobby with a friend. They notice a strange smell
and a small splash of barf near the chairs. The curious friend wants to get
closer and solve the mystery right away, but the detective sees a warning sign:
the floor is slippery, the janitor is still bringing a mop bucket, and rushing
in could make things worse. After checking the clues, they realize the barf came
from a tired puppy who was scared by the crowd. They help the puppy, alert an
adult, and choose a safe path through the lobby together.

Causal state updates:
---
    curiosity + clue -> actor.memes["curiosity"] += 1
    caution sign / warning -> actor.memes["caution"] += 1
    risky approach near barf -> actor.meters["slip_risk"] += 1
    unsafe close inspection -> actor.meters["mess"] += 1
    helper + gentle plan -> actor.memes["trust"] += 1
    solved clue -> actor.memes["pride"] += 1 ; friendship += 1

Narrative instruments:
---
    - Detective Story: clue collection, reasoning, reveal, and a tidy resolution
    - Cautionary: the world rewards careful choices and honest warnings
    - Curiosity: the child wants to inspect, sniff, and learn
    - Friendship: the friend pair cooperate, share clues, and help the smaller creature
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    near: Optional[str] = None
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
    place: str = "the lobby"
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue: str
    danger: str
    rush: str
    reveal: str
    mess: str
    zone: set[str]
    keyword: str = "barf"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone


def _r_curiosity(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("clue_seen", 0.0) < THRESHOLD:
            continue
        sig = ("curious,clue", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["pride"] = actor.memes.get("pride", 0.0) + 0.5
        out.append(f"{actor.id} leaned closer to the clue, hoping to understand it.")
    return out


def _r_risk(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("messy_closeup", 0.0) < THRESHOLD:
            continue
        sig = ("risk", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["slip_risk"] = actor.meters.get("slip_risk", 0.0) + 1
        out.append(f"That was risky in the lobby's slick spot.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    hero = world.entities.get("Hero")
    pal = world.entities.get("Pal")
    if not hero or not pal:
        return out
    if hero.memes.get("trust", 0.0) >= THRESHOLD and pal.memes.get("trust", 0.0) >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
            pal.memes["friendship"] = pal.memes.get("friendship", 0.0) + 1
            out.append("The two friends felt braver because they were working together.")
    return out


CAUSAL_RULES = [_r_curiosity, _r_risk, _r_friendship]


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


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was bright, with chairs, a desk, and a shiny floor."


def predict_mess(world: World, actor: Entity, case: Case) -> dict:
    sim = world.copy()
    _do_investigate(sim, sim.get(actor.id), case, narrate=False)
    return {
        "messy_closeup": sim.get(actor.id).meters.get("messy_closeup", 0.0),
        "slip_risk": sim.get(actor.id).meters.get("slip_risk", 0.0),
    }


def _do_investigate(world: World, actor: Entity, case: Case, narrate: bool = True) -> None:
    actor.memes["clue_seen"] = actor.memes.get("clue_seen", 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    actor.meters["messy_closeup"] = actor.meters.get("messy_closeup", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, pal: Entity) -> None:
    world.say(
        f"{hero.id} was a little detective who loved clues, and {pal.id} was the kind of friend who "
        f"always wanted to help."
    )
    world.say(f"{hero.id} loved careful mysteries, and {pal.id} loved asking why.")
    world.say(setting_detail(world.setting))


def arrival(world: World, hero: Entity, pal: Entity, case: Case) -> None:
    world.say(
        f"One afternoon, {hero.id} and {pal.id} came into the lobby and noticed a strange smell near the chairs."
    )
    world.say(f"There was a small {case.keyword} stain by the wall, and that made the whole place feel like a case.")


def caution(world: World, hero: Entity, pal: Entity, case: Case) -> bool:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    pal.memes["caution"] = pal.memes.get("caution", 0.0) + 1
    world.say(
        f"{hero.id} pointed to a warning cone and said, \"Easy now. {case.danger}\""
    )
    return True


def curiosity(world: World, hero: Entity, pal: Entity, case: Case) -> None:
    world.say(
        f"{pal.id} wanted to rush over and sniff the clue, but {hero.id} said, "
        f"\"Let's look first and step carefully.\""
    )
    _do_investigate(world, pal, case, narrate=True)


def warn_and_hold_back(world: World, hero: Entity, pal: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} kept {pal.id} from slipping into the mess and led {pal.it()} around the slick patch."
    )
    pal.memes["trust"] = pal.memes.get("trust", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1


def reveal(world: World, hero: Entity, pal: Entity, case: Case) -> None:
    world.say(
        f"After checking the paw prints and the dropped paper cup, {hero.id} solved it: {case.reveal}"
    )
    world.say(
        f"{pal.id} gasped, then smiled, because the mystery had an answer and nobody had made the lobby mess worse."
    )


def help_out(world: World, hero: Entity, pal: Entity, adult: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} told {adult.id} right away, and {pal.id} held the little puppy's blanket while the adult cleaned up."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    pal.memes["pride"] = pal.memes.get("pride", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    pal.memes["friendship"] = pal.memes.get("friendship", 0.0) + 1


def ending(world: World, hero: Entity, pal: Entity, case: Case) -> None:
    world.say(
        f"In the end, the lobby smelled cleaner, {pal.id} walked more carefully, and {hero.id} had a good new friend beside {hero.pronoun('object')}."
    )


def tell(setting: Setting, case: Case, hero_name: str = "Milo", pal_name: str = "Nia") -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type="boy", label=hero_name,
                            traits=["little", "detective"]))
    pal = world.add(Entity(id="Pal", kind="character", type="girl", label=pal_name,
                           traits=["curious", "friendly"]))
    adult = world.add(Entity(id="Adult", kind="character", type="woman", label="the clerk"))
    spill = world.add(Entity(id="Spill", type="thing", label="barf stain", owner="puppy"))
    intro(world, hero, pal)
    world.para()
    arrival(world, hero, pal, case)
    caution(world, hero, pal, case)
    curiosity(world, hero, pal, case)
    warn_and_hold_back(world, hero, pal, case)
    world.para()
    reveal(world, hero, pal, case)
    help_out(world, hero, pal, adult, case)
    ending(world, hero, pal, case)
    world.facts.update(hero=hero, pal=pal, adult=adult, case=case, spill=spill, setting=setting)
    return world


SETTINGS = {
    "lobby": Setting(place="the lobby", affords={"barf_case"}),
}

CASES = {
    "barf_case": Case(
        id="barf_case",
        clue="a strange smell and a small splash of barf",
        danger="The floor is slippery, so a fast step could make a mess bigger.",
        rush="run straight to the stain",
        reveal="a tired puppy got scared by the crowd and got sick near the chairs",
        mess="barf",
        zone={"floor"},
        keyword="barf",
        tags={"barf", "lobby", "detective", "curiosity", "friendship"},
    ),
}

GEAR = [
    Gear(
        id="shoes",
        label="non-slip shoes",
        covers={"feet"},
        guards={"barf"},
        prep="put on non-slip shoes first",
        tail="walked back through the lobby in safe steps",
    ),
    Gear(
        id="gloves",
        label="clean gloves",
        covers={"hands"},
        guards={"barf"},
        prep="put on clean gloves before touching anything",
        tail="finished the clue check without getting messy",
    ),
]

NAMES_BOY = ["Milo", "Theo", "Sam", "Jude", "Ezra"]
NAMES_GIRL = ["Nia", "Ivy", "Leah", "Zoe", "Mina"]


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for case in setting.affords:
            combos.append((place, case))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: barf, lobby, caution, curiosity, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)]
    if not combos:
        raise StoryError("No valid combo matches the given options.")
    place, case = rng.choice(combos)
    name = args.name or rng.choice(NAMES_BOY)
    friend = args.friend or rng.choice(NAMES_GIRL)
    return StoryParams(place=place, case=case, name=name, friend=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about barf in the lobby, with caution and friendship.',
        f"Tell a gentle mystery where {f['hero'].label} and {f['pal'].label} find a clue in {f['setting'].place} and solve it carefully.",
        f'Write a simple story that includes the words "barf" and "lobby" and ends with friends helping instead of rushing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, pal, case = f["hero"], f["pal"], f["case"]
    return [
        QAItem(
            question=f"Who was the detective in the lobby story?",
            answer=f"{hero.label} was the little detective, and {pal.label} was the friend who helped solve the mystery.",
        ),
        QAItem(
            question=f"What clue did the children notice in the lobby?",
            answer=f"They noticed a strange smell and a small splash of {case.keyword} near the chairs.",
        ),
        QAItem(
            question=f"Why didn't {pal.label} rush straight to the stain?",
            answer=f"Because {hero.label} warned that the floor was slippery and rushing could make the mess worse.",
        ),
        QAItem(
            question=f"What was the real reason for the barf in the lobby?",
            answer=f"The real answer was that a tired puppy got scared by the crowd and got sick near the chairs.",
        ),
        QAItem(
            question=f"How did the friends help at the end?",
            answer=f"They told the adult right away, helped keep the area calm, and stayed careful together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lobby?",
            answer="A lobby is a room near the entrance of a building where people wait, meet, or walk through on their way somewhere else.",
        ),
        QAItem(
            question="Why should people be careful around barf?",
            answer="People should be careful around barf because it is messy, can smell bad, and can make a floor slippery.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, thinks about what they mean, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means helping each other, sharing trust, and being kind together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A case is valid when the lobby affords it.
valid(Place, Case) :- affords(Place, Case).

% A cautionary mystery has clues, a warning, and friendship in the result.
cautionary_case(Case) :- clue(Case, _), danger(Case, _).
curious_case(Case) :- clue(Case, _).
friendship_case(Case) :- resolve(Case, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("clue", cid, c.clue))
        lines.append(asp.fact("danger", cid, c.danger))
        lines.append(asp.fact("resolve", cid, c.reveal))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def explain_rejection() -> str:
    return "(No story: the requested lobby detective mystery needs the barf case in the lobby.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CASES[params.case], params.name, params.friend)
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
    StoryParams(place="lobby", case="barf_case", name="Milo", friend="Nia"),
    StoryParams(place="lobby", case="barf_case", name="Theo", friend="Ivy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c in combos:
            print(f"  {p:8} {c:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
