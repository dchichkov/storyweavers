#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/refresh_derriere_teamwork_happy_ending_superhero_story.py
========================================================================================

A standalone story world for a tiny superhero teamwork tale with a happy ending.

Seed words: refresh, derriere
Features: teamwork, happy ending
Style: superhero story

The world model tracks a few child-sized facts:
- a team of heroes with physical gear and emotional state
- a mission that leaves one hero sticky, dusty, or tired
- a shared rescue/fix that requires teamwork
- a final refresh beat that leaves everyone proud, clean, and ready to fly again

The script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- emits three QA sets from simulated world state
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
SENSE_MIN = 2


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
    shiny: bool = False
    messy: bool = False
    helper: bool = False
    gadget: bool = False
    washable: bool = False

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    mission: str
    danger: str
    rescue_spot: str


@dataclass
class Challenge:
    id: str
    trouble: str
    cause: str
    aftermath: str
    mess: str
    needs_refresh: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    sense: int
    power: int
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tired"] += 1
        out.append(f"{e.id} looked tired after all the running around.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.characters() if e.role in {"hero", "helper"}]
    if len(team) < 2:
        return out
    if any(e.memes["helped"] >= THRESHOLD for e in team):
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in team:
                e.memes["pride"] += 1
                e.memes["joy"] += 1
            out.append("They worked together like a real superhero team.")
    return out


def _r_refresh(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["refreshed"] < THRESHOLD:
            continue
        sig = ("refresh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] += 1
        e.memes["joy"] += 1
        out.append(f"{e.id} felt fresh and ready again.")
    return out


CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("teamwork", "social", _r_teamwork),
    Rule("refresh", "physical", _r_refresh),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(challenge: Challenge, tool: Tool) -> bool:
    if tool.sense < SENSE_MIN:
        return False
    return challenge.needs_refresh and tool.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for cid in CHALLENGES:
            for tid in TOOLS:
                if reasonableness_ok(CHALLENGES[cid], TOOLS[tid]):
                    out.append((sid, cid, tid))
    return out


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def predict_problem(world: World, hero_id: str, challenge_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    challenge = CHALLENGES[challenge_id]
    hero.meters["mess"] += 1
    hero.meters["refreshed"] += 1
    propagate(sim, narrate=False)
    return {
        "messy": hero.meters["mess"] >= THRESHOLD,
        "joy": hero.memes["joy"],
        "helper_pride": sum(e.memes["pride"] for e in sim.characters()),
        "challenge": challenge.aftermath,
    }


def do_mission(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    hero.meters["mess"] += 1
    hero.memes["bravery"] += 1
    helper.memes["helped"] += 1
    world.say(
        f"On a bright day, {hero.id} and {helper.id} zoomed through {world.setting.label}. "
        f"They were on a rescue mission to {world.setting.mission}."
    )
    world.say(
        f"Then {challenge.cause}, and {hero.id} got {challenge.mess} from top to {hero.label_word}.'s "
        f"derriere while trying to save the day."
    )


def check_problem(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    pred = predict_problem(world, hero.id, challenge.id)
    world.facts["predicted"] = pred
    world.say(
        f"{helper.id} frowned and pointed. \"If we keep going like this, you'll stay {challenge.mess}. "
        f"We need a clever fix,\" {helper.pronoun()} said."
    )


def teamwork_fix(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.meters["refreshed"] += 1
    helper.meters["refreshed"] += 1
    hero.meters["mess"] = 0
    helper.meters["mess"] = 0
    hero.memes["helped"] += 1
    helper.memes["helped"] += 1
    world.say(
        f"Together they used {tool.phrase}; it {tool.effect}. The sticky bits vanished, and even "
        f"{hero.id}'s derriere felt smooth and fresh again."
    )
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, {hero.id} grinned and struck a hero pose. {helper.id} laughed, and the whole team "
        f"flew home clean, fresh, and proud."
    )
    world.say(
        f"The sun sparkled on their capes, and the city below seemed safer because {hero.id} and "
        f"{helper.id} had teamed up so well."
    )


def tell(setting: Setting, challenge: Challenge, tool: Tool,
         hero_name: str = "Nova", hero_type: str = "girl",
         helper_name: str = "Bolt", helper_type: str = "boy",
         captain_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            traits=["brave", "kind"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper",
                              traits=["clever", "steady"]))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, role="captain",
                               label="the captain"))
    world.add(Entity(id="tool", type="tool", label=tool.label, gadget=True, washable=True))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["captain"] = captain
    world.facts["setting"] = setting
    world.facts["challenge"] = challenge
    world.facts["tool"] = tool

    do_mission(world, hero, helper, challenge)
    world.para()
    check_problem(world, hero, helper, challenge)
    if reasonableness_ok(challenge, tool):
        world.say(
            f"{helper.id} smiled. \"I know a way to refresh you fast,\" {helper.pronoun()} said."
        )
    world.para()
    teamwork_fix(world, hero, helper, tool)
    world.para()
    ending(world, hero, helper, challenge)
    world.facts["outcome"] = "happy"
    return world


SETTINGS = {
    "city": Setting("city", "the city", "protect the parade float", "a burst of confetti stuck everywhere", "the hero station"),
    "harbor": Setting("harbor", "the harbor", "guide the boat safely in", "spray from the waves soaked everything", "the lighthouse room"),
    "park": Setting("park", "the park", "save the picnic baskets", "mud splashed up from the path", "the hero tower"),
}

CHALLENGES = {
    "confetti": Challenge("confetti", "the parade needed saving", "a confetti cannon popped too close", "the heroes were covered in sticky glitter", "sticky glitter"),
    "waves": Challenge("waves", "the boat needed guidance", "a wave splashed right over the deck", "the heroes were drenched and salty", "wet salt spray"),
    "mud": Challenge("mud", "the picnic needed saving", "a muddy puddle burst under their boots", "the heroes were muddy from cape to derriere", "mud"),
}

TOOLS = {
    "towel": Tool("towel", "super towel", "a super towel", "made everything dry and bright", 3, 2, {"refresh"}),
    "spray": Tool("spray", "refresh spray", "a refreshing spray bottle", "washed away the sticky mess", 3, 2, {"refresh"}),
    "fan": Tool("fan", "cool fan", "a cool fan", "blew the dust right off", 2, 1, {"refresh"}),
}


@dataclass
class StoryParams:
    setting: str
    challenge: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    captain: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    challenge = f["challenge"]
    tool = f["tool"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "refresh" and "derriere".',
        f"Tell a happy teamwork story where {hero.id} and {helper.id} solve a messy problem with {tool.label}.",
        f"Write a short superhero adventure where the team gets messy, finds a refresh fix, and ends proud and clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    challenge = f["challenge"]
    tool = f["tool"]
    return [
        QAItem(
            question="Who are the story's superheroes?",
            answer=f"The story is about {hero.id} and {helper.id}. They were a superhero team who worked together to solve a problem."
        ),
        QAItem(
            question="What problem did they have?",
            answer=f"They got {challenge.mess} while trying to save the day. That made them look for a clever way to refresh themselves and keep going."
        ),
        QAItem(
            question="How did they fix it?",
            answer=f"They used {tool.phrase} together. It {tool.effect}, so the mess went away and the team could finish happily."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something better than one person could do alone."
        ),
        QAItem(
            question="What does refresh mean?",
            answer="Refresh means to make someone feel clean, cool, or ready again after they are tired or messy."
        ),
        QAItem(
            question="Why do heroes sometimes need a helper?",
            answer="A helper can bring an idea, a tool, or extra hands, and that can turn a hard job into a happy win."
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.shiny:
            bits.append("shiny")
        if e.messy:
            bits.append("messy")
        if e.helper:
            bits.append("helper")
        if e.gadget:
            bits.append("gadget")
        if e.washable:
            bits.append("washable")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("city", "confetti", "towel", "Nova", "girl", "Bolt", "boy", "Captain"),
    StoryParams("harbor", "waves", "spray", "Iris", "girl", "Milo", "boy", "Captain"),
    StoryParams("park", "mud", "fan", "Zane", "boy", "Luna", "girl", "Captain"),
]


def explain_rejection(challenge: Challenge, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return f"(No story: {tool.label} is too weak or too odd for a real superhero fix.)"
    return "(No story: this combination does not make a believable cleanup-and-refresh scene.)"


def valid_asp_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(S, C, T) :- setting(S), challenge(C), tool(T), needs_refresh(C), tool_sense(T, N), sense_min(M), N >= M.
teamwork :- hero(H), helper(X), hero(H), helper(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        if c.needs_refresh:
            lines.append(asp.fact("needs_refresh", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, challenge=None, tool=None, hero=None, hero_gender=None, helper=None, helper_gender=None, captain=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero teamwork story world with a refresh ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_rejection(CHALLENGES[args.challenge or "confetti"], TOOLS[args.tool]))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.challenge:
        combos = [c for c in combos if c[1] == args.challenge]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Nova", "Iris", "Zane", "Sky", "Mira", "Pax"])
    helper = args.helper or rng.choice([n for n in ["Bolt", "Comet", "Flash", "Echo", "Spark", "Jet"] if n != hero])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    captain = args.captain or rng.choice(["mother", "father"])
    return StoryParams(setting, challenge, tool, hero, hero_gender, helper, helper_gender, captain)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHALLENGES[params.challenge],
        TOOLS[params.tool],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.captain,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for s, c, t in combos:
            print(f"  {s:8} {c:10} {t}")
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
            header = f"### {p.hero} & {p.helper}: {p.setting}, {p.challenge}, {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
