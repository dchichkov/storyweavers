#!/usr/bin/env python3
"""
storyworlds/worlds/wax_scalp_smash_kindness_adventure.py
=========================================================

A standalone story world sketch for a small adventure about kindness,
using wax, scalp, and smash as physical anchors.

Seed story used to build the world model:
---
Kai was a small, kind-hearted explorer who loved the forest.
One day, Kai found a glowing jar of wax near an old tree stump.
The wax smelled like honey and pine. A little fox named Ember
had a scratch on her scalp from a thorny branch. Ember whimpered
softly. Kai wanted to help. Kai remembered a smooth stone that
could smash the wax into soft pieces. With the soft wax, Kai
gently smoothed the scratch on Ember's scalp. Ember wagged her
tail and nuzzled Kai's hand. They walked together to the sunny
glade, where the wax sparkled like treasure.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# Physical meter keys.
MESS_KINDS = {"sticky", "scratched", "sore"}


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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fox", "mother"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label


@dataclass
class Setting:
    place: str
    affords: set[str]


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    durability: int


@dataclass
class Creature:
    id: str
    type: str
    label: str
    phrase: str
    habitat: str
    injury: Optional[str] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_injury(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            sig = ("injury", actor.id, mess)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{actor.pronoun('possessive').capitalize()} {mess} spot still hurt.")
    return out


def _r_heal(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["healed"] >= THRESHOLD and actor.meters["hurt"] < THRESHOLD:
            sig = ("heal", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{actor.pronoun().capitalize()} felt better now.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="injury", apply=_r_injury),
    Rule(name="heal", apply=_r_heal),
]


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


def _smash_wax(world: World, tool: Entity, wax: Entity, actor: Entity) -> None:
    world.say(
        f"{actor.pronoun().capitalize()} lifted the {tool.label} and gave the wax a gentle "
        f"smash. The wax broke into soft, warm pieces."
    )
    wax.meters["smashed"] += 1
    tool.meters["used"] += 1


def _apply_wax(world: World, wax: Entity, creature: Entity, actor: Entity) -> None:
    world.say(
        f"{actor.pronoun().capitalize()} carefully smoothed the soft wax over the scratch "
        f"on {creature.pronoun('possessive')} scalp. The wax felt cool and kind."
    )
    creature.meters["healed"] += 1
    creature.meters["scratched"] = max(0.0, creature.meters["scratched"] - 1.0)
    actor.memes["kindness"] += 1
    propagate(world)


SETTINGS = {
    "forest": Setting(place="the deep forest", affords={"explore"}),
    "meadow": Setting(place="the sunny meadow", affords={"explore"}),
    "cave": Setting(place="the rocky cave", affords={"explore"}),
    "river": Setting(place="the winding river", affords={"explore"}),
}

ACTIVITIES = {
    "explore": Activity(
        id="explore",
        verb="explore the woods",
        gerund="exploring new paths",
        risk="scratched by thorns",
        mess="scratched",
        zone="scalp",
        keyword="explore",
    ),
}

TOOLS = {
    "stone": Tool(
        id="stone",
        label="smooth stone",
        phrase="a smooth, round stone that felt good in the hand",
        effect="smash",
        durability=3,
    ),
    "log": Tool(
        id="log",
        label="heavy log",
        phrase="a heavy, dry log from the forest floor",
        effect="smash",
        durability=2,
    ),
}

WAX = "wax"

CREATURES = {
    "fox": Creature(
        id="Ember",
        type="fox",
        label="little fox",
        phrase="a little fox with bright eyes",
        habitat="forest",
        injury="scratch on her scalp",
    ),
    "rabbit": Creature(
        id="Snow",
        type="rabbit",
        label="soft rabbit",
        phrase="a soft rabbit with a worried look",
        habitat="meadow",
        injury="sore spot on his scalp",
    ),
    "bear": Creature(
        id="Bramble",
        type="bear",
        label="small bear",
        phrase="a small bear with a thorn stuck in his scalp",
        habitat="cave",
        injury="scratch from a thorn",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, setting in SETTINGS.items():
        for act_id in setting.affords:
            for tool_id in TOOLS:
                for creature_id in CREATURES:
                    if CREATURES[creature_id].habitat == place_id:
                        combos.append((place_id, act_id, tool_id, creature_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    creature: str
    name: str
    seed: Optional[int] = None


GIRL_NAMES = ["Kai", "Maya", "Luna", "Stella", "Ivy"]
BOY_NAMES = ["Kai", "Finn", "Arlo", "Jace", "Remy"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[2] == args.tool)
              and (args.creature is None or c[3] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, tool, creature = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES)
    return StoryParams(
        place=place,
        activity=activity,
        tool=tool,
        creature=creature,
        name=name,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    tool_cfg = TOOLS[params.tool]
    creature_cfg = CREATURES[params.creature]

    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type="child",
        traits=["kind", "brave", "curious"],
    ))
    wax_entity = world.add(Entity(
        id="wax", kind="thing", type="wax", label="wax",
        phrase="a glowing jar of wax that smelled like honey and pine",
        held_by=hero.id,
    ))
    stone = world.add(Entity(
        id="stone", kind="thing", type=tool_cfg.id, label=tool_cfg.label,
        phrase=tool_cfg.phrase, held_by=hero.id,
    ))
    creature = world.add(Entity(
        id=creature_cfg.id, kind="character", type=creature_cfg.type,
        label=creature_cfg.label, phrase=creature_cfg.phrase,
    ))
    creature.meters["scratched"] = 1.0
    creature.meters["hurt"] = 1.0

    world.say(
        f"{hero.id} was a kind-hearted explorer who loved "
        f"{activity.gerund} in {setting.place}."
    )
    world.say(
        f"One day, {hero.pronoun()} found {wax_entity.phrase} near an old tree stump."
    )
    world.say(
        f"A {creature_cfg.label} named {creature.id} had a {creature_cfg.injury} "
        f"from a thorny branch. {creature.id} whimpered softly."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to help. {hero.pronoun().capitalize()} remembered "
        f"{stone.phrase} that could smash the wax into soft pieces."
    )
    _smash_wax(world, stone, wax_entity, hero)
    world.para()
    _apply_wax(world, wax_entity, creature, hero)
    world.say(
        f"{creature.id} wagged {creature.pronoun('possessive')} tail and nuzzled "
        f"{hero.pronoun('possessive')} hand."
    )
    world.say(
        f"They walked together to a sunny glade, where the wax sparkled like treasure."
    )

    world.facts.update(hero=hero, creature=creature, wax=wax_entity,
                       tool=stone, activity=activity, setting=setting,
                       creature_cfg=creature_cfg, tool_cfg=tool_cfg)
    return world


KNOWLEDGE = {
    "wax": [
        ("What is wax?",
         "Wax is a soft, smooth substance that can be heated or smashed into "
         "shapes. It can help soothe scratches."),
    ],
    "scalp": [
        ("What is a scalp?",
         "The scalp is the skin on top of your head, under your hair. It can "
         "get scratched just like other skin."),
    ],
    "smash": [
        ("What does it mean to smash something?",
         "To smash means to hit something gently so it breaks into smaller "
         "pieces. Here, the stone smashed the wax into soft bits."),
    ],
    "kindness": [
        ("What is kindness?",
         "Kindness is when you help someone who is hurt or sad. It makes both "
         "of you feel good."),
    ],
    "adventure": [
        ("What is an adventure?",
         "An adventure is a fun or exciting journey where you discover new "
         "things and help others along the way."),
    ],
}
KNOWLEDGE_ORDER = ["wax", "scalp", "smash", "kindness", "adventure"]


def generation_prompts(world: World) -> list[str]:
    kw = "wax"
    return [
        f'Write a short adventure story for a child about a kind explorer who '
        f'uses wax to help a hurt animal. Include the words "{kw}", "scalp", and "smash".',
        f"Tell a gentle story where a child finds a jar of wax and uses a stone "
        f"to smash it, then heals a creature's scratched scalp with kindness.",
        f'Write a simple story that uses the noun "{kw}" and ends with an act of kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, creature = f["hero"], f["creature"]
    place = world.setting.place
    creature_cfg = f["creature_cfg"]
    tool_cfg = f["tool_cfg"]
    qa = [
        QAItem(
            question=(
                f"Who found the glowing jar of wax in {place}?"
            ),
            answer=(
                f"A kind explorer named {hero.id} found the jar of wax near an "
                f"old tree stump in {place}."
            ),
        ),
        QAItem(
            question=(
                f"What was wrong with {creature.id} the {creature_cfg.label}?"
            ),
            answer=(
                f"{creature.id} had a scratch on {creature.pronoun('possessive')} scalp "
                f"from a thorny branch. {creature.pronoun().capitalize()} felt hurt and "
                f"whimpered."
            ),
        ),
        QAItem(
            question=(
                f"How did {hero.id} use the {tool_cfg.label} to help {creature.id}?"
            ),
            answer=(
                f"{hero.id} used the {tool_cfg.label} to smash the wax into soft pieces. "
                f"Then {hero.pronoun()} gently smoothed the wax over the scratch on "
                f"{creature.pronoun('possessive')} scalp."
            ),
        ),
        QAItem(
            question=(
                f"Why did {creature.id} nuzzle {hero.pronoun('possessive')} hand "
                f"after the wax was applied?"
            ),
            answer=(
                f"{creature.id} felt better because the wax soothed the scratch. "
                f"{creature.pronoun().capitalize()} was grateful for {hero.id}'s "
                f"kindness and showed it by nuzzling."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} and {creature.id} do at the end of the story?"
            ),
            answer=(
                f"They walked together to a sunny glade, where the wax sparkled "
                f"like treasure. They felt happy and safe together."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a kind adventure with wax, scalp, and smash.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Wax domain: a creature with a scratch on its scalp in a habitat that matches the setting.
needs_help(C) :- creature(C), scratched(C), in_habitat(C, H), setting(_, H).
affords(S, explore) :- setting(S, _).
has_tool(T) :- tool(T).
provides_smash(T) :- tool(T), effect(T, smash).
can_heal(C, T, W) :- needs_help(C), has_tool(T), provides_smash(T), wax(W).
valid(S, A, T, C) :- setting(S, H), in_habitat(C, H), creature(C), scratched(C), tool(T), can_heal(C, T, W), wax(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "explore"))
        for cid, creature in CREATURES.items():
            lines.append(asp.fact("creature", cid))
            lines.append(asp.fact("in_habitat", cid, creature.habitat))
            if creature.injury:
                lines.append(asp.fact("scratched", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("effect", tid, tool.effect))
    lines.append(asp.fact("wax", "wax"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="forest", activity="explore", tool="stone", creature="fox", name="Kai"),
    StoryParams(place="meadow", activity="explore", tool="stone", creature="rabbit", name="Maya"),
    StoryParams(place="cave", activity="explore", tool="log", creature="bear", name="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, tool, creature) combos:\n")
        for place, act, tool, creature in triples:
            print(f"  {place:9} {act:8} {tool:8} {creature:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.activity} in {p.place} (tool: {p.tool}, creature: {p.creature})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
