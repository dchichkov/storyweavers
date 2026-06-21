#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py
==========================================================

A standalone storyworld about a small sharing problem in a child-facing place.
The key idea is simple and concrete: one child clutches a special art supply,
another child cannot finish a picture, and a calm grown-up teaches a sharing
policy that actually fits the material and the setting. The world model tracks
objects, turns, waiting, finished pictures, and feelings, then renders a short
rhyming story from that simulated state.

The world refuses weak combinations. A "sharing policy" must fit the kind of
resource in play: a single special tool needs a taking-turns policy, while a
divisible snack needs a split-in-pieces policy. The inline ASP twin checks the
same compatibility gate and the same happy outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py --resource glitter_glue --policy turns
    python storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py --resource cookie --policy turns
    python storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/policy_sharing_rhyming_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female and self.id != "Teacher":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.id == "Teacher":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "teacher":
            return "teacher"
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    activity: str
    group_name: str
    storage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resource:
    id: str
    label: str
    phrase: str
    kind: str
    texture: str
    use_line: str
    need_line: str
    finished_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Policy:
    id: str
    label: str
    kind: str
    teacher_line: str
    success_line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "waiter"}]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_waiting_sad(world: World) -> list[str]:
    out: list[str] = []
    holder = world.get("holder")
    waiter = world.get("waiter")
    resource = world.get("resource")
    if holder.meters["holding"] >= THRESHOLD and waiter.meters["waiting"] >= THRESHOLD:
        sig = ("waiting_sad", holder.id, waiter.id, resource.id)
        if sig not in world.fired:
            world.fired.add(sig)
            waiter.memes["sad"] += 1
            holder.memes["guilt"] += 1
            out.append("__waiting__")
    return out


def _r_finish_picture(world: World) -> list[str]:
    out: list[str] = []
    resource = world.get("resource")
    for kid in world.kids():
        if kid.meters["used"] < THRESHOLD:
            continue
        sig = ("finish", kid.id, resource.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["picture_done"] += 1
        kid.memes["proud"] += 1
        out.append("__finish__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="waiting_sad", tag="social", apply=_r_waiting_sad),
    Rule(name="finish_picture", tag="physical", apply=_r_finish_picture),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def policy_fits(resource: Resource, policy: Policy) -> bool:
    return resource.kind == policy.kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for resource_id, resource in RESOURCES.items():
            for policy_id, policy in POLICIES.items():
                if policy_fits(resource, policy):
                    combos.append((setting_id, resource_id, policy_id))
    return combos


def explain_rejection(resource: Resource, policy: Policy) -> str:
    if resource.kind == "single_tool" and policy.kind != "single_tool":
        return (
            f"(No story: {resource.phrase} is one shared tool, so the policy must be about turns. "
            f"Splitting works for shareable food, not for {resource.label}.)"
        )
    if resource.kind == "divisible_food" and policy.kind != "divisible_food":
        return (
            f"(No story: {resource.phrase} can be split into pieces, so the policy should be about fair pieces. "
            f"Taking turns with bites is not a good child-facing sharing policy for {resource.label}.)"
        )
    return "(No story: that sharing policy does not fit the resource.)"


def predict_hurt(world: World) -> dict:
    sim = world.copy()
    holder = sim.get("holder")
    waiter = sim.get("waiter")
    holder.meters["holding"] += 1
    waiter.meters["waiting"] += 1
    propagate(sim, narrate=False)
    return {
        "waiter_sad": waiter.memes["sad"] >= THRESHOLD,
        "holder_guilty": holder.memes["guilt"] >= THRESHOLD,
    }


def introduce(world: World, holder: Entity, waiter: Entity, setting: Setting, resource: Resource) -> None:
    for kid in (holder, waiter):
        kid.memes["joy"] += 1
    world.say(
        f"In {setting.place}, with hum and hop and happy chatter, "
        f"{holder.id} and {waiter.id} made art that seemed to matter."
    )
    world.say(
        f"The {setting.group_name} was busy with {setting.activity}, bright and cool, "
        f"and {setting.storage} sparkled like treasure in the room at school."
    )
    world.say(
        f"There on the table lay {resource.phrase}, {resource.texture}; "
        f"it made each page look rich and new, a shiny little mixture."
    )


def clutch(world: World, holder: Entity, resource: Resource) -> None:
    holder.meters["holding"] += 1
    holder.memes["greed"] += 1
    world.say(
        f"{holder.id} reached first and hugged {resource.label} near. "
        f'"I want it all right now," {holder.pronoun()} said. "I need it over here."'
    )


def ask_to_share(world: World, waiter: Entity, resource: Resource) -> None:
    waiter.memes["hope"] += 1
    waiter.meters["needs_resource"] += 1
    world.say(
        f"{waiter.id} looked at an empty spot and whispered, soft and airy, "
        f'"May I have some too? {resource.need_line}," polite and small and wary.'
    )


def refuse(world: World, holder: Entity, waiter: Entity) -> None:
    waiter.meters["waiting"] += 1
    holder.memes["stubborn"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {holder.id} turned away a bit and made a frowny face. '
        f'"No, I need it for my own," {holder.pronoun()} said, and kept the place.'
    )
    if waiter.memes["sad"] >= THRESHOLD:
        world.say(
            f"So {waiter.id} waited with an unfinished page and quiet, droopy eyes. "
            f"The room still rang with snips and songs, but not with {waiter.id}'s glad sighs."
        )


def teacher_notices(world: World, teacher: Entity, holder: Entity, waiter: Entity, resource: Resource, policy: Policy) -> None:
    pred = predict_hurt(world)
    world.facts["predicted_hurt"] = pred
    teacher.memes["care"] += 1
    world.say(
        f"Then {teacher.label_word} came with gentle steps and saw the little folly. "
        f'She knelt beside the table and said, "We have a sharing policy."'
    )
    world.say(
        f'"{policy.teacher_line}" Her voice was calm and clear. '
        f"She showed them how to make more room for every friend nearby and dear."
    )


def apply_policy(world: World, holder: Entity, waiter: Entity, resource: Resource, policy: Policy) -> None:
    holder.memes["understanding"] += 1
    waiter.memes["relief"] += 1
    holder.meters["holding"] = 0.0
    waiter.meters["waiting"] = 0.0
    if policy.kind == "single_tool":
        holder.meters["used"] += 1
        waiter.meters["used"] += 1
        world.facts["shares_by"] = "turns"
        world.say(
            f"{holder.id} took one careful turn, then passed {resource.label} by. "
            f"{waiter.id} used it next with smiling hands and one delighted sigh."
        )
    else:
        holder.meters["used"] += 1
        waiter.meters["used"] += 1
        world.facts["shares_by"] = "pieces"
        world.say(
            f"{teacher_pass_line(resource)} {holder.id} and {waiter.id} each took a fair small part. "
            f"Soon each had enough to finish up a bright and tasty art."
        )
    propagate(world, narrate=False)
    world.say(policy.success_line)


def teacher_pass_line(resource: Resource) -> str:
    return (
        f"The grown-up split {resource.label} into two neat bits without a fuss."
        if resource.kind == "divisible_food"
        else f"The grown-up set {resource.label} in the center, fair for us."
    )


def finish_together(world: World, holder: Entity, waiter: Entity, resource: Resource) -> None:
    for kid in (holder, waiter):
        kid.memes["joy"] += 1
        kid.memes["kindness"] += 1
    world.say(
        f"Soon {holder.id}'s page and {waiter.id}'s page both gleamed from top to floor. "
        f"They {resource.finished_with}, and each one wished to share a little more."
    )
    world.say(
        f"Their shoulders softened, hearts grew light, and trouble slipped away. "
        f"Two pictures dried beside the sink like flags of a kinder day."
    )


def tell(
    setting: Setting,
    resource: Resource,
    policy: Policy,
    holder_name: str = "Mia",
    holder_type: str = "girl",
    waiter_name: str = "Leo",
    waiter_type: str = "boy",
    teacher_type: str = "teacher",
) -> World:
    world = World(setting)
    holder = world.add(Entity(id=holder_name, kind="character", type=holder_type, role="holder", label=holder_name))
    waiter = world.add(Entity(id=waiter_name, kind="character", type=waiter_type, role="waiter", label=waiter_name))
    teacher = world.add(Entity(id="Teacher", kind="character", type=teacher_type, role="teacher", label="the teacher"))
    resource_ent = world.add(
        Entity(
            id="resource",
            kind="thing",
            type=resource.kind,
            label=resource.label,
            phrase=resource.phrase,
            tags=set(resource.tags),
        )
    )

    introduce(world, holder, waiter, setting, resource)
    world.para()
    clutch(world, holder, resource)
    ask_to_share(world, waiter, resource)
    refuse(world, holder, waiter)
    world.para()
    teacher_notices(world, teacher, holder, waiter, resource, policy)
    apply_policy(world, holder, waiter, resource, policy)
    world.para()
    finish_together(world, holder, waiter, resource)

    world.facts.update(
        setting=setting,
        resource_cfg=resource,
        policy_cfg=policy,
        holder=holder,
        waiter=waiter,
        teacher=teacher,
        resource=resource_ent,
        problem_happened=waiter.memes["sad"] >= THRESHOLD or holder.memes["guilt"] >= THRESHOLD,
        both_finished=holder.meters["picture_done"] >= THRESHOLD and waiter.meters["picture_done"] >= THRESHOLD,
        used_policy=True,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="a sunny classroom",
        activity="morning art time",
        group_name="little class",
        storage="the supply shelf",
        tags={"school", "art"},
    ),
    "library_corner": Setting(
        id="library_corner",
        place="the library craft corner",
        activity="story-and-craft time",
        group_name="reading group",
        storage="the rolling craft cart",
        tags={"library", "art"},
    ),
    "kitchen_table": Setting(
        id="kitchen_table",
        place="the kitchen table at home",
        activity="afternoon making time",
        group_name="family pair",
        storage="the jar by the window",
        tags={"home", "art"},
    ),
}

RESOURCES = {
    "glitter_glue": Resource(
        id="glitter_glue",
        label="the glitter glue",
        phrase="one bottle of glitter glue",
        kind="single_tool",
        texture="all silver swirls and sparkling dew",
        use_line="My star needs shiny silver too",
        need_line="My moon needs shiny silver too",
        finished_with="made stars that winked with silver glue",
        tags={"glue", "art", "sharing"},
    ),
    "purple_marker": Resource(
        id="purple_marker",
        label="the purple marker",
        phrase="one purple marker",
        kind="single_tool",
        texture="smooth and plum and bright to see",
        use_line="My flower needs this purple sea",
        need_line="My grape bunch needs this purple sea",
        finished_with="drew purple vines and flowers too",
        tags={"marker", "art", "sharing"},
    ),
    "cookie": Resource(
        id="cookie",
        label="the round cookie",
        phrase="one round cookie",
        kind="divisible_food",
        texture="warm and crumbly, sweet to chew",
        use_line="My tummy likes this treat, it's true",
        need_line="May I have a little too",
        finished_with="crumbled smiles across the blue",
        tags={"cookie", "food", "sharing"},
    ),
}

POLICIES = {
    "turns": Policy(
        id="turns",
        label="take turns",
        kind="single_tool",
        teacher_line="One special thing can still be shared: one turn for you, one turn for a friend, and then we pass it back again",
        success_line="The simple rule made waiting short, and nobody had to hide. Fair turns made room for both their work and both their bits of pride.",
        qa_text="They used a taking-turns policy, so one child used the item and then passed it on. That fit a single shared tool because both children needed the same one object.",
        tags={"policy", "turns", "sharing"},
    ),
    "split": Policy(
        id="split",
        label="split fairly",
        kind="divisible_food",
        teacher_line="When food can break in friendly ways, we split it fair so everyone gets some",
        success_line="Two equal pieces solved the problem fast, and both small faces glowed. A fair split worked because the treat could be divided before it was used.",
        qa_text="They used a split-it-fairly policy, so the grown-up divided the food into equal pieces. That fit a cookie because it can be shared in parts instead of being passed back and forth.",
        tags={"policy", "fairness", "sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Ruby", "Anna"]
BOY_NAMES = ["Leo", "Max", "Noah", "Sam", "Eli", "Finn", "Ben", "Jack"]


@dataclass
class StoryParams:
    setting: str
    resource: str
    policy: str
    holder_name: str
    holder_type: str
    waiter_name: str
    waiter_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "policy": [
        (
            "What is a policy?",
            "A policy is a simple rule people agree to follow. It helps everyone know what is fair and what to do.",
        )
    ],
    "sharing": [
        (
            "Why is sharing important?",
            "Sharing helps more than one person use or enjoy something. It can turn a problem into a kinder time together.",
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person goes first and then passes the chance to someone else. It is a fair way to share one thing that cannot be used by two people at once.",
        )
    ],
    "fairness": [
        (
            "What does fair mean?",
            "Fair means people are treated in a way that makes sense for the situation. Fair does not always mean the same thing every time, but it should give everyone a good chance.",
        )
    ],
    "glue": [
        (
            "What is glitter glue?",
            "Glitter glue is sticky glue with shiny sparkles in it. Children often use it to decorate art projects.",
        )
    ],
    "marker": [
        (
            "What is a marker?",
            "A marker is a drawing tool filled with colored ink. Children use markers to make bold, bright lines on paper.",
        )
    ],
    "cookie": [
        (
            "Why can a cookie be split fairly?",
            "A cookie can be broken into pieces, so two people can each have part of it. That makes splitting a sensible way to share it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["policy", "sharing", "turns", "fairness", "glue", "marker", "cookie"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    resource = f["resource_cfg"]
    policy = f["policy_cfg"]
    setting = f["setting"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "policy" and is about sharing in {setting.place}.',
        f"Tell a gentle rhyming story where {holder.id} will not share {resource.label} with {waiter.id}, and a teacher uses a fair policy to solve the problem.",
        f"Write a TinyStories-style poem-story where a simple {policy.label} rule helps two children finish happily after a sharing problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    teacher = f["teacher"]
    resource = f["resource_cfg"]
    policy = f["policy_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {holder.id} and {waiter.id} during {setting.activity}, with {teacher.label_word} helping them. The problem starts when they both want {resource.phrase}.",
        ),
        (
            f"Why was {waiter.id} sad?",
            f"{waiter.id} was sad because {holder.id} kept {resource.label} and would not share. That left {waiter.pronoun('object')} waiting with an unfinished page.",
        ),
        (
            "What was the sharing policy?",
            f"The sharing policy was to {policy.label}. {policy.qa_text}",
        ),
        (
            "How did the problem get solved?",
            f"The teacher noticed the unfair moment and taught a clear rule both children could follow. After that, both children got to use the resource and finish their work.",
        ),
    ]
    if f.get("both_finished"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with both pictures finished and both children feeling lighter and kinder. The ending image of two pages drying side by side shows that sharing changed the room.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"policy", "sharing"}
    tags |= set(world.facts["policy_cfg"].tags)
    tags |= set(world.facts["resource_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        resource="glitter_glue",
        policy="turns",
        holder_name="Mia",
        holder_type="girl",
        waiter_name="Leo",
        waiter_type="boy",
    ),
    StoryParams(
        setting="library_corner",
        resource="purple_marker",
        policy="turns",
        holder_name="Max",
        holder_type="boy",
        waiter_name="Ava",
        waiter_type="girl",
    ),
    StoryParams(
        setting="kitchen_table",
        resource="cookie",
        policy="split",
        holder_name="Nora",
        holder_type="girl",
        waiter_name="Ben",
        waiter_type="boy",
    ),
]


ASP_RULES = r"""
fits(R, P) :- resource(R), policy(P), resource_kind(R, K), policy_kind(P, K).
valid(S, R, P) :- setting(S), resource(R), policy(P), fits(R, P).

problem_happens :- chosen_resource(R), chosen_policy(P), fits(R, P).
resolved       :- chosen_resource(R), chosen_policy(P), fits(R, P).
happy_ending   :- resolved.

outcome(happy) :- happy_ending.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for resource_id, resource in RESOURCES.items():
        lines.append(asp.fact("resource", resource_id))
        lines.append(asp.fact("resource_kind", resource_id, resource.kind))
    for policy_id, policy in POLICIES.items():
        lines.append(asp.fact("policy", policy_id))
        lines.append(asp.fact("policy_kind", policy_id, policy.kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_resource", params.resource),
            asp.fact("chosen_policy", params.policy),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def verify_smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = "happy" if policy_fits(RESOURCES[params.resource], POLICIES[params.policy]) else "?"
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        verify_smoke_generation()
        print("OK: smoke generation passed.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a sharing problem solved by a fair policy. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--resource", choices=RESOURCES)
    ap.add_argument("--policy", choices=POLICIES)
    ap.add_argument("--holder-name")
    ap.add_argument("--waiter-name")
    ap.add_argument("--holder-type", choices=["girl", "boy"])
    ap.add_argument("--waiter-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def pick_child_name(rng: random.Random, child_type: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.resource and args.policy:
        resource = RESOURCES[args.resource]
        policy = POLICIES[args.policy]
        if not policy_fits(resource, policy):
            raise StoryError(explain_rejection(resource, policy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.resource is None or combo[1] == args.resource)
        and (args.policy is None or combo[2] == args.policy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, resource_id, policy_id = rng.choice(sorted(combos))
    holder_type = args.holder_type or rng.choice(["girl", "boy"])
    waiter_type = args.waiter_type or rng.choice(["girl", "boy"])
    holder_name = args.holder_name or pick_child_name(rng, holder_type)
    waiter_name = args.waiter_name or pick_child_name(rng, waiter_type, avoid=holder_name)
    return StoryParams(
        setting=setting_id,
        resource=resource_id,
        policy=policy_id,
        holder_name=holder_name,
        holder_type=holder_type,
        waiter_name=waiter_name,
        waiter_type=waiter_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.resource not in RESOURCES:
        raise StoryError(f"Unknown resource: {params.resource}")
    if params.policy not in POLICIES:
        raise StoryError(f"Unknown policy: {params.policy}")
    if not policy_fits(RESOURCES[params.resource], POLICIES[params.policy]):
        raise StoryError(explain_rejection(RESOURCES[params.resource], POLICIES[params.policy]))

    world = tell(
        setting=SETTINGS[params.setting],
        resource=RESOURCES[params.resource],
        policy=POLICIES[params.policy],
        holder_name=params.holder_name,
        holder_type=params.holder_type,
        waiter_name=params.waiter_name,
        waiter_type=params.waiter_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, resource, policy) combos:\n")
        for setting_id, resource_id, policy_id in combos:
            print(f"  {setting_id:14} {resource_id:14} {policy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.holder_name} and {p.waiter_name}: {p.resource} with {p.policy} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
