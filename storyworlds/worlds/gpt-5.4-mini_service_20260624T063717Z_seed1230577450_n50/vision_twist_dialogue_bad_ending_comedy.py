#!/usr/bin/env python3
"""
vision_twist_dialogue_bad_ending_comedy.py
=========================================

A small storyworld about a child, a vision-based misunderstanding, a twist,
dialogue, and a comedy that ends with a bad ending image.

Premise:
- A child uses a toy telescope / binoculars / camera / magnifier to "spot" a
  supposed surprise.
- The vision is wrong in a funny way: the child mistakes an ordinary object or
  a harmless animal for something grand.
- A twist reveals the object is not what it seemed, and the attempt to fix the
  situation makes things slightly worse.
- The story ends with a comic, mildly bad ending: the mess or embarrassment is
  not fully repaired, but the ending image proves what changed.

The world is classical and state-driven:
- physical meters: sight, distance, mess, wobble, dropped, stuck, shine, etc.
- emotional memes: hope, confusion, pride, embarrassment, laugh, worry, relief.
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


VISION_THRESHOLD = 1.0
TILT_THRESHOLD = 1.0
CONFUSION_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
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

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class VisionTool:
    id: str
    label: str
    verb: str
    reveals: set[str]
    can_misread: bool = True


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    kind: str
    size: str
    sounds_like: str
    actually: str
    trouble: str
    bad_consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    tool: str
    target: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def build_setting_registry() -> dict[str, Setting]:
    return {
        "kitchen": Setting("the kitchen", indoors=True, affordances={"peek", "search", "tidy"}),
        "garden": Setting("the garden", indoors=False, affordances={"peek", "search", "run"}),
        "attic": Setting("the attic", indoors=True, affordances={"peek", "search", "dust"}),
        "yard": Setting("the backyard", indoors=False, affordances={"peek", "search", "run"}),
    }


def build_tools() -> dict[str, VisionTool]:
    return {
        "binoculars": VisionTool("binoculars", "binoculars", "look through the binoculars", {"far"}),
        "telescope": VisionTool("telescope", "a toy telescope", "peer through the telescope", {"far", "shiny"}),
        "magnifier": VisionTool("magnifier", "a magnifying glass", "peek through the magnifying glass", {"small", "tiny"}),
    }


def build_targets() -> dict[str, Target]:
    return {
        "kite": Target("kite", "kite", "a bright kite in a tree", "thing", "far", "a flag", "a kite", "stuck in a branch", "caught on the highest branch", {"far", "shiny"}),
        "cat": Target("cat", "cat", "a sleepy cat on the porch", "animal", "small", "a hat", "a cat", "sleeping on a warm box", "jumped into the laundry basket", {"small"}),
        "spoon": Target("spoon", "spoon", "a shiny spoon on the floor", "thing", "small", "the moon", "a spoon", "under the table", "slid under the couch", {"small", "shiny"}),
        "balloon": Target("balloon", "balloon", "a red balloon by the fence", "thing", "far", "a tomato", "a balloon", "tied to the fence", "popped on a nail", {"far", "shiny"}),
    }


SETTINGS = build_setting_registry()
TOOLS = build_tools()
TARGETS = build_targets()

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Zoe", "Ada"],
    "boy": ["Leo", "Ben", "Finn", "Max", "Owen"],
}
TRAITS = ["curious", "silly", "cheery", "bouncy", "goofy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for t_id, tool in TOOLS.items():
            for x_id, target in TARGETS.items():
                if target.kind == "animal" and "small" not in tool.reveals:
                    continue
                if target.size == "far" and "far" not in tool.reveals:
                    continue
                if s_id == "attic" and x_id == "balloon":
                    continue
                if s_id == "kitchen" and x_id == "kite":
                    continue
                out.append((s_id, t_id, x_id))
    return out


def reasonableness_gate(setting: Setting, tool: VisionTool, target: Target) -> bool:
    if target.kind == "animal" and "small" not in tool.reveals:
        return False
    if target.size == "far" and "far" not in tool.reveals:
        return False
    if setting.place == "the attic" and target.id == "balloon":
        return False
    if setting.place == "the kitchen" and target.id == "kite":
        return False
    return True


def explain_rejection(setting: Setting, tool: VisionTool, target: Target) -> str:
    if target.kind == "animal" and "small" not in tool.reveals:
        return f"(No story: {tool.label} is not good for spotting small animals like the cat.)"
    if target.size == "far" and "far" not in tool.reveals:
        return f"(No story: {tool.label} cannot really help with something far away like that.)"
    return f"(No story: {setting.place} does not make a reasonable stage for {target.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    s_keys = [args.setting] if args.setting else list(SETTINGS)
    t_keys = [args.tool] if args.tool else list(TOOLS)
    x_keys = [args.target] if args.target else list(TARGETS)
    combos = [(s, t, x) for s in s_keys for t in t_keys for x in x_keys if reasonableness_gate(SETTINGS[s], TOOLS[t], TARGETS[x])]
    if not combos:
        if args.setting and args.tool and args.target:
            raise StoryError(explain_rejection(SETTINGS[args.setting], TOOLS[args.tool], TARGETS[args.target]))
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, target = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, tool=tool, target=target, name=name, gender=gender, parent=parent)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for r in sorted(t.reveals):
            lines.append(asp.fact("reveals", tid, r))
    for xid, x in TARGETS.items():
        lines.append(asp.fact("target", xid))
        lines.append(asp.fact("kind", xid, x.kind))
        lines.append(asp.fact("size", xid, x.size))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,X) :- setting(S), tool(T), target(X), allowed(S,T,X).

allowed(S,T,X) :- target(X), kind(X, animal), reveals(T, small), setting(S).
allowed(S,T,X) :- target(X), size(X, far), reveals(T, far), setting(S).
allowed(S,T,X) :- target(X), size(X, small), setting(S).
allowed(S,T,X) :- setting(S), tool(T), target(X), not forbidden(S,T,X).

forbidden(kitchen,_,kite).
forbidden(attic,_,balloon).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about vision, a twist, dialogue, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def _vision_say(world: World, actor: Entity, tool: VisionTool, target: Target) -> None:
    actor.memes["hope"] = actor.memes.get("hope", 0) + 1
    world.say(f"{actor.name} picked up {tool.label} and went to {world.setting.place}.")
    world.say(f"{actor.pronoun().capitalize()} wanted to {tool.verb} and see the surprise.")
    world.say(f"The air felt full of vision and giggles.")


def _mistake(world: World, actor: Entity, target: Target) -> None:
    actor.memes["confusion"] = actor.memes.get("confusion", 0) + 1
    world.say(f"{actor.name} squinted and gasped, because {target.phrase} looked wrong.")
    world.say(f'"Is that a {target.sounds_like}?" {actor.pronoun()} asked.')
    world.facts["misread"] = True


def _twist(world: World, actor: Entity, target: Target) -> None:
    actor.memes["embarrassment"] = actor.memes.get("embarrassment", 0) + 1
    world.say(f"Then came the twist: it was not {target.sounds_like} at all.")
    world.say(f"It was just {target.actually}, and everybody laughed at the big mistake.")
    world.facts["twist"] = target.actually


def _bad_fix(world: World, actor: Entity, parent: Entity, target: Target) -> None:
    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    actor.meters["dropped"] = actor.meters.get("dropped", 0) + 1
    world.say(f'"I can fix it!" {actor.pronoun()} said.')
    world.say(f'But {actor.pronoun()} tried to help and made it worse: {target.bad_consequence}.')
    world.say(f"{parent.name} sighed, then laughed so hard they had to sit down.")
    world.say(f"In the end, {actor.name} still had {target.trouble}, and that was the funny part.")


def tell(setting: Setting, tool: VisionTool, target: Target, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    world.facts.update(hero=hero, parent=parent, tool=tool, target=target, setting=setting)

    _vision_say(world, hero, tool, target)
    world.para()
    _mistake(world, hero, target)
    world.say(f"{parent.name} said, 'Take a closer look!'")
    world.say(f'{hero.name} said, "I am looking closer!"')
    _twist(world, hero, target)
    world.para()
    _bad_fix(world, hero, parent, target)
    world.facts["ending"] = "bad"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tool = f["tool"]
    target = f["target"]
    return [
        f"Write a short comedy story where {hero.name} uses {tool.label} and mistakes {target.phrase} for something else.",
        f"Tell a child-friendly story with vision, a twist, and dialogue ending in a funny bad ending.",
        f"Make a small story about {hero.name} peeking closely, being wrong at first, and making a silly fix that goes badly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, tool, target = f["hero"], f["parent"], f["tool"], f["target"]
    return [
        QAItem(
            question=f"What did {hero.name} use to look more closely?",
            answer=f"{hero.name} used {tool.label} to look more closely at the surprise.",
        ),
        QAItem(
            question=f"What did {hero.name} think {target.phrase} was at first?",
            answer=f"{hero.name} thought it was {target.sounds_like} at first.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that it was really {target.actually}, not {target.sounds_like}.",
        ),
        QAItem(
            question=f"How did the bad ending happen?",
            answer=f"When {hero.name} tried to fix things, {target.bad_consequence}, so the ending stayed messy and funny.",
        ),
        QAItem(
            question=f"Who laughed in the end?",
            answer=f"{parent.name} laughed, and {hero.name} ended up laughing too, even though the fix went wrong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is vision?",
            answer="Vision is the sense people use to see the world with their eyes.",
        ),
        QAItem(
            question="What does a telescope help with?",
            answer="A telescope helps you see things that are far away more clearly.",
        ),
        QAItem(
            question="Why can a wrong guess be funny?",
            answer="A wrong guess can be funny because someone is very sure about something and then learns it was a silly mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOOLS[params.tool], TARGETS[params.target], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:")
        for triple in triples:
            print(" ", triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s, t, x in valid_combos():
            params = StoryParams(setting=s, tool=t, target=x, name="Mia", gender="girl", parent="mother")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
