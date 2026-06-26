#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero tale built around an
apparent misunderstanding and a reconciliation with a parent.

The premise is classical and child-facing:
- a young hero wants to help
- something looks wrong at first
- the parent misunderstands the hero's actions
- the hero explains, the parent realizes the truth
- they reconcile and finish with a warm, concrete ending image
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTINGS = {
    "city": {
        "place": "the city square",
        "scene": "under the bright buildings",
        "keywords": {"city", "square", "street"},
    },
    "park": {
        "place": "the park",
        "scene": "by the tall slide and the pond",
        "keywords": {"park", "pond", "trees"},
    },
    "harbor": {
        "place": "the harbor",
        "scene": "by the water and the docks",
        "keywords": {"harbor", "dock", "water"},
    },
    "market": {
        "place": "the market",
        "scene": "between stalls of fruit and ribbons",
        "keywords": {"market", "stall", "fruit"},
    },
}

HEROES = {
    "spark": {
        "name": "Nova",
        "type": "child hero",
        "genders": {"girl"},
        "power": "shiny sparks",
        "tool": "a small spark shield",
    },
    "glide": {
        "name": "Finn",
        "type": "child hero",
        "genders": {"boy"},
        "power": "quick gusts",
        "tool": "a bright glide cape",
    },
    "echo": {
        "name": "Mina",
        "type": "child hero",
        "genders": {"girl"},
        "power": "tiny echo sounds",
        "tool": "a badge that chimed softly",
    },
}

ACTIONS = {
    "lift": {
        "verb": "lift the fallen crate",
        "gerund": "lifting the fallen crate",
        "motion": "dash toward the crate",
        "apparent": "looked like",
        "risk": "messing up the market",
        "effect": "tugged the crate just enough to keep it from slipping",
        "power": "strength",
    },
    "guide": {
        "verb": "guide the lost kitten",
        "gerund": "guiding the lost kitten",
        "motion": "run after the kitten",
        "apparent": "looked like",
        "risk": "chasing in a wild way",
        "effect": "used a calm path and a soft whistle",
        "power": "care",
    },
    "catch": {
        "verb": "catch the rolling ball",
        "gerund": "catching the rolling ball",
        "motion": "sprint after the ball",
        "apparent": "looked like",
        "risk": "causing a bigger spill",
        "effect": "stopped the ball before it hit the fountain",
        "power": "speed",
    },
    "save": {
        "verb": "save the old kite",
        "gerund": "saving the old kite",
        "motion": "leap up to the kite",
        "apparent": "looked like",
        "risk": "snatching without thinking",
        "effect": "caught the kite string before it tore",
        "power": "bravery",
    },
}

OBJECTS = {
    "crate": {
        "label": "crate",
        "phrase": "the heavy wooden crate",
        "risk": "it might tip over",
        "safe": "it needed a steady pull",
    },
    "kitten": {
        "label": "kitten",
        "phrase": "the tiny striped kitten",
        "risk": "it might get frightened",
        "safe": "it needed a quiet voice",
    },
    "ball": {
        "label": "ball",
        "phrase": "the red ball",
        "risk": "it might roll into trouble",
        "safe": "it needed a quick stop",
    },
    "kite": {
        "label": "kite",
        "phrase": "the blue kite",
        "risk": "it might tear in the wind",
        "safe": "it needed a careful grab",
    },
}

PARENTS = {
    "mother": "mother",
    "father": "father",
    "parent": "parent",
}

NAMES = {
    "girl": ["Nova", "Mina", "Ruby", "Ada", "Luna"],
    "boy": ["Finn", "Theo", "Max", "Leo", "Jude"],
}

TRAITS = ["brave", "curious", "kind", "restless", "helpful", "careful"]


# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def capitalized_subject(self) -> str:
        return self.pronoun("subject").capitalize()


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    keywords: set[str]


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    motion: str
    apparent: str
    risk: str
    effect: str
    power: str


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    risk: str
    safe: str


@dataclass
class StoryParams:
    setting: str
    action: str
    object: str
    hero_name: str
    hero_gender: str
    parent_role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_setting(setting_id: str) -> Setting:
    s = SETTINGS[setting_id]
    return Setting(id=setting_id, place=s["place"], scene=s["scene"], keywords=set(s["keywords"]))


def build_action(action_id: str) -> Action:
    a = ACTIONS[action_id]
    return Action(**{**a, "id": action_id})


def build_object(object_id: str) -> ObjectSpec:
    o = OBJECTS[object_id]
    return ObjectSpec(id=object_id, **o)


def run_story(params: StoryParams) -> World:
    setting = build_setting(params.setting)
    action = build_action(params.action)
    obj = build_object(params.object)

    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        label=params.hero_name,
        memes={"hope": 1.0, "concern": 0.0, "reconciliation": 0.0, "misunderstanding": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_role,
        label=f"the {params.parent_role}",
        memes={"concern": 1.0, "worry": 0.0, "trust": 0.0, "reconciliation": 0.0, "joy": 0.0},
    ))
    thing = world.add(Entity(
        id=obj.id,
        kind="thing",
        type=obj.id,
        label=obj.label,
        phrase=obj.phrase,
        caretaker=parent.id,
    ))

    world.facts.update(hero=hero, parent=parent, thing=thing, action=action, setting=setting, object=obj)

    world.say(
        f"{hero.label} was a little {params.trait} hero who loved helping people in {setting.place}."
    )
    world.say(
        f"{hero.label} had {action.power} in {hero.pronoun('possessive')} heart and wanted to use it kindly."
    )
    world.say(
        f"One afternoon, {hero.label} and {parent.label} went to {setting.place}, {setting.scene}."
    )
    world.say(
        f"Then {hero.label} noticed {obj.phrase}, and {hero.pronoun().capitalize()} wanted to {action.verb}."

    )
    world.para()
    world.say(
        f"{hero.label} rushed in to help, and {action.effect}."
    )

    # Misunderstanding beat: the parent sees the motion, not the reason.
    parent.memes["misunderstanding"] = 1.0
    hero.memes["misunderstanding"] = 1.0
    world.say(
        f"At first, {parent.label} thought {hero.label} was being careless."
    )
    world.say(
        f"It {action.apparent} {hero.label} was just {action.motion}, and that made {parent.label} worry about {obj.risk}."
    )
    world.say(
        f'"Please stop," said {parent.label}. "I thought you were making things worse."'
    )

    # Emotional turn: explanation and reconciliation.
    world.para()
    hero.memes["concern"] = 1.0
    hero.memes["joy"] = 0.5
    world.say(
        f"{hero.label} took a breath and explained that {hero.pronoun('subject')} was only trying to help."
    )
    world.say(
        f"{hero.pronoun().capitalize()} showed how {action.effect.lower()}, because {obj.safe}."
    )
    world.say(
        f"Then {parent.label} understood the apparent mistake."
    )
    parent.memes["worry"] = 0.0
    parent.memes["trust"] = 1.0
    parent.memes["reconciliation"] = 1.0
    hero.memes["reconciliation"] = 1.0
    world.say(
        f"{parent.label} smiled, gave {hero.pronoun('object')} a hug, and said sorry for the misunderstanding."
    )
    world.say(
        f"{hero.label} smiled back, and the two of them worked together to finish the job safely."
    )

    world.para()
    hero.memes["joy"] = 1.0
    parent.memes["joy"] = 1.0
    world.say(
        f"By sunset, {obj.phrase} was safe again, and {hero.label} and {parent.label} walked home side by side."
    )
    world.say(
        f"{hero.label}'s {action.power} still sparkled, but now it sparkled with trust, too."
    )
    world.say(
        f"The last thing they saw was {setting.place} glowing warmly behind them."
    )

    return world


# ---------------------------------------------------------------------------
# QA and prose helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    action: Action = f["action"]  # type: ignore[assignment]
    obj: ObjectSpec = f["object"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child that includes the words "apparent" and "parent".',
        f"Tell a gentle story where {hero.label} wants to {action.verb} at {setting.place}, but {parent.label} first misunderstands what is happening.",
        f"Write a simple story about a small hero, a misunderstanding, and a reconciliation over {obj.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    action: Action = f["action"]  # type: ignore[assignment]
    obj: ObjectSpec = f["object"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a small superhero who wanted to help at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.label} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry at first?",
            answer=f"{parent.label} thought the scene {action.apparent} {hero.label} was only causing trouble, when really {hero.pronoun('subject')} was helping.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding?",
            answer=f"{hero.label} explained the plan, {parent.label} understood, and they had a reconciliation with a hug and kind words.",
        ),
        QAItem(
            question=f"What was safe by the end?",
            answer=f"{obj.phrase} was safe again, and the problem at {setting.place} was finished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero uses special courage or powers to help other people and solve problems.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something wrong at first and later learns the truth.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and come back together kindly.",
        ),
        QAItem(
            question="What does apparent mean?",
            answer="Apparent means something seems true at first because of how it looks, even before you know the whole story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.kind}/{ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
parent(P) :- parent_role(P).
action(A) :- action_id(A).
object(O) :- object_id(O).
setting(S) :- setting_id(S).

misunderstanding(H,P) :- first_looks_bad(H,P).
reconciliation(H,P) :- explains(H,P), understands(P,H).

apparent_mistake(H,P) :- first_looks_bad(H,P), not true_harm(H,P).

#show apparent_mistake/2.
#show misunderstanding/2.
#show reconciliation/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_id", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action_id", aid))
    for oid in OBJECTS:
        lines.append(asp.fact("object_id", oid))
    for gid, g in HEROES.items():
        lines.append(asp.fact("hero_name", g["name"]))
    for role in PARENTS:
        lines.append(asp.fact("parent_role", role))
    lines.append(asp.fact("first_looks_bad", "hero", "parent"))
    lines.append(asp.fact("explains", "hero", "parent"))
    lines.append(asp.fact("understands", "parent", "hero"))
    lines.append(asp.fact("true_harm", "none", "none"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show apparent_mistake/2.\n#show misunderstanding/2.\n#show reconciliation/2."))
    names = {(sym.name, tuple(getattr(a, "string", getattr(a, "name", None)) for a in sym.arguments)) for sym in model}
    expected = {
        ("apparent_mistake", ("hero", "parent")),
        ("misunderstanding", ("hero", "parent")),
        ("reconciliation", ("hero", "parent")),
    }
    if names == expected:
        print("OK: ASP twin produces the expected reconciliation story facts.")
        return 0
    print("MISMATCH in ASP twin.")
    print("got:", sorted(names))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Sampling / resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid in ACTIONS:
            for oid in OBJECTS:
                combos.append((sid, aid, oid))
    return combos


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.action and args.object:
        if (args.setting, args.action, args.object) not in valid_combos():
            raise StoryError(explain_rejection("that combination does not make a coherent hero-help story"))

    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    object_id = args.object or rng.choice(list(OBJECTS))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES[hero_gender])
    parent_role = args.parent or "parent"
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        action=action,
        object=object_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent_role=parent_role,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = run_story(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="city", action="lift", object="crate", hero_name="Nova", hero_gender="girl", parent_role="parent", trait="brave"),
    StoryParams(setting="park", action="guide", object="kitten", hero_name="Finn", hero_gender="boy", parent_role="parent", trait="kind"),
    StoryParams(setting="market", action="catch", object="ball", hero_name="Mina", hero_gender="girl", parent_role="parent", trait="helpful"),
    StoryParams(setting="harbor", action="save", object="kite", hero_name="Leo", hero_gender="boy", parent_role="parent", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: superhero, misunderstanding, reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=list(PARENTS))
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show apparent_mistake/2.\n#show misunderstanding/2.\n#show reconciliation/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show apparent_mistake/2.\n#show misunderstanding/2.\n#show reconciliation/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
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
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.action} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
