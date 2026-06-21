#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fifth_champagne_conflict_superhero_story.py
===========================================================================

A small superhero storyworld built from the seed words "fifth" and
"champagne" with a conflict-driven turn.

Premise:
- A young superhero team is preparing for the city's fifth victory celebration.
- One hero wants to pop champagne right away.
- Another hero warns that the trapped villain is not secured yet.
- The conflict resolves either by waiting for the safe celebration or by
  calling for help before the party starts.

The world is state-driven: the danger, the conflict, and the resolution all
change meters and memes that are then rendered into prose.
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

TITLE = "Superhero Story"

HERO_NAMES = ["Nova", "Blink", "Comet", "Spark", "Ruby", "Milo", "Iris", "Jett"]
VILLAIN_NAMES = ["Drift", "Murmur", "Gloom", "Static", "Riddle"]
SIDEKICK_NAMES = ["Pip", "Wren", "Taz", "Luna", "Poppy"]

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    role: str = ""
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    champagne_safe: bool = False
    locked: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    city: str
    place: str
    fifth_event: str
    banner: str
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
class Champagne:
    id: str
    phrase: str
    label: str
    safe: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class ConflictPlan:
    id: str
    sense: int
    settle: str
    warn: str
    success: str
    fail: str
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
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    villain: str
    champagne: str
    plan: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "cityhall": Setting(
        city="Aurora City",
        place="the clock tower plaza",
        fifth_event="the fifth victory parade",
        banner="a gold banner with a big 5",
    ),
    "harbor": Setting(
        city="Bluewater Bay",
        place="the lighthouse dock",
        fifth_event="the fifth rescue celebration",
        banner="streamers shaped like lightning bolts",
    ),
}

CHAMPAGNES = {
    "bottle": Champagne(id="bottle", phrase="a bottle of champagne", label="champagne"),
    "mini": Champagne(id="mini", phrase="a tiny bottle of champagne", label="champagne"),
}

PLANS = {
    "wait": ConflictPlan(
        id="wait",
        sense=3,
        settle="waited for the villain cage to be locked first",
        warn="The trap was not safe yet. One shake could let the bad guy slip free.",
        success="kept the champagne chilled and waited for the all-clear",
        fail="almost popped the cork too soon, but stopped at the last second",
    ),
    "call_team": ConflictPlan(
        id="call_team",
        sense=3,
        settle="called the rest of the team to help secure the cage",
        warn="The cage needed one more lock, and the celebration could wait a minute.",
        success="radioed the team and held the bottle steady until the danger passed",
        fail="forgot to call anyone and had to start over",
    ),
    "store_first": ConflictPlan(
        id="store_first",
        sense=2,
        settle="put the champagne in the hero locker first",
        warn="A popping cork could startle the villain before the door was locked.",
        success="set the bottle aside and locked the cage with a calm grin",
        fail="left the bottle on the railing, where it nearly tipped over",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero conflict storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--champagne", choices=CHAMPAGNES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
    ap.add_argument("--villain")
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
    return [(s, c, p) for s in SETTINGS for c in CHAMPAGNES for p in PLANS]


def explain_invalid(reason: str) -> str:
    return f"(No story: {reason})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.champagne:
        combos = [c for c in combos if c[1] == args.champagne]
    if args.plan:
        combos = [c for c in combos if c[2] == args.plan]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, champagne, plan = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    return StoryParams(
        setting=setting,
        hero=args.hero or rng.choice(HERO_NAMES),
        hero_type=hero_type,
        sidekick=args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != args.hero]),
        sidekick_type=sidekick_type,
        villain=args.villain or rng.choice(VILLAIN_NAMES),
        champagne=champagne,
        plan=plan,
    )


def asp_facts() -> str:
    import asp

    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHAMPAGNES:
        lines.append(asp.fact("champagne", c))
    for p, plan in PLANS.items():
        lines.append(asp.fact("plan", p))
        lines.append(asp.fact("sense", p, plan.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,P) :- setting(S), champagne(C), plan(P).
sensible(P) :- plan(P), sense(P, N), sense_min(M), N >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH in valid_combos:")
        print("  python-only:", sorted(py - cl))
        print("  asp-only:", sorted(cl - py))
    if set(asp_sensible()) == set(PLANS):
        print("OK: sensible plans match.")
    else:
        ok = False
        print("MISMATCH in sensible plans.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: smoke test story generation works.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    return 0 if ok else 1


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.champagne not in CHAMPAGNES:
        raise StoryError(f"Unknown champagne variant: {params.champagne}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown conflict plan: {params.plan}")

    setting = SETTINGS[params.setting]
    champ = CHAMPAGNES[params.champagne]
    plan = PLANS[params.plan]

    w = World(setting)
    hero = w.add(Entity(id=params.hero, kind="character", role="hero", type=params.hero_type, label="the hero"))
    sidekick = w.add(Entity(id=params.sidekick, kind="character", role="sidekick", type=params.sidekick_type, label="the sidekick"))
    villain = w.add(Entity(id=params.villain, kind="character", role="villain", type="villain", label="the trapped villain"))
    bottle = w.add(Entity(id="champagne", kind="thing", label=champ.label, locked=False, champagne_safe=False))
    cage = w.add(Entity(id="cage", kind="thing", label="the cage", locked=False))

    hero.meters["energy"] = 1.0
    sidekick.memes["worry"] = 1.0
    villain.meters["trouble"] = 1.0
    w.facts.update(
        hero=hero, sidekick=sidekick, villain=villain, bottle=bottle, cage=cage,
        setting=setting, champ=champ, plan=plan,
    )

    w.say(
        f"On the fifth day of peace, {hero.id} and {sidekick.id} arrived at {setting.place} for {setting.fifth_event}. "
        f"{setting.banner} hung above the crowd, and the whole city felt ready to cheer."
    )
    w.say(
        f"But the trapped villain, {villain.id}, still rattled the cage in the corner."
    )
    w.para()
    w.say(
        f'{hero.id} lifted {champ.phrase} and smiled. "We should open the champagne now!"'
    )
    w.say(
        f'{sidekick.id} frowned. "{plan.warn}"'
    )

    hero.memes["excited"] = 1.0
    sidekick.memes["conflict"] = 1.0
    if plan.id == "wait":
        hero.memes["conflict"] = 1.0
        w.say(
            f"{hero.id} blinked, looked at the cage, and nodded. {sidekick.id} was right."
        )
        w.para()
        cage.locked = True
        bottle.champagne_safe = True
        w.say(
            f"Together they {plan.settle}. Then, when the cage was secure, "
            f"they {plan.success}."
        )
        w.say(
            f"The cork popped at last, the foam sparkled like tiny stars, and the fifth celebration could begin."
        )
    elif plan.id == "call_team":
        hero.memes["conflict"] = 1.0
        w.say(
            f"{hero.id} hesitated, then agreed to help. The argument faded into teamwork."
        )
        w.para()
        cage.locked = True
        bottle.champagne_safe = True
        w.say(f"They {plan.settle}. After that, {hero.id} {plan.success}.")
        w.say(
            f"The bottle hissed softly and the crowd cheered under the moonlit banner."
        )
    else:
        hero.memes["conflict"] = 1.0
        w.say(
            f"{hero.id} almost rushed ahead, but {sidekick.id} grabbed the bottle with a careful hand."
        )
        w.para()
        cage.locked = True
        bottle.champagne_safe = True
        w.say(f"At last they {plan.settle}, and {hero.id} {plan.success}.")
        w.say(
            f"When the cork finally jumped, everyone laughed because the danger was gone."
        )

    hero.memes["joy"] = 1.0
    sidekick.memes["joy"] = 1.0
    w.facts["ending"] = "safe"
    return w


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "fifth" and "champagne".',
        f"Tell a conflict story where {f['hero'].id} wants to open champagne during the fifth celebration, but {f['sidekick'].id} insists they secure the villain first.",
        f"Write a child-friendly superhero tale about a bottle of champagne, a trapped villain, and a safe victory party.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    villain: Entity = f["villain"]  # type: ignore[assignment]
    plan: ConflictPlan = f["plan"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question="What did the hero want to do first?",
            answer=f"{hero.id} wanted to open the champagne first, because the fifth celebration felt exciting and close. But the bottle had to wait until the villain was safe.",
        ),
        QAItem(
            question="Why was there a conflict?",
            answer=f"There was a conflict because {hero.id} wanted to celebrate right away, while {sidekick.id} worried that {villain.id} was still too loose in the cage. They wanted different things for the same moment.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"They solved it by {plan.settle}. That made the celebration safe, so the champagne could be opened after the danger was over.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is champagne?",
            answer="Champagne is a bubbly drink that grown-ups sometimes use to celebrate happy news. In stories like this, it has to wait until everyone is safe.",
        ),
        QAItem(
            question="What does the fifth mean here?",
            answer="Fifth means the number 5. It tells you this is the fifth celebration, not the first or second one.",
        ),
        QAItem(
            question="Why should heroes secure danger before celebrating?",
            answer="Heroes should secure danger first because a party is only fun when everyone is safe. If a villain is still loose, the celebration can turn into trouble very quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id}: kind={e.kind} role={e.role} meters={e.meters or {}} memes={e.memes or {}} attrs={e.attrs or {}}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="cityhall", hero="Nova", hero_type="girl", sidekick="Pip", sidekick_type="boy", villain="Gloom", champagne="bottle", plan="wait"),
    StoryParams(setting="harbor", hero="Comet", hero_type="boy", sidekick="Luna", sidekick_type="girl", villain="Static", champagne="mini", plan="call_team"),
    StoryParams(setting="cityhall", hero="Iris", hero_type="girl", sidekick="Taz", sidekick_type="boy", villain="Riddle", champagne="bottle", plan="store_first"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible plans:", ", ".join(asp_sensible()))
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
