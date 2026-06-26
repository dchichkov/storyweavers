#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/sleep_bad_ending_problem_solving_reconciliation_pirate.py
==============================================================================================================================

A small pirate tale story world about sleep, a bad ending, problem solving,
and reconciliation.

The seed idea:
- A little pirate wants to sleep.
- Something goes wrong aboard the ship.
- The crew must solve the problem.
- A bad ending is avoided, and the pirates make peace again.

This script follows the Storyweavers storyworld contract:
- standalone stdlib storyworld script
- typed entities with meters and memes
- deterministic world simulation drives prose
- inline ASP twin plus Python reasonableness gate
- story, QA, trace, JSON, verification, and ASP modes
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
    location: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the ship"
    sea: str = "calm"
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SleepGear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trouble: Optional[Trouble] = None

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.trouble = self.trouble
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    trouble: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "dock": Setting(place="the dock", sea="calm", affords={"storm", "snore", "fog"}),
    "ship": Setting(place="the ship", sea="rocky", affords={"storm", "snore", "fog"}),
    "cabin": Setting(place="the cabin", sea="windy", affords={"snore", "fog"}),
}

TROUBLES = {
    "storm": Trouble(
        id="storm",
        verb="sleep through the storm",
        gerund="sleeping through the storm",
        rush="dash toward the deck",
        danger="wet and rattling",
        fix_hint="a dry bunk and a snug blanket",
        tags={"sea", "wet", "loud"},
    ),
    "snore": Trouble(
        id="snore",
        verb="sleep while the other pirate snores",
        gerund="trying to sleep beside the snoring",
        rush="cover their ears",
        danger="loud and stubborn",
        fix_hint="a pillow wall and a quiet turn",
        tags={"loud", "sleep"},
    ),
    "fog": Trouble(
        id="fog",
        verb="sleep while the fog rolls in",
        gerund="sleeping under the foggy sky",
        rush="light every lantern",
        danger="cold and blurry",
        fix_hint="a lantern watch and a warm blanket",
        tags={"fog", "sleep"},
    ),
}

GUTS = {
    "blanket": SleepGear(
        id="blanket",
        label="a thick blanket",
        phrase="a thick blanket",
        guards={"wet", "cold"},
        covers={"body"},
        prep="tuck the little pirate into a thick blanket",
        tail="tucked the little pirate into the thick blanket",
    ),
    "earplugs": SleepGear(
        id="earplugs",
        label="soft earplugs",
        phrase="soft earplugs",
        guards={"loud"},
        covers={"ears"},
        prep="fit soft earplugs into the little pirate's ears",
        tail="fit soft earplugs into the little pirate's ears",
        plural=True,
    ),
    "lantern": SleepGear(
        id="lantern",
        label="a lantern watch",
        phrase="a lantern watch",
        guards={"fog"},
        covers={"deck"},
        prep="set a lantern watch by the rail",
        tail="set a lantern watch by the rail",
    ),
}

PIRATE_NAMES = ["Mina", "Jory", "Nell", "Pip", "Rosa", "Toby", "Finn", "Mara"]
TRAITS = ["brave", "sly", "cheerful", "curious", "stubborn", "tiny"]


def trouble_needs(trouble: Trouble, gear: SleepGear) -> bool:
    return bool(trouble.tags & gear.guards)


def select_gear(trouble: Trouble) -> Optional[SleepGear]:
    for gear in GUTS.values():
        if trouble_needs(trouble, gear):
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for trouble_id in setting.affords:
            trouble = TROUBLES[trouble_id]
            gear = select_gear(trouble)
            if gear is not None:
                out.append((place, trouble_id, gear.id))
    return out


def setting_detail(setting: Setting, trouble: Trouble) -> str:
    if trouble.id == "storm":
        return f"The ship rocked as the sea growled outside the hull."
    if trouble.id == "snore":
        return f"The cabin was cramped, and every snore bounced off the boards."
    return f"The fog pressed close, like a gray blanket over the water."


def _do_trouble(world: World, actor: Entity, trouble: Trouble, narrate: bool = True) -> None:
    actor.memes["tired"] = actor.memes.get("tired", 0.0) + 1
    actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
    if trouble.id == "storm":
        actor.meters["wet"] = actor.meters.get("wet", 0.0) + 1
    if trouble.id == "snore":
        actor.memes["frustration"] = actor.memes.get("frustration", 0.0) + 1
    if trouble.id == "fog":
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} could not rest because of the {trouble.id}.")


def predict_bad_ending(world: World, actor: Entity, trouble: Trouble, gear: SleepGear) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(actor.id), trouble, narrate=False)
    bad = False
    if trouble.id == "storm":
        bad = True
    if trouble.id == "snore":
        bad = True
    if trouble.id == "fog":
        bad = True
    return {"bad": bad}


def tell(setting: Setting, trouble: Trouble, gear: SleepGear, hero_name: str,
         parent_type: str = "captain", trait: str = "brave") -> World:
    world = World(setting)
    world.trouble = trouble

    hero = world.add(Entity(id=hero_name, kind="character", type="girl", meters={}, memes={}))
    hero.memes["sleepy"] = 1.0
    hero.memes["hope"] = 1.0
    hero.traits = [trait, "tiny"]  # type: ignore[attr-defined]

    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(
        id="bed",
        type="thing",
        label="bed",
        phrase="a small bunk with a pillow",
        owner=hero.id,
        caretaker=parent.id,
        location="below deck",
    ))
    gear_ent = world.add(Entity(
        id=gear.id,
        type="thing",
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        plural=gear.plural,
    ))

    hero.worn_by = hero.id  # harmless placeholder for ownership-like narration

    # Act 1: a pirate wants sleep.
    world.say(f"Little {trait} pirate {hero.id} lived aboard {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} was so sleepy that {hero.pronoun('subject')} wanted to rest right away.")
    world.say(f"{hero.id} loved {prize.phrase} and curled up whenever the ship grew quiet.")

    # Act 2: bad ending threatens.
    world.para()
    world.say(setting_detail(setting, trouble))
    world.say(f"But just then, the {trouble.id} made sleep hard.")
    world.say(f"{hero.id} wanted to {trouble.verb}, yet the trouble kept tugging at {hero.pronoun('possessive')} eyelids.")
    pred = predict_bad_ending(world, hero, trouble, gear)
    world.facts["predicted_bad"] = pred["bad"]
    if pred["bad"]:
        world.say(f"{parent.label} frowned and said, \"If we do nothing, this could end badly.\"")

    # Problem solving.
    world.para()
    world.say(f"{hero.id} whispered, \"What can we do?\"")
    world.say(f"{parent.label.capitalize()} thought hard and chose {gear.label}.")
    world.say(f"{parent.label.capitalize()} said, \"{gear.prep}, and we can keep the night calm.\"")

    gear_ent.worn_by = hero.id

    # Reconciliation.
    hero.memes["frustration"] = 0.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.memes["peace"] = 1.0
    parent.memes["peace"] = 1.0

    world.say(f"{hero.id} stopped fussing and nodded.")
    world.say(f"Together they solved the problem, and the night softened again.")
    world.say(f"By the end, {gear.tail}, and {hero.id} finally slept.")
    world.say(f"The bad ending was avoided, and {hero.id} and {parent.label} made peace before dawn.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        gear=gear_ent,
        setting=setting,
        trouble=trouble,
        resolved=True,
        bad_ending=False,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    return [
        f'Write a short pirate story for a young child about {hero.id} trying to sleep during a {trouble.id}.',
        f"Tell a tiny pirate tale where a sleepy pirate faces a problem, solves it, and makes peace again.",
        f'Write a story that includes the word "sleep" and ends with a calm pirate night after trouble is fixed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    trouble = f["trouble"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"Who wanted to sleep in the pirate story?",
            answer=f"{hero.id}, the little pirate, wanted to sleep.",
        ),
        QAItem(
            question=f"What problem kept {hero.id} awake?",
            answer=f"The {trouble.id} kept the little pirate from resting.",
        ),
        QAItem(
            question=f"What did {parent.label} use to help solve the problem?",
            answer=f"{parent.label.capitalize()} used {gear.label} to help make the night calm again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finally sleeping and {hero.id} and {parent.label} making peace.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble: Trouble = f["trouble"]
    gear: Entity = f["gear"]
    items = [
        QAItem(
            question="What does sleep do for a child?",
            answer="Sleep helps a child rest, grow, and wake up with more energy.",
        ),
    ]
    if trouble.id == "storm":
        items.append(QAItem(
            question="Why can a storm make sleep hard on a ship?",
            answer="A storm can shake the ship, make loud sounds, and keep a child awake.",
        ))
    if trouble.id == "snore":
        items.append(QAItem(
            question="Why do soft earplugs help?",
            answer="Soft earplugs help by blocking some loud sounds so a person can rest.",
        ))
    if trouble.id == "fog":
        items.append(QAItem(
            question="Why can a lantern watch help in fog?",
            answer="A lantern watch gives light, which helps people see and feel safer in fog.",
        ))
    if gear.label == "a thick blanket":
        items.append(QAItem(
            question="What is a blanket for?",
            answer="A blanket helps keep someone warm and cozy while sleeping.",
        ))
    return items


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", trouble="storm", prize="blanket", name="Mina", parent="captain", trait="brave"),
    StoryParams(place="cabin", trouble="snore", prize="earplugs", name="Pip", parent="captain", trait="tiny"),
    StoryParams(place="dock", trouble="fog", prize="lantern", name="Nell", parent="captain", trait="curious"),
]


KNOWLEDGE = {
    "sleep": [
        ("Why do children sleep?", "Children sleep so their bodies and minds can rest and grow."),
    ],
    "storm": [
        ("What is a storm?", "A storm is very rough weather with wind, rain, and loud sounds."),
    ],
    "snore": [
        ("What is snoring?", "Snoring is a loud noise some people make when they sleep."),
    ],
    "fog": [
        ("What is fog?", "Fog is a cloud near the ground that makes it hard to see."),
    ],
    "blanket": [
        ("What does a blanket do?", "A blanket helps keep someone warm and cozy."),
    ],
    "earplugs": [
        ("What are earplugs?", "Earplugs are small soft pieces that help block loud sounds."),
    ],
    "lantern": [
        ("What is a lantern?", "A lantern is a lamp that helps people see in the dark."),
    ],
}


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for gid, g in GUTS.items():
        lines.append(asp.fact("gear", gid))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


ASP_RULES = r"""
% A trouble is solvable when some gear guards one of its danger tags.
solvable(T, G) :- trouble(T), gear(G), tag(T, M), guards(G, M).

valid_story(S, T, G) :- affords(S, T), solvable(T, G).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return asp_valid_stories()


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate sleep story world with a bad ending, problem solving, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=GUTS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.trouble and args.prize:
        trouble = TROUBLES[args.trouble]
        gear = GUTS[args.prize]
        if not trouble_needs(trouble, gear):
            raise StoryError("The chosen gear does not solve that pirate trouble.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.trouble is None or c[1] == args.trouble)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid pirate sleep story matches those options.")
    place, trouble_id, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(PIRATE_NAMES)
    parent = args.parent or "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble_id, prize=prize_id, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TROUBLES[params.trouble], GUTS[params.prize], params.name, params.parent, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, trouble, gear in stories:
            print(f"  {place:6} {trouble:8} {gear}")
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
            header = f"### {p.name}: {p.trouble} at {p.place} (gear: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
