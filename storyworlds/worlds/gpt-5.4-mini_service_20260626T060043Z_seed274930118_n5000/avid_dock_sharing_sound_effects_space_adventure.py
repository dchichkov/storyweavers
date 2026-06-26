#!/usr/bin/env python3
"""
storyworlds/worlds/avid_dock_sharing_sound_effects_space_adventure.py
=====================================================================

A small, self-contained storyworld: an avid little space-fan at a dock,
sound effects everywhere, and a sharing-based compromise.

Premise source tale, distilled:
---
A child who loved space sounds arrived at a dock with a shining toy console.
The child wanted to make a whole rocket launch by themselves, but a friend
felt left out and the noise rattled a stack of lanterns. After a careful warning,
the child shared the sound console, took turns with the buttons, and the dock
turned into a cheerful little launch scene.

Design:
---
- Typed entities carry physical meters and emotional memes.
- The simulated world drives the prose: want -> warning -> tension -> sharing -> resolution.
- Invalid explicit combinations raise StoryError with a clear reason.
- The ASP twin mirrors the Python reasonableness gate.
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
NOISE_KINDS = {"noise"}
EMOTION_KEYS = {"joy", "eagerness", "stinginess", "sharing", "worry", "belonging", "conflict"}


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the dock"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    intensity: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class SharingTool:
    id: str
    label: str
    phrase: str
    lets_share: bool = True


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.entities.values():
            if ent.kind == "thing" and ent.label == "lanterns" and ent.meters["fragile"] >= THRESHOLD:
                ent.meters["jostled"] += 1
                out.append("The lanterns rattled on the dock.")
                break
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.facts.get("hero")
    buddy = world.facts.get("buddy")
    if not hero or not buddy:
        return []
    if hero.memes["stinginess"] < THRESHOLD:
        return []
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    buddy.memes["worry"] += 1
    return ["__conflict__"]


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_share(tool: SharingTool, prize: Prize, activity: Activity) -> bool:
    return tool.lets_share and prize.kind == "audio" and activity.id == "space_fx"


def at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.kind == "audio" and activity.id == "space_fx"


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"rattled": bool(prize.meters["jostled"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"The {world.setting.place} does not support {activity.verb}.")
    actor.meters["noise"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was an avid little space fan who loved every beep, whoosh, and zoom.")


def arrives(world: World, hero: Entity, buddy: Entity, activity: Activity) -> None:
    world.say(f"One bright day, {hero.id} and {buddy.label} came to {world.setting.place}.")
    world.say(f"The water slapped the posts while the {activity.keyword} kit waited like a tiny launch pad.")


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["eagerness"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} with {hero.pronoun('possessive')} {prize.label} right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not at_risk(activity, prize):
        return False
    pred = predict(world, hero, activity, prize.id)
    if not pred["rattled"]:
        return False
    world.facts["predicted_rattle"] = True
    world.say(f'"If you make all that {activity.sound}, the {prize.label} will shake," {parent.label} said.')
    world.say(f'"Let\'s find a way to share the sounds."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stinginess"] += 1
    world.say(f"{hero.id} pouted and tried to {activity.rush} all by {hero.pronoun('object')} self.")


def share_turns(world: World, buddy: Entity, hero: Entity, tool: SharingTool, activity: Activity) -> None:
    hero.memes["sharing"] += 1
    hero.memes["stinginess"] = 0.0
    buddy.memes["belonging"] += 1
    world.say(
        f"{buddy.label} pointed at {tool.label} and smiled. "
        f'"We can share it," {buddy.pronoun()} said. "You do the loud blast, and I do the soft beep."'
    )


def resolve(world: World, parent: Entity, hero: Entity, buddy: Entity, tool: SharingTool, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id}'s face brightened. {hero.pronoun().capitalize()} handed over the {tool.label} and nodded."
    )
    world.say(
        f"Together they used the {tool.label}; {hero.id} made {activity.sound} sounds, {buddy.label} copied them, "
        f"and the dock became a little rocket show."
    )
    hero.memes["joy"] += 1
    hero.memes["belonging"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f"At the end, the {prize.label} stayed steady, and the waves answered with their own gentle swish."
    )


SETTINGS = {
    "dock": Setting(place="the dock", affords={"space_fx"}),
}

ACTIVITIES = {
    "space_fx": Activity(
        id="space_fx",
        verb="make space sound effects",
        gerund="making space sound effects",
        rush="run the whole sound show",
        sound="beep-whoosh-boom",
        intensity="loud",
        keyword="space",
        tags={"space", "sound", "sharing"},
    ),
}

PRIZES = {
    "lanterns": Prize(
        label="lanterns",
        phrase="a stack of lanterns",
        type="lanterns",
        kind="audio",
        plural=True,
    ),
    "radio": Prize(
        label="radio",
        phrase="a small dock radio",
        type="radio",
        kind="audio",
    ),
    "shells": Prize(
        label="shells",
        phrase="a tray of shell charms",
        type="shells",
        kind="audio",
        plural=True,
    ),
}

TOOLS = {
    "sound_board": SharingTool(
        id="sound_board",
        label="sound board",
        phrase="a bright little sound board",
    ),
    "microphone": SharingTool(
        id="microphone",
        label="microphone",
        phrase="a shiny microphone",
    ),
}

HEROES = ["Ari", "Nova", "Milo", "Zuri", "Ivy", "Kai"]
BUDDIES = ["Pip", "Tess", "Bo", "Remy", "Luna", "Max"]
PARENTS = ["parent", "mom", "dad"]
TRAITS = ["avid", "curious", "lively", "brave", "eager"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    buddy: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if at_risk(act, prize):
                    combos.append((place, aid, pid))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} only matters for noisy audio things, "
        f"but {prize.label} are not an at-risk dock object for this setup.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, buddy, act, prize = f["hero"], f["buddy"], f["activity"], f["prize"]
    return [
        f'Write a short story for a 3-to-5-year-old about an avid child at {world.setting.place} who wants to {act.verb}.',
        f"Tell a space-adventure story where {hero.id} and {buddy.label} share {f['tool'].label} so the {prize.label} stays safe.",
        f'Write a gentle dock story that includes the sound word "{act.sound}" and ends with sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, buddy, parent, act, prize, tool = f["hero"], f["buddy"], f["parent"], f["activity"], f["prize"], f["tool"]
    qa = [
        QAItem(
            question=f"Who is the story about at {world.setting.place}?",
            answer=f"It is about {hero.id}, an avid little space fan, and {buddy.label}, who came along for the dock adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {tool.label}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.pronoun().capitalize()} loved the {act.sound} sounds and wanted to try them right away.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the loud {act.sound} sounds would shake the {prize.label} if {hero.id} made them all alone.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did sharing help at the dock?",
                answer=f"{hero.id} shared the {tool.label} with {buddy.label}, so they could take turns making the sounds while the {prize.label} stayed steady.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dock?",
            answer="A dock is a place by the water where boats can stop, and people can watch the waves and tie things up.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, or taking turns so everyone gets a fair chance.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are made-up sounds like beep, whoosh, and boom that help a story or game feel exciting.",
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, tool_cfg: SharingTool,
         hero_name: str, buddy_name: str, parent_label: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Milo", "Kai", "Max"} else "girl"))
    hero.traits = ["avid", trait]
    buddy = world.add(Entity(id=buddy_name, kind="character", type="girl" if buddy_name in {"Tess", "Luna"} else "boy", label=buddy_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_label if parent_label in {"mother", "father"} else "person", label=parent_label))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=parent.id, plural=prize_cfg.plural))
    prize.meters["fragile"] += 1
    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=hero.id, protective=True))
    lanterns = world.add(Entity(id="Lanterns", type="thing", label="lanterns"))
    lanterns.meters["fragile"] += 1

    world.facts.update(hero=hero, buddy=buddy, parent=parent, prize=prize, tool=tool, activity=activity, setting=setting)

    introduce(world, hero)
    world.para()
    arrives(world, hero, buddy, activity)
    wants(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    world.para()
    share_turns(world, buddy, hero, tool, activity)
    resolve(world, parent, hero, buddy, tool, activity, prize)
    world.facts["resolved"] = True
    return world


CURATED = [
    StoryParams(place="dock", activity="space_fx", prize="lanterns", tool="sound_board", name="Ari", buddy="Pip", parent="mother", trait="brave"),
    StoryParams(place="dock", activity="space_fx", prize="radio", tool="microphone", name="Nova", buddy="Tess", parent="father", trait="eager"),
    StoryParams(place="dock", activity="space_fx", prize="shells", tool="sound_board", name="Milo", buddy="Luna", parent="mother", trait="curious"),
]


KNOWLEDGE_ORDER = ["dock", "sharing", "sound"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("sound", aid, act.sound))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_kind", pid, prize.kind))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.lets_share:
            lines.append(asp.fact("shareable", tid))
    return "\n".join(lines)


ASP_RULES = r"""
risky(A,P) :- activity(A), prize(P), prize_kind(P,audio), sound(A,_).
valid(S,A,P,T) :- affords(S,A), risky(A,P), shareable(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, a, r, t) for (p, a, r) in valid_combos() for t in TOOLS)
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo)} story tuples).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dock-side space-adventure storyworld with sharing and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--buddy", choices=BUDDIES)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.activity and args.prize and args.activity in ACTIVITIES and args.prize in PRIZES:
        if not at_risk(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(list(TOOLS))
    name = args.name or rng.choice(HEROES)
    buddy = args.buddy or rng.choice(BUDDIES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, name=name, buddy=buddy, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], TOOLS[params.tool],
                 params.name, params.buddy, params.parent, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible tuples:")
        for item in vals:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize}, tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
