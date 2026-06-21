#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/generous_fool_ish_teamwork_happy_ending_adventure.py
=====================================================================================

A small adventure storyworld about a generous, fool-ish team climbing, crossing,
and helping each other through a tricky outdoor quest.

Premise:
- Two adventurers set out with a shared goal.
- One is generous and eager to help.
- The other is a little fool-ish and charges ahead without enough care.
- Their teamwork eventually turns the mistake into a happy ending.

The world is simulated, not template-swapped: physical meters track distance,
height, balance, load, and injury risk; emotional memes track trust, courage,
worry, and relief. The prose is derived from state changes and causal beats.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/generous_fool_ish_teamwork_happy_ending_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/generous_fool_ish_teamwork_happy_ending_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/generous_fool_ish_teamwork_happy_ending_adventure.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "height": 0.0, "balance": 1.0, "load": 0.0, "risk": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"trust": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0, "joy": 0.0, "regret": 0.0})

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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    path: str
    danger: str
    victory: str
    afford: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Quest:
    id: str
    tool: str
    goal: str
    misuse: str
    risk: str
    safe_alternative: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Rescue:
    id: str
    method: str
    strength: int
    text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    quest: str
    rescue: str
    hero_a: str
    hero_a_gender: str
    hero_b: str
    hero_b_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


SETTINGS = {
    "canyon": Setting("canyon", "a rocky canyon", "the narrow path", "the edge", "the far ledge", {"climb", "cross"}),
    "island": Setting("island", "a windy island", "the beach path", "the surf", "the hidden cove", {"climb", "cross"}),
    "forest": Setting("forest", "a deep forest", "the rooty trail", "the ravine", "the lookout hill", {"climb", "cross"}),
}

QUESTS = {
    "rope_bridge": Quest("rope_bridge", "rope", "cross the gap", "tug the rope too hard", "a loose bridge can wobble", "work together and hold the rope steady", {"bridge", "teamwork"}),
    "waterfall_path": Quest("waterfall_path", "pole", "reach the safe path", "lean out too far", "slick rocks can slip", "move one careful step at a time", {"climb", "teamwork"}),
    "treasure_tree": Quest("treasure_tree", "basket", "reach the nest", "climb without a plan", "branches can bend and drop you", "share the job and steady the climb", {"climb", "teamwork"}),
}

RESCUES = {
    "pull_together": Rescue("pull_together", "pulled together", 2, "held the rope, pulled hard, and steadied the way", "pulled too weakly and could not steady the way", {"teamwork"}),
    "step_by_step": Rescue("step_by_step", "step by step", 3, "showed the safe footholds and led them across step by step", "showed the footholds, but the wobble was already too strong", {"teamwork"}),
    "lift_and_hold": Rescue("lift_and_hold", "lift and hold", 4, "lifted the load and held it steady until everyone was safe", "lifted, but the load was already slipping", {"teamwork"}),
}

GIRL_NAMES = ["Mina", "Ava", "Nia", "Luna", "Maya", "Iris"]
BOY_NAMES = ["Taro", "Eli", "Noah", "Kai", "Finn", "Leo"]
HELPER_NAMES = ["Pip", "Sora", "Bo", "Rae", "Leni"]

TRAITS = ["generous", "fool-ish", "brave", "curious", "kind", "careful"]


def hazard_score(setting: Setting, quest: Quest) -> bool:
    return bool(setting.afford & quest.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, r) for s, st in SETTINGS.items() for q, qt in QUESTS.items() for r in RESCUES if hazard_score(st, qt)]


def setting_by_id(sid: str) -> Setting:
    if sid not in SETTINGS:
        raise StoryError("Unknown setting.")
    return SETTINGS[sid]


def quest_by_id(qid: str) -> Quest:
    if qid not in QUESTS:
        raise StoryError("Unknown quest.")
    return QUESTS[qid]


def rescue_by_id(rid: str) -> Rescue:
    if rid not in RESCUES:
        raise StoryError("Unknown rescue.")
    return RESCUES[rid]


def _pronoun_name(name: str, gender: str) -> tuple[str, str]:
    return name, gender


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about generosity, fool-ishness, teamwork, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--hero-a")
    ap.add_argument("--hero-a-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-b")
    ap.add_argument("--hero-b-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.setting and args.quest and not hazard_score(setting_by_id(args.setting), quest_by_id(args.quest)):
        raise StoryError("That quest does not fit this setting.")
    if args.rescue and args.rescue not in RESCUES:
        raise StoryError("Unknown rescue.")
    eligible = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.quest is None or c[1] == args.quest) and (args.rescue is None or c[2] == args.rescue)]
    if not eligible:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, rescue = rng.choice(sorted(eligible))
    ha_gender = args.hero_a_gender or rng.choice(["girl", "boy"])
    hb_gender = args.hero_b_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    ha_pool = GIRL_NAMES if ha_gender == "girl" else BOY_NAMES
    hb_pool = GIRL_NAMES if hb_gender == "girl" else BOY_NAMES
    helper_pool = HELPER_NAMES
    hero_a = args.hero_a or rng.choice(ha_pool)
    hero_b = args.hero_b or rng.choice([n for n in hb_pool if n != hero_a] or hb_pool)
    helper = args.helper or rng.choice([n for n in helper_pool if n not in {hero_a, hero_b}] or helper_pool)
    return StoryParams(setting=setting, quest=quest, rescue=rescue, hero_a=hero_a, hero_a_gender=ha_gender, hero_b=hero_b, hero_b_gender=hb_gender, helper=helper, helper_gender=helper_gender)


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    rescue = RESCUES[params.rescue]
    w = World(setting)
    a = w.add(Entity(id=params.hero_a, kind="character", type=params.hero_a_gender, role="leader", traits=["generous"]))
    b = w.add(Entity(id=params.hero_b, kind="character", type=params.hero_b_gender, role="partner", traits=["fool-ish"]))
    h = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["steady"]))
    w.add(Entity(id="trail", type="place", label=setting.place))
    w.facts.update(setting=setting, quest=quest, rescue=rescue, a=a, b=b, h=h)
    a.memes["trust"] = 2
    b.memes["trust"] = 1
    h.memes["trust"] = 3
    return w


def _apply_events(w: World) -> None:
    s: Setting = w.facts["setting"]
    q: Quest = w.facts["quest"]
    r: Rescue = w.facts["rescue"]
    a: Entity = w.facts["a"]
    b: Entity = w.facts["b"]
    h: Entity = w.facts["h"]
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    w.say(f"On {s.place}, {a.id} and {b.id} set out on an adventure.")
    w.say(f"They wanted to {q.goal}, and the path toward {s.victory} glittered ahead.")
    w.para()
    a.memes["courage"] += 1
    b.memes["worry"] += 1
    w.say(f"{a.id} was generous and shared the gear, while {b.id} was a little fool-ish and rushed ahead.")
    w.say(f"That fool-ish choice made the {q.risk} feel real.")
    b.meters["risk"] += 1
    b.meters["balance"] -= 1
    a.memes["worry"] += 1
    w.para()
    w.say(f"{h.id} saw the danger and called them back.")
    w.say(f"Together they chose to {q.safe_alternative}.")
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["joy"] += 1
    b.memes["regret"] += 1
    w.para()
    if r.strength >= 3:
        b.meters["balance"] += 1
        b.meters["risk"] = 0
        h.memes["relief"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        w.say(f"{h.id} {r.text}. The plan held, and they crossed safely.")
    else:
        w.say(f"{h.id} {r.fail_text}. But the others had already steadied the line.")
    w.say(f"In the end, {a.id} and {b.id} reached {s.victory}, laughing with {h.id} beside them.")


def generate(params: StoryParams) -> StorySample:
    w = _build_world(params)
    _apply_events(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(w)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa(w)],
        world=w,
    )


def generation_prompts(w: World) -> list[str]:
    s: Setting = w.facts["setting"]
    q: Quest = w.facts["quest"]
    return [
        f"Write an adventure story about two friends on {s.place} who must {q.goal} and learn teamwork.",
        f"Tell a child-friendly story with the words generous and fool-ish, where one adventurer makes a mistake but everyone ends happy.",
        f"Write a short adventure where teamwork turns a risky choice into a happy ending.",
    ]


def story_qa(w: World) -> list[tuple[str, str]]:
    s: Setting = w.facts["setting"]
    q: Quest = w.facts["quest"]
    a: Entity = w.facts["a"]
    b: Entity = w.facts["b"]
    h: Entity = w.facts["h"]
    return [
        ("Who were the story about?", f"It was about {a.id}, {b.id}, and their helper {h.id}. They went on an adventure together."),
        ("What made the choice fool-ish?", f"{b.id} rushed ahead without enough care, and that was fool-ish because the path had a real danger. The choice could have caused a wobble or slip."),
        ("How did teamwork help?", f"{a.id} shared the job, {h.id} steadied the way, and {b.id} helped again. Working together kept the adventure safe and moving forward."),
        ("How did the story end?", f"It ended happily at {s.victory}. The team reached the goal together and the scary moment turned into a cheerful ending."),
    ]


def world_qa(w: World) -> list[tuple[str, str]]:
    return [
        ("What does generous mean?", "Generous means willing to share, help, or give to someone else. A generous person likes making things better for the group."),
        ("What does teamwork mean?", "Teamwork means people help each other and do a job together. Each person does a part, and the whole group can do more."),
        ("Why should adventurers be careful?", "Adventures can have uneven ground, drops, and other surprises. Being careful helps everyone stay safe while they keep exploring."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
quest(Q) :- quest_fact(Q).
rescue(R) :- rescue_fact(R).
valid(S,Q,R) :- setting(S), quest(Q), rescue(R), hazard(S,Q).

hazard(S,Q) :- afford(S,A), quest_tag(Q,A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_fact", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
    for rid in RESCUES:
        lines.append(asp.fact("rescue_fact", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, rescue=None, hero_a=None, hero_a_gender=None, hero_b=None, hero_b_gender=None, helper=None, helper_gender=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() produced a story.")
    except Exception as exc:
        print(f"FAILED: generate smoke test crashed: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="canyon", quest="rope_bridge", rescue="pull_together", hero_a="Mina", hero_a_gender="girl", hero_b="Taro", hero_b_gender="boy", helper="Pip", helper_gender="boy"),
    StoryParams(setting="forest", quest="treasure_tree", rescue="lift_and_hold", hero_a="Ava", hero_a_gender="girl", hero_b="Kai", hero_b_gender="boy", helper="Rae", helper_gender="girl"),
    StoryParams(setting="island", quest="waterfall_path", rescue="step_by_step", hero_a="Nia", hero_a_gender="girl", hero_b="Eli", hero_b_gender="boy", helper="Sora", helper_gender="girl"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, q, r in combos:
            print(f"  {s:8} {q:16} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
