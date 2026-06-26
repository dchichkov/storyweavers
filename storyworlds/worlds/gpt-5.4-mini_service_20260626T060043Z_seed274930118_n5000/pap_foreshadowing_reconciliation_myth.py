#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pap_foreshadowing_reconciliation_myth.py
===============================================================================================================

A small myth-style storyworld about a child, a pap, a warning sign, and a
reconciliation that changes the ending image.

The domain is intentionally compact: a child in a simple place notices a
foretelling sign, makes a risky choice, then returns to harmony with pap
through a repair action that is physically and emotionally grounded.
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
# World model
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
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "pap"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    sign: str
    omen: str


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    harm: str
    risk_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    protects: set[str]
    repair: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.omen_seen = False
        self.reconciled = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hill": Setting(place="the hill", sign="a crow circling the stone", omen="the wind sounded like a low drum"),
    "river": Setting(place="the riverbank", sign="a white lily bent toward the water", omen="the water hummed under the reeds"),
    "grove": Setting(place="the grove", sign="three leaves turning at once", omen="the trees whispered before the child spoke"),
}

ACTIONS = {
    "climb": Action(
        id="climb",
        verb="climb the high ledge",
        gerund="climbing the high ledge",
        rush="scramble toward the ledge",
        mess="scraped knees",
        harm="a hard fall",
        risk_key="ledge",
        tags={"stone", "height"},
    ),
    "wade": Action(
        id="wade",
        verb="wade into the cold water",
        gerund="wading into the cold water",
        rush="run straight into the current",
        mess="soaked clothes",
        harm="a soaked and shivering night",
        risk_key="water",
        tags={"water", "river"},
    ),
    "fetch": Action(
        id="fetch",
        verb="fetch the glowing reed",
        gerund="fetching the glowing reed",
        rush="reach into the reeds",
        mess="muddy hands",
        harm="a cut from hidden thorns",
        risk_key="reeds",
        tags={"reed", "light"},
    ),
}

ARTIFACTS = {
    "shawl": Artifact(
        id="shawl",
        label="wool shawl",
        phrase="a warm wool shawl",
        region="shoulders",
        protects={"cold", "wind"},
        repair="wrap the shawl around the child",
    ),
    "boots": Artifact(
        id="boots",
        label="river boots",
        phrase="sturdy river boots",
        region="feet",
        protects={"water", "mud"},
        repair="lace up the river boots",
    ),
    "gloves": Artifact(
        id="gloves",
        label="reed gloves",
        phrase="soft reed gloves",
        region="hands",
        protects={"thorns", "mud"},
        repair="put on the reed gloves",
    ),
}

CHILD_NAMES = ["Mira", "Tavi", "Eli", "Nia", "Sora", "Bren"]
TRAITS = ["curious", "brave", "soft-hearted", "stubborn", "bright-eyed"]


@dataclass
class StoryParams:
    setting: str
    action: str
    artifact: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def at_risk(action: Action, artifact: Artifact) -> bool:
    return artifact.region in {"shoulders", "feet", "hands"} and (
        (action.id == "wade" and artifact.region == "feet")
        or (action.id == "climb" and artifact.region == "shoulders")
        or (action.id == "fetch" and artifact.region == "hands")
    )


def select_artifact(action: Action) -> Artifact:
    for art in ARTIFACTS.values():
        if at_risk(action, art):
            return art
    raise StoryError("No compatible artifact exists for that action.")


def explain_rejection(action: Action, artifact: Artifact) -> str:
    return (
        f"(No story: {artifact.label} does not genuinely protect the at-risk part "
        f"of the body for {action.gerund}. The story needs a real foreshadowing sign "
        f"and a real reconciliation, not a fake fix.)"
    )


# ---------------------------------------------------------------------------
# Simulated story
# ---------------------------------------------------------------------------
def _do_action(world: World, child: Entity, action: Action, narrate: bool = True) -> None:
    child.meters[action.mess] = child.meters.get(action.mess, 0.0) + 1.0
    child.memes["thrill"] = child.memes.get("thrill", 0.0) + 1.0
    if narrate:
        world.say(f"{child.pronoun().capitalize()} went on to {action.gerund}.")


def tell(setting: Setting, action: Action, artifact: Artifact, child_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="boy" if child_name in {"Eli", "Bren"} else "girl"))
    pap = world.add(Entity(id="pap", kind="character", type="pap", label="pap"))
    relic = world.add(Entity(id="relic", type=artifact.id, label=artifact.label, phrase=artifact.phrase, owner=child.id, caretaker=pap.id))
    relic.worn_by = child.id

    world.say(f"In the old days of {setting.place}, {child_name} was a {trait} child who listened for signs.")
    world.say(f"{trait.capitalize()} {child_name} loved the way {setting.omen}.")
    world.say(f"One morning, {setting.sign} appeared, and pap said it was a warning from the old world.")
    world.omen_seen = True
    world.say(f"{child_name} wore {relic.phrase} and still wanted to {action.verb}.")

    world.say(f"Pap frowned and said, '{action.harm} follows when little feet forget the sign.'")
    world.say(f"{child_name} tried to {action.rush}, but the place itself seemed to answer back.")

    _do_action(world, child, action, narrate=False)
    world.say(f"{child_name} felt the danger at once; {action.harm} was close enough to imagine.")

    world.say(f"Then pap stepped beside {child_name} with no anger in {pap.pronoun('possessive')} voice.")
    world.say(f"Together they chose to {artifact.repair}.")
    child.meters[action.mess] = 0.0
    child.memes["thrill"] = 0.0
    child.memes["peace"] = child.memes.get("peace", 0.0) + 1.0
    pap.memes["peace"] = pap.memes.get("peace", 0.0) + 1.0
    world.reconciled = True
    world.say(f"{child_name} leaned close, and the two of them finished the task side by side.")
    world.say(f"In the end, the warning had become wisdom, and pap and child stood in calm light.")

    world.facts.update(
        child=child,
        pap=pap,
        relic=relic,
        action=action,
        artifact=artifact,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    return [
        f'Write a short myth about a child named {child.id}, pap, and a warning sign in {f["setting"].place}.',
        f"Tell a child-friendly myth where {child.id} wants to {action.verb}, but a sign foretells trouble and pap helps with a safer choice.",
        f'Write a gentle reconciliation story using the word "pap" and ending with a repaired, calm image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    pap = f["pap"]
    action = f["action"]
    art = f["artifact"]
    setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who is the child in the story at {setting.place}?",
            answer=f"The child is {child.id}, a {trait} little one who lives in a world where pap watches the signs.",
        ),
        QAItem(
            question=f"What did pap warn about when {child.id} wanted to {action.verb}?",
            answer=f"Pap warned that {action.harm} could follow if {child.id} rushed ahead without listening to the sign.",
        ),
        QAItem(
            question=f"How did pap and {child.id} reconcile in the end?",
            answer=f"They reconciled by choosing to {art.repair}, so the child could stay safe and pap could feel calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a foreshadowing sign?",
            answer="A foreshadowing sign is a clue that hints something important or dangerous may happen later.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a problem, so people can be calm with each other.",
        ),
        QAItem(
            question="What is pap in this storyworld?",
            answer="Pap is the child's father figure, a watchful parent who notices signs and helps with careful choices.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
parent(P) :- pap(P).
risk(A, Art) :- action(A), artifact(Art), action_risk(A, R), artifact_region(Art, R).
compatible(A, Art) :- risk(A, Art), action_protects(A, P), artifact_protects(Art, P).
valid_story(S, A, Art) :- setting(S), action(A), artifact(Art), compatible(A, Art).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_risk", aid, a.risk_key))
        for t in sorted(a.tags):
            lines.append(asp.fact("action_tag", aid, t))
    for rid, r in ARTIFACTS.items():
        lines.append(asp.fact("artifact", rid))
        lines.append(asp.fact("artifact_region", rid, r.region))
        for p in sorted(r.protects):
            lines.append(asp.fact("artifact_protects", rid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    clingo_story = asp.one_model(asp_program("#show valid_story/3."))
    clingo = set(asp.atoms(clingo_story, "valid_story"))
    python = {(sid, aid, rid) for sid in SETTINGS for aid, a in ACTIONS.items() for rid, art in ARTIFACTS.items() if at_risk(a, art)}
    if clingo == python:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo - python))
    print("  only in python:", sorted(python - clingo))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with foreshadowing and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name", choices=CHILD_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    action_obj = ACTIONS[action]
    if args.artifact:
        art = ARTIFACTS[args.artifact]
        if not at_risk(action_obj, art):
            raise StoryError(explain_rejection(action_obj, art))
    else:
        art = select_artifact(action_obj)
    if args.artifact and not at_risk(action_obj, ARTIFACTS[args.artifact]):
        raise StoryError(explain_rejection(action_obj, ARTIFACTS[args.artifact]))
    name = args.name or rng.choice(CHILD_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, action=action, artifact=art.id, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], ARTIFACTS[params.artifact], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        parts.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    parts.append(f"  omen_seen={world.omen_seen}")
    parts.append(f"  reconciled={world.reconciled}")
    return "\n".join(parts)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in SETTINGS:
            for aid, act in ACTIONS.items():
                for rid, art in ARTIFACTS.items():
                    if at_risk(act, art):
                        params = StoryParams(setting=sid, action=aid, artifact=rid, name=random.choice(CHILD_NAMES), trait=random.choice(TRAITS))
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
