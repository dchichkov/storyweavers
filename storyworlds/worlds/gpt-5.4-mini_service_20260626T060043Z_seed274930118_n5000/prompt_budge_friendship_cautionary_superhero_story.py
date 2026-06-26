#!/usr/bin/env python3
"""
Storyworld: prompt budge friendship cautionary superhero story.

A small, child-facing superhero world with a gentle cautionary turn:
a hero gets a risky prompt, a friend tries to budge them toward a safer
choice, and the friendship helps them solve the problem without harm.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    companion: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    fix: str
    use: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for risk in ("spark", "mischief"):
            if actor.meters.get(risk, 0.0) < THRESHOLD:
                continue
            sig = ("spill", actor.id, risk)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["danger"] = actor.meters.get("danger", 0.0) + 1
            out.append(f"{actor.id} was in a risky spot.")
    return out


def _r_friend_budge(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("stubborn", 0.0) < THRESHOLD:
        return out
    sig = ("budge", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["softened"] = hero.memes.get("softened", 0.0) + 1
    out.append("__budge__")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_friend_budge,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__budge__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, action: Action) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the air felt close and bright."
    return f"{setting.place.capitalize()} was open and wide, and the wind kept tugging at capes."


def activity_note(action: Action) -> str:
    return {
        "rescue": "every rescue felt like a promise",
        "hover": "hovering made the rooftops look tiny",
        "signal": "the signal light flashed like a tiny star",
        "riddle": "the riddle made everyone think twice",
    }.get(action.id, "the adventure felt bigger than a single block")


def validate_reasonable(action: Action, tool: Tool) -> bool:
    return action.risk in tool.protects


def choose_tool(action: Action, tools: list[Tool]) -> Optional[Tool]:
    for tool in tools:
        if validate_reasonable(action, tool):
            return tool
    return None


def predict_harm(world: World, hero: Entity, action: Action) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    return {
        "danger": sim.get(hero.id).meters.get("danger", 0.0),
        "softened": sim.get(hero.id).memes.get("softened", 0.0),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.meters[action.risk] = actor.meters.get(action.risk, 0.0) + 1
    actor.memes["courage"] = actor.memes.get("courage", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} hero who loved helping people before dinner."
    )


def friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} and {friend.id} were best friends, and they always looked out for each other."
    )


def prompt(world: World, hero: Entity, friend: Entity, action: Action, tool: Optional[Tool]) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"One day, a flashing prompt popped up on the screen: {action.keyword}. "
        f"{hero.id} wanted to rush in right away."
    )
    world.say(
        f"{friend.id} gave a careful look and said, "
        f"\"Let's not just charge ahead. Let's think first.\""
    )
    if tool:
        world.say(
            f"{friend.id} even pointed at {tool.label}, because a good plan can make a brave choice safer."
        )


def caution(world: World, hero: Entity, friend: Entity, action: Action) -> None:
    pred = predict_harm(world, hero, action)
    world.facts["predicted"] = pred
    if pred["danger"] >= THRESHOLD:
        world.say(
            f"{friend.id} warned that {hero.id} could get into trouble if {hero.pronoun('subject')} kept going."
        )
        world.say(
            f"{hero.id} wanted to {action.rush}, but {friend.id} tried to budge {hero.pronoun('object')} toward a safer way."
        )


def turn(world: World, hero: Entity, friend: Entity, action: Action, tool: Optional[Tool]) -> None:
    if tool is None:
        raise StoryError("No reasonable tool can keep this superhero action safe.")
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    hero.meters[action.risk] = hero.meters.get(action.risk, 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried to {action.rush}, but {friend.id} gently budged {hero.pronoun('object')} to stop."
    )
    world.say(
        f'Together they used {tool.label}, and that was the kind of teamwork that kept a hero calm.'
    )


def resolve(world: World, hero: Entity, friend: Entity, action: Action, tool: Tool) -> None:
    hero.memes["stubborn"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"In the end, {hero.id} listened, and the two friends finished the job the careful way."
    )
    world.say(
        f"{hero.id} was still a hero, just a smarter one, and {friend.id} smiled because the friendship had saved the day."
    )
    world.say(
        f"{setting_detail(world.setting, action)} {activity_note(action)}."
    )


def tell(setting: Setting, action: Action, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "brave", "curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["kind", "careful"]))
    tool_def = choose_tool(action, TOOLS)
    tool = None
    if tool_def:
        tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, owner=hero.id, plural=tool_def.plural))
    world.facts.update(hero=hero, friend=friend, action=action, tool=tool, setting=setting)

    intro(world, hero)
    friendship(world, hero, friend)
    world.para()
    prompt(world, hero, friend, action, tool)
    caution(world, hero, friend, action)
    turn(world, hero, friend, action, tool)
    world.para()
    resolve(world, hero, friend, action, tool)
    return world


@dataclass
class SettingChoice:
    place: str
    indoor: bool
    supports: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting(place="the rooftop garden", indoor=False, supports={"hover", "signal"}),
    "lab": Setting(place="the tiny invention lab", indoor=True, supports={"signal", "riddle"}),
    "city": Setting(place="the city square", indoor=False, supports={"rescue", "signal"}),
}

ACTIONS = {
    "rescue": Action(
        id="rescue",
        verb="rescue the kitten",
        gerund="rescuing kittens",
        rush="dash across the shaky ledge",
        risk="spark",
        effect="sparked trouble",
        keyword="prompt",
        tags={"hero", "friendship", "cautionary"},
    ),
    "hover": Action(
        id="hover",
        verb="hover over the gap",
        gerund="hovering over gaps",
        rush="fly too close to the thunder wire",
        risk="mischief",
        effect="caused a big wobble",
        keyword="budge",
        tags={"hero", "friendship", "cautionary"},
    ),
    "signal": Action(
        id="signal",
        verb="send the signal",
        gerund="sending signals",
        rush="touch the blinking switch",
        risk="spark",
        effect="made a dangerous flash",
        keyword="prompt",
        tags={"hero", "friendship", "cautionary"},
    ),
    "riddle": Action(
        id="riddle",
        verb="solve the riddle",
        gerund="solving riddles",
        rush="lean over the loud console",
        risk="mischief",
        effect="made things tangle up",
        keyword="budge",
        tags={"hero", "friendship", "cautionary"},
    ),
}

TOOLS = [
    Tool(id="goggles", label="safety goggles", fix="keep sparks out", use="wear them", protects={"spark"}),
    Tool(id="gloves", label="soft gloves", fix="steady the hands", use="put them on", protects={"mischief"}, plural=True),
]

HERO_NAMES = ["Nova", "Pip", "Zia", "Milo", "Rae", "Tara", "Jett", "Luna"]
FRIEND_NAMES = ["Comet", "Bree", "Sol", "Dani", "Finn", "Mara", "Nell", "Cleo"]
HERO_TYPES = ["girl", "boy"]
FRIEND_TYPES = ["girl", "boy"]
TRAITS = ["brave", "bright", "cheerful", "quick", "steady"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.supports:
            if aid in ACTIONS:
                out.append((place, aid))
    return sorted(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.supports):
            lines.append(asp.fact("supports", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        lines.append(asp.fact("prompt_word", aid, a.keyword))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for r in sorted(t.protects):
            lines.append(asp.fact("protects", t.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, A) :- supports(P, A), action(A), setting(P).
has_tool(A) :- compatible(P, A), risk_of(A, R), tool(T), protects(T, R).
valid(P, A) :- compatible(P, A), has_tool(A).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    return [
        f'Write a short superhero story for a child that includes the word "{action.keyword}".',
        f"Tell a cautionary friendship story where {hero.id} wants to {action.verb} but {friend.id} gently tries to budge {hero.pronoun('object')} toward a safer choice.",
        f"Write a simple superhero story about a prompt, a warning, and a kind friend helping keep everyone safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    tool = f["tool"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {hero.id}, a little superhero, and {friend.id}, the friend who helped keep things safe.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do after the prompt appeared?",
            answer=f"{hero.id} wanted to {action.verb}, but that was risky, so {friend.id} tried to budge {hero.pronoun('object')} to slow down.",
        ),
        QAItem(
            question=f"How did the friends stay safe?",
            answer=f"They used {tool.label} and chose the careful way, so the job got done without trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and being kind to them when they need it.",
        ),
        QAItem(
            question="Why is caution useful for superheroes?",
            answer="Caution is useful because even brave heroes can stay safer when they stop and think before acting.",
        ),
        QAItem(
            question="What does it mean to budge someone?",
            answer="To budge someone means to gently move them or persuade them a little, like nudging them toward a safer choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.kind == "thing":
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with friendship and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    combos = valid_combos()
    if args.place or args.action:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.action is None or c[1] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action = rng.choice(combos)
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice(FRIEND_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    return StoryParams(place=place, action=action, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], params.hero_name, params.hero_type, params.friend_name, params.friend_type)
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


CURATED = [
    StoryParams(place="city", action="rescue", hero_name="Nova", hero_type="girl", friend_name="Comet", friend_type="boy"),
    StoryParams(place="rooftop", action="hover", hero_name="Pip", hero_type="boy", friend_name="Bree", friend_type="girl"),
    StoryParams(place="lab", action="riddle", hero_name="Zia", hero_type="girl", friend_name="Mara", friend_type="girl"),
    StoryParams(place="city", action="signal", hero_name="Milo", hero_type="boy", friend_name="Cleo", friend_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, action in combos:
            print(f"  {place:10} {action}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.action} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
