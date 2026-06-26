#!/usr/bin/env python3
"""
storyworlds/worlds/nurture_wigwam_bad_ending_magic_pirate_tale.py
===================================================================

A small storyworld for a pirate-tale style domain about nurturing a magical
wigwam. The story premise is simple: a young pirate and a little crew try to
care for a magic wigwam on a tiny island. The wigwam needs gentle nurture
(water, songs, patching, lantern-light), but careless use of magic can make it
go wrong. The allowed story shape is intentionally narrow: a setup, a tension
about the wigwam's fragile magic, and a bad ending where the repair fails.

This world is built as a simulation: meters and memes change as actions happen,
and the prose is rendered from that evolving state.
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    magical: bool = False
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    place: str = "the little island"
    sea: bool = True


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mess: str
    risk: str
    requirement: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GoalItem:
    label: str
    phrase: str
    region: str
    fragile: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "windy"
        self.zone: set[str] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.weather = self.weather
        w.zone = set(self.zone)
        return w


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "island": Setting(place="the little island", sea=True),
    "harbor": Setting(place="the harbor cove", sea=True),
    "deck": Setting(place="the ship deck", sea=True),
}

ACTIONS = {
    "water": Action(
        id="water",
        verb="water the wigwam",
        gerund="watering the wigwam",
        mess="damp",
        risk="the reeds would stay thirsty",
        requirement="water",
        keyword="water",
        tags={"water", "nurture", "magic"},
    ),
    "song": Action(
        id="song",
        verb="sing to the wigwam",
        gerund="singing to the wigwam",
        mess="sparkly",
        risk="the magic would get jumpy and wild",
        requirement="song",
        keyword="song",
        tags={"song", "nurture", "magic"},
    ),
    "patch": Action(
        id="patch",
        verb="patch the wigwam",
        gerund="patching the wigwam",
        mess="patched",
        risk="the wind would tug the holes wider",
        requirement="patches",
        keyword="patch",
        tags={"patch", "nurture"},
    ),
    "lantern": Action(
        id="lantern",
        verb="light the lantern by the wigwam",
        gerund="lighting the lantern by the wigwam",
        mess="glow",
        risk="the magic would be lonely in the dark",
        requirement="light",
        keyword="lantern",
        tags={"light", "magic"},
    ),
}

GOALS = {
    "wigwam": GoalItem(
        label="wigwam",
        phrase="a little woven wigwam with shell charms",
        region="shore",
        fragile=True,
    ),
    "magic_map": GoalItem(
        label="magic map",
        phrase="a magic map that shone with sea-blue lines",
        region="hands",
        fragile=True,
    ),
}

NAMES = ["Nia", "Pip", "Mara", "Cora", "Bo", "Sail", "Tess", "Finn"]
TRAITS = ["brave", "small", "cheerful", "curious", "steadfast"]


@dataclass
class StoryParams:
    place: str
    action: str
    goal: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
NURTURE_THRESHOLD = 1.0
WIND_THRESHOLD = 1.0
BROKEN_THRESHOLD = 1.0


def _apply_nurture(world: World) -> list[str]:
    out: list[str] = []
    wigwam = world.get("wigwam")
    for actor in world.characters():
        if actor.meme("care") < NURTURE_THRESHOLD:
            continue
        sig = ("nurture", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        wigwam.meters["safe"] = wigwam.meter("safe") + 1
        out.append(f"{actor.id} tended the wigwam with patient hands.")
    return out


def _apply_wind_damage(world: World) -> list[str]:
    out: list[str] = []
    wigwam = world.get("wigwam")
    if world.weather != "windy":
        return out
    if wigwam.meter("safe") >= NURTURE_THRESHOLD:
        return out
    sig = ("wind",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wigwam.meters["broken"] = wigwam.meter("broken") + 1
    wigwam.memes["fear"] = wigwam.meme("fear") + 1
    out.append("The sea wind shook the little wigwam until the reeds rattled.")
    return out


def _apply_magic_spill(world: World) -> list[str]:
    out: list[str] = []
    wigwam = world.get("wigwam")
    if wigwam.meter("broken") < BROKEN_THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wigwam.meters["magic_spill"] = 1
    out.append("Its magic slipped out in a blue flash and would not come back.")
    return out


CAUSAL_RULES = [_apply_nurture, _apply_wind_damage, _apply_magic_spill]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                lines.extend(got)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def predict_break(world: World, actor: Entity) -> bool:
    sim = world.copy()
    sim.get("wigwam").meters["safe"] = 0
    sim.get("wigwam").memes["care"] = 0
    sim.weather = "windy"
    propagate(sim, narrate=False)
    return sim.get("wigwam").meter("broken") >= BROKEN_THRESHOLD


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, goal: GoalItem) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'brave')} pirate who loved the sea."
    )
    world.say(
        f"On {world.setting.place}, {hero.id} watched over {goal.phrase} and called it {goal.label}."
    )


def desire(world: World, hero: Entity, action: Action) -> None:
    hero.memes["care"] = hero.meme("care") + 1
    world.say(
        f"{hero.id} wanted to {action.verb}, because {action.risk} if nobody helped."
    )


def warning(world: World, hero: Entity, action: Action, goal: GoalItem) -> None:
    if predict_break(world, hero):
        world.say(
            f"The old salt wind warned {hero.id} that {goal.label} would crack if the crew forgot the {action.requirement}."
        )


def mistake(world: World, hero: Entity, action: Action) -> None:
    world.zone = {"shore"}
    world.say(
        f"But {hero.id} got busy with shiny shells and tried to {action.verb} too late."
    )
    propagate(world, narrate=True)


def bad_ending(world: World, hero: Entity, goal: GoalItem) -> None:
    wigwam = world.get("wigwam")
    if wigwam.meter("broken") >= BROKEN_THRESHOLD:
        world.say(
            f"By sunset, the wigwam sagged in the sand, and its magic was gone like foam."
        )
        world.say(
            f"{hero.id} sat quietly beside it, holding the last shell charm while the waves kept singing."
        )
    else:
        world.say(
            f"The wigwam stayed standing, but the world is meant to end badly here, so the story turns solemn."
        )


def tell(setting: Setting, action: Action, goal: GoalItem, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="boy" if hero_name in {"Bo", "Pip", "Finn"} else "girl",
        memes={"care": 0.0, "trait_word": trait},
    ))
    wigwam = world.add(Entity(
        id="wigwam",
        kind="thing",
        type="wigwam",
        label="wigwam",
        phrase=goal.phrase,
        fragile=True,
        magical=True,
        meters={"safe": 0.0, "broken": 0.0, "magic_spill": 0.0},
        memes={"fear": 0.0},
    ))

    world.say(
        f"On a windy morning, {hero.id} found {wigwam.phrase} tucked beside the palms."
    )
    world.say(
        f"It glimmered with a little magic, and {hero.id} promised to nurture it like a ship keeps its lantern lit."
    )

    world.para()
    intro(world, hero, goal)
    desire(world, hero, action)
    warning(world, hero, action, goal)

    world.para()
    mistake(world, hero, action)

    world.para()
    bad_ending(world, hero, goal)

    world.facts.update(hero=hero, wigwam=wigwam, action=action, goal=goal, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    goal = f["goal"]
    return [
        f'Write a short pirate tale for young children that uses the word "{action.keyword}" and features a magical {goal.label}.',
        f"Tell a sea-side story where {hero.id} tries to {action.verb} but the wigwam's magic goes wrong.",
        f"Write a gentle pirate story about nurture, a wigwam, and a bad ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, action, goal = f["hero"], f["action"], f["goal"]
    return [
        QAItem(
            question=f"What did {hero.id} try to do for the wigwam?",
            answer=f"{hero.id} tried to {action.verb}, because the wigwam needed care and the sea wind was rough.",
        ),
        QAItem(
            question="Why was the wigwam in danger?",
            answer=f"It was in danger because it was a fragile magical {goal.label}, and the windy shore could break it if nobody nurtured it.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly. The wigwam sagged in the sand, its magic slipped away, and the pirate sat by the waves in a sad silence.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does nurture mean?",
            answer="To nurture something means to care for it gently so it can stay healthy and grow well.",
        ),
        QAItem(
            question="What is a wigwam?",
            answer="A wigwam is a small shelter made from poles and coverings, shaped like a cozy little house.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is when impossible or surprising things happen, like a glow that moves or a charm that sparkles on its own.",
        ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the pirate tries to nurture the wigwam with one
% of the recognized care actions.
care_action(water).
care_action(song).
care_action(patch).
care_action(lantern).

valid_story(Place, Action, Goal) :-
    setting(Place),
    care_action(Action),
    goal(Goal),
    magical(Goal),
    pirate_tale(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.sea:
            lines.append(asp.fact("pirate_tale", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("verb", aid, a.verb))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        if g.fragile:
            lines.append(asp.fact("fragile", gid))
        lines.append(asp.fact("magical", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {
        (p, a, g)
        for p in SETTINGS
        for a in ACTIONS
        for g in GOALS
        if SETTINGS[p].sea and GOALS[g].fragile and GOALS[g].label == "wigwam"
    }
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-tale storyworld about nurturing a magical wigwam."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name", choices=NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (p, a, g)
        for p in SETTINGS
        for a in ACTIONS
        for g in GOALS
        if SETTINGS[p].sea and GOALS[g].fragile and g == "wigwam"
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.goal is None or c[2] == args.goal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, goal = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, goal=goal, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], GOALS[params.goal], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
        models = asp_valid_stories()
        print(f"{len(models)} compatible story combos:")
        for row in models:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [StoryParams(place="island", action="water", goal="wigwam", name="Nia", trait="steadfast")]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
