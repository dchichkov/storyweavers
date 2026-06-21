#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jamboree_misunderstanding_slice_of_life.py
===========================================================================

A standalone storyworld about a small community jamboree where a harmless
misunderstanding briefly causes hurt feelings, then gets cleared up with a
plainspoken talk and a kinder plan. The style stays slice-of-life: ordinary
people, practical details, and an ending that shows what changed.

The story world is intentionally small and constraint-checked. It models:
- one event setting,
- one misunderstood signal,
- one worried helper,
- one simple clarification,
- one peaceful ending image.

It also provides the shared storyworld interface, Q&A generation, and an
inline ASP twin for the reasonableness gate and outcome model.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    crowd: str
    mood: str


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    meaning: str
    mistaken_for: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    worry: str
    explanation: str
    fix: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    purpose: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_awkward(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["awkward"] < THRESHOLD:
            continue
        sig = ("awkward", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "helper" in world.entities:
            world.get("helper").memes["worry"] += 1
        out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("cleared") and ("relief", "once") not in world.fired:
        world.fired.add(("relief", "once"))
        for name in ("kid", "helper"):
            if name in world.entities:
                world.get(name).memes["relief"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("awkward", _r_awkward), Rule("relief", _r_relief)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for sig_id, sig in SIGNALS.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                if sig_id in sig.mistaken_for.split("|") and mis.sense >= SENSE_MIN:
                    combos.append((sid, sig_id, mid))
    return combos


def reasonableness(setting: Setting, signal: Signal, misunderstanding: Misunderstanding) -> bool:
    return signal.id in signal.mistaken_for.split("|") and misunderstanding.sense >= SENSE_MIN


def predict(world: World, signal_id: str) -> dict:
    sim = world.copy()
    sim.get("signal").meters["seen"] += 1
    sim.get("kid").meters["awkward"] += 1
    propagate(sim)
    return {
        "awkward": sim.get("kid").meters["awkward"] >= THRESHOLD,
        "worry": sim.get("helper").memes["worry"] if "helper" in sim.entities else 0,
    }


def introduce(world: World, kid: Entity, helper: Entity, setting: Setting) -> None:
    kid.memes["hope"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At the neighborhood jamboree, {kid.id} was helping at {setting.place}. "
        f"{setting.detail} {setting.crowd} moved past the tables, and the whole place felt {setting.mood}."
    )


def spot_signal(world: World, kid: Entity, sig: Signal) -> None:
    kid.meters["curious"] += 1
    world.say(
        f"Near the craft table, {kid.id} noticed {sig.phrase}. It looked simple, but it was easy to mix up."
    )
    world.say(
        f'"{sig.label}?" {kid.id} murmured, because {sig.mistaken_for.replace("|", " or ")} could mean something else in a busy crowd.'
    )


def worry(world: World, helper: Entity, kid: Entity, mis: Misunderstanding, sig: Signal) -> None:
    helper.meters["awkward"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} saw the mix-up and frowned a little. {helper.pronoun().capitalize()} thought {kid.id} might be upset by the misunderstanding."
    )
    world.say(
        f'"Wait," {helper.id} said, "that {sig.label} does not mean what you think. {mis.worry}"'
    )


def act_on_mixup(world: World, kid: Entity, sig: Signal) -> None:
    kid.meters["awkward"] += 1
    kid.memes["embarrassed"] += 1
    world.say(
        f"Before anyone could explain, {kid.id} felt the room go still and worried {sig.label} had caused trouble."
    )


def clarify(world: World, helper: Entity, kid: Entity, mis: Misunderstanding, sig: Signal) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} kept {helper.pronoun('possessive')} voice easy. {mis.explanation} The point was to help, not to scold."
    )
    world.say(
        f"{kid.id} listened, and the tight feeling in {kid.id}'s chest started to loosen."
    )
    world.facts["cleared"] = True


def repair(world: World, kid: Entity, helper: Entity, mis: Misunderstanding, item: Item) -> None:
    kid.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'To make it right, {kid.id} adjusted the {item.label} and added a plain sign that said "{mis.fix}".'
    )
    world.say(
        f"That small change made the booth easier to understand, and the two of them stood side by side again."
    )


def ending(world: World, setting: Setting, kid: Entity, helper: Entity, item: Item) -> None:
    world.say(
        f"By the end of the jamboree, the {item.label} sat straight on the table, the sign was easy to read, and {kid.id} was smiling again."
    )
    world.say(
        f"{helper.id} handed out one last treat while {setting.crowd} drifted on, and the booth felt calm, ordinary, and warm."
    )


def tell(setting: Setting, signal: Signal, misunderstanding: Misunderstanding, item: Item,
         kid_name: str = "Mina", kid_type: str = "girl",
         helper_name: str = "Mr. Lee", helper_type: str = "man") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="helper", attrs={"side": "booth"}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", attrs={"side": "booth"}))
    world.add(Entity(id="signal", label=signal.label))
    world.add(Entity(id="item", label=item.label))

    introduce(world, kid, helper, setting)
    world.para()
    spot_signal(world, kid, signal)
    worry(world, helper, kid, misunderstanding, signal)
    act_on_mixup(world, kid, signal)
    world.para()
    clarify(world, helper, kid, misunderstanding, signal)
    repair(world, kid, helper, misunderstanding, item)
    world.para()
    ending(world, setting, kid, helper, item)

    world.facts.update(
        setting=setting, signal=signal, misunderstanding=misunderstanding, item=item,
        kid=kid, helper=helper, cleared=True
    )
    return world


SETTINGS = {
    "green": Setting(
        id="green",
        place="the town green",
        detail="A folding stage sat near the fountain, and paper lanterns hung from a string of poles.",
        crowd="Families and neighbors",
        mood="busy and cheerful",
    ),
    "school": Setting(
        id="school",
        place="the school courtyard",
        detail="A row of snack tables sat under a banner, and little flags fluttered in the wind.",
        crowd="Parents, teachers, and children",
        mood="bright and lively",
    ),
}

SIGNALS = {
    "thumbs_up": Signal(
        id="thumbs_up",
        label="a thumbs-up sign",
        phrase="a hand painted with a big thumbs-up",
        meaning="a friendly thank-you",
        mistaken_for="approval|okay",
        tags={"gesture", "friendly"},
    ),
    "note": Signal(
        id="note",
        label="a note card",
        phrase="a small note card by the jar",
        meaning="a reminder",
        mistaken_for="menu|price",
        tags={"paper", "label"},
    ),
    "bell": Signal(
        id="bell",
        label="a bell",
        phrase="a little brass bell near the register",
        meaning="a signal to come over",
        mistaken_for="alarm|school",
        tags={"sound", "signal"},
    ),
}

MISUNDERSTANDINGS = {
    "wrong_line": Misunderstanding(
        id="wrong_line",
        worry="It was only meant to show that the booth was ready.",
        explanation="The sign meant 'come over here,' not 'something is wrong here.'",
        fix="Come on over for jam cookies",
        sense=3,
        tags={"clarify", "social"},
    ),
    "mixup_menu": Misunderstanding(
        id="mixup_menu",
        worry="It was just a label for the snacks, not a warning.",
        explanation="The card was describing the treats on the table, not telling anyone to stop.",
        fix="Fresh jam and crackers",
        sense=3,
        tags={"clarify", "food"},
    ),
}

ITEMS = {
    "booth": Item(
        id="booth",
        label="jam booth",
        phrase="the little jam booth",
        purpose="to share jam cookies and fruit cups",
        tags={"food", "booth", "jamboree"},
    ),
}

SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Nora", "Lena", "Ivy", "June"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Theo", "Finn"]


@dataclass
class StoryParams:
    setting: str
    signal: str
    misunderstanding: str
    item: str
    kid_name: str
    kid_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life jamboree misunderstanding storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man", "aunt", "uncle", "mother", "father"])
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


def explain_rejection() -> str:
    return "(No story: this combination does not create a believable misunderstanding.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combos available.)")
    if args.setting and args.signal and args.misunderstanding:
        if (args.setting, args.signal, args.misunderstanding) not in combos:
            raise StoryError(explain_rejection())
    choice = rng.choice(sorted(combos))
    setting, signal, misunderstanding = choice
    item = args.item or "booth"
    kid_type = args.kid_type or rng.choice(["girl", "boy"])
    kid_name = args.kid_name or rng.choice(GIRL_NAMES if kid_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["woman", "man", "aunt", "uncle"])
    helper_name = args.helper_name or rng.choice(["Ms. Park", "Mr. Lee", "Aunt Jo", "Uncle Ben"])
    return StoryParams(setting=setting, signal=signal, misunderstanding=misunderstanding, item=item,
                       kid_name=kid_name, kid_type=kid_type, helper_name=helper_name, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the word "jamboree" and a small misunderstanding at {f["setting"].place}.',
        f"Tell a gentle story where {f['kid'].id} misreads {f['signal'].label} at a jamboree booth, then gets a calm explanation.",
        f'Write an everyday story about a booth at a jamboree where a sign is misunderstood and later clarified kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"].id
    helper = f["helper"].id
    signal = f["signal"]
    mis = f["misunderstanding"]
    item = f["item"]
    return [
        QAItem(
            question="What kind of event was it?",
            answer="It was a jamboree, a busy local gathering with booths, treats, and families walking around."
        ),
        QAItem(
            question=f"What did {kid} misunderstand?",
            answer=f"{kid} misunderstood {signal.label}. It looked like a warning or a different kind of sign, but it was really meant to be friendly."
        ),
        QAItem(
            question=f"How did {helper} help?",
            answer=f"{helper} explained the meaning in plain words, then helped fix the booth sign so it was easy to read. That turned the awkward moment into a small, ordinary solution."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The booth was tidied up, the message was clearer, and everyone could keep enjoying the jamboree. The misunderstanding was over, and the day stayed calm."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jamboree?",
            answer="A jamboree is a cheerful event with lots of people, booths, music, or games. It usually feels lively and social."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a word, look, or action means one thing, but it really means something else."
        ),
        QAItem(
            question="What helps after a misunderstanding?",
            answer="A clear explanation helps most. When people speak calmly and use simple words, the confusion can go away."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:10} {e.type:8} meters={meters} memes={memes} role={e.role}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="green", signal="thumbs_up", misunderstanding="wrong_line", item="booth",
                kid_name="Mina", kid_type="girl", helper_name="Mr. Lee", helper_type="man"),
    StoryParams(setting="school", signal="note", misunderstanding="mixup_menu", item="booth",
                kid_name="Owen", kid_type="boy", helper_name="Ms. Park", helper_type="woman"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.signal not in SIGNALS or params.misunderstanding not in MISUNDERSTANDINGS or params.item not in ITEMS:
        raise StoryError("Invalid params.")
    if not reasonableness(SETTINGS[params.setting], SIGNALS[params.signal], MISUNDERSTANDINGS[params.misunderstanding]):
        raise StoryError(explain_rejection())
    world = tell(SETTINGS[params.setting], SIGNALS[params.signal], MISUNDERSTANDINGS[params.misunderstanding], ITEMS[params.item],
                 kid_name=params.kid_name, kid_type=params.kid_type, helper_name=params.helper_name, helper_type=params.helper_type)
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


ASP_RULES = r"""
valid(Sig, Mis) :- signal(Sig), misunderstanding(Mis), sense(Mis, N), sense_min(M), N >= M.
outcome(cleared) :- valid(_, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sig_id, sig in SIGNALS.items():
        lines.append(asp.fact("signal", sig_id))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("sense", mid, mis.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s, si, m) for s, si, m in valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
