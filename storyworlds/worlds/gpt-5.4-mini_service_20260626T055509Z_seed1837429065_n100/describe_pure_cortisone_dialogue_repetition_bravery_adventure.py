#!/usr/bin/env python3
"""
storyworlds/worlds/describe_pure_cortisone_dialogue_repetition_bravery_adventure.py
===================================================================================

A small adventure storyworld built from the seed words:
describe, pure, cortisone

The world premise:
- A child goes on a little adventure trail.
- A tiny skin bother appears: an itchy red patch from a prickly plant or bite.
- A parent or helper describes what is happening, calmly and clearly.
- The child shows bravery.
- Dialogue and repetition help the child stay steady while a safe, pure cortisone cream is used as a gentle remedy.

The story engine models:
- physical meters: itch, soreness, worry, relief, distance, carried_items
- emotional memes: bravery, calm, trust, surprise, pride

The story is generated from world state, not from a fixed paragraph.
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
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "trail": {
        "label": "the forest trail",
        "detail": "The path wound between ferns and little sunlit stones.",
        "adventure": True,
    },
    "hill": {
        "label": "the grassy hill",
        "detail": "The hill was wide and bright, with wind brushing the grass flat.",
        "adventure": True,
    },
    "creek": {
        "label": "the creek path",
        "detail": "Water whispered nearby, and the stones were smooth and cool.",
        "adventure": True,
    },
    "garden": {
        "label": "the back garden",
        "detail": "The garden held tall beans, round leaves, and a few prickly stems.",
        "adventure": False,
    },
}

TRIGGERS = {
    "thorn": {
        "label": "a thorny stem",
        "mess": "prickly",
        "effect": {"itch": 2.0, "soreness": 1.0, "worry": 1.0},
        "dialogue": "That little prick can make skin feel hot and itchy.",
    },
    "bug": {
        "label": "a bug bite",
        "mess": "itchy",
        "effect": {"itch": 2.0, "soreness": 0.5, "worry": 1.0},
        "dialogue": "Bug bites can itch a lot, even when they are tiny.",
    },
    "sun": {
        "label": "too much sun",
        "mess": "stingy",
        "effect": {"itch": 0.5, "soreness": 1.5, "worry": 0.8},
        "dialogue": "Sunburn can make skin sore and warm.",
    },
}

REMEDIES = {
    "cortisone": {
        "label": "pure cortisone cream",
        "short": "cortisone",
        "verb": "smooth on",
        "effect": {"itch": -2.0, "soreness": -0.5, "relief": 2.0, "calm": 1.0},
        "reason": "It is a gentle medicine used on small itchy skin spots.",
    },
    "cool_cloth": {
        "label": "a cool wet cloth",
        "short": "cool cloth",
        "verb": "press on",
        "effect": {"itch": -1.0, "soreness": -0.5, "relief": 1.0, "calm": 1.0},
        "reason": "Cool cloths can help skin feel better for a little while.",
    },
    "bandage": {
        "label": "a soft bandage",
        "short": "bandage",
        "verb": "cover with",
        "effect": {"itch": -0.5, "soreness": -0.5, "relief": 0.7, "calm": 0.4},
        "reason": "A bandage can keep a small spot safe from more rubbing.",
    },
}

CHARACTER_NAMES = [
    "Mila", "Noah", "June", "Toby", "Nina", "Eli", "Sage", "Iris", "Finn", "Ruby"
]

PARENT_NAMES = ["mom", "dad", "aunt", "uncle", "grandma", "grandpa"]

TRAITS = ["brave", "curious", "steady", "gentle", "cheerful", "spirited"]


# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "aunt", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "uncle", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    trigger: str
    remedy: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def describe_place(place: str) -> str:
    return PLACES[place]["detail"]


def describe_trigger(trigger: str) -> str:
    return TRIGGERS[trigger]["dialogue"]


def describe_remedy(remedy: str) -> str:
    return REMEDIES[remedy]["reason"]


def needs_remedy(world: World) -> bool:
    child = world.get("child")
    return _ensure_meter(child, "itch") >= THRESHOLD or _ensure_meter(child, "soreness") >= THRESHOLD


def remedy_is_reasonable(trigger: str, remedy: str) -> bool:
    """Python reasonableness gate."""
    if remedy == "cortisone":
        return trigger in {"thorn", "bug", "sun"}
    if remedy == "cool_cloth":
        return trigger in {"thorn", "bug", "sun"}
    if remedy == "bandage":
        return trigger in {"thorn", "bug"}
    return False


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def rule_trigger(world: World) -> list[str]:
    child = world.get("child")
    trigger = world.facts["trigger"]
    sig = ("trigger", trigger)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for k, v in TRIGGERS[trigger]["effect"].items():
        _add_meter(child, k, v)
    _add_meme(child, "surprise", 0.8)
    return [f"A small problem made {child.id}'s skin feel {TRIGGERS[trigger]['mess']} and uncomfortable."]


def rule_bravery(world: World) -> list[str]:
    child = world.get("child")
    if _ensure_meter(child, "worry") < THRESHOLD:
        return []
    sig = ("bravery", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _add_meme(child, "bravery", 1.5)
    _add_meme(child, "calm", 0.5)
    return [f"But {child.id} took a breath and stayed brave."]


def rule_dialogue(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    if _ensure_meter(child, "worry") < THRESHOLD:
        return []
    sig = ("dialogue", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return [
        f'"Let me describe it," {parent.id} said. "It looks small, but it can feel big."',
        f'"I can be brave," {child.id} said. "I can be brave, I can be brave."',
    ]


def rule_repeat_and_remedy(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    remedy_key = world.facts["remedy"]
    sig = ("remedy", remedy_key)
    if sig in world.fired:
        return []
    if not needs_remedy(world):
        return []
    world.fired.add(sig)
    remedy = REMEDIES[remedy_key]
    for k, v in remedy["effect"].items():
        if k in {"calm", "relief", "bravery"}:
            _add_meme(child, k, v)
        else:
            _add_meter(child, k, v)
    _add_meter(child, "relief", 1.0)
    return [
        f'{parent.id} opened the little tube of {remedy["label"]}.',
        f'"A thin layer is enough," {parent.id} said. "A thin layer, just a thin layer."',
        f"{parent.id} gently {remedy['verb']} {remedy['short']} on the sore spot.",
    ]


def rule_resolution(world: World) -> list[str]:
    child = world.get("child")
    remedy_key = world.facts["remedy"]
    sig = ("resolution", remedy_key)
    if sig in world.fired:
        return []
    if _ensure_meter(child, "relief") < THRESHOLD:
        return []
    world.fired.add(sig)
    child.meters["itch"] = max(0.0, _ensure_meter(child, "itch") - 1.0)
    child.meters["soreness"] = max(0.0, _ensure_meter(child, "soreness") - 0.5)
    _add_meme(child, "pride", 1.0)
    return [
        f"The spot settled down, and the child could smile again.",
        f"{child.id} kept walking, proud and brave, while the trail looked friendly once more.",
    ]


RULES = [rule_trigger, rule_bravery, rule_dialogue, rule_repeat_and_remedy, rule_resolution]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            before = (len(world.fired), world.render())
            out = rule(world)
            if out:
                changed = True
                if narrate:
                    for s in out:
                        world.say(s)


def predict(world: World, trigger: str, remedy: str) -> dict:
    sim = world.copy()
    sim.facts["trigger"] = trigger
    sim.facts["remedy"] = remedy
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "needs_remedy": _ensure_meter(child, "relief") >= 1.0,
        "itch": _ensure_meter(child, "itch"),
        "soreness": _ensure_meter(child, "soreness"),
    }


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(params.place)
    place = PLACES[params.place]
    trigger = TRIGGERS[params.trigger]
    remedy = REMEDIES[params.remedy]

    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl" if params.name in {"June", "Nina", "Sage", "Iris", "Ruby"} else "boy",
        label=params.name,
        meters={"itch": 0.0, "soreness": 0.0, "worry": 0.0, "relief": 0.0},
        memes={"bravery": 0.0, "calm": 0.0, "trust": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={},
        memes={"calm": 0.0},
    ))

    world.facts.update(
        child=child,
        parent=parent,
        place=place["label"],
        trigger=params.trigger,
        remedy=params.remedy,
        trait=params.trait,
        name=params.name,
    )

    # Act 1: adventure setup.
    world.say(f"{params.name} was a {params.trait} little explorer on {place['label']}.")
    world.say(place["detail"])
    world.say(f"{params.name} loved adventure, and {params.name} liked to describe every new sound and leaf.")
    world.say(f'The helper knew how to describe a small problem: "{describe_trigger(params.trigger)}"')
    world.para()

    # Act 2: the problem grows.
    world.say(f"While walking, {params.name} brushed the wrong spot and got a little skin trouble.")
    propagate(world, narrate=True)
    world.say(f'The helper said, "{describe_place(params.place)}"')
    world.para()

    # Act 3: brave response and remedy.
    if remedy_is_reasonable(params.trigger, params.remedy):
        propagate(world, narrate=True)
    else:
        raise StoryError(f"No reasonable remedy for trigger '{params.trigger}' and remedy '{params.remedy}'.")

    world.say(
        f'At last, the helper explained, "{describe_remedy(params.remedy)}"'
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a small child named {f["name"]} that includes the word "describe".',
        f'Write a gentle story where {f["name"]} is brave, repeats a calm phrase, and uses pure cortisone cream.',
        f'Write an adventure scene with dialogue, repetition, and a small itchy problem that gets better.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    place = f["place"]["label"]
    trigger = TRIGGERS[f["trigger"]]
    remedy = REMEDIES[f["remedy"]]

    return [
        QAItem(
            question=f"Where was {child.label} on the adventure?",
            answer=f"{child.label} was at {place}, where the path or yard had room for a little adventure.",
        ),
        QAItem(
            question=f"What caused the skin to feel uncomfortable?",
            answer=f"It was {trigger['label']}, which made the skin feel {trigger['mess']} and upset the child a little.",
        ),
        QAItem(
            question=f"How did the helper calm things down?",
            answer=f"The helper used {remedy['label']} and spoke in a calm voice, repeating the instructions so they were easy to follow.",
        ),
        QAItem(
            question=f"How did {child.label} show bravery?",
            answer=f"{child.label} kept going, listened closely, and repeated brave words instead of panicking.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    remedy = REMEDIES[f["remedy"]]
    trigger = TRIGGERS[f["trigger"]]
    return [
        QAItem(
            question="What does cortisone cream do?",
            answer="Cortisone cream is a medicine that can help calm itchy skin spots and make them feel less bothersome.",
        ),
        QAItem(
            question="Why do people repeat calm words when something scary happens?",
            answer="Repeating calm words can help someone slow down, stay steady, and remember what to do next.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels scared or unsure but still does the good or needed thing.",
        ),
        QAItem(
            question=f"Why might {trigger['label']} need gentle care?",
            answer=f"{trigger['label']} can make skin feel sore or itchy, so gentle care can help it settle down.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A remedy is reasonable when it can help the trigger described in the registry.
reasonable(T, R) :- trigger(T), remedy(R), supports(R, T).
needs_help(T) :- trigger(T).

valid_story(P, T, R) :- place(P), trigger(T), remedy(R), reasonable(T, R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TRIGGERS:
        lines.append(asp.fact("trigger", t))
    for r, info in REMEDIES.items():
        lines.append(asp.fact("remedy", r))
        for t in TRIGGERS:
            if remedy_is_reasonable(t, r):
                lines.append(asp.fact("supports", r, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    valid_python = {
        (p, t, r)
        for p in PLACES
        for t in TRIGGERS
        for r in REMEDIES
        if remedy_is_reasonable(t, r)
    }
    valid_asp = set(asp_valid_stories())
    if valid_python == valid_asp:
        print(f"OK: ASP and Python agree on {len(valid_python)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python:")
    if valid_python - valid_asp:
        print("  only in python:", sorted(valid_python - valid_asp))
    if valid_asp - valid_python:
        print("  only in ASP:", sorted(valid_asp - valid_python))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with dialogue, repetition, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    trigger = args.trigger or rng.choice(list(TRIGGERS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if not remedy_is_reasonable(trigger, remedy):
        # try to repair by choosing a compatible remedy
        compatibles = [r for r in REMEDIES if remedy_is_reasonable(trigger, r)]
        if args.remedy and not compatibles:
            raise StoryError(f"No reasonable remedy for trigger '{trigger}' and remedy '{args.remedy}'.")
        remedy = args.remedy or rng.choice(compatibles)

    name = args.name or rng.choice(CHARACTER_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trigger=trigger, remedy=remedy, name=name, parent=parent, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


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
    StoryParams(place="trail", trigger="thorn", remedy="cortisone", name="Mila", parent="mom", trait="brave"),
    StoryParams(place="creek", trigger="bug", remedy="cortisone", name="Noah", parent="dad", trait="curious"),
    StoryParams(place="garden", trigger="sun", remedy="cool_cloth", name="June", parent="aunt", trait="steady"),
    StoryParams(place="hill", trigger="thorn", remedy="bandage", name="Finn", parent="grandma", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.place} / {p.trigger} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
