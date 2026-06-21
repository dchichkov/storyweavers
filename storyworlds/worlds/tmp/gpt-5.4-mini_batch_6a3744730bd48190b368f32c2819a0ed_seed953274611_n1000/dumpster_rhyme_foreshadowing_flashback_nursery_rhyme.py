#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dumpster_rhyme_foreshadowing_flashback_nursery_rhyme.py
======================================================================================

A small standalone storyworld in a nursery-rhyme voice.

Premise
-------
A child and a grown-up notice a clink-clink by a dumpster at dusk. A foreshadowing
line hints that something tiny has been left behind, and a flashback shows why the
child knows exactly what to look for. The search ends with a sweet recovery: a lost
toy is found, cleaned up, and tucked safely away.

This world keeps the prose child-facing, rhythmic, and concrete. It uses a tiny
simulated state with physical meters and emotional memes, plus a simple forward
model, QA generation from world state, and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    dusk_line: str
    dump_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    tiny: bool = True
    dirtyable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    clue: str
    flashback: str
    find_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "alley"
    lost: str = "ribbon"
    action: str = "search"
    hero: str = "Maya"
    hero_gender: str = "girl"
    parent: str = "mother"
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("lost_item").meters["lost"] >= THRESHOLD and ("worry", "parent") not in world.fired:
        world.fired.add(("worry", "parent"))
        world.get("parent").memes["worry"] += 1
        out.append("The grown-up's heart went thump and thump.")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    lost = world.get("lost_item")
    if lost.meters["found"] >= THRESHOLD and ("found", lost.id) not in world.fired:
        world.fired.add(("found", lost.id))
        world.get("hero").memes["joy"] += 1
        world.get("parent").memes["relief"] += 1
        out.append("The worry turned light as a feather.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("find", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def forward_scan(world: World) -> dict:
    sim = world.copy()
    sim.get("lost_item").meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("lost_item").meters["found"] >= THRESHOLD,
        "relief": sim.get("parent").memes["relief"],
    }


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def setting_line(setting: Setting) -> str:
    return f"In {setting.place}, by the dumpster, the dusk grew dim and gray."


def foreshadow_line(setting: Setting, lost: LostThing) -> str:
    return f"But something small went missing, and the wind said, 'Listen close today.'"


def flashback_line(action: Action, hero: Entity, lost: LostThing) -> str:
    return action.flashback.format(hero=hero.id, lost=lost.label)


def search_line(hero: Entity, action: Action, lost: LostThing) -> str:
    return f"{hero.id} followed the clue clue-clue, by the bins and the bricks, to look for {lost.phrase}."


def recover_line(hero: Entity, parent: Entity, lost: LostThing, action: Action) -> str:
    return action.find_text.format(hero=hero.id, parent=parent.label_word, lost=lost.label)


def tidy_line(hero: Entity, parent: Entity, lost: LostThing) -> str:
    return f"They brushed it clean, hugged it tight, and tucked it safe away at night."


def tell(setting: Setting, lost: LostThing, action: Action, hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    item = world.add(Entity(id="lost_item", kind="thing", type="toy", label=lost.label, phrase=lost.phrase))
    world.add(Entity(id="setting", kind="thing", type="place", label=setting.place))
    hero.memes["curious"] += 1
    item.meters["lost"] += 1

    world.say(setting_line(setting))
    world.say(f"A clink at the dumpster winked like a blink; {foreshadow_line(setting, lost)}")
    world.say(flashback_line(action, hero, lost))

    world.para()
    world.say(search_line(hero, action, lost))
    scan = forward_scan(world)
    if scan["found"]:
        world.say(recover_line(hero, parent, lost, action))
        item.meters["found"] += 1
        item.meters["clean"] += 1
        propagate(world, narrate=True)
        world.para()
        world.say(tidy_line(hero, parent, lost))
        world.say(f"{hero.id} smiled so wide, like a star in the tide, and home they went with cheer.")
    else:
        world.say(f"But the little thing stayed hidden, and the night felt wide and near.")
        world.say(f"So {parent.label_word.capitalize()} said, 'We'll try again in the morning, dear.'")

    world.facts.update(
        setting=setting,
        lost=lost,
        action=action,
        hero=hero,
        parent=parent,
        outcome="found" if item.meters["found"] >= THRESHOLD else "missed",
    )
    return world


SETTINGS = {
    "alley": Setting(id="alley", place="the alley", dusk_line="by the dumpster", dump_line="the old dumpster"),
    "yard": Setting(id="yard", place="the back yard", dusk_line="near the fence", dump_line="the green dumpster"),
    "lane": Setting(id="lane", place="the little lane", dusk_line="by the curb", dump_line="the dented dumpster"),
}

LOST_THINGS = {
    "ribbon": LostThing(id="ribbon", label="ribbon", phrase="a red ribbon"),
    "button": LostThing(id="button", label="button", phrase="a shiny button"),
    "bear": LostThing(id="bear", label="bear", phrase="a tiny teddy bear"),
}

ACTIONS = {
    "search": Action(
        id="search",
        verb="search",
        clue="clue-clue",
        flashback="And {hero} remembered: at noon, {lost} slipped from a little coat.",
        find_text="{parent} lifted the lid, and there was {lost}, all curled in a nest of leaves.",
    ),
    "peek": Action(
        id="peek",
        verb="peek",
        clue="peek-peek",
        flashback="And {hero} remembered: in the playroom, {lost} rolled under a chair.",
        find_text="{parent} peered inside, and there was {lost}, sitting shy and snug.",
    ),
}

CURATED = [
    StoryParams(setting="alley", lost="ribbon", action="search", hero="Maya", hero_gender="girl", parent="mother"),
    StoryParams(setting="yard", lost="button", action="peek", hero="Noah", hero_gender="boy", parent="father"),
    StoryParams(setting="lane", lost="bear", action="search", hero="Luna", hero_gender="girl", parent="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, l, a) for s in SETTINGS for l in LOST_THINGS for a in ACTIONS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with dumpster, foreshadowing, and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.lost is None or c[1] == args.lost)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, lost, action = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Maya", "Luna", "Noah", "Ivy"])
    gender = args.gender or ("boy" if hero in {"Noah"} else "girl")
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, lost=lost, action=action, hero=hero, hero_gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("lost", LOST_THINGS), ("action", ACTIONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(SETTINGS[params.setting], LOST_THINGS[params.lost], ACTIONS[params.action],
                 params.hero, params.hero_gender, params.parent)
    return StorySample(
        params=params,
        story=clean_text(world.render()),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story that includes the word "dumpster" and a lost {f["lost"].label}.',
        f"Tell a soft, rhyming story where {f['hero'].id} remembers a flashback and finds {f['lost'].phrase} near a dumpster.",
        f"Write a gentle flashback-and-foreshadowing story for little kids with a happy ending by the dumpster.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, parent, lost = f["hero"], f["parent"], f["lost"]
    return [
        ("Where did the story happen?",
         f"It happened near a dumpster, in {f['setting'].place}. The dumpster is the place that made the clue feel important."),
        ("What was missing?",
         f"{lost.phrase} was missing. That is why the story needed a careful search."),
        (f"What did {hero.id} remember in the flashback?",
         f"{hero.id} remembered how {lost.label} slipped away earlier. That memory helped {hero.id} know where to look."),
        ("How did the story end?",
         f"It ended happily, with the lost thing found and cleaned up. Then everyone went home with a calm, snug feeling."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dumpster?",
         "A dumpster is a big container where trash is kept until it is taken away."),
        ("What is a flashback?",
         "A flashback is a quick return to something that happened earlier in the story."),
        ("What is foreshadowing?",
         "Foreshadowing is a clue that hints something important will happen later."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
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
    bits = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id}: meters={dict(meters)} memes={dict(memes)}")
    bits.append(f"fired={sorted(world.fired)}")
    return "\n".join(bits)


ASP_RULES = r"""
valid(S,L,A) :- setting(S), lost(L), action(A).
outcome(found) :- chosen(C), C = found.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for l in LOST_THINGS:
        lines.append(asp.fact("lost", l))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: ASP parity and story smoke test passed.")
    return rc


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(" ".join(map(str, t)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
