#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/apricot_easel_jettison_teamwork_fairy_tale.py
=============================================================================

A small fairy-tale storyworld about two helpers, a precious apricot, an easel,
and the choice to jettison something too heavy so teamwork can save the day.

The domain is intentionally tiny and classical:
- a young painter/prince/princess/child is trying to keep a fair-day painting safe
- an apricot is the bright, fragile prize
- an easel is the awkward object that can cause trouble if carried alone
- jettison means to throw away or let go of something heavy enough to stop the
  journey unless the helpers work together

The story engine tracks physical meters and emotional memes, uses a reasonableness
gate, includes an inline ASP twin, and can render short child-facing stories with
grounded Q&A.
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
HELP_MIN = 2.0
HEAVY_MIN = 2.0
LOSSY_MIN = 2.0
TEAM_MIN = 2.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "princess"}
        male = {"boy", "father", "king", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class StoryParams:
    setting: str
    helper1: str
    helper1_gender: str
    helper2: str
    helper2_gender: str
    parent: str
    prize: str
    tool: str
    action: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    scene: str
    place: str
    weather: str
    fairy_note: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    precious: bool = True
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    heavy: bool
    gives_way: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    past: str
    reason: str
    risk: str
    result: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_drop_load(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("guide")
    tool = world.get("easel")
    if guide.memes["burden"] >= HELP_MIN and tool.meters["heavy"] >= HEAVY_MIN:
        sig = ("drop_load",)
        if sig not in world.fired:
            world.fired.add(sig)
            guide.memes["relief"] += 1
            tool.meters["carried"] = 0.0
            out.append("__drop__")
    return out


def _r_team_brighten(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["teamwork"] < TEAM_MIN:
            continue
        sig = ("team_brighten", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__team__")
    return out


CAUSAL_RULES = [Rule("drop_load", "physical", _r_drop_load), Rule("team_brighten", "social", _r_team_brighten)]


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


def valid_story(setting: Setting, prize: Prize, tool: Tool, action: Action) -> bool:
    return prize.fragile and tool.heavy and tool.gives_way and action.id == "jettison"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PRIZES:
            for tid in TOOLS:
                for aid in ACTIONS:
                    if valid_story(SETTINGS[sid], PRIZES[pid], TOOLS[tid], ACTIONS[aid]):
                        combos.append((sid, pid, tid, aid))
    return combos


def predict_issue(world: World, action: Action, tool: Tool) -> dict:
    sim = world.copy()
    sim.get("guide").memes["burden"] += 1
    sim.get("guide").meters["sway"] += 1
    if tool.heavy:
        sim.get("easel").meters["heavy"] += 1
    return {"trouble": sim.get("guide").memes["burden"] >= HELP_MIN}


def setup(world: World, hero: Entity, companion: Entity, setting: Setting, prize: Prize, tool: Tool) -> None:
    hero.memes["curiosity"] += 1
    companion.memes["care"] += 1
    world.say(
        f"In a little fairy kingdom, {hero.id} and {companion.id} came to {setting.scene}. "
        f"{setting.fairy_note}"
    )
    world.say(
        f"At the center stood {prize.phrase}, and beside it waited {tool.phrase}."
    )


def want_to_move(world: World, hero: Entity, setting: Setting, prize: Prize, tool: Tool, action: Action) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'{hero.id} wanted to {action.verb} the {tool.label} so the {prize.label} could travel safely. '
        f'{action.reason}'
    )
    world.say(f'But {action.risk}.')


def teamwork_hint(world: World, hero: Entity, companion: Entity, tool: Tool, action: Action) -> None:
    companion.memes["teamwork"] += 1
    hero.memes["teamwork"] += 1
    pred = predict_issue(world, action, tool)
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{companion.id} nodded. "{hero.id}, let us work together," {companion.id} said. '
        f'"If we both lift, the load will not win."'
    )


def jettison(world: World, hero: Entity, companion: Entity, tool: Tool, prize: Prize, action: Action) -> None:
    hero.memes["burden"] += 1
    companion.memes["burden"] += 1
    tool.meters["heavy"] += 1
    world.say(
        f'Then they decided to {action.verb} the extra weight. Together they lifted the {tool.label}, '
        f'and with a quick "Now!" they let the heavy part go.'
    )
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, companion: Entity, prize: Prize, tool: Tool, action: Action) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    prize.meters["safe"] += 1
    world.say(
        f'The load became light enough to carry, and the {prize.label} stayed bright and untouched. '
        f'{hero.id} and {companion.id} smiled like two children in a lantern-lit tale.'
    )
    world.say(
        f'By dusk, the {tool.label} had been set aside, the {prize.label} rested in a basket, '
        f'and the two friends walked home together.'
    )


def tell(setting: Setting, prize: Prize, tool: Tool, action: Action,
         helper1: str = "Mina", helper1_gender: str = "girl",
         helper2: str = "Tomas", helper2_gender: str = "boy",
         parent: str = "queen") -> World:
    world = World()
    hero = world.add(Entity(id=helper1, kind="character", type=helper1_gender, role="helper"))
    companion = world.add(Entity(id=helper2, kind="character", type=helper2_gender, role="helper"))
    parent_ent = world.add(Entity(id=parent, kind="character", type="queen", role="parent", label="the queen"))
    prize_ent = world.add(Entity(id="apricot", type=prize.type, label=prize.label))
    tool_ent = world.add(Entity(id="easel", type="thing", label=tool.label))
    world.facts.update(hero=hero, companion=companion, parent=parent_ent, prize=prize_ent, tool=tool_ent, setting=setting, action=action)

    setup(world, hero, companion, setting, prize, tool)
    world.para()
    want_to_move(world, hero, setting, prize, tool, action)
    teamwork_hint(world, hero, companion, tool, action)
    world.para()
    jettison(world, hero, companion, tool, prize, action)
    resolve(world, hero, companion, prize, tool, action)

    world.facts.update(
        outcome="saved",
        teamwork=hero.memes["teamwork"] >= TEAM_MIN,
        burden=hero.memes["burden"],
    )
    return world


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        scene="the apple orchard at the edge of the little kingdom",
        place="orchard",
        weather="golden",
        fairy_note="The trees wore blossoms like crowns, and the path glittered with dew.",
    ),
    "garden": Setting(
        id="garden",
        scene="the palace garden with a singing fountain",
        place="garden",
        weather="soft",
        fairy_note="Birds tucked their heads under their wings and listened to the fountain hum.",
    ),
}

PRIZES = {
    "apricot": Prize(
        id="apricot",
        label="apricot",
        phrase="a bright apricot on a silver plate",
        type="fruit",
        tags={"apricot", "fruit"},
    ),
}

TOOLS = {
    "easel": Tool(
        id="easel",
        label="easel",
        phrase="an old easel with one wobbly leg",
        heavy=True,
        gives_way=True,
        tags={"easel"},
    ),
    "crate": Tool(
        id="crate",
        label="crate",
        phrase="a crate of old boards",
        heavy=True,
        gives_way=True,
        tags={"crate"},
    ),
}

ACTIONS = {
    "jettison": Action(
        id="jettison",
        verb="jettison",
        past="jettisoned",
        reason="They could not carry the easel and the apricot in one careful trip.",
        risk="one person alone would have dropped the prize",
        result="the burden vanished",
        tags={"jettison", "teamwork"},
    )
}


GIRL_NAMES = ["Mina", "Lina", "Elise", "Nora", "Iris"]
BOY_NAMES = ["Tomas", "Owen", "Perry", "Jasper", "Theo"]
PARENT_NAMES = ["queen", "king"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, companion, setting, action = f["hero"], f["companion"], f["setting"], f["action"]
    return [
        f'Write a fairy-tale story for a young child about teamwork, using the words "apricot", "easel", and "jettison".',
        f'Tell a gentle fairy tale where {hero.id} and {companion.id} work together in {setting.scene} and decide to {action.verb} something heavy.',
        f'Write a short story about two helpers, an apricot, and an easel, where teamwork helps them finish the journey safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, companion, prize, tool, action = f["hero"], f["companion"], f["prize"], f["tool"], f["action"]
    setting = f["setting"]
    qa = [
        (
            "Who helped in the story?",
            f"{hero.id} and {companion.id} helped each other. They worked as a team, so the heavy part did not have to be carried alone."
        ),
        (
            "What was special about the apricot?",
            f"It was the bright prize they wanted to keep safe. The story treats the apricot like a tiny treasure from a fairy kingdom."
        ),
        (
            "Why did they jettison the extra weight?",
            f"They jettisoned it because the easel was too heavy for one helper. When they let the extra weight go together, the rest of the journey became safe and easy."
        ),
        (
            "What happened to the easel?",
            f"The easel was set aside after they jettisoned the heavy part. It was no longer in the way, which let them carry the apricot without trouble."
        ),
        (
            "Where did the story happen?",
            f"It happened in {setting.scene}. The place feels like a fairy tale because it has a magical, gentle mood."
        ),
    ]
    if f.get("teamwork"):
        qa.append((
            "How did teamwork change the ending?",
            f"Teamwork made the burden smaller and the apricot stayed safe. Because both helpers shared the work, they finished together instead of failing alone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["action"].tags) | set(world.facts["prize"].tags) | set(world.facts["tool"].tags)
    out: list[tuple[str, str]] = []
    if "apricot" in tags:
        out.append(("What is an apricot?", "An apricot is a small orange fruit with soft skin and sweet flesh."))
    if "easel" in tags:
        out.append(("What is an easel?", "An easel is a stand that holds up a painting while someone works on it."))
    if "jettison" in tags:
        out.append(("What does jettison mean?", "To jettison means to throw off or let go of something so it does not weigh you down."))
    if "teamwork" in tags:
        out.append(("What is teamwork?", "Teamwork is when people help each other and share the work so a hard job becomes easier."))
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="orchard", helper1="Mina", helper1_gender="girl", helper2="Tomas", helper2_gender="boy", parent="queen", prize="apricot", tool="easel", action="jettison"),
    StoryParams(setting="garden", helper1="Lina", helper1_gender="girl", helper2="Theo", helper2_gender="boy", parent="king", prize="apricot", tool="crate", action="jettison"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this fairy-tale domain only tells teamwork scenes where the apricot is protected by jettisoning an extra burden.)"


ASP_RULES = r"""
valid(S, P, T, A) :- setting(S), prize(P), tool(T), action(A),
                    fragile(P), heavy(T), gives_way(T), can_jettison(A).

teamwork(2).
saved :- valid(_, _, _, _), teamwork(N), N >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.heavy:
            lines.append(asp.fact("heavy", tid))
        if t.gives_way:
            lines.append(asp.fact("gives_way", tid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if a.id == "jettison":
            lines.append(asp.fact("can_jettison", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        a = set(asp_valid_combos())
        b = set(valid_combos())
        if a == b:
            print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid combos:")
            print("  only in ASP:", sorted(a - b))
            print("  only in Python:", sorted(b - a))
        sample = generate(CURATED[0])
        if not sample.story or "apricot" not in sample.story or "easel" not in sample.story:
            raise RuntimeError("smoke test story missing required words")
        print("OK: generation smoke test passed.")
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale teamwork storyworld about an apricot, an easel, and jettisoning extra weight.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--parent", choices=["queen", "king"])
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
    if args.action and args.action != "jettison":
        raise StoryError("This world only tells the teamwork version of the tale: the helpers must jettison the extra weight.")
    choices = [
        (s, p, t, a)
        for (s, p, t, a) in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.prize is None or p == args.prize)
        and (args.tool is None or t == args.tool)
        and (args.action is None or a == args.action)
    ]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prize, tool, action = rng.choice(sorted(choices))
    helper1_gender = rng.choice(["girl", "boy"])
    helper2_gender = "boy" if helper1_gender == "girl" else "girl"
    helper1 = args.name1 or rng.choice(GIRL_NAMES if helper1_gender == "girl" else BOY_NAMES)
    helper2 = args.name2 or rng.choice([n for n in (BOY_NAMES if helper1_gender == "girl" else GIRL_NAMES) if n != helper1])
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(setting=setting, helper1=helper1, helper1_gender=helper1_gender, helper2=helper2, helper2_gender=helper2_gender, parent=parent, prize=prize, tool=tool, action=action)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.prize not in PRIZES or params.tool not in TOOLS or params.action not in ACTIONS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        setting=SETTINGS[params.setting],
        prize=PRIZES[params.prize],
        tool=TOOLS[params.tool],
        action=ACTIONS[params.action],
        helper1=params.helper1,
        helper1_gender=params.helper1_gender,
        helper2=params.helper2,
        helper2_gender=params.helper2_gender,
        parent=params.parent,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, p, t, a in combos:
            print(f"  {s:8} {p:8} {t:8} {a}")
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
            header = f"### {p.helper1} and {p.helper2}: {p.prize} with {p.tool} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
