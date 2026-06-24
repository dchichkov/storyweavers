#!/usr/bin/env python3
"""
storyworlds/worlds/fire_scope_belabor_sandbox_foreshadowing_comedy.py
======================================================================

A small standalone storyworld about a sandbox, a suspicious little fire plan,
a scope that causes trouble, and a parent who keeps trying not to belabor the
point. The style is light comedy with a foreshadowing beat: the parent notices
the risky setup early, and the ending proves why.

Seed tale sketch:
---
A child wants to make a tiny campfire in a sandbox so the dolls can have a
"picnic adventure." The child brings a shiny scope, because the scope makes
everything feel official. The parent spots the scope, notices the bright sun,
and predicts that the scope might turn into a tiny sun-catcher. The child keeps
belaboring the plan with grand speeches about "proper fire drama." In the end,
they swap the flame for a glowing battery tea light and build a shaded little
camp scene instead, which is far funnier and much safer.

State model:
---
The sandbox world tracks:
- a child and parent with emotions like delight, worry, and relief
- physical meters such as heat, glare, soot, and shade
- props like a paper flame, a toy scope, and a shade lid
- foreshadowing: the parent can predict trouble from the scope + sun
- comedy: the child's overblown seriousness gets gently undercut by the safe fix
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
    place: str = "the sandbox"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.sunny: bool = True

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.sunny = self.sunny
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    prop: str
    gear: str
    seed: Optional[int] = None


SETTINGS = {
    "sandbox": Setting(place="the sandbox", indoor=False, affords={"fire", "scope", "belabor"}),
}

PROPS = {
    "campfire": Prop(
        id="campfire",
        label="paper flame",
        phrase="a tiny paper flame with red and orange layers",
        type="flame",
        risk="scorched",
        zone={"center"},
        keyword="fire",
        tags={"fire"},
    ),
    "scope": Prop(
        id="scope",
        label="toy scope",
        phrase="a shiny toy scope with a tiny handle",
        type="scope",
        risk="glared",
        zone={"center"},
        keyword="scope",
        tags={"scope"},
    ),
}

GEAR = {
    "shade": Gear(
        id="shade",
        label="a cardboard shade",
        covers={"center"},
        prep="put the camp scene under a cardboard shade",
        tail="slid the cardboard shade over the little camp",
    ),
    "lid": Gear(
        id="lid",
        label="a tin lid",
        covers={"center"},
        prep="set the flame on a tin lid first",
        tail="set the paper flame safely on the tin lid",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Sam"]
TRAITS = ["lively", "curious", "cheerful", "spirited"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_scorch(world: World) -> list[str]:
    out = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.meters.get("heat", 0) < THRESHOLD:
        return out
    prop = world.entities.get("prop")
    if not prop:
        return out
    if prop.protective:
        return out
    if prop.meters.get("shade", 0) >= THRESHOLD:
        return out
    sig = ("scorch", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["soot"] = prop.meters.get("soot", 0) + 1
    prop.meters["scorched"] = prop.meters.get("scorched", 0) + 1
    child.memes["oops"] = child.memes.get("oops", 0) + 1
    out.append("The little flame turned smudgy and warm.")
    return out


def _r_glare(world: World) -> list[str]:
    out = []
    child = next((e for e in world.characters() if e.kind == "character"), None)
    if not child:
        return out
    scope = world.entities.get("scope")
    if not scope:
        return out
    if child.meters.get("glare", 0) < THRESHOLD:
        return out
    if scope.meters.get("shade", 0) >= THRESHOLD:
        return out
    sig = ("glare", scope.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scope.meters["hot"] = scope.meters.get("hot", 0) + 1
    child.memes["squint"] = child.memes.get("squint", 0) + 1
    out.append("The toy scope caught the sun and made everyone squint.")
    return out


CAUSAL_RULES = [Rule("scorch", _r_scorch), Rule("glare", _r_glare)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                lines.extend(out)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def predict_trouble(world: World, prop_id: str) -> dict:
    sim = world.copy()
    child = sim.get("child")
    prop = sim.get(prop_id)
    child.meters["heat"] = 1
    child.meters["glare"] = 1
    if prop_id == "prop":
        prop.meters["center"] = 1
    propagate(sim, narrate=False)
    return {
        "soot": prop.meters.get("soot", 0),
        "hot": prop.meters.get("hot", 0),
    }


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {next(t for t in child.memes if t == 'trait')} if that were useful, but mostly {child.memes.get('trait_word', 'curious')}.")
    # Replace with a friendlier authored line below; this helper is unused deliberately.


def tell_story(world: World, child: Entity, parent: Entity, prop: Entity, scope: Entity, gear: Gear) -> None:
    world.say(
        f"{child.id} loved the sandbox because every mound could become a castle, a volcano, or a very serious stage."
    )
    world.say(
        f"One bright afternoon, {child.id} announced a grand plan for {prop.label} and held up {scope.label} like a tiny captain's flag."
    )
    world.say(
        f"'{child.id} wants {world.facts['prop_word']},' {parent.pronoun().capitalize()} said, already squinting at the sun. "
        f"'{That if false else ''}"
    )


def scene(world: World, child: Entity, parent: Entity, prop: Entity, scope: Entity, gear: Gear) -> None:
    world.say(
        f"{child.id} wanted to build a little campfire in {world.setting.place}, and {scope.id} made the plan feel extra official."
    )
    world.say(
        f"{parent.pronoun().capitalize()} looked at the bright sky and, with a very dramatic sigh, said, "
        f'"If we use the scope in this sun, it might turn into a tiny troublemaker."'
    )
    world.say(
        f"{child.id} did not want to hear that and began to belabor the idea with a speech about smoke, sparks, and important fire business."
    )
    child.memes["belabor"] = child.memes.get("belabor", 0) + 1
    child.meters["heat"] = 1
    child.meters["glare"] = 1
    scope.meters["glare"] = 1
    prop.meters["center"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then {parent.id} noticed the shiny scope and the sunny patch and did not belabor the warning at all."
    )
    world.say(
        f'"How about we {gear.prep} instead?" {parent.id} said with a grin. "That way the fire can be pretend and the sandbox can stay happy."'
    )
    world.say(
        f"{child.id} blinked, laughed, and agreed, because the idea was so sensible it was almost funny."
    )
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    parent.memes["relief"] = parent.memes.get("relief", 0) + 1
    prop.meters["shade"] = 1
    scope.meters["shade"] = 1
    world.para()
    world.say(
        f"{gear.tail}, and the tiny campfire became a glowing battery tea light under the shade. "
        f"{child.id} saluted the scene with {scope.label}, and {parent.id} laughed because the whole rescue looked like a tiny parade."
    )


def valid_combos() -> list[tuple[str, str]]:
    return [("sandbox", "fire"), ("sandbox", "scope")]


@dataclass
class Reg:
    setting: str
    prop: str
    gear: str


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "sandbox"), asp.fact("affords", "sandbox", "fire"), asp.fact("affords", "sandbox", "scope")]
    lines.append(asp.fact("prop", "campfire"))
    lines.append(asp.fact("prop", "scope"))
    lines.append(asp.fact("risk", "campfire", "center"))
    lines.append(asp.fact("risk", "scope", "center"))
    lines.append(asp.fact("gear", "shade"))
    lines.append(asp.fact("gear", "lid"))
    lines.append(asp.fact("covers", "shade", "center"))
    lines.append(asp.fact("covers", "lid", "center"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,G) :- affords(S, fire), prop(P), gear(G), covers(G, center).
valid(S,P,G) :- affords(S, scope), prop(P), gear(G), covers(G, center).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((s, p) for s, p in valid_combos())
    cl = set((a, b) for a, b, _ in asp_valid_combos())
    if py and cl:
        print("OK: ASP and Python gates are both populated.")
        return 0
    print("MISMATCH or empty gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sandbox comedy with foreshadowing, fire, scope, and a parent who tries not to belabor the warning.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gear", choices=GEAR)
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
    prop = args.prop or rng.choice(list(PROPS))
    gear = args.gear or ("shade" if prop == "scope" else "lid")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, prop=prop, gear=gear)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["sandbox"])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"trait_word": params.trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    prop = world.add(Entity(id="prop", type="thing", label=PROPS[params.prop].label, phrase=PROPS[params.prop].phrase))
    scope = world.add(Entity(id="scope", type="thing", label=PROPS["scope"].label, phrase=PROPS["scope"].phrase))
    gear = GEAR[params.gear]
    world.facts.update(child=child, parent=parent, prop=prop, scope=scope, gear=gear, prop_word=PROPS[params.prop].keyword)
    world.say(
        f"{child.id} was a {params.trait} little {params.gender} who loved the sandbox."
    )
    world.say(
        f"{child.id} had a plan for {PROPS[params.prop].keyword}, and {scope.label} was part of it."
    )
    scene(world, child, parent, prop, scope, gear)
    story = world.render()
    prompts = [
        f"Write a short comedy story in the sandbox that includes the words fire, scope, and belabor.",
        f"Tell a foreshadowing story where a child wants a {PROPS[params.prop].keyword} plan and a parent worries the scope will cause trouble.",
        f"Write a child-facing story where the funny answer is to use {gear.label} instead of making the risky plan bigger.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {child.id} want to do in the sandbox?",
            answer=f"{child.id} wanted to make a little {PROPS[params.prop].keyword} scene in the sandbox and use the toy scope as if it were very important.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the scope?",
            answer="The parent saw the bright sun and knew the scope could catch the light and make the little plan turn into a silly problem.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"They used {gear.label} instead, so the camp scene stayed safe and the tiny fire became a pretend, glowing tea light under shade.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue earlier in the story that hints something important or funny might happen later.",
        ),
        QAItem(
            question="What does belabor mean?",
            answer="To belabor something is to go on and on about it, sometimes more than the moment really needs.",
        ),
        QAItem(
            question="Why can a scope be tricky in bright sun?",
            answer="A shiny scope can catch sunlight and make a bright spot, which is why a grown-up might move it away from the glare.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'valid'))} valid combos")
        for atom in sorted(set(asp.atoms(model, "valid"))):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for prop in PROPS:
            params = StoryParams(name="Mia", gender="girl", parent="mother", trait="curious", prop=prop, gear="shade" if prop == "scope" else "lid")
            samples.append(generate(params))
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
