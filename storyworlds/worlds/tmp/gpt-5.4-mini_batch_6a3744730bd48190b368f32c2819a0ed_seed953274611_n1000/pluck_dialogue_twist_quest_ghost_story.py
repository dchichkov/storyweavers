#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pluck_dialogue_twist_quest_ghost_story.py
==========================================================================
A small Storyweavers storyworld about a child, a ghostly quest, a spoken clue,
and a twist that turns a spooky chase into a kindly ending.

The world is built for a ghost-story tone: dim hallways, whispering dialogue,
a quest for a lost keepsake, and one important twist that changes what the
characters think the ghost wants. The word "pluck" appears naturally in the
story as both an action and a spoken prompt.

This file is self-contained aside from the shared storyworld result/ASP helpers.
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
SENSE_MIN = 2
WISP_WORRY_INIT = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    haunted: bool = False
    glows: bool = False

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
        return self.label or self.type


@dataclass
class ThingCfg:
    id: str
    label: str
    phrase: str
    room: str
    visible: bool = True
    haunted: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostCfg:
    id: str
    label: str
    title: str
    clue: str
    demand: str
    twist_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestCfg:
    id: str
    goal: str
    place: str
    action: str
    word: str
    requires_dialogue: bool = True
    tags: set[str] = field(default_factory=set)


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if "ghost" not in world.entities or "child" not in world.entities:
        return out
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.meters["mystery"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["worry"] += 1
        out.append("__spooky__")
    return out


def _r_bell(world: World) -> list[str]:
    out: list[str] = []
    if "bell" in world.entities:
        bell = world.get("bell")
        if bell.meters["found"] >= THRESHOLD and ("bell_ring",) not in world.fired:
            world.fired.add(("bell_ring",))
            out.append("A tiny bell rang from the dark.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("bell", _r_bell)]


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
        for s in produced:
            world.say(s)
    return produced


def quest_valid(ghost: GhostCfg, quest: QuestCfg, thing: ThingCfg) -> bool:
    return thing.haunted and quest.place == thing.room and ghost.id in {"ghost", "lantern_ghost"}


def sensible_ghosts() -> list[GhostCfg]:
    return [g for g in GHOSTS.values() if g.id in {"ghost", "lantern_ghost"}]


def outcome_of(params: "StoryParams") -> str:
    return "resolved" if params.response == "kind" else "twist"


def explain_rejection(thing: ThingCfg, quest: QuestCfg) -> str:
    if not thing.haunted:
        return "(No story: that place is too ordinary for a ghost-quest twist.)"
    if quest.place != thing.room:
        return "(No story: the quest does not point to the haunted room.)"
    return "(No story: this combination does not make a clear ghost story.)"


@dataclass
class StoryParams:
    setting: str
    ghost: str
    quest: str
    thing: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    response: str
    seed: Optional[int] = None


SETTINGS = {
    "old_house": {"place": "the old house", "dark": "the long hallway", "tone": "empty and cold"},
    "school": {"place": "the shut-up school", "dark": "the music room", "tone": "silent and dusty"},
}

GHOSTS = {
    "ghost": GhostCfg(
        id="ghost",
        label="a pale ghost",
        title="the ghost",
        clue="Pluck the string, and listen.",
        demand="I am looking for my lost bell",
        twist_line="The ghost was not angry at all; it only wanted help.",
        tags={"ghost", "quest", "dialogue", "twist"},
    ),
    "lantern_ghost": GhostCfg(
        id="lantern_ghost",
        label="a lantern ghost",
        title="the lantern ghost",
        clue="Pluck the cord, then follow the glow.",
        demand="I am looking for my lost key",
        twist_line="The glowing ghost had been guiding them, not chasing them.",
        tags={"ghost", "quest", "dialogue", "twist"},
    ),
}

QUESTS = {
    "bell_quest": QuestCfg(
        id="bell_quest",
        goal="find the lost bell",
        place="attic",
        action="search the attic boards",
        word="pluck",
        tags={"quest", "dialogue"},
    ),
    "key_quest": QuestCfg(
        id="key_quest",
        goal="find the lost key",
        place="music room",
        action="search under the old piano",
        word="pluck",
        tags={"quest", "dialogue"},
    ),
}

THINGS = {
    "bell": ThingCfg(id="bell", label="bell", phrase="a little silver bell", room="attic", haunted=True, tags={"bell"}),
    "key": ThingCfg(id="key", label="key", phrase="an old brass key", room="music room", haunted=True, tags={"key"}),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Ivy", "Maya"]
NAMES_BOY = ["Eli", "Noah", "Finn", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GHOSTS:
            for q in QUESTS:
                for t in THINGS:
                    if quest_valid(GHOSTS[g], QUESTS[q], THINGS[t]):
                        combos.append((s, g, q, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest world with a dialogue twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--response", choices=["kind", "fear"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.response == "fear":
        raise StoryError("(No story: the ghost-story twist needs a kind ending, not only fright.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.quest is None or c[2] == args.quest)
              and (args.thing is None or c[3] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ghost, quest, thing = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    child_name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_name = args.helper or rng.choice(NAMES_BOY if helper_gender == "boy" else NAMES_GIRL)
    return StoryParams(
        setting=setting, ghost=ghost, quest=quest, thing=thing,
        child_name=child_name, child_gender=gender,
        helper_name=helper_name, helper_gender=helper_gender,
        response=args.response or "kind",
    )


def _setup(world: World, params: StoryParams) -> None:
    s = SETTINGS[params.setting]
    g = GHOSTS[params.ghost]
    q = QUESTS[params.quest]
    t = THINGS[params.thing]
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="seeker"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="listener"))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label=g.label, role="ghost", haunted=True))
    thing = world.add(Entity(id="thing", kind="thing", type="thing", label=t.label, haunted=True))
    bell = world.add(Entity(id="bell", kind="thing", type="thing", label=t.label, haunted=True))
    world.facts.update(setting=s, ghost_cfg=g, quest_cfg=q, thing_cfg=t, child=child, helper=helper, ghost=ghost, bell=bell)
    child.memes["curiosity"] = 2
    ghost.meters["mystery"] = 1
    thing.meters["lost"] = 1


def tell(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    s = SETTINGS[params.setting]
    g = GHOSTS[params.ghost]
    q = QUESTS[params.quest]
    t = THINGS[params.thing]
    child = world.get("child")
    helper = world.get("helper")
    ghost = world.get("ghost")
    child.memes["bravery"] += 1
    world.say(f"On a night when {s['tone']}, {child.label} and {helper.label} crept into {s['place']}.")
    world.say(f'Their quest was simple: {q.goal}.')
    world.para()
    world.say(f"In the dark, a voice whispered, \"{g.clue}\"")
    world.say(f"{helper.label} shivered. \"Did you hear that?\" {helper.pronoun()} asked.")
    world.say(f"{child.label} swallowed hard. \"Yes,\" {child.pronoun()} whispered, \"but I think it wants us to {q.action}.\"")
    if params.response == "kind":
        world.say(f"The ghost drifted closer and said, \"{g.demand}.\"")
        world.say(f"{helper.label} blinked. \"A ghost asking for help?\"")
        world.say(f'{child.label} reached into the dust and gave a careful pluck at the loose string hanging from the rafters.')
        world.say("A tiny sound answered from above, soft as a sigh.")
        thing.meters["found"] += 1
        ghost.meters["mystery"] += 1
        propagate(world, narrate=True)
        world.para()
        world.say(f'Then came the twist: {g.twist_line}')
        world.say(f'The bell was not a warning after all. It was the ghost\'s lost keepsake, and the ghost had been waiting for someone brave enough to listen.')
        world.say(f"{child.label} put the bell in {helper.label}'s hands. \"We found it,\" {child.pronoun()} said, and the hallway felt less cold.")
        world.say(f'The ghost smiled until it looked almost like moonlight. "Thank you," it whispered, and the dark house felt wide awake and safe.')
    else:
        world.say("The ghost's whisper made the boards tremble, and the children ran back to the stairway.")
        world.say("But they did not run away forever. They returned with a lamp, followed the clue, and finished the quest with calmer hearts.")
    world.facts["outcome"] = outcome_of(params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest_cfg"]
    g = f["ghost_cfg"]
    return [
        f'Write a ghost story for a young child that includes the word "pluck" and a spoken clue.',
        f"Tell a spooky but gentle quest story where {f['child'].label} and {f['helper'].label} search for {q.goal} and hear {g.clue}",
        f"Write a dialogue-heavy ghost story with a twist: the ghost seems scary first, but the ending changes what everyone thinks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ghost_cfg = f["ghost_cfg"]
    q = f["quest_cfg"]
    t = f["thing"]
    return [
        QAItem(
            question="What was the quest?",
            answer=f"The quest was to {q.goal}. The children went into the dark place because they wanted to solve the ghost's mystery."
        ),
        QAItem(
            question="What did the ghost say?",
            answer=f"The ghost said, \"{ghost_cfg.clue}\" It was a clue, not just a scare, and it pointed the children toward the lost thing."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the ghost was not hunting the children at all. It only wanted help finding {t.phrase}, so the scary moment turned into a kind one."
        ),
        QAItem(
            question=f"Why did {child.label} pluck the string?",
            answer=f"{child.label} plucked the string because the clue told them to listen for a sound. That small move helped them find the lost object and finish the quest."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with the lost thing found and the ghost soothed. The hallway stayed dark, but it no longer felt unfriendly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a ghost in a story?", "A ghost in a story is usually a spooky spirit character that may whisper, glow, or appear in the dark."),
        QAItem("What is a quest?", "A quest is a search for something important. The characters keep going until they solve the problem or find the missing thing."),
        QAItem("What does a clue do?", "A clue gives a helpful hint. It points the characters toward what they need to do next."),
    ]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.haunted:
            bits.append("haunted=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="old_house", ghost="ghost", quest="bell_quest", thing="bell", child_name="Mina", child_gender="girl", helper_name="Eli", helper_gender="boy", response="kind"),
    StoryParams(setting="school", ghost="lantern_ghost", quest="key_quest", thing="key", child_name="Noah", child_gender="boy", helper_name="Ivy", helper_gender="girl", response="kind"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("demand", gid, g.demand))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("place", qid, q.place))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.haunted:
            lines.append(asp.fact("haunted", tid))
        lines.append(asp.fact("room", tid, t.room))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G,Q,T) :- setting(S), ghost(G), quest(Q), thing(T), haunted(T), place(Q,P), room(T,P).
twist_ready(G,Q,T) :- ghost(G), quest(Q), thing(T), haunted(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, ghost=None, quest=None, thing=None, response=None, name=None, helper=None, gender=None, helper_gender=None), _random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.response not in {"kind", "fear"}:
        raise StoryError("invalid response")
    if params.response == "fear":
        raise StoryError("(No story: this world wants a gentle ghost-story twist.)")
    if params.setting not in SETTINGS or params.ghost not in GHOSTS or params.quest not in QUESTS or params.thing not in THINGS:
        raise StoryError("(No story: invalid parameters.)")
    world = tell(params)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("invalid setting")
    if args.ghost and args.ghost not in GHOSTS:
        raise StoryError("invalid ghost")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("invalid quest")
    if args.thing and args.thing not in THINGS:
        raise StoryError("invalid thing")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.quest is None or c[2] == args.quest)
              and (args.thing is None or c[3] == args.thing)]
    if not combos:
        raise StoryError(explain_rejection(THINGS[args.thing] if args.thing else next(iter(THINGS.values())),
                                           QUESTS[args.quest] if args.quest else next(iter(QUESTS.values()))))
    setting, ghost, quest, thing = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    return StoryParams(
        setting=setting, ghost=ghost, quest=quest, thing=thing,
        child_name=args.name or _pick_name(rng, gender),
        child_gender=gender,
        helper_name=args.helper or _pick_name(rng, helper_gender),
        helper_gender=helper_gender,
        response=args.response or "kind",
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible ghost-quest combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
